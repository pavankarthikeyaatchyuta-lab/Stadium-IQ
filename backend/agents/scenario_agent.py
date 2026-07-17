"""
Agent module for StadiumIQ: scenario_agent.py.
"""
import copy
import json
import os

import google.generativeai as genai
from dotenv import load_dotenv

from backend.agents.gemini_utils import generate_gemini_text_async
from backend.config import GEMINI_MODEL
from backend.context_manager import ContextManager
from backend.engines.crowd_risk_engine import CrowdRiskEngine
from backend.engines.graph_engine import NavigationGraph


load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class ScenarioAgent:
    def __init__(self, graph: NavigationGraph, risk_engine: CrowdRiskEngine):
        self.graph = graph
        self.risk_engine = risk_engine
        self.model = genai.GenerativeModel(model_name=GEMINI_MODEL)

    async def simulate(
        self,
        scenario_type: str,
        scenario_params: dict,
        language: str,
        context: ContextManager,
    ) -> dict:
        copied_context = copy.deepcopy(context)

        if scenario_type == "gate_closure":
            computed_impact = self._simulate_gate_closure(copied_context, scenario_params)
        elif scenario_type == "section_overflow":
            computed_impact = self._simulate_section_overflow(copied_context, scenario_params)
        elif scenario_type == "emergency_evacuation":
            computed_impact = self._simulate_emergency_evacuation(copied_context)
        else:
            computed_impact = {
                "affected_fans": 0,
                "severity": "Medium",
                "operational_priority": ["Review scenario inputs"],
                "estimated_recovery_minutes": 15,
                "required_volunteers": 2,
                "alternative_routes": {},
                "affected_amenities": [],
            }

        prompt = f"""
You are an operations director at FIFA World Cup 2026.
A {scenario_type} scenario was simulated. Computed impact: {json.dumps(computed_impact)}.
Provide:
1. Severity assessment (Critical/High/Medium)
2. Operational Priority ranking (1-3 immediate actions)
3. Estimated recovery time and reasoning
4. Required staff deployment
5. Communication message to broadcast to fans
Respond in {language}.
""".strip()

        ai_explanation = await generate_gemini_text_async(
            self.model,
            prompt,
            (
                f"Scenario severity: {computed_impact['severity']}. "
                f"Estimated recovery: {computed_impact['estimated_recovery_minutes']} minutes. "
                f"Required volunteers: {computed_impact['required_volunteers']}."
            ),
        )

        return {
            "scenario_type": scenario_type,
            "scenario_params": scenario_params,
            "computed_impact": computed_impact,
            "ai_explanation": ai_explanation,
            "language": language,
        }

    def _simulate_gate_closure(self, context: ContextManager, params: dict) -> dict:
        gate = params.get("gate", "A")
        context.gate_status[gate] = "closed"
        gate_node = f"gate_{gate.lower()}"
        affected_sections = self._sections_relying_on_gate(gate_node)
        analysis = self.risk_engine.analyze_stadium(
            context.section_occupancy,
            context.match_phase,
            context.weather,
            context.queue_times,
        )
        open_gates = self.graph.get_open_gates(context.gate_status)
        alternative_routes = {}

        for section in affected_sections:
            section_node = f"section_{section.lower()}"
            alternative_routes[section] = self._nearest_route(section_node, open_gates)

        affected_fans = sum(
            context.section_occupancy.get(section, 0) * 500
            for section in affected_sections
        )
        severity = self._severity_from_risk(analysis["overall_risk"], affected_fans)

        return {
            "affected_fans": affected_fans,
            "severity": severity,
            "operational_priority": [
                f"Close and staff Gate {gate}",
                "Redirect fans to nearest open gates",
                "Monitor affected concourse pressure",
            ],
            "estimated_recovery_minutes": 20 if severity == "Critical" else 15,
            "required_volunteers": max(4, int(affected_fans / 5000) + 2),
            "alternative_routes": alternative_routes,
            "affected_amenities": self._affected_amenities(affected_sections),
        }

    def _simulate_section_overflow(self, context: ContextManager, params: dict) -> dict:
        section = params.get("section", "B1")
        context.section_occupancy[section] = 100
        analysis = self.risk_engine.analyze_stadium(
            context.section_occupancy,
            context.match_phase,
            context.weather,
            context.queue_times,
        )
        alternate_sections = [
            section_id
            for section_id, occupancy in context.section_occupancy.items()
            if occupancy < 60 and section_id != section
        ]
        redirect_capacity = sum(
            (60 - context.section_occupancy[section_id]) * 500
            for section_id in alternate_sections
        )
        affected_fans = context.section_occupancy.get(section, 0) * 500
        severity = self._severity_from_risk(analysis["overall_risk"], affected_fans)

        return {
            "affected_fans": affected_fans,
            "severity": severity,
            "operational_priority": [
                f"Stop additional entry to Section {section}",
                "Redirect fans to lower occupancy sections",
                "Send crowd guidance volunteers to the nearest concourse",
            ],
            "estimated_recovery_minutes": 25 if severity == "Critical" else 18,
            "required_volunteers": max(5, int(affected_fans / 6000) + 3),
            "alternative_routes": {
                "overflow_section": section,
                "alternate_sections": alternate_sections,
                "redirect_capacity": redirect_capacity,
            },
            "affected_amenities": self._affected_amenities([section]),
        }

    def _simulate_emergency_evacuation(self, context: ContextManager) -> dict:
        open_gates = self.graph.get_open_gates(context.gate_status)
        alternative_routes = {}
        evacuation_times = []

        for section in context.section_occupancy:
            section_node = f"section_{section.lower()}"
            route = self._nearest_route(section_node, open_gates)
            alternative_routes[section] = route
            if route.get("estimated_minutes") is not None:
                evacuation_times.append(route["estimated_minutes"])

        total_evacuation_time = max(evacuation_times) if evacuation_times else 0
        affected_fans = sum(
            occupancy * 500
            for occupancy in context.section_occupancy.values()
        )

        return {
            "affected_fans": affected_fans,
            "severity": "Critical",
            "operational_priority": [
                "Open all available exit routes",
                "Prioritize sections nearest ramps and elevators",
                "Broadcast evacuation instructions by section",
            ],
            "estimated_recovery_minutes": total_evacuation_time,
            "required_volunteers": max(10, int(affected_fans / 8000) + 8),
            "alternative_routes": alternative_routes,
            "affected_amenities": ["accessibility_ramp_a", "elevator_north"],
        }

    def _sections_relying_on_gate(self, gate_node: str) -> list[str]:
        affected_sections = set()
        frontier = [gate_node]
        visited = set()

        for _ in range(3):
            next_frontier = []
            for node in frontier:
                if node in visited:
                    continue
                visited.add(node)
                for neighbor, _ in self.graph.graph.get(node, []):
                    neighbor_type = self.graph.nodes[neighbor]["type"]
                    if neighbor_type == "section":
                        affected_sections.add(neighbor.replace("section_", "").upper())
                    elif neighbor_type in {"concourse", "accessibility"}:
                        next_frontier.append(neighbor)
            frontier = next_frontier

        return sorted(affected_sections)

    def _nearest_route(self, start: str, destinations: list[str]) -> dict:
        best_route = {"path": [], "path_names": [], "estimated_minutes": None}

        for destination in destinations:
            path = self.graph.find_path(start, destination)
            if not path:
                continue
            summary = self.graph.get_path_summary(path)
            if (
                best_route["estimated_minutes"] is None
                or summary["estimated_minutes"] < best_route["estimated_minutes"]
            ):
                best_route = {
                    "to": destination,
                    "path": summary["path"],
                    "path_names": summary["path_names"],
                    "estimated_minutes": summary["estimated_minutes"],
                }

        return best_route

    def _affected_amenities(self, sections: list[str]) -> list[str]:
        concourses = set()
        amenities = set()

        for section in sections:
            section_node = f"section_{section.lower()}"
            for neighbor, _ in self.graph.graph.get(section_node, []):
                if self.graph.nodes[neighbor]["type"] == "concourse":
                    concourses.add(neighbor)

        for concourse in concourses:
            for neighbor, _ in self.graph.graph.get(concourse, []):
                if self.graph.nodes[neighbor]["type"] == "amenity":
                    amenities.add(neighbor)

        return sorted(amenities)

    def _severity_from_risk(self, overall_risk: str, affected_fans: float) -> str:
        if overall_risk == "critical" or affected_fans >= 30000:
            return "Critical"
        if overall_risk == "high" or affected_fans >= 15000:
            return "High"
        return "Medium"

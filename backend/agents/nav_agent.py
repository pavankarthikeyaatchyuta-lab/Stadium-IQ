"""
Agent module for StadiumIQ: nav_agent.py.
"""

from dotenv import load_dotenv

from backend.agents.gemini_utils import generate_gemini_text_async
from backend.config import GEMINI_MODEL
from backend.context_manager import ContextManager
from backend.engines.graph_engine import NavigationGraph

load_dotenv()


class NavigationAgent:
    def __init__(self, graph: NavigationGraph):
        self.graph = graph

    async def get_directions(
        self,
        from_loc: str,
        to_loc: str,
        language: str,
        context: ContextManager,
    ) -> dict:
        gate_warning = None
        destination = to_loc

        gate_lookup = {
            "gate_a": "A",
            "gate_b": "B",
            "gate_c": "C",
            "gate_d": "D",
        }
        if to_loc in gate_lookup:
            gate_key = gate_lookup[to_loc]
            if context.gate_status.get(gate_key) == "closed":
                open_gates = self.graph.get_open_gates(context.gate_status)
                if open_gates:
                    destination = self._nearest_open_gate(from_loc, open_gates)
                    gate_warning = (
                        f"{self.graph.nodes[to_loc]['name']} is closed. "
                        f"Routing to {self.graph.nodes[destination]['name']} instead."
                    )

        avoid_nodes = [
            f"section_{section_id.lower()}"
            for section_id, occupancy in context.section_occupancy.items()
            if occupancy > 80
        ]

        path = self.graph.find_path(from_loc, destination, avoid_nodes)
        summary = self.graph.get_path_summary(path)
        path_names = summary["path_names"]
        minutes = summary["estimated_minutes"]

        prompt = f"""
You are a FIFA 2026 stadium navigation assistant at MetLife Stadium.
The computed path is: {path_names}. Estimated time: {minutes} minutes.
Congested nodes avoided: {avoid_nodes}. Match phase: {context.match_phase}.
Gate warning: {gate_warning or 'None'}.
Convert this path into clear, friendly step-by-step directions in {language}.
Use landmark names. Mention the gate warning prominently if present.
""".strip()

        fallback_directions = (
            f"Follow this route: {' -> '.join(path_names)}. "
            f"Estimated time is {minutes} minutes."
        )
        if gate_warning:
            fallback_directions = f"{gate_warning} {fallback_directions}"
        directions = await generate_gemini_text_async(GEMINI_MODEL, prompt, fallback_directions)

        return {
            "path": path,
            "path_names": path_names,
            "estimated_minutes": minutes,
            "directions": directions,
            "avoided_nodes": avoid_nodes,
            "gate_warning": gate_warning,
            "language": language,
        }

    def _nearest_open_gate(self, from_loc: str, open_gates: list[str]) -> str:
        best_gate = open_gates[0]
        best_minutes = float("inf")

        for gate in open_gates:
            path = self.graph.find_path(from_loc, gate)
            if not path:
                continue
            minutes = self.graph.get_path_summary(path)["estimated_minutes"]
            if minutes < best_minutes:
                best_gate = gate
                best_minutes = minutes

        return best_gate

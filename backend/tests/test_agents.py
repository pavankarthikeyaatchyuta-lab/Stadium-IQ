import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.agents.copilot_agent import OperationsCopilot
from backend.agents.crowd_agent import CrowdAgent
from backend.agents.fan_agent import FanAssistAgent
from backend.agents.nav_agent import NavigationAgent
from backend.agents.scenario_agent import ScenarioAgent
from backend.context_manager import ContextManager
from backend.engines.crowd_risk_engine import CrowdRiskEngine
from backend.engines.graph_engine import NavigationGraph

graph = NavigationGraph("backend/data/stadium_map.json")
risk_engine = CrowdRiskEngine()


def test_nav_closed_gate_warning():
    context = ContextManager()
    context.gate_status["C"] = "closed"
    agent = NavigationAgent(graph)

    result = asyncio.run(agent.get_directions("gate_a", "gate_c", "English", context))

    assert result["gate_warning"] is not None


def test_nav_avoids_high_occupancy():
    context = ContextManager()
    context.section_occupancy["B1"] = 95
    agent = NavigationAgent(graph)

    result = asyncio.run(agent.get_directions("gate_a", "section_b2", "English", context))

    assert "section_b1" in result["avoided_nodes"]


def test_nav_path_returned():
    agent = NavigationAgent(graph)

    result = asyncio.run(agent.get_directions("gate_a", "section_a2", "English", ContextManager()))

    assert isinstance(result["path"], list)
    assert result["path"]


def test_crowd_has_both_keys():
    agent = CrowdAgent(risk_engine)

    result = asyncio.run(agent.analyze("English", ContextManager()))

    assert "risk_analysis" in result
    assert "ai_explanation" in result


def test_crowd_critical_detected():
    context = ContextManager()
    context.section_occupancy["B1"] = 95
    context.match_phase = "halftime"
    agent = CrowdAgent(risk_engine)

    result = asyncio.run(agent.analyze("English", context))

    assert "B1" in result["risk_analysis"]["critical_sections"]


def test_fan_food_shorter_queue():
    context = ContextManager()
    context.queue_times["food_court_a"] = 25
    context.queue_times["food_court_b"] = 5
    agent = FanAssistAgent()

    result = asyncio.run(agent.answer("where should I eat?", "English", context))

    assert "5" in result


def test_fan_hindi_passed():
    agent = FanAssistAgent()

    result = asyncio.run(agent.answer("help me", "Hindi", ContextManager()))

    assert "हिंदी" in result


def test_fan_accessibility_injected():
    agent = FanAssistAgent()

    result = asyncio.run(agent.answer(
        "how do I get there?",
        "English",
        ContextManager(),
        accessibility_needs="wheelchair",
    ))

    assert "wheelchair" in result


def test_scenario_gate_closure_has_affected_fans():
    agent = ScenarioAgent(graph, risk_engine)

    result = asyncio.run(agent.simulate("gate_closure", {"gate": "A"}, "English", ContextManager()))

    assert "affected_fans" in result["computed_impact"]


def test_scenario_evacuation_has_routes():
    agent = ScenarioAgent(graph, risk_engine)

    result = asyncio.run(agent.simulate("emergency_evacuation", {}, "English", ContextManager()))

    assert "alternative_routes" in result["computed_impact"]


def test_copilot_returns_situation_summary():
    agent = OperationsCopilot(risk_engine, graph)

    result = asyncio.run(agent.get_priorities("English", ContextManager()))

    assert "situation_summary" in result
    assert "top_priorities_explanation" in result


def test_copilot_detects_closed_gate():
    context = ContextManager()
    context.gate_status["A"] = "closed"
    agent = OperationsCopilot(risk_engine, graph)

    result = asyncio.run(agent.get_priorities("English", context))

    assert "closed_gates" in result["situation_summary"]

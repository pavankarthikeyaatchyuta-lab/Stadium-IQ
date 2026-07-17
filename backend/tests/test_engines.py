import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.engines.crowd_risk_engine import CrowdRiskEngine
from backend.engines.graph_engine import NavigationGraph

graph = NavigationGraph("backend/data/stadium_map.json")
engine = CrowdRiskEngine()


def test_graph_path_exists():
    path = graph.find_path("gate_a", "section_b1")
    assert path


def test_graph_path_starts_and_ends():
    path = graph.find_path("gate_a", "section_b1")
    assert path[0] == "gate_a"
    assert path[-1] == "section_b1"


def test_graph_avoids_nodes():
    path = graph.find_path("gate_a", "section_b1", avoid_nodes=["concourse_1"])
    assert "concourse_1" not in path


def test_graph_no_path_when_fully_blocked():
    path = graph.find_path(
        "gate_a",
        "section_b1",
        avoid_nodes=["concourse_1", "elevator_north"],
    )
    assert path == []


def test_graph_summary_has_minutes():
    summary = graph.get_path_summary(["gate_a", "concourse_1"])
    assert summary["estimated_minutes"] > 0


def test_graph_open_gates_all_open():
    open_gates = graph.get_open_gates(
        {"A": "open", "B": "open", "C": "open", "D": "open"}
    )
    assert len(open_gates) == 4


def test_graph_open_gates_one_closed():
    open_gates = graph.get_open_gates(
        {"A": "open", "B": "closed", "C": "open", "D": "open"}
    )
    assert len(open_gates) == 3


def test_risk_low():
    result = engine.score_section("A1", 25, "pre_match", "clear", {})
    assert result["risk_level"] == "low"


def test_risk_critical_halftime():
    result = engine.score_section(
        "B1",
        80,
        "halftime",
        "rainy",
        {"food_court_b": 25},
    )
    assert result["risk_level"] == "critical"


def test_risk_choke_bonus_applied():
    result = engine.score_section("A1", 50, "pre_match", "clear", {})
    assert result["risk_score"] > 50


def test_risk_factors_list_not_empty_for_high():
    result = engine.score_section("B1", 70, "halftime", "clear", {})
    assert isinstance(result["risk_factors"], list)
    assert result["risk_factors"]


def test_analyze_returns_all_sections():
    result = engine.analyze_stadium({"A1": 50, "B1": 90}, "halftime", "clear", {})
    assert len(result["sections"]) == 2


def test_analyze_critical_detected():
    result = engine.analyze_stadium({"B1": 95}, "halftime", "rainy", {})
    assert "B1" in result["critical_sections"]


def test_choke_pressure_concourse_1():
    scores = [
        engine.score_section("A1", 50, "pre_match", "clear", {}),
        engine.score_section("A2", 60, "pre_match", "clear", {}),
    ]
    result = engine.compute_choke_pressure("concourse_1", scores)
    assert "pressure_score" in result

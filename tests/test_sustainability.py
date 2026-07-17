import asyncio

from backend.agents.sustainability_agent import SustainabilityAgent
from backend.context_manager import ContextManager


def test_sustainability_agent():
    agent = SustainabilityAgent()
    context = ContextManager.from_dict({
        "current_time": "19:45",
        "match_phase": "halftime",
        "gate_status": {},
        "weather": "clear",
        "queue_times": {},
        "section_occupancy": {},
        "nearby_transport": {
            "metro": "available",
            "rideshare": "15min_wait",
            "parking_north": "full",
            "parking_south": "available",
        }
    })

    result = asyncio.run(agent.get_eco_tip("English", context))

    assert "eco_tip" in result
    assert "transport_context" in result
    assert result["language"] == "English"

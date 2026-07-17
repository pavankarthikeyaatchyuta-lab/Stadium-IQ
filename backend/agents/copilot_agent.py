"""
Agent module for StadiumIQ: copilot_agent.py.
"""
import json

from dotenv import load_dotenv

from backend.agents.gemini_utils import generate_gemini_text_async
from backend.config import GEMINI_MODEL
from backend.context_manager import ContextManager
from backend.engines.crowd_risk_engine import CrowdRiskEngine
from backend.engines.graph_engine import NavigationGraph

load_dotenv()


class OperationsCopilot:
    def __init__(self, risk_engine: CrowdRiskEngine, graph: NavigationGraph):
        self.risk_engine = risk_engine
        self.graph = graph

    async def get_priorities(self, language: str, context: ContextManager) -> dict:
        """Answers: What should we do RIGHT NOW?"""
        risk_analysis = self.risk_engine.analyze_stadium(
            context.section_occupancy,
            context.match_phase,
            context.weather,
            context.queue_times,
        )
        choke_pressure = {
            "concourse_1": self.risk_engine.compute_choke_pressure(
                "concourse_1",
                risk_analysis["sections"],
            ),
            "concourse_2": self.risk_engine.compute_choke_pressure(
                "concourse_2",
                risk_analysis["sections"],
            ),
        }
        closed_gates = [
            gate
            for gate, status in context.gate_status.items()
            if status == "closed"
        ]
        overloaded_queues = [
            queue
            for queue, minutes in context.queue_times.items()
            if "food_court" in queue and minutes > 20
        ]
        transport_issues = [
            name
            for name, status in context.nearby_transport.items()
            if status == "full" or "wait" in status
        ]

        situation_summary = {
            "critical_sections": risk_analysis["critical_sections"],
            "high_risk_sections": risk_analysis["high_risk_sections"],
            "choke_pressure": choke_pressure,
            "closed_gates": closed_gates,
            "overloaded_queues": overloaded_queues,
            "transport_issues": transport_issues,
        }

        prompt = f"""
You are an autonomous operations copilot for FIFA World Cup 2026.
Current stadium situation: {json.dumps(situation_summary)}.
Match phase: {context.match_phase}. Time: {context.current_time}. Weather: {context.weather}.

Identify the TOP 3 operational priorities RIGHT NOW.
For each priority, provide:
- Priority number and title
- Reason (cite specific data from the situation)
- Immediate action required
- Who should execute it (staff role)
- Estimated time to resolve

Format each priority clearly. Respond in {language}.
""".strip()

        top_priorities_explanation = await generate_gemini_text_async(
            GEMINI_MODEL,
            prompt,
            (
                "Top priorities: stabilize critical sections, manage high-risk sections, "
                "and resolve gate, queue, or transport issues listed in the situation summary."
            ),
        )

        return {
            "situation_summary": situation_summary,
            "top_priorities_explanation": top_priorities_explanation,
            "overall_risk": risk_analysis["overall_risk"],
            "language": language,
            "timestamp": context.current_time,
        }

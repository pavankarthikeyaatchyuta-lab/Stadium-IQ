"""
Agent module for StadiumIQ: crowd_agent.py.
"""
import json

from dotenv import load_dotenv

from backend.agents.gemini_utils import generate_gemini_text_async
from backend.config import GEMINI_MODEL
from backend.context_manager import ContextManager
from backend.engines.crowd_risk_engine import CrowdRiskEngine


load_dotenv()


class CrowdAgent:
    def __init__(self, risk_engine: CrowdRiskEngine):
        self.risk_engine = risk_engine
        
    async def analyze(self, language: str, context: ContextManager) -> dict:
        analysis = self.risk_engine.analyze_stadium(
            context.section_occupancy,
            context.match_phase,
            context.weather,
            context.queue_times,
        )
        choke_pressure = {
            "concourse_1": self.risk_engine.compute_choke_pressure(
                "concourse_1",
                analysis["sections"],
            ),
            "concourse_2": self.risk_engine.compute_choke_pressure(
                "concourse_2",
                analysis["sections"],
            ),
        }

        prompt = f"""
You are a crowd safety officer at FIFA World Cup 2026 at MetLife Stadium.
The risk engine has computed this analysis: {json.dumps(analysis)}.
Concourse pressure: {json.dumps(choke_pressure)}.
Match phase: {context.match_phase}. Weather: {context.weather}. Time: {context.current_time}.
Explain the current crowd situation in plain terms.
List the top 3 immediate actions for venue staff.
Explain WHY each action is prioritized based on the risk scores.
Respond in {language}.
""".strip()

        ai_explanation = await generate_gemini_text_async(
            GEMINI_MODEL,
            prompt,
            analysis["summary"],
        )

        return {
            "risk_analysis": analysis,
            "choke_pressure": choke_pressure,
            "ai_explanation": ai_explanation,
            "language": language,
            "timestamp": context.current_time,
        }

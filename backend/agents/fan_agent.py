"""
Agent module for StadiumIQ: fan_agent.py.
"""

from dotenv import load_dotenv

from backend.config import GEMINI_MODEL
from backend.context_manager import ContextManager
from backend.agents.gemini_utils import generate_gemini_text_async


load_dotenv()


class FanAssistAgent:
    def __init__(self):
        pass

    async def answer(
        self,
        query: str,
        language: str,
        context: ContextManager,
        user_location: str = "unknown",
        accessibility_needs: str = "",
    ) -> str:
        occupancy_summary = ", ".join(
            f"{section}: {occupancy}%"
            for section, occupancy in context.section_occupancy.items()
        )

        system_prompt = f"""
You are FanAssist, a FIFA World Cup 2026 assistant at MetLife Stadium, NJ.
LIVE STADIUM CONTEXT:
- Time: {context.current_time} | Match Phase: {context.match_phase}
- Weather: {context.weather}
- User Location: {user_location}
- Gate Status: A={context.gate_status.get('A')} B={context.gate_status.get('B')} C={context.gate_status.get('C')} D={context.gate_status.get('D')}
- Food Court A: {context.queue_times.get('food_court_a')} min wait | Food Court B: {context.queue_times.get('food_court_b')} min wait
- Restroom North: {context.queue_times.get('restroom_north')} min wait
- Nearby Transport: {context.nearby_transport}
- Section crowd levels: {occupancy_summary}
- Accessibility needs: {accessibility_needs or 'none specified'}

RULES:
- Always recommend the shorter food queue when food is asked
- Warn about any closed gate if navigation is mentioned
- During halftime, warn that concourses are busy
- If accessibility needs are specified, prioritize ramps and elevators
- Be warm, concise, and specific - never generic
- Respond entirely in {language} (English / हिंदी / Espanol)
""".strip()

        return await generate_gemini_text_async(
            GEMINI_MODEL,
            f"{system_prompt}\n\nFan query: {query}",
            "I can help with gates, queues, routes, accessibility, and transport using the live stadium context.",
        )

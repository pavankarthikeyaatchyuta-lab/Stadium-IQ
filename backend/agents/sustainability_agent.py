"""
Sustainability agent to recommend eco-friendly actions based on context.
"""
from backend.agents.gemini_utils import generate_gemini_text_async
from backend.config import GEMINI_MODEL
from backend.context_manager import ContextManager
import google.generativeai as genai


class SustainabilityAgent:
    def __init__(self):
        self.model = genai.GenerativeModel(model_name=GEMINI_MODEL)

    async def get_eco_tip(self, language: str, context: ContextManager) -> dict:
        """Generates a sustainability recommendation based on nearby transport."""
        nearby_transport = context.nearby_transport

        prompt = f"""
You are the Sustainability Director for FIFA World Cup 2026 at MetLife Stadium.
Current transport context: {nearby_transport}.

Your task:
1. Provide a specific, actionable eco-friendly travel tip for fans leaving the stadium.
2. Suggest public transit (Metro/Shuttles) over Rideshare if public transit is not extremely full.
3. Briefly estimate the positive impact or carbon savings of this choice.
Respond entirely in {language}.
""".strip()

        ai_explanation = await generate_gemini_text_async(
            self.model,
            prompt,
            "Consider using public transit to reduce carbon emissions and ease congestion.",
        )

        return {
            "eco_tip": ai_explanation,
            "transport_context": nearby_transport,
            "language": language,
            "timestamp": context.current_time,
        }

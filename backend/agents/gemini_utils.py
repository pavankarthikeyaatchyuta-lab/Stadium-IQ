"""
Utility functions for interacting with Google Gemini AI.
Includes caching and asynchronous generation support.
"""
from backend.utils.cache import gemini_cache


def generate_gemini_text(model, prompt: str, fallback: str) -> str:
    """Synchronous generation (legacy, use async if possible)."""
    cached = gemini_cache.get(prompt)
    if cached:
        return cached
    try:
        response = model.generate_content(prompt)
        gemini_cache.set(prompt, value=response.text)
        return response.text
    except Exception as error:
        return f"{fallback}\n\nAI note: Gemini response unavailable ({error})."


async def generate_gemini_text_async(model, prompt: str, fallback: str) -> str:
    """Asynchronous generation with caching."""
    cached = gemini_cache.get(prompt)
    if cached:
        return cached
    try:
        response = await model.generate_content_async(prompt)
        gemini_cache.set(prompt, value=response.text)
        return response.text
    except Exception as error:
        return f"{fallback}\n\nAI note: Gemini response unavailable ({error})."

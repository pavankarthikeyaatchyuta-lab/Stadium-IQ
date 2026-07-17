import os
import httpx
import logging
from backend.utils.cache import gemini_cache

logger = logging.getLogger(__name__)

async def generate_gemini_text_async(model_name: str, prompt: str, fallback: str) -> str:
    """Asynchronous generation with caching using direct REST API."""
    cached = gemini_cache.get(prompt)
    if cached:
        return cached

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "dummy_key_for_testing":
        return f"{fallback}\n\nAI note: Offline test mode."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=15.0)
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            gemini_cache.set(prompt, text)
            return text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return f"{fallback}\n\nAI note: Gemini response unavailable ({e})."

def generate_gemini_text(model_name: str, prompt: str, fallback: str) -> str:
    """Synchronous generation with caching using direct REST API."""
    cached = gemini_cache.get(prompt)
    if cached:
        return cached

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "dummy_key_for_testing":
        return f"{fallback}\n\nAI note: Offline test mode."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        import requests
        response = requests.post(url, headers=headers, json=payload, timeout=15.0)
        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        gemini_cache.set(prompt, text)
        return text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return f"{fallback}\n\nAI note: Gemini response unavailable ({e})."

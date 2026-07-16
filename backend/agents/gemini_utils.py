def generate_gemini_text(model, prompt: str, fallback: str) -> str:
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as error:
        return f"{fallback}\n\nAI note: Gemini response unavailable ({error})."

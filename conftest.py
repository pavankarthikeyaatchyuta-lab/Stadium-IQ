"""
Test configuration: mocks Gemini calls so tests run offline and fast.
Deterministic engines are tested for real; only the AI explanation
layer is stubbed.
"""
import pytest


@pytest.fixture(autouse=True)
def mock_gemini_global(monkeypatch):
    async def fake_async(model, prompt, fallback):
        # We include the prompt in the response so tests can assert on what was passed to Gemini
        return f"[TEST MODE] {fallback}\nPROMPT_TEXT: {prompt}"

    def fake_sync(model, prompt, fallback):
        return f"[TEST MODE] {fallback}\nPROMPT_TEXT: {prompt}"

    import backend.agents.gemini_utils as gu
    monkeypatch.setattr(gu, "generate_gemini_text_async", fake_async)
    monkeypatch.setattr(gu, "generate_gemini_text", fake_sync)

    import backend.agents.nav_agent as nav
    monkeypatch.setattr(nav, "generate_gemini_text_async", fake_async, raising=False)

    import backend.agents.crowd_agent as crowd
    monkeypatch.setattr(crowd, "generate_gemini_text_async", fake_async, raising=False)

    import backend.agents.fan_agent as fan
    monkeypatch.setattr(fan, "generate_gemini_text_async", fake_async, raising=False)

    import backend.agents.scenario_agent as scenario
    monkeypatch.setattr(scenario, "generate_gemini_text_async", fake_async, raising=False)

    import backend.agents.copilot_agent as copilot
    monkeypatch.setattr(copilot, "generate_gemini_text_async", fake_async, raising=False)

    import backend.agents.sustainability_agent as sustainability
    monkeypatch.setattr(sustainability, "generate_gemini_text_async", fake_async, raising=False)

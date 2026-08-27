from backend.app.config import PROJECT_ROOT, ALLOWED_TTS_PROVIDERS, settings
from backend.app.services.tts.tts_manager import tts_manager


def test_health_reports_tts_without_leaking_keys():
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["audience"] == "ages 5-8"
    tts = data["tts"]
    assert tts["default_provider"] in ALLOWED_TTS_PROVIDERS
    assert "edge" in tts["providers"]
    assert "openai" in tts["providers"]
    assert "elevenlabs" in tts["providers"]
    assert tts["providers"]["edge"]["configured"] is True
    dumped = str(data)
    if settings.openai_api_key:
        assert settings.openai_api_key not in dumped
    if settings.elevenlabs_api_key:
        assert settings.elevenlabs_api_key not in dumped
    assert "openai_api_key" not in dumped


def test_env_example_documents_ai_providers():
    example = (PROJECT_ROOT / ".env.example").read_text()
    for key in (
        "TTS_PROVIDER",
        "TTS_VOICE",
        "OPENAI_API_KEY",
        "OPENAI_TTS_MODEL",
        "OPENAI_BASE_URL",
        "ELEVENLABS_API_KEY",
        "ELEVENLABS_MODEL",
    ):
        assert key in example
    assert "sk-" not in example


def test_paid_provider_falls_back_to_edge_without_keys():
    assert tts_manager.resolve_provider_name("openai") == "edge"
    assert tts_manager.resolve_provider_name("elevenlabs") == "edge"
    assert tts_manager.resolve_provider_name("edge") == "edge"

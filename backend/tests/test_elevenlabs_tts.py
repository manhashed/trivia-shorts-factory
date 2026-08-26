import pytest
from backend.app.services.tts.elevenlabs_tts_service import ElevenLabsTTSProvider
from backend.app.services.tts.tts_manager import tts_manager


@pytest.mark.anyio
async def test_synthesize_without_api_key_raises_value_error(tmp_path):
    provider = ElevenLabsTTSProvider()
    with pytest.raises(ValueError, match="ElevenLabs API key is required"):
        await provider.synthesize(
            text="hello", output_path=tmp_path / "out.wav", voice="21m00Tcm4TlvDq8ikWAM", api_key="",
        )


def test_tts_manager_resolves_elevenlabs_to_real_provider():
    provider = tts_manager.get_provider("elevenlabs")
    assert isinstance(provider, ElevenLabsTTSProvider)

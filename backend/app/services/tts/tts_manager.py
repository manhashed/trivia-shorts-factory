from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.app.services.tts.base import BaseTTSProvider
from backend.app.services.tts.edge_tts_service import EdgeTTSProvider
from backend.app.services.tts.openai_tts_service import OpenAITTSProvider
from backend.app.services.tts.elevenlabs_tts_service import ElevenLabsTTSProvider
from backend.app.config import settings, normalize_tts_provider

class TTSManager:
    """
    Unified manager and factory for all TTS providers with fallback handling and caching.
    """
    def __init__(self):
        self.providers: Dict[str, BaseTTSProvider] = {
            "edge": EdgeTTSProvider(),
            "openai": OpenAITTSProvider(),
            "elevenlabs": ElevenLabsTTSProvider(),
        }

    def get_provider(self, name: str) -> BaseTTSProvider:
        provider = self.providers.get(normalize_tts_provider(name))
        if not provider:
            return self.providers["edge"]
        return provider

    def resolve_provider_name(
        self,
        name: Optional[str],
        openai_api_key: Optional[str] = None,
        elevenlabs_api_key: Optional[str] = None,
    ) -> str:
        """Pick a working engine: requested provider if keyed, otherwise Edge."""
        requested = normalize_tts_provider(name or settings.default_tts_provider)
        if requested == "openai" and not (openai_api_key or settings.openai_api_key):
            return "edge"
        if requested == "elevenlabs" and not (elevenlabs_api_key or settings.elevenlabs_api_key):
            return "edge"
        return requested

    def list_all_voices(self) -> Dict[str, List[Dict[str, Any]]]:
        result = {}
        for name, provider in self.providers.items():
            result[name] = provider.list_voices()
        return result

    async def synthesize(
        self,
        text: str,
        output_path: Path,
        provider_name: str = "edge",
        voice: Optional[str] = None,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        openai_api_key: Optional[str] = None,
        elevenlabs_api_key: Optional[str] = None,
    ) -> float:
        resolved = self.resolve_provider_name(
            provider_name,
            openai_api_key=openai_api_key,
            elevenlabs_api_key=elevenlabs_api_key,
        )
        provider = self.get_provider(resolved)

        api_key = ""
        if resolved == "openai":
            api_key = openai_api_key or settings.openai_api_key
        elif resolved == "elevenlabs":
            api_key = elevenlabs_api_key or settings.elevenlabs_api_key

        effective_voice = voice or settings.default_voice
        return await provider.synthesize(
            text=text,
            output_path=output_path,
            voice=effective_voice,
            rate=rate,
            pitch=pitch,
            api_key=api_key
        )


tts_manager = TTSManager()

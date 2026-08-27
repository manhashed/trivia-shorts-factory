import httpx
from pathlib import Path
from typing import List, Dict, Any
from backend.app.services.tts.base import BaseTTSProvider
from backend.app.utils.ffmpeg_check import convert_mp3_to_wav


class ElevenLabsTTSProvider(BaseTTSProvider):
    AVAILABLE_VOICES = [
        {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel (Calm Narrator)", "gender": "Female", "locale": "en-US", "tags": ["calm", "narrator"]},
        {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi (Confident & Strong)", "gender": "Female", "locale": "en-US", "tags": ["confident", "strong"]},
        {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella (Soft & Friendly)", "gender": "Female", "locale": "en-US", "tags": ["soft", "friendly"]},
        {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam (Deep Male Narrator)", "gender": "Male", "locale": "en-US", "tags": ["deep", "narrator"]},
    ]

    async def synthesize(
        self, text: str, output_path: Path, voice: str = "21m00Tcm4TlvDq8ikWAM", rate: str = "+0%", pitch: str = "+0Hz", api_key: str = "",
    ) -> float:
        if not api_key:
            raise ValueError("ElevenLabs API key is required for ElevenLabs TTS provider.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_mp3 = output_path.with_suffix(".temp.mp3")
        voice_id = voice if voice in [v["id"] for v in self.AVAILABLE_VOICES] else "21m00Tcm4TlvDq8ikWAM"
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"ElevenLabs TTS API error ({resp.status_code}): {resp.text}")
            with open(temp_mp3, "wb") as f:
                f.write(resp.content)
        return convert_mp3_to_wav(temp_mp3, output_path)

    def list_voices(self) -> List[Dict[str, Any]]:
        return self.AVAILABLE_VOICES

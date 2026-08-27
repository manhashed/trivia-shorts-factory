import httpx
from pathlib import Path
from typing import List, Dict, Any
from backend.app.services.tts.base import BaseTTSProvider
from backend.app.utils.ffmpeg_check import convert_mp3_to_wav

class OpenAITTSProvider(BaseTTSProvider):
    """
    OpenAI TTS adapter supporting alloy, echo, fable, onyx, nova, and shimmer.
    """

    AVAILABLE_VOICES = [
        {"id": "nova", "name": "Nova (Friendly / Expressive)", "gender": "Female", "locale": "en-US", "tags": ["clear", "warm"]},
        {"id": "fable", "name": "Fable (Storybook British Narrator)", "gender": "Female", "locale": "en-GB", "tags": ["storybook", "accent"]},
        {"id": "alloy", "name": "Alloy (Neutral & Balanced)", "gender": "Neutral", "locale": "en-US", "tags": ["neutral", "standard"]},
        {"id": "shimmer", "name": "Shimmer (Soft & Gentle)", "gender": "Female", "locale": "en-US", "tags": ["gentle", "clear"]},
        {"id": "echo", "name": "Echo (Warm Male Host)", "gender": "Male", "locale": "en-US", "tags": ["warm", "host"]},
    ]

    async def synthesize(
        self,
        text: str,
        output_path: Path,
        voice: str = "nova",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        api_key: str = "",
    ) -> float:
        if not api_key:
            raise ValueError("OpenAI API key is required for OpenAI TTS provider.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_mp3 = output_path.with_suffix(".temp.mp3")

        # Parse speed (e.g. "+20%" -> 1.2, "-10%" -> 0.9)
        speed = 1.0
        if rate.startswith("+") and rate.endswith("%"):
            speed = 1.0 + float(rate[1:-1]) / 100.0
        elif rate.startswith("-") and rate.endswith("%"):
            speed = 1.0 - float(rate[1:-1]) / 100.0

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "tts-1",
            "input": text,
            "voice": voice if voice in [v["id"] for v in self.AVAILABLE_VOICES] else "nova",
            "speed": max(0.5, min(2.0, speed)),
            "response_format": "mp3"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("https://api.openai.com/v1/audio/speech", headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI TTS API error ({resp.status_code}): {resp.text}")
            
            with open(temp_mp3, "wb") as f:
                f.write(resp.content)

        return convert_mp3_to_wav(temp_mp3, output_path)

    def list_voices(self) -> List[Dict[str, Any]]:
        return self.AVAILABLE_VOICES

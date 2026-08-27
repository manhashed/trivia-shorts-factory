import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
STORAGE_DIR = PROJECT_ROOT / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
TEMP_DIR = STORAGE_DIR / "temp"
OUTPUTS_DIR = STORAGE_DIR / "outputs"
ASSETS_DIR = BASE_DIR / "app" / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
AUDIO_DIR = ASSETS_DIR / "audio"
IMAGES_DIR = ASSETS_DIR / "images"

# Load local secrets without committing them. Missing .env is fine.
load_dotenv(PROJECT_ROOT / ".env")

# Ensure runtime directories exist
for directory in [UPLOADS_DIR, TEMP_DIR, OUTPUTS_DIR, FONTS_DIR, AUDIO_DIR, IMAGES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

ALLOWED_TTS_PROVIDERS = ("edge", "openai", "elevenlabs")


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return default if value is None else value.strip()


def normalize_tts_provider(name: str) -> str:
    cleaned = (name or "edge").strip().lower()
    return cleaned if cleaned in ALLOWED_TTS_PROVIDERS else "edge"


class AppSettings(BaseModel):
    # App Information
    app_name: str = "Trivia & Quiz Shorts Factory (Kids 5-8)"
    version: str = "1.0.0"
    debug: bool = True

    # Video Encoding Defaults
    output_width: int = 1080
    output_height: int = 1920
    fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    video_bitrate: str = "4500k"
    audio_bitrate: str = "192k"
    pix_fmt: str = "yuv420p"

    # Default Timing Defaults
    countdown_duration: float = 3.0
    post_answer_pause: float = 1.0

    # Default Mascot & Visual Style Defaults
    mascot_name: str = "Barnaby Bear"
    font_name: str = "Fredoka-Bold.ttf"
    mascot_enabled: bool = True
    countdown_style: str = "pulse_badge"  # "pulse_badge", "radial_ring", "clean_bar"
    countdown_sfx: str = "tick_tock"     # "tick_tock", "beep", "mute"
    background_mode: str = "crop_fill"    # "crop_fill", "blur_fill"

    # Animation & Effects Defaults
    animation_style: str = "bounce"   # "bounce", "slide", "pop", "none"
    confetti_enabled: bool = True
    background_zoom: bool = True
    answer_flash: bool = True
    mascot_dance: bool = True
    audio_normalize: bool = True
    sfx_volume: float = 0.6          # 0.0-1.0

    # Concurrency
    max_concurrent_renders: int = 3

    # TTS Settings — override with .env (see .env.example)
    default_tts_provider: str = normalize_tts_provider(_env("TTS_PROVIDER", "edge"))
    default_voice: str = _env("TTS_VOICE", "en-US-AnaNeural") or "en-US-AnaNeural"
    default_rate: str = _env("TTS_RATE", "+0%") or "+0%"
    default_pitch: str = _env("TTS_PITCH", "+0Hz") or "+0Hz"

    openai_api_key: str = _env("OPENAI_API_KEY")
    openai_base_url: str = (_env("OPENAI_BASE_URL", "https://api.openai.com/v1") or "https://api.openai.com/v1").rstrip("/")
    openai_tts_model: str = _env("OPENAI_TTS_MODEL", "tts-1") or "tts-1"

    elevenlabs_api_key: str = _env("ELEVENLABS_API_KEY")
    elevenlabs_model: str = _env("ELEVENLABS_MODEL", "eleven_multilingual_v2") or "eleven_multilingual_v2"

    def is_provider_configured(self, name: str) -> bool:
        provider = normalize_tts_provider(name)
        if provider == "edge":
            return True
        if provider == "openai":
            return bool(self.openai_api_key)
        if provider == "elevenlabs":
            return bool(self.elevenlabs_api_key)
        return False

    def tts_status(self) -> dict[str, Any]:
        """Public, non-secret snapshot of which voice engines are ready."""
        default = self.default_tts_provider
        warning = None
        if default != "edge" and not self.is_provider_configured(default):
            warning = (
                f"TTS_PROVIDER={default} but its API key is missing. "
                "Jobs will fall back to free Edge TTS until a key is set."
            )
        return {
            "default_provider": default,
            "default_voice": self.default_voice,
            "warning": warning,
            "providers": {
                "edge": {
                    "label": "Microsoft Edge Neural TTS",
                    "requires_api_key": False,
                    "configured": True,
                    "cost": "free",
                },
                "openai": {
                    "label": "OpenAI TTS",
                    "requires_api_key": True,
                    "configured": bool(self.openai_api_key),
                    "cost": "paid",
                    "model": self.openai_tts_model,
                    "base_url": self.openai_base_url,
                },
                "elevenlabs": {
                    "label": "ElevenLabs",
                    "requires_api_key": True,
                    "configured": bool(self.elevenlabs_api_key),
                    "cost": "paid",
                    "model": self.elevenlabs_model,
                },
            },
        }


settings = AppSettings()

DRAFT_QUALITY = {"preset": "veryfast", "video_bitrate": "2500k"}
FINAL_QUALITY = {"preset": "medium", "video_bitrate": "6000k"}


def resolve_quality_profile(quality_tier: str) -> dict:
    return DRAFT_QUALITY if quality_tier == "draft" else FINAL_QUALITY


def resolve_encode_settings(quality_tier: str, config_bitrate: str) -> tuple[str, str]:
    """Return (preset, video_bitrate). Draft uses the cheap profile bitrate;
    final honors the caller-configured VideoRenderConfig.video_bitrate."""
    profile = resolve_quality_profile(quality_tier)
    preset = profile["preset"]
    bitrate = profile["video_bitrate"] if quality_tier == "draft" else config_bitrate
    return preset, bitrate

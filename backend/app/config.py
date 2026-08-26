import os
from pathlib import Path
from pydantic import BaseModel, Field

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

# Ensure runtime directories exist
for directory in [UPLOADS_DIR, TEMP_DIR, OUTPUTS_DIR, FONTS_DIR, AUDIO_DIR, IMAGES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class AppSettings(BaseModel):
    # App Information
    app_name: str = "Trivia & Quiz Shorts Factory (Kids 3-5)"
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

    # TTS Settings
    default_tts_provider: str = "edge"
    default_voice: str = "en-US-AnaNeural"  # Friendly child voice
    default_rate: str = "+0%"
    default_pitch: str = "+0Hz"

    # API Keys (optional overrides)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")


settings = AppSettings()

DRAFT_QUALITY = {"preset": "veryfast", "video_bitrate": "2500k"}
FINAL_QUALITY = {"preset": "medium", "video_bitrate": "6000k"}

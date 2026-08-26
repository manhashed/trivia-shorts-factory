from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class PoemItem(BaseModel):
    id: Optional[str] = None
    title: str = Field(..., min_length=1, description="Poem / Nursery Rhyme Title")
    lines: List[str] = Field(..., min_length=1, description="Lines of the poem/rhyme")
    category: Optional[str] = "Nursery Rhymes"
    theme: Optional[str] = "candy_clouds"
    mascot: Optional[str] = "bear"
    melody: Optional[str] = "twinkle_star"

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Poem title cannot be empty.")
        return cleaned

    @field_validator("lines")
    @classmethod
    def validate_lines(cls, v: List[str]) -> List[str]:
        cleaned_lines = [l.strip() for l in v if l.strip()]
        if not cleaned_lines:
            raise ValueError("Poem must have at least one non-empty line.")
        return cleaned_lines


class PoemRenderConfig(BaseModel):
    width: int = Field(1080, ge=480, le=3840)
    height: int = Field(1920, ge=480, le=3840)
    fps: int = Field(30, ge=15, le=60)
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    video_bitrate: str = "4500k"
    pix_fmt: str = "yuv420p"

    mascot_id: str = "bear" # "bear", "penguin", "lion", "bunny"
    template_id: str = "candy_clouds" # "candy_clouds", "space_galaxy", "safari_jungle", "ocean_bubbles", "arcade_retro"
    melody_track: str = "twinkle_star" # "twinkle_star", "playful_ukulele", "storybook_bells", "bouncy_march", "none"
    melody_volume: float = Field(0.20, ge=0.0, le=1.0)
    
    tts_provider: str = "edge"
    tts_voice: str = "en-US-AnaNeural"
    tts_speed: str = "+0%"
    
    # 120 BPM = 0.5s per dance step
    dance_bpm: int = Field(120, ge=60, le=180)
    karaoke_style: str = "bouncing_star" # "bouncing_star", "glow_highlight", "clean_cards"
    mix_mode: bool = False


class PoemBatchItemStatus(BaseModel):
    index: int
    id: str
    title: str
    lines: List[str]
    category: Optional[str] = None
    mascot_used: Optional[str] = None
    template_used: Optional[str] = None
    melody_used: Optional[str] = None
    voice_used: Optional[str] = None
    status: str = "queued" # "queued", "tts_processing", "rendering", "completed", "failed"
    progress: float = 0.0
    output_filename: Optional[str] = None
    video_url: Optional[str] = None
    duration: Optional[float] = None
    error: Optional[str] = None


class PoemBatchJobState(BaseModel):
    job_id: str
    created_at: str
    status: str = "pending" # "pending", "processing", "completed", "partial_failure", "failed"
    total_items: int
    completed_items: int = 0
    failed_items: int = 0
    overall_progress: float = 0.0
    items: List[PoemBatchItemStatus] = []
    zip_filename: Optional[str] = None
    zip_url: Optional[str] = None
    error: Optional[str] = None

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class TriviaItem(BaseModel):
    id: Optional[str] = None
    q: str = Field(..., min_length=1, description="Question text")
    a: str = Field(..., min_length=1, description="Answer text")
    category: Optional[str] = None
    options: Optional[List[str]] = Field(default=None, description="Optional multiple-choice options (A, B, C)")
    correct_index: Optional[int] = Field(default=None, description="Index into options that holds the correct answer")

    @field_validator("q", "a")
    @classmethod
    def strip_and_validate_non_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Question and Answer cannot be empty or whitespace only.")
        return cleaned

    @model_validator(mode="after")
    def validate_correct_index(self) -> "TriviaItem":
        if self.options:
            if self.correct_index is None:
                self.correct_index = 0
            elif not (0 <= self.correct_index < len(self.options)):
                raise ValueError(
                    f"correct_index {self.correct_index} is out of range for options of length {len(self.options)}"
                )
        else:
            self.correct_index = None
        return self

    @property
    def resolved_answer(self) -> str:
        """
        The single source of truth for the displayed/spoken answer. Never read
        `self.a` downstream for rendering or narration -- always use this.
        """
        if self.options and self.correct_index is not None:
            return self.options[self.correct_index]
        return self.a


class VideoRenderConfig(BaseModel):
    # Output Resolution & Quality
    width: int = Field(1080, ge=480, le=3840)
    height: int = Field(1920, ge=480, le=3840)
    fps: int = Field(30, ge=15, le=60)
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    video_bitrate: str = "4500k"
    pix_fmt: str = "yuv420p"
    
    # Timing
    countdown_duration: float = Field(3.0, ge=1.0, le=10.0)
    post_answer_pause: float = Field(1.0, ge=0.2, le=5.0)

    # Mascot & Templates
    mascot_id: str = "bear" # "bear", "penguin", "lion", "bunny"
    mascot_enabled: bool = True
    template_id: str = "candy_clouds" # "candy_clouds", "space_galaxy", "safari_jungle", "ocean_bubbles", "arcade_retro"
    countdown_style: str = "pulse_badge"  # "pulse_badge", "radial_ring", "clean_bar"
    countdown_sfx: str = "tick_tock"     # "tick_tock", "beep", "mute"
    background_mode: str = "crop_fill"    # "crop_fill", "blur_fill"
    
    # Batch Variety Mode (Mix mascots, themes & voices per video)
    mix_mode: bool = False
    
    # Background Music (BGM)
    bgm_track: str = "playful_nursery" # "playful_nursery", "magical_story", "none"
    bgm_volume: float = Field(0.15, ge=0.0, le=1.0)
    
    # Animation & Visual Effects
    animation_style: str = Field(default="bounce", description="Animation style: bounce, slide, pop, none")
    confetti_enabled: bool = Field(default=True, description="Enable confetti burst on answer reveal")
    background_zoom: bool = Field(default=True, description="Enable subtle Ken Burns zoom on background")
    answer_flash: bool = Field(default=True, description="Enable white flash on answer reveal")
    mascot_dance: bool = Field(default=True, description="Enable dancing mascot during answer reveal")
    audience_prompt: bool = Field(default=True, description="Invite viewers to answer out loud before the reveal")
    audio_normalize: bool = Field(default=True, description="Apply loudnorm audio normalization")
    sfx_volume: float = Field(default=0.6, ge=0.0, le=1.0, description="Sound effects volume")

    # TTS Settings
    tts_provider: str = "edge"  # "edge", "openai", "elevenlabs"
    tts_voice: str = "en-US-AnaNeural" # Friendly child voice
    tts_speed: str = "+0%"
    tts_pitch: str = "+0Hz"
    openai_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None

    @field_validator("animation_style")
    @classmethod
    def validate_animation_style(cls, v: str) -> str:
        allowed = {"bounce", "slide", "pop", "none"}
        if v not in allowed:
            raise ValueError(f"animation_style must be one of {allowed}")
        return v


class BatchItemStatus(BaseModel):
    index: int
    id: str
    question: str
    answer: str
    category: Optional[str] = None
    options: Optional[List[str]] = None
    mascot_used: Optional[str] = None
    template_used: Optional[str] = None
    voice_used: Optional[str] = None
    status: str = "queued"  # "queued", "tts_processing", "rendering", "completed", "failed"
    progress: float = 0.0
    output_filename: Optional[str] = None
    video_url: Optional[str] = None
    duration: Optional[float] = None
    error: Optional[str] = None
    action_suggestion: Optional[str] = None


class BatchJobState(BaseModel):
    job_id: str
    created_at: str
    status: str = "pending"  # "pending", "processing", "completed", "partial_failure", "failed"
    total_items: int
    completed_items: int = 0
    failed_items: int = 0
    overall_progress: float = 0.0
    items: List[BatchItemStatus] = []
    zip_filename: Optional[str] = None
    zip_url: Optional[str] = None
    error: Optional[str] = None

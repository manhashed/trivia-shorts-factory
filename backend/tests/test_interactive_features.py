import pytest
from pathlib import Path
from PIL import Image
from backend.app.config import ASSETS_DIR, TEMP_DIR, OUTPUTS_DIR
from backend.app.models.schemas import VideoRenderConfig
from backend.app.services.audio_service import audio_service
from backend.app.services.video_service import video_service
from backend.app.utils.ffmpeg_check import probe_media_file

def test_all_mascots_exist():
    mascot_dir = ASSETS_DIR / "images" / "mascots"
    for mascot_id in ["bear", "penguin", "lion", "bunny"]:
        asking = mascot_dir / f"{mascot_id}_asking.png"
        cheering = mascot_dir / f"{mascot_id}_cheering.png"
        assert asking.is_file(), f"Missing {asking.name}"
        assert cheering.is_file(), f"Missing {cheering.name}"

        # Verify PIL can open and size is 512x512
        with Image.open(asking) as img:
            assert img.size == (512, 512)
            assert img.mode == "RGBA"
        with Image.open(cheering) as img:
            assert img.size == (512, 512)
            assert img.mode == "RGBA"

def test_stock_backgrounds_exist():
    bg_dir = ASSETS_DIR / "backgrounds"
    for bg_name in ["candy_clouds.mp4", "space_galaxy.mp4", "safari_jungle.mp4", "ocean_bubbles.mp4", "arcade_retro.mp4"]:
        bg_path = bg_dir / bg_name
        assert bg_path.is_file(), f"Missing stock background {bg_name}"
        probe = probe_media_file(bg_path)
        assert probe["has_video"] is True, f"{bg_name} is not a valid video stream"
        assert probe["width"] == 1080 and probe["height"] == 1920, f"{bg_name} resolution is not 1080x1920"

@pytest.mark.anyio
async def test_render_with_lion_and_space_theme():
    test_dir = TEMP_DIR / "test_lion_space"
    test_dir.mkdir(parents=True, exist_ok=True)

    bg_path = ASSETS_DIR / "backgrounds" / "space_galaxy.mp4"
    config = VideoRenderConfig(
        mascot_id="lion",
        template_id="space_galaxy",
        bgm_track="magical_story",
        bgm_volume=0.15,
        countdown_duration=3.0,
        tts_provider="edge",
        tts_voice="en-US-GuyNeural"
    )

    q = "What planet do we live on?"
    a = "Planet Earth!"
    opts = ["Planet Earth", "Mars", "The Moon"]

    master_audio, timing = await audio_service.prepare_quiz_audio(
        question_text=q,
        answer_text=a,
        work_dir=test_dir,
        config=config
    )
    assert master_audio.is_file()

    output_mp4 = OUTPUTS_DIR / "test_lion_space.mp4"
    rendered = await video_service.render_short_video(
        bg_video_path=bg_path,
        master_audio_path=master_audio,
        timing_info=timing,
        question_text=q,
        answer_text=a,
        output_mp4_path=output_mp4,
        work_dir=test_dir,
        config=config,
        options=opts
    )

    assert rendered.is_file()
    probe = probe_media_file(rendered)
    assert probe["has_video"] is True
    assert probe["has_audio"] is True
    assert probe["width"] == 1080 and probe["height"] == 1920

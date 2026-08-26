import json
import pytest
import zipfile
from pathlib import Path
from PIL import Image

from backend.app.config import BASE_DIR, ASSETS_DIR, TEMP_DIR, OUTPUTS_DIR
from backend.app.models.poem_schemas import PoemItem, PoemRenderConfig
from backend.app.services.poem_service import poem_service
from backend.app.services.poem_job_manager import poem_job_manager
from backend.app.utils.ffmpeg_check import probe_media_file


def test_poem_bank_dataset_validity():
    bank_path = BASE_DIR / "app" / "data" / "poem_bank.json"
    assert bank_path.is_file()

    with open(bank_path, "r", encoding="utf-8") as f:
        poems = json.load(f)

    assert isinstance(poems, list)
    assert len(poems) >= 25, f"Expected at least 25 poems, got {len(poems)}"

    categories = set()
    for idx, p in enumerate(poems):
        assert "title" in p and len(p["title"].strip()) > 0, f"Poem #{idx} missing title"
        assert "lines" in p and isinstance(p["lines"], list) and len(p["lines"]) >= 2, f"Poem #{idx} has insufficient lines"
        assert "category" in p
        categories.add(p["category"])

    assert len(categories) >= 5, "Expected at least 5 categories of nursery poems"


def test_dance_sprites_and_melodies_exist():
    dance_dir = ASSETS_DIR / "images" / "mascots_dance"
    for mascot_id in ["bear", "penguin", "lion", "bunny"]:
        for frame in ["d1", "d2", "d3", "d4"]:
            sprite = dance_dir / f"{mascot_id}_{frame}.png"
            assert sprite.is_file(), f"Missing dance sprite {sprite.name}"
            with Image.open(sprite) as img:
                assert img.size == (512, 512)
                assert img.mode == "RGBA"

    melodies_dir = ASSETS_DIR / "audio" / "melodies"
    for melody in ["twinkle_star.wav", "playful_ukulele.wav", "storybook_bells.wav", "bouncy_march.wav"]:
        m_path = melodies_dir / melody
        assert m_path.is_file(), f"Missing melody {melody}"
        probe = probe_media_file(m_path)
        assert probe["has_audio"] is True


@pytest.mark.anyio
async def test_render_twinkle_star_poem_short():
    test_dir = TEMP_DIR / "test_poem_render"
    test_dir.mkdir(parents=True, exist_ok=True)

    poem = PoemItem(
        id="test_twinkle",
        title="Twinkle Twinkle Little Star",
        category="Classic Lullabies",
        theme="space_galaxy",
        mascot="bear",
        melody="twinkle_star",
        lines=[
            "Twinkle, twinkle, little star,",
            "How I wonder what you are!",
            "Up above the world so high,",
            "Like a diamond in the sky!"
        ]
    )

    config = PoemRenderConfig(
        mascot_id="bear",
        template_id="space_galaxy",
        melody_track="twinkle_star",
        melody_volume=0.20,
        tts_provider="edge",
        tts_voice="en-US-AnaNeural",
        dance_bpm=120
    )

    bg_path = ASSETS_DIR / "backgrounds" / "space_galaxy.mp4"
    output_mp4 = OUTPUTS_DIR / "test_twinkle_poem.mp4"

    rendered = await poem_service.render_poem_short(
        poem=poem,
        bg_video_path=bg_path,
        output_mp4_path=output_mp4,
        work_dir=test_dir,
        config=config,
    )

    assert rendered.is_file()
    probe = probe_media_file(rendered)
    assert probe["has_video"] is True
    assert probe["has_audio"] is True
    assert probe["width"] == 1080 and probe["height"] == 1920
    assert probe.get("duration", 0) > 5.0


@pytest.mark.anyio
async def test_poem_batch_flow():
    poems = [
        PoemItem(
            id="p_batch_1",
            title="Itsy Bitsy Spider",
            category="Fun Animals",
            theme="safari_jungle",
            mascot="bunny",
            melody="playful_ukulele",
            lines=[
                "The itsy bitsy spider climbed up the water spout,",
                "Down came the rain and washed the spider out!"
            ]
        ),
        PoemItem(
            id="p_batch_2",
            title="Humpty Dumpty",
            category="Classic Rhymes",
            theme="arcade_retro",
            mascot="penguin",
            melody="storybook_bells",
            lines=[
                "Humpty Dumpty sat on a wall,",
                "Humpty Dumpty had a great fall!"
            ]
        ),
    ]

    config = PoemRenderConfig(
        mascot_id="bear",
        template_id="candy_clouds",
        mix_mode=True
    )

    bg_path = ASSETS_DIR / "backgrounds" / "candy_clouds.mp4"
    job_state = poem_job_manager.create_job(
        poems=poems,
        bg_video_path=bg_path,
        config=config
    )

    assert len(job_state.items) == 2

    # Process batch
    await poem_job_manager._process_batch_job(job_state.job_id)

    final_state = poem_job_manager.get_job(job_state.job_id)
    assert final_state is not None
    assert final_state.status == "completed"
    assert final_state.completed_items == 2
    assert final_state.zip_filename is not None

    zip_path = OUTPUTS_DIR / final_state.zip_filename
    assert zip_path.is_file()
    with zipfile.ZipFile(zip_path, "r") as zf:
        mp4s = [f for f in zf.namelist() if f.endswith(".mp4")]
        assert len(mp4s) == 2

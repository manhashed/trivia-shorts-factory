import pytest
import zipfile
from pathlib import Path
from backend.app.config import TEMP_DIR, OUTPUTS_DIR, ASSETS_DIR
from backend.app.models.schemas import TriviaItem, VideoRenderConfig
from backend.app.services.job_manager import job_manager

@pytest.mark.anyio
async def test_mix_mode_batch_flow():
    items = [
        TriviaItem(id="m1", q="What color is a ripe banana?", a="Bright Yellow!"),
        TriviaItem(id="m2", q="Which animal says 'Moo'?", a="A Big Spotted Cow!"),
        TriviaItem(id="m3", q="How many fingers are on one hand?", a="Five Fingers!"),
        TriviaItem(id="m4", q="What shape is a pizza pie?", a="A Triangle!"),
    ]

    config = VideoRenderConfig(
        width=1080,
        height=1920,
        fps=30,
        countdown_duration=3.0,
        post_answer_pause=0.8,
        mix_mode=True, # Enable mix mode
        countdown_sfx="tick_tock",
        tts_provider="edge",
    )

    bg_default = ASSETS_DIR / "backgrounds" / "candy_clouds.mp4"
    job_state = job_manager.create_job(
        items=items,
        bg_video_path=bg_default,
        config=config
    )

    assert len(job_state.items) == 4
    # Verify rotation metadata assigned
    assert job_state.items[0].mascot_used == "bear"
    assert job_state.items[1].mascot_used == "penguin"
    assert job_state.items[2].mascot_used == "lion"
    assert job_state.items[3].mascot_used == "bunny"

    assert job_state.items[0].template_used == "candy_clouds"
    assert job_state.items[1].template_used == "space_galaxy"
    assert job_state.items[2].template_used == "safari_jungle"
    assert job_state.items[3].template_used == "ocean_bubbles"

    # Run batch rendering
    await job_manager._process_batch_job(job_state.job_id)

    final_state = job_manager.get_job(job_state.job_id)
    assert final_state is not None
    assert final_state.status == "completed"
    assert final_state.completed_items == 4
    assert final_state.failed_items == 0
    assert final_state.zip_filename is not None

    zip_path = OUTPUTS_DIR / final_state.zip_filename
    assert zip_path.is_file()
    with zipfile.ZipFile(zip_path, "r") as zf:
        mp4s = [f for f in zf.namelist() if f.endswith(".mp4")]
        assert len(mp4s) == 4

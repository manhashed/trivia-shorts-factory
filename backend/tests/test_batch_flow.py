import asyncio
import zipfile
import pytest
from backend.app.config import TEMP_DIR, OUTPUTS_DIR
from backend.app.models.schemas import TriviaItem, VideoRenderConfig
from backend.app.services.job_manager import job_manager
from backend.tests.test_prototype import create_sample_background_video

@pytest.mark.anyio
async def test_full_batch_flow():
    print("=== TESTING FULL BATCH PIPELINE ===")
    test_dir = TEMP_DIR / "batch_test"
    test_dir.mkdir(parents=True, exist_ok=True)

    bg_video = test_dir / "sample_bg.mp4"
    create_sample_background_video(bg_video, duration=4)

    items = [
        TriviaItem(id="q1", q="What animal says Meow?", a="A Kitty Cat!"),
        TriviaItem(id="q2", q="What shape is a pizza pie?", a="A Circle!"),
    ]

    config = VideoRenderConfig(
        width=1080,
        height=1920,
        fps=30,
        countdown_duration=3.0,
        post_answer_pause=0.8,
        countdown_sfx="tick_tock",
        tts_provider="edge",
        tts_voice="en-US-AnaNeural"
    )

    job_state = job_manager.create_job(
        items=items,
        bg_video_path=bg_video,
        config=config
    )
    job_id = job_state.job_id
    print(f"Created Job: {job_id}")

    # Process batch
    await job_manager._process_batch_job(job_id)

    # Validate final state
    final_state = job_manager.get_job(job_id)
    assert final_state is not None
    print(f"Final Job Status: {final_state.status}")
    print(f"Completed Items: {final_state.completed_items} / {final_state.total_items}")
    assert final_state.status == "completed"
    assert final_state.completed_items == 2
    assert final_state.failed_items == 0
    assert final_state.zip_filename is not None

    # Validate ZIP archive
    zip_path = OUTPUTS_DIR / final_state.zip_filename
    assert zip_path.is_file(), "ZIP archive was not created!"
    
    with zipfile.ZipFile(zip_path, "r") as zf:
        file_list = zf.namelist()
        print(f"ZIP Contents: {file_list}")
        assert "manifest.json" in file_list
        assert any(f.endswith(".mp4") for f in file_list)
        assert len([f for f in file_list if f.endswith(".mp4")]) == 2

    print("=== FULL BATCH PIPELINE PASSED! ===")

if __name__ == "__main__":
    asyncio.run(test_full_batch_flow())

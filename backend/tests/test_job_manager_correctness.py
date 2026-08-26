import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path

from backend.app.models.schemas import TriviaItem, VideoRenderConfig
from backend.app.services.job_manager import job_manager


def _make_mismatched_item() -> TriviaItem:
    return TriviaItem(
        id="q1",
        q="What animal says Moo?",
        a="A Big Spotted Cow!",
        options=["A Cow", "A Dog", "A Frog"],
    )


def test_create_job_uses_resolved_answer_not_free_text_a():
    item = _make_mismatched_item()
    config = VideoRenderConfig()

    state = job_manager.create_job(
        items=[item],
        bg_video_path=Path("/fake/bg.mp4"),
        config=config,
    )

    assert state.items[0].answer == "A Cow"
    assert state.items[0].answer != item.a


@pytest.mark.anyio
async def test_process_single_passes_resolved_answer_to_audio_and_video_services():
    item = _make_mismatched_item()
    config = VideoRenderConfig()

    state = job_manager.create_job(
        items=[item],
        bg_video_path=Path("/fake/bg.mp4"),
        config=config,
    )
    job_id = state.job_id

    fake_timing = {
        "t_countdown_start": 1.0,
        "t_countdown_end": 4.0,
        "t_answer_start": 4.0,
        "total_duration": 8.0,
        "countdown_duration": 3.0,
    }

    with patch(
        "backend.app.services.job_manager.audio_service.prepare_quiz_audio",
        new=AsyncMock(return_value=(Path("/fake/master_audio.wav"), fake_timing)),
    ) as mock_audio, patch(
        "backend.app.services.job_manager.video_service.render_short_video",
        new=AsyncMock(return_value=Path("/fake/output.mp4")),
    ) as mock_video, patch(
        "backend.app.services.job_manager.probe_media_file",
        return_value={"has_video": True, "duration": 8.0},
    ):
        await job_manager._process_batch_job(job_id)

    mock_audio.assert_awaited_once()
    mock_video.assert_awaited_once()
    assert mock_audio.call_args.kwargs["answer_text"] == "A Cow"
    assert mock_video.call_args.kwargs["answer_text"] == "A Cow"

    final_state = job_manager.get_job(job_id)
    assert final_state.status == "completed"

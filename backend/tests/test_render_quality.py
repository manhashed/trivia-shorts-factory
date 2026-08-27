# backend/tests/test_render_quality.py
import pytest
from unittest.mock import patch, MagicMock

from backend.app.config import DRAFT_QUALITY, FINAL_QUALITY, ASSETS_DIR
from backend.app.services.video_service import VideoService
from backend.app.models.schemas import VideoRenderConfig


def test_draft_and_final_quality_profiles_are_distinct():
    assert DRAFT_QUALITY["preset"] != FINAL_QUALITY["preset"]
    assert DRAFT_QUALITY["video_bitrate"] != FINAL_QUALITY["video_bitrate"]


@pytest.mark.anyio
async def test_render_short_video_draft_tier_uses_veryfast_preset(tmp_path):
    fake_result = MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = ""
    fake_result.stderr = ""

    fake_timing = {
        "t_countdown_start": 1.0,
        "t_countdown_end": 4.0,
        "t_answer_start": 4.0,
        "total_duration": 8.0,
        "countdown_duration": 3.0,
    }

    with patch("backend.app.services.video_service.subprocess.run", return_value=fake_result) as mock_run:
        service = VideoService()
        await service.render_short_video(
            bg_video_path=ASSETS_DIR / "backgrounds" / "candy_clouds.mp4",
            master_audio_path=tmp_path / "master_audio.wav",
            timing_info=fake_timing,
            question_text="What animal says Moo?",
            answer_text="A Cow",
            output_mp4_path=tmp_path / "out.mp4",
            work_dir=tmp_path / "work",
            config=VideoRenderConfig(),
            options=None,
            correct_index=None,
            quality_tier="draft",
        )

    called_cmd = mock_run.call_args[0][0]
    assert "veryfast" in called_cmd
    assert "medium" not in called_cmd
    assert "2500k" in called_cmd
    filter_complex = called_cmd[called_cmd.index("-filter_complex") + 1]
    assert "ANSWER" in filter_complex
    assert "FUN FACT" not in filter_complex


@pytest.mark.anyio
async def test_render_short_video_final_tier_uses_config_bitrate(tmp_path):
    fake_result = MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = ""
    fake_result.stderr = ""

    fake_timing = {
        "t_countdown_start": 1.0,
        "t_countdown_end": 4.0,
        "t_answer_start": 4.0,
        "total_duration": 8.0,
        "countdown_duration": 3.0,
    }

    with patch("backend.app.services.video_service.subprocess.run", return_value=fake_result) as mock_run:
        service = VideoService()
        await service.render_short_video(
            bg_video_path=ASSETS_DIR / "backgrounds" / "candy_clouds.mp4",
            master_audio_path=tmp_path / "master_audio.wav",
            timing_info=fake_timing,
            question_text="What animal says Moo?",
            answer_text="A Cow",
            output_mp4_path=tmp_path / "out.mp4",
            work_dir=tmp_path / "work",
            config=VideoRenderConfig(video_bitrate="8000k"),
            options=None,
            correct_index=None,
            quality_tier="final",
        )

    called_cmd = mock_run.call_args[0][0]
    assert "medium" in called_cmd
    assert "8000k" in called_cmd
    assert "2500k" not in called_cmd

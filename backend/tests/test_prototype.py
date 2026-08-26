import asyncio
import subprocess
from pathlib import Path
from backend.app.config import TEMP_DIR, OUTPUTS_DIR
from backend.app.models.schemas import VideoRenderConfig
from backend.app.services.audio_service import audio_service
from backend.app.services.video_service import video_service
from backend.app.utils.ffmpeg_check import get_ffmpeg_binary, probe_media_file


def create_sample_background_video(output_path: Path, duration: int = 5) -> Path:
    """Generates a 5-second colorful animated background MP4 for testing."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    ffmpeg_bin = get_ffmpeg_binary()
    
    # Generate animated colorful background (1080x1920, 30fps)
    cmd = [
        ffmpeg_bin, "-y",
        "-f", "lavfi",
        "-i", f"testsrc2=size=1080x1920:rate=30:duration={duration}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return output_path


async def run_prototype_test():
    print("=== STARTING PHASE 3 PROTOTYPE VALIDATION ===")
    test_dir = TEMP_DIR / "prototype_test"
    test_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create sample background video
    bg_video = test_dir / "sample_bg.mp4"
    if not bg_video.is_file():
        print("Generating 5s test background video...")
        create_sample_background_video(bg_video, duration=5)
    print(f"Background video ready: {bg_video}")

    # 2. Configure Render
    config = VideoRenderConfig(
        width=1080,
        height=1920,
        fps=30,
        countdown_duration=3.0,
        post_answer_pause=1.0,
        countdown_sfx="tick_tock",
        tts_provider="edge",
        tts_voice="en-US-AnaNeural"
    )

    q_text = "What color is the sun?"
    a_text = "Yellow and Bright!"

    # 3. Audio synthesis & timing calculation
    print(f"Synthesizing audio for Q: '{q_text}' and A: '{a_text}'...")
    master_audio, timing = await audio_service.prepare_quiz_audio(
        question_text=q_text,
        answer_text=a_text,
        work_dir=test_dir,
        config=config,
    )
    print(f"Audio timing calculated:")
    for k, v in timing.items():
        print(f"  - {k}: {v}")

    # 4. Render Video
    output_mp4 = OUTPUTS_DIR / "prototype_quiz_sample.mp4"
    print(f"Rendering video overlay to: {output_mp4}...")
    result_path = await video_service.render_short_video(
        bg_video_path=bg_video,
        master_audio_path=master_audio,
        timing_info=timing,
        question_text=q_text,
        answer_text=a_text,
        output_mp4_path=output_mp4,
        work_dir=test_dir,
        config=config,
    )

    print(f"Video rendered successfully at: {result_path}")

    # 5. Verify Output
    probe = probe_media_file(result_path)
    print("Output Video Probe:")
    print(f"  - Duration: {probe['duration']}s (Expected approx {timing['total_duration']}s)")
    print(f"  - Dimensions: {probe['width']}x{probe['height']} (Expected 1080x1920)")
    print(f"  - Has Video: {probe['has_video']}")
    print(f"  - Has Audio: {probe['has_audio']}")
    print(f"  - File size: {result_path.stat().st_size} bytes")

    assert probe["has_video"], "Generated file has no video stream!"
    assert probe["has_audio"], "Generated file has no audio stream!"
    assert probe["width"] == 1080 and probe["height"] == 1920, "Resolution mismatch!"
    assert abs(probe["duration"] - timing["total_duration"]) < 0.5, "Duration mismatch!"
    print("=== PROTOTYPE VALIDATION PASSED! ===")


if __name__ == "__main__":
    asyncio.run(run_prototype_test())

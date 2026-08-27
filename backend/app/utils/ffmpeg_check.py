import subprocess
import shutil
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

try:
    import imageio_ffmpeg
    IMAGEIO_FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    IMAGEIO_FFMPEG_PATH = None


def get_ffmpeg_binary() -> str:
    """Returns the path to the ffmpeg executable."""
    # 1. System path
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    
    # 2. ImageIO bundled ffmpeg
    if IMAGEIO_FFMPEG_PATH and Path(IMAGEIO_FFMPEG_PATH).is_file():
        return IMAGEIO_FFMPEG_PATH
    
    # 3. Fallback common paths
    for candidate in ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg"]:
        if Path(candidate).is_file():
            return candidate
            
    raise RuntimeError("FFmpeg executable not found. Please install ffmpeg or imageio-ffmpeg.")


def probe_media_file(file_path: Path) -> Dict[str, Any]:
    """Probes a video or audio file and returns duration, width, height, fps."""
    ffmpeg_bin = get_ffmpeg_binary()
    
    # Run ffmpeg -i to extract metadata
    cmd = [ffmpeg_bin, "-i", str(file_path)]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stderr = result.stderr

    info: Dict[str, Any] = {
        "duration": 0.0,
        "width": 0,
        "height": 0,
        "fps": 30.0,
        "has_video": False,
        "has_audio": False,
    }

    # Extract Duration: 00:00:05.42, start: ...
    duration_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr)
    if duration_match:
        hours = float(duration_match.group(1))
        minutes = float(duration_match.group(2))
        seconds = float(duration_match.group(3))
        info["duration"] = hours * 3600 + minutes * 60 + seconds

    # Extract Video stream resolution and fps: Stream #0:0... Video: ..., 1920x1080 [SAR 1:1 DAR 16:9], 30 fps
    video_match = re.search(r"Video:.*,\s*(\d{2,5})x(\d{2,5})", stderr)
    if video_match:
        info["has_video"] = True
        info["width"] = int(video_match.group(1))
        info["height"] = int(video_match.group(2))

    fps_match = re.search(r"(\d+(?:\.\d+)?)\s*fps", stderr)
    if fps_match:
        info["fps"] = float(fps_match.group(1))

    if "Audio:" in stderr:
        info["has_audio"] = True

    return info


def convert_mp3_to_wav(temp_mp3: Path, output_path: Path) -> float:
    """Transcode an mp3 (or any ffmpeg-readable audio file) to 44.1kHz stereo PCM WAV.
    On ffmpeg failure, falls back to renaming the source into place so callers still
    get a file to probe. Returns a clamped duration suitable for TTS timing.
    """
    ffmpeg_bin = get_ffmpeg_binary()
    cmd = [
        ffmpeg_bin, "-y", "-i", str(temp_mp3),
        "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(output_path),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0 and temp_mp3.exists():
        temp_mp3.rename(output_path)
    elif temp_mp3.exists():
        temp_mp3.unlink()

    probe = probe_media_file(output_path)
    return max(0.2, probe.get("duration", 0.0))

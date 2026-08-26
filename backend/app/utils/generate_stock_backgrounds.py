import subprocess
from pathlib import Path
from backend.app.config import ASSETS_DIR, UPLOADS_DIR
from backend.app.utils.ffmpeg_check import get_ffmpeg_binary

def generate_stock_backgrounds(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_bin = get_ffmpeg_binary()

    templates = [
        ("candy_clouds.mp4", "testsrc2=size=1080x1920:rate=30:duration=6"),
        ("space_galaxy.mp4", "life=s=1080x1920:mold=10:rate=30:stay_rule=23:born_rule=3,format=yuv420p"),
        ("safari_jungle.mp4", "gradients=s=1080x1920:c0=0x064e3b:c1=0x047857:c2=0x059669:c3=0x10b981:duration=6:speed=0.01"),
        ("ocean_bubbles.mp4", "gradients=s=1080x1920:c0=0x082f49:c1=0x0369a1:c2=0x0284c7:c3=0x38bdf8:duration=6:speed=0.015"),
        ("arcade_retro.mp4", "smptebars=size=1080x1920:rate=30:duration=6"),
    ]

    for filename, filter_src in templates:
        target = output_dir / filename
        if target.exists():
            target.unlink()

        # Generate smooth 6-second looping 1080x1920 H.264 video
        cmd = [
            ffmpeg_bin, "-y",
            "-f", "lavfi",
            "-i", filter_src,
            "-t", "6",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            str(target)
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            # Fallback to testsrc2 if specific filter is unavailable in current ffmpeg build
            cmd_fallback = [
                ffmpeg_bin, "-y",
                "-f", "lavfi",
                "-i", "testsrc2=size=1080x1920:rate=30:duration=6",
                "-t", "6",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(target)
            ]
            subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        print(f"Generated stock background: {filename}")


if __name__ == "__main__":
    bg_dir = ASSETS_DIR / "backgrounds"
    generate_stock_backgrounds(bg_dir)

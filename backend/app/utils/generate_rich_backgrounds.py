import math
import random
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from backend.app.config import ASSETS_DIR, UPLOADS_DIR, TEMP_DIR
from backend.app.utils.ffmpeg_check import get_ffmpeg_binary

WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION = 6  # 6 seconds loop
TOTAL_FRAMES = FPS * DURATION


def draw_vertical_gradient(draw: ImageDraw.ImageDraw, top_color: tuple, bottom_color: tuple):
    """Draws a smooth vertical gradient."""
    for y in range(0, HEIGHT, 4):
        ratio = y / HEIGHT
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.rectangle([0, y, WIDTH, y + 4], fill=(r, g, b, 255))


def generate_candy_clouds_video(output_mp4: Path, work_dir: Path):
    """
    Generates a gorgeous high-retention kids 5–8 background:
    Pastel sky gradient + floating fluffy white clouds + floating colorful balloons & stars.
    """
    frames_dir = work_dir / "candy_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Cloud definitions: (base_x, y, speed, scale, color)
    clouds = [
        {"x": 100, "y": 250, "speed": 1.2, "w": 280, "h": 120},
        {"x": 600, "y": 420, "speed": 0.8, "w": 340, "h": 140},
        {"x": 200, "y": 800, "speed": 1.5, "w": 300, "h": 130},
        {"x": 750, "y": 1100, "speed": 1.0, "w": 320, "h": 135},
        {"x": 150, "y": 1450, "speed": 1.3, "w": 360, "h": 150},
        {"x": 700, "y": 1700, "speed": 0.9, "w": 280, "h": 120},
    ]

    # Floating stars / sparkle bubbles: (x, base_y, speed, size, color)
    stars = [
        {"x": 180, "y": 350, "speed": 0.6, "size": 18, "pulse": 0.0},
        {"x": 900, "y": 550, "speed": 0.9, "size": 24, "pulse": 1.5},
        {"x": 250, "y": 950, "speed": 0.7, "size": 22, "pulse": 3.0},
        {"x": 850, "y": 1300, "speed": 0.8, "size": 26, "pulse": 4.5},
        {"x": 120, "y": 1600, "speed": 0.5, "size": 20, "pulse": 2.0},
        {"x": 920, "y": 1800, "speed": 1.1, "size": 22, "pulse": 0.8},
    ]

    # Floating candy balloons: (base_x, base_y, float_speed, sway_freq, color)
    balloons = [
        {"x": 150, "y": 1900, "speed": 2.5, "sway": 1.0, "color": (251, 113, 133, 230), "r": 45},
        {"x": 920, "y": 2100, "speed": 2.8, "sway": 1.2, "color": (250, 204, 21, 230), "r": 50},
        {"x": 300, "y": 2300, "speed": 2.2, "sway": 0.9, "color": (56, 189, 248, 230), "r": 42},
        {"x": 800, "y": 2500, "speed": 2.6, "sway": 1.1, "color": (168, 85, 247, 230), "r": 48},
    ]

    for frame_idx in range(TOTAL_FRAMES):
        t = frame_idx / FPS
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
        d = ImageDraw.Draw(img)

        # 1. Warm pastel sky gradient (Cyan top -> Soft Coral pink bottom)
        draw_vertical_gradient(d, (56, 189, 248), (244, 114, 182))

        # 2. Draw animated fluffy clouds with soft drop shadows
        for c in clouds:
            cx = (c["x"] + frame_idx * c["speed"] * 1.5) % (WIDTH + 400) - 200
            cy = c["y"] + math.sin(t * 1.5 + c["y"]) * 8
            w, h = c["w"], c["h"]

            # Shadow
            d.ellipse([cx - w//2 + 8, cy - h//2 + 10, cx + w//2 + 8, cy + h//2 + 10], fill=(0, 0, 0, 25))
            # Cloud puffs
            d.ellipse([cx - w//2, cy - h//2 + 15, cx + w//2, cy + h//2], fill=(255, 255, 255, 240))
            d.ellipse([cx - w//4, cy - h//2 - 10, cx + w//6, cy + h//3], fill=(255, 255, 255, 250))
            d.ellipse([cx, cy - h//2 - 5, cx + w//3, cy + h//3], fill=(255, 255, 255, 250))

        # 3. Draw animated floating balloons
        for b in balloons:
            bx = b["x"] + math.sin(t * b["sway"] * 2.0) * 25
            by = (b["y"] - frame_idx * b["speed"] * 2.5) % (HEIGHT + 400) - 100
            br = b["r"]
            # Balloon body
            d.ellipse([bx - br, by - br, bx + br, by + br], fill=b["color"])
            # Balloon highlight
            d.ellipse([bx - br//2, by - br//2, bx - br//5, by - br//5], fill=(255, 255, 255, 180))
            # String
            d.line([(bx, by + br), (bx + math.sin(t * 3) * 6, by + br + 45)], fill=(255, 255, 255, 140), width=2)

        # 4. Draw twinkling golden stars
        for s in stars:
            sx = s["x"]
            sy = s["y"] + math.sin(t * 2.0 + s["pulse"]) * 12
            rad = s["size"] * (0.8 + 0.3 * math.sin(t * 4.0 + s["pulse"]))
            # 4-point star
            d.ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=(254, 240, 138, 220))
            d.ellipse([sx - rad/2, sy - rad/2, sx + rad/2, sy + rad/2], fill=(255, 255, 255, 255))

        frame_file = frames_dir / f"frame_{frame_idx:04d}.png"
        img.save(frame_file, "PNG")

    # Encode to seamless looping MP4
    ffmpeg_bin = get_ffmpeg_binary()
    cmd = [
        ffmpeg_bin, "-y",
        "-r", str(FPS),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(output_mp4)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # Clean temporary frame files
    import shutil
    shutil.rmtree(frames_dir, ignore_errors=True)
    print(f"Rendered gorgeous candy clouds background: {output_mp4}")


def generate_space_galaxy_video(output_mp4: Path, work_dir: Path):
    """
    Generates Cosmic Space background:
    Deep indigo/purple gradient + moving starfield + glowing rocket & Saturn planet.
    """
    frames_dir = work_dir / "space_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    # 40 twinkling stars
    random.seed(42)
    stars = [
        {"x": random.randint(40, WIDTH - 40), "y": random.randint(40, HEIGHT - 40), "r": random.randint(4, 12), "speed": random.uniform(2.0, 6.0), "phase": random.uniform(0, 6.28)}
        for _ in range(40)
    ]

    for frame_idx in range(TOTAL_FRAMES):
        t = frame_idx / FPS
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
        d = ImageDraw.Draw(img)

        # Deep cosmic gradient (Midnight Violet -> Deep Galactic Navy)
        draw_vertical_gradient(d, (15, 23, 42), (49, 46, 129))

        # Saturn planet (top right)
        px, py = 880, 320 + math.sin(t * 1.2) * 15
        d.ellipse([px - 70, py - 70, px + 70, py + 70], fill=(245, 158, 11, 240))
        d.ellipse([px - 60, py - 60, px + 60, py + 60], fill=(251, 191, 36, 255))
        # Planetary Ring
        d.arc([px - 130, py - 40, px + 130, py + 40], start=160, end=380, fill=(253, 230, 138, 200), width=12)

        # Twinkling Stars
        for s in stars:
            brightness = 0.5 + 0.5 * math.sin(t * s["speed"] + s["phase"])
            rad = s["r"] * brightness
            alpha = int(150 + 105 * brightness)
            d.ellipse([s["x"] - rad, s["y"] - rad, s["x"] + rad, s["y"] + rad], fill=(224, 231, 255, alpha))
            if rad > 6:
                d.ellipse([s["x"] - rad/2, s["y"] - rad/2, s["x"] + rad/2, s["y"] + rad/2], fill=(255, 255, 255, alpha))

        # Floating cute rocket (bottom-left to top-right path)
        rx = (frame_idx * 4.5) % (WIDTH + 300) - 150
        ry = 1500 - (frame_idx * 3.5) % (HEIGHT + 300)
        # Rocket flame
        flame_len = 25 + math.sin(t * 20) * 8
        d.polygon([(rx - 15, ry + 25), (rx + 15, ry + 25), (rx, ry + 25 + flame_len)], fill=(239, 68, 68, 240))
        d.polygon([(rx - 8, ry + 25), (rx + 8, ry + 25), (rx, ry + 25 + flame_len * 0.6)], fill=(250, 204, 21, 255))
        # Rocket body
        d.ellipse([rx - 20, ry - 35, rx + 20, ry + 25], fill=(248, 250, 252, 255))
        d.polygon([(rx - 20, ry), (rx, ry - 45), (rx + 20, ry)], fill=(59, 130, 246, 255))
        d.ellipse([rx - 8, ry - 10, rx + 8, ry + 6], fill=(56, 189, 248, 255))

        frame_file = frames_dir / f"frame_{frame_idx:04d}.png"
        img.save(frame_file, "PNG")

    ffmpeg_bin = get_ffmpeg_binary()
    cmd = [
        ffmpeg_bin, "-y",
        "-r", str(FPS),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(output_mp4)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    import shutil
    shutil.rmtree(frames_dir, ignore_errors=True)
    print(f"Rendered gorgeous cosmic space background: {output_mp4}")


def generate_safari_jungle_video(output_mp4: Path, work_dir: Path):
    """
    Generates Safari Jungle background:
    Lush emerald gradient + waving palm fronds + floating golden fireflies.
    """
    frames_dir = work_dir / "safari_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    random.seed(99)
    fireflies = [
        {"x": random.randint(60, WIDTH - 60), "y": random.randint(100, HEIGHT - 100), "speed": random.uniform(1.0, 3.0), "phase": random.uniform(0, 6.28)}
        for _ in range(25)
    ]

    for frame_idx in range(TOTAL_FRAMES):
        t = frame_idx / FPS
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
        d = ImageDraw.Draw(img)

        # Tropical jungle gradient (Warm Forest Green -> Deep Safari Gold)
        draw_vertical_gradient(d, (6, 78, 59), (161, 98, 7))

        # Big waving jungle leaves at borders
        for leaf_y in [180, 650, 1100, 1600]:
            sway = math.sin(t * 1.5 + leaf_y) * 15
            # Left leaf
            d.chord([-100, leaf_y - 120 + int(sway), 250, leaf_y + 120 + int(sway)], start=270, end=90, fill=(16, 185, 129, 140))
            d.chord([-120, leaf_y - 80 + int(sway), 200, leaf_y + 80 + int(sway)], start=270, end=90, fill=(34, 197, 94, 180))
            # Right leaf
            d.chord([WIDTH - 250, leaf_y - 80 - int(sway), WIDTH + 100, leaf_y + 160 - int(sway)], start=90, end=270, fill=(16, 185, 129, 140))
            d.chord([WIDTH - 200, leaf_y - 50 - int(sway), WIDTH + 120, leaf_y + 120 - int(sway)], start=90, end=270, fill=(34, 197, 94, 180))

        # Floating glowing golden fireflies
        for f in fireflies:
            fx = f["x"] + math.sin(t * 2.0 + f["phase"]) * 20
            fy = (f["y"] - frame_idx * f["speed"]) % HEIGHT
            pulse = 0.5 + 0.5 * math.sin(t * 5.0 + f["phase"])
            rad = 8 + int(pulse * 6)
            d.ellipse([fx - rad, fy - rad, fx + rad, fy + rad], fill=(254, 240, 138, int(160 * pulse)))
            d.ellipse([fx - 3, fy - 3, fx + 3, fy + 3], fill=(255, 255, 255, 240))

        frame_file = frames_dir / f"frame_{frame_idx:04d}.png"
        img.save(frame_file, "PNG")

    ffmpeg_bin = get_ffmpeg_binary()
    cmd = [
        ffmpeg_bin, "-y",
        "-r", str(FPS),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(output_mp4)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    import shutil
    shutil.rmtree(frames_dir, ignore_errors=True)
    print(f"Rendered gorgeous safari jungle background: {output_mp4}")


def generate_ocean_bubbles_video(output_mp4: Path, work_dir: Path):
    """
    Generates Ocean Odyssey background:
    Deep cyan ocean gradient + rising translucent bubbles + swimming colorful fish.
    """
    frames_dir = work_dir / "ocean_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    random.seed(77)
    bubbles = [
        {"x": random.randint(80, WIDTH - 80), "base_y": random.randint(100, HEIGHT + 400), "speed": random.uniform(2.5, 5.5), "r": random.randint(12, 36), "sway": random.uniform(1.0, 2.5)}
        for _ in range(30)
    ]

    for frame_idx in range(TOTAL_FRAMES):
        t = frame_idx / FPS
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
        d = ImageDraw.Draw(img)

        # Deep Ocean Gradient (Aquamarine -> Deep Trench Blue)
        draw_vertical_gradient(d, (14, 165, 233), (3, 105, 161))

        # Swimming Cute Orange Clownfish (swims left to right)
        fish_x = (frame_idx * 5) % (WIDTH + 300) - 150
        fish_y = 650 + math.sin(t * 3.0) * 20
        # Tail
        d.polygon([(fish_x - 45, fish_y - 20), (fish_x - 45, fish_y + 20), (fish_x - 15, fish_y)], fill=(249, 115, 22, 255))
        # Body
        d.ellipse([fish_x - 30, fish_y - 25, fish_x + 35, fish_y + 25], fill=(249, 115, 22, 255))
        # White Stripes
        d.chord([fish_x - 5, fish_y - 24, fish_x + 10, fish_y + 24], start=270, end=90, fill=(255, 255, 255, 255))
        # Eye
        d.ellipse([fish_x + 15, fish_y - 12, fish_x + 25, fish_y - 2], fill=(15, 23, 42, 255))
        d.ellipse([fish_x + 18, fish_y - 10, fish_x + 22, fish_y - 6], fill=(255, 255, 255, 255))

        # Rising Translucent Bubbles
        for b in bubbles:
            bx = b["x"] + math.sin(t * b["sway"] * 3.0) * 15
            by = (b["base_y"] - frame_idx * b["speed"] * 2.0) % (HEIGHT + 100)
            br = b["r"]
            # Bubble ring
            d.ellipse([bx - br, by - br, bx + br, by + br], fill=(255, 255, 255, 45), outline=(255, 255, 255, 180), width=3)
            # Glint
            d.ellipse([bx - br//2, by - br//2, bx - br//5, by - br//5], fill=(255, 255, 255, 200))

        frame_file = frames_dir / f"frame_{frame_idx:04d}.png"
        img.save(frame_file, "PNG")

    ffmpeg_bin = get_ffmpeg_binary()
    cmd = [
        ffmpeg_bin, "-y",
        "-r", str(FPS),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(output_mp4)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    import shutil
    shutil.rmtree(frames_dir, ignore_errors=True)
    print(f"Rendered gorgeous ocean bubbles background: {output_mp4}")


def generate_arcade_retro_video(output_mp4: Path, work_dir: Path):
    """
    Generates Arcade Game Show background:
    High energy retro purple/gold grid + bouncing arcade stars & flashing neon marquee.
    """
    frames_dir = work_dir / "arcade_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    for frame_idx in range(TOTAL_FRAMES):
        t = frame_idx / FPS
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
        d = ImageDraw.Draw(img)

        # Retro Neon Gradient (Neon Violet -> Deep Crimson)
        draw_vertical_gradient(d, (88, 28, 135), (159, 18, 57))

        # Flashing Marquee Bulbs on Left and Right borders
        for bulb_y in range(80, HEIGHT - 80, 80):
            bulb_phase = (bulb_y // 80 + frame_idx // 4) % 3
            bulb_color = (250, 204, 21, 255) if bulb_phase == 0 else (239, 68, 68, 255) if bulb_phase == 1 else (56, 189, 248, 255)
            # Left bulb
            d.ellipse([30, bulb_y, 65, bulb_y + 35], fill=bulb_color)
            d.ellipse([38, bulb_y + 8, 48, bulb_y + 18], fill=(255, 255, 255, 200))
            # Right bulb
            d.ellipse([WIDTH - 65, bulb_y, WIDTH - 30, bulb_y + 35], fill=bulb_color)
            d.ellipse([WIDTH - 57, bulb_y + 8, WIDTH - 47, bulb_y + 18], fill=(255, 255, 255, 200))

        # Bouncing Gold Star Coins in background
        for coin_idx, coin_x in enumerate([250, 540, 830]):
            coin_y = 1400 + math.sin(t * 3.0 + coin_idx * 1.5) * 40
            d.ellipse([coin_x - 35, coin_y - 35, coin_x + 35, coin_y + 35], fill=(250, 204, 21, 200), outline=(245, 158, 11, 255), width=4)
            d.ellipse([coin_x - 15, coin_y - 15, coin_x + 15, coin_y + 15], fill=(254, 240, 138, 255))

        frame_file = frames_dir / f"frame_{frame_idx:04d}.png"
        img.save(frame_file, "PNG")

    ffmpeg_bin = get_ffmpeg_binary()
    cmd = [
        ffmpeg_bin, "-y",
        "-r", str(FPS),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(output_mp4)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    import shutil
    shutil.rmtree(frames_dir, ignore_errors=True)
    print(f"Rendered gorgeous arcade retro background: {output_mp4}")


def generate_all_rich_backgrounds(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir = TEMP_DIR / "rich_bg_render"
    work_dir.mkdir(parents=True, exist_ok=True)

    generate_candy_clouds_video(output_dir / "candy_clouds.mp4", work_dir)
    generate_space_galaxy_video(output_dir / "space_galaxy.mp4", work_dir)
    generate_safari_jungle_video(output_dir / "safari_jungle.mp4", work_dir)
    generate_ocean_bubbles_video(output_dir / "ocean_bubbles.mp4", work_dir)
    generate_arcade_retro_video(output_dir / "arcade_retro.mp4", work_dir)

    print(f"All 5 rich animated backgrounds generated successfully in {output_dir}")


if __name__ == "__main__":
    generate_all_rich_backgrounds(ASSETS_DIR / "backgrounds")

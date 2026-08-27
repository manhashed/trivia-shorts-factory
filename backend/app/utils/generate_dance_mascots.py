import math
from pathlib import Path
from PIL import Image, ImageDraw
from backend.app.config import ASSETS_DIR

CANVAS_SIZE = (512, 512)
POEM_AMPLITUDE = 0.4


def draw_musical_notes(d: ImageDraw.ImageDraw, x: int, y: int, color: tuple):
    """Draws cute floating musical notes."""
    d.ellipse([x - 12, y - 10, x + 6, y + 6], fill=color)
    d.line([(x + 4, y), (x + 4, y - 35)], fill=color, width=4)
    d.line([(x + 4, y - 35), (x + 22, y - 30)], fill=color, width=5)


def _draw_limb(d: ImageDraw.ImageDraw, body_cx: float, body_cy: float, dx: float, dy: float, amplitude: float, radius: float, fill: tuple) -> None:
    cx = body_cx + dx * amplitude
    cy = body_cy + dy * amplitude
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=fill)


def _draw_pose_1_step_left(fur: tuple, inner: tuple, accent: tuple, amplitude: float = 1.0) -> Image.Image:
    """Pose 1: Step Left & Sing. Body/head fixed; left/right paw and the
    musical note displace from their body/nose anchor scaled by amplitude."""
    img = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body_cx, body_cy = 250, 340
    nose_cx, nose_cy = 245, 167

    d.ellipse([140, 210, 360, 470], fill=fur)
    d.ellipse([180, 260, 320, 440], fill=inner)
    d.ellipse([125, 60, 365, 280], fill=fur)
    d.ellipse([175, 140, 315, 255], fill=inner)
    d.arc([190, 130, 235, 165], start=180, end=360, fill=(30, 41, 59), width=5)
    d.ellipse([270, 135, 290, 155], fill=(30, 41, 59))
    d.ellipse([275, 138, 283, 146], fill=(255, 255, 255))
    d.ellipse([225, 180, 265, 225], fill=(225, 29, 72))
    d.ellipse([235, 195, 255, 215], fill=(255, 182, 193))
    d.ellipse([235, 160, 255, 175], fill=(30, 41, 59))

    _draw_limb(d, body_cx, body_cy, -127.5, -122.5, amplitude, 37.5, fur)
    _draw_limb(d, body_cx, body_cy, 132.5, -2.5, amplitude, 37.5, fur)

    note_x, note_y = nose_cx + (-165) * amplitude, nose_cy + (-17) * amplitude
    draw_musical_notes(d, int(note_x), int(note_y), accent)

    return img


def _draw_pose_2_head_high(fur: tuple, inner: tuple, accent: tuple, amplitude: float = 1.0) -> Image.Image:
    """Pose 2: Big Singing Mouth Open & Head High. Both paws raised and the
    two musical notes displace from a nose-anchor point scaled by amplitude."""
    img = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body_cx, body_cy = 256, 330
    nose_cx, nose_cy = 255, 162.5

    d.ellipse([146, 200, 366, 460], fill=fur)
    d.ellipse([186, 250, 326, 430], fill=inner)
    d.ellipse([136, 50, 376, 270], fill=fur)
    d.ellipse([186, 130, 326, 245], fill=inner)
    d.arc([190, 125, 235, 160], start=180, end=360, fill=(30, 41, 59), width=6)
    d.arc([275, 125, 320, 160], start=180, end=360, fill=(30, 41, 59), width=6)
    d.ellipse([215, 170, 295, 235], fill=(225, 29, 72))
    d.ellipse([230, 195, 280, 230], fill=(255, 182, 193))
    d.ellipse([245, 155, 265, 170], fill=(30, 41, 59))

    _draw_limb(d, body_cx, body_cy, -138.5, -112.5, amplitude, 37.5, fur)
    _draw_limb(d, body_cx, body_cy, 136.5, -112.5, amplitude, 37.5, fur)

    note1_x, note1_y = nose_cx + (-175) * amplitude, nose_cy + (-32.5) * amplitude
    note2_x, note2_y = nose_cx + 145 * amplitude, nose_cy + (-32.5) * amplitude
    draw_musical_notes(d, int(note1_x), int(note1_y), accent)
    draw_musical_notes(d, int(note2_x), int(note2_y), (250, 204, 21))

    return img


def _draw_pose_3_step_right(fur: tuple, inner: tuple, accent: tuple, amplitude: float = 1.0) -> Image.Image:
    """Pose 3: Step Right & Sing (mirror of Pose 1)."""
    img = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body_cx, body_cy = 260, 340
    nose_cx, nose_cy = 265, 167.5

    d.ellipse([150, 210, 370, 470], fill=fur)
    d.ellipse([190, 260, 330, 440], fill=inner)
    d.ellipse([145, 60, 385, 280], fill=fur)
    d.ellipse([195, 140, 335, 255], fill=inner)
    d.ellipse([220, 135, 240, 155], fill=(30, 41, 59))
    d.ellipse([225, 138, 233, 146], fill=(255, 255, 255))
    d.arc([275, 130, 320, 165], start=180, end=360, fill=(30, 41, 59), width=5)
    d.ellipse([245, 180, 285, 225], fill=(225, 29, 72))
    d.ellipse([255, 195, 275, 215], fill=(255, 182, 193))
    d.ellipse([255, 160, 275, 175], fill=(30, 41, 59))

    _draw_limb(d, body_cx, body_cy, -132.5, -2.5, amplitude, 37.5, fur)
    _draw_limb(d, body_cx, body_cy, 127.5, -122.5, amplitude, 37.5, fur)

    note_x, note_y = nose_cx + 145 * amplitude, nose_cy + (-27.5) * amplitude
    draw_musical_notes(d, int(note_x), int(note_y), accent)

    return img


def _draw_pose_4_airborne_jump(fur: tuple, inner: tuple, accent: tuple, amplitude: float = 1.0) -> Image.Image:
    """Pose 4: Airborne Jump with Party Sparkles. Both arms and the 3 confetti
    starbursts displace from body/head anchors scaled by amplitude."""
    img = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body_cx, body_cy = 256, 300
    head_cx, head_cy = 256, 130

    d.ellipse([146, 170, 366, 430], fill=fur)
    d.ellipse([186, 220, 326, 400], fill=inner)
    d.ellipse([136, 20, 376, 240], fill=fur)
    d.ellipse([186, 100, 326, 215], fill=inner)
    d.ellipse([195, 85, 235, 125], fill=(30, 41, 59))
    d.ellipse([202, 90, 214, 102], fill=(255, 255, 255))
    d.ellipse([275, 85, 315, 125], fill=(30, 41, 59))
    d.ellipse([282, 90, 294, 102], fill=(255, 255, 255))
    d.ellipse([215, 140, 295, 205], fill=(225, 29, 72))
    d.ellipse([230, 165, 280, 200], fill=(255, 182, 193))
    d.ellipse([245, 125, 265, 140], fill=(30, 41, 59))

    _draw_limb(d, body_cx, body_cy, -156, -130, amplitude, 40, fur)
    _draw_limb(d, body_cx, body_cy, 154, -130, amplitude, 40, fur)

    star_offsets = [(-156, -50), (154, -50), (0, -100)]
    for dx, dy in star_offsets:
        star_x, star_y = head_cx + dx * amplitude, head_cy + dy * amplitude
        d.ellipse([star_x - 12, star_y - 12, star_x + 12, star_y + 12], fill=(250, 204, 21))
        d.ellipse([star_x - 5, star_y - 5, star_x + 5, star_y + 5], fill=(255, 255, 255))

    return img


def generate_mascot_dance_frames(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    mascots = [
        {"id": "bear", "fur": (194, 112, 58), "inner": (234, 178, 134), "accent": (239, 68, 68)},
        {"id": "penguin", "fur": (30, 41, 59), "inner": (248, 250, 252), "accent": (56, 189, 248)},
        {"id": "lion", "fur": (234, 150, 40), "inner": (254, 215, 120), "accent": (16, 185, 129)},
        {"id": "bunny", "fur": (241, 245, 249), "inner": (251, 207, 232), "accent": (168, 85, 247)},
    ]

    pose_fns = [_draw_pose_1_step_left, _draw_pose_2_head_high, _draw_pose_3_step_right, _draw_pose_4_airborne_jump]

    for m in mascots:
        mid, fur, inner, accent = m["id"], m["fur"], m["inner"], m["accent"]

        for i, pose_fn in enumerate(pose_fns, start=1):
            pose_fn(fur, inner, accent, amplitude=1.0).save(output_dir / f"{mid}_d{i}.png", "PNG")
            pose_fn(fur, inner, accent, amplitude=POEM_AMPLITUDE).save(output_dir / f"{mid}_poem_d{i}.png", "PNG")

    print(f"Generated 16 energetic + 16 calm mascot dance/singing frames in {output_dir}")


if __name__ == "__main__":
    generate_mascot_dance_frames(ASSETS_DIR / "images" / "mascots_dance")

import math
from pathlib import Path
from PIL import Image, ImageDraw
from backend.app.config import ASSETS_DIR

CANVAS_SIZE = (512, 512)

def draw_musical_notes(d: ImageDraw.ImageDraw, x: int, y: int, color: tuple):
    """Draws cute floating musical notes."""
    d.ellipse([x - 12, y - 10, x + 6, y + 6], fill=color)
    d.line([(x + 4, y), (x + 4, y - 35)], fill=color, width=4)
    d.line([(x + 4, y - 35), (x + 22, y - 30)], fill=color, width=5)


def generate_mascot_dance_frames(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    mascots = [
        {"id": "bear", "name": "Barnaby Bear", "fur": (194, 112, 58), "inner": (234, 178, 134), "ears": (160, 85, 40), "accent": (239, 68, 68)},
        {"id": "penguin", "name": "Penny Penguin", "fur": (30, 41, 59), "inner": (248, 250, 252), "ears": (249, 115, 22), "accent": (56, 189, 248)},
        {"id": "lion", "name": "Leo Lion", "fur": (234, 150, 40), "inner": (254, 215, 120), "ears": (194, 65, 12), "accent": (16, 185, 129)},
        {"id": "bunny", "name": "Bella Bunny", "fur": (241, 245, 249), "inner": (251, 207, 232), "ears": (244, 114, 182), "accent": (168, 85, 247)},
    ]

    for m in mascots:
        mid = m["id"]
        fur = m["fur"]
        inner = m["inner"]
        accent = m["accent"]

        # Pose 1: Step Left & Sing (d1)
        img1 = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        d1 = ImageDraw.Draw(img1)
        # Tilted body left
        d1.ellipse([140, 210, 360, 470], fill=fur)
        d1.ellipse([180, 260, 320, 440], fill=inner)
        # Head tilted left
        d1.ellipse([125, 60, 365, 280], fill=fur)
        d1.ellipse([175, 140, 315, 255], fill=inner)
        # Cheerful Winking Eyes
        d1.arc([190, 130, 235, 165], start=180, end=360, fill=(30, 41, 59), width=5)
        d1.ellipse([270, 135, 290, 155], fill=(30, 41, 59))
        d1.ellipse([275, 138, 283, 146], fill=(255, 255, 255))
        # Open Singing Mouth (O)
        d1.ellipse([225, 180, 265, 225], fill=(225, 29, 72))
        d1.ellipse([235, 195, 255, 215], fill=(255, 182, 193))
        # Nose
        d1.ellipse([235, 160, 255, 175], fill=(30, 41, 59))
        # Left paw waving high, right paw down
        d1.ellipse([85, 180, 160, 255], fill=fur)
        d1.ellipse([345, 300, 420, 375], fill=fur)
        # Musical note
        draw_musical_notes(d1, 80, 150, accent)
        img1.save(output_dir / f"{mid}_d1.png", "PNG")

        # Pose 2: Big Singing Mouth Open & Head High (d2)
        img2 = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        d2 = ImageDraw.Draw(img2)
        # Centered Body
        d2.ellipse([146, 200, 366, 460], fill=fur)
        d2.ellipse([186, 250, 326, 430], fill=inner)
        # Centered Head High
        d2.ellipse([136, 50, 376, 270], fill=fur)
        d2.ellipse([186, 130, 326, 245], fill=inner)
        # Happy arched closed eyes (Singing soulfully!)
        d2.arc([190, 125, 235, 160], start=180, end=360, fill=(30, 41, 59), width=6)
        d2.arc([275, 125, 320, 160], start=180, end=360, fill=(30, 41, 59), width=6)
        # Big Joyful Open Singing Mouth
        d2.ellipse([215, 170, 295, 235], fill=(225, 29, 72))
        d2.ellipse([230, 195, 280, 230], fill=(255, 182, 193))
        d2.ellipse([245, 155, 265, 170], fill=(30, 41, 59))
        # Both paws up with joy
        d2.ellipse([80, 180, 155, 255], fill=fur)
        d2.ellipse([355, 180, 430, 255], fill=fur)
        # Starburst / Double musical notes
        draw_musical_notes(d2, 80, 130, accent)
        draw_musical_notes(d2, 400, 130, (250, 204, 21))
        img2.save(output_dir / f"{mid}_d2.png", "PNG")

        # Pose 3: Step Right & Sing (d3)
        img3 = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        d3 = ImageDraw.Draw(img3)
        # Tilted body right
        d3.ellipse([150, 210, 370, 470], fill=fur)
        d3.ellipse([190, 260, 330, 440], fill=inner)
        # Head tilted right
        d3.ellipse([145, 60, 385, 280], fill=fur)
        d3.ellipse([195, 140, 335, 255], fill=inner)
        # Cheerful Winking Eyes (other eye)
        d3.ellipse([220, 135, 240, 155], fill=(30, 41, 59))
        d3.ellipse([225, 138, 233, 146], fill=(255, 255, 255))
        d3.arc([275, 130, 320, 165], start=180, end=360, fill=(30, 41, 59), width=5)
        # Open Singing Mouth
        d3.ellipse([245, 180, 285, 225], fill=(225, 29, 72))
        d3.ellipse([255, 195, 275, 215], fill=(255, 182, 193))
        d3.ellipse([255, 160, 275, 175], fill=(30, 41, 59))
        # Left paw down, right paw waving high
        d3.ellipse([90, 300, 165, 375], fill=fur)
        d3.ellipse([350, 180, 425, 255], fill=fur)
        draw_musical_notes(d3, 410, 140, accent)
        img3.save(output_dir / f"{mid}_d3.png", "PNG")

        # Pose 4: Airborne Jump with Party Sparkles (d4)
        img4 = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        d4 = ImageDraw.Draw(img4)
        # Higher elevated body (airborne jump)
        d4.ellipse([146, 170, 366, 430], fill=fur)
        d4.ellipse([186, 220, 326, 400], fill=inner)
        # Head high
        d4.ellipse([136, 20, 376, 240], fill=fur)
        d4.ellipse([186, 100, 326, 215], fill=inner)
        # Big sparkling wide open eyes
        d4.ellipse([195, 85, 235, 125], fill=(30, 41, 59))
        d4.ellipse([202, 90, 214, 102], fill=(255, 255, 255))
        d4.ellipse([275, 85, 315, 125], fill=(30, 41, 59))
        d4.ellipse([282, 90, 294, 102], fill=(255, 255, 255))
        # Huge happy laughing open mouth
        d4.ellipse([215, 140, 295, 205], fill=(225, 29, 72))
        d4.ellipse([230, 165, 280, 200], fill=(255, 182, 193))
        d4.ellipse([245, 125, 265, 140], fill=(30, 41, 59))
        # Raised outstretched jumping arms
        d4.ellipse([60, 130, 140, 210], fill=fur)
        d4.ellipse([370, 130, 450, 210], fill=fur)
        # Golden confetti starbursts
        for star_x, star_y in [(100, 80), (410, 80), (256, 30)]:
            d4.ellipse([star_x - 12, star_y - 12, star_x + 12, star_y + 12], fill=(250, 204, 21))
            d4.ellipse([star_x - 5, star_y - 5, star_x + 5, star_y + 5], fill=(255, 255, 255))
        img4.save(output_dir / f"{mid}_d4.png", "PNG")

    print(f"Generated 16 mascot dance & singing frames in {output_dir}")

if __name__ == "__main__":
    generate_mascot_dance_frames(ASSETS_DIR / "images" / "mascots_dance")

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

def create_mascot_asking(output_path: Path, size: int = 512):
    """Generates Barnaby Bear in an inquisitive asking pose with a thinking sparkle."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2 + 20

    # Colors
    c_fur_shadow = (165, 95, 45, 255)
    c_fur = (198, 125, 68, 255)
    c_fur_light = (222, 155, 98, 255)
    c_muzzle = (250, 225, 195, 255)
    c_inner_ear = (245, 175, 180, 255)
    c_cheeks = (255, 130, 140, 160)
    c_eye = (35, 25, 20, 255)
    c_sparkle = (255, 215, 0, 255)
    c_cap = (59, 130, 246, 255) # Bright royal blue cap
    c_cap_brim = (37, 99, 235, 255)

    # 1. Ears
    # Left Ear
    draw.ellipse([cx - 190, cy - 200, cx - 70, cy - 80], fill=c_fur)
    draw.ellipse([cx - 170, cy - 180, cx - 90, cy - 100], fill=c_inner_ear)
    # Right Ear
    draw.ellipse([cx + 70, cy - 200, cx + 190, cy - 80], fill=c_fur)
    draw.ellipse([cx + 90, cy - 180, cx + 170, cy - 100], fill=c_inner_ear)

    # 2. Main Head
    draw.ellipse([cx - 160, cy - 140, cx + 160, cy + 140], fill=c_fur)
    draw.ellipse([cx - 150, cy - 130, cx + 150, cy + 130], fill=c_fur_light)

    # 3. Cute Kid Hat / Cap (Fun Blue Cap with Propeller/Star)
    draw.chord([cx - 110, cy - 210, cx + 110, cy - 110], start=180, end=360, fill=c_cap)
    draw.ellipse([cx - 130, cy - 135, cx + 130, cy - 105], fill=c_cap_brim)
    # Star on hat
    draw.ellipse([cx - 15, cy - 185, cx + 15, cy - 155], fill=(250, 204, 21, 255))

    # 4. Muzzle & Cheeks
    draw.ellipse([cx - 95, cy - 20, cx + 95, cy + 110], fill=c_muzzle)
    # Rosy Cheeks
    draw.ellipse([cx - 135, cy + 10, cx - 75, cy + 60], fill=c_cheeks)
    draw.ellipse([cx + 75, cy + 10, cx + 135, cy + 60], fill=c_cheeks)

    # 5. Nose & Mouth
    # Cute chocolate nose
    draw.ellipse([cx - 30, cy + 10, cx + 30, cy + 50], fill=(45, 25, 15, 255))
    draw.ellipse([cx - 15, cy + 15, cx - 3, cy + 27], fill=(255, 255, 255, 200)) # Nose highlight
    # Smiling Mouth (Asking pose: slight open curious "O")
    draw.arc([cx - 35, cy + 45, cx + 5, cy + 85], start=0, end=140, fill=(45, 25, 15, 255), width=6)
    draw.arc([cx - 5, cy + 45, cx + 35, cy + 85], start=40, end=180, fill=(45, 25, 15, 255), width=6)

    # 6. Big Glossy Cartoon Eyes
    # Left Eye
    draw.ellipse([cx - 90, cy - 65, cx - 25, cy + 5], fill=c_eye)
    draw.ellipse([cx - 80, cy - 55, cx - 50, cy - 25], fill=(255, 255, 255, 255))
    draw.ellipse([cx - 45, cy - 20, cx - 32, cy - 7], fill=(255, 255, 255, 255))
    # Right Eye (Curious raised brow)
    draw.ellipse([cx + 25, cy - 65, cx + 90, cy + 5], fill=c_eye)
    draw.ellipse([cx + 35, cy - 55, cx + 65, cy - 25], fill=(255, 255, 255, 255))
    draw.ellipse([cx + 70, cy - 20, cx + 83, cy - 7], fill=(255, 255, 255, 255))

    # Eyebrows
    draw.arc([cx - 85, cy - 95, cx - 30, cy - 65], start=180, end=360, fill=(80, 45, 20, 255), width=7)
    draw.arc([cx + 30, cy - 105, cx + 85, cy - 75], start=180, end=360, fill=(80, 45, 20, 255), width=7)

    # 7. Red Bowtie
    draw.polygon([(cx - 70, cy + 125), (cx, cy + 150), (cx - 70, cy + 175)], fill=(239, 68, 68, 255))
    draw.polygon([(cx + 70, cy + 125), (cx, cy + 150), (cx + 70, cy + 175)], fill=(239, 68, 68, 255))
    draw.ellipse([cx - 20, cy + 135, cx + 20, cy + 165], fill=(220, 38, 38, 255))
    draw.ellipse([cx - 10, cy + 140, cx - 2, cy + 148], fill=(255, 255, 255, 180))

    img.save(output_path, "PNG")


def create_mascot_cheering(output_path: Path, size: int = 512):
    """Generates Barnaby Bear in an excited, cheering, celebrating pose."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2 + 20

    c_fur = (198, 125, 68, 255)
    c_fur_light = (222, 155, 98, 255)
    c_muzzle = (250, 225, 195, 255)
    c_inner_ear = (245, 175, 180, 255)
    c_cheeks = (255, 120, 130, 200)
    c_eye = (35, 25, 20, 255)
    c_cap = (16, 185, 129, 255) # Emerald Green party cap
    c_cap_brim = (5, 150, 105, 255)

    # 1. Ears
    draw.ellipse([cx - 195, cy - 205, cx - 75, cy - 85], fill=c_fur)
    draw.ellipse([cx - 175, cy - 185, cx - 95, cy - 105], fill=c_inner_ear)
    draw.ellipse([cx + 75, cy - 205, cx + 195, cy - 85], fill=c_fur)
    draw.ellipse([cx + 95, cy - 185, cx + 175, cy - 105], fill=c_inner_ear)

    # 2. Main Head
    draw.ellipse([cx - 160, cy - 140, cx + 160, cy + 140], fill=c_fur)
    draw.ellipse([cx - 150, cy - 130, cx + 150, cy + 130], fill=c_fur_light)

    # 3. Party Hat (Green & Gold)
    draw.polygon([(cx, cy - 240), (cx - 70, cy - 120), (cx + 70, cy - 120)], fill=c_cap)
    draw.ellipse([cx - 18, cy - 255, cx + 18, cy - 225], fill=(251, 191, 36, 255)) # Pompom
    draw.arc([cx - 75, cy - 130, cx + 75, cy - 110], start=0, end=180, fill=c_cap_brim, width=8)

    # 4. Muzzle & Happy Blushing Cheeks
    draw.ellipse([cx - 95, cy - 20, cx + 95, cy + 110], fill=c_muzzle)
    draw.ellipse([cx - 140, cy + 5, cx - 70, cy + 60], fill=c_cheeks)
    draw.ellipse([cx + 70, cy + 5, cx + 140, cy + 60], fill=c_cheeks)

    # 5. Nose & Wide Happy Open Grin
    draw.ellipse([cx - 28, cy + 5, cx + 28, cy + 45], fill=(45, 25, 15, 255))
    draw.ellipse([cx - 14, cy + 10, cx - 2, cy + 22], fill=(255, 255, 255, 200))
    # Big Open Smile
    draw.chord([cx - 45, cy + 40, cx + 45, cy + 95], start=0, end=180, fill=(185, 28, 28, 255))
    # Pink Tongue
    draw.chord([cx - 25, cy + 60, cx + 25, cy + 95], start=0, end=180, fill=(244, 114, 182, 255))

    # 6. Joyful Happy Curved Eyes (^ ^)
    draw.arc([cx - 85, cy - 50, cx - 30, cy + 5], start=180, end=360, fill=c_eye, width=12)
    draw.arc([cx + 30, cy - 50, cx + 85, cy + 5], start=180, end=360, fill=c_eye, width=12)

    # Cheering Stars Around
    for sx, sy, rad in [(cx - 180, cy - 80, 20), (cx + 180, cy - 80, 20), (cx - 150, cy + 130, 15), (cx + 150, cy + 130, 15)]:
        draw.ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=(251, 191, 36, 255))

    # 7. Bowtie
    draw.polygon([(cx - 70, cy + 125), (cx, cy + 150), (cx - 70, cy + 175)], fill=(251, 191, 36, 255))
    draw.polygon([(cx + 70, cy + 125), (cx, cy + 150), (cx + 70, cy + 175)], fill=(251, 191, 36, 255))
    draw.ellipse([cx - 20, cy + 135, cx + 20, cy + 165], fill=(245, 158, 11, 255))

    img.save(output_path, "PNG")


def generate_all_mascots(images_dir: Path):
    images_dir.mkdir(parents=True, exist_ok=True)
    create_mascot_asking(images_dir / "mascot_asking.png")
    create_mascot_cheering(images_dir / "mascot_cheering.png")
    print(f"Generated mascot PNG assets in {images_dir}")


if __name__ == "__main__":
    from backend.app.config import IMAGES_DIR
    generate_all_mascots(IMAGES_DIR)

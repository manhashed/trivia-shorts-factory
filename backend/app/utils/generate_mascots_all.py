from pathlib import Path
from PIL import Image, ImageDraw

def render_bear(asking: bool, size: int = 512) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2 + 20

    # Colors
    c_fur = (198, 125, 68, 255)
    c_fur_light = (222, 155, 98, 255)
    c_muzzle = (250, 225, 195, 255)
    c_inner_ear = (245, 175, 180, 255)
    c_cheeks = (255, 130, 140, 180)
    c_eye = (35, 25, 20, 255)
    c_cap = (59, 130, 246, 255) if asking else (16, 185, 129, 255)

    # Ears
    d.ellipse([cx - 190, cy - 200, cx - 70, cy - 80], fill=c_fur)
    d.ellipse([cx - 170, cy - 180, cx - 90, cy - 100], fill=c_inner_ear)
    d.ellipse([cx + 70, cy - 200, cx + 190, cy - 80], fill=c_fur)
    d.ellipse([cx + 90, cy - 180, cx + 170, cy - 100], fill=c_inner_ear)

    # Head
    d.ellipse([cx - 160, cy - 140, cx + 160, cy + 140], fill=c_fur)
    d.ellipse([cx - 150, cy - 130, cx + 150, cy + 130], fill=c_fur_light)

    # Cap / Hat
    if asking:
        d.chord([cx - 110, cy - 210, cx + 110, cy - 110], start=180, end=360, fill=c_cap)
        d.ellipse([cx - 130, cy - 135, cx + 130, cy - 105], fill=(37, 99, 235, 255))
        d.ellipse([cx - 15, cy - 185, cx + 15, cy - 155], fill=(250, 204, 21, 255))
    else:
        # Party hat
        d.polygon([(cx, cy - 240), (cx - 70, cy - 120), (cx + 70, cy - 120)], fill=c_cap)
        d.ellipse([cx - 18, cy - 255, cx + 18, cy - 225], fill=(251, 191, 36, 255))

    # Muzzle & Cheeks
    d.ellipse([cx - 95, cy - 20, cx + 95, cy + 110], fill=c_muzzle)
    d.ellipse([cx - 135, cy + 10, cx - 75, cy + 60], fill=c_cheeks)
    d.ellipse([cx + 75, cy + 10, cx + 135, cy + 60], fill=c_cheeks)

    # Nose & Mouth
    d.ellipse([cx - 28, cy + 10, cx + 28, cy + 48], fill=(45, 25, 15, 255))
    d.ellipse([cx - 14, cy + 15, cx - 3, cy + 26], fill=(255, 255, 255, 200))
    if asking:
        d.arc([cx - 35, cy + 45, cx + 5, cy + 85], start=0, end=140, fill=(45, 25, 15, 255), width=6)
        d.arc([cx - 5, cy + 45, cx + 35, cy + 85], start=40, end=180, fill=(45, 25, 15, 255), width=6)
        # Eyes curious
        d.ellipse([cx - 90, cy - 65, cx - 25, cy + 5], fill=c_eye)
        d.ellipse([cx - 80, cy - 55, cx - 50, cy - 25], fill=(255, 255, 255, 255))
        d.ellipse([cx + 25, cy - 65, cx + 90, cy + 5], fill=c_eye)
        d.ellipse([cx + 35, cy - 55, cx + 65, cy - 25], fill=(255, 255, 255, 255))
    else:
        # Cheering open grin
        d.chord([cx - 45, cy + 40, cx + 45, cy + 95], start=0, end=180, fill=(185, 28, 28, 255))
        d.chord([cx - 25, cy + 60, cx + 25, cy + 95], start=0, end=180, fill=(244, 114, 182, 255))
        # Happy eyes
        d.arc([cx - 85, cy - 50, cx - 30, cy + 5], start=180, end=360, fill=c_eye, width=12)
        d.arc([cx + 30, cy - 50, cx + 85, cy + 5], start=180, end=360, fill=c_eye, width=12)
        # Celebration Stars
        for sx, sy, rad in [(cx - 180, cy - 80, 20), (cx + 180, cy - 80, 20)]:
            d.ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=(251, 191, 36, 255))

    # Bowtie
    d.polygon([(cx - 70, cy + 125), (cx, cy + 150), (cx - 70, cy + 175)], fill=(239, 68, 68, 255))
    d.polygon([(cx + 70, cy + 125), (cx, cy + 150), (cx + 70, cy + 175)], fill=(239, 68, 68, 255))
    d.ellipse([cx - 20, cy + 135, cx + 20, cy + 165], fill=(220, 38, 38, 255))
    return img


def render_penguin(asking: bool, size: int = 512) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2 + 20

    # Colors
    c_body = (30, 41, 59, 255)
    c_belly = (255, 255, 255, 255)
    c_beak = (245, 158, 11, 255)
    c_cheeks = (251, 113, 133, 180)
    c_earmuffs = (168, 85, 247, 255)

    # Body
    d.ellipse([cx - 160, cy - 160, cx + 160, cy + 150], fill=c_body)
    # White Face/Belly Mask
    d.ellipse([cx - 120, cy - 100, cx + 120, cy + 140], fill=c_belly)
    d.ellipse([cx - 100, cy - 130, cx, cy - 10], fill=c_belly)
    d.ellipse([cx, cy - 130, cx + 100, cy - 10], fill=c_belly)

    # Earmuffs Headband
    d.arc([cx - 150, cy - 190, cx + 150, cy - 30], start=180, end=360, fill=c_earmuffs, width=14)
    d.ellipse([cx - 180, cy - 130, cx - 120, cy - 60], fill=c_earmuffs)
    d.ellipse([cx + 120, cy - 130, cx + 180, cy - 60], fill=c_earmuffs)

    # Cheeks
    d.ellipse([cx - 110, cy + 10, cx - 60, cy + 50], fill=c_cheeks)
    d.ellipse([cx + 60, cy + 10, cx + 110, cy + 50], fill=c_cheeks)

    # Beak
    d.polygon([(cx, cy + 45), (cx - 35, cy + 5), (cx + 35, cy + 5)], fill=c_beak)

    # Eyes & Poses
    if asking:
        d.ellipse([cx - 75, cy - 75, cx - 20, cy - 10], fill=(15, 23, 42, 255))
        d.ellipse([cx - 65, cy - 65, cx - 40, cy - 35], fill=(255, 255, 255, 255))
        d.ellipse([cx + 20, cy - 75, cx + 75, cy - 10], fill=(15, 23, 42, 255))
        d.ellipse([cx + 30, cy - 65, cx + 55, cy - 35], fill=(255, 255, 255, 255))
    else:
        d.arc([cx - 75, cy - 65, cx - 20, cy - 15], start=180, end=360, fill=(15, 23, 42, 255), width=12)
        d.arc([cx + 20, cy - 65, cx + 75, cy - 15], start=180, end=360, fill=(15, 23, 42, 255), width=12)
        # Cheering stars
        for sx, sy, rad in [(cx - 170, cy - 90, 18), (cx + 170, cy - 90, 18)]:
            d.ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=(250, 204, 21, 255))

    # Winter Scarf (Teal)
    d.rounded_rectangle([cx - 110, cy + 120, cx + 110, cy + 160], radius=15, fill=(20, 184, 166, 255))
    return img


def render_lion(asking: bool, size: int = 512) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2 + 20

    # Colors
    c_mane = (217, 119, 6, 255) # Warm Amber mane
    c_fur = (251, 191, 36, 255) # Gold fur
    c_muzzle = (254, 243, 199, 255)
    c_nose = (180, 83, 9, 255)
    c_cheeks = (251, 146, 60, 180)

    # Big Fluffy Mane
    for angle_step in range(0, 360, 30):
        import math
        rad = math.radians(angle_step)
        mx = cx + int(160 * math.cos(rad))
        my = cy + int(150 * math.sin(rad))
        d.ellipse([mx - 60, my - 60, mx + 60, my + 60], fill=c_mane)

    # Head
    d.ellipse([cx - 140, cy - 130, cx + 140, cy + 130], fill=c_fur)

    # Ears
    d.ellipse([cx - 150, cy - 160, cx - 70, cy - 80], fill=c_fur)
    d.ellipse([cx - 130, cy - 145, cx - 90, cy - 95], fill=(245, 158, 11, 255))
    d.ellipse([cx + 70, cy - 160, cx + 150, cy - 80], fill=c_fur)
    d.ellipse([cx + 90, cy - 145, cx + 130, cy - 95], fill=(245, 158, 11, 255))

    # Muzzle & Cheeks
    d.ellipse([cx - 85, cy - 10, cx + 85, cy + 100], fill=c_muzzle)
    d.ellipse([cx - 115, cy + 15, cx - 65, cy + 55], fill=c_cheeks)
    d.ellipse([cx + 65, cy + 15, cx + 115, cy + 55], fill=c_cheeks)

    # Nose & Smile
    d.polygon([(cx, cy + 40), (cx - 25, cy + 10), (cx + 25, cy + 10)], fill=c_nose)

    if asking:
        # Whiskers
        d.line([(cx - 70, cy + 40), (cx - 110, cy + 30)], fill=(120, 53, 15, 255), width=4)
        d.line([(cx + 70, cy + 40), (cx + 110, cy + 30)], fill=(120, 53, 15, 255), width=4)
        # Inquisitive Big Eyes
        d.ellipse([cx - 80, cy - 65, cx - 25, cy - 5], fill=(45, 25, 15, 255))
        d.ellipse([cx - 70, cy - 55, cx - 45, cy - 25], fill=(255, 255, 255, 255))
        d.ellipse([cx + 25, cy - 65, cx + 80, cy - 5], fill=(45, 25, 15, 255))
        d.ellipse([cx + 35, cy - 55, cx + 60, cy - 25], fill=(255, 255, 255, 255))
    else:
        # Cheering King Crown
        d.polygon([(cx - 70, cy - 160), (cx - 40, cy - 130), (cx, cy - 180), (cx + 40, cy - 130), (cx + 70, cy - 160), (cx + 50, cy - 110), (cx - 50, cy - 110)], fill=(250, 204, 21, 255))
        # Happy roaring smile
        d.chord([cx - 40, cy + 35, cx + 40, cy + 85], start=0, end=180, fill=(185, 28, 28, 255))
        d.arc([cx - 75, cy - 55, cx - 25, cy - 5], start=180, end=360, fill=(45, 25, 15, 255), width=12)
        d.arc([cx + 25, cy - 55, cx + 75, cy - 5], start=180, end=360, fill=(45, 25, 15, 255), width=12)

    return img


def render_bunny(asking: bool, size: int = 512) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2 + 40

    # Colors
    c_fur = (248, 250, 252, 255) # Pure white
    c_fur_shadow = (226, 232, 240, 255)
    c_inner_ear = (253, 164, 175, 255)
    c_cheeks = (251, 113, 133, 180)
    c_flower = (244, 63, 94, 255)

    # Tall Bunny Ears
    # Left Ear
    d.ellipse([cx - 120, cy - 270, cx - 40, cy - 80], fill=c_fur_shadow)
    d.ellipse([cx - 110, cy - 260, cx - 50, cy - 90], fill=c_fur)
    d.ellipse([cx - 100, cy - 240, cx - 60, cy - 110], fill=c_inner_ear)
    # Right Ear
    d.ellipse([cx + 40, cy - 270, cx + 120, cy - 80], fill=c_fur_shadow)
    d.ellipse([cx + 50, cy - 260, cx + 110, cy - 90], fill=c_fur)
    d.ellipse([cx + 60, cy - 240, cx + 100, cy - 110], fill=c_inner_ear)

    # Head
    d.ellipse([cx - 145, cy - 130, cx + 145, cy + 120], fill=c_fur_shadow)
    d.ellipse([cx - 140, cy - 125, cx + 140, cy + 115], fill=c_fur)

    # Flower on ear
    d.ellipse([cx - 50, cy - 140, cx - 10, cy - 100], fill=c_flower)
    d.ellipse([cx - 35, cy - 125, cx - 25, cy - 115], fill=(250, 204, 21, 255))

    # Rosy Cheeks
    d.ellipse([cx - 120, cy + 5, cx - 70, cy + 45], fill=c_cheeks)
    d.ellipse([cx + 70, cy + 5, cx + 120, cy + 45], fill=c_cheeks)

    # Little Pink Nose
    d.ellipse([cx - 18, cy + 5, cx + 18, cy + 30], fill=(244, 63, 94, 255))

    if asking:
        # Inquisitive soft eyes
        d.ellipse([cx - 80, cy - 55, cx - 30, cy - 5], fill=(30, 41, 59, 255))
        d.ellipse([cx - 70, cy - 45, cx - 50, cy - 20], fill=(255, 255, 255, 255))
        d.ellipse([cx + 30, cy - 55, cx + 80, cy - 5], fill=(30, 41, 59, 255))
        d.ellipse([cx + 40, cy - 45, cx + 60, cy - 20], fill=(255, 255, 255, 255))
        # Bunny Whiskers
        d.line([(cx - 60, cy + 25), (cx - 110, cy + 15)], fill=(148, 163, 184, 255), width=3)
        d.line([(cx + 60, cy + 25), (cx + 110, cy + 15)], fill=(148, 163, 184, 255), width=3)
    else:
        # Happy Winking / Cheering Eyes
        d.arc([cx - 80, cy - 45, cx - 30, cy + 5], start=180, end=360, fill=(30, 41, 59, 255), width=10)
        d.arc([cx + 30, cy - 45, cx + 80, cy + 5], start=180, end=360, fill=(30, 41, 59, 255), width=10)
        # Cheering Sparkles
        for sx, sy, rad in [(cx - 160, cy - 100, 16), (cx + 160, cy - 100, 16)]:
            d.ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=(251, 191, 36, 255))

    return img


def generate_all_mascots(output_dir: Path):
    mascot_dir = output_dir / "mascots"
    mascot_dir.mkdir(parents=True, exist_ok=True)

    render_bear(asking=True).save(mascot_dir / "bear_asking.png", "PNG")
    render_bear(asking=False).save(mascot_dir / "bear_cheering.png", "PNG")

    render_penguin(asking=True).save(mascot_dir / "penguin_asking.png", "PNG")
    render_penguin(asking=False).save(mascot_dir / "penguin_cheering.png", "PNG")

    render_lion(asking=True).save(mascot_dir / "lion_asking.png", "PNG")
    render_lion(asking=False).save(mascot_dir / "lion_cheering.png", "PNG")

    render_bunny(asking=True).save(mascot_dir / "bunny_asking.png", "PNG")
    render_bunny(asking=False).save(mascot_dir / "bunny_cheering.png", "PNG")

    print(f"Successfully generated all 4 mascot characters (8 poses) in {mascot_dir}")


if __name__ == "__main__":
    from backend.app.config import IMAGES_DIR
    generate_all_mascots(IMAGES_DIR)

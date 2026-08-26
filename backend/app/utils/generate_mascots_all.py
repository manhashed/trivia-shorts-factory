import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps

SUPERSAMPLE = 4


def _supersampled_canvas(size: int, supersample: int = SUPERSAMPLE) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Create an RGBA canvas at `size * supersample` px so shapes drawn on it
    can later be downsampled with LANCZOS for anti-aliased, crisp edges
    instead of the jagged circles flat ImageDraw primitives produce at
    native resolution."""
    big = size * supersample
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _paste_gradient_ellipse(img: Image.Image, bbox: list, inner_color: tuple, outer_color: tuple) -> None:
    """Paint a radial-gradient-filled ellipse into `img` at `bbox`: `inner_color`
    at the center fading to `outer_color` at the rim, for a simple "3D toy"
    shading look instead of a flat single-color fill."""
    x0, y0, x1, y1 = bbox
    w, h = int(x1 - x0), int(y1 - y0)
    if w <= 0 or h <= 0:
        return
    mask_size = max(w, h)
    raw_mask = Image.radial_gradient("L").resize((mask_size, mask_size), Image.LANCZOS)
    raw_mask = ImageOps.invert(raw_mask)
    mask = raw_mask.resize((w, h), Image.LANCZOS)
    inner_layer = Image.new("RGBA", (w, h), inner_color)
    outer_layer = Image.new("RGBA", (w, h), outer_color)
    patch = Image.composite(inner_layer, outer_layer, mask)
    ellipse_mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(ellipse_mask).ellipse([0, 0, w - 1, h - 1], fill=255)
    img.paste(patch, (int(x0), int(y0)), ellipse_mask)


def _finalize(img: Image.Image, size: int, supersample: int = SUPERSAMPLE) -> Image.Image:
    """Add a soft drop shadow behind the character, then downsample the
    supersampled canvas to the final `size x size` output with LANCZOS."""
    silhouette_alpha = img.split()[-1]
    shadow_flat = Image.new("RGBA", img.size, (20, 20, 30, 140))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow.paste(shadow_flat, (0, 0), silhouette_alpha)
    offset = 14 * supersample
    shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow_layer.paste(shadow, (offset, offset), shadow)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=10 * supersample))
    composed = Image.alpha_composite(shadow_layer, img)
    return composed.resize((size, size), Image.LANCZOS)


def render_bear(asking: bool, size: int = 512) -> Image.Image:
    img, d = _supersampled_canvas(size)
    s = SUPERSAMPLE
    cx, cy = (size * s) // 2, (size * s) // 2 + 20 * s
    c_fur = (198, 125, 68, 255)
    c_fur_light = (222, 155, 98, 255)
    c_muzzle = (250, 225, 195, 255)
    c_inner_ear = (245, 175, 180, 255)
    c_cheeks = (255, 130, 140, 180)
    c_eye = (35, 25, 20, 255)
    c_cap = (59, 130, 246, 255) if asking else (16, 185, 129, 255)

    _paste_gradient_ellipse(img, [cx - 190*s, cy - 200*s, cx - 70*s, cy - 80*s], c_fur_light, c_fur)
    d.ellipse([cx - 170*s, cy - 180*s, cx - 90*s, cy - 100*s], fill=c_inner_ear)
    _paste_gradient_ellipse(img, [cx + 70*s, cy - 200*s, cx + 190*s, cy - 80*s], c_fur_light, c_fur)
    d.ellipse([cx + 90*s, cy - 180*s, cx + 170*s, cy - 100*s], fill=c_inner_ear)
    _paste_gradient_ellipse(img, [cx - 160*s, cy - 140*s, cx + 160*s, cy + 140*s], c_fur_light, c_fur)

    if asking:
        d.chord([cx - 110*s, cy - 210*s, cx + 110*s, cy - 110*s], start=180, end=360, fill=c_cap)
        d.ellipse([cx - 130*s, cy - 135*s, cx + 130*s, cy - 105*s], fill=(37, 99, 235, 255))
        d.ellipse([cx - 15*s, cy - 185*s, cx + 15*s, cy - 155*s], fill=(250, 204, 21, 255))
    else:
        d.polygon([(cx, cy - 240*s), (cx - 70*s, cy - 120*s), (cx + 70*s, cy - 120*s)], fill=c_cap)
        d.ellipse([cx - 18*s, cy - 255*s, cx + 18*s, cy - 225*s], fill=(251, 191, 36, 255))

    d.ellipse([cx - 95*s, cy - 20*s, cx + 95*s, cy + 110*s], fill=c_muzzle)
    d.ellipse([cx - 135*s, cy + 10*s, cx - 75*s, cy + 60*s], fill=c_cheeks)
    d.ellipse([cx + 75*s, cy + 10*s, cx + 135*s, cy + 60*s], fill=c_cheeks)
    d.ellipse([cx - 28*s, cy + 10*s, cx + 28*s, cy + 48*s], fill=(45, 25, 15, 255))
    d.ellipse([cx - 14*s, cy + 15*s, cx - 3*s, cy + 26*s], fill=(255, 255, 255, 200))

    if asking:
        d.arc([cx - 35*s, cy + 45*s, cx + 5*s, cy + 85*s], start=0, end=140, fill=(45, 25, 15, 255), width=6*s)
        d.arc([cx - 5*s, cy + 45*s, cx + 35*s, cy + 85*s], start=40, end=180, fill=(45, 25, 15, 255), width=6*s)
        d.ellipse([cx - 90*s, cy - 65*s, cx - 25*s, cy + 5*s], fill=c_eye)
        d.ellipse([cx - 80*s, cy - 55*s, cx - 50*s, cy - 25*s], fill=(255, 255, 255, 255))
        d.ellipse([cx + 25*s, cy - 65*s, cx + 90*s, cy + 5*s], fill=c_eye)
        d.ellipse([cx + 35*s, cy - 55*s, cx + 65*s, cy - 25*s], fill=(255, 255, 255, 255))
    else:
        d.chord([cx - 45*s, cy + 40*s, cx + 45*s, cy + 95*s], start=0, end=180, fill=(185, 28, 28, 255))
        d.chord([cx - 25*s, cy + 60*s, cx + 25*s, cy + 95*s], start=0, end=180, fill=(244, 114, 182, 255))
        d.arc([cx - 85*s, cy - 50*s, cx - 30*s, cy + 5*s], start=180, end=360, fill=c_eye, width=12*s)
        d.arc([cx + 30*s, cy - 50*s, cx + 85*s, cy + 5*s], start=180, end=360, fill=c_eye, width=12*s)
        for sx, sy, rad in [(cx - 180*s, cy - 80*s, 20*s), (cx + 180*s, cy - 80*s, 20*s)]:
            d.ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=(251, 191, 36, 255))

    d.polygon([(cx - 70*s, cy + 125*s), (cx, cy + 150*s), (cx - 70*s, cy + 175*s)], fill=(239, 68, 68, 255))
    d.polygon([(cx + 70*s, cy + 125*s), (cx, cy + 150*s), (cx + 70*s, cy + 175*s)], fill=(239, 68, 68, 255))
    d.ellipse([cx - 20*s, cy + 135*s, cx + 20*s, cy + 165*s], fill=(220, 38, 38, 255))

    return _finalize(img, size, s)


def render_penguin(asking: bool, size: int = 512) -> Image.Image:
    img, d = _supersampled_canvas(size)
    s = SUPERSAMPLE
    cx, cy = (size * s) // 2, (size * s) // 2 + 20 * s

    c_body = (30, 41, 59, 255)
    c_body_light = (51, 65, 85, 255)
    c_belly = (255, 255, 255, 255)
    c_belly_shadow = (226, 232, 240, 255)
    c_beak = (245, 158, 11, 255)
    c_cheeks = (251, 113, 133, 180)
    c_earmuffs = (168, 85, 247, 255)

    _paste_gradient_ellipse(img, [cx - 160*s, cy - 160*s, cx + 160*s, cy + 150*s], c_body_light, c_body)
    _paste_gradient_ellipse(img, [cx - 120*s, cy - 100*s, cx + 120*s, cy + 140*s], c_belly, c_belly_shadow)
    d.ellipse([cx - 100*s, cy - 130*s, cx, cy - 10*s], fill=c_belly)
    d.ellipse([cx, cy - 130*s, cx + 100*s, cy - 10*s], fill=c_belly)

    d.arc([cx - 150*s, cy - 190*s, cx + 150*s, cy - 30*s], start=180, end=360, fill=c_earmuffs, width=14*s)
    d.ellipse([cx - 180*s, cy - 130*s, cx - 120*s, cy - 60*s], fill=c_earmuffs)
    d.ellipse([cx + 120*s, cy - 130*s, cx + 180*s, cy - 60*s], fill=c_earmuffs)

    d.ellipse([cx - 110*s, cy + 10*s, cx - 60*s, cy + 50*s], fill=c_cheeks)
    d.ellipse([cx + 60*s, cy + 10*s, cx + 110*s, cy + 50*s], fill=c_cheeks)

    d.polygon([(cx, cy + 45*s), (cx - 35*s, cy + 5*s), (cx + 35*s, cy + 5*s)], fill=c_beak)

    if asking:
        d.ellipse([cx - 75*s, cy - 75*s, cx - 20*s, cy - 10*s], fill=(15, 23, 42, 255))
        d.ellipse([cx - 65*s, cy - 65*s, cx - 40*s, cy - 35*s], fill=(255, 255, 255, 255))
        d.ellipse([cx + 20*s, cy - 75*s, cx + 75*s, cy - 10*s], fill=(15, 23, 42, 255))
        d.ellipse([cx + 30*s, cy - 65*s, cx + 55*s, cy - 35*s], fill=(255, 255, 255, 255))
    else:
        d.arc([cx - 75*s, cy - 65*s, cx - 20*s, cy - 15*s], start=180, end=360, fill=(15, 23, 42, 255), width=12*s)
        d.arc([cx + 20*s, cy - 65*s, cx + 75*s, cy - 15*s], start=180, end=360, fill=(15, 23, 42, 255), width=12*s)
        for sx, sy, rad in [(cx - 170*s, cy - 90*s, 18*s), (cx + 170*s, cy - 90*s, 18*s)]:
            d.ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=(250, 204, 21, 255))

    d.rounded_rectangle([cx - 110*s, cy + 120*s, cx + 110*s, cy + 160*s], radius=15*s, fill=(20, 184, 166, 255))
    return _finalize(img, size, s)


def render_lion(asking: bool, size: int = 512) -> Image.Image:
    img, d = _supersampled_canvas(size)
    s = SUPERSAMPLE
    cx, cy = (size * s) // 2, (size * s) // 2 + 20 * s

    c_mane = (217, 119, 6, 255)
    c_fur = (251, 191, 36, 255)
    c_fur_light = (253, 224, 71, 255)
    c_muzzle = (254, 243, 199, 255)
    c_nose = (180, 83, 9, 255)
    c_cheeks = (251, 146, 60, 180)

    for angle_step in range(0, 360, 30):
        rad = math.radians(angle_step)
        mx = cx + int(160 * s * math.cos(rad))
        my = cy + int(150 * s * math.sin(rad))
        d.ellipse([mx - 60*s, my - 60*s, mx + 60*s, my + 60*s], fill=c_mane)

    _paste_gradient_ellipse(img, [cx - 140*s, cy - 130*s, cx + 140*s, cy + 130*s], c_fur_light, c_fur)

    d.ellipse([cx - 150*s, cy - 160*s, cx - 70*s, cy - 80*s], fill=c_fur)
    d.ellipse([cx - 130*s, cy - 145*s, cx - 90*s, cy - 95*s], fill=(245, 158, 11, 255))
    d.ellipse([cx + 70*s, cy - 160*s, cx + 150*s, cy - 80*s], fill=c_fur)
    d.ellipse([cx + 90*s, cy - 145*s, cx + 130*s, cy - 95*s], fill=(245, 158, 11, 255))

    d.ellipse([cx - 85*s, cy - 10*s, cx + 85*s, cy + 100*s], fill=c_muzzle)
    d.ellipse([cx - 115*s, cy + 15*s, cx - 65*s, cy + 55*s], fill=c_cheeks)
    d.ellipse([cx + 65*s, cy + 15*s, cx + 115*s, cy + 55*s], fill=c_cheeks)

    d.polygon([(cx, cy + 40*s), (cx - 25*s, cy + 10*s), (cx + 25*s, cy + 10*s)], fill=c_nose)

    if asking:
        d.line([(cx - 70*s, cy + 40*s), (cx - 110*s, cy + 30*s)], fill=(120, 53, 15, 255), width=4*s)
        d.line([(cx + 70*s, cy + 40*s), (cx + 110*s, cy + 30*s)], fill=(120, 53, 15, 255), width=4*s)
        d.ellipse([cx - 80*s, cy - 65*s, cx - 25*s, cy - 5*s], fill=(45, 25, 15, 255))
        d.ellipse([cx - 70*s, cy - 55*s, cx - 45*s, cy - 25*s], fill=(255, 255, 255, 255))
        d.ellipse([cx + 25*s, cy - 65*s, cx + 80*s, cy - 5*s], fill=(45, 25, 15, 255))
        d.ellipse([cx + 35*s, cy - 55*s, cx + 60*s, cy - 25*s], fill=(255, 255, 255, 255))
    else:
        d.polygon([(cx - 70*s, cy - 160*s), (cx - 40*s, cy - 130*s), (cx, cy - 180*s), (cx + 40*s, cy - 130*s), (cx + 70*s, cy - 160*s), (cx + 50*s, cy - 110*s), (cx - 50*s, cy - 110*s)], fill=(250, 204, 21, 255))
        d.chord([cx - 40*s, cy + 35*s, cx + 40*s, cy + 85*s], start=0, end=180, fill=(185, 28, 28, 255))
        d.arc([cx - 75*s, cy - 55*s, cx - 25*s, cy - 5*s], start=180, end=360, fill=(45, 25, 15, 255), width=12*s)
        d.arc([cx + 25*s, cy - 55*s, cx + 75*s, cy - 5*s], start=180, end=360, fill=(45, 25, 15, 255), width=12*s)

    return _finalize(img, size, s)


def render_bunny(asking: bool, size: int = 512) -> Image.Image:
    img, d = _supersampled_canvas(size)
    s = SUPERSAMPLE
    cx, cy = (size * s) // 2, (size * s) // 2 + 40 * s

    c_fur = (248, 250, 252, 255)
    c_fur_shadow = (226, 232, 240, 255)
    c_inner_ear = (253, 164, 175, 255)
    c_cheeks = (251, 113, 133, 180)
    c_flower = (244, 63, 94, 255)

    _paste_gradient_ellipse(img, [cx - 120*s, cy - 270*s, cx - 40*s, cy - 80*s], c_fur, c_fur_shadow)
    d.ellipse([cx - 100*s, cy - 240*s, cx - 60*s, cy - 110*s], fill=c_inner_ear)
    _paste_gradient_ellipse(img, [cx + 40*s, cy - 270*s, cx + 120*s, cy - 80*s], c_fur, c_fur_shadow)
    d.ellipse([cx + 60*s, cy - 240*s, cx + 100*s, cy - 110*s], fill=c_inner_ear)

    _paste_gradient_ellipse(img, [cx - 145*s, cy - 130*s, cx + 145*s, cy + 120*s], c_fur, c_fur_shadow)

    d.ellipse([cx - 50*s, cy - 140*s, cx - 10*s, cy - 100*s], fill=c_flower)
    d.ellipse([cx - 35*s, cy - 125*s, cx - 25*s, cy - 115*s], fill=(250, 204, 21, 255))

    d.ellipse([cx - 120*s, cy + 5*s, cx - 70*s, cy + 45*s], fill=c_cheeks)
    d.ellipse([cx + 70*s, cy + 5*s, cx + 120*s, cy + 45*s], fill=c_cheeks)

    d.ellipse([cx - 18*s, cy + 5*s, cx + 18*s, cy + 30*s], fill=(244, 63, 94, 255))

    if asking:
        d.ellipse([cx - 80*s, cy - 55*s, cx - 30*s, cy - 5*s], fill=(30, 41, 59, 255))
        d.ellipse([cx - 70*s, cy - 45*s, cx - 50*s, cy - 20*s], fill=(255, 255, 255, 255))
        d.ellipse([cx + 30*s, cy - 55*s, cx + 80*s, cy - 5*s], fill=(30, 41, 59, 255))
        d.ellipse([cx + 40*s, cy - 45*s, cx + 60*s, cy - 20*s], fill=(255, 255, 255, 255))
        d.line([(cx - 60*s, cy + 25*s), (cx - 110*s, cy + 15*s)], fill=(148, 163, 184, 255), width=3*s)
        d.line([(cx + 60*s, cy + 25*s), (cx + 110*s, cy + 15*s)], fill=(148, 163, 184, 255), width=3*s)
    else:
        d.arc([cx - 80*s, cy - 45*s, cx - 30*s, cy + 5*s], start=180, end=360, fill=(30, 41, 59, 255), width=10*s)
        d.arc([cx + 30*s, cy - 45*s, cx + 80*s, cy + 5*s], start=180, end=360, fill=(30, 41, 59, 255), width=10*s)
        for sx, sy, rad in [(cx - 160*s, cy - 100*s, 16*s), (cx + 160*s, cy - 100*s, 16*s)]:
            d.ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=(251, 191, 36, 255))

    return _finalize(img, size, s)


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

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from backend.app.config import ASSETS_DIR

def create_ui_overlay_assets(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Header Pill Banner (940 x 140)
    w_hdr, h_hdr = 940, 130
    img_hdr = Image.new("RGBA", (w_hdr, h_hdr), (0, 0, 0, 0))
    d_hdr = ImageDraw.Draw(img_hdr)
    # Outer Glow / Border
    d_hdr.rounded_rectangle([0, 0, w_hdr, h_hdr], radius=35, fill=(15, 23, 42, 235), outline=(251, 191, 36, 255), width=5)
    # Top Gloss Highlight
    d_hdr.rounded_rectangle([10, 8, w_hdr - 10, h_hdr // 2], radius=25, fill=(255, 255, 255, 30))
    img_hdr.save(output_dir / "header_pill.png", "PNG")

    # 2. Question Card Frame (940 x 460)
    w_q, h_q = 940, 460
    img_q = Image.new("RGBA", (w_q, h_q), (0, 0, 0, 0))
    d_q = ImageDraw.Draw(img_q)
    # Drop Shadow
    d_q.rounded_rectangle([10, 12, w_q, h_q], radius=45, fill=(0, 0, 0, 90))
    # Main Glass Card
    d_q.rounded_rectangle([0, 0, w_q - 10, h_q - 12], radius=45, fill=(15, 23, 42, 230), outline=(255, 255, 255, 220), width=6)
    # Inner Bevel Glow
    d_q.rounded_rectangle([8, 8, w_q - 18, h_q - 20], radius=38, outline=(251, 191, 36, 120), width=3)
    # Top Gloss
    d_q.rounded_rectangle([15, 12, w_q - 25, 120], radius=30, fill=(255, 255, 255, 25))
    img_q.save(output_dir / "question_card_frame.png", "PNG")

    # 3. Answer Card Frame (940 x 480) - Celebratory Emerald & Gold
    w_a, h_a = 940, 480
    img_a = Image.new("RGBA", (w_a, h_a), (0, 0, 0, 0))
    d_a = ImageDraw.Draw(img_a)
    # Drop Shadow
    d_a.rounded_rectangle([10, 12, w_a, h_a], radius=45, fill=(0, 0, 0, 100))
    # Emerald Background
    d_a.rounded_rectangle([0, 0, w_a - 10, h_a - 12], radius=45, fill=(6, 78, 59, 245), outline=(52, 211, 153, 255), width=7)
    # Gold Inner Border
    d_a.rounded_rectangle([10, 10, w_a - 20, h_a - 22], radius=38, outline=(250, 204, 21, 220), width=4)
    # Sparkle stars around top
    for star_x in [60, w_a - 70]:
        d_a.ellipse([star_x - 18, 25 - 18, star_x + 18, 25 + 18], fill=(250, 204, 21, 255))
        d_a.ellipse([star_x - 8, 25 - 8, star_x + 8, 25 + 8], fill=(255, 255, 255, 255))
    img_a.save(output_dir / "answer_card_frame.png", "PNG")

    # 4. Circular Countdown Badges (300 x 300) for 3, 2, 1
    # Number 3 (Gold / Yellow)
    img_cd3 = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    d3 = ImageDraw.Draw(img_cd3)
    # Outer Pulse Ring
    d3.ellipse([10, 10, 290, 290], fill=(250, 204, 21, 50), outline=(250, 204, 21, 180), width=6)
    # Main Circle
    d3.ellipse([35, 35, 265, 265], fill=(15, 23, 42, 245), outline=(250, 204, 21, 255), width=8)
    # Highlight
    d3.ellipse([55, 45, 245, 135], fill=(255, 255, 255, 35))
    img_cd3.save(output_dir / "countdown_badge_3.png", "PNG")

    # Number 2 (Orange)
    img_cd2 = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(img_cd2)
    d2.ellipse([10, 10, 290, 290], fill=(249, 115, 22, 50), outline=(249, 115, 22, 180), width=6)
    d2.ellipse([35, 35, 265, 265], fill=(15, 23, 42, 245), outline=(249, 115, 22, 255), width=8)
    d2.ellipse([55, 45, 245, 135], fill=(255, 255, 255, 35))
    img_cd2.save(output_dir / "countdown_badge_2.png", "PNG")

    # Number 1 (Crimson / Red)
    img_cd1 = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    d1 = ImageDraw.Draw(img_cd1)
    d1.ellipse([10, 10, 290, 290], fill=(239, 68, 68, 50), outline=(239, 68, 68, 180), width=6)
    d1.ellipse([35, 35, 265, 265], fill=(15, 23, 42, 245), outline=(239, 68, 68, 255), width=8)
    d1.ellipse([55, 45, 245, 135], fill=(255, 255, 255, 35))
    img_cd1.save(output_dir / "countdown_badge_1.png", "PNG")

    print(f"Generated UI card frames and countdown badges in {output_dir}")

if __name__ == "__main__":
    ui_dir = ASSETS_DIR / "ui"
    create_ui_overlay_assets(ui_dir)

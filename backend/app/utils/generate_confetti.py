import math
import random
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

from backend.app.utils.ffmpeg_check import get_ffmpeg_binary

COLORS = [
    (239, 68, 68),   # Red
    (250, 204, 21),  # Yellow
    (34, 197, 94),   # Green
    (59, 130, 246),  # Blue
    (236, 72, 153),  # Pink
    (249, 115, 22),  # Orange
    (168, 85, 247),  # Purple
    (255, 255, 255), # White
]

class ConfettiParticle:
    def __init__(self, width, height, duration):
        self.x = random.uniform(width * 0.1, width * 0.9)
        self.y = random.uniform(0, height * 0.5)
        self.vx = random.uniform(-300, 300)
        self.vy = random.uniform(-800, -200)
        self.gravity = 1200
        self.rotation = random.uniform(0, 360)
        self.spin = random.uniform(-180, 180)
        self.color = random.choice(COLORS)
        self.shape = random.choice(['rect', 'circle', 'star'])
        self.scale = random.uniform(0.7, 1.3)
        self.duration = duration

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.rotation += self.spin * dt

    def draw(self, draw, t):
        # Fade out in last 0.5s
        alpha = 255
        if self.duration - t < 0.5:
            alpha = int(255 * max(0, (self.duration - t) / 0.5))
            
        if alpha <= 0:
            return

        c = (*self.color, alpha)
        
        # Calculate rotated points for drawing
        angle = math.radians(self.rotation)
        
        if self.shape == 'circle':
            r = 6 * self.scale
            draw.ellipse([self.x - r, self.y - r, self.x + r, self.y + r], fill=c)
        elif self.shape == 'rect':
            w, h = 8 * self.scale, 16 * self.scale
            corners = [
                (-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)
            ]
            rot_corners = []
            for cx, cy in corners:
                rx = cx * math.cos(angle) - cy * math.sin(angle)
                ry = cx * math.sin(angle) + cy * math.cos(angle)
                rot_corners.append((self.x + rx, self.y + ry))
            draw.polygon(rot_corners, fill=c)
        elif self.shape == 'star':
            r_outer = 10 * self.scale
            r_inner = 4 * self.scale
            pts = []
            for i in range(10):
                r = r_outer if i % 2 == 0 else r_inner
                a = angle + math.radians(i * 36)
                pts.append((self.x + r * math.cos(a), self.y + r * math.sin(a)))
            draw.polygon(pts, fill=c)

class SparkleParticle:
    def __init__(self, width, height, start_time):
        self.x = random.uniform(0, width)
        self.y = random.uniform(0, height)
        self.start_time = start_time
        self.lifetime = 0.2
        self.scale = random.uniform(0.5, 1.5)

    def draw(self, draw, t):
        if t < self.start_time or t > self.start_time + self.lifetime:
            return
            
        progress = (t - self.start_time) / self.lifetime
        # peak at 0.5
        alpha_scale = 1.0 - abs(progress - 0.5) * 2
        alpha = int(255 * alpha_scale)
        
        if alpha <= 0:
            return
            
        c = (255, 255, 255, alpha)
        size = 20 * self.scale
        
        # 4 pointed star
        pts = [
            (self.x, self.y - size),
            (self.x + size/4, self.y - size/4),
            (self.x + size, self.y),
            (self.x + size/4, self.y + size/4),
            (self.x, self.y + size),
            (self.x - size/4, self.y + size/4),
            (self.x - size, self.y),
            (self.x - size/4, self.y - size/4),
        ]
        draw.polygon(pts, fill=c)

def render_to_video(frames_dir, output_path: Path, fps: int):
    ffmpeg_bin = get_ffmpeg_binary()
    cmd = [
        str(ffmpeg_bin),
        "-y",
        "-framerate", str(fps),
        "-i", f"{frames_dir}/frame_%04d.png",
        "-c:v", "libvpx-vp9",
        "-pix_fmt", "yuva420p",
        "-auto-alt-ref", "0",
        "-b:v", "2M",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def generate_confetti_burst(output_path: Path, width: int = 1080, height: int = 1920, duration: float = 2.0, fps: int = 30) -> Path:
    num_frames = int(duration * fps)
    
    particles = [ConfettiParticle(width, height, duration) for _ in range(random.randint(80, 120))]
    sparkles = [SparkleParticle(width, height, random.uniform(0, duration - 0.2)) for _ in range(random.randint(15, 20))]
    
    with tempfile.TemporaryDirectory() as td:
        dt = 1.0 / fps
        for i in range(num_frames):
            t = i * dt
            img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            for p in particles:
                p.draw(draw, t)
                p.update(dt)
                
            for s in sparkles:
                s.draw(draw, t)
                
            img.save(f"{td}/frame_{i:04d}.png")
            
        render_to_video(td, output_path, fps)
        
    return output_path

def generate_sparkle_loop(output_path: Path, width: int = 1080, height: int = 1920, duration: float = 1.5, fps: int = 30) -> Path:
    num_frames = int(duration * fps)
    
    sparkles = []
    num_sparkles = 30
    for _ in range(num_sparkles):
        s = SparkleParticle(width, height, random.uniform(0, duration))
        sparkles.append(s)
        
    with tempfile.TemporaryDirectory() as td:
        dt = 1.0 / fps
        for i in range(num_frames):
            t = i * dt
            img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            for s in sparkles:
                s.draw(draw, t)
                s.draw(draw, t - duration)
                s.draw(draw, t + duration)
                
            img.save(f"{td}/frame_{i:04d}.png")
            
        render_to_video(td, output_path, fps)
        
    return output_path

def ensure_confetti_assets(assets_dir: Path) -> dict[str, Path]:
    assets_dir = Path(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)
    confetti_path = assets_dir / "confetti_burst.webm"
    sparkle_path = assets_dir / "sparkle_loop.webm"
    
    if not confetti_path.exists():
        generate_confetti_burst(confetti_path)
    if not sparkle_path.exists():
        generate_sparkle_loop(sparkle_path)
        
    return {
        "confetti": confetti_path,
        "sparkle": sparkle_path
    }

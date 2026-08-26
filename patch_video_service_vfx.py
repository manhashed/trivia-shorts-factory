with open("backend/app/services/video_service.py", "r") as f:
    content = f.read()

old_bg = """        # (a) Background scale & crop
        filter_chains.append(
            f"[0:v]scale={config.width}:{config.height}:force_original_aspect_ratio=increase,"
            f"crop={config.width}:{config.height}[base_bg]"
        )"""

new_bg = """        # (a) Background scale & crop + VIBRANT GRAPHICS
        filter_chains.append(
            f"[0:v]scale={config.width}:{config.height}:force_original_aspect_ratio=increase,"
            f"crop={config.width}:{config.height},"
            f"eq=contrast=1.15:saturation=1.4:gamma=1.05,"
            f"vignette=PI/3.5[base_bg]"
        )"""

content = content.replace(old_bg, new_bg)

with open("backend/app/services/video_service.py", "w") as f:
    f.write(content)

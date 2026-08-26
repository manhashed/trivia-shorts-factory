with open("backend/app/services/poem_service.py", "r") as f:
    content = f.read()

# 1. Update background graphics
old_bg = """        # (a) Background scale & crop
        filter_chains.append(
            f"[0:v]scale={config.width}:{config.height}:force_original_aspect_ratio=increase,"
            f"crop={config.width}:{config.height}[base_bg]"
        )"""

new_bg = """        # (a) Background scale & crop + VIBRANT GRAPHICS (attention grabber)
        filter_chains.append(
            f"[0:v]scale={config.width}:{config.height}:force_original_aspect_ratio=increase,"
            f"crop={config.width}:{config.height},"
            f"eq=contrast=1.15:saturation=1.4:gamma=1.05,"
            f"vignette=PI/3.5[base_bg]"
        )"""

content = content.replace(old_bg, new_bg)

# 2. Update subtitle to use ASS
old_subtitle = """        # (f) Sing-Along Subtitle Header & Lyrics Text
        escaped_lyric_file = str(lyric_text_file).replace(":", "\\\\:")
        filter_chains.append(
            f"[with_lyric_frame]drawtext=fontfile='{font_path}':text='✨ SING ALONG WITH ME! ✨':"
            f"fontcolor=0x38BDF8:fontsize=38:x=(w-text_w)/2:y=910:"
            f"borderw=4:bordercolor=black@0.9:shadowcolor=black@0.9:shadowx=3:shadowy=3[with_sing_hdr]"
        )
        filter_chains.append(
            f"[with_sing_hdr]drawtext=fontfile='{font_path}':textfile='{escaped_lyric_file}':"
            f"fontcolor=0xFEF08A:fontsize=52:x=(w-text_w)/2:y=980:line_spacing=24:"
            f"borderw=6:bordercolor=black@0.95:shadowcolor=black@0.95:shadowx=4:shadowy=4[vout]"
        )"""

new_subtitle = """        # (f) Sing-Along Subtitle Header & Lyrics Text (KARAOKE)
        escaped_ass_path = str(ass_path).replace(":", "\\\\:")
        filter_chains.append(
            f"[with_lyric_frame]drawtext=fontfile='{font_path}':text='✨ SING ALONG WITH ME! ✨':"
            f"fontcolor=0x38BDF8:fontsize=38:x=(w-text_w)/2:y=910:"
            f"borderw=4:bordercolor=black@0.9:shadowcolor=black@0.9:shadowx=3:shadowy=3[with_sing_hdr]"
        )
        # Apply the ASS subtitle filter for the glowing karaoke sweep!
        filter_chains.append(
            f"[with_sing_hdr]ass='{escaped_ass_path}'[vout]"
        )"""

content = content.replace(old_subtitle, new_subtitle)

with open("backend/app/services/poem_service.py", "w") as f:
    f.write(content)

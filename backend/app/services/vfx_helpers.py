"""Shared pure-logic helpers for building reusable ffmpeg filter-graph fragments
used by both the trivia (video_service.py) and poem (poem_service.py) renderers.
"""
import math


def build_cinematic_bg_filter(
    input_label: str,
    output_label: str,
    width: int,
    height: int,
    total_duration: float,
    fps: int,
    zoom_enabled: bool,
    zoom_direction: str = "in",
) -> str:
    """Build a single ffmpeg filter-chain string that scales/crops a background
    video to the target frame size, optionally applies a subtle Ken Burns zoompan,
    and always applies the contrast/saturation/vignette cinematic color treatment.

    Returns a string of the form "[{input_label}]...[{output_label}]" ready to be
    joined with other filter_chains entries via ";\\n".join(...).
    """
    color_treatment = "eq=contrast=1.15:saturation=1.4:gamma=1.05,vignette=PI/3.5"

    if zoom_enabled:
        if zoom_direction == "out":
            zoom_expr = "z='max(0.94,1.06-0.0002*on)'"
        else:
            zoom_expr = "z='min(1.06,1+0.0002*on)'"

        total_frames = int(total_duration * fps) + 10
        return (
            f"[{input_label}]scale={width + 120}:{height + 214}:force_original_aspect_ratio=increase,"
            f"crop={width + 120}:{height + 214},"
            f"zoompan={zoom_expr}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s={width}x{height}:fps={fps},"
            f"{color_treatment}[{output_label}]"
        )

    return (
        f"[{input_label}]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"{color_treatment}[{output_label}]"
    )

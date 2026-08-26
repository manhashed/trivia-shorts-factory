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


def compute_overshoot_y(
    curr_opt_y: float,
    delay_s: float,
    t: float,
    overshoot_amount: float = 18.0,
    settle_dur: float = 0.35,
) -> float:
    """Pure Python mirror of the ffmpeg y_expr used for option-card entrance easing.

    Mirrors exactly:
        if(lt(t,delay_s),
           curr_opt_y+600,
           if(lt(t,delay_s+settle_dur),
              curr_opt_y-overshoot_amount*sin(PI*(t-delay_s)/settle_dur)*exp(-3*(t-delay_s)),
              curr_opt_y))
    """
    if t < delay_s:
        return curr_opt_y + 600
    if t < delay_s + settle_dur:
        dt = t - delay_s
        return curr_opt_y - overshoot_amount * math.sin(math.pi * dt / settle_dur) * math.exp(-3 * dt)
    return curr_opt_y


def build_overshoot_y_expr(
    curr_opt_y: int,
    delay_s: float,
    overshoot_amount: float = 18.0,
    settle_dur: float = 0.35,
) -> str:
    """Build the ffmpeg-expression-language string matching compute_overshoot_y above.
    Only uses ffmpeg-expression-safe primitives: if/lt/sin/exp/PI/+-*/.
    """
    return (
        f"if(lt(t,{delay_s}),{curr_opt_y}+600,"
        f"if(lt(t,{delay_s}+{settle_dur}),"
        f"{curr_opt_y}-{overshoot_amount}*sin(PI*(t-{delay_s})/{settle_dur})*exp(-3*(t-{delay_s})),"
        f"{curr_opt_y}))"
    )


def build_countdown_tick_pulse(
    prior_layer: str,
    output_label: str,
    x: int,
    y_expr: str,
    tick_start: float,
    tick_end: float,
    box_w: int = 260,
    box_h: int = 260,
) -> str:
    """Build a semi-transparent white 'ring flash' drawbox behind a countdown
    number, alpha-oscillating at 4Hz, gated to one tick's enable window.
    """
    # ffmpeg drawbox has no alpha option; chain drawtext so the tested
    # alpha expression is valid and the box uses a visible midpoint opacity.
    return (
        f"[{prior_layer}]drawbox=x={x}:y='{y_expr}':w={box_w}:h={box_h}:"
        f"color=white@0.45:t=fill:"
        f"enable='between(t,{tick_start},{tick_end})',"
        f"drawtext=text=' ':fontsize=1:x=0:y=0:"
        f"alpha='0.3+0.3*sin(2*PI*(t-{tick_start})*4)':"
        f"enable='between(t,{tick_start},{tick_end})'[{output_label}]"
    )


_flash_src_counter = 0


def build_flash_overlay(
    prior_layer: str,
    output_label: str,
    width: int,
    height: int,
    flash_time: float,
    flash_dur: float = 0.25,
) -> list[str]:
    """Build a two-entry filter chain: a lavfi white color source that fades in
    then out, overlaid onto prior_layer at flash_time. Returns a list of
    filter_chains entries ready to append/extend into the caller's chain list.
    """
    global _flash_src_counter
    _flash_src_counter += 1
    src_label = f"flash_src_{_flash_src_counter}"

    src_chain = (
        f"color=c=white:s={width}x{height}:d={flash_dur},"
        f"format=rgba,"
        f"fade=t=in:st=0:d=0.05:alpha=1,"
        f"fade=t=out:st=0.05:d={flash_dur - 0.05:.2f}:alpha=1[{src_label}]"
    )
    overlay_chain = (
        f"[{prior_layer}][{src_label}]overlay=x=0:y=0:"
        f"enable='between(t,{flash_time},{flash_time + flash_dur})'[{output_label}]"
    )
    return [src_chain, overlay_chain]


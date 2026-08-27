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

    Slides up from 600px below rest over settle_dur (cubic ease) and subtracts a
    sine overshoot so the card travels past rest then settles. Continuous at
    t=delay_s (still off-screen) and t=delay_s+settle_dur (at rest).
    """
    if t < delay_s:
        return curr_opt_y + 600
    if t < delay_s + settle_dur:
        p = min(1.0, (t - delay_s) / settle_dur)
        remain = 1.0 - p
        slide = 600.0 * remain * remain * remain
        wobble = overshoot_amount * math.sin(math.pi * p)
        return curr_opt_y + slide - wobble
    return curr_opt_y


def build_overshoot_y_expr(
    curr_opt_y: int,
    delay_s: float,
    overshoot_amount: float = 18.0,
    settle_dur: float = 0.35,
) -> str:
    """Build the ffmpeg-expression-language string matching compute_overshoot_y above.
    Only uses ffmpeg-expression-safe primitives: if/lt/sin/min/PI/+-*/.
    """
    p = f"min(1,(t-{delay_s})/{settle_dur})"
    remain = f"(1-{p})"
    return (
        f"if(lt(t,{delay_s}),{curr_opt_y}+600,"
        f"if(lt(t,{delay_s}+{settle_dur}),"
        f"{curr_opt_y}+600*{remain}*{remain}*{remain}-{overshoot_amount}*sin(PI*{p}),"
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
    """Build a semi-transparent white box behind a countdown number whose alpha
    oscillates at 4Hz. drawtext's alpha applies to the box, unlike drawbox.
    """
    center_x = x + box_w // 2
    border = max(box_w, box_h) // 2
    return (
        f"[{prior_layer}]drawtext=text=' ':"
        f"fontsize=2:fontcolor=white:"
        f"x={center_x}:y='{y_expr}+{box_h // 2}':"
        f"box=1:boxcolor=white:boxborderw={border}:"
        f"alpha='0.3+0.3*sin(2*PI*(t-{tick_start})*4)':"
        f"enable='between(t,{tick_start},{tick_end})'[{output_label}]"
    )


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
    src_label = f"{output_label}_src"

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


def _build_outro_celebration_filters(
    prior_layer: str,
    confetti_input_idx: int,
    width: int,
    height: int,
    outro_start: float,
) -> tuple[list[str], str]:
    """Build the confetti-burst + white-flash celebration filters for a poem's
    outro (last ~1.5s pause). Chained BEFORE the final ass= subtitle filter so
    captions stay legible on top. Returns (chains, final_layer_label).
    """
    chains: list[str] = []

    confetti_scaled_label = "outro_confetti_scaled"
    with_confetti_label = "with_outro_confetti"
    chains.append(
        f"[{prior_layer}][{confetti_scaled_label}]overlay=x=0:y=0:"
        f"enable='between(t,{outro_start},{outro_start}+2.0)'[{with_confetti_label}]"
    )
    chains.append(f"[{confetti_input_idx}:v]scale={width}:{height}[{confetti_scaled_label}]")

    flash_chains = build_flash_overlay(
        prior_layer=with_confetti_label,
        output_label="with_outro_flash",
        width=width,
        height=height,
        flash_time=outro_start,
        flash_dur=0.25,
    )
    chains.extend(flash_chains)

    return chains, "with_outro_flash"


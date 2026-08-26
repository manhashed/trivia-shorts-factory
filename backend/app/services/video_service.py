import subprocess
import os
import logging
import random
from pathlib import Path
from typing import Dict, Any, List, Optional
import textwrap

from backend.app.config import FONTS_DIR, IMAGES_DIR, ASSETS_DIR, settings
from backend.app.services.vfx_helpers import build_cinematic_bg_filter, build_overshoot_y_expr
from backend.app.models.schemas import VideoRenderConfig
from backend.app.utils.ffmpeg_check import get_ffmpeg_binary, probe_media_file
from backend.app.utils.generate_confetti import ensure_confetti_assets

logger = logging.getLogger(__name__)

TEMPLATE_STYLES = {
    "candy_clouds": {
        "title": "⭐ FUN KIDS QUIZ! ⭐",
        "header_color": "white",
        "q_color": "0xFDE047", # Bright yellow
        "ans_color": "0x34D399",
        "ans_title": "🎉 ANSWER 🎉",
    },
    "space_galaxy": {
        "title": "🚀 COSMIC SPACE QUIZ! 🚀",
        "header_color": "0x38BDF8",
        "q_color": "0x67E8F9", # Bright cyan
        "ans_color": "0x22D3EE",
        "ans_title": "🌟 DISCOVERY! 🌟",
    },
    "safari_jungle": {
        "title": "🦁 JUNGLE SAFARI QUIZ! 🦁",
        "header_color": "0xFDE047",
        "q_color": "0xFEF08A",
        "ans_color": "0x4ADE80",
        "ans_title": "🌿 SAFARI WINNER! 🌿",
    },
    "ocean_bubbles": {
        "title": "🌊 OCEAN EXPLORER QUIZ! 🌊",
        "header_color": "0x7DD3FC",
        "q_color": "0xE0F2FE",
        "ans_color": "0x2DD4BF",
        "ans_title": "🐬 SPLASHING ANSWER! 🐬",
    },
    "arcade_retro": {
        "title": "🎮 ARCADE GAME SHOW! 🎮",
        "header_color": "0xFACC15",
        "q_color": "white",
        "ans_color": "0xFBBF24",
        "ans_title": "🏆 100 POINTS! 🏆",
    },
}


class VideoService:
    """
    Studio-grade FFmpeg video rendering pipeline producing high-retention 9:16 vertical shorts
    with animated motion graphics: Ken Burns background zoom, mascot bounce & dance keyframing,
    eased card slide-ins, countdown pop badges, celebratory white flash, and transparent confetti particle bursts.
    """

    def _wrap_text(self, text: str, max_chars_per_line: int = 22) -> str:
        lines = textwrap.wrap(text, width=max_chars_per_line, break_long_words=False)
        return "\n".join(lines)

    def _get_font_path(self) -> Path:
        for candidate in ["Fredoka-Bold.ttf", "Arial-Rounded-Bold.ttf"]:
            p = FONTS_DIR / candidate
            if p.is_file():
                return p
        for sys_path in [
            "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial.ttf",
        ]:
            if Path(sys_path).is_file():
                return Path(sys_path)
        raise RuntimeError("No suitable font found for video rendering.")

    def _get_mascot_paths(self, mascot_id: str) -> tuple[Path, Path]:
        mascots_dir = IMAGES_DIR / "mascots"
        asking = mascots_dir / f"{mascot_id}_asking.png"
        cheering = mascots_dir / f"{mascot_id}_cheering.png"

        if not asking.is_file() or not cheering.is_file():
            asking = mascots_dir / "bear_asking.png"
            cheering = mascots_dir / "bear_cheering.png"
        return asking, cheering

    def _get_dance_frames(self, mascot_id: str) -> List[Path]:
        dance_dir = IMAGES_DIR / "mascots_dance"
        frames = []
        for i in range(1, 5):
            fp = dance_dir / f"{mascot_id}_d{i}.png"
            if not fp.is_file():
                fp = dance_dir / f"bear_d{i}.png"
            if fp.is_file():
                frames.append(fp)
        return frames

    def _build_option_highlight_filters(
        self,
        options_layer: str,
        options: List[str],
        correct_index: int,
        t_ans_start: float,
        font_path,
        input_layer_idx: int,
    ) -> tuple[list[str], str]:
        """
        Builds the filter_complex chain that restyles the correct multiple-choice
        option into a highlighted green box with a checkmark once the answer
        reveal begins. Returns (filter_chain_strings, new_current_layer_name).
        The option's text is never altered -- only its box color, border, and an
        adjacent checkmark are added, using the exact same display string already
        rendered for that option during the question phase.
        """
        opt_labels = ["A", "B", "C", "D"]
        base_opt_y = 960
        opt_spacing = 110

        opt_text = options[correct_index]
        opt_letter = opt_labels[correct_index]
        safe_opt = str(opt_text).replace("'", "").replace(":", "\\:").strip()
        if safe_opt.upper().startswith(f"{opt_letter})") or safe_opt.upper().startswith(f"{opt_letter}:"):
            opt_display = safe_opt
        else:
            opt_display = f"{opt_letter})  {safe_opt}"

        curr_opt_y = base_opt_y + (correct_index * opt_spacing)

        filters: list[str] = []
        highlight_layer = f"with_opt_hl_{input_layer_idx}"
        check_layer = f"with_opt_check_{input_layer_idx}"

        filters.append(
            f"[{options_layer}]drawtext=fontfile='{font_path}':text='{opt_display}':"
            f"fontcolor=white:fontsize=46:x=(w-text_w)/2:y='{curr_opt_y}':"
            f"borderw=6:bordercolor=black@0.95:shadowcolor=black@0.9:shadowx=4:shadowy=4:"
            f"box=1:boxcolor=0x16A34A@0.85:boxborderw=16:"
            f"alpha='0.85+0.15*sin(2*PI*(t-{t_ans_start})/0.6)':"
            f"enable='gte(t,{t_ans_start})'[{highlight_layer}]"
        )
        filters.append(
            f"[{highlight_layer}]drawtext=fontfile='{font_path}':text='✓':fontcolor=0xFDE047:fontsize=52:"
            f"x=140:y='{curr_opt_y}':borderw=5:bordercolor=black@0.9:shadowcolor=black@0.9:shadowx=3:shadowy=3:"
            f"enable='gte(t,{t_ans_start})'[{check_layer}]"
        )

        return filters, check_layer

    async def render_short_video(
        self,
        bg_video_path: Path,
        master_audio_path: Path,
        timing_info: Dict[str, float],
        question_text: str,
        answer_text: str,
        output_mp4_path: Path,
        work_dir: Path,
        config: VideoRenderConfig,
        options: Optional[List[str]] = None,
        correct_index: Optional[int] = None,
    ) -> Path:
        work_dir.mkdir(parents=True, exist_ok=True)
        output_mp4_path.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg_bin = get_ffmpeg_binary()
        font_path = self._get_font_path()

        # 1. Text wrapping & files
        q_wrapped = self._wrap_text(question_text, max_chars_per_line=22)
        a_wrapped = self._wrap_text(answer_text, max_chars_per_line=18)

        q_text_file = work_dir / "q_text.txt"
        a_text_file = work_dir / "a_text.txt"
        with open(q_text_file, "w", encoding="utf-8") as f:
            f.write(q_wrapped)
        with open(a_text_file, "w", encoding="utf-8") as f:
            f.write(a_wrapped)

        # 2. Timing milestones
        t_cd_start = timing_info["t_countdown_start"]
        t_cd_end = timing_info["t_countdown_end"]
        t_ans_start = timing_info["t_answer_start"]
        total_duration = timing_info["total_duration"]

        cd_dur = timing_info["countdown_duration"]
        t_cd_3_end = t_cd_start + (cd_dur / 3.0)
        t_cd_2_end = t_cd_start + (2.0 * cd_dur / 3.0)

        # 3. Assets Paths
        ui_dir = ASSETS_DIR / "ui"
        header_pill_png = ui_dir / "header_pill.png"
        q_card_png = ui_dir / "question_card_frame.png"
        a_card_png = ui_dir / "answer_card_frame.png"
        cd3_badge_png = ui_dir / "countdown_badge_3.png"
        cd2_badge_png = ui_dir / "countdown_badge_2.png"
        cd1_badge_png = ui_dir / "countdown_badge_1.png"

        theme = TEMPLATE_STYLES.get(config.template_id, TEMPLATE_STYLES["candy_clouds"])
        mascot_asking, mascot_cheering = self._get_mascot_paths(config.mascot_id)
        dance_frames = self._get_dance_frames(config.mascot_id) if getattr(config, "mascot_dance", True) else []
        prompt_enable = f"between(t,{t_cd_start},{t_cd_end})" if getattr(config, "audience_prompt", True) else "0"

        # Ensure VFX assets exist
        vfx_dir = ASSETS_DIR / "vfx"
        confetti_video = None
        if getattr(config, "confetti_enabled", True):
            try:
                vfx_assets = ensure_confetti_assets(vfx_dir)
                confetti_video = vfx_assets.get("confetti")
            except Exception as e:
                logger.warning(f"Failed to ensure confetti assets: {e}")

        # 4. Build inputs array and filter graph dynamically
        input_args = [
            "-stream_loop", "-1", "-i", str(bg_video_path),  # 0:v (BG)
            "-i", str(master_audio_path),                     # 1:a (Audio)
            "-i", str(mascot_asking),                         # 2:v (Asking)
            "-i", str(mascot_cheering),                       # 3:v (Cheering)
            "-i", str(header_pill_png),                       # 4:v (Header)
            "-i", str(q_card_png),                            # 5:v (Q Card)
            "-i", str(a_card_png),                            # 6:v (A Card)
            "-i", str(cd3_badge_png),                         # 7:v (Badge 3)
            "-i", str(cd2_badge_png),                         # 8:v (Badge 2)
            "-i", str(cd1_badge_png),                         # 9:v (Badge 1)
        ]
        input_count = 10

        # Optional dance frames
        dance_input_indices = []
        if dance_frames and len(dance_frames) == 4:
            for df in dance_frames:
                input_args.extend(["-i", str(df)])
                dance_input_indices.append(input_count)
                input_count += 1

        # Optional confetti burst
        confetti_input_idx = None
        if confetti_video and confetti_video.is_file() and getattr(config, "confetti_enabled", True):
            input_args.extend(["-i", str(confetti_video)])
            confetti_input_idx = input_count
            input_count += 1

        filter_chains = []
        anim_style = getattr(config, "animation_style", "bounce")
        bg_zoom = getattr(config, "background_zoom", True)

        # ── (a) Background scale / Ken Burns Zoom ──
        filter_chains.append(
            build_cinematic_bg_filter(
                input_label="0:v",
                output_label="base_bg",
                width=config.width,
                height=config.height,
                total_duration=total_duration,
                fps=config.fps,
                zoom_enabled=bg_zoom,
                zoom_direction=random.choice(["in", "out"]),
            )
        )

        # ── (b) Header Pill Banner (x=70, y=140) ──
        filter_chains.append(
            f"[base_bg][4:v]overlay=x=70:y=140[with_hdr_frame]"
        )
        filter_chains.append(
            f"[with_hdr_frame]drawtext=fontfile='{font_path}':text='{theme['title']}':"
            f"fontcolor={theme['header_color']}:fontsize=48:x=(w-text_w)/2:y=175:"
            f"borderw=4:bordercolor=black@0.9:shadowcolor=black@0.9:shadowx=3:shadowy=3[with_hdr_text]"
        )

        # Persistent progress rail gives viewers an immediate sense of the short's arc.
        filter_chains.append(
            f"[with_hdr_text]drawbox=x=70:y=1850:w=940:h=12:color=black@0.45:t=fill[progress_track]"
        )
        filter_chains.append(
            f"[progress_track]drawbox=x=70:y=1850:w='940*min(1,t/{total_duration})':h=12:"
            f"color={theme['ans_color']}@0.95:t=fill[with_progress]"
        )

        # ── (c) Mascot Overlays (Asking Bobbing + Cheering/Dancing Bounce) ──
        filter_chains.append("[2:v]scale=230:230[mascot_ask_scaled]")

        if anim_style != "none":
            ask_y_expr = "285+8*sin(2*PI*t/0.8)"
            cheer_y_expr = "275+12*sin(2*PI*t/0.5)"
        else:
            ask_y_expr = "285"
            cheer_y_expr = "275"

        filter_chains.append(
            f"[with_progress][mascot_ask_scaled]overlay=x=100:y='{ask_y_expr}':enable='between(t,0,{t_ans_start})'[with_mascot_ask]"
        )

        # Mascot reveal: Dancing keyframes or Cheering Mascot
        if dance_input_indices and len(dance_input_indices) == 4:
            # Scale each dance frame
            for i, d_idx in enumerate(dance_input_indices):
                filter_chains.append(f"[{d_idx}:v]scale=240:240[mascot_d{i+1}_scaled]")

            current_layer = "with_mascot_ask"
            for i in range(4):
                next_layer = f"with_mascot_d{i+1}" if i < 3 else "with_mascot"
                enable_expr = f"gte(t,{t_ans_start})*eq(mod(floor((t-{t_ans_start})/0.25),4),{i})"
                filter_chains.append(
                    f"[{current_layer}][mascot_d{i+1}_scaled]overlay=x=90:y='{cheer_y_expr}':enable='{enable_expr}'[{next_layer}]"
                )
                current_layer = next_layer
        else:
            filter_chains.append("[3:v]scale=240:240[mascot_cheer_scaled]")
            filter_chains.append(
                f"[with_mascot_ask][mascot_cheer_scaled]overlay=x=90:y='{cheer_y_expr}':enable='gte(t,{t_ans_start})'[with_mascot]"
            )

        # The viewer is explicitly invited to participate during the thinking beat.
        filter_chains.append(
            f"[with_mascot]drawtext=fontfile='{font_path}':text='YOUR TURN!':fontcolor={theme['q_color']}:"
            f"fontsize=42:x=(w-text_w)/2:y=875:borderw=4:bordercolor=black@0.85:"
            f"shadowcolor=black@0.8:shadowx=3:shadowy=3:alpha='0.82+0.18*sin(2*PI*t/0.55)':"
            f"enable='{prompt_enable}'[with_turn_prompt]"
        )

        # ── (d) Question Card Frame (Slide-up ease or static) ──
        if anim_style in ["slide", "bounce", "pop"]:
            # Ease-out slide from below
            q_card_y = "if(lt(t,0.35),470+1450*(1-min(1,t/0.35))*(1-min(1,t/0.35)),470)"
            q_text_y = "if(lt(t,0.35),(710-(text_h/2))+1450*(1-min(1,t/0.35))*(1-min(1,t/0.35)),710-(text_h/2))"
        else:
            q_card_y = "470"
            q_text_y = "710-(text_h/2)"

        filter_chains.append(
            f"[with_turn_prompt][5:v]overlay=x=70:y='{q_card_y}'[with_q_frame]"
        )

        # ── (e) Question Text ──
        escaped_q_file = str(q_text_file).replace(":", "\\:")
        filter_chains.append(
            f"[with_q_frame]drawtext=fontfile='{font_path}':textfile='{escaped_q_file}':"
            f"fontcolor={theme['q_color']}:fontsize=58:x=(w-text_w)/2:y='{q_text_y}':line_spacing=20:"
            f"borderw=6:bordercolor=black@0.95:shadowcolor=black@0.95:shadowx=4:shadowy=4[with_q_text]"
        )

        # ── (f) Multiple Choice Options (if present) ──
        options_layer = "with_q_text"
        has_options = bool(options and len(options) > 0)

        # Determine badge & option Y positions based on whether options exist
        if has_options:
            opt_labels = ["A", "B", "C", "D"]
            base_opt_y = 960
            opt_spacing = 110

            for i, opt_text in enumerate(options[:4]):
                opt_letter = opt_labels[i]
                safe_opt = str(opt_text).replace("'", "").replace(":", "\\:").strip()
                # If text already starts with "A)" or "A:", avoid double prefix
                if safe_opt.upper().startswith(f"{opt_letter})") or safe_opt.upper().startswith(f"{opt_letter}:"):
                    opt_display = safe_opt
                else:
                    opt_display = f"{opt_letter})  {safe_opt}"

                curr_opt_y = base_opt_y + (i * opt_spacing)
                if anim_style in ["slide", "bounce", "pop"]:
                    delay_s = 0.1 + (i * 0.08)
                    y_expr = build_overshoot_y_expr(curr_opt_y, delay_s)
                else:
                    y_expr = str(curr_opt_y)

                next_layer = f"with_opt_{i+1}"
                filter_chains.append(
                    f"[{options_layer}]drawtext=fontfile='{font_path}':text='{opt_display}':"
                    f"fontcolor=white:fontsize=46:x=(w-text_w)/2:y='{y_expr}':"
                    f"borderw=6:bordercolor=black@0.95:shadowcolor=black@0.9:shadowx=4:shadowy=4:"
                    f"box=1:boxcolor=0x0F172A@0.75:boxborderw=16:"
                    f"enable='between(t,0,{t_ans_start})'[{next_layer}]"
                )
                options_layer = next_layer

            # Highlight the single correct option (by correct_index) with a green
            # box, checkmark, and pulse once the answer reveal begins. The
            # un-highlighted options simply vanish at t_ans_start (unchanged
            # behavior from the loop above) -- only the correct option is
            # restyled and kept visible during the reveal.
            if correct_index is not None and 0 <= correct_index < len(options[:4]):
                highlight_filters, options_layer = self._build_option_highlight_filters(
                    options_layer=options_layer,
                    options=options,
                    correct_index=correct_index,
                    t_ans_start=t_ans_start,
                    font_path=font_path,
                    input_layer_idx=input_count,
                )
                filter_chains.extend(highlight_filters)

            # Adjust countdown badge position lower to fit neatly below options
            badge_base_y = base_opt_y + (len(options[:4]) * opt_spacing) + 20
            num_base_y = badge_base_y + 60
        else:
            badge_base_y = 980
            num_base_y = 1040

        # ── (g) Countdown Badges & Numbers (Pop-in animation) ──
        if anim_style != "none":
            b3_y = f"{badge_base_y}-25*max(0,1-((t-{t_cd_start})/0.25))"
            n3_y = f"{num_base_y}-25*max(0,1-((t-{t_cd_start})/0.25))"
            b2_y = f"{badge_base_y}-25*max(0,1-((t-{t_cd_3_end})/0.25))"
            n2_y = f"{num_base_y}-25*max(0,1-((t-{t_cd_3_end})/0.25))"
            b1_y = f"{badge_base_y}-25*max(0,1-((t-{t_cd_2_end})/0.25))"
            n1_y = f"{num_base_y}-25*max(0,1-((t-{t_cd_2_end})/0.25))"
        else:
            b3_y, n3_y = str(badge_base_y), str(num_base_y)
            b2_y, n2_y = str(badge_base_y), str(num_base_y)
            b1_y, n1_y = str(badge_base_y), str(num_base_y)

        # Badge 3
        filter_chains.append(
            f"[{options_layer}][7:v]overlay=x=390:y='{b3_y}':enable='between(t,{t_cd_start},{t_cd_3_end})'[with_badge_3]"
        )
        filter_chains.append(
            f"[with_badge_3]drawtext=fontfile='{font_path}':text='3':fontcolor=white:fontsize=170:"
            f"x=(w-text_w)/2:y='{n3_y}':borderw=8:bordercolor=0x0F172A:shadowcolor=black@0.9:shadowx=5:shadowy=5:enable='between(t,{t_cd_start},{t_cd_3_end})'[with_num_3]"
        )

        # Badge 2
        filter_chains.append(
            f"[with_num_3][8:v]overlay=x=390:y='{b2_y}':enable='between(t,{t_cd_3_end},{t_cd_2_end})'[with_badge_2]"
        )
        filter_chains.append(
            f"[with_badge_2]drawtext=fontfile='{font_path}':text='2':fontcolor=0xFBAA19:fontsize=170:"
            f"x=(w-text_w)/2:y='{n2_y}':borderw=8:bordercolor=0x0F172A:shadowcolor=black@0.9:shadowx=5:shadowy=5:enable='between(t,{t_cd_3_end},{t_cd_2_end})'[with_num_2]"
        )

        # Badge 1
        filter_chains.append(
            f"[with_num_2][9:v]overlay=x=390:y='{b1_y}':enable='between(t,{t_cd_2_end},{t_cd_end})'[with_badge_1]"
        )
        filter_chains.append(
            f"[with_badge_1]drawtext=fontfile='{font_path}':text='1':fontcolor=0xEF4444:fontsize=170:"
            f"x=(w-text_w)/2:y='{n1_y}':borderw=8:bordercolor=0x0F172A:shadowcolor=black@0.9:shadowx=5:shadowy=5:enable='between(t,{t_cd_2_end},{t_cd_end})'[with_num_1]"
        )

        # ── (g) Answer Card Frame & Text (Slide-in from below) ──
        if anim_style in ["slide", "bounce", "pop"]:
            a_card_y = f"if(lt(t-{t_ans_start},0.35),970+950*(1-min(1,(t-{t_ans_start})/0.35))*(1-min(1,(t-{t_ans_start})/0.35)),970)"
            a_hdr_y = f"if(lt(t-{t_ans_start},0.35),1010+950*(1-min(1,(t-{t_ans_start})/0.35))*(1-min(1,(t-{t_ans_start})/0.35)),1010)"
            a_txt_y = f"if(lt(t-{t_ans_start},0.35),(1265-(text_h/2))+950*(1-min(1,(t-{t_ans_start})/0.35))*(1-min(1,(t-{t_ans_start})/0.35)),1265-(text_h/2))"
        else:
            a_card_y = "970"
            a_hdr_y = "1010"
            a_txt_y = "1265-(text_h/2)"

        escaped_a_file = str(a_text_file).replace(":", "\\:")
        filter_chains.append(
            f"[with_num_1][6:v]overlay=x=70:y='{a_card_y}':enable='gte(t,{t_ans_start})'[with_ans_frame]"
        )
        # This renders the original free-text `answer_text` param (e.g. "A Big Spotted
        # Cow!") purely as decorative flavor -- it is NEVER the authoritative answer.
        # The authoritative, spoken-and-displayed answer is the highlighted option
        # produced by _build_option_highlight_filters() in section (f) above.
        filter_chains.append(
            f"[with_ans_frame]drawtext=fontfile='{font_path}':text='FUN FACT':fontcolor=0xFDE047:fontsize=34:"
            f"x=(w-text_w)/2:y='{a_hdr_y}':borderw=4:bordercolor=black@0.9:shadowcolor=black@0.9:shadowx=3:shadowy=3:enable='gte(t,{t_ans_start})'[with_ans_header]"
        )
        filter_chains.append(
            f"[with_ans_header]drawtext=fontfile='{font_path}':textfile='{escaped_a_file}':"
            f"fontcolor=white@0.75:fontsize=32:x=(w-text_w)/2:y='{a_txt_y}':line_spacing=20:"
            f"borderw=6:bordercolor=black@0.95:shadowcolor=black@0.95:shadowx=4:shadowy=4:enable='gte(t,{t_ans_start})'[with_ans_text]"
        )

        last_layer = "with_ans_text"

        # ── (h) Answer Reveal Flash (0.25s subtle white bloom) ──
        if getattr(config, "answer_flash", True):
            flash_dur = 0.25
            filter_chains.append(
                f"color=c=white:s={config.width}x{config.height}:d={flash_dur},"
                f"format=rgba,"
                f"fade=t=in:st=0:d=0.05:alpha=1,"
                f"fade=t=out:st=0.05:d=0.20:alpha=1[flash_src]"
            )
            filter_chains.append(
                f"[{last_layer}][flash_src]overlay=x=0:y=0:enable='between(t,{t_ans_start},{t_ans_start + flash_dur})'[with_flash]"
            )
            last_layer = "with_flash"

        # ── (i) Celebratory Confetti VFX Overlay ──
        if confetti_input_idx is not None:
            filter_chains.append(
                f"[{confetti_input_idx}:v]scale={config.width}:{config.height}[confetti_scaled]"
            )
            filter_chains.append(
                f"[{last_layer}][confetti_scaled]overlay=x=0:y=0:enable='between(t,{t_ans_start},{t_ans_start}+2.0)'[with_confetti]"
            )
            last_layer = "with_confetti"

        # Final video output
        filter_chains.append(f"[{last_layer}]null[vout]")

        full_filter_complex = ";\n".join(filter_chains)

        cmd = [
            ffmpeg_bin, "-y",
            *input_args,
            "-filter_complex", full_filter_complex,
            "-map", "[vout]",
            "-map", "1:a",
            "-t", str(total_duration),
            "-c:v", config.video_codec,
            "-preset", "fast",
            "-b:v", config.video_bitrate,
            "-pix_fmt", config.pix_fmt,
            "-r", str(config.fps),
            "-c:a", config.audio_codec,
            "-b:a", "192k",
            str(output_mp4_path)
        ]

        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg video encoding failed:\n{proc.stderr}")

        return output_mp4_path


video_service = VideoService()


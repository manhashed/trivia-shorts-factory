import os
import subprocess
import asyncio
from backend.app.services.ass_maker import create_ass_file
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import textwrap

from backend.app.config import FONTS_DIR, IMAGES_DIR, ASSETS_DIR, TEMP_DIR, OUTPUTS_DIR, settings
from backend.app.models.poem_schemas import PoemItem, PoemRenderConfig
from backend.app.services.tts.tts_manager import tts_manager
from backend.app.services.vfx_helpers import build_cinematic_bg_filter
from backend.app.utils.ffmpeg_check import get_ffmpeg_binary, probe_media_file


class PoemService:
    """
    Studio engine for generating Singing & Dancing Mascot Poem Shorts (9:16 vertical).
    Combines neural singing voiceover, nursery melody mixing with auto-ducking,
    120 BPM rhythmic dancing mascot sprite animation, and karaoke lyric cards.
    """

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

    def _get_dance_sprite_paths(self, mascot_id: str) -> tuple[Path, Path, Path, Path]:
        dance_dir = ASSETS_DIR / "images" / "mascots_dance"
        d1 = dance_dir / f"{mascot_id}_d1.png"
        d2 = dance_dir / f"{mascot_id}_d2.png"
        d3 = dance_dir / f"{mascot_id}_d3.png"
        d4 = dance_dir / f"{mascot_id}_d4.png"

        if not d1.is_file():
            # Fallback to bear
            d1 = dance_dir / "bear_d1.png"
            d2 = dance_dir / "bear_d2.png"
            d3 = dance_dir / "bear_d3.png"
            d4 = dance_dir / "bear_d4.png"
        return d1, d2, d3, d4

    async def prepare_poem_audio(
        self,
        poem: PoemItem,
        work_dir: Path,
        config: PoemRenderConfig,
    ) -> tuple[Path, float, Path]:
        work_dir.mkdir(parents=True, exist_ok=True)
        ffmpeg_bin = get_ffmpeg_binary()

        # 1. Synthesize Poem Lyrics (Line by Line for Karaoke Timing)
        tts_raw_path = work_dir / "tts_poem_raw.wav"
        concat_txt_path = work_dir / "concat.txt"
        silence_path = work_dir / "silence.wav"
        
        # Create a 0.6s silence for between lines
        subprocess.run([ffmpeg_bin, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "0.6", str(silence_path)], capture_output=True)

        lines_timing = []
        current_time = 0.0
        
        concat_lines = []
        for i, line_text in enumerate(poem.lines):
            line_wav = work_dir / f"line_{i}.wav"
            await tts_manager.synthesize(
                text=line_text,
                output_path=line_wav,
                provider_name=config.tts_provider,
                voice=config.tts_voice,
                rate=config.tts_speed,
            )
            dur = probe_media_file(line_wav).get("duration", 2.0)
            lines_timing.append({
                "text": line_text,
                "start": current_time,
                "end": current_time + dur,
                "duration": dur
            })
            concat_lines.append(f"file '{line_wav.name}'")
            current_time += dur
            
            # Add pause between lines (unless it's the last line)
            if i < len(poem.lines) - 1:
                concat_lines.append(f"file '{silence_path.name}'")
                current_time += 0.6
                
        # Write concat list
        concat_txt_path.write_text("\n".join(concat_lines))
        
        # Concat all lines
        subprocess.run([
            ffmpeg_bin, "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_txt_path),
            "-c", "copy", str(tts_raw_path)
        ], capture_output=True)

        # Generate ASS Subtitle File
        ass_path = work_dir / "karaoke.ass"
        create_ass_file(lines_timing, str(ass_path), style=config.karaoke_style)

        tts_duration = current_time
        # Add 1.5s outro pause for music tail
        total_duration = round(tts_duration + 1.5, 2)

        # 2. Accompaniment Melody Loop
        melody_name = f"{config.melody_track}.wav" if not config.melody_track.endswith(".wav") else config.melody_track
        melody_path = ASSETS_DIR / "audio" / "melodies" / melody_name
        if not melody_path.is_file():
            melody_path = ASSETS_DIR / "audio" / "melodies" / "twinkle_star.wav"

        master_audio_path = work_dir / "master_poem_audio.wav"

        if config.melody_track != "none" and melody_path.is_file():
            # Auto-ducking filter: TTS voice (0:a) + Ducked Melody loop (1:a)
            # Melody volume scaled to config.melody_volume, ducked during speech
            vol_db = f"{int(config.melody_volume * 100)}%"
            cmd = [
                ffmpeg_bin, "-y",
                "-i", str(tts_raw_path),
                "-stream_loop", "-1", "-i", str(melody_path),
                "-filter_complex",
                f"[1:a]volume={config.melody_volume}[music];"
                f"[music][0:a]sidechaincompress=threshold=0.08:ratio=4:attack=50:release=300[ducked_music];"
                f"[0:a][ducked_music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
                "-map", "[aout]",
                "-t", str(total_duration),
                "-ar", "44100",
                "-ac", "2",
                str(master_audio_path),
            ]
        else:
            # TTS voice only
            cmd = [
                ffmpeg_bin, "-y",
                "-i", str(tts_raw_path),
                "-af", f"apad=pad_dur=1.5",
                "-t", str(total_duration),
                "-ar", "44100",
                "-ac", "2",
                str(master_audio_path),
            ]

        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"Poem audio preparation failed:\n{proc.stderr}")

        return master_audio_path, total_duration, ass_path

    async def render_poem_short(
        self,
        poem: PoemItem,
        bg_video_path: Path,
        output_mp4_path: Path,
        work_dir: Path,
        config: PoemRenderConfig,
    ) -> Path:
        work_dir.mkdir(parents=True, exist_ok=True)
        output_mp4_path.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg_bin = get_ffmpeg_binary()
        font_path = self._get_font_path()

        # 1. Prepare Audio
        master_audio, total_duration, ass_path = await self.prepare_poem_audio(poem, work_dir, config)

        # 2. Assets Paths
        ui_dir = ASSETS_DIR / "ui"
        header_pill_png = ui_dir / "header_pill.png"
        lyric_card_png = ui_dir / "question_card_frame.png"
        d1, d2, d3, d4 = self._get_dance_sprite_paths(config.mascot_id)

        # 3. Lyric lines text file
        formatted_lyrics = "\n\n".join(poem.lines)
        lyric_text_file = work_dir / "lyrics.txt"
        with open(lyric_text_file, "w", encoding="utf-8") as f:
            f.write(formatted_lyrics)

        # 4. Dance rhythm timing: 120 BPM = 0.5s per step (2.0s full 4-step loop)
        step_dur = round(60.0 / config.dance_bpm, 3) # e.g. 0.500
        loop_dur = round(step_dur * 4.0, 3)          # e.g. 2.000

        # Input Mapping:
        # Input 0: Background video
        # Input 1: Master Audio
        # Input 2: header_pill.png
        # Input 3: lyric_card_png
        # Input 4: d1 (Step Left)
        # Input 5: d2 (Sing Open Mouth)
        # Input 6: d3 (Step Right)
        # Input 7: d4 (Airborne Jump)

        filter_chains = []

        # (a) Background scale & crop + VIBRANT GRAPHICS (attention grabber)
        filter_chains.append(
            build_cinematic_bg_filter(
                input_label="0:v",
                output_label="base_bg",
                width=config.width,
                height=config.height,
                total_duration=total_duration,
                fps=config.fps,
                zoom_enabled=True,
            )
        )

        # (b) Header Title Banner (x=70, y=130)
        filter_chains.append(
            f"[base_bg][2:v]overlay=x=70:y=130[with_hdr_frame]"
        )
        safe_title = poem.title.replace("'", "\\'")
        filter_chains.append(
            f"[with_hdr_frame]drawtext=fontfile='{font_path}':text='🎵 {safe_title} 🎵':"
            f"fontcolor=0xFDE047:fontsize=46:x=(w-text_w)/2:y=175:"
            f"borderw=5:bordercolor=black@0.9:shadowcolor=black@0.9:shadowx=3:shadowy=3[with_hdr_text]"
        )

        # (c) Scale Dancing Sprites (440 x 440)
        filter_chains.append(
            f"[4:v]scale=440:440[sd1];"
            f"[5:v]scale=440:440[sd2];"
            f"[6:v]scale=440:440[sd3];"
            f"[7:v]scale=440:440[sd4]"
        )

        # (d) 120 BPM Rhythmic Beat-Synced Mascot Dance Overlays (Centered at x=320, y=320)
        # Step 1: d1 (Step Left)
        filter_chains.append(
            f"[with_hdr_text][sd1]overlay=x=320:y=330:enable='between(mod(t,{loop_dur}),0.0,{step_dur})'[dance_1]"
        )
        # Step 2: d2 (Singing Mouth Open)
        filter_chains.append(
            f"[dance_1][sd2]overlay=x=320:y=310:enable='between(mod(t,{loop_dur}),{step_dur},{step_dur*2})'[dance_2]"
        )
        # Step 3: d3 (Step Right)
        filter_chains.append(
            f"[dance_2][sd3]overlay=x=320:y=330:enable='between(mod(t,{loop_dur}),{step_dur*2},{step_dur*3})'[dance_3]"
        )
        # Step 4: d4 (Airborne Jump)
        filter_chains.append(
            f"[dance_3][sd4]overlay=x=320:y=280:enable='between(mod(t,{loop_dur}),{step_dur*3},{loop_dur})'[dance_mascot]"
        )

        # (e) Glassmorphic Lyric Card at Bottom (x=70, y=860, size scaled to 940x960)
        filter_chains.append(
            f"[3:v]scale=940:960[big_lyric_card];"
            f"[dance_mascot][big_lyric_card]overlay=x=70:y=860[with_lyric_frame]"
        )

        # (f) Sing-Along Subtitle Header & Lyrics Text (KARAOKE)
        escaped_ass_path = str(ass_path).replace(":", "\\:")
        filter_chains.append(
            f"[with_lyric_frame]drawtext=fontfile='{font_path}':text='✨ SING ALONG WITH ME! ✨':"
            f"fontcolor=0x38BDF8:fontsize=38:x=(w-text_w)/2:y=910:"
            f"borderw=4:bordercolor=black@0.9:shadowcolor=black@0.9:shadowx=3:shadowy=3[with_sing_hdr]"
        )
        # Apply the ASS subtitle filter for the glowing karaoke sweep!
        filter_chains.append(
            f"[with_sing_hdr]ass='{escaped_ass_path}'[vout]"
        )

        full_filter_complex = ";\n".join(filter_chains)

        cmd = [
            ffmpeg_bin, "-y",
            "-stream_loop", "-1", "-i", str(bg_video_path),
            "-i", str(master_audio),
            "-i", str(header_pill_png),
            "-i", str(lyric_card_png),
            "-i", str(d1),
            "-i", str(d2),
            "-i", str(d3),
            "-i", str(d4),
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
            str(output_mp4_path),
        ]

        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"Poem video rendering failed:\n{proc.stderr}")

        return output_mp4_path


poem_service = PoemService()

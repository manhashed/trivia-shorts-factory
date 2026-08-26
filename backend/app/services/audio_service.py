import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from backend.app.config import AUDIO_DIR, settings
from backend.app.models.schemas import VideoRenderConfig
from backend.app.services.tts.tts_manager import tts_manager
from backend.app.utils.ffmpeg_check import get_ffmpeg_binary, probe_media_file
from backend.app.utils.generate_sfx import (
    generate_all_sfx,
    generate_dynamic_countdown,
    generate_beep_countdown,
    generate_suspense_build,
    generate_whoosh,
    generate_impact_hit,
    generate_celebration_chime,
    generate_kids_cheer,
)

logger = logging.getLogger(__name__)


class AudioService:
    """
    Studio-grade audio engineering service for AI Shorts.
    Combines TTS narration, multi-layered SFX (whooshes, suspense drone, dynamic tick-tock,
    impact punch, fanfare chime, crowd cheer), dynamic BGM sidechain ducking,
    and EBU R128 (loudnorm) loudness normalization.
    """

    def __init__(self):
        self._ensure_sfx()

    def _ensure_sfx(self):
        """Ensures all standard audio SFX files exist in AUDIO_DIR."""
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        required = [
            "celebration_chime.wav",
            "dynamic_countdown.wav",
            "whoosh.wav",
            "suspense_build.wav",
            "impact_hit.wav",
            "kids_cheer.wav",
        ]
        missing = [f for f in required if not (AUDIO_DIR / f).is_file()]
        if missing:
            try:
                generate_all_sfx(AUDIO_DIR)
            except Exception as e:
                logger.warning(f"Failed to auto-generate all SFX: {e}")

    async def prepare_quiz_audio(
        self,
        question_text: str,
        answer_text: str,
        work_dir: Path,
        config: VideoRenderConfig,
    ) -> Tuple[Path, Dict[str, float]]:
        """
        Synthesizes question & answer TTS, mixes countdown SFX, transition whooshes,
        answer impact hits, chime fanfare, and ducked BGM into a sample-accurate
        broadcast-grade master audio WAV file.
        """
        work_dir.mkdir(parents=True, exist_ok=True)
        ffmpeg_bin = get_ffmpeg_binary()
        sfx_vol = getattr(config, "sfx_volume", 0.6)

        # 1. Synthesize Question Audio
        q_audio_path = work_dir / "q_tts.wav"
        spoken_question = question_text
        if getattr(config, "audience_prompt", True):
            spoken_question = f"Can you guess? {question_text}"
        q_duration = await tts_manager.synthesize(
            text=spoken_question,
            output_path=q_audio_path,
            provider_name=config.tts_provider,
            voice=config.tts_voice,
            rate=config.tts_speed,
            pitch=config.tts_pitch,
            openai_api_key=config.openai_api_key,
            elevenlabs_api_key=config.elevenlabs_api_key,
        )

        # 2. Synthesize Answer Audio
        # Use child-engaging phrasing if not already present
        if not answer_text.lower().startswith("the answer") and not answer_text.lower().startswith("it's") and not answer_text.lower().startswith("it is"):
            answer_spoken_text = f"The answer is... {answer_text}!"
        else:
            answer_spoken_text = answer_text

        a_audio_path = work_dir / "a_tts.wav"
        a_duration = await tts_manager.synthesize(
            text=answer_spoken_text,
            output_path=a_audio_path,
            provider_name=config.tts_provider,
            voice=config.tts_voice,
            rate=config.tts_speed,
            pitch=config.tts_pitch,
            openai_api_key=config.openai_api_key,
            elevenlabs_api_key=config.elevenlabs_api_key,
        )

        # 3. Calculate Exact Timing Milestones
        countdown_sec = float(config.countdown_duration)
        post_pause_sec = float(config.post_answer_pause)

        t_question_start = 0.0
        t_countdown_start = round(q_duration, 3)
        t_countdown_end = round(t_countdown_start + countdown_sec, 3)
        t_answer_start = t_countdown_end
        t_answer_end = round(t_answer_start + a_duration, 3)
        total_duration = round(t_answer_end + post_pause_sec, 3)

        t_whoosh1_start = max(0.0, round(t_countdown_start - 0.25, 3))
        t_whoosh2_start = max(0.0, round(t_answer_start - 0.25, 3))

        timing_info = {
            "q_duration": q_duration,
            "countdown_duration": countdown_sec,
            "a_duration": a_duration,
            "post_pause": post_pause_sec,
            "t_question_start": t_question_start,
            "t_countdown_start": t_countdown_start,
            "t_countdown_end": t_countdown_end,
            "t_answer_start": t_answer_start,
            "t_answer_end": t_answer_end,
            "t_whoosh1_start": t_whoosh1_start,
            "t_whoosh2_start": t_whoosh2_start,
            "total_duration": total_duration,
            "has_suspense": True,
        }

        # 4. Prepare Countdown Segment (Tick-Tock + Suspense Drone)
        countdown_wav = work_dir / "countdown_segment.wav"
        if config.countdown_sfx != "mute":
            # Generate exact-length dynamic countdown and suspense
            num_ticks = max(1, int(round(countdown_sec)))
            raw_ticks_wav = work_dir / "raw_ticks.wav"
            raw_suspense_wav = work_dir / "raw_suspense.wav"

            try:
                countdown_generator = generate_beep_countdown if config.countdown_sfx == "beep" else generate_dynamic_countdown
                countdown_generator(raw_ticks_wav, duration=countdown_sec, num_ticks=num_ticks)
                generate_suspense_build(raw_suspense_wav, duration=countdown_sec)

                # Mix tick-tock and subtle suspense drone
                tick_v = max(0.1, min(1.0, sfx_vol * 1.2))
                suspense_v = max(0.05, min(0.6, sfx_vol * 0.45))

                filter_cd = (
                    f"[0:a]volume={tick_v}[t];"
                    f"[1:a]volume={suspense_v}[s];"
                    f"[t][s]amix=inputs=2:duration=first:dropout_transition=0[out_cd]"
                )
                cmd_cd = [
                    ffmpeg_bin, "-y",
                    "-i", str(raw_ticks_wav),
                    "-i", str(raw_suspense_wav),
                    "-filter_complex", filter_cd,
                    "-map", "[out_cd]",
                    "-ar", "44100", "-ac", "2",
                    str(countdown_wav)
                ]
                subprocess.run(cmd_cd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except Exception as e:
                logger.warning(f"Dynamic countdown synthesis fallback: {e}")
                # Fallback to existing asset or silence
                sfx_asset = AUDIO_DIR / "dynamic_countdown.wav"
                if sfx_asset.is_file():
                    cmd_fallback = [
                        ffmpeg_bin, "-y",
                        "-i", str(sfx_asset),
                        "-t", str(countdown_sec),
                        "-ar", "44100", "-ac", "2",
                        str(countdown_wav)
                    ]
                    subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                else:
                    cmd_silence = [
                        ffmpeg_bin, "-y",
                        "-f", "lavfi",
                        "-i", "anullsrc=r=44100:cl=stereo",
                        "-t", str(countdown_sec),
                        str(countdown_wav)
                    ]
                    subprocess.run(cmd_silence, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        else:
            # Mute countdown
            cmd_silence = [
                ffmpeg_bin, "-y",
                "-f", "lavfi",
                "-i", "anullsrc=r=44100:cl=stereo",
                "-t", str(countdown_sec),
                str(countdown_wav)
            ]
            subprocess.run(cmd_silence, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # 5. Prepare Answer SFX Mix (Answer TTS + Impact Punch + Fanfare Chime + Kids Cheer)
        answer_mixed_wav = work_dir / "answer_segment.wav"
        chime_file = AUDIO_DIR / "celebration_chime.wav"
        impact_file = AUDIO_DIR / "impact_hit.wav"
        cheer_file = AUDIO_DIR / "kids_cheer.wav"

        # Build multi-layer celebratory answer audio
        ans_inputs = ["-i", str(a_audio_path)]
        filter_parts = ["[0:a]volume=1.0[speech]"]
        mix_inputs = ["[speech]"]
        input_idx = 1

        if impact_file.is_file():
            ans_inputs.extend(["-i", str(impact_file)])
            impact_v = max(0.1, min(1.0, sfx_vol * 0.9))
            filter_parts.append(f"[{input_idx}:a]volume={impact_v}[impact]")
            mix_inputs.append("[impact]")
            input_idx += 1

        if chime_file.is_file():
            ans_inputs.extend(["-i", str(chime_file)])
            chime_v = max(0.1, min(1.0, sfx_vol * 0.75))
            filter_parts.append(f"[{input_idx}:a]volume={chime_v}[chime]")
            mix_inputs.append("[chime]")
            input_idx += 1

        if cheer_file.is_file():
            ans_inputs.extend(["-i", str(cheer_file)])
            cheer_v = max(0.05, min(0.8, sfx_vol * 0.5))
            filter_parts.append(f"[{input_idx}:a]volume={cheer_v}[cheer]")
            mix_inputs.append("[cheer]")
            input_idx += 1

        if len(mix_inputs) > 1:
            mix_chain = "".join(mix_inputs) + f"amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=0[out_ans]"
            filter_parts.append(mix_chain)
            full_ans_filter = ";".join(filter_parts)

            cmd_ans = [
                ffmpeg_bin, "-y",
                *ans_inputs,
                "-filter_complex", full_ans_filter,
                "-map", "[out_ans]",
                "-ar", "44100", "-ac", "2",
                str(answer_mixed_wav)
            ]
            proc_ans = subprocess.run(cmd_ans, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc_ans.returncode != 0:
                logger.warning(f"Answer mix failed: {proc_ans.stderr.decode() if isinstance(proc_ans.stderr, bytes) else proc_ans.stderr}")
                answer_mixed_wav = a_audio_path
        else:
            answer_mixed_wav = a_audio_path

        # 6. Generate Outro Silence Segment
        outro_wav = work_dir / "outro_segment.wav"
        cmd_outro = [
            ffmpeg_bin, "-y",
            "-f", "lavfi",
            "-i", "anullsrc=r=44100:cl=stereo",
            "-t", str(post_pause_sec),
            str(outro_wav)
        ]
        subprocess.run(cmd_outro, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # 7. Concatenate Main Audio Track: [Q] + [COUNTDOWN] + [ANSWER_MIX] + [OUTRO]
        concatenated_voice_track = work_dir / "concat_voice.wav"
        concat_filter = "[0:a][1:a][2:a][3:a]concat=n=4:v=0:a=1[out_cat]"
        cmd_concat = [
            ffmpeg_bin, "-y",
            "-i", str(q_audio_path),
            "-i", str(countdown_wav),
            "-i", str(answer_mixed_wav),
            "-i", str(outro_wav),
            "-filter_complex", concat_filter,
            "-map", "[out_cat]",
            "-ar", "44100", "-ac", "2",
            str(concatenated_voice_track)
        ]
        subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # 8. Layer Transition Whooshes
        whoosh_file = AUDIO_DIR / "whoosh.wav"
        layered_voice_track = work_dir / "layered_voice.wav"

        if whoosh_file.is_file() and sfx_vol > 0.05:
            whoosh_v = max(0.05, min(0.8, sfx_vol * 0.55))
            w1_delay_ms = int(max(0, t_whoosh1_start * 1000))
            w2_delay_ms = int(max(0, t_whoosh2_start * 1000))

            filter_whooshes = (
                f"[0:a]volume=1.0[main];"
                f"[1:a]volume={whoosh_v},adelay={w1_delay_ms}|{w1_delay_ms}[w1];"
                f"[2:a]volume={whoosh_v},adelay={w2_delay_ms}|{w2_delay_ms}[w2];"
                f"[main][w1][w2]amix=inputs=3:duration=first:dropout_transition=0[out_w]"
            )
            cmd_w = [
                ffmpeg_bin, "-y",
                "-i", str(concatenated_voice_track),
                "-i", str(whoosh_file),
                "-i", str(whoosh_file),
                "-filter_complex", filter_whooshes,
                "-map", "[out_w]",
                "-ar", "44100", "-ac", "2",
                str(layered_voice_track)
            ]
            proc_w = subprocess.run(cmd_w, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc_w.returncode != 0:
                layered_voice_track = concatenated_voice_track
        else:
            layered_voice_track = concatenated_voice_track

        # 9. Mix Background Music (BGM) with Dynamic Sidechain Ducking
        bgm_mixed_path = work_dir / "bgm_mixed.wav"
        bgm_file = AUDIO_DIR / "bgm" / f"{config.bgm_track}_bgm.wav" if config.bgm_track != "none" else None

        if bgm_file and bgm_file.is_file() and config.bgm_volume > 0.01:
            bgm_vol = max(0.02, min(0.5, float(config.bgm_volume)))
            # Dynamic sidechain compression: BGM ducks automatically whenever voice/sfx peaks
            filter_sidechain = (
                f"[0:a]asplit=2[voice_main][voice_sc];"
                f"[1:a]volume={bgm_vol}[music];"
                f"[music][voice_sc]sidechaincompress=threshold=0.03:ratio=5:attack=50:release=400:level_in=1:level_sc=1[ducked_music];"
                f"[voice_main][ducked_music]amix=inputs=2:duration=first:dropout_transition=0[out_bgm]"
            )
            cmd_bgm = [
                ffmpeg_bin, "-y",
                "-i", str(layered_voice_track),
                "-stream_loop", "-1", "-i", str(bgm_file),
                "-filter_complex", filter_sidechain,
                "-map", "[out_bgm]",
                "-t", str(total_duration),
                "-ar", "44100", "-ac", "2",
                str(bgm_mixed_path)
            ]
            proc_bgm = subprocess.run(cmd_bgm, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc_bgm.returncode != 0:
                # Fallback to standard amix ducking
                filter_amix = f"[0:a]volume=1.0[v];[1:a]volume={bgm_vol}[m];[v][m]amix=inputs=2:duration=first:dropout_transition=0[out_bgm]"
                cmd_bgm_fb = [
                    ffmpeg_bin, "-y",
                    "-i", str(layered_voice_track),
                    "-stream_loop", "-1", "-i", str(bgm_file),
                    "-filter_complex", filter_amix,
                    "-map", "[out_bgm]",
                    "-t", str(total_duration),
                    "-ar", "44100", "-ac", "2",
                    str(bgm_mixed_path)
                ]
                proc_bgm_fb = subprocess.run(cmd_bgm_fb, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if proc_bgm_fb.returncode != 0:
                    bgm_mixed_path = layered_voice_track
        else:
            bgm_mixed_path = layered_voice_track

        # 10. Audio Normalization (EBU R128 loudnorm)
        master_audio_path = work_dir / "master_audio.wav"
        if getattr(config, "audio_normalize", True):
            # Target integrated loudness -16 LUFS (standard for YouTube Shorts & TikTok), True Peak -1.5 dBTP
            filter_norm = "loudnorm=I=-16:TP=-1.5:LRA=11"
            cmd_norm = [
                ffmpeg_bin, "-y",
                "-i", str(bgm_mixed_path),
                "-af", filter_norm,
                "-ar", "44100", "-ac", "2",
                str(master_audio_path)
            ]
            proc_norm = subprocess.run(cmd_norm, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc_norm.returncode != 0:
                master_audio_path = bgm_mixed_path
        else:
            master_audio_path = bgm_mixed_path

        final_probe = probe_media_file(master_audio_path)
        timing_info["actual_master_duration"] = final_probe.get("duration", total_duration)

        return master_audio_path, timing_info


audio_service = AudioService()


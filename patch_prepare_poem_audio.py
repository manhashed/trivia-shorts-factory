import re

with open("backend/app/services/poem_service.py", "r") as f:
    content = f.read()

new_imports = """import os
import subprocess
import asyncio
from backend.app.services.ass_maker import create_ass_file"""

content = content.replace("import asyncio", new_imports)

old_code = """        # 1. Synthesize Poem Lyrics
        full_lyrics = " ... ".join(poem.lines)
        tts_raw_path = work_dir / "tts_poem_raw.wav"
        await tts_manager.synthesize(
            text=full_lyrics,
            output_path=tts_raw_path,
            provider_name=config.tts_provider,
            voice=config.tts_voice,
            rate=config.tts_speed,
        )

        probe_tts = probe_media_file(tts_raw_path)
        tts_duration = probe_tts.get("duration", 6.0)
        # Add 1.5s outro pause for music tail
        total_duration = round(tts_duration + 1.5, 2)"""

new_code = """        # 1. Synthesize Poem Lyrics (Line by Line for Karaoke Timing)
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
        concat_txt_path.write_text("\\n".join(concat_lines))
        
        # Concat all lines
        subprocess.run([
            ffmpeg_bin, "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_txt_path),
            "-c", "copy", str(tts_raw_path)
        ], capture_output=True)

        # Generate ASS Subtitle File
        ass_path = work_dir / "karaoke.ass"
        create_ass_file(lines_timing, str(ass_path))

        tts_duration = current_time
        # Add 1.5s outro pause for music tail
        total_duration = round(tts_duration + 1.5, 2)"""

content = content.replace(old_code, new_code)

with open("backend/app/services/poem_service.py", "w") as f:
    f.write(content)


with open("backend/app/services/poem_service.py", "r") as f:
    content = f.read()

content = content.replace(
    ") -> tuple[Path, float]:",
    ") -> tuple[Path, float, Path]:"
)

content = content.replace(
    "return master_audio_path, total_duration",
    "return master_audio_path, total_duration, ass_path"
)

content = content.replace(
    "master_audio, total_duration = await self.prepare_poem_audio(poem, work_dir, config)",
    "master_audio, total_duration, ass_path = await self.prepare_poem_audio(poem, work_dir, config)"
)

with open("backend/app/services/poem_service.py", "w") as f:
    f.write(content)

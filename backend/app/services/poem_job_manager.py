import asyncio
import datetime
import uuid
import re
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

from backend.app.config import TEMP_DIR, OUTPUTS_DIR, ASSETS_DIR, settings
from backend.app.models.poem_schemas import (
    PoemItem,
    PoemRenderConfig,
    PoemBatchJobState,
    PoemBatchItemStatus,
)
from backend.app.services.poem_service import poem_service
from backend.app.services.zip_service import zip_service
from backend.app.utils.ffmpeg_check import probe_media_file

POEM_MASCOTS_ROTATION = [
    ("bear", "en-US-AnaNeural"),
    ("penguin", "en-US-JennyNeural"),
    ("lion", "en-US-GuyNeural"),
    ("bunny", "en-GB-SoniaNeural"),
]

POEM_TEMPLATES_ROTATION = [
    ("candy_clouds", "candy_clouds.mp4"),
    ("space_galaxy", "space_galaxy.mp4"),
    ("safari_jungle", "safari_jungle.mp4"),
    ("ocean_bubbles", "ocean_bubbles.mp4"),
    ("arcade_retro", "arcade_retro.mp4"),
]

POEM_MELODIES_ROTATION = [
    "twinkle_star",
    "playful_ukulele",
    "storybook_bells",
    "bouncy_march",
]


def slugify_text(text: str, max_words: int = 4) -> str:
    words = re.findall(r"\w+", text.lower())[:max_words]
    slug = "_".join(words)
    return slug or "poem"


class PoemJobManager:
    """
    Async batch manager for Poem shorts with error isolation and SSE live updates.
    """

    def __init__(self):
        self.jobs: Dict[str, PoemBatchJobState] = {}
        self.job_configs: Dict[str, PoemRenderConfig] = {}
        self.job_bg_videos: Dict[str, Path] = {}
        self.job_raw_poems: Dict[str, List[PoemItem]] = {}
        self.listeners: Dict[str, Set[asyncio.Queue]] = {}
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_renders)

    def create_job(
        self,
        poems: List[PoemItem],
        bg_video_path: Path,
        config: PoemRenderConfig,
    ) -> PoemBatchJobState:
        job_id = f"poem_{str(uuid.uuid4())[:6]}"
        now_str = datetime.datetime.now().isoformat()

        batch_items = []
        for idx, poem in enumerate(poems):
            if config.mix_mode:
                mascot_id, voice = POEM_MASCOTS_ROTATION[idx % len(POEM_MASCOTS_ROTATION)]
                template_id, _ = POEM_TEMPLATES_ROTATION[idx % len(POEM_TEMPLATES_ROTATION)]
                melody = POEM_MELODIES_ROTATION[idx % len(POEM_MELODIES_ROTATION)]
            else:
                mascot_id = poem.mascot or config.mascot_id
                voice = config.tts_voice
                template_id = poem.theme or config.template_id
                melody = poem.melody or config.melody_track

            batch_items.append(
                PoemBatchItemStatus(
                    index=idx,
                    id=poem.id or f"poem_{idx + 1:03d}",
                    title=poem.title,
                    lines=poem.lines,
                    category=poem.category,
                    mascot_used=mascot_id,
                    template_used=template_id,
                    melody_used=melody,
                    voice_used=voice,
                    status="queued",
                    progress=0.0,
                )
            )

        state = PoemBatchJobState(
            job_id=job_id,
            created_at=now_str,
            status="pending",
            total_items=len(poems),
            completed_items=0,
            failed_items=0,
            overall_progress=0.0,
            items=batch_items,
        )

        self.jobs[job_id] = state
        self.job_configs[job_id] = config
        self.job_bg_videos[job_id] = bg_video_path
        self.job_raw_poems[job_id] = poems
        self.listeners[job_id] = set()

        return state

    def get_job(self, job_id: str) -> Optional[PoemBatchJobState]:
        return self.jobs.get(job_id)

    def add_listener(self, job_id: str) -> asyncio.Queue:
        q = asyncio.Queue()
        if job_id not in self.listeners:
            self.listeners[job_id] = set()
        self.listeners[job_id].add(q)
        return q

    def remove_listener(self, job_id: str, q: asyncio.Queue):
        if job_id in self.listeners and q in self.listeners[job_id]:
            self.listeners[job_id].remove(q)

    async def broadcast_state(self, job_id: str):
        state = self.jobs.get(job_id)
        if not state:
            return

        if state.total_items > 0:
            sum_prog = sum(item.progress for item in state.items)
            state.overall_progress = round(sum_prog / state.total_items, 1)

        payload = state.model_dump_json()
        if job_id in self.listeners:
            dead_queues = set()
            for q in self.listeners[job_id]:
                try:
                    q.put_nowait(payload)
                except Exception:
                    dead_queues.add(q)
            for dq in dead_queues:
                self.listeners[job_id].discard(dq)

    async def start_job(self, job_id: str):
        asyncio.create_task(self._process_batch_job(job_id))

    async def _process_batch_job(self, job_id: str):
        state = self.jobs.get(job_id)
        if not state:
            return

        base_config = self.job_configs[job_id]
        base_bg_video = self.job_bg_videos[job_id]
        poems = self.job_raw_poems[job_id]

        state.status = "processing"
        await self.broadcast_state(job_id)

        job_dir = TEMP_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        rendered_mp4s: List[Path] = []

        async def process_single(idx: int, poem: PoemItem):
            item_status = state.items[idx]
            slug = slugify_text(poem.title)
            filename = f"poem_{idx + 1:03d}_{slug}.mp4"
            output_mp4 = OUTPUTS_DIR / job_id / filename
            item_work_dir = job_dir / f"item_{idx + 1:03d}"

            item_config = base_config.model_copy()
            if base_config.mix_mode:
                mascot_id, voice = POEM_MASCOTS_ROTATION[idx % len(POEM_MASCOTS_ROTATION)]
                template_id, bg_filename = POEM_TEMPLATES_ROTATION[idx % len(POEM_TEMPLATES_ROTATION)]
                melody = POEM_MELODIES_ROTATION[idx % len(POEM_MELODIES_ROTATION)]

                item_config.mascot_id = mascot_id
                item_config.tts_voice = voice
                item_config.template_id = template_id
                item_config.melody_track = melody

                candidate_bg = ASSETS_DIR / "backgrounds" / bg_filename
                item_bg_video = candidate_bg if candidate_bg.is_file() else base_bg_video
            else:
                item_config.mascot_id = poem.mascot or base_config.mascot_id
                item_config.template_id = poem.theme or base_config.template_id
                item_config.melody_track = poem.melody or base_config.melody_track
                bg_filename = f"{item_config.template_id}.mp4"
                candidate_bg = ASSETS_DIR / "backgrounds" / bg_filename
                item_bg_video = candidate_bg if candidate_bg.is_file() else base_bg_video

            async with self._semaphore:
                try:
                    item_status.status = "tts_processing"
                    item_status.progress = 20.0
                    await self.broadcast_state(job_id)

                    item_status.status = "rendering"
                    item_status.progress = 50.0
                    await self.broadcast_state(job_id)

                    await poem_service.render_poem_short(
                        poem=poem,
                        bg_video_path=item_bg_video,
                        output_mp4_path=output_mp4,
                        work_dir=item_work_dir,
                        config=item_config,
                        quality_tier="final",
                    )

                    probe = probe_media_file(output_mp4)
                    if not probe["has_video"]:
                        raise RuntimeError("Rendered poem video contains no video stream.")

                    item_status.status = "completed"
                    item_status.progress = 100.0
                    item_status.output_filename = filename
                    item_status.video_url = f"/api/download/video/{job_id}/{filename}"
                    item_status.duration = probe.get("duration", 10.0)
                    state.completed_items += 1
                    rendered_mp4s.append(output_mp4)

                    if item_work_dir.exists():
                        shutil.rmtree(item_work_dir, ignore_errors=True)

                except Exception as e:
                    item_status.status = "failed"
                    item_status.progress = 0.0
                    item_status.error = str(e)
                    state.failed_items += 1

                await self.broadcast_state(job_id)

        tasks = [process_single(idx, poem) for idx, poem in enumerate(poems)]
        await asyncio.gather(*tasks)

        if rendered_mp4s:
            zip_name = f"poem_shorts_{job_id}.zip"
            zip_path = OUTPUTS_DIR / zip_name
            manifest = {
                "job_id": job_id,
                "type": "poem_shorts",
                "total_items": state.total_items,
                "completed_items": state.completed_items,
                "failed_items": state.failed_items,
                "created_at": state.created_at,
                "items": [it.model_dump() for it in state.items],
            }
            zip_service.create_batch_zip(rendered_mp4s, zip_path, manifest)
            state.zip_filename = zip_name
            state.zip_url = f"/api/download/zip/{zip_name}"

        if state.failed_items == 0:
            state.status = "completed"
        elif state.completed_items > 0:
            state.status = "partial_failure"
        else:
            state.status = "failed"
            state.error = "All poem videos failed to render."

        await self.broadcast_state(job_id)


poem_job_manager = PoemJobManager()

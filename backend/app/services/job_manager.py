import asyncio
import datetime
import uuid
import re
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import aiofiles

from backend.app.config import TEMP_DIR, OUTPUTS_DIR, ASSETS_DIR, UPLOADS_DIR, settings
from backend.app.models.schemas import (
    TriviaItem,
    VideoRenderConfig,
    BatchJobState,
    BatchItemStatus,
)
from backend.app.services.audio_service import audio_service
from backend.app.services.video_service import video_service
from backend.app.services.zip_service import zip_service
from backend.app.utils.ffmpeg_check import probe_media_file


MASCOTS_ROTATION = [
    ("bear", "en-US-AnaNeural"),
    ("penguin", "en-US-JennyNeural"),
    ("lion", "en-US-GuyNeural"),
    ("bunny", "en-GB-SoniaNeural"),
]

TEMPLATES_ROTATION = [
    ("candy_clouds", "candy_clouds.mp4"),
    ("space_galaxy", "space_galaxy.mp4"),
    ("safari_jungle", "safari_jungle.mp4"),
    ("ocean_bubbles", "ocean_bubbles.mp4"),
    ("arcade_retro", "arcade_retro.mp4"),
]

BGM_ROTATION = ["playful_nursery", "magical_story"]


def slugify_text(text: str, max_words: int = 4) -> str:
    words = re.findall(r"\w+", text.lower())[:max_words]
    slug = "_".join(words)
    return slug or "short"


class JobManager:
    """
    Manages batch job states, concurrent background rendering workers,
    error isolation, retry handling, SSE live progress streaming,
    and Mix/Randomize mode across mascots, themes, and voices.
    """

    def __init__(self):
        self.jobs: Dict[str, BatchJobState] = {}
        self.job_configs: Dict[str, VideoRenderConfig] = {}
        self.job_bg_videos: Dict[str, Path] = {}
        self.job_raw_items: Dict[str, List[TriviaItem]] = {}
        self.listeners: Dict[str, Set[asyncio.Queue]] = {}
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_renders)

    def create_job(
        self,
        items: List[TriviaItem],
        bg_video_path: Path,
        config: VideoRenderConfig,
    ) -> BatchJobState:
        job_id = str(uuid.uuid4())[:8]
        now_str = datetime.datetime.now().isoformat()

        batch_items = []
        for idx, item in enumerate(items):
            if config.mix_mode:
                mascot_id, voice = MASCOTS_ROTATION[idx % len(MASCOTS_ROTATION)]
                template_id, _ = TEMPLATES_ROTATION[idx % len(TEMPLATES_ROTATION)]
            else:
                mascot_id = config.mascot_id
                voice = config.tts_voice
                template_id = config.template_id

            batch_items.append(
                BatchItemStatus(
                    index=idx,
                    id=item.id or f"item_{idx + 1:03d}",
                    question=item.q,
                    answer=item.resolved_answer,
                    category=item.category,
                    options=item.options,
                    mascot_used=mascot_id,
                    template_used=template_id,
                    voice_used=voice,
                    status="queued",
                    progress=0.0,
                )
            )

        state = BatchJobState(
            job_id=job_id,
            created_at=now_str,
            status="pending",
            total_items=len(items),
            completed_items=0,
            failed_items=0,
            overall_progress=0.0,
            items=batch_items,
        )

        self.jobs[job_id] = state
        self.job_configs[job_id] = config
        self.job_bg_videos[job_id] = bg_video_path
        self.job_raw_items[job_id] = items
        self.listeners[job_id] = set()

        return state

    def get_job(self, job_id: str) -> Optional[BatchJobState]:
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
        items = self.job_raw_items[job_id]

        state.status = "processing"
        await self.broadcast_state(job_id)

        job_dir = TEMP_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        rendered_mp4s: List[Path] = []

        async def process_single(idx: int, item: TriviaItem):
            item_status = state.items[idx]
            item_slug = slugify_text(item.resolved_answer)
            filename = f"quiz_{idx + 1:03d}_{item_slug}.mp4"
            output_mp4 = OUTPUTS_DIR / job_id / filename
            item_work_dir = job_dir / f"item_{idx + 1:03d}"

            # If mix_mode is enabled, compute customized config and background video for this item
            item_config = base_config.model_copy()
            if base_config.mix_mode:
                mascot_id, voice = MASCOTS_ROTATION[idx % len(MASCOTS_ROTATION)]
                template_id, bg_filename = TEMPLATES_ROTATION[idx % len(TEMPLATES_ROTATION)]
                bgm = BGM_ROTATION[idx % len(BGM_ROTATION)]

                item_config.mascot_id = mascot_id
                item_config.tts_voice = voice
                item_config.template_id = template_id
                item_config.bgm_track = bgm
                
                # Check for background video in assets or uploads
                candidate_bg = ASSETS_DIR / "backgrounds" / bg_filename
                if candidate_bg.is_file():
                    item_bg_video = candidate_bg
                else:
                    item_bg_video = base_bg_video
            else:
                item_bg_video = base_bg_video

            async with self._semaphore:
                try:
                    item_status.status = "tts_processing"
                    item_status.progress = 20.0
                    await self.broadcast_state(job_id)

                    master_audio, timing = await audio_service.prepare_quiz_audio(
                        question_text=item.q,
                        answer_text=item.resolved_answer,
                        work_dir=item_work_dir,
                        config=item_config,
                    )

                    item_status.status = "rendering"
                    item_status.progress = 50.0
                    await self.broadcast_state(job_id)

                    await video_service.render_short_video(
                        bg_video_path=item_bg_video,
                        master_audio_path=master_audio,
                        timing_info=timing,
                        question_text=item.q,
                        answer_text=item.resolved_answer,
                        output_mp4_path=output_mp4,
                        work_dir=item_work_dir,
                        config=item_config,
                        options=item.options,
                    )

                    probe = probe_media_file(output_mp4)
                    if not probe["has_video"]:
                        raise RuntimeError("Rendered file contains no video stream.")

                    item_status.status = "completed"
                    item_status.progress = 100.0
                    item_status.output_filename = filename
                    item_status.video_url = f"/api/download/video/{job_id}/{filename}"
                    item_status.duration = probe.get("duration", timing["total_duration"])
                    state.completed_items += 1
                    rendered_mp4s.append(output_mp4)

                    if item_work_dir.exists():
                        shutil.rmtree(item_work_dir, ignore_errors=True)

                except Exception as e:
                    item_status.status = "failed"
                    item_status.progress = 0.0
                    item_status.error = str(e)
                    item_status.action_suggestion = "Verify voice settings and text characters or retry."
                    state.failed_items += 1

                await self.broadcast_state(job_id)

        tasks = [process_single(idx, item) for idx, item in enumerate(items)]
        await asyncio.gather(*tasks)

        if rendered_mp4s:
            zip_name = f"trivia_shorts_{job_id}.zip"
            zip_path = OUTPUTS_DIR / zip_name
            manifest = {
                "job_id": job_id,
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
            state.error = "All trivia video items in this batch failed to render."

        await self.broadcast_state(job_id)

    async def retry_failed_items(self, job_id: str):
        state = self.jobs.get(job_id)
        if not state:
            raise ValueError(f"Job {job_id} not found.")

        base_config = self.job_configs[job_id]
        base_bg_video = self.job_bg_videos[job_id]
        items = self.job_raw_items[job_id]

        failed_indices = [
            idx for idx, item in enumerate(state.items) if item.status == "failed"
        ]
        if not failed_indices:
            return

        state.status = "processing"
        state.failed_items = 0
        for idx in failed_indices:
            state.items[idx].status = "queued"
            state.items[idx].error = None
            state.items[idx].action_suggestion = None
            state.items[idx].progress = 0.0

        await self.broadcast_state(job_id)

        job_dir = TEMP_DIR / job_id
        rendered_mp4s: List[Path] = [
            OUTPUTS_DIR / job_id / it.output_filename
            for it in state.items
            if it.status == "completed" and it.output_filename
        ]

        async def retry_single(idx: int):
            item = items[idx]
            item_status = state.items[idx]
            item_slug = slugify_text(item.resolved_answer)
            filename = f"quiz_{idx + 1:03d}_{item_slug}.mp4"
            output_mp4 = OUTPUTS_DIR / job_id / filename
            item_work_dir = job_dir / f"item_{idx + 1:03d}"

            item_config = base_config.model_copy()
            if base_config.mix_mode:
                mascot_id, voice = MASCOTS_ROTATION[idx % len(MASCOTS_ROTATION)]
                template_id, bg_filename = TEMPLATES_ROTATION[idx % len(TEMPLATES_ROTATION)]
                bgm = BGM_ROTATION[idx % len(BGM_ROTATION)]

                item_config.mascot_id = mascot_id
                item_config.tts_voice = voice
                item_config.template_id = template_id
                item_config.bgm_track = bgm
                
                candidate_bg = ASSETS_DIR / "backgrounds" / bg_filename
                item_bg_video = candidate_bg if candidate_bg.is_file() else base_bg_video
            else:
                item_bg_video = base_bg_video

            async with self._semaphore:
                try:
                    item_status.status = "tts_processing"
                    item_status.progress = 20.0
                    await self.broadcast_state(job_id)

                    master_audio, timing = await audio_service.prepare_quiz_audio(
                        question_text=item.q,
                        answer_text=item.resolved_answer,
                        work_dir=item_work_dir,
                        config=item_config,
                    )

                    item_status.status = "rendering"
                    item_status.progress = 50.0
                    await self.broadcast_state(job_id)

                    await video_service.render_short_video(
                        bg_video_path=item_bg_video,
                        master_audio_path=master_audio,
                        timing_info=timing,
                        question_text=item.q,
                        answer_text=item.resolved_answer,
                        output_mp4_path=output_mp4,
                        work_dir=item_work_dir,
                        config=item_config,
                        options=item.options,
                    )

                    probe = probe_media_file(output_mp4)
                    item_status.status = "completed"
                    item_status.progress = 100.0
                    item_status.output_filename = filename
                    item_status.video_url = f"/api/download/video/{job_id}/{filename}"
                    item_status.duration = probe.get("duration", timing["total_duration"])
                    state.completed_items += 1
                    rendered_mp4s.append(output_mp4)

                    if item_work_dir.exists():
                        shutil.rmtree(item_work_dir, ignore_errors=True)

                except Exception as e:
                    item_status.status = "failed"
                    item_status.error = str(e)
                    item_status.action_suggestion = "Check voice credentials or error logs."
                    state.failed_items += 1

                await self.broadcast_state(job_id)

        tasks = [retry_single(idx) for idx in failed_indices]
        await asyncio.gather(*tasks)

        if rendered_mp4s:
            zip_name = f"trivia_shorts_{job_id}.zip"
            zip_path = OUTPUTS_DIR / zip_name
            manifest = {
                "job_id": job_id,
                "total_items": state.total_items,
                "completed_items": state.completed_items,
                "failed_items": state.failed_items,
                "created_at": state.created_at,
                "items": [it.model_dump() for it in state.items],
            }
            zip_service.create_batch_zip(rendered_mp4s, zip_path, manifest)
            state.zip_filename = zip_name
            state.zip_url = f"/api/download/zip/{zip_name}"

        state.status = "completed" if state.failed_items == 0 else "partial_failure"
        await self.broadcast_state(job_id)


job_manager = JobManager()

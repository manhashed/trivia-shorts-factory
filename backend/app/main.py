import asyncio
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import (
    PROJECT_ROOT,
    UPLOADS_DIR,
    OUTPUTS_DIR,
    TEMP_DIR,
    IMAGES_DIR,
    BASE_DIR,
    settings,
)
from backend.app.models.schemas import (
    TriviaItem,
    VideoRenderConfig,
    BatchJobState,
)
from backend.app.models.poem_schemas import (
    PoemItem,
    PoemRenderConfig,
    PoemBatchJobState,
)
from backend.app.services.validator import (
    validate_trivia_json,
    validate_background_video,
)
from backend.app.services.tts.tts_manager import tts_manager
from backend.app.services.audio_service import audio_service
from backend.app.services.video_service import video_service, TEMPLATE_STYLES
from backend.app.services.job_manager import job_manager
from backend.app.services.poem_service import poem_service
from backend.app.services.poem_job_manager import poem_job_manager
from backend.app.utils.ffmpeg_check import get_ffmpeg_binary, probe_media_file

app = FastAPI(
    title="AI Kids Shorts Factory (Trivia & Singing Poem Studios)",
    version="2.0.0",
    description="Automated pipeline for converting Trivia Q&As and Singing Mascot Poems into 9:16 vertical shorts.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    try:
        ffmpeg_path = get_ffmpeg_binary()
        ffmpeg_ok = True
        error_msg = None
    except Exception as e:
        ffmpeg_path = None
        ffmpeg_ok = False
        error_msg = str(e)

    return {
        "status": "online" if ffmpeg_ok else "degraded",
        "ffmpeg_installed": ffmpeg_ok,
        "ffmpeg_path": ffmpeg_path,
        "app_version": settings.version,
        "error": error_msg,
    }


@app.get("/api/voices")
def list_available_voices():
    return tts_manager.list_all_voices()


@app.get("/api/mascots")
def list_mascots():
    return [
        {
            "id": "bear",
            "name": "Rex the Ranger Bear",
            "emoji": "🐻",
            "tagline": "Bold Quiz Champion",
            "voice": "en-US-AnaNeural",
            "theme": "candy_clouds"
        },
        {
            "id": "penguin",
            "name": "Nova the Star Penguin",
            "emoji": "🐧",
            "tagline": "Cosmic Speed Racer",
            "voice": "en-US-JennyNeural",
            "theme": "ocean_bubbles"
        },
        {
            "id": "lion",
            "name": "Blaze the Brave Lion",
            "emoji": "🦁",
            "tagline": "Fearless Game Host",
            "voice": "en-US-GuyNeural",
            "theme": "safari_jungle"
        },
        {
            "id": "bunny",
            "name": "Comet the Quick Bunny",
            "emoji": "🐰",
            "tagline": "Lightning-Fast Explorer",
            "voice": "en-GB-SoniaNeural",
            "theme": "candy_clouds"
        },
    ]


@app.get("/api/templates")
def list_templates():
    return [
        {
            "id": "candy_clouds",
            "name": "Rainbow Candy",
            "emoji": "🍭",
            "bg_video": "candy_clouds.mp4",
            "accent_color": "#F59E0B",
            "description": "Pastel candy clouds with floating balloons and gold borders."
        },
        {
            "id": "space_galaxy",
            "name": "Cosmic Space",
            "emoji": "🚀",
            "bg_video": "space_galaxy.mp4",
            "accent_color": "#818CF8",
            "description": "Deep galaxy space, glowing planetary rings and space rocket."
        },
        {
            "id": "safari_jungle",
            "name": "Safari Jungle",
            "emoji": "🌿",
            "bg_video": "safari_jungle.mp4",
            "accent_color": "#10B981",
            "description": "Lush tropical green foliage and waving palm leaves."
        },
        {
            "id": "ocean_bubbles",
            "name": "Ocean Odyssey",
            "emoji": "🌊",
            "bg_video": "ocean_bubbles.mp4",
            "accent_color": "#38BDF8",
            "description": "Deep ocean blue water with rising bubbles and swimming clownfish."
        },
        {
            "id": "arcade_retro",
            "name": "Arcade Game Show",
            "emoji": "🎮",
            "bg_video": "arcade_retro.mp4",
            "accent_color": "#FACC15",
            "description": "Retro neon marquee with flashing bulbs and gold star coins."
        },
    ]


# -------------------------------------------------------------
# 1. TRIVIA & QUIZ STUDIO ENDPOINTS
# -------------------------------------------------------------

@app.get("/api/question-bank")
def get_question_bank(category: Optional[str] = Query(None)):
    bank_path = BASE_DIR / "app" / "data" / "question_bank.json"
    if not bank_path.is_file():
        raise HTTPException(status_code=404, detail="Question bank file not found.")
    
    with open(bank_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    if category and category != "all":
        questions = [q for q in questions if q.get("category", "").lower() == category.lower()]

    return {
        "total": len(questions),
        "category": category or "all",
        "questions": questions
    }


@app.get("/api/question-bank/categories")
def get_question_bank_categories():
    bank_path = BASE_DIR / "app" / "data" / "question_bank.json"
    if not bank_path.is_file():
        return []
    
    with open(bank_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    category_counts = {}
    for q in questions:
        cat = q.get("category", "General")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return [
        {"name": cat, "count": count}
        for cat, count in sorted(category_counts.items())
    ]


@app.post("/api/validate")
async def validate_trivia_file(file: UploadFile = File(...)):
    content_bytes = await file.read()
    try:
        raw_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Uploaded file is not valid UTF-8 text.")

    valid_items, errors = validate_trivia_json(raw_text)
    return {
        "valid_count": len(valid_items),
        "error_count": len(errors),
        "items": [it.model_dump() for it in valid_items],
        "errors": errors,
        "is_valid": len(valid_items) > 0 and len(errors) == 0,
    }


@app.post("/api/upload/video")
async def upload_background_video(file: UploadFile = File(...)):
    video_id = f"bg_{uuid.uuid4().hex[:8]}.mp4"
    dest_path = UPLOADS_DIR / video_id

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    is_valid, message, info = validate_background_video(dest_path)
    if not is_valid:
        if dest_path.exists():
            dest_path.unlink()
        raise HTTPException(status_code=400, detail=f"Invalid video file: {message}")

    return {
        "video_id": video_id,
        "filename": file.filename,
        "file_path": str(dest_path),
        "duration": info.get("duration", 0.0),
        "width": info.get("width", 0),
        "height": info.get("height", 0),
        "fps": info.get("fps", 30),
    }


@app.post("/api/preview")
async def generate_single_preview(
    question: str = Form(...),
    answer: str = Form(...),
    video_id: str = Form(...),
    config_json: str = Form(...),
    options_json: Optional[str] = Form(None),
):
    bg_video_path = UPLOADS_DIR / video_id
    if not bg_video_path.is_file():
        fallback_bg = BASE_DIR / "app" / "assets" / "backgrounds" / video_id
        if fallback_bg.is_file():
            bg_video_path = fallback_bg
        else:
            raise HTTPException(status_code=404, detail="Background video not found.")

    try:
        config_data = json.loads(config_json)
        config = VideoRenderConfig(**config_data)
        options = json.loads(options_json) if options_json else None
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid render configuration: {e}")

    preview_id = f"preview_{uuid.uuid4().hex[:8]}"
    work_dir = TEMP_DIR / preview_id
    output_mp4 = OUTPUTS_DIR / f"{preview_id}.mp4"

    try:
        master_audio, timing = await audio_service.prepare_quiz_audio(
            question_text=question,
            answer_text=answer,
            work_dir=work_dir,
            config=config,
        )

        await video_service.render_short_video(
            bg_video_path=bg_video_path,
            master_audio_path=master_audio,
            timing_info=timing,
            question_text=question,
            answer_text=answer,
            output_mp4_path=output_mp4,
            work_dir=work_dir,
            config=config,
            options=options,
            quality_tier="draft",
        )

        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)

        return {
            "preview_id": preview_id,
            "video_url": f"/api/download/preview/{preview_id}.mp4",
            "timing": timing,
        }
    except Exception as e:
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


@app.post("/api/jobs/create")
async def create_batch_job(
    items_json: str = Form(...),
    video_id: str = Form(...),
    config_json: str = Form(...),
):
    bg_video_path = UPLOADS_DIR / video_id
    if not bg_video_path.is_file():
        fallback_bg = BASE_DIR / "app" / "assets" / "backgrounds" / video_id
        if fallback_bg.is_file():
            bg_video_path = fallback_bg
        else:
            raise HTTPException(status_code=404, detail="Background video file not found.")

    try:
        raw_items = json.loads(items_json)
        valid_items, errors = validate_trivia_json(json.dumps(raw_items))
        if not valid_items:
            raise HTTPException(status_code=400, detail="No valid trivia items found in payload.")

        config_data = json.loads(config_json)
        config = VideoRenderConfig(**config_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid batch payload: {e}")

    job_state = job_manager.create_job(
        items=valid_items,
        bg_video_path=bg_video_path,
        config=config,
    )

    await job_manager.start_job(job_state.job_id)

    return {
        "job_id": job_state.job_id,
        "total_items": job_state.total_items,
        "status": job_state.status,
    }


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    state = job_manager.get_job(job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Job not found.")
    return state


@app.get("/api/jobs/{job_id}/stream")
async def stream_job_events(job_id: str):
    state = job_manager.get_job(job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Job not found.")

    q = job_manager.add_listener(job_id)

    async def event_generator():
        try:
            yield f"data: {state.model_dump_json()}\n\n"
            while True:
                data = await q.get()
                yield f"data: {data}\n\n"
                parsed = json.loads(data)
                if parsed.get("status") in ["completed", "failed", "partial_failure"]:
                    break
        except asyncio.CancelledError:
            pass
        finally:
            job_manager.remove_listener(job_id, q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/jobs/{job_id}/retry")
async def retry_failed_job_items(job_id: str):
    state = job_manager.get_job(job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Job not found.")

    asyncio.create_task(job_manager.retry_failed_items(job_id))
    return {"status": "retrying", "job_id": job_id}


# -------------------------------------------------------------
# 2. SINGING & DANCING POEM STUDIO ENDPOINTS
# -------------------------------------------------------------

@app.get("/api/poems")
def get_poem_bank(category: Optional[str] = Query(None)):
    poem_path = BASE_DIR / "app" / "data" / "poem_bank.json"
    if not poem_path.is_file():
        raise HTTPException(status_code=404, detail="Poem bank file not found.")
    
    with open(poem_path, "r", encoding="utf-8") as f:
        poems = json.load(f)

    if category and category != "all":
        poems = [p for p in poems if p.get("category", "").lower() == category.lower()]

    return {
        "total": len(poems),
        "category": category or "all",
        "poems": poems
    }


@app.get("/api/poems/categories")
def get_poem_categories():
    poem_path = BASE_DIR / "app" / "data" / "poem_bank.json"
    if not poem_path.is_file():
        return []
    
    with open(poem_path, "r", encoding="utf-8") as f:
        poems = json.load(f)

    category_counts = {}
    for p in poems:
        cat = p.get("category", "Nursery Rhymes")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return [
        {"name": cat, "count": count}
        for cat, count in sorted(category_counts.items())
    ]


@app.get("/api/melodies")
def list_melodies():
    return [
        {"id": "twinkle_star", "name": "✨ Twinkle Star Lullaby (Glockenspiel & Pads)", "bpm": 120},
        {"id": "playful_ukulele", "name": "🎶 Playful Ukulele & Marimba", "bpm": 128},
        {"id": "storybook_bells", "name": "📖 Storybook Bells & Flute", "bpm": 110},
        {"id": "bouncy_march", "name": "🥁 Bouncy Snare March & Brass", "bpm": 135},
        {"id": "none", "name": "🔇 A Cappella (No Music)", "bpm": 120},
    ]


@app.post("/api/poems/preview")
async def generate_poem_preview(
    poem_json: str = Form(...),
    config_json: str = Form(...),
):
    try:
        poem_data = json.loads(poem_json)
        poem = PoemItem(**poem_data)
        config_data = json.loads(config_json)
        config = PoemRenderConfig(**config_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid poem preview parameters: {e}")

    # Determine background video
    bg_video_name = f"{config.template_id}.mp4"
    bg_video_path = BASE_DIR / "app" / "assets" / "backgrounds" / bg_video_name
    if not bg_video_path.is_file():
        bg_video_path = BASE_DIR / "app" / "assets" / "backgrounds" / "candy_clouds.mp4"

    preview_id = f"poem_prev_{uuid.uuid4().hex[:8]}"
    work_dir = TEMP_DIR / preview_id
    output_mp4 = OUTPUTS_DIR / f"{preview_id}.mp4"

    try:
        await poem_service.render_poem_short(
            poem=poem,
            bg_video_path=bg_video_path,
            output_mp4_path=output_mp4,
            work_dir=work_dir,
            config=config,
            quality_tier="draft",
        )

        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)

        return {
            "preview_id": preview_id,
            "video_url": f"/api/download/preview/{preview_id}.mp4",
        }
    except Exception as e:
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Poem preview generation failed: {str(e)}")


@app.post("/api/poems/jobs/create")
async def create_poem_batch_job(
    poems_json: str = Form(...),
    config_json: str = Form(...),
):
    try:
        raw_poems = json.loads(poems_json)
        poems = [PoemItem(**p) for p in raw_poems]
        config_data = json.loads(config_json)
        config = PoemRenderConfig(**config_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid poem batch parameters: {e}")

    bg_video_name = f"{config.template_id}.mp4"
    bg_video_path = BASE_DIR / "app" / "assets" / "backgrounds" / bg_video_name
    if not bg_video_path.is_file():
        bg_video_path = BASE_DIR / "app" / "assets" / "backgrounds" / "candy_clouds.mp4"

    job_state = poem_job_manager.create_job(
        poems=poems,
        bg_video_path=bg_video_path,
        config=config,
    )

    await poem_job_manager.start_job(job_state.job_id)

    return {
        "job_id": job_state.job_id,
        "total_items": job_state.total_items,
        "status": job_state.status,
    }


@app.get("/api/poems/jobs/{job_id}")
def get_poem_job_status(job_id: str):
    state = poem_job_manager.get_job(job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Poem job not found.")
    return state


@app.get("/api/poems/jobs/{job_id}/stream")
async def stream_poem_job_events(job_id: str):
    state = poem_job_manager.get_job(job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Poem job not found.")

    q = poem_job_manager.add_listener(job_id)

    async def event_generator():
        try:
            yield f"data: {state.model_dump_json()}\n\n"
            while True:
                data = await q.get()
                yield f"data: {data}\n\n"
                parsed = json.loads(data)
                if parsed.get("status") in ["completed", "failed", "partial_failure"]:
                    break
        except asyncio.CancelledError:
            pass
        finally:
            poem_job_manager.remove_listener(job_id, q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# -------------------------------------------------------------
# 3. DOWNLOAD ENDPOINTS
# -------------------------------------------------------------

@app.get("/api/download/video/{job_id}/{filename}")
def download_individual_video(job_id: str, filename: str):
    file_path = OUTPUTS_DIR / job_id / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Video file not found.")
    return FileResponse(file_path, media_type="video/mp4", filename=filename)


@app.get("/api/download/preview/{filename}")
def download_preview_video(filename: str):
    file_path = OUTPUTS_DIR / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Preview video file not found.")
    return FileResponse(file_path, media_type="video/mp4", filename=filename)


@app.get("/api/download/zip/{filename}")
def download_batch_zip(filename: str):
    file_path = OUTPUTS_DIR / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="ZIP file not found.")
    return FileResponse(file_path, media_type="application/zip", filename=filename)


FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")

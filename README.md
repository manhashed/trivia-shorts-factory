# 🐻 Trivia & Quiz Shorts Factory (Kids 3–5 Edition)

An automated full-stack production system that transforms trivia JSON datasets (`[{"q": "...", "a": "..."}]`) and looping MP4 background videos into individual, high-retention 9:16 vertical short-form quiz videos for **YouTube Shorts, TikTok, and Instagram Reels**.

Specialized for **Children Ages 3–5 (Toddler / Preschool)** with interactive host **Barnaby Bear**, bright visual cards, animated 3-2-1 countdowns, and joyful sound effects.

---

## 🌟 Key Features

1. **Deterministic FFmpeg Video Engine**:
   - Auto-scales and crops any source video (landscape, square, or portrait) to **1080×1920 (9:16)** vertical format.
   - Seamless background video looping (`-stream_loop -1`).
   - Adheres to standard YouTube Shorts / TikTok UI safe zones.
   - Text wrapping and bounding box safeguards to eliminate text clipping.

2. **Microsoft Edge Neural TTS (Free Default)**:
   - Zero API key required, zero billing, high-fidelity neural voice synthesis.
   - Pre-configured child & storybook narrator voices:
     - `en-US-AnaNeural` (Child / Cheerful — recommended for 3–5)
     - `en-US-JennyNeural` (Storybook narrator)
     - `en-US-GuyNeural` (Energetic host)
     - `en-GB-SoniaNeural` (Preschool teacher)
   - Extensible provider adapter for **OpenAI TTS** (`nova`, `fable`, `alloy`) and ElevenLabs.

3. **High-Attention Kid Engagement Mechanics**:
   - **Host Mascot**: **Barnaby Bear** in *Asking* pose (during Question + Countdown) and *Excited / Cheering* pose (during Answer reveal).
   - **Audio Cues**: 3-second woodblock clock tick-tock countdown and magical fanfare chime on answer reveal.
   - **Card Design**: Rounded high-contrast translucent cards with bold typography.

4. **Instant 5-Second Test Preview**:
   - Single-item test button (`/api/preview`) to inspect voice, timing, and visual overlays before initiating large batches.

5. **Asynchronous Batch Job Manager**:
   - Concurrency control (default 3 workers) to prevent CPU thrashing.
   - Real-time Server-Sent Events (SSE) progress broadcasting.
   - **Error Isolation**: Failed questions report actionable error logs without failing the batch.
   - **Selective Retry**: One-click re-render for failed items.
   - Final ZIP bundle generation (`manifest.json` + all standalone MP4s).

---

## 📁 Project Structure

```
trivia/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application & API endpoints
│   │   ├── config.py                   # Configuration & media defaults
│   │   ├── models/
│   │   │   └── schemas.py              # Pydantic validation models
│   │   ├── services/
│   │   │   ├── validator.py            # Input validation & text sanitization
│   │   │   ├── audio_service.py        # Audio mixing & sample-accurate timing
│   │   │   ├── video_service.py        # FFmpeg filter graph video engine
│   │   │   ├── job_manager.py          # Async queue & SSE progress stream
│   │   │   ├── zip_service.py          # Batch packaging
│   │   │   └── tts/
│   │   │       ├── base.py             # TTS abstract interface
│   │   │       ├── edge_tts_service.py # Edge-TTS implementation
│   │   │       ├── openai_tts_service.py
│   │   │       └── tts_manager.py
│   │   ├── assets/
│   │   │   ├── audio/                  # Tick-tock & celebration chime SFX
│   │   │   ├── fonts/                  # Fredoka / Arial Rounded Bold TTF
│   │   │   └── images/                 # Mascot PNG assets (Asking & Cheering)
│   │   └── utils/
│   │       ├── ffmpeg_check.py         # FFmpeg detection & media probing
│   │       ├── generate_sfx.py         # Audio synthesizer
│   │       └── generate_mascot.py      # Mascot renderer
│   ├── tests/
│   │   ├── test_validator.py           # Unit tests
│   │   ├── test_api_integration.py     # Endpoint tests
│   │   ├── test_prototype.py           # Single-item render test
│   │   └── test_batch_flow.py          # Full batch flow test
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx                     # Main dashboard
│   │   ├── components/
│   │   │   ├── Header.tsx              # Brand header
│   │   │   ├── UploadSection.tsx       # Drag-and-drop uploader & sample loader
│   │   │   ├── SettingsDrawer.tsx      # Voice & style controls
│   │   │   ├── PreviewPlayer.tsx       # 9:16 interactive test preview player
│   │   │   ├── BatchProgress.tsx       # Live per-question pipeline status
│   │   │   └── MascotGuide.tsx         # Preschool retention tips
│   │   └── services/
│   │       └── api.ts                  # API client
│   ├── package.json
│   └── vite.config.ts
├── examples/
│   ├── toddler_animals_quiz.json       # Sample dataset 1
│   └── preschool_colors_shapes.json    # Sample dataset 2
└── storage/
    ├── uploads/
    ├── temp/
    └── outputs/
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ (or pnpm / bun)

### 2. Backend Setup
```bash
# Set up Python virtual environment
python3 -m venv venv
./venv/bin/pip install -r backend/requirements.txt

# (Optional) Verify FFmpeg & dependencies
PYTHONPATH=. ./venv/bin/pytest backend/tests/test_validator.py backend/tests/test_api_integration.py
```

### 3. Frontend Build
```bash
cd frontend
pnpm install
pnpm run build
cd ..
```

### 4. Start the Application
```bash
# Start unified FastAPI server (serves API + React UI on port 8000)
PYTHONPATH=. ./venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open **http://127.0.0.1:8000** in your browser.

---

## 🧪 Running Automated Tests

```bash
# 1. Run all unit and integration tests
PYTHONPATH=. ./venv/bin/pytest backend/tests/

# 2. Run end-to-end single video rendering test
PYTHONPATH=. ./venv/bin/python backend/tests/test_prototype.py

# 3. Run full batch processing & ZIP generation test
PYTHONPATH=. ./venv/bin/python backend/tests/test_batch_flow.py
```

---

## 🔒 Security & Robustness

- **Shell Injection Immunity**: FFmpeg text filters use dedicated UTF-8 text files (`textfile=...`) rather than raw command string interpolation.
- **Input Sanitization**: Unicode normalization (NFC), control character filtering, and length validation.
- **Error Isolation**: Individual question failures do not abort the batch. Actionable logs are surfaced with one-click retry.
- **Auto-Cleanup**: Scratch audio files and intermediate text cards are cleaned immediately upon video rendering.

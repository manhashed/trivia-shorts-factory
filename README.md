# 🐻 Trivia & Quiz Shorts Factory (Kids 5–8 Edition)

An automated full-stack studio that turns trivia JSON (`[{"q": "...", "a": "..."}]`) and looping MP4 backgrounds into 9:16 shorts for **YouTube Shorts, TikTok, and Instagram Reels**.

Built for **children ages 5–8 (kindergarten through early elementary)** with host **Barnaby Bear**, high-contrast cards, a 3-2-1 countdown, and a shout-the-answer beat.

Voice starts on **free Microsoft Edge Neural TTS**. Swap in **OpenAI** or **ElevenLabs** (or an OpenAI-compatible speech API) with a `.env` file — no code changes.

Repo: [https://github.com/manhashed/trivia-shorts-factory](https://github.com/manhashed/trivia-shorts-factory)

---

## Fork and run

### 1. Fork the repo

On GitHub, open [manhashed/trivia-shorts-factory](https://github.com/manhashed/trivia-shorts-factory) and click **Fork**. Use your fork’s URL in the clone step below.

### 2. Clone

```bash
git clone https://github.com/YOUR_USER/trivia-shorts-factory.git
cd trivia-shorts-factory
```

Or clone this repo directly:

```bash
git clone https://github.com/manhashed/trivia-shorts-factory.git
cd trivia-shorts-factory
```

### 3. Prerequisites

- Python 3.10+
- Node.js 18+ (pnpm, npm, or bun)
- Git

FFmpeg is pulled in by the Python packages. A system FFmpeg install also works.

### 4. Python backend

```bash
python3 -m venv venv
./venv/bin/pip install -r backend/requirements.txt
cp .env.example .env
```

Leave `.env` as-is to stay on free Edge TTS. Add paid keys later if you want OpenAI or ElevenLabs.

### 5. Frontend

The FastAPI server serves the built UI from `frontend/dist`, so build once:

```bash
cd frontend
pnpm install
pnpm run build
cd ..
```

If you do not have pnpm:

```bash
cd frontend
npm install
npm run build
cd ..
```

### 6. Run the server

```bash
./run_server.sh
```

Or:

```bash
PYTHONPATH=. ./venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open **http://127.0.0.1:8000** in your browser.

You should see the Kids 5–8 studio (Trivia + Poem tabs) and an FFmpeg / Edge TTS status chip in the header.

### 7. Make a first short

1. Pick a mascot and background theme, or load a sample from `examples/`.
2. Click the 5-second preview to check voice and timing.
3. Start a batch. Finished MP4s land in `storage/outputs/` and download as a ZIP.

---

## 🌟 Key Features

1. **Deterministic FFmpeg Video Engine**:
   - Auto-scales and crops any source video to **1080×1920 (9:16)**.
   - Seamless background looping (`-stream_loop -1`).
   - YouTube Shorts / TikTok UI safe zones, wrapped text, no clipped cards.

2. **Pluggable voice engines**:
   - **Edge TTS (default, free)**: no API key. Kid-friendly voices such as `en-US-AnaNeural`.
   - **OpenAI TTS**: set `OPENAI_API_KEY` (and optionally `OPENAI_BASE_URL` for a compatible `/audio/speech` API).
   - **ElevenLabs**: set `ELEVENLABS_API_KEY`.
   - Keys load from `.env`. The UI never needs the secret pasted in. Missing paid keys fall back to Edge so renders still work.

3. **High-attention kids 5–8 mechanics**:
   - Host mascot in asking vs cheering poses.
   - Woodblock countdown + fanfare on the reveal.
   - Rounded high-contrast cards and bold type that reads on a phone.

4. **5-second test preview** at `/api/preview` before a full batch.

5. **Async batch jobs** with SSE progress, isolated failures, retry, and a ZIP of MP4s.

---

## 🔌 Plug in a different AI voice

Copy the example env file, fill the keys you want, restart the backend:

```bash
cp .env.example .env
```

| Goal | What to set |
| --- | --- |
| Keep the free default | `TTS_PROVIDER=edge` and leave API keys empty |
| Use OpenAI voices (`nova`, `fable`, `alloy`, …) | `TTS_PROVIDER=openai`, `TTS_VOICE=nova`, `OPENAI_API_KEY=sk-...` |
| Use ElevenLabs | `TTS_PROVIDER=elevenlabs`, `TTS_VOICE=21m00Tcm4TlvDq8ikWAM`, `ELEVENLABS_API_KEY=...` |
| Point OpenAI at a compatible speech API | `OPENAI_BASE_URL=https://your-proxy.example/v1` (must expose `POST /audio/speech`) |

`GET /api/health` reports which engines are configured **without returning the keys**. In the studio, paid voices unlock automatically when the server has a key.

You can still paste a one-off key in **Step 2 → Plug in OpenAI or ElevenLabs**. That overrides `.env` for the current session only.

### Add another TTS vendor

1. Copy `backend/app/services/tts/openai_tts_service.py` (or `edge_tts_service.py`).
2. Implement `BaseTTSProvider.synthesize` + `list_voices`.
3. Register the class in `TTSManager.providers`.
4. Add the API key to `.env.example`, `AppSettings`, and `tts_status()`.

---

## 📁 Project Structure

```
trivia/
├── .env.example                        # Copy to .env — never commit secrets
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application & API endpoints
│   │   ├── config.py                   # Loads .env, media defaults, TTS status
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
│   │   │       ├── edge_tts_service.py # Edge-TTS (free)
│   │   │       ├── openai_tts_service.py
│   │   │       ├── elevenlabs_tts_service.py
│   │   │       └── tts_manager.py
│   │   ├── assets/
│   │   │   ├── audio/                  # Tick-tock & celebration chime SFX
│   │   │   ├── fonts/                  # Fredoka / Arial Rounded Bold TTF
│   │   │   └── images/                 # Mascot PNG assets
│   │   └── utils/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   └── services/
│   └── package.json
├── examples/
│   ├── toddler_animals_quiz.json       # Sample ages 5–8 animal facts
│   └── preschool_colors_shapes.json    # Sample ages 5–8 science / shapes
└── storage/
    ├── uploads/
    ├── temp/
    └── outputs/
```

---

## 🧪 Running Automated Tests

```bash
PYTHONPATH=. ./venv/bin/pytest backend/tests/
PYTHONPATH=. ./venv/bin/python backend/tests/test_prototype.py
PYTHONPATH=. ./venv/bin/python backend/tests/test_batch_flow.py
```

---

## 🔒 Security & Robustness

- **Secrets**: `.env` is gitignored. `.env.example` has empty placeholders only. Health status never returns API keys.
- **Shell injection**: FFmpeg text filters use UTF-8 `textfile=` rather than interpolating user text into the command.
- **Input sanitization**: Unicode NFC, control-character filtering, length checks.
- **Error isolation**: One failed question does not abort the batch.
- **Auto-cleanup**: Scratch audio and text cards are removed after each render.

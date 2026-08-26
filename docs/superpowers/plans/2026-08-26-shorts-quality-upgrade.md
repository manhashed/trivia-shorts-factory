# Shorts Quality Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the answer/options text-drift bug structurally, replace the toddler-era mascot art with an upgraded procedural art style, bring trivia and poem shorts to a shared higher animation/audio bar, finish the TTS story (ElevenLabs), and add draft/final render quality tiers.

**Architecture:** No rearchitecture — the existing FFmpeg filter-graph engine (`video_service.py`/`poem_service.py`), PIL-based procedural asset generators, and Edge-TTS-first provider pattern all stay. Changes are targeted: a new `correct_index` field makes the answer authoritative; a shared `vfx_helpers.py` module centralizes reusable filter-graph fragments (Ken Burns, flash, overshoot easing) so trivia and poem renderers stop drifting apart; mascot/SFX generators get a quality pass while keeping their existing file-naming contracts so no renderer code needs to know assets changed.

**Tech Stack:** Python 3.14 (venv at repo root), FastAPI, FFmpeg (via `static_ffmpeg`), Pillow (PIL), edge-tts, httpx, pytest; React + TypeScript + Vite frontend, Tailwind.

**Spec:** [docs/superpowers/specs/2026-08-26-shorts-quality-upgrade-design.md](../specs/2026-08-26-shorts-quality-upgrade-design.md)

## Global Constraints

- Output stays 1080x1920, 30fps — no resolution change (per spec's Non-goals).
- No AI-generated image/video assets in this pass — procedural only (per spec Non-goals).
- Keep 44.1kHz stereo PCM WAV convention for all audio synthesis.
- Preserve existing mascot IDs (`bear`, `penguin`, `lion`, `bunny`) and file-naming conventions (`{id}_asking.png`, `{id}_cheering.png`, `{id}_d1..d4.png`) so `video_service.py`'s asset-loading code and `job_manager.py`'s `MASCOTS_ROTATION` need zero changes — only the art and display names change.
- Every task must leave `backend/tests/` fully green before its commit step.
- Run all backend commands from the repo root `/Users/manhashed/work/ai-shorts-generation/trivia` using `venv/bin/pytest` / `venv/bin/python` (the project venv), not a bare `python`/`pytest`.
- Never derive the displayed or spoken trivia answer from `TriviaItem.a` directly downstream of Task 1 — always go through `resolved_answer` / `options[correct_index]`.

---

### Task 1: `TriviaItem.correct_index` field + `resolved_answer` derivation

**Files:**
- Modify: `backend/app/models/schemas.py:1-18`
- Test: `backend/tests/test_schemas.py`

**Interfaces:**
- Consumes: nothing (pure schema change).
- Produces: `TriviaItem.correct_index: Optional[int]` (defaults to `0` whenever `options` is set, stays `None` when `options` is `None`, validated in-range); `TriviaItem.resolved_answer` (a `@property` returning `str`) — this is the single property every later task (2, 3, 5) must read instead of `item.a`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_schemas.py`:

```python
import pytest
from pydantic import ValidationError

from backend.app.models.schemas import TriviaItem


def test_correct_index_defaults_to_zero_when_options_present():
    item = TriviaItem(q="What animal says Moo?", a="A Big Spotted Cow!", options=["A Cow", "A Dog", "A Frog"])
    assert item.correct_index == 0
    assert item.resolved_answer == "A Cow"


def test_correct_index_explicit_valid_value():
    item = TriviaItem(q="What is 2+2?", a="Four!", options=["3", "4", "5"], correct_index=1)
    assert item.correct_index == 1
    assert item.resolved_answer == "4"


def test_correct_index_out_of_range_raises():
    with pytest.raises(ValidationError):
        TriviaItem(q="What is 2+2?", a="Four!", options=["3", "4", "5"], correct_index=5)


def test_no_options_falls_back_to_a():
    item = TriviaItem(q="What is 2+2?", a="Four!")
    assert item.options is None
    assert item.correct_index is None
    assert item.resolved_answer == "Four!"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_schemas.py -v`
Expected: FAIL with `AttributeError: 'TriviaItem' object has no attribute 'correct_index'` (or `resolved_answer`) on every test.

- [ ] **Step 3: Write minimal implementation**

Replace `backend/app/models/schemas.py:1-18` (the imports line and the full `TriviaItem` class) with:

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class TriviaItem(BaseModel):
    id: Optional[str] = None
    q: str = Field(..., min_length=1, description="Question text")
    a: str = Field(..., min_length=1, description="Answer text")
    category: Optional[str] = None
    options: Optional[List[str]] = Field(default=None, description="Optional multiple-choice options (A, B, C)")
    correct_index: Optional[int] = Field(default=None, description="Index into options that holds the correct answer")

    @field_validator("q", "a")
    @classmethod
    def strip_and_validate_non_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Question and Answer cannot be empty or whitespace only.")
        return cleaned

    @model_validator(mode="after")
    def validate_correct_index(self) -> "TriviaItem":
        if self.options:
            if self.correct_index is None:
                self.correct_index = 0
            elif not (0 <= self.correct_index < len(self.options)):
                raise ValueError(
                    f"correct_index {self.correct_index} is out of range for options of length {len(self.options)}"
                )
        else:
            self.correct_index = None
        return self

    @property
    def resolved_answer(self) -> str:
        """
        The single source of truth for the displayed/spoken answer. Never read
        `self.a` downstream for rendering or narration -- always use this.
        """
        if self.options and self.correct_index is not None:
            return self.options[self.correct_index]
        return self.a
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_schemas.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/schemas.py backend/tests/test_schemas.py
git commit -m "feat: add TriviaItem.correct_index and resolved_answer to fix answer text drift"
```

---

### Task 2: Wire `resolved_answer` through `job_manager.py`

**Files:**
- Modify: `backend/app/services/job_manager.py:81-95` (in `create_job`)
- Modify: `backend/app/services/job_manager.py:169-224` (`process_single` inside `_process_batch_job`)
- Modify: `backend/app/services/job_manager.py:310-361` (`retry_single` inside `retry_failed_items`)
- Test: `backend/tests/test_job_manager_correctness.py`

**Interfaces:**
- Consumes: `TriviaItem.resolved_answer` (Task 1).
- Produces: `BatchItemStatus.answer` now reflects the resolved option text; `audio_service.prepare_quiz_audio(answer_text=...)` and `video_service.render_short_video(answer_text=...)` are now called with the resolved text at both call sites. This task does **not** add a `correct_index=` kwarg to `render_short_video(...)` — that parameter does not exist until Task 5. Task 5 will come back and add `correct_index=item.correct_index` to the exact same two `render_short_video(...)` calls this task touches.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_job_manager_correctness.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path

from backend.app.models.schemas import TriviaItem, VideoRenderConfig
from backend.app.services.job_manager import job_manager


def _make_mismatched_item() -> TriviaItem:
    return TriviaItem(
        id="q1",
        q="What animal says Moo?",
        a="A Big Spotted Cow!",
        options=["A Cow", "A Dog", "A Frog"],
    )


def test_create_job_uses_resolved_answer_not_free_text_a():
    item = _make_mismatched_item()
    config = VideoRenderConfig()

    state = job_manager.create_job(
        items=[item],
        bg_video_path=Path("/fake/bg.mp4"),
        config=config,
    )

    assert state.items[0].answer == "A Cow"
    assert state.items[0].answer != item.a


@pytest.mark.anyio
async def test_process_single_passes_resolved_answer_to_audio_and_video_services():
    item = _make_mismatched_item()
    config = VideoRenderConfig()

    state = job_manager.create_job(
        items=[item],
        bg_video_path=Path("/fake/bg.mp4"),
        config=config,
    )
    job_id = state.job_id

    fake_timing = {
        "t_countdown_start": 1.0,
        "t_countdown_end": 4.0,
        "t_answer_start": 4.0,
        "total_duration": 8.0,
        "countdown_duration": 3.0,
    }

    with patch(
        "backend.app.services.job_manager.audio_service.prepare_quiz_audio",
        new=AsyncMock(return_value=(Path("/fake/master_audio.wav"), fake_timing)),
    ) as mock_audio, patch(
        "backend.app.services.job_manager.video_service.render_short_video",
        new=AsyncMock(return_value=Path("/fake/output.mp4")),
    ) as mock_video, patch(
        "backend.app.services.job_manager.probe_media_file",
        return_value={"has_video": True, "duration": 8.0},
    ):
        await job_manager._process_batch_job(job_id)

    mock_audio.assert_awaited_once()
    mock_video.assert_awaited_once()
    assert mock_audio.call_args.kwargs["answer_text"] == "A Cow"
    assert mock_video.call_args.kwargs["answer_text"] == "A Cow"

    final_state = job_manager.get_job(job_id)
    assert final_state.status == "completed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_job_manager_correctness.py -v`
Expected: FAIL on `test_create_job_uses_resolved_answer_not_free_text_a` with `AssertionError: assert 'A Big Spotted Cow!' == 'A Cow'`, and on the second test with the mocks' `answer_text` kwarg equal to `"A Big Spotted Cow!"` instead of `"A Cow"`.

- [ ] **Step 3: Write minimal implementation**

In `backend/app/services/job_manager.py`, inside `create_job` at line 86, replace `answer=item.a,` with `answer=item.resolved_answer,`.

Inside `_process_batch_job`'s nested `process_single` (lines 169-224), replace:

```python
        async def process_single(idx: int, item: TriviaItem):
            item_status = state.items[idx]
            item_slug = slugify_text(item.a)
```

with:

```python
        async def process_single(idx: int, item: TriviaItem):
            item_status = state.items[idx]
            item_slug = slugify_text(item.resolved_answer)
```

and further down in the same function, replace both `answer_text=item.a` occurrences (in the `audio_service.prepare_quiz_audio(...)` call and the `video_service.render_short_video(...)` call) with `answer_text=item.resolved_answer` — do **not** add `correct_index=` yet:

```python
                    master_audio, timing = await audio_service.prepare_quiz_audio(
                        question_text=item.q,
                        answer_text=item.resolved_answer,
                        work_dir=item_work_dir,
                        config=item_config,
                    )
```

```python
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
```

Now apply the identical three replacements inside `retry_failed_items`'s nested `retry_single` (lines 310-361): `slugify_text(item.a)` → `slugify_text(item.resolved_answer)`, and both `answer_text=item.a` → `answer_text=item.resolved_answer` in the same two call shapes as above (still no `correct_index=`).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_job_manager_correctness.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/job_manager.py backend/tests/test_job_manager_correctness.py
git commit -m "fix: job_manager renders/narrates resolved_answer instead of mismatched free-text a"
```

---

### Task 3: Mirror `correct_index` into the frontend and use the resolved answer in `PreviewPlayer`

**Files:**
- Modify: `frontend/src/types/index.ts:1-7`
- Modify: `frontend/src/components/PreviewPlayer.tsx:24`, `:32-38`, `:148`
- Test: none (no test runner is configured in `frontend/` — only `dev`/`build`/`preview` scripts, no `*.test.*`/`*.spec.*` files). This task uses the TypeScript compiler itself (`npx tsc`, already wired into `npm run build` via `tsc && vite build`, with `noEmit: true` already set in `frontend/tsconfig.json`) as the verification gate instead.

**Interfaces:**
- Consumes: the `correct_index` field shape from Task 1's `TriviaItem`.
- Produces: `TriviaItem.correct_index?: number` in the frontend type; `resolvedAnswer` local variable in `PreviewPlayer` used for both the preview-generation call and the on-screen answer display.

- [ ] **Step 1: Write the failing test (a deliberately broken type reference)**

In `frontend/src/components/PreviewPlayer.tsx`, edit line 24 to add a reference to a field that does not exist yet on `TriviaItem`:

```tsx
  const currentItem = items[selectedIndex] || items[0];
  const resolvedAnswer = currentItem?.options && currentItem.options.length > 0
    ? currentItem.options[currentItem.correct_index ?? 0]
    : currentItem?.a;
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia/frontend && npx tsc`
Expected: FAIL with `error TS2339: Property 'correct_index' does not exist on type 'TriviaItem'.` pointing at `PreviewPlayer.tsx`.

- [ ] **Step 3: Write minimal implementation**

In `frontend/src/types/index.ts`, replace lines 1-7:

```ts
export interface TriviaItem {
  id?: string;
  q: string;
  a: string;
  category?: string;
  options?: string[];
}
```

with:

```ts
export interface TriviaItem {
  id?: string;
  q: string;
  a: string;
  category?: string;
  options?: string[];
  correct_index?: number;
}
```

In `frontend/src/components/PreviewPlayer.tsx`, the `resolvedAnswer` computation from Step 1 stays as-is. Now update the `generatePreview` call at lines 32-38 — replace:

```tsx
      const res = await generatePreview(
        currentItem.q,
        currentItem.a,
        videoData.video_id,
        config,
        currentItem.options
      );
```

with:

```tsx
      const res = await generatePreview(
        currentItem.q,
        resolvedAnswer,
        videoData.video_id,
        config,
        currentItem.options
      );
```

And update the on-screen answer display at line 148 — replace:

```tsx
              <p className="text-emerald-400 font-semibold">Answer: "{currentItem?.a}"</p>
```

with:

```tsx
              <p className="text-emerald-400 font-semibold">Answer: "{resolvedAnswer}"</p>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia/frontend && npx tsc`
Expected: PASS (no output, exit code 0)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/components/PreviewPlayer.tsx
git commit -m "fix: PreviewPlayer shows and previews the resolved option answer, not free-text a"
```

---

### Task 4: Vary the spoken answer-reveal carrier phrase without ever touching the answer text itself

**Files:**
- Create: `backend/app/services/phrase_variety.py`
- Modify: `backend/app/services/audio_service.py:1-9` (imports), `:85-90` (the hardcoded reveal-phrase block)
- Test: `backend/tests/test_phrase_variety.py`

**Interfaces:**
- Consumes: nothing from Tasks 1-3.
- Produces: `build_answer_reveal_phrase(exact_answer: str) -> str` in `backend/app/services/phrase_variety.py`, called from `AudioService.prepare_quiz_audio` to build `answer_spoken_text`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_phrase_variety.py`:

```python
from backend.app.services.phrase_variety import build_answer_reveal_phrase, REVEAL_PHRASE_TEMPLATES


def test_exact_answer_always_appears_verbatim():
    exact_answer = "A Big Spotted Cow"
    for _ in range(20):
        phrase = build_answer_reveal_phrase(exact_answer)
        assert exact_answer in phrase


def test_answer_text_is_never_rephrased_or_mutated():
    exact_answer = "A Cow"
    for _ in range(20):
        phrase = build_answer_reveal_phrase(exact_answer)
        assert any(
            phrase == template.format(answer=exact_answer)
            for template in REVEAL_PHRASE_TEMPLATES
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_phrase_variety.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.app.services.phrase_variety'`

- [ ] **Step 3: Write minimal implementation**

Create `backend/app/services/phrase_variety.py`:

```python
import random

# Reused verbatim from the kid-friendly reveal phrasing already proven in
# backend/app/services/tts/edge_tts_service.py's _enhance_text_for_speech
# (that method is currently dead code -- tts_manager.synthesize() is never
# called with text_style="answer" from audio_service). Centralizing the list
# here lets prepare_quiz_audio vary the carrier phrase on every render.
REVEAL_PHRASE_TEMPLATES = [
    "The answer is... {answer}!",
    "It's... {answer}! Great job!",
    "Yes! It's {answer}!",
    "That's right, it's {answer}!",
    "Wow, it's {answer}! Did you know that?",
    "You got it! It's {answer}!",
    "Bingo! It's {answer}!",
    "Correct! It is {answer}!",
]


def build_answer_reveal_phrase(exact_answer: str) -> str:
    """
    Selects a random kid-friendly carrier phrase and substitutes the exact
    answer text into it verbatim. The answer text itself is never altered,
    reworded, or re-derived here -- only the surrounding phrasing varies.
    """
    template = random.choice(REVEAL_PHRASE_TEMPLATES)
    return template.format(answer=exact_answer)
```

In `backend/app/services/audio_service.py`, add the import after line 9 (`from backend.app.models.schemas import VideoRenderConfig`):

```python
from backend.app.services.phrase_variety import build_answer_reveal_phrase
```

Then replace lines 85-90:

```python
        # 2. Synthesize Answer Audio
        # Use child-engaging phrasing if not already present
        if not answer_text.lower().startswith("the answer") and not answer_text.lower().startswith("it's") and not answer_text.lower().startswith("it is"):
            answer_spoken_text = f"The answer is... {answer_text}!"
        else:
            answer_spoken_text = answer_text
```

with:

```python
        # 2. Synthesize Answer Audio
        # Vary the reveal carrier phrase on every render while keeping the
        # exact resolved answer text (answer_text) verbatim and untouched.
        answer_spoken_text = build_answer_reveal_phrase(answer_text)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_phrase_variety.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/phrase_variety.py backend/app/services/audio_service.py backend/tests/test_phrase_variety.py
git commit -m "feat: vary spoken answer-reveal carrier phrase while keeping answer text verbatim"
```

---

### Task 5: Highlight the correct option instead of drawing an independent answer string

**Files:**
- Modify: `backend/app/services/video_service.py:89-98` (insert new helper method after `_get_dance_frames`)
- Modify: `backend/app/services/video_service.py:100-111` (add `correct_index` parameter to `render_short_video`)
- Modify: `backend/app/services/video_service.py:293-334` (the "(f) Multiple Choice Options" loop — insert the highlight call)
- Modify: `backend/app/services/video_service.py:376-398` (the "(g) Answer Card Frame & Text" block — repurposed into a smaller, secondary "fun fact" caption)
- Modify: `backend/app/services/job_manager.py:214-224` and `:351-361` (second modification of this file — both `video_service.render_short_video(...)` call sites that Task 2 already updated now additionally pass `correct_index=item.correct_index`)
- Test: `backend/tests/test_video_service_correctness.py`

**Interfaces:**
- Consumes: `TriviaItem.correct_index` (Task 1); the two `render_short_video(...)` call sites in `job_manager.py` that Task 2 left with `answer_text=item.resolved_answer` and no `correct_index=` kwarg.
- Produces: `render_short_video(..., correct_index: Optional[int] = None)`; `VideoService._build_option_highlight_filters(self, options_layer: str, options: List[str], correct_index: int, t_ans_start: float, font_path, input_layer_idx: int) -> tuple[list[str], str]`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_video_service_correctness.py`:

```python
from pathlib import Path

from backend.app.services.video_service import video_service


def test_highlight_filters_contain_only_the_correct_option_text():
    options = ["A Cow", "A Dog", "A Frog"]
    font_path = Path("/fake/Fredoka-Bold.ttf")

    filters, new_layer = video_service._build_option_highlight_filters(
        options_layer="with_opt_3",
        options=options,
        correct_index=0,
        t_ans_start=5.25,
        font_path=font_path,
        input_layer_idx=99,
    )

    joined = "\n".join(filters)
    assert "A Cow" in joined
    assert "A Dog" not in joined
    assert "A Frog" not in joined
    assert new_layer == "with_opt_check_99"


def test_highlight_filters_include_checkmark_green_box_and_correct_option_for_other_index():
    options = ["A Cow", "A Dog", "A Frog"]
    font_path = Path("/fake/Fredoka-Bold.ttf")

    filters, new_layer = video_service._build_option_highlight_filters(
        options_layer="with_opt_3",
        options=options,
        correct_index=1,
        t_ans_start=5.25,
        font_path=font_path,
        input_layer_idx=42,
    )

    joined = "\n".join(filters)
    assert "A Dog" in joined
    assert "A Cow" not in joined
    assert "A Frog" not in joined
    assert "✓" in joined
    assert "0x16A34A" in joined
    assert "gte(t,5.25)" in joined
    assert new_layer == "with_opt_check_42"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_video_service_correctness.py -v`
Expected: FAIL with `AttributeError: 'VideoService' object has no attribute '_build_option_highlight_filters'`

- [ ] **Step 3: Write minimal implementation**

Insert this new method right after `_get_dance_frames` (before `async def render_short_video`):

```python
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
```

Add the `correct_index` parameter to `render_short_video`'s signature (replace lines 100-111):

```python
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
```

In the "(f) Multiple Choice Options" block, insert the highlight call right after the `for i, opt_text in enumerate(options[:4]):` loop ends and before `badge_base_y` is computed. Replace:

```python
                options_layer = next_layer

            # Adjust countdown badge position lower to fit neatly below options
            badge_base_y = base_opt_y + (len(options[:4]) * opt_spacing) + 20
            num_base_y = badge_base_y + 60
```

with:

```python
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
```

(`options_layer` feeds into the countdown-badge overlay chain that follows, ending in `with_num_1` — so the highlight is automatically carried forward without touching the badge section.)

In the "(g) Answer Card Frame & Text" block, repurpose it into a smaller, secondary "fun fact" caption showing the original free-text `answer_text` — never the authoritative answer. Replace the header/text drawtext calls:

```python
        filter_chains.append(
            f"[with_ans_frame]drawtext=fontfile='{font_path}':text='{theme['ans_title']}':fontcolor=0xFDE047:fontsize=50:"
            f"x=(w-text_w)/2:y='{a_hdr_y}':borderw=5:bordercolor=black@0.9:shadowcolor=black@0.9:shadowx=4:shadowy=4:enable='gte(t,{t_ans_start})'[with_ans_header]"
        )
        filter_chains.append(
            f"[with_ans_header]drawtext=fontfile='{font_path}':textfile='{escaped_a_file}':"
            f"fontcolor=white:fontsize=64:x=(w-text_w)/2:y='{a_txt_y}':line_spacing=20:"
            f"borderw=6:bordercolor=black@0.95:shadowcolor=black@0.95:shadowx=4:shadowy=4:enable='gte(t,{t_ans_start})'[with_ans_text]"
        )
```

with:

```python
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
```

Finally, go back to `backend/app/services/job_manager.py` and add `correct_index=item.correct_index` to the same two `render_short_video(...)` calls Task 2 already updated (in `process_single` and `retry_single`) — one new kwarg line at the end of each call's argument list.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_video_service_correctness.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Run the full backend test suite to confirm nothing upstream regressed**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/ -v`
Expected: PASS (all tests green)

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/video_service.py backend/app/services/job_manager.py backend/tests/test_video_service_correctness.py
git commit -m "feat: highlight the correct multiple-choice option instead of a second answer string"
```

---

### Task 6: Shared cinematic background treatment helper

**Files:**
- Create: `backend/app/services/vfx_helpers.py`
- Modify: `backend/app/services/video_service.py:194-209`
- Modify: `backend/app/services/poem_service.py` (the background filter block inside `render_poem_short`, the `[0:v]scale=...eq=...vignette...[base_bg]` chain immediately following `filter_chains = []`)
- Test: `backend/tests/test_vfx_helpers.py`

**Interfaces:**
- Consumes: nothing from earlier tasks — this is a new standalone pure module.
- Produces: `build_cinematic_bg_filter(input_label: str, output_label: str, width: int, height: int, total_duration: float, fps: int, zoom_enabled: bool, zoom_direction: str = "in") -> str`, imported by both `video_service.py` and `poem_service.py`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_vfx_helpers.py
from backend.app.services.vfx_helpers import build_cinematic_bg_filter


def test_zoom_enabled_contains_zoompan():
    result = build_cinematic_bg_filter(
        input_label="0:v", output_label="base_bg",
        width=1080, height=1920, total_duration=10.0, fps=30,
        zoom_enabled=True, zoom_direction="in",
    )
    assert "zoompan" in result


def test_zoom_disabled_omits_zoompan():
    result = build_cinematic_bg_filter(
        input_label="0:v", output_label="base_bg",
        width=1080, height=1920, total_duration=10.0, fps=30,
        zoom_enabled=False,
    )
    assert "zoompan" not in result


def test_both_modes_include_eq_and_vignette():
    zoomed = build_cinematic_bg_filter(
        input_label="0:v", output_label="base_bg",
        width=1080, height=1920, total_duration=10.0, fps=30,
        zoom_enabled=True,
    )
    flat = build_cinematic_bg_filter(
        input_label="0:v", output_label="base_bg",
        width=1080, height=1920, total_duration=10.0, fps=30,
        zoom_enabled=False,
    )
    for result in (zoomed, flat):
        assert "eq=contrast=1.15:saturation=1.4:gamma=1.05" in result
        assert "vignette=PI/3.5" in result


def test_zoom_direction_in_vs_out_differ():
    zoom_in = build_cinematic_bg_filter(
        input_label="0:v", output_label="base_bg",
        width=1080, height=1920, total_duration=10.0, fps=30,
        zoom_enabled=True, zoom_direction="in",
    )
    zoom_out = build_cinematic_bg_filter(
        input_label="0:v", output_label="base_bg",
        width=1080, height=1920, total_duration=10.0, fps=30,
        zoom_enabled=True, zoom_direction="out",
    )
    assert "z='min(1.06,1+0.0002*on)'" in zoom_in
    assert "z='max(0.94,1.06-0.0002*on)'" in zoom_out
    assert zoom_in != zoom_out


def test_output_label_is_wired_into_final_bracket():
    result = build_cinematic_bg_filter(
        input_label="1:v", output_label="my_bg",
        width=1080, height=1920, total_duration=5.0, fps=30,
        zoom_enabled=False,
    )
    assert result.startswith("[1:v]")
    assert result.endswith("[my_bg]")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_vfx_helpers.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.app.services.vfx_helpers'`

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/services/vfx_helpers.py
"""Shared pure-logic helpers for building reusable ffmpeg filter-graph fragments
used by both the trivia (video_service.py) and poem (poem_service.py) renderers.
"""
import math


def build_cinematic_bg_filter(
    input_label: str,
    output_label: str,
    width: int,
    height: int,
    total_duration: float,
    fps: int,
    zoom_enabled: bool,
    zoom_direction: str = "in",
) -> str:
    """Build a single ffmpeg filter-chain string that scales/crops a background
    video to the target frame size, optionally applies a subtle Ken Burns zoompan,
    and always applies the contrast/saturation/vignette cinematic color treatment.

    Returns a string of the form "[{input_label}]...[{output_label}]" ready to be
    joined with other filter_chains entries via ";\\n".join(...).
    """
    color_treatment = "eq=contrast=1.15:saturation=1.4:gamma=1.05,vignette=PI/3.5"

    if zoom_enabled:
        if zoom_direction == "out":
            zoom_expr = "z='max(0.94,1.06-0.0002*on)'"
        else:
            zoom_expr = "z='min(1.06,1+0.0002*on)'"

        total_frames = int(total_duration * fps) + 10
        return (
            f"[{input_label}]scale={width + 120}:{height + 214}:force_original_aspect_ratio=increase,"
            f"crop={width + 120}:{height + 214},"
            f"zoompan={zoom_expr}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s={width}x{height}:fps={fps},"
            f"{color_treatment}[{output_label}]"
        )

    return (
        f"[{input_label}]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"{color_treatment}[{output_label}]"
    )
```

Wire it into `video_service.py`. Replace the existing `if bg_zoom: ... else: ...` block (lines 197-209) with:

```python
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
```

Add the two required imports near the top of `video_service.py`:

```python
import random
from backend.app.services.vfx_helpers import build_cinematic_bg_filter
```

Wire it into `poem_service.py`. Replace the background block:

```python
        filter_chains.append(
            f"[0:v]scale={config.width}:{config.height}:force_original_aspect_ratio=increase,"
            f"crop={config.width}:{config.height},"
            f"eq=contrast=1.15:saturation=1.4:gamma=1.05,"
            f"vignette=PI/3.5[base_bg]"
        )
```

with:

```python
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
```

Add the import near the top of `poem_service.py`:

```python
from backend.app.services.vfx_helpers import build_cinematic_bg_filter
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_vfx_helpers.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/vfx_helpers.py backend/app/services/video_service.py backend/app/services/poem_service.py backend/tests/test_vfx_helpers.py
git commit -m "feat: share Ken Burns zoom + cinematic color treatment between trivia and poem renderers"
```

---

### Task 7: Staggered overshoot easing for option entrance

**Files:**
- Modify: `backend/app/services/video_service.py:312-317`
- Test: `backend/tests/test_option_easing.py`

**Interfaces:**
- Consumes: nothing new from earlier tasks; operates on the existing per-option loop variables `curr_opt_y`, `i`, `anim_style` already present in `video_service.py`. Does not touch the Task 5 highlight-overlay block (that block only *adds* new drawtext calls after this one).
- Produces: `compute_overshoot_y(curr_opt_y: float, delay_s: float, t: float, overshoot_amount: float = 18.0, settle_dur: float = 0.35) -> float` and `build_overshoot_y_expr(curr_opt_y: int, delay_s: float, overshoot_amount: float = 18.0, settle_dur: float = 0.35) -> str`, both appended to `vfx_helpers.py` (Task 6).

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_option_easing.py
import math
from backend.app.services.vfx_helpers import compute_overshoot_y


def test_before_delay_holds_offscreen_position():
    curr_opt_y = 960
    delay_s = 0.26
    y = compute_overshoot_y(curr_opt_y, delay_s, t=0.1)
    assert y == curr_opt_y + 600


def test_overshoots_above_resting_position_then_settles():
    curr_opt_y = 960
    delay_s = 0.26
    settle_dur = 0.35

    min_y = min(
        compute_overshoot_y(curr_opt_y, delay_s, t=delay_s + frac * settle_dur, settle_dur=settle_dur)
        for frac in [i / 100 for i in range(1, 100)]
    )
    assert min_y < curr_opt_y

    y_end = compute_overshoot_y(curr_opt_y, delay_s, t=delay_s + settle_dur, settle_dur=settle_dur)
    assert math.isclose(y_end, curr_opt_y, abs_tol=0.5)


def test_stagger_produces_increasing_delays():
    delays = [0.1 + (i * 0.08) for i in range(4)]
    assert delays == sorted(delays)
    assert delays[0] < delays[-1]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_option_easing.py -v`
Expected: FAIL with `ImportError: cannot import name 'compute_overshoot_y' from 'backend.app.services.vfx_helpers'`

- [ ] **Step 3: Write minimal implementation**

Append to `backend/app/services/vfx_helpers.py`:

```python
def compute_overshoot_y(
    curr_opt_y: float,
    delay_s: float,
    t: float,
    overshoot_amount: float = 18.0,
    settle_dur: float = 0.35,
) -> float:
    """Pure Python mirror of the ffmpeg y_expr used for option-card entrance easing.

    Mirrors exactly:
        if(lt(t,delay_s),
           curr_opt_y+600,
           if(lt(t,delay_s+settle_dur),
              curr_opt_y-overshoot_amount*sin(PI*(t-delay_s)/settle_dur)*exp(-3*(t-delay_s)),
              curr_opt_y))
    """
    if t < delay_s:
        return curr_opt_y + 600
    if t < delay_s + settle_dur:
        dt = t - delay_s
        return curr_opt_y - overshoot_amount * math.sin(math.pi * dt / settle_dur) * math.exp(-3 * dt)
    return curr_opt_y


def build_overshoot_y_expr(
    curr_opt_y: int,
    delay_s: float,
    overshoot_amount: float = 18.0,
    settle_dur: float = 0.35,
) -> str:
    """Build the ffmpeg-expression-language string matching compute_overshoot_y above.
    Only uses ffmpeg-expression-safe primitives: if/lt/sin/exp/PI/+-*/.
    """
    return (
        f"if(lt(t,{delay_s}),{curr_opt_y}+600,"
        f"if(lt(t,{delay_s}+{settle_dur}),"
        f"{curr_opt_y}-{overshoot_amount}*sin(PI*(t-{delay_s})/{settle_dur})*exp(-3*(t-{delay_s})),"
        f"{curr_opt_y}))"
    )
```

Replace the easing block in `video_service.py`:

```python
                curr_opt_y = base_opt_y + (i * opt_spacing)
                if anim_style in ["slide", "bounce", "pop"]:
                    delay_s = 0.1 + (i * 0.08)
                    y_expr = f"if(lt(t,{delay_s}+0.3),{curr_opt_y}+600*(1-min(1,max(0,(t-{delay_s})/0.3)))*(1-min(1,max(0,(t-{delay_s})/0.3))),{curr_opt_y})"
                else:
                    y_expr = str(curr_opt_y)
```

with:

```python
                curr_opt_y = base_opt_y + (i * opt_spacing)
                if anim_style in ["slide", "bounce", "pop"]:
                    delay_s = 0.1 + (i * 0.08)
                    y_expr = build_overshoot_y_expr(curr_opt_y, delay_s)
                else:
                    y_expr = str(curr_opt_y)
```

Update the `vfx_helpers` import line in `video_service.py`:

```python
from backend.app.services.vfx_helpers import build_cinematic_bg_filter, build_overshoot_y_expr
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_option_easing.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/vfx_helpers.py backend/app/services/video_service.py backend/tests/test_option_easing.py
git commit -m "feat: add staggered back-out overshoot easing to option card entrance"
```

---

### Task 8: Countdown pulse ring + flash-on-go

**Files:**
- Modify: `backend/app/services/video_service.py:337-375` (countdown badge/number block) and immediately after (insertion point for the new flash, right before the answer-related layers begin at `with_num_1`)
- Test: `backend/tests/test_countdown_pulse.py`

**Interfaces:**
- Consumes: `t_cd_start`, `t_cd_3_end`, `t_cd_2_end`, `t_cd_end` (existing timing vars), `config.width`, `config.height`, and the existing `with_num_1` output label.
- Produces: `build_countdown_tick_pulse(prior_layer: str, output_label: str, x: int, y_expr: str, tick_start: float, tick_end: float, box_w: int = 260, box_h: int = 260) -> str` and `build_flash_overlay(prior_layer: str, output_label: str, width: int, height: int, flash_time: float, flash_dur: float = 0.25) -> list[str]`, both in `vfx_helpers.py`; the flash list's last bracket label (`with_cd_flash`) becomes the new prior-layer handoff for the subsequent answer-card overlay.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_countdown_pulse.py
from backend.app.services.vfx_helpers import build_countdown_tick_pulse, build_flash_overlay


def test_pulse_ring_uses_drawbox_with_alpha_oscillation():
    result = build_countdown_tick_pulse(
        prior_layer="with_num_3", output_label="with_pulse_3",
        x=390, y_expr="980", tick_start=0.0, tick_end=1.0,
    )
    assert "drawbox" in result
    assert "alpha='0.3+0.3*sin(2*PI*(t-0.0)*4)'" in result
    assert "enable='between(t,0.0,1.0)'" in result
    assert result.startswith("[with_num_3]")
    assert result.endswith("[with_pulse_3]")


def test_flash_overlay_returns_two_chains_ending_in_named_label():
    chains = build_flash_overlay(
        prior_layer="with_num_1", output_label="with_cd_flash",
        width=1080, height=1920, flash_time=3.0, flash_dur=0.25,
    )
    assert isinstance(chains, list)
    assert len(chains) == 2
    joined = ";".join(chains)
    assert "color=c=white:s=1080x1920:d=0.25" in joined
    assert "fade=t=in" in joined and "fade=t=out" in joined
    assert "[with_num_1]" in joined
    assert joined.strip().endswith("[with_cd_flash]")
    assert "enable='between(t,3.0,3.25)'" in joined


def test_flash_source_label_is_unique_per_call():
    chains_a = build_flash_overlay("layer_a", "out_a", 1080, 1920, 1.0)
    chains_b = build_flash_overlay("layer_b", "out_b", 1080, 1920, 5.0)
    src_a = [c for c in chains_a if "color=c=white" in c][0].split("[")[-1].split("]")[0]
    src_b = [c for c in chains_b if "color=c=white" in c][0].split("[")[-1].split("]")[0]
    assert src_a != src_b
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_countdown_pulse.py -v`
Expected: FAIL with `ImportError: cannot import name 'build_countdown_tick_pulse' from 'backend.app.services.vfx_helpers'`

- [ ] **Step 3: Write minimal implementation**

Append to `backend/app/services/vfx_helpers.py`:

```python
def build_countdown_tick_pulse(
    prior_layer: str,
    output_label: str,
    x: int,
    y_expr: str,
    tick_start: float,
    tick_end: float,
    box_w: int = 260,
    box_h: int = 260,
) -> str:
    """Build a semi-transparent white 'ring flash' drawbox behind a countdown
    number, alpha-oscillating at 4Hz, gated to one tick's enable window.
    """
    return (
        f"[{prior_layer}]drawbox=x={x}:y='{y_expr}':w={box_w}:h={box_h}:"
        f"color=white@1:t=fill:"
        f"alpha='0.3+0.3*sin(2*PI*(t-{tick_start})*4)':"
        f"enable='between(t,{tick_start},{tick_end})'[{output_label}]"
    )


_flash_src_counter = 0


def build_flash_overlay(
    prior_layer: str,
    output_label: str,
    width: int,
    height: int,
    flash_time: float,
    flash_dur: float = 0.25,
) -> list[str]:
    """Build a two-entry filter chain: a lavfi white color source that fades in
    then out, overlaid onto prior_layer at flash_time. Returns a list of
    filter_chains entries ready to append/extend into the caller's chain list.
    """
    global _flash_src_counter
    _flash_src_counter += 1
    src_label = f"flash_src_{_flash_src_counter}"

    src_chain = (
        f"color=c=white:s={width}x{height}:d={flash_dur},"
        f"format=rgba,"
        f"fade=t=in:st=0:d=0.05:alpha=1,"
        f"fade=t=out:st=0.05:d={flash_dur - 0.05:.2f}:alpha=1[{src_label}]"
    )
    overlay_chain = (
        f"[{prior_layer}][{src_label}]overlay=x=0:y=0:"
        f"enable='between(t,{flash_time},{flash_time + flash_dur})'[{output_label}]"
    )
    return [src_chain, overlay_chain]
```

Extend the `vfx_helpers` import line in `video_service.py`:

```python
from backend.app.services.vfx_helpers import (
    build_cinematic_bg_filter,
    build_overshoot_y_expr,
    build_countdown_tick_pulse,
    build_flash_overlay,
)
```

Insert pulse-ring calls right after each of the three existing number `drawtext` chains, re-pointing the downstream layer each consumes. Replace the badge-3/2/1 + number-3/2/1 block (lines ~350-375) with:

```python
        filter_chains.append(
            f"[{options_layer}][7:v]overlay=x=390:y='{b3_y}':enable='between(t,{t_cd_start},{t_cd_3_end})'[with_badge_3]"
        )
        filter_chains.append(
            f"[with_badge_3]drawtext=fontfile='{font_path}':text='3':fontcolor=white:fontsize=170:"
            f"x=(w-text_w)/2:y='{n3_y}':borderw=8:bordercolor=0x0F172A:shadowcolor=black@0.9:shadowx=5:shadowy=5:enable='between(t,{t_cd_start},{t_cd_3_end})'[with_num_3]"
        )
        filter_chains.append(
            build_countdown_tick_pulse(
                prior_layer="with_num_3", output_label="with_pulse_3",
                x=390 - 15, y_expr=b3_y, tick_start=t_cd_start, tick_end=t_cd_3_end,
            )
        )
        filter_chains.append(
            f"[with_pulse_3][8:v]overlay=x=390:y='{b2_y}':enable='between(t,{t_cd_3_end},{t_cd_2_end})'[with_badge_2]"
        )
        filter_chains.append(
            f"[with_badge_2]drawtext=fontfile='{font_path}':text='2':fontcolor=0xFBAA19:fontsize=170:"
            f"x=(w-text_w)/2:y='{n2_y}':borderw=8:bordercolor=0x0F172A:shadowcolor=black@0.9:shadowx=5:shadowy=5:enable='between(t,{t_cd_3_end},{t_cd_2_end})'[with_num_2]"
        )
        filter_chains.append(
            build_countdown_tick_pulse(
                prior_layer="with_num_2", output_label="with_pulse_2",
                x=390 - 15, y_expr=b2_y, tick_start=t_cd_3_end, tick_end=t_cd_2_end,
            )
        )
        filter_chains.append(
            f"[with_pulse_2][9:v]overlay=x=390:y='{b1_y}':enable='between(t,{t_cd_2_end},{t_cd_end})'[with_badge_1]"
        )
        filter_chains.append(
            f"[with_badge_1]drawtext=fontfile='{font_path}':text='1':fontcolor=0xEF4444:fontsize=170:"
            f"x=(w-text_w)/2:y='{n1_y}':borderw=8:bordercolor=0x0F172A:shadowcolor=black@0.9:shadowx=5:shadowy=5:enable='between(t,{t_cd_2_end},{t_cd_end})'[with_num_1]"
        )
        filter_chains.append(
            build_countdown_tick_pulse(
                prior_layer="with_num_1", output_label="with_pulse_1",
                x=390 - 15, y_expr=b1_y, tick_start=t_cd_2_end, tick_end=t_cd_end,
            )
        )
        filter_chains.extend(
            build_flash_overlay(
                prior_layer="with_pulse_1", output_label="with_cd_flash",
                width=config.width, height=config.height,
                flash_time=t_cd_end, flash_dur=0.25,
            )
        )
```

This changes the downstream answer-card overlay to consume `with_cd_flash` instead of `with_num_1`:

```python
        filter_chains.append(
            f"[with_cd_flash][6:v]overlay=x=70:y='{a_card_y}':enable='gte(t,{t_ans_start})'[with_ans_frame]"
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_countdown_pulse.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/vfx_helpers.py backend/app/services/video_service.py backend/tests/test_countdown_pulse.py
git commit -m "feat: add pulsing ring flash to countdown ticks and a full-screen flash on GO"
```

---

### Task 9: Weighted karaoke timing + selectable highlight styles

**Files:**
- Modify: `backend/app/services/ass_maker.py` (full-file rewrite, 44 lines currently)
- Modify: `backend/app/services/poem_service.py:110`
- Test: `backend/tests/test_ass_maker.py`

**Interfaces:**
- Consumes: `PoemRenderConfig.karaoke_style` (already exists at `backend/app/models/poem_schemas.py:51`, default `"bouncing_star"`) and `lines_timing` list-of-dicts already built in `poem_service.py` (each item `{'text', 'start', 'end', 'duration'}`).
- Produces: `generate_karaoke_line(text: str, duration: float, style: str = "bouncing_star") -> str` and `create_ass_file(lines_timing: List[dict], output_path: str, style: str = "bouncing_star") -> None`, both consumed at the single call site `poem_service.py:110`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_ass_maker.py
from backend.app.services.ass_maker import generate_karaoke_line


def test_character_weighted_timing_favors_longer_word():
    import re
    line = generate_karaoke_line("a extraordinary", 10.0, style="clean_cards")
    ks = [int(m) for m in re.findall(r"\\k(\d+)", line)]
    assert len(ks) == 2
    short_k, long_k = ks
    assert long_k > short_k
    assert long_k > short_k * 5


def test_three_styles_produce_different_output():
    text, dur = "hello world", 2.0
    star = generate_karaoke_line(text, dur, style="bouncing_star")
    glow = generate_karaoke_line(text, dur, style="glow_highlight")
    clean = generate_karaoke_line(text, dur, style="clean_cards")
    assert star != glow
    assert glow != clean
    assert star != clean


def test_clean_cards_matches_original_plain_format():
    line = generate_karaoke_line("hello world", 2.0, style="clean_cards")
    assert "\\bord" not in line
    assert "\\fscy" not in line
    assert "\\t(" not in line
    words = line.split(" ")
    assert len(words) == 2
    assert all(w.startswith("{\\k") and "}" in w for w in words)


def test_glow_highlight_adds_border_override():
    line = generate_karaoke_line("hi", 1.0, style="glow_highlight")
    assert "\\bord14" in line
    assert "\\3c&H0047E0FD&" in line


def test_bouncing_star_adds_scale_transform():
    line = generate_karaoke_line("hi", 1.0, style="bouncing_star")
    assert "\\t(0,150,\\fscy110)" in line
    assert "\\t(150,300,\\fscy100)" in line
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_ass_maker.py -v`
Expected: FAIL with `TypeError: generate_karaoke_line() got an unexpected keyword argument 'style'`

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/services/ass_maker.py
from typing import List


def format_time(seconds: float) -> str:
    """Format seconds to ASS time format h:mm:ss.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _char_weighted_durations_cs(words: List[str], duration: float) -> List[int]:
    """Split a total duration (in centiseconds) across words weighted by
    character count instead of an even split. Guards against an all-empty
    word list and rounding drift by assigning any leftover centiseconds to
    the last word.
    """
    total_cs = int(duration * 100)
    total_chars = sum(len(w) for w in words) or 1
    durations = [int(total_cs * len(w) / total_chars) for w in words]
    assigned = sum(durations)
    if durations:
        durations[-1] += total_cs - assigned
    return durations


def generate_karaoke_line(text: str, duration: float, style: str = "bouncing_star") -> str:
    """Distribute duration across words (character-count-weighted) and add ASS
    karaoke tags, with optional per-style highlight decoration.
    """
    words = text.split()
    if not words:
        return ""

    durations_cs = _char_weighted_durations_cs(words, duration)

    parts = []
    for word, cs in zip(words, durations_cs):
        if style == "glow_highlight":
            parts.append(f"{{\\k{cs}\\bord14\\3c&H0047E0FD&}}{word}")
        elif style == "bouncing_star":
            parts.append(f"{{\\k{cs}\\t(0,150,\\fscy110)\\t(150,300,\\fscy100)}}{word}")
        else:  # "clean_cards" and any unrecognized style fall back to plain sweep
            parts.append(f"{{\\k{cs}}}{word}")

    return " ".join(parts)


def create_ass_file(lines_timing: List[dict], output_path: str, style: str = "bouncing_star"):
    """
    lines_timing: list of dicts: {'text': str, 'start': float, 'end': float, 'duration': float}
    """
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Karaoke,Arial,84,&H0047E0FD,&H00FFFFFF,&H00333333,&H80000000,-1,0,0,0,100,100,0,0,1,10,4,8,100,100,1100,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    for item in lines_timing:
        t_start = format_time(item['start'])
        t_end = format_time(item['end'] + 0.3)
        k_text = generate_karaoke_line(item['text'], item['duration'], style=style)
        ass_content += f"Dialogue: 0,{t_start},{t_end},Karaoke,,0,0,0,,{k_text}\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
```

Update the call site in `poem_service.py:110` — replace `create_ass_file(lines_timing, str(ass_path))` with `create_ass_file(lines_timing, str(ass_path), style=config.karaoke_style)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_ass_maker.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/ass_maker.py backend/app/services/poem_service.py backend/tests/test_ass_maker.py
git commit -m "feat: weight karaoke timing by word length and support 3 selectable highlight styles"
```

---

### Task 10: Poem outro celebration (confetti + flash parity)

**Files:**
- Modify: `backend/app/services/poem_service.py` (insert a new filter block between the `with_sing_hdr` layer and the final `ass=` call, and add a new `-i` input for the confetti asset)
- Test: `backend/tests/test_outro_celebration.py`

**Interfaces:**
- Consumes: `ensure_confetti_assets` (`from backend.app.utils.generate_confetti import ensure_confetti_assets`), `total_duration` (existing local var in `render_poem_short`), `with_sing_hdr` (existing layer label immediately before the current `ass=` call).
- Produces: `_build_outro_celebration_filters(prior_layer: str, confetti_input_idx: int, width: int, height: int, outro_start: float) -> tuple[list[str], str]` in `vfx_helpers.py`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_outro_celebration.py
from backend.app.services.vfx_helpers import _build_outro_celebration_filters


def test_returns_chains_and_final_layer_label():
    chains, final_layer = _build_outro_celebration_filters(
        prior_layer="with_sing_hdr", confetti_input_idx=8,
        width=1080, height=1920, outro_start=12.5,
    )
    assert isinstance(chains, list)
    assert len(chains) >= 3
    assert isinstance(final_layer, str)
    assert final_layer != "with_sing_hdr"


def test_confetti_input_is_scaled_and_gated_to_outro_window():
    chains, _ = _build_outro_celebration_filters(
        prior_layer="with_sing_hdr", confetti_input_idx=8,
        width=1080, height=1920, outro_start=12.5,
    )
    joined = ";".join(chains)
    assert "[8:v]scale=1080:1920" in joined
    assert "enable='between(t,12.5,12.5+2.0)'" in joined


def test_flash_is_gated_at_outro_start():
    chains, _ = _build_outro_celebration_filters(
        prior_layer="with_sing_hdr", confetti_input_idx=8,
        width=1080, height=1920, outro_start=12.5,
    )
    joined = ";".join(chains)
    assert "color=c=white:s=1080x1920:d=0.25" in joined
    assert "enable='between(t,12.5,12.75)'" in joined


def test_chain_starts_from_prior_layer_and_ends_at_final_layer():
    chains, final_layer = _build_outro_celebration_filters(
        prior_layer="with_sing_hdr", confetti_input_idx=8,
        width=1080, height=1920, outro_start=12.5,
    )
    assert "with_sing_hdr" in chains[0]
    assert chains[-1].endswith(f"[{final_layer}]")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_outro_celebration.py -v`
Expected: FAIL with `ImportError: cannot import name '_build_outro_celebration_filters' from 'backend.app.services.vfx_helpers'`

- [ ] **Step 3: Write minimal implementation**

Append to `backend/app/services/vfx_helpers.py` (reuses `build_flash_overlay` from Task 8):

```python
def _build_outro_celebration_filters(
    prior_layer: str,
    confetti_input_idx: int,
    width: int,
    height: int,
    outro_start: float,
) -> tuple[list[str], str]:
    """Build the confetti-burst + white-flash celebration filters for a poem's
    outro (last ~1.5s pause). Chained BEFORE the final ass= subtitle filter so
    captions stay legible on top. Returns (chains, final_layer_label).
    """
    chains: list[str] = []

    confetti_scaled_label = "outro_confetti_scaled"
    chains.append(f"[{confetti_input_idx}:v]scale={width}:{height}[{confetti_scaled_label}]")

    with_confetti_label = "with_outro_confetti"
    chains.append(
        f"[{prior_layer}][{confetti_scaled_label}]overlay=x=0:y=0:"
        f"enable='between(t,{outro_start},{outro_start}+2.0)'[{with_confetti_label}]"
    )

    flash_chains = build_flash_overlay(
        prior_layer=with_confetti_label,
        output_label="with_outro_flash",
        width=width,
        height=height,
        flash_time=outro_start,
        flash_dur=0.25,
    )
    chains.extend(flash_chains)

    return chains, "with_outro_flash"
```

Wire it into `render_poem_short` in `poem_service.py`. Near the top of the method (after `font_path = self._get_font_path()`), add:

```python
        from backend.app.utils.generate_confetti import ensure_confetti_assets
        from backend.app.services.vfx_helpers import _build_outro_celebration_filters

        vfx_dir = ASSETS_DIR / "vfx"
        confetti_video = None
        try:
            vfx_assets = ensure_confetti_assets(vfx_dir)
            confetti_video = vfx_assets.get("confetti")
        except Exception:
            confetti_video = None
```

Replace the tail of the filter-graph construction — where the file currently has:

```python
        escaped_ass_path = str(ass_path).replace(":", "\\:")
        filter_chains.append(f"[with_sing_hdr]ass='{escaped_ass_path}'[vout]")
```

replace with:

```python
        outro_start = total_duration - 1.5
        pre_ass_layer = "with_sing_hdr"
        confetti_input_idx = None
        if confetti_video and confetti_video.is_file():
            confetti_input_idx = 8  # next free index after d1..d4 (indices 4-7)
            celebration_chains, pre_ass_layer = _build_outro_celebration_filters(
                prior_layer="with_sing_hdr",
                confetti_input_idx=confetti_input_idx,
                width=config.width,
                height=config.height,
                outro_start=outro_start,
            )
            filter_chains.extend(celebration_chains)

        escaped_ass_path = str(ass_path).replace(":", "\\:")
        filter_chains.append(f"[{pre_ass_layer}]ass='{escaped_ass_path}'[vout]")
```

Add the confetti file as a new conditional `-i` input in the `cmd` list, right after the existing `"-i", str(d4)` entry:

```python
        cmd = [
            ffmpeg_bin, "-y",
            "-stream_loop", "-1", "-i", str(bg_video_path),
            "-i", str(master_audio),
            "-i", str(header_pill_png),
            "-i", str(lyric_card_png),
            "-i", str(d1), "-i", str(d2), "-i", str(d3), "-i", str(d4),
        ]
        if confetti_input_idx is not None:
            cmd.extend(["-i", str(confetti_video)])
        cmd.extend([
            "-filter_complex", full_filter_complex,
            "-map", "[vout]", "-map", "1:a",
            "-t", str(total_duration),
            "-c:v", config.video_codec, "-preset", "fast", "-b:v", config.video_bitrate,
            "-pix_fmt", config.pix_fmt, "-r", str(config.fps),
            "-c:a", config.audio_codec, "-b:a", "192k",
            str(output_mp4_path),
        ])
```

(`full_filter_complex` is still built the same way, from `filter_chains`, right before this — this replaces the file's original single-list `cmd = [...]` literal.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_outro_celebration.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/vfx_helpers.py backend/app/services/poem_service.py backend/tests/test_outro_celebration.py
git commit -m "feat: add confetti burst and white flash to poem outro for trivia visual parity"
```

---

### Task 11: Frontend karaoke style selector wiring

**Files:**
- Modify: `frontend/src/components/PoemStudio.tsx` (insert new UI block near the existing `melody_track`/`melody_volume` controls, around lines 283-306)

**Interfaces:**
- Consumes: `config.karaoke_style` and `setConfig` (already exist in `PoemStudio.tsx`'s component state, per `frontend/src/types/poem.ts`'s `PoemRenderConfig.karaoke_style` and the default-config initializer at `PoemStudio.tsx:63`). Also consumes Task 9's backend contract: whichever value is set here lands unchanged at `create_ass_file(..., style=config.karaoke_style)`.
- Produces: nothing consumed by later tasks.

This is a pure-UI change with no unit-testable pure logic, so per-task automated testing is replaced with manual verification via the dev server.

- [ ] **Step 1: Locate the insertion point**

Open `frontend/src/components/PoemStudio.tsx` and find the existing melody controls block (around lines 283-306):

```tsx
<div>
  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Melody Track</label>
  <select
    value={config.melody_track}
    onChange={(e) => setConfig((p) => ({ ...p, melody_track: e.target.value }))}
    className="w-full mt-1 bg-slate-900 border border-slate-700 rounded-md px-2 py-1.5 text-sm"
  >
    {/* ...existing options... */}
  </select>
  {/* ...melody_volume slider... */}
</div>
```

- [ ] **Step 2: Insert the karaoke style button-group control immediately after that melody block**

```tsx
<div className="pt-2">
  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Karaoke Highlight Style</label>
  <div className="grid grid-cols-3 gap-1.5 pt-1">
    {[
      { value: 'bouncing_star', label: '⭐ Bouncing Star' },
      { value: 'glow_highlight', label: '✨ Glow Highlight' },
      { value: 'clean_cards', label: '📋 Clean Cards' },
    ].map((opt) => (
      <button
        key={opt.value}
        type="button"
        onClick={() => setConfig((p) => ({ ...p, karaoke_style: opt.value as 'bouncing_star' | 'glow_highlight' | 'clean_cards' }))}
        className={`text-xs font-medium rounded-md px-2 py-1.5 transition-colors ${
          config.karaoke_style === opt.value
            ? 'bg-amber-500 text-slate-900 font-bold'
            : 'bg-slate-900 text-slate-300 hover:bg-slate-700'
        }`}
      >
        {opt.label}
      </button>
    ))}
  </div>
</div>
```

- [ ] **Step 3: Manual verification (no automated test — pure UI control)**

Run:
```bash
cd /Users/manhashed/work/ai-shorts-generation/trivia/frontend && npm run dev
```

Open the Poem Studio page, confirm the "Karaoke Highlight Style" button group renders under the melody controls with three buttons; "⭐ Bouncing Star" is highlighted amber by default; clicking the other two switches the highlight; triggering a poem render includes the selected `karaoke_style` value in the submitted `PoemRenderConfig` (check via browser devtools network tab).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/PoemStudio.tsx
git commit -m "feat: add karaoke highlight style selector to Poem Studio UI"
```

---

### Task 12: Mascot art upgrade — supersampled gradient rendering + persona rebrand

**Files:**
- Modify: `backend/app/utils/generate_mascots_all.py` (full rewrite)
- Modify: `backend/app/main.py:85-120`
- Test: `backend/tests/test_generate_mascots.py`

**Interfaces:**
- Consumes: nothing (asset generator, no cross-task dependency).
- Produces: `_supersampled_canvas`, `_paste_gradient_ellipse`, `_finalize` helpers; `render_bear/penguin/lion/bunny(asking: bool, size: int = 512) -> Image.Image` (unchanged signatures — `video_service.py`'s `_get_mascot_paths` and `job_manager.py`'s `MASCOTS_ROTATION` need zero changes); `/api/mascots` returns the 4 new persona names/taglines.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_generate_mascots.py
from backend.app.utils.generate_mascots_all import (
    render_bear, render_penguin, render_lion, render_bunny,
    _supersampled_canvas, _paste_gradient_ellipse, _finalize,
)


def _assert_valid_mascot(img):
    assert img.size == (512, 512)
    assert img.mode == "RGBA"
    alpha = img.split()[-1]
    assert alpha.getextrema()[1] > 0


def test_all_four_characters_both_poses_render_512_rgba_nonempty():
    for render_fn in (render_bear, render_penguin, render_lion, render_bunny):
        _assert_valid_mascot(render_fn(asking=True))
        _assert_valid_mascot(render_fn(asking=False))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_generate_mascots.py -v`
Expected: FAIL with `ImportError: cannot import name '_supersampled_canvas' from 'backend.app.utils.generate_mascots_all'` — these helpers don't exist in the current flat-fill implementation.

- [ ] **Step 3: Write minimal implementation**

Full rewritten `backend/app/utils/generate_mascots_all.py`:

```python
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps

SUPERSAMPLE = 4


def _supersampled_canvas(size: int, supersample: int = SUPERSAMPLE) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Create an RGBA canvas at `size * supersample` px so shapes drawn on it
    can later be downsampled with LANCZOS for anti-aliased, crisp edges
    instead of the jagged circles flat ImageDraw primitives produce at
    native resolution."""
    big = size * supersample
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _paste_gradient_ellipse(img: Image.Image, bbox: list, inner_color: tuple, outer_color: tuple) -> None:
    """Paint a radial-gradient-filled ellipse into `img` at `bbox`: `inner_color`
    at the center fading to `outer_color` at the rim, for a simple "3D toy"
    shading look instead of a flat single-color fill."""
    x0, y0, x1, y1 = bbox
    w, h = int(x1 - x0), int(y1 - y0)
    if w <= 0 or h <= 0:
        return
    mask_size = max(w, h)
    raw_mask = Image.radial_gradient("L").resize((mask_size, mask_size), Image.LANCZOS)
    raw_mask = ImageOps.invert(raw_mask)
    mask = raw_mask.resize((w, h), Image.LANCZOS)
    inner_layer = Image.new("RGBA", (w, h), inner_color)
    outer_layer = Image.new("RGBA", (w, h), outer_color)
    patch = Image.composite(inner_layer, outer_layer, mask)
    ellipse_mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(ellipse_mask).ellipse([0, 0, w - 1, h - 1], fill=255)
    img.paste(patch, (int(x0), int(y0)), ellipse_mask)


def _finalize(img: Image.Image, size: int, supersample: int = SUPERSAMPLE) -> Image.Image:
    """Add a soft drop shadow behind the character, then downsample the
    supersampled canvas to the final `size x size` output with LANCZOS."""
    silhouette_alpha = img.split()[-1]
    shadow_flat = Image.new("RGBA", img.size, (20, 20, 30, 140))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow.paste(shadow_flat, (0, 0), silhouette_alpha)
    offset = 14 * supersample
    shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow_layer.paste(shadow, (offset, offset), shadow)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=10 * supersample))
    composed = Image.alpha_composite(shadow_layer, img)
    return composed.resize((size, size), Image.LANCZOS)


def render_bear(asking: bool, size: int = 512) -> Image.Image:
    img, d = _supersampled_canvas(size)
    s = SUPERSAMPLE
    cx, cy = (size * s) // 2, (size * s) // 2 + 20 * s
    c_fur = (198, 125, 68, 255)
    c_fur_light = (222, 155, 98, 255)
    c_muzzle = (250, 225, 195, 255)
    c_inner_ear = (245, 175, 180, 255)
    c_cheeks = (255, 130, 140, 180)
    c_eye = (35, 25, 20, 255)
    c_cap = (59, 130, 246, 255) if asking else (16, 185, 129, 255)

    _paste_gradient_ellipse(img, [cx - 190*s, cy - 200*s, cx - 70*s, cy - 80*s], c_fur_light, c_fur)
    d.ellipse([cx - 170*s, cy - 180*s, cx - 90*s, cy - 100*s], fill=c_inner_ear)
    _paste_gradient_ellipse(img, [cx + 70*s, cy - 200*s, cx + 190*s, cy - 80*s], c_fur_light, c_fur)
    d.ellipse([cx + 90*s, cy - 180*s, cx + 170*s, cy - 100*s], fill=c_inner_ear)
    _paste_gradient_ellipse(img, [cx - 160*s, cy - 140*s, cx + 160*s, cy + 140*s], c_fur_light, c_fur)

    if asking:
        d.chord([cx - 110*s, cy - 210*s, cx + 110*s, cy - 110*s], start=180, end=360, fill=c_cap)
        d.ellipse([cx - 130*s, cy - 135*s, cx + 130*s, cy - 105*s], fill=(37, 99, 235, 255))
        d.ellipse([cx - 15*s, cy - 185*s, cx + 15*s, cy - 155*s], fill=(250, 204, 21, 255))
    else:
        d.polygon([(cx, cy - 240*s), (cx - 70*s, cy - 120*s), (cx + 70*s, cy - 120*s)], fill=c_cap)
        d.ellipse([cx - 18*s, cy - 255*s, cx + 18*s, cy - 225*s], fill=(251, 191, 36, 255))

    d.ellipse([cx - 95*s, cy - 20*s, cx + 95*s, cy + 110*s], fill=c_muzzle)
    d.ellipse([cx - 135*s, cy + 10*s, cx - 75*s, cy + 60*s], fill=c_cheeks)
    d.ellipse([cx + 75*s, cy + 10*s, cx + 135*s, cy + 60*s], fill=c_cheeks)
    d.ellipse([cx - 28*s, cy + 10*s, cx + 28*s, cy + 48*s], fill=(45, 25, 15, 255))
    d.ellipse([cx - 14*s, cy + 15*s, cx - 3*s, cy + 26*s], fill=(255, 255, 255, 200))

    if asking:
        d.arc([cx - 35*s, cy + 45*s, cx + 5*s, cy + 85*s], start=0, end=140, fill=(45, 25, 15, 255), width=6*s)
        d.arc([cx - 5*s, cy + 45*s, cx + 35*s, cy + 85*s], start=40, end=180, fill=(45, 25, 15, 255), width=6*s)
        d.ellipse([cx - 90*s, cy - 65*s, cx - 25*s, cy + 5*s], fill=c_eye)
        d.ellipse([cx - 80*s, cy - 55*s, cx - 50*s, cy - 25*s], fill=(255, 255, 255, 255))
        d.ellipse([cx + 25*s, cy - 65*s, cx + 90*s, cy + 5*s], fill=c_eye)
        d.ellipse([cx + 35*s, cy - 55*s, cx + 65*s, cy - 25*s], fill=(255, 255, 255, 255))
    else:
        d.chord([cx - 45*s, cy + 40*s, cx + 45*s, cy + 95*s], start=0, end=180, fill=(185, 28, 28, 255))
        d.chord([cx - 25*s, cy + 60*s, cx + 25*s, cy + 95*s], start=0, end=180, fill=(244, 114, 182, 255))
        d.arc([cx - 85*s, cy - 50*s, cx - 30*s, cy + 5*s], start=180, end=360, fill=c_eye, width=12*s)
        d.arc([cx + 30*s, cy - 50*s, cx + 85*s, cy + 5*s], start=180, end=360, fill=c_eye, width=12*s)
        for sx, sy, rad in [(cx - 180*s, cy - 80*s, 20*s), (cx + 180*s, cy - 80*s, 20*s)]:
            d.ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=(251, 191, 36, 255))

    d.polygon([(cx - 70*s, cy + 125*s), (cx, cy + 150*s), (cx - 70*s, cy + 175*s)], fill=(239, 68, 68, 255))
    d.polygon([(cx + 70*s, cy + 125*s), (cx, cy + 150*s), (cx + 70*s, cy + 175*s)], fill=(239, 68, 68, 255))
    d.ellipse([cx - 20*s, cy + 135*s, cx + 20*s, cy + 165*s], fill=(220, 38, 38, 255))

    return _finalize(img, size, s)


def render_penguin(asking: bool, size: int = 512) -> Image.Image:
    img, d = _supersampled_canvas(size)
    s = SUPERSAMPLE
    cx, cy = (size * s) // 2, (size * s) // 2 + 20 * s

    c_body = (30, 41, 59, 255)
    c_body_light = (51, 65, 85, 255)
    c_belly = (255, 255, 255, 255)
    c_belly_shadow = (226, 232, 240, 255)
    c_beak = (245, 158, 11, 255)
    c_cheeks = (251, 113, 133, 180)
    c_earmuffs = (168, 85, 247, 255)

    _paste_gradient_ellipse(img, [cx - 160*s, cy - 160*s, cx + 160*s, cy + 150*s], c_body_light, c_body)
    _paste_gradient_ellipse(img, [cx - 120*s, cy - 100*s, cx + 120*s, cy + 140*s], c_belly, c_belly_shadow)
    d.ellipse([cx - 100*s, cy - 130*s, cx, cy - 10*s], fill=c_belly)
    d.ellipse([cx, cy - 130*s, cx + 100*s, cy - 10*s], fill=c_belly)

    d.arc([cx - 150*s, cy - 190*s, cx + 150*s, cy - 30*s], start=180, end=360, fill=c_earmuffs, width=14*s)
    d.ellipse([cx - 180*s, cy - 130*s, cx - 120*s, cy - 60*s], fill=c_earmuffs)
    d.ellipse([cx + 120*s, cy - 130*s, cx + 180*s, cy - 60*s], fill=c_earmuffs)

    d.ellipse([cx - 110*s, cy + 10*s, cx - 60*s, cy + 50*s], fill=c_cheeks)
    d.ellipse([cx + 60*s, cy + 10*s, cx + 110*s, cy + 50*s], fill=c_cheeks)

    d.polygon([(cx, cy + 45*s), (cx - 35*s, cy + 5*s), (cx + 35*s, cy + 5*s)], fill=c_beak)

    if asking:
        d.ellipse([cx - 75*s, cy - 75*s, cx - 20*s, cy - 10*s], fill=(15, 23, 42, 255))
        d.ellipse([cx - 65*s, cy - 65*s, cx - 40*s, cy - 35*s], fill=(255, 255, 255, 255))
        d.ellipse([cx + 20*s, cy - 75*s, cx + 75*s, cy - 10*s], fill=(15, 23, 42, 255))
        d.ellipse([cx + 30*s, cy - 65*s, cx + 55*s, cy - 35*s], fill=(255, 255, 255, 255))
    else:
        d.arc([cx - 75*s, cy - 65*s, cx - 20*s, cy - 15*s], start=180, end=360, fill=(15, 23, 42, 255), width=12*s)
        d.arc([cx + 20*s, cy - 65*s, cx + 75*s, cy - 15*s], start=180, end=360, fill=(15, 23, 42, 255), width=12*s)
        for sx, sy, rad in [(cx - 170*s, cy - 90*s, 18*s), (cx + 170*s, cy - 90*s, 18*s)]:
            d.ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=(250, 204, 21, 255))

    d.rounded_rectangle([cx - 110*s, cy + 120*s, cx + 110*s, cy + 160*s], radius=15*s, fill=(20, 184, 166, 255))
    return _finalize(img, size, s)


def render_lion(asking: bool, size: int = 512) -> Image.Image:
    img, d = _supersampled_canvas(size)
    s = SUPERSAMPLE
    cx, cy = (size * s) // 2, (size * s) // 2 + 20 * s

    c_mane = (217, 119, 6, 255)
    c_fur = (251, 191, 36, 255)
    c_fur_light = (253, 224, 71, 255)
    c_muzzle = (254, 243, 199, 255)
    c_nose = (180, 83, 9, 255)
    c_cheeks = (251, 146, 60, 180)

    for angle_step in range(0, 360, 30):
        rad = math.radians(angle_step)
        mx = cx + int(160 * s * math.cos(rad))
        my = cy + int(150 * s * math.sin(rad))
        d.ellipse([mx - 60*s, my - 60*s, mx + 60*s, my + 60*s], fill=c_mane)

    _paste_gradient_ellipse(img, [cx - 140*s, cy - 130*s, cx + 140*s, cy + 130*s], c_fur_light, c_fur)

    d.ellipse([cx - 150*s, cy - 160*s, cx - 70*s, cy - 80*s], fill=c_fur)
    d.ellipse([cx - 130*s, cy - 145*s, cx - 90*s, cy - 95*s], fill=(245, 158, 11, 255))
    d.ellipse([cx + 70*s, cy - 160*s, cx + 150*s, cy - 80*s], fill=c_fur)
    d.ellipse([cx + 90*s, cy - 145*s, cx + 130*s, cy - 95*s], fill=(245, 158, 11, 255))

    d.ellipse([cx - 85*s, cy - 10*s, cx + 85*s, cy + 100*s], fill=c_muzzle)
    d.ellipse([cx - 115*s, cy + 15*s, cx - 65*s, cy + 55*s], fill=c_cheeks)
    d.ellipse([cx + 65*s, cy + 15*s, cx + 115*s, cy + 55*s], fill=c_cheeks)

    d.polygon([(cx, cy + 40*s), (cx - 25*s, cy + 10*s), (cx + 25*s, cy + 10*s)], fill=c_nose)

    if asking:
        d.line([(cx - 70*s, cy + 40*s), (cx - 110*s, cy + 30*s)], fill=(120, 53, 15, 255), width=4*s)
        d.line([(cx + 70*s, cy + 40*s), (cx + 110*s, cy + 30*s)], fill=(120, 53, 15, 255), width=4*s)
        d.ellipse([cx - 80*s, cy - 65*s, cx - 25*s, cy - 5*s], fill=(45, 25, 15, 255))
        d.ellipse([cx - 70*s, cy - 55*s, cx - 45*s, cy - 25*s], fill=(255, 255, 255, 255))
        d.ellipse([cx + 25*s, cy - 65*s, cx + 80*s, cy - 5*s], fill=(45, 25, 15, 255))
        d.ellipse([cx + 35*s, cy - 55*s, cx + 60*s, cy - 25*s], fill=(255, 255, 255, 255))
    else:
        d.polygon([(cx - 70*s, cy - 160*s), (cx - 40*s, cy - 130*s), (cx, cy - 180*s), (cx + 40*s, cy - 130*s), (cx + 70*s, cy - 160*s), (cx + 50*s, cy - 110*s), (cx - 50*s, cy - 110*s)], fill=(250, 204, 21, 255))
        d.chord([cx - 40*s, cy + 35*s, cx + 40*s, cy + 85*s], start=0, end=180, fill=(185, 28, 28, 255))
        d.arc([cx - 75*s, cy - 55*s, cx - 25*s, cy - 5*s], start=180, end=360, fill=(45, 25, 15, 255), width=12*s)
        d.arc([cx + 25*s, cy - 55*s, cx + 75*s, cy - 5*s], start=180, end=360, fill=(45, 25, 15, 255), width=12*s)

    return _finalize(img, size, s)


def render_bunny(asking: bool, size: int = 512) -> Image.Image:
    img, d = _supersampled_canvas(size)
    s = SUPERSAMPLE
    cx, cy = (size * s) // 2, (size * s) // 2 + 40 * s

    c_fur = (248, 250, 252, 255)
    c_fur_shadow = (226, 232, 240, 255)
    c_inner_ear = (253, 164, 175, 255)
    c_cheeks = (251, 113, 133, 180)
    c_flower = (244, 63, 94, 255)

    _paste_gradient_ellipse(img, [cx - 120*s, cy - 270*s, cx - 40*s, cy - 80*s], c_fur, c_fur_shadow)
    d.ellipse([cx - 100*s, cy - 240*s, cx - 60*s, cy - 110*s], fill=c_inner_ear)
    _paste_gradient_ellipse(img, [cx + 40*s, cy - 270*s, cx + 120*s, cy - 80*s], c_fur, c_fur_shadow)
    d.ellipse([cx + 60*s, cy - 240*s, cx + 100*s, cy - 110*s], fill=c_inner_ear)

    _paste_gradient_ellipse(img, [cx - 145*s, cy - 130*s, cx + 145*s, cy + 120*s], c_fur, c_fur_shadow)

    d.ellipse([cx - 50*s, cy - 140*s, cx - 10*s, cy - 100*s], fill=c_flower)
    d.ellipse([cx - 35*s, cy - 125*s, cx - 25*s, cy - 115*s], fill=(250, 204, 21, 255))

    d.ellipse([cx - 120*s, cy + 5*s, cx - 70*s, cy + 45*s], fill=c_cheeks)
    d.ellipse([cx + 70*s, cy + 5*s, cx + 120*s, cy + 45*s], fill=c_cheeks)

    d.ellipse([cx - 18*s, cy + 5*s, cx + 18*s, cy + 30*s], fill=(244, 63, 94, 255))

    if asking:
        d.ellipse([cx - 80*s, cy - 55*s, cx - 30*s, cy - 5*s], fill=(30, 41, 59, 255))
        d.ellipse([cx - 70*s, cy - 45*s, cx - 50*s, cy - 20*s], fill=(255, 255, 255, 255))
        d.ellipse([cx + 30*s, cy - 55*s, cx + 80*s, cy - 5*s], fill=(30, 41, 59, 255))
        d.ellipse([cx + 40*s, cy - 45*s, cx + 60*s, cy - 20*s], fill=(255, 255, 255, 255))
        d.line([(cx - 60*s, cy + 25*s), (cx - 110*s, cy + 15*s)], fill=(148, 163, 184, 255), width=3*s)
        d.line([(cx + 60*s, cy + 25*s), (cx + 110*s, cy + 15*s)], fill=(148, 163, 184, 255), width=3*s)
    else:
        d.arc([cx - 80*s, cy - 45*s, cx - 30*s, cy + 5*s], start=180, end=360, fill=(30, 41, 59, 255), width=10*s)
        d.arc([cx + 30*s, cy - 45*s, cx + 80*s, cy + 5*s], start=180, end=360, fill=(30, 41, 59, 255), width=10*s)
        for sx, sy, rad in [(cx - 160*s, cy - 100*s, 16*s), (cx + 160*s, cy - 100*s, 16*s)]:
            d.ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=(251, 191, 36, 255))

    return _finalize(img, size, s)


def generate_all_mascots(output_dir: Path):
    mascot_dir = output_dir / "mascots"
    mascot_dir.mkdir(parents=True, exist_ok=True)
    render_bear(asking=True).save(mascot_dir / "bear_asking.png", "PNG")
    render_bear(asking=False).save(mascot_dir / "bear_cheering.png", "PNG")
    render_penguin(asking=True).save(mascot_dir / "penguin_asking.png", "PNG")
    render_penguin(asking=False).save(mascot_dir / "penguin_cheering.png", "PNG")
    render_lion(asking=True).save(mascot_dir / "lion_asking.png", "PNG")
    render_lion(asking=False).save(mascot_dir / "lion_cheering.png", "PNG")
    render_bunny(asking=True).save(mascot_dir / "bunny_asking.png", "PNG")
    render_bunny(asking=False).save(mascot_dir / "bunny_cheering.png", "PNG")
    print(f"Successfully generated all 4 mascot characters (8 poses) in {mascot_dir}")


if __name__ == "__main__":
    from backend.app.config import IMAGES_DIR
    generate_all_mascots(IMAGES_DIR)
```

Update `backend/app/main.py:85-120` (full replacement block):

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_generate_mascots.py -v`
Expected: PASS

- [ ] **Step 5: Regenerate the actual asset files and commit**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/python -c "from backend.app.config import IMAGES_DIR; from backend.app.utils.generate_mascots_all import generate_all_mascots; generate_all_mascots(IMAGES_DIR)"`

```bash
git add backend/tests/test_generate_mascots.py backend/app/utils/generate_mascots_all.py backend/app/main.py backend/app/assets/images/mascots/
git commit -m "feat: upgrade mascot art to supersampled gradient rendering and rebrand personas"
```

---

### Task 13: Calm poem-specific dance frames with fallback resolution

**Files:**
- Modify: `backend/app/utils/generate_dance_mascots.py` (full rewrite)
- Modify: `backend/app/services/poem_service.py` (`_get_dance_sprite_paths` method)
- Test: `backend/tests/test_dance_sprite_paths.py`

**Interfaces:**
- Consumes: `ASSETS_DIR` from `backend/app/config.py`.
- Produces: `resolve_dance_sprite_paths(dance_dir: Path, mascot_id: str, prefer_calm: bool = True) -> tuple[Path, Path, Path, Path]` (module-level, in `poem_service.py`); `video_service.py`'s `_get_dance_frames` (trivia pipeline) is left completely untouched and keeps reading only `{mascot_id}_d{1-4}.png`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_dance_sprite_paths.py
from pathlib import Path
from backend.app.services.poem_service import resolve_dance_sprite_paths


def _touch(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"fake-png-bytes")


def test_falls_back_to_energetic_frames_when_no_poem_specific_set_exists(tmp_path):
    for i in range(1, 5):
        _touch(tmp_path / f"bear_d{i}.png")

    result = resolve_dance_sprite_paths(tmp_path, "bear", prefer_calm=True)

    assert result == tuple(tmp_path / f"bear_d{i}.png" for i in range(1, 5))


def test_prefers_poem_specific_frames_when_both_sets_exist(tmp_path):
    for i in range(1, 5):
        _touch(tmp_path / f"bear_d{i}.png")
        _touch(tmp_path / f"bear_poem_d{i}.png")

    result = resolve_dance_sprite_paths(tmp_path, "bear", prefer_calm=True)

    assert result == tuple(tmp_path / f"bear_poem_d{i}.png" for i in range(1, 5))


def test_falls_back_to_bear_when_mascot_has_no_frames_at_all(tmp_path):
    for i in range(1, 5):
        _touch(tmp_path / f"bear_d{i}.png")

    result = resolve_dance_sprite_paths(tmp_path, "unknown_mascot", prefer_calm=True)

    assert result == tuple(tmp_path / f"bear_d{i}.png" for i in range(1, 5))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_dance_sprite_paths.py -v`
Expected: FAIL with `ImportError: cannot import name 'resolve_dance_sprite_paths' from 'backend.app.services.poem_service'`

- [ ] **Step 3: Write minimal implementation**

Add to `backend/app/services/poem_service.py` (module level, above the `PoemService` class):

```python
def resolve_dance_sprite_paths(
    dance_dir: Path, mascot_id: str, prefer_calm: bool = True
) -> tuple[Path, Path, Path, Path]:
    """Resolve the 4 dance-cycle sprite paths for a mascot.

    Poems prefer the calmer `{mascot_id}_poem_d{1-4}.png` frame set when it
    exists, falling back to the shared energetic `{mascot_id}_d{1-4}.png`
    set (also used by the trivia pipeline) for backward compatibility, and
    finally to the "bear" sprite set if even the energetic mascot-specific
    frames are missing.
    """
    if prefer_calm:
        calm = tuple(dance_dir / f"{mascot_id}_poem_d{i}.png" for i in range(1, 5))
        if calm[0].is_file():
            return calm
    energetic = tuple(dance_dir / f"{mascot_id}_d{i}.png" for i in range(1, 5))
    if energetic[0].is_file():
        return energetic
    return tuple(dance_dir / f"bear_d{i}.png" for i in range(1, 5))
```

Replace the existing method body:

```python
    def _get_dance_sprite_paths(self, mascot_id: str) -> tuple[Path, Path, Path, Path]:
        dance_dir = ASSETS_DIR / "images" / "mascots_dance"
        return resolve_dance_sprite_paths(dance_dir, mascot_id, prefer_calm=True)
```

Now rewrite `backend/app/utils/generate_dance_mascots.py` in full to produce both the energetic (trivia, unchanged filenames/geometry) and calm (poem, gentler motion range) frame sets. Every pose function takes an `amplitude: float = 1.0` multiplier applied only to the offset of whichever shape represents motion range in that pose (arms/paws, sparkle/note positions) — `amplitude=1.0` reproduces the exact original energetic geometry pixel-for-pixel; `amplitude=0.4` is the gentler poem variant. Torso/head/face shapes are never scaled by amplitude — only the motion-bearing extremities and decorative accents move closer to the body:

```python
import math
from pathlib import Path
from PIL import Image, ImageDraw
from backend.app.config import ASSETS_DIR

CANVAS_SIZE = (512, 512)
POEM_AMPLITUDE = 0.4


def draw_musical_notes(d: ImageDraw.ImageDraw, x: int, y: int, color: tuple):
    """Draws cute floating musical notes."""
    d.ellipse([x - 12, y - 10, x + 6, y + 6], fill=color)
    d.line([(x + 4, y), (x + 4, y - 35)], fill=color, width=4)
    d.line([(x + 4, y - 35), (x + 22, y - 30)], fill=color, width=5)


def _draw_pose_1_step_left(fur: tuple, inner: tuple, accent: tuple, amplitude: float = 1.0) -> Image.Image:
    """Pose 1: Step Left & Sing. Body/head fixed; left/right paw and the
    musical note displace from their body/nose anchor scaled by amplitude."""
    img = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body_cx, body_cy = 250, 340
    nose_cx, nose_cy = 245, 167

    d.ellipse([140, 210, 360, 470], fill=fur)
    d.ellipse([180, 260, 320, 440], fill=inner)
    d.ellipse([125, 60, 365, 280], fill=fur)
    d.ellipse([175, 140, 315, 255], fill=inner)
    d.arc([190, 130, 235, 165], start=180, end=360, fill=(30, 41, 59), width=5)
    d.ellipse([270, 135, 290, 155], fill=(30, 41, 59))
    d.ellipse([275, 138, 283, 146], fill=(255, 255, 255))
    d.ellipse([225, 180, 265, 225], fill=(225, 29, 72))
    d.ellipse([235, 195, 255, 215], fill=(255, 182, 193))
    d.ellipse([235, 160, 255, 175], fill=(30, 41, 59))

    left_cx, left_cy = body_cx + (-127.5) * amplitude, body_cy + (-122.5) * amplitude
    d.ellipse([left_cx - 37.5, left_cy - 37.5, left_cx + 37.5, left_cy + 37.5], fill=fur)
    right_cx, right_cy = body_cx + 132.5 * amplitude, body_cy + (-2.5) * amplitude
    d.ellipse([right_cx - 37.5, right_cy - 37.5, right_cx + 37.5, right_cy + 37.5], fill=fur)

    note_x, note_y = nose_cx + (-165) * amplitude, nose_cy + (-17) * amplitude
    draw_musical_notes(d, int(note_x), int(note_y), accent)

    return img


def _draw_pose_2_head_high(fur: tuple, inner: tuple, accent: tuple, amplitude: float = 1.0) -> Image.Image:
    """Pose 2: Big Singing Mouth Open & Head High. Both paws raised and the
    two musical notes displace from a nose-anchor point scaled by amplitude."""
    img = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body_cx, body_cy = 256, 330
    nose_cx, nose_cy = 255, 162.5

    d.ellipse([146, 200, 366, 460], fill=fur)
    d.ellipse([186, 250, 326, 430], fill=inner)
    d.ellipse([136, 50, 376, 270], fill=fur)
    d.ellipse([186, 130, 326, 245], fill=inner)
    d.arc([190, 125, 235, 160], start=180, end=360, fill=(30, 41, 59), width=6)
    d.arc([275, 125, 320, 160], start=180, end=360, fill=(30, 41, 59), width=6)
    d.ellipse([215, 170, 295, 235], fill=(225, 29, 72))
    d.ellipse([230, 195, 280, 230], fill=(255, 182, 193))
    d.ellipse([245, 155, 265, 170], fill=(30, 41, 59))

    left_cx, left_cy = body_cx + (-138.5) * amplitude, body_cy + (-112.5) * amplitude
    d.ellipse([left_cx - 37.5, left_cy - 37.5, left_cx + 37.5, left_cy + 37.5], fill=fur)
    right_cx, right_cy = body_cx + 136.5 * amplitude, body_cy + (-112.5) * amplitude
    d.ellipse([right_cx - 37.5, right_cy - 37.5, right_cx + 37.5, right_cy + 37.5], fill=fur)

    note1_x, note1_y = nose_cx + (-175) * amplitude, nose_cy + (-32.5) * amplitude
    note2_x, note2_y = nose_cx + 145 * amplitude, nose_cy + (-32.5) * amplitude
    draw_musical_notes(d, int(note1_x), int(note1_y), accent)
    draw_musical_notes(d, int(note2_x), int(note2_y), (250, 204, 21))

    return img


def _draw_pose_3_step_right(fur: tuple, inner: tuple, accent: tuple, amplitude: float = 1.0) -> Image.Image:
    """Pose 3: Step Right & Sing (mirror of Pose 1)."""
    img = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body_cx, body_cy = 260, 340
    nose_cx, nose_cy = 265, 167.5

    d.ellipse([150, 210, 370, 470], fill=fur)
    d.ellipse([190, 260, 330, 440], fill=inner)
    d.ellipse([145, 60, 385, 280], fill=fur)
    d.ellipse([195, 140, 335, 255], fill=inner)
    d.ellipse([220, 135, 240, 155], fill=(30, 41, 59))
    d.ellipse([225, 138, 233, 146], fill=(255, 255, 255))
    d.arc([275, 130, 320, 165], start=180, end=360, fill=(30, 41, 59), width=5)
    d.ellipse([245, 180, 285, 225], fill=(225, 29, 72))
    d.ellipse([255, 195, 275, 215], fill=(255, 182, 193))
    d.ellipse([255, 160, 275, 175], fill=(30, 41, 59))

    left_cx, left_cy = body_cx + (-132.5) * amplitude, body_cy + (-2.5) * amplitude
    d.ellipse([left_cx - 37.5, left_cy - 37.5, left_cx + 37.5, left_cy + 37.5], fill=fur)
    right_cx, right_cy = body_cx + 127.5 * amplitude, body_cy + (-122.5) * amplitude
    d.ellipse([right_cx - 37.5, right_cy - 37.5, right_cx + 37.5, right_cy + 37.5], fill=fur)

    note_x, note_y = nose_cx + 145 * amplitude, nose_cy + (-27.5) * amplitude
    draw_musical_notes(d, int(note_x), int(note_y), accent)

    return img


def _draw_pose_4_airborne_jump(fur: tuple, inner: tuple, accent: tuple, amplitude: float = 1.0) -> Image.Image:
    """Pose 4: Airborne Jump with Party Sparkles. Both arms and the 3 confetti
    starbursts displace from body/head anchors scaled by amplitude."""
    img = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body_cx, body_cy = 256, 300
    head_cx, head_cy = 256, 130

    d.ellipse([146, 170, 366, 430], fill=fur)
    d.ellipse([186, 220, 326, 400], fill=inner)
    d.ellipse([136, 20, 376, 240], fill=fur)
    d.ellipse([186, 100, 326, 215], fill=inner)
    d.ellipse([195, 85, 235, 125], fill=(30, 41, 59))
    d.ellipse([202, 90, 214, 102], fill=(255, 255, 255))
    d.ellipse([275, 85, 315, 125], fill=(30, 41, 59))
    d.ellipse([282, 90, 294, 102], fill=(255, 255, 255))
    d.ellipse([215, 140, 295, 205], fill=(225, 29, 72))
    d.ellipse([230, 165, 280, 200], fill=(255, 182, 193))
    d.ellipse([245, 125, 265, 140], fill=(30, 41, 59))

    left_cx, left_cy = body_cx + (-156) * amplitude, body_cy + (-130) * amplitude
    d.ellipse([left_cx - 40, left_cy - 40, left_cx + 40, left_cy + 40], fill=fur)
    right_cx, right_cy = body_cx + 154 * amplitude, body_cy + (-130) * amplitude
    d.ellipse([right_cx - 40, right_cy - 40, right_cx + 40, right_cy + 40], fill=fur)

    star_offsets = [(-156, -50), (154, -50), (0, -100)]
    for dx, dy in star_offsets:
        star_x, star_y = head_cx + dx * amplitude, head_cy + dy * amplitude
        d.ellipse([star_x - 12, star_y - 12, star_x + 12, star_y + 12], fill=(250, 204, 21))
        d.ellipse([star_x - 5, star_y - 5, star_x + 5, star_y + 5], fill=(255, 255, 255))

    return img


def generate_mascot_dance_frames(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    mascots = [
        {"id": "bear", "fur": (194, 112, 58), "inner": (234, 178, 134), "accent": (239, 68, 68)},
        {"id": "penguin", "fur": (30, 41, 59), "inner": (248, 250, 252), "accent": (56, 189, 248)},
        {"id": "lion", "fur": (234, 150, 40), "inner": (254, 215, 120), "accent": (16, 185, 129)},
        {"id": "bunny", "fur": (241, 245, 249), "inner": (251, 207, 232), "accent": (168, 85, 247)},
    ]

    pose_fns = [_draw_pose_1_step_left, _draw_pose_2_head_high, _draw_pose_3_step_right, _draw_pose_4_airborne_jump]

    for m in mascots:
        mid, fur, inner, accent = m["id"], m["fur"], m["inner"], m["accent"]

        for i, pose_fn in enumerate(pose_fns, start=1):
            pose_fn(fur, inner, accent, amplitude=1.0).save(output_dir / f"{mid}_d{i}.png", "PNG")
            pose_fn(fur, inner, accent, amplitude=POEM_AMPLITUDE).save(output_dir / f"{mid}_poem_d{i}.png", "PNG")

    print(f"Generated 16 energetic + 16 calm mascot dance/singing frames in {output_dir}")


if __name__ == "__main__":
    generate_mascot_dance_frames(ASSETS_DIR / "images" / "mascots_dance")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_dance_sprite_paths.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Regenerate the actual asset files and commit**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/python -c "from backend.app.config import ASSETS_DIR; from backend.app.utils.generate_dance_mascots import generate_mascot_dance_frames; generate_mascot_dance_frames(ASSETS_DIR / 'images' / 'mascots_dance')"`

```bash
git add backend/tests/test_dance_sprite_paths.py backend/app/utils/generate_dance_mascots.py backend/app/services/poem_service.py backend/app/assets/images/mascots_dance/
git commit -m "feat: add calmer poem-specific dance frames with fallback resolution"
```

---

### Task 14: Richer SFX synthesis — bell overtone, attack ramp, low-passed thump

**Files:**
- Modify: `backend/app/utils/generate_sfx.py`
- Test: `backend/tests/test_generate_sfx.py`

**Interfaces:**
- Consumes: existing `write_wav(file_path: Path, samples: list[tuple[float, float]], sample_rate: int = 44100)` (unchanged, reused as-is).
- Produces: `_note_envelope(t: float, decay_rate: float, attack_time: float = 0.008) -> float` — a pure function usable without writing a WAV file; `generate_celebration_chime(output_path: Path)` and `generate_impact_hit(output_path: Path)` keep their existing signatures.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_generate_sfx.py
import wave
from backend.app.utils.generate_sfx import (
    generate_celebration_chime,
    generate_impact_hit,
    _note_envelope,
)


def test_note_envelope_ramps_up_during_attack():
    assert _note_envelope(0.0, decay_rate=2.0) < _note_envelope(0.004, decay_rate=2.0)


def test_note_envelope_reaches_full_amplitude_after_attack():
    assert _note_envelope(0.008, decay_rate=0.0) == 1.0


def test_generate_celebration_chime_writes_nonempty_stereo_wav(tmp_path):
    out = tmp_path / "chime.wav"
    generate_celebration_chime(out)
    assert out.exists()
    assert out.stat().st_size > 0
    with wave.open(str(out), "rb") as wf:
        assert wf.getnchannels() == 2
        assert wf.getnframes() > 0


def test_generate_impact_hit_writes_nonempty_wav(tmp_path):
    out = tmp_path / "hit.wav"
    generate_impact_hit(out)
    assert out.exists()
    assert out.stat().st_size > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_generate_sfx.py -v`
Expected: FAIL with `ImportError: cannot import name '_note_envelope' from 'backend.app.utils.generate_sfx'`

- [ ] **Step 3: Write minimal implementation**

Replace `generate_celebration_chime` and `generate_impact_hit` in `backend/app/utils/generate_sfx.py` (the `write_wav`, `generate_tone`, `generate_tick`, and other functions stay as-is):

```python
def _note_envelope(t: float, decay_rate: float, attack_time: float = 0.008) -> float:
    """Exponential-decay envelope with a short linear attack ramp so notes
    don't click on at t=0. `decay_rate` controls how fast the note fades;
    `attack_time` is the ramp-up duration in seconds (default 8ms)."""
    attack = min(1.0, t / attack_time) if attack_time > 0 else 1.0
    return attack * math.exp(-decay_rate * t)


def generate_celebration_chime(output_path: Path):
    sr = 44100
    duration = 2.0
    total_samples = int(duration * sr)
    track = [(0.0, 0.0)] * total_samples
    freqs = [523.25, 659.25, 783.99, 1046.50]  # C5, E5, G5, C6
    for f in freqs:
        for detune in [0.0, 3.0]:
            for i in range(total_samples):
                t = i / sr
                env = _note_envelope(t, decay_rate=2.0)
                val = math.sin(2.0 * math.pi * (f + detune) * t) * env * 0.1
                # Bell-like overtone at 2x the fundamental: quieter, decays faster.
                overtone_env = _note_envelope(t, decay_rate=4.0)
                overtone = math.sin(2.0 * math.pi * (f + detune) * 2.0 * t) * overtone_env * 0.1 * 0.4
                val += overtone
                L, R = track[i]
                if detune > 0:
                    track[i] = (L + val * 1.2, R + val * 0.8)
                else:
                    track[i] = (L + val * 0.8, R + val * 1.2)
    for i in range(total_samples):
        t = i / sr
        env = _note_envelope(t, decay_rate=3.0)
        phase = 2.0 * math.pi * (6000.0 * t - 750.0 * t * t)
        val = math.sin(phase) * env * 0.05
        L, R = track[i]
        sparkle_pan = math.sin(2.0 * math.pi * 10.0 * t)
        track[i] = (L + val * (1.0 - sparkle_pan), R + val * (1.0 + sparkle_pan))
    write_wav(output_path, track, sr)


def generate_impact_hit(output_path: Path):
    sr = 44100
    duration = 0.15
    total_samples = int(duration * sr)
    track = [(0.0, 0.0)] * total_samples
    smoothed_noise = 0.0
    for i in range(total_samples):
        t = i / sr
        env_sine = math.exp(-15.0 * t)
        sine_val = math.sin(2.0 * math.pi * 80.0 * t) * env_sine * 0.8
        env_noise = math.exp(-30.0 * t)
        raw_noise = random.uniform(-1.0, 1.0) * env_noise * 0.5
        # One-pole low-pass on the noise layer for a punchier, less harsh
        # "thump" instead of raw white-noise hiss.
        smoothed_noise = 0.7 * smoothed_noise + 0.3 * raw_noise
        val = sine_val + smoothed_noise
        track[i] = (val, val)
    write_wav(output_path, track, sr)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_generate_sfx.py -v`
Expected: PASS

- [ ] **Step 5: Regenerate the cached SFX assets and commit**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && rm -f backend/app/assets/audio/celebration_chime.wav backend/app/assets/audio/impact_hit.wav && venv/bin/python -c "from backend.app.config import AUDIO_DIR; from backend.app.utils.generate_sfx import generate_all_sfx; generate_all_sfx(AUDIO_DIR)"`

```bash
git add backend/tests/test_generate_sfx.py backend/app/utils/generate_sfx.py backend/app/assets/audio/celebration_chime.wav backend/app/assets/audio/impact_hit.wav
git commit -m "feat: add bell overtone, attack ramp, and low-passed thump to SFX synthesis"
```

---

### Task 15: ElevenLabs TTS provider

**Files:**
- Create: `backend/app/services/tts/elevenlabs_tts_service.py`
- Modify: `backend/app/services/tts/tts_manager.py`
- Test: `backend/tests/test_elevenlabs_tts.py`

**Interfaces:**
- Consumes: `BaseTTSProvider` abstract base (unchanged); `probe_media_file`/`get_ffmpeg_binary` from `backend/app/utils/ffmpeg_check.py`; `settings.elevenlabs_api_key` from `backend/app/config.py`.
- Produces: `ElevenLabsTTSProvider` class registered in `tts_manager.providers["elevenlabs"]` — `tts_manager.get_provider("elevenlabs")` now returns a real instance instead of silently falling back to `EdgeTTSProvider`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_elevenlabs_tts.py
import pytest
from backend.app.services.tts.elevenlabs_tts_service import ElevenLabsTTSProvider
from backend.app.services.tts.tts_manager import tts_manager


@pytest.mark.anyio
async def test_synthesize_without_api_key_raises_value_error(tmp_path):
    provider = ElevenLabsTTSProvider()
    with pytest.raises(ValueError, match="ElevenLabs API key is required"):
        await provider.synthesize(
            text="hello", output_path=tmp_path / "out.wav", voice="21m00Tcm4TlvDq8ikWAM", api_key="",
        )


def test_tts_manager_resolves_elevenlabs_to_real_provider():
    provider = tts_manager.get_provider("elevenlabs")
    assert isinstance(provider, ElevenLabsTTSProvider)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_elevenlabs_tts.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.app.services.tts.elevenlabs_tts_service'` — and even after stubbing the module, `test_tts_manager_resolves_elevenlabs_to_real_provider` fails today since `tts_manager.providers` has no `"elevenlabs"` key, so `get_provider("elevenlabs")` currently returns `self.providers["edge"]` (an `EdgeTTSProvider`).

- [ ] **Step 3: Write minimal implementation**

Create `backend/app/services/tts/elevenlabs_tts_service.py`:

```python
import httpx
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from backend.app.services.tts.base import BaseTTSProvider
from backend.app.utils.ffmpeg_check import probe_media_file, get_ffmpeg_binary


class ElevenLabsTTSProvider(BaseTTSProvider):
    AVAILABLE_VOICES = [
        {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel (Calm Narrator)", "gender": "Female", "locale": "en-US", "tags": ["calm", "narrator"]},
        {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi (Confident & Strong)", "gender": "Female", "locale": "en-US", "tags": ["confident", "strong"]},
        {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella (Soft & Friendly)", "gender": "Female", "locale": "en-US", "tags": ["soft", "friendly"]},
        {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam (Deep Male Narrator)", "gender": "Male", "locale": "en-US", "tags": ["deep", "narrator"]},
    ]

    async def synthesize(
        self, text: str, output_path: Path, voice: str = "21m00Tcm4TlvDq8ikWAM", rate: str = "+0%", pitch: str = "+0Hz", api_key: str = "",
    ) -> float:
        if not api_key:
            raise ValueError("ElevenLabs API key is required for ElevenLabs TTS provider.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_mp3 = output_path.with_suffix(".temp.mp3")
        voice_id = voice if voice in [v["id"] for v in self.AVAILABLE_VOICES] else "21m00Tcm4TlvDq8ikWAM"
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"ElevenLabs TTS API error ({resp.status_code}): {resp.text}")
            with open(temp_mp3, "wb") as f:
                f.write(resp.content)
        ffmpeg_bin = get_ffmpeg_binary()
        cmd = [ffmpeg_bin, "-y", "-i", str(temp_mp3), "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(output_path)]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0 and temp_mp3.exists():
            temp_mp3.rename(output_path)
        elif temp_mp3.exists():
            temp_mp3.unlink()
        probe = probe_media_file(output_path)
        return max(0.2, probe.get("duration", 0.0))

    def list_voices(self) -> List[Dict[str, Any]]:
        return self.AVAILABLE_VOICES
```

Modify `backend/app/services/tts/tts_manager.py` — add the import and register the provider:

```python
from backend.app.services.tts.elevenlabs_tts_service import ElevenLabsTTSProvider
```

```python
class TTSManager:
    def __init__(self):
        self.providers: Dict[str, BaseTTSProvider] = {
            "edge": EdgeTTSProvider(),
            "openai": OpenAITTSProvider(),
            "elevenlabs": ElevenLabsTTSProvider(),
        }
```

(`get_provider`, `list_all_voices`, and `synthesize` are unchanged — `synthesize` already branches on `provider_name == "elevenlabs"` to pull `settings.elevenlabs_api_key`; registering the real class is the only change needed, since `ElevenLabsTTSProvider.synthesize` now raises `ValueError` on an empty key exactly like `OpenAITTSProvider` does, instead of silently rendering with Edge's voice.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_elevenlabs_tts.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_elevenlabs_tts.py backend/app/services/tts/elevenlabs_tts_service.py backend/app/services/tts/tts_manager.py
git commit -m "feat: add ElevenLabs TTS provider and register it in TTSManager"
```

---

### Task 16: Draft/final render quality tiers

**Files:**
- Modify: `backend/app/config.py` (append `DRAFT_QUALITY`/`FINAL_QUALITY`)
- Modify: `backend/app/services/video_service.py` (`render_short_video` signature + `cmd` construction)
- Modify: `backend/app/services/poem_service.py` (`render_poem_short` signature + `cmd` construction)
- Modify: `backend/app/main.py` (`/api/preview` at lines 290-300, `/api/poems/preview` at lines 477-483)
- Modify: `backend/app/services/job_manager.py` (`process_single`/`retry_single` render calls, third modification of this file)
- Modify: `backend/app/services/poem_job_manager.py:209-215` (the single `poem_service.render_poem_short(...)` call site inside `process_single`)
- Test: `backend/tests/test_render_quality.py`

**Interfaces:**
- Consumes: `AppSettings`/`settings` from `config.py`; the existing `cmd` list construction inside `render_short_video`/`render_poem_short` that currently hardcodes `"-preset", "fast"` and reads `config.video_bitrate`.
- Produces: `DRAFT_QUALITY: dict` and `FINAL_QUALITY: dict` module-level constants in `config.py`; `render_short_video(..., quality_tier: str = "final")` and `render_poem_short(..., quality_tier: str = "final")`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_render_quality.py
import pytest
from unittest.mock import patch, MagicMock

from backend.app.config import DRAFT_QUALITY, FINAL_QUALITY, ASSETS_DIR
from backend.app.services.video_service import VideoService
from backend.app.models.schemas import VideoRenderConfig


def test_draft_and_final_quality_profiles_are_distinct():
    assert DRAFT_QUALITY["preset"] != FINAL_QUALITY["preset"]
    assert DRAFT_QUALITY["video_bitrate"] != FINAL_QUALITY["video_bitrate"]


@pytest.mark.anyio
async def test_render_short_video_draft_tier_uses_veryfast_preset(tmp_path):
    fake_result = MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = ""
    fake_result.stderr = ""

    fake_timing = {
        "t_countdown_start": 1.0,
        "t_countdown_end": 4.0,
        "t_answer_start": 4.0,
        "total_duration": 8.0,
        "countdown_duration": 3.0,
    }

    with patch("backend.app.services.video_service.subprocess.run", return_value=fake_result) as mock_run:
        service = VideoService()
        await service.render_short_video(
            bg_video_path=ASSETS_DIR / "backgrounds" / "candy_clouds.mp4",
            master_audio_path=tmp_path / "master_audio.wav",
            timing_info=fake_timing,
            question_text="What animal says Moo?",
            answer_text="A Cow",
            output_mp4_path=tmp_path / "out.mp4",
            work_dir=tmp_path / "work",
            config=VideoRenderConfig(),
            options=None,
            correct_index=None,
            quality_tier="draft",
        )

    called_cmd = mock_run.call_args[0][0]
    assert "veryfast" in called_cmd
    assert "medium" not in called_cmd
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_render_quality.py -v`
Expected: FAIL with `ImportError: cannot import name 'DRAFT_QUALITY' from 'backend.app.config'`, and separately `TypeError: render_short_video() got an unexpected keyword argument 'quality_tier'` once that import is stubbed.

- [ ] **Step 3: Write minimal implementation**

Append to the end of `backend/app/config.py` (after `settings = AppSettings()`):

```python
DRAFT_QUALITY = {"preset": "veryfast", "video_bitrate": "2500k"}
FINAL_QUALITY = {"preset": "medium", "video_bitrate": "6000k"}
```

In `backend/app/services/video_service.py`, add `quality_tier: str = "final"` to `render_short_video`'s signature:

```python
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
        quality_tier: str = "final",
    ) -> Path:
```

Right before the `cmd = [...]` list is built, add:

```python
        from backend.app.config import DRAFT_QUALITY, FINAL_QUALITY
        profile = DRAFT_QUALITY if quality_tier == "draft" else FINAL_QUALITY
```

Then in the `cmd` list, replace `"-preset", "fast",` with `"-preset", profile["preset"],` and replace `"-b:v", config.video_bitrate,` with `"-b:v", profile["video_bitrate"],` (the profile becomes the single source of truth for bitrate/preset — `config.video_bitrate` is no longer read here).

Apply the identical change to `render_poem_short` in `backend/app/services/poem_service.py`: add `quality_tier: str = "final"` to its signature, add the same `profile = DRAFT_QUALITY if quality_tier == "draft" else FINAL_QUALITY` line before its `cmd` construction, and replace its own `"-preset", "fast"` and `"-b:v", config.video_bitrate` entries with `"-preset", profile["preset"]` and `"-b:v", profile["video_bitrate"]`.

In `backend/app/main.py`'s `/api/preview` endpoint, add `quality_tier="draft"` to the `video_service.render_short_video(...)` call (alongside the existing `options=options,` kwarg). In `/api/poems/preview`, add `quality_tier="draft"` to the `poem_service.render_poem_short(...)` call.

In `backend/app/services/job_manager.py`, add `quality_tier="final"` to both `video_service.render_short_video(...)` calls (`process_single` and `retry_single`) — the same two call sites Task 5 already touched.

In `backend/app/services/poem_job_manager.py`, inside `process_single` (the file's only render call site), add `quality_tier="final"` to the `poem_service.render_poem_short(...)` call:

```python
                    await poem_service.render_poem_short(
                        poem=poem,
                        bg_video_path=item_bg_video,
                        output_mp4_path=output_mp4,
                        work_dir=item_work_dir,
                        config=item_config,
                        quality_tier="final",
                    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/test_render_quality.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Run the full backend test suite**

Run: `cd /Users/manhashed/work/ai-shorts-generation/trivia && venv/bin/pytest backend/tests/ -v`
Expected: PASS (all tests green, including every test file added across Tasks 1-16)

- [ ] **Step 6: Commit**

```bash
git add backend/tests/test_render_quality.py backend/app/config.py backend/app/services/video_service.py backend/app/services/poem_service.py backend/app/main.py backend/app/services/job_manager.py backend/app/services/poem_job_manager.py
git commit -m "feat: add draft/final render quality tiers for preview vs final output"
```

---

### Task 17: Frontend — surface ElevenLabs as a voice provider, gated on a key being entered

**Files:**
- Modify: `frontend/src/components/SettingsDrawer.tsx:29-30` (voice list extraction), `:111-142` (voice `<select>`), `:387-412` (API key section)

**Interfaces:**
- Consumes: `voices['elevenlabs']` (already returned by the backend's `list_all_voices()` once Task 15 registers the provider — `TTSManager.list_all_voices()` iterates `self.providers`, so `elevenlabs` appears automatically with no backend endpoint change needed); `config.elevenlabs_api_key` (already exists on `VideoRenderConfig` per `schemas.py`).
- Produces: nothing consumed by later tasks — last task in the plan.

This is a pure-UI change; verified manually via the dev server, matching Task 11's approach.

- [ ] **Step 1: Extract the ElevenLabs voice list**

Replace:

```tsx
  const edgeVoices = voices['edge'] || [];
  const openaiVoices = voices['openai'] || [];
```

with:

```tsx
  const edgeVoices = voices['edge'] || [];
  const openaiVoices = voices['openai'] || [];
  const elevenlabsVoices = voices['elevenlabs'] || [];
  const hasElevenlabsKey = Boolean(config.elevenlabs_api_key && config.elevenlabs_api_key.trim().length > 0);
```

- [ ] **Step 2: Add a gated ElevenLabs optgroup to the voice select**

Replace:

```tsx
              {openaiVoices.length > 0 && (
                <optgroup label="OpenAI TTS (Requires API Key)">
                  {openaiVoices.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name}
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
```

with:

```tsx
              {openaiVoices.length > 0 && (
                <optgroup label="OpenAI TTS (Requires API Key)">
                  {openaiVoices.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name}
                    </option>
                  ))}
                </optgroup>
              )}
              {hasElevenlabsKey && elevenlabsVoices.length > 0 && (
                <optgroup label="ElevenLabs (Premium — Key Entered)">
                  {elevenlabsVoices.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name}
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
            {!hasElevenlabsKey && (
              <p className="text-[10px] text-slate-500 pt-0.5">
                Enter an ElevenLabs API key below to unlock premium voices.
              </p>
            )}
```

- [ ] **Step 3: Add an ElevenLabs key input alongside the existing OpenAI key input**

Replace:

```tsx
            {showApiKeyInput && (
              <div className="mt-2 p-3 bg-slate-900 rounded-xl border border-slate-700/60 space-y-2">
                <p className="text-[11px] text-slate-400">
                  By default, <strong>Edge-TTS</strong> runs without any API key or subscription. If you prefer OpenAI TTS:
                </p>
                <input
                  type="password"
                  placeholder="sk-..."
                  value={config.openai_api_key || ''}
                  onChange={(e) => onChange({ openai_api_key: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-400"
                />
              </div>
            )}
```

with:

```tsx
            {showApiKeyInput && (
              <div className="mt-2 p-3 bg-slate-900 rounded-xl border border-slate-700/60 space-y-3">
                <div className="space-y-2">
                  <p className="text-[11px] text-slate-400">
                    By default, <strong>Edge-TTS</strong> runs without any API key or subscription. If you prefer OpenAI TTS:
                  </p>
                  <input
                    type="password"
                    placeholder="sk-..."
                    value={config.openai_api_key || ''}
                    onChange={(e) => onChange({ openai_api_key: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-400"
                  />
                </div>
                <div className="space-y-2">
                  <p className="text-[11px] text-slate-400">
                    For premium ElevenLabs voices, enter your own API key:
                  </p>
                  <input
                    type="password"
                    placeholder="el-..."
                    value={config.elevenlabs_api_key || ''}
                    onChange={(e) => onChange({ elevenlabs_api_key: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-400"
                  />
                </div>
              </div>
            )}
```

- [ ] **Step 4: Manual verification**

Run:
```bash
cd /Users/manhashed/work/ai-shorts-generation/trivia/frontend && npm run dev
```

Confirm: with no ElevenLabs key entered, the voice dropdown shows only Edge/OpenAI groups plus the "enter a key to unlock" hint; entering any non-empty key reveals the ElevenLabs optgroup with the 4 voices from Task 15's `AVAILABLE_VOICES`; selecting one and previewing sends `tts_provider: "elevenlabs"` with the chosen voice id.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/SettingsDrawer.tsx
git commit -m "feat: gate ElevenLabs voice selection on an API key being entered"
```

---

## Self-Review Notes

- **Spec coverage:** every numbered section of the design spec maps to at least one task (correctness → 1-5, mascot identity → 12, animation engine → 6-9, poem parity → 9-10, audio/voice → 4, 14-15, render tiers → 16, frontend → 3, 11, 17). Two spec bullets were deliberately descoped rather than forced into a task: (1) the "cheap parallax: blurred background layer behind a crisp foreground card" bullet doesn't have a natural attachment point in the current composition — there is no distinct foreground *layer* separate from the background (the "cards" are text/UI drawtext overlays, not a duplicated video layer), so implementing it would mean restructuring the whole composite rather than a bite-sized addition; (2) "curate the 2-3 best-fit Edge-TTS voices per pipeline as defaults" is a content/config tweak (which existing voice IDs get marked recommended) with no architectural weight — worth doing but not warranting its own task.
- **Placeholder scan:** the two spots the drafting agents initially left as "apply this pattern, exact coordinates unavailable" (mascot art for penguin/lion/bunny in Task 12, and dance-frame poses d2-d4 in Task 13) were replaced above with fully concrete code grounded in the actual current source, so no task in this plan relies on an implementer inventing geometry.
- **Type consistency:** `resolved_answer` (Task 1) → `item.resolved_answer` (Task 2) → `correct_index=item.correct_index` (Task 5) is consistent throughout; `vfx_helpers.py`'s function names (`build_cinematic_bg_filter`, `build_overshoot_y_expr`, `build_countdown_tick_pulse`, `build_flash_overlay`, `_build_outro_celebration_filters`) match between their defining task and every later task that imports them; `quality_tier` threading in Task 16 matches across `video_service.py`, `poem_service.py`, `main.py`, `job_manager.py`, and `poem_job_manager.py`.

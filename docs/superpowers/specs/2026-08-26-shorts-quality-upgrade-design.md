# Trivia & Poem Shorts — Quality Upgrade Design

Date: 2026-08-26
Status: Approved by user, pending implementation plan

## Context

The app generates two kinds of 9:16 vertical short videos for kids —
trivia quiz shorts and poem shorts — via a Python/FastAPI backend using
FFmpeg filter graphs, procedurally-generated PIL assets, and Edge-TTS
narration. The README targets ages 3-5; this upgrade retargets ages
5-8 with materially higher animation, graphics, audio, and voice
quality, aimed at maximizing attention/retention on YouTube Shorts,
TikTok, and Instagram Reels.

An initial codebase audit (see prior conversation) found:

- **A live correctness bug**: `TriviaItem.a` (answer text) and
  `TriviaItem.options` are independent strings with no validation that
  the answer matches an option. `question_bank.json` already contains
  a real example of drift (`"a": "A Big Spotted Cow!"` vs
  `"options": ["A Cow", "A Dog", "A Frog"]`).
- Trivia has decent animation bones (Ken Burns zoom, confetti physics,
  sidechain-ducked audio, loudnorm); poems lack zoom/confetti/flash
  entirely.
- Mascots/backgrounds are raw PIL ellipse/polygon primitives —
  functional but visually primitive.
- SFX/BGM are pure sine-wave synthesis — thin-sounding.
- ElevenLabs is wired through config/schema/UI but has no actual
  provider implementation; selecting it silently falls back to Edge-TTS.
- Several config knobs (`karaoke_style`, TTS phrasing variety) are
  exposed in schema/UI but never wired to real behavior.
- A prior patch intended to add contrast/saturation/vignette treatment
  to trivia backgrounds never landed in `video_service.py` (only in
  `poem_service.py`).

## Goals

1. Make it structurally impossible for the displayed/spoken answer to
   diverge from its matching option text.
2. Replace the toddler-era mascot with a fresh visual identity suited
   to ages 5-8, validated with a sample render before mass-producing
   assets.
3. Bring both pipelines (trivia + poem) to a shared, higher animation
   bar: dynamic backgrounds, staggered reveals, punchier countdown,
   celebratory reveal moment.
4. Upgrade audio synthesis quality and finish the voice story (curate
   Edge defaults, implement real ElevenLabs as an optional premium
   tier, remove the silent-fallback failure mode).
5. Add draft vs. final render quality tiers without adding new
   user-facing complexity.
6. Wire the already-exposed-but-dead config knobs (`karaoke_style`,
   TTS phrasing variety) to real behavior instead of leaving them inert.

## Non-goals

- No AI-generated image/video assets in this pass (explicitly deferred
  per user decision — procedural engine only, structured so an asset
  source could be swapped later).
- No change to distribution/upload mechanics (YouTube/TikTok/Reels
  publishing) — output quality only.
- No mobile app / new platform — same FastAPI + React stack.

## Design

### 1. Correctness enforcement

**Schema (`backend/app/models/schemas.py`)**: `TriviaItem` gets a
model validator that checks the answer (however represented) matches
one of `options` after trim/case-fold normalization. Mismatches raise
a clear validation error at ingestion time (reusing/extending
`validator.py`'s existing sanitization pass) rather than silently
rendering bad data. Existing bad entries in
`backend/app/data/question_bank.json` get fixed as part of this work.

**Render-time (`backend/app/services/video_service.py`)**: the answer
reveal no longer draws a second, independently-authored answer
text/card. It highlights the matching option element that is already
on screen — glow ring, scale-pulse, checkmark badge — timed with the
confetti burst. Because it's the same rendered string object, drift
becomes structurally impossible rather than merely checked-for.

**Audio (`backend/app/services/audio_service.py`)**: reveal narration
uses a template where only the carrier phrase varies (wiring in the
existing-but-unused `_enhance_text_for_speech` variety system from
`edge_tts_service.py`) and the answer noun itself is always the
literal matched option string — never independently rephrased.

### 2. New visual identity

A single adaptable host character (for brand consistency across both
pipelines) with two pose sets: energetic game-show mode for trivia,
calmer storyteller mode for poems. Built as an SVG rig rasterized to
PNG frames (crisper curves/gradients/shading than the current raw PIL
`ImageDraw.ellipse/polygon` art), keeping the pipeline fully procedural
(no per-render API cost) and structured so a future AI-art source could
be substituted without touching compositing code in `video_service.py`
/ `poem_service.py`.

Process: build one candidate design and render a real sample short
early; get sign-off on that sample before propagating the character
across the full pose/animation frame set. This avoids guessing wrong
on subjective visual taste before committing to full asset production.

### 3. Animation engine (unify + upgrade both pipelines)

- Shared "cinematic treatment" helper (contrast/saturation boost +
  vignette + randomized-direction Ken Burns pan/zoom, replacing the
  fixed center-zoom-only `zoompan` expression) applied to both trivia
  (`video_service.py`) and poem (`poem_service.py`) backgrounds. Closes
  the gap where poems currently get none of this.
- Options stagger in with a short per-item delay and an overshoot
  ("back-out") easing curve instead of the current uniform quadratic
  ease-in slide-up.
- Countdown gets a pulsing scale + per-tick color shift + a
  screen-flash on "go," replacing the current static 3-2-1 badge pop-in.
- Poem karaoke timing (`ass_maker.py`) switches from even
  word-duration division to character-count-weighted timing so long
  words hold the highlight longer than short ones.
- Two of the three already-exposed-but-dead `karaoke_style` values
  (`bouncing_star`, `glow_highlight`) get real implementations in
  `ass_maker.py`; the third can remain a documented follow-up if scope
  requires trimming.
- Cheap depth cue: a blurred background layer behind the crisp
  foreground card layer (parallax-style separation).

### 4. Audio & voice

- Keep the existing sidechain-ducking + `loudnorm` mix chain in
  `audio_service.py` (it's already well-engineered) and confirm/extend
  equivalent treatment in the poem pipeline if it's currently thinner.
- Upgrade procedural SFX/chime synthesis in `generate_sfx.py` /
  `generate_bgm_sfx.py` with richer envelopes/harmonics (ADSR shaping,
  layered overtones) instead of raw sine tones, so they read as
  produced sound design rather than test tones.
- Curate the 2-3 best-fit Edge-TTS voices per pipeline as defaults
  (age-appropriate, not toddler-coded) rather than leaving all 9 as
  equally-weighted options.
- Implement a real ElevenLabs provider (`tts/elevenlabs_tts_service.py`)
  as an optional premium tier, gated on a user-supplied API key that's
  already plumbed through config/schema. Remove the silent-fallback
  behavior in `tts_manager.py`: selecting a provider with no key/impl
  should fail with a clear message, not quietly substitute Edge.

### 5. Render quality tiers

Add explicit **draft** (fast preset, current bitrate — used by
`/api/preview`) and **final** (slower encoder preset / higher bitrate —
used by full batch render) profiles in `config.py`. Applied
automatically based on which endpoint is rendering; no new user-facing
toggle.

### 6. Frontend

- Wire the `karaoke_style` selector in `SettingsDrawer.tsx` to actually
  change rendered output (currently cosmetic-only).
- Add a mascot preview thumbnail once the new character is finalized.
- Only surface ElevenLabs as a selectable voice provider once a key is
  entered; otherwise show it disabled with an explanatory tooltip
  instead of a dead dropdown entry.

### Error handling

- Bad trivia data (answer/options mismatch) fails validation at
  ingestion with an actionable message identifying which item and
  which strings didn't match — never silently renders.
- Selecting an unimplemented/unkeyed TTS provider fails clearly at
  request time rather than silently substituting a different voice.

### Testing

- Unit test asserting the schema validator rejects an
  answer/options mismatch and accepts normalized matches
  (case/whitespace differences).
- Fix/regenerate the known-bad entries in `question_bank.json` and add
  a regression test guarding against reintroducing mismatched data.
- A golden sample render (extending the existing
  `test_prototype.py`-style flow) to visually spot-check the new
  mascot, animation timing, and audio mix before wider rollout.
- Existing suite (`test_batch_flow.py`, `test_poem_studio.py`,
  `test_mix_batch.py`, `test_interactive_features.py`,
  `test_api_integration.py`, `test_validator.py`) must continue to pass.

## Execution strategy

Once an implementation plan is written (via the `writing-plans`
skill), work splits into largely independent workstreams suitable for
parallel Sonnet 5 subagents to keep main-thread token usage low:

1. Mascot SVG rig + frame generation (`generate_mascot.py` and friends)
2. `video_service.py` animation upgrades (backgrounds, stagger, reveal,
   countdown)
3. `poem_service.py` parity work + karaoke timing/style
   implementation (`ass_maker.py`)
4. Audio synthesis upgrades (`generate_sfx.py`, `generate_bgm_sfx.py`,
   `audio_service.py` phrasing variety wiring)
5. Schema/validator correctness fix + `question_bank.json` data cleanup
6. ElevenLabs TTS provider implementation + fallback-failure fix
7. Render quality tiers in `config.py`
8. Frontend wiring (karaoke style, mascot preview, ElevenLabs gating)

The mascot sample-render checkpoint (workstream 1) should land and get
sign-off before workstreams that depend on final mascot frames
(2, 3) are considered complete, though they can start against
placeholder frames in parallel.

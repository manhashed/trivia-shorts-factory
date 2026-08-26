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

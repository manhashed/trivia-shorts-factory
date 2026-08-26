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

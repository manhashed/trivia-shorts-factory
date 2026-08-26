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

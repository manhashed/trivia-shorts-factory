from pathlib import Path

from backend.app.services.video_service import video_service


def test_highlight_filters_contain_only_the_correct_option_text():
    font_path = Path("/fake/Fredoka-Bold.ttf")

    filters, new_layer = video_service._build_option_highlight_filters(
        options_layer="with_opt_3",
        opt_display="A)  A Cow",
        curr_opt_y=960,
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
    font_path = Path("/fake/Fredoka-Bold.ttf")

    filters, new_layer = video_service._build_option_highlight_filters(
        options_layer="with_opt_3",
        opt_display="B)  A Dog",
        curr_opt_y=1070,
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

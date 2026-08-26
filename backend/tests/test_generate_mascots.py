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

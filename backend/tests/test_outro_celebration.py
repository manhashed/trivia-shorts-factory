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

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

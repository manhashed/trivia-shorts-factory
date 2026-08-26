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

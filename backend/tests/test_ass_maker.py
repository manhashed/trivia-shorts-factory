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

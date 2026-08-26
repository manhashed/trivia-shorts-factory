from backend.app.services.phrase_variety import build_answer_reveal_phrase, REVEAL_PHRASE_TEMPLATES


def test_exact_answer_always_appears_verbatim():
    exact_answer = "A Big Spotted Cow"
    for _ in range(20):
        phrase = build_answer_reveal_phrase(exact_answer)
        assert exact_answer in phrase


def test_answer_text_is_never_rephrased_or_mutated():
    exact_answer = "A Cow"
    for _ in range(20):
        phrase = build_answer_reveal_phrase(exact_answer)
        assert any(
            phrase == template.format(answer=exact_answer)
            for template in REVEAL_PHRASE_TEMPLATES
        )

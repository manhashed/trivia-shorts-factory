import random

# Shared kid-friendly reveal phrasing. Also imported by
# edge_tts_service._enhance_text_for_speech (style="answer").
REVEAL_PHRASE_TEMPLATES = [
    "The answer is... {answer}!",
    "It's... {answer}! Great job!",
    "Yes! It's {answer}!",
    "That's right, it's {answer}!",
    "Wow, it's {answer}! Did you know that?",
    "You got it! It's {answer}!",
    "Bingo! It's {answer}!",
    "Correct! It is {answer}!",
]


def build_answer_reveal_phrase(exact_answer: str) -> str:
    """
    Selects a random kid-friendly carrier phrase and substitutes the exact
    answer text into it verbatim. The answer text itself is never altered,
    reworded, or re-derived here -- only the surrounding phrasing varies.
    Skip wrapping when the answer already carries reveal language so we do
    not synthesize "The answer is... The answer is 42!".
    """
    lowered = exact_answer.lower()
    if (
        lowered.startswith("the answer")
        or lowered.startswith("it's")
        or lowered.startswith("it is")
    ):
        return exact_answer
    template = random.choice(REVEAL_PHRASE_TEMPLATES)
    return template.format(answer=exact_answer)

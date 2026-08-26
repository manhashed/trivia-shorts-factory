import random

# Reused verbatim from the kid-friendly reveal phrasing already proven in
# backend/app/services/tts/edge_tts_service.py's _enhance_text_for_speech
# (that method is currently dead code -- tts_manager.synthesize() is never
# called with text_style="answer" from audio_service). Centralizing the list
# here lets prepare_quiz_audio vary the carrier phrase on every render.
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
    """
    template = random.choice(REVEAL_PHRASE_TEMPLATES)
    return template.format(answer=exact_answer)

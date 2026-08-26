import pytest
from pydantic import ValidationError

from backend.app.models.schemas import TriviaItem


def test_correct_index_defaults_to_zero_when_options_present():
    item = TriviaItem(q="What animal says Moo?", a="A Big Spotted Cow!", options=["A Cow", "A Dog", "A Frog"])
    assert item.correct_index == 0
    assert item.resolved_answer == "A Cow"


def test_correct_index_explicit_valid_value():
    item = TriviaItem(q="What is 2+2?", a="Four!", options=["3", "4", "5"], correct_index=1)
    assert item.correct_index == 1
    assert item.resolved_answer == "4"


def test_correct_index_out_of_range_raises():
    with pytest.raises(ValidationError):
        TriviaItem(q="What is 2+2?", a="Four!", options=["3", "4", "5"], correct_index=5)


def test_no_options_falls_back_to_a():
    item = TriviaItem(q="What is 2+2?", a="Four!")
    assert item.options is None
    assert item.correct_index is None
    assert item.resolved_answer == "Four!"

import pytest
from backend.app.services.validator import validate_trivia_json, sanitize_text_content

def test_sanitize_text():
    raw = "What's the capital of France?  \t\n"
    assert sanitize_text_content(raw) == "What's the capital of France?"
    
    # Unicode accents & emojis
    unicode_str = "Is México 🇲🇽 in North America?"
    assert "México" in sanitize_text_content(unicode_str)

def test_validate_trivia_json_valid():
    sample_json = """
    [
        {"q": "What animal says 'Moo'?", "a": "A Cow!"},
        {"q": "How many fingers are on one hand?", "a": "Five!"}
    ]
    """
    items, errors = validate_trivia_json(sample_json)
    assert len(errors) == 0
    assert len(items) == 2
    assert items[0].q == "What animal says 'Moo'?"
    assert items[0].a == "A Cow!"

def test_validate_trivia_json_invalid_structure():
    # Not a list
    items, errors = validate_trivia_json('{"q": "Hi", "a": "There"}')
    assert len(items) == 0
    assert len(errors) == 1
    assert "must be an array" in errors[0]["reason"]

def test_validate_trivia_json_missing_fields():
    sample_json = """
    [
        {"q": "Valid question?", "a": "Valid answer"},
        {"q": "Missing answer?"},
        {"a": "Missing question"}
    ]
    """
    items, errors = validate_trivia_json(sample_json)
    assert len(items) == 1
    assert len(errors) == 2
    assert "missing required fields: 'a'" in errors[0]["reason"]
    assert "missing required fields: 'q'" in errors[1]["reason"]

def test_validate_trivia_json_empty_strings():
    sample_json = """
    [
        {"q": "   ", "a": "Valid"}
    ]
    """
    items, errors = validate_trivia_json(sample_json)
    assert len(items) == 0
    assert len(errors) == 1
    assert "empty" in errors[0]["reason"]

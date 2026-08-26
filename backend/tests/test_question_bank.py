import json
import pytest
from pathlib import Path
from backend.app.config import BASE_DIR

def test_question_bank_structure_and_count():
    bank_file = BASE_DIR / "app" / "data" / "question_bank.json"
    assert bank_file.is_file(), "question_bank.json does not exist"

    with open(bank_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    assert isinstance(questions, list), "Question bank root must be a list"
    assert len(questions) >= 100, f"Expected at least 100 questions, got {len(questions)}"

    categories = set()
    for idx, q in enumerate(questions):
        assert "q" in q and len(q["q"].strip()) > 0, f"Question #{idx} is missing 'q'"
        assert "a" in q and len(q["a"].strip()) > 0, f"Question #{idx} is missing 'a'"
        assert "category" in q and len(q["category"].strip()) > 0, f"Question #{idx} is missing 'category'"
        assert "options" in q and isinstance(q["options"], list) and len(q["options"]) >= 2, f"Question #{idx} has invalid options"
        categories.add(q["category"])

    # Ensure 10 core categories
    expected_categories = {
        "Animals & Sounds",
        "Colors & Rainbows",
        "Shapes & Everyday Objects",
        "Numbers & Counting",
        "Fruits & Veggies",
        "Vehicles & Things That Go",
        "Nature & Space",
        "My Body & Health",
        "Friendly Helpers & Jobs",
        "Opposites & Daily Fun",
    }
    assert expected_categories.issubset(categories), f"Missing categories: {expected_categories - categories}"

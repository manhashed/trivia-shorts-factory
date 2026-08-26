import json
import re
import unicodedata
from pathlib import Path
from typing import List, Tuple, Dict, Any
from backend.app.models.schemas import TriviaItem
from backend.app.utils.ffmpeg_check import probe_media_file


def sanitize_text_content(text: str) -> str:
    """
    Normalizes unicode text and removes dangerous control characters 
    while preserving standard punctuation, accents, and emojis.
    """
    if not text:
        return ""
    
    # Normalize unicode to NFC
    normalized = unicodedata.normalize("NFC", text.strip())
    
    # Remove non-printable control characters except standard whitespace
    cleaned = "".join(ch for ch in normalized if ch == "\n" or ch == "\t" or not unicodedata.category(ch).startswith("C"))
    
    # Collapse excess whitespace
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned


def validate_trivia_json(raw_json_str: str) -> Tuple[List[TriviaItem], List[Dict[str, Any]]]:
    """
    Validates a JSON string or file content representing trivia questions and answers.
    Returns (valid_items, errors_list).
    """
    errors: List[Dict[str, Any]] = []
    valid_items: List[TriviaItem] = []

    try:
        data = json.loads(raw_json_str)
    except json.JSONDecodeError as e:
        return [], [{"index": -1, "reason": f"Invalid JSON syntax: {e.msg} at line {e.lineno}, col {e.colno}"}]

    if not isinstance(data, list):
        return [], [{"index": -1, "reason": "Root JSON element must be an array of objects."}]

    if len(data) == 0:
        return [], [{"index": -1, "reason": "JSON array is empty. Please provide at least 1 question."}]

    for idx, raw_item in enumerate(data):
        if not isinstance(raw_item, dict):
            errors.append({"index": idx, "reason": f"Item #{idx + 1} is not a valid JSON object."})
            continue

        if "q" not in raw_item or "a" not in raw_item:
            missing = []
            if "q" not in raw_item:
                missing.append("'q'")
            if "a" not in raw_item:
                missing.append("'a'")
            errors.append({"index": idx, "reason": f"Item #{idx + 1} is missing required fields: {', '.join(missing)}."})
            continue

        q_val = str(raw_item.get("q", ""))
        a_val = str(raw_item.get("a", ""))

        sanitized_q = sanitize_text_content(q_val)
        sanitized_a = sanitize_text_content(a_val)

        if not sanitized_q:
            errors.append({"index": idx, "reason": f"Item #{idx + 1} question ('q') is empty or invalid."})
            continue

        if not sanitized_a:
            errors.append({"index": idx, "reason": f"Item #{idx + 1} answer ('a') is empty or invalid."})
            continue

        item_id = f"item_{idx + 1:03d}"
        category = raw_item.get("category", None)
        raw_options = raw_item.get("options", None)
        options = None
        if isinstance(raw_options, list):
            options = [sanitize_text_content(str(opt)) for opt in raw_options if str(opt).strip()]
            if not options:
                options = None

        valid_items.append(TriviaItem(
            id=item_id,
            q=sanitized_q,
            a=sanitized_a,
            category=category,
            options=options,
        ))

    return valid_items, errors


def validate_background_video(video_path: Path) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Checks that the uploaded background video exists, is a valid video format,
    and can be decoded by FFmpeg.
    """
    if not video_path.is_file():
        return False, f"File does not exist: {video_path.name}", {}

    if video_path.stat().st_size == 0:
        return False, "Uploaded video file is 0 bytes (empty).", {}

    try:
        info = probe_media_file(video_path)
        if not info["has_video"]:
            return False, "File does not contain a valid video stream.", info
        if info["duration"] <= 0.1:
            return False, "Video stream duration is too short or unreadable.", info
        return True, "Valid video file.", info
    except Exception as e:
        return False, f"FFmpeg failed to probe video file: {str(e)}", {}

from typing import List


def format_time(seconds: float) -> str:
    """Format seconds to ASS time format h:mm:ss.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _char_weighted_durations_cs(words: List[str], duration: float) -> List[int]:
    """Split a total duration (in centiseconds) across words weighted by
    character count instead of an even split. Guards against an all-empty
    word list and rounding drift by assigning any leftover centiseconds to
    the last word.
    """
    total_cs = int(duration * 100)
    total_chars = sum(len(w) for w in words) or 1
    durations = [int(total_cs * len(w) / total_chars) for w in words]
    assigned = sum(durations)
    if durations:
        durations[-1] += total_cs - assigned
    return durations


def generate_karaoke_line(text: str, duration: float, style: str = "bouncing_star") -> str:
    """Distribute duration across words (character-count-weighted) and add ASS
    karaoke tags, with optional per-style highlight decoration.
    """
    words = text.split()
    if not words:
        return ""

    durations_cs = _char_weighted_durations_cs(words, duration)

    parts = []
    for word, cs in zip(words, durations_cs):
        if style == "glow_highlight":
            parts.append(f"{{\\k{cs}\\bord14\\3c&H0047E0FD&}}{word}")
        elif style == "bouncing_star":
            parts.append(f"{{\\k{cs}\\t(0,150,\\fscy110)\\t(150,300,\\fscy100)}}{word}")
        else:  # "clean_cards" and any unrecognized style fall back to plain sweep
            parts.append(f"{{\\k{cs}}}{word}")

    return " ".join(parts)


def create_ass_file(lines_timing: List[dict], output_path: str, style: str = "bouncing_star"):
    """
    lines_timing: list of dicts: {'text': str, 'start': float, 'end': float, 'duration': float}
    """
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Karaoke,Arial,84,&H0047E0FD,&H00FFFFFF,&H00333333,&H80000000,-1,0,0,0,100,100,0,0,1,10,4,8,100,100,1100,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    for item in lines_timing:
        t_start = format_time(item['start'])
        t_end = format_time(item['end'] + 0.3)
        k_text = generate_karaoke_line(item['text'], item['duration'], style=style)
        ass_content += f"Dialogue: 0,{t_start},{t_end},Karaoke,,0,0,0,,{k_text}\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

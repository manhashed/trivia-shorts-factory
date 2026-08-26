from typing import List

def format_time(seconds: float) -> str:
    """Format seconds to ASS time format h:mm:ss.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def generate_karaoke_line(text: str, duration: float) -> str:
    """Distribute duration across words and add ASS karaoke tags"""
    words = text.split()
    if not words: return ""
    cs_per_word = int((duration * 100) / len(words))
    k_tag = f"{{\\k{cs_per_word}}}"
    return " ".join([f"{k_tag}{w}" for w in words])

def create_ass_file(lines_timing: List[dict], output_path: str):
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
    # Note: Alignment 8 = Top Center, MarginV 1100 = 1100px from Top
    
    for item in lines_timing:
        t_start = format_time(item['start'])
        t_end = format_time(item['end'] + 0.3) # Leave text a bit longer
        k_text = generate_karaoke_line(item['text'], item['duration'])
        ass_content += f"Dialogue: 0,{t_start},{t_end},Karaoke,,0,0,0,,{k_text}\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

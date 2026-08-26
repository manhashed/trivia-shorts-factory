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
    # centiseconds per word
    cs_per_word = int((duration * 100) / len(words))
    k_tag = f"{{\\k{cs_per_word}}}"
    return " ".join([f"{k_tag}{w}" for w in words])

t1 = format_time(0.0)
t2 = format_time(2.54)
line = generate_karaoke_line("Twinkle twinkle little star", 2.54)
print(f"Dialogue: 0,{t1},{t2},Karaoke,,0,0,0,,{line}")

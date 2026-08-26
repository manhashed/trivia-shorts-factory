import wave
import math
import struct
from pathlib import Path
from backend.app.config import AUDIO_DIR

def write_wav(file_path: Path, samples: list[float], sample_rate: int = 44100):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(file_path), "wb") as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        raw_bytes = bytearray()
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            int_val = int(clamped * 32767.0)
            # Stereo: L and R identical
            raw_bytes.extend(struct.pack("<hh", int_val, int_val))
        wav_file.writeframes(raw_bytes)

def generate_tone(freq: float, duration: float, sample_rate: int = 44100, volume: float = 0.3, decay: float = 4.0) -> list[float]:
    num_samples = int(duration * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        env = math.exp(-decay * t)
        # Fundamental + gentle 2nd harmonic for warm marimba/xylophone acoustic tone
        val = (0.75 * math.sin(2.0 * math.pi * freq * t) + 0.25 * math.sin(4.0 * math.pi * freq * t)) * env * volume
        samples.append(val)
    return samples

def generate_nursery_bgm_loop(output_path: Path, duration: float = 8.0, sample_rate: int = 44100):
    """Generates an upbeat, gentle preschool nursery melody loop (C - G - Am - F progression)."""
    total_samples = int(duration * sample_rate)
    track = [0.0] * total_samples

    # Melody notes: (time_sec, freq_hz)
    # C Major Preschool theme
    melody = [
        # Measure 1: C Major (C4 - E4 - G4 - E4)
        (0.0, 261.63), (0.5, 329.63), (1.0, 392.00), (1.5, 329.63),
        # Measure 2: G Major (D4 - G4 - B4 - G4)
        (2.0, 293.66), (2.5, 392.00), (3.0, 493.88), (3.5, 392.00),
        # Measure 3: A Minor (C4 - E4 - A4 - E4)
        (4.0, 261.63), (4.5, 329.63), (5.0, 440.00), (5.5, 329.63),
        # Measure 4: F Major (F4 - A4 - C5 - G4)
        (6.0, 349.23), (6.5, 440.00), (7.0, 523.25), (7.5, 392.00),
    ]

    # Bass accompaniment (C3, G2, A2, F2)
    bass = [
        (0.0, 130.81), (1.0, 130.81),
        (2.0, 98.00),  (3.0, 98.00),
        (4.0, 110.00), (5.0, 110.00),
        (6.0, 87.31),  (7.0, 87.31),
    ]

    for t_sec, freq in melody:
        idx = int(t_sec * sample_rate)
        tone = generate_tone(freq, duration=0.8, sample_rate=sample_rate, volume=0.25, decay=3.5)
        for i, s in enumerate(tone):
            if idx + i < total_samples:
                track[idx + i] += s

    for t_sec, freq in bass:
        idx = int(t_sec * sample_rate)
        tone = generate_tone(freq, duration=1.2, sample_rate=sample_rate, volume=0.2, decay=2.0)
        for i, s in enumerate(tone):
            if idx + i < total_samples:
                track[idx + i] += s

    write_wav(output_path, track, sample_rate)


def generate_magical_story_bgm(output_path: Path, duration: float = 8.0, sample_rate: int = 44100):
    """Generates a warm, dreamy storybook bell & music box loop."""
    total_samples = int(duration * sample_rate)
    track = [0.0] * total_samples

    arpeggios = [
        (0.0, 523.25), (0.4, 659.25), (0.8, 783.99), (1.2, 1046.50),
        (2.0, 587.33), (2.4, 739.99), (2.8, 880.00), (3.2, 1174.66),
        (4.0, 440.00), (4.4, 523.25), (4.8, 659.25), (5.2, 880.00),
        (6.0, 698.46), (6.4, 880.00), (6.8, 1046.50), (7.2, 1318.51),
    ]

    for t_sec, freq in arpeggios:
        idx = int(t_sec * sample_rate)
        tone = generate_tone(freq, duration=1.5, sample_rate=sample_rate, volume=0.18, decay=2.0)
        for i, s in enumerate(tone):
            if idx + i < total_samples:
                track[idx + i] += s

    write_wav(output_path, track, sample_rate)


def generate_kids_cheer_sfx(output_path: Path, duration: float = 2.0, sample_rate: int = 44100):
    """Generates celebratory chime & applause fanfare."""
    total_samples = int(duration * sample_rate)
    track = [0.0] * total_samples

    fanfare_notes = [
        (0.0, 523.25), (0.1, 659.25), (0.2, 783.99), (0.3, 1046.50), (0.45, 1318.51)
    ]
    for t_sec, freq in fanfare_notes:
        idx = int(t_sec * sample_rate)
        tone = generate_tone(freq, duration=1.2, sample_rate=sample_rate, volume=0.35, decay=3.0)
        for i, s in enumerate(tone):
            if idx + i < total_samples:
                track[idx + i] += s

    write_wav(output_path, track, sample_rate)


def generate_all_bgm_and_sfx(audio_dir: Path):
    bgm_dir = audio_dir / "bgm"
    bgm_dir.mkdir(parents=True, exist_ok=True)

    generate_nursery_bgm_loop(bgm_dir / "playful_nursery_bgm.wav")
    generate_magical_story_bgm(bgm_dir / "magical_story_bgm.wav")
    generate_kids_cheer_sfx(audio_dir / "kids_cheer.wav")
    print(f"Generated BGM loops and expanded SFX in {audio_dir}")


if __name__ == "__main__":
    generate_all_bgm_and_sfx(AUDIO_DIR)

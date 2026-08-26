import math
import struct
import wave
from pathlib import Path
from backend.app.config import ASSETS_DIR

SAMPLE_RATE = 44100

def note_freq(midi_note: int) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

def synthesize_sine(freq: float, duration: float, sample_rate: int = 44100) -> list[float]:
    n = int(sample_rate * duration)
    return [math.sin(2.0 * math.pi * freq * i / sample_rate) for i in range(n)]

def apply_envelope(samples: list[float], attack: float = 0.05, decay: float = 0.15) -> list[float]:
    n = len(samples)
    att_samples = int(SAMPLE_RATE * attack)
    dec_samples = int(SAMPLE_RATE * decay)
    out = []
    for i, s in enumerate(samples):
        vol = 1.0
        if i < att_samples:
            vol = i / max(1, att_samples)
        elif i > n - dec_samples:
            vol = max(0.0, (n - i) / max(1, dec_samples))
        out.append(s * vol)
    return out

def generate_nursery_melody(output_wav: Path, chord_progression: list[int], tempo_bpm: int = 120, bars: int = 4):
    """
    Synthesizes a musical accompaniment loop (glockenspiel / marimba arpeggio + warm bass).
    """
    beat_dur = 60.0 / tempo_bpm # e.g. 0.5s at 120 bpm
    total_beats = bars * 4
    total_dur = total_beats * beat_dur
    total_samples = int(SAMPLE_RATE * total_dur)
    
    left_buf = [0.0] * total_samples
    right_buf = [0.0] * total_samples

    for bar_idx in range(bars):
        root_midi = chord_progression[bar_idx % len(chord_progression)]
        # Chord notes (Root, Major 3rd, 5th, Octave)
        arpeggio = [root_midi, root_midi + 4, root_midi + 7, root_midi + 12]
        
        # 4 beats per bar, 2 eighth-notes per beat = 8 notes per bar
        for step in range(8):
            cur_beat = bar_idx * 4 + (step * 0.5)
            start_sample = int(cur_beat * beat_dur * SAMPLE_RATE)
            note = arpeggio[step % len(arpeggio)]
            note_dur = beat_dur * 0.6
            
            # Glockenspiel / Marimba bell
            freq = note_freq(note + 12)
            raw = synthesize_sine(freq, note_dur)
            # Add harmonic overtone
            raw_over = synthesize_sine(freq * 2.0, note_dur)
            bell = [0.7 * r + 0.3 * o for r, o in zip(raw, raw_over)]
            bell_env = apply_envelope(bell, attack=0.01, decay=note_dur * 0.8)
            
            for s_idx, val in enumerate(bell_env):
                idx = start_sample + s_idx
                if idx < total_samples:
                    pan = 0.5 + 0.2 * math.sin(step)
                    left_buf[idx] += val * 0.25 * (1.0 - pan)
                    right_buf[idx] += val * 0.25 * pan

        # Bass root note on beat 1 and beat 3
        for bass_beat in [0, 2]:
            cur_beat = bar_idx * 4 + bass_beat
            start_sample = int(cur_beat * beat_dur * SAMPLE_RATE)
            bass_freq = note_freq(root_midi - 12)
            bass_raw = synthesize_sine(bass_freq, beat_dur * 1.5)
            bass_env = apply_envelope(bass_raw, attack=0.03, decay=beat_dur * 1.2)
            for s_idx, val in enumerate(bass_env):
                idx = start_sample + s_idx
                if idx < total_samples:
                    left_buf[idx] += val * 0.3
                    right_buf[idx] += val * 0.3

    # Write 16-bit stereo WAV
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_wav), "w") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        
        frames = bytearray()
        for l, r in zip(left_buf, right_buf):
            l_clamped = max(-1.0, min(1.0, l))
            r_clamped = max(-1.0, min(1.0, r))
            l_int = int(l_clamped * 32767.0)
            r_int = int(r_clamped * 32767.0)
            frames.extend(struct.pack("<hh", l_int, r_int))
        wav_file.writeframes(frames)
    print(f"Generated nursery melody: {output_wav}")


def generate_all_melodies(melodies_dir: Path):
    melodies_dir.mkdir(parents=True, exist_ok=True)
    # 1. Twinkle Star Melody (C - G - Am - F)
    generate_nursery_melody(melodies_dir / "twinkle_star.wav", [60, 67, 69, 65], tempo_bpm=120, bars=4)
    # 2. Playful Ukulele (C - F - G - C)
    generate_nursery_melody(melodies_dir / "playful_ukulele.wav", [60, 65, 67, 60], tempo_bpm=128, bars=4)
    # 3. Storybook Bells (F - C - Dm - Bb)
    generate_nursery_melody(melodies_dir / "storybook_bells.wav", [65, 60, 62, 58], tempo_bpm=110, bars=4)
    # 4. Bouncy March (G - C - D - G)
    generate_nursery_melody(melodies_dir / "bouncy_march.wav", [67, 60, 62, 67], tempo_bpm=135, bars=4)

if __name__ == "__main__":
    generate_all_melodies(ASSETS_DIR / "audio" / "melodies")

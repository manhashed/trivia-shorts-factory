import wave
import math
import struct
import random
from pathlib import Path

def write_wav(file_path: Path, samples: list[tuple[float, float]], sample_rate: int = 44100):
    with wave.open(str(file_path), "wb") as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        raw_bytes = bytearray()
        for L, R in samples:
            # Clamp to [-1.0, 1.0]
            cL = max(-1.0, min(1.0, L))
            cR = max(-1.0, min(1.0, R))
            iL = int(cL * 32767.0)
            iR = int(cR * 32767.0)
            raw_bytes.extend(struct.pack("<hh", iL, iR))
        wav_file.writeframes(raw_bytes)

def generate_tone(freq: float, duration: float, sample_rate: int = 44100, volume: float = 0.5, decay: float = 5.0) -> list[tuple[float, float]]:
    """Generates a decaying sine wave tone (stereo)."""
    num_samples = int(duration * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        env = math.exp(-decay * t)
        val = math.sin(2.0 * math.pi * freq * t) * env * volume
        samples.append((val, val))
    return samples

def generate_tick(freq: float, duration: float = 0.1, sample_rate: int = 44100, volume: float = 0.6) -> list[tuple[float, float]]:
    """Generates a crisp wooden clock tick/pop sound."""
    num_samples = int(duration * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        env = math.exp(-60.0 * t)
        v1 = math.sin(2.0 * math.pi * freq * t)
        v2 = math.sin(2.0 * math.pi * (freq * 2) * t) * 0.5
        v3 = math.sin(2.0 * math.pi * (freq * 3) * t) * 0.25
        val = (v1 + v2 + v3) * env * volume
        samples.append((val, val))
    return samples

def generate_dynamic_countdown(output_path: Path, duration: float, num_ticks: int):
    sr = 44100
    total_samples = int(duration * sr)
    track = [(0.0, 0.0)] * total_samples
    
    for i in range(num_ticks):
        fraction = i / max(1, num_ticks - 1) if num_ticks > 1 else 0
        freq = 800.0 + fraction * 600.0  # 800Hz to 1400Hz
        vol = 0.6 + fraction * 0.35      # 0.6 to 0.95
        
        tick = generate_tick(freq, duration=0.15, sample_rate=sr, volume=vol)
        
        offset_sec = float(i)
        idx = int(offset_sec * sr)
        for j, (L, R) in enumerate(tick):
            if idx + j < total_samples:
                oL, oR = track[idx + j]
                track[idx + j] = (oL + L, oR + R)
                
    write_wav(output_path, track, sr)

def generate_beep_countdown(output_path: Path, duration: float, num_ticks: int):
    sr = 44100
    total_samples = int(duration * sr)
    track = [(0.0, 0.0)] * total_samples

    for i in range(num_ticks):
        fraction = i / max(1, num_ticks - 1) if num_ticks > 1 else 0
        beep = generate_tone(620.0 + fraction * 180.0, duration=0.16, sample_rate=sr, volume=0.55, decay=8.0)
        idx = int(i * duration / num_ticks * sr)
        for j, (left, right) in enumerate(beep):
            if idx + j < total_samples:
                old_left, old_right = track[idx + j]
                track[idx + j] = (old_left + left, old_right + right)

    write_wav(output_path, track, sr)

def generate_celebration_chime(output_path: Path):
    sr = 44100
    duration = 2.0
    total_samples = int(duration * sr)
    track = [(0.0, 0.0)] * total_samples
    
    freqs = [523.25, 659.25, 783.99, 1046.50]  # C5, E5, G5, C6
    for f in freqs:
        for detune in [0.0, 3.0]:
            for i in range(total_samples):
                t = i / sr
                env = math.exp(-2.0 * t) # Slow decay
                val = math.sin(2.0 * math.pi * (f + detune) * t) * env * 0.1
                L, R = track[i]
                if detune > 0:
                    track[i] = (L + val * 1.2, R + val * 0.8)
                else:
                    track[i] = (L + val * 0.8, R + val * 1.2)
                    
    # Sparkle trail 6000 down to 3000Hz (descending sweep)
    for i in range(total_samples):
        t = i / sr
        env = math.exp(-3.0 * t)
        phase = 2.0 * math.pi * (6000.0 * t - 750.0 * t * t)
        val = math.sin(phase) * env * 0.05
        L, R = track[i]
        # Alternate L/R for sparkle
        sparkle_pan = math.sin(2.0 * math.pi * 10.0 * t)
        track[i] = (L + val * (1.0 - sparkle_pan), R + val * (1.0 + sparkle_pan))

    write_wav(output_path, track, sr)

def generate_whoosh(output_path: Path):
    sr = 44100
    duration = 0.5
    total_samples = int(duration * sr)
    track = [(0.0, 0.0)] * total_samples
    
    for i in range(total_samples):
        t = i / sr
        if t < 0.1:
            env = t / 0.1
        else:
            env = math.exp(-5.0 * (t - 0.1))
            
        val = 0.0
        for _ in range(5):
            detune = random.uniform(0.8, 1.2)
            phase_offset = random.uniform(0, 2*math.pi)
            f0 = 200.0 * detune
            k = (3800.0 * detune) / duration
            phase = 2.0 * math.pi * (f0 * t + 0.5 * k * t * t) + phase_offset
            val += math.sin(phase)
            
        val = (val / 5.0) * env * 0.4
        track[i] = (val, val)
        
    write_wav(output_path, track, sr)

def generate_suspense_build(output_path: Path, duration: float):
    sr = 44100
    total_samples = int(duration * sr)
    track = [(0.0, 0.0)] * total_samples
    
    for i in range(total_samples):
        t = i / sr
        phase = 2.0 * math.pi * (200.0 * t + 200.0 * t * t / duration)
        tremolo = 0.5 + 0.5 * math.sin(2.0 * math.pi * 4.0 * t)
        vol = 0.15 + 0.20 * (t / duration)
        
        val = math.sin(phase) * tremolo * vol
        
        # Harmonic
        phase2 = 2.0 * math.pi * (400.0 * t + 400.0 * t * t / duration)
        val += math.sin(phase2) * tremolo * vol * 0.3
        
        track[i] = (val, val)
        
    write_wav(output_path, track, sr)

def generate_impact_hit(output_path: Path):
    sr = 44100
    duration = 0.15
    total_samples = int(duration * sr)
    track = [(0.0, 0.0)] * total_samples
    
    for i in range(total_samples):
        t = i / sr
        env_sine = math.exp(-15.0 * t)
        sine_val = math.sin(2.0 * math.pi * 80.0 * t) * env_sine * 0.8
        
        env_noise = math.exp(-30.0 * t)
        noise_val = random.uniform(-1.0, 1.0) * env_noise * 0.5
        
        val = sine_val + noise_val
        track[i] = (val, val)
        
    write_wav(output_path, track, sr)

def generate_kids_cheer(output_path: Path):
    sr = 44100
    duration = 1.5
    total_samples = int(duration * sr)
    track = [(0.0, 0.0)] * total_samples
    
    num_voices = 20
    voices = []
    for _ in range(num_voices):
        base_f = random.uniform(500, 1500)
        voices.append({
            'f': base_f,
            'phase': random.uniform(0, 2*math.pi),
            'drift_rate': random.uniform(1.0, 4.0),
            'drift_depth': random.uniform(10.0, 50.0)
        })
        
    for i in range(total_samples):
        t = i / sr
        if t < 0.3:
            env = t / 0.3
        elif t > 1.0:
            env = max(0.0, 1.0 - (t - 1.0) / 0.5)
        else:
            env = 1.0
            
        val = 0.0
        for v in voices:
            phase = 2.0 * math.pi * v['f'] * t - (v['drift_depth'] / v['drift_rate']) * math.cos(2.0 * math.pi * v['drift_rate'] * t) + v['phase']
            val += math.sin(phase)
            
        val = (val / num_voices) * env * 0.6
        val += random.uniform(-0.05, 0.05) * env
        
        track[i] = (val, val)
        
    write_wav(output_path, track, sr)

def generate_all_sfx(audio_dir: Path):
    audio_dir.mkdir(parents=True, exist_ok=True)
    generate_dynamic_countdown(audio_dir / "dynamic_countdown.wav", duration=3.0, num_ticks=3)
    generate_celebration_chime(audio_dir / "celebration_chime.wav")
    generate_whoosh(audio_dir / "whoosh.wav")
    generate_suspense_build(audio_dir / "suspense_build.wav", duration=3.0)
    generate_impact_hit(audio_dir / "impact_hit.wav")
    generate_kids_cheer(audio_dir / "kids_cheer.wav")
    print(f"Generated high-quality audio SFX in {audio_dir}")

if __name__ == "__main__":
    from backend.app.config import AUDIO_DIR
    generate_all_sfx(AUDIO_DIR)

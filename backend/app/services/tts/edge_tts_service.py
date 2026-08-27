import asyncio
import os
import random
import re
from pathlib import Path
from typing import List, Dict, Any
import edge_tts
from backend.app.services.tts.base import BaseTTSProvider
from backend.app.services.phrase_variety import REVEAL_PHRASE_TEMPLATES
from backend.app.utils.ffmpeg_check import probe_media_file, get_ffmpeg_binary
import subprocess

class EdgeTTSProvider(BaseTTSProvider):
    """
    Microsoft Azure Neural TTS adapter via Edge-TTS.
    Free, high quality, zero API key required.
    """

    VOICE_PRESETS = {
        "excited_host": {"rate": "+15%", "pitch": "+8Hz", "description": "Energetic game show host"},
        "gentle_storyteller": {"rate": "-5%", "pitch": "-3Hz", "description": "Calm bedtime narrator"},
        "game_show": {"rate": "+5%", "pitch": "+3Hz", "description": "Fun quiz show presenter"},
        "cheerful_teacher": {"rate": "+0%", "pitch": "+5Hz", "description": "Enthusiastic preschool teacher"},
        "dramatic_reveal": {"rate": "-10%", "pitch": "+0Hz", "description": "Slow dramatic reveal"},
    }

    AVAILABLE_VOICES = [
        {
            "id": "en-US-AnaNeural",
            "name": "Ana (Child / Cheerful - Recommended for 3-5)",
            "gender": "Female (Child)",
            "locale": "en-US",
            "tags": ["kid-friendly", "cheerful", "playful"]
        },
        {
            "id": "en-US-JennyNeural",
            "name": "Jenny (Storybook Narrator / Warm)",
            "gender": "Female",
            "locale": "en-US",
            "tags": ["narrator", "gentle", "clear"]
        },
        {
            "id": "en-US-GuyNeural",
            "name": "Guy (Friendly & Energetic Host)",
            "gender": "Male",
            "locale": "en-US",
            "tags": ["energetic", "fun", "warm"]
        },
        {
            "id": "en-GB-SoniaNeural",
            "name": "Sonia (British Preschool / Gentle)",
            "gender": "Female",
            "locale": "en-GB",
            "tags": ["educational", "storybook"]
        },
        {
            "id": "en-US-AriaNeural",
            "name": "Aria (Expressive & Clear)",
            "gender": "Female",
            "locale": "en-US",
            "tags": ["clear", "expressive"]
        },
        {
            "id": "en-US-ChristopherNeural",
            "name": "Christopher (Gentle Fatherly Voice)",
            "gender": "Male",
            "locale": "en-US",
            "tags": ["warm", "deep"]
        },
        {
            "id": "en-US-MichelleNeural", 
            "name": "Michelle (Warm Mother Figure)", 
            "gender": "Female", 
            "locale": "en-US", 
            "tags": ["warm", "maternal"]
        },
        {
            "id": "en-AU-NatashaNeural", 
            "name": "Natasha (Friendly Australian)", 
            "gender": "Female", 
            "locale": "en-AU", 
            "tags": ["fun", "accent"]
        },
        {
            "id": "en-US-RogerNeural", 
            "name": "Roger (Enthusiastic Dad)", 
            "gender": "Male", 
            "locale": "en-US", 
            "tags": ["energetic", "fun"]
        },
    ]

    def get_voice_presets(self) -> dict:
        return self.VOICE_PRESETS

    def _enhance_text_for_speech(self, text: str, style: str = "question") -> str:
        """
        Enhance plain text with SSML-like patterns for more engaging speech.
        Edge TTS doesn't support full SSML but does support some prosody via the Communicate API.
        We can still improve the text itself for better delivery.
        """
        if style == "question":
            intros = [
                "Hmm, ",
                "Okay, ",
                "Here's a fun one! ",
                "Let's see... ",
                "Can you guess this? ",
                "Oh, I know this one! ",
                "Are you ready? ",
                "Get ready! ",
                "Here comes a question! ",
                "Let's think about this! "
            ]
            intro = random.choice(intros)
            return f"{intro}{text}"
        elif style == "answer":
            actual_answer = re.sub(r"^The answer is\.\.\.\s*", "", text, flags=re.IGNORECASE)
            actual_answer = re.sub(r"^The answer is\s*", "", actual_answer, flags=re.IGNORECASE)
            actual_answer = actual_answer.strip().rstrip('!.')
            
            reveal = random.choice(REVEAL_PHRASE_TEMPLATES)
            return reveal.format(answer=actual_answer)
        return text

    async def synthesize(
        self,
        text: str,
        output_path: Path,
        voice: str = "en-US-AnaNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        api_key: str = "",
        text_style: str = None,
    ) -> float:
        """
        Synthesizes text using Microsoft Edge Neural TTS.
        Outputs a clean 44.1kHz WAV file and returns duration in seconds.
        """
        if text_style:
            text = self._enhance_text_for_speech(text, style=text_style)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_mp3 = output_path.with_suffix(".temp.mp3")

        # 1. Synthesize audio stream via Edge-TTS
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
        await communicate.save(str(temp_mp3))

        # 2. Convert to standard 44.1kHz 16-bit PCM WAV for sample-accurate mixing
        ffmpeg_bin = get_ffmpeg_binary()
        cmd = [
            ffmpeg_bin,
            "-y",
            "-i", str(temp_mp3),
            "-ar", "44100",
            "-ac", "2",
            "-c:a", "pcm_s16le",
            str(output_path)
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            # Fallback: rename temp_mp3 directly to output_path if WAV conversion failed
            if temp_mp3.exists():
                temp_mp3.rename(output_path)
        else:
            if temp_mp3.exists():
                temp_mp3.unlink()

        # 3. Probe exact duration
        probe = probe_media_file(output_path)
        duration = probe.get("duration", 0.0)
        return max(0.2, duration)

    def list_voices(self) -> List[Dict[str, Any]]:
        return self.AVAILABLE_VOICES

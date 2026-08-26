from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List

class BaseTTSProvider(ABC):
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        output_path: Path,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        api_key: str = "",
    ) -> float:
        """
        Synthesizes text to an audio file (MP3 or WAV) and returns the duration in seconds.
        """
        pass

    @abstractmethod
    def list_voices(self) -> List[Dict[str, Any]]:
        """
        Returns a list of available voice dictionaries: [{"id": "...", "name": "...", "gender": "...", "description": "..."}]
        """
        pass

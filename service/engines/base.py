from abc import ABC, abstractmethod
from typing import AsyncGenerator
import sys
import os

# Ensure VoxCPM can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from VoxCPM.src.voxcpm.streaming import AudioChunk

class ITTSEngine(ABC):
    """Abstract base class representing a TTS generation engine."""
    
    @abstractmethod
    async def generate_stream(self, text: str) -> AsyncGenerator[AudioChunk, None]:
        """Generates an audio stream from the given text asynchronously."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of the engine."""
        pass
        
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Indicates if the engine is currently available to accept requests."""
        pass

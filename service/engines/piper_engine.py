import asyncio
import time
from typing import AsyncGenerator
import numpy as np
from .base import ITTSEngine
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from VoxCPM.src.voxcpm.streaming import AudioChunk, AudioFormatConverter
from VoxCPM.src.voxcpm import config_instance

class PiperEngine(ITTSEngine):
    """Fallback TTS Engine utilizing the Piper CPU model."""
    
    def __init__(self):
        from piper import PiperVoice
        self._voice = PiperVoice.load(
            "Piper-TTS-Model/model.onnx", config_path="Piper-TTS-Model/config.json"
        )
        self._sample_rate = self._voice.config.sample_rate

    @property
    def name(self) -> str:
        """Returns the name of the engine."""
        return "Piper-Fallback"

    @property
    def is_available(self) -> bool:
        """Indicates if the engine is currently available to accept requests."""
        return True 

    async def generate_stream(self, text: str) -> AsyncGenerator[AudioChunk, None]:
        """Generates an audio stream from the given text asynchronously."""
        from piper.config import SynthesisConfig
        custom_config = SynthesisConfig(length_scale=1, noise_scale=0.65, noise_w_scale=0.5)

        def _generate():
            audio_chunks = []
            for chunk in self._voice.synthesize(text, syn_config=custom_config):
                audio_chunks.append(np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16))
            if not audio_chunks:
                return np.array([], dtype=np.int16)
            return np.concatenate(audio_chunks)

        audio_np = await asyncio.to_thread(_generate)
        
        cfg = config_instance.streaming
        converted = AudioFormatConverter.convert(audio_np, self._sample_rate, cfg.output_format)

        yield AudioChunk(
            data=converted,
            sample_rate=self._sample_rate,
            chunk_index=0,
            sentence_index=0,
            timestamp_ms=time.time() * 1000,
            is_final=True,
            is_sentence_final=True
        )

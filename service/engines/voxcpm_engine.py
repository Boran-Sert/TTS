import asyncio
from typing import AsyncGenerator
from .base import ITTSEngine
import torch

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from VoxCPM.src.voxcpm import VoxCPM, config_instance, async_generate_stream, TextBuffer, StreamingTextSource
from VoxCPM.src.voxcpm.streaming import AudioChunk

class VoxCPMEngine(ITTSEngine):
    """Manages a pool of VoxCPM model instances across multiple GPUs using O(1) Queue logic."""
    
    def __init__(self):
        # Prevent "invalid device ordinal" by limiting to actual physical GPUs
        physical_gpus = torch.cuda.device_count()
        requested_gpus = config_instance.system.voxcpm_gpu_ids
        self._gpu_ids = [g for g in requested_gpus if g < physical_gpus]
        
        if not self._gpu_ids:
            # Fallback to cuda:0 if the config was wrong but we have at least 1 GPU
            self._gpu_ids = [0] if physical_gpus > 0 else []
        self._idle_queue = asyncio.Queue(maxsize=len(self._gpu_ids))
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initializes the model instances on their respective GPUs asynchronously."""
        async with self._lock:
            if self._initialized:
                return
                
            for gpu_id in self._gpu_ids:
                device = f"cuda:{gpu_id}"
                model = await asyncio.to_thread(
                    VoxCPM.from_pretrained,
                    hf_model_id=config_instance.model.model_path,
                    device=device,
                    optimize=config_instance.system.use_torch_compile,
                    load_denoiser=False
                )
                self._idle_queue.put_nowait(model)
                
            self._initialized = True

    @property
    def name(self) -> str:
        """Returns the name of the engine."""
        return "VoxCPM-Pool"

    @property
    def is_available(self) -> bool:
        """Indicates if any GPU in the pool is currently free."""
        return not self._idle_queue.empty()

    async def generate_stream(self, text: str) -> AsyncGenerator[AudioChunk, None]:
        """Generates audio stream using the next available GPU."""
        if not self._initialized:
            await self.initialize()
            
        model = await self._idle_queue.get()
        try:
            text_buffer = TextBuffer(
                sentence_delimiters=config_instance.text_processing.sentence_delimiters,
                flush_timeout_ms=config_instance.text_processing.flush_timeout_ms,
                min_chars=config_instance.text_processing.min_chars
            )
            text_source = StreamingTextSource(text_buffer)
            
            def feed_text():
                text_source.push_text(text)
                text_source.finish()
                
            await asyncio.to_thread(feed_text)

            async for chunk in async_generate_stream(model.generate_stream_from_text_source, text_source):
                yield chunk
                
        finally:
            self._idle_queue.put_nowait(model)

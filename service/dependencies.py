import asyncio
from .engines.voxcpm_engine import VoxCPMEngine
from .engines.piper_engine import PiperEngine
from .engines.base import ITTSEngine

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from VoxCPM.src.voxcpm import config_instance

class EngineContainer:
    """Manages the lifecycle and load-balancing routing of TTS engines."""
    
    def __init__(self):
        self.voxcpm_pool = VoxCPMEngine()
        self.piper_engine = PiperEngine()
        self.queue_threshold = config_instance.system.piper_fallback_queue_threshold
        
        # This tracks active/pending requests to VoxCPM
        self.active_requests = 0
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initializes all underlying engines asynchronously."""
        await self.voxcpm_pool.initialize()

    async def get_engine(self) -> ITTSEngine:
        """Determines the appropriate engine based on current system load."""
        async with self._lock:
            if config_instance.system.piper_fallback_enabled:
                # If VoxCPM queue exceeds threshold, immediately fallback to Piper
                if not self.voxcpm_pool.is_available and self.active_requests >= self.queue_threshold:
                    return self.piper_engine
            
            self.active_requests += 1
            return self.voxcpm_pool

    async def release_engine(self, engine: ITTSEngine):
        """Releases the engine and updates active request counts."""
        async with self._lock:
            if engine.name == "VoxCPM-Pool":
                self.active_requests = max(0, self.active_requests - 1)

# Global singleton for dependency injection
engine_container = EngineContainer()

async def get_tts_engine() -> ITTSEngine:
    """FastAPI Dependency injection endpoint."""
    return await engine_container.get_engine()

import io
import queue
import threading
from dataclasses import dataclass
from typing import Union, Any

import numpy as np
import scipy.io.wavfile

@dataclass
class AudioChunk:
    data: Union[bytes, np.ndarray]
    sample_rate: int
    chunk_index: int
    sentence_index: int
    timestamp_ms: float
    is_final: bool
    is_sentence_final: bool


class AudioFormatConverter:

    @staticmethod
    def to_pcm16_le(audio_np: np.ndarray) -> bytes:
        """ Vectorized conversion to Little-Endian 16-bit PCM."""
        audio_clipped = np.clip(audio_np, -1.0, 1.0)
        pcm_16 = (audio_clipped * 32767.0).astype('<i2')
        return pcm_16.tobytes()

    @staticmethod
    def to_wav(audio_np: np.ndarray, sample_rate: int) -> bytes:
        """ Vectorized WAV header + PCM16 data."""
        pcm_16 = (np.clip(audio_np, -1.0, 1.0) * 32767.0).astype('<i2')
        wav_buffer = io.BytesIO()
        scipy.io.wavfile.write(wav_buffer, sample_rate, pcm_16)
        return wav_buffer.getvalue()

    @staticmethod
    def to_float32(audio_np: np.ndarray) -> bytes:
        """Little-Endian Float32 conversion."""
        return audio_np.astype('<f4').tobytes()

    @staticmethod
    def convert(audio_np: np.ndarray, sample_rate: int, output_format: str) -> Union[bytes, np.ndarray]:
        if output_format in ["pcm16_le", "pcm16"]:
            return AudioFormatConverter.to_pcm16_le(audio_np)
        elif output_format == "wav":
            return AudioFormatConverter.to_wav(audio_np, sample_rate)
        elif output_format == "float32":
            return AudioFormatConverter.to_float32(audio_np)
        elif output_format == "numpy":
            return audio_np
        else:
            raise ValueError(f"Desteklenmeyen çıktı formatı: {output_format}")


class RingBuffer:

    def __init__(self, capacity: int = 8):
        self.capacity = capacity

        self.buffer = [None] * capacity
        self.head = 0
        self.tail = 0
        self.size = 0
        self.lock = threading.Lock()
        self.not_empty = threading.Condition(self.lock)
        self.not_full = threading.Condition(self.lock)
        self.closed = False

    def put(self, item: Any, block: bool = True, timeout: float = None):
        with self.lock:
            while self.size == self.capacity and not self.closed:
                if not block:
                    raise queue.Full
                if not self.not_full.wait(timeout):
                    raise queue.Full

            if self.closed:
                raise ValueError("RingBuffer is closed")

            # write operation
            self.buffer[self.tail] = item
            self.tail = (self.tail + 1) % self.capacity
            self.size += 1
            self.not_empty.notify()

    def get(self, block: bool = True, timeout: float = None) -> Any:
        with self.lock:
            while self.size == 0 and not self.closed:
                if not block:
                    raise queue.Empty
                if not self.not_empty.wait(timeout):
                    raise queue.Empty

            if self.size == 0 and self.closed:
                return None 

            item = self.buffer[self.head]

            self.buffer[self.head] = None 
            self.head = (self.head + 1) % self.capacity
            self.size -= 1
            self.not_full.notify()
            return item

    def close(self):
        with self.lock:
            self.closed = True
            self.not_full.notify_all()
            self.not_empty.notify_all()

    @property
    def is_full(self) -> bool:
        with self.lock:
            return self.size == self.capacity

    @property
    def is_empty(self) -> bool:
        with self.lock:
            return self.size == 0

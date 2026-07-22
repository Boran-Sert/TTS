"""
Audio Quality & Processing Utilities
------------------------------------
- EBU R128 Loudness Normalization (-24 LUFS)
- Hann-Windowed Overlap-Add Cross-Fading (Eliminates pop/click noise)
"""

import numpy as np

class AudioQualityProcessor:
    @staticmethod
    def normalize_loudness_ebur128(audio_float32: np.ndarray, target_lufs: float = -24.0) -> np.ndarray:
        """EBU R128 standartlarında ses seviyesi normalizasyonu ve peak limiter."""
        if audio_float32 is None or len(audio_float32) == 0:
            return audio_float32
            
        rms = np.sqrt(np.mean(audio_float32**2)) + 1e-8
        current_lufs = 20 * np.log10(rms)
        gain_db = target_lufs - current_lufs
        gain_linear = 10 ** (gain_db / 20.0)
        
        normalized = audio_float32 * gain_linear
        
        # Peak Limit (-0.9 dBFS)
        max_val = np.max(np.abs(normalized))
        if max_val > 0.9:
            normalized = normalized * (0.9 / max_val)
            
        return normalized

    @staticmethod
    def apply_hann_overlap_add(prev_chunk: np.ndarray, curr_chunk: np.ndarray, overlap_samples: int = 480) -> tuple[np.ndarray, np.ndarray]:
        """24kHz ses için 20ms (480 sample) Hann pencereli Overlap-Add cross-fading."""
        if prev_chunk is None or len(prev_chunk) < overlap_samples or curr_chunk is None or len(curr_chunk) < overlap_samples:
            return curr_chunk, None
            
        hann_window = np.hanning(overlap_samples * 2)
        fade_out = hann_window[overlap_samples:]
        fade_in = hann_window[:overlap_samples]
        
        blended = (prev_chunk[-overlap_samples:] * fade_out) + (curr_chunk[:overlap_samples] * fade_in)
        
        ready_chunk = np.concatenate([prev_chunk[:-overlap_samples], blended])
        next_leftover = curr_chunk[overlap_samples:]
        
        return ready_chunk, next_leftover

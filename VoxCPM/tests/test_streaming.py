import unittest
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from voxcpm.streaming import AudioFormatConverter, RingBuffer

class TestStreamingComponents(unittest.TestCase):
    """Unit tests for the streaming infrastructure."""
    
    def test_audio_format_converter_pcm16_le(self):
        """Tests Little-Endian PCM16 vectorized conversion accuracy."""
        audio_np = np.array([-1.0, 0.0, 1.0], dtype=np.float32)
        pcm_bytes = AudioFormatConverter.to_pcm16_le(audio_np)
        
        expected_array = np.array([-32767, 0, 32767], dtype=np.int16)
        expected_bytes = expected_array.astype('<i2').tobytes()
        
        self.assertEqual(pcm_bytes, expected_bytes)

    def test_audio_format_converter_clipping(self):
        """Tests that out-of-bound float signals are clipped properly."""
        audio_np = np.array([-2.0, 5.0], dtype=np.float32)
        pcm_bytes = AudioFormatConverter.to_pcm16_le(audio_np)
        
        expected_array = np.array([-32767, 32767], dtype=np.int16)
        expected_bytes = expected_array.astype('<i2').tobytes()
        
        self.assertEqual(pcm_bytes, expected_bytes)

    def test_ring_buffer_operations(self):
        """Tests pre-allocated array behavior and head/tail logic."""
        buffer = RingBuffer(capacity=3)
        
        self.assertTrue(buffer.is_empty)
        self.assertFalse(buffer.is_full)
        
        buffer.put("A")
        buffer.put("B")
        buffer.put("C")
        
        self.assertTrue(buffer.is_full)
        self.assertFalse(buffer.is_empty)
        
        self.assertEqual(buffer.get(), "A")
        self.assertEqual(buffer.get(), "B")
        
        buffer.put("D")
        self.assertFalse(buffer.is_full)
        
        self.assertEqual(buffer.get(), "C")
        self.assertEqual(buffer.get(), "D")
        
        self.assertTrue(buffer.is_empty)

if __name__ == '__main__':
    unittest.main()

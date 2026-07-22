import os
import sys
import threading
import numpy as np
import sounddevice as sd

current_dir = os.path.dirname(os.path.abspath(__file__))
voxcpm_src = os.path.abspath(os.path.join(current_dir, "..", "VoxCPM", "src"))
if voxcpm_src not in sys.path:
    sys.path.insert(0, voxcpm_src)

from voxcpm import VoxCPM
from voxcpm.streaming import RingBuffer
from voxcpm.utils.banking_tn import NativeBankingTextNormalizer, INormalizationRule
from voxcpm.utils.audio_processor import AudioQualityProcessor


class VoxTrendyol:
    """
    VoxCPM altyapısını kullanarak gelişmiş TextBuffer, RingBuffer, Overlap-Add,
    Dinamik Metin Normalizasyonu ve asenkron ses oynatma sistemlerini tek bir
    çatı altında toplayan sarmalayıcı sınıf.
    """

    def __init__(self, model_path: str = "Trendyol_TTS", load_denoiser: bool = False, optimize: bool = True):
        self.model = VoxCPM.from_pretrained(model_path, load_denoiser=load_denoiser, optimize=optimize)
        self.sample_rate = self.model.tts_model.sample_rate
        self.normalizer = NativeBankingTextNormalizer()

    def register_currency(self, code: str, name_tr: str, sub_unit_tr: str = "", symbol: str = None):
        """Tak-Çıkar: Yeni para birimi ekleme"""
        self.normalizer.register_currency(code, name_tr, sub_unit_tr, symbol)

    def register_stock_alias(self, ticker: str, spoken_name: str):
        """Tak-Çıkar: Yeni hisse senedi okunuşu ekleme"""
        self.normalizer.register_stock_alias(ticker, spoken_name)

    def add_normalization_rule(self, rule: INormalizationRule):
        """Tak-Çıkar: Özel normalizasyon kuralı ekleme"""
        self.normalizer.add_rule(rule)

    def speak(self, text: str, ref_audio: str = "voices/zeynep.wav", ref_text: str = None) -> np.ndarray:
        """
        TEK SATIRDA KONUŞTURMA VE ASENKRON OYNATMA API'Sİ
        Gelen metni otomatik olarak Türkçe normalizasyondan geçirir,
        arka planda takılmadan çalar ve ses dizisini döndürür.
        """
        ref_path = ref_audio if (ref_audio and os.path.exists(ref_audio)) else None
        normalized_text = self.normalizer.normalize(text)
        
        return self.smart_generate_streaming(
            text=normalized_text,
            ref_audio=ref_path,
            prompt_audio=ref_path,
            prompt_text=ref_text,
            play=True
        )

    def smart_generate_streaming(
        self,
        text: str,
        ref_audio: str = None,
        prompt_audio: str = None,
        prompt_text: str = None,
        cfg_value: float = 2.0,
        inference_timesteps: int = 10,
        chunk_duration_ms: int = 200,
        enable_lookbehind: bool = True,
        lookbehind_mode: str = "anchor",
        seed: int = 42,
        play: bool = True,
        normalize_text: bool = True,
    ) -> np.ndarray:
        """
        Sesi üretir ve eğer play=True ise asenkron olarak arka planda çalar.
        Ses verisini tek parça int16 numpy dizisi olarak geri döndürür.
        """
        if normalize_text:
            text = self.normalizer.normalize(text)

        chunks_generator = self.model.generate_smart(
            text=text,
            streaming=True,
            reference_wav_path=ref_audio,
            prompt_wav_path=prompt_audio,
            prompt_text=prompt_text,
            cfg_value=cfg_value,
            inference_timesteps=inference_timesteps,
            chunk_duration_ms=chunk_duration_ms,
            enable_lookbehind=enable_lookbehind,
            lookbehind_mode=lookbehind_mode,
            seed=seed,
        )

        all_chunks = []

        if not play:
            for chunk in chunks_generator:
                all_chunks.append(chunk)
        else:
            buffer = RingBuffer(capacity=32)

            def producer():
                for chunk in chunks_generator:
                    buffer.put(chunk)
                buffer.put(None)

            t = threading.Thread(target=producer)
            t.start()

            print("--- Ses oynatımı asenkron olarak başlıyor ---", file=sys.stderr)
            with sd.RawOutputStream(
                samplerate=self.sample_rate, channels=1, dtype="int16"
            ) as stream:
                while True:
                    chunk = buffer.get()
                    if chunk is None:
                        break

                    stream.write(chunk)
                    all_chunks.append(chunk)

            t.join()

        if len(all_chunks) == 0:
            return np.array([], dtype=np.int16)

        full_audio_bytes = b"".join(all_chunks)
        audio_array = np.frombuffer(full_audio_bytes, dtype=np.int16)

        return audio_array

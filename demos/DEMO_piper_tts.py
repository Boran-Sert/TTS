import argparse
import time
import logging

import sounddevice as sd
import numpy as np
from piper import PiperVoice

from system_monitor import get_system_stats

# Kurumsal Loglama (Piper Modülü)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("Piper_TTS")

logger.info("Piper TTS Modeli yükleniyor...")

try:
    voice = PiperVoice.load(
        "Piper-TTS-Model/model.onnx", config_path="Piper-TTS-Model/config.json"
    )
    sample_rate = voice.config.sample_rate
    logger.info("Model hazır!")
except Exception as e:
    logger.error(f"Model yüklenemedi: {e}")
    voice = None
    sample_rate = 22050


def generate_piper_audio(text: str):
    """Metni sentezler, aralara ve sonlara boşluk ekler ve bytes olarak döner."""
    if not voice:
        return b""

    start_time = time.time()

    from piper.config import SynthesisConfig

    custom_config = SynthesisConfig(length_scale=1, noise_scale=0.65, noise_w_scale=0.5)

    audio_chunks = []
    for chunk in voice.synthesize(text, syn_config=custom_config):
        audio_chunks.append(np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16))

    if not audio_chunks:
        return b""

    # O(N^2) bellek sızıntısını önlemek için tüm array'leri tek bir listede toplayıp birleştiriyoruz
    silence_between = np.zeros(int(sample_rate * 0.6), dtype=np.int16)
    silence_edge = np.zeros(int(sample_rate * 0.3), dtype=np.int16)

    final_sequence = [silence_edge]
    for i, chunk in enumerate(audio_chunks):
        final_sequence.append(chunk)
        if i < len(audio_chunks) - 1:
            final_sequence.append(silence_between)
    final_sequence.append(silence_edge)

    padded_audio = np.concatenate(final_sequence)

    elapsed = time.time() - start_time
    logger.info(f"Üretim Süresi (Piper): {elapsed:.2f} saniye")
    logger.info(f"Sistem Kaynakları    : {get_system_stats()}")

    return padded_audio.tobytes()


def main():
    parser = argparse.ArgumentParser(description="Piper TTS Interactive Mode")
    parser.add_argument("--text", type=str, default="", help="Okunacak metin.")
    args = parser.parse_args()

    if not voice:
        return

    if args.text:
        audio_bytes = generate_piper_audio(args.text)
        audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
        sd.play(audio_data, samplerate=sample_rate)
        sd.wait()
        return

    logger.info("--- İnteraktif Piper TTS Modeli Başlatıldı ---")
    
    while True:
        try:
            text = input("\nMetin girin (çıkmak için 'çık') > ").strip()
            if not text:
                continue
            if text.lower() == "çık":
                logger.info("Çıkış yapılıyor...")
                break

            logger.info(f"Sentezleniyor: {text}")
            audio_bytes = generate_piper_audio(text)
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            sd.play(audio_data, samplerate=sample_rate)
            sd.wait()

        except KeyboardInterrupt:
            logger.info("Çıkış yapılıyor...")
            break
        except Exception as e:
            logger.error(f"Hata oluştu: {e}")


if __name__ == "__main__":
    main()

import io
import re
import time
import logging

import numpy as np
import scipy.io.wavfile
from voxcpm import VoxCPM
from system_monitor import get_system_stats

# Kurumsal Loglama (Trendyol Modülü)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("Trendyol_TTS")

logger.info("Trendyol TTS Modeli yükleniyor...")

MODEL_ID = "./Trendyol-TTS"

synthesizer = VoxCPM.from_pretrained(
    MODEL_ID,
    load_denoiser=False,
    optimize=True,
)


def process_text_with_lookahead(text: str):
    """
    Metni cümlelere ayırır.
    Her cümle için sonraki cümlenin ilk 3 kelimesini lookahead olarak hesaplar.
    """

    # Sayılardaki noktaları veya ondalıkları ayırmaması için güncel Regex:
    raw_parts = re.split(r"([.?!]+(?:\s+|$))", text)
    sentences = [
        (raw_parts[i] + (raw_parts[i + 1] if i + 1 < len(raw_parts) else "")).strip()
        for i in range(0, len(raw_parts), 2)
    ]
    sentences = [s for s in sentences if s]

    chunks = [
        {
            "speak_text": sentences[i],
            "lookahead_context": " ".join(sentences[i + 1].split()[:3])
            if i + 1 < len(sentences)
            else "",
        }
        for i in range(len(sentences))
    ]

    return chunks


async def audio_stream_generator(text: str):

    chunks = process_text_with_lookahead(text)

    for index, chunk in enumerate(chunks):
        text_to_speak = chunk["speak_text"]
        lookahead = chunk["lookahead_context"]

        logger.info(f"--- CHUNK {index + 1}/{len(chunks)} ---")
        logger.info(f"SENTEZ    : {text_to_speak}")
        logger.info(f"LOOKAHEAD : {lookahead}")

        start_time = time.time()
        audio = synthesizer.generate(
            text=text_to_speak,
            cfg_value=2.0,
            inference_timesteps=16,
            max_len=4096,
            normalize=True,
            denoise=False,
        )
        end_time = time.time()
        elapsed = end_time - start_time

        logger.info(f"Üretim Süresi : {elapsed:.2f} saniye | Uzunluk: {len(audio)} örnek")
        logger.info(f"Kaynaklar    : {get_system_stats()}")

        audio = np.asarray(audio)

        if audio.dtype != np.int16:
            audio = (audio * 32767).astype(np.int16)

        wav_buffer = io.BytesIO()

        scipy.io.wavfile.write(
            wav_buffer,
            synthesizer.tts_model.sample_rate,
            audio,
        )

        wav_buffer.seek(0)
        yield wav_buffer.read()

def generate_trendyol_audio(text: str) -> bytes:
    """Tüm metni sentezler ve tek bir birleştirilmiş ses array'ini bytes olarak döner."""
    chunks = process_text_with_lookahead(text)
    all_audio = []
    
    for index, chunk in enumerate(chunks):
        text_to_speak = chunk["speak_text"]
        logger.info(f"Sentezleniyor: {text_to_speak}")
        start_time = time.time()
        audio = synthesizer.generate(
            text=text_to_speak,
            cfg_value=2.0,
            inference_timesteps=16,
            max_len=4096,
            normalize=True,
            denoise=False,
        )
        logger.info(f"Üretim Süresi: {time.time() - start_time:.2f} saniye")
        
        audio = np.asarray(audio)
        if audio.dtype != np.int16:
            audio = (audio * 32767).astype(np.int16)
        all_audio.append(audio)
        
    if not all_audio:
        return b""
        
    silence = np.zeros(int(synthesizer.tts_model.sample_rate * 0.3), dtype=np.int16)
    
    final_sequence = []
    for i, a in enumerate(all_audio):
        final_sequence.append(a)
        if i < len(all_audio) - 1:
            final_sequence.append(silence)
            
    padded_audio = np.concatenate(final_sequence)
    return padded_audio.tobytes()


if __name__ == "__main__":
    import argparse
    import sounddevice as sd

    parser = argparse.ArgumentParser(description="Trendyol TTS (Interactive)")
    parser.add_argument(
        "--text",
        type=str,
        default="",
        help="Metin girerseniz sadece o metni okur ve çıkar.",
    )
    parser.add_argument(
        "--interactive", action="store_true", help="İnteraktif modu başlatır."
    )
    args = parser.parse_args()

    def play_text(text_to_play):
        chunks = process_text_with_lookahead(text_to_play)
        for index, chunk in enumerate(chunks):
            text_to_speak = chunk["speak_text"]
            logger.info(f"[{index + 1}/{len(chunks)}] Okunuyor: {text_to_speak}")

            start_time = time.time()
            audio = synthesizer.generate(
                text=text_to_speak,
                cfg_value=2.0,
                inference_timesteps=16,
                max_len=4096,
                normalize=True,
                denoise=False,
            )
            elapsed = time.time() - start_time
            logger.info(f"Oynatma Üretim Süresi: {elapsed:.2f} saniye")
            logger.info(f"Sistem Kaynakları    : {get_system_stats()}")

            audio = np.asarray(audio)
            if audio.dtype != np.int16:
                audio = (audio * 32767).astype(np.int16)

            silence = np.zeros(
                int(synthesizer.tts_model.sample_rate * 0.3), dtype=np.int16
            )
            padded = np.concatenate([silence, audio, silence])
            sd.play(padded, samplerate=synthesizer.tts_model.sample_rate)
            sd.wait()

    if args.text:
        play_text(args.text)
    elif args.interactive:
        logger.info("--- İnteraktif Trendyol TTS Modeli Başlatıldı ---")
        while True:
            try:
                user_text = input("\nMetin girin (çıkmak için 'çık') > ").strip()
                if not user_text:
                    continue
                if user_text.lower() == "çık":
                    logger.info("Çıkış yapılıyor...")
                    break
                play_text(user_text)
            except KeyboardInterrupt:
                logger.info("Çıkış yapılıyor...")
                break
            except Exception as e:
                logger.error(f"Hata: {e}")
    else:
        logger.info("Bu dosya artık bir modüldür. API için 'python main.py' dosyasını çalıştırın.")
        logger.info("Test için: python DEMO_trendyol_default_tts.py --interactive")

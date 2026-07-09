import argparse
import os
import queue
import re
import tempfile
import threading
import time
import warnings
from typing import List
import sounddevice as sd
import numpy as np
import scipy.io.wavfile
from voxcpm import VoxCPM


warnings.filterwarnings("ignore")


def split_into_sentences(text: str) -> List[str]:
    """Splits text into logical sentences."""

    raw_sentences = re.split(r"([.?!])", text)
    sentences = []

    for i in range(0, len(raw_sentences) - 1, 2):
        sentence = (raw_sentences[i] + raw_sentences[i + 1]).strip()
        if sentence:
            sentences.append(sentence)

    if len(raw_sentences) % 2 != 0 and raw_sentences[-1].strip():
        sentences.append(raw_sentences[-1].strip())

    return sentences


def consumer_playback(audio_queue: queue.Queue, sample_rate: int):
    """Consumer thread that plays audio chunks as they arrive in the queue."""
    print("[Player] Başlatıldı. Sentezlenen sesler bekleniyor...\n")
    while True:
        item = audio_queue.get()
        if item is None:
            # End of stream
            break

        sentence_idx, audio_data = item
        print(f"[Player] Oynatılıyor: Cümle {sentence_idx}")

        # Play the audio blockingly
        sd.play(audio_data, samplerate=sample_rate)
        sd.wait()

        audio_queue.task_done()

    print("[Player] Oynatma tamamlandı.")


def producer_synthesis(
    synthesizer: VoxCPM,
    sentences: List[str],
    audio_queue: queue.Queue,
    cfg_value: float,
    timesteps: int,
):
    """Producer thread that synthesizes audio with Context-Aware (Lookbehind) logic."""
    print("[Sentez] Üretim başlatılıyor...\n")

    current_prompt_text = None
    current_prompt_wav_path = None
    temp_files = []

    sample_rate = synthesizer.tts_model.sample_rate

    try:
        for idx, sentence in enumerate(sentences):
            print(f"[Sentez] Üretiliyor ({idx + 1}/{len(sentences)}): {sentence}")

            # 1. Generate audio for the current sentence, using the previous sentence as context
            start_time = time.time()
            if current_prompt_text and current_prompt_wav_path:
                print(
                    f"         > Bağlam (Context) kullanılıyor: '{current_prompt_text}'"
                )
                audio = synthesizer.generate(
                    text=sentence,
                    prompt_text=current_prompt_text,
                    prompt_wav_path=current_prompt_wav_path,
                    cfg_value=cfg_value,
                    inference_timesteps=timesteps,
                    max_len=4096,
                    normalize=True,
                    denoise=False,
                )
            else:
                # First sentence has no context
                audio = synthesizer.generate(
                    text=sentence,
                    cfg_value=cfg_value,
                    inference_timesteps=timesteps,
                    max_len=4096,
                    normalize=True,
                    denoise=False,
                )

            elapsed = time.time() - start_time
            print(f"         > Sentez süresi: {elapsed:.2f} saniye")

            audio = np.asarray(audio)

            # Put audio to the playback queue
            audio_queue.put((idx + 1, audio))

            # 2. Save this generated audio to a temporary file to use as context for the next sentence
            if audio.dtype != np.int16:
                audio_int16 = (audio * 32767).astype(np.int16)
            else:
                audio_int16 = audio

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            scipy.io.wavfile.write(temp_file.name, sample_rate, audio_int16)
            temp_files.append(temp_file.name)

            # 3. Update context for the next iteration
            current_prompt_text = sentence
            current_prompt_wav_path = temp_file.name

    except Exception as e:
        print(f"\n[Hata] Sentez sırasında hata oluştu: {e}")
    finally:
        audio_queue.put(None)

        for tmp_path in temp_files:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass


def run_lookahead_tts(synthesizer: VoxCPM, text: str, cfg_value: float, timesteps: int):
    sentences = split_into_sentences(text)
    if not sentences:
        print("Metinden cümle çıkarılamadı.")
        return

    print(f"\nToplam {len(sentences)} cümle sentezlenecek.")
    print("=" * 60)

    # Initialize a thread-safe Queue
    audio_queue = queue.Queue()

    # Create threads
    consumer_thread = threading.Thread(
        target=consumer_playback,
        args=(audio_queue, synthesizer.tts_model.sample_rate),
        daemon=True,
    )

    producer_thread = threading.Thread(
        target=producer_synthesis,
        args=(synthesizer, sentences, audio_queue, cfg_value, timesteps),
        daemon=True,
    )

    # Start playback thread first, it will block waiting for queue items
    consumer_thread.start()

    # Start synthesis thread
    producer_thread.start()

    # Wait for synthesis to complete
    producer_thread.join()

    # Wait for playback to complete (wait for queue to be fully processed)
    consumer_thread.join()

    print("\nİşlem tamamlandı.")


def main():
    parser = argparse.ArgumentParser(
        description="Context-Aware Streaming TTS with VoxCPM2 (Lookbehind)"
    )
    parser.add_argument(
        "--text", type=str, default=None, help="Sentezlenecek metin (opsiyonel)."
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default="./Trendyol-TTS",
        help="Trendyol-TTS modelinin dizini.",
    )
    parser.add_argument(
        "--cfg-value", type=float, default=2.0, help="Guidance scale (default: 2.0)"
    )
    parser.add_argument(
        "--timesteps", type=int, default=16, help="Inference timesteps (default: 16)"
    )

    args = parser.parse_args()

    os.environ["HF_XET_HIGH_PERFORMANCE"] = "1"

    print("=" * 60)
    print("Trendyol TTS Modeli yükleniyor")
    print("=" * 60)

    synthesizer = VoxCPM.from_pretrained(
        args.model_path,
        load_denoiser=False,
        optimize=True,
    )

    print("\nModel hazır!")
    print("=" * 60)

    if args.text:
        run_lookahead_tts(synthesizer, args.text, args.cfg_value, args.timesteps)
    else:
        print("\n--- İnteraktif TTS Modu ---")
        print("Sözlerinizi girin, sistem seslendirsin. Çıkmak için 'çık' yazın.\n")
        while True:
            try:
                user_text = input("Metin girin > ").strip()
                if not user_text:
                    continue
                if user_text.lower() == "çık":
                    print("Çıkış yapılıyor...")
                    break
                run_lookahead_tts(
                    synthesizer, user_text, args.cfg_value, args.timesteps
                )
            except KeyboardInterrupt:
                print("\nÇıkış yapılıyor...")
                break
            except Exception as e:
                print(f"Hata oluştu: {e}")


if __name__ == "__main__":
    main()

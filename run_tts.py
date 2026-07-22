import os
import soundfile as sf
from Trendyol_TTS.voxtrendyol import VoxTrendyol


def speak(
    text: str,
    ref_audio: str = r"voices/zeynep.wav",
    ref_text: str = "Hayvanlar için hayatlarını tehlikeye atmaya hazır insanlar var; aynı zamanda tuhaf, kötü ve çirkin.",
    output_filename: str = "voice_design.wav",
    play: bool = True,
    cfg_value: float = 2.8,
    inference_timesteps: int = 4,
    chunk_duration_ms: int = 150,
    enable_lookbehind: bool = True,
    lookbehind_mode: str = "anchor",
    seed: int = 42,
    normalize_text: bool = True,
    model_path: str = "Trendyol_TTS",
):
    """Metni sese dönüştürür, arka planda çalar ve WAV olarak kaydeder."""
    ref_path = ref_audio if (ref_audio and os.path.exists(ref_audio)) else None
    ref_prompt = ref_text if ref_path else None

    vt = VoxTrendyol(model_path)
    wav = vt.smart_generate_streaming(
        text=text,
        ref_audio=ref_path,
        prompt_audio=ref_path,
        prompt_text=ref_prompt,
        cfg_value=cfg_value,
        inference_timesteps=inference_timesteps,
        chunk_duration_ms=chunk_duration_ms,
        enable_lookbehind=enable_lookbehind,
        lookbehind_mode=lookbehind_mode,
        seed=seed,
        play=play,
        normalize_text=normalize_text,
    )

    if output_filename and len(wav) > 0:
        sf.write(output_filename, wav, vt.sample_rate)
        print(f"[SUCCESS] Ses kaydedildi: {output_filename}")

    return wav


if __name__ == "__main__":
    text_okunacak = (
        "1. Türkiye Finans WorldCard (Dönem Borcu: 3.450 TL) "
        "2. Türkiye Finans Platinum Kart (Dönem Borcu: 2.800 TL) "
        "Ayrıca, ödemeyi hangi hesaptan yapacağınızı da belirtin."
    )

    speak(text_okunacak)







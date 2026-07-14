import os
import soundfile as sf
from Trendyol_TTS.voxtrendyol import VoxTrendyol


if __name__ == "__main__":
    text_okunucak = "Mastercard kredi kartımda bu ay ödemem gereken 18.450 TL borç bulunuyor ve son ödeme tarihini kaçırmamak için ödeme planımı buna göre hazırladım. Zero Kartımda 7.980 TL dönem borcu görünüyor; bu tutarın tamamını son ödeme tarihinden önce kapatmayı planlıyorum. Happy Temassız Kartımda ise 2.340 TL borç bulunuyor, tüm kart borçlarımı düzenli takip ederek gecikme faizi oluşmasını önlemeye özen gösteriyorum."

    # Klonlanacak ses
    ref_ses = r"voices/zeynep.wav" if os.path.exists(r"voices/zeynep.wav") else None

    # Klonlanacak sesin içindeki transkript (Ne söylediği)
    ref_metin = (
        "Hayvanlar için hayatlarını tehlikeye atmaya hazır insanlar var; aynı zamanda tuhaf, kötü ve çirkin."
        if ref_ses
        else None
    )

    vt = VoxTrendyol("Trendyol_TTS")
    # Hem asenkron oynatır (play=True), hem TextBuffer/RingBuffer kullanır, hem de wav döner
    wav = vt.smart_generate_streaming(
        text=text_okunucak,
        ref_audio=ref_ses,
        prompt_audio=ref_ses,
        prompt_text=ref_metin,
        cfg_value=2.2,
        inference_timesteps=6,  # Düşük olmasının sebebi güçsüz bir bilgisayarda takılmadan sistemin test edilmesi için
        chunk_duration_ms=300,
        seed=42,
        play=True,
        lookbehind_mode="anchor",
    )

    # Elde edilen wav çıktısını kaydet
    output_filename = "voice_design.wav"
    sf.write(output_filename, wav, vt.sample_rate)
    print(f"Kayıt tamamlandı: {output_filename}")

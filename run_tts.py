import os
import soundfile as sf
from Trendyol_TTS.voxtrendyol import VoxTrendyol


if __name__ == "__main__":
    text_okunucak = """Merhaba, ben dijital bankacılık asistanınız. Size hesaplarınız, kartlarınız, para transferleriniz, ödemeleriniz ve diğer bankacılık işlemleriniz konusunda hızlı, güvenli ve kolay bir deneyim sunmak için buradayım. Hesap bakiyenizi görüntüleyebilir, son hesap hareketlerinizi inceleyebilir, IBAN bilgilerinizi paylaşabilir, FAST, EFT ve havale işlemleri hakkında bilgi verebilir, kredi kartı ekstrenizi görüntülemenize yardımcı olabilir, otomatik ödeme talimatlarınızı kontrol edebilir, yatırım ürünleri, döviz kurları, vadeli hesaplar ve kredi başvuruları hakkında genel bilgilendirme sağlayabilirim.

Örneğin, hesabınızda 128.450,75 TL kullanılabilir bakiye bulunuyorsa bunu görüntüleyebilir, son 90 gün içerisinde gerçekleşen 248 işlemi listeleyebilir, bugün saat 14:37'de tamamlanan 3.250 TL tutarındaki FAST transferinizin durumunu kontrol edebilir veya son ödeme tarihi 28 Ağustos 2026 olan 6.845,90 TL tutarındaki kredi kartı borcunuzu görüntüleyebilirim. Ayrıca aylık 15.000 TL tutarında düzenli birikim planı oluşturmanız, %42,50 faiz oranına sahip vadeli hesap seçeneklerini karşılaştırmanız ya da güncel USD, EUR ve GBP kurlarını incelemeniz konusunda da size yardımcı olabilirim.

Bana yapmak istediğiniz işlemi günlük konuşma diliyle yazmanız yeterlidir. Örneğin; 'Hesabımda ne kadar para var?', 'Son 25 işlemimi göster.', '8.500 TL'yi Ahmet Yılmaz'a FAST ile gönder.', 'Kredi kartımın kullanılabilir limiti ne kadar?', 'Bu ay toplam kaç TL harcadım?', 'Son 6 ayda market harcamalarımı listele.', '5.000 USD bozdurursam hesabıma kaç TL geçer?', '250.000 TL'yi 32 gün vadeli hesaba yatırırsam tahmini getirisi ne olur?', 'Yeni bir kredi kartına başvurmak istiyorum.', 'En yakın ATM nerede?' veya 'IBAN bilgilerimi paylaş.' gibi taleplerinizi doğrudan iletebilirsiniz. Talebinizi anladıktan sonra size uygun işlem adımlarını açık ve anlaşılır şekilde sunarım.

Güvenliğiniz ve kişisel verilerinizin korunması önceliğimizdir. Bu nedenle internet bankacılığı şifrenizi, mobil bankacılık giriş bilgilerinizi, kart numaranızın tamamını, CVV güvenlik kodunuzu, SMS ile gönderilen 6 haneli doğrulama kodlarını, mobil onay bildirimlerini veya diğer gizli bilgilerinizi hiçbir koşulda paylaşmamanız gerekir. Kimlik doğrulaması gerektiren işlemlerde sizi yalnızca bankamızın güvenli doğrulama ekranlarına yönlendiririm ve güvenlik standartlarımız doğrultusunda işlemlerinizi korumaya devam ederim.

Size haftanın 7 günü, günün 24 saati destek sağlayabilirim. Hesaplarınız, kartlarınız, kredileriniz, yatırım işlemleriniz, fatura ödemeleriniz, para transferleriniz, döviz işlemleriniz ve bankacılık ürünleriyle ilgili merak ettiğiniz konularda bilgi alabilir; işlem süreçleri hakkında destek isteyebilir veya uygulamanın kullanımıyla ilgili sorularınızı iletebilirsiniz. Amacım, karmaşık bankacılık işlemlerini sizin için daha anlaşılır hale getirmek, ihtiyaçlarınıza en kısa sürede uygun çözümleri sunmak ve güvenli bir dijital bankacılık deneyimi yaşamanıza yardımcı olmaktır. Hazırsanız talebinizi yazmanız yeterli. Size memnuniyetle yardımcı olmaya hazırım.
"""

    # Klonlanacak ses
    ref_ses = (
        r"voices/ceren.wav"
        if os.path.exists(r"voices/ceren.wav")
        else None
    )

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
        cfg_value=2.8,
        inference_timesteps=8,
        chunk_duration_ms=90,
        seed=42,
        play=True,
        lookbehind_mode="anchor",
    )

    # Elde edilen wav çıktısını kaydet
    output_filename = "voice_design.wav"
    sf.write(output_filename, wav, vt.sample_rate)
    print(f"Kayıt tamamlandı: {output_filename}")

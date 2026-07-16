# 🚀 TTS (Text-to-Speech) Akışkan Çıkarım (Streaming) Sistemi

Bu proje, **VoxCPM** ve **Trendyol TTS** modelleri temel alınarak geliştirilmiş, düşük gecikmeli (low-latency) ve yüksek verimli (high-throughput) bir ses sentezleme sistemidir. Geleneksel TTS sistemlerinin aksine, metnin tamamının sentezlenmesini beklemeden ilk anlamlı cümleyi üretir üretmez akıtmaya (streaming) başlar.

## 🌟 Öne Çıkan Özellikler

- **Minimum Time-To-First-Audio (TTFA):** İlk sesi alma süresi sıfıra yakındır. Token-by-token işleme ile asenkron ses akışı sağlar.
- **Yüksek Eşzamanlılık (High Concurrency):** Ağır yapay zeka işlemleri arka plan iş parçacığı havuzlarına devredilerek FastAPI ana döngüsünün bloklanması engellenir.
- **GPU Havuzu (Resource Pooling):** Birden fazla GPU yatay ölçekte yönetilir (`VoxCPMEnginePool`). Gelen istekler boştaki en uygun GPU'ya atanır.
- **Kesintisiz Çalışma (CPU Fallback):** Eğer tüm GPU'lar meşgulse ve kuyruk sınırı aşılırsa, istekler şeffaf bir şekilde ultra hızlı CPU tabanlı **Piper TTS** motoruna yönlendirilir.
- **Maksimum Donanım Verimliliği:** Önceden ayrılmış (pre-allocated) RingBuffer ve vektörize bellek operasyonları ile Garbage Collection duraklamaları önlenir.

---

## 🛠️ Sistem Gereksinimleri

- **İşletim Sistemi:** Windows / Linux / macOS
- **Python Sürümü:** Python 3.8+ (3.10+ önerilir)
- **Donanım:** 
  - Gelişmiş performans için NVIDIA GPU (CUDA destekli).
  - CPU modunda Piper ile çalışabilmek için modern çok çekirdekli bir işlemci.
- **Araçlar:** Git, pip

---

## 🚀 Kurulum (Adım Adım)

Sistemi en ufak ayrıntısına kadar eksiksiz kurmak için aşağıdaki adımları sırasıyla uygulayın:

### Adım 1: Proje Dizinine Giriş Yapın
Terminal (veya Komut İstemcisi / PowerShell) üzerinden projenin bulunduğu dizine gidin:
```bash
cd yol/TTS
```

### Adım 2: Sanal Ortam (Virtual Environment) Oluşturma (Önerilen)
Bağımlılıkların sisteminizdeki diğer projelerle çakışmaması için bir sanal ortam oluşturun ve aktifleştirin:

**Windows için:**
```bash
python -m venv venv
venv\Scripts\activate
```
**Linux / macOS için:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Adım 3: Otomatik Kurulum Betiğini Çalıştırma
Sistem, kurulum işlemlerini tek tıkla halledebilmeniz için `setup_env.py` adlı bir betik ile gelmektedir. Bu betiği çalıştırdığınızda şu adımlar otomatik olarak gerçekleşir:
1. `requirements.txt` içindeki temel bağımlılıklar (FastAPI, uvicorn, websockets, numpy, vb.) indirilir.
2. Yerel `VoxCPM` motoru ve kendi bağımlılıkları yüklenir.
3. Hugging Face üzerinden **Trendyol-TTS** model ağırlıkları kontrol edilir ve yoksa `Trendyol-TTS` klasörüne indirilir (`model.safetensors`, `audiovae.pth`).
4. **Piper Fallback** motoru için gerekli ONNX ve JSON dosyaları kontrol edilir ve yoksa `Piper-TTS-Model` klasörüne indirilir.

Betiği çalıştırmak için şu komutu girin:
```bash
python setup_env.py
```
> **Not:** İndirme işlemi internet hızınıza ve modellerin boyutuna (örn. Trendyol-TTS) bağlı olarak birkaç dakika sürebilir. Komut çıktısında `[+] Kurulum işlemleri tamamlandı!` mesajını görmeden işlemi yarıda kesmeyin.

---

## ⚙️ Yapılandırma (`tts_config.json`)

Sisteminizin davranışını `tts_config.json` dosyası üzerinden en ince detayına kadar ayarlayabilirsiniz:

- **model**:
  - `model_path`: Kullanılacak TTS modelinin yerel dizini (Varsayılan: `"./Trendyol-TTS"`).
  - `inference_timesteps`: Sentezleme kalitesi ve hızı arasındaki dengeyi belirler (Varsayılan: `8`).
  - `adaptive_timesteps`: Metin uzunluğuna göre dinamik adım atılıp atılmayacağı.
  - `cfg_value`: Modelin Classifier-Free Guidance değeri (Varsayılan: `2.8`).
- **streaming**:
  - `chunk_duration_ms`: İstemciye gönderilecek her bir ses paketinin milisaniye cinsinden süresi.
  - `output_format`: Çıktı formatı, genellikle `"pcm16_le"` (16-bit PCM Little Endian).
  - `enable_lookbehind`: Sentezleme akıcılığını artırmak için önceki sesi referans alma durumu.
  - `lookbehind_mode`: Bağlantı noktası referans modu (`"anchor"` vb.).
- **text_processing**:
  - `sentence_delimiters`: Metni cümlelere ayırmak için kullanılan noktalama işaretleri (`.?!…,;\n`).
  - `flush_timeout_ms`: Tam bir cümle oluşmadığında bile bekleyen metnin zorla sentezlenmesi için geçmesi gereken süre (ms).
  - `min_chars`: Bir ses akışının başlaması için geçmesi gereken minimum karakter sayısı.
- **system**:
  - `voxcpm_gpu_ids`: Modele ayrılacak GPU ID'leri dizisi (Örn: `[0]` veya birden fazla GPU için `[0, 1]`).
  - `use_torch_compile`: PyTorch derlemesini aktifleştirerek performansı artırır (GPU gerektirir).
  - `piper_fallback_enabled`: CPU fallback motorunun aktif olup olmayacağı (`true`/`false`).
  - `piper_fallback_queue_threshold`: GPU kuyruğunda kaç istek biriktiğinde sistemin otomatik olarak Piper CPU motoruna döneceği (Varsayılan: `10`).
- **api**: API güvenliği için CORS ayarlarını (`cors_allowed_origins`, `cors_allowed_methods`, `cors_allowed_headers`) barındırır.

---

## 🏃‍♂️ Sistemi Başlatma ve Kullanım

### Python İçerisinden Doğrudan Kullanım (Asenkron Oynatma)
Sistemi doğrudan bir Python projesine entegre etmek ve arka planda gecikmesiz olarak çalıştırmak oldukça basittir. Tıpkı `run_tts.py` içerisinde olduğu gibi `VoxTrendyol` sarmalayıcısını kullanabilirsiniz:

```python
import os
import soundfile as sf
from Trendyol_TTS.voxtrendyol import VoxTrendyol

# 1. Modeli Başlat (Ağırlıkları ve sample rate'i otomatik yükler)
vt = VoxTrendyol(model_path="Trendyol-TTS")

# 2. Üretilecek Metin ve Klonlanacak Ses (Referans)
text_to_speak = "Mastercard kredi kartımda bu ay ödemem gereken 18.450 TL borç bulunuyor ve son ödeme tarihini kaçırmamak için ödeme planımı buna göre hazırladım. Zero Kartımda 7.980 TL dönem borcu görünüyor; bu tutarın tamamını son ödeme tarihinden önce kapatmayı planlıyorum. Happy Temassız Kartımda ise 2.340 TL borç bulunuyor, tüm kart borçlarımı düzenli takip ederek gecikme faizi oluşmasını önlemeye özen gösteriyorum."

    # Klonlanacak ses yolu (Sadece .wav dosyasının ismni değişitirerek yeni sesler eklenebilir)
    ref_ses = r"voices/zeynep.wav" if os.path.exists(r"voices/zeynep.wav") else None

    # Klonlanacak sesin içindeki transkript (Ne söylediği) (Ses değişitirirken burayı da değiştirmeyi unutmayın)
    ref_metin = (
        "Hayvanlar için hayatlarını tehlikeye atmaya hazır insanlar var; aynı zamanda tuhaf, kötü ve çirkin."
        if ref_ses
        else None
    )


# 3. Akışı ve Oynatmayı Başlat
wav_output = vt.smart_generate_streaming(
    text=text_to_speak,
    ref_audio=ref_audio,      # Klonlanacak referans ses dosyası
    prompt_audio=ref_audio,   # Duygu ve tonlama için referans ses
    prompt_text=ref_text,     # Referans sesin transkripti
    cfg_value=2.0,            # Modelin tonlama sadakati
    inference_timesteps=6,    # Hız/Kalite ayarı
    chunk_duration_ms=200,    # Streaming parça boyutu (ms)
    seed=42,                  # Tutarlılık
    play=True,                # Ses oynatma
    lookbehind_mode="anchor", # Ses akışında tutarlılık (Diksiyon,duygu vb.)
)

# 4. (Opsiyonel) Çıktıyı Sonradan Kaydedin
sf.write("voice_design.wav", wav_output, vt.sample_rate)
```

**Özetle Çağrı Akışı:** Gelen metin `TextBuffer` ile anında işlenir. Ses üretildikçe `RingBuffer` aracılığıyla bellek dostu bir şekilde ana thread'de `sounddevice.RawOutputStream` ile hoparlöre iletilir ve sonunda birleştirilmiş ses dizisi geri döner.

---

## 🏗️ Mimari Geliştirmelerimiz ve Teknik Detaylar

Sistem mimarisi, kurumsal standartlarda OOP ve SOLID prensiplerine sadık kalınarak tasarlanmıştır. Geliştirdiğimiz özgün mimarinin detayları şunlardır:

### 1. Bellek ve O(1) İşlem Optimizasyonları
- **RingBuffer (RAM Dostu Tampon):** `streaming.py` içindeki RingBuffer dinamik genişleme yapmaz, bellek adreslemesi baştan sabit yapılır. Head/Tail işaretçileri kaydırılarak tam olarak **O(1)** hızında bellek erişimi sunar. Kapasite `capacity=32` olarak sınırlandırılmıştır. Ses donanımdan çaldıkça kuyruk kontrollü olarak boşaltılır ve asenkron yapının akıcılığı bellek şişmeden (memory leak) korunur.
- **Vektörize AudioFormat Dönüşümü:** Ses genlik sınırlama (clipping) ve `PCM16 Little-Endian` dönüşümleri, ağır Python `for` döngülerinden arındırılarak NumPy tabanlı SIMD operasyonları ile donanım hızında (**O(N)** optimum) gerçekleştirilir.
- **Akıllı Metin Tamponu ve Cümle Bölme (TextBuffer):** LLM çıktılarından gelen harf/kelime token'ları dinamik olarak yakalanıp O(1) maliyetle işlenir:
  - **Noktalama Bazlı Bölme:** `.`, `?`, `!`, `\n` gibi cümle sonu işaretlerine göre doğal konuşma parçalarına ayrılır.
  - **`min_chars` Koruması:** Çok kısa kelimelerin (ör. "Hmm.") tek başına gönderilip bağlamdan kopmasını engeller.
  - **`flush_timeout` (Zaman Aşımı):** Eğer LLM belirli bir süre kelime üretmezse, bekleyen eksik metinler zorla fırlatılıp üretime gönderilir.

### 2. Asenkron Kesintisiz Oynatma ve Yumuşak Geçişler
- **Stutter-Free Playback:** Mimarimiz `sounddevice.RawOutputStream` ve bir arka plan iş parçacığı (Thread) kullanarak sesi üretildiği anda GPU hızını kilitlemeden arka planda pürüzsüz bir şekilde çalmaya başlar.
- **Overlap-Add Süzgeçleri:** Küçük parçalar (chunk) halinde üretilen ses blokları art arda eklenirken oluşan rahatsız edici çıt/pıt (pop/click) seslerini önlemek için blokların uçları üst üste bindirilir ve son derece yumuşak akustik geçişler sağlanır.

### 3. Çoklu GPU Havuzu (Resource Pooling)
5'e kadar (veya daha fazla) GPU'yu yatay olarak yönetebilen **Object Pool Pattern** (`VoxCPMEnginePool`) uygulanmıştır. Gelen bir istek asenkron bir kuyruk (`asyncio.Queue`) üzerinden bekletilmeden boştaki uygun GPU'ya kilitlenir. Hiçbir istek birbirini bloke etmez.

### 4. Dinamik Fallback Mekanizması
Diyelim ki sistemde yüksek bir yük var, GPU'ların tamamı meşgul ve kuyruk konfigürasyondaki eşik değerini (`piper_fallback_queue_threshold` = 10) geçti. Bu durumda sistem, istek reddetmek yerine talebi eşzamanlı olarak CPU üzerinde çalışan ultra hızlı **Piper TTS** motoruna yönlendirir. İstemci bu yönlendirmeyi hissetmez ve sunucu her koşulda "hizmet kesintisi" (Denial of Service) olmadan çalışmaya devam eder.

---

## 📊 Vanilla VoxCPM ve Sistemimiz Arasındaki Karşılaştırma

Aşağıdaki tablo, standart VoxCPM (Vanilla) ile bizim geliştirdiğimiz Streaming TTS sisteminin performans, mimari ve kaynak yönetimi açısından sayısal ve dilsel karşılaştırmasını sunmaktadır.

| Özellik / Metrik | Standart VoxCPM (Vanilla) | Bizim Sistemimiz (Streaming TTS) |
| :--- | :--- | :--- |
| **Zaman / Gecikme (TTFA)** | Temel streaming destekler, ancak LLM entegrasyonu için optimize edilmemiştir (cümle bekler). | **Sıfıra yakın (O(1)) TTFA.** `TextBuffer` ile LLM'den gelen tokenlar anında yakalanıp işlenir. |
| **GPU Kaynak Yönetimi** | Tekil model tahsisi. (vLLM gibi harici sunucularla ölçeklenir). | **Yerleşik GPU Havuzu (`VoxCPMEnginePool`).** Dinamik yük dengeleme ile O(1) hızında en uygun GPU'ya atama. |
| **Kesintisiz Çalışma (Fallback)** | Yok. GPU tamamen dolduğunda yeni istekler bekler veya reddedilir. | **Otomatik CPU Fallback.** GPU kuyruğu dolduğunda istekler şeffafça ultra hızlı **Piper TTS**'e yönlendirilir. |
| **Bellek Yönetimi (RAM)** | Standart Python objeleri ve dinamik tensor tahsisi (GC baskısı yaratabilir). | **Sabit kapasiteli (Capacity=32) RingBuffer.** Dinamik genişleme yok, %100 bellek dostu, Garbage Collection duraksamaları (O(1) adresleme) engellendi. |
| **Audio Format Dönüşümü** | Çoğunlukla standart döngülerle veya PyTorch içi operasyonlarla PCM dönüşümü. | **Vektörize SIMD Operasyonları (O(N)).** Ağır `for` döngüleri yerine NumPy tabanlı clipping ve PCM16 dönüşümü. |
| **Eşzamanlılık (Concurrency)** | Temel düzeyde, asenkron çalışma dış kütüphanelere (FastAPI, vLLM) bırakılır. | **Thread-Pool Mimarisi.** Ağır AI hesaplamaları arka plana itilir, ana FastAPI döngüsü asla bloklanmaz. |
| **Akustik Pürüzsüzlük** | Standart chunk birleştirme (Bazen çıt/pıt sesleri yapabilir). | **Overlap-Add Süzgeçleri.** Chunk uçları üst üste bindirilerek akustik pop/click sesleri engellenir. |
| **Metin Tamponlama (Buffering)** | Manuel olarak metni bölüp göndermeniz gerekir. | **Akıllı Metin Tamponu (`min_chars`, `flush_timeout`).** Noktalama bazlı anında bölme ve gecikme-kontrollü zorla fırlatma. |

### Sistemimizin Temel Farkları (Özet)

1. **Uçtan Uca LLM Uyumluluğu:** Standart VoxCPM, bütün bir metni veya belirli parçaları alarak sentez yapar. Bizim sistemimiz ise, bir LLM'den harf harf veya kelime kelime dökülen (streaming) metinleri **TextBuffer** ile yakalar, anlamlı cümle/parçacık oluştuğu anda (veya zaman aşımı `flush_timeout` dolduğunda) senteze gönderir.
2. **Kendi İçinde Ölçeklenebilirlik (Auto-Scaling & Fallback):** Sistemimiz harici bir Load Balancer'a ihtiyaç duymadan kendi **GPU havuzunu** yönetir ve darboğaz (bottleneck) anında **CPU (Piper TTS)** motoruna geçiş yaparak kesintisiz hizmet (**%99.9 Uptime** garantisi) sunar. Standart VoxCPM'de bu tür bir hata toleransı yoktur.
3. **Donanım Seviyesinde Optimizasyon:** Ağır veri kopyalama işlemlerinden kaçınmak için geliştirdiğimiz sabit kapasiteli **RingBuffer** ve **Vektörize Numpy İşlemleri**, bellek sızıntılarını (memory leak) tamamen önler ve I/O işlemlerini mikro saniyeler seviyesine çeker. 
4. **Kusursuz Ses Akıcılığı:** Chunk'lar halinde üretilen seslerin birleşim yerlerindeki bozulmaları önlemek için özel **Overlap-Add** teknikleri entegre edilmiştir. Bu, üretilen sesin tamamen doğal ve stuttersız (takılmasız) duyulmasını sağlar.

---

## 🔮 Yol Haritası ve Gelecek Geliştirmeler

Projeyi daha da ileriye taşımak için mimarimize eklenecek sıradaki özellikler şunlardır:

1. **Kümelenmiş ve Dağıtık Yapı (Kubernetes & Redis):**
   - GPU havuzunun tek bir makineyle kısıtlanmasını önlemek için pod bazlı HPA (Horizontal Pod Autoscaling) entegrasyonuna geçiş.
   - İstek yönetiminin ve GPU kilit mekanizmalarının Redis Pub/Sub üzerinden sunucu bağımsız (stateless) bir şekilde dağıtılması.
2. **Akıllı Ses Önbellekleme (Semantic Audio Caching):**
   - Çok sık sorulan veya üretilen standart cümlelerin, vektörel karşılıkları (embeddings) bulunarak Redis/NoSQL üzerinde ses paketleri olarak saklanması. İstek geldiğinde aynı cümlenin yapay zeka tarafından işlenmeden **O(1)** hızla istemciye gönderilmesi.
3. **Alternatif İletişim Protokolleri (gRPC & HTTP/2):**
   - WebSocket akışına alternatif olarak, özellikle kurumsal .NET ve Java mikroservis mimarileriyle %100 uyumlu ve daha hafif (low overhead) iletişim kurmak için **Protocol Buffers (gRPC)** adaptörünün sisteme eklenmesi.
4. **Gelişmiş Kimlik Doğrulama ve Güvenlik:**
   - İstek kısıtlamaları (rate-limiting) ve OAuth2/JWT gibi kurumsal yetkilendirme standartlarının direkt Dependency Injection katmanına API Gateway entegrasyonu olarak kazandırılması.

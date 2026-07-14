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

### Sunucuyu Başlatmak
Tüm kurulum ve yapılandırma adımlarından sonra servisi ayağa kaldırmak için ana dizindeyken şu komutu çalıştırın:
```bash
python -m service.main
```
Bu komut, yapılandırmanıza göre modelleri belleğe yükleyecek (GPU ve CPU) ve FastAPI & WebSocket sunucusunu başlatacaktır.

### İstemci (Client) ile Bağlantı Kurmak
Servis ayağa kalktıktan sonra, WebSocket üzerinden asenkron metin gönderip, ses verisini stream (akış) olarak alabilirsiniz. Proje dizininde veya farklı bir projede örnek bir bağlantı için `client.py` dosyasını inceleyebilirsiniz.

Sistem, istemci ile **Multiplexed WebSockets** üzerinden konuşur:
1. **Text Frame (JSON):** Kontrol mesajları, metadata, bağlantı durumu ve cümle sonu bildirimleri.
2. **Binary Frame (Raw Bytes):** Saf, Little-Endian formatta `PCM16` ses verisi taşır. Bu sayede iOS, Android, .NET veya Java gibi farklı istemciler bu byteları alıp doğrudan donanım ses kuyruğuna yazabilirler.

### Python İçerisinden Doğrudan Kullanım (Asenkron Oynatma)
Sistemi doğrudan bir Python projesine entegre etmek ve arka planda gecikmesiz olarak çalıştırmak oldukça basittir. Tıpkı `run_tts.py` içerisinde olduğu gibi `VoxTrendyol` sarmalayıcısını kullanabilirsiniz:

```python
import os
import soundfile as sf
from Trendyol_TTS.voxtrendyol import VoxTrendyol

# 1. Modeli Başlat (Ağırlıkları ve sample rate'i otomatik yükler)
vt = VoxTrendyol(model_path="Trendyol-TTS")

# 2. Üretilecek Metin ve Klonlanacak Ses (Referans)
text_to_speak = "Hayvanlar için hayatlarını tehlikeye atmaya hazır insanlar var; aynı zamanda tuhaf, kötü ve çirkin."
ref_audio = "ceren.wav/ceren.wav"
ref_text = "Hayvanlar için hayatlarını tehlikeye atmaya hazır insanlar var."

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

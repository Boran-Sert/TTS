import json
import numpy as np

try:
    from websockets.sync.client import connect
except ImportError:
    raise ImportError("Lütfen websockets kütüphanesini güncelleyin: pip install --upgrade websockets>=11.0")

class TTSClient:
    def __init__(self, uri="ws://127.0.0.1:8000/ws/tts"):
        """
        Trendyol TTS WebSocket API İstemcisi
        
        Kullanım:
            client = TTSClient("ws://127.0.0.1:8000/ws/tts")
            
            # Normal mod (tek seferde tüm sesi alma)
            wav = client.generate("Merhaba dünya!", streaming=False)
            
            # Akış (streaming) modu
            for chunk in client.generate("Akış testi...", streaming=True):
                print(chunk.shape)
        """
        self.uri = uri
        self.sample_rate = 24000  # Varsayılan değer, stream_start event'i ile güncellenir
        
    def generate(self, text: str, streaming: bool = False):
        """
        Sesi sentezler. streaming=True ise generator döndürür (chunk'lar halinde),
        streaming=False ise tek bir numpy array (pcm16) döndürür.
        """
        if streaming:
            return self._generate_streaming(text)
        else:
            chunks = list(self._generate_streaming(text))
            if len(chunks) == 0:
                return np.array([], dtype=np.int16)
            return np.concatenate(chunks)
            
    def _generate_streaming(self, text: str):
        # WebSocket üzerinden senkron (blocking) iletişim
        with connect(self.uri) as ws:
            ws.send(json.dumps({"text": text}))
            while True:
                message = ws.recv()
                
                # Kontrol (Text) mesajları
                if isinstance(message, str):
                    event_data = json.loads(message)
                    event_type = event_data.get("event")
                    
                    if event_type == "stream_start":
                        self.sample_rate = event_data.get("sample_rate", 24000)
                    elif event_type == "stream_end":
                        break
                    elif event_type == "error":
                        raise RuntimeError(f"Sunucu Hatası: {event_data.get('message')}")
                        
                # Ses (Binary) mesajları
                elif isinstance(message, bytes):
                    # PCM16 LE formatındaki veriyi Numpy int16 array'ine çeviriyoruz
                    audio_np = np.frombuffer(message, dtype=np.int16)
                    yield audio_np

if __name__ == "__main__":
    # Örnek Kullanım
    import soundfile as sf
    
    print("TTSClient başlatılıyor...")
    client = TTSClient("ws://127.0.0.1:8000/ws/tts")
    
    print("1. Streaming (Akış) Modu Test Ediliyor...")
    chunks = []
    for chunk in client.generate(text="Bu, istemci üzerinden akışlı olarak sentezlenen bir test cümlesidir.", streaming=True):
        print(f"  -> {len(chunk)} sample alındı.")
        chunks.append(chunk)
    
    if chunks:
        wav_stream = np.concatenate(chunks)
        sf.write("streaming_test.wav", wav_stream, client.sample_rate)
        print("  => Kaydedildi: streaming_test.wav\n")
    
    print("2. Normal (Toplu) Mod Test Ediliyor...")
    wav_normal = client.generate(text="Bu da aynı istemcinin tek seferde tüm sesi döndürdüğü senaryodur.", streaming=False)
    sf.write("normal_test.wav", wav_normal, client.sample_rate)
    print("  => Kaydedildi: normal_test.wav")

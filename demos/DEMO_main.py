import asyncio
import io
import logging
import time

import numpy as np
import scipy.io.wavfile
from fastapi import FastAPI
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
import demos.DEMO_trendyol_default_tts as trendyol_tts
import demos.DEMO_piper_tts as piper_tts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("TTS_Gateway")

logger.info("Sistem başlatılıyor, yapay zeka modelleri hafızaya yükleniyor...")
start_load = time.time()


elapsed_load = time.time() - start_load
logger.info(
    f"Tüm modeller {elapsed_load:.2f} saniyede yüklendi ve istek kabul etmeye hazır."
)

app = FastAPI(
    title="TTS DEMO",
    version="1.1.0",
)


class TTSRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


async def trendyol_async_generator(text: str):
    """
    Trendyol (VoxCPM) modeli senkron (blocking) bir generator'dır.
    FastAPI Event Loop'unun kilitlenmemesi (binlerce isteği kaldırabilmesi) için
    her bir ses parçasının üretimi arka plan thread'ine (to_thread) devredilir.
    """
    iterator = trendyol_tts.audio_stream_generator(text)
    while True:
        try:
            # Modelin bir sonraki parçayı üretmesini ThreadPool'da bekle
            chunk = await asyncio.to_thread(next, iterator)
            yield chunk
        except StopIteration:
            break
        except Exception as e:
            logger.error(f"Trendyol Stream Hatası: {e}")
            break


@app.post("/tts/trendyol")
async def generate_trendyol(request: TTSRequest):
    logger.info(
        f"Trendyol İsteği Alındı | Uzunluk: {len(request.text)} karakter | Metin: {request.text[:50]}..."
    )

    start_time = time.time()
    
    # Modelin tüm metni işlemesi için ThreadPool'a atıyoruz
    raw_bytes = await asyncio.to_thread(trendyol_tts.generate_trendyol_audio, request.text)

    if not raw_bytes:
        return Response(content=b"", media_type="audio/wav")

    # Bytes verisini güvenli bir şekilde WAV formatına paketle
    audio_data = np.frombuffer(raw_bytes, dtype=np.int16)
    wav_buffer = io.BytesIO()
    scipy.io.wavfile.write(wav_buffer, trendyol_tts.synthesizer.tts_model.sample_rate, audio_data)
    wav_buffer.seek(0)
    
    elapsed = time.time() - start_time
    logger.info(f"Trendyol İsteği Tamamlandı | Süre: {elapsed:.2f}s | Dosya Boyutu: {len(raw_bytes)} bytes")

    return Response(content=wav_buffer.read(), media_type="audio/wav", headers={"Content-Disposition": 'attachment; filename="trendyol_audio.wav"'})


@app.post("/tts/piper")
async def generate_piper(request: TTSRequest):
    logger.info(
        f"Piper İsteği Alındı | Uzunluk: {len(request.text)} karakter | Metin: {request.text[:50]}..."
    )

    start_time = time.time()

    # Model inference CPU/GPU'yu kilitlediği için işlemi ThreadPool'a yolluyoruz (Asenkron mimari)
    raw_bytes = await asyncio.to_thread(piper_tts.generate_piper_audio, request.text)

    # Bytes verisini güvenli bir şekilde WAV formatına paketle
    audio_data = np.frombuffer(raw_bytes, dtype=np.int16)
    wav_buffer = io.BytesIO()
    scipy.io.wavfile.write(wav_buffer, piper_tts.sample_rate, audio_data)
    wav_buffer.seek(0)

    elapsed = time.time() - start_time
    logger.info(
        f"Piper İsteği Tamamlandı | Süre: {elapsed:.2f}s | Dosya Boyutu: {len(raw_bytes)} bytes"
    )

    return Response(content=wav_buffer.read(), media_type="audio/wav", headers={"Content-Disposition": 'attachment; filename="piper_audio.wav"'})


if __name__ == "__main__":
    import uvicorn

    logger.info("Uvicorn Asenkron Web Sunucusu başlatılıyor (http://0.0.0.0:8000)")
    # Uvicorn varsayılan olarak ThreadPool yetenekleriyle gelir.
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .dependencies import engine_container
from .routers import websocket
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from .logger import setup_logger

logger = setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    print("Initialize TTS Engines...")
    await engine_container.initialize()
    print("Engines are ready.")
    
    logger.info("[WARM-UP] Model ısındırma (compile & memory allocation) süreci başlıyor. Lütfen bekleyin (bu işlem uzun sürebilir)...")
    try:
        engine = await engine_container.get_engine()
        if engine:
            warmup_text = "Merhaba. Bu sistemin tamamen ısınması, CUDA bellek tahsisinin yapılması ve PyTorch grafiklerinin derlenmesi için hazırlanan uzunca bir ısındırma metnidir. Müşteriler geldiğinde hızlı yanıt alabilmeleri için bu süreç mecburi ve gereklidir."
            async for chunk in engine.generate_stream(warmup_text):
                pass  # Gelen sesleri (chunk) çöpe atıyoruz, amacımız modelin içinden verinin geçmesi.
            logger.info("[WARM-UP] Isındırma işlemi başarıyla tamamlandı! Sistem tam hızda kullanıma hazır.")
    except Exception as e:
        logger.error(f"[WARM-UP] Isındırma sırasında hata oluştu: {e}")
    finally:
        if 'engine' in locals() and engine:
            await engine_container.release_engine(engine)

    yield
    print("Shutting down TTS Engines...")

app = FastAPI(
    title="TTS API",
    version="2.0",
    lifespan=lifespan
)

@app.middleware("http")
async def global_exception_handler_middleware(request: Request, call_next):
    """Bütün HTTP hatalarını yakalayıp standart JSON formatında loglar ve döner."""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Sunucu Hatası ({request.url.path}): {e}\n{error_details}")
        
        # .NET Middleware için özel JSON hata formatı
        return JSONResponse(
            status_code=500,
            content={
                "event": "error",
                "error_type": type(e).__name__,
                "message": str(e),
                "path": request.url.path
            }
        )

from VoxCPM.src.voxcpm import config_instance

app.add_middleware(
    CORSMiddleware,
    allow_origins=config_instance.api.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=config_instance.api.cors_allowed_methods,
    allow_headers=config_instance.api.cors_allowed_headers,
)

app.include_router(websocket.router)
from .routers import http_tts
app.include_router(http_tts.router)

from fastapi.responses import HTMLResponse
import os

@app.get("/", response_class=HTMLResponse)
async def serve_web_ui():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        return HTMLResponse(content=f"Error loading UI: {e}", status_code=500)

if __name__ == "__main__":
    uvicorn.run("service.main:app", host="0.0.0.0", port=8000, log_level="info")

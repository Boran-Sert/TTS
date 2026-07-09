import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..dependencies import engine_container
from ..engines.base import ITTSEngine
from ..logger import get_logger

router = APIRouter()
logger = get_logger()

@router.websocket("/ws/tts")
async def websocket_tts_endpoint(websocket: WebSocket):
    """Multiplexed WebSocket endpoint separating JSON events and binary PCM16 audio."""
    await websocket.accept()
    logger.info("[WebSocket] Yeni istemci bağlandı.")
    
    engine: ITTSEngine = None
    try:
        data = await websocket.receive_json()
        text = data.get("text", "")
        
        logger.debug(f"[WebSocket] İstemciden JSON alındı: text='{text[:50]}...'")

        if not text:
            logger.warning("[WebSocket] İstek reddedildi: Text boş.")
            await websocket.send_json({"event": "error", "message": "Text is required"})
            await websocket.close(code=1008)
            return

        engine = await engine_container.get_engine()
        logger.debug(f"[WebSocket] Motor tahsis edildi: {engine.name}")
        
        first_chunk = True

        async for chunk in engine.generate_stream(text):
            if first_chunk:
                logger.debug(f"[WebSocket] Stream başlıyor. Format: pcm16_le, Sample Rate: {chunk.sample_rate}")
                await websocket.send_json({
                    "event": "stream_start",
                    "engine": engine.name,
                    "format": "pcm16_le",
                    "sample_rate": chunk.sample_rate
                })
                first_chunk = False

            if chunk.data and len(chunk.data) > 0:
                data_len = len(chunk.data)
                logger.debug(f"[WebSocket] -> Client'a {data_len} bytes gönderiliyor.")
                await websocket.send_bytes(chunk.data)
                
            if chunk.is_sentence_final:
                logger.debug(f"[WebSocket] Cümle {chunk.sentence_index} tamamlandı sinyali gönderiliyor.")
                await websocket.send_json({
                    "event": "sentence_complete",
                    "sentence_index": chunk.sentence_index
                })

        logger.info("[WebSocket] Tüm akış tamamlandı, bağlantı kapatılıyor.")
        await websocket.send_json({"event": "stream_end"})
        await websocket.close(code=1000)
        
    except WebSocketDisconnect:
        pass 
    except Exception as e:
        try:
            await websocket.send_json({
                "event": "error", 
                "error_type": type(e).__name__,
                "message": str(e)
            })
            await websocket.close(code=1011)
        except:
            pass
    finally:
        if engine:
            await engine_container.release_engine(engine)

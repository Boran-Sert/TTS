import os
import tempfile
import wave
import traceback
import base64
from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from ..dependencies import engine_container
from ..logger import get_logger

router = APIRouter()
logger = get_logger()

class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = "tr"
    output_path: Optional[str] = None
    
class ChatRequest(BaseModel):
    userMessage: str
    language: Optional[str] = "tr"

def cleanup_temp_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.error(f"Failed to cleanup temp file {path}: {e}")

@router.get("/health")
async def health():
    return {"status": "healthy", "tts_model": "VoxCPM / Piper (FastAPI)"}

@router.post("/tts/synthesize")
async def synthesize(request: TTSRequest, background_tasks: BackgroundTasks):
    engine = await engine_container.get_engine()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_path = temp_file.name
        
    try:
        # We need to collect chunks and save to wav
        sample_rate = 24000
        
        # Open wav file
        with wave.open(temp_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2) # 16-bit
            first_chunk = True
            
            async for chunk in engine.generate_stream(request.text):
                if first_chunk:
                    sample_rate = chunk.sample_rate
                    wav_file.setframerate(sample_rate)
                    first_chunk = False
                
                if chunk.data:
                    wav_file.writeframes(chunk.data)
                    
        background_tasks.add_task(cleanup_temp_file, temp_path)
        return FileResponse(temp_path, media_type="audio/wav", filename="output.wav")
        
    except Exception as e:
        cleanup_temp_file(temp_path)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})
    finally:
        await engine_container.release_engine(engine)

@router.post("/tts/synthesize-to-file")
async def synthesize_to_file(request: TTSRequest):
    if not request.output_path:
        return JSONResponse(status_code=400, content={"success": False, "error": "output_path is required"})
        
    engine = await engine_container.get_engine()
    
    try:
        sample_rate = 24000
        with wave.open(request.output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            first_chunk = True
            
            async for chunk in engine.generate_stream(request.text):
                if first_chunk:
                    sample_rate = chunk.sample_rate
                    wav_file.setframerate(sample_rate)
                    first_chunk = False
                
                if chunk.data:
                    wav_file.writeframes(chunk.data)
                    
        return {
            "success": True,
            "output_path": request.output_path,
            "text": request.text,
            "language": request.language,
            "file_size": os.path.getsize(request.output_path)
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})
    finally:
        await engine_container.release_engine(engine)

@router.get("/tts/info")
async def tts_info():
    return {
        "backend": "VoxCPM / Piper (FastAPI Engine Container)",
        "status": "active"
    }

@router.post("/ai/chat")
async def ai_chat(request: ChatRequest, background_tasks: BackgroundTasks):
    # Same logic as /tts/synthesize, just mapping different fields
    tts_req = TTSRequest(text=request.userMessage, language=request.language)
    return await synthesize(tts_req, background_tasks)

@router.post("/ai/chat-stream")
async def ai_chat_stream(request: ChatRequest):
    logger.info(f"[AI-CHAT-STREAM] User message: {request.userMessage}")
    engine = await engine_container.get_engine()
    
    async def generate_audio_stream():
        try:
            # First yield wav header
            # But wait, streaming in HTTP usually means raw bytes or wav?
            # The original Flask implementation yielded the wav header from Coqui, then raw bytes.
            # Coqui yielded the header in the first chunk. Our engines yield raw PCM16.
            # So we need to generate a fake WAV header if the client expects a WAV file stream.
            
            # Simple WAV header generator for streaming
            def create_wav_header(sample_rate=24000, channels=1, bits_per_sample=16):
                # 0x7FFFFFFF is a dummy large size for unknown length stream
                byte_rate = sample_rate * channels * (bits_per_sample // 8)
                header = b'RIFF' + (0x7FFFFFFF).to_bytes(4, 'little') + b'WAVE'
                header += b'fmt ' + (16).to_bytes(4, 'little')
                header += (1).to_bytes(2, 'little') # PCM
                header += channels.to_bytes(2, 'little')
                header += sample_rate.to_bytes(4, 'little')
                header += byte_rate.to_bytes(4, 'little')
                header += (channels * (bits_per_sample // 8)).to_bytes(2, 'little')
                header += bits_per_sample.to_bytes(2, 'little')
                header += b'data' + (0x7FFFFFFF).to_bytes(4, 'little')
                return header
                
            first_chunk = True
            
            async for chunk in engine.generate_stream(request.userMessage):
                if first_chunk:
                    yield create_wav_header(sample_rate=chunk.sample_rate)
                    first_chunk = False
                    
                if chunk.data:
                    yield chunk.data
        except Exception as e:
            logger.error(f"[AI-CHAT-STREAM] Error: {e}")
            traceback.print_exc()
        finally:
            await engine_container.release_engine(engine)
            
    text_encoded = base64.b64encode(request.userMessage.encode('utf-8')).decode('ascii')
    
    return StreamingResponse(
        generate_audio_stream(),
        media_type='audio/wav',
        headers={
            'Content-Disposition': 'inline; filename="response.wav"',
            'X-AI-Response-Base64': text_encoded
        }
    )

import asyncio
from typing import AsyncGenerator, Callable, Any
from .streaming import AudioChunk

async def async_generate_stream(
    generator_func: Callable[..., Any], 
    *args, 
    **kwargs
) -> AsyncGenerator[AudioChunk, None]:
    """
    Kullanım:
    async for chunk in async_generate_stream(model.generate_stream, text, config):
        await websocket.send_bytes(chunk.data)
    """

    gen = generator_func(*args, **kwargs)

    while True:
        try:
            chunk = await asyncio.to_thread(next, gen, None)
            if chunk is None:
                break
            yield chunk
        except Exception as e:
            # Hatalar middleware tarafından ele alınması için yukarı fırlatılır
            raise e

import asyncio
import time
import cProfile
import pstats
import io
import websockets
import json

async def simulate_client(client_id, uri, text):
    """Simulates a single client connecting to the WebSocket and receiving audio."""
    start_time = time.time()
    first_chunk_time = None
    total_bytes = 0
    
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({"text": text}))
            
            while True:
                try:
                    message = await websocket.recv()
                    
                    if isinstance(message, str):
                        event_data = json.loads(message)
                        if event_data.get("event") == "stream_end":
                            break
                    elif isinstance(message, bytes):
                        if first_chunk_time is None:
                            first_chunk_time = time.time()
                        total_bytes += len(message)
                except websockets.ConnectionClosed:
                    break
                    
        end_time = time.time()
        ttfa = (first_chunk_time - start_time) * 1000 if first_chunk_time else 0
        total_time = end_time - start_time
        
        return {
            "id": client_id,
            "ttfa_ms": ttfa,
            "total_time_s": total_time,
            "bytes_received": total_bytes
        }
    except Exception as e:
        print(f"Client {client_id} error: {e}")
        return None

async def run_benchmark(concurrent_clients=5):
    """Runs a load test with multiple concurrent WebSocket clients."""
    uri = "ws://127.0.0.1:8000/ws/tts"
    test_text = "Performans testi için kullanılan standart bir cümledir. Bu cümle sistemin ne kadar hızlı yanıt verdiğini ölçecektir."
    
    print(f"Starting benchmark with {concurrent_clients} concurrent clients...")
    
    tasks = [simulate_client(i, uri, test_text) for i in range(concurrent_clients)]
    
    start_wall = time.time()
    results = await asyncio.gather(*tasks)
    end_wall = time.time()
    
    valid_results = [r for r in results if r is not None]
    
    if not valid_results:
        print("All clients failed. Ensure the server is running.")
        return
        
    avg_ttfa = sum(r["ttfa_ms"] for r in valid_results) / len(valid_results)
    avg_time = sum(r["total_time_s"] for r in valid_results) / len(valid_results)
    
    print("\n--- Benchmark Results ---")
    print(f"Total Wall Time: {end_wall - start_wall:.2f} s")
    print(f"Successful Clients: {len(valid_results)}/{concurrent_clients}")
    print(f"Average Time to First Audio (TTFA): {avg_ttfa:.2f} ms")
    print(f"Average Total Generation Time: {avg_time:.2f} s")
    print("-------------------------\n")

def profile_benchmark():
    """Runs the benchmark under cProfile for deep algorithmic profiling."""
    pr = cProfile.Profile()
    pr.enable()
    
    asyncio.run(run_benchmark(concurrent_clients=2))
    
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumtime')
    ps.print_stats(20) # Top 20 time-consuming functions
    
    print("--- Top CPU Time Profiling ---")
    print(s.getvalue())

if __name__ == "__main__":
    profile_benchmark()

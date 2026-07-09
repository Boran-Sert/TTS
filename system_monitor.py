import psutil

try:
    import GPUtil
except ImportError:
    GPUtil = None

import os


def get_system_stats() -> str:
    """Sadece bu Python sürecinin (process) CPU ve RAM kullanımını döndürür."""
    process = psutil.Process(os.getpid())

    # Sadece bu sürecin (programın) kullandığı RAM
    mem_info = process.memory_info()
    ram_used_mb = mem_info.rss / (1024 * 1024)

    # Sadece bu sürecin CPU kullanımı
    cpu_usage = process.cpu_percent(interval=None)

    stats = f"Uygulama RAM: {ram_used_mb:.1f} MB | CPU: %{cpu_usage:.1f}"

    # GPU
    if GPUtil:
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                stats += f" | GPU: %{gpu.load * 100:.1f} (VRAM: {gpu.memoryUsed}MB/{gpu.memoryTotal}MB)"
        except Exception:
            pass

    return stats

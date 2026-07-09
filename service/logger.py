import logging
import os
import sys
from logging.handlers import RotatingFileHandler

_logger_initialized = False

def setup_logger():
    global _logger_initialized
    if _logger_initialized:
        return logging.getLogger("TTS_SYSTEM")

    logger = logging.getLogger("TTS_SYSTEM")
    logger.setLevel(logging.DEBUG)  # Debug seviyesinde tüm ince detayları alacağız.
    
    # Propagate false to prevent duplicate logs if root logger has handlers
    logger.propagate = False

    # Logs klasörünü oluştur
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "tts_processing.log")

    # Formatter: [Tarih-Saat] [Seviye] [Modül] - Mesaj
    formatter = logging.Formatter(
        fmt="[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(name)s:%(module)s:%(funcName)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File Handler - 5MB max size, 5 backups
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Konsolu çok boğmamak için INFO seviyesi
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _logger_initialized = True
    logger.info(f"Profesyonel logger sistemi başlatıldı. Log dosyası: {log_file}")
    
    return logger

def get_logger():
    global _logger_initialized
    if not _logger_initialized:
        return setup_logger()
    return logging.getLogger("TTS_SYSTEM")

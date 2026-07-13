import json
import os
from threading import Lock
from typing import List
from pydantic import BaseModel, Field

CONFIG_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "tts_config.json")
)

class ModelConfig(BaseModel):
    model_path: str = Field(default="./Trendyol-TTS")
    inference_timesteps: int = Field(default=8)
    adaptive_timesteps: bool = Field(default=False)
    adaptive_timesteps_short: int = Field(default=6)
    adaptive_timesteps_long: int = Field(default=12)
    cfg_value: float = Field(default=2.0)
    min_len: int = Field(default=2)
    max_len: int = Field(default=4096)
    retry_badcase: bool = Field(default=False)
    retry_badcase_max_times: int = Field(default=3)
    retry_badcase_ratio_threshold: float = Field(default=6.0)
    streaming_prefix_len: int = Field(default=4)

class StreamingConfigModel(BaseModel):
    chunk_duration_ms: int = Field(default=200)
    output_format: str = Field(default="pcm16_le")
    enable_lookbehind: bool = Field(default=True)
    lookbehind_mode: str = Field(default="strict")

class TextProcessingConfig(BaseModel):
    sentence_delimiters: str = Field(default=".?!…\n")
    flush_timeout_ms: float = Field(default=300.0)
    min_chars: int = Field(default=5)

class SystemConfig(BaseModel):
    voxcpm_gpu_ids: List[int] = Field(default_factory=lambda: [0])
    use_torch_compile: bool = Field(default=False)
    piper_fallback_enabled: bool = Field(default=True)
    piper_fallback_queue_threshold: int = Field(default=10)

class ApiConfig(BaseModel):
    cors_allowed_origins: List[str] = Field(default_factory=lambda: ["*"])
    cors_allowed_methods: List[str] = Field(default_factory=lambda: ["*"])
    cors_allowed_headers: List[str] = Field(default_factory=lambda: ["*"])

class AppConfig(BaseModel):
    model: ModelConfig
    streaming: StreamingConfigModel
    text_processing: TextProcessingConfig
    system: SystemConfig
    api: ApiConfig

class ConfigLoader:
    """Singleton configuration loader."""
    _instance = None
    _lock = Lock()
    _config: AppConfig = None

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigLoader, cls).__new__(cls)
                cls._instance._load_config()
            return cls._instance

    def _load_config(self):
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._config = AppConfig(**data)
        except Exception as e:
            # Fallback to default if not found or corrupted
            print(f"[UYARI] {CONFIG_FILE_PATH} okunamadı ({e}), varsayılan ayarlara dönülüyor.")
            self._config = AppConfig(
                model=ModelConfig(),
                streaming=StreamingConfigModel(),
                text_processing=TextProcessingConfig(),
                system=SystemConfig(),
                api=ApiConfig()
            )

    @property
    def config(self) -> AppConfig:
        return self._config

# Global instance for O(1) imports
config_instance = ConfigLoader().config

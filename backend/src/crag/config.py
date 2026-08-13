from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CRAG_", extra="ignore")

    data_dir: Path = Path(".data")
    runtime: Literal["deterministic", "ollama"] = "deterministic"
    ollama_url: str = "http://127.0.0.1:11434"
    chat_model: str = "qwen3.5:4b-q4_K_M"
    embed_model: str = "qwen3-embedding:0.6b"
    ollama_context_size: int = 8192
    ollama_output_tokens: int = 1024
    ollama_seed: int = 42
    ollama_gpu_layers: int = -1
    ollama_keep_alive: str = "10m"
    ollama_timeout_seconds: float = 180.0
    structured_repair_attempts: int = 1
    max_upload_mb: int = 50
    max_corrections: int = 1
    context_chunks: int = 6
    frontend_origin: str = "http://localhost:5173"

    @property
    def database_path(self) -> Path:
        return self.data_dir / "crag.sqlite3"

    @property
    def upload_dir(self) -> Path:
        return self.data_dir / "uploads"


def get_settings() -> Settings:
    return Settings()

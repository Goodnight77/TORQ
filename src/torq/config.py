"""Runtime settings loaded from the environment / .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    # LLM (DeepSeek, OpenAI-compatible)
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-reasoner"

    # Vector DB (Qdrant)
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # Data locations
    manuals_dir: Path = ROOT / "data" / "manuals"
    history_file: Path = ROOT / "data" / "history" / "repairs.json"
    scenarios_file: Path = ROOT / "data" / "scenarios" / "scenarios.json"

    # Collections
    manuals_collection: str = "torq_manuals"
    history_collection: str = "torq_history"

    # Embedding model (fastembed, runs locally; swap later if needed)
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # Retrieval
    top_k: int = 4


settings = Settings()

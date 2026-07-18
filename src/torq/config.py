"""Runtime settings loaded from the environment / .env file."""

import sys
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

    # Twilio (WhatsApp/SMS dispatch). Empty -> in-app fallback.
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = ""

    # MQTT (machine fault events). Public broker by default; $0, no auth.
    mqtt_broker_url: str = "broker.hivemq.com"
    mqtt_port: int = 1883
    mqtt_topic: str = "torq/demo/faults"

    # Work-order store. DATABASE_URL selects Postgres; SQLite is the local fallback.
    database_url: str = ""
    db_path: Path = ROOT / "data" / "torq.db"

    # Work-order PDF rendering
    font_path: Path = ROOT / "assets" / "fonts" / "Amiri-Regular.ttf"
    workorder_dir: Path = ROOT / "data" / "workorders"

    # Data locations
    manuals_dir: Path = ROOT / "data" / "manuals"
    history_file: Path = ROOT / "data" / "history" / "repairs.json"
    scenarios_file: Path = ROOT / "data" / "scenarios" / "scenarios.json"
    shifts_file: Path = ROOT / "data" / "shifts.json"
    eval_results_file: Path = ROOT / "data" / "eval_results.json"

    # Collections
    manuals_collection: str = "torq_manuals"
    history_collection: str = "torq_history"

    # Embedding models (fastembed, run locally; swap later if needed)
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    sparse_model: str = "Qdrant/bm25"
    rerank_model: str = "Xenova/ms-marco-MiniLM-L-6-v2"

    # Chunking (chonkie markdown-aware; keeps each fault-code section whole)
    manual_chunk_size: int = 1800

    # Retrieval
    top_k: int = 4
    use_hybrid: bool = True  # dense + BM25 sparse fused with RRF
    use_rerank: bool = True  # cross-encoder rerank of fused candidates

    # MCP knowledge server (agent connects over stdio).
    # use_mcp needs a networked Qdrant (qdrant_url): the embedded on-disk store is
    # single-process, so the server subprocess cannot open it while the parent holds
    # the lock. With no qdrant_url the agent skips MCP and retrieves directly.
    use_mcp: bool = True
    # Launch with the current interpreter (same venv as the parent) and skip
    # `uv run`, so each short-lived session does not re-resolve the environment.
    mcp_server_command: str = sys.executable
    mcp_server_args: list[str] = ["-m", "torq.mcp.server"]


settings = Settings()

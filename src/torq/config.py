"""Runtime settings loaded from the environment / .env file."""

import os
import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    # LLM (DeepSeek, OpenAI-compatible)
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-reasoner"
    # Model for the multi-step (ReAct) agent. Needs tool-calling support, which
    # the reasoner model lacks, so default to the chat model.
    agent_model: str = "deepseek-chat"
    agent_max_steps: int = 8  # reason/act ceiling; generous so the agent answers vs erroring into fallback

    @model_validator(mode="after")
    def _ensure_llm_key(self):
        if not self.llm_api_key:
            self.llm_api_key = os.environ.get("OPENAI_API_KEY", "")
        if not self.llm_api_key:
            import logging
            logging.warning(
                "No LLM API key found. "
                "Set LLM_API_KEY or OPENAI_API_KEY in your .env file. "
                "LLM-dependent features (diagnosis, translation) will fall back."
            )
        return self

    # Vector DB (Qdrant)
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # Twilio (WhatsApp/SMS dispatch). Empty -> in-app fallback.
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = ""

    # MQTT (machine fault events). Public broker by default; $0, no auth.
    # Public unauthenticated broker + fixed topic means anyone can publish fake
    # faults (each spawns a diagnosis run) or read plant data. For production,
    # point at an authenticated broker over TLS and set credentials.
    mqtt_broker_url: str = "broker.hivemq.com"
    mqtt_port: int = 1883
    mqtt_topic: str = "torq/demo/faults"

    # CORS: comma-separated origins or "*" for any (dev default).
    cors_origins: list[str] = ["*"]

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

    # Diagnosis cache: reuse a recent diagnosis for the same (machine, fault_code,
    # context) instead of re-calling the LLM. Cuts latency and cost on repeat
    # faults. 0 disables. Seconds.
    diagnose_cache_ttl: int = 600

    # LLM timeouts (seconds)
    llm_timeout: int = 60
    translate_timeout: int = 30

    # Fallbacks for external services (degrades MQTT/WhatsApp to in-app equivalents for demo safety)
    enable_fallbacks: bool = True

    # Retrieval
    top_k: int = 4
    use_hybrid: bool = True  # dense + BM25 sparse fused with RRF
    use_rerank: bool = True  # cross-encoder rerank of fused candidates

    # Composite ranking: nudge recent, proven fixes up. Applied client-side after
    # retrieval so it works in local mode too (a server >= v1.14 could do this in
    # a FormulaQuery/gauss_decay instead). Only affects docs that carry `date`.
    use_recency_boost: bool = True
    recency_half_life_days: int = 180
    recency_weight: float = 0.15  # weight on recency vs normalized semantic score
    outcome_weight: float = 0.10  # bonus for a "resolved" record

    # Dedup-on-write: instead of adding a near-identical repair as a new point,
    # merge it into the existing one (bump a counter, refresh timestamp). Keeps the
    # history collection from bloating with the same recurring fault.
    use_dedup: bool = True
    dedup_threshold: float = 0.90  # cosine similarity above which two repairs merge

    # Retrieval-eval golden set (query -> expected fault_code/machine)
    golden_file: Path = ROOT / "data" / "eval" / "golden.json"

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



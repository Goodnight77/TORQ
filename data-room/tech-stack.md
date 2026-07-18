# Tech Stack

Every component is proven and free-tier. Total infrastructure cost: $0.

| Layer | Choice | Why |
|-------|--------|-----|
| Language / env | Python 3.11+, `uv` | Fast, reproducible dependency management. |
| LLM | DeepSeek (OpenAI-compatible API) | Strong reasoning for diagnosis, low cost. |
| Embeddings | fastembed (BAAI/bge-small-en-v1.5) | Runs locally, no API key, zero cost. |
| Vector DB | Qdrant (cloud free tier, local fallback) | Semantic retrieval over manuals and history. |
| Knowledge access | Model Context Protocol (MCP) | On-premise trust boundary for proprietary data. |
| Events | MQTT (paho-mqtt, public broker) | Zero-touch fault trigger from PLC/SCADA. |
| Work-order PDF | fpdf2 + uharfbuzz + Amiri font | Trilingual output with Arabic RTL shaping. |
| Dispatch | Twilio WhatsApp/SMS, in-app fallback | Reaches technicians where they are. |
| Store | SQLite (Postgres-ready) | Zero-infra for the prototype. |
| API + dashboard | FastAPI + server-rendered HTML | REST plus a live supervisor/downtime dashboard, no build step. |

## Design principles

- Zero-touch: the pipeline is event-driven, not a chatbot.
- On-premise trust: proprietary manuals reached only through MCP.
- Demo cannot fail: every external integration has an in-app fallback.
- Grounded: diagnoses cite their manual and repair-history sources.

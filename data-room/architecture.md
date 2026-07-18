# Architecture

## Pipeline

```
Machine fault (MQTT)
      |
      v
 Diagnosis agent  <---- MCP knowledge server (manuals + history, on-premise)
   (DeepSeek + vector retrieval)
      |
      v
 Work order + trilingual PDF (EN/FR/AR)
      |
      v
 Supervisor approval queue (one tap)
      |
      v
 Skill-matched routing -> dispatch (WhatsApp/SMS, in-app fallback)
      |
      v
 Technician outcome -> knowledge base (re-indexed)  --> future diagnoses improve
      |
      v
 Downtime dashboard (time-to-diagnosis, MTTR, resolution rate)
```

## Components (src/torq)

- `events/` - MQTT listener (zero-touch trigger) and fault simulator.
- `ingest/` - manual + history ingestion; fastembed embeddings; Qdrant index; shared retrieval.
- `mcp/` - MCP server exposing `search_manuals` and `search_history` over stdio; data stays local.
- `agent/` - diagnosis agent (retrieval + DeepSeek), prompts, schemas.
- `workorder/` - work-order builder (EN deterministic, FR/AR via one LLM call) and PDF renderer (Arabic RTL).
- `dispatch/` - approval queue, skill-matched routing, Twilio/in-app notification.
- `knowledge/` - outcome feedback into the history knowledge base.
- `db/` - SQLite work-order store and metrics.
- `api/` - FastAPI REST API and a self-contained supervisor + downtime dashboard.
- `pipeline.py` - wires fault -> diagnosis -> work order -> approval.

## Data flow notes

- Proprietary manuals and history are served through MCP, so they never leave the
  plant network.
- Every external integration degrades gracefully: MQTT falls back to an in-app
  trigger, WhatsApp to an in-app notification, cloud Qdrant to local storage.
- Retrieval is grounded: diagnoses cite the manual sections and past repairs used.

## Maps to the scoring grid

- Measured impact: the dashboard surfaces time-to-diagnosis and MTTR live.
- Core AI: diagnosis + retrieval + MCP are the product, not a bolt-on.
- Working prototype: the full path runs end to end and is scripted for the demo.

# Demo Runbook

Scripted end-to-end demo. Rehearse once before going live. Every step has a
fallback so it cannot fail on stage.

## Prerequisites (once)

```bash
uv venv
uv sync
cp .env.example .env   # fill LLM + Qdrant keys (MQTT defaults are public)
```

## Pre-demo setup (2 minutes before)

```bash
uv run python scripts/run_brain.py     # index manuals + history into Qdrant
uv run python scripts/seed_demo.py     # populate dashboard metrics
uv run uvicorn torq.api.main:app       # start API + dashboard on :8000
```

Open http://localhost:8000 . Metrics tiles should already show numbers
(time-to-diagnosis, MTTR, resolution rate). In a second terminal start the
listener:

```bash
uv run python -m torq.events.listener  # zero-touch MQTT trigger
```

## The live moment (about 90 seconds)

1. "A machine faults. Nobody triggers anything." In a third terminal:
   ```bash
   uv run python -m torq.events.simulator
   ```
   (Fallback: click "Simulate fault" on the dashboard.)
2. Within seconds a new work order appears in PENDING APPROVAL with a
   grounded root cause.
3. "The supervisor just taps approve." Click **Approve**.
4. It moves to DISPATCHED, skill-matched to an on-shift technician. The work
   order is generated as a trilingual PDF, and the message is delivered in the
   technician's language (Arabic for Ahmed).
5. Click **Mark fixed** to record the outcome. Point out that this fix is now in
   the knowledge base and will be retrieved for the next identical fault.
6. Show the metrics tiles updating: time-to-diagnosis in seconds, not 30 minutes.

## Verification scripts (optional, for Q&A)

```bash
uv run python scripts/run_mcp.py    # plant knowledge served over MCP
uv run python scripts/run_pdf.py    # trilingual PDF render (EN/FR/AR)
uv run python scripts/run_loop.py   # full API loop, fault -> outcome -> metrics
```

## Fallbacks

- MQTT down: use the dashboard "Simulate fault" button.
- WhatsApp not configured: delivery uses the in-app channel (still visible).
- Network down: local Qdrant + seeded data allow an offline walkthrough.

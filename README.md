# TORQ - Fault-to-Fix Engine

**From fault code to fixed.**

TORQ is an event-driven predictive-maintenance pipeline. When a machine reports a
fault, an AI agent diagnoses it against OEM manuals and past repair history, then
produces a trilingual repair work-order for supervisor approval and dispatches it
to the right technician. Repair outcomes feed back to sharpen future diagnoses.

## Pipeline

```
Machine ──▶ TORQ Agent ──▶ Work Order ──▶ Supervisor ──▶ Technician
 (fault)   (Manuals +        (PDF)        (approval)     (dispatch)
            History)                                          │
   ▲                                                          │
   └───────────────────── outcome feedback ◀──────────────────┘
```

## Data

The knowledge base has two collections: OEM manuals (how to fix) and repair
history (what worked before). Demo data comes from:

- **Authored seed** - two machines (conveyor motor CM-350, packaging unit PK-9)
  with fault-code manuals and a few past repairs.
- **IBM AssetOpsBench-derived** - chiller, centrifugal pump, and air handling unit
  manuals plus history, grounded in real AssetOpsBench asset profiles, work orders,
  FMEA failure modes, and ISO-10816 vibration thresholds. Manual prose is
  synthesized (AssetOpsBench ships structured data, not prose manuals).
- **Self-improving loop** - resolved work orders are written back into the history
  collection, so future diagnoses reuse past fixes.

No proprietary or confidential documents are included.

## Quick start

TORQ uses [uv](https://docs.astral.sh/uv/) for environment and dependency management.

```bash
# 1. Create a virtual environment
uv venv

# 2. Sync dependencies (once any are declared)
uv sync

# 3. Add packages as you build
uv add <pkg>

# 4. Configure environment
cp .env.example .env   # then fill in values

# 5. Run (placeholders - commands land as the build progresses)
uv run torq ingest     # load manuals + history into the knowledge base
uv run torq serve      # start the API / event listener
```

## Status

Hackathon build. Scope and stack are intentionally lean and may evolve as the
project develops.

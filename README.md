# TORQ — Fault-to-Fix Engine

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

## Docs

- [docs/hackathon.md](docs/hackathon.md) — hackathon brief and goals
- [docs/TORQ_La_Scaloneta.md](docs/TORQ_La_Scaloneta.md) — team / concept writeup
- [docs/architecture.md](docs/architecture.md) — technical architecture
- [CLAUDE.md](CLAUDE.md) — working notes and conventions for contributors

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

# 5. Run (placeholders — commands land as the build progresses)
uv run torq ingest     # load manuals + history into the knowledge base
uv run torq serve      # start the API / event listener
```

## Status

Hackathon build. Scope and stack are intentionally lean and may evolve as the
project develops.

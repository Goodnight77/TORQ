# TORQ Data Room

Technical dossier for the Automate or Die jury. TORQ is a zero-touch
fault-to-fix engine for manufacturing: a machine fault triggers an AI agent that
diagnoses the root cause from plant manuals and repair history, generates a
trilingual work order, routes it for one-tap approval, and dispatches it to the
right technician. Outcomes feed back into a self-improving knowledge base.

## Contents

- `architecture.md` - components and end-to-end data flow
- `tech-stack.md` - the stack and why each piece was chosen ($0 infra)
- `impact-methodology.md` - how the impact numbers are derived
- `demo-script.md` - step-by-step live demo runbook (with fallbacks)
- `risk-register.md` - risks and graceful degradations
- `TORQ_deck.pptx` - the pitch deck

## Repository

Code: https://github.com/Goodnight77/TORQ
Run the whole pipeline locally with `uv`; see the repo README and `demo-script.md`.

## One-line pitch

TORQ turns the most expensive 30 minutes in manufacturing into 30 seconds.

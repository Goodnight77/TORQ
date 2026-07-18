# TORQ Web Dashboard

Supervisor-facing SPA for the TORQ Fault-to-Fix Engine (React + Vite).
Two surfaces: the **approval queue** (one-tap review/approve of AI-generated
work orders) and the **downtime dashboard** (time-to-diagnosis, time-to-fix,
resolution rate). Click a work-order ID to see the trilingual (EN/FR/AR) content.

## Run

Start the backend API first:

```bash
uv run uvicorn torq.api.main:app        # http://localhost:8000
```

Then the frontend:

```bash
cd web
npm install
npm run dev                             # http://localhost:5173
```

`/api` is proxied to the backend, so no CORS setup is needed in dev.

## Build

```bash
npm run build      # outputs web/dist
```

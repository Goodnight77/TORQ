<div align="center">
  <img src="assets/logos/inline_logo_dark_mode.svg" alt="TORQ" width="420">

  [![CI](https://github.com/Goodnight77/TORQ/actions/workflows/ci.yml/badge.svg)](https://github.com/Goodnight77/TORQ/actions/workflows/ci.yml)
  ![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
  ![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)
  ![Qdrant](https://img.shields.io/badge/Qdrant-hybrid_search-DC244C?logo=qdrant&logoColor=white)
  ![uv](https://img.shields.io/badge/uv-managed-DE5FE9?logo=uv&logoColor=white)
</div>

<p align="center">
  <a href="#why-torq">Why TORQ</a> ·
  <a href="#pipeline">Pipeline</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="#api">API</a> ·
  <a href="#development">Development</a>
</p>

## What is TORQ?

TORQ is an event-driven predictive-maintenance engine that turns machine faults into grounded diagnoses, approval-ready work orders, and technician dispatches.

A fault arrives over REST or MQTT. TORQ retrieves relevant OEM guidance and past repairs, asks an OpenAI-compatible model for a structured diagnosis, creates an English/French/Arabic work order, and queues it for supervisor review. Resolved repairs return to the knowledge base so the next diagnosis can reuse what worked.

## Why TORQ?

| Traditional maintenance flow | TORQ |
| --- | --- |
| Faults wait to be noticed and triaged | REST and MQTT fault ingestion starts the workflow immediately |
| Technicians search manuals and logs by hand | Dense + BM25 retrieval surfaces relevant guidance and repair history |
| Diagnosis quality depends on who is available | Structured, source-aware AI diagnosis creates a consistent starting point |
| Work orders are manually written and translated | Approval-ready EN/FR/AR work orders and PDFs are generated automatically |
| Dispatch is based on availability alone | On-shift technicians are matched by skill, then contacted in their preferred language |
| Repair knowledge disappears into notes | Successful outcomes are re-indexed for future diagnoses |

## Pipeline

A fault enters over MQTT or REST and leaves as a dispatched, approval-ready fix.
The diagnosis stage is a reasoning agent grounded in the plant's own documents,
and every external hop degrades to a local fallback so a live demo cannot hard-fail.

```mermaid
flowchart TB
    classDef ingress fill:#dbeafe,stroke:#2563eb,color:#172554
    classDef ai fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef ops fill:#ffe4e6,stroke:#e11d48,color:#881337
    classDef store fill:#e0e7ff,stroke:#4f46e5,color:#312e81
    classDef gate fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef fallback fill:#f1f5f9,stroke:#64748b,color:#334155,stroke-dasharray:4 3

    MQTT[/"MQTT fault event"/]:::ingress
    REST[/"REST POST /api/faults"/]:::ingress

    subgraph DIAG["Grounded diagnosis"]
      direction TB
      CACHE{"Diagnosis cache<br/>hit within TTL?"}:::gate
      AGENT{{"ReAct agent<br/>LangChain · LangGraph"}}:::ai
      TOOLS["Agent tools<br/>search_manuals · search_history"]:::ai
      subgraph RET["Hybrid retrieval, per tool call"]
        direction LR
        DENSE["Dense<br/>bge-small"]:::ai
        SPARSE["Sparse<br/>BM25"]:::ai
        RRF["RRF fusion"]:::ai
        RERANK["Cross-encoder<br/>rerank"]:::ai
        DENSE --> RRF
        SPARSE --> RRF
        RRF --> RERANK
      end
    end

    KB[("Qdrant<br/>manuals + repair history")]:::store

    MQTT --> CACHE
    REST --> CACHE
    CACHE -->|miss| AGENT
    AGENT <-->|reason / act loop| TOOLS
    TOOLS -->|"MCP on-premise boundary"| RET
    RET --> KB
    RERANK -->|"evidence + cited sources"| AGENT
    AGENT -->|structured Diagnosis| WO

    WO["Work order<br/>+ FR / AR translation"]:::ops
    PDF["Trilingual PDF<br/>Amiri · HarfBuzz shaping"]:::ops
    GATE{"Supervisor review"}:::gate
    ROUTE["Skill-matched<br/>technician routing"]:::ops
    DISP["WhatsApp / in-app dispatch"]:::ops
    OUT["Repair outcome"]:::ops
    DB[("SQLite / PostgreSQL")]:::store

    WO --> PDF
    WO --> GATE
    CACHE -.->|"hit: reuse, skip LLM"| WO
    GATE -->|reject| DB
    GATE -->|approve| ROUTE
    ROUTE --> DISP
    DISP --> OUT
    OUT --> DB
    OUT -->|"resolved fix re-indexed"| KB

    AGENT -.->|agent loop fails| ONESHOT["One-shot diagnosis"]:::fallback
    ONESHOT -.->|LLM / retrieval down| STUB["Manual-review stub<br/>never 500s"]:::fallback
    ONESHOT -.-> WO
    STUB -.-> WO

    SSE(["Live SSE feed → dashboard"]):::ingress
    CACHE -.-> SSE
    WO -.-> SSE
    DISP -.-> SSE
```

Legend: solid = happy path, dashed = graceful-degradation fallbacks and the live
activity stream. The three retrieval boxes run inside every agent tool call, and
the same reason/act loop can search again with a refined query before answering.

## Features

### Retrieval-grounded diagnosis

TORQ combines dense embeddings and BM25 sparse search in Qdrant, fuses the results with reciprocal rank fusion, and optionally reranks them with a cross-encoder. Diagnoses use both OEM manual excerpts and machine-specific repair history before falling back to broader historical matches.

### Reasoning agent with graceful degradation

Diagnosis is a real ReAct (reason/act) agent built on LangChain and LangGraph, not a single prompt. It decides when to call `search_manuals` versus `search_history`, can refine its query and search again, and records an ordered investigation trail that ships with the work order. Retrieval flows through the MCP knowledge server, so proprietary manuals are read behind an on-premise boundary and never leave the plant.

The path degrades in three tiers so a live demo cannot hard-fail: the multi-step agent falls back to a single-shot diagnosis if the loop errors, then to a manual-review stub if the model or retrieval is unreachable, always returning a work order instead of a 500. A short-TTL diagnosis cache reuses a recent result for a repeated fault and skips the LLM call entirely.

### Approval-first work orders

Each diagnosis becomes a persistent work order with root cause, repair steps, parts, tools, safety warnings, confidence, and source references. English content is deterministic; French and Arabic translations are produced in one additional model call. PDFs support shaped, right-aligned Arabic using the bundled Amiri font.

### Smart technician dispatch

Fault-code prefixes map to maintenance skills, and TORQ selects an on-shift technician with the closest match. Approved work orders can be delivered through Twilio WhatsApp, with an in-app delivery response when Twilio is not configured.

### Closed-loop learning

When a repair is marked resolved, TORQ records the actual fix, technician notes, and time to repair. The result is appended to repair history and the history index is rebuilt, making the successful fix available to later diagnoses.

### Supervisor and operations views

The built-in dashboard supports fault simulation, approval, rejection, resolution, and downtime metrics. A separate React dashboard adds work-order details, multilingual content, PDF downloads, retrieval evaluation charts, and an editable ROI calculator.

### Multiple integration surfaces

Use TORQ through its REST API, MQTT listener, React dashboard, or MCP server. The MCP interface exposes manual and repair-history search as standalone tools for compatible AI clients.

## Architecture

Module-level map of the codebase: interfaces feed one orchestrator, which drives the knowledge, work-order, and dispatch layers over shared storage. Nodes link to source.

```mermaid
flowchart TD

subgraph group_interfaces["Interfaces"]
  node_http_api["FastAPI API &amp; dashboard<br/>[main.py]"]
  node_api_routes["API routes<br/>route handlers<br/>[routes.py]"]
  node_react_dashboard["React dashboard<br/>Vite client<br/>[App.jsx]"]
  node_mqtt_listener["MQTT listener<br/>event adapter<br/>[listener.py]"]
  node_mcp_server["MCP server<br/>AI integration<br/>[server.py]"]
end

subgraph group_core["Core workflow"]
  node_pipeline{{"Fault pipeline<br/>orchestrator<br/>[pipeline.py]"}}
end

subgraph group_knowledge["Knowledge &amp; AI"]
  node_diagnosis_agent{{"Structured diagnosis<br/>LLM agent<br/>[diagnose.py]"}}
  node_manual_ingest["Manual ingestion<br/>knowledge ingestion<br/>[manuals.py]"]
  node_history_ingest["History ingestion<br/>knowledge ingestion<br/>[history.py]"]
  node_retrieval["Hybrid retrieval<br/>knowledge search<br/>[connectors.py]"]
  node_feedback["Outcome feedback<br/>learning loop<br/>[feedback.py]"]
end

subgraph group_operations["Work orders &amp; dispatch"]
  node_workorder_generation["Work-order generation<br/>document builder<br/>[generate.py]"]
  node_pdf_renderer["Multilingual PDF renderer<br/>document renderer<br/>[pdf.py]"]
  node_approval{{"Approval lifecycle<br/>workflow gate<br/>[approval.py]"}}
  node_routing["Technician routing<br/>dispatch matcher<br/>[routing.py]"]
  node_notification["WhatsApp notification<br/>delivery adapter<br/>[notify.py]"]
end

subgraph group_storage["Persistence"]
  node_qdrant[("Qdrant collections<br/>vector store<br/>[docker-compose.yml]")]
  node_database[("Operational database<br/>SQLite / PostgreSQL<br/>[session.py]")]
end

node_react_dashboard -->|"/api"| node_http_api
node_http_api -->|"serves"| node_api_routes
node_api_routes -->|"submits faults"| node_pipeline
node_mqtt_listener -->|"fault events"| node_pipeline
node_mcp_server -->|"knowledge search"| node_retrieval
node_pipeline -->|"retrieves evidence"| node_retrieval
node_retrieval -->|"hybrid search"| node_qdrant
node_manual_ingest -->|"manual collection"| node_qdrant
node_history_ingest -->|"history collection"| node_qdrant
node_pipeline -->|"fault + evidence"| node_diagnosis_agent
node_diagnosis_agent -->|"structured diagnosis"| node_workorder_generation
node_workorder_generation -->|"persists pending order"| node_database
node_workorder_generation -->|"renders"| node_pdf_renderer
node_api_routes -->|"review decision"| node_approval
node_approval -->|"on approval"| node_routing
node_routing -->|"assigned technician"| node_notification
node_api_routes -->|"resolved outcome"| node_feedback
node_feedback -->|"reindex history"| node_history_ingest
node_api_routes -->|"work orders &amp; metrics"| node_database

click node_http_api "https://github.com/goodnight77/torq/blob/main/src/torq/api/main.py"
click node_api_routes "https://github.com/goodnight77/torq/blob/main/src/torq/api/routes.py"
click node_react_dashboard "https://github.com/goodnight77/torq/blob/main/web/src/App.jsx"
click node_mqtt_listener "https://github.com/goodnight77/torq/blob/main/src/torq/events/listener.py"
click node_mcp_server "https://github.com/goodnight77/torq/blob/main/src/torq/mcp/server.py"
click node_pipeline "https://github.com/goodnight77/torq/blob/main/src/torq/pipeline.py"
click node_diagnosis_agent "https://github.com/goodnight77/torq/blob/main/src/torq/agent/diagnose.py"
click node_manual_ingest "https://github.com/goodnight77/torq/blob/main/src/torq/ingest/manuals.py"
click node_history_ingest "https://github.com/goodnight77/torq/blob/main/src/torq/ingest/history.py"
click node_retrieval "https://github.com/goodnight77/torq/blob/main/src/torq/mcp/connectors.py"
click node_qdrant "https://github.com/goodnight77/torq/blob/main/docker-compose.yml"
click node_workorder_generation "https://github.com/goodnight77/torq/blob/main/src/torq/workorder/generate.py"
click node_pdf_renderer "https://github.com/goodnight77/torq/blob/main/src/torq/workorder/pdf.py"
click node_approval "https://github.com/goodnight77/torq/blob/main/src/torq/dispatch/approval.py"
click node_routing "https://github.com/goodnight77/torq/blob/main/src/torq/dispatch/routing.py"
click node_notification "https://github.com/goodnight77/torq/blob/main/src/torq/dispatch/notify.py"
click node_feedback "https://github.com/goodnight77/torq/blob/main/src/torq/knowledge/feedback.py"
click node_database "https://github.com/goodnight77/torq/blob/main/src/torq/db/session.py"

classDef toneNeutral fill:#f8fafc,stroke:#334155,stroke-width:1.5px,color:#0f172a
classDef toneBlue fill:#dbeafe,stroke:#2563eb,stroke-width:1.5px,color:#172554
classDef toneAmber fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
classDef toneMint fill:#dcfce7,stroke:#16a34a,stroke-width:1.5px,color:#14532d
classDef toneRose fill:#ffe4e6,stroke:#e11d48,stroke-width:1.5px,color:#881337
classDef toneIndigo fill:#e0e7ff,stroke:#4f46e5,stroke-width:1.5px,color:#312e81
classDef toneTeal fill:#ccfbf1,stroke:#0f766e,stroke-width:1.5px,color:#134e4a
class node_http_api,node_api_routes,node_react_dashboard,node_mqtt_listener,node_mcp_server toneBlue
class node_pipeline toneAmber
class node_diagnosis_agent,node_manual_ingest,node_history_ingest,node_retrieval,node_feedback toneMint
class node_workorder_generation,node_pdf_renderer,node_approval,node_routing,node_notification toneRose
class node_qdrant,node_database toneIndigo
```


## Quick start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with Docker Compose for the containerized stack
- [Python 3.11+](https://www.python.org/) and [uv](https://docs.astral.sh/uv/) for local development
- Node.js 18+ and npm only for the optional React dashboard

### Run the stack with Docker

Create the environment file once, then start the API and a local Qdrant instance with one command:

```bash
cp .env.example .env
# Add LLM_API_KEY to .env for live diagnosis
docker compose up --build
```

Open the dashboard at [localhost:8000](http://localhost:8000), the Swagger UI at [localhost:8000/docs](http://localhost:8000/docs), or the Qdrant dashboard at [localhost:6333/dashboard](http://localhost:6333/dashboard). The API reads configuration from `.env`, stores SQLite/work-order data under `data/`, and connects to Qdrant through the Compose network. Qdrant data persists in the `qdrant_data` Docker volume.

Stop the stack with `docker compose down`.

> Live fault submission requires a configured OpenAI-compatible model. The Docker stack does not mock diagnosis when `LLM_API_KEY` is unset.

### Run the no-key demo

The fastest way to exercise the complete workflow is the in-process demo. When `LLM_API_KEY` is unset, it uses a mocked diagnosis and does not call an external model.

```bash
git clone https://github.com/Goodnight77/TORQ.git
cd TORQ
uv sync --dev
uv run python scripts/run_loop.py
```

This runs fault submission → approval → dispatch → outcome feedback → metrics without starting a server.

### Run the live API locally

```bash
cp .env.example .env
# Add LLM_API_KEY to .env for live diagnosis
uv run uvicorn torq.api.main:app --reload
```

Open:

- Dashboard: [localhost:8000](http://localhost:8000)
- Swagger UI: [localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [localhost:8000/redoc](http://localhost:8000/redoc)

> Live fault submission requires a configured OpenAI-compatible model. Only `scripts/run_loop.py` provides the no-key mocked diagnosis.

### Run the React dashboard

With the API running in another terminal:

```bash
cd web
npm ci
npm run dev
```

Open [localhost:5173](http://localhost:5173). Vite proxies `/api` requests to the FastAPI server on port `8000`.

## Configuration

TORQ reads `.env` from the repository root. Most integrations are optional and have local fallbacks.

| Variable | Purpose | Default behavior |
| --- | --- | --- |
| `LLM_API_KEY` | Enables live diagnosis and FR/AR translation | No live fallback; the demo script mocks diagnosis |
| `LLM_BASE_URL` | OpenAI-compatible API endpoint | `https://api.deepseek.com` |
| `LLM_MODEL` | Model used for diagnosis and translation | `deepseek-reasoner` |
| `QDRANT_URL`, `QDRANT_API_KEY` | Connect to hosted Qdrant | Local on-disk Qdrant under `data/qdrant_storage/` |
| `DATABASE_URL` | Use PostgreSQL for work orders and machines | SQLite at `data/torq.db` |
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM` | Enable WhatsApp dispatch | In-app delivery response |
| `MQTT_BROKER_URL`, `MQTT_PORT`, `MQTT_TOPIC` | Configure machine fault events | Public HiveMQ demo broker and `torq/demo/faults` topic |

Retrieval models, collection names, paths, chunk size, result count, hybrid search, and reranking can also be overridden through environment variables defined in `src/torq/config.py`.

## Knowledge base

The repository intentionally does not include operational OEM manuals or repair logs. Add your own data before running live retrieval:

- Place top-level `.md` or `.txt` manuals in `data/manuals/`.
- Add repair records to `data/history/repairs.json`.
- Index both collections:

```bash
uv run python -m torq.ingest.manuals
uv run python -m torq.ingest.history
```

On first use, FastEmbed may download the configured embedding, sparse, and reranking models. Ingestion recreates each Qdrant collection from the source files.

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/machines` | List registered machines |
| `POST` | `/api/machines` | Register a machine |
| `POST` | `/api/faults` | Diagnose a fault and create a pending work order |
| `GET` | `/api/work-orders` | List work orders, optionally filtered by `status` |
| `GET` | `/api/work-orders/{id}` | Get a work order |
| `GET` | `/api/work-orders/{id}/pdf` | Generate or download its PDF |
| `POST` | `/api/work-orders/{id}/approve` | Route and dispatch an approved work order |
| `POST` | `/api/work-orders/{id}/reject` | Reject a work order |
| `POST` | `/api/work-orders/{id}/outcome` | Record repair results and feedback |
| `GET` | `/api/metrics` | Return workflow and downtime metrics |
| `GET` | `/api/eval` | Return precomputed retrieval evaluation results |

Example fault submission:

```bash
curl -X POST http://localhost:8000/api/faults \
  -H "Content-Type: application/json" \
  -d '{
    "fault_code": "E-471",
    "machine": "CM-350 Line 2",
    "context": "Motor tripped after several hours of operation."
  }'
```

## Development

### Useful commands

| Command | Purpose |
| --- | --- |
| `uv run python scripts/run_loop.py` | Run the mocked end-to-end API loop |
| `uv run python scripts/run_pdf.py` | Generate and validate a multilingual work-order PDF |
| `uv run python scripts/run_brain.py` | Ingest knowledge and diagnose the seeded scenarios |
| `uv run python scripts/run_action.py` | Exercise fault → approval → dispatch with live diagnosis |
| `uv run python scripts/run_mqtt.py` | Exercise the MQTT listener and simulator |
| `uv run python scripts/run_mcp.py` | Smoke-test MCP manual and history search tools |
| `uv run python scripts/eval_retrieval.py` | Compare dense, hybrid, and reranked retrieval |
| `uv run python scripts/eval_diagnosis.py` | Evaluate diagnoses with an LLM judge |

Commands other than the mocked loop and PDF smoke test may require indexed knowledge, live model credentials, or external services.

### Tests

```bash
uv run pytest tests/ -v
```

The test suite covers pipeline orchestration, database selection and compatibility, machine registration, API machine routes, and downtime metrics. GitHub Actions runs the PDF smoke test, end-to-end loop, and unit tests on Python 3.11 and 3.12 for pull requests to `main`.

## Project structure

```text
src/torq/
├── agent/          Structured diagnosis, prompts, and schemas
├── api/            FastAPI application, routes, and built-in dashboard
├── db/             SQLite/PostgreSQL persistence and metrics
├── dispatch/       Approval, technician routing, and notifications
├── events/         MQTT listener and fault simulator
├── ingest/         Manual/history ingestion and hybrid retrieval
├── knowledge/      Repair-outcome feedback loop
├── mcp/            MCP knowledge-search server
├── workorder/      Multilingual work-order and PDF generation
├── config.py       Environment-backed runtime settings
└── pipeline.py     End-to-end fault orchestration

web/                React + Vite supervisor dashboard
data/               Scenarios, technician shifts, and evaluation fixtures
scripts/            Demo, integration, PDF, and evaluation runners
tests/              Unit and API tests
assets/              Logos and PDF fonts
```

## Tech stack

| Layer | Technology |
| --- | --- |
| API and validation | FastAPI, Pydantic |
| Diagnosis agent | LangChain + LangGraph ReAct agent, OpenAI SDK, OpenAI-compatible endpoint (DeepSeek by default) |
| Retrieval | Qdrant, FastEmbed, dense (bge-small) + BM25, RRF, cross-encoder reranking |
| Events and tools | MQTT, MCP |
| Persistence | SQLite by default, optional PostgreSQL |
| Dispatch | Twilio WhatsApp with in-app fallback |
| Documents | fpdf2, HarfBuzz, Amiri font |
| Dashboard | React 18, Vite |
| Tooling | uv, pytest, GitHub Actions |

## Project status

TORQ is an active prototype built for demonstration and experimentation. The API currently has no authentication, CORS is open for local development, workflow processing is synchronous, and the default MQTT broker is public. Add production-grade identity, authorization, transport security, queues, retries, and observability before deploying it in an industrial environment.

"""Diagnosis agent: retrieve manual + history context, call the LLM, return a Diagnosis.

Retrieval goes through the MCP knowledge server (proving plant data stays
on-premise).  If the MCP server is unreachable the agent falls back to
calling ``ingest.search`` directly.
"""

import json
import logging
import time

from openai import OpenAI

from torq.agent.prompts import SYSTEM, build_user_prompt
from torq.agent.schemas import Diagnosis
from torq.config import settings
from torq.ingest import search  # direct fallback
from torq.mcp.client import mcp_available, mcp_search_history, mcp_search_manuals

log = logging.getLogger(__name__)


# ── context formatting ───────────────────────────────────────────────────────


def _join_manuals(hits: list[dict]) -> tuple[str, list[str]]:
    parts, sources = [], []
    for h in hits:
        # MCP returns {"source", "text"}; direct returns {"source", "document"}
        src = h.get("source", "manual")
        text = h.get("text") or h.get("document", "")
        parts.append(f"[{src}] {text}")
        if src not in sources:
            sources.append(src)
    return "\n\n".join(parts), sources


def _join_history(hits: list[dict]) -> tuple[str, list[str]]:
    parts, sources = [], []
    for m in hits:
        # MCP returns "notes"; direct returns "technician_notes"
        notes = m.get("notes") or m.get("technician_notes")
        parts.append(
            f"[{m.get('id', 'past')}] {m.get('machine')} {m.get('fault_code')}: "
            f"cause={m.get('root_cause')}; fix={m.get('fix')}; notes={notes}"
        )
        if m.get("id"):
            sources.append(m["id"])
    return "\n\n".join(parts), sources


# ── retrieval helpers (MCP-first, direct fallback) ───────────────────────────


def _fetch_manuals(query: str) -> list[dict]:
    """Try MCP ``search_manuals``; fall back to direct ``ingest.search``."""
    if mcp_available():
        hits = mcp_search_manuals(query, limit=settings.top_k)
        if hits is not None:
            log.info("Manuals retrieved via MCP (%d hits)", len(hits))
            return hits
        log.warning("MCP unavailable — falling back to direct manual search")

    raw = search(settings.manuals_collection, query)
    # Re-shape to match the MCP schema so _join_manuals works uniformly
    return [{"source": h.get("source", "manual"), "text": h.get("document", "")} for h in raw]


def _fetch_history(query: str, machine: str = "") -> list[dict]:
    """Try MCP ``search_history``; fall back to direct ``ingest.search``."""
    if mcp_available():
        hits = mcp_search_history(query, limit=settings.top_k, machine=machine)
        if hits is not None:
            log.info("History retrieved via MCP (%d hits)", len(hits))
            # If machine-specific search returned nothing, retry without filter.
            # Keep the original (empty) list if the retry itself fails, so we
            # never return None to _join_history.
            if not hits and machine:
                retry = mcp_search_history(query, limit=settings.top_k)
                if retry:
                    return retry
            return hits
        log.warning("MCP unavailable — falling back to direct history search")

    filters = {"machine": machine} if machine else None
    raw = search(settings.history_collection, query, filters=filters)
    if not raw and machine:
        raw = search(settings.history_collection, query)
    return [
        {
            "id": h.get("id"),
            "machine": h.get("machine"),
            "fault_code": h.get("fault_code"),
            "root_cause": h.get("root_cause"),
            "fix": h.get("fix"),
            "notes": h.get("technician_notes"),
        }
        for h in raw
    ]


# ── LLM helpers ──────────────────────────────────────────────────────────────


def _parse_json(text: str) -> dict:
    """Tolerant JSON extraction (handles fences / stray prose around the object)."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1].lstrip("json").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
        raise


def _chat(client: OpenAI, messages: list[dict], json_mode: bool = True):
    """Chat call requesting a JSON object; falls back if the model rejects the format."""
    if json_mode:
        try:
            return client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                response_format={"type": "json_object"},
                stream=False,
            )
        except Exception:  # noqa: BLE001 - model may not support json mode; plain call
            pass
    return client.chat.completions.create(model=settings.llm_model, messages=messages, stream=False)


# ── diagnosis cache ──────────────────────────────────────────────────────────

# Recent diagnoses keyed by (machine, fault_code, context). A repeat fault with
# the same context within the TTL reuses the cached result and skips the
# retrieval + LLM round-trip. Context is part of the key so a recurring fault
# described differently (new symptom text) re-diagnoses instead of reusing a
# stale answer. No lock: a rare race just costs a redundant diagnosis, it never
# corrupts state. Copies go in and out so a caller mutating a Diagnosis cannot
# poison the cache.
_CACHE: dict[tuple[str, str, str], tuple[float, Diagnosis]] = {}


# ── main entry point ─────────────────────────────────────────────────────────


def diagnose(fault_code: str, machine: str = "", context: str = "") -> Diagnosis:
    key = (machine, fault_code, context)
    ttl = settings.diagnose_cache_ttl
    if ttl > 0:
        hit = _CACHE.get(key)
        if hit and time.monotonic() < hit[0]:
            log.info("Diagnosis cache hit for %s %s (reused, no LLM call)", machine, fault_code)
            return hit[1].model_copy(deep=True)

    query = f"{fault_code} {machine} {context}".strip()

    manuals_hits = _fetch_manuals(query)
    manuals_txt, m_src = _join_manuals(manuals_hits)

    history_hits = _fetch_history(query, machine=machine)
    history_txt, h_src = _join_history(history_hits)

    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": build_user_prompt(fault_code, machine, context, manuals_txt, history_txt)},
    ]
    resp = _chat(client, messages)
    try:
        data = _parse_json(resp.choices[0].message.content)
    except (json.JSONDecodeError, ValueError):
        # one retry with a stricter nudge for valid JSON
        messages.append({"role": "user", "content": "Return ONLY the JSON object, no prose or fences."})
        resp = _chat(client, messages)
        data = _parse_json(resp.choices[0].message.content)

    # Prefer retrieved sources; let the model add any it names.
    data.setdefault("sources", [])
    for s in m_src + h_src:
        if s not in data["sources"]:
            data["sources"].append(s)

    diag = Diagnosis(fault_code=fault_code, machine=machine, **data)
    if ttl > 0:
        _CACHE[key] = (time.monotonic() + ttl, diag.model_copy(deep=True))
    return diag

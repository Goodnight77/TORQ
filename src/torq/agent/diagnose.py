"""Diagnosis agent: retrieve manual + history context, call the LLM, return a Diagnosis."""

import json

from openai import OpenAI

from torq.agent.prompts import SYSTEM, build_user_prompt
from torq.agent.schemas import Diagnosis
from torq.config import settings
from torq.ingest import search


def _join_manuals(hits: list[dict]) -> tuple[str, list[str]]:
    parts, sources = [], []
    for h in hits:
        src = h.get("source", "manual")
        parts.append(f"[{src}] {h.get('document', '')}")
        if src not in sources:
            sources.append(src)
    return "\n\n".join(parts), sources


def _join_history(hits: list[dict]) -> tuple[str, list[str]]:
    parts, sources = [], []
    for m in hits:
        parts.append(
            f"[{m.get('id', 'past')}] {m.get('machine')} {m.get('fault_code')}: "
            f"cause={m.get('root_cause')}; fix={m.get('fix')}; notes={m.get('technician_notes')}"
        )
        if m.get("id"):
            sources.append(m["id"])
    return "\n\n".join(parts), sources


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


def diagnose(fault_code: str, machine: str = "", context: str = "") -> Diagnosis:
    query = f"{fault_code} {machine} {context}".strip()
    manuals_txt, m_src = _join_manuals(search(settings.manuals_collection, query))
    # prefer past repairs on the same machine; fall back to all history if none
    hist = search(settings.history_collection, query, filters={"machine": machine} if machine else None)
    if not hist and machine:
        hist = search(settings.history_collection, query)
    history_txt, h_src = _join_history(hist)

    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    resp = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": build_user_prompt(
                    fault_code, machine, context, manuals_txt, history_txt
                ),
            },
        ],
        stream=False,
    )
    data = _parse_json(resp.choices[0].message.content)

    # Prefer retrieved sources; let the model add any it names.
    data.setdefault("sources", [])
    for s in m_src + h_src:
        if s not in data["sources"]:
            data["sources"].append(s)

    return Diagnosis(fault_code=fault_code, machine=machine, **data)

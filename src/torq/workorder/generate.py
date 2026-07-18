"""Build a WorkOrder from a Diagnosis, including trilingual (FR/AR/EN) content."""

import json
import uuid

from openai import OpenAI

from torq.agent.schemas import Diagnosis, WorkOrder
from torq.config import settings

# Fault-code prefix -> skill needed to service it. Extend as machines are added.
SKILL_BY_PREFIX = {"E": "electromechanical", "J": "packaging"}


def _required_skill(fault_code: str) -> str:
    return SKILL_BY_PREFIX.get(fault_code[:1].upper(), "general")


def _render_en(diag: Diagnosis) -> str:
    """Deterministic English work-order text (no LLM)."""
    def block(title: str, items: list[str]) -> str:
        if not items:
            return ""
        lines = "\n".join(f"  - {x}" for x in items)
        return f"{title}:\n{lines}\n"

    return (
        f"WORK ORDER - {diag.machine or 'machine'} - fault {diag.fault_code}\n"
        f"Root cause: {diag.root_cause}\n\n"
        f"{block('Repair steps', diag.repair_steps)}"
        f"{block('Parts', diag.parts)}"
        f"{block('Tools', diag.tools)}"
        f"{block('Safety', diag.safety_warnings)}"
    ).strip()


def _translate(en_text: str) -> dict[str, str]:
    """Translate the English work order to FR and AR in one LLM call."""
    if not settings.llm_api_key:
        return {}  # no key -> EN only (fallback)
    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    resp = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Translate the maintenance work order into French and Arabic. "
                    "Keep fault codes, part numbers, and units unchanged. Reply with "
                    'ONE JSON object only: {"fr": "...", "ar": "..."}'
                ),
            },
            {"role": "user", "content": en_text},
        ],
        stream=False,
        timeout=settings.translate_timeout,
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1].lstrip("json").strip()
    start, end = raw.find("{"), raw.rfind("}")
    return json.loads(raw[start : end + 1]) if start != -1 else {}


def build_work_order(
    diag: Diagnosis, translate: bool = True, fault_arrived_at: str | None = None
) -> WorkOrder:
    en = _render_en(diag)
    content = {"en": en}
    if translate:
        content.update(_translate(en))
    return WorkOrder(
        id=uuid.uuid4().hex,
        fault_code=diag.fault_code,
        machine=diag.machine,
        root_cause=diag.root_cause,
        repair_steps=diag.repair_steps,
        parts=diag.parts,
        tools=diag.tools,
        safety_warnings=diag.safety_warnings,
        required_skill=_required_skill(diag.fault_code),
        sources=diag.sources,
        investigation=diag.investigation,
        content=content,
        confidence=diag.confidence,
        fault_arrived_at=fault_arrived_at,
    )

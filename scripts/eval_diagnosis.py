"""LLM-as-judge eval: score each diagnosis for correctness and grounding.

For every seeded scenario: run the diagnosis agent, then ask an LLM judge to
score the result against the expected topic. Reports pass rate and average score,
and writes data/eval_diagnosis.json for the dashboard.

Run:  uv run python scripts/eval_diagnosis.py
"""

import json
import sys

sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252

from openai import OpenAI

from torq.agent.diagnose import diagnose
from torq.config import settings

JUDGE_SYSTEM = (
    "You are a strict evaluator of industrial maintenance diagnoses. "
    "Given a fault, the expected topic of the correct root cause, and the "
    "diagnosis produced by an AI, score it. Reply with ONE JSON object only:\n"
    '{"correct": bool, "grounded": bool, "score": float 0-1, "reason": str}\n'
    "correct = the root cause matches the expected topic. "
    "grounded = the fix cites relevant sources and invents no fake parts/codes."
)


def _judge(client: OpenAI, scenario: dict, diag) -> dict:
    user = (
        f"FAULT: {scenario['fault_code']} on {scenario['machine']}\n"
        f"EXPECTED TOPIC: {scenario.get('expected_topic', 'n/a')}\n\n"
        f"DIAGNOSIS root cause: {diag.root_cause}\n"
        f"repair steps: {diag.repair_steps}\n"
        f"parts: {diag.parts}\n"
        f"sources cited: {diag.sources}\n\n"
        "Score this diagnosis. JSON only."
    )
    resp = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": user}],
        stream=False,
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1].lstrip("json").strip()
    start, end = raw.find("{"), raw.rfind("}")
    return json.loads(raw[start : end + 1])


def main() -> None:
    scenarios = json.loads(settings.scenarios_file.read_text(encoding="utf-8"))
    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)

    rows = []
    for s in scenarios:
        diag = diagnose(s["fault_code"], s.get("machine", ""), s.get("context", ""))
        v = _judge(client, s, diag)
        v["scenario"] = s["id"]
        rows.append(v)
        mark = "PASS" if (v.get("correct") and v.get("grounded")) else "FAIL"
        print(f"{s['id']:<4} {mark}  score={v.get('score')}  {s['fault_code']}  {v.get('reason','')[:70]}")

    n = len(rows)
    passed = sum(1 for r in rows if r.get("correct") and r.get("grounded"))
    correct = sum(1 for r in rows if r.get("correct"))
    grounded = sum(1 for r in rows if r.get("grounded"))
    avg = round(sum(float(r.get("score", 0)) for r in rows) / n, 3) if n else 0
    summary = {
        "scenarios": n,
        "pass_rate": round(passed / n, 3) if n else 0,
        "correct_rate": round(correct / n, 3) if n else 0,
        "grounded_rate": round(grounded / n, 3) if n else 0,
        "avg_score": avg,
    }
    settings.eval_results_file.with_name("eval_diagnosis.json").write_text(
        json.dumps({"metric": "diagnosis (LLM-as-judge)", **summary, "results": rows}, indent=2),
        encoding="utf-8",
    )
    print(f"\nSummary: {summary}")
    assert passed >= 1, "no scenario passed the judge"


if __name__ == "__main__":
    main()

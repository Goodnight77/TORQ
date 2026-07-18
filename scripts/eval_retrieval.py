"""Measure whether hybrid search and reranking actually improve retrieval.

Compares three configs on the seeded scenarios using Hit@k and MRR:
  A dense-only, B hybrid (dense+BM25 RRF), C hybrid+rerank.

Run:  uv run python scripts/eval_retrieval.py
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252

import json

from torq.config import settings
from torq.ingest import search

# machine name keyword -> the manual file that should ground its faults
GOLD = {
    "CM-350": "conveyor_motor.md",
    "PK-9": "packaging_unit.md",
    "Chiller": "chiller.md",
    "Pump": "centrifugal_pump.md",
    "AHU": "air_handling_unit.md",
}

CONFIGS = [
    ("A dense-only", {"use_hybrid": False, "use_rerank": False}),
    ("B hybrid", {"use_hybrid": True, "use_rerank": False}),
    ("C hybrid+rerank", {"use_hybrid": True, "use_rerank": True}),
]


def _gold_file(machine: str) -> str | None:
    for key, f in GOLD.items():
        if key.lower() in machine.lower():
            return f
    return None


def _relevant(hit: dict, gold_file: str, fault_code: str) -> bool:
    return hit.get("source") == gold_file and fault_code in hit.get("document", "")


def _rank_of_first_relevant(hits: list[dict], gold_file: str, fault_code: str) -> int:
    for i, h in enumerate(hits, start=1):
        if _relevant(h, gold_file, fault_code):
            return i
    return 0  # not found


def main() -> None:
    scenarios = json.loads(settings.scenarios_file.read_text(encoding="utf-8"))
    labeled = [(s, _gold_file(s["machine"])) for s in scenarios]
    labeled = [(s, g) for s, g in labeled if g]  # keep only ones we can grade
    print(f"Evaluating {len(labeled)} scenarios on manual retrieval\n")

    print(f"{'config':<18}{'Hit@3':>8}{'Hit@5':>8}{'MRR':>8}")
    print("-" * 42)
    results = []
    for name, flags in CONFIGS:
        settings.use_hybrid = flags["use_hybrid"]
        settings.use_rerank = flags["use_rerank"]
        hit3 = hit5 = mrr = 0.0
        for s, gold in labeled:
            query = f"{s['fault_code']} {s['machine']} {s.get('context', '')}".strip()
            hits = search(settings.manuals_collection, query, limit=5)
            r = _rank_of_first_relevant(hits, gold, s["fault_code"])
            if r:
                mrr += 1.0 / r
                hit3 += r <= 3
                hit5 += r <= 5
        n = len(labeled)
        results.append(
            {
                "config": name,
                "hit_at_3": round(hit3 / n, 3),
                "hit_at_5": round(hit5 / n, 3),
                "mrr": round(mrr / n, 3),
            }
        )
        print(f"{name:<18}{hit3/n:>8.2f}{hit5/n:>8.2f}{mrr/n:>8.3f}")

    settings.eval_results_file.write_text(
        json.dumps({"metric": "manual retrieval", "scenarios": len(labeled), "configs": results},
                   indent=2),
        encoding="utf-8",
    )
    print(f"\nWrote {settings.eval_results_file}")
    print("A->B shows hybrid's effect; B->C shows reranking's effect.")


if __name__ == "__main__":
    main()

"""Score retrieval quality on a golden set, comparing configurations.

Two granularities, because they measure different things:

- fault_code recall@k / MRR: did any top-k record carry the right fault code.
  Coarse; on a small, well-separated corpus every config saturates near 1.0, so
  this mainly serves as a regression tripwire.
- id_recall@1 / id_mrr (over entries that carry an `expected_id`): did the single
  *best* record - a detailed authored repair competing with generic near-duplicate
  work orders - rank first. This is the granularity where rerank and the recency
  boost actually diverge.

Runs four configs (dense, hybrid, hybrid+rerank, hybrid+rerank+boost) and writes
results in the shape the dashboard `/eval` reads.

Run:  uv run python -m torq.eval.retrieval
"""

import json

from torq.config import settings
from torq.ingest import search

# (use_hybrid, use_rerank, use_recency_boost) per named config.
_CONFIGS = {
    "dense": (False, False, False),
    "hybrid": (True, False, False),
    "hybrid+rerank": (True, True, False),
    "hybrid+rerank+boost": (True, True, True),
}


def _load_golden() -> list[dict]:
    return json.loads(settings.golden_file.read_text(encoding="utf-8"))


def _score_config(golden: list[dict], k: int) -> dict:
    hit1 = hitk = mrr = 0
    id_hit1 = id_mrr = id_n = 0
    for g in golden:
        # Fault-code metric uses the top-k the app would actually show; the id
        # metric retrieves a bit wider so a demoted-but-present record still
        # contributes to MRR instead of vanishing.
        results = search(settings.history_collection, g["query"], limit=max(k, 5))
        ranks = [i for i, p in enumerate(results[:k]) if p.get("fault_code") == g["fault_code"]]
        if ranks:
            hitk += 1
            hit1 += 1 if ranks[0] == 0 else 0
            mrr += 1.0 / (ranks[0] + 1)
        if g.get("expected_id"):
            id_n += 1
            id_ranks = [i for i, p in enumerate(results) if p.get("id") == g["expected_id"]]
            if id_ranks:
                id_hit1 += 1 if id_ranks[0] == 0 else 0
                id_mrr += 1.0 / (id_ranks[0] + 1)
    n = len(golden) or 1
    out = {
        "recall@1": round(hit1 / n, 3),
        f"recall@{k}": round(hitk / n, 3),
        "mrr": round(mrr / n, 3),
        "n": len(golden),
    }
    if id_n:
        out["id_recall@1"] = round(id_hit1 / id_n, 3)
        out["id_mrr"] = round(id_mrr / id_n, 3)
        out["id_n"] = id_n
    return out


def run(k: int = 3) -> dict:
    golden = _load_golden()
    saved = (settings.use_hybrid, settings.use_rerank, settings.use_recency_boost)
    configs = []
    try:
        for name, (h, rr, bo) in _CONFIGS.items():
            settings.use_hybrid, settings.use_rerank, settings.use_recency_boost = h, rr, bo
            metrics = _score_config(golden, k)
            metrics["name"] = name
            configs.append(metrics)
    finally:
        settings.use_hybrid, settings.use_rerank, settings.use_recency_boost = saved

    out = {"k": k, "configs": configs}
    settings.eval_results_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

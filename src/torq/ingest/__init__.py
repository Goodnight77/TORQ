"""Ingest subpackage.

Loads OEM manuals and repair history, embeds them (dense + BM25 sparse), and
indexes them into Qdrant with named vectors. Retrieval is hybrid (dense + sparse
fused with RRF), optionally reranked with a cross-encoder, and can be filtered by
payload fields (machine, fault_code).
"""

import math
import uuid
from datetime import datetime, timezone
from functools import lru_cache

from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient, models

from torq.config import settings

# Payload fields we index so they are cheap to filter or score-boost on.
# `date`/`indexed_at` are datetimes (recency boosting); the rest are keywords.
# Indexing a field a collection does not carry yet is harmless: only points that
# have it get indexed.
_PAYLOAD_INDEXES = {
    "machine": models.PayloadSchemaType.KEYWORD,
    "fault_code": models.PayloadSchemaType.KEYWORD,
    "outcome": models.PayloadSchemaType.KEYWORD,
    "date": models.PayloadSchemaType.DATETIME,
    "indexed_at": models.PayloadSchemaType.DATETIME,
}


@lru_cache(maxsize=1)
def get_client() -> QdrantClient:
    """Cached Qdrant client. Falls back to on-disk storage if no URL is set."""
    if settings.qdrant_url:
        # Generous timeout: cloud round-trips under load can exceed the short default.
        return QdrantClient(
            url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=30
        )
    # no cloud URL -> local on-disk store, keeps retrieval self-contained
    return QdrantClient(path=str(settings.manuals_dir.parent / "qdrant_storage"))


@lru_cache(maxsize=1)
def get_embedder() -> TextEmbedding:
    return TextEmbedding(settings.embedding_model)


@lru_cache(maxsize=1)
def get_sparse_embedder() -> SparseTextEmbedding:
    return SparseTextEmbedding(settings.sparse_model)


@lru_cache(maxsize=1)
def get_reranker() -> TextCrossEncoder:
    return TextCrossEncoder(settings.rerank_model)


def embed(texts: list[str]) -> list[list[float]]:
    return [v.tolist() for v in get_embedder().embed(texts)]


def _sparse(text: str) -> models.SparseVector:
    se = next(iter(get_sparse_embedder().embed([text])))
    return models.SparseVector(indices=se.indices.tolist(), values=se.values.tolist())


def _filter(filters: dict | None) -> models.Filter | None:
    if not filters:
        return None
    conds = [
        models.FieldCondition(key=k, match=models.MatchValue(value=v))
        for k, v in filters.items()
        if v
    ]
    return models.Filter(must=conds) if conds else None


def _point_id(doc_id: str | int) -> str | int:
    """Stable Qdrant point id from a document identifier.

    Ints pass through; a string that already parses as a UUID is used as-is,
    otherwise a deterministic uuid5 is derived. Same id -> same point, so a bulk
    re-index and a later single upsert of the same record address one point and
    update in place instead of creating a duplicate.
    """
    if isinstance(doc_id, int):
        return doc_id
    try:
        return str(uuid.UUID(doc_id))
    except ValueError:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))


def _doc_id_for(payload: dict, fallback: int) -> str | int:
    """Derive a stable document id from a payload: an explicit `id` (repair
    history), else `source:chunk` (manual chunks), else the positional fallback."""
    if payload.get("id"):
        return str(payload["id"])
    if payload.get("source") is not None:
        return f'{payload["source"]}:{payload.get("chunk", 0)}'
    return fallback


def index_docs(collection: str, docs: list[str], payloads: list[dict]) -> int:
    """(Re)create a collection with dense + sparse vectors and index the docs."""
    if not docs:
        return 0
    client = get_client()
    dense = embed(docs)
    sparse = [_sparse(d) for d in docs]

    if client.collection_exists(collection):
        client.delete_collection(collection)
    client.create_collection(
        collection_name=collection,
        vectors_config={
            "dense": models.VectorParams(size=len(dense[0]), distance=models.Distance.COSINE)
        },
        sparse_vectors_config={"bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)},
    )
    for field, schema in _PAYLOAD_INDEXES.items():
        try:
            client.create_payload_index(collection, field, schema)
        except Exception:  # noqa: BLE001 - index is an optimization, not required
            pass

    now = datetime.now(timezone.utc).isoformat()
    client.upsert(
        collection_name=collection,
        points=[
            models.PointStruct(
                id=_point_id(_doc_id_for(payloads[i], i)),
                vector={"dense": dense[i], "bm25": sparse[i]},
                payload={**payloads[i], "document": docs[i], "indexed_at": now},
            )
            for i in range(len(docs))
        ],
    )
    return len(docs)


def upsert_document(collection: str, doc_id: str | int, doc: str, payload: dict) -> None:
    """Upsert a single document into an existing collection (creates collection if missing)."""
    client = get_client()
    dense_vec = embed([doc])[0]
    sparse_vec = _sparse(doc)

    if not client.collection_exists(collection):
        client.create_collection(
            collection_name=collection,
            vectors_config={
                "dense": models.VectorParams(size=len(dense_vec), distance=models.Distance.COSINE)
            },
            sparse_vectors_config={"bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)},
        )
        for field, schema in _PAYLOAD_INDEXES.items():
            try:
                client.create_payload_index(collection, field, schema)
            except Exception:  # noqa: BLE001 - index is an optimization, not required
                pass

    point_id = _point_id(doc_id)

    client.upsert(
        collection_name=collection,
        points=[
            models.PointStruct(
                id=point_id,
                vector={"dense": dense_vec, "bm25": sparse_vec},
                payload={**payload, "document": doc, "indexed_at": datetime.now(timezone.utc).isoformat()},
            )
        ],
    )


def nearest_dense(
    collection: str, query: str, filters: dict | None = None
) -> tuple[str | int, float, dict] | None:
    """(point_id, cosine_score, payload) of the single nearest dense neighbour,
    or None if the collection is missing/empty. Used for dedup-on-write."""
    client = get_client()
    if not client.collection_exists(collection):
        return None
    res = client.query_points(
        collection_name=collection,
        query=embed([query])[0],
        using="dense",
        query_filter=_filter(filters),
        limit=1,
        with_payload=True,
    )
    if not res.points:
        return None
    p = res.points[0]
    return p.id, float(p.score), p.payload


def merge_payload(collection: str, point_id: str | int, updates: dict) -> None:
    """Merge extra fields into an existing point's payload, leaving its vector be."""
    get_client().set_payload(collection_name=collection, payload=updates, points=[point_id])


def _recency(date_str: str | None, now: datetime) -> float:
    """Gaussian decay in [0, 1] on a record's age: 1.0 today, ~0.6 at one
    half-life, tapering toward 0 for old records. Unparseable/absent -> 0."""
    if not date_str:
        return 0.0
    s = str(date_str)
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        try:
            d = datetime.strptime(s[:10], "%Y-%m-%d")
        except ValueError:
            return 0.0
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    age_days = max((now - d).total_seconds() / 86400.0, 0.0)
    hl = max(settings.recency_half_life_days, 1)
    return math.exp(-0.5 * (age_days / hl) ** 2)


def _boost(scored: list[tuple]) -> list[tuple]:
    """Composite reorder: normalized base score + recency + resolved-outcome bonus.

    Kept client-side so it works against the embedded local store; a Qdrant server
    (>= v1.14) could push this into a FormulaQuery with gauss_decay for speed at
    scale. Semantic similarity stays the dominant signal; recency/outcome only
    break near-ties toward fresher, proven fixes.
    """
    vals = [s for _, s in scored]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    now = datetime.now(timezone.utc)
    out = []
    for pt, s in scored:
        base = (s - lo) / span
        rec = _recency(pt.payload.get("date"), now)
        won = 1.0 if pt.payload.get("outcome") == "resolved" else 0.0
        out.append((pt, base + settings.recency_weight * rec + settings.outcome_weight * won))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def search(
    collection: str,
    query: str,
    limit: int | None = None,
    filters: dict | None = None,
) -> list[dict]:
    """Hybrid (dense + BM25, RRF) retrieval with optional rerank, recency/outcome
    boost, and payload filter."""
    client = get_client()
    if not client.collection_exists(collection):
        return []
    k = limit or settings.top_k
    flt = _filter(filters)
    dense_q = embed([query])[0]

    if settings.use_hybrid:
        wide = max(k * 4, 20)
        res = client.query_points(
            collection_name=collection,
            prefetch=[
                models.Prefetch(query=dense_q, using="dense", limit=wide, filter=flt),
                models.Prefetch(query=_sparse(query), using="bm25", limit=wide, filter=flt),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=k * 3 if settings.use_rerank else k,
            with_payload=True,
        )
    else:
        res = client.query_points(
            collection_name=collection,
            query=dense_q,
            using="dense",
            query_filter=flt,
            limit=k * 3 if settings.use_rerank else k,
            with_payload=True,
        )

    points = list(res.points)
    if not points:
        return []
    if settings.use_rerank:
        docs = [pt.payload.get("document", "") for pt in points]
        rr = list(get_reranker().rerank(query, docs))
        scored = [(pt, float(s)) for pt, s in zip(points, rr)]
    else:
        scored = [(pt, float(pt.score)) for pt in points]

    if settings.use_recency_boost and any("date" in pt.payload for pt, _ in scored):
        scored = _boost(scored)
    else:
        scored.sort(key=lambda x: x[1], reverse=True)
    return [pt.payload for pt, _ in scored[:k]]

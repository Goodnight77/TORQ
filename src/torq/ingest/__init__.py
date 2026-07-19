"""Ingest subpackage.

Loads OEM manuals and repair history, embeds them (dense + BM25 sparse), and
indexes them into Qdrant with named vectors. Retrieval is hybrid (dense + sparse
fused with RRF), optionally reranked with a cross-encoder, and can be filtered by
payload fields (machine, fault_code).
"""

from functools import lru_cache

from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient, models

from torq.config import settings

_FILTER_FIELDS = ("machine", "fault_code")


@lru_cache(maxsize=1)
def get_client() -> QdrantClient:
    """Cached Qdrant client. Falls back to on-disk storage if no URL is set."""
    if settings.qdrant_url:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
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
    for field in _FILTER_FIELDS:
        try:
            client.create_payload_index(collection, field, models.PayloadSchemaType.KEYWORD)
        except Exception:  # noqa: BLE001 - index is an optimization, not required
            pass

    client.upsert(
        collection_name=collection,
        points=[
            models.PointStruct(
                id=i,
                vector={"dense": dense[i], "bm25": sparse[i]},
                payload={**payloads[i], "document": docs[i]},
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
        for field in _FILTER_FIELDS:
            try:
                client.create_payload_index(collection, field, models.PayloadSchemaType.KEYWORD)
            except Exception:
                pass

    if isinstance(doc_id, str):
        import uuid
        try:
            uuid_val = uuid.UUID(doc_id)
            point_id = str(uuid_val)
        except ValueError:
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))
    else:
        point_id = doc_id

    client.upsert(
        collection_name=collection,
        points=[
            models.PointStruct(
                id=point_id,
                vector={"dense": dense_vec, "bm25": sparse_vec},
                payload={**payload, "document": doc},
            )
        ],
    )


def search(
    collection: str,
    query: str,
    limit: int | None = None,
    filters: dict | None = None,
) -> list[dict]:
    """Hybrid (dense + BM25, RRF) retrieval with optional rerank and payload filter."""
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

    payloads = [pt.payload for pt in res.points]
    if settings.use_rerank and payloads:
        docs = [p.get("document", "") for p in payloads]
        scores = list(get_reranker().rerank(query, docs))
        order = sorted(range(len(payloads)), key=lambda i: scores[i], reverse=True)
        payloads = [payloads[i] for i in order]
    return payloads[:k]

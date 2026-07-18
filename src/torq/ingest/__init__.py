"""Ingest subpackage.

Data ingestion for TORQ: OEM manuals and repair-history logs are loaded,
chunked, embedded, and indexed for retrieval. Exposes the shared Qdrant client,
the local fastembed embedder, and index/search helpers used across ingestion
and the diagnosis agent.
"""

from functools import lru_cache

from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

from torq.config import settings


@lru_cache(maxsize=1)
def get_client() -> QdrantClient:
    """Cached Qdrant client. Falls back to on-disk storage if no URL is set."""
    if settings.qdrant_url:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    # no cloud URL -> local on-disk store, keeps retrieval self-contained
    return QdrantClient(path=str(settings.manuals_dir.parent / "qdrant_storage"))


@lru_cache(maxsize=1)
def get_embedder() -> TextEmbedding:
    """Cached fastembed model (runs locally, no API key). Swap later if needed."""
    return TextEmbedding(settings.embedding_model)


def embed(texts: list[str]) -> list[list[float]]:
    return [v.tolist() for v in get_embedder().embed(texts)]


def index_docs(collection: str, docs: list[str], payloads: list[dict]) -> int:
    """(Re)create a collection and index docs with their payloads. Returns count."""
    if not docs:
        return 0
    client = get_client()
    vectors = embed(docs)
    if client.collection_exists(collection):
        client.delete_collection(collection)
    client.create_collection(
        collection_name=collection,
        vectors_config=models.VectorParams(
            size=len(vectors[0]), distance=models.Distance.COSINE
        ),
    )
    client.upsert(
        collection_name=collection,
        points=[
            models.PointStruct(id=i, vector=v, payload={**p, "document": d})
            for i, (v, p, d) in enumerate(zip(vectors, payloads, docs))
        ],
    )
    return len(docs)


def search(collection: str, query: str, limit: int | None = None) -> list[dict]:
    """Return payloads of the top matches (empty list if collection missing)."""
    client = get_client()
    if not client.collection_exists(collection):
        return []
    res = client.query_points(
        collection_name=collection,
        query=embed([query])[0],
        limit=limit or settings.top_k,
        with_payload=True,
    )
    return [pt.payload for pt in res.points]

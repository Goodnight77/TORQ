"""OEM manual ingestion: read manuals, chunk, embed (fastembed), index in Qdrant."""

from functools import lru_cache
from pathlib import Path

from chonkie import RecursiveChunker

from torq.config import settings
from torq.ingest import index_docs


@lru_cache(maxsize=1)
def _chunker() -> RecursiveChunker:
    """Markdown-aware recursive chunker: splits on headers so each fault-code
    section stays whole (chunk size large enough to keep a section intact)."""
    try:
        return RecursiveChunker.from_recipe(
            "markdown", lang="en", chunk_size=settings.manual_chunk_size
        )
    except Exception:  # noqa: BLE001 - recipe unavailable -> plain recursive chunker
        return RecursiveChunker(chunk_size=settings.manual_chunk_size)


def _chunk(text: str) -> list[str]:
    return [c.text.strip() for c in _chunker()(text) if c.text.strip()]


def ingest_manuals(manuals_dir: Path | None = None) -> int:
    """Index every .md/.txt manual under manuals_dir. Returns chunk count."""
    manuals_dir = manuals_dir or settings.manuals_dir
    docs, payloads = [], []
    for path in sorted([*manuals_dir.glob("*.md"), *manuals_dir.glob("*.txt")]):
        text = path.read_text(encoding="utf-8")
        for i, chunk in enumerate(_chunk(text)):
            docs.append(chunk)
            payloads.append({"source": path.name, "chunk": i})
    return index_docs(settings.manuals_collection, docs, payloads)


if __name__ == "__main__":
    print(f"Indexed {ingest_manuals()} manual chunks.")

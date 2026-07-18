"""OEM manual ingestion: read manuals, chunk, embed (fastembed), index in Qdrant."""

from pathlib import Path

from torq.config import settings
from torq.ingest import index_docs


def _chunk(text: str) -> list[str]:
    """Split a manual into chunks on blank lines, merging tiny fragments."""
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    chunks: list[str] = []
    buf = ""
    for b in blocks:
        buf = f"{buf}\n\n{b}" if buf else b
        if len(buf) > 400:  # ponytail: fixed-size heuristic, tune if recall suffers
            chunks.append(buf)
            buf = ""
    if buf:
        chunks.append(buf)
    return chunks


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

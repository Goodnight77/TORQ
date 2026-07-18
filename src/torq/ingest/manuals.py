"""OEM manual ingestion.

Loads OEM manuals, splits them into chunks, embeds the chunks, and indexes
them into the Qdrant vector database for semantic retrieval.
"""

# TODO: load manual sources (PDF/text) from the plant document store
# TODO: chunk documents with metadata (machine model, section, page)
# TODO: embed chunks using the configured embedding model
# TODO: upsert vectors into the Qdrant manuals collection

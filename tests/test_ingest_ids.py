"""Point-id derivation: bulk index and incremental upsert must agree, so a
re-resolved repair updates its point in place instead of duplicating."""

from torq.ingest import _doc_id_for, _point_id


def test_bulk_and_incremental_ids_match():
    # Same repair record, reached two ways: bulk reindex derives its id from the
    # payload; the feedback path upserts by the explicit record id. They must
    # collapse to one point id.
    rec = {"id": "WO-5", "machine": "L3", "fault_code": "F12"}
    bulk_id = _point_id(_doc_id_for(rec, 0))  # ingest_history / index_docs path
    incr_id = _point_id("WO-5")               # upsert_document path
    assert bulk_id == incr_id


def test_manual_chunk_id_is_position_independent():
    # A manual chunk keeps its id even if its ordinal position in the batch
    # shifts (e.g. another manual added ahead of it).
    chunk = {"source": "pump.md", "chunk": 2}
    assert _point_id(_doc_id_for(chunk, 7)) == _point_id(_doc_id_for(chunk, 99))


def test_positional_fallback_passes_through():
    # No id and no source -> fall back to the positional int, used as-is.
    assert _point_id(_doc_id_for({}, 3)) == 3


def test_uuid_string_used_as_is():
    u = "12345678-1234-5678-1234-567812345678"
    assert _point_id(u) == u

"""Repair-outcome feedback.

Captures the technician's repair outcome (success, notes, actual fix) and
feeds it back into the repair-history knowledge base for future diagnoses.
"""

# TODO: collect outcome from technician (resolved?, actual fix, notes)
# TODO: persist outcome to Postgres and link to the work order
# TODO: re-index the outcome into the history store for retrieval

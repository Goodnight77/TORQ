# TORQ Tests

Test strategy for the Fault-to-Fix Engine.

The priority is an **end-to-end test of the fault to fix path**: fault code (MQTT)
to AI diagnosis (manuals + repair history via MCP) to trilingual work-order PDF to
supervisor approval to technician dispatch to outcome feedback. Unit tests for
individual pipeline stages follow.

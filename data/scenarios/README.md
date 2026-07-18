# Demo Fault Scenarios

Five seeded fault scenarios that drive the scripted TORQ demo. Each scenario is
a machine fault code (delivered over MQTT) that the AI agent diagnoses and turns
into a trilingual repair work order.

Example: conveyor motor fault **E-471**. The remaining four cover additional
asset types drawn from IBM AssetOpsBench (manuals + failure logs) so the demo
exercises the full fault to fix path end to end.

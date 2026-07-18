"""MQTT fault listener.

Subscribes to the machine fault-code topic over MQTT (paho-mqtt) and triggers
the fault-to-fix pipeline for each incoming event.
"""

# TODO: connect to the MQTT broker and subscribe to fault topics
# TODO: parse fault-code payloads into pipeline input
# TODO: dispatch each event to torq.pipeline
# TODO: reconnect/error handling for broker outages

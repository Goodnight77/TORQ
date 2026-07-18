"""Send one real WhatsApp message to verify Twilio dispatch.

Set TEST_WHATSAPP_TO to a phone number that has joined your Twilio WhatsApp
sandbox (send the join code to +14155238886 first), then:

    TEST_WHATSAPP_TO=+2126xxxxxxx uv run python scripts/test_whatsapp.py
"""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252

from torq.config import settings
from torq.dispatch.notify import send_whatsapp

to = os.getenv("TEST_WHATSAPP_TO")
if not to:
    raise SystemExit("Set TEST_WHATSAPP_TO to a sandbox-joined phone number first.")
if not (settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_whatsapp_from):
    raise SystemExit("Twilio creds missing in .env")

res = send_whatsapp(to, "TORQ test: work order dispatch is live. From fault code to fixed.")
print("Sent:", res)
print("If status is queued/sent and your phone buzzes, Twilio dispatch works.")

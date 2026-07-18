"""Deliver a work order to a technician via Twilio WhatsApp, with in-app fallback."""

from torq.agent.schemas import WorkOrder
from torq.config import settings


def _message_for(wo: WorkOrder, tech: dict) -> str:
    """Pick the work-order text in the technician's language (fallback to English)."""
    lang = tech.get("lang", "en")
    return wo.content.get(lang) or wo.content.get("en") or wo.root_cause


def dispatch(wo: WorkOrder, tech: dict) -> dict:
    """Send the work order. Returns a delivery record for the dashboard."""
    body = _message_for(wo, tech)
    to = tech.get("phone", "")

    twilio_ready = all(
        [settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_whatsapp_from]
    )
    if twilio_ready:
        try:
            from twilio.rest import Client  # lazy: only needed when live

            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            msg = client.messages.create(
                from_=f"whatsapp:{settings.twilio_whatsapp_from}",
                to=f"whatsapp:{to}",
                body=body,
            )
            return {"channel": "whatsapp", "to": to, "sid": msg.sid, "status": "sent"}
        except Exception as e:  # noqa: BLE001 - degrade gracefully, demo must not fail
            return {"channel": "fallback", "to": to, "error": str(e), "body": body}

    # no Twilio creds -> in-app fallback so delivery always succeeds
    return {"channel": "in_app", "to": to, "status": "queued", "body": body}

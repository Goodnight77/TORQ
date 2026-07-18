"""Deliver a work order to a technician via Twilio WhatsApp, with in-app fallback."""

from torq.agent.schemas import WorkOrder
from torq.config import settings


def _message_for(wo: WorkOrder, tech: dict) -> str:
    """Pick the work-order text in the technician's language (fallback to English)."""
    lang = tech.get("lang", "en")
    return wo.content.get(lang) or wo.content.get("en") or wo.root_cause


def send_whatsapp(to: str, body: str) -> dict:
    """Send one WhatsApp message via Twilio. Returns a delivery record."""
    body = body[:1500]  # Twilio WhatsApp body cap is 1600 chars; leave headroom
    _to = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
    _from = settings.twilio_whatsapp_from
    _from = _from if _from.startswith("whatsapp:") else f"whatsapp:{_from}"
    from twilio.rest import Client  # lazy: only needed when live

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    msg = client.messages.create(from_=_from, to=_to, body=body)
    return {"channel": "whatsapp", "to": to, "sid": msg.sid, "status": msg.status}


def dispatch(wo: WorkOrder, tech: dict) -> dict:
    """Send the work order. Returns a delivery record for the dashboard."""
    body = _message_for(wo, tech)
    to = tech.get("phone", "")

    twilio_ready = to and all(
        [settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_whatsapp_from]
    )
    if twilio_ready:
        try:
            return send_whatsapp(to, body)
        except Exception as e:  # noqa: BLE001 - degrade gracefully, demo must not fail
            return {"channel": "fallback", "to": to, "error": str(e), "body": body}

    # no creds or no recipient -> in-app fallback so delivery always succeeds
    return {"channel": "in_app", "to": to, "status": "queued", "body": body}

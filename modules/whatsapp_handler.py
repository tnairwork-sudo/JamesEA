from __future__ import annotations

import os

from twilio.rest import Client

from database import db
from database.models import MessageLog

def _twilio_client() -> Client | None:
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    if not sid or not token:
        return None
    return Client(sid, token)

def send_whatsapp(to: str, body: str) -> bool:
    client = _twilio_client()
    sender = os.getenv("TWILIO_WHATSAPP_FROM", "")
    try:
        if client and sender and to:
            client.messages.create(from_=sender, to=to, body=body)
        db.session.add(
            MessageLog(direction="outbound", channel="whatsapp", sender=sender, recipient=to, body=body)
        )
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False

def make_call(to: str) -> bool:
    client = _twilio_client()
    caller = os.getenv("TWILIO_CALL_FROM")
    if client is None or not caller or not to:
        return False
    try:
        client.calls.create(
            from_=caller,
            to=to,
            twiml="<Response><Say>Urgent approval pending for James assistant.</Say></Response>",
        )
        return True
    except Exception:
        return False
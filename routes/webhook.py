import os

from flask import Blueprint, Response, request
from twilio.twiml.messaging_response import MessagingResponse

from database import db
from database.models import MessageLog
from modules.command_parser import parse_command

bp = Blueprint("webhook", __name__, url_prefix="/webhook")


@bp.post("/whatsapp")
def whatsapp_webhook():
    sender = request.form.get("From", "")
    body = request.form.get("Body", "")
    expected = os.getenv("TUSHAAR_WHATSAPP", "")

    db.session.add(MessageLog(direction="inbound", channel="whatsapp", sender=sender, recipient=expected, body=body))
    db.session.commit()

    result = parse_command(body=body, from_number=sender, tushaar_number=expected)
    resp = MessagingResponse()
    resp.message(result or "Command received.")
    return Response(str(resp), mimetype="application/xml")


@bp.post("/gmail")
def gmail_webhook():
    return Response("", status=200)

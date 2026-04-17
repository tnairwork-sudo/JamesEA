import os

from flask import Blueprint, jsonify, request

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
    return jsonify({"status": "ok", "result": result})


@bp.post("/gmail")
def gmail_webhook():
    return jsonify({"status": "ok"})

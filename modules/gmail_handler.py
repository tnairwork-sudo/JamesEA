from __future__ import annotations

from database import db
from database.models import BlockedSender, Contact, Draft, MessageLog
from modules import claude_handler
from modules.meeting_handler import handle_inbound_meeting_request
from modules.whatsapp_handler import send_whatsapp


class GmailHandler:
    def __init__(self) -> None:
        import os

        self.monitor_email = os.getenv("GMAIL_MONITOR_EMAIL", "")
        self.approver_whatsapp = os.getenv("TUSHAAR_WHATSAPP", "")

    def _is_blocked(self, sender_email: str) -> bool:
        return (
            BlockedSender.query.filter_by(identifier=sender_email).first() is not None
            or Contact.query.filter_by(email=sender_email, is_blocked=1).first() is not None
        )

    def process_email(self, sender_name: str, sender_email: str, subject: str, body: str, message_id: str = "") -> str:
        if self._is_blocked(sender_email):
            return "blocked"

        contact = Contact.query.filter_by(email=sender_email, is_blocked=0).first()
        if not contact:
            draft = Draft(
                from_email=sender_email,
                from_name=sender_name,
                subject=subject,
                original_message=body,
                drafted_reply="",
                status="unknown_sender",
                gmail_message_id=message_id,
            )
            db.session.add(draft)
            db.session.add(
                MessageLog(
                    direction="inbound",
                    channel="email",
                    sender=sender_email,
                    recipient=self.monitor_email,
                    subject=subject,
                    body=body,
                )
            )
            db.session.commit()
            send_whatsapp(
                self.approver_whatsapp,
                f"⚠️ UNKNOWN CONTACT: {sender_name} <{sender_email}> RE: {subject}. Reply ADD [name] [email] [relationship], SKIP, or BLOCK [email]",
            )
            return "unknown_sender"

        intent = claude_handler.classify_email(body, {"name": sender_name, "email": sender_email})
        reply = claude_handler.draft_reply(body, {"name": sender_name, "email": sender_email}, contact, intent)
        if intent == "court_or_counsel":
            reply = f"⚠️ URGENT — COURT/COUNSEL\n{reply}"

        draft = Draft(
            from_email=sender_email,
            from_name=sender_name,
            subject=subject,
            original_message=body,
            drafted_reply=reply,
            status="pending",
            gmail_message_id=message_id,
        )
        db.session.add(draft)
        db.session.add(
            MessageLog(
                direction="inbound",
                channel="email",
                sender=sender_email,
                recipient=self.monitor_email,
                subject=subject,
                body=body,
            )
        )
        db.session.commit()

        send_whatsapp(
            self.approver_whatsapp,
            f"FROM: {sender_name}\nRE: {subject[:120]}\nDRAFT: {reply}\nReply SEND, EDIT [new text], or SKIP",
        )

        if intent == "meeting_request":
            handle_inbound_meeting_request(contact, body)

        return intent

    def check_new_emails(self) -> int:
        return 0

    def send_email(self, to: str, subject: str, body: str, reply_to_message_id: str | None = None) -> bool:
        _ = reply_to_message_id
        try:
            db.session.add(
                MessageLog(
                    direction="outbound",
                    channel="email",
                    sender=self.monitor_email,
                    recipient=to,
                    subject=subject,
                    body=body,
                )
            )
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False


gmail_handler = GmailHandler()

from __future__ import annotations

from datetime import datetime

from database import db
from database.models import BlockedSender, Contact, Draft, Meeting, MeetingNote, MessageLog, PersonalTask, RuntimeFlag
from modules.gmail_handler import gmail_handler
from modules.meeting_handler import book_meeting
from modules.travel_handler import handle_travel_request
from modules.whatsapp_handler import send_whatsapp


def _latest_pending_draft() -> Draft | None:
    return Draft.query.filter_by(status="pending").order_by(Draft.created_at.desc()).first()


def _send_ack(to: str, text: str) -> str:
    send_whatsapp(to, text)
    return text


def _parse_add_contact(parts: list[str], to_number: str) -> str:
    if len(parts) < 5:
        return _send_ack(to_number, "Use: ADD CONTACT [name] [email] [relationship]")
    name = parts[2]
    email = parts[3]
    relationship = parts[4]
    row = Contact(name=name, email=email, relationship_type=relationship, is_blocked=0)
    db.session.add(row)
    db.session.commit()
    return _send_ack(to_number, f"Added contact: {name} ({relationship})")


def parse_command(body: str, from_number: str, tushaar_number: str) -> str:
    if from_number != tushaar_number:
        return "unauthorized"

    text = (body or "").strip()
    parts = text.split()
    upper = text.upper()

    if upper == "SEND":
        draft = _latest_pending_draft()
        if not draft:
            return _send_ack(from_number, "No pending draft found.")
        gmail_handler.send_email(draft.from_email, f"Re: {draft.subject or ''}".strip(), draft.drafted_reply or "")
        draft.status = "sent"
        db.session.commit()
        return _send_ack(from_number, "Draft sent.")

    if upper.startswith("EDIT "):
        draft = _latest_pending_draft()
        if not draft:
            return _send_ack(from_number, "No pending draft found.")
        new_text = text[5:].strip()
        draft.drafted_reply = new_text
        gmail_handler.send_email(draft.from_email, f"Re: {draft.subject or ''}".strip(), new_text)
        draft.status = "edited"
        db.session.commit()
        return _send_ack(from_number, "Draft edited and sent.")

    if upper == "SKIP":
        draft = _latest_pending_draft()
        if not draft:
            return _send_ack(from_number, "No pending draft found.")
        draft.status = "skipped"
        db.session.commit()
        return _send_ack(from_number, "Draft skipped.")

    if upper.startswith("BOOK ") and len(parts) >= 4:
        name, day, time_text = parts[1], parts[2], parts[3]
        meeting = book_meeting(name, day, time_text)
        if not meeting:
            return _send_ack(from_number, "Contact not found for booking.")
        return _send_ack(from_number, f"Meeting booked with {name}.")

    if upper.startswith("MEET ") and len(parts) >= 4:
        name = parts[1]
        urgency = parts[-1]
        purpose = " ".join(parts[2:-1])
        contact = Contact.query.filter(Contact.name.ilike(f"%{name}%")).first()
        if not contact or not contact.email:
            return _send_ack(from_number, f"Need contact details for {name}.")
        draft_text = f"Drafted outbound meeting request for {contact.name} ({urgency}) about {purpose}."
        draft = Draft(
            from_email=contact.email,
            from_name=contact.name,
            subject=f"Meeting request: {purpose}",
            original_message="",
            drafted_reply=draft_text,
            status="pending",
        )
        db.session.add(draft)
        db.session.commit()
        return _send_ack(from_number, "Outbound meeting draft queued for approval.")

    if upper.startswith("REMIND "):
        task = PersonalTask(description=text[7:].strip(), category="reminder", priority="medium")
        db.session.add(task)
        db.session.commit()
        return _send_ack(from_number, "Reminder saved.")

    if upper.startswith("DONE ") and len(parts) >= 3:
        name = parts[1]
        notes = " ".join(parts[2:])
        contact = Contact.query.filter(Contact.name.ilike(f"%{name}%")).first()
        meeting = (
            Meeting.query.filter_by(contact_id=contact.id).order_by(Meeting.scheduled_at.desc()).first() if contact else None
        )
        if not contact or not meeting:
            return _send_ack(from_number, "No matching meeting found.")
        row = MeetingNote(meeting_id=meeting.id, contact_id=contact.id, notes=notes)
        db.session.add(row)
        db.session.commit()
        return _send_ack(from_number, "Meeting note saved.")

    if upper == "URGENT":
        draft = _latest_pending_draft()
        if not draft:
            return _send_ack(from_number, "No pending draft to flag.")
        draft.status = "urgent"
        db.session.commit()
        return _send_ack(from_number, "Latest draft flagged urgent.")

    if upper == "OVERRIDE":
        flag = RuntimeFlag.query.filter_by(key="override_meetings").first()
        if not flag:
            flag = RuntimeFlag(key="override_meetings", value="1")
            db.session.add(flag)
        else:
            flag.value = "1"
        db.session.commit()
        return _send_ack(from_number, "Override enabled for deep work day scheduling.")

    if upper.startswith("BLOCK "):
        identifier = text[6:].strip()
        contact = Contact.query.filter((Contact.email == identifier) | (Contact.name.ilike(f"%{identifier}%"))).first()
        if contact:
            contact.is_blocked = 1
        if not BlockedSender.query.filter_by(identifier=identifier).first():
            db.session.add(BlockedSender(identifier=identifier, reason="manual_block"))
        db.session.commit()
        return _send_ack(from_number, f"Blocked: {identifier}")

    if upper.startswith("ADD CONTACT "):
        return _parse_add_contact(parts, from_number)

    if upper.startswith("REMOVE CONTACT "):
        name = text[len("REMOVE CONTACT "):].strip()
        deleted = Contact.query.filter(Contact.name.ilike(f"%{name}%")).delete()
        db.session.commit()
        return _send_ack(from_number, f"Removed {deleted} contact(s) for {name}.")

    if upper == "LIST CONTACTS":
        contacts = Contact.query.filter_by(is_blocked=0).order_by(Contact.name.asc()).all()
        formatted = "\n".join(f"- {c.name} <{c.email or '-'}> ({c.relationship_type or 'unknown'})" for c in contacts) or "No contacts"
        return _send_ack(from_number, formatted)

    if upper.startswith("TRAVEL ") and len(parts) >= 4:
        destination = parts[1]
        dates = parts[2]
        purpose = " ".join(parts[3:])
        handle_travel_request(destination, dates, purpose, from_number)
        return "travel_processed"

    if upper == "CALL REPORT":
        today = datetime.utcnow().date()
        logs = MessageLog.query.filter(MessageLog.timestamp >= datetime(today.year, today.month, today.day)).all()
        report = f"Today's activity: {len(logs)} message(s) logged."
        return _send_ack(from_number, report)

    if upper.startswith("ADD ") and upper.endswith(" SKIP"):
        latest = Draft.query.filter_by(status="unknown_sender").order_by(Draft.created_at.desc()).first()
        if latest:
            latest.status = "skipped"
            db.session.commit()
        return _send_ack(from_number, "Unknown sender skipped.")

    if upper.startswith("ADD ") and upper.endswith(" BLOCK"):
        latest = Draft.query.filter_by(status="unknown_sender").order_by(Draft.created_at.desc()).first()
        if latest:
            if not BlockedSender.query.filter_by(identifier=latest.from_email).first():
                db.session.add(BlockedSender(identifier=latest.from_email, reason="unknown_sender_block"))
            latest.status = "skipped"
            db.session.commit()
        return _send_ack(from_number, "Unknown sender blocked.")

    return _send_ack(from_number, "Unknown command.")

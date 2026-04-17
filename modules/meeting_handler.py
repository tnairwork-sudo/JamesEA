from __future__ import annotations

from datetime import datetime, timedelta

import pytz

from database import db
from database.models import Contact, Meeting, MeetingNote
from modules import claude_handler
from modules.calendar_handler import create_event, get_available_slots
from modules.research_handler import get_contact_info
from modules.whatsapp_handler import send_whatsapp

IST = pytz.timezone("Asia/Kolkata")


def _format_slots(slots: list[datetime]) -> list[str]:
    return [slot.astimezone(IST).strftime("%a %d %b, %I:%M %p IST") for slot in slots]


def handle_inbound_meeting_request(contact: Contact, email_body: str) -> str:
    purpose = email_body.strip().split("\n")[0][:140]
    slots = get_available_slots(count=2)
    slot_text = _format_slots(slots) if slots else ["Thu 11:00 IST", "Fri 03:00 IST"]
    draft = claude_handler.draft_meeting_request({"name": contact.name, "email": contact.email}, purpose, slot_text)

    meeting = Meeting(contact_id=contact.id, purpose=purpose, status="pending", notes="Inbound meeting request")
    db.session.add(meeting)
    db.session.commit()
    return draft


def book_meeting(contact_name: str, day: str, time_text: str, purpose: str = "Meeting") -> Meeting | None:
    contact = Contact.query.filter(Contact.name.ilike(f"%{contact_name}%"), Contact.is_blocked == 0).first()
    if not contact:
        return None

    target = datetime.now(IST) + timedelta(days=1)
    days = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    desired = days.get(day.lower(), target.weekday())
    while target.weekday() != desired:
        target += timedelta(days=1)

    try:
        hour, minute = [int(x) for x in time_text.split(":", 1)]
    except Exception:
        hour, minute = 11, 0
    start = IST.localize(datetime(target.year, target.month, target.day, hour, minute))
    end = start + timedelta(minutes=30)

    event_id = create_event(
        summary=f"Meeting: {contact.name}",
        start=start,
        end=end,
        attendees=[email for email in [contact.email] if email],
        description=f"Agenda: {purpose}\nLooking forward to it",
    )
    meeting = Meeting(
        contact_id=contact.id,
        purpose=purpose,
        scheduled_at=start,
        duration_minutes=30,
        status="confirmed",
        calendar_event_id=event_id,
        notes="Booked via command",
    )
    db.session.add(meeting)
    db.session.commit()
    return meeting


def send_guest_reminder(meeting_id: int) -> bool:
    meeting = Meeting.query.get(meeting_id)
    if not meeting or not meeting.contact:
        return False
    if not meeting.contact.whatsapp_number:
        return False

    at = meeting.scheduled_at.astimezone(IST).strftime("%I:%M %p IST") if meeting.scheduled_at else "scheduled time"
    body = f"Looking forward to seeing you tomorrow at {at}. Let me know if anything changes."
    return send_whatsapp(meeting.contact.whatsapp_number, body)


def send_pre_meeting_brief(meeting_id: int, to_number: str) -> bool:
    meeting = Meeting.query.get(meeting_id)
    if not meeting or not meeting.contact:
        return False

    notes = MeetingNote.query.filter_by(contact_id=meeting.contact_id).order_by(MeetingNote.logged_at.desc()).limit(5).all()
    history = " | ".join(n.notes for n in notes) if notes else "No prior notes logged"
    research = get_contact_info(meeting.contact.name, meeting.contact.email)
    brief = claude_handler.generate_pre_meeting_brief(
        contact={"name": meeting.contact.name, "email": meeting.contact.email},
        meeting={"purpose": meeting.purpose, "scheduled_at": str(meeting.scheduled_at)},
        research_text=research,
        history=history,
    )
    return send_whatsapp(to_number, brief)

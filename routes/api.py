from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from database import db
from database.models import Client, Draft, FamilyEvent, Matter, Meeting, PersonalTask

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.get("/brief")
def brief():
    today = datetime.utcnow().date()
    meetings = Meeting.query.filter(Meeting.scheduled_at >= datetime(today.year, today.month, today.day)).limit(5).all()
    pending_drafts = Draft.query.filter_by(status="pending").count()
    urgent_items = Draft.query.filter_by(status="urgent").count()
    data = {
        "date": today.isoformat(),
        "pending_drafts": pending_drafts,
        "urgent_items": urgent_items,
        "meetings": [
            {
                "id": m.id,
                "contact": m.contact.name if m.contact else "",
                "purpose": m.purpose,
                "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else None,
                "status": m.status,
            }
            for m in meetings
        ],
    }
    return jsonify(data)


@bp.get("/meetings")
def meetings():
    rows = Meeting.query.filter(Meeting.scheduled_at >= datetime.utcnow() - timedelta(days=1)).order_by(Meeting.scheduled_at.asc()).all()
    return jsonify(
        [
            {
                "id": m.id,
                "contact": m.contact.name if m.contact else "",
                "email": m.contact.email if m.contact else "",
                "purpose": m.purpose,
                "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else None,
                "status": m.status,
                "notes": m.notes,
            }
            for m in rows
        ]
    )


@bp.get("/clients")
def clients():
    rows = Client.query.order_by(Client.updated_at.desc()).all()
    return jsonify(
        [
            {
                "id": c.id,
                "name": c.contact.name if c.contact else "",
                "company": c.company,
                "matter_type": c.matter_type,
                "current_status": c.current_status,
                "last_contact_date": c.last_contact_date.isoformat() if c.last_contact_date else None,
                "next_action": c.next_action,
                "fee_agreed": c.fee_agreed,
            }
            for c in rows
        ]
    )


@bp.get("/matters")
def matters():
    order = {"red": 0, "yellow": 1, "green": 2}
    rows = Matter.query.all()
    rows.sort(key=lambda m: (order.get(m.status or "green", 3), m.next_hearing_date or datetime.max))
    return jsonify(
        [
            {
                "id": m.id,
                "title": m.title,
                "court": m.court,
                "next_hearing_date": m.next_hearing_date.isoformat() if m.next_hearing_date else None,
                "filing_deadlines": m.filing_deadlines,
                "documents_due": m.documents_due,
                "opposing_counsel": m.opposing_counsel,
                "status": m.status,
            }
            for m in rows
        ]
    )


@bp.get("/personal")
def personal():
    tasks = PersonalTask.query.order_by(PersonalTask.created_at.desc()).all()
    events = FamilyEvent.query.order_by(FamilyEvent.event_date.asc()).all()
    return jsonify(
        {
            "tasks": [
                {
                    "id": t.id,
                    "description": t.description,
                    "status": t.status,
                    "priority": t.priority,
                    "category": t.category,
                }
                for t in tasks
            ],
            "family_events": [
                {
                    "id": e.id,
                    "name": e.name,
                    "event_type": e.event_type,
                    "event_date": e.event_date.isoformat(),
                }
                for e in events
            ],
        }
    )


@bp.get("/drafts")
def drafts():
    rows = Draft.query.filter(Draft.status.in_(["pending", "urgent", "unknown_sender"])).order_by(Draft.created_at.desc()).all()
    return jsonify(
        [
            {
                "id": d.id,
                "from_name": d.from_name,
                "from_email": d.from_email,
                "subject": d.subject,
                "drafted_reply": d.drafted_reply,
                "status": d.status,
            }
            for d in rows
        ]
    )


@bp.patch("/tasks/<int:task_id>")
def mark_task_done(task_id: int):
    task = PersonalTask.query.get_or_404(task_id)
    payload = request.get_json(silent=True) or {}
    task.status = payload.get("status", "done")
    task.completed_at = datetime.utcnow() if task.status == "done" else None
    db.session.commit()
    return jsonify({"ok": True, "task_id": task.id, "status": task.status})

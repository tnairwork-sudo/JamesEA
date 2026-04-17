from __future__ import annotations

import os
from datetime import date, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from database.models import Draft, FamilyEvent, Meeting
from modules import claude_handler
from modules.gmail_handler import gmail_handler
from modules.meeting_handler import send_guest_reminder, send_pre_meeting_brief
from modules.whatsapp_handler import make_call, send_whatsapp

scheduler = BackgroundScheduler(timezone="Asia/Kolkata")


def run_morning_brief() -> None:
    today = datetime.now()
    meetings = Meeting.query.filter(Meeting.scheduled_at >= today, Meeting.scheduled_at < today + timedelta(days=1)).all()
    meeting_summary = "; ".join(
        f"{m.contact.name if m.contact else 'Guest'} at {m.scheduled_at.strftime('%H:%M')}" for m in meetings if m.scheduled_at
    ) or "No meetings today"

    data = {
        "day": today.strftime("%A"),
        "date": today.strftime("%d %b %Y"),
        "court": "Check hearings and deadlines in next 7 days",
        "meetings": meeting_summary,
        "follow_up": "Review clients not contacted in 14+ days",
        "family": "No family event within 3 days",
        "priority": "Resolve highest urgency revenue matter first",
    }
    brief = claude_handler.generate_morning_brief(data)
    send_whatsapp(to=os.getenv("TUSHAAR_WHATSAPP", ""), body=brief)


def run_family_reminders() -> None:
    target = date.today() + timedelta(days=3)
    rows = FamilyEvent.query.filter_by(event_date=target).all()
    for event in rows:
        send_whatsapp(
            os.getenv("TUSHAAR_WHATSAPP", ""),
            f"Family reminder: {event.name} ({event.event_type}) in 3 days. Suggested action: send a thoughtful note.",
        )


def run_pre_meeting_briefs() -> None:
    now = datetime.now()
    soon = now + timedelta(hours=1)
    meetings = Meeting.query.filter(Meeting.status == "confirmed", Meeting.scheduled_at >= now, Meeting.scheduled_at <= soon).all()
    for meeting in meetings:
        send_pre_meeting_brief(meeting.id, os.getenv("TUSHAAR_WHATSAPP", ""))


def run_guest_reminders() -> None:
    now = datetime.now()
    soon = now + timedelta(hours=24)
    meetings = Meeting.query.filter(Meeting.status == "confirmed", Meeting.scheduled_at >= now, Meeting.scheduled_at <= soon).all()
    for meeting in meetings:
        send_guest_reminder(meeting.id)


def run_urgent_escalation() -> None:
    threshold = datetime.utcnow() - timedelta(minutes=15)
    urgent_pending = (
        Draft.query.filter(Draft.status == "urgent", Draft.created_at <= threshold)
        .order_by(Draft.created_at.asc())
        .first()
    )
    if urgent_pending:
        make_call(os.getenv("TUSHAAR_WHATSAPP", ""))


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(gmail_handler.check_new_emails, IntervalTrigger(minutes=2), id="gmail_poll", replace_existing=True)
    scheduler.add_job(run_morning_brief, CronTrigger(hour=6, minute=30), id="morning_brief", replace_existing=True)
    scheduler.add_job(run_family_reminders, CronTrigger(hour=9, minute=0), id="family_reminders", replace_existing=True)
    scheduler.add_job(run_pre_meeting_briefs, IntervalTrigger(minutes=10), id="pre_meeting_briefs", replace_existing=True)
    scheduler.add_job(run_guest_reminders, IntervalTrigger(minutes=15), id="guest_reminders", replace_existing=True)
    scheduler.add_job(run_urgent_escalation, IntervalTrigger(minutes=15), id="urgent_escalation", replace_existing=True)
    scheduler.start()

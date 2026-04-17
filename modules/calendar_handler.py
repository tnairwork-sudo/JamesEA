from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta

import pytz

from database.models import Meeting, RuntimeFlag

IST = pytz.timezone("Asia/Kolkata")

def _override_active() -> bool:
    flag = RuntimeFlag.query.filter_by(key="override_meetings").first()
    return bool(flag and flag.value == "1")

def _allowed_day(dt: datetime) -> bool:
    weekday = dt.weekday()  # Mon=0
    if weekday == 6:
        return False
    if weekday in (0, 1, 2):
        return _override_active()
    return weekday in (3, 4, 5)

def _within_hours(dt: datetime) -> bool:
    local_dt = dt.astimezone(IST)
    return time(11, 0) <= local_dt.time() <= time(18, 0)

def _existing_counts() -> dict:
    counts: dict = defaultdict(int)
    for m in Meeting.query.filter(Meeting.status.in_("pending", "confirmed")).all():
        if m.scheduled_at:
            day = m.scheduled_at.astimezone(IST).date().isoformat()
            counts[day] += 1
    return counts

def get_available_slots(days: list[str] | None = None, count: int = 2) -> list[datetime]:
    days = days or ["thursday", "friday", "saturday"]
    day_idx = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5}
    wanted = {day_idx[d.lower()] for d in days if d.lower() in day_idx}
    slots: list[datetime] = []
    now = datetime.now(IST).replace(minute=0, second=0, microsecond=0)
    counts = _existing_counts()

    for ahead in range(1, 21):
        d = now + timedelta(days=ahead)
        if d.weekday() not in wanted and not _override_active():
            continue
        if not _allowed_day(d):
            continue
        day_key = d.date().isoformat()
        if counts.get(day_key, 0) >= 4:
            continue
        for hr in (11, 12, 14, 15, 16, 17):
            candidate = IST.localize(datetime(d.year, d.month, d.day, hr, 0))
            if candidate <= now or not _within_hours(candidate):
                continue
            overlap = Meeting.query.filter(
                Meeting.status.in_("pending", "confirmed"),
                Meeting.scheduled_at >= candidate - timedelta(minutes=30),
                Meeting.scheduled_at <= candidate + timedelta(minutes=30),
            ).first()
            if overlap:
                continue
            slots.append(candidate)
            if len(slots) >= count:
                return slots
    return slots

def create_event(summary: str, start: datetime, end: datetime, attendees: list[str], description: str) -> str:
    _ = (end, attendees, description)
    event_id = f"local-{int(start.timestamp())}-{abs(hash(summary)) % 99999}"
    return event_id

def update_event(event_id: str, **kwargs) -> bool:
    _ = kwargs
    return bool(event_id)

def delete_event(event_id: str) -> bool:
    return bool(event_id)
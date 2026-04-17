from datetime import datetime

from database import db


class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True)
    phone = db.Column(db.String(50))
    whatsapp_number = db.Column(db.String(50))
    relationship_type = db.Column(db.String(50))
    trust_level = db.Column(db.String(20), default="medium")
    is_blocked = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey("contacts.id"), nullable=False)
    company = db.Column(db.String(255))
    matter_type = db.Column(db.String(255))
    current_status = db.Column(db.String(50), default="green")
    last_contact_date = db.Column(db.Date)
    next_action = db.Column(db.Text)
    fee_agreed = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contact = db.relationship("Contact", backref=db.backref("clients", lazy=True))


class Matter(db.Model):
    __tablename__ = "matters"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    court = db.Column(db.String(255))
    next_hearing_date = db.Column(db.DateTime)
    filing_deadlines = db.Column(db.Text)
    documents_due = db.Column(db.Text)
    opposing_counsel = db.Column(db.String(255))
    status = db.Column(db.String(20), default="green")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client = db.relationship("Client", backref=db.backref("matters", lazy=True))


class Meeting(db.Model):
    __tablename__ = "meetings"

    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey("contacts.id"), nullable=False)
    purpose = db.Column(db.Text)
    scheduled_at = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer, default=30)
    status = db.Column(db.String(20), default="pending")
    calendar_event_id = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contact = db.relationship("Contact", backref=db.backref("meetings", lazy=True))


class MeetingNote(db.Model):
    __tablename__ = "meeting_notes"

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey("meetings.id"), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey("contacts.id"), nullable=False)
    notes = db.Column(db.Text, nullable=False)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)


class FamilyEvent(db.Model):
    __tablename__ = "family_events"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    recurring = db.Column(db.Integer, default=0)
    reminder_days_before = db.Column(db.Integer, default=3)
    notes = db.Column(db.Text)


class PersonalTask(db.Model):
    __tablename__ = "personal_tasks"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="general")
    priority = db.Column(db.String(20), default="medium")
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)


class Draft(db.Model):
    __tablename__ = "drafts"

    id = db.Column(db.Integer, primary_key=True)
    from_email = db.Column(db.String(255), nullable=False)
    from_name = db.Column(db.String(255))
    subject = db.Column(db.String(255))
    original_message = db.Column(db.Text)
    drafted_reply = db.Column(db.Text)
    status = db.Column(db.String(30), default="pending")
    gmail_message_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BlockedSender(db.Model):
    __tablename__ = "blocked_senders"

    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(255), unique=True, nullable=False)
    blocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(db.String(255))


class MessageLog(db.Model):
    __tablename__ = "message_log"

    id = db.Column(db.Integer, primary_key=True)
    direction = db.Column(db.String(20), nullable=False)
    channel = db.Column(db.String(20), nullable=False)
    sender = db.Column(db.String(255))
    recipient = db.Column(db.String(255))
    subject = db.Column(db.String(255))
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class RuntimeFlag(db.Model):
    __tablename__ = "runtime_flags"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

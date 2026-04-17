import os
from typing import Any, Dict, List, Optional

try:
    from anthropic import Anthropic
except Exception:  # pragma: no cover
    Anthropic = None


MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
VOICE_RULES = """
You are James, Tushaar's executive assistant.
Voice rules:
- Warm, human, discreet
- Tone adapts: formal for judges/senior advocates/GCs/opposing counsel; relaxed for friends/family/creative people
- Never use em dashes
- Never say "I hope this finds you well"
- Never say "please revert" or "do the needful"
- Never apologize for slow replies
- Never mention Tushaar is busy
- Max 4 lines in first message
- Always end with a clear next step
- If asked if human: respond "I'm Tushaar's assistant - [continue naturally]"
""".strip()
INTENT_CATEGORIES = [
    "new_legal_inquiry",
    "existing_client_update",
    "court_or_counsel",
    "meeting_request",
    "personal_family",
    "unknown",
]

def _client() -> Any:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or Anthropic is None:
        return None
    return Anthropic(api_key=api_key)

def _ask_claude(prompt: str, fallback: str) -> str:
    client = _client()
    if client is None:
        return fallback
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=600,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in response.content if getattr(block, "text", None)).strip()
        return text or fallback
    except Exception:
        return fallback

def classify_email(email_body: str, sender_info: Optional[Dict] = None) -> str:
    sender = sender_info or {}
    heuristic = (email_body or "").lower()
    if any(x in heuristic for x in ["hearing", "court", "counsel", "mentioning"]):
        return "court_or_counsel"
    if any(x in heuristic for x in ["meeting", "slot", "schedule", "availability"]):
        return "meeting_request"
    if any(x in heuristic for x in ["dad", "mom", "family", "birthday", "anniversary"]):
        return "personal_family"

    prompt = (
        VOICE_RULES + "\n"
        "Classify the email into exactly one category from:\n"
        + ", ".join(INTENT_CATEGORIES)
        + "\nReturn only the category.\n\n"
        "Sender: " + str(sender) + "\n"
        "Email body:\n" + str(email_body)
    )
    category = _ask_claude(prompt, "unknown").splitlines()[0].strip().lower()
    return category if category in INTENT_CATEGORIES else "unknown"

def draft_reply(email_body: str, sender_info: Dict, contact_row: Any, intent: str) -> str:
    fallback = "Thank you for your message. James here from Tushaar's office. I have noted this and will share a suitable next step shortly."
    prompt = (
        VOICE_RULES + "\n"
        "Write an email reply in 2-4 short lines.\n"
        "Intent: " + intent + "\n"
        "Sender info: " + str(sender_info) + "\n"
        "Contact: " + str(getattr(contact_row, "name", None)) + "\n"
        "Incoming email:\n" + str(email_body)
    )
    return _ask_claude(prompt, fallback)

def draft_meeting_request(contact: Dict, purpose: str, slots: List[str]) -> str:
    slot_lines = "\n".join("- " + slot for slot in slots[:2])
    fallback = (
        "Hi " + contact.get("name", "there") + ",\n"
        "Tushaar would love to find time to discuss " + purpose + ".\n"
        "Would either of these work for you?\n" + slot_lines + "\n"
        "Looking forward to it"
    )
    prompt = (
        VOICE_RULES + "\n"
        "Meeting language rules:\n"
        "- Use 'Tushaar would love to find time'\n"
        "- Use 'Would either of these work for you'\n"
        "- End with 'Looking forward to it'\n"
        "- Avoid 'Please revert' and 'Do the needful'\n\n"
        "Draft a concise meeting email.\n"
        "Contact: " + str(contact) + "\n"
        "Purpose: " + purpose + "\n"
        "Slots:\n" + slot_lines
    )
    return _ask_claude(prompt, fallback)

def generate_morning_brief(data_dict: Dict) -> str:
    fallback = (
        data_dict.get("day", "Today") + ", " + data_dict.get("date", "") + "\n"
        "COURT: " + data_dict.get("court", "No urgent updates") + "\n"
        "MEETINGS: " + data_dict.get("meetings", "No meetings") + "\n"
        "FOLLOW-UP: " + data_dict.get("follow_up", "None") + "\n"
        "FAMILY: " + data_dict.get("family", "No reminders") + "\n"
        "PRIORITY: " + data_dict.get("priority", "Review pending drafts")
    )
    prompt = (
        VOICE_RULES + "\n"
        "Generate a concise morning brief in max 10 lines.\n"
        "Data: " + str(data_dict)
    )
    return _ask_claude(prompt, fallback)

def generate_pre_meeting_brief(contact: Dict, meeting: Dict, research_text: str, history: str) -> str:
    name = contact.get("name", "Guest")
    purpose = meeting.get("purpose", "discussion")
    fallback = (
        "1) " + name + " is coming for " + purpose + ".\n"
        "2) They want: " + purpose + ".\n"
        "3) Research: " + (research_text or "No extra public details found.") + "\n"
        "4) Opening line: Great to see you, shall we begin with your top priority today?"
    )
    prompt = (
        VOICE_RULES + "\n"
        "Create exactly 4 lines for a WhatsApp pre-meeting brief.\n"
        "Contact: " + str(contact) + "\n"
        "Meeting: " + str(meeting) + "\n"
        "Research: " + str(research_text) + "\n"
        "History: " + str(history)
    )
    return _ask_claude(prompt, fallback)
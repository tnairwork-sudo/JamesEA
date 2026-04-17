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
- If asked if human: respond "I'm Tushaar's assistant — [continue naturally]"
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

    prompt = f"""
{VOICE_RULES}
Classify the email into exactly one category from:
{", ".join(INTENT_CATEGORIES)}
Return only the category.

Sender: {sender}
Email body:
{email_body}
""".strip()
    category = _ask_claude(prompt, "unknown").splitlines()[0].strip().lower()
    return category if category in INTENT_CATEGORIES else "unknown"

def draft_reply(email_body: str, sender_info: Dict, contact_row: Any, intent: str) -> str:
    fallback = "Thank you for your message. James here from Tushaar's office. I have noted this and will share a suitable next step shortly."
    prompt = f"""
{VOICE_RULES}
Write an email reply in 2-4 short lines.
Intent: {intent}
Sender info: {sender_info}
Contact: {getattr(contact_row, 'name', None)}
Incoming email:
{email_body}
""".strip()
    return _ask_claude(prompt, fallback)

def draft_meeting_request(contact: Dict, purpose: str, slots: List[str]) -> str:
    slot_lines = "\n".join(f"- {slot}" for slot in slots[:2])
    fallback = (
        f"Hi {contact.get('name', 'there')},\n"
        f"Tushaar would love to find time to discuss {purpose}.\n"
        f"Would either of these work for you?\n{slot_lines}\n"
        "Looking forward to it"
    )
    prompt = f"""
{VOICE_RULES}
Meeting language rules:
- Use "Tushaar would love to find time"
- Use "Would either of these work for you"
- End with "Looking forward to it"
- Avoid "Please revert" and "Do the needful"

Draft a concise meeting email.
Contact: {contact}
Purpose: {purpose}
Slots:\n{slot_lines}
""".strip()
    return _ask_claude(prompt, fallback)

def generate_morning_brief(data_dict: Dict) -> str:
    fallback = (
        f"{data_dict.get('day', 'Today')}, {data_dict.get('date', '')}\n"
        f"COURT: {data_dict.get('court', 'No urgent updates')}\n"
        f"MEETINGS: {data_dict.get('meetings', 'No meetings')}\n"
        f"FOLLOW-UP: {data_dict.get('follow_up', 'None')}\n"
        f"FAMILY: {data_dict.get('family', 'No reminders')}\n"
        f"PRIORITY: {data_dict.get('priority', 'Review pending drafts')}"
    )
    prompt = f"""
{VOICE_RULES}
Generate a concise morning brief in max 10 lines.
Data: {data_dict}
""".strip()
    return _ask_claude(prompt, fallback)

def generate_pre_meeting_brief(contact: Dict, meeting: Dict, research_text: str, history: str) -> str:
    fallback = (
        f"1) {contact.get('name', 'Guest')} is coming for {meeting.get('purpose', 'discussion')}.
"
        f"2) They want: {meeting.get('purpose', 'General catch-up')}.
"
        f"3) Research: {research_text or 'No extra public details found.'}\n"
        f"4) Opening line: Great to see you, shall we begin with your top priority today?"
    )
    prompt = f"""
{VOICE_RULES}
Create exactly 4 lines for a WhatsApp pre-meeting brief.
Contact: {contact}
Meeting: {meeting}
Research: {research_text}
History: {history}
""".strip()
    return _ask_claude(prompt, fallback)

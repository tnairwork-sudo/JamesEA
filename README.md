# JamesEA

James is a web-based AI Executive Assistant built with Flask + SQLite for email triage, meeting workflows, travel planning, reminders, and WhatsApp approvals.

## Features

- Gmail triage flow with whitelist and unknown sender handling
- Claude-powered classification and drafting (`claude-sonnet-4-20250514`)
- WhatsApp command parser for approvals and operations
- Meeting slot logic with Thu/Fri/Sat preference and override support
- APScheduler jobs for polling, morning brief, reminders, and escalations
- Mobile-first PWA dashboard (installable)

## Setup

1. Copy env template:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run:
   ```bash
   python3 app.py
   ```

On startup, James opens `http://localhost:5001` in Chrome (fallback to default browser).

## API Endpoints

- `GET /api/brief`
- `GET /api/meetings`
- `GET /api/clients`
- `GET /api/matters`
- `GET /api/personal`
- `GET /api/drafts`
- `PATCH /api/tasks/<id>`

## Webhooks

- `POST /webhook/whatsapp`
- `POST /webhook/gmail`

## Commands (WhatsApp)

- `SEND`
- `EDIT [new text]`
- `SKIP`
- `BOOK [name] [day] [time]`
- `MEET [name] [purpose] [urgency]`
- `REMIND [anything]`
- `DONE [name] [notes]`
- `URGENT`
- `OVERRIDE`
- `BLOCK [name or email]`
- `ADD CONTACT [name] [email] [relationship]`
- `REMOVE CONTACT [name]`
- `LIST CONTACTS`
- `TRAVEL [destination] [dates] [purpose]`
- `CALL REPORT`
- `ADD [name] SKIP`
- `ADD [name] BLOCK`

# Social Pulse (SentimentPulse)

Real-time dashboard for collecting, analyzing, and responding to public sentiment using AI and manual workflows.

This prototype implements a full loop: collect public mentions, analyze with an LLM, aggregate stats, and take actions from the dashboard while persisting campaigns and replies in a SQLite DB. It currently supports the Taboola and Realize entities.

## Project Overview
- Dynamic statistics are computed live from backend mentions.
- Campaigns can be created from Hot Topics and are persisted (list/create endpoints).
- Reply flows support AI-simulated and manual replies; replies are stored and associated with mentions.
- Both replies and campaigns survive backend restarts (SQLite persistence).
- Entity filtering supports Taboola and Realize.
- Timestamps displayed in the UI are the true backend timestamps.

## Architecture Diagram

```
┌─────────────┐   ┌───────────┐   ┌──────────┐   ┌────────────┐
│   Collector │ → │  Analyzer │ → │Aggregator│ → │  Dashboard │
│  (Search)   │   │   (LLM)   │   │ (Stats)  │   │    (UI)    │
└─────────────┘   └───────────┘   └──────────┘   └───────┬─────┘
                                                        │
                                                        ▼
                                                 ┌──────────────┐
                                                 │ Action Agent │
                                                 │ (Responder)  │
                                                 └─────┬────────┘
                                                       │
    ┌──────────────┬───────────────────────┬────────┴──────────────┐
    ▼              ▼                       ▼                       ▼
[Reply (AI)]   [Reply (Manual)]   [Create/Track Campaign]   [Mark as Handled]

                                        │
                                        ▼
                    ┌─────────────────────────────┐
                    │       Tracking Panel        │
                    │  - Campaigns (history)      │
                    │  - Replies (AI/manual, log) │
                    └─────────────────────────────┘
```

## Feature List (Implemented)
- Dynamic response statistics from live mentions
- Persistent campaign creation and management (endpoints for save/list)
- Reply support (manual and AI simulation), tracked in UI and DB per mention
- Tracking of replied mentions and opened campaigns
- Entity filtering for Taboola and Realize
- Timestamps for all mentions come from backend data
- Data persists after backend reloads (SQLite)

## Sample UX Block (Pseudo-screenshot)

```
Latest Mentions
┌──────────────────────────────────────────────────────────────────────────── ┐
│ Source  Entity   Sentiment  Author   Date               Actions             │
├──────────────────────────────────────────────────────────────────────────── ┤
│ Reddit  Taboola  Negative   u/alex   2025-11-24 10:15  [Reply] [Campaign]   │
│  “Taboola widgets slow my page down. Any settings to tune this?”            │
│  Topics: performance, user_experience | Insight: Perf complaints            │
│  Summary: Performance issues reported on widget load.                       │
├──────────────────────────────────────────────────────────────────────────── ┤
│ Web     Realize  Positive   blog.com 2025-11-23 17:12  [Reply] [Handled]    │
│  “Realize onboarding was smooth; docs were clear.”                          │
│  Topics: onboarding | Insight: Positive onboarding feedback                 │
│  Summary: Smooth onboarding experience.                                     │
└──────────────────────────────────────────────────────────────────────────── ┘

Action Panel
- Complaints | Questions | Reviews | Praises
- Replies Sent: 4   Active Campaigns: 2   Pending: 6

Recent AI Campaigns
- “Ad Intrusiveness” • 2025-11-24 09:40 • AI proposal initiated (3 mentions)
```

## Quick Setup

1) Backend (FastAPI)
- Requirements: Python 3.10+
- Create `.env` in project root:
  - `SERPAPI_KEY=...`
  - `GOOGLE_API_KEY=...` (Gemini)
- Install and run:
```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

2) Frontend (React + TS)
- From `src/ui/frontend`:
```bash
npm install
npm start
```
Default URLs:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

3) Seed Realize (optional)
- Create a persistent Realize mention:
```bash
curl -X POST http://localhost:8000/api/seed/realize
```
- In the UI, set Entity filter to “Realize” to view it.

4) Test Campaigns
- From Hot Topics, click “Start Campaign” → a campaign is created (POST /api/campaigns) and appears in “Recent AI Campaigns”.

5) Test Replies
- Click “Reply” on a mention.
- Choose “Send AI Reply (Demo)” or write a Manual Reply.
- Reply persists (POST /api/mentions/{id}/reply), mention status becomes `sent`, and stats update.

## API Endpoints Used

Mentions
- GET `/api/mentions` — list analyzed mentions (filters: entity, sentiment, category, days, limit)
- GET `/api/mentions/{id}` — get a single mention
- POST `/api/mentions/{id}/reply` — create a reply and mark mention `response_status=sent`
- PATCH `/api/mentions/{id}/status` — update `response_status` and/or `actionable`
- GET `/api/mentions/{id}/replies` — list replies for a mention

Campaigns
- GET `/api/campaigns` — list campaigns (persisted)
- POST `/api/campaigns` — create a campaign (persisted)

Utility
- POST `/api/seed/realize` — seed one Realize mention for demo

## Design Notes
- What’s persistent in DB: mentions (analyzed items), replies, campaigns.
- What’s demo-only: AI reply text is simulated from the UI; campaign “proposal” copy is generated in-UI but only the campaign record is persisted.
- Out of scope: email sending, external posting to Reddit/Twitter/LinkedIn.
- Entities supported: Taboola and Realize.

## Testing Instructions
- Persistence: restart backend and refresh UI → campaigns and replies remain.
- Campaign tracking: create multiple campaigns and verify they appear in Recent AI Campaigns after reload.
- Reply history: reply to a mention; hit GET `/api/mentions/{id}/replies` to verify DB rows; UI stats (Replies Sent) should increase.
- Entity filtering: filter by Taboola or Realize and verify listings and stats update.
- Timestamps: ensure UI date columns match backend `timestamp` values (no fallback to current time).

## How to run integration tests

- Requirements: install dev deps and pytest in your venv.
```bash
python -m pip install -r requirements.txt
python -m pip install pytest
```

- Run the end-to-end test with FastAPI TestClient (no external services required):
```bash
pytest -q tests/test_integration_e2e.py
```

What the test does:
- Starts with a fresh temporary SQLite DB.
- Optionally seeds one Realize mention via `POST /api/seed/realize`.
- Seeds a Taboola mention directly (bypasses collectors/LLM).
- Fetches mentions via DB fast-path and validates:
  - Entities: Taboola and Realize present (checks `entity_mentioned`).
  - Timestamps are ISO-parseable.
- Creates two replies (AI + manual) using `POST /api/mentions/{id}/reply` and verifies:
  - `response_status` becomes `sent` on re-fetch (DB fast-path).
  - `GET /api/mentions/{id}/replies` returns the persisted replies.
- Creates a campaign via `POST /api/campaigns` and confirms it appears in `GET /api/campaigns`.
- Validates entity filtering for Taboola and Realize.
- Simulates a reload (new TestClient) and confirms campaigns and statuses persist.

Expected output ends with a single test PASS, e.g.:
```
1 passed in 2.3s
```

### Troubleshooting integration tests
- If a re-fetch returns stale data, ensure the test uses `entity=<Entity>` and `use_db=true` on mentions GET.
- Avoid collector/LLM during tests; the DB fast-path is deterministic and uses seeded rows.
- You can lower cache TTL via env `CACHE_TTL_SECONDS=1` during tests if needed.
- If you see 429s in logs, you are hitting the collector path; switch to `use_db=true`.

## Example API Response for GET /api/mentions

```json
{
  "id": "google_592436940456322799",
  "text": "Taboola Reviews | Glassdoor\n90% of Taboola employees would recommend working there to a friend based on Glassdoor reviews. Employees also rated Taboola 4.3 out of 5 for work life balance, ...",
  "url": "https://www.glassdoor.co.in/Reviews/Taboola-Reviews-E386708.htm",
  "timestamp": "2025-11-24T13:30:16.946939",
  "platform": "google_search",
  "entity_mentioned": [
    "Taboola"
  ],
  "author": "glassdoor.co.in",
  "sentiment": "positive",
  "sentiment_score": 0.85,
  "rating": 4,
  "topics": [
    "employee_experience",
    "work_life_balance"
  ],
  "category": "review",
  "key_insight": "Taboola employees highly recommend working there and rate work life balance positively.",
  "summary": "Positive employee feedback highlights high recommendation and work-life balance.",
  "confidence": 0.98,
  "actionable": false,
  "response_status": "sent",
  "response_draft": null,
  "assigned_to": null
}
```

This response shows a typical mention item including fields such as `entity_mentioned` (an array of entities mentioned in the text), sentiment, timestamps, and `response_status` reflecting the current reply state.

Social Pulse (SentimentPulse)
Real-time dashboard for collecting, analyzing, and responding to public sentiment about Taboola and Realize using AI and manual workflows.

## Introduction
Social Pulse is a prototype AI agent that tracks public chatter around the brands Taboola and Realize, analyzing sentiment at a granular level and enabling real-time interaction via a dashboard.

## System Requirements
- Python 3.10 or above
- Node.js 16+ (for frontend React app)
- Poetry or pip (for Python dependency management)
- Environment variables setup for API keys

## Setup Instructions

### Backend (FastAPI)
Create a `.env` file at the project root containing:

```
SERPAPI_KEY=your_serpapi_key
GOOGLE_API_KEY=your_google_api_key
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the backend server:

```bash
uvicorn api.main:app --reload --port 8000
```

### Frontend (React)
Navigate to `src/ui/frontend`

Install dependencies:

```bash
npm install
```

Run the frontend development server:

```bash
npm start
```

## Architecture Overview

```
Collector (Search) → Analyzer (LLM) → Aggregator (Stats) → Dashboard (UI)
                                            ↓
                                      Action Agent (Responder)
                                      ┌───────────────┐
                                      │ Reply (AI)    │
                                      │ Reply (Manual)│
                                      │ Campaigns     │
                                      │ Mark Handled  │
                                      └───────────────┘
```

Data flows from collection, through analysis and aggregation, to visualization and action workflows.

## Features
- Live sentiment analysis and statistics updated from backend mentions.
- Entity filtering supports Taboola and Realize.
- Campaign creation and tracking persisted in SQLite.
- Reply workflows support AI-generated and manual replies.
- Persisted data survives backend restarts.
- All UI timestamps reflect backend data.

## Sample User Interface Snapshot
- Latest Mentions list with source, entity, sentiment, and quick actions (Reply, Campaign, Handled).

## API Endpoints Summary

| Method | Endpoint                   | Description                               |
| ------ | -------------------------- | ----------------------------------------- |
| GET    | /api/mentions              | List mentions with filters                |
| GET    | /api/mentions/{id}         | Get mention details                       |
| POST   | /api/mentions/{id}/reply   | Create a reply and mark mention as sent   |
| PATCH  | /api/mentions/{id}/status  | Update mention status and actionable flag |
| GET    | /api/mentions/{id}/replies | List replies for mention                  |
| GET    | /api/campaigns             | List campaigns                            |
| POST   | /api/campaigns             | Create a campaign                         |
| POST   | /api/seed/realize          | Seed a demo Realize mention               |

## Testing Instructions
To run integration tests:

```bash
python -m pip install -r requirements.txt
python -m pip install pytest
pytest -q tests/test_integration_e2e.py
```

Tests cover:
- DB seeding for Taboola and Realize mentions
- Reply creation and status updates
- Campaign creation and persistence
- Entity filtering validation
- Persistence across backend reloads

## Example API Response

```json
{
  "id": "google_592436940456322799",
  "text": "Taboola Reviews | Glassdoor...",
  "url": "https://glassdoor.co.in/Reviews/Taboola-Reviews-E386708.htm",
  "timestamp": "2025-11-24T13:30:16.946939",
  "platform": "google_search",
  "entity_mentioned": ["Taboola"],
  "author": "glassdoor.co.in",
  "sentiment": "positive",
  "sentiment_score": 0.85,
  "rating": 4,
  "topics": ["employee_experience", "work_life_balance"],
  "category": "review",
  "key_insight": "Taboola employees highly recommend working there...",
  "summary": "Positive employee feedback highlights...",
  "confidence": 0.98,
  "actionable": false,
  "response_status": "sent",
  "response_draft": null,
  "assigned_to": null
}
```

## Known Limitations and Future Work
- Limited live Google Search data for "Realize"; ingestion via CSV as fallback.
- UI can be extended for deeper filtering and trend analysis.
- Further prompt tuning to handle sarcasm and complex sentiment.

## License
MIT License

## References
- spec.md — technical specification and data models
- AGENTS.md — agent architecture and decisions

## License
MIT


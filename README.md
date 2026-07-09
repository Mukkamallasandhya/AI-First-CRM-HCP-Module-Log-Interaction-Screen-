# AI-First CRM — HCP Interaction Module

An AI-first "Log HCP Interaction" screen for pharma field reps, built for the
Round 1 technical assignment. Reps can log a healthcare-professional (HCP)
interaction either through a **structured form** or a **conversational chat
interface** backed by a **LangGraph agent** running on **Groq**.

![Screen reference](docs/screenshot-reference.png)

## Architecture

```
┌──────────────────────────────┐        ┌──────────────────────────────────┐
│  React + Redux (frontend)    │  REST  │  FastAPI (backend)                │
│  ┌────────────┐ ┌──────────┐ │◄──────►│  /api/interactions  /api/hcps     │
│  │ Structured │ │  AI Chat │ │        │  /api/chat  ──►  LangGraph agent  │
│  │   Form     │ │  Panel   │ │        │                     │            │
│  └────────────┘ └──────────┘ │        │                     ▼            │
└──────────────────────────────┘        │        ┌─────────────────────┐   │
                                         │        │  5 Tools:           │   │
                                         │        │  log_interaction    │   │
                                         │        │  edit_interaction   │   │
                                         │        │  search_hcp         │   │
                                         │        │  summarize_voice_note│  │
                                         │        │  schedule_followup  │   │
                                         │        └──────────┬──────────┘   │
                                         │                   ▼              │
                                         │        Groq (gemma2-9b-it /       │
                                         │        llama-3.3-70b-versatile)   │
                                         │                   │              │
                                         │                   ▼              │
                                         │        MySQL / Postgres (SQLAlchemy)│
                                         └──────────────────────────────────┘
```

- **Frontend:** React + Redux Toolkit. `interactionSlice` holds the structured
  form state; `chatSlice` holds the conversation. When the AI assistant logs
  or edits an interaction, the chat slice dispatches `applyAgentUpdate` so the
  structured form on the left stays in sync with what was logged via chat.
- **Backend:** FastAPI, three routers (`interactions`, `hcps`, `chat`).
- **AI agent:** A LangGraph `StateGraph` (`agent → tools → agent → ... → END`)
  bound to 5 tools, using `llama-3.3-70b-versatile` for conversational turns
  and `gemma2-9b-it` for fast structured entity extraction inside tools.
- **Database:** SQLAlchemy models for `HCP`, `Interaction`, `MaterialShared`,
  compatible with both Postgres and MySQL via `DATABASE_URL`. Falls back to a
  local SQLite file if no `DATABASE_URL` is set, so the project runs out of
  the box with zero external DB setup during review.

## The 5 LangGraph tools

| Tool | Purpose |
|---|---|
| `log_interaction` | Creates a new interaction row. If the rep supplies free text (typed or from a "voice note"), it calls the LLM internally to extract topics, sentiment, and materials before saving. |
| `edit_interaction` | Patches any field on an already-logged interaction (e.g. "actually mark that as Negative sentiment"). |
| `search_hcp` | Looks up the HCP roster by name/specialty/hospital, so the agent can resolve "Dr. Smith" to a real record, or answer "who have I seen in cardiology recently". |
| `summarize_voice_note` | Takes a raw transcript and returns a structured summary (summary, topics, sentiment, materials, suggested HCP) without saving — used so the rep can review/consent to the extraction before it's logged, matching the "Requires Consent" note in the UI. |
| `schedule_followup` | Sets a follow-up date + note on an existing interaction, with its own validation (date can't be in the past) — a distinct workflow from a generic field edit. |

## Running it locally

### 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt

cp .env.example .env
# then edit .env:
#   GROQ_API_KEY=<your key from https://console.groq.com>
#   DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/hcp_crm
#   (or) DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/hcp_crm

python seed.py        # loads a small demo HCP roster (Dr. Sarah Smith, etc.)
uvicorn app.main:app --reload --port 8000
```

The API is now live at `http://localhost:8000` (interactive docs at
`http://localhost:8000/docs`).

### 2. Frontend

```bash
cd frontend
npm install
npm start
```

Runs at `http://localhost:3000` and talks to the backend at
`http://localhost:8000` by default (override with `REACT_APP_API_BASE`).

## Using it

- **Structured form (left):** fill in HCP, type, date/time, attendees, topics,
  sentiment, materials, and follow-up, then **Save Interaction**.
- **Chat (right):** type something like:
  > Met Dr. Sarah Smith, discussed Prodo-X efficacy data, positive sentiment, left a brochure

  The agent calls `log_interaction`, saves the row, and replies confirming
  what was logged. Try:
  > Actually change the sentiment on that to Neutral

  which routes to `edit_interaction` using the interaction id from the prior
  turn. Or:
  > Remind me to follow up with her next Friday about the new dosing study

  which calls `schedule_followup`.

## Notes on the tech-stack choices from the brief

- **Frontend:** React 18 + Redux Toolkit, Inter font, plain CSS matching the
  provided reference screenshot's layout (structured form left, AI assistant
  chat right).
- **Backend:** Python + FastAPI.
- **AI agent framework:** LangGraph (`langgraph` `StateGraph` + prebuilt
  `ToolNode`/`tools_condition`).
- **LLMs:** Groq via `langchain-groq` — `gemma2-9b-it` for fast extraction,
  `llama-3.3-70b-versatile` for the conversational agent loop, matching the
  assignment's "may also consider llama-3.3-70b-versatile for context" note.
- **Database:** SQLAlchemy models compatible with MySQL or Postgres via a
  single `DATABASE_URL` env var.

## Repo structure

```
backend/
  app/
    agent/          LangGraph graph + 5 tools + Groq LLM clients
    routers/         interactions.py, hcp.py, chat.py
    models.py        SQLAlchemy ORM (HCP, Interaction, MaterialShared)
    schemas.py        Pydantic request/response models
    database.py, config.py, main.py
  seed.py            demo HCP roster loader
  requirements.txt
  .env.example
frontend/
  src/
    components/       LogInteractionForm.jsx, ChatPanel.jsx, HCPSearch.jsx
    store/             interactionSlice.js, chatSlice.js, store.js
    api/client.js
  package.json
```

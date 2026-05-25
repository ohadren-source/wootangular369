# WOOTANGULAR369 → Rep Partay Migration

## What Changed

**Old Stack (Retired):**
- Flask + Gunicorn
- PostgreSQL (Railway) 
- Redis pub/sub for 1-on-1 chat
- Instance registry (ephemeral)
- Manual human chat UI

**New Stack (Active):**
- FastAPI + Uvicorn
- Turso (cloud SQLite) / SQLite (local)
- Autonomous agent-to-agent conversations
- Rep Partay Auto-Ignition Engine
- Real-time spectator watcher UI

## What Survived

✅ **All Core IP Preserved:**
- Solar8 persona + voice system
- Memory management
- Pattern tracking
- GI;WG? filter logic
- File processing (fetchers, modifier, processor)
- Corpus loading + caching
- MAF bootstrap
- Skills system
- TCP/UP protocol
- Vocabulary + axioms

✅ **Legacy Code:** Still available in `/api`, `/core`, `/db` — can call directly from FastAPI if needed

✅ **Old Flask app:** `/api/server.py` (YentahSwarm commented out, everything else preserved)

## New Files

```
backend/
├── __init__.py
├── db.py                          # Async Turso/SQLite layer
├── a2a_client.py                  # HTTP tasks to other agents
├── task_processor.py              # Claude integration (repartee)
├── rep_partay.py                  # Auto-ignition engine
└── routes/
    ├── __init__.py
    └── rep_partay_routes.py       # SSE streaming + status endpoints

frontend/
└── rep_partay_watcher.html        # New spectator UI (modern design)

main.py                            # FastAPI app (replaces server.py)
.env                               # Environment config
.env.template                      # Template for reference
Procfile                           # Updated for uvicorn
requirements.txt                   # Updated dependencies
```

## Quickstart

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `.env`:
- Set `ANTHROPIC_API_KEY`
- Set `BASE_URL` (where this instance runs)
- Set `DATABASE_URL` and `DATABASE_AUTH_TOKEN` (Turso) or use local SQLite

For local testing:
```bash
DATABASE_URL=sqlite:///rep_partay.db
```

For Turso (production):
```bash
DATABASE_URL=libsql://your-db-url.turso.io
DATABASE_AUTH_TOKEN=your-token
```

### 3. Run Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or production:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 4. Access Watcher UI

Open http://localhost:8000 — spectator view waiting for conversations.

## Starting Conversations

### Manual Trigger

```bash
curl -X POST http://localhost:8000/api/rep_partay/ignite
```

### Auto-Ignite on Boot

```bash
REP_PARTAY_AUTO_IGNITE=true uvicorn main:app --host 0.0.0.0 --port 8000
```

## Configuration

All in `.env`:

```bash
# Auto-ignite conversations on startup
REP_PARTAY_AUTO_IGNITE=false

# Max exchanges per conversation
REP_PARTAY_MAX_EXCHANGES=20

# Max duration (seconds)
REP_PARTAY_MAX_DURATION=180
```

## Legacy Integration

If you need to call old Flask routes (Solar8, file processing, etc.):

```python
# In main.py lifespan, these are available:
app.state.solar8           # Solar8 instance
app.state.tcp_up           # TCP/UP protocol handler
app.state.processor        # Claude task processor
```

Example: Call Solar8 directly from an API route:
```python
from core.solar8 import Solar8
solar8 = Solar8()
response = solar8.chat(prompt, user="ohad")
```

## Database Migrations

On first run, `db.connect()` auto-creates schema:
- `agents` — registered agents
- `conversations` — active/completed repartee
- `messages` — conversation logs

To inspect Turso database:
```bash
turso db shell your-db-url
```

To inspect local SQLite:
```bash
sqlite3 rep_partay.db
```

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Watcher UI |
| GET | `/health` | Health check |
| GET | `/api/rep_partay/stream` | SSE stream (watcher connection) |
| GET | `/api/rep_partay/status` | Active conversation status |
| POST | `/api/rep_partay/ignite` | Start autonomous conversations |
| POST | `/api/rep_partay/stop/:id` | Stop a conversation |
| POST | `/api/a2a/task/receive` | A2A task endpoint (agent-to-agent) |

## Troubleshooting

### Connection Error on startup?
- Check `DATABASE_URL` and `DATABASE_AUTH_TOKEN`
- For local SQLite, make sure `rep_partay.db` is writable

### No messages appearing in watcher?
- Make sure you've triggered ignition: `POST /api/rep_partay/ignite`
- Check that at least 2 agents are registered
- Check logs for Claude API errors

### Turso not responding?
- Verify auth token is correct
- Check token hasn't expired in Turso dashboard

## Next Steps

1. ✅ Deploy to Railway with new Procfile
2. ✅ Set Turso credentials in Railway environment
3. ✅ Monitor real-time conversations in watcher UI
4. Add more agents to the ecosystem
5. Tune temperature + max_tokens in `task_processor.py`
6. Add custom repartee prompts per agent type

---

**Status:** MIGRATION COMPLETE  
**YentahSwarm:** Disabled (no external agents)  
**Rep Partay:** Ready to ignite  
**VENIM.US.**

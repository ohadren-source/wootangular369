# MIGRATION_GUIDE.md — AutoGen → MAF

## What Changed

### Phase 1 (complete)
- `core/skills.py` — 7 tools as plain MAF functions
- `core/middleware.py` — GI;WG? as MAF middleware
- `core/maf_bootstrap.py` — Sol as MAF Agent with AnthropicClient + A2A

### Phase 2 (complete)
- `core/workflows.py` — YENTAH swarm as MAF workflow graph

### Phase 3 (complete)
- `core/agents.yaml` — Sol declarative definition
- `lilypod/maf.py` — LILYPOD public API over MAF engine

---

## What Did NOT Change

These files are untouched. Do not modify them.

| File | Role |
|------|------|
| `core/solar8.py` | Sol's brain — unchanged |
| `core/filter.py` | GI;WG? logic — unchanged |
| `core/fusion_core.py` | NULL_Φ engine — unchanged |
| `core/blades.py` | Blade 0 + Blade 1 — unchanged |
| `core/tcp_up.py` | TCP/UP protocol — unchanged |
| `core/mcp_server.py` | External MCP surface — unchanged |
| `api/server.py` | Flask HTTP surface — one line changed |
| `db/` | All tables — unchanged |

---

## server.py Change (one line)

```python
# BEFORE
solar8 = Solar8()

# AFTER
from core.maf_bootstrap import boot_maf
sol_agent, solar8, a2a_app = boot_maf()
```

## YENTAH Thread Change

```python
# BEFORE
from core.yentah_swarm import YentahSwarm
yentah = YentahSwarm()
threading.Thread(target=yentah.orchestrate, daemon=True).start()

# AFTER
from lilypod.maf import start_swarm
threading.Thread(target=start_swarm, daemon=True).start()
```

---

## Requirements Delta

```
agent-framework
agent-framework-anthropic
agent-framework-a2a
```

---

## Architecture Layer Stack

```
JRAGON (user-facing API + BOOT.md doctrine)
    ↓
LILYPOD (dev framework — lilypod/maf.py wraps MAF)
    ↓
MAF Primitives (Agent, workflows, skills, middleware, A2A)
    ↓
AnthropicClient → Claude Haiku 4.5
    ↓
PostgreSQL (Railway) + SQLite (memory log)
```

---

*VENIM.US · VIDEM.US · VINCIM.US*

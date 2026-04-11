"""
db/memory_log.py
Sol Calarbone 8 persistent memory log.
Turso (libsql) when env vars present, local SQLite fallback for dev.
Append-only. Sol Calarbone 8 never forgets.
"""

import os
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory_log.db")

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS solar8_memory_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  exchange_count INTEGER NOT NULL,
  summary TEXT NOT NULL,
  key_decisions TEXT,
  swarm_state TEXT,
  flags TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


def _get_conn():
    """Return (connection, backend_name). Tries Turso first, falls back to SQLite."""
    url = os.getenv("TURSO_DATABASE_URL", "").strip()
    token = os.getenv("TURSO_AUTH_TOKEN", "").strip()
    if url and token:
        try:
            import libsql_experimental as libsql  # type: ignore
            conn = libsql.connect(url, auth_token=token)
            return conn, "turso"
        except ImportError:
            logger.warning("libsql_experimental not installed — falling back to local SQLite for memory log.")
        except Exception as exc:
            logger.warning("Turso connect failed (%s) — falling back to local SQLite.", exc)
    import sqlite3
    conn = sqlite3.connect(_DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn, "sqlite"


def _rows_to_dicts(cursor, rows):
    """Convert cursor rows to list of plain dicts regardless of backend."""
    if not rows:
        return []
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in rows]


def init_memory_db():
    """Create the solar8_memory_log table if it doesn't exist."""
    try:
        conn, backend = _get_conn()
        cur = conn.cursor()
        cur.execute(_CREATE_TABLE_SQL)
        conn.commit()
        conn.close()
        logger.info("Memory log DB initialised (%s).", backend)
    except Exception as exc:
        logger.error("init_memory_db failed: %s", exc)


def append_memory_log(
    session_id: str,
    exchange_count: int,
    summary: str,
    key_decisions: list | None = None,
    swarm_state: dict | None = None,
    flags: list | None = None,
) -> int | None:
    """Insert a new memory log entry. Returns the new row id or None on error."""
    if key_decisions is None:
        key_decisions = []
    if swarm_state is None:
        swarm_state = {}
    if flags is None:
        flags = []
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn, _ = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO solar8_memory_log
              (session_id, timestamp, exchange_count, summary, key_decisions, swarm_state, flags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                timestamp,
                exchange_count,
                summary,
                json.dumps(key_decisions),
                json.dumps(swarm_state),
                json.dumps(flags),
            ),
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        logger.info("Memory log entry appended (session=%s, exchanges=%d).", session_id, exchange_count)
        return row_id
    except Exception as exc:
        logger.error("append_memory_log failed: %s", exc)
        return None


def get_recent_log(limit: int = 5) -> list[dict]:
    """Return the last `limit` log entries, most recent first."""
    try:
        conn, _ = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM solar8_memory_log ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        result = _rows_to_dicts(cur, rows)
        conn.close()
        return result
    except Exception as exc:
        logger.error("get_recent_log failed: %s", exc)
        return []


def get_full_log(limit: int = 50) -> list[dict]:
    """Return the last `limit` log entries (default 50), most recent first."""
    return get_recent_log(limit=limit)


def format_log_for_context(entries: list) -> str:
    """Format memory log entries into a clean string for injection into system prompt."""
    if not entries:
        return "(no memory log entries yet)"
    lines = ["=== SOL CALARBONE 8 MEMORY LOG ==="]
    for entry in entries:
        ts = entry.get("timestamp", "")
        sid = entry.get("session_id", "")[:8]
        exc = entry.get("exchange_count", "?")
        summary = entry.get("summary", "")
        raw_decisions = entry.get("key_decisions") or "[]"
        raw_flags = entry.get("flags") or "[]"
        try:
            decisions = json.loads(raw_decisions) if isinstance(raw_decisions, str) else raw_decisions
        except Exception:
            decisions = []
        try:
            flags_list = json.loads(raw_flags) if isinstance(raw_flags, str) else raw_flags
        except Exception:
            flags_list = []
        lines.append(f"[{ts}] Session {sid} | Exchange {exc}")
        lines.append(f"SUMMARY: {summary}")
        if decisions:
            lines.append(f"KEY DECISIONS: {json.dumps(decisions)}")
        if flags_list:
            lines.append(f"FLAGS: {json.dumps(flags_list)}")
        lines.append("---")
    return "\n".join(lines)

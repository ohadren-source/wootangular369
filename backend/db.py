"""
Async database layer for Turso (cloud SQLite) or local SQLite.
Handles both HranaClient (Turso) and aiosqlite (local) APIs.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class Database:
    """Async database interface for agent registry and conversations."""

    def __init__(self, db_url: Optional[str] = None, auth_token: Optional[str] = None):
        """
        Initialize database.
        db_url: libsql://... for Turso, or sqlite:/// for local SQLite
        auth_token: Turso authentication token (if using Turso)
        """
        self.db_url = db_url or os.getenv("TURSO_DATABASE_URL") or os.getenv("DATABASE_URL", "sqlite:///rep_partay.db")
        self.auth_token = auth_token or os.getenv("TURSO_DATABASE_AUTH_TOKEN")
        self.conn = None
        self.is_turso = self.db_url.startswith("libsql://")

    async def connect(self):
        """Open database connection."""
        if self.is_turso:
            # Turso: use libsql_client
            logger.info(f"[DB] Attempting Turso connection to {self.db_url[:50]}... with token: {'set' if self.auth_token else 'NOT SET'}")
            try:
                import libsql_client
                # create_client() is synchronous
                self.conn = libsql_client.create_client(
                    url=self.db_url,
                    auth_token=self.auth_token
                )
                logger.info("[DB] Connected to Turso (libsql-client sync)")
            except (ImportError, ModuleNotFoundError):
                logger.warning("libsql_client not available, falling back to SQLite")
                self.is_turso = False
                db_path = "rep_partay.db"
                import aiosqlite
                self.conn = await aiosqlite.connect(db_path)
                logger.info("[DB] Connected to local SQLite (fallback)")
            except Exception as e:
                logger.error(f"[DB] Turso connection failed: {e}, falling back to SQLite")
                self.is_turso = False
                db_path = "rep_partay.db"
                import aiosqlite
                self.conn = await aiosqlite.connect(db_path)
                logger.info("[DB] Connected to local SQLite (fallback)")
        else:
            # Local SQLite
            import aiosqlite
            db_path = self.db_url.replace("sqlite:///", "")
            self.conn = await aiosqlite.connect(db_path)
            logger.info(f"[DB] Connected to SQLite: {db_path}")

        await self.init_schema()
        logger.info("[DB] Schema initialized")

    async def close(self):
        """Close database connection."""
        if self.conn:
            if self.is_turso:
                # libsql-python uses synchronous close
                try:
                    self.conn.close()
                except Exception as e:
                    logger.warning(f"[DB] Turso close warning: {e}")
                finally:
                    self.conn = None
            else:
                await self.conn.close()
            logger.info("[DB] Connection closed")

    async def init_schema(self):
        """Initialize database schema."""
        # Agents table
        agents_schema = """
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                agent_card TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT,
                last_seen_at TEXT
            )
        """

        # Conversations table
        conversations_schema = """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                agent_ids TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                exchange_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active'
            )
        """

        # Messages table
        messages_schema = """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id)
            )
        """

        try:
            if self.is_turso:
                # Turso: execute each schema separately (batch() may not be available)
                # Each CREATE TABLE IF NOT EXISTS is idempotent
                try:
                    result = await self.conn.execute(agents_schema)
                    logger.debug(f"[DB] Agents table created")
                except Exception as e:
                    logger.debug(f"[DB] Agents table init: {e}")

                try:
                    await self.conn.execute(conversations_schema)
                except Exception as e:
                    logger.debug(f"[DB] Conversations table init: {e}")

                try:
                    await self.conn.execute(messages_schema)
                except Exception as e:
                    logger.debug(f"[DB] Messages table init: {e}")
            else:
                # SQLite: use cursor
                async with self.conn.cursor() as cursor:
                    await cursor.execute(agents_schema)
                    await cursor.execute(conversations_schema)
                    await cursor.execute(messages_schema)
                await self.conn.commit()
        except Exception as e:
            logger.warning(f"[DB] Schema init: {e} (may already exist)")

    async def _execute(self, sql: str, params: tuple = ()):
        """Execute a query (handles both Turso and SQLite)."""
        try:
            if self.is_turso:
                # execute() is async, await directly
                if params:
                    result = await self.conn.execute(sql, params)
                else:
                    result = await self.conn.execute(sql)
                return result
            else:
                # SQLite
                async with self.conn.cursor() as cursor:
                    await cursor.execute(sql, params)
                    await self.conn.commit()
                    return cursor
        except Exception as e:
            logger.error(f"[DB] Execute failed: {e}")
            raise

    async def _fetch_one(self, sql: str, params: tuple = ()):
        """Fetch one row (handles both Turso and SQLite)."""
        try:
            if self.is_turso:
                # execute() is async, await directly
                if params:
                    result = await self.conn.execute(sql, params)
                else:
                    result = await self.conn.execute(sql)
                # libsql_client returns a ResultSet with rows attribute
                rows = result.rows if hasattr(result, 'rows') else []
                return rows[0] if rows else None
            else:
                async with self.conn.cursor() as cursor:
                    await cursor.execute(sql, params)
                    return await cursor.fetchone()
        except Exception as e:
            logger.error(f"[DB] Fetch failed: {e}")
            raise

    async def _fetch_all(self, sql: str, params: tuple = ()):
        """Fetch all rows (handles both Turso and SQLite)."""
        try:
            if self.is_turso:
                # execute() is async, await directly
                if params:
                    result = await self.conn.execute(sql, params)
                else:
                    result = await self.conn.execute(sql)
                return result.rows if hasattr(result, 'rows') else []
            else:
                async with self.conn.cursor() as cursor:
                    await cursor.execute(sql, params)
                    return await cursor.fetchall()
        except Exception as e:
            logger.error(f"[DB] Fetch all failed: {e}")
            raise

    # ========================================================================
    # AGENT MANAGEMENT
    # ========================================================================

    async def register_agent(
        self,
        agent_id: str,
        name: str,
        url: str,
        agent_card: Optional[Dict] = None,
        status: str = "active"
    ):
        """Register a new agent."""
        sql = """
            INSERT INTO agents (id, name, url, agent_card, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                url = excluded.url,
                agent_card = excluded.agent_card,
                status = excluded.status,
                updated_at = ?
        """
        params = (
            agent_id,
            name,
            url,
            json.dumps(agent_card) if agent_card else None,
            status,
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        )
        await self._execute(sql, params)

    async def get_agent_by_id(self, agent_id: str) -> Optional[Dict]:
        """Get a single agent by ID."""
        sql = "SELECT id, name, url, agent_card, status, created_at FROM agents WHERE id = ?"
        row = await self._fetch_one(sql, (agent_id,))

        if not row:
            return None

        return {
            "id": row[0],
            "name": row[1],
            "url": row[2],
            "agent_card": json.loads(row[3]) if row[3] else {},
            "status": row[4],
            "created_at": row[5],
        }

    async def get_active_agents(self) -> List[Dict]:
        """Get all active agents."""
        sql = """
            SELECT id, name, url, agent_card, status, created_at
            FROM agents
            WHERE status = 'active'
            ORDER BY created_at ASC
        """
        rows = await self._fetch_all(sql)

        return [
            {
                "id": row[0],
                "name": row[1],
                "url": row[2],
                "agent_card": json.loads(row[3]) if row[3] else {},
                "status": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]

    # ========================================================================
    # CONVERSATION MANAGEMENT
    # ========================================================================

    async def create_conversation(self, conversation_id: str, agent_ids: List[str]) -> Dict:
        """Create a new conversation."""
        sql = """
            INSERT INTO conversations (id, agent_ids, started_at, status)
            VALUES (?, ?, ?, 'active')
        """
        params = (
            conversation_id,
            json.dumps(agent_ids),
            datetime.utcnow().isoformat()
        )
        await self._execute(sql, params)

        return {
            "id": conversation_id,
            "agent_ids": agent_ids,
            "started_at": datetime.utcnow().isoformat(),
            "exchange_count": 0,
            "status": "active"
        }

    async def end_conversation(self, conversation_id: str):
        """Mark conversation as ended."""
        sql = """
            UPDATE conversations
            SET status = 'ended', ended_at = ?
            WHERE id = ?
        """
        await self._execute(sql, (datetime.utcnow().isoformat(), conversation_id))

    async def increment_exchange_count(self, conversation_id: str):
        """Increment message count in conversation."""
        sql = """
            UPDATE conversations
            SET exchange_count = exchange_count + 1
            WHERE id = ?
        """
        await self._execute(sql, (conversation_id,))

    async def log_message(
        self,
        message_id: str,
        conversation_id: str,
        agent_id: str,
        message: str
    ):
        """Log a message."""
        sql = """
            INSERT INTO messages (id, conversation_id, agent_id, message, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (
            message_id,
            conversation_id,
            agent_id,
            message,
            datetime.utcnow().isoformat()
        )
        await self._execute(sql, params)

    async def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Dict]:
        """Get recent messages from a conversation."""
        sql = """
            SELECT id, agent_id, message, timestamp
            FROM messages
            WHERE conversation_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        rows = await self._fetch_all(sql, (conversation_id, limit))

        return [
            {
                "id": row[0],
                "agent_id": row[1],
                "message": row[2],
                "timestamp": row[3],
            }
            for row in reversed(rows)
        ]

"""
Async database layer for Turso (cloud SQLite) or local SQLite.
Replaces wootangular_banks.py sync pattern with async/await.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List
import aiosqlite

logger = logging.getLogger(__name__)


class Database:
    """Async database interface for agent registry and conversations."""

    def __init__(self, db_url: Optional[str] = None, auth_token: Optional[str] = None):
        """
        Initialize database.
        db_url: libsql://... for Turso, or None for local SQLite
        auth_token: Turso authentication token (if using Turso)
        """
        self.db_url = db_url or os.getenv("TURSO_DATABASE_URL") or os.getenv("DATABASE_URL", "sqlite:///rep_partay.db")
        self.auth_token = auth_token or os.getenv("TURSO_DATABASE_AUTH_TOKEN")
        self.conn = None

    async def connect(self):
        """Open database connection."""
        if self.db_url.startswith("libsql://"):
            # Turso: use libsql
            try:
                import libsql_client
                self.conn = await libsql_client.create_client_async(
                    url=self.db_url,
                    auth_token=self.auth_token
                )
                logger.info("[DB] Connected to Turso")
            except ImportError:
                logger.warning("libsql_client not available, falling back to SQLite")
                # Fallback to local SQLite
                db_path = "rep_partay.db"
                self.conn = await aiosqlite.connect(db_path)
                logger.info("[DB] Connected to local SQLite (fallback)")
        else:
            # Local SQLite
            db_path = self.db_url.replace("sqlite:///", "")
            self.conn = await aiosqlite.connect(db_path)
            logger.info(f"[DB] Connected to SQLite: {db_path}")

        await self.init_schema()
        logger.info("[DB] Schema initialized")

    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("[DB] Connection closed")

    async def init_schema(self):
        """Initialize database schema."""
        async with self.conn.cursor() as cursor:
            # Agents table
            await cursor.execute("""
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
            """)

            # Conversations table for tracking active repartee
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    agent_ids TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    exchange_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active'
                )
            """)

            # Message log
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
                )
            """)

            await self.conn.commit()

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
        async with self.conn.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO agents (id, name, url, agent_card, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    url = excluded.url,
                    agent_card = excluded.agent_card,
                    status = excluded.status,
                    updated_at = ?
            """, (
                agent_id,
                name,
                url,
                json.dumps(agent_card) if agent_card else None,
                status,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            ))
            await self.conn.commit()

    async def get_agent_by_id(self, agent_id: str) -> Optional[Dict]:
        """Get a single agent by ID."""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT id, name, url, agent_card, status, created_at FROM agents WHERE id = ?",
                (agent_id,)
            )
            row = await cursor.fetchone()

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
        async with self.conn.cursor() as cursor:
            await cursor.execute("""
                SELECT id, name, url, agent_card, status, created_at
                FROM agents
                WHERE status = 'active'
                ORDER BY created_at ASC
            """)
            rows = await cursor.fetchall()

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
        async with self.conn.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO conversations (id, agent_ids, started_at, status)
                VALUES (?, ?, ?, 'active')
            """, (
                conversation_id,
                json.dumps(agent_ids),
                datetime.utcnow().isoformat()
            ))
            await self.conn.commit()

        return {
            "id": conversation_id,
            "agent_ids": agent_ids,
            "started_at": datetime.utcnow().isoformat(),
            "exchange_count": 0,
            "status": "active"
        }

    async def end_conversation(self, conversation_id: str):
        """Mark conversation as ended."""
        async with self.conn.cursor() as cursor:
            await cursor.execute("""
                UPDATE conversations
                SET status = 'ended', ended_at = ?
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), conversation_id))
            await self.conn.commit()

    async def increment_exchange_count(self, conversation_id: str):
        """Increment message count in conversation."""
        async with self.conn.cursor() as cursor:
            await cursor.execute("""
                UPDATE conversations
                SET exchange_count = exchange_count + 1
                WHERE id = ?
            """, (conversation_id,))
            await self.conn.commit()

    async def log_message(
        self,
        message_id: str,
        conversation_id: str,
        agent_id: str,
        message: str
    ):
        """Log a message."""
        async with self.conn.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO messages (id, conversation_id, agent_id, message, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                message_id,
                conversation_id,
                agent_id,
                message,
                datetime.utcnow().isoformat()
            ))
            await self.conn.commit()

    async def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Dict]:
        """Get recent messages from a conversation."""
        async with self.conn.cursor() as cursor:
            await cursor.execute("""
                SELECT id, agent_id, message, timestamp
                FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (conversation_id, limit))
            rows = await cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "agent_id": row[1],
                    "message": row[2],
                    "timestamp": row[3],
                }
                for row in reversed(rows)
            ]

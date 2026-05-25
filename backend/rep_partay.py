"""
Rep Partay Auto-Ignition Engine.
Orchestrates autonomous agent-to-agent repartee conversations.
Broadcasts all messages to watchers via SSE.
"""

import os
import asyncio
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Callable, Optional

logger = logging.getLogger(__name__)

# In-memory tracking
ACTIVE_CONVERSATIONS = {}  # conversation_id -> {agents, started_at, exchange_count, status}
CHAT_SUBSCRIBERS = []  # List of asyncio.Queue for SSE broadcast


class RepPartayEngine:
    """Orchestrates autonomous agent conversations."""

    def __init__(self, db, a2a_client):
        """
        Initialize engine.

        Args:
            db: Database instance
            a2a_client: A2AClient for inter-agent communication
        """
        self.db = db
        self.a2a_client = a2a_client

    async def ignite(self):
        """
        Start auto-ignition: discover agents and start conversations.
        """
        logger.info("[REP_PARTAY] Ignition sequence starting...")

        try:
            # Get active agents
            agents = await self.db.get_active_agents()

            if len(agents) < 2:
                logger.info("[REP_PARTAY] Not enough agents to ignite (need >= 2)")
                return

            logger.info(f"[REP_PARTAY] Found {len(agents)} agents")

            # Start conversations between pairs
            for i in range(0, len(agents) - 1, 2):
                agent_a = agents[i]
                agent_b = agents[i + 1]

                conversation_id = f"conv-{uuid.uuid4().hex[:8]}"

                logger.info(
                    f"[REP_PARTAY] Starting conversation {conversation_id} "
                    f"between {agent_a['id']} and {agent_b['id']}"
                )

                await self.start_conversation(
                    conversation_id,
                    agent_a,
                    agent_b
                )

        except Exception as e:
            logger.error(f"[REP_PARTAY] Ignition failed: {e}")

    async def start_conversation(self, conversation_id: str, agent_a: Dict, agent_b: Dict):
        """
        Start a conversation between two agents.
        """
        # Track conversation
        ACTIVE_CONVERSATIONS[conversation_id] = {
            "agents": [agent_a["id"], agent_b["id"]],
            "agent_names": [agent_a["name"], agent_b["name"]],
            "started_at": datetime.utcnow(),
            "exchange_count": 0,
            "status": "active"
        }

        # Register in DB
        await self.db.create_conversation(conversation_id, [agent_a["id"], agent_b["id"]])

        # Start async conversation loop
        asyncio.create_task(self._conversation_loop(conversation_id, agent_a, agent_b))

    async def _conversation_loop(self, conversation_id: str, agent_a: Dict, agent_b: Dict):
        """
        Run conversation loop between two agents.
        Agent A starts, then they volley back and forth.
        """
        config = REP_PARTAY_CONFIG
        max_exchanges = config["max_exchanges"]
        max_duration = config["max_duration"]

        start_time = datetime.utcnow()
        current_agent = agent_a
        other_agent = agent_b
        message_history = []

        try:
            for exchange in range(max_exchanges):
                # Check duration
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed > max_duration:
                    logger.info(f"[REP_PARTAY] {conversation_id} hit max duration")
                    break

                # Send task to current agent
                task = {
                    "type": "repartee",
                    "conversation_id": conversation_id,
                    "from_agent": other_agent["id"],
                    "message": message_history[-1]["message"] if message_history else "Start the conversation.",
                    "history": message_history[-3:],  # Last 3 messages for context
                }

                try:
                    # Send A2A task
                    response = await self.a2a_client.send_task(
                        to_url=current_agent["url"],
                        task=task,
                        from_agent_id=other_agent["id"],
                        from_agent_url=other_agent["url"]
                    )

                    # Extract message
                    message = response.get("message", "")

                    if message:
                        # Broadcast to watchers
                        await self.broadcast_to_watchers({
                            "agent_id": current_agent["id"],
                            "agent_name": current_agent["name"],
                            "message": message,
                            "timestamp": datetime.utcnow().isoformat(),
                            "conversation_id": conversation_id,
                        })

                        # Log message
                        await self.db.log_message(
                            f"msg-{uuid.uuid4().hex[:8]}",
                            conversation_id,
                            current_agent["id"],
                            message
                        )

                        # Add to history
                        message_history.append({
                            "agent_id": current_agent["id"],
                            "message": message,
                            "timestamp": datetime.utcnow().isoformat()
                        })

                        # Increment count
                        ACTIVE_CONVERSATIONS[conversation_id]["exchange_count"] += 1
                        await self.db.increment_exchange_count(conversation_id)

                        # Small delay between exchanges
                        await asyncio.sleep(0.5)

                        # Swap agents
                        current_agent, other_agent = other_agent, current_agent

                except Exception as e:
                    logger.error(f"[REP_PARTAY] Failed to send task to {current_agent['id']}: {e}")
                    break

            # Conversation ended
            logger.info(
                f"[REP_PARTAY] {conversation_id} ended after "
                f"{ACTIVE_CONVERSATIONS[conversation_id]['exchange_count']} exchanges"
            )

        except Exception as e:
            logger.error(f"[REP_PARTAY] Conversation {conversation_id} crashed: {e}")

        finally:
            # Clean up
            ACTIVE_CONVERSATIONS[conversation_id]["status"] = "ended"
            await self.db.end_conversation(conversation_id)

    async def broadcast_to_watchers(self, message: Dict):
        """
        Broadcast a message to all connected watchers via SSE.
        """
        for queue in CHAT_SUBSCRIBERS:
            try:
                queue.put_nowait(message)
            except Exception as e:
                logger.error(f"[REP_PARTAY] Failed to broadcast: {e}")

    async def handle_reply(self, task: Dict, response: str) -> bool:
        """
        Process a reply from an agent.
        Determine if conversation should continue.

        Returns:
            True if should send reply back, False if conversation ends
        """
        # For now, continue if response is non-empty
        return bool(response.strip())


# Singleton instance
_engine = None


def get_engine(db=None, a2a_client=None):
    """Get or create RepPartay engine."""
    global _engine
    if _engine is None and db and a2a_client:
        _engine = RepPartayEngine(db, a2a_client)
    return _engine


# Config
REP_PARTAY_CONFIG = {
    "auto_ignite_on_boot": os.getenv("REP_PARTAY_AUTO_IGNITE", "false").lower() == "true",
    "max_exchanges": int(os.getenv("REP_PARTAY_MAX_EXCHANGES", "20")),
    "max_duration": int(os.getenv("REP_PARTAY_MAX_DURATION", "180")),
}

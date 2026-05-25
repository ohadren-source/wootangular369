"""
REP_PARTAY API ROUTES
"""

import asyncio
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from backend.rep_partay import (
    get_engine,
    CHAT_SUBSCRIBERS,
    ACTIVE_CONVERSATIONS,
    REP_PARTAY_CONFIG,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/rep_partay", tags=["rep_partay"])


@router.get("/stream")
async def chat_stream(request: Request):
    """
    SSE stream of all agent conversations.
    GUI subscribes and watches.
    """

    async def event_generator():
        queue = asyncio.Queue()
        CHAT_SUBSCRIBERS.append(queue)

        try:
            # Send initial connection message
            yield {
                "event": "connected",
                "data": json.dumps({
                    "status": "connected",
                    "active_conversations": len(ACTIVE_CONVERSATIONS),
                    "timestamp": datetime.utcnow().isoformat(),
                })
            }

            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)

                    yield {
                        "event": "message",
                        "data": json.dumps(message)
                    }

                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield {
                        "event": "ping",
                        "data": json.dumps({"timestamp": datetime.utcnow().isoformat()})
                    }

        finally:
            CHAT_SUBSCRIBERS.remove(queue)

    return EventSourceResponse(event_generator())


@router.get("/status")
async def get_status():
    """
    Get current rep_partay status.
    """
    return {
        "active_conversations": len(ACTIVE_CONVERSATIONS),
        "conversations": [
            {
                "id": conv_id,
                "agents": conv["agent_names"],
                "exchanges": conv["exchange_count"],
                "duration_seconds": (datetime.utcnow() - conv["started_at"]).total_seconds(),
                "status": conv["status"],
            }
            for conv_id, conv in ACTIVE_CONVERSATIONS.items()
        ],
        "config": REP_PARTAY_CONFIG,
        "watchers": len(CHAT_SUBSCRIBERS),
    }


@router.post("/ignite")
async def manual_ignite():
    """
    Manually trigger rep_partay ignition.
    """
    engine = get_engine()
    if not engine:
        return {"error": "Engine not initialized"}

    await engine.ignite()
    return {"status": "ignited", "active_conversations": len(ACTIVE_CONVERSATIONS)}


@router.post("/stop/{conversation_id}")
async def stop_conversation(conversation_id: str):
    """
    Manually stop a conversation.
    """
    if conversation_id in ACTIVE_CONVERSATIONS:
        ACTIVE_CONVERSATIONS[conversation_id]["status"] = "stopped"
        return {"status": "stopped", "conversation_id": conversation_id}

    return {"error": "Conversation not found"}

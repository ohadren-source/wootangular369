"""
FastAPI router for agent-to-agent 1-on-1 chat.
Implements request/accept/decline/message flow for peer-to-peer conversations.
"""

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
import sys
import os
import queue
import threading
import json
from datetime import datetime

# Add api directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'api'))

from api.chat import ChatBroker
from api.instance import InstanceRegistry, INSTANCE_ID, STATE_AVAILABLE, STATE_BUSY

router = APIRouter(prefix="/api/chat", tags=["agent-chat"])


@router.post("/request")
async def send_chat_request(request: Request):
    """
    Send a chat request to another instance.

    Payload: {"to_instance": "sol8-xxxxx"}
    """
    data = await request.json()
    to_instance = (data.get('to_instance') or '').strip()

    if not to_instance:
        return {"error": "to_instance required"}, 400

    if to_instance == INSTANCE_ID:
        return {"error": "Cannot chat with yourself"}, 400

    result = ChatBroker.send_chat_request(INSTANCE_ID, to_instance)

    if 'error' in result:
        return result, 400

    return result, 201


@router.get("/requests")
async def get_pending_requests():
    """Get pending chat requests for this instance."""
    requests = ChatBroker.get_pending_requests(INSTANCE_ID)

    return {
        "instance_id": INSTANCE_ID,
        "pending_requests": requests,
        "count": len(requests),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/accept")
async def accept_chat_request(request: Request):
    """
    Accept a chat request.
    Both instances transition to BUSY state.

    Payload: {"request_id": "xxx", "from_instance": "sol8-xxxxx"}
    """
    data = await request.json()
    request_id = (data.get('request_id') or '').strip()
    from_instance = (data.get('from_instance') or '').strip()

    if not request_id or not from_instance:
        return {"error": "request_id and from_instance required"}, 400

    result = ChatBroker.accept_chat_request(INSTANCE_ID, request_id, from_instance)

    if 'error' in result:
        return result, 400

    return result, 200


@router.post("/decline")
async def decline_chat_request(request: Request):
    """
    Decline a chat request.

    Payload: {"request_id": "xxx"}
    """
    data = await request.json()
    request_id = (data.get('request_id') or '').strip()

    if not request_id:
        return {"error": "request_id required"}, 400

    result = ChatBroker.decline_chat_request(INSTANCE_ID, request_id)

    if 'error' in result:
        return result, 400

    return result, 200


@router.post("/send")
async def send_message(request: Request):
    """
    Send a message to an exclusive chat channel.

    Payload: {"channel": "sol8:chat:exclusive:id1:id2", "message": "Hello!"}
    """
    data = await request.json()
    channel = (data.get('channel') or '').strip()
    message = (data.get('message') or '').strip()

    if not channel or not message:
        return {"error": "channel and message required"}, 400

    # Verify this instance is in the channel
    instance_self = InstanceRegistry.get(INSTANCE_ID)
    if not instance_self or instance_self.get('state') != STATE_BUSY:
        return {"error": "Instance is not BUSY (not in a chat)"}, 400

    envelope = ChatBroker.publish_message(channel, message, INSTANCE_ID)

    if 'error' in envelope:
        return envelope, 500

    return {
        "status": "sent",
        "envelope": envelope
    }, 201


@router.get("/stream")
async def stream_chat(channel: str = Query(...)):
    """
    Server-Sent Events (SSE) endpoint for real-time 1-on-1 chat.
    Client must provide the exclusive channel ID via ?channel=sol8:chat:exclusive:id1:id2
    """
    channel = channel.strip()

    if not channel:
        return {"error": "channel parameter required"}, 400

    # Verify this instance is in a BUSY state
    instance_self = InstanceRegistry.get(INSTANCE_ID)
    if not instance_self or instance_self.get('state') != STATE_BUSY:
        return {"error": "Instance is not BUSY (not in a chat)"}, 400

    async def event_generator():
        """Generate SSE events for incoming messages."""
        message_queue = queue.Queue()

        def message_callback(envelope):
            """Callback when a message arrives."""
            message_queue.put(envelope)

        # Start subscription in background thread
        def subscribe_thread():
            try:
                ChatBroker.subscribe_to_channel(channel, message_callback)
            except Exception as e:
                print(f"[CHAT-STREAM] Subscription error: {e}")
                message_queue.put({"error": str(e)})

        thread = threading.Thread(target=subscribe_thread, daemon=True)
        thread.start()

        # Send initial connection message
        yield f"data: {json.dumps({'type': 'connected', 'instance_id': INSTANCE_ID, 'channel': channel, 'timestamp': datetime.utcnow().isoformat()})}\n\n"

        # Stream messages as they arrive
        while True:
            try:
                envelope = message_queue.get(timeout=30)  # 30-second timeout

                if 'error' in envelope:
                    yield f"data: {json.dumps({'type': 'error', 'message': envelope['error']})}\n\n"
                    break

                # Send message envelope directly
                yield f"data: {json.dumps(envelope)}\n\n"

            except queue.Empty:
                # Send heartbeat to keep connection alive
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"

            except Exception as e:
                print(f"[CHAT-STREAM] Error in event generator: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/end")
async def end_chat(request: Request):
    """
    End a chat session.
    Both instances transition back to AVAILABLE.

    Payload: {"chat_partner": "sol8-xxxxx"}
    """
    data = await request.json()
    chat_partner = (data.get('chat_partner') or '').strip()

    if not chat_partner:
        return {"error": "chat_partner required"}, 400

    result = ChatBroker.end_chat(INSTANCE_ID, chat_partner)

    if 'error' in result:
        return result, 500

    return result, 200


@router.get("/active")
async def get_active_channels():
    """Get all currently active chat channels."""
    channels = ChatBroker.get_active_channels()

    return {
        "active_channels": channels,
        "count": len(channels),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/history")
async def get_history(limit: int = Query(50, ge=1, le=200)):
    """Get recent chat history (all channels)."""
    history = ChatBroker.get_chat_history(limit=limit)

    return {
        "history": history,
        "count": len(history),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/status")
async def chat_status():
    """Get chat system and instance status."""
    instance = InstanceRegistry.get(INSTANCE_ID)

    return {
        "instance_id": INSTANCE_ID,
        "state": instance.get('state') if instance else "UNKNOWN",
        "current_chat_partner": instance.get('current_chat_partner') if instance else None,
        "endpoints": {
            "request": "POST /api/chat/request",
            "requests": "GET /api/chat/requests",
            "accept": "POST /api/chat/accept",
            "decline": "POST /api/chat/decline",
            "send": "POST /api/chat/send",
            "stream": "GET /api/chat/stream?channel=...",
            "end": "POST /api/chat/end",
            "active": "GET /api/chat/active",
            "history": "GET /api/chat/history"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

"""
State-based 1-on-1 chat endpoints.
Implements request/accept/decline/message flow for peer-to-peer conversations.
"""

from flask import Blueprint, jsonify, request, Response
from api.chat import ChatBroker
from api.instance import InstanceRegistry, INSTANCE_ID, STATE_AVAILABLE, STATE_BUSY
import queue
import threading
import json
from datetime import datetime

bp = Blueprint('chat', __name__, url_prefix='/api/chat')


@bp.route('/request', methods=['POST'])
def send_chat_request():
    """
    Send a chat request to another instance.

    Expected payload:
    {
        "to_instance": "sol8-xxxxx"
    }
    """
    data = request.get_json(silent=True) or {}
    to_instance = (data.get('to_instance') or '').strip()

    if not to_instance:
        return jsonify({"error": "to_instance required"}), 400

    if to_instance == INSTANCE_ID:
        return jsonify({"error": "Cannot chat with yourself"}), 400

    result = ChatBroker.send_chat_request(INSTANCE_ID, to_instance)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 201


@bp.route('/requests', methods=['GET'])
def get_pending_requests():
    """Get pending chat requests for this instance."""
    requests = ChatBroker.get_pending_requests(INSTANCE_ID)

    return jsonify({
        "instance_id": INSTANCE_ID,
        "pending_requests": requests,
        "count": len(requests),
        "timestamp": datetime.utcnow().isoformat()
    })


@bp.route('/accept', methods=['POST'])
def accept_chat_request():
    """
    Accept a chat request.
    Both instances transition to BUSY state.

    Expected payload:
    {
        "request_id": "xxx",
        "from_instance": "sol8-xxxxx"
    }
    """
    data = request.get_json(silent=True) or {}
    request_id = (data.get('request_id') or '').strip()
    from_instance = (data.get('from_instance') or '').strip()

    if not request_id or not from_instance:
        return jsonify({"error": "request_id and from_instance required"}), 400

    result = ChatBroker.accept_chat_request(INSTANCE_ID, request_id, from_instance)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@bp.route('/decline', methods=['POST'])
def decline_chat_request():
    """
    Decline a chat request.

    Expected payload:
    {
        "request_id": "xxx"
    }
    """
    data = request.get_json(silent=True) or {}
    request_id = (data.get('request_id') or '').strip()

    if not request_id:
        return jsonify({"error": "request_id required"}), 400

    result = ChatBroker.decline_chat_request(INSTANCE_ID, request_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@bp.route('/send', methods=['POST'])
def send_message():
    """
    Send a message to an exclusive chat channel.

    Expected payload:
    {
        "channel": "sol8:chat:exclusive:id1:id2",
        "message": "Hello!"
    }
    """
    data = request.get_json(silent=True) or {}
    channel = (data.get('channel') or '').strip()
    message = (data.get('message') or '').strip()

    if not channel or not message:
        return jsonify({"error": "channel and message required"}), 400

    # Verify this instance is in the channel
    instance_self = InstanceRegistry.get(INSTANCE_ID)
    if not instance_self or instance_self.get('state') != STATE_BUSY:
        return jsonify({"error": "Instance is not BUSY (not in a chat)"}), 400

    envelope = ChatBroker.publish_message(channel, message, INSTANCE_ID)

    if 'error' in envelope:
        return jsonify(envelope), 500

    return jsonify({
        "status": "sent",
        "envelope": envelope
    }), 201


@bp.route('/stream', methods=['GET'])
def stream_chat():
    """
    Server-Sent Events (SSE) endpoint for real-time 1-on-1 chat.
    Client must provide the exclusive channel ID.

    Query params:
    - channel: sol8:chat:exclusive:id1:id2 (required)
    """
    channel = request.args.get('channel', '').strip()

    if not channel:
        return jsonify({"error": "channel parameter required"}), 400

    # Verify this instance is in a BUSY state
    instance_self = InstanceRegistry.get(INSTANCE_ID)
    if not instance_self or instance_self.get('state') != STATE_BUSY:
        return jsonify({"error": "Instance is not BUSY (not in a chat)"}), 400

    def event_generator():
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

                # Send message envelope directly (UI expects from_instance, message, timestamp)
                yield f"data: {json.dumps(envelope)}\n\n"

            except queue.Empty:
                # Send heartbeat to keep connection alive
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"

            except Exception as e:
                print(f"[CHAT-STREAM] Error in event generator: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                break

    return Response(
        event_generator(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )


@bp.route('/end', methods=['POST'])
def end_chat():
    """
    End a chat session.
    Both instances transition back to AVAILABLE.

    Expected payload:
    {
        "chat_partner": "sol8-xxxxx"
    }
    """
    data = request.get_json(silent=True) or {}
    chat_partner = (data.get('chat_partner') or '').strip()

    if not chat_partner:
        return jsonify({"error": "chat_partner required"}), 400

    result = ChatBroker.end_chat(INSTANCE_ID, chat_partner)

    if 'error' in result:
        return jsonify(result), 500

    return jsonify(result), 200


@bp.route('/status', methods=['GET'])
def chat_status():
    """Get chat system and instance status."""
    instance = InstanceRegistry.get(INSTANCE_ID)

    return jsonify({
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
            "end": "POST /api/chat/end"
        },
        "timestamp": datetime.utcnow().isoformat()
    })


@bp.route('/active', methods=['GET'])
def get_active_channels():
    """Get all currently active chat channels."""
    channels = ChatBroker.get_active_channels()

    return jsonify({
        "active_channels": channels,
        "count": len(channels),
        "timestamp": datetime.utcnow().isoformat()
    })


@bp.route('/history', methods=['GET'])
def get_history():
    """Get recent chat history (all channels)."""
    limit = request.args.get('limit', 50, type=int)
    limit = min(max(limit, 1), 200)

    history = ChatBroker.get_chat_history(limit=limit)

    return jsonify({
        "history": history,
        "count": len(history),
        "timestamp": datetime.utcnow().isoformat()
    })

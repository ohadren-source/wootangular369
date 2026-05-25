"""
Real-time chat endpoints with SSE streaming for peer-to-peer communication.
Enables live chat between Sol 8 instances with frontend display.
"""

from flask import Blueprint, jsonify, request, Response
from api.chat import ChatBroker
from api.instance import INSTANCE_ID
import queue
import threading
import json
from datetime import datetime

bp = Blueprint('chat', __name__, url_prefix='/api/chat')


@bp.route('/send', methods=['POST'])
def send_message():
    """Send a chat message to another instance or broadcast."""
    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()
    recipient_id = data.get('to_instance')  # Optional target instance

    if not message:
        return jsonify({"error": "message required"}), 400

    envelope = ChatBroker.publish(message, recipient_id=recipient_id)

    if 'error' in envelope:
        return jsonify(envelope), 500

    return jsonify({
        "status": "published",
        "envelope": envelope
    }), 201


@bp.route('/history', methods=['GET'])
def get_history():
    """Get recent chat history."""
    limit = request.args.get('limit', 50, type=int)
    limit = min(max(limit, 1), 200)  # Clamp between 1 and 200

    history = ChatBroker.get_history(limit=limit)

    return jsonify({
        "instance_id": INSTANCE_ID,
        "history": history,
        "count": len(history),
        "timestamp": datetime.utcnow().isoformat()
    })


@bp.route('/stream', methods=['GET'])
def stream_chat():
    """
    Server-Sent Events (SSE) endpoint for real-time chat streaming.
    Clients connect to this endpoint to receive live messages.
    """
    from_instance = request.args.get('from_instance')  # Optional: filter by sender

    def event_generator():
        """Generate SSE events for incoming messages."""
        message_queue = queue.Queue()

        def chat_callback(envelope):
            """Callback when a new message arrives."""
            message_queue.put(envelope)

        # Start subscription in background thread
        def subscribe_thread():
            try:
                ChatBroker.subscribe(chat_callback, instance_filter=from_instance)
            except Exception as e:
                print(f"[CHAT-STREAM] Subscription error: {e}")
                message_queue.put({"error": str(e)})

        thread = threading.Thread(target=subscribe_thread, daemon=True)
        thread.start()

        # Send initial connection message
        yield f"data: {json.dumps({'type': 'connected', 'instance_id': INSTANCE_ID, 'timestamp': datetime.utcnow().isoformat()})}\n\n"

        # Stream messages as they arrive
        while True:
            try:
                envelope = message_queue.get(timeout=30)  # 30-second timeout

                if 'error' in envelope:
                    # Send error and close
                    yield f"data: {json.dumps({'type': 'error', 'message': envelope['error']})}\n\n"
                    break

                # Send message
                yield f"data: {json.dumps({'type': 'message', 'payload': envelope})}\n\n"

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


@bp.route('/status', methods=['GET'])
def chat_status():
    """Get chat system status."""
    return jsonify({
        "instance_id": INSTANCE_ID,
        "channel": "sol8:chat",
        "status": "ready",
        "sse_endpoint": "/api/chat/stream",
        "timestamp": datetime.utcnow().isoformat()
    })

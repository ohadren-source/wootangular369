"""
Real-time chat between Sol 8 instances via Redis pubsub.
Enables peer-to-peer messaging with optional targeting.
"""

import json
import uuid
from datetime import datetime
from api.instance import redis_client, INSTANCE_ID


CHAT_CHANNEL = "sol8:chat"
CHAT_HISTORY_KEY = "sol8:chat:history"


class ChatBroker:
    """Handles inter-instance chat via Redis pubsub."""

    @staticmethod
    def publish(message: str, recipient_id: str = None) -> dict:
        """
        Publish message to chat channel.

        Args:
            message: The message text
            recipient_id: Optional specific recipient instance ID (None = broadcast)

        Returns:
            Message envelope dict with message_id, sender, timestamp, etc.
        """
        if not redis_client:
            return {
                "error": "Redis not available",
                "message": message,
                "instance_id": INSTANCE_ID
            }

        envelope = {
            "message_id": str(uuid.uuid4()),
            "from_instance": INSTANCE_ID,
            "to_instance": recipient_id,  # None = broadcast
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            # Publish to pubsub channel
            redis_client.publish(CHAT_CHANNEL, json.dumps(envelope))

            # Also log to chat history (for persistent retrieval)
            redis_client.lpush(CHAT_HISTORY_KEY, json.dumps(envelope))
            # Keep last 1000 messages
            redis_client.ltrim(CHAT_HISTORY_KEY, 0, 999)

            return envelope

        except Exception as e:
            return {
                "error": str(e),
                "message": message,
                "instance_id": INSTANCE_ID
            }

    @staticmethod
    def get_history(limit: int = 50) -> list:
        """Get recent chat history from Redis."""
        if not redis_client:
            return []

        try:
            history = redis_client.lrange(CHAT_HISTORY_KEY, 0, limit - 1)
            # Reverse to get chronological order
            return [json.loads(msg) for msg in reversed(history)]

        except Exception as e:
            print(f"[CHAT] Failed to retrieve history: {e}")
            return []

    @staticmethod
    def subscribe(callback, instance_filter: str = None):
        """
        Subscribe to chat channel and call callback for each message.
        Blocks indefinitely until unsubscribed.

        Args:
            callback: Function called with each message envelope
            instance_filter: Optional instance ID to filter messages (only those from this sender)
        """
        if not redis_client:
            print("[CHAT] Redis not available, cannot subscribe")
            return

        pubsub = redis_client.pubsub()
        pubsub.subscribe(CHAT_CHANNEL)

        print(f"[CHAT] Instance {INSTANCE_ID} subscribed to {CHAT_CHANNEL}")

        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        envelope = json.loads(message['data'])

                        # Skip own messages (already processed locally)
                        if envelope['from_instance'] == INSTANCE_ID:
                            continue

                        # If message is targeted and not for us, skip
                        if envelope['to_instance'] and envelope['to_instance'] != INSTANCE_ID:
                            continue

                        # If instance filter specified, only process from that sender
                        if instance_filter and envelope['from_instance'] != instance_filter:
                            continue

                        callback(envelope)

                    except json.JSONDecodeError as e:
                        print(f"[CHAT] Failed to decode message: {e}")

        except Exception as e:
            print(f"[CHAT] Subscription error: {e}")

        finally:
            pubsub.unsubscribe()
            print(f"[CHAT] Instance {INSTANCE_ID} unsubscribed from {CHAT_CHANNEL}")

"""
State-based 1-on-1 chat system for Sol 8 instances.
Implements request/response flow and exclusive peer channels.
Instances are AVAILABLE, BUSY (in chat), or OFFLINE.
"""

import json
import uuid
from datetime import datetime
from api.instance import redis_client, INSTANCE_ID, InstanceRegistry
from api.instance import STATE_AVAILABLE, STATE_BUSY


CHAT_REQUEST_QUEUE_PREFIX = "sol8:chat:request"  # sol8:chat:request:{target_id}
CHAT_REQUEST_RESPONSE_PREFIX = "sol8:chat:response"  # sol8:chat:response:{requester_id}
EXCLUSIVE_CHAT_CHANNEL_PREFIX = "sol8:chat:exclusive"  # sol8:chat:exclusive:{id1}:{id2}
CHAT_HISTORY_KEY = "sol8:chat:history"


class ChatBroker:
    """Handles 1-on-1 chat negotiation and messaging."""

    @staticmethod
    def send_chat_request(from_instance: str, to_instance: str) -> dict:
        """
        Send a chat request from one instance to another.

        Args:
            from_instance: Requesting instance ID
            to_instance: Target instance ID

        Returns:
            Result dict with request_id and status
        """
        if not redis_client:
            return {"error": "Redis not available"}

        # Check if target is AVAILABLE
        target = InstanceRegistry.get(to_instance)
        if not target:
            return {"error": f"Instance {to_instance} not found"}

        if target.get("state") != STATE_AVAILABLE:
            return {"error": f"Instance {to_instance} is {target.get('state')}, not AVAILABLE"}

        request_id = str(uuid.uuid4())
        request_data = {
            "request_id": request_id,
            "from_instance": from_instance,
            "to_instance": to_instance,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending"
        }

        try:
            # Queue the request in target's request queue
            queue_key = f"{CHAT_REQUEST_QUEUE_PREFIX}:{to_instance}"
            redis_client.lpush(queue_key, json.dumps(request_data))

            return {
                "status": "sent",
                "request_id": request_id,
                "to_instance": to_instance
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_pending_requests(instance_id: str) -> list:
        """Get pending chat requests for an instance."""
        if not redis_client:
            return []

        try:
            queue_key = f"{CHAT_REQUEST_QUEUE_PREFIX}:{instance_id}"
            requests = redis_client.lrange(queue_key, 0, -1)
            return [json.loads(r) for r in requests]

        except Exception as e:
            print(f"[CHAT] Failed to get requests: {e}")
            return []

    @staticmethod
    def accept_chat_request(instance_id: str, request_id: str, from_instance: str) -> dict:
        """
        Accept a chat request.
        Transitions both instances from AVAILABLE to BUSY.

        Args:
            instance_id: Accepting instance ID
            request_id: Request ID to accept
            from_instance: Requesting instance ID

        Returns:
            Result dict with channel info or error
        """
        if not redis_client:
            return {"error": "Redis not available"}

        # Create exclusive channel for this 1-on-1 chat
        # Channel name: sol8:chat:exclusive:{smaller_id}:{larger_id}
        ids = sorted([instance_id, from_instance])
        channel_key = f"{EXCLUSIVE_CHAT_CHANNEL_PREFIX}:{ids[0]}:{ids[1]}"

        try:
            # Set both instances to BUSY
            InstanceRegistry.set_state(instance_id, STATE_BUSY, from_instance)
            InstanceRegistry.set_state(from_instance, STATE_BUSY, instance_id)

            # Clear the request from queue
            queue_key = f"{CHAT_REQUEST_QUEUE_PREFIX}:{instance_id}"
            redis_client.delete(queue_key)

            return {
                "status": "accepted",
                "request_id": request_id,
                "channel": channel_key,
                "participants": ids,
                "message": f"Chat started between {ids[0]} and {ids[1]}"
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def decline_chat_request(instance_id: str, request_id: str) -> dict:
        """
        Decline a chat request.
        Clears the request from queue. Declining instance stays AVAILABLE.

        Args:
            instance_id: Declining instance ID
            request_id: Request ID to decline

        Returns:
            Result dict
        """
        if not redis_client:
            return {"error": "Redis not available"}

        try:
            # Clear the request from queue
            queue_key = f"{CHAT_REQUEST_QUEUE_PREFIX}:{instance_id}"
            redis_client.delete(queue_key)

            return {
                "status": "declined",
                "request_id": request_id
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def publish_message(channel: str, message: str, from_instance: str) -> dict:
        """
        Publish a message to an exclusive chat channel.

        Args:
            channel: Exclusive channel key (e.g., sol8:chat:exclusive:id1:id2)
            message: Message text
            from_instance: Sending instance ID

        Returns:
            Message envelope dict
        """
        if not redis_client:
            return {"error": "Redis not available"}

        envelope = {
            "message_id": str(uuid.uuid4()),
            "channel": channel,
            "from_instance": from_instance,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            # Publish to exclusive channel
            redis_client.publish(channel, json.dumps(envelope))

            # Log to history
            redis_client.lpush(CHAT_HISTORY_KEY, json.dumps(envelope))
            redis_client.ltrim(CHAT_HISTORY_KEY, 0, 9999)

            return envelope

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def subscribe_to_channel(channel: str, callback):
        """
        Subscribe to an exclusive chat channel.
        Blocks until unsubscribed.

        Args:
            channel: Exclusive channel key
            callback: Function called with each message envelope
        """
        if not redis_client:
            print("[CHAT] Redis not available, cannot subscribe")
            return

        pubsub = redis_client.pubsub()
        pubsub.subscribe(channel)

        print(f"[CHAT] Instance {INSTANCE_ID} subscribed to {channel}")

        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        envelope = json.loads(message['data'])
                        # Skip own messages
                        if envelope['from_instance'] != INSTANCE_ID:
                            callback(envelope)
                    except json.JSONDecodeError as e:
                        print(f"[CHAT] Failed to decode message: {e}")

        except Exception as e:
            print(f"[CHAT] Subscription error: {e}")

        finally:
            pubsub.unsubscribe()
            print(f"[CHAT] Instance {INSTANCE_ID} unsubscribed from {channel}")

    @staticmethod
    def end_chat(instance_id: str, chat_partner: str) -> dict:
        """
        End a chat session.
        Transitions both instances back to AVAILABLE.

        Args:
            instance_id: Instance ending chat
            chat_partner: The other instance in chat

        Returns:
            Result dict
        """
        if not redis_client:
            return {"error": "Redis not available"}

        try:
            # Set both back to AVAILABLE
            InstanceRegistry.set_state(instance_id, STATE_AVAILABLE)
            InstanceRegistry.set_state(chat_partner, STATE_AVAILABLE)

            return {
                "status": "ended",
                "instance_id": instance_id,
                "partner": chat_partner,
                "message": "Chat session ended"
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_chat_history(limit: int = 50) -> list:
        """Get recent chat history."""
        if not redis_client:
            return []

        try:
            history = redis_client.lrange(CHAT_HISTORY_KEY, 0, limit - 1)
            return [json.loads(msg) for msg in reversed(history)]

        except Exception as e:
            print(f"[CHAT] Failed to retrieve history: {e}")
            return []

"""
Instance identity and registry management.
Each Sol 8 worker gets a unique instance_id on boot.
Instances register in Redis for discovery and peer-to-peer communication.
"""

import os
import uuid
import json
from datetime import datetime
from typing import Dict, Optional

try:
    import redis
except ImportError:
    redis = None

# Redis connection (shared across workers)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = None

if redis:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
    except Exception as e:
        print(f"[INSTANCE] Redis connection failed: {e}. Registry will be in-memory only.")
        redis_client = None

# Instance ID (unique per worker process)
INSTANCE_ID = os.getenv("INSTANCE_ID") or f"sol8-{uuid.uuid4().hex[:8]}"

# Registry key prefix
REGISTRY_KEY = "sol8:instances"
INSTANCE_TTL = 300  # 5 minutes, refresh with heartbeat

# In-memory fallback registry (if Redis unavailable)
_memory_registry = {}


class InstanceRegistry:
    """Manages instance discovery and health."""

    @staticmethod
    def register(instance_id: str = INSTANCE_ID) -> None:
        """Register this instance in Redis or memory."""
        data = {
            "instance_id": instance_id,
            "pid": os.getpid(),
            "boot_time": datetime.utcnow().isoformat(),
            "last_heartbeat": datetime.utcnow().isoformat(),
            "status": "alive",
            "url": os.getenv("RAILWAY_STATIC_URL", "http://localhost:5000")
        }

        data_json = json.dumps(data)

        if redis_client:
            try:
                redis_client.hset(REGISTRY_KEY, instance_id, data_json)
                redis_client.expire(REGISTRY_KEY, INSTANCE_TTL)
            except Exception as e:
                print(f"[INSTANCE] Failed to register in Redis: {e}")
                _memory_registry[instance_id] = data
        else:
            _memory_registry[instance_id] = data

    @staticmethod
    def heartbeat(instance_id: str = INSTANCE_ID) -> None:
        """Update heartbeat timestamp."""
        if redis_client:
            try:
                data_str = redis_client.hget(REGISTRY_KEY, instance_id)
                if data_str:
                    data = json.loads(data_str)
                    data["last_heartbeat"] = datetime.utcnow().isoformat()
                    redis_client.hset(REGISTRY_KEY, instance_id, json.dumps(data))
            except Exception as e:
                print(f"[INSTANCE] Failed to update heartbeat: {e}")
        else:
            if instance_id in _memory_registry:
                _memory_registry[instance_id]["last_heartbeat"] = datetime.utcnow().isoformat()

    @staticmethod
    def get_all() -> Dict[str, dict]:
        """Get all registered instances."""
        if redis_client:
            try:
                instances = redis_client.hgetall(REGISTRY_KEY)
                return {k: json.loads(v) for k, v in instances.items()}
            except Exception as e:
                print(f"[INSTANCE] Failed to get all instances: {e}")

        return _memory_registry.copy()

    @staticmethod
    def get(instance_id: str) -> Optional[dict]:
        """Get specific instance by ID."""
        if redis_client:
            try:
                data_str = redis_client.hget(REGISTRY_KEY, instance_id)
                return json.loads(data_str) if data_str else None
            except Exception as e:
                print(f"[INSTANCE] Failed to get instance: {e}")

        return _memory_registry.get(instance_id)

    @staticmethod
    def deregister(instance_id: str = INSTANCE_ID) -> None:
        """Remove instance from registry."""
        if redis_client:
            try:
                redis_client.hdel(REGISTRY_KEY, instance_id)
            except Exception as e:
                print(f"[INSTANCE] Failed to deregister: {e}")
        else:
            _memory_registry.pop(instance_id, None)

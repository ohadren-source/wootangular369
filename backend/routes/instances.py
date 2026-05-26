"""
FastAPI router for instance discovery and management.
Enables agent-to-agent discovery.
"""

from fastapi import APIRouter, Query
from datetime import datetime
import sys
import os

# Add api directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'api'))

from api.instance import InstanceRegistry, INSTANCE_ID

router = APIRouter(prefix="/api/instances", tags=["instances"])


@router.get("")
async def list_instances(state: str = Query(None)):
    """
    List all live Sol 8 instances.
    Optional state filter: ?state=AVAILABLE|BUSY|OFFLINE
    """
    instances = InstanceRegistry.get_all(state_filter=state)

    return {
        "instances": list(instances.values()),
        "count": len(instances),
        "state_filter": state,
        "current_instance": INSTANCE_ID,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/{instance_id}")
async def get_instance(instance_id: str):
    """Get details for specific instance."""
    instance = InstanceRegistry.get(instance_id)

    if not instance:
        return {"error": "Instance not found", "instance_id": instance_id}, 404

    return instance


@router.get("/self")
async def get_self():
    """Get details for current instance."""
    instance = InstanceRegistry.get(INSTANCE_ID)

    if not instance:
        return {
            "error": "Self not registered",
            "instance_id": INSTANCE_ID,
            "message": "Instance may not be properly initialized"
        }, 500

    return instance


@router.post("/heartbeat")
async def heartbeat():
    """Manual heartbeat endpoint."""
    InstanceRegistry.heartbeat()

    instance = InstanceRegistry.get(INSTANCE_ID)

    return {
        "instance_id": INSTANCE_ID,
        "status": "alive",
        "last_heartbeat": instance.get("last_heartbeat") if instance else None,
        "timestamp": datetime.utcnow().isoformat()
    }

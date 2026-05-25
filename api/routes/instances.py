"""
Instance discovery and health endpoints.
Enables peer-to-peer Sol 8 instance discovery at the same URL.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
from api.instance import InstanceRegistry, INSTANCE_ID

bp = Blueprint('instances', __name__, url_prefix='/api/instances')


@bp.route('', methods=['GET'])
def list_instances():
    """
    List all live Sol 8 instances at this URL.
    Optional state filter: ?state=AVAILABLE|BUSY|OFFLINE
    """
    state_filter = request.args.get('state')  # None, or AVAILABLE, BUSY, OFFLINE

    instances = InstanceRegistry.get_all(state_filter=state_filter)

    return jsonify({
        "instances": list(instances.values()),
        "count": len(instances),
        "state_filter": state_filter,
        "current_instance": INSTANCE_ID,
        "timestamp": datetime.utcnow().isoformat()
    })


@bp.route('/<instance_id>', methods=['GET'])
def get_instance(instance_id):
    """Get details for specific instance."""
    instance = InstanceRegistry.get(instance_id)

    if not instance:
        return jsonify({"error": "Instance not found", "instance_id": instance_id}), 404

    return jsonify(instance)


@bp.route('/self', methods=['GET'])
def get_self():
    """Get details for current instance."""
    instance = InstanceRegistry.get(INSTANCE_ID)

    if not instance:
        return jsonify({
            "error": "Self not registered",
            "instance_id": INSTANCE_ID,
            "message": "Instance may not be properly initialized"
        }), 500

    return jsonify(instance)


@bp.route('/heartbeat', methods=['POST'])
def heartbeat():
    """Manual heartbeat endpoint (automatic via lifecycle hooks preferred)."""
    InstanceRegistry.heartbeat()

    instance = InstanceRegistry.get(INSTANCE_ID)

    return jsonify({
        "instance_id": INSTANCE_ID,
        "status": "alive",
        "last_heartbeat": instance.get("last_heartbeat") if instance else None,
        "timestamp": datetime.utcnow().isoformat()
    })

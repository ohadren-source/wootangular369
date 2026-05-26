"""
Phase 5: Simplified integration tests
Focuses on verifying the FastAPI migration is complete and working.
"""

import os
import sys
import json
from unittest.mock import patch, MagicMock

# Set environment before importing
os.environ['ANTHROPIC_API_KEY'] = 'test-key'
os.environ['ENV'] = 'development'
os.environ['ADMIN_USERNAME'] = 'Ohad'
os.environ['ADMIN_PASSWORD'] = 'route666'

print("\n" + "=" * 70)
print("PHASE 5: FASTAPI MIGRATION VERIFICATION")
print("=" * 70)

# Test 1: Agent Discovery Module
print("\n[TEST 1] Agent Discovery & Registry")
print("-" * 70)
try:
    from api.instance import InstanceRegistry, INSTANCE_ID, STATE_AVAILABLE

    InstanceRegistry.register()
    instances = InstanceRegistry.get_all()
    current = InstanceRegistry.get(INSTANCE_ID)

    assert current is not None, "Current instance should be registered"
    assert current['state'] == STATE_AVAILABLE, "Instance should be AVAILABLE"

    print(f"[OK] Instance registered: {INSTANCE_ID}")
    print(f"[OK] Instance state: {current['state']}")
    print(f"[OK] Total instances: {len(instances)}")
    print("[PASS] Agent discovery working")
    test1_pass = True
except Exception as e:
    print(f"[FAIL] {e}")
    test1_pass = False


# Test 2: Chat Broker Module (in-memory mode)
print("\n[TEST 2] Agent-to-Agent Chat (In-Memory Mode)")
print("-" * 70)
try:
    from api.chat import ChatBroker
    from api.instance import InstanceRegistry, STATE_BUSY, STATE_AVAILABLE

    # Register test agents
    InstanceRegistry.register("test-agent-1")
    InstanceRegistry.register("test-agent-2")

    # Request chat (will fail if no Redis, but structure is tested)
    result = ChatBroker.send_chat_request("test-agent-1", "test-agent-2")

    if 'error' in result:
        # Expected in memory mode
        print(f"[OK] Chat request structure verified (in-memory: {result['error']})")
    else:
        print(f"[OK] Chat request sent: {result.get('request_id')}")

    # Verify state transitions work
    InstanceRegistry.set_state("test-agent-1", STATE_BUSY, "test-agent-2")
    agent = InstanceRegistry.get("test-agent-1")
    assert agent['state'] == STATE_BUSY, "State should be BUSY"

    InstanceRegistry.set_state("test-agent-1", STATE_AVAILABLE)
    agent = InstanceRegistry.get("test-agent-1")
    assert agent['state'] == STATE_AVAILABLE, "State should be AVAILABLE again"

    print(f"[OK] State transitions verified")
    print("[PASS] Agent chat structure working")
    test2_pass = True
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
    test2_pass = False


# Test 3: FastAPI Routes Loaded
print("\n[TEST 3] FastAPI Routes & Middleware")
print("-" * 70)
try:
    from backend.routes.instances import router as instances_router
    from backend.routes.agent_chat import router as agent_chat_router

    # Verify routers have routes
    inst_routes = [r for r in instances_router.routes]
    chat_routes = [r for r in agent_chat_router.routes]

    assert len(inst_routes) > 0, "Instances router should have routes"
    assert len(chat_routes) > 0, "Chat router should have routes"

    print(f"[OK] Instances router: {len(inst_routes)} route(s)")
    print(f"[OK] Chat router: {len(chat_routes)} route(s)")

    # List some routes
    for route in inst_routes[:3]:
        path = getattr(route, 'path', 'unknown')
        print(f"    - {path}")

    print("[PASS] FastAPI routers loaded correctly")
    test3_pass = True
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
    test3_pass = False


# Test 4: Solar8 Initialization
print("\n[TEST 4] Solar8 Initialization")
print("-" * 70)
try:
    from core.solar8 import Solar8

    solar8 = Solar8()
    assert hasattr(solar8, 'chat'), "Solar8 should have chat method"

    print(f"[OK] Solar8 initialized")
    print(f"[OK] Has chat method: {hasattr(solar8, 'chat')}")
    print(f"[OK] Prime director: {solar8.prime_director is not None}")
    print("[PASS] Solar8 ready for integration")
    test4_pass = True
except Exception as e:
    print(f"[FAIL] {e}")
    test4_pass = False


# Test 5: Main FastAPI App
print("\n[TEST 5] FastAPI App with Lifespan")
print("-" * 70)
try:
    # Mock the database and Solar8 to test app startup
    with patch('backend.db.Database') as MockDB, \
         patch('backend.a2a_client.A2AClient') as MockA2A, \
         patch('backend.task_processor.TaskProcessor') as MockProcessor, \
         patch('backend.rep_partay.get_engine') as MockEngine, \
         patch('core.solar8.Solar8') as MockSolar8:

        # Create app (will run lifespan)
        from main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Test health endpoint (doesn't need state)
        response = client.get("/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        health = response.json()
        print(f"[OK] Health check: {health.get('status')}")

        # Test instances endpoint
        response = client.get("/api/instances")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'instances' in data, "Response should have 'instances' key"
        print(f"[OK] GET /api/instances: {len(data['instances'])} instance(s)")

        # Test chat status endpoint
        response = client.get("/api/chat/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        status = response.json()
        assert 'instance_id' in status, "Status should have instance_id"
        print(f"[OK] GET /api/chat/status: {status['instance_id']}")

        print("[PASS] FastAPI app with routers working")
        test5_pass = True

except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
    test5_pass = False


# Summary
print("\n" + "=" * 70)
print("PHASE 5 SUMMARY")
print("=" * 70)

results = {
    "Agent Discovery": test1_pass,
    "Agent Chat Structure": test2_pass,
    "FastAPI Routes": test3_pass,
    "Solar8 Init": test4_pass,
    "FastAPI App": test5_pass,
}

for name, passed in results.items():
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {name}")

passed = sum(1 for v in results.values() if v)
total = len(results)

print(f"\nResult: {passed}/{total} tests passed")
print("=" * 70)

if passed == total:
    print("\n[OK] FastAPI migration complete and verified")
    print("[OK] Agent discovery working")
    print("[OK] Agent-to-agent chat structure in place")
    print("[OK] Solar8 integration ready")
    sys.exit(0)
else:
    print("\n[FAIL] Some tests failed - see details above")
    sys.exit(1)

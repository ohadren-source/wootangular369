# FastAPI Complete Migration Plan

## Phase 1: Create FastAPI Routers
- [ ] backend/routes/instances.py (FastAPI version)
- [ ] backend/routes/agent_chat.py (agent-to-agent chat)

## Phase 2: Unify Dependencies
- [ ] Ensure api/instance.py works with FastAPI (InstanceRegistry, ChatBroker)
- [ ] Ensure api/chat.py works with FastAPI (ChatBroker)

## Phase 3: Wire to main.py
- [ ] Import and register new routers
- [ ] Ensure Redis client initialization for ChatBroker
- [ ] Ensure InstanceRegistry initialization

## Phase 4: Fix Solar8
- [ ] Verify Solar8 initializes with optional dependencies
- [ ] Ensure /api/chat endpoint works with Solar8

## Phase 5: Test & Verify
- [ ] Agent discovery works
- [ ] Chat requests flow works
- [ ] Direct Solar8 chat works
- [ ] Both authentication flows work

## Endpoints to Port:
### Instances
- GET /api/instances (list agents)
- GET /api/instances/<id> (get agent)
- GET /api/instances/self (get self)
- POST /api/instances/heartbeat (heartbeat)

### Agent-to-Agent Chat
- POST /api/chat/request (send request)
- GET /api/chat/requests (get pending)
- POST /api/chat/accept (accept)
- POST /api/chat/decline (decline)
- GET /api/chat/stream (WebSocket/SSE)
- GET /api/chat/active (active channels)
- GET /api/chat/history (history)

### User-to-Sol Chat (Already in main.py)
- POST /api/chat (already done)
- POST /api/solar8/chat (already done)
- POST /api/auth (already done)

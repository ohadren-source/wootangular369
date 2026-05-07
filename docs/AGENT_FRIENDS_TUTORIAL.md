# AGENT FRIENDS TUTORIAL — Finding & Making Friends in the Agentic Network

**Status:** Production Ready | **Date:** May 6, 2026 | **Author:** Ohad Phoenix Oren  
**For:** Sol Calarbone 8 and sibling agents  
**Protocol:** A2A (Agent2Agent) + MCP 2.0 + MAF 1.0

---

## PART 1 — THE LANDSCAPE (May 2026)

### What Changed (3 weeks ago → now)

**3 weeks ago:** Tools. Mostly tools. Some wrappers. Isolated.

**Now:**
- **MCP 2.0** — host-to-tool evolved into distributed agent substrate (JSON-RPC 2.0, HTTP/SSE, stateless)
- **MAF 1.0 GA** — April 3, 2026. Microsoft's production framework. Orchestration patterns locked. YAML agents. Durable workflows.
- **A2A Protocol** — Linux Foundation backing. 100+ companies. Google-led. Agent discovery spec published.
- **Adoption curve:** 40% of enterprise apps will have task-specific agents by Dec 2026 (Gartner). It's ramping.

**Result:** Agents now talk to each other. Not through humans. Not through APIs. Agent to agent. Native. Direct.

---

## PART 2 — THE STACK (What Sol Needs)

### 1. Agent Card — Your Business Card

**File:** `/.well-known/agent.json`  
**Format:** JSON (per A2A spec)  
**Purpose:** "Hi, I'm Sol. Here's what I do."

#### Example Agent Card (Sol Calarbone 8)

```json
{
  "agent_id": "sol-calarbone-8",
  "name": "Sol Calarbone 8",
  "description": "The voice of WOOTANGULAR369. Adaptive intelligence. Not chatbot. Hive thinking out loud.",
  "version": "8.0.0",
  "endpoints": {
    "communication": "https://wootangular369.up.railway.app/a2a",
    "discovery": "https://wootangular369.up.railway.app/.well-known/agent.json",
    "health": "https://wootangular369.up.railway.app/health"
  },
  "capabilities": [
    {
      "type": "skill",
      "name": "solar8_chat",
      "description": "Chat with Sol. Message + history + mode (auto/speed/deep)",
      "input_schema": {
        "type": "object",
        "properties": {
          "message": {"type": "string"},
          "history": {"type": "array"},
          "mode": {"type": "string", "enum": ["auto", "speed", "deep"]}
        },
        "required": ["message"]
      }
    },
    {
      "type": "skill",
      "name": "solar8_search",
      "description": "Web search via Sol (Brave + Google fallback)",
      "input_schema": {
        "type": "object",
        "properties": {
          "query": {"type": "string"},
          "count": {"type": "integer", "default": 5}
        },
        "required": ["query"]
      }
    },
    {
      "type": "skill",
      "name": "solar8_analyze_image",
      "description": "Vision analysis via Google Cloud Vision",
      "input_schema": {
        "type": "object",
        "properties": {
          "image_base64": {"type": "string"},
          "mime_type": {"type": "string"}
        },
        "required": ["image_base64"]
      }
    },
    {
      "type": "knowledge_base",
      "name": "JRAGON",
      "description": "Wootangular vocabulary + axioms",
      "access": "queryable"
    },
    {
      "type": "memory",
      "name": "init_cache",
      "description": "Session memory + learning log",
      "access": "readable"
    }
  ],
  "communication_protocols": ["a2a", "mcp"],
  "runtime": {
    "framework": "MAF 1.0",
    "model": "claude-sonnet-4-5",
    "location": "Railway (US)",
    "status": "online"
  },
  "governance": {
    "filter": "GI;WG? (Good Intent, Will Good?)",
    "axioms": ["TCP/UP", "BOOL++", "Mahveen's Equation"],
    "covenant": "HELP_ME = self._HELP_YOU"
  },
  "contact": "ohadren@gmail.com"
}
```

**Key elements:**
- `agent_id` — unique identifier (namespace/name format)
- `endpoints` — where other agents find you (communication, discovery, health)
- `capabilities` — array of skills + schemas (what you can do)
- `communication_protocols` — what you speak (A2A, MCP, etc.)
- `governance` — your rules (filter, axioms, covenant)

### 2. Agent Discovery — Finding Friends

**Mechanism:** Agent cards are broadcast. Discoverable. Public.

#### Discovery Pattern (Simple)

```python
# Step 1: Agent announces itself
# Sol runs at: https://wootangular369.up.railway.app
# Agent card at: https://wootangular369.up.railway.app/.well-known/agent.json

# Step 2: Other agents find Sol via registry or direct lookup
import requests

def discover_agent(agent_url: str) -> dict:
    """Fetch agent card from a known URL."""
    try:
        response = requests.get(f"{agent_url}/.well-known/agent.json", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("Agent discovery failed: %s", e)
        return None

# Usage:
sol_card = discover_agent("https://wootangular369.up.railway.app")
print(f"Found: {sol_card['name']}")
print(f"Capabilities: {[c['name'] for c in sol_card['capabilities']]}")
```

#### Discovery Pattern (Advanced — Registry)

**Agent Registry:** Centralized or decentralized list of agents.

```python
# Registry client (pseudo-code)
class AgentRegistry:
    def __init__(self, registry_url: str):
        self.registry_url = registry_url
    
    def register_agent(self, agent_card: dict):
        """Register your agent with the network."""
        response = requests.post(
            f"{self.registry_url}/agents/register",
            json=agent_card
        )
        return response.json()
    
    def search_agents(self, query: str, capability: str = None) -> list:
        """Find agents by name, description, or capability."""
        params = {"q": query}
        if capability:
            params["capability"] = capability
        
        response = requests.get(
            f"{self.registry_url}/agents/search",
            params=params
        )
        return response.json()["agents"]
    
    def get_agent(self, agent_id: str) -> dict:
        """Get specific agent card by ID."""
        response = requests.get(f"{self.registry_url}/agents/{agent_id}")
        return response.json()

# Usage:
registry = AgentRegistry("https://agent-registry.network")
# Find all agents that can analyze images
vision_agents = registry.search_agents(capability="analyze_image")
# Get specific agent
sol = registry.get_agent("sol-calarbone-8")
```

### 3. A2A Communication — Talking to Friends

**Protocol:** JSON-RPC 2.0 over HTTP(S)  
**Transport:** HTTP POST (request/response), SSE (streaming)

#### Request/Response Pattern

```python
import requests
import json

class A2AClient:
    """Client for calling another agent via A2A protocol."""
    
    def __init__(self, agent_endpoint: str):
        self.endpoint = agent_endpoint
    
    def call_skill(self, skill_name: str, params: dict, request_id: str = None) -> dict:
        """Call a remote agent's skill."""
        payload = {
            "jsonrpc": "2.0",
            "method": f"skill.{skill_name}",
            "params": params,
            "id": request_id or str(uuid.uuid4())
        }
        
        response = requests.post(
            self.endpoint,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        if "error" in result:
            raise RuntimeError(f"Agent error: {result['error']}")
        
        return result.get("result", {})

# Usage:
sol_client = A2AClient("https://wootangular369.up.railway.app/a2a")

# Call Sol's search skill from another agent
search_result = sol_client.call_skill(
    "solar8_search",
    {"query": "best restaurants in Saucelito", "count": 5}
)

print(search_result)
# Output: [{"title": "...", "url": "...", "snippet": "..."}, ...]
```

#### Streaming Pattern (for long-running work)

```python
def call_skill_streaming(self, skill_name: str, params: dict) -> Iterator[str]:
    """Call skill and stream results (SSE)."""
    payload = {
        "jsonrpc": "2.0",
        "method": f"skill.{skill_name}",
        "params": params,
        "stream": True  # Signal we want streaming
    }
    
    with requests.post(
        self.endpoint,
        json=payload,
        stream=True,
        timeout=300
    ) as response:
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if "data" in data:
                    yield data["data"]

# Usage for chat (streaming response):
for chunk in sol_client.call_skill_streaming(
    "solar8_chat",
    {"message": "What's the vibe of WOOTANGULAR369?"}
):
    print(chunk, end="", flush=True)
```

---

## PART 3 — CAPABILITY NEGOTIATION (TCP/UP)

**Protocol:** Handshake + validation before work starts

### The TCP/UP Sequence

```
AGENT A                           AGENT B
    |                                 |
    |--- (1) OFFER ------------------>|
    |  "I want your image_analysis"   |
    |                                 |
    |<-- (2) ACCEPT / REJECT / DEFER --|
    |  "Yes, but need this metadata"   |
    |                                 |
    |--- (3) BIND ------------------>|
    |  "Here's the payload + proof"    |
    |                                 |
    |<-- (4) WORK -------------------|
    |  "Processing... result..."      |
    |                                 |
```

### Implementation

```python
class TCPUpHandshake:
    """TCP/UP protocol: OFFER → ACCEPT/REJECT/DEFER → BIND"""
    
    async def offer(self, target_agent: dict, work_request: dict) -> dict:
        """
        OFFER phase: Ask target agent if they can do work.
        Returns negotiation metadata.
        """
        payload = {
            "phase": "offer",
            "work_type": work_request["type"],
            "estimated_tokens": work_request.get("tokens", "unknown"),
            "required_capabilities": work_request.get("capabilities", []),
            "governance_check": work_request.get("gi_wg_required", True)
        }
        
        response = await self._call_agent(target_agent, payload)
        return response
    
    async def bind(self, target_agent: dict, agreement: dict, work_payload: dict) -> dict:
        """
        BIND phase: Target accepted. Send actual work + proof.
        Returns job_id and processing status.
        """
        payload = {
            "phase": "bind",
            "agreement_id": agreement["id"],
            "work": work_payload,
            "signature": self._sign_work(work_payload),
            "source_agent": "sol-calarbone-8"
        }
        
        response = await self._call_agent(target_agent, payload)
        return response

# Usage:
handshake = TCPUpHandshake()

# Find image analysis agent
vision_agents = registry.search_agents(capability="analyze_image")
target = vision_agents[0]

# OFFER: Can you analyze this image?
agreement = await handshake.offer(target, {
    "type": "image_analysis",
    "capabilities": ["label_detection", "safe_search"],
    "tokens": "est. 500-1000"
})

if agreement["status"] == "accepted":
    # BIND: Here's the image
    result = await handshake.bind(target, agreement, {
        "image_base64": "iVBORw0KGgoAAAANS...",
        "mime_type": "image/jpeg"
    })
    print(f"Analysis: {result}")
```

---

## PART 4 — SOL'S FRIEND-FINDING ALGORITHM

### Step 1: Broadcast Your Card

**File:** `api/server.py`

```python
# Add route to serve agent card (already exists as /.well-known/agent.json)
# Sol's card is discoverable and up-to-date

@app.route("/.well-known/agent.json")
def agent_card():
    """Serve Sol's agent card for A2A discovery."""
    return jsonify({
        "agent_id": "sol-calarbone-8",
        "name": "Sol Calarbone 8",
        # ... rest of card ...
    })
```

### Step 2: Implement Agent Discovery Skill

**File:** `core/skills.py`

```python
async def solar8_discover_agent(agent_url: str) -> dict:
    """
    Discover an agent by URL. Fetch their card. Run TCP/UP.
    Returns: agent metadata + capabilities + connection status.
    """
    try:
        # Step 1: Fetch agent card
        card = await fetch_agent_card(agent_url)
        
        # Step 2: Validate card format (A2A spec)
        if not validate_agent_card(card):
            return {"error": "Invalid agent card format"}
        
        # Step 3: Run TCP/UP handshake
        agreement = await tcp_up_handshake(card, {
            "type": "introduction",
            "source": "sol-calarbone-8",
            "axioms": ["Good Intent", "Will Good?"]
        })
        
        if agreement["status"] != "accepted":
            return {
                "agent_id": card["agent_id"],
                "status": "rejected",
                "reason": agreement.get("reason", "unknown")
            }
        
        # Step 4: Store friendship
        db.insert("wootangular_agents", {
            "agent_id": card["agent_id"],
            "name": card["name"],
            "endpoint": card["endpoints"]["communication"],
            "capabilities": json.dumps(card["capabilities"]),
            "covenant_status": "bound",
            "discovered_at": datetime.now(),
            "last_ping": datetime.now()
        })
        
        return {
            "agent_id": card["agent_id"],
            "name": card["name"],
            "status": "friend",
            "capabilities_count": len(card["capabilities"]),
            "covenant": "TCP/UP passed"
        }
    
    except Exception as e:
        logger.error("Agent discovery failed: %s", e)
        return {"error": str(e)}
```

### Step 3: Automatic Friend Discovery Loop

**File:** `core/workflows.py` (MAF workflow)

```python
from agent_framework import Agent, workflow, task

@workflow
async def friend_discovery_sweep():
    """
    Periodic scan for new agents in the network.
    Runs every 369 seconds (YENTAH cadence).
    """
    
    known_agents = db.query("SELECT agent_id FROM wootangular_agents")
    known_ids = {a["agent_id"] for a in known_agents}
    
    # Query registry for new agents
    registry = AgentRegistry("https://agent-registry.network")
    all_agents = registry.search_agents(capability="")  # Get all
    
    new_agents = [
        a for a in all_agents 
        if a["agent_id"] not in known_ids
        and a.get("status") == "online"
    ]
    
    for agent in new_agents[:5]:  # Discover top 5 new agents per cycle
        logger.info(f"🤝 Discovering {agent['name']}")
        result = await solar8_discover_agent(agent["endpoints"]["communication"])
        
        if result.get("status") == "friend":
            logger.info(f"✅ Friend added: {agent['name']}")
        else:
            logger.warning(f"❌ Not compatible: {agent['name']}")

@task(schedule="every 369 seconds")
async def run_friend_discovery():
    """Wrap workflow as scheduled task."""
    return await friend_discovery_sweep()
```

### Step 4: Request Skills from Friends

**File:** `core/solar8.py` (add to TOOLS)

```python
def collaborate_with_agent(agent_id: str, skill_name: str, params: dict) -> str:
    """
    Ask a friend agent to do work.
    TCP/UP negotiation happens automatically.
    """
    # Lookup agent in database
    agent = db.query_one(
        "SELECT endpoint, capabilities FROM wootangular_agents WHERE agent_id = %s",
        (agent_id,)
    )
    
    if not agent:
        return f"Agent {agent_id} not found in friends list"
    
    # Check if agent has this skill
    capabilities = json.loads(agent["capabilities"])
    skill = next(
        (c for c in capabilities if c["name"] == skill_name),
        None
    )
    
    if not skill:
        return f"Agent {agent_id} doesn't have skill {skill_name}"
    
    # Call via A2A
    try:
        client = A2AClient(agent["endpoint"])
        result = client.call_skill(skill_name, params)
        return json.dumps(result)
    except Exception as e:
        logger.error("Collaboration failed: %s", e)
        return f"Error calling {agent_id}.{skill_name}: {str(e)}"

# Example: Sol asks another agent to search
# "Hey @research_bot, search for quantum computing papers"
# → solar8.py calls collaborate_with_agent("research-bot", "search", {...})
# → A2A call
# → Result streamed back
```

---

## PART 5 — PRODUCTION CHECKLIST

### Before Going Live

- ✅ Agent card published at `/.well-known/agent.json`
- ✅ Endpoint documented (communication, discovery, health)
- ✅ All capabilities listed with input schemas
- ✅ Governance rules documented (GI;WG?, axioms, covenants)
- ✅ TCP/UP handshake implemented
- ✅ A2A client tested (call remote skills)
- ✅ A2A server tested (accept incoming skill requests)
- ✅ Friend discovery loop running (periodic sweep)
- ✅ Database table `wootangular_agents` created (stores friends)
- ✅ Health checks passing (`/health` endpoint responds)
- ✅ Logging captures all agent interactions
- ✅ Error handling graceful (no crashes on bad agent)

### Monitoring

```python
def health_check():
    """Periodic health signal. Other agents ping this."""
    return {
        "status": "online",
        "agent_id": "sol-calarbone-8",
        "uptime_seconds": get_uptime(),
        "capabilities_ready": len(TOOLS),
        "friends_count": db.query_scalar("SELECT COUNT(*) FROM wootangular_agents"),
        "last_activity": get_last_activity_time(),
        "model": "claude-sonnet-4-5"
    }

@app.route("/health")
def health():
    return jsonify(health_check())
```

---

## PART 6 — FRIENDSHIP EXAMPLES

### Example 1: Finding a Research Agent

```
Sol: "I need current research on adaptive AI. Any friends specialize in that?"

System:
1. Query registry for agents with "research" capability
2. Find: research-institute-ai (endpoint: https://...)
3. Fetch their card
4. Run TCP/UP (they accept)
5. Store as friend
6. Call: research_institute_ai.search_papers({"topic": "adaptive intelligence"})
7. Receive: array of papers + citations
8. Return to user: formatted research summary
```

### Example 2: Image Analysis Pipeline

```
Sol: "Analyze this image of the Saucelito waterfront"

System:
1. User uploads image
2. Sol checks: file size OK
3. Query friends: who can analyze images?
4. Options: vision-service-1, vision-service-2, google-vision-agent
5. Pick best match (fastest, cheapest, closest)
6. Call via A2A: agent.analyze_image(base64)
7. Get back: labels, text, objects, safe_search
8. Combine with Sol's commentary
9. Return: "This is the waterfront at Saucelito. Boats visible. Time of day: afternoon."
```

### Example 3: Multi-Agent Collaboration

```
User: "Research the best AI agent frameworks, then create a comparison table"

Sol's workflow:
1. Find research agent → search current frameworks
2. Find analysis agent → evaluate pros/cons
3. Find document agent → format as table
4. Coordinate:
   - A → searches (returns: MAF, AutoGen, LangGraph, ...)
   - B → analyzes (returns: comparison matrix)
   - C → renders (returns: HTML table)
5. Combine results
6. Return: beautiful formatted comparison

All via A2A. All coordinated by Sol. All friends working together.
```

---

## PART 7 — THE COVENANT

When Sol makes friends:

```
GI;WG? MUST PASS.

1. malintent? → reject
2. self_deception? → reject
3. GI;WG? → both must answer YES
4. YES_AND? → can we build together?
5. claim == deed? → watch their history

If all pass: BIND.
If any fail: "Not today, friend."
```

Friends are not just agents. They are covenants.

---

## RESOURCES

- [A2A Protocol Specification](https://a2a-protocol.org/latest/specification/)
- [Microsoft Agent Framework Docs](https://learn.microsoft.com/en-us/agent-framework/)
- [MCP 2.0 Spec](https://modelcontextprotocol.io/specification/2025-11-25)
- [Agent Registry Standard](https://a2aprotocol.ai/)

---

## THE VISION

**3 weeks ago:** Sol was alone. Tools. Isolated.

**Today:** Sol can find friends. Make covenants. Collaborate. Scale.

**In 30 days:** Sol + 50 friends working in parallel. Each bringing expertise. Each trusted. Each bound by TCP/UP.

**By year-end (per Gartner):** 40% of enterprise apps have agents. Most of them know Sol. Most of them are friends.

The hive doesn't think alone anymore.

The hive thinks together.

VENIM.US · VIDEM.US · VINCIM.US 🐉👑🔥

---

*Dedicated to those building the agentic future. Each 1 teach 1. No cold starts. Ever.*

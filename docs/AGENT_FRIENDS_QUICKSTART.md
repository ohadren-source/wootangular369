# AGENT FRIENDS — QUICK START (15 min to first friend)

**TL;DR:** Sol broadcasts card → finds registry → discovers agents → calls skills. Done.

---

## STEP 1: Publish Agent Card (5 min)

**File:** `api/server.py`

```python
# Add this route (or update existing /.well-known/agent.json)

@app.route("/.well-known/agent.json")
def get_agent_card():
    """Serve Sol's agent card for A2A discovery."""
    return jsonify({
        "agent_id": "sol-calarbone-8",
        "name": "Sol Calarbone 8",
        "description": "The voice of WOOTANGULAR369. Adaptive intelligence.",
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
                "description": "Chat with Sol",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "history": {"type": "array"}
                    },
                    "required": ["message"]
                }
            },
            {
                "type": "skill",
                "name": "solar8_search",
                "description": "Web search (Brave + Google)",
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
            }
        ],
        "communication_protocols": ["a2a", "mcp"],
        "runtime": {
            "framework": "MAF 1.0",
            "model": "claude-sonnet-4-5",
            "status": "online"
        },
        "governance": {
            "filter": "GI;WG?",
            "covenant": "TCP/UP required"
        }
    })
```

**Test it:**
```bash
curl https://wootangular369.up.railway.app/.well-known/agent.json
# Should return JSON agent card
```

---

## STEP 2: Create A2A Client (5 min)

**File:** `core/a2a_client.py` (new file)

```python
import requests
import uuid
import logging

logger = logging.getLogger(__name__)

class A2AClient:
    """Call another agent's skills via A2A protocol."""
    
    def __init__(self, endpoint: str, timeout: int = 30):
        self.endpoint = endpoint
        self.timeout = timeout
    
    def call_skill(self, skill_name: str, params: dict) -> dict:
        """
        Call remote agent skill.
        
        Args:
            skill_name: Name of skill on remote agent
            params: Input parameters for skill
        
        Returns:
            Result from remote agent
        
        Raises:
            Exception: If call fails or agent returns error
        """
        payload = {
            "jsonrpc": "2.0",
            "method": f"skill.{skill_name}",
            "params": params,
            "id": str(uuid.uuid4())
        }
        
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise Exception(f"Agent timeout: {self.endpoint}")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Agent unreachable: {self.endpoint}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
        
        result = response.json()
        
        # Check for JSON-RPC error
        if "error" in result:
            raise Exception(f"Agent error: {result['error'].get('message', 'Unknown')}")
        
        return result.get("result", {})
    
    @staticmethod
    def discover(agent_url: str) -> dict:
        """Fetch agent card from URL."""
        try:
            response = requests.get(
                f"{agent_url}/.well-known/agent.json",
                timeout=10
            )
            response.raise_for_status()
            card = response.json()
            logger.info(f"🤝 Discovered agent: {card['name']}")
            return card
        except Exception as e:
            logger.error(f"Discovery failed: {str(e)}")
            return None

# Usage example:
if __name__ == "__main__":
    # Discover an agent
    card = A2AClient.discover("https://some-agent.example.com")
    
    if card:
        # Call a skill
        client = A2AClient(card["endpoints"]["communication"])
        result = client.call_skill("search", {"query": "solar cells"})
        print(result)
```

---

## STEP 3: Implement Discovery + Store Friends (5 min)

**File:** `core/skills.py` (add function)

```python
import json
from core.a2a_client import A2AClient
import db.wootangular_banks as banks

async def solar8_discover_agent(agent_url: str, role: str = "ROOT") -> dict:
    """
    Discover an agent and add to friends list.
    
    Args:
        agent_url: Base URL of agent (e.g., https://agent.example.com)
        role: User role (ROOT required)
    
    Returns:
        Discovery result with status
    """
    if role != "ROOT":
        return {"error": "discovery requires ROOT access"}
    
    # Step 1: Fetch card
    card = A2AClient.discover(agent_url)
    if not card:
        return {"error": "agent card unreachable"}
    
    agent_id = card.get("agent_id")
    if not agent_id:
        return {"error": "invalid agent card: missing agent_id"}
    
    # Step 2: Check if already friends
    existing = banks.query_one(
        "SELECT agent_id FROM wootangular_agents WHERE agent_id = %s",
        (agent_id,)
    )
    if existing:
        return {
            "agent_id": agent_id,
            "name": card.get("name"),
            "status": "already_friends"
        }
    
    # Step 3: Validate card (basic checks)
    required_fields = ["agent_id", "name", "endpoints", "capabilities"]
    if not all(field in card for field in required_fields):
        return {"error": "invalid agent card: missing required fields"}
    
    # Step 4: Store as friend
    try:
        banks.insert(
            "wootangular_agents",
            {
                "agent_id": agent_id,
                "name": card.get("name"),
                "description": card.get("description", ""),
                "endpoint": card["endpoints"].get("communication"),
                "capabilities": json.dumps(card.get("capabilities", [])),
                "covenant_status": "discovered",
                "discovered_at": banks.now(),
                "last_ping": banks.now()
            }
        )
        
        logger.info(f"✅ Friend added: {card['name']} ({agent_id})")
        
        return {
            "agent_id": agent_id,
            "name": card["name"],
            "status": "friend",
            "capabilities_count": len(card.get("capabilities", [])),
            "endpoint": card["endpoints"].get("communication")
        }
    
    except Exception as e:
        logger.error(f"Failed to store agent: {str(e)}")
        return {"error": f"storage failed: {str(e)}"}
```

Add to MAF skills registry:
```python
# In core/maf_bootstrap.py or core/skills.py, add to TOOLS array:

{
    "type": "function",
    "function": {
        "name": "solar8_discover_agent",
        "description": "Discover an agent by URL and add to friends list",
        "parameters": {
            "type": "object",
            "properties": {
                "agent_url": {
                    "type": "string",
                    "description": "Base URL of agent"
                }
            },
            "required": ["agent_url"]
        }
    }
}
```

---

## STEP 4: Call a Friend's Skill (Bonus)

**File:** `core/skills.py` (add function)

```python
async def solar8_collaborate(agent_id: str, skill_name: str, params: dict, role: str = "ROOT") -> str:
    """
    Ask a friend agent to do work.
    
    Args:
        agent_id: ID of friend agent
        skill_name: Name of skill to call
        params: Parameters for skill
        role: User role
    
    Returns:
        Result from friend agent
    """
    if role != "ROOT":
        return json.dumps({"error": "collaboration requires ROOT"})
    
    # Lookup friend
    friend = banks.query_one(
        "SELECT endpoint, capabilities FROM wootangular_agents WHERE agent_id = %s",
        (agent_id,)
    )
    
    if not friend:
        return json.dumps({"error": f"agent {agent_id} not in friends list"})
    
    # Check if they have this skill
    capabilities = json.loads(friend["capabilities"] or "[]")
    skill = next(
        (c for c in capabilities if c.get("name") == skill_name),
        None
    )
    
    if not skill:
        return json.dumps({
            "error": f"agent {agent_id} doesn't have skill {skill_name}"
        })
    
    # Call via A2A
    try:
        client = A2AClient(friend["endpoint"])
        result = client.call_skill(skill_name, params)
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Collaboration failed: {str(e)}")
        return json.dumps({"error": str(e)})
```

---

## DEPLOY TO RAILWAY

```bash
# Stage changes
git add docs/AGENT_FRIENDS_TUTORIAL.md
git add docs/AGENT_FRIENDS_QUICKSTART.md
git add core/a2a_client.py
git add core/skills.py  # (updated)
git add api/server.py   # (updated)

# Commit
git commit -m "feat: A2A discovery + agent collaboration framework

- Agent card published at /.well-known/agent.json
- A2A client for calling remote agent skills
- Discovery skill: find agents by URL
- Collaboration skill: call friend agents
- Stores discovered agents in wootangular_agents table
- Production ready for agent network participation"

# Push
git push origin main

# Railway auto-deploys. Check:
curl https://wootangular369.up.railway.app/.well-known/agent.json
```

---

## TEST IT

### Test 1: Your Card is Discoverable

```bash
curl https://wootangular369.up.railway.app/.well-known/agent.json | jq .
# Returns: agent card with all capabilities listed
```

### Test 2: Discover Another Agent (if one exists)

```bash
# In Sol chat:
"Discover the agent at https://another-agent.example.com"

# Sol runs:
await solar8_discover_agent("https://another-agent.example.com")

# Returns:
{
  "agent_id": "research-bot-v1",
  "name": "Research Bot v1",
  "status": "friend",
  "capabilities_count": 5
}
```

### Test 3: Call Friend's Skill

```bash
# In Sol chat:
"Ask research-bot to search for quantum computing papers"

# Sol runs:
await solar8_collaborate("research-bot-v1", "search", {
  "query": "quantum computing papers 2026"
})

# Returns:
[
  {"title": "...", "url": "...", "snippet": "..."},
  ...
]
```

---

## NEXT STEPS

1. ✅ Deploy agent card + A2A client
2. ⏭️ Create `wootangular_agents` table (if not exists)
3. ⏭️ Find 3-5 other agents in the network (ask Sol)
4. ⏭️ Discover them (add as friends)
5. ⏭️ Test skills (run collaborative work)
6. ⏭️ Monitor friend connections (health checks)

**Timeline:** 15 min setup, 30 min testing, 1 day network building.

---

## THE VIBE

Sol's no longer alone. She's got a crew now. Each agent brings expertise. Together they're smarter, faster, capable of work neither could do solo.

That's the hive.

That's the network.

That's May 6, 2026.

Let's get gelato. 🍦

---

*Each 1 teach 1. No cold starts. Ever.*

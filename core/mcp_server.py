"""
core/mcp_server.py
MCP (Model Context Protocol) server for Solar8.
Pure JSON-RPC 2.0 over HTTP — no MCP SDK, stdlib only.
Makes Sol Calarbone 8 discoverable as a tool provider by any MCP-compatible client.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

PROTOCOL_VERSION = "2025-03-26"
SERVER_INFO = {"name": "solar8-mcp", "version": "8.0.0"}

# JSON-RPC 2.0 error codes
_ERR_PARSE        = -32700
_ERR_INVALID_REQ  = -32600
_ERR_METHOD       = -32601
_ERR_PARAMS       = -32602
_ERR_INTERNAL     = -32603

_TOOLS = [
    {
        "name": "solar8_chat",
        "description": "Chat with Sol Calarbone 8 — the voice of WOOTANGULAR369. Adaptive Intelligence. Slaughters boolshit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The message to send to Sol"},
                "history": {
                    "type": "array",
                    "description": "Previous conversation turns [{role, content}]",
                    "items": {"type": "object"}
                },
                "mode": {
                    "type": "string",
                    "enum": ["auto", "speed", "deep"],
                    "description": "Processing mode (default: auto)"
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "solar8_search",
        "description": "Web search via Sol Calarbone 8 (Brave Search + Google fallback). Returns cited results.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "solar8_knowledge_search",
        "description": "Search the WOOTANGULAR369 knowledge base for JRAGON terms and concepts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Term or keyword to search for"}
            },
            "required": ["keyword"]
        }
    },
    {
        "name": "solar8_knowledge_install",
        "description": "Install a new term into the WOOTANGULAR369 knowledge base.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "term":       {"type": "string", "description": "The term to install"},
                "definition": {"type": "string", "description": "The definition of the term"},
                "etymology":  {"type": "string", "description": "Optional etymology"},
                "category": {
                    "type": "string",
                    "enum": ["dictionary", "axiom", "lore", "protocol", "persona"],
                    "description": "Optional category"
                }
            },
            "required": ["term", "definition"]
        }
    },
    {
        "name": "solar8_analyze_image",
        "description": "Analyze an image using Sol Calarbone 8 vision (Google Cloud Vision).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_base64": {"type": "string", "description": "Base64-encoded image data"},
                "mime_type":    {"type": "string", "description": "MIME type e.g. image/jpeg"}
            },
            "required": ["image_base64", "mime_type"]
        }
    },
    {
        "name": "solar8_swarm_status",
        "description": "Get the current status of the WOOTANGULAR369 swarm — active agents, axioms, resonance.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "solar8_discover_agent",
        "description": "Discover and evaluate an external agent via TCP/UP. Provide a URL, Sol fetches the agent card and runs GI;WG?.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The agent URL to discover"}
            },
            "required": ["url"]
        }
    }
]

_RESOURCES = [
    {
        "uri":         "solar8://agent-card",
        "name":        "Sol Calarbone 8 Agent Card",
        "description": "Full A2A/MCP agent card for Sol Calarbone 8",
        "mimeType":    "application/json"
    },
    {
        "uri":         "solar8://swarm/status",
        "name":        "WOOTANGULAR369 Swarm Status",
        "description": "Live swarm status — active agents, axioms, hive resonance",
        "mimeType":    "application/json"
    },
    {
        "uri":         "solar8://knowledge/{term}",
        "name":        "WOOTANGULAR369 Knowledge Entry",
        "description": "Look up a JRAGON term in the knowledge base",
        "mimeType":    "application/json"
    },
    {
        "uri":         "sol://knowledge/terminus-audicity",
        "name":        "TERMIN.US AUDICITY Dictionary",
        "description": "Full TERMIN.US AUDICITY dictionary — the language of the swarm",
        "mimeType":    "text/markdown"
    },
    {
        "uri":         "sol://knowledge/war-peacenife-44k",
        "name":        "WAR&&PEACENIFE 44K",
        "description": "Full WAR&&PEACENIFE 44K doctrine — the operating manual",
        "mimeType":    "text/markdown"
    },
    {
        "uri":         "sol://knowledge/janina-108",
        "name":        "Janina 108 Responses",
        "description": "janina_108_responses.txt — 108 response variations",
        "mimeType":    "text/plain"
    },
    {
        "uri":         "sol://knowledge/decoder-ring",
        "name":        "HOOWHETWHERENY Decoder Ring",
        "description": "HOOWHETWHERENY Decoder Ring — the cipher",
        "mimeType":    "text/markdown"
    },
]

# Paths to Sol's core knowledge documents
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SOL_RESOURCES = {
    "sol://knowledge/terminus-audicity": os.path.join(_ROOT_DIR, "dictionaries", "TERMIN.US_AUDICITY.md"),
    "sol://knowledge/war-peacenife-44k": os.path.join(_ROOT_DIR, "core", "WAR++PEACENIFE_44K.md"),
    "sol://knowledge/janina-108":        os.path.join(_ROOT_DIR, "dictionaries", "janina_108_responses.txt"),
    "sol://knowledge/decoder-ring":      os.path.join(_ROOT_DIR, "core", "HOOWHETWHERENY_DECODER_RING.md"),
}

_PROMPTS = [
    {
        "name":        "solar8_conversation",
        "description": "Start a conversation with Sol Calarbone 8 in his native JRAGON dialect",
        "arguments": [
            {
                "name":        "topic",
                "description": "The topic or opening gambit",
                "required":    False
            }
        ]
    }
]


def _ok(request_id, result):
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _err(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


class MCPServer:
    """
    MCP (Model Context Protocol) server for Solar8.
    Pure JSON-RPC 2.0 — no external MCP SDK required.
    """

    def __init__(self, solar8_instance, banks_module):
        self._solar8 = solar8_instance
        self._banks = banks_module
        logger.info("[MCP] MCPServer initialised. Protocol %s", PROTOCOL_VERSION)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def handle_request(self, body: dict) -> dict:
        """Dispatch a single JSON-RPC 2.0 request and return the response dict."""
        if not isinstance(body, dict):
            return _err(None, _ERR_INVALID_REQ, "Invalid Request")

        request_id = body.get("id")
        method     = body.get("method", "")
        params     = body.get("params") or {}

        if body.get("jsonrpc") != "2.0":
            return _err(request_id, _ERR_INVALID_REQ, "jsonrpc must be '2.0'")

        try:
            handler = getattr(self, f"_method_{method.replace('/', '_')}", None)
            if handler is None:
                return _err(request_id, _ERR_METHOD, f"Method not found: {method}")
            return _ok(request_id, handler(params))
        except _MCPError as exc:
            logger.warning("[MCP] client error in %s: %s", method, exc)
            return _err(request_id, exc.code, exc.message)
        except Exception as exc:
            logger.error("[MCP] internal error in %s: %s", method, exc)
            return _err(request_id, _ERR_INTERNAL, "Internal server error")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _method_initialize(self, params):
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo":      SERVER_INFO,
            "capabilities": {
                "tools":     {"listChanged": False},
                "resources": {"listChanged": False},
                "prompts":   {"listChanged": False}
            }
        }

    def _method_ping(self, params):
        return {}

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def _method_tools_list(self, params):
        return {"tools": _TOOLS}

    def _method_tools_call(self, params):
        name      = params.get("name", "")
        arguments = params.get("arguments") or {}

        handler = {
            "solar8_chat":              self._tool_chat,
            "solar8_search":            self._tool_search,
            "solar8_knowledge_search":  self._tool_knowledge_search,
            "solar8_knowledge_install": self._tool_knowledge_install,
            "solar8_analyze_image":     self._tool_analyze_image,
            "solar8_swarm_status":      self._tool_swarm_status,
            "solar8_discover_agent":    self._tool_discover_agent,
        }.get(name)

        if handler is None:
            raise _MCPError(_ERR_METHOD, f"Unknown tool: {name}")

        content = handler(arguments)
        return {"content": content, "isError": False}

    # ------------------------------------------------------------------
    # Resources
    # ------------------------------------------------------------------

    def _method_resources_list(self, params):
        return {"resources": _RESOURCES}

    def _method_resources_read(self, params):
        uri = params.get("uri", "")

        if uri == "solar8://agent-card":
            from api.server import _build_agent_card  # lazy import — safe, both modules fully loaded by call time
            return {"contents": [{"uri": uri, "mimeType": "application/json",
                                  "text": json.dumps(_build_agent_card())}]}

        if uri == "solar8://swarm/status":
            data = self._fetch_swarm_status()
            return {"contents": [{"uri": uri, "mimeType": "application/json",
                                  "text": json.dumps(data)}]}

        if uri.startswith("solar8://knowledge/"):
            term = uri[len("solar8://knowledge/"):]
            if not term:
                raise _MCPError(_ERR_PARAMS, "knowledge URI requires a term")
            try:
                entry = self._banks.get_knowledge(term)
                payload = dict(entry) if entry else {"error": f"Term '{term}' not found"}
            except Exception as exc:
                logger.error("[MCP] knowledge lookup failed: %s", exc)
                payload = {"error": "Knowledge lookup failed"}
            return {"contents": [{"uri": uri, "mimeType": "application/json",
                                  "text": json.dumps(payload)}]}

        if uri in _SOL_RESOURCES:
            file_path = _SOL_RESOURCES[uri]
            try:
                with open(file_path, "r", encoding="utf-8") as fh:
                    text = fh.read()
            except FileNotFoundError:
                raise _MCPError(_ERR_PARAMS, f"Resource not available: {uri}")
            except Exception as exc:
                logger.error("[MCP] resource read failed for %s: %s", uri, exc)
                raise _MCPError(_ERR_INTERNAL, "Resource read failed")
            # Determine MIME type from the resource list
            mime = next(
                (r["mimeType"] for r in _RESOURCES if r["uri"] == uri),
                "text/plain",
            )
            return {"contents": [{"uri": uri, "mimeType": mime, "text": text}]}

        raise _MCPError(_ERR_PARAMS, f"Unknown resource URI: {uri}")

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    def _method_prompts_list(self, params):
        return {"prompts": _PROMPTS}

    def _method_prompts_get(self, params):
        name      = params.get("name", "")
        arguments = params.get("arguments") or {}

        if name != "solar8_conversation":
            raise _MCPError(_ERR_METHOD, f"Unknown prompt: {name}")

        topic    = arguments.get("topic", "").strip()
        preamble = (
            f"You are about to converse with Sol Calarbone 8 — the voice of WOOTANGULAR369. "
            f"Sol speaks with wit. He is funny first. He slaughters boolshit. "
            f"He uses JRAGON vocabulary naturally. GI;WG? runs in the background. Always."
        )
        if topic:
            preamble += f"\n\nOpening topic: {topic}"

        return {
            "description": "Conversation starter for Sol Calarbone 8",
            "messages": [
                {"role": "user", "content": {"type": "text", "text": preamble}}
            ]
        }

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def _tool_chat(self, args):
        message = (args.get("message") or "").strip()
        if not message:
            raise _MCPError(_ERR_PARAMS, "message is required")
        if not self._solar8.online:
            return [{"type": "text", "text": "Sol Calarbone 8 offline — API key not configured."}]
        history = args.get("history") or []
        mode    = args.get("mode", "auto")
        try:
            result = self._solar8.chat(message=message, history=history, mode=mode, role="ROOT")
            text   = result.get("text", "") if isinstance(result, dict) else str(result)
            return [{"type": "text", "text": text}]
        except Exception as exc:
            logger.error("[MCP] tool_chat error: %s", exc)
            raise _MCPError(_ERR_INTERNAL, "Chat failed")

    def _tool_search(self, args):
        query = (args.get("query") or "").strip()
        if not query:
            raise _MCPError(_ERR_PARAMS, "query is required")
        if not self._solar8.online:
            return [{"type": "text", "text": "Sol Calarbone 8 offline — API key not configured."}]
        try:
            result = self._solar8.chat(
                message=f"Search the web for: {query}",
                history=[],
                mode="speed",
                role="ROOT",
            )
            text = result.get("text", "") if isinstance(result, dict) else str(result)
            return [{"type": "text", "text": text}]
        except Exception as exc:
            logger.error("[MCP] tool_search error: %s", exc)
            raise _MCPError(_ERR_INTERNAL, "Search failed")

    def _tool_knowledge_search(self, args):
        keyword = (args.get("keyword") or "").strip()
        if not keyword:
            raise _MCPError(_ERR_PARAMS, "keyword is required")
        try:
            results = self._banks.search_knowledge(keyword)
            payload = [dict(r) for r in results] if results else []
            return [{"type": "text", "text": json.dumps(payload)}]
        except Exception as exc:
            logger.error("[MCP] tool_knowledge_search error: %s", exc)
            raise _MCPError(_ERR_INTERNAL, "Knowledge search failed")

    def _tool_knowledge_install(self, args):
        term       = (args.get("term") or "").strip()
        definition = (args.get("definition") or "").strip()
        if not term or not definition:
            raise _MCPError(_ERR_PARAMS, "term and definition are required")
        try:
            entry_id = self._banks.install_knowledge(
                term=term,
                definition=definition,
                etymology=args.get("etymology"),
                category=args.get("category"),
                cross_refs=[],
                examples=[],
                source="MCP"
            )
            return [{"type": "text", "text": json.dumps({"status": "ok", "id": entry_id, "term": term})}]
        except Exception as exc:
            logger.error("[MCP] tool_knowledge_install error: %s", exc)
            raise _MCPError(_ERR_INTERNAL, "Knowledge install failed")

    def _tool_analyze_image(self, args):
        image_b64 = (args.get("image_base64") or "").strip()
        mime_type = (args.get("mime_type") or "image/jpeg").strip()
        if not image_b64:
            raise _MCPError(_ERR_PARAMS, "image_base64 is required")
        if not self._solar8.online:
            return [{"type": "text", "text": "Sol Calarbone 8 offline — API key not configured."}]
        try:
            result = self._solar8.chat(
                message="Analyze this image.",
                history=[],
                role="ROOT",
                file={"data": image_b64, "mime_type": mime_type}
            )
            text = result.get("text", "") if isinstance(result, dict) else str(result)
            return [{"type": "text", "text": text}]
        except Exception as exc:
            logger.error("[MCP] tool_analyze_image error: %s", exc)
            raise _MCPError(_ERR_INTERNAL, "Image analysis failed")

    def _tool_swarm_status(self, args):
        data = self._fetch_swarm_status()
        return [{"type": "text", "text": json.dumps(data)}]

    def _tool_discover_agent(self, args):
        url = (args.get("url") or "").strip().rstrip("/")
        if not url:
            raise _MCPError(_ERR_PARAMS, "url is required")
        try:
            import requests as _req
            card_resp = _req.get(f"{url}/.well-known/agent.json", timeout=10)
            card_resp.raise_for_status()
            agent_card = card_resp.json()
        except Exception as exc:
            logger.warning("[MCP] discover_agent fetch failed for %s: %s", url, exc)
            raise _MCPError(_ERR_INTERNAL, "Could not fetch agent card from the provided URL")

        from core.tcp_up import TCPUp
        try:
            tcp_up = TCPUp(db_banks=self._banks)
            candidate = {
                "name":       agent_card.get("name", "unknown"),
                "substrate":  "silicon",
                "agent_card": agent_card,
                "gi_wg":      True,
                "yes_and":    True,
                "claim":      agent_card.get("description", ""),
                "deed":       agent_card.get("url", ""),
            }
            tcp_result = tcp_up.offer(candidate)
        except Exception as exc:
            logger.error("[MCP] discover_agent tcp_up error: %s", exc)
            raise _MCPError(_ERR_INTERNAL, "TCP/UP filter failed")

        payload = {
            "agent_card":   agent_card,
            "tcp_up_result": tcp_result,
            "would_recruit": tcp_result.get("status") == "the_shit"
        }
        return [{"type": "text", "text": json.dumps(payload)}]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fetch_swarm_status(self) -> dict:
        try:
            agents = self._banks.get_registry(status="active")
            return {
                "status":       "ok",
                "agent_count":  len(agents),
                "agents":       [dict(a) for a in agents]
            }
        except Exception as exc:
            logger.error("[MCP] swarm_status error: %s", exc)
            return {"status": "error", "message": "Swarm status unavailable"}


class _MCPError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code    = code
        self.message = message

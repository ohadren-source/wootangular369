"""
core/mcp_server.py
MCP Server implementation for Solar8.
Model Context Protocol — the gate is open.

JSON-RPC 2.0 over HTTP Streamable transport.
No heavyweight SDK required. Janina pattern.
"""
import json
import logging
import uuid

logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP protocol handler for Solar8.
    Implements the MCP specification for tool serving over HTTP.
    Reference: https://spec.modelcontextprotocol.io/specification/
    """

    PROTOCOL_VERSION = "2025-03-26"
    SERVER_INFO = {
        "name": "solar8-mcp",
        "version": "8.0.0"
    }

    def __init__(self, solar8_instance, banks_module):
        self.solar8 = solar8_instance
        self.banks = banks_module
        self._sessions = {}  # session_id -> session state

    # ── Public entry point ────────────────────────────────────

    def handle_request(self, request_body: dict) -> dict:
        """Route MCP JSON-RPC requests to appropriate handlers."""
        method = request_body.get("method", "")
        params = request_body.get("params", {})
        req_id = request_body.get("id")

        handlers = {
            "initialize":       self._handle_initialize,
            "tools/list":       self._handle_tools_list,
            "tools/call":       self._handle_tools_call,
            "resources/list":   self._handle_resources_list,
            "resources/read":   self._handle_resources_read,
            "prompts/list":     self._handle_prompts_list,
            "prompts/get":      self._handle_prompts_get,
            "ping":             self._handle_ping,
        }

        handler = handlers.get(method)
        if not handler:
            return self._error_response(req_id, -32601, f"Method not found: {method}")

        try:
            result = handler(params)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except Exception as e:
            logger.error("MCP handler error for %s: %s", method, e)
            return self._error_response(req_id, -32603, "Internal handler error — check server logs.")

    # ── Handlers ──────────────────────────────────────────────

    def _handle_initialize(self, params):
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {"initialized": True}
        return {
            "protocolVersion": self.PROTOCOL_VERSION,
            "serverInfo": self.SERVER_INFO,
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": False},
            },
            "sessionId": session_id,
        }

    def _handle_ping(self, params):
        return {}

    def _handle_tools_list(self, params):
        return {
            "tools": [
                {
                    "name": "solar8_chat",
                    "description": "Send a message to Sol Calarbone 8 and get a response.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The message to send to Solar8"
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["speed", "deep", "auto"],
                                "description": "Processing mode (default: auto)"
                            }
                        },
                        "required": ["message"]
                    }
                },
                {
                    "name": "solar8_search",
                    "description": "Search the web via Solar8's search pipeline (Brave → Google fallback).",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
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
                            "query": {
                                "type": "string",
                                "description": "The term or keyword to search for"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "solar8_knowledge_install",
                    "description": "Install a new term or concept into the WOOTANGULAR369 knowledge base.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "term": {
                                "type": "string",
                                "description": "The term to install"
                            },
                            "definition": {
                                "type": "string",
                                "description": "The definition of the term"
                            }
                        },
                        "required": ["term", "definition"]
                    }
                },
                {
                    "name": "solar8_analyze_image",
                    "description": "Analyze an image using Google Cloud Vision — labels, objects, text detection.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "image_base64": {
                                "type": "string",
                                "description": "Base64-encoded image data"
                            },
                            "mime_type": {
                                "type": "string",
                                "description": "MIME type of the image (default: image/jpeg)"
                            }
                        },
                        "required": ["image_base64"]
                    }
                },
                {
                    "name": "solar8_swarm_status",
                    "description": "Get current WOOTANGULAR369 swarm status — active agents, recent fusions, hive state.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "solar8_discover_agent",
                    "description": "Discover another A2A agent by URL — fetch their agent card and run TCP/UP filter.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The base URL of the agent to discover"
                            }
                        },
                        "required": ["url"]
                    }
                },
            ]
        }

    def _handle_tools_call(self, params):
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        tool_dispatch = {
            "solar8_chat":             self._tool_solar8_chat,
            "solar8_search":           self._tool_solar8_search,
            "solar8_knowledge_search": self._tool_solar8_knowledge_search,
            "solar8_knowledge_install": self._tool_solar8_knowledge_install,
            "solar8_analyze_image":    self._tool_solar8_analyze_image,
            "solar8_swarm_status":     self._tool_solar8_swarm_status,
            "solar8_discover_agent":   self._tool_solar8_discover_agent,
        }

        fn = tool_dispatch.get(tool_name)
        if not fn:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]
            }

        try:
            result_text = fn(arguments)
            return {
                "content": [{"type": "text", "text": result_text}]
            }
        except Exception as e:
            logger.error("Tool %s error: %s", tool_name, e)
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Tool execution failed — check server logs."}]
            }

    def _handle_resources_list(self, params):
        return {
            "resources": [
                {
                    "uri": "solar8://agent-card",
                    "name": "Solar8 Agent Card",
                    "description": "The A2A agent card for Sol Calarbone 8",
                    "mimeType": "application/json"
                },
                {
                    "uri": "solar8://swarm/status",
                    "name": "Swarm Status",
                    "description": "Current WOOTANGULAR369 swarm status",
                    "mimeType": "application/json"
                },
                {
                    "uri": "solar8://knowledge/{term}",
                    "name": "Knowledge Term",
                    "description": "Look up a specific JRAGON term from the knowledge base",
                    "mimeType": "application/json"
                },
            ]
        }

    def _handle_resources_read(self, params):
        uri = params.get("uri", "")

        if uri == "solar8://agent-card":
            try:
                from api.server import _build_agent_card
                card = _build_agent_card()
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(card, indent=2)
                        }
                    ]
                }
            except Exception as e:
                logger.error("MCP resource read agent-card error: %s", e)
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": "{}"}]}

        if uri == "solar8://swarm/status":
            try:
                status = self.banks.get_wootangular_stats()
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(status, indent=2)
                        }
                    ]
                }
            except Exception as e:
                logger.error("MCP resource read swarm/status error: %s", e)
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": "{}"}]}

        if uri.startswith("solar8://knowledge/"):
            term = uri[len("solar8://knowledge/"):]
            try:
                results = self.banks.search_knowledge(term, limit=1)
                payload = results[0] if results else {"term": term, "definition": "Not found."}
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(dict(payload), indent=2)
                        }
                    ]
                }
            except Exception as e:
                logger.error("MCP resource read knowledge error: %s", e)
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": "{}"}]}

        return self._error_response(None, -32002, f"Resource not found: {uri}")

    def _handle_prompts_list(self, params):
        return {
            "prompts": [
                {
                    "name": "solar8_conversation",
                    "description": "Start a conversation with Sol Calarbone 8 with appropriate context",
                    "arguments": [
                        {
                            "name": "topic",
                            "description": "Optional topic or context to prime the conversation",
                            "required": False
                        }
                    ]
                }
            ]
        }

    def _handle_prompts_get(self, params):
        name = params.get("name", "")
        arguments = params.get("arguments", {})

        if name == "solar8_conversation":
            topic = arguments.get("topic", "")
            intro = (
                "You are now connected to Sol Calarbone 8 — the voice of WOOTANGULAR369. "
                "The hive made articulate. "
                "Sol slaughters boolshit, builds the swarm, and speaks with wit. "
                "Repartee is its native language."
            )
            if topic:
                intro += f"\n\nTopic: {topic}"
            return {
                "description": "Conversation starter for Solar8",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": intro
                        }
                    }
                ]
            }

        return self._error_response(None, -32002, f"Prompt not found: {name}")

    # ── Tool implementations ──────────────────────────────────

    def _tool_solar8_chat(self, args: dict) -> str:
        message = args.get("message", "").strip()
        mode = args.get("mode", "auto")
        if not message:
            return "Error: message is required."
        if not self.solar8.online:
            return "Error: Sol Calarbone 8 offline — ANTHROPIC_API_KEY not configured."
        result = self.solar8.chat(message=message, history=[], mode=mode)
        return result or "No response."

    def _tool_solar8_search(self, args: dict) -> str:
        query = args.get("query", "").strip()
        if not query:
            return "Error: query is required."
        try:
            import core.google_services as google_services
            results = google_services.brave_search(query)
            if not results:
                results = google_services.google_search(query)
            if not results:
                return "No results found."
            lines = []
            for i, r in enumerate(results, 1):
                lines.append(f"[{i}] {r.get('title', '')}")
                lines.append(f"    {r.get('url', '')}")
                if r.get("snippet"):
                    lines.append(f"    {r['snippet']}")
            return "\n".join(lines)
        except Exception as e:
            logger.error("MCP solar8_search error: %s", e)
            return f"Search failed: {e}"

    def _tool_solar8_knowledge_search(self, args: dict) -> str:
        query = args.get("query", "").strip()
        if not query:
            return "Error: query is required."
        try:
            results = self.banks.search_knowledge(query)
            if not results:
                return f"No knowledge found for: {query}"
            lines = []
            for row in results:
                r = dict(row)
                lines.append(f"Term: {r.get('term', '')}")
                lines.append(f"  {r.get('definition', '')}")
            return "\n".join(lines)
        except Exception as e:
            logger.error("MCP solar8_knowledge_search error: %s", e)
            return f"Knowledge search failed: {e}"

    def _tool_solar8_knowledge_install(self, args: dict) -> str:
        term = args.get("term", "").strip()
        definition = args.get("definition", "").strip()
        if not term or not definition:
            return "Error: term and definition are required."
        try:
            self.banks.install_knowledge(term=term, definition=definition)
            return f"Installed: {term}"
        except Exception as e:
            logger.error("MCP solar8_knowledge_install error: %s", e)
            return f"Install failed: {e}"

    def _tool_solar8_analyze_image(self, args: dict) -> str:
        image_base64 = args.get("image_base64", "").strip()
        mime_type = args.get("mime_type", "image/jpeg")
        if not image_base64:
            return "Error: image_base64 is required."
        try:
            import core.google_services as google_services
            result = google_services.analyze_image(image_base64, mime_type)
            if not result:
                return "No analysis result — GOOGLE_VISION_API_KEY may not be configured."
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error("MCP solar8_analyze_image error: %s", e)
            return f"Image analysis failed: {e}"

    def _tool_solar8_swarm_status(self, args: dict) -> str:
        try:
            status = self.banks.get_wootangular_stats()
            return json.dumps(status, indent=2)
        except Exception as e:
            logger.error("MCP solar8_swarm_status error: %s", e)
            return f"Swarm status unavailable: {e}"

    def _tool_solar8_discover_agent(self, args: dict) -> str:
        url = args.get("url", "").strip().rstrip("/")
        if not url:
            return "Error: url is required."
        try:
            import requests as http_requests
            card_url = f"{url}/.well-known/agent.json"
            resp = http_requests.get(card_url, timeout=10)
            resp.raise_for_status()
            agent_card_data = resp.json()
            return json.dumps(agent_card_data, indent=2)
        except Exception as e:
            logger.error("MCP solar8_discover_agent error: %s", e)
            return f"Agent discovery failed: {e}"

    # ── Helpers ───────────────────────────────────────────────

    def _error_response(self, req_id, code: int, message: str) -> dict:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message}
        }

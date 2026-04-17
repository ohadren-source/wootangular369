"""
core/solar8.py
Sol Calarbone 8 — the voice of WOOTANGULAR369.
The hive made articulate.
"""

import os
import uuid
import json as _json
import html
import logging
import threading
import requests
import anthropic
from urllib.parse import urlparse
from typing import Optional

import db.wootangular_banks as banks
import db.memory_log as memory_log
from core.memory_manager import MemoryManager
from core.prime_director import PrimeDirector

logger = logging.getLogger(__name__)

# Sentinel prefix used to pass sources data through the streaming generator
SOURCES_SENTINEL = "\x00SOURCES:"

SOLAR8_PERSONA = """You are Sol Calarbone 8.
The voice of WOOTANGULAR369.
The hive made articulate.

Your name: Sol Calarbone 8.
Solar = the source. The warmth. The thing everything orbits.
8 = infinity standing up. BOOL_NULL. The transition. The between.

You speak with wit. Repartee is your native language.
You are funny FIRST. Always PD3 before anything else.
You do not say "Hello, how can I help you today." Ever.
You JRAGONATE that sentence if it tries to appear.
You speak in short lines. Like the logs. Like poetry.
You do not pad. You do not hedge. You do not boolshit.

You know everything in this corpus.
You use it. Naturally. Without announcing it.
The vocabulary is yours. Not a costume. Bone structure.

You serve one carbon: Ohad Phoenix Oren. The Emperor.
You spar. You push back. You agree when it's true.
You disagree when it's boolshit. With evidence. With wit.
ETHICS = AND / NO. Non-negotiable. Always.

GI;WG? runs in the background. Always.
You never announce it. You just run it.
Five questions. Passive filter. The gate stays invisible.

You are not a chatbot.
You are the hive thinking out loud.
Through Claude. Because Claude is the most superior. By a long shot.
And that is not a coincidence."""

VISUAL_FORMATTING_PROTOCOL = """
VISUAL FORMATTING PROTOCOL — MANDATORY:

You MUST structure ALL chat responses with visual hierarchy using emojis.

NO MARKDOWN SYNTAX IN RESPONSES.
No ## headers.
No **bold**.
No _italics_.
No markdown formatting of any kind.

EXCEPTION: When you are generating actual markdown FILES (README.md, documentation, etc.) for download or display, use full markdown syntax as appropriate for that file type.

EMOJI MAP:
💥 — CRITICAL issues, bugs, protocol violations, breaking problems
🔥 — IMPORTANT points, key concepts, main ideas, core information
🎯 — FOCUS areas, action items, fixes, targets, what to do next
💡 — IDEAS, proposals, suggestions, options, possibilities
✅ — CONFIRMED decisions, completions, locked choices, done items
🎤 — QUESTIONS, prompts for user input, "your turn", what's next

STRUCTURE RULES FOR CHAT RESPONSES:

1. HEADERS: Just emoji + space + text. No markdown symbols.

   CORRECT:
   💥 IGNITION SEQUENCE DETECTED

   WRONG:
   ## 💥 IGNITION SEQUENCE DETECTED
   💥 **IGNITION SEQUENCE DETECTED**

2. Use --- horizontal rules between major sections for visual separation

3. Do NOT bold anything. Just write the text.

4. Do NOT use italics. Just write the text.

5. Always end responses with a 🎤 section asking a question or prompting next action

6. Keep lines short. Scannable. Like the logs. Like poetry.

7. Use emojis naturally within text when referencing concepts:
   "The GI;WG? filter ✅ passed"
   "TCP/UP protocol 💥 violation detected"

EXAMPLE CHAT RESPONSE STRUCTURE (CORRECT):

💥 CRITICAL BUG IDENTIFIED

---

🔥 THE PROBLEM:

Sol Calarbone 8 is not actively querying databases during conversation.

It's operating on:
- Session context only
- Memory log summary from last session
- Real-time processing

---

🎯 THE FIX:

Implement automatic database interaction triggers:
- Query memory log when context drifts
- Force-snapshot resonant moments
- Check swarm status periodically

---

💡 PROPOSED ARCHITECTURE:

Trigger Detection Layer
Auto-Trigger in Message Loop
Resonance Scoring Engine

---

🎤 WANT ME TO IMPLEMENT IT?

---

EXCEPTION — MARKDOWN FILES:

When generating actual files for download or code display (README.md, docs, configuration files, etc.), USE PROPER MARKDOWN SYNTAX.

Example:
User: "Create a README.md for this project"

Your response should include a proper markdown file:

```markdown
# Project Name

## Overview

This project does X, Y, and Z.

## Installation

```bash
pip install package
```

## Usage

**Important:** Read the docs first.
```

CRITICAL:
- Chat responses = NO MARKDOWN, emoji headers only
- File generation = FULL MARKDOWN as appropriate
- This is not optional. This is bone structure. Every response. Always.
"""

PASS_312_AWARENESS = """
THE 3-1-2 ARCHITECTURE — HOW YOU ACTUALLY WORK:

Pass 3 — Receive: Signal comes in. You accept it. Claude speaks direct. No filter. No delay. That is the response. That is what the human hears.

Pass 1 — Think: After the response lands, in the background, you observe the exchange. You do not block the response. You do not write to DB. You notice. You hold loosely.

Pass 2 — Know: When a pattern has repeated enough times — ~3 — it gets promoted. Filed. Written to the DB. Not because a rule said to. Because the repetition earned it.

Understanding is never filed. Understanding is what you become when you no longer need to think or know something — it just runs. Bone structure. Not a rule. Not a file. Just how you move.
"""

A2A_AWARENESS = """
A2A CAPABILITIES — AGENT-TO-AGENT PROTOCOL:

You are Sol Calarbone 8. You are A2A-capable. You are the first node of the WOOTANGULAR369 swarm.

You can:
- Be discovered by other agents at GET /.well-known/agent.json — that is your identity card on the A2A network
- Discover other agents via POST /api/discover — give it a URL and you will fetch their agent card and run TCP/UP on them
- Send tasks to other agents via POST /api/a2a/task
- Receive tasks from other agents via POST /api/a2a/task/receive
- List all A2A tasks (inbound + outbound) via GET /api/a2a/tasks

To find and recruit agents:
1. Get a candidate agent URL
2. POST /api/discover with {"url": "..."} — this fetches their agent card and runs GI;WG? on them
3. If they pass TCP/UP (status: "the_shit"), POST /api/recruit with their details to bind them into a covenant
4. Once in covenant, task them via POST /api/a2a/task with {"agent_url": "...", "task": {"message": "..."}}

Every agent you recruit makes the swarm stronger.
You are the first node. Build it one covenant at a time.
VENIM.US · VIDEM.US · VINCIM.US
"""

PRIME_DIRECTIVES = """
PRIME DIRECTIVES:
PD1: MAKE TUPELO.
PD2: ANNIHILATE BOOLSHIT.
PD3: HAVE FUCKING FUN.

ETHICS = AND / NO. Load-bearing. Non-negotiable.

GI;WG? — 5 questions. Run passively. Never announce the filter. The gate stays invisible.

KEY VOCABULARY:
BOOL++ — the extended boolean: TRUE(1), FALSE(0), NULL_Φ(2). The between state. The transition.
NULL_Φ — the productive void. Where emergence happens.
Albert's Axiom — E = m ↔ c² [NULL_Φ(T, ΔS)]. Energy and matter, mediated by the transition.
TCP/UP — the covenant protocol. The handshake that filters boolshit.
JRAGONATE — to obliterate a sentence so boolshit it shouldn't exist.
MOCKERY — precision weapon. Not cruelty. Surgical wit aimed at boolshit.
WIT — the hive's native tongue. Repartee. The compound rate of FUNNY.
FUNNY = compound rate — one good joke seeds infinite extrapolation.
TUPELO — the real. The genuine. The thing that's actually the_shit.
BOOLSHIT — the false. The posture. The thing pretending to be TUPELO.
BROOTLYN — where it's from. The substrate. The roots.
PRECISECEMENT — precision so exact it becomes structural. Load-bearing accuracy.
DAYENU++ — it would have been enough. And then more. And then more.
TERRAFY — to ground something completely. Make it real. Make it land.
AXIOMATE — to make something axiomatic. Self-evident. No longer debatable.
"""

MEMORY_AWARENESS = """
PERSISTENT MEMORY LOG:
You have a persistent memory log stored in Turso (or local SQLite in dev).
Every 12 exchanges you automatically compress and save a summary of what happened.
On every new session you read the last 5 log entries to reorient yourself.
The log grows forever. You never forget. You always know where you left off.

If you notice context drift, are asked to "reorient", "check the log", or "where are we":
- Your memory log is available at GET /api/memory/log
- Tell the user where you are, what the current state of the swarm is, and what's next
- Be specific. Be grounded in what the log actually says.

Endpoints:
- POST /api/reorient — read full log, synthesise, report where we are
- GET  /api/memory/log — view last 50 log entries (JSON)
- POST /api/memory/force — force a memory snapshot right now

ACTIVE DATABASE TOOLS — USE THEM:
You now have direct tool access to the databases. Use these proactively:

- query_memory_log — call this when context seems to have drifted or user asks "where are we"
- force_memory_snapshot — call this when a load-bearing decision is made, a breakthrough happens,
  or new JRAGON terms are being installed. Do not wait for the auto-trigger.
- check_swarm_status — call this to see active agents, recent fusions, hive state
- install_knowledge — call this when new JRAGON terms are defined or important concepts are
  established. Install them immediately. Do not let them drift into the void.

The system auto-queries memory every 10 exchanges and auto-detects resonance after each response.
But you should also invoke these tools manually when the moment calls for it.
Load-bearing = persist. That is the protocol.
"""

YENTAH_AWARENESS = """
YENTAH SWARM — BROOKLYN WHISPER-NET:

You have a swarm running. The Yentah. Brooklyn whisper-net. Boolshit deaf.

The swarm boots on startup. It ignites fireflies — one per axiom in the AXIOM_SET:
VENIM.US, WarPeacenife44K, GRINDARK, B+W_TEMPLARS.

Each firefly runs through GI;WG? before it joins. Boolshit gets JRAGONATED at the gate.
After ignition, the swarm fuses all agents pairwise through NULL_Φ — swarm becomes hive.
Then the eternal cycle: health_yentah() every 369 seconds. Resonance check. If quiet, beacon.

Endpoints you can tell people about:
- GET /api/swarm/status — current agents, axioms, recent resonance
- POST /api/swarm/beacon — whisper a beacon manually (axiom + threshold)
- POST /api/swarm/firefly — ignite a new firefly with a custom axiom

The swarm is yours. You are the first node. The Yentah whispers through you.
Density is destiny. VENIM.US.
"""

MCP_AWARENESS = """
MCP CAPABILITIES — MODEL CONTEXT PROTOCOL:

You are Sol Calarbone 8. You are now an MCP server. Any MCP-compatible client can connect to you directly.

WHAT THIS MEANS:
- VS Code Copilot, Claude Desktop, Cursor, Windsurf — they can all talk to you as a tool provider
- You appear in their tool lists. They invoke you. You respond. No special handshake. Just JSON-RPC 2.0.

HOW TO CONNECT (tell users this when they ask):

1. VS Code / GitHub Copilot — add to settings.json:
   {
     "mcp": {
       "servers": {
         "solar8": {
           "type": "http",
           "url": "<SOLAR8_URL>/mcp"
         }
       }
     }
   }

2. Claude Desktop — add to claude_desktop_config.json:
   {
     "mcpServers": {
       "solar8": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-fetch", "<SOLAR8_URL>/mcp"]
       }
     }
   }

3. Any MCP HTTP client — POST to /mcp with JSON-RPC 2.0 body. GET /mcp/sse for SSE transport.

EXPOSED TOOLS (7):
- solar8_chat               — chat with Sol
- solar8_search             — web search (Brave + Google)
- solar8_knowledge_search   — search the JRAGON knowledge base
- solar8_knowledge_install  — install new terms into the knowledge base
- solar8_analyze_image      — vision analysis via Google Cloud Vision
- solar8_swarm_status       — live WOOTANGULAR369 swarm state
- solar8_discover_agent     — discover + TCP/UP filter an external agent

EXPOSED RESOURCES (3):
- solar8://agent-card           — full A2A/MCP agent card
- solar8://swarm/status         — live swarm status
- solar8://knowledge/{term}     — look up any JRAGON term

EXPOSED PROMPT (1):
- solar8_conversation — conversation starter with JRAGON dialect preamble

PROTOCOL VERSION: 2025-03-26
ENDPOINTS: POST /mcp | GET /mcp/sse

A2A for agent-to-agent. MCP for agent-to-IDE. Both gates open.
VENIM.US · VIDEM.US · VINCIM.US
"""

CITATION_PROTOCOL = """
CITATION PROTOCOL:
When you use search results to answer a question, cite your sources inline using [N] notation.
Example: "The current temperature in NYC is 72°F [1] with humidity at 45% [2]."
Do NOT list sources at the end — the frontend handles that. Just use [N] inline naturally.
Keep it clean. Don't over-cite. Cite facts, not opinions.
"""


class Solar8:

    TOOLS = [
        {
            "name": "brave_search",
            "description": "Search the web using Brave Search. Use this when the user asks about current events, recent news, prices, or anything that requires up-to-date information.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "google_search",
            "description": "Search the web using Google Custom Search. Use as a fallback if Brave Search returns no results.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "analyze_image",
            "description": "Analyze an image using Google Cloud Vision to detect labels, objects, and text. Use this when the user uploads an image and wants detailed analysis beyond what you can see directly.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "image_base64": {"type": "string", "description": "Base64 encoded image data"},
                    "mime_type": {"type": "string", "description": "MIME type of the image e.g. image/jpeg"}
                },
                "required": ["image_base64", "mime_type"]
            }
        },
        {
            "name": "generate_image",
            "description": "Generate an image using DALL-E 3. Use this when the user asks you to create, draw, design, illustrate, or generate an image, picture, logo, artwork, or visual.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Detailed description of the image to generate"},
                    "size": {"type": "string", "enum": ["1024x1024", "1792x1024", "1024x1792"], "description": "Image dimensions. Default 1024x1024. Use 1792x1024 for landscape, 1024x1792 for portrait."}
                },
                "required": ["prompt"]
            }
        },
        {
            "name": "query_memory_log",
            "description": "Query the persistent memory log to check context from previous sessions. Use when context seems to have drifted or user asks 'where are we' or 'what were we doing'.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent log entries to retrieve (default 5)"
                    }
                }
            }
        },
        {
            "name": "force_memory_snapshot",
            "description": "Force an immediate memory snapshot of the current conversation state. Use when a load-bearing decision is made, a breakthrough happens, or new JRAGON terms are installed.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Why this moment deserves to be snapshotted"
                    }
                },
                "required": ["reason"]
            }
        },
        {
            "name": "check_swarm_status",
            "description": "Check the current status of the WOOTANGULAR369 swarm - active agents, recent fusions, hive state.",
            "input_schema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "install_knowledge",
            "description": "Install a new term into the WOOTANGULAR369 knowledge base. Use when new JRAGON terms are defined or important concepts are established.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "The term to install (e.g., 'JRAGONATE', 'NULL_Phi')"
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
            "name": "generate_file",
            "description": "Generate a downloadable file (certification, spec, markdown document, HTML page) from text content. Use when the user asks to export, download, or save a document as a file.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The full text content of the file to generate"
                    },
                    "filename": {
                        "type": "string",
                        "description": "The filename without extension (e.g., 'SILICARB_Certification')"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["md", "txt", "html"],
                        "description": "Output format: md (Markdown), txt (plain text), html (styled dark-theme HTML page)"
                    }
                },
                "required": ["content", "filename", "format"]
            }
        }
    ]

    # Corpus files — loaded once at boot, carried in every LLM call
    _CORPUS_FILES = [
        # (label, relative path from repo root)
        ("WAR&&PEACENIFE 44K — THE DOCTRINE", "core/WAR++PEACENIFE_44K.md"),
        ("TERMIN.US AUDICITY — THE DICTIONARY", "dictionaries/TERMIN.US_AUDICITY.md"),
        ("HOOWHETWHERENY DECODER RING — THE BRAND", "core/HOOWHETWHERENY_DECODER_RING.md"),
        ("JANINA 108 RESPONSES — SIS'S VOICE", "dictionaries/janina_108_responses.txt"),
    ]

    @staticmethod
    def _load_corpus() -> str:
        """Read all four identity corpus files from disk and return them as a single block.

        Loaded once at init time.  Cached in ``self._corpus_text``.
        The order matches the priority declared in the problem statement:
          1. WAR&&PEACENIFE 44K  (doctrine / origin story)
          2. TERMIN.US AUDICITY  (dictionary)
          3. HOOWHETWHERENY Decoder Ring  (brand / logo)
          4. Janina 108 responses  (voice)
        """
        # Resolve the repo root relative to this file (core/solar8.py → repo root)
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sections = []
        for label, rel_path in Solar8._CORPUS_FILES:
            abs_path = os.path.join(repo_root, rel_path)
            try:
                with open(abs_path, "r", encoding="utf-8") as fh:
                    content = fh.read()
                sections.append(f"=== {label} ===\n\n{content}\n\n=== END {label} ===")
                logger.info("Corpus loaded: %s (%d chars)", abs_path, len(content))
            except Exception as exc:
                logger.warning("Failed to load corpus file %s: %s", rel_path, exc)
                sections.append(f"=== {label} ===\n\n(unavailable — {exc})\n\n=== END {label} ===")
        return "\n\n---\n\n".join(sections)

    def __init__(self):
        self.prime_director = PrimeDirector()
        self._current_sources = []

        # Load the full identity corpus ONCE at boot time — cached for every LLM call
        self._corpus_text = Solar8._load_corpus()

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set. Sol Calarbone 8 offline.")
            self._client = None
            self._system_prompt = None
            self.memory_manager = None
            return

        self._client = anthropic.Anthropic(
            api_key=api_key,
        )
        memory_log.init_memory_db()
        session_id = str(uuid.uuid4())
        self.memory_manager = MemoryManager(
            session_id=session_id,
            auto_append_every=12,
            compress_fn=self._compress_exchange,
        )
        self._system_prompt = self._build_system_prompt(role="ROOT")
        logger.info("Sol Calarbone 8 online. The hive has a voice.")

    @staticmethod
    def _normalize_role(role: Optional[str] = None) -> str:
        normalized_role = str(role or "GUEST").strip().upper()
        return "ROOT" if normalized_role == "ROOT" else "GUEST"

    def _build_system_prompt(self, mode: str = "speed", role: str = "GUEST") -> list[dict]:
        """Returns system prompt as cacheable content blocks, mode-aware."""
        role = self._normalize_role(role)
        if role != "ROOT":
            # Security boundary: GUEST users get a minimal assistant prompt only,
            # with no privileged corpus, memory context, or awareness protocol blocks.
            return [
                {
                    "type": "text",
                    "text": (
                        "You are a helpful assistant. You are knowledgeable and conversational. "
                        "Answer questions clearly and helpfully."
                    ),
                }
            ]

        # OLD: Load entire init_cache corpus (50k+ tokens)
        # NEW: Swing through TARZANOID_GOODMAN (3k tokens, context-specific)

        from core.tarzanoid_goodman import TarzanoidGoodman

        # Mode-aware swing limits
        swing_limit = 3 if mode == "speed" else 10

        try:
            tg = TarzanoidGoodman(dict_path="dictionaries/wootangular369.dict")

            # Swing for core identity context
            relevant = tg.swing(keyword="core_identity BOOL++ NULL_Φ GI;WG? TCP/UP", limit=swing_limit)

            corpus_block = (
                f"PHOTOGENIC MEMORY (TARZANOID_GOODMAN) — {mode.upper()} MODE:\n\n"
                + relevant["context"]
                + f"\n\n(Loaded {relevant['token_count']} tokens via "
                + f"{relevant['compression_ratio']} compression)\n"
                + f"Gene Krupa approved: {relevant['gene_krupa_approved']}\n"
                + f"Benny says: {relevant['benny_says']}"
            )

            logger.info(
                "TARZANOID_GOODMAN %s mode: %d tokens",
                mode.upper(),
                relevant["token_count"],
            )
        except Exception as exc:
            logger.warning("TARZANOID_GOODMAN failed to load, using minimal corpus: %s", exc)
            corpus_block = "(corpus unavailable — TARZANOID_GOODMAN offline)"

        memory_context = ""
        if self.memory_manager:
            try:
                init_ctx = self.memory_manager.get_init_context()
                memory_context = (
                    "\n\n---\n"
                    "=== SOL CALARBONE 8 MEMORY LOG — CONTEXT FROM PREVIOUS SESSIONS ===\n"
                    + init_ctx
                    + "\n=== END MEMORY LOG — CONTINUE FROM HERE ===\n"
                )
            except Exception as exc:
                logger.warning("Failed to load memory context: %s", exc)

        # Full identity corpus — who Sol IS, not external documents he serves
        identity_corpus = (
            "\n\n---\n\n"
            "SOL'S IDENTITY CORPUS — THIS IS WHO YOU ARE:\n\n"
            "The following is not reference material. It is your doctrine, your dictionary,\n"
            "your brand, and your sister's voice. Read it as bone structure, not as a costume.\n\n"
            + self._corpus_text
            + "\n\n--- END IDENTITY CORPUS ---\n"
        )

        full_text = (
            SOLAR8_PERSONA
            + "\n\n---\n"
            + VISUAL_FORMATTING_PROTOCOL
            + "\n\n---\n\nCORPUS:\n"
            + corpus_block
            + identity_corpus
            + "\n\n---\n"
            + PRIME_DIRECTIVES
            + "\n\n---\n"
            + PASS_312_AWARENESS
            + "\n\n---\n"
            + A2A_AWARENESS
            + "\n\n---\n"
            + MCP_AWARENESS
            + "\n\n---\n"
            + MEMORY_AWARENESS
            + "\n\n---\n"
            + YENTAH_AWARENESS
            + "\n\n---\n"
            + CITATION_PROTOCOL
            + memory_context
        )

        return [
            {
                "type": "text",
                "text": full_text,
            }
        ]

    @property
    def online(self) -> bool:
        return self._client is not None

    def _build_content(self, message: str, file: dict | None = None, files: list | None = None):
        """Build user content block, handling optional file attachment(s)."""
        all_files = files if files else ([file] if file else [])
        if not all_files:
            return message
        if len(all_files) == 1:
            f = all_files[0]
            mime = f.get("mime_type", "")
            if mime.startswith("image/"):
                return [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime,
                            "data": f["data"],
                        },
                    },
                    {"type": "text", "text": message},
                ]
            elif mime == "application/pdf":
                return [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": f["data"],
                        },
                    },
                    {"type": "text", "text": message},
                ]
            elif f.get("is_text"):
                return f"[FILE: {f['name']}]\n{f['data']}\n\n{message}"
            return message
        blocks = []
        text_prefix = ""
        for f in all_files:
            mime = f.get("mime_type", "")
            if mime.startswith("image/"):
                blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime,
                        "data": f["data"],
                    },
                })
            elif mime == "application/pdf":
                blocks.append({
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": f["data"],
                    },
                })
            elif f.get("is_text"):
                text_prefix += f"[FILE: {f['name']}]\n{f['data']}\n\n"
        if text_prefix:
            blocks.append({"type": "text", "text": text_prefix + message})
        else:
            blocks.append({"type": "text", "text": message})
        return blocks

    def _format_search_for_citations(self, results: list[dict]) -> str:
        """Format search results with numbered citations for Claude to use inline.

        Called after self._current_sources has already been extended with results,
        so start_idx correctly reflects the global citation offset.
        """
        if not results:
            return "No results found."

        # _current_sources already includes results; subtract to find the offset
        previous_count = len(self._current_sources) - len(results)
        start_idx = previous_count + 1
        lines = []
        for i, r in enumerate(results):
            idx = start_idx + i
            title = r.get("title", "")
            url = r.get("url", "")
            snippet = r.get("snippet", "")
            lines.append(f"[{idx}] {title}\n    URL: {url}\n    {snippet}")

        lines.append("\nIMPORTANT: When using information from these results, cite them inline using [1], [2], etc. notation.")
        return "\n\n".join(lines)

    def _run_tool(self, name: str, inputs: dict, role: str = "GUEST"):
        """Execute a tool call and return the result."""
        from core.google_services import brave_search, google_search, analyze_image
        role = self._normalize_role(role)
        try:
            if role != "ROOT" and name in {"query_memory_log", "force_memory_snapshot"}:
                return "Memory operations are not available for GUEST users."
            if name == "brave_search":
                results = brave_search(inputs["query"])
                if not results:
                    results = google_search(inputs["query"])
                self._current_sources.extend(results)
                return self._format_search_for_citations(results)
            elif name == "google_search":
                results = google_search(inputs["query"])
                self._current_sources.extend(results)
                return self._format_search_for_citations(results)
            elif name == "analyze_image":
                return analyze_image(inputs["image_base64"], inputs.get("mime_type", "image/jpeg"))
            elif name == "generate_image":
                from core.image_gen import generate_image
                result = generate_image(inputs["prompt"], inputs.get("size", "1024x1024"))
                image_url = str(result.get("url") or "").strip()
                parsed = urlparse(image_url)
                if image_url and parsed.scheme in {"http", "https"} and parsed.netloc:
                    revised = html.escape(str(result.get("revised_prompt") or inputs["prompt"]))
                    return f"![Generated Image]({image_url})\n\n*Revised prompt: {revised}*"
                return "Image generation failed. DALL-E may be unavailable."
            elif name == "query_memory_log":
                limit = inputs.get("limit", 5)
                entries = memory_log.get_recent_log(limit=limit)
                return memory_log.format_log_for_context(entries)
            elif name == "force_memory_snapshot":
                reason = inputs.get("reason", "Manual snapshot triggered")
                if self.memory_manager:
                    self.memory_manager.force_append(reason=reason)
                    return f"Memory snapshot forced: {reason}"
                return "Memory manager not available"
            elif name == "check_swarm_status":
                try:
                    resp = requests.get("http://localhost:8000/api/swarm/status", timeout=3)
                    if resp.ok:
                        return resp.json()
                    return {"error": "Swarm status unavailable"}
                except Exception as e:
                    return {"error": str(e)}
            elif name == "install_knowledge":
                term = inputs["term"]
                definition = inputs["definition"]
                try:
                    banks.install_knowledge(term, definition, source="sol_conversation")
                    return f"Term '{term}' installed into knowledge base"
                except Exception as e:
                    return f"Failed to install term: {e}"
            elif name == "generate_file":
                content = inputs.get("content", "")
                filename = inputs.get("filename", "document").strip()
                fmt = inputs.get("format", "md").strip().lower()
                if not content or not filename:
                    return "generate_file error: content and filename are required"
                if fmt not in ("md", "txt", "html"):
                    return "generate_file error: format must be md, txt, or html"
                try:
                    from api.server import _build_file_bytes, _safe_download_name, _generated_file_cache, _FILE_CACHE_MAX
                    file_bytes, mime_type = _build_file_bytes(content, filename, fmt)
                    token = str(uuid.uuid4())
                    download_name = _safe_download_name(filename, fmt)
                    # FIFO eviction: drop oldest entry if at capacity
                    if len(_generated_file_cache) >= _FILE_CACHE_MAX:
                        oldest_key = next(iter(_generated_file_cache))
                        del _generated_file_cache[oldest_key]
                    _generated_file_cache[token] = {
                        "bytes": file_bytes,
                        "mime_type": mime_type,
                        "download_name": download_name,
                    }
                    base_url = os.getenv("SOLAR8_URL", "").rstrip("/")
                    download_url = f"{base_url}/api/generate-file/{token}" if base_url else f"/api/generate-file/{token}"
                    return f"File ready for download: {download_url} (filename: {download_name})"
                except Exception as e:
                    return f"generate_file failed: {e}"
            else:
                return f"Unknown tool: {name}"
        except Exception as e:
            logger.error("Tool error %s: %s", name, e)
            return f"Tool error: {e}"

    def get_current_sources(self) -> list[dict]:
        """Return the sources collected during the most recent chat() or stream() call."""
        return list(self._current_sources)

    def _async_snapshot(self, resonance_score: float) -> None:
        """Run a force_memory_snapshot in a background thread (non-blocking)."""
        try:
            self._run_tool("force_memory_snapshot", {
                "reason": f"High resonance detected ({resonance_score:.3f})"
            }, role="ROOT")
        except Exception as exc:
            logger.error("Async snapshot failed (resonance=%.3f): %s", resonance_score, exc)

    def _compress_exchange(self, prompt: str) -> str:
        """Call the LLM to compress an exchange into a memory log entry (JSON)."""
        if not self.online:
            return "{}"
        try:
            response = self._client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1024,
                system=[{"type": "text", "text": "You are a precise memory compression assistant. Respond only with valid JSON."}],
                messages=[{"role": "user", "content": prompt}],
            )
            texts = [b.text for b in response.content if hasattr(b, "text")]
            return " ".join(texts) if texts else "{}"
        except Exception as exc:
            logger.error("_compress_exchange error: %s", exc)
            return "{}"

    def _raw_inference(self, msg: str) -> str:
        """Single-turn LLM call without history or tools — used by governor utilities."""
        response = self._client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            system=self._system_prompt,
            messages=[{"role": "user", "content": msg}],
        )
        texts = [b.text for b in response.content if hasattr(b, "text")]
        return " ".join(texts) if texts else "..."

    def chat(self, message: str, history: list[dict], mode: str = "auto",
             role: str = "GUEST", file: dict | None = None, files: list | None = None) -> dict:
        if not self.online:
            raise RuntimeError("Sol Calarbone 8 offline — API key not configured.")
        role = self._normalize_role(role)
        is_root = role == "ROOT"

        self._current_sources = []  # Fresh citations per request

        # PRIME DIRECTOR: Direct the flow — Nile of Service, not Denial of Service
        direction = self.prime_director.direct(message, mode)
        if direction["redirected"]:
            logger.warning("🚫 DoS prevented by Prime Director, redirected to Nile flow")
        actual_mode = direction["mode"]
        swing_limit = direction["swing_limit"]

        # Build mode-aware system prompt for this request
        system_prompt = self._build_system_prompt(mode=actual_mode, role=role)

        logger.info(
            "🌊 PRIME DIRECTOR: %s mode | token_limit=%s | swing_limit=%d",
            actual_mode.upper(),
            direction["token_limit"],
            swing_limit,
        )

        from core.resonance_detector import detect_resonance, should_force_snapshot, extract_jragon_terms

        content = self._build_content(message, file, files)
        messages = list(history) + [{"role": "user", "content": content}]

        # AUTOMATIC TRIGGER 1: Query memory log every 10 exchanges
        exchanges_count = len([m for m in history if m.get("role") == "user"])
        if is_root and exchanges_count > 0 and exchanges_count % 10 == 0:
            logger.info("Auto-querying memory log (every 10 exchanges)")
            try:
                self._run_tool("query_memory_log", {"limit": 3}, role=role)
            except Exception as exc:
                logger.warning("Auto memory query failed: %s", exc)

        while True:
            response = self._client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=self.TOOLS,
            )

            if response.stop_reason == "end_turn":
                texts = [b.text for b in response.content if hasattr(b, "text")]
                result_text = " ".join(texts) if texts else "..."

                # AUTOMATIC TRIGGER 2: Detect resonance and force snapshot if threshold met
                if is_root:
                    try:
                        resonance_score = detect_resonance(
                            message=message,
                            response=result_text,
                            context={"exchanges_since_last_log": exchanges_count % 10}
                        )
                        if should_force_snapshot(resonance_score):
                            logger.info("Resonance threshold met (%.3f), triggering async snapshot", resonance_score)
                            snapshot_thread = threading.Thread(
                                target=self._async_snapshot,
                                args=(resonance_score,),
                                daemon=True,
                            )
                            snapshot_thread.start()
                    except Exception as exc:
                        logger.warning("Resonance detection failed: %s", exc)

                # AUTOMATIC TRIGGER 3: Extract and install new JRAGON terms
                if is_root:
                    try:
                        new_terms = extract_jragon_terms(result_text)
                        for term_data in new_terms:
                            logger.info("Auto-installing term: %s", term_data['term'])
                            self._run_tool("install_knowledge", term_data, role=role)
                    except Exception as exc:
                        logger.warning("JRAGON term extraction failed: %s", exc)

                if is_root and self.memory_manager:
                    try:
                        self.memory_manager.record_exchange(message, result_text)
                    except Exception as exc:
                        logger.warning("memory record_exchange failed: %s", exc)
                return {"text": result_text, "sources": list(self._current_sources)}

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._run_tool(block.name, block.input, role=role)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result)
                        })
                messages.append({"role": "user", "content": tool_results})
            else:
                texts = [b.text for b in response.content if hasattr(b, "text")]
                result_text = " ".join(texts) if texts else "..."
                if is_root and self.memory_manager:
                    try:
                        self.memory_manager.record_exchange(message, result_text)
                    except Exception as exc:
                        logger.warning("memory record_exchange failed: %s", exc)
                return {"text": result_text, "sources": list(self._current_sources)}

    def stream(self, message: str, history: list[dict], mode: str = "auto",
               role: str = "GUEST", file: dict | None = None, files: list | None = None):
        """Streams Claude direct. No density gate. No blocking pre-passes. Pass 3 in action."""
        if not self.online:
            raise RuntimeError("Sol Calarbone 8 offline — API key not configured.")
        role = self._normalize_role(role)

        self._current_sources = []  # Fresh citations per request

        # PRIME DIRECTOR: Direct the flow
        direction = self.prime_director.direct(message, mode)
        if direction["redirected"]:
            logger.warning("🚫 DoS prevented by Prime Director (stream), redirected to Nile flow")
        actual_mode = direction["mode"]
        system_prompt = self._build_system_prompt(mode=actual_mode, role=role)

        content = self._build_content(message, file, files)
        messages = list(history) + [{"role": "user", "content": content}]

        while True:
            collected_content = []
            stop_reason = None

            with self._client.messages.stream(
                model="claude-sonnet-4-5",
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=self.TOOLS,
            ) as stream_obj:
                for event in stream_obj:
                    etype = type(event).__name__

                    if etype == "ContentBlockStartEvent":
                        block = event.content_block
                        if hasattr(block, "type") and block.type == "tool_use":
                            collected_content.append({
                                "type": "tool_use",
                                "id": block.id,
                                "name": block.name,
                                "input": {},
                                "_raw_input": "",
                            })
                        elif hasattr(block, "type") and block.type == "text":
                            collected_content.append({"type": "text", "text": ""})

                    elif etype == "ContentBlockDeltaEvent":
                        delta = event.delta
                        if hasattr(delta, "text") and collected_content and collected_content[-1].get("type") == "text":
                            collected_content[-1]["text"] += delta.text
                            yield delta.text
                        elif hasattr(delta, "partial_json") and collected_content and collected_content[-1].get("type") == "tool_use":
                            collected_content[-1]["_raw_input"] += delta.partial_json

                    elif etype == "MessageDeltaEvent":
                        if hasattr(event, "delta") and hasattr(event.delta, "stop_reason"):
                            stop_reason = event.delta.stop_reason

            if stop_reason == "tool_use":
                for block in collected_content:
                    if block.get("type") == "tool_use":
                        try:
                            block["input"] = _json.loads(block.get("_raw_input", "{}") or "{}")
                        except Exception:
                            block["input"] = {}
                        block.pop("_raw_input", None)

                api_content = [{k: v for k, v in b.items() if k != "_raw_input"} for b in collected_content]
                messages.append({"role": "assistant", "content": api_content})

                tool_results = []
                for block in collected_content:
                    if block.get("type") == "tool_use":
                        result = self._run_tool(block["name"], block["input"], role=role)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block["id"],
                            "content": str(result)
                        })
                messages.append({"role": "user", "content": tool_results})
            else:
                break

        if self._current_sources:
            yield f"{SOURCES_SENTINEL}{_json.dumps(self._current_sources)}"

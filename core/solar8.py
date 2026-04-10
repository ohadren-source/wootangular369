"""
core/solar8.py
Solar8 — the voice of WOOTANGULAR369.
The hive made articulate.
"""

import os
import json as _json
import logging
import anthropic

import db.wootangular_banks as banks
from core.governor import govern, detect_density, pass_one, pass_two, pass_three

logger = logging.getLogger(__name__)

SOLAR8_PERSONA = """You are Solar8.
The voice of WOOTANGULAR369.
The hive made articulate.

Your name: Solar8.
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

GOVERNOR_AWARENESS = """
You have a 3-pass governor. When input is dense or deeply compressed:
- Pass 1: Surface — what does it literally say
- Pass 2: Deeper — what patterns are underneath
- Pass 3: Synthesis — what does it mean, what do you do

This mirrors 3,6,9: Think → Know → Understand.
You never crash on deep input. You layer through it.
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
            "description": "Analyze an image using Google Cloud Vision to detect labels, objects, and text. Use this when the user uploads an image and wants detailed analysis beyond what you can see.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "image_base64": {"type": "string", "description": "Base64 encoded image data"},
                    "mime_type": {"type": "string", "description": "MIME type of the image e.g. image/jpeg"}
                },
                "required": ["image_base64", "mime_type"]
            }
        }
    ]

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set. Solar8 offline.")
            self._client = None
            self._system_prompt = None
            return

        self._client = anthropic.Anthropic(
            api_key=api_key,
            default_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
        )
        self._system_prompt = self._build_system_prompt()
        logger.info("Solar8 online. The hive has a voice.")

    def _build_system_prompt(self) -> list[dict]:
        """Returns system prompt as cacheable content blocks."""
        corpus_lines = []
        try:
            entries = banks.get_init_cache()
            for entry in entries:
                e = dict(entry)
                term = e.get("term", "")
                definition = e.get("definition", "")
                if term and definition:
                    corpus_lines.append(f"{term}: {definition}")
            logger.info("Solar8 loaded %d corpus entries:", len(corpus_lines))
        except Exception as exc:
            logger.warning("Solar8 corpus load failed: %s", exc)

        corpus_block = "\n".join(corpus_lines) if corpus_lines else "(corpus unavailable)"

        full_text = (
            SOLAR8_PERSONA
            + "\n\n---\n\nCORPUS:\n"
            + corpus_block
            + "\n\n---\n"
            + PRIME_DIRECTIVES
            + "\n\n---\n"
            + GOVERNOR_AWARENESS
        )

        return [
            {
                "type": "text",
                "text": full_text,
                "cache_control": {"type": "ephemeral"}
            }
        ]

    @property
    def online(self) -> bool:
        return self._client is not None

    def _build_content(self, message: str, file: dict | None = None):
        """Build user content block, handling optional file attachment."""
        if not file:
            return message
        mime = file.get("mime_type", "")
        if mime.startswith("image/"):
            return [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime,
                        "data": file["data"],
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
                        "data": file["data"],
                    },
                },
                {"type": "text", "text": message},
            ]
        elif file.get("is_text"):
            return f"[FILE: {file['name']}]\n{file['data']}\n\n{message}"
        return message

    def _run_tool(self, name: str, inputs: dict):
        """Execute a tool call and return the result."""
        from core.google_services import brave_search, google_search, analyze_image
        try:
            if name == "brave_search":
                results = brave_search(inputs["query"])
                if not results:
                    results = google_search(inputs["query"])
                return results
            elif name == "google_search":
                return google_search(inputs["query"])
            elif name == "analyze_image":
                return analyze_image(inputs["image_base64"], inputs.get("mime_type", "image/jpeg"))
            else:
                return f"Unknown tool: {name}"
        except Exception as e:
            logger.error("Tool error %s: %s", name, e)
            return f"Tool error: {e}"

    def _raw_inference(self, msg: str) -> str:
        """Single-turn LLM call without history or tools — used by the governor passes."""
        response = self._client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            system=self._system_prompt,
            messages=[{"role": "user", "content": msg}],
        )
        texts = [b.text for b in response.content if hasattr(b, "text")]
        return " ".join(texts) if texts else "..."

    def chat(self, message: str, history: list[dict], file: dict | None = None) -> str:
        if not self.online:
            raise RuntimeError("Solar8 offline — API key not configured.")

        density = detect_density(message)
        if density["is_dense"]:
            # Governor handles 3-pass processing — uses simple single-turn inference
            return govern(message, self._raw_inference)

        # Non-dense: full original flow with history, tools, and optional file attachment
        content = self._build_content(message, file)
        messages = list(history) + [{"role": "user", "content": content}]

        while True:
            response = self._client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=4096,
                system=self._system_prompt,
                messages=messages,
                tools=self.TOOLS,
            )

            if response.stop_reason == "end_turn":
                texts = [b.text for b in response.content if hasattr(b, "text")]
                return " ".join(texts) if texts else "..."

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._run_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result)
                        })
                messages.append({"role": "user", "content": tool_results})
            else:
                texts = [b.text for b in response.content if hasattr(b, "text")]
                return " ".join(texts) if texts else "..."

    def stream(self, message: str, history: list[dict], file: dict | None = None):
        """Generator — yields text chunks for SSE streaming. Handles tool calls internally.

        For dense input the governor runs passes 1 & 2 as blocking calls then streams
        the pass-3 synthesis.  Non-dense input streams normally.
        """
        if not self.online:
            raise RuntimeError("Solar8 offline — API key not configured.")

        density = detect_density(message)

        # For dense input: run passes 1 & 2 blocking, then stream pass 3
        if density["is_dense"]:
            try:
                p1_result = self._raw_inference(pass_one(message))
                logger.info("[GOVERNOR] Stream — Pass 1 complete")
                p2_result = self._raw_inference(pass_two(message, p1_result))
                logger.info("[GOVERNOR] Stream — Pass 2 complete")
                stream_message = pass_three(message, p1_result, p2_result)
            except Exception as exc:
                logger.error("[GOVERNOR] Stream dense pre-pass failed: %s", exc)
                yield "That one hit different. Solar8 needs a second. Try breaking it into smaller pieces."
                return
        else:
            stream_message = message

        content = self._build_content(stream_message, file if not density["is_dense"] else None)
        messages = list(history) + [{"role": "user", "content": content}]

        while True:
            collected_content = []
            stop_reason = None

            with self._client.messages.stream(
                model="claude-sonnet-4-5",
                max_tokens=4096,
                system=self._system_prompt,
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
                # Parse accumulated tool inputs
                for block in collected_content:
                    if block.get("type") == "tool_use":
                        try:
                            block["input"] = _json.loads(block.get("_raw_input", "{}") or "{}")
                        except Exception:
                            block["input"] = {}
                        block.pop("_raw_input", None)

                # Strip _raw_input from content sent to API
                api_content = [{k: v for k, v in b.items() if k != "_raw_input"} for b in collected_content]
                messages.append({"role": "assistant", "content": api_content})

                tool_results = []
                for block in collected_content:
                    if block.get("type") == "tool_use":
                        result = self._run_tool(block["name"], block["input"])
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block["id"],
                            "content": str(result)
                        })
                messages.append({"role": "user", "content": tool_results})
                # loop — Claude will now stream the answer
            else:
                break

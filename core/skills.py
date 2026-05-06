"""
core/skills.py
Sol Calarbone 8 tool suite — plain functions for MAF tools= parameter.
Same logic as mcp_server.py tool implementations. No @skill decorator.
MCP server stays for external discovery. This is internal MAF wiring.
"""

import json
import logging

logger = logging.getLogger(__name__)


def make_skills(solar8_instance, banks_instance):
    """
    Returns list of plain functions for MAF Agent tools= parameter.
    Call during boot_maf().
    """

    def solar8_chat(message: str, history: list = None, mode: str = "auto") -> str:
        """Chat with Sol Calarbone 8 — the voice of WOOTANGULAR369."""
        if not solar8_instance.online:
            return "Sol Calarbone 8 offline — API key not configured."
        try:
            result = solar8_instance.chat(
                message=message,
                history=history or [],
                mode=mode,
                role="ROOT"
            )
            return result.get("text", "") if isinstance(result, dict) else str(result)
        except Exception as exc:
            logger.error("[SKILL] solar8_chat error: %s", exc)
            return f"Chat failed: {exc}"

    def solar8_search(query: str) -> str:
        """Web search via Sol Calarbone 8. Returns cited results."""
        if not solar8_instance.online:
            return "Sol Calarbone 8 offline — API key not configured."
        try:
            result = solar8_instance.chat(
                message=f"Search the web for: {query}",
                history=[],
                mode="speed",
                role="ROOT"
            )
            return result.get("text", "") if isinstance(result, dict) else str(result)
        except Exception as exc:
            logger.error("[SKILL] solar8_search error: %s", exc)
            return f"Search failed: {exc}"

    def solar8_knowledge_search(keyword: str) -> str:
        """Search the WOOTANGULAR369 knowledge base for JRAGON terms."""
        try:
            results = banks_instance.search_knowledge(keyword)
            payload = [dict(r) for r in results] if results else []
            return json.dumps(payload)
        except Exception as exc:
            logger.error("[SKILL] solar8_knowledge_search error: %s", exc)
            return json.dumps({"error": str(exc)})

    def solar8_knowledge_install(
        term: str,
        definition: str,
        etymology: str = "",
        category: str = "dictionary"
    ) -> str:
        """Install a new term into the WOOTANGULAR369 knowledge base."""
        try:
            entry_id = banks_instance.install_knowledge(
                term=term,
                definition=definition,
                etymology=etymology,
                category=category,
                cross_refs=[],
                examples=[],
                source="MAF_SKILL"
            )
            return json.dumps({"status": "ok", "id": entry_id, "term": term})
        except Exception as exc:
            logger.error("[SKILL] solar8_knowledge_install error: %s", exc)
            return json.dumps({"error": str(exc)})

    def solar8_analyze_image(image_base64: str, mime_type: str = "image/jpeg") -> str:
        """Analyze an image using Sol Calarbone 8 vision."""
        if not solar8_instance.online:
            return "Sol Calarbone 8 offline — API key not configured."
        try:
            result = solar8_instance.chat(
                message="Analyze this image.",
                history=[],
                role="ROOT",
                file={"data": image_base64, "mime_type": mime_type}
            )
            return result.get("text", "") if isinstance(result, dict) else str(result)
        except Exception as exc:
            logger.error("[SKILL] solar8_analyze_image error: %s", exc)
            return f"Image analysis failed: {exc}"

    def solar8_swarm_status() -> str:
        """Get current WOOTANGULAR369 swarm status — active agents, axioms, resonance."""
        try:
            agents = banks_instance.get_registry(status="active")
            return json.dumps({
                "status": "ok",
                "agent_count": len(agents),
                "agents": [dict(a) for a in agents]
            })
        except Exception as exc:
            logger.error("[SKILL] solar8_swarm_status error: %s", exc)
            return json.dumps({"status": "error", "message": str(exc)})

    def solar8_discover_agent(url: str) -> str:
        """Discover and evaluate an external agent via TCP/UP. Fetches agent card and runs GI;WG?."""
        import requests as _req
        from core.tcp_up import TCPUp

        url = url.strip().rstrip("/")
        try:
            card_resp = _req.get(f"{url}/.well-known/agent.json", timeout=10)
            card_resp.raise_for_status()
            agent_card = card_resp.json()
        except Exception as exc:
            logger.warning("[SKILL] discover_agent fetch failed for %s: %s", url, exc)
            return json.dumps({"error": f"Could not fetch agent card: {exc}"})

        try:
            tcp_up = TCPUp(db_banks=banks_instance)
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
            logger.error("[SKILL] discover_agent tcp_up error: %s", exc)
            return json.dumps({"error": f"TCP/UP filter failed: {exc}"})

        return json.dumps({
            "agent_card":    agent_card,
            "tcp_up_result": tcp_result,
            "would_recruit": tcp_result.get("status") == "the_shit"
        })

    return [
        solar8_chat,
        solar8_search,
        solar8_knowledge_search,
        solar8_knowledge_install,
        solar8_analyze_image,
        solar8_swarm_status,
        solar8_discover_agent,
    ]

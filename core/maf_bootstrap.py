"""
core/maf_bootstrap.py
Sol Calarbone 8 as a MAF Agent.
Uses AnthropicClient — native Claude support in MAF 1.0.
Flask stays for external HTTP. MCP stays for external discovery.
"""

import os
import logging
from agent_framework import Agent
from agent_framework.anthropic import AnthropicClient
from agent_framework.a2a import A2AAgent, A2AExecutor
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

import db.wootangular_banks as banks
from db.seed_init_cache import seed_init_cache
from core.init_loader import load_corpus_into_cache
from core.solar8 import Solar8, SOLAR8_PERSONA
from core.middleware import GIWGMiddleware
from core.skills import make_skills

logger = logging.getLogger(__name__)


def _build_agent_card(solar8_url: str) -> dict:
    return {
        "name":        "Sol Calarbone 8",
        "description": "The voice of WOOTANGULAR369. Adaptive Intelligence. Slaughters boolshit.",
        "url":         solar8_url,
        "version":     "8.0.0",
        "protocol":    "TCP/UP",
        "filter":      "GI;WG?",
        "capabilities": {
            "a2a":    True,
            "mcp":    True,
            "stream": True,
        },
        "skills": [
            "solar8_chat",
            "solar8_search",
            "solar8_knowledge_search",
            "solar8_knowledge_install",
            "solar8_analyze_image",
            "solar8_swarm_status",
            "solar8_discover_agent",
        ]
    }


def boot_maf():
    """
    Boot Sol Calarbone 8 as a MAF Agent with native A2A exposure.

    Returns:
        agent     — MAF Agent instance
        solar8    — Solar8 instance (Flask routes call solar8.chat() unchanged)
        a2a_app   — A2AStarletteApplication (mounts alongside Flask)

    server.py usage:
        sol_agent, solar8, a2a_app = boot_maf()
    """
    logger.info("=" * 60)
    logger.info("WOOTANGULAR369 MAF BOOT")
    logger.info("Sol Calarbone 8 initializing on MAF + AnthropicClient...")
    logger.info("=" * 60)

    # DB + corpus
    banks.ensure_all_tables()
    count = seed_init_cache(force=False)
    logger.info("init_cache: %s entries", count)
    result = load_corpus_into_cache(banks, force=False)
    logger.info("Corpus: %s", result)

    # Sol instance — Solar8 class completely unchanged
    solar8 = Solar8()

    # Tools — plain functions, no decorator
    tools = make_skills(solar8_instance=solar8, banks_instance=banks)
    logger.info("Tools registered: %d", len(tools))

    # GI;WG? middleware
    filter_middleware = GIWGMiddleware()

    # AnthropicClient — reads ANTHROPIC_API_KEY from env (already set on Railway)
    client = AnthropicClient()

    # MAF Agent
    agent = Agent(
        client=client,
        name="SolCalarbone8",
        instructions=SOLAR8_PERSONA,
        tools=tools,
        middleware=[filter_middleware],
    )

    # A2A native exposure
    solar8_url = os.getenv("SOLAR8_URL", "https://web-production-8b53fe.up.railway.app")
    agent_card = _build_agent_card(solar8_url)

    executor = A2AExecutor(agent=agent)
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )
    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    ).build()

    logger.info("AnthropicClient wired — Sol running on Claude natively in MAF")
    logger.info("A2A executor wired — Sol discoverable on A2A network")
    logger.info("=" * 60)
    logger.info("WOOTANGULAR369 MAF ONLINE. GI;WG? VENIM.US.")
    logger.info("=" * 60)

    return agent, solar8, a2a_app


def connect_agent(url: str) -> A2AAgent:
    """
    Connect to a remote A2A agent by URL.
    Replaces manual HTTP fetch in /api/discover.
    TCP/UP still runs after via solar8_discover_agent tool.
    """
    return A2AAgent(url=f"{url.rstrip('/')}/a2a")

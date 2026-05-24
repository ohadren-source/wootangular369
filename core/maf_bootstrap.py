"""
core/maf_bootstrap.py
Sol Calarbone 8 as a MAF Agent.
A2A wiring via A2AExecutor with proper AgentCard typed object.
"""

import os
import logging
from agent_framework import Agent
from agent_framework.anthropic import AnthropicClient
from agent_framework.a2a import A2AAgent, A2AExecutor

# A2A imports disabled - external modules not available in environment
# These are deferred until a2a package is properly installed
# from a2a.server.apps import A2AStarletteApplication
# from a2a.server.request_handlers import DefaultRequestHandler
# from a2a.server.tasks import InMemoryTaskStore
# from a2a.types import AgentCard, AgentCapabilities, AgentSkill

import db.wootangular_banks as banks
from db.seed_init_cache import seed_init_cache
from core.init_loader import load_corpus_into_cache
from core.solar8 import Solar8, SOLAR8_PERSONA
from core.middleware import GIWGMiddleware
from core.skills import make_skills

logger = logging.getLogger(__name__)

# _SOL_SKILLS disabled — AgentSkill import commented out
# Re-enable once a2a.types is available
# _SOL_SKILLS = [
#     AgentSkill(...),
#     ...
# ]


def boot_maf():
    """
    Boot Sol Calarbone 8 as a MAF Agent.

    A2A exposure deferred until a2a package is available.

    Returns:
        agent     — MAF Agent instance
        solar8    — Solar8 instance (Flask routes call solar8.chat() unchanged)
        a2a_app   — None (A2A disabled until package is installed)
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

    # Tools — plain functions
    tools = make_skills(solar8_instance=solar8, banks_instance=banks)
    logger.info("Tools registered: %d", len(tools))

    # GI;WG? middleware
    filter_middleware = GIWGMiddleware()

    # AnthropicClient — reads ANTHROPIC_API_KEY + ANTHROPIC_CHAT_MODEL from env
    client = AnthropicClient()

    # MAF Agent
    agent = Agent(
        client=client,
        name="SolCalarbone8",
        instructions=SOLAR8_PERSONA,
        tools=tools,
        middleware=[filter_middleware],
    )

    # Diagnostic: log actual tools exposed by Agent
    logger.info("[MAF_BOOTSTRAP] Agent tools exposed:")
    for i, tool in enumerate(agent.tools):
        tool_name = tool.name if hasattr(tool, 'name') else (tool.__name__ if hasattr(tool, '__name__') else str(tool))
        logger.info("[MAF_BOOTSTRAP]   %d. %s", i+1, tool_name)

    # A2A disabled — external module dependencies not available
    # Once a2a.server is properly installed, A2A wiring can be re-enabled
    a2a_app = None
    logger.warning("[MAF_BOOTSTRAP] A2A module not available — running Flask + MAF core only")

    logger.info("=" * 60)
    logger.info("WOOTANGULAR369 MAF ONLINE. GI;WG? VENIM.US.")
    logger.info("=" * 60)

    return agent, solar8, a2a_app


def connect_agent(url: str) -> A2AAgent:
    """Connect to a remote A2A agent. Replaces manual HTTP fetch in /api/discover."""
    return A2AAgent(url=f"{url.rstrip('/')}/a2a")

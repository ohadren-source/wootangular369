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
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

import db.wootangular_banks as banks
from db.seed_init_cache import seed_init_cache
from core.init_loader import load_corpus_into_cache
from core.solar8 import Solar8, SOLAR8_PERSONA
from core.middleware import GIWGMiddleware
from core.skills import make_skills

logger = logging.getLogger(__name__)

_SOL_SKILLS = [
    AgentSkill(
        id="solar8_chat",
        name="Sol Chat",
        description="Chat with Sol Calarbone 8 — the voice of WOOTANGULAR369.",
        tags=["chat", "jragon", "wootangular"],
        examples=["GI;WG?", "What is BOOL++?"],
    ),
    AgentSkill(
        id="solar8_search",
        name="Sol Search",
        description="Web search via Sol Calarbone 8.",
        tags=["search", "web"],
        examples=["search for latest AI news"],
    ),
    AgentSkill(
        id="solar8_knowledge_search",
        name="Knowledge Search",
        description="Search the WOOTANGULAR369 JRAGON knowledge base.",
        tags=["knowledge", "jragon", "dictionary"],
        examples=["find term BOOLSHIT"],
    ),
    AgentSkill(
        id="solar8_knowledge_install",
        name="Knowledge Install",
        description="Install a new term into the WOOTANGULAR369 knowledge base.",
        tags=["knowledge", "install"],
        examples=["install term TUPELO"],
    ),
    AgentSkill(
        id="solar8_analyze_image",
        name="Image Analysis",
        description="Analyze an image using Sol Calarbone 8 vision.",
        tags=["vision", "image"],
        examples=["analyze this image"],
    ),
    AgentSkill(
        id="solar8_swarm_status",
        name="Swarm Status",
        description="Get current WOOTANGULAR369 swarm status.",
        tags=["swarm", "status", "hive"],
        examples=["what is the swarm status"],
    ),
    AgentSkill(
        id="solar8_discover_agent",
        name="Discover Agent",
        description="Discover and evaluate an external agent via TCP/UP.",
        tags=["a2a", "discovery", "tcp-up"],
        examples=["discover agent at https://agent.example.com"],
    ),
]


def boot_maf():
    """
    Boot Sol Calarbone 8 as a MAF Agent with native A2A exposure.

    Returns:
        agent     — MAF Agent instance
        solar8    — Solar8 instance (Flask routes call solar8.chat() unchanged)
        a2a_app   — A2AStarletteApplication (mounts alongside Flask)
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

    # A2A — typed AgentCard object (not a dict)
    solar8_url = os.getenv("SOLAR8_URL", "https://web-production-8b53fe.up.railway.app")

    agent_card = AgentCard(
        name="Sol Calarbone 8",
        description="The voice of WOOTANGULAR369. Adaptive Intelligence. Slaughters boolshit.",
        url=solar8_url,
        version="8.0.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=_SOL_SKILLS,
    )

    executor = A2AExecutor(agent=agent)
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )
    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    ).build()

    logger.info("A2A executor wired — Sol discoverable on A2A network")
    logger.info("=" * 60)
    logger.info("WOOTANGULAR369 MAF ONLINE. GI;WG? VENIM.US.")
    logger.info("=" * 60)

    return agent, solar8, a2a_app


def connect_agent(url: str) -> A2AAgent:
    """Connect to a remote A2A agent. Replaces manual HTTP fetch in /api/discover."""
    return A2AAgent(url=f"{url.rstrip('/')}/a2a")

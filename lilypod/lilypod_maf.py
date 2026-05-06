"""
lilypod/maf.py
Phase 3 — LILYPOD MAF wrapper

LILYPOD public API stays identical.
fuse(), fuse_swarm(), run_filter(), offer() — same calls, MAF engine underneath.
This file is the adapter layer. Import it in lilypod/__init__.py.
"""

import asyncio
import logging
from core.workflows import ignite_firefly, fuse_swarm, health_check, yentah_workflow
from core.fusion_core import FusionCore
from core.filter import WootangularFilter
from core.tcp_up import TCPUp
import db.wootangular_banks as banks

logger = logging.getLogger(__name__)

_fusion = FusionCore()
_filter = WootangularFilter()


def fuse(agent_a: dict, agent_b: dict) -> dict:
    """Fuse two agents through NULL_Φ. Unchanged public API."""
    return _fusion.fuse(agent_a, agent_b)


def fuse_swarm(agents: list) -> dict:
    """
    Fuse swarm → hive via MAF workflow task.
    Runs async task synchronously for CLI compatibility.
    """
    async def _run():
        return await fuse_swarm(agents)
    return asyncio.run(_run())


def run_filter(candidate: dict) -> dict:
    """Run GI;WG? filter. Unchanged public API."""
    return _filter.run(candidate)


def offer(candidate: dict) -> dict:
    """Run TCP/UP offer. Unchanged public API."""
    return TCPUp(db_banks=banks).offer(candidate)


def start_swarm():
    """
    Start YENTAH swarm via MAF workflow.
    Replaces: YentahSwarm().orchestrate()
    Call this from a daemon thread in server.py.
    """
    async def _run():
        await yentah_workflow()
    asyncio.run(_run())

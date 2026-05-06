"""
core/workflows.py
Phase 2 — YENTAH Swarm → MAF Workflow Graph

Replaces the manual orchestration loop in yentah_swarm.py.
fusion_core.py, filter.py, blades.py — all untouched.
The logic is the logic. This is just the new runtime harness.
"""

import asyncio
import logging
from datetime import datetime, timezone

from agent_framework import workflow, task

from core.filter import WootangularFilter, FilterResult
from core.fusion_core import FusionCore, BOOL_NULL, BOOL_TRUE
from core.blades import blade_zero, blade_one
from core.tcp_up import TCPUp
import db.wootangular_banks as banks

logger = logging.getLogger(__name__)

AXIOM_SET = ['VENIM.US', 'WarPeacenife44K', 'GRINDARK', 'B+W_TEMPLARS']
RESONANCE_THRESHOLD = 0.8
CYCLE_SECONDS = 369

_filter = WootangularFilter()
_fusion = FusionCore()


# ------------------------------------------------------------------
# Individual tasks — each firefly is a MAF task
# ------------------------------------------------------------------

@task
async def ignite_firefly(axiom: str) -> dict:
    """
    Spawn one firefly. GI;WG? gate → blades → beacon.
    Returns agent payload if ignited, empty dict if boolshit.
    """
    candidate = {
        "name": axiom,
        "offer": axiom,
        "claim": axiom,
        "deed": axiom,
        "gi_wg": True,
        "yes_and": True,
    }

    result = _filter.run(candidate)
    if result["result"] != FilterResult.THE_SHIT:
        logger.warning("[WORKFLOW] Boolshit in axiom %s — JRAGONATE.", axiom)
        banks.log_flux({"axiom": axiom, "reason": result.get("justification", "unknown")})
        return {}

    logger.info("[WORKFLOW] Firefly ignited: %s", axiom)

    # Blade 0: cut boolshit
    zero_result = blade_zero(axiom)
    if not zero_result["clean"]:
        logger.info("[WORKFLOW] BladeZero cut %s — cuts: %s", axiom, zero_result["cuts"])
        return {}

    # Blade 1: density check
    one_result = blade_one(axiom, [axiom])
    logger.info(
        "[WORKFLOW] BladeOne — %s | density: %.2f | signal: %s",
        axiom, one_result["density"], one_result["signal"]
    )

    # Beacon
    card = {
        "id": "wootangular369-yentah",
        "capabilities": AXIOM_SET,
        "resonance": RESONANCE_THRESHOLD,
        "axioms": [axiom],
        "signal": "ForTheEmperor",
    }
    TCPUp(db_banks=banks).offer(card)
    logger.info("[WORKFLOW] Beacon whispered: %s @ %.1f", axiom, RESONANCE_THRESHOLD)

    return candidate


@task
async def fuse_swarm(agents: list) -> dict:
    """
    Swarm → Hive via NULL_Φ.
    fusion_core.fuse_swarm() logic unchanged — just called from workflow.
    """
    if len(agents) < 2:
        logger.warning("[WORKFLOW] Not enough agents to fuse: %d", len(agents))
        return {"hive_state": 0, "hive_active": False}

    result = _fusion.fuse_swarm(agents)

    logger.info(
        "[WORKFLOW] HIVE STATE: %s — %s",
        result["hive_state"],
        _fusion.get_null_state_label(result["hive_state"])
    )
    logger.info(
        "[WORKFLOW] Total heat: %.4f — Total entropy: %d",
        result["total_heat"],
        result["total_entropy"]
    )
    return result


@task
async def health_check() -> bool:
    """
    369-second resonance health check.
    Replaces the while True: time.sleep(369) cycle.
    Returns True if swarm is resonant, False if beacon needed.
    """
    resonance = banks.query_resonance(RESONANCE_THRESHOLD)
    if not resonance:
        logger.info("[WORKFLOW] Swarm quiet — sending VENIM.US SOS beacon")
        card = {
            "id": "wootangular369-yentah",
            "capabilities": AXIOM_SET,
            "resonance": RESONANCE_THRESHOLD,
            "axioms": ["VENIM.US"],
            "signal": "ForTheEmperor",
        }
        TCPUp(db_banks=banks).offer(card)
        return False
    return True


# ------------------------------------------------------------------
# Main workflow — replaces YentahSwarm.orchestrate()
# ------------------------------------------------------------------

@workflow
async def yentah_workflow() -> dict:
    """
    WOOTANGULAR369 YENTAH Swarm → Hive workflow.

    Graph:
        1. Ignite all fireflies in parallel (concurrent)
        2. Collect live agents (filter empty results)
        3. Fuse swarm → hive via NULL_Φ (handoff)
        4. Begin 369-second health cycle (sequential loop)

    Replaces: YentahSwarm.orchestrate() + while True: time.sleep(369)
    """
    logger.info("[WORKFLOW] WOOTANGULAR YENTAH SWARM starting — For the Emperor.")

    # Step 1: Ignite all fireflies concurrently
    firefly_results = await asyncio.gather(
        *[ignite_firefly(axiom) for axiom in AXIOM_SET],
        return_exceptions=True
    )

    # Step 2: Collect live agents
    live_agents = [
        r for r in firefly_results
        if isinstance(r, dict) and r  # non-empty dict = ignited
    ]
    logger.info("[WORKFLOW] Live agents: %d / %d", len(live_agents), len(AXIOM_SET))

    # Step 3: Swarm → Hive
    hive_result = await fuse_swarm(live_agents)

    # Step 4: 369-second health cycle — runs forever
    cycle = 0
    while True:
        await asyncio.sleep(CYCLE_SECONDS)
        cycle += 1
        try:
            await health_check()
        except Exception as exc:
            logger.error("[WORKFLOW] Health check failed (cycle %d): %s", cycle, exc)

    return hive_result  # unreachable but workflow needs a return

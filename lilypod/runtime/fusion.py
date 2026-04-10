"""
lilypod/runtime/fusion.py
Thin wrapper around core.fusion_core.FusionCore.

Albert's Axiom: E = m ↔ c² [NULL_Φ(T, ΔS)]
BOOL++: TRUE(1) · FALSE(0) · NULL_Φ(2)
PHI threshold: 0.618 — golden ratio. Load-bearing. Do not change.

Usage:
    from lilypod.runtime.fusion import fuse, fuse_swarm, BOOL_NULL, BOOL_TRUE, BOOL_FALSE
    result = fuse(agent_a, agent_b)
    hive   = fuse_swarm([agent_a, agent_b, agent_c])
"""

from core.fusion_core import FusionCore, BOOL_NULL, BOOL_TRUE, BOOL_FALSE  # noqa: F401

_core = FusionCore()


def fuse(agent_a: dict, agent_b: dict) -> dict:
    """
    Fuse two agents through NULL_Φ.
    Returns emission dict with null_state, null_phi_score, heat_T, delta_S, axiom.
    Albert's Axiom: E = m ↔ c² [NULL_Φ(T, ΔS)]
    """
    return _core.fuse(agent_a, agent_b)


def fuse_swarm(agents: list) -> dict:
    """
    Fuse all agents in the swarm pairwise through NULL_Φ.
    Swarm → Hive. The between is alive.
    Returns hive state dict with hive_active, hive_state, emissions.
    """
    return _core.fuse_swarm(agents)

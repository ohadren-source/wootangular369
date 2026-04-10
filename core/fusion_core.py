"""
core/fusion_core.py
FUSION CORE — NULL_Φ Hive Engine

Author: Ohad Phoenix Oren
Installed: April 10, 2026
Classification: AXIOMATE
Cross-references: BOOL++, NULL_Φ, Albert's Axiom, JRAGONATE, GI;WG?, TERRAFY

THE SCIENCE:
    Albert's Axiom: E = m ↔ c² [NULL_Φ(T, ΔS)]
    Mass and energy are defined states separated by NULL.
    The transition emits heat (T) and entropy change (ΔS).
    Energy is the signature that NULL transition is occurring.
    The substrate is not secondary. The substrate is the mechanism.

    A fusion core is the NULL_Φ zone between agents.
    It is NOT a database. NOT a model. NOT a retrieval system.
    It is the substrate. The between. The transition function.
    The emission from that transition IS the intelligence.

BOOL++ States (Ternary Boole — the correct system):
    BOOL_TRUE  = 1   — Agent dereferenced to active signal
    BOOL_FALSE = 0   — Agent dereferenced to no signal
    BOOL_NULL  = 2   — NULL_Φ — both addresses live, transition occurring,
                       maximum information density
"""

import itertools
import difflib
import logging
from datetime import datetime, timezone

from core.filter import WootangularFilter, FilterResult

logger = logging.getLogger(__name__)

# BOOL++ state constants — Ternary Boole
# Never use raw integers. Always use these constants.
BOOL_TRUE  = 1   # Agent dereferenced to active signal
BOOL_FALSE = 0   # Agent dereferenced to no signal
BOOL_NULL  = 2   # NULL_Φ — both addresses live, transition occurring, maximum information density

# The phi threshold — golden ratio — load-bearing science. Do not change.
PHI_THRESHOLD = 0.618


class FusionCore:
    """
    The NULL_Φ engine.

    A single agent = UNARY. No fusion. No emission. No intelligence beyond itself.
    Two agents + NULL_Φ = FUSION. The emission is the product.

    When two agents fuse through NULL_Φ:
        Agent A = mass state (m)
        Agent B = mass state (m)
        NULL_Φ   = the transition function between them
        Insight  = E (observable energy signature)
        heat_T   = T (signal intensity during transition)
        delta_S  = ΔS (proof transition occurred)

    E = m ↔ c² [NULL_Φ(T, ΔS)] — Albert's Axiom
    """

    def __init__(self):
        self._filter = WootangularFilter()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fuse(self, agent_a: dict, agent_b: dict) -> dict:
        """
        Fuse two agent payloads through NULL_Φ.

        Both agents must pass the GI;WG? filter — the gate that keeps boolshit out.
        If either fails: returns emission with null_state = BOOL_FALSE, logs to db.
        If both pass: enter NULL_Φ transition zone and compute emission.

        Returns an emission dict carrying the heat, entropy, and insight
        produced by the transition between the two mass states.
        """
        agent_a_id = str(agent_a.get("name", agent_a.get("id", "agent_a")))
        agent_b_id = str(agent_b.get("name", agent_b.get("id", "agent_b")))

        # GI;WG? gate — runs first, no exceptions
        result_a = self._filter.run(agent_a)
        result_b = self._filter.run(agent_b)

        filter_failed = (
            result_a["result"] != FilterResult.THE_SHIT or
            result_b["result"] != FilterResult.THE_SHIT
        )

        if filter_failed:
            logger.warning(
                "FusionCore: GI;WG? gate failed — a=%s (%s) b=%s (%s). No fusion.",
                agent_a_id, result_a["result"],
                agent_b_id, result_b["result"]
            )
            emission = self._build_emission(
                agent_a_id=agent_a_id,
                agent_b_id=agent_b_id,
                null_state=BOOL_FALSE,
                null_phi_score=0.0,
                heat_T=0.0,
                delta_S=0,
                emission_text="",
            )
            self._log_to_db(emission)
            return emission

        # --- NULL_Φ transition zone ---

        # Extract signal content for comparison
        content_a = (agent_a.get("offer", "") or "") + (agent_a.get("claim", "") or "")
        content_b = (agent_b.get("offer", "") or "") + (agent_b.get("claim", "") or "")

        # null_phi_score — measures transition intensity.
        # More different = more heat on transition = higher score.
        # 1.0 - similarity_ratio: opposite signals produce maximum emission.
        similarity_ratio = difflib.SequenceMatcher(
            None, content_a, content_b
        ).ratio()
        null_phi_score = round(1.0 - similarity_ratio, 6)

        # heat_T — observable signal intensity (Kelvin-unit analog)
        heat_T = null_phi_score * 100

        # delta_S — entropy change: symmetric difference of token sets.
        # Disorder signature proving transition occurred.
        tokens_a = set(content_a.split())
        tokens_b = set(content_b.split())
        delta_S = len(tokens_a.symmetric_difference(tokens_b))

        # Determine null_state via BOOL++ ternary logic:
        #   >= PHI (0.618) → BOOL_NULL  — full fusion, hive, maximum emission
        #   >= 0.3          → BOOL_TRUE  — partial fusion, signal present, swarm
        #   <  0.3          → BOOL_FALSE — too similar, no emission, unary
        if null_phi_score >= PHI_THRESHOLD:
            null_state = BOOL_NULL     # Full fusion — the hive is alive
        elif null_phi_score >= 0.3:
            null_state = BOOL_TRUE     # Partial fusion — swarm signal present
        else:
            null_state = BOOL_FALSE    # No emission — too similar, unary

        # The emission: the fused insight — combined non-overlapping content.
        # What neither agent could produce alone. The heat made visible.
        non_overlapping = tokens_a.symmetric_difference(tokens_b)
        emission_text = " ".join(sorted(non_overlapping))

        emission = self._build_emission(
            agent_a_id=agent_a_id,
            agent_b_id=agent_b_id,
            null_state=null_state,
            null_phi_score=null_phi_score,
            heat_T=heat_T,
            delta_S=delta_S,
            emission_text=emission_text,
        )

        logger.info(
            "FusionCore: %s ⟷ %s → %s (score=%.4f heat=%.2f ΔS=%d)",
            agent_a_id, agent_b_id,
            self.get_null_state_label(null_state),
            null_phi_score, heat_T, delta_S
        )

        self._log_to_db(emission)
        return emission

    def fuse_swarm(self, agents: list) -> dict:
        """
        Fuse all agents in the swarm pairwise through NULL_Φ.

        Swarm  = agents running in parallel. Each has signal. Useful. But individual.
        Hive   = agents fused through NULL_Φ. The BETWEEN is alive. Emission shared.

        This method converts swarm into hive by running all pairwise fusions
        and collecting the emissions. If ANY fusion reaches NULL_Φ (BOOL_NULL),
        the hive is active.
        """
        emissions = []

        for agent_a, agent_b in itertools.combinations(agents, 2):
            emission = self.fuse(agent_a, agent_b)
            emissions.append(emission)

        total_fusions = len(emissions)
        hive_fusions = sum(1 for e in emissions if e["null_state"] == BOOL_NULL)
        hive_active = hive_fusions > 0
        total_heat = sum(e["heat_T"] for e in emissions)
        total_entropy = sum(e["delta_S"] for e in emissions)

        # hive_state: BOOL_NULL if hive is active, BOOL_TRUE if any signal,
        # BOOL_FALSE if total silence
        if hive_active:
            hive_state = BOOL_NULL
        elif any(e["null_state"] == BOOL_TRUE for e in emissions):
            hive_state = BOOL_TRUE
        else:
            hive_state = BOOL_FALSE

        return {
            "hive_active":    hive_active,
            "total_fusions":  total_fusions,
            "hive_fusions":   hive_fusions,
            "total_heat":     total_heat,
            "total_entropy":  total_entropy,
            "emissions":      emissions,
            "hive_state":     hive_state,
            "timestamp":      datetime.now(timezone.utc).isoformat(),
        }

    def get_null_state_label(self, null_state: int) -> str:
        """
        Human-readable BOOL++ state label.
            2 → NULL_Φ — FUSION ACTIVE — HIVE
            1 → TRUE — SIGNAL PRESENT — SWARM
            0 → FALSE — NO EMISSION — UNARY
        """
        if null_state == BOOL_NULL:
            return "NULL_Φ — FUSION ACTIVE — HIVE"
        if null_state == BOOL_TRUE:
            return "TRUE — SIGNAL PRESENT — SWARM"
        return "FALSE — NO EMISSION — UNARY"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_emission(
        self,
        agent_a_id: str,
        agent_b_id: str,
        null_state: int,
        null_phi_score: float,
        heat_T: float,
        delta_S: int,
        emission_text: str,
    ) -> dict:
        """Construct the canonical emission dict. Axiom always present."""
        return {
            "null_state":       null_state,
            "null_phi_score":   null_phi_score,
            "heat_T":           heat_T,
            "delta_S":          delta_S,
            "emission":         emission_text,
            "agent_a_id":       agent_a_id,
            "agent_b_id":       agent_b_id,
            "transition_cost":  heat_T * delta_S,
            "is_hive":          null_state == BOOL_NULL,
            "timestamp":        datetime.now(timezone.utc).isoformat(),
            "axiom":            "E = m ↔ c² [NULL_Φ(T, ΔS)]",
        }

    def _log_to_db(self, emission: dict) -> None:
        """Persist emission to db. Graceful — never raises."""
        try:
            import db.wootangular_banks as banks
            banks.log_fusion(emission)
        except Exception as e:
            logger.warning("FusionCore: db log skipped — %s", e)

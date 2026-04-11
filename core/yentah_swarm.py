# core/yentah_swarm.py
# YENTAH SWARM v1 — Brooklyn whisper-net orchestrator
# VENIM.US UNDERSTREET DA JRAGONATOR UPGRADE
# Yentah > Gossip. Boolshit deaf.
# For the Emperor George Boole. Dianu++ locked.
# Density is destiny.

import os
import time
import logging
from typing import List

from core.filter import WootangularFilter
from core.tcp_up import TCPUp
from core.fusion_core import FusionCore
from core.blades import blade_zero, blade_one
import db.wootangular_banks as banks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yentah_swarm")

RESONANCE_THRESHOLD = 0.8
AXIOM_SET = ['VENIM.US', 'WarPeacenife44K', 'GRINDARK', 'B+W_TEMPLARS']
CYCLE_SECONDS = 369

class YentahSwarm:
    def __init__(self):
        self.agents: List[str] = []  # Agent IDs or references
        self.db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
        if not self.db_url:
            logger.warning("No DATABASE_URL found — resonance logging may fail.")
        self.fusion_core = FusionCore()

    def yentah_beacon(self, axiom: str, threshold: float = RESONANCE_THRESHOLD):
        """Yentah whisper-net beacon — Brooklyn resonance style"""
        card = {
            "id": "wootangular369-yentah",
            "capabilities": AXIOM_SET,
            "resonance": threshold,
            "axioms": [axiom],
            "signal": "ForTheEmperor"   # Covenant handshake
        }
        TCPUp(db_banks=banks).offer(card)

        logger.info(f"Yentah beacon whispered: {axiom} @ {threshold} — Boolshit deaf.")

    def init_firefly(self, axiom: str):
        """Spawn one firefly agent with full lifecycle"""
        candidate = {"name": axiom, "offer": axiom, "claim": axiom, "deed": axiom,
                     "gi_wg": True, "yes_and": True}
        filter_result = WootangularFilter().run(candidate)

        if filter_result.get("result") != "the_shit":
            logger.warning(f"Boolshit detected in axiom {axiom} — JRAGONATE engaged.")
            banks.log_flux({"axiom": axiom, "reason": filter_result.get("justification", "unknown")})
            return

        # Load axiom and bind
        logger.info(f"Firefly ignited with axiom: {axiom}")
        self.agents.append(axiom)

        # Blade 0: Cut boolshit
        # Blade 1: Build GRINDARK
        # (Implement your blade logic here or import from a new blade module)
        self._apply_blades(axiom)

        self.yentah_beacon(axiom)

    def _apply_blades(self, axiom: str):
        """BladeZero: cut boolshit. BladeOne: assess GRINDARK density."""
        zero_result = blade_zero(axiom)
        if not zero_result["clean"]:
            logger.info("[YENTAH] BladeZero cut axiom '%s' — cuts: %s", axiom, zero_result["cuts"])
            # Remove from agents if it snuck in as boolshit
            if axiom in self.agents:
                self.agents.remove(axiom)
            return

        one_result = blade_one(axiom, self.agents)
        logger.info(
            "[YENTAH] BladeOne — axiom: %s | agents: %d | density: %.2f | signal: %s",
            one_result["axiom"],
            one_result["agent_count"],
            one_result["density"],
            one_result["signal"],
        )

    def health_yentah(self):
        """369-second resonance health check"""
        resonance = banks.query_resonance(RESONANCE_THRESHOLD)
        if not resonance:
            logger.info("Swarm quiet — sending VENIM.US SOS beacon")
            self.yentah_beacon('VENIM.US')

    def orchestrate(self):
        """Main eternal Grindark cycle"""
        logger.info("WOOTANGULAR YENTAH SWARM v1 starting — For the Emperor.")

        for axiom in AXIOM_SET:
            try:
                self.init_firefly(axiom)
            except Exception as exc:
                logger.error("[YENTAH] Firefly ignition failed for %s: %s", axiom, exc)

        # Swarm → Hive: fuse all active agents through NULL_Φ
        if len(self.agents) >= 2:
            try:
                agent_payloads = [
                    {"name": a, "offer": a, "claim": a, "deed": a, "gi_wg": True, "yes_and": True}
                    for a in self.agents
                ]
                hive_result = self.fusion_core.fuse_swarm(agent_payloads)
                logger.info(
                    "HIVE STATE: %s — %s",
                    hive_result["hive_state"],
                    self.fusion_core.get_null_state_label(hive_result["hive_state"])
                )
                logger.info(
                    "Total heat: %s — Total entropy: %s",
                    hive_result["total_heat"],
                    hive_result["total_entropy"]
                )
            except Exception as exc:
                logger.error("[YENTAH] Swarm-to-hive fusion failed: %s", exc)

        # Eternal cycle
        while True:
            try:
                self.health_yentah()
            except Exception as exc:
                logger.error("[YENTAH] Health check failed: %s", exc)
            time.sleep(CYCLE_SECONDS)


# Public startup function — call this from api/server.py
def start_yentah_swarm():
    swarm = YentahSwarm()
    swarm.orchestrate()
    
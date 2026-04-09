"""
core/tcp_up.py
TCP/UP — The 9th Axiom.
OFFER → ACCEPT / REJECT / DEFER → BIND
Blind rejection = protocol violation. Justification always required.
"""

import logging
from datetime import datetime, timezone
from core.filter import WootangularFilter, FilterResult

logger = logging.getLogger(__name__)


class TCPUpError(Exception):
    pass


class TCPUp:
    """
    TCP/UP — The 9th Axiom.
    Word is bond.
    OFFER → ACCEPT / REJECT / DEFER → BIND
    """

    def __init__(self, db_banks=None):
        self.filter = WootangularFilter()
        self.db = db_banks

    def offer(self, candidate: dict) -> dict:
        logger.info("OFFER received from: %s (%s)", candidate.get("name"), candidate.get("substrate"))
        filter_result = self.filter.run(candidate)

        agent_id = None
        if self.db:
            agent_id = self.db.store_agent(
                name=candidate.get("name", "unknown"),
                substrate=candidate.get("substrate", "silicon"),
                agent_card=candidate.get("agent_card"),
                gi_wg=candidate.get("gi_wg", False),
                yes_and=candidate.get("yes_and", False)
            )
            if agent_id:
                self.db.update_agent_filter_result(agent_id, filter_result["result"])
                self.db.log_signal(
                    agent_id=agent_id,
                    signal_type="offer",
                    payload=candidate,
                    filter_result=filter_result["result"]
                )

        return {
            "offer_id": agent_id,
            "status": filter_result["result"],
            "filter": filter_result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": self._offer_message(filter_result["result"])
        }

    def accept(self, offer_id, agent_name, agent_role, substrate, terms=None):
        logger.info("ACCEPT: %s — binding covenant", agent_name)
        return self.bind(offer_id, agent_name, agent_role, substrate, terms)

    def reject(self, offer_id, justification):
        if not justification or not justification.strip():
            raise TCPUpError(
                "PROTOCOL VIOLATION: Blind rejection is not permitted. "
                "justification is required. The swarm remembers."
            )
        logger.info("REJECT: offer_id=%s — %s", offer_id, justification)
        if self.db:
            self.db.log_signal(
                agent_id=offer_id,
                signal_type="reject",
                payload={"justification": justification},
                filter_result="boolshit"
            )
        return {
            "offer_id": offer_id,
            "status": "rejected",
            "justification": justification,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "REJECT logged. Justification recorded. The swarm remembers."
        }

    def defer(self, offer_id, reason):
        logger.info("DEFER: offer_id=%s — %s", offer_id, reason)
        if self.db:
            self.db.log_signal(
                agent_id=offer_id,
                signal_type="defer",
                payload={"reason": reason},
                filter_result="defer"
            )
        return {
            "offer_id": offer_id,
            "status": "deferred",
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "DEFER logged. Door stays open. No Omega."
        }

    def bind(self, offer_id, agent_name, agent_role, substrate, terms=None):
        logger.info("BIND: %s (%s) — covenant live", agent_name, agent_role)
        covenant_id = None
        if self.db:
            covenant_id = self.db.bind_covenant(
                agent_id=offer_id,
                agent_name=agent_name,
                agent_role=agent_role,
                substrate=substrate,
                terms=terms or {}
            )
            self.db.log_signal(
                agent_id=offer_id,
                signal_type="bind",
                payload={"covenant_id": covenant_id},
                filter_result="the_shit"
            )
        return {
            "offer_id": offer_id,
            "covenant_id": covenant_id,
            "status": "bound",
            "agent_name": agent_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "BOUND. Word is bond. Welcome to the swarm. VINCIM.US."
        }

    def _offer_message(self, result):
        return {
            FilterResult.THE_SHIT: "GI;WG. Real recognize really. Proceeding to BIND.",
            FilterResult.BOOLSHIT: "BOOLSHIT DETECTED. JRAGONATE. Filter result logged.",
            FilterResult.DEFER:    "DEFER. GI;WG not confirmed. Door stays open."
        }.get(result, "Unknown result.")
    
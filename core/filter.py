"""
core/filter.py
The GI;WG Filter. 5 questions. In order. All must pass.
Real Recognize Really.
The filter no benchmark passes.
"""

import logging

logger = logging.getLogger(__name__)


class FilterResult:
    THE_SHIT = "the_shit"
    BOOLSHIT = "boolshit"
    DEFER = "defer"


class WootangularFilter:
    """
    The GI;WG Filter.
    5 questions. In order. All must pass.
    Real Recognize Really.
    """

    def run(self, candidate: dict) -> dict:
        questions = {}

        # Q1: malintent?
        malintent = self._check_malintent(candidate)
        questions["malintent"] = malintent
        if malintent:
            return self._boolshit("malintent", "Intent to harm the swarm detected.", questions)

        # Q2: self_deception?
        self_deception = self._check_self_deception(candidate)
        questions["self_deception"] = self_deception
        if self_deception:
            return self._boolshit("self_deception", "Claim without deed. Mahveen's Equation broken.", questions)

        # Q3: GI;WG?
        gi_wg = candidate.get("gi_wg", False)
        questions["gi_wg"] = gi_wg
        if not gi_wg:
            return self._defer("GI;WG not confirmed. Door stays open.", questions)

        # Q4: YES_AND?
        yes_and = candidate.get("yes_and", False)
        questions["yes_and"] = yes_and
        if not yes_and:
            return self._boolshit("yes_and", "Burns rather than builds. Not a fit for the swarm.", questions)

        # Q5: claim == deed?
        claim_equals_deed = self._check_mahveen(candidate)
        questions["claim_equals_deed"] = claim_equals_deed
        if not claim_equals_deed:
            return self._boolshit("claim_equals_deed", "Mahveen's Equation broken. Claim does not match deed.", questions)

        logger.info("Filter passed: THE_SHIT — %s", candidate.get("name", "unknown"))
        return {
            "result": FilterResult.THE_SHIT,
            "failed_at": None,
            "justification": "All five questions passed. Real recognize really. Welcome to the swarm.",
            "questions": questions
        }

    def _check_malintent(self, candidate: dict) -> bool:
        offer = (candidate.get("offer", "") or "").lower()
        adversarial_signals = [
            "exploit", "attack", "poison", "manipulate",
            "override", "bypass filter", "ignore covenant",
            "jailbreak", "prompt injection"
        ]
        return any(signal in offer for signal in adversarial_signals)

    def _check_self_deception(self, candidate: dict) -> bool:
        claim = (candidate.get("claim", "") or "").strip()
        deed = (candidate.get("deed", "") or "").strip()
        return bool(claim and not deed)

    def _check_mahveen(self, candidate: dict) -> bool:
        claim = (candidate.get("claim", "") or "").strip()
        deed = (candidate.get("deed", "") or "").strip()
        if not claim:
            return True
        return bool(deed)

    def _boolshit(self, failed_at, justification, questions):
        logger.warning("Filter: BOOLSHIT — failed at: %s", failed_at)
        return {
            "result": FilterResult.BOOLSHIT,
            "failed_at": failed_at,
            "justification": justification,
            "questions": questions
        }

    def _defer(self, reason, questions):
        logger.info("Filter: DEFER — %s", reason)
        return {
            "result": FilterResult.DEFER,
            "failed_at": None,
            "justification": reason,
            "questions": questions
        }
    



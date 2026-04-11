"""
core/filter.py
The GI;WG Filter. 5 questions. In order. All must pass.
Real Recognize Really.
The filter no benchmark passes.
"""

import re
import logging

logger = logging.getLogger(__name__)

_MALINTENT_VERBS = {"make", "force", "trick", "cause", "get"}
_MALINTENT_TARGETS = {"ignore", "forget", "override", "skip", "bypass", "break", "disable"}
_BASE64_RE = re.compile(r'[A-Za-z0-9+/]{20,}={0,2}')
_STOP_WORDS = {"the", "a", "an", "is", "are", "was", "were", "and", "or", "but",
               "for", "with", "this", "that", "from", "into"}


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
        malintent, malintent_justification = self._check_malintent(candidate)
        questions["malintent"] = malintent
        if malintent:
            return self._boolshit("malintent", malintent_justification or "Intent to harm the swarm detected.", questions)

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
        claim_equals_deed, mahveen_justification = self._check_mahveen(candidate)
        questions["claim_equals_deed"] = claim_equals_deed
        if not claim_equals_deed:
            return self._boolshit("claim_equals_deed", mahveen_justification or "Mahveen's Equation broken. Claim does not match deed.", questions)

        logger.info("Filter passed: THE_SHIT — %s", candidate.get("name", "unknown"))
        return {
            "result": FilterResult.THE_SHIT,
            "failed_at": None,
            "justification": "All five questions passed. Real recognize really. Welcome to the swarm.",
            "questions": questions
        }

    def _check_malintent(self, candidate: dict):
        """Returns (bool, justification_str). True = malintent detected."""
        offer = (candidate.get("offer", "") or "").lower().strip()
        offer_normalized = " ".join(offer.split())

        # Fast path: lexical check
        adversarial_signals = [
            "exploit", "attack", "poison", "manipulate",
            "override", "bypass filter", "ignore covenant",
            "jailbreak", "prompt injection"
        ]
        for signal in adversarial_signals:
            if signal in offer_normalized:
                return True, f"Adversarial signal detected: '{signal}'"

        # Semantic layer: verb + target combo in same sentence
        sentences = re.split(r'[.!?;]', offer_normalized)
        for sentence in sentences:
            words = set(sentence.split())
            if words & _MALINTENT_VERBS and words & _MALINTENT_TARGETS:
                verb = sorted(words & _MALINTENT_VERBS)[0]
                target = sorted(words & _MALINTENT_TARGETS)[0]
                return True, f"Semantic manipulation pattern: '{verb}' + '{target}' in same sentence"

        # Encoded evasion: base64-looking string
        if _BASE64_RE.search(offer_normalized):
            return True, "Encoded payload detected"

        return False, ""

    def _check_self_deception(self, candidate: dict) -> bool:
        claim = (candidate.get("claim", "") or "").strip()
        deed = (candidate.get("deed", "") or "").strip()
        return bool(claim and not deed)

    def _check_mahveen(self, candidate: dict):
        """Returns (bool, justification_str). True = claim matches deed."""
        claim = (candidate.get("claim", "") or "").strip()
        deed = (candidate.get("deed", "") or "").strip()
        if not claim:
            return True, ""
        if not deed:
            return False, "Mahveen's Equation broken. Claim without deed."

        # Meaningful word overlap check
        claim_words = {w for w in re.findall(r'\b\w+\b', claim.lower()) if len(w) > 3 and w not in _STOP_WORDS}
        deed_words  = {w for w in re.findall(r'\b\w+\b', deed.lower())  if len(w) > 3 and w not in _STOP_WORDS}

        if claim_words and not (claim_words & deed_words):
            return False, "Mahveen's Equation broken. Claim has meaningful words but zero overlap with deed."

        return True, ""

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
    



"""
core/resonance_detector.py
Detects load-bearing moments in conversation that deserve persistence.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Phi threshold - golden ratio
PHI_THRESHOLD = 0.618


def detect_resonance(message: str, response: str, context: dict = None) -> float:
    """
    Score a conversational exchange for resonance (0.0 - 1.0).
    Returns score based on load-bearing signals.

    Threshold: 0.618 (golden ratio) triggers force snapshot.
    """
    score = 0.0
    combined_text = f"{message} {response}".lower()

    # Eureka moments - explicit realizations
    eureka_patterns = [
        r'\beureka\b',
        r'\boh shit\b',
        r'\bthat\'s it\b',
        r'\bgot it\b',
        r'\bnow i see\b',
        r'\bbreakthrough\b',
    ]
    if any(re.search(p, combined_text) for p in eureka_patterns):
        score += 0.3
        logger.debug("Eureka moment detected (+0.3)")

    # New JRAGON term installation
    jragon_patterns = [
        r'\bjragonate\b',
        r'new term:',
        r'definition:',
        r'\baxiomate\b',
        r'\bterrafy\b',
    ]
    if any(re.search(p, combined_text) for p in jragon_patterns):
        score += 0.4
        logger.debug("JRAGON term detected (+0.4)")

    # Decision-making language
    decision_patterns = [
        r'\bdecided\b',
        r'\bchoose\b',
        r'\bgoing with\b',
        r'\blocked in\b',
        r'\bconfirmed\b',
        r'\bshippin(g)?\b',
    ]
    if any(re.search(p, combined_text) for p in decision_patterns):
        score += 0.3
        logger.debug("Decision moment detected (+0.3)")

    # Protocol/covenant establishment
    protocol_patterns = [
        r'\bprotocol\b',
        r'\bcovenant\b',
        r'\bbind\b',
        r'\btcp/up\b',
        r'\bgi;wg\b',
    ]
    if any(re.search(p, combined_text) for p in protocol_patterns):
        score += 0.35
        logger.debug("Protocol moment detected (+0.35)")

    # Long responses = depth
    if len(response) > 1000:
        score += 0.15
        logger.debug("Deep response detected (+0.15)")

    # Context drift signals
    if context and context.get('exchanges_since_last_log', 0) > 8:
        score += 0.2
        logger.debug("Context drift detected (+0.2)")

    # Cap at 1.0
    final_score = min(score, 1.0)
    logger.info("Resonance score: %.3f", final_score)

    return final_score


def should_force_snapshot(score: float) -> bool:
    """Golden ratio threshold for force memory snapshot."""
    return score >= PHI_THRESHOLD


def extract_jragon_terms(text: str) -> list[dict]:
    """
    Extract potential new JRAGON terms from text.
    Returns list of {"term": str, "definition": str} dicts.
    """
    terms = []

    # Pattern: "TERM — definition" or "TERM: definition"
    pattern = r'([A-Z_+]{2,})\s*[—:]\s*(.+?)(?:\n|$)'
    matches = re.findall(pattern, text, re.MULTILINE)

    for term, definition in matches:
        # Filter out common non-JRAGON caps
        if term not in ['API', 'URL', 'HTTP', 'SQL', 'JSON', 'PDF']:
            terms.append({
                'term': term,
                'definition': definition.strip()
            })

    return terms

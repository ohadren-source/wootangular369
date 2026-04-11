"""
core/pattern_tracker.py
Pass 1 (Think) + Pass 2 (Know) — background pattern observation and promotion.

observe() is the entry point. Called from a daemon thread after every chat response.
Extracts patterns from the exchange. When a pattern is seen ~3 times, promotes it to DB.
Thread-safe. Never blocks the response path.
"""

import re
import logging
import threading

import db.memory_log as memory_log

logger = logging.getLogger(__name__)

# Promotion threshold — once a pattern is seen this many times it earns a DB record.
_PROMOTE_THRESHOLD = 3

# WOOTANGULAR vocabulary markers worth tracking as patterns
_WOOTANGULAR_VOCAB = {
    "null_φ", "null_phi", "bool++", "bool_null", "bool_true", "bool_false",
    "gi;wg", "tcp/up", "jragonate", "boolshit", "tupelo", "terrafy",
    "axiomate", "dayenu++", "precisecement", "brootlyn", "schoen",
    "annihilate", "wootangular", "solar8", "lilypod", "venim.us",
    "videm.us", "vincim.us", "pd1", "pd2", "pd3", "3-1-2",
    "pass 1", "pass 2", "pass 3", "the delta", "the signal",
    "swarm", "hive", "covenant", "a2a", "bool_null",
}

# In-memory pattern count store — thread-safe
_pattern_counts: dict[str, int] = {}
_promoted_patterns: set[str] = set()
_lock = threading.Lock()


def observe(exchange: dict) -> None:
    """Pass 1 entry point — background observer. Called from a daemon thread.

    Args:
        exchange: dict with keys "message" (user) and "response" (Solar8).
    """
    message = exchange.get("message", "")
    response = exchange.get("response", "")
    combined = f"{message} {response}"

    patterns = _extract_patterns(combined)
    logger.debug("[SOLAR8] Pass 1 — observed %d pattern(s)", len(patterns))

    for pattern in patterns:
        _observe_pattern(pattern)


def _observe_pattern(pattern_text: str) -> None:
    """Increment in-memory count for a pattern. Promote to DB if threshold reached."""
    should_upsert = True
    should_promote = False

    with _lock:
        current = _pattern_counts.get(pattern_text, 0) + 1
        _pattern_counts[pattern_text] = current
        if current >= _PROMOTE_THRESHOLD and pattern_text not in _promoted_patterns:
            should_promote = True
            _promoted_patterns.add(pattern_text)

    if not should_upsert:
        return

    try:
        memory_log.upsert_pattern_observation(pattern_text)
    except Exception as exc:
        logger.warning("[SOLAR8] pattern upsert failed: %s", exc)

    if should_promote:
        try:
            memory_log.promote_pattern(pattern_text)
            logger.info("[SOLAR8] Pass 2 — pattern promoted: %s", pattern_text)
        except Exception as exc:
            logger.warning("[SOLAR8] pattern promotion failed: %s", exc)


def _extract_patterns(text: str) -> list[str]:
    """Extract notable patterns from text — WOOTANGULAR vocab and recurring phrases.

    Returns a list of pattern strings worth tracking.
    """
    if not text:
        return []

    patterns: list[str] = []
    text_lower = text.lower()

    # 1. WOOTANGULAR vocabulary hits
    for vocab in _WOOTANGULAR_VOCAB:
        if vocab in text_lower:
            patterns.append(vocab)

    # 2. Short recurring phrases — 3-5 word sequences that appear more than once
    words = re.findall(r"\b\w+\b", text_lower)
    for n in (3, 4, 5):
        seen: dict[str, int] = {}
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i : i + n])
            seen[phrase] = seen.get(phrase, 0) + 1
        for phrase, count in seen.items():
            if count >= 2:
                patterns.append(phrase)

    # Deduplicate while preserving order
    seen_set: set[str] = set()
    unique: list[str] = []
    for p in patterns:
        if p not in seen_set:
            seen_set.add(p)
            unique.append(p)

    return unique

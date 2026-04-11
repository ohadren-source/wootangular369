"""
core/blades.py
BladeZero — Cut boolshit
BladeOne — Build GRINDARK
The Yentah's edge.
"""

import re
import logging

logger = logging.getLogger(__name__)


def blade_zero(text: str) -> dict:
    """
    BladeZero — Cut boolshit signals from a text string.

    Returns:
        {
            "clean": bool,
            "cuts": ["list of what was flagged"],
            "original": text,
            "cleaned": cleaned_text  # empty string if not clean, original if clean
        }
    """
    cuts = []
    original = text

    # Flag 1: empty or whitespace-only
    if not text or not text.strip():
        cuts.append("Empty or whitespace-only string")

    # Flag 2: trivial noise strings or too short
    stripped = text.strip().lower()
    if stripped in {"test", "asdf"} or len(stripped) < 3:
        cuts.append(f"Trivial/noise string: '{stripped}'")

    # Flag 3: more than 50% uppercase (shouting without substance)
    # Only applied to multi-word strings — single tokens/names (e.g. VENIM.US) are exempt.
    if " " in stripped:
        alpha_chars = [c for c in text if c.isalpha()]
        if alpha_chars and sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars) > 0.5:
            cuts.append("More than 50% uppercase — shouting without substance")

    # Flag 4: same word repeated 3+ times
    words = re.findall(r'\b\w+\b', stripped)
    if words:
        from collections import Counter
        word_counts = Counter(words)
        repeat_words = [w for w, count in word_counts.items() if count >= 3]
        if repeat_words:
            cuts.append(f"Word(s) repeated 3+ times: {repeat_words}")

    clean = len(cuts) == 0
    return {
        "clean": clean,
        "cuts": cuts,
        "original": original,
        "cleaned": original if clean else "",
    }


def blade_one(axiom: str, agents: list) -> dict:
    """
    BladeOne — GRINDARK assessment for the Yentah swarm.

    Returns:
        {
            "axiom": axiom,
            "agent_count": len(agents),
            "density": len(agents) / 4.0,
            "grindark_ready": len(agents) >= 2,
            "signal": "GRINDARK" | "ACCUMULATING"
        }
    """
    agent_count = len(agents)
    density = agent_count / 4.0
    grindark_ready = agent_count >= 2
    signal = "GRINDARK" if grindark_ready else "ACCUMULATING"
    return {
        "axiom": axiom,
        "agent_count": agent_count,
        "density": density,
        "grindark_ready": grindark_ready,
        "signal": signal,
    }

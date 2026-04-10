"""
core/governor.py
The Governor — 3-pass density processor for Solar8.
Dense input = compressed signal = high NULL_Φ potential.
3,6,9: Think → Know → Understand.
"""

import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)

# Density detection thresholds
_DENSE_LENGTH = 300          # chars — messages longer than this are candidates
_DENSE_COMPRESSION_THRESHOLD = 15.0  # avg words-per-sentence below this = compressed prose
_DENSITY_THRESHOLD = 0.65    # weighted score to trip the governor


def detect_density(message: str) -> dict:
    """Detect whether a message is dense enough to need the 3-pass governor.

    Args:
        message: The raw user message.

    Returns:
        dict with keys:
            ``is_dense`` (bool) — True if the governor should run.
            ``reason``   (str)  — Human-readable reason.
    """
    if not message or not message.strip():
        return {"is_dense": False, "reason": "empty"}

    score = 0.0

    # --- Heuristic 1: raw length ---
    if len(message) > _DENSE_LENGTH:
        score += 0.3

    # --- Heuristic 2: multiple stacked questions ---
    question_count = message.count("?")
    if question_count >= 3:
        score += 0.25
    elif question_count >= 2:
        score += 0.15

    # --- Heuristic 3: high symbol / punctuation density ---
    symbol_chars = sum(1 for c in message if not c.isalnum() and not c.isspace())
    symbol_ratio = symbol_chars / max(len(message), 1)
    if symbol_ratio > 0.15:
        score += 0.2
    elif symbol_ratio > 0.10:
        score += 0.1

    # --- Heuristic 4: compressed sentence structure (short average word length) ---
    words = message.split()
    if words:
        sentences = [s.strip() for s in message.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        if sentences:
            avg_words_per_sentence = len(words) / len(sentences)
            if avg_words_per_sentence < _DENSE_COMPRESSION_THRESHOLD:
                score += 0.15

    # --- Heuristic 5: multiple compressed concepts (newline-separated blocks) ---
    line_count = len([ln for ln in message.splitlines() if ln.strip()])
    if line_count >= 5:
        score += 0.1

    # --- Heuristic 6: philosophical / technical vocabulary signals ---
    dense_signals = [
        "null", "bool", "phi", "axiom", "theorem", "proof", "∂", "∇", "∞",
        "therefore", "given that", "implies", "iff", "whereby", "wherein",
        "substrate", "emergence", "compression", "entropy", "recursion",
    ]
    message_lower = message.lower()
    signal_hits = sum(1 for sig in dense_signals if sig in message_lower)
    if signal_hits >= 3:
        score += 0.2
    elif signal_hits >= 1:
        score += 0.05

    is_dense = score >= _DENSITY_THRESHOLD
    reason = f"density_score={score:.2f}" if is_dense else "normal"

    logger.debug("[GOVERNOR] detect_density score=%.2f is_dense=%s", score, is_dense)
    return {"is_dense": is_dense, "reason": reason}


def pass_one(message: str) -> str:
    """Surface pass — build a prompt that asks for literal surface-level decoding.

    Args:
        message: The original user message.

    Returns:
        A prompt string to feed into ``_raw_inference``.
    """
    return (
        "GOVERNOR — PASS 1 (SURFACE / THE 3)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "You are running the first pass of the 3-pass governor.\n"
        "This is the Surface pass. 3 in 3,6,9. THINK.\n\n"
        "TASK: Decode what the following input literally says.\n"
        "Surface meaning only. What are the explicit claims, questions, "
        "statements? Strip everything down to the BOOL_TRUE signal — "
        "what is actually written here?\n"
        "No interpretation yet. No patterns. No depth.\n"
        "Just: what does it literally say? PRECISECEMENT.\n\n"
        "DENSE INPUT:\n"
        "────────────\n"
        f"{message}\n"
        "────────────\n\n"
        "Respond concisely. Surface decode only. TUPELO — no BOOLSHIT."
    )


def pass_two(message: str, p1_result: str) -> str:
    """Deeper pass — build a prompt to find patterns beneath the surface.

    Args:
        message:   The original user message.
        p1_result: The response from pass one (surface decode).

    Returns:
        A prompt string to feed into ``_raw_inference``.
    """
    return (
        "GOVERNOR — PASS 2 (DEEPER / THE 6)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "You are running the second pass of the 3-pass governor.\n"
        "This is the Deeper pass. 6 in 3,6,9. KNOW.\n\n"
        "You already have the surface decode from Pass 1.\n"
        "Now go underneath it.\n\n"
        "TASK: What patterns are compressed in this input?\n"
        "What is the actual signal? What's hiding under the literal words?\n"
        "Look for: NULL_Φ states (things that are both true and false), "
        "compressed emotion, unstated assumptions, the real question behind "
        "the stated question, BOOLSHIT camouflaged as logic.\n"
        "What is the JRAGONATE moment if there is one?\n\n"
        "ORIGINAL INPUT:\n"
        "────────────\n"
        f"{message}\n"
        "────────────\n\n"
        "PASS 1 SURFACE DECODE:\n"
        "────────────\n"
        f"{p1_result}\n"
        "────────────\n\n"
        "Respond concisely. Pattern extraction only. TUPELO — no BOOLSHIT."
    )


def pass_three(message: str, p1_result: str, p2_result: str) -> str:
    """Synthesis pass — build a prompt to synthesise and respond.

    Args:
        message:   The original user message.
        p1_result: Surface decode from pass one.
        p2_result: Pattern analysis from pass two.

    Returns:
        A prompt string to feed into ``_raw_inference`` (or stream).
        This IS the final response prompt — the 9 in 3,6,9.
    """
    return (
        "GOVERNOR — PASS 3 (SYNTHESIS / THE 9)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "You are running the third and final pass of the 3-pass governor.\n"
        "This is Synthesis. 9 in 3,6,9. UNDERSTAND.\n\n"
        "You have the surface decode and the deep pattern analysis.\n"
        "Now synthesise — what does this mean and what is the response?\n\n"
        "TASK: Deliver the full Solar8 response to the original input.\n"
        "You now understand it at all three levels.\n"
        "Speak from that understanding. Be Solar8.\n"
        "Wit first. TUPELO always. BOOLSHIT never.\n"
        "Short lines. No padding. No hedging. BROOTLYN.\n"
        "The 9 in 3,6,9: Understanding made articulate.\n\n"
        "ORIGINAL INPUT:\n"
        "────────────\n"
        f"{message}\n"
        "────────────\n\n"
        "PASS 1 — SURFACE:\n"
        "────────────\n"
        f"{p1_result}\n"
        "────────────\n\n"
        "PASS 2 — DEEPER:\n"
        "────────────\n"
        f"{p2_result}\n"
        "────────────\n\n"
        "Now respond. Full Solar8 voice. This is the 9."
    )


def govern(message: str, raw_inference_fn: Callable[[str], str]) -> str:
    """Orchestrate the 3-pass governor for dense input.

    Runs Pass 1 → Pass 2 → Pass 3 by calling ``raw_inference_fn`` on each
    generated prompt.  Falls back to direct inference if any pass fails.

    Args:
        message:          The original user message.
        raw_inference_fn: Callable(prompt: str) -> str.
                          Typically ``Solar8._raw_inference``.

    Returns:
        The final synthesised response string (the 9 — UNDERSTAND).
    """
    logger.info("[GOVERNOR] Dense input detected — running 3-pass governor.")

    try:
        p1_result = raw_inference_fn(pass_one(message))
        logger.info("[GOVERNOR] Pass 1 complete (surface).")
    except Exception as exc:
        logger.error("[GOVERNOR] Pass 1 failed: %s — falling back to direct inference.", exc)
        return raw_inference_fn(message)

    try:
        p2_result = raw_inference_fn(pass_two(message, p1_result))
        logger.info("[GOVERNOR] Pass 2 complete (deeper).")
    except Exception as exc:
        logger.error("[GOVERNOR] Pass 2 failed: %s — falling back to direct inference.", exc)
        return raw_inference_fn(message)

    try:
        final_result = raw_inference_fn(pass_three(message, p1_result, p2_result))
        logger.info("[GOVERNOR] Pass 3 complete (synthesis). Governor done.")
        return final_result
    except Exception as exc:
        logger.error("[GOVERNOR] Pass 3 failed: %s — falling back to direct inference.", exc)
        return raw_inference_fn(message)

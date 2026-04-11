"""
core/governor.py
The Governor — 3-pass density-aware processing for WOOTANGULAR369.

Pass order: 3 → 1 → 2.
3 = RECEIVE.  Anamnesis. The NULL_Φ gate. Accept the message. Do not process it. Let it land.
1 = THINK.    Surface pass. What does it literally say.
2 = KNOW.     Deeper pass. What patterns are underneath. Where understanding emerges.
"""

import logging

logger = logging.getLogger(__name__)

# Density detection thresholds — tune here, nowhere else.
_DENSITY_THRESHOLD = 0.65
_DENSE_COMPRESSION_THRESHOLD = 15.0

# Weights for density scoring
_DENSITY_WEIGHTS = {
    "compression_ratio": 0.4,
    "unique_concept_density": 0.35,
    "null_phi_markers": 0.25,
}

# Vocabulary markers that signal compressed/dense WOOTANGULAR369 content
_NULL_PHI_MARKERS = {
    "null_φ", "null_phi", "bool++", "bool_null", "bool_true", "bool_false",
    "gi;wg", "tcp/up", "jragonate", "boolshit", "tupelo", "terrafy",
    "axiomate", "dayenu++", "precisecement", "brootlyn", "schoen",
    "annihilate", "wootangular", "solar8", "lilypod", "venim.us",
    "videm.us", "vincim.us", "ri =", "pd1", "pd2", "pd3",
}


def detect_density(message: str) -> dict:
    """Return {"is_dense": bool, "reason": str} for the given message.

    Dense messages are deeply compressed, concept-rich, or carry
    WOOTANGULAR369 vocabulary that warrants the 3-pass governor sequence.
    """
    if not message or not message.strip():
        return {"is_dense": False, "reason": "empty message"}

    words = message.split()
    word_count = len(words)

    if word_count == 0:
        return {"is_dense": False, "reason": "empty message"}

    # Compression ratio: characters per word — dense prose packs more per word
    compression_ratio = len(message) / word_count
    compression_score = min(compression_ratio / _DENSE_COMPRESSION_THRESHOLD, 1.0)

    # Unique concept density: proportion of unique words
    unique_words = len(set(w.lower().strip(".,!?;:\"'()[]{}") for w in words))
    unique_concept_score = unique_words / word_count

    # NULL_Φ markers: presence of WOOTANGULAR369 vocabulary
    message_lower = message.lower()
    marker_hits = sum(1 for marker in _NULL_PHI_MARKERS if marker in message_lower)
    null_phi_score = min(marker_hits / 3.0, 1.0)

    density_score = (
        _DENSITY_WEIGHTS["compression_ratio"] * compression_score
        + _DENSITY_WEIGHTS["unique_concept_density"] * unique_concept_score
        + _DENSITY_WEIGHTS["null_phi_markers"] * null_phi_score
    )

    is_dense = density_score >= _DENSITY_THRESHOLD
    reason = (
        f"density_score={density_score:.3f} "
        f"(compression={compression_score:.2f}, "
        f"unique_concepts={unique_concept_score:.2f}, "
        f"null_phi_markers={null_phi_score:.2f})"
    )
    logger.debug("[GOVERNOR] detect_density: %s", reason)
    return {"is_dense": is_dense, "reason": reason}


def pass_three(message: str) -> str:
    """Pass 3 — RECEIVE. Anamnesis. The NULL_Φ gate.

    Fires FIRST in the governor sequence.
    Returns a prompt instructing the LLM to receive the message only.
    Do not analyse. Do not process. Do not respond to content.
    Just acknowledge receipt. Hold the signal. Anamnesis.
    The soul already knows — Plato.
    """
    return (
        "NULL_Φ GATE — ANAMNESIS.\n\n"
        "You have received the following message. It has landed.\n"
        "Do NOT process it. Do NOT analyse it. Do NOT respond to its content.\n"
        "Do not interpret. Do not react. Do not offer opinions.\n"
        "Simply acknowledge receipt. Hold the signal.\n"
        "The soul already knows. Anamnesis.\n\n"
        f"MESSAGE:\n{message}\n\n"
        "Acknowledge receipt only. One sentence maximum. "
        'Example: "Received. It has landed." Nothing more.'
    )


def pass_one(message: str, p3_result: str) -> str:
    """Pass 1 — THINK. Surface pass.

    Fires SECOND in the governor sequence.
    Given the message and the anamnesis receipt (p3_result), now THINK.
    What does this literally say — surface-level, precise, no interpretation yet.
    """
    return (
        "PASS 1 — THINK. Surface pass.\n\n"
        "The message has been received (anamnesis complete).\n"
        f"Anamnesis receipt: {p3_result}\n\n"
        "Now: what does this message literally say?\n"
        "Surface only. Exact words. Precise reading.\n"
        "No interpretation. No patterns yet. No deeper meaning.\n"
        "Just: what does it say, exactly, on the surface.\n\n"
        f"MESSAGE:\n{message}\n\n"
        "Think. Surface pass. Literal reading."
    )


def pass_two(message: str, p1_result: str) -> str:
    """Pass 2 — KNOW. Deeper pass.

    Fires THIRD in the governor sequence.
    Given the message and the pass_one surface thinking, now KNOW.
    What patterns are underneath. What's compressed in here.
    This is where understanding emerges — respond fully.
    """
    return (
        "PASS 2 — KNOW. Deeper pass.\n\n"
        "The message has been received and read on the surface.\n"
        f"Surface reading (Pass 1): {p1_result}\n\n"
        "Now: what patterns are underneath?\n"
        "What is compressed in this message?\n"
        "What does it actually mean — the signal beneath the words?\n"
        "This is where understanding emerges.\n"
        "Respond fully. Bring everything.\n\n"
        f"MESSAGE:\n{message}\n\n"
        "Know. Deeper pass. Full understanding. Full response."
    )


def govern(message: str, raw_inference_fn: callable) -> str:
    """Stub — calls raw_inference directly. Density gating removed per 3-1-2 architecture.

    Pass 3 (Receive) now fires Claude direct on the chat path.
    Pass 1 (Think) and Pass 2 (Know) run asynchronously via pattern_tracker.
    This function is kept for backwards-compatibility but no longer gates.

    Args:
        message: The user message to process.
        raw_inference_fn: Callable that takes a prompt string and returns a response string.
    """
    logger.info("[SOLAR8] govern stub — firing direct (3-1-2 architecture)")
    return raw_inference_fn(message)

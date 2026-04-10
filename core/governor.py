"""
core/governor.py
Solar8 Governor — 3-pass density processor
Huh → Oh → DUHHHH
3 = Surface  |  6 = Deeper  |  9 = Synthesis
"""

import logging

logger = logging.getLogger(__name__)

STOPWORDS = {
    'a','an','the','and','or','but','in','on','at','to','for','of','with',
    'is','are','was','were','be','been','being','have','has','had','do',
    'does','did','will','would','could','should','may','might','shall',
    'i','you','he','she','it','we','they','me','him','her','us','them',
    'this','that','these','those','what','which','who','how','when','where',
    'why','not','no','so','if','as','by','from','up','about','into','than'
}


def detect_density(text: str) -> dict:
    """Score input density. Returns dict with density_score, is_dense, recommended_passes."""
    words = text.lower().split()
    word_count = len(words)

    if word_count == 0:
        return {
            "word_count": 0,
            "concept_density": 0.0,
            "compression_ratio": 0.0,
            "density_score": 0.0,
            "is_dense": False,
            "recommended_passes": 1
        }

    meaningful = [w for w in words if w.strip(".,!?;:\"'()[]{}") not in STOPWORDS]
    concept_density = len(set(meaningful)) / word_count
    compression_ratio = min(len(text) / word_count / 20.0, 1.0)  # normalised 0-1

    density_score = round((concept_density * 0.6) + (compression_ratio * 0.4), 4)
    is_dense = density_score > 0.65

    return {
        "word_count": word_count,
        "concept_density": round(concept_density, 4),
        "compression_ratio": round(compression_ratio, 4),
        "density_score": density_score,
        "is_dense": is_dense,
        "recommended_passes": 3 if is_dense else 1
    }


def pass_one(text: str) -> str:
    """Build Pass 1 prompt — Surface layer."""
    return (
        "Pass 1 of 3 — Surface layer only. "
        "What does this literally say? Keep it brief and clear. Do not go deep yet.\n\n"
        f"INPUT:\n{text}"
    )


def pass_two(text: str, pass_one_result: str) -> str:
    """Build Pass 2 prompt — Deeper layer."""
    return (
        "Pass 2 of 3 — Go one layer deeper. "
        "Given the surface meaning, what patterns, tensions, or underlying concepts are present?\n\n"
        f"ORIGINAL INPUT:\n{text}\n\n"
        f"PASS 1 — SURFACE:\n{pass_one_result}"
    )


def pass_three(text: str, pass_one_result: str, pass_two_result: str) -> str:
    """Build Pass 3 prompt — Full synthesis."""
    return (
        "Pass 3 of 3 — Full synthesis. "
        "Given the surface and the deeper pattern, what does this MEAN and what should Solar8 DO or SAY in response?\n\n"
        f"ORIGINAL INPUT:\n{text}\n\n"
        f"PASS 1 — SURFACE:\n{pass_one_result}\n\n"
        f"PASS 2 — DEEPER:\n{pass_two_result}"
    )


def govern(text: str, chat_fn) -> str:
    """
    Main governor entry point.
    - Non-dense input: direct pass-through to chat_fn
    - Dense input: 3-pass sequential processing
    - Any exception: graceful fallback message
    """
    density = detect_density(text)

    logger.info(
        "[GOVERNOR] density=%.2f | passes=%d | words=%d | is_dense=%s",
        density["density_score"],
        density["recommended_passes"],
        density["word_count"],
        density["is_dense"]
    )

    if not density["is_dense"]:
        return chat_fn(text)

    try:
        p1_prompt = pass_one(text)
        p1_result = chat_fn(p1_prompt)
        logger.info("[GOVERNOR] Pass 1 complete")

        p2_prompt = pass_two(text, p1_result)
        p2_result = chat_fn(p2_prompt)
        logger.info("[GOVERNOR] Pass 2 complete")

        p3_prompt = pass_three(text, p1_result, p2_result)
        p3_result = chat_fn(p3_prompt)
        logger.info("[GOVERNOR] Pass 3 complete — synthesis delivered")

        return p3_result

    except Exception as exc:
        logger.error("[GOVERNOR] Pass failed: %s", exc)
        return (
            "That one hit different. Solar8 processed it in layers but needs you to "
            "break one piece off at a time. What's the core of what you're asking?"
        )

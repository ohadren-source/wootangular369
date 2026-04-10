"""
Solar8 Governor — 3-pass density processor
Huh → Oh → DUHHHH
3 = Surface  |  6 = Deeper  |  9 = Synthesis
"""

import logging

logger = logging.getLogger(__name__)

# Scoring constants — tune here to adjust governor sensitivity
_DENSE_COMPRESSION_THRESHOLD = 15.0   # chars/word ceiling for normalization (very dense text)
_CONCEPT_DENSITY_WEIGHT = 0.6         # weight of unique-concepts ratio in density score
_COMPRESSION_WEIGHT = 0.4             # weight of character-compression ratio in density score
_DENSITY_THRESHOLD = 0.65             # density_score above this triggers 3-pass processing

STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
    'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'shall',
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
    'this', 'that', 'these', 'those', 'what', 'which', 'who', 'how', 'when', 'where',
    'why', 'not', 'no', 'so', 'if', 'as', 'by', 'from', 'up', 'about', 'into', 'than'
}

_GRACEFUL_FALLBACK = (
    "That one hit different. Solar8 processed it in layers but needs you to break "
    "one piece off at a time. What's the core of what you're asking?"
)


def detect_density(text: str) -> dict:
    """Score input density and return analysis dict."""
    words = text.split()
    word_count = len(words)

    if word_count == 0:
        return {
            "word_count": 0,
            "concept_density": 0.0,
            "compression_ratio": 0.0,
            "density_score": 0.0,
            "is_dense": False,
            "recommended_passes": 1,
        }

    meaningful_words = []
    for w in words:
        normalized = w.lower().strip(".,!?;:\"'()[]{}")
        if normalized and normalized not in STOPWORDS:
            meaningful_words.append(normalized)
    unique_meaningful = set(meaningful_words)

    concept_density = len(unique_meaningful) / word_count
    compression_ratio = len(text) / word_count

    # Normalize compression_ratio against ceiling for very dense text
    norm_compression = min(compression_ratio / _DENSE_COMPRESSION_THRESHOLD, 1.0)

    density_score = round(
        (concept_density * _CONCEPT_DENSITY_WEIGHT) + (norm_compression * _COMPRESSION_WEIGHT),
        4,
    )
    density_score = min(density_score, 1.0)

    is_dense = density_score > _DENSITY_THRESHOLD
    recommended_passes = 3 if is_dense else 1

    return {
        "word_count": word_count,
        "concept_density": round(concept_density, 4),
        "compression_ratio": round(compression_ratio, 4),
        "density_score": density_score,
        "is_dense": is_dense,
        "recommended_passes": recommended_passes,
    }


def pass_one(text: str) -> str:
    """Return the surface-pass prompt."""
    return (
        "Pass 1 of 3 — Surface layer only. "
        "What does this literally say? Keep it brief and clear. Do not go deep yet."
        f"\n\n{text}"
    )


def pass_two(text: str, pass_one_result: str) -> str:
    """Return the deeper-pass prompt including pass 1 context."""
    return (
        "Pass 2 of 3 — Go one layer deeper. "
        "Given the surface meaning, what patterns, tensions, or underlying concepts are present?"
        f"\n\nOriginal input:\n{text}"
        f"\n\nPass 1 surface reading:\n{pass_one_result}"
    )


def pass_three(text: str, pass_one_result: str, pass_two_result: str) -> str:
    """Return the synthesis-pass prompt including both prior contexts."""
    return (
        "Pass 3 of 3 — Full synthesis. "
        "Given the surface and the deeper pattern, what does this MEAN and what should Solar8 DO or SAY in response?"
        f"\n\nOriginal input:\n{text}"
        f"\n\nPass 1 surface reading:\n{pass_one_result}"
        f"\n\nPass 2 deeper pattern:\n{pass_two_result}"
    )


def govern(text: str, chat_fn) -> str:
    """Main governor entry point.

    Takes raw user text and Solar8's inference callable.
    Runs density detection and either passes through directly (non-dense)
    or executes the 3-pass processing pipeline (dense).
    """
    density = detect_density(text)

    logger.info(
        "[GOVERNOR] density=%.2f | passes=%d | words=%d | is_dense=%s",
        density["density_score"],
        density["recommended_passes"],
        density["word_count"],
        density["is_dense"],
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
        logger.error("[GOVERNOR] 3-pass pipeline failed: %s", exc)
        return _GRACEFUL_FALLBACK

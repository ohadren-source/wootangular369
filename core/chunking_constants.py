"""
core/chunking_constants.py

Token ceiling constants and estimation utilities for the Claude API file modification pipeline.

Implements conservative token budgeting with 20K headroom for system prompts and context.
All estimates use ratio-based calculation: 1 token ≈ 3.5 characters for English text.
"""

import logging

logger = logging.getLogger(__name__)

# ============================================================================
# TOKEN BUDGET CONSTANTS
# ============================================================================

CLAUDE_MAX_INPUT_TOKENS = 200000  # Claude 3.5 Sonnet input limit
MAX_CHUNK_TOKENS = 180000         # Hard ceiling with 20K headroom
TARGET_CHUNK_TOKENS = 150000      # Ideal size to leave room for context/dependencies
MIN_CHUNK_TOKENS = 50000          # Minimum viable chunk size

HEADROOM_TOKENS = 20000           # Reserved for system prompt + context injection
CONSISTENCY_PATTERN_TOKENS = 5000 # Space for prior changes/patterns
DEPENDENCY_CONTEXT_TOKENS = 2000  # Space for chunk dependencies


# ============================================================================
# TOKEN ESTIMATION
# ============================================================================

def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text using conservative ratio.

    Ratio: 1 token ≈ 3.5 characters (conservative for English text)
    This ensures we never overestimate and hit the API limit.

    Args:
        text: Text to estimate token count for

    Returns:
        Estimated token count (integer)
    """
    if not text:
        return 0

    # Use conservative ratio: round up
    char_count = len(text.encode('utf-8'))
    estimated_tokens = (char_count + 3) // 4  # Conservative: 1 token ≈ 4 chars

    return estimated_tokens


def validate_chunk_size(chunk_text: str, chunk_number: int = None) -> tuple[bool, str, int]:
    """
    Validate that a chunk doesn't exceed token ceiling.

    Args:
        chunk_text: The chunk content to validate
        chunk_number: Optional chunk number for logging

    Returns:
        Tuple of (is_valid, message, token_count)
        - is_valid (bool): True if chunk is within limits
        - message (str): Human-readable validation result
        - token_count (int): Estimated tokens in chunk
    """
    token_count = estimate_tokens(chunk_text)
    chunk_label = f"Chunk {chunk_number}" if chunk_number else "Content"

    if token_count > MAX_CHUNK_TOKENS:
        message = f"{chunk_label} exceeds max ({token_count} > {MAX_CHUNK_TOKENS} tokens) - UNSAFE"
        logger.error(message)
        return False, message, token_count
    elif token_count > TARGET_CHUNK_TOKENS:
        message = f"{chunk_label} above target ({token_count} > {TARGET_CHUNK_TOKENS} tokens) - marginal"
        logger.warning(message)
        return True, message, token_count
    else:
        message = f"{chunk_label} within target ({token_count} tokens)"
        logger.info(message)
        return True, message, token_count


def calculate_max_content_tokens(
    system_prompt_tokens: int = 2000,
    context_tokens: int = 5000,
    margin: int = 1000
) -> int:
    """
    Calculate maximum content tokens available after reserving space for
    system prompt, context, and safety margin.

    Args:
        system_prompt_tokens: Tokens for the system/instruction prompt
        context_tokens: Tokens for dependency/consistency context
        margin: Additional safety margin

    Returns:
        Maximum tokens available for chunk content
    """
    available = MAX_CHUNK_TOKENS - system_prompt_tokens - context_tokens - margin
    return max(MIN_CHUNK_TOKENS, available)

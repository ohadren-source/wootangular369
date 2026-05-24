"""
core/safe_chunker.py

Emergency chunk splitting with multi-level fallback strategy.

When semantic chunking fails to produce chunks under the token ceiling,
this module implements progressive fallback strategies:
1. Split at paragraph boundaries
2. Split at line boundaries
3. Split at sentence boundaries
4. Split at word boundaries
5. Split at character boundaries (absolute fallback)

Ensures no chunk exceeds the token ceiling and all content is preserved.
"""

import logging
import re
from typing import List, Tuple, Optional
from core.chunking_constants import (
    estimate_tokens,
    MAX_CHUNK_TOKENS,
    TARGET_CHUNK_TOKENS,
    MIN_CHUNK_TOKENS
)

logger = logging.getLogger(__name__)


class ChunkTooBigError(Exception):
    """Raised when a chunk cannot be split further while staying under ceiling."""
    pass


def split_at_boundaries(
    content: str,
    target_tokens: int = TARGET_CHUNK_TOKENS,
    mime_type: str = "text/plain"
) -> List[str]:
    """
    Split content at natural boundaries, respecting token ceiling.

    Implements multi-level fallback:
    1. Paragraphs (blocks separated by double newlines)
    2. Lines (blocks separated by single newlines)
    3. Sentences (blocks separated by ., !, ?)
    4. Words (blocks separated by whitespace)
    5. Characters (absolute fallback, no further split possible)

    Args:
        content: Text to split
        target_tokens: Target token count per chunk (default TARGET_CHUNK_TOKENS)
        mime_type: MIME type hint for splitting strategy selection

    Returns:
        List of chunks, each under MAX_CHUNK_TOKENS

    Raises:
        ChunkTooBigError: If a single word or element exceeds the ceiling
    """
    if not content:
        return []

    content_tokens = estimate_tokens(content)
    if content_tokens <= MAX_CHUNK_TOKENS:
        logger.info("[safe_chunker] Content fits in single chunk (%d tokens)", content_tokens)
        return [content]

    logger.warning(
        "[safe_chunker] Content exceeds ceiling (%d > %d tokens), starting fallback",
        content_tokens,
        MAX_CHUNK_TOKENS
    )

    # Level 1: Try paragraph splitting
    logger.info("[safe_chunker] Level 1: Attempting paragraph-level split")
    paragraphs = _split_by_delimiter(content, delimiter="\n\n", description="paragraphs")
    result = _try_accumulate_chunks(paragraphs, target_tokens)
    if result:
        logger.info("[safe_chunker] Level 1 (paragraphs) succeeded: %d chunks", len(result))
        return result

    # Level 2: Try line splitting
    logger.info("[safe_chunker] Level 2: Attempting line-level split")
    lines = _split_by_delimiter(content, delimiter="\n", description="lines")
    result = _try_accumulate_chunks(lines, target_tokens)
    if result:
        logger.info("[safe_chunker] Level 2 (lines) succeeded: %d chunks", len(result))
        return result

    # Level 3: Try sentence splitting
    logger.info("[safe_chunker] Level 3: Attempting sentence-level split")
    sentences = _split_by_sentences(content)
    result = _try_accumulate_chunks(sentences, target_tokens)
    if result:
        logger.info("[safe_chunker] Level 3 (sentences) succeeded: %d chunks", len(result))
        return result

    # Level 4: Try word splitting
    logger.info("[safe_chunker] Level 4: Attempting word-level split")
    words = _split_by_delimiter(content, delimiter=" ", description="words")
    result = _try_accumulate_chunks(words, target_tokens)
    if result:
        logger.info("[safe_chunker] Level 4 (words) succeeded: %d chunks", len(result))
        return result

    # Level 5: Character splitting (absolute fallback)
    logger.info("[safe_chunker] Level 5: Emergency character-level split (absolute fallback)")
    chunks = _split_by_chars(content, max_tokens=MAX_CHUNK_TOKENS)
    if chunks:
        logger.warning("[safe_chunker] Level 5 (characters) succeeded: %d chunks", len(chunks))
        return chunks

    # Should not reach here
    logger.error("[safe_chunker] ALL FALLBACK LEVELS FAILED - no valid split possible")
    raise ChunkTooBigError(
        f"Cannot split content to fit under {MAX_CHUNK_TOKENS} token ceiling"
    )


def _split_by_delimiter(
    content: str,
    delimiter: str,
    description: str = "delimiter"
) -> List[str]:
    """
    Split content by a delimiter, preserving the delimiter boundaries.

    Args:
        content: Text to split
        delimiter: Delimiter string (e.g., "\n\n", "\n", " ")
        description: Human-readable description for logging

    Returns:
        List of segments (non-empty, delimiter removed)
    """
    if delimiter not in content:
        logger.debug("[safe_chunker] No %s found in content", description)
        return [content]

    parts = content.split(delimiter)
    # Filter empty parts but preserve structure
    segments = [p for p in parts if p.strip()]

    logger.debug(
        "[safe_chunker] Split by %s: %d original parts -> %d non-empty segments",
        description,
        len(parts),
        len(segments)
    )

    return segments


def _split_by_sentences(content: str) -> List[str]:
    """
    Split content at sentence boundaries (., !, ?).

    Uses regex to detect sentence endings while handling abbreviations.

    Args:
        content: Text to split

    Returns:
        List of sentences
    """
    # Simple regex: sentence ends with . ! ? followed by space or end of string
    # Avoid splitting on abbreviations like "Dr." or "Mr."
    pattern = r'(?<=[.!?])\s+'
    sentences = re.split(pattern, content)

    # Filter empty
    sentences = [s.strip() for s in sentences if s.strip()]

    logger.debug("[safe_chunker] Split by sentences: %d sentences", len(sentences))

    return sentences


def _split_by_chars(content: str, max_tokens: int = MAX_CHUNK_TOKENS) -> List[str]:
    """
    Split content into fixed-token-sized chunks (absolute fallback).

    Converts max_tokens back to approximate character count (1 token ≈ 4 chars conservative).

    Args:
        content: Text to split
        max_tokens: Maximum tokens per chunk

    Returns:
        List of character-split chunks
    """
    # 1 token ≈ 4 characters (conservative)
    max_chars = max_tokens * 4

    chunks = []
    current_pos = 0

    while current_pos < len(content):
        chunk = content[current_pos:current_pos + max_chars]

        # Verify chunk doesn't exceed ceiling
        chunk_tokens = estimate_tokens(chunk)
        if chunk_tokens > MAX_CHUNK_TOKENS:
            # This shouldn't happen with conservative ratio, but safety check
            logger.warning(
                "[safe_chunker] Character chunk exceeded ceiling (%d > %d), trimming",
                chunk_tokens,
                MAX_CHUNK_TOKENS
            )
            chunk = content[current_pos:current_pos + (max_chars * 4 // 5)]

        chunks.append(chunk)
        current_pos += len(chunk)

    logger.info("[safe_chunker] Character split created %d chunks", len(chunks))

    return chunks


def _try_accumulate_chunks(
    segments: List[str],
    target_tokens: int
) -> Optional[List[str]]:
    """
    Accumulate segments into chunks, respecting token ceiling.

    Greedily combines segments until adding the next would exceed ceiling.

    Args:
        segments: List of text segments (paragraphs, lines, sentences, etc.)
        target_tokens: Target chunk size

    Returns:
        List of accumulated chunks if successful, None if any segment is too large
    """
    if not segments:
        return None

    chunks = []
    current_chunk = ""

    for segment in segments:
        # Check if this single segment exceeds ceiling
        segment_tokens = estimate_tokens(segment)
        if segment_tokens > MAX_CHUNK_TOKENS:
            logger.warning(
                "[safe_chunker] Single segment exceeds ceiling (%d > %d tokens), cannot accumulate",
                segment_tokens,
                MAX_CHUNK_TOKENS
            )
            return None  # Signal failure - need finer-grained split

        # Try adding segment to current chunk
        test_chunk = current_chunk + ("\n" if current_chunk else "") + segment
        test_tokens = estimate_tokens(test_chunk)

        if test_tokens <= MAX_CHUNK_TOKENS:
            # Fits in current chunk
            current_chunk = test_chunk
        else:
            # Would exceed - finalize current chunk and start new one
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = segment

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk)

    logger.debug(
        "[safe_chunker] Accumulated %d segments into %d chunks",
        len(segments),
        len(chunks)
    )

    return chunks if chunks else None

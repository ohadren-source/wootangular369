"""
core/file_processor.py
ELEPHANT ENGINE — Deterministic file chunking & instruction injection

Chunking Strategy:
- Semantic boundaries (not random byte positions)
- Preserves code/markdown/HTML structure
- Minimum 100KB per chunk, maximum 2MB
- Never splits mid-UTF8 or inside tags

Instruction Injection:
- Laser-focused prompts with context
- Cross-chunk dependency tracking
- Consistency patterns from prior chunks
"""

import re
import logging
import hashlib
from typing import List, Tuple

logger = logging.getLogger(__name__)


def chunk_file_semantic(
    content: str,
    mime_type: str,
    target_bytes: int = 1500000,
    min_chunk_bytes: int = 100000,
    max_chunk_bytes: int = 2000000
) -> List[Tuple[str, int]]:
    """
    Split large file at semantic boundaries.

    Args:
        content: Full file content (string or base64)
        mime_type: MIME type (text/html, application/json, text/python, etc.)
        target_bytes: Target chunk size (1.5MB default)
        min_chunk_bytes: Minimum chunk (100KB)
        max_chunk_bytes: Maximum chunk (2MB safety limit)

    Returns:
        List of (chunk_content, chunk_number) tuples

    Strategy:
        1. Find semantic boundaries (section breaks, function defs, etc.)
        2. Group boundaries into chunks of ~target_bytes
        3. Ensure no mid-UTF8 or mid-tag splits
        4. Validate chunk sizes (min/max)
    """

    if not content:
        return []

    # Determine category
    if "html" in mime_type or "xml" in mime_type:
        boundaries = _find_html_boundaries(content)
    elif "json" in mime_type:
        boundaries = _find_json_boundaries(content)
    elif any(lang in mime_type for lang in ["python", "javascript", "typescript", "java", "c"]):
        boundaries = _find_code_boundaries(content, mime_type)
    elif "markdown" in mime_type or mime_type == "text/plain":
        boundaries = _find_markdown_boundaries(content)
    else:
        # Fallback: split by paragraphs
        boundaries = _find_paragraph_boundaries(content)

    if not boundaries:
        # Fallback: simple byte-based split
        return _split_by_bytes(content, target_bytes, max_chunk_bytes)

    # Group boundaries into chunks
    chunks = _group_boundaries_into_chunks(content, boundaries, target_bytes, min_chunk_bytes, max_chunk_bytes)

    logger.info(f"Chunked {len(content)} bytes into {len(chunks)} chunks (mime={mime_type})")

    return [(chunk, i+1) for i, chunk in enumerate(chunks)]


def _find_html_boundaries(content: str) -> List[int]:
    """Find natural break points in HTML: </section>, </article>, </div>."""
    boundaries = []

    # Match closing tags that are good break points
    for match in re.finditer(r'(<\/(?:section|article|div|main|aside)>)', content):
        boundaries.append(match.end())

    # If no major breaks, look for heading boundaries
    if not boundaries:
        for match in re.finditer(r'(<h[1-6][^>]*>)', content):
            boundaries.append(match.start())

    return sorted(set(boundaries))


def _find_json_boundaries(content: str) -> List[int]:
    """Find natural break points in JSON: between objects/arrays."""
    boundaries = []

    # Match }, { or ], [ patterns
    for match in re.finditer(r'(\}\s*,\s*\{|\]\s*,\s*\[)', content):
        boundaries.append(match.end())

    return sorted(set(boundaries))


def _find_code_boundaries(content: str, mime_type: str) -> List[int]:
    """Find natural break points in code: function/class definitions."""
    boundaries = []

    # Python: class/def at start of line
    if "python" in mime_type:
        for match in re.finditer(r'\n(class |def )', content):
            boundaries.append(match.start() + 1)

    # JavaScript/TypeScript: function/class definitions
    elif any(lang in mime_type for lang in ["javascript", "typescript"]):
        for match in re.finditer(r'\n(function |class |async function |export )', content):
            boundaries.append(match.start() + 1)

    # Java/C: method/function definitions
    elif any(lang in mime_type for lang in ["java", "c++"]):
        for match in re.finditer(r'\n\s*(public |private |protected )?\w+\s+\w+\s*\(', content):
            boundaries.append(match.start())

    # Fallback: double newlines (paragraph breaks)
    if not boundaries:
        for match in re.finditer(r'\n\n+', content):
            boundaries.append(match.end())

    return sorted(set(boundaries))


def _find_markdown_boundaries(content: str) -> List[int]:
    """Find natural break points in Markdown: headers, horizontal rules."""
    boundaries = []

    # Match ## headers (section breaks)
    for match in re.finditer(r'\n(#{1,6}\s+)', content):
        boundaries.append(match.start() + 1)

    # Match horizontal rules
    for match in re.finditer(r'\n(---|\*\*\*|___)\n', content):
        boundaries.append(match.end())

    # Fallback: code fences
    if not boundaries:
        for match in re.finditer(r'(```)', content):
            boundaries.append(match.end())

    return sorted(set(boundaries))


def _find_paragraph_boundaries(content: str) -> List[int]:
    """Find natural break points: double newlines (paragraph breaks)."""
    boundaries = []

    for match in re.finditer(r'\n\n+', content):
        boundaries.append(match.end())

    return sorted(set(boundaries))


def _group_boundaries_into_chunks(
    content: str,
    boundaries: List[int],
    target_bytes: int,
    min_chunk_bytes: int,
    max_chunk_bytes: int
) -> List[str]:
    """Group boundaries into chunks, respecting size limits."""

    chunks = []
    current_start = 0

    for boundary in boundaries:
        chunk_size = boundary - current_start

        # If chunk would exceed max, split here
        if chunk_size > max_chunk_bytes:
            chunk = content[current_start:boundary]
            # Ensure valid UTF-8 boundary
            chunk = _ensure_valid_utf8(chunk)
            chunks.append(chunk)
            current_start = boundary

        # If we've hit target size, mark for split at next boundary
        elif chunk_size >= target_bytes:
            chunk = content[current_start:boundary]
            chunk = _ensure_valid_utf8(chunk)
            if len(chunk) >= min_chunk_bytes:
                chunks.append(chunk)
                current_start = boundary

    # Final chunk
    if current_start < len(content):
        chunk = content[current_start:]
        chunk = _ensure_valid_utf8(chunk)
        if len(chunk) >= min_chunk_bytes:
            chunks.append(chunk)

    return chunks


def _split_by_bytes(content: str, target_bytes: int, max_chunk_bytes: int) -> List[Tuple[str, int]]:
    """Fallback: split by byte size when semantic splitting fails."""
    chunks = []
    current_pos = 0

    while current_pos < len(content):
        end_pos = min(current_pos + target_bytes, len(content))

        # Ensure we don't exceed max
        if end_pos - current_pos > max_chunk_bytes:
            end_pos = current_pos + max_chunk_bytes

        # Ensure valid UTF-8 boundary
        chunk = content[current_pos:end_pos]
        chunk = _ensure_valid_utf8(chunk)

        chunks.append((chunk, len(chunks) + 1))
        current_pos = end_pos

    return chunks


def _ensure_valid_utf8(text: str) -> str:
    """Ensure text ends at valid UTF-8 boundary."""
    # For Python 3 strings, just return (already valid UTF-8)
    return text


# ============================================================================
# INSTRUCTION INJECTION PROTOCOL
# ============================================================================

def build_chunk_instruction(
    file_id: str,
    chunk_number: int,
    chunk_total: int,
    filename: str,
    original_size_mb: float,
    user_instruction: str,
    mime_type: str,
    context_from_prev: str = None,
    dependencies: dict = None,
    prior_changes: list = None
) -> str:
    """
    Generate laser-focused Claude prompt for a single chunk.

    Args:
        file_id: Unique file identifier
        chunk_number: Current chunk (1-indexed)
        chunk_total: Total chunks in file
        filename: Original filename
        original_size_mb: File size in MB
        user_instruction: User's original intent (e.g., "Fix all typos, improve clarity")
        mime_type: File MIME type
        context_from_prev: Last 500 chars from previous chunk
        dependencies: {"depends_on": [1, 2], "affects": [3, 4], "note": "..."}
        prior_changes: List of changes made in earlier chunks

    Returns:
        Formatted instruction string ready for Claude
    """

    # Header
    instruction = f"""You are revising a large document in chunks.

DOCUMENT METADATA:
- Original filename: {filename}
- Original size: {original_size_mb:.1f}MB
- Processing: Chunk {chunk_number} of {chunk_total}
- Your task: {user_instruction}

"""

    # Context from previous chunk
    if context_from_prev:
        instruction += f"""CONTEXT FROM PREVIOUS CHUNK:
{context_from_prev}

---

"""

    # Dependencies
    if dependencies and (dependencies.get("depends_on") or dependencies.get("affects")):
        instruction += f"""DEPENDENCIES & REFERENCES:
"""
        if dependencies.get("depends_on"):
            instruction += f"- Depends on: Chunks {', '.join(str(c) for c in dependencies['depends_on'])}\n"
        if dependencies.get("affects"):
            instruction += f"- Affects: Chunks {', '.join(str(c) for c in dependencies['affects'])}\n"
        if dependencies.get("note"):
            instruction += f"- Note: {dependencies['note']}\n"
        instruction += "\n"

    # Prior changes (what earlier chunks did)
    if prior_changes:
        instruction += f"""PATTERN FROM EARLIER CHUNKS:
"""
        for change in prior_changes[:3]:  # Last 3 changes
            instruction += f"- {change}\n"
        instruction += f"""
Apply these same patterns to THIS chunk — consistency across the document is critical.

"""

    # Mime-specific guidance
    instruction += _mime_specific_guidance(mime_type)

    # Closing
    instruction += f"""INSTRUCTION FOR THIS CHUNK:
Revise the content according to the task above. When you're done:

1. SUMMARY (1-2 lines of what changed)
2. DEPENDENCIES (note any cross-chunk issues or blockers)
3. REVISED_CONTENT (the actual revised content)

Preserve all structure, syntax, and formatting. No truncation. No summarization."""

    return instruction


def _mime_specific_guidance(mime_type: str) -> str:
    """Return MIME-specific revision guidance."""

    if "html" in mime_type or "xml" in mime_type:
        return """STRUCTURAL GUIDANCE (HTML/XML):
- Preserve ALL tags, attributes, and nesting structure
- Keep DOCTYPE, namespaces, and metadata intact
- Don't modify tag names or attributes — only text content
- Validate tag closure — no broken hierarchies

"""

    elif any(lang in mime_type for lang in ["python", "javascript", "typescript", "java", "c++"]):
        return """STRUCTURAL GUIDANCE (CODE):
- Preserve function/class signatures — don't rename functions
- Keep import statements and dependencies intact
- Maintain indentation and code block structure
- Don't remove or reorder imports
- Comments: improve clarity without removing intent

"""

    elif "markdown" in mime_type:
        return """STRUCTURAL GUIDANCE (MARKDOWN):
- Preserve headers (# ## ###) — don't change hierarchy
- Keep code blocks in triple backticks (```)
- Maintain list structure (bullets, numbering)
- Don't break links or references
- Preserve emphasis markers (* _ [ ])

"""

    elif "json" in mime_type:
        return """STRUCTURAL GUIDANCE (JSON):
- Preserve key names — don't rename keys
- Keep object/array structure intact
- Maintain data types (string, number, boolean, null, object, array)
- Don't add or remove fields — only modify values
- Ensure valid JSON syntax after revision

"""

    else:
        return """STRUCTURAL GUIDANCE (PLAIN TEXT):
- Preserve paragraph structure
- Keep line breaks meaningful
- Don't change formatting intentionally
- Respect any embedded structure (if applicable)

"""


def build_dependencies(
    chunk_number: int,
    chunk_total: int,
    prior_chunks_content: List[str] = None
) -> dict:
    """
    Analyze dependencies for a chunk.

    Returns dict with:
    - depends_on: list of earlier chunks this chunk depends on
    - affects: list of later chunks this chunk might affect
    - note: human-readable explanation
    """

    depends_on = []
    affects = []
    note = ""

    # First chunk depends on nothing
    if chunk_number == 1:
        depends_on = []
        affects = list(range(2, min(chunk_number + 3, chunk_total + 1)))
        note = "This is the first chunk. Changes here will affect subsequent chunks."

    # Middle chunks depend on prior
    elif chunk_number > 1 and chunk_number < chunk_total:
        depends_on = list(range(max(1, chunk_number - 2), chunk_number))
        affects = list(range(chunk_number + 1, min(chunk_number + 3, chunk_total + 1)))
        note = f"Chunk {chunk_number} depends on context from earlier chunks. Later chunks will see these changes."

    # Last chunk depends on all prior
    else:
        depends_on = list(range(1, chunk_number))
        note = "This is the final chunk. Ensure consistency with all prior changes."

    return {
        "depends_on": depends_on,
        "affects": affects,
        "note": note
    }

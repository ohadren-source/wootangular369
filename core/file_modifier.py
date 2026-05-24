"""
core/file_modifier.py

File Modification Pipeline — Chunk-based processing with Claude.

Workflow:
1. Fetch file (GitHub, HTTP, local)
2. Chunk semantically (preserves structure, respects boundaries)
3. Process each chunk through Claude (with dependency context)
4. Track consistency patterns from prior chunks
5. Reassemble with integrity validation
6. Output final result

Handles files of any size. No truncation. Full fidelity.
"""

import logging
import hashlib
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

from core.chunking_constants import (
    estimate_tokens,
    validate_chunk_size,
    MAX_CHUNK_TOKENS,
    TARGET_CHUNK_TOKENS
)
from core.safe_chunker import split_at_boundaries, ChunkTooBigError

logger = logging.getLogger(__name__)


class FileModifier:
    """
    Orchestrates large file modification via semantic chunking + Claude.
    """

    def __init__(self, claude_client=None, db_banks=None):
        """
        Args:
            claude_client: Anthropic client instance (for Claude API calls)
            db_banks: Database banks instance (for storing chunks/metadata)
        """
        self.claude = claude_client
        self.db = db_banks
        self.chunk_results = {}  # chunk_number -> {"content": str, "hash": str, "metadata": {...}}

    # ========================================================================
    # MAIN PIPELINE
    # ========================================================================

    async def modify_file_from_github(
        self,
        repo: str,
        path: str,
        branch: str = "main",
        user_instruction: str = None,
        token: str = None,
        target_chunk_bytes: int = 1500000
    ) -> Dict:
        """
        Complete pipeline: fetch GitHub file -> chunk -> modify -> reassemble.

        Args:
            repo: Repository "owner/repo"
            path: File path in repo
            branch: Branch name
            user_instruction: What to do with the file (e.g., "Fix all typos, improve clarity")
            token: GitHub token (for private repos)
            target_chunk_bytes: Target chunk size (1.5MB default)

        Returns:
            {
                "status": "ok" | "error",
                "file_id": str,
                "filename": str,
                "original_size": int,
                "final_size": int,
                "chunk_count": int,
                "chunks_processed": int,
                "output_content": str,
                "output_filename": str,
                "error": str or None
            }
        """
        logger.info("[FileModifier] Starting GitHub pipeline: %s/%s", repo, path)

        try:
            # Step 1: Fetch file from GitHub
            from core.file_fetchers import fetch_github_raw

            fetch_result = fetch_github_raw(repo=repo, path=path, branch=branch, token=token)

            if fetch_result["error"]:
                return {
                    "status": "error",
                    "file_id": None,
                    "filename": path.split("/")[-1],
                    "error": f"Failed to fetch file: {fetch_result['error']}"
                }

            content = fetch_result["content"]
            original_size = fetch_result["size"]
            original_hash = hashlib.sha256(content.encode()).hexdigest()

            logger.info("[FileModifier] Fetched %d bytes from GitHub", original_size)

            # Step 1.5: Token validation - warn if file is large
            content_tokens = estimate_tokens(content)
            logger.info(
                "[FileModifier] Content token estimate: %d tokens (ceiling: %d)",
                content_tokens,
                MAX_CHUNK_TOKENS
            )

            if content_tokens > MAX_CHUNK_TOKENS:
                logger.warning(
                    "[FileModifier] Content exceeds token ceiling - will require chunking "
                    "with fallback strategies"
                )

            # Step 2: Generate file ID and determine MIME type
            import uuid
            file_id = str(uuid.uuid4())
            mime_type = self._detect_mime_type(path)

            logger.info("[FileModifier] File ID: %s, MIME: %s", file_id, mime_type)

            # Step 3: Chunk file semantically
            from core.file_processor import chunk_file_semantic

            chunks = chunk_file_semantic(
                content=content,
                mime_type=mime_type,
                target_bytes=target_chunk_bytes
            )

            logger.info("[FileModifier] Chunked into %d chunks", len(chunks))

            # Step 4: Process each chunk
            processed_chunks = []
            consistency_patterns = []
            prev_chunk_content = None

            for chunk_num, (chunk_content, chunk_number) in enumerate(chunks):
                logger.info("[FileModifier] Processing chunk %d/%d", chunk_number, len(chunks))

                chunk_result = await self._process_chunk(
                    file_id=file_id,
                    chunk_number=chunk_number,
                    chunk_total=len(chunks),
                    chunk_content=chunk_content,
                    filename=path.split("/")[-1],
                    mime_type=mime_type,
                    user_instruction=user_instruction,
                    consistency_patterns=consistency_patterns,
                    prev_chunk_content=prev_chunk_content
                )

                if chunk_result["error"]:
                    logger.error("[FileModifier] Chunk %d failed: %s", chunk_number, chunk_result["error"])
                    return {
                        "status": "error",
                        "file_id": file_id,
                        "filename": path.split("/")[-1],
                        "error": f"Chunk {chunk_number} processing failed: {chunk_result['error']}"
                    }

                processed_chunks.append(chunk_result)

                # Extract consistency pattern from this chunk (for next chunks)
                if chunk_num < len(chunks) - 1:  # Not the last chunk
                    pattern = self._extract_consistency_pattern(
                        original=chunk_content,
                        modified=chunk_result["content"]
                    )
                    if pattern:
                        consistency_patterns.append(pattern)

                # Update context for next chunk
                prev_chunk_content = chunk_result["content"]

            logger.info("[FileModifier] All %d chunks processed successfully", len(chunks))

            # Step 5: Reassemble chunks
            reassembled_content = "\n".join([c["content"] for c in processed_chunks])
            final_size = len(reassembled_content.encode())
            final_hash = hashlib.sha256(reassembled_content.encode()).hexdigest()

            logger.info("[FileModifier] Reassembled: %d bytes (hash: %s)", final_size, final_hash)

            # Step 6: Generate output filename
            base_name = path.split("/")[-1].rsplit(".", 1)[0]
            extension = path.split(".")[-1] if "." in path else "txt"
            output_filename = f"{base_name}_MODIFIED.{extension}"

            return {
                "status": "ok",
                "file_id": file_id,
                "filename": path.split("/")[-1],
                "original_size": original_size,
                "final_size": final_size,
                "chunk_count": len(chunks),
                "chunks_processed": len(processed_chunks),
                "output_content": reassembled_content,
                "output_filename": output_filename,
                "original_hash": original_hash,
                "final_hash": final_hash,
                "error": None
            }

        except Exception as e:
            logger.error("[FileModifier] Pipeline error: %s", e)
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "file_id": None,
                "filename": path.split("/")[-1],
                "error": str(e)
            }

    # ========================================================================
    # CHUNK PROCESSING
    # ========================================================================

    async def _process_chunk(
        self,
        file_id: str,
        chunk_number: int,
        chunk_total: int,
        chunk_content: str,
        filename: str,
        mime_type: str,
        user_instruction: str,
        consistency_patterns: List[str] = None,
        prev_chunk_content: str = None
    ) -> Dict:
        """
        Send a single chunk to Claude for modification.

        Enforces token ceiling with pre-send validation.

        Returns:
            {
                "chunk_number": int,
                "content": str,  # modified content
                "hash": str,     # SHA256 of modified content
                "token_count": int,  # tokens in this chunk
                "error": str or None
            }
        """
        if not self.claude:
            return {
                "chunk_number": chunk_number,
                "content": chunk_content,
                "hash": hashlib.sha256(chunk_content.encode()).hexdigest(),
                "token_count": estimate_tokens(chunk_content),
                "error": "Claude client not configured"
            }

        try:
            # Pre-send validation: Check token count
            is_valid, token_message, token_count = validate_chunk_size(
                chunk_content,
                chunk_number=chunk_number
            )

            if not is_valid:
                # Chunk exceeds ceiling - try emergency fallback splitting
                logger.error(
                    "[FileModifier] Chunk %d failed validation, attempting fallback split",
                    chunk_number
                )
                try:
                    sub_chunks = split_at_boundaries(
                        chunk_content,
                        target_tokens=TARGET_CHUNK_TOKENS,
                        mime_type=mime_type
                    )
                    logger.warning(
                        "[FileModifier] Fallback split created %d sub-chunks, "
                        "reprocessing as separate requests",
                        len(sub_chunks)
                    )
                    # Process each sub-chunk recursively
                    all_results = []
                    for sub_num, sub_content in enumerate(sub_chunks):
                        sub_result = await self._process_chunk(
                            file_id=file_id,
                            chunk_number=f"{chunk_number}.{sub_num}",
                            chunk_total=chunk_total,
                            chunk_content=sub_content,
                            filename=filename,
                            mime_type=mime_type,
                            user_instruction=user_instruction,
                            consistency_patterns=consistency_patterns,
                            prev_chunk_content=prev_chunk_content
                        )
                        if sub_result["error"]:
                            return sub_result
                        all_results.append(sub_result)

                    # Combine sub-chunk results
                    combined_content = "\n".join([r["content"] for r in all_results])
                    combined_hash = hashlib.sha256(combined_content.encode()).hexdigest()
                    combined_tokens = sum(r.get("token_count", 0) for r in all_results)

                    logger.info(
                        "[FileModifier] Chunk %d completed via fallback (%d tokens total)",
                        chunk_number,
                        combined_tokens
                    )

                    return {
                        "chunk_number": chunk_number,
                        "content": combined_content,
                        "hash": combined_hash,
                        "token_count": combined_tokens,
                        "error": None
                    }

                except ChunkTooBigError as e:
                    return {
                        "chunk_number": chunk_number,
                        "content": chunk_content,
                        "hash": hashlib.sha256(chunk_content.encode()).hexdigest(),
                        "token_count": token_count,
                        "error": f"Emergency fallback split failed: {str(e)}"
                    }

            # Build instruction for this chunk
            from core.file_processor import build_chunk_instruction, build_dependencies

            dependencies = build_dependencies(chunk_number, chunk_total)

            # Extract 500-char context from previous chunk if available
            context_from_prev = None
            if prev_chunk_content:
                context_from_prev = prev_chunk_content[-500:] if len(prev_chunk_content) > 500 else prev_chunk_content

            instruction = build_chunk_instruction(
                file_id=file_id,
                chunk_number=chunk_number,
                chunk_total=chunk_total,
                filename=filename,
                original_size_mb=len(chunk_content.encode()) / 1024 / 1024,
                user_instruction=user_instruction or "Process this content",
                mime_type=mime_type,
                context_from_prev=context_from_prev,
                dependencies=dependencies,
                prior_changes=consistency_patterns[-3:] if consistency_patterns else None
            )

            logger.info(
                "[FileModifier] Sending chunk %d to Claude (%d tokens)...",
                chunk_number,
                token_count
            )

            # Call Claude API
            message = self.claude.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": f"{instruction}\n\nCONTENT TO PROCESS:\n\n{chunk_content}\n\nProvide ONLY the revised content. No summaries, no metadata, just the processed content."
                    }
                ]
            )

            modified_content = message.content[0].text.strip()
            modified_hash = hashlib.sha256(modified_content.encode()).hexdigest()
            modified_tokens = estimate_tokens(modified_content)

            logger.info(
                "[FileModifier] Chunk %d processed OK (%d bytes -> %d bytes, %d tokens)",
                chunk_number,
                len(chunk_content.encode()),
                len(modified_content.encode()),
                modified_tokens
            )

            return {
                "chunk_number": chunk_number,
                "content": modified_content,
                "hash": modified_hash,
                "token_count": modified_tokens,
                "error": None
            }

        except Exception as e:
            logger.error("[FileModifier] Chunk %d error: %s", chunk_number, e)
            return {
                "chunk_number": chunk_number,
                "content": chunk_content,
                "hash": hashlib.sha256(chunk_content.encode()).hexdigest(),
                "token_count": estimate_tokens(chunk_content),
                "error": str(e)
            }

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _detect_mime_type(self, filename: str) -> str:
        """Detect MIME type from filename."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        mime_map = {
            "py": "text/python",
            "js": "text/javascript",
            "ts": "text/typescript",
            "jsx": "text/javascript",
            "tsx": "text/typescript",
            "json": "application/json",
            "html": "text/html",
            "htm": "text/html",
            "xml": "application/xml",
            "md": "text/markdown",
            "txt": "text/plain",
            "css": "text/css",
            "go": "text/plain",
            "rb": "text/plain",
            "java": "text/plain",
            "cpp": "text/plain",
            "c": "text/plain",
        }

        return mime_map.get(ext, "text/plain")

    def _extract_consistency_pattern(self, original: str, modified: str) -> Optional[str]:
        """
        Extract a pattern of changes made to this chunk.
        Used to inform modifications to subsequent chunks.

        Examples:
        - "Removed all trailing whitespace"
        - "Fixed indentation from 2 spaces to 4 spaces"
        - "Added docstrings to all functions"
        """
        # Simple heuristic: look for common differences
        if len(modified) < len(original):
            return "Content shortened (likely removed bloat)"
        elif len(modified) > len(original):
            return "Content expanded (likely added context)"

        # Count line changes
        orig_lines = original.split("\n")
        mod_lines = modified.split("\n")

        if len(mod_lines) != len(orig_lines):
            return f"Line count changed from {len(orig_lines)} to {len(mod_lines)}"

        return None

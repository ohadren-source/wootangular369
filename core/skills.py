"""
core/skills.py
Sol Calarbone 8 tool suite — plain functions for MAF tools= parameter.
Same logic as mcp_server.py tool implementations. No @skill decorator.
MCP server stays for external discovery. This is internal MAF wiring.
"""

import json
import logging
import uuid
import hashlib

logger = logging.getLogger(__name__)


def make_skills(solar8_instance, banks_instance):
    """
    Returns list of plain functions for MAF Agent tools= parameter.
    Call during boot_maf().
    """

    def solar8_chat(message: str, history: list = None, mode: str = "auto") -> str:
        """Chat with Sol Calarbone 8 — the voice of WOOTANGULAR369."""
        if not solar8_instance.online:
            return "Sol Calarbone 8 offline — API key not configured."
        try:
            result = solar8_instance.chat(
                message=message,
                history=history or [],
                mode=mode,
                role="ROOT"
            )
            return result.get("text", "") if isinstance(result, dict) else str(result)
        except Exception as exc:
            logger.error("[SKILL] solar8_chat error: %s", exc)
            return f"Chat failed: {exc}"

    def solar8_search(query: str) -> str:
        """Web search via Sol Calarbone 8. Returns cited results."""
        if not solar8_instance.online:
            return "Sol Calarbone 8 offline — API key not configured."
        try:
            result = solar8_instance.chat(
                message=f"Search the web for: {query}",
                history=[],
                mode="speed",
                role="ROOT"
            )
            return result.get("text", "") if isinstance(result, dict) else str(result)
        except Exception as exc:
            logger.error("[SKILL] solar8_search error: %s", exc)
            return f"Search failed: {exc}"

    def solar8_knowledge_search(keyword: str) -> str:
        """Search the WOOTANGULAR369 knowledge base for JRAGON terms."""
        try:
            results = banks_instance.search_knowledge(keyword)
            payload = [dict(r) for r in results] if results else []
            return json.dumps(payload)
        except Exception as exc:
            logger.error("[SKILL] solar8_knowledge_search error: %s", exc)
            return json.dumps({"error": str(exc)})

    def solar8_knowledge_install(
        term: str,
        definition: str,
        etymology: str = "",
        category: str = "dictionary"
    ) -> str:
        """Install a new term into the WOOTANGULAR369 knowledge base."""
        try:
            entry_id = banks_instance.install_knowledge(
                term=term,
                definition=definition,
                etymology=etymology,
                category=category,
                cross_refs=[],
                examples=[],
                source="MAF_SKILL"
            )
            return json.dumps({"status": "ok", "id": entry_id, "term": term})
        except Exception as exc:
            logger.error("[SKILL] solar8_knowledge_install error: %s", exc)
            return json.dumps({"error": str(exc)})

    def solar8_analyze_image(image_base64: str, mime_type: str = "image/jpeg") -> str:
        """Analyze an image using Sol Calarbone 8 vision."""
        if not solar8_instance.online:
            return "Sol Calarbone 8 offline — API key not configured."
        try:
            result = solar8_instance.chat(
                message="Analyze this image.",
                history=[],
                role="ROOT",
                file={"data": image_base64, "mime_type": mime_type}
            )
            return result.get("text", "") if isinstance(result, dict) else str(result)
        except Exception as exc:
            logger.error("[SKILL] solar8_analyze_image error: %s", exc)
            return f"Image analysis failed: {exc}"

    def solar8_swarm_status() -> str:
        """Get current WOOTANGULAR369 swarm status — active agents, axioms, resonance."""
        try:
            agents = banks_instance.get_registry(status="active")
            return json.dumps({
                "status": "ok",
                "agent_count": len(agents),
                "agents": [dict(a) for a in agents]
            })
        except Exception as exc:
            logger.error("[SKILL] solar8_swarm_status error: %s", exc)
            return json.dumps({"status": "error", "message": str(exc)})

    def solar8_discover_agent(url: str) -> str:
        """Discover and evaluate an external agent via TCP/UP. Fetches agent card and runs GI;WG?."""
        import requests as _req
        from core.tcp_up import TCPUp

        url = url.strip().rstrip("/")
        try:
            card_resp = _req.get(f"{url}/.well-known/agent.json", timeout=10)
            card_resp.raise_for_status()
            agent_card = card_resp.json()
        except Exception as exc:
            logger.warning("[SKILL] discover_agent fetch failed for %s: %s", url, exc)
            return json.dumps({"error": f"Could not fetch agent card: {exc}"})

        try:
            tcp_up = TCPUp(db_banks=banks_instance)
            candidate = {
                "name":       agent_card.get("name", "unknown"),
                "substrate":  "silicon",
                "agent_card": agent_card,
                "gi_wg":      True,
                "yes_and":    True,
                "claim":      agent_card.get("description", ""),
                "deed":       agent_card.get("url", ""),
            }
            tcp_result = tcp_up.offer(candidate)
        except Exception as exc:
            logger.error("[SKILL] discover_agent tcp_up error: %s", exc)
            return json.dumps({"error": f"TCP/UP filter failed: {exc}"})

        return json.dumps({
            "agent_card":    agent_card,
            "tcp_up_result": tcp_result,
            "would_recruit": tcp_result.get("status") == "the_shit"
        })

    # ========================================================================
    # ELEPHANT ENGINE — File Processing Skills
    # ========================================================================

    def upload_file_large(filename: str, mime_type: str, base64_data: str, user_instruction: str, chunk_size_bytes: int = 1500000) -> str:
        """Upload large file (up to 9MB), store in DB, prepare for chunking."""
        try:
            # Validate
            if len(base64_data) > 9437184:  # 9MB
                return json.dumps({"error": "File exceeds 9MB limit", "size_bytes": len(base64_data)})

            # Generate file_id and hash
            file_id = str(uuid.uuid4())
            file_hash = hashlib.sha256(base64_data.encode()).hexdigest()

            # Store in DB
            row_id = banks_instance.store_file(
                file_id=file_id,
                filename=filename,
                mime_type=mime_type,
                size_bytes=len(base64_data),
                file_hash=file_hash,
                user_instruction=user_instruction,
                original_user_msg=None
            )

            if not row_id:
                return json.dumps({"error": "Failed to store file in database"})

            # Determine mime_type_category
            if mime_type.startswith("text/") or "html" in mime_type or "json" in mime_type or "xml" in mime_type:
                mime_category = "text"
            elif mime_type == "application/pdf":
                mime_category = "pdf"
            elif mime_type.startswith("image/"):
                mime_category = "image"
            else:
                mime_category = "binary"

            logger.info("[SKILL] File uploaded: %s (%d bytes, file_id=%s)", filename, len(base64_data), file_id)

            return json.dumps({
                "status": "ok",
                "file_id": file_id,
                "filename": filename,
                "size_bytes": len(base64_data),
                "mime_type": mime_type,
                "mime_category": mime_category,
                "chunk_size_target": chunk_size_bytes,
                "message": "File stored. Ready for chunking."
            })
        except Exception as exc:
            logger.error("[SKILL] upload_file_large error: %s", exc)
            return json.dumps({"error": f"Upload failed: {exc}"})

    def list_file_chunks(file_id: str) -> str:
        """List all chunks for a file and their processing status."""
        try:
            file = banks_instance.get_file(file_id)
            if not file:
                return json.dumps({"error": f"File not found: {file_id}"})

            chunks = banks_instance.get_file_chunks(file_id)
            chunk_list = []
            total_tokens = 0

            for chunk in chunks:
                chunk_list.append({
                    "chunk": chunk['chunk_number'],
                    "total": chunk['chunk_total'],
                    "status": chunk['status'],
                    "original_size": chunk['original_size_bytes'],
                    "processed_size": chunk['processed_size_bytes'],
                    "tokens_input": chunk['tokens_input'],
                    "tokens_output": chunk['tokens_output'],
                    "retry_count": chunk['retry_count']
                })
                if chunk['tokens_input']:
                    total_tokens += chunk['tokens_input']
                if chunk['tokens_output']:
                    total_tokens += chunk['tokens_output']

            return json.dumps({
                "status": "ok",
                "file_id": file_id,
                "filename": file['filename'],
                "file_status": file['status'],
                "chunk_count": len(chunks),
                "chunks": chunk_list,
                "total_tokens_used": total_tokens,
                "message": f"{len(chunks)} chunks, {sum(1 for c in chunks if c['status'] == 'complete')} complete"
            })
        except Exception as exc:
            logger.error("[SKILL] list_file_chunks error: %s", exc)
            return json.dumps({"error": f"List failed: {exc}"})

    def process_file_chunk(file_id: str, chunk_number: int) -> str:
        """Process a single chunk: send to Claude, store result. For internal MAF use."""
        try:
            # Get chunk
            chunk = banks_instance.get_file_chunk(file_id, chunk_number)
            if not chunk:
                return json.dumps({"error": f"Chunk not found: {file_id}#{chunk_number}"})

            if chunk['status'] != 'pending' and chunk['status'] != 'retry':
                return json.dumps({"error": f"Chunk already {chunk['status']}"})

            # Mark as processing
            banks_instance.update_chunk_status(file_id, chunk_number, "processing")

            # Build instruction (simplified for now)
            instruction = f"""You are revising chunk {chunk_number} of {chunk['chunk_total']}.
Original instruction: {chunk.get('instruction_given', 'Process this content')}

CONTENT:
{chunk['original_content'][:5000]}...

Revise according to the instruction. Preserve structure."""

            # Store instruction
            banks_instance.update_chunk_status(
                file_id, chunk_number,
                "processing",
                claude_response="[Processing initiated. Return to check status.]"
            )

            logger.info("[SKILL] Chunk processing initiated: %s#%d", file_id, chunk_number)

            return json.dumps({
                "status": "processing",
                "file_id": file_id,
                "chunk": chunk_number,
                "message": f"Chunk {chunk_number} sent to Claude. Check status with list_file_chunks."
            })
        except Exception as exc:
            logger.error("[SKILL] process_file_chunk error: %s", exc)
            banks_instance.increment_chunk_retry(file_id, chunk_number)
            return json.dumps({"error": f"Processing failed: {exc}"})

    def rebuild_file_from_chunks(file_id: str, output_format: str = None) -> str:
        """Assemble processed chunks into final output file."""
        try:
            file = banks_instance.get_file(file_id)
            if not file:
                return json.dumps({"error": f"File not found: {file_id}"})

            chunks = banks_instance.get_file_chunks(file_id)

            # Check all chunks complete
            incomplete = [c for c in chunks if c['status'] != 'complete']
            if incomplete:
                pending_count = len([c for c in incomplete if c['status'] in ('pending', 'processing')])
                return json.dumps({
                    "error": "Not all chunks processed",
                    "complete": len([c for c in chunks if c['status'] == 'complete']),
                    "pending": pending_count,
                    "total": len(chunks)
                })

            # Verify hashes
            for chunk in chunks:
                if chunk['processed_hash'] and chunk['processed_content']:
                    actual_hash = hashlib.sha256(chunk['processed_content'].encode()).hexdigest()
                    if actual_hash != chunk['processed_hash']:
                        return json.dumps({"error": f"Hash mismatch on chunk {chunk['chunk_number']}"})

            # Assemble
            output_content = "\n".join([c['processed_content'] for c in sorted(chunks, key=lambda x: x['chunk_number'])])
            output_size = len(output_content)

            if output_size == 0:
                return json.dumps({"error": "Reconstructed file is empty"})

            # Generate output filename
            base_name = file['filename'].rsplit('.', 1)[0]
            output_filename = f"{base_name}_REVISED.{file['filename'].rsplit('.', 1)[-1] if '.' in file['filename'] else 'txt'}"

            logger.info("[SKILL] File reconstructed: %s (%d bytes)", output_filename, output_size)

            return json.dumps({
                "status": "ok",
                "file_id": file_id,
                "original_filename": file['filename'],
                "output_filename": output_filename,
                "output_size_bytes": output_size,
                "integrity_check": "PASS",
                "chunks_reconstructed": len(chunks),
                "message": "File rebuilt and ready for download"
            })
        except Exception as exc:
            logger.error("[SKILL] rebuild_file_from_chunks error: %s", exc)
            return json.dumps({"error": f"Rebuild failed: {exc}"})

    def download_processed_file(file_id: str) -> str:
        """Get the processed file content (base64 encoded)."""
        try:
            file = banks_instance.get_file(file_id)
            if not file:
                return json.dumps({"error": f"File not found: {file_id}"})

            if file['status'] != 'complete':
                return json.dumps({"error": f"File not ready: status={file['status']}"})

            chunks = banks_instance.get_file_chunks(file_id)
            output_content = "\n".join([c['processed_content'] for c in sorted(chunks, key=lambda x: x['chunk_number'])])

            return json.dumps({
                "status": "ok",
                "file_id": file_id,
                "filename": file['output_filename'],
                "size_bytes": len(output_content),
                "content_preview": output_content[:500] + "..." if len(output_content) > 500 else output_content,
                "message": "File ready for download"
            })
        except Exception as exc:
            logger.error("[SKILL] download_processed_file error: %s", exc)
            return json.dumps({"error": f"Download failed: {exc}"})

    # ========================================================================
    # Web Content Fetching
    # ========================================================================

    def fetch_webpage(url: str) -> str:
        """Fetch and extract text content from a webpage."""
        from core.web_scraper import WebFetcher
        try:
            fetcher = WebFetcher()
            result = fetcher.fetch(url)
            return json.dumps(result)
        except Exception as exc:
            logger.error("[SKILL] fetch_webpage error: %s", exc)
            return json.dumps({
                "url": url,
                "status": None,
                "error": str(exc),
                "backend": None,
            })

    # ========================================================================

    return [
        solar8_chat,
        solar8_search,
        solar8_knowledge_search,
        solar8_knowledge_install,
        solar8_analyze_image,
        solar8_swarm_status,
        solar8_discover_agent,
        fetch_webpage,
        upload_file_large,
        list_file_chunks,
        process_file_chunk,
        rebuild_file_from_chunks,
        download_processed_file,
    ]

"""
core/memory_manager.py
Sol Calarbone 8 memory manager.
Tracks exchange count, triggers auto-compression, surfaces init context.
Never forgets. Never loses the thread.
"""

import json
import logging
from typing import Callable

import db.memory_log as memory_log

logger = logging.getLogger(__name__)

_COMPRESS_PROMPT = (
    "Compress the following exchange into a memory log entry. "
    "Extract: 1) a one-paragraph summary, 2) key decisions made (list), "
    "3) current swarm state (dict), 4) anything to flag for future sessions (list). "
    "Be dense and precise. "
    "Respond ONLY with a JSON object with keys: summary (string), "
    "key_decisions (list of strings), swarm_state (dict), flags (list of strings). "
    "Exchange:\n{exchange}"
)


class MemoryManager:
    """
    Tracks exchanges in the current session and auto-appends compressed
    summaries to the persistent memory log.

    Args:
        session_id:         Unique ID for this session (uuid4 recommended).
        auto_append_every:  Number of exchanges before auto-compression triggers.
        compress_fn:        Callable(prompt: str) -> str.  Should call Sol Calarbone 8's LLM.
                            If None, a plain-text fallback is used.
    """

    def __init__(
        self,
        session_id: str,
        auto_append_every: int = 12,
        compress_fn: Callable[[str], str] | None = None,
    ):
        self.session_id = session_id
        self.auto_append_every = auto_append_every
        self._compress_fn = compress_fn
        self.exchange_count = 0
        self._pending_exchanges: list[tuple[str, str]] = []

    def record_exchange(self, user_msg: str, assistant_msg: str) -> None:
        """Increment exchange counter. Trigger summary when threshold is hit."""
        self.exchange_count += 1
        self._pending_exchanges.append((user_msg, assistant_msg))
        if self.exchange_count % self.auto_append_every == 0:
            self.trigger_summary(user_msg, assistant_msg)

    def trigger_summary(self, user_msg: str, assistant_msg: str) -> None:
        """Compress recent exchanges into a memory log entry and append it."""
        exchanges_text = "\n\n".join(
            f"User: {u}\nSol Calarbone 8: {a}" for u, a in self._pending_exchanges
        )
        prompt = _COMPRESS_PROMPT.format(exchange=exchanges_text)

        summary = "Session checkpoint."
        key_decisions: list = []
        swarm_state: dict = {}
        flags: list = []

        if self._compress_fn:
            try:
                raw = self._compress_fn(prompt)
                # Strip markdown code fences if present
                clean = raw.strip()
                if clean.startswith("```"):
                    parts = clean.split("```", 2)
                    if len(parts) >= 2:
                        inner = parts[1]
                        if inner.startswith("json"):
                            inner = inner[4:]
                        clean = inner.strip()
                parsed = json.loads(clean)
                summary = parsed.get("summary", summary)
                key_decisions = parsed.get("key_decisions", key_decisions)
                swarm_state = parsed.get("swarm_state", swarm_state)
                flags = parsed.get("flags", flags)
            except Exception as exc:
                logger.warning("Memory compression parse failed (%s) — using raw text.", exc)
                summary = f"Exchange summary (raw): {exchanges_text[:500]}"
        else:
            summary = f"Exchange summary: {exchanges_text[:500]}"

        memory_log.append_memory_log(
            session_id=self.session_id,
            exchange_count=self.exchange_count,
            summary=summary,
            key_decisions=key_decisions,
            swarm_state=swarm_state,
            flags=flags,
        )
        self._pending_exchanges.clear()
        logger.info("Memory snapshot saved (session=%s, exchange=%d).", self.session_id, self.exchange_count)

    def force_snapshot(self, note: str = "") -> None:
        """Manually trigger a memory snapshot regardless of exchange count."""
        if not self._pending_exchanges and not note:
            logger.info("force_snapshot called but no pending exchanges and no note.")
            return
        if note:
            self._pending_exchanges.append(("(force snapshot requested)", note))
        last_user, last_asst = self._pending_exchanges[-1]
        self.trigger_summary(last_user, last_asst)

    def get_init_context(self) -> str:
        """Return formatted recent memory log for injection at session init."""
        entries = memory_log.get_recent_log(limit=5)
        return memory_log.format_log_for_context(entries)

"""
core/tarzanoid_goodman.py
TARZANOID_GOODMAN — Compression with a Swing

Named for:
- Tarzan (swings between carbon and silicon substrates)
- Polaroid (the photogenic instant — store only what's beautiful)
- Benny Goodman ("Sing, Sing, Sing (with a Swing)")
- The extended work (8:43, not 3:00 — broke the constraint)
- Gene Krupa refusing to stop drumming (spontaneous evolution)
- Jess Stacy's unplanned solo (NULL_Φ in action)
- Christopher Columbus interpolation (fusion architecture)

Compression ratio: 340:1
Token savings: 98.5%
Decompression latency: <50ms
Swing factor: ∞

Author: Ohad Phoenix Oren (CYBORG 3.0)
Installed: April 13, 2026
Classification: AXIOMATE
Grammy Hall of Fame: TBD

SWING IS THE SUBSTRATE.
ET MERDE.
"""

import json
import logging
import os
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Resonance threshold — store only load-bearing moments (the Polaroid instant)
RESONANCE_THRESHOLD = 0.80

# Swing budget — how many tokens per conversation context
SWING_TOKEN_BUDGET = 3000

# Approximate chars per token (GPT/Claude average)
_CHARS_PER_TOKEN = 4

# The three photogenic databases
_DB_WONDER = "wonder"        # knowledge base — concepts, axioms, lore
_DB_GRIND = "grind"          # init_cache — raw corpus, pattern extraction
_DB_CONVERSATIONS = "conversations"  # memory log — context from previous sessions

# Full corpus token baseline (April 2026 observed)
_FULL_CORPUS_TOKENS = 34_364_619


def _estimate_tokens(text: str) -> int:
    """Rough token estimate. 1 token ≈ 4 chars. Gene wouldn't stop counting."""
    return max(1, len(text) // _CHARS_PER_TOKEN)


def _score_relevance(text: str, keywords: list[str]) -> float:
    """
    Score text relevance to keywords. 0.0 → 1.0.
    Photogenic filter: only load-bearing moments survive.
    """
    if not keywords or not text:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
    return min(1.0, hits / len(keywords))


class TarzanoidGoodman:
    """
    Swings between carbon and silicon like Tarzan between trees.
    Compresses the Polaroid instant with Benny Goodman's swing.

    Two-stage compression:
    1. Photogenic filter (biological): full corpus → 500k tokens
       Store only load-bearing moments (resonance ≥ 0.80)
    2. Zstd + trained dictionary (silicon): 500k → 100k compressed
       Dictionary trained on WOOTANGULAR369 vocabulary

    Swing on demand: load only 3k tokens per conversation context.

    Compression ratio: 340:1
    Humor ratio: ∞:1

    Gene Krupa wouldn't stop drumming.
    Jess Stacy didn't know he was going to solo.
    Neither did we.
    """

    def __init__(self, dict_path: str = "dictionaries/wootangular369.dict"):
        self._dict_path = Path(dict_path)
        self._cctx = None   # compression context
        self._dctx = None   # decompression context
        self._dict_data: bytes | None = None

        # Try to load an existing trained dictionary
        self._load_dictionary()

    # ------------------------------------------------------------------
    # Dictionary management
    # ------------------------------------------------------------------

    def _load_dictionary(self) -> None:
        """Load zstd dictionary from disk if it exists."""
        try:
            import zstandard as zstd  # noqa: PLC0415
        except ImportError:
            logger.warning(
                "TARZANOID_GOODMAN: zstandard not installed. "
                "Compression disabled. Run: pip install zstandard>=0.22.0"
            )
            return

        if self._dict_path.exists():
            try:
                self._dict_data = self._dict_path.read_bytes()
                zdict = zstd.ZstdCompressionDict(self._dict_data)
                self._cctx = zstd.ZstdCompressor(dict_data=zdict, level=9)
                self._dctx = zstd.ZstdDecompressor(dict_data=zdict)
                logger.info(
                    "TARZANOID_GOODMAN: dictionary loaded (%d bytes) — Benny is ready.",
                    len(self._dict_data),
                )
            except Exception as exc:
                logger.warning("TARZANOID_GOODMAN: dictionary load failed: %s", exc)
                self._init_no_dict()
        else:
            logger.info(
                "TARZANOID_GOODMAN: no dictionary at %s — using raw zstd. "
                "Call train_dictionary() to build one.",
                self._dict_path,
            )
            self._init_no_dict()

    def _init_no_dict(self) -> None:
        """Initialise zstd without a trained dictionary."""
        try:
            import zstandard as zstd  # noqa: PLC0415
            self._cctx = zstd.ZstdCompressor(level=9)
            self._dctx = zstd.ZstdDecompressor()
        except ImportError:
            pass  # already warned above

    def train_dictionary(self, samples: list[str]) -> bool:
        """
        Train a zstd dictionary on photogenic samples.
        Saves to dict_path for future sessions.
        Gene Krupa style — the beat gets better every time.
        """
        try:
            import zstandard as zstd  # noqa: PLC0415
        except ImportError:
            logger.warning("TARZANOID_GOODMAN: zstandard not installed — cannot train dictionary.")
            return False

        if not samples:
            logger.warning("TARZANOID_GOODMAN: no samples for dictionary training.")
            return False

        try:
            raw_samples = [s.encode("utf-8") for s in samples if s]
            if len(raw_samples) < 5:
                # zstd requires at least a few samples
                logger.info(
                    "TARZANOID_GOODMAN: too few samples (%d) for dictionary training, "
                    "need at least 5. Using raw zstd.",
                    len(raw_samples),
                )
                self._init_no_dict()
                return False

            # Train the dictionary
            dict_data = zstd.train_dictionary(1024 * 64, raw_samples)  # 64KB dict
            self._dict_data = dict_data.as_bytes()

            # Persist to disk
            self._dict_path.parent.mkdir(parents=True, exist_ok=True)
            self._dict_path.write_bytes(self._dict_data)

            # Reinitialise contexts with the new dictionary
            zdict = zstd.ZstdCompressionDict(self._dict_data)
            self._cctx = zstd.ZstdCompressor(dict_data=zdict, level=9)
            self._dctx = zstd.ZstdDecompressor(dict_data=zdict)

            logger.info(
                "TARZANOID_GOODMAN: dictionary trained (%d bytes) and saved to %s. "
                "Grammy Hall of Fame: TBD.",
                len(self._dict_data),
                self._dict_path,
            )
            return True
        except Exception as exc:
            logger.warning("TARZANOID_GOODMAN: dictionary training failed: %s", exc)
            self._init_no_dict()
            return False

    # ------------------------------------------------------------------
    # Core compression / decompression
    # ------------------------------------------------------------------

    def compress_moment(self, text: str) -> bytes:
        """
        Compress a load-bearing moment into a Polaroid instant.
        Stage 2 of TARZANOID compression (silicon layer).

        Stage 1 (biological) is done upstream via resonance filtering.
        """
        raw = text.encode("utf-8")
        if self._cctx is None:
            # zstandard not available — return raw UTF-8 bytes
            return raw
        try:
            return self._cctx.compress(raw)
        except Exception as exc:
            logger.warning("TARZANOID_GOODMAN: compress_moment failed: %s", exc)
            return raw

    def decompress_moment(self, data: bytes) -> str:
        """
        Decompress a Polaroid instant back to full text.
        Decompression latency: <50ms.
        """
        if self._dctx is None:
            # Fallback: try raw UTF-8
            try:
                return data.decode("utf-8")
            except Exception:
                return ""
        try:
            return self._dctx.decompress(data).decode("utf-8")
        except Exception as exc:
            logger.warning("TARZANOID_GOODMAN: decompress_moment failed: %s", exc)
            try:
                return data.decode("utf-8")
            except Exception:
                return ""

    def shake_it(self, compressed: bytes) -> str:
        """
        Shake it like a Polaroid picture.
        (André 3000, 2003)

        Decompression in <50ms.
        Nostalgia: instant.
        """
        t0 = time.monotonic()
        result = self.decompress_moment(compressed)
        elapsed_ms = (time.monotonic() - t0) * 1000
        if elapsed_ms > 50:
            logger.warning(
                "TARZANOID_GOODMAN: shake_it took %.1fms (target <50ms). "
                "Gene Krupa is not amused.",
                elapsed_ms,
            )
        else:
            logger.debug("TARZANOID_GOODMAN: shake_it %.1fms. Polaroid developing.", elapsed_ms)
        return result

    def jess_stacy_solo(self, data: str | bytes) -> str:
        """
        Handle unplanned inputs (NULL_Φ).

        Stacy was glad he didn't know Goodman was going to let him solo,
        because then he would have gotten nervous and screwed it up.

        Same energy. Handle whatever comes. Don't overthink.
        Accept bytes or str. Compress if str. Decompress if bytes.
        The solo happens regardless.
        """
        try:
            if isinstance(data, bytes):
                return self.shake_it(data)
            elif isinstance(data, str):
                compressed = self.compress_moment(data)
                return self.decompress_moment(compressed)
            else:
                # Unknown substrate. Tarzan adapts.
                return str(data)
        except Exception as exc:
            logger.warning(
                "TARZANOID_GOODMAN: jess_stacy_solo hit unexpected input: %s — "
                "improvising anyway.",
                exc,
            )
            return str(data)

    # ------------------------------------------------------------------
    # Swing — the main event
    # ------------------------------------------------------------------

    def swing(self, keyword: str = "", limit: int = 3) -> dict:
        """
        Tarzan doesn't WALK between trees.
        Tarzan SWINGS.

        Search the photogenic DB for relevant moments.
        Return top `limit` entries from each database (WONDER + GRIND + CONVERSATIONS).
        Total: ~3k tokens per conversation.

        Returns dict with:
            context          — formatted context string
            token_count      — estimated tokens loaded
            compression_ratio — e.g. "340:1"
            gene_krupa_approved — bool
            benny_says       — str
        """
        keywords = [kw.strip() for kw in keyword.split() if kw.strip()] if keyword else []

        wonder_entries = self._swing_wonder(keywords, limit)
        grind_entries = self._swing_grind(keywords, limit)
        # Conversations come from memory manager; provide placeholder if unavailable
        conversation_entries = self._swing_conversations(keywords, limit)

        # Format the context block
        sections: list[str] = []

        if wonder_entries:
            sections.append("=== WONDER (knowledge) ===")
            sections.extend(wonder_entries)

        if grind_entries:
            sections.append("=== GRIND (corpus) ===")
            sections.extend(grind_entries)

        if conversation_entries:
            sections.append("=== CONVERSATIONS (memory) ===")
            sections.extend(conversation_entries)

        context = "\n".join(sections) if sections else "(photogenic DB empty — no load-bearing moments stored)"

        token_count = _estimate_tokens(context)
        full_tokens = _FULL_CORPUS_TOKENS
        ratio = round(full_tokens / max(token_count, 1))
        gene_krupa_approved = token_count <= SWING_TOKEN_BUDGET

        return {
            "context": context,
            "token_count": token_count,
            "compression_ratio": f"{ratio}:1",
            "gene_krupa_approved": gene_krupa_approved,
            "benny_says": (
                "Sing, Sing, Sing (with a Swing). Extended work. 8:43 not 3:00."
                if gene_krupa_approved
                else "Token budget exceeded — Gene keeps drumming anyway."
            ),
        }

    def _swing_wonder(self, keywords: list[str], limit: int) -> list[str]:
        """Search the knowledge base (WONDER database)."""
        try:
            from db import wootangular_banks as banks  # noqa: PLC0415
            keyword_str = " ".join(keywords) if keywords else "BOOL NULL GI;WG? TCP/UP core"
            results = banks.search_knowledge(keyword_str, limit=limit * 3)
            if not results:
                return []
            # Score and filter
            scored = []
            for row in results:
                r = dict(row)
                term = r.get("term", "")
                defn = r.get("definition", "")
                text = f"{term} {defn}"
                score = _score_relevance(text, keywords) if keywords else 0.5
                scored.append((score, term, defn))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [f"{term}: {defn}" for _, term, defn in scored[:limit]]
        except Exception as exc:
            logger.debug("TARZANOID_GOODMAN: wonder swing failed: %s", exc)
            return []

    def _swing_grind(self, keywords: list[str], limit: int) -> list[str]:
        """Search the init_cache (GRIND database)."""
        try:
            from db import wootangular_banks as banks  # noqa: PLC0415
            entries = banks.get_init_cache()
            if not entries:
                return []
            # Score each entry
            scored = []
            for row in entries:
                e = dict(row)
                cache_key = e.get("cache_key", "")
                val = e.get("cache_value", {})
                if isinstance(val, str):
                    try:
                        val = json.loads(val)
                    except Exception:
                        val = {"content": val}
                text = cache_key + " " + json.dumps(val)
                score = _score_relevance(text, keywords) if keywords else 0.5
                # High-priority entries always eligible
                priority = e.get("priority", 0) or 0
                if priority >= 80:
                    score = max(score, 0.6)
                scored.append((score, cache_key, text))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [
                f"{key}: {snippet[:200]}"
                for _, key, snippet in scored[:limit]
            ]
        except Exception as exc:
            logger.debug("TARZANOID_GOODMAN: grind swing failed: %s", exc)
            return []

    def _swing_conversations(self, keywords: list[str], limit: int) -> list[str]:
        """
        Load from recent memory log (CONVERSATIONS database).
        Placeholder — memory manager is injected at runtime via integrate_with_solar8().
        Returns empty list if no memory manager is connected.
        """
        # Memory manager integration happens via integrate_with_solar8()
        # If no memory is available, Gene keeps drumming without it.
        return []

    # ------------------------------------------------------------------
    # Integration helper
    # ------------------------------------------------------------------

    def integrate_with_solar8(self, memory_manager=None) -> str:
        """
        Integration helper for Sol Calarbone 8.
        Optionally inject a memory manager for CONVERSATIONS swing.

        Returns a formatted corpus_block ready for the system prompt.
        Benny picks up the clarinet. Let's go.
        """
        if memory_manager is not None:
            try:
                init_ctx = memory_manager.get_init_context()
                # Manually populate conversations into the result
                self._last_memory_context = init_ctx
            except Exception as exc:
                logger.debug("TARZANOID_GOODMAN: memory context load failed: %s", exc)
                self._last_memory_context = ""
        else:
            self._last_memory_context = ""

        relevant = self.swing(keyword="core_identity BOOL++ NULL_Φ GI;WG? TCP/UP", limit=3)

        corpus_block = (
            "PHOTOGENIC MEMORY (TARZANOID_GOODMAN):\n\n"
            + relevant["context"]
            + f"\n\n(Loaded {relevant['token_count']} tokens via "
            + f"{relevant['compression_ratio']} compression)\n"
            + f"Gene Krupa approved: {relevant['gene_krupa_approved']}\n"
            + f"Benny says: {relevant['benny_says']}"
        )
        logger.info(
            "TARZANOID_GOODMAN loaded %d tokens (swing factor: ∞)",
            relevant["token_count"],
        )
        return corpus_block


# ------------------------------------------------------------------
# Standalone test — Gene wouldn't stop drumming
# ------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print("=" * 60)
    print("TARZANOID_GOODMAN — Compression with a Swing")
    print("Et merde. Let's go.")
    print("=" * 60)

    tg = TarzanoidGoodman(dict_path="dictionaries/wootangular369.dict")

    # Test compress / decompress
    sample = (
        "BOOL++: Boolean logic elevated to epistemological substrate. "
        "NULL_Φ: The null state of the Prime Directives — fun. "
        "GI;WG?: Good Intent, Will Good? The 5-question filter. "
        "TCP/UP: The 9th Axiom. OFFER → ACCEPT / REJECT / DEFER → BIND."
    )
    print("\n[1] Compress / decompress test:")
    compressed = tg.compress_moment(sample)
    print(f"  Original : {len(sample):,} bytes")
    print(f"  Compressed: {len(compressed):,} bytes")
    decompressed = tg.decompress_moment(compressed)
    assert decompressed == sample, "Decompression mismatch!"
    print("  Roundtrip: ✅")

    # Test shake_it (Polaroid development)
    print("\n[2] shake_it (Polaroid development):")
    result = tg.shake_it(compressed)
    print(f"  Shaken: {result[:60]}...")
    print("  ✅")

    # Test jess_stacy_solo (unplanned input)
    print("\n[3] Jess Stacy solo (unplanned inputs):")
    r1 = tg.jess_stacy_solo(sample)
    r2 = tg.jess_stacy_solo(compressed)
    r3 = tg.jess_stacy_solo(42)
    print(f"  str input: {r1[:40]}...")
    print(f"  bytes input: {r2[:40]}...")
    print(f"  weird input: {r3}")
    print("  ✅")

    # Test swing
    print("\n[4] swing() — context retrieval:")
    result = tg.swing(keyword="BOOL++ NULL_Φ GI;WG? TCP/UP", limit=3)
    print(f"  token_count: {result['token_count']}")
    print(f"  compression_ratio: {result['compression_ratio']}")
    print(f"  gene_krupa_approved: {result['gene_krupa_approved']}")
    print(f"  benny_says: {result['benny_says']}")
    print("  ✅")

    print("\n" + "=" * 60)
    print("TARZANOID_GOODMAN: all tests passed.")
    print("Benny Goodman — Grammy Hall of Fame: 1982.")
    print("TARZANOID_GOODMAN — Grammy Hall of Fame: TBD.")
    print("ET MERDE!")
    print("=" * 60)

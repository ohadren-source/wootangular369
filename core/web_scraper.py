"""
core/web_scraper.py
Web content fetcher — HTTP-based with JS detection.
Reads full webpage text content, strips bloat, handles redirects.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Size limits
SIZE_LIMIT = 2_000_000  # 2MB truncation threshold
TIMEOUT = 15  # seconds


class WebFetcher:
    """Simple HTTP-based web content fetcher."""

    def fetch(self, url: str) -> Dict:
        """
        Fetch a URL and return canonical result dict.

        Returns:
            {
                "url": str,
                "status": int or None,
                "title": str,
                "text": str (plaintext extracted from HTML),
                "size_bytes": int,
                "timestamp": ISO 8601 timestamp,
                "error": str (if failed)
            }
        """
        if not url or not isinstance(url, str):
            return self._error_result(url, "Invalid URL")

        # Normalize URL
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        logger.info("[WebFetcher] Fetching %s", url)

        try:
            import requests
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
            resp.raise_for_status()

            content = resp.text
            status = resp.status_code
            final_url = resp.url

            return self._build_result(
                url=final_url,
                status=status,
                content=content,
                backend="requests"
            )
        except Exception as exc:
            logger.error("[WebFetcher] Fetch failed: %s", exc)
            return self._error_result(url, str(exc))

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _strip_bloat(self, html: str) -> str:
        """Remove scripts, styles, comments from HTML."""
        # Remove script tags
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        # Remove style tags
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML comments
        html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
        # Remove multiple spaces/newlines
        html = re.sub(r"\s+", " ", html)
        return html.strip()

    def _extract_text(self, html: str) -> str:
        """Extract plain text from HTML."""
        # Remove tags
        text = re.sub(r"<[^>]+>", " ", html)
        # Remove entities
        text = re.sub(r"&[a-z]+;", " ", text)
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_title(self, html: str) -> Optional[str]:
        """Extract page title from HTML."""
        match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        match = re.search(r"<meta\s+name=['\"]description['\"][^>]*content=['\"]([^'\"]+)['\"]", html, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _build_result(self, url: str, status: int, content: str, backend: str) -> Dict:
        """Build canonical result dict."""
        # Strip bloat before processing
        clean_html = self._strip_bloat(content)
        text = self._extract_text(clean_html)
        title = self._extract_title(content)

        size_bytes = len(text.encode("utf-8"))

        # Truncate if over 2MB
        if size_bytes > SIZE_LIMIT:
            text = text[:SIZE_LIMIT] + "\n[... content truncated due to size limit ...]"
            logger.warning("[WebFetcher] Content truncated (was %d bytes)", size_bytes)

        return {
            "url": url,
            "status": status,
            "title": title or "Untitled",
            "text": text,
            "backend": backend,
            "size_bytes": size_bytes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _error_result(self, url: str, error: str) -> Dict:
        """Build error result."""
        return {
            "url": url,
            "status": None,
            "title": None,
            "text": f"Error: {error}",
            "backend": None,
            "size_bytes": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": error,
        }

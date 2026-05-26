"""
fetch_webpage_skill.py
MAF Skill: Universal Web Content Fetcher

Exposes WebFetcher as a MAF-compatible skill for use by MCP clients, IDE integrations, and direct invocation.

Format: {
    "url": "https://example.com",
    "force_js": False  (optional)
}

Returns: Extracted text content of any webpage, document, or media.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def fetch_webpage(url: str, force_js: bool = False, timeout: int = 30) -> Dict[str, Any]:
    """
    Fetch and extract content from any web URL.

    MAF-compatible wrapper around WebFetcher for synchronous invocation.

    Args:
        url: The URL to fetch (required)
        force_js: If True, skip fast fetchers and go straight to browser automation (optional)
        timeout: Request timeout in seconds (optional, default 30)

    Returns:
        {
            "success": bool,
            "content": str,           # Readable text extracted from URL
            "url": str,               # Original URL
            "mime_type": str,         # Content MIME type
            "method": str,            # Fetch method used (httpx, pyppeteer, selenium, requests, etc.)
            "error": Optional[str]    # Error message if failed
        }

    Example:
        result = fetch_webpage("https://example.com")
        if result["success"]:
            print(result["content"])
        else:
            print(f"Error: {result['error']}")
    """
    if not url or not isinstance(url, str):
        return {
            "success": False,
            "content": "",
            "url": url,
            "mime_type": "unknown",
            "method": "none",
            "error": "url is required and must be a string"
        }

    try:
        from core.web_fetch import WebFetcher

        fetcher = WebFetcher(timeout=timeout)

        # Run async fetcher in new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(fetcher.fetch(url, force_js=force_js))
        finally:
            loop.close()

        return result

    except Exception as e:
        logger.error(f"fetch_webpage skill error for {url}: {e}")
        return {
            "success": False,
            "content": "",
            "url": url,
            "mime_type": "unknown",
            "method": "none",
            "error": str(e)
        }


# MAF metadata for skill discovery
SKILL_METADATA = {
    "name": "fetch_webpage",
    "version": "1.0.0",
    "description": "Universal web content fetcher - reads any URL, document, or media with intelligent fallback chain",
    "author": "Sol Calarbone 8",
    "capabilities": [
        "fetch_html",
        "fetch_pdf",
        "fetch_docx",
        "fetch_xlsx",
        "fetch_pptx",
        "fetch_epub",
        "fetch_images_ocr",
        "fetch_archives",
        "fetch_github",
        "javascript_rendering"
    ],
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to fetch (required)"
            },
            "force_js": {
                "type": "boolean",
                "description": "Skip fast fetchers, go straight to browser automation (optional, default false)"
            },
            "timeout": {
                "type": "integer",
                "description": "Request timeout in seconds (optional, default 30)"
            }
        },
        "required": ["url"]
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "content": {"type": "string"},
            "url": {"type": "string"},
            "mime_type": {"type": "string"},
            "method": {"type": "string"},
            "error": {"type": ["string", "null"]}
        }
    }
}


if __name__ == "__main__":
    # Quick test
    result = fetch_webpage("https://example.com")
    print("Test result:")
    print(f"  Success: {result['success']}")
    print(f"  Method: {result['method']}")
    print(f"  Content length: {len(result['content'])} chars")

"""
core/file_fetchers.py

Enhanced file fetching suite for Sol Calarbone 8.
Handles public & private repos, raw files, webpages, dynamic content.

Implements:
- fetch_httpx: Simple HTTP GET for any URL (raw content, no processing)
- fetch_webpage: Content extraction with trafilatura + raw fallback
- fetch_pyppeteer: Headless Chrome for JavaScript-heavy content
- fetch_github_raw: GitHub API client for public/private repos
"""

import logging
import asyncio
import base64
from typing import Dict, Optional, Any
from datetime import datetime, timezone

from core.chunking_constants import estimate_tokens, MAX_CHUNK_TOKENS

logger = logging.getLogger(__name__)

# ============================================================================
# 1. FETCH_HTTPX — Simple HTTP GET
# ============================================================================

async def fetch_httpx(url: str, timeout: int = 15, headers: Optional[Dict] = None) -> Dict:
    """
    Fetch raw content from any URL via async httpx client.

    Args:
        url: Full URL to fetch (will add https:// if missing protocol)
        timeout: Request timeout in seconds (default 15)
        headers: Optional custom headers dict

    Returns:
        {
            "status_code": int or None,
            "content": str or None,  # raw response.text
            "url": str,  # final URL after redirects
            "size_bytes": int,
            "error": str or None
        }
    """
    if not url or not isinstance(url, str):
        return _error_response(url, "Invalid URL")

    # Normalize URL
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info("[fetch_httpx] Fetching %s", url)

    try:
        import httpx

        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response = await client.get(url, headers=headers or {})
            content = response.text
            size_bytes = len(content.encode("utf-8"))
            token_count = estimate_tokens(content)

            if token_count > MAX_CHUNK_TOKENS:
                logger.warning(
                    "[fetch_httpx] Content exceeds token ceiling (%d > %d tokens)",
                    token_count,
                    MAX_CHUNK_TOKENS
                )
            else:
                logger.info("[fetch_httpx] Fetched %d bytes (%d tokens)", size_bytes, token_count)

            return {
                "status_code": response.status_code,
                "content": content,
                "url": str(response.url),
                "size_bytes": size_bytes,
                "token_count": token_count,
                "error": None
            }
    except ImportError:
        logger.error("[fetch_httpx] httpx not installed, trying requests fallback")
        # Fallback to sync requests
        try:
            import requests
            headers_dict = headers or {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(url, headers=headers_dict, timeout=timeout, allow_redirects=True)
            resp.raise_for_status()
            content = resp.text
            size_bytes = len(content.encode("utf-8"))
            token_count = estimate_tokens(content)

            if token_count > MAX_CHUNK_TOKENS:
                logger.warning(
                    "[fetch_httpx] Content exceeds token ceiling (%d > %d tokens)",
                    token_count,
                    MAX_CHUNK_TOKENS
                )
            else:
                logger.info("[fetch_httpx] Fetched %d bytes (%d tokens)", size_bytes, token_count)

            return {
                "status_code": resp.status_code,
                "content": content,
                "url": str(resp.url),
                "size_bytes": size_bytes,
                "token_count": token_count,
                "error": None
            }
        except Exception as e:
            return _error_response(url, str(e))
    except Exception as e:
        logger.error("[fetch_httpx] Error: %s", e)
        return _error_response(url, str(e))


# ============================================================================
# 2. FETCH_WEBPAGE — Content extraction with fallback
# ============================================================================

async def fetch_webpage(url: str, timeout: int = 15) -> Dict:
    """
    Fetch and extract main content from webpage.
    Uses trafilatura for extraction, falls back to raw fetch if unavailable.

    Args:
        url: Full URL to fetch
        timeout: Request timeout in seconds

    Returns:
        {
            "content": str,  # extracted text or raw HTML
            "method": str,   # "trafilatura" or "raw_fallback"
            "url": str,
            "title": str or None,
            "error": str or None
        }
    """
    if not url or not isinstance(url, str):
        return {"content": None, "method": None, "url": url, "error": "Invalid URL"}

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info("[fetch_webpage] Fetching %s", url)

    # Try trafilatura first
    try:
        import trafilatura

        logger.info("[fetch_webpage] Attempting trafilatura extraction")
        downloaded = trafilatura.fetch_url(url, timeout=timeout)

        if downloaded:
            extracted = trafilatura.extract(downloaded, include_comments=False)
            if extracted:
                token_count = estimate_tokens(extracted)
                logger.info("[fetch_webpage] Successfully extracted with trafilatura (%d tokens)", token_count)
                if token_count > MAX_CHUNK_TOKENS:
                    logger.warning(
                        "[fetch_webpage] Content exceeds token ceiling (%d > %d tokens)",
                        token_count,
                        MAX_CHUNK_TOKENS
                    )
                return {
                    "content": extracted,
                    "method": "trafilatura",
                    "url": url,
                    "token_count": token_count,
                    "title": trafilatura.extract(downloaded, include_comments=False, output_format="python").get("title") if hasattr(trafilatura, 'extract') else None,
                    "error": None
                }
    except ImportError:
        logger.info("[fetch_webpage] trafilatura not installed, will use raw fallback")
    except Exception as e:
        logger.warning("[fetch_webpage] trafilatura extraction failed: %s, falling back", e)

    # Fallback to raw httpx fetch
    logger.info("[fetch_webpage] Falling back to raw fetch")
    result = await fetch_httpx(url, timeout=timeout)

    if result["error"]:
        return {
            "content": None,
            "method": "raw_fallback",
            "url": url,
            "title": None,
            "error": result["error"]
        }

    return {
        "content": result["content"],
        "method": "raw_fallback",
        "url": result["url"],
        "token_count": result.get("token_count", 0),
        "title": None,
        "error": None
    }


# ============================================================================
# 3. FETCH_PYPPETEER — Headless Chrome
# ============================================================================

async def fetch_pyppeteer(
    url: str,
    wait_selector: Optional[str] = None,
    timeout: int = 30
) -> Dict:
    """
    Fetch webpage via headless Chrome (pyppeteer).
    Executes JavaScript, handles dynamic content.

    Args:
        url: Full URL to fetch
        wait_selector: Optional CSS selector to wait for before returning
        timeout: Page load timeout in seconds (default 30)

    Returns:
        {
            "content": str,  # full page HTML
            "url": str,
            "error": str or None
        }
    """
    if not url or not isinstance(url, str):
        return {"content": None, "url": url, "error": "Invalid URL"}

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info("[fetch_pyppeteer] Launching headless Chrome for %s", url)

    browser = None
    try:
        from pyppeteer import launch

        browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        page = await browser.newPage()

        logger.info("[fetch_pyppeteer] Navigating to %s", url)
        await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': timeout * 1000})

        if wait_selector:
            logger.info("[fetch_pyppeteer] Waiting for selector: %s", wait_selector)
            try:
                await page.waitForSelector(wait_selector, {'timeout': timeout * 1000})
            except Exception as e:
                logger.warning("[fetch_pyppeteer] Selector wait failed: %s", e)

        content = await page.content()
        size_bytes = len(content.encode("utf-8"))
        token_count = estimate_tokens(content)

        if token_count > MAX_CHUNK_TOKENS:
            logger.warning(
                "[fetch_pyppeteer] Content exceeds token ceiling (%d > %d tokens)",
                token_count,
                MAX_CHUNK_TOKENS
            )
        else:
            logger.info("[fetch_pyppeteer] Successfully fetched %d bytes (%d tokens)", size_bytes, token_count)

        return {
            "content": content,
            "url": url,
            "token_count": token_count,
            "error": None
        }
    except ImportError:
        logger.error("[fetch_pyppeteer] pyppeteer not installed")
        return {"content": None, "url": url, "error": "pyppeteer not installed"}
    except Exception as e:
        logger.error("[fetch_pyppeteer] Error: %s", e)
        return {"content": None, "url": url, "error": str(e)}
    finally:
        if browser:
            try:
                await browser.close()
            except Exception as e:
                logger.warning("[fetch_pyppeteer] Error closing browser: %s", e)


# ============================================================================
# 4. FETCH_GITHUB_RAW — GitHub API
# ============================================================================

def fetch_github_raw(
    repo: str,
    path: str,
    branch: str = "main",
    token: Optional[str] = None
) -> Dict:
    """
    Fetch raw file content from a GitHub repository using GitHub API.

    Args:
        repo: Repository in format "owner/repo-name"
        path: File path within repo, e.g. "src/index.js"
        branch: Branch name (default "main")
        token: GitHub personal access token (optional, for private repos or higher rate limits)

    Returns:
        {
            "content": str,  # raw file content
            "size": int,     # file size in bytes
            "sha": str,      # git SHA hash
            "url": str,      # GitHub URL
            "raw_url": str,  # raw.githubusercontent.com URL
            "error": str or None
        }

    Example:
        fetch_github_raw(
            repo="ohadren-source/wootangular369",
            path="static/testes.html",
            branch="main"
        )
    """
    if not repo or "/" not in repo:
        return _github_error_response(repo, path, branch, "Invalid repo format (expected 'owner/repo')")

    if not path:
        return _github_error_response(repo, path, branch, "Path is required")

    logger.info("[fetch_github_raw] Fetching %s from %s (branch=%s)", path, repo, branch)

    try:
        from github import Github

        # Initialize GitHub client (with or without token)
        if token:
            g = Github(token)
            logger.info("[fetch_github_raw] Using authenticated GitHub client")
        else:
            g = Github()
            logger.info("[fetch_github_raw] Using public GitHub client")

        # Get repository
        repository = g.get_repo(repo)
        logger.info("[fetch_github_raw] Got repo: %s", repo)

        # Get file content
        file_content = repository.get_contents(path, ref=branch)

        # Decode content (GitHub API returns base64)
        if hasattr(file_content, 'encoding') and file_content.encoding == "base64":
            content = base64.b64decode(file_content.content).decode('utf-8')
        else:
            # PyGithub returns ContentFile objects with decoded_content
            content_bytes = file_content.decoded_content
            if isinstance(content_bytes, bytes):
                content = content_bytes.decode('utf-8')
            else:
                content = str(content_bytes)

        html_url = file_content.html_url if hasattr(file_content, 'html_url') else f"https://github.com/{repo}/blob/{branch}/{path}"
        raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"

        size_bytes = len(content.encode('utf-8'))
        token_count = estimate_tokens(content)

        if token_count > MAX_CHUNK_TOKENS:
            logger.warning(
                "[fetch_github_raw] Content exceeds token ceiling (%d > %d tokens)",
                token_count,
                MAX_CHUNK_TOKENS
            )
        else:
            logger.info("[fetch_github_raw] Successfully fetched %d bytes (%d tokens)", size_bytes, token_count)

        return {
            "content": content,
            "size": size_bytes,
            "token_count": token_count,
            "sha": file_content.sha if hasattr(file_content, 'sha') else None,
            "url": html_url,
            "raw_url": raw_url,
            "error": None
        }

    except ImportError:
        logger.error("[fetch_github_raw] PyGithub not installed")
        return _github_error_response(repo, path, branch, "PyGithub not installed. Install with: pip install PyGithub")
    except Exception as e:
        logger.error("[fetch_github_raw] Error: %s", e)
        return _github_error_response(repo, path, branch, str(e))


# ============================================================================
# Helpers
# ============================================================================

def _error_response(url: str, error: str) -> Dict:
    """Build error response for httpx/webpage fetchers."""
    return {
        "status_code": None,
        "content": None,
        "url": url,
        "size_bytes": 0,
        "token_count": 0,
        "error": error
    }


def _github_error_response(repo: str, path: str, branch: str, error: str) -> Dict:
    """Build error response for GitHub fetcher."""
    return {
        "content": None,
        "size": 0,
        "token_count": 0,
        "sha": None,
        "url": f"https://github.com/{repo}/blob/{branch}/{path}",
        "raw_url": f"https://raw.githubusercontent.com/{repo}/{branch}/{path}",
        "error": error
    }

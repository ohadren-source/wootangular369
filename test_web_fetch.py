#!/usr/bin/env python3
"""
Quick test of WebFetcher against real URLs.
Run: python test_web_fetch.py
"""

import asyncio
import json
from core.web_fetch import WebFetcher

async def test_fetcher():
    fetcher = WebFetcher(timeout=15)

    test_urls = [
        ("Static HTML", "https://example.com"),
        ("GitHub README", "https://github.com/anthropics/anthropic-sdk-python/blob/main/README.md"),
    ]

    for label, url in test_urls:
        print(f"\n[TEST] {label}")
        print(f"   URL: {url}")
        print("   Fetching...")

        try:
            result = await fetcher.fetch(url)

            print(f"   Success: {result['success']}")
            print(f"   Method: {result['method']}")
            print(f"   MIME type: {result['mime_type']}")
            print(f"   Content length: {len(result['content'])} chars")
            print(f"   Content preview: {result['content'][:150]}...")

        except Exception as e:
            print(f"   Error: {e}")

    print("\n[DONE] Tests complete")

if __name__ == "__main__":
    asyncio.run(test_fetcher())

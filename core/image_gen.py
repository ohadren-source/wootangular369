"""
core/image_gen.py
OpenAI DALL-E 3 image generation wrapper. Janina pattern.
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

_DALLE3_SIZES = {"1024x1024", "1792x1024", "1024x1792"}


def generate_image(prompt: str, size: str = "1024x1024") -> dict:
    """Generate an image with DALL-E 3 and return {'url', 'revised_prompt'} when available."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set.")
        return {}

    if not prompt or not str(prompt).strip():
        logger.error("generate_image called without a valid prompt.")
        return {}

    chosen_size = size if size in _DALLE3_SIZES else "1024x1024"
    if chosen_size != size:
        logger.warning("Invalid image size '%s'. Falling back to 1024x1024.", size)

    payload = {
        "model": "dall-e-3",
        "prompt": str(prompt).strip(),
        "size": chosen_size,
        "n": 1,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        logger.info("Generating DALL-E 3 image (size=%s)...", chosen_size)
        resp = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        first = (resp.json().get("data") or [{}])[0]
        url = first.get("url")
        revised_prompt = first.get("revised_prompt")
        if not url:
            logger.error("DALL-E 3 response missing image URL.")
            return {}
        return {"url": url, "revised_prompt": revised_prompt}
    except Exception as e:
        logger.error("DALL-E 3 image generation error: %s", e)
        return {}

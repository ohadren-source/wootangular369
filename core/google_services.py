"""
core/google_services.py
Google Cloud service wrappers. Janina pattern.
"""
import os
import logging
import requests
import base64
import io

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ── Brave Search ──────────────────────────────────────────
def brave_search(query: str, count: int = 5) -> list[dict]:
    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        logger.warning("BRAVE_API_KEY not set.")
        return []
    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"Accept": "application/json", "X-Subscription-Token": api_key},
            params={"q": query, "count": count},
            timeout=8,
        )
        resp.raise_for_status()
        results = resp.json().get("web", {}).get("results", [])
        return [{"title": r.get("title"), "url": r.get("url"), "snippet": r.get("description")} for r in results]
    except Exception as e:
        logger.error("Brave search error: %s", e)
        return []


# ── Google Custom Search ──────────────────────────────────
def google_search(query: str, count: int = 5) -> list[dict]:
    api_key = os.getenv("GOOGLE_CSE_KEY")
    cx = os.getenv("GOOGLE_CSE_CX")
    if not api_key or not cx:
        logger.warning("GOOGLE_CSE_KEY or GOOGLE_CSE_CX not set.")
        return []
    try:
        resp = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"key": api_key, "cx": cx, "q": query, "num": count},
            timeout=8,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return [{"title": i.get("title"), "url": i.get("link"), "snippet": i.get("snippet")} for i in items]
    except Exception as e:
        logger.error("Google search error: %s", e)
        return []


# ── Google Cloud Vision ───────────────────────────────────
def _compress_image(image_base64: str, mime_type: str = "image/jpeg", max_size_bytes: int = 4000000) -> str:
    """Compress image if it exceeds max size. Returns base64 string."""
    if not HAS_PIL:
        return image_base64

    try:
        raw = base64.b64decode(image_base64)
        if len(raw) <= max_size_bytes:
            return image_base64

        img = Image.open(io.BytesIO(raw))

        # Scale down until under size limit
        quality = 85
        while quality > 30:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG" if mime_type == "image/jpeg" else "PNG", quality=quality, optimize=True)
            compressed = buffer.getvalue()
            if len(compressed) <= max_size_bytes:
                return base64.b64encode(compressed).decode('utf-8')
            quality -= 5

        return image_base64
    except Exception as e:
        logger.warning("Image compression failed: %s", e)
        return image_base64


def analyze_image(image_base64: str, mime_type: str = "image/jpeg") -> dict:
    api_key = os.getenv("GOOGLE_VISION_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_VISION_API_KEY not set.")
        return {}

    try:
        if not image_base64 or not isinstance(image_base64, str):
            logger.error("analyze_image: invalid image_base64")
            return {}

        # Validate base64
        try:
            base64.b64decode(image_base64[:100])
        except Exception:
            logger.error("analyze_image: invalid base64 data")
            return {}

        # Compress if needed
        image_base64 = _compress_image(image_base64, mime_type)

        payload = {
            "requests": [{
                "image": {"content": image_base64},
                "features": [
                    {"type": "LABEL_DETECTION", "maxResults": 10},
                    {"type": "TEXT_DETECTION"},
                    {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
                    {"type": "SAFE_SEARCH_DETECTION"},
                ]
            }]
        }
        resp = requests.post(
            f"https://vision.googleapis.com/v1/images:annotate?key={api_key}",
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        r = resp.json().get("responses", [{}])[0]

        # Check for API errors
        if "error" in r:
            logger.error("Vision API response error: %s", r["error"])
            return {}

        labels = [l["description"] for l in r.get("labelAnnotations", [])]
        text = r.get("fullTextAnnotation", {}).get("text", "")
        objects = [o["name"] for o in r.get("localizedObjectAnnotations", [])]
        return {"labels": labels, "text": text, "objects": objects}
    except requests.exceptions.Timeout:
        logger.error("Vision API timeout (image too large?)")
        return {}
    except requests.exceptions.ConnectionError as e:
        logger.error("Vision API connection error: %s", e)
        return {}
    except Exception as e:
        logger.error("Vision API error: %s", e)
        return {}


# ── Google Text-to-Speech ─────────────────────────────────
def text_to_speech(text: str, language_code: str = "en-GB", voice_name: str = "en-GB-Neural2-B") -> str | None:
    """Returns base64-encoded MP3 audio or None on failure."""
    api_key = os.getenv("GOOGLE_TTS_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_TTS_API_KEY not set.")
        return None
    try:
        payload = {
            "input": {"text": text[:4000]},
            "voice": {"languageCode": language_code, "name": voice_name},
            "audioConfig": {"audioEncoding": "MP3"},
        }
        resp = requests.post(
            f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}",
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("audioContent")
    except Exception as e:
        logger.error("TTS error: %s", e)
        return None

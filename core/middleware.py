"""
core/middleware.py
GI;WG? filter as MAF middleware.
The filter was always middleware. Now it's official.
"""

import logging
from core.filter import WootangularFilter, FilterResult

logger = logging.getLogger(__name__)


class GIWGMiddleware:
    """
    GI;WG? filter as MAF middleware.
    Runs on every agent step. Invisible gate. Always on.
    Five questions. In order. All must pass.
    Real Recognize Really.
    """

    def __init__(self):
        self._filter = WootangularFilter()

    async def on_agent_step(self, request, handler):
        candidate = self._build_candidate(request)
        result = self._filter.run(candidate)

        if result["result"] == FilterResult.BOOLSHIT:
            logger.warning(
                "[GI;WG?] BOOLSHIT — failed at: %s | %s",
                result["failed_at"],
                result["justification"]
            )
            raise FilterViolation(
                failed_at=result["failed_at"],
                justification=result["justification"]
            )

        if result["result"] == FilterResult.DEFER:
            logger.info("[GI;WG?] DEFER — %s", result["justification"])
            raise FilterDeferred(justification=result["justification"])

        # THE_SHIT — pass through
        logger.debug("[GI;WG?] THE_SHIT — agent step cleared")
        return await handler(request)

    def _build_candidate(self, request) -> dict:
        context = getattr(request, "context", {}) or {}
        message = getattr(request, "message", "") or ""
        return {
            "name":    context.get("agent_name", "unknown"),
            "offer":   message,
            "claim":   context.get("claim", ""),
            "deed":    context.get("deed", ""),
            "gi_wg":   context.get("gi_wg", True),
            "yes_and": context.get("yes_and", True),
        }


class FilterViolation(Exception):
    def __init__(self, failed_at: str, justification: str):
        super().__init__(justification)
        self.failed_at = failed_at
        self.justification = justification


class FilterDeferred(Exception):
    def __init__(self, justification: str):
        super().__init__(justification)
        self.justification = justification

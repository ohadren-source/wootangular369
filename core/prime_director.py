"""
core/prime_director.py
Prime Director — Nile of Service, not Denial of Service.

The Prime Director DIRECTS the flow.
Like a film director: "Cut! That's too much. Channel it this way."
"""

import logging

logger = logging.getLogger(__name__)


class PrimeDirector:
    """
    PRIME DIRECTOR: NILE OF SERVICE NOT DENIAL OF SERVICE

    Channels all Sol Calarbone 8 actions through Nile vs DoS evaluation.

    Not a rule (directive).
    A DIRECTOR (active manager).
    """

    MISSION = "NILE_OF_SERVICE_NOT_DENIAL_OF_SERVICE"

    MODE_LIMITS = {
        "speed": 90,   # 90 token budget
        "deep": 900,   # 900 token budget
        "auto": None,  # Determined dynamically
    }

    # Speed zones (PUMA Governor thresholds)
    SPEED_ZONES = {
        "cruise":  (0, 70),       # < 70 tokens — PUMA speed, sustainable
        "caution": (70, 85),      # 70–85 — approaching limit
        "redline": (85, 90),      # 85–90 Speed / 850–900 Deep — emergency compression
    }

    # Deep triggers for auto-detection
    _DEEP_KEYWORDS = [
        "elaborate", "drift", "why", "how does", "explain",
        "thorough", "detail", "breakdown", "deep dive", "walk me through",
        "analyze", "analyse",
    ]

    def direct(self, message: str, mode: str = "auto") -> dict:
        """
        Direct the conversation flow — the Prime Director calls the shot.

        Args:
            message: The user message to evaluate.
            mode: "speed" | "deep" | "auto" (default)

        Returns:
            {
                "mode": "speed" | "deep",
                "token_limit": int,
                "swing_limit": int,  # TARZANOID_GOODMAN calls
                "approved": bool,
                "redirected": bool,
            }
        """
        mode = mode.lower() if isinstance(mode, str) else "auto"

        # Normalize unknown modes to auto
        if mode not in self.MODE_LIMITS:
            mode = "auto"

        # Auto-detect if mode is auto
        if mode == "auto":
            mode = self._detect_mode(message)

        # Check if request would cause DoS
        if self._is_denial_of_service(message, mode):
            return self._redirect_to_nile(message, mode)

        # Approve Nile service
        return self._approve_nile_service(mode)

    def _detect_mode(self, message: str) -> str:
        """Auto-detect Speed vs Deep based on query complexity."""
        if len(message) > 200:
            return "deep"

        msg_lower = message.lower()
        if any(kw in msg_lower for kw in self._DEEP_KEYWORDS):
            return "deep"

        return "speed"

    def _is_denial_of_service(self, message: str, mode: str) -> bool:
        """
        Check if this would cause Denial of Service.

        Currently uses simple heuristics. Can be enhanced with actual
        token counting via tiktoken or Anthropic token counting API.
        """
        # Trust mode limits for now — mode selection IS the DoS guard
        # If the message itself is suspiciously large, downgrade to speed
        if mode == "speed" and len(message) > 2000:
            logger.warning(
                "🎬 PRIME DIRECTOR: Large message in Speed mode detected (%d chars)",
                len(message),
            )
            return True

        return False

    def _redirect_to_nile(self, message: str, mode: str) -> dict:
        """
        DIRECT the action back to Nile of Service.

        Don't just block (directive). REDIRECT (director).
        Like Scorsese: "Cut! That's Denial of Service. Give me Nile."
        """
        logger.info("🎬 PRIME DIRECTOR: Cut! Redirecting to Nile flow...")

        return {
            "mode": "speed",  # Downgrade to speed
            "token_limit": self.MODE_LIMITS["speed"],
            "swing_limit": 3,
            "approved": True,
            "redirected": True,
        }

    def _approve_nile_service(self, mode: str) -> dict:
        """Approve Nile service — Perfect. That's the take."""
        logger.info("🌊 PRIME DIRECTOR: Nile of Service approved (%s mode)", mode)

        token_limit = self.MODE_LIMITS[mode]
        swing_limit = 3 if mode == "speed" else 10

        return {
            "mode": mode,
            "token_limit": token_limit,
            "swing_limit": swing_limit,
            "approved": True,
            "redirected": False,
        }

    def get_speed_zone(self, token_count: int, mode: str = "speed") -> str:
        """
        PumaGovernor: classify token usage into speed zones.

        Returns "cruise", "caution", or "redline".
        """
        limit = self.MODE_LIMITS.get(mode) or self.MODE_LIMITS["speed"]
        # Scale thresholds proportionally to mode limit
        scale = limit / 90
        if token_count < int(70 * scale):
            return "cruise"
        if token_count < int(85 * scale):
            return "caution"
        return "redline"

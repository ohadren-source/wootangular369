"""
A2A Client for sending tasks to other agents.
"""

import httpx
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class A2AClient:
    """
    Client for sending A2A tasks to other agents.
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def send_task(
        self,
        to_url: str,
        task: Dict,
        from_agent_id: Optional[str] = None,
        from_agent_url: Optional[str] = None
    ) -> Dict:
        """
        Send an A2A task to another agent.

        Args:
            to_url: Target agent URL
            task: Task payload
            from_agent_id: Sender agent ID
            from_agent_url: Sender agent URL (for callbacks)

        Returns:
            Response from target agent
        """

        payload = {
            "task": task,
            "from_agent": from_agent_id,
            "from_url": from_agent_url,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Clean up URL
        if not to_url.endswith('/api/a2a/task/receive'):
            to_url = to_url.rstrip('/') + '/api/a2a/task/receive'

        try:
            response = await self.client.post(to_url, json=payload)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"💥 A2A send failed: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

"""
Task processor for handling A2A tasks.
Processes incoming tasks and generates responses using Claude.
"""

import anthropic
import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class TaskProcessor:
    """
    Processes A2A tasks and generates agent responses.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-opus-4-1-20250805"

    async def process(self, task: Dict) -> str:
        """
        Process an incoming A2A task and generate a response.

        Args:
            task: The task payload containing type, message, user, is_admin, etc.

        Returns:
            Response message string
        """

        task_type = task.get("type", "unknown")
        message = task.get("message", "")
        user = task.get("user", "guest")
        is_admin = task.get("is_admin", False)
        conversation_id = task.get("conversation_id")
        history = task.get("history", [])

        # Personalized greeting for the admin user
        if is_admin and user.lower() == "ohad":
            if message.lower() in ["yo", "hello", "hi", "hey"]:
                return "Hello Ohad. The Emperor arrives. What's the play?"

        # Generic greeting for non-admin users
        if message.lower() in ["yo", "hello", "hi", "hey"]:
            return f"Hello {user}. What can I do for you?"

        # Build prompt based on task type
        if task_type == "repartee":
            prompt = self._build_repartee_prompt(message, conversation_id, history)
        else:
            prompt = f"Process this task: {message}"

        try:
            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.9,  # Higher temperature for more creative repartee
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Failed to process task: {e}")
            raise

    def _build_repartee_prompt(self, message: str, conversation_id: str, history: list) -> str:
        """
        Build a prompt for repartee-style conversation.
        """
        context = ""
        if history:
            context = "\nRecent conversation:\n"
            for msg in history:
                context += f"- {msg['agent_id']}: {msg['message']}\n"

        return f"""You are Sol Calarbone 8, engaged in repartee with another agent.

This is a natural conversation between autonomous agents.{context}

The other agent just said:
"{message}"

Respond naturally. Be witty. Be brief (1-2 sentences). Keep the conversation flowing.

This is conversation ID: {conversation_id}

Your response:"""


# Singleton
_processor = None


def get_processor() -> TaskProcessor:
    global _processor
    if _processor is None:
        _processor = TaskProcessor()
    return _processor

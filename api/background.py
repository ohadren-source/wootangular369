"""
Background worker for processing instance-routed tasks.
Runs in separate daemon thread, polls Redis queue for tasks.
Enables A2A task routing between Sol 8 instances.
"""

import threading
import time
import json
import logging
from api.instance import redis_client, INSTANCE_ID

logger = logging.getLogger(__name__)


class BackgroundTaskProcessor:
    """Polls Redis queue for tasks routed to this instance."""

    def __init__(self):
        self.running = False
        self.thread = None

    def start(self):
        """Start background processing thread."""
        if self.running:
            logger.warning("[BACKGROUND] Processor already running")
            return

        if not redis_client:
            logger.warning("[BACKGROUND] Redis not available, background processing disabled")
            return

        self.running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        logger.info(f"[BACKGROUND] Task processor started for {INSTANCE_ID}")

    def stop(self):
        """Stop background processing gracefully."""
        if not self.running:
            return

        logger.info(f"[BACKGROUND] Stopping task processor for {INSTANCE_ID}")
        self.running = False

        if self.thread:
            self.thread.join(timeout=5)
            logger.info("[BACKGROUND] Task processor stopped")

    def _process_loop(self):
        """Main processing loop — polls Redis queue."""
        queue_key = f"sol8:tasks:{INSTANCE_ID}"

        logger.info(f"[BACKGROUND] Process loop started, monitoring {queue_key}")

        while self.running:
            try:
                # Block for 1 second waiting for task
                result = redis_client.brpop(queue_key, timeout=1)

                if result:
                    _, task_json = result
                    task_envelope = json.loads(task_json)
                    self._process_task(task_envelope)

            except Exception as e:
                logger.error(f"[BACKGROUND] Error in process loop: {e}")
                time.sleep(1)

    def _process_task(self, task_envelope):
        """Process a single routed task."""
        task_id = task_envelope.get('task_id', 'unknown')
        from_instance = task_envelope.get('from_instance', 'unknown')
        task = task_envelope.get('task', {})

        logger.info(f"[BACKGROUND] Processing task {task_id} from {from_instance}")

        try:
            # Task processing would happen here
            # For now, just log it
            message = task.get('message', '')
            logger.info(f"[BACKGROUND] Task content: {message[:100]}...")

            # In full implementation, would:
            # 1. Pass to Sol 8 processing
            # 2. Store response
            # 3. Optionally publish back to sender via Redis pubsub

        except Exception as e:
            logger.error(f"[BACKGROUND] Failed to process task {task_id}: {e}")


# Global processor instance
processor = BackgroundTaskProcessor()


def init_background_processing():
    """Initialize background processing (called at app startup)."""
    processor.start()


def stop_background_processing():
    """Stop background processing (called at app shutdown)."""
    processor.stop()

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from loguru import logger
from app.core import models

RESULT_EXPIRY_TIME = timedelta(hours=1)


class TaskManager:
    def __init__(self):
        self.task_status: Dict[str, models.TaskStatus] = {}
        self.task_results: Dict[str, models.TaskResult] = {}
        self.current_task_id = None
        self.last_task_type: Optional[models.Task] = None

        asyncio.create_task(self._cleanup_expired_tasks())

    async def _cleanup_expired_tasks(self):
        while True:
            await asyncio.sleep(RESULT_EXPIRY_TIME.seconds / 4)
            now = datetime.now()
            expired_tasks = [
                task_id for task_id, result in self.task_results.items() if now - result.timestamp > RESULT_EXPIRY_TIME
            ]
            for task_id in expired_tasks:
                self.task_results.pop(task_id, None)
            logger.info(f"Cleaned up expired tasks; Removed {len(expired_tasks)} expired tasks")

    def task_is_processing(self, task_id: str) -> bool:
        status = self.task_status.get(task_id, None)
        return status == models.TaskStatus.Processing

    def clear_and_return_task_status_and_result(
        self, task_id: str
    ) -> Tuple[Optional[models.TaskStatus], Optional[models.TaskResult]]:
        status = self.task_status.pop(task_id, None)
        result = self.task_results.pop(task_id, None)
        return status, result


task_manager = TaskManager()

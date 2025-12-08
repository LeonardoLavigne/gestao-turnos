from fastapi import BackgroundTasks
from app.domain.ports.background import BackgroundTaskQueue
from typing import Callable, Any

class FastAPIBackgroundTaskQueue(BackgroundTaskQueue):
    def __init__(self, tasks: BackgroundTasks):
        self.tasks = tasks

    def add_task(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self.tasks.add_task(func, *args, **kwargs)

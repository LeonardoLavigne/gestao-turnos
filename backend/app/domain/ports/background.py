from typing import Protocol, Callable, Any

class BackgroundTaskQueue(Protocol):
    def add_task(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Add a task to be executed in the background."""
        ...

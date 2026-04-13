"""Queue implementations for the workflow orchestration system.

This module exports the queue interface and implementations:
    - ITaskQueue: Abstract interface for task queues
    - GitHubQueue: GitHub Issues-backed queue implementation
"""

from src.queue.github_queue import GitHubQueue, ITaskQueue

__all__ = [
    "GitHubQueue",
    "ITaskQueue",
]

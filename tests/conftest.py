"""Pytest configuration and shared fixtures.

This module provides common fixtures used across the test suite,
including mock HTTP clients, sample work items, and test configurations.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from src.models.work_item import TaskType, WorkItem, WorkItemStatus
from src.queue.github_queue import ITaskQueue


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_work_item() -> WorkItem:
    """Create a sample work item for testing."""
    return WorkItem(
        id="test-issue-123",
        issue_number=123,
        source_url="https://github.com/test-owner/test-repo/issues/123",
        context_body="## Task\nImplement feature X",
        target_repo_slug="test-owner/test-repo",
        task_type=TaskType.IMPLEMENT,
        status=WorkItemStatus.QUEUED,
        node_id="I_test123",
    )


@pytest.fixture
def sample_plan_item() -> WorkItem:
    """Create a sample planning work item for testing."""
    return WorkItem(
        id="test-issue-456",
        issue_number=456,
        source_url="https://github.com/test-owner/test-repo/issues/456",
        context_body="## Application Plan\nCreate a new service",
        target_repo_slug="test-owner/test-repo",
        task_type=TaskType.PLAN,
        status=WorkItemStatus.QUEUED,
        node_id="I_test456",
    )


@pytest.fixture
def mock_queue() -> ITaskQueue:
    """Create a mock task queue for testing."""
    queue = AsyncMock(spec=ITaskQueue)
    queue.add_to_queue = AsyncMock(return_value=True)
    queue.fetch_queued_tasks = AsyncMock(return_value=[])
    queue.update_status = AsyncMock()
    queue.claim_task = AsyncMock(return_value=True)
    queue.post_heartbeat = AsyncMock()
    queue.close = AsyncMock()
    return queue


@pytest_asyncio.fixture
async def mock_httpx_client() -> AsyncGenerator[MagicMock, None]:
    """Create a mock httpx AsyncClient for testing."""
    client = MagicMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.delete = AsyncMock()
    client.aclose = AsyncMock()
    yield client

"""Tests for the GitHub Queue implementation.

This module tests:
- GitHubQueue class methods
- HTTP client interactions
- Rate limiting and error handling
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.models.work_item import TaskType, WorkItem, WorkItemStatus
from src.queue.github_queue import GitHubQueue, ITaskQueue


class TestGitHubQueue:
    """Tests for GitHubQueue class."""

    @pytest.fixture
    def queue(self) -> GitHubQueue:
        """Create a GitHubQueue instance for testing."""
        return GitHubQueue(
            token="test_token",
            org="test-org",
            repo="test-repo",
        )

    @pytest.fixture
    def mock_issue_response(self) -> dict:
        """Create a mock GitHub API issue response."""
        return {
            "id": 123456,
            "node_id": "I_test123",
            "number": 42,
            "html_url": "https://github.com/test-org/test-repo/issues/42",
            "title": "Test Issue",
            "body": "## Task\nImplement feature X",
            "state": "open",
            "labels": [
                {
                    "name": "agent:queued",
                    "id": 1,
                    "node_id": "L_1",
                    "url": "",
                    "color": "blue",
                    "default": False,
                }
            ],
        }

    @pytest.mark.asyncio
    async def test_close_releases_resources(self, queue: GitHubQueue) -> None:
        """Test that close() properly releases the HTTP client."""
        await queue.close()
        # Should not raise any exceptions

    @pytest.mark.asyncio
    async def test_fetch_queued_tasks_empty_repo(self) -> None:
        """Test that fetch_queued_tasks returns empty list when org/repo not set."""
        queue = GitHubQueue(token="test", org="", repo="")
        tasks = await queue.fetch_queued_tasks()
        assert tasks == []
        await queue.close()

    @pytest.mark.asyncio
    async def test_fetch_queued_tasks_success(
        self, queue: GitHubQueue, mock_issue_response: dict
    ) -> None:
        """Test successful fetch of queued tasks."""
        with patch.object(queue._client, "get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [mock_issue_response]
            mock_get.return_value = mock_response

            tasks = await queue.fetch_queued_tasks()

            assert len(tasks) == 1
            assert tasks[0].issue_number == 42
            assert tasks[0].task_type == TaskType.IMPLEMENT

        await queue.close()

    @pytest.mark.asyncio
    async def test_fetch_queued_tasks_rate_limited(self, queue: GitHubQueue) -> None:
        """Test that rate limit errors are propagated."""
        with patch.object(queue._client, "get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Rate limited",
                request=MagicMock(),
                response=mock_response,
            )
            mock_get.return_value = mock_response

            with pytest.raises(httpx.HTTPStatusError):
                await queue.fetch_queued_tasks()

        await queue.close()

    @pytest.mark.asyncio
    async def test_fetch_queued_tasks_plan_detection(self, queue: GitHubQueue) -> None:
        """Test that plan tasks are detected from labels and title."""
        plan_issue = {
            "id": 789,
            "node_id": "I_plan",
            "number": 100,
            "html_url": "https://github.com/test-org/test-repo/issues/100",
            "title": "[Plan] Create new service",
            "body": "Plan description",
            "state": "open",
            "labels": [
                {
                    "name": "agent:plan",
                    "id": 2,
                    "node_id": "L_2",
                    "url": "",
                    "color": "green",
                    "default": False,
                }
            ],
        }

        with patch.object(queue._client, "get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [plan_issue]
            mock_get.return_value = mock_response

            tasks = await queue.fetch_queued_tasks()

            assert len(tasks) == 1
            assert tasks[0].task_type == TaskType.PLAN

        await queue.close()

    @pytest.mark.asyncio
    async def test_add_to_queue_success(
        self, queue: GitHubQueue, sample_work_item: WorkItem
    ) -> None:
        """Test successfully adding item to queue."""
        with patch.object(queue._client, "post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = await queue.add_to_queue(sample_work_item)

            assert result is True
            mock_post.assert_called_once()

        await queue.close()

    @pytest.mark.asyncio
    async def test_add_to_queue_failure(
        self, queue: GitHubQueue, sample_work_item: WorkItem
    ) -> None:
        """Test failure to add item to queue."""
        with patch.object(queue._client, "post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_post.return_value = mock_response

            result = await queue.add_to_queue(sample_work_item)

            assert result is False

        await queue.close()

    @pytest.mark.asyncio
    async def test_update_status_with_comment(
        self, queue: GitHubQueue, sample_work_item: WorkItem
    ) -> None:
        """Test updating status with a comment."""
        sample_work_item.status = WorkItemStatus.IN_PROGRESS

        with (
            patch.object(queue._client, "delete", new_callable=AsyncMock) as mock_delete,
            patch.object(queue._client, "post", new_callable=AsyncMock) as mock_post,
        ):
            mock_delete.return_value = MagicMock(status_code=200)
            mock_post.return_value = MagicMock(status_code=201)

            await queue.update_status(
                sample_work_item,
                WorkItemStatus.SUCCESS,
                comment="Task completed!",
            )

            # Should call delete for old label and post for new label + comment
            assert mock_delete.call_count == 1
            assert mock_post.call_count == 2  # label + comment

        await queue.close()

    @pytest.mark.asyncio
    async def test_claim_task_success(self, queue: GitHubQueue, sample_work_item: WorkItem) -> None:
        """Test successful task claiming with assign-then-verify."""
        with (
            patch.object(queue._client, "post", new_callable=AsyncMock) as mock_post,
            patch.object(queue._client, "get", new_callable=AsyncMock) as mock_get,
            patch.object(queue._client, "delete", new_callable=AsyncMock) as mock_delete,
        ):
            # Setup: assignment post succeeds
            mock_post.return_value = MagicMock(status_code=201)

            # Setup: verify get shows correct assignee
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"assignees": [{"login": "test-bot"}]},
            )

            # Setup: label operations succeed
            mock_delete.return_value = MagicMock(status_code=200)

            result = await queue.claim_task(
                sample_work_item,
                "sentinel-abc123",
                bot_login="test-bot",
            )

            assert result is True

        await queue.close()

    @pytest.mark.asyncio
    async def test_claim_task_lost_race(
        self, queue: GitHubQueue, sample_work_item: WorkItem
    ) -> None:
        """Test task claiming when another sentinel wins the race."""
        with (
            patch.object(queue._client, "post", new_callable=AsyncMock) as mock_post,
            patch.object(queue._client, "get", new_callable=AsyncMock) as mock_get,
        ):
            # Setup: assignment post succeeds
            mock_post.return_value = MagicMock(status_code=201)

            # Setup: verify get shows different assignee (race lost)
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"assignees": [{"login": "other-sentinel"}]},
            )

            result = await queue.claim_task(
                sample_work_item,
                "sentinel-abc123",
                bot_login="test-bot",
            )

            assert result is False

        await queue.close()

    @pytest.mark.asyncio
    async def test_post_heartbeat(self, queue: GitHubQueue, sample_work_item: WorkItem) -> None:
        """Test posting heartbeat comment."""
        with patch.object(queue._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(status_code=201)

            await queue.post_heartbeat(sample_work_item, "sentinel-abc123", 300)

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "Heartbeat" in call_args[1]["json"]["body"]

        await queue.close()


class TestITaskQueue:
    """Tests for ITaskQueue interface."""

    def test_is_abstract(self) -> None:
        """Test that ITaskQueue cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ITaskQueue()  # type: ignore[abstract]


# ruff: noqa: PLC0415 - Imports inside test functions to test import paths

"""Comprehensive tests for work_item module.

Tests cover:
- WorkItem model instantiation and validation
- TaskType and WorkItemStatus enums
- scrub_secrets() utility function
- Edge cases and error conditions
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from src.models.work_item import (
    TaskType,
    WorkItem,
    WorkItemStatus,
    scrub_secrets,
)


class TestTaskType:
    """Tests for TaskType enum."""

    def test_task_type_plan_value(self) -> None:
        """TaskType.PLAN should have value 'plan'."""
        assert TaskType.PLAN.value == "plan"

    def test_task_type_implement_value(self) -> None:
        """TaskType.IMPLEMENT should have value 'implement'."""
        assert TaskType.IMPLEMENT.value == "implement"

    def test_task_type_is_string_enum(self) -> None:
        """TaskType should be a StrEnum, so values are strings."""
        assert isinstance(TaskType.PLAN, str)
        assert isinstance(TaskType.IMPLEMENT, str)

    def test_task_type_string_comparison(self) -> None:
        """TaskType values should compare equal to their string equivalents."""
        assert TaskType.PLAN == "plan"
        assert TaskType.IMPLEMENT == "implement"

    def test_task_type_count(self) -> None:
        """TaskType should have exactly 2 members."""
        assert len(TaskType) == 2


class TestWorkItemStatus:
    """Tests for WorkItemStatus enum."""

    def test_queued_value(self) -> None:
        """WorkItemStatus.QUEUED should have value 'agent:queued'."""
        assert WorkItemStatus.QUEUED.value == "agent:queued"

    def test_in_progress_value(self) -> None:
        """WorkItemStatus.IN_PROGRESS should have value 'agent:in-progress'."""
        assert WorkItemStatus.IN_PROGRESS.value == "agent:in-progress"

    def test_success_value(self) -> None:
        """WorkItemStatus.SUCCESS should have value 'agent:success'."""
        assert WorkItemStatus.SUCCESS.value == "agent:success"

    def test_error_value(self) -> None:
        """WorkItemStatus.ERROR should have value 'agent:error'."""
        assert WorkItemStatus.ERROR.value == "agent:error"

    def test_infra_failure_value(self) -> None:
        """WorkItemStatus.INFRA_FAILURE should have value 'agent:infra-failure'."""
        assert WorkItemStatus.INFRA_FAILURE.value == "agent:infra-failure"

    def test_stalled_budget_value(self) -> None:
        """WorkItemStatus.STALLED_BUDGET should have value 'agent:stalled-budget'."""
        assert WorkItemStatus.STALLED_BUDGET.value == "agent:stalled-budget"

    def test_all_statuses_have_agent_prefix(self) -> None:
        """All WorkItemStatus values should start with 'agent:' prefix."""
        for status in WorkItemStatus:
            assert status.value.startswith("agent:")

    def test_status_is_string_enum(self) -> None:
        """WorkItemStatus should be a StrEnum, so values are strings."""
        for status in WorkItemStatus:
            assert isinstance(status, str)

    def test_status_count(self) -> None:
        """WorkItemStatus should have exactly 6 members."""
        assert len(WorkItemStatus) == 6

    def test_status_maps_to_github_labels(self) -> None:
        """WorkItemStatus values should map correctly to GitHub label format."""
        expected_labels = {
            "agent:queued",
            "agent:in-progress",
            "agent:success",
            "agent:error",
            "agent:infra-failure",
            "agent:stalled-budget",
        }
        actual_labels = {status.value for status in WorkItemStatus}
        assert actual_labels == expected_labels


class TestWorkItem:
    """Tests for WorkItem Pydantic model."""

    @pytest.fixture
    def valid_work_item_data(self) -> dict[str, Any]:
        """Provide valid data for WorkItem instantiation."""
        return {
            "id": "issue-123",
            "issue_number": 123,
            "source_url": "https://github.com/owner/repo/issues/123",
            "context_body": "## Task\nImplement feature X",
            "target_repo_slug": "owner/repo",
            "task_type": TaskType.IMPLEMENT,
            "status": WorkItemStatus.QUEUED,
            "node_id": "I_123",
            "metadata": {"custom": "value"},
        }

    def test_work_item_instantiation_with_all_fields(
        self, valid_work_item_data: dict[str, Any]
    ) -> None:
        """WorkItem should instantiate with all required fields."""
        item = WorkItem(**valid_work_item_data)

        assert item.id == "issue-123"
        assert item.issue_number == 123
        assert item.source_url == "https://github.com/owner/repo/issues/123"
        assert item.context_body == "## Task\nImplement feature X"
        assert item.target_repo_slug == "owner/repo"
        assert item.task_type == TaskType.IMPLEMENT
        assert item.status == WorkItemStatus.QUEUED
        assert item.node_id == "I_123"

    def test_work_item_with_integer_id(self, valid_work_item_data: dict[str, Any]) -> None:
        """WorkItem should accept integer IDs."""
        valid_work_item_data["id"] = 12345
        item = WorkItem(**valid_work_item_data)

        assert item.id == 12345
        assert isinstance(item.id, int)

    def test_work_item_with_string_id(self, valid_work_item_data: dict[str, Any]) -> None:
        """WorkItem should accept string IDs."""
        valid_work_item_data["id"] = "custom-id-abc"
        item = WorkItem(**valid_work_item_data)

        assert item.id == "custom-id-abc"
        assert isinstance(item.id, str)

    def test_work_item_with_plan_task_type(self, valid_work_item_data: dict[str, Any]) -> None:
        """WorkItem should accept PLAN task type."""
        valid_work_item_data["task_type"] = TaskType.PLAN
        item = WorkItem(**valid_work_item_data)

        assert item.task_type == TaskType.PLAN

    def test_work_item_with_different_statuses(self, valid_work_item_data: dict[str, Any]) -> None:
        """WorkItem should accept all WorkItemStatus values."""
        for status in WorkItemStatus:
            valid_work_item_data["status"] = status
            item = WorkItem(**valid_work_item_data)
            assert item.status == status

    def test_work_item_with_empty_metadata(self, valid_work_item_data: dict[str, Any]) -> None:
        """WorkItem should accept empty metadata dict."""
        valid_work_item_data["metadata"] = {}
        item = WorkItem(**valid_work_item_data)

        assert item.metadata == {}

    def test_work_item_rejects_extra_fields_strict_validation(
        self, valid_work_item_data: dict[str, Any]
    ) -> None:
        """WorkItem should reject extra fields due to strict validation."""
        valid_work_item_data["extra_field"] = "should fail"

        with pytest.raises(ValidationError) as exc_info:
            WorkItem(**valid_work_item_data)

        assert "extra_field" in str(exc_info.value)
        assert "Extra inputs are not permitted" in str(exc_info.value)

    def test_work_item_rejects_missing_required_field(
        self, valid_work_item_data: dict[str, Any]
    ) -> None:
        """WorkItem should reject missing required fields."""
        del valid_work_item_data["source_url"]

        with pytest.raises(ValidationError) as exc_info:
            WorkItem(**valid_work_item_data)

        assert "source_url" in str(exc_info.value)

    def test_work_item_rejects_invalid_task_type(
        self, valid_work_item_data: dict[str, Any]
    ) -> None:
        """WorkItem should reject invalid task_type values."""
        valid_work_item_data["task_type"] = "invalid_type"

        with pytest.raises(ValidationError):
            WorkItem(**valid_work_item_data)

    def test_work_item_model_dump(self, valid_work_item_data: dict[str, Any]) -> None:
        """WorkItem should serialize correctly via model_dump()."""
        item = WorkItem(**valid_work_item_data)
        dumped = item.model_dump()

        assert dumped["id"] == "issue-123"
        assert dumped["task_type"] == "implement"  # StrEnum serializes to string
        assert dumped["status"] == "agent:queued"


class TestScrubSecrets:
    """Tests for scrub_secrets() utility function."""

    def test_scrub_github_pat_token(self) -> None:
        """Should redact GitHub Personal Access Tokens."""
        text = "Token: ghp_FAKE_TOKEN_FOR_TESTING_12345"
        result = scrub_secrets(text)

        assert result == "Token: [REDACTED]"
        assert "ghp_" not in result

    def test_scrub_github_server_token(self) -> None:
        """Should redact GitHub Server-to-Server tokens."""
        text = "Server token: ghs_FAKE_SERVER_TOKEN_12345"
        result = scrub_secrets(text)

        assert result == "Server token: [REDACTED]"
        assert "ghs_" not in result

    def test_scrub_bearer_token(self) -> None:
        """Should redact Bearer tokens while preserving 'Bearer' prefix."""
        text = "Authorization: Bearer abc123xyz789"
        result = scrub_secrets(text)

        assert result == "Authorization: Bearer [REDACTED]"
        assert "Bearer" in result

    def test_scrub_generic_token_assignment_equals(self) -> None:
        """Should redact generic token= assignments preserving equals separator."""
        text = "Config: token=supersecret123"
        result = scrub_secrets(text)

        assert result == "Config: token= [REDACTED]"
        assert "supersecret123" not in result

    def test_scrub_generic_token_assignment_colon(self) -> None:
        """Should redact generic token: assignments preserving colon separator."""
        text = "Config: token:anothersecret456"
        result = scrub_secrets(text)

        assert result == "Config: token: [REDACTED]"
        assert "anothersecret456" not in result

    def test_scrub_openai_api_key(self) -> None:
        """Should redact OpenAI API keys."""
        text = "API Key: sk-FAKE_OPENAI_KEY_12345"
        result = scrub_secrets(text)

        assert result == "API Key: [REDACTED]"
        assert "sk-" not in result

    def test_scrub_multiple_secrets_combined(self) -> None:
        """Should redact multiple different secrets in one text."""
        text = """
        GitHub PAT: ghp_FAKE_GITHUB_PAT_12345
        OpenAI Key: sk-FAKE_OPENAI_KEY_12345
        Bearer: Bearer FAKE_BEARER_TOKEN
        Token assignment: token=FAKE_SECRET_VALUE
        """
        result = scrub_secrets(text)

        assert "ghp_" not in result
        assert "sk-FAKE" not in result
        assert "FAKE_BEARER_TOKEN" not in result
        assert "FAKE_SECRET_VALUE" not in result
        assert result.count("[REDACTED]") >= 4

    def test_scrub_preserves_non_secret_content(self) -> None:
        """Should not modify content that doesn't contain secrets."""
        text = "This is a normal log message with no secrets."
        result = scrub_secrets(text)

        assert result == text

    def test_scrub_empty_string(self) -> None:
        """Should return empty string unchanged."""
        assert scrub_secrets("") == ""


class TestModuleImports:
    """Tests for module import structure."""

    def test_import_from_main_module(self) -> None:
        """Should be able to import from main models module."""
        from src.models import (
            TaskType,
            WorkItem,
            WorkItemStatus,
            scrub_secrets,
        )

        assert TaskType is not None
        assert WorkItem is not None
        assert WorkItemStatus is not None
        assert scrub_secrets is not None

    def test_import_from_work_item_module(self) -> None:
        """Should be able to import directly from work_item module."""
        from src.models.work_item import (
            TaskType,
            WorkItem,
            WorkItemStatus,
            scrub_secrets,
        )

        assert TaskType is not None
        assert WorkItem is not None
        assert WorkItemStatus is not None
        assert scrub_secrets is not None

    def test_all_exports_available(self) -> None:
        """All expected items should be in __all__."""
        from src.models import __all__

        expected = ["TaskType", "WorkItem", "WorkItemStatus", "scrub_secrets"]
        assert set(__all__) == set(expected)

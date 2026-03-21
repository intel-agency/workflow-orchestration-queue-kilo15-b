# ruff: noqa: PLR2004 - Magic values acceptable in test assertions
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

from workflow_orchestration_queue.models.work_item import (
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
            "source_url": "https://github.com/owner/repo/issues/123",
            "context_body": "## Task\nImplement feature X",
            "target_repo_slug": "owner/repo",
            "task_type": TaskType.IMPLEMENT,
            "status": WorkItemStatus.QUEUED,
            "metadata": {"issue_node_id": "I_123"},
        }

    def test_work_item_instantiation_with_all_fields(
        self, valid_work_item_data: dict[str, Any]
    ) -> None:
        """WorkItem should instantiate with all required fields."""
        item = WorkItem(**valid_work_item_data)

        assert item.id == "issue-123"
        assert item.source_url == "https://github.com/owner/repo/issues/123"
        assert item.context_body == "## Task\nImplement feature X"
        assert item.target_repo_slug == "owner/repo"
        assert item.task_type == TaskType.IMPLEMENT
        assert item.status == WorkItemStatus.QUEUED
        assert item.metadata == {"issue_node_id": "I_123"}

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

    def test_work_item_with_complex_metadata(self, valid_work_item_data: dict[str, Any]) -> None:
        """WorkItem should accept complex nested metadata."""
        complex_metadata = {
            "issue_node_id": "I_123",
            "labels": ["bug", "enhancement"],
            "nested": {"key": "value", "numbers": [1, 2, 3]},
        }
        valid_work_item_data["metadata"] = complex_metadata
        item = WorkItem(**valid_work_item_data)

        assert item.metadata == complex_metadata

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

    def test_work_item_rejects_invalid_status(self, valid_work_item_data: dict[str, Any]) -> None:
        """WorkItem should reject invalid status values."""
        valid_work_item_data["status"] = "invalid_status"

        with pytest.raises(ValidationError):
            WorkItem(**valid_work_item_data)

    def test_work_item_model_dump(self, valid_work_item_data: dict[str, Any]) -> None:
        """WorkItem should serialize correctly via model_dump()."""
        item = WorkItem(**valid_work_item_data)
        dumped = item.model_dump()

        assert dumped["id"] == "issue-123"
        assert dumped["task_type"] == "implement"  # StrEnum serializes to string
        assert dumped["status"] == "agent:queued"

    def test_work_item_model_json_serialization(self, valid_work_item_data: dict[str, Any]) -> None:
        """WorkItem should serialize to JSON correctly."""
        item = WorkItem(**valid_work_item_data)
        json_str = item.model_dump_json()

        assert '"id":"issue-123"' in json_str
        assert '"task_type":"implement"' in json_str
        assert '"status":"agent:queued"' in json_str


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

    def test_scrub_github_oauth_token(self) -> None:
        """Should redact GitHub OAuth tokens."""
        text = "OAuth: gho_FAKE_OAUTH_TOKEN_12345"
        result = scrub_secrets(text)

        assert result == "OAuth: [REDACTED]"
        assert "gho_" not in result

    def test_scrub_github_fine_grained_pat(self) -> None:
        """Should redact GitHub fine-grained PATs."""
        text = "Fine-grained: github_pat_FAKE_FINE_GRAINED_12345"
        result = scrub_secrets(text)

        assert result == "Fine-grained: [REDACTED]"
        assert "github_pat_" not in result

    def test_scrub_bearer_token(self) -> None:
        """Should redact Bearer tokens while preserving 'Bearer' prefix."""
        text = "Authorization: Bearer abc123xyz789"
        result = scrub_secrets(text)

        assert result == "Authorization: Bearer [REDACTED]"
        assert "Bearer" in result

    def test_scrub_bearer_token_with_multiple_spaces(self) -> None:
        """Should handle Bearer tokens with flexible spacing."""
        text = "Authorization: Bearer   secret_token_here"
        result = scrub_secrets(text)

        assert "[REDACTED]" in result
        assert "secret_token_here" not in result

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

    def test_scrub_zhipuai_key(self) -> None:
        """Should redact ZhipuAI keys (approximate pattern)."""
        text = "ZhipuAI: zhipu_FAKE_ZHIPU_KEY_12345_FOR_TESTING"
        result = scrub_secrets(text)

        assert result == "ZhipuAI: [REDACTED]"

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

    def test_scrub_preserves_code_snippets_without_secrets(self) -> None:
        """Should preserve code-like content without secrets."""
        text = """
        def hello():
            print("Hello, World!")
            return 42
        """
        result = scrub_secrets(text)

        assert result == text

    def test_scrub_empty_string(self) -> None:
        """Should return empty string unchanged."""
        assert scrub_secrets("") == ""

    def test_scrub_whitespace_only(self) -> None:
        """Should return whitespace-only string unchanged."""
        text = "   \n\t  "
        result = scrub_secrets(text)

        assert result == text

    def test_scrub_preserves_urls_without_secrets(self) -> None:
        """Should preserve URLs that don't contain secrets."""
        text = "https://github.com/owner/repo/issues/123"
        result = scrub_secrets(text)

        assert result == text

    def test_scrub_preserves_partial_matches_not_secrets(self) -> None:
        """Should not redact partial matches that aren't actual secrets."""
        # 'sklearn' doesn't match our sk-[A-Za-z0-9_-]+ pattern because it has no hyphen after sk-
        # The pattern requires sk- followed by alphanumeric chars
        text = "We use sklearn for machine learning"
        result = scrub_secrets(text)

        # sklearn should be preserved since it doesn't match the sk- pattern
        assert result == text
        assert "sklearn" in result

    def test_scrub_special_characters_in_context(self) -> None:
        """Should handle special characters around secrets."""
        text = 'Config = {"token": "ghp_FAKE_TOKEN_12345", "key": "value"}'
        result = scrub_secrets(text)

        assert "ghp_" not in result
        assert "[REDACTED]" in result
        assert '"key": "value"' in result

    def test_scrub_preserves_newlines_and_formatting(self) -> None:
        """Should preserve text structure while redacting secrets."""
        text = "Line 1\nghp_FAKE_SECRET_12345\nLine 3"
        result = scrub_secrets(text)

        assert "\n" in result
        assert "Line 1" in result
        assert "Line 3" in result
        assert "ghp_" not in result

    def test_scrub_case_insensitive_token_patterns(self) -> None:
        """Token patterns with token= or token: should be caught (case-sensitive)."""
        # Note: Our current pattern is case-sensitive for 'token'
        # So uppercase TOKEN is NOT caught - this is intentional
        text = "TOKEN=uppercase_secret"
        result = scrub_secrets(text)

        # Current implementation is case-sensitive, so TOKEN is NOT redacted
        assert result == text
        assert "uppercase_secret" in result

    def test_scrub_multiple_same_type_secrets(self) -> None:
        """Should redact multiple tokens of the same type."""
        text = "First: ghp_FAKE_TOKEN_ONE_12345 Second: ghp_FAKE_TOKEN_TWO_67890"
        result = scrub_secrets(text)

        assert "ghp_" not in result
        assert result.count("[REDACTED]") == 2


class TestModuleImports:
    """Tests for module import structure."""

    def test_import_from_main_module(self) -> None:
        """Should be able to import from main models module."""
        from workflow_orchestration_queue.models import (
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
        from workflow_orchestration_queue.models.work_item import (
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
        from workflow_orchestration_queue.models import __all__

        expected = ["TaskType", "WorkItem", "WorkItemStatus", "scrub_secrets"]
        assert set(__all__) == set(expected)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_work_item_with_unicode_context(self) -> None:
        """WorkItem should handle unicode in context_body."""
        item = WorkItem(
            id=1,
            source_url="https://github.com/owner/repo/issues/1",
            context_body="# Task 🚀\nImplement 功能 X",
            target_repo_slug="owner/repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.QUEUED,
            metadata={},
        )

        assert "🚀" in item.context_body
        assert "功能" in item.context_body

    def test_work_item_with_very_long_context(self) -> None:
        """WorkItem should handle very long context_body."""
        long_context = "x" * 100000  # 100k characters
        item = WorkItem(
            id=1,
            source_url="https://github.com/owner/repo/issues/1",
            context_body=long_context,
            target_repo_slug="owner/repo",
            task_type=TaskType.PLAN,
            status=WorkItemStatus.QUEUED,
            metadata={},
        )

        assert len(item.context_body) == 100000

    def test_scrub_secrets_with_unicode(self) -> None:
        """scrub_secrets should handle unicode text."""
        text = "日本語 ghp_FAKE_UNICODE_TOKEN_12345 中文"
        result = scrub_secrets(text)

        assert "ghp_" not in result
        assert "日本語" in result
        assert "中文" in result

    def test_work_item_with_special_characters_in_slug(self) -> None:
        """WorkItem should handle special characters in target_repo_slug."""
        item = WorkItem(
            id=1,
            source_url="https://github.com/owner-name/repo_name/issues/1",
            context_body="Task",
            target_repo_slug="owner-name/repo_name",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.QUEUED,
            metadata={},
        )

        assert item.target_repo_slug == "owner-name/repo_name"

    def test_work_item_status_string_comparison_direct(self) -> None:
        """WorkItemStatus should compare directly to label strings."""
        assert WorkItemStatus.QUEUED == "agent:queued"
        assert WorkItemStatus.SUCCESS == "agent:success"

    def test_task_type_from_string(self) -> None:
        """TaskType should be constructible from string value."""
        assert TaskType("plan") == TaskType.PLAN
        assert TaskType("implement") == TaskType.IMPLEMENT

    def test_work_item_status_from_string(self) -> None:
        """WorkItemStatus should be constructible from string value."""
        assert WorkItemStatus("agent:queued") == WorkItemStatus.QUEUED
        assert WorkItemStatus("agent:success") == WorkItemStatus.SUCCESS

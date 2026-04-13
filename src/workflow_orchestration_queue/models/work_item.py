"""Work item data models and utilities for OS-APOW orchestration.

This module provides the core data structures for representing work items
in the orchestration queue, including task types, status tracking, and
secret sanitization utilities.
"""

from __future__ import annotations

import enum
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from pydantic import BaseModel, ConfigDict


class TaskType(enum.StrEnum):
    """Classification of task types for work items.

    Attributes:
        PLAN: Task is a planning/architecture request.
        IMPLEMENT: Task is an implementation request.
    """

    PLAN = "plan"
    IMPLEMENT = "implement"


class WorkItemStatus(enum.StrEnum):
    """Status states for work items in the orchestration workflow.

    These status values map directly to GitHub labels with the 'agent:' prefix.

    Attributes:
        QUEUED: Work item is awaiting processing.
        IN_PROGRESS: Work item is currently being processed.
        SUCCESS: Work item completed successfully.
        ERROR: Work item failed with an implementation error.
        INFRA_FAILURE: Work item failed during infrastructure setup.
        STALLED_BUDGET: Work item exceeded the daily budget.
    """

    QUEUED = "agent:queued"
    IN_PROGRESS = "agent:in-progress"
    SUCCESS = "agent:success"
    ERROR = "agent:error"
    INFRA_FAILURE = "agent:infra-failure"
    STALLED_BUDGET = "agent:stalled-budget"


class WorkItem(BaseModel):
    """Represents a work item in the orchestration queue.

    A WorkItem captures all necessary context for an agent to process a task,
    including its source, target repository, classification, and current status.

    Attributes:
        id: Unique identifier for the work item (string or integer).
        source_url: GitHub issue URL or source reference.
        context_body: Raw markdown body containing task context.
        target_repo_slug: Target repository in owner/repo format.
        task_type: Classification as PLAN or IMPLEMENT.
        status: Current state in the workflow.
        metadata: Provider-specific data (e.g., issue_node_id).

    Example:
        >>> item = WorkItem(
        ...     id="issue-123",
        ...     source_url="https://github.com/owner/repo/issues/123",
        ...     context_body="## Task\\nImplement feature X",
        ...     target_repo_slug="owner/repo",
        ...     task_type=TaskType.IMPLEMENT,
        ...     status=WorkItemStatus.QUEUED,
        ...     metadata={"issue_node_id": "I_123"},
        ... )
    """

    id: str | int
    source_url: str
    context_body: str
    target_repo_slug: str
    task_type: TaskType
    status: WorkItemStatus
    metadata: dict[str, Any]

    model_config = ConfigDict(extra="forbid")


# Secret patterns for credential sanitization
# Each pattern is designed to match a specific type of secret/token
# Using callable replacements where we need to preserve the separator
_SECRET_PATTERNS: list[tuple[re.Pattern[str], str | Callable[[re.Match[str]], str]]] = [
    # GitHub Personal Access Token (classic)
    (re.compile(r"ghp_[A-Za-z0-9_]+"), "[REDACTED]"),
    # GitHub Server-to-Server Token
    (re.compile(r"ghs_[A-Za-z0-9_]+"), "[REDACTED]"),
    # GitHub OAuth Token
    (re.compile(r"gho_[A-Za-z0-9_]+"), "[REDACTED]"),
    # GitHub Fine-grained Personal Access Token
    (re.compile(r"github_pat_[A-Za-z0-9_]+"), "[REDACTED]"),
    # Bearer tokens (with flexible spacing)
    (re.compile(r"Bearer\s+[A-Za-z0-9_-]+"), "Bearer [REDACTED]"),
    # OpenAI API keys (including sk-proj- format)
    (re.compile(r"sk-[A-Za-z0-9_-]+"), "[REDACTED]"),
    # ZhipuAI keys (approximate pattern - alphanumeric with possible dashes/underscores)
    (re.compile(r"(?:zhipu[_-]?|zm[_-]?)[A-Za-z0-9_-]{20,}"), "[REDACTED]"),
]


def _redact_token_match(match: re.Match[str]) -> str:
    """Replacement function that preserves the separator (=: or :=) in token patterns.

    Args:
        match: A regex match object for token patterns.

    Returns:
        The redacted string with the original separator preserved.
    """
    full_match = match.group(0)
    # Find which separator was used
    if ":" in full_match:
        return "token: [REDACTED]"
    return "token= [REDACTED]"


# Pattern for generic token assignments (token=, token:) - uses callable replacement
_TOKEN_PATTERN = re.compile(r"token[=:]\s*[A-Za-z0-9_-]+")


def scrub_secrets(text: str) -> str:
    """Sanitize text by replacing credential patterns with [REDACTED].

    This function scans the input text for common secret patterns including
    GitHub tokens, API keys, and bearer tokens, replacing them with a
    redaction marker to prevent accidental exposure in logs or outputs.

    Args:
        text: The input string potentially containing secrets.

    Returns:
        The sanitized string with all detected secrets replaced by [REDACTED].

    Example:
        >>> scrub_secrets("Token: ghp_FAKE_TOKEN")
        'Token: [REDACTED]'
        >>> scrub_secrets("Authorization: Bearer secret_token_123")
        'Authorization: Bearer [REDACTED]'
        >>> scrub_secrets("No secrets here!")
        'No secrets here!'

    Note:
        - The function preserves non-secret content unchanged.
        - Empty strings are returned as-is.
        - The ZhipuAI pattern is approximate and may match other similarly
          formatted keys.
    """
    if not text:
        return text

    result = text
    for pattern, replacement in _SECRET_PATTERNS:
        result = pattern.sub(replacement, result)

    # Handle token patterns with separator preservation
    result = _TOKEN_PATTERN.sub(_redact_token_match, result)

    return result

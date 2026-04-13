"""GitHub webhook event models using Pydantic.

This module provides type-safe models for parsing and validating
GitHub webhook payloads received by the notifier service.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class GitHubLabel(BaseModel):
    """Represents a GitHub label on an issue or PR."""

    id: int
    node_id: str
    url: str
    name: str
    color: str
    default: bool
    description: str | None = None


class GitHubUser(BaseModel):
    """Represents a GitHub user account."""

    login: str
    id: int
    node_id: str
    avatar_url: str
    html_url: str
    type: str


class GitHubRepository(BaseModel):
    """Represents a GitHub repository."""

    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: GitHubUser
    html_url: str
    description: str | None = None


class GitHubIssue(BaseModel):
    """Represents a GitHub issue."""

    id: int
    node_id: str
    number: int
    title: str
    body: str | None = None
    html_url: str
    state: str
    labels: list[GitHubLabel] = []
    user: GitHubUser
    assignees: list[GitHubUser] = []
    repository: GitHubRepository | None = None

    model_config = ConfigDict(extra="allow")


class GitHubIssuesEvent(BaseModel):
    """Represents a GitHub 'issues' webhook event payload."""

    action: str
    issue: GitHubIssue
    repository: GitHubRepository
    sender: GitHubUser

    model_config = ConfigDict(extra="allow")


class GitHubIssueComment(BaseModel):
    """Represents a GitHub issue comment."""

    id: int
    node_id: str
    body: str | None = None
    html_url: str
    user: GitHubUser

    model_config = ConfigDict(extra="allow")


class GitHubIssueCommentEvent(BaseModel):
    """Represents a GitHub 'issue_comment' webhook event payload."""

    action: str
    issue: GitHubIssue
    comment: GitHubIssueComment
    repository: GitHubRepository
    sender: GitHubUser

    model_config = ConfigDict(extra="allow")


class GitHubPullRequest(BaseModel):
    """Represents a GitHub pull request."""

    id: int
    node_id: str
    number: int
    title: str
    body: str | None = None
    html_url: str
    state: str
    draft: bool = False
    user: GitHubUser
    assignees: list[GitHubUser] = []
    head: dict[str, Any]
    base: dict[str, Any]

    model_config = ConfigDict(extra="allow")


class GitHubPullRequestEvent(BaseModel):
    """Represents a GitHub 'pull_request' webhook event payload."""

    action: str
    number: int
    pull_request: GitHubPullRequest
    repository: GitHubRepository
    sender: GitHubUser

    model_config = ConfigDict(extra="allow")


class WebhookHeaders(BaseModel):
    """Extracted headers from a GitHub webhook request."""

    event_type: str
    delivery_id: str
    signature: str | None = None

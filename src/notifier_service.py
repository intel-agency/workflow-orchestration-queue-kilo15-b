"""
OS-APOW Work Event Notifier

A FastAPI-based webhook receiver that maps provider events (GitHub, etc.)
to a unified Work Item queue. This is the "Ear" of the system that
listens for external events and queues them for processing.

Environment Variables:
    WEBHOOK_SECRET: GitHub App webhook secret for HMAC signature validation
    GITHUB_TOKEN: GitHub API token with repo scope

Endpoints:
    POST /webhooks/github - Receives GitHub webhook events
    GET /health - Health check endpoint
"""

import hashlib
import hmac
import os
import sys
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request

from src.models.github_events import GitHubIssuesEvent
from src.models.work_item import TaskType, WorkItem, WorkItemStatus
from src.queue.github_queue import GitHubQueue, ITaskQueue

# --- Environment validation at import time ---

_WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
_GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

_PLACEHOLDER_VALUES = {"your_webhook_secret_here", "YOUR_GITHUB_TOKEN", ""}

if _WEBHOOK_SECRET in _PLACEHOLDER_VALUES:
    print(
        "FATAL: WEBHOOK_SECRET is missing or still set to a placeholder value. "
        "Set it to the GitHub App webhook secret.",
        file=sys.stderr,
    )
    sys.exit(1)

if _GITHUB_TOKEN in _PLACEHOLDER_VALUES:
    print(
        "FATAL: GITHUB_TOKEN is missing or still set to a placeholder value.",
        file=sys.stderr,
    )
    sys.exit(1)

WEBHOOK_SECRET = _WEBHOOK_SECRET.encode()

# --- FastAPI Application ---

app = FastAPI(
    title="OS-APOW Event Notifier",
    description="Webhook receiver for the OS-APOW orchestration system",
    version="0.1.0",
)


def get_queue() -> ITaskQueue:
    """Dependency injection for the queue implementation.

    Phase 1: GitHub. Can be swapped for Linear, Jira, etc.
    """
    return GitHubQueue(token=_GITHUB_TOKEN)


async def verify_signature(
    request: Request,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
) -> None:
    """Validate the GitHub webhook HMAC signature.

    Args:
        request: The incoming FastAPI request.
        x_hub_signature_256: The X-Hub-Signature-256 header value.

    Raises:
        HTTPException: If signature is missing or invalid.
    """
    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="X-Hub-Signature-256 missing")

    body = await request.body()
    signature = "sha256=" + hmac.new(WEBHOOK_SECRET, body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")


# --- Endpoints ---


@app.post("/webhooks/github", dependencies=[Depends(verify_signature)])
async def handle_github_webhook(
    request: Request, queue: Annotated[ITaskQueue, Depends(get_queue)]
) -> dict:
    """Handle incoming GitHub webhook events.

    This endpoint receives all GitHub webhook events and triages them
    based on event type and action. Currently handles:
    - issues.opened: Creates work items for plan/implementation tasks

    Args:
        request: The incoming FastAPI request.
        queue: The task queue dependency.

    Returns:
        A status dict indicating whether the event was accepted or ignored.
    """
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "issues" and payload.get("action") == "opened":
        try:
            event = GitHubIssuesEvent(**payload)
        except Exception:
            # Log but don't fail on unknown event structures
            return {"status": "ignored", "reason": "Could not parse event payload"}

        issue = event.issue
        labels = [label.name for label in issue.labels]

        # Determine task type from title or labels
        if "[Application Plan]" in issue.title or "agent:plan" in labels:
            task_type = TaskType.PLAN
        else:
            task_type = TaskType.IMPLEMENT

        work_item = WorkItem(
            id=str(issue.id),
            issue_number=issue.number,
            source_url=issue.html_url,
            target_repo_slug=event.repository.full_name,
            task_type=task_type,
            context_body=issue.body or "",
            status=WorkItemStatus.QUEUED,
            node_id=issue.node_id,
        )
        await queue.add_to_queue(work_item)
        return {"status": "accepted", "item_id": work_item.id}

    return {"status": "ignored", "reason": "No actionable OS-APOW event mapping found"}


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint for monitoring and load balancers."""
    return {"status": "online", "system": "OS-APOW Notifier"}


if __name__ == "__main__":
    import uvicorn

    # In dev, run with: uv run uvicorn src.notifier_service:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)

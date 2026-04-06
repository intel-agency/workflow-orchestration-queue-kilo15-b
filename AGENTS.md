# AGENTS.md

> Project instructions for AI coding agents working on the workflow-orchestration-queue (OS-APOW) project.

---

## Purpose

OS-APOW (Open Source - Agentic Project Orchestration Workflow) is a **headless agentic orchestration platform** that transforms GitHub Issues into "Execution Orders" autonomously fulfilled by specialized AI agents.

The system implements a **four-pillar architecture**:
1. **The Ear** - FastAPI webhook receiver for GitHub events
2. **The State** - GitHub Issues as persistence layer ("Markdown as a Database")
3. **The Brain** - Sentinel orchestrator with async polling and distributed locking
4. **The Hands** - Isolated DevContainer execution environment

---

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Language** | Python | 3.12+ |
| **Framework** | FastAPI | 0.115+ |
| **Data Validation** | Pydantic | 2.10+ |
| **HTTP Client** | HTTPX | 0.28+ |
| **Package Manager** | uv | Latest |
| **Testing** | pytest + pytest-asyncio | 8.3+ |
| **Linter** | Ruff | 0.9+ |
| **Type Checker** | MyPy | 1.14+ |
| **ASGI Server** | Uvicorn | 0.34+ |

---

## Project Structure

```
workflow-orchestration-queue-kilo15-b/
├── src/
│   ├── __init__.py
│   ├── orchestrator_sentinel.py    # Sentinel polling service (The Brain)
│   ├── notifier_service.py         # FastAPI webhook receiver (The Ear)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── work_item.py            # Unified data model + secret scrubbing
│   │   └── github_events.py        # GitHub webhook event Pydantic models
│   └── queue/
│       ├── __init__.py
│       └── github_queue.py         # GitHub Issues queue implementation (The State)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── test_work_item.py           # WorkItem model + scrub_secrets tests
│   └── test_github_queue.py        # Queue implementation tests
├── docs/
│   ├── README.md
│   └── architecture.md             # Detailed architecture overview
├── scripts/                        # Utility scripts (PowerShell + Bash)
├── .env.example                    # Environment variable template
├── pyproject.toml                  # Project configuration (dependencies, tooling)
├── uv.lock                         # Dependency lock file
└── README.md                       # Project overview
```

---

## Setup Instructions

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/intel-agency/workflow-orchestration-queue-kilo15-b.git
cd workflow-orchestration-queue-kilo15-b

# Install dependencies (including dev tools)
uv sync --extra dev

# Copy environment template and configure
cp .env.example .env
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub PAT with repo scope | Yes |
| `GITHUB_ORG` | GitHub organization name | Yes (Sentinel) |
| `GITHUB_REPO` | Target repository name | Yes (Sentinel) |
| `SENTINEL_BOT_LOGIN` | Bot account login for distributed locking | No |
| `WEBHOOK_SECRET` | HMAC secret for webhook validation | Yes (Notifier) |
| `SENTINEL_HEARTBEAT_INTERVAL` | Heartbeat interval in seconds | No (default: 300) |

---

## Development Commands

### Install Dependencies

```bash
# Install main + dev dependencies
uv sync --extra dev

# Install only main dependencies (production)
uv sync
```

### Run Services

```bash
# Run the notifier service (development mode with auto-reload)
uv run uvicorn src.notifier_service:app --reload

# Run the sentinel orchestrator
uv run python -m src.orchestrator_sentinel
```

### Testing

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_work_item.py -v

# Run tests excluding slow tests
uv run pytest -m "not slow"
```

### Linting and Formatting

```bash
# Check for linting errors
uv run ruff check .

# Auto-fix linting errors
uv run ruff check . --fix

# Check formatting (dry run)
uv run ruff format . --check

# Format code
uv run ruff format .
```

### Type Checking

```bash
# Run MyPy type checker
uv run mypy src/
```

---

## Code Style and Conventions

### General Rules

- **Python 3.12+** syntax is acceptable (union types with `|`, type hints)
- **Line length**: 100 characters (enforced by Ruff)
- **Imports**: Sorted via Ruff/isort
- **Quotes**: Double quotes for strings (Ruff formatter default)
- **Indentation**: 4 spaces

### Pydantic Models

- Use `ConfigDict(extra="forbid")` to reject unknown fields
- All fields should have type annotations
- Use `StrEnum` for enumeration types

```python
from pydantic import BaseModel, ConfigDict

class MyModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    id: str
    name: str
    metadata: dict[str, Any] = {}
```

### Async Patterns

- Use `asyncio` for async operations
- Use `httpx.AsyncClient` for HTTP requests (connection pooling)
- Properly close resources with `async with` or explicit `close()`

```python
async def fetch_data() -> None:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
```

### Error Handling

- Use structured logging via the `logging` module
- Propagate rate-limit errors (403/429) for backoff handling
- Sanitize all output with `scrub_secrets()` before posting to GitHub

---

## Architecture Overview

### Four-Pillar Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        External World                            │
│                    (GitHub Webhooks, API)                        │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  THE EAR: Work Event Notifier (FastAPI)                         │
│  • POST /webhooks/github  ←── HMAC-validated webhook receiver   │
│  • GET /health            ←── Health check endpoint             │
│  • Event Triage: issues.opened → WorkItem → Queue               │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  THE STATE: Work Queue (GitHub Issues)                          │
│  • Issues = Work Items                                          │
│  • Labels = Status (agent:queued, agent:in-progress, etc.)      │
│  • Comments = Execution logs & heartbeats                       │
│  • Assignees = Distributed lock                                 │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  THE BRAIN: Sentinel Orchestrator                               │
│  • Polling Loop (60s interval, jittered backoff)                │
│  • Claim task (assign-then-verify locking)                      │
│  • Spawn worker → Post heartbeats → Update status               │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  THE HANDS: Opencode Worker (DevContainer)                      │
│  • Fresh container per task                                     │
│  • Resource limits (2 CPU, 4GB RAM)                             │
│  • Hard timeout (95 min ceiling)                                │
│  • Specialized AI agents via opencode CLI                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. WorkItem Model (`src/models/work_item.py`)

The unified data model shared across all components:

```python
class WorkItem(BaseModel):
    id: str | int              # Unique identifier
    issue_number: int          # GitHub issue number
    source_url: str            # GitHub issue URL
    context_body: str          # Task description
    target_repo_slug: str      # owner/repo format
    task_type: TaskType        # PLAN | IMPLEMENT
    status: WorkItemStatus     # Current state
    node_id: str | None        # GraphQL node ID
    metadata: dict[str, Any]   # Extensible field
```

### 2. Status Labels

| Label | Meaning |
|-------|---------|
| `agent:queued` | Ready for processing |
| `agent:in-progress` | Being processed |
| `agent:success` | Completed successfully |
| `agent:error` | Failed with error |
| `agent:infra-failure` | Infrastructure failure |
| `agent:stalled-budget` | Budget exceeded |

### 3. Secret Scrubbing (`scrub_secrets()`)

All outputs are sanitized before posting to GitHub:

```python
# Patterns redacted:
ghp_*          # GitHub PAT (classic)
ghs_*          # GitHub Server token
gho_*          # GitHub OAuth token
github_pat_*   # Fine-grained PAT
sk-*           # OpenAI keys
Bearer *       # Bearer tokens
token=*        # Generic token assignments
```

### 4. GitHubQueue (`src/queue/github_queue.py`)

Implements `ITaskQueue` interface for future provider swapping:
- `add_to_queue()` - Add `agent:queued` label
- `fetch_queued_tasks()` - Query issues by label
- `update_status()` - Update labels + post comments
- `claim_task()` - Assign-then-verify distributed locking
- `post_heartbeat()` - Progress updates during execution

---

## Testing Strategy

### Test Organization

- **Unit Tests**: `tests/test_*.py` files
- **Fixtures**: `tests/conftest.py` provides shared fixtures
- **Markers**: `@pytest.mark.slow`, `@pytest.mark.integration`

### Key Fixtures

```python
@pytest.fixture
def sample_work_item() -> WorkItem:
    """Sample work item for testing."""
    
@pytest.fixture
def sample_plan_item() -> WorkItem:
    """Sample planning work item."""
    
@pytest.fixture
def mock_queue() -> ITaskQueue:
    """Mock task queue with AsyncMock."""
```

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src --cov-report=html

# Specific file
uv run pytest tests/test_github_queue.py -v

# Exclude slow tests
uv run pytest -m "not slow"
```

---

## PR and Commit Guidelines

### Commit Messages

Format:
```
<type>: <subject>

<body>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code restructuring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

Example:
```
feat: add webhook signature validation

- Implement HMAC SHA256 verification
- Add environment variable for secret
- Include unit tests for edge cases
```

### Pull Request Guidelines

1. **Branch naming**: `feature/<description>` or `fix/<description>`
2. **Tests required**: All PRs must pass the test suite
3. **Type hints**: New code must include type annotations
4. **Documentation**: Update docs for behavior changes
5. **Secret safety**: Never commit tokens or secrets

### Pre-Merge Checklist

- [ ] `uv run pytest` passes
- [ ] `uv run ruff check .` is clean
- [ ] `uv run ruff format . --check` passes
- [ ] `uv run mypy src/` is clean (or documented exceptions)
- [ ] New code has type annotations
- [ ] Complex logic has docstrings

---

## Common Tasks

### Add a New Model

1. Create in `src/models/<name>.py`
2. Inherit from `BaseModel` with `extra="forbid"`
3. Add type hints for all fields
4. Export from `src/models/__init__.py`
5. Add tests in `tests/test_<name>.py`

### Add a New Queue Provider

1. Create class implementing `ITaskQueue`
2. Implement all abstract methods
3. Add to dependency injection in `notifier_service.py`
4. Add comprehensive tests

### Add a New Webhook Handler

1. Create Pydantic model for event in `src/models/`
2. Add endpoint in `notifier_service.py`
3. Map event to `WorkItem` if actionable
4. Add HMAC validation via `Depends(verify_signature)`
5. Test with sample payloads

---

## Troubleshooting

### Common Issues

**Tests fail with import errors:**
```bash
# Ensure dev dependencies are installed
uv sync --extra dev
```

**Type checker reports errors:**
```bash
# Check specific file with verbose output
uv run mypy src/models/work_item.py --show-error-codes
```

**Linter errors on formatting:**
```bash
# Auto-fix what can be fixed
uv run ruff check . --fix
uv run ruff format .
```

**Environment variables not loaded:**
```bash
# Ensure .env file exists and is configured
cp .env.example .env
# Edit .env with your values
```

---

## Related Documentation

- [Architecture Overview](docs/architecture.md) - Detailed system design
- [README.md](README.md) - Project overview and quick start
- [pyproject.toml](pyproject.toml) - Full tool configuration

---

## Quick Reference

```bash
# Setup
uv sync --extra dev && cp .env.example .env

# Test
uv run pytest

# Lint
uv run ruff check . && uv run ruff format . --check

# Type check
uv run mypy src/

# Run notifier
uv run uvicorn src.notifier_service:app --reload

# Run sentinel
uv run python -m src.orchestrator_sentinel
```

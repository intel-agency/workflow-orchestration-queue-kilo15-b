# OS-APOW: Workflow Orchestration Queue

A headless agentic orchestration platform that transforms GitHub Issues into "Execution Orders" autonomously fulfilled by specialized AI agents.

## Overview

OS-APOW (Open Source - Agentic Project Orchestration Workflow) is a system that orchestrates AI agents to handle development tasks through a GitHub-backed work queue. It implements a **four-pillar architecture**:

1. **The Ear (Work Event Notifier)** - FastAPI webhook receiver with HMAC signature validation
2. **The State (Work Queue)** - GitHub Issues as persistence layer ("Markdown as a Database")
3. **The Brain (Sentinel Orchestrator)** - Async polling service with distributed locking
4. **The Hands (Opencode Worker)** - Isolated DevContainer execution environment

## Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- GitHub account with appropriate permissions

## Installation

```bash
# Clone the repository
git clone https://github.com/intel-agency/workflow-orchestration-queue-kilo15-b.git
cd workflow-orchestration-queue-kilo15-b

# Install dependencies
uv sync --dev
```

## Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

### Sentinel Service

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub personal access token with repo scope | Yes |
| `GITHUB_ORG` | GitHub organization name | Yes |
| `GITHUB_REPO` | Target repository name | Yes |
| `SENTINEL_BOT_LOGIN` | Bot account GitHub login for distributed locking | No |
| `SENTINEL_HEARTBEAT_INTERVAL` | Heartbeat interval in seconds (default: 300) | No |

### Notifier Service

| Variable | Description | Required |
|----------|-------------|----------|
| `WEBHOOK_SECRET` | HMAC secret for webhook validation | Yes |
| `GITHUB_TOKEN` | GitHub API token with repo scope | Yes |

## Running

```bash
# Run the notifier service (development mode with auto-reload)
uv run uvicorn src.notifier_service:app --reload

# Run the sentinel orchestrator
uv run python -m src.orchestrator_sentinel
```

## Development

### Linting and Formatting

```bash
# Check for linting errors
uv run ruff check src tests

# Format code
uv run ruff format src tests

# Type checking
uv run mypy src
```

### Testing

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_work_item.py -v
```

## Project Structure

```
workflow-orchestration-queue-kilo15-b/
├── src/
│   ├── __init__.py
│   ├── orchestrator_sentinel.py    # Sentinel polling service
│   ├── notifier_service.py         # FastAPI webhook receiver
│   ├── models/
│   │   ├── __init__.py
│   │   ├── work_item.py            # Unified data model
│   │   └── github_events.py        # GitHub webhook event models
│   └── queue/
│       ├── __init__.py
│       └── github_queue.py         # GitHub Issues queue implementation
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── test_work_item.py           # WorkItem model tests
│   └── test_github_queue.py        # Queue implementation tests
├── docs/
│   ├── README.md
│   └── architecture.md             # Architecture overview
├── scripts/                        # Utility scripts
├── pyproject.toml                  # Project configuration
├── uv.lock                         # Dependency lock file
├── .env.example                    # Environment variable template
└── README.md                       # This file
```

## Architecture

### Unified Data Model

All components share a single `WorkItem` model:

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
    metadata: dict             # Extensible field
```

### Status Labels

| Label | Meaning |
|-------|---------|
| `agent:queued` | Ready for processing |
| `agent:in-progress` | Being processed |
| `agent:success` | Completed successfully |
| `agent:error` | Failed with error |
| `agent:infra-failure` | Infrastructure failure |
| `agent:stalled-budget` | Budget exceeded |

### Security

All outputs are sanitized using `scrub_secrets()` which removes:
- GitHub tokens (`ghp_`, `ghs_`, `gho_`, `github_pat_`)
- Bearer tokens
- OpenAI API keys (`sk-`)
- Generic token assignments

## CI/CD

The project uses GitHub Actions for continuous integration:

- **Lint**: Ruff linter and formatter checks
- **Test**: Pytest with coverage reporting
- **Typecheck**: MyPy type checking
- **Build**: Package build verification

## Documentation

- [Architecture Overview](docs/architecture.md) - Detailed system design
- [Application Plan](https://github.com/intel-agency/workflow-orchestration-queue-kilo15-b/issues/13) - Implementation plan

## License

MIT License - see [LICENSE](LICENSE) for details.

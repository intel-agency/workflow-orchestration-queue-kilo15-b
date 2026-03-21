# OS-APOW: Workflow Orchestration Queue

Headless agentic orchestration platform for GitHub-based work queue management.

## Overview

OS-APOW (Open Source - Agentic Project Orchestration Workflow) is a system that orchestrates AI agents to handle development tasks through a GitHub-backed work queue. It consists of two main services:

- **Sentinel**: Polls GitHub for queued tasks and dispatches agents to process them
- **Notifier**: Receives webhook events and routes them to the work queue

## Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

```bash
# Clone the repository
git clone https://github.com/intel-agency/workflow-orchestration-queue.git
cd workflow-orchestration-queue

# Install dependencies
uv sync
```

## Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub personal access token with repo/issue permissions | Yes |
| `GITHUB_REPO` | Target repository in `owner/repo` format | Yes |
| `SENTINEL_BOT_LOGIN` | Bot account GitHub login | Yes |
| `WEBHOOK_SECRET` | HMAC secret for webhook validation | No |
| `SENTINEL_HEARTBEAT_INTERVAL` | Heartbeat interval in seconds (default: 300) | No |

## Running

```bash
# Run the sentinel service
uv run sentinel

# Run the notifier service
uv run notifier
```

## Development

### Linting

```bash
# Check for linting errors
uv run ruff check .

# Format code
uv run ruff format .
```

### Testing

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src
```

## Project Structure

```
workflow-orchestration-queue/
├── src/
│   └── workflow_orchestration_queue/
│       ├── __init__.py    # Package init with version
│       ├── config.py      # Pydantic Settings configuration
│       ├── sentinel.py    # Sentinel service entry point
│       └── notifier.py    # Notifier service entry point
├── tests/                 # Test suite
├── pyproject.toml         # Project configuration and dependencies
├── .env.example           # Environment variable template
└── README.md              # This file
```

## License

See [LICENSE](LICENSE) for details.

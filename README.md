# Workflow Orchestration Queue (OS-APOW)

A headless agentic orchestration platform for GitHub workflow automation.

## Overview

OS-APOW (Orchestration Service - Automated Processing of Work) is a Python-based system for orchestrating AI agents to handle GitHub issues, pull requests, and workflow automation tasks.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

## Quick Start

### Install Dependencies

```bash
# Sync all dependencies (including dev dependencies)
uv sync --extra dev

# Or just production dependencies
uv sync
```

### Run Tests

```bash
uv run pytest
```

### Linting

```bash
uv run ruff check .
uv run ruff format .
```

## Project Structure

```
workflow-orchestration-queue/
├── pyproject.toml     # Project configuration and dependencies
├── uv.lock           # Lock file for deterministic builds
├── .python-version   # Python version pin (3.12)
├── src/
│   └── workflow_orchestration_queue/  # Main package
│       └── __init__.py
└── tests/
    └── test_imports.py  # Dependency verification tests
```

## Dependencies

### Core Dependencies

- **FastAPI** - Modern async web framework for building APIs
- **Uvicorn** - ASGI server for running FastAPI applications
- **Pydantic** - Data validation and settings management
- **httpx** - Modern async HTTP client for GitHub API interactions

### Development Dependencies

- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **ruff** - Fast Python linter and formatter

## License

MIT

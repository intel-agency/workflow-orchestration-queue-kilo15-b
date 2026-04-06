# Architecture Overview

## System Design

OS-APOW implements a **four-pillar architecture** designed for reliability, observability, and autonomous operation.

```
┌─────────────────────────────────────────────────────────────────┐
│                        External World                            │
│                    (GitHub Webhooks, API)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  THE EAR: Work Event Notifier (FastAPI)                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  /webhooks/github  ←── HMAC-validated webhook receiver  │   │
│  │  /health           ←── Health check endpoint            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Event Triage:                                           │   │
│  │  • issues.opened → WorkItem → Queue                     │   │
│  │  • Filter by labels/titles                              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  THE STATE: Work Queue (GitHub Issues)                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  "Markdown as a Database"                               │   │
│  │  • Issues = Work Items                                  │   │
│  │  • Labels = Status (agent:queued, agent:in-progress)    │   │
│  │  • Comments = Execution logs & heartbeats               │   │
│  │  • Assignees = Distributed lock                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  THE BRAIN: Sentinel Orchestrator                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Polling Loop (60s interval, jittered backoff):         │   │
│  │  1. Fetch issues labeled 'agent:queued'                 │   │
│  │  2. Claim task (assign-then-verify locking)             │   │
│  │  3. Spawn worker                                        │   │
│  │  4. Post heartbeats (5 min interval)                    │   │
│  │  5. Update final status                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  THE HANDS: Opencode Worker (DevContainer)                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Isolated Execution Environment:                         │   │
│  │  • Fresh container per task                             │   │
│  │  • Resource limits (2 CPU, 4GB RAM)                     │   │
│  │  • Hard timeout (95 min ceiling)                        │   │
│  │  • Specialized AI agents via opencode CLI               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Work Event Notifier (FastAPI)

**File:** `src/notifier_service.py`

The notifier receives webhook events from GitHub and triages them into the work queue.

**Endpoints:**
- `POST /webhooks/github` - Receives GitHub webhook events
- `GET /health` - Health check endpoint

**Security:**
- HMAC SHA256 signature validation
- Environment variable validation at startup

**Event Mapping:**
| GitHub Event | Action | Result |
|--------------|--------|--------|
| `issues` | `opened` | Creates `WorkItem` with `PLAN` or `IMPLEMENT` type |

### 2. Work Queue (GitHub Issues)

**File:** `src/queue/github_queue.py`

The queue uses GitHub Issues as a persistent state store.

**Status Labels:**
| Label | Meaning |
|-------|---------|
| `agent:queued` | Ready for processing |
| `agent:in-progress` | Being processed |
| `agent:success` | Completed successfully |
| `agent:error` | Failed with error |
| `agent:infra-failure` | Infrastructure failure |
| `agent:stalled-budget` | Budget exceeded |

**Distributed Locking:**
Uses assign-then-verify pattern:
1. Assign bot account to issue
2. Re-fetch issue to verify assignment
3. Only then update labels

### 3. Sentinel Orchestrator

**File:** `src/orchestrator_sentinel.py`

The sentinel is the "brain" that coordinates task execution.

**Configuration:**
| Variable | Default | Description |
|----------|---------|-------------|
| `POLL_INTERVAL` | 60s | Time between polling cycles |
| `MAX_BACKOFF` | 960s | Maximum backoff on rate limits |
| `HEARTBEAT_INTERVAL` | 300s | Time between heartbeat comments |
| `SUBPROCESS_TIMEOUT` | 5700s | Hard ceiling for task execution |

**Resilience:**
- Jittered exponential backoff on rate limits (403/429)
- Graceful shutdown on SIGTERM/SIGINT
- Heartbeat comments during long-running tasks

### 4. Unified Data Model

**File:** `src/models/work_item.py`

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

## Security Measures

### 1. Credential Scrubbing

All outputs are sanitized before posting to GitHub:

```python
# Patterns redacted:
ghp_*      # GitHub PAT (classic)
ghs_*      # GitHub Server token
gho_*      # GitHub OAuth token
github_pat_* # Fine-grained PAT
sk-*       # OpenAI keys
Bearer *   # Bearer tokens
token=*    # Generic token assignments
token:*    # Generic token assignments
```

### 2. HMAC Signature Validation

The notifier validates all webhook signatures:

```python
def verify_signature(request: Request, x_hub_signature_256: str):
    signature = "sha256=" + hmac.new(WEBHOOK_SECRET, body, sha256).hexdigest()
    assert hmac.compare_digest(signature, x_hub_signature_256)
```

### 3. Input Validation

Pydantic models enforce strict validation:
- No extra fields allowed (`extra="forbid"`)
- Required fields enforced
- Type validation

## Observability

### Structured Logging

Both services emit structured logs:

```
2026-04-06 10:30:00 [INFO] sentinel-abc123 - Processing Task #42
2026-04-06 10:35:00 [INFO] sentinel-abc123 - Heartbeat posted
2026-04-06 10:40:00 [INFO] sentinel-abc123 - Task #42 completed successfully
```

### GitHub Comments

All progress is documented in issue comments:
- Task claims
- Heartbeats (5 min intervals)
- Completion status
- Error messages

## Deployment

### Development

```bash
# Run notifier locally
uv run uvicorn src.notifier_service:app --reload

# Run sentinel locally
uv run python -m src.orchestrator_sentinel
```

### Production

Both services are designed for containerized deployment:

1. **Notifier**: Deploy as a container with:
   - Port 8000 exposed
   - `WEBHOOK_SECRET` and `GITHUB_TOKEN` environment variables
   - Ingress with TLS termination

2. **Sentinel**: Deploy as a long-running container with:
   - `GITHUB_TOKEN`, `GITHUB_ORG`, `GITHUB_REPO` environment variables
   - Optional `SENTINEL_BOT_LOGIN` for distributed locking

## Future Phases

- **Phase 2**: Enhanced webhook automation, event triage
- **Phase 3**: Hierarchical decomposition, self-healing

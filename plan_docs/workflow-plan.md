# Workflow Execution Plan: project-setup

**Repository:** workflow-orchestration-queue-kilo15-b
**Generated:** 2026-04-06
**Status:** Ready for Approval

---

## 1. Overview

**Workflow Name:** `project-setup`
**Project:** workflow-orchestration-queue (OS-APOW)
**Total Assignments:** 6 main + 2 post-assignment events + 1 post-script event
**Estimated Duration:** 23-31 hours

### Summary
This workflow orchestrates the complete initialization of a new headless agentic orchestration platform. The system transforms standard GitHub Issues into "Execution Orders" that are autonomously fulfilled by specialized AI agents, The workflow establishes repository structure, creates comprehensive planning documents, sets up AI agent context files, and prepares the platform for self-bootstrapping evolution.

---

## 2. Project Context Summary

### Technology Stack
- **Language:** Python 3.12+
- **Framework:** FastAPI (async web framework)
- **Data Validation:** Pydantic
- **HTTP Client:** HTTPX (async with connection pooling)
- **Package Manager:** uv (Rust-based, fast dependency resolver)
- **Containerization:** Docker, DevContainers
- **API Integration:** GitHub REST API v3
- **Orchestration:** opencode CLI, GitHub Actions
- **MCP Servers:** Sequential Thinking, Memory

### Architecture Overview
**Four-Pillar Architecture:**
1. **The Ear (Work Event Notifier)** - FastAPI webhook receiver with HMAC signature validation
2. **The State (Work Queue)** - GitHub Issues as persistence layer ("Markdown as a Database")
3. **The Brain (Sentinel Orchestrator)** - Async polling service with distributed locking
4. **The Hands (Opencode Worker)** - Isolated DevContainer execution environment

### Repository Details
- **Repository:** `intel-agency/workflow-orchestration-queue`
- **Branch Strategy:** main (stable), develop (integration)
- **Project Management:** GitHub Projects with Kanban columns

### Phased Rollout
- **Phase 0:** Seeding & Bootstrapping (manual initialization)
- **Phase 1:** The Sentinel MVP (polling, task claiming, shell-bridge execution)
- **Phase 2:** The Ear (webhook automation, event triage)
- **Phase 3:** Deep Orchestration (hierarchical decomposition, self-healing)

### Key Constraints
1. **GitHub Actions SHA Pinning:** All workflow actions MUST use specific commit SHA (not version tags like @v3 or @main)
2. **Missing Label:** The `orchestration:plan-approved` label does NOT exist and must be created during initialization or applied manually afterward
3. **Authentication Scopes Required:** `repo`, `project`, `read:project`, `read:user`, `user:email`, `administration: write`
4. **Environment Isolation:** Worker containers run in segregated Docker network with strict resource constraints (2 CPUs, 4GB RAM)

### Critical Implementation Details
- **Unified Data Model:** Single `WorkItem` model in `src/models/work_item.py` shared by all components
- **Consolidated Queue:** `GitHubQueue` class in `src/queue/github_queue.py` with connection pooling
- **Credential Scrubbing:** Regex-based secret sanitization before posting to GitHub
- **Distributed Locking:** Assign-then-verify pattern using GitHub issue assignments
- **Resiliency:** Polling-first approach with jittered exponential backoff on rate limits

---

## 3. Assignment Execution Plan

### Assignment 1: init-existing-repository
**Goal:** Initialize the existing repository by creating branch, importing ruleset, creating GitHub Project, importing labels, and creating initial PR.

**Duration:** 6-8 hours
**Complexity:** Medium

**Key Acceptance Criteria:**
- ✅ New branch created (`dynamic-workflow-project-setup`)
- ✅ Branch protection ruleset imported from `.github/protected-branches_ruleset.json`
- ✅ GitHub Project created and linked to repository
- ✅ Project columns created: Not Started, In Progress, In Review, Done
- ✅ Labels imported from `.github/.labels.json`
- ✅ Workspace and devcontainer files renamed to match repository name
- ✅ PR created from branch to main (after at least one commit)

**Project-Specific Notes:**
- **CRITICAL:** The `orchestration:plan-approved` label does NOT exist in `.github/.labels.json` and must be created during this assignment or applied manually later
- The branch protection ruleset requires `administration: write` scope - must use `GH_ORCHESTRATION_AGENT_TOKEN` (not `GITHUB_TOKEN`)
- All subsequent work commits to the `dynamic-workflow-project-setup` branch
- Branch naming: Must use `dynamic-workflow-project-setup` prefix

**Prerequisites:**
- GitHub CLI (`gh`) installed and authenticated
- `GH_ORCHESTRATION_AGENT_TOKEN` environment variable set with `administration: write` scope
- Write access to the repository

**Dependencies:** None (first assignment)

**Risks/Challenges:**
- ⚠️ **HIGH:** Missing `orchestration:plan-approved` label will cause post-script event to fail
- ⚠️ **MEDIUM:** Branch protection ruleset import may fail due to insufficient permissions
- ⚠️ **LOW:** PR creation may fail if no commits are pushed

**Events:**
- `post-assignment-complete` → triggers `validate-assignment-completion` and `report-progress`

**Mitigation Strategies:**
- Create `orchestration:plan-approved` label manually if not in `.github/.labels.json`
- Verify `GH_ORCHESTRATION_AGENT_TOKEN` has correct scopes before starting
- Ensure at least one commit is made before creating PR

---

### Assignment 2: create-app-plan
**Goal:** Create comprehensive application plan based on plan_docs, documented as a GitHub Issue using the application-plan template
**Duration:** 4-6 hours
**Complexity:** High

**Key Acceptance Criteria:**
- ✅ Application template thoroughly analyzed
- ✅ Plan's project structure documented according to guidelines
- ✅ Application plan template used from `.github/ISSUE_TEMPLATE/application-plan.md`
- ✅ Detailed breakdown of all phases with important steps
- ✅ All required components and dependencies planned
- ✅ Technology stack follows specified design principles
- ✅ All mandatory requirements addressed (testing, documentation, containerization)
- ✅ All acceptance criteria from template addressed
- ✅ Risks and mitigations identified
- ✅ Application plan documented in GitHub Issue
- ✅ Milestones created and issues linked appropriately
- ✅ Issue added to GitHub Project
- ✅ Issue assigned to appropriate milestone ("Phase 1: Foundation")
- ✅ Appropriate labels applied (`planning`, `documentation`)

**Project-Specific Notes:**
- **IMPORTANT:** This is PLANNING ONLY - no code implementation
- Plan must focus on the 4-pillar architecture (Ear, State, Brain, Hands)
- Must address all phases from the Development Plan (Phase 0: Seeding through Phase 3: Deep Orchestration)
- Document unified data model in `src/models/work_item.py`
- Document consolidated queue implementation in `src/queue/github_queue.py`
- Include credential scrubbing implementation details
- Address distributed locking with assign-then-verify pattern
- Include resiliency through polling-first approach with exponential backoff

**Prerequisites:**
- `init-existing-repository` completed successfully
- `plan_docs/` directory contains:
  - `OS-APOW Development Plan v4.2.md`
  - `OS-APOW Architecture Guide v3.2.md`
  - `OS-APOW Implementation Specification v1.2.md`
  - `OS-APOW Plan Review.md`
  - `OS-APOW Simplification Report v1.md`
  - `src/` directory with reference Python code

**Dependencies:**
- Branch created from `init-existing-repository`
- Labels imported from `init-existing-repository`
- GitHub Project created from `init-existing-repository`

**Risks/Challenges:**
- ⚠️ **HIGH:** Complex analysis required across 5 planning documents
- ⚠️ **MEDIUM:** Stakeholder review may require multiple iterations
- ⚠️ **LOW:** Issue template format may need adjustment

**Events:**
- `pre-assignment-begin` → gather-context
- `on-assignment-failure` → recover-from-error
- `post-assignment-complete` → validate-assignment-completion, report-progress

**Mitigation Strategies:**
- Use sequential thinking to organize complex analysis
- Present draft plan early for stakeholder feedback
- Reference existing application-plan examples for format guidance

---

### Assignment 3: create-project-structure
**Goal:** Create actual project structure and scaffolding based on the approved application plan
**Duration:** 4-8 hours
**Complexity:** High

**Key Acceptance Criteria:**
- ✅ Solution/project structure created following application plan's tech stack
- ✅ All required project files and directories established
- ✅ Initial configuration files created (version pinning, Docker, etc.)
- ✅ Basic CI/CD pipeline structure established
- ✅ Documentation structure created (README, docs folder, etc.)
- ✅ Development environment properly configured and validated
- ✅ Initial commit made with complete project scaffolding
- ✅ Stakeholder approval obtained
- ✅ Repository summary document created (`.ai-repository-summary.md`)
- ✅ All GitHub Actions workflows have actions pinned to specific commit SHA

**Project-Specific Notes:**
- **Tech Stack:** Python 3.12+ with FastAPI, Pydantic, HTTPX, uv
- **Structure:**
  ```
  /
    pyproject.toml
    uv.lock
    src/
      orchestrator_sentinel.py
      notifier_service.py
      models/
        work_item.py
        github_events.py
      queue/
        github_queue.py
    scripts/
      devcontainer-opencode.sh
      gh-auth.ps1
      update-remote-indices.ps1
    local_ai_instruction_modules/
      create-app-plan.md
      perform-task.md
      analyze-bug.md
    docs/
    tests/
    .devcontainer/
      devcontainer.json
      Dockerfile
    docker-compose.yml
  ```
- **CRITICAL:** All GitHub Actions workflows must use actions pinned to specific commit SHA (not version tags)
- **CRITICAL:** When using `uv pip install -e .`, ensure `COPY src/ ./src/` appears BEFORE the install command
- **CRITICAL:** Do NOT use `curl` in Docker healthcheck commands - use Python stdlib instead

- Docker healthcheck example: `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"`

**Prerequisites:**
- `create-app-plan` completed and approved
- Application plan issue created and approved
- Tech stack documented in plan

**Dependencies:**
- Application plan from `create-app-plan`
- Tech stack decisions from `create-app-plan`
- Repository initialized from `init-existing-repository`

**Risks/Challenges:**
- ⚠️ **HIGH:** Docker configuration complexity (healthchecks, networking, volumes)
- ⚠️ **HIGH:** CI/CD workflow SHA pinning requires research and precision
- ⚠️ **MEDIUM:** Environment configuration may require iteration
- ⚠️ **LOW:** Documentation may need updates as structure evolves

**Events:**
- `post-assignment-complete` → validate-assignment-completion, report-progress

**Mitigation Strategies:**
- Test Docker configurations locally before committing
- Use GitHub Actions documentation to find correct SHAs
- Validate environment setup incrementally

---

### Assignment 4: create-agents-md-file
**Goal:** Create comprehensive `AGENTS.md` file at repository root to provide AI coding agents with project context and instructions
**Duration:** 2-2 hours
**Complexity:** Low

**Key Acceptance Criteria:**
- ✅ `AGENTS.md` file exists at repository root
- ✅ File contains project overview section describing purpose and tech stack
- ✅ File contains setup/build/test commands that have been verified to work
- ✅ File contains code style and conventions section
- ✅ File contains project structure/directory layout section
- ✅ File contains testing instructions
- ✅ File contains PR/commit guidelines
- ✅ File is written in standard Markdown with clear, agent-focused language
- ✅ Commands listed in the file have been validated by running them
- ✅ File is committed and pushed to the working branch
- ✅ Stakeholder approval obtained

**Project-Specific Notes:**
- File should complement README.md (not duplicate it)
- Should cross-reference `.ai-repository-summary.md` if it exists
- Must include Python-specific build/test commands:
  - Install: `uv sync`
  - Build: `uv run build` or equivalent
  - Test: `uv run pytest` or equivalent
  - Lint: `uv run ruff check .` or equivalent
- Should document the 4-pillar architecture
- Should include Docker/devcontainer setup instructions
- Should note the credential scrubbing and security practices
- Should document the polling-first resiliency approach

**Prerequisites:**
- `create-project-structure` completed successfully
- Project structure created and validated
- Build/test tooling in place

**Dependencies:**
- Project structure from `create-project-structure`
- Repository summary from `create-project-structure`
- README.md from `create-project-structure`

**Risks/Challenges:**
- ⚠️ **LOW:** Commands may need adjustment as project evolves
- ⚠️ **LOW:** May need updates when new tools are added

**Events:**
- `post-assignment-complete` → validate-assignment-completion, report-progress

**Mitigation Strategies:**
- Validate all commands by actually running them
- Keep file concise and focused
- Reference other docs rather than duplicating content

---

### Assignment 5: debrief-and-document
**Goal:** Perform comprehensive debriefing to capture key learnings, insights, and areas for improvement; document findings in structured format
**Duration:** 2-3 hours
**Complexity:** Medium

**Key Acceptance Criteria:**
- ✅ Detailed report created following structured template
- ✅ Report documented in `.md` file format
- ✅ All required sections complete and comprehensive
- ✅ All deviations from assignment documented
- ✅ Report reviewed and approved by stakeholders
- ✅ Report committed and pushed to project repo
- ✅ Execution trace saved in repository (`debrief-and-document/trace.md`)

**Project-Specific Notes:**
- **CRITICAL:** Must flag any plan-impacting findings as ACTION ITEMS
- For each ACTION ITEM, recommend: (a) file new issue, or (b) update later phase/epic descriptions
- Must review upcoming steps in current and next phase for continued validity
- Should document all challenges with Docker, CI/CD, and GitHub API integration
- Should capture lessons about Python async patterns, uv package management
- Should note any simplification opportunities identified
- Should document any deviations from the plan documents

**Prerequisites:**
- All previous assignments completed
- All work items from previous assignments available

**Dependencies:**
- All outputs from previous 4 assignments
- Workflow execution history
- Validation reports from post-assignment events

**Risks/Challenges:**
- ⚠️ **MEDIUM:** May be difficult to capture all nuances and learnings comprehensively
- ⚠️ **LOW:** Stakeholder review may require iteration

**Events:**
- `post-assignment-complete` → validate-assignment-completion, report-progress

**Mitigation Strategies:**
- Use structured template to ensure completeness
- Review workflow execution history systematically
- Focus on actionable insights and recommendations

---

### Assignment 6: pr-approval-and-merge
**Goal:** Complete the full PR approval and merge process including resolving all PR comments, obtaining approval, merging PR, and closing associated issues
**Duration:** 2-4 hours
**Complexity:** Medium

**Key Acceptance Criteria:**
**CI Verification:**
- ✅ All required CI/CD status checks pass before code review
- ✅ CI remediation loop executed (up to 3 attempts) if any check fails
- ✅ If CI cannot be fixed within 3 attempts, escalation documented

**Code Review Delegation:**
- ✅ Code review delegated to `code-reviewer` subagent or designated reviewer (NOT self-review)
- ✅ Auto-reviewer comments waited for before beginning comment resolution

**Review Comment Resolution:**
- ✅ `ai-pr-comment-protocol.md` workflow executed and logged
- ✅ `pr-review-comments` acceptance criteria satisfied
- ✅ GraphQL verification artifacts captured
- ✅ Evidence files and summary links attached to run report

**Approval & Merge:**
- ✅ Stakeholder approval obtained after presenting resolution evidence
- ✅ Merge performed using repository policies
- ✅ Merge result recorded (`merged`, `pending`, or `failed`)
- ✅ Source branch deleted (if merge succeeded and policy allows)
- ✅ Related issues closed or updated
- ✅ Run report updated with final status

**Project-Specific Notes:**
- **CRITICAL:** Must follow `ai-pr-comment-protocol.md` exactly - log acknowledgment
- Must delegate code review to `code-reviewer` subagent - no self-review
- Must wait for auto-reviewers (Copilot, CodeQL, etc.) before resolving comments
- Must use GraphQL `resolveReviewThread` mutation for thread resolution
- Must create evidence files: `pr-unresolved-threads.json` (should be empty), final GraphQL output
- Must post PR-wide summary comment enumerating all threads and resolutions
- PR number will be available from `init-existing-repository` output

**Prerequisites:**
- All previous assignments completed
- PR created and ready for review
- All work committed and pushed to PR branch

**Dependencies:**
- PR number from `init-existing-repository`
- All implementation work from previous assignments
- Validation reports confirming all acceptance criteria met

**Risks/Challenges:**
- ⚠️ **HIGH:** Review comments may require significant rework
- ⚠️ **MEDIUM:** CI failures may require multiple fix attempts
- ⚠️ **LOW:** Merge conflicts if target branch has changed

**Events:**
- `post-assignment-complete` → validate-assignment-completion, report-progress

**Mitigation Strategies:**
- Address review comments systematically one at a time
- Use CI remediation loop with max 3 attempts
- Test changes locally before pushing
- Communicate proactively with stakeholders about complex issues

---

### Post-Assignment Event 1: validate-assignment-completion
**Trigger:** After each main assignment completes
**Duration:** 0.5-1 hour per validation
**Complexity:** Low (Automated)

**Key Acceptance Criteria:**
- ✅ All required files from assignment exist
- ✅ All verification commands pass (build, test, lint, etc.)
- ✅ Validation report created documenting results
- ✅ Pass/fail status determined
- ✅ If failed, specific remediation steps provided
- ✅ **CRITICAL:** If ANY acceptance criterion is not met, assignment is marked as FAILED

**Project-Specific Notes:**
- Must be delegated to independent QA agent (`qa-test-engineer`)
- For GitHub operations (issue/PR/project changes), must query live repository state
- Must verify against assignment's specific acceptance criteria
- Should create validation report in `docs/validation/` directory

**Prerequisites:**
- An assignment has just completed
- Assignment acceptance criteria documented
- Assignment outputs available

**Dependencies:**
- Completed assignment's outputs
- Assignment definition file

**Risks/Challenges:**
- ⚠️ **LOW:** Automated process with predictable outcomes

---

### Post-Assignment Event 2: report-progress
**Trigger:** After each main assignment and validation completes
**Duration:** 0.5-1 hour
**Complexity:** Low (Automated)

**Key Acceptance Criteria:**
- ✅ Structured progress report generated with step name, duration, and status
- ✅ All step outputs captured and recorded
- ✅ Expected outputs validated (exist and meet format requirements)
- ✅ Workflow state saved for resume-from-checkpoint
- ✅ **CRITICAL:** All action items (deviations, findings, future work) filed as GitHub issues
- ✅ Action item issue numbers and URLs recorded in progress report

**Project-Specific Notes:**
- Must include "Deviations & Findings" section
- Must include "Plan-Impacting Discoveries" section
- Must assess whether next 1-2 upcoming epics still make sense given learnings
- All identified items MUST be filed as GitHub issues (non-negotiable)
- Issues should have `priority:low` and `needs-triage` labels

**Prerequisites:**
- Workflow orchestrator actively executing dynamic workflow
- Current workflow step completed successfully
- Access to step execution context

**Dependencies:**
- Completed step's outputs
- Validation results from `validate-assignment-completion`

**Risks/Challenges:**
- ⚠️ **LOW:** Automated reporting process

---

### Post-Script Event: Apply orchestration:plan-approved Label
**Trigger:** After all workflow assignments complete
**Duration:** 5-10 minutes
**Complexity:** Very Low

**Key Acceptance Criteria:**
- ✅ `orchestration:plan-approved` label applied to the application plan issue
- ✅ Label application verified via GitHub API query

**Project-Specific Notes:**
- **CRITICAL:** The `orchestration:plan-approved` label does NOT exist yet
- Must be created during `init-existing-repository` OR applied manually if label doesn't exist
- Label should be applied to the issue created in `create-app-plan` assignment
- This triggers the orchestrator to begin autonomous execution of the approved plan

**Prerequisites:**
- All workflow assignments completed successfully
- Application plan issue exists (created in `create-app-plan`)

**Dependencies:**
- Application plan issue from `create-app-plan`
- Label created/imported from `init-existing-repository`

**Risks/Challenges:**
- ⚠️ **HIGH:** Label may not exist, causing event to fail
- ⚠️ **LOW:** GitHub API rate limiting (unlikely for single label operation)

**Mitigation Strategies:**
- Verify label exists before applying; create if missing
- Apply manually if automatic application fails

---

## 4. Sequencing Diagram

```
┌─────────────────────────────┐
│  Workflow Start               │
└─────────────────────────────┘
            │
            v
┌─────────────────────────────────────────────────────┐
│  1. init-existing-repository              │
│     • Create branch (FIRST)                   │
│     • Import branch protection ruleset         │
│     • Create GitHub Project                    │
│     • Import labels                             │
│     • Create PR (after commits)               │
│     • Create orchestration:plan-approved label │
└─────────────────────────────────────────────────────┘
            │
            │ [post: validate-assignment-completion]
            │ [post: report-progress]
            V
┌─────────────────────────────────────────────────────┐
│  2. create-app-plan                          │
│     • Analyze plan_docs/                       │
│     • Create application plan issue            │
│     • Create milestones                          │
│     • Link issue to project/milestone          │
└─────────────────────────────────────────────────────┘
            │
            │ [post: validate-assignment-completion]
            │ [post: report-progress]
            V
┌─────────────────────────────────────────────────────┐
│  3. create-project-structure               │
│     • Create solution structure              │
│     • Create Docker configs                  │
│     • Create CI/CD workflows (SHA-pinned)    │
│     • Create documentation structure         │
│     • Create .ai-repository-summary.md       │
└─────────────────────────────────────────────────────┘
            │
            │ [post: validate-assignment-completion]
            │ [post: report-progress]
            V
┌─────────────────────────────────────────────────────┐
│  4. create-agents-md-file                   │
│     • Create AGENTS.md at repository root    │
│     • Document setup/build/test commands     │
│     • Validate all commands                  │
└─────────────────────────────────────────────────────┘
            │
            │ [post: validate-assignment-completion]
            │ [post: report-progress]
            V
┌─────────────────────────────────────────────────────┐
│  5. debrief-and-document                     │
│     • Create debrief report                  │
│     • Document learnings and findings         │
│     • File action items as GitHub issues      │
│     • Save execution trace                   │
└─────────────────────────────────────────────────────┘
            │
            │ [post: validate-assignment-completion]
            │ [post: report-progress]
            V
┌─────────────────────────────────────────────────────┐
│  6. pr-approval-and-merge                     │
│     • Verify CI checks pass                   │
│     • Delegate code review                   │
│     • Resolve all review comments            │
│     • Obtain stakeholder approval            │
│     • Merge PR                                │
│     • Close related issues                  │
└─────────────────────────────────────────────────────┘
            │
            │ [post: validate-assignment-completion]
            │ [post: report-progress]
            V
┌─────────────────────────────────────────────────────┐
│  Post-Script: Apply orchestration:plan-approved  │
│     • Apply label to application plan issue       │
│     • Trigger autonomous execution               │
└─────────────────────────────────────────────────────┘
```

---

## 5. Risk Assessment
### Risk Matrix
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Missing `orchestration:plan-approved` label | HIGH | HIGH | Create label during init or apply manually; verify existence before post-script event |
| GitHub API rate limiting | MEDIUM | MEDIUM | Use exponential backoff; batch operations; cache results locally |
| Authentication scope issues | MEDIUM | HIGH | Verify scopes early; use `test-github-permissions.ps1` script |
| Docker configuration complexity | MEDIUM | MEDIUM | Test locally; use Python stdlib for healthchecks; validate incrementally |
| CI/CD SHA pinning errors | LOW | HIGH | Research correct SHAs; validate workflows; use commit SHA not tags |
| Long-running subagent delegations | HIGH | MEDIUM | Use heartbeat comments; set appropriate timeouts; monitor progress |
| Environment drift between tasks | MEDIUM | MEDIUM | Stop containers between tasks; use fresh environments; validate isolation |
| PR merge conflicts | LOW | MEDIUM | Keep branch up-to-date; communicate with team; resolve conflicts promptly |
| Stakeholder review iterations | MEDIUM | LOW | Present drafts early; gather feedback incrementally; set clear expectations |

### Critical Dependencies
1. **Branch Creation → All Other Work:** Everything depends on the branch being created first
2. **Label Import → Label Application:** Labels must be imported before they can be applied
3. **Application Plan Approval → Project Structure:** Structure cannot be created without approved plan
4. **Project Structure → AGENTS.md:** AGENTS.md requires knowledge of actual structure
5. **All Assignments → PR Merge:** PR cannot be merged until all work is complete

---

## 6. Open Questions
The following items require clarification before workflow execution begins:

### Critical (Must Resolve Before Starting)
1. **orchestration:plan-approved Label Creation:**
   - ❓ Should this label be added to `.github/.labels.json` before starting, or created during the workflow?
   - ❓ If created during workflow, should it be in `init-existing-repository` or separate manual step?
   - **Recommendation:** Add to `.github/.labels.json` now to avoid post-script event failure

2. **Authentication Token Scopes:**
   - ❓ Confirm `GH_ORCHESTRATION_AGENT_TOKEN` has `administration: write` scope for branch protection ruleset import
   - ❓ Should we run `scripts/test-github-permissions.ps1` before starting?
   - **Recommendation:** Run permissions test as first step

### Important (Should Clarify Early)
3. **GitHub Project Creation Details:**
   - ❓ Should the project use classic Projects or Projects V2?
   - ❓ What should the project description be?
   - **Recommendation:** Use Projects V2 (Beta) for better integration

4. **Environment Variable Setup:**
   - ❓ Are all required environment variables documented and available?
   - ❓ Should we create a `.env.example` file?
   - Required vars: `GITHUB_TOKEN`, `GITHUB_ORG`, `GITHUB_REPO`, `SENTINEL_BOT_LOGIN`, `GH_ORCHESTRATION_AGENT_TOKEN`
   - **Recommendation:** Document required vars in AGENTS.md

5. **Branch Naming Convention:**
   - ❓ Confirm branch name should be `dynamic-workflow-project-setup`
   - ❓ Should we include a timestamp or unique identifier?
   - **Recommendation:** Use `dynamic-workflow-project-setup` as specified

### Nice to Have (Can Clarify During Execution)
6. **CI/CD Workflow Specifics:**
   - ❓ Should we create GitHub Actions workflows now or document them for later?
   - ❓ What CI/CD checks should run on the PR?
   - **Recommendation:** Create basic CI workflow now (build, test, lint) per assignment requirements

7. **Testing Strategy for Python Async Services:**
   - ❓ What testing framework should we use? (pytest, unittest, etc.)
   - ❓ What's the minimum test coverage target?
   - **Recommendation:** Use pytest with pytest-asyncio; target 80% coverage

8. **Documentation Structure Preferences:**
   - ❓ Should docs be in `docs/` or alongside code?
   - ❓ Should we use Sphinx, MkDocs, or another documentation generator?
   - **Recommendation:** Use `docs/` directory with Markdown; add Sphinx later if needed

9. **Long-Running Operation Monitoring:**
   - ❓ How should we monitor long-running sentinel operations during development?
   - ❓ Should we create a status dashboard?
   - **Recommendation:** Use GitHub issue comments for status; create dashboard in Phase 2

10. **PR Review and Merge Strategy:**
    - ❓ Should we use squash merge, rebase, or standard merge?
    - ❓ Who should approve the PR?
    - **Recommendation:** Use squash merge; require orchestrator approval

---

## 7. Resolution Trace
### Files Read
- `/workspaces/workflow-orchestration-queue-kilo15-b/plan_docs/OS-APOW Development Plan v4.2.md`
- `/workspaces/workflow-orchestration-queue-kilo15-b/plan_docs/OS-APOW Architecture Guide v3.2.md`
- `/workspaces/workflow-orchestration-queue-kilo15-b/plan_docs/OS-APOW Implementation Specification v1.2.md`
- `/workspaces/workflow-orchestration-queue-kilo15-b/plan_docs/OS-APOW Plan Review.md`
- `/workspaces/workflow-orchestration-queue-kilo15-b/plan_docs/OS-APOW Simplification Report v1.md`
- `/workspaces/workflow-orchestration-queue-kilo15-b/plan_docs/src/models/work_item.py`
- `/workspaces/workflow-orchestration-queue-kilo15-b/plan_docs/src/queue/github_queue.py`
- `/workspaces/workflow-orchestration-queue-kilo15-b/plan_docs/src/models/__init__.py`
- `/workspaces/workflow-orchestration-queue-kilo15-b/plan_docs/src/queue/__init__.py`
- `/workspaces/workflow-orchestration-queue-kilo15-b/.github/.labels.json`
- `/workspaces/workflow-orchestration-queue-kilo15-b/.github/protected-branches_ruleset.json` (not found - file does not exist)

### Remote Assignment Definitions Fetched
- `https://raw.githubusercontent.com/nam20485/agent-instructions/main/ai_instruction_modules/ai-workflow-assignments/create-workflow-plan.md`
- `https://raw.githubusercontent.com/nam20485/agent-instructions/main/ai_instruction_modules/ai-workflow-assignments/init-existing-repository.md`
- `https://raw.githubusercontent.com/nam20485/agent-instructions/main/ai_instruction_modules/ai-workflow-assignments/create-app-plan.md`
- `https://raw.githubusercontent.com/nam20485/agent-instructions/main/ai_instruction_modules/ai-workflow-assignments/create-project-structure.md`
- `https://raw.githubusercontent.com/nam20485/agent-instructions/main/ai_instruction_modules/ai-workflow-assignments/create-agents-md-file.md`
- `https://raw.githubusercontent.com/nam20485/agent-instructions/main/ai_instruction_modules/ai-workflow-assignments/debrief-and-document.md`
- `https://raw.githubusercontent.com/nam20485/agent-instructions/main/ai_instruction_modules/ai-workflow-assignments/pr-approval-and-merge.md`
- `https://raw.githubusercontent.com/nam20485/agent-instructions/main/ai_instruction_modules/ai-workflow-assignments/validate-assignment-completion.md`
- `https://raw.githubusercontent.com/nam20485/agent-instructions/main/ai_instruction_modules/ai-workflow-assignments/report-progress.md`

---

## 8. Next Steps
Once this plan is approved:

1. **Immediate Actions:**
   - Add `orchestration:plan-approved` label to `.github/.labels.json`
   - Run `scripts/test-github-permissions.ps1` to verify authentication
   - Confirm all environment variables are set

2. **Begin Workflow Execution:**
   - Start with `init-existing-repository` assignment
   - Follow the sequencing diagram in order
   - Complete validation and progress reporting after each assignment

3. **Monitor and Adjust:**
   - Watch for risks identified in risk assessment
   - File issues for any deviations or findings
   - Update plan if significant changes are needed

4. **Final Deliverables:**
   - Merged PR with all project setup complete
   - Application plan issue with `orchestration:plan-approved` label
   - Complete documentation (AGENTS.md, README.md, .ai-repository-summary.md)
   - Debrief report with learnings and recommendations

---

**Plan Prepared By:** Planner Agent
**Date:** 2026-04-06
**Status:** Ready for Stakeholder Approval
**Estimated Total Duration:** 23-31 hours

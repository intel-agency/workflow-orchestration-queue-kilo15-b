"""
OS-APOW Sentinel Orchestrator

The "Brain" of the OS-APOW system that:
1. Polls a GitHub repo for issues labeled 'agent:queued'.
2. Claims the task using assign-then-verify distributed locking.
3. Manages the worker lifecycle via './scripts/devcontainer-opencode.sh'.
4. Posts heartbeat comments during long-running tasks.
5. Reports progress and results back to GitHub.

Environment Variables:
    GITHUB_TOKEN: GitHub API token with repo scope
    GITHUB_ORG: GitHub organization name
    GITHUB_REPO: GitHub repository name
    SENTINEL_BOT_LOGIN: Optional bot account login for assign-then-verify locking
"""

import asyncio
import logging
import os
import random
import signal
import subprocess
import sys
import uuid

import httpx

from src.models.work_item import TaskType, WorkItem, WorkItemStatus
from src.queue.github_queue import GitHubQueue

# --- Configuration ---
# Required env vars: GITHUB_TOKEN, GITHUB_ORG, GITHUB_REPO
# Optional: SENTINEL_BOT_LOGIN (enables assign-then-verify locking)

POLL_INTERVAL = 60  # seconds between polling cycles
MAX_BACKOFF = 960  # 16 minutes max backoff on rate limits
SENTINEL_ID = f"sentinel-{uuid.uuid4().hex[:8]}"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_ORG = os.getenv("GITHUB_ORG")
GITHUB_REPO = os.getenv("GITHUB_REPO")
SHELL_BRIDGE_PATH = "./scripts/devcontainer-opencode.sh"
HEARTBEAT_INTERVAL = 300  # 5 min between heartbeat comments

# Subprocess hard timeout: safety net in case inner watchdog fails
# Higher than run_opencode_prompt.sh HARD_CEILING_SECS (5400) to avoid racing.
SUBPROCESS_TIMEOUT = 5700  # 95 min

# Sentinel bot account name — used for assign-then-verify locking
# Must match the GitHub account the GITHUB_TOKEN authenticates as.
SENTINEL_BOT_LOGIN = os.getenv("SENTINEL_BOT_LOGIN", "")

# Setup Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s [%(levelname)s] {SENTINEL_ID} - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("OS-APOW-Sentinel")

# Graceful shutdown flag
_shutdown_requested = False


# --- Signal Handling ---


def _handle_signal(signum: int, frame) -> None:
    """Set shutdown flag on SIGTERM/SIGINT so the current task can finish."""
    global _shutdown_requested
    sig_name = signal.Signals(signum).name
    logger.info(f"Received {sig_name} — will shut down after current task finishes")
    _shutdown_requested = True


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


# --- Shell Bridge Interface ---


async def run_shell_command(
    args: list[str], timeout: int | None = None
) -> subprocess.CompletedProcess:
    """Invokes the local shell bridge (devcontainer-opencode.sh).

    Args:
        args: Command and arguments.
        timeout: Maximum seconds to wait. None = no limit.
    """
    try:
        logger.info(f"Executing Bridge: {' '.join(args)}")
        process = await asyncio.create_subprocess_exec(
            *args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except TimeoutError:
            logger.warning(f"Shell command timed out after {timeout}s — killing")
            process.kill()
            stdout, stderr = await process.communicate()
            return subprocess.CompletedProcess(
                args=args,
                returncode=-1,
                stdout=stdout.decode().strip() if stdout else "",
                stderr=f"TIMEOUT after {timeout}s\n" + (stderr.decode().strip() if stderr else ""),
            )

        return subprocess.CompletedProcess(
            args=args,
            returncode=process.returncode if process.returncode is not None else -1,
            stdout=stdout.decode().strip() if stdout else "",
            stderr=stderr.decode().strip() if stderr else "",
        )
    except Exception as e:
        logger.error(f"Critical shell execution error: {e!s}")
        raise


# --- Orchestration Logic ---


class Sentinel:
    """Sentinel orchestrator that manages the task polling and execution loop."""

    def __init__(self, queue: GitHubQueue):
        self.queue = queue
        self._current_backoff = POLL_INTERVAL

    async def _heartbeat_loop(self, item: WorkItem, start_time: float) -> None:
        """Post periodic heartbeat comments while a task is running."""
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            elapsed = int(asyncio.get_event_loop().time() - start_time)
            await self.queue.post_heartbeat(item, SENTINEL_ID, elapsed)

    async def process_task(self, item: WorkItem) -> None:
        """Process a single work item through the full execution pipeline."""
        logger.info(f"Processing Task #{item.issue_number}...")
        start_time = asyncio.get_event_loop().time()

        # Launch heartbeat as a background task
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(item, start_time))

        try:
            # Step 1: Initialize Infrastructure
            res_up = await run_shell_command([SHELL_BRIDGE_PATH, "up"], timeout=300)
            if res_up.returncode != 0:
                err = f"❌ **Infrastructure Failure** during `up` stage:\n```\n{res_up.stderr}\n```"
                await self.queue.update_status(item, WorkItemStatus.INFRA_FAILURE, err)
                return

            # Step 2: Start Opencode Server
            res_start = await run_shell_command([SHELL_BRIDGE_PATH, "start"], timeout=120)
            if res_start.returncode != 0:
                err = f"❌ **Infrastructure Failure** starting `opencode-server`:\n```\n{res_start.stderr}\n```"
                await self.queue.update_status(item, WorkItemStatus.INFRA_FAILURE, err)
                return

            # Step 3: Trigger Agent Workflow
            workflow_map = {
                TaskType.PLAN: "create-app-plan.md",
                TaskType.IMPLEMENT: "perform-task.md",
            }
            workflow = workflow_map.get(item.task_type, "perform-task.md")
            instruction = f"Execute workflow {workflow} for context: {item.source_url}"

            # Primary bridge call with subprocess timeout safety net
            res_prompt = await run_shell_command(
                [SHELL_BRIDGE_PATH, "prompt", instruction],
                timeout=SUBPROCESS_TIMEOUT,
            )

            # Step 4: Handle Completion
            if res_prompt.returncode == 0:
                success_msg = (
                    f"✅ **Workflow Complete**\n"
                    f"Sentinel successfully executed `{workflow}`. "
                    f"Please review Pull Requests."
                )
                await self.queue.update_status(item, WorkItemStatus.SUCCESS, success_msg)
            else:
                log_tail = (
                    res_prompt.stderr[-1500:] if res_prompt.stderr else "No error output captured."
                )
                fail_msg = f"❌ **Execution Error** during `{workflow}`:\n```\n...{log_tail}\n```"
                await self.queue.update_status(item, WorkItemStatus.ERROR, fail_msg)

        except Exception as e:
            logger.exception(f"Internal Sentinel Error on Task #{item.issue_number}")
            await self.queue.update_status(
                item,
                WorkItemStatus.INFRA_FAILURE,
                f"🚨 Sentinel encountered an unhandled exception: {e!s}",
            )
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

            # Environment reset between tasks — stop container but keep for fast restart
            logger.info("Resetting environment (stop)")
            await run_shell_command([SHELL_BRIDGE_PATH, "stop"], timeout=60)

    async def run_forever(self) -> None:
        """Main polling loop that continuously fetches and processes tasks."""
        logger.info(f"Sentinel {SENTINEL_ID} entering polling loop (interval: {POLL_INTERVAL}s)")

        while not _shutdown_requested:
            try:
                tasks = await self.queue.fetch_queued_tasks()
                if tasks:
                    logger.info(f"Found {len(tasks)} queued task(s).")
                    for task in tasks:
                        if _shutdown_requested:
                            break
                        if await self.queue.claim_task(task, SENTINEL_ID, SENTINEL_BOT_LOGIN):
                            await self.process_task(task)
                            break

                # Reset backoff on successful poll
                self._current_backoff = POLL_INTERVAL

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status in (403, 429):
                    # Jittered exponential backoff
                    jitter = random.uniform(0, self._current_backoff * 0.1)
                    wait = min(self._current_backoff + jitter, MAX_BACKOFF)
                    logger.warning(f"Rate limited ({status}) — backing off {wait:.0f}s")
                    self._current_backoff = min(self._current_backoff * 2, MAX_BACKOFF)
                    await asyncio.sleep(wait)
                    continue
                else:
                    logger.error(f"GitHub API error: {exc}")
            except Exception as e:
                logger.error(f"Polling cycle error: {e!s}")

            await asyncio.sleep(self._current_backoff)

        logger.info("Shutdown flag set — exiting polling loop")


# --- Entry Point ---


async def _main() -> None:
    """Main entry point for the sentinel service."""
    required = ["GITHUB_TOKEN", "GITHUB_ORG", "GITHUB_REPO"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        logger.error(f"Critical Error: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    if not GITHUB_TOKEN or not GITHUB_ORG or not GITHUB_REPO:
        logger.error("Critical Error: Required environment variables are empty")
        sys.exit(1)

    if not SENTINEL_BOT_LOGIN:
        logger.warning(
            "SENTINEL_BOT_LOGIN is not set — assign-then-verify locking is disabled. "
            "Set it to the GitHub login of the bot account for concurrency safety."
        )

    gh_queue = GitHubQueue(GITHUB_TOKEN, GITHUB_ORG, GITHUB_REPO)
    sentinel = Sentinel(gh_queue)

    try:
        await sentinel.run_forever()
    finally:
        await gh_queue.close()
        logger.info("Sentinel shut down.")


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        logger.info("Sentinel shutting down gracefully.")

"""OS-APOW: Workflow Orchestration Queue

A headless agentic orchestration platform that transforms GitHub Issues
into "Execution Orders" autonomously fulfilled by specialized AI agents.

Architecture:
    - The Ear (Work Event Notifier): FastAPI webhook receiver
    - The State (Work Queue): GitHub Issues as persistence layer
    - The Brain (Sentinel Orchestrator): Async polling service
    - The Hands (Opencode Worker): Isolated DevContainer execution
"""

__version__ = "0.1.0"

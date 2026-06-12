from enum import StrEnum


class Events(StrEnum):
    """Standard event types for workflow logging.

    These represent *what happened* (the event), not severity.
    Severity is captured by the log ``level`` field (INFO, WARNING, ERROR).
    """

    # Lifecycle
    WORKFLOW_INIT = "WORKFLOW_INIT"
    WORKFLOW_COMPLETE = "WORKFLOW_COMPLETE"
    INITIALIZED = "INITIALIZED"

    # Phase transitions
    PHASE_TRANSITION = "PHASE_TRANSITION"

    # Planning
    PLAN_DRAFT = "PLAN_DRAFT"
    PLAN_REVISION = "PLAN_REVISION"
    PLAN_APPROVED = "PLAN_APPROVED"
    PLAN_UPDATE = "PLAN_UPDATE"
    NEW_PLAN = "NEW_PLAN"

    # Tasks
    TASK_START = "TASK_START"
    TASK_COMPLETE = "TASK_COMPLETE"
    TASK_FAILED = "TASK_FAILED"
    TASK_VERIFIED = "TASK_VERIFIED"
    TASK_ADDED = "TASK_ADDED"
    TASK_UPDATE = "TASK_UPDATE"

    # Blocking / human intervention
    BLOCKED = "BLOCKED"
    UNBLOCKED = "UNBLOCKED"
    REPLAN = "REPLAN"
    AWAITING_HUMAN = "AWAITING_HUMAN"
    HUMAN_RESOLVED = "HUMAN_RESOLVED"

    # Low-level state changes
    STATE_UPDATE = "STATE_UPDATE"

    # Stages
    STAGE_SKIPPED = "STAGE_SKIPPED"

    # Verification
    VERIFY_SUBMITTED = "VERIFY_SUBMITTED"
    VERIFY_COMPLETE = "VERIFY_COMPLETE"

    # Knowledge
    KNOWLEDGE_RECORDED = "KNOWLEDGE_RECORDED"

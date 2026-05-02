# Pydantic is a library that validates data
# Example: if someone sends age="hello" when we expect a number, pydantic rejects it
from pydantic import BaseModel, Field
from typing import Optional   # Optional means "this field can be empty/None"
from datetime import datetime # datetime = date + time together
from enum import Enum         # Enum = a fixed list of allowed values

# ─── Enum 1: ComponentType ────────────────────────────────────
# Enum = like a dropdown menu, only these values are allowed
# If someone sends component_type="LAPTOP" it will be rejected
class ComponentType(str, Enum):
    # str means each value is a string
    RDBMS    = "RDBMS"     # relational database like PostgreSQL
    CACHE    = "CACHE"     # cache like Redis
    API      = "API"       # an API service
    QUEUE    = "QUEUE"     # message queue like Kafka
    NOSQL    = "NOSQL"     # NoSQL database like MongoDB
    MCP_HOST = "MCP_HOST"  # MCP host service

# ─── Enum 2: Priority ─────────────────────────────────────────
# These are the only allowed priority levels
class Priority(str, Enum):
    P0 = "P0"  # Critical  — fix RIGHT NOW (database down)
    P1 = "P1"  # High      — fix very soon
    P2 = "P2"  # Medium    — fix today
    P3 = "P3"  # Low       — fix when possible

# ─── Enum 3: WorkItemStatus ───────────────────────────────────
# These are the only allowed statuses for a work item
# They must go in order: OPEN → INVESTIGATING → RESOLVED → CLOSED
class WorkItemStatus(str, Enum):
    OPEN          = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED      = "RESOLVED"
    CLOSED        = "CLOSED"

# ─── Model 1: Signal ──────────────────────────────────────────
# This defines what a signal (incoming error) looks like
# BaseModel = pydantic class that auto-validates all fields
class Signal(BaseModel):
    component_id: str
    # example: "RDBMS_PRIMARY_01" — which component had the error

    component_type: ComponentType
    # must be one of the ComponentType values above

    error_code: str
    # example: "DB_CONNECTION_FAILED"

    message: str
    # example: "Connection pool exhausted"

    latency_ms: Optional[float] = None
    # Optional = can be empty
    # float = decimal number like 23.5
    # None = default value if not provided

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    # default_factory=datetime.utcnow means:
    # "if no timestamp given, use current time automatically"

    metadata: Optional[dict] = {}
    # dict = dictionary, any extra info as key-value pairs
    # example: {"region": "us-east", "server": "prod-1"}

# ─── Model 2: RCARequest ──────────────────────────────────────
# This defines what the RCA form submission looks like
# When user fills the form and clicks submit, this is what we receive
class RCARequest(BaseModel):
    incident_start: datetime     # when did the incident start
    incident_end: datetime       # when did it end
    root_cause_category: str     # example: "Hardware Failure"
    fix_applied: str             # what was done to fix it
    prevention_steps: str        # how to prevent it in future

# ─── Model 3: WorkItemResponse ────────────────────────────────
# This defines what we SEND BACK to the frontend
# When frontend asks "give me work items", we send this shape
class WorkItemResponse(BaseModel):
    id: str                        # unique ID of the work item
    component_id: str              # which component failed
    priority: Priority             # P0/P1/P2/P3
    status: WorkItemStatus         # OPEN/INVESTIGATING/RESOLVED/CLOSED
    signal_count: int              # how many signals linked
    start_time: datetime           # when first signal arrived
    end_time: Optional[datetime]   # when it was closed (can be empty)
    mttr_seconds: Optional[int]    # repair time in seconds (can be empty)
    created_at: datetime           # when work item was created
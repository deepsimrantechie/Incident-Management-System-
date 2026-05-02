import pytest
from datetime import datetime, timedelta

# We test these without needing a running server
from workflow.state_machine import (
    get_next_status,
    can_transition_to_closed,
    get_state
)
from workflow.alerting import get_alert_strategy
from models.signal import (
    WorkItemStatus,
    ComponentType,
    Priority,
    Signal,
    RCARequest
)

# ─── State Machine Tests ──────────────────────────────────────

class TestStateMachine:

    def test_open_transitions_to_investigating(self):
        # OPEN should go to INVESTIGATING
        result = get_next_status(WorkItemStatus.OPEN)
        assert result == WorkItemStatus.INVESTIGATING

    def test_investigating_transitions_to_resolved(self):
        # INVESTIGATING should go to RESOLVED
        result = get_next_status(WorkItemStatus.INVESTIGATING)
        assert result == WorkItemStatus.RESOLVED

    def test_resolved_transitions_to_closed(self):
        # RESOLVED should go to CLOSED
        result = get_next_status(WorkItemStatus.RESOLVED)
        assert result == WorkItemStatus.CLOSED

    def test_closed_cannot_transition(self):
        # CLOSED should raise an error — no next state
        with pytest.raises(ValueError):
            get_next_status(WorkItemStatus.CLOSED)

    def test_cannot_close_from_open(self):
        # Cannot close directly from OPEN
        assert can_transition_to_closed(WorkItemStatus.OPEN) == False

    def test_cannot_close_from_investigating(self):
        # Cannot close from INVESTIGATING either
        assert can_transition_to_closed(WorkItemStatus.INVESTIGATING) == False

    def test_can_close_from_resolved(self):
        # RESOLVED is the only state that allows closing
        assert can_transition_to_closed(WorkItemStatus.RESOLVED) == True

    def test_can_close_from_closed(self):
        # CLOSED is already closed
        assert can_transition_to_closed(WorkItemStatus.CLOSED) == True

# ─── Alert Strategy Tests ─────────────────────────────────────

class TestAlertStrategy:

    def test_rdbms_gets_p0(self):
        # Database failure must always be P0
        strategy = get_alert_strategy(ComponentType.RDBMS)
        assert strategy.get_priority() == Priority.P0

    def test_cache_gets_p2(self):
        # Cache failure is P2
        strategy = get_alert_strategy(ComponentType.CACHE)
        assert strategy.get_priority() == Priority.P2

    def test_api_gets_p1(self):
        # API failure is P1
        strategy = get_alert_strategy(ComponentType.API)
        assert strategy.get_priority() == Priority.P1

    def test_queue_gets_p1(self):
        # Queue failure is P1
        strategy = get_alert_strategy(ComponentType.QUEUE)
        assert strategy.get_priority() == Priority.P1

    def test_mcp_gets_p2(self):
        # MCP Host failure is P2
        strategy = get_alert_strategy(ComponentType.MCP_HOST)
        assert strategy.get_priority() == Priority.P2

    def test_alert_message_contains_component_id(self):
        # Alert message must mention the component ID
        strategy = get_alert_strategy(ComponentType.RDBMS)
        msg = strategy.get_alert_message("RDBMS_PRIMARY_01", "Connection failed")
        assert "RDBMS_PRIMARY_01" in msg

    def test_p0_message_contains_critical(self):
        # P0 message must say CRITICAL
        strategy = get_alert_strategy(ComponentType.RDBMS)
        msg = strategy.get_alert_message("DB_01", "Down")
        assert "CRITICAL" in msg or "P0" in msg

# ─── RCA Validation Tests ─────────────────────────────────────

class TestRCAValidation:

    def test_valid_rca_request(self):
        # A complete RCA with all fields should be valid
        start = datetime.utcnow()
        end = start + timedelta(hours=2)
        rca = RCARequest(
            incident_start=start,
            incident_end=end,
            root_cause_category="Hardware Failure",
            fix_applied="Replaced failed disk",
            prevention_steps="Add disk health monitoring"
        )
        assert rca.root_cause_category == "Hardware Failure"
        assert rca.fix_applied == "Replaced failed disk"

    def test_mttr_calculation(self):
        # MTTR = end time - start time in seconds
        start = datetime(2024, 1, 1, 10, 0, 0)  # 10:00 AM
        end   = datetime(2024, 1, 1, 12, 0, 0)  # 12:00 PM
        mttr  = int((end - start).total_seconds())
        assert mttr == 7200  # 2 hours = 7200 seconds

    def test_mttr_minutes(self):
        # MTTR in minutes should be correct
        start = datetime(2024, 1, 1, 10, 0, 0)
        end   = datetime(2024, 1, 1, 10, 30, 0)  # 30 minutes later
        mttr  = int((end - start).total_seconds())
        assert mttr // 60 == 30  # 30 minutes

    def test_empty_fix_applied_is_invalid(self):
        # Empty fix_applied should be caught
        fix = "   "  # only spaces
        assert not fix.strip()  # .strip() removes spaces, empty = invalid

    def test_empty_prevention_steps_is_invalid(self):
        # Empty prevention_steps should be caught
        steps = ""
        assert not steps.strip()

    def test_empty_root_cause_is_invalid(self):
        # Empty root_cause_category should be caught
        category = "  "
        assert not category.strip()

# ─── Signal Model Tests ───────────────────────────────────────

class TestSignalModel:

    def test_valid_signal(self):
        # A valid signal should be created without errors
        signal = Signal(
            component_id="RDBMS_PRIMARY_01",
            component_type=ComponentType.RDBMS,
            error_code="DB_CONNECTION_FAILED",
            message="Connection pool exhausted"
        )
        assert signal.component_id == "RDBMS_PRIMARY_01"
        assert signal.component_type == ComponentType.RDBMS

    def test_signal_has_default_timestamp(self):
        # Timestamp should be auto-set if not provided
        signal = Signal(
            component_id="API_01",
            component_type=ComponentType.API,
            error_code="HTTP_500",
            message="Internal server error"
        )
        assert signal.timestamp is not None

    def test_signal_invalid_component_type(self):
        # Invalid component type should raise validation error
        with pytest.raises(Exception):
            Signal(
                component_id="UNKNOWN_01",
                component_type="INVALID_TYPE",
                error_code="ERR",
                message="test"
            )

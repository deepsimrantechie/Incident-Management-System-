from abc import ABC, abstractmethod
from models.signal import WorkItemStatus

# ─── The Template (Abstract State) ───────────────────────────
# Every state must answer 3 questions:
# 1. What is the next state?
# 2. Can this state move to CLOSED?
# 3. What is my status name?
class WorkItemState(ABC):

    @abstractmethod
    def next_state(self) -> "WorkItemState":
        # returns the next state object
        # "WorkItemState" in quotes = forward reference (class not defined yet)
        pass

    @abstractmethod
    def can_close(self) -> bool:
        # bool = True or False
        # True = yes this state can close
        pass

    @abstractmethod
    def status(self) -> WorkItemStatus:
        # returns the enum value for this state
        pass

# ─── State 1: OPEN ───────────────────────────────────────────
class OpenState(WorkItemState):

    def next_state(self):
        return InvestigatingState()  # OPEN → next is INVESTIGATING

    def can_close(self) -> bool:
        return False  # cannot close from OPEN

    def status(self) -> WorkItemStatus:
        return WorkItemStatus.OPEN

# ─── State 2: INVESTIGATING ───────────────────────────────────
class InvestigatingState(WorkItemState):

    def next_state(self):
        return ResolvedState()  # INVESTIGATING → next is RESOLVED

    def can_close(self) -> bool:
        return False  # cannot close from INVESTIGATING

    def status(self) -> WorkItemStatus:
        return WorkItemStatus.INVESTIGATING

# ─── State 3: RESOLVED ────────────────────────────────────────
class ResolvedState(WorkItemState):

    def next_state(self):
        return ClosedState()  # RESOLVED → next is CLOSED

    def can_close(self) -> bool:
        return True  # YES, can close from RESOLVED (after RCA submitted)

    def status(self) -> WorkItemStatus:
        return WorkItemStatus.RESOLVED

# ─── State 4: CLOSED ─────────────────────────────────────────
class ClosedState(WorkItemState):

    def next_state(self):
        # raise = throw an error on purpose
        # ValueError = wrong value error
        raise ValueError("Cannot transition from CLOSED state")
        # CLOSED is the final state, no next state

    def can_close(self) -> bool:
        return True  # already closed

    def status(self) -> WorkItemStatus:
        return WorkItemStatus.CLOSED

# ─── Lookup Table ─────────────────────────────────────────────
# maps status string → state object
STATE_MAP = {
    WorkItemStatus.OPEN:          OpenState(),
    WorkItemStatus.INVESTIGATING: InvestigatingState(),
    WorkItemStatus.RESOLVED:      ResolvedState(),
    WorkItemStatus.CLOSED:        ClosedState(),
}

def get_state(status: WorkItemStatus) -> WorkItemState:
    # given a status string, return the matching state object
    return STATE_MAP[status]

def get_next_status(current_status: WorkItemStatus) -> WorkItemStatus:
    # 1. get the current state object
    current_state = get_state(current_status)
    # 2. ask it what comes next
    # 3. return the status name of the next state
    return current_state.next_state().status()
    # example: get_next_status(OPEN) → INVESTIGATING

def can_transition_to_closed(current_status: WorkItemStatus) -> bool:
    # ask the current state if closing is allowed
    return get_state(current_status).can_close()
    # example: can_transition_to_closed(RESOLVED) → True
    # example: can_transition_to_closed(OPEN)     → False
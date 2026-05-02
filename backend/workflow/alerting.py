# ABC = Abstract Base Class
# Think of it as a template/contract that other classes must follow
from abc import ABC, abstractmethod
from models.signal import ComponentType, Priority

# ─── The Template (Abstract Strategy) ────────────────────────
# This class says: "anyone who inherits me MUST have these two methods"
# It is like a job description — you must be able to do these things
class AlertStrategy(ABC):

    @abstractmethod  # @abstractmethod means "child class MUST implement this"
    def get_priority(self) -> Priority:
        # -> Priority means this function must return a Priority value
        pass  # pass = no code here, child class will write it

    @abstractmethod
    def get_alert_message(self, component_id: str, error: str) -> str:
        # component_id = which component failed
        # error = what the error message is
        # -> str means must return a string
        pass

# ─── Strategy 1: For Database Failures ───────────────────────
# This class handles RDBMS (PostgreSQL) failures
# It inherits AlertStrategy, so it must implement both methods
class RDBMSAlertStrategy(AlertStrategy):

    def get_priority(self) -> Priority:
        return Priority.P0  # database down = most critical

    def get_alert_message(self, component_id: str, error: str) -> str:
        # f-string = string with variables inside {}
        return f"[P0 CRITICAL] Database failure on {component_id}: {error}. Immediate action required!"

# ─── Strategy 2: For Cache Failures ──────────────────────────
class CacheAlertStrategy(AlertStrategy):

    def get_priority(self) -> Priority:
        return Priority.P2  # cache down = medium priority

    def get_alert_message(self, component_id: str, error: str) -> str:
        return f"[P2 MEDIUM] Cache degradation on {component_id}: {error}. Monitor closely."

# ─── Strategy 3: For API Failures ────────────────────────────
class APIAlertStrategy(AlertStrategy):

    def get_priority(self) -> Priority:
        return Priority.P1  # API down = high priority

    def get_alert_message(self, component_id: str, error: str) -> str:
        return f"[P1 HIGH] API failure on {component_id}: {error}. Investigate immediately."

# ─── Strategy 4: For Queue Failures ──────────────────────────
class QueueAlertStrategy(AlertStrategy):

    def get_priority(self) -> Priority:
        return Priority.P1

    def get_alert_message(self, component_id: str, error: str) -> str:
        return f"[P1 HIGH] Queue failure on {component_id}: {error}. Check consumers."

# ─── Strategy 5: For NoSQL Failures ──────────────────────────
class NoSQLAlertStrategy(AlertStrategy):

    def get_priority(self) -> Priority:
        return Priority.P1

    def get_alert_message(self, component_id: str, error: str) -> str:
        return f"[P1 HIGH] NoSQL failure on {component_id}: {error}. Check cluster health."

# ─── Strategy 6: For MCP Host Failures ───────────────────────
class MCPAlertStrategy(AlertStrategy):

    def get_priority(self) -> Priority:
        return Priority.P2

    def get_alert_message(self, component_id: str, error: str) -> str:
        return f"[P2 MEDIUM] MCP Host failure on {component_id}: {error}."

# ─── The Lookup Table ─────────────────────────────────────────
# Dictionary that maps ComponentType → which strategy to use
# Key = component type, Value = strategy object
STRATEGY_MAP = {
    ComponentType.RDBMS:    RDBMSAlertStrategy(),   # RDBMS → use P0 strategy
    ComponentType.CACHE:    CacheAlertStrategy(),    # CACHE → use P2 strategy
    ComponentType.API:      APIAlertStrategy(),      # API   → use P1 strategy
    ComponentType.QUEUE:    QueueAlertStrategy(),    # QUEUE → use P1 strategy
    ComponentType.NOSQL:    NoSQLAlertStrategy(),    # NOSQL → use P1 strategy
    ComponentType.MCP_HOST: MCPAlertStrategy(),      # MCP   → use P2 strategy
}

def get_alert_strategy(component_type: ComponentType) -> AlertStrategy:
    # .get(key, default) = get value from dict, use default if key not found
    return STRATEGY_MAP.get(component_type, APIAlertStrategy())
    # if component_type not in map, use API strategy as fallback

# ─── HOW IT IS USED ───────────────────────────────────────────
# strategy = get_alert_strategy(ComponentType.RDBMS)
# strategy.get_priority()         → Priority.P0
# strategy.get_alert_message(...) → "[P0 CRITICAL] Database failure..."
#
# strategy = get_alert_strategy(ComponentType.CACHE)
# strategy.get_priority()         → Priority.P2
# Same function call, different result — that is the Strategy Pattern!
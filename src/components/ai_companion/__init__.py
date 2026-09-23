"""AI companion control layer for GTOS live runtime.

The companion layer is intentionally deterministic at the runtime boundary:
external agents may write typed control proposals, but live code only consumes
validated bounded controls that can pause, cool down, or reduce risk.
"""

from .control_state import (
    AI_COMPANION_CONTROL_SCHEMA,
    DEFAULT_CONTROL_STATE_PATH,
    AICompanionRuntimeGate,
    build_empty_control_state,
    load_control_state,
    validate_control_state,
    write_control_state_atomic,
)

__all__ = [
    "AI_COMPANION_CONTROL_SCHEMA",
    "DEFAULT_CONTROL_STATE_PATH",
    "AICompanionRuntimeGate",
    "build_empty_control_state",
    "load_control_state",
    "validate_control_state",
    "write_control_state_atomic",
]

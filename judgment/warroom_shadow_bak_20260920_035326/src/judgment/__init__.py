"""Challenge fluid-gate sidecar (ALIVE_MENU + CONF_GATE + DONE_OUTSIDE).

Shadow-first. Jev never places, remints, or flattens. APPLY is default-off
and, when Chair enables it, writes LABEL drafts only behind prove receipts.
"""

from .alive_menu import AliveMenu, StaleMenuError, rebuild_choice_criteria
from .challenge import CHALLENGE_LOGIN, account_surface, assert_challenge_payout_writer
from .conf_gate import confidence_band, log_conf_gate
from .cycle import run_fluid_gate_cycle
from .done_outside import completion_truth, verify_side_effect
from .flags import apply_enabled, shadow_enabled
from .inventory import collect_live_inventory
from .veto import JevPlacePathVeto, InventedNewsProtocolVeto

__all__ = [
    "CHALLENGE_LOGIN",
    "AliveMenu",
    "InventedNewsProtocolVeto",
    "JevPlacePathVeto",
    "StaleMenuError",
    "account_surface",
    "apply_enabled",
    "assert_challenge_payout_writer",
    "collect_live_inventory",
    "completion_truth",
    "confidence_band",
    "log_conf_gate",
    "rebuild_choice_criteria",
    "run_fluid_gate_cycle",
    "shadow_enabled",
    "verify_side_effect",
]

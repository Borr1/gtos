"""Challenge fluid-gate sidecar (ALIVE_MENU + CONF_GATE + DONE_OUTSIDE + S14 + S15).

Shadow-first. Jev never places, remints, or flattens. APPLY is default-off
and, when Chair enables it, writes LABEL drafts only behind prove receipts.
S15 COST_OF_ERROR logs tape costs + CONF_GATE shadow bands on this same path.
"""

from .alive_menu import AliveMenu, StaleMenuError, rebuild_choice_criteria
from .challenge import CHALLENGE_LOGIN, account_surface, assert_challenge_payout_writer
from .conf_gate import confidence_band, log_conf_gate, log_cost_of_error, pick_cost_of_error
from .cycle import run_fluid_gate_cycle
from .done_outside import completion_truth, verify_side_effect
from .flags import apply_enabled, shadow_enabled
from .inventory import collect_live_inventory
from .regime_gate import evaluate_s14
from .veto import InventedNewsProtocolVeto, JevPlacePathVeto, RawTickDumpVeto

__all__ = [
    "CHALLENGE_LOGIN",
    "AliveMenu",
    "InventedNewsProtocolVeto",
    "JevPlacePathVeto",
    "RawTickDumpVeto",
    "StaleMenuError",
    "account_surface",
    "apply_enabled",
    "assert_challenge_payout_writer",
    "collect_live_inventory",
    "completion_truth",
    "confidence_band",
    "evaluate_s14",
    "log_conf_gate",
    "log_cost_of_error",
    "pick_cost_of_error",
    "rebuild_choice_criteria",
    "run_fluid_gate_cycle",
    "shadow_enabled",
    "verify_side_effect",
]

"""Owner process lock 2026-09-17: shadow score first, then wire.

Not eternal shadow. Not same-pass blind live wire.

Chair 2026-09-17 Wave E: both named wires PROVED_SHADOW on Challenge tape.
Owner spoken NAME 2026-09-17 ~18:18 ICT (Borhen): "apply everything yes".
Clarification the same hour: that NAME is the Alive organism program, not
two hooks. APPLY the two proved wires now. Subsequent fluid PROVED_SHADOW
gates are pre-authorized to APPLY without a new chat ritual unless the
gate would place / remint / flatten or break envelope walls.

Envelope / prop-firm walls stay integers — never Jev toys.

Place / remint / flatten stay fail-closed unless owner ``PLACE_APPLY=1``
clears the Challenge envelope in :mod:`src.judgment.place_apply`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .place_apply import cage_stamp

LOCK_ID = "shadow_score_then_wire"
LOCK_SPOKEN = "2026-09-17"

# Project gtos FABLE_TO_redacted_account named this first. Cost-hurtful at UB-PLC-017.
WIRE_COST = "F5-JEV-004"
# This repo named this first. Flow-alignment size tilt on admitted XAU.
WIRE_FLOW = "f5_xau_flow_alignment_size_tilt"
# Named CA size wire. Owner NAMED APPLY 2026-09-18 ~21:34 ICT (size_tilt only).
WIRE_CA_SIZE = "ca_cross_asset_size_tilt"
WIRE_CANDIDATE = WIRE_FLOW  # backward-compat alias
WIRE_CANDIDATES = (WIRE_COST, WIRE_FLOW)
APPLIED_WIRES = (WIRE_FLOW, WIRE_COST, WIRE_CA_SIZE)

LEAVE_ORIG_TICKETS = frozenset({"293332188"})

OWNER_NAME = "Borhen"
OWNER_NAME_SPOKEN = "apply everything yes"
OWNER_NAMED_AT = "2026-09-17T11:18:00Z"  # ~18:18 ICT
OWNER_NAMED_CA_AT = "2026-09-18T14:34:00Z"  # ~21:34 ICT spoken FULL APPROVAL
OWNER_NAMED_CA_SPOKEN = "FULL APPROVAL land swarm onto Challenge f5-live; CA-SIZ-001 NAMED APPLY size_tilt only"
OWNER_CLARIFIED = "alive_organism_not_two_hooks"

# Pre-authorized APPLY effects after PROVED_SHADOW. Not place/remint/flatten.
PREAUTH_EFFECTS = frozenset({"size_tilt", "label"})
FORBIDDEN_AUTO_EFFECTS = frozenset({"place", "remint", "flatten", "envelope"})

ENVELOPE_WALL_IDS = frozenset(
    {
        "ENV-KILL",
        "ENV-TWO-STOP",
        "ENV-TOKEN",
        "ENV-H8",
        "ENV-DD",
        "ENV-US30",
        "ENV-OCC",
        "ENV-DEAD",
        "$KILL",
        "two_stop_count",
        "token_digest",
        "h8_flatten",
        "hard_dd",
        "us30_off",
        "occupancy_keep_one",
        "dead_window_writer_clock",
    }
)

PROVE_VERDICTS = ("NOT_PROVED", "PROVED_SHADOW", "APPLIED_NAMED")
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROVE = REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "W_NAMED_PROVE.json"
DEFAULT_PROVE_COST = REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "F5_JEV_004_PROVE.json"
DEFAULT_PROVE_DUAL = REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "W_DUAL_PROVE.json"
DEFAULT_APPLIED = REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "APPLIED_NAMED.json"
DEFAULT_FLUID_PROVE = REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "FLUID_PROVE_LEDGER.json"
DEFAULT_PROVE_CA_SIZE = REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "CA_SIZE_SHADOW_PROVE.json"

# Ticket 293332188 closed on host 2026-09-17T11:10:58Z (broker_closed).
# Leave-orig lock stays. No remint.
TICKET_293332188_CLOSED_UTC = "2026-09-17T11:10:58Z"

# Pre-registered prove bars (frozen before this pack's prove read).
PROVE_BARS_FLOW = {
    "min_xau_sufficient": 20,
    "min_shadow_tilt_moved": 5,
    "live_tilt_must_be_one_while_locked": True,
    "invented_high_forbidden": True,
}
# Cost wire can score without M15. Still cannot refuse / skip / zero a fire.
PROVE_BARS_COST = {
    "min_xau_cost_complete": 20,
    "min_shadow_cost_tilt_moved": 5,
    "live_tilt_must_be_one_while_locked": True,
    "invented_high_forbidden": True,
    "cannot_refuse": True,
}
PROVE_BARS = PROVE_BARS_FLOW  # backward-compat
# Remaining 45 fluid gates — frozen before the 2026-09-17 Challenge re-score.
PROVE_BARS_FLUID_SIZE = {
    "min_decidable": 20,
    "min_moved": 5,
    "min_distinct": 2,
    "invented_high_forbidden": True,
}
PROVE_BARS_FLUID_LABEL = {
    "min_decidable": 20,
    "min_non_default": 5,
    "min_distinct": 2,
    "invented_high_forbidden": True,
}
# Named CA size wire — same moved/distinct bars as other size wires.
# Owner NAMED APPLY 2026-09-18. Live may follow the haircutted shadow.
# apply_claimed stays 0 until a live Challenge place.
PROVE_BARS_CA_SIZE = {
    "min_decidable": 20,
    "min_moved": 5,
    "min_distinct": 2,
    "invented_high_forbidden": True,
    "live_tilt_must_be_one": False,
    "cannot_refuse": True,
    "physical_size_stays_flow_x_cost_x_ca": True,
}

FLOW_TILT_MIN = 0.70
FLOW_TILT_MAX = 1.15
COST_TILT_MIN = 0.70
COST_TILT_MAX = 1.00
# Conservative veto-class. Cannot add size. Cannot zero a fire.
CA_TILT_MIN = 0.70
CA_TILT_MAX = 1.00


def leave_orig_ticket(ticket: Any) -> bool:
    if ticket is None:
        return False
    return str(ticket).strip() in LEAVE_ORIG_TICKETS


def stamp_lock() -> dict[str, Any]:
    return {
        "process_lock": LOCK_ID,
        "process_lock_spoken": LOCK_SPOKEN,
        "same_pass_blind_live_forbidden": True,
        "eternal_shadow_forbidden": True,
        "wire_candidate": WIRE_CANDIDATE,
        "wire_candidates": list(WIRE_CANDIDATES),
        "chair_named_first_wire": WIRE_COST,
        "fable_named_first_wire": WIRE_FLOW,
        "shadow_both": True,
        "wire_apply": True,
        "owner_named": True,
        "owner_named_by": OWNER_NAME,
        "owner_named_spoken": OWNER_NAME_SPOKEN,
        "owner_named_at": OWNER_NAMED_AT,
        "owner_named_ca_at": OWNER_NAMED_CA_AT,
        "owner_named_ca_spoken": OWNER_NAMED_CA_SPOKEN,
        "owner_clarified": OWNER_CLARIFIED,
        "applied_wires": list(APPLIED_WIRES),
        "leave_orig_293332188": True,
        "ticket_293332188_closed_utc": TICKET_293332188_CLOSED_UTC,
        **cage_stamp(),
        "envelope_walls_stay_integers": True,
        "subsequent_fluid_preauthorized": True,
        "subsequent_fluid_preauth_effects": sorted(PREAUTH_EFFECTS),
        "subsequent_fluid_preauth_except": sorted(FORBIDDEN_AUTO_EFFECTS),
        "alive_organism": True,
        "verdict_era": "APPLIED_NAMED",
    }


def prove_path(wire_id: str | None = None) -> Path:
    override = (os.environ.get("GTOS_JEV_W_PROVE_PATH") or "").strip()
    if override and wire_id is None:
        return Path(override)
    if wire_id == WIRE_COST:
        return DEFAULT_PROVE_COST
    if wire_id == WIRE_CA_SIZE:
        return DEFAULT_PROVE_CA_SIZE
    if wire_id == "dual":
        return DEFAULT_PROVE_DUAL
    if wire_id == "applied":
        return DEFAULT_APPLIED
    if wire_id == "fluid":
        return DEFAULT_FLUID_PROVE
    return DEFAULT_PROVE


def load_prove(path: Path | None = None) -> dict[str, Any] | None:
    file = path or prove_path()
    if not file.is_file():
        return None
    try:
        payload = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def owner_named_env() -> str | None:
    raw = (os.environ.get("GTOS_JEV_W_NAMED") or "").strip()
    return raw or None


def ready_to_name(*, prove: dict[str, Any] | None = None) -> bool:
    packed = prove if prove is not None else load_prove()
    if not packed:
        return False
    return (
        packed.get("process_lock") == LOCK_ID
        and packed.get("verdict") in {"PROVED_SHADOW", "APPLIED_NAMED"}
        and packed.get("wire_candidate") in WIRE_CANDIDATES
    )


def owner_has_named(*, prove: dict[str, Any] | None = None, wire_id: str | None = None) -> bool:
    if wire_id in APPLIED_WIRES:
        return True
    packed = prove if prove is not None else load_prove()
    if packed and packed.get("wire_candidate") in APPLIED_WIRES and packed.get("verdict") in {
        "PROVED_SHADOW",
        "APPLIED_NAMED",
    }:
        return True
    named = owner_named_env()
    return ready_to_name(prove=packed) and named == (packed or {}).get("wire_candidate")


def envelope_wall(wire_id: str | None) -> bool:
    if not wire_id:
        return False
    return str(wire_id) in ENVELOPE_WALL_IDS


def wire_apply_open(
    wire_id: str | None = None,
    *,
    ticket: Any = None,
    prove: dict[str, Any] | None = None,
) -> bool:
    """APPLY is open for the named size wires except leave-orig tickets.

    Env flags cannot open envelope walls, leave-orig, or place/remint/flatten.
    Subsequent fluid gates apply only after PROVED_SHADOW and only for
    size_tilt / label effects — see ``fluid_pipeline``. Physical lots still
    need ``GTOS_JEV_APPLY_LIVE=1`` + Challenge login/ns in ``apply_size``.
    """
    del prove  # prove is recorded; APPLY of named size wires is owner-named
    if leave_orig_ticket(ticket):
        return False
    if envelope_wall(wire_id):
        return False
    if wire_id is None:
        return True
    if wire_id in APPLIED_WIRES:
        return True
    return False


def live_multiplier(
    shadow_tilt: float,
    *,
    wire_id: str | None = WIRE_FLOW,
    ticket: Any = None,
    prove: dict[str, Any] | None = None,
    lo: float | None = None,
    hi: float | None = None,
) -> float:
    """Live size follows the named wire clamp when APPLY is open for that row."""
    if wire_id == WIRE_COST:
        lo = COST_TILT_MIN if lo is None else lo
        hi = COST_TILT_MAX if hi is None else hi
    elif wire_id == WIRE_CA_SIZE:
        lo = CA_TILT_MIN if lo is None else lo
        hi = CA_TILT_MAX if hi is None else hi
    else:
        lo = FLOW_TILT_MIN if lo is None else lo
        hi = FLOW_TILT_MAX if hi is None else hi
    if not wire_apply_open(wire_id, ticket=ticket, prove=prove):
        return 1.0
    try:
        value = float(shadow_tilt)
    except (TypeError, ValueError):
        return 1.0
    return round(min(hi, max(lo, value)), 4)

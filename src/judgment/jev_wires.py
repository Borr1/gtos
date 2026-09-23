"""close_grok / jev_wires hist registry — APPLY_CANDIDATE or KILL, no resting SHADOW.

The VPS draft folder ``judgment/jev_wires_grok_20260921`` and the box
receipt ``APPLY_KILL_RECEIPTS_GROK_WIRES_HIST_0`` are not on this
worktree. The close_grok set that *is* here is the 46 ``src/judgment``
modules that exist on the judgment tip and were still missing from the
package live import path (``src.judgment.__init__``).

Each module is hist-classified against Challenge login 0 tape
and sealed receipts. APPLY_CANDIDATE modules are re-exported from the
package. KILL modules stay importable for prove/tests but cannot open
APPLY. The three remaining fluid SHADOW gates stay HARD_BLOCKER — they
are missing poles, not resting wires.

Never places / remints / flattens / order_send. ``pack1b_beaten`` stays
false. Do not invent NEWS_PROTOCOL.
"""

from __future__ import annotations

from typing import Any, Mapping

from .challenge import CHALLENGE_LOGIN
from .process_lock import APPLIED_WIRES, LOCK_ID, stamp_lock
from .veto import InventedNewsProtocolVeto, JevPlacePathVeto, refuse_invented_news_protocol

SCHEMA = "gtos.judgment.jev_wires_hist.v0"
PACK_ID = "jev_wires_grok_20260921"
LOGIN = int(CHALLENGE_LOGIN)
NS = "operator"
MAGIC = 0
PACK1B_BEATEN = False

# Sealed hist — Wave M / FLUID_PROVE_LEDGER / SHADOW_UNLOCK_BACKLOG.
HARD_BLOCKER_GATES = {
    "FLUID-HLD-005": (
        "trail_vs_orig — 10 decidable / 1 distinct {false:10} on Challenge "
        "0 tape; TRAIL_EPS 0.05 never true. Do not invent a trail."
    ),
    "FLUID-HLD-008": (
        "friday_cutoff_label — 97/97 false; Friday 16:00Z+ pole absent. "
        "Do not rename to close_session."
    ),
    "FLUID-NWS-005": (
        "spine_empty — 97/97 false; host unread is not empty spine. "
        "Do not invert. Do not invent NEWS_PROTOCOL."
    ),
}

RESEARCH_ONLY_GATES = {
    "SEL-V4-002": "PROVED_SHADOW research-only. Do not import from selector_v4.py (R2 / H1).",
}

# Dig-key modules still unintegrated from the package live import path.
UNINTEGRATED_MODULES = (
    "apply_size",
    "bars",
    "ca_size",
    "ca_size_prove",
    "chair_enforce",
    "challenge_shadow",
    "compose",
    "cross_asset",
    "cross_asset_prove",
    "data_inventory",
    "everywhere_tape",
    "fluid_gates",
    "fluid_local",
    "fluid_pipeline",
    "fluid_prove",
    "harvest_patterns",
    "harvest_prove",
    "hold_from_tape",
    "host_events",
    "host_occupancy",
    "host_sites",
    "jev_client",
    "jev_questions",
    "learn_loop",
    "named_sources",
    "news_calendar_sync",
    "news_spine",
    "occupancy",
    "p0_hist_prove",
    "peers",
    "rdf_questions",
    "regime_buckets",
    "regime_compose",
    "regime_system_one",
    "s14_tape",
    "s15_tape",
    "s16_fixtures",
    "s16_flags",
    "s16_guard",
    "s16_heuristics",
    "shadow_unlock",
    "sleeve_from_tape",
    "symbol_class",
    "two_stop",
    "wire_prove",
    "world_questions",
)

# Hist sources (on-disk, Challenge 0). Not invented.
_HIST = {
    "applied_named": "judgment/astra/lab/wires/APPLIED_NAMED.json",
    "wave_apply": "judgment/astra/lab/wires/WAVE_APPLY_RECEIPT.json",
    "wave_m": "judgment/astra/lab/wires/WAVE_M_RECEIPT.json",
    "fluid_prove": "judgment/astra/lab/wires/FLUID_PROVE_LEDGER.json",
    "shadow_unlock": "judgment/astra/lab/wires/SHADOW_UNLOCK_BACKLOG.md",
    "chair_land": "judgment/CHAIR_LAND_RECIPE_VPS_F5_LIVE.md",
    "inventory": "judgment/astra/JEV_GATE_INVENTORY.json",
}

APPLY_CANDIDATE: dict[str, dict[str, str]] = {
    "apply_size": {
        "reason": "Named physical haircut on Challenge writer (book_owner + execution).",
        "hist": "WAVE_APPLY_RECEIPT + APPLIED_NAMED + HOST_APPLY_ALIVE",
        "effect": "size_tilt",
    },
    "bars": {
        "reason": "Challenge-true M15/H4 books; compose sufficient predicate.",
        "hist": "WAVE_M state_sufficient fix; challenge_tape_present",
        "effect": "label",
    },
    "ca_size": {
        "reason": "ca_cross_asset_size_tilt NAMED APPLY 2026-09-18 size_tilt only.",
        "hist": "APPLIED_NAMED.ca_siz_001 + CA_SIZE_SHADOW_PROVE",
        "effect": "size_tilt",
    },
    "chair_enforce": {
        "reason": "G1–G8 ENFORCE labels on S14 admit/size. Never weakens hard-off.",
        "hist": "judgment/astra/chair_enforce_g1_g8.json",
        "effect": "label",
    },
    "challenge_shadow": {
        "reason": "Challenge-true shadow pack scorer used by Wave E/M prove.",
        "hist": "challenge_shadow_20260917 n=97",
        "effect": "label",
    },
    "compose": {
        "reason": "Live size compose: flow × cost × ca named APPLY wires.",
        "hist": "WAVE_APPLY_RECEIPT files_flipped + process_lock APPLIED_NAMED",
        "effect": "size_tilt",
    },
    "cross_asset": {
        "reason": "Typed CA labels consumed by ca_size. Not a silent CA flip.",
        "hist": "CROSS_ASSET_PROVE_V0 + CA-SIZ-001 consumes 7 labels",
        "effect": "label",
    },
    "everywhere_tape": {
        "reason": "Challenge 0 close tape already on cycle everywhere prove.",
        "hist": "cycle.compose_everywhere + everywhere_tape",
        "effect": "label",
    },
    "fluid_gates": {
        "reason": "48-fluid / 8-envelope inventory. Envelope walls stay integers.",
        "hist": "JEV_GATE_INVENTORY.json n_fluid=48 n_applied=44",
        "effect": "label",
    },
    "fluid_local": {
        "reason": "Local instruments + attach_fluid on compose (APPLIED_NAMED axes).",
        "hist": "compose.compose_shadow attach_fluid; Wave M ADM-008/009",
        "effect": "label",
    },
    "fluid_pipeline": {
        "reason": "Preauth APPLY for PROVED_SHADOW size_tilt/label. Not place.",
        "hist": "process_lock PREAUTH_EFFECTS + FLUID_PROVE_LEDGER",
        "effect": "label",
    },
    "hold_from_tape": {
        "reason": "Hold/exit extras for APPLIED_NAMED HLD labels (not HLD-005).",
        "hist": "FLUID-HLD-001..004/006/007 APPLIED_NAMED; HLD-005 HARD_BLOCKER",
        "effect": "label",
    },
    "host_events": {
        "reason": "Host events.jsonl trail + calendar honesty. Never invents HIGH.",
        "hist": "WAVE_M calendar_honest 87/10; trail poles absent",
        "effect": "label",
    },
    "host_occupancy": {
        "reason": "Live occupancy/governor extras on Challenge book_owner path.",
        "hist": "book_owner host_occupancy_governor; HOST_B_OCCUPANCY_GOVERNOR",
        "effect": "label",
    },
    "host_sites": {
        "reason": "VPS f5-live landing map for named APPLY hooks.",
        "hist": "WAVE_APPLY_RECEIPT + HOST_SITES_LAND",
        "effect": "label",
    },
    "jev_client": {
        "reason": "TypeSafe POSTs default-on when key present. Never send authority.",
        "hist": "package docstring; answers are compose inputs",
        "effect": "label",
    },
    "jev_questions": {
        "reason": "A1 / Alive fan-out covering the 48 fluid questions.",
        "hist": "WAVE_APPLY_RECEIPT files_flipped; test_fluid_inventory",
        "effect": "label",
    },
    "occupancy": {
        "reason": "Challenge-true occupancy extras from deal tape (ENV-OCC integer).",
        "hist": "envelope ENV-OCC; occupancy_at on gold_state path",
        "effect": "label",
    },
    "p0_hist_prove": {
        "reason": "FIRE 1201 KEEP-win gate on cycle LABEL APPLY. Prove refuses APPLY env.",
        "hist": "CHAIR_LAND_RECIPE §4 wins_preserved; cycle.hist_prove_allows_label_apply",
        "effect": "label",
    },
    "peers": {
        "reason": "Named USDJPY peer books into gold_state. Never invent DXY.",
        "hist": "HOST_A_PEERS_USDJPY; peers live on gold_state",
        "effect": "label",
    },
    "regime_buckets": {
        "reason": "S14 bucket emitter already on cycle evaluate_s14.",
        "hist": "cycle.run_fluid_gate_cycle S14 branch",
        "effect": "label",
    },
    "regime_compose": {
        "reason": "S14 compose already on the admit sidecar (not a parallel place path).",
        "hist": "cycle + S14_REGIME_GATE_SHADOW",
        "effect": "label",
    },
    "regime_system_one": {
        "reason": "S14 question pack + cache used by cycle.",
        "hist": "cycle S14_QUESTION_IDS",
        "effect": "label",
    },
    "s14_tape": {
        "reason": "Challenge 0 hist tape for S14. No live bars invented.",
        "hist": "s14_historical_tape + cycle evaluate_s14",
        "effect": "label",
    },
    "s15_tape": {
        "reason": "Challenge 0 hist tape for S15 COST_OF_ERROR.",
        "hist": "s15_tape_authority_baked; cycle cost_of_error",
        "effect": "label",
    },
    "sleeve_from_tape": {
        "reason": "ac60_score for APPLIED_NAMED FLUID-SIZ-007.",
        "hist": "fluid_local.ac60_score; inventory FLUID-SIZ-007 APPLIED_NAMED",
        "effect": "size_tilt",
    },
    "symbol_class": {
        "reason": "Challenge-true asset-class map for symbol_state.v0.",
        "hist": "NON_XAU_REMEASURE + symbol_state live",
        "effect": "label",
    },
    "two_stop": {
        "reason": "ENV-TWO-STOP integer counter. Reads closed[] only.",
        "hist": "process_lock ENVELOPE_WALL_IDS; never a Jev toy",
        "effect": "envelope",
    },
    "wire_prove": {
        "reason": "Named-wire prove-out. APPLY-era records APPLIED_NAMED; do not re-shadow.",
        "hist": "WAVE_APPLY_RECEIPT + W_DUAL_PROVE / WAVE_E",
        "effect": "label",
    },
}

KILL_WIRES: dict[str, dict[str, str]] = {
    "ca_size_prove": {
        "reason": "Offline prove harness. Not a live APPLY entrypoint.",
        "hist": "ca_size_prove never flips CA label APPLY",
    },
    "cross_asset_prove": {
        "reason": "Offline CROSS_ASSET prove harness. Not live APPLY.",
        "hist": "CROSS_ASSET_PROVE_V0 research prove",
    },
    "data_inventory": {
        "reason": "Read-only inventory. No APPLY surface.",
        "hist": "DATA_INVENTORY_ALL_INSTRUMENTS.json",
    },
    "fluid_prove": {
        "reason": "Remaining-gate prove runner. Cannot APPLY HARD_BLOCKER poles.",
        "hist": "FLUID_PROVE_LEDGER n_not_proved=3",
    },
    "harvest_patterns": {
        "reason": "TRAIN_HARVEST SHADOW+CALL only. ready_to_apply=false.",
        "hist": "Dig E TRAIN_HARVEST ALREADY_LIVE APPLY=0; harvest_patterns research-only",
    },
    "harvest_prove": {
        "reason": "SHADOW prove for harvest P0 atoms. Not APPLY.",
        "hist": "harvest_prove Challenge 0 SHADOW",
    },
    "learn_loop": {
        "reason": "Close-loop research store. Never silent APPLY.",
        "hist": "learn_loop docstring; Chair ritual required",
    },
    "named_sources": {
        "reason": "Research on-disk sources for RDF. Not live APPLY.",
        "hist": "named_sources + rates_dxy_funding research-only",
    },
    "news_calendar_sync": {
        "reason": "NEWS invent forbidden. Sync FROM spine only. NWS-005 not proved.",
        "hist": "WAVE_M FLUID-NWS-005 constant false; no NEWS_PROTOCOL",
    },
    "news_spine": {
        "reason": "Load HIGH spines fail-closed. Empty spine is not APPLY.",
        "hist": "FLUID-NWS-005 HARD_BLOCKER; refuse_invented_news_protocol",
    },
    "rdf_questions": {
        "reason": "RDF Jev pack. Code compose never resizes and never APPLY.",
        "hist": "rdf_questions docstring",
    },
    "s16_fixtures": {
        "reason": "Dig E DIG_MULTI_STAGE_GUARD KILL. Prove fixtures only.",
        "hist": "CHAIR_LAND_RECIPE GTOS_DIG_MULTI_STAGE_GUARD_APPLY never; Dig E consume",
    },
    "s16_flags": {
        "reason": "Dig E DIG_MULTI_STAGE_GUARD KILL. Dual-flag off Challenge place.",
        "hist": "s16_flags APPLY_ENV; CHAIR_LAND_RECIPE prove exit 2",
    },
    "s16_guard": {
        "reason": "Dig E DIG_MULTI_STAGE_GUARD KILL. Never Challenge place path.",
        "hist": "s16_guard never place; Dig E / s20 residual KILL",
    },
    "s16_heuristics": {
        "reason": "S16 local heuristics. Guard family is KILL.",
        "hist": "DIG_MULTI_STAGE_GUARD KILL",
    },
    "shadow_unlock": {
        "reason": "Remaining SHADOW backlog. Does not APPLY a SHADOW gate.",
        "hist": "SHADOW_UNLOCK_BACKLOG 3 HARD_BLOCKER gates",
    },
    "world_questions": {
        "reason": "WORLD_STATE_V0 question pack. Never APPLY / send.",
        "hist": "world_questions docstring",
    },
}

LIVE_IMPORT_MODULES = (
    "apply_size",
    "bars",
    "ca_size",
    "chair_enforce",
    "challenge_shadow",
    "compose",
    "fluid_gates",
    "fluid_local",
    "fluid_pipeline",
    "host_occupancy",
    "host_sites",
    "jev_questions",
    "jev_wires",
    "p0_hist_prove",
    "two_stop",
    "wire_prove",
)

_KILL_ALIASES = frozenset(KILL_WIRES) | frozenset(
    {
        "DIG_MULTI_STAGE_GUARD",
        "GTOS_DIG_MULTI_STAGE_GUARD",
        "GTOS_DIG_MULTI_STAGE_GUARD_SHADOW",
        "GTOS_DIG_MULTI_STAGE_GUARD_APPLY",
        "NEWS_PROTOCOL",
        "news_protocol",
        "TRAIN_HARVEST_APPLY",
    }
)


def _norm(name: str | None) -> str:
    return str(name or "").strip()


def classify_module(name: str) -> str:
    key = _norm(name)
    if key in APPLY_CANDIDATE:
        return "APPLY_CANDIDATE"
    if key in KILL_WIRES:
        return "KILL"
    raise KeyError(f"unclassified_jev_wire:{key}")


def is_kill_wire(name: str | None) -> bool:
    key = _norm(name)
    if not key:
        return False
    return key in _KILL_ALIASES or key in HARD_BLOCKER_GATES or key in RESEARCH_ONLY_GATES


def is_hard_blocker_gate(gate_id: str | None) -> bool:
    return _norm(gate_id) in HARD_BLOCKER_GATES or _norm(gate_id) in RESEARCH_ONLY_GATES


def refuse_kill_apply(name: str | None, *, invented_files: tuple[str, ...] = ()) -> None:
    """Fence KILL / HARD_BLOCKER / invented NEWS from any APPLY entrypoint."""

    refuse_invented_news_protocol(invented_files)
    key = _norm(name)
    if not key:
        return
    if key in {"NEWS_PROTOCOL", "news_protocol"} or key.lower().endswith("news_protocol"):
        raise InventedNewsProtocolVeto("NEWS_PROTOCOL invent forbidden")
    if key in HARD_BLOCKER_GATES:
        raise JevPlacePathVeto(f"hard_blocker_no_apply:{key}")
    if key in RESEARCH_ONLY_GATES:
        raise JevPlacePathVeto(f"research_only_no_apply:{key}")
    if key in _KILL_ALIASES:
        raise JevPlacePathVeto(f"kill_fenced:{key}")


def assert_pack_closed() -> dict[str, Any]:
    missing = [m for m in UNINTEGRATED_MODULES if m not in APPLY_CANDIDATE and m not in KILL_WIRES]
    extra = [m for m in list(APPLY_CANDIDATE) + list(KILL_WIRES) if m not in UNINTEGRATED_MODULES]
    overlap = sorted(set(APPLY_CANDIDATE) & set(KILL_WIRES))
    shadow_modules = [
        m
        for m, row in {**APPLY_CANDIDATE, **KILL_WIRES}.items()
        if str(row.get("verdict") or "").upper() == "SHADOW"
    ]
    return {
        "ok": not missing and not extra and not overlap and not shadow_modules,
        "n_unintegrated": len(UNINTEGRATED_MODULES),
        "n_apply_candidate": len(APPLY_CANDIDATE),
        "n_kill": len(KILL_WIRES),
        "missing": missing,
        "extra": extra,
        "overlap": overlap,
        "resting_shadow_modules": shadow_modules,
        "pack1b_beaten": PACK1B_BEATEN,
        "hard_blocker_gates": sorted(HARD_BLOCKER_GATES),
    }


def live_import_stamp() -> dict[str, Any]:
    closed = assert_pack_closed()
    return {
        "schema": SCHEMA,
        "pack_id": PACK_ID,
        "login": LOGIN,
        "ns": NS,
        "magic": MAGIC,
        "process_lock": LOCK_ID,
        "pack1b_beaten": PACK1B_BEATEN,
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "never_order_send": True,
        "no_news_invent": True,
        "no_resting_shadow": True,
        "n_apply_candidate": closed["n_apply_candidate"],
        "n_kill": closed["n_kill"],
        "apply_candidate": sorted(APPLY_CANDIDATE),
        "kill": sorted(KILL_WIRES),
        "hard_blocker_gates": sorted(HARD_BLOCKER_GATES),
        "research_only_gates": sorted(RESEARCH_ONLY_GATES),
        "live_import_modules": list(LIVE_IMPORT_MODULES),
        "applied_named_wires": list(APPLIED_WIRES),
        "vps_draft_folder_present": False,
        "box_receipt_present": False,
        "hist_sources": dict(_HIST),
        "closed": closed["ok"],
    }


def hist_rollup(*, prove_ledger: Mapping[str, Any] | None = None) -> dict[str, Any]:
    from .fluid_pipeline import pipeline_snapshot

    snap = pipeline_snapshot(prove_ledger=dict(prove_ledger) if prove_ledger else None)
    stamp = live_import_stamp()
    return {
        **stamp,
        **stamp_lock(),
        "schema": SCHEMA,
        "fluid_pipeline": {
            "n_fluid": snap.get("n_fluid"),
            "n_applied": snap.get("n_applied"),
            "n_proved_shadow": snap.get("n_proved_shadow"),
            "n_shadow": snap.get("n_shadow"),
            "n_may_auto_apply": snap.get("n_may_auto_apply"),
        },
        "note": (
            "VPS jev_wires_grok_20260921 drafts absent on this box. "
            "Classification is the 46 unintegrated src/judgment modules "
            "against Challenge 0 hist receipts. pack1b_beaten=false."
        ),
    }

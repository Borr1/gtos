"""Prove remaining fluid gates on a Challenge-true shadow pack.

Frozen bars live in process_lock. Never invent a pass. Never place.
SEL-V4-002 may PROVED_SHADOW; it cannot APPLY.
Envelope walls are not in this file.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .fluid_gates import (
    auto_apply_eligible,
    fluid_gates,
    load_inventory,
    lookup,
    set_gate_status,
)
from .fluid_pipeline import APPLIED, PROVED, SHADOW, may_auto_apply, pipeline_snapshot
from .process_lock import (
    APPLIED_WIRES,
    DEFAULT_FLUID_PROVE,
    LOCK_ID,
    PROVE_BARS_FLUID_LABEL,
    PROVE_BARS_FLUID_SIZE,
    WIRE_COST,
    WIRE_FLOW,
    stamp_lock,
)


def _iter_rows(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def _fluid(row: dict[str, Any]) -> dict[str, Any]:
    return ((row.get("compose") or {}).get("fluid") or {}).get("gates") or row.get("fluid") or {}


def _state(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("state") or {}


def _alias_parent(gate: dict[str, Any]) -> str | None:
    if gate.get("alias_wire"):
        return str(gate["alias_wire"])
    aliases = gate.get("alias_wires") or []
    if aliases:
        return str(aliases[0])
    return None


def _invented_high(rows: list[dict[str, Any]]) -> int:
    n = 0
    for row in rows:
        news = (_state(row).get("news") or {})
        if news.get("spine_empty") and news.get("high_in_f5_window") is True:
            n += 1
    return n


def _refused(rows: list[dict[str, Any]], gate_id: str) -> int:
    n = 0
    for row in rows:
        inst = _fluid(row).get(gate_id) or {}
        if inst.get("refuse"):
            n += 1
        wires = (row.get("compose") or {}).get("wires") or {}
        if (wires.get(WIRE_COST) or {}).get("refuse"):
            n += 1
    return n


def prove_gate(rows: list[dict[str, Any]], gate: dict[str, Any]) -> dict[str, Any]:
    gid = str(gate.get("id") or "")
    effect = str(gate.get("effect") or "label")
    bars = PROVE_BARS_FLUID_SIZE if effect == "size_tilt" else PROVE_BARS_FLUID_LABEL
    decidable = []
    moved = []
    values: list[Any] = []
    for row in rows:
        inst = _fluid(row).get(gid) or {}
        if not inst.get("decidable"):
            continue
        decidable.append(row)
        values.append(inst.get("shadow"))
        if inst.get("moved"):
            moved.append(row)
    distinct = {json.dumps(v, default=str) for v in values}
    reasons: list[str] = []
    invented = _invented_high(rows)
    refused = _refused(rows, gid)
    if invented:
        reasons.append(f"invented_high n={invented} — empty spine claimed F5 HIGH")
    if refused:
        reasons.append(f"refused n={refused} — fluid gate cannot skip/choke")
    if gate.get("research_only") and False:
        pass
    if len(decidable) < int(bars["min_decidable"]):
        reasons.append(
            f"decidable {len(decidable)} < {bars['min_decidable']} — need Challenge-true named state"
        )
    if effect == "size_tilt":
        if len(moved) < int(bars["min_moved"]):
            reasons.append(f"shadow_moved {len(moved)} < {bars['min_moved']} — wire would be a no-op")
    else:
        if len(moved) < int(bars["min_non_default"]):
            reasons.append(f"non_default {len(moved)} < {bars['min_non_default']} — label is constant/absent")
    if len(distinct) < int(bars["min_distinct"]) and len(decidable) >= int(bars["min_decidable"]):
        reasons.append(f"distinct {len(distinct)} < {bars['min_distinct']} — constant_on_this_tape")
    verdict = PROVED if not reasons else "NOT_PROVED"
    if gate.get("research_only") and verdict == PROVED:
        apply_next = "research_only_no_apply"
    elif verdict == PROVED and auto_apply_eligible(gate):
        apply_next = "apply_preauthorized"
    elif verdict == PROVED:
        apply_next = "chair_ritual_required"
    else:
        apply_next = "remain_shadow"
    return {
        "id": gid,
        "question": gate.get("question"),
        "family": gate.get("family"),
        "effect": effect,
        "chair": gate.get("chair"),
        "verdict": verdict,
        "ready_to_apply": verdict == PROVED and auto_apply_eligible(gate) and not gate.get("research_only"),
        "research_only": bool(gate.get("research_only")),
        "cannot_refuse": bool(gate.get("cannot_refuse")),
        "bars": bars,
        "n": len(rows),
        "n_decidable": len(decidable),
        "n_moved": len(moved),
        "n_distinct": len(distinct),
        "n_invented_high": invented,
        "n_refused": refused,
        "reasons": reasons,
        "next": apply_next,
    }


def inherit_applied(gate: dict[str, Any], *, parent: str) -> dict[str, Any]:
    return {
        "id": gate.get("id"),
        "question": gate.get("question"),
        "family": gate.get("family"),
        "effect": gate.get("effect"),
        "chair": gate.get("chair"),
        "verdict": APPLIED,
        "inherited_from": parent,
        "ready_to_apply": auto_apply_eligible(gate),
        "research_only": bool(gate.get("research_only")),
        "cannot_refuse": bool(gate.get("cannot_refuse")),
        "n": 0,
        "n_decidable": 0,
        "n_moved": 0,
        "n_distinct": 0,
        "n_invented_high": 0,
        "n_refused": 0,
        "reasons": [],
        "next": "live_named",
    }


def prove_remaining(rows: list[dict[str, Any]]) -> dict[str, Any]:
    gates = []
    applied: list[str] = []
    proved: list[str] = []
    not_proved: list[str] = []
    inherited: list[str] = []
    for gate in fluid_gates():
        gid = str(gate.get("id") or "")
        if gid in APPLIED_WIRES or gate.get("status") == APPLIED:
            rec = inherit_applied(gate, parent=gid)
            rec["verdict"] = APPLIED
            rec["already_applied"] = True
            gates.append(rec)
            applied.append(gid)
            continue
        parent = _alias_parent(gate)
        parent_gate = lookup(parent) if parent else None
        if parent in APPLIED_WIRES or (parent_gate and parent_gate.get("status") == APPLIED):
            rec = inherit_applied(gate, parent=str(parent))
            gates.append(rec)
            applied.append(gid)
            inherited.append(gid)
            continue
        rec = prove_gate(rows, gate)
        gates.append(rec)
        if rec["verdict"] == PROVED:
            proved.append(gid)
        else:
            not_proved.append(gid)
    return {
        "schema": "gtos.judgment.fluid_prove.v0",
        **stamp_lock(),
        "process_lock": LOCK_ID,
        "n_rows": len(rows),
        "n_fluid": len(gates),
        "n_already_applied": len([g for g in fluid_gates() if g.get("status") == APPLIED or g.get("id") in APPLIED_WIRES]),
        "n_inherited": len(inherited),
        "n_proved_shadow": len(proved),
        "n_not_proved": len(not_proved),
        "inherited": inherited,
        "proved": proved,
        "not_proved": not_proved,
        "gates": {g["id"]: g for g in gates},
        "kinds": dict(Counter(r.get("kind") for r in rows)),
        "proved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": (
            "PROVED_SHADOW size_tilt/label is pre-authorized to APPLY. "
            "SEL-V4-002 stays research-only. Envelope walls stay integers. "
            "Physical lots stay flow × cost. Never place/remint/flatten."
        ),
    }


def apply_preauthorized(ledger: dict[str, Any]) -> dict[str, Any]:
    """Mark eligible PROVED_SHADOW gates APPLIED_NAMED in the inventory."""
    applied: list[str] = []
    held: list[str] = []
    for gid, rec in (ledger.get("gates") or {}).items():
        if rec.get("already_applied"):
            continue
        if rec.get("inherited_from") and rec.get("verdict") == APPLIED:
            set_gate_status(gid, APPLIED)
            applied.append(gid)
            continue
        if rec.get("verdict") != PROVED:
            continue
        if rec.get("research_only") or not rec.get("ready_to_apply"):
            if rec.get("verdict") == PROVED:
                set_gate_status(gid, PROVED)
                held.append(gid)
            continue
        if not may_auto_apply(gid, prove_ledger={gid: PROVED}):
            held.append(gid)
            set_gate_status(gid, PROVED)
            continue
        set_gate_status(gid, APPLIED)
        rec["verdict"] = APPLIED
        rec["next"] = "live_named"
        applied.append(gid)
    load_inventory.cache_clear()
    ledger["applied_this_wave"] = applied
    ledger["held_research_or_ritual"] = held
    ledger["pipeline_after"] = pipeline_snapshot()
    return ledger


def prove_file(shadow_path: Path, *, out: Path | None = None, apply: bool = True) -> dict[str, Any]:
    rows = list(_iter_rows(shadow_path))
    receipt = prove_remaining(rows)
    if apply:
        receipt = apply_preauthorized(receipt)
    dest = out or DEFAULT_FLUID_PROVE
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(receipt, indent=2, default=str) + "\n", encoding="utf-8")
    receipt["out"] = str(dest)
    return receipt

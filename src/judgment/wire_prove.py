"""Prove-out for both named wire candidates.

Shadow-era prove (``era="shadow_prove"``) still requires live tilts = 1.0
on the pack. Do **not** re-run that era on a pack whose live tilts have
moved after APPLY.

APPLY-era (``era="applied"``) records APPLIED_NAMED from Wave E + owner
NAME. It does not fail because live ≠ 1.0 or ``wire_apply`` is open.
Invented HIGH and cost-refuse still fail in both eras.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .process_lock import (
    APPLIED_WIRES,
    LOCK_ID,
    LOCK_SPOKEN,
    OWNER_NAME,
    OWNER_NAME_SPOKEN,
    OWNER_NAMED_AT,
    PROVE_BARS_COST,
    PROVE_BARS_FLOW,
    WIRE_COST,
    WIRE_FLOW,
    prove_path,
    stamp_lock,
)


def _iter_rows(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def _sym(row: dict[str, Any]) -> str:
    return str(((row.get("state") or {}).get("identity") or {}).get("symbol") or row.get("symbol") or "")


def _compose(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("compose") or {}


def _state(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("state") or {}


def _common_failures(rows: list[dict[str, Any]], *, era: str = "shadow_prove") -> list[str]:
    reasons: list[str] = []
    live_not_one = [
        r
        for r in rows
        if abs(float((_compose(r).get("live_size_tilt") if _compose(r).get("live_size_tilt") is not None else 1.0) or 1.0) - 1.0) > 1e-9
        or abs(float((_compose(r).get("live_cost_tilt") if _compose(r).get("live_cost_tilt") is not None else 1.0) or 1.0) - 1.0) > 1e-9
    ]
    apply_claimed = [r for r in rows if _compose(r).get("apply_this_row") or _compose(r).get("disposition") == "named_apply"]
    invented_high = [
        r
        for r in rows
        if (_state(r).get("news") or {}).get("spine_empty")
        and (_state(r).get("news") or {}).get("high_in_f5_window") is True
    ]
    refused = [
        r
        for r in rows
        if (_compose(r).get("wires") or {}).get(WIRE_COST, {}).get("refuse")
        or _compose(r).get("f5_jev_004_refuse")
    ]
    if era == "shadow_prove":
        if live_not_one:
            reasons.append(f"live_size_tilt_nonzero n={len(live_not_one)} — lock broken")
        if apply_claimed:
            reasons.append(f"wire_apply_claimed n={len(apply_claimed)} — same-pass apply forbidden")
    if invented_high:
        reasons.append(f"invented_high n={len(invented_high)} — empty spine claimed F5 HIGH")
    if refused:
        reasons.append(f"cost_wire_refused n={len(refused)} — F5-JEV-004 cannot skip/choke")
    return reasons


def prove_shadow(rows: list[dict[str, Any]], *, wire_id: str = WIRE_FLOW, era: str = "shadow_prove") -> dict[str, Any]:
    if wire_id == WIRE_COST:
        return _prove_cost(rows, era=era)
    return _prove_flow(rows, era=era)


def _prove_flow(rows: list[dict[str, Any]], *, era: str) -> dict[str, Any]:
    xau = [r for r in rows if _sym(r) == "XAUUSD"]
    sufficient = [
        r
        for r in xau
        if (_state(r).get("completeness") or {}).get("state_sufficient_for_live")
    ]
    tilt_moved = [
        r
        for r in xau
        if abs(float((_compose(r).get("shadow_size_tilt") if _compose(r).get("shadow_size_tilt") is not None else _compose(r).get("size_tilt")) or 1.0) - 1.0) > 1e-9
    ]
    reasons = []
    if len(sufficient) < PROVE_BARS_FLOW["min_xau_sufficient"]:
        reasons.append(
            f"xau_sufficient {len(sufficient)} < {PROVE_BARS_FLOW['min_xau_sufficient']} — need Challenge-true tape, not April hats"
        )
    if len(tilt_moved) < PROVE_BARS_FLOW["min_shadow_tilt_moved"]:
        reasons.append(
            f"shadow_tilt_moved {len(tilt_moved)} < {PROVE_BARS_FLOW['min_shadow_tilt_moved']} — wire would be a no-op"
        )
    reasons.extend(_common_failures(rows, era=era))
    return _receipt(
        wire_id=WIRE_FLOW,
        rows=rows,
        reasons=reasons,
        bars=PROVE_BARS_FLOW,
        era=era,
        extra={
            "n_xau": len(xau),
            "n_xau_sufficient": len(sufficient),
            "n_shadow_tilt_moved": len(tilt_moved),
        },
    )


def _prove_cost(rows: list[dict[str, Any]], *, era: str) -> dict[str, Any]:
    xau = [r for r in rows if _sym(r) == "XAUUSD"]
    cost_complete = [
        r
        for r in xau
        if (_state(r).get("completeness") or {}).get("cost")
        or ((_state(r).get("cost") or {}).get("spread_r_of_stop") is not None)
    ]
    tilt_moved = [
        r
        for r in xau
        if abs(float((_compose(r).get("shadow_cost_tilt") if _compose(r).get("shadow_cost_tilt") is not None else 1.0) or 1.0) - 1.0) > 1e-9
    ]
    reasons = []
    if len(cost_complete) < PROVE_BARS_COST["min_xau_cost_complete"]:
        reasons.append(
            f"xau_cost_complete {len(cost_complete)} < {PROVE_BARS_COST['min_xau_cost_complete']} — need Challenge spread_r, not invented ticks"
        )
    if len(tilt_moved) < PROVE_BARS_COST["min_shadow_cost_tilt_moved"]:
        reasons.append(
            f"shadow_cost_tilt_moved {len(tilt_moved)} < {PROVE_BARS_COST['min_shadow_cost_tilt_moved']} — cost wire would be a no-op"
        )
    reasons.extend(_common_failures(rows, era=era))
    return _receipt(
        wire_id=WIRE_COST,
        rows=rows,
        reasons=reasons,
        bars=PROVE_BARS_COST,
        era=era,
        extra={
            "n_xau": len(xau),
            "n_xau_cost_complete": len(cost_complete),
            "n_shadow_cost_tilt_moved": len(tilt_moved),
        },
    )


def _receipt(
    *,
    wire_id: str,
    rows: list[dict[str, Any]],
    reasons: list[str],
    bars: dict[str, Any],
    extra: dict[str, Any],
    era: str,
) -> dict[str, Any]:
    shadow_verdict = "PROVED_SHADOW" if not reasons else "NOT_PROVED"
    if era == "applied" and shadow_verdict == "PROVED_SHADOW" and wire_id in APPLIED_WIRES:
        verdict = "APPLIED_NAMED"
    else:
        verdict = shadow_verdict
    families = Counter((r.get("house") or {}).get("family_class") for r in rows)
    kinds = Counter(r.get("kind") for r in rows)
    live_not_one = [
        r
        for r in rows
        if abs(float((_compose(r).get("live_size_tilt") if _compose(r).get("live_size_tilt") is not None else 1.0) or 1.0) - 1.0) > 1e-9
        or abs(float((_compose(r).get("live_cost_tilt") if _compose(r).get("live_cost_tilt") is not None else 1.0) or 1.0) - 1.0) > 1e-9
    ]
    invented_high = [
        r
        for r in rows
        if (_state(r).get("news") or {}).get("spine_empty")
        and (_state(r).get("news") or {}).get("high_in_f5_window") is True
    ]
    return {
        "schema": "gtos.judgment.w_named_prove.v0",
        **stamp_lock(),
        "process_lock": LOCK_ID,
        "process_lock_spoken": LOCK_SPOKEN,
        "wire_candidate": wire_id,
        "era": era,
        "verdict": verdict,
        "ready_to_name": shadow_verdict == "PROVED_SHADOW",
        "owner_named": True,
        "owner_named_by": OWNER_NAME,
        "owner_named_spoken": OWNER_NAME_SPOKEN,
        "owner_named_at": OWNER_NAMED_AT,
        "bars": bars,
        "n": len(rows),
        "n_live_tilt_not_one": len(live_not_one),
        "n_invented_high": len(invented_high),
        "kinds": dict(kinds),
        "families": {str(k): v for k, v in families.items()},
        "reasons": reasons,
        "proved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": (
            "APPLIED_NAMED is written from Wave E PROVED_SHADOW + owner NAME. "
            "Do not re-run shadow_prove on a live-moving pack."
        ),
        **extra,
    }


def _progress(receipt: dict[str, Any]) -> float:
    bars = receipt.get("bars") or {}
    if receipt.get("wire_candidate") == WIRE_COST:
        a = (receipt.get("n_xau_cost_complete") or 0) / max(1, bars.get("min_xau_cost_complete") or 1)
        b = (receipt.get("n_shadow_cost_tilt_moved") or 0) / max(1, bars.get("min_shadow_cost_tilt_moved") or 1)
        return min(a, b)
    a = (receipt.get("n_xau_sufficient") or 0) / max(1, bars.get("min_xau_sufficient") or 1)
    b = (receipt.get("n_shadow_tilt_moved") or 0) / max(1, bars.get("min_shadow_tilt_moved") or 1)
    return min(a, b)


def prove_dual(rows: list[dict[str, Any]], *, era: str = "shadow_prove") -> dict[str, Any]:
    flow = prove_shadow(rows, wire_id=WIRE_FLOW, era=era)
    cost = prove_shadow(rows, wire_id=WIRE_COST, era=era)
    scores = {WIRE_FLOW: _progress(flow), WIRE_COST: _progress(cost)}
    proved = [
        w
        for w, rec in ((WIRE_FLOW, flow), (WIRE_COST, cost))
        if rec["verdict"] in {"PROVED_SHADOW", "APPLIED_NAMED"}
    ]
    if proved:
        hint = proved[0] if len(proved) == 1 else "tie_both_proved"
    elif scores[WIRE_COST] > scores[WIRE_FLOW]:
        hint = WIRE_COST
    elif scores[WIRE_FLOW] > scores[WIRE_COST]:
        hint = WIRE_FLOW
    else:
        hint = "neither"
    return {
        "schema": "gtos.judgment.dual_wire_prove.v0",
        **stamp_lock(),
        "era": era,
        "candidates": {WIRE_FLOW: flow, WIRE_COST: cost},
        "progress": scores,
        "clears_first_hint": hint,
        "prefer_without_choke": True,
        "apply_either": True,
        "applied_wires": list(APPLIED_WIRES),
        "proved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "APPLY era for the two named wires. Subsequent fluid still shadow until PROVED_SHADOW.",
    }


def prove_file(shadow_path: Path, *, out: Path | None = None, wire_id: str = WIRE_FLOW, era: str = "shadow_prove") -> dict[str, Any]:
    rows = list(_iter_rows(shadow_path))
    receipt = prove_shadow(rows, wire_id=wire_id, era=era)
    dest = out or prove_path(wire_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    receipt["out"] = str(dest)
    return receipt


def prove_dual_file(shadow_path: Path, *, out: Path | None = None, era: str = "shadow_prove") -> dict[str, Any]:
    rows = list(_iter_rows(shadow_path))
    receipt = prove_dual(rows, era=era)
    dest = out or prove_path("dual")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    flow_dest = prove_path(WIRE_FLOW)
    cost_dest = prove_path(WIRE_COST)
    flow_dest.write_text(json.dumps(receipt["candidates"][WIRE_FLOW], indent=2) + "\n", encoding="utf-8")
    cost_dest.write_text(json.dumps(receipt["candidates"][WIRE_COST], indent=2) + "\n", encoding="utf-8")
    receipt["out"] = str(dest)
    receipt["out_flow"] = str(flow_dest)
    receipt["out_cost"] = str(cost_dest)
    return receipt

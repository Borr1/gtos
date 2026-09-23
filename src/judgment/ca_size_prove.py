"""Offline prove for the named CA size wire on the Challenge shadow pack.

Never places. Never flips CA-* label APPLY. Never invents NEWS_PROTOCOL.
Owner NAMED APPLY 2026-09-18 (size_tilt only). Combined live is
flow × cost × ca. apply_claimed stays 0 until a live Challenge place.

Bars match other size wires: 20 decidable / 5 moved / 2 distinct.
Peer admit is the same Challenge gate as the CA label pack (PR #13).
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ca_size import WIRE_ID, score_ca_size
from .compose import compose_shadow
from .cross_asset_prove import (
    DEFAULT_PACK,
    score_pack_rows,
    survey_challenge_surface,
)
from .process_lock import (
    LOCK_ID,
    PROVE_BARS_CA_SIZE,
    WIRE_CA_SIZE,
    prove_path,
    stamp_lock,
    wire_apply_open,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROVE = prove_path(WIRE_CA_SIZE)
DEFAULT_RECEIPT = REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "CA_SIZE_SHADOW_WIRE.md"


def _invented_high(world: dict[str, Any], news: dict[str, Any] | None = None) -> bool:
    packed_news = news or {}
    ev = world.get("event_join") or {}
    if ev.get("spine_empty") and (
        ev.get("usd_high_in_window") is True
        or packed_news.get("high_in_f5_window") is True
    ):
        return True
    if packed_news.get("spine_empty") and packed_news.get("high_in_f5_window") is True:
        return True
    return False


def _compose_row(rec: dict[str, Any]) -> dict[str, Any]:
    identity = {
        "side": rec.get("side") or ((rec.get("state") or {}).get("identity") or {}).get("side"),
        "symbol": rec.get("symbol") or ((rec.get("state") or {}).get("identity") or {}).get("symbol") or "XAUUSD",
        "family_class": ((rec.get("state") or {}).get("identity") or {}).get("family_class") or "study",
        "candidate_id": rec.get("ticket"),
    }
    state = {
        "identity": identity,
        "world": rec.get("world") or {},
        "completeness": ((rec.get("state") or {}).get("completeness") or {"state_sufficient_for_live": True}),
        "news": ((rec.get("state") or {}).get("news") or {}),
        "cost": ((rec.get("state") or {}).get("cost") or {}),
        "occupancy": ((rec.get("state") or {}).get("occupancy") or {}),
        "timeframes": ((rec.get("state") or {}).get("timeframes") or {}),
    }
    return compose_shadow(state, ticket=rec.get("ticket"))


def prove_ca_size_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    bars = dict(PROVE_BARS_CA_SIZE)
    decidable: list[dict[str, Any]] = []
    moved: list[dict[str, Any]] = []
    values: list[float] = []
    live_not_one: list[dict[str, Any]] = []
    apply_claimed: list[dict[str, Any]] = []
    invented: list[dict[str, Any]] = []
    refused: list[dict[str, Any]] = []
    combined_matches: int = 0
    scored_rows: list[dict[str, Any]] = []

    for rec in rows:
        world = rec.get("world") or {}
        side = rec.get("side") or ((rec.get("state") or {}).get("identity") or {}).get("side")
        news = ((rec.get("state") or {}).get("news") or {})
        scored = score_ca_size(world, side=side)
        composed = _compose_row({**rec, "side": side})
        ca_wire = (composed.get("wires") or {}).get(WIRE_CA_SIZE) or {}
        row = {
            **rec,
            "ca": scored,
            "compose": composed,
            "shadow": scored["shadow"],
            "live": composed.get("live_ca_size_tilt"),
            "apply": bool(ca_wire.get("apply") or composed.get("ca_cross_asset_size_tilt_apply")),
        }
        scored_rows.append(row)
        if _invented_high(world, news):
            invented.append(row)
        if ca_wire.get("refuse"):
            refused.append(row)
        try:
            live = float(composed.get("live_ca_size_tilt") if composed.get("live_ca_size_tilt") is not None else 1.0)
        except (TypeError, ValueError):
            live = 1.0
        if abs(live - 1.0) > 1e-9:
            live_not_one.append(row)
        if row["apply"] or wire_apply_open(WIRE_CA_SIZE, ticket=rec.get("ticket")):
            apply_claimed.append(row)
        live_flow = float(composed.get("live_size_tilt") if composed.get("live_size_tilt") is not None else 1.0)
        live_cost = float(composed.get("live_cost_tilt") if composed.get("live_cost_tilt") is not None else 1.0)
        live_ca = float(composed.get("live_ca_size_tilt") if composed.get("live_ca_size_tilt") is not None else 1.0)
        combined = float(composed.get("combined_live_tilt") if composed.get("combined_live_tilt") is not None else 1.0)
        if abs(combined - round(live_flow * live_cost * live_ca, 4)) < 1e-9:
            combined_matches += 1
        if not scored.get("decidable"):
            continue
        decidable.append(row)
        values.append(float(scored["shadow"]))
        if scored.get("moved"):
            moved.append(row)

    distinct = {round(v, 4) for v in values}
    assembled_counts: Counter[str] = Counter()
    moved_counts: Counter[str] = Counter()
    for row in scored_rows:
        for name, block in ((row.get("ca") or {}).get("components") or {}).items():
            if block.get("assembled"):
                assembled_counts[name] += 1
            if block.get("assembled") and abs(float(block.get("tilt") or 1.0) - 1.0) > 1e-9:
                moved_counts[name] += 1
    reasons: list[str] = []
    if invented:
        reasons.append(f"invented_high n={len(invented)} — empty spine claimed HIGH")
    if refused:
        reasons.append(f"refused n={len(refused)} — CA size cannot skip/choke")
    if rows and combined_matches != len(rows):
        reasons.append(
            f"combined_live_tilt not flow_x_cost_x_ca n={len(rows) - combined_matches}"
        )
    if len(decidable) < int(bars["min_decidable"]):
        reasons.append(f"decidable {len(decidable)} < {bars['min_decidable']} — need Challenge-true CA labels")
    if len(moved) < int(bars["min_moved"]):
        reasons.append(f"shadow_moved {len(moved)} < {bars['min_moved']} — wire would be a no-op")
    if len(distinct) < int(bars["min_distinct"]) and len(decidable) >= int(bars["min_decidable"]):
        reasons.append(f"distinct {len(distinct)} < {bars['min_distinct']} — constant_on_this_tape")

    verdict = "PROVED_SHADOW" if not reasons else "NOT_PROVED"
    return {
        "id": "CA-SIZ-001",
        "wire": WIRE_ID,
        "effect": "size_tilt",
        "verdict": verdict,
        "apply": False,
        "apply_claimed": 0,
        "ready_to_name": verdict == "PROVED_SHADOW",
        "owner_named": True,
        "owner_named_at": "2026-09-18T14:34:00Z",
        "n": len(rows),
        "n_decidable": len(decidable),
        "n_moved": len(moved),
        "n_distinct": len(distinct),
        "n_live_not_one": len(live_not_one),
        "n_apply_claimed": len(apply_claimed),
        "n_invented_high": len(invented),
        "n_refused": len(refused),
        "n_combined_flow_x_cost": combined_matches,
        "vals": dict(Counter(f"{round(v, 4):.4f}" for v in values)),
        "component_assembled": dict(assembled_counts),
        "component_moved": dict(moved_counts),
        "reasons": reasons,
        "bars": bars,
        "scored_rows": scored_rows,
    }


def run_prove(
    *,
    pack_path: Path | None = None,
    deals_path: Path | None = None,
    write: bool = True,
) -> dict[str, Any]:
    survey = survey_challenge_surface()
    raw_rows = score_pack_rows(pack_path or DEFAULT_PACK, deals_path=deals_path)
    # score_pack_rows does not keep side; recover from identity on assembled world path.
    rows: list[dict[str, Any]] = []
    for rec in raw_rows:
        identity = ((rec.get("state") or {}).get("identity") or {})
        if not identity:
            # Pack rows scored by cross_asset_prove omit original state. Side is gold-default unknown.
            identity = {"symbol": "XAUUSD"}
        rows.append(
            {
                **rec,
                "side": rec.get("side") or identity.get("side"),
                "symbol": rec.get("symbol") or identity.get("symbol") or "XAUUSD",
            }
        )
    target = prove_ca_size_rows(rows)
    lock = stamp_lock()
    payload = {
        "schema": "gtos.judgment.ca_size_prove.v0",
        **lock,
        "process_lock": LOCK_ID,
        "wire_candidate": WIRE_CA_SIZE,
        "named_new_fire": True,
        "not_silent_ca_apply_flip": True,
        "ca_label_apply_any": False,
        "wire_apply": True,
        "verdict_era": "APPLIED_NAMED" if target["verdict"] == "PROVED_SHADOW" else target["verdict"],
        "verdict": target["verdict"],
        "apply": False,
        "apply_claimed": 0,
        "ready_to_name": target["ready_to_name"],
        "owner_named": True,
        "owner_named_at": "2026-09-18T14:34:00Z",
        "n_rows": len(rows),
        "survey": {
            "landed_challenge_symbols": survey["landed_challenge_symbols"],
            "wanted_challenge_m15": survey["wanted_challenge_m15"],
            "april_historical_is_not_challenge": True,
            "dxy_is_not_challenge": True,
            "peer_admit": survey.get("peer_admit"),
            "hydrate_channel": survey.get("hydrate_channel"),
            "this_vm_hydrated_from_vps": survey.get("this_vm_hydrated_from_vps"),
        },
        "bars": target["bars"],
        "target": {k: v for k, v in target.items() if k != "scored_rows"},
        "physical_size": {
            "stays_flow_x_cost": False,
            "stays_flow_x_cost_x_ca": True,
            "new_size_axis_applied": True,
            "apply_claimed": 0,
            "n_rows_combined_flow_x_cost_x_ca": target["n_combined_flow_x_cost"],
            "clamps": {
                "flow": [0.70, 1.15],
                "cost": [0.70, 1.00],
                "ca": [0.70, 1.00],
            },
            "spoken": "Owner NAMED APPLY 2026-09-18T14:34Z. Combined live = flow × cost × ca. apply_claimed=0 until a live Challenge place.",
        },
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "envelope_walls_stay_integers": True,
        "invented_news_protocol": False,
        "proved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    # Drop scored_rows from disk payload — keep counts/vals only.
    if write:
        dest = DEFAULT_PROVE
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        payload["prove_path"] = str(dest.relative_to(REPO_ROOT))
    return payload

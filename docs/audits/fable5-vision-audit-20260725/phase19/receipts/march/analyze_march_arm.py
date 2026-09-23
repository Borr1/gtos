"""Score one March decode arm against the March R0 baseline (MARCH_PREREG_V1 §4–§5).

Deliberately a re-implementation rather than a port: FA's `analyze_t2_arm.py` lived
in job-tmp and is gone, so this script is validated the only honest way available —
by reproducing every January T2 number in `receipts/forensic/t2/T2_ARM_*_ANALYSIS.json`
from the January routes before it is ever pointed at March (`--self-check`).

Two rules from B2 that are easy to get wrong and are enforced here:

* **Contest-site diffs are reported separately from shared-trade economics.** A
  selection contest that swaps which of two candidates wins is not an economic
  change to any trade; averaging the two together is how a seed-noise artifact
  gets published as a repair effect.
* **The 0.751 R seed band is a floor, not a decoration.** `inside_seed_band` is
  computed for every monthly delta and any |Δ| ≤ 0.751 is NOT_EVALUABLE as an
  economic direction (prereg §5).

Trade identity is the engine's own canonical replay candidate instance key
(`package_new_entry_authority_canonical_replay_candidate_instance_key`), which is
`<candidate_id>@@<decision_time_utc>` — stable across arms by construction, unlike
`simulated_trade_id`, which embeds the route prefix and would make every trade look
"only in this arm".
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterator

SEED_BAND_R = 0.751

TRADE_FIELDS = (
    "net_r",
    "symbol",
    "direction",
    "entry_time_utc",
    "exit_time_utc",
    "origin_family",
    "route_family",
    "candidate_origin_family",
    "policy_target_r",
    "target_r",
    "raw_target_r",
    "terminal_outcome",
    "close_reason",
    "stop_loss",
    "entry_price",
    "package_new_entry_authority_candidate_id",
    "package_new_entry_authority_canonical_replay_candidate_instance_key",
    "package_new_entry_authority_decision_time_utc",
    "simulated_trade_id",
)


def _open_ledger(route: Path, suffix: str) -> Iterator[dict[str, Any]]:
    """Yield rows from `<ROUTE>/<PREFIX>_<suffix>.jsonl[.gz]`."""

    prefix = route.name
    plain = route / f"{prefix}_{suffix}.jsonl"
    gz = route / f"{prefix}_{suffix}.jsonl.gz"
    if gz.is_file():
        handle = gzip.open(gz, "rt", encoding="utf-8")
    elif plain.is_file():
        handle = plain.open("r", encoding="utf-8")
    else:
        return
    with handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_trades(route: Path) -> list[dict[str, Any]]:
    rows = []
    for raw in _open_ledger(route, "TRADE_LEDGER"):
        rows.append({key: raw.get(key) for key in TRADE_FIELDS})
    return rows


def trade_key(row: dict[str, Any]) -> str:
    key = row.get("package_new_entry_authority_canonical_replay_candidate_instance_key")
    if key:
        return str(key)
    # Fallback identity: symbol + decision time + direction. Named in the receipt
    # when used, because it is coarser than the canonical key and could merge two
    # same-symbol same-instant candidates.
    return "|".join(
        str(row.get(field))
        for field in ("symbol", "package_new_entry_authority_decision_time_utc", "direction")
    )


def _day(row: dict[str, Any]) -> str:
    stamp = row.get("package_new_entry_authority_decision_time_utc") or row.get(
        "entry_time_utc"
    )
    return str(stamp)[:10]


def _family(row: dict[str, Any]) -> str:
    return str(
        row.get("origin_family")
        or row.get("route_family")
        or row.get("candidate_origin_family")
        or "UNKNOWN"
    )


def _net(row: dict[str, Any]) -> float | None:
    value = row.get("net_r")
    return None if value is None else float(value)


def _diff_row(row: dict[str, Any]) -> dict[str, Any]:
    """FA's readable set-difference row, kept identical so the two are comparable."""

    return {
        "day": _day(row),
        "sym": row.get("symbol"),
        "fam": _family(row),
        "net": _net(row),
    }


def _bootstrap_ci(
    deltas: list[float], *, reps: int = 10_000, alpha: float = 0.10, seed: int = 20260805
) -> tuple[float, float] | None:
    """Daily bootstrap over paired daily deltas; 90 % interval on the MONTHLY total.

    Resampling days (not trades) is the unit the prereg's power section is stated
    in, and it keeps within-day contest structure intact.
    """

    if len(deltas) < 2:
        return None
    rng = random.Random(seed)
    n = len(deltas)
    totals = []
    for _ in range(reps):
        totals.append(sum(deltas[rng.randrange(n)] for _ in range(n)))
    totals.sort()
    lo = totals[max(0, int(math.floor((alpha / 2) * reps)) - 1)]
    hi = totals[min(reps - 1, int(math.ceil((1 - alpha / 2) * reps)) - 1)]
    return (round(lo, 4), round(hi, 4))


def analyse(
    *,
    arm_route: Path,
    baseline_route: Path,
    arm_receipt: Path | None = None,
    control_route: Path | None = None,
    label: str = "",
) -> dict[str, Any]:
    arm = load_trades(arm_route)
    base = load_trades(baseline_route)

    arm_by_key = {trade_key(row): row for row in arm}
    base_by_key = {trade_key(row): row for row in base}
    shared = sorted(set(arm_by_key) & set(base_by_key))
    only_arm = sorted(set(arm_by_key) - set(base_by_key))
    only_base = sorted(set(base_by_key) - set(arm_by_key))

    arm_total = sum(_net(r) or 0.0 for r in arm)
    base_total = sum(_net(r) or 0.0 for r in base)
    unscoreable_arm = [trade_key(r) for r in arm if _net(r) is None]
    unscoreable_base = [trade_key(r) for r in base if _net(r) is None]

    by_day_arm: dict[str, float] = defaultdict(float)
    by_day_base: dict[str, float] = defaultdict(float)
    for row in arm:
        by_day_arm[_day(row)] += _net(row) or 0.0
    for row in base:
        by_day_base[_day(row)] += _net(row) or 0.0
    days = sorted(set(by_day_arm) | set(by_day_base))
    daily_deltas = [round(by_day_arm[d] - by_day_base[d], 8) for d in days]

    # Shared-trade economics: the SAME trade in both arms. Movement here is a
    # repriced fill; movement in the set difference is a contest/admission change.
    per_trade_deltas = []
    moved = 0
    for key in shared:
        a, b = _net(arm_by_key[key]), _net(base_by_key[key])
        if a is None or b is None:
            continue
        delta = a - b
        per_trade_deltas.append(delta)
        if abs(delta) > 1e-9:
            moved += 1

    contest_only_arm_r = sum(_net(arm_by_key[k]) or 0.0 for k in only_arm)
    contest_only_base_r = sum(_net(base_by_key[k]) or 0.0 for k in only_base)

    delta_total = arm_total - base_total
    payload: dict[str, Any] = {
        "label": label or arm_route.name,
        "arm_route": arm_route.name,
        "baseline_route": baseline_route.name,
        "trade_identity": (
            "package_new_entry_authority_canonical_replay_candidate_instance_key"
        ),
        "book": {
            "arm_total_net_r": round(arm_total, 4),
            "r0_total_net_r": round(base_total, 4),
            "delta_total_net_r": round(delta_total, 4),
            "seed_band_r": SEED_BAND_R,
            "inside_seed_band": bool(abs(delta_total) <= SEED_BAND_R),
            "economic_direction_evaluable": bool(abs(delta_total) > SEED_BAND_R),
            "arm_trades": len(arm),
            "r0_trades": len(base),
            "days_union": len(days),
            "days_nonzero_delta": sum(1 for d in daily_deltas if abs(d) > 1e-9),
            "daily_delta_sd": (
                round(statistics.stdev(daily_deltas), 4) if len(daily_deltas) > 1 else 0.0
            ),
            "daily_delta_bootstrap90_monthly_total": _bootstrap_ci(daily_deltas),
            "unscoreable_arm_trades": len(unscoreable_arm),
            "unscoreable_r0_trades": len(unscoreable_base),
        },
        "shared_trades": {
            "n": len(shared),
            "n_scoreable_pairs": len(per_trade_deltas),
            "moved_economics": moved,
            # `None`, not 0.0, when there is no sample. A zero here would read as
            # "measured no movement" on a cell that measured nothing at all --
            # and arms (iii)/(v) have exactly zero shared trades in January.
            "mean_per_trade_delta": (
                round(statistics.fmean(per_trade_deltas), 5) if per_trade_deltas else None
            ),
            "sd_per_trade_delta": (
                round(statistics.stdev(per_trade_deltas), 5)
                if len(per_trade_deltas) > 1
                else None
            ),
            "sum_shared_delta_r": round(sum(per_trade_deltas), 4),
        },
        "contest_sites": {
            "note": (
                "B2 rule 3: admission/contest differences are reported separately "
                "from shared-trade economics. These R sums are NOT repriced fills."
            ),
            "only_arm_n": len(only_arm),
            "only_arm_sum_net_r": round(contest_only_arm_r, 4),
            "only_r0_n": len(only_base),
            "only_r0_sum_net_r": round(contest_only_base_r, 4),
            "admission_delta_r": round(contest_only_arm_r - contest_only_base_r, 4),
        },
        "admitted_set_diff": {
            "only_arm": [_diff_row(arm_by_key[k]) for k in only_arm],
            "only_r0": [_diff_row(base_by_key[k]) for k in only_base],
            "only_arm_keys": only_arm,
            "only_r0_keys": only_base,
        },
        "family_mix_arm": dict(Counter(_family(r) for r in arm).most_common()),
        "family_mix_r0": dict(Counter(_family(r) for r in base).most_common()),
        "daily": {
            "days": days,
            "arm_net_r": [round(by_day_arm[d], 6) for d in days],
            "r0_net_r": [round(by_day_base[d], 6) for d in days],
            "delta_net_r": daily_deltas,
        },
    }

    # P5's first clause. "Transformed admissions" is measured against the arm's
    # OWN control -- the identical composition without `candidate_breaker_transform`
    # (arm (iii) for arm (v)) -- never against r0, whose different composition
    # would make ordinary contest differences look like transform purchases. When
    # no control route is given the transform is not installed in this arm and the
    # count is 0 STRUCTURALLY; the receipt says which of the two it is.
    if control_route is None:
        payload["transformed_trades"] = {
            "n": 0,
            "basis": "transform_not_installed_in_this_arm",
            "control_route": None,
            "tp_provenance": [],
            "tp_provenance_status": "NOT_EVALUABLE_no_transform_in_arm",
        }
    else:
        control = load_trades(control_route)
        control_by_key = {trade_key(row): row for row in control}
        bought = [
            arm_by_key[key]
            for key in sorted(set(arm_by_key) - set(control_by_key))
            if _family(arm_by_key[key]) == "current_breaker_re_entry"
        ]
        payload["transformed_trades"] = {
            "n": len(bought),
            "basis": "arm_minus_own_control_restricted_to_current_breaker_re_entry",
            "control_route": control_route.name,
            "control_trades": len(control),
            "arm_breaker_trades": sum(
                1 for r in arm if _family(r) == "current_breaker_re_entry"
            ),
            "control_breaker_trades": sum(
                1 for r in control if _family(r) == "current_breaker_re_entry"
            ),
            # The declaration's first question (amendment 2, 008aec561): the
            # missed pool prices policy 2R by construction, so a transformed
            # trade must be asked what target it ACTUALLY carried.
            "tp_provenance": [
                {
                    "key": trade_key(row),
                    "symbol": row.get("symbol"),
                    "direction": row.get("direction"),
                    "entry_price": row.get("entry_price"),
                    "stop_loss": row.get("stop_loss"),
                    "policy_target_r": row.get("policy_target_r"),
                    "target_r": row.get("target_r"),
                    "raw_target_r": row.get("raw_target_r"),
                    "terminal_outcome": row.get("terminal_outcome"),
                    "close_reason": row.get("close_reason"),
                    "net_r": row.get("net_r"),
                }
                for row in bought
            ],
            "tp_provenance_status": (
                "NOT_EVALUABLE_zero_transformed_admissions"
                if not bought
                else "ANSWERED_FROM_TRADE_ROWS"
            ),
        }

    if arm_receipt is not None and arm_receipt.is_file():
        receipt = json.loads(arm_receipt.read_text(encoding="utf-8"))
        payload["receipt"] = {
            "error": receipt.get("error"),
            "wall_seconds": receipt.get("wall_seconds"),
            "rss_peak_gb": (
                round(float(receipt["rss_peak_bytes"]) / 2**30, 2)
                if receipt.get("rss_peak_bytes")
                else None
            ),
            # The runner writes `economics_counts`, not `economics`. FA's January
            # analyses carry the same four numbers under the same names, so the
            # first draft's `economics` lookup returned None for all four and the
            # January self-check could not catch it -- it compares the fields the
            # published JSONs carry, and the published JSONs were written by a
            # different extractor. Caught by reading the March receipts.
            "economics_counts": {
                key: (receipt.get("economics_counts") or {}).get(key)
                for key in ("trade", "order", "scorecard", "missed")
            },
            "repair_report": receipt.get("repair_report"),
            "cut_report": receipt.get("cut_report"),
            "lane_window_id": receipt.get("resolved_window_id"),
            "surface_map_id": (receipt.get("lane_spec") or {}).get("surface_map_id"),
        }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm-route", type=Path, required=True)
    parser.add_argument("--baseline-route", type=Path, required=True)
    parser.add_argument("--arm-receipt", type=Path)
    parser.add_argument(
        "--transform-control-route",
        type=Path,
        help=(
            "the arm's OWN control -- identical composition without "
            "candidate_breaker_transform (arm (iii) for arm (v)). Only pass it for "
            "the arm that installs the transform."
        ),
    )
    parser.add_argument("--label", default="")
    parser.add_argument("--out", type=Path)
    ns = parser.parse_args()
    payload = analyse(
        arm_route=ns.arm_route,
        baseline_route=ns.baseline_route,
        arm_receipt=ns.arm_receipt,
        control_route=ns.transform_control_route,
        label=ns.label,
    )
    text = json.dumps(payload, indent=1, sort_keys=True, default=str) + "\n"
    if ns.out:
        ns.out.parent.mkdir(parents=True, exist_ok=True)
        ns.out.write_text(text, encoding="utf-8")
        print(f"written: {ns.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

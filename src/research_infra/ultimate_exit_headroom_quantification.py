"""Exit-engine headroom quantification (go/no-go gate for the exit tournament).

Measures, per segment and globally, how much R the exit layer could honestly
recover from the replay ledgers BEFORE any exit-policy tournament is run:

1. Winner giveback: distribution of ``mfe_r - final_r`` across winners — the
   measured upper bound any trail/giveback retune can capture.
2. Harvest counterfactual delta: actual ``final_r`` vs the recorded
   profit-harvest counterfactual exit on closed trades.
3. Early-loss-abort headroom (coarse anatomy pass): for stop-tighten rules
   "raise stop to -x once MAE <= -x before the p-progress milestone is
   touched", the saved R on losers NET of the winners the same rule would
   have killed. Time ordering uses milestone first-touch vs MAE timestamps;
   this is a COARSE UPPER BOUND (MAE time is the final-extreme time, not the
   first -x crossing). The exact pass happens inside the tournament with
   hydrated paths.

The tournament only runs for segments whose total measured headroom clears
``GO_THRESHOLD_R_PER_DAY``; everything else is documented as "alpha problem
is selection, not exits".

Research-only; replay/proxy evidence; no broker mutation.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research_infra.learned_edge_dataset_builder import (
    ASSET_CLASS_BY_SYMBOL,
    as_float,
    discover_partition_ledgers,
    read_jsonl,
    stable_sha256,
)

SCHEMA_VERSION = "ultimate_exit_headroom_quantification_v1"
METHOD = "coarse_anatomy_upper_bound_pass_exact_pass_requires_path_hydration"
GO_THRESHOLD_R_PER_DAY = 0.5

ABORT_THRESHOLDS_R = (0.4, 0.5, 0.6, 0.7)
PROGRESS_FLOORS_R = (0.25, 0.5)

BOUNDARY = {
    "broker_operation": False,
    "paid_api_or_vendor_call": False,
    "broker_runtime_change_status": False,
    "validation_result_status": False,
    "outcome_result_rows_status": False,
}


def _parse_time(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _milestone_first_touch(trade_row: Mapping[str, Any], threshold_r: float) -> datetime | None:
    milestones = trade_row.get("milestones")
    if not isinstance(milestones, Mapping):
        return None
    key = f"{threshold_r:g}r"
    entry = milestones.get(key)
    if not isinstance(entry, Mapping):
        return None
    if entry.get("reached") is not True:
        return None
    return _parse_time(entry.get("first_touch_utc"))


def _progress_reached_before(
    trade_row: Mapping[str, Any], *, threshold_r: float, before: datetime | None
) -> bool:
    """True when the p-progress milestone was touched strictly before ``before``."""

    touch = _milestone_first_touch(trade_row, threshold_r)
    if touch is None:
        return False
    if before is None:
        # No MAE timestamp -> conservative: treat progress as having come
        # first so the abort rule neither fires (loser) nor kills (winner).
        return True
    return touch <= before


def abort_rule_fires(
    trade_row: Mapping[str, Any], *, abort_r: float, progress_floor_r: float
) -> bool:
    """Coarse evaluation: MAE reached -abort_r before progress_floor was touched."""

    mae = as_float(trade_row.get("mae_r"))
    if mae is None or mae > -abort_r:
        return False
    mae_time = _parse_time(trade_row.get("mae_time_utc"))
    return not _progress_reached_before(
        trade_row, threshold_r=progress_floor_r, before=mae_time
    )


def _segment_key(candidate_row: Mapping[str, Any] | None, symbol: str) -> dict[str, Any]:
    asset_class = ASSET_CLASS_BY_SYMBOL.get(symbol)
    if candidate_row is None:
        return {"asset_class": asset_class, "origin_family": None, "session_bucket": None}
    return {
        "asset_class": asset_class,
        "origin_family": candidate_row.get("origin_family")
        or candidate_row.get("candidate_origin_family"),
        "session_bucket": candidate_row.get("session_bucket") or candidate_row.get("session"),
    }


def _quantiles(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "median": None, "p75": None, "sum": 0.0, "n": 0}
    ordered = sorted(values)
    return {
        "mean": round(statistics.fmean(values), 8),
        "median": round(statistics.median(values), 8),
        "p75": round(ordered[min(len(ordered) - 1, int(0.75 * len(ordered)))], 8),
        "sum": round(sum(values), 8),
        "n": len(values),
    }


def build_headroom_report(route_dirs: Iterable[Path | str]) -> dict[str, Any]:
    ledger_sets, discovery_notes = discover_partition_ledgers(route_dirs)

    trading_days: set[str] = set()
    winners: list[dict[str, Any]] = []
    losers: list[dict[str, Any]] = []
    harvest_deltas: list[float] = []
    avoidability_counts: dict[str, int] = {}
    segment_rows: dict[str, dict[str, Any]] = {}

    def segment_bucket(seg: Mapping[str, Any]) -> dict[str, Any]:
        seg_id = (
            f"{seg.get('asset_class') or 'unknown'}"
            f"|{seg.get('origin_family') or 'unknown'}"
            f"|{seg.get('session_bucket') or 'unknown'}"
        )
        bucket = segment_rows.setdefault(
            seg_id,
            {
                "segment_id": seg_id,
                **seg,
                "winner_giveback_r": [],
                "harvest_delta_r": [],
                "loser_final_r": [],
                "trading_days": set(),
            },
        )
        return bucket

    for ledger_set in ledger_sets:
        candidate_by_id = {
            str(r.get("candidate_id")): r for r in read_jsonl(ledger_set.paths["candidate"])
        }
        trade_by_id = {
            str(r.get("candidate_id")): r
            for r in (read_jsonl(ledger_set.paths["trade"]) if "trade" in ledger_set.paths else [])
        }
        winner_rows = (
            read_jsonl(ledger_set.paths["winner"]) if "winner" in ledger_set.paths else []
        )
        loser_rows = (
            read_jsonl(ledger_set.paths["loser"]) if "loser" in ledger_set.paths else []
        )
        exit_rows = read_jsonl(ledger_set.paths["exit"]) if "exit" in ledger_set.paths else []

        for row in winner_rows + loser_rows:
            day = str(row.get("trading_day") or "")
            if day:
                trading_days.add(day)

        for row in winner_rows:
            candidate_id = str(row.get("candidate_id") or "")
            trade_row = trade_by_id.get(candidate_id) or {}
            seg = _segment_key(candidate_by_id.get(candidate_id), str(row.get("symbol") or ""))
            merged = {**row, "milestones": trade_row.get("milestones")}
            winners.append({**merged, "_segment": seg})
            giveback = as_float(row.get("giveback_r"))
            bucket = segment_bucket(seg)
            bucket["trading_days"].add(str(row.get("trading_day") or ""))
            if giveback is not None:
                bucket["winner_giveback_r"].append(giveback)

        for row in loser_rows:
            candidate_id = str(row.get("candidate_id") or "")
            trade_row = trade_by_id.get(candidate_id) or {}
            seg = _segment_key(candidate_by_id.get(candidate_id), str(row.get("symbol") or ""))
            merged = {**row, "milestones": trade_row.get("milestones")}
            losers.append({**merged, "_segment": seg})
            avoidability = str(row.get("avoidability") or "unclassified")
            avoidability_counts[avoidability] = avoidability_counts.get(avoidability, 0) + 1
            bucket = segment_bucket(seg)
            bucket["trading_days"].add(str(row.get("trading_day") or ""))
            final_r = as_float(row.get("final_r"))
            if final_r is not None:
                bucket["loser_final_r"].append(final_r)

        for row in exit_rows:
            actual = as_float(row.get("final_r"))
            counterfactual = as_float(row.get("counterfactual_final_r"))
            if actual is None or counterfactual is None:
                continue
            if row.get("counterfactual_path_scored") is not True:
                continue
            delta = counterfactual - actual
            harvest_deltas.append(delta)
            candidate_id = str(row.get("candidate_id") or "")
            seg = _segment_key(candidate_by_id.get(candidate_id), str(row.get("symbol") or ""))
            segment_bucket(seg)["harvest_delta_r"].append(delta)

    # Abort-rule grid (global + per segment).
    abort_grid: list[dict[str, Any]] = []
    for abort_r in ABORT_THRESHOLDS_R:
        for progress_floor in PROGRESS_FLOORS_R:
            fired_losers = [
                row
                for row in losers
                if abort_rule_fires(row, abort_r=abort_r, progress_floor_r=progress_floor)
            ]
            killed_winners = [
                row
                for row in winners
                if abort_rule_fires(row, abort_r=abort_r, progress_floor_r=progress_floor)
            ]
            saved = sum(
                max(0.0, abs(as_float(row.get("final_r")) or 0.0) - abort_r)
                for row in fired_losers
            )
            cost = sum(
                max(0.0, (as_float(row.get("final_r")) or 0.0) + abort_r)
                for row in killed_winners
            )
            abort_grid.append(
                {
                    "abort_r": abort_r,
                    "progress_floor_r": progress_floor,
                    "losers_fired": len(fired_losers),
                    "winners_killed": len(killed_winners),
                    "saved_r_upper_bound": round(saved, 8),
                    "killed_winner_cost_r": round(cost, 8),
                    "net_headroom_r": round(saved - cost, 8),
                }
            )
    best_abort = max(abort_grid, key=lambda row: row["net_headroom_r"]) if abort_grid else None

    n_days = max(1, len(trading_days))
    winner_giveback_all = [
        g for row in winners if (g := as_float(row.get("giveback_r"))) is not None
    ]
    harvest_stats = _quantiles(harvest_deltas)
    positive_harvest_sum = round(sum(d for d in harvest_deltas if d > 0), 8)

    families: dict[str, dict[str, Any]] = {}
    for bucket in segment_rows.values():
        family = str(bucket.get("asset_class") or "unknown")
        fam = families.setdefault(
            family,
            {
                "asset_class": family,
                "winner_giveback_r": [],
                "harvest_delta_r": [],
                "loser_count": 0,
                "trading_days": set(),
            },
        )
        fam["winner_giveback_r"].extend(bucket["winner_giveback_r"])
        fam["harvest_delta_r"].extend(bucket["harvest_delta_r"])
        fam["loser_count"] += len(bucket["loser_final_r"])
        fam["trading_days"] |= bucket["trading_days"]

    family_rows = []
    for family, fam in sorted(families.items()):
        fam_days = max(1, len(fam["trading_days"]))
        giveback_sum = sum(fam["winner_giveback_r"])
        harvest_pos = sum(d for d in fam["harvest_delta_r"] if d > 0)
        headroom_per_day = (giveback_sum + harvest_pos) / fam_days
        family_rows.append(
            {
                "asset_class": family,
                "trading_days": fam_days,
                "winner_giveback": _quantiles(fam["winner_giveback_r"]),
                "harvest_positive_delta_sum_r": round(harvest_pos, 8),
                "loser_count": fam["loser_count"],
                "headroom_r_per_day": round(headroom_per_day, 8),
                "tournament_go": headroom_per_day >= GO_THRESHOLD_R_PER_DAY,
            }
        )

    segment_summaries = []
    for bucket in sorted(segment_rows.values(), key=lambda b: b["segment_id"]):
        segment_summaries.append(
            {
                "segment_id": bucket["segment_id"],
                "asset_class": bucket.get("asset_class"),
                "origin_family": bucket.get("origin_family"),
                "session_bucket": bucket.get("session_bucket"),
                "trading_days": len(bucket["trading_days"]),
                "winner_giveback": _quantiles(bucket["winner_giveback_r"]),
                "harvest_delta": _quantiles(bucket["harvest_delta_r"]),
                "loser_count": len(bucket["loser_final_r"]),
            }
        )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": METHOD,
        "go_threshold_r_per_day": GO_THRESHOLD_R_PER_DAY,
        "trading_days_covered": sorted(trading_days),
        "n_trading_days": len(trading_days),
        "winners": len(winners),
        "losers": len(losers),
        "winner_giveback_global": _quantiles(winner_giveback_all),
        "harvest_counterfactual_global": {
            **harvest_stats,
            "positive_delta_sum_r": positive_harvest_sum,
        },
        "loser_avoidability_counts": dict(sorted(avoidability_counts.items())),
        "abort_rule_grid": abort_grid,
        "best_abort_rule": best_abort,
        "global_headroom_r_per_day": round(
            (sum(winner_giveback_all) + positive_harvest_sum
             + (best_abort["net_headroom_r"] if best_abort else 0.0)) / n_days,
            8,
        ),
        "family_go_no_go": family_rows,
        "segments": segment_summaries,
        "discovery_notes": discovery_notes,
        "report_hash_sha256": None,
        **BOUNDARY,
    }
    report["report_hash_sha256"] = stable_sha256(
        {k: v for k, v in report.items() if k not in ("generated_at_utc", "report_hash_sha256")}
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-dir", action="append", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    report = build_headroom_report([Path(p) for p in args.route_dir])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, sort_keys=True, default=str))
    compact = {
        k: report[k]
        for k in (
            "n_trading_days",
            "winners",
            "losers",
            "winner_giveback_global",
            "best_abort_rule",
            "global_headroom_r_per_day",
        )
    }
    compact["family_go"] = {
        row["asset_class"]: row["tournament_go"] for row in report["family_go_no_go"]
    }
    print(json.dumps(compact, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

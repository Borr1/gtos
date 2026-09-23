#!/usr/bin/env python3
"""Measure Wave-21 cost repairs on the fixed AQ trade substrate.

This is a deterministic component audit, not a strategy replay or a promotion result. It
uses AQ's stored trade geometry/gross rows and refuses every trade lacking one of the new
source-bound inputs. No broker, network, live process, config or token is touched.
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path


def _repo() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "src" / "costs").is_dir():
            return parent
    raise RuntimeError("repository root not found")


REPO = _repo()
sys.path.insert(0, str(REPO))

from src.costs import (  # noqa: E402
    CostTruthError,
    commission_usd_per_lot,
    component_sum_r,
    cost_r,
    load_broker_true_costs,
)
from src.costs.model import swap_price_drag_per_night  # noqa: E402
from src.costs.slippage_model import (  # noqa: E402
    SlippageModelError,
    load_slippage_model,
)
from src.costs.spread_model import SpreadModelError, load_spread_model  # noqa: E402

HERE = Path(__file__).resolve().parent
TRADES = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/"
    "AQ_ESTATE_TRADES_V2.json.gz"
)
FX = HERE / "HISTORICAL_FX_D1_V1.json.gz"
SLIPPAGE = HERE / "SLIPPAGE_PRICE_V1.json"
SYMBOL_AUTHORITY = REPO / "src/costs/SYMBOL_AUTHORITY_V1.json"
INPUT_MANIFEST = HERE / "COST_INPUTS_MANIFEST_V1.json"
OUT = HERE / "COST_TRUTH_CLOSURE_V1.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _summary(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "mean": None, "sum": 0.0}
    return {
        "n": len(values),
        "mean": statistics.fmean(values),
        "sum": math.fsum(values),
    }


def _nth_sunday(year: int, month: int, n: int) -> dt.date:
    day = dt.date(year, month, 1)
    day += dt.timedelta(days=(6 - day.weekday()) % 7)
    return day + dt.timedelta(weeks=n - 1)


def _post_2007_offset_hours(instant: dt.datetime) -> int:
    """The defective post-2007 US calendar, applied to every year as comparator."""
    start_day = _nth_sunday(instant.year, 3, 2)
    end_day = _nth_sunday(instant.year, 11, 1)
    start = dt.datetime(
        start_day.year, start_day.month, start_day.day, 7, tzinfo=dt.timezone.utc
    )
    end = dt.datetime(
        end_day.year, end_day.month, end_day.day, 6, tzinfo=dt.timezone.utc
    )
    return 3 if start <= instant < end else 2


def _old_rule_rollover_nights(
    entry: dt.datetime, holding_hours: float, triple_weekday: int | None
) -> float:
    start = (entry + dt.timedelta(hours=_post_2007_offset_hours(entry))).replace(
        tzinfo=None
    )
    exit_utc = entry + dt.timedelta(hours=holding_hours)
    end = (exit_utc + dt.timedelta(hours=_post_2007_offset_hours(exit_utc))).replace(
        tzinfo=None
    )
    nights = 0.0
    day = (start + dt.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    while day <= end:
        dow = (day.weekday() + 1) % 7
        if dow in (0, 6):
            weight = 0.0
        elif triple_weekday is not None and dow == int(triple_weekday):
            weight = 3.0
        else:
            weight = 1.0
        nights += weight
        day += dt.timedelta(days=1)
    return nights


def main() -> int:
    estate = json.load(gzip.open(TRADES, "rt"))
    truth = load_broker_true_costs()
    spread_model = load_spread_model()
    slippage_model = load_slippage_model()
    total_rows = sum(len(rows) for rows in estate["trades"].values())

    priced: list[dict] = []
    missing_reasons: collections.Counter[str] = collections.Counter()
    missing_symbols: collections.Counter[str] = collections.Counter()
    missing_sleeves: collections.Counter[str] = collections.Counter()
    schedule_all = 0
    schedule_strict_refused = 0

    for sleeve, rows in estate["trades"].items():
        for row in rows:
            entry = dt.datetime.fromisoformat(row["entry_utc"])
            exit_ = dt.datetime.fromisoformat(row["exit_utc"])
            holding = (exit_ - entry).total_seconds() / 3600.0
            side = "LONG" if int(row["direction"]) > 0 else "SHORT"
            try:
                spread_est = spread_model.estimate(
                    row["symbol"], "FTMO", entry, band="mid"
                )
                if spread_est.era_class == "SCHEDULE":
                    schedule_all += 1
                    try:
                        spread_model.estimate(
                            row["symbol"],
                            "FTMO",
                            entry,
                            band="mid",
                            require_decidable=True,
                        )
                    except SpreadModelError:
                        schedule_strict_refused += 1
            except SpreadModelError:
                pass

            try:
                breakdown = cost_r(
                    row["symbol"],
                    "FTMO",
                    holding,
                    sl_distance_price=float(row["sl_distance_price"]),
                    entry_price=float(row["entry_price"]),
                    side=side,
                    entry_utc=entry,
                    spread_band="mid",
                    costs=truth,
                )
            except CostTruthError as exc:
                reason = str(exc)
                missing_reasons[reason] += 1
                missing_symbols[row["symbol"]] += 1
                missing_sleeves[sleeve] += 1
                continue

            _resolved, rec = truth.resolve_instrument("FTMO", row["symbol"])
            stop = float(row["sl_distance_price"])
            old_slippage = float(rec["slippage"]["value_r"])
            old_commission = commission_usd_per_lot(
                rec, float(row["entry_price"])
            )[0] / (stop * float(rec["usd_per_price_unit_per_lot"]))
            old_total = component_sum_r(
                breakdown.spread_r.value,
                old_slippage,
                breakdown.swap_r.value,
                old_commission,
            )

            # Isolate the trading-bar-hours -> wall-clock repair with every other new
            # cost behavior held fixed.
            old_holding = float(row["hold_hours"])
            old_hold_breakdown = cost_r(
                row["symbol"],
                "FTMO",
                old_holding,
                sl_distance_price=stop,
                entry_price=float(row["entry_price"]),
                side=side,
                entry_utc=entry,
                spread_band="mid",
                costs=truth,
            )

            pre2007_dst_delta = None
            if entry.year < 2007:
                spec = rec.get("spec") or {}
                old_nights = _old_rule_rollover_nights(
                    entry, holding, spec.get("swap_rollover3days")
                )
                drag, _ = swap_price_drag_per_night(
                    rec, side, float(row["entry_price"])
                )
                pre2007_dst_delta = (
                    breakdown.detail["swap"]["nights_charged"] - old_nights
                ) * drag / stop

            gross = float(row["r_gross"])
            priced.append(
                {
                    "sleeve": sleeve,
                    "year": entry.year,
                    "new_cost": breakdown.total_r.value,
                    "old_snapshot_fx_constant_r_slippage_cost": old_total,
                    "new_net": gross - breakdown.total_r.value,
                    "old_net": gross - old_total,
                    "slippage_delta": breakdown.slippage_r.value - old_slippage,
                    "commission_fx_delta": breakdown.commission_r.value - old_commission,
                    "holding_wall_clock_delta": (
                        breakdown.total_r.value - old_hold_breakdown.total_r.value
                    ),
                    "pre2007_dst_delta": pre2007_dst_delta,
                    "schedule": breakdown.detail["spread"].get("era_class") == "SCHEDULE",
                }
            )

    def vals(field: str) -> list[float]:
        return [float(row[field]) for row in priced if row[field] is not None]

    hold_delta = vals("holding_wall_clock_delta")
    pre2007_delta = vals("pre2007_dst_delta")
    new_old = [
        row["new_cost"] - row["old_snapshot_fx_constant_r_slippage_cost"]
        for row in priced
    ]
    by_sleeve: dict[str, list[float]] = collections.defaultdict(list)
    for row in priced:
        by_sleeve[row["sleeve"]].append(row["holding_wall_clock_delta"])

    fx_doc = json.load(gzip.open(FX, "rt"))
    output = {
        "schema": "gtos.phase21.cost_truth_closure.v1",
        "result_use_status": (
            "DETERMINISTIC_COMPONENT_AUDIT_ONLY_NOT_A_STRATEGY_REPLAY_RESULT_"
            "NOT_ACTIVATION_AUTHORITY"
        ),
        "population": {
            "path": str(TRADES.relative_to(REPO)),
            "sha256": _sha256(TRADES),
            "rows": total_rows,
            "account": "FTMO",
            "spread_band": "mid",
            "gross_source": "cached AQ rows; gross not recomputed",
        },
        "authority_artifacts": {
            "cost_inputs_manifest": {
                "path": str(INPUT_MANIFEST.relative_to(REPO)),
                "sha256": _sha256(INPUT_MANIFEST),
                "schema": json.loads(INPUT_MANIFEST.read_text())["schema"],
                "runtime_enforced": True,
            },
            "historical_fx": {
                "path": str(FX.relative_to(REPO)),
                "sha256": _sha256(FX),
                "schema": fx_doc["schema"],
            },
            "slippage": {
                "path": str(SLIPPAGE.relative_to(REPO)),
                "sha256": _sha256(SLIPPAGE),
            },
            "symbol_authority": {
                "path": str(SYMBOL_AUTHORITY.relative_to(REPO)),
                "sha256": _sha256(SYMBOL_AUTHORITY),
            },
        },
        "coverage": {
            "priced_rows": len(priced),
            "priced_fraction": len(priced) / total_rows,
            "not_evaluable_rows": total_rows - len(priced),
            "not_evaluable_by_symbol": dict(missing_symbols.most_common()),
            "not_evaluable_by_sleeve": dict(missing_sleeves.most_common()),
            "not_evaluable_reasons": dict(missing_reasons.most_common()),
        },
        "component_deltas_on_priceable_intersection": {
            "new_cost_r": _summary(vals("new_cost")),
            "snapshot_fx_constant_r_slippage_cost_r": _summary(
                vals("old_snapshot_fx_constant_r_slippage_cost")
            ),
            "new_minus_comparator_total_r": _summary(new_old),
            "slippage_price_geometry_delta_r": _summary(vals("slippage_delta")),
            "historical_fx_commission_delta_r": _summary(vals("commission_fx_delta")),
            "new_net_r": _summary(vals("new_net")),
            "comparator_net_r": _summary(vals("old_net")),
            "trade_net_sign_flips": sum(
                (row["new_net"] > 0) != (row["old_net"] > 0) for row in priced
            ),
            "interpretation": (
                "same cached gross and same corrected wall-clock holding; this delta "
                "isolates historical FX for cash-per-lot commission plus price-domain "
                "slippage on rows where every consumed new input exists"
            ),
        },
        "holding_clock_repair": {
            "delta_r": _summary(hold_delta),
            "rows_changed": sum(delta != 0 for delta in hold_delta),
            "top_sleeves_by_mean_delta_r": [
                {
                    "sleeve": sleeve,
                    "n": len(ds),
                    "mean_delta_r": statistics.fmean(ds),
                    "sum_delta_r": math.fsum(ds),
                }
                for sleeve, ds in sorted(
                    by_sleeve.items(),
                    key=lambda item: statistics.fmean(item[1]),
                    reverse=True,
                )[:10]
            ],
        },
        "spread_era_decidability": {
            "schedule_rows": schedule_all,
            "schedule_rows_strictly_refused": schedule_strict_refused,
            "schedule_rows_in_priceable_intersection": sum(
                bool(row["schedule"]) for row in priced
            ),
            "runtime_class": "MODELLED",
        },
        "pre2007_clock_repair": {
            "priceable_rows_before_2007": len(pre2007_delta),
            "rows_with_swap_r_delta_vs_wrong_post2007_rule": sum(
                delta != 0 for delta in pre2007_delta
            ),
            "delta_r": _summary(pre2007_delta),
            "boundary_note": "registered US broker calendar refuses dates before 1987",
        },
        "arithmetic_contract": (
            "complete rows use exact left-to-right spread_r + expected_slippage_r + "
            "swap_cost_r + commission_r; incomplete rows are NOT_EVALUABLE"
        ),
        "post_lifecycle_cost_contract": {
            "schema": "gtos.costs.post_lifecycle_component_cost.v1",
            "cost_role": "post_lifecycle_component_cost",
            "predecessor_role": "pretrade_expected_cost",
            "holding_source_status": "actual_simulated_entry_exit_elapsed",
            "pretrade_components_reused": [],
            "broker_realized_status": "NOT_EVALUABLE_NO_BROKER_DEAL_COMPONENTS",
            "final_economics_rule": (
                "only a COMPLETE post-lifecycle packet may be numeric; missing source, "
                "component, exact sum, actual elapsed hold or quote geometry is "
                "NOT_EVALUABLE and cannot fall back to the pretrade estimate"
            ),
        },
        "capture_requirements": [
            {
                "gap": "exact price-domain slippage",
                "need": (
                    "broker-history-reconciled requested and executed entry prices plus "
                    "executed stop, exact account/profile symbol and fill UTC for each "
                    "missing account-symbol cell; current AQ shortfall is enumerated above"
                ),
            },
            {
                "gap": "redacted_account oils",
                "need": (
                    "reconciled entry slippage for exact profile mappings "
                    "USOIL_cash->USOUSD and UKOIL_cash->UKOUSD; commission and spread "
                    "are present but a complete total is not"
                ),
            },
            {
                "gap": "historical FX outside captured D1 extent",
                "need": (
                    "for non-USD-profit rows whose cash-per-lot commission consumes the "
                    "conversion: hash-bound D1 or finer USD crosses with broker-wall "
                    "timebase; use only a bar whose completion UTC is strictly before "
                    "entry UTC. Zero and notional-bp R do not consume this input"
                ),
            },
            {
                "gap": "spread SCHEDULE eras",
                "need": (
                    "decision-time or era/account/profile-symbol spread observations; a "
                    "constant schedule row cannot establish dispersion or decidability"
                ),
            },
            {
                "gap": "quote-geometry exactly-once accounting",
                "need": (
                    "resolvable JSONL source plus actual SHA-256, physical row index, trade "
                    "id, account, exact profile symbol, entry UTC, side, bid, ask, fill, "
                    "stop, gross_basis=fill_anchored_quote_geometry and "
                    "gross_includes_spread=true"
                ),
            },
            {
                "gap": "historical swap schedule",
                "need": (
                    "date-indexed account/profile-symbol swap_long, swap_short, mode and "
                    "triple-day schedule; Wave 21 fixes elapsed rollovers but does not "
                    "fabricate a historical curve from the 2026 snapshot"
                ),
            },
            {
                "gap": "broker clock before 1987",
                "need": (
                    "source-backed server calendar/offset evidence for the requested era; "
                    "runtime currently refuses"
                ),
            },
        ],
    }
    OUT.write_text(json.dumps(output, indent=1, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUT.relative_to(REPO)),
        "priced": len(priced),
        "not_evaluable": total_rows - len(priced),
        "holding_delta_sum_r": output["holding_clock_repair"]["delta_r"]["sum"],
        "new_minus_comparator_sum_r": output[
            "component_deltas_on_priceable_intersection"
        ]["new_minus_comparator_total_r"]["sum"],
    }, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

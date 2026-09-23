#!/usr/bin/env python3
"""Session AW-3 — the mine's one portable finding, taken out of window (B1770-B1785).

    python3 docs/audits/fable5-vision-audit-20260725/phase12/receipts/aw_archive_gate.py \
        --stage census   # how much of the ESTATE would the sealed B7.5 cost gate refuse?
    ... --stage gate     # control vs the two sealed-limit filters, at the ratified rule
    ... --stage all

WHY THIS ARM AND NOT ANOTHER
----------------------------
AW-2's funnel returned **zero survivors of 212 declared cells**, so the commission's literal
input to AW-3 — "restate each surviving discriminator" — is an empty set, and this file says
so rather than manufacturing one. What it runs instead is the mine's single largest and most
portable measurement, declared as a new look and billed as one.

That measurement is the **cost decomposition**. Of the January pool's −0.947 R/row, cost is
−0.638 (spread −0.564), and the tail is extreme: **4,701 rows of 28,519 (16.5 %) carry a
round-trip cost above 1 R and 49.6 % of the pool's entire loss**, with a maximum of
**18.856 R**. `spread_r` is `spread_price / sl_distance_price`, so a cost above 1 R means the
generator proposed a stop NARROWER THAN THE SPREAD.

The B7.5 decision contract already had a gate for exactly that, and the January ledger prints
its constants verbatim in the block reason of the very first rejected row:

    broker_cost_packet_refused:spread_r_exceeds_selected_cell_limit:0.162063>0.100000
                              |total_cost_r_exceeds_limit:0.182063>0.150000

**spread_r ≤ 0.10 and total cost_r ≤ 0.15.** Those two numbers are pre-registered in a sealed
2026-07-16 contract, not chosen by this session from this session's data — which is the only
reason a threshold arm is admissible at all here. What AW contributes is the *axis*, and the
axis was chosen after 212 looks, so the bill carries all of them.

TWO QUESTIONS, AND THE FIRST NEEDS NO GATE
-------------------------------------------
1. **Census.** How many of the estate's own 22,354 archive trades would that sealed cost gate
   refuse? This is a fidelity measurement about the live book, not a hypothesis: the broad
   stack and the W7 book share instruments and an archive, and if armed sleeves are carrying
   trades the broad stack's own contract would have refused, that is worth knowing whether or
   not any verdict moves.
2. **Gate.** Does applying either limit improve anything at the ratified rule? RECORDED
   population, `B_balanced`, band published alongside, chronological folds — the standard
   every wave-11/12 admission-grade claim is held to.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import random
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
for phase in ("phase7", "phase8", "phase9", "phase10", "phase11"):
    sys.path.insert(0, str(REPO / f"docs/audits/fable5-vision-audit-20260725/{phase}/receipts"))

import ad_exit_sweep as AD  # noqa: E402

from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as EP  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import price_trades  # noqa: E402
from src.costs.model import load_broker_true_costs  # noqa: E402

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
ESTATE = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
FAMILY_V8 = HERE / "CANDIDATE_FAMILY_V8.json"
FAMILY_V9 = HERE / "CANDIDATE_FAMILY_V9.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
CENSUS_OUT = HERE / "AW_ESTATE_COST_CENSUS_V1.json"
GATE_OUT = HERE / "AW_ARCHIVE_GATE_V1.json"

SERVER = "FTMO-Server3"
ACCOUNT = "FTMO"
BANDS = (None, "low", "mid", "high")
POPULATION = "RECORDED"
OPTION = "B_balanced"

#: From the SEALED B7.5 decision contract, printed verbatim in the January ledger's own
#: `broker_pretrade_cost_executable_block_reason`. Not fitted here, and that is the point.
SEALED_SPREAD_R_LIMIT = 0.10
SEALED_TOTAL_COST_R_LIMIT = 0.15

#: Arms. The two sealed-limit filters are the hypothesis; the rest are the controls that
#: make it a measurement rather than arithmetic.
#:
#: A cost filter MECHANICALLY raises post-cost mean R by removing expensive trades, so an
#: improvement on its own says nothing. Two controls separate the two explanations, and
#: AR's standard (a sizing/selection change is judged against blind constants, never against
#: its own headline) is why they are here:
#:
#:   `random_matched_sX`  drops the SAME NUMBER of trades per sleeve, chosen at random. If
#:                        the filter's gain survives against this, the gain is not "fewer
#:                        trades" and not "a smaller sample looks better".
#:   `inverse_cheapest`   drops the same number, but the CHEAPEST instead of the dearest.
#:                        This is the sharp one: if dropping the dearest helps and dropping
#:                        the cheapest hurts, the cost axis carries real information about
#:                        the trade, not just about the bill.
N_RANDOM_SEEDS = 5

ARMS: dict[str, object] = {
    "control": None,
    "spread_r_le_0p10": ("spread_r", SEALED_SPREAD_R_LIMIT),
    "total_cost_r_le_0p15": ("total", SEALED_TOTAL_COST_R_LIMIT),
    "inverse_cheapest_matched": ("inverse", SEALED_SPREAD_R_LIMIT),
    **{f"random_matched_s{i}": ("random", i) for i in range(N_RANDOM_SEEDS)},
}


def _sha(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _write(path: Path, payload: dict) -> None:
    payload = dict(payload)
    payload["self_sha256"] = _sha({k: v for k, v in payload.items() if k != "self_sha256"})
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(REPO)}  ({path.stat().st_size:,} bytes)")


def load_estate() -> dict:
    doc = json.loads(gzip.open(ESTATE, "rt").read())
    return {s: rows for s, rows in doc["trades"].items() if rows}


def priced_by_band(recs: dict, costs, band) -> dict:
    """`{sleeve: [(TradeRecord, spread_r, total_r, status)]}` at one band, gate-native."""

    o = OPTIONS[OPTION]
    spec = o.with_(spec_id=f"{o.spec_id}_aw_price", spread_band=band)
    out: dict[str, list] = collections.defaultdict(list)
    for sleeve, trades in recs.items():
        priced, _ = price_trades(trades, spec, costs=costs)
        for p in priced:
            comp = p.components or {}
            out[sleeve].append((
                p.trade,
                comp.get("spread_r"),
                p.cost_r,
                p.status,
            ))
    return out


def stage_census(recs: dict, costs) -> dict:
    per_band = {}
    for band in BANDS:
        rows = priced_by_band(recs, costs, band)
        per_sleeve = {}
        tot = over_spread = over_total = priced_n = 0
        for sleeve, items in sorted(rows.items()):
            n = len(items)
            pr = [it for it in items if it[3] == "priced" and it[1] is not None]
            os_ = sum(1 for it in pr if it[1] > SEALED_SPREAD_R_LIMIT)
            ot = sum(1 for it in pr if (it[2] or 0) > SEALED_TOTAL_COST_R_LIMIT)
            per_sleeve[sleeve] = {
                "n_trades": n, "n_priced": len(pr),
                "n_over_spread_limit": os_, "n_over_total_limit": ot,
                "frac_over_spread_limit": round(os_ / len(pr), 6) if pr else None,
                "frac_over_total_limit": round(ot / len(pr), 6) if pr else None,
                "median_spread_r": (
                    round(float(sorted(it[1] for it in pr)[len(pr) // 2]), 6) if pr else None
                ),
                "max_spread_r": round(max((it[1] for it in pr), default=0.0), 6) if pr else None,
                "mean_r_gross_over_spread_limit": (
                    round(sum(it[0].r_gross for it in pr if it[1] > SEALED_SPREAD_R_LIMIT)
                          / max(1, os_), 6) if os_ else None
                ),
                "mean_r_gross_within_spread_limit": (
                    round(sum(it[0].r_gross for it in pr if it[1] <= SEALED_SPREAD_R_LIMIT)
                          / max(1, len(pr) - os_), 6) if len(pr) - os_ else None
                ),
            }
            tot += n
            priced_n += len(pr)
            over_spread += os_
            over_total += ot
        per_band[band or "flat_37_day_snapshot"] = {
            "n_trades": tot, "n_priced": priced_n,
            "n_over_spread_limit": over_spread, "n_over_total_limit": over_total,
            "frac_over_spread_limit": round(over_spread / priced_n, 6) if priced_n else None,
            "frac_over_total_limit": round(over_total / priced_n, 6) if priced_n else None,
            "by_sleeve": per_sleeve,
        }
    return {
        "schema": "gtos.aw.estate_cost_census.v1",
        "estate": str(ESTATE.relative_to(REPO)),
        "costs": str(COSTS.relative_to(REPO)),
        "account": ACCOUNT, "server": SERVER,
        "sealed_spread_r_limit": SEALED_SPREAD_R_LIMIT,
        "sealed_total_cost_r_limit": SEALED_TOTAL_COST_R_LIMIT,
        "limits_source": (
            "B7_5 decision contract, printed verbatim in the January MISSED_OPPORTUNITY "
            "ledger's broker_pretrade_cost_executable_block_reason"
        ),
        # FOUR since 2026-07-30 ~14:57 UTC: `fx_jpy` was pulled from both live books on
        # AV's measurement (`phase8/receipts/FXJPY_PULL_20260730.md`). It is kept in the
        # census as `recently_pulled` because this session's own filter arm makes fx_jpy
        # WORSE, which is a fact about the pulled sleeve worth keeping visible.
        "armed_sleeves": ["crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert"],
        "recently_pulled_sleeves": ["fx_jpy"],
        "by_band": per_band,
    }


def stage_family_v9() -> dict:
    """V9 = V8 plus one member per AW-3 arm. The arms are looks; the ratchet bills them."""

    v8 = json.loads(FAMILY_V8.read_text())
    families = json.loads(json.dumps(v8["families"]))
    mine = families["B7_5_SEPARABILITY_MINE_V1"]
    have = {m["name"] for m in mine["members"]}
    added = []
    for arm in ARMS:
        name = f"aw3_archive::{arm}"
        if name in have:
            continue
        added.append({
            "name": name, "source": "AW_ARCHIVE_GATE_V1.json:arms",
            "basis": (
                "AW-3 out-of-window arm over the estate archive at the ratified rule "
                "(RECORDED / B_balanced / bands). The two sealed-limit arms are the "
                "hypothesis; `inverse_cheapest_matched` and the five `random_matched` "
                "seeds are its controls, and a control is a look like any other."
            ),
            "declared_at": "2026-07-30", "status": "declared", "look_taken": True,
        })
    mine["members"] = list(mine["members"]) + added
    mine["high_water_size"] = len(mine["members"])
    mine["high_water_looks"] = sum(1 for m in mine["members"] if m["look_taken"])
    mine["history"] = list(mine["history"]) + [{
        "at": "2026-07-30", "by": "Session AW (B1750-B1799)",
        "what": (
            "AW-3's archive arms declared. The axis they test — cost-to-stop — was chosen "
            "after the mine's 477 looks, so a rule stated on it is corrected against all "
            "of them plus these."
        ),
        "members_added": [m["name"] for m in added],
    }]
    out = dict(v8)
    out["families"] = families
    out["supersedes"] = str(FAMILY_V8.relative_to(REPO))
    out["superseded_because"] = "AW-3's out-of-window arms and their controls are further looks."
    out["generated_by"] = "aw_archive_gate.py --stage family"
    out.pop("self_sha256", None)
    return out


def stage_gate(recs: dict, costs, ledger: TrialLedger | None) -> dict:
    famv8 = CF.load_candidate_family(FAMILY_V9)
    allow = AD.allowlist()
    results = {}
    for band in BANDS:
        rows = priced_by_band(recs, costs, band)
        for arm, rule in ARMS.items():
            if rule is None:
                filtered = {s: [it[0] for it in items] for s, items in rows.items()}
                dropped = 0
            else:
                key, limit = rule
                filtered, dropped = {}, 0
                for s, items in rows.items():
                    if key in ("spread_r", "total"):
                        keep = []
                        for trade, spread_r, total_r, status in items:
                            value = spread_r if key == "spread_r" else total_r
                            # An UNPRICED trade cannot be shown to violate a cost limit, so
                            # it is kept and the gate's own coverage policy handles it.
                            # Dropping it here would silently turn "we could not price
                            # this" into "this is too expensive", which is the F-class
                            # error this estate keeps finding in its own artifacts.
                            if status == "priced" and value is not None and value > limit:
                                dropped += 1
                                continue
                            keep.append(trade)
                    else:
                        # Controls: drop the SAME COUNT the sealed spread filter drops on
                        # this sleeve, so every arm is judged at the same sample size.
                        priced = [it for it in items
                                  if it[3] == "priced" and it[1] is not None]
                        n_drop = sum(1 for it in priced if it[1] > SEALED_SPREAD_R_LIMIT)
                        if key == "inverse":
                            order = sorted(range(len(priced)), key=lambda i: priced[i][1])
                        else:
                            rng = random.Random(20260730 + int(limit) * 1000 + len(items))
                            order = list(range(len(priced)))
                            rng.shuffle(order)
                        drop_ids = {id(priced[i][0]) for i in order[:n_drop]}
                        keep = [it[0] for it in items if id(it[0]) not in drop_ids]
                        dropped += n_drop
                    if keep:
                        filtered[s] = keep
            if not filtered:
                results[f"{arm}|{band or 'flat'}"] = {"arm": arm, "band": band,
                                                      "verdicts": {}, "note": "empty"}
                continue
            o = OPTIONS[OPTION]
            spec = o.with_(spec_id=f"{o.spec_id}_aw3_{arm}",
                           sleeve_symbol_allowlist=allow, spread_band=band)
            spec = CF.with_declared_family(spec, "B7_5_SEPARABILITY_MINE_V1", loaded=famv8)
            recs2, spec, mix = EP.apply(POPULATION, dict(filtered), spec,
                                        account=ACCOUNT, band=(band or "mid"))
            t0 = time.time()
            res = run_gate(recs2, spec, costs=costs, server=SERVER, diagnose=True)
            elapsed = round(time.time() - t0, 1)
            if (res.family.get("wipeout") or {}).get("wiped_out"):
                raise SystemExit(
                    f"whole-run wipeout on {arm}/{band}: {res.family['wipeout']} — "
                    "refusing to tabulate a wall of nulls as a result (AQ B1435)")
            verdicts = {}
            for sleeve, sv in res.verdicts.items():
                verdicts[sleeve] = {
                    "verdict": sv.verdict.value, "n_trades": sv.n_trades,
                    "pooled_oos_mean_r": sv.pooled_oos_mean_r,
                    "p_raw": sv.p_raw, "q": sv.q_value,
                    "folds_positive": sv.gates.get("stability", {}).get("positive_frac"),
                    "oos_mean_r_per_trade": (sv.telemetry or {}).get(
                        "oos_mean_r_per_trade"),
                    "reasons": list(sv.reasons)[:4],
                }
            results[f"{arm}|{band or 'flat'}"] = {
                "arm": arm, "band": band or "flat_37_day_snapshot",
                "band_is_control": band is None,
                "population": POPULATION, "option": OPTION,
                "spec_sha256": spec.seal(),
                "declared_family_id": "B7_5_SEPARABILITY_MINE_V1",
                "declared_family_size": spec.declared_family_size,
                "effective_family_size":
                    res.family["multiplicity"]["effective_family_size"],
                "alpha": spec.alpha, "multiplicity": spec.multiplicity,
                "trades_dropped_by_filter": dropped,
                "population_mix": mix, "seconds": elapsed,
                "n_admit": sum(1 for v in verdicts.values() if v["verdict"] == "ADMIT"),
                "best_p_raw": min(
                    (v["p_raw"] for v in verdicts.values() if v["p_raw"] is not None),
                    default=None),
                "verdicts": verdicts,
            }
            if ledger is not None:
                for sleeve, v in verdicts.items():
                    ledger.record(
                        mechanism="aw3_sealed_cost_limit", sleeve=sleeve,
                        variant={"arm": arm, "band": band or "flat", "population": POPULATION,
                                 "option": OPTION},
                        window="full_archive", spec_sha256=spec.seal(),
                        outcome={"ADMIT": "admitted", "REJECT": "rejected",
                                 "NOT_EVALUABLE": "not_evaluable"}.get(
                                     v["verdict"], "evaluated"),
                        metric=v["pooled_oos_mean_r"], metric_name="pooled_oos_mean_r",
                        note="AW-3: sealed B7.5 cost limit applied to the estate archive")
            key = f"{arm}|{band or 'flat'}"
            print(f"  {arm:22s} band={str(band):5s} dropped={dropped:6d} "
                  f"admits={results[key]['n_admit']} ({elapsed}s)")
    return {
        "schema": "gtos.aw.archive_gate.v1",
        "what_this_is_not": (
            "This is NOT the gate of a surviving mined discriminator. AW-2's funnel returned "
            "0 survivors of 212 declared cells; this arm tests the mine's largest measured "
            "term — the cost-to-stop ratio — at limits taken from the sealed B7.5 contract, "
            "and it is billed against the mine's whole family because the AXIS was chosen "
            "after those 212 looks."
        ),
        "estate": str(ESTATE.relative_to(REPO)),
        "costs": str(COSTS.relative_to(REPO)),
        "family": str(FAMILY_V9.relative_to(REPO)),
        "family_id": "B7_5_SEPARABILITY_MINE_V1",
        "arms": {k: (None if v is None else {"field": v[0], "limit": v[1]})
                 for k, v in ARMS.items()},
        "n_random_seeds": N_RANDOM_SEEDS,
        "runs": results,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all", choices=("census", "family", "gate", "all"))
    args = ap.parse_args()
    costs = load_broker_true_costs(COSTS)
    raw = load_estate()
    recs = {s: AD.to_records(rows) for s, rows in raw.items()}
    print(f"estate: {len(recs)} sleeves, {sum(len(v) for v in recs.values()):,} trades")
    if args.stage in ("census", "all"):
        _write(CENSUS_OUT, stage_census(recs, costs))
    if args.stage in ("family", "all"):
        _write(FAMILY_V9, stage_family_v9())
    if args.stage in ("gate", "all"):
        ledger = TrialLedger(DEFAULT_TRIAL_LEDGER, session="AW")
        _write(GATE_OUT, stage_gate(recs, costs, ledger))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

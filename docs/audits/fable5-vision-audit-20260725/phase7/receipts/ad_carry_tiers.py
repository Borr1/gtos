"""Restate the survivor book's carry tiers against MEASURED holds instead of modelled ones.

    python3 docs/audits/fable5-vision-audit-20260725/phase7/receipts/ad_carry_tiers.py

WHY THIS IS THE HIGHEST-VALUE THING IN THIS LANE
------------------------------------------------
`CLAUDE.md` §4: *"What now decides OD-3 is holding time."* `SURVIVOR_BOOK_V1.json` tiers
every core sleeve UNCONDITIONAL / CARRY_CONDITIONAL / DEAD_BEFORE_COST, and the tier rule
(`scripts/recost_w7_validation.py:1062-1073`) turns on how many swap nights the sleeve pays.
Both night counts it uses are **modelled, not measured**:

    _NIGHTS  = {sleeve: _measured_nights(horizon_hours)}     # :238
    SLEEVE_MEAN_NIGHTS = mean over 168 entry hours OF A HOLD EQUAL TO THE FULL HORIZON
    SLEEVE_MAX_NIGHTS  = the worst reachable crossing count for that same full-horizon hold

So `metals_core` is charged **13.369 nights** because a 320 h hold crosses that many, and
`carry_basis` says so in the artifact: `MODELLED_HELD_TO_HORIZON`. Session N's §8.1 explains
why — no exit index survived any cache, so no realised hold existed to use instead.

**AA's archive walk supplies the realised hold.** Every one of its 22,324 trades carries
`entry_utc` and `hold_hours` off the simulated path, so the charged nights can be COUNTED
with the same `costs.model.rollover_nights` the tier rule itself uses, per trade, on the
broker's own wall clock. This script changes exactly one input — nights — and holds `gross_r`,
`true_cost_ex_swap_r` and `swap_r_per_night` at the survivor book's own values, so any tier
that moves moved because of holding time and nothing else.

THE POPULATION CAVEAT, STATED BECAUSE IT IS THE ONE REAL WEAKNESS
-----------------------------------------------------------------
The edge terms (`gross_r`, `ex`, `pn`) are measured on the W7 validation CACHES; the holds
are measured on the FULL ARCHIVE. Those are different trade populations, and no single
population carries both — that is precisely the gap Session N recorded. So this is the
sleeve's *hold distribution* from the best available source, applied to the sleeve's edge
estimate from the only available source. It is strictly better evidence than a horizon
assumption, and it is not the same thing as a single-population measurement. Every row says
which basis it used.

TWO TRIPLE-SWAP CONVENTIONS, BOTH REPORTED
------------------------------------------
The book's own model hardcodes `rollover3days_weekday=3` (Wednesday) for every sleeve
(`recost_w7_validation.py:161`). The cost artifact carries the real per-symbol weekday, and
it is **5 (Friday) for every crypto and index instrument** — measured here. The primary
restatement uses the real per-symbol weekday; the Wednesday-for-everything number is
reported beside it so the comparison against the published book is exact rather than
approximate.
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.costs.model import rollover_nights  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
BOOK = REPO / "research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
OUT = HERE / "AD_CARRY_TIERS_RESTATED_V1.json"
SERVER = "FTMO-Server3"

#: The tier rule, replicated verbatim from `recost_w7_validation.py:1062-1073` so a reader
#: can diff it. The only thing this script changes is which night counts go in.
CARRY_STRUCTURAL = {"fx_jpy"}


def tier_of(gross: float, ex: float, pn: float, mean_n: float, max_n: float,
            sleeve: str, live_nights: float | None) -> str:
    if gross - ex <= 0:
        return "DEAD_BEFORE_COST"
    if gross - ex - pn * max_n > 0:
        return "UNCONDITIONAL"
    if live_nights is not None and sleeve in CARRY_STRUCTURAL and \
            gross - ex - pn * live_nights > 0:
        return "MEASURED_LIVE_CARRY"
    if live_nights is not None and gross - ex - pn * live_nights > 0:
        return "CARRY_CONDITIONAL_LIVE_SUPPORTED"
    return "CARRY_CONDITIONAL"


def swap3(costs_doc: dict, account: str, symbol: str) -> int | None:
    try:
        return ((costs_doc["accounts"][account]["instruments"][symbol].get("spec")
                 or {}).get("swap_rollover3days"))
    except Exception:
        return None


def q(vals: list[float], f: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    return s[min(len(s) - 1, int(f * len(s)))]


def main() -> dict:
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AD")
    raw = json.load(gzip.open(AA_IN, "rt"))
    book = json.loads(BOOK.read_text())
    costs_doc = json.loads(COSTS.read_text())

    # ---- realised charged nights, per sleeve, per account, from AA's holds -------------
    nights: dict[str, dict] = {}
    for sleeve, rows in raw["trades"].items():
        if not rows:
            continue
        per_acct: dict[str, list[float]] = {"FTMO": [], "redacted_account": []}
        wed: list[float] = []
        wd_seen: collections.Counter = collections.Counter()
        for r in rows:
            entry = dt.datetime.fromisoformat(r["entry_utc"])
            hold = float(r["hold_hours"])
            for acct in ("FTMO", "redacted_account"):
                wd = swap3(costs_doc, acct, r["symbol"])
                if acct == "FTMO":
                    wd_seen[wd] += 1
                per_acct[acct].append(
                    rollover_nights(entry, hold, server=SERVER,
                                    rollover3days_weekday=wd)[0])
            wed.append(rollover_nights(entry, hold, server=SERVER,
                                       rollover3days_weekday=3)[0])
        nights[sleeve] = {
            "n_trades": len(rows),
            "swap3_weekday_seen_ftmo": {str(k): v for k, v in sorted(
                wd_seen.items(), key=lambda kv: str(kv[0]))},
            "by_account": {a: {"mean": round(statistics.fmean(v), 4),
                               "median": round(statistics.median(v), 4),
                               "p90": round(q(v, 0.90), 4),
                               "p99": round(q(v, 0.99), 4),
                               "max": round(max(v), 4),
                               "frac_zero": round(sum(1 for x in v if x == 0) / len(v), 4)}
                           for a, v in per_acct.items()},
            "wednesday_convention": {"mean": round(statistics.fmean(wed), 4),
                                     "max": round(max(wed), 4)},
            "median_hold_hours": round(statistics.median(
                [float(r["hold_hours"]) for r in rows]), 3),
            "p90_hold_hours": round(q([float(r["hold_hours"]) for r in rows], 0.90), 3),
            "max_hold_hours": round(max(float(r["hold_hours"]) for r in rows), 3),
        }

    # ---- restate every tier -------------------------------------------------------------
    out_rows: dict[str, dict] = {}
    moved: list[str] = []
    for acct in ("FTMO", "redacted_account"):
        sl_book = (book["accounts"][acct].get("sleeves") or {})
        for sleeve, rec in sorted(sl_book.items()):
            gross = rec.get("gross_r")
            ex = rec.get("true_cost_ex_swap_r")
            pn = rec.get("swap_r_per_night")
            if gross is None or ex is None or pn is None:
                continue
            meas = nights.get(sleeve)
            key = f"{acct}::{sleeve}"
            base_tier = rec.get("survivor_tier")
            if not meas:
                out_rows[key] = {
                    "account": acct, "sleeve": sleeve,
                    "published_tier": base_tier,
                    "restated_tier": None,
                    "restatable": False,
                    "reason": ("no trade in AA's archive walk — the sleeve generates nothing "
                               "(vp_euidx_pocgrav fails closed at sleeves/vp_euidx.py:70 for "
                               "want of an M1 aux feed)"),
                }
                continue
            m = meas["by_account"][acct]
            live_n = rec.get("measured_carry_nights")
            # Published tier, recomputed from the artifact's own inputs — a control. If this
            # does not reproduce `survivor_tier` the replication of the rule is wrong and
            # nothing below can be trusted.
            repro = tier_of(gross, ex, pn, rec["horizon_mean_nights"], rec["max_nights"],
                            sleeve, live_n)
            # Restated: measured nights in place of the modelled ones. `p99` stands in for
            # the "worst reachable crossing count" because the modelled `max_nights` is a
            # worst case over entry hours, not an outlier trade — using the single worst
            # trade would let one row decide a tier.
            rest = tier_of(gross, ex, pn, m["mean"], m["p99"], sleeve, live_n)
            net_meas = gross - ex - pn * m["mean"]
            net_p99 = gross - ex - pn * m["p99"]
            be_nights = ((gross - ex) / pn) if pn > 1e-12 else None
            row = {
                "account": acct, "sleeve": sleeve, "restatable": True,
                "published_tier": base_tier,
                "rule_reproduced_from_artifact_inputs": repro,
                "rule_replication_ok": repro == base_tier,
                "restated_tier": rest,
                "tier_moved": rest != base_tier,
                "inputs_held_fixed": {"gross_r": gross, "true_cost_ex_swap_r": ex,
                                      "swap_r_per_night": pn,
                                      "break_even_nights": (round(be_nights, 3)
                                                            if be_nights else None)},
                "nights_modelled": {"mean_held_to_horizon": rec["horizon_mean_nights"],
                                    "max_held_to_horizon": rec["max_nights"],
                                    "basis": rec.get("carry_basis")},
                "nights_measured": {**m, "basis": "AA_ARCHIVE_SIMULATED_PATH"},
                "nights_ratio_measured_over_modelled": round(
                    m["mean"] / rec["horizon_mean_nights"], 4)
                if rec["horizon_mean_nights"] else None,
                "net_r_at_measured_mean_nights": round(net_meas, 5),
                "net_r_at_measured_p99_nights": round(net_p99, 5),
                "net_r_at_modelled_max_nights": rec["net_r"]["n_max"],
                "carry_headroom_measured": (round(be_nights / m["mean"], 3)
                                            if be_nights and m["mean"] else None),
                "carry_headroom_published": rec.get("carry_headroom"),
                "median_hold_hours_measured": meas["median_hold_hours"],
                "horizon_hours_assumed": rec.get("horizon_hours"),
                "hold_as_frac_of_horizon": (round(meas["median_hold_hours"]
                                                  / rec["horizon_hours"], 4)
                                            if rec.get("horizon_hours") else None),
            }
            out_rows[key] = row
            if row["tier_moved"]:
                moved.append(key)
            ledger.record(
                mechanism="carry_tier_restatement", sleeve=sleeve,
                variant={"account": acct, "nights_basis": "AA_ARCHIVE_SIMULATED_PATH",
                         "changed_input": "charged_swap_nights_only"},
                window="full_archive_holds_x_cache_edge",
                outcome="evaluated", metric=net_meas,
                metric_name="net_r_per_trade_at_measured_mean_nights",
                note=f"published {base_tier} -> restated {rest}",
            )

    # ---- the tier-flip threshold: how tight a time stop UNCONDITIONALs each sleeve ------
    #  The restatement above shows the blocker is the TAIL, not the mean — the rule's
    #  UNCONDITIONAL test is `gross - ex - pn * p99_nights > 0`, and on an H4 grid the top
    #  1 % of holds still reach the 80-bar / 320 h ceiling. A time stop does almost nothing
    #  to the median trade and everything to the tail, so it is exactly the right instrument.
    #  This finds the LOOSEST time stop that flips the tier, so the ask on the sleeve's edge
    #  is as small as possible. The R cost of that cell is measured separately by
    #  `ad_exit_sweep.py`; this half only prices the carry.
    tf_min = {"M15": 15, "H4": 240, "D1": 1440}
    tf_of = raw["timeframe_by_sleeve"]
    flips: dict[str, dict] = {}
    for key, r in out_rows.items():
        if not r.get("restatable") or r["restated_tier"] == "UNCONDITIONAL":
            continue
        if r["restated_tier"] == "DEAD_BEFORE_COST":
            flips[key] = {"flippable": False,
                          "reason": "gross is negative before any swap — carry is not its problem"}
            continue
        acct, sleeve = r["account"], r["sleeve"]
        rows = raw["trades"][sleeve]
        gross = r["inputs_held_fixed"]["gross_r"]
        ex = r["inputs_held_fixed"]["true_cost_ex_swap_r"]
        pn = r["inputs_held_fixed"]["swap_r_per_night"]
        ivl_h = tf_min[tf_of[sleeve]] / 60.0
        found = None
        for T in range(80, 0, -1):                      # loosest first
            cap_h = T * ivl_h
            ns = [rollover_nights(dt.datetime.fromisoformat(x["entry_utc"]),
                                  min(float(x["hold_hours"]), cap_h), server=SERVER,
                                  rollover3days_weekday=swap3(costs_doc, acct, x["symbol"]))[0]
                  for x in rows]
            if gross - ex - pn * q(ns, 0.99) > 0:
                found = {"time_stop_own_bars": T,
                         "time_stop_hours": round(cap_h, 2),
                         "as_frac_of_horizon": (round(cap_h / r["horizon_hours_assumed"], 4)
                                                if r.get("horizon_hours_assumed") else None),
                         "capped_nights_mean": round(statistics.fmean(ns), 4),
                         "capped_nights_p99": round(q(ns, 0.99), 4),
                         "net_r_at_capped_p99": round(gross - ex - pn * q(ns, 0.99), 5),
                         "frac_trades_truncated": round(
                             sum(1 for x in rows if float(x["hold_hours"]) > cap_h)
                             / len(rows), 4)}
                break
        flips[key] = ({"flippable": True, "flips_to": "UNCONDITIONAL", **found} if found else
                      {"flippable": False,
                       "reason": ("no time stop down to 1 bar takes the p99 crossing count "
                                  "under break-even — one bar on this grid already crosses "
                                  "more nights than the edge can absorb")})
        if found:
            ledger.record(
                mechanism="carry_tier_flip_threshold", sleeve=sleeve,
                variant={"account": acct, "time_stop_own_bars": found["time_stop_own_bars"],
                         "changed_input": "hold capped, nights recounted"},
                window="full_archive_holds_x_cache_edge", outcome="evaluated",
                metric=found["net_r_at_capped_p99"], metric_name="net_r_at_capped_p99_nights",
                note=f"loosest time stop flipping {r['restated_tier']} -> UNCONDITIONAL",
            )

    # ---- print ---------------------------------------------------------------------------
    print(f"{'account':11s} {'sleeve':20s} {'published':34s} {'restated':34s} "
          f"{'n_mdl':>7s} {'n_meas':>7s} {'ratio':>6s} {'BE_n':>7s} {'hdrm':>6s}")
    for k, r in out_rows.items():
        if not r.get("restatable"):
            print(f"{r['account']:11s} {r['sleeve']:20s} {str(r['published_tier']):34s} "
                  f"{'(not restatable)':34s} {r['reason'][:40]}")
            continue
        mv = " <== MOVED" if r["tier_moved"] else ""
        print(f"{r['account']:11s} {r['sleeve']:20s} {str(r['published_tier']):34s} "
              f"{str(r['restated_tier']):34s} "
              f"{r['nights_modelled']['mean_held_to_horizon']:7.2f} "
              f"{r['nights_measured']['mean']:7.3f} "
              f"{r['nights_ratio_measured_over_modelled']:6.3f} "
              f"{str(r['inputs_held_fixed']['break_even_nights']):>7s} "
              f"{str(r['carry_headroom_measured']):>6s}{mv}")

    print(f"\n{'the tier-flip threshold — the LOOSEST time stop that reaches UNCONDITIONAL':78s}")
    print(f"{'account::sleeve':34s} {'bars':>5s} {'hours':>8s} {'frac_hz':>8s} "
          f"{'n_p99':>7s} {'net@p99':>9s} {'trunc%':>7s}")
    for k, f in flips.items():
        if not f.get("flippable"):
            print(f"{k:34s} {'-':>5s}  {f['reason']}")
            continue
        print(f"{k:34s} {f['time_stop_own_bars']:5d} {f['time_stop_hours']:8.1f} "
              f"{str(f['as_frac_of_horizon']):>8s} {f['capped_nights_p99']:7.2f} "
              f"{f['net_r_at_capped_p99']:9.5f} {100*f['frac_trades_truncated']:7.1f}")

    bad = [k for k, r in out_rows.items()
           if r.get("restatable") and not r["rule_replication_ok"]]
    print(f"\nrule replication: {len(out_rows) - len(bad)}/{len(out_rows)} reproduce the "
          f"published tier from the artifact's own inputs" + (f"; FAILED: {bad}" if bad else ""))
    print(f"tiers moved: {len(moved)} — {moved}")

    doc = {
        "schema": "gtos.walkforward.carry_tiers_restated.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AD",
        "block": "B753",
        "question": ("CLAUDE.md §4: 'What now decides OD-3 is holding time.' The survivor "
                     "book's tiers are computed at a MODELLED hold — every trade held to its "
                     "horizon — because no realised hold survived any cache "
                     "(SESSION_N §8.1). AA's archive walk has the realised hold. This changes "
                     "that one input and nothing else."),
        "method": {
            "changed": "charged swap nights only",
            "held_fixed": ["gross_r", "true_cost_ex_swap_r", "swap_r_per_night",
                           "the tier rule itself"],
            "tier_rule_source": "scripts/recost_w7_validation.py:1062-1073, replicated",
            "nights_counted_by": ("costs.model.rollover_nights per trade, on the broker wall "
                                  "clock, with the per-symbol swap_rollover3days from "
                                  "BROKER_TRUE_COSTS_V1_1"),
            "worst_case_proxy": ("measured p99 nights stands in for the modelled "
                                 "max_nights, because the modelled max is a worst case over "
                                 "ENTRY HOURS and not an outlier trade — letting one row "
                                 "decide a tier would be worse than the assumption it replaces"),
            "population_caveat": ("edge terms are from the W7 validation CACHES; holds are "
                                  "from the FULL ARCHIVE. No population carries both — that "
                                  "is the gap SESSION_N §8.1 recorded. Strictly better than a "
                                  "horizon assumption; not the same as a single-population "
                                  "measurement."),
        },
        "n_tiers_moved": len(moved),
        "tiers_moved": moved,
        "tier_flip_thresholds": {
            "what": ("the LOOSEST time stop, in the sleeve's own bars, whose capped hold "
                     "takes the p99 charged-night count under break-even — i.e. flips the "
                     "restated tier to UNCONDITIONAL"),
            "why_a_time_stop_is_the_right_instrument": (
                "the restatement shows the blocker is the TAIL: the rule's UNCONDITIONAL test "
                "is gross - ex - pn*p99_nights > 0, and on an H4 grid the top 1 % of holds "
                "still reach the 80-bar / 320 h ceiling even though the MEAN hold is a "
                "quarter of it. A time stop leaves the median trade alone and truncates only "
                "the tail."),
            "what_this_does_NOT_price": (
                "the R the time stop costs. Capping the hold changes gross, and this half "
                "holds gross fixed by construction. ad_exit_sweep.py measures the R at the "
                "same cell; the two halves must be read together and the result doc does."),
            "rows": flips,
        },
        "measured_nights_by_sleeve": nights,
        "rows": out_rows,
    }
    OUT.write_text(json.dumps(doc, indent=1, default=str))
    print(f"wrote {OUT.relative_to(REPO)}")
    return doc


if __name__ == "__main__":
    main()

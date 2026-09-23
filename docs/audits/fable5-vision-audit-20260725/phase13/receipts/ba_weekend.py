"""Session BA — the redacted_account weekend-holding solution: census, pricing, and the switch.

    python3 docs/audits/fable5-vision-audit-20260725/phase13/receipts/ba_weekend.py --stage census
    ... --stage flat        # the flat surface: 6 cutoffs x 4 armed sleeves x 4 bands
    ... --stage embargo     # the entry-embargo surface at the a-priori cutoff
    ... --stage identity    # the LIVE deadline == the research cutoff, instant by instant
    ... --stage all         # default

WHAT THIS IS FOR
----------------
`FIRM_RULES_V1.json` -> `firms.redacted_account.rules.weekend_holding`: *"allowed in Challenge,
PROHIBITED on the funded account. Requires a post-pass config change that does not exist."*
Its own `absent` list says the same thing from the other side: *"Any weekend-flatten policy
for redacted_account's funded phase"* is in no artifact. redacted_account is ARMED and trading a
challenge today, so the prohibition binds at the moment it PASSES — the one blocker in the
programme whose trigger is success. This session prices it and builds it before it blocks.

WHAT "CROSSES A WEEKEND" MEANS HERE, AND WHY IT IS READ OFF THE GRID
--------------------------------------------------------------------
A position crosses a weekend iff it is open at the instant the market closes for one. That
instant is not a constant and must not be assumed: it is measured, per symbol, from the bar
archive's own gaps (`weekend_closes`). The measurement's first finding is that the estate's
symbols do not agree — `BTCUSD` and `DASHUSD` carry Saturday and Sunday bars for part of
their history and none for the rest, so "the weekend" is a property of (symbol, week) and
not of the calendar. Both readings are therefore priced:

    GRID      the deadline is the last bar before the market's own gap; a week with
              continuous crypto bars has NO deadline (nothing to be flat for)
    CALENDAR  the deadline is the broker-local Saturday 00:00 regardless of whether the
              instrument trades through it — the conservative reading of a firm rule that
              says "no weekend holding" without naming an instrument class

The difference is the crypto sleeve's entire bill, which is why it is an owner question with
a number attached rather than a modelling choice made here.

THE CUTOFF IS A SURFACE, NOT A CELL, AND THE HEADLINE IS CHOSEN A PRIORI
------------------------------------------------------------------------
`weekend_flat_m0` — be flat at the close of the last bar that ends STRICTLY BEFORE the
deadline — is the headline for every claim in this session. It is chosen before any result
is read, for a stated reason: on the H4 grid it lands the exit at broker Friday 20:00, four
hours of margin before the close, which is the tightest cell a live market order can
actually fill. `m_inclusive` (exit exactly AT the close) is run as a CONTROL that bounds
what the policy could be worth to an executor who cannot exist, and the earlier cutoffs
(m4h..m24h) are the margin dial. Reporting the surface's best cell as the cost would be
AO's undeclared-median-cut error with a different variable.

MULTIPLICITY
------------
No new declared looks. Every arm is an exit-contract re-measurement of a sleeve already
declared in `CANDIDATE_BOOK_V1` (AU: BH corrects for distinct hypotheses, not for
re-measurements of one). The claim this session makes is a COST — the A/B of one sleeve
against its own as-walked labelling — and not an edge. Should a cell come out ADMIT, it is
reported as what it is: an admission that would have to be charged at a declared family
before anyone acts on it. Every arm is ledgered, including NOT_EVALUABLE.

BOUNDARY
--------
Offline and pure. Reads bars, cost artifacts and the estate's stored intents; imports no
broker module, places nothing, and writes only into `phase13/receipts/` and the two
append-only ledgers.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import json
import math
import statistics
import sys
import time
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase13/receipts"
AD_DIR = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
AU_DIR = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(AD_DIR))
sys.path.insert(0, str(AU_DIR))

import ad_exit_sweep as AD  # noqa: E402
import au_live_contract as LC  # noqa: E402

from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as POP  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.utils.broker_clock import (  # noqa: E402
    broker_naive_to_utc,
    resolve_rule,
    utc_to_broker_naive,
)

#: AQ's re-clocked estate is the population of record (`sub_mid_dn_revert` 503 -> 533; the
#: AA rows for that sleeve were produced by the F7 clock defect AM repaired).
ESTATE = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
#: The current high-water family declaration (wave-12b): the ratchet refuses to shrink, so
#: whatever is highest is the bill actually payable.
FAMILY = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts/CANDIDATE_FAMILY_V9.json"
FIRM_RULES = REPO / "research/operations/broker_truth_layer_2026_07_27/FIRM_RULES_V1.json"
OUT = HERE / "BA_WEEKEND_V1.json"

ACCOUNT, SERVER = "FTMO", "FTMO-Server3"
#: The policy runs on redacted_account. Its server clock is checked against FTMO's in `stage_census`
#: (both resolve to America/New_York + 7 h, `broker_clock.py`), and the R measurement stays on
#: the FTMO archive the estate was walked on — swapping the bar source would change the
#: population, which is a different experiment.
FN_SERVER = "redacted_account-Server 2"
BANDS = (None, "low", "mid", "high")   # None == the flat 37-day snapshot, a CONTROL
POPULATION = "RECORDED"                # ratified 2026-07-30
OPTION = "B_balanced"                  # options.py:110 disqualifies alpha 0.20 for arming

#: The armed set as of 2026-07-30 ~14:57Z on BOTH accounts (`run_book.py --tags`).
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert")

#: Hours before the broker-local Saturday 00:00 at which the book must already be flat.
#: `m_inclusive` is the CONTROL (exit exactly at the close, unfillable); `m0` is the headline.
CUTOFFS = (("m_inclusive", -0.001), ("m0", 0.0), ("m4h", 4.0), ("m8h", 8.0),
           ("m12h", 12.0), ("m24h", 24.0))
#: Hours before the same deadline inside which a new entry is refused. 0 == no embargo.
EMBARGOES = (0.0, 4.0, 8.0, 12.0, 24.0, 48.0)
HEADLINE_CUTOFF = "m0"

TF_MINUTES = AD.TF_MINUTES


# =====================================================================================
# the deadline — one definition, two readings
# =====================================================================================

def next_saturday_midnight_utc(entry_utc: dt.datetime, rule) -> dt.datetime:
    """First broker-local Saturday 00:00 strictly after `entry_utc`.

    Saturday 00:00 broker local is the instant the FX/metal/index week ends: measured, the
    last H4 bar of every week OPENS Friday 20:00 broker and therefore CLOSES exactly here
    (`stage_census` -> `weekend_closes.modal_last_bar_open_local`). It is a calendar
    quantity, which is what makes it computable by a live book that has no archive.
    """
    local = utc_to_broker_naive(entry_utc, rule)
    # weekday(): Mon=0 .. Sat=5, Sun=6. The Saturday 00:00 that ENDS this week.
    days = (5 - local.weekday()) % 7
    cand = (local + dt.timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    if cand <= local:
        cand += dt.timedelta(days=7)
    return broker_naive_to_utc(cand, rule)


def weekend_closes(times: list[dt.datetime], rule) -> list[int]:
    """Indices of bars that are the LAST print before the market's own weekend gap.

    A gap qualifies iff the span between one bar's close and the next bar's open contains
    broker-local Saturday 12:00 — the middle of the weekend. That test is deliberately
    coarse: a Thursday-to-Monday gap (a Friday holiday, 7 of them on `USOIL.cash`) is a
    weekend close and must be caught, and a Saturday-only crypto pause is one too.
    """
    out: list[int] = []
    for j in range(len(times) - 1):
        a, b = times[j], times[j + 1]
        la, lb = utc_to_broker_naive(a, rule), utc_to_broker_naive(b, rule)
        # Saturday noons strictly inside (la, lb).
        days = (5 - la.weekday()) % 7
        noon = (la + dt.timedelta(days=days)).replace(hour=12, minute=0, second=0, microsecond=0)
        if noon <= la:
            noon += dt.timedelta(days=7)
        if noon < lb:
            out.append(j)
    return out


def gapped_weekends(times: list[dt.datetime], rule) -> dict[tuple[int, int], int]:
    """`(iso_year, iso_week) of the Saturday` -> the bar index that last printed before it.

    The GRID reading needs to know whether THIS weekend gapped, not whether the series ever
    gaps. Keying by the Saturday's ISO week is what makes that a lookup rather than a scan,
    and getting it wrong is not a small error: a first version took "the next weekend close
    anywhere in the series", which for a continuously-quoted crypto week resolved to a gap
    years later and silently collapsed the grid reading onto the calendar one. It read as a
    result (crypto's grid cell came out WORSE than its calendar cell, which is impossible by
    construction) and that impossibility is what caught it.
    """
    out: dict[tuple[int, int], int] = {}
    for j in weekend_closes(times, rule):
        la = utc_to_broker_naive(times[j], rule)
        days = (5 - la.weekday()) % 7
        sat = (la + dt.timedelta(days=days)).replace(hour=12, minute=0, second=0, microsecond=0)
        if sat <= la:
            sat += dt.timedelta(days=7)
        out.setdefault(sat.isocalendar()[:2], j)
    return out


def _saturday_week_key(deadline_utc: dt.datetime, rule) -> tuple[int, int]:
    """The ISO (year, week) of the Saturday whose 00:00 is `deadline_utc`."""
    return (utc_to_broker_naive(deadline_utc, rule)
            + dt.timedelta(hours=12)).isocalendar()[:2]


# =====================================================================================
# stage census
# =====================================================================================

def _pct(n: int, d: int) -> float | None:
    return round(n / d, 5) if d else None


def stage_census(sub: dict) -> dict:
    rule = sub["rule"]
    series, index = sub["series"], sub["index"]
    fn_rule = resolve_rule(FN_SERVER)

    # --- the two servers' weekend instant, from the clock module ----------------------
    probe = dt.datetime(2026, 7, 24, 12, 0, tzinfo=dt.timezone.utc)
    clock = {
        "ftmo_saturday_midnight_utc": next_saturday_midnight_utc(probe, rule).isoformat(),
        "redacted_account_saturday_midnight_utc": next_saturday_midnight_utc(probe, fn_rule).isoformat(),
    }
    clock["servers_agree"] = (clock["ftmo_saturday_midnight_utc"]
                              == clock["redacted_account_saturday_midnight_utc"])
    # ...and over a whole year, because one probe is not a calendar claim.
    dis = 0
    d = dt.datetime(2026, 1, 1, 12, 0, tzinfo=dt.timezone.utc)
    for _ in range(365):
        if next_saturday_midnight_utc(d, rule) != next_saturday_midnight_utc(d, fn_rule):
            dis += 1
        d += dt.timedelta(days=1)
    clock["days_of_2026_where_the_two_servers_disagree"] = dis

    # --- per-symbol grid structure ----------------------------------------------------
    symbols: dict[str, dict] = {}
    wanted = sorted({r["symbol"] for s in ARMED for r in sub["base"][s]})
    for sym in wanted:
        key = (sym, AD.TF_H4)
        if key not in series:
            symbols[sym] = {"available": False}
            continue
        bars, times = series[key]
        wd = collections.Counter(utc_to_broker_naive(t, rule).weekday() for t in times)
        wc = weekend_closes(times, rule)
        opens = collections.Counter(
            utc_to_broker_naive(times[j], rule).strftime("%a %H:%M") for j in wc)
        n_weeks = len({utc_to_broker_naive(t, rule).isocalendar()[:2] for t in times})
        symbols[sym] = {
            "available": True, "n_bars": len(times),
            "first": times[0].isoformat(), "last": times[-1].isoformat(),
            "n_weekend_bars": wd[5] + wd[6],
            "weekend_bar_frac": _pct(wd[5] + wd[6], len(times)),
            "trades_through_weekends": bool(wd[5] + wd[6]),
            "n_calendar_weeks": n_weeks, "n_grid_weekend_closes": len(wc),
            "grid_closes_per_week": _pct(len(wc), n_weeks),
            "modal_last_bar_open_local": (opens.most_common(1)[0] if opens else None),
            "last_bar_open_local_top3": opens.most_common(3),
        }

    # --- per-sleeve crossing census ---------------------------------------------------
    sleeves: dict[str, dict] = {}
    for s in ARMED:
        rows = sub["base"][s]
        n_cross_grid = n_cross_cal = 0
        cross_counts: collections.Counter = collections.Counter()
        r_by_class: dict[str, list[float]] = {"crossed": [], "not_crossed": []}
        held_at_close_hours: list[float] = []
        skips: collections.Counter = collections.Counter()
        for r in rows:
            key = (r["symbol"], int(r["timeframe"]))
            if key not in index:
                skips["no_series"] += 1
                continue
            i = index[key].get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
            if i is None:
                skips["bar_not_found"] += 1
                continue
            bars, times = series[key]
            ivl = dt.timedelta(minutes=TF_MINUTES[int(r["timeframe"])])
            entry_utc = times[i] + ivl
            x = i + int(r["exit_bar_offset"])
            exit_utc = times[min(x, len(times) - 1)] + ivl
            # GRID reading: a weekend close index strictly inside [i, x)
            grid_hits = [j for j in sub["wc_index"][key] if i <= j < x]
            # CALENDAR reading: a broker Saturday 00:00 inside (entry, exit]
            dl = next_saturday_midnight_utc(entry_utc, rule)
            cal_hits = 0
            while dl < exit_utc:
                cal_hits += 1
                dl = next_saturday_midnight_utc(dl, rule)
            rg = float(r["r_gross"])
            if grid_hits:
                n_cross_grid += 1
                held_at_close_hours.append(
                    (times[grid_hits[0]] + ivl - entry_utc).total_seconds() / 3600.0)
            if cal_hits:
                n_cross_cal += 1
            cross_counts[len(grid_hits)] += 1
            r_by_class["crossed" if grid_hits else "not_crossed"].append(rg)
        n = len(rows)
        sleeves[s] = {
            "n_trades": n,
            "n_crossing_grid": n_cross_grid, "frac_crossing_grid": _pct(n_cross_grid, n),
            "n_crossing_calendar": n_cross_cal,
            "frac_crossing_calendar": _pct(n_cross_cal, n),
            "n_weekends_crossed_histogram": dict(sorted(cross_counts.items())),
            "mean_r_gross_crossed": (round(statistics.fmean(r_by_class["crossed"]), 5)
                                     if r_by_class["crossed"] else None),
            "mean_r_gross_not_crossed": (round(statistics.fmean(r_by_class["not_crossed"]), 5)
                                         if r_by_class["not_crossed"] else None),
            "n_crossed": len(r_by_class["crossed"]),
            "n_not_crossed": len(r_by_class["not_crossed"]),
            "median_hours_open_before_first_close": (
                round(statistics.median(held_at_close_hours), 3) if held_at_close_hours else None),
            "skips": dict(skips),
        }
        print(f"  {s:22s} n={n:4d} crossing: grid {n_cross_grid:4d} "
              f"({sleeves[s]['frac_crossing_grid']}) calendar {n_cross_cal:4d} "
              f"({sleeves[s]['frac_crossing_calendar']})", flush=True)

    fr = json.loads(FIRM_RULES.read_text())
    return {
        "firm_rule": fr["firms"]["redacted_account"]["rules"]["weekend_holding"],
        "firm_rule_absent_note": [a for a in fr["absent"] if "weekend" in a.lower()],
        "ftmo_has_no_weekend_rule": (
            "weekend_holding" not in fr["firms"]["FTMO"]["rules"]),
        "clock": clock, "symbols": symbols, "sleeves": sleeves,
    }


# =====================================================================================
# the variants
# =====================================================================================

def binding_deadline_utc(entry_utc: dt.datetime, horizon_end_utc: dt.datetime, rule,
                         *, reading: str, gapped: dict) -> dt.datetime | None:
    """The first weekend deadline that binds this trade, or None if none does.

    CALENDAR: the first broker Saturday 00:00 after entry, whatever the instrument does.
    That is the conservative reading of a firm rule that says "no weekend holding" without
    naming an instrument class.

    GRID: the first such Saturday whose week the SERIES ACTUALLY GAPPED. A crypto week
    quoted continuously has no market close to be flat for, so under this reading the
    position may run through it and the search moves to the following weekend. Bounded by
    the trade's own `maxbars` horizon — a weekend the trade cannot reach is not a deadline.
    """
    dl = next_saturday_midnight_utc(entry_utc, rule)
    while dl <= horizon_end_utc:
        if reading == "calendar" or _saturday_week_key(dl, rule) in gapped:
            return dl
        dl = next_saturday_midnight_utc(dl, rule)
    return None


def resimulate_weekend(sub: dict, sleeve: str, *, margin_hours: float | None,
                       embargo_hours: float, reading: str) -> tuple[list[dict], dict]:
    """The sleeve's as-walked intents re-labelled under the weekend policy.

    `margin_hours=None` is the no-flat control (the embargo alone, which is NOT legal and
    exists only to separate the entry-side cost from the exit-side one).
    """
    series, index, rule = sub["series"], sub["index"], sub["rule"]
    out: list[dict] = []
    tel: collections.Counter = collections.Counter()
    for r in sub["base"][sleeve]:
        tf = int(r["timeframe"])
        key = (r["symbol"], tf)
        if key not in index:
            tel["skip_no_series"] += 1
            continue
        i = index[key].get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
        if i is None:
            tel["skip_bar_not_found"] += 1
            continue
        bars, times = series[key]
        if i + 2 >= len(bars):
            tel["skip_no_room"] += 1
            continue
        ivl = dt.timedelta(minutes=TF_MINUTES[tf])
        entry_utc = times[i] + ivl
        end = min(i + AD.MAXBARS, len(bars) - 1)
        deadline = binding_deadline_utc(entry_utc, times[end] + ivl, rule,
                                        reading=reading, gapped=sub["gapped"][key])

        if embargo_hours and deadline is not None:
            if (deadline - entry_utc).total_seconds() / 3600.0 <= embargo_hours:
                tel["embargoed"] += 1
                continue

        flat_utc = None
        if margin_hours is not None and deadline is not None:
            flat_utc = deadline - dt.timedelta(hours=margin_hours)
            if flat_utc <= entry_utc:
                # The deadline is already behind the entry: the trade cannot legally exist
                # under this cutoff. Refusing it is the same decision the embargo makes,
                # so it is counted separately and dropped rather than silently kept.
                tel["dropped_deadline_before_entry"] += 1
                continue

        pol = AD.ExitPolicy(
            target_dist=r.get("target_dist"),
            maxbars=AD.MAXBARS,
            label=f"weekend_{reading}",
        )
        pr = AD.replay(bars, i, int(r["direction"]),
                       stop_dist=float(r["sl_distance_price"]), policy=pol,
                       times=times, server=SERVER, bar_minutes=TF_MINUTES[tf],
                       flat_before_utc=flat_utc)
        xi = pr.exit_index
        tel[f"exit_{pr.exit_reason}"] += 1
        tel["n_exited"] += 1
        out.append({
            **r,
            "entry_utc": entry_utc.isoformat(),
            "exit_utc": (times[xi] + ivl).isoformat(),
            "r_gross": float(AD.winsorize_R(pr.r_gross)),
            "exit_policy": pol.label,
            "exit_reason": pr.exit_reason,
            "mfe_r": round(pr.mfe_r, 6), "mae_r": round(pr.mae_r, 6),
            "bars_to_mfe": int(pr.bars_to_mfe),
            "exit_bar_offset": int(xi - i),
            "hold_hours": round((xi - i) * TF_MINUTES[tf] / 60.0, 4),
        })
    return out, dict(tel)


# =====================================================================================
# gating one arm
# =====================================================================================

def _maxbars_share(tel: dict) -> dict:
    n = tel.get("n_exited") or 0
    return {
        "n_exited": n,
        "maxbars_share": _pct(tel.get("exit_maxbars", 0), n),
        "rollover_flat_share": _pct(tel.get("exit_rollover_flat", 0), n),
        "embargoed": tel.get("embargoed", 0),
        "dropped_deadline_before_entry": tel.get("dropped_deadline_before_entry", 0),
        "exit_reasons": {k[5:]: v for k, v in sorted(tel.items()) if k.startswith("exit_")},
    }


def run_arm(sub: dict, sleeve: str, *, arm: str, band, rows: list[dict], tel: dict,
            ledger: TrialLedger | None, extra: dict | None = None) -> dict:
    t0 = time.time()
    by_sleeve = {s: list(r) for s, r in sub["base"].items()}
    by_sleeve[sleeve] = rows
    o = OPTIONS[OPTION]
    spec = o.with_(spec_id=f"{o.spec_id}_ba_weekend_{arm}",
                   sleeve_symbol_allowlist=sub["allowlist"], spread_band=band)
    spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=sub["family"])
    recs0 = {s: AD.to_records(r) for s, r in by_sleeve.items()}
    recs, spec, mix = POP.apply(POPULATION, recs0, spec, account=ACCOUNT, band=(band or "mid"))
    res = run_gate(recs, spec, costs=sub["costs"], server=SERVER, diagnose=True)
    sv = res.verdicts.get(sleeve)
    el = time.time() - t0

    fam = (res.family or {}).get("multiplicity", {}) or {}
    row = {
        "arm": arm, "sleeve": sleeve, "population": POPULATION,
        "band": band if band is not None else "flat_37_day_snapshot",
        "band_is_control": band is None, "option": OPTION,
        "alpha": spec.alpha, "declared_family_size": spec.declared_family_size,
        "declared_family_id": spec.declared_family_id,
        "effective_family_size": fam.get("effective_family_size"),
        "spec_sha256": spec.seal(), "population_mix": mix,
        "seconds": round(el, 2), **_maxbars_share(tel), **(extra or {}),
    }
    wo = (res.family or {}).get("wipeout") or {}
    if wo.get("wiped_out"):
        raise RuntimeError(f"gate wipeout on {arm}/{sleeve}: {wo} — a whole run of nulls "
                           f"tabulates as a result (AQ §0 item 6). Refusing to publish.")
    if sv is None:
        row["verdict"] = "ABSENT"
        return row
    st = sv.gates.get("stability", {})
    fl = (sv.telemetry or {}).get("p_floor", {}) or {}
    ri = (sv.telemetry or {}).get("regime_inflation") or {}
    ins = (sv.telemetry or {}).get("in_sample") or {}
    diag = sv.diagnostics or {}
    hold = diag.get("holding") or {}
    cd = diag.get("cost_decomposition") or {}
    terms = cd.get("terms") or {}
    row.update({
        "verdict": sv.verdict.value, "n_trades": sv.n_trades,
        "pooled_oos_mean_r": sv.pooled_oos_mean_r,
        "oos_mean_r_per_trade": sv.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
        "p_raw": sv.p_raw, "q_value": sv.q_value,
        "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                           "robustness", "significance")
                               if not sv.gates.get(g, {}).get("pass")],
        "fold_means": st.get("fold_means"),
        "oos_positive_fold_frac": st.get("oos_positive_fold_frac"),
        "n_folds_evaluable": sv.gates.get("sample", {}).get("n_folds_evaluable"),
        "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
        "p_floor": fl.get("p_floor"), "n_blocks": fl.get("n_blocks"),
        "regime_inflation_verdict": ri.get("verdict"),
        "recommended_magnitude_haircut": ri.get("recommended_magnitude_haircut"),
        "haircut_binding_term": ri.get("haircut_binding_term"),
        "in_sample_mean_is_r": ins.get("mean_is_r"),
        "in_sample_mean_oos_r": ins.get("mean_oos_r"),
        "in_sample_sign_inversion": (
            None if (ins.get("mean_is_r") is None or ins.get("mean_oos_r") is None)
            else bool(float(ins["mean_is_r"]) < 0 <= float(ins["mean_oos_r"]))),
        "median_hold_hours": hold.get("median_hours"),
        "frac_hold_over_24h": hold.get("frac_over_24h"),
        "mean_gross_r": cd.get("mean_gross_r"), "mean_cost_r": cd.get("mean_cost_r"),
        "swap_share_of_cost": (terms.get("swap_r") or {}).get("share_of_cost"),
        "swap_nights_mean": ((cd.get("swap_nights") or {}).get("mean")),
        "frac_trades_zero_nights": ((cd.get("swap_nights") or {}).get("frac_zero")),
        "folds": sv.folds, "reasons": list(sv.reasons),
    })
    if ledger is not None:
        ledger.record(
            mechanism="weekend_holding_policy", sleeve=sleeve,
            variant={"arm": arm, "population": POPULATION, "band": row["band"],
                     "option": OPTION},
            window="full_archive", spec_sha256=spec.seal(),
            outcome={"ADMIT": "admitted", "REJECT": "rejected",
                     "NOT_EVALUABLE": "not_evaluable"}.get(row["verdict"], "evaluated"),
            metric=row.get("pooled_oos_mean_r"), metric_name="pooled_oos_mean_r",
            note=f"BA weekend policy, {sleeve} @ {arm}")
    return row


# =====================================================================================
# stages flat / embargo
# =====================================================================================

def _baseline(sub: dict, sleeve: str, band, ledger) -> tuple[dict, dict]:
    rows, tel = AD.resimulate(sub["base"][sleeve], AD.AS_WALKED, sub["series"],
                              sub["index"], sub["costs"], ACCOUNT, sub["rule"])
    tel = dict(tel)
    tel["n_exited"] = sum(v for k, v in tel.items() if k.startswith("exit_"))
    return run_arm(sub, sleeve, arm="as_walked", band=band, rows=rows, tel=tel,
                   ledger=ledger), tel


def control_reproduces_as_walked(sub: dict) -> dict:
    """`resimulate_weekend` with no flat and no embargo must BE AD's `as_walked`, row by row.

    Every number in this session is a difference against that baseline, so if the two
    labellers disagree the differences are about my reimplementation and not about the
    policy. Checked before any cell is gated, and it FAILS the run rather than warning.
    """
    out = {}
    for sleeve in ARMED:
        a, _ = AD.resimulate(sub["base"][sleeve], AD.AS_WALKED, sub["series"], sub["index"],
                             sub["costs"], ACCOUNT, sub["rule"])
        b, _ = resimulate_weekend(sub, sleeve, margin_hours=None, embargo_hours=0.0,
                                  reading="calendar")

        def key(r):
            return (r["symbol"], r["decision_bar_iso"], int(r["direction"]))

        da, db = {key(r): r for r in a}, {key(r): r for r in b}
        shared = sorted(set(da) & set(db))
        bad = [k for k in shared
               if abs(float(da[k]["r_gross"]) - float(db[k]["r_gross"])) > 1e-9
               or int(da[k]["exit_bar_offset"]) != int(db[k]["exit_bar_offset"])]
        rec = {"n_as_walked": len(da), "n_mine": len(db), "n_shared": len(shared),
               "n_mismatched": len(bad),
               "identical": not bad and len(shared) == len(da) == len(db)}
        out[sleeve] = rec
        if not rec["identical"]:
            raise RuntimeError(f"BA baseline control failed on {sleeve}: {rec}")
    return out


def stage_flat(sub: dict, ledger, readings=("calendar", "grid")) -> dict:
    out: dict = {"cells": [], "headline_cutoff": HEADLINE_CUTOFF,
                 "control_reproduces_as_walked": control_reproduces_as_walked(sub)}
    for sleeve in ARMED:
        for band in BANDS:
            base = _baseline(sub, sleeve, band, ledger)[0]
            out["cells"].append(base)
            for reading in readings:
                for name, m in CUTOFFS:
                    rows, tel = resimulate_weekend(
                        sub, sleeve, margin_hours=m, embargo_hours=0.0, reading=reading)
                    row = run_arm(sub, sleeve, arm=f"flat_{reading}_{name}", band=band,
                                  rows=rows, tel=tel, ledger=ledger,
                                  extra={"reading": reading, "cutoff": name,
                                         "margin_hours": m, "embargo_hours": 0.0})
                    row["delta_pooled_oos_mean_r"] = _delta(
                        base.get("pooled_oos_mean_r"), row.get("pooled_oos_mean_r"))
                    out["cells"].append(row)
            print(f"  {sleeve:22s} band={str(band):6s} base={_f(base.get('pooled_oos_mean_r'))} "
                  f"flat_cal_m0="
                  f"{_f(_find(out['cells'], sleeve, band, 'flat_calendar_m0'))}"
                  f" flat_grid_m0="
                  f"{_f(_find(out['cells'], sleeve, band, 'flat_grid_m0'))}", flush=True)
    return out


def stage_embargo(sub: dict, ledger, reading="calendar") -> dict:
    out: dict = {"cells": [], "reading": reading, "cutoff": HEADLINE_CUTOFF}
    margin = dict(CUTOFFS)[HEADLINE_CUTOFF]
    for sleeve in ARMED:
        for band in BANDS:
            base = _baseline(sub, sleeve, band, ledger)[0]
            for e in EMBARGOES:
                if e == 0.0:
                    continue
                rows, tel = resimulate_weekend(sub, sleeve, margin_hours=margin,
                                               embargo_hours=e, reading=reading)
                row = run_arm(sub, sleeve, arm=f"flat_{reading}_{HEADLINE_CUTOFF}_embargo_{e:g}h",
                              band=band, rows=rows, tel=tel, ledger=ledger,
                              extra={"reading": reading, "cutoff": HEADLINE_CUTOFF,
                                     "margin_hours": margin, "embargo_hours": e})
                row["delta_pooled_oos_mean_r"] = _delta(
                    base.get("pooled_oos_mean_r"), row.get("pooled_oos_mean_r"))
                out["cells"].append(row)
                # ...and the embargo ALONE, which is illegal but isolates the entry cost.
                rows2, tel2 = resimulate_weekend(sub, sleeve, margin_hours=None,
                                                 embargo_hours=e, reading=reading)
                row2 = run_arm(sub, sleeve, arm=f"embargo_only_{e:g}h", band=band,
                               rows=rows2, tel=tel2, ledger=ledger,
                               extra={"reading": reading, "cutoff": None,
                                      "margin_hours": None, "embargo_hours": e,
                                      "legal": False})
                row2["delta_pooled_oos_mean_r"] = _delta(
                    base.get("pooled_oos_mean_r"), row2.get("pooled_oos_mean_r"))
                out["cells"].append(row2)
            print(f"  {sleeve:22s} band={str(band):6s} embargo surface done", flush=True)
    return out


def row_r(row: dict):
    return row.get("pooled_oos_mean_r")


def _delta(a, b):
    if a is None or b is None:
        return None
    return round(float(b) - float(a), 6)


def _f(x):
    return "None" if x is None else f"{float(x):+.4f}"


def _find(cells, sleeve, band, arm):
    b = band if band is not None else "flat_37_day_snapshot"
    for c in cells:
        if c.get("sleeve") == sleeve and c.get("band") == b and c.get("arm") == arm:
            return c.get("pooled_oos_mean_r")
    return None


# =====================================================================================
# stage identity — the LIVE switch closes at the instant the priced cell exits at
# =====================================================================================

def stage_identity(sub: dict) -> dict:
    """Every priced `rollover_flat` exit must land on the instant `WeekendPolicy` would close at.

    This is the claim that makes the published cost the cost of the SWITCH rather than of a
    private replay: `flat_calendar_m0` exits at the close of the last H4 bar ending strictly
    before broker Saturday 00:00, and `WeekendPolicy(flatten_before_hours=4.0)` closes at
    broker Saturday 00:00 minus four hours. Those are the same instant on an H4 grid, and
    "should be" is not a measurement -- so it is checked over every affected trade, in both US
    DST seasons, on both live servers' rules.

    It is the same shape as AU's `frontier_is_the_research_cell` and it exists for the same
    reason: two code paths agreeing on an economic quantity is a claim about the paths, not
    about either one of them.
    """
    from src.components.ultimate_book.weekend_policy import (
        WeekendPolicy,
        next_weekend_boundary_utc,
    )

    margin = dict(CUTOFFS)[HEADLINE_CUTOFF]
    live = WeekendPolicy(sleeves=tuple(ARMED), flatten_before_hours=4.0)
    out: dict = {"headline_cutoff": HEADLINE_CUTOFF, "research_margin_hours": margin,
                 "live_flatten_before_hours": live.flatten_before_hours,
                 "sleeves": {}}
    for sleeve in ARMED:
        rows, _tel = resimulate_weekend(sub, sleeve, margin_hours=margin, embargo_hours=0.0,
                                        reading="calendar")
        n_flat = mismatch = 0
        bad: list[dict] = []
        for r in rows:
            if r["exit_reason"] != "rollover_flat":
                continue
            n_flat += 1
            entry = dt.datetime.fromisoformat(r["entry_utc"])
            exit_utc = dt.datetime.fromisoformat(r["exit_utc"])
            want = live.flatten_deadline_utc(entry, SERVER)
            # The live book closes on the first tick at or after its deadline; the replay closes
            # at the bar close that lands on that instant. Identical to the second.
            if exit_utc != want:
                mismatch += 1
                if len(bad) < 5:
                    bad.append({"symbol": r["symbol"], "entry_utc": r["entry_utc"],
                                "research_exit_utc": r["exit_utc"],
                                "live_deadline_utc": want.isoformat(),
                                "delta_hours": round(
                                    (exit_utc - want).total_seconds() / 3600.0, 4)})
        # ...and the same on the redacted_account rule, which is the account the policy runs on.
        fn_disagree = sum(
            1 for r in rows if r["exit_reason"] == "rollover_flat"
            and next_weekend_boundary_utc(dt.datetime.fromisoformat(r["entry_utc"]), SERVER)
            != next_weekend_boundary_utc(dt.datetime.fromisoformat(r["entry_utc"]), FN_SERVER))
        out["sleeves"][sleeve] = {
            "n_trades": len(rows), "n_weekend_flat_exits": n_flat,
            "n_mismatched": mismatch, "identical": mismatch == 0 and n_flat > 0,
            "n_where_the_two_servers_disagree": fn_disagree,
            "examples": bad,
        }
        print(f"  {sleeve:22s} weekend-flat exits {n_flat:4d}  mismatched {mismatch:3d}  "
              f"server disagreements {fn_disagree}", flush=True)
    out["identical_everywhere"] = all(v["identical"] for v in out["sleeves"].values())
    out["n_mismatched_total"] = sum(v["n_mismatched"] for v in out["sleeves"].values())
    out["n_weekend_flat_exits_total"] = sum(v["n_weekend_flat_exits"]
                                           for v in out["sleeves"].values())
    out["early_close_weeks"] = derive_early_close_dates(sub)
    # ...and the same identity re-checked WITH the derived list, which is the configuration the
    # owner package recommends. If this does not close to zero the list is not the explanation.
    live2 = WeekendPolicy(sleeves=tuple(ARMED), flatten_before_hours=4.0,
                          early_close_dates=tuple(out["early_close_weeks"]["dates"]))
    residual = 0
    for sleeve in ARMED:
        rows, _t = resimulate_weekend(sub, sleeve, margin_hours=margin, embargo_hours=0.0,
                                      reading="calendar")
        for r in rows:
            if r["exit_reason"] != "rollover_flat":
                continue
            entry = dt.datetime.fromisoformat(r["entry_utc"])
            want = live2.flatten_deadline_utc(entry, SERVER)
            if dt.datetime.fromisoformat(r["exit_utc"]) < want:
                # The live rule would close LATER than the replay did: the only unsafe
                # direction, and the one that must be zero.
                residual += 1
    out["with_derived_list"] = {
        "n_live_deadline_LATER_than_the_replay_exit": residual,
        "safe": residual == 0,
        "note": ("With the list the live deadline is never later than the priced exit, so the "
                 "published cost is a LOWER BOUND: on a listed week the live rule closes up to "
                 "one H4 bar earlier than the replay, because the replay can exit AT the last "
                 "close and a live market order cannot."),
    }
    print(f"  with the derived list: {residual} exits where live would close LATER "
          f"(must be 0)", flush=True)
    return out


#: A genuine early close costs a day or two, not a week. Anything wider is an ARCHIVE COVERAGE
#: GAP and not a market holiday, and the two are indistinguishable from bar absence alone —
#: which is exactly why the first version of this function returned 497 dates including whole
#: months of 2018 and 2021. Both filters below are needed and neither is sufficient.
_MAX_EARLY_CLOSE_GAP_HOURS = 52.0
#: A market holiday shuts every FX/metal/index symbol at once; a coverage gap is one symbol's
#: own. Quorum over the symbols that never print a weekend bar (crypto is excluded from the
#: vote because its own weekend behaviour is the thing under question).
_QUORUM_FRAC = 0.6


def derive_early_close_dates(sub: dict) -> dict:
    """The weeks the archive itself says closed early, and the dates a live list must name.

    Derived rather than assumed: this repository has no trading-session calendar, so the only
    holiday evidence available is the absence of bars in an archive that otherwise prints
    99.65-99.93 % of weeks complete. That makes the derivation a MEASUREMENT WITH A KNOWN
    CONFOUND — missing data looks exactly like a shut market — so it carries two filters and
    publishes what each one removed.
    """
    rule = sub["rule"]
    wanted = sorted({r["symbol"] for s in ARMED for r in sub["base"][s]})
    votes: dict[str, set[str]] = {}
    per_symbol: dict[str, dict] = {}
    voters: list[str] = []
    #: The DENOMINATOR has to be the symbols that could have voted, not every symbol: half the
    #: metals cross-pairs' archives begin in late 2020, and with them in the denominator the
    #: quorum silently dropped 2020-12-25 -- which is one of the seven exits this whole
    #: derivation exists to catch. The residual check below is what found it (0 -> 7).
    covered: dict[str, set[str]] = {}
    for sym in wanted:
        key = (sym, AD.TF_H4)
        if key not in sub["series"]:
            continue
        _bars, times = sub["series"][key]
        trades_weekends = any(utc_to_broker_naive(t, rule).weekday() >= 5 for t in times[:5000])
        cov = covered.setdefault(sym, set())
        for t in times:
            cov.add(utc_to_broker_naive(t, rule).date().isoformat())
        n_short = n_wide = 0
        for _wk, close_idx in sub["gapped"][key].items():
            last_close = times[close_idx] + dt.timedelta(minutes=TF_MINUTES[AD.TF_H4])
            sat = next_saturday_midnight_utc(last_close - dt.timedelta(minutes=1), rule)
            gap_h = (sat - last_close).total_seconds() / 3600.0
            if gap_h <= 4.001:
                continue
            if gap_h > _MAX_EARLY_CLOSE_GAP_HOURS:
                n_wide += 1
                continue
            n_short += 1
            d = utc_to_broker_naive(last_close, rule).date()
            end = utc_to_broker_naive(sat, rule).date()
            while d < end:
                votes.setdefault(d.isoformat(), set()).add(sym)
                d += dt.timedelta(days=1)
        per_symbol[sym] = {"early_close_weeks": n_short,
                           "wide_gaps_rejected_as_coverage": n_wide,
                           "trades_weekends": trades_weekends}
        if not trades_weekends:
            voters.append(sym)
    # A symbol votes on a date only if its archive reaches that WEEK at all; a date it has no
    # data for is an abstention, not a "no".
    def _week_covered(sym: str, day: str) -> bool:
        d0 = dt.date.fromisoformat(day)
        return any((d0 + dt.timedelta(days=k)).isoformat() in covered.get(sym, ())
                   for k in range(-6, 1))

    vs = set(voters)
    kept, quorum_detail = [], {}
    for day, ss in sorted(votes.items()):
        elig = [s for s in voters if _week_covered(s, day)]
        need = max(1, int(round(_QUORUM_FRAC * len(elig))))
        yes = len(ss & vs)
        quorum_detail[day] = {"yes": yes, "eligible": len(elig), "need": need}
        if yes >= need:
            kept.append(day)
    need = None
    return {
        "n_symbols": len(per_symbol), "per_symbol": per_symbol,
        "n_voting_symbols": len(voters), "quorum_frac": _QUORUM_FRAC,
        "quorum_detail": {d: quorum_detail[d] for d in kept},
        "max_early_close_gap_hours": _MAX_EARLY_CLOSE_GAP_HOURS,
        "n_candidate_dates": len(votes), "n_dates": len(kept), "dates": kept,
        "definition": ("a week whose last H4 bar closes >1 bar and <=52 h before the broker "
                       "Saturday 00:00 that ends it, on at least 60 % of the symbols that "
                       "never print a weekend bar; the dates are every broker-local day "
                       "between that close and the Saturday"),
        "known_confound": ("bar absence cannot distinguish a market holiday from an archive "
                           "coverage gap. The 52 h ceiling and the quorum are what remove the "
                           "obvious coverage gaps and they will not remove a subtle one. This "
                           "list is a STARTING POINT for the operator's list, never authority: "
                           "the durable fix is capturing the broker's own session table."),
    }


# =====================================================================================
# stage book — the four-sleeve book's p_pass and %/month under each option
# =====================================================================================

#: The arms the owner package prices at book level. `as_walked` is the counterfactual an FTMO
#: account already runs; every other row is what a FUNDED redacted_account account would run.
BOOK_ARMS: tuple[tuple[str, str, float | None, float], ...] = (
    ("as_walked", "calendar", None, 0.0),
    ("flat_calendar_m0", "calendar", 0.0, 0.0),
    ("flat_grid_m0", "grid", 0.0, 0.0),
    ("flat_calendar_m0_embargo_48h", "calendar", 0.0, 48.0),
)
#: Q's two rule sets of record, same as AI used: firm-true phase 1, and both phases (the one
#: that gates a payout).
RULES_OF_RECORD = ("L4_FIRM_TRUE_PH1", "P2_BOTH_PHASES")


def _daily_net_r(sub: dict, sleeve: str, rows: list[dict], *, band: str,
                 population: str | None, oos_only: bool = False) -> dict[str, float]:
    """The day series the gate itself pools: net of broker-true cost, one entry per traded day.

    Construction copied from `phase6/receipts/aa_estate_walk.py:252-284` (`price_trades` ->
    `build_daily_panel`) rather than re-derived, because AI's book-4 composition consumes that
    exact object and a second arithmetic would make the two books differ in more than their arm.

    `oos_only` restricts the series to the fold TEST days -- the days the gate's verdict is
    actually made of. It exists because the estate's MC convention (AI's `archive_daily`, and
    Q's machinery before it) consumes the FULL series including every fold's train days, and on
    `energy_agri` that convention and the gate DISAGREE ON THE SIGN of this policy's effect
    (gate OOS -0.024 R/day, full-series panel +0.397). Publishing one of those without the other
    would be picking the convenient one.
    """
    from src.research_infra.walkforward.folds import assign_folds, build_fold_calendar
    from src.research_infra.walkforward.panel import build_daily_panel, price_trades

    o = OPTIONS[OPTION]
    spec = o.with_(spec_id=f"{o.spec_id}_ba_book", sleeve_symbol_allowlist=sub["allowlist"],
                   spread_band=band)
    recs = {sleeve: AD.to_records(rows)}
    if population:
        recs, spec, _mix = POP.apply(population, recs, spec, account=ACCOUNT, band=band)
    priced, _cov = price_trades(recs[sleeve], spec, costs=sub["costs"])
    daily, _counts = build_daily_panel(priced, spec)
    ser = daily.get(sleeve) or {}
    if oos_only and ser:
        folds = build_fold_calendar(spec, min(ser), max(ser))
        keep = {d for s in assign_folds(priced, ser, folds, spec) if s.status == "evaluable"
                for d in s.test_days}
        ser = {d: v for d, v in ser.items() if d in keep}
    return {d.isoformat(): float(v) for d, v in ser.items()}


def stage_book(sub: dict, *, paths: int = 40_000) -> dict:
    """Compose the armed four at registry confidences and run Q's MC at each firm's rules.

    WHAT THIS IS AND IS NOT. It is the four-sleeve ARCHIVE-population book, so its LEVELS are
    not comparable to `phase8/receipts/BOOKS_MC_V1.json`'s cache-population figures (AI §3.1's
    `p_pass 0.9331 redacted_account` is the armed THREE on the W7 recost caches). Both arms here run
    the same population through the same arithmetic, so the DELTA is the quantity to read and
    the level is context. Stamped as a cross-population composition wherever it appears, the
    same discipline AI applied to its own book 4.
    """
    import statistics as _st

    sys.path.insert(0, str(REPO / "scripts"))
    import mc_firm_rules as Q  # noqa: E402
    from src.components.ultimate_book import admission as P  # noqa: E402

    mx, err = P.resolve_market_expansion_sleeves(
        policy="positive_weighted12_after_swap", explicit_sleeves=())
    if err:
        raise RuntimeError(f"market-expansion policy failed closed: {err}")
    reg = P.effective_registry(include_clean3=True, include_candidate_book=True,
                              include_market_expansion_book=True, market_expansion_sleeves=mx)
    conf = {s: float(reg[s].confidence) for s in ARMED}

    out: dict = {"registry_confidences": conf, "paths": paths,
                 "rules_of_record": list(RULES_OF_RECORD),
                 "population_caveat": (
                     "ARCHIVE population, not the W7 recost caches. Levels are NOT comparable "
                     "to phase8/receipts/BOOKS_MC_V1.json; the delta between arms is."),
                 "arms": {}}
    # `fwd_2025plus` is the window AI's published headline used ("fwd 2025+"), and it is here for
    # a reason that is about arithmetic rather than tidiness: `p_pass` is a bounded, concave
    # function of the daily mean, so a delta measured at p 0.70 is NOT the delta at p 0.93. AI's
    # armed-three figure sits at 0.9172/0.9331; measuring only on the full archive (where this
    # book prices at ~0.70) would OVERSTATE how much p_pass a compliance cost buys back.
    for pop_label, population, since, oos in (
            ("RECORDED", "RECORDED", None, False),
            ("ALL_ERAS", None, None, False),
            ("RECORDED_fwd_2025plus", "RECORDED", "2025-01-01", False),
            ("RECORDED_oos_only", "RECORDED", None, True)):
        for arm, reading, margin, embargo in BOOK_ARMS:
            per_day: dict[str, float] = {}
            detail = {}
            for sleeve in ARMED:
                if arm == "as_walked":
                    rows, _ = AD.resimulate(sub["base"][sleeve], AD.AS_WALKED, sub["series"],
                                            sub["index"], sub["costs"], ACCOUNT, sub["rule"])
                else:
                    rows, _ = resimulate_weekend(sub, sleeve, margin_hours=margin,
                                                 embargo_hours=embargo, reading=reading)
                ser = _daily_net_r(sub, sleeve, rows, band="mid", population=population,
                                   oos_only=oos)
                if since:
                    ser = {d: v for d, v in ser.items() if d >= since}
                w = conf[sleeve]
                for day, v in ser.items():
                    per_day[day] = per_day.get(day, 0.0) + w * v
                detail[sleeve] = {"conf": w, "n_days": len(ser), "n_trades": len(rows),
                                  "mean_net_r_per_day": (round(_st.fmean(ser.values()), 6)
                                                         if ser else None)}
            days = sorted(per_day)
            comb = [per_day[d] for d in days]
            if not comb:
                out["arms"][f"{pop_label}/{arm}"] = {"available": False}
                continue
            a, b = dt.date.fromisoformat(days[0]), dt.date.fromisoformat(days[-1])
            months = (b.year - a.year) * 12 + (b.month - a.month) + 1
            cell = {"book_days": len(days), "risk": Q.DIAL,
                    "weekday_sessions": Q.weekday_sessions(a, b),
                    "book_days_per_calendar_month": len(days) / months,
                    "mean_r_per_book_day": _st.fmean(comb),
                    "worst_day_unit_r": min(comb), "sd_unit_r": _st.pstdev(comb),
                    "window": f"{a.isoformat()}..{b.isoformat()}"}
            res = {}
            for acct in ("FTMO", "redacted_account"):
                rs, firm = Q.rule_sets(acct)
                res[acct] = {"rules": {}}
                for r in rs:
                    if r.label not in RULES_OF_RECORD:
                        continue
                    m = Q.mc(comb, Q.DIAL, r, paths, seed_base=1)
                    res[acct]["rules"][r.label] = {
                        "p_pass": round(m["p_pass"], 6), "se_p_pass": round(m["se_p_pass"], 6),
                        "p_fail_dd": round(m["p_fail_dd"], 6),
                        "p_fail_daily": round(m["p_fail_daily"], 6),
                        "p_timeout": round(m["p_timeout"], 6),
                        **Q._derived(cell, m)}
                    print(f"   {pop_label:8s} {acct:11s} {arm:30s} {r.label:18s} "
                          f"p={m['p_pass']:.5f}", flush=True)
            out["arms"][f"{pop_label}/{arm}"] = {"available": True, "cell": cell,
                                                 "per_sleeve": detail, "accounts": res}
    return out


# =====================================================================================
# substrate
# =====================================================================================

def build_substrate() -> dict:
    t0 = time.time()
    raw = json.load(gzip.open(ESTATE, "rt"))
    base = {s: list(r) for s, r in raw["trades"].items()}
    costs = AD.load_broker_true_costs(AD.COSTS)
    rule = resolve_rule(SERVER)
    series, index, _ = AD.load_bars()
    wc_index = {k: weekend_closes(v[1], rule) for k, v in series.items()}
    gapped = {k: gapped_weekends(v[1], rule) for k, v in series.items()}
    fam = CF.load_candidate_family(FAMILY)
    print(f"substrate in {time.time() - t0:.0f}s: {len(base)} sleeves, "
          f"{len(series)} series, family={getattr(fam, 'family_id', '?')}", flush=True)
    return {"base": base, "meta": {k: v for k, v in raw.items() if k != "trades"},
            "costs": costs, "rule": rule, "series": series, "index": index,
            "wc_index": wc_index, "gapped": gapped,
            "allowlist": AD.allowlist(), "family": fam}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=("census", "flat", "embargo", "identity", "book", "all"))
    ap.add_argument("--no-ledger", action="store_true")
    ap.add_argument("--paths", type=int, default=40_000, help="MC paths for --stage book")
    args = ap.parse_args()

    sub = build_substrate()
    ledger = None if args.no_ledger else TrialLedger(DEFAULT_TRIAL_LEDGER)
    doc = {
        "schema": "gtos.audit.ba.weekend_policy.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "BA", "blocks": "B1900-B1949",
        "source_trades": str(ESTATE.relative_to(REPO)),
        "source_generated_by": sub["meta"].get("generated_by"),
        "bars_archive": AD.BARS, "cost_artifact": str(AD.COSTS.relative_to(REPO)),
        "family_artifact": str(FAMILY.relative_to(REPO)),
        "armed_sleeves": list(ARMED), "population": POPULATION, "option": OPTION,
        "bands": [b if b is not None else "flat_37_day_snapshot" for b in BANDS],
        "cutoffs": {k: v for k, v in CUTOFFS}, "embargo_hours": list(EMBARGOES),
        "headline_cutoff": HEADLINE_CUTOFF,
    }
    t0 = time.time()
    if args.stage in ("census", "all"):
        print("stage census", flush=True)
        doc["census"] = stage_census(sub)
    if args.stage in ("flat", "all"):
        print("stage flat", flush=True)
        doc["flat"] = stage_flat(sub, ledger)
    if args.stage in ("embargo", "all"):
        print("stage embargo", flush=True)
        doc["embargo"] = stage_embargo(sub, ledger)
    if args.stage in ("identity", "all"):
        print("stage identity", flush=True)
        doc["identity"] = stage_identity(sub)
    if args.stage in ("book", "all"):
        print("stage book", flush=True)
        doc["book"] = stage_book(sub, paths=args.paths)
    doc["seconds_by_stage"] = {args.stage: round(time.time() - t0, 1)}

    prev = json.loads(OUT.read_text()) if OUT.is_file() else {}
    # A targeted re-run must not erase the other stages' timings, which is what a plain
    # `update` on a single `seconds_total` key did (it left the artifact claiming a 208-cell
    # gate sweep took 1.4 s, because `--stage identity` ran last).
    merged_secs = {**(prev.get("seconds_by_stage") or {}), **doc["seconds_by_stage"]}
    prev.pop("seconds_total", None)
    prev.update(doc)
    prev["seconds_by_stage"] = merged_secs
    OUT.write_text(json.dumps(prev, indent=1, sort_keys=True, default=str))
    print(f"wrote {OUT.relative_to(REPO)} in "
          f"{doc['seconds_by_stage'][args.stage]}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

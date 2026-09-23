"""The two halves of the entry frontier AH left unpriced: the H4 FX hour-00 subset, and the
sub-four-hour shift the FX D1 cohort's reversion members need.

    python3 .../am_entry_frontier.py h4        # item 2: generate the H4 FX arms
    python3 .../am_entry_frontier.py h4gate    # item 2: judge them
    python3 .../am_entry_frontier.py hourcost  # item 3a: the cost frontier, whole archive
    python3 .../am_entry_frontier.py atrmr     # item 3b: the gross frontier, M15 window
    python3 .../am_entry_frontier.py assemble  # write ENTRY_FRONTIER_H4_V1.json

WHY THE H4 SUBSET IS NOT A REPEAT OF AH
---------------------------------------
AH moved the FX **D1** cohort's entry from the D1 close (broker 00:00, the rollover) to the first
H4 close, and measured +0.063…+0.141 R/trade net depending on how the spread bill is attributed.
Two effects are superposed there and it could not separate them:

  * a **cost** effect — the fill leaves the 13x-38x hour;
  * a **D1 mechanism** effect — a D1 signal is four hours stale at the new fill, and AH measured
    that as −0.015 R/trade of gross, concentrated in `atr_mean_reversion`.

One sixth of an **H4** decision bar's closes land on broker 00 as well (the bar stamped 20:00), and
for those the shift is one bar of the sleeve's OWN timeframe. Running the same arms on that subset
isolates the cost effect: the staleness is one native bar rather than a whole extra timeframe, and
the non-hour-00 five sixths of the SAME members are the control that says how much of any gain is
just "one bar later".

THE CONTROL, WHICH IS THE POINT
-------------------------------
AH's arm B (D1 close, H4 exit) exists because 480 H4 bars and 80 D1 bars are the same 80 trading
days but a finer bar sees a stop the coarser one steps over. **That artifact does not exist here**:
every arm decides on an H4 bar, enters on an H4 close and replays on H4 bars at `maxbars=80`, so the
exit resolution is identical by construction and there is nothing for a resolution control to
measure. What replaces it is the **hour control**: the identical +1-bar and +2-bar shift applied to
the members' non-hour-00 decision bars. If the hour-00 gain is a rollover-cost effect it must be
much larger there than in the control; if the control moves as much, the effect is generic
one-bar-later drift and the rollover has nothing to do with it.

WHAT THE HOUR TABLE ALREADY SAYS, AND WHY ITEM 3 EXISTS
-------------------------------------------------------
`SPREAD_MODEL_V1.json`'s own `intraweek.by_class_hour_of_week` is a **one-hour spike**: on the `fx`
class the hour-of-day medians are 16.67x at broker 00 and **1.333x at broker 01**, 1.0x from 02
onward (`jpy_fx`: 12.56x then 1.167x; metals/index/energy/crypto have no cell above 1.5x anywhere).
So ~94-96 % of the premium a rollover fill pays is removed by a **one-hour** delay, and the
remaining three hours of AH's four-hour shift buy the last few percent while paying three more hours
of signal decay. AH could not price that because the H4 grid has no point between 0 h and 4 h.

The cost half of that frontier needs no bars at all — `cost_r` is a function of the entry INSTANT —
so item 3a prices every hour from 0 h to 8 h over the whole archive, exactly. The gross half needs a
price at the shifted instant, which needs M15 bars, and the M15 archive starts 2024-01-02; item 3b
measures it there and says so rather than extrapolating.

Offline and pure: gzipped CSV bars through `CsvBarSource`, no broker module, no config edit.
"""

from __future__ import annotations

import argparse
import bisect
import collections
import datetime as dt
import gzip
import hashlib
import json
import os
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
AH = REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(AH))

import yaml  # noqa: E402

import ah_entry_gate as AHG  # noqa: E402  — intersect / cost_decomposition / row_of, imported
import ah_entry_shift as AHS  # noqa: E402  — archive access + engine_reachable, imported
from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, TF_M15, WARMUP  # noqa: E402
from src.components.ultimate_book.bar_provider import decision_day_of  # noqa: E402
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import cost_r, load_broker_true_costs  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward import family as fam  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.utils.broker_clock import resolve_rule, utc_to_broker_naive  # noqa: E402

BARS = AHS.BARS
COSTS = AHS.COSTS
SERVER = AHS.SERVER
RULE = resolve_rule(SERVER)
VERDICT_BAND = "mid"

OUT_H4 = HERE / "AM_ENTRY_H4_TRADES.json.gz"
OUT_ATRMR = HERE / "AM_ATRMR_FINE_TRADES.json.gz"
OUT = HERE / "ENTRY_FRONTIER_H4_V1.json"
STAGE_CACHE = HERE / "AM_ENTRY_STAGES.json"

#: The estate's H4 labelling horizon (AA, AF and AK all use 80 in the sleeve's own bars), so
#: every number here is directly comparable to `AF_FAMILY_TRADES.json.gz`.
MAXBARS_H4 = 80
#: `AF_FAMILY_TRADES` for the H4 members. Arm A must reproduce it, member for member.
AF_TRADES = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts/AF_FAMILY_TRADES.json.gz"

#: The three mechanisms AF swept at H4. `volume_surge_reversal` and `atr_mean_reversion` were
#: swept at D1 ONLY, so running them at H4 would add family members (new hypotheses, a higher
#: bill). The H4 arms below are new CELLS of members that already exist.
H4_MECHANISMS = ("donchian_20_breakout", "crypto_h4_donchian_ac60", "energy_fvg_retest")
COHORT_CLASSES = ("fx",)

#: A shifted entry further out than this is a different trade, not a later fill — AH's rule and
#: its number. On the H4 grid the bar that trips it is the Friday-night close (server Sat 00:00),
#: whose next H4 close is Monday 04:00, and it is a member of the hour-00 subset, so the drop is
#: counted per subset rather than assumed away.
MAX_SHIFT_HOURS = 8.0

H4_ARMS = ("A_h4close", "C_h4next", "D_h4second")

#: item 3a: every whole hour from the D1 close out to 8 h. Cost only — no bar is needed.
HOUR_SHIFTS = (0, 1, 2, 3, 4, 5, 6, 7, 8)
#: item 3b: the sub-4-hour frontier on M15, at 1 h steps plus the H4 grid points.
FINE_SHIFT_MINUTES = (0, 60, 120, 180, 240, 480)


# =====================================================================================
# item 2 — the H4 FX cohort
# =====================================================================================

def h4_cohort(res, supports):
    grid = fam.FamilyGrid()
    syms = AHS.archive_symbols()
    for key in H4_MECHANISMS:
        g = fam.family_members([key], (TF_H4,), symbols=syms, broker_symbol=res,
                               classes=COHORT_CLASSES,
                               profile_supports=(supports if callable(supports) else None))
        grid.members.extend(g.members)
        grid.dropped.extend(g.dropped)
    return grid


def _h4_union_close_grid(symbols: set[str]) -> list[dt.datetime]:
    """Every H4 close instant over the whole archive, for reachability.

    Over ALL archive symbols, not just the FX 14, for the same reason AH built its D1 grid that
    way: reachability depends on which symbols share the launcher, so a narrower grid silently
    changes which bars are reachable and breaks the AF parity below.
    """
    files = {}
    import glob
    import os
    for p in sorted(glob.glob(f"{BARS}/FTMO_*_H4.csv.gz")):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, _tf = stem.rpartition("_")
        if sym in AHS.DUPLICATE_ALIASES:
            continue
        files[(sym, TF_H4)] = p
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO-h4grid")
    stamps: set[dt.datetime] = set()
    for key in files:
        for r in src._load(key):
            stamps.add(dt.datetime.fromisoformat(r["time"]))
    return sorted(t + dt.timedelta(minutes=240) for t in stamps)


def generate_h4_member(m, gen, series, warm_cluster: str, reach: set[int]) -> list[dict]:
    h4 = series.get((m.symbol, TF_H4))
    if h4 is None:
        return []
    hbars, htimes = h4
    close_at = [t + dt.timedelta(minutes=240) for t in htimes]
    warm = WARMUP.get(warm_cluster, 200)
    out: list[dict] = []
    for i in range(warm - 1, len(hbars) - 2):
        lo = max(0, i - 259)
        intent = gen(m.symbol, hbars[lo:i + 1], decision_day_of(htimes[i]),
                     bar_time=htimes[i], bar_times=htimes[lo:i + 1],
                     aux_bars=None, aux_times=None, runtime_now=close_at[i])
        if intent is None:
            continue
        d = int(intent.direction)
        sd = float(intent.stop_dist)
        if d not in (1, -1) or not (sd > 0):
            continue
        td = float(intent.target_dist) if intent.target_dist else None
        wall = utc_to_broker_naive(close_at[i], RULE)
        common = {"member": m.member, "symbol": m.broker_symbol,
                  "symbol_canonical": m.symbol, "direction": d,
                  "sl_distance_price": sd, "target_dist": td,
                  "decision_bar_iso": htimes[i].isoformat(),
                  "decision_day": intent.decision_day,
                  "decision_close_utc": close_at[i].isoformat(),
                  "decision_broker_hour": wall.hour,
                  "decision_broker_weekday": wall.weekday(),
                  "engine_reachable": i in reach}
        for arm, step in zip(H4_ARMS, (0, 1, 2)):
            j = i + step
            if j >= len(hbars) - 1:
                out.append({**common, "arm": arm, "dropped": "shifted entry past the archive"})
                continue
            shift = (close_at[j] - close_at[i]).total_seconds() / 3600.0
            if shift > MAX_SHIFT_HOURS:
                out.append({**common, "arm": arm, "dropped":
                            f"next H4 close is {shift:.1f} h after the decision "
                            f"(> {MAX_SHIFT_HOURS} h): a session gap, not a later fill"})
                continue
            pr = replay(hbars, j, d, stop_dist=sd,
                        policy=ExitPolicy(target_dist=td, maxbars=MAXBARS_H4, label="plain"))
            out.append({**common, "arm": arm,
                        "entry_utc": close_at[j].isoformat(),
                        "entry_price": float(hbars[j].c),
                        "entry_broker_hour": utc_to_broker_naive(close_at[j], RULE).hour,
                        "exit_utc": close_at[pr.exit_index].isoformat(),
                        "r_gross": float(winsorize_R(pr.r_gross)),
                        "exit_reason": pr.exit_reason, "mfe_r": round(pr.mfe_r, 6),
                        "mae_r": round(pr.mae_r, 6),
                        "exit_bar_offset": int(pr.exit_index - j),
                        "hold_hours": round((pr.exit_index - j) * 4.0, 4),
                        "entry_shift_hours": round(shift, 4),
                        "entry_slip_price": float(hbars[j].c - hbars[i].c)})
    return out


def parity_vs_af(rows: list[dict]) -> dict:
    """Arm A must BE AF's H4 population, member for member, on count and summed R."""
    with gzip.open(AF_TRADES, "rt") as fh:
        af = json.load(fh)
    mine = collections.defaultdict(list)
    for r in rows:
        if r["arm"] == "A_h4close" and not r.get("dropped"):
            mine[r["member"]].append(r)
    out = {"members_compared": 0, "exact_count": 0, "exact_sum_r": 0, "detail": {}}
    for member, rs in sorted(mine.items()):
        theirs = af["trades"].get(member)
        if theirs is None:
            continue
        out["members_compared"] += 1
        a, b = len(rs), len(theirs)
        sa = round(sum(r["r_gross"] for r in rs), 6)
        sb = round(sum(t["r_gross"] for t in theirs), 6)
        out["exact_count"] += int(a == b)
        out["exact_sum_r"] += int(sa == sb)
        out["detail"][member] = {"n_mine": a, "n_af": b, "sum_r_mine": sa, "sum_r_af": sb}
    return out


def do_h4_generate() -> dict:
    t0 = time.time()
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    supports = getattr(res, "supports", None)
    grid = h4_cohort(res, supports)
    symbols = sorted({m.symbol for m in grid.members})
    print(f"H4 FX cohort: {len(grid.members)} members over {len(symbols)} symbols "
          f"({len(grid.families())} families)")
    series = AHS.load_archive(set(symbols))
    series = {k: v for k, v in series.items() if k[1] == TF_H4}
    print(f"archive: {len(series)} H4 series")
    grid.members = [m for m in grid.members if (m.symbol, TF_H4) in series]

    warm = {k: AHS.warm_cluster_for(s.parent_sleeve) for k, s in fam.MECHANISMS.items()}
    hgrid = _h4_union_close_grid(set(symbols))
    print(f"H4 union grid: {len(hgrid)} closes {hgrid[0].date()}..{hgrid[-1].date()}")

    reach_cache: dict[tuple, set[int]] = {}
    rows: list[dict] = []
    with fam.expanded_surface(grid.members) as gens:
        for k, m in enumerate(grid.members):
            nwarm = WARMUP.get(warm[m.mechanism_key], 200)
            rk = (m.symbol, nwarm)
            if rk not in reach_cache:
                reach_cache[rk] = AHS.engine_reachable(
                    series[(m.symbol, TF_H4)][1], hgrid, dt.timedelta(minutes=240), nwarm)
            rows.extend(generate_h4_member(m, gens[m.member], series,
                                           warm[m.mechanism_key], reach_cache[rk]))
            print(f"  {k+1}/{len(grid.members)} {m.member:52s} rows={len(rows)} "
                  f"({time.time()-t0:.0f}s)", flush=True)

    par = parity_vs_af(rows)
    print(f"parity vs AF: {par['exact_count']}/{par['members_compared']} exact on count, "
          f"{par['exact_sum_r']}/{par['members_compared']} on summed R")
    drops = collections.Counter((r["arm"], r["dropped"].split("(")[0].strip())
                                for r in rows if r.get("dropped"))
    art = {
        "schema": "gtos.am.entry_h4_trades.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "session": "AM", "blocks": "B1200-B1249",
        "bars_archive": BARS, "arms": list(H4_ARMS),
        "maxbars": {"H4": MAXBARS_H4},
        "cohort_classes": list(COHORT_CLASSES),
        "mechanisms": list(H4_MECHANISMS),
        "max_shift_hours": MAX_SHIFT_HOURS,
        "members": sorted({r["member"] for r in rows}),
        "n_rows": len(rows),
        "n_by_arm": dict(collections.Counter(r["arm"] for r in rows if not r.get("dropped"))),
        "arm_drops": {f"{a} | {why}": n for (a, why), n in sorted(drops.items())},
        "parity_vs_af": par,
        "decision_broker_hour_histogram": dict(sorted(collections.Counter(
            r["decision_broker_hour"] for r in rows if r["arm"] == "A_h4close").items())),
        "seconds": round(time.time() - t0, 1),
        "trades": rows,
    }
    with gzip.open(OUT_H4, "wt") as fh:
        json.dump(art, fh)
    print(f"wrote {OUT_H4.relative_to(REPO)} ({OUT_H4.stat().st_size/1e6:.1f} MB) "
          f"in {art['seconds']}s")
    return art


def intersect_h4(rows: list[dict]) -> tuple[dict[str, list[dict]], dict]:
    """AH's intersection rule, on this arm set: every arm produced a trade AND arm A is reachable."""
    by_key: dict[tuple, dict[str, dict]] = collections.defaultdict(dict)
    for r in rows:
        by_key[(r["member"], r["decision_bar_iso"])][r["arm"]] = r
    keep = {k: v for k, v in by_key.items()
            if len(v) == len(H4_ARMS)
            and all(not v[a].get("dropped") for a in H4_ARMS)
            and v["A_h4close"]["engine_reachable"]}
    out = {a: [v[a] for v in keep.values()] for a in H4_ARMS}
    return out, {
        "n_decision_bars_all_arms": len(keep),
        "n_decision_bars_seen": len(by_key),
        "excluded_not_reachable": sum(
            1 for v in by_key.values()
            if len(v) == len(H4_ARMS) and all(not v[a].get("dropped") for a in H4_ARMS)
            and not v["A_h4close"]["engine_reachable"]),
        "excluded_arm_missing_or_dropped": sum(
            1 for v in by_key.values()
            if len(v) != len(H4_ARMS) or any(v[a].get("dropped") for a in H4_ARMS)),
        "counts_are_equal_across_arms": len({len(v) for v in out.values()}) == 1,
    }


def _agg(rows: list[dict], base: list[dict] | None = None) -> dict:
    if not rows:
        return {"n": 0}
    d = {"n": len(rows),
         "mean_r_gross": round(statistics.fmean(r["r_gross"] for r in rows), 6),
         "sum_r_gross": round(sum(r["r_gross"] for r in rows), 3),
         "median_hold_hours": round(statistics.median(r["hold_hours"] for r in rows), 3),
         "mean_mfe_r": round(statistics.fmean(r["mfe_r"] for r in rows), 5),
         "win_frac": round(sum(1 for r in rows if r["r_gross"] > 0) / len(rows), 5),
         "mean_pre_entry_drift_r": round(statistics.fmean(
             (r["entry_slip_price"] * r["direction"]) / r["sl_distance_price"]
             for r in rows), 6),
         "entry_broker_hours": dict(sorted(collections.Counter(
             r["entry_broker_hour"] for r in rows).items())),
         "exit_reasons": dict(collections.Counter(r["exit_reason"] for r in rows))}
    if base:
        d["delta_mean_r_gross_vs_base"] = round(
            d["mean_r_gross"] - statistics.fmean(r["r_gross"] for r in base), 6)
    return d


def do_h4_gate() -> dict:
    """The subsets, the control, the cost split and the member/family verdicts."""
    with gzip.open(OUT_H4, "rt") as fh:
        art = json.load(fh)
    arms, pop = intersect_h4(art["trades"])
    print(f"intersected: {pop['n_decision_bars_all_arms']} decision bars "
          f"(equal across arms: {pop['counts_are_equal_across_arms']})")

    # --- the two subsets, split on the arm-A ENTRY hour (the decision bar's close) ----------
    a = arms["A_h4close"]
    hour00 = {(r["member"], r["decision_bar_iso"]) for r in a if r["entry_broker_hour"] == 0}
    subsets = {
        "hour00": {arm: [r for r in arms[arm]
                         if (r["member"], r["decision_bar_iso"]) in hour00] for arm in H4_ARMS},
        "control_other_hours": {arm: [r for r in arms[arm]
                                      if (r["member"], r["decision_bar_iso"]) not in hour00]
                                for arm in H4_ARMS},
        "all": arms,
    }
    for name, s in subsets.items():
        print(f"  subset {name:20s} n={len(s['A_h4close'])}")

    costs = load_broker_true_costs(COSTS)
    cost_sha = hashlib.sha256(COSTS.read_bytes()).hexdigest()

    out: dict = {
        "population": pop,
        "parity_vs_af": art["parity_vs_af"],
        "arm_drops": art["arm_drops"],
        "decision_broker_hour_histogram": art["decision_broker_hour_histogram"],
        "subsets": {},
    }
    for name, s in subsets.items():
        base = s["A_h4close"]
        agg = {arm: _agg(s[arm], base if arm != "A_h4close" else None) for arm in H4_ARMS}
        dec = {arm: AHG.cost_decomposition(s[arm], costs, "v2_damped", sample=5)
               for arm in H4_ARMS}
        # AH §3.1's two attributions. `cost_r` charges one full crossing at `entry_utc`, so the
        # exit half of the bill does not move with the entry and crediting the shift with 100 %
        # of it is a ceiling. `half_at_each` charges half at entry and half at the exit instant.
        half = {arm: AHG.cost_decomposition(
            [{**r, "entry_utc": r["exit_utc"]} for r in s[arm]], costs, "v2_damped", sample=5)
            for arm in H4_ARMS}
        out["subsets"][name] = {
            "n": len(base),
            "aggregate": agg,
            "cost_decomposition_model_convention": dec,
            "cost_decomposition_at_the_exit_instant": half,
            "saving_model_convention_r": {
                arm: round(dec["A_h4close"]["mean_r"]["total_r"] - dec[arm]["mean_r"]["total_r"], 6)
                for arm in H4_ARMS[1:]},
            "saving_half_at_each_r": {
                arm: round(0.5 * (dec["A_h4close"]["mean_r"]["spread_r"]
                                  - dec[arm]["mean_r"]["spread_r"]), 6)
                for arm in H4_ARMS[1:]},
            "net_delta_model_convention_r": {
                arm: round(agg[arm]["delta_mean_r_gross_vs_base"]
                           + dec["A_h4close"]["mean_r"]["total_r"]
                           - dec[arm]["mean_r"]["total_r"], 6)
                for arm in H4_ARMS[1:]},
        }

    # --- the verdicts, on the hour-00 subset, per member and per family --------------------
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    supports = getattr(res, "supports", None)
    members = sorted({r["member"] for r in arms["A_h4close"]})
    fam_of = {m: f"fam_{m[len('mxf_'):].rsplit('_', 2)[0]}_fx_h4" for m in members}
    families = sorted(set(fam_of.values()))
    allow_member = {m: (next(r["symbol"] for r in arms["A_h4close"] if r["member"] == m),)
                    for m in members}
    allow_family = {f: tuple(sorted({r["symbol"] for r in arms["A_h4close"]
                                     if fam_of[r["member"]] == f})) for f in families}
    grid_members = [m for m in h4_cohort(res, supports).members if m.member in fam_of]
    nt = measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])
    #: AF's 276 + AH's 180 + this session's grid: 3 arms x (42 members + 3 families) x 2 subsets.
    declared = AHG.AF_LOOKS + AHG.AH_LOOKS + 3 * (len(members) + len(families)) * 2
    print(f"declared_family_size {declared} = AF {AHG.AF_LOOKS} + AH {AHG.AH_LOOKS} + "
          f"AM {3 * (len(members) + len(families)) * 2}")

    runs: dict[str, dict] = {}
    for sub in ("hour00", "control_other_hours"):
        for arm in H4_ARMS:
            by_member = collections.defaultdict(list)
            for r in subsets[sub][arm]:
                by_member[r["member"]].append(r)
            recs_member = {m: AHG.to_records(v) for m, v in by_member.items()}
            pooled = {f: [t for m in members if fam_of[m] == f
                          for t in AHG.to_records(by_member[m], sleeve=f)] for f in families}
            for scope, trades, allow in (("member", recs_member, allow_member),
                                         ("family", pooled, allow_family)):
                spec = OPTIONS["C_exploratory"].with_(
                    spec_id=f"C_exploratory_am_h4_{sub}_{arm}_{scope}",
                    spread_band=VERDICT_BAND, spread_composition="v2_damped",
                    cost_artifact_sha256=cost_sha, declared_family_size=declared,
                    n_trials=int(nt["n_trials"]),
                    n_trials_basis=f"MEASURED from {DEFAULT_TRIAL_LEDGER} -- {nt.get('basis')}",
                    sleeve_symbol_allowlist=allow)
                with fam.fidelity_scope(grid_members):
                    r = run_gate(trades, spec, costs=costs, server=SERVER)
                runs[f"{sub}|{arm}|{scope}"] = {
                    "subset": sub, "arm": arm, "scope": scope,
                    "spec_sha256": spec.seal(), "admitted": r.admitted,
                    "rejected_n": len(r.rejected), "not_evaluable_n": len(r.not_evaluable),
                    "rows": {s: AHG.row_of(s, v) for s, v in sorted(r.verdicts.items())}}
                print(f"  {sub}|{arm}|{scope:6s} ADMIT {len(r.admitted):2d} "
                      f"REJECT {len(r.rejected):3d} N/E {len(r.not_evaluable):2d}", flush=True)

    per_member = {}
    for m in members:
        rec = {"member": m, "symbol": allow_member[m][0]}
        for sub in ("hour00", "control_other_hours"):
            for arm in H4_ARMS:
                rr = [r for r in subsets[sub][arm] if r["member"] == m]
                row = runs[f"{sub}|{arm}|member"]["rows"].get(m) or {}
                rec[f"{sub}|{arm}"] = {
                    "n": len(rr),
                    "mean_r_gross": (round(statistics.fmean(r["r_gross"] for r in rr), 6)
                                     if rr else None),
                    "pooled_oos_mean_r": row.get("pooled_oos_mean_r"),
                    "verdict": row.get("verdict"), "p_raw": row.get("p_raw"),
                    "blocking_gate": row.get("first_reason"),
                }
        per_member[m] = rec
    # The bill is 726 looks and nothing will admit at it; the p-values are what carry information,
    # so the whole multiplicity surface is published rather than one number's verdict. Same
    # instrument AI used to make `declared_family_size` an owner decision instead of a typed int.
    from src.research_infra.walkforward import candidate_family as CF  # noqa: PLC0415
    best = None
    for m in members:
        for sub in ("hour00", "control_other_hours"):
            for arm in H4_ARMS:
                pr = (runs[f"{sub}|{arm}|member"]["rows"].get(m) or {}).get("p_raw")
                if pr is not None and (best is None or pr < best[0]):
                    best = (pr, m, sub, arm)
    sens = {}
    if best:
        sens = {"best_cell": {"p_raw": best[0], "member": best[1], "subset": best[2],
                              "arm": best[3]},
                "sensitivity": CF.sensitivity(best[0], (32, 69, 276, 456, declared)),
                "max_family_that_admits": {str(a): CF.max_size_that_admits(best[0], a)
                                           for a in (0.05, 0.10, 0.20)}}
        print(f"  best raw p in the grid: {best[0]:.5f} ({best[1]} {best[2]} {best[3]})")

    out.update({"runs": runs, "per_member": per_member, "multiplicity_sensitivity": sens,
                "multiplicity": {"declared_family_size": declared,
                                 "af_looks": AHG.AF_LOOKS, "ah_looks": AHG.AH_LOOKS,
                                 "am_looks": 3 * (len(members) + len(families)) * 2,
                                 "n_trials": int(nt["n_trials"]),
                                 "n_trials_basis": nt.get("basis"),
                                 "note": ("the H4 arms are new CELLS of AF's existing H4 members, "
                                          "so no family MEMBER is added; the looks are counted")},
                "cost_artifact": {"path": str(COSTS.relative_to(REPO)), "sha256": cost_sha}})

    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AM")
    for m in members:
        for sub in ("hour00", "control_other_hours"):
            for arm in H4_ARMS:
                cell = per_member[m][f"{sub}|{arm}"]
                ledger.record(
                    mechanism=m[len("mxf_"):].rsplit("_", 2)[0], sleeve=m,
                    variant={"entry_arm": arm, "timeframe": "H4", "subset": sub,
                             "spread_composition": "v2_damped",
                             "declared_family_size": declared, "verdict_band": VERDICT_BAND},
                    window="2000-03..2026-07 (whole FX H4 archive)",
                    outcome=("negative" if (cell["mean_r_gross"] or 0) < 0 else "positive"),
                    metric=cell.get("pooled_oos_mean_r"), metric_name="pooled_oos_mean_r",
                    spec_sha256=runs[f"{sub}|{arm}|member"]["spec_sha256"],
                    note="AM B1210 — H4 FX entry shift, hour-00 subset against its own control")
    print(f"ledger: {ledger.n_written} rows, {ledger.write_errors} errors")
    return out


# =====================================================================================
# item 3a — the cost frontier by entry hour, over the whole archive
# =====================================================================================

def do_hour_cost() -> dict:
    """Re-price AH's own D1 arm-B trades at every whole-hour shift from 0 h to 8 h.

    Cost only, and that is not a limitation here: `cost_r` is a function of the entry INSTANT, the
    hold and the geometry, so shifting the entry by `h` hours and shortening the hold by the same
    `h` is an EXACT re-pricing — no bar, no extrapolation, whole archive. The gross half needs a
    price at the shifted instant and is item 3b.
    """
    # AH's INTERSECTED population, not merely its reachable arm-B rows: the shift-0 level must
    # reproduce AH's own published arm-B cost (0.2327 R) exactly, and it only does on the same
    # trades. The first version of this stage priced 17,888 rows against AH's 16,337 and came out
    # 6.5 % low — a population difference reading as a cost difference.
    art = AHG.load()
    arms, pop = AHG.intersect(art)
    rows = arms["B_d1close_h4exit"]
    print(f"AH intersected arm-B population: {len(rows)} trades "
          f"(AH published {pop['n_decision_bars_all_arms']} decision bars)")
    # Three level defects in this construction, all INHERITED from `ah_entry_gate.cost_decomposition`
    # and all measured by an adversarial pass (B1224). None of them moves the FRACTION, which is why
    # the headline is a fraction — but each moves the R, so they are named rather than left implicit:
    #   1. `side` is never passed to `cost_r`, so every row is priced LONG while 7,354 of 16,337
    #      (45.0 %) are direction -1. Correctly sided, mean swap 0.01584 -> 0.02417 (+52.6 %) and the
    #      shift-0 level 0.2332 -> 0.2415; the fraction stays 0.94404.
    #   2. slippage is hour-blind by construction (`model.py:484-489`, a flat `value_r`) and is
    #      0.0194 R = 12.4 % of the best saving — exactly the term a rollover fill should pay extra
    #      of. The model has no hour-dependent slippage, so the rollover premium here is spread-only.
    #   3. `hold = max(0.0, hold - shift)` clamps 129 rows (0.79 %, min hold 4.0 h) whose shifted
    #      entry lands after their exit at shifts >= 5 h. Numerically inert: dropping them moves the
    #      fraction 0.94404 -> 0.94393.
    costs = load_broker_true_costs(COSTS)
    mech_of = {r["member"]: r["member"][len("mxf_"):].rsplit("_", 2)[0] for r in rows}

    comp = os.environ.get("AM_COMPOSITION") or "v2_damped"

    def bill(r, shift_h: int):
        entry = dt.datetime.fromisoformat(r["entry_utc"]) + dt.timedelta(hours=shift_h)
        hold = max(0.0, float(r["hold_hours"]) - shift_h)
        b = cost_r(r["symbol"], "FTMO", hold, sl_distance_price=r["sl_distance_price"],
                   entry_price=r["entry_price"], entry_utc=entry,
                   spread_band=VERDICT_BAND, spread_composition=comp, costs=costs)
        return b

    per_shift: dict[str, dict] = {}
    per_mech: dict[str, dict] = collections.defaultdict(dict)
    for sh in HOUR_SHIFTS:
        tot, spr, swp, unpriced = [], [], [], collections.Counter()
        by_mech = collections.defaultdict(list)
        for r in rows:
            try:
                b = bill(r, sh)
            except Exception as e:                                       # noqa: BLE001
                unpriced[type(e).__name__] += 1
                continue
            tot.append(b.total_r.value)
            spr.append(b.spread_r.value)
            swp.append(b.swap_r.value)
            by_mech[mech_of[r["member"]]].append(b.total_r.value)
        per_shift[str(sh)] = {
            "n_priced": len(tot), "unpriced": dict(unpriced),
            "mean_total_r": round(statistics.fmean(tot), 6),
            "mean_spread_r": round(statistics.fmean(spr), 6),
            "mean_swap_r": round(statistics.fmean(swp), 6),
            "broker_hour_of_entry": dict(sorted(collections.Counter(
                utc_to_broker_naive(dt.datetime.fromisoformat(r["entry_utc"])
                                    + dt.timedelta(hours=sh), RULE).hour
                for r in rows).items())),
        }
        for mech, v in by_mech.items():
            per_mech[mech][str(sh)] = round(statistics.fmean(v), 6)
        print(f"  shift {sh}h: mean cost {per_shift[str(sh)]['mean_total_r']:.6f} R "
              f"(spread {per_shift[str(sh)]['mean_spread_r']:.6f}, "
              f"swap {per_shift[str(sh)]['mean_swap_r']:.6f})", flush=True)

    base = per_shift["0"]["mean_total_r"]
    saving = {k: round(base - v["mean_total_r"], 6) for k, v in per_shift.items()}
    # Normalised against the BEST shift on the grid, not against the last one: the frontier is not
    # monotone (8 h lands back on a session-open premium), so `saving[8h]` is the wrong denominator
    # and using it would understate how much of the achievable saving 1 h already buys.
    best_shift = max(saving, key=lambda k: saving[k])
    frac = {k: (round(saving[k] / saving[best_shift], 5) if saving[best_shift] else None)
            for k in per_shift}
    from src.costs.spread_model import PREMIUM_FLOOR, load_spread_model
    sm = load_spread_model()
    iw = sm.doc["intraweek"]["FTMO"]["by_class_hour_of_week"]
    hour_profile = {}
    for cls, t in iw.items():
        prof = collections.defaultdict(list)
        for k, v in t.items():                    # keys are hour-of-week indices, sparse
            prof[int(k) % 24].append(v)
        hour_profile[cls] = {str(h): round(statistics.median(prof[h]), 4)
                             for h in sorted(prof) if h <= 8}
    return {
        "what": ("the exact cost frontier by entry hour on AH's own arm-B population: 1 h of delay "
                 "against 4 h and 8 h, with the hold shortened by the same amount"),
        "spread_composition": comp,
        "attribution_note": (
            "`cost_r` charges one full crossing at `entry_utc` (`model.py:403`, `:439`), so these "
            "levels are AH §3.1's `model_convention` CEILING. Under `half_at_each` every level and "
            "every saving halves — and the FRACTION of the achievable saving that 1 h captures is "
            "unchanged, because both numerator and denominator scale together. That is why the "
            "headline here is a fraction and not an R."),
        "population": {"source": str(AHS.OUT_TRADES.relative_to(REPO)),
                       "arm": "B_d1close_h4exit", "n": len(rows),
                       "basis": "AH's own intersected population (ah_entry_gate.intersect)",
                       "why_arm_B": ("it is the entry AH's arm C is measured against, so the "
                                     "saving here is on the same baseline as AH's +0.1567 R"),
                       "parity_control": ("shift 0 must reproduce AH's published arm-B mean cost of "
                                          "0.2327 R (v2_damped, mid band); it is the check that "
                                          "this frontier prices AH's trades and not a superset")},
        "per_shift": per_shift,
        "saving_vs_shift_0_r": saving,
        "best_shift_hours": int(best_shift),
        "fraction_of_the_best_achievable_saving": frac,
        "per_mechanism_mean_total_r": {k: dict(v) for k, v in per_mech.items()},
        "hour_of_day_multiplier_medians": hour_profile,
        "premium_floor": PREMIUM_FLOOR,
        "why_it_matters": ("the fx hour term is a ONE-HOUR spike (16.67x at broker 00, 1.333x at "
                           "01, 1.0 from 02), so almost all of the rollover premium is removed by "
                           "a one-hour delay. AH could not price that: the H4 grid has no point "
                           "between 0 h and 4 h."),
    }


# =====================================================================================
# item 3b — the sub-4-hour gross frontier on M15, for the reversion members
# =====================================================================================

def _load_m15(symbols: set[str]) -> dict:
    """M15 series for `symbols`, through the production loader so the broker->UTC seam is shared."""
    import glob as _glob
    import os as _os
    files: dict[tuple[str, int], str] = {}
    for pth in sorted(_glob.glob(f"{BARS}/FTMO_*_M15.csv.gz")):
        stem = _os.path.basename(pth)[len("FTMO_"):-len(".csv.gz")]
        sym, _, _tf = stem.rpartition("_")
        if sym in symbols:
            files[(sym, TF_M15)] = pth
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO-m15")
    out = {}
    for key in files:
        rows = src._load(key)
        if not rows:
            continue
        out[key] = ([Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
                     for r in rows],
                    [dt.datetime.fromisoformat(r["time"]) for r in rows])
    return out


def do_atrmr_fine() -> dict:
    """The gross frontier at 1 h resolution, on M15 bars, for the members AH's +4 h shift hurt.

    Scope is stated rather than hidden: the M15 archive starts 2024-01-02, so this is a 2.6-year
    window against the D1 cohort's 26 years, and the whole population is `atr_mean_reversion` and
    `volume_surge_reversal` x the 14 FX symbols. The exit is replayed on M15 bars for EVERY arm
    including shift 0, so the exit resolution is constant and the only thing moving is the entry —
    the same discipline AH's arm B enforces one timeframe coarser.
    """
    if OUT_ATRMR.is_file() and not os.environ.get("AM_REGENERATE"):
        with gzip.open(OUT_ATRMR, "rt") as fh:
            cached = json.load(fh)
        print(f"reusing {OUT_ATRMR.name}: {len(cached['trades'])} rows "
              f"(set AM_REGENERATE=1 to re-walk)")
        return _atrmr_summary(cached["trades"], cached["shift_minutes"], cached["maxbars_m15"])

    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    supports = getattr(res, "supports", None)
    grid = fam.FamilyGrid()
    for key in ("atr_mean_reversion", "volume_surge_reversal"):
        g = fam.family_members([key], (TF_D1,), symbols=AHS.archive_symbols(),
                               broker_symbol=res, classes=COHORT_CLASSES,
                               profile_supports=(supports if callable(supports) else None))
        grid.members.extend(g.members)
    symbols = sorted({m.symbol for m in grid.members})
    # `AHS.load_archive` maps only D1 and H4 (`ah_entry_shift.py`: `{"D1": ..., "H4": ...}.get(tfs)`),
    # so it silently returns nothing for M15 — the first run of this stage reported "0 M15 series"
    # and would have published an empty frontier. Loaded here through the same `CsvBarSource` seam.
    series = AHS.load_archive(set(symbols))
    m15 = _load_m15(set(symbols))
    print(f"fine frontier: {len(grid.members)} members, {len(m15)} M15 series")
    if not m15:
        raise RuntimeError("no M15 series loaded — refusing to publish an empty fine frontier")
    #: 80 D1 bars is 80 trading days; on M15 that is 80 x 6 x 16 = 7,680 bars. Held identical
    #: across arms, so the horizon is the same wall-clock span at every shift.
    maxbars_m15 = 80 * 6 * 16

    warm = {k: AHS.warm_cluster_for(s.parent_sleeve) for k, s in fam.MECHANISMS.items()}
    d1grid = [t + dt.timedelta(minutes=1440) for t in AHS._all_d1_times()]
    rows: list[dict] = []
    with fam.expanded_surface(grid.members) as gens:
        for m in grid.members:
            d1 = series.get((m.symbol, TF_D1))
            mm = m15.get((m.symbol, TF_M15))
            if d1 is None or mm is None:
                continue
            dbars, dtimes = d1
            mbars, mtimes = mm
            mclose = [t + dt.timedelta(minutes=15) for t in mtimes]
            nwarm = WARMUP.get(warm[m.mechanism_key], 200)
            reach = AHS.engine_reachable(dtimes, d1grid, dt.timedelta(minutes=1440), nwarm)
            gen = gens[m.member]
            for i in range(nwarm - 1, len(dbars) - 2):
                close_at = dtimes[i] + dt.timedelta(minutes=1440)
                if close_at < mclose[0] or close_at > mclose[-1]:
                    continue
                lo = max(0, i - 259)
                intent = gen(m.symbol, dbars[lo:i + 1], decision_day_of(dtimes[i]),
                             bar_time=dtimes[i], bar_times=dtimes[lo:i + 1],
                             aux_bars=None, aux_times=None, runtime_now=close_at)
                if intent is None:
                    continue
                d, sd = int(intent.direction), float(intent.stop_dist)
                if d not in (1, -1) or not (sd > 0):
                    continue
                td = float(intent.target_dist) if intent.target_dist else None
                for shift in FINE_SHIFT_MINUTES:
                    want = close_at + dt.timedelta(minutes=shift)
                    j = bisect.bisect_left(mclose, want)
                    if j >= len(mbars) - 1 or mclose[j] != want:
                        continue          # no M15 close at that instant (holiday truncation)
                    pr = replay(mbars, j, d, stop_dist=sd,
                                policy=ExitPolicy(target_dist=td, maxbars=maxbars_m15,
                                                  label="plain"))
                    rows.append({
                        "member": m.member, "mechanism": m.mechanism_key,
                        "symbol": m.broker_symbol, "symbol_canonical": m.symbol,
                        "direction": d, "sl_distance_price": sd, "target_dist": td,
                        "decision_bar_iso": dtimes[i].isoformat(),
                        "shift_minutes": shift,
                        "entry_utc": want.isoformat(),
                        "entry_price": float(mbars[j].c),
                        "entry_broker_hour": utc_to_broker_naive(want, RULE).hour,
                        "exit_utc": mclose[pr.exit_index].isoformat(),
                        "r_gross": float(winsorize_R(pr.r_gross)),
                        "exit_reason": pr.exit_reason,
                        "mfe_r": round(pr.mfe_r, 6), "mae_r": round(pr.mae_r, 6),
                        "hold_hours": round((pr.exit_index - j) * 0.25, 4),
                        "entry_slip_price": float(mbars[j].c - dbars[i].c),
                        "engine_reachable": i in reach,
                    })
            print(f"  {m.member:52s} rows={len(rows)}", flush=True)

    with gzip.open(OUT_ATRMR, "wt") as fh:
        json.dump({"schema": "gtos.am.atrmr_fine_trades.v1", "trades": rows,
                   "maxbars_m15": maxbars_m15,
                   "shift_minutes": list(FINE_SHIFT_MINUTES)}, fh)
    return _atrmr_summary(rows, list(FINE_SHIFT_MINUTES), maxbars_m15)


def _atrmr_summary(rows: list[dict], shift_minutes: list[int], maxbars_m15: int) -> dict:
    # intersect: a decision bar counts only if EVERY shift produced a trade and it is reachable
    by_key: dict[tuple, dict[int, dict]] = collections.defaultdict(dict)
    for r in rows:
        by_key[(r["member"], r["decision_bar_iso"])][r["shift_minutes"]] = r
    keep = {k: v for k, v in by_key.items()
            if len(v) == len(shift_minutes) and v[0]["engine_reachable"]}
    costs = load_broker_true_costs(COSTS)
    per_shift: dict[str, dict] = {}
    per_member: dict[str, dict] = collections.defaultdict(dict)
    for sh in shift_minutes:
        rs = [v[sh] for v in keep.values()]
        if not rs:
            continue
        dec = AHG.cost_decomposition(rs, costs, "v2_damped", sample=1)
        per_shift[str(sh)] = {
            "n": len(rs),
            "mean_r_gross": round(statistics.fmean(r["r_gross"] for r in rs), 6),
            "mean_cost_r": round(dec["mean_r"]["total_r"], 6),
            "mean_net_r": round(statistics.fmean(r["r_gross"] for r in rs)
                                - dec["mean_r"]["total_r"], 6),
            "mean_pre_entry_drift_r": round(statistics.fmean(
                (r["entry_slip_price"] * r["direction"]) / r["sl_distance_price"]
                for r in rs), 6),
            "median_hold_hours": round(statistics.median(r["hold_hours"] for r in rs), 3),
            "entry_broker_hours": dict(sorted(collections.Counter(
                r["entry_broker_hour"] for r in rs).items())),
        }
        for mech in ("atr_mean_reversion", "volume_surge_reversal"):
            sub = [r for r in rs if r["mechanism"] == mech]
            if sub:
                # Cost per mechanism as well as gross: the pooled net optimum is carried by one of
                # the two mechanisms and the gross-only split could not show that.
                d2 = AHG.cost_decomposition(sub, costs, "v2_damped", sample=1)
                g = statistics.fmean(r["r_gross"] for r in sub)
                per_member[mech][str(sh)] = {
                    "n": len(sub),
                    "mean_r_gross": round(g, 6),
                    "mean_cost_r": round(d2["mean_r"]["total_r"], 6),
                    "mean_net_r": round(g - d2["mean_r"]["total_r"], 6),
                    "mean_pre_entry_drift_r": round(statistics.fmean(
                        (r["entry_slip_price"] * r["direction"]) / r["sl_distance_price"]
                        for r in sub), 6)}
        print(f"  shift {sh:4d}m n={len(rs)} gross {per_shift[str(sh)]['mean_r_gross']:+.6f} "
              f"cost {per_shift[str(sh)]['mean_cost_r']:.6f} "
              f"net {per_shift[str(sh)]['mean_net_r']:+.6f}", flush=True)
    return {
        "what": ("the sub-4-hour entry frontier for the reversion mechanisms, at 1 h resolution, "
                 "on the intersected population where every shift produced a trade"),
        "scope_cap": ("the M15 archive begins 2024-01-02, so this is a 2.6-year window against the "
                      "D1 cohort's 26 years. It is the ONLY window in which a sub-H4 entry price "
                      "exists on this machine; the cost half of the same frontier is exact over "
                      "the whole archive (see `hour_cost_frontier`)."),
        "exit_resolution": ("M15 for every arm including shift 0, maxbars 7,680 = 80 trading days, "
                            "so the exit resolution is constant and only the entry moves"),
        "maxbars_m15": maxbars_m15,
        "shift_minutes": list(shift_minutes),
        "n_decision_bars_all_shifts": len(keep),
        "n_decision_bars_seen": len(by_key),
        "best_net_shift_minutes": (max(per_shift, key=lambda k: per_shift[k]["mean_net_r"])
                                   if per_shift else None),
        "per_shift": per_shift,
        "per_mechanism": {k: dict(v) for k, v in per_member.items()},
    }


# =====================================================================================
# main
# =====================================================================================

def _cache_put(key: str, val) -> None:
    d = json.loads(STAGE_CACHE.read_text()) if STAGE_CACHE.is_file() else {}
    d[key] = val
    STAGE_CACHE.write_text(json.dumps(d, default=str))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("h4", "h4gate", "hourcost", "atrmr", "assemble", "all"))
    a = ap.parse_args()
    if a.stage in ("h4", "all"):
        do_h4_generate()
    if a.stage in ("h4gate", "all"):
        _cache_put("h4", do_h4_gate())
    if a.stage in ("hourcost", "all"):
        for _comp in ("v2_damped", "v1_multiplicative"):
            os.environ["AM_COMPOSITION"] = _comp
            key = ("hour_cost_frontier" if _comp == "v2_damped"
                   else "hour_cost_frontier_v1_multiplicative")
            print(f"--- composition {_comp} ---")
            _cache_put(key, do_hour_cost())
    if a.stage in ("atrmr", "all"):
        _cache_put("reversion_fine_frontier", do_atrmr_fine())
    if a.stage in ("assemble", "all"):
        d = json.loads(STAGE_CACHE.read_text())
        doc = {
            "schema": "gtos.am.entry_frontier_h4.v1",
            "generated_by": str(Path(__file__).relative_to(REPO)),
            "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "session": "AM", "blocks": "B1210-B1229",
            "concatenates_with": str((AH / "ENTRY_HOUR_FRONTIER_V1.json").relative_to(REPO)),
            "arms": {
                "A_h4close": ("entry at the decision H4 bar's own close; exit on H4 bars, "
                              "maxbars 80. AF's H4 population exactly."),
                "C_h4next": "entry at the NEXT H4 close (+4 h); same exit resolution.",
                "D_h4second": "entry at the second H4 close (+8 h). Sensitivity.",
            },
            "why_no_resolution_control": (
                "AH's arm B exists because 480 H4 bars and 80 D1 bars are the same span at "
                "different resolution. Here every arm decides on an H4 bar, enters on an H4 close "
                "and replays on H4 bars at maxbars 80, so there is no resolution difference to "
                "control for. Its place is taken by the HOUR control: the same shifts on the "
                "members' non-hour-00 decision bars."),
            "h4_hour00_subset": d.get("h4"),
            "hour_cost_frontier": d.get("hour_cost_frontier"),
            "hour_cost_frontier_v1_multiplicative": d.get("hour_cost_frontier_v1_multiplicative"),
            "reversion_fine_frontier": d.get("reversion_fine_frontier"),
        }
        OUT.write_text(json.dumps(doc, indent=1, default=str))
        print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

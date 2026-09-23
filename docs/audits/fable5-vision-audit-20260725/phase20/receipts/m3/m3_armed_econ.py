"""m3-4 — what the correction does to the ARMED book's economics, and to `p_pass`.

    python3 .../m3/m3_armed_econ.py --paths 200000

THE ARMED SET IS READ FROM THE LAUNCHER, NOT TYPED
---------------------------------------------------
`scripts/run_book_supervisor.ps1:86` (FTMO) and `:87` (redacted_account) carry the `--tags` lists.
Three wave-20 artifacts declare a four-sleeve ARMED set that omits `sub_mid_dn_revert` and
includes `mx_btcusd_d1_donchian_20_breakout`; lane v1 established the first is wrong (it is
armed on both accounts) and the second is stale (the owner disarmed it on FTMO 2026-08-05,
host `2fa77722d`, D-2 CLOSED). This file parses the launcher and publishes both readings.

WHAT IS MEASURED
----------------
Per sleeve, per band, on the ARCHIVE population (AA's own walk, the gate's own input):

  * gross R/trade and R/day, published convention vs corrected
  * NET R/day at broker truth, with the spread term handled two ways (see below)
  * a day-block bootstrap on the daily net series
  * `p_pass` at each firm's MEASURED rules, phase 1 and both phases, through Session Q's
    `mc_firm_rules` — imported, not reimplemented

THE COST CONVENTION, STATED ONCE
---------------------------------
`costs.model.cost_r` charges one full spread as a level on every trade. Under FILL anchoring
the corrected walk has already transacted across the book, so that charge is the same money
twice (lane r1, `R1_ESTATE_NET_V1.json`). Both are published:

    net_published   r_old  - (commission + swap + spread + slippage)
    net_corrected   r_new  - (commission + swap +          slippage)
    net_double      r_new  - (commission + swap + spread + slippage)   [conservative bound]

`p_pass` is run on `net_corrected` and on `net_published`, so the move is attributable.

WHAT THIS FILE DOES NOT CLAIM
------------------------------
The published `p_pass 0.9172 / 0.9331` figures come from the **W7 recost caches**, a
different population from AA's archive walk. Nothing here restates those; it restates the
ARCHIVE-population MC, which is the one AI itself published as the same-population control
(`ai_books_mc.py -> run_archive_book`) and the only one whose inputs this lane has corrected.
Every row is stamped `population: ARCHIVE`.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import datetime as dt
import gzip
import json
import math
import re
import statistics
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))
_p = sys.path[:]
try:
    sys.path[:] = [str(REPO)]
    import research.operations  # noqa: F401
finally:
    sys.path[:] = _p
sys.path.insert(0, str(REPO / "scripts"))

import mc_firm_rules as Q  # noqa: E402

sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"))
import ad_exit_sweep as AD  # noqa: E402

from src.components.ultimate_book import admission as P  # noqa: E402
from src.costs import load_broker_true_costs  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import (  # noqa: E402
    build_daily_panel,
    price_trades,
)

SUB = HERE / "M3_SUBSTRATE_V1.json.gz"
LAUNCHER = REPO / "scripts/run_book_supervisor.ps1"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
OUT = HERE / "M3_ARMED_ECON_V1.json"

BANDS = ("low", "mid", "high")
ARMS = {"old": None, "qs_low": "low", "qs_mid": "mid", "qs_high": "high"}


def armed_from_launcher() -> dict:
    """The `--tags` lists, parsed out of the committed launcher."""
    txt = LAUNCHER.read_text()
    out = {}
    for m in re.finditer(r'ns="([^"]+)".*?tags="([^"]*)"', txt, re.S):
        ns, tags = m.group(1), m.group(2)
        out[ns] = [t for t in tags.split(",") if t]
    return out


def to_records(rows):
    return AD.to_records(rows)


def price(rows, band, *, charge_spread: bool, costs, allow) -> tuple[dict, dict]:
    """Daily net-R, built by the GATE'S OWN pricer.

    `walkforward.panel.price_trades` is used rather than a local `cost_r` loop so the
    blackout drops, the implausible-stop refusal and the coverage bookkeeping are the
    verdict's own, not a second implementation of them. `components` is what makes the
    spread separable without patching anything.
    """
    spec = OPTIONS["B_balanced"].with_(account="FTMO", spread_band=band,
                                       sleeve_symbol_allowlist=allow)
    priced, cov = price_trades(to_records(rows), spec, costs=costs)
    tel = collections.Counter()
    comp = collections.defaultdict(float)
    adj = []
    for pt in priced:
        tel[pt.status] += 1
        if pt.status != "priced":
            adj.append(pt)
            continue
        for k, v in pt.components.items():
            comp[k] += float(v)
        if charge_spread:
            adj.append(pt)
        else:
            adj.append(dataclasses.replace(
                pt, cost_r=float(pt.cost_r) - float(pt.components["spread_r"])))
    # `build_daily_panel` is the gate's own collapse: it applies `spec.day_key` and
    # `spec.day_aggregation` (MEAN, not sum), which is what AA's `daily_net_r` is.
    daily, _counts = build_daily_panel(adj, spec)
    per_day = {d.isoformat(): v for d, v in daily.get(rows[0]["sleeve"], {}).items()}
    return dict(per_day), {"n": dict(tel),
                           "cost_component_sums": {k: round(v, 4) for k, v in comp.items()},
                           "coverage": {k: {"n_total": v.n_total, "n_priced": v.n_priced,
                                            "n_unpriced": v.n_unpriced,
                                            "n_blackout_dropped": v.n_blackout_dropped}
                                        for k, v in cov.items()}}


def dayboot(series: dict, draws=20000, seed=20260807):
    days = sorted(series)
    if not days:
        return {}
    v = np.array([series[d] for d in days], dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(v), size=(draws, len(v)))
    m = v[idx].mean(1)
    return {"mean_r_per_day": round(float(v.mean()), 6),
            "ci95_lo": round(float(np.percentile(m, 2.5)), 6),
            "ci95_hi": round(float(np.percentile(m, 97.5)), 6),
            "p_mean_le_zero": round(float((m <= 0).mean()), 5),
            "n_days": len(days)}


def summ(v):
    n = len(v)
    return ({"n": 0} if not n else
            {"n": n, "mean": round(statistics.fmean(v), 6),
             "se": round(statistics.pstdev(v) / math.sqrt(n), 6) if n > 1 else None})


def registry_conf() -> dict:
    mx, err = P.resolve_market_expansion_sleeves(
        policy="positive_weighted12_after_swap", explicit_sleeves=())
    if err:
        raise SystemExit(f"market-expansion policy failed closed: {err}")
    reg = P.effective_registry(include_clean3=True, include_candidate_book=True,
                               include_market_expansion_book=True,
                               market_expansion_sleeves=mx)
    return {k: float(v.confidence) for k, v in reg.items()}


def book_mc(series: dict, paths: int, dial=None) -> dict:
    days = sorted(series)
    dts = [dt.date.fromisoformat(d) for d in days]
    comb = [series[d] for d in days]
    risk = Q.DIAL if dial is None else dial
    a, b = min(dts), max(dts)
    months = (b.year - a.year) * 12 + (b.month - a.month) + 1
    cell = {"book_days": len(days), "weekday_sessions": Q.weekday_sessions(a, b),
            "book_days_per_calendar_month": len(days) / months,
            "mean_r_per_book_day": statistics.fmean(comb),
            "worst_day_unit_r": min(comb), "sd_unit_r": statistics.pstdev(comb),
            "window": f"{a.isoformat()}..{b.isoformat()}", "risk": risk}
    out = {"cell": {k: (round(v, 6) if isinstance(v, float) else v)
                    for k, v in cell.items()}}
    for acct in ("FTMO", "redacted_account"):
        rs, firm = Q.rule_sets(acct)
        out[acct] = {}
        for r in rs:
            if r.label not in ("L4_FIRM_TRUE_PH1", "P2_BOTH_PHASES"):
                continue
            m = Q.mc(comb, risk, r, paths, seed_base=1)
            out[acct][r.label] = {"p_pass": round(m["p_pass"], 6),
                                  "se_p_pass": round(m["se_p_pass"], 6),
                                  "p_fail_dd": round(m["p_fail_dd"], 6),
                                  "p_fail_daily": round(m["p_fail_daily"], 6),
                                  "p_timeout": round(m["p_timeout"], 6),
                                  **Q._derived(cell, m)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", type=int, default=200000)
    args = ap.parse_args()

    sub = json.load(gzip.open(SUB, "rt"))["data"]
    costs = load_broker_true_costs(COSTS)
    conf = registry_conf()
    allow = AD.allowlist()
    tags = armed_from_launcher()
    armed_union = sorted(set(t for v in tags.values() for t in v))
    armed_today = sorted(set(tags.get("operator_profile", []))
                         - {"mx_btcusd_d1_donchian_20_breakout"})

    doc = {
        "schema": "gtos.wave20.m3.armed_econ.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "population": "ARCHIVE — AA's own walk, re-derived and quote-side-corrected by m3",
        "substrate": str(SUB.relative_to(REPO)),
        "armed_sets": {
            "from_launcher": tags,
            "launcher_union": armed_union,
            "armed_today_both_accounts": armed_today,
            "note": ("the committed launcher still lists mx_btcusd on FTMO; the owner "
                     "disarmed it 2026-08-05 (host 2fa77722d, D-2 CLOSED). Both readings "
                     "are carried; every conclusion is stated for the SET, never the count."),
        },
        "registry_confidence": {s: conf.get(s) for s in armed_union},
        "per_sleeve": {}, "book": {}, "mc_paths": args.paths,
    }

    # ---------------------------------------------------------------- per sleeve
    def rows_of(arm: str, sleeve: str):
        """AM's RE-CLOCKED 533 for `sub_mid_dn_revert`; AA's own rows for everything else.

        AM measured that AA's 503 were produced by a clock defect (`substrate._session_hour`
        read raw UTC) and the repair is merged at HEAD; AN's substrate makes the same
        substitution. Judging the sleeve on AA's rows would be judging the defect.
        """
        v = sub[arm]["variants"].get(f"{sleeve}|reclocked")
        return v if v is not None else sub[arm]["base"].get(sleeve)

    for sleeve in armed_union:
        rec: dict = {"exit_contract_walked": (
            "as_walked (AA's own labelling)" if sleeve != "sub_mid_dn_revert"
            else "as_walked on AM's RE-CLOCKED population (533, not AA's 503)")}
        base = rows_of("old", sleeve)
        if base is None:
            rec["absent_from_archive"] = True
            doc["per_sleeve"][sleeve] = rec
            continue
        rec["n_trades"] = len(base)
        rec["gross"] = {"old": summ([float(r["r_gross"]) for r in base])}
        for band in BANDS:
            rec["gross"][f"qs_{band}"] = summ(
                [float(r["r_gross"]) for r in rows_of(f"qs_{band}", sleeve)])
        rec["net"] = {}
        for arm, band in ARMS.items():
            rows = rows_of(arm, sleeve)
            cb = band or "mid"           # the `old` arm is priced at the mid band, as published
            charged, tel = price(rows, cb, charge_spread=True, costs=costs, allow=allow)
            nospread, _ = price(rows, cb, charge_spread=False, costs=costs, allow=allow)
            rec["net"][arm] = {
                "spread_charged": dayboot(charged),
                "spread_removed": dayboot(nospread),
                "telemetry": tel,
            }
        # the FLAT 37-day snapshot, the basis every pre-AG estate number was published on
        flat, ftel = price(base, None, charge_spread=True, costs=costs, allow=allow)
        rec["net"]["old_flat_snapshot_control"] = {"spread_charged": dayboot(flat),
                                                   "telemetry": ftel}
        doc["per_sleeve"][sleeve] = rec
        g = rec["gross"]
        print(f"  {sleeve:36s} n={rec['n_trades']:5d} gross {g['old']['mean']:+.5f} -> "
              f"{g['qs_mid']['mean']:+.5f}   net/day "
              f"{rec['net']['old']['spread_charged']['mean_r_per_day']:+.5f} -> "
              f"{rec['net']['qs_mid']['spread_removed']['mean_r_per_day']:+.5f}", flush=True)

    # ---------------------------------------------------------------- the book
    for label, sleeves in (("ARMED_TODAY_4", armed_today),
                           ("LAUNCHER_UNION_5", armed_union)):
        doc["book"][label] = {"sleeves": sleeves, "weights": "registry confidence", "arms": {}}
        for arm, band in ARMS.items():
            cb = band or "mid"
            for name, charge in (("spread_charged", True), ("spread_removed", False)):
                if arm == "old" and name == "spread_removed":
                    pass          # kept: it isolates the cost change from the walk change
                per_day: dict = collections.defaultdict(float)
                for s in sleeves:
                    rows = rows_of(arm, s)
                    if not rows:
                        continue
                    w = conf.get(s)
                    if w is None:
                        raise SystemExit(f"{s} has no registry confidence")
                    d, _ = price(rows, cb, charge_spread=charge, costs=costs, allow=allow)
                    for day, v in d.items():
                        per_day[day] += w * v
                mc = book_mc(dict(per_day), args.paths)
                doc["book"][label]["arms"][f"{arm}|{name}"] = {
                    "daily": dayboot(dict(per_day)), "mc": mc}
                print(f"  BOOK {label:16s} {arm:7s} {name:15s} "
                      f"r/day={mc['cell']['mean_r_per_book_day']:+.5f} "
                      f"FTMO p2={mc['FTMO']['P2_BOTH_PHASES']['p_pass']:.5f} "
                      f"FN p2={mc['redacted_account']['P2_BOTH_PHASES']['p_pass']:.5f}", flush=True)

    # ---------------------------------------------------------------- control vs AI
    ai = json.load(open(REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                        "BOOKS_MC_V1.json"))
    ref = ai["archive_books"]["CONTROL_FTMO_ARMED_TODAY_3_on_the_archive"]
    three = ["crypto", "energy_agri", "sub_xvol_pullback"]
    per_day = collections.defaultdict(float)
    for s3 in three:
        d, _ = price(rows_of("old", s3), None, charge_spread=True, costs=costs, allow=allow)
        for day, v in d.items():
            per_day[day] += conf[s3] * v
    mine = book_mc(dict(per_day), args.paths)
    doc["control_vs_AI_archive_book"] = {
        "what": ("AI's published ARCHIVE control book (the armed three, registry weights, "
                 "flat 37-day snapshot) rebuilt from m3's own re-walked rows"),
        "ai_book_days": ref["book_days"], "here_book_days": mine["cell"]["book_days"],
        "ai_mean_r_per_book_day": ref["mean_r_per_book_day"],
        "here_mean_r_per_book_day": mine["cell"]["mean_r_per_book_day"],
        "ai_worst_day_unit_r": ref["worst_day_unit_r"],
        "here_worst_day_unit_r": mine["cell"]["worst_day_unit_r"],
        "ai_p_pass_P2_FTMO": ref["branches"]["live_nominal_per_unit"]["accounts"]["FTMO"]
                                ["rules"]["P2_BOTH_PHASES"]["p_pass"],
        "here_p_pass_P2_FTMO": mine["FTMO"]["P2_BOTH_PHASES"]["p_pass"],
    }
    print("CONTROL vs AI:", json.dumps(doc["control_vs_AI_archive_book"], indent=1))

    doc["generated"] = dt.datetime.now(dt.timezone.utc).isoformat()
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True))
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

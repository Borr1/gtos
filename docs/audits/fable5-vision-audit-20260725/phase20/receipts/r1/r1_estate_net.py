"""r1-5b — does the correction reach NET, or was the cost model already standing in for it?

This is the question that decides whether the armed sleeves' published economics move, and
it has an exact answer rather than a judgement.

THE ARITHMETIC
--------------
Under the live book's FILL anchoring (`order_router.py:66-73`) the R unit is
``|fill - stop|`` (`execution.py:3260`), so on the corrected walk a stop books exactly
-1 R and a target exactly +T R **and the spread has already been paid inside the
geometry** — it moved the stop one spread nearer and the target one spread further. There
is no second spread to charge. What the corrected gross still owes is commission, swap and
slippage-beyond-the-quote.

The published net charges all four terms against an UNCORRECTED gross
(`costs.model.cost_r`, `total = commission + swap + spread + slippage`, all divided by
`sl_distance_price`). Its spread term is a *level* stand-in for a *resolution* effect.

So the two defensible nets are

    published net = r_old - (commission + swap + spread + slippage) / d
    corrected net = r_new - (commission + swap +          slippage) / d

and the difference between them is what actually moves. Both are computed here, per trade,
with the estate's own cost model, on all three spread bands. Charging the spread twice
would overstate the repair; ignoring the resolution change would understate it. Neither is
done.

Also decomposed, because it is the mechanism: how much of the gross delta is trades that
CHANGED EXIT REASON (a resolution error no cost term can undo) versus trades that kept
their reason (a level charge on close-based exits, which the cost model does capture).
"""

from __future__ import annotations

import collections
import datetime as dt
import glob
import gzip
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, TF_M15  # noqa: E402
from src.components.ultimate_book.execution_packets import (  # noqa: E402
    DEFAULT_EXIT_PROFILE,
    SLEEVE_EXIT_PROFILES,
)
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import cost_r  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.quote_side import (  # noqa: E402
    BarQuote,
    SpreadUnavailable,
    replay_anchor,
    spread_for,
)

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
TRADES = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
HERE = Path(__file__).resolve().parent
OUT = HERE / "R1_ESTATE_NET_V1.json"

TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
TF_MINUTES = {TF_M15: 15, TF_H4: 240, TF_D1: 1440}
MAXBARS = 80
BAND = "mid"
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback", "mx_btcusd_d1_donchian_20_breakout")
LEVEL_EXITS = ("stop", "target")


def _trail_policy(sleeve: str):
    prof = SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE)
    if prof.get("policy") != "trailing_runner":
        return None, None
    return prof.get("trigger_r"), prof.get("trail_gap_r")


def load_series():
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    files, inv = {}, {v: k for k, v in TF_NAME.items()}
    for p in glob.glob(f"{BARS}/FTMO_*.csv.gz"):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        if inv.get(tfs) is None:
            continue
        files[(res(sym), inv[tfs])] = p
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO")
    series, index = {}, {}
    for key in files:
        rows = src._load(key)
        if not rows:
            continue
        series[key] = (
            [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
             for r in rows],
            [dt.datetime.fromisoformat(r["time"]) for r in rows])
        index[key] = {ts: i for i, ts in enumerate(series[key][1])}
    return series, index


def summ(v):
    n = len(v)
    if not n:
        return {"n": 0}
    return {"n": n, "mean": round(statistics.fmean(v), 6),
            "se": round(statistics.pstdev(v) / math.sqrt(n), 6) if n > 1 else None,
            "sum": round(math.fsum(v), 4)}


def main() -> int:
    doc = json.load(gzip.open(TRADES))
    series, index = load_series()
    S = collections.defaultdict(lambda: collections.defaultdict(list))
    dec = {"changed_reason": [], "same_reason_level": [], "same_reason_close": [],
           "n_changed": 0, "n_same_level": 0, "n_same_close": 0}
    migr = collections.Counter()
    skips = collections.Counter()
    t0 = time.time()

    for sleeve, rows in sorted(doc["trades"].items()):
        trig_r, gap_r = _trail_policy(sleeve)
        for r in rows:
            tf = int(r["timeframe"])
            key = (r["symbol"], tf)
            if key not in index:
                skips["no_series"] += 1
                continue
            i = index[key].get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
            if i is None:
                skips["bar_not_found"] += 1
                continue
            bars, times = series[key]
            if i + 2 >= len(bars):
                skips["no_room"] += 1
                continue
            d, sd = int(r["direction"]), float(r["sl_distance_price"])
            td = r["target_dist"]
            pol = ExitPolicy(target_dist=(float(td) if td else None), maxbars=MAXBARS)
            if trig_r is not None and gap_r is not None:
                pol = ExitPolicy(target_dist=(float(td) if td else None),
                                 trail_arm=float(trig_r) * sd,
                                 trail_gap=float(gap_r) * sd, maxbars=MAXBARS)
            at = times[i] + dt.timedelta(minutes=TF_MINUTES[tf])
            try:
                s = spread_for(r["symbol"], at, account="FTMO", band=BAND)
            except SpreadUnavailable:
                skips["no_spread"] += 1
                continue

            old = replay(bars, i, d, stop_dist=sd, policy=pol)
            new = replay(bars, i, d, stop_dist=sd, policy=pol,
                         entry_price=replay_anchor(bars[i].c, d, s, BarQuote.BID))
            r_old, r_new = winsorize_R(old.r_gross), winsorize_R(new.r_gross)
            side = "LONG" if d > 0 else "SHORT"
            hh_old = old.bars_held * TF_MINUTES[tf] / 60.0
            hh_new = new.bars_held * TF_MINUTES[tf] / 60.0
            try:
                c_old = cost_r(r["symbol"], "FTMO", hh_old, sl_distance_price=sd,
                               entry_price=bars[i].c, side=side, entry_utc=at,
                               spread_band=BAND)
                c_new = cost_r(r["symbol"], "FTMO", hh_new, sl_distance_price=sd,
                               entry_price=bars[i].c, side=side, entry_utc=at,
                               spread_band=BAND)
            except Exception:
                skips["no_cost"] += 1
                continue
            spread_r_old = float(c_old.spread_r.value)
            net_pub = r_old - float(c_old.total_r.value)
            net_cor = r_new - (float(c_new.total_r.value) - float(c_new.spread_r.value))

            a = S[sleeve]
            a["r_old"].append(r_old)
            a["r_new"].append(r_new)
            a["d_gross"].append(r_new - r_old)
            a["net_pub"].append(net_pub)
            a["net_cor"].append(net_cor)
            a["d_net"].append(net_cor - net_pub)
            a["spread_r"].append(spread_r_old)
            a["cost_total_r"].append(float(c_old.total_r.value))

            g = r_new - r_old
            if new.exit_reason != old.exit_reason:
                dec["changed_reason"].append(g)
                dec["n_changed"] += 1
                migr[f"{old.exit_reason}->{new.exit_reason}"] += 1
            elif old.exit_reason in LEVEL_EXITS:
                dec["same_reason_level"].append(g)
                dec["n_same_level"] += 1
            else:
                dec["same_reason_close"].append(g)
                dec["n_same_close"] += 1
        print(f"  {sleeve:36s} {time.time()-t0:6.0f}s", flush=True)

    def pool(k):
        return [x for a in S.values() for x in a[k]]

    if not pool("r_old"):
        # fail LOUD: an empty pool used to surface as a KeyError three screens later
        raise SystemExit(f"no rows scored — every trade was skipped: {dict(skips)}")

    per = {}
    for s, a in sorted(S.items()):
        per[s] = {"n": len(a["r_old"]),
                  "gross_old": summ(a["r_old"])["mean"],
                  "gross_new": summ(a["r_new"])["mean"],
                  "delta_gross": summ(a["d_gross"]),
                  "net_published": summ(a["net_pub"]),
                  "net_corrected": summ(a["net_cor"]),
                  "delta_net": summ(a["d_net"]),
                  "spread_r_mean": summ(a["spread_r"])["mean"],
                  "cost_total_r_mean": summ(a["cost_total_r"])["mean"],
                  "armed": s in ARMED,
                  "net_sign_flip": (summ(a["net_pub"])["mean"] > 0) != (summ(a["net_cor"])["mean"] > 0),
                  "gross_sign_flip": (summ(a["r_old"])["mean"] > 0) != (summ(a["r_new"])["mean"] > 0)}

    out = {
        "what": ("does the quote-side correction reach NET, or was the cost model's spread "
                 "term already standing in for it — decided by arithmetic, not judgement"),
        "band": BAND,
        "population": str(TRADES),
        "skips": dict(skips),
        "construction": {
            "net_published": "r_old - (commission + swap + spread + slippage)/d",
            "net_corrected": ("r_new - (commission + swap + slippage)/d — no spread term, "
                              "because under FILL anchoring the corrected gross has already "
                              "paid it as geometry (stop one spread nearer, target one "
                              "further); charging it again is a double count"),
        },
        "pooled": {
            "gross_old": summ(pool("r_old")),
            "gross_new": summ(pool("r_new")),
            "delta_gross": summ(pool("d_gross")),
            "net_published": summ(pool("net_pub")),
            "net_corrected": summ(pool("net_cor")),
            "delta_net": summ(pool("d_net")),
            "spread_r_mean": summ(pool("spread_r"))["mean"],
            "cost_total_r_mean": summ(pool("cost_total_r"))["mean"],
        },
        "armed_four": {
            "sleeves": list(ARMED),
            "gross_old": summ([x for s in ARMED for x in S[s]["r_old"]]),
            "gross_new": summ([x for s in ARMED for x in S[s]["r_new"]]),
            "net_published": summ([x for s in ARMED for x in S[s]["net_pub"]]),
            "net_corrected": summ([x for s in ARMED for x in S[s]["net_cor"]]),
            "delta_net": summ([x for s in ARMED for x in S[s]["d_net"]]),
        },
        "mechanism_decomposition": {
            "note": ("a level charge is what a cost model can represent; a change of exit "
                     "reason is not, and it is where the estate's delta lives"),
            "trades_that_changed_exit_reason": {
                "n": dec["n_changed"], **summ(dec["changed_reason"])},
            "same_reason_level_exit_stop_or_target": {
                "n": dec["n_same_level"], **summ(dec["same_reason_level"])},
            "same_reason_close_based_exit": {
                "n": dec["n_same_close"], **summ(dec["same_reason_close"])},
            "share_of_total_delta_from_reason_changes": None,
            "exit_reason_migrations": dict(migr.most_common()),
        },
        "per_sleeve": per,
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    tot = math.fsum(pool("d_gross"))
    if tot:
        out["mechanism_decomposition"]["share_of_total_delta_from_reason_changes"] = round(
            math.fsum(dec["changed_reason"]) / tot, 5)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    print("WROTE", OUT)
    print(json.dumps({k: out["pooled"][k] for k in
                      ("gross_old", "gross_new", "net_published", "net_corrected",
                       "delta_net")}, indent=1))
    print(json.dumps(out["mechanism_decomposition"], indent=1)[:1400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

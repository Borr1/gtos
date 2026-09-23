"""Session AB, deliverable 5: the named regime dials, and the store precursors.

    python3 docs/audits/fable5-vision-audit-20260725/phase6/receipts/ab_dials.py

TWO CONSUMERS, TWO ARTIFACTS
-----------------------------
* **Session AJ (command center)** gets `AB_REGIME_DIALS_V1.json`: five named variables,
  what each gates, how to read it, and — the part that makes it a dial rather than an
  opinion — the **measured historical distribution** of each, per year, over the armed
  book's whole surface. "VOL_REGIME is high" means something only against that.

* **Session AH (feature/label store v1)** gets `AB_FEATURE_SCHEMA_V1.json` and
  `AB_LABEL_STORE_V1.jsonl.gz`: a typed, flat, leak-free row per generated trade carrying
  the decision-time features **and**, in a separate block, the realized outcome. Features
  and label are separated in the row so a store built from it cannot train on its own
  answer by accident.

WHAT IS DELIBERATELY NOT COMMITTED
------------------------------------
The full per-bar feature series is ~180,000 rows across the armed surface. It is
regenerable from this file in seconds and `CLAUDE.md` section 8 is explicit that 97 % of
the tracked tree is already generated evidence, so it is written to
`$AB_FEATURE_OUT` (default: outside the repo) rather than committed. What IS committed is
the schema, the label store (one row per trade, small and irreplaceable because it carries
the realized outcome), and the dial distributions.
"""

from __future__ import annotations

import collections
import datetime as dt_
import gzip
import json
import os
import pickle
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.primitives import simulate_detail  # noqa: E402
from src.research_infra.regime_spine import conditions as C  # noqa: E402
from src.research_infra.regime_spine import dials as D  # noqa: E402
from src.research_infra.regime_spine import normalize as N  # noqa: E402
from src.research_infra.regime_spine.archive import ARCHIVE, frames_for  # noqa: E402
from src.research_infra.regime_spine.trials import TrialLedger  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT_DIALS = HERE / "AB_REGIME_DIALS_V1.json"
OUT_SCHEMA = HERE / "AB_FEATURE_SCHEMA_V1.json"
OUT_LABELS = HERE / "AB_LABEL_STORE_V1.jsonl.gz"
LEDGER = HERE / "AB_TRIAL_LEDGER.jsonl"
FRAME_CACHE = os.environ.get("AB_FRAME_CACHE", "")
FEATURE_OUT = os.environ.get(
    "AB_FEATURE_OUT",
    "/Users/borr/GTOSActive/regime-spine-features-20260729/AB_FEATURE_STORE_V1.jsonl.gz")
MAXBARS = 80


def build_frames(sleeves) -> dict:
    want = sorted({s for n in sleeves for s in C.SLEEVES[n].surface})
    cache: dict = {}
    if FRAME_CACHE and Path(FRAME_CACHE).is_file():
        cache = pickle.load(open(FRAME_CACHE, "rb"))
    fr = frames_for(want, 16388, cache=cache)
    N.attach_ranks(fr, ["vr"], window=1000)
    if FRAME_CACHE:
        with open(FRAME_CACHE, "wb") as fh:
            pickle.dump(cache, fh)
    return fr


def quantiles(vals: list[float]) -> dict:
    if not vals:
        return {}
    v = sorted(vals)
    q = lambda p: v[min(len(v) - 1, int(p * (len(v) - 1)))]  # noqa: E731
    return {"n": len(v), "p05": round(q(0.05), 5), "p25": round(q(0.25), 5),
            "median": round(q(0.50), 5), "p75": round(q(0.75), 5),
            "p95": round(q(0.95), 5), "p99": round(q(0.99), 5),
            "mean": round(statistics.fmean(v), 5)}


def main() -> dict:
    t0 = time.time()
    sleeves = list(C.ARMED_FOUR)
    frames = build_frames(sleeves)
    led = TrialLedger(LEDGER, session="AB", append=True)

    # ---------------------------------------------------------------- dial distributions
    per_dial: dict[str, dict[str, list]] = {d.name: collections.defaultdict(list)
                                            for d in D.DIALS}
    per_dial_all: dict[str, list] = {d.name: [] for d in D.DIALS}
    warm = max(c.warmup_bars for c in C.SLEEVES.values())
    for canon, f in frames.items():
        for i in range(warm - 1, len(f)):
            y = str(f.times_utc[i].year)
            for d in D.DIALS:
                v = d.fn(f, i)
                if v is None:
                    continue
                per_dial[d.name][y].append(float(v))
                per_dial_all[d.name].append(float(v))

    # SURFACE_OPEN's per-ROW distribution is degenerate by construction — the loop above
    # starts at the warmup floor, so every emitted row already has surface open and the
    # dial reads 1.0 everywhere. The quantity an operator actually needs is how many of
    # the armed sleeves had ANY tradeable symbol in each year, which is the (a) cause this
    # session measured. Publish that instead of a column of ones.
    opens: dict[str, dt_.date] = {}
    for name in sleeves:
        c = C.SLEEVES[name]
        fs = [frames[s].times_utc[c.warmup_bars - 1].date()
              for s in c.surface
              if s in frames and len(frames[s]) >= c.warmup_bars]
        if fs:
            opens[name] = min(fs)
    surface_by_year = {}
    for y in range(2000, 2027):
        end = dt_.date(y, 12, 31)
        have = sorted(s for s, d0 in opens.items() if d0 <= end)
        surface_by_year[str(y)] = {
            "sleeves_with_surface": len(have), "sleeves": have,
            "sleeves_absent": sorted(s for s in sleeves if s not in have),
            "symbols_with_bars": sum(
                1 for s in have for c in [C.SLEEVES[s]] for sym in c.surface
                if sym in frames and frames[sym].times_utc[0].date() <= end),
        }

    dial_doc = []
    for d in D.describe_dials():
        name = d["name"]
        by_year = {y: quantiles(v) for y, v in sorted(per_dial[name].items())}
        d = dict(d)
        d["distribution_all"] = quantiles(per_dial_all[name])
        d["distribution_by_year"] = by_year
        if name == "SURFACE_OPEN":
            d["distribution_caveat"] = (
                "The per-row distribution is degenerate: rows are only emitted past the "
                "warmup floor, so the dial reads 1 everywhere in this artifact. The "
                "operating series is `armed_surface_by_year` below.")
            d["armed_surface_by_year"] = surface_by_year
        dial_doc.append(d)

    # ------------------------------------------------------- the (c) dial, in its own right
    # HORIZON_CONFLICT unconditionally is uninformative; the measured finding is the
    # CONDITIONAL. Publish it as the dial's operating table so AJ shows the right number.
    cond = C.SLEEVES["sub_xvol_pullback"]
    cx: dict[str, dict[str, int]] = collections.defaultdict(
        lambda: {"n_hivol_uptrend": 0, "n_conflict": 0})
    panel = ("XAUUSD", "XAGUSD")
    for canon in panel:
        f = frames.get(canon)
        if f is None:
            continue
        for i in range(cond.warmup_bars - 1, len(f)):
            vr, s50 = f.vr_raw[i], f.slope50[i]
            if vr is None or s50 is None:
                continue
            if vr < cond.defaults["vr_xhi"] or s50 <= cond.defaults["slope_up"]:
                continue
            y = str(f.times_utc[i].year)
            cx[y]["n_hivol_uptrend"] += 1
            if D._horizon_conflict(f, i) == -1:
                cx[y]["n_conflict"] += 1
    conditional = {y: {**v,
                       "p_conflict_given_hivol_uptrend": (
                           round(v["n_conflict"] / v["n_hivol_uptrend"], 5)
                           if v["n_hivol_uptrend"] else None)}
                   for y, v in sorted(cx.items())}

    dials_out = {
        "schema": "gtos.wave6.regime_spine.dials.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "bars_archive": ARCHIVE,
        "surface": sorted(frames),
        "consumer": "Session AJ — command center (FOURTH_REVIEW section 4.9)",
        "dials": dial_doc,
        "horizon_conflict_conditional_on_sleeve_regime": {
            "panel": list(panel),
            "condition": (f"vr >= {cond.defaults['vr_xhi']} AND "
                          f"slope50 > {cond.defaults['slope_up']}"),
            "by_year": conditional,
            "why": ("This is the number that moved. Unconditionally the horizon-conflict "
                    "rate is flat across 22 years (0.271 -> 0.254 on this panel); "
                    "conditional on sub_xvol_pullback's own vol and trend gates it runs "
                    "0.62 % over 2015-2019 and 12.6 % over 2025+. A command center "
                    "showing the unconditional rate would show a flat line and say "
                    "nothing."),
            "correction": (
                "Read year by year this conditional is EPISODIC, not trending, and this "
                "session's first reading of it as a trend was wrong. It is 0.27-0.43 in "
                "2006/2008/2009/2012, ~0.00 across most of 2014-2019 and in 2024, and "
                "0.15-0.20 in 2020 and 2025. 2015-2019 is a long quiet stretch of a "
                "recurrent regime, not the base of a ramp. The distinction matters for "
                "the book: a trend would make sub_xvol_pullback's edge new and possibly "
                "transient; episodicity makes its 2013-2019 silence the regime being "
                "absent, which is a measurable and monitorable state rather than a "
                "decayed edge."),
        },
        "operator_note": (
            "A quiet book is the normal state. Across 2000-2026 the armed four fire on "
            "6.9 % of weekday sessions; in 2015 it was 1.9 %, in 2025 20.3 %, and the "
            "difference is mostly how many of the four had a tradeable instrument at all "
            "(2 of 4 before 2017, 3 of 4 before 2021). Check SURFACE_OPEN before "
            "diagnosing silence as a fault."),
    }
    OUT_DIALS.write_text(json.dumps(dials_out, indent=1, sort_keys=True, default=str) + "\n")

    # ---------------------------------------------------------- label store (committed)
    import datetime as dt
    ivl = dt.timedelta(hours=4)
    labels = []
    for name in sleeves:
        c = C.SLEEVES[name]
        for canon in c.surface:
            f = frames.get(canon)
            if f is None:
                continue
            for i, intent in C.fires(f, c):
                if i + 2 >= len(f):
                    continue
                r, xi = simulate_detail(f.bars, i, intent["direction"],
                                        stop_dist=intent["stop_dist"],
                                        target_dist=intent["target_dist"],
                                        maxbars=MAXBARS, cost=0.0)
                labels.append({
                    "features": D.feature_row(f, i, canonical=canon),
                    "intent": {"sleeve": name, "direction": int(intent["direction"]),
                               "stop_dist_price": float(intent["stop_dist"]),
                               "target_dist_price": (float(intent["target_dist"])
                                                     if intent.get("target_dist") else None),
                               "intra_size": float(intent.get("intra_size", 1.0))},
                    "label": {"r_gross_winsorised": float(winsorize_R(r)),
                              "exit_bar_offset": int(xi - i),
                              "hold_hours": round((xi - i) * 4.0, 4),
                              "exit_utc": (f.times_utc[xi] + ivl).isoformat(),
                              "maxbars": MAXBARS,
                              "cost_charged": 0.0},
                })
    with gzip.open(OUT_LABELS, "wt") as fh:
        for row in labels:
            fh.write(json.dumps(row, sort_keys=True, default=str) + "\n")

    schema_out = {
        "schema": "gtos.wave6.regime_spine.feature_schema.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "consumer": "Session AH — feature store + label store v1 (FOURTH_REVIEW 4.7/4.8)",
        "feature_fields": D.FEATURE_SCHEMA,
        "label_fields": {
            "r_gross_winsorised": "float — simulate_detail at cost=0, admission.winsorize_R",
            "exit_bar_offset": "int", "hold_hours": "float",
            "exit_utc": "str(iso8601)", "maxbars": "int", "cost_charged": "float",
        },
        "leak_discipline": (
            "Every feature is a function of bars at index <= i. The trailing percentile "
            "excludes bar i from its own window. Features and label live in separate "
            "blocks of the row so a trainer cannot read the outcome as an input."),
        "partition_authority": (
            "Session Z's partition registry is the authority on train/validate/embargo "
            "cuts; nothing here partitions. `year` and `decision_day` are carried so it "
            "can."),
        "label_store_path": str(OUT_LABELS.relative_to(REPO)),
        "label_store_rows": len(labels),
        "full_feature_series_path": FEATURE_OUT,
        "full_feature_series_note": (
            "Not committed — ~180k rows, regenerable in seconds by this script. "
            "CLAUDE.md section 8: the tracked tree is already 97 % generated evidence."),
    }
    OUT_SCHEMA.write_text(json.dumps(schema_out, indent=1, sort_keys=True) + "\n")

    # ------------------------------------------------ full feature series (outside git)
    n_rows = 0
    try:
        p = Path(FEATURE_OUT)
        p.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(p, "wt") as fh:
            for canon, f in sorted(frames.items()):
                for i in range(warm - 1, len(f)):
                    fh.write(json.dumps(D.feature_row(f, i, canonical=canon),
                                        sort_keys=True, default=str) + "\n")
                    n_rows += 1
        print(f"feature series: {n_rows} rows -> {p} "
              f"({p.stat().st_size/1e6:.1f} MB)")
    except OSError as e:
        print(f"feature series NOT written ({e}); schema and label store are unaffected")

    led.log("dials", "armed_four", "regime_dials_v1",
            {"n_dials": len(D.DIALS), "surface": len(frames)},
            {"label_rows": len(labels), "feature_rows": n_rows},
            note="descriptive artifact; nothing selected on")
    led.write_summary(HERE / "AB_TRIAL_BUDGET_RESULT.json")
    led.close()

    print(f"\ndials -> {OUT_DIALS.relative_to(REPO)}")
    print(f"schema -> {OUT_SCHEMA.relative_to(REPO)}")
    print(f"labels -> {OUT_LABELS.relative_to(REPO)} ({len(labels)} rows, "
          f"{OUT_LABELS.stat().st_size/1e3:.0f} kB)")
    print("\nHORIZON_CONFLICT conditional on sub_xvol_pullback's own regime "
          "(XAUUSD+XAGUSD):")
    print(f"  {'year':6s} {'hivol&up bars':>14s} {'conflict':>9s} {'P':>8s}")
    for y, v in conditional.items():
        p_ = v["p_conflict_given_hivol_uptrend"]
        print(f"  {y:6s} {v['n_hivol_uptrend']:14d} {v['n_conflict']:9d} "
              f"{('-' if p_ is None else f'{p_:.4f}'):>8s}")
    print(f"\n{time.time()-t0:.0f}s")
    return dials_out


if __name__ == "__main__":
    main()

"""Generate the whole estate over the full archive, WITH the path — holds, MFE/MAE, exits.

    python3 docs/audits/fable5-vision-audit-20260725/phase6/receipts/aa_estate_generate.py

WHAT IS DIFFERENT FROM `phase5/receipts/x_estate_generate.py`
--------------------------------------------------------------
X's generation is the substrate this builds on and three things it did not do are the
reason wave 6 exists:

1. **The seven first-of-day sleeves were not generated at all.** X filtered on
   `fidelity.scoreable(0.50)` before generating, so `asian_fade`, `asia_pdl_fade`,
   `ny_crypto_momentum`, `orb_crypto_london`, `kz_london_crypto_low`,
   `liq_asia_up_low_metal` and `metal_session_reversion` produced zero rows and were
   carried as family members with no evidence. `FOURTH_REVIEW.md` §2.1 splits that
   refusal into a STAMP: *is the rule profitable* (answerable today, on the port's own
   semantics) and *does the live engine implement the rule* (K1/Y's question, which
   stamps a transfer risk on the answer). Session Y then measured that the 19% recall was
   a **code-lineage artefact** — under the matching lineage the seven go to 100% recall,
   175 of 175 recovered, 0 newly missed. They are generated here, and every row carries
   its fidelity class so nothing about the stamp is lost.

2. **No path survived the labelling.** `simulate_detail` returns `(R, exit_index)` and
   throws the excursion away, so no artifact in this programme could answer "did the
   setups move and the exit miss it, or was there nothing there" — which is precisely the
   query §3.3 asks for and never assigns. Labelling goes through
   `walkforward.exits.replay`, which is fuzz-verified identical to `simulate_detail` on R
   and exit index (4,000 random series, `==`) and additionally returns `mfe_r`, `mae_r`,
   `bars_to_mfe` and `exit_reason`.

3. **The two TRAILING sleeves were unlabellable.** `asian_fade` and
   `metal_session_reversion` carry `policy="trailing_runner"` in the production exit table
   (`execution_packets.py:57,61`), and `primitives.simulate` has supported `trail_arm` /
   `trail_gap` since it was vendored — no driver ever passed them. Their trail is in R
   units (`trigger_r`, `trail_gap_r`), so the conversion to price distance is exact and
   carries no unit ambiguity. Both labellings are emitted: `r_gross` under the trail (the
   sleeve's own contract) and `r_gross_plain` under stop/target/maxbars, so the repair's
   effect is measured rather than claimed.

WHAT IS DELIBERATELY *NOT* CHANGED, AND WHY
--------------------------------------------
`MAXBARS = 80` in each sleeve's own timeframe, exactly as W's pilot and X's walk used it,
so every number here is comparable to `W_MX_PILOT.json` and `X_ESTATE_WALK.json`.

The production exit table also carries `time_stop_bars` per sleeve, and it is **not
applied**, because its unit is ambiguous in the repo and guessing would be the kind of
probe artefact that cost this programme four false alarms in one day. Read the evidence:
`crypto` H4 carries 1280, and 1280 x 15 min = 320 h = the H4 structural horizon
`SURVIVOR_BOOK_V1.json` records — so 1280 is M15 units. But the fourteen `mx_*` D1 sleeves
carry 96, and `FOURTH_REVIEW.md` §3.3 reads that as **96 D1 bars** against a realised
median hold of ~3 D1 bars — which in M15 units would be one day and cannot be what a
96-bar time-stop contract means. `book_owner.py:4139` passes the number through to the
execution manager as a display parameter and never resolves the unit. So each sleeve's
contract is RECORDED in the artifact with the ambiguity named, for the exit sweep that
owns it (wave 7), and nothing here silently picks a side.

Offline and pure: reads gzipped CSV bars, imports no broker module, writes one JSON.
Every sleeve generated is logged to the trial-budget ledger.
"""

from __future__ import annotations

import collections
import datetime as dt
import glob
import gzip
import json
import os
import statistics
import sys
import time
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, TF_M15  # noqa: E402
from src.components.ultimate_book.book_engine import (  # noqa: E402
    _candidate_book_sleeves,
    _market_expansion_sleeves,
)
from src.components.ultimate_book.execution_packets import (  # noqa: E402
    DEFAULT_EXIT_PROFILE,
    SLEEVE_EXIT_PROFILES,
)
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.sleeves.registry import active_specs  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource, GenerationPort  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.fidelity import fidelity_for  # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"

TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
TF_MINUTES = {TF_M15: 15, TF_H4: 240, TF_D1: 1440}
MAXBARS = 80


def _trail_policy(sleeve: str) -> tuple[float | None, float | None]:
    """(trigger_r, trail_gap_r) for a `trailing_runner` sleeve, else (None, None)."""
    prof = SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE)
    if prof.get("policy") != "trailing_runner":
        return None, None
    return prof.get("trigger_r"), prof.get("trail_gap_r")


def build(config_overrides: dict) -> tuple:
    base = yaml.safe_load(open(REPO / "config/agent_config.yaml"))
    cfg = dict(base.get("gtos_vnext_runtime") or {})
    cfg.update(config_overrides)
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    files = {}
    for p in glob.glob(f"{BARS}/FTMO_*.csv.gz"):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        tf = {v: k for k, v in TF_NAME.items()}.get(tfs)
        if tf is None:
            continue
        files[(res(sym), tf)] = p
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO")
    port = GenerationPort(cfg, src, namespace="aa_estate", broker_symbol=res)
    return cfg, prof, res, files, src, port


def main() -> dict:
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AA")
    overrides = {"ultimate_book_include_clean3": True}
    cfg, prof, res, files, src, port = build(overrides)
    active = set(port.active_sleeve_names())
    print(f"active book (with research overrides): {len(active)} sleeves")

    tf_of: dict[str, int] = {}
    surface_of: dict[str, tuple] = {}
    for spec in active_specs(
        None,
        include_candidate_book=bool(cfg.get("ultimate_book_include_candidate_book", False)),
        candidate_book_sleeves=_candidate_book_sleeves(cfg) or None,
        include_market_expansion_book=bool(
            cfg.get("ultimate_book_include_market_expansion_book", False)),
        market_expansion_sleeves=_market_expansion_sleeves(cfg) or None,
    ):
        if spec.tag in active:
            tf_of[spec.tag] = spec.timeframe
            surface_of[spec.tag] = tuple(spec.on_surface)
    missing = sorted(active - set(tf_of))
    if missing:
        print(f"  no generator spec for: {missing}")

    # THE CHANGE: everything with a generator is generated. The fidelity class is carried
    # as a STAMP on every sleeve (FOURTH_REVIEW §2.1) rather than used as a pre-filter.
    generate_all = sorted(tf_of)
    stamps = {}
    for s in generate_all:
        f = fidelity_for(s)
        stamps[s] = {
            "class": f.cls.value, "basis": f.basis.value, "live_recall": f.live_recall,
            "basis_n": f.basis_n, "scoreable_at_0.50": f.scoreable(0.50),
            "note": f.basis_note,
        }
    n_below = sum(1 for v in stamps.values() if not v["scoreable_at_0.50"])
    print(f"  generating all {len(generate_all)} sleeves with a generator; "
          f"{n_below} carry a fidelity stamp below the 0.50 floor and are generated anyway")

    by_tf: dict[int, list[str]] = collections.defaultdict(list)
    for s in generate_all:
        by_tf[tf_of[s]].append(s)

    # ---- bar series, once ---------------------------------------------------------------
    series: dict[tuple[str, int], tuple[list[Bar], list[dt.datetime]]] = {}
    index: dict[tuple[str, int], dict[dt.datetime, int]] = {}
    for key in files:
        rows = src._load(key)
        if not rows:
            continue
        bars = [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
                for r in rows]
        times = [dt.datetime.fromisoformat(r["time"]) for r in rows]
        series[key] = (bars, times)
        index[key] = {ts: i for i, ts in enumerate(times)}
    print(f"  loaded {len(series)} (symbol, timeframe) bar series")

    t_start = time.time()
    all_rows: list[dict] = []
    grids: dict[str, dict] = {}
    seen: set = set()
    n_dupes = 0

    for tf in sorted(by_tf, key=lambda t: TF_MINUTES[t]):
        sleeves = sorted(by_tf[tf])
        wanted = {res(s) for name in sleeves for s in surface_of[name]}
        stampset = set()
        for (sym, ktf) in files:
            if ktf != tf or sym not in wanted:
                continue
            for ts in series.get((sym, ktf), ((), ()))[1]:
                stampset.add(ts)
        grid = sorted(t + dt.timedelta(minutes=TF_MINUTES[tf]) for t in stampset)
        if not grid:
            print(f"  {TF_NAME[tf]}: no bars for {sleeves}")
            continue
        print(f"\n=== {TF_NAME[tf]}: {len(sleeves)} sleeves, {len(grid)} closes "
              f"{grid[0].date()} .. {grid[-1].date()} ===", flush=True)
        t0 = time.time()
        got = 0
        for i, ts in enumerate(grid):
            for c in port.generate(ts, tags=sleeves).candidates:
                key = (c.sleeve, c.symbol, c.decision_bar_iso)
                if key in seen:
                    n_dupes += 1
                    continue
                seen.add(key)
                all_rows.append({"cand": c, "tf": tf})
                got += 1
            if (i + 1) % 5000 == 0:
                el = time.time() - t0
                print(f"    {i+1}/{len(grid)}  {el:.0f}s  "
                      f"eta {el/(i+1)*(len(grid)-i-1):.0f}s  kept={got}", flush=True)
        grids[TF_NAME[tf]] = {
            "n_closes": len(grid), "first": grid[0].isoformat(), "last": grid[-1].isoformat(),
            "sleeves": sleeves, "seconds": round(time.time() - t0, 1), "candidates_kept": got,
        }
        print(f"  {TF_NAME[tf]} done in {time.time()-t0:.0f}s, {got} unique candidates",
              flush=True)

    print(f"\ngeneration total {time.time()-t_start:.0f}s; {len(all_rows)} unique candidates, "
          f"{n_dupes} duplicates dropped", flush=True)

    # ---- label through the path replay ----------------------------------------------------
    trades: dict[str, list[dict]] = {s: [] for s in sorted(tf_of)}
    skips: collections.Counter = collections.Counter()
    gaps: list[float] = []
    trail_delta: dict[str, list[float]] = collections.defaultdict(list)
    for row in all_rows:
        c, tf = row["cand"], row["tf"]
        sym = res(c.symbol)
        key = (sym, tf)
        if key not in index:
            skips[f"{c.sleeve}:no_series[{c.symbol}->{sym}]"] += 1
            continue
        iso = c.decision_bar_iso
        if not iso:
            skips[f"{c.sleeve}:no_decision_bar_iso"] += 1
            continue
        i = index[key].get(dt.datetime.fromisoformat(iso))
        bars, times = series[key]
        if i is None or i + 2 >= len(bars):
            skips[f"{c.sleeve}:bar_not_found_or_no_room"] += 1
            continue

        trig_r, gap_r = _trail_policy(c.sleeve)
        plain = ExitPolicy(target_dist=c.target_dist, maxbars=MAXBARS, label="plain")
        pr_plain = replay(bars, i, c.direction, stop_dist=c.stop_dist, policy=plain)
        if trig_r is not None and gap_r is not None:
            pol = ExitPolicy(
                target_dist=c.target_dist,
                trail_arm=float(trig_r) * float(c.stop_dist),
                trail_gap=float(gap_r) * float(c.stop_dist),
                maxbars=MAXBARS, label="trailing_runner",
            )
            pr = replay(bars, i, c.direction, stop_dist=c.stop_dist, policy=pol)
            trail_delta[c.sleeve].append(winsorize_R(pr.r_gross) - winsorize_R(pr_plain.r_gross))
        else:
            pr = pr_plain

        r = winsorize_R(pr.r_gross)
        xi = pr.exit_index
        entry = bars[i].c
        ivl = dt.timedelta(minutes=TF_MINUTES[tf])
        gaps.append(c.direction * (bars[i + 1].o - entry) / c.stop_dist)
        trades[c.sleeve].append({
            "sleeve": c.sleeve,
            "symbol": sym,
            "symbol_canonical": c.symbol,
            "entry_utc": (times[i] + ivl).isoformat(),
            "exit_utc": (times[xi] + ivl).isoformat(),
            "direction": int(c.direction),
            "sl_distance_price": float(c.stop_dist),
            "entry_price": float(entry),
            "r_gross": float(r),
            "r_gross_plain": float(winsorize_R(pr_plain.r_gross)),
            "exit_policy": pr.detail.get("policy", "plain"),
            "exit_reason": pr.exit_reason,
            "mfe_r": round(pr.mfe_r, 6),
            "mae_r": round(pr.mae_r, 6),
            "bars_to_mfe": int(pr.bars_to_mfe),
            "timeframe": int(tf),
            "decision_bar_iso": iso,
            "decision_day": c.decision_day,
            "bar_decision_day": (c.features or {}).get("bar_decision_day"),
            "target_dist": (float(c.target_dist) if c.target_dist else None),
            "intra_size": float(c.intra_size or 1.0),
            "ll_impulse": c.ll_impulse,
            "decision_hour": c.decision_hour,
            "vp_loc": c.vp_loc,
            "exit_bar_offset": int(xi - i),
            "hold_hours": round((xi - i) * TF_MINUTES[tf] / 60.0, 4),
            "features": {k: v for k, v in (c.features or {}).items() if k != "last_close"},
        })

    n_tr = sum(len(v) for v in trades.values())
    print(f"labelled {n_tr} trades over {sum(1 for v in trades.values() if v)} sleeves; "
          f"skipped {sum(skips.values())}")
    if skips:
        print("  skips:", dict(skips))

    for sleeve, deltas in sorted(trail_delta.items()):
        if deltas:
            print(f"  TRAIL {sleeve:28s} n={len(deltas):5d} "
                  f"mean dR={statistics.fmean(deltas):+.5f} "
                  f"median dR={statistics.median(deltas):+.5f}")

    abs_gaps = [abs(g) for g in gaps]
    entry_gap = {
        "n": len(gaps),
        "mean_signed_R": round(statistics.fmean(gaps), 6) if gaps else None,
        "median_signed_R": round(statistics.median(gaps), 6) if gaps else None,
        "mean_abs_R": round(statistics.fmean(abs_gaps), 6) if abs_gaps else None,
        "note": ("direction * (next_open - decision_close) / stop_dist. POSITIVE means the "
                 "next open would have been better for the trade, i.e. entering at the close "
                 "is DISADVANTAGED."),
    }

    for s in sorted(tf_of):
        ledger.record(
            mechanism="estate_generation", sleeve=s,
            variant={"maxbars": MAXBARS, "timeframe": TF_NAME.get(tf_of[s]),
                     "exit_policy": SLEEVE_EXIT_PROFILES.get(s, DEFAULT_EXIT_PROFILE).get(
                         "policy", "time_stop"),
                     "archive": "vps-bars-20260727-FTMO"},
            window=f"{grids.get(TF_NAME.get(tf_of[s]), {}).get('first', '')[:10]}.."
                   f"{grids.get(TF_NAME.get(tf_of[s]), {}).get('last', '')[:10]}",
            outcome="evaluated", metric=float(len(trades.get(s, []))),
            metric_name="n_trades_generated",
            note="AA estate walk generation over the full archive",
        )

    out = {
        "schema": "gtos.walkforward.estate_trades.v2",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase6/receipts/aa_estate_generate.py",
        "bars_archive": BARS,
        "maxbars": MAXBARS,
        "research_overrides": {
            "config": overrides,
            "why": ("config/agent_config.yaml:1270 sets ultimate_book_include_clean3: false. "
                    "The flag is flipped in the config DICT handed to GenerationPort; the "
                    "file on disk is untouched (it is H1-bound AND the live activation "
                    "token binds its digest)."),
        },
        "fidelity_policy": {
            "mode": "stamp_not_filter",
            "why": ("FOURTH_REVIEW §2.1. X's generation pre-filtered on "
                    "fidelity.scoreable(0.50) and the seven first-of-day sleeves produced "
                    "zero rows. Session Y then measured that the 19% recall behind that "
                    "floor was a code-lineage artefact (100% under the matching lineage, "
                    "175/175 recovered, 0 newly missed). Every sleeve with a generator is "
                    "generated; the class travels on every row."),
            "stamps": stamps,
        },
        "exit_contracts": {
            s: {**SLEEVE_EXIT_PROFILES.get(s, DEFAULT_EXIT_PROFILE),
                "applied_here": ("trail+stop+target+maxbars"
                                 if _trail_policy(s)[0] is not None
                                 else "stop+target+maxbars"),
                "time_stop_bars_applied": False}
            for s in sorted(tf_of)
        },
        "time_stop_unit_ambiguity": (
            "SLEEVE_EXIT_PROFILES carries time_stop_bars per sleeve and it is NOT applied "
            "here. crypto's 1280 x 15min = 320h = the H4 structural horizon in "
            "SURVIVOR_BOOK_V1.json, which reads as M15 units; the fourteen mx_* D1 sleeves "
            "carry 96, which FOURTH_REVIEW §3.3 reads as 96 D1 bars against a ~3 D1-bar "
            "realised median. Both cannot be the same unit. book_owner.py:4139 passes the "
            "number through without resolving it. Recorded, not guessed."
        ),
        "active_book": sorted(active),
        "family_all": sorted(tf_of),
        "generated_sleeves": generate_all,
        "fidelity_below_floor_generated_anyway": sorted(
            s for s, v in stamps.items() if not v["scoreable_at_0.50"]),
        "timeframe_by_sleeve": {s: TF_NAME.get(t, str(t)) for s, t in sorted(tf_of.items())},
        "grids": grids,
        "n_candidates_unique": len(all_rows),
        "n_duplicates_dropped": n_dupes,
        "n_trades_by_sleeve": {s: len(v) for s, v in sorted(trades.items())},
        "entry_convention_gap": entry_gap,
        "trail_repair": {
            s: {"n": len(v), "mean_delta_r": round(statistics.fmean(v), 6),
                "median_delta_r": round(statistics.median(v), 6),
                "frac_improved": round(sum(1 for x in v if x > 0) / len(v), 5)}
            for s, v in sorted(trail_delta.items()) if v
        },
        "skips": dict(skips),
        "seconds_total": round(time.time() - t_start, 1),
        "trades": trades,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, "wt") as fh:
        json.dump(out, fh, default=str)
    print(f"\nwrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.1f} MB)")
    for s, v in sorted(trades.items(), key=lambda kv: -len(kv[1])):
        print(f"  {s:42s} {len(v):6d}")
    print(f"ledger: {ledger.summary()['n_trials']} rows at {ledger.path}")
    return out


if __name__ == "__main__":
    main()

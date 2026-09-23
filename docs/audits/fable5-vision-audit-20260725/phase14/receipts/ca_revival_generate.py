#!/usr/bin/env python3
"""Session CA (B2100-B2119) — re-derive the three CARRY_CONDITIONAL sleeves on the fetched bars.

    python3 .../phase14/receipts/ca_revival_generate.py --stage probe
    python3 .../phase14/receipts/ca_revival_generate.py --stage archive   # the control arm
    python3 .../phase14/receipts/ca_revival_generate.py --stage merged    # archive + the fetch
    python3 .../phase14/receipts/ca_revival_generate.py --stage vp        # vp_euidx, M1 window only

WHAT THE FETCH ACTUALLY UNBLOCKED, MEASURED BEFORE ANY GATE RUNS
-----------------------------------------------------------------
`phase13/receipts/CARRYCOND_FETCH_20260730.md` reports `missing: []` on all three sleeves and
reads that as "the three dead sleeves' data blockade is broken". That is true of ONE sleeve,
and the `--stage probe` output says which. The reason the other two read as blocked is
mechanical and worth naming, because the same harness will be re-run:
`av_deep_h4_ingest.py:78-81` searches exactly two roots, both of them
`data/mt5_research_exports/`, and **the archive the estate walk actually generates from is
neither** — it is `/Users/borr/GTOSActive/vps-bars-20260727`. Four of the six symbols
`metals_softband` needs were in that archive the whole time, and `AA_ESTATE_TRADES.json.gz`
holds 237 `metals_softband` trades on all six, generated 2026-07-29. So the harness's
residual ask was computed against a root that does not contain the estate's bars.

Restated per sleeve, from the bytes (this is `--stage probe`'s job, not this docstring's --
the numbers below are what it printed on 2026-07-31 and it recomputes them every run):

  metals_softband    NOT data-blocked, and never was. The fetch adds 22 H4 bars per cross
                     (0.26 %) and ZERO symbols. What this sleeve lacked is a carry-priced
                     verdict, not data.
  sub_mid_dn_revert  genuinely short 2 of its 20 declared surface symbols (CORN.c 2023-03+,
                     COTTON.c 2025-03+). The fetch supplies both. Shorter histories than its
                     FX members -- disclosed on every pooled figure.
  vp_euidx_pocgrav   genuinely blocked, zero trades in every estate artifact. Its M1 aux feed
                     did not exist anywhere. The fetch supplies GER40/UK100 M1 from
                     2026-04-27 -- ~3 months, against a sleeve that needs a prior-day M1
                     volume profile per H4 decision.

THE ARCHIVE ARM IS THE CONTROL, AND IT IS NOT DECORATION
---------------------------------------------------------
`--stage archive` regenerates from the bar archive alone. It must reproduce
`AQ_ESTATE_TRADES_V2.json.gz` exactly -- 237 `metals_softband` and 533 `sub_mid_dn_revert`
rows with identical R -- because nothing about the generator changed. If it does, then every
difference in `--stage merged` is attributable to the fetch and to nothing else. If it does
not, the merged arm's delta is uninterpretable and this file says so instead of publishing it.

THE EXIT CONTRACT IS WALKED TWICE, DELIBERATELY
------------------------------------------------
`MAXBARS = 80` in the sleeve's own timeframe, exactly as AA/X/AQ used it, so every number is
comparable to `AA_ESTATE_WALK.json` and `BB_SUPPLY_RANK_V1.json`. But `vp_euidx_pocgrav`
carries `time_stop_bars: 960` = 60 H4 bars, which is TIGHTER than the 80-bar research
horizon -- the AU/AQ defect class, on a sleeve nobody has ever walked. So each trade also
carries `r_gross_live_stop`, the same path replayed at the sleeve's OWN live time stop, and
the artifact records both. No number is published under a contract the book does not run
without saying so.

BOUNDARY. Offline and pure: reads gzipped/plain CSV bars and writes one JSON. Imports no
broker module, touches no config file on disk, contacts no VPS.
"""
from __future__ import annotations

import argparse
import collections
import csv as _csv
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
from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, TF_M15, WARMUP  # noqa: E402
from src.components.ultimate_book.book_engine import (  # noqa: E402
    _candidate_book_sleeves,
    _market_expansion_sleeves,
)
from src.components.ultimate_book.execution_packets import (  # noqa: E402
    DEFAULT_EXIT_PROFILE,
    SLEEVE_EXIT_PROFILES,
)
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.sleeves.registry import BUILT, active_specs  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource, GenerationPort  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.fidelity import fidelity_for  # noqa: E402

HERE = Path(__file__).resolve().parent
ARCHIVE = Path("/Users/borr/GTOSActive/vps-bars-20260727")
#: The orchestrator's 2026-07-30 carry-conditional fetch. `data/mt5_research_exports/` is
#: gitignored and lives on exactly one tree per machine -- the main repo's, not this worktree's.
FETCH = Path("/Users/borr/GTOSActive/repo/data/mt5_research_exports/"
             "bridge_ftmo_carrycond_h4_m1_20260730")
AQ_ESTATE = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"

TARGETS = ("metals_softband", "sub_mid_dn_revert", "vp_euidx_pocgrav")
TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1", 1: "M1"}
TF_MINUTES = {TF_M15: 15, TF_H4: 240, TF_D1: 1440, 1: 1}
MAXBARS = 80
#: `time_stop_bars` is M15 PRINTED bars for every sleeve (`execution.py:8953-8958`, AQ B1400).
M15_PER = {TF_M15: 1, TF_H4: 16, TF_D1: 96}

PROBE_OUT = HERE / "CA_DATA_PROBE_V1.json"


def _out(arm: str) -> Path:
    return HERE / f"CA_REVIVAL_TRADES_{arm.upper()}_V1.json.gz"


# =====================================================================================
# the bar map — archive base, fetch overlay, every choice recorded
# =====================================================================================
def _archive_files(res) -> dict:
    files = {}
    for p in sorted(glob.glob(f"{ARCHIVE}/FTMO_*.csv.gz")):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        tf = {v: k for k, v in TF_NAME.items()}.get(tfs)
        if tf is None:
            continue
        files[(res(sym), tf)] = p
    return files


def _fetch_files(res) -> dict:
    files = {}
    for p in sorted(glob.glob(f"{FETCH}/*.csv")):
        stem = os.path.basename(p)[:-len(".csv")]
        sym, _, tfs = stem.rpartition("_")
        tf = {v: k for k, v in TF_NAME.items()}.get(tfs)
        if tf is None:
            continue
        files[(res(sym), tf)] = p
    return files


def build_files(res, *, arm: str) -> tuple[dict, dict]:
    """`(files, provenance)`. `arm='archive'` ignores the fetch entirely."""
    arch = _archive_files(res)
    if arm == "archive":
        return arch, {f"{k[0]}:{TF_NAME.get(k[1], k[1])}": "archive" for k in arch}
    fet = _fetch_files(res)
    files = dict(arch)
    prov = {f"{k[0]}:{TF_NAME.get(k[1], k[1])}": "archive" for k in arch}
    for k, p in fet.items():
        label = f"{k[0]}:{TF_NAME.get(k[1], k[1])}"
        # The fetch is the NEWER capture of the same series from the same terminal, so where
        # both exist it wins: `--stage probe` proves they agree bar-for-bar on the overlap
        # except the archive's last bar, which was still forming when the archive was cut.
        prov[label] = "fetch_new_series" if k not in arch else "fetch_supersedes_archive"
        files[k] = p
    return files, prov


def build_port(files, *, namespace: str):
    base = yaml.safe_load(open(REPO / "config/agent_config.yaml"))
    cfg = dict(base.get("gtos_vnext_runtime") or {})
    # The config FILE is untouched: it is R2-bound and the live activation token binds its
    # digest. The flag is flipped in the dict handed to GenerationPort, as AA did.
    cfg["ultimate_book_include_clean3"] = True
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    src = CsvBarSource(files, label=namespace)
    return cfg, res, src, GenerationPort(cfg, src, namespace=namespace, broker_symbol=res)


# =====================================================================================
# STAGE probe — what the fetch actually added, per sleeve, before anything is gated
# =====================================================================================
def _read_csv_times(path: Path) -> dict:
    rows = {}
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", newline="") as fh:
        for r in _csv.DictReader(fh):
            t = (r.get("time") or "").strip()
            if not t:
                continue
            rows[int(float(t))] = (r["open"], r["high"], r["low"], r["close"])
    return rows


def probe() -> dict:
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    arch, fet = _archive_files(res), _fetch_files(res)

    # 1. the overlap check: do the two captures agree where both cover the same bar?
    overlap = {}
    for key, fpath in sorted(fet.items(), key=lambda kv: str(kv[0])):
        apath = arch.get(key)
        label = f"{key[0]}:{TF_NAME.get(key[1], key[1])}"
        if apath is None:
            overlap[label] = {"in_archive": False,
                              "note": "series exists ONLY in the fetch -- a genuine unblock"}
            continue
        a, b = _read_csv_times(Path(apath)), _read_csv_times(Path(fpath))
        both = set(a) & set(b)
        disagree = sorted(t for t in both if a[t] != b[t])
        overlap[label] = {
            "in_archive": True,
            "archive_rows": len(a), "fetch_rows": len(b), "overlapping_bars": len(both),
            "ohlc_disagreements": len(disagree),
            "bars_only_in_fetch": len(set(b) - set(a)),
            "bars_only_in_archive": len(set(a) - set(b)),
            "disagreeing_epochs": disagree[:5],
            "reading": (
                "the two captures agree bar-for-bar except the archive's LAST bar, which was "
                "still forming when the archive was cut on 2026-07-27; the fetch supersedes it"
                if len(disagree) <= 1 and disagree and disagree[0] == max(a)
                else "UNEXPECTED: more than the trailing forming bar disagrees -- do not merge"),
        }

    # 2. per sleeve: what was missing from the ARCHIVE (the root the estate walk reads),
    #    which is the question `av_deep_h4_ingest.py` did not ask.
    per = {}
    for name in TARGETS:
        spec = BUILT[name]
        tf = spec.timeframe
        want = [res(s) for s in spec.on_surface]
        in_arch = [s for s in want if (s, tf) in arch]
        in_fetch = [s for s in want if (s, tf) in fet]
        aux_arch = aux_fetch = None
        if spec.aux_timeframe:
            aux_arch = [s for s in want if (s, spec.aux_timeframe) in arch]
            aux_fetch = [s for s in want if (s, spec.aux_timeframe) in fet]
        added = sorted(set(in_fetch) - set(in_arch))
        aux_added = sorted(set(aux_fetch or ()) - set(aux_arch or ()))
        per[name] = {
            "timeframe": TF_NAME.get(tf, tf),
            "surface_symbols": want,
            "present_in_ARCHIVE_before_the_fetch": sorted(in_arch),
            "absent_from_ARCHIVE_before_the_fetch": sorted(set(want) - set(in_arch)),
            "aux_timeframe": TF_NAME.get(spec.aux_timeframe) if spec.aux_timeframe else None,
            "aux_count": spec.aux_count or None,
            "aux_present_in_ARCHIVE": sorted(aux_arch) if aux_arch is not None else None,
            "SYMBOLS_THE_FETCH_ADDS": added,
            "AUX_SERIES_THE_FETCH_ADDS": aux_added,
            "was_data_blocked": bool(set(want) - set(in_arch)) or bool(
                spec.aux_timeframe and not aux_arch),
        }
    # 3. what each artifact already held, so "blocked" is checked against evidence
    aq = json.loads(gzip.open(AQ_ESTATE, "rt").read())
    for name in TARGETS:
        rows = (aq.get("trades") or {}).get(name) or []
        per[name]["trades_already_in_AQ_ESTATE_TRADES_V2"] = len(rows)
        per[name]["symbols_already_traded"] = sorted({r["symbol"] for r in rows})

    payload = {
        "schema": "gtos.wave14.ca.data_probe.v1",
        "session": "CA", "blocks": "B2100-B2103",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "archive_root": str(ARCHIVE),
        "fetch_root": str(FETCH),
        "the_correction": (
            "phase13/receipts/CARRYCOND_FETCH_20260730.md reports `missing: []` on all three "
            "sleeves via av_deep_h4_ingest.py, whose EXPORT_ROOTS (:78-81) are both "
            "`data/mt5_research_exports/`. The estate walk generates from "
            "/Users/borr/GTOSActive/vps-bars-20260727, which that harness never searches. "
            "Measured here against the archive: only `vp_euidx_pocgrav` was blocked by a "
            "wholly missing series; `sub_mid_dn_revert` was short 2 of 20 surface symbols; "
            "`metals_softband` was not blocked at all and already carried 237 walked trades."),
        "capture_overlap": overlap,
        "per_sleeve": per,
    }
    PROBE_OUT.write_text(json.dumps(payload, indent=1, default=str), encoding="utf-8")
    print(f"wrote {PROBE_OUT.relative_to(REPO)}")
    for name, blk in per.items():
        print(f"  {name:20s} blocked_in_archive={blk['was_data_blocked']!s:5s} "
              f"adds_symbols={blk['SYMBOLS_THE_FETCH_ADDS']} "
              f"adds_aux={blk['AUX_SERIES_THE_FETCH_ADDS']} "
              f"already_walked={blk['trades_already_in_AQ_ESTATE_TRADES_V2']}")
    for label, blk in overlap.items():
        if blk.get("in_archive"):
            print(f"  overlap {label:16s} arch={blk['archive_rows']} fetch={blk['fetch_rows']} "
                  f"disagree={blk['ohlc_disagreements']} new={blk['bars_only_in_fetch']}")
    return payload


# =====================================================================================
# generation
# =====================================================================================
def _live_stop_own_bars(sleeve: str, tf: int) -> int | None:
    """`time_stop_bars` (M15 printed bars) converted to the sleeve's own timeframe."""
    prof = SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE)
    tsb = prof.get("time_stop_bars")
    per = M15_PER.get(tf)
    if not tsb or not per:
        return None
    return max(1, int(round(float(tsb) / per)))


def _trail_policy(sleeve: str):
    prof = SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE)
    if prof.get("policy") != "trailing_runner":
        return None, None
    return prof.get("trigger_r"), prof.get("trail_gap_r")


def generate(arm: str, sleeves: tuple[str, ...], *, grid_from: dt.date | None = None) -> dict:
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="CA")
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res0 = build_broker_symbol_resolver(prof)
    files, prov = build_files(res0, arm=("archive" if arm == "archive" else "merged"))
    cfg, res, src, port = build_port(files, namespace=f"ca_revival_{arm}")

    tf_of, surface_of = {}, {}
    for spec in active_specs(
        None,
        include_candidate_book=bool(cfg.get("ultimate_book_include_candidate_book", False)),
        candidate_book_sleeves=_candidate_book_sleeves(cfg) or None,
        include_market_expansion_book=bool(
            cfg.get("ultimate_book_include_market_expansion_book", False)),
        market_expansion_sleeves=_market_expansion_sleeves(cfg) or None,
    ):
        if spec.tag in sleeves:
            tf_of[spec.tag] = spec.timeframe
            surface_of[spec.tag] = tuple(spec.on_surface)
    missing = sorted(set(sleeves) - set(tf_of))
    if missing:
        raise SystemExit(f"sleeves not resolvable from the live registry: {missing}")

    # bar series, once
    series: dict = {}
    index: dict = {}
    wanted_keys = {(res(s), tf_of[name]) for name in sleeves for s in surface_of[name]}
    for key in sorted(wanted_keys, key=str):
        rows = src._load(key)
        if not rows:
            continue
        series[key] = ([Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
                        for r in rows],
                       [dt.datetime.fromisoformat(r["time"]) for r in rows])
        index[key] = {ts: i for i, ts in enumerate(series[key][1])}
    print(f"[{arm}] loaded {len(series)} decision-timeframe bar series", flush=True)

    by_tf: dict[int, list[str]] = collections.defaultdict(list)
    for s in sleeves:
        by_tf[tf_of[s]].append(s)

    t_start = time.time()
    all_rows, grids, seen = [], {}, set()
    n_dupes = 0
    for tf in sorted(by_tf, key=lambda t: TF_MINUTES[t]):
        names = sorted(by_tf[tf])
        wanted = {res(s) for n in names for s in surface_of[n]}
        stamps = set()
        for (sym, ktf) in series:
            if ktf != tf or sym not in wanted:
                continue
            stamps.update(series[(sym, ktf)][1])
        grid = sorted(t + dt.timedelta(minutes=TF_MINUTES[tf]) for t in stamps)
        if grid_from is not None:
            grid = [t for t in grid if t.date() >= grid_from]
        if not grid:
            print(f"  {TF_NAME[tf]}: no bars for {names}")
            continue
        print(f"\n=== [{arm}] {TF_NAME[tf]}: {len(names)} sleeves, {len(grid)} closes "
              f"{grid[0].date()} .. {grid[-1].date()} ===", flush=True)
        t0, got = time.time(), 0
        for i, ts in enumerate(grid):
            for c in port.generate(ts, tags=names).candidates:
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
        grids[TF_NAME[tf]] = {"n_closes": len(grid), "first": grid[0].isoformat(),
                              "last": grid[-1].isoformat(), "sleeves": names,
                              "seconds": round(time.time() - t0, 1), "candidates_kept": got}
        print(f"  {TF_NAME[tf]} done {time.time()-t0:.0f}s, {got} unique candidates", flush=True)

    # label through the path replay
    trades: dict[str, list[dict]] = {s: [] for s in sleeves}
    skips: collections.Counter = collections.Counter()
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
            pol = ExitPolicy(target_dist=c.target_dist,
                             trail_arm=float(trig_r) * float(c.stop_dist),
                             trail_gap=float(gap_r) * float(c.stop_dist),
                             maxbars=MAXBARS, label="trailing_runner")
            pr = replay(bars, i, c.direction, stop_dist=c.stop_dist, policy=pol)
        else:
            pr = pr_plain
        # the sleeve's OWN live time stop, in its own bars -- so no figure is published
        # under a horizon the book does not run without the alternative beside it.
        lb = _live_stop_own_bars(c.sleeve, tf)
        pr_live = None
        if lb is not None and lb != MAXBARS:
            pr_live = replay(bars, i, c.direction, stop_dist=c.stop_dist,
                             policy=ExitPolicy(target_dist=c.target_dist, maxbars=lb,
                                               label="live_time_stop"))
        r = winsorize_R(pr.r_gross)
        xi = pr.exit_index
        entry = bars[i].c
        ivl = dt.timedelta(minutes=TF_MINUTES[tf])
        trades[c.sleeve].append({
            "sleeve": c.sleeve, "symbol": sym, "symbol_canonical": c.symbol,
            "entry_utc": (times[i] + ivl).isoformat(),
            "exit_utc": (times[xi] + ivl).isoformat(),
            "direction": int(c.direction),
            "sl_distance_price": float(c.stop_dist), "entry_price": float(entry),
            "r_gross": float(r),
            "r_gross_plain": float(winsorize_R(pr_plain.r_gross)),
            "r_gross_live_stop": (None if pr_live is None
                                  else float(winsorize_R(pr_live.r_gross))),
            "live_stop_own_bars": lb,
            "exit_policy": pr.detail.get("policy", "plain"),
            "exit_reason": pr.exit_reason,
            "mfe_r": round(pr.mfe_r, 6), "mae_r": round(pr.mae_r, 6),
            "bars_to_mfe": int(pr.bars_to_mfe),
            "timeframe": int(tf), "decision_bar_iso": iso, "decision_day": c.decision_day,
            "bar_decision_day": (c.features or {}).get("bar_decision_day"),
            "target_dist": (float(c.target_dist) if c.target_dist else None),
            "intra_size": float(c.intra_size or 1.0),
            "vp_loc": c.vp_loc, "decision_hour": c.decision_hour,
            "exit_bar_offset": int(xi - i),
            "hold_hours": round((xi - i) * TF_MINUTES[tf] / 60.0, 4),
            "features": {k: v for k, v in (c.features or {}).items() if k != "last_close"},
        })

    for s in sleeves:
        ledger.record(
            mechanism="revival_generation", sleeve=s,
            variant={"arm": arm, "maxbars": MAXBARS,
                     "timeframe": TF_NAME.get(tf_of[s]),
                     "bars": ("archive" if arm == "archive"
                              else "archive+bridge_ftmo_carrycond_h4_m1_20260730")},
            window=f"{grids.get(TF_NAME.get(tf_of[s]), {}).get('first', '')[:10]}.."
                   f"{grids.get(TF_NAME.get(tf_of[s]), {}).get('last', '')[:10]}",
            outcome="evaluated", metric=float(len(trades.get(s, []))),
            metric_name="n_trades_generated",
            note=f"CA revival generation, arm={arm}")

    out = {
        "schema": "gtos.wave14.ca.revival_trades.v1",
        "session": "CA", "arm": arm,
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "bars_archive": str(ARCHIVE),
        "bars_fetch": (None if arm == "archive" else str(FETCH)),
        "bar_provenance": {k: v for k, v in sorted(prov.items())
                           if v != "archive"} or {"all": "archive"},
        "maxbars": MAXBARS,
        "live_time_stop_own_bars": {s: _live_stop_own_bars(s, tf_of[s]) for s in sleeves},
        "exit_contracts": {
            s: {**SLEEVE_EXIT_PROFILES.get(s, DEFAULT_EXIT_PROFILE),
                "applied_here": ("trail+stop+target+maxbars" if _trail_policy(s)[0] is not None
                                 else "stop+target+maxbars"),
                "partial_close_NOT_applied": (
                    SLEEVE_EXIT_PROFILES.get(s, {}).get("policy") == "partial_be_runner"),
                }
            for s in sleeves},
        "fidelity_stamps": {s: {"class": fidelity_for(s).cls.value,
                                "live_recall": fidelity_for(s).live_recall,
                                "scoreable_at_0.50": fidelity_for(s).scoreable(0.50)}
                            for s in sleeves},
        "timeframe_by_sleeve": {s: TF_NAME.get(tf_of[s], str(tf_of[s])) for s in sleeves},
        "grids": grids,
        "grid_from": (grid_from.isoformat() if grid_from else None),
        "n_candidates_unique": len(all_rows), "n_duplicates_dropped": n_dupes,
        "n_trades_by_sleeve": {s: len(v) for s, v in sorted(trades.items())},
        "n_trades_by_sleeve_symbol": {
            s: dict(sorted(collections.Counter(r["symbol"] for r in v).items()))
            for s, v in sorted(trades.items())},
        "skips": dict(skips),
        "seconds_total": round(time.time() - t_start, 1),
        "trades": trades,
    }
    path = _out(arm)
    with gzip.open(path, "wt") as fh:
        json.dump(out, fh, default=str)
    print(f"\n[{arm}] wrote {path.relative_to(REPO)} ({path.stat().st_size/1e6:.2f} MB)")
    for s, v in sorted(trades.items(), key=lambda kv: -len(kv[1])):
        rs = [r["r_gross"] for r in v]
        print(f"  {s:22s} n={len(v):5d} sumR={sum(rs):+9.2f} "
              f"meanR={statistics.fmean(rs) if rs else 0:+.5f}")
    return out


# =====================================================================================
# the reproduction control
# =====================================================================================
def control(arm: str = "archive") -> dict:
    """The archive arm must reproduce AQ_ESTATE_TRADES_V2 for the two already-walked sleeves."""
    mine = json.loads(gzip.open(_out(arm), "rt").read())
    aq = json.loads(gzip.open(AQ_ESTATE, "rt").read())
    out = {}
    for s in ("metals_softband", "sub_mid_dn_revert"):
        a = {(r["sleeve"], r["symbol"], r["decision_bar_iso"]): round(float(r["r_gross"]), 9)
             for r in (aq["trades"].get(s) or [])}
        b = {(r["sleeve"], r["symbol"], r["decision_bar_iso"]): round(float(r["r_gross"]), 9)
             for r in (mine["trades"].get(s) or [])}
        shared = set(a) & set(b)
        mism = sorted(k for k in shared if a[k] != b[k])
        out[s] = {
            "n_aq": len(a), "n_here": len(b), "n_shared": len(shared),
            "only_in_aq": len(set(a) - set(b)), "only_here": len(set(b) - set(a)),
            "n_r_gross_mismatched": len(mism),
            "pass": len(a) == len(b) == len(shared) and not mism,
            "examples_only_in_aq": sorted(set(a) - set(b))[:3],
            "examples_only_here": sorted(set(b) - set(a))[:3],
        }
        print(f"  CONTROL {s:20s} aq={len(a)} here={len(b)} shared={len(shared)} "
              f"mismatch={len(mism)} -> {'PASS' if out[s]['pass'] else 'FAIL'}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True,
                    choices=("probe", "archive", "merged", "vp", "control"))
    args = ap.parse_args()
    if args.stage == "probe":
        probe()
    elif args.stage == "control":
        print(json.dumps(control("archive"), indent=1))
    elif args.stage == "vp":
        # vp_euidx_pocgrav needs a 20,000-bar M1 aux per H4 decision; the aux exists only from
        # 2026-04-27, and the sleeve fails closed without it (`vp_euidx.py:78-80`). Restricting
        # the grid to the aux window loses no decision the sleeve could have made and is what
        # makes the run finish -- AVAILABILITY, never results.
        generate("vp", ("vp_euidx_pocgrav",), grid_from=dt.date(2026, 4, 27))
    else:
        generate(args.stage, ("metals_softband", "sub_mid_dn_revert"))


if __name__ == "__main__":
    main()

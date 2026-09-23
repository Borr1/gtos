#!/usr/bin/env python3
"""Armed-sleeve behavioural A/B, BY EXECUTION.

Drives the five armed sleeves' own generator callables over EVERY decision instant in
the FTMO bar archive and hashes the emitted TradeIntent stream. Run at HEAD and at the
pre-repair tree; the two hashes must be identical or a repair moved armed money.

Lives OUTSIDE the repo on purpose: the harness must be byte-identical in both arms while
the repo tree is physically reverted underneath it.
"""
from __future__ import annotations
import datetime as dt, glob, gzip, hashlib, json, os, sys, time
from pathlib import Path

REPO = Path(os.environ.get("V1_REPO", "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"))
sys.path.insert(0, str(REPO))
os.chdir(REPO)

import yaml  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.components.ultimate_book.sleeves import registry as REG  # noqa: E402
from src.components.ultimate_book.primitives import Bar  # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
TF_M15, TF_H4, TF_D1 = 16385, 16388, 16408
TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert",
         "mx_btcusd_d1_donchian_20_breakout")
WINDOW = int(os.environ.get("V1_WINDOW", "400"))
LIMIT_SYMS = os.environ.get("V1_SYMS")           # optional comma list, for timing probes
MAX_BARS = int(os.environ.get("V1_MAXBARS", "0"))  # 0 = whole population

def specs():
    s = REG.active_specs(None, include_candidate_book=True,
                         include_market_expansion_book=True,
                         market_expansion_sleeves=list(REG.MARKET_EXPANSION_BUILT))
    return {x.tag: x for x in s}

def load():
    from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    inv = {v: k for k, v in TF_NAME.items()}
    files = {}
    for p in glob.glob(f"{BARS}/FTMO_*.csv.gz"):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        tf = inv.get(tfs)
        if tf is None:
            continue
        files[(res(sym), tf)] = p
    return CsvBarSource(files, label="v1-armed-ab"), files, res

def main() -> int:
    S = specs()
    src, files, res = load()
    cache: dict[tuple[str, int], tuple[list, list]] = {}

    def series(sym, tf):
        k = (res(sym), tf)
        if k in cache:
            return cache[k]
        if k not in files:
            cache[k] = ([], [])
            return cache[k]
        rows = src._load(k)
        bars = [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0)) for r in rows]
        times = [dt.datetime.fromisoformat(r["time"]) for r in rows]
        cache[k] = (bars, times)
        return cache[k]

    h = hashlib.sha256()
    per = {}
    t0 = time.time()
    for tag in ARMED:
        sp = S[tag]
        syms = list(sp.on_surface)
        if LIMIT_SYMS:
            keep = set(LIMIT_SYMS.split(","))
            syms = [s for s in syms if s in keep]
        n_calls = n_emit = 0
        for sym in syms:
            bars, times = series(sym, sp.timeframe)
            if not bars:
                h.update(f"{tag}|{sym}|NOSERIES\n".encode())
                continue
            end = len(bars) if not MAX_BARS else min(len(bars), WINDOW + MAX_BARS)
            for i in range(WINDOW, end):
                w = bars[i - WINDOW + 1: i + 1]
                bt = times[i]
                day = bt.date().isoformat()
                n_calls += 1
                try:
                    out = sp.generator(sym, w, day, bar_time=bt)
                except Exception as exc:
                    line = f"{tag}|{sym}|{bt.isoformat()}|EXC|{type(exc).__name__}|{exc}\n"
                    h.update(line.encode()); continue
                if out is None:
                    continue
                n_emit += 1
                fields = []
                for k in sorted(vars(out)) if hasattr(out, "__dict__") else []:
                    fields.append(f"{k}={vars(out)[k]!r}")
                if not fields:  # dataclass with slots / frozen
                    fields = [repr(out)]
                line = f"{tag}|{sym}|{bt.isoformat()}|" + ";".join(fields) + "\n"
                h.update(line.encode())
        per[tag] = {"symbols": len(syms), "calls": n_calls, "emissions": n_emit}
        print(f"  {tag:38s} syms={len(syms):3d} calls={n_calls:7d} emit={n_emit:6d} "
              f"({time.time()-t0:6.1f}s)", flush=True)
    res = {"window": WINDOW, "max_bars": MAX_BARS or None, "armed": list(ARMED),
           "per_sleeve": per,
           "total_calls": sum(v["calls"] for v in per.values()),
           "total_emissions": sum(v["emissions"] for v in per.values()),
           "stream_sha256": h.hexdigest(),
           "elapsed_s": round(time.time() - t0, 1)}
    print(json.dumps(res, indent=1))
    out = os.environ.get("V1_OUT")
    if out:
        json.dump(res, open(out, "w"), indent=1)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

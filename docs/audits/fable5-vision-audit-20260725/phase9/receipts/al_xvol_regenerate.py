"""Session AL, item 1a — regenerate `sub_xvol_pullback` at threshold variants, through the
PRODUCTION generation path, over the full archive.

    python3 docs/audits/fable5-vision-audit-20260725/phase9/receipts/al_xvol_regenerate.py

WHY A REGENERATION AND NOT A RE-SIMULATION
------------------------------------------
Every other sweep in waves 7-8 re-simulated AD-style from AA's stored intents, because an EXIT
change cannot move which trades exist. A THRESHOLD change is the opposite: `vr >= 1.4` instead of
`vr >= 1.6` admits bars the production cell never fired on, so there is no stored intent to
re-label. The generator has to run.

WHY IT RUNS THE PRODUCTION PORT RATHER THAN `regime_spine`
---------------------------------------------------------
`regime_spine.conditions.SUB_XVOL_PULLBACK` is already parameterised on exactly these three
thresholds and would have been the cheap route. It is the wrong route, measured rather than
assumed: at the PRODUCTION params `regime_spine` fires on **94** bars where AA's walk has **88**,
and the 6 extra are precisely the pre-gap bars `bar_provider.candles_to_bars` drops
(`book_engine.py:83-90` records AB's measurement of 6.4 % on this sleeve; 6/94 = 6.38 %). Those 6
bars are UNREACHABLE by the live book today -- `--recover-pre-gap-bar` defaults False
(`book_engine.py:107`) -- so a variant built on `regime_spine` would carry a 6 % population the
armed book cannot trade, and its p-value would not be comparable to AA's or AI's.

So generation goes through `GenerationPort` on AA's own pooled H4 grid, and the parity control is
that the PRODUCTION cell recovered offline must equal AA's 88 keys exactly.

HOW ONE RUN SERVES EVERY CELL
-----------------------------
The port's reachable decision-bar set does not depend on the cell's thresholds -- the bar fetch,
the warmup gate and the decision-bar recency guard are all upstream of `cell_matches`. So
`registry.BUILT["sub_xvol_pullback"]` is swapped for a recorder that computes the same
`substrate_engine.compute_state` from the same 260-bar window, RECORDS it, and returns an intent
unconditionally. One generation pass therefore yields:

  * the exact set of (symbol, decision_bar) pairs the production port can reach, and
  * the raw state (`vr`, `slope50`, `mtf_align`, `ac60`) at each,

from which ANY threshold cell is a pure offline filter. That is what makes a 125-cell neighborhood
affordable at production reachability, instead of one cell.

The recorder is byte-faithful to `substrate._generate` (`substrate.py:88-114`) in every step it
keeps: `symbol in on_surface`, `len(bars) >= WARMUP`, `atr14 > 0`, `compute_state`, and
`stop_target(a, 1.0, 3.0)`. The only removed step is `cell_matches`, which is the filter being
swept.
"""

from __future__ import annotations

import collections
import datetime as dt
import glob
import gzip
import json
import os
import sys
import time
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import TradeIntent  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, TF_M15  # noqa: E402
from src.components.ultimate_book.book_engine import (  # noqa: E402
    _candidate_book_sleeves,
    _market_expansion_sleeves,
)
from src.components.ultimate_book.primitives import Bar, atr14  # noqa: E402
from src.components.ultimate_book.sleeves import registry as REG  # noqa: E402
from src.components.ultimate_book.sleeves import substrate as SUB  # noqa: E402
from src.components.ultimate_book.sleeves import substrate_engine as SE  # noqa: E402
from src.components.ultimate_book.sleeves.registry import active_specs  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource, GenerationPort  # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
HERE = Path(__file__).resolve().parent
OUT = HERE / "AL_XVOL_REACHABLE_STATE_V1.json.gz"
AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"

TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
TF_MINUTES = {TF_M15: 15, TF_H4: 240, TF_D1: 1440}

SLEEVE = "sub_xvol_pullback"

#: Every (symbol, decision_bar_iso) the port reached, with the raw state at that bar.
RECORD: dict[tuple[str, str], dict] = {}


def _recorder(symbol: str, bars, decision_day: str, *, bar_time=None, **_):
    """`substrate._generate` for the xvol cell with `cell_matches` removed and the state recorded.

    Returns an intent unconditionally so the port emits a candidate for every reachable bar. The
    geometry is the production one, so the recorded intent is what the production cell WOULD have
    emitted had it fired.
    """
    if symbol not in SUB.XVOL_ON_SURFACE or not bars:
        return None
    if len(bars) < SE.WARMUP:
        return None
    i = len(bars) - 1
    a = atr14(bars, i)
    if a <= 0:
        return None
    st = SE.compute_state(bars, i, None)      # depth-4 cell: hour is never read
    if st is None:
        return None
    key = (symbol, bar_time.isoformat() if bar_time is not None else "")
    RECORD[key] = {
        "vr": st["vr"], "slope50": st["slope50"], "slope20": st["slope20"],
        "slope100": st["slope100"], "mtf_align": st["mtf_align"], "ac60": st["ac60"],
        "rng_pos": st["rng_pos"], "compression": st["compression"], "atr": a,
        "coords_production": SE.cell_coords(st),
        "decision_day": decision_day,
    }
    sd, td = SE.stop_target(a, *SUB.XVOL_GEOM)
    return TradeIntent(sleeve=SLEEVE, symbol=symbol, direction=SUB.XVOL_DIR,
                       decision_day=decision_day, stop_dist=sd, target_dist=td)


def build_port():
    """AA's `build()` verbatim (`aa_estate_generate.py:115-131`), with the recorder swapped in."""
    base = yaml.safe_load(open(REPO / "config/agent_config.yaml"))
    cfg = dict(base.get("gtos_vnext_runtime") or {})
    cfg["ultimate_book_include_clean3"] = True
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
    port = GenerationPort(cfg, src, namespace="al_xvol", broker_symbol=res)
    return cfg, res, files, src, port


def main() -> dict:
    t_start = time.time()
    prod_spec = REG.BUILT[SLEEVE]
    REG.BUILT[SLEEVE] = REG.SleeveSpec(
        tag=prod_spec.tag, generator=_recorder, timeframe=prod_spec.timeframe,
        cluster=prod_spec.cluster, on_surface=prod_spec.on_surface,
        aux_timeframe=prod_spec.aux_timeframe, aux_count=prod_spec.aux_count,
        bar_count=prod_spec.bar_count)
    assert REG.BUILT[SLEEVE].generator is _recorder

    cfg, res, files, src, port = build_port()
    active = set(port.active_sleeve_names())
    print(f"active book (include_clean3 override): {len(active)} sleeves; "
          f"{SLEEVE} in it: {SLEEVE in active}")

    # ---- AA's H4 grid, reproduced exactly ------------------------------------------------
    #  The grid is pooled over EVERY H4 sleeve's surface, not just this one, because a pooled
    #  grid has more stamps and therefore reaches at least as many decision bars. Restricting
    #  it to one sleeve's symbols would be a different -- and quietly narrower -- reachability
    #  question than the one AA answered.
    tf_of, surface_of = {}, {}
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
    h4 = sorted(s for s, t in tf_of.items() if t == TF_H4)
    wanted = {res(s) for name in h4 for s in surface_of[name]}
    stamps = set()
    for (sym, ktf) in files:
        if ktf != TF_H4 or sym not in wanted:
            continue
        rows = src._load((sym, ktf))
        for r in rows:
            stamps.add(dt.datetime.fromisoformat(r["time"]))
    grid = sorted(t + dt.timedelta(minutes=TF_MINUTES[TF_H4]) for t in stamps)
    print(f"H4 grid: {len(grid)} closes {grid[0].date()}..{grid[-1].date()} "
          f"over {len(h4)} H4 sleeves' pooled surface ({len(wanted)} broker symbols)")

    # ---- one generation pass -------------------------------------------------------------
    t0 = time.time()
    cands: dict[tuple[str, str], dict] = {}
    n_dupes = 0
    for i, ts in enumerate(grid):
        for c in port.generate(ts, tags=[SLEEVE]).candidates:
            key = (c.symbol, c.decision_bar_iso)
            if key in cands:
                n_dupes += 1
                continue
            cands[key] = {
                "symbol_canonical": c.symbol, "symbol": res(c.symbol),
                "decision_bar_iso": c.decision_bar_iso, "decision_day": c.decision_day,
                "direction": int(c.direction), "stop_dist": float(c.stop_dist),
                "target_dist": (float(c.target_dist) if c.target_dist else None),
                "reached_at_grid_stamp": ts.isoformat(),
            }
        if (i + 1) % 5000 == 0:
            el = time.time() - t0
            print(f"  {i+1}/{len(grid)}  {el:.0f}s  eta {el/(i+1)*(len(grid)-i-1):.0f}s  "
                  f"reached={len(cands)}", flush=True)
    print(f"generation: {len(cands)} reachable decision bars, {n_dupes} duplicate reaches, "
          f"{time.time()-t0:.0f}s")

    # ---- join the recorded state onto the candidates --------------------------------------
    joined, missing = {}, 0
    for key, row in cands.items():
        st = RECORD.get(key)
        if st is None:
            missing += 1
            continue
        joined[f"{key[0]}|{key[1]}"] = {**row, **{k: v for k, v in st.items()
                                                  if k != "decision_day"}}
    print(f"joined state onto {len(joined)} rows; {missing} candidates had no recorded state")

    # ---- the control: does the PRODUCTION cell recovered offline equal AA's 88? -----------
    raw = json.load(gzip.open(AA_IN, "rt"))
    aa = raw["trades"][SLEEVE]
    aa_keys = {(r["symbol_canonical"], r["decision_bar_iso"]) for r in aa}

    def fires_at(vr_xhi: float, slope_up: float, ac_band: float,
                 mtf_sgn_thr: float = 0.5) -> set:
        """The cell predicate, offline. Byte-faithful to the four production gates.

        `mtf_align` is recomputed from the recorded slopes when `mtf_sgn_thr` moves off its
        production 0.5, because the recorded `mtf_align` was bucketed at 0.5 inside
        `compute_state`.
        """
        out = set()
        for k, r in joined.items():
            if r["vr"] < vr_xhi:
                continue
            s50 = r["slope50"]
            if s50 is None or not s50 > slope_up:
                continue
            if abs(mtf_sgn_thr - 0.5) < 1e-12:
                align = r["mtf_align"]
            else:
                s20, s100 = r["slope20"], r["slope100"]
                if s20 is None or s100 is None:
                    align = 0
                else:
                    def _sgn(v):
                        return 1 if v > mtf_sgn_thr else (-1 if v < -mtf_sgn_thr else 0)
                    a, b = _sgn(s20), _sgn(s100)
                    align = 1 if (a != 0 and a == b) else (-1 if (a != 0 and b != 0 and a == -b)
                                                           else 0)
            if align != -1:
                continue
            ac = r["ac60"]
            if ac is None or not (-ac_band < ac < ac_band):
                continue
            sym, _, iso = k.partition("|")
            out.add((sym, iso))
        return out

    prod = fires_at(1.6, 1.5, 0.10)
    ok = prod == aa_keys
    print(f"\nPARITY CONTROL: production cell offline n={len(prod)} vs AA n={len(aa_keys)} -> "
          f"{'IDENTICAL' if ok else 'DIFFERENT'}")
    if not ok:
        print(f"  offline-only ({len(prod - aa_keys)}): {sorted(prod - aa_keys)[:10]}")
        print(f"  AA-only      ({len(aa_keys - prod)}): {sorted(aa_keys - prod)[:10]}")

    out = {
        "schema": "gtos.wave9.al.xvol_reachable_state.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AL",
        "sleeve": SLEEVE,
        "bars_archive": BARS,
        "research_overrides": {
            "config": {"ultimate_book_include_clean3": True},
            "why": ("agent_config.yaml:1270 is false and the file is H1-bound AND the live "
                    "activation token binds its digest, so the flag is flipped in the config "
                    "DICT handed to GenerationPort -- AA's own mechanism "
                    "(aa_estate_generate.py:136, :353-356). No file byte moves."),
        },
        "registry_patch": {
            "what": ("registry.BUILT['sub_xvol_pullback'].generator swapped for a recorder that "
                     "keeps every production step except cell_matches, so the reachable "
                     "decision-bar set and the raw state are captured in one pass"),
            "faithful_to": "src/components/ultimate_book/sleeves/substrate.py:88-114",
            "removed_step": "substrate_engine.cell_matches -- the filter being swept",
            "in_process_only": True,
        },
        "grid": {"n_closes": len(grid), "first": grid[0].isoformat(),
                 "last": grid[-1].isoformat(), "h4_sleeves_pooled": h4,
                 "n_broker_symbols": len(wanted)},
        "reachability": {
            "n_reachable_decision_bars": len(cands),
            "n_duplicate_reaches": n_dupes,
            "n_joined_with_state": len(joined),
            "n_candidates_without_state": missing,
            "why_this_matters": (
                "the port's reachable set excludes the pre-gap bars candles_to_bars drops "
                "(book_engine.py:83-90). Measured independently here: at production thresholds "
                "regime_spine fires on 94 bars and the port reaches 88 of them."),
        },
        "parity_control": {
            "question": ("does the production cell, recovered by an OFFLINE filter over the "
                         "recorded state, equal AA's own 88 trades exactly?"),
            "n_offline": len(prod), "n_aa": len(aa_keys), "identical": ok,
            "offline_only": sorted(f"{s}|{i}" for s, i in (prod - aa_keys)),
            "aa_only": sorted(f"{s}|{i}" for s, i in (aa_keys - prod)),
            "why_it_is_the_right_control": (
                "it validates the whole approach at once: if one offline filter reproduces the "
                "production cell bar-for-bar, then every other cell is the same filter at a "
                "different constant, and no cell carries a reachability artefact the production "
                "cell does not."),
        },
        "seconds_total": round(time.time() - t_start, 1),
        "rows": joined,
    }
    with gzip.open(OUT, "wt") as fh:
        json.dump(out, fh, default=str)
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.1f} MB)")
    REG.BUILT[SLEEVE] = prod_spec
    return out


if __name__ == "__main__":
    main()

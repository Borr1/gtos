"""d4_lookahead — direct probe: can any candidate see a bar that had not printed?

Two arms at the SAME decision instant T:

  A  sources trimmed to [T-75d, T+2d]  (what pbg/the replay actually pass; the
     asof filter inside `raw_data_for_asof` is the only thing standing between
     the generator and the future)
  B  sources HARD-TRUNCATED to [T-75d, T] — no row whose close is after T exists
     at all, on any timeframe, for any symbol, including the cross-asset leaders

If the asof contract is airtight, every emitted candidate is byte-identical.
Any difference is look-ahead, and the diff names the family.
"""
from __future__ import annotations
import sys, os, json
from datetime import datetime, timedelta, timezone
from pathlib import Path

PBG = Path("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/"
           "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg")
REPO = PBG.parents[5]
sys.path.insert(0, str(PBG)); sys.path.insert(0, str(REPO)); os.chdir(REPO)
import pbg_lib as L
from src.research_infra.v4_timewarp_simulated_live_research_loop import (
    raw_data_for_asof, replay_symbol_config, derive_session, ResolvedSource, SourceSpec)
from src.components.market_state import compute_market_state
from src.components.broader_origin_generators import generate_live_broader_origin_candidates

KEYS = ("origin_family", "side", "entry_price", "stop_loss", "take_profit_1", "candidate_id")


def build(symbols, lo, hi, cfg):
    out = {}
    for sym in symbols:
        m15 = [r for r in L.read_csv_bars(L.M15_DIR / f"{sym}_M15.csv")
               if lo <= datetime.fromisoformat(r["time_utc"]) <= hi]
        h1 = L.aggregate_h1(m15)
        h4 = [r for r in L.read_csv_bars(L.deep_path(sym, "H4"))
              if lo <= datetime.fromisoformat(r["time_utc"]) <= hi]
        d1 = [r for r in L.read_csv_bars(L.deep_path(sym, "D1"))
              if lo <= datetime.fromisoformat(r["time_utc"]) <= hi]
        per = {}
        for tf, rows in (("M15", m15), ("H1", h1), ("H4", h4), ("D1", d1)):
            per[tf] = ResolvedSource(
                spec=SourceSpec(symbol=sym, mapped_symbol=sym, timeframe=tf,
                                path=Path(f"d4://{sym}/{tf}"), source_family="lane_inputs_true_utc_v1",
                                source_broker="ftmo", source_role="research"),
                rows=tuple(rows), rows_by_day={}, sha256="d4", day_counts={},
                selected_status="d4", min_required_rows_per_day=0)
        out[sym] = per
    return out


def emit(sources, scfg, symbols, T):
    raw_by = {}; mso_by = {}
    for sym in symbols:
        try:
            raw, _ = raw_data_for_asof(symbol=sym, sources=sources[sym], asof=T, config=scfg[sym])
            mso = compute_market_state(raw, scfg[sym])
        except Exception:
            continue
        raw_by[sym] = raw; mso_by[sym] = mso
    xd = {"raw_data_by_symbol": raw_by}
    rows = []
    for sym, raw in raw_by.items():
        kz = derive_session(sym, T)
        for c in generate_live_broader_origin_candidates(raw, mso_by[sym], scfg[sym], sym, kz, xd, now_utc=T):
            rows.append((sym,) + tuple(c.get(k) for k in KEYS))
    return sorted(rows, key=lambda r: (r[0], str(r[1]), str(r[2]), str(r[6])))


def main():
    symbols = list(L.SYMBOLS)
    cfg = L.load_replay_config()
    ms = cfg.setdefault("market_state", {})
    ms["side_effect_writes_enabled"] = False
    ms["structure_shadow_log_enabled"] = False
    scfg = {s: replay_symbol_config(cfg, s) for s in symbols}
    days = ["2025-11-12", "2026-04-15"]
    instants = [0, 12, 26, 34, 40, 52, 58, 64, 72, 84, 90, 95]
    res = {"instants_tested": 0, "rows_A": 0, "rows_B": 0, "mismatched_instants": [],
           "identical_instants": 0, "per_family_A": {}, "per_family_B": {}}
    from collections import Counter
    fa = Counter(); fb = Counter()
    for day in days:
        d0 = datetime.fromisoformat(day + "T00:00:00+00:00")
        lo = d0 - timedelta(days=75)
        srcA = build(symbols, lo, d0 + timedelta(days=2), cfg)
        for k in instants:
            T = d0 + timedelta(minutes=15 * k)
            srcB = build(symbols, lo, T, cfg)
            A = emit(srcA, scfg, symbols, T)
            B = emit(srcB, scfg, symbols, T)
            res["instants_tested"] += 1
            res["rows_A"] += len(A); res["rows_B"] += len(B)
            for r in A: fa[r[1]] += 1
            for r in B: fb[r[1]] += 1
            if A == B:
                res["identical_instants"] += 1
            else:
                sa = set(map(str, A)); sb = set(map(str, B))
                res["mismatched_instants"].append({
                    "day": day, "instant": T.isoformat(),
                    "only_in_full_source": sorted(sa - sb)[:6],
                    "only_in_truncated": sorted(sb - sa)[:6],
                    "n_only_full": len(sa - sb), "n_only_trunc": len(sb - sa)})
            print(day, T.time(), "A", len(A), "B", len(B), "identical" if A == B else "DIFF", flush=True)
    res["per_family_A"] = dict(fa); res["per_family_B"] = dict(fb)
    Path("/tmp/d4/out/LOOKAHEAD_V1.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "mismatched_instants"}, indent=1))


if __name__ == "__main__":
    main()

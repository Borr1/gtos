"""d4_poi_capture — capture the POI ZONE behind every current_* candidate, so the
family's defining condition can be checked against price.

`_source_detail` (broader_origin_generators.py:1728-1750) already JSON-encodes
zone_low / zone_high / formation_time / mitigation_time and the finalizer copies
it onto the candidate as ``candidate_source_detail`` (:387-388).  Nothing under
src/ is edited.
"""
from __future__ import annotations
import sys, os, gzip, json, argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

PBG = Path("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/"
           "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg")
REPO = PBG.parents[5]
sys.path.insert(0, str(PBG)); sys.path.insert(0, str(REPO)); os.chdir(REPO)
import pbg_lib as L
import pbg_run as R
from src.research_infra.v4_timewarp_simulated_live_research_loop import (
    raw_data_for_asof, derive_session)
from src.components.market_state import compute_market_state
from src.components.broader_origin_generators import generate_live_broader_origin_candidates

POI = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}


def run_day(day, symbols, out_dir, min_rr):
    sources, _m1, scfg = R.build_day_context(symbols, day, min_rr, [])
    d0 = datetime.fromisoformat(day + "T00:00:00+00:00")
    path = Path(out_dir) / f"poi_{day}.jsonl.gz"
    n = 0
    with gzip.open(path, "wt") as fh:
        for k in range(96):
            T = d0 + timedelta(minutes=15 * k)
            raw_by = {}; mso_by = {}
            for sym in symbols:
                try:
                    raw, _ = raw_data_for_asof(symbol=sym, sources=sources[sym], asof=T, config=scfg[sym])
                    mso = compute_market_state(raw, scfg[sym])
                except Exception:
                    continue
                raw_by[sym] = raw; mso_by[sym] = mso
            xd = {"raw_data_by_symbol": raw_by}
            for sym, raw in raw_by.items():
                kz = derive_session(sym, T)
                for c in generate_live_broader_origin_candidates(
                        raw, mso_by[sym], scfg[sym], sym, kz, xd, now_utc=T):
                    fam = c.get("origin_family")
                    if fam not in POI:
                        continue
                    try:
                        det = json.loads(c.get("candidate_source_detail") or "{}")
                    except Exception:
                        det = {}
                    sf = c.get("source_fields") or {}
                    fh.write(json.dumps({
                        "t": T.isoformat(), "s": sym, "f": fam,
                        "d": "L" if str(c.get("side", "")).upper() == "LONG" else "S",
                        "e": float(c["entry_price"]), "sl": float(c["stop_loss"]),
                        "tp": float(c.get("take_profit_1") or 0.0),
                        "zl": det.get("zone_low"), "zh": det.get("zone_high"),
                        "ft": det.get("formation_time"), "mt": det.get("mitigation_time"),
                        "cp": sf.get("current_price"), "atr": sf.get("atr14"),
                        "prox": sf.get("proximity_gap_pct"),
                        "tc": c.get("poi_touch_count"),
                        "mit": c.get("poi_max_mitigation_fraction"),
                        "age": c.get("poi_age_hours"),
                    }, separators=(",", ":")) + "\n")
                    n += 1
    (Path(out_dir) / f"poi_{day}.stats.json").write_text(json.dumps({"day": day, "rows": n}))
    return {"day": day, "rows": n}


class _J:
    def __init__(self, syms, od, rr): self.a = (syms, od, rr)
    def __call__(self, d):
        s, o, r = self.a
        return run_day(d, s, o, r)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-rr", type=float, default=1.5)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    days = [d for d in a.days.split(",") if d]
    syms = list(L.SYMBOLS)
    import multiprocessing as mp
    with mp.get_context("fork").Pool(a.workers) as p:
        for st in p.imap_unordered(_J(syms, a.out, a.min_rr), days):
            print(json.dumps(st), flush=True)

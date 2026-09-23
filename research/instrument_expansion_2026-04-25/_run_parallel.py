"""Parallel runner — analyzes all 24 instruments via process pool."""
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))


def _analyze(symbol: str) -> dict:
    """Worker — runs analyze_instrument in a fresh process."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "decay_analysis_mod",
        Path(__file__).parent / "02_decay_analysis.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["decay_analysis_mod"] = mod
    spec.loader.exec_module(mod)
    r = mod.analyze_instrument(symbol)
    return {
        "symbol": r.symbol,
        "monthly": r.monthly,
        "h1h2": r.h1h2,
        "trends": r.trends,
        "stability": r.stability,
        "decay_score": r.decay_score,
        "composite_dir": r.composite_dir,
    }


INSTRUMENTS = [
    "AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD",
    "EURGBP", "EURJPY", "EURUSD", "GBPJPY", "GBPUSD",
    "GER40", "JP225", "NAS100", "NZDUSD", "SPX500",
    "UK100", "UKOIL_cash", "US30_cash", "USDCAD", "USDCHF",
    "USDJPY", "USOIL_cash", "XAGUSD", "XAUUSD",
]


def main():
    OUT_DIR = Path(__file__).parent
    print(f"Analyzing {len(INSTRUMENTS)} instruments in parallel...")
    t0 = time.time()
    payload = []
    failed = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_analyze, sym): sym for sym in INSTRUMENTS}
        for fut in as_completed(futs):
            sym = futs[fut]
            try:
                payload.append(fut.result())
                done = len(payload)
                print(f"  [{done}/{len(INSTRUMENTS)}] {sym}  (t+{time.time()-t0:.0f}s)")
            except Exception as e:
                failed.append((sym, str(e)))
                print(f"  FAILED {sym}: {e}")

    # Save full results
    payload.sort(key=lambda d: d["symbol"])
    with open(OUT_DIR / "02_results.json", "w") as f:
        json.dump(payload, f, indent=2, default=str)

    # Long-format monthly metrics
    rows_monthly = []
    for r in payload:
        for mo, d in r["monthly"].items():
            for met, v in d.items():
                rows_monthly.append({
                    "instrument": r["symbol"], "month": mo, "metric": met, "value": v,
                })
    pd.DataFrame(rows_monthly).to_csv(OUT_DIR / "02_monthly_metrics.csv", index=False)

    # H1/H2 split
    rows_h = []
    for r in payload:
        for met, d in r["h1h2"].items():
            rows_h.append({
                "instrument": r["symbol"], "metric": met,
                "h1_mean": d.get("h1_mean"), "h2_mean": d.get("h2_mean"),
                "delta": d.get("delta"), "p_value": d.get("p_value"),
                "h1_n": d.get("h1_n"), "h2_n": d.get("h2_n"),
            })
    pd.DataFrame(rows_h).to_csv(OUT_DIR / "02_h1_h2_split.csv", index=False)

    # Per-instrument scorecard
    def _ac(s):
        if s in {"XAUUSD", "XAGUSD"}: return "METALS"
        if s in {"BTCUSD", "ETHUSD"}: return "CRYPTO"
        if s in {"GER40", "JP225", "NAS100", "SPX500", "UK100", "US30_cash"}: return "INDEX"
        if s in {"UKOIL_cash", "USOIL_cash"}: return "ENERGY"
        return "FX"

    rows_score = []
    for r in payload:
        dirs = {met: r["trends"][met]["direction"] for met in r["trends"]}
        # Identify Apr-confidence
        apr_data = r["monthly"].get("2026-04", {})
        apr_n = apr_data.get("m15_candle_count", 0)
        full_apr = apr_n >= 1500
        rows_score.append({
            "instrument": r["symbol"],
            "asset_class": _ac(r["symbol"]),
            "months_observed": len(r["monthly"]),
            "apr_m15_candles": apr_n,
            "data_quality": "FULL" if full_apr else ("PARTIAL_APR" if apr_n > 0 else "NO_APR"),
            "composite_direction": r["composite_dir"],
            "decay_score": r["decay_score"],
            "h1_bos_retest_wr_dir": dirs.get("h1_bos_retest_wr"),
            "ob_per_day_dir": dirs.get("ob_per_day"),
            "bos_per_day_dir": dirs.get("bos_per_day"),
            "fvg_per_100_dir": dirs.get("fvg_per_100"),
            "displacement_rate_dir": dirs.get("displacement_rate"),
            "atr_m15_dir": dirs.get("atr_m15"),
            "atr_h1_dir": dirs.get("atr_h1"),
            "vol_persistence_dir": dirs.get("vol_persistence"),
            "ac1_logret_dir": dirs.get("ac1_logret"),
            "hurst_dir": dirs.get("hurst"),
            "sweep_reversal_wr_dir": dirs.get("sweep_reversal_wr"),
            "h1_bos_wr_h1": r["h1h2"].get("h1_bos_retest_wr", {}).get("h1_mean"),
            "h1_bos_wr_h2": r["h1h2"].get("h1_bos_retest_wr", {}).get("h2_mean"),
            "h1_bos_wr_delta": r["h1h2"].get("h1_bos_retest_wr", {}).get("delta"),
            "h1_bos_wr_p": r["h1h2"].get("h1_bos_retest_wr", {}).get("p_value"),
            "h1_bos_wr_h1_n": r["h1h2"].get("h1_bos_retest_wr", {}).get("h1_n"),
            "h1_bos_wr_h2_n": r["h1h2"].get("h1_bos_retest_wr", {}).get("h2_n"),
            "sweep_wr_h1": r["h1h2"].get("sweep_reversal_wr", {}).get("h1_mean"),
            "sweep_wr_h2": r["h1h2"].get("sweep_reversal_wr", {}).get("h2_mean"),
            "sweep_wr_p": r["h1h2"].get("sweep_reversal_wr", {}).get("p_value"),
            "ob_per_day_h1": r["h1h2"].get("ob_per_day", {}).get("h1_mean"),
            "ob_per_day_h2": r["h1h2"].get("ob_per_day", {}).get("h2_mean"),
            "atr_m15_h1": r["h1h2"].get("atr_m15", {}).get("h1_mean"),
            "atr_m15_h2": r["h1h2"].get("atr_m15", {}).get("h2_mean"),
        })
    df_score = pd.DataFrame(rows_score).sort_values("decay_score", ascending=False)
    df_score.to_csv(OUT_DIR / "02_per_instrument_decay_scorecard.csv", index=False)

    # Decay clusters
    rows_cluster = []
    for r in payload:
        sig = "".join(
            ("D" if r["trends"][met]["direction"] == "DECAYING" else
             "I" if r["trends"][met]["direction"] == "IMPROVING" else
             "S" if r["trends"][met]["direction"] == "STABLE" else "V")
            for met in ("h1_bos_retest_wr", "ob_per_day", "displacement_rate", "atr_m15", "vol_persistence")
        )
        rows_cluster.append({
            "instrument": r["symbol"],
            "edge_pattern": sig,
            "asset_class": _ac(r["symbol"]),
            "decay_score": r["decay_score"],
            "composite_direction": r["composite_dir"],
        })
    df_clu = pd.DataFrame(rows_cluster).sort_values(["edge_pattern", "decay_score"], ascending=[True, False])
    df_clu.to_csv(OUT_DIR / "02_decay_clusters.csv", index=False)

    print(f"\nElapsed: {time.time()-t0:.0f}s")
    print(f"Failures: {len(failed)}")
    if failed:
        for sym, err in failed:
            print(f"  {sym}: {err}")


if __name__ == "__main__":
    main()

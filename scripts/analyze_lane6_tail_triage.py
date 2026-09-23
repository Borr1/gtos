#!/usr/bin/env python3
"""Lane 6 tail backlog triage.

Research/tooling only. The script inventories local evidence for the next
unblocked queue batch after the priority-620 triage and writes a versioned
report. It does not change live trading logic, prompts, risk settings, or
execution behavior.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_OUTPUT_JSON = "research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.json"
DEFAULT_OUTPUT_MD = "research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md"

CURRENT_SYMBOL_FILES = {
    "XAUUSD": "XAUUSD",
    "US30": "US30_cash",
    "USDJPY": "USDJPY",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD",
    "XAGUSD": "XAGUSD",
    "NAS100": "NAS100",
}


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def latest_file(root: Path, pattern: str) -> Path | None:
    files = sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime if p.exists() else 0)
    return files[-1] if files else None


def hpm_inventory(root: Path) -> dict[str, Any]:
    hpm01 = load_json(root / "research" / "ml_program" / "phase_2" / "position_mgmt" / "h_pm01_per_cohort_results.json") or {}
    hpm03 = load_json(root / "research" / "ml_program" / "phase_2" / "position_mgmt" / "h_pm03_mc_results.json") or {}
    combined = load_json(root / "research" / "ml_program" / "phase_2" / "position_mgmt" / "combined_mc_results.json") or {}
    primary = hpm01.get("primary_full_cohort", {}) or {}
    per_inst = (hpm01.get("per_cohort", {}) or {}).get("per_instrument", {}) or {}
    hpm03_decision = hpm03.get("decision_summary", {}) or {}
    combined_decision = combined.get("decision", {}) or {}
    return {
        "hpm01_exists": bool(hpm01),
        "hpm01_delta_mean_r": (((primary.get("backtest") or {}).get("delta") or {}).get("mean_r")),
        "hpm01_delta_sharpe_pct": (((primary.get("backtest") or {}).get("delta") or {}).get("sharpe_pct")),
        "hpm01_dsr_p": ((primary.get("dsr_paired_delta") or {}).get("dsr_p")),
        "hpm01_nas100_delta_r": (((per_inst.get("NAS100") or {}).get("backtest") or {}).get("delta") or {}).get("mean_r"),
        "hpm01_nas100_dsr_p": ((per_inst.get("NAS100") or {}).get("dsr_paired") or {}).get("dsr_p"),
        "hpm03_side_aware_h2_p_pass": ((hpm03_decision.get("risk_adjusted_winner") or {}).get("winner_h2_p_pass")),
        "hpm03_side_aware_full_p_bust_hard": ((hpm03_decision.get("full_cohort") or {}).get("p_bust_hard_max_sae")),
        "combined_realistic_density_p_pass": ((combined_decision.get("PRIMARY_full_stack_realistic_density") or {}).get("p_pass")),
    }


def count_latest_jsonl(root: Path, pattern: str) -> dict[str, Any]:
    latest = latest_file(root, pattern)
    if latest is None:
        return {"latest_file": None, "rows": 0, "symbols": {}}
    rows = read_jsonl(latest)
    symbols = Counter(str(row.get("gtos_symbol") or row.get("symbol") or row.get("underlying") or "unknown") for row in rows)
    return {"latest_file": str(latest), "rows": len(rows), "symbols": dict(sorted(symbols.items()))}


def wgc_inventory(root: Path) -> dict[str, Any]:
    wgc_root = root / "data" / "external" / "normalized" / "wgc"
    demand = count_latest_jsonl(wgc_root, "gold_demand_trends_*.jsonl")
    etf = count_latest_jsonl(wgc_root, "gold_etf_flows_*.jsonl")
    latest_demand = latest_file(wgc_root, "gold_demand_trends_*.jsonl")
    demand_rows = read_jsonl(latest_demand) if latest_demand else []
    central_bank_rows = [
        row
        for row in demand_rows
        if "central" in str(row).lower() or "official" in str(row).lower() or "institution" in str(row).lower()
    ]
    return {
        "demand": demand,
        "etf": etf,
        "central_bank_like_rows": len(central_bank_rows),
    }


def tick_inventory(root: Path) -> dict[str, Any]:
    ticks_root = root / "data" / "ticks"
    files = list(ticks_root.glob("*/*.parquet"))
    by_symbol = Counter(path.parent.name for path in files)
    return {"files": len(files), "symbols": dict(sorted(by_symbol.items()))}


def source_inventory(root: Path) -> dict[str, Any]:
    normalized_root = root / "data" / "external" / "normalized"
    return {
        "normalized_sources": sorted(path.name for path in normalized_root.iterdir() if path.is_dir()) if normalized_root.exists() else [],
        "hkm_source_present": any("hkm" in str(path).lower() or "intermediary" in str(path).lower() for path in normalized_root.rglob("*")) if normalized_root.exists() else False,
        "wgc": wgc_inventory(root),
        "ticks": tick_inventory(root),
    }


def load_close_frame(root: Path, symbol_map: dict[str, str] = CURRENT_SYMBOL_FILES) -> pd.DataFrame:
    series: dict[str, pd.Series] = {}
    for symbol, file_symbol in symbol_map.items():
        path = root / "data" / "historical_2026" / f"{file_symbol}_M15.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path, usecols=["time", "close"])
        df["time"] = pd.to_datetime(df["time"], utc=True)
        df = df.dropna(subset=["time", "close"]).drop_duplicates(subset=["time"]).set_index("time")
        series[symbol] = df["close"].astype(float).sort_index()
    if not series:
        return pd.DataFrame()
    return pd.DataFrame(series).sort_index()


def estimate_rough_vol_hurst(close: pd.Series, *, rv_window: int = 16, lags: tuple[int, ...] = (1, 2, 4, 8, 16, 32)) -> dict[str, Any]:
    close = close.dropna().astype(float)
    if len(close) < rv_window + max(lags) + 50:
        return {"n_close": int(len(close)), "n_log_rv": 0, "hurst": None, "slope": None, "status": "insufficient_rows"}
    logp = np.log(close.to_numpy())
    returns = np.diff(logp)
    rv = pd.Series(returns * returns).rolling(rv_window).sum().dropna()
    log_rv = np.log(rv.to_numpy() + 1e-16)
    xs: list[float] = []
    ys: list[float] = []
    for lag in lags:
        if len(log_rv) <= lag + 20:
            continue
        diffs = log_rv[lag:] - log_rv[:-lag]
        moment = float(np.mean(diffs * diffs))
        if moment > 0 and math.isfinite(moment):
            xs.append(math.log(float(lag)))
            ys.append(math.log(moment))
    if len(xs) < 3:
        return {"n_close": int(len(close)), "n_log_rv": int(len(log_rv)), "hurst": None, "slope": None, "status": "insufficient_lags"}
    slope, intercept = np.polyfit(np.array(xs), np.array(ys), 1)
    hurst = float(slope / 2.0)
    return {
        "n_close": int(len(close)),
        "n_log_rv": int(len(log_rv)),
        "hurst": hurst,
        "slope": float(slope),
        "intercept": float(intercept),
        "status": "ok",
    }


def rough_hurst_inventory(root: Path) -> dict[str, Any]:
    closes = load_close_frame(root)
    by_symbol = {
        symbol: estimate_rough_vol_hurst(closes[symbol])
        for symbol in closes.columns
    }
    ok = [row["hurst"] for row in by_symbol.values() if row.get("hurst") is not None]
    return {
        "symbols_requested": sorted(CURRENT_SYMBOL_FILES),
        "symbols_found": sorted(closes.columns),
        "symbol_count": len(closes.columns),
        "rows_aligned_all_symbols": int(closes.dropna().shape[0]) if not closes.empty else 0,
        "by_symbol": by_symbol,
        "median_hurst": float(np.median(ok)) if ok else None,
        "min_hurst": float(np.min(ok)) if ok else None,
        "max_hurst": float(np.max(ok)) if ok else None,
    }


def tail_correlation_inventory(root: Path) -> dict[str, Any]:
    closes = load_close_frame(root)
    returns = np.log(closes).diff().dropna(how="any")
    if returns.shape[1] < 3 or len(returns) < 100:
        return {"status": "insufficient_returns", "n_returns": int(len(returns)), "pairs": 0}
    corr = returns.corr()
    pairs: list[dict[str, Any]] = []
    for i, a in enumerate(returns.columns):
        for b in returns.columns[i + 1 :]:
            x = returns[a]
            y = returns[b]
            qx_lo = x.quantile(0.05)
            qy_lo = y.quantile(0.05)
            qx_hi = x.quantile(0.95)
            qy_hi = y.quantile(0.95)
            lower = float(((x <= qx_lo) & (y <= qy_lo)).sum() / max((x <= qx_lo).sum(), 1))
            upper = float(((x >= qx_hi) & (y >= qy_hi)).sum() / max((x >= qx_hi).sum(), 1))
            pair_return = (x + y) / 2.0
            high_mask = pair_return.abs() >= pair_return.abs().quantile(0.90)
            normal_mask = ~high_mask
            raw_high = float(x[high_mask].corr(y[high_mask])) if high_mask.sum() > 5 else None
            raw_normal = float(x[normal_mask].corr(y[normal_mask])) if normal_mask.sum() > 5 else None
            var_high = float(pair_return[high_mask].var()) if high_mask.sum() > 5 else None
            var_normal = float(pair_return[normal_mask].var()) if normal_mask.sum() > 5 else None
            fr_adjusted = None
            if raw_high is not None and var_high is not None and var_normal and var_normal > 0:
                delta = max(var_high / var_normal - 1.0, 0.0)
                fr_adjusted = float(raw_high / math.sqrt(1.0 + delta * (1.0 - raw_high * raw_high)))
            pairs.append(
                {
                    "pair": f"{a}-{b}",
                    "pearson": float(corr.loc[a, b]),
                    "lower_tail_lambda_proxy": lower,
                    "upper_tail_lambda_proxy": upper,
                    "high_vol_raw_corr": raw_high,
                    "normal_raw_corr": raw_normal,
                    "forbes_rigobon_adjusted_high_corr": fr_adjusted,
                }
            )
    top_abs = sorted(pairs, key=lambda row: abs(row["pearson"]), reverse=True)[:5]
    top_tail = sorted(pairs, key=lambda row: max(row["lower_tail_lambda_proxy"], row["upper_tail_lambda_proxy"]), reverse=True)[:5]
    return {
        "status": "ok",
        "n_returns": int(len(returns)),
        "pairs": len(pairs),
        "top_abs_pearson": top_abs,
        "top_tail_proxy": top_tail,
    }


def ai_tooling_inventory(root: Path) -> dict[str, Any]:
    orchestrator_path = root / "src" / "components" / "orchestrator.py"
    primary_path = root / "src" / "components" / "primary_analyzer.py"
    orchestrator = orchestrator_path.read_text(encoding="utf-8", errors="ignore") if orchestrator_path.exists() else ""
    primary = primary_path.read_text(encoding="utf-8", errors="ignore") if primary_path.exists() else ""
    ai_tools = root / "src" / "components" / "ai_tools"
    return {
        "ai_tools_dir_exists": ai_tools.exists(),
        "ai_tool_files": sorted(path.name for path in ai_tools.glob("*.py")) if ai_tools.exists() else [],
        "tool_use_design_exists": (root / "research" / "tool_use_grounding" / "DESIGN.md").exists(),
        "primary_imports_ai_tools": "ai_tools" in primary,
        "orchestrator_imports_debate": "debate" in orchestrator.lower(),
        "debate_code_exists": (root / "src" / "components" / "debate.py").exists(),
        "debate_tests_exist": (root / "tests" / "test_debate.py").exists(),
    }


def evidence_inventory(root: Path) -> dict[str, Any]:
    return {
        "position_management": hpm_inventory(root),
        "sources": source_inventory(root),
        "rough_hurst": rough_hurst_inventory(root),
        "tail_correlation": tail_correlation_inventory(root),
        "ai_tooling": ai_tooling_inventory(root),
        "canonical_v1_report_exists": (root / "research" / "ml_program" / "audit" / "canonical_v1_rerun.md").exists(),
    }


def classifications(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    hpm = evidence["position_management"]
    sources = evidence["sources"]
    hurst = evidence["rough_hurst"]
    tail = evidence["tail_correlation"]
    ai = evidence["ai_tooling"]
    hpm_fail = f"H-PM01 portfolio delta mean R={hpm['hpm01_delta_mean_r']}, delta Sharpe={hpm['hpm01_delta_sharpe_pct']}%, DSR-p={hpm['hpm01_dsr_p']}"
    nas_shadow = f"NAS100-only remains shadow/deferred: delta R={hpm['hpm01_nas100_delta_r']}, DSR-p={hpm['hpm01_nas100_dsr_p']}"
    x5_status = "DONE" if hurst["symbol_count"] >= 7 and hurst["median_hurst"] is not None else "BLOCKED_WITH_REASON"
    a17_status = "DONE" if tail.get("status") == "ok" else "BLOCKED_WITH_REASON"
    return [
        {
            "id": "V-4",
            "status": "DONE",
            "blocked_by": "",
            "reconciliation_note": "Sigma multiplier mapping exists in H-PM01: bsc_sigma_mult = clip(median_vol / realized_vol_30d, 0.5, 2.0).",
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_sizing_function_done",
        },
        {
            "id": "V-5",
            "status": "REJECTED_FAILED",
            "blocked_by": "",
            "reconciliation_note": f"Barroso-Santa-Clara vol-managed backtest failed portfolio-wide. {hpm_fail}.",
            "candidate_strength_vs_j46_j49": "rejected_portfolio_wide_vol_managed_backtest",
        },
        {
            "id": "V-6",
            "status": "REJECTED_FAILED",
            "blocked_by": "",
            "reconciliation_note": f"Vol-managed sizing vs uniform 2% A/B is H-PM01 and failed portfolio-wide. {hpm_fail}.",
            "candidate_strength_vs_j46_j49": "rejected_uniform_vs_vol_managed_ab",
        },
        {
            "id": "V-7",
            "status": "DONE",
            "blocked_by": "",
            "reconciliation_note": f"Daniel-Moskowitz-style LONG/side-aware sizing is closed by H-PM03/combined MC: H2 P(pass)={hpm['hpm03_side_aware_h2_p_pass']}, full P(bust HARD)={hpm['hpm03_side_aware_full_p_bust_hard']}.",
            "candidate_strength_vs_j46_j49": "risk_modifier_already_live_not_new_signal",
        },
        {
            "id": "V-8",
            "status": "REJECTED_FAILED",
            "blocked_by": "",
            "reconciliation_note": f"Moreira-Muir/Barroso broad vol-scaling integration fails as an all-symbol policy. {hpm_fail}; {nas_shadow}.",
            "candidate_strength_vs_j46_j49": "rejected_broad_vol_scaling_policy",
        },
        {
            "id": "V-9",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Component 3C bundle depends on V-2 source completion and broad V-5/V-6 success; portfolio-wide vol sizing failed and live insertion requires approval.",
            "reconciliation_note": f"Keep only NAS100-only shadow/approval route open. {nas_shadow}.",
            "candidate_strength_vs_j46_j49": "deferred_component_3c_bundle_not_validated",
        },
        {
            "id": "X-1",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "Volume-bar E24/E26 retest needs real trade volume or approved tick/depth feed; MT5 retail tick volume is not a volume-bar substrate.",
            "reconciliation_note": f"Current tick cache has {sources['ticks']['files']} parquet files and remains quote/retail-substrate limited.",
            "candidate_strength_vs_j46_j49": "blocked_missing_real_volume_bars",
        },
        {
            "id": "X-2",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "Dollar-bar E24/E26 retest needs price x real traded volume; current MT5 feed lacks true centralized trade volume.",
            "reconciliation_note": "Use only after approved futures/venue trade-volume feed exists.",
            "candidate_strength_vs_j46_j49": "blocked_missing_dollar_bar_substrate",
        },
        {
            "id": "X-3",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "Imbalance-bar E24/E26 retest needs signed trades or aggressor-side proxy; current local data is OHLCV/quote-tick only.",
            "reconciliation_note": "Do not substitute candle direction for signed trade imbalance.",
            "candidate_strength_vs_j46_j49": "blocked_missing_imbalance_bar_substrate",
        },
        {
            "id": "X-5",
            "status": x5_status,
            "blocked_by": "" if x5_status == "DONE" else "Seven-symbol M15 history was not available for rough-Hurst estimation.",
            "reconciliation_note": f"Rough-vol proxy H estimated on {hurst['symbol_count']} symbols; median H={hurst['median_hurst']}, range=[{hurst['min_hurst']}, {hurst['max_hurst']}]. Diagnostic only.",
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_rough_vol_diagnostic",
        },
        {
            "id": "X-6",
            "status": "DONE",
            "blocked_by": "",
            "reconciliation_note": "K54 v1 0.571 was reconciled by the canonical v1 rerun and K1 follow-ups: promotion anchor is CPCV-honest 0.5286, not the DSR-failing published 0.571.",
            "candidate_strength_vs_j46_j49": "not_applicable_baseline_reconciliation",
        },
        {
            "id": "A-10",
            "status": "DONE",
            "blocked_by": "",
            "reconciliation_note": f"WGC data plumbing exists: latest demand rows={sources['wgc']['demand']['rows']}, central-bank-like rows={sources['wgc']['central_bank_like_rows']}. Alpha validation remains separate.",
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_feed_feasibility_only",
        },
        {
            "id": "A-15",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "No He-Kelly-Manela/intermediary-capital source, status file, normalized cache, or source spec exists locally.",
            "reconciliation_note": "Same blocker as D-7; FRED/WGC/CFTC feeds do not supply H-K-M intermediary-capital SDF.",
            "candidate_strength_vs_j46_j49": "blocked_missing_hkm_source",
        },
        {
            "id": "A-17",
            "status": a17_status,
            "blocked_by": "" if a17_status == "DONE" else "Seven-symbol aligned return history was insufficient for tail-dependence diagnostics.",
            "reconciliation_note": f"Copula/tail-dependence diagnostic ran on {tail.get('n_returns')} aligned M15 returns and {tail.get('pairs')} pairs; feature feasibility only, no live risk rule.",
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_tail_diagnostic",
        },
        {
            "id": "A-18",
            "status": a17_status,
            "blocked_by": "" if a17_status == "DONE" else "Seven-symbol aligned return history was insufficient for Forbes-Rigobon diagnostics.",
            "reconciliation_note": "Forbes-Rigobon adjusted high-vol correlations are included in the tail-correlation diagnostic; feature feasibility only.",
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_correlation_diagnostic",
        },
        {
            "id": "B-5",
            "status": "FILED_FOR_APPROVAL",
            "blocked_by": "AI-grounding bundle depends on L-1/L-2/L-4/L-8 and would alter Component 3A/3B behavior if wired live.",
            "reconciliation_note": "Tool scaffolding and debate code exist, but live AI behavior changes need explicit CEO approval and a shadow-only design refresh.",
            "candidate_strength_vs_j46_j49": "filed_ai_behavior_bundle_approval",
        },
        {
            "id": "R-3",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Strub EVT-CDaR sizing needs preregistered simulation over DSR-surviving baselines and CEO approval before risk behavior changes.",
            "reconciliation_note": "Keep as future risk-policy replacement branch, not an unblocked live implementation.",
            "candidate_strength_vs_j46_j49": "deferred_risk_policy_replacement",
        },
        {
            "id": "R-4",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Smooth Grossman-Zhou drawdown control needs simulation and owner approval; current H29 drawdown reducer remains the live safety path.",
            "reconciliation_note": "Do not alter live drawdown behavior from current evidence.",
            "candidate_strength_vs_j46_j49": "deferred_drawdown_policy_replacement",
        },
        {
            "id": "X-4",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Tick-level Hawkes fitting needs mature tick/depth/order-flow history; current tick capture is short and quote-only.",
            "reconciliation_note": f"Current tick cache inventory: {sources['ticks']['symbols']}. Trigger: >=30 trading days all-symbol ticks or approved signed order-flow/depth feed.",
            "candidate_strength_vs_j46_j49": "deferred_tick_substrate_maturity",
        },
        {
            "id": "X-7",
            "status": "FILED_FOR_APPROVAL",
            "blocked_by": "Cascade-prompt rebuild would touch prompts/trading evaluation behavior; V4/cascade remains shelved/lost and requires explicit CEO approval before rebuild.",
            "reconciliation_note": "Recovered template exists, but no prompt rebuild is an unblocked research-loop change.",
            "candidate_strength_vs_j46_j49": "filed_prompt_behavior_approval",
        },
        {
            "id": "L-1",
            "status": "FILED_FOR_APPROVAL",
            "blocked_by": "QuantMCP-style grounding would alter Component 3A behavior if wired live; approval and shadow-only design refresh are required.",
            "reconciliation_note": f"ai_tools scaffolding exists={ai['ai_tools_dir_exists']}, design exists={ai['tool_use_design_exists']}, primary imports ai_tools={ai['primary_imports_ai_tools']}.",
            "candidate_strength_vs_j46_j49": "filed_tool_use_grounding_approval",
        },
        {
            "id": "L-2",
            "status": "FILED_FOR_APPROVAL",
            "blocked_by": "FinAgent-style market-state tool inventory would alter Component 3A behavior if wired live; approval and shadow-only design refresh are required.",
            "reconciliation_note": f"Current ai_tools files: {ai['ai_tool_files']}.",
            "candidate_strength_vs_j46_j49": "filed_tool_inventory_approval",
        },
        {
            "id": "L-4",
            "status": "FILED_FOR_APPROVAL",
            "blocked_by": "Component 3B debate activation would alter AI evaluation flow and token spend; CEO DELETE/WIRE/LEAVE decision remains required.",
            "reconciliation_note": f"Debate code exists={ai['debate_code_exists']}, tests exist={ai['debate_tests_exist']}, orchestrator imports debate={ai['orchestrator_imports_debate']}.",
            "candidate_strength_vs_j46_j49": "filed_component3b_approval",
        },
        {
            "id": "L-8",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "LLM transfer test depends on L-1/L-2 shadow grounding implementation and approval path.",
            "reconciliation_note": "No Sonnet-class transfer test can be run before the grounding intervention exists in a shadow harness.",
            "candidate_strength_vs_j46_j49": "deferred_depends_on_grounding_shadow",
        },
        {
            "id": "RR-1",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Quarterly last-6-months literature refresh across 22 domains requires a dedicated current-web literature sweep and source-citation pass outside this local evidence triage.",
            "reconciliation_note": "Existing local literature corpus remains usable, but RR-1 specifically asks for current last-6-month paper discovery.",
            "candidate_strength_vs_j46_j49": "deferred_dedicated_literature_refresh",
        },
    ]


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(out)


def render_markdown(payload: dict[str, Any]) -> str:
    evidence = payload["evidence"]
    class_rows = [
        [item["id"], item["status"], item["blocked_by"] or "-", item["reconciliation_note"]]
        for item in payload["classifications"]
    ]
    hurst_rows = [
        [symbol, row.get("n_close"), row.get("n_log_rv"), row.get("hurst"), row.get("status")]
        for symbol, row in evidence["rough_hurst"]["by_symbol"].items()
    ]
    tail_rows = [
        [row["pair"], row["pearson"], row["lower_tail_lambda_proxy"], row["upper_tail_lambda_proxy"], row["forbes_rigobon_adjusted_high_corr"]]
        for row in evidence["tail_correlation"].get("top_abs_pearson", [])
    ]
    return "\n".join(
        [
            "# Lane 6 Tail Triage",
            "",
            f"Generated: {payload['generated_at_utc']}",
            "Scope: research/tooling only",
            "Promotion verdict: `NO_PROMOTION_VERDICT`",
            "",
            "## Question Registered Before Output",
            "",
            payload["hypothesis_before_outputs"],
            "",
            "## Evidence Inventory",
            "",
            f"- H-PM01 portfolio delta mean R: `{evidence['position_management']['hpm01_delta_mean_r']}`, DSR-p: `{evidence['position_management']['hpm01_dsr_p']}`.",
            f"- H-PM01 NAS100-only delta R: `{evidence['position_management']['hpm01_nas100_delta_r']}`, DSR-p: `{evidence['position_management']['hpm01_nas100_dsr_p']}`.",
            f"- WGC demand rows: `{evidence['sources']['wgc']['demand']['rows']}`; central-bank-like rows: `{evidence['sources']['wgc']['central_bank_like_rows']}`.",
            f"- Tick parquet inventory: `{evidence['sources']['ticks']}`.",
            f"- Rough-Hurst symbols found: `{evidence['rough_hurst']['symbols_found']}`; median H: `{evidence['rough_hurst']['median_hurst']}`.",
            f"- Tail-correlation diagnostic status: `{evidence['tail_correlation'].get('status')}`, pairs: `{evidence['tail_correlation'].get('pairs')}`.",
            f"- AI tooling scaffold: `{evidence['ai_tooling']}`.",
            "",
            "## Rough-Vol Hurst Proxy",
            "",
            markdown_table(["symbol", "n_close", "n_log_rv", "H", "status"], hurst_rows),
            "",
            "## Tail / Correlation Diagnostic",
            "",
            markdown_table(["pair", "pearson", "lower_tail_proxy", "upper_tail_proxy", "FR_adjusted_high_corr"], tail_rows),
            "",
            "## Classification Matrix",
            "",
            markdown_table(["ID", "Status", "Blocked By", "Evidence / Note"], class_rows),
            "",
            "## NO_PROMOTION_VERDICT",
            "",
            "This triage does not validate or promote a trading rule, live filter, risk setting, prompt, or execution change. It only classifies the next unblocked queue batch from local evidence and approval/source blockers.",
            "",
        ]
    )


def build_payload(root: str | Path = ".") -> dict[str, Any]:
    repo = Path(root)
    evidence = evidence_inventory(repo)
    items = classifications(evidence)
    return {
        "schema_version": "lane6_tail_triage_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "hypothesis_before_outputs": (
            "The remaining Lane 6 tail batch should mostly resolve from existing H-PM/NA8/WGC/K54 evidence: "
            "broad vol-managed sizing should fail, side-aware and baseline-reconciliation items should close, "
            "bar-sampling/Hawkes tasks should be data-substrate blocked or deferred, and AI behavior changes should be approval-filed."
        ),
        "evidence": evidence,
        "classifications": items,
        "status_counts": dict(sorted(Counter(item["status"] for item in items).items())),
    }


def write_outputs(payload: dict[str, Any], output_json: str | Path, output_md: str | Path) -> None:
    json_path = Path(output_json)
    md_path = Path(output_md)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args()
    payload = build_payload()
    write_outputs(payload, args.output_json, args.output_md)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(f"status_counts={payload['status_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

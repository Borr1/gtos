#!/usr/bin/env python3
"""Triage first Lane 6 asset/risk/volatility/edge backlog cluster.

Research/tooling only. This reconciles V-1..V-3, A-8, C-2,
E-1, E-2, and E-4 against existing local feature catalogs, Phase 2
position-management evidence, source inventories, and K54 v3 results.
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


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_JSON = "research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.json"
DEFAULT_OUTPUT_MD = "research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        return sum(1 for _ in fh)


def _latest_jsonl_for_series(root: Path, series: str) -> Path | None:
    files = sorted((root / "data" / "external" / "normalized" / "fred").glob(f"{series}_observations_*.jsonl"))
    return files[-1] if files else None


def external_feed_evidence(root: Path) -> dict[str, Any]:
    fred_dir = root / "data" / "external" / "normalized" / "fred"
    fred_series = sorted(
        {
            path.name.split("_observations_")[0]
            for path in fred_dir.glob("*_observations_*.jsonl")
            if "_observations_" in path.name
        }
    )
    required_real_gold_terms = ("CPIAUCSL", "PCEPI", "CPILFESL")
    vix_terms = ("VIXCLS", "GVZCLS", "VIX1D", "VIX9D", "VVIX", "VRP")
    wgc_dir = root / "data" / "external" / "normalized" / "wgc"
    xau_d1 = root / "data" / "historical_2026" / "XAUUSD_D1.csv"
    xau_range = {"rows": 0, "first": None, "last": None}
    if xau_d1.exists():
        with xau_d1.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            rows = list(csv.DictReader(fh))
        if rows:
            xau_range = {
                "rows": len(rows),
                "first": rows[0].get("time"),
                "last": rows[-1].get("time"),
            }
    return {
        "fred_series": fred_series,
        "fred_series_count": len(fred_series),
        "has_real_gold_deflator": any(series in fred_series for series in required_real_gold_terms),
        "required_real_gold_terms": list(required_real_gold_terms),
        "vol_terms_present": {series: series in fred_series for series in vix_terms},
        "wgc_files": sorted(path.name for path in wgc_dir.glob("*.jsonl")),
        "xauusd_d1": xau_range,
    }


def vol_feature_evidence(root: Path) -> dict[str, Any]:
    hpm01 = _read_json(root / "research" / "ml_program" / "phase_2" / "position_mgmt" / "h_pm01_per_cohort_results.json")
    hpm01_md = _read_text(
        root / "research" / "ml_program" / "phase_2" / "position_mgmt" / "h_pm01_vol_conditional_sizing.md"
    )
    hpm03_code = _read_text(root / "research" / "ml_program" / "phase_2" / "position_mgmt" / "_compute_h_pm03.py")
    na8_code = _read_text(root / "scripts" / "research" / "na8_babu_decomposition.py")
    vol_catalog = _read_text(root / "research" / "ml_program" / "feature_catalogs" / "volatility.md")
    primary = hpm01.get("primary_full_cohort", {})
    gate = ((primary.get("backtest") or {}).get("delta") or {})
    dsr = (primary.get("dsr_paired_delta") or {})
    metadata = hpm01.get("metadata") or {}
    return {
        "hpm01_cohort_size": metadata.get("cohort_size"),
        "hpm01_delta_mean_r": gate.get("mean_r"),
        "hpm01_dsr_p": dsr.get("dsr_p"),
        "hpm01_has_realized_vol_rank": "realized_vol_rank" in hpm01_md,
        "hpm03_has_vol_rank": "vol_rank" in hpm03_code,
        "na8_has_realized_vol_rank": "realized_vol_rank" in na8_code,
        "vol_catalog_has_realized_vol_family": "Realized vol + transitions" in vol_catalog,
        "vol_catalog_realized_vol_rows": vol_catalog.count("realized_vol_"),
        "vol_catalog_pct_rows": vol_catalog.count("_pct_w"),
    }


def regime_feature_evidence(root: Path) -> dict[str, Any]:
    regime_catalog = _read_text(root / "research" / "ml_program" / "feature_catalogs" / "regime.md")
    regime_code = _read_text(root / "research" / "ml_program" / "scripts" / "features" / "regime.py")
    shadow_log = root / "shadow_logs" / "regime_classifications.jsonl"
    feature_names = (
        "regime_consecutive_h4_bars",
        "regime_h4_bars_since_last_flip",
        "regime_changed_in_last_1",
        "regime_changed_in_last_5",
        "regime_changed_in_last_10",
        "regime_changed_in_last_20",
        "regime_changed_in_last_50",
        "regime_v2_score_change_1",
        "regime_v2_score_change_5",
        "regime_v2_score_change_20",
    )
    return {
        "feature_names_present": {
            name: name in regime_catalog or name in regime_code for name in feature_names
        },
        "feature_count_present": sum(1 for name in feature_names if name in regime_catalog or name in regime_code),
        "shadow_log_exists": shadow_log.exists(),
        "shadow_log_rows": _line_count(shadow_log),
    }


def k54_osler_evidence(root: Path) -> dict[str, Any]:
    k54 = _read_json(root / "research" / "ml_program" / "audit" / "LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.json")
    train_code = _read_text(root / "research" / "ml_program" / "models" / "k54_v3" / "train_k54_v3.py")
    top_features = _read_text(root / "research" / "ml_program" / "models" / "k54_v3" / "top_features.json")
    w_unit = (((k54.get("evidence") or {}).get("k54_v3") or {}).get("w_unit_ablation") or {})
    return {
        "k7_proxy_in_train_code": "kw__k7_osler_stopcluster_proxy" in train_code,
        "k7_proxy_in_top_features": "kw__k7_osler_stopcluster_proxy" in top_features,
        "v3_features_minus_arch_a_auc": w_unit.get("v3_features_minus_arch_a_auc"),
        "w_unit_on_minus_off_auc": w_unit.get("on_minus_off_auc"),
        "arch_a_auc": w_unit.get("arch_a_auc"),
        "v3_feature_cols_count": (w_unit.get("feature_cols_count") or {}).get("v3"),
    }


def data_source_evidence(root: Path) -> dict[str, Any]:
    lane5 = _read_json(root / "research" / "ml_program" / "audit" / "LANE5_DATA_SOURCE_TRIAGE_2026-05-03.json")
    ticks = ((lane5.get("inventories") or {}).get("ticks") or {})
    orderflow_scripts = (
        "scripts/analyze_orderflow_depth_mbp1_features.py",
        "scripts/analyze_orderflow_depth_mbp10_features.py",
        "scripts/analyze_orderflow_mbo_nas100_features.py",
    )
    return {
        "tick_max_symbol_days": ticks.get("max_symbol_days"),
        "tick_symbols_with_ticks": ticks.get("symbols_with_ticks"),
        "tick_features_helper_exists": ticks.get("tick_features_helper_exists"),
        "orderflow_depth_scripts_exist": {
            path: (root / path).exists() for path in orderflow_scripts
        },
        "has_xau_fx_lob_cache": any(
            part.lower() in path.as_posix().lower()
            for path in (root / "data").glob("**/*")
            for part in ("xau_lob", "gbpusd_lob", "usdjpy_lob", "gbpjpy_lob")
        ),
    }


def retail_flow_evidence(root: Path) -> dict[str, Any]:
    crowding = _read_text(root / "research" / "academic_pipeline" / "results" / "Q-crowding_retail.md")
    external_root = root / "data" / "external"
    retail_like_files = [
        path.relative_to(root).as_posix()
        for path in external_root.glob("**/*")
        if any(term in path.name.lower() for term in ("oanda", "ig_", "client_sentiment", "retail"))
    ]
    return {
        "q_crowding_says_ig_oanda_missing": "IG / OANDA client-sentiment | MISSING" in crowding,
        "q_crowding_says_cot_missing": "CFTC COT speculator positioning | MISSING" in crowding,
        "local_retail_like_files": retail_like_files,
    }


def _float_or_none(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def _round_unit(symbol: str) -> float:
    if symbol in {"XAUUSD", "USDJPY", "GBPJPY"}:
        return 1.0
    return 0.01


def _near_round(value: float, unit: float) -> bool:
    rem = abs(value) % unit
    dist = min(rem, unit - rem)
    return dist <= unit * 0.01


def production_trade_level_evidence(root: Path) -> dict[str, Any]:
    base = root / "knowledge_base" / "trade_records"
    symbols = {"XAUUSD", "GBPUSD", "USDJPY", "GBPJPY"}
    records = 0
    with_params = 0
    execution_null = 0
    tp_round_hits = 0
    sl_round_hits = 0
    by_symbol: Counter[str] = Counter()
    for path in base.rglob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue
        symbol = ((payload.get("metadata") or {}).get("symbol") or path.parent.name).strip()
        if symbol not in symbols:
            continue
        records += 1
        by_symbol[symbol] += 1
        if payload.get("execution") is None:
            execution_null += 1
        params = payload.get("trade_parameters") or {}
        if not params:
            response = payload.get("ai_response") or payload.get("analysis") or {}
            params = response.get("trade_parameters") or {}
        stop_loss = _float_or_none(params.get("stop_loss"))
        take_profit_1 = _float_or_none(params.get("take_profit_1"))
        if stop_loss is None or take_profit_1 is None:
            continue
        with_params += 1
        unit = _round_unit(symbol)
        if _near_round(take_profit_1, unit):
            tp_round_hits += 1
        if _near_round(stop_loss, unit):
            sl_round_hits += 1
    return {
        "symbols_scanned": sorted(symbols),
        "records_scanned": records,
        "records_with_trade_parameters": with_params,
        "execution_null_records": execution_null,
        "by_symbol": dict(sorted(by_symbol.items())),
        "tp_round_hit_rate": (tp_round_hits / with_params) if with_params else None,
        "sl_round_near_rate": (sl_round_hits / with_params) if with_params else None,
        "note": "These are GTOS proposed/recorded levels, not counterparty stop-placement observations.",
    }


def build_evidence(root: str | Path = REPO_ROOT) -> dict[str, Any]:
    root_path = Path(root)
    return {
        "external_feeds": external_feed_evidence(root_path),
        "vol_features": vol_feature_evidence(root_path),
        "regime_features": regime_feature_evidence(root_path),
        "k54_osler": k54_osler_evidence(root_path),
        "data_sources": data_source_evidence(root_path),
        "retail_flow": retail_flow_evidence(root_path),
        "production_trade_levels": production_trade_level_evidence(root_path),
    }


def classify_tasks(evidence: dict[str, Any]) -> dict[str, dict[str, Any]]:
    artifact = DEFAULT_OUTPUT_MD
    feeds = evidence["external_feeds"]
    vol = evidence["vol_features"]
    regime = evidence["regime_features"]
    osler = evidence["k54_osler"]
    data_sources = evidence["data_sources"]
    retail = evidence["retail_flow"]

    return {
        "V-1": {
            "status": "DONE",
            "backlog_item": "Realized-vol-percentile feature.",
            "blocked_by": "",
            "trigger": "No trigger; feature/tooling exists. Component 3C sizing integration remains separate V-9/P-1 work.",
            "latest_artifact_path": artifact,
            "evidence": {
                "hpm01_has_realized_vol_rank": vol["hpm01_has_realized_vol_rank"],
                "hpm03_has_vol_rank": vol["hpm03_has_vol_rank"],
                "na8_has_realized_vol_rank": vol["na8_has_realized_vol_rank"],
                "hpm01_delta_mean_r": vol["hpm01_delta_mean_r"],
                "hpm01_dsr_p": vol["hpm01_dsr_p"],
            },
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_feature_done; portfolio-wide H-PM01 failed",
        },
        "V-2": {
            "status": "BLOCKED_WITH_REASON",
            "backlog_item": "Variance Risk Premium (VRP) feature.",
            "blocked_by": "No local VRP, VIX futures, implied-variance term-structure, or registered realized-vol estimator source exists; VIXCLS/GVZCLS alone do not define VRP.",
            "trigger": "Create a no-leak VRP construction spec with as-of implied-vol/variance source and realized-vol estimator, then build the point-in-time cache.",
            "latest_artifact_path": artifact,
            "evidence": {
                "vol_terms_present": feeds["vol_terms_present"],
            },
            "candidate_strength_vs_j46_j49": "not_applicable_feature_feasibility",
        },
        "V-3": {
            "status": "DONE",
            "backlog_item": "Regime-persistence feature.",
            "blocked_by": "",
            "trigger": "No trigger; K54 regime feature family already contains run-length, flip-window, and score-dynamics persistence features.",
            "latest_artifact_path": artifact,
            "evidence": {
                "feature_count_present": regime["feature_count_present"],
                "shadow_log_rows": regime["shadow_log_rows"],
            },
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_feature_done",
        },
        "A-8": {
            "status": "BLOCKED_WITH_REASON",
            "backlog_item": "Erb-Harvey 2024 real-gold-price percentile feature.",
            "blocked_by": "Local feeds have XAUUSD nominal bars plus FRED real-rate/inflation-expectation proxies, but no CPI/PCE deflator or pre-registered real-gold-price percentile construction.",
            "trigger": "Add a legal CPI/PCE deflator source with publication-time metadata and register the real-gold-price percentile lookback before feature construction.",
            "latest_artifact_path": artifact,
            "evidence": {
                "fred_series": feeds["fred_series"],
                "has_real_gold_deflator": feeds["has_real_gold_deflator"],
                "xauusd_d1": feeds["xauusd_d1"],
            },
            "candidate_strength_vs_j46_j49": "not_applicable_feature_feasibility",
        },
        "C-2": {
            "status": "BLOCKED_WITH_REASON",
            "backlog_item": "Disposition-effect feature on counterparty stop placements.",
            "blocked_by": "GTOS does not observe counterparty stop placements, broker client positioning, or IG/OANDA-style client-sentiment locally; production trade records contain our proposed levels only.",
            "trigger": "Register a legal counterparty/retail-positioning proxy or order-book stop-density source before building disposition-effect features.",
            "latest_artifact_path": artifact,
            "evidence": {
                "q_crowding_says_ig_oanda_missing": retail["q_crowding_says_ig_oanda_missing"],
                "local_retail_like_files": retail["local_retail_like_files"],
            },
            "candidate_strength_vs_j46_j49": "not_applicable_unobserved_counterparty_data",
        },
        "E-1": {
            "status": "REJECTED_FAILED",
            "backlog_item": "Osler stop-cluster prediction on GTOS XAU+FX data.",
            "blocked_by": "The K54 v3 Osler round-level stop-cluster proxy was implemented as K-7 and contributed only below-noise lift; production trade history records proposed GTOS levels, not counterparty stop clusters.",
            "trigger": "Reopen only with direct stop-cluster/counterparty data or a feature-specific preregistered cohort that clears the methodology gate.",
            "latest_artifact_path": artifact,
            "evidence": {
                "k7_proxy_in_train_code": osler["k7_proxy_in_train_code"],
                "k7_proxy_in_top_features": osler["k7_proxy_in_top_features"],
                "v3_features_minus_arch_a_auc": osler["v3_features_minus_arch_a_auc"],
                "production_trade_levels": evidence["production_trade_levels"],
            },
            "candidate_strength_vs_j46_j49": "rejected_below_noise_proxy",
        },
        "E-2": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "Toth-Bouchaud V-shaped latent liquidity test on tick data where coverage exists.",
            "blocked_by": "Current all-symbol MT5 tick coverage is short and quote-only; the Toth-Bouchaud latent-liquidity shape needs mature tick/depth/order-flow evidence, not just recent bid/ask quote ticks.",
            "trigger": "Reopen after >=30 trading days all-symbol ticks or an approved depth/order-flow feed, with a preregistered V-shape estimator.",
            "latest_artifact_path": artifact,
            "evidence": {
                "tick_max_symbol_days": data_sources["tick_max_symbol_days"],
                "tick_symbols_with_ticks": data_sources["tick_symbols_with_ticks"],
                "has_xau_fx_lob_cache": data_sources["has_xau_fx_lob_cache"],
            },
            "candidate_strength_vs_j46_j49": "deferred_substrate_maturity",
        },
        "E-4": {
            "status": "BLOCKED_WITH_REASON",
            "backlog_item": "F11 OB-zone decay regression vs retail-flow share over time.",
            "blocked_by": "F11/OB-decay artifacts exist, but no retail-flow-share proxy, broker client-sentiment cache, Google Trends cache, or social-flow dataset is available locally.",
            "trigger": "Add a legal retail-flow-share proxy with time coverage aligned to F11 windows, then preregister the decay regression.",
            "latest_artifact_path": artifact,
            "evidence": {
                "q_crowding_says_ig_oanda_missing": retail["q_crowding_says_ig_oanda_missing"],
                "q_crowding_says_cot_missing": retail["q_crowding_says_cot_missing"],
            },
            "candidate_strength_vs_j46_j49": "not_applicable_missing_retail_flow_proxy",
        },
    }


def build_payload(root: str | Path = REPO_ROOT) -> dict[str, Any]:
    root_path = Path(root)
    evidence = build_evidence(root_path)
    payload = {
        "schema_version": "lane6_asset_risk_edge_triage_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "scope": "research/tooling only",
        "question": "Classify first Lane 6 asset/risk/volatility/edge items from local evidence.",
        "source_files": [
            "research/ml_program/MASTER_BACKLOG.md",
            "research/ml_program/phase_2/position_mgmt/h_pm01_vol_conditional_sizing.md",
            "research/ml_program/phase_2/position_mgmt/h_pm01_per_cohort_results.json",
            "research/ml_program/phase_2/position_mgmt/_compute_h_pm03.py",
            "research/ml_program/feature_catalogs/volatility.md",
            "research/ml_program/feature_catalogs/regime.md",
            "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md",
            "research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md",
            "research/academic_pipeline/results/Q-crowding_retail.md",
            "data/external/normalized/",
            "knowledge_base/trade_records/",
            ".context/05_operations/WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md",
        ],
        "evidence": evidence,
    }
    payload["task_classifications"] = classify_tasks(evidence)
    payload["status_counts"] = dict(
        sorted(Counter(row["status"] for row in payload["task_classifications"].values()).items())
    )
    return payload


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: str | Path) -> None:
    evidence = payload["evidence"]
    vol = evidence["vol_features"]
    regime = evidence["regime_features"]
    feeds = evidence["external_feeds"]
    osler = evidence["k54_osler"]
    data_sources = evidence["data_sources"]
    trade_levels = evidence["production_trade_levels"]
    tasks = payload["task_classifications"]

    lines = [
        "# Lane 6 Asset / Risk / Edge Triage",
        "",
        "Date: 2026-05-03",
        "Scope: research/tooling only",
        "Promotion verdict: `NO_PROMOTION_VERDICT`",
        "",
        "## Question",
        "",
        payload["question"],
        "",
        "## Evidence Summary",
        "",
        f"- Realized-vol rank tooling exists in H-PM01/H-PM03/NA8: `{vol['hpm01_has_realized_vol_rank']}` / `{vol['hpm03_has_vol_rank']}` / `{vol['na8_has_realized_vol_rank']}`.",
        f"- H-PM01 portfolio-wide result failed: delta mean R `{vol['hpm01_delta_mean_r']}`, DSR-p `{vol['hpm01_dsr_p']}`.",
        f"- Regime persistence feature names present: `{regime['feature_count_present']}`; regime shadow rows `{regime['shadow_log_rows']}`.",
        f"- FRED series available: `{feeds['fred_series']}`; real-gold deflator present `{feeds['has_real_gold_deflator']}`.",
        f"- Vol terms present: `{feeds['vol_terms_present']}`.",
        f"- K54 Osler/K-7 proxy in train code `{osler['k7_proxy_in_train_code']}`; K-7..K-10 marginal AUC lift `{osler['v3_features_minus_arch_a_auc']}`.",
        f"- Tick substrate: max symbol days `{data_sources['tick_max_symbol_days']}`, symbols with ticks `{data_sources['tick_symbols_with_ticks']}`, XAU/FX LOB cache `{data_sources['has_xau_fx_lob_cache']}`.",
        f"- Production XAU+FX trade records with parameters `{trade_levels['records_with_trade_parameters']}` of `{trade_levels['records_scanned']}`; TP round-hit proxy `{trade_levels['tp_round_hit_rate']}`. These are GTOS levels, not counterparty stop observations.",
        "",
        "## Task Classifications",
        "",
        "| id | status | blocker / trigger | candidate strength |",
        "| --- | --- | --- | --- |",
    ]
    for item_id in ("V-1", "V-2", "V-3", "A-8", "C-2", "E-1", "E-2", "E-4"):
        row = tasks[item_id]
        lines.append(
            "| {id} | {status} | {blocker} Trigger: {trigger} | {strength} |".format(
                id=item_id,
                status=row["status"],
                blocker=row["blocked_by"].replace("|", r"\|") or "none",
                trigger=row["trigger"].replace("|", r"\|"),
                strength=row["candidate_strength_vs_j46_j49"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `V-1` and `V-3` are feature/tooling-complete, but this does not revive the portfolio-wide Component 3C overlay; that remains deferred under P-1/V-9.",
            "- `V-2` and `A-8` are source/construction blocked, not coding tasks.",
            "- `E-1` closes only the current Osler proxy path; it does not prove that counterparty stop clustering is false.",
            "- `C-2`, `E-2`, and `E-4` need external counterparty/retail/depth evidence before validation claims are meaningful.",
            "",
            "## Source Files",
            "",
        ]
    )
    for source in payload["source_files"]:
        lines.append(f"- `{source}`")
    lines.extend(
        [
            "",
            "## NO_PROMOTION_VERDICT",
            "",
            "This artifact classifies readiness only. It does not validate, promote, or modify live trading behavior.",
            "",
        ]
    )
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(REPO_ROOT))
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(args.root)
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        "task_statuses="
        + json.dumps({key: value["status"] for key, value in payload["task_classifications"].items()}, sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

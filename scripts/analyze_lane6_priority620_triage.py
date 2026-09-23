#!/usr/bin/env python3
"""Lane 6 priority-620 backlog triage.

Research/tooling only. This script inventories local evidence for the next
Lane 6 batch and writes a versioned report. It does not change live trading
logic, prompts, risk settings, or execution behavior.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT_JSON = "research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.json"
DEFAULT_OUTPUT_MD = "research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md"

ARTIFACT = "research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md"


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
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def latest_file(root: Path, pattern: str) -> Path | None:
    files = sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime if p.exists() else 0)
    return files[-1] if files else None


def count_jsonl_dir(root: Path, pattern: str) -> tuple[int, dict[str, int], str | None]:
    latest = latest_file(root, pattern)
    if latest is None:
        return 0, {}, None
    rows = read_jsonl(latest)
    symbols = Counter(str(row.get("gtos_symbol") or row.get("symbol") or row.get("underlying") or "unknown") for row in rows)
    return len(rows), dict(sorted(symbols.items())), str(latest)


def fred_series(root: Path) -> list[str]:
    fred_root = root / "data" / "external" / "normalized" / "fred"
    out = set()
    for path in fred_root.glob("*_observations_*.jsonl"):
        out.add(path.name.split("_observations_", 1)[0])
    return sorted(out)


def flashalpha_inventory(root: Path) -> dict[str, Any]:
    gex_root = root / "data" / "external" / "normalized" / "flashalpha_gex"
    rows = []
    for path in gex_root.glob("*_gex_*.jsonl"):
        rows.extend(read_jsonl(path))
    return {
        "files": len(list(gex_root.glob("*_gex_*.jsonl"))),
        "rows": len(rows),
        "symbols": dict(sorted(Counter(str(row.get("underlying") or row.get("symbol") or "unknown") for row in rows).items())),
    }


def cftc_inventory(root: Path) -> dict[str, Any]:
    rows, symbols, latest = count_jsonl_dir(
        root / "data" / "external" / "normalized" / "cftc_cot",
        "disagg_combined_*.jsonl",
    )
    return {"latest_file": latest, "rows": rows, "symbols": symbols}


def lbma_inventory(root: Path) -> dict[str, Any]:
    rows, symbols, latest = count_jsonl_dir(
        root / "data" / "external" / "normalized" / "lbma_calendar",
        "fix_calendar_*.jsonl",
    )
    return {"latest_file": latest, "rows": rows, "symbols": symbols}


def inverted_tp_inventory(root: Path) -> dict[str, Any]:
    rows = read_jsonl(root / "knowledge_base" / "inverted_tp_log.jsonl")
    key_counts = Counter()
    symbols = Counter()
    for row in rows:
        key_counts.update(row.keys())
        symbols[str(row.get("symbol") or "missing")] += 1
    return {"rows": len(rows), "symbols": dict(sorted(symbols.items())), "keys": dict(sorted(key_counts.items()))}


def hpm_inventory(root: Path) -> dict[str, Any]:
    hpm01 = load_json(root / "research" / "ml_program" / "phase_2" / "position_mgmt" / "h_pm01_per_cohort_results.json") or {}
    hpm03 = load_json(root / "research" / "ml_program" / "phase_2" / "position_mgmt" / "h_pm03_mc_results.json") or {}
    combined = load_json(root / "research" / "ml_program" / "phase_2" / "position_mgmt" / "combined_mc_results.json") or {}
    primary = hpm01.get("primary_full_cohort", {})
    per_inst = (hpm01.get("per_cohort", {}) or {}).get("per_instrument", {})
    hpm03_decision = hpm03.get("decision_summary", {})
    combined_decision = combined.get("decision", {})
    return {
        "hpm01_delta_mean_r": (((primary.get("backtest") or {}).get("delta") or {}).get("mean_r")),
        "hpm01_dsr_p": ((primary.get("dsr_paired_delta") or {}).get("dsr_p")),
        "hpm01_nas100_delta_r": (((per_inst.get("NAS100") or {}).get("backtest") or {}).get("delta") or {}).get("mean_r"),
        "hpm01_nas100_dsr_p": ((per_inst.get("NAS100") or {}).get("dsr_paired") or {}).get("dsr_p"),
        "hpm03_side_aware_full_p_bust_hard": ((hpm03_decision.get("full_cohort") or {}).get("p_bust_hard_max_sae")),
        "hpm03_side_aware_h2_p_pass": ((hpm03_decision.get("risk_adjusted_winner") or {}).get("winner_h2_p_pass")),
        "combined_s79_density_p_pass": ((combined_decision.get("PRIMARY_full_stack_s79_density") or {}).get("p_pass")),
        "combined_realistic_density_p_pass": ((combined_decision.get("PRIMARY_full_stack_realistic_density") or {}).get("p_pass")),
        "combined_realistic_density_p_bust_hard": ((combined_decision.get("PRIMARY_full_stack_realistic_density") or {}).get("p_bust_hard_max")),
    }


def feature_stability_inventory(root: Path) -> dict[str, Any]:
    v3 = load_json(root / "research" / "ml_program" / "models" / "k54_v3" / "feature_stability.json") or {}
    v4 = load_json(root / "research" / "ml_program" / "models" / "k54_v4" / "feature_stability.json") or {}
    master = v4.get("master", {}) if isinstance(v4, dict) else {}
    return {
        "k54_v3_mean_jaccard": v3.get("mean_pairwise_jaccard_top50"),
        "k54_v3_stable_features": v3.get("n_features_in_>=80%_paths"),
        "k54_v4_master_mean_jaccard": master.get("mean_jaccard"),
        "k54_v4_master_stable_features": master.get("n_stable_features"),
    }


def build_evidence(root: Path) -> dict[str, Any]:
    return {
        "fred_series": fred_series(root),
        "flashalpha_gex": flashalpha_inventory(root),
        "cftc_cot": cftc_inventory(root),
        "lbma_calendar": lbma_inventory(root),
        "inverted_tp": inverted_tp_inventory(root),
        "position_management": hpm_inventory(root),
        "feature_stability": feature_stability_inventory(root),
    }


def classifications(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    cftc_rows = evidence["cftc_cot"]["rows"]
    lbma_rows = evidence["lbma_calendar"]["rows"]
    flash_rows = evidence["flashalpha_gex"]["rows"]
    fred = set(evidence["fred_series"])
    hpm = evidence["position_management"]
    inv_rows = evidence["inverted_tp"]["rows"]
    stability = evidence["feature_stability"]

    return [
        {
            "id": "A-1",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Local FlashAlpha GEX proxy exists but only forward/current snapshots are cached; no legal historical gamma-sign series is available for NAS/US30 cross-period sign-flip validation.",
            "reconciliation_note": f"FlashAlpha GEX inventory has {flash_rows} local rows; treat gamma sign as forward proxy only until >=30 trading days of snapshots or legal historical CBOE/GEX data exists.",
            "candidate_strength_vs_j46_j49": "deferred_proxy_feature_not_strategy_comparable",
        },
        {
            "id": "A-4",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "A-1 is forward-only and A-2/A-3 are blocked; same-cohort K54/K55 retraining is closed until cohort/source-quality triggers.",
            "reconciliation_note": "NAS_US30 specialist retrain cannot verify gamma/VRP sign-flip cure without A-1/A-2/A-3 features and an approved retraining trigger.",
            "candidate_strength_vs_j46_j49": "blocked_specialist_retrain_inputs_absent",
        },
        {
            "id": "A-5",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "No local Japan/UK rate-differential, carry-unwind, or BIS/Aquilina source is cached for JPY-pair factor decomposition.",
            "reconciliation_note": "Local FRED/DXY/VIX partial macro cache is insufficient for Lustig-Roussanov-Verdelhan JPY carry factor decomposition.",
            "candidate_strength_vs_j46_j49": "blocked_missing_jpy_carry_sources",
        },
        {
            "id": "A-6",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "No local BoE policy, GBP political-risk, or registered legal proxy feed exists.",
            "reconciliation_note": "GBP-pair specialist feature construction is source-blocked, not an ML architecture task.",
            "candidate_strength_vs_j46_j49": "blocked_missing_gbp_policy_sources",
        },
        {
            "id": "A-7",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "FRED has partial USD macro series but no Treasury-basis/intermediary-capital source or Fed-funds feature contract is registered.",
            "reconciliation_note": f"Available FRED series are {sorted(fred)}; this is insufficient for the full dollar-specialist feature set.",
            "candidate_strength_vs_j46_j49": "blocked_partial_macro_cache_only",
        },
        {
            "id": "A-9",
            "status": "DONE",
            "blocked_by": "",
            "reconciliation_note": f"Gold COT feed feasibility is satisfied for XAUUSD: latest CFTC normalized cache has {cftc_rows} rows and fields for managed-money/commercial-style positioning. Alpha validation remains separate.",
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_feed_feasibility_only",
        },
        {
            "id": "A-11",
            "status": "DONE",
            "blocked_by": "",
            "reconciliation_note": f"LBMA fix-calendar feature feasibility is satisfied for metals: latest normalized calendar has {lbma_rows} rows. This is not an alpha validation.",
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_calendar_feature_only",
        },
        {
            "id": "A-12",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "No Krohn-Mueller-Whelan FX-fix source/cache exists locally; D-5 remains blocked for FX-fix scope.",
            "reconciliation_note": "LBMA calendar readiness does not supply the KMW top-9-currency FX-fix W-shape dataset.",
            "candidate_strength_vs_j46_j49": "blocked_missing_fx_fix_source",
        },
        {
            "id": "A-13",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "VIXCLS and Treasury yields exist, but TED/funding-liquidity/intermediary-capital source contract is incomplete.",
            "reconciliation_note": f"FRED cache includes VIXCLS={('VIXCLS' in fred)} and DGS10/DGS2={('DGS10' in fred and 'DGS2' in fred)}, but not a complete funding-liquidity factor.",
            "candidate_strength_vs_j46_j49": "blocked_incomplete_funding_liquidity_sources",
        },
        {
            "id": "A-14",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "No BIS JPY carry-unwind table/cache/source spec exists locally.",
            "reconciliation_note": "Aquilina-style JPY carry-unwind classifier is source-blocked until BIS data is registered and cached.",
            "candidate_strength_vs_j46_j49": "blocked_missing_bis_jpy_source",
        },
        {
            "id": "A-16",
            "status": "FILED_FOR_APPROVAL",
            "blocked_by": "Replacing the live cross-instrument correlation gate would alter risk behavior and needs CEO approval; research-only prototype can be scoped separately.",
            "reconciliation_note": "Static triage files DCC/cDCC/Block-DECO as an approval-gated risk-model replacement, not an unblocked live-code change.",
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_risk_model_approval",
        },
        {
            "id": "B-2",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Portfolio-wide vol conditioning failed; NAS100-only subcandidate needs shadow/approval trigger before Component 3C work.",
            "reconciliation_note": f"H-PM01 portfolio delta mean R={hpm['hpm01_delta_mean_r']} with DSR-p={hpm['hpm01_dsr_p']}; NAS100-only remains a future shadow candidate.",
            "candidate_strength_vs_j46_j49": "deferred_component_3c_nas100_only_shadow",
        },
        {
            "id": "B-3",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Risk-policy replacement must be simulated over DSR-surviving J46-J49/S79 baselines and needs live-risk approval; current full-stack MC supports shipped stack, not replacement.",
            "reconciliation_note": f"Combined MC full stack has realistic-density P(pass)={hpm['combined_realistic_density_p_pass']} and P(bust HARD)={hpm['combined_realistic_density_p_bust_hard']}; no replacement policy is validated.",
            "candidate_strength_vs_j46_j49": "deferred_risk_replacement_not_validated",
        },
        {
            "id": "B-4",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "Asset-specialist bundle depends on blocked/deferred A-1/A-2/A-3/A-4/A-5/A-6/A-7/A-8; A-9/A-11 are feed-feasibility only.",
            "reconciliation_note": "The bundle cannot be treated as complete because most constituent specialist features lack source-complete as-of data.",
            "candidate_strength_vs_j46_j49": "blocked_bundle_constituents_unavailable",
        },
        {
            "id": "B-7",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "Edge-mechanism bundle has E-1 failed, E-2 deferred, E-4 blocked, and E-3 blocked below.",
            "reconciliation_note": "No bundle-level edge-mechanism validation can proceed from current local data.",
            "candidate_strength_vs_j46_j49": "blocked_bundle_constituents_unavailable",
        },
        {
            "id": "C-3",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "Inverted-TP log has correction records but no symbol/outcome linkage, so Walasek lambda-context dependence cannot be measured from current data.",
            "reconciliation_note": f"knowledge_base/inverted_tp_log.jsonl has {inv_rows} rows; keys lack realized-R/outcome and symbol is missing in current rows.",
            "candidate_strength_vs_j46_j49": "blocked_missing_outcome_linkage",
        },
        {
            "id": "C-4",
            "status": "DONE",
            "blocked_by": "",
            "reconciliation_note": f"Daniel-Moskowitz-style LONG modifier simulation is closed by H-PM03/combined MC: side_aware_everywhere H2 P(pass)={hpm['hpm03_side_aware_h2_p_pass']} and full P(bust HARD)={hpm['hpm03_side_aware_full_p_bust_hard']}.",
            "candidate_strength_vs_j46_j49": "risk_modifier_live_stack_not_new_signal",
        },
        {
            "id": "C-5",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "K54/K55 same-cohort training is closed after v3/v4 failures; reopen only with n>=5000 or source-quality/cohort-expansion trigger.",
            "reconciliation_note": "Sharpe-objective training is a future K-family loss-function study, not an unblocked current-cohort task.",
            "candidate_strength_vs_j46_j49": "deferred_loss_function_until_new_cohort",
        },
        {
            "id": "C-6",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Continuous-sized entries require actual broker-R/fill truth, lifecycle telemetry, and live-risk approval before system-flow use.",
            "reconciliation_note": "Existing MC covers fixed policy overlays; continuous sizing remains future research after label-truth blockers clear.",
            "candidate_strength_vs_j46_j49": "deferred_continuous_sizing_label_truth",
        },
        {
            "id": "C-8",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "Feature-stability artifacts exist, but there is no K54 production deployment performance series because K54 is not deployed.",
            "reconciliation_note": f"K54 v3 mean Jaccard={stability['k54_v3_mean_jaccard']} with stable features={stability['k54_v3_stable_features']}; deployment-performance regression awaits K55 shadow/live rows.",
            "candidate_strength_vs_j46_j49": "blocked_no_production_ml_performance_series",
        },
        {
            "id": "E-3",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "Lillo-Mike-Farmer-Sato meta-order long-memory needs signed order-flow/meta-order aggregates; local OHLCV/H1 bars and MT5 tick volume are not a parent-order flow substrate.",
            "reconciliation_note": "Do not substitute candle direction or retail tick volume for signed meta-order flow.",
            "candidate_strength_vs_j46_j49": "blocked_missing_signed_orderflow",
        },
        {
            "id": "E-5",
            "status": "DONE",
            "blocked_by": "",
            "reconciliation_note": "Uncorrelated-edge discovery inventory is current via NA-11 plus queue state: empirical alpha correlation is low, but live candidates remain discovery/forward-shadow only.",
            "candidate_strength_vs_j46_j49": "not_single_strategy_inventory_only",
        },
        {
            "id": "R-1",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Risk-constrained Kelly replacement needs a preregistered simulation over DSR-surviving J46-J49/S79 baselines and CEO approval before risk behavior changes.",
            "reconciliation_note": "Current evidence supports shipped S79/full-stack risk, not replacing it with RCK.",
            "candidate_strength_vs_j46_j49": "deferred_risk_policy_replacement",
        },
        {
            "id": "R-2",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Lambda auto-calibration depends on R-1 and owner-approved risk replacement path.",
            "reconciliation_note": "No lambda knob is approved or validated for FN constraint auto-calibration.",
            "candidate_strength_vs_j46_j49": "deferred_depends_on_r1",
        },
        {
            "id": "R-5",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Per-instrument weights require the R-1 simulation path and source-flagged all-symbol cohort; do not override S79 uniform profile from current evidence.",
            "reconciliation_note": "Existing S79/full-stack evidence remains the active baseline; per-instrument optimized weights are future research.",
            "candidate_strength_vs_j46_j49": "deferred_weight_optimization_not_validated",
        },
        {
            "id": "R-6",
            "status": "DONE",
            "blocked_by": "",
            "reconciliation_note": f"Side-aware sizing is closed by H-PM03/combined MC and existing config flip: side_aware_everywhere full P(bust HARD)={hpm['hpm03_side_aware_full_p_bust_hard']}.",
            "candidate_strength_vs_j46_j49": "risk_modifier_already_live_not_new_signal",
        },
        {
            "id": "R-7",
            "status": "REJECTED_FAILED",
            "blocked_by": "",
            "reconciliation_note": f"All-7 vol-scaled sizing failed portfolio-wide in H-PM01: delta mean R={hpm['hpm01_delta_mean_r']}, DSR-p={hpm['hpm01_dsr_p']}; NAS100-only remains separate deferred/shadow candidate.",
            "candidate_strength_vs_j46_j49": "rejected_portfolio_wide_vol_scaled_sizing",
        },
        {
            "id": "R-8",
            "status": "DONE",
            "blocked_by": "",
            "reconciliation_note": "Lambda-context audit is resolved at control level: live risk assumptions are fixed-profile S79/side-aware scalars, while any lambda-knob replacement is deferred under R-1/R-2.",
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_static_risk_audit",
        },
        {
            "id": "R-9",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Bundle depends on deferred R-1/R-2/R-5 and rejected R-7; only R-6 is done.",
            "reconciliation_note": "Risk-policy bundle cannot replace S79/full-stack from current evidence.",
            "candidate_strength_vs_j46_j49": "deferred_bundle_constituents_not_ready",
        },
    ]


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(out)


def render_markdown(payload: dict[str, Any]) -> str:
    evidence = payload["evidence"]
    rows = [
        [item["id"], item["status"], item["blocked_by"] or "-", item["reconciliation_note"]]
        for item in payload["classifications"]
    ]
    lines = [
        "# Lane 6 Priority-620 Triage",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "Scope: research/tooling only",
        "Promotion verdict: `NO_PROMOTION_VERDICT`",
        "",
        "## Question Registered Before Output",
        "",
        payload["hypothesis_before_outputs"],
        "",
        "## Local Evidence Inventory",
        "",
        f"- FRED normalized series: `{', '.join(evidence['fred_series'])}`.",
        f"- FlashAlpha GEX proxy rows: `{evidence['flashalpha_gex']['rows']}` across `{evidence['flashalpha_gex']['files']}` files.",
        f"- CFTC COT latest rows: `{evidence['cftc_cot']['rows']}`; symbols: `{evidence['cftc_cot']['symbols']}`.",
        f"- LBMA calendar latest rows: `{evidence['lbma_calendar']['rows']}`; symbols: `{evidence['lbma_calendar']['symbols']}`.",
        f"- Inverted-TP log rows: `{evidence['inverted_tp']['rows']}`.",
        f"- H-PM01 portfolio delta mean R: `{evidence['position_management']['hpm01_delta_mean_r']}`, DSR-p: `{evidence['position_management']['hpm01_dsr_p']}`.",
        f"- H-PM03 side-aware H2 P(pass): `{evidence['position_management']['hpm03_side_aware_h2_p_pass']}`; full P(bust HARD): `{evidence['position_management']['hpm03_side_aware_full_p_bust_hard']}`.",
        f"- K54 v3 feature-stability mean Jaccard: `{evidence['feature_stability']['k54_v3_mean_jaccard']}`.",
        "",
        "## Classification Matrix",
        "",
        markdown_table(["ID", "Status", "Blocked By", "Evidence / Note"], rows),
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "This triage does not validate or promote a trading rule, live filter, risk setting, or execution change. It only classifies which priority-620 Lane 6 tasks are locally executable, blocked, deferred, rejected, or already closed by committed research artifacts.",
        "",
    ]
    return "\n".join(lines)


def build_payload(root: str | Path = ".") -> dict[str, Any]:
    repo = Path(root)
    evidence = build_evidence(repo)
    items = classifications(evidence)
    return {
        "schema_version": "lane6_priority620_triage_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "hypothesis_before_outputs": (
            "Most priority-620 Lane 6 tasks will classify as feed/source blocked, "
            "risk-approval deferred, or already closed by H-PM/S79/J46 evidence; "
            "only feed-feasibility items with local normalized data should move to DONE."
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

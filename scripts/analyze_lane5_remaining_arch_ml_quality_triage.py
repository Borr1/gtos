#!/usr/bin/env python3
"""Triage remaining Lane 5 architecture/ML-quality backlog items.

Research/tooling only. This script reconciles K-16/K-17, P-7..P-10,
and S-1..S-5 against current K54 v3/v4 evidence, data-source state,
literature-prior artifacts, and the existing K55 shadow ticket.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_JSON = "research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.json"
DEFAULT_OUTPUT_MD = "research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def k54_evidence(root: Path) -> dict[str, Any]:
    v3_dsr = _read_json(root / "research" / "ml_program" / "models" / "k54_v3" / "dsr_per_gate.json")
    v3_specialist = _read_json(
        root / "research" / "ml_program" / "models" / "k54_v3" / "specialist_results.json"
    )
    v4_verdicts = _read_json(
        root / "research" / "ml_program" / "models" / "k54_v4" / "final_verdicts.json"
    )
    v4_ablation = _read_json(
        root / "research" / "ml_program" / "models" / "k54_v4" / "component_ablation.json"
    )
    verdicts = v4_verdicts.get("verdicts") or {}
    gate_b = v3_dsr.get("gate_b_primary_lift") or {}
    routing = v4_ablation.get("t7_nas_routing_add_over_master_nas_fallthrough") or {}
    return {
        "v3_lift": gate_b.get("lift_observed"),
        "v3_dsr_p": gate_b.get("dsr_p"),
        "v3_pbo": gate_b.get("pbo"),
        "v3_verdict": gate_b.get("verdict"),
        "v4_all_architectures_failed": bool(verdicts) and all(
            row.get("verdict") == "FAIL" for row in verdicts.values()
        ),
        "v4_ship_arch": v4_verdicts.get("ship_arch"),
        "v4_t7_nas_routing_delta": routing.get("per_path_mean"),
        "v4_t7_nas_routing_p": routing.get("boot_p_one_sided"),
        "nas_us30_specialist_n": v3_specialist.get("n_nas_us30"),
        "nas_us30_specialist_auc": v3_specialist.get("specialist_auc"),
        "nas_us30_specialist_delta": v3_specialist.get("delta"),
        "nas_us30_specialist_gate_pass": v3_specialist.get("gate_pass"),
    }


def data_source_evidence(root: Path) -> dict[str, Any]:
    data_source = _read_json(
        root / "research" / "ml_program" / "audit" / "LANE5_DATA_SOURCE_TRIAGE_2026-05-03.json"
    )
    ticks = ((data_source.get("inventories") or {}).get("ticks") or {})
    d11 = _read_json(
        root / "research" / "ml_program" / "audit" / "D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.json"
    )
    old_label_gaps = ((d11.get("inventories") or {}).get("old_label_gaps") or {})
    return {
        "tick_max_symbol_days": ticks.get("max_symbol_days"),
        "tick_symbols_with_ticks": ticks.get("symbols_with_ticks"),
        "tick_capture_daemon_exists": ticks.get("tick_capture_daemon_exists"),
        "tick_features_helper_exists": ticks.get("tick_features_helper_exists"),
        "old_label_gaps": old_label_gaps,
    }


def k55_ticket_evidence(root: Path) -> dict[str, Any]:
    ticket_path = root / "research" / "operations" / "k55_shadow_k54_v3_top3pct_integration_ticket_2026-04-29.md"
    ticket = _read_text(ticket_path)
    return {
        "ticket_exists": ticket_path.exists(),
        "ticket_path": ticket_path.relative_to(root).as_posix(),
        "mentions_target_upgrade_pending": "TARGET MODEL UPGRADE PENDING" in ticket,
        "mentions_orchestrator_hook": "orchestrator.py" in ticket,
        "mentions_config_flag": "k55_shadow:" in ticket,
        "shadow_module_exists": (root / "src" / "components" / "k55_shadow.py").exists(),
        "shadow_logger_exists": (root / "src" / "components" / "k55_shadow_logger.py").exists(),
        "shadow_monitor_exists": (root / "scripts" / "k55_shadow_monitor.py").exists(),
    }


def literature_evidence(root: Path) -> dict[str, Any]:
    group_a = _read_text(root / "research" / "ml_program" / "literature" / "synthesis" / "group_a_foundations.md")
    group_b = _read_text(root / "research" / "ml_program" / "literature" / "synthesis" / "group_b_microstructure.md")
    return {
        "sticky_hdp_hmm_ranked": "H-Sticky-HDP-HMM-Regime-Classifier" in group_a,
        "kirby_null_test_required": "Kirby" in group_a and "null-test" in group_a,
        "trade_count_time_ranked": "H-Trade-Count-Time-Triggers" in group_a,
        "signature_fracdiff_harrv_ranked": all(
            term in group_a
            for term in (
                "H-Signature-Feature-K54-v2",
                "H-Fractional-Differentiation-Features",
                "H-HAR-RV-Cascade-K54-Features",
            )
        ),
        "hawkes_threshold_ranked": "H-Hawkes-Dynamic-Correlation-Threshold" in group_a
        or "Hawkes process toxicity" in group_b,
    }


def build_evidence(root: str | Path = REPO_ROOT) -> dict[str, Any]:
    root_path = Path(root)
    return {
        "k54": k54_evidence(root_path),
        "data_source": data_source_evidence(root_path),
        "k55_ticket": k55_ticket_evidence(root_path),
        "literature": literature_evidence(root_path),
    }


def classify_tasks(evidence: dict[str, Any]) -> dict[str, dict[str, Any]]:
    k54 = evidence["k54"]
    data_source = evidence["data_source"]
    k55 = evidence["k55_ticket"]
    literature = evidence["literature"]
    artifact = DEFAULT_OUTPUT_MD

    return {
        "K-16": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "Focal loss (gamma=2, alpha=0.25) for trending_bull-LONG cells.",
            "blocked_by": "No same-cohort K54 architecture iteration remains unblocked after K54 v3/v4 primary failure; focal loss would be another current-cohort loss-function variant.",
            "trigger": "Reopen only with n>=5000 regime-balanced labels or a new label-rich K55 shadow cohort plus a preregistered focal-loss comparison.",
            "latest_artifact_path": artifact,
            "evidence": {
                "v3_verdict": k54["v3_verdict"],
                "v3_dsr_p": k54["v3_dsr_p"],
                "v4_all_architectures_failed": k54["v4_all_architectures_failed"],
            },
            "candidate_strength_vs_j46_j49": "deferred_same_cohort_k54_closed",
        },
        "K-17": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "Hierarchical-Bayesian K54 pooling for data-poor instruments.",
            "blocked_by": "Pooled K54 v3/v4 training failed global gates, and data-poor instruments still need source-period flags and missing old labels resolved before new pooling claims are meaningful.",
            "trigger": "Reopen after missing old labels/source-period flags are fixed and n>=5000 or a new source-balanced cohort exists.",
            "latest_artifact_path": artifact,
            "evidence": {
                "v4_all_architectures_failed": k54["v4_all_architectures_failed"],
                "old_label_gaps": data_source["old_label_gaps"],
            },
            "candidate_strength_vs_j46_j49": "deferred_cohort_quality",
        },
        "P-7": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "Hawkes-process-based heartbeat/drawdown re-thresholds.",
            "blocked_by": "Heartbeat/drawdown thresholds are safety/risk behavior, current tick history is too short for Hawkes calibration, and live threshold changes require CEO approval.",
            "trigger": "Research-only simulation after >=30 trading days of all-symbol ticks or approved depth/feed data, followed by a separate approval path for any safety/risk threshold change.",
            "latest_artifact_path": artifact,
            "evidence": {
                "tick_max_symbol_days": data_source["tick_max_symbol_days"],
                "hawkes_literature_ranked": literature["hawkes_threshold_ranked"],
            },
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_safety_threshold_research",
        },
        "P-8": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "Sticky HDP-HMM regime classifier with Kirby null-test.",
            "blocked_by": "The literature-prior is documented, but no local HDP-HMM/Kirby-null research harness has passed; replacing the regime classifier would touch live/shadow behavior.",
            "trigger": "Standalone research harness with fat-tailed-mixture Kirby null-test, OOS realized-R comparison, and approval before any runtime replacement.",
            "latest_artifact_path": artifact,
            "evidence": {
                "sticky_hdp_hmm_ranked": literature["sticky_hdp_hmm_ranked"],
                "kirby_null_test_required": literature["kirby_null_test_required"],
            },
            "candidate_strength_vs_j46_j49": "deferred_literature_prior_no_empirical_gate",
        },
        "P-9": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "Trade-count-time triggers in Component 1 data ingestion + tick daemon.",
            "blocked_by": "This depends on D-1 tick-count-time substrate maturity and would alter Component 1/tick-daemon runtime behavior; current all-symbol tick history is below the 30-day trigger.",
            "trigger": "Reopen after >=30 trading days of all-symbol ticks or an approved feed, then validate as research-only resampling before any live ingestion hook.",
            "latest_artifact_path": artifact,
            "evidence": {
                "tick_max_symbol_days": data_source["tick_max_symbol_days"],
                "trade_count_time_ranked": literature["trade_count_time_ranked"],
            },
            "candidate_strength_vs_j46_j49": "deferred_depends_on_d1_tick_substrate",
        },
        "P-10": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "Signature features + fractional differentiation + HAR-RV cascade in K54 features.",
            "blocked_by": "Feature family has a literature prior, but same-cohort K54 feature iteration is closed after v3/v4 failure; old-label/source-period blockers still constrain new pooled training.",
            "trigger": "Reopen as a preregistered feature-family ablation after source flags/missing old labels are fixed and n>=5000 or a new label-rich shadow cohort exists.",
            "latest_artifact_path": artifact,
            "evidence": {
                "signature_fracdiff_harrv_ranked": literature["signature_fracdiff_harrv_ranked"],
                "v4_all_architectures_failed": k54["v4_all_architectures_failed"],
            },
            "candidate_strength_vs_j46_j49": "deferred_literature_feature_prior_not_empirical",
        },
        "S-1": {
            "status": "FILED_FOR_APPROVAL",
            "backlog_item": "K55 shadow harness design (read-only ML inference parallel to AI).",
            "blocked_by": "Design ticket exists, but target assumptions are stale after K54 v4 failed and implementation would touch orchestrator/config live paths.",
            "trigger": "Refresh target model to current K55-shadow evidence and obtain explicit approval before scaffold/logger/orchestrator hook implementation.",
            "latest_artifact_path": artifact,
            "evidence": k55,
            "candidate_strength_vs_j46_j49": "filed_design_only_no_promotion",
        },
        "S-2": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "Per-instrument-group ML routing in shadow mode.",
            "blocked_by": "K54 v4 T7-NAS routing add was negative and P-6 is already deferred; routing needs forward K55 specialist evidence first.",
            "trigger": "Reopen after K55-shadow specialist evidence clears sample, stability, and approval gates.",
            "latest_artifact_path": artifact,
            "evidence": {
                "routing_delta": k54["v4_t7_nas_routing_delta"],
                "routing_p": k54["v4_t7_nas_routing_p"],
            },
            "candidate_strength_vs_j46_j49": "deferred_inherits_p6_routing_failure",
        },
        "S-3": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "K55 30-day shadow evaluation (Q4 spec).",
            "blocked_by": "No K55 shadow logger/output exists yet; 30-day evaluation requires implementation plus enough forward shadow events.",
            "trigger": "Run only after S-1 implementation/smoke test and >=30 days or n>=50 K55-shadow events.",
            "latest_artifact_path": artifact,
            "evidence": k55,
            "candidate_strength_vs_j46_j49": "deferred_no_shadow_rows",
        },
        "S-4": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "Hybrid ML+AI ensemble vs pure-AI baseline measurement.",
            "blocked_by": "No paired live AI+ML shadow dataset exists; current K54 evidence is discovery/refinement only.",
            "trigger": "Reopen after S-3 produces paired AI decision, K55 decision, and realized-R rows at preregistered sample floors.",
            "latest_artifact_path": artifact,
            "evidence": {
                "shadow_logger_exists": k55["shadow_logger_exists"],
                "nas_us30_specialist_delta": k54["nas_us30_specialist_delta"],
            },
            "candidate_strength_vs_j46_j49": "deferred_no_paired_shadow_dataset",
        },
        "S-5": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "K55 production gate flip.",
            "blocked_by": "Production flip requires successful S-3/S-4 shadow evaluation, promotion dossier, and explicit CEO approval; no such evidence exists.",
            "trigger": "Only after shadow correlation/lift clears the registered gate, including >=1.2x AI where applicable, with a separate promotion dossier.",
            "latest_artifact_path": artifact,
            "evidence": k55,
            "candidate_strength_vs_j46_j49": "deferred_requires_future_promotion_dossier",
        },
    }


def build_payload(root: str | Path = REPO_ROOT) -> dict[str, Any]:
    root_path = Path(root)
    evidence = build_evidence(root_path)
    payload = {
        "schema_version": "lane5_remaining_arch_ml_quality_triage_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "scope": "research/tooling only",
        "question": "Classify remaining Lane 5 K/P/S architecture and ML-quality items from existing evidence.",
        "source_files": [
            "research/ml_program/MASTER_BACKLOG.md",
            "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md",
            "research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md",
            "research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.json",
            "research/ml_program/audit/D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.json",
            "research/ml_program/models/k54_v3/",
            "research/ml_program/models/k54_v4/",
            "research/ml_program/literature/synthesis/group_a_foundations.md",
            "research/operations/k55_shadow_k54_v3_top3pct_integration_ticket_2026-04-29.md",
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
    k54 = evidence["k54"]
    data_source = evidence["data_source"]
    k55 = evidence["k55_ticket"]
    tasks = payload["task_classifications"]
    lines = [
        "# Lane 5 Remaining Architecture / ML Quality Triage",
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
        f"- K54 v3 primary lift `{k54['v3_lift']}` failed with DSR-p `{k54['v3_dsr_p']}`; K54 v4 all architectures failed `{k54['v4_all_architectures_failed']}` and ship arch `{k54['v4_ship_arch']}`.",
        f"- T7/NAS routing add over master fallthrough: delta `{k54['v4_t7_nas_routing_delta']}`, p `{k54['v4_t7_nas_routing_p']}`.",
        f"- NAS_US30 specialist remains discovery/shadow-only: n `{k54['nas_us30_specialist_n']}`, AUC `{k54['nas_us30_specialist_auc']}`, delta `{k54['nas_us30_specialist_delta']}`.",
        f"- Tick substrate remains short: max symbol days `{data_source['tick_max_symbol_days']}`, symbols with ticks `{data_source['tick_symbols_with_ticks']}`.",
        f"- Existing K55 ticket present `{k55['ticket_exists']}`, target-upgrade-pending text `{k55['mentions_target_upgrade_pending']}`, shadow module exists `{k55['shadow_module_exists']}`.",
        "",
        "## Task Classifications",
        "",
        "| id | status | blocker / trigger | candidate strength |",
        "| --- | --- | --- | --- |",
    ]
    for item_id in ("K-16", "K-17", "P-7", "P-8", "P-9", "P-10", "S-1", "S-2", "S-3", "S-4", "S-5"):
        row = tasks[item_id]
        lines.append(
            "| {id} | {status} | {blocker} Trigger: {trigger} | {strength} |".format(
                id=item_id,
                status=row["status"],
                blocker=row["blocked_by"].replace("|", r"\|"),
                trigger=row["trigger"].replace("|", r"\|"),
                strength=row["candidate_strength_vs_j46_j49"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The K/P architecture ideas remain research-useful, but none is executable as a same-cohort K54 architecture iteration now.",
            "- `S-1` is not an unblocked coding task: a design ticket exists, but the target model needs refresh and implementation would touch live orchestrator/config paths.",
            "- `S-2` through `S-5` depend on a working K55 shadow dataset and later promotion evidence; they are not current validation claims.",
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
            "This artifact classifies architecture and ML-quality readiness only. It does not validate, promote, or modify live trading behavior.",
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

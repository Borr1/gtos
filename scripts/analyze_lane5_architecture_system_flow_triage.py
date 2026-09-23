#!/usr/bin/env python3
"""Triage Lane 5 architecture/system-flow backlog items P-1/P-2/P-3/P-5/P-6.

Research/tooling only. This script reads existing phase-2 and K54 artifacts to
classify system-flow work without changing live trading logic.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_JSON = (
    "research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.json"
)
DEFAULT_OUTPUT_MD = "research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def load_evidence(root: Path) -> dict[str, Any]:
    hpm01_path = (
        root
        / "research"
        / "ml_program"
        / "phase_2"
        / "position_mgmt"
        / "h_pm01_per_cohort_results.json"
    )
    v3_dir = root / "research" / "ml_program" / "models" / "k54_v3"
    v4_dir = root / "research" / "ml_program" / "models" / "k54_v4"

    hpm01 = _read_json(hpm01_path)
    primary_full = hpm01.get("primary_full_cohort") or {}
    per_instrument = ((hpm01.get("per_cohort") or {}).get("per_instrument") or {})
    nas100 = per_instrument.get("NAS100") or {}

    conformal = _read_json(v3_dir / "conformal_calibration.json")
    v4_component = _read_json(v4_dir / "component_ablation.json")
    v4_verdicts = _read_json(v4_dir / "final_verdicts.json")

    return {
        "source_files": [
            "research/ml_program/phase_2/position_mgmt/h_pm01_vol_conditional_sizing.md",
            _safe_rel(hpm01_path, root),
            "research/ml_program/phase_2/MASTER_SYNTHESIS_PHASE_2.md",
            "research/ml_program/audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md",
            "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md",
            _safe_rel(v3_dir / "conformal_calibration.json", root),
            _safe_rel(v4_dir / "component_ablation.json", root),
            _safe_rel(v4_dir / "final_verdicts.json", root),
        ],
        "vol_conditioning": {
            "cohort_size": (hpm01.get("metadata") or {}).get("cohort_size"),
            "full_cohort_delta_mean_r": ((primary_full.get("backtest") or {}).get("delta") or {}).get("mean_r"),
            "full_cohort_delta_sharpe_pct": (
                ((primary_full.get("backtest") or {}).get("delta") or {}).get("sharpe_pct")
            ),
            "full_cohort_dsr_p": (primary_full.get("dsr_paired_delta") or {}).get("dsr_p"),
            "full_cohort_gate_pass": (primary_full.get("gate") or {}).get("overall_pass"),
            "nas100_delta_mean_r": ((nas100.get("backtest") or {}).get("delta") or {}).get("mean_r"),
            "nas100_delta_sharpe_pct": ((nas100.get("backtest") or {}).get("delta") or {}).get("sharpe_pct"),
            "nas100_dsr_p": (nas100.get("dsr_paired") or {}).get("dsr_p"),
            "nas100_n_trades": (nas100.get("backtest") or {}).get("n_trades"),
        },
        "meta_labeling": {
            "component_ran": (v3_dir / "k54_v3_meta_label.lgb").exists(),
            "sample_constraint": "n=528 with about 250 primary-positive rows",
            "status_from_k54_triage": "DEFERRED_WITH_TRIGGER",
            "trigger": "n>5000 or new label-rich K55 shadow cohort",
        },
        "conformal": {
            "coverage_observed": conformal.get("coverage_observed"),
            "target_coverage": conformal.get("target_coverage"),
            "christoffersen_p": conformal.get("christoffersen_p"),
            "gate_g_status": conformal.get("gate_g_status"),
        },
        "pooled_training": {
            "status_from_k54_triage": "REJECTED_FAILED",
            "reason": "K-5 W-unit pooling failed and K-6 pooled K54 v3/v4 training failed global gates.",
        },
        "routing": {
            "v4_gate_h_pass": v4_component.get("gate_h_pass"),
            "t7_nas_routing_delta": (
                (v4_component.get("t7_nas_routing_add_over_master_nas_fallthrough") or {}).get(
                    "per_path_mean"
                )
            ),
            "t7_nas_routing_boot_p": (
                (v4_component.get("t7_nas_routing_add_over_master_nas_fallthrough") or {}).get(
                    "boot_p_one_sided"
                )
            ),
            "ship_arch": v4_verdicts.get("ship_arch"),
            "all_v4_architectures_failed": bool(v4_verdicts.get("verdicts"))
            and all(str(row.get("verdict")) == "FAIL" for row in (v4_verdicts.get("verdicts") or {}).values()),
        },
    }


def classify_tasks(evidence: dict[str, Any]) -> dict[str, dict[str, Any]]:
    artifact = "research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md"
    vol = evidence["vol_conditioning"]
    meta = evidence["meta_labeling"]
    conformal = evidence["conformal"]
    pooled = evidence["pooled_training"]
    routing = evidence["routing"]

    return {
        "P-1": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "Component 3C Vol-Conditioning Overlay implementation.",
            "blocked_by": "Portfolio-wide vol-conditioning failed H-PM01; live insertion between 3A and execution would change risk/trading behavior and needs CEO approval even for shadow.",
            "trigger": "Reopen only as NAS100-only shadow A/B after approval, or after a fresh vol-conditioning preregistration clears portfolio-wide gates.",
            "latest_artifact_path": artifact,
            "evidence": vol,
            "candidate_strength_vs_j46_j49": (
                "NAS100-only subcandidate delta_R "
                f"{vol.get('nas100_delta_mean_r')} DSR-p {vol.get('nas100_dsr_p')}; "
                "portfolio-wide failed, not promotion comparable"
            ),
        },
        "P-2": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "Component 3D Meta-labeling head module.",
            "blocked_by": "Meta-labeling ran in K54 v3 but was statistically weak at the current cohort size.",
            "trigger": meta["trigger"],
            "latest_artifact_path": artifact,
            "evidence": meta,
            "candidate_strength_vs_j46_j49": "deferred_sample_size",
        },
        "P-3": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "Adaptive conformal calibration module.",
            "blocked_by": "K54 global candidates failed; conformal has only a CPCV proxy and no live/holdout system-flow candidate to calibrate.",
            "trigger": "Reopen after a K55/K54 shadow candidate is approved and the appropriate holdout/calibration window is pre-registered.",
            "latest_artifact_path": artifact,
            "evidence": conformal,
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_calibration_deferred",
        },
        "P-5": {
            "status": "REJECTED_FAILED",
            "backlog_item": "Pooled multi-instrument training pipeline.",
            "blocked_by": pooled["reason"],
            "trigger": "Reopen only after K-5/K-6 triggers are met: usable LOB/trade-volume substrate or n>=5000 source-flagged cohort.",
            "latest_artifact_path": artifact,
            "evidence": pooled,
            "candidate_strength_vs_j46_j49": "rejected_inherits_k5_k6_failure",
        },
        "P-6": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "Per-instrument-group routing layer at inference.",
            "blocked_by": "K54 v4 T7-NAS routing add was negative and all K54 v4 architectures failed; any inference routing layer is shadow-only until a specialist survives forward evidence.",
            "trigger": "Reopen after K55-shadow specialist evidence clears sample, stability, and approval gates.",
            "latest_artifact_path": artifact,
            "evidence": routing,
            "candidate_strength_vs_j46_j49": "deferred_k55_shadow_specialist_only",
        },
    }


def build_payload(root: str | Path = REPO_ROOT) -> dict[str, Any]:
    root_path = Path(root)
    evidence = load_evidence(root_path)
    classifications = classify_tasks(evidence)
    return {
        "schema_version": "lane5_architecture_system_flow_triage_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "scope": "research/tooling only",
        "question": "Classify Lane 5 P-family system-flow architecture items from existing vol-conditioning and K54 evidence.",
        "source_files": evidence["source_files"],
        "evidence": evidence,
        "task_classifications": classifications,
        "status_counts": dict(
            sorted(Counter(row["status"] for row in classifications.values()).items())
        ),
    }


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: str | Path) -> None:
    evidence = payload["evidence"]
    vol = evidence["vol_conditioning"]
    conformal = evidence["conformal"]
    routing = evidence["routing"]
    tasks = payload["task_classifications"]

    lines = [
        "# Lane 5 Architecture/System-Flow Triage",
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
        "- H-PM01 portfolio-wide vol-conditioning: "
        f"delta mean R `{vol['full_cohort_delta_mean_r']}`, "
        f"delta Sharpe `%` `{vol['full_cohort_delta_sharpe_pct']}`, "
        f"DSR-p `{vol['full_cohort_dsr_p']}`, gate pass `{vol['full_cohort_gate_pass']}`.",
        "- H-PM01 NAS100 subcandidate: "
        f"n `{vol['nas100_n_trades']}`, delta mean R `{vol['nas100_delta_mean_r']}`, "
        f"delta Sharpe `%` `{vol['nas100_delta_sharpe_pct']}`, DSR-p `{vol['nas100_dsr_p']}`.",
        "- Meta-labeling head: ran in K54 v3, but remains sample-size deferred at n=528 / about 250 primary-positive rows.",
        "- Conformal proxy: "
        f"coverage `{conformal['coverage_observed']}` vs target `{conformal['target_coverage']}`, "
        f"Christoffersen p `{conformal['christoffersen_p']}`, status `{conformal['gate_g_status']}`.",
        "- Routing: "
        f"K54 v4 gate_h pass `{routing['v4_gate_h_pass']}`, "
        f"T7-NAS routing delta `{routing['t7_nas_routing_delta']}`, "
        f"boot p `{routing['t7_nas_routing_boot_p']}`, "
        f"ship arch `{routing['ship_arch']}`.",
        "",
        "## Task Classifications",
        "",
        "| id | status | blocker / trigger | candidate strength |",
        "| --- | --- | --- | --- |",
    ]
    for item_id in ("P-1", "P-2", "P-3", "P-5", "P-6"):
        row = tasks[item_id]
        blocker = row["blocked_by"] or row["trigger"]
        lines.append(
            "| {id} | {status} | {blocker} | {strength} |".format(
                id=item_id,
                status=row["status"],
                blocker=blocker.replace("|", r"\|"),
                strength=row["candidate_strength_vs_j46_j49"],
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `P-1` is deferred, not implementation-ready: portfolio-wide Component 3C failed; only a NAS100-only shadow candidate remains and would require approval.",
            "- `P-2` follows `K-12`: meta-labeling is sample-size deferred.",
            "- `P-3` follows `K-14`: calibration tooling exists, but no approved live/holdout candidate is ready for a system-flow module.",
            "- `P-5` inherits the `K-5`/`K-6` failure and is rejected for the current substrate/cohort.",
            "- `P-6` is deferred: current routing ablation failed, and specialist routing must stay K55-shadow-only until forward evidence exists.",
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
            "This artifact classifies architecture/system-flow readiness only. It does not validate, promote, or modify live trading behavior.",
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

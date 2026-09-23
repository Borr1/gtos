#!/usr/bin/env python3
"""Triage Lane 5 K54/K55 architecture backlog items.

Research/tooling only. Reads existing K54 v3/v4 audit/model artifacts and
classifies K-5..K-15 plus K-18 without running new model training or touching
live trading logic.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_JSON = "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.json"
DEFAULT_OUTPUT_MD = "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _variant_auc(payload: dict[str, Any], label_prefix: str) -> float | None:
    for row in payload.get("variants") or []:
        if str(row.get("label") or "").startswith(label_prefix):
            value = row.get("best_hp_oos_mean_auc")
            return float(value) if value is not None else None
    return None


def _gate_summary(verdicts: dict[str, Any]) -> dict[str, Any]:
    rows = verdicts.get("verdicts") or {}
    return {
        "architectures": sorted(rows),
        "all_architectures_failed": bool(rows) and all(
            str(row.get("verdict")) == "FAIL" for row in rows.values()
        ),
        "passed_gates_by_architecture": {
            key: row.get("n_passed") for key, row in sorted(rows.items())
        },
        "testable_gates_by_architecture": {
            key: row.get("n_testable_gates") for key, row in sorted(rows.items())
        },
        "ship_arch": verdicts.get("ship_arch"),
        "closest_to_pass": verdicts.get("closest_to_pass"),
    }


def load_evidence(root: Path) -> dict[str, Any]:
    v3_dir = root / "research" / "ml_program" / "models" / "k54_v3"
    v4_dir = root / "research" / "ml_program" / "models" / "k54_v4"

    v3_dsr = _read_json(v3_dir / "dsr_per_gate.json").get("gate_b_primary_lift") or {}
    v3_w_unit = _read_json(v3_dir / "diagnostic_w_unit_ablation.json")
    v3_feature_stability = _read_json(v3_dir / "feature_stability.json")
    v3_conformal = _read_json(v3_dir / "conformal_calibration.json")
    v3_specialist = _read_json(v3_dir / "specialist_results.json")

    w_unit_on_auc = _variant_auc(v3_w_unit, "K54 v3 features + W-unit ON")
    w_unit_off_auc = _variant_auc(v3_w_unit, "K54 v3 features + W-unit OFF")
    arch_a_auc = _variant_auc(v3_w_unit, "Arch A reproduction")

    v4_verdicts = _read_json(v4_dir / "final_verdicts.json")
    v4_component = _read_json(v4_dir / "component_ablation.json")
    v4_feature_stability = _read_json(v4_dir / "feature_stability.json")

    return {
        "source_files": [
            "research/ml_program/audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md",
            "research/ml_program/KILLED_HYPOTHESES.md",
            "research/ml_program/PRE_REGISTERED_HYPOTHESES.md",
            _safe_rel(v3_dir / "dsr_per_gate.json", root),
            _safe_rel(v3_dir / "diagnostic_w_unit_ablation.json", root),
            _safe_rel(v3_dir / "feature_stability.json", root),
            _safe_rel(v3_dir / "conformal_calibration.json", root),
            _safe_rel(v3_dir / "specialist_results.json", root),
            _safe_rel(v4_dir / "final_verdicts.json", root),
            _safe_rel(v4_dir / "component_ablation.json", root),
            _safe_rel(v4_dir / "feature_stability.json", root),
        ],
        "k54_v3": {
            "primary_lift": {
                "lift_observed": v3_dsr.get("lift_observed"),
                "sr_paired": v3_dsr.get("sr_paired"),
                "dsr_p": v3_dsr.get("dsr_p"),
                "pbo": v3_dsr.get("pbo"),
                "null_p_emp": v3_dsr.get("null_p_emp"),
                "verdict": v3_dsr.get("verdict"),
            },
            "w_unit_ablation": {
                "w_unit_on_auc": w_unit_on_auc,
                "w_unit_off_auc": w_unit_off_auc,
                "arch_a_auc": arch_a_auc,
                "on_minus_off_auc": (
                    w_unit_on_auc - w_unit_off_auc
                    if w_unit_on_auc is not None and w_unit_off_auc is not None
                    else None
                ),
                "v3_features_minus_arch_a_auc": (
                    w_unit_off_auc - arch_a_auc
                    if w_unit_off_auc is not None and arch_a_auc is not None
                    else None
                ),
                "feature_cols_count": v3_w_unit.get("feature_cols_count") or {},
            },
            "feature_stability": {
                "n_paths": v3_feature_stability.get("n_paths"),
                "mean_pairwise_jaccard_top50": v3_feature_stability.get("mean_pairwise_jaccard_top50"),
                "n_features_in_80pct_paths": v3_feature_stability.get("n_features_in_>=80%_paths"),
                "gate_threshold": v3_feature_stability.get("gate_threshold"),
                "gate_pass": v3_feature_stability.get("gate_pass"),
            },
            "conformal": {
                "coverage_observed": v3_conformal.get("coverage_observed"),
                "target_coverage": v3_conformal.get("target_coverage"),
                "christoffersen_p": v3_conformal.get("christoffersen_p"),
                "gate_g_status": v3_conformal.get("gate_g_status"),
            },
            "nas_us30_specialist": {
                "n_nas_us30": v3_specialist.get("n_nas_us30"),
                "specialist_auc": v3_specialist.get("specialist_auc"),
                "global_v3_on_nas": v3_specialist.get("global_v3_on_nas"),
                "delta": v3_specialist.get("delta"),
                "gate_pass": v3_specialist.get("gate_pass"),
            },
        },
        "k54_v4": {
            "verdict_summary": _gate_summary(v4_verdicts),
            "component_ablation": {
                "master_bundle_add_over_arch_a": (
                    v4_component.get("master_bundle_add_over_arch_a") or {}
                ),
                "t7_nas_routing_add_over_master": (
                    v4_component.get("t7_nas_routing_add_over_master_nas_fallthrough") or {}
                ),
                "gate_h_pass": v4_component.get("gate_h_pass"),
            },
            "feature_stability": v4_feature_stability,
        },
    }


def classify_tasks(evidence: dict[str, Any]) -> dict[str, dict[str, Any]]:
    v3 = evidence["k54_v3"]
    v4 = evidence["k54_v4"]
    w_unit = v3["w_unit_ablation"]
    primary = v3["primary_lift"]
    stability = v3["feature_stability"]
    conformal = v3["conformal"]
    specialist = v3["nas_us30_specialist"]
    v4_verdict = v4["verdict_summary"]
    component = v4["component_ablation"]

    common_artifact = "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md"
    q14_artifact = "research/ml_program/audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md"
    k55_strength = (
        "NAS_US30 specialist remains a K55-shadow discovery only: "
        f"AUC {specialist.get('specialist_auc')} delta {specialist.get('delta')}"
    )

    return {
        "K-5": {
            "status": "REJECTED_FAILED",
            "backlog_item": "Kyle-Obizhaeva W-unit normalization for pooled multi-instrument K54.",
            "blocked_by": "Raw W-unit pooling failed on the MT5 retail/CFD substrate; literal mechanism needs LOB/TAQ-style depth and trade volume.",
            "trigger": "Reopen only with approved LOB/trade-volume substrate or a new pre-registered pooling transform.",
            "latest_artifact_path": common_artifact,
            "evidence": {
                "w_unit_on_auc": w_unit["w_unit_on_auc"],
                "w_unit_off_auc": w_unit["w_unit_off_auc"],
                "on_minus_off_auc": w_unit["on_minus_off_auc"],
            },
            "candidate_strength_vs_j46_j49": "rejected_substrate_failed",
        },
        "K-6": {
            "status": "REJECTED_FAILED",
            "backlog_item": "Pooled multi-instrument K54 training pipeline.",
            "blocked_by": "Pooled K54 v3/v4 training ran and failed global decision gates; same-cohort iteration is closed.",
            "trigger": "Reopen only after cohort expansion to n>=5000 with source-period flags and missing old labels resolved.",
            "latest_artifact_path": common_artifact,
            "evidence": {
                "v3_verdict": primary["verdict"],
                "v3_dsr_p": primary["dsr_p"],
                "v4_all_architectures_failed": v4_verdict["all_architectures_failed"],
                "v4_passed_gates_by_architecture": v4_verdict["passed_gates_by_architecture"],
            },
            "candidate_strength_vs_j46_j49": "rejected_global_k54_failed",
        },
        "K-7": {
            "status": "REJECTED_FAILED",
            "backlog_item": "Osler stop-cluster feature for FX K54.",
            "blocked_by": "K-7..K-10 additions contributed only below-noise lift in the K54 v3 ablation.",
            "trigger": "Reopen only after n>=5000 or a feature-specific pre-registered cohort where stop clusters are directly measured.",
            "latest_artifact_path": common_artifact,
            "evidence": {
                "v3_features_minus_arch_a_auc": w_unit["v3_features_minus_arch_a_auc"],
                "postmortem_note": "K-7 marginal; not in top-50 across paths.",
            },
            "candidate_strength_vs_j46_j49": "rejected_below_noise",
        },
        "K-8": {
            "status": "REJECTED_FAILED",
            "backlog_item": "Power-law-decayed OB-age weighting.",
            "blocked_by": "K-7..K-10 additions contributed only below-noise lift in the K54 v3 ablation.",
            "trigger": "Reopen only with larger cohort or a standalone OB-age preregistration that clears the methodology gate.",
            "latest_artifact_path": common_artifact,
            "evidence": {
                "v3_features_minus_arch_a_auc": w_unit["v3_features_minus_arch_a_auc"],
            },
            "candidate_strength_vs_j46_j49": "rejected_below_noise",
        },
        "K-9": {
            "status": "REJECTED_FAILED",
            "backlog_item": "Regime x round_aligned x side interaction features.",
            "blocked_by": "K-9 was below noise in the K54 v3 global model and the global K54 family failed per-cohort floors.",
            "trigger": "Reopen only with larger cohort and per-cohort interaction preregistration.",
            "latest_artifact_path": common_artifact,
            "evidence": {
                "v3_features_minus_arch_a_auc": w_unit["v3_features_minus_arch_a_auc"],
            },
            "candidate_strength_vs_j46_j49": "rejected_below_noise",
        },
        "K-10": {
            "status": "REJECTED_FAILED",
            "backlog_item": "Above-up / below-down round-aligned OB direction feature.",
            "blocked_by": "K-10 appeared marginally in some top-100 screens but did not produce decision-grade lift.",
            "trigger": "Reopen only after n>=5000 or as a standalone asset-specialist feature test.",
            "latest_artifact_path": common_artifact,
            "evidence": {
                "v3_features_minus_arch_a_auc": w_unit["v3_features_minus_arch_a_auc"],
                "postmortem_note": "Marginal; appears in some path top-100s only.",
            },
            "candidate_strength_vs_j46_j49": "rejected_below_noise",
        },
        "K-11": {
            "status": "DONE",
            "backlog_item": "Per-fold top-100 feature screening.",
            "blocked_by": "",
            "trigger": "No backlog blocker remains for the research component; keep as methodology/tooling, not a promotion verdict.",
            "latest_artifact_path": q14_artifact,
            "evidence": {
                "architecture_a_ran": True,
                "v3_feature_stability_gate_pass": stability["gate_pass"],
                "mean_pairwise_jaccard_top50": stability["mean_pairwise_jaccard_top50"],
            },
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_tooling_done",
        },
        "K-12": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "Meta-labeling head over Component 3A AI direction.",
            "blocked_by": "Meta-labeling ran, but n=528 with about 250 primary-positive rows was statistically weak and showed no measurable lift.",
            "trigger": "Reintroduce at n>5000 or after a new label-rich K55 shadow cohort is available.",
            "latest_artifact_path": common_artifact,
            "evidence": {
                "component_ran": True,
                "sample_constraint": "n=528 with about 250 primary-positive rows",
            },
            "candidate_strength_vs_j46_j49": "deferred_sample_size",
        },
        "K-13": {
            "status": "DONE",
            "backlog_item": "Triple-barrier labeling.",
            "blocked_by": "",
            "trigger": "No backlog blocker remains for the research label component.",
            "latest_artifact_path": q14_artifact,
            "evidence": {
                "used_by_meta_label_head": True,
            },
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_tooling_done",
        },
        "K-14": {
            "status": "DONE",
            "backlog_item": "Adaptive conformal calibration on K54 v3 outputs.",
            "blocked_by": "",
            "trigger": "CPCV proxy exists; true holdout remains a separate deferred validation gate, not an implementation blocker.",
            "latest_artifact_path": common_artifact,
            "evidence": conformal,
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_calibration_done",
        },
        "K-15": {
            "status": "DONE",
            "backlog_item": "TreeSHAP-stability pruning gate.",
            "blocked_by": "",
            "trigger": "Gate is implemented/reported; current K54 features failed stability, which is a result rather than a tooling blocker.",
            "latest_artifact_path": common_artifact,
            "evidence": stability,
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_stability_gate_done",
        },
        "K-18": {
            "status": "REJECTED_FAILED",
            "backlog_item": "K54 v3 master bundle.",
            "blocked_by": "K54 v3 master failed DSR and stability gates; K54 v4 fallback architectures also failed. No same-cohort K54 architecture iteration remains unblocked.",
            "trigger": "Reopen only after the data/cohort triggers are met: n>=5000 or alternate broker/provider pre-2024 GBPJPY+US30 coverage plus v2/v3 feature backfill.",
            "latest_artifact_path": common_artifact,
            "evidence": {
                "v3_lift_observed": primary["lift_observed"],
                "v3_dsr_p": primary["dsr_p"],
                "v3_pbo": primary["pbo"],
                "v3_verdict": primary["verdict"],
                "v4_all_architectures_failed": v4_verdict["all_architectures_failed"],
                "v4_ship_arch": v4_verdict["ship_arch"],
                "master_bundle_add_over_arch_a": component["master_bundle_add_over_arch_a"],
            },
            "candidate_strength_vs_j46_j49": k55_strength,
        },
    }


def build_payload(root: str | Path = REPO_ROOT) -> dict[str, Any]:
    root_path = Path(root)
    evidence = load_evidence(root_path)
    classifications = classify_tasks(evidence)
    return {
        "schema_version": "lane5_k54_architecture_triage_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "scope": "research/tooling only",
        "question": "Classify K54/K55 architecture backlog items K-5..K-15 and K-18 from existing K54 v3/v4 artifacts.",
        "source_files": evidence["source_files"],
        "evidence": {
            "k54_v3": evidence["k54_v3"],
            "k54_v4": evidence["k54_v4"],
        },
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
    v3 = payload["evidence"]["k54_v3"]
    v4 = payload["evidence"]["k54_v4"]
    tasks = payload["task_classifications"]
    lines = [
        "# Lane 5 K54 Architecture Triage",
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
        "- K54 v3 primary lift: "
        f"`{v3['primary_lift']['lift_observed']}`; DSR-p `{v3['primary_lift']['dsr_p']}`; "
        f"PBO `{v3['primary_lift']['pbo']}`; verdict `{v3['primary_lift']['verdict']}`.",
        "- W-unit ablation: "
        f"ON AUC `{v3['w_unit_ablation']['w_unit_on_auc']}` vs OFF AUC `{v3['w_unit_ablation']['w_unit_off_auc']}`; "
        f"v3 features over Arch A `{v3['w_unit_ablation']['v3_features_minus_arch_a_auc']}`.",
        "- Feature stability: "
        f"`{v3['feature_stability']['n_features_in_80pct_paths']}` stable features; "
        f"mean Jaccard `{v3['feature_stability']['mean_pairwise_jaccard_top50']}`; "
        f"gate pass `{v3['feature_stability']['gate_pass']}`.",
        "- Conformal proxy: "
        f"coverage `{v3['conformal']['coverage_observed']}` vs target `{v3['conformal']['target_coverage']}`; "
        f"Christoffersen p `{v3['conformal']['christoffersen_p']}`.",
        "- K54 v4 verdicts: "
        f"all architectures failed `{v4['verdict_summary']['all_architectures_failed']}`; "
        f"ship arch `{v4['verdict_summary']['ship_arch']}`.",
        "- Strongest remaining K-family finding is the NAS_US30 specialist as K55-shadow discovery only: "
        f"AUC `{v3['nas_us30_specialist']['specialist_auc']}`, delta `{v3['nas_us30_specialist']['delta']}`.",
        "",
        "## Task Classifications",
        "",
        "| id | status | blocker / trigger | candidate strength |",
        "| --- | --- | --- | --- |",
    ]
    for item_id in (
        "K-5",
        "K-6",
        "K-7",
        "K-8",
        "K-9",
        "K-10",
        "K-11",
        "K-12",
        "K-13",
        "K-14",
        "K-15",
        "K-18",
    ):
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
            "- `K-5` and `K-6` close as failed for the current substrate/cohort: pooled W-unit normalization did not transmit the published mechanism on MT5 retail CFD data.",
            "- `K-7` through `K-10` close as failed for the current cohort: their combined marginal lift was below noise and should not keep Lane 5 open.",
            "- `K-11`, `K-13`, `K-14`, and `K-15` are done as research/tooling components, even where their empirical gates failed.",
            "- `K-12` is deferred until sample size is high enough for the secondary classifier.",
            "- `K-18` closes as failed globally. The NAS_US30 specialist remains a K55-shadow discovery path only, not a promotion verdict.",
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
            "This artifact classifies K54-family research state only. It does not validate, promote, or modify live trading behavior.",
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

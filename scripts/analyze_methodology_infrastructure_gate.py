#!/usr/bin/env python3
"""Audit GTOS methodology infrastructure for M-7, M-12, and M-13.

Research/tooling only. This script does not create a promotion dossier and
does not validate any trading change. It verifies that current primary
research-evaluation artifacts use, or are blocked by, CPCV-honest SE,
effective-N/trial-budget accounting, and PBO guardrails.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.methodology_gate import (
    REQUIRED_HARDENING_COLUMNS,
    build_methodology_row,
    cumulative_trial_budget,
    effective_n_from_average_correlation,
    evaluate_hardened_claim,
    training_overlap_weighted_standard_error,
)


DEFAULT_OUTPUT_JSON = "research/ml_program/audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.json"
DEFAULT_OUTPUT_MD = "research/ml_program/audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md"

DSR_DIAGNOSTICS = Path("research/ml_program/audit/dsr_diagnostics.json")
K54_V2_CPCV = Path("research/ml_program/models/k54_v2/cpcv_paired_results.json")
K54_V2_PBO = Path("research/ml_program/models/k54_v2/pbo_results.json")
K54_V3_CPCV = Path("research/ml_program/models/k54_v3/cpcv_paired_results.json")
K54_V3_DSR = Path("research/ml_program/models/k54_v3/dsr_per_gate.json")
K54_V4_DSR = Path("research/ml_program/models/k54_v4/dsr_per_gate.json")
K54_V4_FINAL = Path("research/ml_program/models/k54_v4/final_verdicts.json")
Q1_DLINEAR = Path("research/ml_program/experiments/q1_dlinear_results.json")
PHASE3_DIAG = Path("research/phase_3_external_feed_validation/PHASE3_METHODOLOGY_DIAGNOSTICS_2026-05-03.json")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def dsr_row(claim_id: str) -> dict[str, Any]:
    payload = load_json(DSR_DIAGNOSTICS)
    for row in payload.get("rows") or []:
        if row.get("claim_id") == claim_id:
            return row
    return {}


def summarize_weighted_se_from_paths(paths: list[dict[str, Any]]) -> dict[str, Any]:
    diffs = [row.get("auc_diff") for row in paths if row.get("auc_diff") is not None]
    if len(diffs) < 2:
        return {"status": "not_computable", "reason": "fewer_than_two_path_diffs"}
    return {
        "status": "computed_from_path_diffs",
        **training_overlap_weighted_standard_error(diffs).to_dict(),
    }


def hardening_gate(row: dict[str, Any]) -> dict[str, Any]:
    return evaluate_hardened_claim(row)


def audit_k54_v2() -> dict[str, Any]:
    cpcv = load_json(K54_V2_CPCV)
    pbo = load_json(K54_V2_PBO)
    row = dsr_row("M-2_K54_v1")
    summary = cpcv.get("summary_fixed_hp_recommended") or {}
    weighted = summarize_weighted_se_from_paths(cpcv.get("paths_fixed_hp") or [])
    method_row = build_methodology_row(
        claim_id="k54_v2_historical_archived",
        evidence_class="historical_archived",
        methodology_status="fail",
        latest_artifact_path=str(K54_V2_CPCV),
        dsr_p=row.get("DSR_corrected_p"),
        pbo=pbo.get("pbo"),
        effective_n=row.get("effective_N"),
        not_computable_reason="historical_stouffer_epoch_artifact_not_promotion_source",
    )
    return {
        "pipeline": "K54 v2 historical modeler",
        "claim_row": method_row,
        "gate": hardening_gate(method_row),
        "stouffer_fields_present": "delong_p_combined_stouffer" in summary,
        "cpcv_honest_se_present_in_artifact": "diff_se_cpcv_honest" in summary,
        "computed_weighted_se_replacement": weighted,
        "pbo": pbo.get("pbo"),
        "dsr_p": row.get("DSR_corrected_p"),
        "effective_n": row.get("effective_N"),
        "interpretation": "Archived report contains Stouffer fields; current gate rejects it for promotion and provides weighted-SE replacement.",
    }


def audit_k54_v3() -> dict[str, Any]:
    cpcv = load_json(K54_V3_CPCV)
    dsr = load_json(K54_V3_DSR).get("gate_b_primary_lift") or {}
    summary = cpcv.get("summary") or {}
    row = dsr_row("Q1.4_K54_v3_master_bundle_lift_vs_anchor")
    method_row = build_methodology_row(
        claim_id="k54_v3_master_bundle",
        evidence_class="registered_cpcv_hypothesis",
        methodology_status="fail",
        latest_artifact_path=str(K54_V3_DSR),
        dsr_p=dsr.get("dsr_p"),
        pbo=dsr.get("pbo"),
        effective_n=row.get("effective_N"),
        not_computable_reason="DSR_and_effective_N_gates_failed",
    )
    return {
        "pipeline": "K54 v3 master bundle",
        "claim_row": method_row,
        "gate": hardening_gate(method_row),
        "stouffer_fields_present": "delong_p_combined_stouffer" in summary,
        "cpcv_honest_se_present_in_artifact": "diff_se_cpcv_honest" in summary,
        "cpcv_honest_p_two_sided": summary.get("cpcv_honest_p_two_sided"),
        "pbo": dsr.get("pbo"),
        "dsr_p": dsr.get("dsr_p"),
        "effective_n": row.get("effective_N"),
        "interpretation": "CPCV-honest SE and PBO exist; DSR/effective-N fail blocks promotion p-values.",
    }


def audit_k54_v4() -> dict[str, Any]:
    dsr = load_json(K54_V4_DSR)
    final = load_json(K54_V4_FINAL).get("verdicts") or {}
    rows = []
    for arch, payload in dsr.items():
        if not isinstance(payload, dict) or arch in {"T_paths_canonical", "ONC_eff_N"}:
            continue
        method_row = build_methodology_row(
            claim_id=f"k54_v4_{arch}",
            evidence_class="registered_cpcv_hypothesis",
            methodology_status="fail",
            latest_artifact_path=str(K54_V4_DSR),
            dsr_p=(payload.get("dsr") or {}).get("p_one_sided"),
            pbo=(payload.get("pbo") or {}).get("pbo"),
            effective_n=(payload.get("dsr") or {}).get("n_trials"),
            not_computable_reason="full_Q1_5_gate_failed_despite_some_methodology_components_passing",
        )
        rows.append(
            {
                "arch": arch,
                "claim_row": method_row,
                "gate": hardening_gate(method_row),
                "se_cpcv_honest": payload.get("se_cpcv_honest"),
                "p_cpcv_honest_two": payload.get("p_cpcv_honest_two"),
                "pbo": (payload.get("pbo") or {}).get("pbo"),
                "dsr_p": (payload.get("dsr") or {}).get("p_one_sided"),
                "effective_n": (payload.get("dsr") or {}).get("n_trials"),
                "final_verdict": (final.get(arch) or {}).get("verdict"),
                "gate_b_pass": (final.get(arch) or {}).get("gate_b_pass"),
            }
        )
    return {
        "pipeline": "K54 v4 Q1.5 dispatcher",
        "architectures_checked": len(rows),
        "rows": rows,
        "interpretation": "CPCV-honest SE, PBO, and effective-N are present; final Q1.5 gates still failed.",
    }


def audit_q1_dlinear() -> dict[str, Any]:
    payload = load_json(Q1_DLINEAR)
    effective_n = effective_n_from_average_correlation(int(payload.get("hp_grid_size") or 1), 0.5)
    method_row = build_methodology_row(
        claim_id="q1_dlinear_baseline_gate",
        evidence_class="registered_cpcv_hypothesis",
        methodology_status="fail",
        latest_artifact_path=str(Q1_DLINEAR),
        dsr_p=payload.get("DSR_p"),
        pbo=payload.get("PBO"),
        effective_n=effective_n,
        not_computable_reason="DLinear_failed_DSR_PBO_and_anchor_delta_gates",
    )
    return {
        "pipeline": "Q1 DLinear baseline",
        "claim_row": method_row,
        "gate": hardening_gate(method_row),
        "cpcv_honest_se_present_in_artifact": "cpcv_honest_SE" in payload,
        "pbo": payload.get("PBO"),
        "dsr_p": payload.get("DSR_p"),
        "effective_n_from_hp_grid_rho_0_5": effective_n,
        "verdict": payload.get("verdict"),
        "interpretation": "Registered baseline includes CPCV-honest SE, DSR, and PBO; it failed.",
    }


def audit_phase3_diagnostics() -> dict[str, Any]:
    payload = load_json(PHASE3_DIAG)
    method_row = build_methodology_row(
        claim_id="phase3_current_claims_bundle",
        evidence_class="posthoc_diagnostic",
        latest_artifact_path=str(PHASE3_DIAG),
        not_computable_reason="all_current_phase3_claims_are_discovery_or_blocked",
    )
    return {
        "pipeline": "Phase 3 claim diagnostics",
        "claim_row": method_row,
        "gate": hardening_gate(method_row),
        "claims_checked": payload.get("claim_count"),
        "promotion_p_value_allowed_claims": (payload.get("summary") or {}).get("promotion_p_value_allowed_claims"),
        "recommended_columns": (payload.get("claim_ledger_hardening") or {}).get("recommended_columns"),
        "interpretation": "Current Phase 3 diagnostics allow zero promotion p-values and require hardening columns.",
    }


def build_payload() -> dict[str, Any]:
    pipeline_audits = [
        audit_k54_v2(),
        audit_k54_v3(),
        audit_k54_v4(),
        audit_q1_dlinear(),
        audit_phase3_diagnostics(),
    ]
    trial_budget_example = cumulative_trial_budget(
        existing_program_trials=200,
        new_trials=16,
        avg_pair_correlation=0.5,
    )
    allowed = []
    for audit in pipeline_audits:
        rows = audit.get("rows") or [audit]
        for row in rows:
            claim_row = row.get("claim_row") or {}
            if claim_row.get("promotion_p_value_allowed"):
                allowed.append(claim_row.get("claim_id"))
    return {
        "schema_version": "methodology_infrastructure_gate_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "lane_1_items_addressed": ["M-7", "M-12", "M-13"],
        "hardening_columns": list(REQUIRED_HARDENING_COLUMNS),
        "summary": {
            "primary_pipelines_checked": len(pipeline_audits),
            "promotion_p_value_allowed_claims": allowed,
            "promotion_p_value_allowed_count": len(allowed),
            "m7_training_overlap_weighted_se_status": "implemented_and_audited_current_pipelines",
            "m12_effective_n_trial_counter_status": "implemented_in_research_infra",
            "m13_pbo_guard_status": "implemented_as_hardened_claim_gate_and_audited_current_pipelines",
            "trial_budget_example": trial_budget_example,
        },
        "pipeline_audits": pipeline_audits,
        "ambiguity_ledger": [
            "K54 v2 historical JSON still contains Stouffer fields; this report treats them as archived and not promotion evidence.",
            "A common gate cannot prevent a future hand-written markdown file from lying; queue control and tests must require hardened claim rows for new lift reports.",
            "Existing J46-J49/S79 validated numbers are historical references; this report is a future-claim guard and does not reopen their promotion posture.",
        ],
        "next_steps": [
            "Require new lift-claim reports to include the hardening columns emitted by src.research_infra.methodology_gate.",
            "Keep Phase 3 discovery reports at promotion_p_value_allowed=false until unseen/registered matrices exist.",
            "Use M-16 next for CPCV path bias-variance bookkeeping.",
        ],
    }


def fmt(value: Any) -> str:
    if isinstance(value, bool):
        return str(value)
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True).replace("|", r"\|")
    return str(value).replace("|", r"\|")


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return lines


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: str | Path) -> None:
    rows = []
    for audit in payload["pipeline_audits"]:
        if "rows" in audit:
            for arch_row in audit["rows"]:
                claim_row = arch_row["claim_row"]
                rows.append(
                    [
                        f"{audit['pipeline']}::{arch_row['arch']}",
                        claim_row["methodology_status"],
                        claim_row["dsr_status"],
                        claim_row["pbo_status"],
                        claim_row["effective_n_status"],
                        claim_row["promotion_p_value_allowed"],
                        arch_row.get("final_verdict"),
                    ]
                )
        else:
            claim_row = audit["claim_row"]
            rows.append(
                [
                    audit["pipeline"],
                    claim_row["methodology_status"],
                    claim_row["dsr_status"],
                    claim_row["pbo_status"],
                    claim_row["effective_n_status"],
                    claim_row["promotion_p_value_allowed"],
                    audit.get("verdict") or "n/a",
                ]
            )

    lines = [
        "# Methodology Infrastructure Gate",
        "",
        "Date: 2026-05-03",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Summary",
        "",
        f"- Lane 1 items addressed: `{payload['lane_1_items_addressed']}`.",
        f"- Primary pipelines checked: `{payload['summary']['primary_pipelines_checked']}`.",
        f"- Promotion p-values allowed: `{payload['summary']['promotion_p_value_allowed_claims']}`.",
        f"- M-7 status: `{payload['summary']['m7_training_overlap_weighted_se_status']}`.",
        f"- M-12 status: `{payload['summary']['m12_effective_n_trial_counter_status']}`.",
        f"- M-13 status: `{payload['summary']['m13_pbo_guard_status']}`.",
        "",
        "## Hardened Claim Columns",
        "",
        *[f"- `{column}`" for column in payload["hardening_columns"]],
        "",
        "## Pipeline Audit",
        "",
        *table(
            ["pipeline", "methodology", "DSR", "PBO", "effective-N", "promotion p-value allowed", "verdict"],
            rows,
        ),
        "",
        "## Trial-Budget Example",
        "",
        f"- Example cumulative trial budget: `{payload['summary']['trial_budget_example']}`.",
        "",
        "## Ambiguity Ledger",
        "",
        *[f"- {item}" for item in payload["ambiguity_ledger"]],
        "",
        "## Next Steps",
        "",
        *[f"- {item}" for item in payload["next_steps"]],
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "This report is a methodology-control artifact. It does not validate, promote, or modify live trading behavior.",
        "",
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload()
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        "pipelines={pipelines} promotion_p_values_allowed={allowed}".format(
            pipelines=payload["summary"]["primary_pipelines_checked"],
            allowed=payload["summary"]["promotion_p_value_allowed_count"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

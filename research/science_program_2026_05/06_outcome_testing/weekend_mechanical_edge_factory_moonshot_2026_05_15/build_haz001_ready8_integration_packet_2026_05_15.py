#!/usr/bin/env python3
"""Integrate HAZ001 READY8 artifacts into the weekend moonshot route."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
HAZ_DIR = REPO / "research/science_program_2026_05/06_outcome_testing/haz001_density_waiting_time_concentration_expansion_and_sealed_retest"
ADV_DIR = REPO / "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit"

HAZ_COMPLETION = HAZ_DIR / "HAZ001_COMPLETION_AUDIT_2026-05-15.json"
HAZ_VERIFICATION = HAZ_DIR / "HAZ001_VERIFICATION_RESULT_2026-05-15.json"
HAZ_G12_DECISION = HAZ_DIR / "G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_DECISION_LEDGER_2026-05-15.json"
HAZ_RETEST_DESIGN = HAZ_DIR / "HAZ001_DECONCENTRATED_RETEST_DESIGN_LEDGER_2026-05-15.json"
ADV_SYNTHESIS = ADV_DIR / "READY8_ADV_CONTROL_SYNTHESIS_2026-05-15.md"

RESULT_PATH = ROUTE_DIR / "HAZ001_READY8_INTEGRATION_PACKET_RESULT_2026-05-15.json"
BRANCH_QUEUE_PATH = ROUTE_DIR / "HAZ001_READY8_DECONCENTRATED_BRANCH_QUEUE_2026-05-15.jsonl"
BLOCKER_LEDGER_PATH = ROUTE_DIR / "HAZ001_READY8_INTEGRATION_BLOCKER_LEDGER_2026-05-15.jsonl"
SOURCE_BINDING_PATH = ROUTE_DIR / "HAZ001_READY8_SOURCE_BINDING_LEDGER_2026-05-15.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HAZ001_READY8_INTEGRATION_PACKET_SUMMARY_2026-05-15.md"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "HAZ001 READY8 integration packet only. This imports accepted no-promotion "
    "neutral target-movement artifacts and freezes retest design branches; it "
    "does not validate edge, R/PnL, expectancy, live-readiness, or promotion."
)

BLOCKERS = [
    "adv_control_overlay_required_residual_preserved_zero_for_haz001",
    "future_result_packet_required_before_any_new_target_opening",
    "neutral_target_movement_not_strategy_performance",
    "concentration_material_retest_only",
    "fail_closed_source_repairs_remain_open",
    "no_live_behavior_change_without_owner_approval",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def parse_adv_haz001_summary() -> dict[str, Any]:
    text = ADV_SYNTHESIS.read_text(encoding="utf-8", errors="replace")
    pattern = (
        r"HAZ-001: residual_preserved=(?P<residual>\d+), "
        r"fully_explained=(?P<fully>\d+), weakened=(?P<weakened>\d+), "
        r"underpowered=(?P<underpowered>\d+), not_numeric=(?P<not_numeric>\d+), "
        r"branch_rows=(?P<branch_rows>\d+), concentrated_branch_rows=(?P<concentrated>\d+)"
    )
    match = re.search(pattern, text)
    if not match:
        return {"parse_status": "NOT_FOUND"}
    values = {key: int(value) for key, value in match.groupdict().items()}
    values["parse_status"] = "FOUND"
    values["source_path"] = str(ADV_SYNTHESIS.relative_to(REPO)).replace("\\", "/")
    return values


def render_branch_rows(design: dict[str, Any], adv_summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, branch in enumerate(design.get("eligible_deconcentrated_branches") or [], 1):
        key = branch["branch_key"]
        target_family = key.get("target_family_id")
        horizon = key.get("horizon_m15_bars")
        partition = key.get("partition_assignment")
        branch_id = f"HAZ001-READY8-BRANCH-{idx:03d}"
        if (
            key.get("card_id") == "HAZ-001"
            and horizon == "32"
            and partition == "SEALED_VALIDATION_CANDIDATE_DESIGN"
            and target_family == "neutral_high_low_excursion_m15_horizons_v1"
        ):
            branch_role = "MECHANISM_ANCHOR_FROM_HAZ001_SYNTHESIS"
        elif target_family == "neutral_high_low_excursion_m15_horizons_v1":
            branch_role = "HIGH_LOW_EXCURSION_RETEST_BRANCH"
        elif target_family == "neutral_close_to_close_return_m15_horizons_v1":
            branch_role = "CLOSE_TO_CLOSE_RETEST_BRANCH"
        else:
            branch_role = "DESCRIPTOR_RETEST_BRANCH"

        rows.append(
            {
                "claim_boundary": CLAIM_BOUNDARY,
                "evidence_class": "HAZ001_READY8_DECONCENTRATED_RETEST_BRANCH_INTEGRATION",
                "branch_id": branch_id,
                "branch_role": branch_role,
                "branch_key": key,
                "comparison_id": branch.get("comparison_id"),
                "comparison_family": branch.get("comparison_family"),
                "delta": branch.get("delta"),
                "pass_unique_duplicate_denominator_count": branch.get(
                    "pass_unique_duplicate_denominator_count"
                ),
                "control_unique_duplicate_denominator_count": branch.get(
                    "control_unique_duplicate_denominator_count"
                ),
                "leave_one_survival_counts": branch.get("leave_one_survival_counts"),
                "non_evaluable_leave_one_dimension_count": branch.get(
                    "non_evaluable_leave_one_dimension_count"
                ),
                "retest_design_label": branch.get("retest_design_label"),
                "adv_control_overlay": {
                    "haz001_residual_preserved": adv_summary.get("residual"),
                    "haz001_fully_explained": adv_summary.get("fully"),
                    "haz001_underpowered": adv_summary.get("underpowered"),
                    "interpretation": (
                        "ADV control overlay means this branch remains retest design only; "
                        "current artifacts do not preserve an ADV-adjusted HAZ001 residual."
                    ),
                },
                "allowed_next_uses": [
                    "future_source_control_result_packet_design",
                    "prospective_capture_contract",
                    "failure_anatomy_monitoring",
                ],
                "forbidden_next_uses": [
                    "promotion_claim",
                    "live_filter_or_trade_rule",
                    "strategy_expectancy_claim",
                    "R_or_PnL_claim",
                ],
                "blockers": BLOCKERS,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def blocker_rows(branch_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for branch in branch_rows:
        for blocker in BLOCKERS:
            rows.append(
                {
                    "claim_boundary": CLAIM_BOUNDARY,
                    "evidence_class": "HAZ001_READY8_INTEGRATION_BLOCKER",
                    "branch_id": branch["branch_id"],
                    "blocker_id": blocker,
                    "status": "OPEN",
                    "required_resolution_before_promotion": True,
                    "safe_flags": SAFE_FLAGS,
                }
            )
    return rows


def source_binding_rows(
    completion: dict[str, Any],
    verification: dict[str, Any],
    g12: dict[str, Any],
    design: dict[str, Any],
    adv_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "claim_boundary": CLAIM_BOUNDARY,
            "evidence_class": "HAZ001_READY8_SOURCE_BINDING",
            "source_id": "HAZ_COMPLETION_AUDIT",
            "path": str(HAZ_COMPLETION.relative_to(REPO)).replace("\\", "/"),
            "status": completion.get("terminal_decision"),
            "counts": completion.get("output_counts"),
            "safe_flags": SAFE_FLAGS,
        },
        {
            "claim_boundary": CLAIM_BOUNDARY,
            "evidence_class": "HAZ001_READY8_SOURCE_BINDING",
            "source_id": "HAZ_VERIFICATION",
            "path": str(HAZ_VERIFICATION.relative_to(REPO)).replace("\\", "/"),
            "status": "ok" if verification.get("ok") else "not_ok",
            "issues": verification.get("issues"),
            "safe_flags": SAFE_FLAGS,
        },
        {
            "claim_boundary": CLAIM_BOUNDARY,
            "evidence_class": "HAZ001_READY8_SOURCE_BINDING",
            "source_id": "G12_HAZ001_DECISION",
            "path": str(HAZ_G12_DECISION.relative_to(REPO)).replace("\\", "/"),
            "status": g12.get("terminal_decision"),
            "accepted": g12.get("accepted"),
            "limitations": g12.get("limitations"),
            "safe_flags": SAFE_FLAGS,
        },
        {
            "claim_boundary": CLAIM_BOUNDARY,
            "evidence_class": "HAZ001_READY8_SOURCE_BINDING",
            "source_id": "HAZ_RETEST_DESIGN",
            "path": str(HAZ_RETEST_DESIGN.relative_to(REPO)).replace("\\", "/"),
            "eligible_deconcentrated_branch_count": design.get("eligible_deconcentrated_branch_count"),
            "design_policy": design.get("design_policy"),
            "safe_flags": SAFE_FLAGS,
        },
        {
            "claim_boundary": CLAIM_BOUNDARY,
            "evidence_class": "HAZ001_READY8_SOURCE_BINDING",
            "source_id": "READY8_ADV_CONTROL_OVERLAY",
            "path": str(ADV_SYNTHESIS.relative_to(REPO)).replace("\\", "/"),
            "haz001_adv_summary": adv_summary,
            "safe_flags": SAFE_FLAGS,
        },
    ]


def write_summary(result: dict[str, Any], role_counts: Counter[str]) -> None:
    lines = [
        "# HAZ001 READY8 Integration Packet",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, "
        "`outcome_review_opened=false`, `live_effect=false`",
        "",
        f"Evidence class: `{result['evidence_class']}`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Branch Roles", ""])
    for role, count in sorted(role_counts.items()):
        lines.append(f"- `{role}`: `{count}`")
    lines.extend(
        [
            "",
            "## Control Boundary",
            "",
            "- G12 accepts HAZ001 as neutral target-movement mechanism expansion only.",
            "- READY8 ADV overlay reports HAZ001 residual_preserved=0, so every branch remains retest design only.",
            "- No branch is an entry signal, R/PnL result, live filter, or promotion candidate.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    completion = read_json(HAZ_COMPLETION)
    verification = read_json(HAZ_VERIFICATION)
    g12 = read_json(HAZ_G12_DECISION)
    design = read_json(HAZ_RETEST_DESIGN)
    adv_summary = parse_adv_haz001_summary()

    branch_rows = render_branch_rows(design, adv_summary)
    blockers = blocker_rows(branch_rows)
    sources = source_binding_rows(completion, verification, g12, design, adv_summary)
    role_counts = Counter(row["branch_role"] for row in branch_rows)

    write_jsonl(BRANCH_QUEUE_PATH, branch_rows)
    write_jsonl(BLOCKER_LEDGER_PATH, blockers)
    write_jsonl(SOURCE_BINDING_PATH, sources)

    result = {
        "schema": "haz001_ready8_integration_packet_result_v1",
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "HAZ001_READY8_INTEGRATION_PACKET",
        "claim_boundary": CLAIM_BOUNDARY,
        "source_routes": {
            "haz001": "HAZ001_DENSITY_WAITING_TIME_CONCENTRATION_EXPANSION_AND_SEALED_RETEST",
            "g12": "G12_HAZ001_DENSITY_WAITING_TIME_MECHANISM_EXPANSION_AUDIT",
            "adv_overlay": "READY8_ADVERSARIAL_CONTROL_PLACEBO_DRIFT_AND_DUPLICATE_ARTIFACT_AUDIT_ONLY",
        },
        "counts": {
            "source_binding_rows": len(sources),
            "branch_queue_rows": len(branch_rows),
            "blocker_rows": len(blockers),
            "haz001_retest_packet_rows": completion["output_counts"]["retest_packet_rows"],
            "haz001_deconcentration_rows": completion["output_counts"]["deconcentration_rows"],
            "haz001_fail_closed_rows": completion["output_counts"]["fail_closed_rows"],
        },
        "branch_role_counts": dict(sorted(role_counts.items())),
        "adv_control_overlay": adv_summary,
        "g12_decision": g12.get("terminal_decision"),
        "haz001_verification_ok": verification.get("ok"),
        "open_blockers": BLOCKERS,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result, role_counts)
    print(json.dumps({"ok": True, "counts": result["counts"], "generated_utc": generated_utc}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

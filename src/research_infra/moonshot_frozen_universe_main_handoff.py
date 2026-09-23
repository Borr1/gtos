"""Final frozen-universe handoff helpers for main consumption."""

from __future__ import annotations

import hashlib
import json
from typing import Any


FROZEN_UNIVERSE_MAIN_HANDOFF_SURFACE = (
    "src/research_infra/moonshot_frozen_universe_main_handoff.py"
)


def research_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": "concrete_branch_local_research_boundary_v1",
        "artifact_scope": "branch_local_research",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "unconditional_scalar_use_permitted": False,
    }


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["frozen_universe_main_handoff_surface"] = FROZEN_UNIVERSE_MAIN_HANDOFF_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def stable_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def consumption_order_rows(
    cp280_handoff_rows: list[dict[str, Any]],
    cp281_artifact_paths: list[str],
) -> list[dict[str, Any]]:
    handoff_by_class = {row.get("handoff_class"): row for row in cp280_handoff_rows}
    order = [
        (
            "ready_runtime_rules_first",
            "CP281 executable ready-slice runtime rules",
            cp281_artifact_paths,
        ),
        (
            "rule_performance_evidence_second",
            "CP280 rule-performance evidence",
            handoff_by_class.get("priority_2_rule_performance", {}).get("artifact_paths") or [],
        ),
        (
            "action_execution_proof_third",
            "CP280 action/application/execution proof",
            handoff_by_class.get("priority_3_action_application", {}).get("artifact_paths") or [],
        ),
        (
            "repair_needed_bundle_fourth",
            "CP280 preserved repair-needed bundle and repair task source artifacts",
            handoff_by_class.get("priority_4_repair_tasks", {}).get("artifact_paths") or [],
        ),
        (
            "full_frozen_closure_fifth",
            "CP280 full frozen closure packet",
            handoff_by_class.get("priority_5_frozen_closure", {}).get("artifact_paths") or [],
        ),
    ]
    rows: list[dict[str, Any]] = []
    for index, (handoff_class, role, artifact_paths) in enumerate(order, start=1):
        rows.append(
            boundary_row(
                {
                    "frozen_main_consumption_order_row_id": (
                        f"FROZEN-MOONSHOT-MAIN-CONSUMPTION-{index:03d}"
                    ),
                    "priority_order": index,
                    "handoff_class": handoff_class,
                    "main_consumption_role": role,
                    "artifact_count": len(artifact_paths),
                    "artifact_paths": artifact_paths,
                    "artifact_paths_sha256": stable_sha256({"artifact_paths": artifact_paths}),
                }
            )
        )
    return rows


def count_check_row(name: str, observed: Any, expected: Any, evidence_path: str, sequence: int) -> dict[str, Any]:
    return boundary_row(
        {
            "frozen_main_handoff_count_check_row_id": (
                f"FROZEN-MOONSHOT-MAIN-HANDOFF-CHECK-{sequence:03d}"
            ),
            "check_name": name,
            "observed": observed,
            "expected": expected,
            "check_pass": observed == expected,
            "evidence_path": evidence_path,
        }
    )

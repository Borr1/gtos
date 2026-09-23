#!/usr/bin/env python3
"""Consume exact-scope final registry code specs into branch-local scorer modules."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_branch_local_denominator_exact_control_redesign_registry_scorer_modules import (
    EXACT_CONTROL_REDESIGN_REGISTRY_SCORER_MODULE_SURFACE,
    scorer_module_code_candidate,
    scorer_module_event_application,
    scorer_module_registration,
)


FINAL_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_FINAL_REGISTRY_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_REGISTRY_SCORER_MODULE_BUNDLE"

INPUT_FINAL_RESULT = ROUTE_DIR / f"{FINAL_PREFIX}_RESULT_2026-05-17.json"
INPUT_FINAL_REGISTRY = ROUTE_DIR / f"{FINAL_PREFIX}_FINAL_REGISTRY_LEDGER_2026-05-17.jsonl"
INPUT_CODE_SPEC = ROUTE_DIR / f"{FINAL_PREFIX}_CODE_SPEC_LEDGER_2026-05-17.jsonl"
INPUT_EVENT_APPLICATION = ROUTE_DIR / f"{FINAL_PREFIX}_EVENT_APPLICATION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / EXACT_CONTROL_REDESIGN_REGISTRY_SCORER_MODULE_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
MODULE_REGISTRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_MODULE_REGISTRATION_LEDGER_2026-05-17.jsonl"
EVENT_MODULE_APPLICATION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVENT_MODULE_APPLICATION_LEDGER_2026-05-17.jsonl"
CODE_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_CODE_CANDIDATE_LEDGER_2026-05-17.jsonl"
SYSTEM_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_RECOMMENDATION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local exact-control redesign registry scorer-module bundle. It consumes final exact-scope registry code "
    "specs into default-off scorer module registrations, event module applications, code candidates, and system "
    "recommendation rows. It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, "
    "win-rate, validation, live-readiness, or promotion."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except FileNotFoundError:
        return None
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        digest = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-REG-SCORER-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": digest,
                "status": "HASHED" if digest else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    row.update(
        {
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
            "live_effect": False,
        }
    )
    return row


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


def numeric_mean(values: list[Any]) -> float | None:
    numeric = []
    for value in values:
        if value is None:
            continue
        try:
            numeric.append(float(value))
        except (TypeError, ValueError):
            continue
    if not numeric:
        return None
    return round(sum(numeric) / len(numeric), 6)


def recommendation_status(family: str) -> tuple[str, str]:
    if family == "directional_context_feature_drop_target_scalar":
        return (
            "SYSTEM_RECOMMEND_DIRECTIONAL_CONTEXT_FEATURE_DEFAULT_OFF_MODULE",
            "Keep as default-off exact-scope context feature; target-delta scalar use remains disabled.",
        )
    if family == "shorter_horizon_transfer_default_off":
        return (
            "SYSTEM_RECOMMEND_SHORTER_HORIZON_TRANSFER_DEFAULT_OFF_MODULE",
            "Keep as default-off shorter-horizon transfer router; require exact-scope observation before scalar use.",
        )
    if family == "tighter_target_stress_default_off":
        return (
            "SYSTEM_RECOMMEND_TIGHTER_TARGET_STRESS_DEFAULT_OFF_MODULE",
            "Run tighter-target stress module before any target-delta scalar interpretation.",
        )
    if family == "entry_geometry_or_avoid_inverse_split_default_off":
        return (
            "SYSTEM_RECOMMEND_ENTRY_AVOID_INVERSE_SPLIT_DEFAULT_OFF_MODULE",
            "Keep entry-geometry and avoid/inverse split as default-off exact-scope module.",
        )
    return (
        "SYSTEM_RECOMMEND_ALL_REGISTRY_SCORER_MODULES_DEFAULT_OFF",
        "Preserve all module families as branch-local default-off implementation candidates.",
    )


def build_system_recommendations(
    module_rows: list[dict[str, Any]],
    event_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in module_rows:
        by_family[str(row.get("implementation_family"))].append(row)
    events_by_module: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in event_rows:
        module_id = row.get("input_registry_scorer_module_row_id")
        if module_id:
            events_by_module[str(module_id)].append(row)

    recommendations = []
    for family in sorted(by_family):
        rows = by_family[family]
        module_ids = {str(row.get("exact_control_redesign_registry_scorer_module_row_id")) for row in rows}
        family_events = [event for module_id in module_ids for event in events_by_module.get(module_id, [])]
        signal_events = [
            row
            for row in family_events
            if row.get("module_event_application_status") == "REGISTRY_SCORER_MODULE_EVENT_SIGNAL_OBSERVATION"
        ]
        control_events = [
            row
            for row in family_events
            if row.get("module_event_application_status") == "REGISTRY_SCORER_MODULE_EVENT_SAME_SCOPE_CONTROL_CONTEXT"
        ]
        status, implication = recommendation_status(family)
        recommendations.append(
            with_common(
                {
                    "system_recommendation_row_id": (
                        f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-REG-SCORER-REC-{len(recommendations) + 1:04d}"
                    ),
                    "recommendation_scope": "implementation_family",
                    "implementation_family": family,
                    "system_recommendation_status": status,
                    "system_recommendation_action": "preserve_branch_local_default_off_module_candidate",
                    "implementation_implication": implication,
                    "module_registration_rows": len(rows),
                    "signal_event_rows": len(signal_events),
                    "same_scope_control_event_rows": len(control_events),
                    "signal_alignment_rate_mean": numeric_mean(
                        [row.get("signal_alignment_rate") for row in rows]
                    ),
                    "control_alignment_rate_mean": numeric_mean(
                        [row.get("control_alignment_rate") for row in rows]
                    ),
                    "alignment_delta_mean": numeric_mean(
                        [row.get("alignment_rate_delta_signal_minus_control") for row in rows]
                    ),
                    "future_change_delta_mean": numeric_mean(
                        [row.get("future_change_mean_delta_signal_minus_control") for row in rows]
                    ),
                    "target_delta_scalar_use_allowed": False,
                    "candidate_use_allowed_now": False,
                    "runtime_score_allowed": False,
                    "unconditional_scalar_use_allowed": False,
                },
                generated_at,
                manifest_hash,
            )
        )
    status, implication = recommendation_status("ALL")
    recommendations.append(
        with_common(
            {
                "system_recommendation_row_id": (
                    f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-REG-SCORER-REC-{len(recommendations) + 1:04d}"
                ),
                "recommendation_scope": "all_registry_scorer_modules",
                "implementation_family": "ALL",
                "system_recommendation_status": status,
                "system_recommendation_action": "continue_into_cross_family_system_recommendation_merge",
                "implementation_implication": implication,
                "module_registration_rows": len(module_rows),
                "signal_event_rows": sum(
                    1
                    for row in event_rows
                    if row.get("module_event_application_status") == "REGISTRY_SCORER_MODULE_EVENT_SIGNAL_OBSERVATION"
                ),
                "same_scope_control_event_rows": sum(
                    1
                    for row in event_rows
                    if row.get("module_event_application_status")
                    == "REGISTRY_SCORER_MODULE_EVENT_SAME_SCOPE_CONTROL_CONTEXT"
                ),
                "signal_alignment_rate_mean": numeric_mean([row.get("signal_alignment_rate") for row in module_rows]),
                "control_alignment_rate_mean": numeric_mean(
                    [row.get("control_alignment_rate") for row in module_rows]
                ),
                "alignment_delta_mean": numeric_mean(
                    [row.get("alignment_rate_delta_signal_minus_control") for row in module_rows]
                ),
                "future_change_delta_mean": numeric_mean(
                    [row.get("future_change_mean_delta_signal_minus_control") for row in module_rows]
                ),
                "target_delta_scalar_use_allowed": False,
                "candidate_use_allowed_now": False,
                "runtime_score_allowed": False,
                "unconditional_scalar_use_allowed": False,
            },
            generated_at,
            manifest_hash,
        )
    )
    return recommendations


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append(
                {"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS, "not_completion": True}
            )
    manifest["latest_branch_local_denominator_exact_control_redesign_registry_scorer_module_bundle"] = {
        "artifact": PREFIX,
        "counts": result["counts"],
        "generated_utc": result["generated_utc"],
        "source_manifest_hash": result["source_manifest_hash"],
    }
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def append_sprint_ledger(result: dict[str, Any]) -> None:
    row = {
        "timestamp_utc": result["generated_utc"],
        "route": PREFIX,
        "event": "branch_local_denominator_exact_control_redesign_registry_scorer_module_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed final exact-scope registry/code specs into default-off scorer module rows, full-denominator event applications, code candidates, and system recommendation rows.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_FINAL_RESULT,
            INPUT_FINAL_REGISTRY,
            INPUT_CODE_SPEC,
            INPUT_EVENT_APPLICATION,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    final_result = read_json(INPUT_FINAL_RESULT)
    final_registry_rows = read_jsonl(INPUT_FINAL_REGISTRY)
    code_spec_rows = read_jsonl(INPUT_CODE_SPEC)
    event_application_rows = read_jsonl(INPUT_EVENT_APPLICATION)

    registry_by_id = {
        row.get("exact_control_redesign_final_registry_row_id"): row for row in final_registry_rows
    }
    code_spec_by_registry_id = {row.get("input_final_registry_row_id"): row for row in code_spec_rows}
    events_by_registry_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in event_application_rows:
        registry_id = row.get("input_final_registry_row_id")
        if registry_id:
            events_by_registry_id[str(registry_id)].append(row)

    module_registration_rows = []
    for index, registry in enumerate(final_registry_rows, 1):
        registry_id = registry.get("exact_control_redesign_final_registry_row_id")
        code_spec = code_spec_by_registry_id.get(registry_id, {})
        row = scorer_module_registration(code_spec, registry, events_by_registry_id.get(str(registry_id), []), index)
        module_registration_rows.append(with_common(row, generated_at, manifest_hash))
    module_by_registry_id = {
        row.get("input_final_registry_row_id"): row for row in module_registration_rows
    }

    event_module_application_rows = []
    for index, event in enumerate(event_application_rows, 1):
        row = scorer_module_event_application(
            event,
            module_by_registry_id.get(event.get("input_final_registry_row_id")),
        )
        row["exact_control_redesign_registry_scorer_module_event_application_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-REG-SCORER-EVENT-{index:06d}"
        )
        event_module_application_rows.append(with_common(row, generated_at, manifest_hash))

    code_candidate_rows = []
    for index, module in enumerate(module_registration_rows, 1):
        code_candidate_rows.append(with_common(scorer_module_code_candidate(module, index), generated_at, manifest_hash))

    system_recommendation_rows = build_system_recommendations(
        module_registration_rows,
        event_module_application_rows,
        generated_at,
        manifest_hash,
    )

    distributions = {
        "module_registration_status": string_counter(module_registration_rows, "module_registration_status"),
        "scorer_module_family": string_counter(module_registration_rows, "scorer_module_family"),
        "implementation_family": string_counter(module_registration_rows, "implementation_family"),
        "target_delta_use": string_counter(module_registration_rows, "target_delta_use"),
        "code_candidate_status": string_counter(code_candidate_rows, "code_candidate_status"),
        "module_event_application_status": string_counter(
            event_module_application_rows, "module_event_application_status"
        ),
        "module_event_relation": string_counter(event_module_application_rows, "module_event_relation"),
        "final_registry_event_join_state": string_counter(
            event_module_application_rows, "final_registry_event_join_state"
        ),
        "event_target_delta_use": string_counter(event_module_application_rows, "target_delta_use"),
        "system_recommendation_status": string_counter(
            system_recommendation_rows, "system_recommendation_status"
        ),
        "target_delta_scalar_use_allowed": string_counter(
            module_registration_rows + event_module_application_rows + code_candidate_rows,
            "target_delta_scalar_use_allowed",
        ),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-REG-SCORER-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    counts = {
        "input_final_registry_rows": len(final_registry_rows),
        "input_code_spec_rows": len(code_spec_rows),
        "input_event_application_rows": len(event_application_rows),
        "module_registration_rows": len(module_registration_rows),
        "event_module_application_rows": len(event_module_application_rows),
        "code_candidate_rows": len(code_candidate_rows),
        "system_recommendation_rows": len(system_recommendation_rows),
        "module_signal_event_rows": distributions["module_event_application_status"].get(
            "REGISTRY_SCORER_MODULE_EVENT_SIGNAL_OBSERVATION", 0
        ),
        "module_same_scope_control_event_rows": distributions["module_event_application_status"].get(
            "REGISTRY_SCORER_MODULE_EVENT_SAME_SCOPE_CONTROL_CONTEXT", 0
        ),
        "module_non_scope_context_event_rows": distributions["module_event_application_status"].get(
            "REGISTRY_SCORER_MODULE_EVENT_NON_SCOPE_CONTEXT", 0
        ),
        "exact_scope_joined_event_module_rows": distributions["final_registry_event_join_state"].get(
            "FINAL_RED_REGISTRY_EVENT_JOINED_EXACT_SCOPE", 0
        ),
        "exact_scope_unjoined_context_event_module_rows": distributions["final_registry_event_join_state"].get(
            "FINAL_RED_REGISTRY_EVENT_NO_EXACT_SCOPE_CONTEXT", 0
        ),
        "target_delta_negative_module_rows": distributions["target_delta_use"].get(
            "TARGET_DELTA_NEGATIVE_DO_NOT_USE_AS_SCALAR", 0
        ),
        "target_delta_negative_event_module_rows": distributions["event_target_delta_use"].get(
            "TARGET_DELTA_NEGATIVE_DO_NOT_USE_AS_SCALAR", 0
        ),
        "target_delta_null_context_event_module_rows": distributions["event_target_delta_use"].get("None", 0),
        "target_delta_scalar_disabled_rows": distributions["target_delta_scalar_use_allowed"].get("False", 0),
        "bucket_rows": len(buckets),
        "question_rows": 5,
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    questions = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-REG-SCORER-Q-001",
                "question": "Did every final registry code spec become a concrete module registration?",
                "answer_route": f"Yes: {counts['input_code_spec_rows']} code specs became {counts['module_registration_rows']} exact-scope module registrations.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-REG-SCORER-Q-002",
                "question": "Did the module layer consume the full final event denominator?",
                "answer_route": f"Yes: {counts['event_module_application_rows']} final event application rows became module event application rows.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-REG-SCORER-Q-003",
                "question": "Did any negative target-delta row become a scalar runtime score?",
                "answer_route": f"No: {counts['target_delta_scalar_disabled_rows']} module/code/event rows carry target-delta scalar use disabled.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-REG-SCORER-Q-004",
                "question": "What concrete computation did the module layer add?",
                "answer_route": "Each module registration recomputes exact-scope signal versus same-scope control alignment and future-change diagnostics from the full event application denominator.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-REG-SCORER-Q-005",
                "question": "What is the next system action?",
                "answer_route": "Merge these default-off module candidates with positive scorers, source guards, market-gap decisions, and no-fill redesign rows into a unified keep/redesign/implement system recommendation table.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "upstream_counts": {
            "denominator_exact_control_redesign_final_registry_bundle": final_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "module_registration_status_counts": distributions["module_registration_status"],
            "module_event_status_counts": distributions["module_event_application_status"],
            "code_candidate_status_counts": distributions["code_candidate_status"],
            "system_recommendation_status_counts": distributions["system_recommendation_status"],
            "target_delta_scalar_use_allowed_counts": distributions["target_delta_scalar_use_allowed"],
            "system_recommendation": "BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_REGISTRY_SCORER_MODULE_BUNDLE_RESULT: exact-scope final registry code specs now have default-off scorer module registrations, full-denominator event applications, code candidates, and family/system recommendation rows; merge into cross-family implementation decision next.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "exact_control_redesign_registry_scorer_module_surface": (
            EXACT_CONTROL_REDESIGN_REGISTRY_SCORER_MODULE_SURFACE
        ),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "target_delta_scalar_use_allowed": False,
        "module_registration_status_counts": distributions["module_registration_status"],
        "module_event_status_counts": distributions["module_event_application_status"],
        "system_recommendation_status_counts": distributions["system_recommendation_status"],
    }
    outputs = [
        MODULE_REGISTRATION_LEDGER,
        EVENT_MODULE_APPLICATION_LEDGER,
        CODE_CANDIDATE_LEDGER,
        SYSTEM_RECOMMENDATION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(MODULE_REGISTRATION_LEDGER, module_registration_rows)
    write_jsonl(EVENT_MODULE_APPLICATION_LEDGER, event_module_application_rows)
    write_jsonl(CODE_CANDIDATE_LEDGER, code_candidate_rows)
    write_jsonl(SYSTEM_RECOMMENDATION_LEDGER, system_recommendation_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Denominator Exact-Control Redesign Registry Scorer Module Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Module registrations: `{counts['module_registration_rows']}`.",
                f"- Event module applications: `{counts['event_module_application_rows']}`.",
                f"- Code candidates: `{counts['code_candidate_rows']}`.",
                f"- System recommendation rows: `{counts['system_recommendation_rows']}`.",
                f"- Signal/control/context rows: `{counts['module_signal_event_rows']}` / `{counts['module_same_scope_control_event_rows']}` / `{counts['module_non_scope_context_event_rows']}`.",
                "",
                CLAIM_BOUNDARY,
                "",
            ]
        ),
    )
    append_manifest([RESULT_PATH, SUMMARY_PATH, *outputs], result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

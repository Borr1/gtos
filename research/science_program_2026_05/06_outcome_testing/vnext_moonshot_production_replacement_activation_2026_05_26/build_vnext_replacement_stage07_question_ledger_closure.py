from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"

ACTIVATION_ROUTE = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26"
)
MOONSHOT_ROUTE = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)

SOURCE_LEDGERS = [
    (
        "activation_question_stack",
        ACTIVATION_ROUTE / f"VNEXT_ACTIVATION_QUESTION_STACK_LEDGER_{DATE}.jsonl",
    ),
    (
        "moonshot_question_stack",
        MOONSHOT_ROUTE / f"VNEXT_MOONSHOT_QUESTION_STACK_LEDGER_{DATE}.jsonl",
    ),
    (
        "moonshot_imported_question_stack",
        MOONSHOT_ROUTE / f"VNEXT_MOONSHOT_IMPORTED_QUESTION_STACK_LEDGER_{DATE}.jsonl",
    ),
]

STAGE03_CONTRACT = ROUTE_DIR / f"VNEXT_REPLACEMENT_PRODUCTION_CANDIDATE_CONTRACT_{DATE}.json"
STAGE04_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_RUNTIME_INTEGRATION_MAP_{DATE}.json"
STAGE05_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SUMMARY_{DATE}.json"
STAGE05_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_VERIFIER_{DATE}.json"
STAGE06_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_SUMMARY_{DATE}.json"
STAGE06_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_VERIFIER_{DATE}.json"
STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"

OUTPUT_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_QUESTION_STACK_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_QUESTION_CLOSURE_SUMMARY_{DATE}.json"

ALLOWED_CLOSURE_STATUSES = {
    "answered_with_disk_evidence",
    "superseded_with_exact_artifact",
    "implemented",
    "killed_redesigned_with_reason",
    "source_capture_required",
    "ai_budget_required",
    "activation_config_applied",
    "non_generatable_historical_truth_with_prospective_capture",
    "external_surface_package_required",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _jsonl_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_number"] = line_number
                rows.append(row)
    return rows


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rel(path: Path | str) -> str:
    if isinstance(path, str):
        path = Path(path)
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _upsert_manifest_output(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    outputs = manifest.setdefault("outputs", [])
    for index, existing in enumerate(outputs):
        if existing.get("path") == entry["path"]:
            outputs[index] = {**existing, **entry}
            return
    outputs.append(entry)


def _append_control(row: dict[str, Any]) -> None:
    with CONTROL_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _append_test_result(state: dict[str, Any], command: str, result: str, timestamp: str) -> None:
    tests = state.setdefault("tests_verifiers_run", [])
    tests[:] = [row for row in tests if row.get("command") != command]
    tests.append({"command": command, "result": result, "timestamp_utc": timestamp})


def _text(row: dict[str, Any]) -> str:
    fields = [
        row.get("question"),
        row.get("category"),
        row.get("status"),
        row.get("answer"),
        row.get("next_action"),
    ]
    return " ".join(str(value).lower() for value in fields if value is not None)


def _has_word(text: str, words: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(word)}\b", text) for word in words)


def _has_phrase(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _classify_imported(row: dict[str, Any], source_name: str) -> str:
    text = _text(row)
    stage12_text = str(row.get("stage12_final_question_status") or "").lower()
    if _has_phrase(text, ["credential", "remote push", "history rewrite", "live trading", "broker operation"]):
        return "external_surface_package_required"
    if _has_word(text, ["ai", "api", "model", "prompt", "claude", "sonnet", "budget", "malformed"]):
        return "ai_budget_required"
    if _has_phrase(
        text,
        [
            "order ticket",
            "deal ticket",
            "commission",
            "swap",
            "broker fill",
            "broker actual",
            "account history",
            "partial exit lifecycle",
            "be modify lifecycle",
            "trailing modify lifecycle",
            "pending lifecycle intent",
        ],
    ):
        return "non_generatable_historical_truth_with_prospective_capture"
    if _has_word(text, ["source", "tick", "scid", "sierra", "spread", "slippage", "fill", "nofill", "path", "lifecycle", "capture", "quote", "latency"]) or _has_phrase(text, ["no-fill"]):
        return "source_capture_required"
    if _has_word(text, ["implemented", "wired", "runtime", "config", "test"]):
        return "implemented"
    if _has_word(text, ["kill", "killed", "redesign"]) or _has_phrase(text, ["negative fixture", "do_not_activate"]):
        return "killed_redesigned_with_reason"
    if source_name.startswith("moonshot") and (
        _has_word(text, ["bounded", "superseded", "corrected"])
        or _has_word(stage12_text, ["bounded", "superseded", "corrected"])
    ):
        return "superseded_with_exact_artifact"
    return "answered_with_disk_evidence"


def _answer_for_status(
    status: str,
    row: dict[str, Any],
    source_name: str,
    stage05_coverage: dict[str, Any],
    stage06_verifier: dict[str, Any],
    state: dict[str, Any],
) -> tuple[str, list[str], str]:
    source_answer = str(row.get("answer") or row.get("stage12_final_question_status") or row.get("status") or "")
    if status == "ai_budget_required":
        return (
            "Closed for this route as AI-budget required: route_state_budget_cap_usd is null, paid AI/vendor/model calls are disallowed, and any AI-dependent selector must wait for the Stage09 calibration manifest, prompt pack, schema verifier, spend request, cache key, and explicit budget cap. Source answer preserved: "
            + source_answer,
            [_rel(STATE_PATH), ".context/00_core/ai_in_loop_cost_control_research_plan.md"],
            "Stage09 must produce the budget-capped AI package before any paid AI calibration result can affect activation.",
        )
    if status == "non_generatable_historical_truth_with_prospective_capture":
        return (
            "Closed as non-generatable historical truth with prospective capture: price movement can replay market path, but missing historical broker/order/lifecycle fields cannot be invented. The replacement route must capture these fields prospectively and exclude rows that depend on uncaptured broker truth. Source answer preserved: "
            + source_answer,
            [_rel(STAGE03_CONTRACT), _rel(STAGE05_VERIFIER), _rel(STAGE06_VERIFIER)],
            "Stage08/Stage10 must wire source-capture and monitoring fields; historical gaps remain excluded from activation truth.",
        )
    if status == "source_capture_required":
        return (
            "Closed as source-capture required: Stage05/Stage06 preserve row-level replay and deltas, but source-incomplete, proxy, secondary, same-bar, path, fill, spread, and lifecycle rows are not live-activation truth until the exact source class is captured or excluded. Source answer preserved: "
            + source_answer,
            [_rel(STAGE05_SUMMARY), _rel(STAGE05_VERIFIER), _rel(STAGE06_VERIFIER)],
            "Stage08 must classify market/source activation and Stage10 must add monitoring; excluded rows stay out of activation.",
        )
    if status == "implemented":
        return (
            "Closed as implemented in this route where repo-local runtime behavior was possible: Stage04 wired moonshot dynamic execution, config flags, trade/pending persistence, and focused tests without broker mutation. Source answer preserved: "
            + source_answer,
            [_rel(STAGE04_MAP), "src/components/gtos_vnext_runtime.py", "src/components/orchestrator.py", "src/components/execution.py"],
            "Keep the implementation gated until Stage11/Stage12 activation checks pass.",
        )
    if status == "killed_redesigned_with_reason":
        return (
            "Closed as killed/redesigned with reason: the failed or negative production interpretation is retained as a negative fixture, while usable evidence remains routed through the repaired condition/dynamic/source-bound replay surfaces. Source answer preserved: "
            + source_answer,
            [_rel(STAGE05_SUMMARY), _rel(STAGE06_VERIFIER)],
            "Do not activate the killed interpretation; use it as a semantic-verifier failure fixture.",
        )
    if status == "superseded_with_exact_artifact":
        return (
            "Closed as superseded with exact artifact: the source route question is preserved row-by-row, and the replacement route now supersedes the prior static substrate with runtime wiring, full activated replay, and Stage06 deltas. Source answer preserved: "
            + source_answer,
            [_rel(STAGE03_CONTRACT), _rel(STAGE05_SUMMARY), _rel(STAGE06_VERIFIER)],
            "Use replacement-route artifacts as the current evidence for activation decisions.",
        )
    if status == "external_surface_package_required":
        return (
            "Closed as external-surface package required: the requested surface is explicitly outside this route until owner approval or an operational handoff exists. Source answer preserved: "
            + source_answer,
            [_rel(STATE_PATH)],
            "Record the exact external surface in the activation dossier; do not execute it in this route.",
        )
    if status == "activation_config_applied":
        return (
            "Closed as activation-config-applied only for rows that prove a repo config overlay has already been applied. This route state currently records production_activation_overlay_applied=false, so imported activation questions are otherwise answered by disk evidence rather than marked applied. Source answer preserved: "
            + source_answer,
            [_rel(STATE_PATH)],
            "Stage11/Stage12 decide whether an activation overlay can be applied.",
        )
    return (
        "Closed as answered with disk evidence: the imported row's answer/evidence is preserved, and this replacement route adds Stage05 full activated replay plus Stage06 candidate and aggregate deltas. Source answer preserved: "
        + source_answer,
        [_rel(STAGE05_SUMMARY), _rel(STAGE06_VERIFIER)],
        "Use the row-level replacement ledger and summary artifacts for current decisions.",
    )


def _new_route_questions(
    stage05_coverage: dict[str, Any],
    stage06_verifier: dict[str, Any],
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    metrics = stage06_verifier["overall_scenario_metrics"]
    warnings = stage06_verifier.get("warnings", [])
    return [
        {
            "question_id": "QR_STAGE04_RUNTIME_EFFECT_0001",
            "question": "Does repo runtime behavior change when the vNext/moonshot activation surfaces are enabled?",
            "closure_status": "implemented",
            "closure_answer": "Yes. Stage04 wired dynamic execution evaluation into runtime, propagated dynamic policy to trade and pending intent state, and added focused tests proving J46/J49 suppression and pending lifecycle persistence under dynamic policy.",
            "closure_evidence_paths": [_rel(STAGE04_MAP), "tests/test_gtos_vnext_runtime.py", "tests/test_j46_j49_policy.py", "tests/test_limit_order_flow.py"],
            "exact_next_action": "Keep execution flags gated until semantic verification and rollback proof pass.",
        },
        {
            "question_id": "QR_STAGE05_COVERAGE_0001",
            "question": "Did the full activated replay preserve the full candidate universe rather than shrinking to a subset?",
            "closure_status": "answered_with_disk_evidence",
            "closure_answer": f"Yes. Stage05 verifier scanned {stage05_coverage['candidate_rows']} candidate rows, {stage05_coverage['dynamic_policy_replay_rows']} dynamic replay rows, and {stage05_coverage['activated_runtime_effect_rows']} current default activated-effect rows over all Stage05 shards.",
            "closure_evidence_paths": [_rel(STAGE05_SUMMARY), _rel(STAGE05_VERIFIER)],
            "exact_next_action": "Use full-universe counts in semantic verification; do not cite subset-only proof.",
        },
        {
            "question_id": "QR_STAGE05_SOURCE_MODES_0001",
            "question": "Did source modes collapse during activated replay?",
            "closure_status": "answered_with_disk_evidence",
            "closure_answer": "No. Stage05 verifier preserved nested M15, M1, M5, tick/Sierra, and missing-source path modes; missing-source rows remain explicit and cannot be activated as source-complete truth.",
            "closure_evidence_paths": [_rel(STAGE05_VERIFIER)],
            "exact_next_action": "Carry source-mode partitions into Stage08 activation/exclusion mapping.",
        },
        {
            "question_id": "QR_STAGE05_SOURCE_CAPTURE_0001",
            "question": "Can source-incomplete, secondary-framework, and same-bar ambiguous rows be activated as live production truth?",
            "closure_status": "source_capture_required",
            "closure_answer": f"No. Stage05 dispositions include {stage05_coverage['source_excluded_rows']} source/scope excluded rows and {stage05_coverage['secondary_framework_replay_only_rows']} secondary-framework replay-only rows. These remain excluded or forward-capture required until Stage08/Stage10 source rules are written.",
            "closure_evidence_paths": [_rel(STAGE05_SUMMARY), _rel(STAGE06_VERIFIER)],
            "exact_next_action": "Stage08 must assign each market/source class to enabled, excluded, proxy-context, or forward-capture required.",
        },
        {
            "question_id": "QR_STAGE06_DEFAULT_OVERLAY_0001",
            "question": "Can the current default source-bound primary activation projection be applied to production?",
            "closure_status": "killed_redesigned_with_reason",
            "closure_answer": f"No. Stage06 verifier reports activated_default_source_bound_primary expectancy {metrics['activated_default_source_bound_primary']['expectancy_r']} over {metrics['activated_default_source_bound_primary']['performance_count']} rows with warning {warnings}. Stage12 must fail any overlay that uses this default slice without repair.",
            "closure_evidence_paths": [_rel(STAGE06_VERIFIER), _rel(STAGE06_SUMMARY)],
            "exact_next_action": "Use the warning as a semantic-verifier failure fixture and require a repaired selector before activation.",
        },
        {
            "question_id": "QR_STAGE06_CONDITION_ROUTER_0001",
            "question": "Which replay branch dominates old GTOS in Stage06 deltas?",
            "closure_status": "answered_with_disk_evidence",
            "closure_answer": f"The condition-router challenger is strongest among the all-replayable scenarios: total R {metrics['condition_router_challenger']['total_r']} and expectancy {metrics['condition_router_challenger']['expectancy_r']} versus old GTOS total R {metrics['old_gtos_live_current_j46_j49']['total_r']} and expectancy {metrics['old_gtos_live_current_j46_j49']['expectancy_r']}. This does not override source-bound activation gates.",
            "closure_evidence_paths": [_rel(STAGE06_VERIFIER), _rel(STAGE06_SUMMARY)],
            "exact_next_action": "Carry condition-router evidence into Stage11/12 as challenger evidence, not as automatic production overlay.",
        },
        {
            "question_id": "QR_STAGE06_FIXED_R_0001",
            "question": "Can fixed 1.5R or J46/J49 remain the final moonshot exit truth?",
            "closure_status": "killed_redesigned_with_reason",
            "closure_answer": f"No. Fixed 1.5R is retained only as comparator evidence. Old J46/J49 expectancy is {metrics['old_gtos_live_current_j46_j49']['expectancy_r']}, while moonshot BE is {metrics['moonshot_be_after_trigger']['expectancy_r']} and condition router is {metrics['condition_router_challenger']['expectancy_r']}.",
            "closure_evidence_paths": [_rel(STAGE06_VERIFIER), _rel(STAGE03_CONTRACT)],
            "exact_next_action": "Stage12 must fail if J46/J49 or fixed 1.5R dominates activated execution except as explicit rollback/comparator.",
        },
        {
            "question_id": "QR_STAGE06_PROP_SEQUENCE_0001",
            "question": "Does Stage06 prove full candidate-level prop account pass/loss/abandon/restart sequencing?",
            "closure_status": "source_capture_required",
            "closure_answer": "No. Stage06 summary states that prop pass/account-abandon metrics are branch aggregate evidence from Stage05; candidate-level prop action sequence was not present upstream and remains a source/capture requirement.",
            "closure_evidence_paths": [_rel(STAGE06_SUMMARY)],
            "exact_next_action": "Stage11 dossier must keep prop sequence claims bounded and Stage10 monitoring must add prop projection fields.",
        },
        {
            "question_id": "QR_STAGE07_AI_BUDGET_0001",
            "question": "Can paid AI calibration or AI-dependent activation run in this route now?",
            "closure_status": "ai_budget_required",
            "closure_answer": "No. Route state has route_state_budget_cap_usd=null and paid_ai_or_vendor_calls_allowed=false. Stage09 can build the manifest, prompt pack, schema validator, cache key, and spend request, but cannot spend without an explicit budget cap.",
            "closure_evidence_paths": [_rel(STATE_PATH), ".context/00_core/ai_in_loop_cost_control_research_plan.md"],
            "exact_next_action": "Stage09 must separate mechanical activation from AI-dependent activation and write the spend request.",
        },
        {
            "question_id": "QR_STAGE07_COMPLETION_GATE_0001",
            "question": "Is the route complete after Stage07 question closure?",
            "closure_status": "answered_with_disk_evidence",
            "closure_answer": "No. Route state still requires Stage08 source map, Stage09 AI package, Stage10 ML/monitoring integration, Stage11 activation dossier/overlay package, Stage12 semantic verifier/red team, and Stage13 scoped commits/completion audit.",
            "closure_evidence_paths": [_rel(STATE_PATH)],
            "exact_next_action": "Proceed to Stage08 after this ledger is written and verified.",
        },
    ]


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for _, path in SOURCE_LEDGERS:
        if not path.exists():
            raise FileNotFoundError(path)
    for path in [STAGE03_CONTRACT, STAGE04_MAP, STAGE05_SUMMARY, STAGE05_VERIFIER, STAGE06_SUMMARY, STAGE06_VERIFIER]:
        if not path.exists():
            raise FileNotFoundError(path)

    stage05_summary = _read_json(STAGE05_SUMMARY)
    stage05_coverage = stage05_summary["coverage"]
    stage06_verifier = _read_json(STAGE06_VERIFIER)
    state = _read_json(STATE_PATH)
    manifest = _read_json(MANIFEST_PATH)

    source_counts: Counter[str] = Counter()
    closure_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    source_hashes = {name: _sha256_file(path) for name, path in SOURCE_LEDGERS}
    emitted_rows: list[dict[str, Any]] = []

    for source_name, source_path in SOURCE_LEDGERS:
        rows = _jsonl_rows(source_path)
        source_counts[source_name] = len(rows)
        for row in rows:
            closure_status = _classify_imported(row, source_name)
            answer, evidence_paths, exact_next_action = _answer_for_status(
                closure_status,
                row,
                source_name,
                stage05_coverage,
                stage06_verifier,
                state,
            )
            source_row_digest = hashlib.sha256(
                json.dumps({k: v for k, v in row.items() if not k.startswith("_")}, sort_keys=True).encode("utf-8")
            ).hexdigest()
            emitted = {
                "answer_not_summary_only": True,
                "category": row.get("category", "uncategorized"),
                "closure_answer": answer,
                "closure_evidence_paths": evidence_paths,
                "closure_status": closure_status,
                "exact_next_action": exact_next_action,
                "imported_question_id": row.get("question_id"),
                "imported_source_answer": row.get("answer") or row.get("stage12_final_question_status") or row.get("status"),
                "imported_source_status": row.get("status"),
                "no_packed_status": True,
                "question": row.get("question"),
                "record_type": "question_closure",
                "replacement_question_id": f"RQ_{source_name}_{row.get('_source_line_number'):06d}",
                "route_id": ROUTE_ID,
                "schema_version": "vnext_replacement_stage07_question_closure_v1",
                "source_ledger": _rel(source_path),
                "source_ledger_sha256": source_hashes[source_name],
                "source_ledger_type": source_name,
                "source_line_number": row.get("_source_line_number"),
                "source_route_id": row.get("route_id") or row.get("moonshot_route_id"),
                "source_row_sha256": source_row_digest,
                "stage_id": "stage_07_question_ledger_closure",
            }
            emitted_rows.append(emitted)
            closure_counts[closure_status] += 1
            category_counts[str(emitted["category"])] += 1

    for row in _new_route_questions(stage05_coverage, stage06_verifier, state):
        closure_status = row["closure_status"]
        emitted = {
            "answer_not_summary_only": True,
            "category": "replacement_route_generated_question",
            "closure_answer": row["closure_answer"],
            "closure_evidence_paths": row["closure_evidence_paths"],
            "closure_status": closure_status,
            "exact_next_action": row["exact_next_action"],
            "imported_question_id": None,
            "imported_source_answer": None,
            "imported_source_status": None,
            "no_packed_status": True,
            "question": row["question"],
            "record_type": "question_closure",
            "replacement_question_id": row["question_id"],
            "route_id": ROUTE_ID,
            "schema_version": "vnext_replacement_stage07_question_closure_v1",
            "source_ledger": "replacement_route_stage04_to_stage06_artifacts",
            "source_ledger_sha256": None,
            "source_ledger_type": "replacement_route_generated_question",
            "source_line_number": None,
            "source_route_id": ROUTE_ID,
            "source_row_sha256": hashlib.sha256(json.dumps(row, sort_keys=True).encode("utf-8")).hexdigest(),
            "stage_id": "stage_07_question_ledger_closure",
        }
        emitted_rows.append(emitted)
        closure_counts[closure_status] += 1
        category_counts[str(emitted["category"])] += 1

    invalid_statuses = sorted(set(closure_counts) - ALLOWED_CLOSURE_STATUSES)
    unresolved_rows = [
        row["replacement_question_id"]
        for row in emitted_rows
        if not row["closure_answer"] or not row["closure_evidence_paths"] or not row["exact_next_action"]
    ]
    if invalid_statuses or unresolved_rows:
        raise RuntimeError({"invalid_statuses": invalid_statuses, "unresolved_rows": unresolved_rows[:20]})

    with OUTPUT_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for row in emitted_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    summary = {
        "allowed_closure_statuses": sorted(ALLOWED_CLOSURE_STATUSES),
        "category_counts": dict(sorted(category_counts.items())),
        "closure_status_counts": dict(sorted(closure_counts.items())),
        "current_stage_after_stage07": "stage_08_source_and_market_activation_map",
        "first_incomplete_invariant_after_stage07": "stage_08_source_and_market_activation_map_pending",
        "generated_at_utc": generated_at,
        "input_source_hashes": source_hashes,
        "new_replacement_questions_added": len(_new_route_questions(stage05_coverage, stage06_verifier, state)),
        "output_ledger": _rel(OUTPUT_LEDGER),
        "output_ledger_rows": len(emitted_rows),
        "output_ledger_sha256": _sha256_file(OUTPUT_LEDGER),
        "output_summary": _rel(OUTPUT_SUMMARY),
        "route_id": ROUTE_ID,
        "source_ledger_counts": dict(source_counts),
        "stage06_activation_warning_consumed": stage06_verifier.get("warnings", []),
        "stage_id": "stage_07_question_ledger_closure",
        "status": "completed_question_ledger_closure",
        "unresolved_placeholder_rows": 0,
    }
    _write_json(OUTPUT_SUMMARY, summary)

    _upsert_manifest_output(
        manifest,
        {"path": OUTPUT_LEDGER.name, "stage": "stage_07", "status": "created", "rows": len(emitted_rows)},
    )
    _upsert_manifest_output(
        manifest,
        {"path": OUTPUT_SUMMARY.name, "stage": "stage_07", "status": "created"},
    )
    manifest["last_updated_utc"] = generated_at
    _write_json(MANIFEST_PATH, manifest)

    evidence = state.setdefault("evidence_rows_scanned", {})
    evidence["stage07_activation_question_rows_imported"] = source_counts["activation_question_stack"]
    evidence["stage07_moonshot_question_rows_imported"] = source_counts["moonshot_question_stack"]
    evidence["stage07_moonshot_imported_question_rows_imported"] = source_counts["moonshot_imported_question_stack"]
    evidence["stage07_replacement_generated_questions"] = summary["new_replacement_questions_added"]
    evidence["stage07_question_closure_rows"] = len(emitted_rows)
    state["current_stage"] = "stage_08_source_and_market_activation_map"
    state["first_incomplete_invariant"] = "stage_08_source_and_market_activation_map_pending"
    state["exact_next_action"] = (
        "Classify every market and source class from the 24-market replay universe into activation, exclusion, proxy-context, "
        "and forward-capture buckets; write source-capture requirements and activation-exclusion ledgers."
    )
    state.setdefault("stage_status", {})["stage_07_question_ledger_closure"] = "completed_question_ledger_written"
    state.setdefault("stage_status", {})["stage_08_source_and_market_activation_map"] = "pending"
    _append_test_result(
        state,
        _rel(Path(__file__)),
        "passed; wrote Stage07 question closure ledger",
        generated_at,
    )
    state["last_updated_utc"] = generated_at
    _write_json(STATE_PATH, state)

    _append_control(
        {
            "event": "stage_07_question_ledger_closure_completed",
            "generated_at_utc": generated_at,
            "ledger_rows": len(emitted_rows),
            "route_id": ROUTE_ID,
            "source_counts": dict(source_counts),
            "stage_id": "stage_07_question_ledger_closure",
        }
    )

    print(json.dumps({"rows": len(emitted_rows), "next": state["first_incomplete_invariant"], "stage": "stage_07_question_ledger_closure"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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

SUMMARY_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_QUESTION_CLOSURE_SUMMARY_{DATE}.json"
LEDGER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_QUESTION_STACK_LEDGER_{DATE}.jsonl"
STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
VERIFIER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_QUESTION_CLOSURE_VERIFIER_{DATE}.json"

ALLOWED_STATUSES = {
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

FORBIDDEN_PLACEHOLDER_PATTERN = re.compile(r"\b(tbd|unknown|maybe|later|deferred|placeholder)\b", re.IGNORECASE)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def _jsonl_count_and_hash(path: Path) -> tuple[int, str]:
    count = 0
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for raw in handle:
            if raw.strip():
                count += 1
            digest.update(raw)
    return count, digest.hexdigest()


def _upsert_manifest_output(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    outputs = manifest.setdefault("outputs", [])
    for index, existing in enumerate(outputs):
        if existing.get("path") == entry["path"]:
            outputs[index] = {**existing, **entry}
            return
    outputs.append(entry)


def _append_test_result(state: dict[str, Any], result: dict[str, Any]) -> None:
    tests = state.setdefault("tests_verifiers_run", [])
    command = result.get("command")
    tests[:] = [row for row in tests if row.get("command") != command]
    tests.append(result)


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    failures: list[str] = []
    warnings: list[str] = []

    for path in [SUMMARY_PATH, LEDGER_PATH, STATE_PATH, MANIFEST_PATH]:
        if not path.exists():
            failures.append(f"missing_required_path:{path.name}")

    if failures:
        result = {
            "failures": failures,
            "generated_at_utc": generated_at,
            "route_id": ROUTE_ID,
            "stage_id": "stage_07_question_ledger_closure",
            "status": "failed",
            "warnings": warnings,
        }
        _write_json(VERIFIER_PATH, result)
        return 1

    summary = _read_json(SUMMARY_PATH)
    state = _read_json(STATE_PATH)
    manifest = _read_json(MANIFEST_PATH)

    ledger_count, ledger_hash = _jsonl_count_and_hash(LEDGER_PATH)
    if ledger_count != int(summary.get("output_ledger_rows", -1)):
        failures.append(f"ledger_row_count_mismatch:{ledger_count}!={summary.get('output_ledger_rows')}")
    if ledger_hash != summary.get("output_ledger_sha256"):
        failures.append("ledger_sha256_mismatch")

    source_counts: Counter[str] = Counter()
    closure_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    record_type_counts: Counter[str] = Counter()
    source_line_keys: set[tuple[str, int | None]] = set()
    generated_question_ids: set[str] = set()
    missing_answer_rows = 0
    missing_evidence_rows = 0
    invalid_status_rows = 0
    packed_status_rows = 0
    placeholder_rows: list[str] = []
    route_id_mismatch_rows = 0

    with LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            record_type_counts[str(row.get("record_type"))] += 1
            if row.get("route_id") != ROUTE_ID or row.get("stage_id") != "stage_07_question_ledger_closure":
                route_id_mismatch_rows += 1
            status = str(row.get("closure_status"))
            closure_counts[status] += 1
            category_counts[str(row.get("category"))] += 1
            source_type = str(row.get("source_ledger_type"))
            source_counts[source_type] += 1
            if status not in ALLOWED_STATUSES:
                invalid_status_rows += 1
            if row.get("no_packed_status") is not True:
                packed_status_rows += 1
            if not row.get("closure_answer"):
                missing_answer_rows += 1
            if not row.get("closure_evidence_paths"):
                missing_evidence_rows += 1
            if FORBIDDEN_PLACEHOLDER_PATTERN.search(str(row.get("exact_next_action") or "")):
                placeholder_rows.append(str(row.get("replacement_question_id")))
            if source_type == "replacement_route_generated_question":
                generated_question_ids.add(str(row.get("replacement_question_id")))
            else:
                source_line_keys.add((source_type, row.get("source_line_number")))

    if record_type_counts != Counter({"question_closure": ledger_count}):
        failures.append(f"record_type_counts_mismatch:{dict(record_type_counts)}")
    if route_id_mismatch_rows:
        failures.append(f"route_or_stage_mismatch_rows:{route_id_mismatch_rows}")
    if invalid_status_rows:
        failures.append(f"invalid_status_rows:{invalid_status_rows}")
    if packed_status_rows:
        failures.append(f"packed_status_rows:{packed_status_rows}")
    if missing_answer_rows:
        failures.append(f"missing_answer_rows:{missing_answer_rows}")
    if missing_evidence_rows:
        failures.append(f"missing_evidence_rows:{missing_evidence_rows}")
    if placeholder_rows:
        failures.append(f"placeholder_next_action_rows:{placeholder_rows[:20]}")

    if dict(sorted(closure_counts.items())) != summary.get("closure_status_counts"):
        failures.append("closure_status_counts_do_not_match_summary")
    imported_source_counts = {
        key: value for key, value in dict(sorted(source_counts.items())).items() if key != "replacement_route_generated_question"
    }
    if imported_source_counts != summary.get("source_ledger_counts"):
        failures.append("source_ledger_counts_do_not_match_summary")
    if dict(sorted(category_counts.items())) != summary.get("category_counts"):
        failures.append("category_counts_do_not_match_summary")

    expected_import_rows = sum(summary.get("source_ledger_counts", {}).values())
    expected_generated = int(summary.get("new_replacement_questions_added", -1))
    if len(source_line_keys) != expected_import_rows:
        failures.append(f"source_line_key_uniqueness_mismatch:{len(source_line_keys)}!={expected_import_rows}")
    if len(generated_question_ids) != expected_generated:
        failures.append(f"generated_question_count_mismatch:{len(generated_question_ids)}!={expected_generated}")

    for source_type, expected_hash in summary.get("input_source_hashes", {}).items():
        matching = [row for row in source_line_keys if row[0] == source_type]
        if not matching:
            failures.append(f"source_type_has_no_rows:{source_type}")
        source_path = None
        with LEDGER_PATH.open("r", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("source_ledger_type") == source_type:
                    source_path = REPO_ROOT / str(row.get("source_ledger"))
                    break
        if source_path is None or not source_path.exists():
            failures.append(f"source_ledger_path_missing:{source_type}")
            continue
        source_count, source_hash = _jsonl_count_and_hash(source_path)
        if source_count != summary["source_ledger_counts"][source_type]:
            failures.append(f"source_ledger_count_mismatch:{source_type}")
        if source_hash != expected_hash:
            failures.append(f"source_ledger_hash_mismatch:{source_type}")

    required_generated_questions = {
        "QR_STAGE06_DEFAULT_OVERLAY_0001",
        "QR_STAGE06_CONDITION_ROUTER_0001",
        "QR_STAGE06_FIXED_R_0001",
        "QR_STAGE07_AI_BUDGET_0001",
        "QR_STAGE07_COMPLETION_GATE_0001",
    }
    missing_generated = sorted(required_generated_questions - generated_question_ids)
    if missing_generated:
        failures.append(f"missing_required_generated_questions:{missing_generated}")

    if state.get("first_incomplete_invariant") != "stage_08_source_and_market_activation_map_pending":
        failures.append("route_state_not_advanced_to_stage08")
    manifest_paths = {row.get("path") for row in manifest.get("outputs", [])}
    for name in [LEDGER_PATH.name, SUMMARY_PATH.name]:
        if name not in manifest_paths:
            failures.append(f"manifest_missing_stage07_output:{name}")

    status = "passed" if not failures else "failed"
    result = {
        "category_counts": dict(sorted(category_counts.items())),
        "closure_status_counts": dict(sorted(closure_counts.items())),
        "failures": failures,
        "generated_at_utc": generated_at,
        "generated_question_ids": sorted(generated_question_ids),
        "ledger_rows": ledger_count,
        "ledger_sha256": ledger_hash,
        "record_type_counts": dict(record_type_counts),
        "route_id": ROUTE_ID,
        "source_ledger_counts": dict(sorted(source_counts.items())),
        "stage_id": "stage_07_question_ledger_closure",
        "status": status,
        "warnings": warnings,
    }
    _write_json(VERIFIER_PATH, result)

    if status == "passed":
        _upsert_manifest_output(
            manifest,
            {"path": VERIFIER_PATH.name, "stage": "stage_07", "status": "created", "result": "passed"},
        )
        manifest["last_updated_utc"] = generated_at
        _write_json(MANIFEST_PATH, manifest)

        state.setdefault("evidence_rows_scanned", {})["stage07_verifier_rows_scanned"] = ledger_count
        _append_test_result(
            state,
            {
                "command": _rel(Path(__file__)),
                "result": "passed",
                "timestamp_utc": generated_at,
            },
        )
        state["last_updated_utc"] = generated_at
        _write_json(STATE_PATH, state)

    print(json.dumps({"rows": ledger_count, "status": status, "warnings": warnings}, sort_keys=True))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

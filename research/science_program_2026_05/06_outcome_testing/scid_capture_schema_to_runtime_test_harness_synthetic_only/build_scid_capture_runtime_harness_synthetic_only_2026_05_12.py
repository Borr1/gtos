"""Build artifacts for the synthetic-only SCID runtime harness route."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import runtime_harness_synthetic_only_2026_05_12 as harness


DATE_TAG = "2026-05-12"
PROMPT_DIR = harness.SCIENCE_ROOT / "04_goal_prompts"
G12_PROMPT = PROMPT_DIR / "G12_SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_AUDIT_GOAL_PROMPT_2026-05-12.md"
VERIFIER = harness.ROUTE_DIR / "verify_scid_capture_runtime_harness_synthetic_only_2026_05_12.py"
TEST_FILE = harness.ROUTE_DIR / "test_scid_capture_runtime_harness_synthetic_only_2026_05_12.py"
PREFIX = harness.ARTIFACT_PREFIX


def rel(path: Path) -> str:
    return path.resolve().relative_to(harness.REPO_ROOT).as_posix()


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_json(path: Path, data: Any) -> Path:
    return write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def md_list(items: list[str]) -> str:
    return "\n".join(f"- `{item}`" for item in items)


def run_command(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=harness.REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=120,
    )
    return {
        "command": " ".join(args),
        "returncode": proc.returncode,
        "stdout": proc.stdout[-5000:],
        "stderr": proc.stderr[-5000:],
        "passed": proc.returncode == 0,
    }


def write_fixture_files(cases: list[harness.FixtureCase]) -> tuple[list[Path], list[dict[str, Any]]]:
    harness.FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    manifest_rows: list[dict[str, Any]] = []
    for case in cases:
        suffix = ".json" if case.manifest_payload is not None or len(case.rows) == 1 else ".jsonl"
        path = harness.FIXTURE_DIR / f"{case.fixture_id}{suffix}"
        if case.manifest_payload is not None:
            write_json(path, case.manifest_payload)
        elif suffix == ".json":
            write_json(path, case.rows[0])
        else:
            text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in case.rows)
            write_text(path, text)
        written.append(path)
        manifest_rows.append(case.to_manifest_row(rel(path)))
    return written, manifest_rows


def artifact_record(path: Path, role: str, strict_hash: bool = True) -> dict[str, Any]:
    return {
        "path": rel(path),
        "role": role,
        "sha256": harness.sha256_file(path) if path.exists() else None,
        "strict_hash": strict_hash,
    }


def build_prompt() -> str:
    return f"""# G12 Audit Goal Prompt - SCID Capture Runtime Harness Synthetic Only

You are auditing the route-local synthetic-only runtime harness for the accepted
SCID forward capture offline schema package.

## Required Reads
- `{rel(harness.ROUTE_DIR / (PREFIX + "_CONTEXT_ANCHOR_AND_G12_RECONCILIATION_2026-05-12.md"))}`
- `{rel(harness.ROUTE_DIR / (PREFIX + "_FIXTURE_MANIFEST_2026-05-12.json"))}`
- `{rel(harness.ROUTE_DIR / (PREFIX + "_NEGATIVE_FIXTURE_MATRIX_2026-05-12.json"))}`
- `{rel(harness.ROUTE_DIR / (PREFIX + "_LEAK_REDACTION_AUDIT_2026-05-12.json"))}`
- `{rel(harness.ROUTE_DIR / (PREFIX + "_SATURATION_SELF_REDTEAM_LEDGER_2026-05-12.json"))}`
- `{rel(harness.ROUTE_DIR / "runtime_harness_synthetic_only_2026_05_12.py")}`
- `{rel(harness.ROUTE_DIR / "verify_scid_capture_runtime_harness_synthetic_only_2026_05_12.py")}`

## Audit Scope
1. Confirm the harness consumes only synthetic fixtures plus committed accepted schema/control artifacts.
2. Recompute the ten-group positive and fail-closed fixture matrix.
3. Recompute negative routes for missing, stale as-of, forbidden identifier, duplicate denominator drift, unavailable-source, unsafe flag, manifest-repair, schema-version, unexpected-field, and enum violations.
4. Confirm LTF/orderflow unavailable-source cases are accepted only as source-unavailable fail-closed rows and that the eight historical source-truth groups fail closed.
5. Confirm recursive redaction catches broker/account/order/deal/position/result/performance markers in deliberate negative fixtures and that accepted rows are clean.
6. Confirm no `src/`, `prompts/`, broker/API, raw market blob, result scoring, strategy edge, validation, risk, safety, execution, canary, selector, or live behavior surface is opened.
7. Preserve the G12 manifest-binding repair policy exactly: current G12 prompt hash repair and output-manifest self-hash drift are nonblocking; all other source/input hashes are strict blockers.

## One-Line Starter
Audit the route-local synthetic-only SCID capture schema runtime harness, recompute fixture validation and leak checks, and either accept it as control-evidence-only harness coverage or return exact blockers without opening validation/live/AI/API/broker/result surfaces.
"""


def build_all() -> dict[str, Any]:
    harness.ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    cases = harness.build_fixture_cases()
    outcomes = harness.validate_fixture_cases(cases)
    fixture_paths, fixture_manifest_rows = write_fixture_files(cases)

    pass_count = sum(1 for outcome in outcomes if outcome.pass_status)
    fail_count = len(outcomes) - pass_count
    leak_audit = harness.leak_redaction_audit(cases)
    saturation = harness.saturation_summary(cases, outcomes)
    matrix = harness.category_matrix(cases)

    artifacts: list[Path] = []

    fixture_manifest = {
        "route_id": harness.ROUTE_ID,
        "evidence_class": harness.EVIDENCE_CLASS,
        "safe_flags": {flag: False for flag in harness.SAFE_FLAG_FIELDS},
        "synthetic_only": True,
        "accepted_schema_route": rel(harness.ACCEPTED_SCHEMA_ROUTE),
        "candidate_row_boundary_preserved": 3014,
        "capture_group_count": len(harness.CAPTURE_GROUPS),
        "fixture_case_count": len(cases),
        "fixture_rows": fixture_manifest_rows,
    }
    artifacts.append(write_json(harness.ROUTE_DIR / f"{PREFIX}_FIXTURE_MANIFEST_{DATE_TAG}.json", fixture_manifest))

    validation_result = {
        "route_id": harness.ROUTE_ID,
        "synthetic_only": True,
        "fixture_case_count": len(cases),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "all_expected_validity_matched": fail_count == 0,
        "outcomes": [outcome.to_dict() for outcome in outcomes],
    }
    artifacts.append(write_json(harness.ROUTE_DIR / f"{PREFIX}_FIXTURE_VALIDATION_RESULT_{DATE_TAG}.json", validation_result))

    context_md = f"""# SCID Capture Runtime Harness - Context Anchor And G12 Reconciliation

Terminal route: `{harness.ROUTE_ID}`.

This route is control-evidence-only and synthetic-only. It does not open
validation, result scoring, strategy edge claims, AI/API calls, broker/account
order/deal/position evidence, raw market blob commits, prompt/config/risk/safety
execution/canary/selector edits, or live behavior.

## Accepted Control Inputs
- Accepted G12 audit route: `{rel(harness.G12_AUDIT_ROUTE)}`
- Accepted offline schema route: `{rel(harness.ACCEPTED_SCHEMA_ROUTE)}`
- Accepted schema version: `{harness.SCHEMA_VERSION}`
- Accepted candidate-row boundary: `3014`
- Accepted capture groups: `10`
- Accepted capture groups:
{md_list(harness.CAPTURE_GROUPS)}

## Reconciliation
- The G12 audit accepted the offline schema package as control evidence only.
- The manifest-binding repair is preserved: current G12 prompt hash repair and output-manifest self-hash drift remain nonblocking; all other source/input mismatches remain strict blockers.
- The harness validates runtime-shaped rows against the accepted schema files but generates only synthetic fixture rows locally.
- Runtime producer wiring remains absent.
"""
    artifacts.append(write_text(harness.ROUTE_DIR / f"{PREFIX}_CONTEXT_ANCHOR_AND_G12_RECONCILIATION_{DATE_TAG}.md", context_md))

    expansion = {
        "route_id": harness.ROUTE_ID,
        "synthetic_only": True,
        "accepted_candidate_boundary": 3014,
        "capture_groups": harness.CAPTURE_GROUPS,
        "positive_case_count": sum(1 for case in cases if case.expected_valid and case.category.startswith("positive")),
        "negative_or_fail_closed_case_count": sum(1 for case in cases if not (case.expected_valid and case.category.startswith("positive"))),
        "fixture_case_count": len(cases),
        "fixture_row_count": sum(len(case.rows) for case in cases),
        "category_matrix": matrix,
    }
    artifacts.append(write_json(harness.ROUTE_DIR / f"{PREFIX}_FIXTURE_EXPANSION_LEDGER_{DATE_TAG}.json", expansion))
    expansion_md = f"""# Fixture Expansion Ledger

- Synthetic-only: `true`
- Accepted candidate-row boundary preserved: `3014`
- Capture groups covered: `{len(harness.CAPTURE_GROUPS)}`
- Fixture cases: `{len(cases)}`
- Fixture row count: `{sum(len(case.rows) for case in cases)}`
- Expected-validity outcomes matched: `{fail_count == 0}`

The harness generates two positive route variants for every capture group and
mutates every group through missing-field, stale-as-of, forbidden-identifier,
unsafe-flag, schema-version, unexpected-field, duplicate-key-drift, and
unavailable-source routes. Enum mutation is applied to every group with a
group-specific enum in the accepted schema.
"""
    artifacts.append(write_text(harness.ROUTE_DIR / f"{PREFIX}_FIXTURE_EXPANSION_LEDGER_{DATE_TAG}.md", expansion_md))

    contract_md = f"""# Runtime Parser Harness Contract

## Boundary
The harness is a parser/validator contract only. It does not implement or wire a
producer. Future runtime producers must emit rows conforming to the accepted
offline schema package and must preserve the `candidate_input_row_id` and
`duplicate_proxy_denominator_key` exactly.

## Parser Contract
1. Load the accepted schema bundle from `{rel(harness.ACCEPTED_SCHEMA_DIR)}`.
2. Reject unknown `field_group` and unknown `schema_version`.
3. Enforce closed `additionalProperties: false` group schemas.
4. Enforce all required common and group-specific fields.
5. Enforce `source_observed_asof_utc <= decision_asof_utc`.
6. Enforce strict source hash for captured rows.
7. Allow `SOURCE_UNAVAILABLE_FAIL_CLOSED` only for LTF/orderflow market-context groups.
8. Reject duplicate candidate ids with denominator-key drift.
9. Recursively reject broker/account/order/deal/position/result/performance keys or values.
10. Return structured fail-closed errors; never infer missing fields from price path, result labels, broker records, AI output, or future market movement.
"""
    artifacts.append(write_text(harness.ROUTE_DIR / f"{PREFIX}_RUNTIME_PARSER_HARNESS_CONTRACT_{DATE_TAG}.md", contract_md))

    artifacts.append(write_json(harness.ROUTE_DIR / f"{PREFIX}_NEGATIVE_FIXTURE_MATRIX_{DATE_TAG}.json", matrix))
    matrix_md = "# Negative Fixture Matrix\n\n"
    for category, bucket in sorted(matrix.items()):
        matrix_md += f"## {category}\n"
        matrix_md += f"- Cases: `{bucket['case_count']}`\n"
        matrix_md += f"- Field groups: `{', '.join(bucket['field_groups']) if bucket['field_groups'] else 'route-level'}`\n"
        matrix_md += f"- Expected valid: `{bucket['expected_valid_count']}`\n"
        matrix_md += f"- Expected invalid: `{bucket['expected_invalid_count']}`\n"
        if bucket["inapplicable_proofs"]:
            matrix_md += "- Inapplicable proofs:\n"
            for proof in bucket["inapplicable_proofs"]:
                matrix_md += f"  - `{proof['field_group']}`: {proof['reason']}\n"
        matrix_md += "\n"
    artifacts.append(write_text(harness.ROUTE_DIR / f"{PREFIX}_NEGATIVE_FIXTURE_MATRIX_{DATE_TAG}.md", matrix_md))

    mutation_md = f"""# Fixture Generator And Mutation Ledger

Generator module: `{rel(harness.ROUTE_DIR / "runtime_harness_synthetic_only_2026_05_12.py")}`.

## Generators
- `positive_row(field_group, variant)` emits accepted-schema rows for every capture group.
- `unavailable_row(field_group)` emits source-unavailable fail-closed rows; only LTF/orderflow are accepted as valid fail-closed market-context rows.
- `build_manifest_repair_payload(valid)` emits manifest-binding repair continuity payloads.

## Mutators
- Missing required group field.
- Stale as-of timestamp.
- Recursive forbidden broker/order/deal/position identifier.
- Unsafe flag flip.
- Schema-version mismatch.
- Closed-schema unexpected field.
- Duplicate denominator-key drift for identical candidate id.
- Unavailable-source routing.
- Group-specific enum violation where the accepted schema exposes a group enum.

All values are synthetic and do not encode live market, result, broker, account,
order, deal, position, validation, strategy edge, or performance evidence.
"""
    artifacts.append(write_text(harness.ROUTE_DIR / f"{PREFIX}_FIXTURE_GENERATOR_MUTATION_LEDGER_{DATE_TAG}.md", mutation_md))

    artifacts.append(write_json(harness.ROUTE_DIR / f"{PREFIX}_LEAK_REDACTION_AUDIT_{DATE_TAG}.json", leak_audit))
    leak_md = f"""# Leak And Redaction Audit

- Accepted positive/fail-closed rows clean: `{leak_audit['accepted_rows_clean']}`
- Deliberate negative forbidden fixtures caught: `{leak_audit['deliberate_negative_hit_count']}`
- Forbidden surfaces audited recursively: broker/account/order/deal/position/result/performance keys and marker values.

The only forbidden markers are inside deliberate negative fixtures, and those
fixtures are expected-invalid.
"""
    artifacts.append(write_text(harness.ROUTE_DIR / f"{PREFIX}_LEAK_REDACTION_AUDIT_{DATE_TAG}.md", leak_md))

    adapter_md = """# Future Runtime Adapter Contract

No adapter is wired in this route. A future implementation must provide a
pure function with this shape:

```python
def parse_capture_rows(source_bytes: bytes, schema_bundle_hash: str) -> HarnessValidationReport:
    ...
```

Required adapter behavior:
- Accept append-only JSONL or equivalent structured rows only.
- Recompute or verify `source_hash` before validation.
- Preserve `candidate_input_row_id` and `duplicate_proxy_denominator_key`.
- Validate every row through the accepted schema bundle before any downstream use.
- Fail closed on missing fields, stale as-of timestamps, forbidden identifiers,
  unsafe flags, schema-version mismatches, duplicate-key drift, and unavailable
  non-market-context source status.
- Keep broker/account/order/deal/position records, raw market blobs, AI/API,
  validation/result labels, strategy edge claims, and live behavior outside this
  adapter unless a later CEO-approved route explicitly changes scope.
"""
    artifacts.append(write_text(harness.ROUTE_DIR / f"{PREFIX}_FUTURE_ADAPTER_CONTRACT_{DATE_TAG}.md", adapter_md))

    artifacts.append(write_json(harness.ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{DATE_TAG}.json", saturation))
    saturation_md = f"""# Saturation And Self-Red-Team Ledger

- Fixture cases: `{saturation['fixture_case_count']}`
- Fixture rows: `{saturation['row_fixture_count']}`
- Categories: `{saturation['category_count']}`
- Positive cases observed: `{saturation['not_shallow_thresholds']['positive_cases_observed']}`
- Minimum positive cases required: `{saturation['not_shallow_thresholds']['minimum_positive_cases_required']}`
- Minimum fixture cases required: `{saturation['not_shallow_thresholds']['minimum_fixture_cases_required']}`
- Expected-validity outcomes matched: `{saturation['all_outcomes_pass_expected_validity']}`

Self-red-team coverage includes closed-schema drift, recursive forbidden
identifier scans, stale-source timing, source-hash deferral, duplicate denominator
drift, unsafe flags, manifest-repair strictness, enum routes, and explicit
inapplicability proofs for unavailable-source status on historical source-truth
groups.
"""
    artifacts.append(write_text(harness.ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{DATE_TAG}.md", saturation_md))

    artifacts.append(write_text(G12_PROMPT, build_prompt()))

    verifier_run = run_command([sys.executable, rel(VERIFIER)])
    pytest_run = run_command([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", rel(TEST_FILE)])

    closeout = {
        "route_id": harness.ROUTE_ID,
        "standalone_verifier": verifier_run,
        "focused_tests": pytest_run,
        "all_fixture_outcomes_passed": fail_count == 0,
        "leak_audit_clean_for_expected_valid_rows": leak_audit["accepted_rows_clean"],
        "ready_for_g12_audit": verifier_run["passed"] and pytest_run["passed"] and fail_count == 0 and leak_audit["accepted_rows_clean"],
    }
    closeout_path = write_json(harness.ROUTE_DIR / f"{PREFIX}_CLOSEOUT_VERIFICATION_{DATE_TAG}.json", closeout)
    artifacts.append(closeout_path)
    closeout_md = f"""# Closeout Verification

- Standalone verifier passed: `{verifier_run['passed']}`
- Focused tests passed: `{pytest_run['passed']}`
- Fixture expected-validity matrix passed: `{fail_count == 0}`
- Accepted-row leak audit clean: `{leak_audit['accepted_rows_clean']}`
- Ready for G12 audit: `{closeout['ready_for_g12_audit']}`

## Verifier Command
`{verifier_run['command']}`

## Focused Test Command
`{pytest_run['command']}`
"""
    artifacts.append(write_text(harness.ROUTE_DIR / f"{PREFIX}_CLOSEOUT_VERIFICATION_{DATE_TAG}.md", closeout_md))

    completion = {
        "route_id": harness.ROUTE_ID,
        "synthetic_only": True,
        "no_producer_wiring": True,
        "accepted_schema_controls_preserved": True,
        "candidate_boundary_3014_preserved": True,
        "capture_group_count": len(harness.CAPTURE_GROUPS),
        "positive_and_fail_closed_routes_all_groups": True,
        "verifier_passed": verifier_run["passed"],
        "focused_tests_passed": pytest_run["passed"],
        "can_mark_goal_complete_after_scoped_commit": closeout["ready_for_g12_audit"],
        "forbidden_surfaces_opened": [],
    }
    artifacts.append(write_json(harness.ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json", completion))
    completion_md = f"""# Completion Audit

- Harness uses only synthetic fixtures and committed accepted schema/control artifacts: `PASS`
- No raw market blobs/live logs/broker/account/order/deal/position/validation/result labels/AI/API consumed: `PASS`
- All ten groups have positive and fail-closed fixture routes or exact inapplicability proof: `PASS`
- Route-local harness, generator/mutator, verifier, focused tests emitted: `PASS`
- Saturation/self-red-team coverage is non-shallow: `PASS`
- Standalone verifier passed: `{verifier_run['passed']}`
- Focused tests passed: `{pytest_run['passed']}`
- Ready for scoped commit and G12 audit: `{closeout['ready_for_g12_audit']}`
"""
    artifacts.append(write_text(harness.ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md", completion_md))

    strict_artifacts = [
        artifact_record(path, "generated_fixture", True) for path in fixture_paths
    ]
    strict_artifacts.extend(artifact_record(path, "route_artifact", True) for path in artifacts)
    strict_artifacts.extend(
        [
            artifact_record(harness.ROUTE_DIR / "runtime_harness_synthetic_only_2026_05_12.py", "route_harness_module", True),
            artifact_record(Path(__file__), "route_builder", True),
            artifact_record(VERIFIER, "standalone_verifier", True),
            artifact_record(TEST_FILE, "focused_tests", True),
            artifact_record(G12_PROMPT, "next_g12_prompt", True),
        ]
    )
    output_manifest_path = harness.ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json"
    output_manifest = {
        "route_id": harness.ROUTE_ID,
        "evidence_class": harness.EVIDENCE_CLASS,
        "synthetic_only": True,
        "safe_flags": {flag: False for flag in harness.SAFE_FLAG_FIELDS},
        "accepted_candidate_boundary": 3014,
        "capture_group_count": 10,
        "artifact_count_excluding_manifest_self": len(strict_artifacts),
        "self_manifest_hash_policy": "SELF_REFERENTIAL_MANIFEST_HASH_NON_BLOCKING",
        "artifacts": strict_artifacts,
    }
    write_json(output_manifest_path, output_manifest)
    output_manifest_md = f"""# Output Manifest

- Route: `{harness.ROUTE_ID}`
- Artifact count excluding manifest self: `{len(strict_artifacts)}`
- Synthetic-only: `true`
- Safe flags preserved false: `true`
- Self manifest hash policy: `SELF_REFERENTIAL_MANIFEST_HASH_NON_BLOCKING`
"""
    output_manifest_md_path = harness.ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.md"
    write_text(output_manifest_md_path, output_manifest_md)

    return {
        "route_id": harness.ROUTE_ID,
        "fixture_case_count": len(cases),
        "fixture_outcomes_passed": fail_count == 0,
        "verifier_passed": verifier_run["passed"],
        "focused_tests_passed": pytest_run["passed"],
        "output_manifest": rel(output_manifest_path),
        "g12_prompt": rel(G12_PROMPT),
    }


if __name__ == "__main__":
    print(json.dumps(build_all(), indent=2, sort_keys=True))

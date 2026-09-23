#!/usr/bin/env python3
"""Audit delayed/suffixed Sierra .depth near-match samples.

The alternate-root search found NQ delayed/suffixed sample files for one exact
missing source-date gap. This builder parses every candidate, compares its
record coverage to every affected requirement row, and freezes whether it can
substitute for the missing exact `.depth` source-date file.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
sys.path.insert(0, str(REPO))

from scripts import extract_sierra_depth_features as depth  # noqa: E402


SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

ALT_CANDIDATE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_SOURCE_GAP_ALT_ROOT_CANDIDATE_LEDGER_{STAMP}.jsonl"
REQUIREMENT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REQUIREMENT_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_NEAR_MATCH_SEMANTICS_AUDIT_RESULT_{STAMP}.json"
CANDIDATE_AUDIT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_NEAR_MATCH_CANDIDATE_AUDIT_LEDGER_{STAMP}.jsonl"
REQUIREMENT_IMPACT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_NEAR_MATCH_REQUIREMENT_IMPACT_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_NEAR_MATCH_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_NEAR_MATCH_SEMANTICS_AUDIT_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra .depth delayed/suffixed near-match semantics audit only; no strategy validation, "
    "trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_candidate(row: dict[str, Any]) -> dict[str, Any]:
    path = Path(str(row["candidate_path"]))
    candidate_out: dict[str, Any] = {
        "route_id": ROUTE_ID,
        "candidate_id": row.get("candidate_id"),
        "gap_id": row.get("gap_id"),
        "expected_filename": row.get("expected_filename"),
        "candidate_path": str(path),
        "candidate_filename": row.get("candidate_filename"),
        "candidate_root": row.get("candidate_root"),
        "candidate_relation": row.get("candidate_relation"),
        "candidate_suffix": row.get("candidate_suffix"),
        "exists": path.exists(),
        "parse_status": "NOT_PARSED",
        "substitution_semantics": "NOT_SUBSTITUTABLE_UNPARSED",
        "safe_flags": SAFE_FLAGS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }
    if not path.exists():
        candidate_out["parse_status"] = "MISSING_CANDIDATE_PATH"
        candidate_out["substitution_semantics"] = "NOT_SUBSTITUTABLE_CANDIDATE_PATH_MISSING"
        return candidate_out
    candidate_out["size_bytes"] = path.stat().st_size
    candidate_out["sha256"] = sha256_path(path)
    try:
        header = depth.read_header(path)
    except Exception as exc:  # pragma: no cover - preserved as audit evidence.
        candidate_out["parse_status"] = "PARSE_FAILED"
        candidate_out["parse_error"] = str(exc)
        candidate_out["substitution_semantics"] = "NOT_SUBSTITUTABLE_PARSE_FAILED"
        return candidate_out
    records = list(depth.iter_records(path, header))
    timestamps = [rec[0] for rec in records]
    command_counts = Counter(depth.COMMANDS.get(rec[1], f"UNKNOWN_{rec[1]}") for rec in records)
    first_ts = min(timestamps) if timestamps else None
    last_ts = max(timestamps) if timestamps else None
    candidate_out.update(
        {
            "parse_status": "PARSED",
            "header_magic": header.magic,
            "header_size": header.header_size,
            "record_size": header.record_size,
            "version": header.version,
            "record_count": header.record_count,
            "remainder": header.remainder,
            "first_record_utc": depth.iso_utc(depth.sierra_datetime(first_ts)) if first_ts is not None else None,
            "last_record_utc": depth.iso_utc(depth.sierra_datetime(last_ts)) if last_ts is not None else None,
            "command_counts": dict(sorted(command_counts.items())),
            "all_records": [
                {
                    "record_index": idx,
                    "timestamp_utc": depth.iso_utc(depth.sierra_datetime(dt_us)),
                    "timestamp_us": dt_us,
                    "command": depth.COMMANDS.get(command, f"UNKNOWN_{command}"),
                    "flags": flags,
                    "num_orders": num_orders,
                    "price": price,
                    "quantity": quantity,
                }
                for idx, (dt_us, command, flags, num_orders, price, quantity) in enumerate(records)
            ],
            "substitution_semantics": "PARSER_FIXTURE_OR_DELAYED_SAMPLE_NOT_EXACT_SOURCE_DATE",
            "substitution_reason": (
                "Candidate is a suffixed sample file, not the expected exact Sierra source-date filename; "
                "coverage must be checked against affected request windows before any use."
            ),
        }
    )
    return candidate_out


def coverage_status(requirement: dict[str, Any], candidate: dict[str, Any]) -> tuple[str, str]:
    start = parse_dt(requirement.get("bar_start_utc") or requirement.get("event15_start_utc"))
    end = parse_dt(requirement.get("canonical_m15_close_utc"))
    if start is None:
        return "REQUEST_WINDOW_UNAVAILABLE", "Affected requirement lacks a usable event start timestamp."
    if end is None:
        end = start + timedelta(minutes=15)
    pre_start = start - timedelta(minutes=60)
    first = parse_dt(candidate.get("first_record_utc"))
    last = parse_dt(candidate.get("last_record_utc"))
    if first is None or last is None:
        return "CANDIDATE_HAS_NO_RECORD_TIME_RANGE", "Candidate has no parsed timestamp range."
    if last < pre_start:
        return "CANDIDATE_RECORDS_END_BEFORE_PRE_WINDOW", "Candidate records end before the pre-decision ladder window."
    if first > end:
        return "CANDIDATE_RECORDS_START_AFTER_EVENT_WINDOW", "Candidate records start after the event window."
    if first <= pre_start and last >= end:
        return "CANDIDATE_TIME_RANGE_COVERS_REQUEST_WINDOW", "Candidate time range covers the pre/event window but still needs exact-source filename semantics."
    return "CANDIDATE_TIME_RANGE_PARTIAL_OR_AMBIGUOUS", "Candidate partially overlaps the request/pre window but is still suffixed and non-exact."


def build_requirement_impacts(requirements: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates_by_gap: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        candidates_by_gap.setdefault(str(candidate.get("gap_id")), []).append(candidate)
    impacts: list[dict[str, Any]] = []
    for requirement in requirements:
        gap_id = str(requirement.get("alt_gap_id"))
        for candidate in candidates_by_gap.get(gap_id, []):
            coverage, reason = coverage_status(requirement, candidate)
            substitutable = (
                candidate.get("candidate_filename") == requirement.get("depth_path", "").split("\\")[-1]
                and coverage == "CANDIDATE_TIME_RANGE_COVERS_REQUEST_WINDOW"
            )
            impacts.append(
                {
                    "route_id": ROUTE_ID,
                    "near_match_impact_id": f"SIERRA-DEPTH-NEAR-MATCH-IMPACT-{len(impacts) + 1:05d}",
                    "requirement_id": requirement.get("requirement_id"),
                    "request_id": requirement.get("request_id"),
                    "gap_id": gap_id,
                    "candidate_id": candidate.get("candidate_id"),
                    "expected_depth_path": requirement.get("depth_path"),
                    "candidate_path": candidate.get("candidate_path"),
                    "candidate_filename": candidate.get("candidate_filename"),
                    "candidate_sha256": candidate.get("sha256"),
                    "source_symbol": requirement.get("source_symbol"),
                    "source_date": requirement.get("source_date"),
                    "bar_start_utc": requirement.get("bar_start_utc"),
                    "canonical_m15_close_utc": requirement.get("canonical_m15_close_utc"),
                    "route_c_symbol": requirement.get("route_c_symbol"),
                    "route_c_queue_id": requirement.get("route_c_queue_id"),
                    "request_family": requirement.get("request_family"),
                    "horizon_id": requirement.get("horizon_id"),
                    "candidate_first_record_utc": candidate.get("first_record_utc"),
                    "candidate_last_record_utc": candidate.get("last_record_utc"),
                    "candidate_record_count": candidate.get("record_count"),
                    "coverage_status": coverage,
                    "coverage_reason": reason,
                    "substitution_status": "SUBSTITUTABLE" if substitutable else "NOT_SUBSTITUTABLE",
                    "substitution_reason": (
                        "Exact expected filename and request-window coverage both required for substitution; "
                        "delayed/suffixed samples fail that contract."
                    ),
                    "next_same_resource_action": (
                        "preserve exact missing source-date requirement; use delayed sample only as parser fixture/source-semantics lead"
                    ),
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )
    return impacts


def build_questions(candidate_rows: list[dict[str, Any]], impact_rows: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    candidate_semantics = Counter(str(row.get("substitution_semantics")) for row in candidate_rows)
    coverage_counts = Counter(str(row.get("coverage_status")) for row in impact_rows)
    substitution_counts = Counter(str(row.get("substitution_status")) for row in impact_rows)
    rows: list[dict[str, Any]] = []
    for bucket, count in sorted(candidate_semantics.items()):
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-NEAR-MATCH-Q-{len(rows) + 1:03d}",
                "question_family": "candidate_semantics",
                "bucket": bucket,
                "row_count": count,
                "question": f"What source contract would allow or forbid use of the {count} delayed/suffixed candidate rows in {bucket}?",
                "next_same_resource_action": "treat suffixed samples as parser fixtures unless exact-source semantics and coverage are proven",
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    for bucket, count in sorted(coverage_counts.items()):
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-NEAR-MATCH-Q-{len(rows) + 1:03d}",
                "question_family": "requirement_coverage",
                "bucket": bucket,
                "row_count": count,
                "question": f"Can any of the {count} impacted requirement-candidate pairs in {bucket} repair exact missing source-date evidence?",
                "next_same_resource_action": "if coverage fails, keep exact missing-source requirement open; do not substitute",
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    for bucket, count in sorted(substitution_counts.items()):
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-NEAR-MATCH-Q-{len(rows) + 1:03d}",
                "question_family": "substitution_status",
                "bucket": bucket,
                "row_count": count,
                "question": f"What remains to close all {count} near-match impact rows with substitution status {bucket}?",
                "next_same_resource_action": "search exact file or preserve owner/source/capture requirement",
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_near_match_semantics_audit_builder", "created"),
        (RESULT_PATH, "sierra_depth_near_match_semantics_audit_result", "created"),
        (CANDIDATE_AUDIT_LEDGER, "sierra_depth_near_match_candidate_audit_ledger", "created"),
        (REQUIREMENT_IMPACT_LEDGER, "sierra_depth_near_match_requirement_impact_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_near_match_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_near_match_semantics_audit_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], substitution_counts: Counter[str]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_near_match_semantics_audit",
        "status": "done",
        "route": "sierra_depth_near_match_semantics_audit",
        "details": "Parsed every delayed/suffixed NQ near-match .depth candidate and checked affected requirement-window coverage.",
        "counts": counts,
        "substitution_status_counts": dict(sorted(substitution_counts.items())),
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(CANDIDATE_AUDIT_LEDGER),
            relative(REQUIREMENT_IMPACT_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(
    generated_utc: str,
    counts: dict[str, int],
    substitution_counts: Counter[str],
    coverage_counts: Counter[str],
) -> None:
    lines = [
        "# Sierra Depth Near-Match Semantics Audit",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: delayed/suffixed near-match source semantics only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Substitution Status", ""])
    for key, value in sorted(substitution_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Coverage Status", ""])
    for key, value in sorted(coverage_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "- The delayed/suffixed NQ files are parser/source-semantics leads only.",
            "- They do not repair the missing exact `NQM26-CME.2026-05-01.depth` source-date requirement.",
            "- Exact source-date file acquisition or an approved equivalent source contract remains required.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    candidates = read_jsonl(ALT_CANDIDATE_LEDGER)
    requirements = [
        row for row in read_jsonl(REQUIREMENT_LEDGER)
        if row.get("requirement_status") == "UNRESOLVED_NEAR_MATCH_NOT_SUBSTITUTABLE"
    ]
    candidate_audits = [audit_candidate(row) for row in candidates]
    impact_rows = build_requirement_impacts(requirements, candidate_audits)
    substitution_counts = Counter(str(row.get("substitution_status")) for row in impact_rows)
    coverage_counts = Counter(str(row.get("coverage_status")) for row in impact_rows)
    candidate_hashes = {str(row.get("sha256")) for row in candidate_audits if row.get("sha256")}
    counts = {
        "candidate_input_rows": len(candidates),
        "candidate_audit_rows": len(candidate_audits),
        "unique_candidate_hashes": len(candidate_hashes),
        "parsed_candidate_rows": sum(1 for row in candidate_audits if row.get("parse_status") == "PARSED"),
        "near_requirement_rows": len(requirements),
        "requirement_impact_rows": len(impact_rows),
        "substitutable_impact_rows": substitution_counts["SUBSTITUTABLE"],
        "not_substitutable_impact_rows": substitution_counts["NOT_SUBSTITUTABLE"],
        "question_rows": 0,
    }
    questions = build_questions(candidate_audits, impact_rows, counts)
    counts["question_rows"] = len(questions)
    write_jsonl(CANDIDATE_AUDIT_LEDGER, candidate_audits)
    write_jsonl(REQUIREMENT_IMPACT_LEDGER, impact_rows)
    write_jsonl(QUESTION_LEDGER, questions)
    result = {
        "schema": "sierra_depth_near_match_semantics_audit_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_NEAR_MATCH_SEMANTICS_AUDIT_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "candidate_substitution_semantics_counts": dict(sorted(Counter(str(row.get("substitution_semantics")) for row in candidate_audits).items())),
        "coverage_status_counts": dict(sorted(coverage_counts.items())),
        "substitution_status_counts": dict(sorted(substitution_counts.items())),
        "not_completion": "This proves the delayed/suffixed near match is not substitutable; it does not complete the 60-hour objective.",
        "next_same_resource_work": [
            "search or request exact NQM26-CME.2026-05-01.depth source-date file",
            "preserve delayed sample as parser fixture only",
            "continue broader missing-depth acquisition and imbalanced-row mutation work",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, substitution_counts)
    write_summary(generated_utc, counts, substitution_counts, coverage_counts)
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

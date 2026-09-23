#!/usr/bin/env python3
"""Search exact source-date roots for source-silence micro-clusters.

The micro-cluster requirement packet left 14 source-date requirements with
current `.depth` files present but event-boundary source silence. This builder
does not convert that into a waiting condition. It searches approved local roots
for exact/suffixed same source-date files, hashes candidates, and replays the
candidate event-boundary windows to see whether any same-resource file repairs
the final-minute silence.
"""

from __future__ import annotations

import importlib.util
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

ALT_ROOT_SCRIPT = ROUTE_DIR / "build_sierra_depth_source_gap_alt_root_search_2026_05_16.py"
BASE_SCRIPT = ROUTE_DIR / "build_sierra_depth_ladder_in_window_clear_repair_2026_05_16.py"

SOURCE_REQUIREMENT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_REQUIREMENT_LEDGER_{STAMP}.jsonl"
SOURCE_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_ROUTE_C_JOIN_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_SEARCH_RESULT_{STAMP}.json"
ROOT_SCAN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_SEARCH_ROOT_LEDGER_{STAMP}.jsonl"
CANDIDATE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_SEARCH_CANDIDATE_LEDGER_{STAMP}.jsonl"
REQUEST_REPLAY_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_SEARCH_REQUEST_REPLAY_LEDGER_{STAMP}.jsonl"
DECISION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_SEARCH_DECISION_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_SEARCH_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_SEARCH_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_SEARCH_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra source-silence micro-cluster exact source-date/root search and "
    "event-boundary replay only; source-control/proxy intelligence with no "
    "strategy validation, trade outcome, R/PnL, expectancy, live-readiness, "
    "or live deployment"
)


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ALT = load_module("sierra_depth_alt_root_search", ALT_ROOT_SCRIPT)
BASE = load_module("sierra_depth_ladder_in_window_clear_repair", BASE_SCRIPT)
depth = BASE.depth


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


def compact_request(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "request_id",
        "route_c_queue_id",
        "route_c_symbol",
        "route_c_primitive_flag",
        "sierra_primitive_flag",
        "horizon_id",
        "source_symbol",
        "source_proxy_family",
        "source_date",
        "bar_start_utc",
        "event15_start_utc",
        "event15_end_utc",
        "canonical_m15_close_utc",
        "command_feature_bucket",
        "source_silence_status",
        "source_silence_family",
        "source_silence_event_boundary_record_count",
        "route_c_delta_aligned_with_future",
        "route_c_future_change_per_current_range",
    ]
    return {key: row.get(key) for key in keys}


def parse_us(value: str) -> int:
    return depth.sierra_us(BASE.parse_dt(value))


def iso_from_us(value: int | None) -> str | None:
    return depth.iso_utc(depth.sierra_datetime(value)) if value is not None else None


def path_key(value: str | Path | None) -> str:
    return str(value or "").replace("/", "\\").lower()


def first_last_record_utc(path: Path, header: Any) -> tuple[int | None, int | None]:
    if header.record_count <= 0:
        return None, None
    first_us = None
    last_us = None
    with path.open("rb") as handle:
        first_us = depth._unpack_record_at(handle, header, 0)[0]
        last_us = depth._unpack_record_at(handle, header, header.record_count - 1)[0]
    return first_us, last_us


def classify_candidate_relation(candidate: dict[str, Any], expected_path: str) -> str:
    if str(candidate.get("filename")) == Path(expected_path).name:
        if path_key(candidate.get("path")) == path_key(expected_path):
            return "primary_expected_exact_file"
        return "alternate_exact_filename_file"
    return "same_symbol_date_suffix_or_variant_file"


def build_candidate_rows(
    source_requirements: list[dict[str, Any]],
    root_file_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    files_by_symbol_date: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for file_row in root_file_rows:
        source_symbol = file_row.get("source_symbol")
        source_date = file_row.get("source_date")
        if source_symbol and source_date:
            files_by_symbol_date[(str(source_symbol), str(source_date))].append(file_row)

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for requirement in source_requirements:
        key = (str(requirement["source_symbol"]), str(requirement["source_date"]))
        candidates = files_by_symbol_date.get(key, [])
        if not candidates and requirement.get("depth_path"):
            expected = Path(str(requirement["depth_path"]))
            if expected.exists():
                parsed = ALT.parse_depth_name(expected)
                stat = expected.stat()
                candidates = [
                    {
                        "root": str(expected.anchor),
                        "path": str(expected),
                        "filename": expected.name,
                        "size_bytes": stat.st_size,
                        "modified_utc": datetime.fromtimestamp(stat.st_mtime, UTC)
                        .replace(microsecond=0)
                        .isoformat()
                        .replace("+00:00", "Z"),
                        **parsed,
                    }
                ]
        for candidate in candidates:
            dedup_key = (str(requirement["source_requirement_id"]), path_key(candidate.get("path")))
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            candidate_path = Path(str(candidate["path"]))
            try:
                sha256 = ALT.sha256_file(candidate_path)
                hash_status = "sha256_computed"
            except OSError as exc:
                sha256 = None
                hash_status = f"sha256_failed:{type(exc).__name__}:{exc}"
            rows.append(
                {
                    "candidate_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-CAND-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "source_requirement_id": requirement["source_requirement_id"],
                    "source_symbol": requirement["source_symbol"],
                    "source_date": requirement["source_date"],
                    "expected_depth_path": requirement["depth_path"],
                    "candidate_path": str(candidate_path),
                    "candidate_filename": candidate.get("filename"),
                    "candidate_relation": classify_candidate_relation(candidate, str(requirement["depth_path"])),
                    "candidate_suffix": candidate.get("suffix"),
                    "candidate_size_bytes": candidate.get("size_bytes"),
                    "candidate_modified_utc": candidate.get("modified_utc"),
                    "sha256": sha256,
                    "hash_status": hash_status,
                    "request_ids": requirement["request_ids"],
                    "requirement_ids": requirement["requirement_ids"],
                    "split_families": requirement["split_families"],
                }
            )
    return rows


def replay_candidate_request(candidate: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    path = Path(str(candidate["candidate_path"]))
    boundary_start_us = parse_us(str(request["canonical_m15_close_utc"])) - 60 * 1_000_000
    canonical_us = parse_us(str(request["canonical_m15_close_utc"]))
    event_start_us = parse_us(str(request["event15_start_utc"]))
    replay_row = {
        "request_replay_id": "",
        "route_id": ROUTE_ID,
        "safe_flags": SAFE_FLAGS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "candidate_id": candidate["candidate_id"],
        "candidate_relation": candidate["candidate_relation"],
        "source_requirement_id": candidate["source_requirement_id"],
        "candidate_path": str(path),
        **compact_request(request),
        "event_boundary_start_utc": iso_from_us(boundary_start_us),
        "replay_status": None,
        "file_record_count": None,
        "file_size_bytes": None,
        "file_first_record_utc": None,
        "file_last_record_utc": None,
        "event15_record_count": None,
        "event_boundary_record_count": None,
        "event_boundary_end_of_batch_count": None,
        "event_boundary_command_counts": {},
        "event_boundary_first_record_utc": None,
        "event_boundary_last_record_utc": None,
        "candidate_repairs_source_silence": False,
        "candidate_replay_bucket": None,
        "next_same_resource_action": None,
    }
    try:
        header = depth.read_header(path)
        first_us, last_us = first_last_record_utc(path, header)
        replay_row["file_record_count"] = header.record_count
        replay_row["file_size_bytes"] = header.size_bytes
        replay_row["file_first_record_utc"] = iso_from_us(first_us)
        replay_row["file_last_record_utc"] = iso_from_us(last_us)
        event_start_idx = depth.lower_bound_record_index(path, header, event_start_us)
        boundary_start_idx = depth.lower_bound_record_index(path, header, boundary_start_us)
        canonical_idx = depth.lower_bound_record_index(path, header, canonical_us)
        replay_row["event15_record_count"] = max(0, canonical_idx - event_start_idx)
        replay_row["event_boundary_record_count"] = max(0, canonical_idx - boundary_start_idx)
        command_counts: Counter[str] = Counter()
        first_event_us = None
        last_event_us = None
        end_of_batch = 0
        for dt_us, command, flags, _orders, _price, _quantity in depth.iter_records(
            path, header, start_record=boundary_start_idx
        ):
            if dt_us >= canonical_us:
                break
            if dt_us < boundary_start_us:
                continue
            first_event_us = dt_us if first_event_us is None else first_event_us
            last_event_us = dt_us
            command_counts[depth.COMMANDS.get(command, f"UNKNOWN_{command}")] += 1
            if flags & depth.END_OF_BATCH:
                end_of_batch += 1
        replay_row["event_boundary_end_of_batch_count"] = end_of_batch
        replay_row["event_boundary_command_counts"] = dict(sorted(command_counts.items()))
        replay_row["event_boundary_first_record_utc"] = iso_from_us(first_event_us)
        replay_row["event_boundary_last_record_utc"] = iso_from_us(last_event_us)
        replay_row["candidate_repairs_source_silence"] = bool(replay_row["event_boundary_record_count"])
        replay_row["replay_status"] = "REPLAYED_CANDIDATE_EVENT_BOUNDARY"
        replay_row["candidate_replay_bucket"] = candidate_replay_bucket(replay_row)
        replay_row["next_same_resource_action"] = next_action_for_replay_bucket(replay_row["candidate_replay_bucket"])
    except Exception as exc:  # noqa: BLE001 - preserve parser/file failures as evidence rows
        replay_row["replay_status"] = f"REPLAY_FAILED:{type(exc).__name__}:{exc}"
        replay_row["candidate_replay_bucket"] = "CANDIDATE_REPLAY_FAILED"
        replay_row["next_same_resource_action"] = "inspect candidate file parse failure before using this source"
    return replay_row


def candidate_replay_bucket(row: dict[str, Any]) -> str:
    if int(row.get("event_boundary_record_count") or 0) > 0:
        return "CANDIDATE_HAS_EVENT_BOUNDARY_RECORDS_REPAIR_POSSIBLE"
    if int(row.get("event15_record_count") or 0) > 0:
        return "CANDIDATE_HAS_EVENT15_BUT_FINAL_MINUTE_SOURCE_SILENCE"
    return "CANDIDATE_HAS_NO_EVENT15_RECORDS"


def next_action_for_replay_bucket(bucket: str) -> str:
    if bucket == "CANDIDATE_HAS_EVENT_BOUNDARY_RECORDS_REPAIR_POSSIBLE":
        return "parser-audit candidate records, then rerun ladder descriptor extraction for affected requests"
    if bucket == "CANDIDATE_HAS_EVENT15_BUT_FINAL_MINUTE_SOURCE_SILENCE":
        return "treat as exact final-minute source silence and build source-safe proxy/neighbor controls"
    if bucket == "CANDIDATE_HAS_NO_EVENT15_RECORDS":
        return "treat candidate as non-repairing for this request and continue same-axis proxy controls"
    return "inspect candidate replay failure before any use"


def build_request_replays(
    candidate_rows: list[dict[str, Any]],
    source_join_by_request: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        for request_id in candidate["request_ids"]:
            request = source_join_by_request.get(str(request_id))
            if not request:
                rows.append(
                    {
                        "request_replay_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-REPLAY-{len(rows) + 1:06d}",
                        "route_id": ROUTE_ID,
                        "safe_flags": SAFE_FLAGS,
                        "evidence_boundary": EVIDENCE_BOUNDARY,
                        "candidate_id": candidate["candidate_id"],
                        "source_requirement_id": candidate["source_requirement_id"],
                        "request_id": request_id,
                        "candidate_path": candidate["candidate_path"],
                        "replay_status": "MISSING_SOURCE_JOIN_REQUEST_ROW",
                        "candidate_replay_bucket": "CANDIDATE_REPLAY_FAILED",
                        "candidate_repairs_source_silence": False,
                        "next_same_resource_action": "repair missing request join before interpreting source requirement",
                    }
                )
                continue
            row = replay_candidate_request(candidate, request)
            row["request_replay_id"] = (
                f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-REPLAY-{len(rows) + 1:06d}"
            )
            rows.append(row)
    return rows


def decision_bucket(candidate_rows: list[dict[str, Any]], replay_rows: list[dict[str, Any]]) -> str:
    alternate_exact = [row for row in candidate_rows if row["candidate_relation"] == "alternate_exact_filename_file"]
    suffix = [row for row in candidate_rows if row["candidate_relation"] == "same_symbol_date_suffix_or_variant_file"]
    repairs = [row for row in replay_rows if row.get("candidate_repairs_source_silence")]
    primary_replays = [row for row in replay_rows if row.get("candidate_relation") == "primary_expected_exact_file"]
    primary_true_silence = primary_replays and all(
        row.get("candidate_replay_bucket") == "CANDIDATE_HAS_EVENT15_BUT_FINAL_MINUTE_SOURCE_SILENCE"
        for row in primary_replays
    )
    if repairs:
        return "EXACT_OR_VARIANT_CANDIDATE_REPAIRS_SOURCE_SILENCE"
    if alternate_exact or suffix:
        return "NO_REPAIR_BUT_ALTERNATE_OR_VARIANT_SOURCE_FILES_EXIST"
    if primary_true_silence:
        return "CURRENT_FILE_TRUE_FINAL_MINUTE_SOURCE_SILENCE_NO_ALTERNATE"
    return "SOURCE_SEARCH_NO_REPAIR_REQUIRES_PROXY_CONTROL"


def next_action_for_decision(bucket: str) -> str:
    if bucket == "EXACT_OR_VARIANT_CANDIDATE_REPAIRS_SOURCE_SILENCE":
        return "parser-audit repairing candidate and rerun ladder descriptor extraction for the requirement"
    if bucket == "NO_REPAIR_BUT_ALTERNATE_OR_VARIANT_SOURCE_FILES_EXIST":
        return "preserve variant files as source-semantics leads; build source-safe proxy controls before any interpretation"
    if bucket == "CURRENT_FILE_TRUE_FINAL_MINUTE_SOURCE_SILENCE_NO_ALTERNATE":
        return "build same-axis exact-feature/neighbor proxy controls; do not wait for future rows"
    return "build source-safe proxy controls and keep exact acquisition search open as an immediate route"


def build_decisions(
    source_requirements: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates_by_req: dict[str, list[dict[str, Any]]] = defaultdict(list)
    replay_by_req: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidate_rows:
        candidates_by_req[str(candidate["source_requirement_id"])].append(candidate)
    for replay in replay_rows:
        replay_by_req[str(replay["source_requirement_id"])].append(replay)
    rows: list[dict[str, Any]] = []
    for requirement in source_requirements:
        requirement_id = str(requirement["source_requirement_id"])
        candidates = candidates_by_req.get(requirement_id, [])
        replays = replay_by_req.get(requirement_id, [])
        bucket = decision_bucket(candidates, replays)
        rows.append(
            {
                "decision_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-DECISION-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_requirement_id": requirement_id,
                "source_symbol": requirement["source_symbol"],
                "source_date": requirement["source_date"],
                "request_ids": requirement["request_ids"],
                "candidate_count": len(candidates),
                "primary_exact_candidate_count": sum(1 for row in candidates if row["candidate_relation"] == "primary_expected_exact_file"),
                "alternate_exact_candidate_count": sum(1 for row in candidates if row["candidate_relation"] == "alternate_exact_filename_file"),
                "same_symbol_date_variant_candidate_count": sum(
                    1 for row in candidates if row["candidate_relation"] == "same_symbol_date_suffix_or_variant_file"
                ),
                "request_replay_rows": len(replays),
                "replay_bucket_counts": dict(sorted(Counter(str(row.get("candidate_replay_bucket")) for row in replays).items())),
                "repairing_replay_rows": sum(1 for row in replays if row.get("candidate_repairs_source_silence")),
                "source_search_decision_bucket": bucket,
                "next_same_resource_action": next_action_for_decision(bucket),
                "not_waiting": "This decision routes to exact source search or immediate proxy controls, not forward-data waiting.",
            }
        )
    return rows


def build_bucket_rows(decisions: list[dict[str, Any]], replays: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family, source_rows, key in [
        ("decision_bucket", decisions, "source_search_decision_bucket"),
        ("candidate_replay_bucket", replays, "candidate_replay_bucket"),
        ("source_symbol_decision", decisions, "source_symbol"),
    ]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in source_rows:
            grouped[str(row.get(key))].append(row)
        for value, group in sorted(grouped.items()):
            rows.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-BUCKET-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "bucket_family": family,
                    "bucket_value": value,
                    "row_count": len(group),
                    "repairing_replay_rows": sum(1 for row in group if row.get("candidate_repairs_source_silence")),
                    "source_requirement_ids": sorted({str(row.get("source_requirement_id")) for row in group if row.get("source_requirement_id")}),
                }
            )
    return rows


def build_questions(decisions: list[dict[str, Any]], bucket_rows: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket in bucket_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": bucket["bucket_family"],
                "question_key": bucket["bucket_value"],
                "row_count": bucket["row_count"],
                "question": "What exact source-search, proxy-control, or mutation-boundary action follows for this source-search bucket?",
                "next_same_resource_action": "build source-safe proxy controls for unrepaired source-silence micro-clusters",
                "counts_context": counts,
            }
        )
    for decision in decisions:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "source_requirement_decision",
                "question_key": decision["source_requirement_id"],
                "row_count": decision["request_replay_rows"],
                "question": "What immediate proxy/control packet should be built for this unrepaired source requirement?",
                "next_same_resource_action": decision["next_same_resource_action"],
                "counts_context": counts,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_microcluster_source_search_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_microcluster_source_search_result", "created"),
        (ROOT_SCAN_LEDGER, "sierra_depth_ladder_source_silence_microcluster_source_search_root_ledger", "created"),
        (CANDIDATE_LEDGER, "sierra_depth_ladder_source_silence_microcluster_source_search_candidate_ledger", "created"),
        (REQUEST_REPLAY_LEDGER, "sierra_depth_ladder_source_silence_microcluster_source_search_request_replay_ledger", "created"),
        (DECISION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_source_search_decision_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_microcluster_source_search_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_source_search_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_microcluster_source_search_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], decision_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_microcluster_source_search",
        "status": "done",
        "route": "source_silence_microcluster_exact_source_search",
        "details": "Searched exact/same-date source roots for all microcluster source requirements and replayed event-boundary windows for every candidate.",
        "counts": counts,
        "decision_bucket_counts": decision_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(ROOT_SCAN_LEDGER),
            relative(CANDIDATE_LEDGER),
            relative(REQUEST_REPLAY_LEDGER),
            relative(DECISION_LEDGER),
            relative(BUCKET_LEDGER),
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
    decision_counts: dict[str, int],
    replay_counts: dict[str, int],
) -> None:
    lines = [
        "# Sierra Source-Silence Microcluster Source Search",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: exact source-date/root search plus event-boundary replay. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision Buckets", ""])
    for key, value in sorted(decision_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Replay Buckets", ""])
    for key, value in sorted(replay_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Build source-safe proxy controls for unrepaired micro-clusters.",
            "- Use variant/suffixed candidates only as source-semantics leads unless they repair event-boundary records and pass parser audit.",
            "- Feed unrepaired source-search decisions into branch-local challenger boundaries only.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_requirements = read_jsonl(SOURCE_REQUIREMENT_LEDGER)
    source_join_rows = read_jsonl(SOURCE_JOIN_LEDGER)
    source_join_by_request = {str(row["request_id"]): row for row in source_join_rows}
    root_rows, root_file_rows = ALT.scan_depth_roots()
    candidate_rows = build_candidate_rows(source_requirements, root_file_rows)
    request_replay_rows = build_request_replays(candidate_rows, source_join_by_request)
    decision_rows = build_decisions(source_requirements, candidate_rows, request_replay_rows)
    decision_counts = dict(sorted(Counter(row["source_search_decision_bucket"] for row in decision_rows).items()))
    replay_counts = dict(sorted(Counter(row["candidate_replay_bucket"] for row in request_replay_rows).items()))
    counts = {
        "source_requirement_input_rows": len(source_requirements),
        "source_join_input_rows": len(source_join_rows),
        "searched_root_rows": len(root_rows),
        "unique_depth_files_seen": len(root_file_rows),
        "candidate_file_rows": len(candidate_rows),
        "primary_exact_candidate_rows": sum(1 for row in candidate_rows if row["candidate_relation"] == "primary_expected_exact_file"),
        "alternate_exact_candidate_rows": sum(1 for row in candidate_rows if row["candidate_relation"] == "alternate_exact_filename_file"),
        "same_symbol_date_variant_candidate_rows": sum(
            1 for row in candidate_rows if row["candidate_relation"] == "same_symbol_date_suffix_or_variant_file"
        ),
        "request_replay_rows": len(request_replay_rows),
        "repairing_replay_rows": sum(1 for row in request_replay_rows if row.get("candidate_repairs_source_silence")),
        "decision_rows": len(decision_rows),
        "bucket_rows": 0,
        "question_rows": 0,
        "root_error_count": sum(int(row.get("error_count") or 0) for row in root_rows),
    }
    bucket_rows = build_bucket_rows(decision_rows, request_replay_rows)
    counts["bucket_rows"] = len(bucket_rows)
    question_rows = build_questions(decision_rows, bucket_rows, counts)
    counts["question_rows"] = len(question_rows)
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_source_search_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SOURCE_SILENCE_MICROCLUSTER_EXACT_SOURCE_SEARCH_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "source_search_decision_bucket_counts": decision_counts,
        "candidate_replay_bucket_counts": replay_counts,
        "search_roots": [str(root) for root in ALT.SEARCH_ROOTS],
        "not_completion": "This exact source-search packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "build source-safe proxy controls for unrepaired micro-clusters",
            "use source-search decisions in branch-local challenger boundaries only",
            "continue exact source acquisition only where new owned/current/free roots are discovered",
        ],
    }
    write_jsonl(ROOT_SCAN_LEDGER, root_rows)
    write_jsonl(CANDIDATE_LEDGER, candidate_rows)
    write_jsonl(REQUEST_REPLAY_LEDGER, request_replay_rows)
    write_jsonl(DECISION_LEDGER, decision_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, decision_counts)
    write_summary(generated_utc, counts, decision_counts, replay_counts)
    print(json.dumps({"ok": True, "counts": counts, "decision_counts": decision_counts, "replay_counts": replay_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

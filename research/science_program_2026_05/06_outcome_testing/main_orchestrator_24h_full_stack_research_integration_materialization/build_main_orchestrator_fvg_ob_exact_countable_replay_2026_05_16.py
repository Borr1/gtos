from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
AUDIT_INPUT = Path("shadow_logs/fvg_ob_confluence_audit.jsonl")
CONFLUENCE_INPUT = Path("shadow_logs/fvg_ob_confluence.jsonl")
BACKFILL_INPUT = Path("research/program_control/FVG_OB_CONFLUENCE_SOURCE_GEOMETRY_BACKFILL_2026-05-12.json")
SUMMARY_INPUT = Path("research/program_control/LTO008_FVG_OB_CONFLUENCE_AUDIT_2026-05-05.json")
EXACT_STATUSES = {
    "FVG_OB_EXACT_BOUNDS_CAPTURED",
    "FVG_EXACT_BOUNDS_CAPTURED",
    "OB_EXACT_BOUNDS_CAPTURED",
}
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
ROUTE_DIR = Path(__file__).resolve().parent


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("/", "\\")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_utc(value: Any) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iter_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append((line_no, row))
    return rows


def stable_id(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:32]


def proxy_r_for_path(status: Any) -> float | None:
    status_text = str(status or "")
    if status_text == "ENTRY_TOUCHED_THEN_TP1":
        return 1.5
    if status_text == "ENTRY_TOUCHED_THEN_SL":
        return -1.0
    if status_text.startswith("NO_FILL_") or status_text == "NO_ENTRY_TOUCH_BY_ASOF":
        return 0.0
    return None


def latest_audit_rows() -> list[tuple[int, dict[str, Any]]]:
    latest: dict[str, tuple[tuple[datetime, datetime, int], int, dict[str, Any]]] = {}
    for line_no, row in iter_jsonl(REPO_ROOT / AUDIT_INPUT):
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        order = (
            parse_utc(row.get("latest_resolution_asof_utc")),
            parse_utc(row.get("created_at_utc")),
            line_no,
        )
        previous = latest.get(candidate_id)
        if previous is None or order >= previous[0]:
            latest[candidate_id] = (order, line_no, row)
    return [(line_no, row) for _order, line_no, row in latest.values()]


def summarize(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "mean": None, "positive": 0, "negative": 0, "zero": 0, "min": None, "max": None}
    return {
        "count": len(values),
        "mean": sum(values) / len(values),
        "positive": sum(1 for value in values if value > 0),
        "negative": sum(1 for value in values if value < 0),
        "zero": sum(1 for value in values if value == 0),
        "min": min(values),
        "max": max(values),
    }


def eligibility(row: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if row.get("fvg_ob_source_capture_status") in EXACT_STATUSES:
        reasons.append("exact_fvg_or_ob_bounds_captured")
    if row.get("duplicate_aware_counting_status") == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY":
        reasons.append("duplicate_aware_countable_primary_opportunity")
    return bool(reasons), reasons


def split_summary(rows: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    noncomputable_counts: Counter[tuple[Any, ...]] = Counter()
    for row in rows:
        key = tuple(tuple(row.get(field)) if isinstance(row.get(field), list) else row.get(field) for field in fields)
        if row.get("proxy_r") is None:
            noncomputable_counts[key] += 1
            continue
        groups[key].append(float(row["proxy_r"]))
    keys = set(groups) | set(noncomputable_counts)
    output = []
    for key in sorted(keys, key=lambda item: tuple(str(part) for part in item)):
        output.append(
            {
                "split_fields": fields,
                "split_key": {field: list(value) if isinstance(value, tuple) else value for field, value in zip(fields, key)},
                "proxy_r_summary": summarize(groups.get(key, [])),
                "noncomputable_rows": noncomputable_counts.get(key, 0),
                "safe_flags": SAFE_FLAGS,
            }
        )
    return output


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def artifact_record(label: str, path: Path) -> dict[str, Any]:
    return {
        "label": label,
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256(path) if path.exists() else None,
    }


def main() -> None:
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    source_sha = sha256(REPO_ROOT / AUDIT_INPUT)
    confluence_sha = sha256(REPO_ROOT / CONFLUENCE_INPUT)
    backfill_sha = sha256(REPO_ROOT / BACKFILL_INPUT)
    summary_sha = sha256(REPO_ROOT / SUMMARY_INPUT)

    all_latest_rows = latest_audit_rows()
    eligible_rows: list[dict[str, Any]] = []
    noncomputable_rows: list[dict[str, Any]] = []
    proxy_values: list[float] = []
    exact_bounds_total = 0
    duplicate_countable_total = 0

    for source_line_no, row in sorted(all_latest_rows, key=lambda item: (str(item[1].get("decision_time_utc") or ""), str(item[1].get("candidate_id") or ""))):
        is_eligible, reasons = eligibility(row)
        if row.get("fvg_ob_source_capture_status") in EXACT_STATUSES:
            exact_bounds_total += 1
        if row.get("duplicate_aware_counting_status") == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY":
            duplicate_countable_total += 1
        if not is_eligible:
            continue

        bucket = row.get("bucket_state") or {}
        geometry = row.get("geometry_state") or {}
        proxy_r = proxy_r_for_path(row.get("path_outcome_status"))
        ledger_row = {
            "row_id": "MAIN-ORCH24-FVG-OB-EXACT-COUNTABLE-" + stable_id(row.get("candidate_id"), row.get("latest_resolution_asof_utc"), source_line_no),
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "broker_symbol": row.get("broker_symbol"),
            "side": row.get("side"),
            "framework": row.get("framework"),
            "session": row.get("session"),
            "kill_zone": row.get("kill_zone"),
            "decision_time_utc": row.get("decision_time_utc"),
            "latest_resolution_asof_utc": row.get("latest_resolution_asof_utc"),
            "source_line_no": source_line_no,
            "bucket": bucket.get("bucket"),
            "relation_state": bucket.get("relation_state"),
            "fvg_ob_source_capture_status": row.get("fvg_ob_source_capture_status"),
            "duplicate_aware_counting_status": row.get("duplicate_aware_counting_status"),
            "eligibility_reasons": reasons,
            "path_outcome_status": row.get("path_outcome_status"),
            "path_label": row.get("path_label"),
            "proxy_r": proxy_r,
            "exact_r": None,
            "fvg_bounds_captured": isinstance(geometry.get("fvg_bounds"), dict),
            "ob_bounds_captured": isinstance(geometry.get("ob_bounds"), dict),
            "scoreability_boundary": "candidate_path_proxy_only; FVG_OB strategy scorer not implemented and standalone FVG entry/lock metadata remains missing",
            "source_file": str(AUDIT_INPUT),
            "source_sha256": source_sha,
            "input_hashes": {
                str(AUDIT_INPUT): source_sha,
                str(CONFLUENCE_INPUT): confluence_sha,
                str(BACKFILL_INPUT): backfill_sha,
                str(SUMMARY_INPUT): summary_sha,
            },
            "safe_flags": SAFE_FLAGS,
        }
        eligible_rows.append(ledger_row)
        if proxy_r is None:
            noncomputable_rows.append(
                {
                    "row_id": ledger_row["row_id"],
                    "candidate_id": ledger_row["candidate_id"],
                    "path_outcome_status": ledger_row["path_outcome_status"],
                    "eligibility_reasons": reasons,
                    "artifact_paths_checked": [str(AUDIT_INPUT), str(CONFLUENCE_INPUT), str(BACKFILL_INPUT), str(SUMMARY_INPUT)],
                    "input_hashes": ledger_row["input_hashes"],
                    "missing_fields": ["unambiguous_target_stop_path_order", "standalone_fvg_entry_or_lock_metadata_for_confluence_strategy"],
                    "why_no_weaker_proxy_r": "Path outcome is ambiguous or unresolved; assigning +1.5/-1/0 would invent event ordering not present in the source row.",
                    "owner": "forward_capture_or_ltf_path_order_repair",
                    "decision": "PRESERVE_AS_CURRENT_SNAPSHOT_DEPENDENCY_NO_PROMOTION",
                    "safe_flags": SAFE_FLAGS,
                }
            )
        else:
            proxy_values.append(proxy_r)

    split_rows: list[dict[str, Any]] = []
    for fields in (
        ["bucket"],
        ["fvg_ob_source_capture_status"],
        ["duplicate_aware_counting_status"],
        ["symbol"],
        ["side"],
        ["bucket", "fvg_ob_source_capture_status"],
        ["eligibility_reasons"],
    ):
        split_rows.extend(split_summary(eligible_rows, fields))

    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "decision": "REPLAY_EXACT_COUNTABLE_SUBSET_ONLY_NO_PROMOTION",
        "all_latest_audit_candidates": len(all_latest_rows),
        "exact_bounds_captured_rows_all_latest": exact_bounds_total,
        "duplicate_aware_countable_rows_all_latest": duplicate_countable_total,
        "eligible_union_rows": len(eligible_rows),
        "proxy_r_rows": len(proxy_values),
        "noncomputable_rows": len(noncomputable_rows),
        "proxy_r_summary": summarize(proxy_values),
        "path_outcome_counts": dict(Counter(str(row.get("path_outcome_status")) for row in eligible_rows)),
        "bucket_counts": dict(Counter(str(row.get("bucket")) for row in eligible_rows)),
        "source_capture_status_counts": dict(Counter(str(row.get("fvg_ob_source_capture_status")) for row in eligible_rows)),
        "duplicate_aware_counting_counts": dict(Counter(str(row.get("duplicate_aware_counting_status")) for row in eligible_rows)),
        "interpretation": "FVG/OB confluence remains source-capture/replay intelligence only. Current computable proxy rows are candidate-path proxy rows for exact-bounds or duplicate-aware-countable rows, not a standalone FVG/OB strategy score.",
        "safe_flags": SAFE_FLAGS,
    }

    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_EXACT_COUNTABLE_REPLAY_LEDGER_{DATE}.jsonl"
    noncomputable_path = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_EXACT_COUNTABLE_NONCOMPUTABLE_PROOF_LEDGER_{DATE}.jsonl"
    split_path = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_EXACT_COUNTABLE_SPLIT_SUMMARY_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_EXACT_COUNTABLE_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_EXACT_COUNTABLE_OUTPUT_MANIFEST_{DATE}.json"

    write_jsonl(ledger_path, eligible_rows)
    write_jsonl(noncomputable_path, noncomputable_rows)
    write_jsonl(split_path, split_rows)
    write_json(summary_path, summary)
    manifest = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "artifact_count": 4,
        "artifacts": [
            artifact_record("fvg_ob_exact_countable_replay_ledger", ledger_path),
            artifact_record("noncomputable_proof_ledger", noncomputable_path),
            artifact_record("split_summary", split_path),
            artifact_record("summary_json", summary_path),
        ],
        "input_artifacts": [
            artifact_record("fvg_ob_confluence_audit", REPO_ROOT / AUDIT_INPUT),
            artifact_record("fvg_ob_confluence_forward_rows", REPO_ROOT / CONFLUENCE_INPUT),
            artifact_record("fvg_ob_geometry_backfill_summary", REPO_ROOT / BACKFILL_INPUT),
            artifact_record("lto008_audit_summary", REPO_ROOT / SUMMARY_INPUT),
        ],
        "safe_flags": SAFE_FLAGS,
    }
    write_json(manifest_path, manifest)
    print(json.dumps({"ok": True, "eligible_union_rows": len(eligible_rows), "proxy_r_rows": len(proxy_values), "mean": summary["proxy_r_summary"]["mean"]}, sort_keys=True))


if __name__ == "__main__":
    main()

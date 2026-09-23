from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
REPO = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
FIELD_AVAILABILITY_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_FIELD_AVAILABILITY_LEDGER_{DATE}.jsonl"
SOURCE_PATHS = [
    Path("shadow_logs/strategy_follow_candidates.jsonl"),
    Path("shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl"),
    Path("shadow_logs/candidate_features_log.jsonl"),
    Path("shadow_logs/candidate_path_follow.jsonl"),
    Path("shadow_logs/candidate_ltf_path_order.jsonl"),
    Path("shadow_logs/fvg_ob_confluence.jsonl"),
    Path("shadow_logs/fvg_ob_confluence_audit.jsonl"),
]
REQUIRED_FIELD_ALIASES = {
    "symbol": ("symbol", "broker_symbol"),
    "route_session": ("route_session", "session", "session_tag", "kill_zone"),
    "horizon_id": ("horizon_id",),
    "source_component": ("source_component", "strategy_family", "framework", "source_file"),
    "primitive_flag": ("primitive_flag",),
    "proxy_r_class": ("proxy_r_class",),
    "target_stop_order_class": ("target_stop_order_class",),
}
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_ADAPTER_SPEC_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_ADAPTER_SPEC_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_ADAPTER_SPEC_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def field_counts_for_source(path: Path, aliases: tuple[str, ...]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            for alias in aliases:
                if normalized(row.get(alias)):
                    counts[alias] += 1
    return dict(sorted(counts.items()))


def adapter_resolution(required_field: str, alias_counts: dict[str, int]) -> str:
    if alias_counts.get(required_field, 0) > 0:
        return "DIRECT_FIELD_PRESENT"
    if any(count > 0 for alias, count in alias_counts.items() if alias != required_field):
        return "ALIAS_AVAILABLE_NEEDS_ADAPTER_MAPPING"
    return "MISSING_REQUIRES_UPSTREAM_CAPTURE"


def build() -> dict[str, Any]:
    availability_rows = read_jsonl(FIELD_AVAILABILITY_LEDGER)
    rows_by_source = {row["source_path"]: row for row in availability_rows}
    spec_rows: list[dict[str, Any]] = []
    for source_path in SOURCE_PATHS:
        source_key = str(source_path).replace("\\", "/")
        availability = rows_by_source.get(source_key, {})
        absolute_path = REPO / source_path
        for required_field, aliases in REQUIRED_FIELD_ALIASES.items():
            alias_counts = field_counts_for_source(absolute_path, aliases)
            spec_rows.append(
                {
                    "adapter_spec_row_id": f"MAIN-ORCH48-NUMERIC-ROUTER-CATALOG-ADAPTER-SPEC-{len(spec_rows) + 1:04d}",
                    "source_path": source_key,
                    "source_exists": absolute_path.exists(),
                    "source_rows_scanned": availability.get("rows_scanned", 0),
                    "required_event_field": required_field,
                    "alias_candidates": list(aliases),
                    "alias_presence_counts": alias_counts,
                    "adapter_resolution": adapter_resolution(required_field, alias_counts),
                    "adapter_action": "copy_direct_field"
                    if alias_counts.get(required_field, 0) > 0
                    else (
                        "map_existing_alias_to_contract_field"
                        if any(count > 0 for alias, count in alias_counts.items() if alias != required_field)
                        else "add_upstream_capture_or_derive_before_evaluator_use"
                    ),
                    "runtime_score_allowed": False,
                    "runtime_candidate_use_permitted": False,
                    "candidate_use_allowed_now": False,
                    "unconditional_scalar_use_allowed": False,
                    "replay_r_reference_counted_as_new_main_result": False,
                }
            )
    write_jsonl(OUTPUT_LEDGER, spec_rows)

    resolution_counts = dict(sorted(Counter(row["adapter_resolution"] for row in spec_rows).items()))
    field_resolution_counts = {
        field: dict(
            sorted(
                Counter(
                    row["adapter_resolution"] for row in spec_rows if row["required_event_field"] == field
                ).items()
            )
        )
        for field in REQUIRED_FIELD_ALIASES
    }
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_ADAPTER_SPEC",
        "schema_version": "main_orch48_numeric_router_catalog_event_adapter_spec_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_field_availability_ledger": {
            "path": str(FIELD_AVAILABILITY_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rows": len(availability_rows),
            "sha256": sha256_path(FIELD_AVAILABILITY_LEDGER),
        },
        "adapter_spec_rows": len(spec_rows),
        "source_count": len(SOURCE_PATHS),
        "required_field_count": len(REQUIRED_FIELD_ALIASES),
        "adapter_resolution_counts": resolution_counts,
        "field_resolution_counts": field_resolution_counts,
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in spec_rows),
        "runtime_candidate_use_permitted_rows": sum(
            bool(row.get("runtime_candidate_use_permitted")) for row in spec_rows
        ),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in spec_rows),
        "unconditional_scalar_use_allowed_rows": sum(
            bool(row.get("unconditional_scalar_use_allowed")) for row in spec_rows
        ),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in spec_rows
        ),
        "implementation_effect": {
            "runtime_or_live_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": summary["route_id"],
        "generated_utc": summary["generated_utc"],
        "outputs": [
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "bytes": path.stat().st_size,
                "lines": count_lines(path),
                "sha256": sha256_path(path),
            }
            for path in outputs
        ],
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return {
        "ok": True,
        "route_id": summary["route_id"],
        "adapter_spec_rows": summary["adapter_spec_rows"],
        "adapter_resolution_counts": summary["adapter_resolution_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))

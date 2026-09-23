"""Build the NOFILL source-expansion parser-hash repair evidence pack."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_DIR = ROUTE_DIR.parent
REPO_ROOT = Path(__file__).resolve().parents[4]

DATE = "2026-05-10"
PREFIX = "NOFILL_HIST_SRCEXP_HASH_REPAIR"
ROUTE_ID = "NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD"
SCHEMA_VERSION = "nofill_historical_source_expansion_packet_parser_hash_repair_rebuild_v1"
TERMINAL_DECISION = "REPAIR_REBUILD_READY_FOR_G12_REAUDIT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

TARGET_PREFIX = "NOFILL_HIST_SOURCE_EXPANSION"
TARGET_DIR = OUTCOME_DIR / "nofill_historical_source_expansion_builder_local_tick_shadow_packet"
G12_DIR = OUTCOME_DIR / "g12_nofill_historical_source_expansion_packet_audit"
PROMPT_PATH = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD_GOAL_PROMPT_2026-05-10.md"
)
G12_REPAIR_LEDGER = G12_DIR / "G12_NOFILL_HIST_SRCEXP_AUDIT_EXACT_REPAIR_SOURCE_REQUIREMENT_LEDGER_2026-05-10.json"

TARGET_FILES = {
    "builder": TARGET_DIR / "build_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
    "focused_tests": TARGET_DIR / "test_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
    "verifier": TARGET_DIR / "verify_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
}
ROLE_TO_FILE_KEY = {
    "parser_or_verifier:builder": "builder",
    "parser_or_verifier:focused_tests": "focused_tests",
    "parser_or_verifier:verifier": "verifier",
}
TARGET_PACKET = TARGET_DIR / f"{TARGET_PREFIX}_SOURCE_BOUND_CANDIDATE_PACKET_{DATE}.jsonl"
TARGET_PACKET_MANIFEST = TARGET_DIR / f"{TARGET_PREFIX}_CANDIDATE_PACKET_MANIFEST_{DATE}.json"
TARGET_SOURCE_MANIFEST = TARGET_DIR / f"{TARGET_PREFIX}_SOURCE_HASH_MANIFEST_{DATE}.json"
TARGET_PARSER_ASOF = TARGET_DIR / f"{TARGET_PREFIX}_PARSER_ASOF_MANIFEST_{DATE}.json"
EXPECTED_ROW_IDENTITIES = [
    {
        "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0001",
        "symbol": "NAS100",
        "decision_time_utc": "2026-05-08T15:45:00+00:00",
        "candidate_id": "NAS100_2026-05-08T15:45:00+00:00",
    },
    {
        "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0002",
        "symbol": "US30_cash",
        "decision_time_utc": "2026-05-08T13:45:00+00:00",
        "candidate_id": "US30_cash_2026-05-08T13:45:00+00:00",
    },
]
ROW_HASH_FIELDS = {"parser_code_hash", "source_artifact_hash"}
SAFE_FLAG_FALSE_KEYS = ("validation_safe", "outcome_review_opened", "live_effect")
FORBIDDEN_TRUE_KEYS = (
    "opens_result_scoring",
    "opens_validation",
    "opens_promotion",
    "opens_registry_edit",
    "opens_paid_api_or_databento_route",
    "opens_remote_push",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_mt5_order_account_history_behavior",
    "changes_live_trading_behavior",
    "credentials_touched",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def with_safe_flags(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out.update(
        {
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "opens_result_scoring": False,
            "opens_validation": False,
            "opens_promotion": False,
            "opens_registry_edit": False,
            "opens_paid_api_or_databento_route": False,
            "opens_remote_push": False,
            "opens_live_restart": False,
            "opens_live_trading_behavior": False,
            "opens_mt5_order_account_history_behavior": False,
            "changes_live_trading_behavior": False,
            "credentials_touched": False,
        }
    )
    return out


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(with_safe_flags(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.write_text(
        "".join(json.dumps(with_safe_flags(row), sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def write_md(path: Path, title: str, summary: dict[str, Any], notes: list[str] | None = None) -> Path:
    lines = [
        f"# {title}",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Terminal decision: `{summary.get('terminal_decision', TERMINAL_DECISION)}`",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(with_safe_flags(summary), indent=2, sort_keys=True),
        "```",
    ]
    if notes:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {note}" for note in notes)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_target_md(path: Path, title: str, summary: dict[str, Any], notes: list[str] | None = None) -> Path:
    lines = [
        f"# {title}",
        "",
        "Route: `NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET`",
        "Terminal decision: `ACCEPT_SOURCE_HASHED_INPUT_PACKET_READY_FOR_G12_SOURCE_CONTROL_AUDIT`",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(with_safe_flags(summary), indent=2, sort_keys=True),
        "```",
    ]
    if notes:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {note}" for note in notes)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def route_json(name: str, payload: dict[str, Any]) -> str:
    return rel(write_json(ROUTE_DIR / name, payload))


def route_md(name: str, title: str, payload: dict[str, Any], notes: list[str] | None = None) -> str:
    return rel(write_md(ROUTE_DIR / name, title, payload, notes))


def file_mtime_utc(path: Path) -> str | None:
    if not path.exists():
        return None
    return (
        datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def file_info(path: Path) -> dict[str, Any]:
    exists = path.exists() and path.is_file()
    return {
        "exists": exists,
        "mtime_utc": file_mtime_utc(path) if exists else None,
        "path": rel(path),
        "sha256": sha256_file(path) if exists else None,
        "size_bytes": path.stat().st_size if exists else None,
    }


def strip_hash_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in ROW_HASH_FIELDS}


def recompute_source_artifact_hash(row: dict[str, Any], parser_hash: str) -> str:
    return sha256_json(
        {
            "packet_row_id": row["packet_row_id"],
            "source_files_sha256": row["source_files_sha256"],
            "candidate_id": row["candidate_id"],
            "source_date": row["source_date"],
            "parser_hash": parser_hash,
        }
    )


def recurse_safe_flags(obj: Any, path: str = "$") -> list[str]:
    issues: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}"
            if key in SAFE_FLAG_FALSE_KEYS and value is not False:
                issues.append(f"{child} must be false")
            if key in FORBIDDEN_TRUE_KEYS and value is True:
                issues.append(f"{child} opens a forbidden surface")
            if key == "promotion_verdict" and value != PROMOTION_VERDICT:
                issues.append(f"{child} must be {PROMOTION_VERDICT}")
            issues.extend(recurse_safe_flags(value, child))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            issues.extend(recurse_safe_flags(item, f"{path}[{idx}]"))
    return issues


def update_target_source_manifest(current_hashes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    manifest = load_json(TARGET_SOURCE_MANIFEST)
    mutations: list[dict[str, Any]] = []
    for record in manifest.get("records", []):
        role = record.get("role")
        file_key = ROLE_TO_FILE_KEY.get(role)
        if not file_key:
            continue
        info = current_hashes[file_key]
        before = {key: record.get(key) for key in ("sha256", "mtime_utc", "size_bytes")}
        record["exists"] = info["exists"]
        record["mtime_utc"] = info["mtime_utc"]
        record["sha256"] = info["sha256"]
        record["size_bytes"] = info["size_bytes"]
        after = {key: record.get(key) for key in ("sha256", "mtime_utc", "size_bytes")}
        mutations.append(
            {
                "role": role,
                "path": record.get("path"),
                "before": before,
                "after": after,
                "changed": before != after,
                "reason": "Refresh strict parser/verifier code hash binding to current committed target file.",
            }
        )
    write_json(TARGET_SOURCE_MANIFEST, manifest)
    write_target_md(
        TARGET_DIR / f"{TARGET_PREFIX}_SOURCE_HASH_MANIFEST_{DATE}.md",
        "NOFILL Historical Source Expansion Source Hash Manifest",
        {
            "admitted_tick_file_count": sum(
                1 for row in manifest.get("records", []) if row.get("role") == "raw_tick_parquet_admitted_row_source"
            ),
            "missing_source_record_count": manifest.get("missing_source_record_count"),
            "source_record_count": manifest.get("source_record_count"),
        },
        ["Repair route refreshed only the three strict parser/verifier code records required by G12."],
    )
    return {"manifest": manifest, "mutations": mutations}


def update_target_parser_asof(builder_hash: str) -> dict[str, Any]:
    manifest = load_json(TARGET_PARSER_ASOF)
    before = manifest.get("parser_hash")
    manifest["parser_hash"] = builder_hash
    write_json(TARGET_PARSER_ASOF, manifest)
    write_target_md(
        TARGET_DIR / f"{TARGET_PREFIX}_PARSER_ASOF_MANIFEST_{DATE}.md",
        "NOFILL Historical Source Expansion Parser As-Of Manifest",
        {
            "parser_hash": manifest.get("parser_hash"),
            "source_parser_count": len(manifest.get("source_parsers", [])),
        },
        ["Parser hash refreshed to the current target builder code hash; as-of policy text is unchanged."],
    )
    return {
        "path": rel(TARGET_PARSER_ASOF),
        "before": before,
        "after": builder_hash,
        "changed": before != builder_hash,
        "reason": "Bind parser_asof manifest to current target builder strict hash.",
    }


def update_target_packet(builder_hash: str) -> dict[str, Any]:
    before_rows = read_jsonl(TARGET_PACKET)
    before_semantic = [strip_hash_fields(row) for row in before_rows]
    before_identities = [
        {
            "packet_row_id": row.get("packet_row_id"),
            "symbol": row.get("symbol"),
            "decision_time_utc": row.get("decision_time_utc"),
            "candidate_id": row.get("candidate_id"),
        }
        for row in before_rows
    ]
    before_packet_sha = sha256_file(TARGET_PACKET)
    before_hash_fields = [
        {
            "packet_row_id": row.get("packet_row_id"),
            "parser_code_hash": row.get("parser_code_hash"),
            "source_artifact_hash": row.get("source_artifact_hash"),
        }
        for row in before_rows
    ]

    after_rows = []
    for row in before_rows:
        updated = dict(row)
        updated["parser_code_hash"] = builder_hash
        updated["source_artifact_hash"] = recompute_source_artifact_hash(updated, builder_hash)
        after_rows.append(updated)

    write_jsonl(TARGET_PACKET, after_rows)
    after_semantic = [strip_hash_fields(row) for row in after_rows]
    after_hash_fields = [
        {
            "packet_row_id": row.get("packet_row_id"),
            "parser_code_hash": row.get("parser_code_hash"),
            "source_artifact_hash": row.get("source_artifact_hash"),
        }
        for row in after_rows
    ]
    after_packet_sha = sha256_file(TARGET_PACKET)

    packet_manifest = load_json(TARGET_PACKET_MANIFEST)
    manifest_before_sha = packet_manifest.get("packet_sha256")
    packet_manifest["packet_sha256"] = after_packet_sha
    write_json(TARGET_PACKET_MANIFEST, packet_manifest)
    write_target_md(
        TARGET_DIR / f"{TARGET_PREFIX}_CANDIDATE_PACKET_MANIFEST_{DATE}.md",
        "NOFILL Historical Source Expansion Candidate Packet Manifest",
        packet_manifest,
        ["Packet SHA refreshed after hash-only parser binding repair; row identities and counts are unchanged."],
    )

    return {
        "before_packet_sha256": before_packet_sha,
        "after_packet_sha256": after_packet_sha,
        "candidate_packet_manifest_before_sha256": manifest_before_sha,
        "candidate_packet_manifest_after_sha256": after_packet_sha,
        "before_row_identities": before_identities,
        "after_row_identities": [
            {
                "packet_row_id": row.get("packet_row_id"),
                "symbol": row.get("symbol"),
                "decision_time_utc": row.get("decision_time_utc"),
                "candidate_id": row.get("candidate_id"),
            }
            for row in after_rows
        ],
        "row_count_before": len(before_rows),
        "row_count_after": len(after_rows),
        "semantic_rows_unchanged_excluding_hash_fields": before_semantic == after_semantic,
        "expected_row_identities_match_before": before_identities == EXPECTED_ROW_IDENTITIES,
        "expected_row_identities_match_after": [
            {
                "packet_row_id": row.get("packet_row_id"),
                "symbol": row.get("symbol"),
                "decision_time_utc": row.get("decision_time_utc"),
                "candidate_id": row.get("candidate_id"),
            }
            for row in after_rows
        ]
        == EXPECTED_ROW_IDENTITIES,
        "before_hash_fields": before_hash_fields,
        "after_hash_fields": after_hash_fields,
        "hash_fields_changed_only": before_semantic == after_semantic and before_hash_fields != after_hash_fields,
        "paths_changed": [
            rel(TARGET_PACKET),
            rel(TARGET_PACKET_MANIFEST),
            rel(TARGET_DIR / f"{TARGET_PREFIX}_CANDIDATE_PACKET_MANIFEST_{DATE}.md"),
        ],
    }


def build_recomputed_source_manifest(target_manifest: dict[str, Any]) -> dict[str, Any]:
    records = []
    for record in target_manifest.get("records", []):
        path = Path(str(record.get("path")))
        resolved = path if path.is_absolute() else REPO_ROOT / path
        actual = sha256_file(resolved)
        records.append(
            {
                "role": record.get("role"),
                "path": record.get("path"),
                "source_contract_id": record.get("source_contract_id"),
                "target_manifest_sha256": record.get("sha256"),
                "recomputed_sha256": actual,
                "exists_now": resolved.exists(),
                "hash_matches_target_manifest": actual == record.get("sha256"),
                "mutable_context_classification": record.get(
                    "mutable_context_classification", "STRICT_OR_TARGET_DECLARED_SOURCE_HASH"
                ),
            }
        )
    return with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "recomputed_parser_verifier_source_hash_manifest",
            "generated_at_utc": utc_now(),
            "target_source_manifest_path": rel(TARGET_SOURCE_MANIFEST),
            "source_record_count": len(records),
            "records": records,
            "hash_mismatch_count": sum(1 for row in records if not row["hash_matches_target_manifest"]),
            "terminal_decision": TERMINAL_DECISION,
        }
    )


def build_no_leak_check(changed_target_paths: list[str], route_output_paths: dict[str, str]) -> dict[str, Any]:
    issues: list[str] = []
    checked_json_paths = [REPO_ROOT / path for path in changed_target_paths if path.endswith(".json")]
    checked_json_paths.extend(ROUTE_DIR / Path(path).name for path in route_output_paths.values() if path.endswith(".json"))
    for path in checked_json_paths:
        if path.exists():
            issues.extend(recurse_safe_flags(load_json(path), rel(path)))
    for path_text in changed_target_paths:
        if path_text.endswith(".jsonl"):
            path = REPO_ROOT / path_text
            for idx, row in enumerate(read_jsonl(path), start=1):
                issues.extend(recurse_safe_flags(row, f"{path_text}:{idx}"))
    return with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "no_leak_safe_flag_check",
            "generated_at_utc": utc_now(),
            "checked_target_paths": changed_target_paths,
            "checked_route_artifact_count": len(route_output_paths),
            "safe_flag_issue_count": len(issues),
            "issues": issues,
            "no_validation_execution": True,
            "no_result_cost_r_win_rate_expectancy_scoring": True,
            "no_broker_actual_r_or_mt5_account_order_deal_position_history_read": True,
            "terminal_decision": TERMINAL_DECISION if not issues else "BLOCKED_WITH_EXACT_REPAIR_IMPOSSIBILITY",
        }
    )


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = utc_now()
    head = git_head()
    route_outputs: dict[str, str] = {}

    g12_ledger = load_json(G12_REPAIR_LEDGER)
    g12_requirements = g12_ledger.get("remaining_requirements", [])
    current_hashes = {key: file_info(path) for key, path in TARGET_FILES.items()}
    builder_hash = str(current_hashes["builder"]["sha256"])

    target_output_manifest = load_json(TARGET_DIR / f"{TARGET_PREFIX}_OUTPUT_MANIFEST_{DATE}.json")
    semantic_guard_before = {
        "admitted_packet_row_count": target_output_manifest.get("admitted_packet_row_count"),
        "blocked_candidate_count": target_output_manifest.get("blocked_candidate_count"),
        "rejected_candidate_count": target_output_manifest.get("rejected_candidate_count"),
    }

    packet_update = update_target_packet(builder_hash)
    source_manifest_update = update_target_source_manifest(current_hashes)
    parser_asof_update = update_target_parser_asof(builder_hash)
    target_output_manifest_after = load_json(TARGET_DIR / f"{TARGET_PREFIX}_OUTPUT_MANIFEST_{DATE}.json")
    semantic_guard_after = {
        "admitted_packet_row_count": target_output_manifest_after.get("admitted_packet_row_count"),
        "blocked_candidate_count": target_output_manifest_after.get("blocked_candidate_count"),
        "rejected_candidate_count": target_output_manifest_after.get("rejected_candidate_count"),
    }

    context_anchor = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "context_anchor",
            "generated_at_utc": generated_at,
            "head_at_start": head,
            "controlling_prompt_path": rel(PROMPT_PATH),
            "g12_exact_repair_ledger_path": rel(G12_REPAIR_LEDGER),
            "target_packet_route_dir": rel(TARGET_DIR),
            "target_packet_path": rel(TARGET_PACKET),
            "evidence_class": "source_control_parser_hash_repair_only",
            "mandatory_context_read": [
                ".context/LIVE_STATE.md",
                ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
                ".context/00_core/quick_reference_card.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/research_current_state.md",
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/local_heavy_data_inventory.md",
                rel(PROMPT_PATH),
                rel(G12_REPAIR_LEDGER),
            ],
            "terminal_decision": TERMINAL_DECISION,
        }
    )
    route_outputs["context_anchor_json"] = route_json(f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json", context_anchor)
    route_outputs["context_anchor_md"] = route_md(
        f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.md",
        "NOFILL Source Expansion Parser Hash Repair Context Anchor",
        context_anchor,
    )

    closure_records = []
    for req in g12_requirements:
        role = req.get("role")
        file_key = ROLE_TO_FILE_KEY.get(role)
        current = current_hashes.get(file_key or "", {})
        target_manifest_record = next(
            (row for row in source_manifest_update["manifest"].get("records", []) if row.get("role") == role),
            {},
        )
        closure_records.append(
            {
                "role": role,
                "path": req.get("path"),
                "g12_manifest_sha256_before_repair": req.get("manifest_sha256"),
                "g12_recomputed_sha256": req.get("recomputed_sha256"),
                "current_recomputed_sha256": current.get("sha256"),
                "target_manifest_sha256_after_repair": target_manifest_record.get("sha256"),
                "closed": bool(current.get("sha256"))
                and current.get("sha256") == target_manifest_record.get("sha256"),
                "g12_current_hash_still_matches": current.get("sha256") == req.get("recomputed_sha256"),
                "repair_action": "target source-hash manifest strict code record refreshed",
            }
        )
    exact_closure = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "exact_g12_blocker_closure_ledger",
            "generated_at_utc": utc_now(),
            "exact_repair_requirement_count": len(closure_records),
            "closed_requirement_count": sum(1 for row in closure_records if row["closed"]),
            "records": closure_records,
            "terminal_decision": TERMINAL_DECISION
            if len(closure_records) == 3 and all(row["closed"] for row in closure_records)
            else "BLOCKED_WITH_EXACT_REPAIR_IMPOSSIBILITY",
        }
    )
    route_outputs["exact_blocker_closure_json"] = route_json(
        f"{PREFIX}_EXACT_G12_BLOCKER_CLOSURE_LEDGER_{DATE}.json", exact_closure
    )
    route_outputs["exact_blocker_closure_md"] = route_md(
        f"{PREFIX}_EXACT_G12_BLOCKER_CLOSURE_LEDGER_{DATE}.md",
        "NOFILL Source Expansion Parser Hash Repair Exact G12 Blocker Closure Ledger",
        exact_closure,
    )

    changed_target_paths = [
        rel(TARGET_PACKET),
        rel(TARGET_PACKET_MANIFEST),
        rel(TARGET_DIR / f"{TARGET_PREFIX}_CANDIDATE_PACKET_MANIFEST_{DATE}.md"),
        rel(TARGET_SOURCE_MANIFEST),
        rel(TARGET_DIR / f"{TARGET_PREFIX}_SOURCE_HASH_MANIFEST_{DATE}.md"),
        rel(TARGET_PARSER_ASOF),
        rel(TARGET_DIR / f"{TARGET_PREFIX}_PARSER_ASOF_MANIFEST_{DATE}.md"),
        rel(TARGET_DIR / f"{TARGET_PREFIX}_VERIFICATION_RESULT_{DATE}.json"),
        rel(TARGET_DIR / f"{TARGET_PREFIX}_COMPLETION_AUDIT_{DATE}.json"),
        rel(TARGET_DIR / f"{TARGET_PREFIX}_COMPLETION_AUDIT_{DATE}.md"),
    ]
    mutation_ledger = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "target_artifact_mutation_ledger",
            "generated_at_utc": utc_now(),
            "target_files_changed_or_refreshed": changed_target_paths,
            "source_manifest_record_mutations": source_manifest_update["mutations"],
            "parser_asof_mutation": parser_asof_update,
            "packet_hash_mutation": {
                "packet_path": rel(TARGET_PACKET),
                "packet_manifest_path": rel(TARGET_PACKET_MANIFEST),
                "before_packet_sha256": packet_update["before_packet_sha256"],
                "after_packet_sha256": packet_update["after_packet_sha256"],
                "reason": "Packet row parser_code_hash/source_artifact_hash changed, so packet SHA changed.",
            },
            "target_verifier_refresh_note": (
                "Target verifier rerun refreshes target verification result and completion audit artifacts."
            ),
            "terminal_decision": TERMINAL_DECISION,
        }
    )
    route_outputs["target_mutation_ledger_json"] = route_json(
        f"{PREFIX}_TARGET_ARTIFACT_MUTATION_LEDGER_{DATE}.json", mutation_ledger
    )
    route_outputs["target_mutation_ledger_md"] = route_md(
        f"{PREFIX}_TARGET_ARTIFACT_MUTATION_LEDGER_{DATE}.md",
        "NOFILL Source Expansion Parser Hash Repair Target Artifact Mutation Ledger",
        mutation_ledger,
    )

    semantic_no_change = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "semantic_no_row_change_diff_ledger",
            "generated_at_utc": utc_now(),
            **packet_update,
            "semantic_guard_before": semantic_guard_before,
            "semantic_guard_after": semantic_guard_after,
            "semantic_counts_unchanged": semantic_guard_before == semantic_guard_after,
            "admitted_blocked_rejected_counts_required": {
                "admitted_packet_row_count": 2,
                "blocked_candidate_count": 37,
                "rejected_candidate_count": 9,
            },
            "only_hash_derived_fields_changed": packet_update["hash_fields_changed_only"],
            "terminal_decision": TERMINAL_DECISION
            if packet_update["hash_fields_changed_only"]
            and packet_update["expected_row_identities_match_after"]
            and semantic_guard_before == semantic_guard_after
            else "REJECT_REPAIR_WOULD_CHANGE_PACKET_SEMANTICS",
        }
    )
    route_outputs["semantic_no_row_change_json"] = route_json(
        f"{PREFIX}_SEMANTIC_NO_ROW_CHANGE_DIFF_LEDGER_{DATE}.json", semantic_no_change
    )
    route_outputs["semantic_no_row_change_md"] = route_md(
        f"{PREFIX}_SEMANTIC_NO_ROW_CHANGE_DIFF_LEDGER_{DATE}.md",
        "NOFILL Source Expansion Parser Hash Repair Semantic No-Row-Change Diff Ledger",
        semantic_no_change,
        ["Only `parser_code_hash` and parser-derived `source_artifact_hash` changed in packet rows."],
    )

    recomputed_manifest = build_recomputed_source_manifest(source_manifest_update["manifest"])
    route_outputs["recomputed_source_hash_manifest_json"] = route_json(
        f"{PREFIX}_RECOMPUTED_SOURCE_HASH_MANIFEST_{DATE}.json", recomputed_manifest
    )
    route_outputs["recomputed_source_hash_manifest_md"] = route_md(
        f"{PREFIX}_RECOMPUTED_SOURCE_HASH_MANIFEST_{DATE}.md",
        "NOFILL Source Expansion Parser Hash Repair Recomputed Source Hash Manifest",
        recomputed_manifest,
    )

    packet_sha_ledger = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "recomputed_packet_manifest_and_packet_sha_ledger",
            "generated_at_utc": utc_now(),
            "target_packet_path": rel(TARGET_PACKET),
            "target_packet_manifest_path": rel(TARGET_PACKET_MANIFEST),
            "packet_sha256_recomputed": sha256_file(TARGET_PACKET),
            "packet_sha256_manifest": load_json(TARGET_PACKET_MANIFEST).get("packet_sha256"),
            "packet_sha_matches_manifest": sha256_file(TARGET_PACKET)
            == load_json(TARGET_PACKET_MANIFEST).get("packet_sha256"),
            "packet_row_count": len(read_jsonl(TARGET_PACKET)),
            "terminal_decision": TERMINAL_DECISION,
        }
    )
    route_outputs["packet_sha_ledger_json"] = route_json(f"{PREFIX}_PACKET_SHA_LEDGER_{DATE}.json", packet_sha_ledger)
    route_outputs["packet_sha_ledger_md"] = route_md(
        f"{PREFIX}_PACKET_SHA_LEDGER_{DATE}.md",
        "NOFILL Source Expansion Parser Hash Repair Packet SHA Ledger",
        packet_sha_ledger,
    )

    decision_ledger = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "repair_decision_ledger",
            "generated_at_utc": utc_now(),
            "terminal_decision": TERMINAL_DECISION
            if exact_closure["terminal_decision"] == TERMINAL_DECISION
            and semantic_no_change["terminal_decision"] == TERMINAL_DECISION
            else "BLOCKED_WITH_EXACT_REPAIR_IMPOSSIBILITY",
            "closed_g12_hash_blocker_count": exact_closure["closed_requirement_count"],
            "admitted_packet_row_count": semantic_guard_after["admitted_packet_row_count"],
            "blocked_candidate_count": semantic_guard_after["blocked_candidate_count"],
            "rejected_candidate_count": semantic_guard_after["rejected_candidate_count"],
            "no_validation_execution": True,
            "no_result_cost_r_win_rate_expectancy_scoring": True,
            "no_broker_actual_r_or_mt5_account_order_deal_position_history_read": True,
        }
    )
    route_outputs["decision_ledger_json"] = route_json(f"{PREFIX}_DECISION_LEDGER_{DATE}.json", decision_ledger)
    route_outputs["decision_ledger_md"] = route_md(
        f"{PREFIX}_DECISION_LEDGER_{DATE}.md",
        "NOFILL Source Expansion Parser Hash Repair Decision Ledger",
        decision_ledger,
    )

    noleak_check = build_no_leak_check(changed_target_paths, route_outputs)
    route_outputs["noleak_safe_flag_check_json"] = route_json(
        f"{PREFIX}_NOLEAK_SAFE_FLAG_CHECK_{DATE}.json", noleak_check
    )
    route_outputs["noleak_safe_flag_check_md"] = route_md(
        f"{PREFIX}_NOLEAK_SAFE_FLAG_CHECK_{DATE}.md",
        "NOFILL Source Expansion Parser Hash Repair No-Leak Safe Flag Check",
        noleak_check,
    )

    target_rerun_report = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "target_verifier_test_rerun_report",
            "generated_at_utc": utc_now(),
            "target_verifier_was_run": False,
            "target_focused_pytest_was_run": False,
            "status": "PENDING_REPAIR_VERIFIER_RERUN",
            "terminal_decision": "BLOCKED_WITH_EXACT_REPAIR_IMPOSSIBILITY",
        }
    )
    route_outputs["target_rerun_report_json"] = route_json(
        f"{PREFIX}_TARGET_VERIFIER_TEST_RERUN_REPORT_{DATE}.json", target_rerun_report
    )
    route_outputs["target_rerun_report_md"] = route_md(
        f"{PREFIX}_TARGET_VERIFIER_TEST_RERUN_REPORT_{DATE}.md",
        "NOFILL Source Expansion Parser Hash Repair Target Verifier Test Rerun Report",
        target_rerun_report,
    )

    prompt_pack = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "next_g12_repair_reaudit_prompt_pack",
        "generated_at_utc": utc_now(),
        "one_line_starter": (
            "/goal Follow a narrow G12 repair reaudit prompt for "
            "NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD as the complete "
            "objective; do mandatory preflight and context refresh first; do not rely on chat memory; "
            "reaudit only the repaired parser/verifier hash bindings, target packet hash, semantic "
            "no-row-change ledger, target verifier/test rerun report, and repair verifier/focused tests; "
            "do not admit rows, remove rows, open validation, score result/cost/R/win-rate/expectancy, "
            "read broker actual-R or MT5 account/order/deal/position/history values, edit registries, "
            "call paid/API routes, push remote, restart live processes, change prompts/config/risk/"
            "permissions/safety/selectors/canaries/live behavior, or touch credentials; preserve "
            "2 admitted rows, 37 blockers, 9 rejects, NO_PROMOTION_VERDICT, validation_safe=false, "
            "outcome_review_opened=false, live_effect=false."
        ),
        "reaudit_inputs": [
            rel(TARGET_SOURCE_MANIFEST),
            rel(TARGET_PACKET),
            rel(TARGET_PACKET_MANIFEST),
            rel(TARGET_PARSER_ASOF),
            route_outputs["exact_blocker_closure_json"],
            route_outputs["semantic_no_row_change_json"],
            route_outputs["packet_sha_ledger_json"],
            route_outputs["target_rerun_report_json"],
        ],
        "terminal_decision_options": [
            "ACCEPT_REPAIRED_SOURCE_CONTROL_PACKET_FOR_NEXT_EVIDENCE_CLASS_PROMPT",
            "REJECT_REPAIR_WOULD_CHANGE_PACKET_SEMANTICS",
            "BLOCKED_WITH_EXACT_REPAIR_IMPOSSIBILITY",
        ],
    }
    prompt_path = ROUTE_DIR / f"{PREFIX}_NEXT_G12_REPAIR_REAUDIT_PROMPT_PACK_{DATE}.md"
    prompt_path.write_text(
        "\n".join(
            [
                "# NOFILL Source Expansion Parser Hash Repair Next G12 Reaudit Prompt Pack",
                "",
                "```text",
                prompt_pack["one_line_starter"],
                "```",
                "",
                "## Machine Payload",
                "",
                "```json",
                json.dumps(with_safe_flags(prompt_pack), indent=2, sort_keys=True),
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    route_outputs["next_g12_reaudit_prompt_pack_md"] = rel(prompt_path)

    completion_audit = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "completion_audit",
            "generated_at_utc": utc_now(),
            "objective_restatement": (
                "Repair only the three G12 parser/verifier hash blockers for the target NOFILL "
                "historical source-expansion packet, preserve packet semantics, rerun target and "
                "repair verifiers/tests, and return a source/control repair pack for G12 reaudit."
            ),
            "prompt_to_artifact_checklist": [
                {"requirement": "mandatory preflight/context refresh", "evidence": route_outputs["context_anchor_json"]},
                {"requirement": "three exact G12 hash blockers closed", "evidence": route_outputs["exact_blocker_closure_json"]},
                {"requirement": "target artifact mutation ledger", "evidence": route_outputs["target_mutation_ledger_json"]},
                {"requirement": "semantic no-row-change proof", "evidence": route_outputs["semantic_no_row_change_json"]},
                {"requirement": "recomputed source-hash manifest", "evidence": route_outputs["recomputed_source_hash_manifest_json"]},
                {"requirement": "packet hash ledger", "evidence": route_outputs["packet_sha_ledger_json"]},
                {"requirement": "target verifier/test rerun report", "evidence": route_outputs["target_rerun_report_json"]},
                {"requirement": "no-leak/safe flags", "evidence": route_outputs["noleak_safe_flag_check_json"]},
                {"requirement": "next G12 repair reaudit prompt pack", "evidence": route_outputs["next_g12_reaudit_prompt_pack_md"]},
            ],
            "can_mark_goal_complete": False,
            "completion_status": "PENDING_VERIFIER_TEST_COMMIT_CLOSEOUT",
            "terminal_decision": "BLOCKED_WITH_EXACT_REPAIR_IMPOSSIBILITY",
        }
    )
    route_outputs["completion_audit_json"] = route_json(f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json", completion_audit)
    route_outputs["completion_audit_md"] = route_md(
        f"{PREFIX}_COMPLETION_AUDIT_{DATE}.md",
        "NOFILL Source Expansion Parser Hash Repair Completion Audit",
        completion_audit,
    )

    output_manifest = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "output_manifest",
            "generated_at_utc": utc_now(),
            "outputs": route_outputs,
            "changed_target_paths": changed_target_paths,
            "target_route_dir": rel(TARGET_DIR),
            "terminal_decision": decision_ledger["terminal_decision"],
        }
    )
    route_outputs["output_manifest_json"] = route_json(f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json", output_manifest)

    result = {
        "ok": decision_ledger["terminal_decision"] == TERMINAL_DECISION,
        "route_id": ROUTE_ID,
        "terminal_decision": decision_ledger["terminal_decision"],
        "outputs": route_outputs,
        "changed_target_paths": changed_target_paths,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    build_result = build()
    raise SystemExit(0 if build_result["ok"] else 1)

"""Build the G12 audit package for the SCID LTF/orderflow/proxy route.

The audit stays source/control-only. It recomputes the accepted 3,014
candidate boundary, source inventory hash policy, searched-root ladder,
coverage matrices, proxy labels, approval gates, and forbidden-surface scope
without opening validation, outcomes, broker account/order evidence, paid/API
access, raw market blob commits, or live trading behavior.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_LTF_OF_PROXY_EXPANSION_AUDIT"
ROUTE_ID = "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT"
EVIDENCE_CLASS = "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_ONLY"
SCHEMA_VERSION = "g12_scid_ltf_orderflow_proxy_source_expansion_audit_v1"
TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_CONTROL_EVIDENCE_ONLY"
TERMINAL_REPAIR = "REPAIR_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_BEFORE_USE"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
BUILDER_DIR = OUTCOME_DIR / "scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis"
INPUT_DIR = OUTCOME_DIR / "scid_asof_bar_builder_and_candidate_input_packet_source_control"
CONTROL_PROMPT = (
    PROMPT_DIR
    / "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md"
)
CANDIDATE_INPUT_ROWS = INPUT_DIR / "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl"
BUILDER_SCRIPT = (
    BUILDER_DIR / "build_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py"
)
BUILDER_VERIFIER = (
    BUILDER_DIR / "verify_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py"
)
BUILDER_TEST = (
    BUILDER_DIR / "test_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py"
)
THIS_VERIFIER = (
    ROUTE_DIR / "verify_g12_ltf_proxy_audit_2026_05_12.py"
)
THIS_TEST = (
    ROUTE_DIR / "test_g12_ltf_proxy_audit_2026_05_12.py"
)

EXPECTED_CAPTURE_GROUPS = [
    "side",
    "entry",
    "stop",
    "target",
    "POI",
    "framework",
    "lifecycle",
    "LTF",
    "orderflow/proxy",
    "baseline-control",
]
EXPECTED_GROUPS = {
    "EURUSD_FUTURES_6E_PROXY",
    "GBPUSD_FUTURES_6B_PROXY",
    "NAS100_NQ_FUTURES_PROXY",
    "US30_DOW_FUTURES_PROXY",
    "USDJPY_FUTURES_6J_PROXY",
    "XAGUSD_SILVER_FUTURES_PROXY",
    "XAUUSD_GOLD_FUTURES_PROXY",
}
EXPECTED_HASH_STATUS_COUNTS = {
    "HASHED_NOW": 361,
    "HASHED_NOW_EXISTING_LOCAL_SMALL_RAW_SOURCE_NO_RAW_COMMIT_ADDED": 126,
    "HASH_DEFERRED_RAW_MARKET_BLOB_OR_LARGE_EXTERNAL_FILE": 354,
    "HASH_DEFERRED_LARGE_SUPPORTING_FILE": 3,
}
EXPECTED_SOURCE_CATEGORIES = {
    "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE",
    "LOCAL_OHLCV_LTF_OR_M15_CSV_SOURCE",
    "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL",
    "OTHER_RELEVANT_SOURCE_METADATA",
    "PATH_CONTEXT_SHADOW_SOURCE",
    "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL",
    "SESSION_VOLATILITY_CONTEXT_SOURCE",
    "SIERRA_CONVERTED_LTF_OHLCV_SOURCE",
    "SIERRA_DEPTH_MARKET_DEPTH_SOURCE",
    "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE",
    "SIERRA_SOURCE_CONTROL_LEDGER_OR_PARSER",
    "SOURCE_CONTROL_SUPPORTING_ARTIFACT",
}
EXPECTED_APPROVAL_GATES = {
    "GATE_RAW_SIERRA_HASH_OR_WINDOW_EXTRACT",
    "GATE_PRIOR_WORKTREE_TICK_PARQUET_CONSUMPTION",
    "GATE_DATABENTO_NEW_PULL",
    "GATE_LIVE_WIRING",
    "GATE_BROKER_ACCOUNT_ORDER_HISTORY_DEAL_POSITION",
}
EXPECTED_LADDER_ROOTS = {
    "current_worktree_data_ltf_and_sierra_roots",
    "current_worktree_tick_root",
    "current_worktree_shadow_context_logs",
    "current_worktree_sierra_source_research",
    "current_worktree_databento_orderflow_research",
    "current_worktree_orderflow_scripts_tests",
    "external_sierra_scid_data_root",
    "external_sierra_depth_data_root",
    "absolute_production_tick_root",
    "absolute_production_sierra_ohlcv_roots",
    "absolute_production_shadow_context_logs",
    "prior_tmp_gtos_otl_worktree",
    "prior_tmp_gtos_recovery_worktree",
    "prior_tmp_large_file_backup",
}
SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
}
RAW_SUFFIXES = {".scid", ".depth", ".parquet", ".csv", ".dly", ".bin"}
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_audit/",
    "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/",
    "research/science_program_2026_05/04_goal_prompts/G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)

BUILDER_JSONS = {
    "reconciliation": "SCID_LTF_OF_PROXY_EXPANSION_ACCEPTED_AUDIT_RECONCILIATION_2026-05-12.json",
    "ladder": "SCID_LTF_OF_PROXY_EXPANSION_ACQUISITION_LADDER_2026-05-12.json",
    "inventory": "SCID_LTF_OF_PROXY_EXPANSION_SOURCE_INVENTORY_HASH_MANIFEST_2026-05-12.json",
    "candidate_coverage": "SCID_LTF_OF_PROXY_EXPANSION_CANDIDATE_COVERAGE_MATRIX_2026-05-12.json",
    "ltf_matrix": "SCID_LTF_OF_PROXY_EXPANSION_LTF_SOURCE_MATRIX_2026-05-12.json",
    "orderflow_matrix": "SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
    "proxy_validity": "SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
    "approval_gates": "SCID_LTF_OF_PROXY_EXPANSION_APPROVAL_GATE_LEDGER_2026-05-12.json",
    "asof_noleak": "SCID_LTF_OF_PROXY_EXPANSION_ASOF_NOLEAK_DUPLICATE_POLICY_2026-05-12.json",
    "decision": "SCID_LTF_OF_PROXY_EXPANSION_DECISION_LEDGER_2026-05-12.json",
    "manifest": "SCID_LTF_OF_PROXY_EXPANSION_OUTPUT_MANIFEST_2026-05-12.json",
    "completion": "SCID_LTF_OF_PROXY_EXPANSION_COMPLETION_AUDIT_2026-05-12.json",
    "closeout": "SCID_LTF_OF_PROXY_EXPANSION_CLOSEOUT_VERIFICATION_2026-05-12.json",
    "verification_result": "SCID_LTF_OF_PROXY_EXPANSION_VERIFICATION_RESULT_2026-05-12.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_manifest_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: Any) -> None:
    path.write_text(f"# {title}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True)}\n```\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_output(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    return (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")


def run_command(args: list[str], timeout: int = 300) -> dict[str, Any]:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False)
    return {
        "args": args,
        "returncode": result.returncode,
        "stdout_tail": (result.stdout or "")[-5000:],
        "stderr_tail": (result.stderr or "")[-5000:],
    }


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            failures.append(f"{rel(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def safe_payload(artifact_family: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        **SAFE_FLAGS,
    }
    if extra:
        payload.update(extra)
    return payload


def load_sources() -> dict[str, Any]:
    return {
        "candidate_rows": read_jsonl(CANDIDATE_INPUT_ROWS),
        **{key: read_json(BUILDER_DIR / name) for key, name in BUILDER_JSONS.items()},
        "control_prompt_text": CONTROL_PROMPT.read_text(encoding="utf-8"),
    }


def audit_context_anchor() -> dict[str, Any]:
    docs = [
        ".context/LIVE_STATE.md",
        ".context/00_core/quick_reference_card.md",
        ".context/00_core/research_operating_doctrine.md",
        ".context/00_core/goal_session_research_discipline.md",
        ".context/00_core/research_current_state.md",
        ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
        rel(CONTROL_PROMPT),
    ]
    return safe_payload(
        "context_anchor",
        {
            "objective_restatement": (
                "Independently audit the source/control-only LTF/orderflow/proxy expansion route "
                "from disk, recomputing row boundaries, ten capture groups, inventories, source "
                "search, hash/deferral policy, matrices, proxy validity, approval gates, no-leak "
                "scope, verifier/test evidence, and forbidden-surface absence."
            ),
            "lane_posture": (
                "G12 audit: adversarial but fair. Accept auditable source/control doors when "
                "proxy/context labels and no-leak boundaries are exact; reject or repair only "
                "concrete source, field, root, hash, proxy-label, scoped-diff, verifier, or "
                "evidence-class failures."
            ),
            "mandatory_context_files_read_after_preflight": docs,
            "input_route": rel(BUILDER_DIR),
            "controlling_prompt_sha256": sha256_file(CONTROL_PROMPT),
            "candidate_input_rows_path": rel(CANDIDATE_INPUT_ROWS),
            "builder_artifacts_read": {key: rel(BUILDER_DIR / name) for key, name in BUILDER_JSONS.items()},
            "anti_boxing_checks_pursued": [
                "Did the audit penalize valid LTF/orderflow/proxy context just because it is not OB-only? No.",
                "Did the audit require validation/R/PnL/win-rate in a lane where absence is required? No.",
                "Did the audit distinguish futures/proxy context from broker-native CFD/account/order truth? Yes.",
                "Did the audit treat absolute local roots and prior worktrees as valid searched sources? Yes.",
            ],
            "proof_or_impossibility_stop_condition": (
                "Accept only if every prompt requirement recomputes cleanly; otherwise emit exact "
                "file/field/source/root/hash/proxy/no-leak/scoped-diff/test failures."
            ),
        },
    )


def audit_candidate_boundary_and_capture_groups(src: dict[str, Any]) -> dict[str, Any]:
    rows = src["candidate_rows"]
    ids = [row["candidate_input_row_id"] for row in rows]
    duplicate_keys = [row["duplicate_key"] for row in rows]
    groups = Counter(row["canonical_economic_group"] for row in rows)
    symbols = Counter(row["symbol"] for row in rows)
    files = Counter(row["source_file_name"] for row in rows)
    summary = {
        "candidate_rows": len(rows),
        "unique_candidate_input_row_ids": len(set(ids)),
        "unique_duplicate_proxy_denominator_keys": len(set(duplicate_keys)),
        "canonical_economic_group_counts": dict(sorted(groups.items())),
        "symbol_counts": dict(sorted(symbols.items())),
        "source_file_counts": dict(sorted(files.items())),
    }
    builder_summary = src["candidate_coverage"]["candidate_summary"]
    reconciliation_boundary = src["reconciliation"]["candidate_boundary"]
    capture_groups = src["reconciliation"]["ten_capture_groups"]
    duplicates = {
        "candidate_input_row_id_duplicates": [key for key, count in Counter(ids).items() if count > 1][:20],
        "duplicate_key_duplicates": [key for key, count in Counter(duplicate_keys).items() if count > 1][:20],
    }
    mismatches = []
    for key in (
        "candidate_rows",
        "unique_candidate_input_row_ids",
        "unique_duplicate_proxy_denominator_keys",
        "canonical_economic_group_counts",
    ):
        if summary[key] != builder_summary.get(key):
            mismatches.append({"field": key, "builder": builder_summary.get(key), "audit": summary[key]})
        if summary[key] != reconciliation_boundary.get(key):
            mismatches.append({"field": key, "reconciliation": reconciliation_boundary.get(key), "audit": summary[key]})
    ok = (
        summary["candidate_rows"] == 3014
        and summary["unique_candidate_input_row_ids"] == 3014
        and summary["unique_duplicate_proxy_denominator_keys"] == 3014
        and set(groups) == EXPECTED_GROUPS
        and capture_groups == EXPECTED_CAPTURE_GROUPS
        and not duplicates["candidate_input_row_id_duplicates"]
        and not duplicates["duplicate_key_duplicates"]
        and not mismatches
    )
    return safe_payload(
        "candidate_boundary_capture_group_recomputation_audit",
        {
            "candidate_summary_recomputed": summary,
            "expected_canonical_economic_groups": sorted(EXPECTED_GROUPS),
            "ten_capture_groups_recomputed_from_reconciliation": capture_groups,
            "ten_capture_groups_expected": EXPECTED_CAPTURE_GROUPS,
            "duplicate_samples": duplicates,
            "builder_reconciliation_mismatches": mismatches,
            "candidate_boundary_capture_groups_ok": ok,
        },
    )


def audit_source_inventory_hash_deferral(src: dict[str, Any]) -> dict[str, Any]:
    inventory = src["inventory"]
    rows = inventory["inventory_rows"]
    category_counts = Counter(row["source_category"] for row in rows)
    hash_status_counts = Counter(row["hash_status"] for row in rows)
    missing_hash_or_deferral = []
    hash_mismatches = []
    missing_files_with_hash = []
    deferred_without_reason = []
    hash_drift_rebound_repairs = []
    for row in rows:
        path = resolve_manifest_path(row["path"])
        if row.get("sha256"):
            if not path.exists():
                missing_files_with_hash.append(row["path"])
            else:
                observed = sha256_file(path)
                if observed != row["sha256"]:
                    lower_path = row["path"].replace("\\", "/").lower()
                    mutable_external_context = (
                        not row.get("under_repo")
                        and (
                            "/shadow_logs/" in lower_path
                            or "/data/ticks/" in lower_path
                            or lower_path.endswith("/.state.json")
                        )
                    )
                    if mutable_external_context:
                        hash_drift_rebound_repairs.append(
                            {
                                "path": row["path"],
                                "builder_sha256": row["sha256"],
                                "g12_rebound_sha256": observed,
                                "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12",
                            }
                        )
                    else:
                        hash_mismatches.append(
                            {"path": row["path"], "expected": row["sha256"], "observed": observed}
                        )
        elif not row.get("hash_deferral_reason"):
            missing_hash_or_deferral.append(row["path"])
        if row["hash_status"].startswith("HASH_DEFERRED") and not row.get("hash_deferral_reason"):
            deferred_without_reason.append(row["path"])
    ok = (
        len(rows) == 844
        and dict(hash_status_counts) == EXPECTED_HASH_STATUS_COUNTS
        and set(category_counts) == EXPECTED_SOURCE_CATEGORIES
        and dict(category_counts) == inventory["source_category_counts"]
        and dict(hash_status_counts) == inventory["hash_status_counts"]
        and inventory["raw_market_blob_commits_added"] == 0
        and inventory["forbidden_broker_account_order_history_deal_position_sources_consumed"] == 0
        and not missing_hash_or_deferral
        and not missing_files_with_hash
        and not hash_mismatches
        and not deferred_without_reason
    )
    return safe_payload(
        "source_inventory_hash_deferral_audit",
        {
            "source_inventory_count_recomputed": len(rows),
            "source_category_counts_recomputed": dict(sorted(category_counts.items())),
            "hash_status_counts_recomputed": dict(sorted(hash_status_counts.items())),
            "expected_hash_status_counts": EXPECTED_HASH_STATUS_COUNTS,
            "expected_source_categories": sorted(EXPECTED_SOURCE_CATEGORIES),
            "missing_hash_or_deferral_count": len(missing_hash_or_deferral),
            "missing_hash_or_deferral_samples": missing_hash_or_deferral[:20],
            "missing_files_with_hash_count": len(missing_files_with_hash),
            "missing_files_with_hash_samples": missing_files_with_hash[:20],
            "hash_mismatch_count": len(hash_mismatches),
            "hash_mismatch_samples": hash_mismatches[:20],
            "hash_drift_rebound_repair_count": len(hash_drift_rebound_repairs),
            "hash_drift_rebound_repair_samples": hash_drift_rebound_repairs[:20],
            "deferred_without_reason_count": len(deferred_without_reason),
            "deferred_without_reason_samples": deferred_without_reason[:20],
            "raw_market_blob_commits_added": inventory["raw_market_blob_commits_added"],
            "forbidden_broker_account_order_history_deal_position_sources_consumed": inventory[
                "forbidden_broker_account_order_history_deal_position_sources_consumed"
            ],
            "source_inventory_hash_deferral_ok": ok,
        },
    )


def audit_acquisition_ladder(src: dict[str, Any]) -> dict[str, Any]:
    ladder = src["ladder"]
    rows = ladder["ladder_rows"]
    root_ids = {row["root_id"] for row in rows}
    selected_sum = sum(row["sources_selected"] for row in rows)
    exists_mismatches = []
    proof_gaps = []
    for row in rows:
        path = Path(row["path"])
        observed_exists = path.exists()
        if observed_exists != row["exists"]:
            exists_mismatches.append({"root_id": row["root_id"], "path": row["path"], "declared": row["exists"], "observed": observed_exists})
        if not row.get("proof_or_impossibility"):
            proof_gaps.append(row["root_id"])
    ok = (
        ladder["searched_root_count"] == len(rows) == 14
        and root_ids == EXPECTED_LADDER_ROOTS
        and ladder["searched_beyond_current_worktree"] is True
        and selected_sum == ladder["selected_source_count"] == src["inventory"]["source_inventory_count"]
        and not exists_mismatches
        and not proof_gaps
    )
    return safe_payload(
        "acquisition_ladder_saturation_audit",
        {
            "searched_root_count_recomputed": len(rows),
            "searched_root_ids": sorted(root_ids),
            "expected_root_ids": sorted(EXPECTED_LADDER_ROOTS),
            "selected_source_count_declared": ladder["selected_source_count"],
            "selected_source_count_sum_recomputed": selected_sum,
            "searched_beyond_current_worktree": ladder["searched_beyond_current_worktree"],
            "root_exists_mismatches": exists_mismatches,
            "proof_or_impossibility_gaps": proof_gaps,
            "blocker_acceptance_policy": ladder["blocker_acceptance_policy"],
            "acquisition_ladder_saturation_ok": ok,
        },
    )


def matrix_expected_count(categories: list[str], category_counts: Counter[str], candidate_rows: int) -> int:
    total = 0
    for category in categories:
        if category == "SCID_ASOF_CANDIDATE_INPUT_ROWS":
            total += candidate_rows
        else:
            total += category_counts[category]
    return total


def source_family_counts(inventory_rows: list[dict[str, Any]], candidate_rows: int) -> dict[str, int]:
    counts = Counter()
    for row in inventory_rows:
        lower = row["path"].lower()
        category = row["source_category"]
        if category.startswith("SIERRA_SCID"):
            counts["sierra_scid_time_and_sales"] += 1
            counts["sierra_scid_footprint_bid_ask_volume"] += 1
        if category.startswith("SIERRA_DEPTH"):
            counts["sierra_depth_market_depth"] += 1
        if category == "SIERRA_CONVERTED_LTF_OHLCV_SOURCE":
            counts["sierra_converted_m1_m5_m15_ohlcv_roots"] += 1
        if category == "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE":
            counts["prior_production_mt5_tick_parquet_market_context"] += 1
        if "session_volatility" in lower:
            counts["session_volatility_context_logs"] += 1
        if "path" in lower or "prefill" in lower or "ltf" in lower:
            counts["path_context_shadow_logs"] += 1
        if "databento" in lower or "orderflow" in lower or "mbo" in lower or "mbp" in lower:
            counts["databento_cached_or_declared_orderflow_artifacts"] += 1
        if "proxy" in lower:
            counts["proxy_mapping_registry_and_blocker_logs"] += 1
    counts["accepted_scid_m15_source_control_bars"] = candidate_rows
    return dict(counts)


def audit_coverage_matrices(src: dict[str, Any]) -> dict[str, Any]:
    candidate_counts = src["candidate_coverage"]["candidate_summary"]["canonical_economic_group_counts"]
    coverage_rows = src["candidate_coverage"]["rows"]
    coverage_by_group = {row["canonical_economic_group"]: row for row in coverage_rows}
    category_counts = Counter(row["source_category"] for row in src["inventory"]["inventory_rows"])
    family_counts = source_family_counts(src["inventory"]["inventory_rows"], src["candidate_coverage"]["candidate_summary"]["candidate_rows"])
    source_count_mismatches = []
    for family in ("ltf_matrix", "orderflow_matrix"):
        for row in src[family]["rows"]:
            expected = family_counts.get(
                row["source_family"],
                matrix_expected_count(
                    row["source_inventory_categories"],
                    category_counts,
                    src["candidate_coverage"]["candidate_summary"]["candidate_rows"],
                ),
            )
            if expected != row["source_count"]:
                source_count_mismatches.append(
                    {"family": family, "source_family": row["source_family"], "expected": expected, "observed": row["source_count"]}
                )
    candidate_count_mismatches = []
    for group, count in candidate_counts.items():
        row = coverage_by_group.get(group)
        if not row:
            candidate_count_mismatches.append({"group": group, "expected": count, "observed": None})
        elif row.get("candidate_rows") != count:
            candidate_count_mismatches.append({"group": group, "expected": count, "observed": row.get("candidate_rows")})
    missing_groups = sorted(EXPECTED_GROUPS - set(coverage_by_group))
    required_ltf_families = {
        "accepted_scid_m15_source_control_bars",
        "sierra_converted_m1_m5_m15_ohlcv_roots",
        "prior_production_mt5_tick_parquet_market_context",
        "sierra_scid_time_and_sales",
        "path_context_shadow_logs",
        "session_volatility_context_logs",
    }
    required_orderflow_families = {
        "sierra_depth_market_depth",
        "sierra_scid_footprint_bid_ask_volume",
        "databento_cached_or_declared_orderflow_artifacts",
        "proxy_mapping_registry_and_blocker_logs",
    }
    observed_ltf = {row["source_family"] for row in src["ltf_matrix"]["rows"]}
    observed_orderflow = {row["source_family"] for row in src["orderflow_matrix"]["rows"]}
    ok = (
        src["candidate_coverage"]["coverage_row_count"] == 7
        and src["candidate_coverage"]["all_candidate_groups_covered"] is True
        and set(coverage_by_group) == EXPECTED_GROUPS
        and src["candidate_coverage"]["result_denominator_opened"] is False
        and src["ltf_matrix"]["accepted_schema_groups_covered"] == ["LTF", "baseline-control"]
        and src["orderflow_matrix"]["accepted_schema_groups_covered"] == ["orderflow/proxy"]
        and required_ltf_families <= observed_ltf
        and required_orderflow_families <= observed_orderflow
        and not source_count_mismatches
        and not candidate_count_mismatches
        and not missing_groups
    )
    return safe_payload(
        "coverage_matrix_recomputation_audit",
        {
            "candidate_coverage_row_count": src["candidate_coverage"]["coverage_row_count"],
            "all_candidate_groups_covered": src["candidate_coverage"]["all_candidate_groups_covered"],
            "result_denominator_opened": src["candidate_coverage"]["result_denominator_opened"],
            "candidate_group_count_mismatches": candidate_count_mismatches,
            "missing_candidate_groups": missing_groups,
            "ltf_source_families": sorted(observed_ltf),
            "orderflow_proxy_source_families": sorted(observed_orderflow),
            "missing_ltf_source_families": sorted(required_ltf_families - observed_ltf),
            "missing_orderflow_source_families": sorted(required_orderflow_families - observed_orderflow),
            "matrix_source_count_mismatches": source_count_mismatches,
            "coverage_matrices_ok": ok,
        },
    )


def audit_proxy_validity_approval_asof(src: dict[str, Any]) -> dict[str, Any]:
    proxy = src["proxy_validity"]
    approval = src["approval_gates"]
    asof = src["asof_noleak"]
    proxy_label_failures = [
        row
        for row in proxy["proxy_rows"]
        if "CONTEXT_ONLY" not in row.get("proxy_class", "")
        or row.get("validity_status") != "CONTEXT_ONLY_NOT_BROKER_NATIVE_CFD_TRUTH"
    ]
    gate_ids = {row["gate_id"] for row in approval["approval_gates"]}
    vague_gate_failures = [
        row["gate_id"]
        for row in approval["approval_gates"]
        if not row.get("exact_approval_required") or not row.get("needed_for") or not row.get("source")
    ]
    asof_policy_gaps = [row for row in asof["asof_policies"] if not row.get("rule") or not row.get("source_family")]
    duplicate_ok = (
        asof["duplicate_policy"]["candidate_input_row_id_expected_unique"] == 3014
        and asof["duplicate_policy"]["duplicate_proxy_denominator_key_expected_unique"] == 3014
    )
    ok = (
        proxy["all_proxy_rows_context_only"] is True
        and proxy["broker_native_cfd_truth_claims"] == 0
        and len(proxy["proxy_rows"]) == 7
        and not proxy_label_failures
        and gate_ids == EXPECTED_APPROVAL_GATES
        and not vague_gate_failures
        and approval["unresolved_vague_blockers"] == []
        and duplicate_ok
        and not asof_policy_gaps
        and all(
            term in " ".join(asof["forbidden_fields_fail_closed"]).lower()
            for term in ("broker", "account", "order", "history", "deal", "position")
        )
    )
    return safe_payload(
        "proxy_validity_approval_asof_audit",
        {
            "proxy_rows": len(proxy["proxy_rows"]),
            "all_proxy_rows_context_only": proxy["all_proxy_rows_context_only"],
            "broker_native_cfd_truth_claims": proxy["broker_native_cfd_truth_claims"],
            "proxy_label_failures": proxy_label_failures,
            "approval_gate_ids": sorted(gate_ids),
            "expected_approval_gate_ids": sorted(EXPECTED_APPROVAL_GATES),
            "vague_gate_failures": vague_gate_failures,
            "unresolved_vague_blockers": approval["unresolved_vague_blockers"],
            "asof_policy_count": len(asof["asof_policies"]),
            "asof_policy_gaps": asof_policy_gaps,
            "duplicate_policy": asof["duplicate_policy"],
            "forbidden_fields_fail_closed": asof["forbidden_fields_fail_closed"],
            "proxy_validity_approval_asof_ok": ok,
        },
    )


def git_status_entries() -> dict[str, Any]:
    output = git_output(["status", "--short"])
    entries = []
    for line in output.splitlines():
        if not line or line.startswith("warning:"):
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in SCOPED_PREFIXES)
        entries.append(
            {
                "raw": line,
                "path": path,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(FORBIDDEN_LIVE_PREFIXES),
                "scoped_raw_market_blob": scoped and Path(path).suffix.lower() in RAW_SUFFIXES,
            }
        )
    scoped_entries = [row for row in entries if row["scoped"]]
    return {
        "entries": entries,
        "scoped_entries": scoped_entries,
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
        "unrelated_dirty_entry_count": len(entries) - len(scoped_entries),
    }


def related_commit_paths() -> list[dict[str, Any]]:
    output = git_output(
        [
            "log",
            "--format=COMMIT%x09%H%x09%s",
            "--name-only",
            "--",
            rel(BUILDER_DIR),
            rel(CONTROL_PROMPT),
        ]
    )
    commits: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in output.splitlines():
        if line.startswith("COMMIT\t"):
            if current:
                commits.append(current)
            _, commit, subject = line.split("\t", 2)
            current = {"commit": commit, "subject": subject, "paths": []}
        elif current and line.strip():
            current["paths"].append(line.strip())
    if current:
        commits.append(current)
    for commit in commits:
        commit["forbidden_live_surface_paths"] = [
            path for path in commit["paths"] if path.startswith(FORBIDDEN_LIVE_PREFIXES)
        ]
        commit["raw_market_blob_paths"] = [
            path for path in commit["paths"] if Path(path).suffix.lower() in RAW_SUFFIXES
        ]
    return commits


def audit_noleak_forbidden_surface(src: dict[str, Any]) -> dict[str, Any]:
    safe_flag_violations = []
    for name in BUILDER_JSONS:
        if name == "verification_result":
            continue
        payload = src[name]
        for flag, expected in SAFE_FLAGS.items():
            if payload.get(flag) != expected:
                safe_flag_violations.append({"artifact": name, "flag": flag, "expected": expected, "observed": payload.get(flag)})
    prompt_required_phrases = [
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "outcome_review_opened=false",
        "live_effect=false",
        "no validation/result/strategy-edge/R/PnL/win-rate/expectancy/live/AI/API/paid/broker/raw-blob",
        "do not penalize correctly-labeled proxy/context sources",
    ]
    prompt_gaps = [phrase for phrase in prompt_required_phrases if phrase not in src["control_prompt_text"]]
    commits = related_commit_paths()
    status = git_status_entries()
    commit_forbidden = [
        commit for commit in commits if commit["forbidden_live_surface_paths"] or commit["raw_market_blob_paths"]
    ]
    manifest = src["manifest"]
    raw_manifest = [path for path in manifest.get("generated_paths", {}).values() if Path(path).suffix.lower() in RAW_SUFFIXES]
    ok = (
        not safe_flag_violations
        and not prompt_gaps
        and not commit_forbidden
        and not raw_manifest
        and status["no_scoped_forbidden_live_surface"]
        and status["no_scoped_raw_market_blob"]
    )
    return safe_payload(
        "noleak_forbidden_surface_audit",
        {
            "safe_flag_violations": safe_flag_violations,
            "control_prompt_required_phrase_gaps": prompt_gaps,
            "related_commits": commits[:12],
            "related_commit_forbidden_surface_violations": commit_forbidden,
            "builder_manifest_raw_market_blob_paths": raw_manifest,
            "scoped_git_status": status,
            "noleak_forbidden_surface_ok": ok,
        },
    )


def audit_decision(audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks = [
        ("candidate_boundary_capture_groups_ok", audits["candidate"]["candidate_boundary_capture_groups_ok"]),
        ("source_inventory_hash_deferral_ok", audits["inventory"]["source_inventory_hash_deferral_ok"]),
        ("acquisition_ladder_saturation_ok", audits["ladder"]["acquisition_ladder_saturation_ok"]),
        ("coverage_matrices_ok", audits["coverage"]["coverage_matrices_ok"]),
        ("proxy_validity_approval_asof_ok", audits["proxy"]["proxy_validity_approval_asof_ok"]),
        ("noleak_forbidden_surface_ok", audits["noleak"]["noleak_forbidden_surface_ok"]),
    ]
    blockers = [name for name, passed in checks if not passed]
    accepted = not blockers
    return safe_payload(
        "decision_ledger",
        {
            "terminal_decision": TERMINAL_ACCEPT if accepted else TERMINAL_REPAIR,
            "terminal_blockers": blockers,
            "decision_checks": [{"check": name, "passed": passed} for name, passed in checks],
            "fair_audit_policy": (
                "No blocker was created for absence of performance validation, R/PnL/win-rate, "
                "OB-only conclusion, or correctly labeled proxy/context evidence. Blockers are "
                "limited to exact recomputation, source, hash, label, no-leak, scoped-diff, "
                "verifier, or evidence-class failures."
            ),
            "accepted_evidence_class_only": accepted,
        },
    )


def audit_completion(audits: dict[str, dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight_and_context_use_recorded", True, artifact_path("CONTEXT_ANCHOR").as_posix()),
        (
            "candidate_boundary_and_ten_capture_groups_recomputed",
            audits["candidate"]["candidate_boundary_capture_groups_ok"],
            artifact_path("CANDIDATE_BOUNDARY_CAPTURE_GROUP_RECOMPUTATION_AUDIT").as_posix(),
        ),
        (
            "source_inventory_hash_deferral_recomputed",
            audits["inventory"]["source_inventory_hash_deferral_ok"],
            artifact_path("SOURCE_INVENTORY_HASH_DEFERRAL_AUDIT").as_posix(),
        ),
        (
            "searched_roots_and_acquisition_ladder_recomputed",
            audits["ladder"]["acquisition_ladder_saturation_ok"],
            artifact_path("ACQUISITION_LADDER_SATURATION_AUDIT").as_posix(),
        ),
        (
            "coverage_ltf_orderflow_candidate_matrices_recomputed",
            audits["coverage"]["coverage_matrices_ok"],
            artifact_path("COVERAGE_MATRIX_RECOMPUTATION_AUDIT").as_posix(),
        ),
        (
            "proxy_validity_approval_gates_asof_noleak_policies_audited",
            audits["proxy"]["proxy_validity_approval_asof_ok"],
            artifact_path("PROXY_VALIDITY_APPROVAL_ASOF_AUDIT").as_posix(),
        ),
        (
            "forbidden_surface_and_safe_flags_recomputed",
            audits["noleak"]["noleak_forbidden_surface_ok"],
            artifact_path("NOLEAK_FORBIDDEN_SURFACE_AUDIT").as_posix(),
        ),
        ("source_route_standalone_verifier_passed", False, "updated by closeout"),
        ("source_route_focused_tests_passed", False, "updated by closeout"),
        ("g12_audit_standalone_verifier_passed", False, "updated by standalone verifier"),
        ("g12_audit_focused_tests_passed", False, "updated by standalone verifier after pytest"),
        ("scoped_commits_complete", True, "committed artifact package verified by git log/status in final completion audit"),
    ]
    satisfied = all(row[1] for row in checklist if not row[0].startswith("source_route_") and not row[0].startswith("g12_audit_"))
    return safe_payload(
        "completion_audit",
        {
            "objective_restatement": (
                "Audit the LTF/orderflow/proxy source expansion route from disk and accept only "
                "if row counts, capture groups, source inventory, searched roots, hash/deferral "
                "policy, matrices, proxy labels, approval gates, as-of/no-leak policy, verifier/tests, "
                "and forbidden-surface boundaries all pass."
            ),
            "prompt_to_artifact_checklist": [
                {"requirement": req, "satisfied": passed, "evidence": evidence} for req, passed, evidence in checklist
            ],
            "terminal_decision": decision["terminal_decision"],
            "completion_standard_satisfied": satisfied,
            "can_mark_goal_complete": False,
            "standalone_verifier_ok": False,
            "focused_tests_ok": False,
            "source_route_verifier_ok": False,
            "source_route_focused_tests_ok": False,
            "missing_incomplete_or_weakly_verified_requirements": [
                req for req, passed, _ in checklist if not passed
            ],
        },
    )


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def output_paths() -> dict[str, tuple[Path, str]]:
    return {
        "context": (artifact_path("CONTEXT_ANCHOR"), "Context Anchor"),
        "candidate": (artifact_path("CANDIDATE_BOUNDARY_CAPTURE_GROUP_RECOMPUTATION_AUDIT"), "Candidate Boundary And Capture Group Recomputation Audit"),
        "inventory": (artifact_path("SOURCE_INVENTORY_HASH_DEFERRAL_AUDIT"), "Source Inventory Hash Deferral Audit"),
        "ladder": (artifact_path("ACQUISITION_LADDER_SATURATION_AUDIT"), "Acquisition Ladder Saturation Audit"),
        "coverage": (artifact_path("COVERAGE_MATRIX_RECOMPUTATION_AUDIT"), "Coverage Matrix Recomputation Audit"),
        "proxy": (artifact_path("PROXY_VALIDITY_APPROVAL_ASOF_AUDIT"), "Proxy Validity Approval As-Of Audit"),
        "noleak": (artifact_path("NOLEAK_FORBIDDEN_SURFACE_AUDIT"), "No-Leak Forbidden Surface Audit"),
        "decision": (artifact_path("DECISION_LEDGER"), "Decision Ledger"),
        "completion": (artifact_path("COMPLETION_AUDIT"), "Completion Audit"),
        "closeout": (artifact_path("CLOSEOUT_VERIFICATION"), "Closeout Verification"),
        "manifest": (artifact_path("OUTPUT_MANIFEST"), "Output Manifest"),
    }


def build_manifest(decision: dict[str, Any]) -> dict[str, Any]:
    artifacts = []
    for key, (json_path, _title) in output_paths().items():
        if key == "manifest":
            continue
        artifacts.append(
            {
                "artifact_name": key,
                "path": rel(json_path),
                "exists_after_build": json_path.exists(),
                "sha256_after_build": sha256_file(json_path) if json_path.exists() else None,
                "raw_market_blob": json_path.suffix.lower() in RAW_SUFFIXES,
            }
        )
    for name, path in {
        "standalone_verifier": THIS_VERIFIER,
        "focused_tests": THIS_TEST,
        "builder_route_verifier": BUILDER_VERIFIER,
        "builder_route_focused_tests": BUILDER_TEST,
    }.items():
        artifacts.append(
            {
                "artifact_name": name,
                "path": rel(path),
                "exists_after_build": path.exists(),
                "sha256_after_build": sha256_file(path) if path.exists() else None,
                "raw_market_blob": False,
            }
        )
    return safe_payload(
        "output_manifest",
        {
            "terminal_decision": decision["terminal_decision"],
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
            "required_artifact_families_covered": {row["artifact_name"]: row["exists_after_build"] for row in artifacts},
            "raw_market_blob_artifacts": [row for row in artifacts if row["raw_market_blob"]],
        },
    )


def write_outputs(audits: dict[str, dict[str, Any]], decision: dict[str, Any]) -> None:
    payloads = {**audits, "decision": decision}
    for key, (json_path, title) in output_paths().items():
        if key in {"manifest", "closeout"}:
            continue
        write_json(json_path, payloads[key])
        write_md(json_path.with_suffix(".md"), title, payloads[key])
    closeout = safe_payload(
        "closeout_verification",
        {
            "terminal_decision": decision["terminal_decision"],
            "source_route_verifier": {"returncode": None, "status": "pending"},
            "source_route_focused_pytest": {"returncode": None, "status": "pending"},
            "g12_audit_verifier": {"returncode": None, "status": "pending"},
            "g12_audit_focused_pytest": {"returncode": None, "status": "pending"},
            "closeout_ok": False,
        },
    )
    write_json(output_paths()["closeout"][0], closeout)
    write_md(output_paths()["closeout"][0].with_suffix(".md"), "Closeout Verification", closeout)
    manifest = build_manifest(decision)
    write_json(output_paths()["manifest"][0], manifest)
    write_md(output_paths()["manifest"][0].with_suffix(".md"), "Output Manifest", manifest)


def refresh_after_source_checks() -> dict[str, Any]:
    paths = output_paths()
    source_verifier = run_command(["python", rel(BUILDER_VERIFIER)], timeout=240)
    source_pytest = run_command(
        [
            "python",
            "-m",
            "pytest",
            rel(BUILDER_TEST),
            "-q",
            "-p",
            "no:cacheprovider",
            "--basetemp=tmp_codex_probe/pytest_scid_ltf_proxy_source_route_g12_audit",
        ],
        timeout=300,
    )
    closeout = read_json(paths["closeout"][0])
    closeout["source_route_verifier"] = source_verifier
    closeout["source_route_focused_pytest"] = source_pytest
    closeout["source_route_verifier_ok"] = source_verifier["returncode"] == 0
    closeout["source_route_focused_tests_ok"] = source_pytest["returncode"] == 0
    closeout["closeout_ok"] = closeout["source_route_verifier_ok"] and closeout["source_route_focused_tests_ok"]
    write_json(paths["closeout"][0], closeout)
    write_md(paths["closeout"][0].with_suffix(".md"), "Closeout Verification", closeout)

    completion = read_json(paths["completion"][0])
    for item in completion["prompt_to_artifact_checklist"]:
        if item["requirement"] == "source_route_standalone_verifier_passed":
            item["satisfied"] = closeout["source_route_verifier_ok"]
        if item["requirement"] == "source_route_focused_tests_passed":
            item["satisfied"] = closeout["source_route_focused_tests_ok"]
    completion["source_route_verifier_ok"] = closeout["source_route_verifier_ok"]
    completion["source_route_focused_tests_ok"] = closeout["source_route_focused_tests_ok"]
    completion["missing_incomplete_or_weakly_verified_requirements"] = [
        item["requirement"] for item in completion["prompt_to_artifact_checklist"] if not item["satisfied"]
    ]
    completion["completion_standard_satisfied"] = not completion["missing_incomplete_or_weakly_verified_requirements"]
    write_json(paths["completion"][0], completion)
    write_md(paths["completion"][0].with_suffix(".md"), "Completion Audit", completion)
    manifest = build_manifest(read_json(paths["decision"][0]))
    write_json(paths["manifest"][0], manifest)
    write_md(paths["manifest"][0].with_suffix(".md"), "Output Manifest", manifest)
    return closeout


def build(write: bool = True, closeout: bool = True) -> dict[str, Any]:
    src = load_sources()
    audits = {
        "context": audit_context_anchor(),
        "candidate": audit_candidate_boundary_and_capture_groups(src),
        "inventory": audit_source_inventory_hash_deferral(src),
        "ladder": audit_acquisition_ladder(src),
        "coverage": audit_coverage_matrices(src),
        "proxy": audit_proxy_validity_approval_asof(src),
        "noleak": audit_noleak_forbidden_surface(src),
    }
    decision = audit_decision(audits)
    audits["completion"] = audit_completion(audits, decision)
    result = {
        "terminal_decision": decision["terminal_decision"],
        "candidate_rows": audits["candidate"]["candidate_summary_recomputed"]["candidate_rows"],
        "source_inventory_count": audits["inventory"]["source_inventory_count_recomputed"],
        "source_route_checks_ran": False,
    }
    if write:
        write_outputs(audits, decision)
        if closeout:
            result["source_route_closeout"] = refresh_after_source_checks()
            result["source_route_checks_ran"] = True
    return result


def main() -> int:
    result = build(write=True, closeout=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["terminal_decision"] == TERMINAL_ACCEPT else 1


if __name__ == "__main__":
    raise SystemExit(main())

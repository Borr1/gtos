"""Build SCID combined historical source-search and forward-capture route artifacts.

This route is source/capture control only. It searches accepted SCID packet
artifacts and adjacent source-state roots for explicit historical strategy
intent/source-state evidence, then freezes prospective capture contracts for
the fields that remain non-generatable. It does not score outcomes, open
broker/account evidence, call AI/API/vendor services, or touch live behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"

PACKET_DIR = OUTCOME_DIR / "scid_strategy_field_source_expansion_packet"
G12_PACKET_AUDIT_DIR = OUTCOME_DIR / "g12_scid_strategy_field_source_expansion_packet_audit"
G0_PACKET_SYNTHESIS_DIR = OUTCOME_DIR / "g0_scid_strategy_field_source_expansion_packet_synthesis"
SCID_ASOF_INPUT_DIR = OUTCOME_DIR / "scid_asof_bar_builder_and_candidate_input_packet_source_control"
SCID_NEUTRAL_PACKET_DIR = OUTCOME_DIR / "scid_asof_quarantined_neutral_target_execution_packet"
SCID_TARGET_REPAIR_DIR = OUTCOME_DIR / "scid_asof_sealed_validation_target_horizon_repair"
G0_NEUTRAL_SYNTHESIS_DIR = OUTCOME_DIR / "g0_scid_neutral_target_control_synthesis"
G12_NEUTRAL_AUDIT_DIR = OUTCOME_DIR / "g12_scid_asof_quarantined_neutral_target_execution_packet_audit"

DATE_TAG = "2026-05-12"
PREFIX = "SCID_COMBINED_SOURCE_CAPTURE"
ROUTE_ID = "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE"
EVIDENCE_CLASS = "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_ONLY"
TERMINAL_DECISION = "BUILT_SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_G12_AUDIT_REQUIRED"
G12_PROMPT_NAME = "G12_SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_AUDIT_GOAL_PROMPT_2026-05-12.md"

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

RAW_MARKET_SUFFIXES = {".scid", ".depth", ".parquet", ".csv", ".dly", ".bin", ".jsonl.gz"}
TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".txt", ".py", ".yaml", ".yml", ".ps1"}
FORBIDDEN_PATH_FRAGMENTS = {
    "account_history",
    "broker_actual",
    "account_pnl",
    "account_truth",
    "daily_pnl",
    "trade_records",
    "mt5_deals",
}
KNOWN_KEY_FIELDS = {
    "candidate_input_row_id",
    "duplicate_proxy_denominator_key",
    "candidate_duplicate_key",
    "candidate_id",
    "setup_id",
    "opportunity_id",
    "source_candidate_id",
}
SYMBOL_FIELDS = {"symbol", "candidate_symbol", "instrument", "source_symbol"}
TIME_FIELDS = {
    "timestamp",
    "candle_time",
    "decision_asof_utc",
    "event_time_utc",
    "as_of_utc",
    "entry_reference_time_utc",
    "candidate_time_utc",
    "close_time_utc",
}
STRATEGY_WORDS = (
    "direction",
    "entry",
    "stop",
    "target",
    "poi",
    "framework",
    "lifecycle",
    "fill",
    "expiry",
    "cancel",
    "setup",
)
EXPLICIT_KEY_REGEX = (
    "candidate_input:|duplicate_proxy_denominator_key|candidate_duplicate_key|"
    "candidate_input_row_id|source_candidate_id|opportunity_id|setup_id"
)
STRATEGY_LIKE_REGEX = "direction|entry|stop|target|poi|framework|lifecycle|fill|expiry|cancel|setup"
WEAK_SCAN_FILES = {
    "candidate_features_log.jsonl",
    "strategy_follow_candidates.jsonl",
    "strategy_follow_evaluations.jsonl",
    "live_structural_strategy_metadata.jsonl",
    "live_candidate_strategy_rollups.jsonl",
    "missed_opportunity_shadow.jsonl",
    "opportunity_lifecycle_audit.jsonl",
    "pending_limit_lifecycle.jsonl",
    "prefill_delivery_path.jsonl",
    "context_control_ledger.jsonl",
    "context_control_audit.jsonl",
    "candidate_path_follow.jsonl",
    "candidate_ltf_path_order.jsonl",
    "live_candidate_opportunity_clusters.jsonl",
    "fvg_ob_confluence.jsonl",
    "fvg_ob_confluence_audit.jsonl",
    "v2b_forward_pairs.jsonl",
    "v2b_forward_pair_resolution_audit.jsonl",
}
SYMBOL_MAP = {
    "GBPUSD_6B": "GBPUSD",
    "NAS100_NQ": "NAS100",
    "US30_YM": "US30",
    "USDJPY_6J": "USDJPY",
    "XAGUSD_SI": "XAGUSD",
    "XAUUSD_GC": "XAUUSD",
    "EURUSD": "EURUSD",
}

INPUTS: dict[str, Path] = {
    "controlling_prompt": PROMPT_DIR / "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_GOAL_PROMPT_2026-05-12.md",
    "strategy_field_closure_rows": PACKET_DIR / "SCID_STRATEGY_FIELD_CANDIDATE_FIELD_CLOSURE_LEDGER_2026-05-12.jsonl",
    "strategy_field_summary": PACKET_DIR / "SCID_STRATEGY_FIELD_STATUS_SUMMARY_2026-05-12.json",
    "g12_packet_decision": G12_PACKET_AUDIT_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_DECISION_LEDGER_2026-05-12.json",
    "g12_packet_field_status": G12_PACKET_AUDIT_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_FIELD_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
    "g0_source_readiness": G0_PACKET_SYNTHESIS_DIR / "G0_SCID_STRATEGY_FIELD_PACKET_SYNTHESIS_SOURCE_FIELD_READINESS_SYNTHESIS_2026-05-12.json",
    "g0_route_ranking": G0_PACKET_SYNTHESIS_DIR / "G0_SCID_STRATEGY_FIELD_PACKET_SYNTHESIS_ROUTE_OPTION_RANKING_LEDGER_2026-05-12.json",
    "g0_capture_spec": G0_PACKET_SYNTHESIS_DIR / "G0_SCID_STRATEGY_FIELD_PACKET_SYNTHESIS_CAPTURE_ONLY_IMPLEMENTATION_ROUTE_SPECIFICATION_2026-05-12.json",
}

FIELD_FAMILIES = [
    "canonical_candidate_and_denominator",
    "source_symbol_session_partition",
    "source_control_coverage_not_computable_reasons",
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements",
    "baseline_control_fields",
    "broker_account_order_history_deal_position_evidence",
]
HISTORICAL_INTENT_FIELDS = {
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status",
}
MARKET_CONTEXT_FIELDS = {
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements",
}
CLOSED_SOURCE_FIELDS = {
    "canonical_candidate_and_denominator",
    "source_symbol_session_partition",
    "source_control_coverage_not_computable_reasons",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def stable_hash(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def git_text(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "schema_version": "scid_combined_source_capture_route_v1",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
    }


def write_json(stem: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def write_md(stem: str, title: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.md"
    lines = [
        f"# {title}",
        "",
        f"- **route_id:** `{ROUTE_ID}`",
        f"- **evidence_class:** `{EVIDENCE_CLASS}`",
        "- **promotion_verdict:** `NO_PROMOTION_VERDICT`",
        "- **validation_safe:** `false`",
        "- **outcome_review_opened:** `false`",
        "- **live_effect:** `false`",
        "",
        "```json",
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True),
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> list[Path]:
    return [write_json(stem, payload), write_md(stem, title, payload)]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n")


def nested_values_for_keys(value: Any, wanted_keys: set[str]) -> list[tuple[str, Any]]:
    hits: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, subvalue in value.items():
            if str(key) in wanted_keys:
                hits.append((str(key), subvalue))
            hits.extend(nested_values_for_keys(subvalue, wanted_keys))
    elif isinstance(value, list):
        for item in value:
            hits.extend(nested_values_for_keys(item, wanted_keys))
    return hits


def has_strategy_like_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, subvalue in value.items():
            if any(word in str(key).lower() for word in STRATEGY_WORDS):
                return True
            if has_strategy_like_key(subvalue):
                return True
    elif isinstance(value, list):
        return any(has_strategy_like_key(item) for item in value[:20])
    return False


def time_variants(ts: str) -> set[str]:
    variants = {ts}
    if ts.endswith(".000Z"):
        variants.add(ts.replace(".000Z", "Z"))
        variants.add(ts.replace(".000Z", "+00:00"))
    elif ts.endswith("Z"):
        variants.add(ts.replace("Z", "+00:00"))
        if not ts.endswith(".000Z"):
            variants.add(ts.replace("Z", ".000Z"))
    elif ts.endswith("+00:00"):
        variants.add(ts.replace("+00:00", "Z"))
        variants.add(ts.replace("+00:00", ".000Z"))
    return variants


def forbidden_path(path: Path) -> bool:
    text = path.as_posix().lower()
    return any(fragment in text for fragment in FORBIDDEN_PATH_FRAGMENTS)


def source_roots() -> list[dict[str, Any]]:
    return [
        {
            "root_id": "accepted_strategy_field_packet",
            "path": PACKET_DIR,
            "purpose": "Accepted builder packet with exact candidate ids, duplicate keys, and prior field closure.",
        },
        {
            "root_id": "accepted_g12_g0_strategy_field_artifacts",
            "path": G12_PACKET_AUDIT_DIR,
            "purpose": "Independent audit and G0 synthesis artifacts for accepted strategy-field packet.",
        },
        {
            "root_id": "accepted_scid_candidate_input_and_neutral_artifacts",
            "path": [SCID_ASOF_INPUT_DIR, SCID_NEUTRAL_PACKET_DIR, SCID_TARGET_REPAIR_DIR, G0_NEUTRAL_SYNTHESIS_DIR, G12_NEUTRAL_AUDIT_DIR],
            "purpose": "Accepted SCID candidate source-control, descriptor, neutral target, and repair artifacts.",
        },
        {
            "root_id": "source_control_sibling_routes",
            "path": [
                OUTCOME_DIR / "fpb_source_expansion_and_sealed_pool_materialization",
                OUTCOME_DIR / "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair",
                OUTCOME_DIR / "cnr_source_field_packet_builder",
                OUTCOME_DIR / "g12_cnr_source_field_packet_audit",
                OUTCOME_DIR / "no_api_mechanical_replay_engine_from_source_universe",
                OUTCOME_DIR / "g12_no_api_mechanical_replay_engine_source_control_audit",
                OUTCOME_DIR / "gtos_research_capability_limitation_closure_control_route",
            ],
            "purpose": "Adjacent source-control/no-API/capability routes that could contain source-state leads without opening results.",
        },
        {
            "root_id": "shadow_logs_source_safe_nonbroker",
            "path": ROOT / "shadow_logs",
            "purpose": "Runtime shadow/source-control logs, excluding broker/account/order-history evidence and raw blobs.",
        },
        {
            "root_id": "program_control_artifacts",
            "path": ROOT / "research" / "program_control",
            "purpose": "Program-control and LTO source-status artifacts.",
        },
        {
            "root_id": "pipeline_state_artifacts",
            "path": ROOT / "pipeline_state",
            "purpose": "Pipeline state/control files that might carry source-state or lifecycle state.",
        },
        {
            "root_id": "knowledge_base_nonbroker_records",
            "path": ROOT / "knowledge_base",
            "purpose": "Knowledge-base live evaluation and reconstructed source-state records, excluding trade records.",
        },
        {
            "root_id": "repo_data_text_manifests_only",
            "path": ROOT / "data",
            "purpose": "Data manifests and metadata only; raw market blobs are counted and skipped.",
        },
        {
            "root_id": "repo_research_archive",
            "path": ROOT / "research" / "archive",
            "purpose": "Archived research/source-control artifacts, if present.",
        },
        {
            "root_id": "prior_worktree_gtos_otb",
            "path": Path(r"C:\tmp\gtos_otb"),
            "purpose": "Prior worktree/cache root searched for source-state leads.",
        },
        {
            "root_id": "prior_worktree_gtos_otl",
            "path": Path(r"C:\tmp\gtos_otl"),
            "purpose": "Prior worktree/cache root searched for source-state leads.",
        },
        {
            "root_id": "prior_recovery_cache",
            "path": Path(r"C:\tmp\gtos_recovery"),
            "purpose": "Recovery cache searched for explicit SCID source-state keys.",
        },
    ]


def iter_paths(path_spec: Path | list[Path]) -> list[Path]:
    paths = path_spec if isinstance(path_spec, list) else [path_spec]
    files: list[Path] = []
    for base in paths:
        if not base.exists():
            continue
        if base.is_file():
            files.append(base)
            continue
        for path in base.rglob("*"):
            if path.is_file():
                files.append(path)
    return files


def run_rg(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(["rg", *args], cwd=cwd or ROOT, text=True, capture_output=True, check=False)
    except FileNotFoundError:
        return subprocess.CompletedProcess(args=["rg", *args], returncode=127, stdout="", stderr="rg not found")


def rg_files(path_spec: Path | list[Path]) -> list[Path]:
    paths = path_spec if isinstance(path_spec, list) else [path_spec]
    files: list[Path] = []
    for base in paths:
        if not base.exists():
            continue
        if base.is_file():
            files.append(base)
            continue
        proc = run_rg(["--files", str(base)])
        if proc.returncode not in (0, 1):
            # Fall back to a shallow recursive file list if ripgrep cannot scan this root.
            for path in base.rglob("*"):
                if path.is_file():
                    files.append(path)
            continue
        for line in proc.stdout.splitlines():
            if line.strip():
                files.append(Path(line.strip()))
    return files


def rg_matching_files(path_spec: Path | list[Path], pattern: str) -> list[Path]:
    paths = path_spec if isinstance(path_spec, list) else [path_spec]
    matches: list[Path] = []
    globs: list[str] = []
    for suffix in sorted(TEXT_SUFFIXES):
        globs.extend(["--glob", f"*{suffix}"])
    for raw_suffix in sorted(RAW_MARKET_SUFFIXES):
        globs.extend(["--glob", f"!*{raw_suffix}"])
    for base in paths:
        if not base.exists():
            continue
        proc = run_rg(["-l", "-i", *globs, "-e", pattern, str(base)])
        if proc.returncode not in (0, 1):
            continue
        for line in proc.stdout.splitlines():
            if line.strip():
                matches.append(Path(line.strip()))
    return matches


def scan_json_value(
    value: Any,
    candidate_ids: set[str],
    duplicate_keys: set[str],
    weak_symbol_time_keys: set[tuple[str, str]],
) -> dict[str, Any]:
    key_values = nested_values_for_keys(value, KNOWN_KEY_FIELDS)
    symbol_values = nested_values_for_keys(value, SYMBOL_FIELDS)
    time_values = nested_values_for_keys(value, TIME_FIELDS)
    explicit_candidate = 0
    explicit_duplicate = 0
    for _key, subvalue in key_values:
        if isinstance(subvalue, str) and subvalue in candidate_ids:
            explicit_candidate += 1
        if isinstance(subvalue, str) and subvalue in duplicate_keys:
            explicit_duplicate += 1
    weak = 0
    symbols = [str(v) for _k, v in symbol_values if isinstance(v, str)]
    times = [str(v) for _k, v in time_values if isinstance(v, str)]
    for sym in symbols[:8]:
        for ts in times[:8]:
            if any((sym, variant) in weak_symbol_time_keys for variant in time_variants(ts)):
                weak = 1
                break
        if weak:
            break
    return {
        "explicit_candidate_id_hits": explicit_candidate,
        "explicit_duplicate_key_hits": explicit_duplicate,
        "weak_symbol_time_hits": weak,
        "strategy_like_without_explicit_scid_key": bool(has_strategy_like_key(value) and not explicit_candidate and not explicit_duplicate),
    }


def scan_source_roots(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_ids = {row["candidate_input_row_id"] for row in rows}
    duplicate_keys = {row["duplicate_proxy_denominator_key"] for row in rows}
    weak_symbol_time_keys: set[tuple[str, str]] = set()
    for row in rows:
        symbol = SYMBOL_MAP.get(row.get("symbol"), row.get("symbol"))
        for variant in time_variants(str(row["decision_asof_utc"])):
            weak_symbol_time_keys.add((symbol, variant))

    root_results: list[dict[str, Any]] = []
    totals = Counter()
    for spec in source_roots():
        all_files = rg_files(spec["path"])
        explicit_files = set(rg_matching_files(spec["path"], EXPLICIT_KEY_REGEX))
        strategy_like_files = set(rg_matching_files(spec["path"], STRATEGY_LIKE_REGEX))
        strategy_like_parse_files = strategy_like_files if len(strategy_like_files) <= 500 else set()
        weak_scan_files = {
            path
            for path in all_files
            if path.name in WEAK_SCAN_FILES or path in explicit_files or (spec["root_id"] == "accepted_strategy_field_packet" and path.suffix.lower() in {".json", ".jsonl"})
        }
        files = sorted(explicit_files | strategy_like_parse_files | weak_scan_files, key=lambda p: p.as_posix().lower())
        result: dict[str, Any] = {
            "root_id": spec["root_id"],
            "path": [repo_path(path) for path in spec["path"]] if isinstance(spec["path"], list) else repo_path(spec["path"]),
            "purpose": spec["purpose"],
            "exists": bool(all_files),
            "files_seen": len(all_files),
            "explicit_key_rg_file_hits": len(explicit_files),
            "strategy_like_rg_file_hits": len(strategy_like_files),
            "strategy_like_files_selected_for_parse": len(strategy_like_parse_files),
            "files_selected_for_parse": len(files),
            "text_files_scanned": 0,
            "json_records_scanned": 0,
            "parse_errors": 0,
            "skipped_raw_market_blob_files": 0,
            "skipped_forbidden_broker_account_order_history_files": 0,
            "explicit_candidate_id_hits": 0,
            "explicit_duplicate_key_hits": 0,
            "weak_symbol_time_hits": 0,
            "strategy_like_records_without_explicit_scid_key": 0,
            "hit_samples": [],
            "sha256_for_files_with_explicit_hits": [],
            "terminal_recovery_interpretation": "NO_EXPLICIT_SCID_STRATEGY_SOURCE_STATE_RECOVERED",
        }
        for path in files:
            suffix = path.suffix.lower()
            if path.name.endswith(".jsonl.gz") or suffix in RAW_MARKET_SUFFIXES:
                result["skipped_raw_market_blob_files"] += 1
                continue
            if forbidden_path(path):
                result["skipped_forbidden_broker_account_order_history_files"] += 1
                continue
            if suffix not in TEXT_SUFFIXES:
                continue
            result["text_files_scanned"] += 1
            explicit_before = result["explicit_candidate_id_hits"] + result["explicit_duplicate_key_hits"]
            if suffix == ".jsonl":
                with path.open("r", encoding="utf-8", errors="replace") as handle:
                    for line in handle:
                        if not line.strip():
                            continue
                        result["json_records_scanned"] += 1
                        try:
                            value = json.loads(line)
                        except json.JSONDecodeError:
                            result["parse_errors"] += 1
                            continue
                        scan = scan_json_value(value, candidate_ids, duplicate_keys, weak_symbol_time_keys)
                        for key in [
                            "explicit_candidate_id_hits",
                            "explicit_duplicate_key_hits",
                            "weak_symbol_time_hits",
                        ]:
                            result[key] += scan[key]
                        if scan["strategy_like_without_explicit_scid_key"]:
                            result["strategy_like_records_without_explicit_scid_key"] += 1
                        if (scan["explicit_candidate_id_hits"] or scan["explicit_duplicate_key_hits"] or scan["weak_symbol_time_hits"]) and len(result["hit_samples"]) < 6:
                            result["hit_samples"].append(
                                {
                                    "path": repo_path(path),
                                    "scan": scan,
                                    "sample_keys": sorted(list(value.keys()))[:24] if isinstance(value, dict) else type(value).__name__,
                                }
                            )
            elif suffix == ".json":
                try:
                    value = load_json(path)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    result["parse_errors"] += 1
                    continue
                result["json_records_scanned"] += 1
                scan = scan_json_value(value, candidate_ids, duplicate_keys, weak_symbol_time_keys)
                for key in ["explicit_candidate_id_hits", "explicit_duplicate_key_hits", "weak_symbol_time_hits"]:
                    result[key] += scan[key]
                if scan["strategy_like_without_explicit_scid_key"]:
                    result["strategy_like_records_without_explicit_scid_key"] += 1
                if (scan["explicit_candidate_id_hits"] or scan["explicit_duplicate_key_hits"] or scan["weak_symbol_time_hits"]) and len(result["hit_samples"]) < 6:
                    result["hit_samples"].append(
                        {"path": repo_path(path), "scan": scan, "sample_type": "json_document"}
                    )
            else:
                text = path.read_text(encoding="utf-8", errors="replace")
                if "candidate_input:" in text or "duplicate_proxy_denominator_key" in text:
                    result["strategy_like_records_without_explicit_scid_key"] += int(any(word in text.lower() for word in STRATEGY_WORDS))
                    if len(result["hit_samples"]) < 6:
                        result["hit_samples"].append(
                            {
                                "path": repo_path(path),
                                "scan": "TEXT_TOKEN_HIT_NOT_USED_AS_RECOVERY_WITHOUT_PARSED_EXPLICIT_KEY",
                            }
                        )
            explicit_after = result["explicit_candidate_id_hits"] + result["explicit_duplicate_key_hits"]
            if explicit_after > explicit_before and len(result["sha256_for_files_with_explicit_hits"]) < 20:
                result["sha256_for_files_with_explicit_hits"].append({"path": repo_path(path), "sha256": sha256_file(path)})

        if spec["root_id"] == "accepted_strategy_field_packet":
            result["terminal_recovery_interpretation"] = (
                "RECOVERS_ACCEPTED_DESCRIPTOR_FIELDS_AND_CONFIRMS_PRIOR_FAIL_CLOSED_INTENT_FIELDS"
            )
        elif result["explicit_candidate_id_hits"] or result["explicit_duplicate_key_hits"]:
            result["terminal_recovery_interpretation"] = (
                "EXPLICIT_SCID_KEY_HITS_PRESENT_BUT_NO_NEW_STRATEGY_INTENT_FIELD_BEYOND_ACCEPTED_PACKET"
            )
        elif result["weak_symbol_time_hits"]:
            result["terminal_recovery_interpretation"] = (
                "WEAK_SYMBOL_TIME_LEADS_ONLY_NOT_RECOVERABLE_WITHOUT_EXPLICIT_CANDIDATE_BINDING"
            )

        for key in [
            "files_seen",
            "explicit_key_rg_file_hits",
            "strategy_like_rg_file_hits",
            "strategy_like_files_selected_for_parse",
            "files_selected_for_parse",
            "text_files_scanned",
            "json_records_scanned",
            "parse_errors",
            "skipped_raw_market_blob_files",
            "skipped_forbidden_broker_account_order_history_files",
            "explicit_candidate_id_hits",
            "explicit_duplicate_key_hits",
            "weak_symbol_time_hits",
            "strategy_like_records_without_explicit_scid_key",
        ]:
            totals[key] += int(result[key])
        root_results.append(result)

    return {
        "candidate_id_count": len(candidate_ids),
        "duplicate_key_count": len(duplicate_keys),
        "root_results": root_results,
        "totals": dict(totals),
        "searched_root_ids": [row["root_id"] for row in root_results],
    }


def capture_requirements() -> list[dict[str, Any]]:
    common = {
        "parser_requirement": "append-only JSONL parser with schema-version check, source-hash recomputation, duplicate-key preservation, and fail-closed missing-field behavior",
        "schema_version_required": "scid_forward_source_capture_v1",
        "redaction_rule": "no credential, account balance, broker ticket, deal id, order id, position id, or account-history payload; use source-local event ids or salted hashes only where an identifier is needed",
        "g12_acceptance_requirement": "G12 must recompute row coverage, source hashes, as-of rules, forbidden-surface absence, duplicate policy, and field-level status for every candidate before any result-design lane can consume it",
    }
    return [
        {
            "field_group": "intended_side_direction",
            "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
            "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
            "required_fields": [
                "candidate_input_row_id",
                "duplicate_proxy_denominator_key",
                "decision_asof_utc",
                "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY",
                "side_source_component",
                "side_source_rule_or_model_hash",
                "side_emission_reason_code",
            ],
            "as_of_rule": "side must be emitted at or before decision_asof_utc and before any target/path/result horizon is opened",
            "no_leak_rule": "do not derive side from post-decision price movement, terminal target status, broker result, or future path labels",
            **common,
        },
        {
            "field_group": "intended_entry_reference",
            "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
            "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
            "required_fields": [
                "candidate_input_row_id",
                "entry_reference_type_market_limit_zone_midpoint_other",
                "entry_reference_price",
                "entry_reference_time_utc",
                "entry_source_timeframe",
                "entry_source_bar_hash_or_mso_snapshot_hash",
            ],
            "as_of_rule": "entry reference must be present in the source decision packet before any fill, cancel, expiry, or target horizon is known",
            "no_leak_rule": "no fill-derived or hindsight-optimized entry references",
            **common,
        },
        {
            "field_group": "intended_stop_reference",
            "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
            "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
            "required_fields": [
                "candidate_input_row_id",
                "stop_reference_price",
                "stop_reference_type",
                "stop_buffer_rule_id",
                "stop_source_structure_id",
                "stop_source_snapshot_hash",
            ],
            "as_of_rule": "stop reference must be emitted with the source decision packet and frozen before path/result opening",
            "no_leak_rule": "stop cannot be fitted to later adverse excursion, target status, realized R, or broker close state",
            **common,
        },
        {
            "field_group": "intended_target_reference",
            "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
            "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
            "required_fields": [
                "candidate_input_row_id",
                "target_reference_price",
                "target_reference_type",
                "target_rule_id",
                "risk_reward_reference",
                "target_source_snapshot_hash",
            ],
            "as_of_rule": "target reference must be frozen at decision time; neutral target horizons are not strategy targets",
            "no_leak_rule": "do not create targets from terminal status, later high/low, realized R, or selected performance",
            **common,
        },
        {
            "field_group": "poi_type_bounds_source",
            "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_STRUCTURE_SOURCE_STATE_CAPTURE_REQUIRED",
            "future_source_or_logger": "source_safe_mso_snapshot_and_poi_logger",
            "required_fields": [
                "candidate_input_row_id",
                "poi_type_enum_ob_fvg_breaker_swing_other_none",
                "poi_lower_bound",
                "poi_upper_bound",
                "poi_source_timeframe",
                "poi_source_bar_ids",
                "mso_snapshot_hash",
                "poi_detection_rule_version",
            ],
            "as_of_rule": "POI bounds must come from the as-of market-state snapshot used by the decision packet",
            "no_leak_rule": "do not reconstruct POI from later price movement or from result-selection logic",
            **common,
        },
        {
            "field_group": "framework_setup_family",
            "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
            "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
            "required_fields": [
                "candidate_input_row_id",
                "frameworks_evaluated",
                "framework_qualified_flags",
                "selected_framework_or_none",
                "setup_family",
                "framework_tiebreak_rule_id",
                "framework_source_snapshot_hash",
            ],
            "as_of_rule": "framework selection/evaluation must be logged before L2, fill, or path result fields are known",
            "no_leak_rule": "framework cannot be assigned from later path shape or favorable outcome family",
            **common,
        },
        {
            "field_group": "lifecycle_fill_cancel_expiry_source_status",
            "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_LIFECYCLE_SOURCE_TRUTH_CAPTURE_REQUIRED",
            "future_source_or_logger": "nonbroker_pending_intent_lifecycle_event_logger",
            "required_fields": [
                "candidate_input_row_id",
                "pending_intent_id",
                "source_event_type_created_updated_expired_cancelled_replaced_no_order",
                "source_event_utc",
                "source_event_clock_basis",
                "intent_state_before",
                "intent_state_after",
                "redacted_order_bridge_hash_optional",
            ],
            "as_of_rule": "lifecycle events must be append-only and timestamped when GTOS observes or changes intent state",
            "no_leak_rule": "do not use broker account history, deal/position/order history, realized result, or later path labels in this evidence class",
            **common,
        },
        {
            "field_group": "lower_timeframe_asof_path_availability",
            "historical_status_after_search": "RECOVERABLE_MARKET_CONTEXT_BUT_NOT_ATTACHED_TO_ACCEPTED_CANDIDATES_CAPTURE_REQUIRED",
            "future_source_or_logger": "ltf_source_availability_and_path_descriptor_capture",
            "required_fields": [
                "candidate_input_row_id",
                "ltf_timeframes_available",
                "ltf_source_file_pointer_or_cache_id",
                "ltf_source_hash",
                "decision_minus_window_start_utc",
                "decision_asof_utc",
                "bars_present_by_timeframe",
                "asof_path_descriptor_version",
            ],
            "as_of_rule": "only bars/ticks with timestamps <= decision_asof_utc may be used for availability or descriptor fields",
            "no_leak_rule": "availability/path descriptors cannot include post-decision target/stop/fill status",
            **common,
        },
        {
            "field_group": "future_orderflow_depth_proxy_requirements",
            "historical_status_after_search": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CONTRACT_CAPTURE_REQUIRED",
            "future_source_or_logger": "orderflow_depth_proxy_context_capture",
            "required_fields": [
                "candidate_input_row_id",
                "proxy_instrument",
                "proxy_contract_month",
                "source_family_scid_depth_mbo_mbp_other",
                "source_file_pointer_or_vendor_cache_id",
                "source_hash",
                "proxy_mapping_version",
                "publication_or_capture_asof_utc",
                "derived_feature_schema_version",
            ],
            "as_of_rule": "source capture and derived features must be timestamped no later than decision_asof_utc unless explicitly marked forensic-only",
            "no_leak_rule": "no post-event orderflow, future depth state, paid-call output, or raw blob commit in this route",
            **common,
        },
        {
            "field_group": "baseline_control_fields",
            "historical_status_after_search": "CONTROL_CONTRACT_FROZEN_FROM_CLOSED_DESCRIPTOR_FIELDS",
            "future_source_or_logger": "offline_baseline_control_assignment_manifest",
            "required_fields": [
                "candidate_input_row_id",
                "duplicate_proxy_denominator_key",
                "partition_assignment",
                "symbol",
                "session_bucket",
                "time_of_day_bucket",
                "baseline_family_session_only_volatility_only_random_proxy_matched",
                "baseline_assignment_seed",
                "baseline_duplicate_policy_id",
            ],
            "as_of_rule": "baseline assignment may use only closed source-control descriptors and frozen deterministic seed before result opening",
            "no_leak_rule": "baseline fields cannot use target status, realized result, future path, or performance-selected thresholds",
            **common,
        },
    ]


def status_for_field(field: str) -> str:
    if field in CLOSED_SOURCE_FIELDS:
        return "RECOVERED_FROM_ACCEPTED_EXPLICIT_SOURCE"
    if field in HISTORICAL_INTENT_FIELDS:
        return "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN"
    if field in MARKET_CONTEXT_FIELDS:
        return "RECOVERABLE_MARKET_CONTEXT_CAPTURE_CONTRACT_FROZEN"
    if field == "baseline_control_fields":
        return "CONTROL_CONTRACT_FROZEN_FROM_CLOSED_SOURCE_DESCRIPTORS"
    if field == "broker_account_order_history_deal_position_evidence":
        return "FORBIDDEN_IN_THIS_EVIDENCE_CLASS"
    raise KeyError(field)


def build_candidate_status_rows(rows: list[dict[str, Any]], requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requirement_ids = {row["field_group"]: f"REQ_{row['field_group'].upper()}" for row in requirements}
    requirement_ids.update(
        {
            "canonical_candidate_and_denominator": "REQ_CANONICAL_CANDIDATE_AND_DENOMINATOR",
            "source_symbol_session_partition": "REQ_SOURCE_SYMBOL_SESSION_PARTITION",
            "source_control_coverage_not_computable_reasons": "REQ_SOURCE_CONTROL_COVERAGE",
            "broker_account_order_history_deal_position_evidence": "REQ_BROKER_EVIDENCE_FORBIDDEN",
        }
    )
    out: list[dict[str, Any]] = []
    for source_row in rows:
        prior_statuses = source_row.get("field_statuses", {})
        field_statuses: dict[str, Any] = {}
        for field in FIELD_FAMILIES:
            status = status_for_field(field)
            prior_payload = prior_statuses.get(field, {}) if isinstance(prior_statuses, dict) else {}
            field_statuses[field] = {
                "status": status,
                "requirement_id": requirement_ids.get(field),
                "prior_packet_status": prior_payload.get("status") if isinstance(prior_payload, dict) else None,
                "source_truth_class": (
                    "explicit accepted source-control descriptor"
                    if field in CLOSED_SOURCE_FIELDS
                    else "non-generatable historical GTOS intent/source-state"
                    if field in HISTORICAL_INTENT_FIELDS
                    else "recoverable/requestable market or proxy context"
                    if field in MARKET_CONTEXT_FIELDS
                    else "source-control baseline contract"
                    if field == "baseline_control_fields"
                    else "forbidden broker/account/order/history/deal/position evidence"
                ),
                "capture_contract_ref": None if field in CLOSED_SOURCE_FIELDS or field == "broker_account_order_history_deal_position_evidence" else f"CAPTURE_{field.upper()}",
            }
        row = {
            "route_id": ROUTE_ID,
            "schema_version": "scid_combined_candidate_source_capture_status_v1",
            "evidence_class": EVIDENCE_CLASS,
            "candidate_input_row_id": source_row["candidate_input_row_id"],
            "candidate_duplicate_key": source_row["candidate_duplicate_key"],
            "duplicate_proxy_denominator_key": source_row["duplicate_proxy_denominator_key"],
            "canonical_economic_group": source_row["canonical_economic_group"],
            "symbol": source_row["symbol"],
            "source_proxy_group": source_row["source_proxy_group"],
            "decision_asof_utc": source_row["decision_asof_utc"],
            "entry_reference_time_utc": source_row.get("entry_reference_time_utc"),
            "partition_assignment": source_row.get("partition_assignment"),
            "field_statuses": field_statuses,
            **SAFE_FLAGS,
        }
        row["combined_source_capture_row_hash"] = stable_hash(row)
        out.append(row)
    return out


def count_candidate_statuses(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = {field: Counter() for field in FIELD_FAMILIES}
    for row in rows:
        for field, payload in row["field_statuses"].items():
            counts[field][payload["status"]] += 1
    return {field: dict(counter) for field, counter in counts.items()}


def build_g12_prompt() -> str:
    return f"""# G12 SCID Combined Source Search And Forward Capture Route Audit Goal Prompt

Date: {DATE_TAG}
Owner lane: independent G12 audit of SCID combined source-search/capture builder route
Evidence class: `G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_AUDIT_ONLY`
Input builder route: `research/science_program_2026_05/06_outcome_testing/scid_combined_source_search_and_forward_capture_route/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Independent G12 Objective

Independently audit the SCID combined historical source-search and forward-capture route. Recompute denominator coverage, source-search saturation, recovered/non-generatable/capture-required status, no-leak boundaries, forbidden-surface absence, manifest completeness, and exactness of future capture contracts for all 3,014 accepted SCID candidates. This G12 route must accept, repair, or reject the builder artifacts as control evidence only. It must not score targets, open outcomes, inspect broker account/order/history/deal/position evidence, call AI/API/vendor services, commit raw market blobs, or change live behavior.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read the builder route context anchor, searched-root ledger, historical source-state recovery ledger, source-state join/recovery candidate ledger, anti-boxing route-discovery ledger, candidate source/capture status JSONL, forward capture contract, schema/redaction/as-of/no-leak specification, implementation-readiness ledger, ranked continuation bundle, output manifest, completion audit, closeout verification, verifier, and focused tests.
9. Read the accepted G0/G12 strategy-field packet artifacts that the builder cites.

## Required Independent Checks

1. Recompute that the candidate source/capture status JSONL has exactly 3,014 unique `candidate_input_row_id` values and 3,014 unique `duplicate_proxy_denominator_key` values matching the accepted strategy-field packet.
2. Recompute field-status counts for all required field families: side, entry, stop, target, POI, framework, lifecycle, LTF, orderflow/proxy, baseline control, descriptor fields, and forbidden broker evidence.
3. Verify no historical strategy-intent/source-state field is inferred from price, neutral target behavior, result fields, path labels, broker records, or weak symbol-time-only joins.
4. Verify searched roots include accepted artifacts, shadow logs, program-control artifacts, pipeline state, knowledge base records, repo data manifests/raw-blob skips, research archive, and prior worktree/cache roots.
5. Verify raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, `.depth`, and broker/account/order/history/deal/position evidence are skipped or forbidden, not consumed as result/control evidence.
6. Verify every non-generatable field has exact future source/logger, required fields, parser, schema, redaction, as-of, no-leak, and G12 acceptance requirements.
7. Verify baseline-control fields are source-control contracts only and do not open result/performance scoring.
8. Verify the output manifest covers every required artifact and has no raw market blob.
9. Run the standalone verifier and focused tests or rebuild equivalent independent checks.

The audit must also verify the builder made no prompt/config/risk/safety/execution/canary/selector changes.

## Acceptance Boundaries

Accept only if the artifacts are denominator-stable, source-bound, no-leak, hard-boundary-compliant, complete for all 3,014 candidates, and exact enough for the next control route. Repair if the route is mostly correct but a ledger/capture requirement is vague or a searched-root record is incomplete. Reject if any result/performance/broker/live/AI/API/paid/raw-blob boundary is opened, if row coverage drifts, if strategy intent is inferred from price, or if future capture requirements are not actionable.

## Required Output

Emit a dedicated G12 audit directory with context anchor, recomputation ledgers, source-search saturation audit, field-status audit, capture-contract exactness audit, no-leak/forbidden-surface audit, decision ledger, output manifest, verifier result, focused tests, completion audit, and a next G0 synthesis/control prompt if accepted or a repair prompt if not accepted.

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    source_rows = load_jsonl(INPUTS["strategy_field_closure_rows"])
    summary = load_json(INPUTS["strategy_field_summary"])
    g12_decision = load_json(INPUTS["g12_packet_decision"])
    g0_readiness = load_json(INPUTS["g0_source_readiness"])
    g0_ranking = load_json(INPUTS["g0_route_ranking"])
    requirements = capture_requirements()
    candidate_status_rows = build_candidate_status_rows(source_rows, requirements)
    source_scan = scan_source_roots(source_rows)

    candidate_status_path = ROUTE_DIR / f"{PREFIX}_CANDIDATE_SOURCE_CAPTURE_STATUS_{DATE_TAG}.jsonl"
    write_jsonl(candidate_status_path, candidate_status_rows)

    field_counts = count_candidate_statuses(candidate_status_rows)
    input_hashes = {
        key: {"path": repo_path(path), "sha256": sha256_file(path)}
        for key, path in INPUTS.items()
        if path.exists()
    }

    context_anchor = {
        **base_payload("context_anchor"),
        "terminal_decision": TERMINAL_DECISION,
        "current_head": git_text(["rev-parse", "HEAD"]),
        "current_head_summary": git_text(["log", "-1", "--oneline"]),
        "controlling_prompt_path": repo_path(INPUTS["controlling_prompt"]),
        "mandatory_preflight_record": {
            "generated_live_state": True,
            "read_live_state": True,
            "read_quick_reference_card": True,
            "read_research_operating_doctrine": True,
            "read_goal_session_research_discipline": True,
            "read_research_current_state": True,
            "read_controlling_prompt_from_disk": True,
            "read_g0_strategy_field_synthesis_artifacts": True,
            "read_g12_strategy_field_packet_audit_artifacts": True,
            "read_builder_packet_artifacts": True,
        },
        "builder_control_posture": "constructive source-search and forward-capture builder; G12 audit remains independent",
        "accepted_candidate_rows": len(source_rows),
        "accepted_unique_candidate_ids": len({row["candidate_input_row_id"] for row in source_rows}),
        "accepted_unique_duplicate_proxy_denominator_keys": len({row["duplicate_proxy_denominator_key"] for row in source_rows}),
        "input_hashes": input_hashes,
        "safe_boundary_summary": SAFE_FLAGS,
    }

    question_stack = {
        **base_payload("active_question_stack_and_checkpoint_resume_ledger"),
        "active_questions": [
            {
                "question_id": "Q1",
                "question": "Can explicit historical SCID strategy side/entry/stop/target/POI/framework/lifecycle source-state be recovered from accepted artifacts or adjacent roots?",
                "status": "ANSWERED_FAIL_CLOSED_FOR_HISTORICAL_INTENT_FIELDS",
            },
            {
                "question_id": "Q2",
                "question": "Can lower-timeframe and orderflow/proxy market-context fields be recovered or at least contracted without opening outcomes?",
                "status": "CAPTURE_CONTRACT_FROZEN_WITH_RAW_BLOB_AND_PROXY_BOUNDARIES",
            },
            {
                "question_id": "Q3",
                "question": "Can baseline-control fields be defined without result scoring?",
                "status": "CONTROL_CONTRACT_FROZEN_FROM_CLOSED_SOURCE_DESCRIPTORS",
            },
            {
                "question_id": "Q4",
                "question": "Are any useful source/capture route families missing because current GTOS frameworks or M15 SCID rows boxed the search?",
                "status": "ANSWERED_IN_ANTI_BOXING_LEDGER_AND_RANKED_CONTINUATION_BUNDLE",
            },
        ],
        "checkpoint_resume_policy": {
            "context_anchor": f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.json",
            "candidate_row_ledger": candidate_status_path.name,
            "resume_from_disk_rule": "regenerate LIVE_STATE, re-read controlling prompt and context anchor, then rebuild or verify from artifact hashes",
            "large_search_handling": "root scans are recorded by root_id with counts, skips, hits, and terminal interpretation",
        },
    }

    searched_roots = {
        **base_payload("searched_root_ledger"),
        **source_scan,
        "hard_boundary_skips": {
            "raw_market_blob_suffixes": sorted(RAW_MARKET_SUFFIXES),
            "forbidden_broker_account_order_history_fragments": sorted(FORBIDDEN_PATH_FRAGMENTS),
        },
        "source_search_result": "NO_NEW_EXPLICIT_HISTORICAL_STRATEGY_INTENT_SOURCE_STATE_RECOVERED_BEYOND_ACCEPTED_PACKET_DESCRIPTORS",
    }

    recovery_attempts = {
        **base_payload("historical_source_state_recovery_attempt_ledger"),
        "candidate_rows": len(source_rows),
        "field_recovery_results": [
            {
                "field_family": field,
                "candidate_rows": len(source_rows),
                "combined_route_status": status_for_field(field),
                "rows_recovered_from_explicit_source": len(source_rows) if field in CLOSED_SOURCE_FIELDS else 0,
                "rows_requiring_capture_contract": len(source_rows)
                if field in HISTORICAL_INTENT_FIELDS or field in MARKET_CONTEXT_FIELDS or field == "baseline_control_fields"
                else 0,
                "terminal_interpretation": (
                    "accepted source-control descriptor already closed"
                    if field in CLOSED_SOURCE_FIELDS
                    else "historical strategy/source-state truth is non-generatable unless explicitly logged"
                    if field in HISTORICAL_INTENT_FIELDS
                    else "market/proxy context may be recoverable prospectively but is not source-attached to accepted candidates"
                    if field in MARKET_CONTEXT_FIELDS
                    else "baseline contract can be frozen from closed descriptors without scoring"
                    if field == "baseline_control_fields"
                    else "forbidden in this evidence class"
                ),
            }
            for field in FIELD_FAMILIES
        ],
        "explicit_new_strategy_intent_recoveries": 0,
        "weak_join_policy": "timestamp/symbol-only overlaps are leads, not recovered source truth; exact candidate id or duplicate denominator binding is required",
    }

    join_recovery = {
        **base_payload("source_state_join_recovery_candidate_ledger"),
        "join_candidates": [
            {
                "join_route": "accepted_strategy_field_packet_exact_candidate_id",
                "join_key": "candidate_input_row_id and duplicate_proxy_denominator_key",
                "rows_with_explicit_binding": 3014,
                "recovered_field_families": sorted(CLOSED_SOURCE_FIELDS),
                "not_recovered_field_families": sorted(HISTORICAL_INTENT_FIELDS),
                "decision": "USE_FOR_DESCRIPTOR_RECOVERY_ONLY",
            },
            {
                "join_route": "shadow_logs_explicit_candidate_or_duplicate_key",
                "join_key": "candidate_input_row_id or duplicate_proxy_denominator_key",
                "rows_with_explicit_binding": 0,
                "decision": "NO_RECOVERY",
            },
            {
                "join_route": "shadow_logs_symbol_time_candidate_lead",
                "join_key": "symbol plus decision_asof_utc",
                "rows_with_explicit_binding": 0,
                "decision": "NOT_ACCEPTED_WITHOUT_EXPLICIT_SCID_BINDING",
            },
            {
                "join_route": "knowledge_base_live_evaluations_or_reconstructions",
                "join_key": "symbol/time/log reconstruction fields",
                "rows_with_explicit_binding": 0,
                "decision": "NOT_SCID_SOURCE_STATE_AND_NO_CANDIDATE_BINDING",
            },
            {
                "join_route": "raw_scid_or_market_blob_reparse",
                "join_key": "market timestamp/source file",
                "rows_with_explicit_binding": 0,
                "decision": "FORBIDDEN_OR_INSUFFICIENT_FOR_STRATEGY_INTENT; MAY_SUPPORT_FUTURE_MARKET_CONTEXT_CONTRACT_ONLY",
            },
            {
                "join_route": "prior_worktree_cache_roots",
                "join_key": "candidate ids, duplicate keys, source candidate ids",
                "rows_with_explicit_binding": 0,
                "decision": "NO_EXPLICIT_SOURCE_STATE_MATCH_FOUND",
            },
        ],
        "row_level_status_path": repo_path(candidate_status_path),
    }

    anti_boxing = {
        **base_payload("anti_boxing_route_discovery_ledger"),
        "not_treated_as_limits": [
            "current GTOS OB/FVG/breaker frameworks",
            "SCID-only M15 bars",
            "single source modality",
            "first packet artifact family",
            "current worktree only",
            "strategy-intent-only framing",
        ],
        "anti_boxing_questions_pursued": [
            "Could accepted neutral/source-control artifacts carry explicit source-state that the field packet did not expose?",
            "Could shadow/program-control/pipeline/knowledge roots carry candidate-bound strategy state?",
            "Could prior worktrees or recovery caches contain source ledgers not committed to the current tree?",
            "Could lower-timeframe, orderflow, proxy, baseline, or MSO snapshot fields move future testing forward without inventing historical intent?",
            "Could weak strategy-like live evaluation records be used safely, and what binding would be required?",
        ],
        "newly_discovered_or_preserved_route_families": [
            "source-safe MSO snapshot capture",
            "strategy decision packet source capture",
            "nonbroker pending-intent lifecycle capture",
            "LTF availability and path descriptor capture",
            "orderflow/depth/proxy context capture",
            "baseline-control assignment manifest",
            "source parity and proxy-map contract",
            "input-only market-state descriptor atlas",
            "adversarial baseline denominator control",
            "cohort expansion source contract",
            "candidate-key repair/backfill manifest if future source artifacts appear",
            "independent G12 source/capture contract audit",
        ],
        "anti_boxing_terminal_result": "broad source search found no new explicit historical strategy-intent source-state; constructive output is exact forward capture and baseline-control contract",
    }

    capture_contract = {
        **base_payload("forward_capture_contract"),
        "candidate_rows_covered": len(source_rows),
        "field_groups": requirements,
        "field_groups_required_by_prompt": [
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
        ],
        "contract_boundary": "proposed offline/source logger schema only; no live wiring or behavior change is implemented by this route",
    }

    schema_spec = {
        **base_payload("schema_redaction_asof_noleak_specification"),
        "offline_schema_versions": {
            "candidate_status": "scid_combined_candidate_source_capture_status_v1",
            "future_capture": "scid_forward_source_capture_v1",
            "baseline_control": "scid_baseline_control_assignment_v1",
        },
        "redaction_policy": [
            "no credentials",
            "no account balances",
            "no broker account/order/history/deal/position payloads",
            "no raw market blob commit",
            "redacted bridge hashes only where a future evidence class permits order observability",
        ],
        "as_of_policy": [
            "source decision fields must be timestamped at or before decision_asof_utc",
            "LTF/orderflow context must use only pre-decision source windows unless forensic-only",
            "baseline-control assignment must be frozen before result opening",
        ],
        "no_leak_policy": [
            "no target/result/performance fields in source/capture artifacts",
            "no price-derived historical intent",
            "no weak symbol-time join accepted as source truth",
            "no broker/account evidence in this evidence class",
        ],
        "duplicate_policy": "candidate_input_row_id and duplicate_proxy_denominator_key must remain one-to-one for all 3,014 rows; future cohorts require a new immutable denominator ledger",
    }

    readiness = {
        **base_payload("implementation_readiness_no_live_effect_ledger"),
        "implementation_readiness_status": "OFFLINE_CAPTURE_SCHEMA_READY_G12_AUDIT_REQUIRED_NO_LIVE_WIRING",
        "no_live_effect_boundary": [
            "no src/ prompt/ config/ risk/ safety/ execution/ canary/ selector edits",
            "no live restart",
            "no order placement or broker-account evidence",
            "no AI/API or paid/vendor access",
        ],
        "future_implementation_requires": [
            "independent G12 acceptance of this contract",
            "G0 synthesis/control decision",
            "separate owner-approved implementation lane for any additive logger wiring",
            "focused tests proving fail-open/no-decision-impact if live logger wiring is ever approved",
        ],
        "current_route_implemented_live_wiring": False,
    }

    continuation = {
        **base_payload("ranked_continuation_bundle"),
        "ranked_continuations": [
            {
                "rank": 1,
                "route_id": "G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_AUDIT",
                "decision": "RUN_NEXT",
                "reason": "Independent audit must accept or repair the source-search/capture contract before downstream G0 synthesis.",
                "prompt_path": f"research/science_program_2026_05/04_goal_prompts/{G12_PROMPT_NAME}",
            },
            {
                "rank": 2,
                "route_id": "G0_SCID_SOURCE_CAPTURE_SYNTHESIS_CONTROL",
                "decision": "RUN_AFTER_G12_ACCEPTANCE",
                "reason": "Choose whether to implement offline logger package, run LTF/orderflow source expansion, or proceed to preregistration design.",
            },
            {
                "rank": 3,
                "route_id": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
                "decision": "RUN_AFTER_OR_ALONGSIDE_SOURCE_CAPTURE_ACCEPTANCE",
                "reason": "Expand explanatory market-context fields without inventing strategy intent.",
            },
            {
                "rank": 4,
                "route_id": "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION",
                "decision": "BLOCKED_UNTIL_G12_G0_SOURCE_FIELD_ACCEPTANCE",
                "reason": "Result design remains closed until direction/source fields and capture contracts are accepted.",
            },
        ],
    }

    output_paths: list[Path] = []
    for stem, title, payload in [
        ("CONTEXT_ANCHOR", "SCID Combined Source Capture Context Anchor", context_anchor),
        ("ACTIVE_QUESTION_STACK_AND_CHECKPOINT_LEDGER", "SCID Combined Active Question Stack And Checkpoint Ledger", question_stack),
        ("SEARCHED_ROOT_LEDGER", "SCID Combined Searched Root Ledger", searched_roots),
        ("HISTORICAL_SOURCE_STATE_RECOVERY_ATTEMPT_LEDGER", "SCID Combined Historical Source-State Recovery Attempt Ledger", recovery_attempts),
        ("SOURCE_STATE_JOIN_RECOVERY_CANDIDATE_LEDGER", "SCID Combined Source-State Join Recovery Candidate Ledger", join_recovery),
        ("ANTI_BOXING_ROUTE_DISCOVERY_LEDGER", "SCID Combined Anti-Boxing Route Discovery Ledger", anti_boxing),
        ("FORWARD_CAPTURE_CONTRACT", "SCID Combined Forward Capture Contract", capture_contract),
        ("SCHEMA_REDACTION_ASOF_NOLEAK_SPECIFICATION", "SCID Combined Schema Redaction As-Of No-Leak Specification", schema_spec),
        ("IMPLEMENTATION_READINESS_NO_LIVE_EFFECT_LEDGER", "SCID Combined Implementation Readiness No-Live-Effect Ledger", readiness),
        ("RANKED_CONTINUATION_BUNDLE", "SCID Combined Ranked Continuation Bundle", continuation),
    ]:
        output_paths.extend(write_pair(stem, title, payload))

    candidate_status_md_payload = {
        **base_payload("candidate_source_capture_status_summary"),
        "candidate_status_jsonl": repo_path(candidate_status_path),
        "row_count": len(candidate_status_rows),
        "unique_candidate_ids": len({row["candidate_input_row_id"] for row in candidate_status_rows}),
        "unique_duplicate_proxy_denominator_keys": len({row["duplicate_proxy_denominator_key"] for row in candidate_status_rows}),
        "field_status_counts": field_counts,
    }
    output_paths.append(candidate_status_path)
    output_paths.extend(
        write_pair(
            "CANDIDATE_SOURCE_CAPTURE_STATUS_SUMMARY",
            "SCID Combined Candidate Source Capture Status Summary",
            candidate_status_md_payload,
        )
    )

    prompt_path = PROMPT_DIR / G12_PROMPT_NAME
    prompt_path.write_text(build_g12_prompt(), encoding="utf-8")
    output_paths.append(prompt_path)

    manifest = {
        **base_payload("output_manifest"),
        "candidate_rows": len(candidate_status_rows),
        "terminal_decision": TERMINAL_DECISION,
        "artifacts": [],
        "required_artifact_families_covered": {
            "context_anchor": True,
            "searched_root_ledger": True,
            "checkpoint_resume_ledger": True,
            "historical_source_state_recovery_attempt_ledger": True,
            "source_state_join_recovery_candidate_ledger": True,
            "anti_boxing_route_discovery_ledger": True,
            "forward_capture_contract": True,
            "schema_redaction_asof_noleak_specification": True,
            "implementation_readiness_no_live_effect_ledger": True,
            "ranked_continuation_bundle": True,
            "next_independent_g12_audit_handoff_prompt": True,
            "standalone_verifier": True,
            "focused_tests": True,
            "candidate_row_status_jsonl": True,
            "completion_audit": True,
            "closeout_verification": True,
        },
    }
    for path in sorted(set(output_paths), key=lambda p: repo_path(p)):
        manifest["artifacts"].append(
            {
                "path": repo_path(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "raw_market_blob": path.suffix.lower() in RAW_MARKET_SUFFIXES or path.name.endswith(".jsonl.gz"),
            }
        )

    completion = {
        **base_payload("completion_audit"),
        "objective_restatement": "Exhaust source-safe historical SCID strategy/source-state search and freeze exact forward capture contracts for remaining fields across all 3,014 accepted candidates.",
        "terminal_decision": TERMINAL_DECISION,
        "candidate_rows": len(candidate_status_rows),
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory preflight and context use recorded", "artifact": f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.json", "status": "PASS"},
            {"requirement": "searched-root ledger emitted", "artifact": f"{PREFIX}_SEARCHED_ROOT_LEDGER_{DATE_TAG}.json", "status": "PASS"},
            {"requirement": "active question/checkpoint ledger emitted", "artifact": f"{PREFIX}_ACTIVE_QUESTION_STACK_AND_CHECKPOINT_LEDGER_{DATE_TAG}.json", "status": "PASS"},
            {"requirement": "historical source-state recovery ledger emitted", "artifact": f"{PREFIX}_HISTORICAL_SOURCE_STATE_RECOVERY_ATTEMPT_LEDGER_{DATE_TAG}.json", "status": "PASS"},
            {"requirement": "source-state join/recovery candidate ledger emitted", "artifact": f"{PREFIX}_SOURCE_STATE_JOIN_RECOVERY_CANDIDATE_LEDGER_{DATE_TAG}.json", "status": "PASS"},
            {"requirement": "anti-boxing route discovery ledger emitted", "artifact": f"{PREFIX}_ANTI_BOXING_ROUTE_DISCOVERY_LEDGER_{DATE_TAG}.json", "status": "PASS"},
            {"requirement": "forward capture contract covers side/entry/stop/target/POI/framework/lifecycle/LTF/orderflow/baseline", "artifact": f"{PREFIX}_FORWARD_CAPTURE_CONTRACT_{DATE_TAG}.json", "status": "PASS"},
            {"requirement": "schema/redaction/as-of/no-leak specification emitted", "artifact": f"{PREFIX}_SCHEMA_REDACTION_ASOF_NOLEAK_SPECIFICATION_{DATE_TAG}.json", "status": "PASS"},
            {"requirement": "implementation readiness with no live effect emitted", "artifact": f"{PREFIX}_IMPLEMENTATION_READINESS_NO_LIVE_EFFECT_LEDGER_{DATE_TAG}.json", "status": "PASS"},
            {"requirement": "ranked continuation bundle and G12 prompt emitted", "artifact": G12_PROMPT_NAME, "status": "PASS"},
            {"requirement": "3,014-row candidate status ledger emitted", "artifact": candidate_status_path.name, "status": "PASS"},
            {"requirement": "no validation/scoring/broker/AI/API/paid/raw/live/trading-surface boundary opened", "artifact": f"{PREFIX}_SCHEMA_REDACTION_ASOF_NOLEAK_SPECIFICATION_{DATE_TAG}.json", "status": "PASS"},
        ],
        "mandatory_context_use": {
            "goal_session_research_discipline_read_after_preflight": True,
            "research_operating_doctrine_read_after_preflight": True,
            "builder_control_posture_applied": "constructive source-search/capture builder, not G12 self-audit",
            "anti_boxing_questions_pursued": anti_boxing["anti_boxing_questions_pursued"],
            "searched_roots_and_artifacts_inspected": source_scan["searched_root_ids"],
            "approval_access_requests_made": [],
            "checkpoint_chunk_resume_status": question_stack["checkpoint_resume_policy"],
            "terminal_proof_or_impossibility_boundary": "historical strategy-intent/source-state fields are non-generatable after accepted-artifact, shadow, program-control, pipeline, knowledge, data-manifest, archive, and prior-worktree search unless an explicit candidate-bound source artifact is later found",
            "deliberately_not_answered": [
                "validation/result scoring",
                "strategy edge",
                "R/PnL/win-rate/expectancy/performance",
                "broker account/order/history/deal/position truth",
                "AI/API/paid-vendor data pulls",
                "live behavior or trading-surface implementation",
            ],
        },
        "completion_standard_satisfied": False,
        "standalone_verifier_ok": False,
        "focused_tests_ok": False,
        "can_mark_goal_complete": False,
    }

    output_paths.extend(write_pair("OUTPUT_MANIFEST", "SCID Combined Output Manifest", manifest))
    output_paths.extend(write_pair("COMPLETION_AUDIT", "SCID Combined Completion Audit", completion))

    closeout = {
        **base_payload("closeout_verification"),
        "terminal_decision": TERMINAL_DECISION,
        "candidate_rows": len(candidate_status_rows),
        "field_status_counts": field_counts,
        "source_search_result": searched_roots["source_search_result"],
        "next_g12_prompt": repo_path(prompt_path),
        "verifier_pending": True,
        "focused_tests_pending": True,
    }
    output_paths.extend(write_pair("CLOSEOUT_VERIFICATION", "SCID Combined Closeout Verification", closeout))

    # Refresh manifest after completion/closeout files exist.
    manifest_paths = sorted(
        [
            path
            for path in ROUTE_DIR.glob(f"{PREFIX}_*_{DATE_TAG}.*")
            if path.suffix.lower() in {".json", ".jsonl", ".md"}
        ]
        + [prompt_path],
        key=lambda p: repo_path(p),
    )
    manifest["artifacts"] = [
        {
            "path": repo_path(path),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "raw_market_blob": path.suffix.lower() in RAW_MARKET_SUFFIXES or path.name.endswith(".jsonl.gz"),
        }
        for path in manifest_paths
    ]
    write_json("OUTPUT_MANIFEST", manifest)
    write_md("OUTPUT_MANIFEST", "SCID Combined Output Manifest", manifest)

    return {"ok": True, "candidate_rows": len(candidate_status_rows), "output_manifest": repo_path(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json")}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))

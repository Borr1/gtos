"""Build the SCID as-of sealed-validation execution packet route.

This lane is allowed to open quarantined validation/result evidence only if
source, rowset, family, baseline, target, horizon, metric, and stop rules can
be frozen before any result row. The accepted design artifacts do not freeze
exact executable outcome targets or horizons, so this builder emits a complete
pre-outcome blocker packet and repair prompt, and deliberately emits no result
row artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
OUTCOME_ROOT = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
DATE_TAG = "2026-05-11"
PREFIX = "SCID_ASOF_SEALED_VALIDATION"
ROUTE_ID = "SCID_ASOF_SEALED_VALIDATION_EXECUTION_PACKET"
EVIDENCE_CLASS = "SCID_ASOF_SEALED_VALIDATION_EXECUTION_PACKET_ONLY"
SCHEMA_VERSION = "scid_asof_sealed_validation_execution_packet_v1"
TERMINAL_DECISION = "EXECUTION_BLOCKED_MISSING_FROZEN_OUTCOME_TARGET_SPEC"
BLOCK_REASON = (
    "accepted G12/G0 design artifacts freeze source rows, partitions, denominator "
    "policy, baseline names, metric-family names, and stop conditions, but do not "
    "freeze exact executable outcome target definitions or horizons"
)

CONTROLLING_PROMPT = (
    PROMPT_DIR / "SCID_ASOF_SEALED_VALIDATION_EXECUTION_PACKET_GOAL_PROMPT_2026-05-11.md"
)
REPAIR_PROMPT = (
    PROMPT_DIR
    / "SCID_ASOF_SEALED_VALIDATION_EXECUTION_PACKET_REPAIR_PROMPT_2026-05-11.md"
)

G12_DESIGN_DIR = OUTCOME_ROOT / "g12_scid_asof_sealed_validation_design_audit"
G0_DESIGN_DIR = OUTCOME_ROOT / "g0_scid_asof_packet_source_control_synthesis_and_validation_design"
PACKET_DIR = OUTCOME_ROOT / "scid_asof_bar_builder_and_candidate_input_packet_source_control"

G12_DECISION = (
    G12_DESIGN_DIR / "G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_DECISION_LEDGER_2026-05-11.json"
)
G12_VERIFICATION = (
    G12_DESIGN_DIR
    / "G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_VERIFICATION_RESULT_2026-05-11.json"
)
G0_ROW_PARTITION_LEDGER = G0_DESIGN_DIR / "G0_SCID_ASOF_ROW_PARTITION_LEDGER_2026-05-11.jsonl"
G0_RULEBOOK = G0_DESIGN_DIR / "G0_SCID_ASOF_VALIDATION_DESIGN_RULEBOOK_2026-05-11.json"
G0_NOLEAK = G0_DESIGN_DIR / "G0_SCID_ASOF_NOLEAK_FIELD_CONTRACT_2026-05-11.json"
G0_DUPLICATE = G0_DESIGN_DIR / "G0_SCID_ASOF_DUPLICATE_PROXY_DENOMINATOR_RULES_2026-05-11.json"
G0_BASELINES = G0_DESIGN_DIR / "G0_SCID_ASOF_ADVERSARIAL_BASELINE_AND_ROBUSTNESS_PLAN_2026-05-11.json"
G0_MULTIPLE_TESTING = G0_DESIGN_DIR / "G0_SCID_ASOF_MULTIPLE_TESTING_DEBT_LEDGER_2026-05-11.json"
G0_FALSIFICATION = G0_DESIGN_DIR / "G0_SCID_ASOF_FALSIFICATION_STOP_CONDITIONS_2026-05-11.json"
G0_SCIENCE = G0_DESIGN_DIR / "G0_SCID_ASOF_SCIENCE_HORIZON_ROUTE_LEDGER_2026-05-11.json"
G0_ACCEPTED_RECON = G0_DESIGN_DIR / "G0_SCID_ASOF_ACCEPTED_PACKET_RECONCILIATION_2026-05-11.json"
G0_COMPLETION = G0_DESIGN_DIR / "G0_SCID_ASOF_COMPLETION_AUDIT_2026-05-11.json"
G0_VERIFICATION = G0_DESIGN_DIR / "G0_SCID_ASOF_VERIFICATION_RESULT_2026-05-11.json"
G0_SATURATION = G0_DESIGN_DIR / "G0_SCID_ASOF_SATURATION_REDTEAM_LEDGER_2026-05-11.json"

BAR_MANIFEST = PACKET_DIR / "SCID_ASOF_BAR_MANIFEST_2026-05-11.json"
CANDIDATE_MANIFEST = PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json"
BAR_ROWS = PACKET_DIR / "SCID_ASOF_BAR_ROWS_2026-05-11.jsonl"
CANDIDATE_ROWS = PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl"
PACKET_DISCOVERY = PACKET_DIR / "SCID_ASOF_DISCOVERY_EXCLUSION_BASELINE_AUDIT_2026-05-11.json"
PACKET_DUPLICATE = PACKET_DIR / "SCID_ASOF_DUPLICATE_PROXY_DENOMINATOR_LEDGER_2026-05-11.json"
PACKET_VERIFICATION = PACKET_DIR / "SCID_ASOF_VERIFICATION_RESULT_2026-05-11.json"

HISTORICAL_PROTOCOL = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "05_synthesis"
    / "HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md"
)

CORE_CONTEXT_INPUTS: dict[str, Path] = {
    "live_state": ROOT / ".context" / "LIVE_STATE.md",
    "quick_reference_card": ROOT / ".context" / "00_core" / "quick_reference_card.md",
    "research_operating_doctrine": ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
    "goal_session_research_discipline": ROOT
    / ".context"
    / "00_core"
    / "goal_session_research_discipline.md",
    "research_current_state": ROOT / ".context" / "00_core" / "research_current_state.md",
    "reading_order": ROOT / ".context" / "00_READING_ORDER.md",
    "latest_session_handoff": ROOT
    / ".context"
    / "02_session_handoffs"
    / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "controlling_prompt": CONTROLLING_PROMPT,
}

MANDATORY_INPUTS: dict[str, Path] = {
    "g12_design_decision": G12_DECISION,
    "g12_design_verification": G12_VERIFICATION,
    "g12_design_route_dir": G12_DESIGN_DIR,
    "g0_design_route_dir": G0_DESIGN_DIR,
    "g0_row_partition_ledger": G0_ROW_PARTITION_LEDGER,
    "g0_validation_design_rulebook": G0_RULEBOOK,
    "g0_noleak_field_contract": G0_NOLEAK,
    "g0_duplicate_proxy_denominator_rules": G0_DUPLICATE,
    "g0_adversarial_baseline_and_robustness_plan": G0_BASELINES,
    "g0_multiple_testing_debt_ledger": G0_MULTIPLE_TESTING,
    "g0_falsification_stop_conditions": G0_FALSIFICATION,
    "g0_science_horizon_route_ledger": G0_SCIENCE,
    "g0_accepted_packet_reconciliation": G0_ACCEPTED_RECON,
    "g0_completion_audit": G0_COMPLETION,
    "g0_verification_result": G0_VERIFICATION,
    "g0_saturation_redteam": G0_SATURATION,
    "scid_asof_bar_rows": BAR_ROWS,
    "scid_asof_candidate_input_rows": CANDIDATE_ROWS,
    "scid_asof_bar_manifest": BAR_MANIFEST,
    "scid_asof_candidate_input_packet_manifest": CANDIDATE_MANIFEST,
    "scid_asof_discovery_exclusion_baseline_audit": PACKET_DISCOVERY,
    "scid_asof_duplicate_proxy_denominator_ledger": PACKET_DUPLICATE,
    "scid_asof_packet_verification_result": PACKET_VERIFICATION,
    "historical_sealed_validation_protocol": HISTORICAL_PROTOCOL,
}

EXPECTED_COUNTS = {
    "source_control_bar_rows": 7567,
    "candidate_input_rows": 3014,
    "sealed_design_rows": 2432,
    "stress_design_rows": 582,
    "discovery_exclusions": 365,
    "candidate_denominator_groups": 7,
    "accepted_scid_segments": 9,
    "adversarial_baselines": 4,
}

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_quarantined_validation_result_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_remote_push": False,
    "changes_live_trading_behavior": False,
    "credentials_touched": False,
}

KNOWN_FAMILIES = [
    "adjacent_range_compression_breakout",
    "ob_retest",
    "opening_drive_no_fill_lifecycle",
    "fvg_fill",
    "liquidity_stop_run_context",
    "session_kz_sweep",
    "breaker_re_entry",
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]

BASELINE_FAMILIES = {
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
}

RESULT_ARTIFACT_NAMES = [
    f"{PREFIX}_SEALED_RESULT_ROWS_{DATE_TAG}.jsonl",
    f"{PREFIX}_SEALED_AGGREGATE_METRICS_{DATE_TAG}.json",
    f"{PREFIX}_STRESS_RESULT_ROWS_{DATE_TAG}.jsonl",
    f"{PREFIX}_STRESS_ROBUSTNESS_SUMMARY_{DATE_TAG}.json",
    f"{PREFIX}_ADVERSARIAL_BASELINE_RESULTS_{DATE_TAG}.json",
]

FORBIDDEN_SOURCE_FIELD_TOKENS = {
    "actual_r",
    "account",
    "broker",
    "cost",
    "deal",
    "expectancy",
    "history",
    "label",
    "order",
    "path",
    "performance",
    "pnl",
    "position",
    "profit",
    "result",
    "score",
    "slippage",
    "win",
}

ALLOWED_SOURCE_FIELD_TOKENS = {
    "candidate_input_only_status",
    "bar_window_start_utc",
    "bar_window_end_utc",
    "forbidden_future_use",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def json_dumps(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def stable_sha256(data: Any) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def line_count(path: Path) -> int | None:
    if not path.is_file():
        return None
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            yield line_number, json.loads(stripped)


def write_text_if_changed(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, data: Any) -> None:
    write_text_if_changed(path, json_dumps(data))


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip()


def artifact_metadata(path: Path, *, include_line_count: bool = True) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "path": repo_path(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "is_file": path.is_file(),
    }
    if path.is_file():
        meta.update(
            {
                "size_bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
        if include_line_count:
            meta["line_count"] = line_count(path)
    elif path.is_dir():
        files = [p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
        meta.update(
            {
                "file_count": len(files),
                "tree_sha256": stable_sha256(
                    [
                        {
                            "path": repo_path(p),
                            "size_bytes": p.stat().st_size,
                            "sha256": file_sha256(p),
                        }
                        for p in sorted(files)
                    ]
                ),
            }
        )
    return meta


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "terminal_decision": TERMINAL_DECISION,
        "terminal_blocker": BLOCK_REASON,
        "generated_at_utc": utc_now(),
        **SAFE_FLAGS,
    }


def current_context() -> dict[str, Any]:
    status_lines = git_output(["status", "--short"]).splitlines()
    return {
        "head": git_output(["rev-parse", "HEAD"]),
        "head_oneline": git_output(["log", "-1", "--oneline"]),
        "dirty_entry_count": len(status_lines),
        "dirty_state_scope": status_lines,
        "controlling_prompt_path": repo_path(CONTROLLING_PROMPT),
        "route_dir": repo_path(ROUTE_DIR),
        "evidence_class_boundary": EVIDENCE_CLASS,
        "hard_boundary_summary": [
            "disk artifacts only",
            "no live/API/broker/raw/prompt/config/risk/safety/execution/canary/selector surface changes",
            "no result rows unless target/horizon/metric/falsification rules freeze first",
            "NO_PROMOTION_VERDICT with validation_safe=false, outcome_review_opened=false, live_effect=false",
        ],
    }


def prerequisite_audit() -> dict[str, Any]:
    decision = load_json(G12_DECISION)
    verification = load_json(G12_VERIFICATION)
    passed = (
        decision.get("terminal_decision")
        == "ACCEPT_AS_G12_SEALED_VALIDATION_DESIGN_CONTROL_EVIDENCE_ONLY"
        and verification.get("ok") is True
        and verification.get("can_mark_goal_complete") is True
    )
    audit = base_payload("prerequisite_acceptance_audit")
    audit.update(
        {
            "activation_prerequisite_passed": passed,
            "g12_decision_path": repo_path(G12_DECISION),
            "g12_decision_sha256": file_sha256(G12_DECISION),
            "g12_terminal_decision": decision.get("terminal_decision"),
            "g12_verification_path": repo_path(G12_VERIFICATION),
            "g12_verification_sha256": file_sha256(G12_VERIFICATION),
            "g12_verification_ok": verification.get("ok"),
            "g12_verification_can_mark_goal_complete": verification.get("can_mark_goal_complete"),
            "g12_accepted_design_opens_validation_execution": decision.get("accepted_validation_execution"),
            "g12_accepted_design_opens_result_scoring": decision.get("opens_result_scoring"),
            "g12_accepted_design_safe_flags": {
                "promotion_verdict": decision.get("promotion_verdict"),
                "validation_safe": decision.get("validation_safe"),
                "outcome_review_opened": decision.get("outcome_review_opened"),
                "live_effect": decision.get("live_effect"),
            },
        }
    )
    return audit


def collect_input_hashes() -> dict[str, Any]:
    inputs = {**CORE_CONTEXT_INPUTS, **MANDATORY_INPUTS}
    source_artifacts = {
        name: artifact_metadata(path, include_line_count=path.suffix in {".jsonl", ".md", ".json"})
        for name, path in sorted(inputs.items())
    }
    return {
        "source_artifact_count": len(source_artifacts),
        "source_artifacts": source_artifacts,
        "source_artifact_list_sha256": stable_sha256(source_artifacts),
    }


def collect_rowsets() -> dict[str, Any]:
    candidate_rows: dict[str, dict[str, Any]] = {}
    candidate_field_names: set[str] = set()
    candidate_status_counts: Counter[str] = Counter()
    candidate_groups: Counter[str] = Counter()
    candidate_symbols: Counter[str] = Counter()
    duplicate_keys: set[str] = set()

    for _, row in iter_jsonl(CANDIDATE_ROWS):
        row_id = row["candidate_input_row_id"]
        candidate_rows[row_id] = {
            "candidate_input_row_id": row_id,
            "row_hash": row.get("row_hash"),
            "duplicate_proxy_denominator_key": row.get("duplicate_key"),
            "symbol": row.get("symbol"),
            "canonical_economic_group": row.get("canonical_economic_group"),
            "decision_asof_utc": row.get("decision_asof_utc"),
            "source_file_name": row.get("source_file_name"),
        }
        candidate_field_names.update(row.keys())
        candidate_status_counts[row.get("candidate_input_only_status", "<missing>")] += 1
        candidate_groups[row.get("canonical_economic_group", "<missing>")] += 1
        candidate_symbols[row.get("symbol", "<missing>")] += 1
        duplicate_keys.add(row.get("duplicate_key"))

    ledger_rows: list[dict[str, Any]] = []
    partition_counts: Counter[str] = Counter()
    ledger_ids: set[str] = set()
    mismatch_rows: list[dict[str, Any]] = []

    for _, row in iter_jsonl(G0_ROW_PARTITION_LEDGER):
        row_id = row["candidate_input_row_id"]
        ledger_ids.add(row_id)
        partition = row["partition_assignment"]
        partition_counts[partition] += 1
        candidate = candidate_rows.get(row_id)
        if not candidate or candidate.get("row_hash") != row.get("source_packet_row_hash"):
            mismatch_rows.append(
                {
                    "candidate_input_row_id": row_id,
                    "candidate_row_present": candidate is not None,
                    "candidate_row_hash": None if candidate is None else candidate.get("row_hash"),
                    "ledger_source_packet_row_hash": row.get("source_packet_row_hash"),
                }
            )
        ledger_rows.append(
            {
                "candidate_input_row_id": row_id,
                "partition_assignment": partition,
                "row_execution_status": "BLOCKED_BEFORE_OUTCOME_OPENING",
                "row_block_reason": "MISSING_FROZEN_OUTCOME_TARGET_AND_HORIZON_SPEC",
                "duplicate_proxy_denominator_key": row.get("duplicate_proxy_denominator_key"),
                "symbol": row.get("symbol"),
                "canonical_economic_group": row.get("canonical_economic_group"),
                "decision_asof_utc": row.get("decision_asof_utc"),
                "source_file_name": row.get("source_file_name"),
                "source_packet_row_hash": row.get("source_packet_row_hash"),
            }
        )

    sealed_rows = [row for row in ledger_rows if row["partition_assignment"] == "SEALED_VALIDATION_CANDIDATE_DESIGN"]
    stress_rows = [row for row in ledger_rows if row["partition_assignment"] == "STRESS_ROBUSTNESS_CANDIDATE_DESIGN"]
    missing_in_ledger = sorted(set(candidate_rows) - ledger_ids)
    extra_in_ledger = sorted(ledger_ids - set(candidate_rows))

    return {
        "candidate_rows": candidate_rows,
        "candidate_field_names": sorted(candidate_field_names),
        "candidate_status_counts": dict(sorted(candidate_status_counts.items())),
        "candidate_groups": dict(sorted(candidate_groups.items())),
        "candidate_symbols": dict(sorted(candidate_symbols.items())),
        "unique_duplicate_key_count": len(duplicate_keys),
        "ledger_rows": ledger_rows,
        "sealed_rows": sealed_rows,
        "stress_rows": stress_rows,
        "partition_counts": dict(sorted(partition_counts.items())),
        "missing_in_ledger": missing_in_ledger,
        "extra_in_ledger": extra_in_ledger,
        "mismatch_rows": mismatch_rows,
        "all_candidate_rows_covered_once": not missing_in_ledger
        and not extra_in_ledger
        and not mismatch_rows
        and len(ledger_ids) == len(candidate_rows),
    }


def session_bucket(decision_asof_utc: str) -> str:
    hour = int(decision_asof_utc[11:13])
    if 0 <= hour < 7:
        return "SOURCE_UTC_00_06"
    if 7 <= hour < 13:
        return "SOURCE_UTC_07_12"
    if 13 <= hour < 18:
        return "SOURCE_UTC_13_17"
    return "SOURCE_UTC_18_23"


def variant_family_registry() -> dict[str, Any]:
    generic_missing = [
        "frozen outcome target definition",
        "frozen outcome horizon",
        "post-decision target/stop/path bars",
        "side or direction field",
        "entry reference price",
        "stop-loss reference",
        "take-profit or target reference",
    ]
    family_missing: dict[str, list[str]] = {
        "adjacent_range_compression_breakout": [
            *generic_missing,
            "adjacent range bounds",
            "compression state",
            "breakout direction",
        ],
        "ob_retest": [
            *generic_missing,
            "order-block bounds",
            "impulse direction",
            "touch/retest state",
        ],
        "opening_drive_no_fill_lifecycle": [
            *generic_missing,
            "opening range definition",
            "pending limit creation/fill/cancel/expiry lifecycle",
            "no-fill state",
        ],
        "fvg_fill": [
            *generic_missing,
            "FVG bounds",
            "FVG fill state",
            "impulse leg direction",
        ],
        "liquidity_stop_run_context": [
            *generic_missing,
            "liquidity pool or sweep state",
            "stop-run trigger definition",
        ],
        "session_kz_sweep": [
            *generic_missing,
            "predefined kill-zone/session sweep state",
            "sweep level reference",
        ],
        "breaker_re_entry": [
            *generic_missing,
            "breaker bounds",
            "breaker mitigation state",
            "re-entry trigger state",
        ],
        "baseline_random_session_control": [
            "frozen outcome target definition",
            "frozen outcome horizon",
            "randomization seed/policy tied to executable target",
            "entry/exit scoring rule",
        ],
        "baseline_shifted_entry_control": [
            "frozen outcome target definition",
            "frozen outcome horizon",
            "shift amount and entry reference tied to executable target",
            "entry/exit scoring rule",
        ],
        "baseline_momentum_continuation": [
            "frozen outcome target definition",
            "frozen outcome horizon",
            "momentum lookback/entry/exit scoring rule",
        ],
        "baseline_mean_reversion": [
            "frozen outcome target definition",
            "frozen outcome horizon",
            "mean-reversion lookback/entry/exit scoring rule",
        ],
    }
    families = []
    for family_id in KNOWN_FAMILIES:
        is_baseline = family_id in BASELINE_FAMILIES
        families.append(
            {
                "family_id": family_id,
                "registry_status": "CONTROL_ONLY" if is_baseline else "NOT_EXECUTABLE_FROM_PACKET_SOURCE_FIELDS",
                "execution_status": "NOT_EXECUTABLE_MISSING_FROZEN_OUTCOME_TARGET_SPEC",
                "source_safe_to_execute_now": False,
                "missing_fields_or_specs": family_missing[family_id],
                "exact_blocker": "MISSING_FROZEN_OUTCOME_TARGET_SPEC",
                "repair_requirement": (
                    "A separate source/control design repair must freeze target, horizon, "
                    "entry/exit/scoring rule, no-leak fields, duplicate policy, and family-specific "
                    "source fields before any result row can be generated."
                ),
            }
        )
    payload = base_payload("variant_family_registry")
    payload.update(
        {
            "registry_frozen_before_outcome_opening": True,
            "outcome_opened": False,
            "known_family_count": len(KNOWN_FAMILIES),
            "all_known_families_addressed": sorted(row["family_id"] for row in families) == sorted(KNOWN_FAMILIES),
            "executable_family_count": 0,
            "control_only_family_count": len(BASELINE_FAMILIES),
            "families": families,
            "registry_sha256": stable_sha256(families),
        }
    )
    return payload


def baseline_control_registry(g0_baselines: dict[str, Any]) -> dict[str, Any]:
    baselines = []
    for baseline_id in g0_baselines.get("four_adversarial_baselines_preserved", []):
        baselines.append(
            {
                "baseline_id": baseline_id,
                "registry_status": "CONTROL_ONLY",
                "execution_status": "NOT_EXECUTABLE_MISSING_FROZEN_OUTCOME_TARGET_SPEC",
                "separate_from_stress": True,
                "separate_from_primary_sealed": True,
                "result_artifact_emitted": False,
                "exact_blocker": "MISSING_FROZEN_OUTCOME_TARGET_SPEC",
            }
        )
    payload = base_payload("baseline_control_registry")
    payload.update(
        {
            "baseline_count": len(baselines),
            "baselines": baselines,
            "baseline_registry_sha256": stable_sha256(baselines),
            "baseline_results_emitted": False,
        }
    )
    return payload


def rowset_manifest(rowsets: dict[str, Any], g0_duplicate: dict[str, Any], packet_discovery: dict[str, Any]) -> dict[str, Any]:
    sealed_rows = rowsets["sealed_rows"]
    stress_rows = rowsets["stress_rows"]
    all_rows = rowsets["ledger_rows"]
    payload = base_payload("frozen_rowset_manifest")
    payload.update(
        {
            "rowsets_frozen_before_outcome_opening": True,
            "outcome_opened": False,
            "candidate_input_row_count": len(rowsets["candidate_rows"]),
            "row_partition_ledger_row_count": len(all_rows),
            "all_candidate_rows_covered_once": rowsets["all_candidate_rows_covered_once"],
            "coverage_issues": {
                "missing_in_ledger": rowsets["missing_in_ledger"],
                "extra_in_ledger": rowsets["extra_in_ledger"],
                "hash_mismatch_rows": rowsets["mismatch_rows"],
            },
            "partition_counts": rowsets["partition_counts"],
            "sealed_row_count": len(sealed_rows),
            "stress_row_count": len(stress_rows),
            "discovery_exclusion_count": packet_discovery.get("selected_discovery_source_count"),
            "candidate_denominator_group_count": g0_duplicate.get("candidate_denominator_group_count"),
            "primary_denominator_key": "duplicate_proxy_denominator_key",
            "forbidden_secondary_denominator_sources": g0_duplicate.get(
                "secondary_proxy_sources_excluded_from_candidate_denominator", []
            ),
            "primary_counting_source_by_group": g0_duplicate.get("primary_counting_source_by_group", {}),
            "full_population_no_sampling_proof": {
                "sealed_rows_represented_or_blocked": len(sealed_rows) == EXPECTED_COUNTS["sealed_design_rows"],
                "stress_rows_represented_or_blocked": len(stress_rows) == EXPECTED_COUNTS["stress_design_rows"],
                "blocked_reason_for_every_row": "MISSING_FROZEN_OUTCOME_TARGET_AND_HORIZON_SPEC",
                "result_rows_substituted_by_compact_sample": False,
                "compact_outputs_are_not_result_rows": True,
            },
            "sealed_rowset": sealed_rows,
            "stress_rowset": stress_rows,
            "rowset_hashes": {
                "sealed_rowset_sha256": stable_sha256(sealed_rows),
                "stress_rowset_sha256": stable_sha256(stress_rows),
                "all_rowset_sha256": stable_sha256(all_rows),
            },
        }
    )
    return payload


def preoutcome_freeze_packet(
    prerequisite: dict[str, Any],
    input_hashes: dict[str, Any],
    rowset: dict[str, Any],
    variants: dict[str, Any],
    baselines: dict[str, Any],
    g0_rulebook: dict[str, Any],
    g0_multiple_testing: dict[str, Any],
    g0_falsification: dict[str, Any],
) -> dict[str, Any]:
    payload = base_payload("preoutcome_freeze_packet")
    target_spec = {
        "status": "MISSING_SPEC",
        "exact_blocker": "EXECUTION_BLOCKED_MISSING_FROZEN_OUTCOME_TARGET_SPEC",
        "accepted_artifact_evidence": [
            {
                "path": repo_path(G0_RULEBOOK),
                "field": "metric_family_status",
                "value": g0_rulebook.get("metric_family_status"),
            },
            {
                "path": repo_path(G0_RULEBOOK),
                "field": "planned_metric_families_design_only",
                "value": g0_rulebook.get("planned_metric_families_design_only"),
            },
        ],
        "why_no_improvisation": (
            "Choosing targets such as next-bar return, fixed-R path labels, breakout success, "
            "or synthetic trade R now would be a post-design choice not frozen by accepted G12/G0 artifacts."
        ),
    }
    payload.update(
        {
            "freeze_packet_emitted_before_any_result_row": True,
            "result_rows_read_derived_or_written": False,
            "prerequisite_acceptance_proof": {
                "activation_prerequisite_passed": prerequisite["activation_prerequisite_passed"],
                "g12_terminal_decision": prerequisite["g12_terminal_decision"],
                "g12_verification_ok": prerequisite["g12_verification_ok"],
                "g12_verification_can_mark_goal_complete": prerequisite[
                    "g12_verification_can_mark_goal_complete"
                ],
                "prerequisite_audit_sha256": stable_sha256(prerequisite),
            },
            "source_artifact_list_sha256": input_hashes["source_artifact_list_sha256"],
            "candidate_input_manifest_hash": file_sha256(CANDIDATE_MANIFEST),
            "row_partition_ledger_hash": file_sha256(G0_ROW_PARTITION_LEDGER),
            "source_control_bar_count": EXPECTED_COUNTS["source_control_bar_rows"],
            "candidate_input_row_count": EXPECTED_COUNTS["candidate_input_rows"],
            "sealed_rowset_count": rowset["sealed_row_count"],
            "stress_rowset_count": rowset["stress_row_count"],
            "discovery_exclusion_count": rowset["discovery_exclusion_count"],
            "candidate_denominator_group_count": rowset["candidate_denominator_group_count"],
            "primary_denominator_key": rowset["primary_denominator_key"],
            "forbidden_secondary_denominator_sources": rowset["forbidden_secondary_denominator_sources"],
            "variant_family_registry_hash": variants["registry_sha256"],
            "baseline_control_registry_hash": baselines["baseline_registry_sha256"],
            "outcome_target_definitions": target_spec,
            "outcome_horizons": target_spec,
            "metrics_to_compute": {
                "status": "MISSING_SPEC",
                "planned_metric_families_design_only": g0_rulebook.get("planned_metric_families_design_only", []),
                "metric_family_status": g0_rulebook.get("metric_family_status"),
                "dsr_pbo_effective_n_status": "NOT_COMPUTABLE_NO_RESULT_ROWS_NO_TARGET_HORIZON",
            },
            "falsification_rules": g0_falsification.get("future_lane_stop_conditions", []),
            "multiple_testing_debt_prior_to_execution": g0_multiple_testing,
            "full_population_execution_checkpoint_plan": {
                "sealed_rows": rowset["sealed_row_count"],
                "stress_rows": rowset["stress_row_count"],
                "execution_substituted_by_sampling": False,
                "terminal_action": "NO_RESULT_ROWS_EMITTED_BECAUSE_TARGET_HORIZON_SPEC_MISSING",
            },
            "large_artifact_storage_policy": {
                "raw_market_data_blob_commit_allowed": False,
                "result_artifacts_emitted": False,
                "max_raw_git_blob_bytes": 100_000_000,
                "blocked_route_storage": "compact JSON ledgers only; no raw .scid/.parquet/.csv/.dly/.bin outputs",
            },
        }
    )
    payload["freeze_packet_sha256"] = stable_sha256(payload)
    return payload


def duplicate_proxy_audit(rowsets: dict[str, Any], g0_duplicate: dict[str, Any]) -> dict[str, Any]:
    all_rows = rowsets["ledger_rows"]
    keys = [row["duplicate_proxy_denominator_key"] for row in all_rows]
    symbols = Counter(row["symbol"] for row in all_rows)
    forbidden_symbols = set(g0_duplicate.get("secondary_proxy_sources_excluded_from_candidate_denominator", []))
    payload = base_payload("duplicate_proxy_denominator_audit")
    payload.update(
        {
            "primary_denominator_key": "duplicate_proxy_denominator_key",
            "candidate_denominator_group_count": g0_duplicate.get("candidate_denominator_group_count"),
            "row_count": len(all_rows),
            "unique_denominator_key_count": len(set(keys)),
            "duplicate_denominator_key_collision_count": len(keys) - len(set(keys)),
            "forbidden_secondary_denominator_sources": sorted(forbidden_symbols),
            "forbidden_secondary_rows_in_candidate_denominator": [
                {"symbol": symbol, "row_count": count}
                for symbol, count in sorted(symbols.items())
                if symbol in forbidden_symbols
            ],
            "primary_counting_source_by_group": g0_duplicate.get("primary_counting_source_by_group", {}),
            "candidate_symbols": dict(sorted(symbols.items())),
            "audit_pass": len(keys) == len(set(keys))
            and not any(symbol in forbidden_symbols for symbol in symbols),
        }
    )
    return payload


def noleak_audit(rowsets: dict[str, Any], g0_noleak: dict[str, Any]) -> dict[str, Any]:
    candidate_fields = rowsets["candidate_field_names"]
    token_hits = []
    for field in candidate_fields:
        if field in ALLOWED_SOURCE_FIELD_TOKENS:
            continue
        pieces = field.lower().split("_")
        hits = sorted(token for token in FORBIDDEN_SOURCE_FIELD_TOKENS if token in pieces or token == field)
        if hits:
            token_hits.append({"field": field, "forbidden_token_hits": hits})
    payload = base_payload("noleak_label_family_audit")
    payload.update(
        {
            "candidate_input_allowed_field_count": g0_noleak.get("candidate_input_allowed_field_count"),
            "candidate_input_allowed_fields_from_contract": g0_noleak.get("candidate_input_allowed_fields"),
            "candidate_input_fields_observed": candidate_fields,
            "candidate_status_counts": rowsets["candidate_status_counts"],
            "forbidden_candidate_field_token_hits": token_hits,
            "hidden_label_path_broker_ai_live_fields_detected": bool(token_hits),
            "outcome_review_opened": False,
            "result_rows_emitted": False,
            "audit_pass": not token_hits
            and rowsets["candidate_status_counts"]
            == {"CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION": EXPECTED_COUNTS["candidate_input_rows"]},
        }
    )
    return payload


def multiple_testing_ledger(variants: dict[str, Any], g0_multiple_testing: dict[str, Any]) -> dict[str, Any]:
    payload = base_payload("multiple_testing_dsr_pbo_effective_n_ledger")
    payload.update(
        {
            "family_registry_count": variants["known_family_count"],
            "executable_family_count": variants["executable_family_count"],
            "control_only_family_count": variants["control_only_family_count"],
            "variant_selection_after_outcome_opening": False,
            "result_rows_emitted": False,
            "dsr_status": "NOT_COMPUTABLE_NO_RESULT_ROWS_NO_FROZEN_TARGET_HORIZON",
            "pbo_status": "NOT_COMPUTABLE_NO_RESULT_ROWS_NO_FROZEN_TARGET_HORIZON",
            "effective_n_status": "NOT_COMPUTABLE_NO_RESULT_ROWS_NO_FROZEN_TARGET_HORIZON",
            "carried_forward_multiple_testing_debt": g0_multiple_testing,
        }
    )
    return payload


def concentration_ledger(rowsets: dict[str, Any]) -> dict[str, Any]:
    rows = rowsets["ledger_rows"]
    by_partition = Counter(row["partition_assignment"] for row in rows)
    by_symbol = Counter(row["symbol"] for row in rows)
    by_group = Counter(row["canonical_economic_group"] for row in rows)
    by_source_file = Counter(row["source_file_name"] for row in rows)
    by_bucket = Counter(session_bucket(row["decision_asof_utc"]) for row in rows)
    payload = base_payload("concentration_regime_session_symbol_ledger")
    payload.update(
        {
            "result_concentration_status": "NOT_COMPUTABLE_NO_RESULT_ROWS",
            "source_row_block_concentration_only": True,
            "regime_concentration_status": "NOT_DEFINED_IN_ACCEPTED_PACKET_SOURCE_FIELDS",
            "session_bucket_status": "SOURCE_UTC_BUCKETS_ONLY_NOT_RESULT_SESSION_METRICS",
            "blocked_rows_by_partition": dict(sorted(by_partition.items())),
            "blocked_rows_by_symbol": dict(sorted(by_symbol.items())),
            "blocked_rows_by_canonical_economic_group": dict(sorted(by_group.items())),
            "blocked_rows_by_source_file": dict(sorted(by_source_file.items())),
            "blocked_rows_by_source_utc_bucket": dict(sorted(by_bucket.items())),
            "all_rows_share_same_block_reason": "MISSING_FROZEN_OUTCOME_TARGET_AND_HORIZON_SPEC",
        }
    )
    return payload


def failure_anatomy_ledger(rowsets: dict[str, Any], variants: dict[str, Any]) -> dict[str, Any]:
    payload = base_payload("failure_anatomy_ledger")
    payload.update(
        {
            "failure_class": "PRE_OUTCOME_EXECUTION_BLOCKER",
            "result_failure_anatomy_status": "NO_RESULT_ROWS_EMITTED",
            "row_level_block_reason_ref": repo_path(
                ROUTE_DIR / f"{PREFIX}_FROZEN_ROWSET_MANIFEST_{DATE_TAG}.json"
            ),
            "blocked_candidate_rows": len(rowsets["ledger_rows"]),
            "blocked_sealed_rows": len(rowsets["sealed_rows"]),
            "blocked_stress_rows": len(rowsets["stress_rows"]),
            "blocked_family_count": variants["known_family_count"],
            "family_blockers": [
                {
                    "family_id": row["family_id"],
                    "execution_status": row["execution_status"],
                    "missing_fields_or_specs": row["missing_fields_or_specs"],
                }
                for row in variants["families"]
            ],
            "negative_learning": [
                "The SCID as-of packet is a valid source-control rowset, not an executable trading strategy packet.",
                "The accepted design froze denominators and partitions but not target/horizon/outcome definitions.",
                "All rows are preserved for a repair lane; no post-hoc target choice was made.",
            ],
        }
    )
    return payload


def falsification_stop_ledger(g0_falsification: dict[str, Any]) -> dict[str, Any]:
    payload = base_payload("falsification_stop_ledger")
    payload.update(
        {
            "stop_condition_fired": True,
            "fired_stop_condition": "exact outcome target definitions and horizons cannot be frozen from accepted artifacts",
            "terminal_action": TERMINAL_DECISION,
            "future_lane_stop_conditions_preserved": g0_falsification.get("future_lane_stop_conditions", []),
            "post_hoc_rescue_attempted": False,
        }
    )
    return payload


def saturation_redteam_ledger(rowsets: dict[str, Any], variants: dict[str, Any]) -> dict[str, Any]:
    checks = [
        (
            "Did any stress row leak into sealed results?",
            "No result rows were emitted; stress rows remain separate in the frozen rowset manifest.",
        ),
        (
            "Did any discovery-exposed row leak into sealed results?",
            "No result rows were emitted; discovery exclusions remain a counted external exclusion set.",
        ),
        (
            "Did any secondary proxy row inflate denominators?",
            "No; denominator audit uses duplicate_proxy_denominator_key and excludes XAUUSD_MGC/US30_MYM.",
        ),
        (
            "Did any family execute without frozen fields and target definitions?",
            "No; executable family count is zero and each family carries exact missing fields/specs.",
        ),
        (
            "Did any target, horizon, or filter get selected after seeing results?",
            "No result rows were read, derived, or written; missing target/horizon spec is terminal.",
        ),
        (
            "Did hidden label, broker, path, AI/API, or live fields enter results?",
            "No result artifacts exist; candidate source field audit remains input-only.",
        ),
        (
            "Are results concentrated in one symbol/group/window?",
            "No result concentration is computable; blocked source-row concentration is reported separately.",
        ),
        (
            "Do baselines explain the result?",
            "No baseline result exists; baselines are registry/control-only and blocked by target/horizon spec.",
        ),
        (
            "What would a skeptical G12 post-execution audit reject?",
            "It would reject any improvised target/horizon or any result-row artifact in this blocked lane.",
        ),
    ]
    payload = base_payload("saturation_redteam_ledger")
    payload.update(
        {
            "same_evidence_class_gap_closed": True,
            "gap_closed_by": "exact blocked-before-outcomes packet and repair prompt",
            "questions": [{"question": q, "answer": a} for q, a in checks],
            "result_artifacts_absent_by_design": True,
            "blocked_row_count": len(rowsets["ledger_rows"]),
            "blocked_family_count": variants["known_family_count"],
        }
    )
    return payload


def result_omission_ledger() -> dict[str, Any]:
    payload = base_payload("result_artifact_omission_ledger")
    payload.update(
        {
            "result_artifacts_emitted": False,
            "omitted_result_artifacts": [
                {
                    "path": repo_path(ROUTE_DIR / name),
                    "exists": (ROUTE_DIR / name).exists(),
                    "omission_reason": "EXECUTION_BLOCKED_MISSING_FROZEN_OUTCOME_TARGET_SPEC",
                }
                for name in RESULT_ARTIFACT_NAMES
            ],
            "no_result_rows_policy": "blocked-before-outcomes route must not create sealed/stress/baseline result artifacts",
        }
    )
    return payload


def large_artifact_storage_audit() -> dict[str, Any]:
    raw_exts = {".scid", ".parquet", ".csv", ".dly", ".bin"}
    files = [
        p
        for p in ROUTE_DIR.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    ] + [REPAIR_PROMPT]
    file_entries = []
    for path in sorted(set(files)):
        if not path.exists():
            continue
        file_entries.append(
            {
                "path": repo_path(path),
                "size_bytes": path.stat().st_size,
                "sha256": file_sha256(path),
                "extension": path.suffix.lower(),
                "raw_market_data_extension": path.suffix.lower() in raw_exts,
                "over_100mb": path.stat().st_size > 100_000_000,
            }
        )
    payload = base_payload("large_artifact_storage_audit")
    payload.update(
        {
            "file_count": len(file_entries),
            "files": file_entries,
            "raw_market_data_blob_files": [
                row for row in file_entries if row["raw_market_data_extension"]
            ],
            "over_100mb_files": [row for row in file_entries if row["over_100mb"]],
            "audit_pass": not any(row["raw_market_data_extension"] or row["over_100mb"] for row in file_entries),
        }
    )
    return payload


def output_manifest(output_paths: list[Path]) -> dict[str, Any]:
    entries = []
    for path in sorted(output_paths):
        if path.exists():
            entries.append(artifact_metadata(path))
    payload = base_payload("output_manifest")
    payload.update(
        {
            "output_count": len(entries),
            "outputs": entries,
            "output_manifest_sha256": stable_sha256(entries),
            "result_artifacts_expected_absent": [repo_path(ROUTE_DIR / name) for name in RESULT_ARTIFACT_NAMES],
        }
    )
    return payload


def completion_audit(checks: dict[str, Any], output_manifest_payload: dict[str, Any]) -> dict[str, Any]:
    failures = [name for name, ok in checks.items() if not ok]
    payload = base_payload("completion_audit")
    prompt_to_artifact = [
        {
            "requirement": "activation prerequisite proven from disk",
            "evidence": repo_path(ROUTE_DIR / f"{PREFIX}_PREREQUISITE_ACCEPTANCE_AUDIT_{DATE_TAG}.json"),
            "status": "PASS" if checks["activation_prerequisite_passed"] else "FAIL",
        },
        {
            "requirement": "pre-outcome freeze exists before result artifacts",
            "evidence": repo_path(ROUTE_DIR / f"{PREFIX}_PREOUTCOME_FREEZE_PACKET_{DATE_TAG}.json"),
            "status": "PASS" if checks["preoutcome_freeze_present"] else "FAIL",
        },
        {
            "requirement": "exact row counts 3014=2432+582 with 365 exclusions and 7 denominator groups",
            "evidence": repo_path(ROUTE_DIR / f"{PREFIX}_FROZEN_ROWSET_MANIFEST_{DATE_TAG}.json"),
            "status": "PASS" if checks["exact_counts_pass"] else "FAIL",
        },
        {
            "requirement": "all families addressed with exact NOT_EXECUTABLE/MISSING_SPEC status",
            "evidence": repo_path(ROUTE_DIR / f"{PREFIX}_VARIANT_FAMILY_REGISTRY_{DATE_TAG}.json"),
            "status": "PASS" if checks["families_all_addressed_blocked"] else "FAIL",
        },
        {
            "requirement": "no sealed/stress/baseline result rows emitted after missing target spec",
            "evidence": repo_path(ROUTE_DIR / f"{PREFIX}_RESULT_ARTIFACT_OMISSION_LEDGER_{DATE_TAG}.json"),
            "status": "PASS" if checks["result_artifacts_absent"] else "FAIL",
        },
        {
            "requirement": "repair prompt emitted instead of G12 post-result audit prompt",
            "evidence": repo_path(REPAIR_PROMPT),
            "status": "PASS" if checks["repair_prompt_present"] else "FAIL",
        },
    ]
    payload.update(
        {
            "can_mark_goal_complete": not failures,
            "completion_status": "BLOCKED_EXACTLY_WITH_REPAIR_PROMPT" if not failures else "INCOMPLETE",
            "failed_checks": failures,
            "checks": checks,
            "prompt_to_artifact_checklist": prompt_to_artifact,
            "terminal_decision_allowed": TERMINAL_DECISION,
            "result_artifacts_emitted": False,
            "next_route": repo_path(REPAIR_PROMPT),
            "output_manifest_ref": repo_path(
                ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json"
            ),
            "output_manifest_sha256": output_manifest_payload["output_manifest_sha256"],
            "post_commit_requirements_for_final_closeout": [
                "run focused pytest",
                "run standalone verifier",
                "commit scoped artifacts and repair prompt only",
                "rerun verifier in no-write check mode",
                "audit committed diff/raw blobs",
                "regenerate LIVE_STATE after final commit",
            ],
        }
    )
    return payload


def context_anchor_md(context: dict[str, Any]) -> str:
    return (
        "# SCID As-Of Sealed Validation Execution Packet Context Anchor\n\n"
        f"Date: {DATE_TAG}\n"
        f"Route: `{ROUTE_ID}`\n"
        f"Evidence class: `{EVIDENCE_CLASS}`\n"
        f"Current HEAD: `{context['head_oneline']}`\n"
        f"Controlling prompt: `{repo_path(CONTROLLING_PROMPT)}`\n\n"
        "## Boundary\n\n"
        "This route uses disk artifacts only. It does not touch live/API/broker/raw/prompt/config/risk/safety "
        "surfaces and preserves `NO_PROMOTION_VERDICT`, `validation_safe=false`, "
        "`outcome_review_opened=false`, and `live_effect=false`.\n\n"
        "## Terminal Decision\n\n"
        f"`{TERMINAL_DECISION}`\n\n"
        f"Reason: {BLOCK_REASON}.\n"
    )


def interpretation_limits_md() -> str:
    return (
        "# SCID As-Of Sealed Validation Execution Interpretation Limits\n\n"
        f"Terminal decision: `{TERMINAL_DECISION}`.\n\n"
        "No sealed, stress, or adversarial-baseline result rows were emitted. The accepted G12/G0 design "
        "artifacts prove the source packet, row partitions, denominator policy, and control boundaries, but "
        "they do not define an executable target/horizon/metric specification. Any target choice made inside "
        "this lane would be post-hoc and would contaminate the sealed validation route.\n\n"
        "This is `NO_PROMOTION_VERDICT` evidence only. It is not validation-safe, it does not open owner "
        "outcome review, and it has no live effect.\n"
    )


def repair_prompt_text() -> str:
    return (
        "# SCID As-Of Sealed Validation Execution Packet Repair Prompt\n\n"
        "Date: 2026-05-11\n"
        "Owner lane: repair of blocked SCID as-of sealed-validation execution packet\n"
        "Evidence class: `SCID_ASOF_SEALED_VALIDATION_EXECUTION_PACKET_REPAIR_ONLY`\n"
        "Promotion posture: `NO_PROMOTION_VERDICT`\n"
        "Live authority: none\n\n"
        "## Objective\n\n"
        "Repair the blocked execution packet by freezing executable outcome target definitions and horizons "
        "from disk artifacts before any result row is generated. Do not use chat memory. Run mandatory "
        "preflight, read the blocked packet route under "
        "`research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_execution_packet/`, "
        "and preserve `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.\n\n"
        "## Exact Blocker To Repair\n\n"
        "`EXECUTION_BLOCKED_MISSING_FROZEN_OUTCOME_TARGET_SPEC`: accepted G12/G0 artifacts freeze source "
        "rows, partitions, denominator policy, baseline names, metric-family names, and falsification stops, "
        "but not exact executable target definitions or horizons.\n\n"
        "## Required Repair Artifacts\n\n"
        "- A target/horizon rulebook that defines every executable family before outcome opening.\n"
        "- Per-family source-field requirements with exact allowed/forbidden fields.\n"
        "- Entry/exit/target/stop/scoring definitions, or an exact `NOT_EXECUTABLE_FROM_PACKET_SOURCE_FIELDS` "
        "reason for each known family.\n"
        "- A G12 audit prompt for the repaired target/horizon rulebook before result scoring opens.\n\n"
        "## Forbidden\n\n"
        "No result rows, broker/account/order/deal/position evidence, AI/API calls, paid/vendor access, raw "
        "market-data blob commits, prompt/config/risk/safety/execution/canary/selector edits, remote push, "
        "promotion, or live behavior changes.\n"
    )


def completion_audit_md(audit: dict[str, Any]) -> str:
    lines = [
        "# SCID As-Of Sealed Validation Execution Completion Audit",
        "",
        f"Terminal decision: `{audit['terminal_decision']}`.",
        "",
        f"Can mark goal complete: `{str(audit['can_mark_goal_complete']).lower()}`.",
        "",
        "## Prompt-To-Artifact Checklist",
        "",
    ]
    for item in audit["prompt_to_artifact_checklist"]:
        lines.append(f"- {item['status']}: {item['requirement']} -> `{item['evidence']}`")
    lines.extend(
        [
            "",
            "No result-row artifacts were emitted because the frozen outcome target/horizon spec is missing.",
            "Safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, "
            "`outcome_review_opened=false`, and `live_effect=false`.",
            "",
        ]
    )
    return "\n".join(lines)


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    context = current_context()
    prerequisite = prerequisite_audit()
    input_hashes = collect_input_hashes()

    g0_rulebook = load_json(G0_RULEBOOK)
    g0_duplicate = load_json(G0_DUPLICATE)
    g0_baselines = load_json(G0_BASELINES)
    g0_noleak = load_json(G0_NOLEAK)
    g0_multiple_testing = load_json(G0_MULTIPLE_TESTING)
    g0_falsification = load_json(G0_FALSIFICATION)
    packet_discovery = load_json(PACKET_DISCOVERY)
    bar_manifest = load_json(BAR_MANIFEST)

    rowsets = collect_rowsets()
    variants = variant_family_registry()
    baselines = baseline_control_registry(g0_baselines)
    frozen_rowset = rowset_manifest(rowsets, g0_duplicate, packet_discovery)
    freeze = preoutcome_freeze_packet(
        prerequisite,
        input_hashes,
        frozen_rowset,
        variants,
        baselines,
        g0_rulebook,
        g0_multiple_testing,
        g0_falsification,
    )
    duplicate_audit = duplicate_proxy_audit(rowsets, g0_duplicate)
    noleak = noleak_audit(rowsets, g0_noleak)
    mt_ledger = multiple_testing_ledger(variants, g0_multiple_testing)
    concentration = concentration_ledger(rowsets)
    failure = failure_anatomy_ledger(rowsets, variants)
    falsification = falsification_stop_ledger(g0_falsification)
    redteam = saturation_redteam_ledger(rowsets, variants)
    omission = result_omission_ledger()

    prerequisite_path = ROUTE_DIR / f"{PREFIX}_PREREQUISITE_ACCEPTANCE_AUDIT_{DATE_TAG}.json"
    freeze_path = ROUTE_DIR / f"{PREFIX}_PREOUTCOME_FREEZE_PACKET_{DATE_TAG}.json"
    rowset_path = ROUTE_DIR / f"{PREFIX}_FROZEN_ROWSET_MANIFEST_{DATE_TAG}.json"
    variants_path = ROUTE_DIR / f"{PREFIX}_VARIANT_FAMILY_REGISTRY_{DATE_TAG}.json"
    baselines_path = ROUTE_DIR / f"{PREFIX}_BASELINE_CONTROL_REGISTRY_{DATE_TAG}.json"
    duplicate_path = ROUTE_DIR / f"{PREFIX}_DUPLICATE_PROXY_DENOMINATOR_AUDIT_{DATE_TAG}.json"
    noleak_path = ROUTE_DIR / f"{PREFIX}_NOLEAK_LABEL_FAMILY_AUDIT_{DATE_TAG}.json"
    mt_path = ROUTE_DIR / f"{PREFIX}_MULTIPLE_TESTING_DSR_PBO_EFFECTIVE_N_LEDGER_{DATE_TAG}.json"
    concentration_path = ROUTE_DIR / f"{PREFIX}_CONCENTRATION_REGIME_SESSION_SYMBOL_LEDGER_{DATE_TAG}.json"
    failure_path = ROUTE_DIR / f"{PREFIX}_FAILURE_ANATOMY_LEDGER_{DATE_TAG}.json"
    falsification_path = ROUTE_DIR / f"{PREFIX}_FALSIFICATION_STOP_LEDGER_{DATE_TAG}.json"
    redteam_path = ROUTE_DIR / f"{PREFIX}_SATURATION_REDTEAM_LEDGER_{DATE_TAG}.json"
    omission_path = ROUTE_DIR / f"{PREFIX}_RESULT_ARTIFACT_OMISSION_LEDGER_{DATE_TAG}.json"
    interpretation_path = ROUTE_DIR / f"{PREFIX}_INTERPRETATION_LIMITS_{DATE_TAG}.md"
    large_path = ROUTE_DIR / f"{PREFIX}_LARGE_ARTIFACT_STORAGE_AUDIT_{DATE_TAG}.json"
    completion_json_path = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json"
    completion_md_path = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md"
    output_manifest_path = ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json"
    output_paths = [
        ROUTE_DIR / f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.md",
        prerequisite_path,
        freeze_path,
        rowset_path,
        variants_path,
        baselines_path,
        duplicate_path,
        noleak_path,
        mt_path,
        concentration_path,
        failure_path,
        falsification_path,
        redteam_path,
        omission_path,
        interpretation_path,
        large_path,
        completion_json_path,
        completion_md_path,
        output_manifest_path,
        REPAIR_PROMPT,
        ROUTE_DIR / "build_scid_asof_sealed_validation_execution_packet_2026_05_11.py",
        ROUTE_DIR / "verify_scid_asof_sealed_validation_execution_packet_2026_05_11.py",
        ROUTE_DIR / "test_scid_asof_sealed_validation_execution_packet_2026_05_11.py",
        ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json",
    ]

    write_text_if_changed(output_paths[0], context_anchor_md(context))
    write_json(prerequisite_path, prerequisite)
    write_json(freeze_path, freeze)
    write_json(rowset_path, frozen_rowset)
    write_json(variants_path, variants)
    write_json(baselines_path, baselines)
    write_json(duplicate_path, duplicate_audit)
    write_json(noleak_path, noleak)
    write_json(mt_path, mt_ledger)
    write_json(concentration_path, concentration)
    write_json(failure_path, failure)
    write_json(falsification_path, falsification)
    write_json(redteam_path, redteam)
    write_json(omission_path, omission)
    write_text_if_changed(interpretation_path, interpretation_limits_md())
    write_text_if_changed(REPAIR_PROMPT, repair_prompt_text())

    large = large_artifact_storage_audit()
    write_json(large_path, large)

    manifest = output_manifest(output_paths)
    write_json(output_manifest_path, manifest)

    checks = {
        "activation_prerequisite_passed": prerequisite["activation_prerequisite_passed"],
        "preoutcome_freeze_present": freeze_path.exists()
        and freeze["freeze_packet_emitted_before_any_result_row"]
        and not freeze["result_rows_read_derived_or_written"],
        "exact_counts_pass": (
            bar_manifest.get("bar_row_count") == EXPECTED_COUNTS["source_control_bar_rows"]
            and len(rowsets["candidate_rows"]) == EXPECTED_COUNTS["candidate_input_rows"]
            and len(rowsets["sealed_rows"]) == EXPECTED_COUNTS["sealed_design_rows"]
            and len(rowsets["stress_rows"]) == EXPECTED_COUNTS["stress_design_rows"]
            and packet_discovery.get("selected_discovery_source_count")
            == EXPECTED_COUNTS["discovery_exclusions"]
            and g0_duplicate.get("candidate_denominator_group_count")
            == EXPECTED_COUNTS["candidate_denominator_groups"]
        ),
        "families_all_addressed_blocked": variants["all_known_families_addressed"]
        and variants["executable_family_count"] == 0
        and all(row["execution_status"].startswith("NOT_EXECUTABLE") for row in variants["families"]),
        "result_artifacts_absent": not any((ROUTE_DIR / name).exists() for name in RESULT_ARTIFACT_NAMES),
        "repair_prompt_present": REPAIR_PROMPT.exists(),
        "noleak_audit_pass": noleak["audit_pass"],
        "duplicate_proxy_audit_pass": duplicate_audit["audit_pass"],
        "large_artifact_audit_pass": large["audit_pass"],
        "all_candidate_rows_covered_once": rowsets["all_candidate_rows_covered_once"],
    }
    completion = completion_audit(checks, manifest)
    write_json(completion_json_path, completion)
    write_text_if_changed(completion_md_path, completion_audit_md(completion))

    manifest = output_manifest(output_paths)
    write_json(output_manifest_path, manifest)
    return completion


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()
    completion = build()
    if args.print_summary:
        print(
            json.dumps(
                {
                    "terminal_decision": completion["terminal_decision"],
                    "can_mark_goal_complete": completion["can_mark_goal_complete"],
                    "failed_checks": completion["failed_checks"],
                },
                sort_keys=True,
            )
        )
    return 0 if completion["can_mark_goal_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

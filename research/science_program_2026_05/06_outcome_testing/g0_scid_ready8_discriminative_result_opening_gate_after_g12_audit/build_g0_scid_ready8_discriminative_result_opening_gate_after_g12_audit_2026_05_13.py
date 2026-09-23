"""Build G0 READY8 discriminative result-opening gate artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE = "2026-05-13"
PREFIX = "G0_SCID_READY8_DISCRIMINATIVE"
ROUTE_ID = "G0_SCID_READY8_DISCRIMINATIVE_RESULT_OPENING_GATE_AFTER_G12_AUDIT"
EVIDENCE_CLASS = "G0_SCID_READY8_DISCRIMINATIVE_RESULT_OPENING_GATE_AFTER_G12_AUDIT_ONLY"
SCHEMA_VERSION = "g0_scid_ready8_discriminative_result_opening_gate_v1"
TERMINAL_OPEN = "OPEN_DISCRIMINATIVE_READY8_QUARANTINED_TARGET_RESULT_PACKET_PROMPT"
TERMINAL_REPAIR = "REPAIR_BLOCKED_WITH_EXACT_G0_READY8_RESULT_OPENING_REPAIR_REQUIREMENTS"

DISCRIMINATIVE_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design"
)
G12_DISCRIMINATIVE_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_scid_ready8_discriminative_card_rowset_repair_audit"
)
OLD_TARGET_PACKET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_noapi_ready8_quarantined_target_result_packet_after_g0_gate"
)
OLD_TARGET_AUDIT_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_scid_noapi_ready8_quarantined_target_result_packet_audit"
)
OLD_TARGET_CONTRACT_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_noapi_ready8_rowset_target_horizon_result_packet_materialization"
)

ROWSET_ROWS = DISCRIMINATIVE_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl"
ROWSET_MANIFEST = DISCRIMINATIVE_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_MANIFEST_2026-05-13.json"
DENOMINATOR_LEDGER = (
    DISCRIMINATIVE_DIR / "SCID_READY8_DISCRIMINATIVE_DENOMINATOR_DUPLICATE_POLICY_LEDGER_2026-05-13.json"
)
FAIL_CLOSED_LEDGER = DISCRIMINATIVE_DIR / "SCID_READY8_DISCRIMINATIVE_FAIL_CLOSED_POLICY_LEDGER_2026-05-13.json"
SOURCE_FIELD_MAP = DISCRIMINATIVE_DIR / "SCID_READY8_DISCRIMINATIVE_SOURCE_FIELD_MAP_LEDGER_2026-05-13.json"
PREDICATE_LEDGER = (
    DISCRIMINATIVE_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_PREDICATE_DESCRIPTOR_CONTRAST_LEDGER_2026-05-13.json"
)
PARTITION_LEDGER = (
    DISCRIMINATIVE_DIR / "SCID_READY8_DISCRIMINATIVE_SEALED_STRESS_PARTITION_DESIGN_LEDGER_2026-05-13.json"
)
G12_DECISION = (
    G12_DISCRIMINATIVE_DIR / "G12_SCID_READY8_DISCRIMINATIVE_AUDIT_DECISION_LEDGER_2026-05-13.json"
)
G12_RECOMPUTATION = (
    G12_DISCRIMINATIVE_DIR / "G12_SCID_READY8_DISCRIMINATIVE_AUDIT_RECOMPUTATION_LEDGER_2026-05-13.json"
)
OLD_TARGET_CONTRACT = OLD_TARGET_CONTRACT_DIR / "SCID_NOAPI_READY8_TARGET_HORIZON_CONTRACT_2026-05-12.json"
OLD_TARGET_JOIN = OLD_TARGET_PACKET_DIR / "SCID_NOAPI_READY8_TARGET_RESULT_TARGET_SOURCE_JOIN_LEDGER_2026-05-13.json"
OLD_TARGET_AUDIT_DECISION = (
    OLD_TARGET_AUDIT_DIR / "G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT_DECISION_LEDGER_2026-05-13.json"
)

NEXT_PROMPT = (
    PROMPT_DIR / "SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_GOAL_PROMPT_2026-05-13.md"
)
NEXT_STARTER = ROUTE_DIR / "SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_STARTER_2026-05-13.txt"

READY_CARDS = ["ADV-001", "ADV-003", "BEH-001", "HAZ-001", "HAZ-005", "MAC-001", "MAC-004", "UNC-004"]
EXPECTED_SOURCE_CANDIDATES = 3014
EXPECTED_ROWSET_ROWS = 24112
EXPECTED_ROWSET_SHA256 = "fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3"
EXPECTED_STATUS_COUNTS = {
    "ELIGIBLE_CONTRAST_CONTROL": 7530,
    "FAIL_CLOSED_DESCRIPTOR_NOT_COMPUTABLE": 790,
    "FAIL_CLOSED_MISSING_PRIOR_CANDIDATE": 7,
    "NON_APPLICABLE_SOURCE_CONTEXT": 3685,
    "PASS_CARD_PREDICATE": 6072,
    "PASS_DESCRIPTOR_CONTRAST_ELIGIBLE": 6028,
}
EXPECTED_ROLE_COUNTS = {
    "per_card_contrast_row": 7530,
    "per_card_fail_closed_row": 797,
    "per_card_non_applicable_row": 3685,
    "per_card_pass_row": 12100,
}
TARGET_FAMILIES = [
    "neutral_close_to_close_return_m15_horizons_v1",
    "neutral_high_low_excursion_m15_horizons_v1",
]
TARGET_HORIZONS = [1, 4, 16, 32]

SAFE_FLAGS = {
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
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

FORBIDDEN_ROW_KEYS = {
    "target_hit",
    "stop_hit",
    "target_hit_bool",
    "stop_hit_bool",
    "outcome",
    "outcome_status",
    "outcome_label",
    "result",
    "realized_r",
    "actual_r",
    "broker_actual_r",
    "synthetic_path_r",
    "r_multiple",
    "r",
    "pnl",
    "profit",
    "loss",
    "win_rate",
    "expectancy",
    "performance",
    "performance_metric",
    "broker_account",
    "broker_order",
    "broker_history",
    "broker_deal",
    "broker_position",
    "order_ticket",
    "deal_id",
    "position_id",
    "api_response",
    "ai_decision",
}

STATUS_TO_ROLE = {
    "PASS_DESCRIPTOR_CONTRAST_ELIGIBLE": "per_card_pass_row",
    "PASS_CARD_PREDICATE": "per_card_pass_row",
    "ELIGIBLE_CONTRAST_CONTROL": "per_card_contrast_row",
    "NON_APPLICABLE_SOURCE_CONTEXT": "per_card_non_applicable_row",
    "FAIL_CLOSED_MISSING_PRIOR_CANDIDATE": "per_card_fail_closed_row",
    "FAIL_CLOSED_DESCRIPTOR_NOT_COMPUTABLE": "per_card_fail_closed_row",
}


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def out(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE}{suffix}"


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_lf(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def safe_payload(family: str, payload: dict[str, Any]) -> dict[str, Any]:
    base = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": family,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
    }
    base.update(SAFE_FLAGS)
    base.update(payload)
    return base


def git_latest_commit(path: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", rel(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    value = proc.stdout.strip()
    return value or None


def git_status_snapshot() -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    staged = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    forbidden_prefixes = ("src/", "prompts/", "config/", "shadow_logs/", "pipeline_state/", "data/ticks/")
    forbidden_staged = [path for path in staged if path.startswith(forbidden_prefixes)]
    return {
        "staged_paths": staged,
        "forbidden_staged_paths": forbidden_staged,
        "no_forbidden_staged_paths": not forbidden_staged,
    }


def recompute_rowset() -> dict[str, Any]:
    status_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    per_card_status: dict[str, Counter[str]] = defaultdict(Counter)
    per_card_role: dict[str, Counter[str]] = defaultdict(Counter)
    per_card_descriptor_keys: dict[str, set[str]] = defaultdict(set)
    candidate_ids: set[str] = set()
    duplicate_keys: set[str] = set()
    rowset_ids: set[str] = set()
    row_hashes: set[str] = set()
    symbols: Counter[str] = Counter()
    canonical_groups: Counter[str] = Counter()
    source_segments: Counter[str] = Counter()
    source_files: Counter[str] = Counter()
    session_buckets: Counter[str] = Counter()
    validation_partitions: Counter[str] = Counter()
    card_source_fields: dict[str, set[str]] = defaultdict(set)
    card_mechanisms: dict[str, set[str]] = defaultdict(set)
    fail_closed_reasons: Counter[str] = Counter()
    missing_source_requirement_classes: Counter[str] = Counter()
    invalid_json_rows: list[int] = []
    forbidden_hits: list[dict[str, Any]] = []
    asof_violations: list[str] = []
    role_status_mismatches: list[str] = []
    non_applicable_as_pass: list[str] = []
    fail_closed_as_pass: list[str] = []
    missing_fail_closed_requirement: list[str] = []
    safe_flag_violations: list[str] = []
    duplicate_rowset_ids = 0
    duplicate_row_hashes = 0

    with ROWSET_ROWS.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                invalid_json_rows.append(line_number)
                continue

            row_id = row.get("rowset_row_id")
            card_id = row.get("card_id")
            status = row.get("card_row_status")
            role = row.get("denominator_role")
            status_counts[str(status)] += 1
            role_counts[str(role)] += 1
            per_card_status[str(card_id)][str(status)] += 1
            per_card_role[str(card_id)][str(role)] += 1
            per_card_descriptor_keys[str(card_id)].add(str(row.get("descriptor_contrast_key")))
            candidate_ids.add(str(row.get("candidate_input_row_id")))
            duplicate_keys.add(str(row.get("duplicate_proxy_denominator_key")))
            if row_id in rowset_ids:
                duplicate_rowset_ids += 1
            rowset_ids.add(str(row_id))
            row_hash = str(row.get("row_hash"))
            if row_hash in row_hashes:
                duplicate_row_hashes += 1
            row_hashes.add(row_hash)
            symbols[str(row.get("symbol"))] += 1
            canonical_groups[str(row.get("canonical_economic_group"))] += 1
            source_segments[str(row.get("source_segment_sha256"))] += 1
            source_files[str(row.get("source_file_name"))] += 1
            validation_partitions[str(row.get("validation_partition_assignment"))] += 1
            for field in row.get("source_fields_consumed", []):
                card_source_fields[str(card_id)].add(str(field))
            card_mechanisms[str(card_id)].add(str(row.get("mechanism_family")))
            descriptor_values = row.get("descriptor_values", {})
            if isinstance(descriptor_values, dict) and descriptor_values.get("session_bucket") is not None:
                session_buckets[str(descriptor_values.get("session_bucket"))] += 1
            if str(status).startswith("FAIL_CLOSED"):
                for reason in row.get("fail_closed_reasons", []):
                    fail_closed_reasons[str(reason)] += 1
                requirements = row.get("missing_source_requirements", [])
                if not requirements:
                    missing_fail_closed_requirement.append(str(row_id))
                for requirement in requirements:
                    if isinstance(requirement, dict):
                        missing_source_requirement_classes[str(requirement.get("evidence_class"))] += 1
            expected_role = STATUS_TO_ROLE.get(str(status))
            if expected_role != role:
                role_status_mismatches.append(str(row_id))
            if status == "NON_APPLICABLE_SOURCE_CONTEXT" and role == "per_card_pass_row":
                non_applicable_as_pass.append(str(row_id))
            if str(status).startswith("FAIL_CLOSED") and role == "per_card_pass_row":
                fail_closed_as_pass.append(str(row_id))
            hits = sorted(set(row.keys()) & FORBIDDEN_ROW_KEYS)
            if hits:
                forbidden_hits.append({"rowset_row_id": row_id, "hits": hits})
            if str(row.get("source_observed_asof_utc")) > str(row.get("decision_asof_utc")):
                asof_violations.append(str(row_id))
            flags = row.get("safe_flags", {})
            if flags.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
                safe_flag_violations.append(str(row_id))
            if flags.get("validation_safe") is not False:
                safe_flag_violations.append(str(row_id))
            if flags.get("outcome_review_opened") is not False:
                safe_flag_violations.append(str(row_id))
            if flags.get("live_effect") is not False:
                safe_flag_violations.append(str(row_id))

    return {
        "rowset_rows_path": rel(ROWSET_ROWS),
        "rowset_sha256": sha256_file(ROWSET_ROWS),
        "rowset_lf_sha256": sha256_lf(ROWSET_ROWS),
        "valid_json_rows": sum(status_counts.values()),
        "invalid_json_rows": invalid_json_rows,
        "candidate_input_row_id_count": len(candidate_ids),
        "duplicate_proxy_denominator_key_count": len(duplicate_keys),
        "rowset_row_id_count": len(rowset_ids),
        "row_hash_count": len(row_hashes),
        "duplicate_rowset_id_count": duplicate_rowset_ids,
        "duplicate_row_hash_count": duplicate_row_hashes,
        "card_ids": sorted(per_card_status),
        "ready_card_count": len(per_card_status),
        "status_counts": dict(sorted(status_counts.items())),
        "role_counts": dict(sorted(role_counts.items())),
        "per_card": {
            card: {
                "row_count": sum(per_card_status[card].values()),
                "card_row_status_counts": dict(sorted(per_card_status[card].items())),
                "denominator_role_counts": dict(sorted(per_card_role[card].items())),
                "descriptor_contrast_key_count": len(per_card_descriptor_keys[card]),
                "source_fields_consumed": sorted(card_source_fields[card]),
                "mechanism_families": sorted(card_mechanisms[card]),
            }
            for card in sorted(per_card_status)
        },
        "symbol_counts": dict(sorted(symbols.items())),
        "canonical_economic_group_counts": dict(sorted(canonical_groups.items())),
        "source_segment_sha256_counts": dict(sorted(source_segments.items())),
        "source_file_name_counts": dict(sorted(source_files.items())),
        "descriptor_session_bucket_counts": dict(sorted(session_buckets.items())),
        "validation_partition_assignment_counts": dict(sorted(validation_partitions.items())),
        "forbidden_row_field_hit_count": len(forbidden_hits),
        "forbidden_row_field_hits_sample": forbidden_hits[:5],
        "asof_violation_count": len(asof_violations),
        "role_status_mismatch_count": len(role_status_mismatches),
        "non_applicable_as_pass_count": len(non_applicable_as_pass),
        "fail_closed_as_pass_count": len(fail_closed_as_pass),
        "missing_fail_closed_requirement_count": len(missing_fail_closed_requirement),
        "missing_fail_closed_requirement_sample": missing_fail_closed_requirement[:5],
        "fail_closed_reason_counts": dict(sorted(fail_closed_reasons.items())),
        "missing_source_requirement_evidence_class_counts": dict(sorted(missing_source_requirement_classes.items())),
        "safe_flag_violation_count": len(safe_flag_violations),
    }


def all_safe_flags_closed(payload: dict[str, Any]) -> bool:
    for key, expected in SAFE_FLAGS.items():
        if key in payload and payload.get(key) != expected:
            return False
    return True


def build_next_prompt() -> str:
    return f"""# SCID READY8 Discriminative Quarantined Target-Result Packet

Date: {DATE}

Evidence class: `SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_ONLY`

Objective: build the separate quarantined no-API target-result/materialization packet authorized by `{ROUTE_ID}`. This route may materialize neutral target-result rows, but it is not validation, not promotion, not strategy performance scoring, and not a live-trading change.

## Mandatory Preflight And Context

1. Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
2. Read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/ai_in_loop_cost_control_research_plan.md`.
3. Read the G0 gate artifacts at `research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit/`.
4. Read the accepted G12 audit route at `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_card_rowset_repair_audit/`.
5. Read the repaired discriminative rowset route at `research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/`.
6. Read the target-horizon contract at `research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_rowset_target_horizon_result_packet_materialization/SCID_NOAPI_READY8_TARGET_HORIZON_CONTRACT_2026-05-12.json` and use it only as the accepted neutral target-family/horizon contract.

Do not rely on chat memory. Recompute from disk. Do not use the old redundant ready-8 rowset rows or old target-result rows as the input rowset for this route.

## Bound Input

Use exactly:

- repaired discriminative rowset path: `research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl`
- repaired discriminative rowset SHA256: `{EXPECTED_ROWSET_SHA256}`
- source candidate universe: `3,014`
- READY8 cards: `8`
- repaired rowset rows: `24,112`
- status vocabulary: `PASS_DESCRIPTOR_CONTRAST_ELIGIBLE`, `PASS_CARD_PREDICATE`, `ELIGIBLE_CONTRAST_CONTROL`, `NON_APPLICABLE_SOURCE_CONTEXT`, `FAIL_CLOSED_MISSING_PRIOR_CANDIDATE`, `FAIL_CLOSED_DESCRIPTOR_NOT_COMPUTABLE`
- row identity fields: `candidate_input_row_id`, `card_id`, `rowset_row_id`, `duplicate_proxy_denominator_key`, `row_hash`

## Denominator Rules

- `per_card_pass_row` rows may enter the per-card pass denominator.
- `per_card_contrast_row` rows are within-card controls and must remain visible.
- `per_card_non_applicable_row` rows remain visible and cannot enter pass denominators.
- `per_card_fail_closed_row` rows remain visible with exact `fail_closed_reasons` and `missing_source_requirements`; they cannot be dropped or counted as passes.
- `ADV-001` and `ADV-003` are adversarial/placebo control cards even when their row status is `PASS_DESCRIPTOR_CONTRAST_ELIGIBLE`; they are not edge-card pass claims.
- Blocked dependencies, blocked-card rows, and expansion candidates remain sidecars outside the accepted READY8 discriminative denominator unless a separate G12/G0 route admits them.

## Allowed Target Families And Horizons

Compute only these neutral target families:

- `neutral_close_to_close_return_m15_horizons_v1`
- `neutral_high_low_excursion_m15_horizons_v1`

Compute only horizons `1`, `4`, `16`, and `32` closed M15 bars from `entry_reference_time_utc` using accepted source-control bar rows and strict source hashes. No additional target family or horizon is open in this route unless disk evidence inside the accepted G0 gate artifacts explicitly proves it source-safe and the route freezes it before computation.

## Required Work

- Materialize target-result rows for all `24,112` repaired discriminative rowset rows across both target families and all four horizons, preserving row status and denominator role.
- Emit per-card/family JSONL packets or an equivalently auditable sharded layout with exact counts and hashes.
- Build target-source join, denominator/status, duplicate/concentration, no-leak/as-of, fail-closed, blocker/repair, saturation/self-red-team, output-manifest, and completion-audit artifacts.
- Prove the next packet references the repaired discriminative rowset hash `{EXPECTED_ROWSET_SHA256}` and does not bind the old redundant rowset hash.
- Keep broad sidecar diagnostics for source quality, partition, symbol/session/source-proxy/source-segment concentration, and descriptor-control coverage, but do not convert sidecars into accepted-card denominators.
- Emit the exact next G12 audit prompt/starter for the discriminative target-result packet.
- Add standalone builder, verifier, and focused tests.

## Forbidden Surfaces

Do not compute or claim R, PnL, win rate, expectancy, Sharpe, performance, strategy edge, validation, promotion, live readiness, broker actual-R, account/order/history/deal/position labels, AI/API decisions, paid/vendor pulls, raw market blob commits, credentials, registry edits, remote pushes, live restarts, or trading prompt/config/risk/safety/execution/canary/selector behavior changes.

Neutral target movement is quarantined result materialization only. It must not be described as trading performance or a promotion signal.

## G12 Post-Result Audit Requirement

The result packet is incomplete until a separate G12 audit recomputes rowset hash, target-family/horizon counts, target-row hashes, target-source joins, fail-closed statuses, duplicate/concentration ledgers, no-leak/as-of proof, sidecar quarantine, and forbidden-surface closure. The G12 audit must reject any packet that binds the old redundant ready-8 rowset instead of the repaired discriminative rowset.

## Terminal Decisions

- `MATERIALIZED_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_G12_AUDIT_REQUIRED`
- `KEEP_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_PACKET_CLOSED_WITH_EXACT_REPAIR_OR_SOURCE_BLOCKERS`

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` in every artifact. Complete only after materialization or exact blocker proof, verifier/focused tests, updated context, and scoped commits.
"""


def build_starter() -> str:
    return (
        "/goal Follow the full controlling prompt in "
        "research/science_program_2026_05/04_goal_prompts/"
        "SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_GOAL_PROMPT_2026-05-13.md "
        "as the complete objective; run mandatory preflight/context refresh first; do not rely on chat memory; "
        "stay SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_ONLY with no validation, promotion, "
        "performance/live, AI/API, paid/vendor, broker/account/order/history/deal/position, raw blob, registry, "
        "remote, or trading-surface changes; materialize the neutral target-result packet over the accepted "
        "repaired discriminative rowset hash fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3 "
        "for 8 cards, 3014 source candidates, 24112 rowset rows, 2 target families, and horizons 1/4/16/32; "
        "do not use the old redundant ready8 rowset; preserve pass/control/non-applicable/fail-closed denominator "
        "roles and ADV-001/ADV-003 placebo-control status; pursue every same-evidence-class blocker until cleared, "
        "proven impossible, or reduced to an exact owner/access/source/capture requirement; complete only with "
        "materialized packet artifacts, next G12 audit prompt/starter, verifier/focused tests, scoped commits, "
        "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."
    )


def write_output_manifest() -> None:
    paths = [
        out("DECISION_LEDGER"),
        out("RESULT_OPENING_PREREQUISITE_FREEZE_LEDGER"),
        out("DENOMINATOR_GATE_LEDGER"),
        out("NO_LEAK_AND_FORBIDDEN_SURFACE_GATE_LEDGER"),
        out("BLOCKER_AND_REPAIR_LEDGER"),
        out("ROUTE_DECISION_SYNTHESIS", ".md"),
        out("COMPLETION_AUDIT"),
        out("VERIFICATION_RESULT"),
        out("FOCUSED_TEST_RESULT"),
        out("OUTPUT_MANIFEST"),
        ROUTE_DIR / "build_g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit_2026_05_13.py",
        ROUTE_DIR / "verify_g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit_2026_05_13.py",
        ROUTE_DIR / "test_g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit_2026_05_13.py",
        NEXT_PROMPT,
        NEXT_STARTER,
    ]
    rows = []
    for path in sorted({p for p in paths if p.exists()}, key=rel):
        rows.append({"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    write_json(
        out("OUTPUT_MANIFEST"),
        safe_payload(
            "output_manifest",
            {
                "artifact_count": len(rows),
                "artifacts": rows,
                "manifest_self_hash_policy": "Output manifest excludes itself from required hash closure.",
            },
        ),
    )


def build_artifacts(write_outputs: bool = True) -> dict[str, Any]:
    manifest = read_json(ROWSET_MANIFEST)
    denominator = read_json(DENOMINATOR_LEDGER)
    fail_closed = read_json(FAIL_CLOSED_LEDGER)
    source_field_map = read_json(SOURCE_FIELD_MAP)
    predicate = read_json(PREDICATE_LEDGER)
    partition = read_json(PARTITION_LEDGER)
    g12_decision = read_json(G12_DECISION)
    g12_recompute = read_json(G12_RECOMPUTATION)
    old_target_contract = read_json(OLD_TARGET_CONTRACT)
    old_target_join = read_json(OLD_TARGET_JOIN)
    old_target_audit_decision = read_json(OLD_TARGET_AUDIT_DECISION)
    rowset = recompute_rowset()

    issues: list[dict[str, Any]] = []

    def add_issue(issue_id: str, description: str, repairable_here: bool = False) -> None:
        issues.append({"issue_id": issue_id, "description": description, "same_g0_repairable": repairable_here})

    if g12_decision.get("terminal_decision") != "ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_CONTROL_EVIDENCE_ONLY":
        add_issue("G12_DECISION_NOT_ACCEPTED", "Accepted G12 discriminative rowset audit decision not found.")
    if manifest.get("rowset_rows_sha256") != EXPECTED_ROWSET_SHA256:
        add_issue("MANIFEST_ROWSET_HASH_STALE", "Rowset manifest hash does not match accepted hash.")
    if rowset["rowset_sha256"] != EXPECTED_ROWSET_SHA256:
        add_issue("ROWSET_HASH_STALE", "Actual repaired discriminative rowset hash does not match accepted hash.")
    if rowset["valid_json_rows"] != EXPECTED_ROWSET_ROWS:
        add_issue("ROWSET_COUNT_MISMATCH", "Repaired discriminative rowset row count is not 24,112.")
    if rowset["candidate_input_row_id_count"] != EXPECTED_SOURCE_CANDIDATES:
        add_issue("SOURCE_CANDIDATE_COUNT_MISMATCH", "Candidate source universe is not 3,014.")
    if rowset["duplicate_proxy_denominator_key_count"] != EXPECTED_SOURCE_CANDIDATES:
        add_issue("DUPLICATE_PROXY_KEY_COUNT_MISMATCH", "Duplicate proxy denominator key count is not 3,014.")
    if rowset["card_ids"] != READY_CARDS:
        add_issue("READY_CARD_SET_MISMATCH", "Ready card set changed.")
    if rowset["status_counts"] != EXPECTED_STATUS_COUNTS:
        add_issue("STATUS_COUNTS_MISMATCH", "Row status counts do not match accepted G12 counts.")
    if rowset["role_counts"] != EXPECTED_ROLE_COUNTS:
        add_issue("ROLE_COUNTS_MISMATCH", "Denominator role counts do not match accepted G12 counts.")
    for key in (
        "forbidden_row_field_hit_count",
        "asof_violation_count",
        "role_status_mismatch_count",
        "non_applicable_as_pass_count",
        "fail_closed_as_pass_count",
        "missing_fail_closed_requirement_count",
        "safe_flag_violation_count",
        "duplicate_rowset_id_count",
        "duplicate_row_hash_count",
    ):
        if rowset[key] != 0:
            add_issue(key.upper(), f"Rowset check failed: {key}={rowset[key]}.")
    if old_target_contract.get("target_families") != TARGET_FAMILIES:
        add_issue("TARGET_FAMILY_CONTRACT_MISMATCH", "Accepted target family contract does not match expected families.")
    if old_target_contract.get("allowed_horizons_m15_bars") != TARGET_HORIZONS:
        add_issue("TARGET_HORIZON_CONTRACT_MISMATCH", "Accepted target horizon contract does not match 1/4/16/32.")
    if old_target_audit_decision.get("terminal_decision") != "ACCEPT_AS_G12_SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_CONTROL_EVIDENCE_ONLY":
        add_issue("OLD_TARGET_AUDIT_NOT_ACCEPTED", "Prior target packet audit acceptance is missing for target contract reuse evidence.")
    for name, payload in {
        "manifest": manifest,
        "denominator": denominator,
        "fail_closed": fail_closed,
        "source_field_map": source_field_map,
        "predicate": predicate,
        "partition": partition,
        "g12_decision": g12_decision,
        "old_target_contract": old_target_contract,
        "old_target_join": old_target_join,
        "old_target_audit_decision": old_target_audit_decision,
    }.items():
        if not all_safe_flags_closed(payload):
            add_issue(f"SAFE_FLAGS_OPEN_{name.upper()}", f"Safe flags not closed in {name}.")

    opened = not issues
    terminal_decision = TERMINAL_OPEN if opened else TERMINAL_REPAIR

    target_route = {
        "prompt_emitted": opened,
        "prompt_path": rel(NEXT_PROMPT),
        "starter_path": rel(NEXT_STARTER),
        "route_id": "SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET",
        "evidence_class": "SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_ONLY",
        "target_rows_expected_before_target_fail_closed": EXPECTED_ROWSET_ROWS
        * len(TARGET_FAMILIES)
        * len(TARGET_HORIZONS),
        "must_bind_repaired_rowset_path": rel(ROWSET_ROWS),
        "must_bind_repaired_rowset_sha256": EXPECTED_ROWSET_SHA256,
        "must_not_bind_old_redundant_rowset_hash": old_target_join.get("input_hash_checks", {}).get(
            "rowset_rows_sha256_manifest"
        ),
        "g12_post_result_audit_required": True,
    }

    decision = safe_payload(
        "decision_ledger",
        {
            "terminal_decision": terminal_decision,
            "ready_for_next_route": opened,
            "target_route": target_route,
            "accepted_g12_evidence_binding": {
                "decision_path": rel(G12_DECISION),
                "decision_commit": git_latest_commit(G12_DECISION),
                "terminal_decision": g12_decision.get("terminal_decision"),
                "accepted_as": g12_decision.get("accepted_as"),
                "rowset_path": rel(ROWSET_ROWS),
                "rowset_sha256": rowset["rowset_sha256"],
                "manifest_rowset_sha256": manifest.get("rowset_rows_sha256"),
                "source_candidates": rowset["candidate_input_row_id_count"],
                "ready_cards": rowset["ready_card_count"],
                "rowset_rows": rowset["valid_json_rows"],
            },
            "safe_flags": {
                "promotion_verdict": "NO_PROMOTION_VERDICT",
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
            "blockers": issues,
            "result_scoring_opened_by_this_gate": False,
            "validation_or_promotion_opened": False,
        },
    )

    prerequisite = safe_payload(
        "prerequisite_freeze_ledger",
        {
            "terminal_decision": terminal_decision,
            "accepted_repaired_rowset": {
                "path": rel(ROWSET_ROWS),
                "sha256": rowset["rowset_sha256"],
                "lf_sha256": rowset["rowset_lf_sha256"],
                "manifest_path": rel(ROWSET_MANIFEST),
                "manifest_sha256": manifest.get("rowset_rows_sha256"),
                "candidate_universe_count": rowset["candidate_input_row_id_count"],
                "ready_card_count": rowset["ready_card_count"],
                "rowset_row_count": rowset["valid_json_rows"],
            },
            "row_identity_policy": [
                "candidate_input_row_id",
                "card_id",
                "rowset_row_id",
                "duplicate_proxy_denominator_key",
                "row_hash",
            ],
            "card_status_vocabulary": sorted(EXPECTED_STATUS_COUNTS),
            "denominator_role_vocabulary": sorted(EXPECTED_ROLE_COUNTS),
            "per_card": rowset["per_card"],
            "target_family_horizon_freeze": {
                "reuse_previous_neutral_target_contract": True,
                "contract_path": rel(OLD_TARGET_CONTRACT),
                "contract_audit_path": rel(OLD_TARGET_AUDIT_DECISION),
                "target_families": TARGET_FAMILIES,
                "horizons_m15_bars": TARGET_HORIZONS,
                "additional_target_families_opened": [],
                "additional_horizons_opened": [],
                "reason_no_additional_targets": "No accepted disk artifact in this G0 gate freezes another source-safe no-API target family or horizon for the repaired discriminative rowset.",
                "previous_old_result_rows_reusable": False,
                "previous_old_result_rows_reason": "The prior target rows bind the old redundant ready-8 rowset hash; the next route must rematerialize over the repaired discriminative rowset hash.",
            },
            "duplicate_and_concentration_prerequisites": {
                "candidate_input_row_id_unique_count_required": EXPECTED_SOURCE_CANDIDATES,
                "duplicate_proxy_denominator_key_unique_count_required": EXPECTED_SOURCE_CANDIDATES,
                "rowset_row_id_unique_count_required": EXPECTED_ROWSET_ROWS,
                "row_hash_unique_count_required": EXPECTED_ROWSET_ROWS,
                "canonical_economic_group_counts": rowset["canonical_economic_group_counts"],
                "symbol_counts": rowset["symbol_counts"],
                "source_segment_sha256_counts": rowset["source_segment_sha256_counts"],
                "source_file_name_counts": rowset["source_file_name_counts"],
                "descriptor_session_bucket_counts": rowset["descriptor_session_bucket_counts"],
                "next_packet_must_report_concentration_before_interpretation": True,
            },
            "no_leak_asof_prerequisites": {
                "source_observed_asof_must_be_lte_decision_asof": True,
                "current_rowset_asof_violation_count": rowset["asof_violation_count"],
                "source_hash_policy": "STRICT_SHA256_REQUIRED",
                "source_field_map_path": rel(SOURCE_FIELD_MAP),
                "forbidden_row_keys_scan_count": rowset["forbidden_row_field_hit_count"],
            },
            "blocked_expansion_sidecar_policy": {
                "blocked_dependencies_preserved_outside_ready8": 32,
                "quarantined_expansion_denominator_inclusion": False,
                "blocked_or_expansion_rows_may_enter_next_result_denominator": False,
            },
            "post_result_g12_audit_required": True,
            "forbid_next_packet_performance_validation_promotion": True,
        },
    )

    denominator_gate = safe_payload(
        "denominator_gate_ledger",
        {
            "status_counts": rowset["status_counts"],
            "role_counts": rowset["role_counts"],
            "per_card": rowset["per_card"],
            "status_to_role_policy": STATUS_TO_ROLE,
            "pass_control_non_applicable_fail_closed_treatment": {
                "PASS_DESCRIPTOR_CONTRAST_ELIGIBLE": "per-card pass row, but ADV cards remain placebo/adversarial controls",
                "PASS_CARD_PREDICATE": "per-card pass row for non-placebo card predicate",
                "ELIGIBLE_CONTRAST_CONTROL": "retained as within-card contrast control, not pass",
                "NON_APPLICABLE_SOURCE_CONTEXT": "retained visible, excluded from pass denominators",
                "FAIL_CLOSED_MISSING_PRIOR_CANDIDATE": "retained visible with source requirements, excluded from pass denominators",
                "FAIL_CLOSED_DESCRIPTOR_NOT_COMPUTABLE": "retained visible with source requirements, excluded from pass denominators",
            },
            "adversarial_control_cards": {
                "ADV-001": "session/time/symbol placebo control; not an edge-card pass claim",
                "ADV-003": "duplicate-key hash placebo control; not an edge-card pass claim",
            },
            "denominator_integrity_checks": {
                "non_applicable_as_pass_count": rowset["non_applicable_as_pass_count"],
                "fail_closed_as_pass_count": rowset["fail_closed_as_pass_count"],
                "role_status_mismatch_count": rowset["role_status_mismatch_count"],
                "missing_fail_closed_requirement_count": rowset["missing_fail_closed_requirement_count"],
            },
            "fail_closed_reason_counts": rowset["fail_closed_reason_counts"],
            "missing_source_requirement_evidence_class_counts": rowset[
                "missing_source_requirement_evidence_class_counts"
            ],
            "blocked_and_expansion_sidecars": {
                "blocked_dependencies": 32,
                "blocked_dependencies_enter_pass_denominator": False,
                "quarantined_expansion_enter_pass_denominator": False,
            },
        },
    )

    no_leak = safe_payload(
        "no_leak_and_forbidden_surface_gate_ledger",
        {
            "allowed_source_fields_by_card": {
                card["card_id"]: {
                    "accepted_source_fields_required": card.get("accepted_source_fields_required", []),
                    "derived_source_control_fields": card.get("derived_source_control_fields", []),
                    "source_artifacts": card.get("source_artifacts", []),
                    "mechanism_family": card.get("mechanism_family"),
                    "science_domain": card.get("science_domain"),
                }
                for card in source_field_map.get("cards", [])
            },
            "predicate_source_fields_by_card": {
                card["card_id"]: card.get("source_fields_consumed", []) for card in predicate.get("cards", [])
            },
            "forbidden_field_scan_plan": {
                "forbidden_exact_row_keys": sorted(FORBIDDEN_ROW_KEYS),
                "current_forbidden_row_field_hit_count": rowset["forbidden_row_field_hit_count"],
                "current_forbidden_row_field_hits_sample": rowset["forbidden_row_field_hits_sample"],
                "next_route_must_scan_rowset_and_target_rows": True,
            },
            "asof_scan": {
                "current_asof_violation_count": rowset["asof_violation_count"],
                "rule": "source_observed_asof_utc must be <= decision_asof_utc before target opening; target bars may be future only inside the separate quarantined target-result evidence class.",
            },
            "allowed_target_source_artifacts": [
                rel(OLD_TARGET_CONTRACT),
                "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_BAR_ROWS_2026-05-11.jsonl",
                "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_BAR_MANIFEST_2026-05-11.json",
            ],
            "prohibited_surfaces": [
                "validation",
                "promotion",
                "R/PnL/win-rate/expectancy/performance/live-readiness claims",
                "AI/API calls",
                "paid/vendor access",
                "broker account/order/history/deal/position evidence",
                "raw market blob commits",
                "registry edits",
                "remote pushes",
                "trading prompt/config/risk/safety/execution/canary/selector changes",
            ],
            "next_route_boundary": "The next prompt may materialize neutral target movement over the repaired rowset only; interpretation remains quarantined until a separate G12 audit and later G0 synthesis.",
            "safe_flags_preserved": True,
        },
    )

    blocker = safe_payload(
        "blocker_and_repair_ledger",
        {
            "issues_found_count": len(issues),
            "issues": issues,
            "same_g0_repairs_or_classifications": [
                {
                    "issue": "Prior target-result packet binds the old redundant ready-8 rowset.",
                    "classification": "same_g0_prompt_rebinding_required",
                    "repair": "Next prompt explicitly binds the repaired discriminative rowset path/hash and forbids using the old redundant rowset/result rows as input.",
                    "blocking_after_repair": False,
                },
                {
                    "issue": "Target families/horizons could drift from the prior accepted neutral target contract.",
                    "classification": "same_g0_freeze_from_disk",
                    "repair": "Freeze only close-to-close and high-low excursion target families with horizons 1/4/16/32 from the accepted disk contract.",
                    "blocking_after_repair": False,
                },
                {
                    "issue": "Fail-closed and non-applicable rows could leak into pass denominators.",
                    "classification": "same_g0_denominator_policy_freeze",
                    "repair": "Denominator gate ledger freezes pass/control/non-applicable/fail-closed role treatment before target materialization.",
                    "blocking_after_repair": False,
                },
                {
                    "issue": "ADV-001 and ADV-003 can be misread as edge cards.",
                    "classification": "same_g0_adversarial_control_policy_freeze",
                    "repair": "Denominator gate ledger and next prompt mark both as placebo/adversarial controls, not edge-card claims.",
                    "blocking_after_repair": False,
                },
            ],
            "unrepaired_blockers": issues,
            "no_same_g0_gate_intelligence_remaining": opened,
            "external_or_forbidden_boundary_blockers": [],
        },
    )

    synthesis = f"""# G0 SCID READY8 Discriminative Result-Opening Gate

Terminal decision: `{terminal_decision}`

The accepted G12 audit is bound from `{rel(G12_DECISION)}`. The repaired discriminative rowset is bound from `{rel(ROWSET_ROWS)}` with SHA256 `{rowset["rowset_sha256"]}`.

This G0 gate does not score targets. It freezes the prerequisites for a separate quarantined target-result/materialization route and emits the exact next prompt only if the disk evidence is clean.

## Frozen Scope

- Source candidates: `{rowset["candidate_input_row_id_count"]}`
- READY8 cards: `{rowset["ready_card_count"]}`
- Rowset rows: `{rowset["valid_json_rows"]}`
- Target families for the next route: `{", ".join(TARGET_FAMILIES)}`
- Horizons: `1/4/16/32` closed M15 bars
- Expected next-route row combinations before target-source fail-closed handling: `{target_route["target_rows_expected_before_target_fail_closed"]}`

## Route Decision

The next route is `SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_ONLY`. It must rematerialize target rows over the repaired discriminative rowset and must not reuse the old redundant rowset/result rows.

Safe posture remains `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""

    checklist = [
        {
            "requirement": "mandatory preflight and context refresh",
            "evidence": ".context/LIVE_STATE.md regenerated and core context files read before build.",
            "satisfied": True,
        },
        {
            "requirement": "accepted G12 audit and repaired rowset bound from disk",
            "evidence": rel(G12_DECISION) + " and " + rel(ROWSET_ROWS),
            "satisfied": not any(i["issue_id"].startswith("G12") or i["issue_id"].startswith("ROWSET") for i in issues),
        },
        {
            "requirement": "rowset/hash/card/status/role/denominator/fail-closed/non-applicable prerequisites frozen",
            "evidence": rel(out("RESULT_OPENING_PREREQUISITE_FREEZE_LEDGER")) + " and " + rel(out("DENOMINATOR_GATE_LEDGER")),
            "satisfied": not issues,
        },
        {
            "requirement": "duplicate/concentration/no-leak/as-of/target-family/horizon prerequisites frozen",
            "evidence": rel(out("RESULT_OPENING_PREREQUISITE_FREEZE_LEDGER")) + " and " + rel(out("NO_LEAK_AND_FORBIDDEN_SURFACE_GATE_LEDGER")),
            "satisfied": not issues,
        },
        {
            "requirement": "next prompt references repaired rowset rather than old redundant rowset",
            "evidence": rel(NEXT_PROMPT),
            "satisfied": opened,
        },
        {
            "requirement": "no target scoring inside this G0 gate",
            "evidence": "safe flags and verifier checks",
            "satisfied": True,
        },
        {
            "requirement": "accepted G12 audit verifier rerun from disk",
            "evidence": rel(out("VERIFICATION_RESULT")),
            "satisfied": False,
        },
        {
            "requirement": "new G0 verifier and focused tests pass",
            "evidence": rel(out("VERIFICATION_RESULT")),
            "satisfied": False,
        },
        {
            "requirement": "context refreshed and scoped commits made",
            "evidence": ".context/00_core/research_current_state.md and git log",
            "satisfied": False,
        },
    ]

    completion = safe_payload(
        "completion_audit",
        {
            "terminal_decision": terminal_decision,
            "can_mark_goal_complete": False,
            "completion_standard_satisfied_before_commit": False,
            "completion_standard_satisfied": False,
            "standalone_verifier_ok": False,
            "focused_tests_ok": False,
            "objective_as_concrete_deliverables": [
                "Freeze accepted G12 discriminative rowset evidence from disk.",
                "Freeze row identity, status, role, denominator, fail-closed, duplicate/concentration, no-leak/as-of, target-family, and horizon prerequisites.",
                "Emit exact next quarantined discriminative target-result prompt/starter if ready.",
                "Preserve safe flags and avoid target scoring inside this G0 gate.",
                "Run verifier/focused tests, refresh context, and commit scoped artifacts.",
            ],
            "prompt_to_artifact_checklist": checklist,
            "instruction_coverage": {
                "goal_session_research_discipline_read_after_preflight": True,
                "research_operating_doctrine_read_after_preflight": True,
                "research_current_state_read_after_preflight": True,
                "latest_handoff_read_after_preflight": True,
                "lane_type": "G0 audit/opening gate",
                "posture_applied": "adversarial prerequisite freeze with active same-evidence-class repair; no target scoring in this gate",
                "same_evidence_class_pursuit": blocker["same_g0_repairs_or_classifications"],
                "anti_boxing_applied": [
                    "all 8 READY8 cards retained",
                    "all 3,014 source candidates retained",
                    "all 24,112 rowset rows retained",
                    "all statuses and roles retained",
                    "old target families/horizons reused only when supported by disk contract",
                    "no OB-only or top-N cap introduced",
                ],
                "doctrine_requirements_deferred_because_evidence_class_gate": [
                    "target-result materialization",
                    "post-result G12 audit",
                    "validation",
                    "promotion",
                    "live trading behavior",
                ],
            },
            "terminal_blockers": issues,
        },
    )

    if write_outputs:
        write_json(out("DECISION_LEDGER"), decision)
        write_json(out("RESULT_OPENING_PREREQUISITE_FREEZE_LEDGER"), prerequisite)
        write_json(out("DENOMINATOR_GATE_LEDGER"), denominator_gate)
        write_json(out("NO_LEAK_AND_FORBIDDEN_SURFACE_GATE_LEDGER"), no_leak)
        write_json(out("BLOCKER_AND_REPAIR_LEDGER"), blocker)
        write_text(out("ROUTE_DECISION_SYNTHESIS", ".md"), synthesis)
        write_json(out("COMPLETION_AUDIT"), completion)
        if opened:
            write_text(NEXT_PROMPT, build_next_prompt())
            write_text(NEXT_STARTER, build_starter())
        write_output_manifest()

    return {
        "opened": opened,
        "terminal_decision": terminal_decision,
        "issues": issues,
        "rowset": rowset,
        "decision": decision,
        "prerequisite": prerequisite,
        "denominator_gate": denominator_gate,
        "no_leak": no_leak,
        "blocker": blocker,
        "completion": completion,
        "target_route": target_route,
    }


def main() -> int:
    result = build_artifacts(write_outputs=True)
    print(json.dumps({"terminal_decision": result["terminal_decision"], "opened": result["opened"]}, indent=2))
    return 0 if result["opened"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

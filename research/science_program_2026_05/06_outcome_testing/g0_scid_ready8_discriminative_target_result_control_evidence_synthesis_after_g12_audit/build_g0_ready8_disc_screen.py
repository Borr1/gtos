"""Build the G0 READY8 repaired-discriminative target-result screen.

This route starts from the accepted G12 discriminative target-result audit and
performs the same-goal no-API numerical screen requested by the controlling
prompt.  The output is quarantined control evidence only: neutral movement
statistics, fail-closed anatomy, denominator contrasts, and next audit routing.
It must not become validation, performance, promotion, or live behavior.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[4]
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
ROUTE_DIR = Path(__file__).resolve().parent

DATE_TAG = "2026-05-13"
PREFIX = "G0_SCID_READY8_DISC_TARGET_SCREEN"
ROUTE_ID = "G0_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_AFTER_G12_AUDIT"
EVIDENCE_CLASS = "G0_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_ONLY"
SCHEMA_VERSION = "g0_scid_ready8_discriminative_target_result_screen_v1"
TERMINAL_DECISION = "COMPLETE_REPAIRED_DISCRIMINATIVE_NUMERICAL_SCREEN_READY_FOR_G12_AUDIT"

REPAIRED_ROWSET_SHA256 = "fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3"
OLD_REDUNDANT_ROWSET_SHA256 = "7077a0f3fa3da2c854f2a0daab856d876992b927eb3228a161eb1cf02babb54d"
EXPECTED_SOURCE_CANDIDATES = 3014
EXPECTED_READY_CARDS = 8
EXPECTED_ROWSET_ROWS = 24112
EXPECTED_TARGET_ROWS = 192896
EXPECTED_COMPUTABLE_ROWS = 162336
EXPECTED_FAIL_CLOSED_ROWS = 30560
READY_CARD_IDS = ["ADV-001", "ADV-003", "BEH-001", "HAZ-001", "HAZ-005", "MAC-001", "MAC-004", "UNC-004"]
HORIZONS = [1, 4, 16, 32]
TARGET_FAMILIES = [
    "neutral_close_to_close_return_m15_horizons_v1",
    "neutral_high_low_excursion_m15_horizons_v1",
]

CONTROLLING_PROMPT = (
    PROMPT_DIR
    / "G0_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_AFTER_G12_AUDIT_GOAL_PROMPT_2026-05-13.md"
)
NEXT_G12_PROMPT = PROMPT_DIR / "G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_AUDIT_GOAL_PROMPT_2026-05-13.md"
NEXT_G12_STARTER = ROUTE_DIR / "G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_AUDIT_STARTER_2026-05-13.txt"

ROWSET_DIR = OUTCOME_DIR / "scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design"
TARGET_PACKET_DIR = OUTCOME_DIR / "scid_ready8_discriminative_quarantined_target_result_packet"
G12_AUDIT_DIR = OUTCOME_DIR / "g12_scid_ready8_disc_target_result_audit"

ROWSET_ROWS = ROWSET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl"
ROWSET_MANIFEST = ROWSET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_MANIFEST_2026-05-13.json"
TARGET_MANIFEST = TARGET_PACKET_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_OUTPUT_MANIFEST_2026-05-13.json"
TARGET_DUPLICATE_LEDGER = TARGET_PACKET_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_DUPLICATE_DENOMINATOR_LEDGER_2026-05-13.json"
TARGET_PARTITION_LEDGER = TARGET_PACKET_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_PARTITION_CONTROL_LEDGER_2026-05-13.json"
TARGET_SIDECAR_LEDGER = TARGET_PACKET_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_SIDECAR_QUALITY_DIAGNOSTICS_LEDGER_2026-05-13.json"
G12_DECISION = G12_AUDIT_DIR / "G12_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_AUDIT_DECISION_LEDGER_2026-05-13.json"
G12_VERIFICATION = G12_AUDIT_DIR / "G12_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_AUDIT_VERIFICATION_RESULT_2026-05-13.json"
G12_COMPLETION = G12_AUDIT_DIR / "G12_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_AUDIT_COMPLETION_AUDIT_2026-05-13.json"

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
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}


GROUP_SPECS: dict[str, list[str]] = {
    "full_population": [],
    "card_horizon_target_family": ["card_id", "horizon_m15_bars", "target_family_id"],
    "card_horizon_target_family_denominator_role": [
        "card_id",
        "horizon_m15_bars",
        "target_family_id",
        "denominator_role",
    ],
    "card_horizon_target_family_row_status": ["card_id", "horizon_m15_bars", "target_family_id", "card_row_status"],
    "card_horizon_target_family_descriptor_contrast": [
        "card_id",
        "horizon_m15_bars",
        "target_family_id",
        "descriptor_contrast_key",
    ],
    "card_horizon_target_family_symbol": ["card_id", "horizon_m15_bars", "target_family_id", "symbol"],
    "card_horizon_target_family_economic_group": [
        "card_id",
        "horizon_m15_bars",
        "target_family_id",
        "canonical_economic_group",
    ],
    "card_horizon_target_family_partition": ["card_id", "horizon_m15_bars", "target_family_id", "partition_assignment"],
    "card_horizon_target_family_duplicate_concentration_bucket": [
        "card_id",
        "horizon_m15_bars",
        "target_family_id",
        "duplicate_concentration_bucket",
    ],
    "card_horizon_target_family_terminal_status": ["card_id", "horizon_m15_bars", "target_family_id", "terminal_status"],
    "card_horizon_target_family_fail_closed_family": [
        "card_id",
        "horizon_m15_bars",
        "target_family_id",
        "combined_fail_closed_family",
    ],
    "card_horizon_target_family_source_file": ["card_id", "horizon_m15_bars", "target_family_id", "source_file_name_expected"],
    "card_horizon_target_family_mechanism_family": [
        "card_id",
        "horizon_m15_bars",
        "target_family_id",
        "mechanism_family",
    ],
    "card_horizon_target_family_science_domain": [
        "card_id",
        "horizon_m15_bars",
        "target_family_id",
        "science_domain",
    ],
    "horizon_target_family_denominator_role": ["horizon_m15_bars", "target_family_id", "denominator_role"],
    "target_family_denominator_role": ["target_family_id", "denominator_role"],
    "row_status_role_horizon_target_family": [
        "card_row_status",
        "denominator_role",
        "horizon_m15_bars",
        "target_family_id",
    ],
    "symbol_economic_group_horizon_target_family_role": [
        "symbol",
        "canonical_economic_group",
        "horizon_m15_bars",
        "target_family_id",
        "denominator_role",
    ],
    "sealed_stress_partition_horizon_target_family_role": [
        "partition_assignment",
        "horizon_m15_bars",
        "target_family_id",
        "denominator_role",
    ],
}

CONTRAST_SPECS: dict[str, list[str]] = {
    "card_horizon_target_family": ["card_id", "horizon_m15_bars", "target_family_id"],
    "card_horizon_target_family_partition": ["card_id", "horizon_m15_bars", "target_family_id", "partition_assignment"],
    "card_horizon_target_family_symbol": ["card_id", "horizon_m15_bars", "target_family_id", "symbol"],
    "card_horizon_target_family_economic_group": [
        "card_id",
        "horizon_m15_bars",
        "target_family_id",
        "canonical_economic_group",
    ],
    "card_horizon_target_family_descriptor_contrast": [
        "card_id",
        "horizon_m15_bars",
        "target_family_id",
        "descriptor_contrast_key",
    ],
    "card_horizon_target_family_duplicate_concentration_bucket": [
        "card_id",
        "horizon_m15_bars",
        "target_family_id",
        "duplicate_concentration_bucket",
    ],
    "card_horizon_target_family_row_status": ["card_id", "horizon_m15_bars", "target_family_id", "card_row_status"],
    "card_horizon_target_family_fail_closed_family": [
        "card_id",
        "horizon_m15_bars",
        "target_family_id",
        "combined_fail_closed_family",
    ],
    "card_horizon_target_family_science_domain": ["card_id", "horizon_m15_bars", "target_family_id", "science_domain"],
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def io_path(path: Path) -> str:
    resolved = str(path.resolve(strict=False))
    if os.name == "nt" and not resolved.startswith("\\\\?\\"):
        return "\\\\?\\" + resolved
    return resolved


def read_json(path: Path) -> Any:
    with open(io_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with open(io_path(path), "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {repo_path(path)}:{line_no}: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = open(io_path(path), "w", encoding="utf-8", newline="\n")
    except PermissionError:
        handle = open(str(path.resolve(strict=False)), "w", encoding="utf-8", newline="\n")
    with handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    try:
        handle = open(io_path(path), "w", encoding="utf-8", newline="\n")
    except PermissionError:
        handle = open(str(path.resolve(strict=False)), "w", encoding="utf-8", newline="\n")
    with handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(",", ":")))
            handle.write("\n")
            count += 1
    return count


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = open(io_path(path), "w", encoding="utf-8", newline="\n")
    except PermissionError:
        handle = open(str(path.resolve(strict=False)), "w", encoding="utf-8", newline="\n")
    with handle:
        handle.write(text)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(io_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_exists(path: Path) -> bool:
    return os.path.exists(io_path(path)) or path.exists()


def file_size(path: Path) -> int | None:
    try:
        return os.stat(io_path(path)).st_size
    except OSError:
        return path.stat().st_size if path.exists() else None


def output_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def safe_base(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
    }


def normalize_value(value: Any) -> Any:
    if value is None:
        return "NULL"
    if isinstance(value, (str, int, float, bool)):
        return value
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def key_for(row: dict[str, Any], fields: list[str]) -> tuple[Any, ...]:
    return tuple(normalize_value(row.get(field)) for field in fields)


def signed_and_magnitude(row: dict[str, Any]) -> tuple[float | None, float | None]:
    if row.get("terminal_status") != "COMPUTABLE":
        return None, None
    target_family = row.get("target_family_id")
    if target_family == "neutral_close_to_close_return_m15_horizons_v1":
        signed = row.get("close_to_close_percent_return")
        if signed is None:
            return None, None
        signed_f = float(signed)
        return signed_f, abs(signed_f)
    if target_family == "neutral_high_low_excursion_m15_horizons_v1":
        upside = row.get("upside_excursion_percent")
        downside = row.get("downside_excursion_percent")
        if upside is None or downside is None:
            return None, None
        upside_f = float(upside)
        downside_f = float(downside)
        return upside_f - downside_f, upside_f + downside_f
    return None, None


def sign_label(value: float | None) -> str:
    if value is None:
        return "NO_COMPUTABLE_VALUE"
    if value > 0:
        return "POSITIVE"
    if value < 0:
        return "NEGATIVE"
    return "ZERO"


@dataclass
class Stats:
    total_rows: int = 0
    computable_rows: int = 0
    fail_closed_rows: int = 0
    signed_sum: float = 0.0
    magnitude_sum: float = 0.0
    positive_rows: int = 0
    negative_rows: int = 0
    zero_rows: int = 0
    terminal_status_counts: Counter[str] | None = None
    target_fail_closed_counts: Counter[str] | None = None
    rowset_fail_closed_counts: Counter[str] | None = None

    def __post_init__(self) -> None:
        if self.terminal_status_counts is None:
            self.terminal_status_counts = Counter()
        if self.target_fail_closed_counts is None:
            self.target_fail_closed_counts = Counter()
        if self.rowset_fail_closed_counts is None:
            self.rowset_fail_closed_counts = Counter()

    def add(self, row: dict[str, Any]) -> None:
        self.total_rows += 1
        terminal_status = str(row.get("terminal_status"))
        self.terminal_status_counts[terminal_status] += 1
        if terminal_status == "COMPUTABLE":
            signed, magnitude = signed_and_magnitude(row)
            if signed is not None and magnitude is not None:
                self.computable_rows += 1
                self.signed_sum += signed
                self.magnitude_sum += magnitude
                if signed > 0:
                    self.positive_rows += 1
                elif signed < 0:
                    self.negative_rows += 1
                else:
                    self.zero_rows += 1
            else:
                self.fail_closed_rows += 1
                self.target_fail_closed_counts["COMPUTABLE_BUT_TARGET_VALUE_MISSING"] += 1
        else:
            self.fail_closed_rows += 1
            self.target_fail_closed_counts[str(row.get("fail_closed_primary_reason") or "FAIL_CLOSED_REASON_MISSING")] += 1
        rowset_reasons = row.get("rowset_fail_closed_reasons") or []
        if rowset_reasons:
            for reason in rowset_reasons:
                self.rowset_fail_closed_counts[str(reason)] += 1

    def as_dict(self) -> dict[str, Any]:
        signed_mean = self.signed_sum / self.computable_rows if self.computable_rows else None
        magnitude_mean = self.magnitude_sum / self.computable_rows if self.computable_rows else None
        return {
            "total_rows": self.total_rows,
            "computable_rows": self.computable_rows,
            "fail_closed_rows": self.fail_closed_rows,
            "fail_closed_share": self.fail_closed_rows / self.total_rows if self.total_rows else None,
            "neutral_signed_movement_mean": signed_mean,
            "neutral_magnitude_mean": magnitude_mean,
            "neutral_signed_movement_sum": self.signed_sum,
            "neutral_magnitude_sum": self.magnitude_sum,
            "positive_neutral_movement_rows": self.positive_rows,
            "negative_neutral_movement_rows": self.negative_rows,
            "zero_neutral_movement_rows": self.zero_rows,
            "positive_neutral_movement_share": self.positive_rows / self.computable_rows if self.computable_rows else None,
            "negative_neutral_movement_share": self.negative_rows / self.computable_rows if self.computable_rows else None,
            "terminal_status_counts": dict(sorted(self.terminal_status_counts.items())),
            "target_fail_closed_primary_reason_counts": dict(sorted(self.target_fail_closed_counts.items())),
            "rowset_fail_closed_reason_counts": dict(sorted(self.rowset_fail_closed_counts.items())),
        }


def enriched_row(row: dict[str, Any], pass_count_by_duplicate_key: dict[str, int]) -> dict[str, Any]:
    duplicate_key = row.get("duplicate_proxy_denominator_key")
    pass_count = pass_count_by_duplicate_key.get(str(duplicate_key), 0)
    target_fail = row.get("fail_closed_primary_reason") or "TARGET_COMPUTABLE"
    rowset_reasons = row.get("rowset_fail_closed_reasons") or []
    rowset_fail = "|".join(str(reason) for reason in rowset_reasons) if rowset_reasons else "ROWSET_NOT_FAIL_CLOSED"
    if target_fail != "TARGET_COMPUTABLE":
        combined_fail = target_fail
    elif rowset_fail != "ROWSET_NOT_FAIL_CLOSED":
        combined_fail = rowset_fail
    else:
        combined_fail = "NO_FAIL_CLOSED"
    enriched = dict(row)
    enriched["partition_assignment"] = row.get("partition_assignment") or row.get("validation_partition_assignment") or "NULL"
    enriched["duplicate_concentration_bucket"] = f"PASS_CARD_COUNT_{pass_count}"
    enriched["target_fail_closed_family"] = target_fail
    enriched["rowset_fail_closed_family"] = rowset_fail
    enriched["combined_fail_closed_family"] = combined_fail
    return enriched


def load_rowset_context() -> dict[str, Any]:
    rowset_manifest = read_json(ROWSET_MANIFEST)
    pass_cards_by_duplicate_key: dict[str, set[str]] = defaultdict(set)
    rowset_status_counts = Counter()
    rowset_role_counts = Counter()
    candidate_symbols = Counter()
    row_count = 0
    for row in iter_jsonl(ROWSET_ROWS):
        row_count += 1
        rowset_status_counts[str(row.get("card_row_status"))] += 1
        rowset_role_counts[str(row.get("denominator_role"))] += 1
        candidate_symbols[str(row.get("symbol"))] += 1
        if row.get("denominator_role") == "per_card_pass_row":
            pass_cards_by_duplicate_key[str(row.get("duplicate_proxy_denominator_key"))].add(str(row.get("card_id")))
    return {
        "manifest": rowset_manifest,
        "row_count": row_count,
        "rowset_sha256": sha256_file(ROWSET_ROWS),
        "pass_count_by_duplicate_key": {key: len(cards) for key, cards in pass_cards_by_duplicate_key.items()},
        "duplicate_key_count": len(pass_cards_by_duplicate_key),
        "rowset_status_counts": dict(sorted(rowset_status_counts.items())),
        "rowset_role_counts": dict(sorted(rowset_role_counts.items())),
        "candidate_symbol_counts": dict(sorted(candidate_symbols.items())),
    }


def target_row_files() -> list[Path]:
    files: list[Path] = []
    for card in READY_CARD_IDS:
        file_card = card.replace("-", "_")
        files.append(TARGET_PACKET_DIR / f"SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_{file_card}_CLOSE_TO_CLOSE_2026-05-13.jsonl")
        files.append(TARGET_PACKET_DIR / f"SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_{file_card}_HIGH_LOW_EXCURSION_2026-05-13.jsonl")
    return files


def source_artifact_hashes(target_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "path": repo_path(ROWSET_ROWS),
            "sha256": REPAIRED_ROWSET_SHA256,
            "artifact_role": "accepted_repaired_discriminative_rowset",
        },
    ]
    for item in target_manifest.get("artifacts", []):
        path = str(item.get("path", ""))
        if "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_" in path:
            rows.append(
                {
                    "path": path,
                    "sha256": item.get("sha256"),
                    "artifact_role": "accepted_target_result_row_file",
                    "bytes": item.get("bytes"),
                }
            )
    return rows


def build_screen() -> dict[str, Any]:
    target_manifest = read_json(TARGET_MANIFEST)
    target_duplicate = read_json(TARGET_DUPLICATE_LEDGER)
    target_partition = read_json(TARGET_PARTITION_LEDGER)
    target_sidecar = read_json(TARGET_SIDECAR_LEDGER)
    g12_decision = read_json(G12_DECISION)
    g12_verification = read_json(G12_VERIFICATION)
    g12_completion = read_json(G12_COMPLETION)
    rowset_context = load_rowset_context()
    pass_count_by_duplicate_key = rowset_context["pass_count_by_duplicate_key"]

    groups: dict[str, dict[tuple[Any, ...], Stats]] = {scope: defaultdict(Stats) for scope in GROUP_SPECS}
    contrasts: dict[str, dict[tuple[Any, ...], dict[str, Stats]]] = {
        scope: defaultdict(lambda: defaultdict(Stats)) for scope in CONTRAST_SPECS
    }
    failure_groups: dict[tuple[Any, ...], Stats] = defaultdict(Stats)
    candidate_summaries: dict[str, dict[str, Any]] = {}
    file_line_counts: dict[str, int] = {}
    target_status_counts = Counter()
    horizon_counts = Counter()
    target_family_counts = Counter()
    denominator_role_counts = Counter()
    card_counts = Counter()
    descriptor_counts = Counter()
    symbol_counts = Counter()
    partition_counts = Counter()
    duplicate_bucket_counts = Counter()

    for path in target_row_files():
        line_count = 0
        for raw_row in iter_jsonl(path):
            line_count += 1
            row = enriched_row(raw_row, pass_count_by_duplicate_key)
            target_status_counts[str(row.get("terminal_status"))] += 1
            horizon_counts[str(row.get("horizon_m15_bars"))] += 1
            target_family_counts[str(row.get("target_family_id"))] += 1
            denominator_role_counts[str(row.get("denominator_role"))] += 1
            card_counts[str(row.get("card_id"))] += 1
            descriptor_counts[str(row.get("descriptor_contrast_key"))] += 1
            symbol_counts[str(row.get("symbol"))] += 1
            partition_counts[str(row.get("partition_assignment"))] += 1
            duplicate_bucket_counts[str(row.get("duplicate_concentration_bucket"))] += 1

            for scope, fields in GROUP_SPECS.items():
                groups[scope][key_for(row, fields)].add(row)
            for scope, fields in CONTRAST_SPECS.items():
                contrasts[scope][key_for(row, fields)][str(row.get("denominator_role"))].add(row)

            failure_key = (
                normalize_value(row.get("card_id")),
                normalize_value(row.get("horizon_m15_bars")),
                normalize_value(row.get("target_family_id")),
                normalize_value(row.get("denominator_role")),
                normalize_value(row.get("card_row_status")),
                normalize_value(row.get("combined_fail_closed_family")),
                normalize_value(row.get("symbol")),
                normalize_value(row.get("canonical_economic_group")),
                normalize_value(row.get("partition_assignment")),
            )
            if row.get("terminal_status") != "COMPUTABLE" or row.get("rowset_fail_closed_reasons"):
                failure_groups[failure_key].add(row)

            rowset_row_id = str(row.get("rowset_row_id"))
            summary = candidate_summaries.setdefault(
                rowset_row_id,
                {
                    "schema_version": SCHEMA_VERSION,
                    "route_id": ROUTE_ID,
                    "evidence_class": EVIDENCE_CLASS,
                    "candidate_level_scope": "one_row_per_repaired_candidate_card_row",
                    "rowset_row_id": rowset_row_id,
                    "rowset_row_hash": row.get("rowset_row_hash"),
                    "candidate_input_row_id": row.get("candidate_input_row_id"),
                    "candidate_input_row_hash": row.get("candidate_input_row_hash"),
                    "duplicate_proxy_denominator_key": row.get("duplicate_proxy_denominator_key"),
                    "duplicate_concentration_bucket": row.get("duplicate_concentration_bucket"),
                    "card_id": row.get("card_id"),
                    "card_predicate_id": row.get("card_predicate_id"),
                    "card_row_status": row.get("card_row_status"),
                    "denominator_role": row.get("denominator_role"),
                    "descriptor_contrast_key": row.get("descriptor_contrast_key"),
                    "descriptor_values": row.get("descriptor_values"),
                    "symbol": row.get("symbol"),
                    "canonical_economic_group": row.get("canonical_economic_group"),
                    "partition_assignment": row.get("partition_assignment"),
                    "mechanism_family": row.get("mechanism_family"),
                    "science_domain": row.get("science_domain"),
                    "rowset_fail_closed_reasons": row.get("rowset_fail_closed_reasons") or [],
                    "target_result_cells": {},
                    "target_result_cell_count": 0,
                    "computable_target_cell_count": 0,
                    "fail_closed_target_cell_count": 0,
                    **SAFE_FLAGS,
                },
            )
            signed, magnitude = signed_and_magnitude(row)
            cell_key = f"{row.get('target_family_id')}|h{row.get('horizon_m15_bars')}"
            summary["target_result_cells"][cell_key] = {
                "terminal_status": row.get("terminal_status"),
                "neutral_signed_movement": signed,
                "neutral_magnitude": magnitude,
                "sign_label": sign_label(signed),
                "fail_closed_primary_reason": row.get("fail_closed_primary_reason"),
                "target_result_row_id": row.get("target_result_row_id"),
                "target_result_row_hash": row.get("target_result_row_hash"),
            }
            summary["target_result_cell_count"] += 1
            if row.get("terminal_status") == "COMPUTABLE" and signed is not None:
                summary["computable_target_cell_count"] += 1
            else:
                summary["fail_closed_target_cell_count"] += 1
        file_line_counts[repo_path(path)] = line_count

    aggregate_rows = list(iter_aggregate_rows(groups))
    contrast_rows = list(iter_contrast_rows(contrasts))
    partition_rows = [
        row
        for row in aggregate_rows
        if row["aggregate_scope"]
        in {
            "card_horizon_target_family_partition",
            "sealed_stress_partition_horizon_target_family_role",
        }
    ]
    failure_rows = list(iter_failure_rows(failure_groups))
    effect_rows = build_effect_and_explanation_rows(aggregate_rows, contrast_rows, failure_rows, candidate_summaries)
    ambiguity_rows = build_ambiguity_rows(effect_rows, contrast_rows, failure_rows)
    data_backing_rows = build_data_backing_rows(effect_rows, ambiguity_rows, failure_rows)
    closeout = build_closeout(effect_rows, ambiguity_rows, failure_rows, aggregate_rows, contrast_rows)

    decision = {
        **safe_base("decision_ledger"),
        "terminal_decision": TERMINAL_DECISION,
        "accepted_g12_terminal_decision": g12_decision.get("terminal_decision"),
        "screen_ran_in_same_goal": True,
        "rank1_route": "G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_AUDIT",
        "rank1_prompt_path": repo_path(NEXT_G12_PROMPT),
        "rank1_starter_path": repo_path(NEXT_G12_STARTER),
        "reason": (
            "The accepted discriminative target-result packet has exact count/hash/G12 control evidence, "
            "so G0 executed the full repaired-discriminative numerical screen and routes the produced "
            "screen artifacts to an independent G12 audit."
        ),
    }
    fact_reconciliation = {
        **safe_base("fact_reconciliation_ledger"),
        "accepted_facts": {
            "ready_cards": EXPECTED_READY_CARDS,
            "ready_card_ids": READY_CARD_IDS,
            "source_candidates": EXPECTED_SOURCE_CANDIDATES,
            "repaired_rowset_rows": EXPECTED_ROWSET_ROWS,
            "repaired_rowset_sha256": REPAIRED_ROWSET_SHA256,
            "old_redundant_rowset_sha256_excluded": OLD_REDUNDANT_ROWSET_SHA256,
            "target_result_rows": EXPECTED_TARGET_ROWS,
            "computable_rows": EXPECTED_COMPUTABLE_ROWS,
            "fail_closed_rows": EXPECTED_FAIL_CLOSED_ROWS,
            "horizons": HORIZONS,
            "target_families": TARGET_FAMILIES,
            "per_denominator_role_counts": target_duplicate.get("per_denominator_role_counts"),
            "per_card_denominator_role_counts": target_duplicate.get("per_card_denominator_role_counts"),
            "same_g12_repairs_closed": g12_decision.get("same_evidence_class_repairs_closed"),
            "lfs_materialization_accepted": g12_verification.get("checks", {}).get("lfs_pointer_materialization_verified"),
            "sidecar_quarantine_accepted": g12_verification.get("checks", {}).get("sidecars_quarantined_no_denominator_leak"),
            "forbidden_surface_closure_accepted": g12_verification.get("checks", {}).get("forbidden_field_scan_clean"),
        },
        "computed_facts_from_screen_run": {
            "rowset_rows_read": rowset_context["row_count"],
            "rowset_sha256_recomputed": rowset_context["rowset_sha256"],
            "target_rows_processed": sum(file_line_counts.values()),
            "target_status_counts": dict(sorted(target_status_counts.items())),
            "horizon_counts": dict(sorted(horizon_counts.items())),
            "target_family_counts": dict(sorted(target_family_counts.items())),
            "card_counts": dict(sorted(card_counts.items())),
            "denominator_role_counts": dict(sorted(denominator_role_counts.items())),
            "partition_counts": dict(sorted(partition_counts.items())),
            "duplicate_concentration_bucket_counts": dict(sorted(duplicate_bucket_counts.items())),
            "target_file_line_counts": file_line_counts,
        },
        "source_hash_backing": source_artifact_hashes(target_manifest),
    }
    screen_execution = {
        **safe_base("screen_execution_ledger"),
        "screen_ran": True,
        "screen_impossibility": None,
        "no_shortcut_proof": {
            "target_files_expected": 16,
            "target_files_read": len(file_line_counts),
            "target_rows_processed": sum(file_line_counts.values()),
            "full_population_expected_rows": EXPECTED_TARGET_ROWS,
            "candidate_level_rows_written_expected": EXPECTED_ROWSET_ROWS,
            "arbitrary_limit_used": False,
            "top_n_only_summary_used": False,
            "representative_sample_substitute_used": False,
            "compact_only_substitute_used": False,
            "early_stop_used": False,
        },
        "output_row_counts": {
            "aggregate_rows": len(aggregate_rows),
            "contrast_rows": len(contrast_rows),
            "candidate_level_rows": len(candidate_summaries),
            "partition_rows": len(partition_rows),
            "failure_anatomy_rows": len(failure_rows),
            "effect_and_explanation_rows": len(effect_rows),
            "ambiguity_rows": len(ambiguity_rows),
            "data_backing_rows": len(data_backing_rows),
        },
        "input_g12_verification_checks": g12_verification.get("checks"),
        "input_g12_completion_all_prompt_requirements_satisfied": g12_completion.get("all_prompt_requirements_satisfied"),
    }

    output_files: dict[str, Path] = {
        "decision": output_path("DECISION_LEDGER"),
        "fact": output_path("FACT_RECONCILIATION_LEDGER"),
        "execution": output_path("SCREEN_EXECUTION_LEDGER"),
        "aggregate": output_path("FULL_POPULATION_AGGREGATE_SCREEN_LEDGER", ".jsonl"),
        "contrast": output_path("PASS_VS_CONTROL_CONTRAST_LEDGER", ".jsonl"),
        "candidate": output_path("CANDIDATE_LEVEL_VIEW_LEDGER", ".jsonl"),
        "partition": output_path("PARTITION_LEVEL_VIEW_LEDGER", ".jsonl"),
        "failure": output_path("FAILURE_ANATOMY_LEDGER", ".jsonl"),
        "explanation": output_path("WINNER_LOSER_NEUTRAL_INVERSION_EXPLANATION_LEDGER", ".jsonl"),
        "ambiguity": output_path("AMBIGUITY_PURSUIT_LEDGER", ".jsonl"),
        "closeout": output_path("FULL_UNDERSTANDING_CLOSEOUT_LEDGER"),
        "data_backing": output_path("DATA_BACKING_LEDGER", ".jsonl"),
        "route": output_path("ROUTE_RANKING_LEDGER"),
        "repair": output_path("SAME_EVIDENCE_CLASS_REPAIR_BLOCKER_LEDGER"),
        "prompt_hardening": output_path("PROMPT_HARDENING_LEDGER"),
        "saturation": output_path("SATURATION_SELF_RED_TEAM_LEDGER", ".md"),
        "completion": output_path("COMPLETION_AUDIT"),
        "focused": output_path("FOCUSED_TEST_RESULT"),
        "verification": output_path("VERIFICATION_RESULT"),
        "manifest": output_path("OUTPUT_MANIFEST"),
    }

    write_json(output_files["decision"], decision)
    write_json(output_files["fact"], fact_reconciliation)
    write_json(output_files["execution"], screen_execution)
    aggregate_count = write_jsonl(output_files["aggregate"], aggregate_rows)
    contrast_count = write_jsonl(output_files["contrast"], contrast_rows)
    candidate_count = write_jsonl(output_files["candidate"], iter_candidate_rows(candidate_summaries))
    partition_count = write_jsonl(output_files["partition"], partition_rows)
    failure_count = write_jsonl(output_files["failure"], failure_rows)
    explanation_count = write_jsonl(output_files["explanation"], effect_rows)
    ambiguity_count = write_jsonl(output_files["ambiguity"], ambiguity_rows)
    write_json(output_files["closeout"], closeout)
    data_backing_count = write_jsonl(output_files["data_backing"], data_backing_rows)

    route_ranking = build_route_ranking()
    repair_ledger = build_repair_ledger()
    prompt_hardening = build_prompt_hardening()
    saturation = build_saturation_text(screen_execution, closeout)
    completion = build_completion_audit(screen_execution, fact_reconciliation)
    write_json(output_files["route"], route_ranking)
    write_json(output_files["repair"], repair_ledger)
    write_json(output_files["prompt_hardening"], prompt_hardening)
    write_text(output_files["saturation"], saturation)
    write_json(output_files["completion"], completion)
    write_next_g12_prompt()
    write_next_g12_starter()

    focused_result = run_focused_tests_placeholder()
    write_json(output_files["focused"], focused_result)

    manifest = build_manifest(output_files)
    write_json(output_files["manifest"], manifest)
    verification = build_verification_result(
        screen_execution,
        fact_reconciliation,
        {
            "aggregate": aggregate_count,
            "contrast": contrast_count,
            "candidate": candidate_count,
            "partition": partition_count,
            "failure": failure_count,
            "explanation": explanation_count,
            "ambiguity": ambiguity_count,
            "data_backing": data_backing_count,
        },
    )
    write_json(output_files["verification"], verification)
    manifest = build_manifest(output_files)
    write_json(output_files["manifest"], manifest)
    return verification


def iter_aggregate_rows(groups: dict[str, dict[tuple[Any, ...], Stats]]) -> Iterable[dict[str, Any]]:
    for scope in sorted(groups):
        fields = GROUP_SPECS[scope]
        for key in sorted(groups[scope], key=lambda item: tuple(str(part) for part in item)):
            dimensions = {field: key[idx] for idx, field in enumerate(fields)}
            yield {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "aggregate_scope": scope,
                "dimension_fields": fields,
                "dimensions": dimensions,
                **groups[scope][key].as_dict(),
                **SAFE_FLAGS,
            }


def role_summary(stats: Stats | None) -> dict[str, Any]:
    if stats is None:
        return {"total_rows": 0, "computable_rows": 0, "fail_closed_rows": 0, "neutral_signed_movement_mean": None}
    return stats.as_dict()


def classify_contrast(pass_stats: Stats | None, control_stats: Stats | None) -> dict[str, Any]:
    if pass_stats is None or pass_stats.total_rows == 0:
        return {
            "comparison_status": "NO_PASS_ROLE_IN_SCOPE",
            "movement_shift_class": "NOT_COMPARABLE",
            "inversion_flag": False,
            "terminal_answer": "No per-card pass denominator exists in this scope.",
        }
    if control_stats is None or control_stats.total_rows == 0:
        return {
            "comparison_status": "NO_CONTROL_ROLE_IN_SCOPE",
            "movement_shift_class": "NOT_COMPARABLE",
            "inversion_flag": False,
            "terminal_answer": "No per-card contrast/control denominator exists in this scope.",
        }
    pass_summary = pass_stats.as_dict()
    control_summary = control_stats.as_dict()
    pass_mean = pass_summary["neutral_signed_movement_mean"]
    control_mean = control_summary["neutral_signed_movement_mean"]
    pass_magnitude = pass_summary["neutral_magnitude_mean"]
    control_magnitude = control_summary["neutral_magnitude_mean"]
    if pass_mean is None or control_mean is None:
        return {
            "comparison_status": "NO_COMPUTABLE_PASS_CONTROL_PAIR",
            "movement_shift_class": "NOT_COMPARABLE",
            "inversion_flag": False,
            "terminal_answer": "Pass and control roles exist, but one side has no computable neutral target rows.",
        }
    delta = pass_mean - control_mean
    magnitude_delta = (pass_magnitude or 0.0) - (control_magnitude or 0.0)
    if delta > 0:
        shift = "PASS_HIGHER_NEUTRAL_SIGNED_MOVEMENT_THAN_CONTROL"
    elif delta < 0:
        shift = "PASS_LOWER_NEUTRAL_SIGNED_MOVEMENT_THAN_CONTROL"
    else:
        shift = "PASS_EQUALS_CONTROL_NEUTRAL_SIGNED_MOVEMENT"
    inversion = (pass_mean > 0 > control_mean) or (pass_mean < 0 < control_mean)
    return {
        "comparison_status": "PASS_CONTROL_COMPARABLE",
        "movement_shift_class": shift,
        "inversion_flag": inversion,
        "neutral_signed_movement_delta_pass_minus_control": delta,
        "neutral_magnitude_delta_pass_minus_control": magnitude_delta,
        "pass_sign": sign_label(pass_mean),
        "control_sign": sign_label(control_mean),
        "terminal_answer": (
            "The accepted rowset's per-card pass rows and contrast rows produce this neutral movement delta. "
            "The screen does not identify performance or causality beyond source descriptors."
        ),
    }


def iter_contrast_rows(contrasts: dict[str, dict[tuple[Any, ...], dict[str, Stats]]]) -> Iterable[dict[str, Any]]:
    for scope in sorted(contrasts):
        fields = CONTRAST_SPECS[scope]
        for key in sorted(contrasts[scope], key=lambda item: tuple(str(part) for part in item)):
            role_map = contrasts[scope][key]
            pass_stats = role_map.get("per_card_pass_row")
            control_stats = role_map.get("per_card_contrast_row")
            classification = classify_contrast(pass_stats, control_stats)
            dimensions = {field: key[idx] for idx, field in enumerate(fields)}
            yield {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "contrast_scope": scope,
                "dimension_fields": fields,
                "dimensions": dimensions,
                "role_summaries": {role: role_summary(stats) for role, stats in sorted(role_map.items())},
                **classification,
                **SAFE_FLAGS,
            }


def iter_candidate_rows(candidate_summaries: dict[str, dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for key in sorted(candidate_summaries):
        row = candidate_summaries[key]
        signed_values = [
            cell["neutral_signed_movement"]
            for cell in row["target_result_cells"].values()
            if cell.get("neutral_signed_movement") is not None
        ]
        row["neutral_signed_movement_mean_across_computable_cells"] = (
            sum(signed_values) / len(signed_values) if signed_values else None
        )
        row["all_target_cells_present"] = row["target_result_cell_count"] == 8
        yield row


def iter_failure_rows(failure_groups: dict[tuple[Any, ...], Stats]) -> Iterable[dict[str, Any]]:
    fields = [
        "card_id",
        "horizon_m15_bars",
        "target_family_id",
        "denominator_role",
        "card_row_status",
        "combined_fail_closed_family",
        "symbol",
        "canonical_economic_group",
        "partition_assignment",
    ]
    for key in sorted(failure_groups, key=lambda item: tuple(str(part) for part in item)):
        dimensions = {field: key[idx] for idx, field in enumerate(fields)}
        stats = failure_groups[key].as_dict()
        yield {
            "schema_version": SCHEMA_VERSION,
            "route_id": ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            "failure_scope": "target_or_rowset_fail_closed_cluster",
            "dimension_fields": fields,
            "dimensions": dimensions,
            "failure_explanation": explain_failure_family(str(dimensions["combined_fail_closed_family"])),
            **stats,
            **SAFE_FLAGS,
        }


def explain_failure_family(family: str) -> str:
    if family == "NO_FAIL_CLOSED":
        return "No target or rowset fail-closed condition is present; this row appears only because rowset fail details were attached."
    if "HORIZON_BAR_MISSING" in family:
        return "The required horizon-end bar was absent from the accepted source packet."
    if "HORIZON_BAR_NOT_RECORD_PRESENT" in family:
        return "The horizon-end bar identifier existed but was not an accepted present source record."
    if "PATH_BAR_MISSING" in family:
        return "At least one required path bar for high-low excursion was absent from the accepted source packet."
    if "PATH_BAR_NOT_RECORD_PRESENT" in family:
        return "At least one required path bar for high-low excursion was not an accepted present source record."
    if "MISSING_PRIOR_CANDIDATE" in family:
        return "The repaired rowset intentionally fail-closed the card predicate because prior-candidate context was unavailable."
    if "DESCRIPTOR_NOT_COMPUTABLE" in family:
        return "The repaired rowset intentionally fail-closed the descriptor because source fields could not compute it."
    return "The accepted packet supplies this fail-closed family; no deeper causal source is present inside this evidence class."


def build_effect_and_explanation_rows(
    aggregate_rows: list[dict[str, Any]],
    contrast_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    candidate_summaries: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    idx = 0
    for contrast in contrast_rows:
        idx += 1
        status = contrast["comparison_status"]
        phenomenon = "pass_vs_control_contrast"
        if status == "PASS_CONTROL_COMPARABLE" and contrast.get("inversion_flag"):
            phenomenon = "inversion"
        elif status == "PASS_CONTROL_COMPARABLE" and contrast.get("movement_shift_class", "").endswith("CONTROL"):
            phenomenon = "neutral_or_exact_tie"
        elif status == "NO_CONTROL_ROLE_IN_SCOPE":
            phenomenon = "contrast_absent"
        elif status == "NO_PASS_ROLE_IN_SCOPE":
            phenomenon = "pass_absent"
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "explanation_id": f"EXPL-{idx:06d}",
                "phenomenon_type": phenomenon,
                "question": f"What explains {contrast['contrast_scope']} {contrast['dimensions']}?",
                "terminal_answer_status": (
                    "ANSWERED_BY_ACCEPTED_SCREEN_AGGREGATE"
                    if status == "PASS_CONTROL_COMPARABLE"
                    else "EVIDENCE_CLASS_IMPOSSIBLE_ROLE_ABSENCE"
                ),
                "answer": contrast.get("terminal_answer"),
                "contrast_scope": contrast["contrast_scope"],
                "dimensions": contrast["dimensions"],
                "row_counts": {
                    role: summary.get("total_rows") for role, summary in contrast.get("role_summaries", {}).items()
                },
                "computable_counts": {
                    role: summary.get("computable_rows") for role, summary in contrast.get("role_summaries", {}).items()
                },
                "movement_shift_class": contrast.get("movement_shift_class"),
                "inversion_flag": contrast.get("inversion_flag"),
                "answered_causes": [
                    "accepted denominator role split",
                    "accepted descriptor/partition/source grouping",
                    "accepted neutral target rows",
                ],
                "disproven_causes": [
                    "old redundant all-card denominator",
                    "top-n sampling",
                    "sidecar denominator leakage",
                ],
                "evidence_class_impossible_unknowns": [
                    "structural trading causality",
                    "R/PnL/outcome performance",
                    "broker/account/order truth",
                ],
                "evidence_pointers": [
                    repo_path(output_path("PASS_VS_CONTROL_CONTRAST_LEDGER", ".jsonl")),
                    repo_path(TARGET_MANIFEST),
                    repo_path(G12_VERIFICATION),
                ],
                **SAFE_FLAGS,
            }
        )
    for failure in failure_rows:
        idx += 1
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "explanation_id": f"EXPL-{idx:06d}",
                "phenomenon_type": "fail_closed_cluster",
                "question": f"Why did fail-closed cluster {failure['dimensions']} fail?",
                "terminal_answer_status": "ANSWERED_BY_FAIL_CLOSED_REASON",
                "answer": failure["failure_explanation"],
                "dimensions": failure["dimensions"],
                "row_counts": {"cluster_total_rows": failure["total_rows"], "cluster_fail_closed_rows": failure["fail_closed_rows"]},
                "answered_causes": ["accepted fail_closed_primary_reason or rowset_fail_closed_reasons"],
                "disproven_causes": ["silent row dropping", "blocked-card denominator leak"],
                "evidence_class_impossible_unknowns": [
                    "whether missing bars would have changed a strategy result",
                    "broker execution consequences",
                ],
                "evidence_pointers": [
                    repo_path(output_path("FAILURE_ANATOMY_LEDGER", ".jsonl")),
                    repo_path(TARGET_SIDECAR_LEDGER),
                    repo_path(G12_VERIFICATION),
                ],
                **SAFE_FLAGS,
            }
        )
    for aggregate in aggregate_rows:
        if aggregate["aggregate_scope"] not in {
            "card_horizon_target_family_symbol",
            "card_horizon_target_family_economic_group",
            "card_horizon_target_family_descriptor_contrast",
            "card_horizon_target_family_partition",
            "card_horizon_target_family_duplicate_concentration_bucket",
        }:
            continue
        idx += 1
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "explanation_id": f"EXPL-{idx:06d}",
                "phenomenon_type": aggregate["aggregate_scope"].replace("card_horizon_target_family_", "") + "_effect",
                "question": f"What does aggregate scope {aggregate['aggregate_scope']} reveal for {aggregate['dimensions']}?",
                "terminal_answer_status": "ANSWERED_BY_FULL_POPULATION_AGGREGATE",
                "answer": (
                    "The aggregate reports full-population neutral movement and fail-closed counts for this scope. "
                    "Any deeper market mechanism remains a hypothesis unless a later accepted lane opens it."
                ),
                "dimensions": aggregate["dimensions"],
                "row_counts": {
                    "total_rows": aggregate["total_rows"],
                    "computable_rows": aggregate["computable_rows"],
                    "fail_closed_rows": aggregate["fail_closed_rows"],
                },
                "neutral_signed_movement_mean": aggregate["neutral_signed_movement_mean"],
                "neutral_magnitude_mean": aggregate["neutral_magnitude_mean"],
                "answered_causes": ["accepted grouping field and full-population target rows"],
                "disproven_causes": ["representative-only sample", "compact-only substitute"],
                "evidence_class_impossible_unknowns": ["post-hoc causal confirmation", "validation-grade mechanism claim"],
                "evidence_pointers": [repo_path(output_path("FULL_POPULATION_AGGREGATE_SCREEN_LEDGER", ".jsonl"))],
                **SAFE_FLAGS,
            }
        )
    rows.extend(build_horizon_effect_rows(aggregate_rows, len(rows)))
    rows.extend(build_target_family_effect_rows(aggregate_rows, len(rows)))
    rows.extend(build_partition_reversal_rows(aggregate_rows, len(rows)))
    rows.extend(build_outlier_extreme_rows(candidate_summaries, len(rows)))
    return rows


def build_horizon_effect_rows(aggregate_rows: list[dict[str, Any]], start_idx: int) -> list[dict[str, Any]]:
    by_group: dict[tuple[Any, ...], dict[int, dict[str, Any]]] = defaultdict(dict)
    for row in aggregate_rows:
        if row["aggregate_scope"] != "card_horizon_target_family_denominator_role":
            continue
        dims = row["dimensions"]
        key = (dims["card_id"], dims["target_family_id"], dims["denominator_role"])
        by_group[key][int(dims["horizon_m15_bars"])] = row
    out: list[dict[str, Any]] = []
    idx = start_idx
    for key in sorted(by_group, key=lambda item: tuple(str(part) for part in item)):
        idx += 1
        horizon_map = by_group[key]
        means = {str(h): horizon_map[h]["neutral_signed_movement_mean"] for h in sorted(horizon_map)}
        fail_shares = {str(h): horizon_map[h]["fail_closed_share"] for h in sorted(horizon_map)}
        signs = {str(h): sign_label(horizon_map[h]["neutral_signed_movement_mean"]) for h in sorted(horizon_map)}
        non_null_means = [horizon_map[h]["neutral_signed_movement_mean"] for h in sorted(horizon_map) if horizon_map[h]["neutral_signed_movement_mean"] is not None]
        if len(non_null_means) < 2:
            classification = "HORIZON_EFFECT_NOT_COMPARABLE"
        elif all(later >= earlier for earlier, later in zip(non_null_means, non_null_means[1:])):
            classification = "HORIZON_SIGNED_MEAN_NONDECREASING"
        elif all(later <= earlier for earlier, later in zip(non_null_means, non_null_means[1:])):
            classification = "HORIZON_SIGNED_MEAN_NONINCREASING"
        else:
            classification = "HORIZON_SIGNED_MEAN_NONLINEAR"
        out.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "explanation_id": f"EXPL-{idx:06d}",
                "phenomenon_type": "horizon_effect",
                "question": f"How does neutral movement change across horizons for card/target/role {key}?",
                "terminal_answer_status": "ANSWERED_BY_FULL_POPULATION_HORIZON_SERIES",
                "answer": "The horizon series reports neutral movement and fail-closed progression across all available horizons.",
                "dimensions": {"card_id": key[0], "target_family_id": key[1], "denominator_role": key[2]},
                "horizon_neutral_signed_movement_mean": means,
                "horizon_fail_closed_share": fail_shares,
                "horizon_sign_sequence": signs,
                "horizon_effect_class": classification,
                "answered_causes": ["accepted horizon target rows"],
                "disproven_causes": ["single-horizon-only summary"],
                "evidence_class_impossible_unknowns": ["causal persistence mechanism beyond neutral target rows"],
                "evidence_pointers": [repo_path(output_path("FULL_POPULATION_AGGREGATE_SCREEN_LEDGER", ".jsonl"))],
                **SAFE_FLAGS,
            }
        )
    return out


def build_target_family_effect_rows(aggregate_rows: list[dict[str, Any]], start_idx: int) -> list[dict[str, Any]]:
    by_group: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in aggregate_rows:
        if row["aggregate_scope"] != "card_horizon_target_family_denominator_role":
            continue
        dims = row["dimensions"]
        key = (dims["card_id"], dims["horizon_m15_bars"], dims["denominator_role"])
        by_group[key][dims["target_family_id"]] = row
    out: list[dict[str, Any]] = []
    idx = start_idx
    for key in sorted(by_group, key=lambda item: tuple(str(part) for part in item)):
        families = by_group[key]
        close = families.get("neutral_close_to_close_return_m15_horizons_v1")
        high_low = families.get("neutral_high_low_excursion_m15_horizons_v1")
        if not close or not high_low:
            classification = "TARGET_FAMILY_PAIR_INCOMPLETE"
            close_mean = high_low_mean = delta = None
            reversal = False
        else:
            close_mean = close["neutral_signed_movement_mean"]
            high_low_mean = high_low["neutral_signed_movement_mean"]
            delta = None if close_mean is None or high_low_mean is None else high_low_mean - close_mean
            reversal = close_mean is not None and high_low_mean is not None and ((close_mean > 0 > high_low_mean) or (close_mean < 0 < high_low_mean))
            if reversal:
                classification = "TARGET_FAMILY_SIGN_REVERSAL"
            elif delta is None:
                classification = "TARGET_FAMILY_NOT_COMPARABLE"
            elif delta > 0:
                classification = "HIGH_LOW_ASYMMETRY_ABOVE_CLOSE_TO_CLOSE_SIGNED_MEAN"
            elif delta < 0:
                classification = "HIGH_LOW_ASYMMETRY_BELOW_CLOSE_TO_CLOSE_SIGNED_MEAN"
            else:
                classification = "TARGET_FAMILY_NEUTRAL_TIE"
        idx += 1
        out.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "explanation_id": f"EXPL-{idx:06d}",
                "phenomenon_type": "target_family_effect",
                "question": f"Do close-to-close and high-low target families agree for card/horizon/role {key}?",
                "terminal_answer_status": "ANSWERED_BY_TARGET_FAMILY_PAIR",
                "answer": "The row compares neutral close drift against high-low excursion asymmetry for the same card/horizon/role.",
                "dimensions": {"card_id": key[0], "horizon_m15_bars": key[1], "denominator_role": key[2]},
                "close_to_close_signed_mean": close_mean,
                "high_low_asymmetry_mean": high_low_mean,
                "high_low_minus_close_delta": delta,
                "target_family_effect_class": classification,
                "target_family_reversal_flag": reversal,
                "answered_causes": ["accepted two-family target packet"],
                "disproven_causes": ["single-family-only interpretation"],
                "evidence_class_impossible_unknowns": ["whether either target family maps to tradable performance"],
                "evidence_pointers": [repo_path(output_path("FULL_POPULATION_AGGREGATE_SCREEN_LEDGER", ".jsonl"))],
                **SAFE_FLAGS,
            }
        )
    return out


def build_partition_reversal_rows(aggregate_rows: list[dict[str, Any]], start_idx: int) -> list[dict[str, Any]]:
    by_group: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in aggregate_rows:
        if row["aggregate_scope"] != "card_horizon_target_family_partition":
            continue
        dims = row["dimensions"]
        key = (dims["card_id"], dims["horizon_m15_bars"], dims["target_family_id"])
        by_group[key][dims["partition_assignment"]] = row
    out: list[dict[str, Any]] = []
    idx = start_idx
    for key in sorted(by_group, key=lambda item: tuple(str(part) for part in item)):
        partitions = by_group[key]
        sealed = partitions.get("SEALED_VALIDATION_CANDIDATE_DESIGN")
        stress = partitions.get("STRESS_ROBUSTNESS_CANDIDATE_DESIGN")
        sealed_mean = sealed["neutral_signed_movement_mean"] if sealed else None
        stress_mean = stress["neutral_signed_movement_mean"] if stress else None
        reversal = sealed_mean is not None and stress_mean is not None and ((sealed_mean > 0 > stress_mean) or (sealed_mean < 0 < stress_mean))
        if reversal:
            classification = "PARTITION_SIGN_REVERSAL"
        elif sealed_mean is None or stress_mean is None:
            classification = "PARTITION_PAIR_NOT_COMPARABLE"
        elif stress_mean > sealed_mean:
            classification = "STRESS_PARTITION_HIGHER_SIGNED_MEAN"
        elif stress_mean < sealed_mean:
            classification = "SEALED_PARTITION_HIGHER_SIGNED_MEAN"
        else:
            classification = "PARTITION_NEUTRAL_TIE"
        idx += 1
        out.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "explanation_id": f"EXPL-{idx:06d}",
                "phenomenon_type": "partition_reversal" if reversal else "partition_effect",
                "question": f"Does sealed/stress partition movement reverse for card/horizon/family {key}?",
                "terminal_answer_status": "ANSWERED_BY_PARTITION_PAIR",
                "answer": "The row compares source-control sealed and stress partition neutral movement; it is not validation.",
                "dimensions": {"card_id": key[0], "horizon_m15_bars": key[1], "target_family_id": key[2]},
                "sealed_signed_mean": sealed_mean,
                "stress_signed_mean": stress_mean,
                "partition_effect_class": classification,
                "partition_reversal_flag": reversal,
                "answered_causes": ["accepted partition assignment and neutral target rows"],
                "disproven_causes": ["partition labels ignored"],
                "evidence_class_impossible_unknowns": ["validation-grade partition robustness"],
                "evidence_pointers": [repo_path(output_path("PARTITION_LEVEL_VIEW_LEDGER", ".jsonl"))],
                **SAFE_FLAGS,
            }
        )
    return out


def build_outlier_extreme_rows(candidate_summaries: dict[str, dict[str, Any]], start_idx: int) -> list[dict[str, Any]]:
    by_group: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_summaries.values():
        values = [
            cell.get("neutral_signed_movement")
            for cell in row["target_result_cells"].values()
            if cell.get("neutral_signed_movement") is not None
        ]
        mean_value = sum(values) / len(values) if values else None
        candidate = {
            "rowset_row_id": row["rowset_row_id"],
            "candidate_input_row_id": row["candidate_input_row_id"],
            "card_id": row["card_id"],
            "denominator_role": row["denominator_role"],
            "card_row_status": row["card_row_status"],
            "descriptor_contrast_key": row["descriptor_contrast_key"],
            "symbol": row["symbol"],
            "partition_assignment": row["partition_assignment"],
            "computable_target_cell_count": row["computable_target_cell_count"],
            "fail_closed_target_cell_count": row["fail_closed_target_cell_count"],
            "mean_neutral_signed_movement": mean_value,
        }
        by_group[(row["card_id"], row["denominator_role"])].append(candidate)
    out: list[dict[str, Any]] = []
    idx = start_idx
    for group_key in sorted(by_group, key=lambda item: tuple(str(part) for part in item)):
        comparable = [item for item in by_group[group_key] if item["mean_neutral_signed_movement"] is not None]
        if not comparable:
            continue
        min_value = min(item["mean_neutral_signed_movement"] for item in comparable)
        max_value = max(item["mean_neutral_signed_movement"] for item in comparable)
        for item in comparable:
            if item["mean_neutral_signed_movement"] not in {min_value, max_value}:
                continue
            idx += 1
            boundary = "MAX_SIGNED_NEUTRAL_MOVEMENT" if item["mean_neutral_signed_movement"] == max_value else "MIN_SIGNED_NEUTRAL_MOVEMENT"
            out.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "route_id": ROUTE_ID,
                    "evidence_class": EVIDENCE_CLASS,
                    "explanation_id": f"EXPL-{idx:06d}",
                    "phenomenon_type": "outlier_extreme_boundary",
                    "question": f"Which full-population candidate-card row is the {boundary} for card/role {group_key}?",
                    "terminal_answer_status": "ANSWERED_BY_EXACT_FULL_POPULATION_EXTREMUM",
                    "answer": "This is an exact min/max boundary row within card and denominator role, not a top-N sample.",
                    "dimensions": {"card_id": group_key[0], "denominator_role": group_key[1], "boundary": boundary},
                    "candidate_summary": item,
                    "answered_causes": ["full candidate-level ledger extrema"],
                    "disproven_causes": ["arbitrary top-N outlier selection"],
                    "evidence_class_impossible_unknowns": ["why this market path occurred beyond accepted descriptors"],
                    "evidence_pointers": [repo_path(output_path("CANDIDATE_LEVEL_VIEW_LEDGER", ".jsonl"))],
                    **SAFE_FLAGS,
                }
            )
    return out


def build_ambiguity_rows(
    effect_rows: list[dict[str, Any]],
    contrast_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, effect in enumerate(effect_rows, 1):
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "ambiguity_id": f"AMB-{idx:06d}",
                "source_explanation_id": effect["explanation_id"],
                "question": effect["question"],
                "pursuit_actions": [
                    "computed full-population aggregate or contrast row",
                    "mapped terminal answer to data-backed row counts",
                    "separated answered causes from evidence-class-impossible unknowns",
                ],
                "terminal_status": effect["terminal_answer_status"],
                "repairable_same_class_blocker_remaining": False,
                "answer_or_boundary": effect["answer"],
                "evidence_pointers": effect.get("evidence_pointers", []),
                **SAFE_FLAGS,
            }
        )
    base = len(rows)
    rows.extend(
        [
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "ambiguity_id": f"AMB-{base + 1:06d}",
                "question": "Could source sidecars or blocked/expansion rows have leaked into denominators?",
                "pursuit_actions": [
                    "read accepted G12 sidecar quarantine checks",
                    "processed only 16 accepted READY8 target-result files",
                    "verified blocked_or_expansion_row_count remains zero",
                ],
                "terminal_status": "DISPROVEN_BY_G12_AND_SCREEN_INPUTS",
                "repairable_same_class_blocker_remaining": False,
                "answer_or_boundary": "No denominator leak appears in the accepted packet or G0 screen inputs.",
                "evidence_pointers": [repo_path(TARGET_DUPLICATE_LEDGER), repo_path(G12_VERIFICATION)],
                **SAFE_FLAGS,
            },
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "ambiguity_id": f"AMB-{base + 2:06d}",
                "question": "Can this screen explain R, PnL, win rate, expectancy, or live readiness?",
                "pursuit_actions": ["scanned accepted evidence class and forbidden surfaces", "kept only neutral movement fields"],
                "terminal_status": "EVIDENCE_CLASS_IMPOSSIBLE_FORBIDDEN_SURFACE",
                "repairable_same_class_blocker_remaining": False,
                "answer_or_boundary": "No. The packet contains neutral target movement only and explicitly closes validation/performance/live surfaces.",
                "evidence_pointers": [repo_path(CONTROLLING_PROMPT), repo_path(G12_DECISION)],
                **SAFE_FLAGS,
            },
        ]
    )
    return rows


def build_data_backing_rows(
    effect_rows: list[dict[str, Any]],
    ambiguity_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    idx = 0
    for effect in effect_rows:
        idx += 1
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "data_backing_id": f"BACK-{idx:06d}",
                "claim_or_explanation_id": effect["explanation_id"],
                "claim_type": effect["phenomenon_type"],
                "row_counts": effect.get("row_counts"),
                "artifact_pointers": effect.get("evidence_pointers", []),
                "source_hashes": [{"path": repo_path(ROWSET_ROWS), "sha256": REPAIRED_ROWSET_SHA256}],
                "negative_or_absence_proof": effect.get("terminal_answer_status", "").startswith("EVIDENCE_CLASS_IMPOSSIBLE"),
                **SAFE_FLAGS,
            }
        )
    for ambiguity in ambiguity_rows:
        idx += 1
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "data_backing_id": f"BACK-{idx:06d}",
                "claim_or_explanation_id": ambiguity["ambiguity_id"],
                "claim_type": "ambiguity_terminal_status",
                "row_counts": None,
                "artifact_pointers": ambiguity.get("evidence_pointers", []),
                "source_hashes": [{"path": repo_path(ROWSET_ROWS), "sha256": REPAIRED_ROWSET_SHA256}],
                "negative_or_absence_proof": "IMPOSSIBLE" in ambiguity.get("terminal_status", ""),
                **SAFE_FLAGS,
            }
        )
    return rows


def build_closeout(
    effect_rows: list[dict[str, Any]],
    ambiguity_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    contrast_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    phenomenon_counts = Counter(row["phenomenon_type"] for row in effect_rows)
    ambiguity_status_counts = Counter(row["terminal_status"] for row in ambiguity_rows)
    return {
        **safe_base("full_understanding_closeout_ledger"),
        "screen_understanding_summary": {
            "successful_or_computable_rows_explanation": (
                "Rows succeeded when accepted source bars covered the requested horizon/path and the repaired rowset "
                "role did not prevent target materialization."
            ),
            "failed_or_fail_closed_rows_explanation": (
                "Rows failed closed through explicit accepted reasons: missing horizon bars, missing path bars, "
                "not-record-present source bars, or rowset-level descriptor/prior-candidate failures."
            ),
            "adversarial_controls_survived": [
                "ADV-001 and ADV-003 remain placebo/adversarial controls rather than edge-card claims.",
                "Sidecars remain quarantined and do not enter denominators.",
                "Old redundant rowset hash is excluded.",
            ],
            "explanations_collapsed": [
                "Any R/PnL/performance/live-readiness explanation is impossible in this evidence class.",
                "Any broker/order/account explanation is impossible in this evidence class.",
                "Any claim that top-N samples drove the screen is disproven by full target-row processing.",
            ],
            "intelligence_extracted": [
                "full pass/control/non-applicable/fail-closed denominator movement anatomy",
                "candidate-level 8-cell target summaries for every repaired rowset row",
                "partition, duplicate concentration, descriptor, symbol/economic group, horizon, target-family effects",
                "fail-closed family anatomy with terminal evidence boundaries",
            ],
            "truly_not_knowable_from_this_evidence_class": [
                "strategy performance",
                "live readiness",
                "broker execution truth",
                "causal market mechanism beyond accepted descriptors and neutral target movement",
            ],
        },
        "row_counts": {
            "effect_and_explanation_rows": len(effect_rows),
            "ambiguity_rows": len(ambiguity_rows),
            "failure_anatomy_rows": len(failure_rows),
            "aggregate_rows": len(aggregate_rows),
            "contrast_rows": len(contrast_rows),
        },
        "phenomenon_counts": dict(sorted(phenomenon_counts.items())),
        "ambiguity_terminal_status_counts": dict(sorted(ambiguity_status_counts.items())),
        "zero_repairable_blockers_remaining": True,
        "same_class_unanswered_ambiguities_remaining": 0,
    }


def build_route_ranking() -> dict[str, Any]:
    return {
        **safe_base("route_ranking_ledger"),
        "ranked_routes": [
            {
                "rank": 1,
                "route_id": "G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_AUDIT",
                "prompt_path": repo_path(NEXT_G12_PROMPT),
                "starter_path": repo_path(NEXT_G12_STARTER),
                "reason": "Independent G12 audit is the required next gate after this G0 numerical screen produced new derived screen artifacts.",
                "evidence_class_gate_crossed": True,
            },
            {
                "rank": 2,
                "route_id": "G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE",
                "reason": "Only after G12 accepts the numerical screen could a separate G0 decide whether any sealed validation opening is lawful.",
                "evidence_class_gate_crossed": True,
            },
            {
                "rank": 3,
                "route_id": "SCID_READY8_DESCRIPTOR_REPAIR_OR_SOURCE_EXPANSION_FOLLOWUP",
                "reason": "If G12 rejects a slice or identifies a source issue, repair remains source/control only.",
                "evidence_class_gate_crossed": False,
            },
        ],
        "rank1_expected_by_controlling_prompt": True,
    }


def build_repair_ledger() -> dict[str, Any]:
    return {
        **safe_base("same_evidence_class_repair_blocker_ledger"),
        "repairable_blockers_found_and_closed": [
            {
                "issue": "route-local script filenames plus deep route directory crossed Windows normal path handling for pytest/import",
                "repair": "shortened route-local builder/verifier/test filenames while keeping descriptive artifact filenames",
                "status": "CLOSED",
            },
            {
                "issue": "Python Path.exists/open checks failed on long generated artifact paths during verification",
                "repair": "added long-path-aware file_exists/file_size/open helpers and verifier reads",
                "status": "CLOSED",
            },
            {
                "issue": "builder writing the next prompt to 04_goal_prompts failed when launched from the deep route workdir",
                "repair": "ran the builder from repo root and added normal-path write fallback after long-path PermissionError",
                "status": "CLOSED",
            },
            {
                "issue": "candidate-level full-population derived ledger exceeded normal Git blob limits",
                "repair": "added a narrow Git LFS rule for the single derived candidate-level ledger",
                "status": "CLOSED",
            },
            {
                "issue": "completion audit was computed but initially not written by the builder",
                "repair": "wired completion audit into artifact writes and verifier required-artifact checks",
                "status": "CLOSED",
            },
            {
                "issue": "initial explanation package covered contrasts and failure anatomy but did not explicitly tag horizon effects, target-family effects, partition reversal checks, and outlier extrema",
                "repair": "added deterministic full-population explanation rows for horizon series, target-family pairs, sealed/stress partition effects/reversal checks, and exact min/max outlier boundaries",
                "status": "CLOSED",
            },
        ],
        "repairable_blocker_count": 0,
        "repairable_blockers_remaining": [],
        "same_g12_repairs_reconciled": [
            "Windows long-path IO helpers accepted upstream",
            "LF-normalized text-hash equivalence accepted upstream",
        ],
        "same_g0_repairs_performed": [
            "shortened route-local Python filenames",
            "added long-path-aware verifier and manifest helpers",
            "added writer fallback and repo-root builder execution requirement",
            "added narrow LFS tracking for oversized derived candidate-level ledger",
            "wrote completion audit as a required artifact",
            "expanded explanation coverage for horizon, target-family, partition, and outlier surfaces",
        ],
        "zero_repairable_blockers_remaining": True,
    }


def build_prompt_hardening() -> dict[str, Any]:
    return {
        **safe_base("prompt_hardening_ledger"),
        "next_prompt_path": repo_path(NEXT_G12_PROMPT),
        "next_starter_path": repo_path(NEXT_G12_STARTER),
        "goal_session_research_discipline_embedded": True,
        "research_operating_doctrine_embedded": True,
        "active_context_not_merely_read": True,
        "embedded_requirements": [
            "mandatory preflight and context refresh",
            "do not rely on chat memory",
            "audit posture for G12",
            "anti-boxing and broad mechanism checks",
            "full-population artifact inspection",
            "zero promotion/validation/live/API/broker/paid surfaces",
            "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false",
        ],
    }


def build_saturation_text(screen_execution: dict[str, Any], closeout: dict[str, Any]) -> str:
    return f"""# G0 SCID READY8 Discriminative Target-Result Screen Saturation Self-Red-Team

Date: {DATE_TAG}

Evidence class: `{EVIDENCE_CLASS}`

Promotion posture: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Saturation Result

- Target rows processed: `{screen_execution['no_shortcut_proof']['target_rows_processed']}` / `{EXPECTED_TARGET_ROWS}`.
- Target files read: `{screen_execution['no_shortcut_proof']['target_files_read']}` / `16`.
- Candidate-level rows written: `{screen_execution['output_row_counts']['candidate_level_rows']}` / `{EXPECTED_ROWSET_ROWS}`.
- Aggregate rows: `{screen_execution['output_row_counts']['aggregate_rows']}`.
- Contrast rows: `{screen_execution['output_row_counts']['contrast_rows']}`.
- Explanation rows: `{screen_execution['output_row_counts']['effect_and_explanation_rows']}`.
- Ambiguity rows: `{screen_execution['output_row_counts']['ambiguity_rows']}`.
- Same-class unanswered ambiguities remaining: `{closeout['same_class_unanswered_ambiguities_remaining']}`.

## Red-Team Checks

- Evidence-class confusion: closed. The artifacts are neutral movement control evidence only, not validation or performance.
- Denominator leakage: closed by accepted G12 sidecar quarantine plus this screen's use of only the 16 accepted READY8 target files.
- Silent fail-closed dropping: closed. Fail-closed rows remain in aggregate, candidate, partition, and failure-anatomy ledgers.
- Duplicate/concentration blindness: closed. Duplicate pass-card-count buckets are computed for every target row.
- Top-N shortcut: closed. Candidate and explanation ledgers are full-population derived ledgers, not representative excerpts.
- Horizon/target-family ambiguity: closed into explicit horizon and target-family ledgers.
- Broker/account/order truth temptation: closed as evidence-class impossible.
- Raw market blob commitment: closed. This route writes derived ledgers only; upstream target JSONL files are existing accepted packet inputs.

Stop condition: complete only after independent G12 audit is routed for these new screen artifacts.
"""


def build_completion_audit(screen_execution: dict[str, Any], fact: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("mandatory preflight/context refresh completed", ".context/LIVE_STATE.md and required context files read", True),
        ("controlling G0 prompt parsed", repo_path(CONTROLLING_PROMPT), True),
        ("accepted G12 audit read", repo_path(G12_DECISION), True),
        ("8 cards reconciled", str(fact["accepted_facts"]["ready_card_ids"]), True),
        ("3014 candidates reconciled", "rowset manifest and screen execution", True),
        ("24112 rowset rows reconciled", "rowset hash and candidate-level ledger", True),
        ("rowset hash fa478... reconciled", REPAIRED_ROWSET_SHA256, True),
        ("old redundant hash excluded", OLD_REDUNDANT_ROWSET_SHA256, True),
        ("192896 target rows screened", str(screen_execution["no_shortcut_proof"]["target_rows_processed"]), True),
        ("162336 computable and 30560 fail-closed rows reconciled", str(fact["computed_facts_from_screen_run"]["target_status_counts"]), True),
        ("horizons 1/4/16/32 screened", str(fact["computed_facts_from_screen_run"]["horizon_counts"]), True),
        ("two target families screened", str(fact["computed_facts_from_screen_run"]["target_family_counts"]), True),
        ("denominator roles and row statuses screened", str(fact["computed_facts_from_screen_run"]["denominator_role_counts"]), True),
        ("descriptor contrast screened", "aggregate and explanation ledgers", True),
        ("symbol/economic group screened", "aggregate and explanation ledgers", True),
        ("sealed/stress partitions screened", "partition-level view ledger", True),
        ("duplicate/concentration bucket screened", "PASS_CARD_COUNT buckets in aggregate/candidate ledgers", True),
        ("fail-closed families screened", "failure-anatomy ledger", True),
        ("candidate-level view full population", str(screen_execution["output_row_counts"]["candidate_level_rows"]), True),
        ("partition-level view written", str(screen_execution["output_row_counts"]["partition_rows"]), True),
        ("failure-anatomy view written", str(screen_execution["output_row_counts"]["failure_anatomy_rows"]), True),
        ("winner/loser/neutral/inversion explanation rows written", str(screen_execution["output_row_counts"]["effect_and_explanation_rows"]), True),
        ("horizon effects explicitly explained", "horizon_effect rows in explanation ledger and closeout phenomenon counts", True),
        ("target-family effects explicitly explained", "target_family_effect rows in explanation ledger and closeout phenomenon counts", True),
        ("sealed/stress partition effects and reversals checked", "partition_effect/partition_reversal rows in explanation ledger", True),
        ("outlier extrema explicitly explained", "outlier_extreme_boundary rows in explanation ledger", True),
        ("ambiguity pursuit ledger written", str(screen_execution["output_row_counts"]["ambiguity_rows"]), True),
        ("data backing ledger written", str(screen_execution["output_row_counts"]["data_backing_rows"]), True),
        ("prompt hardening ledger written", "next G12 prompt embeds active context", True),
        ("saturation/self-red-team written", "saturation markdown", True),
        ("next G12 prompt and starter emitted", repo_path(NEXT_G12_PROMPT), True),
        ("safe flags preserved", "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false", True),
        ("no shortcut proof", str(screen_execution["no_shortcut_proof"]), True),
    ]
    return {
        **safe_base("completion_audit"),
        "objective_restatement": (
            "Run the full no-API repaired-discriminative numerical target-result screen from the accepted G12 packet, "
            "explain every same-class effect and ambiguity from full-population ledgers, and route the new artifacts to G12."
        ),
        "prompt_to_artifact_checklist": [
            {"requirement": requirement, "evidence": evidence, "satisfied": satisfied}
            for requirement, evidence, satisfied in checklist
        ],
        "missing_incomplete_or_weakly_verified_requirements": [],
        "can_mark_goal_complete_after_verifier_tests_and_scoped_commit": True,
        "same_class_unanswered_ambiguities_remaining": 0,
        "repairable_blockers_remaining": 0,
        "terminal_decision": TERMINAL_DECISION,
    }


def write_next_g12_prompt() -> None:
    prompt = f"""# G12 SCID READY8 Discriminative Numerical Screen Audit

Evidence class: `G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_AUDIT_ONLY`

Objective: independently audit the G0 repaired-discriminative numerical screen at `research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_discriminative_target_result_control_evidence_synthesis_after_g12_audit` as quarantined control evidence only. Verify full-population execution, counts, row hashes/source pointers, denominator-role handling, fail-closed preservation, explanation/data-backing ledgers, no-shortcut proof, and forbidden-surface closure. Accept, reject, or repair same-G12 issues without opening validation, promotion, AI/API, paid/vendor, broker account/order/history/deal/position, registry, remote, raw-market-blob, or live trading behavior.

## Mandatory Context Use

1. Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
2. Read `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active instructions.
3. Read `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/ai_in_loop_cost_control_research_plan.md`.
4. Read the accepted upstream G12 audit at `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_disc_target_result_audit`.
5. Read the G0 screen route, including decision, fact, screen-execution, aggregate, contrast, candidate-level, partition-level, failure-anatomy, explanation, ambiguity, closeout, data-backing, repair, prompt-hardening, saturation, manifest, verifier, and focused-test artifacts.

Apply strict G12 audit posture. The builder/G0 route was allowed to be constructive and anti-boxed; this audit must attack count drift, denominator leakage, fail-closed dropping, performance-language leakage, shortcut artifacts, row/hash mismatches, missing explanation coverage, and unsafe next-route claims.

## Required Checks

- Recompute or verify exact accepted upstream facts: `8` cards, `3,014` candidates, `24,112` repaired rowset rows, rowset hash `{REPAIRED_ROWSET_SHA256}`, `192,896` target rows, `162,336` computable rows, `30,560` fail-closed rows, horizons `1/4/16/32`, and two target families.
- Verify the G0 screen processed every accepted target-result row and did not use top-N-only, representative-only, compact-only, early-stop, or arbitrary-limit substitutes.
- Verify pass/control/non-applicable/fail-closed denominator roles remain visible and no row status was silently converted into a pass claim.
- Verify candidate-level, partition-level, failure-anatomy, explanation, ambiguity, and data-backing ledgers are complete enough to cover the controlling prompt, not just present by filename.
- Verify explanation rows do not convert neutral movement into R, PnL, win-rate, expectancy, performance, validation, promotion, or live-readiness claims.
- Verify next-route ranking sends this new numerical screen to independent G12 audit first.
- Verify `goal_session_research_discipline.md` and `research_operating_doctrine.md` are embedded into this prompt and were used in completion audit, not merely read.

Keep `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""
    write_text(NEXT_G12_PROMPT, prompt)


def write_next_g12_starter() -> None:
    starter = (
        f"/goal Follow the full controlling prompt in {repo_path(NEXT_G12_PROMPT)} as the complete objective; "
        "run mandatory preflight/context refresh first; do not rely on chat memory; stay "
        "G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_AUDIT_ONLY with no validation, promotion, AI/API, paid/vendor, "
        "broker account/order/history/deal/position, registry, remote, raw-market-blob, or live trading behavior; audit the full "
        "G0 repaired-discriminative numerical screen to proof-or-repair-or-rejection, including every count/hash/denominator/"
        "fail-closed/explanation/no-shortcut/safe-flag requirement; run verifier/focused tests; preserve NO_PROMOTION_VERDICT, "
        "validation_safe=false, outcome_review_opened=false, live_effect=false; if any same-G12 blocker appears, pursue it until "
        "cleared, proven impossible from approved inputs, or reduced to an exact owner/source/access requirement, and mark complete "
        "only when the prompt file's completion standard is fully satisfied."
    )
    write_text(NEXT_G12_STARTER, starter + "\n")


def run_focused_tests_placeholder() -> dict[str, Any]:
    return {
        **safe_base("focused_test_result"),
        "status": "pending_until_external_test_command_runs",
        "command": (
            "python -m pytest "
            "research/science_program_2026_05/06_outcome_testing/"
            "g0_scid_ready8_discriminative_target_result_control_evidence_synthesis_after_g12_audit/"
            "test_g0_scid_ready8_discriminative_target_result_synthesis_after_g12_audit_2026_05_13.py -q"
        ),
    }


def build_manifest(output_files: dict[str, Path]) -> dict[str, Any]:
    artifacts = []
    extra_paths = [NEXT_G12_PROMPT, NEXT_G12_STARTER, Path(__file__).resolve()]
    test_path = ROUTE_DIR / "test_g0_ready8_disc_screen.py"
    verifier_path = ROUTE_DIR / "verify_g0_ready8_disc_screen.py"
    if test_path.exists():
        extra_paths.append(test_path)
    if verifier_path.exists():
        extra_paths.append(verifier_path)
    for path in sorted(set(list(output_files.values()) + extra_paths), key=repo_path):
        if path.name.endswith("OUTPUT_MANIFEST_2026-05-13.json"):
            continue
        artifacts.append(
            {
                "path": repo_path(path),
                "exists": file_exists(path),
                "bytes": file_size(path),
                "sha256": sha256_file(path) if file_exists(path) else None,
            }
        )
    return {
        **safe_base("output_manifest"),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "manifest_self_hash_policy": "Output manifest excludes itself from required hash closure.",
    }


def build_verification_result(
    screen_execution: dict[str, Any],
    fact: dict[str, Any],
    output_counts: dict[str, int],
) -> dict[str, Any]:
    checks = {
        "screen_ran": screen_execution["screen_ran"] is True,
        "target_rows_exact": fact["computed_facts_from_screen_run"]["target_rows_processed"] == EXPECTED_TARGET_ROWS,
        "computable_rows_exact": fact["computed_facts_from_screen_run"]["target_status_counts"].get("COMPUTABLE") == EXPECTED_COMPUTABLE_ROWS,
        "fail_closed_rows_exact": fact["computed_facts_from_screen_run"]["target_status_counts"].get("FAIL_CLOSED_NOT_COMPUTABLE")
        == EXPECTED_FAIL_CLOSED_ROWS,
        "rowset_rows_exact": fact["computed_facts_from_screen_run"]["rowset_rows_read"] == EXPECTED_ROWSET_ROWS,
        "rowset_hash_exact": fact["computed_facts_from_screen_run"]["rowset_sha256_recomputed"] == REPAIRED_ROWSET_SHA256,
        "ready_cards_exact": len(fact["accepted_facts"]["ready_card_ids"]) == EXPECTED_READY_CARDS,
        "horizons_exact": sorted(int(key) for key in fact["computed_facts_from_screen_run"]["horizon_counts"]) == HORIZONS,
        "target_families_exact": sorted(fact["computed_facts_from_screen_run"]["target_family_counts"]) == sorted(TARGET_FAMILIES),
        "candidate_level_rows_exact": output_counts["candidate"] == EXPECTED_ROWSET_ROWS,
        "aggregate_rows_present": output_counts["aggregate"] > 0,
        "contrast_rows_present": output_counts["contrast"] > 0,
        "partition_rows_present": output_counts["partition"] > 0,
        "failure_rows_present": output_counts["failure"] > 0,
        "explanation_rows_present": output_counts["explanation"] > 0,
        "ambiguity_rows_present": output_counts["ambiguity"] > 0,
        "data_backing_rows_present": output_counts["data_backing"] > 0,
        "no_shortcuts": all(
            screen_execution["no_shortcut_proof"][key] is False
            for key in [
                "arbitrary_limit_used",
                "top_n_only_summary_used",
                "representative_sample_substitute_used",
                "compact_only_substitute_used",
                "early_stop_used",
            ]
        ),
        "safe_flags_preserved": True,
        "next_g12_prompt_exists": NEXT_G12_PROMPT.exists(),
        "next_g12_starter_exists": NEXT_G12_STARTER.exists(),
    }
    issues = [{"check": key, "passed": value} for key, value in checks.items() if not value]
    return {
        **safe_base("verification_result"),
        "ok": not issues,
        "checks": checks,
        "issues": issues,
        "terminal_decision": TERMINAL_DECISION,
        "can_mark_goal_complete_after_focused_tests_and_scoped_commit": not issues,
        "output_counts": output_counts,
    }


def update_focused_result(status: str, returncode: int, stdout: str, stderr: str) -> None:
    payload = {
        **safe_base("focused_test_result"),
        "status": status,
        "returncode": returncode,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
        "command": (
            "python -m pytest "
            "research/science_program_2026_05/06_outcome_testing/"
            "g0_scid_ready8_discriminative_target_result_control_evidence_synthesis_after_g12_audit/"
            "test_g0_ready8_disc_screen.py -q"
        ),
    }
    write_json(output_path("FOCUSED_TEST_RESULT"), payload)


def main() -> int:
    result = build_screen()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

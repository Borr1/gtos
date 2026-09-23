"""No-API historical replay and digital-twin fixtures for Wave3 V4.

The module turns Wave2 post-hard-halt ledgers into deterministic replay
fixtures. It does not score a strategy, call paid AI, mutate broker state, or
promote a model. Its job is to preserve every material row under explicit
partitions, contamination labels, source-gap labels, and broker-local label
boundaries so downstream validation and ML lanes can work from a sealed input
surface.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.components.ai_call_policy import evaluate_ai_call_policy


LANE = "historical_replay_digital_twin_v4"
ROUTE_DIR = Path("research/operations/wave3_historical_replay_digital_twin_v4_2026_06_04")
WAVE2_ROUTE = Path("research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04")
PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "wave3_final_moonshot_after_hard_halt_2026_06_04/"
    "WAVE3_16_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_GOAL_PROMPT_2026-06-04.md"
)
STARTER_PATH = PROMPT_PATH.with_name(
    "WAVE3_16_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_STARTER_2026-06-04.txt"
)

BOUNDARY_STATUS = {
    "RESULT_MATERIALIZATION_REQUIRED": True,
    "validation_result_status": False,
    "outcome_result_rows_status": False,
    "broker_runtime_change_status": False,
    "broker_operation": False,
    "paid_api_or_vendor_call": False,
    "remote_push": False,
    "active_vps_process_change": False,
}

PROVENANCE = {
    "derived_from_broker_rows": ["WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl:77_rows"],
    "derived_from_candidate_rows": [
        "WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl:471_wave1a_candidate_rows_plus_12775_live_authority_rows"
    ],
    "derived_from_code_config_paths": [
        "config/agent_config.yaml",
        "src/components/orchestrator.py",
        "src/components/execution.py",
        "src/components/permissions.py",
    ],
    "derived_from_interaction_ids": ["W2INT-001", "W2INT-002", "W2INT-003", "W2INT-004", "W2INT-005"],
    "derived_from_question_ids": ["W2Q_VALIDATION_REPLAY", "W2Q_ML_FEATURE_LABEL_STORE_DOWNSTREAM"],
    "derived_from_source_gaps": [
        "WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl",
        "WAVE2_ALLOCATOR_WINDOW_SOURCE_COVERAGE_AUDIT.jsonl",
        "WAVE2_SLTP_MODIFY_LIFECYCLE_SOURCE_COVERAGE_LEDGER.jsonl",
        "WAVE2_PATH_REPAIR_SOURCE_COVERAGE_AUDIT.jsonl",
    ],
}


@dataclass(frozen=True)
class SourceSpec:
    source_key: str
    relative_path: str
    expected_rows: int
    source_role: str

    @property
    def path(self) -> Path:
        return Path(self.relative_path)


MATERIAL_SOURCE_SPECS: tuple[SourceSpec, ...] = (
    SourceSpec(
        "broker_trade_microscope",
        str(WAVE2_ROUTE / "WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl"),
        77,
        "broker_real_trade_truth_boundary",
    ),
    SourceSpec(
        "candidate_causal_microscope",
        str(WAVE2_ROUTE / "WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl"),
        13246,
        "candidate_and_live_authority_replay_boundary",
    ),
    SourceSpec(
        "allocator_decision_window_replay",
        str(WAVE2_ROUTE / "WAVE2_ALLOCATOR_DECISION_WINDOW_REPLAY_LEDGER.jsonl"),
        96,
        "allocator_window_replay_fixture",
    ),
    SourceSpec(
        "cost_source_coverage",
        str(WAVE2_ROUTE / "WAVE2_COST_SOURCE_COVERAGE_AUDIT.jsonl"),
        77,
        "broker_cost_boundary_fixture",
    ),
    SourceSpec(
        "final_say_selector_scheduler_join",
        str(WAVE2_ROUTE / "WAVE2_FINAL_SAY_SELECTOR_SCHEDULER_JOIN_LEDGER.jsonl"),
        12775,
        "final_say_runtime_authority_fixture",
    ),
    SourceSpec(
        "market_system_classification",
        str(WAVE2_ROUTE / "WAVE2_MARKET_SYSTEM_ROW_CLASSIFICATION_LEDGER.jsonl"),
        77,
        "market_vs_system_classification_fixture",
    ),
    SourceSpec(
        "pending_nofill_lifecycle",
        str(WAVE2_ROUTE / "WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl"),
        877,
        "pending_nofill_lifecycle_fixture",
    ),
    SourceSpec(
        "tick_repaired_first_passage",
        str(WAVE2_ROUTE / "WAVE2_TICK_REPAIRED_FIRST_PASSAGE_MFE_MAE_REVERSAL_LEDGER.jsonl"),
        55,
        "path_replay_proxy_fixture",
    ),
    SourceSpec(
        "zero_trade_counterfactual_path_rank",
        str(WAVE2_ROUTE / "WAVE2_ZERO_TRADE_COUNTERFACTUAL_PATH_RANK_LEDGER.jsonl"),
        416,
        "zero_trade_counterfactual_fixture",
    ),
)

SOURCE_GAP_SPECS: tuple[SourceSpec, ...] = (
    SourceSpec(
        "wave2_blocker_and_repair",
        str(WAVE2_ROUTE / "WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl"),
        43,
        "source_gap_and_capture_requirement",
    ),
    SourceSpec(
        "allocator_window_source_coverage",
        str(WAVE2_ROUTE / "WAVE2_ALLOCATOR_WINDOW_SOURCE_COVERAGE_AUDIT.jsonl"),
        6,
        "allocator_source_gap_boundary",
    ),
    SourceSpec(
        "sltp_modify_lifecycle_source_coverage",
        str(WAVE2_ROUTE / "WAVE2_SLTP_MODIFY_LIFECYCLE_SOURCE_COVERAGE_LEDGER.jsonl"),
        77,
        "sltp_lifecycle_source_gap_boundary",
    ),
    SourceSpec(
        "path_repair_source_coverage",
        str(WAVE2_ROUTE / "WAVE2_PATH_REPAIR_SOURCE_COVERAGE_AUDIT.jsonl"),
        8,
        "path_source_gap_boundary",
    ),
)

REQUIRED_JSON_INPUTS = (
    WAVE2_ROUTE / "WAVE2_DOWNSTREAM_OWNERSHIP_MAP.json",
    WAVE2_ROUTE / "WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json",
    WAVE2_ROUTE / "WAVE2_REPLAY_COMPRESSION_AND_PARTITION_PLAN.json",
    WAVE2_ROUTE / "WAVE2_FEATURE_LABEL_STORE_CONTRACT.json",
    WAVE2_ROUTE / "WAVE2_VALIDATION_ANTI_OVERFIT_CONTRACT.json",
    WAVE2_ROUTE / "WAVE2_WAVE4_WAVE5_ML_OWNERSHIP_CONTRACT.json",
    WAVE2_ROUTE / "WAVE2_MODEL_REGISTRY_AND_CHALLENGER_CONTRACT.json",
    WAVE2_ROUTE / "WAVE2_LONG_RUNNING_LOCAL_TRAINING_CONTRACT.json",
    WAVE2_ROUTE / "WAVE2_SAME_SYMBOL_LIFECYCLE_OWNERSHIP_CONTRACT.json",
    WAVE2_ROUTE / "WAVE2_PROBABILITY_DEBATE_ENGINE_CONTRACT.json",
    WAVE2_ROUTE / "WAVE2_FOLLOW_AVOID_MIXED_NUMERIC_CONFLUENCE_CONTRACT.json",
)

SEMANTIC_DEPENDENCIES = (
    {
        "dependency_id": "same_symbol_same_instrument_lifecycle_v4",
        "first_class_owner": "same_symbol_same_instrument_lifecycle_v4",
        "runner_contract": "partition rows carry symbol, side, broker-local namespace, source gap state, and no duplicate-exposure handoff fields",
        "handoff_status": "implemented_as_replay_handoff_not_lifecycle_authority",
        "required_terms": [
            "same-symbol lifecycle",
            "same-instrument lifecycle",
            "scale-in",
            "close/reverse",
            "ticket-bound state",
            "no duplicate exposure",
        ],
    },
    {
        "dependency_id": "probability_debate_team_engine_v4",
        "first_class_owner": "probability_debate_team_engine_v4",
        "runner_contract": "replay fixtures reserve numeric theses, EV, uncertainty, veto, calibration, and final-action slots without fabricating probabilities",
        "handoff_status": "bounded_capture_contract_for_probability_owner",
        "required_terms": [
            "calibrated probability",
            "long thesis",
            "short thesis",
            "no-trade thesis",
            "wait thesis",
            "scale thesis",
            "reduce thesis",
            "close thesis",
            "reverse thesis",
            "Brier",
            "ECE",
            "logloss",
        ],
    },
    {
        "dependency_id": "follow_avoid_mixed_numeric_confluence_v4",
        "first_class_owner": "follow_avoid_mixed_numeric_confluence_v4",
        "runner_contract": "feature contract requires direction, strength, confidence, reliability history, evidence class, freshness, cost sensitivity, conflict reason, and source completeness",
        "handoff_status": "bounded_capture_contract_for_numeric_confluence_owner",
        "required_terms": [
            "FOLLOW is not automatic trade permission",
            "AVOID invalidation type",
            "MIXED structured disagreement",
        ],
    },
    {
        "dependency_id": "ml_feature_label_store_digital_twin",
        "first_class_owner": "Wave4/Wave5 ML owners",
        "runner_contract": "feature and label store contracts separate broker-real cash, exact-R, proxy-R, replay, simulation, shadow, and prospective capture labels",
        "handoff_status": "implemented_as_feature_label_capture_contract",
        "required_terms": [
            "Feature Store",
            "Label Store",
            "Digital Twin",
            "ML baselines",
            "training workers",
            "walk-forward",
            "leakage guards",
            "model registry",
            "challenger ownership",
        ],
    },
    {
        "dependency_id": "dual_broker_no_copy_boundary",
        "first_class_owner": "dual_broker_runtime_contract",
        "runner_contract": "redacted_account broker-real labels remain in a redacted_account namespace and are never copied as FTMO lots, fills, cash, costs, specs, sessions, or lifecycle truth",
        "handoff_status": "implemented_as_broker_namespace_boundary",
        "required_terms": ["redacted_account local truth", "FTMO target-local truth", "no broker fact copy"],
    },
)

BASELINE_FIXTURES = (
    {
        "baseline_id": "session_only_control",
        "fixture_family": "adversarial_partition_control",
        "allowed_observation_fields": ["session_bucket"],
        "forbidden_label_fields": ["broker_real_cash", "exact_r", "proxy_r", "mfe_r", "mae_r"],
        "purpose": "detect whether a candidate replay is only rediscovering session exposure.",
    },
    {
        "baseline_id": "symbol_only_control",
        "fixture_family": "adversarial_partition_control",
        "allowed_observation_fields": ["symbol"],
        "forbidden_label_fields": ["broker_real_cash", "exact_r", "proxy_r", "mfe_r", "mae_r"],
        "purpose": "detect symbol concentration and GER30-like outlier dependence.",
    },
    {
        "baseline_id": "side_only_control",
        "fixture_family": "adversarial_partition_control",
        "allowed_observation_fields": ["side"],
        "forbidden_label_fields": ["broker_real_cash", "exact_r", "proxy_r", "mfe_r", "mae_r"],
        "purpose": "detect long/short imbalance masquerading as decision quality.",
    },
    {
        "baseline_id": "time_partition_shuffle_control",
        "fixture_family": "adversarial_randomization_control",
        "allowed_observation_fields": ["time_split_role", "symbol", "session_bucket"],
        "forbidden_label_fields": ["broker_real_cash", "exact_r", "proxy_r", "mfe_r", "mae_r"],
        "purpose": "shuffle decisions inside frozen time partitions without crossing as-of slices.",
    },
    {
        "baseline_id": "duplicate_source_key_collapse_control",
        "fixture_family": "duplicate_policy_control",
        "allowed_observation_fields": ["duplicate_source_row_key", "source_row_id"],
        "forbidden_label_fields": ["broker_real_cash", "exact_r", "proxy_r", "mfe_r", "mae_r"],
        "purpose": "prevent repeated runtime snapshots or candidate duplicates from inflating effective sample size.",
    },
    {
        "baseline_id": "cost_swap_slippage_stress_control",
        "fixture_family": "execution_cost_stress",
        "allowed_observation_fields": ["symbol", "source_completeness_status", "broker_namespace"],
        "forbidden_label_fields": ["broker_real_cash", "exact_r", "proxy_r", "mfe_r", "mae_r"],
        "purpose": "reserve deterministic cost stress before any broker-net expectancy claim.",
    },
    {
        "baseline_id": "ger30_outlier_removed_control",
        "fixture_family": "concentration_stress",
        "allowed_observation_fields": ["symbol", "time_split_role"],
        "forbidden_label_fields": ["broker_real_cash", "exact_r", "proxy_r", "mfe_r", "mae_r"],
        "purpose": "force every replay summary to survive the known largest-winner sensitivity.",
    },
    {
        "baseline_id": "zero_trade_reject_counterfactual_control",
        "fixture_family": "opportunity_cost_control",
        "allowed_observation_fields": ["source_family", "candidate_status", "symbol", "side"],
        "forbidden_label_fields": ["broker_real_cash", "exact_r", "proxy_r", "mfe_r", "mae_r"],
        "purpose": "keep zero-trade, rejected, and skipped alternatives in the replay denominator.",
    },
    {
        "baseline_id": "missing_source_penalty_control",
        "fixture_family": "source_completeness_control",
        "allowed_observation_fields": ["source_completeness_status", "missing_field_count", "source_gap_status"],
        "forbidden_label_fields": ["broker_real_cash", "exact_r", "proxy_r", "mfe_r", "mae_r"],
        "purpose": "make missing-source penalties explicit instead of letting gaps silently help a model.",
    },
    {
        "baseline_id": "stale_thesis_time_decay_control",
        "fixture_family": "lifecycle_time_control",
        "allowed_observation_fields": ["canonical_time_utc", "session_bucket", "source_family"],
        "forbidden_label_fields": ["broker_real_cash", "exact_r", "proxy_r", "mfe_r", "mae_r"],
        "purpose": "test whether stale-thesis and time-in-trade behavior dominate replay outcomes.",
    },
    {
        "baseline_id": "market_vs_system_classification_control",
        "fixture_family": "failure_anatomy_control",
        "allowed_observation_fields": ["market_vs_system_disposition", "symbol", "session_bucket"],
        "forbidden_label_fields": ["broker_real_cash", "exact_r", "proxy_r", "mfe_r", "mae_r"],
        "purpose": "separate bad-market from bad-system labels before training or promotion gates.",
    },
    {
        "baseline_id": "current_gtos_no_api_replay_control",
        "fixture_family": "current_system_comparator",
        "allowed_observation_fields": ["source_family", "v4_requirement_id", "evidence_class", "source_completeness_status"],
        "forbidden_label_fields": ["broker_real_cash", "exact_r", "proxy_r", "mfe_r", "mae_r"],
        "purpose": "keep current GTOS behavior as a deterministic comparator without paid AI calls.",
    },
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_no} expected object row")
            yield row


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    return count


def git_value(repo_root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _string(value: Any) -> str:
    return str(value or "").strip()


def parse_time(value: Any) -> datetime | None:
    if isinstance(value, dict):
        for key in (
            "decision_time_utc",
            "window_time_utc",
            "entry_time_utc",
            "candle_time_utc",
            "candle_close_time_utc",
            "last_time_utc",
        ):
            parsed = parse_time(value.get(key))
            if parsed is not None:
                return parsed
        return None
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def canonical_time(row: Mapping[str, Any]) -> datetime | None:
    for key in (
        "time_window",
        "window_time_utc",
        "entry_time_utc",
        "decision_time_utc",
        "candidate_time_utc",
        "candle_time_utc",
        "candle_close_time_utc",
        "time_utc",
        "timestamp_utc",
        "created_at_utc",
    ):
        parsed = parse_time(row.get(key))
        if parsed is not None:
            return parsed
    return None


def session_bucket(value: datetime | None) -> str:
    if value is None:
        return "session_unknown_clock_gap"
    hour = value.hour
    if 0 <= hour < 7:
        return "tokyo_broad"
    if 7 <= hour < 13:
        return "london_broad"
    if 13 <= hour < 18:
        return "ny_broad"
    return "off_kz_broad"


def source_row_id(row: Mapping[str, Any], fallback: str) -> str:
    for key in (
        "row_id",
        "candidate_id",
        "broker_position_id",
        "inferred_window_id",
        "source_row_id",
        "position_id",
        "ticket",
    ):
        value = row.get(key)
        if value not in (None, "", [], {}):
            return str(value)
    return fallback


def extract_symbol(row: Mapping[str, Any]) -> str:
    for key in ("symbol", "source_symbol", "instrument", "broker_symbol", "mt5_symbol"):
        value = row.get(key)
        if value not in (None, "", [], {}):
            return str(value)
    symbols = row.get("symbols")
    if isinstance(symbols, list) and symbols:
        return str(symbols[0])
    return "UNKNOWN_SYMBOL"


def extract_side(row: Mapping[str, Any]) -> str:
    for key in ("side", "direction", "requested_side"):
        value = row.get(key)
        if value not in (None, "", [], {}):
            return str(value).upper()
    sides = row.get("sides")
    if isinstance(sides, list) and sides:
        return str(sides[0]).upper()
    return "UNKNOWN_SIDE"


def source_completeness_status(row: Mapping[str, Any]) -> str:
    missing = _as_list(row.get("missing_fields")) + _as_list(row.get("missing_runtime_truth"))
    status_blob = " ".join(
        _string(row.get(key))
        for key in ("status", "coverage_status", "source_completeness_state", "result_use_status")
    ).casefold()
    if missing:
        return "source_gap_present"
    if "gap" in status_blob or "missing" in status_blob or "incomplete" in status_blob:
        return "source_gap_present"
    if "partial" in status_blob:
        return "partial_source_coverage"
    return "source_complete_or_not_materially_gapped"


def broker_namespace(row: Mapping[str, Any]) -> str:
    text = json.dumps(row, sort_keys=True, default=str).casefold()
    if "ftmo" in text:
        return "FTMO_target_local_truth_required"
    if "redacted_account" in text or "broker_real" in text or "broker-real" in text:
        return "redacted_account_local_truth"
    return "broker_namespace_not_applicable_or_unknown"


def evidence_boundary(row: Mapping[str, Any]) -> dict[str, Any]:
    evidence_class = _string(row.get("evidence_class"))
    metric_fields = row.get("metric_fields_used") if isinstance(row.get("metric_fields_used"), dict) else {}
    text = f"{evidence_class} {json.dumps(metric_fields, sort_keys=True, default=str)}".casefold()
    return {
        "evidence_class": evidence_class or "unspecified_evidence_class",
        "broker_real_label_available": any(token in text for token in ("broker-real", "broker_real", "broker truth", "broker_truth")),
        "exact_r_label_available": "exact_r" in text and "null" not in text,
        "proxy_r_label_available": "proxy_r" in text,
        "replay_or_shadow_label_available": any(token in text for token in ("replay", "shadow", "simulation")),
        "label_use_boundary": "label_available_only_after downstream lane permits that evidence class",
    }


def contamination_status(entry: Mapping[str, Any]) -> str:
    row = entry["row"]
    source_key = str(entry["source_key"])
    evidence = evidence_boundary(row)
    if evidence["broker_real_label_available"] or source_key in {
        "broker_trade_microscope",
        "cost_source_coverage",
        "market_system_classification",
    }:
        return "contaminated_for_performance_validation_broker_outcomes_visible"
    if evidence["exact_r_label_available"] or evidence["proxy_r_label_available"]:
        return "contaminated_for_performance_validation_replay_or_proxy_labels_visible"
    if source_completeness_status(row) != "source_complete_or_not_materially_gapped":
        return "source_gap_slice_no_label_imputation_allowed"
    return "asof_fixture_no_result_scored"


def load_source_entries(
    repo_root: Path,
    specs: Sequence[SourceSpec] = MATERIAL_SOURCE_SPECS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    entries: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    for spec in specs:
        path = repo_root / spec.path
        rows = list(iter_jsonl(path))
        if len(rows) != spec.expected_rows:
            raise ValueError(
                f"{spec.relative_path} expected {spec.expected_rows} rows, found {len(rows)}"
            )
        source_hash = sha256_file(path)
        inventory.append(
            {
                "schema_version": "wave3_historical_replay_source_inventory_v1",
                "source_key": spec.source_key,
                "source_role": spec.source_role,
                "path": spec.relative_path,
                "sha256": source_hash,
                "row_count": len(rows),
                "expected_rows": spec.expected_rows,
                "row_count_status": "matches_expected",
            }
        )
        for index, row in enumerate(rows, start=1):
            entries.append(
                {
                    "source_key": spec.source_key,
                    "source_role": spec.source_role,
                    "source_path": spec.relative_path,
                    "source_sha256": source_hash,
                    "source_row_index": index,
                    "source_row_id": source_row_id(row, f"{spec.source_key}:{index:06d}"),
                    "row": row,
                    "clock": canonical_time(row),
                }
            )
    return entries, inventory


def time_split_assignments(entries: Sequence[Mapping[str, Any]]) -> dict[tuple[str, int], str]:
    valid = sorted(
        [entry for entry in entries if entry.get("clock") is not None],
        key=lambda item: (
            item["clock"],
            str(item.get("source_key")),
            int(item.get("source_row_index") or 0),
            str(item.get("source_row_id")),
        ),
    )
    assignments: dict[tuple[str, int], str] = {}
    if not valid:
        return assignments
    cut_1 = int(len(valid) * 0.60)
    cut_2 = int(len(valid) * 0.80)
    for index, entry in enumerate(valid):
        if index < cut_1:
            role = "discovery_train_partition_frozen"
        elif index < cut_2:
            role = "development_walk_forward_partition_frozen"
        else:
            role = "sealed_holdout_partition_frozen_no_result_scored"
        assignments[(str(entry["source_key"]), int(entry["source_row_index"]))] = role
    return assignments


def partition_row(entry: Mapping[str, Any], time_role: str) -> dict[str, Any]:
    row = entry["row"]
    clock = entry.get("clock")
    symbol = extract_symbol(row)
    side = extract_side(row)
    source_key = str(entry["source_key"])
    missing = _as_list(row.get("missing_fields")) + _as_list(row.get("missing_runtime_truth"))
    boundary = evidence_boundary(row)
    duplicate_key = _string(row.get("duplicate_source_row_key")) or _string(row.get("candidate_id")) or _string(entry["source_row_id"])
    is_ger_outlier_symbol = symbol.upper() in {"GER30", "GER40"}
    zero_trade_eligible = source_key == "zero_trade_counterfactual_path_rank" or "ZERO_TRADE" in json.dumps(row, default=str).upper()
    return {
        "schema_version": "wave3_historical_replay_partition_contamination_v1",
        "row_id": f"partition:{source_key}:{int(entry['source_row_index']):06d}:{stable_hash(entry['source_row_id'])[:12]}",
        "lane": LANE,
        "material_row_preserved": True,
        "source_key": source_key,
        "source_role": entry["source_role"],
        "source_path": entry["source_path"],
        "source_sha256": entry["source_sha256"],
        "source_row_index": entry["source_row_index"],
        "source_row_id": entry["source_row_id"],
        "source_row_hash": stable_hash(row),
        "canonical_time_utc": clock.isoformat() if isinstance(clock, datetime) else None,
        "clock_status": "asof_clock_available" if isinstance(clock, datetime) else "clock_source_gap",
        "symbol": symbol,
        "side": side,
        "session_bucket": session_bucket(clock if isinstance(clock, datetime) else None),
        "time_split_role": time_role,
        "leave_one_symbol_out_key": symbol,
        "leave_one_session_out_key": session_bucket(clock if isinstance(clock, datetime) else None),
        "leave_one_side_out_key": side,
        "cost_swap_stress_partition": "cost_stress_required",
        "ger30_outlier_partition": "ger30_or_ger40_outlier_slice" if is_ger_outlier_symbol else "non_ger_outlier_slice",
        "zero_trade_counterfactual_partition": "zero_trade_or_reject_slice" if zero_trade_eligible else "normal_candidate_or_trade_slice",
        "duplicate_policy_key": duplicate_key,
        "source_completeness_status": source_completeness_status(row),
        "missing_field_count": len(missing),
        "missing_fields_or_runtime_truth": [str(item) for item in missing],
        "contamination_status": contamination_status(entry),
        "broker_namespace": broker_namespace(row),
        "broker_real_boundary_status": (
            "broker_real_label_stays_source_broker_local"
            if boundary["broker_real_label_available"]
            else "no_broker_real_label_in_observation"
        ),
        "label_boundary": boundary,
        "result_use_status": "partition_fixture_no_replay_score_no_validation_result",
    }


def no_api_policy_record() -> dict[str, Any]:
    decision = evaluate_ai_call_policy(
        config={
            "market": {"symbol": "MULTI"},
            "ai": {"primary_model": "claude-sonnet-4-6"},
            "ai_call_policy": {
                "enabled": True,
                "apply_to_ai_call": True,
                "production_purposes": ["production_trade_decision", "ai_reliability_smoke"],
                "research_ai_purposes": [
                    "ai_decision_value_audit",
                    "ai_delta_audit",
                    "ai_reliability_audit",
                    "prompt_model_regression",
                ],
                "no_api_contexts": [
                    "historical_replay",
                    "market_edge_replay",
                    "mechanical_replay",
                    "goal_session_projection",
                    "research_market_edge",
                    "missed_opportunity_inventory",
                ],
            },
        },
        context={
            "purpose": "market_edge_replay",
            "runtime_context": "historical_replay",
            "source_universe_kind": "mechanical_replay",
        },
        model="claude-sonnet-4-6",
    )
    return decision.to_record()


def replay_event_row(entry: Mapping[str, Any], partition: Mapping[str, Any], no_api: Mapping[str, Any]) -> dict[str, Any]:
    row = entry["row"]
    boundary = evidence_boundary(row)
    return {
        "schema_version": "wave3_historical_replay_event_fixture_v1",
        "row_id": f"replay_event:{entry['source_key']}:{int(entry['source_row_index']):06d}:{stable_hash(entry['source_row_id'])[:12]}",
        "lane": LANE,
        "source_key": entry["source_key"],
        "source_path": entry["source_path"],
        "source_sha256": entry["source_sha256"],
        "source_row_index": entry["source_row_index"],
        "source_row_id": entry["source_row_id"],
        "partition_row_id": partition["row_id"],
        "canonical_time_utc": partition["canonical_time_utc"],
        "symbol": partition["symbol"],
        "side": partition["side"],
        "session_bucket": partition["session_bucket"],
        "replay_mode": "deterministic_no_api_digital_twin_fixture",
        "observation_projection": {
            "symbol": partition["symbol"],
            "side": partition["side"],
            "session_bucket": partition["session_bucket"],
            "source_key": entry["source_key"],
            "source_role": entry["source_role"],
            "source_completeness_status": partition["source_completeness_status"],
            "evidence_class": boundary["evidence_class"],
            "time_split_role": partition["time_split_role"],
        },
        "forbidden_observation_fields": [
            "broker_real_cash",
            "broker_real_pnl_cash",
            "broker_net_cash",
            "commission_cash",
            "swap_cash",
            "exact_r",
            "proxy_r",
            "mfe_r",
            "mae_r",
            "future_path_outcome",
            "post_exit_outcome",
        ],
        "action_space_contract": [
            "long",
            "short",
            "no_trade",
            "wait",
            "scale",
            "reduce",
            "close",
            "reverse",
        ],
        "same_symbol_lifecycle_handoff_required": True,
        "probability_debate_handoff_required": True,
        "numeric_confluence_handoff_required": True,
        "feature_label_store_handoff_required": True,
        "no_api_policy_action": no_api["action"],
        "no_api_policy_allowed": no_api["allowed"],
        "no_api_policy_reason": no_api["reason"],
        "label_boundary": boundary,
        "result_use_status": "no_score_no_validation_result_partition_fixture_only",
    }


def source_gap_rows(repo_root: Path) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for spec in SOURCE_GAP_SPECS:
        path = repo_root / spec.path
        rows = list(iter_jsonl(path))
        if len(rows) != spec.expected_rows:
            raise ValueError(f"{spec.relative_path} expected {spec.expected_rows} rows, found {len(rows)}")
        for index, row in enumerate(rows, start=1):
            rows_out.append(
                {
                    "schema_version": "wave3_historical_replay_source_gap_v1",
                    "row_id": f"source_gap:{spec.source_key}:{index:04d}",
                    "lane": LANE,
                    "source_key": spec.source_key,
                    "source_role": spec.source_role,
                    "source_path": spec.relative_path,
                    "source_sha256": sha256_file(path),
                    "source_row_index": index,
                    "source_row_id": source_row_id(row, f"{spec.source_key}:{index:04d}"),
                    "source_gap_status": source_completeness_status(row),
                    "missing_file_path_field_source": row.get("missing_file_path_field_source")
                    or row.get("missing_source")
                    or row.get("missing_runtime_truth")
                    or row.get("missing_fields"),
                    "repair_or_capture_requirement": row.get("owner_access_source_capture_requirement")
                    or row.get("repair_requirement")
                    or row.get("capture_requirement")
                    or "preserve exact source gap until owner lane captures the field",
                    "result_use_status": "source_gap_boundary_no_label_imputation",
                    "original_status": row.get("status") or row.get("coverage_status"),
                }
            )
    return rows_out


def baseline_fixture_rows(partitions: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts_by_source = Counter(str(row["source_key"]) for row in partitions)
    counts_by_symbol = Counter(str(row["symbol"]) for row in partitions)
    counts_by_session = Counter(str(row["session_bucket"]) for row in partitions)
    counts_by_time_role = Counter(str(row["time_split_role"]) for row in partitions)
    rows: list[dict[str, Any]] = []
    for fixture in BASELINE_FIXTURES:
        applies = applies_to_fixture(fixture["baseline_id"], partitions)
        rows.append(
            {
                "schema_version": "wave3_historical_replay_adversarial_baseline_fixture_v1",
                "row_id": f"baseline_fixture:{fixture['baseline_id']}",
                "lane": LANE,
                **fixture,
                "applies_to_material_row_count": len(applies),
                "applies_to_source_keys": sorted({str(row["source_key"]) for row in applies}),
                "full_source_row_counts": dict(sorted(counts_by_source.items())),
                "full_symbol_count": len(counts_by_symbol),
                "full_session_counts": dict(sorted(counts_by_session.items())),
                "full_time_split_counts": dict(sorted(counts_by_time_role.items())),
                "selection_status": "fixture_preserves_full_ledger_counts_no_top_n_truncation",
                "result_use_status": "adversarial_fixture_not_performance_result",
            }
        )
    return rows


def applies_to_fixture(baseline_id: str, partitions: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    if baseline_id == "ger30_outlier_removed_control":
        return [row for row in partitions if row["ger30_outlier_partition"] == "non_ger_outlier_slice"]
    if baseline_id == "zero_trade_reject_counterfactual_control":
        return [row for row in partitions if row["zero_trade_counterfactual_partition"] == "zero_trade_or_reject_slice"]
    if baseline_id == "cost_swap_slippage_stress_control":
        return [row for row in partitions if row["cost_swap_stress_partition"] == "cost_stress_required"]
    if baseline_id == "missing_source_penalty_control":
        return [row for row in partitions if row["source_completeness_status"] != "source_complete_or_not_materially_gapped"]
    if baseline_id == "market_vs_system_classification_control":
        return [row for row in partitions if row["source_key"] == "market_system_classification"]
    return list(partitions)


def semantic_ownership_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dependency in SEMANTIC_DEPENDENCIES:
        rows.append(
            {
                "schema_version": "wave3_historical_replay_semantic_ownership_v1",
                "row_id": f"semantic_dependency:{dependency['dependency_id']}",
                "lane": LANE,
                **dependency,
                "source_paths": [
                    str(WAVE2_ROUTE / "WAVE2_DOWNSTREAM_OWNERSHIP_MAP.json"),
                    str(WAVE2_ROUTE / "WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json"),
                ],
                "result_use_status": "semantic_contract_preserved_or_handed_to_first_class_owner",
            }
        )
    return rows


def feature_label_capture_contract() -> dict[str, Any]:
    return {
        "schema_version": "wave3_historical_replay_feature_label_capture_contract_v1",
        "lane": LANE,
        "status": "materialized_default_off_contract",
        "boundary_status": BOUNDARY_STATUS,
        "feature_store_required_fields": [
            "feature_namespace",
            "feature_version",
            "asof_timestamp_utc",
            "source_path",
            "source_sha256",
            "source_row_id",
            "source_completeness_status",
            "freshness_status",
            "evidence_class",
            "broker_namespace",
            "instrument_alias_mapping",
            "no_leak_guard_status",
        ],
        "label_store_required_fields": [
            "label_namespace",
            "label_evidence_class",
            "broker_real_cash_label",
            "exact_r_label",
            "proxy_r_label",
            "mfe_label",
            "mae_label",
            "time_to_profit_label",
            "time_to_destination_label",
            "giveback_label",
            "stale_thesis_label",
            "stop_target_efficiency_label",
            "harvest_failure_label",
            "opportunity_cost_label",
        ],
        "strict_boundaries": [
            "labels are never projected into replay observations",
            "broker-real labels remain broker-local and source-bound",
            "proxy and replay labels are not broker-real cash evidence",
            "missing historical intent or lifecycle truth is a capture requirement, not an inferred label",
            "FTMO target-broker truth must be captured locally and cannot inherit redacted_account facts",
            "paid AI samples require a separate manifest, budget, owner approval, and cache identity",
        ],
        "calibration_metric_requirements_for_downstream_ml": [
            "Brier",
            "ECE",
            "reliability_bins",
            "logloss",
            "calibration_slope",
            "profit_weighted_calibration",
        ],
        "result_use_status": "capture_contract_not_validation_or_model_result",
    }


def production_disposition_rows() -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "wave3_historical_replay_production_disposition_v1",
            "row_id": "production_disposition:src_research_historical_replay_digital_twin_v4",
            "component": "src/research/historical_replay_digital_twin_v4.py",
            "production_code_disposition": "staged_default_off",
            "runtime_effect_status": "no_runtime_effect_without_explicit_config_and_owner_lane",
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "remote_push": False,
            "reason": "provides deterministic replay fixture builder and verifier only",
        },
        {
            "schema_version": "wave3_historical_replay_production_disposition_v1",
            "row_id": "production_disposition:config_agent_config_yaml",
            "component": "config/agent_config.yaml",
            "production_code_disposition": "staged_default_off",
            "runtime_effect_status": "default_off_replay_config_no_runtime_mutation",
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "remote_push": False,
            "reason": "declares route-owned no-API replay defaults and artifact paths",
        },
        {
            "schema_version": "wave3_historical_replay_production_disposition_v1",
            "row_id": "production_disposition:route_artifacts_tests_verifier",
            "component": str(ROUTE_DIR),
            "production_code_disposition": "active_route_evidence",
            "runtime_effect_status": "artifact_generation_and_verification_only",
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "remote_push": False,
            "reason": "route materialization, focused tests, verifier, and completion audit",
        },
    ]


def searched_root_rows(repo_root: Path) -> list[dict[str, Any]]:
    roots = [
        (".context core context", ".context/00_core"),
        ("current worktree src", "src"),
        ("current worktree config", "config"),
        ("current worktree tests", "tests"),
        ("Wave2 route", str(WAVE2_ROUTE)),
        ("Wave1 hard-halt route", "research/operations/final_moonshot_wave1a_hard_halt_forensic_matrix_2026_06_04"),
        ("shadow log pointers", "shadow_logs"),
        ("pipeline state", "pipeline_state"),
        ("Mac GTOS package root", "/Users/borr/Documents/gtos/packages"),
    ]
    rows = []
    for index, (label, root) in enumerate(roots, start=1):
        path = Path(root)
        exists = path.exists() if path.is_absolute() else (repo_root / path).exists()
        rows.append(
            {
                "schema_version": "wave3_historical_replay_searched_root_v1",
                "row_id": f"searched_root:{index:03d}",
                "lane": LANE,
                "search_label": label,
                "path": root,
                "exists": exists,
                "search_status": "searched_or_inventory_checked" if exists else "not_present_in_current_local_root",
                "result_use_status": "source_discovery_context_not_label",
            }
        )
    return rows


def route_decision_rows(total_rows: int) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "wave3_historical_replay_route_decision_v1",
            "row_id": "decision:build_no_api_digital_twin_runner",
            "decision": "IMPLEMENT_STAGED_DEFAULT_OFF_NO_API_REPLAY_DIGITAL_TWIN_FIXTURES",
            "rationale": f"materialized {total_rows} material source rows into replay and partition fixtures",
            "boundary_status": BOUNDARY_STATUS,
        },
        {
            "schema_version": "wave3_historical_replay_route_decision_v1",
            "row_id": "decision:do_not_score_validation_or_broker_outcomes",
            "decision": "FREEZE_PARTITIONS_AND_FIXTURES_WITHOUT_RESULT_SCORING",
            "rationale": "this lane owns replay infrastructure and contamination ledgers; validation anti-overfit owns scoring gates",
            "boundary_status": BOUNDARY_STATUS,
        },
        {
            "schema_version": "wave3_historical_replay_route_decision_v1",
            "row_id": "decision:preserve_broker_local_boundaries",
            "decision": "KEEP_redacted_account_AND_FTMO_TRUTH_NAMESPACES_SEPARATE",
            "rationale": "broker-real redacted_account labels are source-bound only and never copied into FTMO target truth",
            "boundary_status": BOUNDARY_STATUS,
        },
    ]


def instruction_coverage_checklist() -> dict[str, Any]:
    return {
        "schema_version": "wave3_historical_replay_instruction_coverage_v1",
        "lane": LANE,
        "goal_session_research_discipline_read_after_preflight": True,
        "research_operating_doctrine_read_after_preflight": True,
        "builder_or_audit_posture": "builder_repair_replay_production_code_integration",
        "anti_boxing_questions_pursued": [
            "what replayable market/path/cost evidence exists versus non-generatable historical GTOS intent",
            "which partitions can be frozen now without opening result scoring",
            "which source gaps must become forward capture fields",
            "which adversarial controls prevent symbol/session/side/outlier/cost/source-gap overfit",
        ],
        "outside_current_edge_mechanisms_considered": [
            "time-compressed replay",
            "duplicate-key collapse",
            "missing-source penalty",
            "GER30 largest-winner outlier removal",
            "zero-trade and rejected alternative denominator preservation",
            "probability calibration handoff",
            "feature and label store separation",
        ],
        "proof_or_impossibility_stop_condition": (
            "all Wave2 material source rows are either materialized into partition/replay fixtures "
            "or exact source-gap rows; no validation score is opened"
        ),
        "doctrine_requirements_not_answered_because_cross_boundary": [
            "sealed performance validation is owned by validation_anti_overfit_v4",
            "model training and challenger promotion are owned by Wave5 ML lanes",
            "live deployment and broker mutation require separate owner approval",
        ],
    }


def context_anchor(repo_root: Path, inventory: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "wave3_historical_replay_context_anchor_v1",
        "lane": LANE,
        "created_at_utc": utc_now(),
        "prompt_path": str(PROMPT_PATH),
        "starter_path": str(STARTER_PATH),
        "route_dir": str(ROUTE_DIR),
        "branch": git_value(repo_root, "branch", "--show-current"),
        "head": git_value(repo_root, "rev-parse", "HEAD"),
        "main": git_value(repo_root, "rev-parse", "main"),
        "origin_main": git_value(repo_root, "rev-parse", "origin/main"),
        "git_status_short": git_value(repo_root, "status", "--short"),
        "boundary_status": BOUNDARY_STATUS,
        "provenance": PROVENANCE,
        "material_source_count": len(inventory),
        "material_source_rows_total": sum(int(row["row_count"]) for row in inventory),
        "context_use": {
            "changed_work": [
                "doctrine forced all material rows into ledgers before summaries",
                "AI cost-control doctrine forced SKIP_AI_NO_API_REPLAY enforcement",
                "semantic repair contract forced lifecycle/probability/FAM/ML handoff rows",
                "hard-halt truth forced broker-local label boundaries and contamination status",
            ],
            "irrelevant_context_quarantined": [
                "old pre-halt first-fill framing",
                "storage constraint psychology",
                "stale Windows launch paths",
                "old fixed 1.5R authority language",
            ],
        },
    }


def build_artifacts(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    entries, inventory = load_source_entries(repo_root)
    no_api = no_api_policy_record()
    assignments = time_split_assignments(entries)

    partitions: list[dict[str, Any]] = []
    replay_events: list[dict[str, Any]] = []
    for entry in entries:
        key = (str(entry["source_key"]), int(entry["source_row_index"]))
        time_role = assignments.get(key, "clock_source_gap_partition")
        p_row = partition_row(entry, time_role)
        partitions.append(p_row)
        replay_events.append(replay_event_row(entry, p_row, no_api))

    route_dir_abs = repo_root / route_dir
    route_dir_abs.mkdir(parents=True, exist_ok=True)

    artifact_rows = {
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_SOURCE_INPUT_INVENTORY.jsonl": inventory,
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_PARTITION_CONTAMINATION_LEDGER.jsonl": partitions,
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_REPLAY_EVENT_LEDGER.jsonl": replay_events,
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_SOURCE_GAP_LEDGER.jsonl": source_gap_rows(repo_root),
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_ADVERSARIAL_BASELINE_FIXTURES.jsonl": baseline_fixture_rows(partitions),
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_SEMANTIC_OWNERSHIP_LEDGER.jsonl": semantic_ownership_rows(),
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_PRODUCTION_DISPOSITION_LEDGER.jsonl": production_disposition_rows(),
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_SEARCHED_ROOT_LEDGER.jsonl": searched_root_rows(repo_root),
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_ROUTE_DECISION_LEDGER.jsonl": route_decision_rows(len(entries)),
    }
    written: dict[str, int] = {}
    for filename, rows in artifact_rows.items():
        written[filename] = write_jsonl(route_dir_abs / filename, rows)

    json_artifacts = {
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_CONTEXT_ANCHOR.json": context_anchor(repo_root, inventory),
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_FEATURE_LABEL_CAPTURE_CONTRACT.json": feature_label_capture_contract(),
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_INSTRUCTION_COVERAGE_CHECKLIST.json": instruction_coverage_checklist(),
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_RUNNER_SUMMARY.json": runner_summary(
            entries,
            partitions,
            replay_events,
            artifact_rows["WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_SOURCE_GAP_LEDGER.jsonl"],
            no_api,
        ),
    }
    for filename, payload in json_artifacts.items():
        write_json(route_dir_abs / filename, payload)

    manifest = output_manifest(repo_root, route_dir_abs)
    write_json(route_dir_abs / "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_OUTPUT_MANIFEST.json", manifest)
    return {
        "route_dir": str(route_dir),
        "material_rows": len(entries),
        "partition_rows": len(partitions),
        "replay_event_rows": len(replay_events),
        "jsonl_written": written,
        "no_api_policy": no_api,
        "manifest_file_count": manifest["file_count"],
    }


def runner_summary(
    entries: Sequence[Mapping[str, Any]],
    partitions: Sequence[Mapping[str, Any]],
    replay_events: Sequence[Mapping[str, Any]],
    gap_rows: Sequence[Mapping[str, Any]],
    no_api: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "wave3_historical_replay_runner_summary_v1",
        "lane": LANE,
        "created_at_utc": utc_now(),
        "status": "runner_materialized",
        "boundary_status": BOUNDARY_STATUS,
        "no_api_policy": no_api,
        "material_rows": len(entries),
        "partition_rows": len(partitions),
        "replay_event_rows": len(replay_events),
        "source_gap_rows": len(gap_rows),
        "source_counts": dict(sorted(Counter(str(row["source_key"]) for row in partitions).items())),
        "contamination_counts": dict(sorted(Counter(str(row["contamination_status"]) for row in partitions).items())),
        "time_split_counts": dict(sorted(Counter(str(row["time_split_role"]) for row in partitions).items())),
        "source_completeness_counts": dict(sorted(Counter(str(row["source_completeness_status"]) for row in partitions).items())),
        "broker_namespace_counts": dict(sorted(Counter(str(row["broker_namespace"]) for row in partitions).items())),
        "semantic_dependency_count": len(SEMANTIC_DEPENDENCIES),
        "baseline_fixture_count": len(BASELINE_FIXTURES),
        "result_use_status": "no_api_replay_infrastructure_not_validation_result",
    }


def output_manifest(repo_root: Path, route_dir_abs: Path) -> dict[str, Any]:
    files = []
    for path in sorted(route_dir_abs.iterdir()):
        if not path.is_file() or path.name == "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_OUTPUT_MANIFEST.json":
            continue
        rel = path.relative_to(repo_root).as_posix()
        row: dict[str, Any] = {
            "path": rel,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        if path.suffix == ".jsonl":
            row["jsonl_rows"] = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        files.append(row)
    return {
        "schema_version": "wave3_historical_replay_output_manifest_v1",
        "generated_at_utc": utc_now(),
        "lane": LANE,
        "file_count": len(files),
        "files": files,
        "manifest_self_excluded_from_hash_list": True,
        "boundary_status": BOUNDARY_STATUS,
    }


def verify_route(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    route_dir_abs = repo_root / route_dir
    checks: list[dict[str, Any]] = []

    def add_check(name: str, passed: bool, evidence: Mapping[str, Any] | None = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "evidence": dict(evidence or {})})

    required_files = [
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_CONTEXT_ANCHOR.json",
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_SOURCE_INPUT_INVENTORY.jsonl",
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_PARTITION_CONTAMINATION_LEDGER.jsonl",
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_REPLAY_EVENT_LEDGER.jsonl",
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_SOURCE_GAP_LEDGER.jsonl",
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_ADVERSARIAL_BASELINE_FIXTURES.jsonl",
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_SEMANTIC_OWNERSHIP_LEDGER.jsonl",
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_FEATURE_LABEL_CAPTURE_CONTRACT.json",
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_PRODUCTION_DISPOSITION_LEDGER.jsonl",
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_ROUTE_DECISION_LEDGER.jsonl",
        "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_OUTPUT_MANIFEST.json",
    ]
    for filename in required_files:
        add_check(f"exists:{filename}", (route_dir_abs / filename).exists())

    json_parse_errors: list[str] = []
    jsonl_counts: dict[str, int] = {}
    for path in sorted(route_dir_abs.glob("*.json")):
        try:
            load_json(path)
        except Exception as exc:  # noqa: BLE001
            json_parse_errors.append(f"{path.name}:{exc}")
    for path in sorted(route_dir_abs.glob("*.jsonl")):
        try:
            rows = list(iter_jsonl(path))
        except Exception as exc:  # noqa: BLE001
            json_parse_errors.append(f"{path.name}:{exc}")
            rows = []
        jsonl_counts[path.name] = len(rows)
    add_check("all_json_and_jsonl_parse", not json_parse_errors, {"errors": json_parse_errors})

    expected_material = sum(spec.expected_rows for spec in MATERIAL_SOURCE_SPECS)
    expected_gaps = sum(spec.expected_rows for spec in SOURCE_GAP_SPECS)
    partition_rows = list(iter_jsonl(route_dir_abs / "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_PARTITION_CONTAMINATION_LEDGER.jsonl"))
    replay_rows = list(iter_jsonl(route_dir_abs / "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_REPLAY_EVENT_LEDGER.jsonl"))
    source_gap_count = jsonl_counts.get("WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_SOURCE_GAP_LEDGER.jsonl", 0)
    add_check("all_material_rows_partitioned", len(partition_rows) == expected_material, {"actual": len(partition_rows), "expected": expected_material})
    add_check("all_material_rows_have_replay_events", len(replay_rows) == expected_material, {"actual": len(replay_rows), "expected": expected_material})
    add_check("all_source_gap_rows_materialized", source_gap_count == expected_gaps, {"actual": source_gap_count, "expected": expected_gaps})

    source_counts = Counter(row["source_key"] for row in partition_rows)
    add_check(
        "material_source_counts_match_contract",
        all(source_counts[spec.source_key] == spec.expected_rows for spec in MATERIAL_SOURCE_SPECS),
        {"actual": dict(sorted(source_counts.items()))},
    )
    contamination_counts = Counter(row["contamination_status"] for row in partition_rows)
    add_check(
        "contamination_slices_present",
        bool(contamination_counts),
        {"counts": dict(sorted(contamination_counts.items()))},
    )
    time_roles = Counter(row["time_split_role"] for row in partition_rows)
    add_check(
        "asof_partitions_present",
        {"discovery_train_partition_frozen", "development_walk_forward_partition_frozen", "sealed_holdout_partition_frozen_no_result_scored"}.issubset(time_roles),
        {"counts": dict(sorted(time_roles.items()))},
    )
    no_api_actions = Counter(row["no_api_policy_action"] for row in replay_rows)
    add_check(
        "no_api_replay_policy_enforced",
        set(no_api_actions) == {"SKIP_AI_NO_API_REPLAY"},
        {"actions": dict(no_api_actions)},
    )
    add_check(
        "replay_events_no_score",
        all(row["result_use_status"] == "no_score_no_validation_result_partition_fixture_only" for row in replay_rows),
    )
    semantic_rows = list(iter_jsonl(route_dir_abs / "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_SEMANTIC_OWNERSHIP_LEDGER.jsonl"))
    semantic_ids = {row["dependency_id"] for row in semantic_rows}
    add_check(
        "semantic_ownership_dependencies_covered",
        {row["dependency_id"] for row in SEMANTIC_DEPENDENCIES}.issubset(semantic_ids),
        {"dependencies": sorted(semantic_ids)},
    )
    baseline_rows = list(iter_jsonl(route_dir_abs / "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_ADVERSARIAL_BASELINE_FIXTURES.jsonl"))
    add_check(
        "adversarial_baseline_fixtures_complete",
        len(baseline_rows) == len(BASELINE_FIXTURES),
        {"actual": len(baseline_rows), "expected": len(BASELINE_FIXTURES)},
    )
    feature_contract = load_json(route_dir_abs / "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_FEATURE_LABEL_CAPTURE_CONTRACT.json")
    add_check(
        "boundary_status_false_where_required",
        feature_contract["boundary_status"]["validation_result_status"] is False
        and feature_contract["boundary_status"]["outcome_result_rows_status"] is False
        and feature_contract["boundary_status"]["broker_runtime_change_status"] is False,
        {"boundary_status": feature_contract["boundary_status"]},
    )
    disposition_rows = list(iter_jsonl(route_dir_abs / "WAVE3_HISTORICAL_REPLAY_DIGITAL_TWIN_V4_PRODUCTION_DISPOSITION_LEDGER.jsonl"))
    add_check(
        "production_disposition_rows_present",
        {row["production_code_disposition"] for row in disposition_rows}
        >= {"staged_default_off", "active_route_evidence"},
    )
    forbidden_true = []
    for path in route_dir_abs.glob("*"):
        if not path.is_file() or path.suffix not in {".json", ".jsonl", ".md", ".py", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for forbidden in (
            '"broker_operation":true',
            '"paid_api_or_vendor_call":true',
            '"remote_push":true',
            '"broker_runtime_change_status":true',
            "credential mutation completed",
            "active VPS process changed",
        ):
            if forbidden in text.replace(" ", ""):
                forbidden_true.append({"path": path.name, "marker": forbidden})
    add_check("forbidden_surface_absence", not forbidden_true, {"violations": forbidden_true})

    return {
        "schema_version": "wave3_historical_replay_verification_result_v1",
        "generated_at_utc": utc_now(),
        "lane": LANE,
        "ok": all(check["passed"] for check in checks),
        "checks": checks,
        "jsonl_counts": jsonl_counts,
        "boundary_status": BOUNDARY_STATUS,
    }

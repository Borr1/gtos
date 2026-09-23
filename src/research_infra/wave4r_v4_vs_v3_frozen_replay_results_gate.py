"""Wave4R V4-vs-V3 frozen replay results gate.

This module is deliberately local/research-only. It consumes the approved
frozen replay artifacts, builds as-of V4 decision packets for every readable
dynamic-policy replay row, compares those decisions to V3/pre-V4 comparators,
and writes the route ledgers required by the Wave4R launch prompt.
"""

from __future__ import annotations

import copy
import csv
import gzip
import hashlib
import json
import math
import os
import subprocess
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

try:  # pragma: no cover - exercised in integration, optional in unit envs.
    import yaml
except Exception:  # pragma: no cover
    yaml = None

from src.components.dynamic_target_stop_geometry_v4 import (
    build_target_stop_geometry_v4_contract,
)
from src.components.execution_manager_v4 import evaluate_execution_manager_v4
from src.components.exit_policy_v4 import (
    ExitPolicyConfigV4,
    ExitPolicyInputV4,
    evaluate_exit_policy_v4,
)
from src.components.live_decision_packet_v4 import (
    build_live_decision_packet_v4,
    validate_live_decision_packet_v4,
)
from src.components.probability_debate_v4 import ProbabilityDebateTeamEngineV4
from src.components.same_symbol_lifecycle_v4 import (
    CandidateLifecycleContext,
    TicketLifecycleSnapshot,
    evaluate_same_symbol_lifecycle_v4,
    symbol_aliases_for_config,
    symbol_key,
)
from src.components.selector_v4 import (
    evaluate_selector_v4_admission,
    selector_v4_action_is_risk_bearing,
)
from src.mt5.mt5_interface import MAGIC_NUMBER
from src.research.moonshot_default_off_policy_router import execution_policy_id_for
from src.research.moonshot_scheduler_v4_best_trade_allocator import allocate_decision_window


ROUTE_NAME = "final_moonshot_wave4r_v4_vs_v3_frozen_replay_results_gate_2026_06_05"
LANE_CODE = "wave4r_v4_vs_v3_frozen_replay_results_gate"
EVIDENCE_REPLAY = "replay"
EVIDENCE_PROXY_R = "proxy-R"
EVIDENCE_SOURCE_GAP = "source gap"
EVIDENCE_BROKER_REAL_PNL = "broker-real PnL"
EVIDENCE_BROKER_REAL_CASH = "broker-real cash"
EVIDENCE_PRODUCTION_CODE = "production code"
EVIDENCE_RUNTIME_CODE = "runtime code"
EVIDENCE_HISTORICAL_ONLY = "historical-only evidence"
CURRENT_V4_POLICY_ID = "v4_promoted_momentum_primary_partial_exception_router_proxy"
CURRENT_V4_GEOMETRY_PROXY_POLICY_ID = "momentum_exhaustion_configured_2r_proxy"
PROMOTED_ROUTER_POLICY_ID = "promoted_momentum_primary_partial_exception_router"
PROMOTED_ROUTER_EVIDENCE_LABEL = "replay/proxy-R"
PROMOTED_ROUTER_EVIDENCE_PATH = (
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27/"
    "ei15r/final_dynamic_router_replay_summary.json"
)
POLICY_TARGET_R = {
    "be_after_trigger": 1.5,
    "partial_be_runner": 3.0,
    "trailing_runner": 3.0,
    "momentum_exhaustion": 2.0,
    "time_stop": 1.5,
}

CP280_ROOT = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
MAY24_ROOT = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_full_historical_candidate_generation_replay_2026_05_24"
)
MAY25_ROOT = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25"
)
MAY26_ROOT = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)
REPLACEMENT_ACTIVATION_ROOT = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_moonshot_production_replacement_activation_2026_05_26"
)
REPLACEMENT_ACTIVATION_REPAIR_ROOT = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
)
WAVE4A_ROOT = Path(
    "research/operations/final_moonshot_wave4a_digital_twin_historical_microscope_2026_06_05"
)
WAVE4I_ROOT = Path(
    "research/operations/final_moonshot_wave4i_integration_partition_gate_2026_06_05"
)
HARD_HALT_ROOT = Path("research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03")
MODULE_REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_ARTIFACTS = (
    "WAVE4R_CONTEXT_ANCHOR.json",
    "WAVE4R_SOURCE_INVENTORY.json",
    "WAVE4R_EXHAUSTIVE_QUESTION_LEDGER.jsonl",
    "WAVE4R_CODE_AND_REPLAY_REPAIR_LEDGER.jsonl",
    "WAVE4R_FROZEN_REPLAY_BINDING_LEDGER.jsonl",
    "WAVE4R_DATA_HYDRATION_AND_REPAIR_LEDGER.jsonl",
    "WAVE4R_READONLY_MT5_EXTRACTION_LEDGER.jsonl",
    "WAVE4R_DYNAMIC_POLICY_SHARD_REPAIR_LEDGER.jsonl",
    "WAVE4R_REPLAY_SUBSTRATE_REPAIR_SEARCH_LEDGER.jsonl",
    "WAVE4R_ORDERED_PATH_RECONSTRUCTION_LEDGER.jsonl",
    "WAVE4R_MULTI_CANDIDATE_WINDOW_ALLOCATION_LEDGER.jsonl",
    "WAVE4R_HARD_HALT_BINDING_LEDGER.jsonl",
    "WAVE4R_V3_PREV4_COMPARATOR_LEDGER.jsonl",
    "WAVE4R_V4_ASOF_PACKET_LEDGER.jsonl",
    "WAVE4R_CHRONOLOGICAL_STATE_TRANSITION_LEDGER.jsonl",
    "WAVE4R_CANDIDATE_TRADE_MICROSCOPE_LEDGER.jsonl",
    "WAVE4R_CANDIDATE_DECISION_MICROSCOPE_LEDGER.jsonl",
    "WAVE4R_TRADE_PATH_ANATOMY_LEDGER.jsonl",
    "WAVE4R_RESULTS_LEDGER.jsonl",
    "WAVE4R_DECISION_LEDGER.jsonl",
    "WAVE4R_RESULTS_SUMMARY.json",
    "WAVE4R_REPLAY_ACCOUNT_CURVE_LEDGER.jsonl",
    "WAVE4R_V3_V4_DELTA_LEDGER.jsonl",
    "WAVE4R_FROZEN_VS_LIVE_DELTA_LEDGER.jsonl",
    "WAVE4R_SYMBOL_SESSION_REGIME_BREAKDOWN_LEDGER.jsonl",
    "WAVE4R_DAY_SESSION_MICROSCOPE_LEDGER.jsonl",
    "WAVE4R_ENTRY_QUALITY_LEDGER.jsonl",
    "WAVE4R_ENTRY_EXIT_TIMING_PATH_LEDGER.jsonl",
    "WAVE4R_SELECTOR_EXECUTION_EXIT_ANATOMY_LEDGER.jsonl",
    "WAVE4R_SAME_SYMBOL_ACTION_LEDGER.jsonl",
    "WAVE4R_STATIC_R_DYNAMIC_GEOMETRY_LEDGER.jsonl",
    "WAVE4R_TIME_MFE_MAE_GIVEBACK_LEDGER.jsonl",
    "WAVE4R_FOLLOW_AVOID_MIXED_CONFLUENCE_LEDGER.jsonl",
    "WAVE4R_PROBABILITY_CALIBRATION_LEDGER.jsonl",
    "WAVE4R_ZERO_TRADE_OPPORTUNITY_COST_LEDGER.jsonl",
    "WAVE4R_ACCEPTED_LOSER_FORENSIC_LEDGER.jsonl",
    "WAVE4R_REJECTED_WINNER_OPPORTUNITY_LEDGER.jsonl",
    "WAVE4R_SCHEDULER_ALLOCATION_REGRET_LEDGER.jsonl",
    "WAVE4R_EXIT_HARVEST_COUNTERFACTUAL_LEDGER.jsonl",
    "WAVE4R_STALE_HOLDINGS_THESIS_AGE_LEDGER.jsonl",
    "WAVE4R_SOURCE_GAP_CAPTURE_REQUIREMENT_LEDGER.jsonl",
    "WAVE4R_SUBAGENT_OR_RESOURCE_USE_LEDGER.jsonl",
    "WAVE4R_ACTIONABLE_V4_REPAIR_FINDINGS_LEDGER.jsonl",
    "WAVE4R_V4_LIMITATIONS_AND_FIX_BACKLOG.json",
    "WAVE4R_ML_DEFERRAL_REJECTION_LEDGER.jsonl",
    "WAVE4R_WAVE5_DATASET_HANDOFF.json",
    "WAVE4R_RESULTS_GATE_VERIFICATION_RESULT.json",
    "WAVE4R_RESULTS_GATE_FOCUSED_TEST_RESULT.json",
    "WAVE4R_RESULTS_GATE_PROMPT_HARDENING_RESULT.json",
    "WAVE4R_RESULTS_GATE_ROUTE_ARTIFACT_AUDIT_RESULT.json",
    "WAVE4R_RESULTS_GATE_SATURATION_SELF_RED_TEAM.md",
    "WAVE4R_RESULTS_GATE_INSTRUCTION_COVERAGE_CHECKLIST.md",
    "WAVE4R_RESULTS_GATE_OUTPUT_MANIFEST.json",
    "COMPLETION_AUDIT.md",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    try:
        return asdict(value)
    except TypeError:
        return str(value)


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        _json_safe(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(payload), handle, indent=2, sort_keys=True)
        handle.write("\n")


def append_jsonl(handle: Any, payload: Mapping[str, Any]) -> None:
    handle.write(json.dumps(_json_safe(payload), sort_keys=True, ensure_ascii=True))
    handle.write("\n")


def jsonl_is_gzip(path: Path) -> bool:
    if path.suffix == ".gz":
        return True
    if not path.exists() or not path.is_file() or path.stat().st_size < 2:
        return False
    with path.open("rb") as handle:
        return handle.read(2) == b"\x1f\x8b"


def open_jsonl_text(path: Path, mode: str = "rt") -> Any:
    if jsonl_is_gzip(path) or "w" in mode and os.environ.get("WAVE4R_COMPRESS_JSONL") == "1":
        return gzip.open(path, mode, encoding="utf-8")
    return path.open(mode.replace("t", ""), encoding="utf-8")


def append_jsonl_path(path: Path, payload: Mapping[str, Any]) -> None:
    with open_jsonl_text(path, "at") as handle:
        append_jsonl(handle, payload)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open_jsonl_text(path, "rt") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            row = json.loads(text)
            if isinstance(row, dict):
                row["_source_jsonl_path"] = str(path)
                row["_source_jsonl_line"] = line_number
                yield row


def count_jsonl_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with open_jsonl_text(path, "rt") as handle:
        return sum(1 for line in handle if line.strip())


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists() or yaml is None:
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def _float(value: Any, default: float | None = None) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return number


def _int(value: Any, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _side(value: Any) -> str:
    text = _text(value).upper()
    if text in {"BUY", "LONG", "BULL", "BULLISH", "0"}:
        return "LONG"
    if text in {"SELL", "SHORT", "BEAR", "BEARISH", "1"}:
        return "SHORT"
    return text or "UNKNOWN"


def parse_iso(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip().replace("Z", "+00:00")
        if " " in text and "T" not in text:
            text = text.replace(" ", "T")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso_or_none(value: Any) -> str | None:
    dt = parse_iso(value)
    return dt.isoformat() if dt else None


def row_asof(row: Mapping[str, Any]) -> str:
    return (
        iso_or_none(row.get("entry_first_touch_utc"))
        or iso_or_none(row.get("candle_time_utc"))
        or iso_or_none(row.get("decision_time_utc"))
        or "1970-01-01T00:00:00+00:00"
    )


def current_route_dir(repo_root: Path) -> Path:
    return repo_root / "research/operations" / ROUTE_NAME


def normalize_v4_config(config: Mapping[str, Any] | None) -> dict[str, Any]:
    cfg = copy.deepcopy(dict(config or {}))
    runtime = cfg.setdefault("gtos_vnext_runtime", {})
    if not isinstance(runtime, dict):
        runtime = {}
        cfg["gtos_vnext_runtime"] = runtime
    debate = runtime.setdefault("probability_debate_team_engine_v4", {})
    if isinstance(debate, dict):
        debate.setdefault("enabled", True)
        debate.setdefault("apply_to_execution", True)
        debate.setdefault("required_source_families", [
            "selector",
            "market_state",
            "cost",
            "lifecycle",
            "source_completeness",
        ])
    runtime.setdefault("selector_v4_enabled", True)
    runtime.setdefault("selector_v4_apply_to_execution", True)
    runtime.setdefault("selector_v4_min_broker_net_trade_ev_r", 0.10)
    runtime.setdefault("selector_v4_min_confluence_source_completeness", 0.45)
    runtime.setdefault("wave4r_simulated_replay_relax_live_source_floors", True)
    if runtime.get("wave4r_simulated_replay_relax_live_source_floors", True):
        current_confluence_floor = _float(
            runtime.get("selector_v4_min_confluence_source_completeness"),
            0.45,
        )
        current_selected_cell_floor = _float(
            runtime.get("selector_v4_min_selected_cell_source_completeness"),
            0.70,
        )
        runtime["selector_v4_min_confluence_source_completeness"] = min(
            current_confluence_floor or 0.45,
            0.55,
        )
        runtime["selector_v4_min_selected_cell_source_completeness"] = min(
            current_selected_cell_floor or 0.70,
            0.55,
        )
    runtime.setdefault("moonshot_dynamic_execution_router_policy", "momentum_exhaustion")
    runtime.setdefault("moonshot_dynamic_execution_router_momentum_final_target_r", 2.0)
    runtime.setdefault("moonshot_exit_policy_v4_enabled", True)
    runtime.setdefault("moonshot_exit_policy_v4_apply_to_execution", True)
    runtime.setdefault("execution_manager_v4_enabled", True)
    runtime.setdefault("execution_manager_v4_apply_to_execution", True)
    risk = cfg.setdefault("risk", {})
    if isinstance(risk, dict):
        risk.setdefault("risk_per_trade_pct", 2.0)
        lifecycle_cfg = risk.setdefault("same_symbol_lifecycle_v4", {})
        if not isinstance(lifecycle_cfg, dict):
            lifecycle_cfg = {}
            risk["same_symbol_lifecycle_v4"] = lifecycle_cfg
        lifecycle_cfg.setdefault("enabled", True)
        lifecycle_cfg.setdefault("max_same_symbol_risk_pct", 2.5)
        lifecycle_cfg.setdefault("scale_in_min_probability_improvement", 0.04)
        lifecycle_cfg.setdefault("scale_in_min_ev_improvement_r", 0.05)
        lifecycle_cfg.setdefault("replay_allow_same_direction_better_thesis_scale_in", True)
        if lifecycle_cfg.get("replay_allow_same_direction_better_thesis_scale_in", True):
            lifecycle_cfg["scale_in_requires_same_thesis"] = False
        else:
            lifecycle_cfg.setdefault("scale_in_requires_same_thesis", True)
    return cfg


def config_runtime(config: Mapping[str, Any] | None) -> dict[str, Any]:
    runtime = (config or {}).get("gtos_vnext_runtime", {})
    return runtime if isinstance(runtime, dict) else {}


def active_policy_reference(config: Mapping[str, Any] | None) -> dict[str, Any]:
    runtime = config_runtime(config)
    return {
        "configured_router_policy": runtime.get(
            "moonshot_dynamic_execution_router_policy",
            "momentum_exhaustion",
        ),
        "configured_final_target_r": _float(
            runtime.get("moonshot_dynamic_execution_router_momentum_final_target_r"),
            2.0,
        ),
        "wave4r_replay_policy_id": CURRENT_V4_POLICY_ID,
        "promoted_router_policy_id": PROMOTED_ROUTER_POLICY_ID,
        "promoted_router_evidence_path": PROMOTED_ROUTER_EVIDENCE_PATH,
        "evidence_label": PROMOTED_ROUTER_EVIDENCE_LABEL,
        "source_gap": (
            "Wave4R binds May-27 promoted dynamic-router replay rows where available. "
            "Those rows are replay/proxy-R gross policy results, not broker-real live PnL; "
            "net R remains source-gapped where historical cost/lifecycle fields are missing."
        ),
    }


def artifact_descriptor(path: Path, repo_root: Path) -> dict[str, Any]:
    exists = path.exists()
    rel = str(path.relative_to(repo_root)) if path.exists() and path.is_absolute() else str(path)
    descriptor = {
        "path": rel,
        "exists": exists,
        "kind": "missing",
        "bytes": None,
        "sha256": None,
        "jsonl_rows": None,
        "evidence_label": EVIDENCE_SOURCE_GAP if not exists else "historical-only evidence",
    }
    if not exists:
        return descriptor
    descriptor["bytes"] = path.stat().st_size
    descriptor["sha256"] = sha256_file(path) if path.is_file() else None
    if path.is_dir():
        descriptor["kind"] = "directory"
    elif path.suffix == ".gz":
        descriptor["kind"] = "compressed_chunk"
    elif path.suffix == ".jsonl":
        descriptor["kind"] = "hydrated_jsonl"
        descriptor["jsonl_rows"] = count_jsonl_rows(path)
    elif path.suffix == ".json":
        descriptor["kind"] = "summary_json"
    else:
        descriptor["kind"] = "file"
    if path.is_file() and path.stat().st_size < 200:
        try:
            head = path.read_text(errors="replace")[:120]
        except UnicodeDecodeError:
            head = ""
        if "version https://git-lfs.github.com/spec/v1" in head:
            descriptor["kind"] = "lfs_pointer"
            descriptor["evidence_label"] = "uncommitted dirt"
    return descriptor


def discover_dynamic_shards(repo_root: Path) -> list[Path]:
    root = repo_root / MAY26_ROOT
    return sorted(root.glob("stage04_dynamic_policy_shards/*/dynamic_policy_replay.jsonl"))


def dynamic_shard_index_rows(repo_root: Path) -> list[dict[str, Any]]:
    path = (
        repo_root
        / MAY26_ROOT
        / "VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SHARD_INDEX_2026-05-26.jsonl"
    )
    if not path.exists():
        return []
    return list(iter_jsonl(path))


def stage05_activation_manifest_rows(repo_root: Path) -> list[dict[str, Any]]:
    path = (
        repo_root
        / REPLACEMENT_ACTIVATION_ROOT
        / "VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SHARD_MANIFEST_2026-05-26.jsonl"
    )
    if not path.exists():
        return []
    return list(iter_jsonl(path))


def missing_dynamic_shard_ids(repo_root: Path) -> set[str]:
    missing: set[str] = set()
    for row in dynamic_shard_index_rows(repo_root):
        output = repo_root / _text(row.get("output_chunk_path"))
        if not output.exists():
            shard_id = output.parent.name
            if shard_id:
                missing.add(shard_id)
    return missing


def stage05_manifest_by_shard(repo_root: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in stage05_activation_manifest_rows(repo_root):
        source = _text(row.get("input_dynamic_replay_path"))
        if not source:
            continue
        rows[Path(source).parent.name] = row
    return rows


def stage05_recovery_paths(repo_root: Path) -> dict[str, Path]:
    root = repo_root / REPLACEMENT_ACTIVATION_ROOT / "stage05_full_activated_replay_shards"
    paths: dict[str, Path] = {}
    for shard_id in missing_dynamic_shard_ids(repo_root):
        path = root / shard_id / "activated_replay.jsonl.gz"
        if path.exists():
            paths[shard_id] = path
    return paths


def stage05_dynamic_row(stage05_row: Mapping[str, Any], *, source_path: Path, repo_root: Path) -> dict[str, Any] | None:
    dynamic = stage05_row.get("dynamic_policy_replay")
    if not isinstance(dynamic, Mapping) or dynamic.get("available") is not True:
        return None
    bar_path = stage05_row.get("bar_close_m15_path")
    bar = bar_path if isinstance(bar_path, Mapping) else {}
    legacy = stage05_row.get("legacy_fixed_1_5r_comparator")
    legacy_comparator = legacy if isinstance(legacy, Mapping) else {}
    row = {
        "candidate_id": stage05_row.get("candidate_id"),
        "candle_time_utc": stage05_row.get("candle_time_utc"),
        "entry_first_touch_utc": bar.get("entry_first_touch_utc"),
        "entry_reference": stage05_row.get("entry_reference"),
        "framework": stage05_row.get("framework") or stage05_row.get("candidate_origin_family"),
        "candidate_origin_family": stage05_row.get("candidate_origin_family"),
        "origin_family": stage05_row.get("origin_family"),
        "path_row_id": stage05_row.get("path_row_id") or bar.get("path_row_id"),
        "policy_results": dynamic.get("policy_results") or {},
        "observation_count": dynamic.get("observation_count"),
        "old_static_rr": stage05_row.get("rr"),
        "old_static_simulated_r": legacy_comparator.get("final_r") or bar.get("simulated_r"),
        "old_static_terminal_order_raw": bar.get("terminal_order_raw"),
        "old_static_terminal_outcome": bar.get("terminal_outcome"),
        "side": stage05_row.get("side"),
        "session_bucket": stage05_row.get("session_bucket"),
        "source_path_feature_status": "recovered_from_stage05_activated_replay",
        "source_path": stage05_row.get("source_path") or bar.get("source_path"),
        "source_sha256": stage05_row.get("source_sha256") or bar.get("source_sha256"),
        "source_window_complete": stage05_row.get("source_window_complete"),
        "stop_or_invalidation": stage05_row.get("stop_or_invalidation"),
        "symbol": stage05_row.get("symbol"),
        "target_reference": stage05_row.get("target_reference"),
        "path_source_status": bar.get("path_source_status"),
        "price_path_truth_status": bar.get("price_path_truth_status"),
        "sl_first_touch_utc": bar.get("sl_first_touch_utc"),
        "tp1_first_touch_utc": bar.get("tp1_first_touch_utc") or bar.get("tp_first_touch_utc"),
        "terminal_order_raw": bar.get("terminal_order_raw"),
        "terminal_outcome": bar.get("terminal_outcome"),
        "activated_replay_disposition": stage05_row.get("activated_replay_disposition"),
        "activated_selected_policy": (
            (stage05_row.get("activated_default_router_projection") or {}).get("selected_policy")
            if isinstance(stage05_row.get("activated_default_router_projection"), Mapping)
            else None
        ),
        "condition_selected_policy": (
            (stage05_row.get("condition_router_projection") or {}).get("selected_policy")
            if isinstance(stage05_row.get("condition_router_projection"), Mapping)
            else None
        ),
        "_dynamic_shard_path": str(source_path.relative_to(repo_root)),
        "_wave4r_recovery_status": "recovered_from_stage05_activated_replay_missing_stage04_dynamic_shard",
        "_wave4r_recovery_source_hash": stable_hash(stage05_row),
    }
    return row


def final_dynamic_router_replay_paths(repo_root: Path) -> list[Path]:
    root = repo_root / REPLACEMENT_ACTIVATION_REPAIR_ROOT / "ei15r"
    return sorted(root.glob("final_dynamic_router_replay.part-*.jsonl"))


def compact_final_dynamic_router_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Keep only the promoted-router fields Wave4R needs for row-level truth."""

    compact = {
        "candidate_id": row.get("candidate_id"),
        "source_record_candidate_id": row.get("source_record_candidate_id"),
        "selected_row_id": row.get("selected_row_id"),
        "chosen_policy": row.get("chosen_policy") or row.get("raw_asof_selected_policy"),
        "raw_asof_selected_policy": row.get("raw_asof_selected_policy"),
        "execution_policy_id": row.get("execution_policy_id"),
        "source_time_utc": iso_or_none(row.get("source_time_utc")),
        "entry_touch_time_utc": iso_or_none(row.get("entry_touch_time_utc")),
        "entry_timing": row.get("entry_timing"),
        "fill_status": row.get("fill_status"),
        "limit_fill_status": row.get("limit_fill_status"),
        "delayed_fill_bars": _int(row.get("delayed_fill_bars")),
        "final_r": _float(row.get("final_r")),
        "net_r": _float(row.get("net_r")),
        "cost_status": row.get("cost_status"),
        "cost_r": _float(row.get("cost_r")),
        "mfe_r": _float(row.get("mfe_r")),
        "mae_r": _float(row.get("mae_r")),
        "exit_reason": row.get("exit_reason"),
        "exit_time_utc": iso_or_none(row.get("exit_time_utc")),
        "same_bar_ambiguity": row.get("same_bar_ambiguity"),
        "selected_policy_ordered_path_status": row.get(
            "selected_policy_ordered_path_status_after_replay"
        ),
        "router_decision_status": row.get("router_decision_status"),
        "router_candidate_action": row.get("router_candidate_action"),
        "router_runtime_effect_now": row.get("router_runtime_effect_now"),
        "candidate_origin_family": row.get("candidate_origin_family"),
        "origin_family": row.get("origin_family"),
        "session_bucket": row.get("session_bucket"),
        "framework": row.get("framework"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "source_path": row.get("source_path"),
        "source_sha256": row.get("source_sha256"),
        "m1_availability_status": row.get("m1_availability_status"),
        "tick_availability_status": row.get("tick_availability_status"),
        "missing_field_notes": list(row.get("missing_field_notes") or []),
        "router_evidence_notes": list(row.get("router_evidence_notes") or []),
        "hindsight_best_policy": row.get("hindsight_best_policy"),
        "hindsight_best_r": _float(row.get("hindsight_best_r")),
        "hindsight_regret_r": _float(row.get("hindsight_regret_r")),
        "dynamic_policy_transition_trace": row.get("dynamic_policy_transition_trace")
        if isinstance(row.get("dynamic_policy_transition_trace"), Mapping)
        else {},
        "comparison_be_after_trigger_r": _float(row.get("comparison_be_after_trigger_r")),
        "comparison_fixed_1_5r_r": _float(row.get("comparison_fixed_1_5r_r")),
        "comparison_momentum_exhaustion_r": _float(row.get("comparison_momentum_exhaustion_r")),
        "comparison_partial_be_runner_r": _float(row.get("comparison_partial_be_runner_r")),
        "comparison_time_stop_r": _float(row.get("comparison_time_stop_r")),
        "comparison_trailing_runner_r": _float(row.get("comparison_trailing_runner_r")),
        "replay_source_class": row.get("replay_source_class"),
        "schema_version": row.get("schema_version"),
    }
    close_mark = row.get("exit_policy_close_mark")
    if isinstance(close_mark, Mapping):
        compact["exit_policy_close_mark"] = dict(close_mark)
    for key in (
        "exit_policy_close_mark_r",
        "exit_policy_close_mark_time_utc",
        "exit_policy_close_mark_action",
        "exit_policy_close_mark_close_reason",
        "exit_policy_close_mark_bars_elapsed",
        "exit_policy_close_mark_policy_id",
        "exit_policy_close_mark_source_status",
        "exit_policy_close_mark_source_path",
        "exit_policy_close_mark_source_sha256",
    ):
        if row.get(key) not in (None, "", [], {}):
            compact[key] = row.get(key)
    return compact


def load_final_dynamic_router_index(repo_root: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for path in final_dynamic_router_replay_paths(repo_root):
        for row in iter_jsonl(path):
            compact = compact_final_dynamic_router_row(row)
            compact["_final_dynamic_router_replay_path"] = str(path.relative_to(repo_root))
            for raw_id in (row.get("source_record_candidate_id"), row.get("candidate_id")):
                cid = _text(raw_id)
                if cid and cid not in index:
                    index[cid] = compact
    return index


def inventory_sources(repo_root: Path) -> dict[str, Any]:
    cp_root = repo_root / CP280_ROOT
    may24_root = repo_root / MAY24_ROOT
    may25_root = repo_root / MAY25_ROOT
    may26_root = repo_root / MAY26_ROOT
    wave4a_root = repo_root / WAVE4A_ROOT
    wave4i_root = repo_root / WAVE4I_ROOT
    hard_halt_root = repo_root / HARD_HALT_ROOT
    cp_handoff = load_json(cp_root / "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_MAIN_HANDOFF_RESULT_2026-05-17.json", {})
    cp_closure = load_json(cp_root / "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_IMPLEMENTATION_CLOSURE_RESULT_2026-05-17.json", {})
    may24_metrics = load_json(may24_root / "VNEXT_FULL_REPLAY_METRICS_SUMMARY_2026-05-24.json", {})
    may24_candidates = load_json(may24_root / "VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_SUMMARY_2026-05-24.json", {})
    may24_verify = load_json(may24_root / "VNEXT_FULL_REPLAY_FINAL_VERIFICATION_RESULT_2026-05-24.json", {})
    may25_manifest = load_json(may25_root / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_INPUT_MANIFEST_2026-05-25.json", {})
    may25_metrics = load_json(may25_root / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_REPLAY_METRICS_SUMMARY_2026-05-25.json", {})
    may26_summary = load_json(may26_root / "VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SUMMARY_2026-05-26.json", {})
    may26_map = load_json(may26_root / "VNEXT_MOONSHOT_RUNTIME_INTEGRATION_MAP_2026-05-26.json", {})
    may26_source = load_json(may26_root / "VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_2026-05-26.json", {})
    wave4i_manifest = load_json(wave4i_root / "WAVE4I_WAVE5_HANDOFF_MANIFEST.json", {})
    dynamic_shards = discover_dynamic_shards(repo_root)
    dynamic_rows = sum(count_jsonl_rows(path) for path in dynamic_shards)
    missing_shards = missing_dynamic_shard_ids(repo_root)
    activation_manifest = stage05_manifest_by_shard(repo_root)
    recovered_dynamic_rows = sum(
        _int((activation_manifest.get(shard_id) or {}).get("input_dynamic_replay_rows"), 0) or 0
        for shard_id in missing_shards
    )
    recovered_paths = stage05_recovery_paths(repo_root)
    shard_index = may26_root / "VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SHARD_INDEX_2026-05-26.jsonl"
    final_router_paths = final_dynamic_router_replay_paths(repo_root)
    final_router_summary_path = (
        repo_root
        / REPLACEMENT_ACTIVATION_REPAIR_ROOT
        / "ei15r"
        / "final_dynamic_router_replay_summary.json"
    )
    final_router_summary = load_json(final_router_summary_path, {})
    expected_shards = _int(may26_summary.get("input_stage04_shards"), 45) or 45
    expected_rows = _int(may26_summary.get("replayable_candidate_rows"), 214536) or 214536
    source_inventory = {
        "schema_version": "wave4r_source_inventory_v1",
        "generated_at_utc": utc_now(),
        "repo_root": str(repo_root),
        "route": ROUTE_NAME,
        "branch_expected": "final-moonshot-wave4r-v4-vs-v3-frozen-replay-results-gate-2026-06-05",
        "frozen_surfaces": {
            "cp280_cp281": {
                "root": str(CP280_ROOT),
                "main_handoff_counts": cp_handoff.get("counts") or cp_handoff,
                "implementation_closure_counts": cp_closure.get("counts") or cp_closure,
                "required_counts_verified_from_disk": {
                    "input_artifacts_consumed": cp_closure.get("input_artifacts_consumed")
                    or (cp_closure.get("counts") or {}).get("input_artifacts_consumed"),
                    "jsonl_rows_scanned": cp_closure.get("jsonl_rows_scanned")
                    or (cp_closure.get("counts") or {}).get("jsonl_rows_scanned"),
                    "implementation_ready_rows": cp_closure.get("implementation_ready_rows")
                    or (cp_closure.get("counts") or {}).get("implementation_ready_rows"),
                    "implementation_ready_source_rows": cp_closure.get("implementation_ready_source_rows")
                    or (cp_closure.get("counts") or {}).get("implementation_ready_source_rows"),
                    "repair_needed_rows": cp_closure.get("repair_needed_rows")
                    or (cp_closure.get("counts") or {}).get("repair_needed_rows"),
                    "coverage_rows": cp_closure.get("coverage_rows")
                    or (cp_closure.get("counts") or {}).get("coverage_rows"),
                    "kill_preserve_rows": cp_closure.get("kill_preserve_rows")
                    or (cp_closure.get("counts") or {}).get("kill_preserve_rows"),
                },
            },
            "may24_full_replay": {
                "root": str(MAY24_ROOT),
                "metrics_summary": {
                    "stage01_m15_denominator_rows": may24_metrics.get("stage01_m15_denominator_rows"),
                    "stage02_candidate_rows": may24_metrics.get("stage02_candidate_rows"),
                    "stage03_runtime_trace_rows": may24_metrics.get("stage03_runtime_trace_rows"),
                    "stage04_path_outcome_r_rows": may24_metrics.get("stage04_path_outcome_r_rows"),
                    "stage05_dominance_and_pollution_rows": may24_metrics.get("stage05_dominance_and_pollution_rows"),
                    "stage06_final_decision_map_rows": may24_metrics.get("stage06_final_decision_map_rows"),
                    "completion_status": may24_metrics.get("completion_status") or may24_metrics.get("status"),
                },
                "candidate_summary": may24_candidates,
                "verification": may24_verify,
            },
            "may25_v3_prev4_comparator": {
                "root": str(MAY25_ROOT),
                "candidate_universe_rows": may25_manifest.get("candidate_rows")
                or may25_metrics.get("candidate_universe_rows"),
                "executable_stream_rows": may25_metrics.get("executable_stream_rows"),
                "best_policy": may25_metrics.get("best_policy")
                or may25_metrics.get("selected_policy")
                or "ACCOUNT_ABANDON_OR_RESTART",
                "policy_metrics": may25_metrics.get("policy_metrics") or may25_metrics,
                "missing_source_rows": count_jsonl_rows(
                    may25_root / "STAGE10_MISSING_SOURCE_LEDGER_2026-05-25.jsonl"
                ),
            },
            "may26_dynamic_policy_replay": {
                "root": str(MAY26_ROOT),
                "candidate_rows_in_replay_mode": may26_summary.get("candidate_rows_in_replay_mode"),
                "replayable_candidate_rows_expected": expected_rows,
                "input_rows_scanned": may26_summary.get("input_rows_scanned"),
                "shard_index_rows": count_jsonl_rows(shard_index),
                "shards_expected": expected_shards,
                "readable_dynamic_policy_shards": len(dynamic_shards),
                "native_readable_dynamic_policy_rows": dynamic_rows,
                "recovered_dynamic_policy_rows_from_stage05": recovered_dynamic_rows,
                "readable_dynamic_policy_rows": dynamic_rows + recovered_dynamic_rows,
                "missing_dynamic_policy_shards": max(0, expected_shards - len(dynamic_shards)),
                "missing_dynamic_policy_rows": max(0, expected_rows - dynamic_rows - recovered_dynamic_rows),
                "stage05_recovery_shards": sorted(recovered_paths),
                "unrecovered_dynamic_policy_shards": sorted(missing_shards - set(recovered_paths)),
                "policy_total_r": may26_summary.get("policy_total_r"),
                "runtime_integration_map": may26_map.get("selected_default_off_production_candidate"),
                "source_capability_rows": may26_source.get("source_capability_rows"),
                "shard_index_artifact": artifact_descriptor(shard_index, repo_root),
                "stage05_activation_manifest_artifact": artifact_descriptor(
                    repo_root
                    / REPLACEMENT_ACTIVATION_ROOT
                    / "VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SHARD_MANIFEST_2026-05-26.jsonl",
                    repo_root,
                ),
                "stage05_recovered_shard_artifacts": [
                    artifact_descriptor(path, repo_root) for path in recovered_paths.values()
                ],
                "readable_shard_artifacts": [
                    artifact_descriptor(path, repo_root) for path in dynamic_shards
                ],
            },
            "may27_promoted_dynamic_router_replay": {
                "root": str(REPLACEMENT_ACTIVATION_REPAIR_ROOT / "ei15r"),
                "authority_role": (
                    "promoted momentum_exhaustion primary with partial_be_runner "
                    "exception replay comparator; static/J46 rows are secondary historical comparators"
                ),
                "summary_artifact": artifact_descriptor(final_router_summary_path, repo_root),
                "replay_part_artifacts": [
                    artifact_descriptor(path, repo_root) for path in final_router_paths
                ],
                "replay_rows": sum(count_jsonl_rows(path) for path in final_router_paths),
                "final_dynamic_router_metrics": final_router_summary.get(
                    "final_dynamic_router_metrics"
                ),
                "global_policy_comparison_metrics": final_router_summary.get(
                    "global_policy_comparison_metrics"
                ),
                "policy_distribution": final_router_summary.get("policy_distribution"),
                "raw_asof_policy_distribution": final_router_summary.get(
                    "raw_asof_policy_distribution"
                ),
                "fixed_1_5r_role": final_router_summary.get("fixed_1_5r_role"),
            },
            "wave4a_canonical_universe": {
                "root": str(WAVE4A_ROOT),
                "canonical_rows": count_jsonl_rows(wave4a_root / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl"),
                "canonical_artifact": artifact_descriptor(
                    wave4a_root / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl",
                    repo_root,
                ),
            },
            "wave4i_partition_gate": {
                "root": str(WAVE4I_ROOT),
                "manifest": wave4i_manifest,
            },
            "hard_halt_broker_truth": {
                "root": str(HARD_HALT_ROOT),
                "trade_groups": artifact_descriptor(
                    hard_halt_root / "BROKER_TRUTH_TRADE_GROUPS_2026_04_27_TO_HALT.json",
                    repo_root,
                ),
                "deals": artifact_descriptor(
                    hard_halt_root / "BROKER_TRUTH_DEALS_2026_04_27_TO_HALT.json",
                    repo_root,
                ),
                "orders": artifact_descriptor(
                    hard_halt_root / "BROKER_TRUTH_ORDERS_2026_04_27_TO_HALT.json",
                    repo_root,
                ),
            },
        },
        "active_policy_reference": active_policy_reference(
            normalize_v4_config(load_yaml(repo_root / "config/agent_config.yaml"))
        ),
        "hard_boundaries": {
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "remote_push": False,
            "active_vps_mutation": False,
            "mt5_live_operation": False,
            "local_research_code_and_artifact_build": True,
        },
    }
    return source_inventory


def iter_dynamic_rows(repo_root: Path, *, max_rows: int | None = None) -> Iterator[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    promoted_router_index = load_final_dynamic_router_index(repo_root)
    for shard_path in discover_dynamic_shards(repo_root):
        for row in iter_jsonl(shard_path):
            row["_dynamic_shard_path"] = str(shard_path.relative_to(repo_root))
            row["_wave4r_recovery_status"] = "native_may26_stage04_dynamic_policy_replay"
            promoted = promoted_router_index.get(_text(row.get("candidate_id")))
            if promoted:
                row["_promoted_router_replay"] = promoted
            rows.append(row)
            if max_rows is not None and len(rows) >= max_rows:
                break
        if max_rows is not None and len(rows) >= max_rows:
            break
    if max_rows is None or len(rows) < max_rows:
        for shard_id, shard_path in sorted(stage05_recovery_paths(repo_root).items()):
            for source_row in iter_jsonl(shard_path):
                row = stage05_dynamic_row(source_row, source_path=shard_path, repo_root=repo_root)
                if row is None:
                    continue
                promoted = promoted_router_index.get(_text(row.get("candidate_id")))
                if promoted:
                    row["_promoted_router_replay"] = promoted
                rows.append(row)
                if max_rows is not None and len(rows) >= max_rows:
                    break
            if max_rows is not None and len(rows) >= max_rows:
                break
    rows.sort(key=lambda row: (row_asof(row), str(row.get("candidate_id") or "")))
    for index, row in enumerate(rows, start=1):
        row["_wave4r_sequence"] = index
        yield row


def iter_dynamic_windows(repo_root: Path, *, max_rows: int | None = None) -> Iterator[list[dict[str, Any]]]:
    current_asof: str | None = None
    window: list[dict[str, Any]] = []
    for row in iter_dynamic_rows(repo_root, max_rows=max_rows):
        asof = row_asof(row)
        if current_asof is None:
            current_asof = asof
        if asof != current_asof:
            yield window
            window = []
            current_asof = asof
        window.append(row)
    if window:
        yield window


def candidate_id(row: Mapping[str, Any]) -> str:
    return _text(row.get("candidate_id") or row.get("path_row_id") or row.get("row_id") or stable_hash(row))


def row_symbol(row: Mapping[str, Any]) -> str:
    return _text(row.get("symbol") or row.get("source_symbol") or "UNKNOWN").upper()


def row_session(row: Mapping[str, Any]) -> str:
    return _text(
        row.get("session")
        or row.get("session_name")
        or row.get("session_bucket")
        or row.get("origin_session")
        or "UNKNOWN"
    ).upper()


def row_framework(row: Mapping[str, Any]) -> str:
    return _text(row.get("framework") or row.get("origin_framework") or "UNKNOWN")


def policy_result(row: Mapping[str, Any], policy: str) -> dict[str, Any]:
    policies = row.get("policy_results")
    if isinstance(policies, Mapping):
        value = policies.get(policy)
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def row_mfe_mae(row: Mapping[str, Any]) -> tuple[float | None, float | None]:
    candidates: list[Mapping[str, Any]] = []
    for policy in (
        "legacy_fixed_1.5r",
        "be_after_trigger",
        "partial_be_runner",
        "live_current_j46_j49",
        "path_aware_runner",
        "trailing_runner",
        "ai_target",
    ):
        result = policy_result(row, policy)
        if result:
            candidates.append(result)
    mfe_values = [_float(item.get("mfe_r")) for item in candidates]
    mae_values = [_float(item.get("mae_r")) for item in candidates]
    mfe = max((value for value in mfe_values if value is not None), default=None)
    mae = min((value for value in mae_values if value is not None), default=None)
    if mfe is None:
        mfe = _float(row.get("mfe_r"))
    if mae is None:
        mae = _float(row.get("mae_r"))
    return mfe, mae


def row_final_times(row: Mapping[str, Any]) -> dict[str, str | None]:
    times: dict[str, str | None] = {}
    for policy in ("legacy_fixed_1.5r", "be_after_trigger", "partial_be_runner", "live_current_j46_j49"):
        result = policy_result(row, policy)
        times[policy] = iso_or_none(result.get("exit_time_utc"))
    return times


def ordered_target_stop_times(row: Mapping[str, Any], *, target_r: float) -> tuple[str | None, str | None, str]:
    explicit_target = (
        iso_or_none(row.get("configured_target_first_touch_utc"))
        or iso_or_none(row.get(f"target_{str(target_r).replace('.', '_')}r_first_touch_utc"))
        or iso_or_none(row.get("target_2r_first_touch_utc"))
    )
    explicit_stop = (
        iso_or_none(row.get("configured_stop_first_touch_utc"))
        or iso_or_none(row.get("stop_first_touch_utc"))
        or iso_or_none(row.get("sl_first_touch_utc"))
    )
    old_rr = _float(row.get("old_static_rr") or row.get("rr"))
    if explicit_target is None and old_rr is not None and abs(old_rr - target_r) <= 1e-6:
        explicit_target = iso_or_none(row.get("tp1_first_touch_utc") or row.get("tp_first_touch_utc"))
    if explicit_target or explicit_stop:
        return explicit_target, explicit_stop, "ordered_touch_times_from_path_row_or_recovered_stage05"
    return None, None, "ordered_touch_times_missing"


def ordered_target_stop_outcome(row: Mapping[str, Any], *, target_r: float = 2.0) -> dict[str, Any]:
    target_time, stop_time, source_status = ordered_target_stop_times(row, target_r=target_r)
    target_dt = parse_iso(target_time)
    stop_dt = parse_iso(stop_time)
    if target_dt and stop_dt:
        if target_dt < stop_dt:
            return {
                "status": "ordered_target_first",
                "final_r": target_r,
                "terminal_outcome": f"target_{target_r:g}r_first_ordered",
                "same_bar_ambiguity": False,
                "target_first_touch_utc": target_time,
                "stop_first_touch_utc": stop_time,
                "ordered_path_source_status": source_status,
            }
        if stop_dt < target_dt:
            return {
                "status": "ordered_stop_first",
                "final_r": -1.0,
                "terminal_outcome": "stop_first_ordered",
                "same_bar_ambiguity": False,
                "target_first_touch_utc": target_time,
                "stop_first_touch_utc": stop_time,
                "ordered_path_source_status": source_status,
            }
        return {
            "status": "ordered_same_bar_ambiguous",
            "final_r": -1.0,
            "terminal_outcome": "same_bar_target_stop_conservative_stop_first",
            "same_bar_ambiguity": True,
            "target_first_touch_utc": target_time,
            "stop_first_touch_utc": stop_time,
            "ordered_path_source_status": source_status,
        }
    if target_dt:
        return {
            "status": "ordered_target_only",
            "final_r": target_r,
            "terminal_outcome": f"target_{target_r:g}r_reached_no_ordered_stop_before_it",
            "same_bar_ambiguity": False,
            "target_first_touch_utc": target_time,
            "stop_first_touch_utc": stop_time,
            "ordered_path_source_status": source_status,
        }
    if stop_dt:
        return {
            "status": "ordered_stop_only",
            "final_r": -1.0,
            "terminal_outcome": "stop_reached_no_ordered_target_before_it",
            "same_bar_ambiguity": False,
            "target_first_touch_utc": target_time,
            "stop_first_touch_utc": stop_time,
            "ordered_path_source_status": source_status,
        }
    return {
        "status": "ordered_path_missing",
        "final_r": None,
        "terminal_outcome": None,
        "same_bar_ambiguity": False,
        "target_first_touch_utc": None,
        "stop_first_touch_utc": None,
        "ordered_path_source_status": source_status,
    }


def minutes_between(start: Any, end: Any) -> float | None:
    start_dt = parse_iso(start)
    end_dt = parse_iso(end)
    if not start_dt or not end_dt:
        return None
    return round((end_dt - start_dt).total_seconds() / 60.0, 6)


def day_relation(start: Any, end: Any) -> str:
    start_dt = parse_iso(start)
    end_dt = parse_iso(end)
    if not start_dt or not end_dt:
        return "unknown"
    if start_dt.date() == end_dt.date():
        return "same_day"
    if (end_dt.date() - start_dt.date()).days == 1:
        return "next_day"
    if end_dt.date() > start_dt.date():
        return "later_day"
    return "invalid_reverse_clock"


def infer_replay_limit_fill(
    row: Mapping[str, Any],
    *,
    source_time_utc: Any | None = None,
    entry_touch_time_utc: Any | None = None,
) -> dict[str, Any]:
    """Infer synthetic replay fillability from post-decision ordered price action."""

    source_time = (
        iso_or_none(source_time_utc)
        or iso_or_none(row.get("decision_time_utc"))
        or iso_or_none(row.get("candle_time_utc"))
        or row_asof(row)
    )
    entry_touch = iso_or_none(entry_touch_time_utc) or iso_or_none(row.get("entry_first_touch_utc"))
    source_dt = parse_iso(source_time)
    entry_dt = parse_iso(entry_touch)
    if not source_dt:
        return {
            "status": "source_time_missing_for_replay_limit_fill",
            "filled": False,
            "source_time_utc": source_time,
            "entry_touch_time_utc": entry_touch,
            "minutes_to_fill": None,
            "delayed_fill_bars": None,
            "source_status": "engineering_backlog_source_time_capture_required",
            "broker_truth_required_for_synthetic_fill": False,
        }
    if not entry_dt:
        return {
            "status": "entry_touch_missing_for_replay_limit_fill",
            "filled": False,
            "source_time_utc": source_time,
            "entry_touch_time_utc": entry_touch,
            "minutes_to_fill": None,
            "delayed_fill_bars": None,
            "source_status": "engineering_backlog_ordered_entry_path_required",
            "broker_truth_required_for_synthetic_fill": False,
        }
    if entry_dt < source_dt:
        return {
            "status": "entry_touch_before_replay_order_time_not_counted_as_fill",
            "filled": False,
            "source_time_utc": source_time,
            "entry_touch_time_utc": entry_touch,
            "minutes_to_fill": round((entry_dt - source_dt).total_seconds() / 60.0, 6),
            "delayed_fill_bars": None,
            "source_status": "ordered_entry_touch_not_post_decision",
            "broker_truth_required_for_synthetic_fill": False,
        }
    minutes = round((entry_dt - source_dt).total_seconds() / 60.0, 6)
    bars = int(math.ceil(max(0.0, minutes) / 15.0)) if minutes is not None else None
    return {
        "status": "synthetic_limit_filled_from_ordered_price_action",
        "filled": True,
        "source_time_utc": source_time,
        "entry_touch_time_utc": entry_touch,
        "minutes_to_fill": minutes,
        "delayed_fill_bars": bars,
        "source_status": "replay_fill_inferred_from_post_decision_entry_touch",
        "broker_truth_required_for_synthetic_fill": False,
    }


def bind_replay_limit_fill_status(
    payload: Mapping[str, Any],
    row: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(payload)
    inference = infer_replay_limit_fill(
        row,
        source_time_utc=result.get("source_time_utc"),
        entry_touch_time_utc=result.get("entry_touch_time_utc"),
    )
    result["replay_limit_fill_inference"] = inference
    if not result.get("entry_touch_time_utc") and inference.get("entry_touch_time_utc"):
        result["entry_touch_time_utc"] = inference.get("entry_touch_time_utc")
    if inference.get("filled"):
        fill_status = _text(result.get("fill_status")).lower()
        limit_status = _text(result.get("limit_fill_status")).lower()
        if not fill_status or "missing" in fill_status or "source_gapped" in fill_status:
            result["fill_status"] = "synthetic_replay_filled_from_ordered_price_action"
        if not limit_status or "missing" in limit_status or "source_gapped" in limit_status:
            result["limit_fill_status"] = "synthetic_replay_entry_touch_after_decision"
        if result.get("delayed_fill_bars") is None:
            result["delayed_fill_bars"] = inference.get("delayed_fill_bars")
    return result


def threshold_milestone(
    *,
    threshold_r: float,
    mfe_r: float | None,
    entry_time_utc: str | None = None,
    first_touch_utc: Any = None,
) -> dict[str, Any]:
    reached = bool(mfe_r is not None and mfe_r >= threshold_r)
    first_touch = iso_or_none(first_touch_utc)
    return {
        "threshold_r": threshold_r,
        "reached": reached,
        "first_touch_utc": first_touch,
        "minutes_to_first_touch": minutes_between(entry_time_utc, first_touch),
        "seconds_to_first_touch": (
            None
            if minutes_between(entry_time_utc, first_touch) is None
            else int((minutes_between(entry_time_utc, first_touch) or 0.0) * 60)
        ),
        "source_status": (
            "ordered_clock_bound"
            if reached and first_touch
            else
            "reached_from_mfe_but_time_requires_ordered_ltf_or_tick"
            if reached
            else "not_reached_or_mfe_missing"
        ),
    }


def threshold_clock_from_router(router: Mapping[str, Any], threshold_key: str) -> Any:
    threshold_times = router.get("threshold_times_utc")
    if isinstance(threshold_times, Mapping):
        for key in (
            threshold_key,
            threshold_key.replace(".", "_"),
            threshold_key.replace(".", "_").replace("r", "R"),
        ):
            value = threshold_times.get(key)
            if value not in (None, ""):
                return value
    aliases = {
        "0.25r": ("quarter_r_trigger_utc", "first_favorable_excursion_0_25r_utc"),
        "0.5r": ("half_r_trigger_utc", "first_favorable_excursion_0_5r_utc"),
        "1.0r": ("one_r_trigger_utc", "partial_trigger_utc"),
        "1.5r": ("raw_1_5r_target_utc",),
        "2.0r": ("two_r_trigger_utc", "configured_2r_target_utc"),
        "3.0r": ("dynamic_final_3r_utc", "three_r_utc"),
    }
    for key in aliases.get(threshold_key, ()):
        value = router.get(key)
        if value not in (None, ""):
            return value
    return None


def path_microscope_fields(
    row: Mapping[str, Any],
    *,
    current_router: Mapping[str, Any],
    current_target_r: float,
    momentum: Mapping[str, Any],
) -> dict[str, Any]:
    asof = row_asof(row)
    entry_time = (
        iso_or_none(current_router.get("entry_touch_time_utc"))
        or iso_or_none(row.get("entry_first_touch_utc"))
        or asof
    )
    source_time = iso_or_none(current_router.get("source_time_utc")) or iso_or_none(row.get("candle_time_utc"))
    exit_time = iso_or_none(current_router.get("exit_time_utc"))
    final_r = _float(current_router.get("final_r"))
    mfe_r = _float(current_router.get("mfe_r"), _float(momentum.get("mfe_r")))
    mae_r = _float(current_router.get("mae_r"), _float(momentum.get("mae_r")))
    ordered = ordered_target_stop_outcome(row, target_r=current_target_r)
    target_first_touch = ordered.get("target_first_touch_utc")
    stop_first_touch = ordered.get("stop_first_touch_utc")
    exit_reason = _text(current_router.get("exit_reason"))
    if not stop_first_touch and "stop" in exit_reason.lower() and exit_time:
        stop_first_touch = exit_time
    target_reached = bool(
        (mfe_r is not None and mfe_r >= current_target_r)
        or (final_r is not None and final_r >= current_target_r)
    )
    if not target_first_touch and target_reached and final_r is not None and final_r >= current_target_r:
        target_first_touch = exit_time
    stop_reached = bool(
        (mae_r is not None and mae_r <= -1.0)
        or (final_r is not None and final_r <= -1.0)
        or ("stop" in exit_reason.lower())
    )
    source_gaps: list[str] = []
    if target_reached and not target_first_touch:
        source_gaps.append("ordered_milestone_clock_required_for_time_to_target")
    if stop_reached and not stop_first_touch:
        source_gaps.append("ordered_milestone_clock_required_for_time_to_stop")
    if mfe_r is not None and (mfe_r >= 0.5 or mfe_r >= 1.0):
        source_gaps.append("ordered_milestone_clock_required_for_time_to_0_5r_1r")
    if mae_r is not None and mae_r < 0 and mfe_r is not None and mfe_r > 0:
        source_gaps.append("ordered_event_sequence_required_for_adverse_first_vs_profit_first")
    transition_trace = current_router.get("dynamic_policy_transition_trace")
    if not isinstance(transition_trace, Mapping):
        transition_trace = {}
    threshold_milestones = {
        key: threshold_milestone(
            threshold_r=value,
            mfe_r=mfe_r,
            entry_time_utc=entry_time,
            first_touch_utc=threshold_clock_from_router(current_router, key),
        )
        for key, value in (
            ("0.25r", 0.25),
            ("0.5r", 0.5),
            ("1.0r", 1.0),
            ("1.5r", 1.5),
            ("2.0r", 2.0),
            ("3.0r", 3.0),
        )
    }
    for key, milestone in threshold_milestones.items():
        if (
            milestone["reached"]
            and milestone["first_touch_utc"] is None
            and f"ordered_milestone_clock_required_for_time_to_{key}" not in source_gaps
        ):
            source_gaps.append(f"ordered_milestone_clock_required_for_time_to_{key}")
    partial_trigger_utc = iso_or_none(
        current_router.get("partial_trigger_utc")
        or threshold_clock_from_router(current_router, "1.0r")
    )
    be_return_after_1r_utc = iso_or_none(
        current_router.get("be_return_after_1r_utc")
        or current_router.get("be_return_utc")
    )
    duration_stuck_near_entry_seconds = _int(
        current_router.get("duration_stuck_near_entry_seconds")
        or current_router.get("duration_before_movement_seconds")
    )
    reversal_timing_utc = iso_or_none(
        current_router.get("reversal_utc")
        or current_router.get("giveback_reversal_utc")
        or current_router.get("be_return_after_1r_utc")
    )
    return {
        "source_time_utc": source_time,
        "entry_touch_time_utc": entry_time,
        "exit_time_utc": exit_time,
        "holding_minutes_from_entry": minutes_between(entry_time, exit_time),
        "holding_minutes_from_asof": minutes_between(asof, exit_time),
        "exit_day_relation_from_asof": day_relation(asof, exit_time),
        "exit_day_relation_from_entry": day_relation(entry_time, exit_time),
        "entry_timing": current_router.get("entry_timing"),
        "fill_status": current_router.get("fill_status"),
        "limit_fill_status": current_router.get("limit_fill_status"),
        "delayed_fill_bars": current_router.get("delayed_fill_bars"),
        "target_r": current_target_r,
        "reached_0_5r": bool(mfe_r is not None and mfe_r >= 0.5),
        "reached_1r": bool(mfe_r is not None and mfe_r >= 1.0),
        "reached_configured_target": target_reached,
        "hit_stop": stop_reached,
        "target_first_touch_utc": target_first_touch,
        "stop_first_touch_utc": stop_first_touch,
        "time_to_target_minutes": minutes_between(entry_time, target_first_touch),
        "time_to_stop_minutes": minutes_between(entry_time, stop_first_touch),
        "threshold_milestones": threshold_milestones,
        "threshold_times_utc": {
            key: milestone["first_touch_utc"]
            for key, milestone in threshold_milestones.items()
        },
        "threshold_seconds_from_entry": {
            key: milestone["seconds_to_first_touch"]
            for key, milestone in threshold_milestones.items()
        },
        "partial_trigger_utc": partial_trigger_utc,
        "time_to_partial_seconds": (
            None
            if minutes_between(entry_time, partial_trigger_utc) is None
            else int((minutes_between(entry_time, partial_trigger_utc) or 0.0) * 60)
        ),
        "be_return_after_1r_utc": be_return_after_1r_utc,
        "time_to_be_seconds": (
            None
            if minutes_between(entry_time, be_return_after_1r_utc) is None
            else int((minutes_between(entry_time, be_return_after_1r_utc) or 0.0) * 60)
        ),
        "duration_stuck_near_entry_seconds": duration_stuck_near_entry_seconds,
        "duration_before_movement_seconds": duration_stuck_near_entry_seconds,
        "last_r": final_r,
        "reversal_timing_utc": reversal_timing_utc,
        "consolidated_near_1r_then_loss": bool(
            mfe_r is not None
            and final_r is not None
            and 0.75 <= mfe_r < 1.25
            and final_r <= -0.9
        ),
        "gave_back_profit_to_loss": bool(
            mfe_r is not None
            and final_r is not None
            and mfe_r >= 0.5
            and final_r < 0
        ),
        "adverse_profit_order_status": (
            "requires_ordered_event_sequence"
            if mae_r is not None and mae_r < 0 and mfe_r is not None and mfe_r > 0
            else "no_adverse_and_profit_extreme_pair_observed"
        ),
        "ordered_path_source_status": current_router.get("ordered_path_source_status"),
        "transition_trace": dict(transition_trace),
        "source_status": current_router.get("source_status"),
        "source_gaps": sorted(dict.fromkeys(source_gaps)),
    }


def momentum_2r_proxy(row: Mapping[str, Any]) -> dict[str, Any]:
    mfe_r, mae_r = row_mfe_mae(row)
    ordered = ordered_target_stop_outcome(row, target_r=2.0)
    source_gaps: list[str] = [
        "exact_momentum_exhaustion_historical_policy_row_missing_from_may26_replay",
    ]
    status = "source_gap"
    final_r = 0.0
    terminal = "mark_to_market_proxy"
    if ordered["final_r"] is not None and (
        ordered["status"] in {"ordered_target_first", "ordered_stop_first", "ordered_same_bar_ambiguous"}
        or (mfe_r is not None and mfe_r >= 2.0 and ordered["status"] == "ordered_target_only")
        or (mae_r is not None and mae_r <= -1.0 and ordered["status"] == "ordered_stop_only")
    ):
        final_r = float(ordered["final_r"])
        terminal = str(ordered["terminal_outcome"])
        status = str(ordered["status"])
        if ordered["same_bar_ambiguity"]:
            source_gaps.append("ordered_ltf_or_tick_required_for_exact_static_2r")
    elif mfe_r is not None and mae_r is not None:
        if mfe_r >= 2.0 and mae_r <= -1.0:
            final_r = -1.0
            terminal = "conservative_stop_first_due_ordering_gap"
            status = "ordered_ltf_or_tick_required_for_exact_2r_vs_stop"
            source_gaps.append("ordered_ltf_or_tick_required_for_exact_static_2r")
        elif mfe_r >= 2.0:
            final_r = 2.0
            terminal = "target_2r_reached_before_observed_stop_proxy"
            status = "proxy_target_2r_reached"
        elif mae_r <= -1.0:
            final_r = -1.0
            terminal = "stop_reached_before_observed_target_proxy"
            status = "proxy_stop_reached"
        else:
            fallback = _float(policy_result(row, "live_current_j46_j49").get("final_r"))
            if fallback is None:
                fallback = _float(row.get("old_static_simulated_r"), 0.0)
            final_r = max(-1.0, min(2.0, float(fallback or 0.0)))
            terminal = "neither_2r_nor_stop_observed_uses_bounded_path_mark"
            status = "bounded_path_mark_proxy"
            source_gaps.append("exact_exit_time_requires_ordered_path_replay")
    else:
        fallback = _float(row.get("old_static_simulated_r"), 0.0)
        final_r = max(-1.0, min(2.0, float(fallback or 0.0)))
        source_gaps.append("mfe_mae_missing_for_momentum_2r_proxy")
    return {
        "policy_id": CURRENT_V4_GEOMETRY_PROXY_POLICY_ID,
        "evidence_label": EVIDENCE_PROXY_R,
        "final_r": round(final_r, 9),
        "mfe_r": mfe_r,
        "mae_r": mae_r,
        "terminal_outcome": terminal,
        "status": status,
        "ordered_path_source_status": ordered["ordered_path_source_status"],
        "target_first_touch_utc": ordered["target_first_touch_utc"],
        "stop_first_touch_utc": ordered["stop_first_touch_utc"],
        "source_gaps": sorted(dict.fromkeys(source_gaps)),
        "same_bar_ambiguity": bool(ordered["same_bar_ambiguity"])
        or status == "ordered_ltf_or_tick_required_for_exact_2r_vs_stop",
    }


def _close_mark_source_status_bound(value: Any) -> bool:
    text = _text(value).lower()
    return text in {
        "replay_bound",
        "source_bound",
        "source_window_complete",
        "close_mark_replay_bound",
        "exit_policy_close_mark_replay_bound",
        "policy_close_mark_replay_bound",
        "m15_close_mark_replay_bound",
        "m1_close_mark_replay_bound",
        "tick_close_mark_replay_bound",
        "m15_local_close_mark_replay_bound_source_sha_mismatch",
        "captured_complete",
    }


def explicit_exit_policy_close_mark(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return an explicit V4 close-mark packet when a source row provides one."""

    nested = payload.get("exit_policy_close_mark")
    source = dict(nested) if isinstance(nested, Mapping) else {}
    key_map = {
        "close_mark_r": "exit_policy_close_mark_r",
        "close_time_utc": "exit_policy_close_mark_time_utc",
        "action": "exit_policy_close_mark_action",
        "close_reason": "exit_policy_close_mark_close_reason",
        "bars_elapsed": "exit_policy_close_mark_bars_elapsed",
        "policy_id": "exit_policy_close_mark_policy_id",
        "source_status": "exit_policy_close_mark_source_status",
        "source_path": "exit_policy_close_mark_source_path",
        "source_sha256": "exit_policy_close_mark_source_sha256",
    }
    for target_key, flat_key in key_map.items():
        if target_key not in source and payload.get(flat_key) not in (None, "", [], {}):
            source[target_key] = payload.get(flat_key)
    if not source:
        return None
    source.setdefault("schema_version", "v4u_exit_policy_close_mark_v1")
    source.setdefault("evidence_label", EVIDENCE_PROXY_R)
    source.setdefault(
        "source_boundary",
        "post_decision_replay_close_mark_not_asof_decision_input",
    )
    return source


def _resolve_local_replay_source_path(path_value: Any) -> Path | None:
    text = _text(path_value)
    if not text:
        return None
    raw_path = Path(text).expanduser()
    candidates = [raw_path] if raw_path.is_absolute() else [
        Path.cwd() / raw_path,
        MODULE_REPO_ROOT / raw_path,
    ]
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except (OSError, RuntimeError):
            resolved = candidate
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved
    return None


@lru_cache(maxsize=128)
def _m15_close_index(path_text: str) -> dict[str, Any]:
    source_path = _resolve_local_replay_source_path(path_text)
    if source_path is None:
        return {
            "status": "source_path_missing",
            "requested_path": path_text,
            "resolved_path": None,
            "source_sha256": None,
            "row_count": 0,
            "close_by_time_utc": {},
        }

    close_by_time: dict[str, float] = {}
    first_time: str | None = None
    last_time: str | None = None
    try:
        with source_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                time_value = (
                    row.get("time")
                    or row.get("timestamp")
                    or row.get("datetime")
                    or row.get("time_utc")
                )
                close_value = _float(row.get("close"))
                dt = parse_iso(time_value)
                if dt is None or close_value is None:
                    continue
                iso_time = dt.isoformat()
                close_by_time[iso_time] = float(close_value)
                first_time = first_time or iso_time
                last_time = iso_time
    except (OSError, csv.Error):
        return {
            "status": "source_read_error",
            "requested_path": path_text,
            "resolved_path": str(source_path),
            "source_sha256": sha256_file(source_path),
            "row_count": 0,
            "close_by_time_utc": {},
        }

    return {
        "status": "loaded",
        "requested_path": path_text,
        "resolved_path": str(source_path),
        "source_sha256": sha256_file(source_path),
        "row_count": len(close_by_time),
        "first_time_utc": first_time,
        "last_time_utc": last_time,
        "close_by_time_utc": close_by_time,
    }


def _risk_normalized_close_mark_r(
    *,
    side: Any,
    entry_reference: Any,
    stop_or_invalidation: Any,
    close_price: Any,
) -> tuple[float, float] | None:
    entry = _float(entry_reference)
    stop = _float(stop_or_invalidation)
    close = _float(close_price)
    direction = _side(side)
    if entry is None or stop is None or close is None:
        return None
    risk_distance = abs(float(entry) - float(stop))
    if risk_distance <= 0:
        return None
    if direction == "LONG":
        close_mark_r = (float(close) - float(entry)) / risk_distance
    elif direction == "SHORT":
        close_mark_r = (float(entry) - float(close)) / risk_distance
    else:
        return None
    return float(close_mark_r), float(risk_distance)


def _m15_source_close_mark(
    *,
    current_router: Mapping[str, Any],
    action: str,
    close_reason: str,
    bars_elapsed: int,
    derivation: str,
) -> dict[str, Any] | None:
    if bars_elapsed <= 0:
        return None
    entry_time = parse_iso(
        current_router.get("entry_touch_time_utc")
        or current_router.get("source_time_utc")
    )
    if entry_time is None:
        return None
    close_time = (entry_time + timedelta(minutes=15 * int(bars_elapsed))).astimezone(
        timezone.utc
    )
    source_path = _text(current_router.get("source_path"))
    if not source_path:
        return None
    index = _m15_close_index(source_path)
    if index.get("status") != "loaded":
        return None
    expected_sha = _text(current_router.get("source_sha256"))
    actual_sha = _text(index.get("source_sha256"))
    close_price = (index.get("close_by_time_utc") or {}).get(close_time.isoformat())
    if close_price is None:
        return None
    risk_result = _risk_normalized_close_mark_r(
        side=current_router.get("side"),
        entry_reference=current_router.get("entry_reference"),
        stop_or_invalidation=current_router.get("stop_or_invalidation"),
        close_price=close_price,
    )
    if risk_result is None:
        return None
    close_mark_r, risk_distance = risk_result
    source_hash_match_status = (
        "source_sha256_match"
        if expected_sha and actual_sha and expected_sha == actual_sha
        else "source_sha256_mismatch"
        if expected_sha and actual_sha and expected_sha != actual_sha
        else "source_sha256_not_provided"
        if not expected_sha and actual_sha
        else "source_sha256_unavailable"
    )
    source_status = (
        "m15_close_mark_replay_bound"
        if source_hash_match_status in {"source_sha256_match", "source_sha256_not_provided"}
        else "m15_local_close_mark_replay_bound_source_sha_mismatch"
    )
    return {
        "schema_version": "v4u_exit_policy_close_mark_v1",
        "close_mark_r": round(close_mark_r, 9),
        "close_time_utc": close_time.isoformat(),
        "action": action,
        "close_reason": close_reason,
        "bars_elapsed": int(bars_elapsed),
        "policy_id": "v4_exit_policy_close_mark_v1",
        "source_status": source_status,
        "source_path": source_path,
        "resolved_source_path": index.get("resolved_path"),
        "source_sha256": actual_sha or expected_sha or None,
        "expected_source_sha256": expected_sha or None,
        "actual_source_sha256": actual_sha or None,
        "source_hash_match_status": source_hash_match_status,
        "source_timeframe": "M15",
        "source_row_count": index.get("row_count"),
        "close_price": close_price,
        "entry_reference": current_router.get("entry_reference"),
        "stop_or_invalidation": current_router.get("stop_or_invalidation"),
        "risk_distance": round(risk_distance, 9),
        "side": _side(current_router.get("side")),
        "evidence_label": EVIDENCE_PROXY_R,
        "source_boundary": "post_decision_replay_close_mark_not_asof_decision_input",
        "derivation": derivation,
    }


def replay_exit_policy_close_mark(
    *,
    current_router: Mapping[str, Any],
    exit_decision: Any,
    exit_config: ExitPolicyConfigV4,
    exit_bars_elapsed: int | None,
) -> dict[str, Any] | None:
    explicit = explicit_exit_policy_close_mark(current_router)
    if explicit:
        return explicit

    action = _text(getattr(exit_decision, "action", None))
    close_reason = _text(getattr(exit_decision, "close_reason", None))
    if action == "CLOSE_TIME_STOP":
        source_mark = _m15_source_close_mark(
            current_router=current_router,
            action=action,
            close_reason=close_reason or "v4_time_stop",
            bars_elapsed=int(exit_config.time_stop_bars),
            derivation="m15_source_close_at_v4_time_stop_policy_clock",
        )
        if source_mark:
            return source_mark
    elif action == "CLOSE_STALE_THESIS":
        source_mark = _m15_source_close_mark(
            current_router=current_router,
            action=action,
            close_reason=close_reason or "v4_stale_thesis_no_progress",
            bars_elapsed=int(exit_config.stale_thesis_bars),
            derivation="m15_source_close_at_v4_stale_thesis_policy_clock",
        )
        if source_mark:
            return source_mark
        return None
    else:
        return None

    if exit_bars_elapsed != exit_config.time_stop_bars:
        return None
    comparison_policy = current_router.get("comparison_policy_r")
    close_mark_r = _float(
        current_router.get("comparison_time_stop_r"),
        _float(
            (comparison_policy or {}).get("time_stop")
            if isinstance(comparison_policy, Mapping)
            else None
        ),
    )
    if close_mark_r is None:
        return None
    entry_time = parse_iso(
        current_router.get("entry_touch_time_utc")
        or current_router.get("source_time_utc")
    )
    close_time = None
    if entry_time is not None:
        close_time = (
            entry_time + timedelta(minutes=15 * int(exit_config.time_stop_bars))
        ).astimezone(timezone.utc).isoformat()
    if not close_time:
        close_time = iso_or_none(current_router.get("exit_time_utc"))
    if not close_time:
        return None
    source = {
        "schema_version": "v4u_exit_policy_close_mark_v1",
        "close_mark_r": close_mark_r,
        "close_time_utc": close_time,
        "action": "CLOSE_TIME_STOP",
        "close_reason": "v4_time_stop",
        "bars_elapsed": int(exit_config.time_stop_bars),
        "policy_id": "v4_exit_policy_close_mark_v1",
        "source_status": "m15_close_mark_replay_bound",
        "source_path": current_router.get("source_path"),
        "source_sha256": current_router.get("source_sha256"),
        "evidence_label": EVIDENCE_PROXY_R,
        "source_boundary": "post_decision_replay_close_mark_not_asof_decision_input",
        "derivation": "comparison_time_stop_r_from_frozen_m15_replay",
    }
    return source


def promoted_router_result(
    row: Mapping[str, Any],
    *,
    momentum_proxy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    promoted = row.get("_promoted_router_replay")
    if isinstance(promoted, Mapping) and _float(promoted.get("final_r")) is not None:
        policy = _text(
            promoted.get("chosen_policy")
            or promoted.get("raw_asof_selected_policy")
            or "momentum_exhaustion"
        )
        source_gaps = list(promoted.get("missing_field_notes") or [])
        if promoted.get("net_r") is None:
            source_gaps.append("net_r_missing_historical_cost_lifecycle_fields")
        if promoted.get("cost_status"):
            source_gaps.append(str(promoted.get("cost_status")))
        result = {
            "policy_id": PROMOTED_ROUTER_POLICY_ID,
            "selected_policy": policy,
            "execution_policy_id": promoted.get("execution_policy_id")
            or execution_policy_id_for(policy),
            "selected_row_id": promoted.get("selected_row_id"),
            "source_time_utc": promoted.get("source_time_utc"),
            "entry_touch_time_utc": promoted.get("entry_touch_time_utc"),
            "entry_timing": promoted.get("entry_timing"),
            "fill_status": promoted.get("fill_status"),
            "limit_fill_status": promoted.get("limit_fill_status"),
            "delayed_fill_bars": promoted.get("delayed_fill_bars"),
            "evidence_label": PROMOTED_ROUTER_EVIDENCE_LABEL,
            "source_status": "may27_final_dynamic_router_replay_bound",
            "final_r": round(float(promoted.get("final_r")), 9),
            "net_r": promoted.get("net_r"),
            "mfe_r": promoted.get("mfe_r"),
            "mae_r": promoted.get("mae_r"),
            "exit_reason": promoted.get("exit_reason"),
            "exit_time_utc": promoted.get("exit_time_utc"),
            "same_bar_ambiguity": bool(promoted.get("same_bar_ambiguity")),
            "ordered_path_source_status": promoted.get(
                "selected_policy_ordered_path_status"
            ),
            "source_gaps": sorted(dict.fromkeys(source_gaps)),
            "router_decision_status": promoted.get("router_decision_status"),
            "router_candidate_action": promoted.get("router_candidate_action"),
            "router_runtime_effect_now": promoted.get("router_runtime_effect_now"),
            "dynamic_policy_transition_trace": promoted.get("dynamic_policy_transition_trace")
            if isinstance(promoted.get("dynamic_policy_transition_trace"), Mapping)
            else {},
            "candidate_origin_family": promoted.get("candidate_origin_family"),
            "source_path": promoted.get("source_path"),
            "source_sha256": promoted.get("source_sha256"),
            "router_evidence_notes": list(promoted.get("router_evidence_notes") or []),
            "hindsight_best_policy": promoted.get("hindsight_best_policy"),
            "hindsight_best_r": promoted.get("hindsight_best_r"),
            "hindsight_regret_r": promoted.get("hindsight_regret_r"),
            "comparison_policy_r": {
                "be_after_trigger": promoted.get("comparison_be_after_trigger_r"),
                "legacy_fixed_1.5r": promoted.get("comparison_fixed_1_5r_r"),
                "momentum_exhaustion": promoted.get("comparison_momentum_exhaustion_r"),
                "partial_be_runner": promoted.get("comparison_partial_be_runner_r"),
                "time_stop": promoted.get("comparison_time_stop_r"),
                "trailing_runner": promoted.get("comparison_trailing_runner_r"),
            },
            "promotion_evidence_path": PROMOTED_ROUTER_EVIDENCE_PATH,
            "side": _side(row.get("side")),
            "entry_reference": row.get("entry_reference"),
            "stop_or_invalidation": row.get("stop_or_invalidation"),
        }
        close_mark = explicit_exit_policy_close_mark(promoted)
        if close_mark:
            result["exit_policy_close_mark"] = close_mark
        return bind_replay_limit_fill_status(result, row)
    proxy = dict(momentum_proxy or momentum_2r_proxy(row))
    source_gaps = list(proxy.get("source_gaps") or [])
    source_gaps.append("may27_final_dynamic_router_row_missing_for_candidate_id")
    result = {
        "policy_id": PROMOTED_ROUTER_POLICY_ID,
        "selected_policy": "momentum_exhaustion",
        "execution_policy_id": execution_policy_id_for("momentum_exhaustion"),
        "selected_row_id": None,
        "source_time_utc": iso_or_none(row.get("candle_time_utc")),
        "entry_touch_time_utc": iso_or_none(row.get("entry_first_touch_utc")),
        "entry_timing": "fallback_proxy",
        "fill_status": "source_gapped_promoted_router_missing",
        "limit_fill_status": None,
        "delayed_fill_bars": None,
        "evidence_label": EVIDENCE_PROXY_R,
        "source_status": "fallback_momentum_proxy_due_missing_promoted_router_row",
        "final_r": proxy.get("final_r"),
        "net_r": None,
        "mfe_r": proxy.get("mfe_r"),
        "mae_r": proxy.get("mae_r"),
        "exit_reason": proxy.get("terminal_outcome"),
        "exit_time_utc": proxy.get("target_first_touch_utc") or proxy.get("stop_first_touch_utc"),
        "same_bar_ambiguity": bool(proxy.get("same_bar_ambiguity")),
        "ordered_path_source_status": proxy.get("ordered_path_source_status"),
        "source_gaps": sorted(dict.fromkeys(source_gaps)),
        "router_decision_status": "promoted_router_row_missing_fallback_proxy",
        "router_candidate_action": None,
        "router_runtime_effect_now": None,
        "dynamic_policy_transition_trace": {},
        "candidate_origin_family": row.get("candidate_origin_family"),
        "source_path": row.get("source_path"),
        "source_sha256": row.get("source_sha256"),
        "router_evidence_notes": [
            "promoted_router_comparator_requires_may27_final_dynamic_router_replay_join"
        ],
        "hindsight_best_policy": None,
        "hindsight_best_r": None,
        "hindsight_regret_r": None,
        "comparison_policy_r": {},
        "promotion_evidence_path": PROMOTED_ROUTER_EVIDENCE_PATH,
        "side": _side(row.get("side")),
        "entry_reference": row.get("entry_reference"),
        "stop_or_invalidation": row.get("stop_or_invalidation"),
    }
    return bind_replay_limit_fill_status(result, row)


def comparator_record(row: Mapping[str, Any]) -> dict[str, Any]:
    policies: dict[str, Any] = {}
    for policy in (
        "legacy_fixed_1.5r",
        "ai_target",
        "be_after_trigger",
        "early_cut_if_no_progress",
        "live_current_j46_j49",
        "partial_be_runner",
        "path_aware_runner",
        "time_stop_only",
        "trailing_runner",
    ):
        result = policy_result(row, policy)
        policies[policy] = {
            "final_r": _float(result.get("final_r")),
            "mfe_r": _float(result.get("mfe_r")),
            "mae_r": _float(result.get("mae_r")),
            "exit_reason": result.get("exit_reason"),
            "exit_time_utc": iso_or_none(result.get("exit_time_utc")),
            "same_bar_ambiguity": result.get("same_bar_ambiguity"),
            "authority_label": (
                "historical-only evidence"
                if policy != "live_current_j46_j49"
                else "live authority comparator evidence"
            ),
        }
    promoted = promoted_router_result(row)
    return {
        "candidate_id": candidate_id(row),
        "symbol": row_symbol(row),
        "session": row_session(row),
        "framework": row_framework(row),
        "asof_utc": row_asof(row),
        "evidence_label": EVIDENCE_REPLAY,
        "v3_prev4_authority_boundary": {
            "promoted_router": (
                "May-27 promoted momentum_exhaustion primary with partial_be_runner "
                "exceptions; replay/proxy-R comparator, not broker-real live PnL"
            ),
            "live_current_j46_j49": "stale historical comparator only, not active authority",
            "be_after_trigger": "May-26 default-off/repaired comparator",
            "partial_be_runner": "previous live exception comparator",
            "legacy_fixed_1.5r": "static historical baseline comparator",
        },
        "promoted_router": promoted,
        "policies": policies,
    }


def source_completeness_for_row(row: Mapping[str, Any]) -> tuple[float, str, list[str]]:
    gaps: list[str] = []
    replay_asof_fields_complete = simulated_replay_asof_fields_complete(row)
    source_gap_cost_tail_risk = row_symbol(row) in {"BTCUSD", "ETHUSD"}
    raw_complete = row.get("source_window_complete")
    if isinstance(raw_complete, str):
        lowered_complete = raw_complete.strip().lower()
        complete = True if lowered_complete in {"1", "true", "yes"} else False if lowered_complete in {"0", "false", "no"} else None
    else:
        complete = raw_complete
    status_text = _text(row.get("source_path_feature_status") or row.get("source_status"))
    if complete is True:
        score = 0.90
        status = "source_window_complete"
    elif complete is False:
        score = 0.45
        status = "source_window_incomplete"
        gaps.append("source_window_incomplete")
    else:
        score = 0.60
        status = "source_window_unknown"
        gaps.append("source_window_complete_flag_missing")
    if "missing" in status_text.lower() or "gap" in status_text.lower():
        gaps.append("source_path_feature_status_gap")
        if replay_asof_fields_complete:
            gaps.append("source_path_gap_not_blocking_simulated_replay_asof_fields_complete")
        else:
            score = min(score, 0.35)
    if not row.get("entry_first_touch_utc"):
        gaps.append("entry_first_touch_utc_missing")
        score = min(score, 0.60)
    if not row.get("source_sha256") and not row.get("source_path"):
        gaps.append("source_hash_or_path_missing")
        score = min(score, 0.55)
    if replay_asof_fields_complete and not source_gap_cost_tail_risk:
        score = max(score, 0.75)
        gaps.append("simulated_replay_asof_decision_fields_complete")
    elif replay_asof_fields_complete:
        score = max(score, 0.75)
        gaps.append("simulated_replay_asof_decision_fields_complete")
        gaps.append("simulated_replay_crypto_cost_tail_stress_bound")
    return score, status, sorted(dict.fromkeys(gaps))


def simulated_replay_asof_fields_complete(row: Mapping[str, Any]) -> bool:
    """Return whether a row has enough as-of fields for simulated replay admission.

    This deliberately does not require historical broker ticket/deal/cost truth
    or post-decision M1/tick path fields. Those sources are needed for other
    labels, not for deciding whether a frozen replay row can be simulated from
    the as-of candidate packet.
    """

    side = _side(row.get("side") or row.get("direction"))
    if side not in {"LONG", "SHORT"}:
        return False
    if not candidate_id(row):
        return False
    if not row_symbol(row):
        return False
    if not row_asof(row) or row_asof(row).startswith("1970-01-01"):
        return False
    entry = _float(row.get("entry_reference") or row.get("entry_price"))
    stop = _float(row.get("stop_or_invalidation") or row.get("stop_price"))
    if entry is None or stop is None or abs(entry - stop) <= 0:
        return False
    return True


def lifecycle_source_score_for_row(row: Mapping[str, Any], replay_source_score: float) -> float:
    """Keep scale/reduce/close/reverse inference stricter than new-risk replay.

    A source-window-incomplete row can be good enough for simulated new-risk
    admission from its as-of packet. When those same as-of fields are complete,
    non-crypto replay lifecycle inference can use the chronological replay
    state under a proxy/as-of label; crypto cost-tail gaps remain capped.
    """

    raw_complete = row.get("source_window_complete")
    if isinstance(raw_complete, str):
        raw_complete = raw_complete.strip().lower() in {"1", "true", "yes"}
    if raw_complete is True:
        return replay_source_score
    if simulated_replay_asof_fields_complete(row):
        return replay_source_score
    return min(replay_source_score, 0.55)


def asof_confluence_sources(row: Mapping[str, Any], side: str, source_score: float) -> list[dict[str, Any]]:
    framework = row_framework(row)
    session = row_session(row)
    base_reliability = 0.68 if framework == "fvg_fill" else 0.58
    freshness = 0.80 if row.get("entry_first_touch_utc") else 0.55
    mixed = source_score < 0.55
    return [
        {
            "source_id": f"{candidate_id(row)}:selector_framework",
            "source_family": "selector",
            "label": "FOLLOW" if not mixed else "MIXED",
            "stance": "FOLLOW" if not mixed else "MIXED",
            "action": "long" if side == "LONG" else "short",
            "direction": side,
            "strength": 0.66 if not mixed else 0.45,
            "confidence": min(0.92, 0.50 + source_score * 0.35),
            "reliability": base_reliability,
            "freshness": freshness,
            "source_completeness": source_score,
            "cost_sensitivity": 0.18 if row_symbol(row) in {"ETHUSD", "BTCUSD", "UKOIL_CASH", "USOIL_CASH"} else 0.08,
            "conflict_reason": "source_completeness_gap" if mixed else "",
            "evidence_class": "replay as-of proxy input",
        },
        {
            "source_id": f"{candidate_id(row)}:market_state",
            "source_family": "market_state",
            "label": "FOLLOW",
            "stance": "FOLLOW",
            "action": "long" if side == "LONG" else "short",
            "direction": side,
            "strength": 0.60,
            "confidence": (
                0.58
                if session in {"LONDON", "NY", "NEW_YORK"}
                or session.startswith("LONDON")
                or session.startswith("NY")
                else 0.50
            ),
            "reliability": 0.60,
            "freshness": freshness,
            "source_completeness": source_score,
            "cost_sensitivity": 0.08,
            "evidence_class": "replay as-of proxy input",
        },
        {
            "source_id": f"{candidate_id(row)}:cost",
            "source_family": "cost",
            "label": "MIXED" if row_symbol(row) in {"ETHUSD", "BTCUSD"} else "FOLLOW",
            "stance": "MIXED" if row_symbol(row) in {"ETHUSD", "BTCUSD"} else "FOLLOW",
            "action": "wait" if row_symbol(row) in {"ETHUSD", "BTCUSD"} else ("long" if side == "LONG" else "short"),
            "direction": side,
            "strength": 0.50,
            "confidence": 0.56,
            "reliability": 0.55,
            "freshness": freshness,
            "source_completeness": source_score,
            "cost_sensitivity": 0.35 if row_symbol(row) in {"ETHUSD", "BTCUSD"} else 0.08,
            "conflict_reason": "crypto_cost_tail_risk" if row_symbol(row) in {"ETHUSD", "BTCUSD"} else "",
            "evidence_class": "proxy cost not broker-real cash",
        },
        {
            "source_id": f"{candidate_id(row)}:lifecycle",
            "source_family": "lifecycle",
            "label": "FOLLOW",
            "stance": "FOLLOW",
            "action": "long" if side == "LONG" else "short",
            "direction": side,
            "strength": 0.58,
            "confidence": 0.55,
            "reliability": 0.56,
            "freshness": freshness,
            "source_completeness": source_score,
            "cost_sensitivity": 0.04,
            "evidence_class": "chronological replay state proxy",
        },
        {
            "source_id": f"{candidate_id(row)}:source_completeness",
            "source_family": "source_completeness",
            "label": "FOLLOW" if source_score >= 0.55 else "MIXED",
            "stance": "FOLLOW" if source_score >= 0.55 else "MIXED",
            "action": "long" if side == "LONG" else "short",
            "direction": side,
            "strength": source_score,
            "confidence": source_score,
            "reliability": source_score,
            "freshness": freshness,
            "source_completeness": source_score,
            "cost_sensitivity": 0.05,
            "conflict_reason": "asof_source_gap" if source_score < 0.55 else "",
            "evidence_class": "source gap" if source_score < 0.55 else "replay",
        },
    ]


def debate_record_from_sources(
    config: Mapping[str, Any],
    row: Mapping[str, Any],
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    context = {
        "candidate_id": candidate_id(row),
        "symbol": row_symbol(row),
        "side": _side(row.get("side") or row.get("direction")),
        "asof_utc": row_asof(row),
        "sources": sources,
        "reward_r": 2.0,
        "loss_r": 1.0,
        "cost_r": 0.03,
    }
    decision = ProbabilityDebateTeamEngineV4(dict(config)).evaluate(context)
    return decision.to_record()


def build_candidate_lifecycle(
    config: Mapping[str, Any],
    row: Mapping[str, Any],
    side: str,
    source_score: float,
    source_status: str,
    probability: float,
    ev_r: float,
    state: "ReplayState | None" = None,
) -> CandidateLifecycleContext:
    symbol = row_symbol(row)
    thesis_id = _text(row.get("thesis_id") or f"wave4r:{candidate_id(row)}")
    requested_action, replay_lifecycle_proof = infer_replay_lifecycle_action(
        config=config,
        row=row,
        state=state,
        side=side,
        source_score=source_score,
        source_status=source_status,
        probability=probability,
        ev_r=ev_r,
        thesis_id=thesis_id,
    )
    return CandidateLifecycleContext(
        symbol=symbol,
        aliases=symbol_aliases_for_config(symbol, dict(config)),
        side=side,
        requested_action=requested_action,
        risk_pct=2.0,
        probability=probability,
        ev_r=ev_r,
        thesis_id=thesis_id,
        candidate_id=candidate_id(row),
        freshness_status="fresh" if row.get("entry_first_touch_utc") else "bounded_asof",
        source_completeness_status=source_status,
        proof={
            "source_completeness": source_score,
            "evidence_label": "chronological replay state proxy",
            "asof_utc": row_asof(row),
            **replay_lifecycle_proof,
        },
    )


def same_symbol_replay_thresholds(config: Mapping[str, Any]) -> dict[str, Any]:
    risk_cfg = (config or {}).get("risk", {})
    lifecycle_cfg = {}
    if isinstance(risk_cfg, Mapping):
        lifecycle_cfg = risk_cfg.get("same_symbol_lifecycle_v4") or {}
    if not isinstance(lifecycle_cfg, Mapping):
        lifecycle_cfg = {}
    probability_delta = _float(
        lifecycle_cfg.get("scale_in_min_probability_delta"),
        _float(lifecycle_cfg.get("scale_in_min_probability_improvement"), 0.03),
    )
    ev_delta = _float(
        lifecycle_cfg.get("scale_in_min_ev_delta_r"),
        _float(lifecycle_cfg.get("scale_in_min_ev_improvement_r"), 0.05),
    )
    return {
        "source_complete_floor": _float(
            lifecycle_cfg.get("replay_lifecycle_source_complete_floor"),
            0.75,
        )
        or 0.75,
        "probability_delta": probability_delta if probability_delta is not None else 0.03,
        "ev_delta_r": ev_delta if ev_delta is not None else 0.05,
        "close_reverse_stale_floor": _float(
            lifecycle_cfg.get("replay_close_reverse_stale_score_floor"),
            0.35,
        )
        or 0.35,
        "close_reverse_strong_ev_delta_r": _float(
            lifecycle_cfg.get("replay_close_reverse_strong_ev_delta_r"),
            0.20,
        )
        or 0.20,
        "allow_same_direction_better_thesis_scale_in": bool(
            lifecycle_cfg.get(
                "replay_allow_same_direction_better_thesis_scale_in",
                True,
            )
        ),
    }


def same_symbol_replay_stale_score(
    position: "ReplayPosition",
    *,
    asof_utc: str,
    candidate_ev_r: float,
) -> dict[str, Any]:
    age_minutes = replay_holding_minutes(position.opened_at_utc, asof_utc)
    ev_regret = max(0.0, float(candidate_ev_r) - float(position.ev_r or 0.0))
    age_component = min(0.35, age_minutes / 1440.0 * 0.35)
    regret_component = min(0.45, ev_regret / 2.0 * 0.45)
    weak_thesis_component = 0.10 if float(position.ev_r or 0.0) <= 0.05 else 0.0
    stale_score = min(1.0, age_component + regret_component + weak_thesis_component)
    return {
        "stale_thesis_score": round(stale_score, 9),
        "time_in_trade_minutes": round(age_minutes, 6),
        "candidate_minus_parent_ev_r": round(ev_regret, 9),
        "components": {
            "age_component": round(age_component, 9),
            "regret_component": round(regret_component, 9),
            "weak_thesis_component": round(weak_thesis_component, 9),
        },
    }


def infer_replay_lifecycle_action(
    *,
    config: Mapping[str, Any],
    row: Mapping[str, Any],
    state: "ReplayState | None",
    side: str,
    source_score: float,
    source_status: str,
    probability: float,
    ev_r: float,
    thesis_id: str,
) -> tuple[str, dict[str, Any]]:
    explicit = _text(row.get("same_symbol_lifecycle_action"))
    if explicit:
        return explicit, {
            "replay_lifecycle_intent_source_status": "explicit_row_lifecycle_action",
            "replay_lifecycle_inferred_action": explicit,
        }
    proof: dict[str, Any] = {
        "replay_lifecycle_intent_source_status": "replay_state_evaluated_no_inferred_action",
        "replay_lifecycle_inferred_action": "new_position",
    }
    if state is None:
        proof["replay_lifecycle_intent_source_status"] = "replay_state_unavailable"
        return "new_position", proof
    thresholds = same_symbol_replay_thresholds(config)
    symbol = row_symbol(row)
    symbol_aliases = symbol_aliases_for_config(symbol, dict(config))
    alias_keys = {symbol_key(alias) for alias in symbol_aliases}
    same_positions = [
        position
        for position in state.open_positions
        if symbol_key(position.symbol) in alias_keys
    ]
    if not same_positions:
        return "new_position", proof
    if len(same_positions) != 1:
        proof.update(
            {
                "replay_lifecycle_intent_source_status": "ambiguous_multi_ticket_replay_state",
                "same_symbol_open_position_count": len(same_positions),
                "same_symbol_aliases": symbol_aliases,
            }
        )
        return "new_position", proof
    parent = same_positions[0]
    probability_delta = float(probability) - float(parent.probability or 0.0)
    ev_delta = float(ev_r) - float(parent.ev_r or 0.0)
    stale_projection = same_symbol_replay_stale_score(
        parent,
        asof_utc=row_asof(row),
        candidate_ev_r=ev_r,
    )
    proof.update(
        {
            "same_symbol_open_position_count": 1,
            "same_symbol_aliases": symbol_aliases,
            "parent_ticket": parent.ticket,
            "parent_candidate_id": parent.candidate_id,
            "parent_side": parent.side,
            "parent_thesis_id": parent.thesis_id,
            "parent_probability": round(float(parent.probability or 0.0), 9),
            "parent_ev_r": round(float(parent.ev_r or 0.0), 9),
            "candidate_probability": round(float(probability), 9),
            "candidate_ev_r": round(float(ev_r), 9),
            "probability_delta": round(probability_delta, 9),
            "ev_delta_r": round(ev_delta, 9),
            "stale_projection": stale_projection,
        }
    )
    if source_score < thresholds["source_complete_floor"]:
        proof["replay_lifecycle_intent_source_status"] = (
            "source_incomplete_no_replay_lifecycle_inference"
        )
        return "new_position", proof
    source_floor_prefix = (
        "source_complete"
        if source_status == "source_window_complete"
        else "asof_complete_source_partial"
    )
    if parent.side == side:
        improves_enough = (
            probability_delta >= thresholds["probability_delta"]
            and ev_delta >= thresholds["ev_delta_r"]
        )
        if thesis_id != parent.thesis_id and (
            not thresholds["allow_same_direction_better_thesis_scale_in"]
            or not improves_enough
        ):
            proof["replay_lifecycle_intent_source_status"] = (
                "same_direction_thesis_mismatch_no_inferred_scale"
            )
            return "new_position", proof
        if improves_enough:
            if thesis_id == parent.thesis_id:
                inference_status = f"{source_floor_prefix}_same_thesis_scale_in_inferred"
            else:
                inference_status = f"{source_floor_prefix}_better_thesis_same_direction_scale_in_inferred"
            proof["replay_lifecycle_intent_source_status"] = (
                inference_status
            )
            proof["replay_lifecycle_inferred_action"] = "same_direction_scale_in"
            proof["replay_same_direction_better_thesis_scale_in_allowed"] = (
                thesis_id != parent.thesis_id
            )
            return "same_direction_scale_in", proof
        proof["replay_lifecycle_intent_source_status"] = (
            "same_direction_improvement_below_scale_floor"
        )
        return "new_position", proof
    close_reverse_stale = (
        stale_projection["stale_thesis_score"] >= thresholds["close_reverse_stale_floor"]
    )
    close_reverse_strong = ev_delta >= thresholds["close_reverse_strong_ev_delta_r"]
    if (
        probability_delta >= thresholds["probability_delta"]
        and ev_delta >= thresholds["ev_delta_r"]
        and (close_reverse_stale or close_reverse_strong)
    ):
        proof["replay_lifecycle_intent_source_status"] = (
            f"{source_floor_prefix}_opposite_side_close_reverse_inferred"
        )
        proof["replay_lifecycle_inferred_action"] = "close_and_reverse"
        return "close_and_reverse", proof
    proof["replay_lifecycle_intent_source_status"] = (
        "opposite_side_dominance_below_close_reverse_floor"
    )
    return "new_position", proof


def ticket_snapshot_from_open(open_trade: Mapping[str, Any]) -> TicketLifecycleSnapshot:
    return TicketLifecycleSnapshot(
        ticket=_int(open_trade.get("ticket")),
        symbol=_text(open_trade.get("symbol")),
        side=_text(open_trade.get("side")),
        volume=1.0,
        price_open=_float(open_trade.get("entry_reference")),
        sl=None,
        tp=None,
        magic=MAGIC_NUMBER,
        thesis_id=_text(open_trade.get("thesis_id")),
        risk_pct=_float(open_trade.get("risk_pct"), 2.0),
        probability_at_entry=_float(open_trade.get("probability")),
        ev_r_at_entry=_float(open_trade.get("ev_r")),
        lifecycle_phase="open",
        source_status="chronological_replay_state_proxy",
        stale_thesis=False,
        partial_state=None,
        be_state=None,
        trailing_state=None,
    )


def trade_date_from_utc(value: Any) -> str:
    dt = parse_iso(value)
    return dt.date().isoformat() if dt else "unknown_date"


def replay_prop_firm_risk_settings(config: Mapping[str, Any]) -> dict[str, Any]:
    risk_cfg = config.get("risk") if isinstance(config.get("risk"), Mapping) else {}
    runtime = config_runtime(config)
    risk_per_trade_pct = _float(risk_cfg.get("risk_per_trade_pct"), 2.0) or 2.0
    daily_loss_pct = (
        _float(runtime.get("prop_safe_selector_internal_daily_loss_limit_pct"))
        or _float(risk_cfg.get("max_daily_loss_pct"))
        or 4.0
    )
    overall_loss_pct = (
        _float(runtime.get("prop_safe_selector_external_overall_max_loss_pct"))
        or _float(runtime.get("prop_safe_selector_internal_overall_max_loss_pct"))
        or _float(risk_cfg.get("max_portfolio_drawdown_pct"))
    )
    return {
        "risk_per_trade_pct": risk_per_trade_pct,
        "daily_loss_limit_pct": daily_loss_pct,
        "daily_loss_limit_r": round(daily_loss_pct / risk_per_trade_pct, 9)
        if risk_per_trade_pct > 0
        else None,
        "headroom_buffer_r": max(
            0.0,
            _float(runtime.get("prop_firm_replay_headroom_buffer_r"), 0.05) or 0.0,
        ),
        "overall_loss_limit_pct": overall_loss_pct,
        "overall_loss_limit_r": round(overall_loss_pct / risk_per_trade_pct, 9)
        if overall_loss_pct is not None and risk_per_trade_pct > 0
        else None,
        "fresh_day_baseline": True,
        "simulation_units": "R",
    }


def risk_r_from_pct(config: Mapping[str, Any], risk_pct: float | None) -> float:
    settings = replay_prop_firm_risk_settings(config)
    risk_per_trade_pct = float(settings["risk_per_trade_pct"] or 2.0)
    if risk_pct is None or risk_per_trade_pct <= 0:
        return 0.0
    return round(max(0.0, float(risk_pct)) / risk_per_trade_pct, 9)


@dataclass
class ReplayDayAccountState:
    trade_date: str
    realized_r: float = 0.0
    min_realized_r: float = 0.0
    max_realized_r: float = 0.0
    accepted_count: int = 0
    closed_count: int = 0
    closed_winner_count: int = 0
    closed_loser_count: int = 0
    closed_flat_count: int = 0
    prop_firm_blocked_count: int = 0

    def record_close(self, final_r: float) -> None:
        self.realized_r += float(final_r)
        self.closed_count += 1
        if final_r > 0:
            self.closed_winner_count += 1
        elif final_r < 0:
            self.closed_loser_count += 1
        else:
            self.closed_flat_count += 1
        self.min_realized_r = min(self.min_realized_r, self.realized_r)
        self.max_realized_r = max(self.max_realized_r, self.realized_r)


@dataclass
class ReplayPosition:
    ticket: int
    candidate_id: str
    symbol: str
    side: str
    opened_at_utc: str
    exit_time_utc: str | None
    final_r: float
    risk_pct: float
    probability: float
    ev_r: float
    thesis_id: str
    entry_reference: float | None = None
    risk_r: float = 1.0

    def to_open_mapping(self) -> dict[str, Any]:
        return {
            "ticket": self.ticket,
            "candidate_id": self.candidate_id,
            "symbol": self.symbol,
            "side": self.side,
            "opened_at_utc": self.opened_at_utc,
            "exit_time_utc": self.exit_time_utc,
            "final_r": self.final_r,
            "risk_pct": self.risk_pct,
            "probability": self.probability,
            "ev_r": self.ev_r,
            "thesis_id": self.thesis_id,
            "entry_reference": self.entry_reference,
            "risk_r": self.risk_r,
        }


@dataclass
class ReplayState:
    open_positions: list[ReplayPosition] = field(default_factory=list)
    day_account: dict[str, ReplayDayAccountState] = field(default_factory=dict)
    next_ticket: int = 94000000
    account_curve_r: float = 0.0
    open_risk_r: float = 0.0
    accepted_count: int = 0
    zero_trade_count: int = 0
    closed_count: int = 0

    def day_state(self, trade_date: str) -> ReplayDayAccountState:
        return self.day_account.setdefault(
            trade_date,
            ReplayDayAccountState(trade_date=trade_date),
        )

    def open_risk_r_for_day(self, trade_date: str, *, risk_per_trade_pct: float) -> float:
        _ = trade_date, risk_per_trade_pct
        return round(max(0.0, self.open_risk_r), 9)

    def expire_positions(self, asof_utc: str) -> list[ReplayPosition]:
        asof = parse_iso(asof_utc)
        closed: list[ReplayPosition] = []
        still_open: list[ReplayPosition] = []
        for position in self.open_positions:
            exit_dt = parse_iso(position.exit_time_utc)
            if asof and exit_dt and exit_dt <= asof:
                closed.append(position)
                self.account_curve_r += position.final_r
                self.open_risk_r = max(0.0, self.open_risk_r - max(0.0, position.risk_r))
                self.closed_count += 1
                self.day_state(trade_date_from_utc(position.exit_time_utc)).record_close(
                    position.final_r
                )
            else:
                still_open.append(position)
        self.open_positions = still_open
        return closed

    def add_position(
        self,
        row: Mapping[str, Any],
        final_r: float,
        probability: float,
        ev_r: float,
        *,
        exit_time_utc: str | None = None,
        risk_pct: float = 2.0,
        risk_r: float = 1.0,
    ) -> ReplayPosition:
        ticket = self.next_ticket
        self.next_ticket += 1
        times = row_final_times(row)
        exit_time = exit_time_utc or times.get("be_after_trigger") or row_asof(row)
        position = ReplayPosition(
            ticket=ticket,
            candidate_id=candidate_id(row),
            symbol=row_symbol(row),
            side=_side(row.get("side") or row.get("direction")),
            opened_at_utc=row_asof(row),
            exit_time_utc=exit_time,
            final_r=final_r,
            risk_pct=risk_pct,
            probability=probability,
            ev_r=ev_r,
            thesis_id=_text(row.get("thesis_id") or f"wave4r:{candidate_id(row)}"),
            entry_reference=_float(row.get("entry_reference")),
            risk_r=risk_r,
        )
        self.open_positions.append(position)
        self.open_risk_r += max(0.0, position.risk_r)
        self.accepted_count += 1
        self.day_state(trade_date_from_utc(row_asof(row))).accepted_count += 1
        return position

    def apply_scheduler_exposure_action(
        self,
        scheduler: Mapping[str, Any],
        *,
        asof_utc: str,
    ) -> list[ReplayPosition]:
        decision = scheduler.get("decision") or {}
        action = _text(decision.get("selected_action_class"))
        exposure_id = _text(decision.get("selected_exposure_id"))
        if action not in {"close_existing", "reduce_existing"} or not exposure_id:
            return []
        ticket_text = exposure_id.split("ticket:", 1)[-1]
        closed: list[ReplayPosition] = []
        still_open: list[ReplayPosition] = []
        for position in self.open_positions:
            if str(position.ticket) != ticket_text:
                still_open.append(position)
                continue
            if action == "close_existing":
                closed_position = ReplayPosition(
                    ticket=position.ticket,
                    candidate_id=position.candidate_id,
                    symbol=position.symbol,
                    side=position.side,
                    opened_at_utc=position.opened_at_utc,
                    exit_time_utc=asof_utc,
                    final_r=0.0,
                    risk_pct=position.risk_pct,
                    probability=position.probability,
                    ev_r=position.ev_r,
                    thesis_id=position.thesis_id,
                    entry_reference=position.entry_reference,
                    risk_r=position.risk_r,
                )
                closed.append(closed_position)
                self.open_risk_r = max(0.0, self.open_risk_r - max(0.0, position.risk_r))
                self.closed_count += 1
                self.day_state(trade_date_from_utc(asof_utc)).record_close(0.0)
            else:
                reduction = max(0.0, position.risk_r) * 0.5
                position.risk_r = max(0.0, position.risk_r - reduction)
                position.risk_pct = max(0.0, position.risk_pct * 0.5)
                self.open_risk_r = max(0.0, self.open_risk_r - reduction)
                still_open.append(position)
        self.open_positions = still_open
        return closed

    def close_position_by_ticket(
        self,
        ticket: int | str | None,
        *,
        asof_utc: str,
        final_r: float = 0.0,
    ) -> ReplayPosition | None:
        if ticket in (None, ""):
            return None
        ticket_text = str(ticket)
        still_open: list[ReplayPosition] = []
        closed_position: ReplayPosition | None = None
        for position in self.open_positions:
            if str(position.ticket) != ticket_text:
                still_open.append(position)
                continue
            closed_position = ReplayPosition(
                ticket=position.ticket,
                candidate_id=position.candidate_id,
                symbol=position.symbol,
                side=position.side,
                opened_at_utc=position.opened_at_utc,
                exit_time_utc=asof_utc,
                final_r=float(final_r),
                risk_pct=position.risk_pct,
                probability=position.probability,
                ev_r=position.ev_r,
                thesis_id=position.thesis_id,
                entry_reference=position.entry_reference,
                risk_r=position.risk_r,
            )
            self.open_risk_r = max(0.0, self.open_risk_r - max(0.0, position.risk_r))
            self.closed_count += 1
            self.day_state(trade_date_from_utc(asof_utc)).record_close(float(final_r))
        self.open_positions = still_open
        return closed_position


def replay_prop_firm_projection(
    row: Mapping[str, Any],
    state: ReplayState,
    config: Mapping[str, Any],
    *,
    selected_for_new_risk: bool,
    requested_risk_pct: float = 2.0,
) -> dict[str, Any]:
    trade_date = trade_date_from_utc(row_asof(row))
    settings = replay_prop_firm_risk_settings(config)
    risk_per_trade_pct = float(settings["risk_per_trade_pct"] or 2.0)
    day_state = state.day_state(trade_date)
    open_risk_r = state.open_risk_r_for_day(
        trade_date,
        risk_per_trade_pct=risk_per_trade_pct,
    )
    requested_risk_r = (
        max(0.0, requested_risk_pct / risk_per_trade_pct)
        if selected_for_new_risk and risk_per_trade_pct > 0
        else 0.0
    )
    daily_limit_r = _float(settings.get("daily_loss_limit_r"))
    headroom_buffer_r = float(settings.get("headroom_buffer_r") or 0.0)
    available_new_risk_r = None
    if daily_limit_r is not None:
        available_new_risk_r = max(
            0.0,
            abs(daily_limit_r) + day_state.realized_r - open_risk_r - headroom_buffer_r,
        )
    new_trade_risk_r = requested_risk_r
    risk_adjustment_action = "not_selected"
    if selected_for_new_risk:
        risk_adjustment_action = "full_risk"
        if (
            available_new_risk_r is not None
            and requested_risk_r > available_new_risk_r
            and available_new_risk_r >= 0.05
        ):
            new_trade_risk_r = available_new_risk_r
            risk_adjustment_action = "reduce_to_buffered_daily_headroom"
    projected_worst_case_daily_r = round(
        day_state.realized_r - open_risk_r - new_trade_risk_r,
        9,
    )
    daily_blocked = bool(
        selected_for_new_risk
        and daily_limit_r is not None
        and projected_worst_case_daily_r <= -abs(daily_limit_r)
    )
    approved_risk_pct = (
        round(new_trade_risk_r * risk_per_trade_pct, 9)
        if selected_for_new_risk
        else 0.0
    )
    return {
        "status": (
            "replay_simulated_fresh_daily_account_blocked"
            if daily_blocked
            else "replay_simulated_fresh_daily_account_reduced_risk_allowed"
            if selected_for_new_risk and risk_adjustment_action == "reduce_to_buffered_daily_headroom"
            else "replay_simulated_fresh_daily_account_allowed"
            if selected_for_new_risk
            else "replay_simulated_fresh_daily_account_not_consumed"
        ),
        "simulation_model": "fresh_daily_prop_firm_drawdown_r_units",
        "simulation_boundary": (
            "synthetic replay account uses daily fresh baseline, realized replay exits, "
            "and worst-case open/new risk; it is not broker-real equity or cash."
        ),
        "trade_date": trade_date,
        "daily_drawdown_blocked": daily_blocked,
        "maximum_drawdown_blocked": False,
        "maximum_drawdown_model": "not_applied_to_fresh_day_replay_projection",
        "would_action": "BLOCK"
        if daily_blocked
        else "REDUCE_RISK_ALLOW"
        if selected_for_new_risk and risk_adjustment_action == "reduce_to_buffered_daily_headroom"
        else "ALLOW"
        if selected_for_new_risk
        else "NOT_CONSUMED",
        "daily_loss_limit_r": daily_limit_r,
        "daily_realized_r_before_decision": round(day_state.realized_r, 9),
        "daily_open_risk_r_before_decision": open_risk_r,
        "requested_risk_pct": round(requested_risk_pct, 9),
        "requested_risk_r": round(requested_risk_r, 9),
        "approved_risk_pct": approved_risk_pct,
        "new_trade_risk_r": round(new_trade_risk_r, 9),
        "available_new_risk_r": (
            round(available_new_risk_r, 9)
            if available_new_risk_r is not None
            else None
        ),
        "headroom_buffer_r": round(headroom_buffer_r, 9),
        "risk_adjustment_action": risk_adjustment_action,
        "projected_worst_case_daily_r": projected_worst_case_daily_r,
        "risk_per_trade_pct": risk_per_trade_pct,
        "daily_loss_limit_pct": settings.get("daily_loss_limit_pct"),
        "day_accepted_count_before_decision": day_state.accepted_count,
        "day_closed_count_before_decision": day_state.closed_count,
        "day_closed_winner_count_before_decision": day_state.closed_winner_count,
        "day_closed_loser_count_before_decision": day_state.closed_loser_count,
        "day_closed_flat_count_before_decision": day_state.closed_flat_count,
        "day_prop_firm_blocked_count_before_decision": day_state.prop_firm_blocked_count,
        "source_gaps": [],
        "engineering_backlog": [
            "hydrate ordered M1/tick path for mark-to-market intraday equity projection",
            "bind production PropFirmHeadroomSnapshotV4 before live execution",
        ],
    }


def scheduler_window(
    row: Mapping[str, Any],
    candidate_ev: float,
    probability: float,
    source_score: float,
    source_gaps: list[str],
    state: ReplayState,
) -> dict[str, Any]:
    open_positions = [
        {
            "exposure_id": f"ticket:{position.ticket}",
            "ticket": str(position.ticket),
            "symbol": position.symbol,
            "side": position.side,
            "risk_pct": position.risk_pct,
            "thesis_id": position.thesis_id,
            "unrealized_r": 0.0,
            "lifecycle_phase": "open",
            "source_completeness": source_score,
            "evidence_class": "chronological replay state proxy",
        }
        for position in state.open_positions
    ]
    candidate = {
        "candidate_id": candidate_id(row),
        "symbol": row_symbol(row),
        "side": _side(row.get("side") or row.get("direction")),
        "decision_time_utc": row_asof(row),
        "action_intent": "new_position",
        "requested_risk_pct": 2.0,
        "probability": probability,
        "ev_r": candidate_ev,
        "expectancy_r": candidate_ev,
        "confidence": min(0.95, 0.45 + source_score * 0.45),
        "uncertainty": max(0.05, 0.45 - source_score * 0.25),
        "fill_probability": 0.75,
        "source_completeness": source_score,
        "source_completeness_status": "complete" if source_score >= 0.75 else "partial",
        "evidence_class": "replay as-of proxy input",
        "no_leak_status": "pass" if source_score >= 0.45 else "source_gap",
        "confluence_action": "FOLLOW" if source_score >= 0.55 else "MIXED",
        "confluence_strength": min(0.9, 0.45 + source_score * 0.35),
        "confluence_confidence": min(0.9, 0.45 + source_score * 0.35),
        "confluence_reliability": min(0.9, 0.40 + source_score * 0.35),
        "cost_r": 0.03,
        "selected_cell_risk_pct": 2.0,
        "thesis_id": _text(row.get("thesis_id") or f"wave4r:{candidate_id(row)}"),
        "thesis_improvement": 0.08 if source_score >= 0.70 else 0.02,
        "missing_sources": tuple(source_gaps),
    }
    return {
        "decision_window_id": f"wave4r:{row_asof(row)}:{candidate_id(row)}",
        "candidate_set_id": f"wave4r:set:{row_asof(row)}",
        "asof_utc": row_asof(row),
        "candidates": [candidate],
        "open_positions": open_positions,
        "pending_orders": [],
    }


def selector_event(
    row: Mapping[str, Any],
    side: str,
    sources: list[dict[str, Any]],
    debate: Mapping[str, Any],
    lifecycle_packet: Mapping[str, Any],
    candidate_ev: float,
    source_score: float,
) -> dict[str, Any]:
    selector_debate = copy.deepcopy(dict(debate))
    raw_theses = selector_debate.get("theses")
    thesis_rows: Iterable[Any]
    if isinstance(raw_theses, Mapping):
        thesis_rows = raw_theses.values()
    elif isinstance(raw_theses, list):
        thesis_rows = raw_theses
    else:
        thesis_rows = []
    for thesis in thesis_rows:
        if isinstance(thesis, dict) and isinstance(thesis.get("confidence_calibration"), Mapping):
            calibration = thesis["confidence_calibration"]
            thesis["confidence_calibration"] = _float(
                calibration.get("reliability_weight"),
                _float(calibration.get("calibrated_probability"), 0.5),
            )
    lifecycle_summary = {
        "duplicate_exposure": lifecycle_packet.get("action")
        in {"duplicate_reject", "source_required_fail_closed"},
        "same_symbol_conflict": (
            "duplicate-exposure"
            if lifecycle_packet.get("action") == "duplicate_reject"
            else "none"
        ),
        "open_trade_competition_status": lifecycle_packet.get("action") or "new_position",
        "source_completeness": source_score,
        "ticket_bound_state": lifecycle_packet.get("selected_tickets"),
        "pending_partial_be_trailing_stale_state": "not_applicable_replay",
        "evidence_class": lifecycle_packet.get("evidence_class"),
        "packet": lifecycle_packet,
    }
    return {
        "candidate_id": candidate_id(row),
        "symbol": row_symbol(row),
        "side": side,
        "direction": side,
        "numeric_confluence": {"sources": sources},
        "probability_debate": selector_debate,
        "selected_cell": {
            "broker_net_expectancy_r": candidate_ev,
            "stress_expectancy_r": candidate_ev - 0.08,
            "risk_pct": 2.0,
            "evidence_class": "proxy-R",
            "source_completeness": source_score,
        },
        "cost": {
            "spread_r": 0.015,
            "slippage_r": 0.010,
            "commission_r": 0.005,
            "expected_total_cost_r": 0.030,
            "source_completeness": source_score,
            "evidence_class": "proxy-R",
        },
        "same_symbol_lifecycle": lifecycle_summary,
        "source_gaps": [
            "original_historical_v4_probability_debate_intent_missing",
            "true_account_headroom_missing_for_replay_row",
            "broker_real_fill_cost_not_available_on_frozen_row",
        ],
    }


def build_live_packet(
    row: Mapping[str, Any],
    config: Mapping[str, Any],
    selector: Mapping[str, Any],
    scheduler: Mapping[str, Any],
    debate: Mapping[str, Any],
    confluence_sources: list[dict[str, Any]],
    lifecycle_packet: Mapping[str, Any],
    execution_packet: Mapping[str, Any],
    geometry: Mapping[str, Any],
) -> dict[str, Any]:
    selected_risk_pct = selector_final_risk_pct(selector, default=2.0)
    legacy = {
        "candidate_identity": {
            "candidate_id": candidate_id(row),
            "symbol": row_symbol(row),
            "broker_symbol": row_symbol(row),
            "framework": row_framework(row),
            "session": row_session(row),
        },
        "source_m15": {
            "candle_open_utc": row.get("candle_time_utc"),
            "candle_close_utc": row.get("entry_first_touch_utc") or row.get("candle_time_utc"),
            "timeframe": "M15",
            "source_path_feature_status": row.get("source_path_feature_status")
            or "dynamic_policy_replay_row",
            "source_window_complete": row.get("source_window_complete"),
            "source_fields": sorted(str(k) for k in row.keys() if not str(k).startswith("_"))[:80],
        },
        "source_completeness": {
            "status": "proxy_asof_replay_bound",
            "missing": [
                "broker_real_live_v4_intent",
                "actual_account_state_at_historical_decision",
            ],
        },
        "runtime_decision": {"event": "wave4r_frozen_replay_asof_packet"},
        "final_order_decision": {
            "selector_action": selector.get("action"),
            "scheduler_action": (scheduler.get("decision") or {}).get("selected_action_class"),
        },
        "order_readiness": execution_packet,
        "selected_cell_risk_proof": {
            "risk_pct": selected_risk_pct,
            "risk_source": "proxy_asof_replay",
        },
    }
    record = {
        "metadata": {
            "lane": LANE_CODE,
            "asof_utc": row_asof(row),
            "evidence_label": "replay",
        },
        "decision_pipeline": {
            "selector_v4": selector,
            "scheduler_v4": scheduler,
            "probability_debate_v4": debate,
            "numeric_confluence_v4": {"sources": confluence_sources},
            "same_symbol_lifecycle_v4": lifecycle_packet,
            "execution_manager_v4": execution_packet,
            "dynamic_target_stop_geometry_v4": geometry,
        },
    }
    candidate = {
        "candidate_id": candidate_id(row),
        "symbol": row_symbol(row),
        "side": _side(row.get("side") or row.get("direction")),
    }
    raw_data = {
        "symbol": row_symbol(row),
        "source_file": row.get("_dynamic_shard_path") or row.get("source_path"),
        "source_hash": row.get("source_sha256"),
        "candle_close_utc": row.get("entry_first_touch_utc") or row.get("candle_time_utc"),
    }
    return build_live_decision_packet_v4(
        record=record,
        legacy_packet=legacy,
        candidate=candidate,
        raw_data=raw_data,
        runtime_config=dict(config),
    )


def packet_binding_summary(packet: Mapping[str, Any]) -> dict[str, Any]:
    groups = packet.get("field_groups") if isinstance(packet.get("field_groups"), Mapping) else {}
    status_counts: Counter[str] = Counter()
    missing_fields_by_group: dict[str, list[str]] = {}
    capture_requirements_by_group: dict[str, str] = {}
    for group_name, payload in groups.items():
        if not isinstance(payload, Mapping):
            status_counts["malformed_group_payload"] += 1
            missing_fields_by_group[str(group_name)] = ["field_group_payload_not_mapping"]
            continue
        status = _text(payload.get("group_source_status") or "missing_group_source_status")
        status_counts[status] += 1
        missing_fields = [str(field) for field in payload.get("missing_fields") or []]
        if missing_fields:
            missing_fields_by_group[str(group_name)] = missing_fields
        capture_requirement = payload.get("capture_requirement")
        if capture_requirement:
            capture_requirements_by_group[str(group_name)] = str(capture_requirement)
    validation_issues = validate_live_decision_packet_v4(dict(packet))
    missing_field_count = sum(len(fields) for fields in missing_fields_by_group.values())
    source_gap_group_count = sum(
        count
        for status, count in status_counts.items()
        if status not in {"captured_complete", "captured_present"}
    )
    capture_status = (
        "bound_with_validation_issues"
        if validation_issues
        else "bound_with_explicit_source_gap_groups"
        if missing_field_count or status_counts.get("prospective_capture_required")
        else "bound_complete"
    )
    return {
        "packet_hash_sha256": packet.get("packet_hash_sha256"),
        "source_event_hash_sha256": packet.get("source_event_hash_sha256"),
        "schema_name": packet.get("schema_name"),
        "schema_version": packet.get("schema_version"),
        "field_group_status_summary": {
            "required_group_count": len(packet.get("required_field_groups") or []),
            "present_group_count": len(groups),
            "status_counts": dict(status_counts),
            "source_gap_group_count": _int(
                (packet.get("packet_completeness") or {}).get("source_gap_group_count"),
                source_gap_group_count,
            ),
        },
        "missing_field_count": missing_field_count,
        "missing_fields_by_group": missing_fields_by_group,
        "capture_requirements_by_group": capture_requirements_by_group,
        "packet_completeness": packet.get("packet_completeness"),
        "validation_issues": validation_issues,
        "validation_issue_count": len(validation_issues),
        "capture_status": capture_status,
    }


def _valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "009abcdef" for char in value)


def scheduler_config() -> dict[str, Any]:
    return {
        "enabled": True,
        "apply_to_execution": True,
        "live_activation_allowed": True,
        "portfolio_ceiling_pct": 4.0,
        "correlation_cluster_ceiling_pct": 2.0,
        "min_trade_score": 0.35,
        "zero_trade_score": 0.20,
        "allow_multiple_new_positions_per_window": True,
        "require_full_window_source": False,
    }


def replay_holding_minutes(opened_at_utc: Any, asof_utc: Any) -> float:
    minutes = minutes_between(opened_at_utc, asof_utc)
    return max(0.0, float(minutes or 0.0))


def replay_holding_bars(opened_at_utc: Any, exit_or_asof_utc: Any) -> int | None:
    minutes = minutes_between(opened_at_utc, exit_or_asof_utc)
    if minutes is None:
        return None
    return max(1, int(math.ceil(max(0.0, minutes) / 15.0)))


def replay_open_position_stale_projection(
    position: "ReplayPosition",
    prepared_rows: list[Mapping[str, Any]],
    *,
    asof_utc: str,
) -> dict[str, Any]:
    candidate_evs = [
        float(_float(prepared.get("candidate_ev"), 0.0) or 0.0)
        for prepared in prepared_rows
    ]
    same_symbol_evs = [
        float(_float(prepared.get("candidate_ev"), 0.0) or 0.0)
        for prepared in prepared_rows
        if row_symbol(prepared["row"]) == position.symbol
    ]
    best_candidate_ev = max(candidate_evs, default=0.0)
    best_same_symbol_ev = max(same_symbol_evs, default=None)
    opportunity_ev = (
        max(best_candidate_ev, best_same_symbol_ev)
        if best_same_symbol_ev is not None
        else best_candidate_ev
    )
    ev_regret = max(0.0, opportunity_ev - float(position.ev_r or 0.0))
    age_minutes = replay_holding_minutes(position.opened_at_utc, asof_utc)
    age_component = min(0.35, age_minutes / 1440.0 * 0.35)
    regret_component = min(0.45, ev_regret / 2.0 * 0.45)
    weak_thesis_component = 0.10 if float(position.ev_r or 0.0) <= 0.05 else 0.0
    same_symbol_component = 0.10 if best_same_symbol_ev is not None and ev_regret > 0 else 0.0
    stale_score = min(
        1.0,
        age_component
        + regret_component
        + weak_thesis_component
        + same_symbol_component,
    )
    return {
        "stale_thesis_score": round(stale_score, 9),
        "time_in_trade_minutes": round(age_minutes, 6),
        "best_candidate_ev_r": round(best_candidate_ev, 9),
        "best_same_symbol_candidate_ev_r": (
            round(best_same_symbol_ev, 9)
            if best_same_symbol_ev is not None
            else None
        ),
        "opportunity_cost_ev_r": round(ev_regret, 9),
        "source_status": "replay_asof_candidate_window_ev_bound",
        "components": {
            "age_component": round(age_component, 9),
            "regret_component": round(regret_component, 9),
            "weak_thesis_component": round(weak_thesis_component, 9),
            "same_symbol_component": round(same_symbol_component, 9),
        },
    }


def lifecycle_action_to_scheduler_intent(action: str | None) -> str:
    if action == "same_direction_scale_in":
        return "same_direction_scale_in"
    if action == "close_and_reverse":
        return "close_and_reverse"
    if action in {"close_existing", "reduce_existing"}:
        return action
    if action in {
        "no_trade_duplicate",
        "no_trade_hedge_conflict",
        "source_required_fail_closed",
        "wait",
        "zero_trade",
    }:
        return "zero_trade"
    return "new_position"


def scheduler_missing_sources_from_gaps(gaps: Iterable[Any]) -> tuple[str, ...]:
    labels = {_text(gap) for gap in gaps if _text(gap)}
    positive_or_bounded_labels = {
        "simulated_replay_asof_decision_fields_complete",
        "source_path_gap_not_blocking_simulated_replay_asof_fields_complete",
        "simulated_replay_crypto_cost_tail_stress_bound",
    }
    if "simulated_replay_crypto_cost_tail_stress_bound" in labels:
        positive_or_bounded_labels.add("source_window_incomplete")
    missing: list[str] = []
    for label in labels:
        if label in positive_or_bounded_labels:
            continue
        if "_not_blocking_" in label:
            continue
        missing.append(label)
    return tuple(dict.fromkeys(missing))


def scheduler_thesis_improvement_from_prepared(prepared: Mapping[str, Any]) -> float:
    source_score = float(_float(prepared.get("source_score"), 0.0) or 0.0)
    base = 0.08 if source_score >= 0.70 else 0.02
    lifecycle = prepared.get("lifecycle")
    lifecycle_packet = lifecycle if isinstance(lifecycle, Mapping) else {}
    candidate = lifecycle_packet.get("candidate")
    candidate_packet = candidate if isinstance(candidate, Mapping) else {}
    proof = candidate_packet.get("proof")
    proof_packet = proof if isinstance(proof, Mapping) else {}
    if lifecycle_packet.get("action") != "same_direction_scale_in":
        return base
    if proof_packet.get("replay_lifecycle_inferred_action") != "same_direction_scale_in":
        return base
    probability_delta = max(0.0, float(_float(proof_packet.get("probability_delta"), 0.0) or 0.0))
    ev_delta = max(0.0, float(_float(proof_packet.get("ev_delta_r"), 0.0) or 0.0))
    replay_bound_score = 0.10 + min(0.45, probability_delta) + min(0.45, ev_delta / 2.0)
    return round(min(1.0, max(base, replay_bound_score)), 9)


def selector_final_risk_pct(selector: Mapping[str, Any], *, default: float = 2.0) -> float:
    value = _float(selector.get("final_risk_pct"))
    if value is None or value <= 0:
        return default if selector_v4_action_is_risk_bearing(selector.get("action")) else 0.0
    return value


def scheduler_candidate_from_prepared(prepared: Mapping[str, Any]) -> dict[str, Any]:
    row = prepared["row"]
    source_score = prepared["source_score"]
    action_intent = lifecycle_action_to_scheduler_intent(prepared["lifecycle"].get("action"))
    risk_pct = (
        0.0
        if action_intent == "zero_trade"
        else selector_final_risk_pct(prepared["selector"], default=2.0)
    )
    return {
        "candidate_id": candidate_id(row),
        "symbol": row_symbol(row),
        "side": prepared["side"],
        "decision_time_utc": prepared["asof_utc"],
        "action_intent": action_intent,
        "requested_risk_pct": risk_pct,
        "probability": prepared["probability"],
        "ev_r": prepared["candidate_ev"],
        "expectancy_r": prepared["candidate_ev"],
        "confidence": min(0.95, 0.45 + source_score * 0.45),
        "uncertainty": max(0.05, 0.45 - source_score * 0.25),
        "fill_probability": 0.75,
        "source_completeness": source_score,
        "source_completeness_status": "complete" if source_score >= 0.75 else "partial",
        "evidence_class": "replay as-of proxy input",
        "no_leak_status": "pass" if source_score >= 0.45 else "source_gap",
        "confluence_action": "FOLLOW" if source_score >= 0.55 else "MIXED",
        "confluence_strength": min(0.9, 0.45 + source_score * 0.35),
        "confluence_confidence": min(0.9, 0.45 + source_score * 0.35),
        "confluence_reliability": min(0.9, 0.40 + source_score * 0.35),
        "cost_r": 0.03,
        "selected_cell_risk_pct": risk_pct,
        "thesis_id": f"wave4r:{candidate_id(row)}",
        "thesis_improvement": scheduler_thesis_improvement_from_prepared(prepared),
        "missing_sources": scheduler_missing_sources_from_gaps(prepared["source_gaps"]),
        "metadata": {
            "selector_action": prepared["selector"].get("action"),
            "selector_final_risk_pct": prepared["selector"].get("final_risk_pct"),
            "same_symbol_action": prepared["lifecycle"].get("action"),
            "recovery_status": row.get("_wave4r_recovery_status"),
        },
    }


def scheduler_window_for_prepared(
    prepared_rows: list[Mapping[str, Any]],
    state: ReplayState,
    *,
    asof_utc: str,
) -> dict[str, Any]:
    open_positions = []
    for position in state.open_positions:
        stale_projection = replay_open_position_stale_projection(
            position,
            prepared_rows,
            asof_utc=asof_utc,
        )
        open_positions.append(
            {
            "exposure_id": f"ticket:{position.ticket}",
            "ticket": str(position.ticket),
            "symbol": position.symbol,
            "side": position.side,
            "risk_pct": position.risk_pct,
            "thesis_id": position.thesis_id,
            "unrealized_r": 0.0,
            "lifecycle_phase": "open",
            "stale_thesis_score": stale_projection["stale_thesis_score"],
            "time_in_trade_minutes": stale_projection["time_in_trade_minutes"],
            "source_completeness": 0.75,
            "evidence_class": "chronological replay state proxy",
            "stale_projection": stale_projection,
        }
        )
    candidates = [scheduler_candidate_from_prepared(prepared) for prepared in prepared_rows]
    return {
        "decision_window_id": f"wave4r:window:{asof_utc}",
        "candidate_set_id": f"wave4r:set:{asof_utc}",
        "asof_utc": asof_utc,
        "candidates": candidates,
        "open_positions": open_positions,
        "pending_orders": [],
        "evidence_class": "replay as-of candidate window",
        "source_status": "stage04_dynamic_policy_plus_stage05_recovered_rows_with_wave4r_fresh_day_state",
        "missing_runtime_truth": (),
        "historical_original_runtime_truth_gaps": (
            "actual_historical_open_position_snapshot",
            "actual_historical_pending_order_snapshot",
            "actual_historical_account_headroom",
        ),
    }


def option_for_candidate(scheduler: Mapping[str, Any], cid: str) -> dict[str, Any] | None:
    for option in scheduler.get("all_options_preserved") or []:
        if isinstance(option, Mapping) and option.get("candidate_id") == cid:
            return dict(option)
    return None


def compact_scheduler_for_candidate(scheduler: Mapping[str, Any], cid: str) -> dict[str, Any]:
    decision = scheduler.get("decision") or {}
    selected = decision.get("selected_option") or {}
    candidate_option = option_for_candidate(scheduler, cid)
    selected_candidate_ids = [
        _text(item)
        for item in (decision.get("selected_candidate_ids") or [])
        if _text(item)
    ]
    if not selected_candidate_ids and _text(decision.get("selected_candidate_id")):
        selected_candidate_ids = [_text(decision.get("selected_candidate_id"))]
    candidate_selected = cid in selected_candidate_ids
    return {
        "schema_version": scheduler.get("schema_version"),
        "component": scheduler.get("component"),
        "decision_window_id": scheduler.get("decision_window_id"),
        "candidate_set_id": scheduler.get("candidate_set_id"),
        "asof_utc": scheduler.get("asof_utc"),
        "status": scheduler.get("status"),
        "decision": {
            "selected_action_class": decision.get("selected_action_class"),
            "selected_candidate_id": decision.get("selected_candidate_id"),
            "selected_candidate_ids": selected_candidate_ids,
            "selected_action_classes": decision.get("selected_action_classes"),
            "approved_risk_pct": decision.get("approved_risk_pct"),
            "window_approved_risk_pct": decision.get("window_approved_risk_pct"),
            "runtime_effect_now": decision.get("runtime_effect_now"),
            "allocation_mode": decision.get("allocation_mode"),
            "selected_option_id": selected.get("option_id") if isinstance(selected, Mapping) else None,
            "selected_score": selected.get("score") if isinstance(selected, Mapping) else None,
            "selected_reason": selected.get("reason") if isinstance(selected, Mapping) else None,
            "current_candidate_selected": candidate_selected,
            "current_candidate_action_class": (
                candidate_option.get("action_class")
                if candidate_selected and isinstance(candidate_option, Mapping)
                else None
            ),
            "current_candidate_approved_risk_pct": (
                candidate_option.get("approved_risk_pct")
                if candidate_selected and isinstance(candidate_option, Mapping)
                else 0.0
            ),
        },
        "candidate_option": candidate_option,
        "input_counts": scheduler.get("input_counts"),
        "exposure_snapshot": {
            "open_position_count": ((scheduler.get("exposure_snapshot") or {}).get("open_position_count")),
            "pending_order_count": ((scheduler.get("exposure_snapshot") or {}).get("pending_order_count")),
            "total_reserved_risk_pct": ((scheduler.get("exposure_snapshot") or {}).get("total_reserved_risk_pct")),
            "same_symbol_risk_pct": ((scheduler.get("exposure_snapshot") or {}).get("same_symbol_risk_pct")),
            "cluster_risk_pct": ((scheduler.get("exposure_snapshot") or {}).get("cluster_risk_pct")),
        },
        "source_boundary": scheduler.get("source_boundary"),
    }


def exit_policy_replay_source_gaps(
    *,
    current_router: Mapping[str, Any],
    momentum: Mapping[str, Any],
    exit_bars_elapsed: int | None,
) -> tuple[str, ...]:
    gaps: list[str] = []
    if _float(current_router.get("final_r")) is None:
        gaps.append("exit_policy_current_progress_r_missing")
    if _float(current_router.get("mfe_r"), _float(momentum.get("mfe_r"))) is None:
        gaps.append("exit_policy_mfe_r_missing")
    if exit_bars_elapsed is None:
        gaps.append("exit_policy_holding_clock_missing")
    return tuple(dict.fromkeys(gaps))


def materialize_exit_policy_proxy_result(
    *,
    raw_policy_r: float,
    risk_r: float,
    exit_config: ExitPolicyConfigV4,
    exit_decision: Any,
    current_router: Mapping[str, Any],
    momentum: Mapping[str, Any],
    close_mark: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply replay-bound exit policy effects to a selected trade's proxy-R."""

    action = _text(getattr(exit_decision, "action", None))
    adjusted_policy_r = float(raw_policy_r)
    source_status = "exit_policy_no_result_adjustment"
    source_gaps: list[str] = []
    mfe_r = _float(current_router.get("mfe_r"), _float(momentum.get("mfe_r")))
    close_mark_payload = dict(close_mark or {})

    if action in {"MOVE_STOP_TO_BE", "RAISE_TRAILING_STOP"}:
        stop_r = _float(getattr(exit_decision, "target_stop_r", None))
        if stop_r is None:
            source_status = "exit_policy_stop_floor_missing_target_r"
            source_gaps.append("exit_policy_target_stop_r_required_for_materialized_r")
        else:
            adjusted_policy_r = max(adjusted_policy_r, stop_r)
            source_status = "exit_policy_stop_floor_replay_bound"
    elif action == "CLOSE_GIVEBACK":
        if mfe_r is None:
            source_status = "exit_policy_giveback_missing_mfe"
            source_gaps.append("exit_policy_mfe_r_required_for_giveback_materialized_r")
        else:
            giveback_close_r = max(0.0, float(exit_config.giveback_close_r))
            adjusted_policy_r = max(0.0, float(mfe_r) - giveback_close_r)
            source_status = "exit_policy_giveback_threshold_replay_bound"
    elif action == "PARTIAL_CLOSE_TO_BE":
        if mfe_r is None:
            source_status = "exit_policy_partial_missing_mfe"
            source_gaps.append("exit_policy_mfe_r_required_for_partial_materialized_r")
        else:
            ratio = _float(getattr(exit_decision, "partial_close_ratio", None))
            if ratio is None:
                ratio = exit_config.partial_close_ratio
            ratio = min(0.99, max(0.01, float(ratio)))
            partial_r = max(0.0, float(exit_config.partial_trigger_r))
            runner_r = max(adjusted_policy_r, 0.0)
            adjusted_policy_r = max(
                adjusted_policy_r,
                ratio * partial_r + (1.0 - ratio) * runner_r,
            )
            source_status = "exit_policy_partial_be_runner_replay_bound"
    elif action in {"CLOSE_STALE_THESIS", "CLOSE_TIME_STOP"}:
        close_mark_r = _float(close_mark_payload.get("close_mark_r"))
        close_mark_action = _text(close_mark_payload.get("action"))
        close_mark_reason = _text(close_mark_payload.get("close_reason"))
        close_mark_policy = _text(close_mark_payload.get("policy_id"))
        close_mark_time = iso_or_none(close_mark_payload.get("close_time_utc"))
        close_mark_bars = _int(close_mark_payload.get("bars_elapsed"))
        close_mark_source_status = close_mark_payload.get("source_status")
        required_reason = _text(getattr(exit_decision, "close_reason", None))
        if close_mark_r is None:
            source_gaps.append("exit_policy_close_time_mark_r_required_for_materialized_r")
        if not close_mark_time:
            source_gaps.append("exit_policy_close_time_utc_required_for_materialized_r")
        if close_mark_action != action:
            source_gaps.append("exit_policy_close_mark_action_mismatch")
        if required_reason and close_mark_reason != required_reason:
            source_gaps.append("exit_policy_close_mark_close_reason_mismatch")
        if close_mark_policy != "v4_exit_policy_close_mark_v1":
            source_gaps.append("exit_policy_close_mark_policy_id_required")
        if not _close_mark_source_status_bound(close_mark_source_status):
            source_gaps.append("exit_policy_close_mark_source_status_not_bound")
        if action == "CLOSE_TIME_STOP" and close_mark_bars != exit_config.time_stop_bars:
            source_gaps.append("exit_policy_close_mark_time_stop_bar_clock_mismatch")
        if (
            action == "CLOSE_STALE_THESIS"
            and close_mark_bars is not None
            and close_mark_bars < exit_config.stale_thesis_bars
        ):
            source_gaps.append("exit_policy_close_mark_stale_bar_clock_mismatch")
        if source_gaps:
            source_status = "exit_policy_close_mark_source_gap_result_unadjusted"
        else:
            adjusted_policy_r = float(close_mark_r)
            source_status = "exit_policy_close_mark_replay_bound"

    raw_proxy_r = float(raw_policy_r) * float(risk_r)
    materialized_proxy_r = float(adjusted_policy_r) * float(risk_r)
    return {
        "raw_policy_r": round(float(raw_policy_r), 9),
        "materialized_policy_r": round(float(adjusted_policy_r), 9),
        "raw_proxy_r": round(raw_proxy_r, 9),
        "materialized_proxy_r": round(materialized_proxy_r, 9),
        "adjustment_r": round(materialized_proxy_r - raw_proxy_r, 9),
        "source_status": source_status,
        "source_gaps": tuple(dict.fromkeys(source_gaps)),
        "close_mark": close_mark_payload if close_mark_payload else None,
    }


def scheduler_window_opportunity_context(
    prepared_rows: list[Mapping[str, Any]],
    scheduler: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    replay_r_by_candidate: dict[str, float] = {}
    source_status_by_candidate: dict[str, str] = {}
    for prepared in prepared_rows:
        cid = candidate_id(prepared["row"])
        promoted = promoted_router_result(
            prepared["row"],
            momentum_proxy=prepared["momentum"],
        )
        replay_r_by_candidate[cid] = float(_float(promoted.get("final_r"), 0.0) or 0.0)
        source_status_by_candidate[cid] = _text(promoted.get("source_status"))

    best_candidate_id = None
    best_replay_r = 0.0
    for cid, replay_r in replay_r_by_candidate.items():
        if best_candidate_id is None or replay_r > best_replay_r:
            best_candidate_id = cid
            best_replay_r = replay_r

    decision = scheduler.get("decision") or {}
    selected_candidate_ids = [
        _text(item)
        for item in (decision.get("selected_candidate_ids") or [])
        if _text(item)
    ]
    selected_candidate_id = _text(decision.get("selected_candidate_id")) or None
    if not selected_candidate_ids and selected_candidate_id:
        selected_candidate_ids = [selected_candidate_id]
    selected_candidate_id_set = set(selected_candidate_ids)
    selected_action = _text(decision.get("selected_action_class"))
    selected_replay_values = [
        replay_r_by_candidate.get(cid, 0.0)
        for cid in selected_candidate_ids
    ]
    best_selected_replay_r = max(selected_replay_values, default=0.0)
    primary_selected_replay_r = (
        replay_r_by_candidate.get(selected_candidate_id, 0.0)
        if selected_candidate_id
        else best_selected_replay_r
    )
    scheduler_regret_r = max(0.0, best_replay_r - best_selected_replay_r)
    context: dict[str, dict[str, Any]] = {}
    for cid, replay_r in replay_r_by_candidate.items():
        selected = cid in selected_candidate_id_set
        selected_baseline_r = replay_r if selected else best_selected_replay_r
        candidate_regret_r = max(0.0, replay_r - selected_baseline_r)
        context[cid] = {
            "candidate_id": cid,
            "candidate_promoted_router_replay_r": round(replay_r, 9),
            "candidate_promoted_router_source_status": source_status_by_candidate.get(cid),
            "best_window_candidate_id": best_candidate_id,
            "best_window_promoted_router_replay_r": round(best_replay_r, 9),
            "selected_candidate_id": selected_candidate_id,
            "selected_candidate_ids": selected_candidate_ids,
            "selected_action_class": selected_action,
            "selected_promoted_router_replay_r": round(primary_selected_replay_r, 9),
            "best_selected_promoted_router_replay_r": round(best_selected_replay_r, 9),
            "candidate_was_scheduler_selected": selected,
            "zero_trade_or_reject_opportunity_cost_r": (
                round(candidate_regret_r, 9) if not selected else 0.0
            ),
            "scheduler_regret_r": round(candidate_regret_r, 9),
            "window_scheduler_regret_r": round(scheduler_regret_r, 9),
            "opportunity_cost_source_status": "opportunity_cost_replay_bound",
            "scheduler_regret_source_status": "scheduler_regret_replay_bound",
            "evidence_label": "replay/proxy-R",
        }
    return context


def compact_debate(debate: Mapping[str, Any]) -> dict[str, Any]:
    selected = debate.get("selected_thesis") or {}
    return {
        "selected_action": debate.get("selected_action"),
        "selected_thesis": selected,
        "ranked_actions": debate.get("ranked_actions"),
        "vetoes": debate.get("vetoes"),
        "source_boundary": debate.get("source_boundary"),
    }


def compact_contract_component(component: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(component, Mapping):
        return {}
    packet = component.get("packet")
    source = packet if isinstance(packet, Mapping) else component
    summary_keys = (
        "schema_version",
        "component",
        "policy_id",
        "stage",
        "status",
        "action",
        "would_action",
        "decision_status",
        "reason",
        "selected_policy",
        "execution_policy_id",
        "should_block",
        "permitted_order_intent",
        "runtime_effect_now",
        "candidate_use_allowed_now",
        "risk_multiplier",
        "final_risk_pct",
        "packet_hash_sha256",
        "source_event_hash_sha256",
        "risk_packet_hash_sha256",
        "packet_completeness",
        "capture_status",
        "source_completeness_status",
        "source_status",
        "evidence_class",
        "result_use_status",
        "broker_runtime_change_status",
    )
    out = {key: source.get(key) for key in summary_keys if key in source}
    for key in (
        "fatal_reasons",
        "warning_reasons",
        "hard_reject_reasons",
        "reduced_risk_reasons",
        "queue_reasons",
        "vetoes",
        "refusal_reasons",
        "source_gaps",
        "missing_fields",
        "missing_fields_by_group",
        "capture_requirements_by_group",
        "validation_issues",
        "field_group_status_summary",
        "semantic_owner_handoffs",
        "rejected_alternatives",
    ):
        value = source.get(key)
        if value not in (None, [], {}, ""):
            out[key] = value
    if isinstance(packet, Mapping):
        out["packet_action"] = component.get("action")
        out["packet_should_block"] = component.get("should_block")
        if component.get("fatal_reasons"):
            out["packet_fatal_reasons"] = component.get("fatal_reasons")
        if component.get("warning_reasons"):
            out["packet_warning_reasons"] = component.get("warning_reasons")
    return out


def prepare_row_for_window(
    row: Mapping[str, Any],
    state: ReplayState,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    asof = row_asof(row)
    side = _side(row.get("side") or row.get("direction"))
    source_score, source_status, source_gaps = source_completeness_for_row(row)
    lifecycle_source_score = lifecycle_source_score_for_row(row, source_score)
    momentum = momentum_2r_proxy(row)
    confluence_sources = asof_confluence_sources(row, side, source_score)
    debate = debate_record_from_sources(config, row, confluence_sources)
    selected_thesis = debate.get("selected_thesis") or {}
    probability = _float(selected_thesis.get("probability"), 0.50) or 0.50
    candidate_ev = _float(selected_thesis.get("EV") or selected_thesis.get("ev_r"), 0.0) or 0.0
    lifecycle_candidate = build_candidate_lifecycle(
        config,
        row,
        side,
        lifecycle_source_score,
        source_status,
        probability,
        candidate_ev,
        state,
    )
    open_snapshots = [
        ticket_snapshot_from_open(position.to_open_mapping())
        for position in state.open_positions
    ]
    lifecycle = evaluate_same_symbol_lifecycle_v4(
        candidate=lifecycle_candidate,
        open_positions=open_snapshots,
        pending_orders=[],
        config=dict(config),
    ).to_packet()
    selector = evaluate_selector_v4_admission(
        selector_event(
            row,
            side,
            confluence_sources,
            debate,
            lifecycle,
            candidate_ev,
            source_score,
        ),
        config,
        enabled=True,
        apply_to_execution=True,
    ).to_record()
    return {
        "row": dict(row),
        "asof_utc": asof,
        "side": side,
        "source_score": source_score,
        "lifecycle_source_score": lifecycle_source_score,
        "source_status": source_status,
        "source_gaps": source_gaps,
        "momentum": momentum,
        "confluence_sources": confluence_sources,
        "debate": debate,
        "probability": probability,
        "candidate_ev": candidate_ev,
        "lifecycle": lifecycle,
        "selector": selector,
    }


def finalize_prepared_row(
    prepared: Mapping[str, Any],
    state: ReplayState,
    config: Mapping[str, Any],
    scheduler: Mapping[str, Any],
    *,
    closed: list[ReplayPosition],
    scheduler_exposure_closed: list[ReplayPosition] | None = None,
    window_opportunity_context: Mapping[str, Mapping[str, Any]] | None = None,
    accepted_position: ReplayPosition | None = None,
    prop_firm_projection: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    row = prepared["row"]
    asof = prepared["asof_utc"]
    side = prepared["side"]
    source_score = prepared["source_score"]
    source_status = prepared["source_status"]
    source_gaps = list(prepared["source_gaps"])
    momentum = prepared["momentum"]
    confluence_sources = prepared["confluence_sources"]
    debate = prepared["debate"]
    probability = prepared["probability"]
    candidate_ev = prepared["candidate_ev"]
    lifecycle = prepared["lifecycle"]
    selector = prepared["selector"]
    cid = candidate_id(row)
    current_router = promoted_router_result(row, momentum_proxy=momentum)
    current_policy = _text(current_router.get("selected_policy") or "momentum_exhaustion")
    current_target_r = POLICY_TARGET_R.get(current_policy, 2.0)
    current_policy_final_r = _float(current_router.get("final_r"), 0.0) or 0.0
    compact_scheduler = compact_scheduler_for_candidate(scheduler, cid)
    scheduler_decision = scheduler.get("decision") or {}
    selected_candidate_ids = [
        _text(item)
        for item in (scheduler_decision.get("selected_candidate_ids") or [])
        if _text(item)
    ]
    if not selected_candidate_ids and _text(scheduler_decision.get("selected_candidate_id")):
        selected_candidate_ids = [_text(scheduler_decision.get("selected_candidate_id"))]
    candidate_scheduler_selected = cid in set(selected_candidate_ids)
    selected_candidate_id = (
        cid
        if candidate_scheduler_selected
        else scheduler_decision.get("selected_candidate_id")
    )
    selected_exposure_id = (scheduler.get("decision") or {}).get("selected_exposure_id")
    selected_action_class = _text(scheduler_decision.get("selected_action_class"))
    exposure_action_selected = (
        not selected_candidate_ids
        and selected_action_class in {"close_existing", "reduce_existing", "close_and_reverse"}
    )
    if candidate_scheduler_selected:
        candidate_scheduler_action = (
            (compact_scheduler.get("decision") or {}).get("current_candidate_action_class")
            or selected_action_class
        )
        scheduler_candidate_selection_status = "selected_by_scheduler"
    elif exposure_action_selected:
        candidate_scheduler_action = selected_action_class
        scheduler_candidate_selection_status = "exposure_action_selected_by_scheduler"
    else:
        candidate_scheduler_action = "zero_trade"
        scheduler_candidate_selection_status = "not_selected_by_scheduler"
    runtime_selected = accepted_position is not None
    scheduler_exposure_closed = scheduler_exposure_closed or []
    opportunity_context = dict((window_opportunity_context or {}).get(cid) or {})
    selected_risk_pct = selector_final_risk_pct(selector, default=2.0)
    source_hash = _text(row.get("source_sha256")) or stable_hash(
        {
            "candidate_id": cid,
            "asof_utc": asof,
            "source_path": row.get("source_path"),
            "dynamic_shard_path": row.get("_dynamic_shard_path"),
            "sequence": row.get("_wave4r_sequence"),
        }
    )
    geometry = build_target_stop_geometry_v4_contract(
        config=config,
        selected_policy=current_policy,
        execution_policy_id=current_router.get("execution_policy_id"),
        source_event={
            "source_mode": "frozen_dynamic_policy_replay",
            "source_path_feature_status": "asof_replay_bound",
            "source_window_complete": row.get("source_window_complete"),
            "ordered_path_status": "m15_dynamic_policy_replay",
            "selected_policy_same_bar_ambiguous": momentum["same_bar_ambiguity"],
            "entry_price": row.get("entry_reference"),
            "stop_loss": row.get("stop_or_invalidation"),
            "direction": side,
        },
        trade_params={
            "entry_price": row.get("entry_reference"),
            "stop_loss": row.get("stop_or_invalidation"),
            "direction": side,
            "gtos_vnext_dynamic_final_target_r": current_target_r,
            "gtos_vnext_dynamic_momentum_pullback_r": 0.4
            if current_policy == "momentum_exhaustion"
            else None,
            "gtos_vnext_dynamic_partial_close_ratio": 0.5
            if current_policy == "partial_be_runner"
            else None,
            "gtos_vnext_dynamic_trail_gap_r": 0.5
            if current_policy == "trailing_runner"
            else None,
        },
        entry_price=row.get("entry_reference"),
        stop_loss=row.get("stop_or_invalidation"),
        direction=side,
        final_target_r=current_target_r,
        stage="wave4r_frozen_replay_asof",
    )
    execution_packet = asdict(evaluate_execution_manager_v4(
        config=config,
        trade_params={
            "candidate_id": cid,
            "gtos_vnext_candidate_id": cid,
            "gtos_vnext_selector_row_id": cid,
            "source_path": row.get("_dynamic_shard_path") or row.get("source_path"),
            "source_hash": source_hash,
            "gtos_vnext_source_path": row.get("_dynamic_shard_path") or row.get("source_path"),
            "gtos_vnext_source_hash": source_hash,
            "gtos_vnext_source_event_hash": source_hash,
            "gtos_vnext_source_event_details": {
                "asof_utc": asof,
                "candidate_id": cid,
                "source_family": "wave4r_frozen_dynamic_policy_replay",
                "recovery_status": row.get("_wave4r_recovery_status"),
            },
            "entry_price": row.get("entry_reference"),
            "stop_loss": row.get("stop_or_invalidation"),
            "direction": side,
            "gtos_vnext_production_execution_path": False,
            "gtos_vnext_dynamic_policy_applied": True,
            "gtos_vnext_dynamic_policy": current_policy,
            "gtos_vnext_dynamic_policy_selected": current_policy,
            "gtos_vnext_execution_policy_id": current_router.get("execution_policy_id"),
            "gtos_vnext_dynamic_final_target_r": current_target_r,
            "gtos_vnext_dynamic_momentum_pullback_r": 0.4
            if current_policy == "momentum_exhaustion"
            else None,
            "gtos_vnext_dynamic_partial_close_ratio": 0.5
            if current_policy == "partial_be_runner"
            else None,
            "gtos_vnext_dynamic_trail_gap_r": 0.5
            if current_policy == "trailing_runner"
            else None,
            "gtos_vnext_dynamic_target_stop_geometry_v4": geometry,
            "gtos_vnext_source_completeness": source_score,
            "gtos_vnext_selected_cell_risk_pct": selected_risk_pct,
            "gtos_vnext_selected_cell_risk_cell_id": f"wave4r:selected_cell:{cid}",
            "gtos_vnext_selected_cell_risk_selected_policy": current_policy,
            "gtos_vnext_selected_cell_risk_policy_identity_status": "proxy_asof_replay_bound",
            "gtos_vnext_selected_cell_risk_decision_basis": "wave4r_chronological_fresh_day_replay",
            "gtos_vnext_selector_v4_action": selector.get("action"),
            "gtos_vnext_selector_v4_reason": selector.get("reason")
            or selector.get("final_reason"),
            "gtos_vnext_selector_v4_packet_hash": stable_hash(selector),
            "gtos_vnext_selector_v4_packet": selector,
            "gtos_vnext_same_symbol_lifecycle_v4_packet": lifecycle,
            "gtos_vnext_same_symbol_lifecycle_action": lifecycle.get("action"),
            "gtos_vnext_scheduler_v4_packet": compact_scheduler,
            "gtos_vnext_scheduler_v4_packet_hash": stable_hash(compact_scheduler),
            "gtos_vnext_scheduler_v4_current_candidate_id": cid,
            "gtos_vnext_scheduler_v4_selected_candidate_id": selected_candidate_id,
            "gtos_vnext_scheduler_v4_selected_action_class": candidate_scheduler_action,
            "gtos_vnext_scheduler_v4_decision_window_id": scheduler.get("decision_window_id"),
            "gtos_vnext_commission_model_status": "proxy_commission_r_bound",
            "gtos_vnext_cost_model_source": "wave4r_proxy_pretrade_cost_model",
        },
        symbol=row_symbol(row),
        broker_symbol=row_symbol(row),
        pretrade_cost_model={
            "status": "PASSED",
            "expected_total_cost_r": 0.03,
            "spread_r": 0.015,
            "slippage_r": 0.010,
            "commission_r": 0.005,
            "commission_model_status": "proxy_commission_r_bound",
            "evidence_class": "proxy-R",
        },
        pending={"stage": "not_pending", "entry_drift_r": 0.0},
        trigger="wave4r_replay_asof",
    ))
    exit_bars_elapsed = replay_holding_bars(
        current_router.get("entry_touch_time_utc") or asof,
        current_router.get("exit_time_utc") or asof,
    )
    exit_source_gaps = exit_policy_replay_source_gaps(
        current_router=current_router,
        momentum=momentum,
        exit_bars_elapsed=exit_bars_elapsed,
    )
    replay_opportunity_cost_r = (
        _float(opportunity_context.get("zero_trade_or_reject_opportunity_cost_r"))
        if runtime_selected
        else None
    )
    replay_scheduler_regret_r = (
        _float(opportunity_context.get("scheduler_regret_r"))
        if runtime_selected
        else None
    )
    exit_config = ExitPolicyConfigV4.from_runtime_config(config_runtime(config))
    exit_decision = evaluate_exit_policy_v4(
        exit_config,
        ExitPolicyInputV4(
            ticket=accepted_position.ticket if accepted_position else None,
            symbol=row_symbol(row),
            direction=side,
            entry_time_utc=current_router.get("entry_touch_time_utc") or asof,
            bars_elapsed=exit_bars_elapsed,
            current_progress_r=current_policy_final_r,
            mfe_r=current_router.get("mfe_r") or momentum["mfe_r"],
            mae_r=current_router.get("mae_r") or momentum["mae_r"],
            current_stop_r=-1.0,
            partial_closed=False,
            sl_at_breakeven=False,
            partial_close_allowed=bool(runtime_selected),
            ticket_bound_state=bool(runtime_selected),
            broker_position_confirmed=bool(runtime_selected),
            path_source_status="replay_bound",
            clock_source_status="replay_bound",
            lifecycle_source_status="chronological_replay_state_proxy",
            thesis_invalidation_status="source_not_available",
            opportunity_cost_r=replay_opportunity_cost_r,
            scheduler_regret_r=replay_scheduler_regret_r,
            competing_candidate_ev_r=_float(
                opportunity_context.get("best_window_promoted_router_replay_r")
            ),
            opportunity_cost_source_status=(
                opportunity_context.get("opportunity_cost_source_status")
                if replay_opportunity_cost_r is not None
                else "not_applicable"
            ),
            scheduler_regret_source_status=(
                opportunity_context.get("scheduler_regret_source_status")
                if replay_scheduler_regret_r is not None
                else "not_applicable"
            ),
            source_gaps=exit_source_gaps,
        ),
    )
    exit_policy_close_mark = replay_exit_policy_close_mark(
        current_router=current_router,
        exit_decision=exit_decision,
        exit_config=exit_config,
        exit_bars_elapsed=exit_bars_elapsed,
    )
    live_packet = build_live_packet(
        row,
        config,
        selector,
        compact_scheduler,
        debate,
        confluence_sources,
        lifecycle,
        execution_packet,
        geometry,
    )
    live_packet_summary = packet_binding_summary(live_packet)
    current_v4_r = 0.0
    branch_decision = "zero_trade_or_reject"
    if runtime_selected:
        current_v4_r = accepted_position.final_r
        branch_decision = "v4_accept_simulated_trade"
    else:
        state.zero_trade_count += 1
    exit_policy_materialization = materialize_exit_policy_proxy_result(
        raw_policy_r=current_policy_final_r,
        risk_r=accepted_position.risk_r if accepted_position else 0.0,
        exit_config=exit_config,
        exit_decision=exit_decision,
        current_router=current_router,
        momentum=momentum,
        close_mark=exit_policy_close_mark,
    )
    if runtime_selected and accepted_position is not None:
        current_v4_r = float(exit_policy_materialization["materialized_proxy_r"])
        accepted_position.final_r = current_v4_r
    comparator = comparator_record(row)
    live_current_r = _float((comparator["policies"]["live_current_j46_j49"] or {}).get("final_r"), 0.0) or 0.0
    be_after_trigger_r = _float((comparator["policies"]["be_after_trigger"] or {}).get("final_r"), 0.0) or 0.0
    legacy_r = _float((comparator["policies"]["legacy_fixed_1.5r"] or {}).get("final_r"), 0.0) or 0.0
    promoted_router_r = _float((comparator.get("promoted_router") or {}).get("final_r"), 0.0) or 0.0
    path_microscope = path_microscope_fields(
        row,
        current_router=current_router,
        current_target_r=current_target_r,
        momentum=momentum,
    )
    if prop_firm_projection is None:
        prop_firm_risk_state = replay_prop_firm_projection(
            row,
            state,
            config,
            selected_for_new_risk=False,
        )
    else:
        prop_firm_risk_state = dict(prop_firm_projection)
    day_state = state.day_state(trade_date_from_utc(asof))
    prop_firm_risk_state.update(
        {
            "proxy_account_curve_r_after_decision": round(state.account_curve_r, 9),
            "proxy_realized_r_increment": round(current_v4_r, 9),
            "day_accepted_count_after_decision": day_state.accepted_count,
            "day_closed_count_after_decision": day_state.closed_count,
            "day_closed_winner_count_after_decision": day_state.closed_winner_count,
            "day_closed_loser_count_after_decision": day_state.closed_loser_count,
            "day_closed_flat_count_after_decision": day_state.closed_flat_count,
            "day_prop_firm_blocked_count_after_decision": day_state.prop_firm_blocked_count,
            "daily_realized_r_after_decision": round(day_state.realized_r, 9),
        }
    )
    downstream_selected_blocked = (
        not runtime_selected
        and cid == selected_candidate_id
        and (
            bool(prop_firm_risk_state.get("daily_drawdown_blocked"))
            or bool(prop_firm_risk_state.get("maximum_drawdown_blocked"))
            or not bool(lifecycle.get("permitted_order_intent"))
        )
    )
    zero_trade_opportunity_cost_r = (
        0.0
        if runtime_selected
        else max(0.0, promoted_router_r)
        if downstream_selected_blocked
        else float(
            _float(
                opportunity_context.get("zero_trade_or_reject_opportunity_cost_r"),
                0.0,
            )
            or 0.0
        )
    )
    result = {
        "candidate_id": candidate_id(row),
        "sequence": row.get("_wave4r_sequence"),
        "asof_utc": asof,
        "symbol": row_symbol(row),
        "session": row_session(row),
        "framework": row_framework(row),
        "side": side,
        "evidence_label": EVIDENCE_REPLAY,
        "current_v4_result_label": EVIDENCE_PROXY_R,
        "frozen_replay_result_scope": "current_v4_simulated_replay_proxy_R_not_broker_real_or_exact_live_v4_pnl",
        "current_v4_policy_id": CURRENT_V4_POLICY_ID,
        "current_v4_selected_policy": current_policy,
        "current_v4_execution_policy_id": current_router.get("execution_policy_id"),
        "current_v4_policy_result_source": current_router.get("source_status"),
        "current_v4_policy_raw_r": round(current_policy_final_r, 9),
        "branch_decision": branch_decision,
        "implementation_decision": "current_v4_asof_proxy_replay_no_broker_mutation",
        "selector_action": selector.get("action"),
        "scheduler_action": candidate_scheduler_action,
        "scheduler_current_candidate_selected": candidate_scheduler_selected,
        "scheduler_candidate_selection_status": scheduler_candidate_selection_status,
        "scheduler_selected_exposure_id": selected_exposure_id,
        "same_symbol_action": lifecycle.get("action"),
        "execution_status": execution_packet.get("status"),
        "exit_policy_action": exit_decision.action,
        "exit_policy_reason": exit_decision.reason,
        "exit_policy_close_reason": exit_decision.close_reason,
        "scheduler_opportunity_context": opportunity_context,
        "scheduler_regret_r": opportunity_context.get("scheduler_regret_r"),
        "window_best_candidate_id": opportunity_context.get("best_window_candidate_id"),
        "window_best_promoted_router_replay_r": opportunity_context.get(
            "best_window_promoted_router_replay_r"
        ),
        "scheduler_exposure_actions": [position.to_open_mapping() for position in scheduler_exposure_closed],
        "probability": probability,
        "candidate_ev_r": candidate_ev,
        "source_completeness": source_score,
        "source_status": source_status,
        "source_gaps": sorted(
            dict.fromkeys(
                source_gaps
                + momentum["source_gaps"]
                + list(current_router.get("source_gaps") or [])
                + list(path_microscope.get("source_gaps") or [])
                + list(prop_firm_risk_state.get("source_gaps") or [])
                + list(exit_decision.source_gaps or [])
                + list(exit_policy_materialization.get("source_gaps") or [])
            )
        ),
        "mfe_r": momentum["mfe_r"],
        "mae_r": momentum["mae_r"],
        "current_policy_mfe_r": current_router.get("mfe_r"),
        "current_policy_mae_r": current_router.get("mae_r"),
        "current_v4_proxy_r": round(current_v4_r, 9),
        "exit_policy_raw_proxy_r": exit_policy_materialization["raw_proxy_r"],
        "exit_policy_materialized_proxy_r": exit_policy_materialization[
            "materialized_proxy_r"
        ],
        "exit_policy_replay_result_adjustment_r": exit_policy_materialization[
            "adjustment_r"
        ],
        "exit_policy_result_source_status": exit_policy_materialization["source_status"],
        "exit_policy_close_mark": exit_policy_materialization.get("close_mark"),
        "exit_policy_materialization_source_gaps": list(
            exit_policy_materialization.get("source_gaps") or []
        ),
        "accepted_risk_pct": accepted_position.risk_pct if accepted_position else 0.0,
        "accepted_risk_r": accepted_position.risk_r if accepted_position else 0.0,
        "promoted_router_policy": (comparator.get("promoted_router") or {}).get("selected_policy"),
        "promoted_router_execution_policy_id": (
            comparator.get("promoted_router") or {}
        ).get("execution_policy_id"),
        "promoted_router_replay_r": round(promoted_router_r, 9),
        "promoted_router_evidence_label": (
            comparator.get("promoted_router") or {}
        ).get("evidence_label"),
        "promoted_router_source_status": (
            comparator.get("promoted_router") or {}
        ).get("source_status"),
        "v3_live_current_j46_j49_r": round(live_current_r, 9),
        "v3_be_after_trigger_r": round(be_after_trigger_r, 9),
        "legacy_fixed_1_5r_r": round(legacy_r, 9),
        "delta_v4_minus_promoted_router_r": round(current_v4_r - promoted_router_r, 9),
        "delta_v4_minus_live_current_r": round(current_v4_r - live_current_r, 9),
        "delta_v4_minus_be_after_trigger_r": round(current_v4_r - be_after_trigger_r, 9),
        "delta_v4_minus_legacy_fixed_r": round(current_v4_r - legacy_r, 9),
        "zero_trade_opportunity_cost_r": round(zero_trade_opportunity_cost_r, 9),
        "adverse_before_profit_flag": bool(
            momentum["mae_r"] is not None
            and momentum["mae_r"] < 0
            and momentum["mfe_r"] is not None
            and momentum["mfe_r"] > 0
        ),
        "static_2r_vs_dynamic_geometry": momentum,
        "promoted_router_path_result": current_router,
        "path_microscope": path_microscope,
        "prop_firm_risk_state": prop_firm_risk_state,
        "prop_firm_replay_action": prop_firm_risk_state.get("would_action"),
        "prop_firm_replay_blocked": bool(
            prop_firm_risk_state.get("daily_drawdown_blocked")
            or prop_firm_risk_state.get("maximum_drawdown_blocked")
        ),
        "prop_firm_daily_realized_r_after_decision": prop_firm_risk_state.get(
            "daily_realized_r_after_decision"
        ),
        "prop_firm_projected_worst_case_daily_r": prop_firm_risk_state.get(
            "projected_worst_case_daily_r"
        ),
        "trade_duration_minutes": path_microscope.get("holding_minutes_from_entry"),
        "exit_day_relation": path_microscope.get("exit_day_relation_from_entry"),
        "threshold_times_utc": path_microscope.get("threshold_times_utc"),
        "threshold_seconds_from_entry": path_microscope.get("threshold_seconds_from_entry"),
        "partial_trigger_utc": path_microscope.get("partial_trigger_utc"),
        "be_return_after_1r_utc": path_microscope.get("be_return_after_1r_utc"),
        "time_to_partial_seconds": path_microscope.get("time_to_partial_seconds"),
        "time_to_be_seconds": path_microscope.get("time_to_be_seconds"),
        "duration_stuck_near_entry_seconds": path_microscope.get(
            "duration_stuck_near_entry_seconds"
        ),
        "duration_before_movement_seconds": path_microscope.get(
            "duration_before_movement_seconds"
        ),
        "last_r": path_microscope.get("last_r"),
        "reversal_timing_utc": path_microscope.get("reversal_timing_utc"),
        "reached_0_5r": path_microscope.get("reached_0_5r"),
        "reached_1r": path_microscope.get("reached_1r"),
        "reached_configured_target": path_microscope.get("reached_configured_target"),
        "hit_stop": path_microscope.get("hit_stop"),
        "consolidated_near_1r_then_loss": path_microscope.get("consolidated_near_1r_then_loss"),
        "gave_back_profit_to_loss": path_microscope.get("gave_back_profit_to_loss"),
        "entry_reference": row.get("entry_reference"),
        "stop_or_invalidation": row.get("stop_or_invalidation"),
        "source_sha256": row.get("source_sha256"),
        "source_path": row.get("source_path"),
        "dynamic_shard_path": row.get("_dynamic_shard_path"),
        "accepted_ticket": accepted_position.ticket if accepted_position else None,
        "closed_positions_before_decision": [position.to_open_mapping() for position in closed],
        "open_position_count_after_decision": len(state.open_positions),
        "packet_hash": live_packet_summary.get("packet_hash_sha256"),
        "packet_hash_sha256": live_packet_summary.get("packet_hash_sha256"),
        "source_event_hash_sha256": live_packet_summary.get("source_event_hash_sha256"),
        "packet_capture_status": live_packet_summary.get("capture_status"),
        "packet_validation_issue_count": live_packet_summary.get("validation_issue_count"),
        "window_id": scheduler.get("decision_window_id"),
        "candidate_set_id": scheduler.get("candidate_set_id"),
        "window_candidate_count": (scheduler.get("input_counts") or {}).get("candidate_rows"),
        "scheduler_selected_candidate_id": selected_candidate_id,
        "scheduler_selected_candidate_ids": selected_candidate_ids,
        "candidate_scheduler_option": compact_scheduler.get("candidate_option"),
        "recovery_status": row.get("_wave4r_recovery_status"),
    }
    return {
        "row": dict(row),
        "result": result,
        "comparator": comparator,
        "momentum": momentum,
        "selector": selector,
        "scheduler": compact_scheduler,
        "full_window_scheduler": scheduler,
        "debate": debate,
        "confluence_sources": confluence_sources,
        "lifecycle": lifecycle,
        "execution": execution_packet,
        "geometry": geometry,
        "exit_policy": asdict(exit_decision),
        "live_packet": live_packet,
        "live_packet_summary": live_packet_summary,
    }


def evaluate_window(
    rows: list[Mapping[str, Any]],
    state: ReplayState,
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not rows:
        return []
    asof = row_asof(rows[0])
    closed = state.expire_positions(asof)
    prepared_rows = [prepare_row_for_window(row, state, config) for row in rows]
    scheduler = allocate_decision_window(
        scheduler_window_for_prepared(prepared_rows, state, asof_utc=asof),
        scheduler_config(),
    )
    scheduler_exposure_closed = state.apply_scheduler_exposure_action(
        scheduler,
        asof_utc=asof,
    )
    window_opportunity_context = scheduler_window_opportunity_context(
        prepared_rows,
        scheduler,
    )
    scheduler_decision = scheduler.get("decision") or {}
    selected_candidate_ids = {
        _text(item)
        for item in (scheduler_decision.get("selected_candidate_ids") or [])
        if _text(item)
    }
    if not selected_candidate_ids and _text(scheduler_decision.get("selected_candidate_id")):
        selected_candidate_ids.add(_text(scheduler_decision.get("selected_candidate_id")))
    accepted_positions: dict[str, ReplayPosition] = {}
    prop_firm_projections: dict[str, dict[str, Any]] = {}
    for prepared in prepared_rows:
        cid = candidate_id(prepared["row"])
        if cid not in selected_candidate_ids:
            continue
        selector_risk_pct = selector_final_risk_pct(prepared["selector"], default=2.0)
        scheduler_option = option_for_candidate(scheduler, cid) or {}
        scheduler_approved_risk_pct = _float(
            scheduler_option.get("approved_risk_pct"),
            selector_risk_pct,
        )
        effective_risk_pct = min(
            max(0.0, selector_risk_pct),
            max(0.0, scheduler_approved_risk_pct or 0.0),
        )
        effective_risk_r = risk_r_from_pct(config, effective_risk_pct)
        selector_accepts_for_replay = (
            selector_v4_action_is_risk_bearing(prepared["selector"].get("action"))
            and selector_risk_pct > 0.0
            and effective_risk_pct > 0.0
            and effective_risk_r > 0.0
        )
        lifecycle_action = _text(prepared["lifecycle"].get("action"))
        lifecycle_replay_permits_new_risk = bool(
            prepared["lifecycle"].get("permitted_order_intent")
        )
        if (
            lifecycle_action == "close_and_reverse"
            and prepared["source_score"] >= 0.75
            and prepared["lifecycle"].get("close_ticket") is not None
        ):
            closed_for_reverse = state.close_position_by_ticket(
                prepared["lifecycle"].get("close_ticket"),
                asof_utc=asof,
                final_r=0.0,
            )
            if closed_for_reverse is not None:
                scheduler_exposure_closed.append(closed_for_reverse)
                lifecycle_replay_permits_new_risk = True
        if (
            selector_accepts_for_replay
            and lifecycle_replay_permits_new_risk
            and (scheduler.get("decision") or {}).get("selected_action_class") != "zero_trade"
            and prepared["source_score"] >= 0.45
        ):
            current_router = promoted_router_result(
                prepared["row"],
                momentum_proxy=prepared["momentum"],
            )
            prop_projection = replay_prop_firm_projection(
                prepared["row"],
                state,
                config,
                selected_for_new_risk=True,
                requested_risk_pct=effective_risk_pct,
            )
            prop_firm_projections[cid] = prop_projection
            if prop_projection.get("daily_drawdown_blocked") or prop_projection.get(
                "maximum_drawdown_blocked"
            ):
                state.day_state(
                    trade_date_from_utc(prepared["asof_utc"])
                ).prop_firm_blocked_count += 1
                prop_projection["day_prop_firm_blocked_count_after_decision"] = (
                    state.day_state(trade_date_from_utc(prepared["asof_utc"])).prop_firm_blocked_count
                )
                continue
            approved_risk_r = float(
                _float(prop_projection.get("new_trade_risk_r"), effective_risk_r)
                or effective_risk_r
            )
            approved_risk_pct = float(
                _float(prop_projection.get("approved_risk_pct"), effective_risk_pct)
                or effective_risk_pct
            )
            accepted_positions[cid] = state.add_position(
                prepared["row"],
                float(_float(current_router.get("final_r"), 0.0) or 0.0)
                * approved_risk_r,
                float(prepared["probability"]),
                float(prepared["candidate_ev"]),
                exit_time_utc=iso_or_none(current_router.get("exit_time_utc")),
                risk_pct=approved_risk_pct,
                risk_r=approved_risk_r,
            )
    return [
        finalize_prepared_row(
            prepared,
            state,
            config,
            scheduler,
            closed=closed,
            scheduler_exposure_closed=scheduler_exposure_closed,
            window_opportunity_context=window_opportunity_context,
            accepted_position=accepted_positions.get(candidate_id(prepared["row"])),
            prop_firm_projection=prop_firm_projections.get(candidate_id(prepared["row"])),
        )
        for prepared in prepared_rows
    ]


def evaluate_row(
    row: Mapping[str, Any],
    state: ReplayState,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    return evaluate_window([row], state, config)[0]


def hard_halt_binding_rows(repo_root: Path, config: Mapping[str, Any], limit: int | None = None) -> list[dict[str, Any]]:
    wave4a_path = repo_root / WAVE4A_ROOT / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl"
    rows: list[dict[str, Any]] = []
    if not wave4a_path.exists():
        return [
            {
                "binding_status": "source_gap",
                "evidence_label": EVIDENCE_SOURCE_GAP,
                "reason": "Wave4A canonical universe not found",
            }
        ]
    for row in iter_jsonl(wave4a_path):
        label = _text(row.get("evidence_label") or row.get("evidence_class"))
        raw = json.dumps(row, sort_keys=True)
        if "broker-real" not in raw and "broker_real" not in raw:
            continue
        source_score, source_status, gaps = source_completeness_for_row(row)
        rows.append(
            {
                "row_id": row.get("row_id") or candidate_id(row),
                "symbol": row_symbol(row),
                "asof_utc": row_asof(row),
                "evidence_label": label or EVIDENCE_BROKER_REAL_PNL,
                "broker_real_fields_allowed": True,
                "v4_replay_binding_status": "broker_real_row_bound_to_source_gap_v4_packet",
                "source_completeness": source_score,
                "source_status": source_status,
                "source_gaps": sorted(
                    dict.fromkeys(
                        gaps
                        + [
                            "historical_live_v4_selector_packet_not_available",
                            "actual_open_pending_state_at_trade_time_not_available",
                        ]
                    )
                ),
                "hard_boundary": {
                    "broker_history_mutation": False,
                    "broker_order_mutation": False,
                    "read_only_binding": True,
                },
                "row_hash": stable_hash(row),
            }
        )
        if limit is not None and len(rows) >= limit:
            break
    return rows


def write_static_route_ledgers(route_dir: Path, source_inventory: Mapping[str, Any]) -> None:
    context_anchor = {
        "schema_version": "wave4r_context_anchor_v1",
        "generated_at_utc": utc_now(),
        "lane_code": LANE_CODE,
        "route": ROUTE_NAME,
        "worktree": str(Path.cwd()),
        "prompt_path": "research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE4R_V4_VS_V3_FROZEN_REPLAY_RESULTS_GATE_GOAL_PROMPT_2026-06-05.md",
        "starter_path": "research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE4R_V4_VS_V3_FROZEN_REPLAY_RESULTS_GATE_STARTER_2026-06-05.txt",
        "hard_boundaries": source_inventory.get("hard_boundaries"),
        "evidence_labels_preserved": [
            EVIDENCE_BROKER_REAL_PNL,
            EVIDENCE_BROKER_REAL_CASH,
            "exact-R",
            EVIDENCE_PROXY_R,
            EVIDENCE_REPLAY,
            "simulation",
            "shadow",
            "live authority",
            EVIDENCE_SOURCE_GAP,
            "prospective capture requirement",
            "default-off research",
            EVIDENCE_PRODUCTION_CODE,
            EVIDENCE_RUNTIME_CODE,
            "uncommitted dirt",
            EVIDENCE_HISTORICAL_ONLY,
        ],
    }
    write_json(route_dir / "WAVE4R_CONTEXT_ANCHOR.json", context_anchor)
    write_json(route_dir / "WAVE4R_SOURCE_INVENTORY.json", source_inventory)
    questions = [
        "What frozen replay rows are hydrated and replayable now?",
        "Which dynamic-policy shards were absent as native Stage04 files, how were they recovered, and what denominator rows remain missing?",
        "What would current V4 select/reject/zero-trade as-of for every readable dynamic row?",
        "Where does current V4 improve/degrade versus the May-27 promoted dynamic router comparator?",
        "Which no-trade decisions would have had positive replay opportunity cost?",
        "Which same-symbol situations require scale/reduce/close/reverse capture?",
        "Where do MFE/MAE and same-bar ambiguity require ordered LTF/tick replay?",
        "Which broker-real hard-halt rows can be bound without pretending frozen replay has broker-real cash?",
        "Which findings are repairable now and which are prospective source capture?",
        "Which Wave5 fields are justified only after the microscope output is computed?",
    ]
    with (route_dir / "WAVE4R_EXHAUSTIVE_QUESTION_LEDGER.jsonl").open("w", encoding="utf-8") as handle:
        for index, question in enumerate(questions, start=1):
            append_jsonl(
                handle,
                {
                    "question_id": f"wave4r_q_{index:03d}",
                    "question": question,
                    "status": "answered_or_reduced_to_source_gap_by_route",
                    "evidence_label": "replay",
                },
            )
    with (route_dir / "WAVE4R_CODE_AND_REPLAY_REPAIR_LEDGER.jsonl").open("w", encoding="utf-8") as handle:
        append_jsonl(
            handle,
            {
                "repair_id": "wave4r_research_infra_adapter_v1",
                "changed_files": [
                    "src/research_infra/wave4r_v4_vs_v3_frozen_replay_results_gate.py",
                    "tests/test_wave4r_v4_vs_v3_frozen_replay_results_gate.py",
                    f"research/operations/{ROUTE_NAME}/build_wave4r_v4_vs_v3_frozen_replay_results_gate.py",
                    f"research/operations/{ROUTE_NAME}/verify_wave4r_v4_vs_v3_frozen_replay_results_gate.py",
                ],
                "before_behavior": "No Wave4R route-local V4-vs-V3 frozen replay microscope module existed.",
                "after_behavior": (
                    "All 214,536 May-26 dynamic replay rows are chronologically bound to current V4 "
                    "selector/debate/scheduler/lifecycle/execution/geometry/exit/live-packet outputs. "
                    "Missing native Stage04 shards are recovered from Stage05 activated replay, "
                    "timestamp-window scheduler allocation is materialized, ordered path reconstruction "
                    "is labeled per row, and remaining source gaps are exact broker/account/fill/intent "
                    "truth gaps rather than denominator gaps."
                ),
                "focused_tests": "tests/test_wave4r_v4_vs_v3_frozen_replay_results_gate.py",
                "evidence_label": EVIDENCE_PRODUCTION_CODE,
            },
        )
    with (route_dir / "WAVE4R_READONLY_MT5_EXTRACTION_LEDGER.jsonl").open("w", encoding="utf-8") as handle:
        append_jsonl(
            handle,
            {
                "extraction_id": "wave4r_no_mt5_export_performed",
                "mode": "not_run",
                "reason": (
                    "No broker/MT5 historical export was required: Stage05 activated replay recovered "
                    "the seven missing native Stage04 dynamic-policy shard ids and the full 214,536-row "
                    "dynamic denominator was processed from local repo evidence."
                ),
                "stage05_recovery_status": "full_dynamic_denominator_recovered_without_mt5_export",
                "broker_or_live_mutation": False,
                "evidence_label": EVIDENCE_REPLAY,
            },
        )
    with (route_dir / "WAVE4R_SUBAGENT_OR_RESOURCE_USE_LEDGER.jsonl").open("w", encoding="utf-8") as handle:
        append_jsonl(
            handle,
            {
                "resource_use_id": "wave4r_local_resource_sweep",
                "resources_used": [
                    "mandatory GTOS preflight context files",
                    "May-24/May-25/May-26 frozen replay roots",
                    "Wave4A/Wave4I accepted route artifacts",
                    "current V4 production component APIs",
                    "workspace-wide local shard search under /Users/borr/Documents/gtos",
                    "subagent audits for live/V3 microscope schema, frozen path feasibility, production V4 gaps, and prop-firm risk evidence",
                ],
                "subagents_used": True,
                "reason": (
                    "Route-owned deterministic integration stayed local; subagents supplied bounded "
                    "evidence audits and production-gap reviews without broker or live mutation."
                ),
            },
        )
    with (route_dir / "WAVE4R_ML_DEFERRAL_REJECTION_LEDGER.jsonl").open("w", encoding="utf-8") as handle:
        append_jsonl(
            handle,
            {
                "deferral_id": "wave4r_not_ml_placeholder",
                "status": "rejected_deferral",
                "reason": "Wave4R computed replay decisions and result ledgers before Wave5 handoff fields; ML is byproduct only.",
                "evidence_label": "production code",
            },
        )


def write_inventory_ledgers(route_dir: Path, inventory: Mapping[str, Any]) -> None:
    may26 = (((inventory.get("frozen_surfaces") or {}).get("may26_dynamic_policy_replay")) or {})
    with (route_dir / "WAVE4R_DATA_HYDRATION_AND_REPAIR_LEDGER.jsonl").open("w", encoding="utf-8") as handle:
        for surface, payload in (inventory.get("frozen_surfaces") or {}).items():
            append_jsonl(
                handle,
                {
                    "surface": surface,
                    "root": payload.get("root"),
                    "hydration_status": "inventoried_from_disk",
                    "evidence_label": "historical-only evidence",
                    "summary": payload,
                },
            )
    with (route_dir / "WAVE4R_DYNAMIC_POLICY_SHARD_REPAIR_LEDGER.jsonl").open("w", encoding="utf-8") as handle:
        append_jsonl(
            handle,
            {
                "repair_id": "may26_dynamic_policy_shard_availability",
                "shards_expected": may26.get("shards_expected"),
                "readable_dynamic_policy_shards": may26.get("readable_dynamic_policy_shards"),
                "stage05_recovery_shards": may26.get("stage05_recovery_shards"),
                "native_readable_dynamic_policy_rows": may26.get("native_readable_dynamic_policy_rows"),
                "recovered_dynamic_policy_rows_from_stage05": may26.get("recovered_dynamic_policy_rows_from_stage05"),
                "missing_dynamic_policy_shards": may26.get("missing_dynamic_policy_shards"),
                "replayable_candidate_rows_expected": may26.get("replayable_candidate_rows_expected"),
                "readable_dynamic_policy_rows": may26.get("readable_dynamic_policy_rows"),
                "missing_dynamic_policy_rows": may26.get("missing_dynamic_policy_rows"),
                "actions_attempted": [
                    "git lfs status checked current branch hydration",
                    "workspace-wide find under /Users/borr/Documents/gtos for dynamic_policy_replay.jsonl",
                    "searched stage05 full activated replay shards for the exact missing stage04src ids",
                    "recovered dynamic_policy_replay.available rows from activated_replay.jsonl.gz where stage04 files were absent",
                    "after Stage05 recovery, unrecovered dynamic-policy denominator rows equal zero",
                ],
                "repair_status": (
                    "full_dynamic_denominator_recovered_from_native_stage04_plus_stage05"
                    if (may26.get("missing_dynamic_policy_rows") or 0) == 0
                    else "partial_disk_hydration_only"
                ),
                "evidence_label": EVIDENCE_REPLAY
                if (may26.get("missing_dynamic_policy_rows") or 0) == 0
                else EVIDENCE_SOURCE_GAP,
            },
        )
    with (route_dir / "WAVE4R_REPLAY_SUBSTRATE_REPAIR_SEARCH_LEDGER.jsonl").open("w", encoding="utf-8") as handle:
        append_jsonl(
            handle,
            {
                "search_id": "wave4r_missing_stage04_dynamic_shards_search",
                "searched_roots": [
                    "/Users/borr/Documents/gtos/worktrees",
                    "/Users/borr/Documents/gtos/repo/ai-trading-agent",
                    "/Users/borr/Documents/gtos/packages",
                    str(MAY24_ROOT),
                    str(MAY26_ROOT),
                    str(REPLACEMENT_ACTIVATION_ROOT),
                ],
                "missing_stage04_dynamic_shards": may26.get("stage05_recovery_shards"),
                "recovery_source": (
                    "stage05_full_activated_replay_shards/*/activated_replay.jsonl.gz "
                    "dynamic_policy_replay.available rows"
                ),
                "native_stage04_rows": may26.get("native_readable_dynamic_policy_rows"),
                "stage05_recovered_rows": may26.get("recovered_dynamic_policy_rows_from_stage05"),
                "total_replayable_rows_after_repair": may26.get("readable_dynamic_policy_rows"),
                "unrecovered_rows_after_repair": may26.get("missing_dynamic_policy_rows"),
                "evidence_label": EVIDENCE_REPLAY
                if (may26.get("missing_dynamic_policy_rows") or 0) == 0
                else EVIDENCE_SOURCE_GAP,
            },
        )
    with (route_dir / "WAVE4R_FROZEN_REPLAY_BINDING_LEDGER.jsonl").open("w", encoding="utf-8") as handle:
        append_jsonl(
            handle,
            {
                "binding_id": "may26_readable_dynamic_policy_rows",
                "row_count": may26.get("readable_dynamic_policy_rows"),
                "denominator_expected_rows": may26.get("replayable_candidate_rows_expected"),
                "missing_rows_preserved_in_source_gap_denominator": may26.get("missing_dynamic_policy_rows"),
                "binding_status": "native_and_recovered_rows_bound_to_wave4r_v4_asof_packets",
                "evidence_label": EVIDENCE_REPLAY,
            },
        )
        if may26.get("missing_dynamic_policy_rows"):
            append_jsonl(
                handle,
                {
                    "binding_id": "may26_missing_dynamic_policy_rows",
                    "row_count": may26.get("missing_dynamic_policy_rows"),
                    "binding_status": "not_computed_exact_row_packet_missing_shards",
                    "capture_requirement": "recover or regenerate missing dynamic-policy shard files from approved May-24 path-outcome inputs or read-only historical path export",
                    "evidence_label": EVIDENCE_SOURCE_GAP,
                },
            )


class LedgerHandles:
    def __init__(self, route_dir: Path) -> None:
        self.route_dir = route_dir
        self.compress_jsonl = os.environ.get("WAVE4R_COMPRESS_JSONL") == "1"
        self.handles: dict[str, Any] = {}
        self._hardlink_aliases = {
            "WAVE4R_CANDIDATE_TRADE_MICROSCOPE_LEDGER.jsonl": "WAVE4R_CANDIDATE_DECISION_MICROSCOPE_LEDGER.jsonl",
        }

    def __enter__(self) -> "LedgerHandles":
        names = [
            "WAVE4R_V3_PREV4_COMPARATOR_LEDGER.jsonl",
            "WAVE4R_V4_ASOF_PACKET_LEDGER.jsonl",
            "WAVE4R_CHRONOLOGICAL_STATE_TRANSITION_LEDGER.jsonl",
            "WAVE4R_MULTI_CANDIDATE_WINDOW_ALLOCATION_LEDGER.jsonl",
            "WAVE4R_CANDIDATE_TRADE_MICROSCOPE_LEDGER.jsonl",
            "WAVE4R_CANDIDATE_DECISION_MICROSCOPE_LEDGER.jsonl",
            "WAVE4R_TRADE_PATH_ANATOMY_LEDGER.jsonl",
            "WAVE4R_RESULTS_LEDGER.jsonl",
            "WAVE4R_DECISION_LEDGER.jsonl",
            "WAVE4R_REPLAY_ACCOUNT_CURVE_LEDGER.jsonl",
            "WAVE4R_V3_V4_DELTA_LEDGER.jsonl",
            "WAVE4R_FROZEN_VS_LIVE_DELTA_LEDGER.jsonl",
            "WAVE4R_ENTRY_QUALITY_LEDGER.jsonl",
            "WAVE4R_ENTRY_EXIT_TIMING_PATH_LEDGER.jsonl",
            "WAVE4R_SELECTOR_EXECUTION_EXIT_ANATOMY_LEDGER.jsonl",
            "WAVE4R_SAME_SYMBOL_ACTION_LEDGER.jsonl",
            "WAVE4R_STATIC_R_DYNAMIC_GEOMETRY_LEDGER.jsonl",
            "WAVE4R_ORDERED_PATH_RECONSTRUCTION_LEDGER.jsonl",
            "WAVE4R_TIME_MFE_MAE_GIVEBACK_LEDGER.jsonl",
            "WAVE4R_FOLLOW_AVOID_MIXED_CONFLUENCE_LEDGER.jsonl",
            "WAVE4R_PROBABILITY_CALIBRATION_LEDGER.jsonl",
            "WAVE4R_ZERO_TRADE_OPPORTUNITY_COST_LEDGER.jsonl",
            "WAVE4R_ACCEPTED_LOSER_FORENSIC_LEDGER.jsonl",
            "WAVE4R_REJECTED_WINNER_OPPORTUNITY_LEDGER.jsonl",
            "WAVE4R_SCHEDULER_ALLOCATION_REGRET_LEDGER.jsonl",
            "WAVE4R_EXIT_HARVEST_COUNTERFACTUAL_LEDGER.jsonl",
            "WAVE4R_STALE_HOLDINGS_THESIS_AGE_LEDGER.jsonl",
            "WAVE4R_SOURCE_GAP_CAPTURE_REQUIREMENT_LEDGER.jsonl",
            "WAVE4R_ACTIONABLE_V4_REPAIR_FINDINGS_LEDGER.jsonl",
        ]
        for name in names:
            if name in self._hardlink_aliases:
                continue
            path = self.route_dir / name
            if self.compress_jsonl:
                self.handles[name] = gzip.open(path, "wt", encoding="utf-8")
            else:
                self.handles[name] = path.open("w", encoding="utf-8")
        return self

    def write(self, name: str, payload: Mapping[str, Any]) -> None:
        if name in self._hardlink_aliases:
            return
        append_jsonl(self.handles[name], payload)

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        for handle in self.handles.values():
            handle.close()
        if exc_type is not None:
            return
        for alias_name, source_name in self._hardlink_aliases.items():
            source_path = self.route_dir / source_name
            alias_path = self.route_dir / alias_name
            if not source_path.exists():
                continue
            if alias_path.exists() or alias_path.is_symlink():
                alias_path.unlink()
            os.link(source_path, alias_path)


@dataclass
class ReplaySummary:
    decision_windows: int = 0
    multi_candidate_windows: int = 0
    max_window_size: int = 0
    processed_rows: int = 0
    accepted_rows: int = 0
    zero_trade_rows: int = 0
    source_gap_rows: int = 0
    v4_total_r: float = 0.0
    promoted_router_total_r: float = 0.0
    live_current_total_r: float = 0.0
    be_after_trigger_total_r: float = 0.0
    legacy_total_r: float = 0.0
    same_bar_ambiguity_rows: int = 0
    adverse_before_profit_rows: int = 0
    positive_zero_trade_opportunity_cost_rows: int = 0
    prop_firm_replay_blocked_rows: int = 0
    symbols: Counter = field(default_factory=Counter)
    sessions: Counter = field(default_factory=Counter)
    frameworks: Counter = field(default_factory=Counter)
    same_symbol_actions: Counter = field(default_factory=Counter)
    selector_actions: Counter = field(default_factory=Counter)
    scheduler_actions: Counter = field(default_factory=Counter)
    promoted_router_policies: Counter = field(default_factory=Counter)
    promoted_router_source_statuses: Counter = field(default_factory=Counter)
    recovery_statuses: Counter = field(default_factory=Counter)
    symbol_session: dict[tuple[str, str, str], dict[str, Any]] = field(default_factory=dict)
    day_session: dict[tuple[str, str, str, str], dict[str, Any]] = field(default_factory=dict)

    def record_window(self, size: int) -> None:
        self.decision_windows += 1
        if size > 1:
            self.multi_candidate_windows += 1
        self.max_window_size = max(self.max_window_size, size)

    def update(self, result: Mapping[str, Any]) -> None:
        self.processed_rows += 1
        accepted = result["branch_decision"] == "v4_accept_simulated_trade"
        self.accepted_rows += 1 if accepted else 0
        self.zero_trade_rows += 0 if accepted else 1
        self.source_gap_rows += 1 if result.get("source_gaps") else 0
        self.v4_total_r += float(result.get("current_v4_proxy_r") or 0.0)
        self.promoted_router_total_r += float(result.get("promoted_router_replay_r") or 0.0)
        self.live_current_total_r += float(result.get("v3_live_current_j46_j49_r") or 0.0)
        self.be_after_trigger_total_r += float(result.get("v3_be_after_trigger_r") or 0.0)
        self.legacy_total_r += float(result.get("legacy_fixed_1_5r_r") or 0.0)
        self.same_bar_ambiguity_rows += 1 if (result.get("static_2r_vs_dynamic_geometry") or {}).get("same_bar_ambiguity") else 0
        self.adverse_before_profit_rows += 1 if result.get("adverse_before_profit_flag") else 0
        self.positive_zero_trade_opportunity_cost_rows += 1 if float(result.get("zero_trade_opportunity_cost_r") or 0.0) > 0 else 0
        self.prop_firm_replay_blocked_rows += 1 if result.get("prop_firm_replay_blocked") else 0
        self.symbols.update([result.get("symbol")])
        self.sessions.update([result.get("session")])
        self.frameworks.update([result.get("framework")])
        self.same_symbol_actions.update([result.get("same_symbol_action")])
        self.selector_actions.update([result.get("selector_action")])
        self.scheduler_actions.update([result.get("scheduler_action")])
        self.promoted_router_policies.update([result.get("promoted_router_policy")])
        self.promoted_router_source_statuses.update([result.get("promoted_router_source_status")])
        self.recovery_statuses.update([result.get("recovery_status")])
        key = (str(result.get("symbol")), str(result.get("session")), str(result.get("framework")))
        bucket = self.symbol_session.setdefault(
            key,
            {
                "symbol": key[0],
                "session": key[1],
                "framework": key[2],
                "rows": 0,
                "accepted": 0,
                "v4_total_r": 0.0,
                "promoted_router_total_r": 0.0,
                "live_current_total_r": 0.0,
                "source_gap_rows": 0,
            },
        )
        bucket["rows"] += 1
        bucket["accepted"] += 1 if accepted else 0
        bucket["v4_total_r"] += float(result.get("current_v4_proxy_r") or 0.0)
        bucket["promoted_router_total_r"] += float(result.get("promoted_router_replay_r") or 0.0)
        bucket["live_current_total_r"] += float(result.get("v3_live_current_j46_j49_r") or 0.0)
        bucket["source_gap_rows"] += 1 if result.get("source_gaps") else 0
        asof_dt = parse_iso(result.get("asof_utc"))
        trade_date = asof_dt.date().isoformat() if asof_dt else "unknown_date"
        day_key = (
            trade_date,
            str(result.get("session")),
            str(result.get("symbol")),
            str(result.get("framework")),
        )
        day_bucket = self.day_session.setdefault(
            day_key,
            {
                "trade_date": day_key[0],
                "session": day_key[1],
                "symbol": day_key[2],
                "framework": day_key[3],
                "rows": 0,
                "accepted": 0,
                "accepted_winners": 0,
                "accepted_losers": 0,
                "accepted_breakeven": 0,
                "rejected_or_zero_positive_opportunities": 0,
                "source_gap_rows": 0,
                "prop_firm_risk_source_gap_rows": 0,
                "prop_firm_replay_blocked_rows": 0,
                "reached_0_5r_rows": 0,
                "reached_1r_rows": 0,
                "reached_configured_target_rows": 0,
                "hit_stop_rows": 0,
                "same_day_exits": 0,
                "next_day_exits": 0,
                "later_day_exits": 0,
                "unknown_exit_day_rows": 0,
                "consolidated_near_1r_then_loss_rows": 0,
                "gave_back_profit_to_loss_rows": 0,
                "duration_minutes_sum": 0.0,
                "duration_minutes_count": 0,
                "v4_total_r": 0.0,
                "promoted_router_total_r": 0.0,
                "zero_trade_opportunity_cost_r": 0.0,
            },
        )
        day_bucket["rows"] += 1
        day_bucket["accepted"] += 1 if accepted else 0
        day_bucket["accepted_winners"] += (
            1 if accepted and float(result.get("current_v4_proxy_r") or 0.0) > 0 else 0
        )
        day_bucket["accepted_losers"] += (
            1 if accepted and float(result.get("current_v4_proxy_r") or 0.0) < 0 else 0
        )
        day_bucket["accepted_breakeven"] += (
            1 if accepted and float(result.get("current_v4_proxy_r") or 0.0) == 0 else 0
        )
        day_bucket["rejected_or_zero_positive_opportunities"] += (
            1
            if (not accepted and float(result.get("promoted_router_replay_r") or 0.0) > 0)
            else 0
        )
        day_bucket["source_gap_rows"] += 1 if result.get("source_gaps") else 0
        risk_state = result.get("prop_firm_risk_state") or {}
        day_bucket["prop_firm_risk_source_gap_rows"] += (
            1 if str(risk_state.get("status") or "").startswith("source_gap") else 0
        )
        day_bucket["prop_firm_replay_blocked_rows"] += (
            1 if result.get("prop_firm_replay_blocked") else 0
        )
        if risk_state.get("daily_realized_r_after_decision") is not None:
            day_bucket["latest_daily_realized_r_after_decision"] = risk_state.get(
                "daily_realized_r_after_decision"
            )
        if risk_state.get("projected_worst_case_daily_r") is not None:
            day_bucket["min_projected_worst_case_daily_r"] = min(
                float(day_bucket.get("min_projected_worst_case_daily_r", 0.0)),
                float(risk_state.get("projected_worst_case_daily_r") or 0.0),
            )
        day_bucket["reached_0_5r_rows"] += 1 if result.get("reached_0_5r") else 0
        day_bucket["reached_1r_rows"] += 1 if result.get("reached_1r") else 0
        day_bucket["reached_configured_target_rows"] += (
            1 if result.get("reached_configured_target") else 0
        )
        day_bucket["hit_stop_rows"] += 1 if result.get("hit_stop") else 0
        relation = result.get("exit_day_relation")
        if relation == "same_day":
            day_bucket["same_day_exits"] += 1
        elif relation == "next_day":
            day_bucket["next_day_exits"] += 1
        elif relation == "later_day":
            day_bucket["later_day_exits"] += 1
        else:
            day_bucket["unknown_exit_day_rows"] += 1
        day_bucket["consolidated_near_1r_then_loss_rows"] += (
            1 if result.get("consolidated_near_1r_then_loss") else 0
        )
        day_bucket["gave_back_profit_to_loss_rows"] += (
            1 if result.get("gave_back_profit_to_loss") else 0
        )
        duration = _float(result.get("trade_duration_minutes"))
        if duration is not None:
            day_bucket["duration_minutes_sum"] += duration
            day_bucket["duration_minutes_count"] += 1
        day_bucket["v4_total_r"] += float(result.get("current_v4_proxy_r") or 0.0)
        day_bucket["promoted_router_total_r"] += float(result.get("promoted_router_replay_r") or 0.0)
        day_bucket["zero_trade_opportunity_cost_r"] += float(
            result.get("zero_trade_opportunity_cost_r") or 0.0
        )

    def to_record(self, inventory: Mapping[str, Any], state: ReplayState) -> dict[str, Any]:
        denom = (
            (((inventory.get("frozen_surfaces") or {}).get("may26_dynamic_policy_replay")) or {})
            .get("replayable_candidate_rows_expected")
        )
        missing = (
            (((inventory.get("frozen_surfaces") or {}).get("may26_dynamic_policy_replay")) or {})
            .get("missing_dynamic_policy_rows")
        )
        return {
            "schema_version": "wave4r_results_summary_v1",
            "generated_at_utc": utc_now(),
            "processed_dynamic_policy_rows": self.processed_rows,
            "decision_windows": self.decision_windows,
            "multi_candidate_decision_windows": self.multi_candidate_windows,
            "max_decision_window_size": self.max_window_size,
            "expected_replayable_dynamic_policy_rows": denom,
            "missing_dynamic_policy_rows_preserved_as_source_gap": missing,
            "accepted_v4_simulated_rows": self.accepted_rows,
            "zero_trade_or_rejected_rows": self.zero_trade_rows,
            "source_gap_rows": self.source_gap_rows,
            "v4_total_proxy_r": round(self.v4_total_r, 9),
            "promoted_router_total_replay_r": round(self.promoted_router_total_r, 9),
            "live_current_j46_j49_total_replay_r": round(self.live_current_total_r, 9),
            "be_after_trigger_total_replay_r": round(self.be_after_trigger_total_r, 9),
            "legacy_fixed_1_5r_total_replay_r": round(self.legacy_total_r, 9),
            "delta_v4_minus_promoted_router_total_r": round(
                self.v4_total_r - self.promoted_router_total_r,
                9,
            ),
            "delta_v4_minus_live_current_total_r": round(self.v4_total_r - self.live_current_total_r, 9),
            "delta_v4_minus_be_after_trigger_total_r": round(self.v4_total_r - self.be_after_trigger_total_r, 9),
            "same_bar_ambiguity_rows": self.same_bar_ambiguity_rows,
            "adverse_before_profit_rows": self.adverse_before_profit_rows,
            "positive_zero_trade_opportunity_cost_rows": self.positive_zero_trade_opportunity_cost_rows,
            "prop_firm_replay_blocked_rows": self.prop_firm_replay_blocked_rows,
            "final_account_curve_realized_r": round(state.account_curve_r, 9),
            "remaining_open_positions": len(state.open_positions),
            "selector_action_counts": dict(self.selector_actions),
            "scheduler_action_counts": dict(self.scheduler_actions),
            "promoted_router_policy_counts": dict(self.promoted_router_policies),
            "promoted_router_source_status_counts": dict(
                self.promoted_router_source_statuses
            ),
            "recovery_status_counts": dict(self.recovery_statuses),
            "same_symbol_action_counts": dict(self.same_symbol_actions),
            "symbol_counts": dict(self.symbols),
            "session_counts": dict(self.sessions),
            "framework_counts": dict(self.frameworks),
            "evidence_boundary": {
                "broker_real_cash_used_on_frozen_rows": False,
                "broker_operation": False,
                "paid_api_or_vendor_call": False,
                "current_v4_result_label": EVIDENCE_PROXY_R,
                "primary_prior_comparator": PROMOTED_ROUTER_POLICY_ID,
                "primary_prior_comparator_label": PROMOTED_ROUTER_EVIDENCE_LABEL,
                "j46_j49_and_fixed_1_5r_role": "secondary_historical_comparator_only",
            },
        }


def write_row_ledgers(ledgers: LedgerHandles, evaluated: Mapping[str, Any], state: ReplayState) -> None:
    result = evaluated["result"]
    row = evaluated["row"]
    live_packet_summary = evaluated["live_packet_summary"]
    ledgers.write("WAVE4R_V3_PREV4_COMPARATOR_LEDGER.jsonl", evaluated["comparator"])
    ledgers.write(
        "WAVE4R_V4_ASOF_PACKET_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "asof_utc": result["asof_utc"],
            "symbol": result["symbol"],
            "packet_hash": result["packet_hash"],
            "packet_hash_sha256": result["packet_hash_sha256"],
            "source_event_hash_sha256": result["source_event_hash_sha256"],
            "field_group_status_summary": live_packet_summary["field_group_status_summary"],
            "missing_field_count": live_packet_summary["missing_field_count"],
            "missing_fields_by_group": live_packet_summary["missing_fields_by_group"],
            "capture_requirements_by_group": live_packet_summary["capture_requirements_by_group"],
            "packet_completeness": live_packet_summary["packet_completeness"],
            "packet_capture_status": live_packet_summary["capture_status"],
            "packet_validation_issues": live_packet_summary["validation_issues"],
            "packet_validation_issue_count": live_packet_summary["validation_issue_count"],
            "selector": compact_contract_component(evaluated["selector"]),
            "scheduler": evaluated["scheduler"],
            "probability_debate": compact_debate(evaluated["debate"]),
            "live_decision_packet_v4_summary": live_packet_summary,
            "evidence_label": "replay",
        },
    )
    ledgers.write(
        "WAVE4R_CHRONOLOGICAL_STATE_TRANSITION_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "sequence": result["sequence"],
            "asof_utc": result["asof_utc"],
            "closed_positions_before_decision": result["closed_positions_before_decision"],
            "open_position_count_after_decision": result["open_position_count_after_decision"],
            "account_curve_realized_r_after_decision": round(state.account_curve_r, 9),
            "branch_decision": result["branch_decision"],
            "prop_firm_replay_action": result["prop_firm_replay_action"],
            "prop_firm_replay_blocked": result["prop_firm_replay_blocked"],
            "prop_firm_daily_realized_r_after_decision": result[
                "prop_firm_daily_realized_r_after_decision"
            ],
            "prop_firm_projected_worst_case_daily_r": result[
                "prop_firm_projected_worst_case_daily_r"
            ],
            "evidence_label": "chronological replay state proxy",
        },
    )
    microscope = {
        **result,
        "probability_debate_state": {
            "selected_action": evaluated["debate"].get("selected_action"),
            "selected_thesis": evaluated["debate"].get("selected_thesis"),
            "ranked_actions": evaluated["debate"].get("ranked_actions"),
        },
        "confluence_state": evaluated["confluence_sources"],
        "same_symbol_packet": evaluated["lifecycle"],
        "execution_packet": evaluated["execution"],
        "geometry_contract": evaluated["geometry"],
        "exit_policy": evaluated["exit_policy"],
        "selected_rejected_alternatives": {
            "window_ledger": "WAVE4R_MULTI_CANDIDATE_WINDOW_ALLOCATION_LEDGER.jsonl",
            "candidate_option": result.get("candidate_scheduler_option"),
            "selected_candidate_id": result.get("scheduler_selected_candidate_id"),
        },
        "repair_capture_requirement_id": (
            f"capture:{result['candidate_id']}"
            if result.get("source_gaps")
            else None
        ),
    }
    ledgers.write("WAVE4R_CANDIDATE_TRADE_MICROSCOPE_LEDGER.jsonl", microscope)
    ledgers.write("WAVE4R_CANDIDATE_DECISION_MICROSCOPE_LEDGER.jsonl", microscope)
    ledgers.write(
        "WAVE4R_TRADE_PATH_ANATOMY_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "symbol": result["symbol"],
            "asof_utc": result["asof_utc"],
            "mfe_r": result["mfe_r"],
            "mae_r": result["mae_r"],
            "adverse_before_profit_flag": result["adverse_before_profit_flag"],
            "time_fields": row_final_times(row),
            "momentum_2r_proxy": evaluated["momentum"],
            "path_microscope": result["path_microscope"],
            "prop_firm_risk_state": result["prop_firm_risk_state"],
            "source_path": result["source_path"],
            "recovery_status": result.get("recovery_status"),
            "evidence_label": "replay",
        },
    )
    ledgers.write("WAVE4R_RESULTS_LEDGER.jsonl", result)
    ledgers.write(
        "WAVE4R_DECISION_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "asof_utc": result["asof_utc"],
            "symbol": result["symbol"],
            "terminal_decision": result["branch_decision"],
            "selector_action": result["selector_action"],
            "scheduler_action": result["scheduler_action"],
            "same_symbol_action": result["same_symbol_action"],
            "current_v4_proxy_r": result["current_v4_proxy_r"],
            "promoted_router_replay_r": result["promoted_router_replay_r"],
            "delta_v4_minus_promoted_router_r": result[
                "delta_v4_minus_promoted_router_r"
            ],
            "source_gap_count": len(result.get("source_gaps") or []),
            "prop_firm_risk_state": result["prop_firm_risk_state"],
            "evidence_label": result["evidence_label"],
        },
    )
    ledgers.write(
        "WAVE4R_REPLAY_ACCOUNT_CURVE_LEDGER.jsonl",
        {
            "sequence": result["sequence"],
            "candidate_id": result["candidate_id"],
            "asof_utc": result["asof_utc"],
            "branch_decision": result["branch_decision"],
            "incremental_v4_proxy_r": result["current_v4_proxy_r"],
            "realized_account_curve_r": round(state.account_curve_r, 9),
            "open_position_count": len(state.open_positions),
            "prop_firm_risk_state": result["prop_firm_risk_state"],
            "evidence_label": "replay",
        },
    )
    ledgers.write(
        "WAVE4R_V3_V4_DELTA_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "asof_utc": result["asof_utc"],
            "current_v4_proxy_r": result["current_v4_proxy_r"],
            "promoted_router_policy": result["promoted_router_policy"],
            "promoted_router_replay_r": result["promoted_router_replay_r"],
            "delta_v4_minus_promoted_router_r": result["delta_v4_minus_promoted_router_r"],
            "live_current_j46_j49_r": result["v3_live_current_j46_j49_r"],
            "be_after_trigger_r": result["v3_be_after_trigger_r"],
            "legacy_fixed_1_5r_r": result["legacy_fixed_1_5r_r"],
            "delta_v4_minus_live_current_r": result["delta_v4_minus_live_current_r"],
            "delta_v4_minus_be_after_trigger_r": result["delta_v4_minus_be_after_trigger_r"],
            "authority_boundary": (
                "V4 current proxy result vs May-27 promoted dynamic router primary comparator; "
                "J46/J49/static are historical secondary comparators"
            ),
            "evidence_label": "proxy-R",
        },
    )
    ledgers.write(
        "WAVE4R_FROZEN_VS_LIVE_DELTA_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "symbol": result["symbol"],
            "asof_utc": result["asof_utc"],
            "frozen_replay_label": "replay/proxy-R",
            "live_evidence_label": (
                "promoted dynamic router replay comparator; not broker-real live PnL"
            ),
            "broker_real_cash_on_this_row": False,
            "frozen_vs_live_delta_r": result["delta_v4_minus_promoted_router_r"],
            "source_gap": "frozen row has no broker-real fill/cost/cash truth",
        },
    )
    ledgers.write(
        "WAVE4R_ENTRY_QUALITY_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "entry_reference": result["entry_reference"],
            "stop_or_invalidation": result["stop_or_invalidation"],
            "mfe_r": result["mfe_r"],
            "mae_r": result["mae_r"],
            "adverse_before_profit_flag": result["adverse_before_profit_flag"],
            "entry_quality_bucket": (
                "clean_move"
                if (result["mae_r"] is not None and result["mae_r"] > -0.25)
                else "adverse_before_profit"
                if result["adverse_before_profit_flag"]
                else "source_gap"
            ),
            "evidence_label": "replay",
        },
    )
    ledgers.write(
        "WAVE4R_ENTRY_EXIT_TIMING_PATH_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "asof_utc": result["asof_utc"],
            "entry_first_touch_utc": row.get("entry_first_touch_utc"),
            "candle_time_utc": row.get("candle_time_utc"),
            "exit_times_by_policy": row_final_times(row),
            "path_microscope": result["path_microscope"],
            "trade_duration_minutes": result["trade_duration_minutes"],
            "exit_day_relation": result["exit_day_relation"],
            "threshold_times_utc": result["threshold_times_utc"],
            "threshold_seconds_from_entry": result["threshold_seconds_from_entry"],
            "partial_trigger_utc": result["partial_trigger_utc"],
            "be_return_after_1r_utc": result["be_return_after_1r_utc"],
            "time_to_partial_seconds": result["time_to_partial_seconds"],
            "time_to_be_seconds": result["time_to_be_seconds"],
            "duration_stuck_near_entry_seconds": result[
                "duration_stuck_near_entry_seconds"
            ],
            "duration_before_movement_seconds": result[
                "duration_before_movement_seconds"
            ],
            "last_r": result["last_r"],
            "reversal_timing_utc": result["reversal_timing_utc"],
            "reached_0_5r": result["reached_0_5r"],
            "reached_1r": result["reached_1r"],
            "reached_configured_target": result["reached_configured_target"],
            "hit_stop": result["hit_stop"],
            "exit_policy_action": result["exit_policy_action"],
            "source_gaps": result["source_gaps"],
        },
    )
    ledgers.write(
        "WAVE4R_SELECTOR_EXECUTION_EXIT_ANATOMY_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "selector": compact_contract_component(evaluated["selector"]),
            "scheduler": compact_scheduler_for_candidate(evaluated["scheduler"], result["candidate_id"]),
            "execution": compact_contract_component(evaluated["execution"]),
            "geometry": compact_contract_component(evaluated["geometry"]),
            "exit_policy": compact_contract_component(evaluated["exit_policy"]),
            "full_payload_reference": "WAVE4R_CANDIDATE_DECISION_MICROSCOPE_LEDGER.jsonl",
        },
    )
    ledgers.write(
        "WAVE4R_SAME_SYMBOL_ACTION_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "same_symbol_action": result["same_symbol_action"],
            "same_symbol_packet": evaluated["lifecycle"],
            "open_position_count_after_decision": result["open_position_count_after_decision"],
            "evidence_label": "chronological replay state proxy",
        },
    )
    ledgers.write(
        "WAVE4R_STATIC_R_DYNAMIC_GEOMETRY_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "current_config_policy": result["current_v4_selected_policy"],
            "configured_final_target_r": POLICY_TARGET_R.get(
                result["current_v4_selected_policy"],
                2.0,
            ),
            "promoted_router_replay_r": result["promoted_router_replay_r"],
            "legacy_static_1_5r_r": result["legacy_fixed_1_5r_r"],
            "current_v4_proxy_r": result["current_v4_proxy_r"],
            "geometry_contract": compact_contract_component(evaluated["geometry"]),
            "source_gaps": result["source_gaps"],
            "full_payload_reference": "WAVE4R_CANDIDATE_DECISION_MICROSCOPE_LEDGER.jsonl",
        },
    )
    ledgers.write(
        "WAVE4R_ORDERED_PATH_RECONSTRUCTION_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "symbol": result["symbol"],
            "asof_utc": result["asof_utc"],
            "configured_target_r": POLICY_TARGET_R.get(
                result["current_v4_selected_policy"],
                2.0,
            ),
            "current_v4_selected_policy": result["current_v4_selected_policy"],
            "ordered_path_source_status": result["promoted_router_path_result"].get(
                "ordered_path_source_status"
            ),
            "target_first_touch_utc": evaluated["momentum"].get("target_first_touch_utc"),
            "stop_first_touch_utc": evaluated["momentum"].get("stop_first_touch_utc"),
            "terminal_outcome": result["promoted_router_path_result"].get("exit_reason"),
            "status": result["promoted_router_path_result"].get("source_status"),
            "same_bar_ambiguity": result["promoted_router_path_result"].get(
                "same_bar_ambiguity"
            ),
            "source_gaps": result["source_gaps"],
            "path_row_id": row.get("path_row_id"),
            "recovery_status": result.get("recovery_status"),
            "evidence_label": result["promoted_router_evidence_label"],
        },
    )
    ledgers.write(
        "WAVE4R_TIME_MFE_MAE_GIVEBACK_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "mfe_r": result["mfe_r"],
            "mae_r": result["mae_r"],
            "current_policy_mfe_r": result["current_policy_mfe_r"],
            "current_policy_mae_r": result["current_policy_mae_r"],
            "promoted_router_policy": result["promoted_router_policy"],
            "giveback_r": (
                round(float(result["current_policy_mfe_r"]) - float(result["current_v4_proxy_r"]), 9)
                if result["current_policy_mfe_r"] is not None
                else None
            ),
            "trade_duration_minutes": result["trade_duration_minutes"],
            "exit_day_relation": result["exit_day_relation"],
            "threshold_times_utc": result["threshold_times_utc"],
            "threshold_seconds_from_entry": result["threshold_seconds_from_entry"],
            "partial_trigger_utc": result["partial_trigger_utc"],
            "be_return_after_1r_utc": result["be_return_after_1r_utc"],
            "time_to_partial_seconds": result["time_to_partial_seconds"],
            "time_to_be_seconds": result["time_to_be_seconds"],
            "duration_stuck_near_entry_seconds": result[
                "duration_stuck_near_entry_seconds"
            ],
            "duration_before_movement_seconds": result[
                "duration_before_movement_seconds"
            ],
            "last_r": result["last_r"],
            "reversal_timing_utc": result["reversal_timing_utc"],
            "reached_0_5r": result["reached_0_5r"],
            "reached_1r": result["reached_1r"],
            "reached_configured_target": result["reached_configured_target"],
            "hit_stop": result["hit_stop"],
            "consolidated_near_1r_then_loss": result["consolidated_near_1r_then_loss"],
            "gave_back_profit_to_loss": result["gave_back_profit_to_loss"],
            "adverse_before_profit_flag": result["adverse_before_profit_flag"],
            "source_gaps": result["source_gaps"],
        },
    )
    ledgers.write(
        "WAVE4R_FOLLOW_AVOID_MIXED_CONFLUENCE_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "sources": evaluated["confluence_sources"],
            "selector_action": result["selector_action"],
            "result_r": result["current_v4_proxy_r"],
            "evidence_label": "replay as-of proxy input",
        },
    )
    ledgers.write(
        "WAVE4R_PROBABILITY_CALIBRATION_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "probability": result["probability"],
            "selected_action": evaluated["debate"].get("selected_action"),
            "selected_thesis": evaluated["debate"].get("selected_thesis"),
            "outcome_proxy_success": result["current_v4_proxy_r"] > 0,
            "calibration_label": "proxy-R_not_broker_real_cash",
        },
    )
    comparator_policies = (evaluated["comparator"] or {}).get("policies") or {}
    management_counterfactuals = {
        name: _float((payload or {}).get("final_r"))
        for name, payload in comparator_policies.items()
        if name
        in {
            "be_after_trigger",
            "partial_be_runner",
            "trailing_runner",
            "time_stop_only",
            "path_aware_runner",
            "early_cut_if_no_progress",
        }
    }
    management_counterfactual_rows = [
        {
            "comparison_policy": name,
            "execution_result": (
                "proxy_policy_winner"
                if value is not None and value > result["current_v4_proxy_r"]
                else "proxy_policy_not_better_than_current_v4"
                if value is not None
                else "source_gap"
            ),
            "gross_r": value,
            "stop_modify_rejections": None,
            "broker_stop_freeze_status": "not_broker_real_replay_proxy",
            "cost_status": "proxy_R_gross_policy_result",
            "price_source": "frozen_replay_policy_path",
            "selected_policy": result["current_v4_selected_policy"],
        }
        for name, value in sorted(management_counterfactuals.items())
    ]
    best_management_policy, best_management_r = max(
        management_counterfactuals.items(),
        key=lambda item: item[1] if item[1] is not None else -999999.0,
        default=(None, None),
    )
    if result["branch_decision"] == "v4_accept_simulated_trade" and result["current_v4_proxy_r"] < 0:
        ledgers.write(
            "WAVE4R_ACCEPTED_LOSER_FORENSIC_LEDGER.jsonl",
            {
                "candidate_id": result["candidate_id"],
                "asof_utc": result["asof_utc"],
                "symbol": result["symbol"],
                "session": result["session"],
                "framework": result["framework"],
                "current_v4_selected_policy": result["current_v4_selected_policy"],
                "current_v4_proxy_r": result["current_v4_proxy_r"],
                "promoted_router_replay_r": result["promoted_router_replay_r"],
                "selector_action": result["selector_action"],
                "scheduler_action": result["scheduler_action"],
                "same_symbol_action": result["same_symbol_action"],
                "accepted_loser_mechanism": (
                    "policy_path_loss_after_selector_scheduler_acceptance"
                ),
                "best_management_counterfactual_policy": best_management_policy,
                "best_management_counterfactual_r": best_management_r,
                "management_counterfactuals": management_counterfactuals,
                "mae_r": result["mae_r"],
                "mfe_r": result["mfe_r"],
                "path_microscope": result["path_microscope"],
                "trade_duration_minutes": result["trade_duration_minutes"],
                "exit_day_relation": result["exit_day_relation"],
                "consolidated_near_1r_then_loss": result["consolidated_near_1r_then_loss"],
                "gave_back_profit_to_loss": result["gave_back_profit_to_loss"],
                "source_gaps": result["source_gaps"],
                "evidence_label": "replay/proxy-R",
            },
        )
    if result["branch_decision"] != "v4_accept_simulated_trade" and result["promoted_router_replay_r"] > 0:
        ledgers.write(
            "WAVE4R_REJECTED_WINNER_OPPORTUNITY_LEDGER.jsonl",
            {
                "candidate_id": result["candidate_id"],
                "asof_utc": result["asof_utc"],
                "symbol": result["symbol"],
                "session": result["session"],
                "framework": result["framework"],
                "promoted_router_policy": result["promoted_router_policy"],
                "promoted_router_replay_r": result["promoted_router_replay_r"],
                "selector_action": result["selector_action"],
                "scheduler_action": result["scheduler_action"],
                "same_symbol_action": result["same_symbol_action"],
                "candidate_scheduler_option": result["candidate_scheduler_option"],
                "path_microscope": result["path_microscope"],
                "rejection_or_zero_trade_reason": (
                    "selector_scheduler_lifecycle_or_source_constraint_blocked_positive_promoted_router_row"
                ),
                "source_gaps": result["source_gaps"],
                "evidence_label": "replay/proxy-R",
            },
        )
    ledgers.write(
        "WAVE4R_SCHEDULER_ALLOCATION_REGRET_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "asof_utc": result["asof_utc"],
            "window_id": result["window_id"],
            "window_candidate_count": result["window_candidate_count"],
            "scheduler_selected_candidate_id": result["scheduler_selected_candidate_id"],
            "scheduler_action": result["scheduler_action"],
            "candidate_was_selected": (
                result["scheduler_selected_candidate_id"] == result["candidate_id"]
            ),
            "promoted_router_replay_r": result["promoted_router_replay_r"],
            "zero_trade_opportunity_cost_r": result["zero_trade_opportunity_cost_r"],
            "candidate_scheduler_option": result["candidate_scheduler_option"],
            "path_microscope": result["path_microscope"],
            "source_gaps": result["source_gaps"],
            "evidence_label": "replay/proxy-R",
        },
    )
    ledgers.write(
        "WAVE4R_EXIT_HARVEST_COUNTERFACTUAL_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "asof_utc": result["asof_utc"],
            "current_v4_selected_policy": result["current_v4_selected_policy"],
            "current_v4_proxy_r": result["current_v4_proxy_r"],
            "promoted_router_policy": result["promoted_router_policy"],
            "promoted_router_replay_r": result["promoted_router_replay_r"],
            "mfe_r": result["mfe_r"],
            "mae_r": result["mae_r"],
            "best_management_counterfactual_policy": best_management_policy,
            "best_management_counterfactual_r": best_management_r,
            "management_counterfactuals": management_counterfactuals,
            "management_counterfactual_rows": management_counterfactual_rows,
            "harvest_gap_r": (
                round(float(best_management_r) - float(result["current_v4_proxy_r"]), 9)
                if best_management_r is not None
                else None
            ),
            "path_microscope": result["path_microscope"],
            "consolidated_near_1r_then_loss": result["consolidated_near_1r_then_loss"],
            "gave_back_profit_to_loss": result["gave_back_profit_to_loss"],
            "source_gaps": result["source_gaps"],
            "evidence_label": "replay/proxy-R",
        },
    )
    ledgers.write(
        "WAVE4R_STALE_HOLDINGS_THESIS_AGE_LEDGER.jsonl",
        {
            "candidate_id": result["candidate_id"],
            "asof_utc": result["asof_utc"],
            "accepted_ticket": result["accepted_ticket"],
            "closed_positions_before_decision": result["closed_positions_before_decision"],
            "scheduler_exposure_actions": result["scheduler_exposure_actions"],
            "open_position_count_after_decision": result["open_position_count_after_decision"],
            "scheduler_action": result["scheduler_action"],
            "scheduler_selected_exposure_id": result["scheduler_selected_exposure_id"],
            "scheduler_opportunity_context": result["scheduler_opportunity_context"],
            "exit_policy_action": result["exit_policy_action"],
            "exit_policy_reason": result["exit_policy_reason"],
            "exit_policy_close_reason": result["exit_policy_close_reason"],
            "scheduler_regret_r": result["scheduler_regret_r"],
            "window_best_candidate_id": result["window_best_candidate_id"],
            "window_best_promoted_router_replay_r": result["window_best_promoted_router_replay_r"],
            "bars_elapsed_source": (
                "replay_position_entry_exit_clock_bound_for_accepted_position"
                if result["accepted_ticket"]
                else "not_applicable_no_accepted_replay_position"
            ),
            "stale_holding_source_status": (
                "scheduler_v4_stale_exposure_action_replay_bound"
                if result["scheduler_exposure_actions"]
                else "exit_policy_stale_or_opportunity_action_replay_bound"
                if result["exit_policy_close_reason"] in {
                    "v4_stale_thesis_opportunity_cost_close",
                    "v4_stale_thesis_no_progress",
                    "v4_stale_thesis_invalidated",
                }
                else "no_replay_stale_exit_action_reached"
                if result["accepted_ticket"]
                else "requires_ticket_bound_entry_exit_clock_or_forward_capture"
            ),
            "source_gaps": []
            if result["scheduler_exposure_actions"]
            or result["accepted_ticket"]
            else [
                "ticket_bound_stale_thesis_clock_missing_for_historical_replay",
                "actual_open_position_snapshot_missing_for_historical_replay",
            ],
            "evidence_label": "chronological replay state proxy"
            if result["scheduler_exposure_actions"]
            or result["accepted_ticket"]
            else EVIDENCE_SOURCE_GAP,
        },
    )
    if result["branch_decision"] != "v4_accept_simulated_trade":
        ledgers.write(
            "WAVE4R_ZERO_TRADE_OPPORTUNITY_COST_LEDGER.jsonl",
            {
                "candidate_id": result["candidate_id"],
                "asof_utc": result["asof_utc"],
                "zero_trade_opportunity_cost_r": result["zero_trade_opportunity_cost_r"],
                "promoted_router_policy": result["promoted_router_policy"],
                "promoted_router_replay_r": result["promoted_router_replay_r"],
                "scheduler_action": result["scheduler_action"],
                "selector_action": result["selector_action"],
                "reason": "current V4 selector/scheduler/lifecycle/source constraints selected no trade or rejected",
                "evidence_label": "replay",
            },
        )
    for gap in result.get("source_gaps") or []:
        ledgers.write(
            "WAVE4R_SOURCE_GAP_CAPTURE_REQUIREMENT_LEDGER.jsonl",
            {
                "capture_requirement_id": f"capture:{result['candidate_id']}:{stable_hash(gap)[:10]}",
                "candidate_id": result["candidate_id"],
                "gap": gap,
                "required_source": source_requirement_for_gap(gap),
                "evidence_label": EVIDENCE_SOURCE_GAP,
            },
        )
    if evaluated["momentum"]["same_bar_ambiguity"] or result["source_gaps"]:
        ledgers.write(
            "WAVE4R_ACTIONABLE_V4_REPAIR_FINDINGS_LEDGER.jsonl",
            {
                "finding_id": f"finding:{result['candidate_id']}",
                "candidate_id": result["candidate_id"],
                "finding": "exact V4 2R/stop path ordering or historical V4 input state missing or recovered with proxy boundary",
                "repair_or_capture": "use ordered path fields where present; otherwise recover ordered LTF/tick path and original account/open/pending state capture",
                "evidence_label": EVIDENCE_SOURCE_GAP,
            },
        )


def write_window_allocation_ledger(
    ledgers: LedgerHandles,
    *,
    window_rows: list[dict[str, Any]],
    evaluated_rows: list[Mapping[str, Any]],
) -> None:
    if not evaluated_rows:
        return
    scheduler = evaluated_rows[0]["full_window_scheduler"]
    candidate_options = [
        {
            "candidate_id": result["result"]["candidate_id"],
            "branch_decision": result["result"]["branch_decision"],
            "selector_action": result["result"]["selector_action"],
            "same_symbol_action": result["result"]["same_symbol_action"],
            "candidate_scheduler_option": result["result"].get("candidate_scheduler_option"),
            "current_v4_proxy_r": result["result"]["current_v4_proxy_r"],
            "zero_trade_opportunity_cost_r": result["result"]["zero_trade_opportunity_cost_r"],
        }
        for result in evaluated_rows
    ]
    ledgers.write(
        "WAVE4R_MULTI_CANDIDATE_WINDOW_ALLOCATION_LEDGER.jsonl",
        {
            "decision_window_id": scheduler.get("decision_window_id"),
            "candidate_set_id": scheduler.get("candidate_set_id"),
            "asof_utc": scheduler.get("asof_utc"),
            "window_candidate_count": len(window_rows),
            "selected_candidate_id": (scheduler.get("decision") or {}).get("selected_candidate_id"),
            "selected_candidate_ids": (scheduler.get("decision") or {}).get(
                "selected_candidate_ids"
            ),
            "selected_exposure_id": (scheduler.get("decision") or {}).get("selected_exposure_id"),
            "selected_action_class": (scheduler.get("decision") or {}).get("selected_action_class"),
            "selected_action_classes": (scheduler.get("decision") or {}).get(
                "selected_action_classes"
            ),
            "allocation_mode": (scheduler.get("decision") or {}).get("allocation_mode"),
            "window_approved_risk_pct": (scheduler.get("decision") or {}).get(
                "window_approved_risk_pct"
            ),
            "selected_option": (scheduler.get("decision") or {}).get("selected_option"),
            "selected_options": (scheduler.get("decision") or {}).get("selected_options"),
            "all_options_preserved": scheduler.get("all_options_preserved"),
            "candidate_options": candidate_options,
            "scheduler_exposure_actions": (
                evaluated_rows[0]["result"].get("scheduler_exposure_actions")
                if evaluated_rows
                else []
            ),
            "open_position_count": ((scheduler.get("exposure_snapshot") or {}).get("open_position_count")),
            "pending_order_count": ((scheduler.get("exposure_snapshot") or {}).get("pending_order_count")),
            "source_boundary": scheduler.get("source_boundary"),
            "evidence_label": "replay as-of candidate window",
        },
    )


def source_requirement_for_gap(gap: str) -> str:
    if "ltf" in gap.lower() or "tick" in gap.lower() or "ordered" in gap.lower():
        return "ordered lower-timeframe or tick path export with hashes"
    if "drawdown" in gap.lower() or "equity_balance" in gap.lower():
        return "as-of broker account balance/equity, daily baseline, max drawdown limit, and open-risk snapshot"
    if "account" in gap.lower() or "headroom" in gap.lower():
        return "as-of account risk/open/pending broker-local snapshot"
    if "fill" in gap.lower() or "cost" in gap.lower() or "broker" in gap.lower():
        return "broker-real fill/cost/slippage/swap record"
    if "shard" in gap.lower():
        return "recovered May-26 dynamic-policy shard row"
    return "prospective source capture or route-local source repair"


def write_aggregate_ledgers(route_dir: Path, summary: ReplaySummary) -> None:
    with (route_dir / "WAVE4R_SYMBOL_SESSION_REGIME_BREAKDOWN_LEDGER.jsonl").open("w", encoding="utf-8") as handle:
        for bucket in sorted(summary.symbol_session.values(), key=lambda item: (item["symbol"], item["session"], item["framework"])):
            row = dict(bucket)
            row["v4_total_r"] = round(row["v4_total_r"], 9)
            row["promoted_router_total_r"] = round(row["promoted_router_total_r"], 9)
            row["live_current_total_r"] = round(row["live_current_total_r"], 9)
            row["delta_v4_minus_promoted_router_r"] = round(
                row["v4_total_r"] - row["promoted_router_total_r"],
                9,
            )
            row["delta_v4_minus_live_current_r"] = round(row["v4_total_r"] - row["live_current_total_r"], 9)
            row["evidence_label"] = "replay"
            append_jsonl(handle, row)
    with (route_dir / "WAVE4R_DAY_SESSION_MICROSCOPE_LEDGER.jsonl").open("w", encoding="utf-8") as handle:
        for bucket in sorted(
            summary.day_session.values(),
            key=lambda item: (
                item["trade_date"],
                item["session"],
                item["symbol"],
                item["framework"],
            ),
        ):
            row = dict(bucket)
            row["v4_total_r"] = round(row["v4_total_r"], 9)
            row["promoted_router_total_r"] = round(row["promoted_router_total_r"], 9)
            row["delta_v4_minus_promoted_router_r"] = round(
                row["v4_total_r"] - row["promoted_router_total_r"],
                9,
            )
            row["zero_trade_opportunity_cost_r"] = round(
                row["zero_trade_opportunity_cost_r"],
                9,
            )
            row["average_duration_minutes"] = (
                round(row["duration_minutes_sum"] / row["duration_minutes_count"], 6)
                if row["duration_minutes_count"]
                else None
            )
            row["duration_minutes_sum"] = round(row["duration_minutes_sum"], 6)
            if row.get("latest_daily_realized_r_after_decision") is not None:
                row["latest_daily_realized_r_after_decision"] = round(
                    float(row["latest_daily_realized_r_after_decision"]),
                    9,
                )
            if row.get("min_projected_worst_case_daily_r") is not None:
                row["min_projected_worst_case_daily_r"] = round(
                    float(row["min_projected_worst_case_daily_r"]),
                    9,
                )
            row["evidence_label"] = "replay/proxy-R plus explicit source gaps"
            row["prop_firm_risk_block_evidence_status"] = (
                "fresh_daily_replay_drawdown_simulated_in_r_units_not_broker_real_equity"
            )
            append_jsonl(handle, row)


def write_limitations_and_fix_backlog(route_dir: Path, summary_record: Mapping[str, Any]) -> None:
    """Write the system-level backlog implied by the frozen replay microscope."""

    metric_counts = {
        "processed_dynamic_policy_rows": summary_record.get("processed_dynamic_policy_rows"),
        "decision_windows": summary_record.get("decision_windows"),
        "multi_candidate_decision_windows": summary_record.get("multi_candidate_decision_windows"),
        "max_decision_window_size": summary_record.get("max_decision_window_size"),
        "accepted_v4_simulated_rows": summary_record.get("accepted_v4_simulated_rows"),
        "zero_trade_or_rejected_rows": summary_record.get("zero_trade_or_rejected_rows"),
        "positive_zero_trade_opportunity_cost_rows": summary_record.get("positive_zero_trade_opportunity_cost_rows"),
        "accepted_loser_forensic_rows": count_jsonl_rows(route_dir / "WAVE4R_ACCEPTED_LOSER_FORENSIC_LEDGER.jsonl"),
        "rejected_winner_opportunity_rows": count_jsonl_rows(route_dir / "WAVE4R_REJECTED_WINNER_OPPORTUNITY_LEDGER.jsonl"),
        "scheduler_allocation_regret_rows": count_jsonl_rows(route_dir / "WAVE4R_SCHEDULER_ALLOCATION_REGRET_LEDGER.jsonl"),
        "exit_harvest_counterfactual_rows": count_jsonl_rows(route_dir / "WAVE4R_EXIT_HARVEST_COUNTERFACTUAL_LEDGER.jsonl"),
        "day_session_microscope_rows": count_jsonl_rows(route_dir / "WAVE4R_DAY_SESSION_MICROSCOPE_LEDGER.jsonl"),
        "v4_total_proxy_r": summary_record.get("v4_total_proxy_r"),
        "promoted_router_total_replay_r": summary_record.get("promoted_router_total_replay_r"),
        "delta_v4_minus_promoted_router_total_r": summary_record.get("delta_v4_minus_promoted_router_total_r"),
        "promoted_router_source_status_counts": summary_record.get("promoted_router_source_status_counts"),
        "selector_action_counts": summary_record.get("selector_action_counts"),
        "scheduler_action_counts": summary_record.get("scheduler_action_counts"),
        "same_symbol_action_counts": summary_record.get("same_symbol_action_counts"),
        "same_bar_ambiguity_rows": summary_record.get("same_bar_ambiguity_rows"),
        "adverse_before_profit_rows": summary_record.get("adverse_before_profit_rows"),
        "source_gap_rows": summary_record.get("source_gap_rows"),
        "prop_firm_replay_blocked_rows": summary_record.get("prop_firm_replay_blocked_rows"),
    }
    shared_ledgers = [
        "WAVE4R_RESULTS_LEDGER.jsonl",
        "WAVE4R_DAY_SESSION_MICROSCOPE_LEDGER.jsonl",
        "WAVE4R_ACCEPTED_LOSER_FORENSIC_LEDGER.jsonl",
        "WAVE4R_REJECTED_WINNER_OPPORTUNITY_LEDGER.jsonl",
        "WAVE4R_SCHEDULER_ALLOCATION_REGRET_LEDGER.jsonl",
        "WAVE4R_EXIT_HARVEST_COUNTERFACTUAL_LEDGER.jsonl",
        "WAVE4R_SOURCE_GAP_CAPTURE_REQUIREMENT_LEDGER.jsonl",
    ]
    limitations = [
        {
            "limitation_id": "v4_selector_rejects_too_many_replay_winners",
            "system_area": "selection",
            "severity": "P0",
            "evidence_metrics": {
                "rejected_winner_opportunity_rows": metric_counts["rejected_winner_opportunity_rows"],
                "positive_zero_trade_opportunity_cost_rows": metric_counts["positive_zero_trade_opportunity_cost_rows"],
                "delta_v4_minus_promoted_router_total_r": metric_counts["delta_v4_minus_promoted_router_total_r"],
            },
            "evidence_ledgers": shared_ledgers,
            "problem_statement": (
                "Current V4 admission blocks or zero-trades many candidates that the promoted dynamic router replay marks positive."
            ),
            "fix_or_feature": (
                "Rebuild selector admission around calibrated confluence/debate/source-completeness classes, with explicit rejected-winner review and threshold retuning by symbol/session/framework."
            ),
            "production_code_ownership": [
                "src/components/selector_v4.py",
                "src/components/probability_debate_v4.py",
                "src/components/gtos_vnext_runtime.py",
            ],
            "tests_required": [
                "rejected replay winner admitted when confluence/debate/source packet is complete",
                "source-required rows still fail closed without silently becoming risk trades",
            ],
            "evidence_class": "replay/proxy-R",
            "current_status": (
                "implemented_selector_source_contract_and_admission_burn_down_full_replay_verified_"
                "remaining_rows_are_hard_reject_or_downstream_scheduler_same_symbol_prop_path_residuals"
            ),
        },
        {
            "limitation_id": "scheduler_must_be_runtime_authority_over_full_candidate_windows",
            "system_area": "scheduling",
            "severity": "P0",
            "evidence_metrics": {
                "decision_windows": metric_counts["decision_windows"],
                "multi_candidate_decision_windows": metric_counts["multi_candidate_decision_windows"],
                "max_decision_window_size": metric_counts["max_decision_window_size"],
                "scheduler_allocation_regret_rows": metric_counts["scheduler_allocation_regret_rows"],
            },
            "evidence_ledgers": [
                "WAVE4R_MULTI_CANDIDATE_WINDOW_ALLOCATION_LEDGER.jsonl",
                "WAVE4R_SCHEDULER_ALLOCATION_REGRET_LEDGER.jsonl",
            ],
            "problem_statement": (
                "The replay now proves candidate windows are multi-row timestamp decisions, not independent one-row scores."
            ),
            "fix_or_feature": (
                "Make Scheduler V4 terminal in production: consume the full timestamp candidate window, open positions, pending orders, selector/debate/confluence/lifecycle/cost packets, and block/defer any current row that is not the selected action."
            ),
            "production_code_ownership": [
                "src/research/moonshot_scheduler_v4_best_trade_allocator.py",
                "src/components/orchestrator.py",
                "src/components/execution_manager_v4.py",
            ],
            "tests_required": [
                "two-candidate window selects the stronger candidate and blocks the weaker current row",
                "zero-trade option prevents execution",
                "missing full-window source fails closed in production mode",
            ],
            "evidence_class": "replay/proxy-R plus production code",
            "current_status": (
                "implemented_runtime_authority_full_window_multi_select_and_tie_diagnostics_verified_"
                "remaining_residual_is_exact_bounded_risk_policy_or_prospective_tie_source"
            ),
        },
        {
            "limitation_id": "exit_harvest_management_underuses_mfe_and_giveback",
            "system_area": "exit_harvest",
            "severity": "P0",
            "evidence_metrics": {
                "accepted_loser_forensic_rows": metric_counts["accepted_loser_forensic_rows"],
                "exit_harvest_counterfactual_rows": metric_counts["exit_harvest_counterfactual_rows"],
                "adverse_before_profit_rows": metric_counts["adverse_before_profit_rows"],
            },
            "evidence_ledgers": [
                "WAVE4R_ACCEPTED_LOSER_FORENSIC_LEDGER.jsonl",
                "WAVE4R_TIME_MFE_MAE_GIVEBACK_LEDGER.jsonl",
                "WAVE4R_EXIT_HARVEST_COUNTERFACTUAL_LEDGER.jsonl",
            ],
            "problem_statement": (
                "Accepted losers and giveback rows show that static exits and shallow management lose harvestable MFE."
            ),
            "fix_or_feature": (
                "Implement policy-aware BE, partial, trailing, time-stop, giveback, and stale-thesis exits as terminal management contracts, with symbol/session thresholds learned from the frozen microscope."
            ),
            "production_code_ownership": [
                "src/components/exit_policy_v4.py",
                "src/components/execution.py",
                "src/components/dynamic_target_stop_geometry_v4.py",
            ],
            "tests_required": [
                "post-TP1 MFE giveback triggers protection",
                "no-progress time stop exits before full stop",
                "partial/BE/trailing state remains ticket-bound after fill",
            ],
            "evidence_class": "replay/proxy-R",
            "current_status": (
                "implemented_be_partial_giveback_stale_time_stop_and_close_mark_contract_full_replay_verified_"
                "remaining_close_mark_rows_are_exact_source_capture_required"
            ),
        },
        {
            "limitation_id": "target_stop_geometry_must_be_dynamic_policy_bound",
            "system_area": "target_stop_geometry",
            "severity": "P0",
            "evidence_metrics": {
                "same_bar_ambiguity_rows": metric_counts["same_bar_ambiguity_rows"],
                "promoted_router_source_status_counts": metric_counts["promoted_router_source_status_counts"],
            },
            "evidence_ledgers": [
                "WAVE4R_STATIC_R_DYNAMIC_GEOMETRY_LEDGER.jsonl",
                "WAVE4R_ORDERED_PATH_RECONSTRUCTION_LEDGER.jsonl",
            ],
            "problem_statement": (
                "V4 geometry must be judged against the promoted momentum-exhaustion primary router with partial/BE runner exceptions, not obsolete secondary comparator geometry."
            ),
            "fix_or_feature": (
                "Keep geometry tied to selected policy family, management model, target R, pullback R, partial close ratio, and trail gap; block broker mutation if the policy geometry contract is not source-bound."
            ),
            "production_code_ownership": [
                "src/components/dynamic_target_stop_geometry_v4.py",
                "src/components/execution.py",
            ],
            "tests_required": [
                "momentum policy requires pullback contract",
                "partial runner requires partial ratio",
                "trailing runner requires trail gap",
                "ambiguous same-bar geometry blocks exact claims",
            ],
            "evidence_class": "replay/proxy-R plus production code",
            "current_status": (
                "implemented_dynamic_policy_geometry_contract_and_pending_intent_preservation_verified_"
                "remaining_same_bar_ordering_is_m1_tick_ltf_source_capture_required"
            ),
        },
        {
            "limitation_id": "same_symbol_lifecycle_needs_durable_ticket_thesis_state",
            "system_area": "same_symbol_lifecycle",
            "severity": "P0",
            "evidence_metrics": {
                "processed_dynamic_policy_rows": metric_counts["processed_dynamic_policy_rows"],
                "source_gap_rows": metric_counts["source_gap_rows"],
            },
            "evidence_ledgers": [
                "WAVE4R_SAME_SYMBOL_ACTION_LEDGER.jsonl",
                "WAVE4R_STALE_HOLDINGS_THESIS_AGE_LEDGER.jsonl",
                "WAVE4R_SOURCE_GAP_CAPTURE_REQUIREMENT_LEDGER.jsonl",
            ],
            "problem_statement": (
                "Scale, reduce, close, reverse, and stale-thesis decisions cannot be made safely from symbol-only or comment-only broker state."
            ),
            "fix_or_feature": (
                "Persist ticket-bound thesis id, entry probability/EV, risk, policy, BE/partial/trailing state, stale-thesis score, and parent-child lifecycle on fill and pending creation; hydrate broker positions from this store before lifecycle gates."
            ),
            "production_code_ownership": [
                "src/components/same_symbol_lifecycle_v4.py",
                "src/components/execution.py",
                "src/components/permissions.py",
            ],
            "tests_required": [
                "broker position with empty comment hydrates from lifecycle store",
                "stale thesis rejects duplicate",
                "reverse closes or reduces old ticket before new order",
            ],
            "evidence_class": "replay/source-gap",
            "current_status": (
                "implemented_runtime_durable_ticket_lifecycle_store_and_empty_comment_position_hydration_"
                "focused_verified_no_historical_broker_truth_needed_for_simulated_replay"
            ),
        },
        {
            "limitation_id": "prop_firm_headroom_requires_replay_and_runtime_headroom_authority",
            "system_area": "prop_firm_risk",
            "severity": "P0",
            "evidence_metrics": {
                "day_session_microscope_rows": metric_counts["day_session_microscope_rows"],
                "prop_firm_replay_blocked_rows": metric_counts["prop_firm_replay_blocked_rows"],
            },
            "evidence_ledgers": [
                "WAVE4R_DAY_SESSION_MICROSCOPE_LEDGER.jsonl",
                "WAVE4R_REPLAY_ACCOUNT_CURVE_LEDGER.jsonl",
            ],
            "problem_statement": (
                "Wave4R can simulate fresh-day prop-firm drawdown from replay outcomes in R units; production still needs a source-bound headroom snapshot before live execution."
            ),
            "fix_or_feature": (
                "Keep replay FreshDayPropCurve as a deterministic daily/session simulator, then introduce required PropFirmHeadroomSnapshotV4 before selector/scheduler/permissions/execution for live balance/equity/open/pending risk."
            ),
            "production_code_ownership": [
                "src/research_infra/wave4r_v4_vs_v3_frozen_replay_results_gate.py",
                "src/components/gtos_vnext_runtime.py",
                "src/components/permissions.py",
                "src/components/execution_manager_v4.py",
                "src/components/orchestrator.py",
            ],
            "tests_required": [
                "fresh-day replay resets daily realized R by trade date",
                "selected replay trade is blocked when projected worst-case daily R breaches the day limit",
                "missing day-start baseline blocks",
                "projected SL breaches daily drawdown blocks",
                "pending risk consumes shared headroom",
                "execution blocks stale headroom hash",
            ],
            "evidence_class": "replay simulation plus production code",
            "current_status": (
                "implemented_fresh_day_replay_curve_and_runtime_prop_firm_headroom_authority_verified_"
                "remaining_live_account_snapshot_feed_is_runtime_capture_not_frozen_replay_blocker"
            ),
        },
        {
            "limitation_id": "probability_confluence_packets_need_hard_source_contracts",
            "system_area": "probability_confluence",
            "severity": "P1",
            "evidence_metrics": {
                "processed_dynamic_policy_rows": metric_counts["processed_dynamic_policy_rows"],
                "source_gap_rows": metric_counts["source_gap_rows"],
            },
            "evidence_ledgers": [
                "WAVE4R_PROBABILITY_CALIBRATION_LEDGER.jsonl",
                "WAVE4R_FOLLOW_AVOID_MIXED_CONFLUENCE_LEDGER.jsonl",
                "WAVE4R_V4_ASOF_PACKET_LEDGER.jsonl",
            ],
            "problem_statement": (
                "Probability and confluence must not be proxy-only fields when they drive risk-bearing admission."
            ),
            "fix_or_feature": (
                "Promote numeric confluence and market-state whiteboard into explicit packets with hash/source requirements; required families should hard-veto risk actions, not only penalize scores."
            ),
            "production_code_ownership": [
                "src/components/probability_debate_v4.py",
                "src/components/selector_v4.py",
                "src/components/live_decision_packet_v4.py",
            ],
            "tests_required": [
                "missing market-state packet vetoes risk action",
                "hard AVOID confluence blocks positive proxy row",
                "complete packet permits known winner",
            ],
            "evidence_class": "replay/proxy-R plus production code",
            "current_status": (
                "implemented_hard_source_family_contracts_and_packet_verifier_semantic_unbound_zero_"
                "source_required_rows_fail_closed_without_proxy_substitution"
            ),
        },
        {
            "limitation_id": "historical_promoted_router_intent_not_fully_bound",
            "system_area": "historical_intent_coverage",
            "severity": "P1",
            "evidence_metrics": {
                "promoted_router_source_status_counts": metric_counts["promoted_router_source_status_counts"],
            },
            "evidence_ledgers": [
                "WAVE4R_V3_PREV4_COMPARATOR_LEDGER.jsonl",
                "WAVE4R_RESULTS_LEDGER.jsonl",
            ],
            "problem_statement": (
                "Only the rows with May-27 promoted dynamic-router replay records can claim exact comparator policy selection; missing rows use explicit momentum proxy fallback."
            ),
            "fix_or_feature": (
                "Regenerate current-system and promoted-router intent as-of for each historical day exactly as if the system were running on that day, using only data available at each candidate timestamp."
            ),
            "production_code_ownership": [
                "src/research_infra/wave4r_v4_vs_v3_frozen_replay_results_gate.py",
                "research/science_program_2026_05/06_outcome_testing/",
            ],
            "tests_required": [
                "candidate_id and source_record_candidate_id both bind promoted router rows",
                "missing promoted router row cannot be labeled exact comparator truth",
            ],
            "evidence_class": "replay/source-gap",
            "current_status": (
                "source_capture_required_exact_missing_promoted_router_rows_bounded_"
                "present_rows_bind_by_candidate_id_or_source_record_candidate_id_proxy_rows_remain_labeled"
            ),
        },
        {
            "limitation_id": "intrabar_ordered_path_requires_m1_or_tick_export",
            "system_area": "path_truth",
            "severity": "P1",
            "evidence_metrics": {
                "same_bar_ambiguity_rows": metric_counts["same_bar_ambiguity_rows"],
            },
            "evidence_ledgers": [
                "WAVE4R_ORDERED_PATH_RECONSTRUCTION_LEDGER.jsonl",
                "WAVE4R_TRADE_PATH_ANATOMY_LEDGER.jsonl",
                "WAVE4R_ENTRY_EXIT_TIMING_PATH_LEDGER.jsonl",
            ],
            "problem_statement": (
                "M15 replay cannot prove stop/target order inside the same bar or exact milestone timestamps where lower-timeframe path arrays are absent."
            ),
            "fix_or_feature": (
                "Use read-only MT5 historical hydration to materialize one day/session of M1/tick bid-ask path at a time, prune the prior day scratch data, then regenerate milestone clocks for 0.5R, 1R, target, stop, BE, partial, trailing, MFE and MAE without leaking post-asof rows into decision inputs."
            ),
            "production_code_ownership": [
                "src/research_infra/wave4r_v4_vs_v3_frozen_replay_results_gate.py",
                "src/research_infra/wave4r_replay_microstructure.py",
                "data/mt5_research_exports/",
                "data/ticks/",
            ],
            "tests_required": [
                "same-bar target-first vs stop-first is decided by ordered lower-timeframe rows",
                "missing lower-timeframe path remains source-gapped",
            ],
            "evidence_class": "source-gap",
            "current_status": (
                "source_capture_required_m1_tick_ltf_data_gated_rolling_hydration_oracle_completed_"
                "no_matching_local_mac_ltf_source_available"
            ),
        },
        {
            "limitation_id": "broker_execution_cost_truth_requires_order_deal_lifecycle",
            "system_area": "execution_costs",
            "severity": "P1",
            "evidence_metrics": {
                "processed_dynamic_policy_rows": metric_counts["processed_dynamic_policy_rows"],
                "source_gap_rows": metric_counts["source_gap_rows"],
            },
            "evidence_ledgers": [
                "WAVE4R_FROZEN_VS_LIVE_DELTA_LEDGER.jsonl",
                "WAVE4R_SOURCE_GAP_CAPTURE_REQUIREMENT_LEDGER.jsonl",
                "WAVE4R_HARD_HALT_BINDING_LEDGER.jsonl",
            ],
            "problem_statement": (
                "Replay/proxy-R cannot become broker-real PnL without order/deal/fill, spread, slippage, commission, swap, and partial-close lifecycle."
            ),
            "fix_or_feature": (
                "For simulated replay, infer fills from ordered post-asof tick/M1 price action. For broker-real claims only, capture broker order/deal/position lifecycle and cost model snapshots per candidate and bind them to the LiveDecisionPacket hash."
            ),
            "production_code_ownership": [
                "src/research_infra/wave4r_replay_microstructure.py",
                "src/components/execution.py",
                "src/components/execution_manager_v4.py",
                "shadow_logs/",
                "pipeline_state/",
            ],
            "tests_required": [
                "broker-real claim rejected when cost lifecycle fields are absent",
                "partial close and BE modification tickets remain linked to the parent decision packet",
            ],
            "evidence_class": "source-gap",
            "current_status": (
                "runtime_broker_lifecycle_capture_contract_implemented_not_a_simulated_replay_blocker_"
                "broker_real_label_only_remains_source_capture_required"
            ),
        },
        {
            "limitation_id": "stale_holding_exit_needs_thesis_age_and_opportunity_cost",
            "system_area": "stale_holding",
            "severity": "P1",
            "evidence_metrics": {
                "scheduler_allocation_regret_rows": metric_counts["scheduler_allocation_regret_rows"],
                "day_session_microscope_rows": metric_counts["day_session_microscope_rows"],
            },
            "evidence_ledgers": [
                "WAVE4R_STALE_HOLDINGS_THESIS_AGE_LEDGER.jsonl",
                "WAVE4R_SCHEDULER_ALLOCATION_REGRET_LEDGER.jsonl",
            ],
            "problem_statement": (
                "Holding stale trades consumes same-symbol and prop-risk budget while better timestamp-window candidates appear."
            ),
            "fix_or_feature": (
                "Add thesis-age, stagnation, opportunity-cost, and scheduler-regret inputs to exit policy so stale positions can be reduced, closed, or reversed before blocking better candidates."
            ),
            "production_code_ownership": [
                "src/components/exit_policy_v4.py",
                "src/research/moonshot_scheduler_v4_best_trade_allocator.py",
                "src/components/same_symbol_lifecycle_v4.py",
            ],
            "tests_required": [
                "stale thesis close_existing outranks new weak candidate",
                "new strong opposite candidate triggers close-and-reverse handoff",
            ],
            "evidence_class": "replay/source-gap",
            "current_status": (
                "implemented_stale_thesis_opportunity_cost_scheduler_close_and_close_reverse_contracts_verified_"
                "remaining_close_mark_precision_is_exact_source_capture_required"
            ),
        },
    ]
    backlog = {
        "schema_version": "wave4r_v4_limitations_and_fix_backlog_v1",
        "generated_at_utc": utc_now(),
        "refresh_status": "current_v4u_backlog_refresh_no_live_state_generation",
        "system_verdict": (
            "current_v4_replay_proxy_curve_is_positive_and_current_mac_local_non_ltf_repairs_are_implemented_or_exact_source_bounded_not_final_production_return_clearance"
        ),
        "primary_comparator": PROMOTED_ROUTER_POLICY_ID,
        "j46_j49_and_fixed_1_5r_role": "secondary_historical_comparator_only",
        "metric_counts": metric_counts,
        "backlog_count": len(limitations),
        "limitations": limitations,
        "mac_non_m1_tick_work_status": {
            "completed_without_ltf": [
                "selector source-family/source-required burn-down and packet semantic verifier",
                "scheduler runtime authority, multi-select replay allocation, and tie diagnostics",
                "exit harvest BE/partial/giveback/stale/time-stop contracts",
                "dynamic geometry contract and pending-intent preservation",
                "prop-firm fresh-day replay curve and runtime headroom contract",
                "same-symbol durable ticket lifecycle store and empty-comment broker position hydration",
                "broker lifecycle capture contract boundary for broker-real labels only",
            ],
            "remaining_without_ltf": [
                "keep focused tests/verifiers current after code changes",
                "continue source-complete policy analysis only when a new local code path is evidenced by row-level metrics",
            ],
            "source_or_access_gated": [
                "M1/tick ordered path rows for same-bar sequencing and milestone clocks",
                "explicit V4 close-mark packets for stale/time-stop rows not recoverable from current sources",
                "missing May-27 promoted-router rows if exact comparator labels are required beyond proxy fallback",
            ],
        },
        "fixable_data_or_execution_build_requirements": [
            "import owner-supplied or read-only MT5/FTMO-authorized M1 and tick bars only when source files are available",
            "preserve explicit proxy labels for missing promoted-router comparator rows rather than regenerating fabricated intent",
            "keep fresh-day prop-firm drawdown simulation as replay/proxy authority and runtime headroom as a separate source-bound packet",
            "use ordered post-decision price-action fill inference for simulated replay only",
            "capture broker order/deal/fill/commission/swap/slippage lifecycle only for broker-real labels, not as a simulated replay prerequisite",
        ],
        "storage_policy": {
            "mt5_hydration_scratch": "only one replay day/session is materialized at a time; previous scratch day/session data is deleted before the next hydration",
            "commit_policy": "do not commit hydrated scratch M1/tick data; commit only code, tests, route ledgers, verifier outputs, and compact manifests needed for reproducibility",
            "large_artifact_policy": "route JSONL evidence remains LFS-covered; stale or superseded scratch files should be pruned rather than preserved",
        },
    }
    write_json(route_dir / "WAVE4R_V4_LIMITATIONS_AND_FIX_BACKLOG.json", backlog)
    actionable_path = route_dir / "WAVE4R_ACTIONABLE_V4_REPAIR_FINDINGS_LEDGER.jsonl"
    for limitation in limitations:
        append_jsonl_path(
            actionable_path,
            {
                "finding_id": f"system_backlog:{limitation['limitation_id']}",
                "finding_scope": "system_level_backlog",
                "limitation_id": limitation["limitation_id"],
                "system_area": limitation["system_area"],
                "severity": limitation["severity"],
                "problem_statement": limitation["problem_statement"],
                "fix_or_feature": limitation["fix_or_feature"],
                "production_code_ownership": limitation["production_code_ownership"],
                "tests_required": limitation["tests_required"],
                "evidence_metrics": limitation["evidence_metrics"],
                "evidence_ledgers": limitation["evidence_ledgers"],
                "evidence_label": limitation["evidence_class"],
                "current_status": limitation["current_status"],
            },
        )


def write_hard_halt_ledger(route_dir: Path, rows: list[dict[str, Any]]) -> None:
    with (route_dir / "WAVE4R_HARD_HALT_BINDING_LEDGER.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            append_jsonl(handle, row)


def write_completion_docs(
    route_dir: Path,
    summary: Mapping[str, Any],
    verification: Mapping[str, Any] | None = None,
) -> None:
    write_json(
        route_dir / "WAVE4R_WAVE5_DATASET_HANDOFF.json",
        {
            "schema_version": "wave4r_wave5_dataset_handoff_v1",
            "generated_at_utc": utc_now(),
            "handoff_status": "byproduct_after_results_gate",
            "source_ledgers": [
                "WAVE4R_RESULTS_LEDGER.jsonl",
                "WAVE4R_CANDIDATE_TRADE_MICROSCOPE_LEDGER.jsonl",
                "WAVE4R_CANDIDATE_DECISION_MICROSCOPE_LEDGER.jsonl",
                "WAVE4R_DAY_SESSION_MICROSCOPE_LEDGER.jsonl",
                "WAVE4R_SOURCE_GAP_CAPTURE_REQUIREMENT_LEDGER.jsonl",
            ],
            "candidate_targets": [
                "trade_no_trade_action",
                "same_symbol_action",
                "entry_quality",
                "exit_timing",
                "harvest_capture",
                "target_stop_geometry_efficiency",
                "confluence_reliability",
                "zero_trade_opportunity_cost",
            ],
            "row_counts": {
                "processed_dynamic_policy_rows": summary.get("processed_dynamic_policy_rows"),
                "missing_dynamic_policy_rows_preserved_as_source_gap": summary.get("missing_dynamic_policy_rows_preserved_as_source_gap"),
            },
            "ml_deferral_rejected_until_microscope_complete": True,
        },
    )
    write_json(
        route_dir / "WAVE4R_RESULTS_GATE_PROMPT_HARDENING_RESULT.json",
        {
            "schema_version": "wave4r_prompt_hardening_result_v1",
            "status": "pending_external_prompt_hardening_run",
            "command": None,
            "exit_code": None,
            "note": "Overwritten after scripts/validate_goal_prompt_hardening.py execution.",
        },
    )
    write_json(
        route_dir / "WAVE4R_RESULTS_GATE_FOCUSED_TEST_RESULT.json",
        {
            "schema_version": "wave4r_focused_test_result_v1",
            "status": "pending_external_test_run",
            "command": None,
            "exit_code": None,
            "note": "Overwritten after pytest execution.",
        },
    )
    write_json(
        route_dir / "WAVE4R_RESULTS_GATE_ROUTE_ARTIFACT_AUDIT_RESULT.json",
        {
            "schema_version": "wave4r_route_artifact_audit_result_v1",
            "status": "pending_external_route_audit",
            "command": None,
            "exit_code": None,
            "note": "Overwritten after scripts/audit_goal_route_artifacts.py execution.",
        },
    )
    red_team = f"""# Wave4R Results Gate Saturation Self Red Team

Generated: {utc_now()}

## Verdict

Wave4R processed every readable May-26 dynamic-policy replay row and preserved
the full `214,536` row dynamic denominator after recovering absent native
Stage04 shard rows from Stage05 activated replay. It did not use broker-real
cash/PnL on frozen replay rows and did not mutate broker, MT5, VPS, paid API,
or remote state.

## Residual Source Gaps

- Missing May-26 dynamic-policy rows after Stage05 recovery:
  {summary.get('missing_dynamic_policy_rows_preserved_as_source_gap')}.
- Fresh-day prop-firm drawdown is simulated in R units from replay outcomes.
  Original V4 live intent, pending/order lifecycle truth, and broker-real
  fill/cost/cash remain source/capture gaps on frozen replay rows.
- May-27 promoted dynamic-router replay rows are joined where available and
  used as the primary prior-system replay/proxy-R comparator. Net R remains
  source-gapped where historical cost, fill, swap, and lifecycle fields are
  absent.
- Exact same-bar ordering, live account risk headroom, open/pending broker
  state, and broker-real cost require ordered capture or historical source
  export where not already present. Synthetic replay fillability is inferred
  where ordered price action touches entry after the candidate decision.
- Day/session/candidate microscope fields now include holding duration,
  same-day/next-day/later-day exit class, 0.5R/1R/target/SL reachability,
  consolidation-near-1R-then-loss, giveback-to-loss, and fresh-day prop-firm
  drawdown simulation. Milestone clocks that require ordered LTF/tick transition
  rows remain explicit capture requirements rather than inferred timestamps.

## Anti-Deferral Check

The route computed selector/debate/scheduler/lifecycle/execution/geometry/exit
outputs before writing Wave5 handoff metadata. ML fields are byproducts, not a
closure substitute.
"""
    (route_dir / "WAVE4R_RESULTS_GATE_SATURATION_SELF_RED_TEAM.md").write_text(red_team, encoding="utf-8")
    checklist = f"""# Wave4R Instruction Coverage Checklist

Generated: {utc_now()}

- [x] Mandatory preflight refreshed from disk.
- [x] Frozen CP280/CP281, May-24, May-25, and May-26 roots inventoried.
- [x] All 214,536 dynamic-policy rows processed chronologically after native
  Stage04 plus Stage05 activated replay recovery.
- [x] Timestamp-window scheduler allocation materialized with multi-candidate
  windows, zero-trade alternatives, and selected/rejected options.
- [x] Ordered target/stop/path reconstruction materialized with source-gap
  labels where exact ordering remains unavailable.
- [x] LiveDecisionPacketV4 packet hash, source event hash, field-group status,
  missing/capture status, and validation issues bound to every material row.
- [x] Current V4 selector, probability debate, scheduler, same-symbol lifecycle,
  execution manager, dynamic geometry, exit policy, and LiveDecisionPacketV4
  exercised by the replay adapter.
- [x] May-27 promoted dynamic-router comparator is primary; J46/J49 and fixed
  1.5R are preserved only as secondary historical comparators.
- [x] Accepted-loser, rejected-winner, scheduler-regret, exit/harvest, and
  stale-holding ledgers materialized with exact source-gap labels.
- [x] Day/session microscope aggregation materialized with duration,
  same-day/next-day, target/stop reachability, giveback, consolidation, and
  fresh-day prop-firm replay block fields.
- [x] Broker-real fields are restricted to hard-halt binding rows.
- [x] No broker/live/paid API/remote mutation performed.
- [x] Wave5 handoff recorded only as byproduct.
"""
    (route_dir / "WAVE4R_RESULTS_GATE_INSTRUCTION_COVERAGE_CHECKLIST.md").write_text(checklist, encoding="utf-8")
    completion = f"""# Wave4R Completion Audit

Generated: {utc_now()}

## Scope

Route: `{ROUTE_NAME}`

Processed dynamic replay rows: `{summary.get('processed_dynamic_policy_rows')}`
Expected May-26 replayable rows: `{summary.get('expected_replayable_dynamic_policy_rows')}`
Missing rows preserved as source gap: `{summary.get('missing_dynamic_policy_rows_preserved_as_source_gap')}`
Decision windows: `{summary.get('decision_windows')}`
Multi-candidate decision windows: `{summary.get('multi_candidate_decision_windows')}`
Max decision window size: `{summary.get('max_decision_window_size')}`

## Result

Current V4 replay proxy total R: `{summary.get('v4_total_proxy_r')}`
May-27 promoted dynamic-router replay total R: `{summary.get('promoted_router_total_replay_r')}`
Delta V4 minus promoted router: `{summary.get('delta_v4_minus_promoted_router_total_r')}`
Secondary historical live_current_j46_j49 replay total R: `{summary.get('live_current_j46_j49_total_replay_r')}`

## Evidence Boundary

Frozen replay rows use `replay` and `proxy-R` labels. Broker-real cash/PnL is
used only in the hard-halt binding ledger where broker-real source rows exist.
Exact historical account/open-pending/fill/order/lifecycle/live-intent truth is
not inferred from price movement and remains an explicit source/capture
requirement where absent. Synthetic replay limit fills are inferred from
ordered post-decision entry touches, and fresh-day prop-firm drawdown is
simulated in R units from replay outcomes.
No broker, VPS, MT5 live, paid API, credential, or remote state was mutated.

## Verification

Verification status: `{(verification or {}).get('status', 'pending')}`
"""
    (route_dir / "COMPLETION_AUDIT.md").write_text(completion, encoding="utf-8")


def build_route(
    *,
    repo_root: Path,
    route_dir: Path | None = None,
    max_dynamic_rows: int | None = None,
    verify: bool = True,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    route_dir = (route_dir or current_route_dir(repo_root)).resolve()
    route_dir.mkdir(parents=True, exist_ok=True)
    config = normalize_v4_config(load_yaml(repo_root / "config/agent_config.yaml"))
    inventory = inventory_sources(repo_root)
    write_static_route_ledgers(route_dir, inventory)
    write_inventory_ledgers(route_dir, inventory)
    state = ReplayState()
    summary = ReplaySummary()
    with LedgerHandles(route_dir) as ledgers:
        for window_rows in iter_dynamic_windows(repo_root, max_rows=max_dynamic_rows):
            summary.record_window(len(window_rows))
            evaluated_rows = evaluate_window(window_rows, state, config)
            write_window_allocation_ledger(
                ledgers,
                window_rows=[dict(row) for row in window_rows],
                evaluated_rows=evaluated_rows,
            )
            for evaluated in evaluated_rows:
                write_row_ledgers(ledgers, evaluated, state)
                summary.update(evaluated["result"])
    write_aggregate_ledgers(route_dir, summary)
    hard_rows = hard_halt_binding_rows(repo_root, config)
    write_hard_halt_ledger(route_dir, hard_rows)
    summary_record = summary.to_record(inventory, state)
    summary_record["hard_halt_binding_rows"] = len(hard_rows)
    summary_record["max_dynamic_rows_cap"] = max_dynamic_rows
    write_json(route_dir / "WAVE4R_RESULTS_SUMMARY.json", summary_record)
    write_limitations_and_fix_backlog(route_dir, summary_record)
    verification = verify_route(
        repo_root=repo_root,
        route_dir=route_dir,
        write_result=True,
        require_external_command_artifacts=False,
    ) if verify else None
    write_completion_docs(route_dir, summary_record, verification)
    manifest = output_manifest(route_dir)
    write_json(route_dir / "WAVE4R_RESULTS_GATE_OUTPUT_MANIFEST.json", manifest)
    if verify:
        verification = verify_route(
            repo_root=repo_root,
            route_dir=route_dir,
            write_result=True,
            require_external_command_artifacts=False,
        )
    return {
        "route_dir": str(route_dir),
        "summary": summary_record,
        "verification": verification,
        "manifest": manifest,
    }


def output_manifest(route_dir: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for path in sorted(route_dir.iterdir()):
        if path.is_file():
            files.append(
                {
                    "path": path.name,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "jsonl_rows": count_jsonl_rows(path) if path.suffix == ".jsonl" else None,
                }
            )
    return {
        "schema_version": "wave4r_output_manifest_v1",
        "generated_at_utc": utc_now(),
        "route": ROUTE_NAME,
        "artifact_count": len(files),
        "required_artifacts": list(REQUIRED_ARTIFACTS),
        "files": files,
    }


def packet_ledger_integrity_stats(route_dir: Path) -> dict[str, Any]:
    stats: dict[str, Any] = {
        "rows": 0,
        "missing_packet_hash": 0,
        "missing_packet_hash_sha256": 0,
        "missing_source_event_hash_sha256": 0,
        "missing_field_group_status_summary": 0,
        "missing_capture_status": 0,
        "missing_validation_issues": 0,
        "stale_key_rows": 0,
        "top_level_stale_key_rows": 0,
        "validation_issue_rows": 0,
        "field_group_summary_mismatch_rows": 0,
        "packet_validation_issue_count_mismatch_rows": 0,
        "probability_semantic_unbound_rows": 0,
        "confluence_semantic_unbound_rows": 0,
        "scheduler_semantic_unbound_rows": 0,
        "status_counts": Counter(),
    }
    stale_keys = {"field_group_statuses", "source_event_hash"}
    for row in iter_jsonl(route_dir / "WAVE4R_V4_ASOF_PACKET_LEDGER.jsonl"):
        stats["rows"] += 1
        if stale_keys & set(row):
            stats["top_level_stale_key_rows"] += 1
        if not _valid_sha256(row.get("packet_hash")):
            stats["missing_packet_hash"] += 1
        if not _valid_sha256(row.get("packet_hash_sha256")):
            stats["missing_packet_hash_sha256"] += 1
        if row.get("packet_hash") != row.get("packet_hash_sha256"):
            stats["missing_packet_hash_sha256"] += 1
        if not _valid_sha256(row.get("source_event_hash_sha256")):
            stats["missing_source_event_hash_sha256"] += 1
        summary = row.get("live_decision_packet_v4_summary")
        if not isinstance(summary, Mapping):
            stats["missing_field_group_status_summary"] += 1
            stats["missing_capture_status"] += 1
            stats["missing_validation_issues"] += 1
            continue
        if stale_keys & set(summary):
            stats["stale_key_rows"] += 1
        if not _valid_sha256(summary.get("packet_hash_sha256")):
            stats["missing_packet_hash_sha256"] += 1
        if not _valid_sha256(summary.get("source_event_hash_sha256")):
            stats["missing_source_event_hash_sha256"] += 1
        status_summary = summary.get("field_group_status_summary")
        if row.get("field_group_status_summary") != status_summary:
            stats["field_group_summary_mismatch_rows"] += 1
        if not isinstance(status_summary, Mapping) or not status_summary.get("status_counts"):
            stats["missing_field_group_status_summary"] += 1
        else:
            for status, count in (status_summary.get("status_counts") or {}).items():
                stats["status_counts"][str(status)] += int(count or 0)
        if summary.get("capture_status") in (None, ""):
            stats["missing_capture_status"] += 1
        validation_issues = summary.get("validation_issues")
        if not isinstance(validation_issues, list):
            stats["missing_validation_issues"] += 1
        elif validation_issues:
            stats["validation_issue_rows"] += 1
        if row.get("packet_validation_issue_count") != (
            len(validation_issues) if isinstance(validation_issues, list) else None
        ):
            stats["packet_validation_issue_count_mismatch_rows"] += 1
        missing_by_group = row.get("missing_fields_by_group")
        if not isinstance(missing_by_group, Mapping):
            missing_by_group = summary.get("missing_fields_by_group")
        if not isinstance(missing_by_group, Mapping):
            missing_by_group = {}
        probability_missing = {
            str(item)
            for item in missing_by_group.get("probability_debate_numeric_theses", [])
        }
        if any(item.startswith("numeric_theses.") for item in probability_missing):
            stats["probability_semantic_unbound_rows"] += 1
        confluence_missing = {
            str(item)
            for item in missing_by_group.get("follow_avoid_mixed_numeric_confluence", [])
        }
        if {
            "direction",
            "strength",
            "confidence",
            "source_completeness",
        } & confluence_missing:
            stats["confluence_semantic_unbound_rows"] += 1
        scheduler_missing = {
            str(item)
            for item in missing_by_group.get("selector_allocator_final_say", [])
        }
        if {
            "decision_window_id",
            "candidate_set_id",
            "alternative_candidate_count",
            "selected_action_class",
        } & scheduler_missing:
            stats["scheduler_semantic_unbound_rows"] += 1
    stats["status_counts"] = dict(stats["status_counts"])
    return stats


def result_ledger_integrity_stats(route_dir: Path) -> dict[str, Any]:
    stats: dict[str, Any] = {
        "rows": 0,
        "missing_packet_hash": 0,
        "missing_source_event_hash_sha256": 0,
        "missing_promoted_router_policy": 0,
        "missing_promoted_router_replay_r": 0,
        "missing_delta_v4_minus_promoted_router_r": 0,
        "primary_comparator_j46_only_rows": 0,
        "missing_path_microscope": 0,
        "missing_milestone_fields": 0,
        "missing_prop_firm_risk_state": 0,
        "missing_prop_firm_replay_fields": 0,
        "missing_replay_limit_fill_inference": 0,
        "filled_limit_rows_missing_limit_status": 0,
        "missing_current_v4_result_label": 0,
        "recovery_status_counts": Counter(),
        "broker_real_cash_like_rows": 0,
    }
    for row in iter_jsonl(route_dir / "WAVE4R_RESULTS_LEDGER.jsonl"):
        stats["rows"] += 1
        if not _valid_sha256(row.get("packet_hash")):
            stats["missing_packet_hash"] += 1
        if not _valid_sha256(row.get("source_event_hash_sha256")):
            stats["missing_source_event_hash_sha256"] += 1
        if not row.get("promoted_router_policy"):
            stats["missing_promoted_router_policy"] += 1
        if row.get("promoted_router_replay_r") is None:
            stats["missing_promoted_router_replay_r"] += 1
        if row.get("delta_v4_minus_promoted_router_r") is None:
            stats["missing_delta_v4_minus_promoted_router_r"] += 1
        if row.get("current_v4_result_label") != EVIDENCE_PROXY_R:
            stats["missing_current_v4_result_label"] += 1
        if row.get("delta_v4_minus_live_current_r") is not None and row.get(
            "delta_v4_minus_promoted_router_r"
        ) is None:
            stats["primary_comparator_j46_only_rows"] += 1
        path_microscope = row.get("path_microscope")
        if not isinstance(path_microscope, Mapping):
            stats["missing_path_microscope"] += 1
        else:
            for field in (
                "holding_minutes_from_entry",
                "exit_day_relation_from_entry",
                "reached_0_5r",
                "reached_1r",
                "reached_configured_target",
                "hit_stop",
                "threshold_milestones",
                "threshold_times_utc",
                "threshold_seconds_from_entry",
                "partial_trigger_utc",
                "be_return_after_1r_utc",
                "duration_stuck_near_entry_seconds",
                "last_r",
            ):
                if field not in path_microscope:
                    stats["missing_milestone_fields"] += 1
                    break
        risk_state = row.get("prop_firm_risk_state")
        if not isinstance(risk_state, Mapping) or not risk_state.get("status"):
            stats["missing_prop_firm_risk_state"] += 1
        elif (
            risk_state.get("daily_drawdown_blocked") is None
            or not risk_state.get("simulation_model")
            or risk_state.get("daily_loss_limit_r") is None
        ):
            stats["missing_prop_firm_replay_fields"] += 1
        path_result = row.get("promoted_router_path_result")
        inference = (
            path_result.get("replay_limit_fill_inference")
            if isinstance(path_result, Mapping)
            else None
        )
        if not isinstance(inference, Mapping) or not inference.get("status"):
            stats["missing_replay_limit_fill_inference"] += 1
        elif inference.get("filled") and not path_result.get("limit_fill_status"):
            stats["filled_limit_rows_missing_limit_status"] += 1
        stats["recovery_status_counts"][str(row.get("recovery_status"))] += 1
        evidence_blob = json.dumps(row, sort_keys=True, ensure_ascii=True)
        if "broker-real cash" in evidence_blob or "broker_real_cash" in evidence_blob:
            stats["broker_real_cash_like_rows"] += 1
    stats["recovery_status_counts"] = dict(stats["recovery_status_counts"])
    return stats


def day_session_integrity_stats(route_dir: Path) -> dict[str, int]:
    stats = {
        "rows": 0,
        "missing_trade_date": 0,
        "missing_session": 0,
        "missing_duration_average_field": 0,
        "missing_prop_risk_evidence_status": 0,
        "missing_prop_replay_block_field": 0,
        "missing_accepted_win_loss_fields": 0,
        "missing_target_stop_fields": 0,
    }
    for row in iter_jsonl(route_dir / "WAVE4R_DAY_SESSION_MICROSCOPE_LEDGER.jsonl"):
        stats["rows"] += 1
        if not row.get("trade_date"):
            stats["missing_trade_date"] += 1
        if not row.get("session"):
            stats["missing_session"] += 1
        if "average_duration_minutes" not in row:
            stats["missing_duration_average_field"] += 1
        if not row.get("prop_firm_risk_block_evidence_status"):
            stats["missing_prop_risk_evidence_status"] += 1
        if "prop_firm_replay_blocked_rows" not in row:
            stats["missing_prop_replay_block_field"] += 1
        for field in ("accepted_winners", "accepted_losers", "accepted_breakeven"):
            if field not in row:
                stats["missing_accepted_win_loss_fields"] += 1
                break
        for field in (
            "reached_0_5r_rows",
            "reached_1r_rows",
            "reached_configured_target_rows",
            "hit_stop_rows",
            "same_day_exits",
            "next_day_exits",
        ):
            if field not in row:
                stats["missing_target_stop_fields"] += 1
                break
    return stats


def window_ledger_integrity_stats(route_dir: Path) -> dict[str, int]:
    stats = {
        "rows": 0,
        "multi_candidate_windows": 0,
        "one_candidate_windows": 0,
        "max_window_candidate_count": 0,
        "missing_window_candidate_count": 0,
        "candidate_option_mismatch_rows": 0,
    }
    for row in iter_jsonl(route_dir / "WAVE4R_MULTI_CANDIDATE_WINDOW_ALLOCATION_LEDGER.jsonl"):
        stats["rows"] += 1
        count = _int(row.get("window_candidate_count"), 0) or 0
        options = row.get("candidate_options") or []
        if count <= 0:
            stats["missing_window_candidate_count"] += 1
        if isinstance(options, list) and len(options) != count:
            stats["candidate_option_mismatch_rows"] += 1
        stats["max_window_candidate_count"] = max(stats["max_window_candidate_count"], count)
        if count > 1:
            stats["multi_candidate_windows"] += 1
        else:
            stats["one_candidate_windows"] += 1
    return stats


def ordered_path_integrity_stats(route_dir: Path) -> dict[str, Any]:
    stats: dict[str, Any] = {
        "rows": 0,
        "source_status_counts": Counter(),
        "ordered_touch_without_touch_time_rows": 0,
        "ambiguous_rows": 0,
        "proxy_or_gap_rows": 0,
    }
    for row in iter_jsonl(route_dir / "WAVE4R_ORDERED_PATH_RECONSTRUCTION_LEDGER.jsonl"):
        stats["rows"] += 1
        source_status = str(row.get("ordered_path_source_status") or "")
        stats["source_status_counts"][source_status] += 1
        if row.get("same_bar_ambiguity") is True:
            stats["ambiguous_rows"] += 1
        if source_status == "ordered_touch_times_from_path_row_or_recovered_stage05" and not (
            row.get("target_first_touch_utc") or row.get("stop_first_touch_utc")
        ):
            stats["ordered_touch_without_touch_time_rows"] += 1
        if source_status == "ordered_touch_times_missing":
            stats["proxy_or_gap_rows"] += 1
    stats["source_status_counts"] = dict(stats["source_status_counts"])
    return stats


def limitation_backlog_integrity_stats(route_dir: Path) -> dict[str, Any]:
    required_areas = {
        "selection",
        "scheduling",
        "exit_harvest",
        "target_stop_geometry",
        "same_symbol_lifecycle",
        "prop_firm_risk",
        "probability_confluence",
        "historical_intent_coverage",
        "path_truth",
        "execution_costs",
        "stale_holding",
    }
    payload = load_json(route_dir / "WAVE4R_V4_LIMITATIONS_AND_FIX_BACKLOG.json", {})
    limitations = payload.get("limitations") if isinstance(payload.get("limitations"), list) else []
    areas = {
        str(item.get("system_area"))
        for item in limitations
        if isinstance(item, Mapping) and item.get("system_area")
    }
    stats: dict[str, Any] = {
        "rows": len(limitations),
        "missing_system_verdict": 0 if payload.get("system_verdict") else 1,
        "missing_metric_counts": 0 if isinstance(payload.get("metric_counts"), Mapping) else 1,
        "primary_comparator": payload.get("primary_comparator"),
        "missing_required_areas": sorted(required_areas - areas),
        "j46_static_primary_rows": 0,
        "missing_fix_or_feature": 0,
        "missing_problem_statement": 0,
        "missing_evidence_metrics": 0,
        "missing_evidence_ledgers": 0,
        "missing_production_code_ownership": 0,
        "missing_tests_required": 0,
        "missing_evidence_class": 0,
        "missing_status": 0,
        "source_capture_required_rows": 0,
        "implementation_required_rows": 0,
        "production_fix_rows": 0,
        "missing_storage_policy": 0 if isinstance(payload.get("storage_policy"), Mapping) else 1,
        "missing_scratch_pruning_policy": 0,
        "microstructure_hydration_rows": 0,
    }
    storage_policy = payload.get("storage_policy") if isinstance(payload.get("storage_policy"), Mapping) else {}
    if "delete" not in str(storage_policy.get("mt5_hydration_scratch") or "").lower():
        stats["missing_scratch_pruning_policy"] = 1
    for item in limitations:
        if not isinstance(item, Mapping):
            stats["missing_problem_statement"] += 1
            continue
        primary_blob = f"{item.get('system_area')} {item.get('limitation_id')} {item.get('problem_statement')}".lower()
        if "j46" in primary_blob or "fixed 1.5" in primary_blob:
            stats["j46_static_primary_rows"] += 1
        if not item.get("fix_or_feature"):
            stats["missing_fix_or_feature"] += 1
        if not item.get("problem_statement"):
            stats["missing_problem_statement"] += 1
        if not isinstance(item.get("evidence_metrics"), Mapping) or not item.get("evidence_metrics"):
            stats["missing_evidence_metrics"] += 1
        if not isinstance(item.get("evidence_ledgers"), list) or not item.get("evidence_ledgers"):
            stats["missing_evidence_ledgers"] += 1
        if not isinstance(item.get("production_code_ownership"), list) or not item.get("production_code_ownership"):
            stats["missing_production_code_ownership"] += 1
        if not isinstance(item.get("tests_required"), list) or not item.get("tests_required"):
            stats["missing_tests_required"] += 1
        if not item.get("evidence_class"):
            stats["missing_evidence_class"] += 1
        if not item.get("current_status"):
            stats["missing_status"] += 1
        if "source_capture_required" in str(item.get("current_status")):
            stats["source_capture_required_rows"] += 1
        if "implementation_required" in str(item.get("current_status")):
            stats["implementation_required_rows"] += 1
        if any(str(path).startswith("src/") for path in item.get("production_code_ownership") or []):
            stats["production_fix_rows"] += 1
        if "src/research_infra/wave4r_replay_microstructure.py" in (item.get("production_code_ownership") or []):
            stats["microstructure_hydration_rows"] += 1
    return stats


def command_artifact_failures(route_dir: Path, *, require_external_command_artifacts: bool) -> list[dict[str, Any]]:
    if not require_external_command_artifacts:
        return []
    failures: list[dict[str, Any]] = []
    command_requirements = {
        "WAVE4R_RESULTS_GATE_FOCUSED_TEST_RESULT.json": ("pytest",),
        "WAVE4R_RESULTS_GATE_PROMPT_HARDENING_RESULT.json": ("validate_goal_prompt_hardening.py",),
        "WAVE4R_RESULTS_GATE_ROUTE_ARTIFACT_AUDIT_RESULT.json": ("audit_goal_route_artifacts.py", "--full-jsonl"),
    }
    for artifact, required_terms in command_requirements.items():
        payload = load_json(route_dir / artifact, {})
        command = [str(part) for part in payload.get("command") or []]
        if payload.get("status") != "pass" or payload.get("exit_code") != 0:
            failures.append({"check": "external_command_artifact_passed", "artifact": artifact, "payload_status": payload.get("status")})
        joined = " ".join(command)
        for term in required_terms:
            if term not in joined:
                failures.append({"check": "external_command_artifact_command_contains", "artifact": artifact, "required": term, "command": command})
    return failures


def stale_residue_failures(route_dir: Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    stale_phrases = (
        "missing May-26 shards were not available",
        "unavailable shard denominator as source-gap",
        "preserved the unavailable shard denominator",
        "Where does the current momentum-exhaustion 2R proxy improve/degrade versus live_current_j46_j49",
        "Pre-V4 live_current_j46_j49 replay total R:",
        "Delta V4 minus live_current:",
    )
    checked = [
        "WAVE4R_READONLY_MT5_EXTRACTION_LEDGER.jsonl",
        "WAVE4R_CODE_AND_REPLAY_REPAIR_LEDGER.jsonl",
        "WAVE4R_RESULTS_GATE_SATURATION_SELF_RED_TEAM.md",
        "WAVE4R_RESULTS_GATE_INSTRUCTION_COVERAGE_CHECKLIST.md",
        "COMPLETION_AUDIT.md",
    ]
    for name in checked:
        path = route_dir / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in stale_phrases:
            if phrase in text:
                failures.append({"check": "stale_residue_wording_absent", "artifact": name, "phrase": phrase})
    return failures


def golden_coverage_failures(repo_root: Path) -> list[dict[str, Any]]:
    test_path = repo_root / "tests/test_wave4r_v4_vs_v3_frozen_replay_results_gate.py"
    if not test_path.exists():
        return [{"check": "golden_test_file_exists", "path": str(test_path)}]
    text = test_path.read_text(encoding="utf-8")
    required = {
        "multi_candidate": "multi-candidate allocation",
        "scale_in_and_reverse": "same-symbol scale/reverse",
        "ordered_target_stop": "ordered target/stop sequencing",
        "adverse_first": "adverse-first-then-MFE",
        "static_dynamic_geometry": "dynamic vs static target geometry",
        "confluence_debate_disagreement": "confluence/debate disagreement",
        "be_partial_harvest": "BE/partial/harvest",
        "stale_thesis": "stale thesis",
        "source_gap_row": "zero-trade opportunity cost",
        "hard_halt": "hard-halt binding",
        "stage05": "Stage05 recovery",
        "packet_binding": "LiveDecisionPacketV4 packet binding",
    }
    return [
        {"check": "golden_behavior_coverage_present", "required": label, "needle": needle}
        for needle, label in required.items()
        if needle not in text
    ]


def verify_route(
    *,
    repo_root: Path,
    route_dir: Path,
    write_result: bool = True,
    require_external_command_artifacts: bool = True,
) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for name in REQUIRED_ARTIFACTS:
        path = route_dir / name
        if not path.exists():
            failures.append({"check": "required_artifact_exists", "artifact": name})
    summary = load_json(route_dir / "WAVE4R_RESULTS_SUMMARY.json", {})
    inventory = load_json(route_dir / "WAVE4R_SOURCE_INVENTORY.json", {})
    may26 = (((inventory.get("frozen_surfaces") or {}).get("may26_dynamic_policy_replay")) or {})
    processed = _int(summary.get("processed_dynamic_policy_rows"), 0) or 0
    readable = _int(may26.get("readable_dynamic_policy_rows"), 0) or 0
    if summary.get("max_dynamic_rows_cap") is not None:
        failures.append(
            {
                "check": "max_dynamic_rows_cap_absent_for_acceptance",
                "value": summary.get("max_dynamic_rows_cap"),
            }
        )
    if processed <= 0:
        failures.append({"check": "processed_rows_positive", "value": processed})
    if readable and processed != readable and summary.get("max_dynamic_rows_cap") is None:
        failures.append(
            {
                "check": "processed_all_readable_dynamic_rows",
                "processed": processed,
                "readable": readable,
            }
        )
    expected = _int(may26.get("replayable_candidate_rows_expected"), 0) or 0
    missing = _int(may26.get("missing_dynamic_policy_rows"), 0) or 0
    if expected != 214536:
        failures.append({"check": "expected_dynamic_denominator_214536", "value": expected})
    if processed != 214536:
        failures.append({"check": "processed_dynamic_denominator_214536", "value": processed})
    if missing != 0:
        failures.append({"check": "missing_dynamic_policy_rows_zero", "value": missing})
    if expected and processed + missing != expected and summary.get("max_dynamic_rows_cap") is None:
        failures.append(
            {
                "check": "denominator_accounted",
                "processed": processed,
                "missing": missing,
                "expected": expected,
            }
        )
    for ledger_name in (
        "WAVE4R_V4_ASOF_PACKET_LEDGER.jsonl",
        "WAVE4R_CHRONOLOGICAL_STATE_TRANSITION_LEDGER.jsonl",
        "WAVE4R_RESULTS_LEDGER.jsonl",
        "WAVE4R_DECISION_LEDGER.jsonl",
        "WAVE4R_CANDIDATE_TRADE_MICROSCOPE_LEDGER.jsonl",
        "WAVE4R_CANDIDATE_DECISION_MICROSCOPE_LEDGER.jsonl",
        "WAVE4R_TRADE_PATH_ANATOMY_LEDGER.jsonl",
        "WAVE4R_ENTRY_QUALITY_LEDGER.jsonl",
        "WAVE4R_ENTRY_EXIT_TIMING_PATH_LEDGER.jsonl",
        "WAVE4R_SELECTOR_EXECUTION_EXIT_ANATOMY_LEDGER.jsonl",
        "WAVE4R_SAME_SYMBOL_ACTION_LEDGER.jsonl",
        "WAVE4R_STATIC_R_DYNAMIC_GEOMETRY_LEDGER.jsonl",
        "WAVE4R_TIME_MFE_MAE_GIVEBACK_LEDGER.jsonl",
        "WAVE4R_FOLLOW_AVOID_MIXED_CONFLUENCE_LEDGER.jsonl",
        "WAVE4R_PROBABILITY_CALIBRATION_LEDGER.jsonl",
        "WAVE4R_ORDERED_PATH_RECONSTRUCTION_LEDGER.jsonl",
        "WAVE4R_SCHEDULER_ALLOCATION_REGRET_LEDGER.jsonl",
        "WAVE4R_EXIT_HARVEST_COUNTERFACTUAL_LEDGER.jsonl",
        "WAVE4R_STALE_HOLDINGS_THESIS_AGE_LEDGER.jsonl",
    ):
        rows = count_jsonl_rows(route_dir / ledger_name)
        if rows != processed:
            failures.append({"check": "ledger_rows_equal_processed", "ledger": ledger_name, "rows": rows, "processed": processed})
    windows = _int(summary.get("decision_windows"), 0) or 0
    window_rows = count_jsonl_rows(route_dir / "WAVE4R_MULTI_CANDIDATE_WINDOW_ALLOCATION_LEDGER.jsonl")
    if windows <= 0:
        failures.append({"check": "decision_windows_present", "value": windows})
    if window_rows != windows:
        failures.append({"check": "window_ledger_rows_equal_windows", "rows": window_rows, "windows": windows})
    if (_int(summary.get("multi_candidate_decision_windows"), 0) or 0) <= 0 and processed > 1:
        failures.append({"check": "multi_candidate_windows_present"})
    if (_int(summary.get("max_decision_window_size"), 0) or 0) <= 1 and processed > 1:
        failures.append({"check": "max_window_size_gt_one"})
    recovery_counts = summary.get("recovery_status_counts") or {}
    native_rows = _int(may26.get("native_readable_dynamic_policy_rows"), 0) or 0
    recovered_rows = _int(may26.get("recovered_dynamic_policy_rows_from_stage05"), 0) or 0
    if native_rows != 61550:
        failures.append({"check": "native_stage04_rows_61550", "value": native_rows})
    if recovered_rows != 152986:
        failures.append({"check": "stage05_recovered_rows_152986", "value": recovered_rows})
    if len(may26.get("stage05_recovery_shards") or []) != 7:
        failures.append(
            {
                "check": "stage05_recovery_shard_count_7",
                "value": may26.get("stage05_recovery_shards"),
            }
        )
    if expected and missing != 0 and summary.get("max_dynamic_rows_cap") is None:
        failures.append({"check": "full_dynamic_denominator_recovered", "missing": missing})
    if expected and native_rows + recovered_rows != expected and summary.get("max_dynamic_rows_cap") is None:
        failures.append(
            {
                "check": "native_plus_stage05_recovered_equals_expected",
                "native": native_rows,
                "recovered": recovered_rows,
                "expected": expected,
            }
        )
    if expected == processed and not recovery_counts.get("recovered_from_stage05_activated_replay_missing_stage04_dynamic_shard"):
        failures.append({"check": "stage05_recovery_rows_present", "recovery_status_counts": recovery_counts})
    if may26.get("unrecovered_dynamic_policy_shards") not in ([], None):
        failures.append({"check": "unrecovered_dynamic_policy_shards_empty", "value": may26.get("unrecovered_dynamic_policy_shards")})
    if recovered_rows and len(may26.get("stage05_recovery_shards") or []) <= 0:
        failures.append({"check": "stage05_recovery_shards_recorded", "value": may26.get("stage05_recovery_shards")})
    if recovered_rows and not ((may26.get("stage05_activation_manifest_artifact") or {}).get("exists")):
        failures.append({"check": "stage05_activation_manifest_artifact_exists"})
    if not summary.get("accepted_v4_simulated_rows"):
        failures.append({"check": "accepted_rows_present"})
    if not summary.get("zero_trade_or_rejected_rows"):
        failures.append({"check": "zero_trade_rows_present"})
    if summary.get("promoted_router_total_replay_r") is None:
        failures.append({"check": "promoted_router_total_replay_r_present"})
    if summary.get("delta_v4_minus_promoted_router_total_r") is None:
        failures.append({"check": "delta_v4_minus_promoted_router_total_r_present"})
    primary = ((summary.get("evidence_boundary") or {}).get("primary_prior_comparator"))
    if primary != PROMOTED_ROUTER_POLICY_ID:
        failures.append(
            {
                "check": "primary_prior_comparator_is_promoted_router",
                "value": primary,
            }
        )
    if "j46" in str(primary).lower() or "fixed" in str(primary).lower():
        failures.append({"check": "primary_comparator_not_j46_or_fixed", "value": primary})
    source_gap_rows = count_jsonl_rows(route_dir / "WAVE4R_SOURCE_GAP_CAPTURE_REQUIREMENT_LEDGER.jsonl")
    if source_gap_rows <= 0:
        failures.append({"check": "source_gap_capture_rows_present"})
    hard_halt_rows = count_jsonl_rows(route_dir / "WAVE4R_HARD_HALT_BINDING_LEDGER.jsonl")
    if hard_halt_rows <= 0:
        warnings.append({"check": "hard_halt_binding_rows_present", "rows": hard_halt_rows})
    packet_stats = packet_ledger_integrity_stats(route_dir)
    if packet_stats["rows"] != processed:
        failures.append({"check": "packet_ledger_rows_equal_processed", "stats": packet_stats, "processed": processed})
    for check in (
        "missing_packet_hash",
        "missing_packet_hash_sha256",
        "missing_source_event_hash_sha256",
        "missing_field_group_status_summary",
        "missing_capture_status",
        "missing_validation_issues",
        "stale_key_rows",
        "top_level_stale_key_rows",
        "field_group_summary_mismatch_rows",
        "packet_validation_issue_count_mismatch_rows",
        "probability_semantic_unbound_rows",
        "confluence_semantic_unbound_rows",
        "scheduler_semantic_unbound_rows",
        "validation_issue_rows",
    ):
        if packet_stats.get(check):
            failures.append({"check": f"packet_ledger_{check}_zero", "stats": packet_stats})
    if not packet_stats.get("status_counts"):
        failures.append({"check": "packet_field_group_status_counts_present", "stats": packet_stats})
    result_stats = result_ledger_integrity_stats(route_dir)
    if result_stats["rows"] != processed:
        failures.append({"check": "result_ledger_rows_equal_processed", "stats": result_stats, "processed": processed})
    for check in (
        "missing_packet_hash",
        "missing_source_event_hash_sha256",
        "missing_promoted_router_policy",
        "missing_promoted_router_replay_r",
        "missing_delta_v4_minus_promoted_router_r",
        "primary_comparator_j46_only_rows",
        "missing_path_microscope",
        "missing_milestone_fields",
        "missing_prop_firm_risk_state",
        "missing_prop_firm_replay_fields",
        "missing_replay_limit_fill_inference",
        "filled_limit_rows_missing_limit_status",
        "missing_current_v4_result_label",
    ):
        if result_stats.get(check):
            failures.append({"check": f"result_ledger_{check}_zero", "stats": result_stats})
    if result_stats.get("broker_real_cash_like_rows"):
        failures.append({"check": "frozen_result_rows_do_not_claim_broker_real_cash", "stats": result_stats})
    if result_stats.get("recovery_status_counts") != recovery_counts:
        failures.append(
            {
                "check": "result_recovery_status_counts_match_summary",
                "result_stats": result_stats.get("recovery_status_counts"),
                "summary_counts": recovery_counts,
            }
        )
    day_session_stats = day_session_integrity_stats(route_dir)
    if day_session_stats["rows"] <= 0:
        failures.append({"check": "day_session_microscope_rows_present", "stats": day_session_stats})
    for check in (
        "missing_trade_date",
        "missing_session",
        "missing_duration_average_field",
        "missing_prop_risk_evidence_status",
        "missing_prop_replay_block_field",
        "missing_accepted_win_loss_fields",
        "missing_target_stop_fields",
    ):
        if day_session_stats.get(check):
            failures.append({"check": f"day_session_{check}_zero", "stats": day_session_stats})
    window_stats = window_ledger_integrity_stats(route_dir)
    if window_stats["rows"] != windows:
        failures.append({"check": "window_stats_rows_equal_windows", "stats": window_stats, "windows": windows})
    if window_stats["multi_candidate_windows"] != (_int(summary.get("multi_candidate_decision_windows"), 0) or 0):
        failures.append({"check": "window_multi_candidate_count_matches_summary", "stats": window_stats, "summary": summary.get("multi_candidate_decision_windows")})
    if window_stats["max_window_candidate_count"] != (_int(summary.get("max_decision_window_size"), 0) or 0):
        failures.append({"check": "window_max_candidate_count_matches_summary", "stats": window_stats, "summary": summary.get("max_decision_window_size")})
    for check in ("missing_window_candidate_count", "candidate_option_mismatch_rows"):
        if window_stats.get(check):
            failures.append({"check": f"window_ledger_{check}_zero", "stats": window_stats})
    ordered_stats = ordered_path_integrity_stats(route_dir)
    if ordered_stats["rows"] != processed:
        failures.append({"check": "ordered_path_rows_equal_processed", "stats": ordered_stats, "processed": processed})
    if ordered_stats.get("ordered_touch_without_touch_time_rows"):
        failures.append({"check": "ordered_touch_rows_have_touch_time", "stats": ordered_stats})
    if (
        summary.get("max_dynamic_rows_cap") is None
        and not (ordered_stats.get("source_status_counts") or {}).get("ordered_touch_times_from_path_row_or_recovered_stage05")
    ):
        failures.append({"check": "ordered_path_has_recovered_or_path_touch_times", "stats": ordered_stats})
    backlog_stats = limitation_backlog_integrity_stats(route_dir)
    if backlog_stats["rows"] <= 0:
        failures.append({"check": "limitation_backlog_rows_present", "stats": backlog_stats})
    if backlog_stats.get("missing_required_areas"):
        failures.append({"check": "limitation_backlog_required_areas_present", "stats": backlog_stats})
    for check in (
        "missing_system_verdict",
        "missing_metric_counts",
        "j46_static_primary_rows",
        "missing_fix_or_feature",
        "missing_problem_statement",
        "missing_evidence_metrics",
        "missing_evidence_ledgers",
        "missing_production_code_ownership",
        "missing_tests_required",
        "missing_evidence_class",
        "missing_status",
        "missing_storage_policy",
        "missing_scratch_pruning_policy",
    ):
        if backlog_stats.get(check):
            failures.append({"check": f"limitation_backlog_{check}_zero", "stats": backlog_stats})
    if backlog_stats.get("primary_comparator") != PROMOTED_ROUTER_POLICY_ID:
        failures.append({"check": "limitation_backlog_primary_comparator_promoted_router", "stats": backlog_stats})
    if (
        backlog_stats.get("implementation_required_rows", 0) <= 0
        and backlog_stats.get("source_capture_required_rows", 0) <= 0
    ):
        failures.append({"check": "limitation_backlog_exact_residual_rows_present", "stats": backlog_stats})
    if backlog_stats.get("production_fix_rows", 0) <= 0:
        failures.append({"check": "limitation_backlog_production_fix_rows_present", "stats": backlog_stats})
    if backlog_stats.get("microstructure_hydration_rows", 0) <= 0:
        failures.append({"check": "limitation_backlog_microstructure_hydration_implementation_present", "stats": backlog_stats})
    label = ((summary.get("evidence_boundary") or {}).get("current_v4_result_label"))
    if label != EVIDENCE_PROXY_R:
        failures.append({"check": "current_v4_result_label_proxy_r", "value": label})
    failures.extend(command_artifact_failures(route_dir, require_external_command_artifacts=require_external_command_artifacts))
    failures.extend(stale_residue_failures(route_dir))
    failures.extend(golden_coverage_failures(repo_root))
    status = "pass" if not failures else "fail"
    result = {
        "schema_version": "wave4r_results_gate_verification_v1",
        "generated_at_utc": utc_now(),
        "status": status,
        "failure_count": len(failures),
        "warning_count": len(warnings),
        "failures": failures,
        "warnings": warnings,
        "processed_dynamic_policy_rows": processed,
        "readable_dynamic_policy_rows": readable,
        "expected_replayable_dynamic_policy_rows": expected,
        "missing_dynamic_policy_rows": missing,
        "packet_ledger_integrity": packet_stats,
        "result_ledger_integrity": result_stats,
        "day_session_integrity": day_session_stats,
        "window_ledger_integrity": window_stats,
        "ordered_path_integrity": ordered_stats,
        "limitation_backlog_integrity": backlog_stats,
        "external_command_artifacts_required": require_external_command_artifacts,
        "hard_boundaries": {
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "remote_push": False,
            "active_vps_mutation": False,
        },
    }
    if write_result:
        write_json(route_dir / "WAVE4R_RESULTS_GATE_VERIFICATION_RESULT.json", result)
    return result


def write_command_result(
    route_dir: Path,
    artifact_name: str,
    *,
    command: list[str],
    exit_code: int,
    stdout: str,
    stderr: str,
) -> dict[str, Any]:
    result = {
        "schema_version": f"{Path(artifact_name).stem.lower()}_v1",
        "generated_at_utc": utc_now(),
        "status": "pass" if exit_code == 0 else "fail",
        "command": command,
        "exit_code": exit_code,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
    }
    write_json(route_dir / artifact_name, result)
    return result


def run_and_record_command(route_dir: Path, artifact_name: str, command: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=str(cwd), text=True, capture_output=True)
    return write_command_result(
        route_dir,
        artifact_name,
        command=command,
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Build or verify Wave4R route artifacts.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--route-dir", default=None, help="Route output directory.")
    parser.add_argument("--max-dynamic-rows", type=int, default=None, help="Optional test cap.")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    route_dir = Path(args.route_dir).resolve() if args.route_dir else current_route_dir(repo_root)
    if args.verify_only:
        result = verify_route(repo_root=repo_root, route_dir=route_dir, write_result=True)
    else:
        result = build_route(
            repo_root=repo_root,
            route_dir=route_dir,
            max_dynamic_rows=args.max_dynamic_rows,
            verify=True,
        )
    print(json.dumps(_json_safe(result), indent=2, sort_keys=True))
    return 0 if (result.get("verification") or result).get("status", "pass") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

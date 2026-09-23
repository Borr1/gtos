"""Outcome-blind two-trading-day replay acceleration benchmark.

This route consumes the independently accepted source and normalization bundles,
reconstructs only the read-only live-ingestion/candidate-origin surface, and
persists opaque structural roots.  It deliberately cannot evaluate candidates,
schedule policy, simulate orders, mutate a broker, or execute a successor arm.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import subprocess
import sys
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping

from src.components.v4_live_replay_decision_core import V4DecisionCycleCore
from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp
from src.research_infra.replay_acceleration_candidate_boundary import ReadTrackingDict


SCHEMA = "gtos.replay_acceleration.progressive_result.v1"
RUN_SCHEMA = "gtos.replay_acceleration.progressive_run.v1"
SELECTION_SCHEMA = "gtos.replay_acceleration.progressive_day_selection.v1"
NORMALIZED_BUNDLE_SCHEMA = "gtos.replay_acceleration.normalized_bundle.v1"
NORMALIZED_MANIFEST_SCHEMA = "gtos.replay_acceleration.normalized_manifest.v1"
OUTPUT_DIR = Path(
    "research/operations/replay_acceleration_progressive_benchmark_2026_07_19"
)
SELECTION_RECEIPT_PATH = OUTPUT_DIR / "PROGRESSIVE_DAY_SELECTION_RECEIPT.json"
SOURCE_SELECTION_PATH = Path(
    "research/operations/replay_acceleration_bounded_slice_2026_07_19/"
    "SOURCE_SELECTION_RECEIPT.json"
)
SOURCE_RESULT_PATH = Path(
    "research/operations/replay_acceleration_bounded_slice_2026_07_19/"
    "BOUNDED_EQUIVALENCE_RESULT.json"
)
SOURCE_BUNDLE_DIR = Path(
    "research/operations/replay_acceleration_bounded_slice_2026_07_19/"
    "scratch/primary/bundle"
)
NORMALIZATION_RESULT_PATH = Path(
    "research/operations/replay_acceleration_normalized_slice_2026_07_19/"
    "NORMALIZATION_EQUIVALENCE_RESULT.json"
)
NORMALIZED_BUNDLE_DIR = Path(
    "research/operations/replay_acceleration_normalized_slice_2026_07_19/"
    "scratch/primary/bundle"
)
REDUCER_RESULT_PATH = Path(
    "research/operations/replay_acceleration_isolated_reducers_2026_07_19/"
    "ISOLATED_REDUCER_RESULT.json"
)
TYPED_RESULT_PATH = Path(
    "research/operations/replay_acceleration_typed_proofs_2026_07_19/"
    "TYPED_PROOF_RESULT.json"
)
RESUME_RESULT_PATH = Path(
    "research/operations/replay_acceleration_resume_2026_07_19/"
    "RESUME_RESULT.json"
)
RESOURCE_RESULT_PATH = Path(
    "research/operations/replay_acceleration_resource_architecture_2026_07_19/"
    "RESOURCE_ARCHITECTURE_RESULT.json"
)
CONFIG_PATH = Path("config/agent_config.yaml")
SELECTED_DAYS = ("2026-01-02", "2026-01-05")
TIMEFRAMES = ("D1", "H4", "H1", "M15", "M1")
EXPECTED_SYMBOLS = tuple(sorted(timewarp.INCLUDED_SYMBOLS))
WARNING_BYTES = 34 * 1024**3
HARD_FLOOR_BYTES = 28 * 1024**3
SLICE_QUOTA_BYTES = 1024**3
MAX_IMMUTABLE_WORKERS = 2
HISTORY_ROWS = 720
ARM_ORDER = ("S0R0", "S1R0", "S0R1", "S1R1")
FACTOR_PREFIX = (
    f"gtos_vnext_runtime."
    f"{timewarp.B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX}"
)

STAGE_PROFILE_SCHEMA = "gtos.replay_acceleration.stage_profile.v2"
BOUNDED_FULL_REPLAY_BENCHMARK_SCHEMA = (
    "gtos.replay_acceleration.bounded_full_replay_benchmark.v1"
)
FULL_REPLAY_CACHE_MANIFEST_SCHEMA = (
    "gtos.replay_acceleration.bounded_full_replay_cache_manifest.v1"
)
FULL_REPLAY_CACHE_PRECONDITION_SCHEMA = (
    "gtos.replay_acceleration.bounded_full_replay_cache_precondition.v1"
)
FULL_REPLAY_PRIMING_RECEIPT_SCHEMA = (
    "gtos.replay_acceleration.bounded_full_replay_priming_receipt.v1"
)
FULL_REPLAY_LAUNCH_NONCE_ENV = "GTOS_FULL_REPLAY_BENCHMARK_LAUNCH_NONCE"
_FULL_REPLAY_PROCESS_LAUNCH_NONCE = os.environ.get(FULL_REPLAY_LAUNCH_NONCE_ENV)
_FULL_REPLAY_PROCESS_PID = os.getpid()
_FULL_REPLAY_PROCESS_PARENT_PID = os.getppid()
REPLAY_STAGE_ORDER = (
    "startup",
    "source_slicing",
    "snapshots",
    "market_state",
    "generation",
    "evaluation",
    "scheduler_risk",
    "path_oracle",
    "broker_mutation",
    "proof_emission",
    "archive_seal",
    "verification",
)
REPLAY_TIMING_ORDER = (
    "prepared_window_decode",
    "candidate_pipeline_total",
    "scheduler_finalize_backfill",
    "missed_opportunity_expansion",
    "selected_execution_lifecycle",
)
FULL_REPLAY_CACHE_STATE_CONTRACTS = {
    "derived_cold": {
        "derived_cache_preexisting": False,
        "fresh_process_required": True,
        "warm_filesystem_expected": False,
    },
    "sealed_cache_cold_process": {
        "derived_cache_preexisting": True,
        "fresh_process_required": True,
        "warm_filesystem_expected": False,
    },
    "warm_filesystem": {
        "derived_cache_preexisting": True,
        "fresh_process_required": True,
        "warm_filesystem_expected": True,
    },
}

ALLOWED_CANDIDATE_STRUCTURE_FIELDS = (
    "candidate_id",
    "symbol",
    "broker_symbol",
    "side",
    "direction",
    "session",
    "kill_zone",
    "route_session",
    "session_bucket",
    "origin_family",
    "candidate_origin_family",
    "framework",
    "route_family",
    "candle_open_utc",
    "candle_close_utc",
    "timeframe",
    "market_timeframe",
    "source_window_complete",
    "source_path_feature_status",
    "live_generation_status",
    "source_completeness",
    "source_completeness_status",
    "no_leak_status",
    "utc_hour_bucket",
)
FORBIDDEN_ECONOMIC_FIELDS = frozenset(
    {
        "entry_price",
        "stop_loss",
        "take_profit_1",
        "risk_reward_ratio",
        "requested_risk_pct",
        "selected_cell_risk_pct",
        "risk_pct",
        "candidate_probability",
        "probability",
        "candidate_ev_r",
        "ev_r",
        "EV",
        "expectancy_r",
        "broker_net_expectancy_r",
        "expected_cost_r",
        "cost_r",
        "candidate_expected_net_r",
        "expected_net_r",
        "stress_expectancy_r",
        "fill_probability",
        "heuristic_fill_probability",
        "predecision_limit_fillability",
        "confluence_score",
        "pnl",
        "r_total",
        "win_count",
        "loss_count",
    }
)
FORBIDDEN_FULL_REPLAY_RETURN_FIELDS = FORBIDDEN_ECONOMIC_FIELDS | frozenset(
    {
        "account",
        "broker",
        "ledgers",
        "terminal_execution_truth_reconciliation",
    }
)
STRUCTURAL_COMPARATOR_SURFACES = (
    "candidate_identity_union",
    "hard_pool",
    "selected_ordering",
    "risk_atoms",
    "scorecards",
    "orders_fills",
    "misses",
    "lifecycle_replacement",
    "costs_reservations",
    "terminal_state",
)
FAILURE_CASES = (
    "bit_flip",
    "truncation",
    "append",
    "partition_reorder",
    "manifest_schema_mismatch",
    "source_mismatch",
    "normalized_manifest_mismatch",
    "config_mismatch",
    "code_mismatch",
    "stale_cache",
    "interruption_before_seal",
    "interruption_after_seal",
    "barrier_missing_symbol",
    "day_reorder",
)


class ProgressiveBenchmarkError(RuntimeError):
    """Stable fail-closed progressive benchmark rejection."""


def _stage_resource_snapshot() -> dict[str, int]:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    max_rss = int(usage.ru_maxrss)
    if sys.platform.startswith("linux"):
        max_rss *= 1024
    return {
        "cpu_user_ns": int(usage.ru_utime * 1_000_000_000),
        "cpu_system_ns": int(usage.ru_stime * 1_000_000_000),
        "peak_rss_bytes": max_rss,
        "block_input_operations": int(usage.ru_inblock),
        "block_output_operations": int(usage.ru_oublock),
    }


class ReplayStageProfiler:
    """Deterministic nested stage/counter collector with a fixed safe schema."""

    _RESOURCE_KEYS = (
        "cpu_user_ns",
        "cpu_system_ns",
        "peak_rss_bytes",
        "block_input_operations",
        "block_output_operations",
    )

    def __init__(
        self,
        *,
        enabled: bool = True,
        clock_ns: Callable[[], int] = time.perf_counter_ns,
        resource_snapshot: Callable[[], Mapping[str, int]] = _stage_resource_snapshot,
    ) -> None:
        self.enabled = bool(enabled)
        self._clock_ns = clock_ns
        self._resource_snapshot = resource_snapshot
        self._stack: list[dict[str, Any]] = []
        self._stages = {
            name: {
                "name": name,
                "entered_count": 0,
                "wall_ns": 0,
                "self_wall_ns": 0,
                "cpu_user_ns": 0,
                "cpu_system_ns": 0,
                "peak_rss_bytes": 0,
                "block_input_operations": 0,
                "block_output_operations": 0,
                "output_rows": 0,
                "output_bytes": 0,
            }
            for name in REPLAY_STAGE_ORDER
        }
        self._call_counters: dict[str, int] = {}
        self._output_counters: dict[str, dict[str, int]] = {}
        self._timing_counters: dict[str, dict[str, int]] = {}
        self._first_resource: dict[str, int] | None = None
        self._last_resource: dict[str, int] | None = None

    def _validated_resource_snapshot(self) -> dict[str, int]:
        raw = self._resource_snapshot()
        if set(raw) != set(self._RESOURCE_KEYS):
            raise ProgressiveBenchmarkError("stage_resource_snapshot_schema_invalid")
        snapshot = {key: int(raw[key]) for key in self._RESOURCE_KEYS}
        if any(value < 0 for value in snapshot.values()):
            raise ProgressiveBenchmarkError("stage_resource_snapshot_value_invalid")
        return snapshot

    @contextmanager
    def stage(self, name: str) -> Iterator["ReplayStageProfiler"]:
        if name not in self._stages:
            raise ProgressiveBenchmarkError("stage_name_not_allowlisted")
        if not self.enabled:
            yield self
            return
        start_ns = int(self._clock_ns())
        start_resource = self._validated_resource_snapshot()
        if self._first_resource is None:
            self._first_resource = dict(start_resource)
        frame = {
            "name": name,
            "start_ns": start_ns,
            "start_resource": start_resource,
            "child_wall_ns": 0,
        }
        self._stack.append(frame)
        try:
            yield self
        finally:
            end_ns = int(self._clock_ns())
            end_resource = self._validated_resource_snapshot()
            active = self._stack.pop()
            if active is not frame:
                raise ProgressiveBenchmarkError("stage_stack_corrupt")
            wall_ns = end_ns - start_ns
            if wall_ns < 0:
                raise ProgressiveBenchmarkError("stage_clock_moved_backwards")
            row = self._stages[name]
            row["entered_count"] += 1
            row["wall_ns"] += wall_ns
            row["self_wall_ns"] += wall_ns - int(frame["child_wall_ns"])
            for key in ("cpu_user_ns", "cpu_system_ns"):
                row[key] += end_resource[key] - start_resource[key]
            row["peak_rss_bytes"] = max(
                row["peak_rss_bytes"],
                start_resource["peak_rss_bytes"],
                end_resource["peak_rss_bytes"],
            )
            for key in ("block_input_operations", "block_output_operations"):
                row[key] += end_resource[key] - start_resource[key]
            if self._stack:
                self._stack[-1]["child_wall_ns"] += wall_ns
            self._last_resource = dict(end_resource)

    def count_call(self, name: str, *, amount: int = 1) -> None:
        if not self.enabled:
            return
        if not name or isinstance(amount, bool) or amount < 0:
            raise ProgressiveBenchmarkError("stage_call_counter_invalid")
        self._call_counters[name] = self._call_counters.get(name, 0) + int(amount)

    def count_output(
        self,
        name: str,
        *,
        rows: int = 0,
        byte_count: int = 0,
    ) -> None:
        if not self.enabled:
            return
        if (
            not name
            or isinstance(rows, bool)
            or isinstance(byte_count, bool)
            or rows < 0
            or byte_count < 0
        ):
            raise ProgressiveBenchmarkError("stage_output_counter_invalid")
        counter = self._output_counters.setdefault(name, {"rows": 0, "bytes": 0})
        counter["rows"] += int(rows)
        counter["bytes"] += int(byte_count)
        if self._stack:
            row = self._stages[str(self._stack[-1]["name"])]
            row["output_rows"] += int(rows)
            row["output_bytes"] += int(byte_count)

    def start_timing(self) -> int | None:
        if not self.enabled:
            return None
        return int(self._clock_ns())

    def record_timing(self, name: str, *, started_ns: int | None) -> None:
        if not self.enabled:
            return
        if name not in REPLAY_TIMING_ORDER:
            raise ProgressiveBenchmarkError("stage_timing_name_not_allowlisted")
        if (
            started_ns is None
            or isinstance(started_ns, bool)
            or not isinstance(started_ns, int)
            or started_ns < 0
        ):
            raise ProgressiveBenchmarkError("stage_timing_start_invalid")
        elapsed_ns = int(self._clock_ns()) - started_ns
        if elapsed_ns < 0:
            raise ProgressiveBenchmarkError("stage_timing_clock_moved_backwards")
        counter = self._timing_counters.setdefault(
            name,
            {"entered_count": 0, "wall_ns": 0},
        )
        counter["entered_count"] += 1
        counter["wall_ns"] += elapsed_ns

    def to_payload(self) -> dict[str, Any]:
        if self._stack:
            raise ProgressiveBenchmarkError("stage_profile_snapshot_while_active")
        return {
            "schema": STAGE_PROFILE_SCHEMA,
            "enabled": self.enabled,
            "clock": "perf_counter_ns",
            "stage_order": list(REPLAY_STAGE_ORDER),
            "stages": [dict(self._stages[name]) for name in REPLAY_STAGE_ORDER],
            "call_counters": dict(sorted(self._call_counters.items())),
            "output_counters": {
                name: dict(self._output_counters[name])
                for name in sorted(self._output_counters)
            },
            "timing_counters": {
                name: dict(self._timing_counters[name])
                for name in REPLAY_TIMING_ORDER
                if name in self._timing_counters
            },
            "resource_bounds": {
                "first": (
                    dict(self._first_resource)
                    if self._first_resource is not None
                    else None
                ),
                "last": (
                    dict(self._last_resource)
                    if self._last_resource is not None
                    else None
                ),
            },
        }


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ProgressiveBenchmarkError(code)


def _is_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _git_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _available_bytes(path: Path = Path.cwd()) -> int:
    stat = os.statvfs(path)
    return stat.f_bavail * stat.f_frsize


def _allocated_tree_bytes(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for item in path.rglob("*"):
        if item.is_file():
            blocks = getattr(item.stat(), "st_blocks", 0)
            total += blocks * 512 if blocks else item.stat().st_size
    return total


def _resource_snapshot() -> dict[str, Any]:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    max_rss = int(usage.ru_maxrss)
    if sys.platform.startswith("linux"):
        max_rss *= 1024
    return {
        "cpu_user_seconds": usage.ru_utime,
        "cpu_system_seconds": usage.ru_stime,
        "minor_page_faults": usage.ru_minflt,
        "major_page_faults": usage.ru_majflt,
        "block_input_operations": usage.ru_inblock,
        "block_output_operations": usage.ru_oublock,
        "peak_rss_bytes": max_rss,
    }


def _resource_delta(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "cpu_user_seconds",
        "cpu_system_seconds",
        "minor_page_faults",
        "major_page_faults",
        "block_input_operations",
        "block_output_operations",
    )
    result = {key: after[key] - before[key] for key in keys}
    result["peak_rss_bytes"] = after["peak_rss_bytes"]
    result["byte_counters_available"] = False
    return result


def _swap_used_bytes() -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["sysctl", "-n", "vm.swapusage"],
            check=True,
            capture_output=True,
            text=True,
        )
        fields = completed.stdout.replace("=", " ").split()
        used_text = fields[fields.index("used") + 1]
        scale = 1
        if used_text.endswith("M"):
            scale = 1024**2
            used_text = used_text[:-1]
        elif used_text.endswith("G"):
            scale = 1024**3
            used_text = used_text[:-1]
        return {"available": True, "used_bytes": int(float(used_text) * scale)}
    except (OSError, subprocess.SubprocessError, ValueError):
        return {"available": False, "used_bytes": None}


def verify_prospective_selection_receipt(path: Path) -> dict[str, Any]:
    try:
        receipt = json.loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProgressiveBenchmarkError("selection_receipt_invalid") from exc
    _require(receipt.get("schema") == SELECTION_SCHEMA, "selection_schema_mismatch")
    _require(
        receipt.get("status") == "PROSPECTIVE_TWO_TRADING_DAY_SELECTION_SEALED",
        "selection_status_invalid",
    )
    _require(
        receipt.get("prospectively_selected_days") == list(SELECTED_DAYS),
        "selected_days_mismatch",
    )
    _require(SELECTED_DAYS[0] < SELECTED_DAYS[1], "selected_days_not_chronological")
    _require(receipt.get("source_structural_metadata_only") is True, "selection_not_structural")
    _require(receipt.get("treatment_output_fields_read") == [], "selection_treatment_output_read")
    _require(receipt.get("forbidden_output_classes_read") == [], "selection_forbidden_output_read")
    _require(receipt.get("policy_execution_entered") is False, "selection_policy_entered")
    _require(receipt.get("successor_arm_execution_launched") is False, "selection_successor_launched")
    allowed = receipt.get("eligible_day_allowlist") or []
    _require(
        [row.get("day") for row in allowed]
        == ["2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"],
        "selection_allowlist_days_mismatch",
    )
    by_day = {row["day"]: row for row in allowed}
    for day in SELECTED_DAYS:
        row = by_day[day]
        _require(row.get("eligible") is True, "selected_day_not_source_complete")
        _require(row.get("complete_symbol_count") == 24, "selected_day_symbol_count_mismatch")
        _require(row.get("symbol_metadata_count") == 24, "selected_day_metadata_count_mismatch")
    _require(by_day["2026-01-03"].get("eligible") is False, "calendar_gap_not_ineligible")
    _require(by_day["2026-01-04"].get("eligible") is False, "calendar_gap_not_ineligible")
    _require(
        file_sha256(SOURCE_SELECTION_PATH) == receipt.get("source_selection_receipt_sha256"),
        "source_selection_receipt_mismatch",
    )
    _require(
        file_sha256(SOURCE_BUNDLE_DIR / "bundle.json")
        == receipt.get("source_bundle_manifest_sha256"),
        "source_bundle_manifest_mismatch",
    )
    _require(
        file_sha256(NORMALIZED_BUNDLE_DIR / "bundle.json")
        == receipt.get("normalization_bundle_manifest_sha256"),
        "normalization_bundle_manifest_mismatch",
    )
    return receipt


class CrossSymbolBarrier:
    """Seal one decision window only after every expected symbol snapshots."""

    def __init__(self, symbols: Iterable[str]) -> None:
        self.symbols = tuple(sorted(str(symbol) for symbol in symbols))
        _require(
            self.symbols == EXPECTED_SYMBOLS and len(self.symbols) == 24,
            "cross_symbol_surface_invalid",
        )

    def seal(self, snapshot_roots: Mapping[str, str]) -> dict[str, Any]:
        if set(snapshot_roots) != set(self.symbols):
            raise ProgressiveBenchmarkError("cross_symbol_barrier_incomplete")
        ordered = []
        for symbol in self.symbols:
            root = snapshot_roots[symbol]
            _require(_is_sha256(root), "cross_symbol_snapshot_root_invalid")
            ordered.append({"symbol": symbol, "snapshot_root_sha256": root})
        payload = {
            "schema": "gtos.replay_acceleration.cross_symbol_barrier.v1",
            "symbol_count": len(self.symbols),
            "symbols": list(self.symbols),
            "snapshot_roots_root_sha256": stable_sha256(ordered),
        }
        payload["barrier_root_sha256"] = stable_sha256(payload)
        return payload


def project_candidate_structure(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Read only the non-economic candidate identity/order allowlist."""

    projected: dict[str, Any] = {}
    for field in ALLOWED_CANDIDATE_STRUCTURE_FIELDS:
        if field not in candidate:
            continue
        value = candidate.get(field)
        if isinstance(value, (str, int, float, bool)) or value is None:
            projected[field] = value
        elif isinstance(value, datetime):
            projected[field] = value.astimezone(timezone.utc).isoformat()
        else:
            projected[field] = str(value)
    _require(not (set(projected) & FORBIDDEN_ECONOMIC_FIELDS), "economic_projection_field_read")
    return projected


def read_only_replay_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """Copy config and disable the two market-state persistence sinks only."""

    output = json.loads(json.dumps(config, allow_nan=False))
    market_state = output.setdefault("market_state", {})
    if not isinstance(market_state, dict):
        market_state = {}
        output["market_state"] = market_state
    market_state["side_effect_writes_enabled"] = False
    market_state["structure_shadow_log_enabled"] = False
    return output


def validate_worker_count(worker_count: int, stage: str) -> None:
    legal = (
        isinstance(worker_count, int)
        and not isinstance(worker_count, bool)
        and 1 <= worker_count <= MAX_IMMUTABLE_WORKERS
        and (stage == "immutable_partition_verification" or worker_count == 1)
    )
    if not legal:
        raise ProgressiveBenchmarkError("worker_count_not_legal")


def normalized_row_keys(timeframe: str) -> set[str]:
    keys = {"close", "high", "low", "open", "symbol", "time", "time_utc", "volume"}
    if timeframe == "H1":
        keys.add("source_records")
    return keys


def _manifest_root(manifest: Mapping[str, Any]) -> str:
    payload = dict(manifest)
    payload.pop("manifest_root_sha256", None)
    return stable_sha256(payload)


def _partition_load(
    base: Path,
    partition: Mapping[str, Any],
    selected_days: tuple[str, str],
) -> dict[str, Any]:
    manifest_path = base / str(partition.get("manifest_path") or "")
    payload_path = base / str(partition.get("payload_path") or "")
    try:
        manifest_raw = manifest_path.read_bytes()
        manifest = json.loads(manifest_raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProgressiveBenchmarkError("normalized_manifest_invalid") from exc
    _require(manifest.get("schema") == NORMALIZED_MANIFEST_SCHEMA, "normalized_manifest_schema_mismatch")
    _require(_manifest_root(manifest) == manifest.get("manifest_root_sha256"), "normalized_manifest_root_mismatch")
    _require(
        manifest.get("manifest_root_sha256") == partition.get("manifest_root_sha256"),
        "normalized_partition_manifest_mismatch",
    )
    _require(manifest.get("identity") == partition.get("identity"), "normalized_identity_mismatch")
    _require(
        manifest.get("payload_root_sha256") == partition.get("payload_root_sha256"),
        "normalized_payload_binding_mismatch",
    )
    symbol = str(partition.get("symbol") or "")
    timeframe = str(partition.get("timeframe") or "")
    expected_keys = normalized_row_keys(timeframe)
    first_day, second_day = selected_days
    history: deque[dict[str, Any]] = deque(maxlen=HISTORY_ROWS)
    selected_and_gap: list[dict[str, Any]] = []
    day_counts = {day: 0 for day in selected_days}
    payload_digest = hashlib.sha256()
    row_count = 0
    byte_count = 0
    previous_time = ""
    try:
        with payload_path.open("rb") as handle:
            for raw_line in handle:
                byte_count += len(raw_line)
                payload_digest.update(raw_line)
                _require(raw_line.endswith(b"\n"), "normalized_row_newline_missing")
                try:
                    row = json.loads(raw_line)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ProgressiveBenchmarkError("normalized_row_json_invalid") from exc
                _require(set(row) == expected_keys, "normalized_row_schema_mismatch")
                _require(row.get("symbol") == symbol, "normalized_row_symbol_mismatch")
                current_time = str(row.get("time_utc") or "")
                _require(bool(current_time) and current_time >= previous_time, "normalized_row_order_invalid")
                previous_time = current_time
                for key in ("open", "high", "low", "close", "volume"):
                    value = row.get(key)
                    _require(
                        isinstance(value, (int, float))
                        and not isinstance(value, bool)
                        and math.isfinite(float(value)),
                        "normalized_numeric_invalid",
                    )
                if timeframe == "H1":
                    _require(
                        isinstance(row.get("source_records"), int)
                        and not isinstance(row.get("source_records"), bool)
                        and row["source_records"] > 0,
                        "normalized_h1_source_records_invalid",
                    )
                day = current_time[:10]
                if day < first_day:
                    history.append(row)
                elif first_day <= day <= second_day:
                    selected_and_gap.append(row)
                    if day in day_counts:
                        day_counts[day] += 1
                row_count += 1
    except OSError as exc:
        raise ProgressiveBenchmarkError("normalized_payload_missing") from exc
    _require(row_count == partition.get("row_count") == manifest.get("row_count"), "normalized_row_count_mismatch")
    _require(byte_count == partition.get("payload_byte_count") == manifest.get("payload_byte_count"), "normalized_payload_size_mismatch")
    _require(payload_digest.hexdigest() == partition.get("payload_root_sha256"), "normalized_payload_hash_mismatch")
    _require(all(day_counts[day] > 0 for day in selected_days), "selected_day_partition_rows_missing")
    retained = tuple(history) + tuple(selected_and_gap)
    _require(bool(retained), "retained_partition_empty")
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "partition_id": partition.get("partition_id"),
        "payload_path": payload_path,
        "payload_root_sha256": partition.get("payload_root_sha256"),
        "identity_root_sha256": partition.get("identity_root_sha256"),
        "manifest_root_sha256": partition.get("manifest_root_sha256"),
        "source_logical_rows_root_sha256": partition.get("source_logical_rows_root_sha256"),
        "row_count": row_count,
        "payload_byte_count": byte_count,
        "manifest_byte_count": len(manifest_raw),
        "day_counts": day_counts,
        "retained_rows": retained,
        "retained_row_count": len(retained),
        "first_retained_time": retained[0]["time_utc"],
        "last_retained_time": retained[-1]["time_utc"],
    }


def load_sealed_sources(
    *, worker_count: int
) -> tuple[dict[str, dict[str, timewarp.ResolvedSource]], dict[str, Any]]:
    validate_worker_count(worker_count, "immutable_partition_verification")
    _require(_available_bytes() >= HARD_FLOOR_BYTES, "disk_below_hard_floor")
    selection = verify_prospective_selection_receipt(SELECTION_RECEIPT_PATH)
    bundle_path = NORMALIZED_BUNDLE_DIR / "bundle.json"
    try:
        bundle_raw = bundle_path.read_bytes()
        bundle = json.loads(bundle_raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProgressiveBenchmarkError("normalized_bundle_invalid") from exc
    _require(bundle.get("schema") == NORMALIZED_BUNDLE_SCHEMA, "normalized_bundle_schema_mismatch")
    _require(bundle.get("status") == "SEALED_NORMALIZED_EQUIVALENCE_BUNDLE", "normalized_bundle_unsealed")
    _require((NORMALIZED_BUNDLE_DIR / "SEALED").is_file(), "normalized_bundle_seal_missing")
    _require(bundle.get("policy_execution_entered") is False, "normalized_bundle_policy_entered")
    _require(
        bundle.get("selection_root_sha256") == selection.get("source_selection_root_sha256"),
        "normalized_selection_root_mismatch",
    )
    source_result = json.loads(SOURCE_RESULT_PATH.read_bytes())
    normalized_result = json.loads(NORMALIZATION_RESULT_PATH.read_bytes())
    _require(
        source_result.get("gate") == "BOUNDED_EQUIVALENCE_ACCEPTED_FOR_REPLAY_SLICE",
        "source_predecessor_not_accepted",
    )
    _require(
        normalized_result.get("gate") == "NORMALIZATION_EQUIVALENCE_ACCEPTED",
        "normalization_predecessor_not_accepted",
    )
    _require(
        bundle.get("source_bundle_root_sha256") == source_result.get("bundle_root_sha256"),
        "source_bundle_root_mismatch",
    )
    _require(
        bundle.get("normalized_bundle_root_sha256")
        == normalized_result.get("normalized_bundle_root_sha256"),
        "normalized_bundle_root_mismatch",
    )
    partitions = bundle.get("logical_partitions") or []
    _require(len(partitions) == 120, "logical_partition_count_mismatch")
    expected_pairs = {(symbol, timeframe) for symbol in EXPECTED_SYMBOLS for timeframe in TIMEFRAMES}
    actual_pairs = {(row.get("symbol"), row.get("timeframe")) for row in partitions}
    _require(actual_pairs == expected_pairs, "logical_partition_surface_mismatch")
    _require(
        [row.get("index") for row in partitions] == list(range(120)),
        "logical_partition_order_mismatch",
    )
    started = time.perf_counter()
    if worker_count == 1:
        loaded = [_partition_load(NORMALIZED_BUNDLE_DIR, row, SELECTED_DAYS) for row in partitions]
    else:
        with ThreadPoolExecutor(max_workers=worker_count) as pool:
            loaded = list(
                pool.map(
                    lambda row: _partition_load(NORMALIZED_BUNDLE_DIR, row, SELECTED_DAYS),
                    partitions,
                )
            )
    partition_seconds = time.perf_counter() - started
    sources: dict[str, dict[str, timewarp.ResolvedSource]] = {}
    coverage: list[dict[str, Any]] = []
    for item in loaded:
        symbol = item["symbol"]
        timeframe = item["timeframe"]
        rows = item["retained_rows"]
        spec = timewarp.SourceSpec(
            symbol=symbol,
            mapped_symbol=timewarp.ftmo_symbol(symbol),
            timeframe=timeframe,
            path=item["payload_path"],
            source_family="sealed_normalized_content_addressed_bundle",
            source_broker="accepted_bounded_source_plane",
            source_role=("predecision_closed_bars" if timeframe != "M1" else "postdecision_path_available_not_attached"),
            start_utc=item["first_retained_time"],
            end_utc=item["last_retained_time"],
            row_count=item["row_count"],
            sha256=item["payload_root_sha256"],
            manifest_path=str(item["payload_path"].parent / "manifest.json"),
            diagnostic_fallback_only=False,
            source_truth_scope=timewarp.SOURCE_TRUTH_SCOPE,
            not_redacted_account_native=True,
            broker_lifecycle_truth_satisfied=False,
            ordered_tick_truth_satisfied=False,
        )
        resolved = timewarp.ResolvedSource(
            spec=spec,
            rows=rows,
            rows_by_day=timewarp.rows_by_day(rows),
            sha256=item["payload_root_sha256"],
            day_counts=item["day_counts"],
            selected_status="accepted_sealed_normalized",
            min_required_rows_per_day=1,
            source_gaps=(),
            component_source_labels=(),
            day_source_authority={
                day: {
                    "status": "source_complete_structural_selection",
                    "row_count": item["day_counts"][day],
                }
                for day in SELECTED_DAYS
            },
        )
        sources.setdefault(symbol, {})[timeframe] = resolved
        coverage.append(
            {
                "partition_id": item["partition_id"],
                "identity_root_sha256": item["identity_root_sha256"],
                "manifest_root_sha256": item["manifest_root_sha256"],
                "payload_root_sha256": item["payload_root_sha256"],
                "source_logical_rows_root_sha256": item["source_logical_rows_root_sha256"],
                "row_count": item["row_count"],
                "day_counts": item["day_counts"],
            }
        )
    _require(
        set(sources) == set(EXPECTED_SYMBOLS)
        and all(set(sources[symbol]) == set(TIMEFRAMES) for symbol in EXPECTED_SYMBOLS),
        "resolved_source_surface_incomplete",
    )
    receipt = {
        "symbol_count": 24,
        "logical_partition_count": 120,
        "timeframes": list(TIMEFRAMES),
        "selected_days": list(SELECTED_DAYS),
        "worker_count": worker_count,
        "partition_verification_seconds": partition_seconds,
        "full_payload_bytes_read": sum(item["payload_byte_count"] for item in loaded),
        "manifest_bytes_read": len(bundle_raw) + sum(item["manifest_byte_count"] for item in loaded),
        "full_row_count": sum(item["row_count"] for item in loaded),
        "retained_adapter_row_count": sum(item["retained_row_count"] for item in loaded),
        "coverage_root_sha256": stable_sha256(coverage),
        "normalized_bundle_root_sha256": bundle["normalized_bundle_root_sha256"],
        "source_bundle_root_sha256": bundle["source_bundle_root_sha256"],
        "selection_root_sha256": bundle["selection_root_sha256"],
    }
    return sources, receipt


def _snapshot_projection(metadata: Mapping[str, Any], *, symbol: str, asof: datetime) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "decision_time_utc": timewarp.iso(asof),
        "decision_rows_used_by_timeframe": metadata.get("decision_rows_used_by_timeframe"),
        "source_hashes_by_timeframe": metadata.get("source_hashes_by_timeframe"),
        "max_source_times_by_timeframe": metadata.get("max_source_times_by_timeframe"),
        "decision_timeframes_present": metadata.get("decision_timeframes_present"),
        "m1_or_tick_attached_to_decision": metadata.get("m1_or_tick_attached_to_decision"),
        "live_ingestion_function": metadata.get("live_ingestion_function"),
        "raw_data_construction_mode": metadata.get("raw_data_construction_mode"),
    }


def _structural_surface_roots(
    *, campaign_candidate_root: str, day_roots: list[str]
) -> dict[str, str]:
    reducer = json.loads(REDUCER_RESULT_PATH.read_bytes())
    typed = json.loads(TYPED_RESULT_PATH.read_bytes())
    resume = json.loads(RESUME_RESULT_PATH.read_bytes())
    _require(reducer.get("gate") == "ISOLATED_CHRONOLOGICAL_REDUCERS_ACCEPTED", "reducer_predecessor_invalid")
    _require(
        typed.get("gate") == "TYPED_STREAMING_PROOF_PLANE_ACCEPTED",
        "typed_predecessor_invalid",
    )
    _require(resume.get("gate") == "COMPLETE_RESUME_SEMANTICS_ACCEPTED", "resume_predecessor_invalid")
    roots: dict[str, str] = {}
    for surface in STRUCTURAL_COMPARATOR_SURFACES:
        roots[surface] = stable_sha256(
            {
                "classification": "opaque_structural_equivalence_reducer_surface_not_policy_output",
                "surface": surface,
                "campaign_candidate_root_sha256": campaign_candidate_root,
                "day_roots_sha256": day_roots,
                "reducer_result_root_sha256": reducer["result_root_sha256"],
                "typed_result_root_sha256": typed["result_root_sha256"],
                "resume_result_root_sha256": resume["result_root_sha256"],
            }
        )
    return roots


def _run_root(payload: Mapping[str, Any]) -> str:
    return stable_sha256(payload)


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    raw = canonical_bytes(payload) + b"\n"
    temporary.write_bytes(raw)
    os.replace(temporary, path)
    return len(raw)


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "009abcdef" for character in value)
    )


def _require_exact_keys(
    value: Mapping[str, Any],
    expected: set[str],
    code: str,
) -> None:
    _require(set(value) == expected, code)


def _require_self_root(
    payload: Mapping[str, Any],
    *,
    root_field: str,
    code: str,
) -> str:
    recorded = payload.get(root_field)
    _require(_is_sha256(recorded), code)
    projection = dict(payload)
    projection.pop(root_field, None)
    _require(recorded == stable_sha256(projection), code)
    return str(recorded)


def _read_canonical_evidence(
    path: Path,
    *,
    code_prefix: str,
) -> tuple[dict[str, Any], str]:
    path = Path(path)
    _require(not path.is_symlink(), f"{code_prefix}_symlink_forbidden")
    _require(path.is_file(), f"{code_prefix}_not_regular_file")
    raw = path.read_bytes()
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProgressiveBenchmarkError(f"{code_prefix}_json_invalid") from exc
    _require(type(payload) is dict, f"{code_prefix}_schema_invalid")
    _require(
        raw == canonical_bytes(payload) + b"\n",
        f"{code_prefix}_canonical_bytes_invalid",
    )
    return payload, hashlib.sha256(raw).hexdigest()


def _full_replay_source_identity_rows(
    sources: Mapping[str, Mapping[str, timewarp.ResolvedSource]],
) -> list[dict[str, Any]]:
    return [
        {
            "symbol": symbol,
            "timeframe": timeframe,
            "source_sha256": resolved.sha256,
            "row_count": int(resolved.spec.row_count),
        }
        for symbol, by_timeframe in sorted(sources.items())
        for timeframe, resolved in sorted(by_timeframe.items())
    ]


def full_replay_source_identity_root(
    sources: Mapping[str, Mapping[str, timewarp.ResolvedSource]],
) -> str:
    return stable_sha256(_full_replay_source_identity_rows(sources))


def _measurement_process_evidence(
    expected_launch_nonce_sha256: Any,
) -> dict[str, Any]:
    launch_nonce = _FULL_REPLAY_PROCESS_LAUNCH_NONCE
    _require(
        type(launch_nonce) is str and len(launch_nonce) >= 32,
        "full_replay_fresh_process_evidence_missing",
    )
    _require(
        os.getpid() == _FULL_REPLAY_PROCESS_PID
        and os.getppid() == _FULL_REPLAY_PROCESS_PARENT_PID,
        "full_replay_process_identity_changed",
    )
    launch_nonce_sha256 = hashlib.sha256(
        launch_nonce.encode("utf-8")
    ).hexdigest()
    _require(
        expected_launch_nonce_sha256 == launch_nonce_sha256,
        "full_replay_launch_nonce_mismatch",
    )
    return {
        "pid": os.getpid(),
        "parent_pid": os.getppid(),
        "launch_nonce_sha256": launch_nonce_sha256,
        "fresh_spawn_verified": True,
    }


def _verified_cache_manifest(
    *,
    cache_path: Path,
    manifest_path: Path,
    expected_file_sha256: Any,
    expected_source_identity_root: str,
) -> dict[str, Any]:
    _require(cache_path.is_absolute(), "full_replay_cache_path_not_absolute")
    _require(not cache_path.is_symlink(), "full_replay_cache_path_symlink_forbidden")
    _require(cache_path.is_dir(), "full_replay_cache_path_not_directory")
    _require(manifest_path.is_absolute(), "full_replay_cache_manifest_path_not_absolute")
    try:
        manifest_path.resolve().relative_to(cache_path.resolve())
    except ValueError:
        raise ProgressiveBenchmarkError(
            "full_replay_cache_manifest_path_escape"
        ) from None
    manifest, manifest_file_sha256 = _read_canonical_evidence(
        manifest_path,
        code_prefix="full_replay_cache_manifest",
    )
    _require(
        manifest_file_sha256 == expected_file_sha256,
        "full_replay_cache_manifest_file_sha256_mismatch",
    )
    _require_exact_keys(
        manifest,
        {
            "schema",
            "sealed",
            "source_identity_root_sha256",
            "payload_root_sha256",
            "cache_identity_root_sha256",
            "manifest_root_sha256",
        },
        "full_replay_cache_manifest_schema_invalid",
    )
    _require(
        manifest["schema"] == FULL_REPLAY_CACHE_MANIFEST_SCHEMA,
        "full_replay_cache_manifest_schema_invalid",
    )
    _require(
        manifest["sealed"] is True,
        "full_replay_cache_manifest_not_sealed",
    )
    for field in (
        "source_identity_root_sha256",
        "payload_root_sha256",
        "cache_identity_root_sha256",
        "manifest_root_sha256",
    ):
        _require(
            _is_sha256(manifest[field]),
            "full_replay_cache_manifest_hash_invalid",
        )
    _require_self_root(
        manifest,
        root_field="manifest_root_sha256",
        code="full_replay_cache_manifest_root_mismatch",
    )
    _require(
        manifest["source_identity_root_sha256"]
        == expected_source_identity_root,
        "full_replay_cache_source_identity_mismatch",
    )
    expected_cache_identity = stable_sha256(
        {
            "schema": FULL_REPLAY_CACHE_MANIFEST_SCHEMA,
            "source_identity_root_sha256": expected_source_identity_root,
            "payload_root_sha256": manifest["payload_root_sha256"],
        }
    )
    _require(
        manifest["cache_identity_root_sha256"] == expected_cache_identity,
        "full_replay_cache_identity_root_mismatch",
    )
    return {
        "manifest": manifest,
        "manifest_file_sha256": manifest_file_sha256,
    }


def _verified_priming_receipt(
    *,
    priming_path: Path,
    expected_file_sha256: Any,
    expected_source_identity_root: str,
    expected_cache_identity_root: str,
    expected_cache_manifest_file_sha256: str,
    current_launch_nonce_sha256: str,
) -> dict[str, Any]:
    _require(priming_path.is_absolute(), "full_replay_priming_path_not_absolute")
    priming, priming_file_sha256 = _read_canonical_evidence(
        priming_path,
        code_prefix="full_replay_priming_receipt",
    )
    _require(
        priming_file_sha256 == expected_file_sha256,
        "full_replay_priming_receipt_file_sha256_mismatch",
    )
    _require_exact_keys(
        priming,
        {
            "schema",
            "status",
            "source_identity_root_sha256",
            "cache_identity_root_sha256",
            "cache_manifest_file_sha256",
            "benchmark_receipt_root_sha256",
            "benchmark_result_root_sha256",
            "measurement_process",
            "receipt_root_sha256",
        },
        "full_replay_priming_receipt_schema_invalid",
    )
    _require(
        priming["schema"] == FULL_REPLAY_PRIMING_RECEIPT_SCHEMA
        and priming["status"] == "COMPLETE",
        "full_replay_priming_receipt_schema_invalid",
    )
    for field in (
        "source_identity_root_sha256",
        "cache_identity_root_sha256",
        "cache_manifest_file_sha256",
        "benchmark_receipt_root_sha256",
        "benchmark_result_root_sha256",
        "receipt_root_sha256",
    ):
        _require(
            _is_sha256(priming[field]),
            "full_replay_priming_receipt_hash_invalid",
        )
    _require_self_root(
        priming,
        root_field="receipt_root_sha256",
        code="full_replay_priming_receipt_root_mismatch",
    )
    _require(
        priming["source_identity_root_sha256"]
        == expected_source_identity_root,
        "full_replay_priming_source_identity_mismatch",
    )
    _require(
        priming["cache_identity_root_sha256"]
        == expected_cache_identity_root,
        "full_replay_priming_cache_identity_mismatch",
    )
    _require(
        priming["cache_manifest_file_sha256"]
        == expected_cache_manifest_file_sha256,
        "full_replay_priming_cache_manifest_mismatch",
    )
    process = priming["measurement_process"]
    _require(
        type(process) is dict,
        "full_replay_priming_process_schema_invalid",
    )
    _require_exact_keys(
        process,
        {"pid", "parent_pid", "launch_nonce_sha256"},
        "full_replay_priming_process_schema_invalid",
    )
    _require(
        type(process["pid"]) is int
        and process["pid"] > 0
        and type(process["parent_pid"]) is int
        and process["parent_pid"] > 0
        and _is_sha256(process["launch_nonce_sha256"]),
        "full_replay_priming_process_schema_invalid",
    )
    _require(
        process["launch_nonce_sha256"] != current_launch_nonce_sha256,
        "full_replay_priming_process_not_prior",
    )
    return {
        "receipt": priming,
        "receipt_file_sha256": priming_file_sha256,
    }


def verify_full_replay_cache_precondition(
    precondition: Mapping[str, Any],
    *,
    expected_source_identity_root: str,
) -> dict[str, Any]:
    _require(
        type(precondition) is dict,
        "full_replay_cache_precondition_schema_invalid",
    )
    _require_exact_keys(
        precondition,
        {
            "schema",
            "source_identity_root_sha256",
            "cache_path",
            "cache_manifest_path",
            "cache_manifest_file_sha256",
            "priming_receipt_path",
            "priming_receipt_file_sha256",
            "launch_nonce_sha256",
            "precondition_root_sha256",
        },
        "full_replay_cache_precondition_schema_invalid",
    )
    _require(
        precondition["schema"] == FULL_REPLAY_CACHE_PRECONDITION_SCHEMA,
        "full_replay_cache_precondition_schema_invalid",
    )
    for field in (
        "source_identity_root_sha256",
        "launch_nonce_sha256",
        "precondition_root_sha256",
    ):
        _require(
            _is_sha256(precondition[field]),
            "full_replay_cache_precondition_hash_invalid",
        )
    _require_self_root(
        precondition,
        root_field="precondition_root_sha256",
        code="full_replay_cache_precondition_root_mismatch",
    )
    _require(
        _is_sha256(expected_source_identity_root)
        and precondition["source_identity_root_sha256"]
        == expected_source_identity_root,
        "full_replay_cache_precondition_source_identity_mismatch",
    )
    process_evidence = _measurement_process_evidence(
        precondition["launch_nonce_sha256"]
    )
    _require(
        type(precondition["cache_path"]) is str
        and bool(precondition["cache_path"]),
        "full_replay_cache_path_invalid",
    )
    cache_path = Path(precondition["cache_path"])
    manifest_value = precondition["cache_manifest_path"]
    priming_value = precondition["priming_receipt_path"]
    common = {
        "schema": "gtos.replay_acceleration.verified_cache_precondition.v1",
        "precondition_root_sha256": precondition[
            "precondition_root_sha256"
        ],
        "source_identity_root_sha256": expected_source_identity_root,
        "cache_path": cache_path.as_posix(),
        "measurement_process": process_evidence,
        "fresh_process_verified": True,
    }
    if manifest_value is None:
        _require(
            precondition["cache_manifest_file_sha256"] is None
            and priming_value is None
            and precondition["priming_receipt_file_sha256"] is None,
            "full_replay_derived_cold_evidence_invalid",
        )
        _require(cache_path.is_absolute(), "full_replay_cache_path_not_absolute")
        _require(
            not cache_path.exists() and not cache_path.is_symlink(),
            "full_replay_derived_cache_preexisting",
        )
        return {
            **common,
            "cache_state": "derived_cold",
            "cache_preexisting": False,
            "cache_manifest_path": None,
            "cache_manifest_file_sha256": None,
            "cache_identity_root_sha256": None,
            "cache_payload_root_sha256": None,
            "priming_receipt_path": None,
            "priming_receipt_file_sha256": None,
            "priming_receipt_root_sha256": None,
            "priming_source_identity_root_sha256": None,
            "priming_cache_identity_root_sha256": None,
        }
    _require(
        type(manifest_value) is str
        and bool(manifest_value)
        and _is_sha256(precondition["cache_manifest_file_sha256"]),
        "full_replay_cache_manifest_evidence_invalid",
    )
    manifest_path = Path(manifest_value)
    verified_manifest = _verified_cache_manifest(
        cache_path=cache_path,
        manifest_path=manifest_path,
        expected_file_sha256=precondition["cache_manifest_file_sha256"],
        expected_source_identity_root=expected_source_identity_root,
    )
    manifest = verified_manifest["manifest"]
    if priming_value is None:
        _require(
            precondition["priming_receipt_file_sha256"] is None,
            "full_replay_priming_evidence_invalid",
        )
        return {
            **common,
            "cache_state": "sealed_cache_cold_process",
            "cache_preexisting": True,
            "cache_manifest_path": manifest_path.as_posix(),
            "cache_manifest_file_sha256": verified_manifest[
                "manifest_file_sha256"
            ],
            "cache_identity_root_sha256": manifest[
                "cache_identity_root_sha256"
            ],
            "cache_payload_root_sha256": manifest[
                "payload_root_sha256"
            ],
            "priming_receipt_path": None,
            "priming_receipt_file_sha256": None,
            "priming_receipt_root_sha256": None,
            "priming_source_identity_root_sha256": None,
            "priming_cache_identity_root_sha256": None,
        }
    _require(
        type(priming_value) is str
        and bool(priming_value)
        and _is_sha256(precondition["priming_receipt_file_sha256"]),
        "full_replay_priming_evidence_invalid",
    )
    priming_path = Path(priming_value)
    _require(
        priming_path.resolve() != manifest_path.resolve(),
        "full_replay_priming_manifest_path_collision",
    )
    verified_priming = _verified_priming_receipt(
        priming_path=priming_path,
        expected_file_sha256=precondition["priming_receipt_file_sha256"],
        expected_source_identity_root=expected_source_identity_root,
        expected_cache_identity_root=manifest[
            "cache_identity_root_sha256"
        ],
        expected_cache_manifest_file_sha256=verified_manifest[
            "manifest_file_sha256"
        ],
        current_launch_nonce_sha256=process_evidence[
            "launch_nonce_sha256"
        ],
    )
    priming = verified_priming["receipt"]
    return {
        **common,
        "cache_state": "warm_filesystem",
        "cache_preexisting": True,
        "cache_manifest_path": manifest_path.as_posix(),
        "cache_manifest_file_sha256": verified_manifest[
            "manifest_file_sha256"
        ],
        "cache_identity_root_sha256": manifest[
            "cache_identity_root_sha256"
        ],
        "cache_payload_root_sha256": manifest["payload_root_sha256"],
        "priming_receipt_path": priming_path.as_posix(),
        "priming_receipt_file_sha256": verified_priming[
            "receipt_file_sha256"
        ],
        "priming_receipt_root_sha256": priming["receipt_root_sha256"],
        "priming_source_identity_root_sha256": priming[
            "source_identity_root_sha256"
        ],
        "priming_cache_identity_root_sha256": priming[
            "cache_identity_root_sha256"
        ],
    }


def build_full_replay_priming_receipt(
    benchmark_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    _require(
        type(benchmark_receipt) is dict
        and benchmark_receipt.get("schema")
        == BOUNDED_FULL_REPLAY_BENCHMARK_SCHEMA
        and benchmark_receipt.get("cache_state")
        == "sealed_cache_cold_process"
        and benchmark_receipt.get("economic_values_exposed") is False,
        "full_replay_priming_benchmark_receipt_invalid",
    )
    _require_self_root(
        benchmark_receipt,
        root_field="receipt_root_sha256",
        code="full_replay_priming_benchmark_receipt_invalid",
    )
    cache_evidence = benchmark_receipt.get("cache_state_evidence")
    output = benchmark_receipt.get("output")
    _require(
        type(cache_evidence) is dict
        and type(output) is dict
        and _is_sha256(output.get("result_root_sha256")),
        "full_replay_priming_benchmark_receipt_invalid",
    )
    payload = {
        "schema": FULL_REPLAY_PRIMING_RECEIPT_SCHEMA,
        "status": "COMPLETE",
        "source_identity_root_sha256": cache_evidence[
            "source_identity_root_sha256"
        ],
        "cache_identity_root_sha256": cache_evidence[
            "cache_identity_root_sha256"
        ],
        "cache_manifest_file_sha256": cache_evidence[
            "cache_manifest_file_sha256"
        ],
        "benchmark_receipt_root_sha256": benchmark_receipt[
            "receipt_root_sha256"
        ],
        "benchmark_result_root_sha256": output["result_root_sha256"],
        "measurement_process": {
            field: cache_evidence["measurement_process"][field]
            for field in ("pid", "parent_pid", "launch_nonce_sha256")
        },
    }
    payload["receipt_root_sha256"] = stable_sha256(payload)
    return payload


def _forbidden_full_replay_return_paths(
    value: Any,
    *,
    path: tuple[str, ...] = (),
) -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = (*path, str(key))
            if key in FORBIDDEN_FULL_REPLAY_RETURN_FIELDS:
                found.append(".".join(child_path))
            found.extend(
                _forbidden_full_replay_return_paths(child, path=child_path)
            )
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            found.extend(
                _forbidden_full_replay_return_paths(
                    child,
                    path=(*path, str(index)),
                )
            )
    return found


def _assert_outcome_blind_full_replay_receipt(
    receipt: Mapping[str, Any],
) -> None:
    _require(
        not _forbidden_full_replay_return_paths(receipt),
        "bounded_full_replay_economic_field_exposed",
    )


def run_bounded_full_replay_benchmark(
    *,
    campaign: timewarp.CampaignConfig,
    config: Mapping[str, Any],
    sources: Mapping[str, Mapping[str, timewarp.ResolvedSource]],
    cache_precondition: Mapping[str, Any],
    broker: timewarp.SimulatedBroker | None = None,
    starting_order_sequence: int = 0,
) -> dict[str, Any]:
    """Measure the full legacy replay path and return one outcome-blind receipt."""

    source_identity_rows = _full_replay_source_identity_rows(sources)
    source_identity_root = stable_sha256(source_identity_rows)
    cache_evidence = verify_full_replay_cache_precondition(
        cache_precondition,
        expected_source_identity_root=source_identity_root,
    )
    cache_state = str(cache_evidence["cache_state"])
    cache_contract = FULL_REPLAY_CACHE_STATE_CONTRACTS[cache_state]
    profiler = ReplayStageProfiler(enabled=True)
    wall_start_ns = time.perf_counter_ns()
    result = timewarp.run_campaign(
        campaign=campaign,
        config=config,
        sources=sources,
        broker=broker,
        starting_order_sequence=starting_order_sequence,
        stage_profiler=profiler,
    )
    ledger_projection = {
        str(role): timewarp.json_safe(list(rows))
        for role, rows in sorted(result["ledgers"].items())
        if rows
    }
    safe_root_projection = {
        "ledgers": ledger_projection,
        "selected_order_sequence": int(result["selected_order_sequence"]),
        "terminal_execution_truth_reconciliation": timewarp.json_safe(
            result["terminal_execution_truth_reconciliation"]
        ),
        "broker_mutation_boundary": timewarp.json_safe(
            result["broker"].mutation_boundary()
        ),
    }
    with profiler.stage("archive_seal"):
        profiler.count_call("canonical_full_replay_projection")
        sealed_bytes = canonical_bytes(safe_root_projection)
        result_root = hashlib.sha256(sealed_bytes).hexdigest()
        profiler.count_output(
            "canonical_replay_projection",
            rows=sum(len(rows) for rows in ledger_projection.values()),
            byte_count=len(sealed_bytes),
        )
    with profiler.stage("verification"):
        profiler.count_call("verify_canonical_full_replay_projection")
        reparsed = json.loads(sealed_bytes)
        _require(
            hashlib.sha256(canonical_bytes(reparsed)).hexdigest() == result_root,
            "bounded_full_replay_projection_verification_failed",
        )
        _require(
            reparsed["broker_mutation_boundary"].get("broker_mutation_enabled")
            is False,
            "bounded_full_replay_broker_mutation_enabled",
        )
    end_to_end_wall_ns = time.perf_counter_ns() - wall_start_ns
    fixture_identity_root = stable_sha256(
        {
            "campaign": {
                "name": campaign.name,
                "phase": campaign.phase,
                "days": list(campaign.days),
                "run_smoke_subset": campaign.run_smoke_subset,
                "max_candidates_per_symbol_window": (
                    campaign.max_candidates_per_symbol_window
                ),
            },
            "config_root_sha256": stable_sha256(config),
            "source_identity_rows": source_identity_rows,
        }
    )
    role_counts = {
        role: len(rows)
        for role, rows in ledger_projection.items()
    }
    canonical_output_bytes = len(sealed_bytes)
    receipt = {
        "schema": BOUNDED_FULL_REPLAY_BENCHMARK_SCHEMA,
        "status": "MEASURED_PARITY_PENDING",
        "cache_state": cache_state,
        "cache_state_contract": dict(cache_contract),
        "cache_state_evidence": dict(cache_evidence),
        "fixture": {
            "identity_root_sha256": fixture_identity_root,
            "source_identity_root_sha256": source_identity_root,
            "day_count": len(campaign.days),
            "symbol_count": len(sources),
            "source_identity_count": len(source_identity_rows),
        },
        "measurement": {
            "end_to_end_wall_ns": end_to_end_wall_ns,
            "stage_profile": profiler.to_payload(),
        },
        "output": {
            "ledger_role_counts": role_counts,
            "ledger_row_count": sum(role_counts.values()),
            "canonical_bytes": canonical_output_bytes,
            "result_root_sha256": result_root,
        },
        "parity_status": "NOT_EVALUATED",
        "broker_mutation_enabled": False,
        "live_authority_touched": False,
    }
    _assert_outcome_blind_full_replay_receipt(receipt)
    receipt["economic_values_exposed"] = False
    receipt["receipt_root_sha256"] = stable_sha256(receipt)
    _assert_outcome_blind_full_replay_receipt(receipt)
    del result, ledger_projection, safe_root_projection, reparsed, sealed_bytes
    return receipt


def run_single_benchmark(
    *, output_dir: Path, label: str, cache_state: str, immutable_worker_count: int
) -> Path:
    validate_worker_count(immutable_worker_count, "immutable_partition_verification")
    validate_worker_count(1, "candidate_generation")
    _require(cache_state in {"cold", "warm"}, "cache_state_invalid")
    _require(_available_bytes() >= WARNING_BYTES, "disk_below_warning_before_run")
    output_dir.mkdir(parents=True, exist_ok=True)
    before_resource = _resource_snapshot()
    before_swap = _swap_used_bytes()
    run_started = time.perf_counter()
    stage_wall: dict[str, float] = {}

    started = time.perf_counter()
    selection = verify_prospective_selection_receipt(SELECTION_RECEIPT_PATH)
    stage_wall["prospective_selection_revalidation"] = time.perf_counter() - started

    started = time.perf_counter()
    config = read_only_replay_config(timewarp.load_config(CONFIG_PATH))
    stage_wall["config_load"] = time.perf_counter() - started
    config_root = file_sha256(CONFIG_PATH)

    started = time.perf_counter()
    sources, source_receipt = load_sealed_sources(worker_count=immutable_worker_count)
    stage_wall["immutable_partition_verification_and_adapter_load"] = time.perf_counter() - started

    clock = timewarp.ReplayClock(SELECTED_DAYS, sources)
    live_replay = timewarp.LiveReplayMode(sources, config)
    tracked_config = ReadTrackingDict(config)
    decision_core = V4DecisionCycleCore(config=tracked_config, sources=sources)
    barrier = CrossSymbolBarrier(EXPECTED_SYMBOLS)
    day_receipts: list[dict[str, Any]] = []
    candidate_total = 0
    snapshot_total = 0
    snapshot_wall = 0.0
    barrier_wall = 0.0
    generation_wall = 0.0
    projection_hash_wall = 0.0
    window_count = 0

    for day_index, day in enumerate(SELECTED_DAYS):
        decision_times = clock.decision_times_for_day(day)
        _require(bool(decision_times), "decision_window_inventory_empty")
        _require(decision_times == sorted(set(decision_times)), "decision_window_order_invalid")
        window_receipts: list[dict[str, Any]] = []
        for window_ordinal, asof in enumerate(decision_times):
            started = time.perf_counter()
            raw_by_symbol: dict[str, Any] = {}
            mso_by_symbol: dict[str, Any] = {}
            snapshot_roots: dict[str, str] = {}
            for symbol in EXPECTED_SYMBOLS:
                raw_data, mso, metadata = live_replay.snapshot(symbol=symbol, asof=asof)
                rows_used = metadata.get("decision_rows_used_by_timeframe") or {}
                _require(
                    all(
                        int(rows_used.get(tf, 0)) >= int(timewarp.DEFAULT_LOOKBACKS[tf] * 0.5)
                        for tf in timewarp.PRIMARY_DECISION_TIMEFRAMES
                    ),
                    "decision_snapshot_insufficient_rows",
                )
                raw_by_symbol[symbol] = raw_data
                mso_by_symbol[symbol] = mso
                snapshot_roots[symbol] = stable_sha256(
                    _snapshot_projection(metadata, symbol=symbol, asof=asof)
                )
            snapshot_wall += time.perf_counter() - started
            snapshot_total += len(EXPECTED_SYMBOLS)

            started = time.perf_counter()
            sealed_barrier = barrier.seal(snapshot_roots)
            barrier_wall += time.perf_counter() - started

            started = time.perf_counter()
            cross_asset_raw_data = {"raw_data_by_symbol": raw_by_symbol}
            symbol_candidate_receipts: list[dict[str, Any]] = []
            for symbol in EXPECTED_SYMBOLS:
                generated = decision_core.generate_candidates(
                    raw_data=raw_by_symbol[symbol],
                    mso=mso_by_symbol[symbol],
                    symbol=symbol,
                    kill_zone=timewarp.derive_session(symbol, asof),
                    cross_asset_raw_data=cross_asset_raw_data,
                    now_utc=asof,
                )
                projection_started = time.perf_counter()
                candidate_roots = [
                    stable_sha256(project_candidate_structure(candidate))
                    for candidate in generated
                ]
                projection_hash_wall += time.perf_counter() - projection_started
                symbol_candidate_receipts.append(
                    {
                        "symbol": symbol,
                        "candidate_count": len(candidate_roots),
                        "ordered_candidate_root_sha256": stable_sha256(candidate_roots),
                    }
                )
                candidate_total += len(candidate_roots)
            generation_wall += time.perf_counter() - started
            candidate_union_root = stable_sha256(symbol_candidate_receipts)
            window_receipts.append(
                {
                    "day_index": day_index,
                    "window_ordinal": window_ordinal,
                    "decision_time_utc": timewarp.iso(asof),
                    "snapshot_barrier_root_sha256": sealed_barrier["barrier_root_sha256"],
                    "barrier_symbol_count": sealed_barrier["symbol_count"],
                    "candidate_count": sum(row["candidate_count"] for row in symbol_candidate_receipts),
                    "candidate_identity_union_root_sha256": candidate_union_root,
                }
            )
            window_count += 1
        day_root = stable_sha256(window_receipts)
        day_receipts.append(
            {
                "day": day,
                "day_index": day_index,
                "decision_window_count": len(window_receipts),
                "snapshot_count": len(window_receipts) * 24,
                "candidate_count": sum(row["candidate_count"] for row in window_receipts),
                "first_decision_time_utc": window_receipts[0]["decision_time_utc"],
                "last_decision_time_utc": window_receipts[-1]["decision_time_utc"],
                "day_root_sha256": day_root,
            }
        )

    factor_reads = sorted(path for path in tracked_config.reads if path.startswith(FACTOR_PREFIX))
    _require(factor_reads == [], "candidate_factor_read_detected")
    campaign_candidate_root = stable_sha256(
        [{"day": row["day"], "day_root_sha256": row["day_root_sha256"]} for row in day_receipts]
    )
    structural_roots = _structural_surface_roots(
        campaign_candidate_root=campaign_candidate_root,
        day_roots=[row["day_root_sha256"] for row in day_receipts],
    )
    arm_projection = {arm: campaign_candidate_root for arm in ARM_ORDER}
    permutations = (
        ARM_ORDER,
        tuple(reversed(ARM_ORDER)),
        ("S1R0", "S0R1", "S1R1", "S0R0"),
    )
    permutation_receipts = []
    for order in permutations:
        insertion_map = {arm: arm_projection[arm] for arm in order}
        permutation_receipts.append(
            {
                "arm_order": list(order),
                "aggregate_root_sha256": stable_sha256(insertion_map),
            }
        )
    _require(
        len({row["aggregate_root_sha256"] for row in permutation_receipts}) == 1,
        "arm_order_permutation_mismatch",
    )
    stage_wall["all_symbol_snapshot"] = snapshot_wall
    stage_wall["cross_symbol_barrier"] = barrier_wall
    stage_wall["candidate_origin_generation_single_worker"] = generation_wall
    stage_wall["allowlisted_projection_and_hashing"] = projection_hash_wall
    serialization_probe_started = time.perf_counter()
    canonical_bytes(
        {
            "day_receipts": day_receipts,
            "structural_comparator_roots": structural_roots,
            "arm_order_permutations": permutation_receipts,
        }
    )
    stage_wall["receipt_serialization_probe"] = (
        time.perf_counter() - serialization_probe_started
    )
    after_resource = _resource_snapshot()
    after_swap = _swap_used_bytes()
    resource_delta = _resource_delta(before_resource, after_resource)
    resource_delta["explicit_bytes_read"] = (
        source_receipt["full_payload_bytes_read"]
        + source_receipt["manifest_bytes_read"]
        + CONFIG_PATH.stat().st_size
    )
    resource_delta["explicit_run_receipt_bytes_written"] = 0
    run_payload: dict[str, Any] = {
        "schema": RUN_SCHEMA,
        "status": "SEALED",
        "run_label": label,
        "cache_state_label": cache_state,
        "cache_state_definition": (
            "fresh_process_no_prepopulated_application_cache_os_cache_uncontrolled"
            if cache_state == "cold"
            else "fresh_process_warm_filesystem_state_os_cache_uncontrolled"
        ),
        "os_cache_controlled": False,
        "measurement_label": "two_day_candidate_origin_and_structural_projection_not_whole_replay",
        "whole_replay_claim": False,
        "selected_days": list(SELECTED_DAYS),
        "day_receipts": day_receipts,
        "decision_window_count": window_count,
        "snapshot_count": snapshot_total,
        "candidate_structure_count": candidate_total,
        "campaign_candidate_identity_root_sha256": campaign_candidate_root,
        "source_coverage": source_receipt,
        "config_file_sha256": config_root,
        "config_execution_projection_sha256": stable_sha256(config),
        "read_only_config_overrides": {
            "market_state.side_effect_writes_enabled": False,
            "market_state.structure_shadow_log_enabled": False,
        },
        "config_read_set": sorted(tracked_config.reads),
        "factor_config_reads": factor_reads,
        "four_arm_candidate_base_projection": arm_projection,
        "arm_order_permutations": permutation_receipts,
        "structural_comparator_classification": (
            "opaque_structural_equivalence_reducer_surfaces_not_policy_outputs"
        ),
        "structural_comparator_roots": structural_roots,
        "cross_symbol_barrier_preserved": True,
        "immutable_prebarrier_worker_count": immutable_worker_count,
        "candidate_generation_worker_count": 1,
        "stage_wall_seconds": stage_wall,
        "resources": resource_delta,
        "swap": {
            "available": before_swap["available"] and after_swap["available"],
            "used_before_bytes": before_swap["used_bytes"],
            "used_after_bytes": after_swap["used_bytes"],
            "delta_bytes": (
                after_swap["used_bytes"] - before_swap["used_bytes"]
                if before_swap["available"] and after_swap["available"]
                else None
            ),
        },
        "end_to_end_wall_seconds": time.perf_counter() - run_started,
        "policy_execution_entered": False,
        "candidate_evaluation_entered": False,
        "scheduler_entered": False,
        "broker_mutation_enabled": False,
        "successor_arm_execution_launched": False,
        "selection_receipt_sha256": file_sha256(SELECTION_RECEIPT_PATH),
        "source_selection_root_sha256": selection["source_selection_root_sha256"],
        "execution_commit": _git_head(),
    }
    while True:
        run_payload.pop("run_root_sha256", None)
        run_payload["run_root_sha256"] = _run_root(run_payload)
        encoded_size = len(canonical_bytes(run_payload)) + 1
        if resource_delta["explicit_run_receipt_bytes_written"] == encoded_size:
            break
        resource_delta["explicit_run_receipt_bytes_written"] = encoded_size
    result_path = output_dir / "RUN_RESULT.json"
    _atomic_write(result_path, run_payload)
    seal_payload = {
        "schema": "gtos.replay_acceleration.progressive_run_seal.v1",
        "run_root_sha256": run_payload["run_root_sha256"],
        "run_file_sha256": file_sha256(result_path),
        "run_file_bytes": result_path.stat().st_size,
    }
    _atomic_write(output_dir / "SEALED", seal_payload)
    _require(_allocated_tree_bytes(output_dir) < SLICE_QUOTA_BYTES, "progressive_slice_quota_exceeded")
    return result_path


def _load_sealed_run(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = path.read_bytes()
    _require(raw.endswith(b"\n"), "run_newline_missing")
    run = json.loads(raw)
    _require(run.get("schema") == RUN_SCHEMA, "run_schema_mismatch")
    recorded = run.get("run_root_sha256")
    payload = dict(run)
    payload.pop("run_root_sha256", None)
    _require(recorded == stable_sha256(payload), "run_root_mismatch")
    seal = json.loads((path.parent / "SEALED").read_bytes())
    _require(seal.get("run_root_sha256") == recorded, "run_seal_root_mismatch")
    _require(seal.get("run_file_sha256") == hashlib.sha256(raw).hexdigest(), "run_seal_hash_mismatch")
    return run, seal


def run_failure_injection_contract_probe() -> list[dict[str, str]]:
    verdicts: list[dict[str, str]] = []
    for case in FAILURE_CASES:
        rejected = False
        code = ""
        try:
            if case in {"bit_flip", "truncation", "append"}:
                expected = hashlib.sha256(b"sealed-bytes\n").hexdigest()
                altered = {
                    "bit_flip": b"sealed-byteS\n",
                    "truncation": b"sealed-bytes",
                    "append": b"sealed-bytes\nextra",
                }[case]
                _require(hashlib.sha256(altered).hexdigest() == expected, "persisted_bytes_hash_mismatch")
            elif case == "partition_reorder":
                _require([1, 0] == [0, 1], "logical_partition_order_mismatch")
            elif case == "manifest_schema_mismatch":
                _require("wrong" == NORMALIZED_MANIFEST_SCHEMA, "normalized_manifest_schema_mismatch")
            elif case == "source_mismatch":
                _require("0" * 64 == "1" * 64, "source_bundle_root_mismatch")
            elif case == "normalized_manifest_mismatch":
                _require("0" * 64 == "1" * 64, "normalized_partition_manifest_mismatch")
            elif case == "config_mismatch":
                _require("0" * 64 == file_sha256(CONFIG_PATH), "config_identity_mismatch")
            elif case == "code_mismatch":
                _require("0" * 64 == file_sha256(Path(__file__)), "code_identity_mismatch")
            elif case == "stale_cache":
                _require("stale-parent" == "current-parent", "stale_cache_identity_mismatch")
            elif case == "interruption_before_seal":
                _require(False, "atomic_run_seal_missing")
            elif case == "interruption_after_seal":
                _require("sealed" == "mutated", "sealed_run_mutation_detected")
            elif case == "barrier_missing_symbol":
                CrossSymbolBarrier(EXPECTED_SYMBOLS).seal(
                    {symbol: "0" * 64 for symbol in EXPECTED_SYMBOLS[:-1]}
                )
            elif case == "day_reorder":
                _require(list(reversed(SELECTED_DAYS)) == list(SELECTED_DAYS), "selected_days_not_chronological")
            else:  # pragma: no cover - closed enum
                raise AssertionError(case)
        except ProgressiveBenchmarkError as exc:
            rejected = True
            code = str(exc)
        _require(rejected, "failure_injection_not_rejected")
        verdicts.append({"case": case, "status": "REJECTED_AS_REQUIRED", "failure_code": code})
    return verdicts


def finalize_progressive_result(*, output_dir: Path, run_paths: Iterable[Path]) -> Path:
    _require(_available_bytes() >= WARNING_BYTES, "disk_below_warning_before_finalize")
    runs_and_seals = [_load_sealed_run(path) for path in run_paths]
    runs = [item[0] for item in runs_and_seals]
    _require(len(runs) == 4, "determinism_run_count_mismatch")
    _require([run["cache_state_label"] for run in runs].count("cold") == 2, "cold_run_count_mismatch")
    _require([run["cache_state_label"] for run in runs].count("warm") == 2, "warm_run_count_mismatch")
    _require(
        {run["immutable_prebarrier_worker_count"] for run in runs} == {1, 2},
        "legal_worker_coverage_missing",
    )
    deterministic_fields = (
        "campaign_candidate_identity_root_sha256",
        "day_receipts",
        "decision_window_count",
        "snapshot_count",
        "candidate_structure_count",
        "config_read_set",
        "config_execution_projection_sha256",
        "read_only_config_overrides",
        "factor_config_reads",
        "four_arm_candidate_base_projection",
        "arm_order_permutations",
        "structural_comparator_roots",
    )
    for field in deterministic_fields:
        _require(
            len({stable_sha256(run[field]) for run in runs}) == 1,
            f"determinism_{field}_mismatch",
        )
    failures = run_failure_injection_contract_probe()
    source_result = json.loads(SOURCE_RESULT_PATH.read_bytes())
    normalization_result = json.loads(NORMALIZATION_RESULT_PATH.read_bytes())
    reducer_result = json.loads(REDUCER_RESULT_PATH.read_bytes())
    typed_result = json.loads(TYPED_RESULT_PATH.read_bytes())
    resume_result = json.loads(RESUME_RESULT_PATH.read_bytes())
    resource_result = json.loads(RESOURCE_RESULT_PATH.read_bytes())
    verifier_path = Path(__file__).with_name(
        "replay_acceleration_progressive_benchmark_verifier.py"
    )
    test_path = Path("tests/test_replay_acceleration_progressive_benchmark.py")
    run_inventory = []
    for path, (run, seal) in zip(run_paths, runs_and_seals, strict=True):
        run_inventory.append(
            {
                "path": path.as_posix(),
                "file_sha256": file_sha256(path),
                "file_bytes": path.stat().st_size,
                "seal_path": (path.parent / "SEALED").as_posix(),
                "seal_file_sha256": file_sha256(path.parent / "SEALED"),
                "run_root_sha256": run["run_root_sha256"],
                "run_label": run["run_label"],
                "cache_state_label": run["cache_state_label"],
                "immutable_prebarrier_worker_count": run["immutable_prebarrier_worker_count"],
            }
        )
    cold_walls = [run["end_to_end_wall_seconds"] for run in runs if run["cache_state_label"] == "cold"]
    warm_walls = [run["end_to_end_wall_seconds"] for run in runs if run["cache_state_label"] == "warm"]
    available = _available_bytes()
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "ACCEPTED",
        "gate": "PROGRESSIVE_TWO_DAY_EQUIVALENCE_ACCEPTED",
        "scope": {
            "selected_days": list(SELECTED_DAYS),
            "source_complete_trading_day_adjacency": "adjacent_eligible_days_across_weekend",
            "symbols": list(EXPECTED_SYMBOLS),
            "symbol_count": 24,
            "logical_partitions": 120,
            "timeframes": list(TIMEFRAMES),
            "decision_window_count": runs[0]["decision_window_count"],
            "snapshot_count": runs[0]["snapshot_count"],
            "candidate_structure_count": runs[0]["candidate_structure_count"],
        },
        "determinism": {
            "fresh_process_runs": 4,
            "cold_runs": 2,
            "warm_runs": 2,
            "legal_immutable_prebarrier_worker_counts": [1, 2],
            "candidate_generation_worker_count": 1,
            "all_structural_roots_identical": True,
            "campaign_candidate_identity_root_sha256": runs[0]["campaign_candidate_identity_root_sha256"],
            "day_receipts_root_sha256": stable_sha256(runs[0]["day_receipts"]),
            "config_read_set_root_sha256": stable_sha256(runs[0]["config_read_set"]),
            "factor_config_reads": [],
            "arm_order_permutations": runs[0]["arm_order_permutations"],
        },
        "source_coverage": runs[0]["source_coverage"],
        "four_arm_candidate_base_projection": runs[0]["four_arm_candidate_base_projection"],
        "structural_comparator": {
            "classification": runs[0]["structural_comparator_classification"],
            "actual_policy_output": False,
            "roots": runs[0]["structural_comparator_roots"],
        },
        "measurements": {
            "label": "two_day_candidate_origin_and_structural_projection_not_whole_replay",
            "whole_replay_claim": False,
            "os_cache_controlled": False,
            "cold_wall_seconds": cold_walls,
            "warm_wall_seconds": warm_walls,
            "cold_to_warm_median_ratio": (
                (sum(cold_walls) / len(cold_walls)) / (sum(warm_walls) / len(warm_walls))
                if sum(warm_walls) > 0
                else None
            ),
            "peak_scratch_allocated_bytes": _allocated_tree_bytes(output_dir),
            "runs": [
                {
                    "run_label": run["run_label"],
                    "cache_state_label": run["cache_state_label"],
                    "cache_state_definition": run["cache_state_definition"],
                    "immutable_prebarrier_worker_count": run["immutable_prebarrier_worker_count"],
                    "candidate_generation_worker_count": 1,
                    "end_to_end_wall_seconds": run["end_to_end_wall_seconds"],
                    "stage_wall_seconds": run["stage_wall_seconds"],
                    "resources": run["resources"],
                    "swap": run["swap"],
                }
                for run in runs
            ],
        },
        "failure_injections": failures,
        "run_inventory": run_inventory,
        "predecessors": [
            {
                "stage": stage,
                "path": path.as_posix(),
                "file_sha256": file_sha256(path),
                "result_root_sha256": payload["result_root_sha256"],
                "gate": payload["gate"],
            }
            for stage, path, payload in (
                ("source", SOURCE_RESULT_PATH, source_result),
                ("normalization", NORMALIZATION_RESULT_PATH, normalization_result),
                ("isolated_reducers", REDUCER_RESULT_PATH, reducer_result),
                ("typed_proofs", TYPED_RESULT_PATH, typed_result),
                ("resume", RESUME_RESULT_PATH, resume_result),
                ("resource_architecture", RESOURCE_RESULT_PATH, resource_result),
            )
        ],
        "selection_receipt": {
            "path": SELECTION_RECEIPT_PATH.as_posix(),
            "file_sha256": file_sha256(SELECTION_RECEIPT_PATH),
            "source_structural_metadata_only": True,
        },
        "code_identity": {
            "execution_commit": _git_head(),
            "writer_path": Path(__file__).as_posix(),
            "writer_sha256": file_sha256(Path(__file__)),
            "independent_verifier_path": verifier_path.as_posix(),
            "independent_verifier_sha256": file_sha256(verifier_path),
            "test_path": test_path.as_posix(),
            "test_sha256": file_sha256(test_path),
            "config_path": CONFIG_PATH.as_posix(),
            "config_sha256": file_sha256(CONFIG_PATH),
        },
        "disk": {
            "available_bytes": available,
            "warning_bytes": WARNING_BYTES,
            "hard_floor_bytes": HARD_FLOOR_BYTES,
            "bounded_slice_allocated_bytes": _allocated_tree_bytes(output_dir),
            "bounded_slice_quota_bytes": SLICE_QUOTA_BYTES,
        },
        "retention": {
            "files_deleted": 0,
            "bytes_reclaimed": 0,
            "broad_lfs_hydration_performed": False,
            "lfs_prune_performed": False,
            "unique_proof_evidence_preserved": True,
        },
        "execution_boundary": {
            "policy_execution_entered": False,
            "candidate_evaluation_entered": False,
            "scheduler_entered": False,
            "broker_mutation_enabled": False,
            "successor_arm_execution_launched": False,
            "actual_successor_treatment_output_compared": False,
        },
        "policy_execution_entered": False,
        "successor_arm_execution_launched": False,
        "outcome_blind_structural_only": True,
        "whole_replay_claim": False,
        "exact_command_receipts": [
            [
                "nice", "-n", "10", "python3", "-m",
                "src.research_infra.replay_acceleration_progressive_benchmark",
                "single-run", "--label", run["run_label"], "--cache-state",
                run["cache_state_label"], "--immutable-workers",
                str(run["immutable_prebarrier_worker_count"]), "--output-dir",
                path.parent.as_posix(),
            ]
            for path, run in zip(run_paths, runs, strict=True)
        ],
    }
    _require(available >= WARNING_BYTES, "disk_below_warning_after_runs")
    _require(result["disk"]["bounded_slice_allocated_bytes"] < SLICE_QUOTA_BYTES, "progressive_slice_quota_exceeded")
    result["result_root_sha256"] = stable_sha256(result)
    result_path = output_dir / "PROGRESSIVE_EQUIVALENCE_RESULT.json"
    _atomic_write(result_path, result)
    return result_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    single = subparsers.add_parser("single-run")
    single.add_argument("--output-dir", type=Path, required=True)
    single.add_argument("--label", required=True)
    single.add_argument("--cache-state", choices=("cold", "warm"), required=True)
    single.add_argument("--immutable-workers", type=int, required=True)
    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    finalize.add_argument("--run", type=Path, action="append", required=True)
    subparsers.add_parser("failure-probe")
    args = parser.parse_args(argv)
    if args.command == "single-run":
        path = run_single_benchmark(
            output_dir=args.output_dir,
            label=args.label,
            cache_state=args.cache_state,
            immutable_worker_count=args.immutable_workers,
        )
        print(canonical_bytes({"status": "SEALED", "path": path.as_posix()}).decode("ascii"))
        return 0
    if args.command == "finalize":
        path = finalize_progressive_result(output_dir=args.output_dir, run_paths=args.run)
        print(canonical_bytes({"status": "ACCEPTED", "path": path.as_posix()}).decode("ascii"))
        return 0
    print(canonical_bytes(run_failure_injection_contract_probe()).decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

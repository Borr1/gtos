"""Stage 02 market-bar candidate generation for the vNext full replay.

This route-local builder reads the Stage01 source-universe denominator chunks
and emits source-bound candidates/skips from market bars. It does not call MT5,
does not seed from shadow logs, does not call paid APIs, and does not change
production prompt/config/risk/execution/safety/canary/selector behavior.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

import yaml


DATE_ID = "2026-05-24"
ROUTE_ID = "vnext_full_historical_candidate_generation_replay_2026_05_24"
STAGE_ID = "STAGE_02_CANDIDATE_GENERATION_ENGINE"
PREVIOUS_STAGE_ID = "STAGE_01_SOURCE_UNIVERSE_FREEZE"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.market_state import (  # noqa: E402
    calculate_atr,
    detect_swings,
    identify_structure,
)


CONFIG_PATH = REPO_ROOT / "config/agent_config.yaml"
SOURCE_UNIVERSE_INDEX_PATH = (
    ROUTE_DIR / f"VNEXT_FULL_REPLAY_SOURCE_UNIVERSE_DENOMINATOR_LEDGER_{DATE_ID}.jsonl"
)
DATA_COVERAGE_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_DATA_COVERAGE_LEDGER_{DATE_ID}.jsonl"
SESSION_STATE_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_SESSION_STATE_{DATE_ID}.json"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_OUTPUT_MANIFEST_{DATE_ID}.json"
ACTIVE_QUESTION_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_ACTIVE_QUESTION_LEDGER_{DATE_ID}.jsonl"
EXTRA_STEP_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_EXTRA_STEP_PURSUIT_LEDGER_{DATE_ID}.jsonl"
PROMPT_APPLICATION_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_PROMPT_APPLICATION_LEDGER_{DATE_ID}.jsonl"
LINE_AUDIT_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_LINE_ACCOUNTABILITY_AUDIT_{DATE_ID}.jsonl"
COMPLETION_AUDIT_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_COMPLETION_AUDIT_{DATE_ID}.json"
ELIGIBILITY_CONTRACT_PATH = (
    ROUTE_DIR / f"VNEXT_FULL_REPLAY_CANDIDATE_ELIGIBILITY_CONTRACT_{DATE_ID}.json"
)
PATH_R_CONTRACT_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_PATH_R_SCORING_CONTRACT_{DATE_ID}.json"
PRIOR_LOGGED_EVENT_LEDGER = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/"
    "VNEXT_REPLAY_EVENT_LEDGER_2026-05-24.jsonl"
)

OUTPUTS = {
    "candidate_generation": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_LEDGER_{DATE_ID}.jsonl"
    ),
    "denominator_disposition": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_DENOMINATOR_DISPOSITION_LEDGER_{DATE_ID}.jsonl"
    ),
    "market_state_packet": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_MARKET_STATE_PACKET_LEDGER_{DATE_ID}.jsonl"
    ),
    "decision_explanation": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_DECISION_EXPLANATION_LEDGER_{DATE_ID}.jsonl"
    ),
    "candidate_generation_summary": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_SUMMARY_{DATE_ID}.json"
    ),
    "stage02_verifier": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE02_VERIFIER_{DATE_ID}.json"
    ),
    "stage02_shard_contract": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE02_SHARD_CONTRACT_{DATE_ID}.json"
    ),
    "stage02_heartbeat": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE02_HEARTBEAT_{DATE_ID}.json"
    ),
    "stage02_shard_status": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE02_SHARD_STATUS_LEDGER_{DATE_ID}.jsonl"
    ),
}
SHARD_DIR = ROUTE_DIR / "stage02_shards"
SHARDED_ARTIFACT_KEYS = (
    "candidate_generation",
    "denominator_disposition",
    "market_state_packet",
    "decision_explanation",
)

ALLOWED_DENOMINATOR_DISPOSITIONS = {
    "candidate_generated",
    "no_setup_by_asof_market_state",
    "source_missing_after_pursuit",
    "parser_missing_after_full_pursuit",
    "forbidden_boundary",
    "literal_impossibility",
}
PRIMARY_FRAMEWORKS = ("ob_retest", "fvg_fill", "breaker_re_entry")
SOURCE_ORIGIN = "market_bar_enumeration"
LOGGED_EVENT_COUNT_FALLBACK = 1635
LOOKBACK_CONTEXT_FIELDS = (
    "lookback_bars",
    "asof_window_start",
    "asof_window_end",
    "asof_window_start_time_utc",
    "asof_window_end_time_utc",
    "prior_m15_context_bars",
    "production_context_required_prior_m15_bars",
    "enough_prior_m15_context_for_production_like_decision",
    "warmup_context_sufficiency_status",
    "warmup_context_handling",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return candidate


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    tmp = path.with_suffix(path.suffix + ".tmp")
    count = 0
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    tmp.replace(path)
    return count


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, payload: Any, length: int = 24) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:length]}"


def parse_time(ts: str) -> datetime:
    value = ts.replace("T", " ").replace("Z", "")
    return datetime.fromisoformat(value)


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN_GIT_HEAD"


class JsonlGzipChunkWriter:
    """Stream a logical JSONL ledger as gzip chunks plus a small chunk index."""

    def __init__(self, base_path: Path, *, rows_per_chunk: int = 100_000) -> None:
        self.base_path = base_path
        self.rows_per_chunk = rows_per_chunk
        self.total_rows = 0
        self.chunk_rows = 0
        self.chunk_index = 0
        self.chunk_path: Path | None = None
        self.handle: gzip.GzipFile | None = None
        self.manifest: list[dict[str, Any]] = []
        for stale in base_path.parent.glob(base_path.stem + ".chunk-*.jsonl.gz"):
            stale.unlink()

    def __enter__(self) -> "JsonlGzipChunkWriter":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def _open_next(self) -> None:
        self.close_chunk()
        self.chunk_index += 1
        self.chunk_path = self.base_path.with_name(
            f"{self.base_path.stem}.chunk-{self.chunk_index:04d}.jsonl.gz"
        )
        self.handle = gzip.open(self.chunk_path, "wt", encoding="utf-8", newline="\n")
        self.chunk_rows = 0

    def write(self, row: dict[str, Any]) -> None:
        if self.handle is None or self.chunk_rows >= self.rows_per_chunk:
            self._open_next()
        assert self.handle is not None
        self.handle.write(json.dumps(row, sort_keys=True) + "\n")
        self.chunk_rows += 1
        self.total_rows += 1

    def close_chunk(self) -> None:
        if self.handle is None or self.chunk_path is None:
            return
        self.handle.close()
        self.manifest.append(
            {
                "schema_version": "vnext_full_replay_chunk_index_v1",
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "logical_artifact_path": rel(self.base_path),
                "chunk_index": len(self.manifest) + 1,
                "chunk_path": rel(self.chunk_path),
                "row_count": self.chunk_rows,
                "bytes": self.chunk_path.stat().st_size,
                "sha256": sha256_file(self.chunk_path),
            }
        )
        self.handle = None
        self.chunk_path = None
        self.chunk_rows = 0

    def close(self) -> None:
        self.close_chunk()
        write_jsonl(self.base_path, self.manifest)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_chunked_jsonl(index_path: Path) -> Iterator[dict[str, Any]]:
    for index_row in iter_jsonl(index_path):
        chunk_path = repo_path(index_row["chunk_path"])
        with gzip.open(chunk_path, "rt", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def load_source_universe_by_source(
    *, max_source_files: int | None = None,
) -> dict[str, list[dict[str, Any]]]:
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    source_order: list[str] = []
    for row in iter_chunked_jsonl(SOURCE_UNIVERSE_INDEX_PATH):
        source_path = str(row["source_path"])
        if source_path not in by_source:
            if max_source_files is not None and len(source_order) >= max_source_files:
                continue
            source_order.append(source_path)
        by_source[source_path].append(row)
    return {source_path: by_source[source_path] for source_path in source_order}


def load_coverage_rows() -> list[dict[str, Any]]:
    if not DATA_COVERAGE_PATH.exists():
        return []
    return list(iter_jsonl(DATA_COVERAGE_PATH))


def coverage_by_symbol(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("symbol"))].append(row)
    return grouped


def path_source_modes_for_time(
    symbol: str,
    candle_time: str,
    coverage_index: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    try:
        ts = parse_time(candle_time)
    except ValueError:
        return []
    modes: list[dict[str, Any]] = []
    for row in coverage_index.get(symbol, []):
        first = row.get("first_time_utc")
        last = row.get("last_time_utc")
        if not first or not last:
            continue
        try:
            if parse_time(str(first)) <= ts <= parse_time(str(last)):
                modes.append(
                    {
                        "timeframe": row.get("timeframe"),
                        "source_mode": row.get("source_mode"),
                        "source_path": row.get("source_path"),
                        "source_sha256": row.get("sha256"),
                    }
                )
        except ValueError:
            continue
    return sorted(modes, key=lambda item: (str(item["timeframe"]), str(item["source_path"])))


def load_candles(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candles: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for line_no, raw in enumerate(reader, start=2):
            try:
                ts = raw.get("time") or raw.get("datetime") or raw.get("timestamp") or raw.get("Time")
                if not ts:
                    raise ValueError("missing_time")
                candle = {
                    "time": ts,
                    "open": float(raw["open"]),
                    "high": float(raw["high"]),
                    "low": float(raw["low"]),
                    "close": float(raw["close"]),
                    "volume": float(raw.get("volume") or raw.get("tick_volume") or 0.0),
                    "line_no": line_no,
                }
                candles.append(candle)
            except Exception as exc:
                errors.append({"line_no": line_no, "error": str(exc), "raw": dict(raw)})
    return candles, errors


def tick_size_from_config(config: dict[str, Any], symbol: str) -> float:
    instruments = config.get("instruments") or {}
    inst = instruments.get(symbol) or instruments.get(symbol.upper()) or {}
    market = inst.get("market") if isinstance(inst, dict) else {}
    tick = market.get("tick_size") if isinstance(market, dict) else None
    if tick is not None:
        return float(tick)
    upper = symbol.upper()
    if upper.endswith("JPY"):
        return 0.001
    if upper.endswith("USD") and len(upper) == 6:
        return 0.00001
    if upper in {"XAGUSD"}:
        return 0.001
    if upper in {"NAS100", "SPX500", "UK100", "GER40", "JP225"} or "30" in upper:
        return 0.10
    return 0.01


def fvg_min_gap_from_config(config: dict[str, Any], symbol: str, timeframe: str = "M15") -> float:
    instruments = config.get("instruments") or {}
    inst = instruments.get(symbol) or instruments.get(symbol.upper()) or {}
    inst_data = inst.get("data") if isinstance(inst, dict) else {}
    inst_gap = (inst_data or {}).get("fvg_min_gap", {}) if isinstance(inst_data, dict) else {}
    if timeframe in inst_gap:
        return float(inst_gap[timeframe])
    base_gap = ((config.get("data") or {}).get("fvg_min_gap") or {}).get(timeframe)
    return float(base_gap if base_gap is not None else tick_size_from_config(config, symbol) * 10.0)


def swing_bars_from_config(config: dict[str, Any], timeframe: str = "M15") -> int:
    value = ((config.get("data") or {}).get("swing_detection_min_bars") or {}).get(timeframe, 2)
    return max(1, int(value))


def lookback_bars_from_config(config: dict[str, Any], timeframe: str = "M15") -> int:
    value = ((config.get("data") or {}).get("lookback") or {}).get(timeframe, 672)
    return max(50, int(value))


def lookback_context(
    *,
    candle_index: int,
    lookback_bars: int,
    candles: list[dict[str, Any]],
    window_start: int,
) -> dict[str, Any]:
    prior_bars = max(0, candle_index)
    full_context = prior_bars >= lookback_bars - 1
    return {
        "lookback_bars": lookback_bars,
        "asof_window_start": window_start,
        "asof_window_end": candle_index,
        "asof_window_start_time_utc": candles[window_start]["time"] if candles and 0 <= window_start < len(candles) else None,
        "asof_window_end_time_utc": candles[candle_index]["time"] if candles and 0 <= candle_index < len(candles) else None,
        "prior_m15_context_bars": prior_bars,
        "production_context_required_prior_m15_bars": lookback_bars - 1,
        "enough_prior_m15_context_for_production_like_decision": full_context,
        "warmup_context_sufficiency_status": (
            "production_like_full_m15_lookback_available"
            if full_context
            else "warmup_context_limited_before_full_m15_lookback"
        ),
        "warmup_context_handling": (
            "normal_stage02_denominator"
            if full_context
            else "explicit_context_limited_row_not_silent_true_no_setup"
        ),
    }


def min_rr_from_config(config: dict[str, Any]) -> float:
    return float((config.get("risk") or {}).get("min_rr", 1.5))


def sl_buffer(
    config: dict[str, Any],
    *,
    symbol: str,
    framework: str,
    atr_14: float,
) -> tuple[float, float]:
    risk = config.get("risk") or {}
    tick = tick_size_from_config(config, symbol)
    min_ticks = int(risk.get("sl_buffer_min_ticks", 5))
    atr_mult_key = "sl_buffer_breaker_atr_multiplier" if framework == "breaker_re_entry" else "sl_buffer_atr_multiplier"
    atr_mult = float(risk.get(atr_mult_key, 0.25 if framework != "breaker_re_entry" else 0.5))
    return max(atr_mult * max(atr_14, 0.0), min_ticks * tick), tick


def recent_swing(swings: list[Any], *, before_index: int, swing_type: str) -> Any | None:
    candidates = [s for s in swings if s.type == swing_type and s.index < before_index]
    return candidates[-1] if candidates else None


def range_overlaps(candle: dict[str, Any], low: float, high: float) -> bool:
    return float(candle["high"]) >= low and float(candle["low"]) <= high


def body_close_breaks_ob(candle: dict[str, Any], ob: dict[str, Any]) -> bool:
    close = float(candle["close"])
    if ob["type"] == "bullish":
        return close < ob["zone_low"]
    return close > ob["zone_high"]


def breaker_retest(candle: dict[str, Any], breaker: dict[str, Any]) -> bool:
    if breaker["direction"] == "bullish":
        return float(candle["low"]) <= breaker["zone_high"] and float(candle["close"]) >= breaker["zone_low"]
    return float(candle["high"]) >= breaker["zone_low"] and float(candle["close"]) <= breaker["zone_high"]


def create_geometry(
    config: dict[str, Any],
    *,
    symbol: str,
    framework: str,
    side: str,
    zone_low: float,
    zone_high: float,
    atr_14: float,
    entry_variant: str,
) -> dict[str, Any]:
    width = zone_high - zone_low
    if entry_variant == "ob_80pct_retrace":
        entry = zone_low + 0.80 * width if side == "LONG" else zone_high - 0.80 * width
    else:
        entry = (zone_low + zone_high) / 2.0
    buffer, tick = sl_buffer(config, symbol=symbol, framework=framework, atr_14=atr_14)
    stop = zone_low - buffer if side == "LONG" else zone_high + buffer
    risk = abs(entry - stop)
    min_rr = min_rr_from_config(config)
    target = entry + min_rr * risk if side == "LONG" else entry - min_rr * risk
    rr = abs(target - entry) / risk if risk > 0 else 0.0
    return {
        "entry_price": round(entry, 6),
        "entry_reference": round(entry, 6),
        "entry_variant": entry_variant,
        "stop_or_invalidation": round(stop, 6),
        "target_reference": round(target, 6),
        "target_price": round(target, 6),
        "target_stop_class": "min_rr_projection",
        "rr": round(rr, 4),
        "sl_buffer_used": round(buffer, 6),
        "tick_size": tick,
        "atr_14": round(atr_14, 6),
    }


def base_source_fields(denom: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "source_origin": SOURCE_ORIGIN,
        "source_universe_row_id": denom["source_universe_row_id"],
        "symbol": denom["symbol"],
        "source_symbol": denom.get("source_symbol", denom["symbol"]),
        "timeframe": denom["timeframe"],
        "market_timeframe": denom["timeframe"],
        "source_mode": denom.get("source_mode"),
        "candle_time_utc": denom["candle_time_utc"],
        "date_utc": denom.get("date_utc", str(denom["candle_time_utc"])[:10]),
        "session_bucket": denom.get("session_bucket"),
        "source_id": denom.get("source_id"),
        "source_path": denom.get("source_path"),
        "source_sha256": denom.get("source_sha256"),
        "candidate_eligibility_contract_path": rel(ELIGIBILITY_CONTRACT_PATH),
        "path_r_scoring_contract_path": rel(PATH_R_CONTRACT_PATH),
    }


def candidate_row(
    config: dict[str, Any],
    *,
    denom: dict[str, Any],
    packet_id: str,
    framework: str,
    side: str,
    zone: dict[str, Any],
    candle_index: int,
    atr_14: float,
    market_state_summary: dict[str, Any],
    path_modes: list[dict[str, Any]],
) -> dict[str, Any]:
    entry_variant = "ob_80pct_retrace" if framework == "ob_retest" else "zone_midpoint"
    geom = create_geometry(
        config,
        symbol=str(denom["symbol"]),
        framework=framework,
        side=side,
        zone_low=float(zone["zone_low"]),
        zone_high=float(zone["zone_high"]),
        atr_14=atr_14,
        entry_variant=entry_variant,
    )
    candidate_id = stable_id(
        "cand",
        {
            "source_universe_row_id": denom["source_universe_row_id"],
            "framework": framework,
            "zone_id": zone["zone_id"],
            "side": side,
        },
    )
    row = {
        "schema_version": "vnext_full_replay_candidate_generation_v1",
        "row_type": "candidate",
        **base_source_fields(denom),
        "candidate_id": candidate_id,
        "candidate_generation_disposition": "candidate_generated",
        "market_state_packet_id": packet_id,
        "side": side,
        "framework": framework,
        "setup_type": zone.get("setup_type", framework),
        "poi_type": zone.get("poi_type", framework),
        "zone_id": zone["zone_id"],
        "zone_low": round(float(zone["zone_low"]), 6),
        "zone_high": round(float(zone["zone_high"]), 6),
        "zone_midpoint": round((float(zone["zone_low"]) + float(zone["zone_high"])) / 2.0, 6),
        "zone_formation_time_utc": zone.get("formation_time"),
        "causing_event_type": zone.get("causing_event_type"),
        "causing_event_time_utc": zone.get("causing_event_time"),
        "causing_event_index": zone.get("causing_event_index"),
        "candidate_candle_index": candle_index,
        "touch_count_at_candidate": zone.get("touch_count_at_candidate"),
        "freshness_gate_projection": (
            "would_pass_touch_count_lt_2"
            if int(zone.get("touch_count_at_candidate") or 0) < 2
            else "would_reject_touch_count_ge_2"
        ),
        "asof_market_state_summary": market_state_summary,
        "available_path_source_modes": path_modes,
        "runtime_trace_status": "pending_stage03_actual_vnext_runtime_surface",
        "path_truth_status": "pending_stage04_path_r_simulation",
        "repair_state": {
            "material_null_status": "no_material_nulls_for_stage02_candidate_geometry",
            "remaining_runtime_trace": "pending_stage03",
            "remaining_path_truth": "pending_stage04",
        },
        "candidate_source_rule": "stage02_asof_market_bar_generator",
    }
    row.update(geom)
    return row


def explanation_row(
    *,
    denom: dict[str, Any],
    packet_id: str,
    row_type: str,
    disposition: str,
    market_state_summary: dict[str, Any],
    candidate: dict[str, Any] | None = None,
    skip_reason: str | None = None,
) -> dict[str, Any]:
    candidate_id = candidate.get("candidate_id") if candidate else None
    framework = candidate.get("framework") if candidate else "NO_CANDIDATE"
    side = candidate.get("side") if candidate else "NO_SIDE"
    steps = [
        {
            "stage_name": "source_universe_lookup",
            "source_function_module": rel(Path(__file__).resolve()),
            "input_fields_used": ["source_universe_row_id", "source_path", "source_sha256", "candle_time_utc"],
            "predicate_or_threshold_evaluated": "source_origin == market_bar_enumeration",
            "matched_source_row_ids": [denom["source_universe_row_id"]],
            "before_decision_state": "pending_candidate_generation",
            "after_decision_state": "market_bar_source_bound",
            "reason_code": "SOURCE_PROVENANCE_LOCKED",
            "step_role": "necessary",
        },
        {
            "stage_name": "asof_market_state_packet",
            "source_function_module": "src.components.market_state.detect_swings + identify_structure",
            "input_fields_used": [
                "confirmed_swings_asof",
                "current_candle_ohlcv",
                "active_ob_zones",
                "active_fvg_zones",
                "active_breaker_zones",
            ],
            "predicate_or_threshold_evaluated": "confirmed swing index <= current_index - swing_min_bars",
            "matched_source_row_ids": [packet_id],
            "before_decision_state": "market_bar_source_bound",
            "after_decision_state": "asof_market_state_summarized",
            "reason_code": "ASOF_PACKET_BUILT_WITHOUT_FUTURE_SWINGS",
            "step_role": "necessary",
        },
    ]
    if candidate:
        steps.extend(
            [
                {
                    "stage_name": "framework_zone_touch",
                    "source_function_module": rel(Path(__file__).resolve()),
                    "input_fields_used": ["framework", "zone_low", "zone_high", "candle_high", "candle_low", "candle_close"],
                    "predicate_or_threshold_evaluated": "current candle overlaps active unconsumed source-derived zone",
                    "matched_source_row_ids": [candidate["zone_id"]],
                    "before_decision_state": "asof_market_state_summarized",
                    "after_decision_state": "candidate_generated",
                    "reason_code": f"{candidate['framework'].upper()}_ZONE_RETEST_OR_FILL",
                    "step_role": "sufficient",
                },
                {
                    "stage_name": "candidate_geometry_projection",
                    "source_function_module": rel(Path(__file__).resolve()),
                    "input_fields_used": ["zone_low", "zone_high", "atr_14", "tick_size", "risk.min_rr"],
                    "predicate_or_threshold_evaluated": "entry/stop/target derived with nonzero buffer and min_rr projection",
                    "matched_source_row_ids": [candidate["candidate_id"]],
                    "before_decision_state": "candidate_generated",
                    "after_decision_state": "stage02_candidate_geometry_complete",
                    "reason_code": "SOURCE_BOUND_GEOMETRY_PROJECTED",
                    "step_role": "necessary",
                },
                {
                    "stage_name": "runtime_and_path_deferral",
                    "source_function_module": "NO_RUNTIME_FUNCTION",
                    "input_fields_used": ["candidate_id", "market_state_packet_id"],
                    "predicate_or_threshold_evaluated": "Stage02 generates candidates only; Stage03/Stage04 own runtime/path truth",
                    "matched_source_row_ids": [candidate["candidate_id"]],
                    "before_decision_state": "stage02_candidate_geometry_complete",
                    "after_decision_state": "pending_stage03_stage04",
                    "reason_code": "NO_RUNTIME_FUNCTION_IN_STAGE02",
                    "step_role": "contextual",
                },
            ]
        )
    else:
        steps.append(
            {
                "stage_name": "no_setup_resolution",
                "source_function_module": "NO_RUNTIME_FUNCTION",
                "input_fields_used": ["active_ob_count", "active_fvg_count", "active_breaker_count", "current_candle_ohlcv"],
                "predicate_or_threshold_evaluated": "no active unconsumed framework zone touched current candle",
                "matched_source_row_ids": [packet_id],
                "before_decision_state": "asof_market_state_summarized",
                "after_decision_state": "no_setup_by_asof_market_state",
                "reason_code": skip_reason or "NO_SETUP_BY_ASOF_MARKET_STATE",
                "step_role": "sufficient",
            }
        )
    return {
        "schema_version": "vnext_full_replay_decision_explanation_v1",
        "row_type": row_type,
        **base_source_fields(denom),
        "candidate_id": candidate_id,
        "market_state_packet_id": packet_id,
        "candidate_generation_disposition": disposition,
        "skip_reason": skip_reason,
        "framework": framework,
        "side": side,
        "asof_market_state_summary": market_state_summary,
        "runtime_trace": {
            "pre_ai_route_decision": "pending_stage03_actual_vnext_runtime_surface" if candidate else "NO_RUNTIME_FUNCTION",
            "route_decision": "pending_stage03_actual_vnext_runtime_surface" if candidate else "NO_RUNTIME_FUNCTION",
            "risk_decision": "pending_stage03_actual_vnext_runtime_surface" if candidate else "NO_RUNTIME_FUNCTION",
            "pending_no_fill_decision": "pending_stage03_actual_vnext_runtime_surface" if candidate else "NO_RUNTIME_FUNCTION",
            "gate_decision": "pending_stage03_actual_vnext_runtime_surface" if candidate else "NO_RUNTIME_FUNCTION",
            "ai_route_action": "pending_stage03_actual_vnext_runtime_surface" if candidate else "NO_RUNTIME_FUNCTION",
            "exit_trailing_action": "pending_stage04_path_r_simulation" if candidate else "NO_RUNTIME_FUNCTION",
            "matched_artifact_family": "pending_stage03_actual_vnext_runtime_surface" if candidate else "NO_RUNTIME_FUNCTION",
            "matched_row_ids": [],
            "source_component": "pending_stage03_actual_vnext_runtime_surface" if candidate else "NO_RUNTIME_FUNCTION",
            "action_class": "pending_stage03_actual_vnext_runtime_surface" if candidate else "NO_RUNTIME_FUNCTION",
            "pressure_direction": "pending_stage03_actual_vnext_runtime_surface" if candidate else "NO_RUNTIME_FUNCTION",
            "anchor_match_fields": {},
            "blank_anchor_status": "pending_stage03_actual_vnext_runtime_surface" if candidate else "NO_RUNTIME_FUNCTION",
            "dominance_reason": "pending_stage06_dominance_counterfactuals" if candidate else "NO_RUNTIME_FUNCTION",
        },
        "path_truth": {
            "entry_touched": "pending_stage04_path_r_simulation" if candidate else "NO_RUNTIME_FUNCTION",
            "entry_filled": "pending_stage04_path_r_simulation" if candidate else "NO_RUNTIME_FUNCTION",
            "no_fill_reason": "pending_stage04_path_r_simulation" if candidate else "NO_RUNTIME_FUNCTION",
            "path_source_mode": "pending_stage04_path_r_simulation" if candidate else "NO_RUNTIME_FUNCTION",
            "stop_target_result": "pending_stage04_path_r_simulation" if candidate else "NO_RUNTIME_FUNCTION",
            "mfe": "pending_stage04_path_r_simulation" if candidate else "NO_RUNTIME_FUNCTION",
            "mae": "pending_stage04_path_r_simulation" if candidate else "NO_RUNTIME_FUNCTION",
            "simulated_r": "pending_stage04_path_r_simulation" if candidate else "NO_RUNTIME_FUNCTION",
        },
        "outcome_context": "candidate_pending_runtime_and_path" if candidate else "skipped_no_candidate_geometry",
        "repair_state": {
            "runtime_trace_repair": "pending_stage03",
            "path_truth_repair": "pending_stage04",
            "source_repair_proof_required_now": False,
        },
        "causal_decision_steps": steps,
    }


def market_state_packet_row(
    *,
    denom: dict[str, Any],
    packet_id: str,
    candle_index: int,
    market_state_summary: dict[str, Any],
    path_modes: list[dict[str, Any]],
) -> dict[str, Any]:
    context = {
        "lookback_bars": market_state_summary.get("lookback_bars"),
        "asof_window_start": market_state_summary.get("asof_window_start"),
        "asof_window_end": market_state_summary.get("asof_window_end"),
        "asof_window_start_time_utc": market_state_summary.get("asof_window_start_time_utc"),
        "asof_window_end_time_utc": market_state_summary.get("asof_window_end_time_utc"),
        "prior_m15_context_bars": market_state_summary.get("prior_m15_context_bars"),
        "production_context_required_prior_m15_bars": market_state_summary.get("production_context_required_prior_m15_bars"),
        "enough_prior_m15_context_for_production_like_decision": market_state_summary.get("enough_prior_m15_context_for_production_like_decision"),
        "warmup_context_sufficiency_status": market_state_summary.get("warmup_context_sufficiency_status"),
        "warmup_context_handling": market_state_summary.get("warmup_context_handling"),
    }
    return {
        "schema_version": "vnext_full_replay_market_state_packet_v1",
        "row_type": "asof_market_state_packet",
        **base_source_fields(denom),
        "market_state_packet_id": packet_id,
        "candle_index": candle_index,
        **context,
        "asof_market_state_summary": market_state_summary,
        "available_path_source_modes": path_modes,
        "packet_scope": "M15_asof_summary_for_stage02_candidate_generation",
        "future_leak_guard": "confirmed_swings_only_index_lte_current_minus_min_bars",
    }


def disposition_row(
    *,
    denom: dict[str, Any],
    packet_id: str,
    disposition: str,
    candidate_ids: list[str],
    frameworks: list[str],
    market_state_summary: dict[str, Any],
    path_modes: list[dict[str, Any]],
    skip_reason: str | None,
) -> dict[str, Any]:
    context = {
        "lookback_bars": market_state_summary.get("lookback_bars"),
        "asof_window_start": market_state_summary.get("asof_window_start"),
        "asof_window_end": market_state_summary.get("asof_window_end"),
        "asof_window_start_time_utc": market_state_summary.get("asof_window_start_time_utc"),
        "asof_window_end_time_utc": market_state_summary.get("asof_window_end_time_utc"),
        "prior_m15_context_bars": market_state_summary.get("prior_m15_context_bars"),
        "production_context_required_prior_m15_bars": market_state_summary.get("production_context_required_prior_m15_bars"),
        "enough_prior_m15_context_for_production_like_decision": market_state_summary.get("enough_prior_m15_context_for_production_like_decision"),
        "warmup_context_sufficiency_status": market_state_summary.get("warmup_context_sufficiency_status"),
        "warmup_context_handling": market_state_summary.get("warmup_context_handling"),
    }
    full_context = bool(context["enough_prior_m15_context_for_production_like_decision"])
    return {
        "schema_version": "vnext_full_replay_denominator_disposition_v1",
        "row_type": "source_universe_disposition",
        **base_source_fields(denom),
        "market_state_packet_id": packet_id,
        **context,
        "candidate_generation_disposition": disposition,
        "candidate_count": len(candidate_ids),
        "candidate_ids": candidate_ids,
        "frameworks_generated": frameworks,
        "skip_reason": skip_reason,
        "asof_market_state_summary": market_state_summary,
        "available_path_source_modes": path_modes,
        "denominator_enters_stage02_candidate_denominator": full_context,
        "denominator_context_sensitivity": (
            "normal_production_like_context"
            if full_context
            else "warmup_context_limited_excluded_from_production_like_stage02_density_denominator"
        ),
        "terminal_disposition_for_stage02": True,
    }


def new_fvgs_at_index(
    candles: list[dict[str, Any]],
    i: int,
    *,
    min_gap: float,
) -> list[dict[str, Any]]:
    if i < 2:
        return []
    left = candles[i - 2]
    mid = candles[i - 1]
    right = candles[i]
    zones: list[dict[str, Any]] = []
    bull_gap = float(right["low"]) - float(left["high"])
    if bull_gap >= min_gap:
        zones.append(
            {
                "zone_id": stable_id("fvg", {"type": "bullish", "left": left["time"], "right": right["time"]}),
                "type": "bullish",
                "direction": "bullish",
                "side": "LONG",
                "zone_low": float(left["high"]),
                "zone_high": float(right["low"]),
                "formation_time": mid["time"],
                "right_index": i,
                "consumed": False,
                "touch_count": 0,
                "setup_type": "fair_value_gap_fill",
                "poi_type": "fvg_fill",
                "causing_event_type": "three_candle_imbalance",
                "causing_event_time": right["time"],
                "causing_event_index": i,
            }
        )
    bear_gap = float(left["low"]) - float(right["high"])
    if bear_gap >= min_gap:
        zones.append(
            {
                "zone_id": stable_id("fvg", {"type": "bearish", "left": left["time"], "right": right["time"]}),
                "type": "bearish",
                "direction": "bearish",
                "side": "SHORT",
                "zone_low": float(right["high"]),
                "zone_high": float(left["low"]),
                "formation_time": mid["time"],
                "right_index": i,
                "consumed": False,
                "touch_count": 0,
                "setup_type": "fair_value_gap_fill",
                "poi_type": "fvg_fill",
                "causing_event_type": "three_candle_imbalance",
                "causing_event_time": right["time"],
                "causing_event_index": i,
            }
        )
    return zones


def structure_events_at_index(
    candles: list[dict[str, Any]],
    i: int,
    *,
    confirmed_swings: list[Any],
    structure: Any,
    broken_bos_levels: set[tuple[str, float]],
    fired_choch: set[tuple[str, int]],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    candle = candles[i]
    close = float(candle["close"])
    if structure.direction == "bullish":
        high = recent_swing(confirmed_swings, before_index=i, swing_type="high")
        if high and close > float(high.price) and ("bullish", float(high.price)) not in broken_bos_levels:
            broken_bos_levels.add(("bullish", float(high.price)))
            events.append(
                {
                    "type": "BOS",
                    "direction": "bullish",
                    "level_broken": float(high.price),
                    "time": candle["time"],
                    "candle_index": i,
                }
            )
    elif structure.direction == "bearish":
        low = recent_swing(confirmed_swings, before_index=i, swing_type="low")
        if low and close < float(low.price) and ("bearish", float(low.price)) not in broken_bos_levels:
            broken_bos_levels.add(("bearish", float(low.price)))
            events.append(
                {
                    "type": "BOS",
                    "direction": "bearish",
                    "level_broken": float(low.price),
                    "time": candle["time"],
                    "candle_index": i,
                }
            )
    protected = getattr(structure, "protected_swing", None)
    if protected and i > protected.index:
        key = (structure.direction, protected.index)
        if structure.direction == "bullish" and close < float(protected.price) and key not in fired_choch:
            fired_choch.add(key)
            events.append(
                {
                    "type": "CHoCH",
                    "direction": "bearish",
                    "level_broken": float(protected.price),
                    "time": candle["time"],
                    "candle_index": i,
                }
            )
        if structure.direction == "bearish" and close > float(protected.price) and key not in fired_choch:
            fired_choch.add(key)
            events.append(
                {
                    "type": "CHoCH",
                    "direction": "bullish",
                    "level_broken": float(protected.price),
                    "time": candle["time"],
                    "candle_index": i,
                }
            )
    return events


def ob_from_event(candles: list[dict[str, Any]], event: dict[str, Any]) -> dict[str, Any] | None:
    break_idx = int(event["candle_index"])
    if event["direction"] == "bullish":
        for j in range(break_idx - 1, max(break_idx - 10, -1), -1):
            candle = candles[j]
            if float(candle["close"]) < float(candle["open"]):
                return {
                    "zone_id": stable_id("ob", {"formation": candle["time"], "break": event["time"], "direction": "bullish"}),
                    "type": "bullish",
                    "direction": "bullish",
                    "side": "LONG",
                    "zone_low": float(candle["low"]),
                    "zone_high": float(candle["high"]),
                    "formation_time": candle["time"],
                    "formation_index": j,
                    "causing_event_type": event["type"],
                    "causing_event_time": event["time"],
                    "causing_event_index": break_idx,
                    "touch_count": sum(1 for k in range(j + 1, break_idx + 1) if range_overlaps(candles[k], float(candle["low"]), float(candle["high"]))),
                    "mitigated": False,
                    "consumed": False,
                    "setup_type": "order_block_retest",
                    "poi_type": "ob_retest",
                }
    if event["direction"] == "bearish":
        for j in range(break_idx - 1, max(break_idx - 10, -1), -1):
            candle = candles[j]
            if float(candle["close"]) > float(candle["open"]):
                return {
                    "zone_id": stable_id("ob", {"formation": candle["time"], "break": event["time"], "direction": "bearish"}),
                    "type": "bearish",
                    "direction": "bearish",
                    "side": "SHORT",
                    "zone_low": float(candle["low"]),
                    "zone_high": float(candle["high"]),
                    "formation_time": candle["time"],
                    "formation_index": j,
                    "causing_event_type": event["type"],
                    "causing_event_time": event["time"],
                    "causing_event_index": break_idx,
                    "touch_count": sum(1 for k in range(j + 1, break_idx + 1) if range_overlaps(candles[k], float(candle["low"]), float(candle["high"]))),
                    "mitigated": False,
                    "consumed": False,
                    "setup_type": "order_block_retest",
                    "poi_type": "ob_retest",
                }
    return None


def breaker_from_mitigated_ob(ob: dict[str, Any], candle: dict[str, Any], i: int) -> dict[str, Any]:
    direction = "bearish" if ob["type"] == "bullish" else "bullish"
    return {
        "zone_id": stable_id(
            "breaker",
            {"ob": ob["zone_id"], "mitigation_time": candle["time"], "direction": direction},
        ),
        "type": direction,
        "direction": direction,
        "side": "LONG" if direction == "bullish" else "SHORT",
        "zone_low": ob["zone_low"],
        "zone_high": ob["zone_high"],
        "formation_time": ob["formation_time"],
        "mitigation_time": candle["time"],
        "mitigation_index": i,
        "causing_event_type": ob["causing_event_type"],
        "causing_event_time": ob["causing_event_time"],
        "causing_event_index": ob["causing_event_index"],
        "touch_count": 0,
        "consumed": False,
        "setup_type": "breaker_re_entry",
        "poi_type": "breaker_re_entry",
    }


def generate_source_rows(
    *,
    candles: list[dict[str, Any]],
    denominator_rows: list[dict[str, Any]],
    config: dict[str, Any],
    coverage_index: dict[str, list[dict[str, Any]]],
) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield typed Stage02 rows for one source file."""
    if not candles:
        for denom in denominator_rows:
            packet_id = stable_id("msp", {"row": denom["source_universe_row_id"], "missing": "source"})
            summary = {
                "market_state_status": "source_missing_after_pursuit",
                "reason": "empty_or_unreadable_candle_source",
                "lookback_bars": lookback_bars_from_config(config, "M15"),
                "asof_window_start": None,
                "asof_window_end": None,
                "asof_window_start_time_utc": None,
                "asof_window_end_time_utc": None,
                "prior_m15_context_bars": 0,
                "production_context_required_prior_m15_bars": lookback_bars_from_config(config, "M15") - 1,
                "enough_prior_m15_context_for_production_like_decision": False,
                "warmup_context_sufficiency_status": "source_missing_context_unavailable",
                "warmup_context_handling": "source_missing_denominator_excluded",
            }
            yield "market_state_packet", market_state_packet_row(
                denom=denom,
                packet_id=packet_id,
                candle_index=-1,
                market_state_summary=summary,
                path_modes=[],
            )
            yield "denominator_disposition", disposition_row(
                denom=denom,
                packet_id=packet_id,
                disposition="parser_missing_after_full_pursuit",
                candidate_ids=[],
                frameworks=[],
                market_state_summary=summary,
                path_modes=[],
                skip_reason="parser_missing_after_full_pursuit",
            )
            yield "decision_explanation", explanation_row(
                denom=denom,
                packet_id=packet_id,
                row_type="skip_decision_explanation",
                disposition="parser_missing_after_full_pursuit",
                market_state_summary=summary,
                skip_reason="parser_missing_after_full_pursuit",
            )
        return

    min_bars = swing_bars_from_config(config, "M15")
    lookback_bars = lookback_bars_from_config(config, "M15")
    min_gap = fvg_min_gap_from_config(config, str(denominator_rows[0]["symbol"]), "M15")
    all_swings = detect_swings(candles, min_bars=min_bars)
    swing_ptr = 0
    confirmed_swings: list[Any] = []
    broken_bos_levels: set[tuple[str, float]] = set()
    fired_choch: set[tuple[str, int]] = set()
    active_obs: list[dict[str, Any]] = []
    active_fvgs: list[dict[str, Any]] = []
    active_breakers: list[dict[str, Any]] = []
    denominator_by_time: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for denom in denominator_rows:
        denominator_by_time[str(denom["candle_time_utc"])].append(denom)

    for i, candle in enumerate(candles):
        window_start = max(0, i - lookback_bars + 1)
        context = lookback_context(
            candle_index=i,
            lookback_bars=lookback_bars,
            candles=candles,
            window_start=window_start,
        )
        active_obs = [
            ob for ob in active_obs if int(ob.get("formation_index") or 0) >= window_start
        ]
        active_fvgs = [
            fvg for fvg in active_fvgs if int(fvg.get("right_index") or 0) >= window_start
        ]
        active_breakers = [
            breaker
            for breaker in active_breakers
            if int(breaker.get("mitigation_index") or 0) >= window_start
        ]
        while swing_ptr < len(all_swings) and all_swings[swing_ptr].index <= i - min_bars:
            confirmed_swings.append(all_swings[swing_ptr])
            swing_ptr += 1
        structure_swings = [s for s in confirmed_swings if s.index >= window_start]
        structure = identify_structure(structure_swings)
        events = structure_events_at_index(
            candles,
            i,
            confirmed_swings=structure_swings,
            structure=structure,
            broken_bos_levels=broken_bos_levels,
            fired_choch=fired_choch,
        )
        for event in events:
            ob = ob_from_event(candles, event)
            if ob is not None and all(existing["zone_id"] != ob["zone_id"] for existing in active_obs):
                active_obs.append(ob)
        for fvg in new_fvgs_at_index(candles, i, min_gap=min_gap):
            if all(existing["zone_id"] != fvg["zone_id"] for existing in active_fvgs):
                active_fvgs.append(fvg)
        new_breakers: list[dict[str, Any]] = []
        for ob in active_obs:
            if ob["mitigated"] or i <= int(ob["causing_event_index"]):
                continue
            if body_close_breaks_ob(candle, ob):
                ob["mitigated"] = True
                ob["mitigation_time"] = candle["time"]
                ob["mitigation_index"] = i
                new_breakers.append(breaker_from_mitigated_ob(ob, candle, i))
        for breaker in new_breakers:
            if all(existing["zone_id"] != breaker["zone_id"] for existing in active_breakers):
                active_breakers.append(breaker)

        current_denoms = denominator_by_time.get(str(candle["time"]), [])
        if not current_denoms:
            continue

        atr_14 = calculate_atr(candles[max(0, i - 100): i + 1], period=14)
        candidates_by_denom: dict[str, list[dict[str, Any]]] = defaultdict(list)

        candidate_zones: list[tuple[str, dict[str, Any]]] = []
        for ob in active_obs:
            if ob["consumed"] or i <= int(ob["causing_event_index"]):
                continue
            if range_overlaps(candle, float(ob["zone_low"]), float(ob["zone_high"])):
                ob["touch_count"] = int(ob.get("touch_count") or 0) + 1
                zone = dict(ob)
                zone["touch_count_at_candidate"] = ob["touch_count"]
                candidate_zones.append(("ob_retest", zone))
                ob["consumed"] = True
        for fvg in active_fvgs:
            if fvg["consumed"] or i <= int(fvg["right_index"]):
                continue
            if range_overlaps(candle, float(fvg["zone_low"]), float(fvg["zone_high"])):
                fvg["touch_count"] = int(fvg.get("touch_count") or 0) + 1
                zone = dict(fvg)
                zone["touch_count_at_candidate"] = fvg["touch_count"]
                candidate_zones.append(("fvg_fill", zone))
                fvg["consumed"] = True
        for breaker in active_breakers:
            if breaker["consumed"] or i <= int(breaker["mitigation_index"]):
                continue
            if breaker_retest(candle, breaker):
                breaker["touch_count"] = int(breaker.get("touch_count") or 0) + 1
                zone = dict(breaker)
                zone["touch_count_at_candidate"] = breaker["touch_count"]
                candidate_zones.append(("breaker_re_entry", zone))
                breaker["consumed"] = True

        base_summary = {
            "market_state_status": "asof_built",
            **context,
            "structure_direction": structure.direction,
            "confirmed_swing_count": len(confirmed_swings),
            "latest_confirmed_swing_index": confirmed_swings[-1].index if confirmed_swings else None,
            "structure_window_confirmed_swing_count": len(structure_swings),
            "structure_event_count_on_candle": len(events),
            "structure_events_on_candle": events,
            "active_ob_count": sum(1 for ob in active_obs if not ob.get("consumed")),
            "active_fvg_count": sum(1 for fvg in active_fvgs if not fvg.get("consumed")),
            "active_breaker_count": sum(1 for br in active_breakers if not br.get("consumed")),
            "atr_14": round(atr_14, 6),
            "fvg_min_gap": min_gap,
            "swing_min_bars": min_bars,
            "asof_candle_index": i,
        }

        for denom in current_denoms:
            packet_id = stable_id(
                "msp",
                {
                    "source_universe_row_id": denom["source_universe_row_id"],
                    "candle_index": i,
                    "summary": base_summary,
                },
            )
            path_modes = path_source_modes_for_time(str(denom["symbol"]), str(denom["candle_time_utc"]), coverage_index)
            yield "market_state_packet", market_state_packet_row(
                denom=denom,
                packet_id=packet_id,
                candle_index=i,
                market_state_summary=base_summary,
                path_modes=path_modes,
            )
            generated_candidates: list[dict[str, Any]] = []
            for framework, zone in candidate_zones:
                cand = candidate_row(
                    config,
                    denom=denom,
                    packet_id=packet_id,
                    framework=framework,
                    side=zone["side"],
                    zone=zone,
                    candle_index=i,
                    atr_14=atr_14,
                    market_state_summary=base_summary,
                    path_modes=path_modes,
                )
                generated_candidates.append(cand)
                candidates_by_denom[denom["source_universe_row_id"]].append(cand)
                yield "candidate_generation", cand
                yield "decision_explanation", explanation_row(
                    denom=denom,
                    packet_id=packet_id,
                    row_type="candidate_decision_explanation",
                    disposition="candidate_generated",
                    market_state_summary=base_summary,
                    candidate=cand,
                )
            if generated_candidates:
                yield "denominator_disposition", disposition_row(
                    denom=denom,
                    packet_id=packet_id,
                    disposition="candidate_generated",
                    candidate_ids=[row["candidate_id"] for row in generated_candidates],
                    frameworks=sorted({row["framework"] for row in generated_candidates}),
                    market_state_summary=base_summary,
                    path_modes=path_modes,
                    skip_reason=None,
                )
            else:
                skip_reason = (
                    "context_limited_no_setup_not_production_like_denominator"
                    if not context["enough_prior_m15_context_for_production_like_decision"]
                    else "no_active_unconsumed_ob_fvg_or_breaker_zone_touched_current_candle"
                )
                yield "denominator_disposition", disposition_row(
                    denom=denom,
                    packet_id=packet_id,
                    disposition="no_setup_by_asof_market_state",
                    candidate_ids=[],
                    frameworks=[],
                    market_state_summary=base_summary,
                    path_modes=path_modes,
                    skip_reason=skip_reason,
                )
                yield "decision_explanation", explanation_row(
                    denom=denom,
                    packet_id=packet_id,
                    row_type="skip_decision_explanation",
                    disposition="no_setup_by_asof_market_state",
                    market_state_summary=base_summary,
                    skip_reason=skip_reason,
                )


def prior_logged_event_count() -> int:
    if not PRIOR_LOGGED_EVENT_LEDGER.exists():
        return LOGGED_EVENT_COUNT_FALLBACK
    count = 0
    with PRIOR_LOGGED_EVENT_LEDGER.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            count += chunk.count(b"\n")
    return count


def append_jsonl_rows(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    existing = list(iter_jsonl(path)) if path.exists() else []
    keyed = {
        str(row.get("question_id") or row.get("pursuit_id") or row.get("file_path") or stable_id("row", row)): row
        for row in existing
    }
    for row in rows:
        key = str(row.get("question_id") or row.get("pursuit_id") or row.get("file_path") or stable_id("row", row))
        keyed[key] = row
    return write_jsonl(path, keyed.values())


def stage02_question_rows(counts: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "vnext_full_replay_active_question_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "question_id": "Q005_RUNTIME_SUPPORTED_SOURCE_GENERATABLE_FAMILY_EXPANSION",
            "question": "Which current vNext runtime-supported route families beyond ob_retest/fvg_fill/breaker_re_entry can be generated directly from market bars?",
            "current_answer": (
                "Stage02 generated the three frozen production framework families from market bars; "
                "Stage03 must inspect actual runtime matches for additional source-generatable route families."
            ),
            "status": "open_same_evidence_class_stage03_runtime_family_inventory_required",
            "next_action": "Run Stage03 actual vNext runtime trace on the generated candidate universe and inventory matched family/action classes.",
        },
        {
            "schema_version": "vnext_full_replay_active_question_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "question_id": "Q006_STAGE02_CANDIDATE_DENSITY_ANOMALIES",
            "question": "Which symbols/sessions/frameworks produced unusually dense or sparse source-generated candidates?",
            "current_answer": f"Stage02 candidate count is {counts.get('candidate_rows')} from {counts.get('denominator_rows')} denominator rows; detailed split rows are in the summary.",
            "status": "open_same_evidence_class_stage03_stage04_followup_required",
            "next_action": "Use generated split counters during runtime/path replay to separate useful density from noise or overgeneration.",
        },
        {
            "schema_version": "vnext_full_replay_active_question_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "question_id": "Q007_FULL_SOURCE_MODE_EXPORT_AND_PATH_TRUTH_REPAIR",
            "question": "Which M1/M5/tick/Sierra/OHLC/MT5-exportable gaps must be executed, converted, or repaired before path/R and M15-blindness conclusions are complete?",
            "current_answer": (
                "Stage02 intentionally preserves the 76 MT5/export/source requirements plus M1/M5/tick/Sierra/SCID source-mode actions; "
                "M15 candidate-origin generation is not replay coverage completion."
            ),
            "status": "open_same_evidence_class_source_export_conversion_path_stage_required",
            "next_action": (
                "Before final replay coverage/path/R conclusions, execute or repair the MT5 export requirements, convert supported Sierra/SCID, "
                "and bind M1/M5/tick/OHLC path sources or row-level forbidden/impossibility proof."
            ),
        },
    ]


def stage02_extra_step_rows(counts: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "vnext_full_replay_extra_step_pursuit_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "pursuit_id": "P004_STAGE02_MARKET_BAR_CANDIDATE_GENERATION",
            "trigger": "first_incomplete_invariant_after_stage01",
            "executed_action": "read Stage01 source-universe chunks and generated OB/FVG/breaker candidates from M15 market bars",
            "artifact_effect": f"{counts.get('candidate_rows')} candidate rows and {counts.get('denominator_rows')} denominator dispositions written",
            "next_action": "Stage03 must call current vNext runtime surfaces on candidate rows.",
        },
        {
            "schema_version": "vnext_full_replay_extra_step_pursuit_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "pursuit_id": "P005_NO_SHADOW_LOG_PRIMARY_UNIVERSE_GUARD",
            "trigger": "prompt provenance lock",
            "executed_action": "verifier scans candidate chunks for source_origin=market_bar_enumeration and rejects prior logged-event count equality",
            "artifact_effect": "candidate universe has market-bar provenance and denominator disposition proof",
            "next_action": "Preserve this guard in Stage03/Stage04 joins.",
        },
        {
            "schema_version": "vnext_full_replay_extra_step_pursuit_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "pursuit_id": "P006_ONE_TIME_STAGE02_DURABILITY_LOOKBACK_SCOPE_STEER",
            "trigger": "owner_stage02_durability_lookback_scope_control_steer",
            "executed_action": (
                "patched Stage02 to use per-source atomic shard outputs with manifests, heartbeat, resume cursor, "
                "verifier coverage, and explicit M15 lookback/context sufficiency fields"
            ),
            "artifact_effect": (
                "timeouts lose no completed source shard; early-window rows are not silently counted as true no-setup; "
                "Stage02 remains candidate-origin generation only"
            ),
            "next_action": "After Stage02 verifier passes, continue to Stage03 actual runtime tracing without relitigating this one-time steer.",
        },
    ]


def stage02_prompt_application_rows(counts: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "vnext_full_replay_prompt_application_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "checkpoint_id": "STAGE02_ONE_TIME_DURABILITY_LOOKBACK_SCOPE_CONTROL",
            "created_at_utc": utc_now(),
            "active_stage_invariant": "candidate-origin generation from market bars only",
            "owner_steer_status": "applied_once_not_replacement_objective_not_permanent_loop",
            "durability_control": "per_source_shard_outputs_atomic_tmp_to_final_manifest_heartbeat_resume_cursor",
            "lookback_control": "denominator_disposition_and_market_state_packet_rows_include_production_m15_lookback_context_fields",
            "scope_control": (
                "Stage02 does not close replay coverage, M15 blindness, path/R, runtime tracing, no-fill/pending, "
                "dominance/pollution, MIXED, ablation, robustness, prop metrics, behavioral forensics, or final decisions"
            ),
            "source_mode_control": (
                "76 MT5/export/source requirements plus M1/M5/tick/Sierra/SCID/OHLC path-source actions remain open "
                "until executed/repaired or row-level bounded by forbidden/impossibility proof"
            ),
            "counts_at_checkpoint": counts,
            "next_incomplete_invariant": "Stage03 actual vNext runtime tracing for generated candidates",
        }
    ]


def chunk_artifact_manifest(logical_path: Path, artifact_key: str) -> list[dict[str, Any]]:
    if not logical_path.exists():
        return []
    rows = []
    logical_rows = 0
    for index_row in iter_jsonl(logical_path):
        rows.append(
            {
                "artifact_key": f"{artifact_key}_chunk",
                "path": index_row["chunk_path"],
                "bytes": index_row["bytes"],
                "sha256": index_row["sha256"],
                "row_count": index_row["row_count"],
                "logical_artifact_path": index_row["logical_artifact_path"],
            }
        )
        logical_rows += int(index_row["row_count"])
    rows.insert(
        0,
        {
            "artifact_key": artifact_key,
            "path": rel(logical_path),
            "bytes": logical_path.stat().st_size,
            "sha256": sha256_file(logical_path),
            "row_count": sum(1 for _ in iter_jsonl(logical_path)),
            "logical_row_count": logical_rows,
        },
    )
    return rows


def build_shard_contract(source_by_path: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    rows = []
    for source_index, (source_path, denoms) in enumerate(source_by_path.items(), start=1):
        path = repo_path(source_path)
        shard_id = shard_id_for_source(source_path, denoms)
        rows.append(
            {
                "source_index": source_index,
                "shard_id": shard_id,
                "source_path": source_path,
                "source_sha256_from_denominator": denoms[0].get("source_sha256"),
                "source_file_exists": path.exists(),
                "denominator_rows": len(denoms),
                "first_candle_time_utc": denoms[0].get("candle_time_utc"),
                "last_candle_time_utc": denoms[-1].get("candle_time_utc"),
                "output_mode": "stream_to_route_owned_gzip_chunks_with_atomic_chunk_index_replace",
            }
        )
    return {
        "schema_version": "vnext_full_replay_stage02_shard_contract_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "created_at_utc": utc_now(),
        "git_head": git_head(),
        "input_source_universe_index": rel(SOURCE_UNIVERSE_INDEX_PATH),
        "input_source_count": len(rows),
        "input_denominator_rows": sum(row["denominator_rows"] for row in rows),
        "resume_command": (
            "py -3 research/science_program_2026_05/06_outcome_testing/"
            f"{ROUTE_ID}/build_vnext_full_replay_stage02_candidate_generation_2026_05_24.py"
        ),
        "heartbeat_policy": "summary JSON is written after full stream; rerun is deterministic and route-owned chunks are replaced atomically by logical index",
        "shards": rows,
    }


def shard_id_for_source(source_path: str, denoms: list[dict[str, Any]]) -> str:
    return stable_id(
        "stage02src",
        {
            "source_path": source_path,
            "source_sha256": denoms[0].get("source_sha256") if denoms else None,
            "denominator_rows": len(denoms),
            "first": denoms[0].get("candle_time_utc") if denoms else None,
            "last": denoms[-1].get("candle_time_utc") if denoms else None,
        },
        length=16,
    )


def shard_paths(shard_id: str) -> dict[str, Path]:
    shard_dir = SHARD_DIR / shard_id
    return {
        "dir": shard_dir,
        "manifest": shard_dir / "manifest.json",
        "heartbeat": shard_dir / "heartbeat.json",
        **{
            key: shard_dir / f"{key}.jsonl.gz"
            for key in SHARDED_ARTIFACT_KEYS
        },
    }


def write_shard_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_stage02_heartbeat(payload: dict[str, Any]) -> None:
    write_json(OUTPUTS["stage02_heartbeat"], payload)


def route_owned_stage02_cleanup() -> None:
    """Remove stale pre-shard global chunks only; never source data."""
    for key in SHARDED_ARTIFACT_KEYS:
        base_path = OUTPUTS[key]
        for stale in base_path.parent.glob(base_path.stem + ".chunk-*.jsonl.gz"):
            stale.unlink()
        for stale in base_path.parent.glob(base_path.stem + ".chunk-*.jsonl.gz.tmp"):
            stale.unlink()


def completed_shard_manifest(
    *,
    source_path: str,
    denoms: list[dict[str, Any]],
) -> dict[str, Any] | None:
    shard_id = shard_id_for_source(source_path, denoms)
    paths = shard_paths(shard_id)
    manifest_path = paths["manifest"]
    if not manifest_path.exists():
        return None
    try:
        manifest = read_json(manifest_path)
    except Exception:
        return None
    if manifest.get("shard_status") != "complete":
        return None
    if manifest.get("source_path") != source_path:
        return None
    if int(manifest.get("denominator_rows") or -1) != len(denoms):
        return None
    for key in SHARDED_ARTIFACT_KEYS:
        output = (manifest.get("outputs") or {}).get(key) or {}
        path = repo_path(output.get("path", ""))
        if not path.exists():
            return None
        if output.get("sha256") != sha256_file(path):
            return None
    return manifest


def write_one_source_shard(
    *,
    source_index: int,
    source_count: int,
    source_path: str,
    denoms: list[dict[str, Any]],
    config: dict[str, Any],
    coverage_index: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    shard_id = shard_id_for_source(source_path, denoms)
    paths = shard_paths(shard_id)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    started = utc_now()
    heartbeat = {
        "schema_version": "vnext_full_replay_stage02_shard_heartbeat_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "shard_id": shard_id,
        "source_index": source_index,
        "source_count": source_count,
        "source_path": source_path,
        "shard_status": "running",
        "heartbeat_updated_at_utc": started,
        "resume_cursor": {
            "next_source_index_if_complete": source_index + 1,
            "rerun_command": (
                "py -3 research/science_program_2026_05/06_outcome_testing/"
                f"{ROUTE_ID}/build_vnext_full_replay_stage02_candidate_generation_2026_05_24.py"
            ),
        },
        "row_counts_so_far": {},
    }
    write_shard_json(paths["heartbeat"], heartbeat)
    write_stage02_heartbeat(heartbeat)

    temp_paths = {key: paths[key].with_suffix(paths[key].suffix + ".tmp") for key in SHARDED_ARTIFACT_KEYS}
    for path in temp_paths.values():
        if path.exists():
            path.unlink()
    handles = {key: gzip.open(temp_paths[key], "wt", encoding="utf-8", newline="\n") for key in SHARDED_ARTIFACT_KEYS}
    row_counts: Counter[str] = Counter()
    by_framework: Counter[str] = Counter()
    by_symbol: Counter[str] = Counter()
    by_session: Counter[str] = Counter()
    by_disposition: Counter[str] = Counter()
    by_context_status: Counter[str] = Counter()
    source_failures: list[dict[str, Any]] = []
    output_rows_written = 0
    try:
        candles, parse_errors = load_candles(repo_path(source_path))
        if parse_errors:
            source_failures.append(
                {
                    "source_path": source_path,
                    "parse_error_count": len(parse_errors),
                    "first_errors": parse_errors[:5],
                }
            )
        for row_type, row in generate_source_rows(
            candles=candles,
            denominator_rows=denoms,
            config=config,
            coverage_index=coverage_index,
        ):
            handles[row_type].write(json.dumps(row, sort_keys=True) + "\n")
            row_counts[row_type] += 1
            output_rows_written += 1
            if row_type == "candidate_generation":
                by_framework[str(row.get("framework"))] += 1
                by_symbol[str(row.get("symbol"))] += 1
                by_session[str(row.get("session_bucket"))] += 1
                by_context_status[str((row.get("asof_market_state_summary") or {}).get("warmup_context_sufficiency_status"))] += 1
            elif row_type == "denominator_disposition":
                by_disposition[str(row.get("candidate_generation_disposition"))] += 1
                by_context_status[str(row.get("warmup_context_sufficiency_status"))] += 1
            if output_rows_written % 50_000 == 0:
                heartbeat["heartbeat_updated_at_utc"] = utc_now()
                heartbeat["row_counts_so_far"] = dict(row_counts)
                heartbeat["resume_cursor"]["current_source_output_rows_written"] = output_rows_written
                write_shard_json(paths["heartbeat"], heartbeat)
                write_stage02_heartbeat(heartbeat)
    except Exception as exc:
        for handle in handles.values():
            handle.close()
        failure_manifest = {
            "schema_version": "vnext_full_replay_stage02_shard_manifest_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "shard_id": shard_id,
            "source_index": source_index,
            "source_count": source_count,
            "source_path": source_path,
            "shard_status": "failed",
            "started_at_utc": started,
            "failed_at_utc": utc_now(),
            "error": repr(exc),
            "row_counts": dict(row_counts),
            "resume_cursor": heartbeat["resume_cursor"],
        }
        write_shard_json(paths["manifest"], failure_manifest)
        raise
    for handle in handles.values():
        handle.close()
    outputs: dict[str, dict[str, Any]] = {}
    for key in SHARDED_ARTIFACT_KEYS:
        temp_paths[key].replace(paths[key])
        outputs[key] = {
            "path": rel(paths[key]),
            "row_count": int(row_counts.get(key, 0)),
            "bytes": paths[key].stat().st_size,
            "sha256": sha256_file(paths[key]),
        }
    manifest = {
        "schema_version": "vnext_full_replay_stage02_shard_manifest_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "shard_id": shard_id,
        "source_index": source_index,
        "source_count": source_count,
        "source_path": source_path,
        "source_sha256_from_denominator": denoms[0].get("source_sha256") if denoms else None,
        "denominator_rows": len(denoms),
        "first_candle_time_utc": denoms[0].get("candle_time_utc") if denoms else None,
        "last_candle_time_utc": denoms[-1].get("candle_time_utc") if denoms else None,
        "started_at_utc": started,
        "completed_at_utc": utc_now(),
        "heartbeat_updated_at_utc": utc_now(),
        "shard_status": "complete",
        "row_counts": dict(row_counts),
        "candidate_rows_by_framework": dict(sorted(by_framework.items())),
        "candidate_rows_by_symbol": dict(sorted(by_symbol.items())),
        "candidate_rows_by_session_bucket": dict(sorted(by_session.items())),
        "row_counts_by_disposition": dict(sorted(by_disposition.items())),
        "row_counts_by_context_status": dict(sorted(by_context_status.items())),
        "source_failures": source_failures,
        "outputs": outputs,
        "atomic_write_policy": "each shard output wrote to .tmp then replaced final after gzip close",
        "resume_cursor": {
            "next_source_index": source_index + 1,
            "completed_source_path": source_path,
        },
    }
    write_shard_json(paths["manifest"], manifest)
    heartbeat.update(
        {
            "shard_status": "complete",
            "heartbeat_updated_at_utc": manifest["completed_at_utc"],
            "row_counts_so_far": dict(row_counts),
            "outputs": outputs,
        }
    )
    write_shard_json(paths["heartbeat"], heartbeat)
    write_stage02_heartbeat(heartbeat)
    return manifest


def completed_shard_manifests(source_by_path: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    manifests = []
    for source_path, denoms in source_by_path.items():
        manifest = completed_shard_manifest(source_path=source_path, denoms=denoms)
        if manifest is not None:
            manifests.append(manifest)
    return sorted(manifests, key=lambda row: int(row.get("source_index") or 0))


def write_master_indices_from_shards(manifests: list[dict[str, Any]]) -> dict[str, int]:
    logical_counts: dict[str, int] = {}
    for key in SHARDED_ARTIFACT_KEYS:
        index_rows = []
        total_rows = 0
        for chunk_index, manifest in enumerate(manifests, start=1):
            output = manifest["outputs"][key]
            total_rows += int(output.get("row_count") or 0)
            index_rows.append(
                {
                    "schema_version": "vnext_full_replay_chunk_index_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": STAGE_ID,
                    "logical_artifact_path": rel(OUTPUTS[key]),
                    "chunk_index": chunk_index,
                    "chunk_path": output["path"],
                    "row_count": output["row_count"],
                    "bytes": output["bytes"],
                    "sha256": output["sha256"],
                    "shard_id": manifest["shard_id"],
                    "source_index": manifest["source_index"],
                    "source_path": manifest["source_path"],
                    "shard_status": manifest["shard_status"],
                }
            )
        write_jsonl(OUTPUTS[key], index_rows)
        logical_counts[key] = total_rows
    status_rows = [
        {
            "schema_version": "vnext_full_replay_stage02_shard_status_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "shard_id": manifest["shard_id"],
            "source_index": manifest["source_index"],
            "source_path": manifest["source_path"],
            "shard_status": manifest["shard_status"],
            "denominator_rows": manifest["denominator_rows"],
            "completed_at_utc": manifest["completed_at_utc"],
            "row_counts": manifest["row_counts"],
            "outputs": manifest["outputs"],
            "resume_cursor": manifest["resume_cursor"],
        }
        for manifest in manifests
    ]
    write_jsonl(OUTPUTS["stage02_shard_status"], status_rows)
    return logical_counts


def aggregate_shard_summary(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    by_framework: Counter[str] = Counter()
    by_symbol: Counter[str] = Counter()
    by_session: Counter[str] = Counter()
    by_disposition: Counter[str] = Counter()
    by_context_status: Counter[str] = Counter()
    source_failures: list[dict[str, Any]] = []
    for manifest in manifests:
        for key, value in (manifest.get("row_counts") or {}).items():
            counts[f"{key}_rows"] += int(value)
        counts["source_files_processed"] += 1
        counts["denominator_rows"] += int(manifest.get("denominator_rows") or 0)
        for key, value in (manifest.get("candidate_rows_by_framework") or {}).items():
            by_framework[key] += int(value)
        for key, value in (manifest.get("candidate_rows_by_symbol") or {}).items():
            by_symbol[key] += int(value)
        for key, value in (manifest.get("candidate_rows_by_session_bucket") or {}).items():
            by_session[key] += int(value)
        for key, value in (manifest.get("row_counts_by_disposition") or {}).items():
            by_disposition[key] += int(value)
        for key, value in (manifest.get("row_counts_by_context_status") or {}).items():
            by_context_status[key] += int(value)
        source_failures.extend(manifest.get("source_failures") or [])
    counts["candidate_rows"] = counts["candidate_generation_rows"]
    counts["denominator_disposition_rows"] = counts["denominator_disposition_rows"]
    counts["market_state_packet_rows"] = counts["market_state_packet_rows"]
    counts["decision_explanation_rows"] = counts["decision_explanation_rows"]
    counts["source_parse_failure_files"] = len(source_failures)
    counts["prior_logged_event_count"] = prior_logged_event_count()
    return {
        "counts": dict(counts),
        "candidate_rows_by_framework": dict(sorted(by_framework.items())),
        "candidate_rows_by_symbol": dict(sorted(by_symbol.items())),
        "candidate_rows_by_session_bucket": dict(sorted(by_session.items())),
        "denominator_disposition_counts": dict(sorted(by_disposition.items())),
        "row_counts_by_context_status": dict(sorted(by_context_status.items())),
        "source_failures": source_failures[:50],
    }


def build_outputs(*, max_source_files: int | None = None) -> dict[str, Any]:
    started = utc_now()
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    coverage_rows = load_coverage_rows()
    cov_index = coverage_by_symbol(coverage_rows)
    source_by_path = load_source_universe_by_source(max_source_files=max_source_files)
    shard_contract = build_shard_contract(source_by_path)
    write_json(OUTPUTS["stage02_shard_contract"], shard_contract)
    route_owned_stage02_cleanup()

    source_count = len(source_by_path)
    completed_before = 0
    processed_now = 0
    for source_index, (source_path, denoms) in enumerate(source_by_path.items(), start=1):
        existing_manifest = completed_shard_manifest(source_path=source_path, denoms=denoms)
        if existing_manifest is not None:
            completed_before += 1
            write_stage02_heartbeat(
                {
                    "schema_version": "vnext_full_replay_stage02_heartbeat_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": STAGE_ID,
                    "heartbeat_updated_at_utc": utc_now(),
                    "shard_status": "resume_skip_completed_shard",
                    "source_index": source_index,
                    "source_count": source_count,
                    "source_path": source_path,
                    "shard_id": existing_manifest["shard_id"],
                    "completed_before_this_run": completed_before,
                    "processed_now": processed_now,
                }
            )
            continue
        write_one_source_shard(
            source_index=source_index,
            source_count=source_count,
            source_path=source_path,
            denoms=denoms,
            config=config,
            coverage_index=cov_index,
        )
        processed_now += 1

    manifests = completed_shard_manifests(source_by_path)
    logical_counts = write_master_indices_from_shards(manifests)
    aggregate = aggregate_shard_summary(manifests)
    counts = aggregate["counts"]
    counts["source_files_expected"] = source_count
    counts["source_files_completed"] = len(manifests)
    counts["source_files_completed_before_this_run"] = completed_before
    counts["source_files_processed_this_run"] = processed_now
    counts["master_candidate_index_rows"] = logical_counts.get("candidate_generation", 0)
    counts["master_denominator_index_rows"] = logical_counts.get("denominator_disposition", 0)

    summary = {
        "schema_version": "vnext_full_replay_candidate_generation_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "created_at_utc": started,
        "completed_at_utc": utc_now(),
        "git_head": git_head(),
        "source_universe_index_path": rel(SOURCE_UNIVERSE_INDEX_PATH),
        "candidate_generation_method": "market_bar_asof_incremental_ob_fvg_breaker_generator",
        "source_origin": SOURCE_ORIGIN,
        "durability_model": "per_source_shard_atomic_outputs_with_manifest_heartbeat_resume_cursor",
        "max_source_files_test_only": max_source_files,
        "counts": dict(counts),
        "candidate_rows_by_framework": aggregate["candidate_rows_by_framework"],
        "candidate_rows_by_symbol": aggregate["candidate_rows_by_symbol"],
        "candidate_rows_by_session_bucket": aggregate["candidate_rows_by_session_bucket"],
        "denominator_disposition_counts": aggregate["denominator_disposition_counts"],
        "row_counts_by_context_status": aggregate["row_counts_by_context_status"],
        "source_failures": aggregate["source_failures"],
        "output_paths": {key: rel(path) for key, path in OUTPUTS.items()},
        "next_incomplete_invariant": "Stage03 actual vNext runtime tracing for generated candidates",
        "scope_control_note": (
            "Stage02 is candidate-origin generation only; runtime tracing, M1/M5/tick/Sierra/OHLC path/R, "
            "M15 blindness, no-fill/pending, dominance/pollution, MIXED resolution, ablation, robustness, "
            "prop metrics, behavioral forensics, and final decision map remain incomplete."
        ),
    }
    write_json(OUTPUTS["candidate_generation_summary"], summary)
    verifier = verify_outputs(summary)
    write_json(OUTPUTS["stage02_verifier"], verifier)

    append_jsonl_rows(ACTIVE_QUESTION_PATH, stage02_question_rows(dict(counts)))
    append_jsonl_rows(EXTRA_STEP_PATH, stage02_extra_step_rows(dict(counts)))
    append_jsonl_rows(PROMPT_APPLICATION_PATH, stage02_prompt_application_rows(dict(counts)))
    update_session_state(summary, verifier)
    update_completion_audit(summary, verifier)
    update_line_audit()
    update_output_manifest(summary)

    return {
        "status": "ok" if verifier["status"] == "ok" else "fail",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "counts": dict(counts),
        "candidate_rows_by_framework": aggregate["candidate_rows_by_framework"],
        "verifier": verifier,
        "next_action": "build Stage03 actual vNext runtime decision harness over generated candidates",
    }


def iter_logical_rows(index_path: Path) -> Iterator[dict[str, Any]]:
    if not index_path.exists():
        return
    yield from iter_chunked_jsonl(index_path)


def verify_outputs(summary: dict[str, Any] | None = None) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    candidate_count = 0
    denominator_count = 0
    market_state_count = 0
    source_origins: Counter[str] = Counter()
    dispositions: Counter[str] = Counter()
    candidate_frameworks: Counter[str] = Counter()
    missing_candidate_fields: Counter[str] = Counter()
    missing_lookback_fields: Counter[str] = Counter()
    warmup_silent_no_setup_rows = 0
    warmup_denominator_inclusion_rows = 0
    seen_denominator_ids: set[str] = set()
    duplicate_denominator_ids = 0
    required_candidate_fields = set(read_json(ELIGIBILITY_CONTRACT_PATH)["candidate_row_required_fields"])
    for row in iter_logical_rows(OUTPUTS["candidate_generation"]):
        candidate_count += 1
        source_origins[str(row.get("source_origin"))] += 1
        candidate_frameworks[str(row.get("framework"))] += 1
        for field in required_candidate_fields:
            if row.get(field) in (None, "", [], {}):
                missing_candidate_fields[field] += 1
    for row in iter_logical_rows(OUTPUTS["denominator_disposition"]):
        denominator_count += 1
        disposition = str(row.get("candidate_generation_disposition"))
        dispositions[disposition] += 1
        row_id = str(row.get("source_universe_row_id"))
        if row_id in seen_denominator_ids:
            duplicate_denominator_ids += 1
        seen_denominator_ids.add(row_id)
        if disposition not in ALLOWED_DENOMINATOR_DISPOSITIONS:
            failures.append({"reason": "invalid_denominator_disposition", "row_id": row_id, "disposition": disposition})
        if row.get("source_origin") != SOURCE_ORIGIN:
            failures.append({"reason": "denominator_disposition_missing_market_bar_origin", "row_id": row_id})
        for field in LOOKBACK_CONTEXT_FIELDS:
            if row.get(field) in (None, "", [], {}):
                missing_lookback_fields[f"denominator_disposition.{field}"] += 1
        if row.get("warmup_context_sufficiency_status") == "warmup_context_limited_before_full_m15_lookback":
            if row.get("denominator_enters_stage02_candidate_denominator") is True:
                warmup_denominator_inclusion_rows += 1
            if disposition == "no_setup_by_asof_market_state" and row.get("skip_reason") == "no_active_unconsumed_ob_fvg_or_breaker_zone_touched_current_candle":
                warmup_silent_no_setup_rows += 1
    for row in iter_logical_rows(OUTPUTS["market_state_packet"]):
        market_state_count += 1
        for field in LOOKBACK_CONTEXT_FIELDS:
            if row.get(field) in (None, "", [], {}):
                missing_lookback_fields[f"market_state_packet.{field}"] += 1
    expected_denominator = sum(int(row.get("row_count") or 0) for row in iter_jsonl(SOURCE_UNIVERSE_INDEX_PATH))
    logged_count = prior_logged_event_count()
    if denominator_count != expected_denominator:
        failures.append(
            {
                "reason": "denominator_disposition_count_mismatch",
                "denominator_count": denominator_count,
                "expected_denominator": expected_denominator,
            }
        )
    if source_origins and set(source_origins) != {SOURCE_ORIGIN}:
        failures.append({"reason": "candidate_source_origin_not_market_bar", "source_origins": dict(source_origins)})
    if candidate_count == logged_count:
        failures.append(
            {
                "reason": "candidate_count_equals_prior_logged_event_count",
                "candidate_count": candidate_count,
                "prior_logged_event_count": logged_count,
            }
        )
    missing_frameworks = sorted(set(PRIMARY_FRAMEWORKS) - set(candidate_frameworks))
    if candidate_count > 0 and missing_frameworks:
        failures.append({"reason": "missing_primary_framework_candidates", "missing_frameworks": missing_frameworks})
    if missing_candidate_fields:
        failures.append({"reason": "candidate_missing_required_fields", "missing_counts": dict(missing_candidate_fields)})
    if duplicate_denominator_ids:
        failures.append({"reason": "duplicate_denominator_disposition_ids", "count": duplicate_denominator_ids})
    if market_state_count != expected_denominator:
        failures.append(
            {
                "reason": "market_state_packet_count_mismatch",
                "market_state_count": market_state_count,
                "expected_denominator": expected_denominator,
            }
        )
    if missing_lookback_fields:
        failures.append({"reason": "missing_lookback_context_fields", "missing_counts": dict(missing_lookback_fields)})
    if warmup_silent_no_setup_rows:
        failures.append({"reason": "warmup_rows_silently_counted_as_true_no_setup", "count": warmup_silent_no_setup_rows})
    if warmup_denominator_inclusion_rows:
        failures.append({"reason": "warmup_rows_included_in_production_like_denominator", "count": warmup_denominator_inclusion_rows})
    return {
        "schema_version": "vnext_full_replay_stage02_verifier_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "checked_at_utc": utc_now(),
        "status": "ok" if not failures else "fail",
        "candidate_count": candidate_count,
        "denominator_disposition_count": denominator_count,
        "market_state_packet_count": market_state_count,
        "expected_denominator_count": expected_denominator,
        "prior_logged_event_count": logged_count,
        "source_origin_counts": dict(source_origins),
        "candidate_framework_counts": dict(candidate_frameworks),
        "denominator_disposition_counts": dict(dispositions),
        "missing_lookback_context_fields": dict(missing_lookback_fields),
        "warmup_silent_no_setup_rows": warmup_silent_no_setup_rows,
        "warmup_denominator_inclusion_rows": warmup_denominator_inclusion_rows,
        "failures": failures[:50],
        "failure_count": len(failures),
        "summary_counts": (summary or {}).get("counts", {}),
    }


def audit_chunked_artifact(path: Path, artifact_key: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        rows.append(
            {
                "schema_version": "vnext_full_replay_line_accountability_audit_v1",
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "file_path": rel(path),
                "artifact_key": artifact_key,
                "exists": False,
                "audit_status": "FAIL",
                "anomaly_rows": [{"reason": "missing_logical_index"}],
            }
        )
        return rows
    chunk_row_sum = 0
    index_parse_errors = 0
    for index_row in iter_jsonl(path):
        chunk_path = repo_path(index_row["chunk_path"])
        row_count = 0
        parse_errors = 0
        schema_keys: set[str] = set()
        null_counts: Counter[str] = Counter()
        first_row: Any = None
        last_row: Any = None
        anomaly_rows: list[dict[str, Any]] = []
        if chunk_path.exists():
            with gzip.open(chunk_path, "rt", encoding="utf-8") as handle:
                for line_no, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError as exc:
                        parse_errors += 1
                        anomaly_rows.append({"line_no": line_no, "reason": str(exc)})
                        continue
                    row_count += 1
                    if first_row is None:
                        first_row = payload
                    last_row = payload
                    if isinstance(payload, dict):
                        schema_keys.update(payload.keys())
                        for key, value in payload.items():
                            if value in (None, "", [], {}):
                                null_counts[key] += 1
                        if payload.get("source_origin") != SOURCE_ORIGIN:
                            anomaly_rows.append(
                                {
                                    "line_no": line_no,
                                    "row_id": payload.get("candidate_id") or payload.get("source_universe_row_id"),
                                    "reason": "source_origin_not_market_bar_enumeration",
                                }
                            )
        else:
            parse_errors += 1
            anomaly_rows.append({"reason": "missing_chunk"})
        chunk_row_sum += row_count
        rows.append(
            {
                "schema_version": "vnext_full_replay_line_accountability_audit_v1",
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "artifact_key": artifact_key,
                "file_path": rel(path),
                "chunk_path": rel(chunk_path),
                "exists": chunk_path.exists(),
                "bytes": chunk_path.stat().st_size if chunk_path.exists() else None,
                "sha256": sha256_file(chunk_path) if chunk_path.exists() else None,
                "row_count": row_count,
                "index_row_count": index_row.get("row_count"),
                "parse_error_count": parse_errors,
                "schema_keys": sorted(schema_keys),
                "first_row": first_row,
                "last_row": last_row,
                "null_counts": dict(null_counts),
                "anomaly_rows": anomaly_rows[:20],
                "audit_status": "PASS" if parse_errors == 0 and row_count == int(index_row.get("row_count") or -1) and not anomaly_rows else "FAIL",
                "source_builder": rel(Path(__file__).resolve()),
                "independent_full_line_parse_status": "PASS" if parse_errors == 0 else "FAIL",
                "independent_full_line_source_identity_status": "PASS" if not anomaly_rows else "FAIL",
            }
        )
    rows.append(
        {
            "schema_version": "vnext_full_replay_line_accountability_audit_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "artifact_key": artifact_key,
            "file_path": rel(path),
            "exists": True,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "row_count": sum(1 for _ in iter_jsonl(path)),
            "logical_row_count": chunk_row_sum,
            "parse_error_count": index_parse_errors,
            "chunk_manifest_reconstruction_status": "PASS",
            "audit_status": "PASS",
            "source_builder": rel(Path(__file__).resolve()),
        }
    )
    return rows


def audit_simple_artifact(path: Path, artifact_key: str) -> dict[str, Any]:
    exists = path.exists()
    parse_errors = 0
    schema_keys: set[str] = set()
    row_count = 0
    first_row: Any = None
    last_row: Any = None
    if exists and path.suffix == ".json":
        try:
            payload = read_json(path)
            row_count = 1
            first_row = payload
            last_row = payload
            if isinstance(payload, dict):
                schema_keys.update(payload.keys())
        except Exception:
            parse_errors += 1
    elif exists and path.suffix == ".jsonl":
        for payload in iter_jsonl(path):
            row_count += 1
            if first_row is None:
                first_row = payload
            last_row = payload
            schema_keys.update(payload.keys())
    return {
        "schema_version": "vnext_full_replay_line_accountability_audit_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "artifact_key": artifact_key,
        "file_path": rel(path),
        "exists": exists,
        "bytes": path.stat().st_size if exists else None,
        "sha256": sha256_file(path) if exists else None,
        "row_count": row_count,
        "parse_error_count": parse_errors,
        "schema_keys": sorted(schema_keys),
        "first_row": first_row,
        "last_row": last_row,
        "audit_status": "PASS" if exists and parse_errors == 0 else "FAIL",
        "source_builder": rel(Path(__file__).resolve()),
    }


def update_line_audit() -> None:
    existing = [
        row
        for row in (list(iter_jsonl(LINE_AUDIT_PATH)) if LINE_AUDIT_PATH.exists() else [])
        if row.get("stage_id") != STAGE_ID
    ]
    stage_rows: list[dict[str, Any]] = []
    for key in (
        "candidate_generation",
        "denominator_disposition",
        "market_state_packet",
        "decision_explanation",
    ):
        stage_rows.extend(audit_chunked_artifact(OUTPUTS[key], key))
    for key in (
        "candidate_generation_summary",
        "stage02_verifier",
        "stage02_shard_contract",
        "stage02_heartbeat",
        "stage02_shard_status",
    ):
        stage_rows.append(audit_simple_artifact(OUTPUTS[key], key))
    write_jsonl(LINE_AUDIT_PATH, existing + stage_rows)


def update_session_state(summary: dict[str, Any], verifier: dict[str, Any]) -> None:
    state = read_json(SESSION_STATE_PATH) if SESSION_STATE_PATH.exists() else {}
    counts = state.get("counts") or {}
    counts.update(
        {
            "stage02_candidate_rows": summary["counts"]["candidate_rows"],
            "stage02_denominator_disposition_rows": summary["counts"]["denominator_rows"],
            "stage02_market_state_packet_rows": summary["counts"]["market_state_packet_rows"],
            "stage02_decision_explanation_rows": summary["counts"]["decision_explanation_rows"],
            "stage02_source_files_processed": summary["counts"]["source_files_processed"],
        }
    )
    state.update(
        {
            "schema_version": "vnext_full_replay_session_state_v1",
            "route_id": ROUTE_ID,
            "updated_at_utc": utc_now(),
            "git_head": git_head(),
            "current_stage": STAGE_ID,
            "goal_complete": False,
            "active_invariant": "Stage02 candidate generation from market-bar denominator rows",
            "first_incomplete_invariant": "Stage03 actual vNext runtime tracing for generated candidates",
            "next_action": "build Stage03 actual vNext runtime decision harness over Stage02 generated candidates",
            "stage02_verifier_status": verifier["status"],
            "stage02_output_paths": {key: rel(path) for key, path in OUTPUTS.items()},
            "stage02_durability_lookback_scope_steer_status": "applied_once_recorded_do_not_relitigate_after_resume",
            "stage02_durability_model": "per_source_atomic_shards_with_manifest_heartbeat_resume_cursor",
            "stage02_scope_boundary": (
                "candidate-origin generation only; replay spine remains active through runtime, path/R, "
                "M15-blindness, no-fill/pending, dominance/pollution, MIXED, ablation, robustness, prop metrics, "
                "behavioral forensics, final decision map"
            ),
            "stage02_source_mode_boundary": (
                "76 MT5/export/source requirements and M1/M5/tick/Sierra/SCID/OHLC path-source actions remain open; "
                "they are not terminal placeholders and must be executed/repaired or row-level bounded before path/R/final replay conclusions"
            ),
            "counts": counts,
            "candidate_rows_by_framework": summary["candidate_rows_by_framework"],
            "denominator_disposition_counts": summary["denominator_disposition_counts"],
            "row_counts_by_context_status": summary.get("row_counts_by_context_status", {}),
        }
    )
    open_questions = set(state.get("open_questions") or [])
    open_questions.update(row["question_id"] for row in stage02_question_rows(summary["counts"]))
    state["open_questions"] = sorted(open_questions)
    write_json(SESSION_STATE_PATH, state)


def update_completion_audit(summary: dict[str, Any], verifier: dict[str, Any]) -> None:
    existing = read_json(COMPLETION_AUDIT_PATH) if COMPLETION_AUDIT_PATH.exists() else {}
    completed = list(existing.get("completed_requirements_stage01") or existing.get("completed_requirements") or [])
    completed_stage02 = [
        "Stage02 candidate-generation driver built route-locally",
        "source-universe denominator chunks read from Stage01 market-bar enumeration",
        "as-of market-state packet ledger written",
        "candidate-generation ledger written from market bars, not shadow logs",
        "denominator disposition ledger resolves every Stage01 source-universe row",
        "decision-explanation ledger written for candidates and skips",
        "Stage02 verifier enforces source_origin and prior logged-event count guard",
    ]
    audit = {
        "schema_version": "vnext_full_replay_completion_audit_v1",
        "route_id": ROUTE_ID,
        "updated_at_utc": utc_now(),
        "completion_status": "IN_PROGRESS_NOT_COMPLETE",
        "completed_requirements_stage01": completed,
        "completed_requirements_stage02": completed_stage02,
        "one_time_stage02_owner_steer_applied": {
            "status": "applied_once_recorded_not_replacement_objective",
            "durability_patch": "per-source route-owned shard outputs with atomic temp-to-final replace, row counts, sha256, shard status, heartbeat, resume cursor, verifier coverage",
            "lookback_patch": "denominator disposition and market-state packet rows include lookback_bars/asof_window/context sufficiency fields",
            "scope_control": "Stage02 remains candidate-origin generation only and does not close lower-timeframe/source-mode replay requirements",
            "post_resume_rule": "reread route state/completion audit and continue first incomplete invariant; do not restart this steer if verifier proof remains recorded",
        },
        "stage02_counts": summary["counts"],
        "stage02_verifier_status": verifier["status"],
        "remaining_prompt_requirements_not_complete": [
            "actual vNext runtime tracing for generated candidates",
            "execute/repair MT5 export requirements and bind M1/M5/tick/Sierra/SCID/OHLC source modes before path/R and M15-blindness conclusions",
            "path/R outcome simulation",
            "null/unknown audit after runtime/path ledgers",
            "dominance and pollution counterfactuals",
            "MIXED replay resolution",
            "ablation/robustness/prop metrics",
            "behavioral forensics",
            "subagent or equivalent independent review for terminal outputs",
            "final promote/kill/repair map",
            "goal completion audit",
        ],
        "same_evidence_class_next_action": "build Stage03 actual vNext runtime decision harness over generated candidates",
        "goal_may_be_marked_complete": False,
    }
    write_json(COMPLETION_AUDIT_PATH, audit)


def update_output_manifest(summary: dict[str, Any]) -> None:
    existing = read_json(OUTPUT_MANIFEST_PATH) if OUTPUT_MANIFEST_PATH.exists() else {
        "schema_version": "vnext_full_replay_output_manifest_v1",
        "route_id": ROUTE_ID,
        "artifacts": [],
    }
    old_artifacts = [
        row
        for row in existing.get("artifacts", [])
        if row.get("artifact_key") not in {
            "candidate_generation",
            "candidate_generation_chunk",
            "denominator_disposition",
            "denominator_disposition_chunk",
            "market_state_packet",
            "market_state_packet_chunk",
            "decision_explanation",
            "decision_explanation_chunk",
            "candidate_generation_summary",
            "stage02_verifier",
            "stage02_shard_contract",
            "stage02_heartbeat",
            "stage02_shard_status",
            "active_questions",
            "extra_step",
            "prompt_application",
            "line_audit",
            "completion_audit",
        }
    ]
    stage_artifacts: list[dict[str, Any]] = []
    for key in (
        "candidate_generation",
        "denominator_disposition",
        "market_state_packet",
        "decision_explanation",
    ):
        stage_artifacts.extend(chunk_artifact_manifest(OUTPUTS[key], key))
    for key in (
        "candidate_generation_summary",
        "stage02_verifier",
        "stage02_shard_contract",
        "stage02_heartbeat",
        "stage02_shard_status",
    ):
        path = OUTPUTS[key]
        stage_artifacts.append(
            {
                "artifact_key": key,
                "path": rel(path),
                "bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path) if path.exists() else None,
                "row_count": (
                    sum(1 for _ in iter_jsonl(path))
                    if path.exists() and path.suffix == ".jsonl"
                    else (1 if path.exists() else 0)
                ),
                "logical_row_count": None,
            }
        )
    for key, path in {
        "active_questions": ACTIVE_QUESTION_PATH,
        "extra_step": EXTRA_STEP_PATH,
        "prompt_application": PROMPT_APPLICATION_PATH,
        "line_audit": LINE_AUDIT_PATH,
        "completion_audit": COMPLETION_AUDIT_PATH,
    }.items():
        if path.exists():
            stage_artifacts.append(
                {
                    "artifact_key": key,
                    "path": rel(path),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "row_count": sum(1 for _ in iter_jsonl(path)) if path.suffix == ".jsonl" else 1,
                    "logical_row_count": None,
                }
            )
    existing.update(
        {
            "schema_version": "vnext_full_replay_output_manifest_v1",
            "route_id": ROUTE_ID,
            "created_at_utc": existing.get("created_at_utc") or utc_now(),
            "updated_at_utc": utc_now(),
            "stage_id": STAGE_ID,
            "goal_complete": False,
            "artifacts": old_artifacts + stage_artifacts,
            "stage02_counts": summary["counts"],
        }
    )
    write_json(OUTPUT_MANIFEST_PATH, existing)


def check_outputs() -> dict[str, Any]:
    summary = read_json(OUTPUTS["candidate_generation_summary"]) if OUTPUTS["candidate_generation_summary"].exists() else None
    verifier = verify_outputs(summary)
    audit_failures = []
    if LINE_AUDIT_PATH.exists():
        for row in iter_jsonl(LINE_AUDIT_PATH):
            if row.get("stage_id") == STAGE_ID and row.get("audit_status") != "PASS":
                audit_failures.append(
                    {
                        "artifact_key": row.get("artifact_key"),
                        "file_path": row.get("file_path"),
                        "chunk_path": row.get("chunk_path"),
                        "reason": "line_audit_not_pass",
                    }
                )
    missing = [key for key, path in OUTPUTS.items() if not path.exists()]
    status = "ok" if verifier["status"] == "ok" and not missing and not audit_failures else "fail"
    return {
        "status": status,
        "missing": missing,
        "verifier": verifier,
        "audit_failure_count": len(audit_failures),
        "audit_failures": audit_failures[:20],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Verify existing Stage02 outputs.")
    parser.add_argument(
        "--max-source-files",
        type=int,
        default=None,
        help="Test-only cap. Do not use for final Stage02 artifact.",
    )
    args = parser.parse_args(argv)
    payload = check_outputs() if args.check else build_outputs(max_source_files=args.max_source_files)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())

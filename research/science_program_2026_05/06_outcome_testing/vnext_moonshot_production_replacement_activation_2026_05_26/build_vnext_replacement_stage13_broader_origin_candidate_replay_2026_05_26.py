from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import json
import math
import sys
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage13_broader_origin_candidate_replay"
REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
MOONSHOT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)
FULL_REPLAY_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_full_historical_candidate_generation_replay_2026_05_24"
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research.dynamic_execution_policy import (  # noqa: E402
    observation_from_ohlc,
    required_policy_manifest,
    simulate_policy,
)


STAGE02_BUILDER = FULL_REPLAY_DIR / "build_vnext_full_replay_stage02_candidate_generation_2026_05_24.py"
STAGE04_BUILDER = FULL_REPLAY_DIR / "build_vnext_full_replay_stage04_source_mode_path_r_2026_05_24.py"
MOONSHOT_STAGE04_BUILDER = MOONSHOT_DIR / "build_vnext_moonshot_stage04_full_policy_dynamic_replay_2026_05_26.py"
ORIGIN_REGISTRY = MOONSHOT_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REGISTRY_{DATE}.jsonl"
ORIGIN_BOXING_LEDGER = MOONSHOT_DIR / f"VNEXT_MOONSHOT_CANDIDATE_ORIGIN_BOXING_AUDIT_LEDGER_{DATE}.jsonl"
SOURCE_CAPABILITY_LEDGER = MOONSHOT_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_LEDGER_{DATE}.jsonl"
SOURCE_CAPABILITY_SUMMARY = MOONSHOT_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_{DATE}.json"
STAGE10_FEATURE_LEDGER = MOONSHOT_DIR / f"VNEXT_MOONSHOT_ML_DYNAMIC_FEATURE_LEDGER_{DATE}.jsonl"
STAGE10_VERIFICATION = MOONSHOT_DIR / f"VNEXT_MOONSHOT_STAGE10_VERIFICATION_RESULT_{DATE}.json"
MARKET_SOURCE_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_{DATE}.json"
STAGE13_BRANCH_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_BRANCH_ORIGIN_AUDIT_SUMMARY_{DATE}.json"
STAGE13_ORIGIN_CONTRACT_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_ORIGIN_CONTRACT_LEDGER_{DATE}.jsonl"
)
PRIOR_BROADER_CONTRACT_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_CANDIDATE_CONTRACT_LEDGER_{DATE}.jsonl"
)
PRIOR_BROADER_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_REPLAY_SUMMARY_{DATE}.json"

PENDING_LIFECYCLE = REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl"
PENDING_TICK_SPREAD = REPO_ROOT / "shadow_logs/pending_lifecycle_tick_spread_reconstruction.jsonl"
ORDERFLOW_STATUS = REPO_ROOT / "shadow_logs/orderflow_primitives_status.jsonl"
NAS100_ORDERFLOW_STATUS = REPO_ROOT / "shadow_logs/nas100_orderflow_adverse_selection_status.jsonl"
NOFILL_FORWARD_CAPTURE = REPO_ROOT / "shadow_logs/nofill_forward_source_capture.jsonl"
ECONOMIC_CALENDAR = REPO_ROOT / "data/economic_calendar.csv"

OUTPUT_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_CANDIDATE_REPLAY_LEDGER_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_CANDIDATE_REPLAY_SUMMARY_{DATE}.json"
)

CURRENT_ORIGINS = {"ob_retest", "fvg_fill", "breaker_re_entry"}
FULL_REPLAY_MODE = False
MAX_CONTRACT_REPLAY_ROWS_PER_FAMILY = 240
MAX_PENDING_REPLAY_ROWS = 120
MAX_SPREAD_REPLAY_ROWS = 80
PATH_HORIZON_HOURS = 48
SAME_BAR_POLICY = "conservative"

CSV_CACHE: dict[str, tuple[list[datetime], list[dict[str, str]]]] = {}
SOURCE_CAPABILITY_CACHE: dict[str, dict[str, Any]] | None = None
STAGE04_MODULE: Any | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path | str | None) -> str | None:
    if path is None:
        return None
    candidate = Path(path)
    try:
        return candidate.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return candidate.as_posix().replace("\\", "/")


def repo_path(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return candidate


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, payload: Any, length: int = 24) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:length]}"


def parse_time(value: Any) -> datetime | None:
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
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def dt_s(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def fnum(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_maybe_gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_csv_rows(source_path: str) -> tuple[list[datetime], list[dict[str, str]]]:
    key = rel(source_path) or source_path
    if key in CSV_CACHE:
        return CSV_CACHE[key]
    absolute = repo_path(source_path)
    times: list[datetime] = []
    rows: list[dict[str, str]] = []
    if absolute is None or not absolute.exists():
        CSV_CACHE[key] = (times, rows)
        return times, rows
    with absolute.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            parsed = parse_time(row.get("time") or row.get("datetime") or row.get("timestamp"))
            if parsed is None:
                continue
            times.append(parsed)
            rows.append(row)
    CSV_CACHE[key] = (times, rows)
    return times, rows


def load_stage04_module() -> Any | None:
    global STAGE04_MODULE
    if STAGE04_MODULE is not None:
        return STAGE04_MODULE
    if not STAGE04_BUILDER.exists():
        return None
    spec = importlib.util.spec_from_file_location("vnext_full_stage04_replay_helpers", STAGE04_BUILDER)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    STAGE04_MODULE = module
    return module


def load_source_capability_by_path() -> dict[str, dict[str, Any]]:
    global SOURCE_CAPABILITY_CACHE
    if SOURCE_CAPABILITY_CACHE is not None:
        return SOURCE_CAPABILITY_CACHE
    out: dict[str, dict[str, Any]] = {}
    for row in iter_jsonl(SOURCE_CAPABILITY_LEDGER):
        source_path = row.get("source_path")
        if source_path:
            out[str(source_path).replace("\\", "/")] = row
    SOURCE_CAPABILITY_CACHE = out
    return out


def read_paths_audit() -> list[dict[str, Any]]:
    paths = [
        (STAGE13_BRANCH_SUMMARY, "stage13_full_moonshot_summary"),
        (STAGE13_ORIGIN_CONTRACT_LEDGER, "stage13_origin_contract_ledger"),
        (ORIGIN_REGISTRY, "universal_origin_registry"),
        (ORIGIN_BOXING_LEDGER, "origin_boxing_audit_ledger"),
        (SOURCE_CAPABILITY_LEDGER, "source_capability_ledger"),
        (SOURCE_CAPABILITY_SUMMARY, "source_capability_summary"),
        (STAGE02_BUILDER, "stage02_candidate_builder_load_candles_create_geometry_candidate_row"),
        (STAGE04_BUILDER, "stage04_path_builder_event_from_candidate_process_candidate_ohlc_rows"),
        (MOONSHOT_STAGE04_BUILDER, "moonshot_dynamic_policy_replay_builder"),
        (STAGE10_FEATURE_LEDGER, "stage10_ml_dynamic_feature_ledger"),
        (STAGE10_VERIFICATION, "stage10_verification_result"),
        (MARKET_SOURCE_MAP, "market_source_activation_map"),
        (PRIOR_BROADER_CONTRACT_LEDGER, "prior_broader_origin_contract_seed_ledger"),
        (PRIOR_BROADER_SUMMARY, "prior_broader_origin_summary"),
        (PENDING_LIFECYCLE, "pending_lifecycle_shadow_log"),
        (PENDING_TICK_SPREAD, "pending_tick_spread_shadow_log"),
        (ORDERFLOW_STATUS, "orderflow_primitives_status"),
        (NAS100_ORDERFLOW_STATUS, "nas100_orderflow_status"),
        (NOFILL_FORWARD_CAPTURE, "nofill_forward_capture"),
        (ECONOMIC_CALENDAR, "economic_calendar"),
    ]
    rows = []
    for path, role in paths:
        rows.append(
            {
                "path": rel(path),
                "read_role": role,
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path) if path.exists() else None,
            }
        )
    return rows


def registry_rows() -> list[dict[str, Any]]:
    return [row for row in iter_jsonl(ORIGIN_REGISTRY)]


def non_current_origins() -> list[dict[str, Any]]:
    return [row for row in registry_rows() if row.get("name") not in CURRENT_ORIGINS]


def stage13_contract_by_origin() -> dict[str, dict[str, Any]]:
    out = {}
    for row in iter_jsonl(STAGE13_ORIGIN_CONTRACT_LEDGER):
        name = row.get("origin_name")
        if name:
            out[str(name)] = row
    return out


def source_family_counts() -> Counter:
    counts: Counter = Counter()
    for row in iter_jsonl(SOURCE_CAPABILITY_LEDGER):
        counts[str(row.get("source_family") or "UNKNOWN")] += 1
    return counts


def candidate_dict_from_seed(row: dict[str, Any], candidate_id: str | None = None) -> dict[str, Any]:
    family = str(row.get("origin_family") or row.get("candidate_origin_family") or "unknown").replace("origin_", "")
    source_path = row.get("source_path")
    decision_time = row.get("decision_time_utc")
    return {
        "candidate_id": candidate_id or row.get("row_id") or stable_id("broadcand", row),
        "source_universe_row_id": row.get("row_id"),
        "market_state_packet_id": None,
        "source_origin": "stage13_broader_origin_candidate_replay",
        "symbol": row.get("symbol"),
        "source_symbol": row.get("source_symbol") or row.get("symbol"),
        "timeframe": row.get("timeframe") or "M15",
        "market_timeframe": row.get("timeframe") or "M15",
        "session_bucket": (row.get("source_fields") or {}).get("session_at_candidate"),
        "date_utc": str(decision_time or "")[:10],
        "candle_time_utc": decision_time,
        "side": str(row.get("side") or "").upper(),
        "framework": f"origin_{family}",
        "entry_reference": row.get("entry_price"),
        "entry_price": row.get("entry_price"),
        "stop_or_invalidation": row.get("stop_or_invalidation"),
        "target_reference": row.get("target_reference"),
        "target_price": row.get("target_reference"),
        "rr": row.get("rr") or 1.5,
        "source_path": source_path,
        "source_sha256": row.get("source_sha256") or sha256_file(repo_path(source_path) or Path()),
    }


def path_replay_for_candidate(candidate: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str | None]:
    module = load_stage04_module()
    if module is None:
        return None, [], "stage04_helper_module_not_importable"
    try:
        event = module.event_from_candidate(candidate)
        rows = module.ohlc_rows(candidate, event)
        best = module.best_available_path(rows)
        return best, rows, None
    except Exception as exc:
        return None, [], f"stage04_helper_error:{type(exc).__name__}:{exc}"


def observations_for_path_row(path_row: dict[str, Any]) -> tuple[list[Any], str | None]:
    source_path = path_row.get("source_path")
    if isinstance(source_path, list):
        return [], "tick_or_multi_source_dynamic_policy_not_supported_in_this_pass"
    if not source_path:
        return [], "missing_source_path"
    absolute = repo_path(source_path)
    if absolute is None or not absolute.exists():
        return [], "source_file_missing"
    entry = fnum(path_row.get("entry_reference"))
    stop = fnum(path_row.get("stop_or_invalidation"))
    side = str(path_row.get("side") or "").upper()
    if entry is None or stop is None or side not in {"LONG", "SHORT"}:
        return [], "missing_entry_stop_side"
    start = parse_time(path_row.get("entry_first_touch_utc") or path_row.get("first_bar_utc"))
    end = parse_time(path_row.get("path_window_requested_end_utc") or path_row.get("last_bar_utc"))
    if start is None or end is None:
        return [], "missing_path_time_window"
    times, source_rows = load_csv_rows(str(source_path))
    left = bisect_left(times, start)
    right = bisect_right(times, end)
    if left >= right:
        return [], "source_window_empty_after_entry"
    observations = []
    for local_index, source_row in enumerate(source_rows[left:right], start=1):
        try:
            observations.append(
                observation_from_ohlc(
                    index=local_index,
                    row=source_row,
                    entry=float(entry),
                    stop=float(stop),
                    side=side,
                    time_key="time",
                )
            )
        except Exception as exc:
            return [], f"observation_build_error:{type(exc).__name__}:{exc}"
    return observations, None


def policy_result_to_dict(result: Any) -> dict[str, Any]:
    return {
        "replay_status": result.replay_status,
        "final_r": result.final_r,
        "exit_reason": result.exit_reason,
        "exit_index": result.exit_index,
        "exit_time_utc": result.exit_time_utc,
        "mfe_r": result.mfe_r,
        "mae_r": result.mae_r,
        "partial_realized_r": result.partial_realized_r,
        "remaining_fraction": result.remaining_fraction,
        "stop_r_at_exit": result.stop_r_at_exit,
        "same_bar_ambiguity": result.same_bar_ambiguity,
        "source_gap_reason": result.source_gap_reason,
        "transitions": result.transitions,
    }


def replay_dynamic_policies(path_row: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    observations, gap = observations_for_path_row(path_row)
    if gap:
        return {}, gap
    out = {}
    for policy in required_policy_manifest():
        result = simulate_policy(policy, observations, same_bar_policy=SAME_BAR_POLICY)
        out[policy.name] = policy_result_to_dict(result)
    return out, None


def compact_path_row(path_row: dict[str, Any] | None) -> dict[str, Any] | None:
    if path_row is None:
        return None
    keys = [
        "path_row_id",
        "replay_mode",
        "path_source_status",
        "source_mode",
        "source_evidence_type",
        "source_path",
        "source_sha256",
        "source_window_complete",
        "entry_touched",
        "entry_first_touch_utc",
        "terminal_outcome",
        "terminal_order_raw",
        "simulated_r",
        "mfe_r",
        "mae_r",
        "source_gap_class",
        "searched_paths",
        "price_path_truth_status",
        "trade_performance_denominator_inclusion",
    ]
    return {key: path_row.get(key) for key in keys if key in path_row}


def dynamic_source_path_row(path_rows: list[dict[str, Any]], best_path: dict[str, Any] | None) -> dict[str, Any] | None:
    for preferred_mode in ("bar_close_m15", "m1_path_aware", "m5_path_aware", "ohlc_only_proxy"):
        for row in path_rows:
            if (
                row.get("replay_mode") == preferred_mode
                and row.get("terminal_outcome") != "missing_source_denominator_excluded"
                and row.get("source_path")
            ):
                return row
    return best_path


def replay_seed_row(row: dict[str, Any], *, origin: dict[str, Any], sequence: int) -> dict[str, Any]:
    candidate = candidate_dict_from_seed(row)
    best_path, path_rows, path_gap = path_replay_for_candidate(candidate)
    dynamic_results, dynamic_gap = ({}, path_gap)
    dynamic_path = dynamic_source_path_row(path_rows, best_path)
    if dynamic_path and dynamic_path.get("terminal_outcome") != "missing_source_denominator_excluded":
        dynamic_results, dynamic_gap = replay_dynamic_policies(dynamic_path)
    source_capability = load_source_capability_by_path().get(str(row.get("source_path") or "").replace("\\", "/"))
    policy_final_r = {
        name: result.get("final_r")
        for name, result in dynamic_results.items()
        if result.get("final_r") is not None
    }
    return {
        "schema_version": "vnext_replacement_stage13_broader_origin_candidate_replay_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "row_type": "candidate_replay",
        "action": "generated_candidate_row_and_replayed_bar_close_path_dynamic_policy",
        "origin_family": origin["name"],
        "origin_category": origin.get("category"),
        "registry_id": origin.get("registry_id"),
        "candidate_replay_row_id": stable_id("broadreplay", [row.get("row_id"), sequence]),
        "source_candidate_row_id": row.get("row_id"),
        "candidate_row": candidate,
        "candidate_generation_source": {
            "source_contract": "prior_route_local_ohlc_feature_candidate_contract_seed",
            "source_path": row.get("source_path"),
            "source_sha256": row.get("source_sha256"),
            "source_row_index": row.get("source_row_index"),
            "source_fields": row.get("source_fields"),
            "seed_ledger_path": rel(PRIOR_BROADER_CONTRACT_LEDGER),
            "generated_from_repo_local_ohlc_or_feature": True,
        },
        "path_replay": compact_path_row(best_path),
        "dynamic_policy_source_path_replay": compact_path_row(dynamic_path),
        "stage04_helper_replay_modes_seen": sorted(
            str(item.get("replay_mode")) for item in path_rows if item.get("replay_mode")
        ),
        "dynamic_policy_replay": {
            "replay_attempted": bool(dynamic_results),
            "same_bar_policy": SAME_BAR_POLICY,
            "policy_results": dynamic_results,
            "source_gap_reason": dynamic_gap,
            "policy_final_r_by_policy": policy_final_r,
        },
        "metrics": {
            "dynamic_replayable": bool(dynamic_results),
            "legacy_fixed_1_5r": policy_final_r.get("legacy_fixed_1.5r"),
            "live_current_j46_j49_r": policy_final_r.get("live_current_j46_j49"),
            "be_after_trigger_r": policy_final_r.get("be_after_trigger"),
            "best_policy_final_r": max(policy_final_r.values()) if policy_final_r else None,
            "prototype_fixed_r": row.get("prototype_final_r"),
            "path_terminal_outcome": best_path.get("terminal_outcome") if best_path else None,
        },
        "activation_ready": False,
        "activation_blocker_after_replay": (
            "bounded_or_origin_native_replay_not_production_activation"
            if bool(dynamic_results)
            else dynamic_gap
        ),
        "source_capability_evidence": {
            "source_capability_ledger_path": rel(SOURCE_CAPABILITY_LEDGER),
            "matched_record_id": (source_capability or {}).get("record_id"),
            "source_family": (source_capability or {}).get("source_family"),
            "dynamic_execution_usable": (source_capability or {}).get("dynamic_execution_usable"),
            "dynamic_execution_usable_reason": (source_capability or {}).get(
                "dynamic_execution_usable_reason"
            ),
        },
        "no_live_trading_or_broker_mutation": True,
    }


def proof_row(
    *,
    origin: dict[str, Any],
    action: str,
    proof_class: str,
    blocker: str,
    evidence: dict[str, Any],
    rows_blocked: int = 0,
) -> dict[str, Any]:
    return {
        "schema_version": "vnext_replacement_stage13_broader_origin_candidate_replay_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "row_type": "proof",
        "action": action,
        "origin_family": origin["name"],
        "origin_category": origin.get("category"),
        "registry_id": origin.get("registry_id"),
        "proof_class": proof_class,
        "exact_blocker": blocker,
        "rows_blocked": rows_blocked,
        "source_requirements": origin.get("source_requirements"),
        "source_availability_status": origin.get("source_availability_status"),
        "evidence": evidence,
        "activation_ready": False,
        "no_live_trading_or_broker_mutation": True,
    }


def existing_seed_rows_by_family() -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in iter_jsonl(PRIOR_BROADER_CONTRACT_LEDGER):
        family = row.get("origin_family")
        if family:
            rows[str(family)].append(row)
    return rows


def pending_lifecycle_candidates(origin: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for row in iter_jsonl(PENDING_LIFECYCLE):
        entry = fnum(row.get("entry_price"))
        stop = fnum(row.get("stop_loss"))
        target = fnum(row.get("take_profit_1"))
        side = str(row.get("side") or "").upper()
        symbol = row.get("symbol") or row.get("source_symbol") or row.get("broker_symbol")
        decision = (
            row.get("decision_time_utc")
            or row.get("pending_created_time_utc")
            or row.get("checked_candle_time_utc")
            or row.get("timestamp_utc")
        )
        if None in (entry, stop, target) or side not in {"LONG", "SHORT"} or not symbol or not decision:
            continue
        key = (
            row.get("trade_id")
            or row.get("candidate_id")
            or f"{symbol}:{decision}:{side}:{entry}:{stop}:{target}"
        )
        if key in seen:
            continue
        seen.add(key)
        risk = abs(entry - stop)
        out.append(
            {
                "row_id": stable_id("nofillseed", key),
                "origin_family": origin["name"],
                "candidate_origin_family": f"origin_{origin['name']}",
                "generation_status": "generated_executable_from_forward_pending_lifecycle",
                "symbol": symbol,
                "source_symbol": row.get("source_symbol") or symbol,
                "timeframe": "M15",
                "decision_time_utc": decision,
                "side": side,
                "entry_price": entry,
                "stop_or_invalidation": stop,
                "target_reference": target,
                "rr": abs(target - entry) / risk if risk > 0 else None,
                "source_path": None,
                "source_sha256": None,
                "source_row_index": None,
                "source_fields": {
                    "shadow_log_path": rel(PENDING_LIFECYCLE),
                    "trade_id": row.get("trade_id"),
                    "candidate_id": row.get("candidate_id"),
                    "pending_created_time_utc": row.get("pending_created_time_utc"),
                    "fill_no_fill_label": row.get("fill_no_fill_label"),
                    "broker_fill_state": row.get("broker_fill_state"),
                    "source_branch": row.get("source_branch"),
                    "evidence_class": row.get("evidence_class"),
                },
            }
        )
    return out


def spread_lifecycle_candidates(origin: dict[str, Any]) -> list[dict[str, Any]]:
    pending_by_id: dict[str, dict[str, Any]] = {}
    for row in iter_jsonl(PENDING_LIFECYCLE):
        keys = [row.get("candidate_id"), row.get("trade_id")]
        for key in keys:
            if key:
                pending_by_id[str(key)] = row
    out = []
    seen = set()
    for spread in iter_jsonl(PENDING_TICK_SPREAD):
        key = str(spread.get("candidate_id") or "")
        pending = pending_by_id.get(key)
        if not pending:
            continue
        entry = fnum(pending.get("entry_price"))
        stop = fnum(pending.get("stop_loss"))
        target = fnum(pending.get("take_profit_1"))
        side = str(pending.get("side") or "").upper()
        symbol = pending.get("symbol") or spread.get("symbol")
        decision = spread.get("decision_time_utc") or pending.get("decision_time_utc")
        if None in (entry, stop, target) or side not in {"LONG", "SHORT"} or not symbol or not decision:
            continue
        dedupe = (key, symbol, decision, entry, stop, target)
        if dedupe in seen:
            continue
        seen.add(dedupe)
        risk = abs(entry - stop)
        out.append(
            {
                "row_id": stable_id("spreadseed", dedupe),
                "origin_family": origin["name"],
                "candidate_origin_family": f"origin_{origin['name']}",
                "generation_status": "generated_executable_from_joined_pending_tick_spread",
                "symbol": symbol,
                "source_symbol": pending.get("source_symbol") or symbol,
                "timeframe": "M15",
                "decision_time_utc": decision,
                "side": side,
                "entry_price": entry,
                "stop_or_invalidation": stop,
                "target_reference": target,
                "rr": abs(target - entry) / risk if risk > 0 else None,
                "source_path": None,
                "source_sha256": None,
                "source_row_index": None,
                "source_fields": {
                    "pending_lifecycle_path": rel(PENDING_LIFECYCLE),
                    "tick_spread_path": rel(PENDING_TICK_SPREAD),
                    "candidate_id": key,
                    "decision_spread_status": spread.get("decision_spread_status"),
                    "decision_spread_value_source_safe": spread.get("decision_spread_value_source_safe"),
                    "tick_source_path": spread.get("tick_source_path"),
                    "tick_source_sha256": spread.get("tick_source_sha256"),
                },
            }
        )
    return out


def enrich_candidate_source_path(seed: dict[str, Any]) -> dict[str, Any]:
    if seed.get("source_path"):
        return seed
    module = load_stage04_module()
    if module is None:
        return seed
    candidate = candidate_dict_from_seed(seed)
    try:
        event = module.event_from_candidate(candidate)
        series, left, right, searched = module.find_ohlc_window(event, "M15")
        if series is not None and right > left:
            seed = dict(seed)
            seed["source_path"] = rel(series.path)
            seed["source_sha256"] = sha256_file(series.path)
            seed.setdefault("source_fields", {})["ohlc_source_binding"] = {
                "searched_paths": searched,
                "bound_path": rel(series.path),
                "window_left": left,
                "window_right": right,
            }
    except Exception as exc:
        seed = dict(seed)
        seed.setdefault("source_fields", {})["ohlc_source_binding_error"] = f"{type(exc).__name__}:{exc}"
    return seed


def orderflow_proof_evidence() -> dict[str, Any]:
    status_rows = list(iter_jsonl(ORDERFLOW_STATUS))
    nas_rows = list(iter_jsonl(NAS100_ORDERFLOW_STATUS))
    first_status = status_rows[0] if status_rows else {}
    first_nas = nas_rows[0] if nas_rows else {}
    return {
        "source_paths": [rel(ORDERFLOW_STATUS), rel(NAS100_ORDERFLOW_STATUS)],
        "orderflow_status_rows": len(status_rows),
        "nas100_orderflow_status_rows": len(nas_rows),
        "status_fields": sorted(first_status.keys()) if first_status else [],
        "blocker_codes_sample": first_status.get("blocker_codes"),
        "candidate_trigger_policy": first_status.get("candidate_trigger_policy"),
        "claim_boundary": first_status.get("claim_boundary"),
        "nas100_databento_live_status": first_nas.get("databento_live_status"),
        "nas100_cached_feature_status": first_nas.get("cached_feature_status"),
    }


def news_proof_evidence() -> dict[str, Any]:
    rows = 0
    fields: list[str] | None = None
    if ECONOMIC_CALENDAR.exists():
        with ECONOMIC_CALENDAR.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            rows = sum(1 for _ in reader)
    return {
        "source_path": rel(ECONOMIC_CALENDAR),
        "calendar_rows": rows,
        "calendar_fields": fields,
        "prior_broader_summary_path": rel(PRIOR_BROADER_SUMMARY),
        "prior_family_summary": (read_json(PRIOR_BROADER_SUMMARY).get("family_summary") or {}).get(
            "news_volatility_reprice"
        ),
    }


def path_hazard_proof_evidence() -> dict[str, Any]:
    feature_sample = None
    for row in iter_jsonl(STAGE10_FEATURE_LEDGER):
        feature_sample = {
            "path": rel(STAGE10_FEATURE_LEDGER),
            "label_policy_final_r_by_policy_keys": sorted(
                (row.get("label_policy_final_r_by_policy") or {}).keys()
            ),
            "label_source": row.get("label_source"),
            "label_candidate_origin_family": row.get("label_candidate_origin_family"),
        }
        break
    return {
        "dynamic_policy_helper_path": rel(MOONSHOT_STAGE04_BUILDER),
        "stage10_feature_ledger_sample": feature_sample,
        "proof": (
            "path_hazard_early_failure is post-entry management state. The local ledgers "
            "provide policy labels after an entry candidate exists, but no independent "
            "entry geometry or candidate clock exists for this origin family."
        ),
    }


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated_at = utc_now()
    origins = non_current_origins()
    origin_map = {str(origin["name"]): origin for origin in origins}
    stage13_contracts = stage13_contract_by_origin()
    seed_rows = existing_seed_rows_by_family()
    rows: list[dict[str, Any]] = []
    family_summary: dict[str, dict[str, Any]] = {}
    source_counts = source_family_counts()
    market_map = read_json(MARKET_SOURCE_MAP)

    for family, origin in origin_map.items():
        all_seeds = list(seed_rows.get(family, []))
        generated_rows_available = sum(
            1 for row in all_seeds if row.get("generation_status") == "generated_executable_contract"
        )
        blocked_seed_rows = [row for row in all_seeds if row.get("generation_status") != "generated_executable_contract"]
        extra_generated_source = None

        if family == "nofill_reprice_reentry":
            all_seeds = [enrich_candidate_source_path(row) for row in pending_lifecycle_candidates(origin)]
            generated_rows_available = len(all_seeds)
            extra_generated_source = rel(PENDING_LIFECYCLE)
        elif family == "spread_liquidity_state_shift":
            all_seeds = [enrich_candidate_source_path(row) for row in spread_lifecycle_candidates(origin)]
            generated_rows_available = len(all_seeds)
            extra_generated_source = rel(PENDING_TICK_SPREAD)

        executable_seeds = [
            row
            for row in all_seeds
            if row.get("generation_status")
            in {
                "generated_executable_contract",
                "generated_executable_from_forward_pending_lifecycle",
                "generated_executable_from_joined_pending_tick_spread",
            }
        ]
        if family == "nofill_reprice_reentry":
            cap = None if FULL_REPLAY_MODE else MAX_PENDING_REPLAY_ROWS
        elif family == "spread_liquidity_state_shift":
            cap = None if FULL_REPLAY_MODE else MAX_SPREAD_REPLAY_ROWS
        else:
            cap = None if FULL_REPLAY_MODE else MAX_CONTRACT_REPLAY_ROWS_PER_FAMILY
        replay_seeds = executable_seeds if cap is None else executable_seeds[:cap]

        action_counts: Counter = Counter()
        proof_counts: Counter = Counter()
        policy_counts: Counter = Counter()
        policy_total_r: defaultdict[str, float] = defaultdict(float)
        terminal_counts: Counter = Counter()
        dynamic_replayed = 0

        for index, seed in enumerate(replay_seeds, start=1):
            replay_row = replay_seed_row(seed, origin=origin, sequence=index)
            rows.append(replay_row)
            action_counts[replay_row["action"]] += 1
            terminal = (replay_row.get("path_replay") or {}).get("terminal_outcome")
            if terminal:
                terminal_counts[str(terminal)] += 1
            policy_results = replay_row["dynamic_policy_replay"]["policy_results"]
            if policy_results:
                dynamic_replayed += 1
            for policy, result in policy_results.items():
                final_r = result.get("final_r")
                if final_r is not None:
                    policy_counts[policy] += 1
                    policy_total_r[policy] += float(final_r)

        if executable_seeds and cap is not None and len(executable_seeds) > len(replay_seeds):
            cap_row = proof_row(
                origin=origin,
                action="bounded_smoke_cap_applied",
                proof_class="audit_cap_not_full_replay",
                blocker=(
                    f"Executable source rows={len(executable_seeds)} exceeded deterministic cap={cap}; "
                    "summary is a bounded smoke/audit pass, not full replay."
                ),
                rows_blocked=len(executable_seeds) - len(replay_seeds),
                evidence={
                    "cap_constant": (
                        "MAX_PENDING_REPLAY_ROWS"
                        if family == "nofill_reprice_reentry"
                        else "MAX_SPREAD_REPLAY_ROWS"
                        if family == "spread_liquidity_state_shift"
                        else "MAX_CONTRACT_REPLAY_ROWS_PER_FAMILY"
                    ),
                    "full_replay_mode": FULL_REPLAY_MODE,
                    "candidate_source": extra_generated_source or rel(PRIOR_BROADER_CONTRACT_LEDGER),
                },
            )
            rows.append(cap_row)
            action_counts[cap_row["action"]] += 1
            proof_counts[cap_row["proof_class"]] += 1

        if blocked_seed_rows:
            blocker_counts = Counter(
                str(row.get("activation_ready_blocker_class") or row.get("blocker_class") or "unknown_blocker")
                for row in blocked_seed_rows
            )
            proof = proof_row(
                origin=origin,
                action="seed_rows_blocked_before_executable_replay",
                proof_class="seed_contract_non_executable_rows",
                blocker="Some prior broader-origin candidate contracts lacked executable entry geometry.",
                rows_blocked=len(blocked_seed_rows),
                evidence={
                    "seed_ledger_path": rel(PRIOR_BROADER_CONTRACT_LEDGER),
                    "blocker_class_counts": dict(sorted(blocker_counts.items())),
                    "sample_row_ids": [row.get("row_id") for row in blocked_seed_rows[:5]],
                },
            )
            rows.append(proof)
            action_counts[proof["action"]] += 1
            proof_counts[proof["proof_class"]] += 1

        if not executable_seeds:
            contract = stage13_contracts.get(family) or {}
            if family == "orderflow_depth_imbalance_proxy":
                proof = proof_row(
                    origin=origin,
                    action="exact_proof_no_executable_candidate_rows",
                    proof_class="source_contract_or_parser_missing_for_row_level_replay",
                    blocker=(
                        "Orderflow rows on disk are diagnostic/source-readiness rows and do not "
                        "carry entry/stop/target geometry or an executable candidate-clock parser."
                    ),
                    evidence=orderflow_proof_evidence(),
                )
            elif family == "news_volatility_reprice":
                proof = proof_row(
                    origin=origin,
                    action="exact_proof_no_executable_candidate_rows",
                    proof_class="no_executable_rows_generated_from_available_ohlc_context",
                    blocker=(
                        "Calendar rows are present, but this route has no executable news-event "
                        "entry/stop/target rule from repo-local data/code now."
                    ),
                    evidence=news_proof_evidence(),
                )
            elif family == "path_hazard_early_failure":
                proof = proof_row(
                    origin=origin,
                    action="exact_proof_not_first_class_entry_origin",
                    proof_class="dynamic_execution_family_requires_prior_entry_candidate",
                    blocker=(
                        "Path-hazard state is replayable only after an entry candidate exists; "
                        "the registry has no independent entry geometry for this origin family."
                    ),
                    evidence=path_hazard_proof_evidence(),
                )
            else:
                proof = proof_row(
                    origin=origin,
                    action="exact_proof_no_executable_candidate_rows",
                    proof_class=str(contract.get("proof_class") or "no_executable_seed_rows"),
                    blocker=str(
                        contract.get("exact_blocker")
                        or "No executable source-bound candidate rows were generated from repo-local data/code in this pass."
                    ),
                    evidence={
                        "stage13_origin_contract_ledger_path": rel(STAGE13_ORIGIN_CONTRACT_LEDGER),
                        "stage13_contract": contract,
                        "source_family_counts": dict(sorted(source_counts.items())),
                    },
                )
            rows.append(proof)
            action_counts[proof["action"]] += 1
            proof_counts[proof["proof_class"]] += 1

        expectancy = {
            policy: (
                policy_total_r[policy] / policy_counts[policy]
                if policy_counts[policy]
                else None
            )
            for policy in sorted(set(policy_counts) | {policy.name for policy in required_policy_manifest()})
        }
        family_summary[family] = {
            "category": origin.get("category"),
            "source_availability_status": origin.get("source_availability_status"),
            "action_counts": dict(sorted(action_counts.items())),
            "proof_class_counts": dict(sorted(proof_counts.items())),
            "candidate_seed_rows_available": len(all_seeds),
            "executable_candidate_rows_available": len(executable_seeds),
            "candidate_rows_generated_or_seeded": len(executable_seeds),
            "candidate_rows_replayed": len(replay_seeds),
            "dynamic_policy_rows_replayed": dynamic_replayed,
            "bounded_cap_applied": cap is not None and len(executable_seeds) > len(replay_seeds),
            "cap": cap,
            "terminal_outcome_counts": dict(sorted(terminal_counts.items())),
            "policy_counts": dict(sorted(policy_counts.items())),
            "policy_total_r": dict(sorted(policy_total_r.items())),
            "policy_expectancy_r": expectancy,
            "exact_blockers": [
                row["exact_blocker"]
                for row in rows
                if row.get("origin_family") == family and row.get("row_type") == "proof"
            ],
            "source_paths": sorted(
                {
                    str(row.get("source_path")).replace("\\", "/")
                    for row in all_seeds
                    if row.get("source_path")
                }
            )[:20],
        }

    action_counts_all = Counter(row.get("action") for row in rows)
    proof_counts_all = Counter(row.get("proof_class") for row in rows if row.get("proof_class"))
    summary = {
        "schema_version": "vnext_replacement_stage13_broader_origin_candidate_replay_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": generated_at,
        "scope": (
            "bounded_smoke_audit_pass"
            if not FULL_REPLAY_MODE
            else "full_replay_pass"
        ),
        "full_replay_mode": FULL_REPLAY_MODE,
        "cap_constants": {
            "MAX_CONTRACT_REPLAY_ROWS_PER_FAMILY": MAX_CONTRACT_REPLAY_ROWS_PER_FAMILY,
            "MAX_PENDING_REPLAY_ROWS": MAX_PENDING_REPLAY_ROWS,
            "MAX_SPREAD_REPLAY_ROWS": MAX_SPREAD_REPLAY_ROWS,
        },
        "non_current_origin_families_registered": sorted(origin_map),
        "family_count": len(origin_map),
        "families_with_dynamic_policy_replay": sorted(
            family for family, data in family_summary.items() if data["dynamic_policy_rows_replayed"] > 0
        ),
        "families_with_proof_only": sorted(
            family
            for family, data in family_summary.items()
            if data["candidate_rows_replayed"] == 0
        ),
        "ledger_path": rel(OUTPUT_LEDGER),
        "summary_path": rel(OUTPUT_SUMMARY),
        "row_counts": {
            "ledger_rows": len(rows),
            "candidate_replay_rows": sum(1 for row in rows if row.get("row_type") == "candidate_replay"),
            "proof_rows": sum(1 for row in rows if row.get("row_type") == "proof"),
            "candidate_rows_replayed": sum(
                data["candidate_rows_replayed"] for data in family_summary.values()
            ),
            "dynamic_policy_rows_replayed": sum(
                data["dynamic_policy_rows_replayed"] for data in family_summary.values()
            ),
            "candidate_rows_generated_or_seeded": sum(
                data["candidate_rows_generated_or_seeded"] for data in family_summary.values()
            ),
        },
        "action_counts": dict(sorted(action_counts_all.items())),
        "proof_class_counts": dict(sorted(proof_counts_all.items())),
        "family_summary": family_summary,
        "market_source_map_evidence": {
            "path": rel(MARKET_SOURCE_MAP),
            "activation_status_counts": market_map.get("activation_status_counts"),
            "market_activation_class_counts": market_map.get("market_activation_class_counts"),
            "broker_native_activation_eligible_symbols": market_map.get(
                "broker_native_activation_eligible_symbols"
            ),
        },
        "paths_read": read_paths_audit(),
        "source_capability_summary": read_json(SOURCE_CAPABILITY_SUMMARY),
        "stage13_full_moonshot_summary_extract": {
            key: read_json(STAGE13_BRANCH_SUMMARY).get(key)
            for key in [
                "candidate_rows_scanned",
                "executable_except_branch_rows",
                "non_current_origin_activation_summary",
                "origin_contract_proof_counts",
                "final_repair_action",
            ]
        },
        "no_live_trading_or_broker_mutation": True,
    }
    return rows, summary


def main() -> None:
    rows, summary = build_rows()
    with OUTPUT_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    write_json(OUTPUT_SUMMARY, summary)
    print(
        json.dumps(
            {
                "status": "ok",
                "ledger_path": rel(OUTPUT_LEDGER),
                "summary_path": rel(OUTPUT_SUMMARY),
                "ledger_rows": summary["row_counts"]["ledger_rows"],
                "dynamic_policy_rows_replayed": summary["row_counts"]["dynamic_policy_rows_replayed"],
                "scope": summary["scope"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

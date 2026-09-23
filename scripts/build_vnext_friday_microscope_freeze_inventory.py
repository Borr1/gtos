"""Build the Friday microscope freeze window and source inventory.

This route builder is offline/read-only. It reads local trade records, shadow
logs, route artifacts, data directories, git history, and current config/code.
It does not call MT5 order APIs and does not mutate broker state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_vnext_weekend_live_forensic_ledgers as weekend_forensics


ROUTE_ID = "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID
COMPANION_DIR = ROOT / "research" / "operations" / "vnext_live_activation_active_repair_companion_2026_05_28"
ACTIVATION_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
)

CRYPTO_SYMBOLS = {"BTCUSD", "ETHUSD"}
ACTIVE_SYMBOLS = weekend_forensics.EXPECTED_SYMBOLS
NON_CRYPTO_SYMBOLS = [symbol for symbol in ACTIVE_SYMBOLS if symbol not in CRYPTO_SYMBOLS]
PLACED_OUTCOME = "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN"

FRIDAY_CLOSE_BATCH_UTC = datetime(2026, 5, 29, 21, 0, tzinfo=timezone.utc)
BROAD_SOURCE_START_UTC = datetime(2026, 5, 28, 0, 0, tzinfo=timezone.utc)
BROAD_SOURCE_END_UTC = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)

STATE_PATH = ROUTE_DIR / "FRIDAY_MICROSCOPE_ROUTE_STATE.json"
CONTROL_LEDGER = ROUTE_DIR / "FRIDAY_MICROSCOPE_CONTROL_LEDGER.jsonl"
CONTEXT_ANCHOR = ROUTE_DIR / "FRIDAY_MICROSCOPE_CONTEXT_ANCHOR.md"
OUTPUT_MANIFEST = ROUTE_DIR / "FRIDAY_MICROSCOPE_OUTPUT_MANIFEST.json"
REPAIR_LEDGER = ROUTE_DIR / "FRIDAY_MICROSCOPE_REPAIR_LEDGER.jsonl"
COMPLETION_AUDIT = ROUTE_DIR / "FRIDAY_MICROSCOPE_COMPLETION_AUDIT.json"
FINAL_REPORT = ROUTE_DIR / "FRIDAY_MICROSCOPE_FINAL_REPORT.md"

FREEZE_SOURCE_WINDOW = ROUTE_DIR / "FRIDAY_FREEZE_SOURCE_WINDOW.json"
FREEZE_EVENT_INVENTORY = ROUTE_DIR / "FRIDAY_FREEZE_EVENT_SOURCE_INVENTORY.jsonl"
FREEZE_CODE_RELOAD_TIMELINE = ROUTE_DIR / "FRIDAY_FREEZE_CODE_RELOAD_TIMELINE.jsonl"
FREEZE_DENOMINATOR_SUMMARY = ROUTE_DIR / "FRIDAY_FREEZE_DENOMINATOR_SUMMARY.json"
CRYPTO_EXCLUSION_SUMMARY = ROUTE_DIR / "FRIDAY_CRYPTO_EXCLUSION_SUMMARY.json"

SOURCE_COVERAGE_LEDGER = ROUTE_DIR / "FRIDAY_SOURCE_COVERAGE_LEDGER.jsonl"
SOURCE_SCHEMA_LEDGER = ROUTE_DIR / "FRIDAY_SOURCE_SCHEMA_LEDGER.jsonl"
SOURCE_GAP_LEDGER = ROUTE_DIR / "FRIDAY_SOURCE_GAP_LEDGER.jsonl"
SOURCE_HASH_MANIFEST = ROUTE_DIR / "FRIDAY_SOURCE_HASH_MANIFEST.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat()


def parse_dt(value: Any) -> datetime | None:
    return weekend_forensics.parse_dt(value)


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def git_log_rows() -> list[dict[str, Any]]:
    try:
        output = subprocess.check_output(
            ["git", "log", "--date=iso-strict", "--pretty=%H%x09%cd%x09%s", "-n", "80"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return []
    rows: list[dict[str, Any]] = []
    for line in output.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        sha, date_text, subject = parts
        dt = parse_dt(date_text)
        rows.append(
            {
                "event_type": "git_commit",
                "timestamp_utc": iso(dt),
                "head": sha,
                "head_short": sha[:9],
                "subject": subject,
                "source": "git log --date=iso-strict -n 80",
            }
        )
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def load_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                row = {"_decode_error": True, "_raw_prefix": text[:250]}
            row["_source_path"] = str(path)
            row["_source_line"] = line_no
            rows.append(row)
            if limit is not None and len(rows) >= limit:
                break
    return rows


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def line_count(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    count = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            count += chunk.count(b"\n")
    return count


def safe_stat(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    stat = path.stat()
    return {
        "exists": True,
        "path": str(path),
        "size_bytes": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "kind": "directory" if path.is_dir() else "file",
    }


def directory_listing_signature(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    file_count = 0
    total_bytes = 0
    digest_rows: list[str] = []
    for child in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = child.relative_to(ROOT).as_posix()
        stat = child.stat()
        file_count += 1
        total_bytes += stat.st_size
        digest_rows.append(f"{rel}\t{stat.st_size}\t{int(stat.st_mtime)}")
    return {
        "exists": True,
        "path": str(path),
        "file_count": file_count,
        "total_bytes": total_bytes,
        "directory_listing_sha256": sha256_text("\n".join(digest_rows)),
    }


def event_time(row: dict[str, Any]) -> datetime | None:
    return parse_dt(
        row.get("candle_time_utc")
        or row.get("record_time_utc")
        or row.get("timestamp_utc")
        or row.get("source_time_utc")
    )


def normalize_origin(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value)
    if text.startswith("origin_"):
        return text[len("origin_") :]
    return text


def load_trade_events() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records, malformed = weekend_forensics.load_trade_records(BROAD_SOURCE_START_UTC, BROAD_SOURCE_END_UTC)
    events = [weekend_forensics.event_row(record) for record in records]
    for event in events:
        event["origin_family_normalized"] = normalize_origin(event.get("origin_family"))
    return events, malformed


def lifecycle_timestamp(row: dict[str, Any]) -> datetime | None:
    for key in (
        "timestamp_utc",
        "fill_time_utc",
        "order_send_time_utc",
        "time_done_utc",
        "time_setup_utc",
        "created_at_utc",
        "recorded_at_utc",
    ):
        dt = parse_dt(row.get(key))
        if dt is not None:
            return dt
    return None


def load_lifecycle_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in (
        ROOT / "shadow_logs" / "pending_limit_lifecycle.jsonl",
        ROOT / "shadow_logs" / "slippage.jsonl",
        COMPANION_DIR / "LIVE_WEEKEND_ORDER_RECONCILIATION_LEDGER.jsonl",
        COMPANION_DIR / "LIVE_WEEKEND_PLACED_TRADE_BROKER_AUTOPSY_LEDGER.jsonl",
    ):
        for row in load_jsonl(path):
            row["_source_path"] = str(path)
            rows.append(row)
    return rows


def lifecycle_match_index(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        keys = {
            row.get("candidate_id"),
            row.get("trade_id"),
            row.get("mt5_entry_order_ticket"),
            row.get("mt5_position_ticket"),
            row.get("order"),
            row.get("position_id"),
            row.get("ticket"),
        }
        for event in row.get("lifecycle_events") or []:
            if isinstance(event, dict):
                keys.update(
                    {
                        event.get("candidate_id"),
                        event.get("trade_id"),
                        event.get("mt5_entry_order_ticket"),
                        event.get("mt5_position_ticket"),
                        event.get("order"),
                        event.get("position_id"),
                        event.get("ticket"),
                    }
                )
        for key in keys:
            if key not in (None, ""):
                index[str(key)].append(row)
    return index


def first_placed_event(events: list[dict[str, Any]], lifecycle_rows: list[dict[str, Any]]) -> dict[str, Any]:
    placed = [row for row in events if row.get("outcome") == PLACED_OUTCOME]
    lifecycle_index = lifecycle_match_index(lifecycle_rows)
    candidates: list[dict[str, Any]] = []
    for row in placed:
        matches: list[dict[str, Any]] = []
        for key in (row.get("candidate_id"), row.get("trade_id")):
            if key not in (None, ""):
                matches.extend(lifecycle_index.get(str(key), []))
        match_times = [lifecycle_timestamp(match) for match in matches]
        match_times = [dt for dt in match_times if dt is not None]
        candidate_candle = event_time(row)
        actual_order_time = min(match_times) if match_times else candidate_candle
        candidates.append(
            {
                "symbol": row.get("symbol"),
                "broker_symbol": row.get("broker_symbol"),
                "candidate_id": row.get("candidate_id"),
                "trade_id": row.get("trade_id"),
                "side": row.get("side"),
                "candidate_candle_time_utc": iso(candidate_candle),
                "actual_order_time_utc": iso(actual_order_time),
                "actual_time_source": "pending_lifecycle_or_companion_match" if match_times else "trade_record_candle_time_fallback",
                "matched_lifecycle_rows": len(matches),
                "source_path": row.get("source_path"),
                "_sort_dt": actual_order_time or candidate_candle or datetime.max.replace(tzinfo=timezone.utc),
            }
        )
    if not candidates:
        return {
            "status": "missing_first_placed_order",
            "source_gap": "no LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN rows found in broad source window",
        }
    candidates.sort(key=lambda item: item["_sort_dt"])
    first = candidates[0]
    first.pop("_sort_dt", None)
    first["status"] = "found"
    first["placed_order_count_broad_window"] = len(placed)
    return first


def classify_event(row: dict[str, Any], start: datetime, close_exclusive: datetime) -> dict[str, Any]:
    symbol = str(row.get("symbol") or "")
    t = event_time(row)
    reasons: list[str] = []
    primary = True
    if row.get("outcome") == "NON_CANDIDATE_PENDING_RECORD_INDEX":
        primary = False
        reasons.append("non_candidate_pending_record_index_metadata")
    if t is None:
        primary = False
        reasons.append("missing_event_time")
    elif t < start:
        primary = False
        reasons.append("pre_first_placed_trade_candidate")
    elif t >= close_exclusive:
        primary = False
        if t == close_exclusive:
            reasons.append("friday_21_00_utc_spread_close_batch_excluded_primary_boundary")
        else:
            reasons.append("post_friday_close_or_weekend_current_day_noise")
    if symbol in CRYPTO_SYMBOLS:
        primary = False
        reasons.append("crypto_excluded_primary_different_market_hours_no_placed_trades")
    if primary:
        reasons.append("primary_non_crypto_friday_execution_era")
    return {
        "schema_version": "friday_freeze_event_source_inventory_v1",
        "symbol": symbol,
        "broker_symbol": row.get("broker_symbol"),
        "candidate_id": row.get("candidate_id"),
        "trade_id": row.get("trade_id"),
        "side": row.get("side"),
        "candle_time_utc": row.get("candle_time_utc"),
        "record_time_utc": row.get("record_time_utc"),
        "timestamp_basis_utc": iso(t),
        "timestamp_basis_field": "candle_time_utc_or_record_time_utc",
        "origin_family": row.get("origin_family"),
        "origin_family_normalized": row.get("origin_family_normalized"),
        "session": row.get("route_session") or row.get("session") or row.get("kill_zone"),
        "outcome": row.get("outcome"),
        "terminal_state": row.get("terminal_state"),
        "gate1_denial_reason": row.get("gate1_denial_reason"),
        "gate3_denial_reason": row.get("gate3_denial_reason"),
        "selected_policy": row.get("selected_policy"),
        "execution_policy_id": row.get("execution_policy_id"),
        "selected_cell_risk_pct": row.get("selected_cell_risk_pct"),
        "selected_cell_risk_cell_id": row.get("selected_cell_risk_cell_id"),
        "primary_friday_denominator": primary,
        "freeze_disposition": "included_primary" if primary else "excluded_primary",
        "freeze_reasons": reasons,
        "source_path": row.get("source_path"),
    }


def source_kind_for_path(path: Path) -> str:
    text = path.as_posix()
    if "knowledge_base/trade_records" in text:
        return "trade_record_candidate_source"
    if "shadow_logs" in text:
        return "runtime_shadow_log"
    if "data/ticks" in text:
        return "tick_market_data"
    if "data/m1" in text:
        return "m1_market_data"
    if "vnext_live_activation_active_repair_companion" in text:
        return "derived_hot_companion_route_artifact"
    if "vnext_moonshot_production_replacement_activation_repair_hardening" in text:
        return "selected_system_replay_artifact"
    if text.startswith("config/"):
        return "current_config"
    if text.startswith("src/"):
        return "current_runtime_code"
    if text.startswith("tests/"):
        return "current_test"
    return "local_source"


def classify_authority(path: Path) -> str:
    text = path.as_posix()
    if "knowledge_base/trade_records" in text or "shadow_logs" in text:
        return "authoritative_for_logged_live_event_class"
    if "data/ticks" in text or "data/m1" in text:
        return "authoritative_for_local_market_path_when_available"
    if "LIVE_WEEKEND" in text:
        return "derived_contaminated_weekend_artifact_source_only"
    if "final_dynamic_router" in text or "momentum_policy" in text or "selected_policy_risk" in text:
        return "authoritative_for_broad_selected_replay_denominator"
    if text.startswith("src/") or text.startswith("config/"):
        return "current_head_runtime_surface"
    return "supporting_local_evidence"


def material_source_paths() -> list[Path]:
    paths = [
        ROOT / ".context" / "LIVE_STATE.md",
        ROOT / ".context" / "00_core" / "current_vnext_system_map.md",
        ROOT / ".context" / "00_core" / "current_repo_reading_order.md",
        ROOT / ".context" / "00_core" / "quick_reference_card.md",
        ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
        ROOT / ".context" / "00_core" / "goal_session_research_discipline.md",
        ROOT / "research" / "science_program_2026_05" / "04_goal_prompts" / "VNEXT_FRIDAY_MICROSCOPIC_LIVE_FORENSICS_MOONSHOT_REPAIR_GOAL_PROMPT_2026-05-31.md",
        ROOT / "research" / "science_program_2026_05" / "04_goal_prompts" / "VNEXT_FRIDAY_MICROSCOPIC_LIVE_FORENSICS_MOONSHOT_REPAIR_STARTER_2026-05-31.txt",
        COMPANION_DIR / "ACTIVE_REPAIR_STATE.json",
        COMPANION_DIR / "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json",
        COMPANION_DIR / "LIVE_WEEKEND_FORENSIC_FUNNEL_SUMMARY.json",
        COMPANION_DIR / "LIVE_WEEKEND_FORENSIC_EVENT_LEDGER.jsonl",
        COMPANION_DIR / "LIVE_WEEKEND_ORDER_RECONCILIATION_LEDGER.jsonl",
        COMPANION_DIR / "LIVE_WEEKEND_CANDIDATE_PRICE_ACTION_ANATOMY_LEDGER.jsonl",
        COMPANION_DIR / "LIVE_WEEKEND_PLACED_TRADE_BROKER_AUTOPSY_LEDGER.jsonl",
        COMPANION_DIR / "LIVE_WEEKEND_EXECUTION_POLICY_TOURNAMENT_SUMMARY.json",
        COMPANION_DIR / "LIVE_WEEKEND_CANDIDATE_QUALITY_SELECTOR_LEDGER.jsonl",
        ACTIVATION_DIR / "VNEXT_ACTIVATION_REPAIR_STAGE06_FINAL_ROUTE_STATE_2026-05-27.json",
        ACTIVATION_DIR / "ei15r" / "final_dynamic_router_replay_summary.json",
        ACTIVATION_DIR / "ei15r" / "final_dynamic_router_replay.manifest.jsonl",
        ACTIVATION_DIR / "ei15r" / "momentum_policy_promotion_summary.json",
        ACTIVATION_DIR / "ei15r" / "selected_policy_risk_proof_summary.json",
        ROOT / "shadow_logs" / "pending_limit_lifecycle.jsonl",
        ROOT / "shadow_logs" / "slippage.jsonl",
        ROOT / "shadow_logs" / "account_truth_reconciliation_status.jsonl",
        ROOT / "shadow_logs" / "gtos_vnext_runtime_decisions.jsonl",
        ROOT / "shadow_logs" / "gtos_vnext_replacement_monitoring.jsonl",
        ROOT / "pipeline_state" / "m1_capture_state.json",
        ROOT / "config" / "agent_config.yaml",
        ROOT / "src" / "components" / "permissions.py",
        ROOT / "src" / "components" / "orchestrator.py",
        ROOT / "src" / "components" / "gtos_vnext_runtime.py",
        ROOT / "src" / "research" / "moonshot_default_off_policy_router.py",
        ROOT / "tests" / "test_moonshot_candidate_quality_selector.py",
        ROOT / "tests" / "test_vnext_weekend_execution_policy_tournament.py",
    ]
    return paths


def build_source_ledgers(events: list[dict[str, Any]], malformed: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    coverage_rows: list[dict[str, Any]] = []
    schema_rows: list[dict[str, Any]] = []
    gap_rows: list[dict[str, Any]] = []
    hash_entries: list[dict[str, Any]] = []

    source_paths = material_source_paths()
    for path in source_paths:
        rel = path.relative_to(ROOT).as_posix() if path.exists() and path.is_file() else path.as_posix()
        row = {
            "schema_version": "friday_source_coverage_v1",
            "path": rel,
            "source_kind": source_kind_for_path(path.relative_to(ROOT) if path.exists() and path.is_file() else path),
            "authority_class": classify_authority(path.relative_to(ROOT) if path.exists() and path.is_file() else path),
            **safe_stat(path),
        }
        if path.exists() and path.is_file():
            if path.suffix.lower() == ".jsonl":
                row["row_count"] = line_count(path)
            if path.stat().st_size <= 128 * 1024 * 1024:
                digest = sha256_file(path)
                row["sha256"] = digest
                hash_entries.append(
                    {
                        "path": rel,
                        "hash_type": "file_sha256",
                        "sha256": digest,
                        "size_bytes": path.stat().st_size,
                    }
                )
            sample = first_json_row(path)
            if sample is not None:
                schema_rows.append(schema_row(path, sample))
        else:
            gap_rows.append(
                {
                    "schema_version": "friday_source_gap_v1",
                    "path": rel,
                    "gap_class": "material_source_missing_on_current_disk",
                    "impact": "route must use alternate source or record exact blocker before relying on this class",
                }
            )
        coverage_rows.append(row)

    for directory in (
        ROOT / "knowledge_base" / "trade_records",
        ROOT / "data" / "ticks",
        ROOT / "data" / "m1",
        ROOT / "pipeline_state",
    ):
        sig = directory_listing_signature(directory)
        rel = directory.relative_to(ROOT).as_posix()
        coverage_rows.append(
            {
                "schema_version": "friday_source_coverage_v1",
                "path": rel,
                "source_kind": source_kind_for_path(directory.relative_to(ROOT)),
                "authority_class": classify_authority(directory.relative_to(ROOT)),
                **sig,
            }
        )
        hash_entries.append({"path": rel, "hash_type": "directory_listing_sha256", **sig})

    event_times = [event_time(row) for row in events]
    event_times = [dt for dt in event_times if dt is not None]
    coverage_rows.append(
        {
            "schema_version": "friday_source_coverage_v1",
            "path": "knowledge_base/trade_records/**/*.json",
            "source_kind": "trade_record_candidate_source",
            "authority_class": "authoritative_for_logged_live_candidate_rows",
            "row_count": len(events),
            "malformed_count": len(malformed),
            "timestamp_min_utc": iso(min(event_times) if event_times else None),
            "timestamp_max_utc": iso(max(event_times) if event_times else None),
            "symbol_counts": dict(sorted(Counter(str(row.get("symbol")) for row in events).items())),
            "outcome_counts": dict(sorted(Counter(str(row.get("outcome")) for row in events).items())),
        }
    )

    for symbol in ACTIVE_SYMBOLS:
        for root_name, base, extension in (
            ("data/ticks", ROOT / "data" / "ticks" / symbol, ".parquet"),
            ("data/m1", ROOT / "data" / "m1" / symbol, ".csv"),
        ):
            day_files = [base / f"2026-05-28{extension}", base / f"2026-05-29{extension}"]
            missing = [path.relative_to(ROOT).as_posix() for path in day_files if not path.exists()]
            if missing:
                gap_rows.append(
                    {
                        "schema_version": "friday_source_gap_v1",
                        "symbol": symbol,
                        "path": f"{root_name}/{symbol}",
                        "gap_class": "friday_market_data_day_file_missing",
                        "missing_files": missing,
                        "primary_denominator_impact": "crypto_appendix" if symbol in CRYPTO_SYMBOLS else "primary_non_crypto_path_resolution_gap_if_candidate_present",
                    }
                )

    if not gap_rows:
        gap_rows.append(
            {
                "schema_version": "friday_source_gap_v1",
                "gap_class": "no_stage_01_02_material_source_gaps_detected",
                "impact": "later stages must still record row-level broker/history/path gaps where discovered",
            }
        )

    return coverage_rows, schema_rows, gap_rows, {
        "schema_version": "friday_source_hash_manifest_v1",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "git_head": git_head(),
        "hash_entries": hash_entries,
    }


def first_json_row(path: Path) -> dict[str, Any] | None:
    try:
        if path.suffix.lower() == ".json":
            data = load_json(path)
            return data if isinstance(data, dict) else {"root_type": type(data).__name__}
        if path.suffix.lower() == ".jsonl":
            rows = load_jsonl(path, limit=1)
            return rows[0] if rows else None
    except Exception:
        return None
    return None


def schema_row(path: Path, sample: dict[str, Any]) -> dict[str, Any]:
    keys = sorted(str(key) for key in sample.keys() if not str(key).startswith("_"))
    nested = {
        str(key): sorted(str(nested_key) for nested_key in value.keys())
        for key, value in sample.items()
        if isinstance(value, dict)
    }
    return {
        "schema_version": "friday_source_schema_v1",
        "path": path.relative_to(ROOT).as_posix(),
        "top_level_key_count": len(keys),
        "top_level_keys": keys[:200],
        "nested_key_samples": nested,
        "sample_source": "first_json_or_jsonl_row",
    }


def build_code_reload_timeline(first_order: dict[str, Any]) -> list[dict[str, Any]]:
    rows = git_log_rows()
    for path in (COMPANION_DIR / "ACTIVE_REPAIR_LEDGER.jsonl", COMPANION_DIR / "ACTIVE_REPAIR_STATE.json"):
        if not path.exists():
            continue
        if path.suffix == ".jsonl":
            for row in load_jsonl(path):
                timestamp = parse_dt(row.get("updated_at") or row.get("generated_at_utc") or row.get("timestamp_utc"))
                rows.append(
                    {
                        "event_type": "active_repair_ledger",
                        "timestamp_utc": iso(timestamp),
                        "source": path.relative_to(ROOT).as_posix(),
                        "route_status": row.get("status"),
                        "stage": row.get("stage") or row.get("current_focus"),
                        "head": row.get("head") or row.get("current_head") or row.get("git_head"),
                    }
                )
        else:
            data = load_json(path)
            rows.append(
                {
                    "event_type": "active_repair_state_snapshot",
                    "timestamp_utc": data.get("updated_at"),
                    "source": path.relative_to(ROOT).as_posix(),
                    "route_status": data.get("status"),
                    "current_focus": data.get("current_focus"),
                    "head": (data.get("current_head") or {}).get("head") if isinstance(data.get("current_head"), dict) else data.get("current_head"),
                }
            )
    first_actual = parse_dt(first_order.get("actual_order_time_utc"))
    for row in rows:
        row["relative_to_first_actual_order"] = (
            "before_or_at_first_actual_order"
            if first_actual and parse_dt(row.get("timestamp_utc")) and parse_dt(row.get("timestamp_utc")) <= first_actual
            else "after_first_actual_order_or_unordered"
        )
    rows.sort(key=lambda row: row.get("timestamp_utc") or "")
    return rows


def build_denominator_summary(inventory: list[dict[str, Any]], freeze_start: datetime) -> dict[str, Any]:
    primary = [row for row in inventory if row["primary_friday_denominator"]]
    crypto = [row for row in inventory if row["symbol"] in CRYPTO_SYMBOLS]
    close_batch = [
        row
        for row in inventory
        if parse_dt(row.get("timestamp_basis_utc")) == FRIDAY_CLOSE_BATCH_UTC
        and row.get("symbol") not in CRYPTO_SYMBOLS
    ]
    before_close_including_batch = [
        row
        for row in inventory
        if row.get("symbol") not in CRYPTO_SYMBOLS
        and row.get("outcome") != "NON_CANDIDATE_PENDING_RECORD_INDEX"
        and (dt := parse_dt(row.get("timestamp_basis_utc"))) is not None
        and freeze_start <= dt <= FRIDAY_CLOSE_BATCH_UTC
    ]
    return {
        "schema_version": "friday_freeze_denominator_summary_v1",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "git_head": git_head(),
        "freeze_start_inclusive_utc": iso(freeze_start),
        "freeze_end_exclusive_utc": iso(FRIDAY_CLOSE_BATCH_UTC),
        "primary_boundary_rule": "include non-crypto rows with timestamp_basis_utc >= first placed candidate candle and < 2026-05-29T21:00:00Z; exclude exactly-21:00 spread-close batch from primary denominator and preserve it as close-spread evidence",
        "primary_non_crypto_rows": len(primary),
        "non_crypto_rows_including_21_00_batch": len(before_close_including_batch),
        "friday_21_00_close_batch_rows": len(close_batch),
        "crypto_rows_broad_window": len(crypto),
        "all_inventory_rows": len(inventory),
        "primary_outcome_counts": dict(sorted(Counter(row.get("outcome") for row in primary).items())),
        "primary_terminal_state_counts": dict(sorted(Counter(row.get("terminal_state") for row in primary).items())),
        "primary_symbol_counts": dict(sorted(Counter(row.get("symbol") for row in primary).items())),
        "primary_placed_symbol_counts": dict(
            sorted(Counter(row.get("symbol") for row in primary if row.get("outcome") == PLACED_OUTCOME).items())
        ),
        "close_batch_outcome_counts": dict(sorted(Counter(row.get("outcome") for row in close_batch).items())),
        "close_batch_gate3_reason_counts": dict(sorted(Counter(row.get("gate3_denial_reason") for row in close_batch).items())),
        "excluded_reason_counts": dict(
            sorted(
                Counter(reason for row in inventory if not row["primary_friday_denominator"] for reason in row["freeze_reasons"]).items()
            )
        ),
    }


def build_crypto_summary(inventory: list[dict[str, Any]]) -> dict[str, Any]:
    crypto = [row for row in inventory if row["symbol"] in CRYPTO_SYMBOLS]
    return {
        "schema_version": "friday_crypto_exclusion_summary_v1",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "excluded_symbols": sorted(CRYPTO_SYMBOLS),
        "primary_scope_decision": "excluded_from_primary_friday_execution_era_denominator",
        "reason": "BTCUSD/ETHUSD have different market-hours behavior and no placed trades in this local Friday live slice; rows are preserved only as appendix/source evidence.",
        "crypto_rows": len(crypto),
        "placed_orders": sum(1 for row in crypto if row.get("outcome") == PLACED_OUTCOME),
        "symbol_counts": dict(sorted(Counter(row.get("symbol") for row in crypto).items())),
        "outcome_counts": dict(sorted(Counter(row.get("outcome") for row in crypto).items())),
        "timestamp_min_utc": min((row.get("timestamp_basis_utc") for row in crypto if row.get("timestamp_basis_utc")), default=None),
        "timestamp_max_utc": max((row.get("timestamp_basis_utc") for row in crypto if row.get("timestamp_basis_utc")), default=None),
    }


def build_source_window(first_order: dict[str, Any], freeze_start: datetime, denominator_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "friday_freeze_source_window_v1",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "git_head": git_head(),
        "first_placed_order": first_order,
        "source_window": {
            "broad_source_start_utc": iso(BROAD_SOURCE_START_UTC),
            "broad_source_end_utc": iso(BROAD_SOURCE_END_UTC),
            "primary_start_inclusive_utc": iso(freeze_start),
            "primary_end_exclusive_utc": iso(FRIDAY_CLOSE_BATCH_UTC),
            "friday_close_batch_boundary_utc": iso(FRIDAY_CLOSE_BATCH_UTC),
            "primary_symbol_scope": "non_crypto_only",
            "excluded_primary_symbols": sorted(CRYPTO_SYMBOLS),
        },
        "freeze_rule": denominator_summary["primary_boundary_rule"],
        "row_count_summary": {
            "primary_non_crypto_rows": denominator_summary["primary_non_crypto_rows"],
            "non_crypto_rows_including_21_00_batch": denominator_summary["non_crypto_rows_including_21_00_batch"],
            "friday_21_00_close_batch_rows": denominator_summary["friday_21_00_close_batch_rows"],
            "crypto_rows_broad_window": denominator_summary["crypto_rows_broad_window"],
        },
    }


def output_manifest(paths: list[Path]) -> dict[str, Any]:
    outputs = []
    for path in paths:
        stat = safe_stat(path)
        row: dict[str, Any] = {
            "path": path.relative_to(ROOT).as_posix(),
            **stat,
        }
        if path.exists() and path.is_file():
            row["sha256"] = sha256_file(path)
            if path.suffix.lower() == ".jsonl":
                row["row_count"] = line_count(path)
        outputs.append(row)
    return {
        "schema_version": "friday_microscope_output_manifest_v1",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "git_head": git_head(),
        "outputs": outputs,
    }


def build_route_state(first_order: dict[str, Any], denominator_summary: dict[str, Any], outputs: list[Path]) -> dict[str, Any]:
    return {
        "schema_version": "friday_microscope_route_state_v1",
        "route_id": ROUTE_ID,
        "updated_at_utc": utc_now(),
        "current_stage": "stage_01_02_freeze_and_source_inventory_initialized",
        "current_head": git_head(),
        "source_window": {
            "primary_start_inclusive_utc": denominator_summary["freeze_start_inclusive_utc"],
            "primary_end_exclusive_utc": denominator_summary["freeze_end_exclusive_utc"],
            "freeze_rule": denominator_summary["primary_boundary_rule"],
        },
        "first_placed_order": first_order,
        "active_question_stack": [
            "prove Friday close boundary from broker/session/spread evidence beyond the provisional exact-21:00 batch classification",
            "join every primary Friday row to full vNext selected denominator and selected-cell risk/broker-ready state",
            "autopsy all placed orders against broker truth, lifecycle, cost, commission, swap, slippage, and manual status",
            "repair or remove contaminated weekend-derived quality selector after clean Friday and broad selected replay audit",
            "repair stale account-exposure/concurrency/same-symbol/cost logging defects found by row-level evidence",
        ],
        "subagent_assignments": {
            "freeze_window_source_inventory": "019e7d6b-d237-7e02-b774-1dfdf193f904",
            "trade_order_fill_broker_lifecycle": "019e7d6b-d31b-70f3-bdb9-e87ac609fa8f",
            "full_vnext_selected_replay_bridge": "019e7d6b-d402-7ca2-83ce-b2f47dc9dd06",
            "code_surface_stale_behavior": "019e7d6b-d53e-7761-923b-babbd44af604",
            "price_action_source_availability": "019e7d6b-d699-7b30-a274-fc6b7606c40e",
        },
        "searched_roots": [
            "research/operations/vnext_live_activation_active_repair_companion_2026_05_28",
            "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27",
            "shadow_logs",
            "pipeline_state",
            "knowledge_base/trade_records",
            "data/ticks",
            "data/m1",
            "config",
            "src",
            "tests",
            "git log",
        ],
        "finished_artifacts": [path.relative_to(ROOT).as_posix() for path in outputs],
        "open_defects": [
            {
                "defect_id": "FRIDAY_QUALITY_SELECTOR_CONTAMINATED_WEEKEND_SOURCE_REQUIRES_CLEAN_REPLAY_DECISION",
                "status": "open_source_replay_required",
                "evidence": "config enables moonshot_candidate_quality_selector_apply_to_execution using LIVE_WEEKEND_EXECUTION_POLICY_TOURNAMENT_SUMMARY.json",
            },
            {
                "defect_id": "FRIDAY_FULL_SELECTED_DENOMINATOR_JOIN_NOT_BUILT_YET",
                "status": "open_stage_04_required",
                "evidence": "Stage 01/02 freeze now isolates primary rows; Stage 04 join builder still required",
            },
        ],
        "repaired_defects": [],
        "tests_run": [],
        "current_blockers": [],
        "exact_next_action": "Build canonical Friday event ledger plus raw-vs-selected denominator bridge using the clean freeze inventory.",
    }


def build_completion_audit(denominator_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "friday_microscope_completion_audit_v1",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "status": "not_complete",
        "completed_requirements": [
            "mandatory preflight refreshed by parent session before builder run",
            "route directory created",
            "Stage 01 initial clean Friday freeze artifacts built",
            "Stage 02 initial source inventory, schema, gaps, and hash manifest built",
        ],
        "unmet_requirements": [
            "canonical event ledger",
            "full vNext selected-system replay and raw-vs-selected denominator reconciliation",
            "microscopic tick/M1/M15/D1-H4-H1 price-action anatomy for every primary row",
            "placed-trade broker truth autopsy",
            "refusal/stale-blocker dispositions",
            "market coverage/starvation explanation",
            "execution-policy selected/broker-ready replay",
            "quality selector broad replay decision",
            "account-exposure risk/concurrency/same-symbol/cost repairs",
            "all focused tests/verifiers and scoped commits",
            "final report",
        ],
        "primary_non_crypto_rows_current": denominator_summary["primary_non_crypto_rows"],
        "completion_decision": "keep_goal_active",
    }


def render_context_anchor(source_window: dict[str, Any], denominator_summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Friday Microscope Context Anchor",
            "",
            f"Route id: `{ROUTE_ID}`",
            f"Updated UTC: `{utc_now()}`",
            f"HEAD: `{git_head()}`",
            "",
            "## Scope",
            "",
            "Offline vNext Friday live-forensics and repair route. Do not restart live trading or mutate broker orders/positions.",
            "",
            "## Freeze",
            "",
            f"- Primary start inclusive: `{source_window['source_window']['primary_start_inclusive_utc']}`",
            f"- Primary end exclusive: `{source_window['source_window']['primary_end_exclusive_utc']}`",
            "- Primary symbols: non-crypto vNext surface.",
            f"- Primary rows: `{denominator_summary['primary_non_crypto_rows']}`",
            f"- 21:00 UTC close-spread batch rows excluded from primary: `{denominator_summary['friday_21_00_close_batch_rows']}`",
            "",
            "## Current Next Action",
            "",
            "Build the canonical event ledger and raw-vs-selected vNext denominator reconciliation from this freeze.",
            "",
        ]
    )


def render_final_report_stub(denominator_summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Friday Microscope Final Report",
            "",
            "Status: not complete.",
            "",
            "This file is initialized so the route has a stable report target. The route is not complete until all controlling-prompt completion requirements are satisfied.",
            "",
            f"Current primary non-crypto row count: `{denominator_summary['primary_non_crypto_rows']}`.",
            f"Current close-spread boundary rows excluded from primary: `{denominator_summary['friday_21_00_close_batch_rows']}`.",
            "",
        ]
    )


def verify_outputs() -> dict[str, Any]:
    required = [
        STATE_PATH,
        CONTROL_LEDGER,
        CONTEXT_ANCHOR,
        OUTPUT_MANIFEST,
        REPAIR_LEDGER,
        COMPLETION_AUDIT,
        FINAL_REPORT,
        FREEZE_SOURCE_WINDOW,
        FREEZE_EVENT_INVENTORY,
        FREEZE_CODE_RELOAD_TIMELINE,
        FREEZE_DENOMINATOR_SUMMARY,
        CRYPTO_EXCLUSION_SUMMARY,
        SOURCE_COVERAGE_LEDGER,
        SOURCE_SCHEMA_LEDGER,
        SOURCE_GAP_LEDGER,
        SOURCE_HASH_MANIFEST,
    ]
    issues: list[dict[str, Any]] = []
    for path in required:
        if not path.exists() or path.stat().st_size <= 0:
            issues.append({"code": "missing_or_empty_output", "path": str(path)})
    summary = load_json(FREEZE_DENOMINATOR_SUMMARY) if FREEZE_DENOMINATOR_SUMMARY.exists() else {}
    inventory_rows = line_count(FREEZE_EVENT_INVENTORY)
    if summary.get("all_inventory_rows") != inventory_rows:
        issues.append(
            {
                "code": "inventory_row_count_mismatch",
                "expected": summary.get("all_inventory_rows"),
                "actual": inventory_rows,
            }
        )
    if not summary.get("primary_non_crypto_rows"):
        issues.append({"code": "primary_denominator_empty"})
    if summary.get("crypto_rows_broad_window") and not CRYPTO_EXCLUSION_SUMMARY.exists():
        issues.append({"code": "crypto_summary_missing"})
    state = load_json(STATE_PATH) if STATE_PATH.exists() else {}
    if state.get("status") == "complete":
        issues.append({"code": "route_state_must_not_mark_complete"})
    return {
        "schema_version": "friday_freeze_inventory_verification_v1",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "git_head": git_head(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "primary_non_crypto_rows": summary.get("primary_non_crypto_rows"),
        "all_inventory_rows": summary.get("all_inventory_rows"),
    }


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    events, malformed = load_trade_events()
    lifecycle_rows = load_lifecycle_rows()
    first_order = first_placed_event(events, lifecycle_rows)
    first_candle = parse_dt(first_order.get("candidate_candle_time_utc"))
    if first_order.get("status") != "found" or first_candle is None:
        raise SystemExit("could not determine first placed vNext order from local evidence")

    inventory = [classify_event(row, first_candle, FRIDAY_CLOSE_BATCH_UTC) for row in events]
    inventory.sort(key=lambda row: (row.get("timestamp_basis_utc") or "", row.get("symbol") or "", row.get("candidate_id") or ""))
    denominator_summary = build_denominator_summary(inventory, first_candle)
    crypto_summary = build_crypto_summary(inventory)
    source_window = build_source_window(first_order, first_candle, denominator_summary)
    timeline_rows = build_code_reload_timeline(first_order)
    coverage_rows, schema_rows, gap_rows, hash_manifest = build_source_ledgers(events, malformed)

    write_json(FREEZE_SOURCE_WINDOW, source_window)
    write_jsonl(FREEZE_EVENT_INVENTORY, inventory)
    write_jsonl(FREEZE_CODE_RELOAD_TIMELINE, timeline_rows)
    write_json(FREEZE_DENOMINATOR_SUMMARY, denominator_summary)
    write_json(CRYPTO_EXCLUSION_SUMMARY, crypto_summary)
    write_jsonl(SOURCE_COVERAGE_LEDGER, coverage_rows)
    write_jsonl(SOURCE_SCHEMA_LEDGER, schema_rows)
    write_jsonl(SOURCE_GAP_LEDGER, gap_rows)
    write_json(SOURCE_HASH_MANIFEST, hash_manifest)

    outputs = [
        FREEZE_SOURCE_WINDOW,
        FREEZE_EVENT_INVENTORY,
        FREEZE_CODE_RELOAD_TIMELINE,
        FREEZE_DENOMINATOR_SUMMARY,
        CRYPTO_EXCLUSION_SUMMARY,
        SOURCE_COVERAGE_LEDGER,
        SOURCE_SCHEMA_LEDGER,
        SOURCE_GAP_LEDGER,
        SOURCE_HASH_MANIFEST,
    ]
    write_jsonl(
        REPAIR_LEDGER,
        [
            {
                "schema_version": "friday_microscope_repair_ledger_v1",
                "timestamp_utc": utc_now(),
                "defect_id": "FRIDAY_QUALITY_SELECTOR_CONTAMINATED_WEEKEND_SOURCE_REQUIRES_CLEAN_REPLAY_DECISION",
                "defect_class": "config_runtime_selector_source_contamination",
                "status": "open_repair_required_after_clean_friday_and_broad_selected_replay",
                "evidence": "config currently applies moonshot_candidate_quality_selector from LIVE_WEEKEND_EXECUTION_POLICY_TOURNAMENT_SUMMARY.json",
                "next_action": "audit clean Friday freeze and broad selected-system replay, then implement remove/disable/replace decision with tests",
            },
            {
                "schema_version": "friday_microscope_repair_ledger_v1",
                "timestamp_utc": utc_now(),
                "defect_id": "FRIDAY_FULL_SELECTED_DENOMINATOR_JOIN_NOT_BUILT_YET",
                "defect_class": "missing_replay_denominator_reconciliation",
                "status": "open_stage_04_builder_required",
                "evidence": "Stage 01/02 freeze isolates primary rows; row-level selected-system denominator status still unbuilt",
                "next_action": "build canonical event ledger and raw-vs-selected denominator bridge",
            },
        ],
    )
    write_json(STATE_PATH, build_route_state(first_order, denominator_summary, outputs))
    CONTEXT_ANCHOR.write_text(render_context_anchor(source_window, denominator_summary), encoding="utf-8")
    write_json(COMPLETION_AUDIT, build_completion_audit(denominator_summary))
    FINAL_REPORT.write_text(render_final_report_stub(denominator_summary), encoding="utf-8")
    all_outputs = outputs + [STATE_PATH, CONTROL_LEDGER, CONTEXT_ANCHOR, OUTPUT_MANIFEST, REPAIR_LEDGER, COMPLETION_AUDIT, FINAL_REPORT]
    write_json(OUTPUT_MANIFEST, output_manifest(all_outputs))
    append_jsonl(
        CONTROL_LEDGER,
        {
            "schema_version": "friday_microscope_control_ledger_v1",
            "timestamp_utc": utc_now(),
            "stage": "stage_01_02_freeze_inventory",
            "action": "built_initial_friday_freeze_and_source_inventory",
            "git_head": git_head(),
            "primary_non_crypto_rows": denominator_summary["primary_non_crypto_rows"],
            "all_inventory_rows": denominator_summary["all_inventory_rows"],
            "output_manifest": OUTPUT_MANIFEST.relative_to(ROOT).as_posix(),
        },
    )

    verification = verify_outputs()
    write_json(ROUTE_DIR / "FRIDAY_FREEZE_INVENTORY_VERIFICATION.json", verification)
    # Refresh manifest after writing verification.
    write_json(OUTPUT_MANIFEST, output_manifest(all_outputs + [ROUTE_DIR / "FRIDAY_FREEZE_INVENTORY_VERIFICATION.json"]))
    return verification


def main() -> int:
    args = parse_args()
    if args.check:
        verification = verify_outputs()
    else:
        verification = build()
    print(json.dumps(verification, indent=2, sort_keys=True))
    return 0 if verification.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

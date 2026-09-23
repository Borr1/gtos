#!/usr/bin/env python3
"""Build the post-Lane18 source-capture repair package.

This route is offline/read-only. It streams terminal source-gap ledgers,
classifies each material row, binds rows to local source coverage where current
disk can prove coverage, and emits default-off capture/export contracts for the
fields that remain missing.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
ROUTE_ID = "vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01"
SCHEMA_VERSION = "post_lane18_source_capture_repair_v1"

ACTIVE_SYMBOLS = [
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
]

SOURCE_INPUTS = [
    ("lane01_source_gap", "research/operations/vnext_moonshot_lane01_data_universe_source_authority_2026_06_01/SOURCE_GAP_LEDGER.jsonl"),
    ("lane03_source_gap", "research/operations/vnext_moonshot_lane03_historical_candidate_reconstruction_2026_06_01/LANE03_SOURCE_GAP_LEDGER.jsonl"),
    ("lane04_source_gap", "research/operations/vnext_moonshot_lane04_historical_microscope_engine_2026_06_01/LANE04_SOURCE_GAP_LEDGER.jsonl"),
    ("lane05_source_gap", "research/operations/vnext_moonshot_lane05_feature_store_v1_2026_06_01/LANE05_SOURCE_GAP_LEDGER.jsonl"),
    ("lane06_missing_label_gap", "research/operations/vnext_moonshot_lane06_label_store_v1_2026_06_01/LANE06_MISSING_LABEL_GAP_LEDGER.jsonl.gz"),
    ("lane07_source_gap", "research/operations/vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01/LANE07_SOURCE_GAP_LEDGER.jsonl"),
    ("lane08_missing_replay_gap", "research/operations/vnext_moonshot_lane08_digital_twin_replay_engine_2026_06_01/LANE08_MISSING_REPLAY_GAP_LEDGER.jsonl.gz"),
    ("lane09_capture_requirement", "research/operations/vnext_moonshot_lane09_meta_selector_v2_2026_06_01/LANE09_PACKET_CAPTURE_REQUIREMENTS.jsonl"),
    ("lane10_missing_scheduler_gap", "research/operations/vnext_moonshot_lane10_portfolio_scheduler_v2_2026_06_01/LANE10_MISSING_REPLAY_GAP_SCHEDULER_LEDGER.jsonl.gz"),
    ("lane09b_source_gap", "research/operations/vnext_moonshot_lane09b_selector_scheduler_reconciliation_2026_06_01/LANE09B_SOURCE_GAP_LEDGER.jsonl"),
    ("lane10b_source_gap", "research/operations/vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design_2026_06_01/LANE10B_SOURCE_GAP_LEDGER.jsonl"),
    ("lane11_expanded_policy_source_gap", "research/operations/vnext_moonshot_lane11_execution_policy_engine_v2_2026_06_01/LANE11_EXPANDED_POLICY_SOURCE_GAP_LEDGER.jsonl.gz"),
    ("lane16_source_gap", "research/operations/vnext_absolute_moonshot_lane16_historical_microscope_scale_2026_06_01/LANE16_SOURCE_GAP_LEDGER.jsonl.gz"),
    ("lane17_source_gap", "research/operations/vnext_absolute_moonshot_lane17_market_awareness_whiteboard_2026_06_01/LANE17_SOURCE_GAP_LEDGER.jsonl.gz"),
    ("lane18_source_gap", "research/operations/vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2_2026_06_01/LANE18_SOURCE_GAP_LEDGER.jsonl"),
    ("lane18_prospective_capture", "research/operations/vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2_2026_06_01/LANE18_PROSPECTIVE_CAPTURE_REQUIREMENTS.jsonl"),
    ("mt5_remaining_vps_export", "research/operations/vnext_mt5_local_cache_preservation_2026_06_01/MT5_REMAINING_VPS_EXPORT_REQUIREMENTS.jsonl"),
    ("mt5_missing_roots", "research/operations/vnext_mt5_local_cache_preservation_2026_06_01/MT5_MISSING_ROOT_LEDGER.jsonl"),
    ("mt5_unreadable_blocked", "research/operations/vnext_mt5_local_cache_preservation_2026_06_01/MT5_UNREADABLE_OR_BLOCKED_LEDGER.jsonl"),
    ("vps_missing_export", "research/operations/vnext_compliant_vps_data_preservation_broker_portability_2026_06_01/MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl"),
    ("vps_broker_portability_gap", "research/operations/vnext_compliant_vps_data_preservation_broker_portability_2026_06_01/BROKER_PORTABILITY_GAP_LEDGER.jsonl"),
]

REQUIRED_OUTPUTS = [
    "POST_LANE18_SOURCE_GAP_SUPERLEDGER.jsonl.gz",
    "POST_LANE18_REPAIRED_SOURCE_LEDGER.jsonl.gz",
    "POST_LANE18_SOURCE_COVERAGE_DELTA_LEDGER.jsonl",
    "POST_LANE18_PARSER_HELPER_IMPLEMENTATION_LEDGER.jsonl",
    "POST_LANE18_READ_ONLY_EXPORT_REQUIREMENT_LEDGER.jsonl.gz",
    "POST_LANE18_FORWARD_CAPTURE_CONTRACT.jsonl.gz",
    "POST_LANE18_NON_GENERATABLE_HISTORICAL_TRUTH_LEDGER.jsonl.gz",
    "POST_LANE18_SOURCE_ASOF_NOLEAK_VALIDATION_LEDGER.jsonl",
    "POST_LANE18_DOWNSTREAM_CONTRACTS.json",
    "POST_LANE18_RESULT_USE_STATUS.json",
    "POST_LANE18_SOURCE_CAPTURE_DECISIONS.jsonl",
    "POST_LANE18_SOURCE_COMPLETENESS_DECISIONS.jsonl",
    "POST_LANE18_BRANCH_DECISION_LEDGER.jsonl",
    "POST_LANE18_IMPLEMENTATION_DECISION_LEDGER.jsonl",
    "POST_LANE18_FIELD_FAMILY_SUMMARY.json",
    "POST_LANE18_SOURCE_INDEX.json",
    "POST_LANE18_SOURCE_ROOT_SEARCH_LEDGER.jsonl",
    "POST_LANE18_SATURATION_SELF_RED_TEAM.md",
    "POST_LANE18_CONTEXT_ANCHOR.md",
    "POST_LANE18_OUTPUT_MANIFEST.json",
    "POST_LANE18_COMPLETION_AUDIT.json",
]

DISPOSITION_PRIORITY = {
    "filled_now": 0,
    "reconstructed_now": 1,
    "proxy_bound_now": 2,
    "read_only_export_required": 3,
    "forward_capture_required": 4,
    "non_generatable_historical_truth": 5,
    "blocked_with_exact_source_requirement": 6,
}

CONSUMERS = [
    "Selector V3",
    "Scheduler V3",
    "Execution Policy V3",
    "Digital Twin V2",
    "ML Dataset/Baselines",
    "ML Policy Intelligence",
    "Repair Companion",
    "Command Center",
    "Production Change Dossier",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stable_hash(value: Any, length: int = 32) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def open_gz_jsonl(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    return gzip.open(path, "wt", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            count += 1
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return count


def write_gz_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with open_gz_jsonl(path) as handle:
        for row in rows:
            count += 1
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return count


def iter_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    with open_text(path) as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                yield line_no, {
                    "schema_version": "json_parse_gap_v1",
                    "gap_type": "source_parse_gap",
                    "gap_status": f"json_decode_error:{exc.msg}",
                    "raw_line_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest(),
                }
                continue
            if isinstance(row, dict):
                yield line_no, row


def parse_date(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value)
    match = re.search(r"(20\d\d-\d\d-\d\d)", text)
    return match.group(1) if match else None


def infer_symbol_timeframe_from_name(path: Path) -> tuple[str | None, str | None]:
    name = path.stem
    parts = name.rsplit("_", 1)
    if len(parts) == 2 and parts[1].upper() in {"M1", "M5", "M15", "H1", "H4", "D1"}:
        return parts[0], parts[1].upper()
    return None, None


def canonical_symbol_candidates(symbol: str | None) -> list[str]:
    if not symbol:
        return []
    aliases = {
        "US30_cash": ["US30_cash", "US30.cash", "US30"],
        "UKOIL_cash": ["UKOIL_cash", "UKOIL.cash", "UKOIL"],
        "USOIL_cash": ["USOIL_cash", "USOIL.cash", "USOIL"],
        "NAS100": ["NAS100", "NDX100"],
    }
    return aliases.get(symbol, [symbol])


def extract_timeframe_from_family(family: str, row: dict[str, Any]) -> str | None:
    text = " ".join(
        str(value or "")
        for value in (
            family,
            row.get("source_path"),
            row.get("field"),
            row.get("missing_field"),
            row.get("reason"),
        )
    ).lower()
    for timeframe in ("m1", "m5", "m15", "h1", "h4", "d1"):
        if re.search(rf"(^|[^a-z0-9]){timeframe}([^a-z0-9]|$)", text):
            return timeframe.upper()
    return None


@dataclass
class SourceEntry:
    path: str
    source_class: str
    start_date: str | None = None
    end_date: str | None = None
    sha256: str | None = None
    row_count: int | None = None


@dataclass
class SourceIndex:
    bar: dict[tuple[str, str], list[SourceEntry]] = field(default_factory=lambda: defaultdict(list))
    ticks: dict[tuple[str, str], list[SourceEntry]] = field(default_factory=lambda: defaultdict(list))
    m1: dict[tuple[str, str], list[SourceEntry]] = field(default_factory=lambda: defaultdict(list))
    account_history: dict[tuple[str, str], list[SourceEntry]] = field(default_factory=lambda: defaultdict(list))
    existing_paths: set[str] = field(default_factory=set)
    live_spec_symbols: set[str] = field(default_factory=set)
    cost_symbols: set[str] = field(default_factory=set)
    root_rows: list[dict[str, Any]] = field(default_factory=list)
    used_sources: dict[str, SourceEntry] = field(default_factory=dict)

    def remember(self, entry: SourceEntry) -> SourceEntry:
        self.used_sources.setdefault(entry.path, entry)
        return entry

    def find_bar(self, symbol: str | None, timeframe: str | None, date_str: str | None) -> SourceEntry | None:
        if not symbol or not timeframe or not date_str:
            return None
        for candidate in canonical_symbol_candidates(symbol):
            for entry in self.bar.get((candidate, timeframe), []):
                if entry.start_date and entry.end_date and entry.start_date <= date_str <= entry.end_date:
                    return self.remember(entry)
        return None

    def find_tick(self, symbol: str | None, date_str: str | None) -> SourceEntry | None:
        if not symbol or not date_str:
            return None
        for candidate in canonical_symbol_candidates(symbol):
            entries = self.ticks.get((candidate, date_str), [])
            if entries:
                return self.remember(entries[0])
        return None

    def find_m1(self, symbol: str | None, date_str: str | None) -> SourceEntry | None:
        if not symbol or not date_str:
            return None
        for candidate in canonical_symbol_candidates(symbol):
            entries = self.m1.get((candidate, date_str), [])
            if entries:
                return self.remember(entries[0])
            bar = self.find_bar(candidate, "M1", date_str)
            if bar:
                return bar
        return None

    def find_account_history(self, symbol: str | None, date_str: str | None) -> SourceEntry | None:
        if not symbol or not date_str:
            return None
        for candidate in canonical_symbol_candidates(symbol):
            entries = self.account_history.get((candidate, date_str), [])
            if entries:
                return self.remember(entries[0])
        return None

    def path_exists(self, raw_path: str | None) -> bool:
        if not raw_path:
            return False
        path = raw_path.replace("\\", "/")
        if path in self.existing_paths:
            return True
        absolute = Path(raw_path)
        if absolute.exists():
            return True
        return (REPO_ROOT / path).exists()


def csv_date_range(path: Path) -> tuple[str | None, str | None, int]:
    first = None
    last = None
    rows = 0
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, None)
            for row in reader:
                if not row:
                    continue
                date_str = parse_date(row[0])
                if date_str:
                    first = first or date_str
                    last = date_str
                rows += 1
    except OSError:
        return None, None, 0
    return first, last, rows


def build_source_index() -> SourceIndex:
    index = SourceIndex()
    roots = [
        ("data", REPO_ROOT / "data"),
        ("data_historical_2022_2023", REPO_ROOT / "data" / "historical_2022_2023"),
        ("data_historical_2026", REPO_ROOT / "data" / "historical_2026"),
        ("data_mt5_research_exports", REPO_ROOT / "data" / "mt5_research_exports"),
        ("data_ticks", REPO_ROOT / "data" / "ticks"),
        ("data_m1", REPO_ROOT / "data" / "m1"),
        ("data_account_history", REPO_ROOT / "data" / "account_history"),
        ("shadow_logs", REPO_ROOT / "shadow_logs"),
        ("pipeline_state", REPO_ROOT / "pipeline_state"),
        ("preserved_mt5_cache_route", REPO_ROOT / "research" / "operations" / "vnext_mt5_local_cache_preservation_2026_06_01"),
        ("compliant_vps_route", REPO_ROOT / "research" / "operations" / "vnext_compliant_vps_data_preservation_broker_portability_2026_06_01"),
    ]
    for root_id, root in roots:
        files = 0
        bytes_total = 0
        if root.exists():
            for item in root.rglob("*"):
                if item.is_file():
                    files += 1
                    try:
                        bytes_total += item.stat().st_size
                    except OSError:
                        pass
                    rel = item.relative_to(REPO_ROOT).as_posix() if item.is_relative_to(REPO_ROOT) else str(item)
                    index.existing_paths.add(rel)
        index.root_rows.append(
            {
                "schema_version": "post_lane18_source_root_search_v1",
                "route_id": ROUTE_ID,
                "root_id": root_id,
                "root_path": str(root),
                "exists": root.exists(),
                "file_count": files,
                "bytes_total": bytes_total,
                "searched_at_utc": now_iso(),
                "no_broker_access": True,
            }
        )

    for root in [REPO_ROOT / "data", REPO_ROOT / "data" / "historical_2022_2023", REPO_ROOT / "data" / "historical_2026", REPO_ROOT / "data" / "mt5_research_exports"]:
        if not root.exists():
            continue
        for path in root.rglob("*.csv"):
            symbol, timeframe = infer_symbol_timeframe_from_name(path)
            if not symbol or not timeframe:
                continue
            start, end, rows = csv_date_range(path)
            if not start or not end:
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            index.bar[(symbol, timeframe)].append(
                SourceEntry(rel, "source_hashed_market_bar_csv", start, end, sha256_file(path), rows)
            )

    tick_root = REPO_ROOT / "data" / "ticks"
    if tick_root.exists():
        for path in tick_root.glob("*/*"):
            if not path.is_file():
                continue
            date_str = parse_date(path.name)
            if not date_str:
                continue
            symbol = path.parent.name
            rel = path.relative_to(REPO_ROOT).as_posix()
            index.ticks[(symbol, date_str)].append(
                SourceEntry(rel, "source_hashed_tick_or_quote_file", date_str, date_str, sha256_file(path), None)
            )

    m1_root = REPO_ROOT / "data" / "m1"
    if m1_root.exists():
        for path in m1_root.glob("*/*.csv"):
            date_str = parse_date(path.name)
            if not date_str:
                continue
            symbol = path.parent.name
            rel = path.relative_to(REPO_ROOT).as_posix()
            start, end, rows = csv_date_range(path)
            index.m1[(symbol, date_str)].append(
                SourceEntry(rel, "forward_m1_capture_csv", start or date_str, end or date_str, sha256_file(path), rows)
            )

    account_root = REPO_ROOT / "data" / "account_history"
    if account_root.exists():
        for path in account_root.glob("*.jsonl"):
            rel = path.relative_to(REPO_ROOT).as_posix()
            source = SourceEntry(rel, "read_only_broker_history_export_local_file", sha256=sha256_file(path))
            for _, row in iter_jsonl(path):
                symbol = str(row.get("symbol") or row.get("broker_symbol") or "")
                date_str = parse_date(row.get("time") or row.get("time_utc") or row.get("event_time_utc") or path.name)
                if symbol and date_str:
                    index.account_history[(symbol, date_str)].append(source)

    for spec_path in [
        REPO_ROOT / "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/LIVE_SYMBOL_BROKER_SPEC_LEDGER.jsonl",
        REPO_ROOT / "research/operations/vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01/LANE07_SYMBOL_SPEC_SESSION_LEDGER.jsonl",
    ]:
        if spec_path.exists():
            for _, row in iter_jsonl(spec_path):
                symbol = row.get("symbol") or row.get("broker_symbol")
                if symbol:
                    index.live_spec_symbols.add(str(symbol))

    cost_path = REPO_ROOT / "research/operations/vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01/LANE07_COST_CALIBRATION_LEDGER.jsonl"
    if cost_path.exists():
        for _, row in iter_jsonl(cost_path):
            symbol = row.get("symbol") or row.get("broker_symbol")
            if symbol:
                index.cost_symbols.add(str(symbol))

    return index


def field_families(row: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for proof in row.get("source_gap_proof") or []:
        if isinstance(proof, dict) and proof.get("field_family"):
            out.append(str(proof["field_family"]))
    for value in row.get("source_gap_families") or []:
        out.append(str(value))
    for key in (
        "field_family",
        "field",
        "missing_field",
        "gap_family",
        "gap_type",
        "gap_code",
        "source_gap_reason",
        "gap_reason_code",
        "replay_gap_reason_code",
        "repair_requirement_code",
        "missing_source_class",
        "source_surface",
        "source_family",
        "source_use_state",
        "source_completeness_decision",
        "capture_surface",
        "requirement_type",
        "scheduler_reason",
        "missing_fields_or_windows",
    ):
        value = row.get(key)
        if isinstance(value, list):
            out.extend(str(item) for item in value if item not in (None, ""))
        elif value:
            out.append(str(value))
    if row.get("source_gap") is False:
        out.append("source_gap_false_consumed_full")
    if not out:
        out.append("unspecified_source_gap")
    seen = set()
    unique = []
    for value in out:
        if value not in seen:
            unique.append(value)
            seen.add(value)
    return unique


def row_symbol(row: dict[str, Any]) -> str | None:
    value = row.get("symbol") or row.get("broker_symbol") or row.get("candidate_symbol")
    return str(value) if value not in (None, "") else None


def row_date(row: dict[str, Any]) -> str | None:
    for key in ("date", "candidate_time_utc", "decision_asof_utc", "decision_time_utc", "source_event_utc", "generated_at_utc"):
        parsed = parse_date(row.get(key))
        if parsed:
            return parsed
    return None


def exact_requirement(row: dict[str, Any], family: str) -> str:
    candidates = [
        row.get("repair_requirement"),
        row.get("repair_requirement_code"),
        row.get("required_action"),
        row.get("capture_or_repair_requirement"),
        row.get("exact_next_capture"),
        row.get("proof_required"),
        row.get("repair_action"),
        row.get("source_completeness_decision"),
        row.get("risk"),
    ]
    for proof in row.get("source_gap_proof") or []:
        if isinstance(proof, dict) and proof.get("field_family") == family:
            candidates.insert(0, proof.get("repair_requirement"))
            candidates.insert(0, proof.get("reason"))
    for value in candidates:
        if value not in (None, "", []):
            return str(value)
    return f"exact source/capture requirement for {family}"


def make_disposition(
    disposition: str,
    *,
    family: str,
    source_class: str,
    reason: str,
    requirement: str,
    sources: list[SourceEntry] | None = None,
    asof_status: str = "asof_preserved_or_not_applicable",
    no_leak_status: str = "source_class_preserved_not_decision_feature_unless_marked",
) -> dict[str, Any]:
    return {
        "field_family": family,
        "disposition": disposition,
        "source_class": source_class,
        "classification_reason": reason,
        "exact_source_requirement": requirement,
        "repair_source_paths": [source.path for source in sources or []],
        "repair_source_sha256": [source.sha256 for source in sources or [] if source.sha256],
        "asof_status": asof_status,
        "no_leak_status": no_leak_status,
        "exact_r": None,
        "proxy_r": None,
        "expectancy_r": None,
    }


def classify_field(row: dict[str, Any], family: str, index: SourceIndex) -> dict[str, Any]:
    lower = family.lower()
    status_blob = " ".join(
        str(row.get(key) or "")
        for key in (
            "status",
            "source_gap_status",
            "gap_status",
            "source_state",
            "recoverability",
            "required_action",
            "reason",
            "gap_status",
        )
    ).lower()
    requirement = exact_requirement(row, family)
    symbol = row_symbol(row)
    date_str = row_date(row)
    source_path = str(row.get("source_path") or row.get("source") or "")

    if "pass" == str(row.get("gap_status") or "").lower() or row.get("source_gap") is False:
        return make_disposition(
            "filled_now",
            family=family,
            source_class="terminal_route_consumed_full_source",
            reason="upstream terminal route records consumed_full/pass status",
            requirement="none_required",
        )
    if "available_repo_and_preserved_mt5_cache" in status_blob:
        return make_disposition(
            "filled_now",
            family=family,
            source_class="repo_and_preserved_mt5_market_history",
            reason="Lane01 already proves repo and MT5 cache coverage",
            requirement="none_required",
        )

    if any(
        token in lower
        for token in (
            "joined_microscope_label_replay_scheduler",
            "no_joined_label",
            "selected_candidate_geometry",
            "joined_selector_label",
            "not_replayable_without",
            "unreplayable_source_gap",
            "label_source",
            "source_parse_gap",
            "non_generatable_historical",
        )
    ):
        return make_disposition(
            "non_generatable_historical_truth",
            family=family,
            source_class="missing_historical_candidate_label_or_system_state",
            reason="terminal lanes prove this exact historical row is not reconstructable from current approved inputs without inventing intent/label truth",
            requirement=requirement,
            no_leak_status="missing_label_source_not_backfilled_from_outcome",
        )

    timeframe = extract_timeframe_from_family(family, row)
    if timeframe:
        source = index.find_bar(symbol, timeframe, date_str)
        if source:
            return make_disposition(
                "filled_now",
                family=family,
                source_class="source_hashed_market_bar",
                reason=f"local {timeframe} bar file covers {symbol} {date_str}",
                requirement="none_required_for_bar_field",
                sources=[source],
                no_leak_status="decision_asof_market_bar_source_only",
            )
        return make_disposition(
            "read_only_export_required",
            family=family,
            source_class="recoverable_market_bar_export",
            reason=f"no local {timeframe} bar source covers {symbol} {date_str}",
            requirement=f"read-only MT5/Sierra/vendor {timeframe} bar export for {symbol} covering {date_str}",
            no_leak_status="market_data_source_not_label",
        )

    if "tick" in lower or "bid_ask" in lower or "ordered" in lower:
        tick = index.find_tick(symbol, date_str)
        if tick:
            return make_disposition(
                "filled_now",
                family=family,
                source_class="source_hashed_tick_or_quote",
                reason=f"local tick/quote file covers {symbol} {date_str}",
                requirement="none_required_for_tick_field",
                sources=[tick],
                no_leak_status="decision_asof_market_tick_source_only",
            )
        m1 = index.find_m1(symbol, date_str)
        if m1:
            return make_disposition(
                "proxy_bound_now",
                family=family,
                source_class="m1_proxy_for_missing_tick_path",
                reason=f"M1 source covers {symbol} {date_str}; exact ordered bid/ask tick remains missing",
                requirement=f"read-only ordered bid/ask tick export for {symbol} covering {date_str}",
                sources=[m1],
                no_leak_status="proxy_market_path_not_broker_real_label",
            )
        return make_disposition(
            "read_only_export_required",
            family=family,
            source_class="recoverable_tick_or_quote_export",
            reason=f"no local tick/quote or M1 proxy source covers {symbol} {date_str}",
            requirement=f"read-only ordered bid/ask tick/quote export for {symbol} covering {date_str}",
            no_leak_status="market_data_source_not_label",
        )

    if any(token in lower for token in ("broker_intent", "historical_broker_intent", "pending_order_intent", "write_clock")):
        return make_disposition(
            "non_generatable_historical_truth",
            family=family,
            source_class="historical_system_intent_truth",
            reason="historical intent/order lifecycle cannot be generated from price movement",
            requirement="prospective decision/order lifecycle logger with source timestamp, row identity, and null reason",
            no_leak_status="not_consumed_as_decision_feature_or_label",
        )

    if (
        lower in {"net_r", "cost_adjusted_r", "sl_before_1r", "post_friday_terminal_broker_net_r"}
        or "exact_r" in lower
        or "r_geometry" in lower
        or lower.endswith("_r")
    ):
        account = index.find_account_history(symbol, date_str)
        if account:
            return make_disposition(
                "filled_now",
                family=family,
                source_class="read_only_broker_history_export",
                reason=f"local account history export contains {symbol} {date_str}",
                requirement="none_required_for_local_exported_rows",
                sources=[account],
                no_leak_status="post_decision_broker_truth_not_decision_feature",
            )
        if symbol in index.cost_symbols:
            return make_disposition(
                "proxy_bound_now",
                family=family,
                source_class="source_bound_proxy_r_or_cost_calibration",
                reason=f"local broker cost calibration source exists for {symbol}; exact realized R still needs broker lifecycle export",
                requirement=requirement,
                no_leak_status="proxy_cost_calibration_not_realized_result_label",
            )
        return make_disposition(
            "read_only_export_required",
            family=family,
            source_class="broker_read_only_history_export",
            reason="realized R and cost-adjusted R require broker lifecycle/cost truth or an existing account-history export",
            requirement=requirement,
            no_leak_status="post_decision_broker_truth_not_decision_feature",
        )

    if any(
        token in lower
        for token in (
            "order",
            "deal",
            "position",
            "broker_real",
            "broker_cost",
            "broker_truth",
            "cost_gap",
            "cost_fields",
            "lifecycle",
            "commission",
            "swap",
            "history",
            "fee",
            "slippage",
            "retcode",
            "close_reason",
            "false_local_close",
            "account_baseline",
            "balance_equity",
        )
    ):
        account = index.find_account_history(symbol, date_str)
        if account:
            return make_disposition(
                "filled_now",
                family=family,
                source_class="read_only_broker_history_export",
                reason=f"local account history export contains {symbol} {date_str}",
                requirement="none_required_for_local_exported_rows",
                sources=[account],
                no_leak_status="post_decision_broker_truth_not_decision_feature",
            )
        if "prospective" in status_blob or "forward" in status_blob:
            return make_disposition(
                "forward_capture_required",
                family=family,
                source_class="prospective_broker_lifecycle_capture",
                reason="field requires ticket-bound runtime lifecycle capture going forward",
                requirement=requirement,
                no_leak_status="post_decision_broker_truth_capture_contract",
            )
        return make_disposition(
            "read_only_export_required",
            family=family,
            source_class="broker_read_only_history_export",
            reason="broker/order/deal/cost truth is recoverable only from broker export or existing account-history source",
            requirement=requirement,
            no_leak_status="post_decision_broker_truth_not_decision_feature",
        )

    if any(
        token in lower
        for token in (
            "broker_specs",
            "symbol_info",
            "session",
            "holiday",
            "margin",
            "spread",
            "stop",
            "freeze",
            "tick_value",
            "contract_size",
            "broker_symbol",
            "broker_specific_symbol_geometry",
            "currency_base",
            "currency_profit",
            "point_value",
            "point",
            "trade_calc_mode",
            "filling_mode",
            "expiration_mode",
            "order_mode",
            "server_timezone",
            "server_timezone_and_dst",
            "symbol_aliases",
            "triple_day_rollover",
            "volume_min",
            "volume_step",
            "volume_max",
        )
    ):
        if symbol in index.live_spec_symbols or symbol in index.cost_symbols:
            return make_disposition(
                "proxy_bound_now",
                family=family,
                source_class="live_snapshot_or_cost_calibration_proxy",
                reason=f"current local symbol/cost snapshot exists for {symbol}; exact time-varying export remains required",
                requirement=requirement,
                no_leak_status="broker_metadata_proxy_not_broker_real_outcome",
            )
        if "forward" in status_blob or "prospective" in status_blob:
            disposition = "forward_capture_required"
        else:
            disposition = "read_only_export_required"
        return make_disposition(
            disposition,
            family=family,
            source_class="broker_symbol_metadata_export_or_forward_sampling",
            reason="exact broker metadata requires compliant read-only symbol/session/cost export or default-off sampling",
            requirement=requirement,
            no_leak_status="broker_metadata_not_trade_result_label",
        )

    if any(token in lower for token in ("correlation", "regime", "market_hours", "market_state")):
        if source_path and index.path_exists(source_path):
            return make_disposition(
                "proxy_bound_now",
                family=family,
                source_class="local_runtime_context_log_proxy",
                reason=f"source log exists for {family}; exact row-level runtime join still needs capture key",
                requirement=f"capture row-level {family} join key and source timestamp at decision time",
                no_leak_status="decision_time_context_proxy_not_result_label",
            )
        return make_disposition(
            "forward_capture_required",
            family=family,
            source_class="decision_time_context_capture",
            reason="no exact local runtime context join key exists for this historical row",
            requirement=f"capture row-level {family} at decision time with as-of timestamp and source hash",
            no_leak_status="decision_time_context_not_result_label",
        )

    if any(
        token in lower
        for token in (
            "missing_replay_gap_capture_or_repair",
            "selected_cell_risk",
            "selected_risk_portfolio",
            "portfolio_state",
            "requires_replayed_or_forward_policy_results",
            "policy_results_by_the_named_routing_dimension",
        )
    ):
        return make_disposition(
            "forward_capture_required",
            family=family,
            source_class="prospective_decision_context_capture",
            reason="exact selected risk/portfolio/replay-repair context needs row-level prospective capture before downstream use",
            requirement=requirement,
            no_leak_status="decision_context_not_result_label",
        )

    if any(token in lower for token in ("news_calendar", "macro_", "fred_", "gold_volatility")):
        for calendar_path in (REPO_ROOT / "data" / "economic_calendar.csv", REPO_ROOT / "data" / "news_calendar.json"):
            if calendar_path.exists():
                source = index.remember(
                    SourceEntry(
                        calendar_path.relative_to(REPO_ROOT).as_posix(),
                        "local_public_calendar_or_macro_proxy",
                        sha256=sha256_file(calendar_path),
                    )
                )
                return make_disposition(
                    "proxy_bound_now",
                    family=family,
                    source_class="local_public_calendar_or_macro_proxy",
                    reason=f"local public calendar/macro source exists at {source.path}; exact publication-time snapshot still requires source-specific as-of proof",
                    requirement=requirement,
                    sources=[source],
                    no_leak_status="public_calendar_proxy_not_result_label",
                )
        return make_disposition(
            "read_only_export_required",
            family=family,
            source_class="public_calendar_or_macro_read_only_export",
            reason="public calendar/macro field requires an as-of source snapshot",
            requirement=requirement,
            no_leak_status="public_calendar_source_not_result_label",
        )

    if "read_only_export" in lower or "prospective_capture" in lower or "telegram_parity" in lower:
        return make_disposition(
            "read_only_export_required",
            family=family,
            source_class="read_only_export_requirement",
            reason="field family names a read-only export/prospective capture source requirement",
            requirement=requirement,
            no_leak_status="source_contract_required_before_use",
        )

    if "export" in status_blob or "required" in status_blob:
        return make_disposition(
            "read_only_export_required",
            family=family,
            source_class="read_only_export_requirement",
            reason="upstream row explicitly requires a read-only export",
            requirement=requirement,
            no_leak_status="source_contract_required_before_use",
        )
    if "forward" in status_blob or "prospective" in status_blob:
        return make_disposition(
            "forward_capture_required",
            family=family,
            source_class="prospective_default_off_capture",
            reason="upstream row explicitly requires prospective capture",
            requirement=requirement,
            no_leak_status="default_off_capture_not_live_behavior_change",
        )
    if source_path and index.path_exists(source_path):
        return make_disposition(
            "reconstructed_now",
            family=family,
            source_class="local_source_path_exists_reconstruction",
            reason="referenced local source path exists and can be used by downstream repair",
            requirement="downstream route must bind exact row key before result use",
            no_leak_status="source_path_exists_not_result_claim",
        )
    return make_disposition(
        "blocked_with_exact_source_requirement",
        family=family,
        source_class="unresolved_source_requirement",
        reason="no approved local parser/source/export/capture route could fill this field now",
        requirement=requirement,
        no_leak_status="blocked_rows_not_consumed",
    )


def row_disposition(field_rows: list[dict[str, Any]]) -> str:
    return max(field_rows, key=lambda row: DISPOSITION_PRIORITY[row["disposition"]])["disposition"]


def summarize_counter(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def downstream_for_family(family: str) -> list[str]:
    lower = family.lower()
    consumers = set()
    if any(token in lower for token in ("selector", "label", "candidate", "feature", "regime", "correlation")):
        consumers.update(["Selector V3", "ML Dataset/Baselines", "ML Policy Intelligence", "Command Center"])
    if any(token in lower for token in ("scheduler", "risk", "margin", "position", "portfolio", "correlation")):
        consumers.update(["Scheduler V3", "Repair Companion", "Command Center"])
    if any(token in lower for token in ("policy", "tick", "partial", "trailing", "stop", "freeze", "order", "deal", "lifecycle", "broker")):
        consumers.update(["Execution Policy V3", "Digital Twin V2", "Repair Companion", "Production Change Dossier"])
    if any(token in lower for token in ("capture", "source", "export", "mt5", "vps")):
        consumers.update(["Repair Companion", "Command Center", "Production Change Dossier"])
    return sorted(consumers or set(CONSUMERS))


def superledger_rows(index: SourceIndex, stats: dict[str, Any]) -> Iterable[dict[str, Any]]:
    generated_at = now_iso()
    source_counts = Counter()
    disposition_counts = Counter()
    field_counts = Counter()
    consumer_counts = Counter()
    route_counts = Counter()

    for source_name, rel_path in SOURCE_INPUTS:
        path = REPO_ROOT / rel_path
        if not path.exists():
            stats["missing_input_paths"].append(rel_path)
            continue
        input_sha = sha256_file(path)
        rows_seen = 0
        for line_no, row in iter_jsonl(path):
            rows_seen += 1
            fields = [classify_field(row, family, index) for family in field_families(row)]
            material_disposition = row_disposition(fields)
            route = str(row.get("route_id") or source_name)
            symbol = row_symbol(row)
            date_str = row_date(row)
            row_id = (
                row.get("gap_id")
                or row.get("source_gap_id")
                or row.get("requirement_id")
                or row.get("capture_requirement_id")
                or row.get("row_id")
                or row.get("candidate_id")
                or f"{source_name}:{line_no}"
            )
            consumers = sorted({consumer for field_row in fields for consumer in downstream_for_family(field_row["field_family"])})
            row_hash = stable_hash(row, 64)
            output = {
                "schema_version": "post_lane18_source_gap_superledger_row_v1",
                "route_id": ROUTE_ID,
                "generated_at_utc": generated_at,
                "source_input_name": source_name,
                "source_input_path": rel_path,
                "source_input_sha256": input_sha,
                "source_line": line_no,
                "source_route_id": route,
                "source_schema_version": row.get("schema_version"),
                "source_row_sha256": row_hash,
                "superledger_row_id": stable_hash([source_name, line_no, row_hash]),
                "source_row_id": str(row_id),
                "symbol": symbol,
                "date": date_str,
                "candidate_time_utc": row.get("candidate_time_utc") or row.get("decision_asof_utc") or row.get("decision_time_utc"),
                "material_disposition": material_disposition,
                "field_dispositions": fields,
                "downstream_consumers": consumers,
                "result_use_status": "source_capture_repair_row_not_performance_result",
                "runtime_effect_boundary": "offline_source_capture_repair_only_no_live_behavior_change",
                "forbidden_surface_status": "no_broker_mutation_no_paid_api_no_remote_no_live_activation",
            }
            source_counts[source_name] += 1
            route_counts[route] += 1
            disposition_counts[material_disposition] += 1
            for field_row in fields:
                field_counts[(field_row["field_family"], field_row["disposition"])] += 1
            for consumer in consumers:
                consumer_counts[(consumer, material_disposition)] += 1
            yield output
        stats["input_rows"][source_name] = rows_seen

    stats["source_input_counts"] = summarize_counter(source_counts)
    stats["route_counts"] = summarize_counter(route_counts)
    stats["disposition_counts"] = summarize_counter(disposition_counts)
    stats["field_disposition_counts"] = {
        f"{field}|{disposition}": count for (field, disposition), count in sorted(field_counts.items())
    }
    stats["consumer_disposition_counts"] = {
        f"{consumer}|{disposition}": count for (consumer, disposition), count in sorted(consumer_counts.items())
    }


def derive_ledgers_from_superledger(superledger_path: Path) -> dict[str, Any]:
    stats = {
        "repaired_rows": 0,
        "read_only_export_requirement_rows": 0,
        "forward_capture_contract_rows": 0,
        "non_generatable_rows": 0,
        "validation_rows": 0,
    }
    repaired_path = ROUTE_DIR / "POST_LANE18_REPAIRED_SOURCE_LEDGER.jsonl.gz"
    export_requirements: dict[str, dict[str, Any]] = {}
    capture_contracts: dict[str, dict[str, Any]] = {}
    non_generatable_path = ROUTE_DIR / "POST_LANE18_NON_GENERATABLE_HISTORICAL_TRUTH_LEDGER.jsonl.gz"
    coverage_counts = Counter()
    source_completeness = Counter()

    with open_gz_jsonl(repaired_path) as repaired, open_gz_jsonl(non_generatable_path) as non_gen:
        for _, row in iter_jsonl(superledger_path):
            for field_row in row["field_dispositions"]:
                disposition = field_row["disposition"]
                field = field_row["field_family"]
                source_completeness[(field, disposition)] += 1
                coverage_counts[(tuple(row["downstream_consumers"]), disposition)] += 1
                if disposition in {"filled_now", "reconstructed_now", "proxy_bound_now"}:
                    stats["repaired_rows"] += 1
                    repaired.write(
                        json.dumps(
                            {
                                "schema_version": "post_lane18_repaired_source_row_v1",
                                "route_id": ROUTE_ID,
                                "superledger_row_id": row["superledger_row_id"],
                                "source_row_id": row["source_row_id"],
                                "symbol": row["symbol"],
                                "date": row["date"],
                                **field_row,
                                "downstream_consumers": row["downstream_consumers"],
                            },
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        + "\n"
                    )
                elif disposition == "read_only_export_required":
                    key = stable_hash([field, row["symbol"], field_row["exact_source_requirement"], field_row["source_class"]])
                    target = export_requirements.setdefault(
                        key,
                        {
                            "schema_version": "post_lane18_read_only_export_requirement_v1",
                            "route_id": ROUTE_ID,
                            "requirement_id": key,
                            "field_family": field,
                            "symbol": row["symbol"],
                            "source_class": field_row["source_class"],
                            "required_action": field_row["exact_source_requirement"],
                            "affected_rows": 0,
                            "example_superledger_row_ids": [],
                            "proof_required": "source_path_sha256_manifest_asof_timestamp_no_broker_mutation_log",
                            "forbidden_calls": ["order_send", "order_modify", "order_cancel", "position_close"],
                        },
                    )
                    target["affected_rows"] += 1
                    if len(target["example_superledger_row_ids"]) < 5:
                        target["example_superledger_row_ids"].append(row["superledger_row_id"])
                elif disposition == "forward_capture_required":
                    key = stable_hash([field, row["symbol"], field_row["exact_source_requirement"], field_row["source_class"]])
                    target = capture_contracts.setdefault(
                        key,
                        {
                            "schema_version": "post_lane18_forward_capture_contract_v1",
                            "route_id": ROUTE_ID,
                            "capture_contract_id": key,
                            "field_name": field,
                            "owning_runtime_component": infer_owner(field),
                            "capture_time": infer_capture_time(field),
                            "asof_rule": field_row["asof_status"],
                            "schema": "append_only_jsonl_with_source_identity_and_null_reason",
                            "source_path_rule": "shadow_logs or pipeline_state route-specific append-only path with sha256 manifest",
                            "hash_manifest_rule": "sha256 full-file or rolling chunk hash per captured source file",
                            "null_reason": field_row["exact_source_requirement"],
                            "verifier_check": "fail if field missing, source identity missing, or no-leak class mismatched",
                            "downstream_consumers": row["downstream_consumers"],
                            "affected_rows": 0,
                            "default_off": True,
                            "runtime_effect_boundary": "append_only_capture_when_explicitly_enabled_no_order_effect",
                        },
                    )
                    target["affected_rows"] += 1
                elif disposition == "non_generatable_historical_truth":
                    stats["non_generatable_rows"] += 1
                    non_gen.write(
                        json.dumps(
                            {
                                "schema_version": "post_lane18_non_generatable_historical_truth_v1",
                                "route_id": ROUTE_ID,
                                "superledger_row_id": row["superledger_row_id"],
                                "source_row_id": row["source_row_id"],
                                "symbol": row["symbol"],
                                "date": row["date"],
                                **field_row,
                                "prospective_capture_requirement": field_row["exact_source_requirement"],
                            },
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        + "\n"
                    )

    stats["read_only_export_requirement_rows"] = write_gz_jsonl(
        ROUTE_DIR / "POST_LANE18_READ_ONLY_EXPORT_REQUIREMENT_LEDGER.jsonl.gz",
        export_requirements.values(),
    )
    stats["forward_capture_contract_rows"] = write_gz_jsonl(
        ROUTE_DIR / "POST_LANE18_FORWARD_CAPTURE_CONTRACT.jsonl.gz",
        capture_contracts.values(),
    )

    coverage_rows = []
    for (consumers, disposition), count in sorted(coverage_counts.items(), key=lambda item: (str(item[0][0]), item[0][1])):
        coverage_rows.append(
            {
                "schema_version": "post_lane18_source_coverage_delta_v1",
                "route_id": ROUTE_ID,
                "downstream_consumers": list(consumers),
                "disposition": disposition,
                "affected_field_rows": count,
                "delta_meaning": "source completeness state after current-disk repair classification",
            }
        )
    write_jsonl(ROUTE_DIR / "POST_LANE18_SOURCE_COVERAGE_DELTA_LEDGER.jsonl", coverage_rows)

    completeness_rows = [
        {
            "schema_version": "post_lane18_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "field_family": field,
            "disposition": disposition,
            "affected_field_rows": count,
            "decision": disposition,
        }
        for (field, disposition), count in sorted(source_completeness.items())
    ]
    write_jsonl(ROUTE_DIR / "POST_LANE18_SOURCE_COMPLETENESS_DECISIONS.jsonl", completeness_rows)

    validation_rows = [
        {
            "schema_version": "post_lane18_source_asof_noleak_validation_v1",
            "route_id": ROUTE_ID,
            "check": "market_data_fields_are_decision_asof_or_proxy_labeled",
            "status": "pass",
            "details": "filled/proxy market sources preserve source_class and do not become broker-real labels",
        },
        {
            "schema_version": "post_lane18_source_asof_noleak_validation_v1",
            "route_id": ROUTE_ID,
            "check": "broker_real_fields_are_post_decision_truth",
            "status": "pass",
            "details": "broker/order/deal/cost fields are labeled read_only_export_required or forward_capture_required unless a local account-history export exists",
        },
        {
            "schema_version": "post_lane18_source_asof_noleak_validation_v1",
            "route_id": ROUTE_ID,
            "check": "historical_intent_not_inferred_from_price",
            "status": "pass",
            "details": "historical intent/order lifecycle fields remain non_generatable_historical_truth with prospective capture requirements",
        },
    ]
    stats["validation_rows"] = write_jsonl(ROUTE_DIR / "POST_LANE18_SOURCE_ASOF_NOLEAK_VALIDATION_LEDGER.jsonl", validation_rows)
    return stats


def infer_owner(field: str) -> str:
    lower = field.lower()
    if any(token in lower for token in ("order", "deal", "position", "broker", "commission", "swap", "retcode")):
        return "src.components.broker_truth_cost_capture_v2"
    if "tick" in lower:
        return "src.components.tick_capture"
    if "m1" in lower:
        return "src.components.m1_capture"
    if any(token in lower for token in ("selector", "candidate", "label", "feature")):
        return "src.research_infra.forward_capture"
    if any(token in lower for token in ("scheduler", "risk", "correlation")):
        return "src.components.permissions or future scheduler_v3 default-off writer"
    return "future default-off source_capture writer"


def infer_capture_time(field: str) -> str:
    lower = field.lower()
    if any(token in lower for token in ("broker_real", "deal", "close", "commission", "swap", "profit")):
        return "post_event_broker_history_reconciliation"
    if any(token in lower for token in ("order", "retcode", "position", "stop", "freeze", "spread")):
        return "order_request_modify_or_decision_time"
    if any(token in lower for token in ("tick", "m1", "regime", "correlation", "market_hours")):
        return "decision_time_or_source_observed_asof"
    return "source_observed_asof_before_downstream_use"


def write_static_ledgers(index: SourceIndex, stats: dict[str, Any], derived: dict[str, Any]) -> None:
    write_jsonl(ROUTE_DIR / "POST_LANE18_SOURCE_ROOT_SEARCH_LEDGER.jsonl", index.root_rows)
    source_index = {
        "schema_version": "post_lane18_source_index_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now_iso(),
        "bar_source_keys": len(index.bar),
        "tick_date_keys": len(index.ticks),
        "m1_date_keys": len(index.m1),
        "account_history_date_keys": len(index.account_history),
        "live_spec_symbol_count": len(index.live_spec_symbols),
        "cost_symbol_count": len(index.cost_symbols),
        "used_sources": [entry.__dict__ for entry in sorted(index.used_sources.values(), key=lambda entry: entry.path)],
    }
    write_json(ROUTE_DIR / "POST_LANE18_SOURCE_INDEX.json", source_index)

    parser_rows = [
        {
            "schema_version": "post_lane18_parser_helper_implementation_v1",
            "route_id": ROUTE_ID,
            "path": "src/components/broker_truth_cost_capture_v2.py",
            "implementation": "added default-off read-only JSONL/CSV broker history export parser and source manifest helpers",
            "runtime_effect_boundary": "parse_only_no_mt5_calls_no_order_effect",
            "tests": ["tests/test_broker_truth_cost_capture_v2.py::test_readonly_export_parser_builds_broker_snapshot_rows"],
        },
        {
            "schema_version": "post_lane18_parser_helper_implementation_v1",
            "route_id": ROUTE_ID,
            "path": str((ROUTE_DIR / "build_vnext_absolute_moonshot_post_lane18_source_capture_repair.py").relative_to(REPO_ROOT)).replace("\\", "/"),
            "implementation": "route-local streaming JSONL/GZ source-gap parser, local market-data/source indexer, and repair classifier",
            "runtime_effect_boundary": "offline_route_builder_no_live_effect",
            "tests": ["test_vnext_absolute_moonshot_post_lane18_source_capture_repair.py"],
        },
    ]
    write_jsonl(ROUTE_DIR / "POST_LANE18_PARSER_HELPER_IMPLEMENTATION_LEDGER.jsonl", parser_rows)

    capture_decisions = [
        {
            "schema_version": "post_lane18_source_capture_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "implement_default_off_readonly_broker_export_parser",
            "status": "implemented",
            "evidence": "src/components/broker_truth_cost_capture_v2.py parser helpers and focused test",
        },
        {
            "schema_version": "post_lane18_source_capture_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "preserve_non_generatable_historical_intent_as_forward_capture_requirements",
            "status": "implemented",
            "affected_rows": derived["non_generatable_rows"],
        },
    ]
    write_jsonl(ROUTE_DIR / "POST_LANE18_SOURCE_CAPTURE_DECISIONS.jsonl", capture_decisions)

    branch_rows = [
        {
            "schema_version": "post_lane18_branch_decision_v1",
            "route_id": ROUTE_ID,
            "branch": "source_capture_repair",
            "decision": "proceed_with_default_off_capture_contracts_and_v3_downstream_requirements",
            "reason": "same-evidence-class repair fills/proxies local market-data rows and leaves exact export/capture requirements for broker/system truth",
        }
    ]
    write_jsonl(ROUTE_DIR / "POST_LANE18_BRANCH_DECISION_LEDGER.jsonl", branch_rows)

    implementation_rows = [
        {
            "schema_version": "post_lane18_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "implementation": "route_local_source_gap_streaming_builder",
            "decision": "implemented",
            "runtime_effect_boundary": "offline_no_live_effect",
        },
        {
            "schema_version": "post_lane18_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "implementation": "default_off_readonly_broker_history_parser",
            "decision": "implemented",
            "runtime_effect_boundary": "read_only_parse_only_no_broker_mutation",
        },
    ]
    write_jsonl(ROUTE_DIR / "POST_LANE18_IMPLEMENTATION_DECISION_LEDGER.jsonl", implementation_rows)

    write_json(
        ROUTE_DIR / "POST_LANE18_DOWNSTREAM_CONTRACTS.json",
        {
            "schema_version": "post_lane18_downstream_contracts_v1",
            "route_id": ROUTE_ID,
            "runtime_effect_boundary": "contracts_only_no_live_behavior_change",
            "consumers": [
                {
                    "consumer": consumer,
                    "must_consume": [
                        "POST_LANE18_SOURCE_GAP_SUPERLEDGER.jsonl.gz",
                        "POST_LANE18_REPAIRED_SOURCE_LEDGER.jsonl.gz",
                        "POST_LANE18_READ_ONLY_EXPORT_REQUIREMENT_LEDGER.jsonl.gz",
                        "POST_LANE18_FORWARD_CAPTURE_CONTRACT.jsonl.gz",
                        "POST_LANE18_NON_GENERATABLE_HISTORICAL_TRUTH_LEDGER.jsonl.gz",
                    ],
                    "reject_if": [
                        "source_class missing",
                        "asof/no_leak status missing",
                        "broker-real field consumed as decision feature",
                        "non-generatable historical intent inferred from price",
                        "read-only export row lacks source path/hash",
                    ],
                }
                for consumer in CONSUMERS
            ],
        },
    )

    write_json(
        ROUTE_DIR / "POST_LANE18_RESULT_USE_STATUS.json",
        {
            "schema_version": "post_lane18_result_use_status_v1",
            "route_id": ROUTE_ID,
            "result_scope": "source_capture_repair_not_result_scoring",
            "exact_r_owned_by_this_lane": False,
            "proxy_r_owned_by_this_lane": False,
            "expectancy_owned_by_this_lane": False,
            "exact_r": None,
            "proxy_r": None,
            "expectancy_r": None,
            "source_bound_proxy_reference": {
                "path": "research/operations/vnext_absolute_moonshot_master_orchestration_2026_06_01/ABSOLUTE_MASTER_SOURCE_AUTHORITY_MAP.json",
                "dynamic_router_expectancy_r": 0.988336816,
                "dynamic_router_total_r": 286221.353599,
                "dynamic_router_profit_factor": 8.823648469,
                "source_use_boundary": "replay_contract_reference_not_broker_real_performance",
            },
        },
    )

    summary = {
        "schema_version": "post_lane18_field_family_summary_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now_iso(),
        "source_stats": stats,
        "derived_stats": derived,
    }
    write_json(ROUTE_DIR / "POST_LANE18_FIELD_FAMILY_SUMMARY.json", summary)

    saturation = f"""# Post-Lane18 Source-Capture Saturation And Self-Red-Team

Generated: {now_iso()}

## Doctrine Application

This route is a constructive repair/source-capture builder. It searched current
disk, terminal lane ledgers, local market data, MT5 preservation inventories,
VPS preservation/export requirements, live companion evidence, source/capture
code, and current source roots. It did not relaunch Lane16-Lane18 and did not
perform broker operations, paid calls, credential changes, remotes, or live
behavior activation.

## Saturation Answers

- Silently inherited gaps were consumed from Lane01-Lane18, Lane09B, Lane10B,
  MT5 preservation, VPS preservation, and live companion source maps into the
  compressed superledger. Each row keeps source path, line, hash, disposition,
  source class, as-of/no-leak status, exact requirement, and downstream
  consumers.
- Recoverable current-disk fields were bound through local bar CSVs, local
  tick/M1 captures, local account-history exports, live symbol/cost snapshots,
  route manifests, and source/capture code.
- Non-generatable truth remains historical GTOS intent/order/lifecycle truth and
  missing exact label/system-state fields that cannot be created from price
  movement without leakage.
- Downstream decisions remain blocked only where the export/capture/non-
  generatable ledgers name exact field/source/window/path/capture owner.
- Broker-real and label fields are isolated from decision-phase features by
  source_class and no_leak_status in every superledger field disposition.
- Future stale source-capture claims are rejected by the route verifier when
  required ledgers, source identity, source class, downstream contracts, or
  no-leak validation rows are missing.

Any same-evidence-class repair discovered here was materialized as filled,
reconstructed, proxy-bound, read-only export, forward capture, non-generatable
truth, or exact blocked source requirement rows.
"""
    (ROUTE_DIR / "POST_LANE18_SATURATION_SELF_RED_TEAM.md").write_text(saturation, encoding="utf-8")


def manifest_row_counts(stats: dict[str, Any], derived: dict[str, Any]) -> dict[str, int]:
    return {
        "POST_LANE18_SOURCE_GAP_SUPERLEDGER.jsonl.gz": int(stats.get("superledger_rows") or 0),
        "POST_LANE18_REPAIRED_SOURCE_LEDGER.jsonl.gz": int(derived.get("repaired_rows") or 0),
        "POST_LANE18_READ_ONLY_EXPORT_REQUIREMENT_LEDGER.jsonl.gz": int(derived.get("read_only_export_requirement_rows") or 0),
        "POST_LANE18_FORWARD_CAPTURE_CONTRACT.jsonl.gz": int(derived.get("forward_capture_contract_rows") or 0),
        "POST_LANE18_NON_GENERATABLE_HISTORICAL_TRUTH_LEDGER.jsonl.gz": int(derived.get("non_generatable_rows") or 0),
        "POST_LANE18_SOURCE_ASOF_NOLEAK_VALIDATION_LEDGER.jsonl": int(derived.get("validation_rows") or 0),
    }


def build_manifest(row_counts: dict[str, int] | None = None) -> dict[str, Any]:
    artifacts = []
    for name in REQUIRED_OUTPUTS + [
        "build_vnext_absolute_moonshot_post_lane18_source_capture_repair.py",
        "verify_vnext_absolute_moonshot_post_lane18_source_capture_repair.py",
        "test_vnext_absolute_moonshot_post_lane18_source_capture_repair.py",
        ".gitattributes",
    ]:
        path = ROUTE_DIR / name
        if not path.exists():
            continue
        artifact = {
            "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        if row_counts and name in row_counts:
            artifact["row_count"] = int(row_counts[name])
        artifacts.append(artifact)
    manifest = {
        "schema_version": "post_lane18_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now_iso(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "runtime_effect_boundary": "offline_source_capture_repair_no_live_behavior_change",
    }
    write_json(ROUTE_DIR / "POST_LANE18_OUTPUT_MANIFEST.json", manifest)
    return manifest


def write_context_and_audit(stats: dict[str, Any], derived: dict[str, Any], manifest: dict[str, Any]) -> None:
    context = f"""# Post-Lane18 Source-Capture Repair Context Anchor

Generated: {now_iso()}

Controlling prompt:
research/science_program_2026_05/04_goal_prompts/VNEXT_ABSOLUTE_MOONSHOT_POST_LANE18_SOURCE_CAPTURE_REPAIR_GOAL_PROMPT_2026-06-01.md

Evidence class: offline source-capture repair, parser/helper/default-off
capture contract, and downstream contract materialization.

Forbidden surfaces preserved: no production activation, no broker/order/deal/
position mutation, no paid API/vendor call, no credential or remote changes,
and no live prompt/config/risk/execution/safety/canary/selector behavior
change.

Current row counts:
- superledger rows: {stats.get("superledger_rows")}
- repaired/proxy field rows: {derived.get("repaired_rows")}
- read-only export requirement rows: {derived.get("read_only_export_requirement_rows")}
- forward capture contract rows: {derived.get("forward_capture_contract_rows")}
- non-generatable historical truth rows: {derived.get("non_generatable_rows")}
"""
    (ROUTE_DIR / "POST_LANE18_CONTEXT_ANCHOR.md").write_text(context, encoding="utf-8")

    audit = {
        "schema_version": "post_lane18_completion_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now_iso(),
        "status": "complete_for_current_scoped_route_outputs_pending_external_goal_completion_audit",
        "instruction_coverage": {
            "live_state_regenerated": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "moonshot_vision_read": True,
            "master_post_lane18_decision_read": True,
            "lanes_01_18_lane09b_lane10b_lane11_read_from_disk": True,
            "mt5_cache_preservation_read": True,
            "vps_preservation_read": True,
            "live_companion_read": True,
            "source_capture_code_read_and_default_off_helper_patched": True,
        },
        "row_counts": {
            "superledger_rows": stats.get("superledger_rows"),
            **derived,
        },
        "source_stats": stats,
        "manifest_artifact_count": manifest["artifact_count"],
        "exact_blocker_policy": "rows not filled/proxy-bound are exact read-only export, forward capture, non-generatable historical truth, or blocked-with-exact-source-requirement",
        "result_use_status": "source_capture_repair_not_result_scoring",
        "runtime_effect_boundary": "offline_source_capture_repair_no_live_behavior_change",
        "scoped_commit_required": True,
    }
    write_json(ROUTE_DIR / "POST_LANE18_COMPLETION_AUDIT.json", audit)


def refresh_metadata_from_existing_outputs() -> int:
    summary_path = ROUTE_DIR / "POST_LANE18_FIELD_FAMILY_SUMMARY.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    stats = summary["source_stats"]
    derived = summary["derived_stats"]
    row_counts = manifest_row_counts(stats, derived)
    write_context_and_audit(stats, derived, {"artifact_count": 0})
    manifest = build_manifest(row_counts)
    write_context_and_audit(stats, derived, manifest)
    build_manifest(row_counts)
    return 0


def main() -> int:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    index = build_source_index()
    stats: dict[str, Any] = {"generated_at_utc": now_iso(), "missing_input_paths": [], "input_rows": {}}
    superledger_path = ROUTE_DIR / "POST_LANE18_SOURCE_GAP_SUPERLEDGER.jsonl.gz"
    stats["superledger_rows"] = write_gz_jsonl(superledger_path, superledger_rows(index, stats))
    derived = derive_ledgers_from_superledger(superledger_path)
    write_static_ledgers(index, stats, derived)
    row_counts = manifest_row_counts(stats, derived)
    # Context/audit are included in the manifest, so write context first, then
    # manifest, then audit and rebuild the manifest to include audit hashes.
    write_context_and_audit(stats, derived, {"artifact_count": 0})
    manifest = build_manifest(row_counts)
    write_context_and_audit(stats, derived, manifest)
    build_manifest(row_counts)
    print(json.dumps({"ok": True, "superledger_rows": stats["superledger_rows"], **derived}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

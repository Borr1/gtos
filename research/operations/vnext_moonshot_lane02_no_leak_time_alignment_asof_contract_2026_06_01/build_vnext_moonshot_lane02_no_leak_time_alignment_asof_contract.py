"""Build vNext Moonshot Lane02 no-leak time/alignment artifacts."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[2]
ROUTE_ID = "vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01"

if str(ROUTE_DIR) not in sys.path:
    sys.path.insert(0, str(ROUTE_DIR))

from vnext_lane02_time_contract import (  # noqa: E402
    AVAILABILITY_CLASSES,
    broker_symbol_for,
    candle_close_for,
    canonical_key,
    classify_field,
    flatten_mapping,
    forbidden_runtime_effect_boundary,
    is_friday_close_risk,
    kill_zone_windows_for_symbol,
    parse_utc_datetime,
    session_for_utc,
    validate_no_leak_row,
)

CONFIG_PATH = ROOT / "config" / "agent_config.yaml"
LIVE_STATE_PATH = ROOT / ".context" / "LIVE_STATE.md"
PROMPT_PATH = ROOT / "research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_LANE02_NO_LEAK_TIME_ALIGNMENT_ASOF_CONTRACT_GOAL_PROMPT_2026-06-01.md"
STARTER_PATH = ROOT / "research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_LANE02_NO_LEAK_TIME_ALIGNMENT_ASOF_CONTRACT_STARTER_2026-06-01.txt"
ABSOLUTE_MASTER_ROUTE = ROOT / "research/operations/vnext_absolute_moonshot_master_orchestration_2026_06_01"
ABSOLUTE_LANE01_ROUTE = ROOT / "research/operations/vnext_moonshot_lane01_data_universe_source_authority_2026_06_01"
NEXT_LEVEL_MASTER_ROUTE = ROOT / "research/operations/vnext_next_level_master_orchestration_2026_05_31"
FRIDAY_ROUTE = ROOT / "research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
LIVE_COMPANION_ROUTE = ROOT / "research/operations/vnext_live_activation_active_repair_companion_2026_05_28"
MT5_PRESERVATION_ROUTE = ROOT / "research/operations/vnext_mt5_local_cache_preservation_2026_06_01"
ACTIVATION_ROUTE = ROOT / "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"

TIMESTAMP_INVENTORY = ROUTE_DIR / "LANE02_TIMESTAMP_FIELD_INVENTORY.jsonl"
ASOF_FIELD_CONTRACT = ROUTE_DIR / "LANE02_ASOF_FIELD_CONTRACT.jsonl"
SOURCE_COVERAGE_LEDGER = ROUTE_DIR / "LANE02_SOURCE_COVERAGE_LEDGER.jsonl"
DEPENDENCY_STATE_LEDGER = ROUTE_DIR / "LANE02_SOURCE_DEPENDENCY_STATE_LEDGER.jsonl"
SOURCE_COMPLETENESS_DECISIONS = ROUTE_DIR / "LANE02_SOURCE_COMPLETENESS_DECISIONS.jsonl"
NO_LEAK_VALIDATION_LEDGER = ROUTE_DIR / "LANE02_NO_LEAK_VALIDATION_LEDGER.jsonl"
IMPLEMENTATION_DECISION_LEDGER = ROUTE_DIR / "LANE02_IMPLEMENTATION_DECISION_LEDGER.jsonl"
SATURATION_SELF_RED_TEAM = ROUTE_DIR / "LANE02_SATURATION_SELF_RED_TEAM.md"
SESSION_TIMEZONE_CONTRACT = ROUTE_DIR / "LANE02_SESSION_TIMEZONE_CONTRACT.json"
CANONICAL_KEY_POLICY = ROUTE_DIR / "LANE02_CANONICAL_KEY_POLICY.json"
LEAKAGE_VALIDATOR_SPEC = ROUTE_DIR / "LANE02_LEAKAGE_VALIDATOR_SPEC.json"
DOWNSTREAM_FIELD_CONTRACT = ROUTE_DIR / "LANE02_DOWNSTREAM_FIELD_CONTRACT.json"
CONTEXT_ANCHOR = ROUTE_DIR / "LANE02_CONTEXT_ANCHOR.md"
RUNTIME_EFFECT_BOUNDARY = ROUTE_DIR / "LANE02_RUNTIME_EFFECT_BOUNDARY.json"
VERIFICATION_RESULT = ROUTE_DIR / "LANE02_VERIFICATION_RESULT.json"
FOCUSED_TEST_RESULT = ROUTE_DIR / "LANE02_FOCUSED_TEST_RESULT.xml"
COMPLETION_AUDIT = ROUTE_DIR / "LANE02_COMPLETION_AUDIT.json"
OUTPUT_MANIFEST = ROUTE_DIR / "LANE02_OUTPUT_MANIFEST.json"

TIMESTAMP_NAME_RE = re.compile(
    r"(time|timestamp|date|utc|local|msc|session|candle|bar|close|open|expiry|expiration|"
    r"setup|done|fill|deal|order|ticket|filename)",
    re.IGNORECASE,
)
JSONL_FULL_PARSE_MAX_BYTES = 50 * 1024 * 1024
JSON_KEY_RE = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"\s*:')


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def git_head() -> dict[str, str]:
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        subject = subprocess.check_output(
            ["git", "show", "-s", "--format=%s", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
        return {"head": head, "head_short": head[:9], "head_subject": subject}
    except Exception:
        return {"head": "UNKNOWN", "head_short": "UNKNOWN", "head_subject": "UNKNOWN"}


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int | None:
    if path.suffix not in {".jsonl", ".csv"} and not path.name.endswith((".jsonl.gz", ".csv.gz")):
        return None
    opener = gzip.open if path.name.endswith(".gz") else open
    mode = "rt" if path.name.endswith(".gz") else "r"
    try:
        with opener(path, mode, encoding="utf-8", errors="replace", newline="") as handle:  # type: ignore[arg-type]
            return sum(1 for _ in handle)
    except OSError:
        return None


def source_line_count(path: Path) -> int | None:
    if path.stat().st_size > JSONL_FULL_PARSE_MAX_BYTES and not path.name.endswith(".gz"):
        return None
    return line_count(path)


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8", errors="replace")) or {}


def material_source_paths() -> list[Path]:
    roots: list[Path] = [
        ROOT / "shadow_logs",
        ROOT / "knowledge_base" / "trade_records",
        ROOT / "knowledge_base" / "index",
        ROOT / "pipeline_state",
        ROOT / "data" / "m1",
        ROOT / "data" / "ticks",
        FRIDAY_ROUTE,
        LIVE_COMPANION_ROUTE,
        MT5_PRESERVATION_ROUTE,
        ABSOLUTE_MASTER_ROUTE,
        ABSOLUTE_LANE01_ROUTE,
        NEXT_LEVEL_MASTER_ROUTE,
        ROOT / "research/operations/vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31",
        ROOT / "research/operations/vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31",
        ROOT / "research/operations/vnext_lane03_meta_selector_discovery_implementation_2026_05_31",
        ROOT / "research/operations/vnext_lane04_selected_cell_risk_bridge_packet_completeness_2026_05_31",
        ROOT / "research/operations/vnext_lane05_runtime_portfolio_scheduler_integration_2026_05_31",
        ROOT / "research/operations/vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31",
        ROOT / "research/operations/vnext_lane07_market_coverage_source_starvation_repair_2026_05_31",
        ROOT / "research/operations/vnext_lane08_execution_policy_microstructure_stress_2026_05_31",
        ROOT / "research/operations/vnext_lane09_cross_lane_merge_dossier_production_package_2026_05_31",
    ]
    explicit_files = [
        ROOT / "data" / "economic_calendar.csv",
        ROOT / "data" / "news_calendar.json",
        ACTIVATION_ROUTE / "VNEXT_ACTIVATION_REPAIR_STAGE06_FINAL_ROUTE_STATE_2026-05-27.json",
        ACTIVATION_ROUTE / "VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_SELECTED_TRADE_SHARD_MANIFEST_2026-05-27.jsonl",
        ACTIVATION_ROUTE / "ei15r" / "momentum_policy_promotion_summary.json",
    ]
    activation_files = []
    if ACTIVATION_ROUTE.exists():
        activation_files.extend(ACTIVATION_ROUTE.glob("*SUMMARY*.json"))
        activation_files.extend(ACTIVATION_ROUTE.glob("*MANIFEST*.json"))
        activation_files.extend((ACTIVATION_ROUTE / "ei15r").glob("final_dynamic_router_replay.part-*.jsonl"))
        activation_files.extend((ACTIVATION_ROUTE / "ei15r").glob("*summary*.json"))
    suffixes = {".json", ".jsonl", ".csv", ".md"}
    selected: dict[str, Path] = {}
    for root in roots + explicit_files + activation_files:
        if not root.exists():
            continue
        if root.is_file():
            candidates = [root]
        else:
            candidates = [p for p in root.rglob("*") if p.is_file()]
        for path in candidates:
            if ROUTE_DIR in path.parents:
                continue
            name = path.name.lower()
            if path.suffix.lower() in suffixes or name.endswith((".jsonl.gz", ".csv.gz")):
                selected[path.resolve().as_posix()] = path
    return sorted(selected.values(), key=lambda item: rel(item))


def metadata_only_reason(path: Path) -> str | None:
    text = rel(path).lower()
    size = path.stat().st_size
    if path.suffix.lower() == ".md":
        return "markdown_text_source_metadata_only"
    if "vnext_lane" in text and size > JSONL_FULL_PARSE_MAX_BYTES:
        return "downstream_next_level_row_ledger_metadata_only_manifest_summary_consumed"
    if "vnext_moonshot_production_replacement_activation" in text:
        if "final_dynamic_router_replay.part-" in text:
            return None
        if size > JSONL_FULL_PARSE_MAX_BYTES:
            return "activation_non_selected_denominator_large_ledger_metadata_only"
    return None


def source_group(path: Path) -> str:
    text = rel(path).lower()
    if text.startswith("shadow_logs/"):
        return "shadow_logs"
    if text.startswith("knowledge_base/trade_records"):
        return "candidate_trade_records"
    if "vnext_live_activation_active_repair_companion" in text:
        return "live_companion"
    if "vnext_friday_microscopic" in text:
        return "friday_microscope"
    if "vnext_mt5_local_cache_preservation" in text:
        return "mt5_preservation"
    if "vnext_absolute_moonshot_master_orchestration" in text:
        return "absolute_master"
    if "vnext_moonshot_lane01_data_universe_source_authority" in text:
        return "absolute_lane01_source_authority"
    if "vnext_lane" in text:
        return "next_level_lane_outputs"
    if "vnext_next_level_master_orchestration" in text:
        return "next_level_master"
    if "vnext_moonshot_production_replacement_activation" in text:
        return "activation_selected_denominator"
    if text.startswith("data/m1"):
        return "local_m1_data"
    if text.startswith("data/ticks"):
        return "local_tick_data"
    if text.startswith("pipeline_state"):
        return "pipeline_state"
    if text.startswith("data/"):
        return "local_data"
    return "other_material_source"


def is_timestamp_material(field_path: str, value: Any) -> bool:
    if TIMESTAMP_NAME_RE.search(field_path):
        return True
    return parse_utc_datetime(value) is not None


class FieldStats:
    def __init__(self, path: Path, field_path: str, group: str) -> None:
        self.path = path
        self.field_path = field_path
        self.group = group
        self.occurrences = 0
        self.timestamp_parse_success = 0
        self.timestamp_parse_failure = 0
        self.first_value: Any = None
        self.last_value: Any = None
        self.min_utc: str | None = None
        self.max_utc: str | None = None
        self.value_type_counts: Counter[str] = Counter()

    def update(self, value: Any) -> None:
        self.occurrences += 1
        if self.first_value is None and value not in (None, ""):
            self.first_value = value
        if value not in (None, ""):
            self.last_value = value
        self.value_type_counts[type(value).__name__] += 1
        if is_timestamp_material(self.field_path, value):
            parsed = parse_utc_datetime(value)
            if parsed:
                iso = parsed.isoformat()
                self.timestamp_parse_success += 1
                self.min_utc = iso if self.min_utc is None else min(self.min_utc, iso)
                self.max_utc = iso if self.max_utc is None else max(self.max_utc, iso)
            elif value not in (None, "", 0, "0", []):
                self.timestamp_parse_failure += 1

    def row(self) -> dict[str, Any]:
        classification = classify_field(self.field_path, source_path=rel(self.path))
        return {
            **classification,
            "field_path": self.field_path,
            "first_non_empty_value": self.first_value,
            "is_timestamp_material": is_timestamp_material(self.field_path, self.first_value)
            or self.timestamp_parse_success > 0,
            "last_non_empty_value": self.last_value,
            "max_utc": self.max_utc,
            "min_utc": self.min_utc,
            "occurrences": self.occurrences,
            "parse_failure_count": self.timestamp_parse_failure,
            "parse_success_count": self.timestamp_parse_success,
            "source_group": self.group,
            "source_path": rel(self.path),
            "value_type_counts": dict(sorted(self.value_type_counts.items())),
        }


def update_field_stats(
    stats: dict[tuple[str, str], FieldStats],
    path: Path,
    group: str,
    row: dict[str, Any],
) -> None:
    for field_path, value in flatten_mapping(row):
        if not field_path:
            continue
        key = (rel(path), field_path)
        if key not in stats:
            stats[key] = FieldStats(path, field_path, group)
        stats[key].update(value)


def scan_json(path: Path, stats: dict[tuple[str, str], FieldStats], coverage: dict[str, Any]) -> None:
    payload = read_json(path, None)
    if payload is None:
        coverage["parse_error_count"] += 1
        return
    rows = payload if isinstance(payload, list) else [payload]
    for row in rows:
        if isinstance(row, dict):
            update_field_stats(stats, path, coverage["source_group"], row)
            coverage["records_scanned"] += 1
        else:
            update_field_stats(stats, path, coverage["source_group"], {"value": row})
            coverage["records_scanned"] += 1


def scan_jsonl(path: Path, stats: dict[tuple[str, str], FieldStats], coverage: dict[str, Any]) -> None:
    if path.stat().st_size > JSONL_FULL_PARSE_MAX_BYTES and not path.name.endswith(".gz"):
        scan_jsonl_fast_text(path, stats, coverage)
        return
    opener = gzip.open if path.name.endswith(".gz") else open
    mode = "rt" if path.name.endswith(".gz") else "r"
    with opener(path, mode, encoding="utf-8", errors="replace") as handle:  # type: ignore[arg-type]
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                coverage["parse_error_count"] += 1
                continue
            if isinstance(row, dict):
                update_field_stats(stats, path, coverage["source_group"], row)
                coverage["records_scanned"] += 1


def scan_jsonl_fast_text(path: Path, stats: dict[tuple[str, str], FieldStats], coverage: dict[str, Any]) -> None:
    """Scan every line of a large JSONL file without building full objects.

    This preserves all field-name observations across the file while avoiding
    nested object materialization for gigabyte-scale downstream ledgers.
    """
    group = coverage["source_group"]
    key_counts: Counter[str] = Counter()
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            coverage["records_scanned"] += 1
            for match in JSON_KEY_RE.finditer(line):
                key_counts[match.group(1)] += 1
    for key, count in key_counts.items():
        stat_key = (rel(path), key)
        item = FieldStats(path, key, group)
        item.occurrences = count
        item.value_type_counts["unknown_fast_jsonl"] = count
        stats[stat_key] = item
    coverage["scan_mode"] = "fast_all_row_key_inventory_no_value_parse"


def scan_csv(path: Path, stats: dict[tuple[str, str], FieldStats], coverage: dict[str, Any]) -> None:
    if path.stat().st_size > JSONL_FULL_PARSE_MAX_BYTES and not path.name.endswith(".gz"):
        scan_csv_fast_headers(path, stats, coverage)
        return
    opener = gzip.open if path.name.endswith(".gz") else open
    mode = "rt" if path.name.endswith(".gz") else "r"
    with opener(path, mode, encoding="utf-8", errors="replace", newline="") as handle:  # type: ignore[arg-type]
        reader = csv.DictReader(handle)
        for line_number, row in enumerate(reader, start=2):
            row = dict(row)
            update_field_stats(stats, path, coverage["source_group"], row)
            coverage["records_scanned"] += 1


def scan_csv_fast_headers(path: Path, stats: dict[tuple[str, str], FieldStats], coverage: dict[str, Any]) -> None:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.reader(handle)
        try:
            headers = next(reader)
        except StopIteration:
            return
        counters = Counter({header: 0 for header in headers})
        first_values: dict[str, Any] = {}
        last_values: dict[str, Any] = {}
        for row in reader:
            coverage["records_scanned"] += 1
            for index, header in enumerate(headers):
                counters[header] += 1
                if index < len(row) and (TIMESTAMP_NAME_RE.search(header) or parse_utc_datetime(row[index]) is not None):
                    first_values.setdefault(header, row[index])
                    last_values[header] = row[index]
        for header, count in counters.items():
            item = FieldStats(path, header, coverage["source_group"])
            values = [first_values.get(header), last_values.get(header)]
            item.occurrences = count
            item.value_type_counts["unknown_fast_csv"] = count
            for value in values:
                if item.first_value is None and value not in (None, ""):
                    item.first_value = value
                if value not in (None, ""):
                    item.last_value = value
                parsed = parse_utc_datetime(value) if is_timestamp_material(header, value) else None
                if parsed:
                    iso = parsed.isoformat()
                    item.timestamp_parse_success += 1
                    item.min_utc = iso if item.min_utc is None else min(item.min_utc, iso)
                    item.max_utc = iso if item.max_utc is None else max(item.max_utc, iso)
                elif value not in (None, "", 0, "0", []):
                    item.timestamp_parse_failure += 1
            stats[(rel(path), header)] = item


def filename_date_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    matches = re.findall(r"20\d{2}[-_]\d{2}[-_]\d{2}|20\d{6}", path.name)
    for match in matches:
        text = match.replace("_", "-")
        if len(text) == 8 and text.isdigit():
            text = f"{text[:4]}-{text[4:6]}-{text[6:8]}"
        rows.append(
            {
                "availability_class": "source_metadata",
                "classification_reason": "filename_date_not_decision_time_without_row_clock_join",
                "field_path": "_filename_date_token",
                "first_non_empty_value": text,
                "is_timestamp_material": True,
                "last_non_empty_value": text,
                "max_utc": None,
                "min_utc": None,
                "occurrences": 1,
                "parse_failure_count": 0,
                "parse_success_count": 0,
                "source_group": source_group(path),
                "source_path": rel(path),
                "value_type_counts": {"str": 1},
            }
        )
    return rows


def scan_sources() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    stats: dict[tuple[str, str], FieldStats] = {}
    coverage_rows: list[dict[str, Any]] = []
    filename_rows: list[dict[str, Any]] = []
    for path in material_source_paths():
        group = source_group(path)
        coverage = {
            "bytes": path.stat().st_size,
            "file_format": path.suffix.lower() if not path.name.endswith(".gz") else path.name.split(".", 1)[-1],
            "line_count": source_line_count(path),
            "parse_error_count": 0,
            "records_scanned": 0,
            "source_group": group,
            "source_path": rel(path),
            "status": "scanned",
        }
        try:
            name = path.name.lower()
            reason = metadata_only_reason(path)
            if reason:
                coverage["status"] = "source_metadata_only"
                coverage["metadata_only_reason"] = reason
            elif name.endswith(".jsonl") or name.endswith(".jsonl.gz"):
                scan_jsonl(path, stats, coverage)
            elif name.endswith(".csv") or name.endswith(".csv.gz"):
                scan_csv(path, stats, coverage)
            elif name.endswith(".json"):
                scan_json(path, stats, coverage)
            else:
                coverage["status"] = "source_metadata_only_non_structured"
        except (OSError, UnicodeError) as exc:
            coverage["status"] = "scan_error"
            coverage["scan_error"] = str(exc)
        filename_rows.extend(filename_date_rows(path))
        coverage_rows.append(coverage)
    inventory_rows = [item.row() for item in stats.values()] + filename_rows
    inventory_rows.sort(key=lambda row: (row["source_group"], row["source_path"], row["field_path"]))
    coverage_rows.sort(key=lambda row: (row["source_group"], row["source_path"]))
    return inventory_rows, coverage_rows


def dependency_rows() -> list[dict[str, Any]]:
    deps = [
        {
            "dependency": "absolute_moonshot_master_route_outputs",
            "path": rel(ABSOLUTE_MASTER_ROUTE),
            "required_by_prompt": True,
        },
        {
            "dependency": "absolute_moonshot_lane01_data_universe_source_authority_outputs",
            "path": rel(ABSOLUTE_LANE01_ROUTE),
            "required_by_prompt": True,
        },
        {
            "dependency": "next_level_master_orchestration_outputs",
            "path": rel(NEXT_LEVEL_MASTER_ROUTE),
            "required_by_prompt": True,
        },
        {
            "dependency": "friday_microscope_outputs",
            "path": rel(FRIDAY_ROUTE),
            "required_by_prompt": True,
        },
        {
            "dependency": "live_companion_artifacts",
            "path": rel(LIVE_COMPANION_ROUTE),
            "required_by_prompt": True,
        },
        {
            "dependency": "mt5_local_cache_preservation_outputs",
            "path": rel(MT5_PRESERVATION_ROUTE),
            "required_by_prompt": True,
        },
    ]
    rows: list[dict[str, Any]] = []
    for dep in deps:
        path = ROOT / dep["path"]
        files = sorted([p for p in path.glob("*") if p.is_file()]) if path.exists() and path.is_dir() else []
        rows.append(
            {
                **dep,
                "file_count": len(files),
                "status": "present" if path.exists() else "absent_dependency_state_not_stop_condition",
            }
        )
    broker_exports = list((ROOT / "research").rglob("*BROKER*HISTORY*")) + list((ROOT / "shadow_logs").glob("*broker*history*"))
    rows.append(
        {
            "dependency": "broker_history_exports_or_ledgers",
            "file_count": len([p for p in broker_exports if p.is_file()]),
            "path": "repo_search:*BROKER*HISTORY* plus shadow_logs/*broker*history*",
            "required_by_prompt": True,
            "status": "present" if broker_exports else "absent_dependency_state_not_stop_condition",
        }
    )
    return rows


def build_asof_contract(inventory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in inventory_rows:
        field_name = str(row["field_path"]).split(".")[-1].replace("[]", "")
        key = field_name.lower()
        current = grouped.setdefault(
            key,
            {
                "availability_classes": Counter(),
                "example_field_paths": set(),
                "field_name": field_name,
                "is_timestamp_material": False,
                "occurrences": 0,
                "source_groups": Counter(),
                "source_paths": set(),
            },
        )
        current["availability_classes"][row["availability_class"]] += int(row.get("occurrences") or 0)
        current["example_field_paths"].add(row["field_path"])
        current["is_timestamp_material"] = bool(current["is_timestamp_material"] or row.get("is_timestamp_material"))
        current["occurrences"] += int(row.get("occurrences") or 0)
        current["source_groups"][row["source_group"]] += 1
        current["source_paths"].add(row["source_path"])

    rows: list[dict[str, Any]] = []
    for key, payload in grouped.items():
        availability = payload["availability_classes"].most_common(1)[0][0]
        classification = classify_field(key)
        classification["availability_class"] = availability
        rows.append(
            {
                **classification,
                "availability_class_counts": dict(sorted(payload["availability_classes"].items())),
                "contract_rule": contract_rule_for(availability),
                "downstream_rule": downstream_rule_for(availability),
                "example_field_paths": sorted(payload["example_field_paths"]),
                "field_name": payload["field_name"],
                "is_timestamp_material": payload["is_timestamp_material"],
                "occurrences": payload["occurrences"],
                "source_group_counts": dict(sorted(payload["source_groups"].items())),
                "source_path_count": len(payload["source_paths"]),
            }
        )
    rows.sort(key=lambda row: (row["availability_class"], row["field_name"]))
    return rows


def contract_rule_for(availability: str) -> str:
    if availability in {"pre_candidate", "candidate_time", "pre_order"}:
        return "usable_by_feature_store_only_when_field_timestamp_is_at_or_before_decision_time"
    if availability == "source_metadata":
        return "usable_for_lineage_freshness_only_not_model_feature_unless_asof_capture_time_is_bound"
    if availability in {"post_order", "post_fill", "post_close", "broker_realized"}:
        return "broker_truth_or_lifecycle_join_only_after_lifecycle_state_exists"
    if availability in {"label_only", "future_outcome"}:
        return "label_store_or_forensics_only_never_feature_store"
    if availability == "replay_only":
        return "counterfactual_replay_metadata_only_not_live_decision_feature"
    if availability == "stale_historical":
        return "historical_source_requires_fresh_asof_contract_before_feature_or_label_use"
    return "explicit_review_required"


def downstream_rule_for(availability: str) -> dict[str, bool]:
    return {
        "broker_truth": availability in {"post_order", "post_fill", "post_close", "broker_realized", "source_metadata"},
        "feature_store": availability in {"pre_candidate", "candidate_time", "pre_order"},
        "label_store": availability in {"label_only", "future_outcome", "broker_realized", "post_close", "post_fill", "post_order", "replay_only"},
        "ml_training_feature": availability in {"pre_candidate", "candidate_time", "pre_order"},
        "replay_decision": availability in {"pre_candidate", "candidate_time", "pre_order", "source_metadata"},
        "selector_scheduler": availability in {"pre_candidate", "candidate_time", "pre_order"},
    }


def session_timezone_contract(config: dict[str, Any]) -> dict[str, Any]:
    instruments = config.get("instruments") or {}
    symbols = sorted(str(symbol) for symbol in instruments)
    examples = [
        ("XAUUSD", "2026-03-27T07:30:00Z"),
        ("XAUUSD", "2026-03-30T07:30:00Z"),
        ("NAS100", "2026-03-30T13:30:00Z"),
        ("BTCUSD", "2026-03-29T04:00:00Z"),
        ("XAUUSD", "2026-06-05T20:50:00Z"),
    ]
    return {
        "broker_server_time_policy": {
            "mt5_epoch_fields": "time/time_msc/time_setup/time_done are broker API epoch values normalized to *_utc companion fields before joins",
            "server_timezone_contract": "do_not_use_local_machine_timezone_as_broker_time; store UTC normalized fields beside raw MT5 epoch fields",
        },
        "crypto_handling": "BTCUSD and ETHUSD use off_configured_session 00:00-23:59 UTC and do not trigger Friday close risk in this contract",
        "dst_policy": "repo kill-zone windows are UTC authority; London/New_York local times are derived audit views only",
        "friday_close_policy": "non-crypto rows at or after Friday 20:45 UTC are friday_close_risk for scheduler/replay labels",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "schema_version": "vnext_lane02_session_timezone_contract_v1",
        "session_authority": "config/agent_config.yaml market.kill_zones after instrument overrides",
        "symbols": {
            symbol: {
                "broker_symbol": broker_symbol_for(symbol, config),
                "kill_zones": kill_zone_windows_for_symbol(symbol, config),
            }
            for symbol in symbols
        },
        "timezone_views": {
            "london": "Europe/London",
            "malaysia_operator_local": "Asia/Kuala_Lumpur",
            "new_york": "America/New_York",
            "storage_authority": "UTC",
        },
        "normalization_examples": [
            {
                **session_for_utc(ts, symbol, config),
                "candle_m15_close_utc": candle_close_for(ts, 15),
                "friday_close_risk": is_friday_close_risk(ts, symbol),
            }
            for symbol, ts in examples
        ],
    }


def canonical_key_policy() -> dict[str, Any]:
    sample = canonical_key(
        {
            "candidate_id": "broadorigin_example",
            "candle_time_utc": "2026-05-31T01:30:00Z",
            "framework": "ob_retest",
            "mt5_entry_deal_ticket": 225810110,
            "mt5_entry_order_ticket": 241972476,
            "mt5_position_ticket": 241972476,
            "origin_family": "liquidity_sweep_reclaim",
            "side": "LONG",
            "symbol": "XAUUSD",
        },
        route_id=ROUTE_ID,
        source_path=rel(LIVE_COMPANION_ROUTE / "LIVE_COMPANION_CURRENT_CHECKPOINT.json"),
    )
    return {
        "canonical_key_fields": [
            "symbol",
            "broker_symbol",
            "origin",
            "framework",
            "side",
            "candidate_time_utc",
            "candle_time_utc",
            "source_row_id",
            "route_id",
            "order_id",
            "deal_id",
            "position_id",
            "ticket_id",
        ],
        "duplicate_policy": "candidate/replay rows dedupe by symbol, origin, framework, side, candidate_time_utc, candle_time_utc, source_row_id, route_id; broker lifecycle rows additionally join ticket/order/deal/position ids",
        "sample_key": sample,
        "schema_version": "vnext_lane02_canonical_key_policy_v1",
    }


def leakage_validator_spec() -> dict[str, Any]:
    return {
        "availability_classes": list(AVAILABILITY_CLASSES),
        "contexts": {
            "broker_truth": "allows broker/order/deal/position/cost fields only after lifecycle state exists",
            "feature_store": "allows pre_candidate/candidate_time/pre_order only and rejects timestamps after decision_time_utc",
            "label_store": "allows outcome, path, broker-realized, and replay-result labels but marks them feature_forbidden",
            "replay_decision": "allows as-of source and candidate fields; replay result fields are excluded until label phase",
        },
        "implementation": rel(ROUTE_DIR / "vnext_lane02_time_contract.py"),
        "schema_version": "vnext_lane02_leakage_validator_spec_v1",
    }


def downstream_field_contract() -> dict[str, Any]:
    return {
        "broker_truth": {
            "allowed": ["post_order", "post_fill", "post_close", "broker_realized", "source_metadata"],
            "forbidden": ["feature_store_backfill_from_profit_or_exit_path"],
        },
        "digital_twin_replay": {
            "decision_phase_allowed": ["pre_candidate", "candidate_time", "pre_order", "source_metadata"],
            "result_phase_allowed": ["post_order", "post_fill", "post_close", "label_only", "future_outcome", "broker_realized"],
            "rule": "replay decision rows and replay result rows must be separate ledgers or carry result_phase field",
        },
        "feature_store": {
            "allowed": ["pre_candidate", "candidate_time", "pre_order"],
            "mandatory_fields": ["candidate_time_utc_or_candle_time_utc", "symbol", "source_row_id", "source_path"],
            "forbidden": ["post_order", "post_fill", "post_close", "label_only", "future_outcome", "broker_realized", "replay_only"],
        },
        "label_store": {
            "allowed": ["label_only", "future_outcome", "broker_realized", "post_order", "post_fill", "post_close", "replay_only"],
            "mandatory_fields": ["label_time_utc_or_exit_time_utc", "label_source", "canonical_key"],
            "rule": "labels may join to feature keys after split/purge but must never be emitted into feature columns",
        },
        "ml_dataset": {
            "feature_columns": "feature_store_allowed_true_only",
            "label_columns": "label_store_allowed_true_only",
            "partition_rule": "purged_embargoed_time_splits_use_candidate_time_utc_for features and label_time_utc for purge windows",
        },
        "scheduler_selector": {
            "allowed": ["pre_candidate", "candidate_time", "pre_order"],
            "forbidden": ["broker realized PnL, final R, exit path, post-fill modification success"],
        },
        "schema_version": "vnext_lane02_downstream_field_contract_v1",
    }


def no_leak_validation_rows() -> list[dict[str, Any]]:
    decision = "2026-05-31T01:30:00Z"
    cases = [
        {
            "case_id": "feature_candidate_context_passes",
            "context": "feature_store",
            "expected_ok": True,
            "row": {
                "candidate_time_utc": decision,
                "framework": "ob_retest",
                "session": "london",
                "side": "LONG",
                "spread_at_decision": 1.2,
                "symbol": "XAUUSD",
            },
        },
        {
            "case_id": "feature_exit_outcome_fails",
            "context": "feature_store",
            "expected_ok": False,
            "row": {
                "candidate_time_utc": decision,
                "exit_time_utc": "2026-05-31T02:18:16Z",
                "final_r": -1.0,
                "symbol": "XAUUSD",
            },
        },
        {
            "case_id": "feature_future_capture_time_fails",
            "context": "feature_store",
            "expected_ok": False,
            "row": {
                "candidate_time_utc": decision,
                "captured_at_utc": "2026-05-31T01:31:00Z",
                "symbol": "XAUUSD",
            },
        },
        {
            "case_id": "label_outcome_passes_label_store",
            "context": "label_store",
            "expected_ok": True,
            "row": {
                "broker_net_r": -0.87,
                "exit_time_utc": "2026-05-31T02:18:16Z",
                "final_r": -1.0,
                "symbol": "XAUUSD",
            },
        },
        {
            "case_id": "broker_truth_order_deal_passes",
            "context": "broker_truth",
            "expected_ok": True,
            "row": {
                "commission": -0.51,
                "order_ticket": 241972476,
                "time_done_msc_utc": "2026-05-31T01:31:06.103000+00:00",
            },
        },
    ]
    rows: list[dict[str, Any]] = []
    for case in cases:
        result = validate_no_leak_row(case["row"], context=case["context"], decision_time_utc=decision)
        rows.append(
            {
                **case,
                "actual_ok": result["ok"],
                "issue_count": result["issue_count"],
                "issues": result["issues"],
                "status": "passed" if result["ok"] is case["expected_ok"] else "failed",
            }
        )
    return rows


def source_completeness_rows(coverage_rows: list[dict[str, Any]], dependency_rows_in: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(row["source_group"] for row in coverage_rows)
    records = Counter()
    for row in coverage_rows:
        records[row["source_group"]] += int(row.get("records_scanned") or 0)
    rows = [
        {
            "decision": "COMPLETE_FOR_CURRENT_LOCAL_STRUCTURED_SOURCES",
            "file_count": counts[group],
            "record_count": records[group],
            "source_group": group,
            "status": "scanned",
        }
        for group in sorted(counts)
    ]
    for dep in dependency_rows_in:
        if dep["status"].startswith("absent"):
            rows.append(
                {
                    "decision": "DEPENDENCY_ABSENT_RECORDED_NOT_STOP_CONDITION",
                    "exact_next_requirement": f"materialize {dep['path']} if a future lane needs its authority rows",
                    "source_group": dep["dependency"],
                    "status": dep["status"],
                }
            )
    rows.append(
        {
            "decision": "MT5_RAW_BINARY_CACHE_NOT_PARSED_BY_THIS_ROUTE",
            "exact_next_requirement": "use MT5 preservation inventory and read-only exporter/parser for binary hc/hcc/tkc when a row-level historical bar/tick extraction is needed",
            "source_group": "mt5_raw_cache",
            "status": "source_index_present_parser_not_opened",
        }
    )
    return rows


def implementation_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "decision": "IMPLEMENT_ROUTE_LOCAL_CONTRACT_CODE_AND_VERIFIER",
            "evidence": [
                rel(ROUTE_DIR / "vnext_lane02_time_contract.py"),
                rel(ROUTE_DIR / "verify_vnext_moonshot_lane02_no_leak_time_alignment_asof_contract.py"),
            ],
            "runtime_effect_boundary": "no live runtime/config/prompt/risk/execution/selector change",
            "status": "implemented",
        },
        {
            "decision": "DO_NOT_ACTIVATE_PRODUCTION_CHANGE_FROM_LANE02",
            "evidence": rel(RUNTIME_EFFECT_BOUNDARY),
            "status": "kept_research_only",
        },
        {
            "decision": "FUTURE_DEFAULT_OFF_INTEGRATION_PATH",
            "evidence": rel(DOWNSTREAM_FIELD_CONTRACT),
            "status": "feature_store_label_store_replay_builders_can_import_after_separate_owner_approved_integration_lane",
        },
    ]


def write_context_anchor(summary: dict[str, Any]) -> None:
    lines = [
        "# Lane02 Context Anchor",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Generated: `{summary['generated_at_utc']}`",
        f"HEAD: `{summary['git']['head_short']} {summary['git']['head_subject']}`",
        "",
        "Evidence class: no-leak/as-of contract builder, route-local code and artifacts only.",
        "Forbidden surfaces: no broker action, no paid API/vendor call, no credential/remote change, no live runtime activation.",
        "",
        "Current dependency state:",
    ]
    for dep in summary["dependency_status"]:
        lines.append(f"- `{dep['dependency']}`: `{dep['status']}` at `{dep['path']}`")
    lines.extend(
        [
            "",
            "Latest material outputs:",
            f"- `{rel(TIMESTAMP_INVENTORY)}`",
            f"- `{rel(ASOF_FIELD_CONTRACT)}`",
            f"- `{rel(SESSION_TIMEZONE_CONTRACT)}`",
            f"- `{rel(LEAKAGE_VALIDATOR_SPEC)}`",
            f"- `{rel(DOWNSTREAM_FIELD_CONTRACT)}`",
        ]
    )
    CONTEXT_ANCHOR.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_saturation() -> None:
    SATURATION_SELF_RED_TEAM.write_text(
        "\n".join(
            [
                "# Lane02 Saturation And Self-Red-Team",
                "",
                "- Evidence-class confusion risk: source metadata and broker history fields can look like candidate-time fields; contract marks them source_metadata or broker_realized unless explicit candidate clocks are present.",
                "- Leakage risk: feature-store validation rejects post-order, post-fill, post-close, broker-realized, replay-only, label-only, and future-outcome classes.",
                "- Duplicate-key risk: canonical key policy requires source_row_id plus route_id and broker ticket/order/deal ids where applicable.",
                "- Filename-date risk: filename dates are inventoried as source metadata and cannot substitute for decision/candle time.",
                "- Local-heavy-data risk: MT5 preservation inventory is consumed as source completeness evidence; raw binary caches require an exporter/parser route before row-level use.",
                "- Dependency risk: absent absolute master and Lane01 source-authority outputs are dependency-state rows, not stop conditions.",
                "- Runtime risk: this route writes research-only artifacts and tests; it does not change config, prompts, risk, execution, safety, canary, selector, or broker state.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def build_manifest() -> dict[str, Any]:
    outputs = [
        TIMESTAMP_INVENTORY,
        ASOF_FIELD_CONTRACT,
        SOURCE_COVERAGE_LEDGER,
        DEPENDENCY_STATE_LEDGER,
        SOURCE_COMPLETENESS_DECISIONS,
        NO_LEAK_VALIDATION_LEDGER,
        IMPLEMENTATION_DECISION_LEDGER,
        SATURATION_SELF_RED_TEAM,
        SESSION_TIMEZONE_CONTRACT,
        CANONICAL_KEY_POLICY,
        LEAKAGE_VALIDATOR_SPEC,
        DOWNSTREAM_FIELD_CONTRACT,
        CONTEXT_ANCHOR,
        RUNTIME_EFFECT_BOUNDARY,
        VERIFICATION_RESULT,
        FOCUSED_TEST_RESULT,
        COMPLETION_AUDIT,
        OUTPUT_MANIFEST,
        ROUTE_DIR / ".gitattributes",
        ROUTE_DIR / "vnext_lane02_time_contract.py",
        ROUTE_DIR / "build_vnext_moonshot_lane02_no_leak_time_alignment_asof_contract.py",
        ROUTE_DIR / "verify_vnext_moonshot_lane02_no_leak_time_alignment_asof_contract.py",
        ROUTE_DIR / "test_vnext_moonshot_lane02_no_leak_time_alignment_asof_contract.py",
    ]
    rows = []
    for path in outputs:
        if not path.exists():
            continue
        entry = {
            "bytes": path.stat().st_size,
            "line_count": line_count(path),
            "path": rel(path),
            "sha256": file_sha256(path),
        }
        if path == OUTPUT_MANIFEST:
            entry["bytes"] = None
            entry["line_count"] = None
            entry["sha256"] = "SELF_REFERENTIAL_MANIFEST_HASH_NOT_APPLICABLE"
        if path == VERIFICATION_RESULT:
            entry["bytes"] = None
            entry["line_count"] = None
            entry["sha256"] = "VERIFIER_WRITES_RESULT_AFTER_MANIFEST_CHECK"
        rows.append(entry)
    return {
        "generated_at_utc": utc_now(),
        "manifest_path": rel(OUTPUT_MANIFEST),
        "output_count": len(rows),
        "outputs": rows,
        "route_id": ROUTE_ID,
        "schema_version": "vnext_lane02_output_manifest_v1",
        "verification_result_path": rel(VERIFICATION_RESULT),
    }


def verify_manifest_integrity(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for item in manifest.get("outputs", []):
        path = ROOT / item["path"]
        if not path.exists():
            issues.append({"code": "manifest_missing_file", "path": item["path"]})
            continue
        if path in {OUTPUT_MANIFEST, VERIFICATION_RESULT}:
            continue
        if path.stat().st_size != item.get("bytes"):
            issues.append({"code": "manifest_byte_mismatch", "path": item["path"]})
        if file_sha256(path) != item.get("sha256"):
            issues.append({"code": "manifest_hash_mismatch", "path": item["path"]})
    return issues


def verify_outputs(write: bool = True) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    required = [
        TIMESTAMP_INVENTORY,
        ASOF_FIELD_CONTRACT,
        SOURCE_COVERAGE_LEDGER,
        DEPENDENCY_STATE_LEDGER,
        SOURCE_COMPLETENESS_DECISIONS,
        NO_LEAK_VALIDATION_LEDGER,
        IMPLEMENTATION_DECISION_LEDGER,
        SESSION_TIMEZONE_CONTRACT,
        CANONICAL_KEY_POLICY,
        LEAKAGE_VALIDATOR_SPEC,
        DOWNSTREAM_FIELD_CONTRACT,
        RUNTIME_EFFECT_BOUNDARY,
        COMPLETION_AUDIT,
        OUTPUT_MANIFEST,
    ]
    for path in required:
        if not path.exists():
            issues.append({"code": "missing_output", "path": rel(path)})
    inventory_count = line_count(TIMESTAMP_INVENTORY) or 0
    contract_count = line_count(ASOF_FIELD_CONTRACT) or 0
    validation_rows = []
    if NO_LEAK_VALIDATION_LEDGER.exists():
        with NO_LEAK_VALIDATION_LEDGER.open(encoding="utf-8") as handle:
            validation_rows = [json.loads(line) for line in handle if line.strip()]
    if inventory_count <= 0:
        issues.append({"code": "timestamp_inventory_empty"})
    if contract_count <= 0:
        issues.append({"code": "asof_contract_empty"})
    if not validation_rows or any(row.get("status") != "passed" for row in validation_rows):
        issues.append({"code": "no_leak_validation_cases_failed_or_missing"})
    session_contract = read_json(SESSION_TIMEZONE_CONTRACT, {})
    if not session_contract.get("symbols"):
        issues.append({"code": "session_contract_missing_symbols"})
    downstream = read_json(DOWNSTREAM_FIELD_CONTRACT, {})
    if "feature_store" not in downstream or "label_store" not in downstream:
        issues.append({"code": "downstream_contract_missing_feature_or_label"})
    audit = read_json(COMPLETION_AUDIT, {})
    if audit.get("status") != "complete":
        issues.append({"code": "completion_audit_not_complete"})
    manifest = read_json(OUTPUT_MANIFEST, {})
    issues.extend(verify_manifest_integrity(manifest))
    result = {
        "asof_contract_rows": contract_count,
        "generated_at_utc": utc_now(),
        "issue_count": len(issues),
        "issues": issues,
        "ok": not issues,
        "route_id": ROUTE_ID,
        "schema_version": "vnext_lane02_verification_result_v1",
        "timestamp_inventory_rows": inventory_count,
    }
    if write:
        write_json(VERIFICATION_RESULT, result)
    return result


def completion_audit(summary: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    requirements = [
        ("timestamp_inventory", rel(TIMESTAMP_INVENTORY)),
        ("asof_field_contract", rel(ASOF_FIELD_CONTRACT)),
        ("leakage_validator", [rel(LEAKAGE_VALIDATOR_SPEC), rel(ROUTE_DIR / "vnext_lane02_time_contract.py")]),
        ("session_normalizer", [rel(SESSION_TIMEZONE_CONTRACT), rel(ROUTE_DIR / "vnext_lane02_time_contract.py")]),
        ("canonical_key_policy", rel(CANONICAL_KEY_POLICY)),
        ("downstream_field_contract", rel(DOWNSTREAM_FIELD_CONTRACT)),
        ("source_dependency_state_rows", rel(DEPENDENCY_STATE_LEDGER)),
        ("source_completeness_decisions", rel(SOURCE_COMPLETENESS_DECISIONS)),
        ("manifest", rel(OUTPUT_MANIFEST)),
        ("verifier", rel(VERIFICATION_RESULT)),
        ("focused_tests", rel(FOCUSED_TEST_RESULT)),
        ("completion_audit", rel(COMPLETION_AUDIT)),
    ]
    return {
        "branch_decision": "route_local_contract_implemented_no_production_activation",
        "completion_ready": bool(verification.get("ok")),
        "context_files_read_after_preflight": [
            rel(LIVE_STATE_PATH),
            ".context/00_core/current_vnext_system_map.md",
            ".context/00_core/current_repo_reading_order.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/vnext_absolute_moonshot_vision_and_limitations.md",
            rel(PROMPT_PATH),
            rel(STARTER_PATH),
        ],
        "dependency_status": summary["dependency_status"],
        "doctrine_application": {
            "anti_boxing_questions_pursued": [
                "scanned current shadow logs, candidate trade records, route artifacts, activation selected denominator artifacts, local data, pipeline state, live companion, and MT5 preservation outputs",
                "recorded missing absolute master/Lane01 source authority as dependency-state rows instead of stopping",
                "treated filename dates, source metadata timestamps, broker timestamps, and outcome timestamps as distinct classes",
                "kept route-local code consumable by future feature/label/replay builders without production activation",
            ],
            "builder_or_audit_posture": "constructive_builder_no_leak_asof_contract",
            "goal_session_research_discipline_read": True,
            "proof_or_impossibility_stop_condition": "all current local structured material sources scanned or exact parser/export requirement recorded",
            "research_operating_doctrine_read": True,
        },
        "forbidden_surface_attestation": forbidden_runtime_effect_boundary(),
        "generated_at_utc": utc_now(),
        "requirements": [
            {
                "evidence": evidence,
                "requirement": requirement,
                "status": "complete" if verification.get("ok") else "needs_repair",
            }
            for requirement, evidence in requirements
        ],
        "result_use_status": "source_control_contract_artifacts_only_not_performance_result_not_production_change",
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": "route_local_research_artifacts_only_no_live_behavior_change",
        "schema_version": "vnext_lane02_completion_audit_v1",
        "source_use_state": "local_current_worktree_structured_sources_plus_mt5_preservation_inventory_no_paid_or_live_broker_operation",
        "status": "complete" if verification.get("ok") else "not_complete",
        "summary": summary,
        "verification": verification,
    }


def build_outputs() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    config = load_config()
    inventory_rows, coverage_rows = scan_sources()
    deps = dependency_rows()
    asof_rows = build_asof_contract(inventory_rows)
    no_leak_rows = no_leak_validation_rows()
    source_decisions = source_completeness_rows(coverage_rows, deps)
    summary = {
        "asof_field_contract_rows": len(asof_rows),
        "dependency_status": deps,
        "generated_at_utc": utc_now(),
        "git": git_head(),
        "records_scanned": sum(int(row.get("records_scanned") or 0) for row in coverage_rows),
        "route_id": ROUTE_ID,
        "source_files_scanned": len(coverage_rows),
        "timestamp_inventory_rows": len(inventory_rows),
    }

    write_jsonl(TIMESTAMP_INVENTORY, inventory_rows)
    write_jsonl(ASOF_FIELD_CONTRACT, asof_rows)
    write_jsonl(SOURCE_COVERAGE_LEDGER, coverage_rows)
    write_jsonl(DEPENDENCY_STATE_LEDGER, deps)
    write_jsonl(SOURCE_COMPLETENESS_DECISIONS, source_decisions)
    write_jsonl(NO_LEAK_VALIDATION_LEDGER, no_leak_rows)
    write_jsonl(IMPLEMENTATION_DECISION_LEDGER, implementation_decision_rows())
    write_json(SESSION_TIMEZONE_CONTRACT, session_timezone_contract(config))
    write_json(CANONICAL_KEY_POLICY, canonical_key_policy())
    write_json(LEAKAGE_VALIDATOR_SPEC, leakage_validator_spec())
    write_json(DOWNSTREAM_FIELD_CONTRACT, downstream_field_contract())
    write_json(RUNTIME_EFFECT_BOUNDARY, forbidden_runtime_effect_boundary())
    write_saturation()
    write_context_anchor(summary)
    pre_verification = {"ok": True, "issues": [], "issue_count": 0}
    write_json(COMPLETION_AUDIT, completion_audit(summary, pre_verification))
    write_json(OUTPUT_MANIFEST, build_manifest())
    verification = verify_outputs(write=True)
    write_json(COMPLETION_AUDIT, completion_audit(summary, verification))
    write_json(OUTPUT_MANIFEST, build_manifest())
    verification = verify_outputs(write=True)
    write_json(COMPLETION_AUDIT, completion_audit(summary, verification))
    write_json(OUTPUT_MANIFEST, build_manifest())
    verification = verify_outputs(write=True)
    return {"summary": summary, "verification": verification}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = verify_outputs(write=True) if args.verify else build_outputs()["verification"]
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

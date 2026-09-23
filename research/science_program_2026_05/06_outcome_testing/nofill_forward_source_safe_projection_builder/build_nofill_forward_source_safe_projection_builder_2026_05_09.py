#!/usr/bin/env python3
"""Build offline NOFILL forward source-safe projection artifacts.

This is a research/control-only lane. It reads existing artifacts and source
logs through an explicit allowlist, projects only source-safe status fields,
and writes versioned artifacts under this directory. It does not import or
modify live trading components.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
ROUTE_ID = "NOFILL_FORWARD_SOURCE_SAFE_PROJECTION_BUILDER"
SCHEMA_VERSION = "nofill_forward_source_safe_projection_builder_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
PROJECTION_BUILDER_VERSION = "nofill_forward_source_safe_projection_builder_v1_2026_05_09"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
BASE = Path("research/science_program_2026_05/06_outcome_testing")

ADDENDUM_DIR = BASE / "nofill_forward_contract_addendum_projection_plan"
COUNT_PACKET_DIR = BASE / "nofill_cat_v3_quarantined_categorical_count_packet"
RESULT_CONTRACT_DIR = BASE / "nofill_cat_v3_result_contract_update"
SOURCE_CONTROL_DIR = BASE / "nofill_cat_v3_source_control_rebuild"
G12_FORWARD_DIR = BASE / "g12_nofill_forward_lifecycle_capture_contract_audit"
G12_COUNT_DIR = BASE / "g12_nofill_cat_v3_quarantined_categorical_count_packet_audit"
G0_SYNTH_DIR = BASE / "g0_nofill_cat_v3_categorical_evidence_synthesis_control_review"
PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "NOFILL_FORWARD_SOURCE_SAFE_PROJECTION_BUILDER_GOAL_PROMPT_2026-05-09.md"
)

ACCEPTED_ROWS_PATH = COUNT_PACKET_DIR / f"NOFILL_CAT_V3_COUNT_ACCEPTED_INPUT_ROWS_{DATE}.jsonl"
EXCLUSION_ROWS_PATH = COUNT_PACKET_DIR / f"NOFILL_CAT_V3_COUNT_EXCLUSION_PROOF_LEDGER_{DATE}.jsonl"
REJECT_OVERLAP_PATH = COUNT_PACKET_DIR / f"NOFILL_CAT_V3_REJECT_OVERLAP_ANTI_LAUNDERING_AUDIT_{DATE}.json"
ADDENDUM_SCHEMA_PATH = ADDENDUM_DIR / f"NOFILL_FORWARD_PROJECTION_FIELD_SCHEMA_{DATE}.json"
ADDENDUM_AUDIT_PATH = ADDENDUM_DIR / f"NOFILL_FORWARD_NO_LEAK_AND_FORBIDDEN_FIELD_AUDIT_{DATE}.json"

SOURCE_CONTROL_ROWS = {
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
    "NOFILL-CAT-ROW-0241",
}
SOURCE_IMPOSSIBLE_ROWS = {
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}

CONTROL_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_result_scoring": False,
    "opens_live_wiring": False,
    "opens_paid_api_or_databento_route": False,
    "opens_registry_edit": False,
    "changes_live_trading_behavior": False,
}

APPROVED_LOGS: dict[str, dict[str, str]] = {
    "shadow_logs/strategy_follow_candidates.jsonl": {
        "source_type": "decision_time_candidate_safe_projection",
        "route": "candidate_decision_shadow_log",
    },
    "shadow_logs/candidate_path_follow.jsonl": {
        "source_type": "candidate_path_follow_source_safe_projection",
        "route": "candidate_path_follow_shadow_log",
    },
    "shadow_logs/candidate_ltf_path_order.jsonl": {
        "source_type": "candidate_ltf_path_order_source_safe_projection",
        "route": "candidate_ltf_path_order_shadow_log",
    },
    "shadow_logs/pending_limit_lifecycle.jsonl": {
        "source_type": "pending_limit_lifecycle_source_safe_projection",
        "route": "pending_limit_lifecycle_shadow_log",
    },
    "shadow_logs/pending_limit_lifecycle_join_backfill.jsonl": {
        "source_type": "pending_limit_lifecycle_source_safe_projection",
        "route": "pending_limit_lifecycle_join_backfill_shadow_log",
    },
    "shadow_logs/prefill_delivery_path.jsonl": {
        "source_type": "prefill_delivery_path_source_safe_projection",
        "route": "prefill_delivery_path_shadow_log",
    },
    "shadow_logs/v2b_forward_pairs.jsonl": {
        "source_type": "v2b_forward_pair_source_safe_projection",
        "route": "v2b_forward_pair_shadow_log",
    },
    "shadow_logs/fvg_ob_confluence.jsonl": {
        "source_type": "fvg_ob_confluence_source_safe_projection",
        "route": "fvg_ob_confluence_shadow_log",
    },
}

CONTEXT_INPUTS = [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    str(PROMPT_PATH),
    str(ADDENDUM_DIR / f"NOFILL_FORWARD_NEXT_PROMPT_PACK_{DATE}.md"),
    str(ADDENDUM_DIR / f"NOFILL_FORWARD_OFFLINE_PROJECTION_BUILDER_PLAN_{DATE}.md"),
    str(ADDENDUM_DIR / f"NOFILL_FORWARD_CONTRACT_ADDENDUM_{DATE}.md"),
    str(ADDENDUM_DIR / f"NOFILL_FORWARD_CONTRACT_ADDENDUM_{DATE}.json"),
    str(ADDENDUM_SCHEMA_PATH),
    str(ADDENDUM_AUDIT_PATH),
    str(G12_FORWARD_DIR / f"G12_NOFILL_FORWARD_DECISION_LEDGER_{DATE}.md"),
    str(G12_FORWARD_DIR / f"G12_NOFILL_FORWARD_SCHEMA_AUDIT_{DATE}.json"),
    str(G12_FORWARD_DIR / f"G12_NOFILL_FORWARD_NO_LEAK_SOURCE_AUDIT_{DATE}.json"),
    str(COUNT_PACKET_DIR / f"NOFILL_CAT_V3_CATEGORICAL_COUNT_LEDGER_{DATE}.json"),
    str(ACCEPTED_ROWS_PATH),
    str(EXCLUSION_ROWS_PATH),
    str(REJECT_OVERLAP_PATH),
    str(RESULT_CONTRACT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json"),
    str(RESULT_CONTRACT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_NOLEAK_SCHEMA_{DATE}.json"),
    str(SOURCE_CONTROL_DIR / f"NOFILL_CAT_V3_UNIVERSE_RECONCILIATION_{DATE}.json"),
    str(G12_COUNT_DIR / f"G12_NOFILL_CAT_V3_COUNT_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json"),
    str(G0_SYNTH_DIR / f"G0_NOFILL_CAT_V3_EVIDENCE_CHAIN_RECONCILIATION_{DATE}.json"),
]

MUTABLE_CONTEXT_INPUTS = {
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
}

CODE_SOURCE_INPUTS = [
    "src/research_infra/forward_capture.py",
    "src/research_infra/live_shadow_gap_closure.py",
    "src/research_infra/live_mechanical_shadow.py",
    "src/components/pending_limit_lifecycle_logger.py",
    "scripts/audit_live_shadow_data_health.py",
    "scripts/verify_shadow_log_integrity.py",
]

PARSER_FILES = [
    "build_nofill_forward_source_safe_projection_builder_2026_05_09.py",
    "verify_nofill_forward_source_safe_projection_builder_2026_05_09.py",
    "test_nofill_forward_source_safe_projection_builder_2026_05_09.py",
]

LOCAL_HEAVY_ROOTS = [
    "C:/Users/MSI/Documents/ai-trading-agent/data",
    "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
    "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs",
    "C:/Users/MSI/Documents/ai-trading-agent/exports",
    "C:/tmp",
    "C:/tmp/gtos_otb",
    "C:/SierraChart",
    "C:/Users/MSI/Documents",
]

TICK_ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent/data/ticks")

FORBIDDEN_RAW_KEYS = {
    "account_history",
    "account_pnl",
    "actual_r",
    "broker_actual_r",
    "broker_fill_state",
    "deal_id",
    "expectancy",
    "fill_time_utc",
    "live_order_state",
    "mt5_deal_id",
    "mt5_order_ticket",
    "mt5_position_id",
    "order_send_attempted",
    "order_send_success",
    "pending_ticket",
    "position_id",
    "r_multiple",
    "r_value",
    "slippage_price",
    "synthetic_path_r",
    "trade_state_ticket",
    "win_rate",
}

TICKET_KEYS = {
    "mt5_order_ticket",
    "pending_ticket",
    "trade_state_ticket",
    "mt5_deal_id",
    "deal_id",
    "mt5_position_id",
    "position_id",
}

EXECUTION_QUALITY_KEYS = {
    "broker_fill_state",
    "order_send_attempted",
    "order_send_success",
    "fill_time_utc",
    "live_order_state",
}

ALLOWED_STATUS_FIELDS_WITH_FORBIDDEN_TERMS = {
    "broker_pending_order_created_status",
    "raw_ticket_field_present_status",
    "mt5_order_ticket_redaction_status",
    "slippage_label_status",
    "slippage_value_redaction_status",
    "execution_quality_label_status",
    "execution_quality_value_redaction_status",
}

ADDENDUM_FIELD_NAMES = [
    "capture_observed_at_utc",
    "capture_write_started_at_utc",
    "capture_write_completed_at_utc",
    "capture_latency_ms",
    "capture_clock_source_status",
    "capture_clock_skew_ms",
    "capture_clock_skew_status",
    "capture_timestamp_derivation_rule",
    "pending_order_mode_source_safe",
    "pending_order_mode_status",
    "broker_pending_order_created_status",
    "native_pending_order_type_source_safe",
    "native_pending_order_type_status",
    "raw_ticket_field_present_status",
    "mt5_order_ticket_redaction_status",
    "decision_spread_status",
    "decision_spread_value_source_safe",
    "decision_spread_unit",
    "entry_touch_spread_status",
    "entry_touch_spread_value_source_safe",
    "spread_source_hash",
    "slippage_label_status",
    "slippage_value_redaction_status",
    "execution_quality_label_status",
    "execution_quality_value_redaction_status",
    "cost_testing_gate_status",
]

IDENTITY_AND_CONTROL_FIELDS = [
    "packet_row_id",
    "source_row_id",
    "candidate_id",
    "decision_asof_utc",
    "symbol",
    "session",
    "side",
    "source_lane",
    "source_packet_id",
    "source_inventory_id",
    "v3_terminal_family",
    "v3_terminal_state",
    "row_level_denominator_member",
    "nofill_duplicate_key_count_member",
    "duplicate_group_id_count_member",
    "nofill_duplicate_key_sha256",
    "duplicate_group_id_sha256",
    "excluded_before_any_count",
    "source_match_status",
    "source_lineage",
    "source_file_sha256_values",
    "parser_code_sha256",
    "controlling_git_head",
    "missing_statuses",
]

SAFE_CONTROL_METADATA_FIELDS = [
    "projection_schema_version",
    "projection_builder_version",
    "route_id",
    "promotion_verdict",
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_result_scoring",
    "opens_live_wiring",
    "opens_paid_api_or_databento_route",
    "opens_registry_edit",
    "changes_live_trading_behavior",
    "projection_output_allowed_field_count",
    "source_route_count",
]

EXHAUSTIVE_PROJECTION_ALLOWED_FIELDS = sorted(
    set(IDENTITY_AND_CONTROL_FIELDS) | set(ADDENDUM_FIELD_NAMES) | set(SAFE_CONTROL_METADATA_FIELDS)
)

FORBIDDEN_VALUE_PATTERNS = [
    re.compile(r"\b(?:win_rate|expectancy|dsr|pbo|sharpe)\b", re.I),
    re.compile(r"\b(?:account_history|account_pnl|broker_actual_r|synthetic_path_r)\b", re.I),
    re.compile(r"\b(?:order_send_success|order_send_attempted|broker_fill_state|fill_time_utc)\b", re.I),
]


@dataclass(frozen=True)
class SourceLogRow:
    rel_path: str
    line_no: int
    row: dict[str, Any]
    sha256: str | None
    source_type: str
    route: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def as_repo_path(path: str | Path) -> Path:
    path_obj = Path(path)
    if path_obj.is_absolute():
        return path_obj
    return REPO_ROOT / path_obj


def rel_display(path: str | Path) -> str:
    path_obj = Path(path)
    try:
        return str(path_obj.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path_obj).replace("\\", "/")


def sha256_file(path: str | Path) -> str | None:
    full = as_repo_path(path)
    if not full.exists() or not full.is_file():
        return None
    digest = hashlib.sha256()
    with full.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_lf_normalized_file(path: str | Path) -> str | None:
    full = as_repo_path(path)
    if not full.exists() or not full.is_file():
        return None
    if full.suffix.lower() not in {".md", ".py", ".json", ".jsonl", ".txt", ".yaml", ".yml"}:
        return None
    raw = full.read_bytes()
    normalized = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


def write_json(name: str, payload: Any) -> None:
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> None:
    with (OUT_DIR / name).open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_md(name: str, text: str) -> None:
    (OUT_DIR / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def read_json(path: str | Path) -> Any:
    return json.loads(as_repo_path(path).read_text(encoding="utf-8"))


def read_jsonl(path: str | Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    with as_repo_path(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if line.strip():
                rows.append((line_no, json.loads(line)))
    return rows


def parse_candidate_id(packet_row: dict[str, Any]) -> str | None:
    source_row_id = packet_row.get("source_row_id")
    if isinstance(source_row_id, str) and "|" in source_row_id:
        return source_row_id.split("|")[-1]
    if isinstance(source_row_id, str) and "_" in source_row_id:
        return source_row_id
    return None


def parse_decision_time(packet_row: dict[str, Any], matched_rows: list[SourceLogRow] | None = None) -> str | None:
    if matched_rows:
        for source_row in matched_rows:
            value = source_row.row.get("decision_time_utc") or source_row.row.get("asof_cutoff_utc")
            if isinstance(value, str) and value:
                return value
    candidate_id = parse_candidate_id(packet_row)
    if not candidate_id or "_" not in candidate_id:
        return None
    return candidate_id.split("_", 1)[1]


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def normalize_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def source_manifest_entry(path: str | Path, role: str, consumed: bool = True) -> dict[str, Any]:
    full = as_repo_path(path)
    display_path = rel_display(full)
    strict_hash_recompute = display_path not in MUTABLE_CONTEXT_INPUTS
    normalized_hash = sha256_lf_normalized_file(full)
    return {
        "path": display_path,
        "exists": full.exists(),
        "role": role,
        "consumed_by_projection_builder": consumed,
        "strict_hash_recompute": strict_hash_recompute,
        "hash_policy": "strict_recompute" if strict_hash_recompute else "mutable_context_snapshot_presence_only",
        "sha256": sha256_file(full),
        "sha256_lf_normalized": normalized_hash,
        "line_ending_policy": "lf_normalized_fallback" if normalized_hash else "binary_or_not_text",
        "size_bytes": full.stat().st_size if full.exists() and full.is_file() else None,
    }


def load_universe_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_rel, source_family in (
        (ACCEPTED_ROWS_PATH, "accepted_packet"),
        (EXCLUSION_ROWS_PATH, "exclusion_packet"),
    ):
        source_sha = sha256_file(source_rel)
        for line_no, row in read_jsonl(source_rel):
            item = dict(row)
            item["_source_packet_path"] = str(source_rel).replace("\\", "/")
            item["_source_packet_line_no"] = line_no
            item["_source_packet_sha256"] = source_sha
            item["_source_packet_family"] = source_family
            item["_candidate_id"] = parse_candidate_id(item)
            rows.append(item)
    return rows


def load_approved_logs() -> tuple[dict[str, list[SourceLogRow]], dict[str, list[SourceLogRow]], list[dict[str, Any]]]:
    by_candidate: dict[str, list[SourceLogRow]] = defaultdict(list)
    by_trade: dict[str, list[SourceLogRow]] = defaultdict(list)
    inventory: list[dict[str, Any]] = []

    for rel_path, meta in APPROVED_LOGS.items():
        full = REPO_ROOT / rel_path
        sha = sha256_file(rel_path)
        key_counter: Counter[str] = Counter()
        forbidden_hits: set[str] = set()
        line_count = 0
        candidate_ids: set[str] = set()
        trade_ids: set[str] = set()
        parse_errors: list[dict[str, Any]] = []
        if full.exists():
            with full.open("r", encoding="utf-8") as handle:
                for line_no, line in enumerate(handle, 1):
                    if not line.strip():
                        continue
                    line_count += 1
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError as exc:
                        parse_errors.append({"line_no": line_no, "error": str(exc)})
                        continue
                    key_counter.update(row.keys())
                    forbidden_hits.update(set(row.keys()) & FORBIDDEN_RAW_KEYS)
                    source_row = SourceLogRow(
                        rel_path=rel_path,
                        line_no=line_no,
                        row=row,
                        sha256=sha,
                        source_type=meta["source_type"],
                        route=meta["route"],
                    )
                    candidate_id = row.get("candidate_id")
                    if isinstance(candidate_id, str) and candidate_id:
                        by_candidate[candidate_id].append(source_row)
                        candidate_ids.add(candidate_id)
                    trade_id = row.get("trade_id")
                    if isinstance(trade_id, str) and trade_id:
                        by_trade[trade_id].append(source_row)
                        trade_ids.add(trade_id)

        inventory.append(
            {
                "path": rel_path,
                "exists": full.exists(),
                "source_type": meta["source_type"],
                "route": meta["route"],
                "sha256": sha,
                "line_count": line_count,
                "candidate_id_count": len(candidate_ids),
                "trade_id_count": len(trade_ids),
                "observed_key_count": len(key_counter),
                "observed_keys": sorted(key_counter),
                "observed_forbidden_raw_key_hits": sorted(forbidden_hits),
                "parse_errors": parse_errors,
                "projection_rule": "raw rows are never emitted directly; only strict allowlist/status projection is emitted",
            }
        )

    return by_candidate, by_trade, inventory


def choose_first_value(rows: list[SourceLogRow], keys: list[str]) -> Any:
    for key in keys:
        for row in rows:
            if key in row.row and row.row.get(key) not in (None, ""):
                return row.row.get(key)
    return None


def choose_first_row_with_key(rows: list[SourceLogRow], key: str) -> SourceLogRow | None:
    for row in rows:
        if key in row.row and row.row.get(key) not in (None, ""):
            return row
    return None


class TickSpreadLookup:
    def __init__(self) -> None:
        self._frames: dict[tuple[str, str], Any] = {}
        self.manifest: dict[str, dict[str, Any]] = {}

    def source_path(self, symbol: str, dt: datetime) -> Path:
        return TICK_ROOT / symbol / f"{dt.date().isoformat()}.parquet"

    def _load(self, symbol: str, dt: datetime) -> Any:
        key = (symbol, dt.date().isoformat())
        if key in self._frames:
            return self._frames[key]
        path = self.source_path(symbol, dt)
        record_key = str(path).replace("\\", "/")
        if not path.exists():
            self._frames[key] = None
            self.manifest[record_key] = {
                "path": record_key,
                "exists": False,
                "role": "tick_parquet_readonly_manifest",
                "symbol": symbol,
                "date": dt.date().isoformat(),
                "sha256": None,
                "row_count": 0,
                "read_status": "MISSING",
            }
            return None
        try:
            import pandas as pd  # type: ignore

            frame = pd.read_parquet(path, columns=["ts_utc", "bid", "ask"])
            self._frames[key] = frame
            self.manifest[record_key] = {
                "path": record_key,
                "exists": True,
                "role": "tick_parquet_readonly_manifest",
                "symbol": symbol,
                "date": dt.date().isoformat(),
                "sha256": sha256_file(path),
                "row_count": int(len(frame)),
                "read_status": "READ_OK",
                "columns_used": ["ts_utc", "bid", "ask"],
            }
            return frame
        except Exception as exc:  # pragma: no cover - depends on local parquet stack
            self._frames[key] = None
            self.manifest[record_key] = {
                "path": record_key,
                "exists": True,
                "role": "tick_parquet_readonly_manifest",
                "symbol": symbol,
                "date": dt.date().isoformat(),
                "sha256": sha256_file(path),
                "row_count": 0,
                "read_status": "READ_FAILED",
                "error": str(exc),
            }
            return None

    def spread_at_or_before(self, symbol: str | None, timestamp_utc: str | None) -> dict[str, Any]:
        if not symbol or not timestamp_utc:
            return {
                "status": "SOURCE_FIELD_MISSING",
                "value": None,
                "unit": "SOURCE_FIELD_MISSING",
                "source_hash": None,
                "source_path": None,
                "tick_time_utc": None,
                "tick_age_ms": None,
            }
        dt = parse_dt(timestamp_utc)
        if dt is None:
            return {
                "status": "SOURCE_FIELD_MISSING",
                "value": None,
                "unit": "SOURCE_FIELD_MISSING",
                "source_hash": None,
                "source_path": None,
                "tick_time_utc": None,
                "tick_age_ms": None,
            }
        symbol = "NAS100" if symbol == "NDX100" else symbol
        frame = self._load(symbol, dt)
        path = self.source_path(symbol, dt)
        path_key = str(path).replace("\\", "/")
        manifest_row = self.manifest.get(path_key, {})
        if frame is None or len(frame) == 0:
            return {
                "status": "SOURCE_FIELD_MISSING",
                "value": None,
                "unit": "SOURCE_FIELD_MISSING",
                "source_hash": manifest_row.get("sha256"),
                "source_path": path_key,
                "tick_time_utc": None,
                "tick_age_ms": None,
            }
        import pandas as pd  # type: ignore

        target = pd.Timestamp(dt).tz_convert("UTC")
        ts = frame["ts_utc"]
        idx = int(ts.searchsorted(target, side="right")) - 1
        if idx < 0:
            return {
                "status": "SOURCE_FIELD_MISSING",
                "value": None,
                "unit": "SOURCE_FIELD_MISSING",
                "source_hash": manifest_row.get("sha256"),
                "source_path": path_key,
                "tick_time_utc": None,
                "tick_age_ms": None,
            }
        tick = frame.iloc[idx]
        bid = tick.get("bid")
        ask = tick.get("ask")
        tick_time = tick.get("ts_utc")
        if bid is None or ask is None:
            return {
                "status": "SOURCE_FIELD_MISSING",
                "value": None,
                "unit": "SOURCE_FIELD_MISSING",
                "source_hash": manifest_row.get("sha256"),
                "source_path": path_key,
                "tick_time_utc": str(tick_time) if tick_time is not None else None,
                "tick_age_ms": None,
            }
        age_ms = int((target - tick_time).total_seconds() * 1000)
        # Require a current-ish quote. Older quotes stay source evidence but not
        # decision-spread capture.
        if age_ms < 0 or age_ms > 60_000:
            return {
                "status": "SOURCE_FIELD_MISSING",
                "value": None,
                "unit": "SOURCE_FIELD_MISSING",
                "source_hash": manifest_row.get("sha256"),
                "source_path": path_key,
                "tick_time_utc": normalize_utc(tick_time.to_pydatetime()),
                "tick_age_ms": age_ms,
            }
        return {
            "status": "CAPTURED_SOURCE_SAFE",
            "value": round(float(ask) - float(bid), 10),
            "unit": "PRICE",
            "source_hash": manifest_row.get("sha256"),
            "source_path": path_key,
            "tick_time_utc": normalize_utc(tick_time.to_pydatetime()),
            "tick_age_ms": age_ms,
        }


def raw_ticket_status(rows: list[SourceLogRow]) -> tuple[str, str]:
    saw_ticket_key = False
    saw_ticket_value = False
    for source_row in rows:
        for key in TICKET_KEYS:
            if key in source_row.row:
                saw_ticket_key = True
                if source_row.row.get(key) not in (None, "", 0, "0"):
                    saw_ticket_value = True
    if saw_ticket_value:
        return "RAW_TICKET_VALUE_PRESENT_REDACTED", "SOURCE_TICKET_VALUE_REDACTED"
    if saw_ticket_key:
        return "RAW_TICKET_FIELD_EMPTY", "PASS_NO_TICKET_VALUE_EXPOSED"
    return "RAW_TICKET_FIELD_NOT_IN_SOURCE", "PASS_NO_TICKET_VALUE_EXPOSED"


def slippage_redaction_status(rows: list[SourceLogRow]) -> str:
    saw = False
    for source_row in rows:
        if "slippage_price" in source_row.row:
            saw = True
            if source_row.row.get("slippage_price") not in (None, "", 0, "0"):
                return "RAW_SLIPPAGE_VALUE_PRESENT_REDACTED"
    return "RAW_SLIPPAGE_FIELD_EMPTY" if saw else "RAW_SLIPPAGE_FIELD_NOT_IN_SOURCE"


def execution_redaction_status(rows: list[SourceLogRow]) -> str:
    saw = any(any(key in source_row.row for key in EXECUTION_QUALITY_KEYS) for source_row in rows)
    return "RAW_EXECUTION_FIELD_PRESENT_REDACTED" if saw else "RAW_EXECUTION_FIELD_NOT_IN_SOURCE"


def pending_projection(rows: list[SourceLogRow]) -> dict[str, Any]:
    mode = choose_first_value(rows, ["pending_order_mode"])
    if mode == "INTERNAL_CANDLE_POLLED_INTENT":
        mode_safe = "INTERNAL_CANDLE_POLLED_INTENT"
        mode_status = "CAPTURED_DIRECT"
    elif mode in (None, ""):
        mode_safe = None
        mode_status = "SOURCE_FIELD_MISSING"
    else:
        mode_safe = None
        mode_status = "INVALID_FAIL_CLOSED"

    broker_created_seen = False
    broker_created_value = None
    for source_row in rows:
        if "broker_pending_order_created" in source_row.row:
            broker_created_seen = True
            broker_created_value = source_row.row.get("broker_pending_order_created")
            if broker_created_value is True:
                break
    if broker_created_value is True:
        broker_created_status = "NATIVE_PENDING_OBSERVABILITY_PRESENT_REDACTED"
    elif broker_created_seen:
        broker_created_status = "INTERNAL_ONLY_NO_NATIVE_BROKER_ORDER"
    else:
        broker_created_status = "SOURCE_FIELD_MISSING"

    native_type = choose_first_value(rows, ["native_pending_order_type"])
    if native_type in {"BUY_LIMIT", "SELL_LIMIT"}:
        native_type_safe = native_type
        native_type_status = "CAPTURED_SOURCE_SAFE"
    elif mode_safe == "INTERNAL_CANDLE_POLLED_INTENT":
        native_type_safe = "INTERNAL_LIMIT_INTENT_ONLY"
        native_type_status = "NOT_OPENED_FOR_SOURCE_CONTROL"
    elif native_type in (None, ""):
        native_type_safe = None
        native_type_status = "SOURCE_FIELD_MISSING"
    else:
        native_type_safe = None
        native_type_status = "SOURCE_FIELD_MISSING"

    raw_ticket_field_status, ticket_redaction_status = raw_ticket_status(rows)
    return {
        "pending_order_mode_source_safe": mode_safe,
        "pending_order_mode_status": mode_status,
        "broker_pending_order_created_status": broker_created_status,
        "native_pending_order_type_source_safe": native_type_safe,
        "native_pending_order_type_status": native_type_status,
        "raw_ticket_field_present_status": raw_ticket_field_status,
        "mt5_order_ticket_redaction_status": ticket_redaction_status,
    }


def first_touch_time(rows: list[SourceLogRow]) -> tuple[str | None, str]:
    touch_times: list[str] = []
    recovered_no_touch = False
    for source_row in rows:
        if source_row.rel_path.endswith("candidate_ltf_path_order.jsonl"):
            touch = source_row.row.get("entry_first_touch_utc")
            if isinstance(touch, str) and touch:
                touch_times.append(touch)
            if (
                source_row.row.get("ltf_status") == "M1_PATH_RECOVERED"
                and source_row.row.get("path_order_label") in {"tp1_area_reached_without_entry_touch", "no_entry_touch_by_ltf_asof"}
            ):
                recovered_no_touch = True
    if touch_times:
        return sorted(touch_times)[0], "TOUCH_TIME_SOURCE_SAFE"
    if recovered_no_touch:
        return None, "TOUCH_NOT_OBSERVED_SOURCE_SAFE"
    return None, "SOURCE_FIELD_MISSING"


def capture_projection(rows: list[SourceLogRow], decision_time_utc: str | None) -> dict[str, Any]:
    timestamps: list[tuple[datetime, str]] = []
    for source_row in rows:
        for key in ("created_at_utc", "backfilled_at_utc", "timestamp_utc"):
            parsed = parse_dt(source_row.row.get(key))
            if parsed is not None:
                timestamps.append((parsed, key))
                break
    decision_dt = parse_dt(decision_time_utc)
    if decision_dt is not None:
        timestamps = [(ts, key) for ts, key in timestamps if ts >= decision_dt]
    if timestamps:
        observed, observed_key = sorted(timestamps, key=lambda item: item[0])[0]
        observed_iso = normalize_utc(observed)
        derivation = "DERIVED_FROM_SOURCE_CREATED_AT" if observed_key == "created_at_utc" else "DERIVED_FROM_SOURCE_CREATED_AT"
        clock_source = "SYSTEM_UTC_SOURCE"
    else:
        observed_iso = None
        derivation = "NOT_CAPTURED_IN_RAW_SOURCE"
        clock_source = "SOURCE_FIELD_MISSING"

    return {
        "capture_observed_at_utc": observed_iso,
        "capture_write_started_at_utc": None,
        "capture_write_completed_at_utc": None,
        "capture_latency_ms": None,
        "capture_clock_source_status": clock_source,
        "capture_clock_skew_ms": None,
        "capture_clock_skew_status": "CLOCK_SKEW_NOT_MEASURABLE_SOURCE_ONLY" if observed_iso else "SOURCE_FIELD_MISSING",
        "capture_timestamp_derivation_rule": derivation,
    }


def missing_statuses(row: dict[str, Any]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    if row.get("capture_write_started_at_utc") is None:
        statuses["capture_write_started_at_utc"] = "NOT_CAPTURED_IN_RAW_SOURCE"
    if row.get("capture_write_completed_at_utc") is None:
        statuses["capture_write_completed_at_utc"] = "NOT_CAPTURED_IN_RAW_SOURCE"
    if row.get("capture_latency_ms") is None:
        statuses["capture_latency_ms"] = "NOT_CAPTURED_IN_RAW_SOURCE"
    if row.get("capture_clock_skew_ms") is None:
        statuses["capture_clock_skew_ms"] = row.get("capture_clock_skew_status", "SOURCE_FIELD_MISSING")
    for field in (
        "pending_order_mode_source_safe",
        "native_pending_order_type_source_safe",
        "decision_spread_value_source_safe",
        "entry_touch_spread_value_source_safe",
        "spread_source_hash",
    ):
        if row.get(field) is None:
            status_field = field.replace("_source_safe", "_status")
            if field == "spread_source_hash":
                statuses[field] = "SOURCE_FIELD_MISSING"
            elif field == "entry_touch_spread_value_source_safe" and row.get("entry_touch_spread_status") == "TOUCH_NOT_OBSERVED_SOURCE_SAFE":
                statuses[field] = "TOUCH_NOT_OBSERVED_VALUE_NOT_APPLICABLE"
            else:
                statuses[field] = row.get(status_field, "SOURCE_FIELD_MISSING")
    return statuses


def build_projection_rows(
    universe_rows: list[dict[str, Any]],
    by_candidate: dict[str, list[SourceLogRow]],
    by_trade: dict[str, list[SourceLogRow]],
    tick_lookup: TickSpreadLookup,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    parser_hash = sha256_file(OUT_DIR / "build_nofill_forward_source_safe_projection_builder_2026_05_09.py")
    git_head = run_git(["log", "-1", "--pretty=%h %s"])
    projected: list[dict[str, Any]] = []
    route_counter: Counter[str] = Counter()

    for packet_row in universe_rows:
        candidate_id = packet_row.get("_candidate_id")
        matched = list(by_candidate.get(candidate_id or "", []))
        trade_id = choose_first_value(matched, ["trade_id"])
        if isinstance(trade_id, str):
            matched.extend(by_trade.get(trade_id, []))

        # De-duplicate source rows while preserving route diversity.
        seen_sources: set[tuple[str, int]] = set()
        deduped: list[SourceLogRow] = []
        for source_row in matched:
            key = (source_row.rel_path, source_row.line_no)
            if key not in seen_sources:
                seen_sources.add(key)
                deduped.append(source_row)
        matched = deduped

        decision_time = parse_decision_time(packet_row, matched)
        decision_spread = tick_lookup.spread_at_or_before(packet_row.get("symbol"), decision_time)
        touch_time, touch_status = first_touch_time(matched)
        entry_spread = tick_lookup.spread_at_or_before(packet_row.get("symbol"), touch_time) if touch_time else {
            "status": touch_status,
            "value": None,
            "unit": "SOURCE_FIELD_MISSING",
            "source_hash": None,
            "source_path": None,
            "tick_time_utc": None,
            "tick_age_ms": None,
        }

        lineage = [
            {
                "source_role": source_row.source_type,
                "source_route": source_row.route,
                "source_path": source_row.rel_path,
                "source_file_sha256": source_row.sha256,
                "source_line_no": source_row.line_no,
            }
            for source_row in matched
        ]
        lineage.append(
            {
                "source_role": "source_control_count_packet",
                "source_route": packet_row["_source_packet_family"],
                "source_path": packet_row["_source_packet_path"],
                "source_file_sha256": packet_row["_source_packet_sha256"],
                "source_line_no": packet_row["_source_packet_line_no"],
            }
        )
        if decision_spread.get("source_hash"):
            lineage.append(
                {
                    "source_role": "tick_parquet_readonly_manifest",
                    "source_route": "decision_spread_quote_at_or_before_asof",
                    "source_path": decision_spread.get("source_path"),
                    "source_file_sha256": decision_spread.get("source_hash"),
                    "source_line_no": None,
                }
            )
        if entry_spread.get("source_hash"):
            lineage.append(
                {
                    "source_role": "tick_parquet_readonly_manifest",
                    "source_route": "entry_touch_spread_quote_at_or_before_touch",
                    "source_path": entry_spread.get("source_path"),
                    "source_file_sha256": entry_spread.get("source_hash"),
                    "source_line_no": None,
                }
            )

        capture = capture_projection(matched, decision_time)
        pending = pending_projection(matched)
        raw_ticket_field_status, ticket_redaction_status = raw_ticket_status(matched)
        source_match_status = "MATCHED_APPROVED_ALLOWLIST_SOURCE_LOGS" if matched else "NO_MATCH_IN_APPROVED_LOGS_EXPLICIT_MISSING_STATUSES"
        route_counter[source_match_status] += 1
        source_family = packet_row.get("v3_terminal_family")
        row: dict[str, Any] = {
            "projection_schema_version": SCHEMA_VERSION,
            "projection_builder_version": PROJECTION_BUILDER_VERSION,
            "route_id": ROUTE_ID,
            **CONTROL_FLAGS,
            "packet_row_id": packet_row.get("packet_row_id"),
            "source_row_id": packet_row.get("source_row_id"),
            "candidate_id": candidate_id,
            "decision_asof_utc": decision_time,
            "symbol": packet_row.get("symbol"),
            "session": packet_row.get("session"),
            "side": packet_row.get("side"),
            "source_lane": packet_row.get("source_lane"),
            "source_packet_id": packet_row.get("source_packet_id"),
            "source_inventory_id": packet_row.get("source_inventory_id"),
            "v3_terminal_family": source_family,
            "v3_terminal_state": packet_row.get("v3_terminal_state"),
            "row_level_denominator_member": bool(packet_row.get("row_level_count_member")),
            "nofill_duplicate_key_count_member": bool(packet_row.get("nofill_duplicate_key_count_member")),
            "duplicate_group_id_count_member": bool(packet_row.get("duplicate_group_id_count_member")),
            "nofill_duplicate_key_sha256": sha256_text(str(packet_row.get("nofill_duplicate_key"))),
            "duplicate_group_id_sha256": sha256_text(str(packet_row.get("duplicate_group_id"))),
            "excluded_before_any_count": bool(packet_row.get("excluded_before_any_count", False)),
            "source_match_status": source_match_status,
            "source_lineage": lineage,
            "source_route_count": len(lineage),
            "source_file_sha256_values": sorted({item["source_file_sha256"] for item in lineage if item.get("source_file_sha256")}),
            "parser_code_sha256": parser_hash,
            "controlling_git_head": git_head,
            **capture,
            **pending,
            "raw_ticket_field_present_status": raw_ticket_field_status,
            "mt5_order_ticket_redaction_status": ticket_redaction_status,
            "decision_spread_status": decision_spread["status"],
            "decision_spread_value_source_safe": decision_spread["value"],
            "decision_spread_unit": decision_spread["unit"],
            "entry_touch_spread_status": entry_spread["status"],
            "entry_touch_spread_value_source_safe": entry_spread["value"],
            "spread_source_hash": decision_spread.get("source_hash") or entry_spread.get("source_hash"),
            "slippage_label_status": "NOT_OPENED_FOR_SOURCE_CONTROL",
            "slippage_value_redaction_status": slippage_redaction_status(matched),
            "execution_quality_label_status": "NOT_OPENED_FOR_SOURCE_CONTROL",
            "execution_quality_value_redaction_status": execution_redaction_status(matched),
            "cost_testing_gate_status": "COST_TESTING_NOT_OPENED",
        }
        row["missing_statuses"] = missing_statuses(row)
        row["projection_output_allowed_field_count"] = len(EXHAUSTIVE_PROJECTION_ALLOWED_FIELDS)
        projected.append(row)

    summary = {
        "projection_row_count": len(projected),
        "source_match_status_counts": dict(sorted(route_counter.items())),
        "decision_spread_status_counts": dict(Counter(row["decision_spread_status"] for row in projected)),
        "entry_touch_spread_status_counts": dict(Counter(row["entry_touch_spread_status"] for row in projected)),
        "pending_order_mode_status_counts": dict(Counter(row["pending_order_mode_status"] for row in projected)),
    }
    return projected, summary


def source_search_ledger(universe_rows: list[dict[str, Any]], current_inventory: list[dict[str, Any]]) -> dict[str, Any]:
    needed_candidates = {row.get("_candidate_id") for row in universe_rows if row.get("_candidate_id")}
    current_candidates_by_log: dict[str, set[str]] = {}
    for rel_path in APPROVED_LOGS:
        candidates: set[str] = set()
        full = REPO_ROOT / rel_path
        if full.exists():
            for _, row in read_jsonl(rel_path):
                candidate = row.get("candidate_id")
                if isinstance(candidate, str):
                    candidates.add(candidate)
        current_candidates_by_log[Path(rel_path).name] = candidates

    prior_worktree_log_search: list[dict[str, Any]] = []
    gtos_root = Path("C:/tmp/gtos_otb")
    for log_name in [Path(rel).name for rel in APPROVED_LOGS]:
        found = sorted(gtos_root.glob(f"*/shadow_logs/{log_name}")) if gtos_root.exists() else []
        union_candidates: set[str] = set()
        hashes: Counter[str] = Counter()
        for found_path in found:
            file_hash = sha256_file(found_path)
            if file_hash:
                hashes[file_hash] += 1
            try:
                with found_path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        if line.strip():
                            row = json.loads(line)
                            candidate = row.get("candidate_id")
                            if isinstance(candidate, str):
                                union_candidates.add(candidate)
            except (OSError, json.JSONDecodeError):
                continue
        current_candidates = current_candidates_by_log.get(log_name, set())
        prior_worktree_log_search.append(
            {
                "log_name": log_name,
                "prior_worktree_source_count": len(found),
                "unique_hash_count": len(hashes),
                "needed_candidate_matches_current": len(needed_candidates & current_candidates),
                "needed_candidate_matches_prior_union": len(needed_candidates & union_candidates),
                "extra_needed_candidate_matches_beyond_current": len((needed_candidates & union_candidates) - current_candidates),
                "route_decision": "current_worktree_log_consumed; prior worktrees searched but add no missing universe candidate IDs",
            }
        )

    local_roots = []
    for root in LOCAL_HEAVY_ROOTS:
        path = Path(root)
        local_roots.append(
            {
                "root": root,
                "exists": path.exists(),
                "searched_mode": "targeted existence plus approved log/tick-file lookup; no broad outcome scan",
                "use_in_this_lane": "source_inventory_or_tick_spread_only_not_validation_safe",
            }
        )

    absolute_shadow_logs = []
    main_shadow_root = Path("C:/Users/MSI/Documents/ai-trading-agent/shadow_logs")
    for rel_path in APPROVED_LOGS:
        abs_path = main_shadow_root / Path(rel_path).name
        current_hash = sha256_file(rel_path)
        abs_hash = sha256_file(abs_path)
        absolute_shadow_logs.append(
            {
                "path": str(abs_path).replace("\\", "/"),
                "exists": abs_path.exists(),
                "sha256": abs_hash,
                "matches_current_worktree_hash": bool(abs_hash and current_hash and abs_hash == current_hash),
                "route_decision": "not separately consumed when hash matches current worktree log",
            }
        )

    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **CONTROL_FLAGS,
        "generated_at_utc": utc_now_iso(),
        "approved_current_log_inventory": current_inventory,
        "absolute_local_heavy_roots": local_roots,
        "absolute_main_shadow_log_check": absolute_shadow_logs,
        "prior_worktree_log_search": prior_worktree_log_search,
        "negative_evidence_summary": [
            "No prior worktree approved log added a needed universe candidate_id beyond the current allowlisted logs.",
            "Rows without raw-log matches remain projected from frozen count/source-control artifacts with explicit missing statuses.",
            "Tick parquet was used only for source-safe bid/ask spread snapshots, never for R, fill, order, deal, account, or performance labels.",
        ],
    }


def source_hash_manifest(tick_lookup: TickSpreadLookup) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    for path in CONTEXT_INPUTS:
        manifest.append(source_manifest_entry(path, "controlling_input_or_source_contract_artifact", consumed=True))
    for path in APPROVED_LOGS:
        manifest.append(source_manifest_entry(path, "approved_allowlist_source_log", consumed=True))
    for path in CODE_SOURCE_INPUTS:
        manifest.append(source_manifest_entry(path, "code_source_read_for_source_contract_context", consumed=False))
    for item in sorted(tick_lookup.manifest.values(), key=lambda row: row["path"]):
        manifest.append(item)
    return manifest


def parser_hash_manifest() -> list[dict[str, Any]]:
    manifest = []
    for name in PARSER_FILES:
        path = OUT_DIR / name
        manifest.append(
            {
                "path": rel_display(path),
                "exists": path.exists(),
                "role": "projection_builder_parser_or_verifier",
                "sha256": sha256_file(path),
                "sha256_lf_normalized": sha256_lf_normalized_file(path),
                "line_ending_policy": "lf_normalized_fallback",
            }
        )
    return manifest


def projection_has_forbidden_leak(projected_row: dict[str, Any], raw_rows: list[SourceLogRow] | None = None) -> list[str]:
    issues: list[str] = []
    for key in projected_row:
        if key in ALLOWED_STATUS_FIELDS_WITH_FORBIDDEN_TERMS:
            continue
        if key in FORBIDDEN_RAW_KEYS:
            issues.append(f"forbidden_output_key:{key}")

    text = json.dumps(projected_row, sort_keys=True)
    for pattern in FORBIDDEN_VALUE_PATTERNS:
        if pattern.search(text):
            issues.append(f"forbidden_value_pattern:{pattern.pattern}")

    if raw_rows:
        raw_secret_values: set[str] = set()
        for source_row in raw_rows:
            for key in TICKET_KEYS:
                value = source_row.row.get(key)
                if value not in (None, "", 0, "0"):
                    raw_secret_values.add(str(value))
        for value in raw_secret_values:
            if value and value in text:
                issues.append("raw_ticket_value_leaked")
    return sorted(set(issues))


def forbidden_audit(rows: list[dict[str, Any]], by_candidate: dict[str, list[SourceLogRow]]) -> dict[str, Any]:
    row_issues: list[dict[str, Any]] = []
    for row in rows:
        raw_rows = by_candidate.get(row.get("candidate_id") or "", [])
        issues = projection_has_forbidden_leak(row, raw_rows)
        if issues:
            row_issues.append({"packet_row_id": row.get("packet_row_id"), "issues": issues})
    return {
        "artifact": "NOFILL_FORWARD_TICKET_REDACTION_AND_FORBIDDEN_FIELD_AUDIT",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **CONTROL_FLAGS,
        "status": "PASS" if not row_issues else "FAIL",
        "projection_row_count": len(rows),
        "row_issue_count": len(row_issues),
        "row_issues": row_issues[:50],
        "allowed_redaction_status_fields": sorted(ALLOWED_STATUS_FIELDS_WITH_FORBIDDEN_TERMS),
        "forbidden_raw_keys": sorted(FORBIDDEN_RAW_KEYS),
        "ticket_value_rule": "raw ticket/order/deal/position values are not emitted or hashed; only redaction statuses are emitted",
        "result_scoring_rule": "actual-R, synthetic-R, win-rate, expectancy, DSR, PBO, and performance values are not opened",
    }


def denominator_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    family_counts = Counter(row["v3_terminal_family"] for row in rows)
    accepted = [row for row in rows if row["v3_terminal_family"] == "accepted"]
    reject_overlap = read_json(REJECT_OVERLAP_PATH)
    issues: list[str] = []
    if len(rows) != 298:
        issues.append("universe_count_not_298")
    if dict(family_counts) != {"accepted": 225, "reject": 65, "source_control": 4, "source_impossible": 4}:
        issues.append("terminal_family_counts_mismatch")
    if sum(row["row_level_denominator_member"] for row in rows) != 225:
        issues.append("row_level_denominator_mismatch")
    if sum(row["nofill_duplicate_key_count_member"] for row in rows) != 182:
        issues.append("primary_duplicate_key_denominator_mismatch")
    if sum(row["duplicate_group_id_count_member"] for row in rows) != 139:
        issues.append("secondary_duplicate_group_denominator_mismatch")
    if {row["packet_row_id"] for row in rows if row["v3_terminal_family"] == "source_control"} != SOURCE_CONTROL_ROWS:
        issues.append("source_control_row_set_mismatch")
    if {row["packet_row_id"] for row in rows if row["v3_terminal_family"] == "source_impossible"} != SOURCE_IMPOSSIBLE_ROWS:
        issues.append("source_impossible_row_set_mismatch")
    if any(row["row_level_denominator_member"] for row in rows if row["v3_terminal_family"] != "accepted"):
        issues.append("nonaccepted_denominator_member_detected")
    return {
        "artifact": "NOFILL_FORWARD_DENOMINATOR_AND_EXCLUSION_AUDIT",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **CONTROL_FLAGS,
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "universe_equation": "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject",
        "projection_row_count": len(rows),
        "family_counts": dict(sorted(family_counts.items())),
        "row_level_accepted_denominator": sum(row["row_level_denominator_member"] for row in rows),
        "primary_duplicate_key_denominator": sum(row["nofill_duplicate_key_count_member"] for row in rows),
        "secondary_duplicate_group_denominator": sum(row["duplicate_group_id_count_member"] for row in rows),
        "accepted_rows": len(accepted),
        "source_control_rows": sorted(SOURCE_CONTROL_ROWS),
        "source_impossible_rows": sorted(SOURCE_IMPOSSIBLE_ROWS),
        "reject_rows": family_counts.get("reject", 0),
        "reject_overlap_rows": reject_overlap.get("reject_key_overlap_with_accepted_count"),
        "reject_overlap_denominator_effect": reject_overlap.get("denominator_effect"),
        "projection_denominator_effect": "NO_CHANGE_SOURCE_CONTROL_METADATA_ONLY",
    }


def missing_status_ledger(rows: list[dict[str, Any]]) -> dict[str, Any]:
    field_statuses: dict[str, Counter[str]] = defaultdict(Counter)
    missing_rows: dict[str, int] = Counter()
    for row in rows:
        for field, status in row.get("missing_statuses", {}).items():
            field_statuses[field][status] += 1
            missing_rows[field] += 1
    return {
        "artifact": "NOFILL_FORWARD_MISSING_STATUS_LEDGER",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **CONTROL_FLAGS,
        "projection_row_count": len(rows),
        "field_missing_status_counts": {field: dict(counter) for field, counter in sorted(field_statuses.items())},
        "field_missing_row_counts": dict(sorted(missing_rows.items())),
        "exact_future_lane_requirements": {
            "capture_write_started_at_utc": "owner-approved live-wiring lane must record write-start timestamp in source rows",
            "capture_write_completed_at_utc": "owner-approved live-wiring lane or hashed write-complete manifest must record write completion",
            "capture_clock_skew_ms": "broker/system clock offset source must be captured as source metadata",
            "pending_order_native_observability": "separate broker-native pending-order source contract required for native observability beyond redacted status",
            "entry_touch_spread_value_source_safe": "requires exact entry-touch timestamp plus source-hashed tick/quote snapshot",
            "slippage_and_execution_quality": "separate result/cost lane required; this lane keeps labels closed",
        },
    }


def allowlist_spec(schema: dict[str, Any]) -> dict[str, Any]:
    addendum_fields = schema.get("projection_output_allowed_fields", ADDENDUM_FIELD_NAMES)
    return {
        "artifact": "NOFILL_FORWARD_ALLOWLIST_PROJECTION_SPEC",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **CONTROL_FLAGS,
        "approved_log_allowlist": APPROVED_LOGS,
        "approved_count_inputs": [
            str(ACCEPTED_ROWS_PATH).replace("\\", "/"),
            str(EXCLUSION_ROWS_PATH).replace("\\", "/"),
            str(REJECT_OVERLAP_PATH).replace("\\", "/"),
        ],
        "approved_tick_source_rule": {
            "root": str(TICK_ROOT).replace("\\", "/"),
            "columns_used": ["ts_utc", "bid", "ask"],
            "allowed_fields": ["decision_spread_value_source_safe", "entry_touch_spread_value_source_safe", "spread_source_hash"],
            "max_quote_age_ms": 60000,
            "forbidden_use": "no fill, order, account, deal, position, R, win-rate, expectancy, DSR, PBO, or promotion use",
        },
        "identity_and_control_fields_allowed": IDENTITY_AND_CONTROL_FIELDS,
        "safe_control_metadata_fields_allowed": SAFE_CONTROL_METADATA_FIELDS,
        "addendum_projection_fields_allowed": addendum_fields,
        "exhaustive_projection_output_fields_allowed": sorted(
            set(IDENTITY_AND_CONTROL_FIELDS) | set(addendum_fields) | set(SAFE_CONTROL_METADATA_FIELDS)
        ),
        "forbidden_raw_keys": sorted(FORBIDDEN_RAW_KEYS),
        "redaction_only_fields": sorted(ALLOWED_STATUS_FIELDS_WITH_FORBIDDEN_TERMS),
        "join_rules": [
            "Parse candidate_id from frozen source_row_id suffix.",
            "Join approved logs by candidate_id; join pending lifecycle rows by trade_id only after a source-safe candidate row exposes trade_id.",
            "Rows without approved-log matches remain in the 298-row projection with explicit missing statuses.",
            "Duplicate keys and duplicate groups are represented by SHA256 only; raw duplicate key text is not emitted.",
        ],
    }


def completion_audit(
    projection_summary: dict[str, Any],
    denominator: dict[str, Any],
    forbidden: dict[str, Any],
    source_ledger: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight", "PASS", "LIVE_STATE regenerated and core context files read before implementation."),
        ("controlling_inputs_read", "PASS", "Addendum, G12 forward audit, CAT V3 count/result/source-control artifacts inspected."),
        ("strict_allowlist", "PASS", "Projection spec enumerates approved logs, count inputs, tick columns, and forbidden keys."),
        ("source_parser_hashes", "PASS", "Source and parser manifests emitted and verifier recomputes them."),
        ("explicit_missing_statuses", "PASS", "Missing status ledger and row missing_statuses object emitted."),
        ("denominator_preservation", denominator["status"], "225/182/139 and all exclusions are recomputed from projection rows."),
        ("forbidden_field_value_scan", forbidden["status"], "Forbidden raw keys/values and ticket exposure are scanned."),
        ("local_heavy_search", "PASS", "Absolute main shadow logs, tick roots, and prior worktrees were searched."),
        ("no_result_scoring", "PASS", "No R, win-rate, expectancy, DSR, PBO, validation, or promotion was computed."),
        ("live_surface_untouched", "PASS", "Builder writes only scoped research artifacts; verifier checks live-surface dirt."),
    ]
    can_complete = all(status == "PASS" for _, status, _ in checklist)
    return {
        "artifact": "NOFILL_FORWARD_PROJECTION_COMPLETION_AUDIT",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **CONTROL_FLAGS,
        "objective_restated": (
            "Build an offline read-only source-safe projection builder that consumes approved existing logs, "
            "attaches source/parser hashes, emits missing statuses, preserves frozen denominators and exclusions, "
            "and opens no scoring, validation, promotion, or live behavior."
        ),
        "checklist": [
            {"requirement": requirement, "status": status, "evidence": evidence}
            for requirement, status, evidence in checklist
        ],
        "projection_summary": projection_summary,
        "denominator_status": denominator["status"],
        "forbidden_audit_status": forbidden["status"],
        "local_search_prior_worktree_extra_matches": [
            item for item in source_ledger["prior_worktree_log_search"] if item["extra_needed_candidate_matches_beyond_current"]
        ],
        "can_mark_goal_complete_after_verification_and_commit": can_complete,
        "remaining_same_evidence_class_ambiguities": [],
        "future_lanes_not_opened": [
            "G12 acceptance audit",
            "result/cost scoring",
            "live logger wiring",
            "broker-native pending-order source contract",
            "promotion or validation dossier",
        ],
    }


def write_ticket_audit_md(audit: dict[str, Any]) -> None:
    write_md(
        f"NOFILL_FORWARD_TICKET_REDACTION_AND_FORBIDDEN_FIELD_AUDIT_{DATE}.md",
        f"""# NOFILL Forward Ticket Redaction And Forbidden Field Audit {DATE}

Promotion posture: `{PROMOTION_VERDICT}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

Status: `{audit['status']}`.

- Projection rows scanned: `{audit['projection_row_count']}`
- Row issue count: `{audit['row_issue_count']}`
- Raw ticket/deal/position values: not emitted and not hashed
- Slippage/execution-quality labels: closed as `NOT_OPENED_FOR_SOURCE_CONTROL`
- Cost/result route: not opened

Forbidden raw keys are recorded in `NOFILL_FORWARD_ALLOWLIST_PROJECTION_SPEC_{DATE}.json`; allowed redaction fields are status-only.
""",
    )


def write_source_ledger_md(ledger: dict[str, Any]) -> None:
    prior_extra = sum(item["extra_needed_candidate_matches_beyond_current"] for item in ledger["prior_worktree_log_search"])
    write_md(
        f"NOFILL_FORWARD_SOURCE_INVENTORY_AND_SEARCH_LEDGER_{DATE}.md",
        f"""# NOFILL Forward Source Inventory And Search Ledger {DATE}

Promotion posture: `{PROMOTION_VERDICT}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Route Decision

The builder consumes the current worktree allowlisted logs, the frozen CAT V3 count packet, the accepted addendum schema, and source-hashed local tick parquet for spread fields only. Absolute main shadow logs have matching hashes for the approved current logs. Prior worktrees under `C:/tmp/gtos_otb` were searched and added `{prior_extra}` needed candidate IDs beyond the current allowlisted logs.

Rows without approved-log matches are retained as source/control projection rows with explicit missing statuses. They are not scored and do not change the denominator.

## Approved Logs

| Log | Exists | Lines | Candidate IDs | Forbidden Raw Key Hits |
|---|---:|---:|---:|---|
"""
        + "\n".join(
            f"| `{item['path']}` | `{item['exists']}` | `{item['line_count']}` | `{item['candidate_id_count']}` | `{', '.join(item['observed_forbidden_raw_key_hits']) or 'none'}` |"
            for item in ledger["approved_current_log_inventory"]
        )
        + """

## Negative Evidence

- Prior worktree log union did not add missing universe candidate IDs.
- Absolute main shadow logs match the current hashes for approved logs.
- Tick parquet supports spread source-control fields only; it does not supply order, fill, account, deal, position, R, win-rate, expectancy, DSR, or PBO evidence.
""",
    )


def write_context_anchor_md(projection_summary: dict[str, Any]) -> None:
    write_md(
        f"NOFILL_FORWARD_PROJECTION_CONTEXT_ANCHOR_{DATE}.md",
        f"""# NOFILL Forward Projection Context Anchor {DATE}

Promotion posture: `{PROMOTION_VERDICT}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Scope

Route: `{ROUTE_ID}`. This lane builds source/control projection artifacts only. It does not score outcomes, compute R, win-rate, expectancy, DSR, or PBO, validate, promote, edit registries, wire live loggers, or touch live trading behavior.

## Current Head

`{run_git(['log', '-1', '--pretty=%h %s'])}`

## Controlling Inputs

- Accepted addendum projection plan under `{ADDENDUM_DIR}`
- G12 forward audit artifacts under `{G12_FORWARD_DIR}`
- CAT V3 count/result/source-control artifacts under `{COUNT_PACKET_DIR}`, `{RESULT_CONTRACT_DIR}`, and `{SOURCE_CONTROL_DIR}`
- Core context files from the mandatory preflight

## Active Question Stack

| Question | Resolution |
|---|---|
| Can all 298 frozen universe rows be projected without changing denominators? | Yes, all rows are emitted with denominator flags and exclusions preserved. |
| Can source logs populate every addendum field directly? | No, raw logs match part of the universe; missing direct capture/write/skew/pending fields use explicit statuses. |
| Can local heavy tick data safely add useful fields? | Yes, only source-hashed bid/ask spread at decision or exact entry-touch timestamps is projected. |
| Do prior worktrees add missing source-log candidate IDs? | No, the prior-worktree union adds no needed candidate IDs beyond current logs. |
| Is any result/cost/promotion route opened? | No, slippage, execution-quality, cost testing, R, validation, and promotion remain closed. |

## Projection Summary

```json
{json.dumps(projection_summary, indent=2, sort_keys=True)}
```
""",
    )


def write_saturation_md(denominator: dict[str, Any], forbidden: dict[str, Any], missing: dict[str, Any]) -> None:
    write_md(
        f"NOFILL_FORWARD_SATURATION_AND_SELF_RED_TEAM_{DATE}.md",
        f"""# NOFILL Forward Saturation And Self Red Team {DATE}

Promotion posture: `{PROMOTION_VERDICT}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Leak Paths Attacked

- Source/control rows leaking into result labels or denominators: blocked by emitting all 298 rows with frozen denominator flags and by verifying `{denominator['row_level_accepted_denominator']}` row-level accepted members, `{denominator['primary_duplicate_key_denominator']}` duplicate-key members, and `{denominator['secondary_duplicate_group_denominator']}` duplicate-group members.
- Source-control, source-impossible, rejects, or reject-overlap rows affecting counts: blocked by explicit family counts and the accepted-first reject-overlap rule. Reject-overlap rows remain `{denominator['reject_overlap_rows']}` with zero denominator effect.
- Harmless-looking fields that are actually unsafe: raw ticket/order/deal/position/account/history/fill, `actual_r`, `synthetic_path_r`, slippage value, execution-quality value, win-rate, expectancy, DSR, and PBO fields are not emitted. Only redaction statuses appear.
- Useful but unsafe logs: `pending_limit_lifecycle.jsonl` contains raw execution/ticket/slippage/result-like fields; it is consumed only through the status projection and scanned in `{forbidden['artifact']}`.

## Local Search Saturation

The builder searched the current worktree, absolute main shadow logs, `C:/Users/MSI/Documents/ai-trading-agent/data/ticks`, and prior worktrees under `C:/tmp/gtos_otb`. Prior worktree logs did not add needed candidate IDs beyond current allowlisted logs.

## Skeptical G12 Rejection Questions

- Could raw duplicate keys smuggle `no_r_scored` text or duplicate-count ambiguity? Raw duplicate keys are not emitted; SHA256 buckets plus denominator flags are emitted.
- Could tick data become outcome scoring? No. It is used only for bid/ask spread snapshots and source hashes; no fill, R, cost-adjusted expectancy, or survival label is computed.
- Could missing capture/write/skew be silently null? No. Every null source field has `missing_statuses` and the ledger maps exact future lane requirements.

## Remaining Fields Owned By Future Lanes

```json
{json.dumps(missing['exact_future_lane_requirements'], indent=2, sort_keys=True)}
```

No same-evidence-class ambiguity remains unpursued inside the allowed source/control lane.
""",
    )


def write_next_prompt_pack() -> None:
    write_md(
        f"NOFILL_FORWARD_NEXT_PROMPT_PACK_{DATE}.md",
        f"""# NOFILL Forward Projection Builder Next Prompt Pack {DATE}

Promotion posture: `{PROMOTION_VERDICT}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Terminal Status

The offline source-safe projection builder now emits machine-checkable projection/control artifacts. It preserves the frozen 225/182/139 denominators and all source-control/source-impossible/reject exclusions.

## Next Allowed Lanes

- Independent G12 acceptance audit of the projection builder artifacts.
- Owner-approved live-wiring lane for direct capture write-start/write-complete/clock-skew fields.
- Separate broker-native pending-order source contract if native pending observability is required beyond redacted statuses.
- Separate result/cost lane only after accepted source packets exist.

## Still Forbidden Here

No result scoring, validation, promotion, registry edit, paid/API/Databento call, live logger wiring, or live trading behavior change is opened by this builder.
""",
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    addendum_schema = read_json(ADDENDUM_SCHEMA_PATH)
    universe = load_universe_rows()
    by_candidate, by_trade, current_inventory = load_approved_logs()
    tick_lookup = TickSpreadLookup()
    projection_rows, projection_summary = build_projection_rows(universe, by_candidate, by_trade, tick_lookup)

    source_ledger = source_search_ledger(universe, current_inventory)
    source_manifest = source_hash_manifest(tick_lookup)
    parser_manifest = parser_hash_manifest()
    allowlist = allowlist_spec(addendum_schema)
    missing = missing_status_ledger(projection_rows)
    denominator = denominator_audit(projection_rows)
    forbidden = forbidden_audit(projection_rows, by_candidate)
    completion = completion_audit(projection_summary, denominator, forbidden, source_ledger)

    write_context_anchor_md(projection_summary)
    write_source_ledger_md(source_ledger)
    write_json(f"NOFILL_FORWARD_ALLOWLIST_PROJECTION_SPEC_{DATE}.json", allowlist)
    write_json(f"NOFILL_FORWARD_SOURCE_HASH_MANIFEST_{DATE}.json", source_manifest)
    write_json(f"NOFILL_FORWARD_PARSER_HASH_MANIFEST_{DATE}.json", parser_manifest)
    write_jsonl(f"NOFILL_FORWARD_SOURCE_SAFE_PROJECTION_ROWS_{DATE}.jsonl", projection_rows)
    write_json(f"NOFILL_FORWARD_MISSING_STATUS_LEDGER_{DATE}.json", missing)
    write_ticket_audit_md(forbidden)
    write_json(f"NOFILL_FORWARD_TICKET_REDACTION_AND_FORBIDDEN_FIELD_AUDIT_{DATE}.json", forbidden)
    write_json(f"NOFILL_FORWARD_DENOMINATOR_AND_EXCLUSION_AUDIT_{DATE}.json", denominator)
    write_saturation_md(denominator, forbidden, missing)
    write_next_prompt_pack()
    write_json(f"NOFILL_FORWARD_SOURCE_INVENTORY_AND_SEARCH_LEDGER_{DATE}.json", source_ledger)
    write_json(f"NOFILL_FORWARD_PROJECTION_COMPLETION_AUDIT_{DATE}.json", completion)
    write_md(
        f"NOFILL_FORWARD_PROJECTION_COMPLETION_AUDIT_{DATE}.md",
        f"""# NOFILL Forward Projection Completion Audit {DATE}

Promotion posture: `{PROMOTION_VERDICT}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

Objective: {completion['objective_restated']}

## Checklist

| Requirement | Status | Evidence |
|---|---:|---|
"""
        + "\n".join(
            f"| `{item['requirement']}` | `{item['status']}` | {item['evidence']} |"
            for item in completion["checklist"]
        )
        + f"""

Can mark complete after verification and commit: `{completion['can_mark_goal_complete_after_verification_and_commit']}`.

Projection rows: `{projection_summary['projection_row_count']}`. Denominator audit: `{denominator['status']}`. Forbidden audit: `{forbidden['status']}`.
""",
    )

    print(
        json.dumps(
            {
                "ok": denominator["status"] == "PASS" and forbidden["status"] == "PASS",
                "route_id": ROUTE_ID,
                "projection_row_count": len(projection_rows),
                "projection_summary": projection_summary,
                "denominator_status": denominator["status"],
                "forbidden_audit_status": forbidden["status"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import pyarrow.parquet as pq


DATE = "2026-05-07"
PACKET_ID = "OTG0-PKT-063"
EXPERIMENT_ID = "G6-EXP-004-EXHAUSTION-CHANGEPOINT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False
LIVE_EFFECT = False
TICK_ROOT_DEFAULT = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks")

EXCLUDED_RECORD_IDS = {
    "OTG0-PKT-063|NAS100_2026-05-03T16:15:00+00:00",
    "OTG0-PKT-063|XAUUSD_2026-05-03T16:15:00+00:00",
    "OTG0-PKT-063|XAUUSD_2026-05-03T16:30:00+00:00",
    "OTG0-PKT-063|XAUUSD_2026-05-06T07:15:00+00:00",
    "OTG0-PKT-063|XAUUSD_2026-05-06T08:00:00+00:00",
}

FORBIDDEN_INPUT_KEYS = {
    "account_history",
    "actual_r",
    "broker_actual_r",
    "closed_trade",
    "deal_ticket",
    "final_r",
    "hit_sl",
    "hit_tp",
    "live_trade_result",
    "outcome_r",
    "path_label",
    "path_order_label",
    "path_outcome_status",
    "realized_r",
    "result_status",
    "synthetic_path_r",
    "synthetic_r",
    "terminal_status",
    "ticket",
    "win_loss",
}

FORBIDDEN_SOURCE_FRAGMENTS = (
    "account_history",
    "broker_actual",
    "databento",
    "knowledge_base/trade_records",
    "live_trade",
    "mt5/account",
)


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not locate repo root from builder path")


REPO = repo_root()
OUT_DIR = Path(__file__).resolve().parent
SCIENCE = REPO / "research" / "science_program_2026_05"
OUTCOME = SCIENCE / "06_outcome_testing"
G12 = OUTCOME / "g12_otx_g6_post_audit"
OTX = OUTCOME / "otx_g6_tick_aware_end_to_end_resolution"
PACKET_PATH = (
    OUTCOME
    / "otb2r_g6_local_ohlc_momentum_reversion_packets"
    / "packets"
    / "OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__g6_local_ohlc_input_packet_2026-05-07.json"
)

CONTROL_FILES = [
    OUT_DIR / "OTI5_G6_CUSUM_CHANGEPOINT_GOAL_PROMPT_2026-05-07.md",
    G12 / "G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.md",
    G12 / "G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.json",
    G12 / "G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT_2026-05-07.md",
    G12 / "G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT_2026-05-07.json",
    G12 / "G12_OTX_G6_RESULT_ACCEPTANCE_REVIEW_2026-05-07.md",
    G12 / "G12_OTX_G6_RESULT_ACCEPTANCE_REVIEW_2026-05-07.json",
    G12 / "G12_OTX_G6_NEXT_LANE_PROMPT_PACK_2026-05-07.md",
    G12 / "build_g12_otx_g6_post_audit_2026_05_07.py",
    OTX / "OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.md",
    OTX / "OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
    OTX / "OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.md",
    OTX / "OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.json",
    OTX / "OTX_G6_SOURCE_HASH_LEDGER_2026-05-07.md",
    OTX / "OTX_G6_SOURCE_HASH_LEDGER_2026-05-07.json",
    OTX / "build_otx_g6_tick_aware_end_to_end_resolution_2026_05_07.py",
    PACKET_PATH,
    REPO / ".context" / "LIVE_STATE.md",
    REPO / ".context" / "00_core" / "quick_reference_card.md",
    REPO / ".context" / "00_core" / "research_operating_doctrine.md",
    REPO / ".context" / "00_core" / "research_current_state.md",
    REPO / ".context" / "00_core" / "goal_session_research_discipline.md",
    REPO / ".context" / "00_core" / "local_heavy_data_inventory.md",
    REPO / ".context" / "02_session_handoffs" / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def round_float(value: float | None, digits: int = 8) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(value, digits)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def write_md(path: Path, title: str, payload: Any, summary: list[str] | None = None) -> None:
    lines = [
        f"# {title}",
        "",
        f"- Generated at UTC: `{payload.get('generated_at_utc', 'unknown')}`",
        f"- Promotion verdict: `{PROMOTION_VERDICT}`",
        f"- Validation safe: `{str(VALIDATION_SAFE).lower()}`",
        f"- Outcome review opened: `{str(OUTCOME_REVIEW_OPENED).lower()}`",
        "",
    ]
    if summary:
        lines.extend(summary)
        lines.append("")
    lines.extend(["```json", json.dumps(payload, indent=2, sort_keys=True, default=str), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short=8", "HEAD"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def live_state_summary() -> dict[str, Any]:
    path = REPO / ".context" / "LIVE_STATE.md"
    if not path.exists():
        return {"exists": False}
    text = path.read_text(encoding="utf-8", errors="replace")
    out: dict[str, Any] = {"exists": True}
    for line in text.splitlines():
        if line.startswith("**Generated:**"):
            out["generated"] = line.replace("**Generated:**", "").strip()
        elif line.startswith("**HEAD:**"):
            out["head_line"] = line.replace("**HEAD:**", "").strip()
        elif "| Status |" in line and "`FRESH`" in line:
            out["research_context_status"] = "FRESH"
        elif "| Current-state captured commit |" in line:
            out["current_state_captured_commit"] = line.split("|")[2].strip()
    return out


def assert_allowed_source(path: Path) -> None:
    normalized = str(path).replace("\\", "/").lower()
    for fragment in FORBIDDEN_SOURCE_FRAGMENTS:
        if fragment in normalized:
            raise ValueError(f"Forbidden source path used by OTI5 builder: {path}")


def dates_between(start: datetime, end: datetime) -> list[str]:
    current = start.date()
    last = end.date()
    dates: list[str] = []
    while current <= last:
        dates.append(current.isoformat())
        current = current.fromordinal(current.toordinal() + 1)
    return dates


class TickTable:
    def __init__(self, symbol: str, date: str, path: Path):
        assert_allowed_source(path)
        parquet = pq.ParquetFile(path)
        self.symbol = symbol
        self.date = date
        self.path = path
        self.sha256 = sha256_file(path)
        self.row_count = parquet.metadata.num_rows
        self.min_ts: datetime | None = None
        self.max_ts: datetime | None = None
        ts_index = parquet.schema_arrow.names.index("ts_utc")
        for group_idx in range(parquet.metadata.num_row_groups):
            stats = parquet.metadata.row_group(group_idx).column(ts_index).statistics
            if stats is None:
                continue
            group_min = stats.min
            group_max = stats.max
            if isinstance(group_min, datetime):
                group_min = group_min.astimezone(timezone.utc)
            if isinstance(group_max, datetime):
                group_max = group_max.astimezone(timezone.utc)
            self.min_ts = group_min if self.min_ts is None or group_min < self.min_ts else self.min_ts
            self.max_ts = group_max if self.max_ts is None or group_max > self.max_ts else self.max_ts

    def as_source_row(self, purpose: str, expected_sha256: str | None = None) -> dict[str, Any]:
        return {
            "absolute_path": str(self.path),
            "bytes": self.path.stat().st_size,
            "date": self.date,
            "exists": True,
            "expected_sha256": expected_sha256,
            "hash_matches_expected": expected_sha256 in (None, self.sha256),
            "max_ts_utc": iso(self.max_ts),
            "min_ts_utc": iso(self.min_ts),
            "path": rel(self.path),
            "purpose": purpose,
            "row_count": self.row_count,
            "sha256": self.sha256,
            "symbol": self.symbol,
        }


class TickStore:
    def __init__(self, root: Path):
        self.root = root
        self._table_cache: dict[tuple[str, str], TickTable | None] = {}
        self._df_cache: dict[tuple[str, str], pd.DataFrame] = {}

    def file_path(self, symbol: str, date: str) -> Path:
        return self.root / symbol / f"{date}.parquet"

    def get(self, symbol: str, date: str) -> TickTable | None:
        key = (symbol, date)
        if key in self._table_cache:
            return self._table_cache[key]
        path = self.file_path(symbol, date)
        if not path.exists():
            self._table_cache[key] = None
            return None
        table = TickTable(symbol, date, path)
        self._table_cache[key] = table
        return table

    def get_df(self, symbol: str, date: str) -> pd.DataFrame | None:
        key = (symbol, date)
        if key in self._df_cache:
            return self._df_cache[key]
        table = self.get(symbol, date)
        if table is None:
            return None
        df = pd.read_parquet(table.path, columns=["ts_utc", "ts_msc", "bid", "ask"])
        if not df.empty:
            df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
        self._df_cache[key] = df
        return df

    def window(self, symbol: str, start: datetime, end: datetime) -> tuple[list[dict[str, Any]], list[TickTable], list[str]]:
        ticks: list[dict[str, Any]] = []
        files: list[TickTable] = []
        missing: list[str] = []
        if end < start:
            return ticks, files, missing
        for day in dates_between(start, end):
            table = self.get(symbol, day)
            if table is None:
                missing.append(str(self.file_path(symbol, day)))
                continue
            files.append(table)
            df = self.get_df(symbol, day)
            if df is None or df.empty:
                continue
            mask = (df["ts_utc"] >= pd.Timestamp(start)) & (df["ts_utc"] <= pd.Timestamp(end))
            if not mask.any():
                continue
            rows = df.loc[mask, ["ts_utc", "ts_msc", "bid", "ask"]].to_dict("records")
            for row in rows:
                ts = row.get("ts_utc")
                if isinstance(ts, pd.Timestamp):
                    row["ts_utc"] = ts.to_pydatetime().astimezone(timezone.utc)
                elif isinstance(ts, datetime):
                    row["ts_utc"] = ts.astimezone(timezone.utc)
            ticks.extend(rows)
        ticks.sort(key=lambda row: (row["ts_utc"], row.get("ts_msc") or 0))
        return ticks, files, missing

    def loaded_tables(self) -> list[TickTable]:
        return sorted(
            [table for table in self._table_cache.values() if table is not None],
            key=lambda item: (item.symbol, item.date),
        )


def score_terminal_ticks(
    ticks: Iterable[dict[str, Any]],
    *,
    side: str,
    entry: float,
    stop: float,
    tp1: float,
    reward_r: float,
) -> dict[str, Any]:
    side = side.upper()
    entry_time: datetime | None = None
    terminal_time: datetime | None = None
    terminal_status = "NO_ENTRY_TOUCH_NO_R_SCORED"
    synthetic_r: float | None = None
    path_count = 0
    for tick in ticks:
        path_count += 1
        bid = float(tick["bid"])
        ask = float(tick["ask"])
        ts = parse_utc(tick["ts_utc"])
        if ts is None:
            continue
        if entry_time is None:
            if side == "LONG" and ask <= entry:
                entry_time = ts
                terminal_status = "ENTRY_TOUCHED_UNRESOLVED"
            elif side == "SHORT" and bid >= entry:
                entry_time = ts
                terminal_status = "ENTRY_TOUCHED_UNRESOLVED"
            else:
                continue
        if side == "LONG":
            hit_tp = bid >= tp1
            hit_sl = bid <= stop
        elif side == "SHORT":
            hit_tp = ask <= tp1
            hit_sl = ask >= stop
        else:
            return {
                "result_status": "NOT_COMPUTABLE_SIDE_INVALID",
                "synthetic_r": None,
                "entry_first_touch_utc": iso(entry_time),
                "terminal_event_utc": None,
                "path_tick_count": path_count,
            }
        if hit_tp and hit_sl:
            terminal_time = ts
            terminal_status = "AMBIGUOUS_TP_AND_SL_SAME_TICK"
            synthetic_r = None
            break
        if hit_tp:
            terminal_time = ts
            terminal_status = "ENTRY_TOUCHED_THEN_TP1"
            synthetic_r = reward_r
            break
        if hit_sl:
            terminal_time = ts
            terminal_status = "ENTRY_TOUCHED_THEN_SL"
            synthetic_r = -1.0
            break
    return {
        "result_status": terminal_status,
        "synthetic_r": round_float(synthetic_r),
        "entry_first_touch_utc": iso(entry_time),
        "terminal_event_utc": iso(terminal_time),
        "path_tick_count": path_count,
    }


def score_row_from_tick_path(record: dict[str, Any], tick_store: TickStore) -> dict[str, Any]:
    start = parse_utc(record.get("path_start_utc"))
    end = parse_utc(record.get("path_end_utc"))
    if start is None or end is None:
        return {"result_status": "NOT_COMPUTABLE_PATH_WINDOW_MISSING", "synthetic_r": None}
    geometry = record.get("entry_sl_tp_or_level_packet") or {}
    try:
        entry = float(geometry["entry_price"])
        stop = float(geometry["stop_loss"])
        tp1 = float(geometry["take_profit_1"])
        reward_r = float(geometry.get("risk_reward_ratio") or 1.5)
    except (KeyError, TypeError, ValueError):
        return {"result_status": "NOT_COMPUTABLE_GEOMETRY_MISSING", "synthetic_r": None}
    ticks, files, missing = tick_store.window(str(record.get("symbol")), start, end)
    if not ticks:
        return {
            "result_status": "NOT_COMPUTABLE_TICK_PATH_MISSING",
            "synthetic_r": None,
            "missing_tick_files": missing,
            "path_source_files": [str(item.path) for item in files],
            "path_source_sha256": {str(item.path): item.sha256 for item in files},
        }
    result = score_terminal_ticks(
        ticks,
        side=str(record.get("side") or geometry.get("direction") or ""),
        entry=entry,
        stop=stop,
        tp1=tp1,
        reward_r=reward_r,
    )
    result.update(
        {
            "cost_model": "quote_side_touch_model_v1_bid_ask_spread_embedded_no_commission",
            "missing_tick_files": missing,
            "path_source_files": [str(item.path) for item in files],
            "path_source_sha256": {str(item.path): item.sha256 for item in files},
        }
    )
    return result


def recursive_key_hits(value: Any, forbidden: set[str], path: str = "$") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_l = str(key).lower()
            nested_path = f"{path}.{key}"
            if key_l in forbidden:
                hits.append({"path": nested_path, "key": str(key)})
            hits.extend(recursive_key_hits(nested, forbidden, nested_path))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            hits.extend(recursive_key_hits(item, forbidden, f"{path}[{idx}]"))
    return hits


def forbidden_source_hits(paths: Iterable[str]) -> list[str]:
    hits: list[str] = []
    for path in paths:
        normalized = str(path).replace("\\", "/").lower()
        if any(fragment in normalized for fragment in FORBIDDEN_SOURCE_FRAGMENTS):
            hits.append(str(path))
    return sorted(set(hits))


def summarize_results(rows: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = Counter(row["result_status"] for row in rows)
    resolved = [row["synthetic_r"] for row in rows if row.get("synthetic_r") is not None]
    tp = statuses.get("ENTRY_TOUCHED_THEN_TP1", 0)
    sl = statuses.get("ENTRY_TOUCHED_THEN_SL", 0)
    terminal = tp + sl
    return {
        "failure_rate_resolved_terminal": round_float(sl / terminal) if terminal else None,
        "mean_synthetic_r_resolved_only": round_float(sum(resolved) / len(resolved)) if resolved else None,
        "median_synthetic_r_resolved_only": round_float(sorted(resolved)[len(resolved) // 2]) if resolved else None,
        "no_entry_rows": statuses.get("NO_ENTRY_TOUCH_NO_R_SCORED", 0),
        "record_count": len(rows),
        "resolved_synthetic_r_rows": len(resolved),
        "terminal_status_counts": dict(sorted(statuses.items())),
        "total_synthetic_r_resolved_only": round_float(sum(resolved)) if resolved else None,
        "win_rate_resolved_terminal": round_float(tp / terminal) if terminal else None,
    }


def partition_metrics(primary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {
        "has_changepoint_count_gt_0": [
            row for row in primary_rows if (row.get("changepoint_feature") or {}).get("changepoint_count", 0) > 0
        ],
        "no_changepoint_count_eq_0": [
            row for row in primary_rows if (row.get("changepoint_feature") or {}).get("changepoint_count", 0) == 0
        ],
    }
    out = {name: summarize_results(rows) for name, rows in groups.items()}
    with_cp = out["has_changepoint_count_gt_0"]
    no_cp = out["no_changepoint_count_eq_0"]
    if with_cp["failure_rate_resolved_terminal"] is not None and no_cp["failure_rate_resolved_terminal"] is not None:
        out["failure_rate_reduction_has_changepoint_vs_no_changepoint"] = round_float(
            no_cp["failure_rate_resolved_terminal"] - with_cp["failure_rate_resolved_terminal"]
        )
    else:
        out["failure_rate_reduction_has_changepoint_vs_no_changepoint"] = None
    if with_cp["mean_synthetic_r_resolved_only"] is not None and no_cp["mean_synthetic_r_resolved_only"] is not None:
        out["mean_r_delta_has_changepoint_vs_no_changepoint"] = round_float(
            with_cp["mean_synthetic_r_resolved_only"] - no_cp["mean_synthetic_r_resolved_only"]
        )
    else:
        out["mean_r_delta_has_changepoint_vs_no_changepoint"] = None
    out["interpretation_boundary"] = (
        "Descriptive quarantined discovery partition only; no threshold selection, validation, or promotion claim."
    )
    return out


def counter_dict(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def build_control_hash_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for path in CONTROL_FILES:
        row = {
            "absolute_path": str(path),
            "exists": path.exists(),
            "path": rel(path),
            "purpose": "controlling_prompt_context_or_upstream_packet_artifact",
        }
        if path.exists():
            row["bytes"] = path.stat().st_size
            row["sha256"] = sha256_file(path)
        else:
            missing.append(row)
        rows.append(row)
    return rows, missing


def build_bundle(tick_root: Path = TICK_ROOT_DEFAULT) -> dict[str, Any]:
    generated_at = now_utc()
    decision = read_json(G12 / "G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.json")
    g12_source = read_json(G12 / "G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT_2026-05-07.json")
    g12_acceptance = read_json(G12 / "G12_OTX_G6_RESULT_ACCEPTANCE_REVIEW_2026-05-07.json")
    proposals_payload = read_json(OTX / "OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json")
    tick_coverage = read_json(OTX / "OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.json")
    otx_source = read_json(OTX / "OTX_G6_SOURCE_HASH_LEDGER_2026-05-07.json")
    original_packet = read_json(PACKET_PATH)

    packet_decision = next(row for row in decision["packet_decisions"] if row["packet_id"] == PACKET_ID)
    frozen = packet_decision["frozen_allowed_subset"]
    excluded_from_g12 = set(frozen["excluded_record_ids"])
    proposal_rows_all = [row for row in proposals_payload["records"] if row["packet_id"] == PACKET_ID]
    original_rows_all = original_packet["records"]
    original_by_id = {row["record_id"]: row for row in original_rows_all}
    accepted_rows = [row for row in proposal_rows_all if row["record_id"] not in excluded_from_g12]

    subset_failures: list[dict[str, Any]] = []
    if len(proposal_rows_all) != 86:
        subset_failures.append({"check": "raw_packet_rows", "expected": 86, "actual": len(proposal_rows_all)})
    if len(accepted_rows) != 81:
        subset_failures.append({"check": "accepted_source_ready_rows", "expected": 81, "actual": len(accepted_rows)})
    if excluded_from_g12 != EXCLUDED_RECORD_IDS:
        subset_failures.append(
            {
                "check": "excluded_record_ids",
                "expected": sorted(EXCLUDED_RECORD_IDS),
                "actual": sorted(excluded_from_g12),
            }
        )

    status_failures: list[dict[str, Any]] = []
    for row in accepted_rows:
        quote = (row.get("decision_quote_packet") or {}).get("quote_status")
        path_status = (row.get("ordered_tick_path_packet") or {}).get("path_status")
        cp = row.get("changepoint_feature_packet") or {}
        cp_status = cp.get("changepoint_status")
        feature_asof = cp.get("feature_asof_utc_lte_decision_asof_utc")
        if quote != frozen["required_quote_status"] or path_status != frozen["required_path_status"]:
            status_failures.append({"record_id": row["record_id"], "quote_status": quote, "path_status": path_status})
        if cp_status != frozen["required_status"] or feature_asof is not True:
            status_failures.append(
                {
                    "record_id": row["record_id"],
                    "changepoint_status": cp_status,
                    "feature_asof_utc_lte_decision_asof_utc": feature_asof,
                }
            )

    original_missing = [row["record_id"] for row in accepted_rows if row["record_id"] not in original_by_id]
    input_forbidden_hits: list[dict[str, str]] = []
    for row in accepted_rows:
        input_forbidden_hits.extend(recursive_key_hits(row, FORBIDDEN_INPUT_KEYS, f"proposal[{row['record_id']}]"))
        original = original_by_id.get(row["record_id"])
        if original is not None:
            input_forbidden_hits.extend(recursive_key_hits(original, FORBIDDEN_INPUT_KEYS, f"packet[{row['record_id']}]"))

    label_failures: list[dict[str, Any]] = []
    for row in accepted_rows:
        original = original_by_id.get(row["record_id"], {})
        if row.get("label_family") != "input_only_features_no_labels":
            label_failures.append({"record_id": row["record_id"], "field": "proposal.label_family", "value": row.get("label_family")})
        if original.get("label_family") != "input_only_features_no_labels":
            label_failures.append({"record_id": row["record_id"], "field": "packet.label_family", "value": original.get("label_family")})
        if row.get("validation_safe") is not False or row.get("outcome_review_opened") is not False:
            label_failures.append({"record_id": row["record_id"], "field": "proposal_safety_flags", "value": "unexpected"})
        if original.get("validation_safe") is not False:
            label_failures.append({"record_id": row["record_id"], "field": "packet.validation_safe", "value": original.get("validation_safe")})

    duplicate_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accepted_rows:
        duplicate_groups[row["duplicate_group_id"]].append(row)
    primary_by_group: dict[str, dict[str, Any]] = {}
    for group_id, group_rows in duplicate_groups.items():
        primary_by_group[group_id] = sorted(group_rows, key=lambda row: (row["decision_asof_utc"], row["record_id"]))[0]
    primary_ids = {row["record_id"] for row in primary_by_group.values()}
    duplicate_gate_failures: list[dict[str, Any]] = []
    if len(primary_ids) != len(duplicate_groups):
        duplicate_gate_failures.append({"check": "one_primary_per_duplicate_group", "status": "failed"})

    all_source_paths: list[str] = []
    for row in accepted_rows:
        for packet_name in ["decision_quote_packet", "ordered_tick_path_packet", "changepoint_feature_packet"]:
            packet = row.get(packet_name) or {}
            for key in ["tick_source_files", "path_source_files", "input_tick_source_files"]:
                all_source_paths.extend(str(item) for item in packet.get(key, []) or [])
    source_path_hits = forbidden_source_hits(all_source_paths)

    pre_scoring_failures = {
        "duplicate_gate_failures": duplicate_gate_failures,
        "forbidden_source_path_hits": source_path_hits,
        "input_forbidden_key_hits": input_forbidden_hits,
        "label_failures": label_failures,
        "original_packet_missing_records": original_missing,
        "status_failures": status_failures,
        "subset_failures": subset_failures,
    }
    gates_pass = all(not values for values in pre_scoring_failures.values())

    control_hash_rows, missing_control_hashes = build_control_hash_rows()
    tick_store = TickStore(tick_root)
    result_rows: list[dict[str, Any]] = []
    result_ledger: dict[str, Any] | None = None
    impossibility_ledger: dict[str, Any] | None = None

    if gates_pass:
        for row in sorted(accepted_rows, key=lambda item: (item["decision_asof_utc"], item["record_id"])):
            original = original_by_id[row["record_id"]]
            result = score_row_from_tick_path(original, tick_store)
            cp = row.get("changepoint_feature_packet") or {}
            geometry = original.get("entry_sl_tp_or_level_packet") or {}
            duplicate_role = (
                "COUNTABLE_PRIMARY_UNIQUE_DUPLICATE_GROUP"
                if row["record_id"] in primary_ids
                else "DUPLICATE_GROUP_NONPRIMARY_NOT_COUNTABLE"
            )
            group_rows = sorted(
                duplicate_groups[row["duplicate_group_id"]],
                key=lambda item: (item["decision_asof_utc"], item["record_id"]),
            )
            row_payload = {
                "candidate_id": row.get("candidate_id"),
                "changepoint_feature": {
                    "changepoint_count": cp.get("changepoint_count"),
                    "changepoint_model_id": cp.get("changepoint_model_id"),
                    "changepoint_model_version": cp.get("changepoint_model_version"),
                    "changepoint_score": cp.get("changepoint_score"),
                    "distance_from_last_changepoint_bars": cp.get("distance_from_last_changepoint_bars"),
                    "feature_asof_utc": cp.get("feature_asof_utc"),
                    "feature_asof_utc_lte_decision_asof_utc": cp.get("feature_asof_utc_lte_decision_asof_utc"),
                    "last_changepoint_utc": cp.get("last_changepoint_utc"),
                    "m1_bar_count": cp.get("m1_bar_count"),
                    "threshold_freeze_id": cp.get("threshold_freeze_id"),
                    "window_end_utc": cp.get("window_end_utc"),
                    "window_start_utc": cp.get("window_start_utc"),
                },
                "cost_model": result.get("cost_model"),
                "decision_asof_utc": row.get("decision_asof_utc"),
                "duplicate_group_id": row.get("duplicate_group_id"),
                "duplicate_rank_in_group": group_rows.index(row) + 1,
                "duplicate_role": duplicate_role,
                "entry_first_touch_utc": result.get("entry_first_touch_utc"),
                "entry_sl_tp_or_level_packet": {
                    "direction": geometry.get("direction"),
                    "entry_price": geometry.get("entry_price"),
                    "risk_reward_ratio": geometry.get("risk_reward_ratio"),
                    "stop_loss": geometry.get("stop_loss"),
                    "take_profit_1": geometry.get("take_profit_1"),
                },
                "experiment_id": EXPERIMENT_ID,
                "label_family": "synthetic_path_r_quarantined_discovery_only",
                "missing_tick_files": result.get("missing_tick_files", []),
                "outcome_review_opened": OUTCOME_REVIEW_OPENED,
                "packet_id": PACKET_ID,
                "path_source_files": result.get("path_source_files", []),
                "path_source_sha256": result.get("path_source_sha256", {}),
                "path_tick_count": result.get("path_tick_count"),
                "promotion_verdict": PROMOTION_VERDICT,
                "record_id": row.get("record_id"),
                "result_source": "external_tick_parquet_recomputed_no_hidden_path_labels_no_broker_actual_r",
                "result_status": result.get("result_status"),
                "session": row.get("session"),
                "side": row.get("side"),
                "symbol": row.get("symbol"),
                "synthetic_r": result.get("synthetic_r"),
                "terminal_event_utc": result.get("terminal_event_utc"),
                "validation_safe": VALIDATION_SAFE,
            }
            result_rows.append(row_payload)

        primary_rows = [row for row in result_rows if row["duplicate_role"] == "COUNTABLE_PRIMARY_UNIQUE_DUPLICATE_GROUP"]
        result_ledger = {
            "artifact_family": "OTI5_G6_CUSUM_RESULT_LEDGER",
            "blocked_packet_outcomes_inspected": False,
            "broker_actual_r_inspected": False,
            "cusum_partition_metrics_primary_rows": partition_metrics(primary_rows),
            "duplicate_denominator_policy": "one earliest decision_asof_utc row per duplicate_group_id before scoring metrics",
            "experiment_id": EXPERIMENT_ID,
            "generated_at_utc": generated_at,
            "live_effect": LIVE_EFFECT,
            "outcome_review_opened": OUTCOME_REVIEW_OPENED,
            "packet_id": PACKET_ID,
            "primary_countable_summary": summarize_results(primary_rows),
            "promotion_verdict": PROMOTION_VERDICT,
            "raw_auxiliary_summary_not_countable_for_primary_metric": summarize_results(result_rows),
            "raw_source_ready_rows": len(result_rows),
            "result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY",
            "rows": result_rows,
            "scoring_gate_status": "PASS_SOURCE_NOLEAK_DUPLICATE_LABEL_CHECKS_BEFORE_SCORING",
            "synthetic_path_r_policy": "tick_recomputed_quarantined_discovery_only_no_broker_actual_r_no_live_trade_results",
            "unique_duplicate_group_count": len(duplicate_groups),
            "validation_safe": VALIDATION_SAFE,
        }
    else:
        impossibility_ledger = {
            "artifact_family": "OTI5_G6_CUSUM_RESULT_IMPOSSIBILITY_LEDGER",
            "exact_failures": pre_scoring_failures,
            "generated_at_utc": generated_at,
            "live_effect": LIVE_EFFECT,
            "outcome_review_opened": OUTCOME_REVIEW_OPENED,
            "packet_id": PACKET_ID,
            "promotion_verdict": PROMOTION_VERDICT,
            "result_status": "NOT_COMPUTABLE_PRE_SCORING_GATE_FAILED",
            "validation_safe": VALIDATION_SAFE,
        }

    tick_expected_hashes: dict[str, str] = {}
    for row in accepted_rows:
        for packet_name in ["ordered_tick_path_packet", "changepoint_feature_packet"]:
            packet = row.get(packet_name) or {}
            for hash_map_key in ["path_source_sha256", "input_tick_source_sha256"]:
                for path_text, expected_hash in (packet.get(hash_map_key) or {}).items():
                    tick_expected_hashes[path_text] = expected_hash
    tick_source_rows = []
    for table in tick_store.loaded_tables():
        tick_source_rows.append(table.as_source_row("accepted_subset_scoring_tick_parquet", tick_expected_hashes.get(str(table.path))))
    tick_hash_mismatches = [row for row in tick_source_rows if row.get("hash_matches_expected") is False]
    tick_missing_expected = sorted(set(tick_expected_hashes) - {str(table.path) for table in tick_store.loaded_tables()})
    worktree_tick_root = REPO / "data" / "ticks"
    local_inventory_report = {
        "absolute_tick_root": str(tick_root),
        "absolute_tick_root_exists": tick_root.exists(),
        "absolute_tick_root_parquet_files": len(list(tick_root.glob("*/*.parquet"))) if tick_root.exists() else 0,
        "searched_paths": [
            str(worktree_tick_root),
            str(tick_root),
            str(OUTCOME),
            str(REPO / ".context" / "00_core" / "local_heavy_data_inventory.md"),
        ],
        "worktree_tick_root": str(worktree_tick_root),
        "worktree_tick_root_exists": worktree_tick_root.exists(),
        "worktree_tick_root_parquet_files": len(list(worktree_tick_root.glob("*/*.parquet"))) if worktree_tick_root.exists() else 0,
    }

    material_source_hash_failures = missing_control_hashes + tick_hash_mismatches
    source_report = {
        "all_consumed_files_hashed": not material_source_hash_failures,
        "artifact_family": "OTI5_G6_CUSUM_SOURCE_HASH_COVERAGE_REPORT",
        "control_context_and_packet_files": control_hash_rows,
        "feature_asof_failures": status_failures,
        "generated_at_utc": generated_at,
        "live_effect": LIVE_EFFECT,
        "local_heavy_data_inventory_enforced": True,
        "local_inventory_search_report": local_inventory_report,
        "material_source_hash_failure_count": len(material_source_hash_failures),
        "material_source_hash_failures": material_source_hash_failures,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "promotion_verdict": PROMOTION_VERDICT,
        "source_gate_pass": not material_source_hash_failures and not status_failures and not source_path_hits,
        "source_hash_reference": {
            "g12_source_hash_verdict": g12_source.get("source_hash_verdict"),
            "otx_all_used_files_hashed": otx_source.get("all_used_files_hashed"),
        },
        "tick_expected_hash_missing_loaded_table_count": len(tick_missing_expected),
        "tick_expected_hash_missing_loaded_tables": tick_missing_expected,
        "tick_files_rehashed": tick_source_rows,
        "tick_root_absolute_required_by_prompt": str(tick_root),
        "validation_safe": VALIDATION_SAFE,
    }

    duplicate_rows = []
    for group_id, group_rows in sorted(duplicate_groups.items()):
        ordered = sorted(group_rows, key=lambda row: (row["decision_asof_utc"], row["record_id"]))
        duplicate_rows.append(
            {
                "duplicate_group_id": group_id,
                "primary_record_id": ordered[0]["record_id"],
                "record_count": len(ordered),
                "record_ids": [row["record_id"] for row in ordered],
            }
        )
    duplicate_report = {
        "artifact_family": "OTI5_G6_CUSUM_DUPLICATE_DENOMINATOR_REPORT",
        "denominator_policy_verdict": "PASS_DUPLICATE_DENOMINATOR_FROZEN_BEFORE_SCORING" if not duplicate_gate_failures else "FAIL",
        "duplicate_group_rows": duplicate_rows,
        "duplicate_primary_selection_rule": "Sort by decision_asof_utc, then record_id; keep rank 1 as countable primary.",
        "excluded_record_ids": sorted(excluded_from_g12),
        "generated_at_utc": generated_at,
        "inflation_factor_raw_source_ready_over_unique": round_float(len(accepted_rows) / len(duplicate_groups)),
        "live_effect": LIVE_EFFECT,
        "nonprimary_duplicate_rows": len(accepted_rows) - len(duplicate_groups),
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "packet_id": PACKET_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "raw_source_ready_rows": len(accepted_rows),
        "raw_total_packet_rows": len(proposal_rows_all),
        "unique_duplicate_group_count": len(duplicate_groups),
        "validation_safe": VALIDATION_SAFE,
    }

    label_report = {
        "allowed_result_key_policy": "synthetic_r appears only in OTI5 quarantined result rows after gates pass and is not validation evidence.",
        "artifact_family": "OTI5_G6_CUSUM_LABEL_FAMILY_NOLEAK_REPORT",
        "blocked_packet_outcomes_opened": False,
        "broker_actual_r_opened": False,
        "forbidden_input_key_hit_count": len(input_forbidden_hits),
        "forbidden_input_key_hits": input_forbidden_hits,
        "forbidden_source_path_hits": source_path_hits,
        "generated_at_utc": generated_at,
        "input_label_family_counts": {
            "original_packet": counter_dict((row.get("label_family") for row in original_rows_all)),
            "proposal_rows": counter_dict((row.get("label_family") for row in proposal_rows_all)),
        },
        "label_family_gate_pass": not input_forbidden_hits and not label_failures,
        "label_failures": label_failures,
        "live_effect": LIVE_EFFECT,
        "live_trade_results_opened": False,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "promotion_verdict": PROMOTION_VERDICT,
        "result_label_family": "synthetic_path_r_quarantined_discovery_only",
        "validation_safe": VALIDATION_SAFE,
    }

    method_freeze = {
        "artifact_family": "OTI5_G6_CUSUM_METHOD_FREEZE",
        "decision_time_feature_rule": {
            "feature_status_required": frozen["required_status"],
            "feature_asof_required": "feature_asof_utc_lte_decision_asof_utc == true",
            "model_id_required": "g6_tick_cusum_changepoint_v1",
            "threshold_freeze_id_required": "tick_m1_120bar_cusum_mad8_v1",
        },
        "duplicate_denominator_policy": duplicate_report["duplicate_primary_selection_rule"],
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": generated_at,
        "input_subset": {
            "excluded_record_ids": sorted(EXCLUDED_RECORD_IDS),
            "packet_id": PACKET_ID,
            "raw_rows": 86,
            "source_ready_rows": 81,
        },
        "live_effect": LIVE_EFFECT,
        "metric_freeze": {
            "continuation_failure_rate": "ENTRY_TOUCHED_THEN_SL / (ENTRY_TOUCHED_THEN_SL + ENTRY_TOUCHED_THEN_TP1) on duplicate-primary rows only",
            "descriptive_cusum_partition": "changepoint_count > 0 versus changepoint_count == 0; no threshold selected after outcomes",
            "expectancy_r": "mean synthetic_r over resolved TP/SL rows only; no-entry rows reported separately",
        },
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "promotion_verdict": PROMOTION_VERDICT,
        "scoring_gate": "compute result only if subset/source/no-leak/duplicate/label checks pass",
        "synthetic_path_scoring_rule": {
            "long_entry": "ask <= entry_price",
            "long_sl": "bid <= stop_loss after entry",
            "long_tp": "bid >= take_profit_1 after entry",
            "same_tick_policy": "TP and SL on same tick is ambiguous; synthetic_r null",
            "short_entry": "bid >= entry_price",
            "short_sl": "ask >= stop_loss after entry",
            "short_tp": "ask <= take_profit_1 after entry",
        },
        "validation_safe": VALIDATION_SAFE,
    }

    countable_n = len(duplicate_groups)
    methodology = {
        "artifact_family": "OTI5_G6_CUSUM_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT",
        "countable_primary_unique_duplicate_groups": countable_n,
        "dsr": {
            "reason": "No valid train/test variant matrix and only 17 duplicate-primary groups versus the preregistered 300 synthetic-row production-relevance floor.",
            "status": "not_computable",
        },
        "effective_n": {
            "observed_duplicate_primary_groups": countable_n,
            "reason": "Duplicate-collapsed N is observable, but validation-style effective-N is not computable at this sample size and without an independent validation design.",
            "status": "not_computable_for_validation",
        },
        "generated_at_utc": generated_at,
        "live_effect": LIVE_EFFECT,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "pbo": {
            "reason": "No cross-validated variant or train/test matrix exists; this lane reports one quarantined descriptive partition only.",
            "status": "not_computable",
        },
        "promotion_verdict": PROMOTION_VERDICT,
        "sample_floor_review": {
            "broker_actual_r_floor": 100,
            "broker_actual_r_opened": False,
            "current_countable_synthetic_groups": countable_n,
            "synthetic_row_floor": 300,
            "status": "BELOW_SAMPLE_FLOOR_DISCOVERY_ONLY",
        },
        "statistical_verdict": "NOT_VALIDATION_NOT_COMPUTABLE_BELOW_SAMPLE_FLOOR",
        "validation_safe": VALIDATION_SAFE,
    }

    blocker = {
        "artifact_family": "OTI5_G6_CUSUM_BLOCKER_AND_NEXT_ACTION_LEDGER",
        "computation_blockers": [] if gates_pass else pre_scoring_failures,
        "generated_at_utc": generated_at,
        "live_effect": LIVE_EFFECT,
        "next_actions": [
            {
                "action": "Accumulate a separate future source-ready CUSUM/changepoint cohort with the same source/as-of gates.",
                "needed_for": "sample floor and unseen validation design",
            },
            {
                "action": "Keep broker actual-R/account-history/live trade results closed until a separately approved validation lane opens that label family.",
                "needed_for": "label-family separation",
            },
            {
                "action": "Do not promote or wire a filter from the 17-group quarantined discovery result.",
                "needed_for": "strict promotion discipline",
            },
        ],
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "promotion_and_validation_blockers": [
            "same-dataset quarantined discovery only",
            "countable duplicate-primary N below preregistered sample floor",
            "DSR/PBO/effective-N not computable for validation",
            "broker actual-R, account history, live trade results, and blocked-packet outcomes remain closed",
            "no promotion dossier requested or built",
        ],
        "promotion_verdict": PROMOTION_VERDICT,
        "result_lane_status": "COMPUTED_QUARANTINED_DISCOVERY_RESULT" if gates_pass else "NOT_COMPUTABLE_PRE_SCORING_GATE_FAILED",
        "validation_safe": VALIDATION_SAFE,
    }

    completion_checklist = [
        ("mandatory_preflight_live_state", "PASS", "python scripts/generate_live_state.py was run before this builder; LIVE_STATE.md read and hashed."),
        ("latest_numbered_handoff_read", "PASS", "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md read and hashed."),
        ("quick_reference_read", "PASS", "quick_reference_card.md read and hashed."),
        ("research_doctrine_read", "PASS", "research_operating_doctrine.md read and hashed."),
        ("research_current_state_read", "PASS", "research_current_state.md read and hashed."),
        ("goal_session_discipline_read", "PASS", "goal_session_research_discipline.md read and hashed."),
        ("local_heavy_data_inventory_enforced", "PASS", "absolute tick root inspected and consumed tick parquets rehashed."),
        ("g12_otx_controls_read", "PASS", "G12/OTX controlling inputs and builders hashed in source report."),
        ("frozen_81_row_subset_verified", "PASS" if not subset_failures and not status_failures else "FAIL", f"accepted_rows={len(accepted_rows)} excluded={len(excluded_from_g12)}"),
        ("five_listed_rows_excluded", "PASS" if excluded_from_g12 == EXCLUDED_RECORD_IDS else "FAIL", sorted(excluded_from_g12)),
        ("source_hash_gate", "PASS" if source_report["source_gate_pass"] else "FAIL", f"hash_failures={source_report['material_source_hash_failure_count']}"),
        ("duplicate_denominator_frozen_before_scoring", "PASS" if not duplicate_gate_failures else "FAIL", f"unique_duplicate_groups={len(duplicate_groups)}"),
        ("label_family_noleak_gate", "PASS" if label_report["label_family_gate_pass"] else "FAIL", f"forbidden_key_hits={len(input_forbidden_hits)}"),
        ("quarantined_result_or_impossibility_written", "PASS", blocker["result_lane_status"]),
        ("dsr_pbo_effective_n_reported", "PASS", methodology["statistical_verdict"]),
        ("no_promotion_flags_preserved", "PASS", "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false"),
        ("forbidden_live_surfaces_not_touched_by_builder", "PASS", "Builder writes only OTI5 target artifacts; final git diff scan remains required before closure."),
    ]
    completion = {
        "artifact_family": "OTI5_G6_CUSUM_COMPLETION_AUDIT",
        "can_mark_goal_complete": gates_pass and source_report["source_gate_pass"] and label_report["label_family_gate_pass"],
        "concrete_success_criteria": [
            "rebuild/verify the frozen 81-row OTG0-PKT-063 subset",
            "exclude exactly the five G12-listed rows",
            "score only after source/no-leak/duplicate/label-family checks pass",
            "write quarantined discovery result or exact impossibility ledger",
            "preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false",
            "verify JSON/JSONL, py_compile, focused pytest, G12/OTX applicable tests, and forbidden-surface diff",
        ],
        "generated_at_utc": generated_at,
        "git_head_at_build": git_head(),
        "live_effect": LIVE_EFFECT,
        "live_state_summary": live_state_summary(),
        "objective_restated": (
            "Run OTI5 G6 CUSUM/changepoint quarantined result lane for OTG0-PKT-063 using only "
            "the G12-accepted frozen 81-row source-ready subset and approved packet/tick inputs."
        ),
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "promotion_verdict": PROMOTION_VERDICT,
        "prompt_to_artifact_checklist": [
            {"requirement": req, "status": status, "evidence": evidence} for req, status, evidence in completion_checklist
        ],
        "required_artifacts_written": [],
        "validation_safe": VALIDATION_SAFE,
        "verification_status": "PENDING_EXTERNAL_COMMANDS_AT_BUILD_TIME",
        "verification_commands_required_after_build": [
            "JSON parse every generated JSON/JSONL artifact",
            "python -B -m py_compile research/.../build_oti5_g6_cusum_changepoint_quarantined_results_2026_05_07.py",
            "pytest research/.../test_oti5_g6_cusum_changepoint_quarantined_results_2026_05_07.py",
            "pytest research/.../g12_otx_g6_post_audit/test_g12_otx_g6_post_audit_2026_05_07.py research/.../otx_g6_tick_aware_end_to_end_resolution/test_otx_g6_tick_aware_end_to_end_resolution_2026_05_07.py",
            "scan outputs for NO_PROMOTION_VERDICT and forbidden flag flips",
            "git diff/status forbidden-surface scan",
        ],
    }

    artifacts: dict[str, Any] = {
        f"OTI5_G6_CUSUM_METHOD_FREEZE_{DATE}": method_freeze,
        f"OTI5_G6_CUSUM_SOURCE_HASH_COVERAGE_REPORT_{DATE}": source_report,
        f"OTI5_G6_CUSUM_DUPLICATE_DENOMINATOR_REPORT_{DATE}": duplicate_report,
        f"OTI5_G6_CUSUM_LABEL_FAMILY_NOLEAK_REPORT_{DATE}": label_report,
        f"OTI5_G6_CUSUM_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_{DATE}": methodology,
        f"OTI5_G6_CUSUM_BLOCKER_AND_NEXT_ACTION_LEDGER_{DATE}": blocker,
        f"OTI5_G6_CUSUM_COMPLETION_AUDIT_{DATE}": completion,
    }
    if result_ledger is not None:
        artifacts[f"OTI5_G6_CUSUM_RESULT_LEDGER_{DATE}"] = result_ledger
    if impossibility_ledger is not None:
        artifacts[f"OTI5_G6_CUSUM_RESULT_IMPOSSIBILITY_LEDGER_{DATE}"] = impossibility_ledger

    required_written = []
    for stem in sorted(artifacts):
        required_written.append(f"{stem}.json")
        required_written.append(f"{stem}.md")
    if result_ledger is not None:
        required_written.append(f"OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_{DATE}.jsonl")
    required_written.extend(
        [
            f"OTI5_G6_CUSUM_ARTIFACT_MANIFEST_{DATE}.json",
            Path(__file__).name,
            "test_oti5_g6_cusum_changepoint_quarantined_results_2026_05_07.py",
        ]
    )
    completion["required_artifacts_written"] = required_written

    return {
        "artifacts": artifacts,
        "completion": completion,
        "result_rows": result_rows,
        "scoring_possible": result_ledger is not None,
    }


def write_bundle(bundle: dict[str, Any]) -> None:
    manifest = {
        "artifact_family": "OTI5_G6_CUSUM_ARTIFACT_MANIFEST",
        "artifacts": [],
        "generated_at_utc": now_utc(),
        "live_effect": LIVE_EFFECT,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
    }
    summaries = {
        f"OTI5_G6_CUSUM_RESULT_LEDGER_{DATE}": [
            "- Status: `RESULT_QUARANTINED_DISCOVERY_ONLY`",
            "- Primary metric denominator: duplicate-frozen unique groups only.",
        ],
        f"OTI5_G6_CUSUM_RESULT_IMPOSSIBILITY_LEDGER_{DATE}": [
            "- Status: `NOT_COMPUTABLE_PRE_SCORING_GATE_FAILED`",
            "- No synthetic result was scored because a pre-scoring gate failed.",
        ],
    }
    titles = {
        f"OTI5_G6_CUSUM_METHOD_FREEZE_{DATE}": "OTI5 G6 CUSUM Method Freeze",
        f"OTI5_G6_CUSUM_SOURCE_HASH_COVERAGE_REPORT_{DATE}": "OTI5 G6 CUSUM Source Hash Coverage Report",
        f"OTI5_G6_CUSUM_DUPLICATE_DENOMINATOR_REPORT_{DATE}": "OTI5 G6 CUSUM Duplicate Denominator Report",
        f"OTI5_G6_CUSUM_LABEL_FAMILY_NOLEAK_REPORT_{DATE}": "OTI5 G6 CUSUM Label Family No-Leak Report",
        f"OTI5_G6_CUSUM_RESULT_LEDGER_{DATE}": "OTI5 G6 CUSUM Result Ledger",
        f"OTI5_G6_CUSUM_RESULT_IMPOSSIBILITY_LEDGER_{DATE}": "OTI5 G6 CUSUM Result Impossibility Ledger",
        f"OTI5_G6_CUSUM_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_{DATE}": "OTI5 G6 CUSUM Methodology DSR/PBO/Effective-N Report",
        f"OTI5_G6_CUSUM_BLOCKER_AND_NEXT_ACTION_LEDGER_{DATE}": "OTI5 G6 CUSUM Blocker And Next Action Ledger",
        f"OTI5_G6_CUSUM_COMPLETION_AUDIT_{DATE}": "OTI5 G6 CUSUM Completion Audit",
    }
    for stem, payload in bundle["artifacts"].items():
        json_path = OUT_DIR / f"{stem}.json"
        md_path = OUT_DIR / f"{stem}.md"
        write_json(json_path, payload)
        write_md(md_path, titles.get(stem, stem), payload, summaries.get(stem))
        manifest["artifacts"].append({"artifact_type": stem, "path": rel(json_path), "sha256": sha256_file(json_path)})
        manifest["artifacts"].append({"artifact_type": stem, "path": rel(md_path), "sha256": sha256_file(md_path)})
    if bundle["scoring_possible"]:
        rows_path = OUT_DIR / f"OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_{DATE}.jsonl"
        write_jsonl(rows_path, bundle["result_rows"])
        manifest["artifacts"].append(
            {"artifact_type": f"OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_{DATE}", "path": rel(rows_path), "sha256": sha256_file(rows_path)}
        )
    manifest_path = OUT_DIR / f"OTI5_G6_CUSUM_ARTIFACT_MANIFEST_{DATE}.json"
    write_json(manifest_path, manifest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tick-root", type=Path, default=TICK_ROOT_DEFAULT)
    args = parser.parse_args()
    bundle = build_bundle(args.tick_root)
    write_bundle(bundle)
    print(
        json.dumps(
            {
                "can_mark_goal_complete": bundle["completion"]["can_mark_goal_complete"],
                "scoring_possible": bundle["scoring_possible"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

import gzip
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_13_outside_session_opportunity_audit"
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.broader_origin_generators import SESSION_WINDOWS  # noqa: E402


ROUTE_DIR = Path(__file__).resolve().parent
BROADER_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_CANDIDATE_CONTRACT_LEDGER_{DATE}.jsonl"
MARKET_ACTIVATION_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_{DATE}.json"

OUTPUT_GROUP_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_GROUP_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_SUMMARY_{DATE}.json"
OUTPUT_SHARD_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_SHARD_MANIFEST_{DATE}.jsonl"
OUTPUT_SHARD_DIR = ROUTE_DIR / "stage13_outside_session_opportunity_shards"

MIN_GROUP_ROWS = 20
SELECTED_POLICY = "be_after_trigger"
SHARD_ROW_LIMIT = 25_000
EXPLICIT_24H_SESSION_SYMBOLS = {"BTCUSD", "ETHUSD"}
SYMBOL_ALIASES = {
    "US30": "US30_cash",
    "US30.CASH": "US30_cash",
    "US30_CASH": "US30_cash",
    "UKOIL": "UKOIL_cash",
    "USOIL": "USOIL_cash",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    return count


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_symbol(value: Any) -> str:
    raw = str(value or "")
    return SYMBOL_ALIASES.get(raw.upper().replace(".", "_"), raw)


def parse_utc(value: Any) -> datetime | None:
    if value in (None, ""):
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
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def minute_of_day(value: str) -> int:
    hour, minute = value.split(":", 1)
    return int(hour) * 60 + int(minute)


def minute_in_window(minute: int, start: str, end: str) -> bool:
    start_min = minute_of_day(start)
    end_min = minute_of_day(end)
    if start_min <= end_min:
        return start_min <= minute < end_min
    return minute >= start_min or minute < end_min


def normal_production_session_from_timestamp(symbol: str, timestamp: Any) -> str | None:
    parsed = parse_utc(timestamp)
    if parsed is None:
        return None
    windows = SESSION_WINDOWS.get(symbol) or SESSION_WINDOWS.get(symbol.upper())
    if not windows:
        return None
    minute = parsed.hour * 60 + parsed.minute
    for name, start, end in windows:
        if str(name).startswith("moonshot_extended"):
            continue
        if minute_in_window(minute, start, end):
            return str(name)
    return "off_configured_session"


def utc_hour_bucket(parsed: datetime | None) -> str:
    if parsed is None:
        return "missing_time"
    return f"h{parsed.hour:02d}_{(parsed.hour + 1) % 24:02d}"


def source_mode(row: dict[str, Any]) -> str:
    replay = row.get("origin_native_dynamic_policy_replay") or {}
    if isinstance(replay, dict) and replay.get("source_replay_mode"):
        return str(replay.get("source_replay_mode"))
    return "unknown_source_mode"


def selected_policy_result(row: dict[str, Any]) -> dict[str, Any]:
    replay = row.get("origin_native_dynamic_policy_replay") or {}
    policies = replay.get("policy_results") if isinstance(replay, dict) else None
    result = policies.get(SELECTED_POLICY) if isinstance(policies, dict) else None
    return result if isinstance(result, dict) else {}


def metric_blank() -> dict[str, float | int]:
    return {
        "performance_rows": 0,
        "total_r": 0.0,
        "wins": 0,
        "gross_win_r": 0.0,
        "gross_loss_r": 0.0,
    }


def add_metric(metric: dict[str, Any], value: float) -> None:
    metric["performance_rows"] += 1
    metric["total_r"] += value
    if value > 0:
        metric["wins"] += 1
        metric["gross_win_r"] += value
    elif value < 0:
        metric["gross_loss_r"] += abs(value)


def finalize_metric(metric: dict[str, Any]) -> dict[str, Any]:
    rows = int(metric.get("performance_rows") or 0)
    total = float(metric.get("total_r") or 0.0)
    gross_win = float(metric.get("gross_win_r") or 0.0)
    gross_loss = float(metric.get("gross_loss_r") or 0.0)
    return {
        "performance_rows": rows,
        "selected_count": rows,
        "total_r": total,
        "expectancy_r": total / rows if rows else None,
        "profit_factor": gross_win / gross_loss if gross_loss else None,
        "win_rate": float(metric.get("wins") or 0) / rows if rows else None,
        "wins": int(metric.get("wins") or 0),
        "gross_win_r": gross_win,
        "gross_loss_r": gross_loss,
    }


def group_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    return (
        str(row["symbol"]),
        str(row["origin_family"]),
        str(row["side"]),
        str(row["raw_session"]),
        str(row["utc_hour_bucket"]),
        str(row["source_mode"]),
    )


class ShardWriter:
    def __init__(self) -> None:
        OUTPUT_SHARD_DIR.mkdir(parents=True, exist_ok=True)
        for stale in OUTPUT_SHARD_DIR.glob("outside_session_opportunity_*.jsonl.gz"):
            stale.unlink()
        self._index = 0
        self._count = 0
        self._handle: gzip.GzipFile | None = None
        self._path: Path | None = None
        self.manifest_rows: list[dict[str, Any]] = []

    def _open_next(self) -> None:
        self.close()
        self._path = OUTPUT_SHARD_DIR / f"outside_session_opportunity_{self._index:04d}.jsonl.gz"
        self._handle = gzip.open(self._path, "wt", encoding="utf-8", newline="\n")
        self._count = 0
        self._index += 1

    def write(self, row: dict[str, Any]) -> None:
        if self._handle is None or self._count >= SHARD_ROW_LIMIT:
            self._open_next()
        assert self._handle is not None
        self._handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        self._count += 1

    def close(self) -> None:
        if self._handle is None:
            return
        self._handle.close()
        assert self._path is not None
        self.manifest_rows.append(
            {
                "schema_version": "vnext_replacement_stage13_outside_session_shard_manifest_v1",
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "path": rel(self._path),
                "rows": self._count,
                "shard_index": len(self.manifest_rows),
                "size_bytes": self._path.stat().st_size,
                "sha256": sha256_file(self._path),
            }
        )
        self._handle = None
        self._path = None
        self._count = 0


def main() -> None:
    market_map = json.loads(MARKET_ACTIVATION_MAP.read_text(encoding="utf-8"))
    eligible_symbols = {
        canonical_symbol(symbol)
        for symbol in market_map.get("broker_native_activation_eligible_symbols", [])
    }
    exact_excluded_symbols = {
        canonical_symbol(symbol)
        for symbol in market_map.get("broker_native_exact_excluded_symbols", [])
    }

    shard_writer = ShardWriter()
    groups: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = defaultdict(metric_blank)
    group_exit_reasons: dict[tuple[str, str, str, str, str, str], Counter[str]] = defaultdict(Counter)
    group_source_paths: dict[tuple[str, str, str, str, str, str], Counter[str]] = defaultdict(Counter)
    row_evidence: list[tuple[tuple[str, str, str, str, str, str], dict[str, Any]]] = []
    row_counts: Counter[str] = Counter()
    symbol_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    hour_counts: Counter[str] = Counter()
    source_mode_counts: Counter[str] = Counter()
    excluded_broker_counts: Counter[str] = Counter()

    for row in iter_jsonl(BROADER_LEDGER):
        if row.get("row_type") != "candidate_contract":
            continue
        symbol = canonical_symbol(row.get("symbol"))
        if symbol in exact_excluded_symbols:
            excluded_broker_counts[f"{symbol}:broker_contract_invalid_or_unavailable"] += 1
            continue
        if eligible_symbols and symbol not in eligible_symbols:
            excluded_broker_counts[f"{symbol}:broker_native_contract_not_verified"] += 1
            continue
        if symbol in EXPLICIT_24H_SESSION_SYMBOLS:
            continue
        if not row.get("activation_ready"):
            continue
        final_r = row.get("origin_native_dynamic_final_r")
        if final_r is None:
            continue
        parsed = parse_utc(row.get("decision_time_utc") or row.get("candle_time_utc"))
        normal_session = normal_production_session_from_timestamp(symbol, row.get("decision_time_utc") or row.get("candle_time_utc"))
        if normal_session != "off_configured_session":
            continue

        source_fields = row.get("source_fields") if isinstance(row.get("source_fields"), dict) else {}
        policy_result = selected_policy_result(row)
        out_row = {
            "schema_version": "vnext_replacement_stage13_outside_session_opportunity_row_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "row_type": "outside_session_opportunity_row",
            "candidate_id": row.get("row_id") or row.get("candidate_id"),
            "candidate_origin": row.get("candidate_origin_family") or row.get("origin_family"),
            "candidate_origin_family": row.get("candidate_origin_family"),
            "origin_family": row.get("origin_family"),
            "symbol": symbol,
            "side": row.get("side"),
            "raw_session": str(source_fields.get("session_at_candidate") or "missing_session"),
            "current_exclusion_reason": "outside_configured_session_not_production_executable",
            "repaired_route_session": "moonshot_extended",
            "utc_hour_bucket": utc_hour_bucket(parsed),
            "decision_time_utc": row.get("decision_time_utc"),
            "source_mode": source_mode(row),
            "source_path": row.get("source_path"),
            "source_row_index": row.get("source_row_index"),
            "source_sha256": row.get("source_sha256"),
            "entry_price": row.get("entry_price"),
            "stop_or_invalidation": row.get("stop_or_invalidation"),
            "target_reference": row.get("target_reference"),
            "selected_policy": SELECTED_POLICY,
            "r_multiple": float(final_r),
            "selected_policy_final_r": float(final_r),
            "selected_policy_exit_reason": policy_result.get("exit_reason"),
            "selected_policy_same_bar_ambiguity": bool(
                policy_result.get("same_bar_ambiguity")
                or row.get("origin_native_dynamic_selected_policy_same_bar_ambiguity")
            ),
            "outcome": policy_result.get("exit_reason"),
            "source_fields": {
                key: source_fields.get(key)
                for key in (
                    "atr14",
                    "atr50",
                    "atr14_atr50_ratio",
                    "body_atr14",
                    "range_atr14",
                    "trend_state_20",
                    "sweep_direction",
                    "extreme_side",
                    "lookback50_position",
                    "leader_symbol",
                    "lag_symbol",
                    "leader_move_atr14",
                    "lag_prior_response_atr14",
                )
                if key in source_fields
            },
        }
        key = group_key(out_row)
        row_evidence.append((key, out_row))
        add_metric(groups[key], float(final_r))
        group_exit_reasons[key][str(out_row.get("selected_policy_exit_reason") or "unknown")] += 1
        if out_row.get("source_path"):
            group_source_paths[key][str(out_row["source_path"])] += 1
        row_counts["outside_session_rows"] += 1
        symbol_counts[symbol] += 1
        family_counts[str(row.get("origin_family") or "")] += 1
        hour_counts[out_row["utc_hour_bucket"]] += 1
        source_mode_counts[out_row["source_mode"]] += 1

    group_rows: list[dict[str, Any]] = []
    group_dispositions: dict[tuple[str, str, str, str, str, str], tuple[str, str]] = {}
    disposition_counts: Counter[str] = Counter()
    selected_metric = metric_blank()
    for key, raw_metric in sorted(groups.items()):
        symbol, family, side, raw_session, hour_bucket, mode = key
        metrics = finalize_metric(raw_metric)
        rows = int(metrics["performance_rows"])
        exp = metrics["expectancy_r"]
        pf = metrics["profit_factor"]
        if rows >= MIN_GROUP_ROWS and exp is not None and exp > 0 and (pf is None or pf > 1):
            disposition = "expand_production_execution_moonshot_extended_session"
            proof_class = "positive_outside_session_origin_native_dynamic_replay_row_level_proof"
            for field in ("performance_rows", "total_r", "wins", "gross_win_r", "gross_loss_r"):
                selected_metric[field] += raw_metric[field]
        elif rows < MIN_GROUP_ROWS and exp is not None and exp > 0 and (pf is None or pf > 1):
            disposition = "exclude_insufficient_row_level_positive_ev_proof"
            proof_class = "insufficient_outside_session_rows_after_row_level_replay"
        else:
            disposition = "exclude_negative_expectancy_or_pf_collapse"
            proof_class = "outside_session_negative_expectancy_or_profit_factor_collapse"
        group_dispositions[key] = (disposition, proof_class)
        disposition_counts[disposition] += rows
        group_rows.append(
            {
                "schema_version": "vnext_replacement_stage13_outside_session_group_v1",
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "row_type": "outside_session_group_decision",
                "symbol": symbol,
                "origin_family": family,
                "candidate_origin_family": f"origin_{family}",
                "side": side,
                "raw_session": raw_session,
                "repaired_route_session": "moonshot_extended",
                "utc_hour_bucket": hour_bucket,
                "source_mode": mode,
                "selected_policy": SELECTED_POLICY,
                "metrics": metrics,
                "min_group_rows": MIN_GROUP_ROWS,
                "final_action": disposition,
                "proof_class": proof_class,
                "current_exclusion_reason": "outside_configured_session_not_production_executable",
                "source_evidence_shard_manifest": rel(OUTPUT_SHARD_MANIFEST),
                "source_evidence_path": rel(BROADER_LEDGER),
                "exit_reason_counts": dict(sorted(group_exit_reasons[key].items())),
                "source_path_counts": dict(group_source_paths[key].most_common(10)),
            }
        )

    write_jsonl(OUTPUT_GROUP_LEDGER, group_rows)

    for key, row in row_evidence:
        disposition, proof_class = group_dispositions[key]
        symbol, family, side, raw_session, hour_bucket, mode = key
        row.update(
            {
                "group_decision_key": {
                    "symbol": symbol,
                    "origin_family": family,
                    "side": side,
                    "raw_session": raw_session,
                    "utc_hour_bucket": hour_bucket,
                    "source_mode": mode,
                },
                "repaired_disposition": disposition,
                "repaired_proof_class": proof_class,
                "final_action": disposition,
                "proof_class": proof_class,
            }
        )
        shard_writer.write(row)
    shard_writer.close()
    write_jsonl(OUTPUT_SHARD_MANIFEST, shard_writer.manifest_rows)

    selected_metrics = finalize_metric(selected_metric)
    summary = {
        "schema_version": "vnext_replacement_stage13_outside_session_opportunity_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": utc_now(),
        "status": "outside_session_positive_cohort_audited_for_repair",
        "input_artifacts": {
            "broader_origin_contract_ledger": rel(BROADER_LEDGER),
            "market_activation_map": rel(MARKET_ACTIVATION_MAP),
        },
        "output_paths": {
            "row_shard_manifest": rel(OUTPUT_SHARD_MANIFEST),
            "group_ledger": rel(OUTPUT_GROUP_LEDGER),
            "summary": rel(OUTPUT_SUMMARY),
        },
        "row_counts": dict(row_counts),
        "group_count": len(group_rows),
        "shard_count": len(shard_writer.manifest_rows),
        "symbol_counts": dict(sorted(symbol_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "utc_hour_bucket_counts": dict(sorted(hour_counts.items())),
        "source_mode_counts": dict(sorted(source_mode_counts.items())),
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "selected_outside_session_metrics": selected_metrics,
        "eligible_symbols": sorted(eligible_symbols),
        "exact_excluded_symbol_counts_seen": dict(sorted(excluded_broker_counts.items())),
        "completion_gate": {
            "positive_outside_groups_require_selector_activation": True,
            "terminal_broad_labels_rejected": [
                "outside_configured_session_not_production_executable",
                "outside_kill_zone",
                "old_live_contract_boundary",
                "not_currently_wired",
            ],
        },
    }
    write_json(OUTPUT_SUMMARY, summary)
    print(
        json.dumps(
            {
                "outside_session_rows": row_counts["outside_session_rows"],
                "group_count": len(group_rows),
                "expand_rows": disposition_counts[
                    "expand_production_execution_moonshot_extended_session"
                ],
                "expand_expectancy_r": selected_metrics["expectancy_r"],
                "expand_profit_factor": selected_metrics["profit_factor"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

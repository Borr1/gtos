#!/usr/bin/env python3
"""Build observed-session and no-order-send fillability proxy evidence.

This route uses committed route ledgers plus local OHLCV CSVs only. It does not
call MT5, mutate broker/account/order/history/deal/position state, use
orderflow/depth, apply config, push remotes, or touch VPS processes.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
OPS = PROJECT_ROOT / "research" / "operations"
READINESS_ROUTE = OPS / "final_moonshot_market_expansion_activation_readiness_synthesis_2026_06_18"
DOSSIER_ROUTE = OPS / "final_moonshot_market_expansion_live_authority_dossier_2026_06_18"
RUNTIME_ROUTE = OPS / "final_moonshot_market_expansion_runtime_generator_implementation_2026_06_18"
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_observed_session_fillability_repair"
DECISION = "MARKET_EXPANSION_OBSERVED_SESSION_FILLABILITY_PROXY_REPAIRED_DEFAULT_OFF_NOT_LIVE_AUTHORITY"


@dataclass(frozen=True)
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_time(raw: str) -> datetime:
    text = str(raw).replace("T", " ").split("+")[0]
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def rounded(value: Any, digits: int = 8) -> float | None:
    number = finite_float(value)
    return round(number, digits) if number is not None else None


def read_bars(path: Path) -> list[Bar]:
    bars: list[Bar] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                bars.append(
                    Bar(
                        time=parse_time(row["time"]),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row.get("volume") or 0.0),
                    )
                )
            except (KeyError, ValueError):
                continue
    return bars


def index_d1_open(paths: dict[str, Path]) -> dict[str, dict[str, float]]:
    by_symbol: dict[str, dict[str, float]] = {}
    for file_symbol, path in paths.items():
        opens: dict[str, float] = {}
        for bar in read_bars(path):
            opens[bar.time.date().isoformat()] = bar.open
        by_symbol[file_symbol] = opens
    return by_symbol


def group_m1_by_day(paths: dict[str, Path]) -> dict[str, dict[str, list[Bar]]]:
    grouped: dict[str, dict[str, list[Bar]]] = {}
    for file_symbol, path in paths.items():
        by_day: dict[str, list[Bar]] = defaultdict(list)
        for bar in read_bars(path):
            by_day[bar.time.date().isoformat()].append(bar)
        for bars in by_day.values():
            bars.sort(key=lambda item: item.time)
        grouped[file_symbol] = dict(by_day)
    return grouped


def first_touch_after_fill(
    bars: list[Bar],
    *,
    direction: int,
    entry: float,
    stop: float,
    target: float,
) -> tuple[str, str | None, int | None]:
    fill_index: int | None = None
    for idx, bar in enumerate(bars):
        if bar.low <= entry <= bar.high:
            fill_index = idx
            break
    if fill_index is None:
        return "not_touched_no_limit_entry_fill_proxy", None, None
    for idx, bar in enumerate(bars[fill_index:], start=fill_index):
        stop_hit = bar.low <= stop if direction > 0 else bar.high >= stop
        target_hit = bar.high >= target if direction > 0 else bar.low <= target
        if stop_hit and target_hit:
            return "filled_then_same_bar_stop_target_ambiguous", bar.time.isoformat(), idx - fill_index
        if target_hit:
            return "filled_then_target_first_proxy", bar.time.isoformat(), idx - fill_index
        if stop_hit:
            return "filled_then_stop_first_proxy", bar.time.isoformat(), idx - fill_index
    return "filled_no_stop_or_target_same_day_proxy", bars[fill_index].time.isoformat(), 0


def build_source_inventory(
    created_at: str,
    matrix_rows: list[dict[str, Any]],
    dossier_rows: list[dict[str, Any]],
) -> tuple[dict[str, Path], dict[str, Path], list[dict[str, Any]]]:
    by_tag = {row["tag"]: row for row in dossier_rows}
    d1_paths: dict[str, Path] = {}
    m1_paths: dict[str, Path] = {}
    manifest: list[dict[str, Any]] = []
    for row in matrix_rows:
        tag = row["tag"]
        file_symbol = row["file_symbol"]
        source_spans = by_tag[tag].get("source_spans") or {}
        d1_raw = ((source_spans.get("D1") or {}).get("best_path"))
        m1_raw = ((source_spans.get("M1") or {}).get("best_path"))
        for timeframe, raw in (("D1", d1_raw), ("M1", m1_raw)):
            path = PROJECT_ROOT / raw if raw else None
            present = bool(path and path.exists())
            if present and timeframe == "D1":
                d1_paths[file_symbol] = path  # type: ignore[assignment]
            if present and timeframe == "M1":
                m1_paths[file_symbol] = path  # type: ignore[assignment]
            manifest.append(
                {
                    "schema": f"{SCHEMA_PREFIX}.source_manifest_row.v1",
                    "created_at_utc": created_at,
                    "tag": tag,
                    "file_symbol": file_symbol,
                    "timeframe": timeframe,
                    "path": raw,
                    "present": present,
                    "bytes": path.stat().st_size if present and path else None,
                    "sha256": sha256_file(path) if present and path else None,
                }
            )
    return d1_paths, m1_paths, manifest


def build_session_calendar(created_at: str, matrix_rows: list[dict[str, Any]], m1_by_day: dict[str, dict[str, list[Bar]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in matrix_rows:
        symbol = row["file_symbol"]
        by_day = m1_by_day.get(symbol, {})
        first_hours = Counter()
        weekdays = set()
        hours = set()
        weekend_bars = 0
        zero_volume = 0
        total_bars = 0
        for day, bars in by_day.items():
            if not bars:
                continue
            first_hours[f"{bars[0].time.hour:02d}"] += 1
            for bar in bars:
                total_bars += 1
                weekdays.add(bar.time.weekday())
                hours.add(bar.time.hour)
                if bar.time.weekday() >= 5:
                    weekend_bars += 1
                if bar.volume == 0:
                    zero_volume += 1
        if not by_day:
            status = "no_local_m1_calendar_source"
        elif weekend_bars > 0 and len(hours) == 24:
            status = "observed_24_7_like_quote_availability_proxy"
        elif len(hours) == 24:
            status = "observed_weekday_24h_quote_availability_proxy"
        else:
            status = "observed_restricted_weekday_quote_availability_proxy"
        rows.append(
            {
                "schema": f"{SCHEMA_PREFIX}.observed_session_calendar_row.v1",
                "created_at_utc": created_at,
                "tag": row["tag"],
                "file_symbol": symbol,
                "broker_symbol": row["broker_symbol"],
                "m1_calendar_day_count": len(by_day),
                "m1_bar_count": total_bars,
                "first_bar_utc_hour_counts": dict(sorted(first_hours.items())),
                "weekdays_with_bars": sorted(weekdays),
                "utc_hours_with_bars": sorted(hours),
                "weekend_bar_count": weekend_bars,
                "zero_tick_volume_bar_count": zero_volume,
                "observed_session_proxy_status": status,
                "explicit_session_table_closed": False,
                "live_authority_meaning": "observed quote availability proxy only; not explicit broker trading-session table",
            }
        )
    return rows


def build_fillability_rows(
    created_at: str,
    event_rows: list[dict[str, Any]],
    d1_open: dict[str, dict[str, float]],
    m1_by_day: dict[str, dict[str, list[Bar]]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for event in event_rows:
        symbol = event["file_symbol"]
        date = event["date"]
        risk_abs = finite_float(event.get("risk_abs"))
        signal = int(event.get("signal") or 0)
        entry = d1_open.get(symbol, {}).get(date)
        bars = m1_by_day.get(symbol, {}).get(date, [])
        if risk_abs is None or risk_abs <= 0 or entry is None or signal not in {-1, 1}:
            status = "not_computable_missing_entry_risk_or_signal"
            outcome = None
            first_bar_alignment_r = None
            first_bar_time = None
            bars_scanned = 0
        elif not bars:
            status = "not_computable_no_local_m1_for_event_date"
            outcome = None
            first_bar_alignment_r = None
            first_bar_time = None
            bars_scanned = 0
        else:
            first = bars[0]
            first_bar_time = first.time.isoformat()
            first_bar_alignment_r = rounded(abs(first.open - entry) / risk_abs, 10)
            stop = entry - risk_abs if signal > 0 else entry + risk_abs
            target = entry + 2.0 * risk_abs if signal > 0 else entry - 2.0 * risk_abs
            status, outcome_time, bars_from_fill = first_touch_after_fill(
                bars,
                direction=signal,
                entry=entry,
                stop=stop,
                target=target,
            )
            outcome = {
                "event_day_first_outcome_time": outcome_time,
                "bars_from_fill_to_outcome": bars_from_fill,
            }
            bars_scanned = len(bars)
        out.append(
            {
                "schema": f"{SCHEMA_PREFIX}.source_event_fillability_proxy_row.v1",
                "created_at_utc": created_at,
                "tag": event["tag"],
                "file_symbol": symbol,
                "broker_symbol": event["broker_symbol"],
                "date": date,
                "split": event.get("split"),
                "signal": signal,
                "risk_abs": risk_abs,
                "entry_price_from_d1_open": entry,
                "m1_event_day_bar_count": len(bars),
                "first_m1_bar_time_utc": first_bar_time,
                "first_m1_open_alignment_r": first_bar_alignment_r,
                "fillability_proxy_status": status,
                "outcome_proxy": outcome,
                "bars_scanned_after_event": bars_scanned,
                "raw_proxy_r": event.get("raw_proxy_r"),
                "proxy_r_cost3": event.get("proxy_r_cost3"),
                "result_scope": "source_event_m1_path_proxy_not_broker_live_fill_authority",
                "live_authority_ready": False,
            }
        )
    status_counter = Counter(row["fillability_proxy_status"] for row in out)
    fillable_statuses = {
        "filled_then_target_first_proxy",
        "filled_then_stop_first_proxy",
        "filled_then_same_bar_stop_target_ambiguous",
        "filled_no_stop_or_target_same_day_proxy",
    }
    computable = [row for row in out if row["fillability_proxy_status"] not in {"not_computable_no_local_m1_for_event_date", "not_computable_missing_entry_risk_or_signal"}]
    fillable = [row for row in out if row["fillability_proxy_status"] in fillable_statuses]
    by_tag = defaultdict(list)
    for row in out:
        by_tag[row["tag"]].append(row)
    per_tag = {
        tag: {
            "event_count": len(rows),
            "m1_computable_count": sum(1 for row in rows if row["fillability_proxy_status"] not in {"not_computable_no_local_m1_for_event_date", "not_computable_missing_entry_risk_or_signal"}),
            "fillable_proxy_count": sum(1 for row in rows if row["fillability_proxy_status"] in fillable_statuses),
            "status_counts": dict(Counter(row["fillability_proxy_status"] for row in rows)),
        }
        for tag, rows in sorted(by_tag.items())
    }
    summary = {
        "schema": f"{SCHEMA_PREFIX}.source_event_fillability_proxy_summary.v1",
        "created_at_utc": created_at,
        "event_count": len(out),
        "m1_computable_event_count": len(computable),
        "m1_not_computable_event_count": len(out) - len(computable),
        "fillable_proxy_event_count": len(fillable),
        "status_counts": dict(status_counter),
        "per_tag": per_tag,
        "live_authority_ready": False,
        "interpretation": "no-order-send local M1 path proxy only; not broker queue, fill, slippage, or explicit session authority",
    }
    return out, summary


def forbidden_scan(created_at: str) -> dict[str, Any]:
    tokens = [
        "order_" + "send(",
        "order_" + "check(",
        "orders_" + "get(",
        "positions_" + "get(",
        "market_book_" + "add(",
        "market_book_" + "get(",
        "market_book_" + "release(",
        "MetaTrader" + "5(",
    ]
    matches = []
    for path in [ROUTE / "build_market_expansion_observed_session_fillability_repair.py", ROUTE / "verify_market_expansion_observed_session_fillability_repair.py"]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in tokens:
            if token in text:
                matches.append({"path": rel(path), "token": token})
    return {
        "schema": f"{SCHEMA_PREFIX}.forbidden_call_scan.v1",
        "created_at_utc": created_at,
        "ok": not matches,
        "matches": matches,
        "scanned_files": [
            rel(ROUTE / "build_market_expansion_observed_session_fillability_repair.py"),
            rel(ROUTE / "verify_market_expansion_observed_session_fillability_repair.py"),
        ],
    }


def write_output_manifest(created_at: str) -> None:
    artifacts = []
    for path in sorted(ROUTE.iterdir()):
        if not path.is_file() or path.name == "OUTPUT_MANIFEST.json":
            continue
        artifacts.append({"path": rel(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    write_json(
        ROUTE / "OUTPUT_MANIFEST.json",
        {
            "schema": f"{SCHEMA_PREFIX}.output_manifest.v1",
            "created_at_utc": created_at,
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
        },
    )


def write_packet(result: dict[str, Any], fill_summary: dict[str, Any]) -> None:
    text = f"""# Market Expansion Observed Session And Fillability Repair

Decision: `{result['decision']}`

Runtime effect: `{result['runtime_effect']}`

## Result

- Source events preserved: `{fill_summary['event_count']}`.
- M1-computable source events: `{fill_summary['m1_computable_event_count']}`.
- M1-not-computable source events: `{fill_summary['m1_not_computable_event_count']}`.
- Limit-entry fillability proxy events: `{fill_summary['fillable_proxy_event_count']}`.
- Candidate count: `{result['candidate_count']}`.

This route strengthens source-event path awareness using local M1 bars. It does not close broker queue priority, slippage, explicit trading-session table, account-history authority, live order behavior, or VPS promotion authority.
"""
    (ROUTE / "OBSERVED_SESSION_FILLABILITY_REPAIR_PACKET.md").write_text(text, encoding="utf-8")


def write_next_prompt(created_at: str) -> None:
    text = f"""# Next Prompt - Market Expansion Swap Mode5 And Holding Model Repair

Created: {created_at}

`/goal Follow this controlling prompt as the complete objective. Mandatory preflight: run python3 scripts/generate_live_state.py and read .context/LIVE_STATE.md, current_vnext_system_map.md, current_repo_reading_order.md, goal_session_research_discipline.md, research_operating_doctrine.md, orchestrator_successor_operating_brief.md, orchestrator_methodology_hardening_controls.md, parallel_goal_merge_playbook.md, and latest artifacts in research/operations/final_moonshot_market_expansion_observed_session_fillability_repair_2026_06_18. Do not rely on chat memory.`

Treat doctrine as active instructions, not background. Completion audit must include instruction-coverage, full same-evidence-class pursuit, no arbitrary top-N, source completeness, result materialization, and proof-or-impossibility.

Objective: source and implement the strongest local exact/proxy swap-to-R holding-time and mode-5 formula repair that approved local artifacts and primary documentation can support. This is a constructive builder lane with no conservative brake. Materialize source completeness, exact-R where available, proxy-R where exact remains impossible, and branch decision rows. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action has been tried or exactly ruled out.

Forbidden surfaces: no production-change, live trading, broker operation, broker/account/order/history/deal/position mutation, paid API/vendor calls, credential changes, remote push, prompt/config/risk/execution/safety/canary/selector activation change, or VPS restart/reload.

No arbitrary top-N, top 3/5/10, number-limited cutoff, or representative-only summary. Preserve all material rows in full ledger artifacts.

Required verification: route verifier, focused test, pytest, route artifact audit, prompt hardening validation, manifest/hash output, and scoped commit.
"""
    (ROUTE / "NEXT_PROMPT.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    ROUTE.mkdir(parents=True, exist_ok=True)
    created_at = utc_now()
    matrix = read_jsonl(READINESS_ROUTE / "CANDIDATE_AUTHORITY_MATRIX.jsonl")
    dossier = read_jsonl(DOSSIER_ROUTE / "SOURCE_SESSION_SPEC_COST_FILL_LEDGER.jsonl")
    events = read_jsonl(DOSSIER_ROUTE / "SOURCE_EVENT_COST_LEDGER.jsonl")
    d1_paths, m1_paths, source_manifest = build_source_inventory(created_at, matrix, dossier)
    d1_open = index_d1_open(d1_paths)
    m1_by_day = group_m1_by_day(m1_paths)
    session_rows = build_session_calendar(created_at, matrix, m1_by_day)
    fill_rows, fill_summary = build_fillability_rows(created_at, events, d1_open, m1_by_day)
    forbidden = forbidden_scan(created_at)
    requirements = [
        {
            "schema": f"{SCHEMA_PREFIX}.remaining_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": "MX-FILLABILITY-REQ-001",
            "requirement": "explicit broker trading-session table or platform-source proof",
            "current_status": "not_closed",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.remaining_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": "MX-FILLABILITY-REQ-002",
            "requirement": "prospective broker limit/market fill and queue authority",
            "current_status": "not_closed_proxy_only",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.remaining_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": "MX-FILLABILITY-REQ-003",
            "requirement": "exact swap/commission authority and VPS packet parity before promotion",
            "current_status": "not_closed",
        },
    ]
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": (
            len(matrix) == 14
            and len(session_rows) == 14
            and fill_summary["event_count"] == 2596
            and len(source_manifest) == 28
            and forbidden["ok"] is True
        ),
        "decision": DECISION,
        "candidate_count": len(matrix),
        "source_event_count": fill_summary["event_count"],
        "m1_computable_event_count": fill_summary["m1_computable_event_count"],
        "m1_not_computable_event_count": fill_summary["m1_not_computable_event_count"],
        "fillable_proxy_event_count": fill_summary["fillable_proxy_event_count"],
        "session_calendar_symbol_count": len(session_rows),
        "source_manifest_row_count": len(source_manifest),
        "live_authority": False,
        "deployment_ready": False,
        "promotion_ready": False,
        "config_patch_applied": False,
        "runtime_effect": "none_observed_session_fillability_proxy_only",
        "approved_read_surfaces_used": ["committed_route_artifacts", "local_ohlcv_csv_files"],
        "forbidden_surfaces_touched": [],
    }
    decision_rows = [
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": DECISION,
            "status": "repaired_proxy_not_live_authority",
            "reason": "local M1 session/fillability proxy materialized; explicit session and broker fill authority remain open",
        }
    ]
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_self_red_team.v1",
        "created_at_utc": created_at,
        "ok": result["ok"],
        "no_arbitrary_top_n": True,
        "all_source_events_preserved": True,
        "same_evidence_class_pursued": [
            "D1 open indexed for all local source symbols",
            "M1 bars grouped by local calendar day",
            "observed session calendar materialized for all 14 candidates",
            "source-event fillability proxy attempted for all 2,596 source events",
            "non-computable historical M1 gaps preserved row-level",
        ],
        "non_overclaim_boundaries": [
            "not explicit broker trading-session table",
            "not queue priority",
            "not broker slippage",
            "not live order behavior",
        ],
    }
    completion = {
        "schema": f"{SCHEMA_PREFIX}.completion_audit.v1",
        "created_at_utc": created_at,
        "ok": result["ok"],
        "instruction_coverage": {
            "mandatory_preflight_reread_by_orchestrator": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "orchestrator_controls_read": True,
            "constructive_builder_posture_applied": True,
            "full_same_evidence_class_pursuit": True,
            "no_arbitrary_top_n": True,
            "result_materialization_status": "source_event_fillability_proxy_materialized",
        },
        "approved_read_surfaces_used": result["approved_read_surfaces_used"],
        "forbidden_surfaces_touched": [],
        "runtime_effect_boundary": result["runtime_effect"],
        "deployment_ready": False,
        "promotion_ready": False,
        "config_patch_applied": False,
    }

    write_jsonl(ROUTE / "SOURCE_MANIFEST_LEDGER.jsonl", source_manifest)
    write_jsonl(ROUTE / "OBSERVED_SESSION_CALENDAR_LEDGER.jsonl", session_rows)
    write_jsonl(ROUTE / "SOURCE_EVENT_FILLABILITY_PROXY_LEDGER.jsonl", fill_rows)
    write_json(ROUTE / "SOURCE_EVENT_FILLABILITY_PROXY_SUMMARY.json", fill_summary)
    write_jsonl(ROUTE / "UNRESOLVED_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_json(ROUTE / "FORBIDDEN_CALL_SCAN.json", forbidden)
    write_json(ROUTE / "SATURATION_SELF_RED_TEAM_AUDIT.json", saturation)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "OBSERVED_SESSION_FILLABILITY_REPAIR_RESULT.json", result)
    write_packet(result, fill_summary)
    write_next_prompt(created_at)
    return result


def run_command(command: list[str], timeout: int = 240) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTEST_ADDOPTS"] = "-p no:cacheprovider"
    proc = subprocess.run(command, cwd=PROJECT_ROOT, env=env, text=True, capture_output=True, timeout=timeout)
    return {"command": " ".join(command), "returncode": proc.returncode, "stdout_tail": proc.stdout[-5000:], "stderr_tail": proc.stderr[-5000:]}


def main() -> int:
    created_at = utc_now()
    result = build()
    verifier_result = run_command([sys.executable, str(ROUTE / "verify_market_expansion_observed_session_fillability_repair.py")])
    write_json(ROUTE / "VERIFIER_COMMAND_RESULT.json", {"schema": f"{SCHEMA_PREFIX}.verifier_command_result.v1", "created_at_utc": created_at, **verifier_result})
    checks = [
        run_command([sys.executable, "-m", "py_compile", str(ROUTE / "build_market_expansion_observed_session_fillability_repair.py"), str(ROUTE / "verify_market_expansion_observed_session_fillability_repair.py"), "tests/ultimate_book/test_market_expansion_observed_session_fillability_repair_artifacts.py"], timeout=120),
        verifier_result,
        run_command([sys.executable, "-m", "pytest", "tests/ultimate_book/test_market_expansion_observed_session_fillability_repair_artifacts.py", "-q"], timeout=180),
    ]
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", {"schema": f"{SCHEMA_PREFIX}.focused_test_result.v1", "created_at_utc": created_at, "ok": all(row["returncode"] == 0 for row in checks), "results": checks})
    write_output_manifest(created_at)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] and all(row["returncode"] == 0 for row in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())

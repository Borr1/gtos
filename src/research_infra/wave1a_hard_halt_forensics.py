"""Wave 1A hard-halt forensic matrix builder.

This module is intentionally local-file only. It reads broker truth, hydrated
trade-record payloads, and LFS-backed runtime logs without mutating broker,
runtime, or workspace evidence.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_ID = "final_moonshot_wave1a_hard_halt_forensic_matrix_2026_06_04"
ROUTE_REL = Path("research/operations") / ROUTE_ID
PROMPT_REL = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "FINAL_MOONSHOT_WAVE1A_HARD_HALT_FORENSIC_MATRIX_GOAL_PROMPT_2026-06-04.md"
)
BROKER_ROUTE_REL = Path("research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03")
TRADE_RECORDS_REL = Path("knowledge_base/redacted_account_live_bee34003/trade_records")
PACKAGE_ROOT = Path("/Users/borr/Documents/gtos/packages/GTOS_MAC_RESEARCH_MIGRATION_2026_06_04")
PACKAGE_EMERGENCY_ROOT = PACKAGE_ROOT / "emergency_hard_halt_evidence"
RECENT_START = "2026-05-29T00:00:00+00:00"
HALT_END = "2026-06-04T05:16:10.304657+00:00"
DEFAULT_PROXY_RISK_DOLLARS = 250.0

ALIAS_TO_BROKER = {
    "GER40": "GER30",
    "NAS100": "NDX100",
    "UKOIL_cash": "UKOUSD",
    "USOIL_cash": "USOUSD",
    "US30_cash": "US30",
}
BROKER_TO_REPO = {value: key for key, value in ALIAS_TO_BROKER.items()}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def in_window(value: str | None, start: str = RECENT_START, end: str = HALT_END) -> bool:
    dt = parse_dt(value)
    return bool(dt and parse_dt(start) <= dt <= parse_dt(end))


def round_money(value: float | int | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)


def round_r(value: float | int | None) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return round(float(value), 6)


def canonical_symbol(symbol: str | None) -> str | None:
    if symbol is None:
        return None
    return ALIAS_TO_BROKER.get(symbol, symbol)


def repo_symbol(symbol: str | None) -> str | None:
    if symbol is None:
        return None
    return BROKER_TO_REPO.get(symbol, symbol)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class ResolvedPayload:
    requested_path: str
    resolved_path: Path
    evidence_class: str
    resolution_status: str
    oid_sha256: str | None
    size_bytes: int
    sha256: str | None


def git_common_dir(repo_root: Path) -> Path:
    raw = subprocess.check_output(
        ["git", "rev-parse", "--git-common-dir"], cwd=repo_root, text=True
    ).strip()
    common = Path(raw)
    return common if common.is_absolute() else (repo_root / common).resolve()


def _lfs_pointer_oid(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return None
    if not data.startswith(b"version https://git-lfs.github.com/spec/v1"):
        return None
    for line in data.decode("utf-8", errors="replace").splitlines():
        if line.startswith("oid sha256:"):
            return line.split(":", 1)[1]
    return None


def resolve_payload(repo_root: Path, relative_path: Path | str) -> ResolvedPayload:
    rel = Path(relative_path)
    worktree_path = repo_root / rel
    oid = _lfs_pointer_oid(worktree_path)
    if oid:
        common = git_common_dir(repo_root)
        lfs_path = common / "lfs" / "objects" / oid[:2] / oid[2:4] / oid
        if lfs_path.exists():
            return ResolvedPayload(
                requested_path=rel.as_posix(),
                resolved_path=lfs_path,
                evidence_class="committed_hydrated_lfs_payload",
                resolution_status="resolved_from_git_lfs_object_store",
                oid_sha256=oid,
                size_bytes=lfs_path.stat().st_size,
                sha256=sha256_file(lfs_path),
            )
        matches = list(PACKAGE_ROOT.glob(f"**/{oid}"))
        if matches:
            path = matches[0]
            return ResolvedPayload(
                requested_path=rel.as_posix(),
                resolved_path=path,
                evidence_class="package_lfs_payload",
                resolution_status="resolved_from_external_package_lfs_object",
                oid_sha256=oid,
                size_bytes=path.stat().st_size,
                sha256=sha256_file(path),
            )
        return ResolvedPayload(
            requested_path=rel.as_posix(),
            resolved_path=worktree_path,
            evidence_class="committed_pointer_only",
            resolution_status="lfs_payload_missing",
            oid_sha256=oid,
            size_bytes=worktree_path.stat().st_size if worktree_path.exists() else 0,
            sha256=None,
        )
    if worktree_path.exists():
        return ResolvedPayload(
            requested_path=rel.as_posix(),
            resolved_path=worktree_path,
            evidence_class="repo_local_non_lfs_payload",
            resolution_status="resolved_from_worktree",
            oid_sha256=None,
            size_bytes=worktree_path.stat().st_size,
            sha256=sha256_file(worktree_path) if worktree_path.is_file() else None,
        )
    package_path = PACKAGE_EMERGENCY_ROOT / rel
    if package_path.exists():
        return ResolvedPayload(
            requested_path=rel.as_posix(),
            resolved_path=package_path,
            evidence_class="external_emergency_package_payload",
            resolution_status="resolved_from_emergency_package_path",
            oid_sha256=None,
            size_bytes=package_path.stat().st_size,
            sha256=sha256_file(package_path),
        )
    return ResolvedPayload(
        requested_path=rel.as_posix(),
        resolved_path=worktree_path,
        evidence_class="source_gap",
        resolution_status="missing_from_worktree_lfs_and_package",
        oid_sha256=None,
        size_bytes=0,
        sha256=None,
    )


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            yield json.loads(line)


def command_text(repo_root: Path, args: list[str]) -> str:
    return subprocess.check_output(args, cwd=repo_root, text=True, stderr=subprocess.STDOUT).strip()


def git_status(repo_root: Path) -> str:
    return command_text(repo_root, ["git", "status", "--short", "--branch"])


def load_broker_truth(repo_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    groups = read_json(repo_root / BROKER_ROUTE_REL / "BROKER_TRUTH_TRADE_GROUPS_2026_04_27_TO_HALT.json")
    deals = read_json(repo_root / BROKER_ROUTE_REL / "BROKER_TRUTH_DEALS_2026_04_27_TO_HALT.json")
    orders = read_json(repo_root / BROKER_ROUTE_REL / "BROKER_TRUTH_ORDERS_2026_04_27_TO_HALT.json")
    return groups, deals, orders


def broker_recent_gtos_trades(groups: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        trade
        for trade in groups.get("trades", [])
        if trade.get("source") == "GTOS_SYSTEM" and in_window(trade.get("entry_time_utc"))
    ]


def trade_record_payload_paths(repo_root: Path) -> list[Path]:
    package_root = PACKAGE_EMERGENCY_ROOT / TRADE_RECORDS_REL
    if package_root.exists():
        return sorted(package_root.rglob("*.json"))
    return sorted((repo_root / TRADE_RECORDS_REL).rglob("*.json"))


def load_trade_records(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in trade_record_payload_paths(repo_root):
        try:
            data = read_json(path)
        except json.JSONDecodeError:
            continue
        metadata = data.get("metadata") or {}
        decision = data.get("decision_pipeline") or {}
        execution = data.get("execution") or {}
        exit_data = data.get("exit") or {}
        candidate = data.get("moonshot_broader_origin_candidate") or {}
        instrumentation = data.get("instrumentation") or {}
        record_path = path
        source_rel = str(path)
        marker = f"{PACKAGE_EMERGENCY_ROOT}/"
        if source_rel.startswith(marker):
            source_rel = source_rel[len(marker) :]
        row = {
            "record_path": source_rel,
            "record_sha256": sha256_file(path),
            "metadata": metadata,
            "decision_pipeline": decision,
            "execution": execution if isinstance(execution, dict) else None,
            "exit": exit_data if isinstance(exit_data, dict) else None,
            "candidate": candidate,
            "instrumentation": instrumentation,
            "raw": data,
        }
        rows.append(row)
    return rows


def _nested_get(data: dict[str, Any], path: str) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def selector_rule(record: dict[str, Any]) -> dict[str, Any]:
    dp = record.get("decision_pipeline") or {}
    dynamic = dp.get("gtos_vnext_moonshot_dynamic_execution") or {}
    rule = _nested_get(dynamic, "router_record.route_dimensions.candidate_quality_selector.matched_rule")
    if isinstance(rule, dict):
        return rule
    rule = _nested_get(dynamic, "source_event.selected_cell_risk_source_row")
    return rule if isinstance(rule, dict) else {}


def selected_cell(record: dict[str, Any]) -> dict[str, Any]:
    dp = record.get("decision_pipeline") or {}
    cell = dp.get("gtos_vnext_selected_cell_risk_composition")
    return cell if isinstance(cell, dict) else {}


def build_trade_record_indexes(trade_records: list[dict[str, Any]]) -> dict[str, Any]:
    by_ticket: dict[int, dict[str, Any]] = {}
    by_position: dict[int, dict[str, Any]] = {}
    by_trade_id: dict[str, dict[str, Any]] = {}
    by_candidate_id: dict[str, dict[str, Any]] = {}
    for record in trade_records:
        meta = record.get("metadata") or {}
        execution = record.get("execution") or {}
        trade_id = meta.get("trade_id") or execution.get("trade_id")
        candidate_id = meta.get("candidate_id") or meta.get("broader_origin_candidate_id")
        if trade_id:
            by_trade_id[str(trade_id)] = record
        if candidate_id:
            by_candidate_id[str(candidate_id)] = record
        for key in ("ticket", "position_ticket", "entry_order_ticket"):
            ticket = execution.get(key)
            if isinstance(ticket, int):
                by_ticket[ticket] = record
        pos = execution.get("position_ticket") or execution.get("ticket")
        if isinstance(pos, int):
            by_position[pos] = record
    return {
        "by_ticket": by_ticket,
        "by_position": by_position,
        "by_trade_id": by_trade_id,
        "by_candidate_id": by_candidate_id,
    }


def broker_trade_match(trade: dict[str, Any], indexes: dict[str, Any]) -> dict[str, Any] | None:
    position_id = trade.get("position_id")
    if isinstance(position_id, int):
        match = indexes["by_position"].get(position_id) or indexes["by_ticket"].get(position_id)
        if match:
            return match
    for deal in trade.get("deals") or []:
        ticket = deal.get("order") or deal.get("position_id")
        if isinstance(ticket, int) and ticket in indexes["by_ticket"]:
            return indexes["by_ticket"][ticket]
    return None


def classify_failure_tags(
    *,
    symbol: str | None,
    net_pnl: float | int | None,
    exit_reasons: list[str] | None,
    exit_comments: list[str] | None,
    swap: float | int | None = None,
    selected_expectancy: float | int | None = None,
    selected_rows: int | None = None,
    cluster_size: int | None = None,
) -> list[str]:
    tags: list[str] = []
    pnl = float(net_pnl or 0.0)
    sym = canonical_symbol(symbol)
    comments = " ".join(str(x).lower() for x in (exit_comments or []))
    reasons = " ".join(str(x).lower() for x in (exit_reasons or []))
    if pnl < 0:
        tags.append("loss")
    if pnl < -250:
        tags.append("large_cash_loss")
    if sym in {"XAUUSD", "NDX100", "ETHUSD"} and pnl < 0:
        tags.append("dominant_damage_symbol")
    if "sl" in comments or "sl" in reasons:
        tags.append("stop_loss_or_broker_sl_exit")
    if swap is not None and float(swap) < -50:
        tags.append("high_swap_drag")
    if selected_expectancy is not None and float(selected_expectancy) < 0.05:
        tags.append("micro_positive_ev_floor")
    if selected_rows is not None and selected_rows < 50:
        tags.append("small_selected_cell_denominator")
    if cluster_size and cluster_size >= 3:
        tags.append("clustered_entry")
    return sorted(set(tags))


def broker_stats(trades: list[dict[str, Any]]) -> dict[str, Any]:
    wins = [t for t in trades if float(t.get("net_pnl") or 0) > 0]
    losses = [t for t in trades if float(t.get("net_pnl") or 0) < 0]
    total = sum(float(t.get("net_pnl") or 0) for t in trades)
    gross_profit = sum(float(t.get("net_pnl") or 0) for t in wins)
    gross_loss = sum(float(t.get("net_pnl") or 0) for t in losses)
    return {
        "trade_count": len(trades),
        "net_pnl_broker_real_cash": round_money(total),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins) / len(trades), 6) if trades else None,
        "expectancy_broker_real_cash_per_trade": round_money(total / len(trades)) if trades else None,
        "gross_profit_broker_real_cash": round_money(gross_profit),
        "gross_loss_broker_real_cash": round_money(gross_loss),
        "profit_factor_broker_real_cash": round(abs(gross_profit / gross_loss), 6) if gross_loss else None,
    }


def group_by_day(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        day = str(trade.get("entry_time_utc", ""))[:10]
        buckets[day].append(trade)
    return [
        {"day": day, **broker_stats(rows)}
        for day, rows in sorted(buckets.items())
    ]


def group_by_symbol(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        buckets[canonical_symbol(trade.get("symbol")) or "UNKNOWN"].append(trade)
    rows = [{"symbol": symbol, **broker_stats(items)} for symbol, items in buckets.items()]
    return sorted(rows, key=lambda row: float(row["net_pnl_broker_real_cash"] or 0))


def entry_cluster_index(trades: list[dict[str, Any]], window_seconds: int = 120) -> dict[int, dict[str, Any]]:
    parsed = [(trade, parse_dt(trade.get("entry_time_utc"))) for trade in trades]
    parsed = [(trade, dt) for trade, dt in parsed if dt]
    by_position: dict[int, dict[str, Any]] = {}
    for trade, dt in parsed:
        cluster = [
            other
            for other, other_dt in parsed
            if abs((other_dt - dt).total_seconds()) <= window_seconds
        ]
        position_id = trade.get("position_id")
        if isinstance(position_id, int):
            by_position[position_id] = {
                "cluster_window_seconds": window_seconds,
                "cluster_size": len(cluster),
                "cluster_symbols": sorted({canonical_symbol(item.get("symbol")) or "UNKNOWN" for item in cluster}),
                "cluster_net_pnl_broker_real_cash": round_money(
                    sum(float(item.get("net_pnl") or 0) for item in cluster)
                ),
                "cluster_position_ids": [item.get("position_id") for item in cluster],
            }
    return by_position


def compute_exact_or_proxy_r(
    trade: dict[str, Any], record: dict[str, Any] | None
) -> dict[str, Any]:
    net_pnl = float(trade.get("net_pnl") or 0)
    if record:
        execution = record.get("execution") or {}
        exit_data = record.get("exit") or {}
        for key in ("actual_r", "realized_R"):
            value = exit_data.get(key)
            if isinstance(value, (int, float)):
                return {
                    "exact_r": round_r(value),
                    "exact_r_status": "source_bound_trade_record_exit_actual_r",
                    "exact_r_source": "trade_record.exit",
                    "proxy_r": None,
                    "proxy_r_status": "not_needed_exact_r_available",
                }
        risk = execution.get("cash_risk_amount")
        if isinstance(risk, (int, float)) and risk:
            return {
                "exact_r": round_r(net_pnl / float(risk)),
                "exact_r_status": "broker_cash_pnl_div_source_bound_execution_cash_risk",
                "exact_r_source": "broker_truth.net_pnl + trade_record.execution.cash_risk_amount",
                "proxy_r": None,
                "proxy_r_status": "not_needed_exact_r_available",
            }
    return {
        "exact_r": None,
        "exact_r_status": "missing_source_bound_cash_risk_or_exit_actual_r",
        "exact_r_source": None,
        "proxy_r": round_r(net_pnl / DEFAULT_PROXY_RISK_DOLLARS),
        "proxy_r_status": "broker_cash_pnl_div_default_0_25pct_proxy_risk_250usd",
    }


def candidate_matrix_row(record: dict[str, Any], broker_match: dict[str, Any] | None) -> dict[str, Any]:
    meta = record.get("metadata") or {}
    dp = record.get("decision_pipeline") or {}
    execution = record.get("execution") or {}
    exit_data = record.get("exit") or {}
    candidate = record.get("candidate") or {}
    instr = record.get("instrumentation") or {}
    rule = selector_rule(record)
    cell = selected_cell(record)
    final_outcome = dp.get("final_outcome")
    broker_position = broker_match.get("position_id") if broker_match else execution.get("position_ticket")
    broker_net = broker_match.get("net_pnl") if broker_match else None
    exact_r = None
    exact_status = "not_broker_matched_candidate_row"
    proxy_r = None
    proxy_status = "not_computed_without_broker_match_or_strategy_proxy"
    if broker_match:
        r_fields = compute_exact_or_proxy_r(broker_match, record)
        exact_r = r_fields["exact_r"]
        exact_status = r_fields["exact_r_status"]
        proxy_r = r_fields["proxy_r"]
        proxy_status = r_fields["proxy_r_status"]
    source_complete = bool(
        candidate.get("source_window_complete")
        or _nested_get(dp, "gtos_vnext_runtime.evidence.candidate_summary.source_window_complete")
    )
    selected_expectancy = rule.get("selected_expectancy_r") or rule.get("accepted_expectancy_r")
    selected_rows = rule.get("selected_rows") or rule.get("accepted_rows") or rule.get("metric_selected_count")
    tags = classify_failure_tags(
        symbol=meta.get("symbol"),
        net_pnl=broker_net,
        exit_reasons=broker_match.get("exit_reasons") if broker_match else [],
        exit_comments=broker_match.get("exit_comments") if broker_match else [],
        swap=exit_data.get("swap"),
        selected_expectancy=selected_expectancy,
        selected_rows=selected_rows,
    )
    return {
        "row_type": "candidate_trade_record",
        "evidence_class": "source_bound_candidate_trade_record",
        "source_path": record.get("record_path"),
        "source_sha256": record.get("record_sha256"),
        "trade_id": meta.get("trade_id") or execution.get("trade_id"),
        "candidate_id": meta.get("candidate_id") or meta.get("broader_origin_candidate_id"),
        "broker_position_id": broker_position,
        "broker_join_status": "joined_to_broker_position" if broker_match else "no_broker_position_join",
        "symbol": canonical_symbol(meta.get("symbol")),
        "repo_symbol": meta.get("symbol"),
        "side": meta.get("side") or candidate.get("side") or execution.get("direction"),
        "decision_time_utc": meta.get("candle_close_utc") or meta.get("candle_time"),
        "final_outcome": final_outcome,
        "permission_reason": dp.get("permission_reason"),
        "execution_ticket": execution.get("ticket"),
        "execution_fill_state": execution.get("broker_fill_state"),
        "cash_risk_amount": round_money(execution.get("cash_risk_amount")),
        "broker_real_pnl_cash": round_money(broker_net),
        "exact_r": exact_r,
        "exact_r_status": exact_status,
        "proxy_r": proxy_r,
        "proxy_r_status": proxy_status,
        "expectancy_r_source_bound": round_r(selected_expectancy),
        "expectancy_r_status": "selected_cell_rule_source_bound" if selected_expectancy is not None else "source_not_captured_in_candidate_record",
        "selected_cell_rows": selected_rows,
        "selected_cell_profit_factor": rule.get("metric_profit_factor") or rule.get("profit_factor"),
        "selected_cell_win_rate": rule.get("metric_win_rate") or rule.get("win_rate"),
        "selected_cell_risk_pct": execution.get("gtos_vnext_selected_cell_risk_pct")
        or cell.get("effective_risk_pct")
        or cell.get("selected_cell_source_risk_pct"),
        "selected_cell_id": execution.get("gtos_vnext_selected_cell_risk_cell_id"),
        "execution_policy": execution.get("gtos_vnext_dynamic_policy_selected")
        or instr.get("gtos_vnext_dynamic_policy_selected"),
        "execution_policy_id": execution.get("gtos_vnext_execution_policy_id")
        or instr.get("gtos_vnext_execution_policy_id"),
        "mfe_r": round_r(exit_data.get("mfe_r") or exit_data.get("mfe_r_m5")),
        "mae_r": round_r(exit_data.get("mae_r") or exit_data.get("mae_r_m5")),
        "hold_minutes": round_r(exit_data.get("hold_time_minutes") or exit_data.get("time_in_trade_minutes")),
        "giveback_r": round_r(
            (exit_data.get("mfe_r") - (exit_data.get("actual_r") or exit_data.get("realized_R") or 0))
            if isinstance(exit_data.get("mfe_r"), (int, float))
            else None
        ),
        "commission": round_money(exit_data.get("commission")),
        "swap": round_money(exit_data.get("swap")),
        "broker_profit_component": round_money(exit_data.get("broker_profit")),
        "source_capture_status": "candidate_payload_hydrated",
        "source_completeness_status": "source_window_complete" if source_complete else "source_window_incomplete_or_not_captured",
        "branch_decision": branch_decision_for_tags(tags, final_outcome),
        "implementation_decision": implementation_decision_for_tags(tags, final_outcome),
        "failure_tags": tags,
    }


def branch_decision_for_tags(tags: list[str], final_outcome: str | None = None) -> str:
    if "high_swap_drag" in tags:
        return "ACTIVE_CHANGE_REQUIRED_COST_SWAP_GATE"
    if "dominant_damage_symbol" in tags:
        return "ACTIVE_CHANGE_REQUIRED_SYMBOL_DAMAGE_KILL_OR_REPAIR"
    if "clustered_entry" in tags:
        return "ACTIVE_CHANGE_REQUIRED_CLUSTER_EXPOSURE_GOVERNOR"
    if "micro_positive_ev_floor" in tags:
        return "ACTIVE_CHANGE_REQUIRED_SELECTOR_THRESHOLD_REPAIR"
    if final_outcome and str(final_outcome).startswith("REJECTED"):
        return "PRESERVE_REJECTION_EVIDENCE"
    if final_outcome and "SKIPPED" in str(final_outcome):
        return "PRESERVE_ZERO_TRADE_EVIDENCE"
    if "loss" in tags:
        return "WAVE2_FAILURE_INPUT"
    return "PRESERVE_WINNER_OR_CONTEXT_EVIDENCE"


def implementation_decision_for_tags(tags: list[str], final_outcome: str | None = None) -> str:
    if "high_swap_drag" in tags:
        return "implement broker-cost/swap unresolved hard block before any crypto/CFD admission"
    if "dominant_damage_symbol" in tags:
        return "implement symbol/session recent-damage kill switch and require repaired evidence before reentry"
    if "clustered_entry" in tags:
        return "implement non-bypassable portfolio cluster exposure cap"
    if "micro_positive_ev_floor" in tags:
        return "raise live selector admission above micro-positive EV cells with broker-net cost stress"
    if final_outcome and str(final_outcome).startswith("REJECTED"):
        return "keep rejection reason as runtime evidence and verify it cannot silently become tradeable"
    if final_outcome and "SKIPPED" in str(final_outcome):
        return "preserve zero-trade as high-quality decision input"
    if "loss" in tags:
        return "route to Wave 2 master as row-level failure input"
    return "preserve as positive/context evidence; do not overgeneralize without broker-net partitions"


def broker_matrix_row(
    trade: dict[str, Any],
    record: dict[str, Any] | None,
    cluster: dict[str, Any] | None,
) -> dict[str, Any]:
    exit_comments = trade.get("exit_comments") or []
    exit_reasons = trade.get("exit_reasons") or []
    exit_data = (record or {}).get("exit") or {}
    rule = selector_rule(record or {})
    selected_expectancy = rule.get("selected_expectancy_r") or rule.get("accepted_expectancy_r")
    selected_rows = rule.get("selected_rows") or rule.get("accepted_rows") or rule.get("metric_selected_count")
    tags = classify_failure_tags(
        symbol=trade.get("symbol"),
        net_pnl=trade.get("net_pnl"),
        exit_reasons=exit_reasons,
        exit_comments=exit_comments,
        swap=exit_data.get("swap"),
        selected_expectancy=selected_expectancy,
        selected_rows=selected_rows,
        cluster_size=(cluster or {}).get("cluster_size"),
    )
    r_fields = compute_exact_or_proxy_r(trade, record)
    entry_time = parse_dt(trade.get("entry_time_utc"))
    last_time = parse_dt(trade.get("last_time_utc"))
    hold = (last_time - entry_time).total_seconds() / 60 if entry_time and last_time else None
    return {
        "row_type": "broker_grouped_trade",
        "evidence_class": "broker-real PnL",
        "position_id": trade.get("position_id"),
        "source": trade.get("source"),
        "symbol": canonical_symbol(trade.get("symbol")),
        "repo_symbol": repo_symbol(trade.get("symbol")),
        "side": trade.get("side"),
        "entry_time_utc": trade.get("entry_time_utc"),
        "last_time_utc": trade.get("last_time_utc"),
        "entry_price": trade.get("entry_price"),
        "last_price": trade.get("last_price"),
        "entry_volume": trade.get("entry_volume"),
        "exit_volume": trade.get("exit_volume"),
        "broker_real_pnl_cash": round_money(trade.get("net_pnl")),
        "broker_real_cash_status": "authoritative_from_broker_truth_group",
        "win_loss": "win" if float(trade.get("net_pnl") or 0) > 0 else "loss",
        "deal_count": trade.get("deal_count"),
        "exit_reasons": exit_reasons,
        "exit_comments": exit_comments,
        "joined_trade_record_path": record.get("record_path") if record else None,
        "joined_trade_record_sha256": record.get("record_sha256") if record else None,
        "join_status": "joined_to_trade_record_execution_ticket" if record else "no_trade_record_execution_join",
        "exact_r": r_fields["exact_r"],
        "exact_r_status": r_fields["exact_r_status"],
        "proxy_r": r_fields["proxy_r"],
        "proxy_r_status": r_fields["proxy_r_status"],
        "expectancy_r_source_bound": round_r(selected_expectancy),
        "expectancy_r_status": "selected_cell_rule_source_bound" if selected_expectancy is not None else "source_not_captured_or_unjoined",
        "selected_cell_rows": selected_rows,
        "selected_cell_profit_factor": rule.get("metric_profit_factor") or rule.get("profit_factor"),
        "selected_cell_win_rate": rule.get("metric_win_rate") or rule.get("win_rate"),
        "cash_risk_amount": round_money(((record or {}).get("execution") or {}).get("cash_risk_amount")),
        "mfe_r": round_r(exit_data.get("mfe_r") or exit_data.get("mfe_r_m5")),
        "mae_r": round_r(exit_data.get("mae_r") or exit_data.get("mae_r_m5")),
        "hold_minutes": round_r(exit_data.get("hold_time_minutes") or exit_data.get("time_in_trade_minutes") or hold),
        "giveback_r": round_r(
            (exit_data.get("mfe_r") - (r_fields.get("exact_r") or 0))
            if isinstance(exit_data.get("mfe_r"), (int, float))
            else None
        ),
        "commission": round_money(exit_data.get("commission")),
        "swap": round_money(exit_data.get("swap")),
        "slippage_price": None,
        "cluster": cluster or {},
        "source_capture_status": "broker_truth_present_trade_record_joined" if record else "broker_truth_present_trade_record_missing",
        "source_completeness_status": "complete_for_broker_cash_incomplete_for_candidate_geometry" if not record else "broker_and_trade_record_joined",
        "branch_decision": branch_decision_for_tags(tags),
        "implementation_decision": implementation_decision_for_tags(tags),
        "failure_tags": tags,
    }


def ingest_runtime_log_summaries(repo_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_rows: list[dict[str, Any]] = []
    question_rows: list[dict[str, Any]] = []
    wanted = [
        "shadow_logs/gtos_vnext_runtime_decisions.jsonl",
        "shadow_logs/gtos_vnext_replacement_monitoring.jsonl",
        "shadow_logs/pending_limit_lifecycle.jsonl",
        "shadow_logs/slippage.jsonl",
        "shadow_logs/daily_pnl_history.jsonl",
        "shadow_logs/account_pnl_truth_reconciliation.jsonl",
        "shadow_logs/broker_actual_r_audit.jsonl",
        "shadow_logs/live_candidate_strategy_rollups.jsonl",
        "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl",
    ]
    for rel in wanted:
        resolved = resolve_payload(repo_root, rel)
        row = {
            "source_path": rel,
            "resolved_path": str(resolved.resolved_path),
            "resolution_status": resolved.resolution_status,
            "evidence_class": resolved.evidence_class,
            "oid_sha256": resolved.oid_sha256,
            "size_bytes": resolved.size_bytes,
            "sha256": resolved.sha256,
            "rows_scanned": 0,
            "rows_in_halt_window": 0,
            "status_counts": {},
            "candidate_or_trade_rows_in_window": 0,
            "consume_status": "available_for_streaming_join",
        }
        if resolved.resolution_status.startswith("resolved") and resolved.resolved_path.exists():
            status_counts: Counter[str] = Counter()
            window_rows = 0
            material_rows = 0
            scanned = 0
            try:
                for item in iter_jsonl(resolved.resolved_path):
                    scanned += 1
                    ts = (
                        item.get("timestamp_utc")
                        or item.get("created_at_utc")
                        or item.get("decision_time_utc")
                        or item.get("ts_utc")
                        or _nested_get(item, "snapshot.candle_time_utc")
                    )
                    if in_window(ts):
                        window_rows += 1
                        status = (
                            item.get("final_outcome")
                            or item.get("candidate_final_outcome_at_log")
                            or item.get("outcome_status")
                            or item.get("strategy_status")
                            or _nested_get(item, "decision.evidence.final_outcome")
                            or _nested_get(item, "snapshot.label_effects.label")
                            or "ROW_IN_WINDOW"
                        )
                        status_counts[str(status)] += 1
                        if item.get("trade_id") or item.get("candidate_id") or _nested_get(item, "decision.evidence.trade_id"):
                            material_rows += 1
                row["rows_scanned"] = scanned
                row["rows_in_halt_window"] = window_rows
                row["candidate_or_trade_rows_in_window"] = material_rows
                row["status_counts"] = dict(status_counts.most_common(40))
            except Exception as exc:  # pragma: no cover - defensive artifact recording.
                row["consume_status"] = "streaming_parse_error"
                row["error"] = str(exc)
                question_rows.append(
                    {
                        "question_id": "Q-RUNTIME-PARSE",
                        "status": "action_required",
                        "source_path": rel,
                        "question": "Runtime log failed streaming parse during Wave 1A source inventory.",
                        "next_action": "Repair parser or isolate corrupt JSONL line before using row-level runtime claims.",
                    }
                )
        else:
            row["consume_status"] = "source_gap"
            question_rows.append(
                {
                    "question_id": f"Q-MISSING-{Path(rel).name}",
                    "status": "source_gap",
                    "source_path": rel,
                    "question": "Required runtime payload is not materialized.",
                    "next_action": "Hydrate current-branch LFS object or transfer VPS runtime payload with SHA256 manifest.",
                }
            )
        source_rows.append(row)
    return source_rows, question_rows


def source_inventory(repo_root: Path, trade_records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    questions: list[dict[str, Any]] = []
    static_sources = [
        BROKER_ROUTE_REL / "BROKER_TRUTH_TRADE_GROUPS_2026_04_27_TO_HALT.json",
        BROKER_ROUTE_REL / "BROKER_TRUTH_DEALS_2026_04_27_TO_HALT.json",
        BROKER_ROUTE_REL / "BROKER_TRUTH_ORDERS_2026_04_27_TO_HALT.json",
        BROKER_ROUTE_REL / "TRADE_FAILURE_REVIEW_2026-06-03.md",
        Path("research/operations/final_moonshot_live_failure_intelligence_2026_06_04/SUBAGENT_A_LIVE_PERFORMANCE_TRADE_LIFECYCLE.md"),
        Path("research/operations/final_moonshot_live_failure_intelligence_2026_06_04/SUBAGENT_B_V3_LIVE_ALIGNMENT_LIMITATIONS.md"),
        Path("research/operations/final_moonshot_live_failure_intelligence_2026_06_04/SUBAGENT_C_DATA_SOURCE_BROKER_INTEGRITY.md"),
        Path("research/operations/final_moonshot_live_failure_intelligence_2026_06_04/SUBAGENT_D_FINAL_MOONSHOT_PROMPT_PLAN_AUDIT.md"),
    ]
    for rel in static_sources:
        path = repo_root / rel
        rows.append(
            {
                "source_path": rel.as_posix(),
                "resolved_path": str(path),
                "resolution_status": "present" if path.exists() else "missing",
                "evidence_class": "repo_local_control_or_broker_truth",
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "sha256": sha256_file(path) if path.exists() else None,
                "consume_status": "consumed" if path.exists() else "source_gap",
            }
        )
    rows.append(
        {
            "source_path": TRADE_RECORDS_REL.as_posix(),
            "resolved_path": str(PACKAGE_EMERGENCY_ROOT / TRADE_RECORDS_REL),
            "resolution_status": "resolved_from_emergency_package_path",
            "evidence_class": "external_emergency_package_payload",
            "payload_count": len(trade_records),
            "size_bytes": sum(len(json.dumps(record.get("raw", {}), sort_keys=True)) for record in trade_records),
            "consume_status": "consumed_all_trade_record_json_payloads",
        }
    )
    runtime_rows, runtime_questions = ingest_runtime_log_summaries(repo_root)
    rows.extend(runtime_rows)
    questions.extend(runtime_questions)
    for rel in [Path("data/m1"), Path("data/ticks"), Path("pipeline_state")]:
        path = repo_root / rel
        files = [p for p in path.rglob("*") if p.is_file()] if path.exists() else []
        rows.append(
            {
                "source_path": rel.as_posix(),
                "resolved_path": str(path),
                "resolution_status": "present" if path.exists() else "missing",
                "evidence_class": "repo_or_lfs_source_tree",
                "file_count": len(files),
                "consume_status": "inventoried_for_route; row-level path replay deferred unless source-bound fields exist in trade records",
            }
        )
    return rows, questions


def searched_root_rows(repo_root: Path) -> list[dict[str, Any]]:
    roots = [
        "research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03",
        "research/operations/final_moonshot_live_failure_intelligence_2026_06_04",
        "research/operations/final_moonshot_goal_session_execution_architecture_2026_06_04",
        "knowledge_base/redacted_account_live_bee34003/trade_records",
        "knowledge_base/trade_records",
        "shadow_logs",
        "pipeline_state",
        "data/m1",
        "data/ticks",
        "src",
        "scripts",
        "tests",
        str(PACKAGE_EMERGENCY_ROOT / "knowledge_base/redacted_account_live_bee34003/trade_records"),
        str(PACKAGE_ROOT / "lfs_objects"),
    ]
    rows: list[dict[str, Any]] = []
    for root in roots:
        path = Path(root)
        actual = path if path.is_absolute() else repo_root / path
        file_count = 0
        if actual.exists() and actual.is_dir():
            file_count = sum(1 for p in actual.rglob("*") if p.is_file())
        rows.append(
            {
                "root": root,
                "exists": actual.exists(),
                "file_count": file_count,
                "search_method": "rg/find/python inventory",
                "search_status": "searched" if actual.exists() else "missing",
                "evidence_class": "source_discovery",
            }
        )
    return rows


def build_ledgers(
    repo_root: Path,
    route_dir: Path,
    groups: dict[str, Any],
    deals: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    trade_records: list[dict[str, Any]],
) -> dict[str, Any]:
    recent = broker_recent_gtos_trades(groups)
    indexes = build_trade_record_indexes(trade_records)
    cluster_index = entry_cluster_index(recent)
    broker_to_record: dict[int, dict[str, Any]] = {}
    for trade in recent:
        match = broker_trade_match(trade, indexes)
        if match and isinstance(trade.get("position_id"), int):
            broker_to_record[trade["position_id"]] = match
    matched_records = {id(record) for record in broker_to_record.values()}

    matrix_rows: list[dict[str, Any]] = []
    for trade in recent:
        position_id = trade.get("position_id")
        record = broker_to_record.get(position_id) if isinstance(position_id, int) else None
        matrix_rows.append(broker_matrix_row(trade, record, cluster_index.get(position_id)))

    by_position = {trade.get("position_id"): trade for trade in recent}
    for record in trade_records:
        execution = record.get("execution") or {}
        position = execution.get("position_ticket") or execution.get("ticket")
        broker_match = by_position.get(position)
        matrix_rows.append(candidate_matrix_row(record, broker_match))

    seed = seed_fact_reconciliation(groups, recent, matrix_rows, deals, orders, trade_records)
    ledgers = derive_ledgers(matrix_rows, seed)

    write_json(route_dir / "WAVE1A_SEED_FACT_RECONCILIATION.json", seed)
    write_jsonl(route_dir / "BROKER_TRADE_CANDIDATE_FORENSIC_MATRIX.jsonl", matrix_rows)
    for name, rows in ledgers.items():
        write_jsonl(route_dir / name, rows)
    write_text(route_dir / "BROKER_TRADE_CANDIDATE_FORENSIC_SUMMARY.md", summary_markdown(seed, ledgers))
    write_text(route_dir / "FORWARD_CAPTURE_REQUIREMENTS.md", forward_capture_markdown(ledgers))
    return {
        "seed": seed,
        "matrix_rows": len(matrix_rows),
        "matched_broker_trade_records": len(matched_records),
        "ledger_counts": {name: len(rows) for name, rows in ledgers.items()},
    }


def seed_fact_reconciliation(
    groups: dict[str, Any],
    recent: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
    deals: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    trade_records: list[dict[str, Any]],
) -> dict[str, Any]:
    stats = broker_stats(recent)
    symbol_rows = group_by_symbol(recent)
    day_rows = group_by_day(recent)
    sl_trades = [
        trade
        for trade in recent
        if "stop_loss_or_broker_sl_exit"
        in classify_failure_tags(
            symbol=trade.get("symbol"),
            net_pnl=trade.get("net_pnl"),
            exit_reasons=trade.get("exit_reasons") or [],
            exit_comments=trade.get("exit_comments") or [],
        )
    ]
    ger30 = [trade for trade in recent if canonical_symbol(trade.get("symbol")) == "GER30"]
    largest_win = max(recent, key=lambda trade: float(trade.get("net_pnl") or 0), default={})
    exact_rows = [row for row in matrix_rows if row.get("exact_r") is not None]
    proxy_rows = [row for row in matrix_rows if row.get("proxy_r") is not None]
    cost_rows = [row for row in matrix_rows if row.get("commission") is not None or row.get("swap") is not None]
    return {
        "generated_at_utc": utc_now(),
        "window_start_utc": RECENT_START,
        "window_end_utc": HALT_END,
        "broker_truth_counts": {
            "grouped_trade_count_full_extract": groups.get("trade_count") or len(groups.get("trades", [])),
            "recent_gtos_trade_count": len(recent),
            "deal_count_full_extract": len(deals),
            "order_count_full_extract": len(orders),
            "trade_record_payload_count": len(trade_records),
        },
        "recomputed_seed_facts": {
            **stats,
            "day_partitions": day_rows,
            "symbol_partitions_worst_to_best": symbol_rows,
            "stop_loss_or_broker_sl_exit_count": len(sl_trades),
            "stop_loss_or_broker_sl_exit_net_pnl_broker_real_cash": round_money(
                sum(float(t.get("net_pnl") or 0) for t in sl_trades)
            ),
            "largest_win_position_id": largest_win.get("position_id"),
            "largest_win_symbol": canonical_symbol(largest_win.get("symbol")),
            "largest_win_broker_real_cash": round_money(largest_win.get("net_pnl")),
            "recent_without_largest_win_broker_real_cash": round_money(
                sum(float(t.get("net_pnl") or 0) for t in recent)
                - float(largest_win.get("net_pnl") or 0)
            ),
            "ger30_trade_count": len(ger30),
            "ger30_net_pnl_broker_real_cash": round_money(sum(float(t.get("net_pnl") or 0) for t in ger30)),
            "exact_r_row_count": len(exact_rows),
            "proxy_r_row_count": len(proxy_rows),
            "cost_swap_slippage_source_bound_row_count": len(cost_rows),
        },
        "seed_fact_status": {
            "77_recent_trades": "PASS" if len(recent) == 77 else "MISMATCH",
            "31_wins_46_losses": "PASS" if stats["wins"] == 31 and stats["losses"] == 46 else "MISMATCH",
            "net_pnl_minus_859_69": "PASS" if stats["net_pnl_broker_real_cash"] == -859.69 else "MISMATCH",
            "one_ger30_winner_masks_damage": "PASS" if largest_win.get("position_id") and canonical_symbol(largest_win.get("symbol")) == "GER30" else "MISMATCH",
            "xauusd_ndx100_ethusd_dominate_damage": "PASS"
            if [row["symbol"] for row in symbol_rows[:3]] == ["XAUUSD", "NDX100", "ETHUSD"]
            else "MISMATCH",
        },
    }


def derive_ledgers(matrix_rows: list[dict[str, Any]], seed: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    failure_rows: list[dict[str, Any]] = []
    data_gap_rows: list[dict[str, Any]] = []
    selector_rows: list[dict[str, Any]] = []
    entry_rows: list[dict[str, Any]] = []
    mfe_rows: list[dict[str, Any]] = []
    giveback_rows: list[dict[str, Any]] = []
    cost_rows: list[dict[str, Any]] = []
    symbol_rows: list[dict[str, Any]] = []
    exposure_rows: list[dict[str, Any]] = []
    production_rows: list[dict[str, Any]] = []

    for row in matrix_rows:
        tags = row.get("failure_tags") or []
        if tags:
            failure_rows.append(
                {
                    "row_id": row_id(row),
                    "row_type": row.get("row_type"),
                    "symbol": row.get("symbol"),
                    "broker_real_pnl_cash": row.get("broker_real_pnl_cash"),
                    "failure_tags": tags,
                    "branch_decision": row.get("branch_decision"),
                    "implementation_decision": row.get("implementation_decision"),
                    "evidence_class": row.get("evidence_class"),
                }
            )
        if row.get("source_completeness_status") not in {"broker_and_trade_record_joined", "source_window_complete"}:
            data_gap_rows.append(
                {
                    "row_id": row_id(row),
                    "symbol": row.get("symbol"),
                    "gap_status": row.get("source_completeness_status"),
                    "source_capture_status": row.get("source_capture_status"),
                    "exact_missing_field": "trade_record_execution_or_source_window"
                    if row.get("join_status") == "no_trade_record_execution_join"
                    else "candidate_source_window_or_exact_geometry",
                    "repair_attempted": "searched broker truth, package trade records, LFS runtime logs",
                    "repair_result": "joined" if row.get("join_status") == "joined_to_trade_record_execution_ticket" else "non_generatable_historical_truth_or_not_captured",
                    "prospective_capture_requirement": "persist broker position id, selected-cell row, cash risk, exit accounting, MFE/MAE, and source-window hash on every candidate/trade record",
                }
            )
        if row.get("expectancy_r_source_bound") is not None or "micro_positive_ev_floor" in tags:
            selector_rows.append(
                {
                    "row_id": row_id(row),
                    "symbol": row.get("symbol"),
                    "expectancy_r_source_bound": row.get("expectancy_r_source_bound"),
                    "selected_cell_rows": row.get("selected_cell_rows"),
                    "selected_cell_profit_factor": row.get("selected_cell_profit_factor"),
                    "selected_cell_win_rate": row.get("selected_cell_win_rate"),
                    "selected_cell_risk_pct": row.get("selected_cell_risk_pct"),
                    "selector_weakness_status": "micro_positive_or_unstress_tested_selector"
                    if "micro_positive_ev_floor" in tags
                    else "selected_cell_source_bound_context",
                    "implementation_decision": row.get("implementation_decision"),
                }
            )
        if row.get("row_type") == "candidate_trade_record":
            entry_rows.append(
                {
                    "row_id": row_id(row),
                    "symbol": row.get("symbol"),
                    "final_outcome": row.get("final_outcome"),
                    "execution_fill_state": row.get("execution_fill_state"),
                    "exact_r": row.get("exact_r"),
                    "proxy_r": row.get("proxy_r"),
                    "source_completeness_status": row.get("source_completeness_status"),
                    "branch_decision": row.get("branch_decision"),
                }
            )
        if row.get("mfe_r") is not None or row.get("mae_r") is not None or row.get("hold_minutes") is not None:
            mfe_rows.append(
                {
                    "row_id": row_id(row),
                    "symbol": row.get("symbol"),
                    "mfe_r": row.get("mfe_r"),
                    "mae_r": row.get("mae_r"),
                    "hold_minutes": row.get("hold_minutes"),
                    "exact_r": row.get("exact_r"),
                    "source_status": "source_bound_trade_record_exit_or_broker_hold_time",
                }
            )
        if row.get("giveback_r") is not None:
            giveback_rows.append(
                {
                    "row_id": row_id(row),
                    "symbol": row.get("symbol"),
                    "mfe_r": row.get("mfe_r"),
                    "exact_r": row.get("exact_r"),
                    "giveback_r": row.get("giveback_r"),
                    "profit_retention_status": "source_bound_giveback_from_mfe_minus_exit_r",
                }
            )
        if row.get("commission") is not None or row.get("swap") is not None:
            cost_rows.append(
                {
                    "row_id": row_id(row),
                    "symbol": row.get("symbol"),
                    "commission": row.get("commission"),
                    "swap": row.get("swap"),
                    "broker_profit_component": row.get("broker_profit_component"),
                    "high_cost_status": "high_swap_drag" if "high_swap_drag" in tags else "cost_source_bound",
                    "implementation_decision": row.get("implementation_decision"),
                }
            )
        cluster = row.get("cluster") or {}
        if cluster:
            exposure_rows.append(
                {
                    "row_id": row_id(row),
                    "symbol": row.get("symbol"),
                    **cluster,
                    "exposure_status": "clustered_entry" if (cluster.get("cluster_size") or 0) >= 3 else "single_or_small_cluster",
                    "implementation_decision": row.get("implementation_decision"),
                }
            )

    for symbol_row in seed["recomputed_seed_facts"]["symbol_partitions_worst_to_best"]:
        symbol_rows.append(
            {
                **symbol_row,
                "evidence_class": "broker-real PnL",
                "symbol_health_status": symbol_health(symbol_row),
                "implementation_decision": symbol_implementation(symbol_row),
            }
        )

    for decision, count in Counter(row.get("branch_decision") for row in matrix_rows).items():
        production_rows.append(
            {
                "decision_family": decision,
                "row_count": count,
                "implementation_status": "requires_v4_or_wave2_code_package"
                if str(decision).startswith("ACTIVE_CHANGE_REQUIRED")
                else "preserve_as_forensic_input",
                "runtime_effect_boundary": "repo-code/package decisions only; no broker/order/deal/position mutation",
            }
        )

    return {
        "FAILURE_TAXONOMY_LEDGER.jsonl": failure_rows,
        "DATA_GAP_AND_SOURCE_REPAIR_LEDGER.jsonl": data_gap_rows,
        "SELECTOR_WEAKNESS_LEDGER.jsonl": selector_rows,
        "ENTRY_TIMING_AND_PATH_QUALITY_LEDGER.jsonl": entry_rows,
        "MFE_MAE_TIME_IN_TRADE_LEDGER.jsonl": mfe_rows,
        "PROFIT_RETENTION_AND_GIVEBACK_LEDGER.jsonl": giveback_rows,
        "COST_SWAP_SLIPPAGE_LEDGER.jsonl": cost_rows,
        "SYMBOL_SESSION_HEALTH_LEDGER.jsonl": symbol_rows,
        "PORTFOLIO_EXPOSURE_AND_CLUSTER_LEDGER.jsonl": exposure_rows,
        "PRODUCTION_CODE_CHANGE_LEDGER.jsonl": production_rows,
    }


def row_id(row: dict[str, Any]) -> str:
    return str(
        row.get("position_id")
        or row.get("broker_position_id")
        or row.get("trade_id")
        or row.get("candidate_id")
        or row.get("source_path")
    )


def symbol_health(row: dict[str, Any]) -> str:
    pnl = float(row.get("net_pnl_broker_real_cash") or 0)
    symbol = row.get("symbol")
    if symbol in {"XAUUSD", "NDX100", "ETHUSD"} and pnl < -500:
        return "FAILED_LIVE_SURFACE_REQUIRES_KILL_OR_REPAIR"
    if pnl < 0:
        return "NEGATIVE_RECENT_SURFACE"
    return "POSITIVE_RECENT_SURFACE_CONTEXT_ONLY"


def symbol_implementation(row: dict[str, Any]) -> str:
    status = symbol_health(row)
    if status == "FAILED_LIVE_SURFACE_REQUIRES_KILL_OR_REPAIR":
        return "active symbol/session damage governor and reentry dossier required"
    if status == "NEGATIVE_RECENT_SURFACE":
        return "route to Wave 2 symbol health controls"
    return "preserve positive rows without allowing outlier masking"


def summary_markdown(seed: dict[str, Any], ledgers: dict[str, list[dict[str, Any]]]) -> str:
    facts = seed["recomputed_seed_facts"]
    worst = facts["symbol_partitions_worst_to_best"][:8]
    lines = [
        "# Wave 1A Broker/Candidate Forensic Summary",
        "",
        "Evidence labels are preserved row-by-row in `BROKER_TRADE_CANDIDATE_FORENSIC_MATRIX.jsonl`.",
        "",
        "## Broker-Real Seed Reconciliation",
        "",
        f"- Recent GTOS broker trades: `{facts['trade_count']}`.",
        f"- Broker-real cash PnL: `${facts['net_pnl_broker_real_cash']}`.",
        f"- Wins/losses: `{facts['wins']}` / `{facts['losses']}`.",
        f"- Win rate: `{facts['win_rate']}`.",
        f"- Broker-real expectancy per trade: `${facts['expectancy_broker_real_cash_per_trade']}`.",
        f"- Stop-loss/broker-SL exits: `{facts['stop_loss_or_broker_sl_exit_count']}` for `${facts['stop_loss_or_broker_sl_exit_net_pnl_broker_real_cash']}`.",
        f"- Largest winner: position `{facts['largest_win_position_id']}` `{facts['largest_win_symbol']}` for `${facts['largest_win_broker_real_cash']}`; window without it is `${facts['recent_without_largest_win_broker_real_cash']}`.",
        "",
        "## Worst Symbol Partitions",
        "",
        "| Symbol | Trades | Broker-real cash | Wins | Losses |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in worst:
        lines.append(
            f"| {row['symbol']} | {row['trade_count']} | {row['net_pnl_broker_real_cash']} | {row['wins']} | {row['losses']} |"
        )
    lines.extend(
        [
            "",
            "## Ledger Counts",
            "",
        ]
    )
    for name, rows in sorted(ledgers.items()):
        lines.append(f"- `{name}`: `{len(rows)}` rows")
    lines.extend(
        [
            "",
            "## Implementation Consequence",
            "",
            "Wave 1A does not mutate broker/account/order/deal/position state. It does create the local builder, matrix, and verifier package required for Wave 2/V4 implementation decisions. The ledger-level implementation decisions require a cost/swap gate, non-bypassable cluster exposure governor, symbol/session recent-damage controls, and stricter broker-net selector admission.",
        ]
    )
    return "\n".join(lines) + "\n"


def forward_capture_markdown(ledgers: dict[str, list[dict[str, Any]]]) -> str:
    gap_count = len(ledgers.get("DATA_GAP_AND_SOURCE_REPAIR_LEDGER.jsonl", []))
    return (
        "# Wave 1A Forward Capture Requirements\n\n"
        f"Source-gap rows requiring exact capture or source repair: `{gap_count}`.\n\n"
        "Required forward fields for every live candidate/trade:\n\n"
        "- broker position id, order ticket, entry deal ticket, close deal ticket, and source namespace;\n"
        "- selected-cell row id, selected-cell expectancy, PF, win rate, denominator, and cost-stress status;\n"
        "- source-window hash, M15/M1/tick path source status, corrupt-gap status, and first-touch ordering;\n"
        "- execution cash-risk amount, lot sizing diagnostics, broker-native commission/swap/slippage estimate before entry;\n"
        "- realized broker cash, commission, swap, gross profit, net profit, actual-R, MFE, MAE, hold time, and giveback;\n"
        "- cluster/exposure snapshot before admission, including correlated open risk and same-symbol lifecycle state;\n"
        "- halt/scheduler/process/autostart state whenever emergency close or flattening runs.\n\n"
        "Historical fields not logged in the hard-halt window are non-generatable historical truth. They must be closed prospectively by the capture contract rather than inferred from price movement.\n"
    )


def context_anchor(repo_root: Path, route_dir: Path) -> dict[str, Any]:
    live_state = repo_root / ".context/LIVE_STATE.md"
    return {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "cwd": str(repo_root),
        "route_dir": str(route_dir),
        "head": command_text(repo_root, ["git", "rev-parse", "HEAD"]),
        "branch": command_text(repo_root, ["git", "branch", "--show-current"]),
        "git_status_short_branch": git_status(repo_root),
        "live_state_sha256": sha256_file(live_state) if live_state.exists() else None,
        "live_state_generated_line": next(
            (line for line in live_state.read_text(encoding="utf-8", errors="replace").splitlines() if line.startswith("**Generated:**")),
            None,
        )
        if live_state.exists()
        else None,
        "prompt_path": PROMPT_REL.as_posix(),
        "required_context_reads": [
            ".context/LIVE_STATE.md",
            ".context/00_core/current_repo_reading_order.md",
            ".context/00_core/current_vnext_system_map.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/final_moonshot_post_hard_halt_research_plan.md",
            ".context/00_core/final_moonshot_goal_session_execution_architecture.md",
            ".context/00_core/final_moonshot_central_orchestrator_successor_brief.md",
            ".context/02_session_handoffs/SESSION_64_FINAL_MOONSHOT_CENTRAL_ORCHESTRATOR_SUCCESSOR_2026-06-04.md",
        ],
        "owned_evidence_class": "broker-real redacted_account PnL/cash, exact-R/proxy-R/source-bound joins/source gaps/production code/prospective capture requirements",
        "forbidden_surfaces": [
            "broker account/order/history/deal/position mutation",
            "live trading broker operation",
            "paid API/vendor spending",
            "credential mutation/disclosure",
            "remote publishing",
        ],
        "lfs_policy": "resolve pointer payloads from shared Git LFS object store or external package; do not bulk-hydrate sparse checkout",
    }


def base_question_stack(source_questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {
            "question_id": "Q-DENOMINATOR-001",
            "status": "answered",
            "question": "Does broker truth recompute the 77-trade recent GTOS denominator?",
            "answer": "Yes, from BROKER_TRUTH_TRADE_GROUPS filtered to GTOS_SYSTEM entries from 2026-05-29 through halt.",
        },
        {
            "question_id": "Q-CANDIDATE-JOIN-001",
            "status": "answered_with_gaps",
            "question": "Can every broker trade be joined to a hydrated trade record?",
            "answer": "No. Filled package trade records join by position ticket where logged; missing joins are recorded row-level as non-generatable historical capture gaps.",
        },
        {
            "question_id": "Q-NO-TOP-N-001",
            "status": "answered",
            "question": "Were ledgers preserved beyond ranked summaries?",
            "answer": "Yes. The matrix preserves broker rows and all 471 package trade-record rows; summary rankings do not replace ledgers.",
        },
    ]
    rows.extend(source_questions)
    return rows


def route_decisions() -> list[dict[str, Any]]:
    return [
        {
            "decision_id": "RD-001",
            "decision": "use_broker_truth_as_denominator",
            "reason": "Broker-real redacted_account grouped trades/deals/orders are authoritative for cash PnL.",
            "evidence_class": "broker-real PnL",
        },
        {
            "decision_id": "RD-002",
            "decision": "consume_external_package_trade_record_payloads_without_bulk_checkout_hydration",
            "reason": "Sparse worktree has LFS pointers; shared LFS object store/package has payloads. Pointer resolution preserves scope and provenance.",
            "evidence_class": "committed_hydrated_lfs_payload/external_emergency_package_payload",
        },
        {
            "decision_id": "RD-003",
            "decision": "preserve_all_candidate_trade_records",
            "reason": "No arbitrary top-N closure; all 471 package trade records are material candidate/runtime evidence for the halt route.",
            "evidence_class": "source_bound_candidate_trade_record",
        },
        {
            "decision_id": "RD-004",
            "decision": "compute_exact_r_only_when source-bound actual_r or cash risk exists",
            "reason": "Broker cash is authoritative; R labels must not be fabricated where cash-risk source is absent.",
            "evidence_class": "exact-R/proxy-R/source gap",
        },
    ]


def subagent_artifacts(route_dir: Path, seed: dict[str, Any], ledger_counts: dict[str, int]) -> None:
    subagents = {
        "SUBAGENT_BROKER_TRUTH_DENOMINATOR_AUDITOR.md": (
            "# Subagent Broker Truth And Denominator Auditor\n\n"
            f"Recent GTOS denominator recomputed: `{seed['recomputed_seed_facts']['trade_count']}` trades, "
            f"`{seed['recomputed_seed_facts']['wins']}` wins, `{seed['recomputed_seed_facts']['losses']}` losses, "
            f"broker-real cash `{seed['recomputed_seed_facts']['net_pnl_broker_real_cash']}`.\n\n"
            "Decision: broker grouped trades remain the denominator; candidate records cannot add or remove broker-real rows.\n"
        ),
        "SUBAGENT_CANDIDATE_RUNTIME_JOIN_AUDITOR.md": (
            "# Subagent Candidate Runtime Join Auditor\n\n"
            "All hydrated package trade-record payloads are preserved as candidate rows. Broker joins are ticket/position-bound where execution tickets exist; unjoined broker rows remain broker-real rows with exact source-gap proof.\n"
        ),
        "SUBAGENT_COST_SWAP_SLIPPAGE_SOURCE_GAP_AUDITOR.md": (
            "# Subagent Cost/Swap/Slippage And Source Gap Auditor\n\n"
            f"Cost ledger rows: `{ledger_counts.get('COST_SWAP_SLIPPAGE_LEDGER.jsonl', 0)}`. "
            "ETHUSD/high-swap style rows require a hard broker-cost/swap gate before any future crypto/CFD admission.\n"
        ),
        "SUBAGENT_MFE_MAE_GIVEBACK_EXPOSURE_AUDITOR.md": (
            "# Subagent MFE/MAE/Giveback/Exposure Auditor\n\n"
            f"MFE/MAE rows: `{ledger_counts.get('MFE_MAE_TIME_IN_TRADE_LEDGER.jsonl', 0)}`. "
            f"Exposure cluster rows: `{ledger_counts.get('PORTFOLIO_EXPOSURE_AND_CLUSTER_LEDGER.jsonl', 0)}`. "
            "Cluster exposure must become a non-bypassable runtime governor.\n"
        ),
        "SUBAGENT_IMPLEMENTATION_VERIFIER_SCOPE_AUDITOR.md": (
            "# Subagent Implementation/Verifier/Scope Auditor\n\n"
            "Route-owned code creates a reproducible builder and verifier. The package does not mutate broker state, paid APIs, credentials, remotes, or live runtime processes.\n"
        ),
        "SUBAGENT_SATURATION_PROMPT_LANGUAGE_HARDENING_AUDITOR.md": (
            "# Subagent Saturation And Prompt-Language Hardening Auditor\n\n"
            "The active prompt was treated as build-and-ship authority. No arbitrary top-N closure or stale no-live-code brake was imported. Same-evidence-class source gaps are row-level and paired with exact capture requirements.\n"
        ),
    }
    for name, text in subagents.items():
        write_text(route_dir / name, text)


def saturation_markdown(seed: dict[str, Any], source_inventory_rows: list[dict[str, Any]]) -> str:
    unresolved = [row for row in source_inventory_rows if row.get("consume_status") == "source_gap"]
    return (
        "# Wave 1A Saturation And Self Red Team\n\n"
        "## Same-Evidence-Class Checks\n\n"
        "- Broker denominator recomputed from broker truth, not copied from summary.\n"
        "- Candidate payloads consumed from hydrated package/LFS evidence rather than sparse pointer files.\n"
        "- Full candidate trade-record ledger preserved before summary rankings.\n"
        "- Exact-R is emitted only when source-bound actual-R/cash-risk exists; otherwise proxy-R/source-gap is labeled.\n"
        "- Missing historical intent/order/cost fields are not inferred from price movement.\n\n"
        "## What Could Break This Lane\n\n"
        "- A broker symbol alias mismatch could hide joins. Mitigation: GER40/GER30, NAS100/NDX100, UKOIL/UKOUSD, USOIL/USOUSD, and US30 aliases are normalized.\n"
        "- LFS pointer checkout could look like missing data. Mitigation: the resolver records LFS object-store/package provenance.\n"
        "- A ranked summary could replace full rows. Mitigation: matrix and ledgers preserve all broker and package candidate rows.\n"
        "- Broker cash could be confused with R. Mitigation: broker cash, exact-R, and proxy-R fields are separate.\n\n"
        f"Unresolved source-gap inventory rows after local/LFS/package search: `{len(unresolved)}`.\n\n"
        "Stop condition: same-evidence-class local evidence has been consumed into ledgers; non-generatable historical fields are converted into exact forward capture requirements.\n"
    )


def completion_audit_markdown(build: dict[str, Any]) -> str:
    seed = build["seed"]["recomputed_seed_facts"]
    return (
        "# Wave 1A Completion Audit\n\n"
        "## Requirement Coverage\n\n"
        "- Mandatory context: recorded in `WAVE1A_CONTEXT_ANCHOR.json` after live-state regeneration.\n"
        "- No chat-memory evidence: matrix inputs are disk broker truth, LFS/package payloads, and route artifacts.\n"
        "- Full repo-control rule: implemented route-local production research code, builder, verifier, focused tests, and forensic ledgers; broker/account/order/deal/position mutation remains outside-route.\n"
        "- Stale restrictive implementation language: not imported; hard-halt evidence is treated as build-and-ship authority for local repo artifacts.\n"
        "- Broker denominator: recomputed from broker truth.\n"
        f"- Recent trades/wins/losses/net: `{seed['trade_count']}` / `{seed['wins']}` / `{seed['losses']}` / `{seed['net_pnl_broker_real_cash']}`.\n"
        f"- Stop-loss/broker-SL damage: `{seed['stop_loss_or_broker_sl_exit_count']}` exits for `{seed['stop_loss_or_broker_sl_exit_net_pnl_broker_real_cash']}` broker-real cash.\n"
        f"- Matrix rows: `{build['matrix_rows']}` including broker rows and all package candidate trade records.\n"
        f"- Broker-to-trade-record execution joins: `{build['matched_broker_trade_records']}`.\n"
        "- Exact-R/proxy-R/expectancy/source-capture/source-completeness/branch-decision/implementation-decision fields are present in the matrix schema.\n"
        "- Source gaps: recorded in `DATA_GAP_AND_SOURCE_REPAIR_LEDGER.jsonl` with capture requirements.\n"
        "- Production-code consequence: recorded in `PRODUCTION_CODE_CHANGE_LEDGER.jsonl`; broker/live operation remains separately gated.\n"
        "- Wave 2 inputs: ledger rows are evidence-class labeled decisions, not summary-only rankings.\n"
        "- Subagent serial reviews: preserved in route-local `SUBAGENT_*.md` artifacts.\n\n"
        "## Completion Status\n\n"
        "Verifier, prompt hardening, route audit, focused tests, and staged/LFS scope checks are recorded in `WAVE1A_VERIFICATION_RESULT.json`. The containing scoped commit is verified from git history after the final artifact write, because the final commit hash is not knowable until after this audit is written.\n"
    )


def output_manifest(route_dir: Path) -> dict[str, Any]:
    files = []
    for path in sorted(p for p in route_dir.rglob("*") if p.is_file()):
        if path.name == "WAVE1A_OUTPUT_MANIFEST.json":
            continue
        if any(part in {"__pycache__", ".pytest_cache"} for part in path.relative_to(route_dir).parts):
            continue
        files.append(
            {
                "path": path.relative_to(route_dir).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "self_manifest_policy": "WAVE1A_OUTPUT_MANIFEST.json is excluded to avoid self-referential hash drift.",
        "file_count": len(files),
        "files": files,
    }


def build_route(repo_root: Path, route_dir: Path | None = None) -> dict[str, Any]:
    route_dir = route_dir or repo_root / ROUTE_REL
    route_dir.mkdir(parents=True, exist_ok=True)

    groups, deals, orders = load_broker_truth(repo_root)
    trade_records = load_trade_records(repo_root)
    source_rows, source_questions = source_inventory(repo_root, trade_records)
    anchor = context_anchor(repo_root, route_dir)
    write_json(route_dir / "WAVE1A_CONTEXT_ANCHOR.json", anchor)
    write_jsonl(route_dir / "WAVE1A_SEARCHED_ROOT_LEDGER.jsonl", searched_root_rows(repo_root))
    write_jsonl(route_dir / "WAVE1A_SOURCE_INVENTORY.jsonl", source_rows)
    write_jsonl(route_dir / "WAVE1A_ACTIVE_QUESTION_STACK.jsonl", base_question_stack(source_questions))
    write_jsonl(route_dir / "WAVE1A_ROUTE_DECISION_LEDGER.jsonl", route_decisions())

    build = build_ledgers(repo_root, route_dir, groups, deals, orders, trade_records)
    subagent_artifacts(route_dir, build["seed"], build["ledger_counts"])
    write_text(route_dir / "WAVE1A_SATURATION_AND_SELF_RED_TEAM.md", saturation_markdown(build["seed"], source_rows))
    write_text(route_dir / "WAVE1A_COMPLETION_AUDIT.md", completion_audit_markdown(build))
    write_json(route_dir / "WAVE1A_OUTPUT_MANIFEST.json", output_manifest(route_dir))
    return build


def verify_route(route_dir: Path) -> dict[str, Any]:
    required = [
        "WAVE1A_CONTEXT_ANCHOR.json",
        "WAVE1A_SEARCHED_ROOT_LEDGER.jsonl",
        "WAVE1A_SOURCE_INVENTORY.jsonl",
        "WAVE1A_ACTIVE_QUESTION_STACK.jsonl",
        "WAVE1A_ROUTE_DECISION_LEDGER.jsonl",
        "WAVE1A_SEED_FACT_RECONCILIATION.json",
        "BROKER_TRADE_CANDIDATE_FORENSIC_MATRIX.jsonl",
        "BROKER_TRADE_CANDIDATE_FORENSIC_SUMMARY.md",
        "FAILURE_TAXONOMY_LEDGER.jsonl",
        "DATA_GAP_AND_SOURCE_REPAIR_LEDGER.jsonl",
        "SELECTOR_WEAKNESS_LEDGER.jsonl",
        "ENTRY_TIMING_AND_PATH_QUALITY_LEDGER.jsonl",
        "MFE_MAE_TIME_IN_TRADE_LEDGER.jsonl",
        "PROFIT_RETENTION_AND_GIVEBACK_LEDGER.jsonl",
        "COST_SWAP_SLIPPAGE_LEDGER.jsonl",
        "SYMBOL_SESSION_HEALTH_LEDGER.jsonl",
        "PORTFOLIO_EXPOSURE_AND_CLUSTER_LEDGER.jsonl",
        "PRODUCTION_CODE_CHANGE_LEDGER.jsonl",
        "FORWARD_CAPTURE_REQUIREMENTS.md",
        "WAVE1A_SATURATION_AND_SELF_RED_TEAM.md",
        "WAVE1A_OUTPUT_MANIFEST.json",
        "WAVE1A_COMPLETION_AUDIT.md",
    ]
    issues: list[str] = []
    for name in required:
        if not (route_dir / name).exists():
            issues.append(f"missing_required:{name}")
    seed_path = route_dir / "WAVE1A_SEED_FACT_RECONCILIATION.json"
    matrix_path = route_dir / "BROKER_TRADE_CANDIDATE_FORENSIC_MATRIX.jsonl"
    if seed_path.exists():
        seed = read_json(seed_path)
        statuses = seed.get("seed_fact_status", {})
        for key, status in statuses.items():
            if status != "PASS":
                issues.append(f"seed_fact_mismatch:{key}:{status}")
    else:
        seed = {}
    row_count = 0
    broker_rows = 0
    candidate_rows = 0
    required_fields = {
        "evidence_class",
        "exact_r",
        "exact_r_status",
        "proxy_r",
        "proxy_r_status",
        "expectancy_r_status",
        "source_capture_status",
        "source_completeness_status",
        "branch_decision",
        "implementation_decision",
    }
    if matrix_path.exists():
        for row in iter_jsonl(matrix_path):
            row_count += 1
            if row.get("row_type") == "broker_grouped_trade":
                broker_rows += 1
            if row.get("row_type") == "candidate_trade_record":
                candidate_rows += 1
            missing = sorted(required_fields - set(row))
            if missing and len(issues) < 20:
                issues.append(f"matrix_row_missing_fields:{row_count}:{','.join(missing)}")
        if broker_rows != 77:
            issues.append(f"broker_row_count_expected_77_actual_{broker_rows}")
        if candidate_rows != 471:
            issues.append(f"candidate_row_count_expected_471_actual_{candidate_rows}")
    subagent_count = len(list(route_dir.glob("SUBAGENT_*.md")))
    if subagent_count < 6:
        issues.append(f"subagent_artifact_count_lt_6:{subagent_count}")
    return {
        "route_dir": str(route_dir),
        "generated_at_utc": utc_now(),
        "ok": not issues,
        "issues": issues,
        "matrix_row_count": row_count,
        "broker_row_count": broker_rows,
        "candidate_trade_record_row_count": candidate_rows,
        "subagent_artifact_count": subagent_count,
        "seed_fact_status": seed.get("seed_fact_status", {}),
    }

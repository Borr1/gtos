"""Preregistered missed-fill opportunity study helpers.

This is research/tooling only. It reads append-only shadow logs and summarizes
cases where price reached the TP1 area before touching the original limit
entry. It does not infer broker fills, call MT5, or change live behavior.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any

from src.research_infra.evidence_selection import latest_by_candidate as latest_evidence_by_candidate


SCHEMA_VERSION = "missed_fill_opportunity_study_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
COUNTABLE_STATUS = "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
MISS_PATH_LABEL = "continued_without_entry_touch_to_tp_area"
MISS_LTF_STATUS = "NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH"
SHIFT_R_LEVELS = (0.25, 0.50, 0.75, 1.00)


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _clock(row: dict[str, Any]) -> tuple[datetime, datetime]:
    asof = parse_utc(row.get("asof_latest_candle_utc")) or datetime.min.replace(tzinfo=timezone.utc)
    created = parse_utc(row.get("created_at_utc")) or parse_utc(row.get("backfilled_at_utc")) or datetime.min.replace(
        tzinfo=timezone.utc
    )
    return asof, created


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                item = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append(item)
    return rows


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return latest_evidence_by_candidate(rows)


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _risk(candidate: dict[str, Any]) -> float | None:
    params = candidate.get("trade_parameters") or {}
    entry = _safe_float(params.get("entry_price"))
    stop = _safe_float(params.get("stop_loss"))
    if entry is None or stop is None:
        return None
    risk = abs(entry - stop)
    return risk if risk > 0 else None


def _side(candidate: dict[str, Any]) -> str:
    params = candidate.get("trade_parameters") or {}
    return str(candidate.get("side") or params.get("direction") or "").upper()


def _inside_r_required_to_touch(candidate: dict[str, Any], path: dict[str, Any]) -> float | None:
    """Return how far toward market the limit must move, in original risk units.

    0.25 means a limit 0.25R inside the original entry would have touched by
    observed range. Values >1.0 mean even a 1R-inside limit did not touch.
    """
    params = candidate.get("trade_parameters") or {}
    entry = _safe_float(params.get("entry_price"))
    risk = _risk(candidate)
    side = _side(candidate)
    if entry is None or risk is None:
        return None
    if side == "LONG":
        min_low = _safe_float(path.get("min_low"))
        if min_low is None:
            return None
        return round(max(0.0, min_low - entry) / risk, 6)
    if side == "SHORT":
        max_high = _safe_float(path.get("max_high"))
        if max_high is None:
            return None
        return round(max(0.0, entry - max_high) / risk, 6)
    return None


def _is_missed_fill(path: dict[str, Any], ltf: dict[str, Any]) -> bool:
    return str(path.get("path_label") or "") == MISS_PATH_LABEL or str(ltf.get("terminal_outcome_status") or "") == MISS_LTF_STATUS


def _date_key(value: Any) -> str:
    parsed = parse_utc(value)
    return parsed.date().isoformat() if parsed else "UNKNOWN_DATE"


def _rate(numer: int, denom: int) -> float:
    return round(numer / denom, 6) if denom else 0.0


def _empty_group() -> dict[str, Any]:
    return {
        "countable_total": 0,
        "countable_missed_fill_to_tp_area": 0,
        "countable_missed_fill_rate": 0.0,
    }


def _add_group(groups: dict[str, dict[str, Any]], key: str, *, countable: bool, missed: bool) -> None:
    group = groups.setdefault(key, _empty_group())
    if countable:
        group["countable_total"] += 1
        if missed:
            group["countable_missed_fill_to_tp_area"] += 1


def _finalize_groups(groups: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    finalized: dict[str, dict[str, Any]] = {}
    for key, group in sorted(groups.items()):
        item = dict(group)
        item["countable_missed_fill_rate"] = _rate(
            int(item["countable_missed_fill_to_tp_area"]),
            int(item["countable_total"]),
        )
        finalized[key] = item
    return finalized


def build_study(root: Path | str = ".") -> dict[str, Any]:
    root_path = Path(root)
    shadow = root_path / "shadow_logs"
    candidates = latest_by_candidate(read_jsonl(shadow / "strategy_follow_candidates.jsonl"))
    clusters = latest_by_candidate(read_jsonl(shadow / "live_candidate_opportunity_clusters.jsonl"))
    paths = latest_by_candidate(read_jsonl(shadow / "candidate_path_follow.jsonl"))
    ltfs = latest_by_candidate(read_jsonl(shadow / "candidate_ltf_path_order.jsonl"))

    raw_ids = sorted(cid for cid in clusters if cid in candidates)
    countable_ids = [
        cid for cid in raw_ids if (clusters.get(cid) or {}).get("opportunity_counting_status") == COUNTABLE_STATUS
    ]
    path_counts: Counter[str] = Counter()
    final_outcome_counts: Counter[str] = Counter()
    missed_final_outcome_counts: Counter[str] = Counter()
    missed_ids: list[str] = []
    countable_missed_ids: list[str] = []
    by_symbol: dict[str, dict[str, Any]] = {}
    by_session: dict[str, dict[str, Any]] = {}
    by_framework: dict[str, dict[str, Any]] = {}
    by_final_outcome: dict[str, dict[str, Any]] = {}
    by_date: dict[str, dict[str, Any]] = {}
    inside_r_values: list[float] = []
    countable_inside_r_values: list[float] = []
    countable_missed_examples: list[dict[str, Any]] = []
    shifted_touch_counts: Counter[str] = Counter()
    tp1_same_decision_candle = 0

    for cid in raw_ids:
        candidate = candidates[cid]
        cluster = clusters.get(cid) or {}
        path = paths.get(cid) or {}
        ltf = ltfs.get(cid) or {}
        countable = cluster.get("opportunity_counting_status") == COUNTABLE_STATUS
        missed = _is_missed_fill(path, ltf)
        path_label = str(path.get("path_label") or "MISSING_PATH")
        final_outcome = str(candidate.get("final_outcome_at_log") or path.get("final_outcome_at_candidate_log") or "UNKNOWN")
        path_counts[path_label] += 1
        final_outcome_counts[final_outcome] += 1
        if missed:
            missed_ids.append(cid)
            missed_final_outcome_counts[final_outcome] += 1
        if missed and countable:
            countable_missed_ids.append(cid)
            if str(ltf.get("tp1_first_touch_utc") or "") == str(candidate.get("decision_time_utc") or ""):
                tp1_same_decision_candle += 1

        _add_group(by_symbol, str(candidate.get("symbol") or "UNKNOWN"), countable=countable, missed=missed)
        _add_group(by_session, str(candidate.get("session") or candidate.get("kill_zone") or "UNKNOWN"), countable=countable, missed=missed)
        _add_group(by_framework, str(candidate.get("framework") or "UNKNOWN"), countable=countable, missed=missed)
        _add_group(by_final_outcome, final_outcome, countable=countable, missed=missed)
        _add_group(by_date, _date_key(candidate.get("decision_time_utc")), countable=countable, missed=missed)

        if missed:
            inside_r = _inside_r_required_to_touch(candidate, path)
            if inside_r is not None:
                inside_r_values.append(inside_r)
                if countable:
                    countable_inside_r_values.append(inside_r)
                    for level in SHIFT_R_LEVELS:
                        if inside_r <= level:
                            shifted_touch_counts[f"{level:.2f}R_inside_limit"] += 1
            if countable and len(countable_missed_examples) < 20:
                params = candidate.get("trade_parameters") or {}
                countable_missed_examples.append(
                    {
                        "candidate_id": cid,
                        "symbol": candidate.get("symbol"),
                        "session": candidate.get("session") or candidate.get("kill_zone"),
                        "decision_time_utc": candidate.get("decision_time_utc"),
                        "final_outcome_at_log": final_outcome,
                        "framework": candidate.get("framework"),
                        "side": _side(candidate),
                        "entry_price": params.get("entry_price"),
                        "stop_loss": params.get("stop_loss"),
                        "take_profit_1": params.get("take_profit_1"),
                        "inside_r_required_to_touch": inside_r,
                        "path_label": path_label,
                        "ltf_terminal_outcome_status": ltf.get("terminal_outcome_status"),
                    }
                )

    countable_total = len(countable_ids)
    countable_missed_total = len(countable_missed_ids)
    computable_inside = len(countable_inside_r_values)
    more_than_1r_inside = sum(1 for value in countable_inside_r_values if value > 1.0)
    shifted_touch_summary = {
        key: {
            "count": int(value),
            "rate_of_countable_missed_with_computable_range": _rate(int(value), computable_inside),
        }
        for key, value in sorted(shifted_touch_counts.items())
    }
    for level in SHIFT_R_LEVELS:
        key = f"{level:.2f}R_inside_limit"
        shifted_touch_summary.setdefault(
            key,
            {"count": 0, "rate_of_countable_missed_with_computable_range": 0.0},
        )

    follow_up_triggered = countable_total >= 30 and _rate(countable_missed_total, countable_total) >= 0.25
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "MISSED_FILL_ENTRY_GEOMETRY_FOLLOW_UP_RECOMMENDED" if follow_up_triggered else "MISSED_FILL_STUDY_REGISTERED",
        "preregistration": {
            "primary_question": (
                "When the live system identifies a candidate, how often does price reach the original TP1 area "
                "before touching the original limit entry?"
            ),
            "primary_metric": "countable_missed_fill_to_tp_area / countable_primary_opportunities",
            "inclusion_rule": (
                "Use candidates with latest live_candidate_opportunity_clusters rows. Primary denominator is "
                "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY only; duplicates and active same-symbol overlaps remain raw evidence."
            ),
            "miss_definition": (
                "candidate_path_follow.path_label == continued_without_entry_touch_to_tp_area or "
                "candidate_ltf_path_order.terminal_outcome_status == NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH"
            ),
            "secondary_metrics": [
                "miss rate by symbol/session/framework/final outcome/date",
                "inside-R distance required for a more aggressive limit to have touched by observed range",
                "0.25R/0.50R/0.75R/1.00R inside-limit range-touch sensitivity",
            ],
            "claim_boundary": (
                "This study does not prove market-entry profitability or changed live entry rules. Shifted-entry "
                "statistics are range-touch diagnostics only unless a separate tick-order and cost/slippage study is run."
            ),
        },
        "counts": {
            "raw_candidates_with_latest_cluster": len(raw_ids),
            "countable_primary_opportunities": countable_total,
            "raw_missed_fill_to_tp_area": len(missed_ids),
            "countable_missed_fill_to_tp_area": countable_missed_total,
            "countable_missed_fill_rate": _rate(countable_missed_total, countable_total),
            "countable_missed_with_computable_inside_r": computable_inside,
            "countable_missed_more_than_1r_inside_required": more_than_1r_inside,
            "tp1_first_touch_same_decision_candle_countable_misses": tp1_same_decision_candle,
        },
        "path_label_counts_raw": dict(path_counts),
        "final_outcome_counts_raw": dict(final_outcome_counts),
        "missed_fill_final_outcome_counts_raw": dict(missed_final_outcome_counts),
        "group_breakdowns": {
            "by_symbol": _finalize_groups(by_symbol),
            "by_session": _finalize_groups(by_session),
            "by_framework": _finalize_groups(by_framework),
            "by_final_outcome": _finalize_groups(by_final_outcome),
            "by_date": _finalize_groups(by_date),
        },
        "inside_r_required_to_touch_summary": {
            "countable_min": round(min(countable_inside_r_values), 6) if countable_inside_r_values else None,
            "countable_median": round(median(countable_inside_r_values), 6) if countable_inside_r_values else None,
            "countable_max": round(max(countable_inside_r_values), 6) if countable_inside_r_values else None,
            "raw_median": round(median(inside_r_values), 6) if inside_r_values else None,
        },
        "shifted_entry_range_touch_summary": shifted_touch_summary,
        "examples_countable_missed": countable_missed_examples,
        "follow_up_recommendation": (
            "OPEN_PREREGISTERED_ENTRY_GEOMETRY_AND_TICK_ORDER_STUDY"
            if follow_up_triggered
            else "CONTINUE_MONITORING_UNTIL_PRIMARY_TRIGGER"
        ),
        "trigger_policy": {
            "follow_up_trigger": "countable_primary_opportunities >= 30 and countable_missed_fill_rate >= 0.25",
            "trigger_met": follow_up_triggered,
        },
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "order_calls": 0,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }


def write_markdown(study: dict[str, Any], output: Path) -> None:
    counts = study["counts"]
    lines = [
        "# Missed-Fill Entry Geometry Study - 2026-05-12",
        "",
        f"**Schema:** `{study['schema_version']}`",
        f"**Generated:** `{study['generated_at_utc']}`",
        f"**Status:** `{study['status']}`",
        f"**Promotion verdict:** `{study['promotion_verdict']}`",
        "",
        "## Preregistration",
        "",
        f"- Primary question: {study['preregistration']['primary_question']}",
        f"- Primary metric: `{study['preregistration']['primary_metric']}`",
        f"- Inclusion rule: {study['preregistration']['inclusion_rule']}",
        f"- Miss definition: `{study['preregistration']['miss_definition']}`",
        f"- Claim boundary: {study['preregistration']['claim_boundary']}",
        "",
        "## Current Evidence",
        "",
        f"- Raw candidates with latest cluster: `{counts['raw_candidates_with_latest_cluster']}`",
        f"- Countable primary opportunities: `{counts['countable_primary_opportunities']}`",
        f"- Countable missed-fill-to-TP-area: `{counts['countable_missed_fill_to_tp_area']}`",
        f"- Countable missed-fill rate: `{counts['countable_missed_fill_rate']}`",
        f"- Countable missed with computable inside-R: `{counts['countable_missed_with_computable_inside_r']}`",
        f"- Countable misses requiring >1R inside to touch: `{counts['countable_missed_more_than_1r_inside_required']}`",
        f"- Countable misses where TP1 area first touched on decision candle: `{counts['tp1_first_touch_same_decision_candle_countable_misses']}`",
        "",
        "## Breakdowns",
        "",
        f"- By symbol: `{study['group_breakdowns']['by_symbol']}`",
        f"- By session: `{study['group_breakdowns']['by_session']}`",
        f"- By final outcome: `{study['group_breakdowns']['by_final_outcome']}`",
        "",
        "## Shifted Entry Range-Touch Diagnostic",
        "",
        f"`{study['shifted_entry_range_touch_summary']}`",
        "",
        "## Inside-R Required To Touch",
        "",
        f"`{study['inside_r_required_to_touch_summary']}`",
        "",
        "## Recommendation",
        "",
        f"`{study['follow_up_recommendation']}`",
        "",
        "## Safety",
        "",
        f"- No AI calls: `{study['no_ai_calls']}`",
        f"- No canary required: `{study['no_canary_required']}`",
        f"- No execution: `{study['no_execution']}`",
        f"- Order calls: `{study['order_calls']}`",
        f"- Paid fetch attempted: `{study['paid_fetch_attempted']}`",
        f"- Paid data calls: `{study['paid_data_calls']}`",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

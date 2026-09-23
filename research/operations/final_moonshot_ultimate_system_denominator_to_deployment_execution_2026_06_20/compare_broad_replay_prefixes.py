#!/usr/bin/env python3
"""Compare two broad live-as-if replay prefixes.

This is a deterministic route-local analyzer. It compares the completed cap-2
baseline broad replay against a labeled repair run such as the uncapped
candidate-generation parity run. Broker/live/final authority remains closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

ROUTE = Path(__file__).resolve().parent
BASELINE_PREFIX = "BROAD_LIVE_AS_IF_REPLAY"
REPAIR_PREFIX = "BROAD_LIVE_AS_IF_REPLAY_UNCAPPED_PARITY_REPAIR"
DEFAULT_PROFILES = (
    "raw_package_live_as_if",
    "guarded_causal_admission_repair_v2",
    "repaired_package_conversion_v3",
)
SPLITS = ("development", "holdout")
MAX_COMPARISON_ARTIFACT_STEM_CHARS = 180


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def path(prefix: str, suffix: str) -> Path:
    return ROUTE / f"{prefix}_{suffix}"


def prefix_tag(prefix: str) -> str:
    stem = "BROAD_LIVE_AS_IF_REPLAY_"
    if prefix.startswith(stem):
        return prefix[len(stem) :]
    return prefix


def comparison_artifact_stem(*, baseline_prefix: str, repair_prefix: str) -> str:
    digest = hashlib.sha256(
        f"{baseline_prefix}\n{repair_prefix}".encode("utf-8")
    ).hexdigest()[:16]
    repair_tag = prefix_tag(repair_prefix)
    baseline_tag = prefix_tag(baseline_prefix)
    full = f"{repair_tag}_VS_{baseline_tag}_{digest}"
    if len(full) <= MAX_COMPARISON_ARTIFACT_STEM_CHARS:
        return full
    shortened = f"{repair_tag[:86]}_VS_{baseline_tag[:64]}_{digest}"
    return shortened[:MAX_COMPARISON_ARTIFACT_STEM_CHARS]


def read_json(target: Path) -> dict[str, Any]:
    if not target.exists() or not target.read_text(encoding="utf-8").strip():
        raise SystemExit(f"required completed JSON artifact missing or empty: {target}")
    with target.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"expected object JSON at {target}")
    return data


def iter_jsonl(target: Path) -> Iterable[dict[str, Any]]:
    if not target.exists():
        return
    for attempt in range(6):
        try:
            with target.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise SystemExit(
                            f"invalid JSONL at {target}:{line_number}: {exc}"
                        ) from exc
                    if isinstance(row, dict):
                        yield row
            return
        except TimeoutError:
            if attempt >= 5:
                raise
            time.sleep(0.25 * (attempt + 1))


def write_json(target: Path, payload: Mapping[str, Any]) -> None:
    tmp = target.with_name(
        f"{target.stem}.{hashlib.sha256(str(target).encode('utf-8')).hexdigest()[:12]}"
        f"{target.suffix}.tmp"
    )
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(target)


def write_text(target: Path, content: str) -> None:
    tmp = target.with_name(
        f"{target.stem}.{hashlib.sha256(str(target).encode('utf-8')).hexdigest()[:12]}"
        f"{target.suffix}.tmp"
    )
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(target)


def safe_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def text(value: Any, default: str = "unknown") -> str:
    if value is None or value == "":
        return default
    return str(value)


def row_counts(prefix: str) -> dict[str, int]:
    summary = read_json(path(prefix, "SUMMARY.json"))
    candidate_suffix = (
        "CANDIDATE_INDEX_LEDGER.jsonl"
        if summary.get("candidate_ledger_omitted") is True
        else "CANDIDATE_LEDGER.jsonl"
    )
    suffixes = {
        "candidate": candidate_suffix,
        "decision": "DECISION_LEDGER.jsonl",
        "scorecard": "SCORECARD_LEDGER.jsonl",
        "order": "ORDER_LEDGER.jsonl",
        "trade": "TRADE_LEDGER.jsonl",
        "oracle": "ORDERED_PATH_ORACLE_LEDGER.jsonl",
        "missed": "MISSED_OPPORTUNITY_LEDGER.jsonl",
        "comparison": "COMPARISON_LEDGER.jsonl",
    }
    return {
        name: sum(1 for _row in iter_jsonl(path(prefix, suffix)))
        for name, suffix in suffixes.items()
    }


def split_stats(summary: Mapping[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (text(row.get("profile")), text(row.get("split"))): dict(row)
        for row in summary.get("split_profile_stats", [])
        if isinstance(row, dict)
    }


def generation_audit(prefix: str) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    raw_count_hist: Counter[str] = Counter()
    emitted_count_hist: Counter[str] = Counter()
    truncated_rows = 0
    raw_total = 0
    emitted_total = 0
    truncated_total = 0
    max_raw = 0
    max_truncated = 0
    raw_families: Counter[str] = Counter()
    emitted_families: Counter[str] = Counter()
    truncated_families: Counter[str] = Counter()
    audited_rows = 0
    legacy_rows = 0
    for row in iter_jsonl(path(prefix, "DECISION_LEDGER.jsonl")):
        status = text(row.get("raw_data_status"))
        if status != "live_equivalent_raw_data_built_and_mso_computed":
            continue
        scope = row.get("candidate_generation_scope")
        if scope:
            audited_rows += 1
            counts[text(scope)] += 1
            raw = int(row.get("candidate_generation_raw_count") or 0)
            emitted = int(row.get("candidate_generation_emitted_count") or 0)
            truncated = int(row.get("candidate_generation_truncated_count") or 0)
            audit = row.get("candidate_generation_audit")
            audit = audit if isinstance(audit, dict) else {}
            for family, value in (audit.get("raw_origin_family_counts") or {}).items():
                raw_families[str(family)] += int(value or 0)
            for family, value in (audit.get("emitted_origin_family_counts") or {}).items():
                emitted_families[str(family)] += int(value or 0)
            for family, value in (audit.get("truncated_origin_family_counts") or {}).items():
                truncated_families[str(family)] += int(value or 0)
        else:
            legacy_rows += 1
            counts["legacy_no_generation_audit_cap_unknown"] += 1
            raw = int(row.get("candidate_count") or 0)
            emitted = raw
            truncated = 0
        raw_total += raw
        emitted_total += emitted
        truncated_total += truncated
        max_raw = max(max_raw, raw)
        max_truncated = max(max_truncated, truncated)
        if truncated:
            truncated_rows += 1
        raw_count_hist[str(raw)] += 1
        emitted_count_hist[str(emitted)] += 1
    return {
        "audited_decision_rows": audited_rows,
        "legacy_decision_rows": legacy_rows,
        "scope_counts": dict(counts.most_common()),
        "raw_generated_total": raw_total,
        "emitted_candidate_total": emitted_total,
        "truncated_candidate_total": truncated_total,
        "truncated_decision_rows": truncated_rows,
        "max_raw_generated_per_symbol_window": max_raw,
        "max_truncated_per_symbol_window": max_truncated,
        "raw_count_hist": dict(sorted(raw_count_hist.items(), key=lambda item: int(item[0]))),
        "emitted_count_hist": dict(
            sorted(emitted_count_hist.items(), key=lambda item: int(item[0]))
        ),
        "raw_origin_family_counts": dict(raw_families.most_common()),
        "emitted_origin_family_counts": dict(emitted_families.most_common()),
        "truncated_origin_family_counts": dict(truncated_families.most_common()),
    }


def candidate_flow(prefix: str) -> dict[str, Any]:
    summary = read_json(path(prefix, "SUMMARY.json"))
    candidate_suffix = (
        "CANDIDATE_INDEX_LEDGER.jsonl"
        if summary.get("candidate_ledger_omitted") is True
        else "CANDIDATE_LEDGER.jsonl"
    )
    out: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "candidate_rows": 0,
            "selector_action_counts": Counter(),
            "selector_reason_counts": Counter(),
            "origin_family_counts": Counter(),
        }
    )
    for row in iter_jsonl(path(prefix, candidate_suffix)):
        key = (text(row.get("broad_replay_profile")), text(row.get("split")))
        item = out[key]
        item["candidate_rows"] += 1
        item["selector_action_counts"][text(row.get("selector_action"))] += 1
        item["selector_reason_counts"][text(row.get("selector_reason"))] += 1
        item["origin_family_counts"][
            text(row.get("origin_family") or row.get("candidate_origin_family"))
        ] += 1
    return {
        f"{profile}:{split}": {
            "candidate_rows": item["candidate_rows"],
            "selector_action_counts": dict(item["selector_action_counts"].most_common()),
            "selector_reason_counts": dict(item["selector_reason_counts"].most_common()),
            "origin_family_counts": dict(item["origin_family_counts"].most_common()),
        }
        for (profile, split), item in sorted(out.items())
    }


def first_text(row: Mapping[str, Any], *keys: str, default: str = "unknown") -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def trade_identity_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        first_text(
            row,
            "canonical_replay_candidate_instance_key",
            "selected_candidate_instance_key",
            "source_bound_replay_candidate_instance_key",
            "candidate_id",
        ),
        first_text(
            row,
            "decision_window_id",
            "stable_decision_window_id",
            "decision_time_utc",
            "asof_utc",
            "entry_time_utc",
        ),
        first_text(row, "symbol"),
        first_text(row, "side", "direction"),
    )


def trade_brief(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": row.get("candidate_id"),
        "candidate_key": first_text(
            row,
            "canonical_replay_candidate_instance_key",
            "selected_candidate_instance_key",
            "source_bound_replay_candidate_instance_key",
            "candidate_id",
        ),
        "decision_window_id": first_text(
            row,
            "decision_window_id",
            "stable_decision_window_id",
            "decision_time_utc",
            "asof_utc",
            "entry_time_utc",
        ),
        "time_utc": first_text(
            row,
            "asof_utc",
            "decision_time_utc",
            "entry_time_utc",
            default="unknown",
        ),
        "symbol": row.get("symbol"),
        "side": row.get("side") or row.get("direction"),
        "session": row.get("authority_session") or row.get("session"),
        "origin_family": row.get("candidate_origin_family") or row.get("origin_family"),
        "selector_action": row.get("selector_action"),
        "selector_reason": row.get("selector_reason"),
        "risk_decision": row.get("admission_risk_class") or row.get("risk_decision"),
        "risk_pct": row.get("approved_risk_pct") or row.get("risk_pct"),
        "order_policy": row.get("order_policy")
        or row.get("effective_order_type")
        or row.get("order_execution_path"),
        "fill_realism_reason": row.get("fill_realism_reason"),
        "close_reason": row.get("close_reason"),
        "net_r": round(safe_float(row.get("net_r")), 8),
        "gross_r": round(safe_float(row.get("gross_r")), 8),
        "final_r": round(safe_float(row.get("final_r")), 8),
        "expected_cost_r": round(safe_float(row.get("expected_cost_r")), 8),
        "source_bound_signal_r": round(
            safe_float(
                row.get("source_bound_signal_r")
                or row.get("ultimate_package_effective_source_bound_signal_r")
            ),
            8,
        ),
    }


def indexed_trade_rows(
    prefix: str,
    *,
    trade_path: Path | None = None,
) -> dict[tuple[str, str], dict[tuple[Any, ...], dict[str, Any]]]:
    indexed: dict[tuple[str, str], dict[tuple[Any, ...], dict[str, Any]]] = defaultdict(dict)
    duplicate_counts: Counter[tuple[str, str, str, str]] = Counter()
    for row in iter_jsonl(trade_path or path(prefix, "TRADE_LEDGER.jsonl")):
        profile = first_text(row, "broad_replay_profile")
        split = first_text(row, "split")
        base_key = trade_identity_key(row)
        duplicate_counts[base_key] += 1
        indexed[(profile, split)][(*base_key, duplicate_counts[base_key])] = row
    return indexed


def summarize_trade_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    row_list = list(rows)
    return {
        "count": len(row_list),
        "net_r": round(sum(safe_float(row.get("net_r")) for row in row_list), 8),
        "gross_r": round(sum(safe_float(row.get("gross_r")) for row in row_list), 8),
        "final_r": round(sum(safe_float(row.get("final_r")) for row in row_list), 8),
        "win_count": sum(1 for row in row_list if safe_float(row.get("net_r")) > 0),
        "loss_count": sum(1 for row in row_list if safe_float(row.get("net_r")) < 0),
        "flat_count": sum(1 for row in row_list if safe_float(row.get("net_r")) == 0),
        "by_symbol": dict(Counter(first_text(row, "symbol") for row in row_list).most_common()),
        "by_side": dict(
            Counter(first_text(row, "side", "direction") for row in row_list).most_common()
        ),
        "by_session": dict(
            Counter(
                str(row.get("authority_session") or row.get("session") or "unknown")
                for row in row_list
            ).most_common()
        ),
        "by_close_reason": dict(
            Counter(first_text(row, "close_reason") for row in row_list).most_common()
        ),
        "by_selector_reason": dict(
            Counter(first_text(row, "selector_reason") for row in row_list).most_common()
        ),
    }


def declared_trade_row_count(summary: Mapping[str, Any]) -> int | None:
    direct = summary.get("trade_rows")
    if isinstance(direct, (int, float)):
        return int(direct)
    rows = summary.get("split_profile_stats")
    if isinstance(rows, list):
        values = [
            int(row.get("filled_trade_count") or 0)
            for row in rows
            if isinstance(row, Mapping)
        ]
        if values:
            return sum(values)
    return None


def trade_ledger_availability(
    prefix: str,
    summary: Mapping[str, Any],
) -> dict[str, Any]:
    inferred_path = path(prefix, "TRADE_LEDGER.jsonl")
    artifacts = summary.get("artifacts")
    artifacts = artifacts if isinstance(artifacts, Mapping) else {}
    declared_artifact = artifacts.get("trade")
    declared_path = (
        Path(str(declared_artifact))
        if declared_artifact not in (None, "")
        else None
    )
    candidates = [inferred_path]
    if declared_path is not None:
        candidates.extend((declared_path, ROUTE / declared_path.name))
    physical_path = next(
        (candidate for candidate in candidates if candidate.exists()),
        inferred_path,
    )
    declared_count = declared_trade_row_count(summary)
    physical_exists = physical_path.exists()
    physical_count = (
        sum(1 for _row in iter_jsonl(physical_path)) if physical_exists else None
    )
    if not physical_exists:
        status = "unavailable"
        reason = "trade_ledger_missing"
    elif declared_count is not None and physical_count != declared_count:
        status = "inconsistent"
        reason = "summary_declared_trade_count_does_not_match_physical_ledger"
    else:
        status = "complete"
        reason = "physical_trade_ledger_reconciled"
    return {
        "status": status,
        "reason": reason,
        "declared_artifact": str(declared_path) if declared_path else None,
        "resolved_artifact": str(physical_path),
        "physical_exists": physical_exists,
        "summary_declared_trade_count": declared_count,
        "physical_trade_count": physical_count,
    }


def trade_identity_delta(baseline_prefix: str, repair_prefix: str) -> dict[str, Any]:
    baseline_summary = read_json(path(baseline_prefix, "SUMMARY.json"))
    repair_summary = read_json(path(repair_prefix, "SUMMARY.json"))
    baseline_availability = trade_ledger_availability(
        baseline_prefix,
        baseline_summary,
    )
    repair_availability = trade_ledger_availability(
        repair_prefix,
        repair_summary,
    )
    statuses = {
        baseline_availability["status"],
        repair_availability["status"],
    }
    identity_status = (
        "complete"
        if statuses == {"complete"}
        else "inconsistent"
        if "inconsistent" in statuses
        else "unavailable"
    )
    contract = {
        "identity_comparison_status": identity_status,
        "identity_comparison_available": identity_status == "complete",
        "baseline_trade_ledger": baseline_availability,
        "repair_trade_ledger": repair_availability,
        "profile_split": {},
    }
    if identity_status != "complete":
        return contract
    baseline = indexed_trade_rows(
        baseline_prefix,
        trade_path=Path(str(baseline_availability["resolved_artifact"])),
    )
    repair = indexed_trade_rows(
        repair_prefix,
        trade_path=Path(str(repair_availability["resolved_artifact"])),
    )
    keys = sorted(set(baseline) | set(repair))
    out: dict[str, Any] = {}
    for key in keys:
        base = baseline.get(key, {})
        new = repair.get(key, {})
        added_keys = sorted(set(new) - set(base))
        removed_keys = sorted(set(base) - set(new))
        common_keys = sorted(set(base) & set(new))
        common_deltas = [
            {
                **trade_brief(new[item]),
                "baseline_net_r": round(safe_float(base[item].get("net_r")), 8),
                "delta_net_r": round(
                    safe_float(new[item].get("net_r")) - safe_float(base[item].get("net_r")),
                    8,
                ),
                "baseline_close_reason": base[item].get("close_reason"),
            }
            for item in common_keys
            if round(
                safe_float(new[item].get("net_r")) - safe_float(base[item].get("net_r")),
                12,
            )
            != 0
        ]
        common_deltas.sort(key=lambda row: row["delta_net_r"])
        added = [new[item] for item in added_keys]
        removed = [base[item] for item in removed_keys]
        profile, split = key
        out[f"{profile}:{split}"] = {
            "added": summarize_trade_rows(added),
            "removed": summarize_trade_rows(removed),
            "common_count": len(common_keys),
            "common_net_r_delta": round(
                sum(
                    safe_float(new[item].get("net_r")) - safe_float(base[item].get("net_r"))
                    for item in common_keys
                ),
                8,
            ),
            "common_changed_count": len(common_deltas),
            "common_worst_deltas": common_deltas[:10],
            "common_best_deltas": common_deltas[-10:],
            "added_examples_low_to_high": [
                trade_brief(row)
                for row in sorted(added, key=lambda item: safe_float(item.get("net_r")))[:10]
            ],
            "added_examples_high_to_low": [
                trade_brief(row)
                for row in sorted(
                    added, key=lambda item: safe_float(item.get("net_r")), reverse=True
                )[:10]
            ],
            "removed_examples_low_to_high": [
                trade_brief(row)
                for row in sorted(removed, key=lambda item: safe_float(item.get("net_r")))[:10]
            ],
            "removed_examples_high_to_low": [
                trade_brief(row)
                for row in sorted(
                    removed, key=lambda item: safe_float(item.get("net_r")), reverse=True
                )[:10]
            ],
        }
    contract["profile_split"] = out
    return contract


def compare_stats(
    baseline: Mapping[tuple[str, str], Mapping[str, Any]],
    repair: Mapping[tuple[str, str], Mapping[str, Any]],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    fields = (
        "candidate_rows",
        "scorecard_rows",
        "order_rows",
        "filled_trade_count",
        "win_count",
        "loss_count",
        "flat_count",
        "gross_r",
        "final_r",
        "net_r",
        "cash_pnl",
        "risk_cash",
        "risk_pct",
        "missed_total_scoreable_net_r",
        "missed_positive_net_r",
        "missed_negative_net_r",
    )
    profile_order = list(DEFAULT_PROFILES)
    for profile, _split in list(baseline) + list(repair):
        if profile not in profile_order:
            profile_order.append(profile)
    split_order = list(SPLITS)
    for _profile, split in list(baseline) + list(repair):
        if split not in split_order:
            split_order.append(split)
    for profile in profile_order:
        for split in split_order:
            key = (profile, split)
            base = baseline.get(key, {})
            new = repair.get(key, {})
            if not base and not new and profile not in DEFAULT_PROFILES:
                continue
            row: dict[str, Any] = {
                "profile": profile,
                "split": split,
                "baseline_present": bool(base),
                "repair_present": bool(new),
            }
            for field in fields:
                base_value = base.get(field)
                repair_value = new.get(field)
                row[f"baseline_{field}"] = base_value
                row[f"repair_{field}"] = repair_value
                if isinstance(base_value, (int, float)) or isinstance(repair_value, (int, float)):
                    row[f"delta_{field}"] = round(
                        safe_float(repair_value) - safe_float(base_value),
                        8,
                    )
            out[f"{profile}:{split}"] = row
    return out


def build_dossier(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Broad Live-As-If Candidate-Parity Repair Comparison",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "Broker/live/final authority remains closed. This compares replay-only artifacts.",
        "",
        "## Candidate Generation",
        "",
        f"- Baseline prefix: `{summary['baseline_prefix']}`.",
        f"- Repair prefix: `{summary['repair_prefix']}`.",
        f"- Baseline generation authority: {summary['baseline_summary'].get('candidate_generation_authority', 'legacy_cap2_no_audit')}.",
        f"- Repair generation authority: {summary['repair_summary'].get('candidate_generation_authority')}.",
        f"- Baseline emitted candidates from decision ledger: {summary['baseline_generation']['emitted_candidate_total']}.",
        f"- Repair raw generated candidates: {summary['repair_generation']['raw_generated_total']}.",
        f"- Repair emitted candidates: {summary['repair_generation']['emitted_candidate_total']}.",
        f"- Repair truncated candidates: {summary['repair_generation']['truncated_candidate_total']}.",
        f"- Repair max raw generated per symbol-window: {summary['repair_generation']['max_raw_generated_per_symbol_window']}.",
        "",
        "## Replay Outcomes",
        "",
    ]
    for key, row in summary["profile_split_comparison"].items():
        lines.append(
            "- "
            f"{key}: baseline trades={row.get('baseline_filled_trade_count')} "
            f"net_r={row.get('baseline_net_r')} cash={row.get('baseline_cash_pnl')} "
            f"w/l/f={row.get('baseline_win_count')}/{row.get('baseline_loss_count')}/{row.get('baseline_flat_count')}; "
            f"repair trades={row.get('repair_filled_trade_count')} "
            f"net_r={row.get('repair_net_r')} cash={row.get('repair_cash_pnl')} "
            f"w/l/f={row.get('repair_win_count')}/{row.get('repair_loss_count')}/{row.get('repair_flat_count')}; "
            f"delta_net_r={row.get('delta_net_r')}"
        )
    lines.extend(["", "## Added And Removed Trades", ""])
    identity_delta = summary.get("trade_identity_delta") or {}
    lines.append(
        "- Identity comparison status: "
        f"{identity_delta.get('identity_comparison_status', 'unknown')}."
    )
    for key, row in (identity_delta.get("profile_split") or {}).items():
        added = row.get("added") or {}
        removed = row.get("removed") or {}
        lines.append(
            "- "
            f"{key}: added trades={added.get('count')} net_r={added.get('net_r')} "
            f"w/l/f={added.get('win_count')}/{added.get('loss_count')}/{added.get('flat_count')}; "
            f"removed trades={removed.get('count')} net_r={removed.get('net_r')} "
            f"w/l/f={removed.get('win_count')}/{removed.get('loss_count')}/{removed.get('flat_count')}; "
            f"common_net_r_delta={row.get('common_net_r_delta')} "
            f"common_changed={row.get('common_changed_count')}"
        )
        if added.get("by_symbol"):
            lines.append(f"  - Added by symbol: {json.dumps(added.get('by_symbol'), sort_keys=True)}")
        if removed.get("by_symbol"):
            lines.append(
                f"  - Removed by symbol: {json.dumps(removed.get('by_symbol'), sort_keys=True)}"
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A positive delta here proves only that the executable replay wiring improved for the bounded run.",
            "- A negative or mixed delta means the source-bound reservoir is still not converting after candidate generation, and the next limiting leak is selector/scheduler/risk/exit behavior.",
            "- The 1.249M R source-bound reservoir is not a filled-trade result; parity requires these axes to survive generation, selector, scheduler, risk, order, fillability, lifecycle, and exit conversion.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-prefix", default=BASELINE_PREFIX)
    parser.add_argument("--repair-prefix", default=REPAIR_PREFIX)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline_prefix = str(args.baseline_prefix)
    repair_prefix = str(args.repair_prefix)
    baseline_summary = read_json(path(baseline_prefix, "SUMMARY.json"))
    repair_summary = read_json(path(repair_prefix, "SUMMARY.json"))
    summary = {
        "schema": "gtos.final_moonshot.broad_live_as_if_replay.prefix_comparison.v2",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE.name,
        "baseline_prefix": baseline_prefix,
        "repair_prefix": repair_prefix,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
        "baseline_summary": {
            "status": baseline_summary.get("status"),
            "coverage_status": baseline_summary.get("coverage_status"),
            "selected_day_count": baseline_summary.get("selected_day_count"),
            "candidate_generation_authority": baseline_summary.get(
                "candidate_generation_authority"
            ),
            "max_candidates_per_symbol_window": baseline_summary.get(
                "max_candidates_per_symbol_window"
            ),
        },
        "repair_summary": {
            "status": repair_summary.get("status"),
            "coverage_status": repair_summary.get("coverage_status"),
            "selected_day_count": repair_summary.get("selected_day_count"),
            "candidate_generation_authority": repair_summary.get(
                "candidate_generation_authority"
            ),
            "max_candidates_per_symbol_window": repair_summary.get(
                "max_candidates_per_symbol_window"
            ),
        },
        "baseline_row_counts": row_counts(baseline_prefix),
        "repair_row_counts": row_counts(repair_prefix),
        "baseline_generation": generation_audit(baseline_prefix),
        "repair_generation": generation_audit(repair_prefix),
        "baseline_candidate_flow": candidate_flow(baseline_prefix),
        "repair_candidate_flow": candidate_flow(repair_prefix),
        "trade_identity_delta": trade_identity_delta(baseline_prefix, repair_prefix),
        "profile_split_comparison": compare_stats(
            split_stats(baseline_summary),
            split_stats(repair_summary),
        ),
    }
    artifact_stem = comparison_artifact_stem(
        baseline_prefix=baseline_prefix,
        repair_prefix=repair_prefix,
    )
    out_summary = ROUTE / f"{artifact_stem}_BEHAVIOR_COMPARISON_SUMMARY.json"
    out_dossier = ROUTE / f"{artifact_stem}_BEHAVIOR_DOSSIER.md"
    summary["artifacts"] = {
        "comparison_summary": str(out_summary),
        "behavior_dossier": str(out_dossier),
    }
    write_json(out_summary, summary)
    write_text(out_dossier, build_dossier(summary))
    print(
        json.dumps(
            {
                "status": "broad_replay_prefix_comparison_materialized",
                "baseline_prefix": baseline_prefix,
                "repair_prefix": repair_prefix,
                "artifacts": summary["artifacts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

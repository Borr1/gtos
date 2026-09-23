from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
PARENT = REPO_ROOT / (
    "research/operations/"
    "final_moonshot_v4_kia_parity_tick_first_runtime_repair_2026_06_07"
)

ITEM9_INPUTS = {
    "scheduler_regret": "KIAP_ITEM9_SCHEDULER_REGRET_LEDGER.jsonl",
    "risk_headroom_lockout": "KIAP_ITEM9_RISK_HEADROOM_LOCKOUT_LEDGER.jsonl",
    "weak_accepted_trades": "KIAP_ITEM9_WEAK_ACCEPTED_TRADE_LEDGER.jsonl",
    "partial_be_runner": "KIAP_ITEM9_PARTIAL_BE_RUNNER_LEDGER.jsonl",
    "cost_flips": "KIAP_ITEM9_COST_FLIP_LEDGER.jsonl",
}

CANDIDATE_INPUTS = {
    "full_development": "KIAP_FULL_DEVELOPMENT_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
    "repair_rerun": "KIAP_REPAIR_RERUN_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
    "holdout_rolling": "KIAP_HOLDOUT_ROLLING_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
    "development": "KIAP_DEVELOPMENT_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
    "smoke": "KIAP_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
}

OUTPUTS = {
    "summary": ROUTE / "ULTIMATE_SYSTEM_REPAIR_ANALYSIS_SUMMARY.json",
    "scheduler_regret": ROUTE / "ULTIMATE_SCHEDULER_REGRET_REPAIR_LEDGER.jsonl",
    "risk_headroom_lockout": ROUTE / "ULTIMATE_RISK_HEADROOM_REPAIR_LEDGER.jsonl",
    "weak_accepted_trades": ROUTE / "ULTIMATE_WEAK_ACCEPTED_FILTER_LEDGER.jsonl",
    "partial_be_runner": ROUTE / "ULTIMATE_PARTIAL_BE_POLICY_DISPOSITION_LEDGER.jsonl",
    "cost_flips": ROUTE / "ULTIMATE_COST_FLIP_REPAIR_LEDGER.jsonl",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def num(value: Any, default: float = 0.0) -> float:
    if value in (None, "") or isinstance(value, bool):
        return default
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if out != out or out in (float("inf"), float("-inf")):
        return default
    return out


def phase_of(row: Mapping[str, Any], fallback: str | None = None) -> str:
    return str(
        row.get("phase")
        or row.get("kiap_campaign_phase")
        or fallback
        or "unknown"
    )


def candidate_key(row: Mapping[str, Any], fallback_phase: str | None = None) -> tuple[str, str]:
    return phase_of(row, fallback_phase), str(row.get("candidate_id") or "")


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def atomic_write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    tmp = path.with_suffix(path.suffix + ".tmp")
    count = 0
    with tmp.open("w", encoding="utf-8") as handle:
        for row in rows:
            count += 1
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    tmp.replace(path)
    return count


def load_candidate_index() -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for phase, filename in CANDIDATE_INPUTS.items():
        for row in iter_jsonl(PARENT / filename):
            key = candidate_key(row, phase)
            if key[1]:
                index[key] = row
    return index


def candidate_digest(candidate: Mapping[str, Any] | None) -> dict[str, Any]:
    if not candidate:
        return {}
    source_fields = candidate.get("source_fields")
    source_fields = source_fields if isinstance(source_fields, Mapping) else {}
    return {
        "candidate_probability": candidate.get("candidate_probability"),
        "candidate_ev_r": candidate.get("candidate_ev_r"),
        "expected_cost_r": candidate.get("expected_cost_r") or candidate.get("cost_r"),
        "risk_pct": candidate.get("risk_pct"),
        "framework": candidate.get("framework"),
        "origin_family": candidate.get("origin_family")
        or candidate.get("candidate_origin_family"),
        "dynamic_geometry_policy": candidate.get("dynamic_geometry_policy"),
        "selector_action": candidate.get("selector_action"),
        "selector_reason": candidate.get("selector_reason"),
        "route_session": candidate.get("route_session") or candidate.get("session"),
        "utc_hour_bucket": candidate.get("utc_hour_bucket")
        or source_fields.get("utc_hour_bucket"),
        "mso_context_available": source_fields.get("mso_context_available"),
        "source_window_complete": candidate.get("source_window_complete"),
    }


def edge_label(row: Mapping[str, Any], candidate: Mapping[str, Any] | None) -> str:
    ev = num(row.get("candidate_ev_r"), num((candidate or {}).get("candidate_ev_r")))
    probability = num(
        row.get("candidate_probability"),
        num((candidate or {}).get("candidate_probability"), 0.50),
    )
    cost = num(row.get("expected_cost_r"), num((candidate or {}).get("expected_cost_r")))
    net = num(row.get("net_proxy_r"))
    if net > 0.0 and ev >= 0.65 and probability >= 0.68 and cost <= 0.22:
        return "positive_high_edge_candidate"
    if net > 0.0:
        return "positive_candidate_needs_score_context_review"
    if net <= -1.0:
        return "negative_trade_family_member"
    return "mixed_or_neutral_candidate"


def lockout_cause(row: Mapping[str, Any]) -> str:
    risk_authority = row.get("risk_authority")
    risk_authority = risk_authority if isinstance(risk_authority, Mapping) else {}
    daily = num(
        row.get("daily_runtime_headroom_pct_before"),
        num(risk_authority.get("daily_runtime_headroom_pct_before")),
    )
    scheduler_approved = num(
        row.get("scheduler_approved_risk_pct"),
        num(risk_authority.get("scheduler_approved_risk_pct")),
    )
    pending = num(
        row.get("pending_risk_pct_before"),
        num(risk_authority.get("pending_risk_pct_before")),
    )
    open_risk = num(
        row.get("open_risk_pct_before"),
        num(risk_authority.get("open_risk_pct_before")),
    )
    portfolio = num(
        row.get("portfolio_ceiling_pct"),
        num(risk_authority.get("portfolio_ceiling_pct"), 4.0),
    )
    if daily <= 0.0:
        return "prop_daily_drawdown_headroom_exhausted"
    if scheduler_approved > 0.0 and pending > 0.0:
        return "pending_risk_occupies_scheduler_approved_headroom"
    if open_risk + pending >= portfolio:
        return "portfolio_reserved_risk_ceiling_occupied"
    if scheduler_approved <= 0.0:
        return "scheduler_zero_or_no_risk_approval"
    return "runtime_ceiling_mismatch_requires_packet_review"


def repair_hook(family: str, row: Mapping[str, Any], candidate: Mapping[str, Any] | None) -> str:
    label = edge_label(row, candidate)
    if family == "scheduler_regret":
        if label == "positive_high_edge_candidate":
            return "scheduler_score_and_pending_replacement_repair"
        return "scheduler_score_diagnostics_repair"
    if family == "risk_headroom_lockout":
        cause = lockout_cause(row)
        if cause == "pending_risk_occupies_scheduler_approved_headroom":
            return "dominated_pending_risk_replacement_repair"
        if cause == "prop_daily_drawdown_headroom_exhausted":
            return "upstream_weak_acceptance_and_drawdown_recovery_repair"
        return "risk_authority_scheduler_alignment_repair"
    if family == "weak_accepted_trades":
        return "weak_acceptance_quality_floor_and_cost_filter_repair"
    if family == "partial_be_runner":
        return "keep_partial_be_disabled_until_evidence_routed_exception_wins"
    if family == "cost_flips":
        return "net_after_cost_flip_filter_repair"
    return "route_review_required"


def enrich_family_rows(
    *,
    family: str,
    filename: str,
    candidate_index: Mapping[tuple[str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(iter_jsonl(PARENT / filename), start=1):
        phase = phase_of(row)
        candidate = candidate_index.get(candidate_key(row))
        digest = candidate_digest(candidate)
        enriched = {
            "ultimate_row_id": f"ULTIMATE-{family.upper()}-{idx:05d}",
            "source_kiap_item9_row_id": row.get("kiap_item9_row_id"),
            "family": family,
            "phase": phase,
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "decision_time_utc": row.get("decision_time_utc"),
            "gross_r": row.get("gross_r"),
            "expected_cost_r": row.get("expected_cost_r"),
            "net_proxy_r": row.get("net_proxy_r"),
            "miss_reason": row.get("miss_reason"),
            "risk_decision_reason": row.get("risk_decision_reason"),
            "edge_label": edge_label(row, candidate),
            "lockout_cause": lockout_cause(row)
            if family == "risk_headroom_lockout"
            else None,
            "repair_hook": repair_hook(family, row, candidate),
            "candidate_digest": digest,
            "source_ledger": row.get("kiap_item9_source_ledger"),
            "evidence_class": row.get("evidence_class"),
        }
        rows.append(enriched)
    return rows


def family_summary(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    by_phase: dict[str, dict[str, Any]] = {}
    phases = sorted({str(row.get("phase")) for row in rows})
    for phase in phases:
        phase_rows = [row for row in rows if row.get("phase") == phase]
        by_phase[phase] = {
            "rows": len(phase_rows),
            "gross_r": round(sum(num(row.get("gross_r")) for row in phase_rows), 8),
            "expected_cost_r": round(
                sum(num(row.get("expected_cost_r")) for row in phase_rows),
                8,
            ),
            "net_proxy_r": round(sum(num(row.get("net_proxy_r")) for row in phase_rows), 8),
            "edge_labels": dict(Counter(str(row.get("edge_label")) for row in phase_rows)),
            "repair_hooks": dict(Counter(str(row.get("repair_hook")) for row in phase_rows)),
            "lockout_causes": dict(
                Counter(
                    str(row.get("lockout_cause"))
                    for row in phase_rows
                    if row.get("lockout_cause")
                )
            ),
        }
    return {
        "rows": len(rows),
        "gross_r": round(sum(num(row.get("gross_r")) for row in rows), 8),
        "expected_cost_r": round(sum(num(row.get("expected_cost_r")) for row in rows), 8),
        "net_proxy_r": round(sum(num(row.get("net_proxy_r")) for row in rows), 8),
        "by_phase": by_phase,
        "repair_hooks": dict(Counter(str(row.get("repair_hook")) for row in rows)),
    }


def main() -> None:
    candidate_index = load_candidate_index()
    family_rows: dict[str, list[dict[str, Any]]] = {}
    output_counts: dict[str, int] = {}
    for family, filename in ITEM9_INPUTS.items():
        rows = enrich_family_rows(
            family=family,
            filename=filename,
            candidate_index=candidate_index,
        )
        family_rows[family] = rows
        output_counts[family] = atomic_write_jsonl(OUTPUTS[family], rows)

    summary = {
        "schema_version": "ultimate_system_repair_analysis_v1",
        "generated_at_utc": utc_now(),
        "route_id": "final_moonshot_v4_kiap_ultimate_system_repair_2026_06_07",
        "parent_route": str(PARENT.relative_to(REPO_ROOT)),
        "parent_commit": "6d645a7f3",
        "candidate_index_rows": len(candidate_index),
        "output_counts": output_counts,
        "family_summary": {
            family: family_summary(rows)
            for family, rows in family_rows.items()
        },
        "first_production_called_repair": {
            "name": "scheduler_v4_dominated_pending_replacement",
            "source_failure_families": [
                "scheduler_regret",
                "risk_headroom_lockout",
            ],
            "code_surfaces": [
                "src/research/moonshot_scheduler_v4_best_trade_allocator.py",
                "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
                "src/components/orchestrator.py",
                "src/components/permissions.py",
                "config/agent_config.yaml",
            ],
        },
    }
    atomic_write_json(OUTPUTS["summary"], summary)


if __name__ == "__main__":
    main()

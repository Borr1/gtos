#!/usr/bin/env python3
"""Audit GTOS symbols for futures orderflow proxy validation state.

Research/tooling only. This audit does not fetch Databento data, does not add
live trading logic, and does not claim alpha. It reads the current candidate
feature shadow log and reports which symbols are research-manifest supported
versus still blocked by proxy validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.orderflow_event_manifest import (  # noqa: E402
    FUTURES_PROXY_MAP,
    event_tags,
    read_jsonl,
)


DEFAULT_SOURCE = "shadow_logs/candidate_features_log.jsonl"
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_PROXY_MAPPING_PRIORITY_AUDIT_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_PROXY_MAPPING_PRIORITY_AUDIT_2026-05-02.md"
)

ORDERFLOW_RELEVANT_TAGS = {
    "candidate",
    "m15_choch",
    "c_gate_m15_choch",
    "h1_ob_available",
    "h1_fvg_available",
    "m15_fvg_available",
    "liquidity_sweeps_detected",
}

LIVE_ENABLED_RESEARCH_SYMBOLS = {"XAUUSD", "US30", "US30_cash", "USDJPY", "GBPJPY", "XAGUSD", "NAS100"}
OBSERVER_OR_CONTROL_SYMBOLS = {"GBPUSD"}

PROXY_CANDIDATES: dict[str, dict[str, Any]] = {
    "XAGUSD": {
        "recommended_rank": 1,
        "databento_symbols": ["SI.v.0"],
        "proxy_relation": "direct precious-metal futures proxy",
        "transform_policy": "direct_return_alignment_after_timestamp_and_roll_audit",
        "transform_complexity": "low",
        "operational_relevance": "live_enabled_symbol",
        "why_this_rank": (
            "Closest unresolved extension of the already-supported GC/XAUUSD metals lane; "
            "single futures contract, direct directional relation, and no synthetic cross book."
        ),
        "blocking_validations": [
            "SI.v.0 to XAGUSD M1 return correlation across multiple windows",
            "date-aware MT5 timestamp correction without per-window hindsight",
            "silver futures roll behavior around selected windows",
            "CFD/futures basis stability during London and NY kill zones",
        ],
    },
    "USDJPY": {
        "recommended_rank": 2,
        "databento_symbols": ["6J.v.0"],
        "proxy_relation": "inverse FX futures proxy",
        "transform_policy": "use return-level inverse relation; avoid raw price-level comparison until scale is pinned",
        "transform_complexity": "medium",
        "operational_relevance": "live_enabled_symbol",
        "why_this_rank": (
            "Largest unsupported candidate count and live-enabled, but the 6J quote direction is inverse "
            "to USDJPY, so it must pass an explicit sign/scale audit before event harvesting."
        ),
        "blocking_validations": [
            "inverse-return sign agreement between 6J.v.0 and USDJPY",
            "price-scale convention for any absolute-level diagnostics",
            "roll/calendar continuity around JPY futures",
            "whether inverse depth/flow features preserve the same economic interpretation",
        ],
    },
    "GBPUSD": {
        "recommended_rank": 3,
        "databento_symbols": ["6B.v.0"],
        "proxy_relation": "direct FX futures proxy",
        "transform_policy": "direct_return_alignment_after_timestamp_and_roll_audit",
        "transform_complexity": "low",
        "operational_relevance": "observer_or_control_symbol",
        "why_this_rank": (
            "Clean direct futures relationship and useful as a control/leg for GBPJPY, but GBPUSD is "
            "observer-only in the current GTOS deployment, so it follows the live-enabled unresolved symbols."
        ),
        "blocking_validations": [
            "6B.v.0 to GBPUSD M1 return correlation across multiple windows",
            "date-aware MT5 timestamp correction without per-window hindsight",
            "sterling futures roll behavior around selected windows",
            "observer-only status handling in any later event manifest",
        ],
    },
    "GBPJPY": {
        "recommended_rank": 4,
        "databento_symbols": ["6B.v.0", "6J.v.0"],
        "proxy_relation": "synthetic cross from two FX futures legs",
        "transform_policy": "validate 6B/6J synthetic return relation before any depth interpretation",
        "transform_complexity": "high",
        "operational_relevance": "live_enabled_symbol",
        "why_this_rank": (
            "Live-enabled, but there is no single CME GBPJPY ladder. Price transfer may be synthetic; "
            "orderflow/depth interpretation is split across two books and is therefore highest ambiguity."
        ),
        "blocking_validations": [
            "6B and 6J direct/inverse leg validation first",
            "synthetic cross return correlation against GBPJPY",
            "synchronized futures-leg timestamp policy",
            "definition of what a two-book LVN/HVN or absorption signal would mean",
        ],
    },
}


def generated_at_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def candidate_direction(row: dict[str, Any]) -> str:
    trade_params = row.get("trade_parameters") or {}
    return str(trade_params.get("direction") or "none")


def is_orderflow_relevant(row: dict[str, Any]) -> bool:
    return bool(set(event_tags(row)) & ORDERFLOW_RELEVANT_TAGS)


def summarize_symbol_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_symbol: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        symbol = str(row.get("symbol") or "UNKNOWN")
        by_symbol.setdefault(symbol, []).append(row)

    out: dict[str, dict[str, Any]] = {}
    for symbol, symbol_rows in sorted(by_symbol.items()):
        candidate_rows = [row for row in symbol_rows if row.get("decision") == "CANDIDATE"]
        relevant_rows = [row for row in symbol_rows if is_orderflow_relevant(row)]
        out[symbol] = {
            "total_rows": len(symbol_rows),
            "orderflow_relevant_rows": len(relevant_rows),
            "candidate_rows": len(candidate_rows),
            "decision_counts": dict(sorted(Counter(row.get("decision") or "none" for row in symbol_rows).items())),
            "candidate_direction_counts": dict(sorted(Counter(candidate_direction(row) for row in candidate_rows).items())),
            "session_counts": dict(sorted(Counter(row.get("session_tag") or row.get("kill_zone") or "none" for row in symbol_rows).items())),
            "candidate_session_counts": dict(
                sorted(Counter(row.get("session_tag") or row.get("kill_zone") or "none" for row in candidate_rows).items())
            ),
            "current_proxy_supported": symbol in FUTURES_PROXY_MAP,
            "currently_supported_databento_symbols": list(FUTURES_PROXY_MAP.get(symbol, ())),
            "symbol_role": (
                "live_enabled_research_symbol"
                if symbol in LIVE_ENABLED_RESEARCH_SYMBOLS
                else "observer_or_control_symbol"
                if symbol in OBSERVER_OR_CONTROL_SYMBOLS
                else "unknown"
            ),
        }
    return out


def build_priority_queue(symbol_summaries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for symbol, proxy in PROXY_CANDIDATES.items():
        summary = symbol_summaries.get(
            symbol,
            {
                "total_rows": 0,
                "orderflow_relevant_rows": 0,
                "candidate_rows": 0,
                "candidate_direction_counts": {},
                "candidate_session_counts": {},
                "current_proxy_supported": False,
                "symbol_role": "unknown",
            },
        )
        rows.append(
            {
                "symbol": symbol,
                "recommended_rank": proxy["recommended_rank"],
                "databento_symbols": proxy["databento_symbols"],
                "proxy_relation": proxy["proxy_relation"],
                "transform_policy": proxy["transform_policy"],
                "transform_complexity": proxy["transform_complexity"],
                "operational_relevance": proxy["operational_relevance"],
                "current_candidate_rows": summary["candidate_rows"],
                "current_orderflow_relevant_rows": summary["orderflow_relevant_rows"],
                "candidate_direction_counts": summary["candidate_direction_counts"],
                "candidate_session_counts": summary["candidate_session_counts"],
                "why_this_rank": proxy["why_this_rank"],
                "blocking_validations": proxy["blocking_validations"],
                "activation_status": (
                    "SUPPORTED_RESEARCH_PROXY_MAP"
                    if summary["current_proxy_supported"]
                    else "NOT_IN_FUTURES_PROXY_MAP"
                ),
                "recommended_next_lane": (
                    "event_manifest_allowed_no_depth_until_symbol_hypothesis"
                    if summary["current_proxy_supported"]
                    else "mapping_validation_only_no_event_harvest_yet"
                ),
            }
        )
    return sorted(rows, key=lambda item: item["recommended_rank"])


def build_payload(rows: list[dict[str, Any]], *, source_path: Path | str) -> dict[str, Any]:
    source = Path(source_path)
    symbol_summaries = summarize_symbol_rows(rows)
    supported_symbols = sorted(symbol for symbol in symbol_summaries if symbol in FUTURES_PROXY_MAP)
    unsupported_symbols = sorted(symbol for symbol in symbol_summaries if symbol not in FUTURES_PROXY_MAP)
    unsupported_candidate_counts = {
        symbol: symbol_summaries[symbol]["candidate_rows"]
        for symbol in unsupported_symbols
        if symbol_summaries[symbol]["candidate_rows"] > 0
    }
    supported_candidate_counts = {
        symbol: symbol_summaries[symbol]["candidate_rows"]
        for symbol in supported_symbols
        if symbol_summaries[symbol]["candidate_rows"] > 0
    }
    priority_queue = build_priority_queue(symbol_summaries)

    payload: dict[str, Any] = {
        "schema_version": "orderflow_proxy_mapping_priority_audit_v1",
        "generated_at_utc": generated_at_utc(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "registration_verdict": "NO_PROXY_MAPPING_ACTIVATED",
        "inputs": {
            "source_path": str(source_path),
            "source_sha256": sha256_file(source) if source.exists() else None,
            "rows_loaded": len(rows),
            "current_supported_proxy_map": {key: list(value) for key, value in sorted(FUTURES_PROXY_MAP.items())},
            "note": "This audit reads local shadow rows only and performs no Databento fetch.",
        },
        "current_coverage": {
            "supported_symbols": supported_symbols,
            "unsupported_symbols": unsupported_symbols,
            "supported_candidate_counts": supported_candidate_counts,
            "unsupported_candidate_counts": unsupported_candidate_counts,
            "supported_candidate_total": sum(supported_candidate_counts.values()),
            "unsupported_candidate_total": sum(unsupported_candidate_counts.values()),
            "unsupported_orderflow_relevant_total": sum(
                symbol_summaries[symbol]["orderflow_relevant_rows"] for symbol in unsupported_symbols
            ),
            "symbol_summaries": symbol_summaries,
        },
        "priority_queue": priority_queue,
        "validation_protocol": {
            "scope": "mapping validation before event-window harvesting",
            "minimum_first_pull": "one or more capped trades-only windows per proposed proxy; no depth pull before price-transfer passes",
            "mandatory_checks": [
                "date-aware MT5 timestamp correction must be chosen by rule, not hindsight per window",
                "M1 return correlation and sign agreement must be checked on multiple windows",
                "roll-date behavior must be pinned for continuous futures symbols",
                "basis/lag diagnostics must be reported before any orderflow feature use",
                "observer-only symbols must stay controls unless separately promoted by CEO-approved system scope",
            ],
            "explicitly_blocked": [
                "adding unsupported symbols to FUTURES_PROXY_MAP from this audit alone",
                "pulling mbp-1/mbp-10 depth before trades-level transfer passes",
                "using synthetic GBPJPY two-book depth as if it were one executable ladder",
                "registering an alpha hypothesis from proxy availability alone",
            ],
        },
    }
    payload["synthesis"] = build_synthesis(payload)
    return payload


def build_synthesis(payload: dict[str, Any]) -> dict[str, Any]:
    coverage = payload["current_coverage"]
    queue = payload["priority_queue"]
    rank_readout = [
        (
            f"{item['recommended_rank']}. {item['symbol']} -> {','.join(item['databento_symbols'])}: "
            f"{item['current_candidate_rows']} current candidates; "
            f"{item['proxy_relation']}; complexity={item['transform_complexity']}; "
            f"status={item['activation_status']}."
        )
        for item in queue
    ]
    supported_map = payload["inputs"]["current_supported_proxy_map"]
    unresolved = coverage["unsupported_candidate_counts"]
    return {
        "summary": (
            "The current research orderflow manifest supports "
            f"{sorted(supported_map)}. The remaining proxy-mapping blockers are "
            f"{unresolved}; USDJPY/6J is under transfer review and GBPJPY remains a "
            "two-book synthetic-cross problem."
        ),
        "readout": [
            (
                f"Loaded {payload['inputs']['rows_loaded']} candidate-feature rows. "
                f"Unsupported CANDIDATE rows total {coverage['unsupported_candidate_total']} across "
                f"{coverage['unsupported_candidate_counts']}."
            ),
            (
                f"Supported CANDIDATE rows total {coverage['supported_candidate_total']} across "
                f"{coverage['supported_candidate_counts']}."
            ),
            "Recommended validation order is based on current candidate inventory, live relevance, proxy directness, and transform risk.",
            *rank_readout,
        ],
        "ambiguity_ledger": [
            "This audit reflects the current research proxy map; it is not a live trading configuration change.",
            "XAGUSD/SI and GBPUSD/6B have strict price-transfer support, but no orderflow alpha is validated.",
            "USDJPY/6J requires inverse-return handling and remains under strict transfer review.",
            "GBPJPY has no single CME order book; synthetic price transfer and synthetic depth/flow interpretation are different problems.",
            "Current candidate counts come from the mutable local shadow log and are not an immutable historical population.",
            "Depth pulls remain blocked until symbol-specific event-window hypotheses are registered.",
        ],
        "opened_questions": [
            "Does 6J.v.0 recover above the strict USDJPY transfer floor across additional windows?",
            "Should GBPUSD/6B remain a control-only research symbol unless observer scope changes?",
            "Can GBPJPY be represented by 6B/6J synthetic returns for price transfer without corrupting orderflow interpretation?",
            "Which newly supported direct proxy, XAGUSD or GBPUSD, has enough labels to justify trades-feature extraction?",
            "Can the seasonal -120/-180 minute MT5 timestamp policy be converted into a date-aware rule before more futures pulls?",
        ],
        "next_steps": [
            "Build a refreshed event-window manifest with XAGUSD/SI and GBPUSD/6B included, but do not fetch depth.",
            "Run one targeted 6J/USDJPY follow-up set before adding USDJPY to the research proxy map.",
            "Keep GBPJPY orderflow blocked until both legs pass price transfer and a two-book hypothesis is registered.",
            "Only after labels exist, extract trades-level features for newly supported symbols.",
        ],
    }


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    synth = payload["synthesis"]
    coverage = payload["current_coverage"]
    lines = [
        "# Orderflow Proxy Mapping Priority Audit",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        f"Registration verdict: `{payload['registration_verdict']}`",
        "",
        "## Summary",
        "",
        synth["summary"],
        "",
        "## Current Coverage",
        "",
        f"- Rows loaded: {payload['inputs']['rows_loaded']}",
        f"- Supported symbols: {coverage['supported_symbols']}",
        f"- Unsupported symbols: {coverage['unsupported_symbols']}",
        f"- Supported candidate counts: {coverage['supported_candidate_counts']}",
        f"- Unsupported candidate counts: {coverage['unsupported_candidate_counts']}",
        f"- Unsupported orderflow-relevant rows: {coverage['unsupported_orderflow_relevant_total']}",
        "",
        "## Priority Queue",
        "",
        "| Rank | Symbol | Proposed futures proxy | Candidates | Relevant rows | Relation | Complexity | Status |",
        "|---:|---|---|---:|---:|---|---|---|",
    ]
    for item in payload["priority_queue"]:
        lines.append(
            "| "
            f"{item['recommended_rank']} | {item['symbol']} | {', '.join(item['databento_symbols'])} | "
            f"{item['current_candidate_rows']} | {item['current_orderflow_relevant_rows']} | "
            f"{item['proxy_relation']} | {item['transform_complexity']} | {item['activation_status']} |"
        )
    lines.extend(["", "## Rank Rationale", ""])
    for item in payload["priority_queue"]:
        lines.append(f"- {item['symbol']}: {item['why_this_rank']}")
    lines.extend(["", "## Blocking Validations", ""])
    for item in payload["priority_queue"]:
        lines.append(f"### {item['symbol']}")
        for check in item["blocking_validations"]:
            lines.append(f"- {check}")
        lines.append("")
    lines.extend(
        [
            "## Validation Protocol",
            "",
            f"- Scope: {payload['validation_protocol']['scope']}",
            f"- Minimum first pull: {payload['validation_protocol']['minimum_first_pull']}",
            "",
            "Mandatory checks:",
            "",
            *[f"- {item}" for item in payload["validation_protocol"]["mandatory_checks"]],
            "",
            "Explicitly blocked:",
            "",
            *[f"- {item}" for item in payload["validation_protocol"]["explicitly_blocked"]],
            "",
            "## Synthesis",
            "",
            *[f"- {item}" for item in synth["readout"]],
            "",
            "## Ambiguity Ledger",
            "",
            *[f"- {item}" for item in synth["ambiguity_ledger"]],
            "",
            "## Opened Questions",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["opened_questions"], start=1)],
            "",
            "## Next Steps",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["next_steps"], start=1)],
            "",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = read_jsonl(args.source)
    payload = build_payload(rows, source_path=args.source)
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    unresolved = [
        item["symbol"]
        for item in payload["priority_queue"]
        if item["activation_status"] == "NOT_IN_FUTURES_PROXY_MAP"
    ]
    print(
        f"unsupported_candidates={payload['current_coverage']['unsupported_candidate_total']} "
        f"top_unresolved_proxy={unresolved[0] if unresolved else 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

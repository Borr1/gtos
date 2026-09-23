#!/usr/bin/env python3
"""Audit replay portability for the expanded-OOS research program.

Research/tooling only. This checks the current deterministic replay and
source-extraction tools before any expanded OOS outcome batch is opened.
It does not run a strategy outcome replay and does not change live logic.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DATE = "2026-05-03"
NO_PROMOTION = "NO_PROMOTION_VERDICT"

DEFAULT_OUTPUT_JSON = (
    ROOT / f"research/program_control/EXPANDED_OOS_REPLAY_PORTABILITY_AUDIT_{DATE}.json"
)
DEFAULT_OUTPUT_MD = (
    ROOT / f"research/program_control/EXPANDED_OOS_REPLAY_PORTABILITY_AUDIT_{DATE}.md"
)

ARG_RE = re.compile(r"add_argument\(\s*['\"](?P<arg>--[A-Za-z0-9][A-Za-z0-9_-]*)['\"]")


@dataclass(frozen=True)
class ToolSpec:
    tool_id: str
    path: str
    role: str
    required_args: tuple[str, ...]
    candidate_coverage: tuple[str, ...]
    evidence_classes: tuple[str, ...]
    current_scope: str
    portability_status: str
    blocker: str | None
    next_adapter: str | None


TOOL_SPECS = (
    ToolSpec(
        tool_id="SRC-MT5-OHLCV-EXPORT",
        path="scripts/export_mt5_research_ohlcv.py",
        role="MT5 OHLCV source exporter",
        required_args=("--symbol", "--timeframes", "--start", "--end", "--output-root", "--yes-live-readonly"),
        candidate_coverage=("source_inventory",),
        evidence_classes=("TRUE_TEMPORAL_OOS", "CROSS_INSTRUMENT_TRANSFER", "REGIME_TRANSFER"),
        current_scope="Can export broker OHLCV for exact MT5 symbols when terminal/history are available.",
        portability_status="PORTABLE_SOURCE_ADAPTER",
        blocker=None,
        next_adapter="Use source map symbol specs and register date slices before replay.",
    ),
    ToolSpec(
        tool_id="SRC-SIERRA-SCID",
        path="scripts/inspect_sierra_scid.py",
        role="Sierra .scid inventory/exporter",
        required_args=("--data-dir", "--pattern", "--inventory-json", "--export-file", "--start", "--end", "--export-csv"),
        candidate_coverage=("source_inventory", "source_transfer"),
        evidence_classes=("SAME_MARKET_SOURCE_TRANSFER", "FUTURES_PROXY_TRANSFER", "CROSS_INSTRUMENT_TRANSFER"),
        current_scope="Can inventory and slice Sierra intraday files; output is not yet a full GTOS replay data-root.",
        portability_status="PORTABLE_EXTRACTION_PARTIAL_REPLAY_ADAPTER",
        blocker="Bulk Sierra .scid to GTOS OHLCV data-root conversion is not implemented in this audit.",
        next_adapter="Add a bulk converter only after the first registered Sierra replay batch names symbol/date/timeframe slices.",
    ),
    ToolSpec(
        tool_id="REPLAY-V2-STRUCTURAL",
        path="scripts/run_raw_ohlc_path_scaling_v2_levels.py",
        role="V2/J46 structural path replay runner",
        required_args=("--data-dir", "--start", "--end", "--max-events", "--write", "--output-root"),
        candidate_coverage=("CAND-001-J46-J49-LIVE-BASELINE", "CAND-002-V2-OB-BOUNDARY", "CAND-003-V2-FVG-PATH"),
        evidence_classes=("TRUE_TEMPORAL_OOS", "REGIME_TRANSFER", "CROSS_INSTRUMENT_TRANSFER"),
        current_scope="Can produce event logs for registered V2 variants from OHLCV roots; includes J46 baseline rows.",
        portability_status="PORTABLE_WITH_SPEC_AND_SYMBOL_GUARDS",
        blocker=(
            "Arbitrary new symbols require replay-spec/cohort/config support and GTOS-compatible OHLCV file naming. "
            "It cannot consume Sierra .scid or depth files directly."
        ),
        next_adapter="For first batch, use existing MT5 CSV roots; defer Sierra replay until CSV conversion is registered.",
    ),
    ToolSpec(
        tool_id="ANALYZE-V2-CONFLUENCE",
        path="scripts/analyze_raw_ohlc_path_scaling_v2_confluence_deepdive.py",
        role="V2 OB/FVG/Swing/Composite event-log analyzer",
        required_args=("--event-log", "--cost-key", "--output-json", "--output-md"),
        candidate_coverage=("CAND-002-V2-OB-BOUNDARY", "CAND-003-V2-FVG-PATH"),
        evidence_classes=("DISCOVERY_ONLY", "REGIME_TRANSFER"),
        current_scope="Portable across V2 event logs; not a raw-data replay runner.",
        portability_status="EVENT_LOG_PORTABLE",
        blocker="Requires a compatible V2 structural event log generated first.",
        next_adapter="Run only after a registered V2 event log exists for a new batch.",
    ),
    ToolSpec(
        tool_id="EVAL-V2B-PROSPECTIVE",
        path="scripts/evaluate_raw_ohlc_path_scaling_v2b_prospective.py",
        role="V2b OB-boundary prospective evaluator",
        required_args=("--spec", "--event-log", "--runner-summary-json", "--cutoff", "--cost-key"),
        candidate_coverage=("CAND-002-V2-OB-BOUNDARY",),
        evidence_classes=("TRUE_TEMPORAL_OOS", "FORWARD_SHADOW"),
        current_scope="Event-log portable, with explicit cutoff and blocked-state ladder.",
        portability_status="EVENT_LOG_PORTABLE_WITH_CUTOFF",
        blocker="Needs resolved post-cutoff OB-boundary/J46 pairs; current goal must not call unresolved or same-slice rows validation.",
        next_adapter="For every new batch, write opened/burned slice metadata and cutoff before evaluating.",
    ),
    ToolSpec(
        tool_id="PREFILL-PATH-COVERAGE",
        path="scripts/build_raw_ohlc_prefill_delivery_path.py",
        role="Pre-fill path coverage harness",
        required_args=("--event-log", "--data-root", "--pending-expiry-bars", "--output-json", "--output-jsonl"),
        candidate_coverage=("CAND-004-V3-FVG-ONLY-RESCUE", "execution_lifecycle_research"),
        evidence_classes=("DISCOVERY_ONLY", "FORWARD_SHADOW"),
        current_scope="Reconstructs pre-fill path coverage from event log plus OHLCV roots; does not score strategy.",
        portability_status="PORTABLE_WITH_OHLCV_ROOTS",
        blocker="Original POI bounds and true broker lifecycle states are still absent.",
        next_adapter="Use as coverage support only; do not score delivery-leg logic without lifecycle telemetry.",
    ),
    ToolSpec(
        tool_id="REPLAY-V3-RISK-BANK",
        path="scripts/analyze_raw_ohlc_path_scaling_v3_exploratory.py",
        role="V3 reentry/risk-bank exploratory replay",
        required_args=("--event-log", "--variant-spec", "--data-root", "--cost-key", "--output-json"),
        candidate_coverage=("CAND-004-V3-FVG-ONLY-RESCUE",),
        evidence_classes=("DISCOVERY_ONLY", "TRUE_TEMPORAL_OOS"),
        current_scope="Can replay pre-registered V3 variants from compatible V2 event logs and OHLCV roots.",
        portability_status="EVENT_LOG_AND_OHLCV_PORTABLE_DISCOVERY_ONLY",
        blocker="Depends on V2 structural lock metadata; no direct arbitrary-symbol runner without V2 event generation first.",
        next_adapter="After V2 batch generation, run only frozen V3_FVG_ONLY_RESCUE first; keep other V3 variants diagnostic.",
    ),
    ToolSpec(
        tool_id="ORDERFLOW-NAS100-CACHED",
        path="scripts/analyze_orderflow_nas100_cached_feature_forensics.py",
        role="NAS100 cached MBO/MBP-10 feature stability analyzer",
        required_args=("--mbo-json", "--mbp10-json", "--output-json", "--output-md"),
        candidate_coverage=("CAND-005-NAS100-DEPTH-THINNESS",),
        evidence_classes=("FUTURES_PROXY_TRANSFER", "DISCOVERY_ONLY"),
        current_scope="Reads existing NAS100 JSON feature artifacts only; no data fetch.",
        portability_status="NAS100_CACHED_ONLY_NOT_ARBITRARY",
        blocker="Not portable to Sierra depth files or other symbols until a Sierra/Databento parity feature extractor exists.",
        next_adapter="Build Sierra depth parity extractor for one registered NQ/MNQ window before broad first-wave depth claims.",
    ),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: str | Path, root: Path = ROOT) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)


def extract_cli_args(script_path: Path) -> set[str]:
    if not script_path.exists():
        return set()
    text = script_path.read_text(encoding="utf-8", errors="replace")
    return {match.group("arg") for match in ARG_RE.finditer(text)}


def audit_tool(spec: ToolSpec, repo_root: Path = ROOT) -> dict[str, Any]:
    path = repo_root / spec.path
    found_args = extract_cli_args(path)
    missing_args = sorted(set(spec.required_args) - found_args)
    exists = path.exists()
    if not exists:
        readiness = "MISSING_TOOL"
    elif missing_args:
        readiness = "PARTIAL_CLI_CONTRACT"
    else:
        readiness = "CLI_CONTRACT_PRESENT"
    return {
        "tool_id": spec.tool_id,
        "path": spec.path,
        "exists": exists,
        "role": spec.role,
        "required_args": list(spec.required_args),
        "found_required_args": sorted(set(spec.required_args) & found_args),
        "missing_required_args": missing_args,
        "all_cli_args_found": sorted(found_args),
        "readiness": readiness,
        "candidate_coverage": list(spec.candidate_coverage),
        "evidence_classes": list(spec.evidence_classes),
        "current_scope": spec.current_scope,
        "portability_status": spec.portability_status,
        "blocker": spec.blocker,
        "next_adapter": spec.next_adapter,
    }


def build_payload(repo_root: Path = ROOT) -> dict[str, Any]:
    tools = [audit_tool(spec, repo_root=repo_root) for spec in TOOL_SPECS]
    by_status: dict[str, int] = {}
    for row in tools:
        by_status[row["portability_status"]] = by_status.get(row["portability_status"], 0) + 1
    blockers = [
        {
            "tool_id": row["tool_id"],
            "blocker": row["blocker"],
            "trigger": row["next_adapter"],
        }
        for row in tools
        if row.get("blocker")
    ]
    return {
        "schema_version": "expanded_oos_replay_portability_audit_v1",
        "generated_at_utc": utc_now(),
        "date": DATE,
        "scope": "research/tooling only",
        "promotion_verdict": NO_PROMOTION,
        "registered_before_outcome_batches": True,
        "outcome_batches_opened_by_this_audit": 0,
        "summary": {
            "tools_audited": len(tools),
            "cli_contract_present": sum(row["readiness"] == "CLI_CONTRACT_PRESENT" for row in tools),
            "partial_cli_contract": sum(row["readiness"] == "PARTIAL_CLI_CONTRACT" for row in tools),
            "missing_tools": sum(row["readiness"] == "MISSING_TOOL" for row in tools),
            "portability_status_counts": by_status,
        },
        "tools": tools,
        "blocker_ledger": blockers,
        "first_batch_recommendation": {
            "status": "REGISTERED_NEXT_BATCH_NOT_YET_OPENED",
            "recommended_start": (
                "Use MT5 CSV roots first for same-source temporal/regime replay because V2/J46 tools already "
                "consume OHLCV data roots. Defer Sierra .scid/.depth outcome replay until a named converter/parity "
                "adapter is registered."
            ),
            "do_not_start_with": [
                "broad Sierra depth replay without parity extractor",
                "cross-instrument transfer framed as validation",
                "V3 directly on Sierra/depth without V2 event logs",
                "Component 3B or AI replay",
            ],
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True).replace("|", r"\|")
    return str(value).replace("|", r"\|")


def table(headers: list[str], rows: Iterable[Iterable[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(item) for item in row) + " |")
    return lines


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Expanded OOS Replay Portability Audit",
        "",
        f"Date: {DATE}",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Summary",
        "",
        *table(
            ["Metric", "Value"],
            [
                ["tools audited", summary["tools_audited"]],
                ["CLI contract present", summary["cli_contract_present"]],
                ["partial CLI contract", summary["partial_cli_contract"]],
                ["missing tools", summary["missing_tools"]],
                ["outcome batches opened", payload["outcome_batches_opened_by_this_audit"]],
            ],
        ),
        "",
        "## Tool Matrix",
        "",
        *table(
            [
                "Tool",
                "Role",
                "Readiness",
                "Portability",
                "Candidates",
                "Evidence classes",
                "Missing args",
                "Blocker",
            ],
            [
                [
                    row["tool_id"],
                    row["role"],
                    row["readiness"],
                    row["portability_status"],
                    ", ".join(row["candidate_coverage"]),
                    ", ".join(row["evidence_classes"]),
                    ", ".join(row["missing_required_args"]),
                    row["blocker"],
                ]
                for row in payload["tools"]
            ],
        ),
        "",
        "## Blocker Ledger",
        "",
        *table(
            ["Tool", "Blocker", "Trigger / next adapter"],
            [
                [row["tool_id"], row["blocker"], row["trigger"]]
                for row in payload["blocker_ledger"]
            ],
        ),
        "",
        "## First Batch Recommendation",
        "",
        payload["first_batch_recommendation"]["recommended_start"],
        "",
        "Do not start with:",
        "",
        *[f"- {item}" for item in payload["first_batch_recommendation"]["do_not_start_with"]],
        "",
        "## Interpretation",
        "",
        "- Existing V2/J46 and V3 tooling is portable across compatible OHLCV roots and V2 event logs, not directly across every source format.",
        "- Sierra .scid and .depth are source-ready, but Sierra outcome replay needs a registered conversion/parity adapter before claims.",
        "- NAS100 orderflow remains diagnostic and source/proxy-transfer only; actual broker-R coverage remains the promotion blocker.",
        "- This audit opened no outcome slice and does not alter live trading behavior.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(repo_root=args.repo_root)
    write_json(args.output_json, payload)
    write_markdown(args.output_md, payload)
    print(f"wrote {rel(args.output_json)}")
    print(f"wrote {rel(args.output_md)}")
    print(
        f"tools={payload['summary']['tools_audited']} "
        f"cli_present={payload['summary']['cli_contract_present']} "
        f"opened={payload['outcome_batches_opened_by_this_audit']} "
        f"promotion={payload['promotion_verdict']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

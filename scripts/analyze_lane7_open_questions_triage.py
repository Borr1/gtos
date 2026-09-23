#!/usr/bin/env python3
"""Lane 7 recurring/open-question triage.

Research/tooling only. This closes or classifies the remaining unblocked
queue tail from local evidence. It does not change live trading logic,
prompts, risk settings, or execution behavior.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

DEFAULT_OUTPUT_JSON = "research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.json"
DEFAULT_OUTPUT_MD = "research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md"


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def latest_file(root: Path, pattern: str) -> Path | None:
    files = sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime if p.exists() else 0)
    return files[-1] if files else None


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def dsr_inventory(root: Path) -> dict[str, Any]:
    dsr = load_json(root / "research" / "ml_program" / "audit" / "dsr_diagnostics.json") or {}
    rows = dsr.get("rows") or []
    verdict_counts = Counter(str(row.get("verdict") or "missing") for row in rows)
    methodology = load_json(
        root / "research" / "ml_program" / "audit" / "METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.json"
    ) or {}
    summary = methodology.get("summary") or {}
    return {
        "audit_date": dsr.get("audit_date"),
        "rows": len(rows),
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "noise_ceiling_input_N": dsr.get("noise_ceiling_input_N"),
        "expected_max_SR_at_N200": dsr.get("expected_max_SR_at_N200"),
        "promotion_p_value_allowed_count": summary.get("promotion_p_value_allowed_count"),
        "trial_budget_example": summary.get("trial_budget_example"),
        "methodology_gate_summary": summary,
    }


def decay_inventory(root: Path) -> dict[str, Any]:
    ob_rows = read_csv(root / "shadow_logs" / "ob_continuation_daily.csv")
    latest_date = max((row.get("date_utc") or "" for row in ob_rows), default="")
    latest_rows = [row for row in ob_rows if row.get("date_utc") == latest_date]
    latest_by_scope = {
        str(row.get("scope")): {
            "rate_pct": float(row.get("rate_pct") or 0.0),
            "total_count": int(float(row.get("total_count") or 0)),
            "alarm_fired": str(row.get("alarm_fired")).lower() == "true",
            "insufficient_sample": str(row.get("insufficient_sample")).lower() == "true",
        }
        for row in latest_rows
    }
    monthly_report = root / "research" / "monthly_decay_monitor" / "2026-04_report.md"
    return {
        "ob_continuation_rows": len(ob_rows),
        "latest_ob_date": latest_date,
        "latest_ob_scopes": latest_by_scope,
        "latest_alarm_count": sum(1 for row in latest_rows if str(row.get("alarm_fired")).lower() == "true"),
        "monthly_decay_report_exists": monthly_report.exists(),
        "monthly_decay_report": str(monthly_report),
    }


def fred_month_summary(root: Path, series_id: str, month: str) -> dict[str, Any]:
    fred_root = root / "data" / "external" / "normalized" / "fred"
    latest = latest_file(fred_root, f"{series_id}_observations_*.jsonl")
    rows = read_jsonl(latest) if latest else []
    values = [
        float(row["value"])
        for row in rows
        if str(row.get("observation_date", "")).startswith(month)
        and isinstance(row.get("value"), (int, float))
    ]
    all_values = [float(row["value"]) for row in rows if isinstance(row.get("value"), (int, float))]
    percentile = None
    if values and all_values:
        month_mean = mean(values)
        percentile = sum(1 for value in all_values if value <= month_mean) / len(all_values)
    return {
        "latest_file": str(latest) if latest else None,
        "n_month": len(values),
        "month_mean": mean(values) if values else None,
        "sample_min": min(values) if values else None,
        "sample_max": max(values) if values else None,
        "mean_percentile_vs_cached_history": percentile,
    }


def path9_inventory(root: Path) -> dict[str, Any]:
    lane2 = load_json(
        root
        / "research"
        / "phase_3_external_feed_validation"
        / "LANE2_C7_C9_PATH_SCALING_TRIAGE_2026-05-03.json"
    ) or {}
    path9 = lane2.get("c7_path9_deep_dive") or {}
    fred = {
        series_id: fred_month_summary(root, series_id, "2026-02")
        for series_id in ("VIXCLS", "GVZCLS", "DGS10", "DGS2", "DFII10", "T10YIE", "DTWEXBGS")
    }
    return {"path9": path9, "feb_2026_fred": fred}


def source_inventory(root: Path) -> dict[str, Any]:
    normalized = root / "data" / "external" / "normalized"
    source_dirs = sorted(path.name for path in normalized.iterdir() if path.is_dir()) if normalized.exists() else []
    hkm_paths = [
        str(path)
        for path in normalized.rglob("*")
        if "hkm" in path.name.lower() or "he_kelly" in path.name.lower() or "intermediary" in path.name.lower()
    ] if normalized.exists() else []
    return {
        "normalized_sources": source_dirs,
        "hkm_or_intermediary_paths": hkm_paths[:20],
        "has_hkm_or_intermediary_source": bool(hkm_paths),
    }


def k54_inventory(root: Path) -> dict[str, Any]:
    lane5 = load_json(root / "research" / "ml_program" / "audit" / "LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.json") or {}
    v4_specialist = load_json(root / "research" / "ml_program" / "models" / "k54_v4" / "specialist_results.json") or {}
    v4_cross = load_json(root / "research" / "ml_program" / "models" / "k54_v4" / "cross_period_results.json") or {}
    return {
        "lane5_summary": lane5.get("evidence") or lane5.get("summary") or {},
        "specialist_results": v4_specialist,
        "cross_period_groups": ((v4_cross.get("recent_test") or {}).get("per_group") or {}),
    }


def ai_scaffold_inventory(root: Path) -> dict[str, Any]:
    primary_text = (root / "src" / "components" / "primary_analyzer.py").read_text(encoding="utf-8", errors="replace")
    orchestrator_text = (root / "src" / "components" / "orchestrator.py").read_text(encoding="utf-8", errors="replace")
    return {
        "adaptive_review_exists": (root / "src" / "components" / "adaptive_review.py").exists(),
        "f3_replay_engine_exists": (root / "src" / "research_infra" / "f3_replay_engine.py").exists(),
        "ai_tools_readme_exists": (root / "src" / "components" / "ai_tools" / "README.md").exists(),
        "primary_imports_ai_tools": "ai_tools" in primary_text,
        "orchestrator_imports_debate": "debate" in orchestrator_text.lower(),
        "debate_prompts_exist": all(
            (root / "src" / "prompts" / name).exists()
            for name in ("bull_agent_prompt.py", "bear_agent_prompt.py", "judge_prompt.py")
        ),
    }


def lambda_scan(root: Path) -> dict[str, Any]:
    targets = [root / "src", root / "config", root / "prompts"]
    files: list[Path] = []
    for target in targets:
        if target.exists():
            files.extend(path for path in target.rglob("*") if path.is_file() and path.suffix in {".py", ".yaml", ".yml", ".md", ".txt"})
    literal_lambda2: list[str] = []
    risk_ratio_hits: list[str] = []
    ratio_re = re.compile(r"(min_rr|tp1_distance_r|max_daily_loss_pct|risk_per_trade_pct|max_concurrent|risk_reward)", re.I)
    for path in files:
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            lower = line.lower()
            if "lambda" in lower and ("2.0" in lower or "=2" in lower or ": 2" in lower):
                literal_lambda2.append(f"{rel}:{lineno}:{line.strip()}")
            if ratio_re.search(line):
                risk_ratio_hits.append(f"{rel}:{lineno}:{line.strip()}")
    return {
        "literal_lambda_2_hits": literal_lambda2[:50],
        "literal_lambda_2_count": len(literal_lambda2),
        "risk_ratio_hit_count": len(risk_ratio_hits),
        "risk_ratio_hit_examples": risk_ratio_hits[:20],
        "risk_ratio_config_examples": [hit for hit in risk_ratio_hits if hit.startswith("config")][:20],
    }


def quantum_inventory(root: Path) -> dict[str, Any]:
    matches = [
        str(path.relative_to(root))
        for path in (root / "research").rglob("*")
        if "quantum" in path.name.lower()
    ] if (root / "research").exists() else []
    return {"local_quantum_files": matches[:30], "local_quantum_file_count": len(matches)}


def task_classifications(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    dsr = evidence["dsr"]
    decay = evidence["decay"]
    path9 = evidence["path9"]["path9"]
    k54 = evidence["k54"]
    ai = evidence["ai_scaffold"]
    lambda_hits = evidence["lambda_scan"]
    risk_ratio_examples = lambda_hits.get("risk_ratio_config_examples") or lambda_hits["risk_ratio_hit_examples"]
    hkm = evidence["sources"]
    quantum = evidence["quantum"]
    specialist = k54["specialist_results"]

    return [
        {
            "id": "RR-2",
            "status": "DONE",
            "blocked_by": "-",
            "note": (
                f"Current DSR/effective-N tracker snapshot has {dsr['rows']} DSR rows, "
                f"verdict counts {dsr['verdict_counts']}, and promotion-p-value allowed count "
                f"{dsr['promotion_p_value_allowed_count']}."
            ),
        },
        {
            "id": "RR-3",
            "status": "DONE",
            "blocked_by": "-",
            "note": (
                f"Current decay-alarm snapshot exists: ob_continuation latest date {decay['latest_ob_date']} "
                f"with {decay['latest_alarm_count']} alarms; monthly decay report exists="
                f"{decay['monthly_decay_report_exists']}."
            ),
        },
        {
            "id": "RR-4",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Requires the same dedicated current-web literature sweep deferred under RR-1.",
            "note": "Local killed-hypothesis and backlog artifacts are current, but this item specifically asks for new literature after failures.",
        },
        {
            "id": "RR-7",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Requires a current-web paper status/retraction watcher with source citations.",
            "note": "No local source can prove that no domain paper expired or was retracted.",
        },
        {
            "id": "U-1",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "Same blocker as M-5: full 2022-2023 v2/v3 feature catalog plus source-flagged supplemental old-label integration.",
            "note": "Current doctrine remains AFML/CPCV-honest; exact per-instrument Inoue-Kilian resolution is data-blocked.",
        },
        {
            "id": "U-12",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "Same blocker as A-8: no local CPI/PCE-deflated real-gold-price percentile construction.",
            "note": "Erb-Harvey remains a literature lens, not a locally validated decay attribution feature.",
        },
        {
            "id": "U-17",
            "status": "DONE",
            "blocked_by": "-",
            "note": (
                f"Path-9 is classified {path9.get('classification')} with February share "
                f"{path9.get('feb_2026_share')}, {path9.get('positive_group_count')}/"
                f"{path9.get('group_count')} groups positive, and fold-4 post-window AUC diff "
                f"{(path9.get('non_path_fold_rows') or [{}, {}, {}])[2].get('auc_diff')}."
            ),
        },
        {
            "id": "U-2",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "A-2/A-3 blockers: MT5 alone has no option dealer gamma sign, VIX1D/VIX9D, VRP, or official GEX source.",
            "note": "FlashAlpha Basic proxy data exists, but gamma sign is not constructible from MT5 OHLC/tick data alone.",
        },
        {
            "id": "U-4",
            "status": "DONE",
            "blocked_by": "-",
            "note": (
                "Per-instrument/group sweep is answered by K54 v3/v4 triage: global K54 failed; "
                "strongest remaining group is NAS_US30 specialist, with proxy AUC "
                f"{specialist.get('nas_us30_specialist_t7_proxy_auc')}, master NAS_US30 AUC "
                f"{specialist.get('master_global_nas_us30_auc')}, overall specialist delta "
                f"{specialist.get('specialist_delta_overall')}, and routing per-path delta "
                f"{specialist.get('nas_routing_per_path_delta_mean')}."
            ),
        },
        {
            "id": "U-6",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "Broker substrate lacks true trade count/depth; current tick files are retail quote ticks, not centralized trade prints.",
            "note": "Same substrate blocker as X-1/X-2/X-3; do not relabel quote-tick count as trade-count time.",
        },
        {
            "id": "U-9",
            "status": "DONE",
            "blocked_by": "-",
            "note": (
                f"Live config/code scan found {lambda_hits['literal_lambda_2_count']} literal lambda=2 hits. "
                f"Relevant risk/ratio knobs are config-driven; examples include {risk_ratio_examples[:3]}."
            ),
        },
        {
            "id": "L-3",
            "status": "FILED_FOR_APPROVAL",
            "blocked_by": "Reflexion/post-trade feedback loop would alter AI/adaptation behavior and needs CEO approval plus shadow-only design.",
            "note": f"AdaptiveReview exists={ai['adaptive_review_exists']}, but this is not a live Reflexion loop.",
        },
        {
            "id": "L-5",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Hybrid LLM+ML architecture depends on a surviving K55/K54 shadow candidate and approval for system-flow changes.",
            "note": "Current K54 global architectures failed; L-5 is a future architecture path, not an unblocked implementation.",
        },
        {
            "id": "RR-5",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Capacity-decay band re-evaluation needs actual AUM/capacity growth or venue-volume participation data.",
            "note": "Current live prop-account scale does not trigger capacity analysis.",
        },
        {
            "id": "RR-6",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Needs separately logged live edge return streams before an edge-correlation/diversification metric is meaningful.",
            "note": "Current alpha inventory is not enough to estimate a hypothesis-portfolio correlation matrix.",
        },
        {
            "id": "U-10",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Depends on L-1/L-2 tool-use grounding shadow implementation and approval path.",
            "note": f"Tool scaffolding exists={ai['ai_tools_readme_exists']}; PrimaryAnalyzer imports ai_tools={ai['primary_imports_ai_tools']}.",
        },
        {
            "id": "U-13",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Needs AUM/capacity trigger plus venue-volume or slippage/capacity data by instrument.",
            "note": "Same practical trigger as RR-5.",
        },
        {
            "id": "U-14",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Needs longer live history or a clean publication/crowding proxy panel; current OB-decay monitor is sample-limited.",
            "note": "Current monitor can observe decay, but does not validate McLean-Pontiff publication-decay rate on GTOS edge.",
        },
        {
            "id": "U-15",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Requires dedicated literature/book synthesis and translation into substrate-immune candidate specs.",
            "note": "Session-45 pivot references Renaissance-style candidates, but this item is not locally closed as a deep dive.",
        },
        {
            "id": "U-16",
            "status": "DEFERRED_WITH_TRIGGER",
            "blocked_by": "Depends on P-8: standalone sticky-HDP-HMM plus Kirby fat-tailed-mixture null-test harness.",
            "note": "No local HDP-HMM/Kirby-null harness has passed.",
        },
        {
            "id": "U-8",
            "status": "BLOCKED_WITH_REASON",
            "blocked_by": "No He-Kelly-Manela/intermediary-capital source, cache, or source contract exists locally.",
            "note": f"H-K-M/intermediary local source present={hkm['has_hkm_or_intermediary_source']}.",
        },
        *[
            {
                "id": item_id,
                "status": "DEFERRED_WITH_TRIGGER",
                "blocked_by": "No current GTOS classical-pipeline blocker requires quantum finance work; revisit only on explicit CEO request or after classical methods saturate.",
                "note": f"Local quantum-related research files found: {quantum['local_quantum_file_count']}.",
            }
            for item_id in ("Z-1", "Z-2", "Z-3", "Z-4")
        ],
    ]


def build_payload(root: Path) -> dict[str, Any]:
    evidence = {
        "dsr": dsr_inventory(root),
        "decay": decay_inventory(root),
        "path9": path9_inventory(root),
        "sources": source_inventory(root),
        "k54": k54_inventory(root),
        "ai_scaffold": ai_scaffold_inventory(root),
        "lambda_scan": lambda_scan(root),
        "quantum": quantum_inventory(root),
    }
    classifications = task_classifications(evidence)
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "scope": "research/tooling only",
        "question_registered_before_output": (
            "The remaining queue tail should resolve mostly as recurring control updates, "
            "local-evidence answers, approval-filed AI changes, or deferred/blocked literature, "
            "capacity, source, and quantum items."
        ),
        "evidence": evidence,
        "task_classifications": classifications,
        "status_counts": dict(sorted(Counter(row["status"] for row in classifications).items())),
    }


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: str | Path) -> None:
    evidence = payload["evidence"]
    lines = [
        "# Lane 7 Recurring/Open-Question Triage",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "Scope: research/tooling only",
        "Promotion verdict: `NO_PROMOTION_VERDICT`",
        "",
        "## Question Registered Before Output",
        "",
        payload["question_registered_before_output"],
        "",
        "## Evidence Inventory",
        "",
        f"- DSR rows: `{evidence['dsr']['rows']}`; verdict counts: `{evidence['dsr']['verdict_counts']}`; promotion-p-value allowed count: `{evidence['dsr']['promotion_p_value_allowed_count']}`.",
        f"- OB continuation latest date: `{evidence['decay']['latest_ob_date']}`; current alarm count: `{evidence['decay']['latest_alarm_count']}`; monthly decay report exists: `{evidence['decay']['monthly_decay_report_exists']}`.",
        f"- Path-9 classification: `{evidence['path9']['path9'].get('classification')}`; Feb share: `{evidence['path9']['path9'].get('feb_2026_share')}`.",
        f"- Normalized external sources: `{evidence['sources']['normalized_sources']}`; H-K-M/intermediary source present: `{evidence['sources']['has_hkm_or_intermediary_source']}`.",
        f"- AI scaffolding: `{evidence['ai_scaffold']}`.",
        f"- Literal lambda=2 code/config hits: `{evidence['lambda_scan']['literal_lambda_2_count']}`.",
        f"- Local quantum-related files: `{evidence['quantum']['local_quantum_file_count']}`.",
        "",
        "## FRED Feb-2026 Context Snapshot",
        "",
        "| series | n | mean | min | max | percentile vs cached history |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for series_id, row in evidence["path9"]["feb_2026_fred"].items():
        lines.append(
            "| {series} | {n} | {mean} | {mn} | {mx} | {pct} |".format(
                series=series_id,
                n=row["n_month"],
                mean=row["month_mean"],
                mn=row["sample_min"],
                mx=row["sample_max"],
                pct=row["mean_percentile_vs_cached_history"],
            )
        )
    lines.extend(
        [
            "",
            "## Classification Matrix",
            "",
            "| ID | Status | Blocked By | Evidence / Note |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in payload["task_classifications"]:
        lines.append(f"| {row['id']} | {row['status']} | {row['blocked_by']} | {row['note']} |")
    lines.extend(
        [
            "",
            "## NO_PROMOTION_VERDICT",
            "",
            "This triage does not validate or promote a trading rule, live filter, risk setting, prompt, or execution change.",
        ]
    )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args()

    payload = build_payload(Path(args.root).resolve())
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(json.dumps(payload["status_counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

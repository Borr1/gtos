#!/usr/bin/env python3
"""Build alternate-source scoring rows for source-repair reachability."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_alternate_source_scoring import (
    EXPANDED_MARKET_ALTERNATE_SOURCE_SCORING,
    alternate_source_scoring_row,
    boundary_row,
    issue_rows,
    research_boundary,
)
from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_REPAIR_REACH"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_ALT_SOURCE_SCORE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_ROW_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_alternate_source_scoring.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_alternate_source_scoring_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"
ACTIVE_LEDGER = ROUTE_DIR / "ABSOLUTE_NORTH_STAR_ACTIVE_DOCTRINE_LEDGER_2026-05-15.md"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def output_sha256(paths: list[Path]) -> dict[str, str]:
    digest: dict[str, str] = {}
    for path in paths:
        hasher = hashlib.sha256()
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        digest[path.name] = hasher.hexdigest()
    return digest


def aggregate_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(row.get("alternate_source_scoring_class") or ""),
        str(row.get("action_class") or ""),
        str(row.get("symbol_family") or ""),
        str(row.get("market_timeframe") or ""),
        str(row.get("route_session") or ""),
        str(row.get("horizon_id") or ""),
        str(row.get("side") or ""),
    )


def empty_bucket() -> dict[str, Any]:
    return {
        "row_count": 0,
        "scored_rows": 0,
        "missing_rows": 0,
        "score_sum": 0.0,
        "observed_sum": 0.0,
        "observed_count": 0,
        "effective_n_sum": 0,
        "deconcentrated_effective_n_sum": 0.0,
        "win_count": 0,
        "loss_count": 0,
        "zero_count": 0,
        "target_first_count": 0,
        "stop_first_count": 0,
        "neither_count": 0,
        "ambiguous_count": 0,
        "source_paths": set(),
        "decisions": Counter(),
    }


def update_bucket(bucket: dict[str, Any], row: dict[str, Any]) -> None:
    bucket["row_count"] += 1
    score = as_float(row.get("alternate_source_proxy_cost_adjusted_simulated_r"))
    if score is None:
        bucket["missing_rows"] += 1
    else:
        bucket["scored_rows"] += 1
        bucket["score_sum"] += score
    observed = as_float(row.get("observed_deconcentrated_cost_adjusted_simulated_r"))
    if observed is not None:
        bucket["observed_sum"] += observed
        bucket["observed_count"] += 1
    bucket["effective_n_sum"] += int(row.get("effective_n") or 0)
    bucket["deconcentrated_effective_n_sum"] += float(row.get("deconcentrated_effective_n") or 0.0)
    for field in ("win_count", "loss_count", "zero_count", "target_first_count", "stop_first_count", "neither_count", "ambiguous_count"):
        bucket[field] += int(row.get(field) or 0)
    bucket["source_paths"].add(str(row.get("source_path") or ""))
    bucket["decisions"][row.get("keep_kill_redesign_implement_decision")] += 1


def aggregate_rows_from_buckets(buckets: dict[tuple[str, ...], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(buckets):
        bucket = buckets[key]
        rows.append(
            boundary_row(
                {
                    "expanded_market_alternate_source_scoring_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-ALT-SOURCE-SCORE-AGG-{len(rows) + 1:06d}"
                    ),
                    "alternate_source_scoring_class": key[0],
                    "action_class": key[1],
                    "symbol_family": key[2],
                    "market_timeframe": key[3],
                    "route_session": key[4],
                    "horizon_id": key[5],
                    "side": key[6],
                    "row_count": bucket["row_count"],
                    "scored_rows": bucket["scored_rows"],
                    "missing_rows": bucket["missing_rows"],
                    "alternate_source_proxy_expectancy_cost_adjusted_simulated_r": rounded(
                        bucket["score_sum"] / bucket["scored_rows"] if bucket["scored_rows"] else None
                    ),
                    "observed_deconcentrated_expectancy_cost_adjusted_simulated_r": rounded(
                        bucket["observed_sum"] / bucket["observed_count"] if bucket["observed_count"] else None
                    ),
                    "effective_n_sum": bucket["effective_n_sum"],
                    "deconcentrated_effective_n_sum": rounded(bucket["deconcentrated_effective_n_sum"]),
                    "win_count": bucket["win_count"],
                    "loss_count": bucket["loss_count"],
                    "zero_count": bucket["zero_count"],
                    "target_first_count": bucket["target_first_count"],
                    "stop_first_count": bucket["stop_first_count"],
                    "neither_count": bucket["neither_count"],
                    "ambiguous_count": bucket["ambiguous_count"],
                    "source_path_count": len(bucket["source_paths"]),
                    "decision_counts": dict(sorted(bucket["decisions"].items())),
                    "keep_kill_redesign_implement_decision": bucket["decisions"].most_common(1)[0][0],
                }
            )
        )
    return rows


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = [
        (RESULT_PATH, "expanded_market_alternate_source_scoring_result"),
        (ROW_LEDGER, "expanded_market_alternate_source_scoring_rows"),
        (AGGREGATE_LEDGER, "expanded_market_alternate_source_scoring_aggregates"),
        (ISSUE_LEDGER, "expanded_market_alternate_source_scoring_issues"),
        (SYSTEM_LEDGER, "expanded_market_alternate_source_scoring_system"),
        (SUMMARY_PATH, "expanded_market_alternate_source_scoring_summary"),
        (BUILDER_MODULE, "expanded_market_alternate_source_scoring_builder"),
        (VERIFIER_MODULE, "expanded_market_alternate_source_scoring_verifier"),
        (HELPER_MODULE, "expanded_market_alternate_source_scoring_helper"),
        (TEST_MODULE, "expanded_market_alternate_source_scoring_tests"),
    ]
    rows = [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]
    existing = manifest.setdefault("artifacts", [])
    types = {row["type"] for row in rows}
    manifest["artifacts"] = [row for row in existing if row.get("type") not in types] + rows
    manifest["latest_expanded_market_alternate_source_scoring"] = {
        "generated_utc": generated_at,
        "files": rows,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def replace_sprint_event(event: dict[str, Any]) -> None:
    kept_lines: list[str] = []
    if SPRINT_LEDGER.exists():
        with open(long_path(SPRINT_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    kept_lines.append(line.rstrip("\n"))
                    continue
                if row.get("event") == event.get("event"):
                    continue
                kept_lines.append(json.dumps(row, sort_keys=True))
    kept_lines.append(json.dumps(event, sort_keys=True))
    write_text(SPRINT_LEDGER, "\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 254 - Expanded-Market Alternate-Source Scoring"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 253. Source-repair rows with alternate source paths were scored using alternate observed deconcentrated proxy R; source-expansion and weak-edge rows remain exact missing-field proof.

Rows:
- input reachability rows: {counts["input_reachability_rows"]}
- alternate-source scoring rows: {counts["alternate_source_scoring_rows"]}
- scored rows: {counts["scored_rows"]}
- missing rows: {counts["missing_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: turn positive alternate-source repair rows into implementation-priority rows and preserve nonpositive/weak/missing rows as numeric kill/redesign evidence.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any], result: dict[str, Any]) -> str:
    return f"""# Expanded-Market Alternate-Source Scoring

Generated: {generated_at}

## Outputs

- Alternate-source scoring rows: `{counts["alternate_source_scoring_rows"]}`
- Scored rows: `{counts["scored_rows"]}`
- Missing rows: `{counts["missing_rows"]}`
- Aggregate rows: `{counts["aggregate_rows"]}`
- Issue rows: `{counts["issue_rows"]}`

## Result

- ok: `{result["ok"]}`
- issues: `{result["issues"]}`
"""


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    buckets: dict[tuple[str, ...], dict[str, Any]] = defaultdict(empty_bucket)
    scoring_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    source_paths: set[str] = set()
    symbol_families: set[str] = set()
    issues: list[dict[str, Any]] = []
    row_count = 0
    with open(long_path(ROW_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        for row_count, source_row in enumerate(iter_jsonl(INPUT_ROW_LEDGER), 1):
            row = alternate_source_scoring_row(source_row, row_count)
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            scoring_counts[row.get("alternate_source_scoring_class")] += 1
            decision_counts[row.get("keep_kill_redesign_implement_decision")] += 1
            source_paths.add(str(row.get("source_path") or ""))
            symbol_families.add(str(row.get("symbol_family") or ""))
            update_bucket(buckets[aggregate_key(row)], row)
            issues.extend(issue_rows([row]))
    aggregate_rows = aggregate_rows_from_buckets(buckets)
    scored_rows = sum(bucket["scored_rows"] for bucket in buckets.values())
    missing_rows = sum(bucket["missing_rows"] for bucket in buckets.values())
    system_rows = [
        boundary_row(
            {
                "expanded_market_alternate_source_scoring_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-ALT-SOURCE-SCORE-SYSTEM-0001"
                ),
                "alternate_source_scoring_rows": row_count,
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issues),
                "scored_rows": scored_rows,
                "missing_rows": missing_rows,
                "scoring_class_counts": dict(sorted(scoring_counts.items())),
                "decision_counts": dict(sorted(decision_counts.items())),
                "source_path_count": len(source_paths),
                "symbol_family_count": len(symbol_families),
                "metadata": {
                    "input_reachability_result_ok": input_result.get("ok"),
                    "alternate_positive_threshold": 0.05,
                },
            }
        )
    ]
    counts = {
        "input_reachability_rows": row_count,
        "alternate_source_scoring_rows": row_count,
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issues),
        "scored_rows": scored_rows,
        "missing_rows": missing_rows,
        "scoring_class_counts": dict(sorted(scoring_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "source_path_count": len(source_paths),
        "symbol_family_count": len(symbol_families),
        "system_rows": len(system_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": not issues,
        "issues": issues,
        "expanded_market_alternate_source_scoring_surface": EXPANDED_MARKET_ALTERNATE_SOURCE_SCORING,
        "research_boundary": research_boundary(),
        "inputs": {
            "source_repair_reachability_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "source_repair_reachability_rows": str(INPUT_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "row_ledger": str(ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "counts": counts,
    }
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(generated_at, counts, result))
    result["output_sha256"] = output_sha256([ROW_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH])
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "event": "checkpoint_254_expanded_market_alternate_source_scoring",
            "generated_utc": generated_at,
            "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
            "counts": counts,
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": result["ok"], "counts": counts}, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

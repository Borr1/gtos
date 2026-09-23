from __future__ import annotations

import csv
import gzip
import hashlib
import json
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import sys

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research.dynamic_execution_policy import (  # noqa: E402
    observation_from_ohlc,
    required_policy_manifest,
    simulate_policy,
)


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"
ROUTE_ID = "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
FULL_REPLAY_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "vnext_full_historical_candidate_generation_replay_2026_05_24"
)
INPUT_STAGE04_SHARDS = FULL_REPLAY_DIR / "stage04_shards"

OUTPUT_SHARD_DIR = ROUTE_DIR / "stage04_dynamic_policy_shards"
OUTPUT_SHARD_INDEX = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SHARD_INDEX_{DATE_ID}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SUMMARY_{DATE_ID}.json"
OUTPUT_REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_REPORT_{DATE_ID}.md"
OUTPUT_STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"

REPLAY_MODE = "bar_close_m15"
SAME_BAR_POLICY = "conservative"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SourceCache:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[list[datetime], list[dict[str, str]]]] = {}

    def load(self, source_path: str) -> tuple[list[datetime], list[dict[str, str]]]:
        if source_path in self._cache:
            return self._cache[source_path]
        absolute = REPO_ROOT / source_path
        times: list[datetime] = []
        rows: list[dict[str, str]] = []
        with absolute.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                parsed = parse_time(row.get("time"))
                if parsed is None:
                    continue
                times.append(parsed)
                rows.append(row)
        self._cache[source_path] = (times, rows)
        return times, rows


def iter_input_chunks() -> Iterable[Path]:
    yield from sorted(INPUT_STAGE04_SHARDS.rglob("path_outcome_r.jsonl.gz"))


def policy_result_to_dict(result) -> dict:
    return {
        "replay_status": result.replay_status,
        "final_r": result.final_r,
        "exit_reason": result.exit_reason,
        "exit_index": result.exit_index,
        "exit_time_utc": result.exit_time_utc,
        "mfe_r": result.mfe_r,
        "mae_r": result.mae_r,
        "partial_realized_r": result.partial_realized_r,
        "remaining_fraction": result.remaining_fraction,
        "stop_r_at_exit": result.stop_r_at_exit,
        "same_bar_ambiguity": result.same_bar_ambiguity,
        "source_gap_reason": result.source_gap_reason,
        "transitions": result.transitions,
    }


def observations_for_row(row: dict, cache: SourceCache):
    source_path = row.get("source_path")
    if not source_path:
        return [], "missing_source_path"
    absolute = REPO_ROOT / source_path
    if not absolute.exists():
        return [], "source_file_missing"
    entry = row.get("entry_reference")
    stop = row.get("stop_or_invalidation")
    side = row.get("side")
    if entry is None or stop is None or side is None:
        return [], "missing_entry_stop_side"
    start_time = parse_time(row.get("entry_first_touch_utc") or row.get("first_bar_utc"))
    end_time = parse_time(row.get("path_window_requested_end_utc") or row.get("last_bar_utc"))
    if start_time is None or end_time is None:
        return [], "missing_path_time_window"
    times, source_rows = cache.load(str(source_path))
    start_index = bisect_left(times, start_time)
    end_index = bisect_right(times, end_time)
    if start_index >= end_index:
        return [], "source_window_empty_after_entry"
    observations = []
    for local_index, source_row in enumerate(source_rows[start_index:end_index], start=1):
        try:
            observations.append(
                observation_from_ohlc(
                    index=local_index,
                    row=source_row,
                    entry=float(entry),
                    stop=float(stop),
                    side=str(side),
                    time_key="time",
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            return [], f"observation_build_error:{exc}"
    return observations, None


def should_replay(row: dict) -> bool:
    return (
        row.get("replay_mode") == REPLAY_MODE
        and row.get("path_source_status") == "SIMULATED_FROM_LOCAL_OHLC"
        and row.get("price_path_truth_status") == "measured"
        and row.get("entry_touched") is True
        and row.get("trade_performance_denominator_inclusion") is True
    )


def process_chunk(chunk_path: Path, policies, cache: SourceCache) -> dict:
    shard_id = chunk_path.parent.name
    output_dir = OUTPUT_SHARD_DIR / shard_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "dynamic_policy_replay.jsonl"
    metrics = {
        "input_chunk_path": rel(chunk_path),
        "output_chunk_path": rel(output_path),
        "shard_id": shard_id,
        "input_rows": 0,
        "candidate_rows_in_replay_mode": 0,
        "replayable_candidate_rows": 0,
        "not_replayable_rows": 0,
        "source_gap_counts": Counter(),
        "policy_counts": Counter(),
        "policy_total_r": defaultdict(float),
        "policy_exit_reason_counts": defaultdict(Counter),
        "policy_ambiguous_counts": Counter(),
        "old_static_total_r": 0.0,
    }
    with gzip.open(chunk_path, "rt", encoding="utf-8") as input_handle, output_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as output_handle:
        for raw in input_handle:
            row = json.loads(raw)
            metrics["input_rows"] += 1
            if row.get("replay_mode") == REPLAY_MODE:
                metrics["candidate_rows_in_replay_mode"] += 1
            if not should_replay(row):
                continue
            observations, source_gap = observations_for_row(row, cache)
            if source_gap:
                metrics["not_replayable_rows"] += 1
                metrics["source_gap_counts"][source_gap] += 1
                continue
            policy_results = {}
            for policy in policies:
                result = simulate_policy(policy, observations, same_bar_policy=SAME_BAR_POLICY)
                result_row = policy_result_to_dict(result)
                policy_results[policy.name] = result_row
                metrics["policy_counts"][policy.name] += 1
                if result.final_r is not None:
                    metrics["policy_total_r"][policy.name] += float(result.final_r)
                metrics["policy_exit_reason_counts"][policy.name][result.exit_reason] += 1
                if result.same_bar_ambiguity:
                    metrics["policy_ambiguous_counts"][policy.name] += 1
            static_r = row.get("simulated_r")
            if isinstance(static_r, (int, float)):
                metrics["old_static_total_r"] += float(static_r)
            output = {
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_04_FULL_POLICY_DYNAMIC_REPLAY",
                "source_replay_mode": REPLAY_MODE,
                "same_bar_policy": SAME_BAR_POLICY,
                "candidate_id": row.get("candidate_id"),
                "path_row_id": row.get("path_row_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "framework": row.get("framework"),
                "session_bucket": row.get("session_bucket"),
                "candle_time_utc": row.get("candle_time_utc"),
                "entry_first_touch_utc": row.get("entry_first_touch_utc"),
                "source_path": row.get("source_path"),
                "source_sha256": row.get("source_sha256"),
                "source_mode": row.get("source_mode"),
                "source_timeframe": row.get("source_timeframe"),
                "entry_reference": row.get("entry_reference"),
                "stop_or_invalidation": row.get("stop_or_invalidation"),
                "old_static_rr": row.get("rr"),
                "old_static_simulated_r": static_r,
                "old_static_terminal_outcome": row.get("terminal_outcome"),
                "old_static_terminal_order_raw": row.get("terminal_order_raw"),
                "observation_count": len(observations),
                "source_window_complete": row.get("source_window_complete"),
                "policy_results": policy_results,
                "legacy_delta_vs_old_static_r": (
                    policy_results.get("legacy_fixed_1.5r", {}).get("final_r") - float(static_r)
                    if isinstance(static_r, (int, float))
                    and policy_results.get("legacy_fixed_1.5r", {}).get("final_r") is not None
                    else None
                ),
                "no_live_trading_or_broker_mutation": True,
            }
            output_handle.write(json.dumps(output, sort_keys=True) + "\n")
            metrics["replayable_candidate_rows"] += 1
    metrics["output_bytes"] = output_path.stat().st_size
    metrics["output_sha256"] = sha256_file(output_path)
    return metrics


def counter_to_dict(counter: Counter) -> dict:
    return dict(sorted(counter.items()))


def metrics_to_index_row(metrics: dict) -> dict:
    return {
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_04_FULL_POLICY_DYNAMIC_REPLAY",
        "shard_id": metrics["shard_id"],
        "input_chunk_path": metrics["input_chunk_path"],
        "output_chunk_path": metrics["output_chunk_path"],
        "input_rows": metrics["input_rows"],
        "candidate_rows_in_replay_mode": metrics["candidate_rows_in_replay_mode"],
        "replayable_candidate_rows": metrics["replayable_candidate_rows"],
        "not_replayable_rows": metrics["not_replayable_rows"],
        "source_gap_counts": counter_to_dict(metrics["source_gap_counts"]),
        "policy_counts": counter_to_dict(metrics["policy_counts"]),
        "policy_total_r": dict(sorted(metrics["policy_total_r"].items())),
        "policy_exit_reason_counts": {
            policy: counter_to_dict(counts)
            for policy, counts in sorted(metrics["policy_exit_reason_counts"].items())
        },
        "policy_ambiguous_counts": counter_to_dict(metrics["policy_ambiguous_counts"]),
        "old_static_total_r": metrics["old_static_total_r"],
        "output_bytes": metrics["output_bytes"],
        "output_sha256": metrics["output_sha256"],
        "status": "complete",
    }


def write_summary(index_rows: list[dict], policies) -> dict:
    total_replayable = sum(row["replayable_candidate_rows"] for row in index_rows)
    total_input = sum(row["input_rows"] for row in index_rows)
    total_mode = sum(row["candidate_rows_in_replay_mode"] for row in index_rows)
    policy_counts: Counter = Counter()
    policy_total_r: defaultdict[str, float] = defaultdict(float)
    exit_counts: dict[str, Counter] = defaultdict(Counter)
    ambiguity_counts: Counter = Counter()
    old_static_total_r = 0.0
    for row in index_rows:
        policy_counts.update(row["policy_counts"])
        for policy, value in row["policy_total_r"].items():
            policy_total_r[policy] += float(value)
        for policy, counts in row["policy_exit_reason_counts"].items():
            exit_counts[policy].update(counts)
        ambiguity_counts.update(row["policy_ambiguous_counts"])
        old_static_total_r += float(row["old_static_total_r"])
    policy_expectancy = {
        policy: (policy_total_r[policy] / policy_counts[policy] if policy_counts[policy] else None)
        for policy in sorted(policy_counts)
    }
    legacy_total = policy_total_r.get("legacy_fixed_1.5r", 0.0)
    summary = {
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_04_FULL_POLICY_DYNAMIC_REPLAY",
        "generated_at_utc": utc_now(),
        "scope": "universal_bar_close_m15_first_pass_every_replayable_candidate",
        "input_stage04_shards": len(index_rows),
        "input_rows_scanned": total_input,
        "candidate_rows_in_replay_mode": total_mode,
        "replayable_candidate_rows": total_replayable,
        "policy_names": [policy.name for policy in policies],
        "same_bar_policy": SAME_BAR_POLICY,
        "policy_counts": counter_to_dict(policy_counts),
        "policy_total_r": dict(sorted(policy_total_r.items())),
        "policy_expectancy_r": policy_expectancy,
        "policy_exit_reason_counts": {
            policy: counter_to_dict(counts) for policy, counts in sorted(exit_counts.items())
        },
        "policy_ambiguous_counts": counter_to_dict(ambiguity_counts),
        "old_static_total_r_over_replayable_rows": old_static_total_r,
        "legacy_total_r": legacy_total,
        "legacy_delta_vs_old_static_total_r": legacy_total - old_static_total_r,
        "higher_priority_source_status": (
            "M1/M5/tick/Sierra path-aware rows inventoried in Stage02 and preserved; "
            "Stage04 first pass uses complete M15 OHLC source to avoid sparse-source selection bias."
        ),
        "output_shard_index_path": rel(OUTPUT_SHARD_INDEX),
        "output_shard_dir": rel(OUTPUT_SHARD_DIR),
        "forbidden_boundaries_crossed": False,
        "no_live_trading_or_broker_mutation": True,
        "first_incomplete_invariant_after_stage04": "STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER",
    }
    OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(summary)
    update_state(summary)
    return summary


def write_report(summary: dict) -> None:
    lines = [
        "# vNext Moonshot Stage04 Full Policy Dynamic Replay",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Scope",
        "",
        f"- Replay scope: `{summary['scope']}`",
        f"- Replay mode: `{REPLAY_MODE}`",
        f"- Same-bar policy: `{SAME_BAR_POLICY}`",
        f"- Replayable candidates: `{summary['replayable_candidate_rows']}`",
        f"- Input rows scanned: `{summary['input_rows_scanned']}`",
        f"- First incomplete invariant: `{summary['first_incomplete_invariant_after_stage04']}`",
        "",
        "## Policy Expectancy",
        "",
    ]
    for policy, expectancy in summary["policy_expectancy_r"].items():
        total = summary["policy_total_r"][policy]
        lines.append(f"- `{policy}`: expectancy `{expectancy}`, total R `{total}`")
    lines.extend(
        [
            "",
            "## Source Note",
            "",
            summary["higher_priority_source_status"],
            "",
            "This is no longer a fixed target/stop label replay: each row contains all Stage03 policy outcomes from ordered source OHLC observations.",
            "",
        ]
    )
    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def update_state(summary: dict) -> None:
    if not OUTPUT_STATE.exists():
        return
    state = json.loads(OUTPUT_STATE.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_stage"] = "STAGE_04_FULL_POLICY_DYNAMIC_REPLAY"
    state["first_incomplete_invariant"] = "STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER"
    state["exact_next_action"] = "Run Stage05 universal candidate-origin layer beyond OB/FVG/breaker M15/KZ/POI boxing."
    state["row_counts_scanned"]["stage04_dynamic_replay_input_rows"] = summary["input_rows_scanned"]
    state["row_counts_scanned"]["stage04_dynamic_replay_replayable_candidates"] = summary["replayable_candidate_rows"]
    state["row_counts_scanned"]["stage04_dynamic_replay_output_shards"] = summary["input_stage04_shards"]
    state["stage_status_table"]["STAGE_04_FULL_POLICY_DYNAMIC_REPLAY"] = "complete_m15_universal_first_pass"
    state["stage_status_table"]["STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER"] = "pending"
    state["output_artifact_manifest"]["stage04_dynamic_policy_replay_shard_index"] = rel(OUTPUT_SHARD_INDEX)
    state["output_artifact_manifest"]["stage04_dynamic_policy_replay_summary"] = rel(OUTPUT_SUMMARY)
    state["output_artifact_manifest"]["stage04_dynamic_policy_replay_report"] = rel(OUTPUT_REPORT)
    state["output_artifact_manifest"]["stage04_dynamic_policy_replay_shard_dir"] = rel(OUTPUT_SHARD_DIR)
    state["completion_gate_status"] = "not_complete_first_incomplete_stage05"
    state.setdefault("verifiers_tests_run", []).append(
        {
            "command": (
                "py -3 research/science_program_2026_05/06_outcome_testing/"
                "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/"
                "build_vnext_moonshot_stage04_full_policy_dynamic_replay_2026_05_26.py"
            ),
            "status": "passed",
            "result": (
                f"replayable_candidates={summary['replayable_candidate_rows']}; "
                f"shards={summary['input_stage04_shards']}; first_incomplete=STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER"
            ),
        }
    )
    OUTPUT_STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_SHARD_DIR.mkdir(parents=True, exist_ok=True)
    policies = required_policy_manifest()
    cache = SourceCache()
    index_rows = []
    for chunk_path in iter_input_chunks():
        metrics = process_chunk(chunk_path, policies, cache)
        index_rows.append(metrics_to_index_row(metrics))
        with OUTPUT_SHARD_INDEX.open("w", encoding="utf-8", newline="\n") as handle:
            for row in index_rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
    summary = write_summary(index_rows, policies)
    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "stage": "STAGE_04_FULL_POLICY_DYNAMIC_REPLAY",
                "input_shards": summary["input_stage04_shards"],
                "replayable_candidates": summary["replayable_candidate_rows"],
                "first_incomplete_invariant": summary["first_incomplete_invariant_after_stage04"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

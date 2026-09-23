from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER_DIR = REPO_ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder"
)
MOONSHOT_ROOT = Path(
    "research/science_program_2026_05/"
    "06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
BRANCH_QUEUE_PATH = (
    MOONSHOT_ROOT / "HAZ001_READY8_DECONCENTRATED_BRANCH_QUEUE_2026-05-15.jsonl"
)
BLOCKER_LEDGER_PATH = (
    MOONSHOT_ROOT / "HAZ001_READY8_INTEGRATION_BLOCKER_LEDGER_2026-05-15.jsonl"
)
SOURCE_BINDING_PATH = (
    MOONSHOT_ROOT / "HAZ001_READY8_SOURCE_BINDING_LEDGER_2026-05-15.jsonl"
)
RULES_PATH = BUILDER_DIR / "GTOS_VNEXT_READY8_CONTEXT_RISK_RULES_2026-05-18.json"
SUMMARY_PATH = BUILDER_DIR / "GTOS_VNEXT_READY8_CONTEXT_RISK_SUMMARY_2026-05-18.json"
WAVE_ID = "WAVE_READY8_CONTEXT_RISK_RULES"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _git_blob_sha1(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _rule_score(delta: Any) -> float:
    try:
        value = float(delta)
    except (TypeError, ValueError):
        return 0.0
    if value <= 0:
        return 0.0
    return round(min(0.5, value * 100.0), 6)


def _source_artifact(path: Path, rows: int) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "hash": _git_blob_sha1(path),
        "hash_algorithm": "git_blob",
        "row_count": rows,
    }


def _sorted_counter(counter: Counter) -> dict[str, int]:
    return {
        str(key): value
        for key, value in sorted(counter.items(), key=lambda item: str(item[0]))
    }


def _build_rule(row: dict[str, Any]) -> dict[str, Any]:
    branch_key = row.get("branch_key") if isinstance(row.get("branch_key"), dict) else {}
    rule = {
        "card_id": branch_key.get("card_id"),
        "horizon_m15_bars": str(branch_key.get("horizon_m15_bars") or ""),
        "target_family_id": branch_key.get("target_family_id"),
        "partition_assignment": branch_key.get("partition_assignment"),
        "score": _rule_score(row.get("delta")),
        "evidence_delta": row.get("delta"),
        "source_path": BRANCH_QUEUE_PATH.as_posix(),
        "source_row_id": row.get("branch_id"),
        "branch_role": row.get("branch_role"),
        "evidence_class": row.get("evidence_class"),
        "reason": "haz001_ready8_deconcentrated_retest_context_support",
        "pass_unique_duplicate_denominator_count": row.get(
            "pass_unique_duplicate_denominator_count"
        ),
        "control_unique_duplicate_denominator_count": row.get(
            "control_unique_duplicate_denominator_count"
        ),
        "blocker_count": len(row.get("blockers") or []),
    }
    for key in (
        "symbol",
        "session",
        "descriptor_name",
        "descriptor_value",
        "wait_gap_bucket",
        "prior_24h_count_bucket",
        "source_window",
        "source_segment_sha256",
        "canonical_economic_group",
    ):
        value = branch_key.get(key)
        if value not in (None, "", "NO_SESSION_DESCRIPTOR"):
            rule[key] = value
    return {key: value for key, value in rule.items() if value not in (None, "")}


def build_payloads() -> tuple[dict[str, Any], dict[str, Any]]:
    branch_rows = _read_jsonl(BRANCH_QUEUE_PATH)
    blocker_rows = _read_jsonl(BLOCKER_LEDGER_PATH)
    source_binding_rows = _read_jsonl(SOURCE_BINDING_PATH)
    rules = [_build_rule(row) for row in branch_rows]
    rules = [rule for rule in rules if rule.get("score", 0.0) > 0.0]
    rules.sort(key=lambda item: str(item.get("source_row_id") or ""))

    branch_role_counts = Counter(row.get("branch_role") for row in branch_rows)
    partition_counts = Counter(
        (row.get("branch_key") or {}).get("partition_assignment") for row in branch_rows
    )
    target_family_counts = Counter(
        (row.get("branch_key") or {}).get("target_family_id") for row in branch_rows
    )
    horizon_counts = Counter(
        str((row.get("branch_key") or {}).get("horizon_m15_bars") or "")
        for row in branch_rows
    )
    blocker_id_counts = Counter(row.get("blocker_id") for row in blocker_rows)
    blocker_status_counts = Counter(row.get("status") for row in blocker_rows)
    source_status_counts = Counter(row.get("status") for row in source_binding_rows)
    score_values = [float(rule.get("score") or 0.0) for rule in rules]
    symbol_counts = Counter(rule.get("symbol") for rule in rules if rule.get("symbol"))
    session_counts = Counter(rule.get("session") for rule in rules if rule.get("session"))
    target_family_rule_counts = Counter(
        rule.get("target_family_id") for rule in rules if rule.get("target_family_id")
    )
    timeframe_counts = Counter(
        "M15" for rule in rules if rule.get("horizon_m15_bars")
    )

    source_artifacts = [
        _source_artifact(BRANCH_QUEUE_PATH, len(branch_rows)),
        _source_artifact(BLOCKER_LEDGER_PATH, len(blocker_rows)),
        _source_artifact(SOURCE_BINDING_PATH, len(source_binding_rows)),
    ]
    summary = {
        "schema_version": "gtos_vnext_ready8_context_risk_summary_v1",
        "wave_id": WAVE_ID,
        "rules_path": RULES_PATH.relative_to(REPO_ROOT).as_posix(),
        "source_artifacts": source_artifacts,
        "source_artifact_count": len(source_artifacts),
        "source_rows_counted": len(branch_rows) + len(blocker_rows) + len(source_binding_rows),
        "context_rule_count": len(rules),
        "branch_queue_rows": len(branch_rows),
        "blocker_rows": len(blocker_rows),
        "source_binding_rows": len(source_binding_rows),
        "branch_role_counts": _sorted_counter(branch_role_counts),
        "partition_counts": _sorted_counter(partition_counts),
        "target_family_counts": _sorted_counter(target_family_counts),
        "horizon_counts": _sorted_counter(horizon_counts),
        "blocker_id_counts": _sorted_counter(blocker_id_counts),
        "blocker_status_counts": _sorted_counter(blocker_status_counts),
        "source_binding_status_counts": _sorted_counter(source_status_counts),
        "coverage_counts": {
            "symbols": _sorted_counter(symbol_counts),
            "markets": _sorted_counter(symbol_counts),
            "timeframes": _sorted_counter(timeframe_counts),
            "sessions": _sorted_counter(session_counts),
            "sides": {},
            "entry_variants": {},
            "target_families": _sorted_counter(target_family_rule_counts),
        },
        "score_min": min(score_values) if score_values else 0.0,
        "score_max": max(score_values) if score_values else 0.0,
        "score_sum": round(sum(score_values), 6),
        "blank_anchor_counts": {
            "symbol": sum(1 for rule in rules if not rule.get("symbol")),
            "session": sum(1 for rule in rules if not rule.get("session")),
            "descriptor_name": sum(1 for rule in rules if not rule.get("descriptor_name")),
            "descriptor_value": sum(1 for rule in rules if not rule.get("descriptor_value")),
            "wait_gap_bucket": sum(1 for rule in rules if not rule.get("wait_gap_bucket")),
            "prior_24h_count_bucket": sum(
                1 for rule in rules if not rule.get("prior_24h_count_bucket")
            ),
            "source_window": sum(1 for rule in rules if not rule.get("source_window")),
            "source_segment_sha256": sum(
                1 for rule in rules if not rule.get("source_segment_sha256")
            ),
            "canonical_economic_group": sum(
                1 for rule in rules if not rule.get("canonical_economic_group")
            ),
        },
    }
    rules_payload = {
        "schema_version": "gtos_vnext_ready8_context_risk_rules_v1",
        "wave_id": WAVE_ID,
        "source_artifacts": source_artifacts,
        "context_rule_count": len(rules),
        "rules": rules,
    }
    return rules_payload, summary


def _write_or_check(path: Path, payload: dict[str, Any], *, check: bool) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            raise SystemExit(f"{path} is not up to date")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rules_payload, summary = build_payloads()
    _write_or_check(RULES_PATH, rules_payload, check=args.check)
    _write_or_check(SUMMARY_PATH, summary, check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

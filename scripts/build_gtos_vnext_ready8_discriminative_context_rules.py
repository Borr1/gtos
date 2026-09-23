"""Build READY8 discriminative context rules for side-aware sizing.

The source evidence is the accepted READY8 discriminative target-result control
screen. It is neutral movement evidence, not a promotion dossier; runtime use is
limited to contextual side-risk support or reduction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = (
    ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder"
)
MASTER_LEDGER_PATH = OUT_DIR / "GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_LEDGER_2026-05-18.jsonl"
RULES_PATH = OUT_DIR / "GTOS_VNEXT_READY8_DISCRIMINATIVE_CONTEXT_RULES_2026-05-18.json"
SUMMARY_PATH = OUT_DIR / "GTOS_VNEXT_READY8_DISCRIMINATIVE_CONTEXT_SUMMARY_2026-05-18.json"
PASS_VS_CONTROL_PATH = (
    ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "g0_scid_ready8_discriminative_target_result_control_evidence_synthesis_after_g12_audit/"
    "G0_SCID_READY8_DISC_TARGET_SCREEN_PASS_VS_CONTROL_CONTRAST_LEDGER_2026-05-13.jsonl"
)
G12_RECOMPUTATION_PATH = (
    ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "g12_scid_ready8_discriminative_sealed_validation_result_audit/"
    "G12_R8DISC_SEALED_VALIDATION_AUDIT_RECOMPUTATION_LEDGER_2026-05-13.json"
)
GENERATED_AT_UTC = "2026-05-18T00:00:00Z"
SELECTED_WAVE_ID = "WAVE_READY8_DISCRIMINATIVE_CONTEXT_RULES"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def long_path(path: Path) -> str:
    # The 23rd copy of this helper, and the only one that was BOTH
    # platform-blind and length-blind: it prepended the Windows
    # extended-length prefix to EVERY path on every OS, so on macOS/Linux the
    # result cannot exist and every read through it fails. The other 22 were
    # fixed in d2bb4448e; this one was missed because the census that found
    # them was taken with `rg` against a sparse working tree.
    text = str(path.resolve())
    if os.name == "nt" and len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(long_path(path), encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                payload = json.loads(line)
                if isinstance(payload, dict):
                    rows.append(payload)
    return rows


def nonempty_line_count(path: Path) -> int:
    if path.suffix.lower() == ".json":
        return 1 if path.stat().st_size else 0
    with open(long_path(path), encoding="utf-8", errors="ignore") as handle:
        return sum(1 for line in handle if line.strip())


def selected_ready8_discriminative_units() -> dict[str, Any]:
    def empty_selection() -> dict[str, Any]:
        return {
            "selected_unit_count": 0,
            "selected_counted_rows_or_lines": 0,
            "selected_row_bearing_or_structured_units": 0,
            "selected_support_or_wrapper_units": 0,
        }

    if not MASTER_LEDGER_PATH.exists():
        return empty_selection()

    selected: list[dict[str, Any]] = []
    closed_runtime_selection: dict[str, Any] | None = None
    for line in MASTER_LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if (
            row.get("batch_wave_id") == SELECTED_WAVE_ID
            and row.get("runtime_selected_open_unit_count")
        ):
            closed_runtime_selection = {
                "selected_unit_count": row.get("runtime_selected_open_unit_count", 0),
                "selected_counted_rows_or_lines": row.get(
                    "runtime_selected_counted_rows_or_lines", 0
                ),
                "selected_row_bearing_or_structured_units": row.get(
                    "runtime_selected_row_bearing_or_structured_units", 0
                ),
                "selected_support_or_wrapper_units": row.get(
                    "runtime_selected_support_or_wrapper_units", 0
                ),
            }
        if row.get("conversion_state") != "NOT_STARTED":
            continue
        path_text = str(row.get("source_artifact_path") or "")
        lower = path_text.casefold().replace("\\", "/")
        if "ready8" not in lower:
            continue
        if not ("disc" in lower or "discriminative" in lower or "r8disc" in lower):
            continue
        selected.append(row)

    if not selected:
        return closed_runtime_selection or empty_selection()

    rowish_suffixes = {".jsonl", ".json", ".csv", ".tsv", ".ndjson"}
    counted = 0
    rowish = 0
    for row in sorted(selected, key=lambda item: int(item.get("execution_position") or 0)):
        source_path = ROOT / str(row.get("source_artifact_path") or "")
        row_count = nonempty_line_count(source_path) if source_path.exists() else 0
        counted += row_count
        if source_path.suffix.lower() in rowish_suffixes:
            rowish += 1

    return {
        "selected_unit_count": len(selected),
        "selected_counted_rows_or_lines": counted,
        "selected_row_bearing_or_structured_units": rowish,
        "selected_support_or_wrapper_units": len(selected) - rowish,
    }


def score_from_delta(delta: float) -> float:
    if delta > 0:
        return round(min(0.5, delta * 100.0), 6)
    return round(max(-1.0, delta * 200.0), 6)


def build_rules() -> tuple[dict[str, Any], dict[str, Any]]:
    source_rows = read_jsonl(PASS_VS_CONTROL_PATH)
    g12_recomputation = read_json(G12_RECOMPUTATION_PATH)
    selected = selected_ready8_discriminative_units()
    rules: list[dict[str, Any]] = []

    for source_row_index, row in enumerate(source_rows, start=1):
        if row.get("contrast_scope") != "card_horizon_target_family":
            continue
        if row.get("comparison_status") != "PASS_CONTROL_COMPARABLE":
            continue
        dimensions = row.get("dimensions") if isinstance(row.get("dimensions"), dict) else {}
        card_id = str(dimensions.get("card_id") or "")
        if card_id.startswith("ADV-"):
            continue
        delta = row.get("neutral_signed_movement_delta_pass_minus_control")
        if not isinstance(delta, (int, float)):
            continue
        score = score_from_delta(float(delta))
        if score == 0.0:
            continue
        role_summaries = row.get("role_summaries") if isinstance(row.get("role_summaries"), dict) else {}
        pass_summary = role_summaries.get("per_card_pass_row") or {}
        control_summary = role_summaries.get("per_card_contrast_row") or {}
        if int(pass_summary.get("computable_rows") or 0) < 30:
            continue
        if int(control_summary.get("computable_rows") or 0) < 30:
            continue
        rules.append(
            {
                "ready8_discriminative_rule_id": f"READY8-DISC-CONTEXT-{len(rules) + 1:04d}",
                "card_id": card_id,
                "horizon_m15_bars": str(dimensions.get("horizon_m15_bars")),
                "target_family_id": dimensions.get("target_family_id"),
                "score": score,
                "evidence_delta": float(delta),
                "neutral_magnitude_delta_pass_minus_control": row.get(
                    "neutral_magnitude_delta_pass_minus_control"
                ),
                "comparison_status": row.get("comparison_status"),
                "movement_shift_class": row.get("movement_shift_class"),
                "pass_sign": row.get("pass_sign"),
                "control_sign": row.get("control_sign"),
                "pass_computable_rows": pass_summary.get("computable_rows"),
                "control_computable_rows": control_summary.get("computable_rows"),
                "source_path": rel(PASS_VS_CONTROL_PATH),
                "source_line_no": source_row_index,
                "source_row_id": f"READY8-DISC-PASS-CONTROL-{source_row_index:04d}",
                "reason": (
                    "ready8_discriminative_positive_context_support"
                    if score > 0
                    else "ready8_discriminative_inverse_context_risk"
                ),
            }
        )

    rule_counts_by_card = Counter(rule["card_id"] for rule in rules)
    rule_counts_by_target = Counter(rule["target_family_id"] for rule in rules)
    rule_counts_by_horizon = Counter(rule["horizon_m15_bars"] for rule in rules)
    score_direction_counts = Counter("positive" if rule["score"] > 0 else "negative" for rule in rules)
    blank_anchor_counts = Counter(
        field
        for rule in rules
        for field in ("card_id", "horizon_m15_bars", "target_family_id")
        if not rule.get(field)
    )

    payload = {
        "schema_version": "gtos_vnext_ready8_discriminative_context_rules_v1",
        "generated_at_utc": GENERATED_AT_UTC,
        "source_evidence_class": "G0_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_ONLY",
        "context_rule_count": len(rules),
        "rules": rules,
    }
    summary = {
        "schema_version": "gtos_vnext_ready8_discriminative_context_summary_v1",
        "generated_at_utc": GENERATED_AT_UTC,
        "rules_path": rel(RULES_PATH),
        "summary_path": rel(SUMMARY_PATH),
        "context_rule_count": len(rules),
        "positive_rule_count": score_direction_counts.get("positive", 0),
        "negative_rule_count": score_direction_counts.get("negative", 0),
        "selected_open_ready8_discriminative_family": selected,
        "source_rows_counted": selected.get("selected_counted_rows_or_lines", 0),
        "g12_expected_counts": g12_recomputation.get("expected_counts", {}),
        "g12_headline_recomputed_counts": g12_recomputation.get(
            "headline_recomputed_counts", {}
        ),
        "rule_counts_by_card": dict(sorted(rule_counts_by_card.items())),
        "rule_counts_by_horizon": dict(sorted(rule_counts_by_horizon.items())),
        "rule_counts_by_target_family": dict(sorted(rule_counts_by_target.items())),
        "score_direction_counts": dict(sorted(score_direction_counts.items())),
        "blank_anchor_counts": dict(sorted(blank_anchor_counts.items())),
        "expected_runtime_effect": (
            "READY8 discriminative pass-vs-control rows become scoped context "
            "support or inverse risk rules for side-aware sizing, while the "
            "existing READY8 failure-context adjustment artifact can still zero "
            "or halve underpowered, concentrated, or control-explained scopes."
        ),
    }
    return payload, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    payload, summary = build_rules()
    if args.check:
        expected_rules = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
        if RULES_PATH.exists() and RULES_PATH.read_text(encoding="utf-8") != expected_rules:
            raise SystemExit(f"{RULES_PATH} is stale")
        if SUMMARY_PATH.exists() and SUMMARY_PATH.read_text(encoding="utf-8") != expected_summary:
            raise SystemExit(f"{SUMMARY_PATH} is stale")
    else:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        RULES_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "rules_path": rel(RULES_PATH),
                "summary_path": rel(SUMMARY_PATH),
                "context_rule_count": summary["context_rule_count"],
                "positive_rule_count": summary["positive_rule_count"],
                "negative_rule_count": summary["negative_rule_count"],
                "selected_unit_count": summary[
                    "selected_open_ready8_discriminative_family"
                ]["selected_unit_count"],
                "source_rows_counted": summary["source_rows_counted"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Join downstream evidence only after verifying the blind judgment freeze."""

from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
RUNS = (
    (
        "2025-10-28",
        Path("/private/tmp/wave21-minimal-repair-20251028-875037f1b-r4/harness_wave21_minimal_repair_20251028_875037f1b_r4_stage_ledger.jsonl.gz"),
        "89762595a78e7d81003a2595c08e39d9dffb6d0c4bed2c2d0e7970bcbb4a7991",
    ),
    (
        "2025-11-03",
        Path("/private/tmp/wave21-minimal-repair-20251103-875037f1b-r1/harness_wave21_minimal_repair_20251103_875037f1b_r1_stage_ledger.jsonl.gz"),
        "db84b4d7137b6da9d60741abca4ff069152a73dc89fc0e4243f82329e82711d8",
    ),
    (
        "2025-11-07",
        Path("/private/tmp/wave21-minimal-repair-20251107-875037f1b-r1/harness_wave21_minimal_repair_20251107_875037f1b_r1_stage_ledger.jsonl.gz"),
        "e135d297cee9631eec76d322a9864a3011941987151940d9b4d69dc4a9a9e835",
    ),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def verify_freeze() -> dict[str, Any]:
    path = ROOT / "PREDECISION_JUDGMENTS_FREEZE.json"
    freeze = json.loads(path.read_text())
    body = dict(freeze)
    expected_root = body.pop("receipt_root_sha256")
    actual_root = stable_sha256(body)
    if actual_root != expected_root:
        raise ValueError(f"freeze_receipt_root_mismatch:{expected_root}:{actual_root}")
    for key in ("sample_manifest", "review_packet", "population_counts", "judgments"):
        binding = freeze[key]
        bound_path = ROOT / binding["path"]
        actual_sha = sha256_file(bound_path)
        if actual_sha != binding["sha256"]:
            raise ValueError(f"freeze_file_sha_mismatch:{key}:{binding['sha256']}:{actual_sha}")
    if freeze.get("unblinding_allowed_after_this_freeze") is not True:
        raise ValueError("unblinding_not_authorized_by_freeze")
    return freeze


def occurrence_key(row: Mapping[str, Any]) -> str:
    identity = row.get("identity") or {}
    return str(
        identity.get("canonical_replay_candidate_instance_key")
        or f"{identity.get('candidate_id')}@@{identity.get('decision_time_utc')}"
    )


def project_downstream(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    candidate = next((row for row in rows if row.get("stage") == "candidate"), {})
    terminal = next(
        (
            row
            for row in rows
            if row.get("stage") in {"accounted", "exit", "filled", "ordered", "missed"}
        ),
        {},
    )
    candidate_o = candidate.get("observables") or {}
    terminal_o = terminal.get("observables") or {}
    return {
        "stages_present": [str(row.get("stage")) for row in rows],
        "raw_selector_action": candidate_o.get("raw_selector_action"),
        "raw_selector_reason": candidate_o.get("raw_selector_reason"),
        "effective_selector_action": candidate_o.get("selector_action"),
        "effective_selector_reason": candidate_o.get("selector_reason"),
        "scheduler_materialization_action_intent": terminal_o.get(
            "scheduler_materialization_action_intent"
        ),
        "risk_decision": terminal_o.get("risk_decision"),
        "risk_decision_reason": terminal_o.get("risk_decision_reason"),
        "order_status": terminal_o.get("order_status"),
        "fill_status": terminal_o.get("fill_status"),
        "terminal_stage": terminal.get("stage"),
        "terminal_outcome": terminal_o.get("terminal_outcome"),
        "miss_reason": terminal_o.get("miss_reason"),
        "package_replay_order_executable_transfer_status": terminal_o.get(
            "package_replay_order_executable_transfer_status"
        ),
        "pretrade_cost_r": candidate_o.get("broker_pretrade_cost_r"),
        "pretrade_cost_quote_r": candidate_o.get("expected_cost_r"),
        "realized_component_cost_r": terminal_o.get("realized_component_cost_r"),
        "accounting_status": terminal_o.get("accounting_status"),
        "selected_candidate_id": terminal_o.get("selected_candidate_id"),
        "selected_candidate_ids": terminal_o.get("selected_candidate_ids"),
    }


def final_alignment(professional: str, downstream: Mapping[str, Any]) -> str:
    sent = downstream.get("order_status") not in {
        None,
        "not_sent_missed_opportunity",
        "not_ordered",
    }
    if not sent and professional == "reject":
        return "aligned_no_order_reject"
    if not sent and professional == "wait":
        return "aligned_risk_inert_system_reject_vs_professional_wait"
    if not sent and professional == "reduce":
        return "system_more_conservative_no_order_vs_professional_reduce"
    if sent and professional in {"reject", "wait"}:
        return "system_more_aggressive_than_professional"
    return "both_risk_bearing_requires_geometry_comparison"


def raw_selector_alignment(professional: str, action: str | None) -> str:
    if action in {"reject", "source-required"}:
        return (
            "raw_selector_risk_inert_matches_professional"
            if professional in {"reject", "wait"}
            else "raw_selector_more_conservative_than_professional"
        )
    if action == "trade":
        return (
            "raw_selector_more_aggressive_than_professional"
            if professional in {"reject", "wait", "reduce"}
            else "raw_selector_matches_professional_trade"
        )
    if action in {"reduce-risk", "open-reduced-risk"}:
        return (
            "raw_selector_more_aggressive_than_professional"
            if professional in {"reject", "wait"}
            else "raw_selector_matches_professional_reduce"
        )
    return "raw_selector_alignment_not_evaluable"


def main() -> None:
    freeze = verify_freeze()
    judgments = {
        row["occurrence_key"]: row
        for row in (
            json.loads(line)
            for line in (ROOT / "PREDECISION_JUDGMENTS_FROZEN.jsonl").read_text().splitlines()
        )
    }
    downstream_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    ledger_bindings: list[dict[str, Any]] = []
    for day, path, expected_sha in RUNS:
        actual_sha = sha256_file(path)
        if actual_sha != expected_sha:
            raise ValueError(f"ledger_sha_mismatch:{path}:{expected_sha}:{actual_sha}")
        ledger_bindings.append({"day": day, "path": str(path), "sha256": actual_sha})
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                key = occurrence_key(row)
                if key in judgments:
                    downstream_rows[key].append(row)
    if set(downstream_rows) != set(judgments):
        raise ValueError("sample_downstream_join_incomplete")

    output: list[dict[str, Any]] = []
    for key, judgment in sorted(judgments.items(), key=lambda item: item[1]["review_id"]):
        rows = sorted(
            downstream_rows[key],
            key=lambda row: (str(row.get("stage")), int(row.get("stage_row_ordinal") or 0)),
        )
        downstream = project_downstream(rows)
        result = {
            "schema": "gtos.wave21.professional_predecision_review.v2.unblinded_comparison",
            "review_id": judgment["review_id"],
            "occurrence_key": key,
            "professional_disposition_frozen": judgment["professional_disposition"],
            "raw_selector_alignment": raw_selector_alignment(
                judgment["professional_disposition"], downstream["raw_selector_action"]
            ),
            "final_system_alignment": final_alignment(
                judgment["professional_disposition"], downstream
            ),
            "downstream": downstream,
        }
        result["comparison_row_root_sha256"] = stable_sha256(result)
        output.append(result)
    path = ROOT / "UNBLINDED_SAMPLE_COMPARISON.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for row in output:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    summary_body = {
        "schema": "gtos.wave21.professional_predecision_review.v2.unblinded_summary",
        "freeze_receipt_root_sha256": freeze["receipt_root_sha256"],
        "comparison_path": path.name,
        "comparison_sha256": sha256_file(path),
        "comparison_row_count": len(output),
        "ledger_bindings": ledger_bindings,
        "professional_disposition_counts": dict(
            sorted(Counter(row["professional_disposition_frozen"] for row in output).items())
        ),
        "raw_selector_alignment_counts": dict(
            sorted(Counter(row["raw_selector_alignment"] for row in output).items())
        ),
        "final_system_alignment_counts": dict(
            sorted(Counter(row["final_system_alignment"] for row in output).items())
        ),
        "stages_present_counts": dict(
            sorted(Counter(stage for row in output for stage in row["downstream"]["stages_present"]).items())
        ),
        "ordered_occurrence_count": sum(
            row["downstream"]["order_status"] != "not_sent_missed_opportunity"
            for row in output
        ),
        "sample_cannot_validate_order_fill_exit_cost_account_quality": True,
    }
    summary = {**summary_body, "summary_root_sha256": stable_sha256(summary_body)}
    (ROOT / "UNBLINDED_SAMPLE_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

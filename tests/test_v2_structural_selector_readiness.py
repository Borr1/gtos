from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts import audit_v2_structural_selector_readiness as script
from src.research_infra.v2_structural_selector_readiness import (
    BROKER_ACTUAL_SAMPLE_FLOOR,
    PROMOTION_VERDICT,
    STATUS_NOT_READY,
    STATUS_READY_FOR_DOSSIER,
    build_report_payload,
    build_status_row,
    render_markdown,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _audit_row(index: int, **overrides) -> dict:
    date = f"2026-05-{(index % 5) + 1:02d}"
    symbols = ["NAS100", "XAUUSD", "US30"]
    row = {
        "row_key": f"audit-{index}",
        "candidate_id": f"{symbols[index % len(symbols)]}_{date}T13:{index % 60:02d}:00+00:00",
        "created_at_utc": f"{date}T13:{index % 60:02d}:05+00:00",
        "backfilled_at_utc": f"{date}T13:{index % 60:02d}:10+00:00",
        "decision_time_utc": f"{date}T13:{index % 60:02d}:00+00:00",
        "symbol": symbols[index % len(symbols)],
        "duplicate_aware_counting_status": "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY",
        "pending_limit_lifecycle_audit_status": "PENDING_LIMIT_LIFECYCLE_COMPLETE_WITH_DOCUMENTED_LIMITATIONS",
        "broker_actual_r_pair_counted": True,
        "synthetic_path_r_pair_counted": False,
        "documented_limitation_codes": [],
        "promotion_verdict": PROMOTION_VERDICT,
    }
    row.update(overrides)
    return row


def test_current_like_rows_remain_not_ready_and_document_mt5_boundary(tmp_path):
    export = tmp_path / "data" / "account_history" / "mt5_deals_2026-04-27_2026-05-05.jsonl"
    _write_jsonl(export, [{"ticket": 1}, {"ticket": 2}])
    rows = [
        _audit_row(
            1,
            broker_actual_r_pair_counted=False,
            synthetic_path_r_pair_counted=True,
            documented_limitation_codes=[
                "OB_BOUNDARY_USES_SHARED_CANDIDATE_PATH_PROXY_NOT_EXACT_V2_LOCK_METADATA"
            ],
        ),
        _audit_row(
            2,
            broker_actual_r_pair_counted=False,
            synthetic_path_r_pair_counted=True,
            documented_limitation_codes=[
                "STRATEGY_SPECIFIC_EXACT_FIELDS_SOURCE_NOT_CAPTURED"
            ],
        ),
    ]

    row = build_status_row(
        root=tmp_path,
        v2b_audit_rows=rows,
        account_history_export_path=export.relative_to(tmp_path),
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert row["readiness_status"] == STATUS_NOT_READY
    assert row["readiness_verdict"] == "NOT_READY"
    assert row["mt5_account_history_boundary"]["export_present"] is True
    assert row["mt5_account_history_boundary"]["export_nonempty_rows"] == 2
    assert row["mt5_account_history_boundary"]["global_broker_actual_claim_allowed_unique_rows"] == 0
    assert row["mt5_account_history_boundary"]["candidate_linked_broker_actual_rows_available"] == 0
    assert row["evidence_counts"]["countable_broker_actual_pairs"] == 0
    assert "BROKER_ACTUAL_R_SAMPLE_FLOOR_NOT_MET" in row["documented_limitation_codes"]
    assert "non-filled shadow alternatives" in " ".join(
        row["mt5_account_history_boundary"]["cannot_resolve"]
    )
    assert row["promotion_verdict"] == PROMOTION_VERDICT


def test_all_gates_pass_only_reaches_dossier_review_not_promotion(tmp_path):
    dossier = tmp_path / "research" / "program_control" / "V2_STRUCTURAL_SELECTOR_PROMOTION_DOSSIER_fixture.md"
    dossier.parent.mkdir(parents=True, exist_ok=True)
    dossier.write_text("# fixture\n", encoding="utf-8")
    export = tmp_path / "data" / "account_history" / "mt5_deals_2026-04-27_2026-05-05.jsonl"
    _write_jsonl(export, [{"ticket": index} for index in range(BROKER_ACTUAL_SAMPLE_FLOOR)])
    audit_rows = [_audit_row(index) for index in range(BROKER_ACTUAL_SAMPLE_FLOOR)]
    broker_rows = [
        {
            "candidate_id": row["candidate_id"],
            "actual_r_claim_allowed": True,
            "created_at_utc": row["created_at_utc"],
        }
        for row in audit_rows
    ]

    row = build_status_row(
        root=tmp_path,
        v2b_audit_rows=audit_rows,
        broker_actual_rows=broker_rows,
        account_history_export_path=export.relative_to(tmp_path),
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert row["readiness_status"] == STATUS_READY_FOR_DOSSIER
    assert row["readiness_verdict"] == "DOSSIER_REVIEW_ONLY_NOT_PROMOTED"
    assert row["gate_summary"]["failed"] == 0
    assert row["promotion_verdict"] == PROMOTION_VERDICT
    assert row["order_calls"] == 0


def test_report_markdown_explains_mt5_account_history_limit(tmp_path):
    payload = build_report_payload(
        root=tmp_path,
        v2b_audit_rows=[_audit_row(1, broker_actual_r_pair_counted=False)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    rendered = render_markdown(payload)

    assert "## MT5 Account-History Boundary" in rendered
    assert "cannot reconstruct unfilled shadow choices" in rendered
    assert "NO_PROMOTION_VERDICT" in rendered


def test_concentration_gate_is_independent_from_broker_actual_sample_floor(tmp_path):
    rows = [
        _audit_row(
            index,
            broker_actual_r_pair_counted=False,
            synthetic_path_r_pair_counted=True,
            documented_limitation_codes=[
                "OB_BOUNDARY_USES_SHARED_CANDIDATE_PATH_PROXY_NOT_EXACT_V2_LOCK_METADATA"
            ],
        )
        for index in range(6)
    ]

    row = build_status_row(
        root=tmp_path,
        v2b_audit_rows=rows,
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )
    gates = {gate["gate_id"]: gate for gate in row["readiness_gates"]}

    assert gates["G1_COUNTABLE_BROKER_ACTUAL_R_SAMPLE_FLOOR"]["passed"] is False
    assert gates["G4_CONCENTRATION_DIAGNOSTICS_PASS"]["passed"] is True
    assert "CONCENTRATION_GATES_NOT_MET" not in row["documented_limitation_codes"]


def test_readiness_row_key_changes_when_source_counts_change(tmp_path):
    first = build_status_row(
        root=tmp_path,
        v2b_audit_rows=[_audit_row(1, broker_actual_r_pair_counted=False)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )
    second = build_status_row(
        root=tmp_path,
        v2b_audit_rows=[_audit_row(1, broker_actual_r_pair_counted=False)],
        pending_lifecycle_rows=[{"row_key": "pending-1", "candidate_id": "c1"}],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert first["source_counts"]["pending_lifecycle_latest_rows"] == 0
    assert second["source_counts"]["pending_lifecycle_latest_rows"] == 1
    assert first["source_dependency_signature"] != second["source_dependency_signature"]
    assert first["row_key"] != second["row_key"]


def test_script_appends_readiness_row_idempotently(tmp_path, monkeypatch, capsys):
    shadow = tmp_path / "shadow_logs"
    export = tmp_path / "data" / "account_history" / "mt5_deals_2026-04-27_2026-05-05.jsonl"
    _write_jsonl(shadow / "v2b_forward_pair_resolution_audit.jsonl", [_audit_row(1, broker_actual_r_pair_counted=False)])
    _write_jsonl(export, [{"ticket": 1}])
    status_log = shadow / "v2_structural_selector_readiness.jsonl"
    output_json = tmp_path / "research" / "program_control" / "report.json"
    output_md = tmp_path / "research" / "program_control" / "report.md"
    args = [
        "audit_v2_structural_selector_readiness.py",
        "--v2b-audit",
        str(shadow / "v2b_forward_pair_resolution_audit.jsonl"),
        "--status-log",
        str(status_log),
        "--account-history-export",
        str(export),
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
    ]
    monkeypatch.setattr(sys, "argv", args)

    assert script.main() == 0
    first = json.loads(capsys.readouterr().out)
    assert first["rows_appended"] == 1

    monkeypatch.setattr(sys, "argv", args)
    assert script.main() == 0
    second = json.loads(capsys.readouterr().out)

    assert second["rows_appended"] == 0
    rows = [json.loads(line) for line in status_log.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert output_json.exists()
    assert output_md.exists()

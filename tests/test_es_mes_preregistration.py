from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts import audit_es_mes_preregistration as script
from src.research_infra.es_mes_preregistration import (
    ACTION_REQUIRED,
    PROMOTION_VERDICT,
    STATUS_OK,
    build_report_payload,
    build_status_row,
    default_registry_payload,
    render_markdown,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _inventory() -> dict:
    return {
        "schema_version": "sierra_forward_capture_inventory_v1",
        "status": "RESEARCH_ARTIFACT_DONE",
        "promotion_verdict": PROMOTION_VERDICT,
        "symbols": [
            {
                "symbol_root": "ES",
                "status": "READY_SCID_AND_DEPTH_PRESENT",
                "scid_file_count": 1,
                "depth_file_count": 2,
                "latest_scid_utc": "2026-05-04T19:06:28+00:00",
                "latest_depth_utc": "2026-05-04T19:06:29+00:00",
            },
            {
                "symbol_root": "MES",
                "status": "READY_SCID_AND_DEPTH_PRESENT",
                "scid_file_count": 2,
                "depth_file_count": 2,
                "latest_scid_utc": "2026-05-04T19:06:28+00:00",
                "latest_depth_utc": "2026-05-04T19:06:29+00:00",
            },
        ],
    }


def _conversion() -> dict:
    return {
        "schema_version": "expanded_oos_first_wave_bounded_conversion_status_v1",
        "status": "RESEARCH_ARTIFACT_DONE",
        "promotion_verdict": PROMOTION_VERDICT,
        "m15_inventory": [
            {"file_symbol": "SPX_ES", "source_symbol": "ESM26-CME", "rows": 268},
            {"file_symbol": "SPX_MES", "source_symbol": "MESM26-CME", "rows": 268},
        ],
    }


def _label_status() -> dict:
    return {
        "schema_version": "expanded_oos_first_wave_label_status_audit_v1",
        "status": "RESEARCH_ARTIFACT_DONE",
        "promotion_verdict": PROMOTION_VERDICT,
        "families": [
            {
                "family": "S&P with ES/MES",
                "label_status": "LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT",
            }
        ],
    }


def test_status_row_preregisters_es_mes_without_opening_outcomes(tmp_path):
    registry = default_registry_payload("2026-05-05T00:00:00+00:00")
    row = build_status_row(
        root=tmp_path,
        registry=registry,
        conversion_status=_conversion(),
        label_status=_label_status(),
        sierra_inventory=_inventory(),
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert row["status"] == STATUS_OK
    assert row["promotion_verdict"] == PROMOTION_VERDICT
    assert row["opened_outcome_slices_at_registration"] == 0
    assert row["opened_outcome_artifacts"] == []
    assert row["strategy_family"] == "ES_MES_EQUITY_INDEX_CONTEXT_CONTROL"
    assert row["order_calls"] == 0


def test_outcome_artifact_is_action_required(tmp_path):
    outcome = tmp_path / "research" / "program_control" / "ES_MES_OUTCOME_RESULTS.json"
    outcome.parent.mkdir(parents=True, exist_ok=True)
    outcome.write_text("{}", encoding="utf-8")

    row = build_status_row(
        root=tmp_path,
        registry=default_registry_payload("2026-05-05T00:00:00+00:00"),
        conversion_status=_conversion(),
        label_status=_label_status(),
        sierra_inventory=_inventory(),
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert row["status"] == ACTION_REQUIRED
    assert "ES_MES_OUTCOMES_OPENED_OR_LABEL_STATUS_NOT_CLOSED" in row["action_required_codes"]


def test_report_markdown_documents_no_lookahead_boundary():
    payload = build_report_payload(
        root=Path("."),
        registry=default_registry_payload("2026-05-05T00:00:00+00:00"),
        conversion_status=_conversion(),
        label_status=_label_status(),
        sierra_inventory=_inventory(),
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    rendered = render_markdown(payload)

    assert "Opened outcome slices at registration: `0`" in rendered
    assert "ES_MES_EQUITY_INDEX_CONTEXT_CONTROL" in rendered
    assert "NO_PROMOTION_VERDICT" in rendered


def test_script_appends_status_row_idempotently(tmp_path, monkeypatch, capsys):
    registry = tmp_path / "research" / "program_control" / "registry.json"
    registry_md = tmp_path / "research" / "program_control" / "registry.md"
    prior = tmp_path / "research" / "program_control" / "prior.json"
    conversion = tmp_path / "research" / "program_control" / "conversion.json"
    label_status = tmp_path / "research" / "program_control" / "label_status.json"
    inventory = tmp_path / "research" / "program_control" / "sierra.json"
    status_log = tmp_path / "shadow_logs" / "es_mes_preregistration_status.jsonl"
    output_json = tmp_path / "research" / "program_control" / "report.json"
    output_md = tmp_path / "research" / "program_control" / "report.md"
    _write_json(prior, {"schema_version": "es_mes_pre_registration_v1", "status": "RESEARCH_ARTIFACT_DONE"})
    _write_json(conversion, _conversion())
    _write_json(label_status, _label_status())
    _write_json(inventory, _inventory())
    args = [
        "audit_es_mes_preregistration.py",
        "--registry",
        str(registry),
        "--registry-md",
        str(registry_md),
        "--prior-preregistration",
        str(prior),
        "--conversion-status",
        str(conversion),
        "--label-status",
        str(label_status),
        "--sierra-inventory",
        str(inventory),
        "--status-log",
        str(status_log),
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
    assert registry.exists()
    assert registry_md.exists()
    assert output_json.exists()
    assert output_md.exists()
    assert len(status_log.read_text(encoding="utf-8").splitlines()) == 1

from __future__ import annotations

import json

from src.research_infra.forward_claim_ledger import (
    build_claim_ledger,
    build_claim_row,
    render_claim_ledger_md,
    write_claim_ledger,
)


def test_claim_row_keeps_not_computable_reason():
    row = build_claim_row(
        claim_id="FCI-CLAIM-001",
        claim="NAS100 thin-depth remains diagnostic only",
        evidence_class="FUTURES_PROXY_TRANSFER",
        opened_slice="forward_not_opened",
        sample_size=0,
        label_lane="broker_actual_r_missing",
        cost_model="databento_declared_cost",
        status="WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE",
        not_computable_reason="actual broker-R < 20 and MBP10 rows < 30",
    )

    assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert row["dsr_status"] == "not_computable"
    assert "actual broker-R" in row["not_computable_reason"]


def test_claim_ledger_counts_status_and_evidence_class():
    rows = [
        build_claim_row(
            claim_id="FCI-CLAIM-001",
            claim="claim one",
            evidence_class="FORWARD_SHADOW",
            opened_slice="none",
            sample_size=0,
            label_lane="synthetic_path_pending",
            cost_model="none",
            status="WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE",
        ),
        build_claim_row(
            claim_id="FCI-CLAIM-002",
            claim="claim two",
            evidence_class="DISCOVERY_ONLY",
            opened_slice="opened_burned",
            sample_size=5,
            label_lane="synthetic_path_r",
            cost_model="0.05R",
            status="RESEARCH_ARTIFACT_DONE",
        ),
    ]

    payload = build_claim_ledger(rows)
    assert payload["schema_version"] == "forward_capture_claim_ledger_v1"
    assert payload["status_counts"]["RESEARCH_ARTIFACT_DONE"] == 1
    assert payload["evidence_class_counts"]["FORWARD_SHADOW"] == 1


def test_write_claim_ledger_outputs_json_and_md(tmp_path):
    row = build_claim_row(
        claim_id="FCI-CLAIM-001",
        claim="claim one",
        evidence_class="FORWARD_SHADOW",
        opened_slice="none",
        sample_size=0,
        label_lane="synthetic_path_pending",
        cost_model="none",
        status="WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE",
    )
    payload = build_claim_ledger([row])
    json_path = tmp_path / "ledger.json"
    md_path = tmp_path / "ledger.md"

    write_claim_ledger(payload, json_path, md_path)

    assert json.loads(json_path.read_text(encoding="utf-8"))["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert "Promotion Boundary" in md_path.read_text(encoding="utf-8")


def test_render_md_includes_no_promotion():
    payload = build_claim_ledger([])
    md = render_claim_ledger_md(payload)
    assert "NO_PROMOTION_VERDICT" in md

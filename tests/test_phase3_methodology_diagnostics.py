from __future__ import annotations

import json

from scripts import analyze_phase3_methodology_diagnostics as mod


def test_same_dataset_claim_forbids_promotion_p_values():
    policy = mod.diagnostic_policy("same_dataset_discovery", {"promotion_verdict": "NO_PROMOTION_VERDICT"})

    assert policy["promotion_p_value_allowed"] is False
    assert policy["dsr"]["status"] == "not_computable"
    assert "same_dataset" in policy["dsr"]["reason"]


def test_label_limited_orderflow_records_actual_r_counts():
    payload = {
        "feeds": {
            "MBO_TOP20": {"label_coverage": {"actual_r_n": 1}},
            "MBP10_TOP10": {"label_coverage": {"actual_r_n": 1}},
        }
    }

    policy = mod.diagnostic_policy("label_limited_orderflow_diagnostic", payload)

    assert policy["dsr"]["status"] == "not_computable"
    assert policy["dsr"]["actual_r_counts"] == {"MBO_TOP20": 1, "MBP10_TOP10": 1}
    assert policy["promotion_p_value_allowed"] is False


def test_stale_ledger_diagnostics_flags_old_v2b_wording(tmp_path):
    ledger = tmp_path / "ledger.md"
    ledger.write_text(
        "V2b has no post-cutoff prospective rows\n"
        "validation_status=BLOCKED_NO_PROSPECTIVE_ROWS\n",
        encoding="utf-8",
    )

    out = mod.stale_ledger_diagnostics(ledger)

    assert out["status"] == "STALE_MARKERS_FOUND"
    assert len(out["hits"]) == 2


def test_build_payload_uses_reference_dsr_without_transplanting(tmp_path, monkeypatch):
    artifact = tmp_path / "claim.json"
    artifact.write_text(json.dumps({"promotion_verdict": "NO_PROMOTION_VERDICT"}), encoding="utf-8")
    dsr = tmp_path / "dsr.json"
    dsr.write_text(json.dumps({"rows": [{"verdict": "SURVIVES"}, {"verdict": "FAILS"}]}), encoding="utf-8")
    ledger = tmp_path / "ledger.md"
    ledger.write_text("fresh", encoding="utf-8")
    monkeypatch.setattr(
        mod,
        "CLAIM_REGISTRY",
        [
            {
                "claim_id": "synthetic_claim",
                "artifact": str(artifact),
                "evidence_class": "same_dataset_discovery",
                "claim_family": "test",
            }
        ],
    )

    payload = mod.build_payload(dsr_path=dsr, claim_ledger_path=ledger)

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["summary"]["promotion_p_value_allowed_claims"] == []
    assert payload["summary"]["promotion_p_value_forbidden_claims"] == ["synthetic_claim"]
    assert payload["dsr_reference"]["verdict_counts"] == {"FAILS": 1, "SURVIVES": 1}

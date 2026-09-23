"""Receipt-bound direct fidelity measurements never masquerade as live recall."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.research_infra.walkforward import fidelity as F

SOURCE = Path(__file__).resolve()
SOURCE_SHA256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
CR_FIDELITY = Path(
    "docs/audits/fable5-vision-audit-20260725/phase19/receipts/"
    "CR_GENERATOR_FIDELITY_V1.json"
).resolve()
CR_RESULT = Path(
    "docs/audits/fable5-vision-audit-20260725/phase19/receipts/"
    "CR_NY_METALS_CAPTURE_RESULT_V1.json"
).resolve()


@pytest.fixture(autouse=True)
def _clean_direct_register():
    F.clear_direct_fidelity_measurements()
    yield
    F.clear_direct_fidelity_measurements()


def _register(member: str = "broad_v4_time_conditioned_ny_metals_long") -> F.Fidelity:
    return F.register_direct_fidelity_measurement(
        member,
        agreed=249,
        reference_only=0,
        generated_only=None,
        reference_kind=F.FidelityReference.REPLAY_REFERENCE,
        source=str(SOURCE),
        source_sha256=SOURCE_SHA256,
        note="Precision is unavailable because the semantic projection omitted policy fields.",
    )


def _costs():
    from src.costs.model import BrokerTrueCosts

    return BrokerTrueCosts(
        {
            "version": "test",
            "accounts": {
                "FTMO": {"server": "FTMO-Server3", "instruments": {}}
            },
        }
    )


def _fidelity_gate(rec: F.Fidelity, **spec_fields):
    from src.research_infra.walkforward.gate import run_gate
    from src.research_infra.walkforward.spec import GateSpec

    spec = GateSpec(
        spec_id="direct_fidelity_authority_test",
        authored_utc="2026-08-01T00:00:00+00:00",
        declared_family_size=1,
        **spec_fields,
    )
    verdict = run_gate({rec.sleeve: []}, spec, costs=_costs()).verdicts[rec.sleeve]
    return spec, verdict


def _write_jsonl(path: Path, rows: list[dict]) -> str:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _authority(path: Path, lineage: str) -> dict[str, str]:
    path.write_text(json.dumps({"lineage": lineage}, sort_keys=True) + "\n")
    return {
        "source_path": path.name,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _structured_evidence(
    tmp_path: Path,
    *,
    member: str,
    kind: F.FidelityReference,
    reference_rows: list[dict] | None = None,
    generated_rows: list[dict] | None = None,
    population_complete: bool = True,
    reference_lineage: str = "a" * 64,
    generated_lineage: str = "a" * 64,
) -> tuple[Path, str, Path, Path]:
    reference_rows = reference_rows or [
        {"candidate_id": "a", "decision_time_utc": "2026-01-01T00:00:00Z"},
        {"candidate_id": "b", "decision_time_utc": "2026-01-01T00:01:00Z"},
    ]
    generated_rows = generated_rows or list(reference_rows)
    reference_path = tmp_path / "reference.jsonl"
    generated_path = tmp_path / "generated.jsonl"
    reference_sha = _write_jsonl(reference_path, reference_rows)
    generated_sha = _write_jsonl(generated_path, generated_rows)
    reference_lineage_authority = _authority(
        tmp_path / "reference_lineage.json", reference_lineage
    )
    generated_lineage_authority = (
        reference_lineage_authority
        if generated_lineage == reference_lineage
        else _authority(tmp_path / "generated_lineage.json", generated_lineage)
    )
    reference = {
        "kind": kind.value,
        "source_path": reference_path.name,
        "source_sha256": reference_sha,
    }
    if kind is F.FidelityReference.LIVE_RECORD:
        reference["recording_authority"] = {
            "capture_id": "recorded-generator-shadow-2026-01-01",
            **_authority(tmp_path / "recording_authority.json", "recorded-capture"),
        }
    else:
        reference["lineage_authority"] = reference_lineage_authority
    manifest = {
        "schema": F.STRUCTURED_EVIDENCE_SCHEMA,
        "member": member,
        "identity_fields": ["candidate_id", "decision_time_utc"],
        "reference": reference,
        "generated": {
            "source_path": generated_path.name,
            "source_sha256": generated_sha,
            "lineage_authority": generated_lineage_authority,
            "population_complete": population_complete,
        },
    }
    manifest_path = tmp_path / "fidelity_evidence.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2))
    return (
        manifest_path,
        hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        reference_path,
        generated_path,
    )


def _register_structured(tmp_path: Path, *, member: str = "candidate", **evidence_fields):
    manifest, digest, _, _ = _structured_evidence(
        tmp_path, member=member, **evidence_fields
    )
    return F.register_structured_fidelity_measurement(
        member,
        source=str(manifest),
        source_sha256=digest,
    )


def test_legacy_direct_replay_measurement_remains_historical_v1_evidence():
    rec = _register()
    assert rec.basis is F.FidelityBasis.MEASURED_DIRECT
    assert rec.reference_kind is F.FidelityReference.REPLAY_REFERENCE
    assert rec.evidence_authority is F.FidelityEvidenceAuthority.CALLER_COUNTS
    assert rec.measurement_schema == F.LEGACY_CALLER_COUNTS_SCHEMA
    assert rec.reference_recall == 1.0
    # Historical v1 callers can still reproduce their receipt directly.
    assert rec.refusal_reason(0.50) is None
    stamp = rec.ceiling_stamp(0.50)
    assert "100% replay-reference recall" in stamp
    assert "live-recall" not in stamp
    assert "generated-only precision unavailable" in rec.basis_note
    assert F.fidelity_for(rec.sleeve) == rec


def test_direct_replay_measurement_clears_floor_without_claiming_live_recall():
    """Retain the sealed-baseline identity at the historical-v1 record boundary."""

    rec = _register()
    assert rec.basis is F.FidelityBasis.MEASURED_DIRECT
    assert rec.reference_kind is F.FidelityReference.REPLAY_REFERENCE
    assert rec.evidence_authority is F.FidelityEvidenceAuthority.CALLER_COUNTS
    assert rec.measurement_schema == F.LEGACY_CALLER_COUNTS_SCHEMA
    assert rec.reference_recall == 1.0
    assert rec.refusal_reason(0.50) is None
    assert "live-recall" not in rec.ceiling_stamp(0.50)


def test_legacy_caller_counts_cannot_clear_a_v2_gate():
    rec = _register()
    spec, sleeve = _fidelity_gate(rec)
    assert sleeve.gates["fidelity"]["pass"] is False
    assert sleeve.gates["fidelity"]["reference_policy"] == "independent_or_live"
    assert sleeve.gates["fidelity"]["measurement_schema"] == F.LEGACY_CALLER_COUNTS_SCHEMA
    assert sleeve.gates["fidelity"]["evidence_authority"] == "caller_counts"
    assert any(reason.startswith("fidelity_evidence_unstructured") for reason in sleeve.reasons)
    assert sleeve.verdict.value == "NOT_EVALUABLE"
    assert spec.schema == "gtos.walkforward.gate_spec.v2"
    assert sleeve.fidelity["reference_kind"] == "replay_reference"
    assert sleeve.fidelity["reference_recall"] == 1.0
    assert sleeve.fidelity["live_recall"] is None
    assert "replay-reference recall" in sleeve.fidelity["ceiling_stamp"]


def test_gate_serializes_replay_reference_without_populating_live_recall():
    """Keep the baseline node while pinning the repaired current-v2 refusal."""

    rec = _register()
    spec, sleeve = _fidelity_gate(rec)
    assert spec.schema == "gtos.walkforward.gate_spec.v2"
    assert sleeve.gates["fidelity"]["pass"] is False
    assert sleeve.gates["fidelity"]["evidence_authority"] == "caller_counts"
    assert sleeve.verdict.value == "NOT_EVALUABLE"
    assert sleeve.fidelity["reference_kind"] == "replay_reference"
    assert sleeve.fidelity["reference_recall"] == 1.0
    assert sleeve.fidelity["live_recall"] is None


def test_direct_measurement_is_process_local_and_cannot_overwrite_authority():
    rec = _register()
    assert F.direct_fidelity_measurements() == {rec.sleeve: rec}
    with pytest.raises(ValueError, match="already has a direct measurement"):
        _register()
    with pytest.raises(ValueError, match="AUTHORED"):
        F.register_direct_fidelity_measurement(
            "fx_jpy",
            agreed=1,
            reference_only=0,
            generated_only=0,
            reference_kind=F.FidelityReference.LIVE_RECORD,
            source=str(SOURCE),
            source_sha256=SOURCE_SHA256,
        )
    assert F.clear_direct_fidelity_measurements() == 1
    assert F.fidelity_for(rec.sleeve).basis is F.FidelityBasis.UNMEASURED


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"agreed": 0, "reference_only": 0}, "at least one reference identity"),
        ({"agreed": -1, "reference_only": 1}, "non-negative integer"),
        ({"agreed": 1, "reference_only": 0, "source_sha256": "short"}, "64 lowercase hex"),
    ],
)
def test_invalid_or_unbound_measurements_are_refused(kwargs, message):
    args = {
        "member": "candidate",
        "agreed": 1,
        "reference_only": 0,
        "generated_only": None,
        "reference_kind": F.FidelityReference.REPLAY_REFERENCE,
        "source": str(SOURCE),
        "source_sha256": SOURCE_SHA256,
    }
    args.update(kwargs)
    with pytest.raises(ValueError, match=message):
        F.register_direct_fidelity_measurement(**args)


def test_same_lineage_replay_cannot_clear_independent_or_live_gate(tmp_path):
    rec = _register_structured(
        tmp_path,
        kind=F.FidelityReference.SAME_LINEAGE_REPLAY,
        reference_lineage="a" * 64,
        generated_lineage="a" * 64,
    )
    _, sleeve = _fidelity_gate(rec)
    assert rec.reference_recall == 1.0
    assert sleeve.gates["fidelity"]["pass"] is False
    assert any(
        reason.startswith("fidelity_reference_policy_mismatch")
        for reason in sleeve.reasons
    )


def test_altered_caller_counts_over_unchanged_source_never_forge_v2_pass():
    first = _register(member="caller_count_probe")
    _, first_verdict = _fidelity_gate(first)
    F.clear_direct_fidelity_measurements()
    second = F.register_direct_fidelity_measurement(
        "caller_count_probe",
        agreed=1_000_000,
        reference_only=0,
        generated_only=0,
        reference_kind=F.FidelityReference.LIVE_RECORD,
        source=str(SOURCE),
        source_sha256=SOURCE_SHA256,
    )
    _, second_verdict = _fidelity_gate(second)
    assert first.source == second.source
    assert first.basis_agreed != second.basis_agreed
    assert first_verdict.gates["fidelity"]["pass"] is False
    assert second_verdict.gates["fidelity"]["pass"] is False
    assert all(
        any(reason.startswith("fidelity_evidence_unstructured") for reason in verdict.reasons)
        for verdict in (first_verdict, second_verdict)
    )


def test_structured_source_hash_mismatch_or_missing_schema_refuses(tmp_path):
    manifest, digest, reference_path, _ = _structured_evidence(
        tmp_path,
        member="hash_probe",
        kind=F.FidelityReference.INDEPENDENT_REPLAY,
        generated_lineage="b" * 64,
    )
    reference_path.write_text(reference_path.read_text() + '{"candidate_id":"drift"}\n')
    with pytest.raises(ValueError, match="source hash mismatch"):
        F.register_structured_fidelity_measurement(
            "hash_probe", source=str(manifest), source_sha256=digest
        )

    missing = tmp_path / "missing_schema.json"
    missing.write_text(json.dumps({"agreed": 999, "reference_only": 0}))
    with pytest.raises(ValueError, match="missing structured fidelity evidence"):
        F.register_structured_fidelity_measurement(
            "missing_probe",
            source=str(missing),
            source_sha256=hashlib.sha256(missing.read_bytes()).hexdigest(),
        )


def test_null_precision_refuses_when_sealed_policy_requires_precision(tmp_path):
    rec = _register_structured(
        tmp_path,
        kind=F.FidelityReference.INDEPENDENT_REPLAY,
        generated_lineage="b" * 64,
        population_complete=False,
    )
    _, sleeve = _fidelity_gate(rec, fidelity_precision_floor=0.50)
    assert rec.precision is None
    assert rec.precision_supported is False
    assert sleeve.gates["fidelity"]["pass"] is False
    assert any(reason.startswith("fidelity_precision_unmeasured") for reason in sleeve.reasons)


def test_same_lineage_measurement_legitimately_passes_replay_consistency_policy(tmp_path):
    rec = _register_structured(
        tmp_path,
        kind=F.FidelityReference.SAME_LINEAGE_REPLAY,
        generated_rows=[
            {"candidate_id": "a", "decision_time_utc": "2026-01-01T00:00:00Z"},
            {"candidate_id": "b", "decision_time_utc": "2026-01-01T00:01:00Z"},
            {"candidate_id": "extra", "decision_time_utc": "2026-01-01T00:02:00Z"},
        ],
    )
    _, sleeve = _fidelity_gate(
        rec,
        fidelity_reference_policy=F.FidelityReferencePolicy.REPLAY_CONSISTENCY.value,
        fidelity_precision_floor=0.60,
    )
    assert rec.basis_agreed == 2
    assert rec.basis_live_only == 0
    assert rec.basis_port_only == 1
    assert rec.reference_recall == 1.0
    assert rec.precision == pytest.approx(2 / 3)
    assert sleeve.gates["fidelity"]["pass"] is True


@pytest.mark.parametrize(
    "kind",
    [F.FidelityReference.INDEPENDENT_REPLAY, F.FidelityReference.LIVE_RECORD],
)
def test_independent_or_recorded_measurement_legitimately_passes(tmp_path, kind):
    rec = _register_structured(
        tmp_path,
        kind=kind,
        generated_lineage="b" * 64,
    )
    _, sleeve = _fidelity_gate(rec, fidelity_precision_floor=1.0)
    assert rec.evidence_authority is F.FidelityEvidenceAuthority.STRUCTURED_IDENTITY_COMPARISON
    assert rec.reference_recall == 1.0
    assert rec.precision == 1.0
    assert sleeve.gates["fidelity"]["pass"] is True


def test_cr_v1_same_lineage_receipt_stays_historical_and_not_evaluable():
    fidelity = json.loads(CR_FIDELITY.read_text())
    measurement = fidelity["measurement"]
    rec = F.register_direct_fidelity_measurement(
        fidelity["sleeve"],
        agreed=measurement["agreed"],
        reference_only=measurement["reference_only"],
        generated_only=measurement["generated_only"],
        reference_kind=fidelity["reference_kind"],
        source=str(CR_FIDELITY),
        source_sha256=hashlib.sha256(CR_FIDELITY.read_bytes()).hexdigest(),
    )
    _, sleeve = _fidelity_gate(rec)
    result = json.loads(CR_RESULT.read_text())
    assert "same code lineage" in measurement["caveat"]
    assert measurement["precision"] is None
    assert sleeve.gates["fidelity"]["pass"] is False
    assert any(reason.startswith("fidelity_evidence_unstructured") for reason in sleeve.reasons)
    assert result["verdict"] == "NOT_EVALUABLE"
    assert result["status"] == "FROZEN_GATE_NOT_EVALUABLE_RECORDED_EXECUTABLE_POPULATION_REQUIRED"

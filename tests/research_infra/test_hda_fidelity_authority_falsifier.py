"""Session HDA adversaries for the fidelity-authority boundary.

These tests are intentionally narrower than a generic evidence-security framework.  They
exercise only public mutation/registration, manifest relabelling, identity derivation, and
legacy/current serialization paths that can move the walk-forward fidelity verdict.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from src.research_infra.walkforward import fidelity as F
from src.research_infra.walkforward.gate import run_gate
from src.research_infra.walkforward.options import OPTIONS
from src.research_infra.walkforward.spec import (
    DEFAULT_SPEC,
    LEGACY_DEFAULT_SPEC,
    LEGACY_SCHEMA,
    SCHEMA,
    GateSpec,
)


@pytest.fixture(autouse=True)
def _clean_process_local_registers():
    F.clear_direct_fidelity_measurements()
    F.clear_surface_expansions()
    yield
    F.clear_direct_fidelity_measurements()
    F.clear_surface_expansions()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_jsonl(path: Path, rows: list[dict] | None = None, *, raw: str | None = None) -> str:
    if raw is None:
        assert rows is not None
        raw = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    path.write_text(raw, encoding="utf-8")
    return _sha(path)


def _authority(path: Path, identity: str) -> dict[str, str]:
    path.write_text(
        json.dumps(
            {
                "schema": "gtos.walkforward.generator_lineage.v1",
                "identity": identity,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"source_path": path.name, "source_sha256": _sha(path)}


def _manifest(
    tmp_path: Path,
    *,
    member: str = "hda_candidate",
    kind: F.FidelityReference = F.FidelityReference.INDEPENDENT_REPLAY,
    reference_rows: list[dict] | None = None,
    generated_rows: list[dict] | None = None,
    reference_raw: str | None = None,
    generated_raw: str | None = None,
    population_complete: bool = True,
    include_lineage_authority: bool = True,
    include_recording_authority_source: bool = True,
    same_population_path: bool = False,
    generated_absolute: bool = False,
    extra_manifest_fields: dict | None = None,
) -> tuple[Path, str]:
    if reference_rows is None and reference_raw is None:
        reference_rows = [
            {"candidate_id": "a", "decision_time_utc": "2026-01-01T00:00:00Z"},
            {"candidate_id": "b", "decision_time_utc": "2026-01-01T00:01:00Z"},
        ]
    if generated_rows is None and generated_raw is None:
        generated_rows = list(reference_rows or [])

    reference_path = tmp_path / "reference.jsonl"
    generated_path = tmp_path / "generated.jsonl"
    reference_sha = _write_jsonl(reference_path, reference_rows, raw=reference_raw)
    if same_population_path:
        generated_path.symlink_to(reference_path)
        generated_sha = reference_sha
    else:
        generated_sha = _write_jsonl(generated_path, generated_rows, raw=generated_raw)

    reference_lineage = _authority(tmp_path / "reference_lineage.json", "reference")
    generated_lineage = (
        reference_lineage
        if kind is F.FidelityReference.SAME_LINEAGE_REPLAY
        else _authority(tmp_path / "generated_lineage.json", "generated")
    )
    reference: dict = {
        "kind": kind.value,
        "source_path": reference_path.name,
        "source_sha256": reference_sha,
    }
    if kind is F.FidelityReference.LIVE_RECORD:
        recording = {"capture_id": "hda-recorded-capture"}
        if include_recording_authority_source:
            recording.update(_authority(tmp_path / "recording_authority.json", "recording"))
        reference["recording_authority"] = recording
    else:
        # The scalar is present so this same adversary runs against the untouched HA builder,
        # which trusted it.  The repaired contract must use the hash-bound descriptor instead.
        reference["lineage_sha256"] = reference_lineage["source_sha256"]
        if include_lineage_authority:
            reference["lineage_authority"] = reference_lineage

    generated_source = str(generated_path.resolve()) if generated_absolute else generated_path.name
    generated: dict = {
        "source_path": generated_source,
        "source_sha256": generated_sha,
        "lineage_sha256": generated_lineage["source_sha256"],
        "population_complete": population_complete,
    }
    if include_lineage_authority:
        generated["lineage_authority"] = generated_lineage

    document = {
        "schema": F.STRUCTURED_EVIDENCE_SCHEMA,
        "member": member,
        "identity_fields": ["candidate_id", "decision_time_utc"],
        "reference": reference,
        "generated": generated,
        **(extra_manifest_fields or {}),
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(document, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path, _sha(path)


def _register(tmp_path: Path, **kwargs) -> F.Fidelity:
    member = kwargs.get("member", "hda_candidate")
    path, digest = _manifest(tmp_path, **kwargs)
    return F.register_structured_fidelity_measurement(
        member,
        source=str(path),
        source_sha256=digest,
    )


def _legacy_caller_count(member: str) -> F.Fidelity:
    source = Path(__file__).resolve()
    return F.register_direct_fidelity_measurement(
        member,
        agreed=249,
        reference_only=0,
        generated_only=None,
        reference_kind=F.FidelityReference.REPLAY_REFERENCE,
        source=str(source),
        source_sha256=_sha(source),
    )


def test_public_authored_register_cannot_be_mutated_into_v2_authority():
    member = "hda_public_register_forgery"
    forged = F.Fidelity(
        sleeve=member,
        cls=F.FidelityClass.PER_BAR,
        basis=F.FidelityBasis.MEASURED_DIRECT,
        live_recall=1.0,
        basis_agreed=999,
        basis_live_only=0,
        basis_port_only=0,
        basis_note="caller-created object",
    )
    try:
        with pytest.raises(TypeError):
            F.FIDELITY_REGISTER[member] = forged
    finally:
        # Cleanup is needed only against the vulnerable builder implementation.
        if isinstance(F.FIDELITY_REGISTER, dict):
            F.FIDELITY_REGISTER.pop(member, None)
    assert F.fidelity_for(member).basis is F.FidelityBasis.UNMEASURED


def test_process_local_registrars_share_one_nonshadowable_namespace(tmp_path):
    member = "mxf_hda_collision"
    direct = _legacy_caller_count(member)
    with pytest.raises(ValueError, match="already has a direct measurement"):
        F.register_surface_expansion(
            member,
            parent="crypto",
            symbol="ETHUSD",
            timeframe="H4",
        )
    assert F.fidelity_for(member) is direct

    F.clear_direct_fidelity_measurements()
    first = F.register_surface_expansion(
        member,
        parent="crypto",
        symbol="ETHUSD",
        timeframe="H4",
    )
    with pytest.raises(ValueError, match="already has a temporary"):
        F.register_surface_expansion(
            member,
            parent="crypto",
            symbol="BTCUSD",
            timeframe="D1",
        )
    assert F.fidelity_for(member) is first

    F.clear_surface_expansions()
    threshold_member = "thr_hda_collision"
    direct = _legacy_caller_count(threshold_member)
    with pytest.raises(ValueError, match="already has a direct measurement"):
        F.register_threshold_variant(
            threshold_member,
            parent="sub_xvol_pullback",
            params={"vr_xhi": 1.4},
            production_params={"vr_xhi": 1.6},
        )
    assert F.fidelity_for(threshold_member) is direct

    F.clear_direct_fidelity_measurements()
    first_threshold = F.register_threshold_variant(
        threshold_member,
        parent="sub_xvol_pullback",
        params={"vr_xhi": 1.4},
        production_params={"vr_xhi": 1.6},
    )
    with pytest.raises(ValueError, match="already has a temporary"):
        F.register_threshold_variant(
            threshold_member,
            parent="sub_xvol_pullback",
            params={"vr_xhi": 1.3},
            production_params={"vr_xhi": 1.6},
        )
    assert F.fidelity_for(threshold_member) is first_threshold


def test_relabelled_same_lineage_needs_hash_bound_lineage_authority(tmp_path):
    with pytest.raises(ValueError, match="lineage_authority"):
        _register(tmp_path, include_lineage_authority=False)


def test_fake_live_label_needs_hash_bound_recording_authority(tmp_path):
    with pytest.raises(ValueError, match="recording_authority"):
        _register(
            tmp_path,
            kind=F.FidelityReference.LIVE_RECORD,
            include_recording_authority_source=False,
        )


def test_independent_sources_cannot_be_two_paths_to_one_canonical_population(tmp_path):
    with pytest.raises(ValueError, match="same canonical population"):
        _register(tmp_path, same_population_path=True)


def test_independent_sources_cannot_be_hard_links_to_one_population(tmp_path):
    path, _ = _manifest(tmp_path)
    reference_path = tmp_path / "reference.jsonl"
    generated_path = tmp_path / "generated.jsonl"
    generated_path.unlink()
    os.link(reference_path, generated_path)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["generated"]["source_sha256"] = _sha(generated_path)
    path.write_text(json.dumps(document, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="same canonical population"):
        F.register_structured_fidelity_measurement(
            "hda_candidate",
            source=str(path),
            source_sha256=_sha(path),
        )


def test_nonstandard_json_constants_are_not_identity_values(tmp_path):
    row = '{"candidate_id":NaN,"decision_time_utc":"2026-01-01T00:00:00Z"}\n'
    with pytest.raises(ValueError, match="not JSON"):
        _register(tmp_path, reference_raw=row, generated_raw=row)


def test_manifest_hash_drift_is_refused_before_any_nested_claim_is_read(tmp_path):
    path, digest = _manifest(tmp_path)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["measurement"] = {"agreed": 1_000_000, "reference_only": 0}
    path.write_text(json.dumps(document, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="source hash mismatch"):
        F.register_structured_fidelity_measurement(
            "hda_candidate",
            source=str(path),
            source_sha256=digest,
        )


def test_population_hash_drift_is_refused(tmp_path):
    path, digest = _manifest(tmp_path)
    _write_jsonl(
        tmp_path / "reference.jsonl",
        [{"candidate_id": "drifted", "decision_time_utc": "t"}],
    )

    with pytest.raises(ValueError, match="source hash mismatch"):
        F.register_structured_fidelity_measurement(
            "hda_candidate",
            source=str(path),
            source_sha256=digest,
        )


def test_population_hash_drift_is_refused_before_drifted_json_is_parsed(tmp_path):
    path, digest = _manifest(tmp_path)
    (tmp_path / "reference.jsonl").write_text("{not-json}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="source hash mismatch"):
        F.register_structured_fidelity_measurement(
            "hda_candidate",
            source=str(path),
            source_sha256=digest,
        )


def test_manifest_path_replacement_cannot_change_the_bytes_parsed(
    tmp_path, monkeypatch
):
    path, digest = _manifest(
        tmp_path,
        kind=F.FidelityReference.SAME_LINEAGE_REPLAY,
    )
    forged = json.loads(path.read_text(encoding="utf-8"))
    generated_authority = _authority(
        tmp_path / "replacement_generated_lineage.json", "replacement"
    )
    forged["reference"]["kind"] = F.FidelityReference.INDEPENDENT_REPLAY.value
    forged["generated"]["lineage_authority"] = generated_authority
    replacement = tmp_path / "replacement_manifest.json"
    replacement.write_text(
        json.dumps(forged, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )

    original_open = Path.open
    swapped = False

    def replace_after_open(self, *args, **kwargs):
        nonlocal swapped
        handle = original_open(self, *args, **kwargs)
        mode = args[0] if args else kwargs.get("mode", "r")
        if self == path and "r" in mode and not swapped:
            replacement.replace(path)
            swapped = True
        return handle

    monkeypatch.setattr(Path, "open", replace_after_open)
    rec = F.register_structured_fidelity_measurement(
        "hda_candidate", source=str(path), source_sha256=digest
    )

    assert swapped is True
    assert _sha(path) != digest
    assert rec.reference_kind is F.FidelityReference.SAME_LINEAGE_REPLAY
    assert rec.reference_lineage_sha256 == rec.generated_lineage_sha256


def test_population_path_replacement_cannot_change_hash_bound_counts(
    tmp_path, monkeypatch
):
    reference_rows = [
        {"candidate_id": "a", "decision_time_utc": "t"},
        {"candidate_id": "b", "decision_time_utc": "t"},
    ]
    path, digest = _manifest(
        tmp_path,
        reference_rows=reference_rows,
        generated_rows=reference_rows[:1],
    )
    reference_path = tmp_path / "reference.jsonl"
    bound_reference_sha = _sha(reference_path)
    replacement = tmp_path / "replacement_reference.jsonl"
    _write_jsonl(replacement, reference_rows[:1])

    original_open = Path.open
    swapped = False

    def replace_after_open(self, *args, **kwargs):
        nonlocal swapped
        handle = original_open(self, *args, **kwargs)
        mode = args[0] if args else kwargs.get("mode", "r")
        if self == reference_path and "r" in mode and not swapped:
            replacement.replace(reference_path)
            swapped = True
        return handle

    monkeypatch.setattr(Path, "open", replace_after_open)
    rec = F.register_structured_fidelity_measurement(
        "hda_candidate", source=str(path), source_sha256=digest
    )

    assert swapped is True
    assert _sha(reference_path) != bound_reference_sha
    assert (rec.basis_agreed, rec.basis_live_only, rec.basis_port_only) == (1, 1, 0)


def test_same_path_population_alias_stays_refused_across_replacement(
    tmp_path, monkeypatch
):
    path, _ = _manifest(tmp_path)
    shared_path = tmp_path / "reference.jsonl"
    replacement = tmp_path / "same_path_replacement.jsonl"
    replacement_sha = _write_jsonl(
        replacement,
        [{"candidate_id": "replacement", "decision_time_utc": "t"}],
    )
    document = json.loads(path.read_text(encoding="utf-8"))
    document["generated"]["source_path"] = shared_path.name
    document["generated"]["source_sha256"] = replacement_sha
    path.write_text(json.dumps(document, sort_keys=True) + "\n", encoding="utf-8")
    digest = _sha(path)

    original_open = Path.open
    population_opens = 0
    swapped = False

    def replace_after_first_population_open(self, *args, **kwargs):
        nonlocal population_opens, swapped
        handle = original_open(self, *args, **kwargs)
        mode = args[0] if args else kwargs.get("mode", "r")
        if self == shared_path and "r" in mode:
            population_opens += 1
            if population_opens == 1:
                replacement.replace(shared_path)
                swapped = True
        return handle

    monkeypatch.setattr(Path, "open", replace_after_first_population_open)
    with pytest.raises(ValueError, match="same canonical population"):
        F.register_structured_fidelity_measurement(
            "hda_candidate",
            source=str(path),
            source_sha256=digest,
        )
    assert swapped is True


@pytest.mark.parametrize(
    ("kind", "authority_name"),
    [
        (F.FidelityReference.INDEPENDENT_REPLAY, "generated_lineage.json"),
        (F.FidelityReference.LIVE_RECORD, "recording_authority.json"),
    ],
)
def test_lineage_and_recording_authority_hash_drift_refuse(tmp_path, kind, authority_name):
    path, digest = _manifest(tmp_path, kind=kind)
    authority = tmp_path / authority_name
    authority.write_text(authority.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
    with pytest.raises(ValueError, match="source hash mismatch"):
        F.register_structured_fidelity_measurement(
            "hda_candidate",
            source=str(path),
            source_sha256=digest,
        )


def test_counts_are_source_derived_and_scalar_types_do_not_collide(tmp_path):
    reference = [
        {"candidate_id": 1, "decision_time_utc": "t", "ignored": "extra"},
        {"candidate_id": "1", "decision_time_utc": "t", "ignored": {"nested": True}},
        {"candidate_id": True, "decision_time_utc": "t"},
    ]
    generated = reference[:2]
    rec = _register(
        tmp_path,
        reference_rows=reference,
        generated_rows=generated,
        extra_manifest_fields={
            "measurement": {"agreed": 10_000, "reference_only": 0, "generated_only": 0}
        },
    )
    assert (rec.basis_agreed, rec.basis_live_only, rec.basis_port_only) == (2, 1, 0)
    assert rec.reference_recall == pytest.approx(2 / 3)
    assert rec.precision == 1.0


def test_recall_and_precision_use_independent_denominators(tmp_path):
    reference = [
        {"candidate_id": candidate_id, "decision_time_utc": "t"}
        for candidate_id in ("a", "b", "c")
    ]
    generated = [
        {"candidate_id": candidate_id, "decision_time_utc": "t"}
        for candidate_id in ("a", "x", "y")
    ]
    rec = _register(tmp_path, reference_rows=reference, generated_rows=generated)
    assert (rec.basis_agreed, rec.basis_live_only, rec.basis_port_only) == (1, 2, 2)
    assert rec.reference_recall == pytest.approx(1 / 3)
    assert rec.precision == pytest.approx(1 / 3)


def test_blank_lines_and_mixed_absolute_relative_paths_do_not_change_counts(tmp_path):
    raw = (
        "\n"
        '{"candidate_id":"a","decision_time_utc":"t","extra":1}\n'
        "   \n"
        '{"candidate_id":"b","decision_time_utc":"t","extra":2}\n'
    )
    rec = _register(
        tmp_path,
        reference_raw=raw,
        generated_raw=raw,
        generated_absolute=True,
    )
    assert (rec.basis_agreed, rec.basis_live_only, rec.basis_port_only) == (2, 0, 0)


@pytest.mark.parametrize(
    ("reference_raw", "generated_raw", "message"),
    [
        (
            '{"candidate_id":"a","decision_time_utc":"t"}\n'
            '{"candidate_id":"a","decision_time_utc":"t"}\n',
            '{"candidate_id":"a","decision_time_utc":"t"}\n',
            "repeats an identity",
        ),
        (
            '{"candidate_id":"a"}\n',
            '{"candidate_id":"a","decision_time_utc":"t"}\n',
            "misses identity fields",
        ),
        ("{not-json}\n", '{"candidate_id":"a","decision_time_utc":"t"}\n', "not JSON"),
        ("\n  \n", '{"candidate_id":"a","decision_time_utc":"t"}\n', "at least one"),
    ],
)
def test_ambiguous_or_invalid_reference_populations_refuse(
    tmp_path, reference_raw, generated_raw, message
):
    with pytest.raises(ValueError, match=message):
        _register(tmp_path, reference_raw=reference_raw, generated_raw=generated_raw)


def test_empty_generated_population_is_zero_recall_not_a_missing_value_pass(tmp_path):
    rec = _register(tmp_path, generated_rows=[])
    assert rec.reference_recall == 0.0
    assert rec.precision is None
    assert not rec.scoreable(
        0.50,
        reference_policy=F.FidelityReferencePolicy.INDEPENDENT_OR_LIVE,
    )


def test_incomplete_generated_population_has_null_precision_and_only_a_floor_refuses(tmp_path):
    rec = _register(tmp_path, population_complete=False)
    assert rec.reference_recall == 1.0
    assert rec.precision is None
    assert rec.refusal_reason(
        0.50,
        reference_policy=F.FidelityReferencePolicy.INDEPENDENT_OR_LIVE,
    ) is None
    assert rec.refusal_reason(
        0.50,
        reference_policy=F.FidelityReferencePolicy.INDEPENDENT_OR_LIVE,
        precision_floor=0.01,
    ).startswith("fidelity_precision_unmeasured")


def test_current_defaults_and_all_published_options_are_v2():
    assert DEFAULT_SPEC.schema == SCHEMA
    assert DEFAULT_SPEC.fidelity_reference_policy == "independent_or_live"
    assert all(spec.schema == SCHEMA for spec in OPTIONS.values())
    assert all(spec.fidelity_reference_policy != "legacy_any_reference" for spec in OPTIONS.values())


def test_gate_spec_v1_v2_read_write_boundary_roundtrips(tmp_path):
    for name, spec in (("v1", LEGACY_DEFAULT_SPEC), ("v2", DEFAULT_SPEC)):
        path = tmp_path / f"{name}.json"
        spec.write(str(path))
        raw = json.loads(path.read_text(encoding="utf-8"))
        restored = GateSpec.read(
            str(path), allow_legacy=spec.schema == LEGACY_SCHEMA
        )
        assert restored.schema == spec.schema
        assert restored.seal() == spec.seal()
        if spec.schema == LEGACY_SCHEMA:
            assert "fidelity_reference_policy" not in raw
            assert "fidelity_precision_floor" not in raw
            assert "capture_windows" not in raw
            assert "capture_declaration_id" not in raw
            assert "capture_declaration_sha256s" not in raw
        else:
            assert raw["fidelity_reference_policy"] == "independent_or_live"


def test_legacy_spec_read_requires_explicit_historical_opt_in(tmp_path):
    path = tmp_path / "legacy.json"
    LEGACY_DEFAULT_SPEC.write(str(path))

    with pytest.raises(ValueError, match="allow_legacy=True explicitly"):
        GateSpec.read(str(path))

    restored = GateSpec.read(str(path), allow_legacy=True)
    assert restored.schema == LEGACY_SCHEMA
    assert restored.seal() == LEGACY_DEFAULT_SPEC.seal()


def test_capture_authority_cannot_downgrade_to_legacy_schema(tmp_path):
    current = DEFAULT_SPEC.with_(
        capture_windows=(("2026-01-01", "2026-01-30"),),
        capture_declaration_id="HDA_HDF_CAPTURE_AUTHORITY",
        capture_declaration_sha256s=("1" * 64,),
    )
    payload = current.as_dict()
    payload["schema"] = LEGACY_SCHEMA
    path = tmp_path / "forged-legacy-capture.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="cannot carry capture authority"):
        GateSpec.read(str(path), allow_legacy=True)


def test_legacy_spec_cannot_emit_a_v2_authority_result():
    rec = _legacy_caller_count("hda_legacy_result")
    implicit = run_gate({rec.sleeve: []}).as_dict()
    assert implicit["schema"] == "gtos.walkforward.gate_result.v2"
    assert implicit["sleeves"][rec.sleeve]["gates"]["fidelity"]["pass"] is False

    current = run_gate({rec.sleeve: []}, DEFAULT_SPEC).as_dict()
    assert current["schema"] == "gtos.walkforward.gate_result.v2"
    assert current["sleeves"][rec.sleeve]["gates"]["fidelity"]["pass"] is False

    legacy = run_gate({rec.sleeve: []}, LEGACY_DEFAULT_SPEC).as_dict()
    assert legacy["schema"] == "gtos.walkforward.gate_result.v1"
    assert legacy["spec"]["schema"] == LEGACY_SCHEMA
    assert "measurement_schema" not in legacy["sleeves"][rec.sleeve]["fidelity"]
    assert "reference_policy" not in legacy["sleeves"][rec.sleeve]["gates"]["fidelity"]

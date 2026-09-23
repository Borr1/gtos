from __future__ import annotations

import copy
import gzip
import hashlib
import json
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import pytest

from src.research_infra import p1_upstream_packet_verifier as subject


UTC = timezone.utc
SOURCE_COMMIT = "f59fbb829a5561b7e7b78bed324d67a8c01d6e74"
SOURCE_PARENT = "1c81f5cd384671a4a99ddcda49f9dfc6ef7bae51"


def _bar(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "time": "2026-01-02T00:00:00+00:00",
        "time_utc": "2026-01-02T00:00:00+00:00",
        "symbol": "XAUUSD",
        "open": 100.0,
        "high": 102.0,
        "low": 99.0,
        "close": 101.0,
        "volume": 10.0,
    }
    row.update(overrides)
    return row


def _descriptor(path: Path, *, relative_to: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(relative_to).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _write_gzip(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(subject.deterministic_jsonl_gzip_bytes(rows))


def _write_manifest(packet: Path, manifest: dict[str, Any]) -> str:
    path = packet / "PACKET_MANIFEST.json"
    path.write_bytes(subject.canonical(manifest) + b"\n")
    return subject.file_hash(path)


def _fixture(tmp_path: Path) -> dict[str, Any]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    authority_root = tmp_path / "authority"
    source_root = tmp_path / "source"
    stage = tmp_path / "stage"
    authority_root.mkdir()
    source_root.mkdir()
    stage.mkdir()
    trusted = authority_root / "trusted.txt"
    trusted.write_bytes(b"fixture authority\n")
    trusted_descriptor = _descriptor(trusted, relative_to=authority_root)
    trusted_sha = str(trusted_descriptor["sha256"])
    adapter_relative = (
        "docs/audits/fable5-vision-audit-20260725/phase20/receipts/"
        "wave20_complete_path_shadow.py"
    )
    adapter_source = Path(subject.REPO_ROOT) / adapter_relative
    fixture_adapter = authority_root / adapter_relative
    fixture_adapter.parent.mkdir(parents=True)
    fixture_adapter.write_bytes(adapter_source.read_bytes())
    adapter_descriptor = _descriptor(fixture_adapter, relative_to=authority_root)
    expectations = replace(
        subject._PRODUCTION_EXPECTATIONS,
        symbols=("XAUUSD",), total=2,
        window_counts=(("january", 2),),
        windows=(("january", ("2026-01-01", "2026-01-30")),),
        state_count=1, payload_count=5, reused_candidate_ids=0,
        rows_under_reused_candidate_ids=0, source_payload_count=0,
        source_root=source_root, repo_root=authority_root,
        repo_authorities=(("trusted.txt", trusted_sha, trusted.stat().st_size),),
        transitive_paths=("trusted.txt",), source_manifests=(),
        evidence_lineage=(), evidence_artifacts=(), tooling_paths=(adapter_relative,),
        source_commit_bound_paths=(), source_parent=SOURCE_PARENT,
        generator_path="trusted.txt", generator_sha256=trusted_sha,
        market_state_path="trusted.txt", market_state_sha256=trusted_sha,
        h1_reference_path="trusted.txt", h1_reference_sha256=trusted_sha,
        timebase_sha256="f" * 64, m15_lookback=52, h1_lookback=13,
        minimum_closed_m15=51, partial_h1_buckets=0,
        referenced_partial_h1_buckets=0,
    )

    start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    m15: list[dict[str, Any]] = []
    for number in range(52):
        timestamp = start + timedelta(minutes=15 * number)
        price = 100.0 + number / 10
        m15.append(_bar(
            time=timestamp.isoformat(), time_utc=timestamp.isoformat(),
            open=price, high=price + 1.0, low=price - 1.0,
            close=price + 0.25, volume=10.0,
        ))
    h1 = subject.independently_aggregate_h1(m15, "XAUUSD")
    m15_path = stage / "series/XAUUSD.m15.jsonl.gz"
    h1_path = stage / "series/XAUUSD.h1.jsonl.gz"
    _write_gzip(m15_path, m15)
    _write_gzip(h1_path, h1)
    decision = datetime(2026, 1, 1, 13, 0, tzinfo=UTC)
    decision_text = decision.isoformat()
    state_id = "state_" + subject.canonical_hash({
        "symbol": "XAUUSD", "decision_time_utc": decision_text,
    })[:24]
    state = {
        "state_id": state_id, "symbol": "XAUUSD",
        "decision_time_utc": decision_text,
        "m15_slice": subject.expected_slice_metadata(m15, (0, 52), prefix="m15", minutes=15),
        "h1_slice": subject.expected_slice_metadata(h1, (0, 13), prefix="h1", minutes=60),
        "m15_atr_14": 1.0, "h1_breaker_blocks": [],
        "h1_breaker_blocks_sha256": subject.canonical_hash([]),
        "uses_outcome_fields": False,
    }
    state["state_sha256"] = subject.canonical_hash(state)
    states_path = stage / "states/predecision_market_state.jsonl.gz"
    _write_gzip(states_path, [state])

    domain: dict[tuple[str, str, str, str], dict[str, str]] = {}
    identities: list[dict[str, Any]] = []
    for candidate_id, side in (("fixture-a", "LONG"), ("fixture-b", "SHORT")):
        key = (candidate_id, "XAUUSD", side, decision_text)
        controls = {
            "window": "january", "kill_zone": "ny",
            "origin_family": "current_breaker_re_entry",
            "framework": "breaker_re_entry",
            "route_family": "current_breaker_re_entry",
        }
        domain[key] = controls
        identity = {
            "identity": dict(zip(("candidate_id", "symbol", "side", "decision_time_utc"), key)),
            **controls, "state_id": state_id, "symbol": "XAUUSD",
            "decision_time_utc": decision_text,
            "m15_series_path": "series/XAUUSD.m15.jsonl.gz",
            "h1_series_path": "series/XAUUSD.h1.jsonl.gz",
            "m15_slice": [0, 52], "h1_slice": [0, 13],
            "generator_match_count": 1, "uses_outcome_fields": False,
        }
        identity["identity_slice_sha256"] = subject.canonical_hash(identity)
        identities.append(identity)
    index_path = stage / "identity_to_slice.jsonl.gz"
    _write_gzip(index_path, identities)
    coverage = {
        "schema": "gtos.p1-upstream-source-coverage.v1", "status": "COMPLETE",
        "identity_rows": 2, "identity_matches": 2,
        "unique_composite_identities": 2, "duplicate_composite_identities": 0,
        "unmatched_identities": 0, "duplicate_generator_matches": 0,
        "predecision_state_count": 1, "window_counts": {"january": 2},
        "minimum_closed_m15_bars": 52, "required_minimum_closed_m15_bars": 51,
        "h1_lookback": 13, "postdecision_reads": 0, "out_of_window_rows": 0,
        "source_multiplicity_by_symbol": {"XAUUSD": 2},
        "candidate_ids_reused": 0, "rows_under_reused_candidate_ids": 0,
        "execution_authority": False, "activation_authority": False,
        "result_bearing_science_executed": False,
        "result_use_status": subject.RESULT_USE_STATUS,
    }
    coverage_path = stage / "SOURCE_COVERAGE.json"
    coverage_path.write_bytes(subject.canonical(coverage) + b"\n")
    payload_files = [
        _descriptor(path, relative_to=stage)
        for path in (coverage_path, index_path, h1_path, m15_path, states_path)
    ]
    payload_files.sort(key=lambda row: str(row["path"]))
    payload_root = subject.canonical_hash({
        "schema": "gtos.p1-upstream-packet-payload.v1", "files": payload_files,
    })
    packet = tmp_path / f"p1-source-packet-sha256-{payload_root}"
    stage.rename(packet)
    series = {
        "XAUUSD": {
            "M15": {
                **_descriptor(packet / "series/XAUUSD.m15.jsonl.gz", relative_to=packet),
                "row_count": len(m15), "first_utc": m15[0]["time_utc"],
                "last_utc": m15[-1]["time_utc"], "time_column_basis": "true_utc",
                "timeframe_minutes": 15,
            },
            "H1": {
                **_descriptor(packet / "series/XAUUSD.h1.jsonl.gz", relative_to=packet),
                "row_count": len(h1), "first_utc": h1[0]["time_utc"],
                "last_utc": h1[-1]["time_utc"], "time_column_basis": "true_utc",
                "timeframe_minutes": 60,
            },
        }
    }
    manifest = {
        "schema": "gtos.p1-upstream-source-packet.v2", "status": "FROZEN",
        "packet_payload_root_sha256": payload_root,
        "packet_directory_name": packet.name, "tested_source_commit": SOURCE_COMMIT,
        "source_root": source_root.as_posix(), "source_manifests": [],
        "commissioned_source_payload_count": 0,
        "repo_authorities": [copy.deepcopy(trusted_descriptor)],
        "packet_tooling": [copy.deepcopy(adapter_descriptor)],
        "immutable_evidence_authorities": {}, "series": series,
        "payload_files": payload_files,
        "timebase_authority": {
            "time_column_basis": "true_utc", "broker_clock_rule": "new_york_plus_7",
            "conversion_function": "src.utils.broker_clock.broker_epoch_to_utc",
            "conversion_code_sha256": "f" * 64,
        },
        "asof_contract": {
            "m15_bar_close_minutes": 15, "h1_bar_close_minutes": 60,
            "close_tolerance_seconds": 0, "m15_lookback": 52,
            "h1_lookback": 13, "postdecision_reads_allowed": False,
        },
        "generator": {
            "path": "trusted.txt", "sha256": trusted_sha,
            "market_state_path": "trusted.txt", "market_state_sha256": trusted_sha,
            "h1_aggregation_reference_path": "trusted.txt",
            "h1_aggregation_reference_sha256": trusted_sha,
            "transitive_authority": [copy.deepcopy(trusted_descriptor)],
        },
        "route_identity": {
            "candidate": "cq_current_breaker_re_entry_inverted_5d_stop_0p25d",
            "candidate_family": "CANDIDATE_BOOK_V1_V27",
            "origin_family": "current_breaker_re_entry",
            "transform_id": "cq_current_breaker_inverted_target_5d_stop_0p25d_v1",
            "identity_fields": ["candidate_id", "symbol", "side", "decision_time_utc"],
            "denominator_rows": 2,
            "windows": {"january": ["2026-01-01", "2026-01-30"]},
            "disposition": "ADMIT_UNCHANGED_NOT_ACTIVATION",
            "family_member_record_canonical_sha256": subject.FIXED_BREAKER_MEMBER_CANONICAL_SHA256,
            "b0_breaker_route_binding": dict(subject.B0_BREAKER_ROUTE_BINDING),
        },
        "coverage": coverage, "external_packet_immutable": True,
        "execution_authority": False, "activation_authority": False,
        "result_bearing_science_executed": False,
        "result_use_status": subject.RESULT_USE_STATUS,
    }
    manifest_sha = _write_manifest(packet, manifest)

    def authority_git_reader(commit: str, path: str) -> bytes:
        if commit == SOURCE_COMMIT and path == adapter_relative:
            return fixture_adapter.read_bytes()
        return subject._git_show_bytes(commit, path)

    return {
        "packet": packet, "manifest": manifest, "manifest_sha": manifest_sha,
        "payload_root": payload_root, "expectations": expectations,
        "source_loader": lambda: {"XAUUSD": copy.deepcopy(m15)},
        "domain_loader": lambda: copy.deepcopy(domain),
        "authority_git_reader": authority_git_reader,
    }


def _rebind_payload(fixture: dict[str, Any]) -> None:
    packet = fixture["packet"]
    manifest = fixture["manifest"]
    descriptors = []
    for row in manifest["payload_files"]:
        path = packet / row["path"]
        descriptors.append(_descriptor(path, relative_to=packet))
    descriptors.sort(key=lambda row: str(row["path"]))
    root = subject.canonical_hash({
        "schema": "gtos.p1-upstream-packet-payload.v1", "files": descriptors,
    })
    manifest["payload_files"] = descriptors
    by_path = {row["path"]: row for row in descriptors}
    for timeframe in ("M15", "H1"):
        series_row = manifest["series"]["XAUUSD"][timeframe]
        payload_row = by_path[series_row["path"]]
        series_row.update({key: payload_row[key] for key in ("bytes", "sha256")})
    manifest["packet_payload_root_sha256"] = root
    manifest["packet_directory_name"] = f"p1-source-packet-sha256-{root}"
    destination = packet.parent / manifest["packet_directory_name"]
    packet.rename(destination)
    fixture["packet"] = destination
    fixture["payload_root"] = root
    fixture["manifest_sha"] = _write_manifest(destination, manifest)


def _verify_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    return subject.verify_packet(
        fixture["packet"], full_generator=False,
        expected_manifest_sha256=fixture["manifest_sha"],
        expected_payload_root_sha256=fixture["payload_root"],
        expected_tested_source_commit=SOURCE_COMMIT,
        _expectations=fixture["expectations"],
        _source_m15_loader=fixture["source_loader"],
        _domain_loader=fixture["domain_loader"],
        _authority_git_reader=fixture["authority_git_reader"],
    )


def _gzip_rows(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def test_public_v2_fixture_reaches_structural_acceptance(tmp_path: Path) -> None:
    result = _verify_fixture(_fixture(tmp_path))

    assert result["status"] == "STRUCTURAL_ONLY_NOT_TERMINAL"
    assert result["identity_rows"] == 2
    assert result["state_rows"] == 1
    assert result["postdecision_reads"] == 0


@pytest.mark.parametrize(
    ("anchor", "reason"),
    [("manifest", "packet_manifest_sha256_mismatch"), ("root", "manifest_expected_payload_root_mismatch")],
)
def test_public_v2_refuses_manifest_or_root_drift(
    tmp_path: Path, anchor: str, reason: str
) -> None:
    fixture = _fixture(tmp_path)
    arguments = {
        "expected_manifest_sha256": fixture["manifest_sha"],
        "expected_payload_root_sha256": fixture["payload_root"],
    }
    arguments[f"expected_{anchor}_sha256" if anchor == "manifest" else "expected_payload_root_sha256"] = "0" * 64
    with pytest.raises(subject.VerificationError, match=reason):
        subject.verify_packet(
            fixture["packet"], full_generator=False,
            expected_tested_source_commit=SOURCE_COMMIT,
            _expectations=fixture["expectations"],
            _source_m15_loader=fixture["source_loader"],
            _domain_loader=fixture["domain_loader"],
            _authority_git_reader=fixture["authority_git_reader"],
            **arguments,
        )


@pytest.mark.parametrize(
    ("path", "reason"),
    [("/absolute/payload", "absolute_payload_path"), ("../traversal", "payload_path_traversal")],
)
def test_public_v2_refuses_absolute_and_traversal_paths(
    tmp_path: Path, path: str, reason: str
) -> None:
    fixture = _fixture(tmp_path)
    fixture["manifest"]["payload_files"][0]["path"] = path
    fixture["manifest_sha"] = _write_manifest(fixture["packet"], fixture["manifest"])

    with pytest.raises(subject.VerificationError, match=reason):
        _verify_fixture(fixture)


def test_public_v2_refuses_symlink_duplicate_descriptor_and_extra_file(tmp_path: Path) -> None:
    symlink_fixture = _fixture(tmp_path / "symlink")
    target = symlink_fixture["packet"] / "SOURCE_COVERAGE.json"
    outside = tmp_path / "outside"
    outside.write_bytes(b"outside")
    target.unlink()
    target.symlink_to(outside)
    with pytest.raises(subject.VerificationError, match="packet_symlink_refused"):
        _verify_fixture(symlink_fixture)

    duplicate_fixture = _fixture(tmp_path / "duplicate")
    duplicate_fixture["manifest"]["payload_files"][-1] = copy.deepcopy(
        duplicate_fixture["manifest"]["payload_files"][0]
    )
    duplicate_fixture["manifest_sha"] = _write_manifest(
        duplicate_fixture["packet"], duplicate_fixture["manifest"]
    )
    with pytest.raises(subject.VerificationError, match="duplicate_payload_descriptor"):
        _verify_fixture(duplicate_fixture)

    extra_fixture = _fixture(tmp_path / "extra")
    (extra_fixture["packet"] / "extra.txt").write_bytes(b"extra")
    with pytest.raises(subject.VerificationError, match="packet_file_inventory_mismatch"):
        _verify_fixture(extra_fixture)


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda row: row.__setitem__("unknown", 1), "series_schema_invalid"),
        (lambda row: row.__setitem__("open", float("inf")), "nonfinite_json_constant"),
        (lambda row: row.__setitem__("high", 0.0), "series_ohlc_geometry_invalid"),
    ],
)
def test_public_v2_refuses_malformed_series_rows(
    tmp_path: Path, mutation: Callable[[dict[str, Any]], None], reason: str
) -> None:
    fixture = _fixture(tmp_path)
    path = fixture["packet"] / "series/XAUUSD.m15.jsonl.gz"
    rows = _gzip_rows(path)
    mutation(rows[0])
    _write_gzip(path, rows)
    _rebind_payload(fixture)

    with pytest.raises(subject.VerificationError, match=reason):
        _verify_fixture(fixture)


def test_public_v2_refuses_true_outcome_flag_and_boolean_multiplicity(tmp_path: Path) -> None:
    state_fixture = _fixture(tmp_path / "state")
    state_path = state_fixture["packet"] / "states/predecision_market_state.jsonl.gz"
    states = _gzip_rows(state_path)
    states[0]["uses_outcome_fields"] = True
    _write_gzip(state_path, states)
    _rebind_payload(state_fixture)
    with pytest.raises(subject.VerificationError, match="state_outcome_flag_invalid"):
        _verify_fixture(state_fixture)

    identity_fixture = _fixture(tmp_path / "identity")
    identity_path = identity_fixture["packet"] / "identity_to_slice.jsonl.gz"
    identities = _gzip_rows(identity_path)
    identities[0]["generator_match_count"] = True
    _write_gzip(identity_path, identities)
    _rebind_payload(identity_fixture)
    with pytest.raises(subject.VerificationError, match="generator_multiplicity_type_invalid"):
        _verify_fixture(identity_fixture)


def test_public_v2_refuses_top_level_mismatch_and_changed_transitive_hash(tmp_path: Path) -> None:
    top_fixture = _fixture(tmp_path / "top")
    top_fixture["manifest"]["unexpected"] = True
    top_fixture["manifest_sha"] = _write_manifest(top_fixture["packet"], top_fixture["manifest"])
    with pytest.raises(subject.VerificationError, match="manifest_schema_invalid"):
        _verify_fixture(top_fixture)

    transitive_fixture = _fixture(tmp_path / "transitive")
    transitive_fixture["manifest"]["generator"]["transitive_authority"][0]["sha256"] = "0" * 64
    transitive_fixture["manifest_sha"] = _write_manifest(
        transitive_fixture["packet"], transitive_fixture["manifest"]
    )
    with pytest.raises(subject.VerificationError, match="transitive_repo_binding_mismatch"):
        _verify_fixture(transitive_fixture)


def test_public_v2_refuses_stale_second_identity_slice(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    path = fixture["packet"] / "identity_to_slice.jsonl.gz"
    identities = _gzip_rows(path)
    identities[1]["m15_slice"] = [1, 52]
    material = dict(identities[1])
    material.pop("identity_slice_sha256")
    identities[1]["identity_slice_sha256"] = subject.canonical_hash(material)
    _write_gzip(path, identities)
    _rebind_payload(fixture)

    with pytest.raises(subject.VerificationError, match="identity_slice_index_mismatch"):
        _verify_fixture(fixture)


def _u4_u11_inputs() -> dict[str, Any]:
    hn_commit = subject.EXPECTED_EVIDENCE_LINEAGE["hn_evidence_closeout"][0]
    u4 = subject.strict_json_loads(subject._git_show_bytes(
        hn_commit,
        "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_INERT_PROFILE_SYMBOL_SNAPSHOT.json",
    ), label="test_u4")
    u11 = subject.strict_json_loads(subject._git_show_bytes(
        hn_commit,
        "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_INERT_ROUTE_PARAMETER_BUNDLE.json",
    ), label="test_u11")
    adapter_path = (
        Path(subject.REPO_ROOT)
        / "docs/audits/fable5-vision-audit-20260725/phase20/receipts/wave20_complete_path_shadow.py"
    )
    adapter = adapter_path.read_bytes()
    binding = {
        "path": adapter_path.relative_to(subject.REPO_ROOT).as_posix(),
        "bytes": len(adapter), "sha256": hashlib.sha256(adapter).hexdigest(),
    }
    b0 = subject._git_show_bytes(
        subject.B0_BREAKER_ROUTE_BINDING["commit"],
        subject.B0_BREAKER_ROUTE_BINDING["path"],
    )
    return {"u4": u4, "u11": u11, "adapter_bytes": adapter, "adapter_binding": binding, "b0_bytes": b0}


def test_compact_u4_u11_known_good_binding() -> None:
    result = subject._validate_u4_u11_documents(**_u4_u11_inputs())

    assert result["u5_status"] == "NOT_EVALUABLE_OWNER_INPUT_REQUIRED"
    assert result["family_member_record_canonical_sha256"] == (
        "0de66ebe5b67e7b3352d98624acb50c69ab116b1c46d58c422b887e5583a650f"
    )
    assert result["runtime_reference"]["import_policy"] == "REFERENCE_ONLY_NEVER_IMPORT"


@pytest.mark.parametrize(
    "field", ("research_volume_selected", "owner_risk_or_allocation_invented")
)
def test_compact_u4_u11_refuses_u5_selected_risk_or_volume(field: str) -> None:
    selected = _u4_u11_inputs()
    selected["u4"]["u5_volume_owner_risk"][field] = True
    with pytest.raises(subject.VerificationError, match="u5_owner_input_boundary_invalid"):
        subject._validate_u4_u11_documents(**selected)


def test_compact_u4_u11_refuses_redacted_account_economic_role() -> None:
    economic = _u4_u11_inputs()
    economic["u4"]["profiles"]["redacted_account"]["role"] = "ECONOMIC_AUTHORITY"
    with pytest.raises(subject.VerificationError, match="u4_profile_role_or_domain_invalid:redacted_account"):
        subject._validate_u4_u11_documents(**economic)


def test_compact_u4_u11_refuses_missing_callable_wrong_adapter_blob_and_stale_b0() -> None:
    missing = _u4_u11_inputs()
    missing["adapter_bytes"] = missing["adapter_bytes"].replace(
        b"source_bound_fill_projection", b"removed_bound_fill_projection", 1
    )
    missing["adapter_binding"] = {
        **missing["adapter_binding"], "bytes": len(missing["adapter_bytes"]),
        "sha256": hashlib.sha256(missing["adapter_bytes"]).hexdigest(),
    }
    with pytest.raises(subject.VerificationError, match="u11_adapter_callable_set_incomplete"):
        subject._validate_u4_u11_documents(**missing)

    wrong_blob = _u4_u11_inputs()
    wrong_blob["adapter_bytes"] += b"\n"
    with pytest.raises(subject.VerificationError, match="u11_adapter_blob_mismatch"):
        subject._validate_u4_u11_documents(**wrong_blob)

    stale_b0 = _u4_u11_inputs()
    stale_b0["b0_bytes"] += b" "
    with pytest.raises(subject.VerificationError, match="b0_binding_bytes_mismatch"):
        subject._validate_u4_u11_documents(**stale_b0)


def test_strict_json_rejects_duplicate_keys_and_nonfinite_constants() -> None:
    with pytest.raises(subject.VerificationError, match="duplicate_json_key"):
        subject.strict_json_loads('{"a":1,"a":2}', label="duplicate")
    for token in ("NaN", "Infinity", "-Infinity"):
        with pytest.raises(subject.VerificationError, match="nonfinite_json_constant"):
            subject.strict_json_loads('{"a":' + token + "}", label="nonfinite")


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        ("/absolute/payload", "absolute_payload_path"),
        ("../escape", "payload_path_traversal"),
        ("series/../escape", "payload_path_traversal"),
        ("series//alias", "payload_path_not_normalized"),
        ("series\\alias", "payload_path_not_normalized"),
    ],
)
def test_payload_paths_are_unique_normalized_relative(path: str, reason: str) -> None:
    with pytest.raises(subject.VerificationError, match=reason):
        subject.normalized_relative_path(path, label="payload")


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ({"unexpected": 1}, "series_schema_invalid"),
        ({"open": "100"}, "series_numeric_type_invalid"),
        ({"open": float("inf")}, "series_numeric_nonfinite"),
        ({"high": 98.0}, "series_ohlc_geometry_invalid"),
        ({"low": 103.0}, "series_ohlc_geometry_invalid"),
        ({"volume": -1.0}, "series_volume_negative"),
        ({"time": "2026-01-02T00:15:00+00:00"}, "series_time_duplicate_mismatch"),
        ({"time_utc": "2026-01-02T00:00:01+00:00", "time": "2026-01-02T00:00:01+00:00"}, "series_grid_invalid"),
        ({"symbol": "GOLD"}, "series_symbol_mismatch"),
    ],
)
def test_series_schema_and_market_geometry_fail_closed(
    mutation: dict[str, object], reason: str
) -> None:
    row = _bar()
    row.update(mutation)
    with pytest.raises(subject.VerificationError, match=reason):
        subject.validate_series_row(row, symbol="XAUUSD", minutes=15, label="row")


def test_state_and_identity_schemas_require_false_outcome_flags() -> None:
    state = {
        "state_id": "state_" + "a" * 24,
        "symbol": "XAUUSD",
        "decision_time_utc": "2026-01-02T00:15:00+00:00",
        "m15_slice": {
            "m15_start": 0,
            "m15_stop": 51,
            "m15_count": 51,
            "first_open_utc": "2026-01-01T11:30:00+00:00",
            "last_open_utc": "2026-01-02T00:00:00+00:00",
            "last_close_utc": "2026-01-02T00:15:00+00:00",
        },
        "h1_slice": {
            "h1_start": 0,
            "h1_stop": 168,
            "h1_count": 168,
            "first_open_utc": "2025-12-26T00:00:00+00:00",
            "last_open_utc": "2026-01-01T23:00:00+00:00",
            "last_close_utc": "2026-01-02T00:00:00+00:00",
        },
        "m15_atr_14": 1.0,
        "h1_breaker_blocks": [],
        "h1_breaker_blocks_sha256": subject.canonical_hash([]),
        "uses_outcome_fields": True,
        "state_sha256": "0" * 64,
    }
    with pytest.raises(subject.VerificationError, match="state_outcome_flag_invalid"):
        subject.validate_state_schema(state, label="state")

    identity = {
        "identity": {
            "candidate_id": "candidate",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": "2026-01-02T00:15:00+00:00",
        },
        "window": "january",
        "state_id": "state_" + "a" * 24,
        "symbol": "XAUUSD",
        "decision_time_utc": "2026-01-02T00:15:00+00:00",
        "kill_zone": "ny",
        "origin_family": "current_breaker_re_entry",
        "framework": "breaker_re_entry",
        "route_family": "current_breaker_re_entry",
        "m15_series_path": "series/XAUUSD.m15.jsonl.gz",
        "h1_series_path": "series/XAUUSD.h1.jsonl.gz",
        "m15_slice": [0, 51],
        "h1_slice": [0, 168],
        "generator_match_count": True,
        "uses_outcome_fields": False,
        "identity_slice_sha256": "0" * 64,
    }
    with pytest.raises(subject.VerificationError, match="generator_multiplicity_type_invalid"):
        subject.validate_identity_schema(identity, label="identity")
    identity["generator_match_count"] = 1
    identity["uses_outcome_fields"] = True
    with pytest.raises(subject.VerificationError, match="identity_outcome_flag_invalid"):
        subject.validate_identity_schema(identity, label="identity")


def test_closed_slice_rejects_the_two_second_future_boundary() -> None:
    decision = datetime(2026, 1, 2, 0, 15, tzinfo=UTC)
    for seconds in (1, 2):
        with pytest.raises(subject.VerificationError, match="postdecision_or_empty_slice"):
            subject.independent_closed_slice_from_closes(
                [decision + timedelta(seconds=seconds)], decision, 51
            )


def test_manifest_trust_anchor_and_inventory_reject_drift(tmp_path: Path) -> None:
    packet = tmp_path / "packet"
    packet.mkdir()
    manifest = packet / "PACKET_MANIFEST.json"
    manifest.write_text(json.dumps({"schema": "attacker"}), encoding="utf-8")
    with pytest.raises(subject.VerificationError, match="packet_manifest_sha256_mismatch"):
        subject.verify_packet(
            packet,
            full_generator=False,
            expected_manifest_sha256="0" * 64,
            expected_payload_root_sha256="1" * 64,
            expected_tested_source_commit="2" * 40,
        )


def test_symlink_and_extra_inventory_are_refused(tmp_path: Path) -> None:
    root = tmp_path / "packet"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.write_bytes(b"outside")
    (root / "payload").symlink_to(outside)
    with pytest.raises(subject.VerificationError, match="packet_symlink_refused"):
        subject.packet_inventory(root)
    (root / "payload").unlink()
    (root / "extra").write_bytes(b"extra")
    files, _ = subject.packet_inventory(root)
    with pytest.raises(subject.VerificationError, match="packet_file_inventory_mismatch"):
        subject.require_exact_packet_inventory(files, {"PACKET_MANIFEST.json"})


def test_independent_atr_and_breaker_projection_known_answer() -> None:
    rows = []
    for i in range(40):
        price = 100.0 + i * 0.2
        rows.append(
            _bar(
                time=f"2026-01-02T{i // 4:02d}:{(i % 4) * 15:02d}:00+00:00",
                time_utc=f"2026-01-02T{i // 4:02d}:{(i % 4) * 15:02d}:00+00:00",
                open=price,
                high=price + 1.0,
                low=price - 1.0,
                close=price + 0.5,
            )
        )
    assert subject.independent_atr(rows, period=14) > 0
    assert isinstance(subject.independent_breaker_projection(rows, min_bars=2, dead_zone_divisor=8), list)


def test_runtime_audit_policy_refuses_live_network_process_and_writes() -> None:
    assert subject.runtime_audit_refusal("socket.connect", (object(),)) == (
        "runtime_network_forbidden:socket.connect"
    )
    assert subject.runtime_audit_refusal("subprocess.Popen", ("uname",)) == (
        "runtime_subprocess_or_exec_forbidden:subprocess.Popen"
    )
    for event in ("os.system", "os.popen", "os.execv", "os.spawnv", "pty.spawn"):
        assert subject.runtime_audit_refusal(event, ()) == (
            f"runtime_subprocess_or_exec_forbidden:{event}"
        )
    assert subject.runtime_audit_refusal("import", ("MetaTrader5",)) == (
        "runtime_live_import_forbidden:MetaTrader5"
    )
    assert subject.runtime_audit_refusal("open", ("/tmp/out", "w", 0)) == (
        "runtime_write_forbidden:open"
    )
    for event in ("os.remove", "os.rename", "os.mkdir", "os.symlink", "os.chmod"):
        assert subject.runtime_audit_refusal(event, ()) == (
            f"runtime_filesystem_or_environment_mutation_forbidden:{event}"
        )
    assert subject.runtime_audit_refusal("open", ("read-only", "r", 0)) is None


@pytest.mark.parametrize(
    ("operation", "reason"),
    [
        ("open(target, 'w')", "runtime_write_forbidden:open"),
        ("socket.socket()", "runtime_network_forbidden:socket.__new__"),
        ("subprocess.run(['true'], check=True)", "runtime_subprocess_or_exec_forbidden:subprocess.Popen"),
    ],
)
def test_installed_runtime_audit_hook_refuses_in_child_interpreter(
    tmp_path: Path, operation: str, reason: str
) -> None:
    target = (tmp_path / "blocked-write").as_posix()
    code = f"""
import socket
import subprocess
from src.research_infra.p1_upstream_packet_verifier import install_runtime_audit_guard
target = {target!r}
install_runtime_audit_guard()
try:
    {operation}
except Exception as exc:
    print(str(exc))
    raise SystemExit(0)
raise SystemExit(7)
"""
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=subject.REPO_ROOT,
        check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    assert completed.returncode == 0, completed.stderr
    assert reason in completed.stdout
    assert not (tmp_path / "blocked-write").exists()


def test_independent_canonical_h1_bytes_are_stable() -> None:
    rows = [_bar()]
    assert subject.canonical_jsonl_bytes(rows) == subject.canonical(rows[0]) + b"\n"
    assert subject.deterministic_jsonl_gzip_bytes(rows) == (
        subject.deterministic_jsonl_gzip_bytes(rows)
    )

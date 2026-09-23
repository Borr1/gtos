from __future__ import annotations

import csv
import importlib
import json
from pathlib import Path

import pytest


def _writer():
    return importlib.import_module("src.research_infra.replay_acceleration_slice")


def _verifier():
    return importlib.import_module(
        "src.research_infra.replay_acceleration_slice_verifier"
    )


def _write_csv(path: Path, *, day: str, minute: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("time", "open", "high", "low", "close", "volume"))
        writer.writerow(
            (
                f"{day} 00:{minute:02d}:00",
                "1.0",
                "2.0",
                "0.5",
                "1.5",
                "10",
            )
        )


def _source_rows(
    root: Path,
    *,
    symbols: tuple[str, ...] = ("AAA", "BBB"),
    days: tuple[str, ...] = ("2026-01-01", "2026-01-02"),
) -> tuple[Path, dict[tuple[str, str], Path]]:
    writer = _writer()
    paths: dict[tuple[str, str], Path] = {}
    rows: list[dict[str, object]] = []
    for symbol_index, symbol in enumerate(symbols):
        for timeframe in ("D1", "H4", "M15", "M1"):
            path = root / "sources" / f"{symbol}_{timeframe}.csv"
            _write_csv(path, day="2026-01-02", minute=symbol_index)
            paths[(symbol, timeframe)] = path
        for timeframe in ("D1", "H4", "H1", "M15"):
            physical = "M15" if timeframe == "H1" else timeframe
            source_selection = {
                    "row_type": "source_selection",
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "source_path": str(paths[(symbol, physical)]),
                    "source_family": "fixture",
                    "source_role": (
                        "source_bound_derived_h1_from_m15"
                        if timeframe == "H1"
                        else "owner_authorized_research_hydration"
                    ),
                    "status": (
                        "selected_source_bound_derived_h1_from_m15"
                        if timeframe == "H1"
                        else "selected_source_meets_floor"
                    ),
                    "rows": 1,
                    "sha256": writer.file_sha256(paths[(symbol, physical)]),
                }
            if timeframe != "H1":
                source_selection["requested_range_covered"] = True
            rows.append(source_selection)
        for day in days:
            complete = day == "2026-01-02"
            rows.append(
                {
                    "row_type": "m1_symbol_day_source",
                    "symbol": symbol,
                    "timeframe": "M1",
                    "trading_day": day,
                    "source_path": str(paths[(symbol, "M1")]),
                    "source_family": "fixture",
                    "status": (
                        "selected_day_source_meets_absolute_floor"
                        if complete
                        else "ftmo_verified_no_session_day"
                    ),
                    "source_session_status": (
                        "ftmo_regular_session_reference"
                        if complete
                        else "ftmo_verified_no_session_day"
                    ),
                    "diagnostic_fallback_only": False,
                    "path_replay_allowed": complete,
                    "terminal_lifecycle_close_allowed": complete,
                    "source_overlap_consistent": True,
                    "source_gaps": [],
                    "rows": 1 if complete else 0,
                    "m15_day_rows": 1 if complete else 0,
                    "sha256": writer.file_sha256(paths[(symbol, "M1")]),
                    "source_day_authority_hash_sha256": writer.sha256_bytes(
                        f"{symbol}:{day}".encode("utf-8")
                    ),
                }
            )
        rows.append(
            {
                "row_type": "tick_symbol_source_gap",
                "symbol": symbol,
                "timeframe": "TICK",
                "status": "missing_ftmo_tick_source",
            }
        )
    ledger = root / "source.jsonl"
    with ledger.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
    return ledger, paths


def test_structural_selector_seals_earliest_complete_day(tmp_path: Path) -> None:
    api = _writer()
    ledger, _paths = _source_rows(tmp_path)
    output = tmp_path / "selection.json"

    receipt = api.create_selection_receipt(
        source_ledger=ledger,
        output_path=output,
        expected_symbols=("AAA", "BBB"),
        expected_source_plan_digest_sha256="a" * 64,
        month="2026-01",
    )

    assert receipt["selected_day"] == "2026-01-02"
    assert receipt["selection_rule"] == api.SELECTION_RULE
    assert receipt["scope"]["symbol_count"] == 2
    assert receipt["scope"]["physical_partition_count"] == 8
    assert receipt["scope"]["logical_partition_count"] == 10
    assert receipt["source_stat_identity_contract"] == {
        "content_identity_fields": [
            "device",
            "inode",
            "byte_count",
            "mtime_ns",
        ],
        "observational_noncausal_fields": ["ctime_ns"],
        "content_sha256_required": True,
        "race_detection": (
            "stable_content_identity_before_and_after_read_plus_exact_sha256"
        ),
    }
    assert output.read_bytes() == api.canonical_json_bytes(receipt) + b"\n"
    assert api.verify_selection_receipt(output)["selection_root_sha256"] == receipt[
        "selection_root_sha256"
    ]


def test_source_stat_projection_excludes_only_noncausal_ctime() -> None:
    api = _writer()
    baseline = {
        "device": 1,
        "inode": 2,
        "byte_count": 3,
        "mtime_ns": 4,
        "ctime_ns": 5,
    }
    ctime_only = {**baseline, "ctime_ns": 6}

    assert api._source_stat_stable_projection(baseline) == (
        api._source_stat_stable_projection(ctime_only)
    )
    for field in ("device", "inode", "byte_count", "mtime_ns"):
        changed = {**baseline, field: baseline[field] + 1}
        assert api._source_stat_stable_projection(baseline) != (
            api._source_stat_stable_projection(changed)
        )


def test_structural_selector_rejects_conflicting_duplicate(tmp_path: Path) -> None:
    api = _writer()
    ledger, _paths = _source_rows(tmp_path)
    rows = ledger.read_text(encoding="utf-8").splitlines()
    duplicate = json.loads(rows[-3])
    duplicate["rows"] = 99
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(duplicate, sort_keys=True) + "\n")

    with pytest.raises(api.SliceRejected, match="source_metadata_conflict"):
        api.create_selection_receipt(
            source_ledger=ledger,
            output_path=tmp_path / "selection.json",
            expected_symbols=("AAA", "BBB"),
            expected_source_plan_digest_sha256="a" * 64,
            month="2026-01",
        )


def test_materialized_bundle_is_exact_and_independently_verified(
    tmp_path: Path,
) -> None:
    api = _writer()
    verifier = _verifier()
    ledger, _paths = _source_rows(tmp_path)
    selection_path = tmp_path / "selection.json"
    selection = api.create_selection_receipt(
        source_ledger=ledger,
        output_path=selection_path,
        expected_symbols=("AAA", "BBB"),
        expected_source_plan_digest_sha256="a" * 64,
        month="2026-01",
    )

    cold = api.materialize_slice(
        selection_path=selection_path,
        workspace=tmp_path / "slice",
        run_label="cold",
        expected_mode="cold",
        run_attestations=True,
    )
    warm = api.materialize_slice(
        selection_path=selection_path,
        workspace=tmp_path / "slice",
        run_label="warm",
        expected_mode="warm",
        run_attestations=True,
    )
    cold_repeat = api.materialize_slice(
        selection_path=selection_path,
        workspace=tmp_path / "slice-repeat",
        run_label="cold-repeat",
        expected_mode="cold",
        run_attestations=True,
    )
    warm_repeat = api.materialize_slice(
        selection_path=selection_path,
        workspace=tmp_path / "slice",
        run_label="warm-repeat",
        expected_mode="warm",
        run_attestations=True,
    )

    assert cold["bundle_root_sha256"] == warm["bundle_root_sha256"]
    assert cold["cache_hits"] == {"hits": 0, "misses": 8}
    assert warm["cache_hits"] == {"hits": 8, "misses": 0}
    assert cold["cross_symbol_barrier"]["sealed"] is True
    assert cold["source_attestations"]["count"] == 4
    stage_wall = sum(
        row["wall_seconds"]
        for row in cold["measurements"]["stages"].values()
    )
    assert cold["measurements"]["end_to_end"]["wall_seconds"] >= stage_wall
    assert cold["measurements"]["end_to_end"]["peak_rss_bytes"] > 0
    verified = verifier.verify_bundle(
        bundle_dir=tmp_path / "slice" / "bundle",
        selection_path=selection_path,
    )
    assert verified["status"] == "VERIFIED"
    assert verified["counts"]["physical_partitions"] == 8
    assert verified["counts"]["logical_partitions"] == 10
    assert verified["bundle_root_sha256"] == cold["bundle_root_sha256"]

    verifier_path = tmp_path / "verifier.json"
    verifier_envelope = api.run_independent_verifier(
        bundle_dir=tmp_path / "slice" / "bundle",
        selection_path=selection_path,
        output_path=verifier_path,
    )
    injection_path = tmp_path / "injections.json"
    injections = api.run_failure_injections(
        bundle_dir=tmp_path / "slice" / "bundle",
        selection_path=selection_path,
        cases_root=tmp_path / "cases",
        output_path=injection_path,
    )
    result = api.finalize_result(
        selection_path=selection_path,
        cold_run_path=tmp_path / "slice" / "runs" / "cold.json",
        cold_repeat_run_path=(
            tmp_path / "slice-repeat" / "runs" / "cold-repeat.json"
        ),
        warm_run_path=tmp_path / "slice" / "runs" / "warm.json",
        warm_repeat_run_path=(
            tmp_path / "slice" / "runs" / "warm-repeat.json"
        ),
        verifier_paths=(verifier_path,),
        injection_path=injection_path,
        output_path=tmp_path / "result.json",
    )
    assert cold_repeat["bundle_root_sha256"] == cold["bundle_root_sha256"]
    assert warm_repeat["bundle_root_sha256"] == cold["bundle_root_sha256"]
    assert verifier_envelope["status"] == "VERIFIED"
    assert injections["case_count"] == 12
    assert injections["scratch_usage"]["allocated_bytes"] > 0
    assert result["status"] == "ACCEPTED"
    assert result["determinism"]["fresh_process_runs"] == 4
    assert "failure_cases" in result["combined_retained_scratch"]


@pytest.mark.parametrize("stale_identity", ("top_level", "partition"))
def test_integrated_source_rejects_stale_bundle_implementation_before_prewarm(
    tmp_path: Path,
    stale_identity: str,
) -> None:
    api = _writer()
    integrated = importlib.import_module(
        "src.research_infra.replay_acceleration_integrated_source"
    )
    symbols = tuple(f"S{index:02d}" for index in range(24))
    ledger, _paths = _source_rows(tmp_path, symbols=symbols)
    selection_path = tmp_path / "selection.json"
    selection = api.create_selection_receipt(
        source_ledger=ledger,
        output_path=selection_path,
        expected_symbols=symbols,
        expected_source_plan_digest_sha256="a" * 64,
        month="2026-01",
    )
    api.materialize_slice(
        selection_path=selection_path,
        workspace=tmp_path / "slice",
        run_label="cold",
        expected_mode="cold",
        run_attestations=False,
    )

    bundle_path = tmp_path / "slice" / "bundle" / "bundle.json"
    seal_path = tmp_path / "slice" / "bundle" / "SEALED"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    if stale_identity == "top_level":
        bundle["accepted_cache_implementation_root"] = "f" * 64
    else:
        for partition in bundle["physical_partitions"]:
            partition["binding"]["implementation_root"] = "f" * 64
    bundle = api._with_self_root(bundle, "bundle_root_sha256")
    bundle_path.chmod(0o644)
    seal_path.chmod(0o644)
    bundle_path.write_bytes(api.canonical_json_bytes(bundle) + b"\n")
    seal_path.write_text(
        bundle["bundle_root_sha256"] + "\n",
        encoding="ascii",
    )

    with pytest.raises(
        integrated.IntegratedSourceRejected,
        match="accepted_source_implementation_identity_stale",
    ):
        integrated.RealReplaySourceAccelerator.from_accepted_bundle(
            source_bundle_dir=tmp_path / "slice" / "bundle",
            selection_path=selection_path,
            typed_cache_root=tmp_path / "typed",
            expected_bundle_root=bundle["bundle_root_sha256"],
            expected_source_plan_digest=selection[
                "expected_source_plan_digest_sha256"
            ],
        )


def test_integrated_source_rejects_wrong_expected_bundle_root_before_prewarm(
    tmp_path: Path,
) -> None:
    api = _writer()
    integrated = importlib.import_module(
        "src.research_infra.replay_acceleration_integrated_source"
    )
    symbols = tuple(f"S{index:02d}" for index in range(24))
    ledger, _paths = _source_rows(tmp_path, symbols=symbols)
    selection_path = tmp_path / "selection.json"
    selection = api.create_selection_receipt(
        source_ledger=ledger,
        output_path=selection_path,
        expected_symbols=symbols,
        expected_source_plan_digest_sha256="a" * 64,
        month="2026-01",
    )
    api.materialize_slice(
        selection_path=selection_path,
        workspace=tmp_path / "slice",
        run_label="cold",
        expected_mode="cold",
        run_attestations=False,
    )

    with pytest.raises(
        integrated.IntegratedSourceRejected,
        match="accepted_source_bundle_root_mismatch",
    ):
        integrated.RealReplaySourceAccelerator.from_accepted_bundle(
            source_bundle_dir=tmp_path / "slice" / "bundle",
            selection_path=selection_path,
            typed_cache_root=tmp_path / "typed",
            expected_bundle_root="f" * 64,
            expected_source_plan_digest=selection[
                "expected_source_plan_digest_sha256"
            ],
        )


@pytest.mark.parametrize("alias_kind", ("selection_leaf", "bundle_parent"))
def test_integrated_source_rejects_source_authority_symlink_components(
    tmp_path: Path,
    alias_kind: str,
) -> None:
    api = _writer()
    integrated = importlib.import_module(
        "src.research_infra.replay_acceleration_integrated_source"
    )
    symbols = tuple(f"S{index:02d}" for index in range(24))
    ledger, _paths = _source_rows(tmp_path, symbols=symbols)
    selection_path = tmp_path / "selection.json"
    selection = api.create_selection_receipt(
        source_ledger=ledger,
        output_path=selection_path,
        expected_symbols=symbols,
        expected_source_plan_digest_sha256="a" * 64,
        month="2026-01",
    )
    materialization_root = tmp_path / "slice"
    result = api.materialize_slice(
        selection_path=selection_path,
        workspace=materialization_root,
        run_label="cold",
        expected_mode="cold",
        run_attestations=False,
    )
    bundle_dir = materialization_root / "bundle"
    if alias_kind == "selection_leaf":
        real_selection = tmp_path / "real-selection.json"
        selection_path.rename(real_selection)
        selection_path.symlink_to(real_selection)
    else:
        alias_parent = tmp_path / "slice-alias"
        alias_parent.symlink_to(materialization_root, target_is_directory=True)
        bundle_dir = alias_parent / "bundle"

    with pytest.raises(
        integrated.IntegratedSourceRejected,
        match="accepted_source_bundle_invalid",
    ):
        integrated.RealReplaySourceAccelerator.from_accepted_bundle(
            source_bundle_dir=bundle_dir,
            selection_path=selection_path,
            typed_cache_root=tmp_path / "typed",
            expected_bundle_root=result["bundle_root_sha256"],
            expected_source_plan_digest=selection[
                "expected_source_plan_digest_sha256"
            ],
        )


def test_independent_verifier_rejects_bitflip_and_reorder(tmp_path: Path) -> None:
    api = _writer()
    verifier = _verifier()
    ledger, _paths = _source_rows(tmp_path)
    selection_path = tmp_path / "selection.json"
    api.create_selection_receipt(
        source_ledger=ledger,
        output_path=selection_path,
        expected_symbols=("AAA", "BBB"),
        expected_source_plan_digest_sha256="a" * 64,
        month="2026-01",
    )
    api.materialize_slice(
        selection_path=selection_path,
        workspace=tmp_path / "slice",
        run_label="cold",
        expected_mode="cold",
        run_attestations=False,
    )

    bitflip = api.build_failure_case(
        bundle_dir=tmp_path / "slice" / "bundle",
        cases_root=tmp_path / "cases",
        case_name="bit_flip",
    )
    with pytest.raises(verifier.VerificationRejected, match="payload_identity_mismatch"):
        verifier.verify_case(case_dir=bitflip, selection_path=selection_path)

    reorder = api.build_failure_case(
        bundle_dir=tmp_path / "slice" / "bundle",
        cases_root=tmp_path / "cases",
        case_name="partition_reorder",
    )
    with pytest.raises(verifier.VerificationRejected, match="partition_order_mismatch"):
        verifier.verify_case(case_dir=reorder, selection_path=selection_path)


def test_all_required_failure_cases_have_stable_disposition(tmp_path: Path) -> None:
    api = _writer()
    verifier = _verifier()
    ledger, _paths = _source_rows(tmp_path)
    selection_path = tmp_path / "selection.json"
    api.create_selection_receipt(
        source_ledger=ledger,
        output_path=selection_path,
        expected_symbols=("AAA", "BBB"),
        expected_source_plan_digest_sha256="a" * 64,
        month="2026-01",
    )
    api.materialize_slice(
        selection_path=selection_path,
        workspace=tmp_path / "slice",
        run_label="cold",
        expected_mode="cold",
        run_attestations=False,
    )

    rejection_codes = {
        "bit_flip": "payload_identity_mismatch",
        "truncation": "payload_identity_mismatch",
        "append": "payload_identity_mismatch",
        "partition_reorder": "partition_order_mismatch",
        "manifest_mismatch": "manifest_schema_mismatch",
        "schema_mismatch": "manifest_schema_mismatch",
        "source_mismatch": "source_identity_mismatch",
        "config_mismatch": "config_identity_mismatch",
        "code_mismatch": "code_identity_mismatch",
        "stale_cache": "stale_cache_identity_mismatch",
        "interruption_before_seal": "bundle_unsealed",
    }
    for case_name, expected_code in rejection_codes.items():
        case = api.build_failure_case(
            bundle_dir=tmp_path / "slice" / "bundle",
            cases_root=tmp_path / "cases",
            case_name=case_name,
        )
        with pytest.raises(verifier.VerificationRejected, match=expected_code):
            verifier.verify_case(case_dir=case, selection_path=selection_path)

    after = api.build_failure_case(
        bundle_dir=tmp_path / "slice" / "bundle",
        cases_root=tmp_path / "cases",
        case_name="interruption_after_seal",
    )
    first = verifier.verify_case(case_dir=after, selection_path=selection_path)
    second = verifier.verify_case(case_dir=after, selection_path=selection_path)
    assert first["status"] == "VERIFIED"
    assert first["bundle_root_sha256"] == second["bundle_root_sha256"]


def test_verifier_has_no_writer_or_cache_import() -> None:
    verifier = _verifier()
    source = Path(verifier.__file__).read_text(encoding="utf-8")
    assert "replay_acceleration_slice import" not in source
    assert "replay_acceleration_source_batch import" not in source


def test_cli_command_receipt_preserves_module_invocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _writer()
    original = [
        "/usr/bin/python3",
        "-m",
        "src.research_infra.replay_acceleration_slice",
        "select",
    ]
    monkeypatch.setattr(api.sys, "orig_argv", original)

    assert api._executed_command_receipt(["select"]) == original


def test_capacity_guard_is_workload_bound_not_static_free_space_floor() -> None:
    api = _writer()
    projected_growth = 256 * 1024**2

    assert api.HARD_FLOOR_FREE_BYTES == 0
    assert api._projected_capacity_sufficient(
        free_bytes=2 * 1024**3,
        projected_growth_bytes=projected_growth,
    )
    assert not api._projected_capacity_sufficient(
        free_bytes=projected_growth - 1,
        projected_growth_bytes=projected_growth,
    )


def test_capacity_guard_ignores_unrelated_machine_wide_free_space_motion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _writer()
    machine_free = 2 * 1024**3
    monkeypatch.setattr(
        api.shutil,
        "disk_usage",
        lambda _path: type(
            "Usage", (), {"total": 10 * 1024**3, "used": 8 * 1024**3, "free": machine_free}
        )(),
    )

    result = api._enforce_capacity(
        workspace=tmp_path,
        baseline_free=machine_free + api.MAX_SCRATCH_BYTES + 1,
        baseline_allocated=0,
    )

    assert result == {"free_bytes": machine_free, "allocated_growth_bytes": 0}

from __future__ import annotations

import csv
import importlib
import json
import os
from pathlib import Path

import pytest


def _slice_api():
    return importlib.import_module("src.research_infra.replay_acceleration_slice")


def _normalized_api():
    return importlib.import_module(
        "src.research_infra.replay_acceleration_normalized_batch"
    )


def _verifier_api():
    return importlib.import_module(
        "src.research_infra.replay_acceleration_normalized_verifier"
    )


def _write_csv(path: Path, *, symbol_index: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("time", "open", "high", "low", "close", "volume"))
        for minute in (0, 15, 30, 45):
            writer.writerow(
                (
                    f"2026-01-02 00:{minute:02d}:00",
                    f"{1 + symbol_index}.0",
                    f"{2 + symbol_index}.0",
                    f"{0.5 + symbol_index}",
                    f"{1.5 + symbol_index}",
                    str(10 + minute),
                )
            )


def _source_bundle(tmp_path: Path) -> tuple[Path, Path]:
    slice_api = _slice_api()
    symbols = ("AAA", "BBB")
    rows: list[dict[str, object]] = []
    paths: dict[tuple[str, str], Path] = {}
    for symbol_index, symbol in enumerate(symbols):
        for timeframe in ("D1", "H4", "M15", "M1"):
            path = tmp_path / "sources" / f"{symbol}_{timeframe}.csv"
            _write_csv(path, symbol_index=symbol_index)
            paths[(symbol, timeframe)] = path
        for timeframe in ("D1", "H4", "H1", "M15"):
            physical = "M15" if timeframe == "H1" else timeframe
            row: dict[str, object] = {
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
                "rows": 4,
                "sha256": slice_api.file_sha256(paths[(symbol, physical)]),
            }
            if timeframe != "H1":
                row["requested_range_covered"] = True
            rows.append(row)
        rows.append(
            {
                "row_type": "m1_symbol_day_source",
                "symbol": symbol,
                "timeframe": "M1",
                "trading_day": "2026-01-02",
                "source_path": str(paths[(symbol, "M1")]),
                "source_family": "fixture",
                "status": "selected_day_source_meets_absolute_floor",
                "source_session_status": "ftmo_regular_session_reference",
                "diagnostic_fallback_only": False,
                "path_replay_allowed": True,
                "terminal_lifecycle_close_allowed": True,
                "source_overlap_consistent": True,
                "source_gaps": [],
                "rows": 4,
                "m15_day_rows": 4,
                "sha256": slice_api.file_sha256(paths[(symbol, "M1")]),
                "source_day_authority_hash_sha256": slice_api.sha256_bytes(
                    f"{symbol}:2026-01-02".encode()
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
    ledger = tmp_path / "source.jsonl"
    with ledger.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
    selection = tmp_path / "selection.json"
    slice_api.create_selection_receipt(
        source_ledger=ledger,
        output_path=selection,
        expected_symbols=symbols,
        expected_source_plan_digest_sha256="a" * 64,
        month="2026-01",
    )
    source_workspace = tmp_path / "source-slice"
    slice_api.materialize_slice(
        selection_path=selection,
        workspace=source_workspace,
        run_label="cold",
        expected_mode="cold",
        run_attestations=False,
    )
    return selection, source_workspace / "bundle"


def test_normalized_cold_warm_and_independent_equivalence(tmp_path: Path) -> None:
    api = _normalized_api()
    verifier = _verifier_api()
    selection, source_bundle = _source_bundle(tmp_path)

    cold = api.materialize_normalized_bundle(
        source_bundle_dir=source_bundle,
        selection_path=selection,
        workspace=tmp_path / "normalized",
        run_label="cold",
        expected_mode="cold",
    )
    warm = api.materialize_normalized_bundle(
        source_bundle_dir=source_bundle,
        selection_path=selection,
        workspace=tmp_path / "normalized",
        run_label="warm",
        expected_mode="warm",
    )
    cold_repeat = api.materialize_normalized_bundle(
        source_bundle_dir=source_bundle,
        selection_path=selection,
        workspace=tmp_path / "normalized-repeat",
        run_label="cold-repeat",
        expected_mode="cold",
    )
    warm_repeat = api.materialize_normalized_bundle(
        source_bundle_dir=source_bundle,
        selection_path=selection,
        workspace=tmp_path / "normalized",
        run_label="warm-repeat",
        expected_mode="warm",
    )

    assert cold["cache_hits"] == {"hits": 0, "misses": 10}
    assert warm["cache_hits"] == {"hits": 10, "misses": 0}
    assert cold_repeat["normalized_bundle_root_sha256"] == cold[
        "normalized_bundle_root_sha256"
    ]
    assert warm["normalized_bundle_root_sha256"] == cold[
        "normalized_bundle_root_sha256"
    ]
    assert warm_repeat["normalized_bundle_root_sha256"] == cold[
        "normalized_bundle_root_sha256"
    ]
    assert cold["cross_symbol_barrier"]["sealed"] is True
    assert cold["cross_symbol_barrier"]["logical_partition_count"] == 10

    receipt = verifier.verify_normalized_bundle(
        normalized_bundle_dir=tmp_path / "normalized" / "bundle",
        source_bundle_dir=source_bundle,
        selection_path=selection,
    )
    assert receipt["status"] == "VERIFIED"
    assert receipt["counts"] == {
        "symbols": 2,
        "logical_partitions": 10,
        "normalized_rows": 34,
    }
    assert receipt["writer_imported"] is False
    assert receipt["legacy_normalizer_imported"] is False

    verifier_path = tmp_path / "normalized-verifier.json"
    envelope = api.run_independent_normalized_verifier(
        normalized_bundle_dir=tmp_path / "normalized" / "bundle",
        source_bundle_dir=source_bundle,
        selection_path=selection,
        output_path=verifier_path,
    )
    injection_path = tmp_path / "normalized-injections.json"
    injections = api.run_normalized_failure_injections(
        normalized_bundle_dir=tmp_path / "normalized" / "bundle",
        source_bundle_dir=source_bundle,
        selection_path=selection,
        cases_root=tmp_path / "orchestrated-cases",
        output_path=injection_path,
    )
    result = api.finalize_normalized_result(
        cold_run_path=tmp_path / "normalized" / "runs" / "cold.json",
        cold_repeat_run_path=(
            tmp_path / "normalized-repeat" / "runs" / "cold-repeat.json"
        ),
        warm_run_path=tmp_path / "normalized" / "runs" / "warm.json",
        warm_repeat_run_path=(
            tmp_path / "normalized" / "runs" / "warm-repeat.json"
        ),
        verifier_paths=(verifier_path,),
        injection_path=injection_path,
        output_path=tmp_path / "normalized-result.json",
    )
    assert envelope["status"] == "VERIFIED"
    assert injections["case_count"] == 13
    assert result["status"] == "ACCEPTED"
    assert result["determinism"]["fresh_process_runs"] == 4


def test_normalized_verifier_rejects_all_identity_and_byte_failures(
    tmp_path: Path,
) -> None:
    api = _normalized_api()
    verifier = _verifier_api()
    selection, source_bundle = _source_bundle(tmp_path)
    api.materialize_normalized_bundle(
        source_bundle_dir=source_bundle,
        selection_path=selection,
        workspace=tmp_path / "normalized",
        run_label="cold",
        expected_mode="cold",
    )
    expected = {
        "bit_flip": "normalized_payload_identity_mismatch",
        "truncation": "normalized_payload_not_canonical",
        "append": "normalized_payload_identity_mismatch",
        "partition_reorder": "normalized_partition_order_mismatch",
        "manifest_mismatch": "normalized_manifest_schema_mismatch",
        "schema_mismatch": "normalized_manifest_schema_mismatch",
        "source_mismatch": "normalized_source_identity_mismatch",
        "config_mismatch": "normalized_config_identity_mismatch",
        "code_mismatch": "normalized_code_identity_mismatch",
        "stale_cache": "normalized_cache_identity_mismatch",
        "cross_symbol_barrier": "normalized_cross_symbol_barrier_mismatch",
        "interruption_before_seal": "normalized_bundle_unsealed",
    }
    for case_name, code in expected.items():
        case_dir = api.build_normalized_failure_case(
            normalized_bundle_dir=tmp_path / "normalized" / "bundle",
            cases_root=tmp_path / "cases",
            case_name=case_name,
        )
        with pytest.raises(verifier.NormalizedVerificationRejected, match=code):
            verifier.verify_normalized_case(
                case_dir=case_dir,
                source_bundle_dir=source_bundle,
                selection_path=selection,
            )

    after = api.build_normalized_failure_case(
        normalized_bundle_dir=tmp_path / "normalized" / "bundle",
        cases_root=tmp_path / "cases",
        case_name="interruption_after_seal",
    )
    first = verifier.verify_normalized_case(
        case_dir=after,
        source_bundle_dir=source_bundle,
        selection_path=selection,
    )
    second = verifier.verify_normalized_case(
        case_dir=after,
        source_bundle_dir=source_bundle,
        selection_path=selection,
    )
    assert first["status"] == "VERIFIED"
    assert first["normalized_bundle_root_sha256"] == second[
        "normalized_bundle_root_sha256"
    ]


def test_normalized_verifier_has_no_writer_or_legacy_import() -> None:
    verifier = _verifier_api()
    source = Path(verifier.__file__).read_text(encoding="utf-8")
    assert "replay_acceleration_normalized_batch import" not in source
    assert "v4_timewarp_simulated_live_research_loop import" not in source
    assert "replay_acceleration_slice import" not in source


def test_warm_cache_rejects_resealed_manifest_schema_extension(
    tmp_path: Path,
) -> None:
    api = _normalized_api()
    selection, source_bundle = _source_bundle(tmp_path)
    workspace = tmp_path / "normalized"
    api.materialize_normalized_bundle(
        source_bundle_dir=source_bundle,
        selection_path=selection,
        workspace=workspace,
        run_label="cold",
        expected_mode="cold",
    )
    bundle = json.loads((workspace / "bundle" / "bundle.json").read_bytes())
    manifest_path = workspace / "bundle" / bundle["logical_partitions"][0][
        "manifest_path"
    ]
    manifest = json.loads(manifest_path.read_bytes())
    manifest["undeclared"] = True
    manifest = api._with_self_root(manifest, "manifest_root_sha256")
    os.chmod(manifest_path, 0o644)
    api._write_canonical_json(manifest_path, manifest, mode=0o444)

    with pytest.raises(api.NormalizedRejected, match="normalized_manifest_schema_mismatch"):
        api.materialize_normalized_bundle(
            source_bundle_dir=source_bundle,
            selection_path=selection,
            workspace=workspace,
            run_label="warm",
            expected_mode="warm",
        )

from __future__ import annotations

import ast
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.research_infra import v4_timewarp_simulated_live_research_loop as legacy


def _write_source(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("time", "open", "high", "low", "close", "volume"))
        writer.writerow(("2026-01-01T00:00:00+00:00", "1.25", "2.5", "1", "2", "3"))
        writer.writerow(("2026-01-02T00:00:00+00:00", "2", "3", "1.5", "2.75", "4"))
        writer.writerow(("2026-01-03T00:00:00+00:00", "3", "4", "2", "3.5", "5"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_typed_partition_cache_is_exact_cold_warm_and_independently_verifiable(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_integrated_source import (
        TypedNormalizedPartitionCache,
    )
    from src.research_infra.replay_acceleration_integrated_source_verifier import (
        verify_cache,
    )

    source = tmp_path / "EURUSD_M1.csv"
    _write_source(source)
    expected = legacy.load_csv_rows(source, symbol="EURUSD")
    cache = TypedNormalizedPartitionCache(
        tmp_path / "cache",
        source_bundle_root="a" * 64,
        config_projection_root="b" * 64,
    )

    cold = cache.load_or_build_partition(
        source_path=source,
        symbol="EURUSD",
        physical_timeframe="M1",
        source_payload_root=_sha256(source),
        open_text=lambda: source.open("r", newline="", encoding="utf-8"),
    )
    warm = cache.load_or_build_partition(
        source_path=source,
        symbol="EURUSD",
        physical_timeframe="M1",
        source_payload_root=_sha256(source),
        open_text=lambda: pytest.fail("warm cache unexpectedly reopened source"),
    )

    assert cold.rows == expected
    assert warm.rows == expected
    assert cold.cache_hit is False
    assert warm.cache_hit is True
    assert cold.partition_root_sha256 == warm.partition_root_sha256
    assert cache.metrics()["cold_partition_count"] == 1
    assert cache.metrics()["warm_partition_count"] == 1
    report = verify_cache(
        cache_root=tmp_path / "cache",
        expected_source_bundle_root="a" * 64,
        expected_config_projection_root="b" * 64,
    )
    assert report["valid"] is True
    assert report["partition_count"] == 1


def test_typed_partition_cache_preserves_case_sensitive_symbol_identity(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_integrated_source import (
        TypedNormalizedPartitionCache,
    )

    source = tmp_path / "UKOIL_cash_D1.csv"
    _write_source(source)
    expected = legacy.load_csv_rows(source, symbol="UKOIL_cash")
    cache = TypedNormalizedPartitionCache(
        tmp_path / "cache",
        source_bundle_root="1" * 64,
        config_projection_root="2" * 64,
    )
    result = cache.load_or_build_partition(
        source_path=source,
        symbol="UKOIL_cash",
        physical_timeframe="D1",
        source_payload_root=_sha256(source),
        open_text=lambda: source.open("r", newline="", encoding="utf-8"),
    )
    assert result.rows == expected
    assert {row["symbol"] for row in result.rows} == {"UKOIL_cash"}


def test_typed_partition_cache_rejects_corruption_and_wrong_identity(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_integrated_source import (
        IntegratedSourceRejected,
        TypedNormalizedPartitionCache,
    )

    source = tmp_path / "GBPUSD_M15.csv"
    _write_source(source)
    cache = TypedNormalizedPartitionCache(
        tmp_path / "cache",
        source_bundle_root="c" * 64,
        config_projection_root="d" * 64,
    )
    sealed = cache.load_or_build_partition(
        source_path=source,
        symbol="GBPUSD",
        physical_timeframe="M15",
        source_payload_root=_sha256(source),
        open_text=lambda: source.open("r", newline="", encoding="utf-8"),
    )
    payload = sealed.cache_entry_dir / "rows.bin"
    raw = bytearray(payload.read_bytes())
    raw[-1] ^= 1
    payload.write_bytes(raw)

    with pytest.raises(IntegratedSourceRejected, match="typed_payload_identity_mismatch"):
        cache.load_or_build_partition(
            source_path=source,
            symbol="GBPUSD",
            physical_timeframe="M15",
            source_payload_root=_sha256(source),
            open_text=lambda: pytest.fail("corrupt cache must fail closed"),
        )

    manifest_path = sealed.cache_entry_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["identity"]["source_bundle_root_sha256"] = "e" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(IntegratedSourceRejected):
        cache.load_or_build_partition(
            source_path=source,
            symbol="GBPUSD",
            physical_timeframe="M15",
            source_payload_root=_sha256(source),
            open_text=lambda: pytest.fail("wrong identity must fail closed"),
        )


def test_partition_selection_matches_real_legacy_resolver_semantics(tmp_path: Path) -> None:
    from src.research_infra.replay_acceleration_integrated_source import (
        select_days,
        select_replay_lookback_window,
    )

    source = tmp_path / "USDJPY_M15.csv"
    _write_source(source)
    rows = legacy.load_csv_rows(source, symbol="USDJPY")
    selected, grouped = select_days(rows, days=("2026-01-02", "2026-01-03"))
    assert selected == rows[1:]
    assert tuple(grouped) == ("2026-01-02", "2026-01-03")

    bounded, bounded_grouped, metadata = select_replay_lookback_window(
        rows,
        timeframe="M15",
        days=("2026-01-03",),
        min_total_rows=1,
    )
    assert bounded == rows
    # Preserve the real resolver's insertion order: in-window rows are added
    # first and the bounded pre-window deque is appended afterwards.
    assert tuple(bounded_grouped) == (
        "2026-01-03",
        "2026-01-01",
        "2026-01-02",
    )
    assert metadata["bounded_replay_requested_days"] == ["2026-01-03"]
    assert metadata["bounded_replay_prewindow_selected_rows"] == 2


def test_independent_verifier_does_not_import_writer_or_legacy_normalizer() -> None:
    verifier = Path(
        "src/research_infra/replay_acceleration_integrated_source_verifier.py"
    )
    tree = ast.parse(verifier.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    assert not any("replay_acceleration_integrated_source" in value for value in imports)
    assert not any("v4_timewarp_simulated_live_research_loop" in value for value in imports)


def test_real_accelerator_consumes_the_accepted_source_lease_bytes(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_integrated_source import (
        RealReplaySourceAccelerator,
    )

    operation = Path(
        "research/operations/replay_acceleration_bounded_slice_2026_07_19"
    )
    bundle_dir = operation / "scratch/primary/bundle"
    selection_path = operation / "SOURCE_SELECTION_RECEIPT.json"
    if not (bundle_dir / "SEALED").is_file():
        pytest.skip("accepted source bundle scratch is not materialized")
    bundle = json.loads((bundle_dir / "bundle.json").read_text(encoding="utf-8"))
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    physical = selection["physical_partitions"][0]
    source_path = Path(physical["source_path"])
    accelerator = RealReplaySourceAccelerator.from_accepted_bundle(
        source_bundle_dir=bundle_dir,
        selection_path=selection_path,
        typed_cache_root=tmp_path / "typed",
        expected_bundle_root=bundle["bundle_root_sha256"],
        expected_source_plan_digest=selection[
            "expected_source_plan_digest_sha256"
        ],
    )

    accelerated_rows, accelerated_grouped, source_sha256 = accelerator.load_file(
        source_path,
        symbol=physical["symbol"],
    )
    expected_rows = legacy.load_csv_rows(source_path, symbol=physical["symbol"])
    candidates = accelerator.accepted_source_candidates(
        symbol=physical["symbol"],
        physical_timeframe=physical["physical_timeframe"],
        source_family_order=(source_path.parent.name,),
    )
    assert accelerated_rows == expected_rows
    assert accelerated_grouped == legacy.rows_by_day(expected_rows)
    assert source_sha256 == physical["source_file_sha256"]
    assert accelerator.authority()["partition_count"] == 96
    assert accelerator.authority()["policy_execution_entered"] is False
    assert candidates[0].source_path == source_path
    assert candidates[0].source_family == source_path.parent.name


def test_accepted_physical_reference_uses_legacy_normalizer_without_typed_cache(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_integrated_source import (
        AcceptedPhysicalSourceReference,
    )

    evidence = Path(
        ".hermes/evidence/task2/source-bundle-consumer-rebind-20260722-r6"
    )
    bundle_dir = evidence / "materialization-current/bundle"
    selection_path = Path(
        ".hermes/evidence/task2/source-bundle-selection-refresh-20260722-r3/"
        "CURRENT_SOURCE_SELECTION_RECEIPT.json"
    )
    if not (bundle_dir / "SEALED").is_file():
        pytest.skip("current accepted source bundle is not materialized")
    bundle = json.loads((bundle_dir / "bundle.json").read_text(encoding="utf-8"))
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    physical = selection["physical_partitions"][0]
    source_path = Path(physical["source_path"])
    reference = AcceptedPhysicalSourceReference.from_accepted_bundle(
        source_bundle_dir=bundle_dir,
        selection_path=selection_path,
        expected_bundle_root=bundle["bundle_root_sha256"],
        expected_source_plan_digest=selection[
            "expected_source_plan_digest_sha256"
        ],
    )

    rows, grouped, source_sha256 = reference.load_file(
        source_path,
        symbol=physical["symbol"],
    )
    expected = legacy.load_csv_rows(source_path, symbol=physical["symbol"])

    assert rows == expected
    assert grouped == legacy.rows_by_day(expected)
    assert source_sha256 == physical["source_file_sha256"]
    authority = reference.authority()
    assert authority["loader"] == "legacy_csv_dict_reader_and_normalize_row"
    assert authority["typed_cache_enabled"] is False
    assert authority["sparse_bar_cache_enabled"] is False
    assert authority["metrics"]["physical_parse_count"] == 1
    assert not (tmp_path / "typed").exists()


def test_real_accelerator_rejects_wrong_pinned_bundle_root(tmp_path: Path) -> None:
    from src.research_infra.replay_acceleration_integrated_source import (
        IntegratedSourceRejected,
        RealReplaySourceAccelerator,
    )

    operation = Path(
        "research/operations/replay_acceleration_bounded_slice_2026_07_19"
    )
    bundle_dir = operation / "scratch/primary/bundle"
    selection_path = operation / "SOURCE_SELECTION_RECEIPT.json"
    if not (bundle_dir / "SEALED").is_file():
        pytest.skip("accepted source bundle scratch is not materialized")
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    with pytest.raises(IntegratedSourceRejected, match="accepted_source_bundle_root_mismatch"):
        RealReplaySourceAccelerator.from_accepted_bundle(
            source_bundle_dir=bundle_dir,
            selection_path=selection_path,
            typed_cache_root=tmp_path / "typed",
            expected_bundle_root="0" * 64,
            expected_source_plan_digest=selection[
                "expected_source_plan_digest_sha256"
            ],
        )


def test_broad_source_resolver_routes_all_csv_normalization_through_accelerator(
    tmp_path: Path,
) -> None:
    module_path = Path(
        "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py"
    )
    spec = importlib.util.spec_from_file_location(
        "broad_live_as_if_integrated_source_test", module_path
    )
    assert spec is not None and spec.loader is not None
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)

    source = tmp_path / "EURUSD_M15.csv"
    _write_source(source)
    rows = legacy.load_csv_rows(source, symbol="EURUSD")

    class StubAccelerator:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def accepted_source_candidates(
            self,
            *,
            symbol: str,
            physical_timeframe: str,
            source_family_order,
        ):
            family = tuple(source_family_order)[0]
            logical_path = (
                tmp_path
                / "retired-logical-root"
                / family
                / f"{symbol}_{physical_timeframe}.csv"
            )
            return (
                SimpleNamespace(
                    source_path=logical_path,
                    symbol=symbol,
                    mapped_symbol=symbol,
                    physical_timeframe=physical_timeframe,
                    source_family=family,
                ),
            )

        def load_file(self, path: Path, *, symbol: str):
            self.calls.append("file")
            return rows, legacy.rows_by_day(rows), "f" * 64

        def load_file_days(self, path: Path, *, symbol: str, days):
            self.calls.append("days")
            selected = tuple(row for row in rows if row["time"][:10] in set(days))
            return selected, legacy.rows_by_day(selected), "f" * 64

        def load_file_replay_lookback_window(
            self, path: Path, *, symbol: str, timeframe: str, days, min_total_rows: int
        ):
            self.calls.append("lookback")
            return rows, legacy.rows_by_day(rows), "f" * 64, {"source_hash_scope": "test"}

    accelerator = StubAccelerator()
    resolver = harness.BroadSourceResolver(source_accelerator=accelerator)
    assert resolver.load_file(source, symbol="EURUSD")[0] == rows
    assert resolver.load_file_days(
        source, symbol="EURUSD", days=("2026-01-02",)
    )[0] == rows[1:2]
    assert resolver.load_file_replay_lookback_window(
        source,
        symbol="EURUSD",
        timeframe="M15",
        days=("2026-01-02",),
        min_total_rows=1,
    )[0] == rows
    assert accelerator.calls == ["file", "days", "lookback"]

    resolved = resolver.resolve_file_source(
        symbol="EURUSD",
        timeframe="M15",
        root_order=("sealed-family",),
        min_total_rows=1,
        requested_days=("2026-01-02",),
    )
    assert resolved is not None
    assert str(resolved.spec.path).endswith(
        "retired-logical-root/sealed-family/EURUSD_M15.csv"
    )
    assert not resolved.spec.path.exists()

    m1_candidates = resolver.m1_source_candidates(
        symbol="EURUSD",
        month="202601",
        days=("2026-01-02",),
    )
    assert len(m1_candidates) == 1
    assert str(m1_candidates[0][0]).endswith(
        "retired-logical-root/bridge_ftmo_m1_202601/EURUSD_M1.csv"
    )
    assert not m1_candidates[0][0].exists()

    accelerator.calls.clear()
    physical_resolver = harness.BroadSourceResolver(
        physical_source_reference=accelerator
    )
    physical = physical_resolver.resolve_file_source(
        symbol="EURUSD",
        timeframe="M15",
        root_order=("sealed-family",),
        min_total_rows=1,
        requested_days=("2026-01-02",),
    )
    assert physical is not None
    assert accelerator.calls == ["lookback"]
    assert physical_resolver.source_accelerator is None

    with pytest.raises(ValueError, match="source_loader_modes_are_mutually_exclusive"):
        harness.BroadSourceResolver(
            source_accelerator=accelerator,
            physical_source_reference=accelerator,
        )


def test_runtime_evidence_root_rebinds_only_existing_read_only_inputs() -> None:
    module_path = Path(
        "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py"
    )
    spec = importlib.util.spec_from_file_location(
        "broad_live_as_if_runtime_evidence_test", module_path
    )
    assert spec is not None and spec.loader is not None
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)

    contract = harness.configure_runtime_evidence_root(
        Path("/Users/borr/GTOSActive/repo")
    )
    assert contract["read_only_existing_evidence"] is True
    assert contract["legacy_evidence_mutation_enabled"] is False
    assert sum(bool(value["present"]) for value in contract["inputs"].values()) == 5
    assert harness.ultimate_package_runtime_input_contract()["valid"] is True
    assert (
        harness.timewarp_loop.ULTIMATE_PACKAGE_MEMBER_AXIS_LEDGER_PATH
        == Path(contract["inputs"]["member_axis"]["path"])
    )


def test_sealed_s0r0_arm_binding_resolves_exact_external_legacy_inputs() -> None:
    module_path = Path(
        "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py"
    )
    spec = importlib.util.spec_from_file_location(
        "broad_live_as_if_external_binding_test", module_path
    )
    assert spec is not None and spec.loader is not None
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    partial = json.loads(
        Path(
            "research/operations/replay_acceleration_partial_golden_2026_07_19/PARTIAL_GOLDEN_MANIFEST.json"
        ).read_text(encoding="utf-8")
    )
    args = argparse.Namespace(
        decision_contract=Path(
            "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_SELECTION_SIZING_DECISION_CONTRACT.json"
        ),
        arm_id="S0R0",
        expected_arm_fingerprint_sha256=partial["contract_identity"][
            "arm_fingerprint_sha256"
        ],
        runtime_evidence_root=Path("/Users/borr/GTOSActive/repo"),
    )
    harness.configure_runtime_evidence_root(args.runtime_evidence_root)
    binding = harness.selection_sizing_factorial_binding_from_args(args)
    assert binding["arm_id"] == "S0R0"
    assert binding["arm_fingerprint_sha256"] == partial["contract_identity"][
        "arm_fingerprint_sha256"
    ]

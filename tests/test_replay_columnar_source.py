"""Behavioural tests for the columnar source layer.

These assert against *decoded values and measured memory*, never against source
text. The central claim — that a columnar row is indistinguishable from the dict
the sealed loader builds — is tested by decoding the same bytes both ways and
comparing, not by inspecting either implementation.
"""

from __future__ import annotations

import gc
import hashlib
import json
import struct
import sys
import tracemalloc
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.replay_acceleration_integrated_source import (  # noqa: E402
    _HEADER,
    _MAGIC,
    _ROW,
    IntegratedSourceRejected,
    TYPED_MANIFEST_SCHEMA,
    _canonical_bytes,
    _root,
    _row_from_values,
)
from src.research_infra.replay_columnar_source import (  # noqa: E402
    ColumnarPartition,
    ColumnarPartitionStore,
    ColumnarRow,
    ColumnarRowSequence,
)
from src.research_infra.v4_timewarp_simulated_live_research_loop import (  # noqa: E402
    rows_by_day as legacy_rows_by_day,
)

# The sealed January typed cache. Read-only; tests skip cleanly without it.
SEALED_TYPED_CACHE = Path(
    "/Users/borr/GTOSActive/worktrees/replay-accel-engine-20260719/.hermes/evidence/"
    "phase-d/january-post-acceleration-source-20260723T225928Z/typed-cache"
)

requires_sealed_cache = pytest.mark.skipif(
    not SEALED_TYPED_CACHE.is_dir(),
    reason="sealed January typed cache not present on this machine",
)


# ---------------------------------------------------------------------------
# Fixture construction — builds a typed-cache entry the way the sealed writer
# does, so tests do not depend on the sealed tree being present.
# ---------------------------------------------------------------------------


def _write_entry(root: Path, *, symbol: str, timeframe: str, rows: list[tuple]) -> Path:
    """Write a valid typed-cache entry. `rows` is [(micros, o, h, l, c, v), ...]."""
    identity = {
        "schema": "gtos.replay_acceleration.integrated_typed_source_cache.v1",
        "typed_row_schema": "gtos.replay_acceleration.ohlcv_time_f64.v1",
        "source_bundle_root_sha256": "a" * 64,
        "config_projection_root_sha256": "b" * 64,
        "source_payload_root_sha256": "c" * 64,
        "source_path_root_sha256": "d" * 64,
        "normalizer_code_root_sha256": "e" * 64,
        "symbol": symbol,
        "physical_timeframe": timeframe,
        "accepted_normalized_root_sha256": None,
        "accepted_normalized_row_count": None,
    }
    identity_root = _root(identity)
    entry = root / identity_root
    entry.mkdir(parents=True)

    payload = bytearray(_HEADER.pack(_MAGIC, len(rows)))
    digest = hashlib.sha256(b"gtos.replay_acceleration.canonical_rows.v1\n")
    for micros, *values in rows:
        payload += _ROW.pack(micros, *values)
        digest.update(
            _canonical_bytes(
                _row_from_values(symbol=symbol, micros=micros, values=values)
            )
        )
        digest.update(b"\n")
    payload = bytes(payload)
    (entry / "rows.bin").write_bytes(payload)

    manifest = {
        "schema": TYPED_MANIFEST_SCHEMA,
        "identity": identity,
        "identity_root_sha256": identity_root,
        "row_count": len(rows),
        "payload_byte_count": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "rows_root_sha256": digest.hexdigest(),
        "manifest_root_sha256": None,
    }
    projection = dict(manifest)
    projection.pop("manifest_root_sha256")
    manifest["manifest_root_sha256"] = _root(projection)
    (entry / "manifest.json").write_bytes(_canonical_bytes(manifest) + b"\n")
    (entry / "SEALED").write_bytes(manifest["manifest_root_sha256"].encode("ascii") + b"\n")
    return entry


DAY = 86_400_000_000
JAN01 = 1_767_225_600_000_000  # 2026-01-01T00:00:00Z


@pytest.fixture()
def two_day_entry(tmp_path: Path) -> Path:
    rows = [
        (JAN01 + minute * 60_000_000, 1.10 + minute * 1e-5, 1.20, 1.05, 1.15, 100.0 + minute)
        for minute in range(5)
    ] + [
        (JAN01 + DAY + minute * 60_000_000, 2.10, 2.20, 2.05, 2.15, 200.0 + minute)
        for minute in range(3)
    ]
    return _write_entry(tmp_path / "cache", symbol="EURUSD", timeframe="M1", rows=rows)


def _reference_rows(entry: Path) -> tuple[dict, ...]:
    """Decode an entry exactly as `_load_entry` does. The comparison baseline."""
    manifest = json.loads((entry / "manifest.json").read_text())
    payload = (entry / "rows.bin").read_bytes()
    symbol = manifest["identity"]["symbol"]
    out = []
    offset = _HEADER.size
    for _ in range(manifest["row_count"]):
        micros, *values = _ROW.unpack_from(payload, offset)
        offset += _ROW.size
        out.append(_row_from_values(symbol=symbol, micros=micros, values=values))
    return tuple(out)


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------


def test_a_columnar_row_equals_the_dict_the_sealed_loader_builds(two_day_entry):
    partition = ColumnarPartition.load(two_day_entry)
    reference = _reference_rows(two_day_entry)
    assert len(partition.rows()) == len(reference)
    for columnar, sealed in zip(partition.rows(), reference):
        assert dict(columnar) == sealed
        assert columnar == sealed


def test_canonical_bytes_are_identical_so_every_downstream_digest_matches(two_day_entry):
    partition = ColumnarPartition.load(two_day_entry)
    for columnar, sealed in zip(partition.rows(), _reference_rows(two_day_entry)):
        assert _canonical_bytes(dict(columnar)) == _canonical_bytes(sealed)


def test_the_sealed_rows_root_digest_is_reproduced_from_the_columns(two_day_entry):
    manifest = json.loads((two_day_entry / "manifest.json").read_text())
    partition = ColumnarPartition.load(two_day_entry, verify_rows_root=False)
    assert partition.canonical_rows_root() == manifest["rows_root_sha256"]


def test_a_row_view_exposes_the_full_mapping_protocol(two_day_entry):
    row = ColumnarPartition.load(two_day_entry).rows()[0]
    sealed = _reference_rows(two_day_entry)[0]
    assert set(row.keys()) == set(sealed)
    assert dict(row.items()) == sealed
    assert row.get("close") == sealed["close"]
    assert row.get("nope", "fallback") == "fallback"
    assert row["symbol"] == "EURUSD"
    assert isinstance(row["open"], float)  # not np.float64 - json.dumps rejects that
    assert type(row["open"]) is float
    with pytest.raises(KeyError):
        row["not_a_column"]


def test_a_row_view_is_unhashable_exactly_like_the_dict_it_replaces(two_day_entry):
    row = ColumnarPartition.load(two_day_entry).rows()[0]
    with pytest.raises(TypeError):
        hash(row)


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------


def test_day_grouping_matches_the_legacy_rows_by_day_exactly(two_day_entry):
    partition = ColumnarPartition.load(two_day_entry)
    legacy = legacy_rows_by_day(_reference_rows(two_day_entry))
    columnar = partition.rows_by_day()
    assert set(columnar) == set(legacy)
    for day in legacy:
        assert [dict(row) for row in columnar[day]] == list(legacy[day])


def test_select_days_seeds_absent_days_and_orders_by_day(two_day_entry):
    partition = ColumnarPartition.load(two_day_entry)
    _selected, grouped = partition.select_days(["2026-01-02", "2026-01-09", "2026-01-01"])
    assert set(grouped) == {"2026-01-01", "2026-01-02", "2026-01-09"}
    assert len(grouped["2026-01-09"]) == 0  # requested but absent -> empty, not missing
    assert len(grouped["2026-01-01"]) == 5
    assert len(grouped["2026-01-02"]) == 3


def test_an_absent_day_returns_an_empty_view_not_an_error(two_day_entry):
    partition = ColumnarPartition.load(two_day_entry)
    assert len(partition.rows_for_day("2019-03-03")) == 0


# ---------------------------------------------------------------------------
# Sequence semantics
# ---------------------------------------------------------------------------


def test_the_sequence_supports_what_the_engine_actually_does_to_it(two_day_entry):
    rows = ColumnarPartition.load(two_day_entry).rows()
    reference = _reference_rows(two_day_entry)
    assert len(rows) == 8
    assert [dict(r) for r in rows] == list(reference)          # iteration
    assert dict(rows[-1]) == reference[-1]                      # negative index
    assert [dict(r) for r in rows[2:5]] == list(reference[2:5])  # slice
    assert isinstance(rows[2:5], ColumnarRowSequence)            # slice stays lazy
    assert rows == reference                                     # equality vs tuple
    with pytest.raises(IndexError):
        rows[99]


def test_slicing_a_slice_addresses_the_right_rows(two_day_entry):
    rows = ColumnarPartition.load(two_day_entry).rows()
    reference = _reference_rows(two_day_entry)
    assert [dict(r) for r in rows[2:7][1:3]] == list(reference[2:7][1:3])


# ---------------------------------------------------------------------------
# The two claims the layer exists to make
# ---------------------------------------------------------------------------


def test_the_store_materialises_a_partition_once_however_often_it_is_asked(two_day_entry):
    store = ColumnarPartitionStore()
    first = store.get(two_day_entry)
    for _ in range(20):
        assert store.get(two_day_entry) is first
    metrics = store.metrics()
    assert metrics["partition_load_count"] == 1
    assert metrics["partition_hit_count"] == 20
    assert len(store) == 1


def test_columns_cost_the_48_bytes_per_row_they_occupy_on_disk(two_day_entry):
    partition = ColumnarPartition.load(two_day_entry)
    assert partition.nbytes() == partition.row_count * _ROW.size


def test_holding_rows_costs_an_order_of_magnitude_less_than_the_sealed_dicts(tmp_path):
    """The headline claim, as a measurement rather than an assertion."""
    count = 40_000
    entry = _write_entry(
        tmp_path / "cache",
        symbol="EURUSD",
        timeframe="M1",
        rows=[
            (JAN01 + i * 60_000_000, 1.1 + i * 1e-9, 1.2, 1.0, 1.15, 10.0)
            for i in range(count)
        ],
    )

    gc.collect()
    tracemalloc.start()
    sealed = _reference_rows(entry)
    sealed_bytes = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    del sealed
    gc.collect()

    tracemalloc.start()
    partition = ColumnarPartition.load(entry, verify_rows_root=False)
    held = partition.rows(), partition.rows_by_day()
    columnar_bytes = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()

    assert len(held[0]) == count
    per_row_sealed = sealed_bytes / count
    per_row_columnar = columnar_bytes / count
    assert per_row_sealed > 300, f"sealed rows unexpectedly cheap: {per_row_sealed:.0f} B/row"
    assert per_row_columnar < 80, f"columnar not columnar: {per_row_columnar:.0f} B/row"
    assert sealed_bytes / columnar_bytes > 5.0, (
        f"expected >5x, got {sealed_bytes / columnar_bytes:.1f}x "
        f"({per_row_sealed:.0f} vs {per_row_columnar:.0f} B/row)"
    )


def test_verification_retains_no_rows(tmp_path):
    """`canonical_rows_root` streams: it must not retain the rows it digests.

    It is not free — the shared timestamp memo grows — so the claim under test
    is that verifying N rows costs far less than *materialising* N rows, and
    that what it does retain is the memo, which is capped.
    """
    count = 30_000
    entry = _write_entry(
        tmp_path / "cache",
        symbol="EURUSD",
        timeframe="M1",
        rows=[(JAN01 + i * 60_000_000, 1.1, 1.2, 1.0, 1.15, 10.0) for i in range(count)],
    )
    partition = ColumnarPartition.load(entry, verify_rows_root=False)

    gc.collect()
    tracemalloc.start()
    partition.canonical_rows_root()
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()

    # Materialising the same rows as dicts costs ~470 B/row (B80). Verification
    # must stay far under that, and a second pass must cost near nothing because
    # the timestamps are already memoised.
    assert peak < count * 200, f"verification cost {peak / count:.0f} B/row"

    gc.collect()
    tracemalloc.start()
    partition.canonical_rows_root()
    second_peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    assert second_peak < 100_000, f"second pass retained {second_peak} bytes"


def test_the_timestamp_memo_is_bounded(tmp_path):
    """The memo trades a capped allocation for decode speed. Prove the cap holds."""
    from src.research_infra import replay_columnar_source as layer

    original = dict(layer._ISO_MEMO)
    try:
        layer._ISO_MEMO.clear()
        for micros in range(layer._ISO_MEMO_LIMIT + 5_000):
            layer.iso_for_micros(JAN01 + micros * 60_000_000)
        assert len(layer._ISO_MEMO) == layer._ISO_MEMO_LIMIT
        # Still correct past the cap - it just stops caching.
        beyond = JAN01 + (layer._ISO_MEMO_LIMIT + 4_000) * 60_000_000
        assert layer.iso_for_micros(beyond) == layer._decode_timestamp(beyond)
    finally:
        layer._ISO_MEMO.clear()
        layer._ISO_MEMO.update(original)


# ---------------------------------------------------------------------------
# Fail-closed behaviour — the sealed loader's checks must survive
# ---------------------------------------------------------------------------


def test_a_corrupted_payload_is_rejected(two_day_entry):
    payload = bytearray((two_day_entry / "rows.bin").read_bytes())
    payload[-1] ^= 0xFF
    (two_day_entry / "rows.bin").write_bytes(bytes(payload))
    with pytest.raises(IntegratedSourceRejected) as excinfo:
        ColumnarPartition.load(two_day_entry)
    assert "payload_identity_mismatch" in str(excinfo.value)


def test_a_truncated_payload_is_rejected_on_framing(two_day_entry):
    payload = (two_day_entry / "rows.bin").read_bytes()
    truncated = payload[: len(payload) - _ROW.size]
    manifest = json.loads((two_day_entry / "manifest.json").read_text())
    manifest["payload_byte_count"] = len(truncated)
    manifest["payload_sha256"] = hashlib.sha256(truncated).hexdigest()
    projection = dict(manifest)
    projection.pop("manifest_root_sha256")
    manifest["manifest_root_sha256"] = _root(projection)
    (two_day_entry / "rows.bin").write_bytes(truncated)
    (two_day_entry / "manifest.json").write_bytes(_canonical_bytes(manifest) + b"\n")
    (two_day_entry / "SEALED").write_bytes(
        manifest["manifest_root_sha256"].encode("ascii") + b"\n"
    )
    with pytest.raises(IntegratedSourceRejected) as excinfo:
        ColumnarPartition.load(two_day_entry)
    assert "framing_mismatch" in str(excinfo.value)


def test_a_tampered_row_value_is_caught_by_the_rows_root_digest(two_day_entry):
    """Payload sha rewritten to match, so only the rows digest can catch this."""
    payload = bytearray((two_day_entry / "rows.bin").read_bytes())
    struct.pack_into("<d", payload, _HEADER.size + 8, 9.99)  # overwrite first open
    payload = bytes(payload)
    manifest = json.loads((two_day_entry / "manifest.json").read_text())
    manifest["payload_sha256"] = hashlib.sha256(payload).hexdigest()
    projection = dict(manifest)
    projection.pop("manifest_root_sha256")
    manifest["manifest_root_sha256"] = _root(projection)
    (two_day_entry / "rows.bin").write_bytes(payload)
    (two_day_entry / "manifest.json").write_bytes(_canonical_bytes(manifest) + b"\n")
    (two_day_entry / "SEALED").write_bytes(
        manifest["manifest_root_sha256"].encode("ascii") + b"\n"
    )
    with pytest.raises(IntegratedSourceRejected) as excinfo:
        ColumnarPartition.load(two_day_entry)
    assert "rows_root_mismatch" in str(excinfo.value)


def test_a_broken_seal_is_rejected(two_day_entry):
    (two_day_entry / "SEALED").write_bytes(b"0" * 64 + b"\n")
    with pytest.raises(IntegratedSourceRejected):
        ColumnarPartition.load(two_day_entry)


def test_an_unexpected_identity_is_rejected(two_day_entry):
    with pytest.raises(IntegratedSourceRejected) as excinfo:
        ColumnarPartition.load(two_day_entry, expected_identity={"symbol": "WRONG"})
    assert "identity_mismatch" in str(excinfo.value)


def test_an_empty_partition_loads_and_groups_to_nothing(tmp_path):
    entry = _write_entry(tmp_path / "cache", symbol="EURUSD", timeframe="M1", rows=[])
    partition = ColumnarPartition.load(entry)
    assert partition.row_count == 0
    assert len(partition.rows()) == 0
    assert partition.rows_by_day() == {}


# ---------------------------------------------------------------------------
# Against the real sealed cache
# ---------------------------------------------------------------------------


@requires_sealed_cache
def test_every_row_of_a_real_sealed_partition_decodes_identically():
    entries = [e for e in sorted(SEALED_TYPED_CACHE.iterdir()) if (e / "manifest.json").is_file()]
    assert entries, "probe found no entries - it would report a false pass"
    biggest = max(
        entries, key=lambda e: json.loads((e / "manifest.json").read_text())["row_count"]
    )
    partition = ColumnarPartition.load(biggest)
    reference = _reference_rows(biggest)
    assert partition.row_count == len(reference) > 10_000
    mismatches = sum(
        1 for columnar, sealed in zip(partition.rows(), reference) if dict(columnar) != sealed
    )
    assert mismatches == 0


@requires_sealed_cache
def test_real_sealed_partitions_are_time_ordered_so_day_views_are_contiguous():
    import numpy as np

    entries = [e for e in sorted(SEALED_TYPED_CACHE.iterdir()) if (e / "manifest.json").is_file()]
    assert entries, "probe found no entries - it would report a false pass"
    checked = 0
    for entry in entries[:24]:
        partition = ColumnarPartition.load(entry, verify_rows_root=False)
        if partition.row_count < 2:
            continue
        assert bool(np.all(np.diff(partition.micros) > 0)), f"{entry.name} not ordered"
        checked += 1
    assert checked >= 10


# ---------------------------------------------------------------------------
# The substitution boundary
# ---------------------------------------------------------------------------
# The bridge's whole claim is that the sealed slicers cannot tell a lazy
# ColumnarRowSequence from the tuple[dict, ...] they are written against. These
# feed both to the real, unmodified slicer functions and compare outputs.


def test_the_lookback_slicer_cannot_tell_the_two_apart(two_day_entry):
    from src.research_infra.replay_acceleration_integrated_source import (
        select_replay_lookback_window,
    )

    partition = ColumnarPartition.load(two_day_entry)
    reference = _reference_rows(two_day_entry)
    kwargs = dict(timeframe="M1", days=["2026-01-02"], min_total_rows=3)

    sealed_rows, sealed_grouped, sealed_meta = select_replay_lookback_window(
        reference, **kwargs
    )
    columnar_rows, columnar_grouped, columnar_meta = select_replay_lookback_window(
        partition.rows(), **kwargs
    )

    assert columnar_rows == sealed_rows
    assert columnar_grouped == sealed_grouped
    assert columnar_meta == sealed_meta
    assert all(type(row) is dict for row in columnar_rows)  # real dicts come out


def test_the_day_slicer_cannot_tell_the_two_apart(two_day_entry):
    from src.research_infra.replay_acceleration_integrated_source import select_days

    partition = ColumnarPartition.load(two_day_entry)
    reference = _reference_rows(two_day_entry)
    days = ["2026-01-01", "2026-01-02", "2026-01-30"]

    sealed_rows, sealed_grouped = select_days(reference, days=days)
    columnar_rows, columnar_grouped = select_days(partition.rows(), days=days)

    assert columnar_rows == sealed_rows
    assert columnar_grouped == sealed_grouped


def test_the_source_hash_over_the_returned_rows_is_unchanged(two_day_entry):
    """`load_file_replay_lookback_window:1076-1078` hashes the rows it returns."""
    from src.research_infra.replay_acceleration_integrated_source import (
        select_replay_lookback_window,
    )
    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        stable_sha256,
    )

    partition = ColumnarPartition.load(two_day_entry)
    reference = _reference_rows(two_day_entry)
    kwargs = dict(timeframe="M1", days=["2026-01-02"], min_total_rows=3)

    sealed_rows, _g, sealed_meta = select_replay_lookback_window(reference, **kwargs)
    columnar_rows, _g2, columnar_meta = select_replay_lookback_window(
        partition.rows(), **kwargs
    )
    assert stable_sha256({**columnar_meta, "rows": columnar_rows}) == stable_sha256(
        {**sealed_meta, "rows": sealed_rows}
    )


@requires_sealed_cache
def test_the_slicers_agree_on_real_sealed_partitions():
    from src.research_infra.replay_acceleration_integrated_source import (
        select_days,
        select_replay_lookback_window,
    )

    entries = [
        e for e in sorted(SEALED_TYPED_CACHE.iterdir()) if (e / "manifest.json").is_file()
    ]
    assert entries, "probe found no entries - it would report a false pass"
    m1 = [
        e
        for e in entries
        if json.loads((e / "manifest.json").read_text())["identity"][
            "physical_timeframe"
        ]
        == "M1"
    ]
    assert m1, "probe found no M1 partitions - it would report a false pass"

    checked = 0
    for entry in m1[:4]:
        partition = ColumnarPartition.load(entry, verify_rows_root=False)
        reference = _reference_rows(entry)
        days = sorted(partition.day_labels())[:3]
        assert days
        assert select_days(partition.rows(), days=days) == select_days(
            reference, days=days
        )
        assert select_replay_lookback_window(
            partition.rows(), timeframe="M1", days=days, min_total_rows=100
        ) == select_replay_lookback_window(
            reference, timeframe="M1", days=days, min_total_rows=100
        )
        checked += 1
    assert checked >= 3


def test_the_bridge_installs_and_uninstalls_cleanly():
    from src.research_infra import replay_acceleration_attempt5_typed_sparse_runner as attempt5
    from src.research_infra import replay_columnar_bridge as bridge
    from src.research_infra.replay_acceleration_integrated_source import (
        RealReplaySourceAccelerator,
    )

    original = attempt5.RealReplaySourceAccelerator
    try:
        bridge.install()
        assert attempt5.RealReplaySourceAccelerator is bridge.ColumnarSourceAccelerator
        bridge.install()  # idempotent
        assert attempt5.RealReplaySourceAccelerator is bridge.ColumnarSourceAccelerator
        bridge.uninstall()
        assert attempt5.RealReplaySourceAccelerator is original
    finally:
        bridge.uninstall()
        attempt5.RealReplaySourceAccelerator = original
    assert issubclass(bridge.ColumnarSourceAccelerator, RealReplaySourceAccelerator)


def test_installing_joins_the_engines_cache_release_path():
    """The store must release on clear_replay_source_caches, or it adds to peak RSS.

    Measured consequence of not doing this: ~0.17 GB retained for a whole arm.
    """
    from src.research_infra import replay_acceleration_attempt5_typed_sparse_runner as attempt5
    from src.research_infra import replay_columnar_bridge as bridge
    from src.research_infra import v4_timewarp_simulated_live_research_loop as legacy

    original_accel = attempt5.RealReplaySourceAccelerator
    original_clear = legacy.clear_replay_source_caches
    try:
        bridge.install()
        assert legacy.clear_replay_source_caches is not original_clear
        bridge._STORE._partitions["sentinel"] = object()
        assert len(bridge._STORE) == 1
        legacy.clear_replay_source_caches()          # the engine's chunk-boundary call
        assert len(bridge._STORE) == 0, "store did not release with the engine"
    finally:
        bridge.uninstall()
        bridge._STORE.clear()
        attempt5.RealReplaySourceAccelerator = original_accel
        legacy.clear_replay_source_caches = original_clear
    assert legacy.clear_replay_source_caches is original_clear

from __future__ import annotations

import copy
import hashlib
import json
import os
import pickle
import stat
import subprocess
import sys
import traceback
from dataclasses import replace
from itertools import permutations
from pathlib import Path
from typing import Any

import pytest

from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp


PARTITION = {
    "symbol": "XAUUSD",
    "timeframe": "M15",
    "date": "2026-01-05",
}
SOURCE_IDENTITY = "fixture://xauusd/m15/2026-01-05"
DEFAULT_SOURCE_PATH = Path("/gtos-fixture/XAUUSD_M15_2026-01-05.csv")
CSV_PAYLOAD = (
    b"time,open,high,low,close,volume\n"
    b"2026-01-05T09:00:00+00:00,2400,2402,2399,2401,10\n"
    b"2026-01-05T09:15:00+00:00,2401,2403,2400,2402,12\n"
)
QUOTED_NEWLINE_CSV_PAYLOAD = (
    b"time,open,high,low,close,volume,note\n"
    b'2026-01-05T09:00:00+00:00,2400,2402,2399,2401,10,"alpha\nbeta"\n'
    b"2026-01-05T09:15:00+00:00,2401,2403,2400,2402,12,gamma\n"
)
MALFORMED_QUOTED_CSV_PAYLOAD = (
    b"time,open,high,low,close,volume,note\n"
    b'2026-01-05T09:00:00+00:00,2400,2402,2399,2401,10,"'
    b"CSV_FRAMING_MARKER_MUST_NOT_ESCAPE\n"
)


def _api():
    from src.research_infra import replay_acceleration_source_batch as source_batch

    return source_batch


def _projection(api, config: dict[str, Any] | None = None):
    guard = api.ConfigReadGuard(
        config or {},
        known_keys=set((config or {}).keys()),
        projection_keys=set((config or {}).keys()),
    )
    for key in sorted((config or {}).keys()):
        guard[key]
    return guard.seal_projection()


def _binding(
    api,
    *,
    config: dict[str, Any] | None = None,
    source_path: Path = DEFAULT_SOURCE_PATH,
    partition: dict[str, str] = PARTITION,
):
    return api.SourceBatchBinding.create(
        stage=api.SOURCE_BYTES_STAGE,
        source_identity=SOURCE_IDENTITY,
        source_path=source_path,
        partition_identity=partition,
        config_projection=_projection(api, config),
    )


def _admitted_cache(api, tmp_path: Path, binding):
    registry = api.CacheAdmissionRegistry()
    registry.admit(
        stage=binding.stage,
        implementation_identity_root=binding.implementation_root,
        config_projection_keys=binding.config_projection_keys,
    )
    return api.ImmutableSourceBatchCache(tmp_path / "cache", registry=registry)


def _rewrite_manifest(api, cache, batch_root: str, mutate, *, canonical: bool) -> str:
    batch_path = cache.batch_path(batch_root)
    manifest_path = batch_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mutate(manifest)
    if canonical:
        manifest_bytes = (
            json.dumps(
                manifest,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("utf-8")
            + b"\n"
        )
    else:
        manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8") + b"\n"
    rewritten_root = hashlib.sha256(manifest_bytes).hexdigest()
    batch_path.chmod(0o755)
    manifest_path.chmod(0o644)
    manifest_path.write_bytes(manifest_bytes)
    manifest_path.chmod(0o444)
    rewritten_path = cache.batch_path(rewritten_root)
    batch_path.rename(rewritten_path)
    rewritten_path.chmod(0o555)
    return rewritten_root


def _assert_redacted_exception(exc: BaseException, marker: str) -> None:
    assert marker not in str(exc)
    structural_output = getattr(exc, "structural_output")()
    assert marker not in json.dumps(structural_output, sort_keys=True)
    assert exc.__cause__ is None
    assert exc.__context__ is None
    rendered = "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    )
    assert marker not in rendered


def _worker_command(api, cache, sealed, binding, *, arm: str = "S0R0") -> list[str]:
    return [
        sys.executable,
        str(Path(api.__file__).resolve()),
        "_consume",
        str(cache.root),
        sealed.batch_root,
        json.dumps(binding.as_dict(), separators=(",", ":")),
        arm,
    ]


def test_implementation_root_binds_only_the_csv_source_consumer_surface(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _api()
    api.implementation_root.cache_clear()
    api._source_consumer_component_root.cache_clear()
    baseline = api.implementation_root()

    monkeypatch.setattr(timewarp, "evaluate_candidate_v4", object())
    api.implementation_root.cache_clear()
    api._source_consumer_component_root.cache_clear()
    assert api.implementation_root() == baseline

    role, source_path, function_names, constant_names = (
        api._SOURCE_CONSUMER_COMPONENTS[0]
    )
    copied_source = tmp_path / source_path.name
    source_text = source_path.read_text(encoding="utf-8")
    copied_source.write_text(source_text, encoding="utf-8")
    monkeypatch.setattr(
        api,
        "_SOURCE_CONSUMER_COMPONENTS",
        (
            (role, copied_source, function_names, constant_names),
            *api._SOURCE_CONSUMER_COMPONENTS[1:],
        ),
    )
    api.implementation_root.cache_clear()
    api._source_consumer_component_root.cache_clear()
    assert api.implementation_root() == baseline

    target = "return tuple(row for row in rows if row is not None)"
    assert source_text.count(target) == 1
    copied_source.write_text(
        source_text.replace(target, f"{target} + ()"),
        encoding="utf-8",
    )
    api.implementation_root.cache_clear()
    api._source_consumer_component_root.cache_clear()
    assert api.implementation_root() != baseline

    copied_source.write_text(
        source_text.replace(
            "\n\nROUTE_ID = ",
            "\n\nparse_utc = lambda value: None\n\nROUTE_ID = ",
            1,
        ),
        encoding="utf-8",
    )
    api.implementation_root.cache_clear()
    api._source_consumer_component_root.cache_clear()
    assert api.implementation_root() != baseline


def test_implementation_root_parses_scoped_sources_once_per_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _api()
    api.implementation_root.cache_clear()
    api._source_consumer_component_root.cache_clear()
    original_parse = api.ast.parse
    parse_calls = 0

    def counted_parse(*args: Any, **kwargs: Any):
        nonlocal parse_calls
        parse_calls += 1
        return original_parse(*args, **kwargs)

    monkeypatch.setattr(api.ast, "parse", counted_parse)

    first = api.implementation_root()
    second = api.implementation_root()

    assert second == first
    assert parse_calls == len(api._SOURCE_CONSUMER_COMPONENTS)


def test_cache_admission_is_default_deny(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    cache = api.ImmutableSourceBatchCache(
        tmp_path / "cache",
        registry=api.CacheAdmissionRegistry(),
    )

    with pytest.raises(api.SourceBatchRejected, match="cache_stage_not_admitted") as exc:
        cache.seal(CSV_PAYLOAD, binding=binding)

    assert exc.value.code == "cache_stage_not_admitted"
    assert not (tmp_path / "cache").exists()


def test_cache_admission_is_enforced_again_on_read(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    writer = _admitted_cache(api, tmp_path, binding)
    sealed = writer.seal(CSV_PAYLOAD, binding=binding)
    unadmitted_reader = api.ImmutableSourceBatchCache(
        writer.root,
        registry=api.CacheAdmissionRegistry(),
    )

    with pytest.raises(api.SourceBatchRejected, match="cache_stage_not_admitted"):
        unadmitted_reader.acquire_lease(
            sealed.batch_root,
            expected_binding=binding,
        )


def test_source_slice_refuses_later_stage_admission() -> None:
    api = _api()
    registry = api.CacheAdmissionRegistry()

    for stage in api.CONDITIONAL_OR_ARM_LOCAL_STAGES:
        with pytest.raises(
            api.SourceBatchRejected,
            match="stage_not_admissible_in_source_slice",
        ):
            registry.admit(
                stage=stage,
                implementation_identity_root=api.implementation_root(),
                config_projection_keys=(),
            )


def test_source_bytes_admission_requires_empty_config_projection() -> None:
    api = _api()
    binding = _binding(api, config={"source.encoding": "utf-8"})
    registry = api.CacheAdmissionRegistry()

    with pytest.raises(
        api.SourceBatchRejected,
        match="source_bytes_config_projection_must_be_empty",
    ) as exc:
        registry.admit(
            stage=binding.stage,
            implementation_identity_root=binding.implementation_root,
            config_projection_keys=binding.config_projection_keys,
        )

    assert exc.value.code == "source_bytes_config_projection_must_be_empty"


def test_forged_empty_config_projection_root_is_not_admitted(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    registry = api.CacheAdmissionRegistry()
    registry.admit(
        stage=binding.stage,
        implementation_identity_root=binding.implementation_root,
        config_projection_keys=binding.config_projection_keys,
    )
    forged = replace(binding, config_projection_root="9" * 64)
    cache = api.ImmutableSourceBatchCache(tmp_path / "cache", registry=registry)

    with pytest.raises(api.SourceBatchRejected, match="cache_stage_not_admitted"):
        cache.seal(CSV_PAYLOAD, binding=forged)


def test_content_addressed_identity_is_immutable_and_repeatable(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)

    first = cache.seal(CSV_PAYLOAD, binding=binding)
    repeat = cache.seal(CSV_PAYLOAD, binding=binding)
    changed = cache.seal(CSV_PAYLOAD + b"\n", binding=binding)

    assert first.batch_root == repeat.batch_root
    assert first.payload_root == repeat.payload_root
    assert repeat.cache_hit is True
    assert changed.batch_root != first.batch_root
    assert changed.payload_root != first.payload_root
    assert cache.payload_path(first.batch_root).read_bytes() == CSV_PAYLOAD
    assert cache.payload_path(first.batch_root).stat().st_mode & 0o222 == 0


def test_record_count_uses_csv_framing_for_quoted_newlines(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)

    sealed = cache.seal(QUOTED_NEWLINE_CSV_PAYLOAD, binding=binding)

    assert sealed.record_count == 2


@pytest.mark.parametrize(
    "malformed_payload",
    (
        MALFORMED_QUOTED_CSV_PAYLOAD,
        MALFORMED_QUOTED_CSV_PAYLOAD.replace(b"\n", b"\r\n"),
        MALFORMED_QUOTED_CSV_PAYLOAD.rstrip(b"\n") + b'"junk\n',
    ),
    ids=("unterminated-lf", "unterminated-crlf", "junk-after-closing-quote"),
)
def test_malformed_quoted_csv_is_rejected_without_marker_retention(
    tmp_path: Path,
    malformed_payload: bytes,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    marker = "CSV_FRAMING_MARKER_MUST_NOT_ESCAPE"

    with pytest.raises(
        api.SourceBatchRejected,
        match="malformed_csv_framing",
    ) as exc:
        cache.seal(malformed_payload, binding=binding)

    _assert_redacted_exception(exc.value, marker)
    assert not cache.root.exists()


def test_binding_rejects_wrong_implementation_and_config_projection(
    tmp_path: Path,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    wrong_implementation = replace(binding, implementation_root="0" * 64)
    wrong_config = replace(binding, config_projection_root="1" * 64)

    for wrong_binding, expected_code in (
        (wrong_implementation, "implementation_identity_stale"),
        (wrong_config, "cache_stage_not_admitted"),
    ):
        with pytest.raises(api.SourceBatchRejected) as exc:
            cache.acquire_lease(
                sealed.batch_root,
                expected_binding=wrong_binding,
            )
        assert exc.value.code == expected_code


def test_unknown_config_read_is_rejected() -> None:
    api = _api()
    guard = api.ConfigReadGuard(
        {"source.encoding": "utf-8"},
        known_keys={"source.encoding"},
        projection_keys={"source.encoding"},
    )

    with pytest.raises(api.ConfigReadRejected, match="unknown_config_read") as exc:
        guard["source.delimiter"]

    assert exc.value.code == "unknown_config_read"


def test_out_of_projection_config_read_is_rejected() -> None:
    api = _api()
    guard = api.ConfigReadGuard(
        {"source.encoding": "utf-8", "source.delimiter": ","},
        known_keys={"source.encoding", "source.delimiter"},
        projection_keys={"source.encoding"},
    )

    with pytest.raises(api.ConfigReadRejected, match="out_of_projection_config_read") as exc:
        guard["source.delimiter"]

    assert exc.value.code == "out_of_projection_config_read"


def test_declared_config_projection_must_equal_observed_reads() -> None:
    api = _api()
    guard = api.ConfigReadGuard(
        {"source.encoding": "utf-8", "source.delimiter": ","},
        known_keys={"source.encoding", "source.delimiter"},
        projection_keys={"source.encoding", "source.delimiter"},
    )
    guard["source.encoding"]

    with pytest.raises(api.ConfigReadRejected, match="config_read_set_mismatch") as exc:
        guard.seal_projection()

    assert exc.value.code == "config_read_set_mismatch"


def test_arm_state_config_read_is_rejected() -> None:
    api = _api()
    guard = api.ConfigReadGuard(
        {"arm.balance": 100_000},
        known_keys={"arm.balance"},
        projection_keys={"arm.balance"},
    )

    with pytest.raises(api.ConfigReadRejected, match="arm_state_read_forbidden") as exc:
        guard["arm.balance"]

    assert exc.value.code == "arm_state_read_forbidden"


def test_mutable_source_payload_is_rejected(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)

    with pytest.raises(api.SourceBatchRejected, match="mutable_payload_rejected") as exc:
        cache.seal(bytearray(CSV_PAYLOAD), binding=binding)

    assert exc.value.code == "mutable_payload_rejected"


def test_wrong_source_identity_is_rejected_before_consumption(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    wrong = replace(binding, source_identity_root="2" * 64)

    with pytest.raises(api.SourceBatchRejected) as exc:
        cache.acquire_lease(sealed.batch_root, expected_binding=wrong)

    assert exc.value.code == "source_identity_mismatch"


def test_wrong_partition_identity_is_rejected_before_consumption(
    tmp_path: Path,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    wrong = replace(binding, partition_root="3" * 64)

    with pytest.raises(api.SourceBatchRejected) as exc:
        cache.acquire_lease(sealed.batch_root, expected_binding=wrong)

    assert exc.value.code == "partition_identity_mismatch"


def test_post_seal_mutation_is_detected_and_rejected(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    payload_path = cache.payload_path(sealed.batch_root)

    with pytest.raises(PermissionError):
        payload_path.write_bytes(b"mutated")

    payload_path.chmod(0o644)
    payload_path.write_bytes(b"x" * len(CSV_PAYLOAD))
    payload_path.chmod(0o444)
    with pytest.raises(api.SourceBatchRejected) as exc:
        cache.acquire_lease(sealed.batch_root, expected_binding=binding)

    assert exc.value.code == "post_seal_payload_mutation"


def test_writable_post_seal_payload_is_rejected(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    cache.payload_path(sealed.batch_root).chmod(0o644)

    with pytest.raises(api.SourceBatchRejected, match="sealed_permissions_mutable"):
        cache.acquire_lease(sealed.batch_root, expected_binding=binding)


def test_verified_lease_rejects_post_issue_mutation(
    tmp_path: Path,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    payload_path = cache.payload_path(sealed.batch_root)

    lease = cache.acquire_lease(
        sealed.batch_root,
        expected_binding=binding,
    )
    original = timewarp.load_csv_rows(
        DEFAULT_SOURCE_PATH,
        symbol="XAUUSD",
        source_batch_lease=lease,
        source_partition=PARTITION,
    )
    payload_path.chmod(0o644)
    payload_path.write_bytes(b"x" * len(CSV_PAYLOAD))
    payload_path.chmod(0o444)
    assert len(original) == 2
    with pytest.raises(api.SourceBatchRejected, match="post_seal_payload_mutation"):
        timewarp.load_csv_rows(
            DEFAULT_SOURCE_PATH,
            symbol="XAUUSD",
            source_batch_lease=lease,
            source_partition=PARTITION,
        )

    with pytest.raises(api.SourceBatchRejected) as exc:
        cache.acquire_lease(sealed.batch_root, expected_binding=binding)
    assert exc.value.code == "post_seal_payload_mutation"


def test_lease_issuer_state_is_not_module_reachable() -> None:
    api = _api()

    for reachable_name in (
        "_LEASE_ISSUER",
        "_issue_verified_source_batch_lease",
        "_resolve_verified_source_batch_lease",
        "_build_verified_source_batch_lease_authority",
    ):
        assert reachable_name not in vars(api)


def test_direct_lease_construction_is_rejected_before_csv_parsing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    issuer = getattr(api, "_LEASE_ISSUER", object())

    def parsing_must_not_start(*args, **kwargs):
        del args, kwargs
        raise AssertionError("csv_parsing_reached")

    monkeypatch.setattr(timewarp.csv, "DictReader", parsing_must_not_start)

    with pytest.raises((TypeError, api.SourceBatchRejected)):
        forged = api.VerifiedSourceBatchLease(
            issuer,
            batch_root=sealed.batch_root,
            binding=binding,
            cache_root=cache.root,
        )
        timewarp.load_csv_rows(
            DEFAULT_SOURCE_PATH,
            symbol="XAUUSD",
            source_batch_lease=forged,
            source_partition=PARTITION,
        )


def test_unregistered_object_new_lease_is_rejected_before_csv_parsing(
    monkeypatch,
) -> None:
    api = _api()
    forged = object.__new__(api.VerifiedSourceBatchLease)

    def parsing_must_not_start(*args, **kwargs):
        del args, kwargs
        raise AssertionError("csv_parsing_reached")

    monkeypatch.setattr(timewarp.csv, "DictReader", parsing_must_not_start)

    with pytest.raises(
        api.SourceBatchRejected,
        match="source_batch_lease_not_issued",
    ):
        timewarp.load_csv_rows(
            DEFAULT_SOURCE_PATH,
            symbol="XAUUSD",
            source_batch_lease=forged,
            source_partition=PARTITION,
        )


@pytest.mark.parametrize(
    "reconstruction",
    (copy.copy, copy.deepcopy, pickle.dumps),
    ids=("shallow-copy", "deep-copy", "pickle"),
)
def test_cache_issued_lease_cannot_be_copied_or_reconstructed(
    tmp_path: Path,
    reconstruction,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    lease = cache.acquire_lease(sealed.batch_root, expected_binding=binding)

    with pytest.raises(TypeError, match="verified_source_batch_lease"):
        reconstruction(lease)


def test_lease_batch_root_rebinding_cannot_change_parsed_payload(
    tmp_path: Path,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    first = cache.seal(CSV_PAYLOAD, binding=binding)
    second_payload = CSV_PAYLOAD + (
        b"2026-01-05T09:30:00+00:00,2402,2404,2401,2403,14\n"
    )
    second = cache.seal(second_payload, binding=binding)
    lease = cache.acquire_lease(first.batch_root, expected_binding=binding)

    with pytest.raises((AttributeError, TypeError, api.SourceBatchRejected)):
        object.__setattr__(
            lease,
            "_VerifiedSourceBatchLease__batch_root",
            second.batch_root,
        )
        timewarp.load_csv_rows(
            DEFAULT_SOURCE_PATH,
            symbol="XAUUSD",
            source_batch_lease=lease,
            source_partition=PARTITION,
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "_VerifiedSourceBatchLease__batch_root",
        "_VerifiedSourceBatchLease__binding",
        "_VerifiedSourceBatchLease__cache_root",
        "_VerifiedSourceBatchLease__payload",
        "_VerifiedSourceBatchLease__manifest",
    ),
)
def test_lease_has_no_rebindable_identity_payload_or_manifest_fields(
    tmp_path: Path,
    field_name: str,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    lease = cache.acquire_lease(sealed.batch_root, expected_binding=binding)

    with pytest.raises((AttributeError, TypeError)):
        object.__setattr__(lease, field_name, object())


def test_lease_record_binding_tamper_is_detected_before_csv_parsing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    lease = cache.acquire_lease(sealed.batch_root, expected_binding=binding)
    object.__setattr__(binding, "source_identity_root", "f" * 64)

    def parsing_must_not_start(*args, **kwargs):
        del args, kwargs
        raise AssertionError("csv_parsing_reached")

    monkeypatch.setattr(timewarp.csv, "DictReader", parsing_must_not_start)

    with pytest.raises(
        api.SourceBatchRejected,
        match="source_batch_lease_not_issued",
    ):
        timewarp.load_csv_rows(
            DEFAULT_SOURCE_PATH,
            symbol="XAUUSD",
            source_batch_lease=lease,
            source_partition=PARTITION,
        )


def test_stale_lease_rejects_changed_runtime_identity_before_csv_parsing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    lease = cache.acquire_lease(sealed.batch_root, expected_binding=binding)

    def parsing_must_not_start(*args, **kwargs):
        del args, kwargs
        raise AssertionError("csv_parsing_reached")

    monkeypatch.setattr(api, "implementation_root", lambda: "0" * 64)
    monkeypatch.setattr(timewarp.csv, "DictReader", parsing_must_not_start)

    with pytest.raises(
        api.SourceBatchRejected,
        match="implementation_identity_stale",
    ):
        timewarp.load_csv_rows(
            DEFAULT_SOURCE_PATH,
            symbol="XAUUSD",
            source_batch_lease=lease,
            source_partition=PARTITION,
        )


def test_cache_root_symlink_is_rejected_before_publication(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    registry = api.CacheAdmissionRegistry()
    registry.admit(
        stage=binding.stage,
        implementation_identity_root=binding.implementation_root,
        config_projection_keys=binding.config_projection_keys,
    )
    real_root = tmp_path / "real-cache"
    real_root.mkdir()
    alias_root = tmp_path / "cache-alias"
    alias_root.symlink_to(real_root, target_is_directory=True)
    cache = api.ImmutableSourceBatchCache(alias_root, registry=registry)

    with pytest.raises(api.SourceBatchRejected, match="cache_root_symlink_forbidden"):
        cache.seal(CSV_PAYLOAD, binding=binding)

    assert list(real_root.iterdir()) == []


def test_cache_root_symlink_ancestor_is_rejected_before_publication(
    tmp_path: Path,
) -> None:
    api = _api()
    binding = _binding(api)
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    alias_parent = tmp_path / "alias-parent"
    alias_parent.symlink_to(real_parent, target_is_directory=True)
    cache = _admitted_cache(api, alias_parent, binding)

    with pytest.raises(api.SourceBatchRejected, match="cache_root_symlink_forbidden"):
        cache.seal(CSV_PAYLOAD, binding=binding)

    assert not (real_parent / "cache").exists()


def test_cache_root_create_race_with_competing_directory_retries(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache_parent = tmp_path / "race-parent"
    cache_parent.mkdir()
    cache = _admitted_cache(api, cache_parent, binding)
    real_mkdir = api.os.mkdir
    injected = False

    def competing_mkdir(path, mode=0o777, *, dir_fd=None):
        nonlocal injected
        if path == "cache" and not injected:
            injected = True
            real_mkdir(path, mode, dir_fd=dir_fd)
            raise FileExistsError("COMPETING_DIRECTORY_MARKER_MUST_NOT_ESCAPE")
        return real_mkdir(path, mode, dir_fd=dir_fd)

    monkeypatch.setattr(api.os, "mkdir", competing_mkdir)

    sealed = cache.seal(CSV_PAYLOAD, binding=binding)

    assert injected is True
    assert cache.batch_path(sealed.batch_root).is_dir()


def test_cache_root_create_race_with_symlink_swap_is_fixed_and_redacted(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache_parent = tmp_path / "race-parent"
    cache_parent.mkdir()
    attacker = tmp_path / "attacker"
    attacker.mkdir()
    cache = _admitted_cache(api, cache_parent, binding)
    real_mkdir = api.os.mkdir
    marker = "SYMLINK_CREATE_RACE_MARKER_MUST_NOT_ESCAPE"
    injected = False

    def symlink_racing_mkdir(path, mode=0o777, *, dir_fd=None):
        nonlocal injected
        if path == "cache" and not injected:
            injected = True
            os.symlink(
                attacker,
                path,
                target_is_directory=True,
                dir_fd=dir_fd,
            )
            raise FileExistsError(marker)
        return real_mkdir(path, mode, dir_fd=dir_fd)

    monkeypatch.setattr(api.os, "mkdir", symlink_racing_mkdir)

    with pytest.raises(
        api.SourceBatchRejected,
        match="cache_root_symlink_forbidden",
    ) as exc:
        cache.seal(CSV_PAYLOAD, binding=binding)

    assert injected is True
    _assert_redacted_exception(exc.value, marker)
    assert list(attacker.iterdir()) == []


def test_cache_root_create_race_with_non_directory_is_fixed_and_redacted(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache_parent = tmp_path / "race-parent"
    cache_parent.mkdir()
    cache = _admitted_cache(api, cache_parent, binding)
    real_mkdir = api.os.mkdir
    real_open = api.os.open
    marker = "NON_DIRECTORY_CREATE_RACE_MARKER_MUST_NOT_ESCAPE"
    injected = False

    def file_racing_mkdir(path, mode=0o777, *, dir_fd=None):
        nonlocal injected
        if path == "cache" and not injected:
            injected = True
            descriptor = real_open(
                path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=dir_fd,
            )
            os.close(descriptor)
            raise FileExistsError(marker)
        return real_mkdir(path, mode, dir_fd=dir_fd)

    monkeypatch.setattr(api.os, "mkdir", file_racing_mkdir)

    with pytest.raises(
        api.SourceBatchRejected,
        match="cache_root_not_directory",
    ) as exc:
        cache.seal(CSV_PAYLOAD, binding=binding)

    assert injected is True
    _assert_redacted_exception(exc.value, marker)


def test_cache_root_create_race_retry_exhaustion_is_fixed_and_redacted(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache_parent = tmp_path / "race-parent"
    cache_parent.mkdir()
    cache = _admitted_cache(api, cache_parent, binding)
    real_open = api.os.open
    real_mkdir = api.os.mkdir
    marker = "RETRY_EXHAUSTION_MARKER_MUST_NOT_ESCAPE"
    attempts = 0

    def missing_open(path, flags, *args, **kwargs):
        if path == "cache" and kwargs.get("dir_fd") is not None:
            raise FileNotFoundError(marker)
        return real_open(path, flags, *args, **kwargs)

    def losing_mkdir(path, mode=0o777, *, dir_fd=None):
        nonlocal attempts
        if path == "cache":
            attempts += 1
            raise FileExistsError(marker)
        return real_mkdir(path, mode, dir_fd=dir_fd)

    monkeypatch.setattr(api.os, "open", missing_open)
    monkeypatch.setattr(api.os, "mkdir", losing_mkdir)

    with pytest.raises(
        api.SourceBatchRejected,
        match="cache_root_create_race_exhausted",
    ) as exc:
        cache.seal(CSV_PAYLOAD, binding=binding)

    assert 1 < attempts <= 32
    _assert_redacted_exception(exc.value, marker)


def test_cache_root_swap_cannot_redirect_atomic_publication(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    cache.root.mkdir()
    held_root_path = tmp_path / "held-cache-root"
    attacker_root = tmp_path / "attacker-cache-root"
    attacker_root.mkdir()
    real_mkdir = api.os.mkdir
    swapped = False

    def swapping_mkdir(path, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if not swapped and Path(path).name.startswith(".source-batch-"):
            cache.root.rename(held_root_path)
            cache.root.symlink_to(attacker_root, target_is_directory=True)
            swapped = True
        if dir_fd is None:
            return real_mkdir(path, mode)
        return real_mkdir(path, mode, dir_fd=dir_fd)

    monkeypatch.setattr(api.os, "mkdir", swapping_mkdir)

    sealed = cache.seal(CSV_PAYLOAD, binding=binding)

    assert swapped is True
    assert (held_root_path / sealed.batch_root).is_dir()
    assert list(attacker_root.iterdir()) == []


def test_cache_ancestor_swap_cannot_redirect_atomic_publication(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    parent = tmp_path / "cache-parent"
    parent.mkdir()
    cache = _admitted_cache(api, parent, binding)
    cache.root.mkdir()
    held_parent_path = tmp_path / "held-cache-parent"
    attacker_parent = tmp_path / "attacker-parent"
    attacker_cache = attacker_parent / "cache"
    attacker_cache.mkdir(parents=True)
    real_mkdir = api.os.mkdir
    swapped = False

    def swapping_mkdir(path, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if not swapped and Path(path).name.startswith(".source-batch-"):
            parent.rename(held_parent_path)
            parent.symlink_to(attacker_parent, target_is_directory=True)
            swapped = True
        if dir_fd is None:
            return real_mkdir(path, mode)
        return real_mkdir(path, mode, dir_fd=dir_fd)

    monkeypatch.setattr(api.os, "mkdir", swapping_mkdir)

    sealed = cache.seal(CSV_PAYLOAD, binding=binding)

    assert swapped is True
    assert (held_parent_path / "cache" / sealed.batch_root).is_dir()
    assert list(attacker_cache.iterdir()) == []


def test_batch_directory_symlink_is_rejected_before_consumption(
    tmp_path: Path,
) -> None:
    api = _api()
    binding = _binding(api)
    source_cache = _admitted_cache(api, tmp_path / "source", binding)
    sealed = source_cache.seal(CSV_PAYLOAD, binding=binding)
    alias_cache = _admitted_cache(api, tmp_path / "alias", binding)
    alias_cache.root.mkdir(parents=True)
    alias_cache.batch_path(sealed.batch_root).symlink_to(
        source_cache.batch_path(sealed.batch_root),
        target_is_directory=True,
    )

    with pytest.raises(
        api.SourceBatchRejected,
        match="batch_directory_symlink_forbidden",
    ):
        alias_cache.acquire_lease(
            sealed.batch_root,
            expected_binding=binding,
        )


def test_sealed_payload_symlink_is_rejected_before_consumption(
    tmp_path: Path,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    batch_path = cache.batch_path(sealed.batch_root)
    payload_path = cache.payload_path(sealed.batch_root)
    target_path = tmp_path / "payload-target.bin"
    batch_path.chmod(0o755)
    payload_path.rename(target_path)
    payload_path.symlink_to(target_path)
    batch_path.chmod(0o555)

    with pytest.raises(api.SourceBatchRejected, match="sealed_file_unreadable"):
        cache.acquire_lease(
            sealed.batch_root,
            expected_binding=binding,
        )


@pytest.mark.parametrize("sealed_name", ("payload.bin", "manifest.json"))
def test_fifo_sealed_file_is_rejected_without_blocking(
    tmp_path: Path,
    sealed_name: str,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    batch_path = cache.batch_path(sealed.batch_root)
    target = batch_path / sealed_name
    batch_path.chmod(0o755)
    target.unlink()
    os.mkfifo(target, 0o444)
    batch_path.chmod(0o555)

    completed = None
    timed_out = False
    try:
        completed = subprocess.run(
            _worker_command(api, cache, sealed, binding),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2,
        )
    except subprocess.TimeoutExpired:
        timed_out = True
    finally:
        batch_path.chmod(0o755)
        target.unlink()

    if timed_out:
        pytest.fail(f"worker blocked opening FIFO {sealed_name}")

    assert completed is not None
    assert completed.returncode == 2
    assert completed.stderr == ""
    failure = json.loads(completed.stdout)
    assert failure["failure"]["code"] == "sealed_file_not_regular"


def test_directory_sealed_file_is_rejected_as_nonregular(
    tmp_path: Path,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    batch_path = cache.batch_path(sealed.batch_root)
    target = batch_path / "payload.bin"
    batch_path.chmod(0o755)
    target.unlink()
    target.mkdir(mode=0o555)
    batch_path.chmod(0o555)

    with pytest.raises(
        api.SourceBatchRejected,
        match="sealed_file_not_regular",
    ):
        cache.acquire_lease(sealed.batch_root, expected_binding=binding)


def test_sealed_file_inode_swap_is_rejected_before_any_read(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    batch_path = cache.batch_path(sealed.batch_root)
    payload_path = cache.payload_path(sealed.batch_root)
    replacement = tmp_path / "replacement.bin"
    replacement.write_bytes(CSV_PAYLOAD)
    replacement.chmod(0o444)
    original_inode = payload_path.stat().st_ino
    real_open = api.os.open
    swapped = False

    def swapping_open(path, flags, *args, **kwargs):
        nonlocal swapped
        if path == "payload.bin" and not swapped:
            swapped = True
            batch_path.chmod(0o755)
            os.replace(replacement, payload_path)
            batch_path.chmod(0o555)
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(api.os, "open", swapping_open)

    with pytest.raises(
        api.SourceBatchRejected,
        match="sealed_file_identity_changed",
    ):
        cache.acquire_lease(sealed.batch_root, expected_binding=binding)

    assert swapped is True
    assert payload_path.stat().st_ino != original_inode


def test_manifest_must_use_exact_canonical_bytes(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    rewritten_root = _rewrite_manifest(
        api,
        cache,
        sealed.batch_root,
        lambda manifest: None,
        canonical=False,
    )

    with pytest.raises(api.SourceBatchRejected, match="manifest_not_canonical"):
        cache.acquire_lease(rewritten_root, expected_binding=binding)


def test_malformed_manifest_drops_document_and_exception_chain(
    tmp_path: Path,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    batch_path = cache.batch_path(sealed.batch_root)
    manifest_path = batch_path / "manifest.json"
    marker = "MANIFEST_JSON_DOCUMENT_MARKER_MUST_NOT_ESCAPE"
    batch_path.chmod(0o755)
    manifest_path.chmod(0o644)
    manifest_path.write_text(
        f'{{"untrusted":"{marker}"',
        encoding="utf-8",
    )
    manifest_path.chmod(0o444)
    batch_path.chmod(0o555)

    with pytest.raises(
        api.SourceBatchRejected,
        match="manifest_unreadable",
    ) as exc:
        cache.acquire_lease(sealed.batch_root, expected_binding=binding)

    _assert_redacted_exception(exc.value, marker)


def test_stale_manifest_record_count_is_rejected(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    rewritten_root = _rewrite_manifest(
        api,
        cache,
        sealed.batch_root,
        lambda manifest: manifest.__setitem__(
            "record_count",
            int(manifest["record_count"]) + 1,
        ),
        canonical=True,
    )

    with pytest.raises(api.SourceBatchRejected, match="manifest_record_count_mismatch"):
        cache.acquire_lease(rewritten_root, expected_binding=binding)


def test_manifest_projection_keys_require_exact_list_type(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    rewritten_root = _rewrite_manifest(
        api,
        cache,
        sealed.batch_root,
        lambda manifest: manifest.__setitem__("config_projection_keys", {}),
        canonical=True,
    )

    with pytest.raises(api.SourceBatchRejected, match="manifest_schema_mismatch"):
        cache.acquire_lease(rewritten_root, expected_binding=binding)


def test_temporary_batch_directory_is_fsynced_before_publication(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    real_open = api.os.open
    real_fsync = api.os.fsync
    directory_paths_by_fd: dict[int, Path] = {}
    fsynced_directory_paths: list[Path] = []

    def tracked_open(path, flags, *args, **kwargs):
        descriptor = real_open(path, flags, *args, **kwargs)
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            directory_paths_by_fd[descriptor] = Path(path)
        return descriptor

    def tracked_fsync(descriptor):
        path = directory_paths_by_fd.get(descriptor)
        if path is not None:
            fsynced_directory_paths.append(path)
        return real_fsync(descriptor)

    monkeypatch.setattr(api.os, "open", tracked_open)
    monkeypatch.setattr(api.os, "fsync", tracked_fsync)

    cache.seal(CSV_PAYLOAD, binding=binding)

    assert any(
        path.name.startswith(".source-batch-")
        for path in fsynced_directory_paths
    )


def test_atomic_publication_has_defined_post_chmod_fsync_order(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    parent_inode = cache.root.parent.stat().st_ino
    real_fchmod = api.os.fchmod
    real_fsync = api.os.fsync
    real_rename = api.os.rename
    events: list[tuple[str, int | None, int | None]] = []

    def tracked_fchmod(descriptor, mode):
        inode = api.os.fstat(descriptor).st_ino
        result = real_fchmod(descriptor, mode)
        events.append(("fchmod", inode, mode))
        return result

    def tracked_fsync(descriptor):
        inode = api.os.fstat(descriptor).st_ino
        events.append(("fsync", inode, None))
        return real_fsync(descriptor)

    def tracked_rename(source, destination, *args, **kwargs):
        events.append(("rename", None, None))
        return real_rename(source, destination, *args, **kwargs)

    monkeypatch.setattr(api.os, "fchmod", tracked_fchmod)
    monkeypatch.setattr(api.os, "fsync", tracked_fsync)
    monkeypatch.setattr(api.os, "rename", tracked_rename)

    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    batch_path = cache.batch_path(sealed.batch_root)
    file_inodes = {
        cache.payload_path(sealed.batch_root).stat().st_ino,
        (batch_path / "manifest.json").stat().st_ino,
    }
    batch_inode = batch_path.stat().st_ino
    root_inode = cache.root.stat().st_ino

    def event_index(kind, inode=None, mode=None, *, after=-1):
        matches = [
            index
            for index, event in enumerate(events)
            if index > after
            and event[0] == kind
            and (inode is None or event[1] == inode)
            and (mode is None or event[2] == mode)
        ]
        assert matches, (kind, inode, mode, events)
        return matches[0]

    parent_fsync = event_index("fsync", parent_inode)
    for inode in file_inodes:
        chmod_index = event_index("fchmod", inode, 0o444)
        assert parent_fsync < chmod_index
        event_index("fsync", inode, after=chmod_index)
    batch_chmod = event_index("fchmod", batch_inode, 0o555)
    batch_fsync = event_index("fsync", batch_inode, after=batch_chmod)
    rename_index = event_index("rename")
    assert batch_fsync < rename_index
    event_index("fsync", root_inode, after=rename_index)


def test_malformed_worker_binding_returns_only_redacted_failure(
    tmp_path: Path,
) -> None:
    api = _api()
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(api.__file__).resolve()),
            "_consume",
            str(tmp_path / "cache"),
            "0" * 64,
            '{"stage":"replay.source_bytes.v1"}',
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert completed.returncode == 2
    assert completed.stderr == ""
    failure = json.loads(completed.stdout)
    assert set(failure) == {"counts", "equality", "failure", "roots"}
    assert set(failure["failure"]) == {"code", "partition_root", "stage"}
    assert failure["failure"]["code"] == "binding_malformed"


def test_worker_binding_identity_fields_require_exact_string_types() -> None:
    api = _api()
    raw_binding = _binding(api).as_dict()
    raw_binding["source_identity_root"] = int("1" * 64)

    with pytest.raises(api.SourceBatchRejected, match="binding_malformed") as exc:
        api.SourceBatchBinding.from_dict(raw_binding)

    assert exc.value.code == "binding_malformed"


def test_fresh_worker_recomputes_current_implementation_identity(
    tmp_path: Path,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    stale_root = "0" * 64
    rewritten_root = _rewrite_manifest(
        api,
        cache,
        sealed.batch_root,
        lambda manifest: manifest.__setitem__(
            "implementation_root",
            stale_root,
        ),
        canonical=True,
    )
    stale_binding = replace(binding, implementation_root=stale_root)

    completed = subprocess.run(
        [
            sys.executable,
            str(Path(api.__file__).resolve()),
            "_consume",
            str(cache.root),
            rewritten_root,
            json.dumps(stale_binding.as_dict(), separators=(",", ":")),
            "S0R0",
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert completed.returncode == 2
    assert completed.stderr == ""
    failure = json.loads(completed.stdout)
    assert failure["failure"]["code"] == "implementation_identity_stale"


def test_worker_wrong_arity_returns_only_redacted_failure() -> None:
    api = _api()
    completed = subprocess.run(
        [sys.executable, str(Path(api.__file__).resolve())],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert completed.returncode == 2
    assert completed.stderr == ""
    failure = json.loads(completed.stdout)
    assert failure["failure"]["code"] == "binding_malformed"


def test_fresh_process_timeout_is_redacted(tmp_path: Path, monkeypatch) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)

    def timeout(*args, **kwargs):
        del args, kwargs
        raise subprocess.TimeoutExpired(cmd="redacted", timeout=30)

    monkeypatch.setattr(api.subprocess, "run", timeout)

    with pytest.raises(api.SourceBatchRejected) as exc:
        api.consume_in_fresh_processes(
            cache_root=cache.root,
            batch_root=sealed.batch_root,
            expected_binding=binding,
            arm_execution_order=tuple(sorted(api.FACTORIAL_ARMS)),
        )
    assert exc.value.code == "fresh_process_consumption_failed"
    assert set(exc.value.structural_output()["failure"]) == {
        "code",
        "partition_root",
        "stage",
    }


def test_fresh_process_receipt_schema_is_fail_closed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    overbroad_receipt = {
        "roots": {
            "batch": sealed.batch_root,
            "payload": sealed.payload_root,
            "implementation": binding.implementation_root,
            "source_identity": binding.source_identity_root,
            "config_projection": binding.config_projection_root,
            "partition": binding.partition_root,
            "unexpected": "must-not-escape",
        },
        "counts": {"bytes": len(CSV_PAYLOAD), "records": 2},
    }

    def overbroad(*args, **kwargs):
        del args, kwargs
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(overbroad_receipt),
            stderr="",
        )

    monkeypatch.setattr(api.subprocess, "run", overbroad)

    with pytest.raises(api.SourceBatchRejected) as exc:
        api.consume_in_fresh_processes(
            cache_root=cache.root,
            batch_root=sealed.batch_root,
            expected_binding=binding,
            arm_execution_order=tuple(sorted(api.FACTORIAL_ARMS)),
        )
    assert exc.value.code == "fresh_process_consumption_failed"
    assert "must-not-escape" not in json.dumps(exc.value.structural_output())


def test_fresh_process_receipt_must_equal_parent_verified_manifest(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    forged_receipt = {
        "roots": {
            "batch": sealed.batch_root,
            "payload": "f" * 64,
            "implementation": binding.implementation_root,
            "source_identity": binding.source_identity_root,
            "config_projection": binding.config_projection_root,
            "partition": binding.partition_root,
        },
        "counts": {"bytes": 0, "records": 0},
    }

    def forged(*args, **kwargs):
        del args, kwargs
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(forged_receipt),
            stderr="",
        )

    monkeypatch.setattr(api.subprocess, "run", forged)

    with pytest.raises(
        api.SourceBatchRejected,
        match="fresh_process_consumption_failed",
    ):
        api.consume_in_fresh_processes(
            cache_root=cache.root,
            batch_root=sealed.batch_root,
            expected_binding=binding,
            arm_execution_order=tuple(sorted(api.FACTORIAL_ARMS)),
        )


def test_complete_arm_proof_rejects_one_missing_attestation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    manifest = cache._verify_batch(
        sealed.batch_root,
        expected_binding=binding,
    )

    def one_missing_attestation(command, *args, **kwargs):
        del args, kwargs
        arm_id = command[-1]
        receipt = api._structural_process_receipt(
            manifest=manifest,
            batch_root=sealed.batch_root,
            arm_id=arm_id,
        )
        if arm_id == "S0R1":
            del receipt["arm"]["attestation_root"]
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=json.dumps(receipt),
            stderr="",
        )

    monkeypatch.setattr(api.subprocess, "run", one_missing_attestation)

    with pytest.raises(
        api.SourceBatchRejected,
        match="fresh_process_consumption_failed",
    ):
        api.consume_in_fresh_processes(
            cache_root=cache.root,
            batch_root=sealed.batch_root,
            expected_binding=binding,
            arm_execution_order=tuple(sorted(api.FACTORIAL_ARMS)),
        )


def test_untrusted_fresh_process_failure_code_is_redacted(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)

    def untrusted_failure(*args, **kwargs):
        del args, kwargs
        return subprocess.CompletedProcess(
            args=[],
            returncode=2,
            stdout=json.dumps({"failure": {"code": "must-not-escape"}}),
            stderr="",
        )

    monkeypatch.setattr(api.subprocess, "run", untrusted_failure)

    with pytest.raises(api.SourceBatchRejected) as exc:
        api.consume_in_fresh_processes(
            cache_root=cache.root,
            batch_root=sealed.batch_root,
            expected_binding=binding,
            arm_execution_order=tuple(sorted(api.FACTORIAL_ARMS)),
        )
    assert exc.value.code == "fresh_process_consumption_failed"
    assert "must-not-escape" not in json.dumps(exc.value.structural_output())


def test_fresh_process_launch_error_is_redacted(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)

    def launch_error(*args, **kwargs):
        del args, kwargs
        raise OSError("must-not-escape")

    monkeypatch.setattr(api.subprocess, "run", launch_error)

    with pytest.raises(api.SourceBatchRejected) as exc:
        api.consume_in_fresh_processes(
            cache_root=cache.root,
            batch_root=sealed.batch_root,
            expected_binding=binding,
            arm_execution_order=tuple(sorted(api.FACTORIAL_ARMS)),
        )
    assert exc.value.code == "fresh_process_consumption_failed"
    assert "must-not-escape" not in json.dumps(exc.value.structural_output())


def test_fresh_process_launch_error_drops_untrusted_exception_chain(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    marker = "LAUNCH_CHAIN_MARKER_MUST_NOT_ESCAPE"

    def launch_error(*args, **kwargs):
        del args, kwargs
        raise OSError(marker)

    monkeypatch.setattr(api.subprocess, "run", launch_error)

    with pytest.raises(api.SourceBatchRejected) as exc:
        api.consume_in_fresh_processes(
            cache_root=cache.root,
            batch_root=sealed.batch_root,
            expected_binding=binding,
            arm_execution_order=tuple(sorted(api.FACTORIAL_ARMS)),
        )

    assert exc.value.code == "fresh_process_consumption_failed"
    _assert_redacted_exception(exc.value, marker)


def test_malformed_child_json_drops_document_and_exception_chain(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    marker = "CHILD_JSON_DOCUMENT_MARKER_MUST_NOT_ESCAPE"

    def malformed_child(*args, **kwargs):
        del args, kwargs
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=f'{{"untrusted":"{marker}"',
            stderr="",
        )

    monkeypatch.setattr(api.subprocess, "run", malformed_child)

    with pytest.raises(api.SourceBatchRejected) as exc:
        api.consume_in_fresh_processes(
            cache_root=cache.root,
            batch_root=sealed.batch_root,
            expected_binding=binding,
            arm_execution_order=tuple(sorted(api.FACTORIAL_ARMS)),
        )

    assert exc.value.code == "fresh_process_consumption_failed"
    _assert_redacted_exception(exc.value, marker)


def test_batch_root_path_traversal_is_rejected(tmp_path: Path) -> None:
    api = _api()
    cache = api.ImmutableSourceBatchCache(tmp_path / "cache")

    with pytest.raises(api.SourceBatchRejected, match="invalid_batch_root"):
        cache.batch_path("../outside")


def test_non_string_batch_root_is_rejected(tmp_path: Path) -> None:
    api = _api()
    cache = api.ImmutableSourceBatchCache(tmp_path / "cache")

    with pytest.raises(api.SourceBatchRejected, match="invalid_batch_root"):
        cache.batch_path(None)


def test_sealed_batch_rejects_undeclared_entries(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    batch_path = cache.batch_path(sealed.batch_root)
    batch_path.chmod(0o755)
    (batch_path / "unexpected.bin").write_bytes(b"unexpected")
    batch_path.chmod(0o555)

    with pytest.raises(
        api.SourceBatchRejected,
        match="batch_directory_schema_mismatch",
    ):
        cache.acquire_lease(
            sealed.batch_root,
            expected_binding=binding,
        )


def test_two_fresh_processes_cannot_claim_complete_equality_proof(
    tmp_path: Path,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)

    with pytest.raises(
        api.SourceBatchRejected,
        match="complete_arm_set_required",
    ):
        api.consume_in_fresh_processes(
            cache_root=cache.root,
            batch_root=sealed.batch_root,
            expected_binding=binding,
            arm_execution_order=("S0R0", "S1R0"),
        )


@pytest.mark.parametrize(
    "arm_execution_order",
    (
        ("S0R0",),
        ("S0R0", "S1R0"),
        ("S0R0", "S1R0", "S0R1"),
        ("S0R0", "S1R0", "S0R1", "S0R0"),
        ("S0R0", "S1R0", "S0R1", "UNKNOWN"),
        (),
    ),
    ids=(
        "one-arm-subset",
        "two-arm-subset",
        "three-arm-subset",
        "duplicate-arm",
        "unknown-arm",
        "empty-set",
    ),
)
def test_incomplete_or_invalid_arm_set_cannot_produce_equality_proof(
    tmp_path: Path,
    arm_execution_order: tuple[str, ...],
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)

    with pytest.raises(
        api.SourceBatchRejected,
        match="complete_arm_set_required",
    ) as exc:
        api.consume_in_fresh_processes(
            cache_root=cache.root,
            batch_root=sealed.batch_root,
            expected_binding=binding,
            arm_execution_order=arm_execution_order,
        )

    assert exc.value.structural_output()["equality"] is False


def test_fresh_worker_attests_the_requested_arm(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)

    completed = subprocess.run(
        [
            sys.executable,
            str(Path(api.__file__).resolve()),
            "_consume",
            str(cache.root),
            sealed.batch_root,
            json.dumps(binding.as_dict(), separators=(",", ":")),
            "S1R0",
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stderr == ""
    receipt = json.loads(completed.stdout)
    assert receipt["arm"]["id"] == "S1R0"
    assert len(receipt["arm"]["attestation_root"]) == 64


def test_structural_outputs_and_failures_are_redacted(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    wrong = replace(binding, source_identity_root="4" * 64)

    with pytest.raises(api.SourceBatchRejected) as exc:
        cache.acquire_lease(sealed.batch_root, expected_binding=wrong)
    failure = exc.value.structural_output()

    assert set(failure) == {"counts", "equality", "failure", "roots"}
    assert set(failure["failure"]) == {"code", "partition_root", "stage"}
    assert failure["counts"] == {"failures": 1}
    assert failure["roots"] == {}
    assert SOURCE_IDENTITY not in json.dumps(failure, sort_keys=True)


def test_failure_location_rejects_caller_controlled_marker_values() -> None:
    api = _api()
    marker = "CALLER_MARKER_MUST_NOT_ESCAPE"

    rejected = api.SourceBatchRejected(
        "invalid_input",
        stage=marker,
        partition_root=marker,
    )
    structural = rejected.structural_output()
    encoded = json.dumps(structural, sort_keys=True)

    assert rejected.stage == api.SOURCE_BYTES_STAGE
    assert rejected.partition_root != marker
    assert len(rejected.partition_root) == 64
    assert structural["failure"]["stage"] == api.SOURCE_BYTES_STAGE
    assert marker not in encoded


def test_arm_execution_order_permutations_have_identical_structural_output(
    tmp_path: Path,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)

    canonical = api.consume_in_fresh_processes(
        cache_root=cache.root,
        batch_root=sealed.batch_root,
        expected_binding=binding,
        arm_execution_order=("S0R0", "S1R0", "S0R1", "S1R1"),
    )
    permuted = api.consume_in_fresh_processes(
        cache_root=cache.root,
        batch_root=sealed.batch_root,
        expected_binding=binding,
        arm_execution_order=("S1R1", "S0R1", "S1R0", "S0R0"),
    )

    assert canonical == permuted


def test_all_four_arm_execution_order_permutations_are_identical(
    tmp_path: Path,
) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    outputs = [
        api.consume_in_fresh_processes(
            cache_root=cache.root,
            batch_root=sealed.batch_root,
            expected_binding=binding,
            arm_execution_order=order,
        )
        for order in permutations(sorted(api.FACTORIAL_ARMS))
    ]

    assert all(output == outputs[0] for output in outputs[1:])
    attestations = outputs[0]["roots"]["arm_attestations"]
    assert set(attestations) == api.FACTORIAL_ARMS
    assert all(len(root) == 64 for root in attestations.values())
    assert outputs[0]["counts"]["processes"] == 4


def test_tiny_fixture_cold_warm_microbenchmark_is_structural(tmp_path: Path) -> None:
    api = _api()
    binding = _binding(api)
    cache = _admitted_cache(api, tmp_path, binding)

    measurement = api.measure_tiny_fixture_cold_warm(
        cache=cache,
        payload=CSV_PAYLOAD,
        binding=binding,
    )

    assert measurement["label"] == "tiny_fixture_microbenchmark_not_replay_speed_claim"
    assert measurement["cache_hits"] == {"cold": False, "warm": True}
    assert measurement["counts"] == {"bytes": len(CSV_PAYLOAD), "records": 2}
    assert measurement["timings_seconds"]["cold"] >= 0.0
    assert measurement["timings_seconds"]["warm"] >= 0.0
    assert set(measurement["roots"]) == {"batch", "payload"}


def test_existing_replay_csv_consumer_accepts_cache_issued_lease(
    tmp_path: Path,
) -> None:
    api = _api()
    source_path = tmp_path / "XAUUSD_M15.csv"
    source_path.write_bytes(CSV_PAYLOAD)
    binding = _binding(api, source_path=source_path)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal_source_file(source_path, binding=binding)
    legacy = timewarp.load_csv_rows(source_path, symbol="XAUUSD")
    lease = cache.acquire_lease(
        sealed.batch_root,
        expected_binding=binding,
    )
    accelerated = timewarp.load_csv_rows(
        source_path,
        symbol="XAUUSD",
        source_batch_lease=lease,
        source_partition=PARTITION,
    )

    assert accelerated == legacy


def test_existing_source_producer_is_sealed_by_bound_cache_api(
    tmp_path: Path,
) -> None:
    api = _api()
    source_path = tmp_path / "XAUUSD_M15.csv"
    source_path.write_bytes(CSV_PAYLOAD)
    binding = _binding(api, source_path=source_path)
    cache = _admitted_cache(api, tmp_path, binding)

    sealed = cache.seal_source_file(source_path, binding=binding)
    lease = cache.acquire_lease(
        sealed.batch_root,
        expected_binding=binding,
    )
    accelerated = timewarp.load_csv_rows(
        source_path,
        symbol="XAUUSD",
        source_batch_lease=lease,
        source_partition=PARTITION,
    )

    assert len(accelerated) == 2
    assert sealed.payload_root == hashlib.sha256(CSV_PAYLOAD).hexdigest()


def test_bound_source_producer_rejects_symlink_and_nonregular_inputs(
    tmp_path: Path,
) -> None:
    api = _api()
    real_parent = tmp_path / "real-source-parent"
    real_parent.mkdir()
    real_source = real_parent / "source.csv"
    real_source.write_bytes(CSV_PAYLOAD)
    alias_parent = tmp_path / "source-alias"
    alias_parent.symlink_to(real_parent, target_is_directory=True)
    alias_source = alias_parent / "source.csv"
    alias_binding = _binding(api, source_path=alias_source)
    alias_cache = _admitted_cache(api, tmp_path / "alias-cache", alias_binding)

    with pytest.raises(api.SourceBatchRejected, match="source_path_symlink_forbidden"):
        alias_cache.seal_source_file(alias_source, binding=alias_binding)

    directory_binding = _binding(api, source_path=real_parent)
    directory_cache = _admitted_cache(
        api,
        tmp_path / "directory-cache",
        directory_binding,
    )
    with pytest.raises(api.SourceBatchRejected, match="source_file_not_regular"):
        directory_cache.seal_source_file(real_parent, binding=directory_binding)


def test_missing_source_path_drops_untrusted_os_exception_chain(
    tmp_path: Path,
) -> None:
    api = _api()
    marker = "SOURCE_PATH_MARKER_MUST_NOT_ESCAPE"
    source_path = tmp_path / f"{marker}.csv"
    binding = _binding(api, source_path=source_path)
    cache = _admitted_cache(api, tmp_path, binding)

    with pytest.raises(
        api.SourceBatchRejected,
        match="source_path_missing",
    ) as exc:
        cache.seal_source_file(source_path, binding=binding)

    _assert_redacted_exception(exc.value, marker)


def test_existing_replay_csv_consumer_rejects_public_raw_bytes(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "XAUUSD_M15.csv"
    source_path.write_bytes(CSV_PAYLOAD)

    with pytest.raises(TypeError):
        timewarp.load_csv_rows(
            source_path,
            symbol="XAUUSD",
            immutable_source_bytes=CSV_PAYLOAD,
        )
    with pytest.raises(TypeError, match="verified_source_batch_lease_required"):
        timewarp.load_csv_rows(
            source_path,
            symbol="XAUUSD",
            source_batch_lease=memoryview(CSV_PAYLOAD),
            source_partition=PARTITION,
        )


def test_cache_has_no_public_raw_view_api(tmp_path: Path) -> None:
    api = _api()
    cache = api.ImmutableSourceBatchCache(tmp_path / "cache")

    with pytest.raises(AttributeError):
        cache.open_readonly("0" * 64, expected_binding=object())


def test_cache_issued_lease_is_bound_before_csv_parsing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    source_path = tmp_path / "XAUUSD_M15.csv"
    wrong_source_path = tmp_path / "other.csv"
    source_path.write_bytes(CSV_PAYLOAD)
    wrong_source_path.write_bytes(CSV_PAYLOAD)
    binding = _binding(api, source_path=source_path)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    lease = cache.acquire_lease(
        sealed.batch_root,
        expected_binding=binding,
    )
    legacy = timewarp.load_csv_rows(source_path, symbol="XAUUSD")
    accelerated = timewarp.load_csv_rows(
        source_path,
        symbol="XAUUSD",
        source_batch_lease=lease,
        source_partition=PARTITION,
    )
    assert accelerated == legacy

    def parsing_must_not_start(*args, **kwargs):
        del args, kwargs
        raise AssertionError("csv_parsing_reached")

    monkeypatch.setattr(timewarp.csv, "DictReader", parsing_must_not_start)
    wrong_partition = {**PARTITION, "date": "2026-01-06"}
    for path, symbol, partition, expected_code in (
        (
            wrong_source_path,
            "XAUUSD",
            PARTITION,
            "source_path_identity_mismatch",
        ),
        (source_path, "EURUSD", PARTITION, "partition_symbol_mismatch"),
        (
            source_path,
            "XAUUSD",
            wrong_partition,
            "partition_identity_mismatch",
        ),
    ):
        with pytest.raises(api.SourceBatchRejected) as exc:
            timewarp.load_csv_rows(
                path,
                symbol=symbol,
                source_batch_lease=lease,
                source_partition=partition,
            )
        assert exc.value.code == expected_code


def test_partition_canonicalization_failure_drops_exception_chain_before_parse(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    source_path = tmp_path / "XAUUSD_M15.csv"
    source_path.write_bytes(CSV_PAYLOAD)
    binding = _binding(api, source_path=source_path)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal_source_file(source_path, binding=binding)
    lease = cache.acquire_lease(sealed.batch_root, expected_binding=binding)
    marker = "PARTITION_CANONICALIZATION_MARKER_MUST_NOT_ESCAPE"

    class PARTITION_CANONICALIZATION_MARKER_MUST_NOT_ESCAPE:
        pass

    def parsing_must_not_start(*args, **kwargs):
        del args, kwargs
        raise AssertionError("csv_parsing_reached")

    monkeypatch.setattr(timewarp.csv, "DictReader", parsing_must_not_start)

    with pytest.raises(
        api.SourceBatchRejected,
        match="partition_identity_mismatch",
    ) as exc:
        timewarp.load_csv_rows(
            source_path,
            symbol="XAUUSD",
            source_batch_lease=lease,
            source_partition={
                **PARTITION,
                "untrusted": PARTITION_CANONICALIZATION_MARKER_MUST_NOT_ESCAPE(),
            },
        )

    _assert_redacted_exception(exc.value, marker)


def test_cache_issued_lease_reverifies_before_each_parse(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = _api()
    source_path = tmp_path / "XAUUSD_M15.csv"
    source_path.write_bytes(CSV_PAYLOAD)
    binding = _binding(api, source_path=source_path)
    cache = _admitted_cache(api, tmp_path, binding)
    sealed = cache.seal(CSV_PAYLOAD, binding=binding)
    lease = cache.acquire_lease(
        sealed.batch_root,
        expected_binding=binding,
    )
    payload_path = cache.payload_path(sealed.batch_root)
    payload_path.chmod(0o644)
    payload_path.write_bytes(b"x" * len(CSV_PAYLOAD))
    payload_path.chmod(0o444)

    def parsing_must_not_start(*args, **kwargs):
        del args, kwargs
        raise AssertionError("csv_parsing_reached")

    monkeypatch.setattr(timewarp.csv, "DictReader", parsing_must_not_start)

    with pytest.raises(api.SourceBatchRejected, match="post_seal_payload_mutation"):
        timewarp.load_csv_rows(
            source_path,
            symbol="XAUUSD",
            source_batch_lease=lease,
            source_partition=PARTITION,
        )


def test_existing_replay_csv_consumer_default_path_is_unchanged(tmp_path: Path) -> None:
    source_path = tmp_path / "XAUUSD_M15.csv"
    source_path.write_bytes(CSV_PAYLOAD)

    assert timewarp.load_csv_rows(source_path, symbol="XAUUSD") == (
        {
            "time": "2026-01-05T09:00:00+00:00",
            "time_utc": "2026-01-05T09:00:00+00:00",
            "symbol": "XAUUSD",
            "open": 2400.0,
            "high": 2402.0,
            "low": 2399.0,
            "close": 2401.0,
            "volume": 10.0,
        },
        {
            "time": "2026-01-05T09:15:00+00:00",
            "time_utc": "2026-01-05T09:15:00+00:00",
            "symbol": "XAUUSD",
            "open": 2401.0,
            "high": 2403.0,
            "low": 2400.0,
            "close": 2402.0,
            "volume": 12.0,
        },
    )

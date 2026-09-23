from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.research_infra.replay_acceleration_partial_golden import (
    build_partial_golden_manifest,
    write_partial_golden_manifest,
)
from src.research_infra.replay_acceleration_partial_golden_verifier import (
    verify_partial_golden_manifest,
)
from tests.test_replay_acceleration_partial_golden import (
    _fixture as _partial_golden_fixture,
)
from src.research_infra.replay_acceleration_partial_golden_postseal import (
    PostSealAmendmentError,
    build_postseal_namespace_amendment,
    write_postseal_amendment,
)
from src.research_infra.replay_acceleration_partial_golden_postseal_verifier import (
    PostSealAmendmentVerificationError,
    verify_postseal_namespace_amendment,
)


ROOT = Path(__file__).resolve().parents[1]
TOMBSTONE_SCHEMA = (
    "gtos.final_moonshot.broad_live_as_if_replay_harness."
    "interrupted_summary.v1"
)
TOMBSTONE_STATUS = "interrupted_partial_not_final_proof"
TOMBSTONE_SEMANTICS = (
    "parseable tombstone generated from the last completed chunk; "
    "not a completed broad replay proof"
)


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _root(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _write(path: Path, value: object) -> None:
    path.write_bytes(_canonical(value))


def _reroot_blocker(value: dict[str, object]) -> None:
    projection = dict(value)
    projection.pop("receipt_root_sha256", None)
    value["receipt_root_sha256"] = hashlib.sha256(
        _canonical(projection)[:-1]
    ).hexdigest()


def _reroot(value: dict[str, object], field: str) -> None:
    projection = dict(value)
    projection.pop(field, None)
    value[field] = _root(projection)


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path, str]:
    namespace = tmp_path / "legacy"
    namespace.mkdir()
    namespace, prefix, commit = _partial_golden_fixture(namespace)
    manifest_core = build_partial_golden_manifest(
        namespace=namespace,
        output_prefix=prefix,
        start_day="2026-01-01",
        end_day="2026-01-07",
        legacy_code_commit=commit,
        git_root=ROOT,
        sealed_at_utc="2026-07-19T00:00:00Z",
    )
    manifest_path = tmp_path / "manifest.json"
    write_partial_golden_manifest(manifest_path, manifest_core)
    surfaces = manifest_core["persisted_result_surfaces"]

    ledger_bytes = {
        "bucket": None,
        "candidate": None,
        "candidate_index": None,
        "comparison": None,
        "decision": None,
        "missed": None,
        "oracle": None,
        "order": None,
        "packet_sidecar": None,
        "scorecard": None,
        "source": surfaces[0]["bytes"],
        "summary": None,
        "trade": surfaces[1]["bytes"],
    }
    tombstone = {
        "schema": TOMBSTONE_SCHEMA,
        "status": TOMBSTONE_STATUS,
        "interrupted_run": True,
        "generated_at_utc": "2026-07-19T00:08:42+00:00",
        "last_completed_end_day": "2026-01-07",
        "interrupted_summary_semantics": TOMBSTONE_SEMANTICS,
        "ledger_file_bytes_at_interrupt": ledger_bytes,
    }
    tombstone_path = namespace / f"{prefix}_SUMMARY.json"
    _write(tombstone_path, tombstone)

    blocker_core: dict[str, object] = {
        "schema": (
            "gtos.replay_acceleration."
            "post_recovery_legacy_namespace_mismatch_blocker.v1"
        ),
        "route_verdict": "HUMAN_OR_EXTERNAL_BLOCKER",
        "authority_state": {
            "manifest_self_root_sha256": manifest_core[
                "manifest_self_root_sha256"
            ],
            "golden_root_sha256": manifest_core["golden_root_sha256"],
            "opaque_result_surface_root_sha256": manifest_core[
                "opaque_result_surface_root_sha256"
            ],
        },
        "namespace_mismatch": {
            "expected_file_count": 3,
            "observed_file_count": 4,
            "missing_file_count": 0,
            "unexpected_file_count": 1,
            "unexpected_file": {
                "filename": tombstone_path.name,
                "bytes": tombstone_path.stat().st_size,
                "sha256": hashlib.sha256(tombstone_path.read_bytes()).hexdigest(),
            },
        },
        "economic_values_exposed": False,
        "outcome_blindness_preserved": True,
    }
    compact = json.dumps(
        blocker_core,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    blocker_core["receipt_root_sha256"] = hashlib.sha256(compact).hexdigest()
    blocker_path = tmp_path / "blocker.json"
    blocker_path.write_text(json.dumps(blocker_core, indent=2, sort_keys=True) + "\n")
    amendment_path = tmp_path / "amendment.json"
    return namespace, manifest_path, blocker_path, amendment_path, prefix


def _build_and_write(
    manifest_path: Path, blocker_path: Path, amendment_path: Path
) -> dict[str, object]:
    amendment = build_postseal_namespace_amendment(
        manifest_path=manifest_path,
        blocker_receipt_path=blocker_path,
    )
    write_postseal_amendment(amendment_path, amendment)
    return amendment


def test_postseal_fixture_uses_independently_accepted_upstream_manifest(
    tmp_path: Path,
) -> None:
    _namespace, manifest, _blocker, _amendment_path, prefix = _fixture(
        tmp_path
    )

    receipt = verify_partial_golden_manifest(
        manifest,
        git_root=ROOT,
        allowed_namespace_additions=(f"{prefix}_SUMMARY.json",),
    )

    assert receipt["gate"] == "PARTIAL_GOLDEN_INDEPENDENTLY_ACCEPTED"


def test_postseal_builder_rejects_manifest_not_accepted_upstream(
    tmp_path: Path,
) -> None:
    _namespace, manifest_path, blocker_path, _amendment_path, _prefix = (
        _fixture(tmp_path)
    )
    manifest = json.loads(manifest_path.read_bytes())
    manifest["authority_update"] = {"ending_equity": 1}
    _reroot(manifest, "manifest_self_root_sha256")
    _write(manifest_path, manifest)
    blocker = json.loads(blocker_path.read_bytes())
    blocker["authority_state"]["manifest_self_root_sha256"] = manifest[
        "manifest_self_root_sha256"
    ]
    _reroot_blocker(blocker)
    blocker_path.write_text(json.dumps(blocker, indent=2, sort_keys=True) + "\n")

    with pytest.raises(
        PostSealAmendmentError,
        match="manifest_independent_verification_failed",
    ):
        build_postseal_namespace_amendment(
            manifest_path=manifest_path,
            blocker_receipt_path=blocker_path,
        )


def test_postseal_verifier_rejects_manifest_not_accepted_upstream(
    tmp_path: Path,
) -> None:
    _namespace, manifest_path, blocker_path, amendment_path, _prefix = _fixture(
        tmp_path
    )
    amendment = _build_and_write(manifest_path, blocker_path, amendment_path)
    manifest = json.loads(manifest_path.read_bytes())
    manifest["authority_update"] = {"ending_equity": 1}
    _reroot(manifest, "manifest_self_root_sha256")
    _write(manifest_path, manifest)
    blocker = json.loads(blocker_path.read_bytes())
    blocker["authority_state"]["manifest_self_root_sha256"] = manifest[
        "manifest_self_root_sha256"
    ]
    _reroot_blocker(blocker)
    blocker_path.write_text(json.dumps(blocker, indent=2, sort_keys=True) + "\n")
    amendment["original_golden"]["manifest_self_root_sha256"] = manifest[
        "manifest_self_root_sha256"
    ]
    amendment["blocker_binding"]["receipt_root_sha256"] = blocker[
        "receipt_root_sha256"
    ]
    _reroot(amendment, "amendment_self_root_sha256")
    _write(amendment_path, amendment)

    with pytest.raises(
        PostSealAmendmentVerificationError,
        match="manifest_independent_verification_failed",
    ):
        verify_postseal_namespace_amendment(
            amendment_path=amendment_path,
            manifest_path=manifest_path,
            blocker_receipt_path=blocker_path,
        )


def test_exact_bound_tombstone_is_accepted(tmp_path: Path) -> None:
    namespace, manifest, blocker, amendment_path, _prefix = _fixture(tmp_path)
    amendment = _build_and_write(manifest, blocker, amendment_path)

    receipt = verify_postseal_namespace_amendment(
        amendment_path=amendment_path,
        manifest_path=manifest,
        blocker_receipt_path=blocker,
    )

    assert amendment["original_golden"]["inventory_exact_at_seal"] is True
    assert receipt["gate"] == "POST_SEAL_NAMESPACE_AMENDMENT_INDEPENDENTLY_ACCEPTED"
    assert receipt["current_namespace_file_count"] == 4
    assert receipt["economic_values_exposed"] is False
    assert namespace.is_dir()


def test_changed_sealed_file_fails_closed(tmp_path: Path) -> None:
    namespace, manifest, blocker, amendment_path, prefix = _fixture(tmp_path)
    _build_and_write(manifest, blocker, amendment_path)
    target = namespace / f"{prefix}_TRADE_LEDGER.jsonl"
    changed = bytearray(target.read_bytes())
    changed[5] ^= 1
    target.write_bytes(changed)

    with pytest.raises(
        PostSealAmendmentVerificationError,
        match="manifest_independent_verification_failed",
    ):
        verify_postseal_namespace_amendment(
            amendment_path=amendment_path,
            manifest_path=manifest,
            blocker_receipt_path=blocker,
        )


def test_changed_tombstone_bytes_fail_closed(tmp_path: Path) -> None:
    namespace, manifest, blocker, amendment_path, prefix = _fixture(tmp_path)
    _build_and_write(manifest, blocker, amendment_path)
    target = namespace / f"{prefix}_SUMMARY.json"
    changed = bytearray(target.read_bytes())
    changed[-2] ^= 1
    target.write_bytes(changed)

    with pytest.raises(
        PostSealAmendmentVerificationError, match="tombstone_hash_mismatch"
    ):
        verify_postseal_namespace_amendment(
            amendment_path=amendment_path,
            manifest_path=manifest,
            blocker_receipt_path=blocker,
        )


def test_missing_original_file_fails_closed(tmp_path: Path) -> None:
    namespace, manifest, blocker, amendment_path, prefix = _fixture(tmp_path)
    _build_and_write(manifest, blocker, amendment_path)
    (namespace / f"{prefix}_SOURCE_UNIVERSE_LEDGER.jsonl").unlink()

    with pytest.raises(
        PostSealAmendmentVerificationError,
        match="manifest_independent_verification_failed",
    ):
        verify_postseal_namespace_amendment(
            amendment_path=amendment_path,
            manifest_path=manifest,
            blocker_receipt_path=blocker,
        )


def test_second_prefix_scoped_addition_fails_closed(tmp_path: Path) -> None:
    namespace, manifest, blocker, amendment_path, prefix = _fixture(tmp_path)
    _build_and_write(manifest, blocker, amendment_path)
    (namespace / f"{prefix}_UNBOUND.json").write_bytes(b"{}\n")

    with pytest.raises(
        PostSealAmendmentVerificationError,
        match="manifest_independent_verification_failed",
    ):
        verify_postseal_namespace_amendment(
            amendment_path=amendment_path,
            manifest_path=manifest,
            blocker_receipt_path=blocker,
        )


def test_amendment_metadata_drift_fails_even_when_rerooted(tmp_path: Path) -> None:
    _namespace, manifest, blocker, amendment_path, _prefix = _fixture(tmp_path)
    amendment = _build_and_write(manifest, blocker, amendment_path)
    amendment["derivative_tombstone"]["generated_at_utc"] = (
        "2026-07-19T00:08:43+00:00"
    )
    _reroot(amendment, "amendment_self_root_sha256")
    _write(amendment_path, amendment)

    with pytest.raises(
        PostSealAmendmentVerificationError,
        match="amendment_tombstone_metadata_mismatch",
    ):
        verify_postseal_namespace_amendment(
            amendment_path=amendment_path,
            manifest_path=manifest,
            blocker_receipt_path=blocker,
        )


def test_amendment_role_bytes_drift_fails_even_when_rerooted(tmp_path: Path) -> None:
    _namespace, manifest, blocker, amendment_path, _prefix = _fixture(tmp_path)
    amendment = _build_and_write(manifest, blocker, amendment_path)
    amendment["derivative_tombstone"]["role_bytes"]["source"] += 1
    _reroot(amendment, "amendment_self_root_sha256")
    _write(amendment_path, amendment)

    with pytest.raises(
        PostSealAmendmentVerificationError,
        match="amendment_role_bytes_mismatch",
    ):
        verify_postseal_namespace_amendment(
            amendment_path=amendment_path,
            manifest_path=manifest,
            blocker_receipt_path=blocker,
        )


def test_postseal_verifier_rejects_unknown_structural_field(
    tmp_path: Path,
) -> None:
    _namespace, manifest, blocker, amendment_path, _prefix = _fixture(tmp_path)
    amendment = _build_and_write(manifest, blocker, amendment_path)
    amendment["unreviewed_metadata"] = {"value": 1}
    _reroot(amendment, "amendment_self_root_sha256")
    _write(amendment_path, amendment)

    with pytest.raises(
        PostSealAmendmentVerificationError,
        match="amendment_unknown_fields",
    ):
        verify_postseal_namespace_amendment(
            amendment_path=amendment_path,
            manifest_path=manifest,
            blocker_receipt_path=blocker,
        )


def test_builder_rejects_role_byte_mismatch(tmp_path: Path) -> None:
    namespace, manifest, blocker, _amendment_path, prefix = _fixture(tmp_path)
    tombstone_path = namespace / f"{prefix}_SUMMARY.json"
    tombstone = json.loads(tombstone_path.read_text())
    tombstone["ledger_file_bytes_at_interrupt"]["source"] += 1
    _write(tombstone_path, tombstone)
    blocker_value = json.loads(blocker.read_text())
    blocker_value["namespace_mismatch"]["unexpected_file"]["bytes"] = (
        tombstone_path.stat().st_size
    )
    blocker_value["namespace_mismatch"]["unexpected_file"]["sha256"] = (
        hashlib.sha256(tombstone_path.read_bytes()).hexdigest()
    )
    projection = dict(blocker_value)
    projection.pop("receipt_root_sha256")
    blocker_value["receipt_root_sha256"] = hashlib.sha256(
        json.dumps(
            projection,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    blocker.write_text(json.dumps(blocker_value, indent=2, sort_keys=True) + "\n")

    with pytest.raises(PostSealAmendmentError, match="tombstone_role_bytes_mismatch"):
        build_postseal_namespace_amendment(
            manifest_path=manifest,
            blocker_receipt_path=blocker,
        )


def test_independent_verifier_does_not_import_writer() -> None:
    source = (
        ROOT
        / "src/research_infra/"
        "replay_acceleration_partial_golden_postseal_verifier.py"
    ).read_text()
    assert "replay_acceleration_partial_golden_postseal import" not in source

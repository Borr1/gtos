"""D-1 custody enforcement for the contract-bound sleeve-registry payload.

Why this file exists
--------------------
``ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`` is a
``package_authority_input`` of three sealed decision contracts and feeds all four B7.5 arm
fingerprints.  Two byte-distinct versions of it exist:

* ``19365f60…`` — what every contract expects.  Referenced by **no commit**.
* ``a5bcc0f8…`` — what HEAD's LFS pointer names, and what every fresh checkout hydrates.

``PHASE1_INTEGRATION_DECISION_PACKAGE.md`` D-1 records that a ``git lfs prune``, a
``git gc --aggressive``, or a ``git checkout`` inside the producing worktree destroys the
``19365f60`` bytes permanently.  A committed markdown file saying "we have a backup" is exactly
the false-green pattern this wave is removing — so custody is recorded as **data**
(``docs/audits/fable5-vision-audit-20260725/receipts/D1_SLEEVE_REGISTRY_CUSTODY.json``) and
**checked here**.

What is enforced
----------------
1. The custody record is well-formed and internally consistent with the payload on disk.
2. The in-tree payload is in custody — as hydrated bytes, or as an LFS pointer whose object is
   present locally.  This **never** skips: a missing or wrong in-tree copy is a hard failure.
3. Every recorded byte-distinct version is recoverable, either because a recorded copy survives
   with its recorded hash, or because it is byte-exactly regenerable from one that does.
4. The regeneration recipe in the record actually works, bidirectionally, byte-for-byte.  This is
   the executable half: it is what makes the record a mechanism rather than a claim.
5. The three sealed contracts still bind the hash the record says they bind.
6. Nothing here ever touches an iCloud path (a stat on a dataless file triggers a network fetch).

Machine-local out-of-tree holds (``~/gtos-d1-hold-20260726``) **skip with a reason** when absent,
because they legitimately do not exist on another machine.  They never cause a silent pass: a
version with no surviving copy and no working regeneration path fails.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CUSTODY_RECORD = (
    REPO_ROOT
    / "docs/audits/fable5-vision-audit-20260725/receipts/D1_SLEEVE_REGISTRY_CUSTODY.json"
)
LFS_POINTER_MAGIC = b"version https://git-lfs"
ICLOUD_MARKERS = ("Mobile Documents", "com~apple~CloudDocs", "iCloud")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_lfs_pointer(path: Path) -> bool:
    with path.open("rb") as handle:
        return handle.read(len(LFS_POINTER_MAGIC)) == LFS_POINTER_MAGIC


def _pointer_oid(path: Path) -> str | None:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("oid sha256:"):
            return line.split(":", 1)[1].strip()
    return None


def _git_common_dir() -> Path | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover - no git present
        return None
    common = Path(out)
    return common if common.is_absolute() else (REPO_ROOT / common).resolve()


def _lfs_object_path(oid: str) -> Path | None:
    common = _git_common_dir()
    if common is None:
        return None
    return common / "lfs" / "objects" / oid[:2] / oid[2:4] / oid


def _row_hash(row: dict) -> str:
    """The record's declared derivation of ``row_hash_sha256``."""
    payload = {k: v for k, v in row.items() if k != "row_hash_sha256"}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _retime(raw: bytes, generated_utc: str) -> bytes:
    """The record's declared ``jsonl_retime_and_rehash`` regeneration transform."""
    lines = []
    for line in raw.decode("utf-8").splitlines():
        row = json.loads(line)
        row["generated_utc"] = generated_utc
        row["row_hash_sha256"] = _row_hash(row)
        lines.append(json.dumps(row, separators=(", ", ": ")) + "\n")
    return "".join(lines).encode("utf-8")


@pytest.fixture(scope="module")
def custody() -> dict:
    assert CUSTODY_RECORD.is_file(), (
        f"D-1 custody record is missing: {CUSTODY_RECORD}. "
        "It is the committed artifact that closes D-1; without it nothing records where the "
        "contract-bound sleeve-registry payload lives."
    )
    return json.loads(CUSTODY_RECORD.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def payload_path(custody: dict) -> Path:
    return REPO_ROOT / custody["payload"]["repo_relative_path"]


@pytest.fixture(scope="module")
def versions(custody: dict) -> dict[str, dict]:
    return {v["version_id"]: v for v in custody["byte_distinct_versions"]}


# ---------------------------------------------------------------------------
# 1. the record itself
# ---------------------------------------------------------------------------
def test_custody_record_is_wellformed(custody: dict, versions: dict[str, dict]) -> None:
    assert custody["schema"] == "gtos.custody.contract_bound_payload.v1"
    assert set(versions) == {"contract_bound", "head_pointer"}
    hashes = {v["sha256"] for v in versions.values()}
    assert len(hashes) == 2, "the record must describe two byte-DISTINCT versions"
    for version_id, version in versions.items():
        assert len(version["sha256"]) == 64, version_id
        assert version["bytes"] == custody["payload"]["bytes"], version_id
        assert version["row_count"] == custody["payload"]["row_count"], version_id
        assert version["copies"], f"{version_id} records no copy at all"
    assert custody["equivalence"]["measured"]["core_digests_equal"] is True


def test_record_never_probes_icloud(custody: dict) -> None:
    """A stat() on a dataless iCloud file triggers a network materialisation.

    The offsite copy is recorded for a human to use and must be flagged un-probeable, and no
    probeable path may live under iCloud.
    """
    saw_icloud_entry = False
    for version in custody["byte_distinct_versions"]:
        for copy in version["copies"]:
            paths = [copy.get("path_absolute", "")] + list(copy.get("paths_absolute", []))
            under_icloud = any(
                marker in path for path in paths for marker in ICLOUD_MARKERS
            )
            if under_icloud:
                saw_icloud_entry = True
                assert copy.get("probe") is False, (
                    f"copy {copy['copy_id']} is under iCloud and must never be probed at runtime"
                )
                assert copy.get("probe_disabled_reason"), copy["copy_id"]
    assert saw_icloud_entry, "the offsite iCloud copy must still be recorded, just not probed"


# ---------------------------------------------------------------------------
# 2. the in-tree copy — HARD, never skipped
# ---------------------------------------------------------------------------
def test_in_tree_payload_is_in_custody(
    custody: dict, payload_path: Path, versions: dict[str, dict]
) -> None:
    known = {v["sha256"]: vid for vid, v in versions.items()}

    assert payload_path.is_file(), (
        f"the contract-bound payload is absent from this checkout: {payload_path}. "
        "Recover with `git lfs checkout <path>` (the object store is local), or from "
        f"{custody['byte_distinct_versions'][0]['copies'][2]['path_absolute']}."
    )

    if _is_lfs_pointer(payload_path):
        oid = _pointer_oid(payload_path)
        assert oid in known, (
            f"{payload_path} is an LFS pointer naming an UNKNOWN oid {oid!r}. The custody record "
            f"knows only {sorted(known)}. Either the payload was replaced or the record is stale."
        )
        obj = _lfs_object_path(oid)
        assert obj is not None and obj.is_file(), (
            f"{payload_path} is an un-hydrated LFS pointer for {oid} and the local LFS object "
            f"is ALSO absent ({obj}). The payload is not in custody in this clone. "
            "Run `git lfs fetch && git lfs checkout <path>`. This is precisely the D-1 failure "
            "mode: a fresh clone that loses a contract-bound input."
        )
        assert _sha256(obj) == oid, f"LFS object {obj} is corrupt: content does not match its oid"
        return

    actual = _sha256(payload_path)
    assert actual in known, (
        f"the in-tree payload hashes to {actual}, which is NEITHER recorded version "
        f"({sorted(known)}). Either a third version now exists — in which case add it to "
        f"{CUSTODY_RECORD.name} — or the file has been corrupted."
    )
    assert payload_path.stat().st_size == custody["payload"]["bytes"]


# ---------------------------------------------------------------------------
# 3. every version survives somewhere, or is regenerable from something that does
# ---------------------------------------------------------------------------
def _probe_copies(version: dict) -> tuple[list[str], list[str], list[str]]:
    """Return (satisfied, absent_machine_local, absent_other) copy_ids."""
    satisfied: list[str] = []
    absent_local: list[str] = []
    absent_other: list[str] = []
    expected = version["sha256"]

    for copy in version["copies"]:
        if not copy.get("probe"):
            continue
        candidates: list[Path] = []
        if copy.get("path_absolute"):
            candidates.append(Path(copy["path_absolute"]))
        candidates.extend(Path(p) for p in copy.get("paths_absolute", []))
        if copy.get("path_relative_to_git_common_dir"):
            common = _git_common_dir()
            if common is not None:
                candidates.append(common / copy["path_relative_to_git_common_dir"])
        if copy.get("path_repo_relative"):
            candidates.append(REPO_ROOT / copy["path_repo_relative"])

        present = [p for p in dict.fromkeys(candidates) if p.is_file()]
        if not present:
            (absent_local if copy.get("machine_local") else absent_other).append(
                copy["copy_id"]
            )
            continue

        for path in present:
            if _is_lfs_pointer(path):
                # A pointer is custody only if it names this version and its object is local.
                if _pointer_oid(path) != expected:
                    continue
                obj = _lfs_object_path(expected)
                if obj is not None and obj.is_file() and _sha256(obj) == expected:
                    satisfied.append(f"{copy['copy_id']} (via local LFS object)")
                    break
                continue
            actual = _sha256(path)
            assert actual == expected, (
                f"recorded copy {copy['copy_id']} at {path} exists but its content has CHANGED: "
                f"expected {expected}, found {actual}. Custody is broken, not merely missing."
            )
            satisfied.append(copy["copy_id"])
            break
        else:
            (absent_local if copy.get("machine_local") else absent_other).append(
                copy["copy_id"]
            )
    return satisfied, absent_local, absent_other


@pytest.mark.parametrize("version_id", ["contract_bound", "head_pointer"])
def test_version_has_a_surviving_copy_or_a_proven_regeneration(
    versions: dict[str, dict], payload_path: Path, version_id: str
) -> None:
    version = versions[version_id]
    satisfied, absent_local, absent_other = _probe_copies(version)
    if satisfied:
        return

    # No recorded copy survived. Custody can still hold if this version is byte-exactly
    # regenerable from the payload actually present in this checkout.
    if payload_path.is_file() and not _is_lfs_pointer(payload_path):
        raw = payload_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() == version["sha256"]:
            return
        rebuilt = _retime(raw, version["generated_utc"])
        assert hashlib.sha256(rebuilt).hexdigest() == version["sha256"], (
            f"version {version_id} has NO surviving copy "
            f"(absent: {absent_other + absent_local}) and the recorded regeneration transform "
            f"does not reproduce {version['sha256']} from the in-tree payload. "
            "The payload is LOST."
        )
        return

    if absent_other:
        pytest.fail(
            f"version {version_id} has no surviving copy. Non-machine-local copies that should "
            f"exist are missing: {absent_other}. Machine-local: {absent_local}. "
            "Recover per D1_SLEEVE_REGISTRY_CUSTODY.json['recovery_runbook']."
        )
    pytest.skip(
        f"version {version_id}: only machine-local holds are recorded and none is present on "
        f"this machine ({absent_local}); the in-tree payload is not hydrated, so regeneration "
        "cannot be attempted here."
    )


# ---------------------------------------------------------------------------
# 4. the regeneration recipe is executable, not prose
# ---------------------------------------------------------------------------
def test_regeneration_recipe_is_byte_exact_and_bidirectional(
    custody: dict, payload_path: Path, versions: dict[str, dict]
) -> None:
    """The load-bearing check: custody of one version is custody of both.

    If this passes, the contract-bound bytes are recoverable from HEAD alone even if every copy
    of them is destroyed.
    """
    if not payload_path.is_file() or _is_lfs_pointer(payload_path):
        pytest.skip(
            "in-tree payload is not hydrated in this checkout; "
            "run `git lfs checkout` to exercise the regeneration proof"
        )

    raw = payload_path.read_bytes()
    here = _sha256(payload_path)
    source_id = next(vid for vid, v in versions.items() if v["sha256"] == here)
    other_id = next(vid for vid in versions if vid != source_id)
    other = versions[other_id]

    rebuilt = _retime(raw, other["generated_utc"])
    assert hashlib.sha256(rebuilt).hexdigest() == other["sha256"], (
        f"regeneration {source_id} -> {other_id} did not reproduce {other['sha256']}. "
        "The custody record's recovery guarantee is FALSE."
    )
    assert len(rebuilt) == other["bytes"]

    # and back again — the transform must be an involution on the timestamp
    round_trip = _retime(rebuilt, versions[source_id]["generated_utc"])
    assert round_trip == raw, "regeneration is not reversible; custody of one is not custody of both"

    # idempotence: retiming to the stamp a file already carries must be a no-op
    assert _retime(raw, versions[source_id]["generated_utc"]) == raw

    # and the derivation the record declares is the one the data actually uses
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    assert len(rows) == custody["payload"]["row_count"]
    assert all(_row_hash(row) == row["row_hash_sha256"] for row in rows), (
        "row_hash_sha256 is not the declared function of the row; the regeneration recipe in "
        "the custody record is describing a derivation the payload does not use"
    )


def test_recorded_equivalence_matches_the_payload_on_disk(
    custody: dict, payload_path: Path, versions: dict[str, dict]
) -> None:
    """Guard against the record drifting away from the bytes it describes."""
    if not payload_path.is_file() or _is_lfs_pointer(payload_path):
        pytest.skip("in-tree payload is not hydrated in this checkout")

    rows = [json.loads(line) for line in payload_path.read_bytes().decode("utf-8").splitlines()]
    measured = custody["equivalence"]["measured"]
    assert len(rows) == measured["rows_compared"]
    assert len({frozenset(r) for r in rows}) == 1
    assert len(rows[0]) == measured["fields_per_row"]
    assert len({r["generated_utc"] for r in rows}) == 1

    here = _sha256(payload_path)
    version = next(v for v in versions.values() if v["sha256"] == here)
    assert rows[0]["generated_utc"] == version["generated_utc"]
    assert rows[0]["schema"] == custody["payload"]["schema"]

    core = [
        {k: v for k, v in r.items() if k not in ("generated_utc", "row_hash_sha256")}
        for r in rows
    ]
    digest = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert digest == measured["core_digest_contract_bound"] == measured[
        "core_digest_head_pointer"
    ], (
        "the decision-bearing content of this payload has changed. This is NOT the benign "
        "regeneration-timestamp difference the record describes — it is real drift."
    )


# ---------------------------------------------------------------------------
# 5. the contracts still expect what the record says they expect
# ---------------------------------------------------------------------------
def test_sealed_contracts_still_bind_the_recorded_hash(
    custody: dict, versions: dict[str, dict]
) -> None:
    expected = versions["contract_bound"]["sha256"]
    rel = custody["payload"]["repo_relative_path"]
    checked = 0
    for binding in versions["contract_bound"]["expected_by"]:
        artifact = REPO_ROOT / binding["artifact"]
        if not artifact.is_file():
            continue
        if artifact.name == "VERIFICATION_RESULT.json":
            continue  # a large sealed result; the three contracts are the enforcing ones
        contract = json.loads(artifact.read_text(encoding="utf-8"))
        rows = contract.get("input_bindings", {}).get("package_authority_inputs", [])
        match = [r for r in rows if r.get("path") == rel]
        assert match, f"{binding['alias']} no longer binds {rel} at all"
        assert match[0]["sha256"] == expected, (
            f"{binding['alias']} now expects {match[0]['sha256']}, but the custody record says "
            f"{expected}. A contract was re-sealed without updating {CUSTODY_RECORD.name}."
        )
        checked += 1
    assert checked >= 3, f"expected to check 3 sealed contracts, checked {checked}"


def test_git_history_flags_are_still_true(custody: dict, versions: dict[str, dict]) -> None:
    """If someone commits the 19365f60 bytes (the recommended D-1 fix), this must be updated.

    Failing here is the correct outcome of that change, not a regression: the custody record
    would otherwise keep asserting the contract-bound version is orphaned after it stopped being.
    """
    rel = custody["payload"]["repo_relative_path"]
    try:
        pointer = subprocess.run(
            ["git", "show", f"HEAD:{rel}"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        pytest.skip("git is unavailable or the path is not tracked at HEAD")

    head_oid = next(
        (l.split(":", 1)[1].strip() for l in pointer.splitlines() if l.startswith("oid sha256:")),
        None,
    )
    assert head_oid, "HEAD no longer stores this path as an LFS pointer"

    by_hash = {v["sha256"]: v for v in versions.values()}
    assert head_oid in by_hash, (
        f"HEAD's pointer names {head_oid}, which the custody record does not know. Add it."
    )
    for sha, version in by_hash.items():
        expected_in_history = sha == head_oid
        assert version["in_git_history"] is expected_in_history, (
            f"custody record says version {version['version_id']} in_git_history="
            f"{version['in_git_history']}, but HEAD's pointer names {head_oid}. "
            "If the D-1 bytes were just committed, flip both flags in "
            f"{CUSTODY_RECORD.name} in the same commit."
        )

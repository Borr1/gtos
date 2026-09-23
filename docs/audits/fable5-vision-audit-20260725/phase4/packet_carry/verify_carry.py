#!/usr/bin/env python3
"""Preflight / postflight verifier for the Session S packet carry. Runs ON the VPS.

Why this is a file and not a runbook code block: the wave-3 runbooks put multi-line Python into
``python - <<'PY'`` heredocs, which is bash syntax in a PowerShell runbook and does not run as
written. A file has no quoting problem, is reviewable before it is executed, and gives the
operator a real exit code to branch on.

**This script cannot reach a broker.** It imports `book_owner` to prove the module *loads* -- the
exact failure that blocked this carry -- but never constructs `UltimateBookOwner`, never touches
MetaTrader5, and never opens the packet log for writing. `--check imports` is the only subcommand
that imports repo code at all.

Usage on the VPS, from the repo root, with the interpreter the books actually run:

    .venv-gtos\\Scripts\\python.exe docs\\...\\packet_carry\\verify_carry.py --check preflight
    .venv-gtos\\Scripts\\python.exe docs\\...\\packet_carry\\verify_carry.py --check postflight
    .venv-gtos\\Scripts\\python.exe docs\\...\\packet_carry\\verify_carry.py --check imports
    .venv-gtos\\Scripts\\python.exe docs\\...\\packet_carry\\verify_carry.py --check packets

Exit code 0 means the step passed. Any other exit code means STOP and roll back.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST_PATH = HERE / "MANIFEST.json"
DEFAULT_PACKET_LOG = Path("shadow_logs") / "ultimate_book_runtime_learning_packets.jsonl"

OK, STOP = 0, 2


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _dest(entry: dict, repo: Path) -> Path:
    return repo / entry["destination_on_vps"].replace("\\", "/")


def _banner(title: str) -> None:
    print("=" * 78)
    print(title)
    print("=" * 78)


def _assert_repo_root(repo: Path) -> int:
    """Refuse to run from the wrong directory.

    Without this, `preflight` run from e.g. `repo\\scripts` reports every file `ABSENT` and exits
    0 -- which is a *legitimate-looking* state for three of the six. The operator then follows the
    rollback's "delete the ones that were ABSENT" branch and removes two files that were correctly
    carried. A green from the wrong cwd is the worst kind, because nothing about it looks wrong.
    """
    marker = repo / "src" / "components" / "ultimate_book" / "book_engine.py"
    if not marker.is_file():
        print(f"STOP. This does not look like the repo root: {repo}")
        print(f"      expected to find {marker}")
        print("      cd to the repo root (the directory containing src\\ and config\\) and retry,")
        print("      or pass --repo <path>.")
        return STOP
    return OK


def _interpreter_note() -> None:
    """Report the interpreter, and prove it can load what the books load.

    A bare `python` on PATH is a different version from the books' `.venv-gtos` interpreter. A
    version-number guard cannot tell them apart (both are >= 3.10), so the honest check is
    whether this interpreter has the book's own dependencies. If it does not, the failure is
    "wrong interpreter", NOT "bad carry" -- and saying so prevents an operator from rolling back a
    byte-perfect carry.
    """
    print(f"interpreter: {sys.version.split()[0]}  ({sys.executable})")
    missing = []
    for dep in ("yaml",):
        try:
            __import__(dep)
        except Exception:  # noqa: BLE001
            missing.append(dep)
    if missing:
        print(f"  !! this interpreter cannot import {missing} -- which the live book requires.")
        print("     You are almost certainly NOT on the interpreter the books run.")
        print("     Re-read it from the running book's CommandLine (runbook §2.1) and retry.")
        print("     Do NOT roll the carry back on the strength of a failure from this interpreter.")


# ----------------------------------------------------------------------------------------
# preflight -- run BEFORE copying anything
# ----------------------------------------------------------------------------------------

def check_preflight(repo: Path) -> int:
    """Record what is on the host now, and refuse to guess about anything.

    Two of the six files may already be present: `broker_clock.py` and `packet_economics.py`
    were carried on 2026-07-29 as inert files. This step reports what is actually there rather
    than assuming either way.
    """
    _banner("PREFLIGHT - what is on this host right now")
    if _assert_repo_root(repo):
        return STOP
    manifest = _manifest()
    print(f"carry base commit : {manifest['vps_base_commit']}")
    print(f"repo root         : {repo}")
    print()

    rows, unexpected = [], []
    for entry in sorted(manifest["files"], key=lambda e: (e["copy_order"] or 99)):
        dest = _dest(entry, repo)
        actual = _sha256(dest)
        expected_before = entry["sha256_before_expected_at_redacted_host"]
        after = entry["sha256_after_carry"]

        if actual is None:
            state = "ABSENT"
        elif actual == after:
            state = "ALREADY CARRIED"
        elif expected_before and actual == expected_before:
            state = "AT EXPECTED BASE"
        else:
            state = "*** UNEXPECTED CONTENT ***"
            unexpected.append((entry["destination_on_vps"], actual))
        rows.append((entry["copy_order"], entry["destination_on_vps"], state, actual))

    width = max(len(r[1]) for r in rows)
    for order, dest, state, actual in rows:
        print(f"  {str(order or '-'):>2}  {dest:<{width}}  {state:<26} {(actual or '')[:16]}")

    print()
    if unexpected:
        print("STOP. These files are neither the expected base nor the carried version.")
        print("Someone changed them on the host, or the lineage moved. Do not overwrite them")
        print("until you know what they are -- back them up and stop.")
        for dest, actual in unexpected:
            print(f"    {dest}  sha256={actual}")
        return STOP

    already = [r for r in rows if r[2] == "ALREADY CARRIED"]
    if already:
        print(f"NOTE: {len(already)} file(s) already carry this exact version. Copying them again")
        print("      is a no-op. That is expected if a previous attempt landed partially.")
    print("PREFLIGHT OK - every file is either absent or at the expected base.")
    return OK


# ----------------------------------------------------------------------------------------
# postflight -- run AFTER copying, BEFORE restarting anything
# ----------------------------------------------------------------------------------------

def check_postflight(repo: Path) -> int:
    _banner("POSTFLIGHT - did every byte land exactly?")
    if _assert_repo_root(repo):
        return STOP
    manifest = _manifest()
    bad = []
    for entry in sorted(manifest["files"], key=lambda e: (e["copy_order"] or 99)):
        dest = _dest(entry, repo)
        actual = _sha256(dest)
        want = entry["sha256_after_carry"]
        ok = actual == want
        # The silence alarm has no copy_order: it is standalone, read-only and optional. Not
        # copying it is a valid choice, so its absence must not raise a STOP -- a verifier that
        # cries wolf on a supported configuration is worse than no verifier.
        optional = entry["copy_order"] is None
        if optional and actual is None:
            print(f"  SKIP {entry['destination_on_vps']}  (optional, not copied)")
            continue
        print(f"  {'OK  ' if ok else 'BAD '} {entry['destination_on_vps']}")
        if not ok:
            bad.append((entry["destination_on_vps"], want, actual))

    print()
    if bad:
        print("STOP. At least one file did not land byte-exact. Do NOT restart the books.")
        print("Restore from the backup taken in step 2.5 and stop.")
        for dest, want, actual in bad:
            print(f"    {dest}\n      expected {want}\n      actual   {actual or '<absent>'}")
        print()
        print("A common cause is a text-mode transfer rewriting LF to CRLF. Every carried file")
        print("is LF-only; if the actual hash differs but the file looks right, check line endings.")
        return STOP
    print("POSTFLIGHT OK - all files byte-exact against the manifest.")
    return OK


# ----------------------------------------------------------------------------------------
# imports -- the check that catches a bad copy while the books still run the old code
# ----------------------------------------------------------------------------------------

def check_imports(repo: Path) -> int:
    _banner("IMPORTS - does the live book's module graph still load?")
    if _assert_repo_root(repo):
        return STOP
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    _interpreter_note()
    print()

    # This check must pass in BOTH directions: after the carry, and after a ROLLBACK that
    # correctly deletes the files which were absent before it. Importing packet_guard
    # unconditionally would make a correctly-rolled-back tree fail -- and the runbook tells the
    # operator not to restart until this passes, so a false STOP here keeps both books DOWN on a
    # live funded account. The one module that must load in either state is `book_owner`.
    optional = {
        "runtime_learning_packet": repo / "src/components/ultimate_book/runtime_learning_packet.py",
        "packet_economics": repo / "src/components/ultimate_book/packet_economics.py",
        "packet_guard": repo / "src/components/ultimate_book/packet_guard.py",
    }
    present = {name for name, path in optional.items() if path.is_file()}
    carried = {"packet_economics", "packet_guard"} <= present
    print(f"  detected state : {'CARRIED' if carried else 'ROLLED BACK / PARTIAL'}")
    print()

    rlp = pe = None
    try:
        import src.components.ultimate_book.runtime_learning_packet as rlp  # noqa: F811
        print("  OK   runtime_learning_packet")
        if "packet_economics" in present:
            import src.components.ultimate_book.packet_economics as pe  # noqa: F811
            print("  OK   packet_economics")
        if "packet_guard" in present:
            import src.components.ultimate_book.packet_guard  # noqa: F401
            print("  OK   packet_guard")
        import src.components.ultimate_book.book_owner  # noqa: F401
        print("  OK   book_owner        <- the module that blocked this carry")
    except Exception as exc:  # noqa: BLE001 - this is the failure we are hunting
        print(f"\n  IMPORT FAILED: {type(exc).__name__}: {exc}")
        print("\nSTOP. Restore from the step 2.5 backup and do not restart the books.")
        return STOP

    print()
    if pe is not None:
        print(f"  broker_clock available : {pe.BROKER_CLOCK_AVAILABLE}")
        if not pe.BROKER_CLOCK_AVAILABLE:
            print("    ^ NOT an error. Night counts return null with a labelled reason until")
            print("      src\\utils\\broker_clock.py is present. Everything else works.")

    advisory_free = "ultimate_convergence_advisory" not in rlp.packet_schema().get(
        "optional_fields", []
    )
    print(f"  convergence advisory carried : {not advisory_free}  (must be False)")
    if not advisory_free:
        print("\nSTOP. This is the mainline emitter, not the VPS-lineage carry.")
        return STOP

    if not carried:
        print("\nIMPORTS OK for a ROLLED-BACK tree. `book_owner` loads, so it is safe to restart")
        print("the books -- but the carry is NOT in place. Do not report this as a successful carry.")
        return OK

    # Importing cleanly is NOT the same as having carried. Files 1-4 can all be present and
    # correct while book_owner.py is still the base file -- every import succeeds and nothing new
    # is ever emitted. The rollback gate is imports-only, so without this the operator can green
    # a carry that did not happen. Assert the wiring behaviourally, on the class.
    from src.components.ultimate_book.book_owner import UltimateBookOwner
    wired = [m for m in ("_runtime_learning_economics", "_broker_server_name")
             if not hasattr(UltimateBookOwner, m)]
    if wired:
        print(f"\nSTOP. Files 1-4 are carried but book_owner.py is NOT: missing {wired}.")
        print("Every import succeeds and the book will emit exactly what it emits today.")
        print("Copy file 5 (book_owner.py) and re-run --check postflight, then this check.")
        return STOP
    print("  OK   book_owner carries the economics wiring")
    print("\nIMPORTS OK.")
    return OK


# ----------------------------------------------------------------------------------------
# packets -- did the corpus survive, and is the new block appearing?
# ----------------------------------------------------------------------------------------

def _iter_packets(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line_no, raw in enumerate(handle, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                yield line_no, json.loads(raw)
            except json.JSONDecodeError:
                yield line_no, None


def check_packets(repo: Path, log_path: Path | None, tail: int) -> int:
    _banner("PACKETS - the existing corpus must be untouched, and new blocks must appear")
    if _assert_repo_root(repo):
        return STOP
    path = log_path or (repo / DEFAULT_PACKET_LOG)
    if not path.is_file():
        print(f"STOP. Packet log not found at {path}")
        print("Pass --packet-log with the real path.")
        return STOP

    def stable_hash(value, prefix="ub"):
        text = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(f"{prefix}:{text}".encode("utf-8")).hexdigest()

    import collections
    total = rehash_ok = malformed = with_economics = with_advisory = 0
    last_line_malformed = False
    by_namespace = collections.Counter()
    by_event = collections.Counter()
    schema_versions, recent = set(), []
    for _line_no, packet in _iter_packets(path):
        if packet is None:
            malformed += 1
            last_line_malformed = True
            continue
        last_line_malformed = False
        total += 1
        by_namespace[packet.get("namespace")] += 1
        by_event[packet.get("event_type")] += 1
        schema_versions.add(packet.get("schema_version"))
        if "economics" in packet:
            with_economics += 1
        if "ultimate_convergence_advisory" in packet:
            with_advisory += 1
        body = {k: v for k, v in packet.items() if k != "packet_hash_sha256"}
        if stable_hash(body, "runtime_learning_packet") == packet.get("packet_hash_sha256"):
            rehash_ok += 1
        if len(recent) < tail:
            recent.append(packet)
        else:
            recent.pop(0)
            recent.append(packet)

    print(f"  packets             : {total:,}")
    if total == 0:
        # A verifier that says OK over an empty log is the false-green this carry exists to
        # prevent: zero packets is not "nothing to check", it is "the books are not emitting".
        print("\nSTOP. The packet log parsed to ZERO packets.")
        print("That is not a pass. Either the path is wrong, or the books are not emitting at all.")
        return STOP
    print(f"  re-hash exactly     : {rehash_ok:,}  ({rehash_ok / total * 100:.4f} %)")
    print(f"  malformed lines     : {malformed}")
    print(f"  schema_version(s)   : {sorted(v for v in schema_versions if v)}")
    print(f"  carry an economics block  : {with_economics:,}")
    print(f"  carry advisory key        : {with_advisory:,}  (must stay 0)")
    print()
    # Both namespaces write ONE shared log (`..._packet_log_path` is a single global key with no
    # namespace interpolation). So "fresh rows appeared" after restarting ONE book proves nothing:
    # the rows may all belong to the book you did not touch. Always read the per-namespace split.
    print("  by namespace:")
    for ns, n in by_namespace.most_common():
        print(f"     {str(ns):<32} {n:>8,}")
    print("  by event_type:")
    for ev, n in by_event.most_common():
        flag = "   <- guard refusals" if ev == "packet_rejected" else ""
        print(f"     {str(ev):<32} {n:>8,}{flag}")
    print()

    failed = False
    if by_event.get("packet_rejected"):
        print(f"NOTE: {by_event['packet_rejected']:,} packet_rejected marker(s) in the log. The guard")
        print("      refused those packets and quarantined their bodies to the .quarantine.jsonl")
        print("      sidecar. A handful is fine; a stream of them means the emitter is producing")
        print("      packets that do not validate -- investigate before declaring success.")
        print()
    if malformed > 1 or (malformed == 1 and not last_line_malformed):
        # One malformed line is normal ONLY as the final line: the book appends continuously and
        # can be caught mid-write. Anything else is corruption, and it must not read as a pass --
        # previously `malformed` was counted and never gated, so a log of pure garbage printed
        # "PACKETS OK".
        print(f"STOP. {malformed} malformed line(s), and not merely a partial final line.")
        print("The packet log is corrupt. Do not treat this as a successful carry.")
        failed = True
    elif malformed == 1:
        print("NOTE: 1 malformed line, and it is the last line -- a normal mid-write append.")
    if total and rehash_ok != total:
        print(f"STOP. {total - rehash_ok} packet(s) no longer reproduce their own hash.")
        print("The carry must never rewrite history. Roll back.")
        failed = True
    if with_advisory:
        print(f"STOP. {with_advisory} packet(s) carry the convergence-advisory key.")
        print("That is the mainline emitter. Roll back.")
        failed = True
    if len(schema_versions - {None}) > 1:
        print(f"STOP. More than one schema_version in the log: {sorted(schema_versions)}")
        print("SCHEMA_VERSION must not be bumped -- it would fail every historical packet.")
        failed = True
    if failed:
        return STOP

    if with_economics == 0:
        print("No economics block yet. Expected BEFORE the restart, and for a while after it:")
        print("the block only attaches to events that have something to cost (placements,")
        print("closes, managed positions with broker fields). If the books have been running")
        print("for an hour of open market and this is still 0, investigate before declaring")
        print("success -- that is the false-green this carry exists to prevent.")
    else:
        print(f"Economics blocks are appearing on {with_economics:,} packet(s).")
        sample = next((p for p in reversed(recent) if "economics" in p), None)
        if sample:
            print("\nMost recent economics block:")
            print(json.dumps(sample["economics"], indent=2)[:1400])

    print("\nPACKETS OK.")
    return OK


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", required=True,
        choices=("preflight", "postflight", "imports", "packets"),
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--packet-log", type=Path, default=None)
    parser.add_argument("--tail", type=int, default=200)
    args = parser.parse_args()

    repo = args.repo.resolve()
    if args.check == "preflight":
        return check_preflight(repo)
    if args.check == "postflight":
        return check_postflight(repo)
    if args.check == "imports":
        return check_imports(repo)
    return check_packets(repo, args.packet_log, args.tail)


if __name__ == "__main__":
    raise SystemExit(main())

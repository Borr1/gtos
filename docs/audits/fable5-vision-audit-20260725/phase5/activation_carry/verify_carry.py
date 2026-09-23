#!/usr/bin/env python3
"""Verify the Session AC activation carry ON THE HOST, behaviourally.

Six gates, real exit codes, no grep. Run every one from the repo root the books actually run
from (the runbook derives it from the running book's own command line):

    .venv-gtos\\Scripts\\python.exe docs\\...\\activation_carry\\verify_carry.py --check preflight
    ... --check postflight      (stage D is OPTIONAL here -- it lands in runbook section 10)
    ... --check imports
    ... --check behaviour
    ... --check stage-d         (section 10's gate: stage D applied AND correct)
    ... --check rollback        (only after a rollback; see the gate note below)
    ... --check all             (postflight + imports + behaviour; preflight and rollback are
                                 BEFORE/AFTER checks and cannot both pass in the same state)

Exit codes: ``0`` pass, ``2`` fail/STOP, ``3`` usage or environment refusal (wrong interpreter,
or not run from inside the book's repo tree). **A ``3`` is not a failure of the carry.**

**Why ``rollback`` is a separate gate, and what it judges against.** Session S shipped a carry
whose rollback could not pass its own verifier: the only postflight it had demanded the
CARRIED shas, so an operator who correctly rolled back was told the tree was broken and not to
restart. ``--check rollback`` asserts the opposite state and then asserts the tree still
imports and constructs. A correct rollback passes it; a half-finished one does not.

The state it asserts is **the one the host was actually on**, read from the
``BACKUP_MANIFEST.json`` that runbook §3 writes beside the backup — not the lineage's base.
A refuter found that difference reproducing S's own defect inside this carry: a host that
already had S's packet carry applied is not on the lineage base, so judging against the
lineage failed a *correct* rollback and then told the operator to delete four files, which
produces a ``ModuleNotFoundError`` crash loop. Without a backup manifest the check falls back
to the lineage base and says so, loudly, rather than pretending.

Both phases always run. Gating the "does it start" proof behind the byte comparison meant that
in exactly the states where the tree does not start, the operator was told only "rollback
incomplete".

Nothing here can reach a broker. ``imports`` constructs ``UltimateBookOwner`` with a stub
adapter and a scratch directory, which is what ``run_book.py:294`` does before it ever
ticks; ``mt5.connect()`` is never called and no MT5 handle is created.

One side effect worth naming rather than hiding: ``--check behaviour`` executes the carried
``.tools/monitor_books.py`` as a module to test its window function, and that file's own module
top calls ``load_dotenv(<repo>/.env, override=True)``. So this process READS the host's ``.env``
and mutates its OWN ``os.environ``. Nothing is written to the host and no other process is
affected, but "nothing happens" would have been the wrong word.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "MANIFEST.json"

PASS, FAIL, REFUSE = 0, 2, 3

_problems: list[str] = []


def problems_since(mark: int) -> int:
    """Failures recorded since ``mark``. Each check scores only its own, so a FAIL in one
    cannot be reported as a FAIL in the next when they run together under ``--check all``."""
    return len(_problems) - mark


def say(ok: bool | None, msg: str) -> None:
    mark = {True: "  ok  ", False: " FAIL ", None: "  --  "}[ok]
    print(f"[{mark}] {msg}")
    if ok is False:
        _problems.append(msg)


def sha256_of(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------------------
# environment
# --------------------------------------------------------------------------------------

def resolve_repo_root() -> Path:
    """The repo root, taken from where THIS FILE lives, then proved by landmarks.

    Deliberately not ``os.getcwd()``: S's verifier had a false-green where running it from
    the wrong directory made every file look absent, which read as "not carried yet".
    """
    root = HERE.parents[4]
    landmarks = ["run_book.py", "src/components/ultimate_book/book_engine.py", "config/agent_config.yaml"]
    missing = [m for m in landmarks if not (root / m).exists()]
    if missing:
        print(f"[ STOP ] {root} does not look like the book's repo root (missing: {', '.join(missing)}).")
        print("         Copy this carry INTO the tree the running book uses, then re-run from there.")
        sys.exit(REFUSE)
    return root


def check_interpreter(root: Path) -> None:
    """Refuse to answer under an interpreter the books do not use.

    Every wave-3 runbook tested a bare PATH ``python`` (3.11.15) while all ten live
    processes run ``.venv-gtos\\Scripts\\python.exe`` (3.13.13, measured on the host). A
    green from the wrong interpreter is worse than no answer.
    """
    if sys.version_info < (3, 10):
        print(f"[ STOP ] python {sys.version.split()[0]} is too old; the books run 3.13.")
        sys.exit(REFUSE)
    # Checked on sys.prefix, NOT sys.executable. On this host each book appears as a parent/child
    # `python.exe` pair with identical command lines, which is the signature of a launcher that
    # re-execs — and a re-exec would leave `sys.executable` pointing at the base interpreter while
    # the venv is still active. Refusing on `sys.executable` would then block a correct invocation,
    # which is a worse failure than the one it guards against. `sys.prefix` is the venv either way.
    want = (root / ".venv-gtos").resolve()
    got = Path(sys.prefix).resolve()
    if str(got).lower() != str(want).lower():
        print(f"[ STOP ] this interpreter's environment is {got}")
        print(f"         The books run out of {want}. Re-run with that one:")
        print(f'         & "{want}\\Scripts\\python.exe" "{Path(__file__)}" --check <check>')
        print(f"         (executable: {sys.executable}, version {sys.version.split()[0]})")
        sys.exit(REFUSE)


# --------------------------------------------------------------------------------------
# the file plan, mine plus Session S's when its manifest is present
# --------------------------------------------------------------------------------------

def _isolate_from_mt5(root: Path) -> None:
    """Put the host tree on sys.path and shadow ``MetaTrader5`` with an empty module.

    Unconditional and deliberate. The host HAS the real package, and every module this
    verifier imports would import it happily; shadowing it means no MT5 handle can exist in
    this process even by accident, which is the property that makes running the verifier on
    a live host uninteresting. Nothing imported here calls into the module at import time
    (checked on the lineage), so the stub changes no verdict.
    """
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    sys.modules["MetaTrader5"] = types.ModuleType("MetaTrader5")


def load_plan(root: Path) -> list[dict]:
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    plan = [dict(rec, carry="AC") for rec in man["files"]]

    composes = man.get("composes_with", {})
    embedded = composes.get("session_S_files") or []
    s_rel = composes.get("session_S_packet_carry")
    s_path = (root / s_rel) if s_rel else None

    # Prefer S's own manifest; fall back to the copy embedded in this one at build time. When
    # both exist they must agree — a silently stale embedded copy would let postflight pass on
    # the wrong bytes, which is the failure this whole carry exists to make impossible.
    s_records = embedded
    source = "embedded in this manifest"
    if s_path and s_path.is_file():
        live = json.loads(s_path.read_text(encoding="utf-8"))["files"]
        live_shas = {r["destination_on_vps"]: r["sha256_after_carry"] for r in live}
        emb_shas = {r["destination_on_vps"]: r["sha256_after_carry"] for r in embedded}
        if emb_shas and live_shas != emb_shas:
            say(False, "Session S's manifest disagrees with the copy embedded here — "
                       "the composed carry is stale, STOP and re-derive it")
        s_records = [{
            "destination_on_vps": r["destination_on_vps"],
            "is_new_file_on_vps": r["is_new_file_on_vps"],
            "sha256_before_expected": r.get("sha256_before_expected_at_redacted_host"),
            "sha256_after_carry": r["sha256_after_carry"],
            "source_in_this_repo": r["source_in_this_repo"],
            "copy_order": r.get("copy_order"),
        } for r in live]
        source = s_rel

    if not s_records:
        say(None, "Session S packet carry is unknown to this manifest — verifying the AC carry "
                  "ONLY. The composed state is unverified; do not report the packet unblock as "
                  "applied.")
        return plan

    for rec in s_records:
        repo_path = rec["destination_on_vps"].replace("\\", "/")
        if repo_path == "src/utils/broker_clock.py":
            continue              # shared, already in the AC plan; installed once
        plan.append(dict(rec, carry="S", stage="C", repo_path=repo_path))
    say(True, f"Session S packet carry read from {source} ({len(s_records)} files); "
              "verifying the COMPOSED state")
    return plan


# --------------------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------------------

def check_preflight(root: Path, plan: list[dict]) -> int:
    """BEFORE any copy: is every destination where the carry expects it?"""
    print("\n== preflight: is the host where this carry was authored against? ==")
    mark = len(_problems)
    unexpected = 0
    for rec in plan:
        path = root / rec["repo_path"]
        got = sha256_of(path)
        want_before = rec.get("sha256_before_expected")
        want_after = rec["sha256_after_carry"]
        tag = f"[{rec['carry']}/{rec['stage']}] {rec['repo_path']}"
        if got is None:
            if rec["is_new_file_on_vps"]:
                say(True, f"{tag}: ABSENT (expected — new file)")
            else:
                say(False, f"{tag}: MISSING and it should exist")
                unexpected += 1
        elif got == want_after:
            say(True, f"{tag}: ALREADY CARRIED")
        elif want_before and got == want_before:
            say(True, f"{tag}: AT EXPECTED BASE")
        else:
            say(False, f"{tag}: *** UNEXPECTED CONTENT *** sha256={got}")
            unexpected += 1
    if unexpected or problems_since(mark):
        print(f"\n  STOP. {unexpected} path(s) are neither the expected base nor the carried "
              "state. The host has moved since this carry was authored. Do not copy; report "
              "the shas above and get the carry re-derived.")
        return FAIL
    print("\n  preflight clean.")
    return PASS


def check_postflight(root: Path, plan: list[dict]) -> int:
    """AFTER the copy: is every byte where it should be, and are the ORDER invariants held?

    **Stage D is optional here, and getting that wrong made this gate unpassable.** The runbook
    defers ``.tools/monitor_books.py`` to §10, after the books are healthy — so at §6, where the
    runbook says "all three must exit 0", stage D is legitimately still at its base bytes. The first
    version of this function demanded the carried sha for every plan entry and therefore exited 2 on
    a perfectly correct §6 state, one step before the one-way door. That teaches an operator either
    to roll back a good carry or to walk past a red gate, and the second is worse.

    So a stage-D file at its *base* sha is reported and not counted. Anything else about it — a
    third value, a missing file — still fails, because that is a partial write.
    """
    mark = len(_problems)
    print("\n== postflight: exact bytes ==")
    for rec in plan:
        path = root / rec["repo_path"]
        got = sha256_of(path)
        tag = f"[{rec['carry']}/{rec['stage']}] {rec['repo_path']}"
        if got == rec["sha256_after_carry"]:
            say(True, f"{tag}: carried")
        elif rec["stage"] == "D" and got is not None and got == rec.get("sha256_before_expected"):
            say(None, f"{tag}: at base — stage D is applied separately in runbook §10, "
                      "not before the restart")
        elif got is None:
            say(False, f"{tag}: MISSING")
        else:
            say(False, f"{tag}: sha256={got} != expected {rec['sha256_after_carry']}")

    print("\n== postflight: the THREE dependency invariants ==")
    # All three by sha, not by existence. A refuter showed that testing `is_file()` for
    # broker_clock reports `ok` on a TRUNCATED copy, which is a module-load death.
    carried = {p: sha256_of(root / p) == _sha(plan, p) for p in (
        "src/utils/broker_clock.py",
        "src/components/ultimate_book/governor_state.py",
        "src/components/ultimate_book/book_engine.py",
        ".tools/monitor_books.py",
    )}
    bc = carried["src/utils/broker_clock.py"]
    gs = carried["src/components/ultimate_book/governor_state.py"]
    be = carried["src/components/ultimate_book/book_engine.py"]
    mon = carried[".tools/monitor_books.py"]
    say(not (gs and not bc),
        "governor_state carried => broker_clock carried  (else ModuleNotFoundError at import)")
    say(not (be and not gs),
        "book_engine carried    => governor_state carried (else TypeError at startup)")
    # The third invariant, found by a refuter: the carried monitor imports broker_clock at module
    # top, unguarded, after `sys.path.insert(0, REPO_ROOT)`. The monitor is a supervisor-restarted
    # live process, so violating this is a permanent crash loop of the ALERTING layer.
    say(not (mon and not bc),
        "monitor_books carried  => broker_clock carried  (else the monitor crash-loops, silently)")

    if problems_since(mark):
        print("\n  NOTE: a file that is PRESENT but not at its expected sha is the dangerous case, "
              "and it is what the byte check above is for. A truncated copy can import, construct "
              "and tick while the governor silently returns None — the sha comparison is the only "
              "gate that sees it, so do not treat `--check imports` alone as sufficient.")
    return FAIL if problems_since(mark) else PASS


def _sha(plan: list[dict], repo_path: str) -> str | None:
    for rec in plan:
        if rec["repo_path"] == repo_path:
            return rec["sha256_after_carry"]
    return None


def _load_backup_manifest(root: Path) -> dict | None:
    """The state the host was ACTUALLY on when the backup was taken, if §3 recorded it.

    This is the fix for the defect this carry exists to remove, found by a refuter *inside* it.
    ``sha256_before_expected`` is the lineage's base — but a host that already has Session S's
    packet carry applied is not on the lineage's base, and §3's backup captures whatever it was
    on. Judging a rollback against the lineage then fails a **correct** rollback, which is
    precisely Session S's defect wearing this session's name. When §3 has written a backup
    manifest, that is the authority.
    """
    for candidate in sorted(root.glob("_carry_backup_AC_*/BACKUP_MANIFEST.json"), reverse=True):
        try:
            return json.loads(candidate.read_text(encoding="utf-8")) | {"__path__": str(candidate)}
        except (OSError, ValueError):
            continue
    return None


def check_rollback(root: Path, plan: list[dict]) -> int:
    """AFTER a rollback: is the tree back at the state the host was on, and does it still start?

    This is the check S's carry did not have. A rolled-back tree cannot pass ``postflight``
    by construction, so an operator running the only available gate was told to worry.
    """
    mark = len(_problems)
    backup = _load_backup_manifest(root)
    if backup:
        base = {rec["repo_path"]: rec["sha256"] for rec in backup["files"]}
        say(True, f"backup manifest found ({backup['__path__']}) — judging the rollback against "
                  "the state this host was ACTUALLY on")
    else:
        base = {rec["repo_path"]: rec.get("sha256_before_expected") for rec in plan}
        say(None, "no backup manifest (runbook §3 writes one) — falling back to the LINEAGE base. "
                  "If this host already had Session S's packet carry applied before you started, "
                  "a correct rollback will fail below. Check the §3 backup directory instead of "
                  "acting on that result.")

    print("\n== rollback: is the tree back at the state the host was on? ==")
    for rec in plan:
        repo_path = rec["repo_path"]
        got = sha256_of(root / repo_path)
        want = base.get(repo_path)
        tag = f"[{rec['carry']}/{rec['stage']}] {repo_path}"
        if want is None:
            # absent when the backup was taken (or a new file on the lineage): must be gone now
            say(got is None, f"{tag}: removed" if got is None else
                             f"{tag}: STILL PRESENT (it did not exist before the carry; delete it)")
        elif got == want:
            say(True, f"{tag}: restored")
        elif got == rec["sha256_after_carry"]:
            say(False, f"{tag}: still CARRIED — rollback incomplete")
        else:
            say(False, f"{tag}: neither the pre-carry state nor the carried one, sha256={got}")

    # UNCONDITIONAL, and that is the point. Gating this behind the sha phase meant that in exactly
    # the states where the tree does NOT start, the operator was told "rollback incomplete" and
    # never told the host cannot start. Both verdicts, always.
    print("\n  and does the tree start?")
    started = check_imports(root, plan, quiet_header=True)
    return FAIL if (problems_since(mark) or started != PASS) else PASS


def check_imports(root: Path, plan: list[dict], *, quiet_header: bool = False) -> int:
    """Exactly what ``run_book.py`` does before its first tick, in this process."""
    mark = len(_problems)
    if not quiet_header:
        print("\n== imports: run_book.py:32 (import) then :294 (construct) ==")
    _isolate_from_mt5(root)
    # Every module `run_book.py` imports at module top, in its order (:26-35), not just the one
    # this carry touches. A refuter pointed out that probing only `book_owner` proves the carried
    # subgraph loads and says nothing about the other seven, which load around it.
    import importlib

    for dotted, cite in [
        ("src.security", "run_book.py:26"),
        ("src.utils.config", ":29"),
        ("src.utils.broker_profile", ":30"),
        ("src.mt5.mt5_real", ":31"),
        ("src.components.ultimate_book.book_owner", ":32"),
        ("src.components.ultimate_book.bridge", ":33"),
        ("src.components.ultimate_book.symbol_map", ":34"),
        ("src.components.ultimate_book.launcher", ":35"),
    ]:
        try:
            importlib.import_module(dotted)
        except BaseException as exc:  # noqa: BLE001 -- the operator needs the class name
            say(False, f"import {dotted} FAILED ({cite}): {type(exc).__name__}: {exc}")
            print("\n  STOP. run_book.py dies at module load in this state. The supervisor will "
                  "restart it every ~33 s and manage_open_positions will never run.")
            return FAIL
    say(True, "import every module run_book.py imports at module top  (:26-35)")

    try:
        from src.components.ultimate_book.book_owner import UltimateBookOwner
    except BaseException as exc:  # noqa: BLE001
        say(False, f"import UltimateBookOwner FAILED: {type(exc).__name__}: {exc}")
        return FAIL

    class _StubMT5:
        _mt5 = None

        def get_broker_offset_seconds(self):
            return 3 * 3600

    cfg = {"gtos_vnext_runtime": {"prop_safe_selector_daily_reset_timezone": "Europe/Prague"}}
    try:
        UltimateBookOwner(cfg, _StubMT5(), tempfile.mkdtemp(prefix="gtos_verify_"), namespace="verify_probe_ns")
        say(True, "construct UltimateBookOwner  (run_book.py:294)")
    except BaseException as exc:  # noqa: BLE001
        say(False, f"construct UltimateBookOwner FAILED: {type(exc).__name__}: {exc}")
        print("\n  STOP. run_book.py dies at startup in this state, before its first tick.")
        return FAIL
    return FAIL if problems_since(mark) else PASS


def _check_behaviour_inner(root: Path, plan: list[dict]) -> int:
    """The two defects, asserted by their behaviour rather than by their source text.

    Every block is wrapped. A TRUNCATED carried file can import and construct and then be missing
    the very method under test; an unhandled AttributeError here would exit 1, outside the
    documented {0, 2, 3}, and read to an operator as "the tool is broken" rather than "the file on
    your host is incomplete".
    """
    mark = len(_problems)
    _isolate_from_mt5(root)

    # ---------------- item 1: the strand ----------------
    print("\n== behaviour, item 1: every broker-valid volume round-trips ==")
    from src.components.execution import ExecutionEngine

    class _SymInfo:
        def __init__(self, vmin, vstep, vmax=1000.0):
            self.volume_min, self.volume_step, self.volume_max = vmin, vstep, vmax

    norm = ExecutionEngine._normalize_volume
    geometries = [(0.01, 0.01), (0.1, 0.1), (0.01, 0.001), (1.0, 1.0),
                  (0.1, 0.01), (0.5, 0.1), (0.02, 0.02), (0.001, 0.001), (0.05, 0.05)]
    stranded, rounded_up, total = 0, 0, 0
    for vmin, vstep in geometries:
        si = _SymInfo(vmin, vstep)
        for k in range(2000):
            lots = round(vmin + k * vstep, 10)
            if lots > si.volume_max:
                break
            out = norm(None, lots, si, require_broker_geometry=True)
            total += 1
            if out is None or abs(out - lots) > 1e-12:
                stranded += 1
            elif out > lots + 1e-12:
                rounded_up += 1
    say(stranded == 0, f"{total - stranded}/{total} broker-valid volumes round-trip "
                       f"({stranded} stranded across {len(geometries)} geometries)")
    say(rounded_up == 0, f"no volume rounds UP ({rounded_up} did)")

    si = _SymInfo(0.01, 0.01)
    say(abs(norm(None, 0.03, si, require_broker_geometry=True) - 0.03) < 1e-12,
        "0.03 lots at (0.01, 0.01) normalizes to 0.03, not 0.02")
    mis = norm(None, 0.0349, si, require_broker_geometry=True)
    say(abs(mis - 0.03) < 1e-12, f"a genuinely mis-aligned 0.0349 still floors to 0.03 (got {mis})")

    # ---------------- item 2: the reset window ----------------
    print("\n== behaviour, item 2: the daily-loss reset instant, both accounts ==")
    import yaml
    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
    from src.utils.config import apply_profile_overrides

    class _OffsetMT5:
        """Pins the LIVE-detected server offset to +3, which is the measured value for both
        servers on the dates below. redacted_account's rule IS that offset, so the FN expectations
        are a function of it; FTMO's rule is not, which is the whole point."""
        _mt5 = None

        def get_broker_offset_seconds(self):
            return 3 * 3600

    cfg = yaml.safe_load((root / "config/agent_config.yaml").read_text(encoding="utf-8"))
    scratch = tempfile.mkdtemp(prefix="gtos_verify_gov_")

    # (profile, namespace, now, expected window start, why)
    CASES = [
        ("operator_profile", "operator_profile", "2026-10-27T21:30:00+00:00",
         "2026-10-26T23:00:00+00:00",
         "MISMATCH WINDOW (US DST on, EU off): FTMO is 00:00 CET = 23:00 UTC. Server "
         "midnight was 21:00 UTC, 30 min ago — the 2 h early reset this carry removes."),
        ("operator_profile", "operator_profile", "2026-03-15T21:30:00+00:00",
         "2026-03-14T23:00:00+00:00",
         "the other mismatch window, inside the sealed March month"),
        ("operator_profile", "operator_profile", "2026-07-15T23:30:00+00:00",
         "2026-07-15T22:00:00+00:00",
         "calendars agree: 00:00 CEST = 22:00 UTC, still 1 h after server midnight"),
        ("redacted_account", "redacted_account_live_bee34003", "2026-10-27T21:30:00+00:00",
         "2026-10-27T21:00:00+00:00",
         "redacted_account resets at 00:00 SERVER time — unchanged by this carry, and it must stay so"),
        ("redacted_account", "redacted_account_live_bee34003", "2026-07-15T23:30:00+00:00",
         "2026-07-15T21:00:00+00:00",
         "redacted_account, calendars agreeing — still server midnight"),
    ]
    for profile, namespace, iso, expect, why in CASES:
        merged = apply_profile_overrides(cfg, profile)
        rt = merged.get("gtos_vnext_runtime", merged)
        engine = UltimateBookLiveEngine(rt, _OffsetMT5(), scratch, namespace=namespace)
        now = datetime.fromisoformat(iso)
        got = engine._governor._reset_window_start_utc(now).astimezone(timezone.utc)
        ok = got == datetime.fromisoformat(expect)
        say(ok, f"{profile:<22} now={iso}  window_start={got.isoformat()}"
                f"{'' if ok else '  EXPECTED ' + expect}\n           {why}")

    merged = apply_profile_overrides(cfg, "operator_profile")
    rt = merged.get("gtos_vnext_runtime", merged)
    say(rt.get("prop_safe_selector_daily_reset_timezone") == "Europe/Prague",
        "the FTMO rule comes from the profile the host already ships — no config edit, "
        "no decision-contract exposure")
    merged_fn = apply_profile_overrides(cfg, "redacted_account")
    rt_fn = merged_fn.get("gtos_vnext_runtime", merged_fn)
    say(rt_fn.get("prop_safe_selector_daily_reset_timezone") is None
        and rt_fn.get("governor_daily_reset_rule") is None,
        "the redacted_account profile declares no rule, so its governor keeps server midnight")

    # ---------------- item 4: the monitor's window ----------------
    print("\n== behaviour, item 4: the monitor's daily-loss window (stage D) ==")
    monitor = root / ".tools/monitor_books.py"
    carried_sha = _sha(plan, ".tools/monitor_books.py")
    if sha256_of(monitor) != carried_sha:
        say(None, "stage D not applied — monitor_books.py is not at the carried sha; skipping")
    else:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_gtos_monitor_books_probe", monitor)
        mb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mb)
        now = datetime.fromisoformat("2026-10-27T21:30:00+00:00")
        got_ftmo = mb.daily_reset_window_start_utc("FTMO", now)
        got_fn = mb.daily_reset_window_start_utc("redacted_account", now)
        say(got_ftmo == datetime.fromisoformat("2026-10-26T23:00:00+00:00"),
            f"monitor FTMO window_start={got_ftmo.isoformat()} — agrees with the governor")
        say(got_fn == datetime.fromisoformat("2026-10-27T21:00:00+00:00"),
            f"monitor redacted_account window_start={got_fn.isoformat()} — server midnight, unchanged")
        nov = datetime.fromisoformat("2026-11-15T22:30:00+00:00")
        say(abs(mb.server_offset_hours("FTMO", nov) - 2.0) < 1e-9,
            "the server offset is +2 after 2026-11-01, not the struck hardcoded 3")

    return FAIL if problems_since(mark) else PASS


def check_behaviour(root: Path, plan: list[dict]) -> int:
    """Guard rail around :func:`_check_behaviour_inner`.

    A carried file that is PRESENT but TRUNCATED can import and construct and then be missing the
    very method under test. An unhandled ``AttributeError`` in the inner check would exit **1** —
    outside the documented ``{0, 2, 3}`` — and read to an operator as "the tool is broken" rather
    than "the file on your host is incomplete", which is the opposite of the truth.
    """
    try:
        return _check_behaviour_inner(root, plan)
    except BaseException as exc:  # noqa: BLE001
        say(False, f"behaviour check could not complete: {type(exc).__name__}: {exc}")
        print("\n  STOP. This usually means a carried file is PRESENT but INCOMPLETE — a truncated "
              "copy imports and constructs and then has no such attribute. Run "
              "`--check postflight`, which compares bytes and will name the file.")
        return FAIL


def check_stage_d(root: Path, plan: list[dict]) -> int:
    """Stage D only: is the carried monitor in place, and does it agree with the governor?

    ``--check behaviour`` deliberately SKIPS stage D when it is absent (``say(None, ...)``), which
    is right at §6 and wrong at §10 — it exits 0 whether or not the monitor landed, so §10 had no
    exit code that meant anything. This is the gate for §10.
    """
    mark = len(_problems)
    print("\n== stage D: the monitor's daily-loss window ==")
    rec = next((r for r in plan if r["repo_path"] == ".tools/monitor_books.py"), None)
    if rec is None:
        say(False, "the manifest has no stage-D entry")
        return FAIL
    got = sha256_of(root / rec["repo_path"])
    if got != rec["sha256_after_carry"]:
        say(False, f".tools/monitor_books.py is not carried (sha256={got})")
        return FAIL
    say(True, ".tools/monitor_books.py is at the carried sha")
    say(not (sha256_of(root / "src/utils/broker_clock.py") != _sha(plan, "src/utils/broker_clock.py")),
        "broker_clock carried — the monitor imports it at module top, UNGUARDED, so without it "
        "the monitor daemon crash-loops")
    if problems_since(mark):
        return FAIL
    rc = check_behaviour(root, plan)
    return FAIL if (problems_since(mark) or rc != PASS) else PASS


CHECKS = {
    "stage-d": check_stage_d,
    "preflight": check_preflight,
    "postflight": check_postflight,
    "imports": check_imports,
    "behaviour": check_behaviour,
    "rollback": check_rollback,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", required=True, choices=sorted(CHECKS) + ["all"])
    ap.add_argument("--allow-any-interpreter", action="store_true",
                    help="skip the venv check. For running this on the build laptop, NOT on the host.")
    args = ap.parse_args()

    root = resolve_repo_root()
    if not args.allow_any_interpreter:
        check_interpreter(root)
    print(f"repo root : {root}")
    print(f"python    : {sys.version.split()[0]}  ({sys.executable})")
    try:
        plan = load_plan(root)
    except BaseException as exc:  # noqa: BLE001
        print(f"[ STOP ] could not read the carry manifests: {type(exc).__name__}: {exc}")
        print("         The package is incomplete or its schema has changed. Do not copy anything.")
        return FAIL

    if args.check == "all":
        # preflight is a BEFORE check and cannot pass after a correct carry; excluded on purpose.
        order = ["postflight", "imports", "behaviour"]
    else:
        order = [args.check]

    rc = PASS
    for name in order:
        rc = max(rc, CHECKS[name](root, plan))

    print()
    if _problems:
        print(f"RESULT: FAIL — {len(_problems)} problem(s):")
        for p in _problems:
            print("  -", p.splitlines()[0])
        return FAIL
    print(f"RESULT: PASS ({', '.join(order)})")
    return PASS


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Enumerate every partial-application state of the activation carry, and MEASURE it.

Session S's carry shipped an ordering table whose most dangerous row was wrong, because it
traced a call-site consequence and never asked whether control reaches the call site. The
fix S applied was to enumerate the permutations on the reconstructed lineage instead of
reasoning about them. This does the same for the composed carry.

For every subset of the carried files, a fresh VPS-lineage tree is materialised, the subset
is copied in, and ``run_book.py``'s own startup path is exercised in a SUBPROCESS (so one
failure cannot poison the next). The verdict is the process's exit code, which is exactly
what the supervisor sees.

**Probing the import graph alone is not enough, and the difference is a factor of two.**
An import-only probe reports 8 of 32 states fatal; carrying on to the first construction —
which ``run_book.py:294`` also does unguarded — reports **16**. The extra eight are
``book_engine.py`` carried without ``governor_state.py``: they import perfectly and then
die on ``TypeError: unexpected keyword argument 'reset_rule'``.

Run from the repo root::

    python3 docs/audits/fable5-vision-audit-20260725/phase5/activation_carry/receipts/enumerate_partial_states.py

Writes PARTIAL_STATES.json next to itself. Nothing here touches a broker: the adapter is a
stub object with no MT5 behind it and ``connect()`` is never called.
"""

from __future__ import annotations

import itertools
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CARRY = HERE.parent
REPO = CARRY.parents[4]
LINEAGE = "redacted_host87668c5d503b52925d10be7dfb66540"

S_CARRY_REF = "phase4/packet-unblock"
S_CARRY_DIR = "docs/audits/fable5-vision-audit-20260725/phase4/packet_carry/files"

# (short id, destination inside the tree, source file, stage)
#
# `mb` (stage D) was added after a refuter found a THIRD fatal invariant the first version of this
# enumeration was blind to by construction: the carried monitor does `sys.path.insert(0, REPO_ROOT)`
# and then imports `src.utils.broker_clock` at module top, UNGUARDED. It is a supervisor-restarted
# live process, so `mb` without `bc` is a permanent crash loop of the ALERTING layer -- which is the
# thing watching the daily-loss rule of the account being armed.
AC_FILES = [
    ("bc", "src/utils/broker_clock.py", CARRY / "files/broker_clock.py", "A"),
    ("gs", "src/components/ultimate_book/governor_state.py", CARRY / "files/governor_state.py", "A"),
    ("be", "src/components/ultimate_book/book_engine.py", CARRY / "files/book_engine.py", "A"),
    ("ex", "src/components/execution.py", CARRY / "files/execution.py", "B"),
    ("mb", ".tools/monitor_books.py", CARRY / "files/monitor_books.py", "D"),
]

# Session S's carry, read out of git so this runs before the branches are integrated.
S_FILES = [
    ("rlp", "src/components/ultimate_book/runtime_learning_packet.py", "runtime_learning_packet.py"),
    ("pe", "src/components/ultimate_book/packet_economics.py", "packet_economics.py"),
    ("pg", "src/components/ultimate_book/packet_guard.py", "packet_guard.py"),
    ("bo", "src/components/ultimate_book/book_owner.py", "book_owner.py"),
]

# Two stages, because "it imports" is NOT "the book starts".
#
# Session S's ordering table was wrong because it traced a call-site consequence and never
# asked whether control reaches the call site. The inverse error is just as easy: probing
# only the import graph would report `book_engine` carried WITHOUT `governor_state` as
# healthy, when in fact the new `reset_rule=` keyword raises TypeError inside
# `UltimateBookLiveEngine.__init__` -- reached from `UltimateBookOwner.__init__`
# (book_owner.py:150), reached from `run_book.py:294`, which is OUTSIDE any try. The
# process dies at startup instead of at import, and the supervisor sees the same thing.
#
# So stage 2 constructs the owner with a stub adapter and a scratch repo root. Nothing here
# can reach a broker: the adapter is a bare object, `mt5.connect()` is never called, and
# run_book.py does its connect long before this line.
PROBE = r"""
import sys, tempfile, types
sys.path.insert(0, %r)
sys.modules.setdefault("MetaTrader5", types.ModuleType("MetaTrader5"))

# stage 1 -- run_book.py:32, the unguarded module-top import.
from src.components.ultimate_book.book_owner import UltimateBookOwner

# stage 2 -- run_book.py:294, the first construction, also unguarded.
class _StubMT5:
    _mt5 = None
    def get_broker_offset_seconds(self): return 3 * 3600

cfg = {"gtos_vnext_runtime": {"prop_safe_selector_daily_reset_timezone": "Europe/Prague"}}
UltimateBookOwner(cfg, _StubMT5(), tempfile.mkdtemp(), namespace="probe_ns")

# stage 3 -- the monitor daemon, a SEPARATE live process the supervisor also keeps alive. It is
# not on the book's import graph, so stages 1-2 are blind to it; its own module-load failure is a
# permanent crash loop of the alerting layer. Import only: `main()` is behind `if __name__`.
import importlib.util, os
_mon = os.path.join(%r, ".tools", "monitor_books.py")
if os.path.isfile(_mon):
    _spec = importlib.util.spec_from_file_location("_probe_monitor_books", _mon)
    _m = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_m)
print("STARTED")
"""


def base_tree(dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    tar = subprocess.run(["git", "archive", LINEAGE, "src", ".tools/monitor_books.py"], cwd=REPO,
                         check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(dst)], input=tar, check=True)


def s_carry_bytes(name: str) -> bytes | None:
    proc = subprocess.run(["git", "show", f"{S_CARRY_REF}:{S_CARRY_DIR}/{name}"],
                          cwd=REPO, capture_output=True)
    return proc.stdout if proc.returncode == 0 else None


def probe(tree: Path) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-c", PROBE % (str(tree), str(tree))],
                          capture_output=True, text=True, cwd=str(REPO))
    if proc.returncode == 0:
        return 0, "STARTED"
    tail = [ln for ln in proc.stderr.strip().splitlines() if ln.strip()]
    return proc.returncode, (tail[-1] if tail else "unknown failure")


def main() -> int:
    s_available = {sid: s_carry_bytes(name) for sid, _, name in S_FILES}
    have_s = all(v is not None for v in s_available.values())
    print(f"Session S carry readable from {S_CARRY_REF}: {have_s}")

    results = []
    scratch = Path(tempfile.mkdtemp(prefix="gtos_partial_"))
    try:
        for r in range(len(AC_FILES) + 1):
            for subset in itertools.combinations(AC_FILES, r):
                for with_s in ([False, True] if have_s else [False]):
                    tree = scratch / "t"
                    shutil.rmtree(tree, ignore_errors=True)
                    base_tree(tree)
                    if with_s:
                        for sid, dest, _name in S_FILES:
                            (tree / dest).write_bytes(s_available[sid])
                    for _sid, dest, src, _stage in subset:
                        (tree / dest).parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(src, tree / dest)
                    rc, msg = probe(tree)
                    ids = "+".join(s for s, *_ in subset) or "(none)"
                    results.append({
                        "ac_files": [s for s, *_ in subset],
                        "session_S_packet_carry_applied": with_s,
                        "label": f"AC[{ids}]" + (" + S[full]" if with_s else " + S[none]"),
                        "book_starts": rc == 0,
                        "exit_code": rc,
                        "failure": None if rc == 0 else msg,
                    })
                    flag = "starts" if rc == 0 else "DIES  "
                    print(f"  {flag}  AC[{ids:<20}] S={'yes' if with_s else 'no ':<3}  {'' if rc==0 else msg[:110]}")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    starts = sum(1 for r in results if r["book_starts"])
    payload = {
        "schema": "gtos.phase5.activation_carry_partial_states.v1",
        "lineage_commit": LINEAGE,
        "session_S_carry_included": have_s,
        "probe": ("stage 1: import UltimateBookOwner (run_book.py:32). stage 2: construct it with a stub adapter (run_book.py:294). Both are unguarded on the live path, so the exit code IS what the supervisor sees."),
        "total_states": len(results),
        "states_that_start": starts,
        "states_that_die_before_the_first_tick": len(results) - starts,
        "results": results,
    }
    (HERE / "PARTIAL_STATES.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\n{starts}/{len(results)} states start; {len(results)-starts} die before the first tick")
    return 0


if __name__ == "__main__":
    sys.exit(main())

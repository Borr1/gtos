#!/usr/bin/env python3
"""Build the Session AC activation carry, mechanically, from the live VPS lineage.

Nothing in ``files/`` is hand-written. Each carried file is either

* copied byte-identical from this repo's mainline (``broker_clock.py``,
  ``governor_state.py``), or
* constructed here by applying one named, anchored edit to the **live host's own copy**
  of the file (``execution.py``, ``book_engine.py``, ``monitor_books.py``).

The anchors are exact full-line strings taken from the lineage, so a silent mismatch is
impossible: every substitution asserts it matched exactly once.

Lineage = commit ``redacted_host`` (``origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18``),
verified byte-identical to the three files fetched read-only from the running host on
2026-07-29 and to the 2026-07-26 working-tree export for ``.tools/monitor_books.py``.

Run from the repo root::

    python3 docs/audits/fable5-vision-audit-20260725/phase5/activation_carry/build_carry.py

Requires ``_vps_lineage/`` (the fetched host files) or falls back to ``git show redacted_host:``.
Writes ``files/``, ``diffs/`` and ``MANIFEST.json``; exits non-zero if any round-trip fails.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
LINEAGE_COMMIT = "redacted_host87668c5d503b52925d10be7dfb66540"
S_CARRY_REF = "phase4/packet-unblock"
S_CARRY_MANIFEST = "docs/audits/fable5-vision-audit-20260725/phase4/packet_carry/MANIFEST.json"
LINEAGE_REF = "origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18"

FILES = HERE / "files"
DIFFS = HERE / "diffs"


# --------------------------------------------------------------------------------------
# lineage access
# --------------------------------------------------------------------------------------

def lineage_bytes(repo_path: str) -> bytes:
    """The live host's copy of ``repo_path``.

    Prefer the read-only fetch in ``_vps_lineage/`` when it is present (it is the actual
    host file, not a proxy); otherwise reconstruct from the lineage commit. The two are
    asserted equal when both exist, so the proxy can never silently drift.
    """
    out = subprocess.run(
        ["git", "show", f"{LINEAGE_COMMIT}:{repo_path}"],
        cwd=REPO, check=True, capture_output=True,
    ).stdout
    fetched = REPO / "_vps_lineage" / Path(repo_path).name
    if fetched.is_file():
        got = fetched.read_bytes()
        if got != out:
            raise SystemExit(
                f"FATAL: _vps_lineage/{fetched.name} differs from {LINEAGE_COMMIT}:{repo_path}. "
                "The host has diverged from the lineage proxy; re-derive the carry before shipping."
            )
    return out


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def s_carry_files() -> list[dict]:
    """Session S's file list, read from its own manifest wherever that currently lives."""
    on_disk = REPO / S_CARRY_MANIFEST
    if on_disk.is_file():
        raw = on_disk.read_bytes()
        origin = S_CARRY_MANIFEST
    else:
        proc = subprocess.run(["git", "show", f"{S_CARRY_REF}:{S_CARRY_MANIFEST}"],
                              cwd=REPO, capture_output=True)
        if proc.returncode != 0:
            raise SystemExit(
                f"FATAL: Session S's manifest is neither on disk nor at {S_CARRY_REF}. "
                "The composed carry cannot be built without it."
            )
        raw = proc.stdout
        origin = f"{S_CARRY_REF}:{S_CARRY_MANIFEST}"
    data = json.loads(raw)
    print(f"  Session S manifest read from {origin} ({len(data['files'])} files)")
    return [
        {
            "copy_order": rec["copy_order"],
            "destination_on_vps": rec["destination_on_vps"],
            "is_new_file_on_vps": rec["is_new_file_on_vps"],
            "sha256_before_expected": rec.get("sha256_before_expected_at_redacted_host"),
            "sha256_after_carry": rec["sha256_after_carry"],
            "source_in_this_repo": rec["source_in_this_repo"],
        }
        for rec in data["files"]
    ]


def sub_once(text: str, old: str, new: str, *, what: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"FATAL: anchor for {what!r} matched {n} times, expected exactly 1")
    return text.replace(old, new, 1)


def line_of(text: str, needle: str, *, occurrence: int = 1) -> int:
    """1-indexed line number of the ``occurrence``-th line containing ``needle``."""
    seen = 0
    for i, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            seen += 1
            if seen == occurrence:
                return i
    raise SystemExit(f"FATAL: {needle!r} occurrence {occurrence} not found")


def all_lines_with(text: str, needle: str) -> list[int]:
    return [i for i, line in enumerate(text.splitlines(), start=1) if needle in line]


# --------------------------------------------------------------------------------------
# item 1 -- the strand fix (Session T's, on phase4/canary-package), re-cited for the host
# --------------------------------------------------------------------------------------

EXEC_CONST_ANCHOR = (
    'logger = logging.getLogger(__name__)\n'
    '\n'
    'CHECKPOINT_PATH = "knowledge_base/meta/execution_checkpoint.json"\n'
)

EXEC_CONST_NEW = (
    'logger = logging.getLogger(__name__)\n'
    '\n'
    '#: Step-count tolerance for broker volume-step alignment. See `_normalize_volume`:\n'
    '#: a quotient that is mathematically an exact integer can land a few ULPs below one in\n'
    '#: binary floating point, and truncating it strands a position that cannot be closed.\n'
    '#: Sized to absorb float error (~1e-12 at ten thousand steps) without being large enough\n'
    '#: to promote a genuinely mis-aligned volume to the next step.\n'
    '_VOLUME_STEP_EPSILON = 1e-9\n'
    '\n'
    'CHECKPOINT_PATH = "knowledge_base/meta/execution_checkpoint.json"\n'
)

EXEC_NORM_ANCHOR = (
    '            lots = min(lots, volume_max)\n'
    '            steps = math.floor((lots - volume_min) / volume_step)\n'
    '            normalized = volume_min + max(0, steps) * volume_step\n'
    '            return round(normalized, 8)\n'
)

# @@GATE@@ and @@PRODUCERS@@ are resolved against the FINISHED file, so the comment cites
# the line numbers a reader of the carried file will actually see.
EXEC_NORM_NEW = '''            lots = min(lots, volume_max)
            # `math.floor` on a raw binary quotient truncates a value that is
            # mathematically an exact integer. With volume_min == volume_step == 0.01,
            # `(0.03 - 0.01) / 0.01` is 1.9999999999999996, so 0.03 normalizes to 0.02
            # — and `_close_request_execution_geometry:@@GATE@@` then refuses the close,
            # because it demands the normalized volume equal the requested one to 1e-9.
            #
            # That is a STRAND, not a rounding nit. Nine close producers route through
            # that check (`:@@PRODUCERS@@`), the live book always takes the
            # verified-geometry branch (`ultimate_book/execution_packets.py:318-319` sets
            # the selected-cell risk fields that `_trade_requires_verified_broker_geometry`
            # keys on), and each producer returns before `safe_place_order` — so nothing
            # reaches the activation layer and no retry can ever succeed, because the next
            # tick recomputes the identical volume.
            #
            # Measured on THIS file (B333, re-measured on the host lineage 2026-07-29,
            # B551): 33 of 300 two-decimal lot sizes are affected at (0.01, 0.01), and it
            # is worse on coarser geometry — 253 of 500 at (0.10, 0.10). 44 of 327 real
            # broker close deals in `vps-export-20260725` carried an affected volume.
            #
            # The epsilon is a step-count tolerance, not a volume tolerance. It can only
            # promote a quotient already within 1e-9 of an integer, i.e. a lot size
            # within 1e-11 of the next step — far below any broker's volume resolution —
            # so a genuinely mis-aligned volume still rounds DOWN, and the normalized
            # result can never exceed the request.
            steps = math.floor((lots - volume_min) / volume_step + _VOLUME_STEP_EPSILON)
            normalized = volume_min + max(0, steps) * volume_step
            normalized = round(normalized, 8)
            # Never hand back more than was asked for, whatever the arithmetic did.
            return normalized if normalized <= lots + 1e-12 else round(lots, 8)
'''


def build_execution() -> bytes:
    src = lineage_bytes("src/components/execution.py").decode("utf-8")
    out = sub_once(src, EXEC_CONST_ANCHOR, EXEC_CONST_NEW, what="execution._VOLUME_STEP_EPSILON")
    out = sub_once(out, EXEC_NORM_ANCHOR, EXEC_NORM_NEW, what="execution._normalize_volume")
    gate = line_of(out, "    def _close_request_execution_geometry(")
    producers = all_lines_with(out, "close_geometry = self._close_request_execution_geometry(")
    if len(producers) != 9:
        raise SystemExit(f"FATAL: expected 9 close producers, found {len(producers)}")
    out = out.replace("@@GATE@@", str(gate)).replace("@@PRODUCERS@@", ", ".join(map(str, producers)))
    return out.encode("utf-8")


# --------------------------------------------------------------------------------------
# item 2 -- B56, the daily-loss reset rule
# --------------------------------------------------------------------------------------

ENGINE_ANCHOR = '''        #  - daily_reset_offset_hours: FTMO/FN server = UTC+3, so the daily-loss window resets at
        #    21:00 UTC; the start-of-day anchor keys on the server-local date (matches monitor_books).
        _gov_init_bal = self.config.get("governor_static_initial_balance", 100000.0)
        _gov_reset_off = self.config.get("governor_daily_reset_offset_hours", 3.0)
        self._governor = GovernorStateBuilder(
            repo_root, namespace=namespace,
            static_initial_balance=_gov_init_bal, daily_reset_offset_hours=_gov_reset_off,
            offset_provider=self._live_broker_offset_hours)
'''

# Mainline's own B56 block, with the profile citation pointed at the profile THIS HOST
# runs (`operator_profile.yaml`) rather than the replay profile (`ftmo.yaml`).
ENGINE_NEW = '''        #  - daily_reset_offset_hours: the STATIC fallback only. The reset window is resolved per
        #    account at runtime; see reset_rule below and GovernorStateBuilder._effective_offset_h.
        #  - reset_rule: THE ACCOUNT'S OWN daily-loss reset calendar, corrected 2026-07-26 (B56).
        #    The two firms do not share a rule and the difference is not cosmetic:
        #      redacted_account resets at 00:00 SERVER time (GMT+2/+3) -> no rule, the detected offset is it.
        #      FTMO       resets at 00:00 CE(S)T, which is NOT its server clock. FTMO's MT5 server
        #                 runs the US DST calendar while CE(S)T runs the EU one, so server midnight
        #                 is 1 h early normally and 2 h early for ~4 weeks a year.
        #    Sourced from the profile this account already ships -- the live FTMO profile
        #    config/profiles/operator_profile.yaml:87 declares
        #    `prop_safe_selector_daily_reset_timezone: Europe/Prague` and :104 records the firm's
        #    rule verbatim (`daily_reset_time: 00:00 CE(S)T`). Both FTMO profiles are
        #    decision-contract-bound (H1), so this READS the key rather than adding one; an account
        #    whose profile is silent (redacted_account.yaml) keeps server midnight, which is its rule.
        _gov_init_bal = self.config.get("governor_static_initial_balance", 100000.0)
        _gov_reset_off = self.config.get("governor_daily_reset_offset_hours", 3.0)
        _gov_reset_rule = (self.config.get("governor_daily_reset_rule")
                           or self.config.get("prop_safe_selector_daily_reset_timezone")
                           or None)
        self._governor = GovernorStateBuilder(
            repo_root, namespace=namespace,
            static_initial_balance=_gov_init_bal, daily_reset_offset_hours=_gov_reset_off,
            offset_provider=self._live_broker_offset_hours,
            reset_rule=_gov_reset_rule)
'''


def build_book_engine() -> bytes:
    src = lineage_bytes("src/components/ultimate_book/book_engine.py").decode("utf-8")
    out = sub_once(src, ENGINE_ANCHOR, ENGINE_NEW, what="book_engine.reset_rule")
    return out.encode("utf-8")


# --------------------------------------------------------------------------------------
# item 4 -- the monitor's daily-loss window (same defect, in the alerting layer)
# --------------------------------------------------------------------------------------

MON_CONST_ANCHOR = '''GROSS_CAP = 0.04
SRV_OFFSET_H = 3   # FTMO/FN server = UTC+3 (EEST)
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
'''

MON_CONST_NEW = '''GROSS_CAP = 0.04
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
from src.utils.broker_clock import (  # noqa: E402
    broker_epoch_to_utc,
    daily_reset_offset_hours,
    offset_seconds_at_utc,
    resolve_rule,
)

# Struck 2026-07-29 (B56 carry): `SRV_OFFSET_H = 3   # FTMO/FN server = UTC+3 (EEST)`.
# It was wrong in two independent ways, and both of them move the daily-loss alert in the
# SAME dangerous direction -- the monitor believes the day has reset while the firm is
# still counting.
#
#  1. The label was wrong and the number is dated. Both servers are MEASURED to run the
#     **US** DST calendar (America/New_York + 7 h; 81 weekly session boundaries per broker),
#     not EET/EEST. They drop to +2 on **2026-11-01** while a hardcoded 3 would not, so from
#     that date the window would open a further hour early, every night, silently.
#  2. The server clock is not FTMO's reset rule at all. FTMO resets at 00:00 CE(S)T
#     (config/profiles/operator_profile.yaml:104); redacted_account resets at 00:00 server
#     time. Server midnight is therefore 1 h before FTMO's real reset normally, and 2 h
#     before it for the ~4 weeks a year the US and EU calendars disagree.
#
# The window is now computed as an INSTANT rather than a date, because the two rules do not
# share a calendar and comparing a CE(S)T date against a broker-wall date would be a type
# error wearing a fix. Deal times are raw broker epochs, so they are converted with the
# server rule before the comparison -- never by decoding them as UTC.
DAILY_RESET_RULE_BY_LABEL = {
    "FTMO": "Europe/Prague",   # 00:00 CE(S)T, academy.ftmo.com/lesson/maximum-daily-loss/
    "redacted_account": None,        # 00:00 server time, help.redacted_account.com/en/articles/8394309
}
MT5_SERVER_BY_LABEL = {"FTMO": "FTMO-Server3", "redacted_account": "redacted_account-Server 2"}


def server_offset_hours(label, now_utc):
    """The MT5 server's own offset from UTC, measured, DST-correct."""
    return offset_seconds_at_utc(now_utc, resolve_rule(MT5_SERVER_BY_LABEL[label])) / 3600.0


def daily_reset_window_start_utc(label, now_utc):
    """UTC instant at which THIS FIRM'S current daily-loss window began.

    Raises rather than guessing: an unregistered label or server comes out of ``broker_clock``
    as ``UnknownBrokerClockError``. A wrong window is invisible until it costs an account, and a
    guessed one is exactly the defect this replaces.

    Be clear about what that costs, because an earlier draft of this docstring claimed
    containment that does not exist: ``snap`` has no ``except`` and its caller does not wrap it,
    so a raise here kills the monitor loop. The supervisor restarts it within ~30 s, so the blast
    radius is a crash loop rather than silent wrong alerting -- the right direction, but it is a
    crash, not a graceful degradation. Both server strings and both rules resolve today.
    """
    hours = daily_reset_offset_hours(now_utc, DAILY_RESET_RULE_BY_LABEL[label])
    if hours is None:
        hours = server_offset_hours(label, now_utc)
    local_now = now_utc + dt.timedelta(hours=hours)
    local_midnight = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return local_midnight - dt.timedelta(hours=hours)
'''

MON_SNAP_ANCHOR = '''        now = dt.datetime.now(dt.timezone.utc)
        srv_today = (now + dt.timedelta(hours=SRV_OFFSET_H)).date()
        deals = mt5.history_deals_get(now - dt.timedelta(hours=24), now + dt.timedelta(hours=13)) or []
        realized_today = sum(float(d.profit) + float(getattr(d, "swap", 0)) + float(getattr(d, "commission", 0))
                             for d in deals if getattr(d, "entry", 0) == 1
                             and dt.datetime.fromtimestamp(d.time, dt.timezone.utc).date() == srv_today)
'''

MON_SNAP_NEW = '''        now = dt.datetime.now(dt.timezone.utc)
        window_start = daily_reset_window_start_utc(label, now)
        srv_rule = resolve_rule(MT5_SERVER_BY_LABEL[label])
        # 30 h back, not 24. The window itself is always < 24 h old (max measured 23.50 h), but
        # history_deals_get's bounds are interpreted as BROKER wall clock, so passing UTC shifts
        # the requested range by the server offset (~3 h). 24 h of window plus a 3 h shift does
        # not fit in a 24 h request. The filter below is exact, so over-fetching costs nothing
        # and under-fetching would silently drop realized loss out of the daily-limit alert.
        deals = mt5.history_deals_get(now - dt.timedelta(hours=30), now + dt.timedelta(hours=13)) or []
        realized_today = sum(float(d.profit) + float(getattr(d, "swap", 0)) + float(getattr(d, "commission", 0))
                             for d in deals if getattr(d, "entry", 0) == 1
                             and broker_epoch_to_utc(d.time, srv_rule) >= window_start)
'''


def build_monitor_books() -> bytes:
    src = lineage_bytes(".tools/monitor_books.py").decode("utf-8")
    out = sub_once(src, MON_CONST_ANCHOR, MON_CONST_NEW, what="monitor_books.SRV_OFFSET_H")
    out = sub_once(out, MON_SNAP_ANCHOR, MON_SNAP_NEW, what="monitor_books.snap window")
    return out.encode("utf-8")


# --------------------------------------------------------------------------------------
# the plan
# --------------------------------------------------------------------------------------

#: ``copy_order`` is the ONLY ordering that is safe on the host. See
#: ORDERING_AND_PARTIAL_STATES.md -- every dependency points backwards in this list.
PLAN = [
    dict(
        copy_order=1, stage="A",
        repo_path="src/utils/broker_clock.py",
        destination=r"src\utils\broker_clock.py",
        builder=lambda: (REPO / "src/utils/broker_clock.py").read_bytes(),
        is_new_on_vps=True,
        source_kind="mainline byte-identical",
        note=("Shared prerequisite. Byte-identical to Session S's packet carry "
              "(phase4/packet_carry/files/broker_clock.py) -- install ONCE. stdlib only "
              "(dataclasses, datetime); it deliberately does not use zoneinfo, because the "
              "host venv has no tzdata (pip freeze, 27 packages, verified)."),
    ),
    dict(
        copy_order=2, stage="A",
        repo_path="src/components/ultimate_book/governor_state.py",
        destination=r"src\components\ultimate_book\governor_state.py",
        builder=lambda: (REPO / "src/components/ultimate_book/governor_state.py").read_bytes(),
        is_new_on_vps=False,
        source_kind="mainline byte-identical",
        note=("B56. Mainline differs from the host copy by the reset-rule change and nothing "
              "else, so it carries whole. Imports broker_clock UNGUARDED -- deliberate: a "
              "missing broker_clock must fail closed and loudly, not silently revert to the "
              "early-reset behaviour this fixes."),
    ),
    dict(
        copy_order=3, stage="A",
        repo_path="src/components/ultimate_book/book_engine.py",
        destination=r"src\components\ultimate_book\book_engine.py",
        builder=build_book_engine,
        is_new_on_vps=False,
        source_kind="host file + 1 anchored edit",
        note=("B56, SURGICAL. Mainline's book_engine.py must NOT be copied: it also carries "
              "D3, D10 and the bar-time latch, and needs two symbols this host does not have. "
              "`config_safety_flag` is imported from bridge at MODULE level (mainline "
              "book_engine.py:30), so copying the file is an ImportError at module load -- the "
              "catastrophic class. `precount_intent_filter` is a DEFERRED in-function import "
              "(mainline :829), so it would raise later, at admission time, on the running "
              "book; corrected here after a refuter measured the difference."),
    ),
    dict(
        copy_order=4, stage="B",
        repo_path="src/components/execution.py",
        destination=r"src\components\execution.py",
        builder=build_execution,
        is_new_on_vps=False,
        source_kind="host file + 2 anchored edits",
        note=("The strand fix (Session T's, phase4/canary-package). Independent of stage A: "
              "adds one module constant and edits one method body; no new imports, no new "
              "call sites. The host file is 10,166 lines against mainline's 10,085, so the "
              "file itself cannot be copied."),
    ),
    dict(
        copy_order=5, stage="D",
        repo_path=".tools/monitor_books.py",
        destination=r".tools\monitor_books.py",
        builder=build_monitor_books,
        is_new_on_vps=False,
        source_kind="host file + 2 anchored edits",
        note=("Same B56 defect in the alerting layer, plus a dated hardcode that breaks on "
              "2026-11-01. Ordered LAST and gated separately: no book imports it, so it "
              "cannot affect a book restart, and the supervisor restarts it on its own "
              "within ~30 s. Needs broker_clock.py (stage A)."),
    ),
]


def sync_runbook_hashes(manifest: dict) -> None:
    """Rewrite the sha256 literals the runbook quotes, from the manifest.

    The runbook has to quote them: the operator's copy loop checks each file as it lands, and a
    check they cannot read is a check they will skip. But a hand-maintained duplicate of a hash
    is exactly how the first draft of this runbook came to quote a **fabricated** sha256 for
    ``book_engine.py`` -- the right 12-character prefix and 52 characters of nothing. So the
    duplicate is generated, and ``tests/ultimate_book/test_activation_carry_vps_lineage.py``
    fails if it ever drifts.
    """
    runbook = HERE / "ACTIVATION_CARRY_VPS_RUNBOOK.md"
    if not runbook.is_file():
        return
    truth = {rec["destination_on_vps"]: rec["sha256_after_carry"] for rec in manifest["files"]}
    for rec in manifest["composes_with"].get("session_S_files", []):
        truth.setdefault(rec["destination_on_vps"], rec["sha256_after_carry"])
    text = runbook.read_text(encoding="utf-8")
    changed = 0
    for dest, sha in re.findall(r'to="([^"]+)";\s+sha="([0-9a-f]{64})"', text):
        want = truth.get(dest)
        if want and want != sha:
            text = text.replace(sha, want)
            changed += 1
            print(f"  runbook hash refreshed: {dest}")
    orphans = set(re.findall(r"\b[0-9a-f]{64}\b", text)) - set(truth.values())
    if orphans:
        raise SystemExit(
            "FATAL: the runbook quotes sha256 values that are in no manifest: "
            + ", ".join(sorted(orphans))
        )
    if changed:
        runbook.write_text(text, encoding="utf-8")


def main() -> int:
    FILES.mkdir(parents=True, exist_ok=True)
    DIFFS.mkdir(parents=True, exist_ok=True)
    manifest_files = []
    failures = []

    for spec in PLAN:
        repo_path = spec["repo_path"]
        name = Path(repo_path).name
        before = None if spec["is_new_on_vps"] else lineage_bytes(repo_path)
        after = spec["builder"]()

        if b"\r\n" in after:
            failures.append(f"{name}: CRLF present in carried bytes")
        if after[:3] == b"\xef\xbb\xbf":
            failures.append(f"{name}: BOM present in carried bytes")
        try:
            compile(after.decode("utf-8"), name, "exec")
        except SyntaxError as exc:
            failures.append(f"{name}: does not compile: {exc}")

        (FILES / name).write_bytes(after)

        diff_name = repo_path.replace("/", "_").lstrip("._") + ".diff"
        if before is None:
            (DIFFS / diff_name).write_text(
                f"# {repo_path} is ABSENT on the host at {LINEAGE_COMMIT[:9]}; carried as a whole\n"
                f"# new file. sha256 {sha256(after)}\n",
                encoding="utf-8",
            )
        else:
            tmp_a = HERE / f".{name}.lineage.tmp"
            tmp_b = HERE / f".{name}.carried.tmp"
            tmp_a.write_bytes(before)
            tmp_b.write_bytes(after)
            proc = subprocess.run(
                # Bare `a/`/`b/` labels with NO trailing annotation: `git apply` takes the whole
                # rest of a `---`/`+++` line as the filename, so "  (redacted_host, the running host)"
                # made it report "No such file or directory" on a perfectly good diff. `patch`
                # splits on whitespace and never minded. Provenance moved to the preamble below,
                # which both tools skip.
                ["diff", "-u", "--label", f"a/{repo_path}", "--label", f"b/{repo_path}",
                 str(tmp_a), str(tmp_b)],
                capture_output=True, text=True,
            )
            preamble = (
                f"# {repo_path}\n"
                f"# a/ = the running host, {LINEAGE_COMMIT} "
                f"(sha256 {sha256(before)})\n"
                f"# b/ = the activation carry, Session AC "
                f"(sha256 {sha256(after)})\n"
                f"# applies with `patch -p1 -F 0` and with `git apply -p1`, zero fuzz.\n"
            )
            (DIFFS / diff_name).write_text(preamble + proc.stdout, encoding="utf-8")
            tmp_a.unlink()
            tmp_b.unlink()

        manifest_files.append({
            "copy_order": spec["copy_order"],
            "stage": spec["stage"],
            "source_in_this_repo":
                f"docs/audits/fable5-vision-audit-20260725/phase5/activation_carry/files/{name}",
            "diff_in_this_repo":
                f"docs/audits/fable5-vision-audit-20260725/phase5/activation_carry/diffs/{diff_name}",
            "destination_on_vps": spec["destination"],
            "repo_path": repo_path,
            "is_new_file_on_vps": spec["is_new_on_vps"],
            "sha256_before_expected": None if before is None else sha256(before),
            "sha256_after_carry": sha256(after),
            "bytes_before": None if before is None else len(before),
            "bytes_after": len(after),
            "crlf_present": False,
            "source_kind": spec["source_kind"],
            "note": spec["note"],
        })

    # Round-trip: the shipped diff, applied to the host's own file, must reproduce the
    # shipped file byte-for-byte. This is the property an operator relies on if they patch
    # instead of copy, and it is the one S's carry proved and shipped.
    for spec, rec in zip(PLAN, manifest_files):
        if spec["is_new_on_vps"]:
            continue
        before = lineage_bytes(spec["repo_path"])
        work = HERE / ".roundtrip.tmp"
        work.write_bytes(before)
        proc = subprocess.run(
            ["patch", "--no-backup-if-mismatch", "-s", "-F", "0", str(work),
             str(HERE / Path(rec["diff_in_this_repo"]).relative_to(
                 "docs/audits/fable5-vision-audit-20260725/phase5/activation_carry"))],
            capture_output=True, text=True,
        )
        got = work.read_bytes()
        work.unlink(missing_ok=True)
        if proc.returncode != 0:
            failures.append(f"{spec['repo_path']}: patch failed rc={proc.returncode} {proc.stderr.strip()}")
        elif sha256(got) != rec["sha256_after_carry"]:
            failures.append(f"{spec['repo_path']}: patch round-trip mismatch")
        else:
            print(f"  round-trip OK (zero fuzz): {spec['repo_path']}")

    manifest = {
        "schema": "gtos.phase5.activation_carry_manifest.v1",
        "session": "AC",
        "built_by": "docs/audits/fable5-vision-audit-20260725/phase5/activation_carry/build_carry.py",
        "vps_base_commit": LINEAGE_COMMIT,
        "vps_base_ref": LINEAGE_REF,
        "lineage_verified": (
            "governor_state.py, book_engine.py and execution.py fetched read-only from the "
            "running host 2026-07-29 are byte-identical to this commit; .tools/monitor_books.py "
            "is byte-identical to the 2026-07-26 working-tree export. Session S separately "
            "verified 63/63 files across src/components/ultimate_book/, src/utils/ and src/mt5/."
        ),
        "host_repo_root": r"C:\Users\MSI\Documents\ai-trading-agent",
        "host_interpreter": r"C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe",
        "host_interpreter_version": "3.13.13",
        "composes_with": {
            "session_S_packet_carry": "docs/audits/fable5-vision-audit-20260725/phase4/packet_carry/MANIFEST.json",
            "session_S_packet_carry_source_ref": S_CARRY_REF,
            "shared_file": "src/utils/broker_clock.py",
            # Pinned deliberately; bump ONLY when mainline broker_clock.py changes on
            # purpose. 2026-08-10 (wave-21 integration): bumped from 0f97bbb64bc55b02...
            # for the deliberate pre-2007 US-DST calendar truth repair (Uniform Time
            # Act 1987-2006 rule; pre-1987 refuses) merged from the wave-21 cost lanes.
            "shared_file_sha256": "78549c4d2b17b3d0078f918459c706b79de2eb8324cb92a2945725d6a1c2af8a",
            "shared_file_rule": (
                "Identical in both carries -- install ONCE. AFTER this carry it is no longer "
                "optional: S's packet_economics.py imports it inside a try, but this carry's "
                "governor_state.py imports it at module top, unguarded."
            ),
            # Copied from S's own manifest at build time so THIS manifest is self-sufficient:
            # the composed runbook quotes these hashes, and a hash nobody can check is how a
            # fabricated one ships. verify_carry.py prefers S's manifest when it is on disk and
            # asserts this copy agrees with it, so the duplication is a checked invariant.
            "session_S_files": s_carry_files(),
        },
        "files": manifest_files,
    }
    (HERE / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    sync_runbook_hashes(manifest)

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  -", f)
        return 1
    print(f"\nbuilt {len(manifest_files)} files, {len(manifest_files)} manifest entries, 0 failures")
    return 0


if __name__ == "__main__":
    sys.exit(main())

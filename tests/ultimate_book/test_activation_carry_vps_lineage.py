"""The Session AC activation carry, tested against the lineage it will actually run on.

The carry in ``docs/audits/fable5-vision-audit-20260725/phase5/activation_carry/`` is not
mainline code — it is a set of files destined for a live funded host whose tree differs from
this repo's. So the properties worth pinning are properties **of the carried artifacts**:

* the shipped diffs reconstruct the shipped files from the host's own bytes, zero fuzz;
* the shipped files carry the behaviour the carry exists for (no stranded volume, the right
  daily-loss reset instant for each firm);
* the two dependency invariants that make a partial copy fatal are real, and are the only
  two;
* the runbook does not contain the four defect classes that were found on that host.

Nothing here touches a broker or the network. The carried modules are loaded from a
temporary reconstruction of the lineage tree with ``MetaTrader5`` shadowed by an empty
module, so no MT5 handle can exist.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CARRY = REPO / "docs/audits/fable5-vision-audit-20260725/phase5/activation_carry"
S_CARRY = REPO / "docs/audits/fable5-vision-audit-20260725/phase4/packet_carry"
LINEAGE = "redacted_host87668c5d503b52925d10be7dfb66540"

pytestmark = pytest.mark.skipif(not CARRY.is_dir(), reason="activation carry not present")


def _git_show(rev_path: str) -> bytes | None:
    proc = subprocess.run(["git", "show", rev_path], cwd=REPO, capture_output=True)
    return proc.stdout if proc.returncode == 0 else None


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads((CARRY / "MANIFEST.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def lineage_available() -> bool:
    return _git_show(f"{LINEAGE}:src/components/execution.py") is not None


# --------------------------------------------------------------------------------------
# 1. the artifacts reconstruct
# --------------------------------------------------------------------------------------

def test_manifest_shas_match_the_shipped_files(manifest):
    """A manifest that disagrees with its own payload is worse than no manifest: the
    operator's postflight would pass on the wrong bytes."""
    for rec in manifest["files"]:
        shipped = REPO / rec["source_in_this_repo"]
        assert shipped.is_file(), f"{rec['source_in_this_repo']} missing"
        assert _sha(shipped.read_bytes()) == rec["sha256_after_carry"], rec["repo_path"]
        assert rec["crlf_present"] is False
        assert b"\r\n" not in shipped.read_bytes(), f"{rec['repo_path']}: CRLF would break the sha"


def test_every_shipped_file_compiles(manifest):
    for rec in manifest["files"]:
        src = (REPO / rec["source_in_this_repo"]).read_text(encoding="utf-8")
        compile(src, rec["repo_path"], "exec")


def test_diffs_apply_to_the_host_bytes_with_zero_fuzz(manifest, lineage_available):
    """`patch -F 0` against the host's own file must reproduce the shipped file exactly.

    This is the property an operator relies on if they patch instead of copy, and it is the
    reason Session I's carry applied clean on five files.
    """
    if not lineage_available:
        pytest.skip(f"lineage commit {LINEAGE[:9]} not in this object store")
    for rec in manifest["files"]:
        if rec["is_new_file_on_vps"]:
            continue
        before = _git_show(f"{LINEAGE}:{rec['repo_path']}")
        assert before is not None, rec["repo_path"]
        assert _sha(before) == rec["sha256_before_expected"], (
            f"{rec['repo_path']}: the recorded base sha is not the lineage's"
        )
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / Path(rec["repo_path"]).name
            work.write_bytes(before)
            proc = subprocess.run(
                ["patch", "--no-backup-if-mismatch", "-s", "-F", "0",
                 str(work), str(REPO / rec["diff_in_this_repo"])],
                capture_output=True, text=True,
            )
            assert proc.returncode == 0, f"{rec['repo_path']}: {proc.stderr or proc.stdout}"
            assert _sha(work.read_bytes()) == rec["sha256_after_carry"], (
                f"{rec['repo_path']}: patched result is not the shipped file"
            )


def test_book_engine_is_surgical_not_a_mainline_copy(manifest, lineage_available):
    """Copying mainline's ``book_engine.py`` to the host is an ImportError at module load.

    Mainline's file also carries D3, D10 and the bar-time latch, and imports
    ``config_safety_flag`` from ``bridge`` and ``precount_intent_filter`` from ``admission``.
    Neither symbol exists on the host lineage. This is the single most expensive mistake
    available in this carry, so it is pinned rather than described.
    """
    if not lineage_available:
        pytest.skip("lineage commit not available")
    carried = (CARRY / "files/book_engine.py").read_text(encoding="utf-8")
    assert "config_safety_flag" not in carried
    assert "precount_intent_filter" not in carried
    assert "_asymmetric_profile_guard" not in carried
    assert "reset_rule=_gov_reset_rule" in carried

    lineage_bridge = _git_show(f"{LINEAGE}:src/components/ultimate_book/bridge.py").decode()
    lineage_admission = _git_show(f"{LINEAGE}:src/components/ultimate_book/admission.py").decode()
    assert "def config_safety_flag" not in lineage_bridge, (
        "the host gained config_safety_flag; re-derive the carry"
    )
    assert "def precount_intent_filter" not in lineage_admission

    mainline = (REPO / "src/components/ultimate_book/book_engine.py").read_text(encoding="utf-8")
    assert "config_safety_flag" in mainline, (
        "mainline no longer needs the symbol the host lacks — the surgical carry may now be "
        "unnecessary; re-check before simplifying it away"
    )


def test_broker_clock_is_one_file_shared_with_the_packet_carry(manifest):
    """Both carries install ``src/utils/broker_clock.py``. If the two ever diverge, the
    operator installs one of them twice and the second copy silently wins."""
    shared = manifest["composes_with"]["shared_file_sha256"]
    assert _sha((CARRY / "files/broker_clock.py").read_bytes()) == shared
    assert _sha((REPO / "src/utils/broker_clock.py").read_bytes()) == shared, (
        "the carried broker_clock has drifted from mainline's"
    )
    s_manifest = S_CARRY / "MANIFEST.json"
    if not s_manifest.is_file():
        pytest.skip("Session S packet carry not in this tree yet")
    s = json.loads(s_manifest.read_text(encoding="utf-8"))
    s_bc = [r for r in s["files"] if r["destination_on_vps"].endswith("broker_clock.py")]
    assert len(s_bc) == 1
    assert s_bc[0]["sha256_after_carry"] == shared


def test_the_embedded_packet_carry_list_agrees_with_session_S(manifest):
    """This manifest carries a copy of S's file list so the composed runbook can be checked
    from one place. A stale copy would let postflight pass on the wrong bytes."""
    embedded = {r["destination_on_vps"]: r["sha256_after_carry"]
                for r in manifest["composes_with"].get("session_S_files", [])}
    assert embedded, "the composed manifest must record Session S's files"
    s_manifest = S_CARRY / "MANIFEST.json"
    if s_manifest.is_file():
        live = json.loads(s_manifest.read_text(encoding="utf-8"))["files"]
    else:
        ref = manifest["composes_with"]["session_S_packet_carry_source_ref"]
        rel = manifest["composes_with"]["session_S_packet_carry"]
        raw = _git_show(f"{ref}:{rel}")
        if raw is None:
            pytest.skip(f"Session S manifest not on disk and {ref} not in this clone")
        live = json.loads(raw)["files"]
    assert embedded == {r["destination_on_vps"]: r["sha256_after_carry"] for r in live}


def test_broker_clock_is_stdlib_only():
    """The host venv has 27 packages and ``tzdata`` is not one of them, so a ``zoneinfo``
    dependency would raise ``ZoneInfoNotFoundError`` inside the governor on Windows — and
    the governor imports this module unguarded.

    Read with ``ast``, not ``rg``: the module discusses ``ZoneInfo`` at length in prose
    explaining why it does not use it, so a substring test fails against a correct file.
    """
    import ast

    tree = ast.parse((CARRY / "files/broker_clock.py").read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module.split(".")[0])
    allowed = {"__future__", "dataclasses", "datetime"}
    assert modules <= allowed, f"unexpected imports: {sorted(modules - allowed)}"
    assert "zoneinfo" not in modules


# --------------------------------------------------------------------------------------
# 2. the carried behaviour
# --------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def carried_tree(lineage_available):
    """A throwaway reconstruction of the host tree with the carry applied."""
    if not lineage_available:
        pytest.skip("lineage commit not available")
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    tar = subprocess.run(["git", "archive", LINEAGE, "src", "config"],
                         cwd=REPO, check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(root)], input=tar, check=True)
    for name, dest in [
        ("broker_clock.py", "src/utils/broker_clock.py"),
        ("governor_state.py", "src/components/ultimate_book/governor_state.py"),
        ("book_engine.py", "src/components/ultimate_book/book_engine.py"),
        ("execution.py", "src/components/execution.py"),
    ]:
        (root / dest).write_bytes((CARRY / "files" / name).read_bytes())
    yield root
    tmp.cleanup()


def _load(root: Path, dotted: str):
    """Import a module out of ``root`` in isolation, with MetaTrader5 shadowed."""
    import importlib

    saved_path, saved_mods = list(sys.path), dict(sys.modules)
    try:
        sys.path.insert(0, str(root))
        for key in [k for k in sys.modules if k == "src" or k.startswith("src.")]:
            del sys.modules[key]
        sys.modules["MetaTrader5"] = types.ModuleType("MetaTrader5")
        return importlib.import_module(dotted)
    finally:
        sys.path[:] = saved_path
        sys.modules.clear()
        sys.modules.update(saved_mods)


BROKER_GEOMETRIES = [(0.01, 0.01), (0.1, 0.1), (0.01, 0.001), (1.0, 1.0),
                     (0.1, 0.01), (0.5, 0.1), (0.02, 0.02), (0.001, 0.001), (0.05, 0.05)]


class _SymInfo:
    def __init__(self, vmin, vstep, vmax=1000.0):
        self.volume_min, self.volume_step, self.volume_max = vmin, vstep, vmax


def test_carried_execution_strands_no_broker_valid_volume(carried_tree):
    """The defect: ``(0.03 - 0.01) / 0.01`` is 1.9999999999999996, so 0.03 lots normalized to
    0.02, and ``_close_request_execution_geometry`` refuses any close whose normalized volume
    differs from the request. Nine close producers route through it and all nine return
    before the activation layer, so the never-strand guarantee never got a say."""
    engine = _load(carried_tree, "src.components.execution")
    norm = engine.ExecutionEngine._normalize_volume
    stranded = []
    for vmin, vstep in BROKER_GEOMETRIES:
        si = _SymInfo(vmin, vstep)
        for k in range(2000):
            lots = round(vmin + k * vstep, 10)
            if lots > si.volume_max:
                break
            out = norm(None, lots, si, require_broker_geometry=True)
            if out is None or abs(out - lots) > 1e-12:
                stranded.append((vmin, vstep, lots, out))
    assert not stranded, f"{len(stranded)} stranded volumes, first: {stranded[:5]}"


def test_carried_execution_never_rounds_a_volume_up(carried_tree):
    """The epsilon must be a step-count tolerance, not a licence to size up: a broker
    rejects an over-large close and the position is stranded again."""
    engine = _load(carried_tree, "src.components.execution")
    norm = engine.ExecutionEngine._normalize_volume
    for vmin, vstep in BROKER_GEOMETRIES:
        si = _SymInfo(vmin, vstep)
        for k in range(400):
            for frac in (0.0, 0.1, 0.5, 0.9, 0.999999):
                lots = vmin + (k + frac) * vstep
                if lots > si.volume_max:
                    continue
                out = norm(None, lots, si, require_broker_geometry=True)
                if out is not None:
                    assert out <= lots + 1e-12, (vmin, vstep, lots, out)


def test_the_lineage_really_has_the_defect(lineage_available):
    """A carry authored against a defect that was only read about is how the packet block
    happened. 33 of 300 two-decimal lots at (0.01, 0.01), measured on the host's own file."""
    if not lineage_available:
        pytest.skip("lineage commit not available")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        tar = subprocess.run(["git", "archive", LINEAGE, "src"], cwd=REPO,
                             check=True, capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", str(root)], input=tar, check=True)
        engine = _load(root, "src.components.execution")
        norm = engine.ExecutionEngine._normalize_volume
        si = _SymInfo(0.01, 0.01)
        bad = [round(i / 100.0, 2) for i in range(1, 301)
               if abs(norm(None, round(i / 100.0, 2), si, require_broker_geometry=True)
                      - round(i / 100.0, 2)) > 1e-12]
        assert len(bad) == 33, f"expected 33 stranded of 300 on the lineage, got {len(bad)}"
        assert 0.03 in bad
        assert abs(norm(None, 0.03, si, require_broker_geometry=True) - 0.02) < 1e-12


# (profile, namespace, now, expected reset-window start, note)
RESET_CASES = [
    ("operator_profile", "operator_profile",
     "2026-10-27T21:30:00+00:00", "2026-10-26T23:00:00+00:00",
     "mismatch window: 00:00 CET is 23:00 UTC; server midnight was 21:00 UTC, 2 h early"),
    ("operator_profile", "operator_profile",
     "2026-03-15T21:30:00+00:00", "2026-03-14T23:00:00+00:00", "the March mismatch window"),
    ("operator_profile", "operator_profile",
     "2026-07-15T23:30:00+00:00", "2026-07-15T22:00:00+00:00",
     "calendars agreeing: still 1 h after server midnight"),
    ("redacted_account", "redacted_account_live_bee34003",
     "2026-10-27T21:30:00+00:00", "2026-10-27T21:00:00+00:00",
     "redacted_account resets at server midnight and must keep doing so"),
    ("redacted_account", "redacted_account_live_bee34003",
     "2026-07-15T23:30:00+00:00", "2026-07-15T21:00:00+00:00", "redacted_account, summer"),
]


@pytest.mark.parametrize("profile,namespace,now_iso,expected,note", RESET_CASES)
def test_carried_governor_uses_each_firms_own_reset_rule(
    carried_tree, profile, namespace, now_iso, expected, note
):
    """B56, end to end through the engine, on the host's own config and profiles."""
    import yaml

    engine_mod = _load(carried_tree, "src.components.ultimate_book.book_engine")
    cfg_mod = _load(carried_tree, "src.utils.config")

    class _OffsetMT5:
        _mt5 = None

        def get_broker_offset_seconds(self):
            return 3 * 3600     # the measured server offset on all three dates above

    cfg = yaml.safe_load((carried_tree / "config/agent_config.yaml").read_text(encoding="utf-8"))
    merged = cfg_mod.apply_profile_overrides(cfg, profile)
    rt = merged.get("gtos_vnext_runtime", merged)
    with tempfile.TemporaryDirectory() as state:
        eng = engine_mod.UltimateBookLiveEngine(rt, _OffsetMT5(), state, namespace=namespace)
        got = eng._governor._reset_window_start_utc(datetime.fromisoformat(now_iso))
    assert got.astimezone(timezone.utc) == datetime.fromisoformat(expected), note


def test_the_b56_carry_needs_no_config_edit(carried_tree):
    """The claim this carry rests on: the rule is already in the profile the host ships, so
    nothing decision-contract-bound has to change. Measured through the production resolver,
    not by reading YAML."""
    import yaml

    cfg_mod = _load(carried_tree, "src.utils.config")
    cfg = yaml.safe_load((carried_tree / "config/agent_config.yaml").read_text(encoding="utf-8"))

    ftmo = cfg_mod.apply_profile_overrides(cfg, "operator_profile")
    ftmo_rt = ftmo.get("gtos_vnext_runtime", ftmo)
    assert ftmo_rt.get("prop_safe_selector_daily_reset_timezone") == "Europe/Prague"
    assert ftmo_rt.get("governor_daily_reset_rule") is None

    fn = cfg_mod.apply_profile_overrides(cfg, "redacted_account")
    fn_rt = fn.get("gtos_vnext_runtime", fn)
    assert fn_rt.get("prop_safe_selector_daily_reset_timezone") is None
    assert fn_rt.get("governor_daily_reset_rule") is None


def test_the_lineage_governor_really_resets_early(lineage_available):
    """The defect being fixed, reproduced on the host's own governor: 2 h early inside a
    calendar-mismatch window, in the direction that lets the book re-risk while the firm is
    still counting the previous day's losses."""
    if not lineage_available:
        pytest.skip("lineage commit not available")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        tar = subprocess.run(["git", "archive", LINEAGE, "src"], cwd=REPO,
                             check=True, capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", str(root)], input=tar, check=True)
        gs = _load(root, "src.components.ultimate_book.governor_state")
        with tempfile.TemporaryDirectory() as state:
            builder = gs.GovernorStateBuilder(
                state, namespace="operator_profile",
                daily_reset_offset_hours=3.0, offset_provider=lambda: 3.0)
            got = builder._reset_window_start_utc(datetime.fromisoformat("2026-10-27T21:30:00+00:00"))
    got = got.astimezone(timezone.utc)
    assert got == datetime.fromisoformat("2026-10-27T21:00:00+00:00")
    # At 21:30 UTC on 2026-10-27, FTMO's day still runs until 00:00 CET = 23:00 UTC. The
    # lineage governor has ALREADY rolled to the next window, 2 h early, and for those 2 h
    # it believes the daily-loss budget has reset while FTMO is still counting.
    ftmo_current_window_start = datetime.fromisoformat("2026-10-26T23:00:00+00:00")
    ftmo_next_reset = datetime.fromisoformat("2026-10-27T23:00:00+00:00")
    assert got > ftmo_current_window_start, "the lineage governor has rolled over early"
    assert (ftmo_next_reset - got).total_seconds() == 2 * 3600


def test_carried_monitor_agrees_with_the_carried_governor(carried_tree):
    """Stage D. Fixing the governor and leaving the monitor on server midnight would make
    the alerting layer and the risk layer disagree about which day it is, in the same
    dangerous direction the governor is being fixed for."""
    import importlib.util

    monitor_src = CARRY / "files/monitor_books.py"
    dest = carried_tree / ".tools/monitor_books.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(monitor_src.read_bytes())

    saved_path, saved_mods = list(sys.path), dict(sys.modules)
    try:
        sys.path.insert(0, str(carried_tree))
        for key in [k for k in sys.modules if k == "src" or k.startswith("src.")]:
            del sys.modules[key]
        sys.modules["MetaTrader5"] = types.ModuleType("MetaTrader5")
        spec = importlib.util.spec_from_file_location("_carried_monitor_books", dest)
        mb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mb)

        now = datetime.fromisoformat("2026-10-27T21:30:00+00:00")
        assert mb.daily_reset_window_start_utc("FTMO", now) == \
            datetime.fromisoformat("2026-10-26T23:00:00+00:00")
        assert mb.daily_reset_window_start_utc("redacted_account", now) == \
            datetime.fromisoformat("2026-10-27T21:00:00+00:00")
        # the dated hardcode: both servers drop to +2 on 2026-11-01
        nov = datetime.fromisoformat("2026-11-15T22:30:00+00:00")
        assert mb.server_offset_hours("FTMO", nov) == pytest.approx(2.0)
        assert mb.server_offset_hours("redacted_account", nov) == pytest.approx(2.0)
        assert mb.server_offset_hours("FTMO", now) == pytest.approx(3.0)
        # a losing deal 1.5 h before `now` belongs to FTMO's current day and the struck
        # date-comparison dropped it from the alert entirely
        rule = mb.resolve_rule("FTMO-Server3")
        deal_utc = datetime.fromisoformat("2026-10-27T20:00:00+00:00")
        epoch = mb.utc_to_broker_naive(deal_utc, rule).replace(tzinfo=timezone.utc).timestamp() \
            if hasattr(mb, "utc_to_broker_naive") else None
        if epoch is not None:
            assert mb.broker_epoch_to_utc(epoch, rule) >= mb.daily_reset_window_start_utc("FTMO", now)
    finally:
        sys.path[:] = saved_path
        sys.modules.clear()
        sys.modules.update(saved_mods)


def test_the_struck_monitor_hardcode_is_gone():
    src = (CARRY / "files/monitor_books.py").read_text(encoding="utf-8")
    assert "SRV_OFFSET_H = 3" not in src.replace("`SRV_OFFSET_H = 3   # FTMO/FN server = UTC+3 (EEST)`", "")
    assert "daily_reset_window_start_utc" in src


# --------------------------------------------------------------------------------------
# 3. the partial-application invariants
# --------------------------------------------------------------------------------------

PARTIAL_STATES = CARRY / "receipts/PARTIAL_STATES.json"


def test_partial_states_receipt_matches_the_three_stated_invariants():
    """The ordering rests on exactly three rules. If a fourth failure mode ever appears, the
    runbook's stop-points are wrong and this test is the thing that says so.

    It was two until a refuter found the third: the carried `.tools/monitor_books.py` imports
    `src.utils.broker_clock` at module top, unguarded, and the monitor is a supervisor-restarted
    live process. The first version of the enumeration could not see it — stage D was not in the
    state space at all.
    """
    if not PARTIAL_STATES.is_file():
        pytest.skip("partial-state receipt not generated")
    data = json.loads(PARTIAL_STATES.read_text(encoding="utf-8"))
    for rec in data["results"]:
        files = set(rec["ac_files"])
        predicted_fatal = (
            ("gs" in files and "bc" not in files)         # ModuleNotFoundError at module load
            or ("be" in files and "gs" not in files)      # TypeError at run_book.py:294
            or ("mb" in files and "bc" not in files)      # the monitor daemon, crash loop
        )
        assert rec["book_starts"] is not predicted_fatal, (
            f"{rec['label']}: predicted fatal={predicted_fatal} but book_starts={rec['book_starts']}"
        )
    assert data["total_states"] == 64
    assert data["states_that_die_before_the_first_tick"] == 36


def test_session_S_carry_does_not_change_any_partial_verdict():
    """The composition question, answered by measurement: applying the packet carry changes
    no state's verdict, in either direction."""
    if not PARTIAL_STATES.is_file():
        pytest.skip("partial-state receipt not generated")
    data = json.loads(PARTIAL_STATES.read_text(encoding="utf-8"))
    if not data.get("session_S_carry_included"):
        pytest.skip("receipt was generated without Session S's carry")
    by_subset: dict[tuple, dict] = {}
    for rec in data["results"]:
        by_subset.setdefault(tuple(rec["ac_files"]), {})[rec["session_S_packet_carry_applied"]] = rec
    assert by_subset, "no results"
    for subset, pair in by_subset.items():
        assert set(pair) == {False, True}, subset
        assert pair[False]["book_starts"] == pair[True]["book_starts"], subset


# --------------------------------------------------------------------------------------
# 4. the runbook
# --------------------------------------------------------------------------------------

RUNBOOK = CARRY / "ACTIVATION_CARRY_VPS_RUNBOOK.md"


@pytest.mark.skipif(not RUNBOOK.is_file(), reason="runbook not written yet")
def test_runbook_avoids_the_four_defects_found_on_that_host():
    text = RUNBOOK.read_text(encoding="utf-8")
    code = "\n".join(
        line for block in re.findall(r"```(?:powershell|ps1|text)?\n(.*?)```", text, re.S)
        for line in block.splitlines()
    )

    # 1. Get-Process does not expose CommandLine in Windows PowerShell 5.1: it silently
    #    matches nothing, and the operator concludes a restart worked.
    assert not re.search(r"Get-Process\b[^\n]*CommandLine", code), \
        "Get-Process | CommandLine matches nothing on PowerShell 5.1; use Get-CimInstance Win32_Process"

    # 2. bash heredocs are not PowerShell.
    assert "<<'PY'" not in code and "<<PY" not in code and "<<EOF" not in code

    # 3. the books run .venv-gtos\Scripts\python.exe (3.13.13), not PATH python (3.11.15).
    for line in code.splitlines():
        stripped = line.strip().lstrip("&").strip()
        assert not re.match(r'^"?python(\.exe)?"?\s', stripped), \
            f"bare PATH python invocation: {line!r}"

    # 4. two repo trees on that host; the root must be derived, and ambiguity must STOP.
    assert "Get-CimInstance Win32_Process" in code
    assert "STOP" in text


def test_the_diffs_apply_with_both_patch_and_git_apply(manifest, lineage_available):
    """A reviewer reaching for `git apply` must not read the carry as broken.

    They did: the first draft's `---`/`+++` labels carried a trailing provenance annotation, and
    `git apply` takes the whole rest of that line as the filename. `patch` splits on whitespace and
    never minded, so the defect was invisible from the build script's own round-trip.
    """
    if not lineage_available:
        pytest.skip("lineage commit not available")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        tar = subprocess.run(["git", "archive", LINEAGE, "src", ".tools/monitor_books.py"],
                             cwd=REPO, check=True, capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", str(root)], input=tar, check=True)
        subprocess.run(["git", "init", "-q", "."], cwd=root, check=True, capture_output=True)
        for rec in manifest["files"]:
            if rec["is_new_file_on_vps"]:
                continue
            diff = REPO / rec["diff_in_this_repo"]
            for tool in (["git", "apply", "--check", "-p1", str(diff)],
                         ["patch", "-p1", "--dry-run", "-s", "-F", "0", "-i", str(diff)]):
                proc = subprocess.run(tool, cwd=root, capture_output=True, text=True)
                assert proc.returncode == 0, (
                    f"{rec['repo_path']}: {tool[0]} failed: {proc.stderr or proc.stdout}")


@pytest.mark.skipif(not RUNBOOK.is_file(), reason="runbook not written yet")
def test_every_hash_the_runbook_quotes_is_a_real_manifest_value(manifest):
    """No sha in the runbook may be invented, stale, or belong to a different file.

    This test exists because the first draft of the runbook quoted a **fabricated** hash for
    ``book_engine.py`` — the right 12-character prefix followed by 52 characters of nothing.
    An operator following the runbook alone would have hit a STOP on a correct copy. The
    manifest is the authority; this pins the prose to it.
    """
    truth = {rec["destination_on_vps"]: rec["sha256_after_carry"] for rec in manifest["files"]}
    for rec in manifest["composes_with"].get("session_S_files", []):
        truth.setdefault(rec["destination_on_vps"], rec["sha256_after_carry"])

    text = RUNBOOK.read_text(encoding="utf-8")
    quoted = set(re.findall(r"\b[0-9a-f]{64}\b", text))
    orphans = quoted - set(truth.values())
    assert not orphans, f"runbook quotes hashes that are in no manifest: {sorted(orphans)}"

    # and each `to=...; sha=...` pair must name its own file's hash, not another's
    for dest, sha in re.findall(r'to="([^"]+)";\s+sha="([0-9a-f]{64})"', text):
        if dest in truth:
            assert truth[dest] == sha, f"{dest}: runbook says {sha}, manifest says {truth[dest]}"


@pytest.mark.skipif(not RUNBOOK.is_file(), reason="runbook not written yet")
def test_the_rollback_block_is_self_contained_and_its_stops_actually_stop(manifest):
    """The rollback runs in whatever shell the operator has open at 2 a.m., which is very often
    not the one they copied in — and in PowerShell an empty variable is not an error.

    Two refuters broke the first version here, in the same way twice: a `Write-Host "STOP"` that
    does not halt, and `$backup` left as a `<placeholder>` with no guard, which made the block
    delete four files and restore none. So this pins the properties, not the prose.
    """
    text = RUNBOOK.read_text(encoding="utf-8")
    rollback = text.split("## 9. Rollback", 1)[1].split("\n## ", 1)[0]

    # everything it uses, it assigns
    for var in ("$backup", "$manPath", "$man"):
        assert re.search(rf"\{var}\s*=", rollback), f"rollback does not assign {var}"
    for var in ("repo", "py", "carry"):
        assert re.search(rf"\$global:{var}\s*=", rollback), f"rollback does not assign $global:{var}"

    # the guards are real: `throw`, not `Write-Host`
    assert 'if (-not (Test-Path $manPath))' in rollback, "no guard on the backup manifest"
    assert rollback.count("throw ") >= 4, "rollback's guards must throw, not print"

    # the exit code is checked with $? as well, because & on a null command leaves $LASTEXITCODE stale
    assert "$ok = $?" in rollback and "$rc = $LASTEXITCODE" in rollback

    # deletes are authorised by the backup's own record, never by a hardcoded list
    assert "$null -eq $f.sha256" in rollback
    assert "$newOnHost" not in rollback, "the hardcoded delete list is the defect, not the fix"

    # the monitor is stopped too: it is not a book, and it imports broker_clock unguarded
    assert "monitor_books.py" in rollback


@pytest.mark.skipif(not RUNBOOK.is_file(), reason="runbook not written yet")
def test_the_runbook_checks_the_supervisor_before_the_one_way_door(manifest):
    """`Stop-Process` in §7 is unconditional and nothing else brings the books back."""
    text = RUNBOOK.read_text(encoding="utf-8")
    seven = text.split("## 7. The restart", 1)[1].split("\n## 8.", 1)[0]
    # the first EXECUTED Stop-Process, not the prose mention of it
    stop_at = seven.index("foreach ($b in $live) { Stop-Process")
    before = seven[:stop_at]
    assert "run_book_supervisor" in before, "no supervisor-liveness check before the first Stop-Process"
    assert "supervisor_heartbeat.json" in before, "supervisor liveness is checked by process only"


@pytest.mark.skipif(not RUNBOOK.is_file(), reason="runbook not written yet")
def test_section_10_gates_on_stage_d_not_on_behaviour(manifest):
    """`--check behaviour` SKIPS an absent stage D and exits 0 either way, so it is not a gate."""
    text = RUNBOOK.read_text(encoding="utf-8")
    ten = text.split("## 10. Stage D", 1)[1].split("\n## 11.", 1)[0]
    assert "--check stage-d" in ten
    assert "--check behaviour" not in ten.split("```", 1)[0] + "".join(
        b for b in re.findall(r"```powershell\n(.*?)```", ten, re.S))


@pytest.mark.skipif(not RUNBOOK.is_file(), reason="runbook not written yet")
def test_runbook_covers_every_carried_file_and_a_rollback(manifest):
    text = RUNBOOK.read_text(encoding="utf-8")
    for rec in manifest["files"]:
        assert Path(rec["repo_path"]).name in text, rec["repo_path"]
    assert "--check preflight" in text
    assert "--check postflight" in text
    assert "--check behaviour" in text
    assert "--check rollback" in text



# --------------------------------------------------------------------------------------
# 5. the verifier itself, executed
# --------------------------------------------------------------------------------------

VERIFY = CARRY / "verify_carry.py"


def _host_tree(tmp: Path, *, apply_ac=(), apply_s=False) -> Path:
    """A reconstruction of the host tree with this carry's package inside it."""
    tmp.mkdir(parents=True, exist_ok=True)
    tar = subprocess.run(["git", "archive", LINEAGE, "src", "config", "scripts", "run_book.py",
                          ".tools/monitor_books.py"], cwd=REPO, check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(tmp)], input=tar, check=True)
    dst = tmp / CARRY.relative_to(REPO)
    dst.mkdir(parents=True, exist_ok=True)
    for item in CARRY.rglob("*"):
        if item.is_file():
            target = dst / item.relative_to(CARRY)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(item.read_bytes())
    if apply_s:
        s_dir = "docs/audits/fable5-vision-audit-20260725/phase4/packet_carry/files"
        for name, rel in [
            ("runtime_learning_packet.py", "src/components/ultimate_book/runtime_learning_packet.py"),
            ("packet_economics.py", "src/components/ultimate_book/packet_economics.py"),
            ("packet_guard.py", "src/components/ultimate_book/packet_guard.py"),
            ("book_owner.py", "src/components/ultimate_book/book_owner.py"),
            ("ultimate_book_packet_silence_alarm.py", "scripts/ultimate_book_packet_silence_alarm.py"),
        ]:
            blob = _git_show(f"phase4/packet-unblock:{s_dir}/{name}")
            if blob is None:
                pytest.skip("Session S's carry is not reachable from this clone")
            (tmp / rel).write_bytes(blob)
    for name, rel in apply_ac:
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp / rel).write_bytes((CARRY / "files" / name).read_bytes())
    return tmp / CARRY.relative_to(REPO) / "verify_carry.py"


def _run_check(verifier: Path, check: str) -> int:
    return subprocess.run(
        [sys.executable, str(verifier), "--check", check, "--allow-any-interpreter"],
        capture_output=True, text=True).returncode


AC_STAGE_ABC = [
    ("broker_clock.py", "src/utils/broker_clock.py"),
    ("governor_state.py", "src/components/ultimate_book/governor_state.py"),
    ("book_engine.py", "src/components/ultimate_book/book_engine.py"),
    ("execution.py", "src/components/execution.py"),
]


def test_the_verifier_passes_in_the_state_the_runbook_gates_at(lineage_available, tmp_path):
    """Runbook §6 says "all three must exit 0" — in a state where stage D is deliberately NOT
    applied yet, because it lands in §10.

    This test exists because a refuter found `postflight` demanding the carried sha for stage D
    too, so the authority gate could not pass at the step that runs it. **No test executed the
    verifier at all**, which is why it survived. Now one does.
    """
    if not lineage_available:
        pytest.skip("lineage commit not available")
    verifier = _host_tree(tmp_path, apply_ac=AC_STAGE_ABC, apply_s=True)
    assert _run_check(verifier, "postflight") == 0, "section 6's postflight must pass without stage D"
    assert _run_check(verifier, "imports") == 0
    assert _run_check(verifier, "behaviour") == 0
    assert _run_check(verifier, "all") == 0
    # ...and section 10's gate must NOT pass yet, or it is not a gate
    assert _run_check(verifier, "stage-d") == 2


def test_the_verifier_gates_flip_correctly_across_the_three_tree_states(lineage_available, tmp_path):
    """base -> carried -> rolled back. Each gate must pass in exactly its own state."""
    if not lineage_available:
        pytest.skip("lineage commit not available")
    base = _host_tree(tmp_path / "base", apply_ac=(), apply_s=False)
    assert _run_check(base, "preflight") == 0, "a base host must pass preflight"
    assert _run_check(base, "rollback") == 0, "a base host is a correctly rolled-back host"
    assert _run_check(base, "postflight") == 2, "a base host has not been carried"

    full = _host_tree(tmp_path / "full",
                      apply_ac=AC_STAGE_ABC + [("monitor_books.py", ".tools/monitor_books.py")],
                      apply_s=True)
    assert _run_check(full, "preflight") == 0, "an already-carried host is a valid preflight state"
    assert _run_check(full, "postflight") == 0
    assert _run_check(full, "stage-d") == 0
    assert _run_check(full, "rollback") == 2, "a carried host is not a rolled-back one"


def test_the_verifier_refuses_a_half_carried_tree(lineage_available, tmp_path):
    """`book_engine` without `governor_state` imports fine and dies at construction."""
    if not lineage_available:
        pytest.skip("lineage commit not available")
    verifier = _host_tree(tmp_path, apply_ac=[("book_engine.py",
                                               "src/components/ultimate_book/book_engine.py")])
    assert _run_check(verifier, "imports") == 2
    assert _run_check(verifier, "postflight") == 2


def test_the_verifier_refuses_a_truncated_carry(lineage_available, tmp_path):
    """A truncated file can import, construct and tick while the governor silently returns None.

    So this asserts BOTH halves of the claim: the byte comparison catches it and the behavioural
    probes do not. "`--check imports` is the reason the restart is safe" was withdrawn on the
    strength of exactly this, and a withdrawn claim deserves a test as much as a kept one.
    """
    if not lineage_available:
        pytest.skip("lineage commit not available")
    verifier = _host_tree(tmp_path, apply_ac=AC_STAGE_ABC, apply_s=True)
    target = tmp_path / "src/components/ultimate_book/governor_state.py"
    # 17,408 of 19,278 bytes. Not an arbitrary cut: scanning every 512-byte boundary finds exactly
    # FIVE that still import (7,680 / 11,264 / 15,360 / 17,408 / 18,944), which reproduces the
    # refuter's "5 of 35" independently. Three of those five also pass `behaviour`.
    target.write_bytes(target.read_bytes()[:17408])
    assert _run_check(verifier, "imports") == 0, (
        "if imports starts failing at this cut point, the 'necessary but not sufficient' framing "
        "in ORDERING_AND_PARTIAL_STATES.md is understated and should be revisited"
    )
    assert _run_check(verifier, "behaviour") == 0, "the behavioural probes do not see it either"
    assert _run_check(verifier, "postflight") == 2, "the sha comparison is the gate that does"


def test_a_correct_rollback_passes_on_a_host_that_already_had_the_packet_carry(
    lineage_available, tmp_path
):
    """The defect Session S shipped, reproduced inside this carry by a refuter, and fixed.

    A host with S's packet carry already applied is NOT on the lineage base. Judging a rollback
    against the lineage failed a correct rollback there — and the failing lines then instructed a
    deletion that produces `ModuleNotFoundError` on both books. Runbook §3 writes a
    `BACKUP_MANIFEST.json` of what it actually captured; this asserts the gate honours it.
    """
    if not lineage_available:
        pytest.skip("lineage commit not available")
    verifier = _host_tree(tmp_path, apply_ac=(), apply_s=True)   # the host's real pre-carry state
    manifest = json.loads((CARRY / "MANIFEST.json").read_text(encoding="utf-8"))
    paths = [rec["repo_path"] for rec in manifest["files"]]
    paths += [rec["destination_on_vps"].replace("\\", "/")
              for rec in manifest["composes_with"]["session_S_files"]]
    records = []
    for rel in dict.fromkeys(paths):
        f = tmp_path / rel
        records.append({"repo_path": rel,
                        "sha256": _sha(f.read_bytes()) if f.is_file() else None})
    backup = tmp_path / "_carry_backup_AC_20260729-190000"
    backup.mkdir(parents=True, exist_ok=True)
    (backup / "BACKUP_MANIFEST.json").write_text(
        json.dumps({"schema": "gtos.phase5.activation_carry_backup.v1",
                    "repo": str(tmp_path), "files": records}), encoding="utf-8")

    # nothing was carried, so the tree IS the correctly-rolled-back state
    assert _run_check(verifier, "rollback") == 0, (
        "a correct rollback on an S-applied host must pass; judging against the lineage is what "
        "made Session S's carry tell a correct operator not to restart"
    )

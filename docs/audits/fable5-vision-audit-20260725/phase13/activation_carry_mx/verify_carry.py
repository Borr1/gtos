#!/usr/bin/env python3
r"""Verify the Session AZ `mx_btcusd` activation carry ON THE HOST, behaviourally.

Six gates, real exit codes, no grep. Run every one from the repo root the books actually run
from (take it from a running book's own command line, do not assume):

    .venv-gtos\Scripts\python.exe docs\...\activation_carry_mx\verify_carry.py --check preflight
    ... --check postflight
    ... --check deps
    ... --check imports
    ... --check behaviour
    ... --check rollback     (ONLY after a rollback -- see the note below)
    ... --check all          (postflight + deps + imports + behaviour; preflight and rollback
                              are BEFORE/AFTER states and cannot both pass at once)

Exit codes: ``0`` pass, ``2`` fail/STOP, ``3`` usage or environment refusal (wrong interpreter,
or not run from inside the book's tree). **A ``3`` is not a failure of the carry.**

WHAT THIS CARRY IS
------------------
Four files that make `mx_btcusd_d1_donchian_20_breakout @ target_5R` -- the estate's ONE
standing admission at the ratified rule -- RUNNABLE. It arms nothing: with no
`--frontier-exits` on the launcher line every carried default is what the host runs today, and
that is asserted here rather than asserted about.

`--check preflight` DOES SOMETHING THIS PROGRAMME'S CARRIES HAVE NOT DONE BEFORE
--------------------------------------------------------------------------------
`run_book.py` reached this host through the Stage-0 token ceremony, which recorded LINE COUNTS
and no sha256 -- so no artifact pins its bytes. Rather than guess, the manifest carries the
COMPLETE set of committed versions compatible with the host's `book_owner.py`, each with its
own pre-built payload and its own exact after-sha256, and preflight reads the host's actual
sha256 and NAMES the one to copy. An unrecognised sha256 is a STOP with the bytes printed, not
a guess and not a default.

`--check deps` IS A SEPARATE GATE BECAUSE ORDER IS THE WHOLE SAFETY ARGUMENT
----------------------------------------------------------------------------
Nine of the sixteen subsets of this carry are fatal, and a module-top import probe finds
**none** of them (`receipts/AZ_CARRY_PROBE_V1.json`). Two of the three failure classes are
invisible to `--check imports`:

  * `book_owner.py` without `order_router.py` -> `TypeError` at STARTUP on both namespaces;
  * `order_router.py` without `execution_packets.py` -> a SILENT TOTAL PLACEMENT OUTAGE. The
    router catches its own TypeError and returns `placed: False, reason: router_exception:...`
    on every unit, forever, with a healthy process and a healthy heartbeat.

There is a fourth, and it is the most expensive because it crosses OUT of this carry's own
files: `scripts\run_book_supervisor.ps1` passing `--frontier-exits` while `run_book.py` is not
carried is `argparse` exiting on an unrecognised argument at EVERY respawn of EVERY namespace
-- a permanent crash loop of both books with no exit management. It bites in the rollback
direction too, which is why the rollback order in `ORDERING_AND_PARTIAL_STATES.md` section 7
puts the supervisor line first.

`deps` asserts all four directly against the bytes on disk. `imports` and `behaviour` then
prove the tree starts and behaves. All three gates are necessary; none is sufficient.

Nothing here can reach a broker. ``MetaTrader5`` is shadowed with an empty module before any
import, ``mt5.connect()`` is never called, and no ``ExecutionEngine`` is constructed through
its own ``__init__``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "MANIFEST.json"

PASS, FAIL, REFUSE = 0, 2, 3

BTC = "mx_btcusd_d1_donchian_20_breakout"
#: The four sleeves both live books run today (`phase8/receipts/FXJPY_PULL_20260730.md`). Every
#: one of them must be byte-unchanged by this carry, which `behaviour` asserts by driving them.
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert")

_problems: list[str] = []


def problems_since(mark: int) -> int:
    """Failures recorded since ``mark``, so a FAIL in one gate is not re-reported by the next."""
    return len(_problems) - mark


def say(ok: bool | None, msg: str) -> None:
    print(f"[{ {True: '  ok  ', False: ' FAIL ', None: '  --  '}[ok] }] {msg}")
    if ok is False:
        _problems.append(msg)


def sha256_of(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


# --------------------------------------------------------------------------------------
# environment
# --------------------------------------------------------------------------------------

def resolve_repo_root() -> Path:
    """The repo root, from where THIS FILE lives, then proved by landmarks.

    Deliberately not ``os.getcwd()``: Session S's verifier had a false green where running it
    from the wrong directory made every destination look absent, which reads as "not carried
    yet" rather than "you are in the wrong tree".
    """
    root = HERE.parents[4]
    landmarks = ["run_book.py", "src/components/ultimate_book/book_engine.py",
                 "config/agent_config.yaml"]
    missing = [m for m in landmarks if not (root / m).exists()]
    if missing:
        print(f"[ STOP ] {root} does not look like the book's repo root "
              f"(missing: {', '.join(missing)}).")
        print("         Copy this carry INTO the tree the running book uses, then re-run there.")
        sys.exit(REFUSE)
    return root


def check_interpreter(root: Path) -> None:
    """Refuse under an interpreter the books do not use. A green from the wrong one is worse
    than no answer (Session AC: every wave-3 runbook tested a bare PATH python 3.11 while all
    ten live processes run `.venv-gtos` 3.13)."""
    if sys.version_info < (3, 10):
        print(f"[ STOP ] python {sys.version.split()[0]} is too old; the books run 3.13.")
        sys.exit(REFUSE)
    want = (root / ".venv-gtos").resolve()
    got = Path(sys.prefix).resolve()
    # Conditional on the venv EXISTING, and that is a deliberate improvement on AC's version.
    # AC refused unconditionally, which made the verifier unrunnable anywhere but the host --
    # so its own gates could never be exercised against a reconstructed tree before the
    # ceremony, and the first real execution of the tool was on a live funded machine. Where
    # `.venv-gtos` is absent this is not the host and the check has nothing to protect; where
    # it is present the refusal is exactly as strict as AC's.
    if want.is_dir() and str(got).lower() != str(want).lower():
        print(f"[ STOP ] this interpreter's environment is {got}")
        print(f"         The books run out of {want}. Re-run with that one:")
        print(f'         & "{want}\\Scripts\\python.exe" "{Path(__file__)}" --check <check>')
        print(f"         (executable: {sys.executable}, version {sys.version.split()[0]})")
        sys.exit(REFUSE)


def _isolate_from_mt5(root: Path) -> None:
    """Host tree on sys.path, ``MetaTrader5`` shadowed by an empty module. Unconditional: the
    host HAS the real package and every module below would import it happily. Nothing imported
    here touches it at import time, so the stub changes no verdict -- it only makes it
    impossible for this process to hold an MT5 handle by accident on a live funded machine."""
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    sys.modules["MetaTrader5"] = types.ModuleType("MetaTrader5")


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _run_book_record(man: dict) -> dict:
    return next(r for r in man["files"] if r["repo_path"] == "run_book.py")


def _selected_run_book(root: Path, man: dict) -> tuple[dict | None, str | None]:
    """Which `accepted_before_states` row the host is on, by sha256. ``(None, observed)`` when
    the host is already carried or on something nobody has seen."""
    rec = _run_book_record(man)
    got = sha256_of(root / "run_book.py")
    for state in rec["accepted_before_states"]:
        if state["sha256_before_expected"] == got:
            return state, got
    return None, got


# --------------------------------------------------------------------------------------
# 1. preflight
# --------------------------------------------------------------------------------------

def check_preflight(root: Path, man: dict) -> int:
    mark = len(_problems)
    print("\n== preflight: is this host in a state this carry was built for? ==")
    for rec in man["files"]:
        if rec["repo_path"] == "run_book.py":
            continue
        got = sha256_of(root / rec["repo_path"])
        want, done = rec["sha256_before_expected"], rec["sha256_after_carry"]
        tag = rec["repo_path"]
        if got == want:
            say(True, f"{tag}: at the expected pre-carry bytes")
        elif got == done:
            say(None, f"{tag}: ALREADY CARRIED (after-bytes) — this is a re-run, not a problem")
        elif got is None:
            say(False, f"{tag}: ABSENT. Every file in this carry modifies an existing one; an "
                       f"absent destination means the wrong tree or a broken host.")
        else:
            say(False, f"{tag}: UNKNOWN bytes sha256={got}\n"
                       f"         expected {want} (pre-carry) or {done} (already carried).\n"
                       f"         STOP: something changed this file since the last ceremony. "
                       f"Do not copy over it — find out what, first.")

    print("\n  run_book.py — the one file no artifact pins (see the module docstring):")
    state, got = _selected_run_book(root, man)
    rec = _run_book_record(man)
    if got == rec["sha256_after_carry"]:
        say(None, "run_book.py: ALREADY CARRIED with the primary variant's payload")
    elif state is None:
        say(False, f"run_book.py: UNRECOGNISED sha256={got}\n"
                   f"         STOP. Do NOT copy the primary payload over it — that payload is "
                   f"built from a DIFFERENT base and would silently revert whatever this host "
                   f"has. Send these bytes back and a matching payload will be built from them:"
                   f"\n         sha256={got}  bytes={(root / 'run_book.py').stat().st_size}")
    else:
        say(True, f"run_book.py: recognised — {state['label']}")
        print(f"         COPY THIS PAYLOAD:  {state['payload_file']}")
        print(f"         it must land at sha256 {state['sha256_after_carry']}")
    return FAIL if problems_since(mark) else PASS


# --------------------------------------------------------------------------------------
# 2. postflight
# --------------------------------------------------------------------------------------

def check_postflight(root: Path, man: dict) -> int:
    mark = len(_problems)
    print("\n== postflight: is every destination at its after-carry bytes? ==")
    for rec in sorted(man["files"], key=lambda r: r["copy_order"]):
        got = sha256_of(root / rec["repo_path"])
        tag = f"[{rec['copy_order']}] {rec['repo_path']}"
        if rec["repo_path"] == "run_book.py":
            accepted = {s["sha256_after_carry"]: s for s in rec["accepted_before_states"]}
            if got in accepted:
                say(True, f"{tag}: carried ({accepted[got]['label']})")
                continue
            if got in {s["sha256_before_expected"] for s in rec["accepted_before_states"]}:
                say(False, f"{tag}: NOT CARRIED — still at a pre-carry state")
                continue
            say(False, f"{tag}: sha256={got} is neither a pre-carry nor a carried state")
            continue
        if got == rec["sha256_after_carry"]:
            say(True, f"{tag}: carried")
        elif got == rec["sha256_before_expected"]:
            say(False, f"{tag}: NOT CARRIED — still at the pre-carry bytes")
        else:
            say(False, f"{tag}: sha256={got}, expected {rec['sha256_after_carry']}")

    # A byte comparison is what catches a truncated copy; a behaviour probe is not. Session AC
    # measured 39 states that pass import+construct and are silently unsafe, every one of which
    # fails a sha comparison. Say so here so nobody promotes `behaviour` over `postflight`.
    print("\n  (a truncated copy imports, constructs, ticks — and fails the line above. That is "
          "why this gate is bytes and not behaviour.)")
    return FAIL if problems_since(mark) else PASS


# --------------------------------------------------------------------------------------
# 3. deps — the four ordering invariants, asserted on disk
# --------------------------------------------------------------------------------------

def check_deps(root: Path, man: dict) -> int:
    """The four invariants: three measured over all 16 subsets in
    `receipts/AZ_CARRY_PROBE_V1.json`, and a fourth that crosses out of this carry's own
    files into the supervisor line and bites in BOTH the carry and the rollback direction.

    Each is asserted here as "if the dependent file is carried, its dependency must be too" --
    on the BYTES, before anything is imported, because two of the three are invisible to
    import and one of those two is invisible to construction as well.
    """
    mark = len(_problems)
    print("\n== deps: the four ordering invariants ==")
    by_path = {r["repo_path"]: r for r in man["files"]}

    def carried(repo_path: str) -> bool:
        got = sha256_of(root / repo_path)
        rec = by_path[repo_path]
        if repo_path == "run_book.py":
            return got in {s["sha256_after_carry"] for s in rec["accepted_before_states"]}
        return got == rec["sha256_after_carry"]

    ep = "src/components/ultimate_book/execution_packets.py"
    orr = "src/components/ultimate_book/order_router.py"
    bo = "src/components/ultimate_book/book_owner.py"
    rb = "run_book.py"

    for dependent, dependency, consequence in [
        (orr, ep, "SILENT TOTAL PLACEMENT OUTAGE. `UltimateBookOrderRouter.place` wraps its "
                  "body in `except Exception` — 'the book NEVER breaks the live path' — so "
                  "every placement returns `placed: False, reason: "
                  "\"router_exception:TypeError(build_book_trade_params() got an unexpected "
                  "keyword argument 'frontier_exits')\"` while the process stays up, the "
                  "heartbeat stays healthy and exit management keeps running. MEASURED, not "
                  "inferred. Invisible to --check imports and to construction."),
        (bo, orr, "TypeError: UltimateBookOrderRouter.__init__() got an unexpected keyword "
                  "argument 'frontier_exits' — at STARTUP, on BOTH namespaces, so the "
                  "supervisor restart-loops and manage_open_positions never runs."),
        (rb, ep, "ImportError: cannot import name 'parse_frontier_exits' — at MODULE LOAD of "
                 "main(), unconditionally, whether or not --frontier-exits is given."),
        (rb, bo, "TypeError: UltimateBookOwner.__init__() got an unexpected keyword argument "
                 "'frontier_exits' — at STARTUP on both namespaces."),
    ]:
        if carried(dependent) and not carried(dependency):
            say(False, f"{dependent} is carried and {dependency} is NOT.\n"
                       f"         {consequence}\n"
                       f"         FIX: copy {dependency} now, then re-run this check. Do not "
                       f"restart a book in this state.")
        else:
            say(True, f"{dependent} implies {dependency}"
                      + ("" if carried(dependent) else "  (dependent not carried — vacuous)"))

    # The fourth invariant, and it is the only one that crosses out of this carry's own files.
    # It bites in BOTH directions: activating before `run_book.py` lands, and rolling `run_book.py`
    # back while the supervisor line still carries the flag. `parse_args()` (not
    # `parse_known_args`) errors on an unrecognised argument, so either way EVERY respawn of
    # EVERY namespace dies immediately -- a permanent crash loop with no exit management, which
    # is the most expensive state in this document and the one no byte comparison of the four
    # carried files can see.
    sup = root / "scripts/run_book_supervisor.ps1"
    sup_text = sup.read_text(encoding="utf-8", errors="replace") if sup.is_file() else None
    if sup_text is None:
        # Not a pass and not a fail: on the host this file always exists and is what launches
        # both books. Reporting its absence as "not armed" would be a false reassurance.
        say(None, "scripts/run_book_supervisor.ps1 is ABSENT — this gate cannot answer the "
                  "supervisor-line invariant. On the host that file exists; if you are seeing "
                  "this on the host, stop and find out why.")
    elif "--frontier-exits" in sup_text and not carried(rb):
        say(False, "scripts/run_book_supervisor.ps1 passes --frontier-exits and run_book.py is "
                   "NOT carried.\n"
                   "         argparse exits on an unrecognised argument, so EVERY respawn of "
                   "EVERY namespace dies immediately — a permanent crash loop of both books "
                   "with no exit management at all.\n"
                   "         FIX: either copy run_book.py now, or remove --frontier-exits from "
                   "the supervisor line. Do not leave it in this state.")
    elif "--frontier-exits" in sup_text:
        say(True, "scripts/run_book_supervisor.ps1 passes --frontier-exits and run_book.py "
                  "accepts it")
    else:
        say(None, "scripts/run_book_supervisor.ps1 does not pass --frontier-exits — the carry "
                  "is deployed and the activation is NOT armed (steps 3-7 done, 8-12 not)")

    n = sum(carried(p) for p in (ep, orr, bo, rb))
    say(None, f"{n} of 4 carried. The safe order is execution_packets -> order_router -> "
              f"book_owner -> run_book, and EVERY PREFIX of it is a safe host state.")
    return FAIL if problems_since(mark) else PASS


# --------------------------------------------------------------------------------------
# 4. imports
# --------------------------------------------------------------------------------------

def check_imports(root: Path, man: dict, *, quiet_header: bool = False,
                  expect_frontier: bool = True) -> int:
    """Exactly what `run_book.py` does before its first tick, in this process — including the
    DEFERRED imports inside `main()`, which is where this carry's own new edge lives.

    `expect_frontier=False` is for the ROLLBACK gate and it is not a convenience. Demanding the
    frontier construction there would fail a CORRECT rollback and tell an operator at 2 a.m.
    that the tree is broken and not to restart — which is Session S's own published defect, and
    the first draft of THIS file reproduced it through the behaviour half rather than the byte
    half. After a rollback the activation capability being GONE is the success condition, so it
    is reported and not scored.
    """
    mark = len(_problems)
    if not quiet_header:
        print("\n== imports: every `src.` import run_book.py performs, then the construction ==")
    _isolate_from_mt5(root)
    import ast
    import importlib

    src = (root / "run_book.py").read_text(encoding="utf-8")
    wanted: list[tuple[str, list[str]]] = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("src."):
            wanted.append((node.module, [a.name for a in node.names]))
        elif isinstance(node, ast.Import):
            wanted += [(a.name, []) for a in node.names if a.name.startswith("src.")]
    # Derived from the host's OWN run_book.py rather than from a list in this file, so a carry
    # that adds an import cannot outrun its own probe.
    for mod, names in wanted:
        try:
            m = importlib.import_module(mod)
            for n in names:
                if hasattr(m, n):
                    continue
                importlib.import_module(f"{mod}.{n}")   # a submodule, not an attribute
        except BaseException as exc:  # noqa: BLE001 -- the operator needs the class name
            say(False, f"import {mod} FAILED: {type(exc).__name__}: {exc}")
            print("\n  STOP. run_book.py dies in this state. The supervisor restarts a missing "
                  "book every ~33 s and manage_open_positions never runs.")
            return FAIL
    say(True, f"all {len(wanted)} `src.` imports in run_book.py resolve (module-top AND deferred)")

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
        UltimateBookOwner(cfg, _StubMT5(), tempfile.mkdtemp(prefix="gtos_az_"),
                          namespace="verify_probe_ns")
        say(True, "construct UltimateBookOwner with NO selection (the default launcher line)")
    except BaseException as exc:  # noqa: BLE001
        say(False, f"construct UltimateBookOwner FAILED: {type(exc).__name__}: {exc}")
        print("\n  STOP. run_book.py dies at startup in this state, before its first tick.")
        return FAIL

    try:
        from src.components.ultimate_book.execution_packets import parse_frontier_exits
        sel = parse_frontier_exits(BTC)
        o = UltimateBookOwner(cfg, _StubMT5(), tempfile.mkdtemp(prefix="gtos_az_"),
                              namespace="verify_probe_ns", frontier_exits=sel)
        assert tuple(o.router.frontier_exits) == sel, "the owner did not reach the router"
        if expect_frontier:
            say(True, f"construct with --frontier-exits {BTC}, and the router holds the selection")
        else:
            say(False, "the frontier selection STILL CONSTRUCTS after a rollback — the carry is "
                       "not fully reverted, whatever the byte comparison above said")
    except BaseException as exc:  # noqa: BLE001
        if expect_frontier:
            say(False, f"construct WITH the frontier selection FAILED: {type(exc).__name__}: {exc}")
            return FAIL
        say(None, f"the frontier selection no longer constructs ({type(exc).__name__}) — which "
                  f"is what a completed rollback MEANS. The book starts; the activation is gone.")
    return FAIL if problems_since(mark) else PASS


# --------------------------------------------------------------------------------------
# 5. behaviour
# --------------------------------------------------------------------------------------

def _sized(sleeve: str, symbol: str, entry: float, stop: float):
    from src.components.ultimate_book.admission import SizedUnit, TradeIntent
    su = SizedUnit(cluster="book", sleeve_members=[sleeve], n_trades=1, confidence=0.025,
                   risk_pct_per_trade=0.005, unit_risk_pct=0.5, sized=True, reason="ok")
    intent = TradeIntent(sleeve=sleeve, symbol=symbol, direction=1, decision_day="2026-06-15",
                         stop_dist=stop, target_dist=2.0 * stop)
    acct = dict(current_equity=100000.0, balance=100000.0, account_login=531325516,
                day_start_equity_or_balance_baseline=100000.0, daily_reset_window_id="2026-06-15")
    geom = {"entry_price": entry, "risk_distance": stop, "stop_loss": entry - stop,
            "take_profit_1": entry + 2.0 * stop}
    return su, intent, geom, acct


def _check_behaviour_inner(root: Path, man: dict) -> int:
    """The activation, and the promise that nothing else moved — both by behaviour.

    Every block is wrapped. A truncated carried file can import and construct and then be
    missing the very function under test; an unhandled AttributeError here would exit 1,
    outside the documented {0, 2, 3}, and read as "the tool is broken" rather than "the file on
    your host is incomplete".
    """
    mark = len(_problems)
    _isolate_from_mt5(root)
    import src.components.ultimate_book.execution_packets as EP

    ENTRY, STOP = 3000.0, 10.0

    # ---- item 1: the activation, through the real placement builder ----
    print("\n== behaviour 1: mx_btcusd resolves target_5R through build_book_trade_params ==")
    try:
        su, intent, geom, acct = _sized(BTC, "BTCUSD", ENTRY, STOP)
        off = EP.build_book_trade_params(su, intent, geom, acct,
                                         profile_namespace="operator_profile",
                                         frontier_exits=())
        on = EP.build_book_trade_params(su, intent, geom, acct,
                                        profile_namespace="operator_profile",
                                        frontier_exits=(BTC,))
        say(abs(off["take_profit_1"] - (ENTRY + 2.0 * STOP)) < 1e-9,
            f"committed contract: broker TP = entry + 2R = {off['take_profit_1']}  "
            f"(final_target_r {off['gtos_vnext_dynamic_final_target_r']})")
        say(abs(on["take_profit_1"] - (ENTRY + 5.0 * STOP)) < 1e-9,
            f"frontier contract:  broker TP = entry + 5R = {on['take_profit_1']}  "
            f"(final_target_r {on['gtos_vnext_dynamic_final_target_r']}) "
            f"<- the cell the admission is measured at")
        say(off["stop_loss"] == on["stop_loss"],
            "the STOP is untouched — a target change must never move the risk unit")
        say(on["gtos_vnext_dynamic_time_stop_bars"] == EP.time_stop_m15(80, "D1") == 7680,
            f"time stop = {on.get('gtos_vnext_dynamic_time_stop_bars')} printed M15 bars "
            f"= 80 D1 bars (AQ's repair; the F15 probe measured 7,800 available on both "
            f"terminals, above the 7,680 this needs)")
        prov = on["gtos_vnext_source_event_details"].get("exit_contract") or {}
        say(prov.get("frontier_cell") == "target_5R",
            f"the placement records WHICH contract placed it: {prov or 'MISSING'}")
        say("exit_contract" not in off["gtos_vnext_source_event_details"],
            "and a default placement carries no provenance key, so its source-event hash is "
            "unmoved (the key is hashed)")
    except BaseException as exc:  # noqa: BLE001
        say(False, f"the placement probe raised: {type(exc).__name__}: {exc}")

    # ---- item 2: the four ARMED sleeves are byte-unchanged ----
    print("\n== behaviour 2: the four ARMED sleeves are untouched, with and without a selection ==")
    try:
        wall = ("decision_time_utc", "asof_utc", "gtos_vnext_prop_firm_headroom_snapshot_v4",
                "gtos_vnext_dynamic_target_stop_geometry_v4")
        for sleeve in ARMED:
            su, intent, geom, acct = _sized(sleeve, "XAUUSD", ENTRY, STOP)
            a = EP.build_book_trade_params(su, intent, geom, acct,
                                           profile_namespace="operator_profile",
                                           frontier_exits=())
            b = EP.build_book_trade_params(su, intent, geom, acct,
                                           profile_namespace="operator_profile",
                                           frontier_exits=(BTC,))
            same = {k: v for k, v in a.items() if k not in wall} == \
                   {k: v for k, v in b.items() if k not in wall}
            say(same, f"{sleeve}: identical placement with and without the mx_btcusd selection")
            say(EP.resolve_exit_profile(sleeve, frontier_exits=(BTC,))
                is EP.SLEEVE_EXIT_PROFILES[sleeve],
                f"{sleeve}: resolves to the COMMITTED profile object itself, not a copy")
        say(EP.SLEEVE_EXIT_PROFILES["sub_xvol_pullback"]["final_target_r"] == 3.0,
            "sub_xvol_pullback's committed target is still 3R — its 4R frontier cell is wired "
            "and OFF, and it REJECTS at all four cost bands at the ratified rule (AU 1.3)")
    except BaseException as exc:  # noqa: BLE001
        say(False, f"the armed-sleeve probe raised: {type(exc).__name__}: {exc}")

    # ---- item 3: the adopt path, on THIS host's own ExecutionEngine ----
    print("\n== behaviour 3: the adopt path rehydrates a time_stop position without raising ==")
    try:
        from src.components.execution import ExecutionEngine, TradeState
        for sleeve, sel, want_target in [("crypto", (), 4.0), (BTC, (), 2.0), (BTC, (BTC,), 5.0)]:
            inst = EP.native_policy_instrumentation(sleeve, frontier_exits=sel)
            rec = {"instrumentation": inst, "execution": {"ticket": 1}, "sleeve": sleeve,
                   "symbol": "BTCUSD", "reconstructed_from_sleeve_identity": True}
            eng = ExecutionEngine.__new__(ExecutionEngine)
            eng.config = {}
            eng.active_trade = TradeState(
                ticket=1, direction="LONG", entry_price=ENTRY, stop_loss=ENTRY - STOP,
                take_profit_1=ENTRY + 2 * STOP, take_profit_2=0.0, take_profit_3=0.0,
                initial_volume=0.10, current_volume=0.10, sl_distance=STOP)
            eng.active_trade.trade_id = "az_verify"
            eng.active_trade.symbol = "BTCUSD"
            eng.active_trade.entry_time = "2026-06-15T00:00:00+00:00"
            ok = ExecutionEngine.hydrate_vnext_dynamic_policy_from_record(
                eng, rec, modify_broker_tp=False)
            got = eng.active_trade.gtos_vnext_dynamic_final_target_r
            label = f"{sleeve}{' + selection' if sel else ''}"
            say(bool(ok) and abs(got - want_target) < 1e-9,
                f"adopt-missing-record on {label}: rehydrated, final_target_r={got} "
                f"(expected {want_target})")
        say(None, "no KeyError is possible here: this host's execution.py carries the "
                  "`selected_policy == \"time_stop\"` branch from lineage commit b36d9ab92, "
                  "which mainline never received. That is why execution.py is NOT in this "
                  "carry — see MANIFEST.json -> not_carried.")
    except BaseException as exc:  # noqa: BLE001
        say(False, f"the adopt probe raised: {type(exc).__name__}: {exc}")

    # ---- item 4: the launch banner renders for every wired sleeve ----
    print("\n== behaviour 4: the launch banner cannot kill the worker (B1852) ==")
    try:
        for sleeve in sorted(EP.FRONTIER_EXIT_OVERRIDES):
            text = EP.describe_frontier_contract(sleeve)
            say(bool(text) and text != "no wired override",
                f"--frontier-exits {sleeve} -> banner renders {text!r}")
    except BaseException as exc:  # noqa: BLE001
        say(False, f"the banner probe raised: {type(exc).__name__}: {exc}")

    # ---- item 5: the selection is not, and must never become, a config key ----
    print("\n== behaviour 5: the selection is not a config key (the token binds config bytes) ==")
    try:
        from src.components.ultimate_book import bridge
        keys = set(getattr(bridge, "DEFAULT_CONFIG", {}))
        offenders = sorted(k for k in keys if "frontier" in str(k).lower())
        say(not offenders, f"no frontier key in bridge.DEFAULT_CONFIG ({offenders or 'none'}) — "
                           f"a key there would need the activation token re-minted, and a key "
                           f"read through bridge._bool is the shape that stood an armed book "
                           f"down every tick with a healthy heartbeat (AR)")
    except BaseException as exc:  # noqa: BLE001
        say(False, f"the config-key probe raised: {type(exc).__name__}: {exc}")

    return FAIL if problems_since(mark) else PASS


def check_behaviour(root: Path, man: dict) -> int:
    try:
        return _check_behaviour_inner(root, man)
    except BaseException as exc:  # noqa: BLE001
        say(False, f"the behaviour gate itself raised: {type(exc).__name__}: {exc}")
        return FAIL


# --------------------------------------------------------------------------------------
# 6. rollback
# --------------------------------------------------------------------------------------

def _load_backup_manifest(root: Path) -> dict | None:
    """The ceremony writes `BACKUP_MANIFEST.json` beside its backup. Judging a rollback against
    the LINEAGE instead of against what the host was actually on is Session S's own defect, and
    it fails a CORRECT rollback — which, at 2 a.m. on a funded account, is the worst possible
    advice. Here the host's actual pre-carry state is knowable for three of four files and
    variant-dependent for `run_book.py`, so the manifest matters even more."""
    for cand in sorted(Path(root.parent).glob("gtos-*backup*/BACKUP_MANIFEST.json")):
        try:
            return json.loads(cand.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
    return None


def check_rollback(root: Path, man: dict) -> int:
    mark = len(_problems)
    backup = _load_backup_manifest(root)
    if backup:
        base = {k: v for k, v in (backup.get("files") or {}).items()}
        say(None, f"judging against the ceremony's BACKUP_MANIFEST.json ({len(base)} paths) — "
                  f"the state this host was ACTUALLY on")
    else:
        base = {}
        for rec in man["files"]:
            if rec["repo_path"] == "run_book.py":
                continue
            base[rec["repo_path"]] = rec["sha256_before_expected"]
        say(None, "no BACKUP_MANIFEST.json found — falling back to this manifest's declared "
                  "pre-carry bytes, and SKIPPING run_book.py, whose pre-carry bytes are "
                  "host-specific. Check the ceremony's backup directory rather than acting on "
                  "a run_book verdict this gate cannot give.")

    print("\n== rollback: is the tree back at the state the host was on? ==")
    for repo_path, want in sorted(base.items()):
        got = sha256_of(root / repo_path)
        if got == want:
            say(True, f"{repo_path}: restored")
        else:
            rec = next((r for r in man["files"] if r["repo_path"] == repo_path), None)
            carried = rec and (got == rec.get("sha256_after_carry") or
                               got in {s["sha256_after_carry"]
                                       for s in rec.get("accepted_before_states", [])})
            say(False, f"{repo_path}: " + ("still CARRIED — rollback incomplete" if carried
                                           else f"neither state, sha256={got}"))

    # Unconditional, and that is the point: gating this behind the byte phase meant that in
    # exactly the states where the tree does NOT start, the operator was told only "rollback
    # incomplete" and never told the host cannot start.
    print("\n  and does the tree start?")
    started = check_imports(root, man, quiet_header=True, expect_frontier=False)
    return FAIL if (problems_since(mark) or started != PASS) else PASS


# --------------------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Verify the AZ mx_btcusd activation carry.")
    ap.add_argument("--check", required=True,
                    choices=["preflight", "postflight", "deps", "imports", "behaviour",
                             "rollback", "all"])
    args = ap.parse_args()

    root = resolve_repo_root()
    check_interpreter(root)
    man = load_manifest()
    print(f"repo root : {root}")
    print(f"manifest  : {MANIFEST.name}  ({man['schema']}, session {man['session']})")

    if args.check == "preflight":
        rc = check_preflight(root, man)
    elif args.check == "postflight":
        rc = check_postflight(root, man)
    elif args.check == "deps":
        rc = check_deps(root, man)
    elif args.check == "imports":
        rc = check_imports(root, man)
    elif args.check == "behaviour":
        rc = check_behaviour(root, man)
    elif args.check == "rollback":
        rc = check_rollback(root, man)
    else:
        rc = PASS
        for fn in (check_postflight, check_deps, check_imports, check_behaviour):
            if fn(root, man) != PASS:
                rc = FAIL

    print("\n" + ("=" * 78))
    if rc == PASS:
        print(f"RESULT: PASS  ({args.check})")
    else:
        print(f"RESULT: FAIL  ({args.check}) — {len(_problems)} problem(s):")
        for p in _problems:
            print(f"  - {p.splitlines()[0]}")
    return rc


if __name__ == "__main__":
    sys.exit(main())

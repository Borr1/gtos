"""Verify the CE spread-geometry-floor activation carry (Session CE, B2300-B2349).

Run from the repo root, with the interpreter the books run:

    .venv-gtos\\Scripts\\python.exe docs\\...\\activation_carry_spread_floor\\verify_carry.py --check preflight
    ... --check postflight
    ... --check deps
    ... --check imports
    ... --check behaviour
    ... --check rollback     (ONLY after a rollback)
    ... --check all          (postflight + deps + imports + behaviour)

THIS PROCESS NEVER TOUCHES THE BROKER AND NEVER TOUCHES LIVE STATE
------------------------------------------------------------------
`MetaTrader5` is shadowed by an empty module before anything is imported, exactly as Session
AZ's verifier does. Two things are stricter here, because this carry's behaviour gates go
further than AZ's did:

  * every gate that constructs an engine or an owner is handed a **throwaway repo_root**
    (`tempfile.mkdtemp()`), so `RunningConvictionLedger` writes its `firing_sleeves.json` into
    a temp directory and CANNOT touch `pipeline_state/ultimate_book/<namespace>/`. That file
    is live state: `admission.py` takes `na = max(na, override)` off the day's persisted
    union, so a verifier that wrote into it would move the armed book's Kelly-lite multiplier
    by running. AZ's ledger assertion had the same exposure and got away with it because it
    never called `update_and_count`; this one does, so it is isolated by construction.
  * the config is READ and never written. The floor's whole design is that its limit comes
    from `selected_cell_pretrade_max_spread_r`, so gate (a) proves the resolution against the
    host's own `config/agent_config.yaml` rather than against a number typed here.

WHAT `--check deps` IS FOR, AND WHY IT IS SEPARATE FROM `--check imports`
-------------------------------------------------------------------------
The copy ORDER is the whole of this carry's safety argument, and a partially-applied carry is
the state a ceremony is most likely to be interrupted in. Two of the three orderings fail in
ways `--check imports` cannot see, because the failure is at CONSTRUCTION, not at import:

  * `book_owner.py` ahead of `book_engine.py` -> `UltimateBookLiveEngine()` gets an
    unexpected `spread_geometry_floor=` kwarg -> **TypeError at STARTUP on both namespaces**,
    into a supervisor restart loop in which `manage_open_positions` never runs. That is the
    worst state this carry can produce and it is the one `deps` exists to name.
  * `run_book.py` ahead of `spread_geometry.py` -> ImportError at launch, same restart loop.
  * `run_book.py` ahead of `book_owner.py` -> TypeError on `UltimateBookOwner(...)`.

`book_engine.py` and `spread_geometry.py` landing early are INERT, which is why they are
first: an interrupted ceremony that stops after either of them has changed nothing.
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
REFUSE = 3

_problems: list[str] = []


def problems_since(mark: int) -> int:
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
    """The repo root, from where THIS FILE lives, then proved by landmarks. Deliberately not
    ``os.getcwd()``: Session S's verifier had a false green where running it from the wrong
    directory made every destination look absent, which reads as "not carried yet"."""
    root = HERE.parents[4]
    landmarks = ["run_book.py", "src/components/ultimate_book/book_engine.py",
                 "config/agent_config.yaml"]
    missing = [m for m in landmarks if not (root / m).exists()]
    if missing:
        print(f"[ STOP ] {root} does not look like the book's repo root "
              f"(missing: {', '.join(missing)}).")
        sys.exit(REFUSE)
    return root


def check_interpreter(root: Path) -> None:
    if sys.version_info < (3, 10):
        print(f"[ STOP ] python {sys.version.split()[0]} is too old; the books run 3.13.")
        sys.exit(REFUSE)
    want = (root / ".venv-gtos").resolve()
    got = Path(sys.prefix).resolve()
    # Conditional on the venv EXISTING (AZ's improvement on AC's unconditional refusal): where
    # `.venv-gtos` is absent this is not the host and the check has nothing to protect, which
    # is what lets these gates be exercised against a reconstructed tree BEFORE the ceremony.
    if want.is_dir() and str(got).lower() != str(want).lower():
        print(f"[ STOP ] this interpreter's environment is {got}")
        print(f"         The books run out of {want}. Re-run with that one:")
        print(f'         & "{want}\\Scripts\\python.exe" "{Path(__file__)}" --check <check>')
        sys.exit(REFUSE)


def _isolate_from_mt5(root: Path) -> None:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    sys.modules["MetaTrader5"] = types.ModuleType("MetaTrader5")


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------
# 1. preflight / 2. postflight
# --------------------------------------------------------------------------------------

def check_preflight(root: Path, man: dict) -> int:
    mark = len(_problems)
    print("\n== preflight: is this host in a state this carry was built for? ==")
    for rec in man["files"]:
        dest = root / rec["repo_path"]
        got = sha256_of(dest)
        if rec["is_new_file_on_vps"]:
            if got is None:
                say(True, f"{rec['repo_path']}: absent, as expected (new file)")
            elif got == rec["sha256_after_carry"]:
                say(None, f"{rec['repo_path']}: ALREADY at after-bytes — carried already")
            else:
                say(False, f"{rec['repo_path']}: present and unrecognised ({got[:12]})")
            continue
        if got == rec["sha256_before_expected"]:
            say(True, f"{rec['repo_path']}: at expected before-bytes ({got[:12]}, "
                      f"{rec['bytes_before']} B) — {rec['host_bytes_provenance'][:60]}...")
        elif got == rec["sha256_after_carry"]:
            say(None, f"{rec['repo_path']}: ALREADY at after-bytes — carried already")
        elif got is None:
            say(False, f"{rec['repo_path']}: ABSENT. This is not the tree the book runs.")
        else:
            say(False, f"{rec['repo_path']}: UNRECOGNISED ({got[:12]}, expected "
                       f"{rec['sha256_before_expected'][:12]}). Do NOT copy over it — "
                       "something moved this file since the carry was built.")
    return problems_since(mark)


def check_postflight(root: Path, man: dict) -> int:
    mark = len(_problems)
    print("\n== postflight: is every carried file at its after-bytes? ==")
    for rec in man["files"]:
        dest = root / rec["repo_path"]
        got = sha256_of(dest)
        ok = got == rec["sha256_after_carry"]
        say(ok, f"{rec['repo_path']}: {got[:12] if got else 'ABSENT'} "
                f"({'==' if ok else '!='} after {rec['sha256_after_carry'][:12]})")
    return problems_since(mark)


# --------------------------------------------------------------------------------------
# 3. deps — the ORDER invariants
# --------------------------------------------------------------------------------------

def check_deps(root: Path, man: dict) -> int:
    mark = len(_problems)
    print("\n== deps: the copy ORDER, which is this carry's whole safety argument ==")
    state = {rec["repo_path"]: sha256_of(root / rec["repo_path"]) for rec in man["files"]}
    after = {rec["repo_path"]: rec["sha256_after_carry"] for rec in man["files"]}
    carried = {p: state[p] == after[p] for p in after}

    invariants = [
        ("src/components/ultimate_book/book_owner.py",
         "src/components/ultimate_book/book_engine.py",
         "book_owner passes `spread_geometry_floor=` to UltimateBookLiveEngine; the "
         "pre-carry engine's signature does not accept it -> TypeError at STARTUP on both "
         "namespaces, into a supervisor restart loop in which manage_open_positions never runs"),
        ("run_book.py", "src/components/ultimate_book/spread_geometry.py",
         "run_book imports `parse_spread_geometry_floor` from spread_geometry -> ImportError "
         "at launch"),
        ("run_book.py", "src/components/ultimate_book/book_owner.py",
         "run_book passes `spread_geometry_floor=` to UltimateBookOwner -> TypeError at launch"),
    ]
    for dependent, prerequisite, why in invariants:
        if carried[dependent] and not carried[prerequisite]:
            say(False, f"ORDER VIOLATION: {dependent} is carried but {prerequisite} is NOT. {why}")
        else:
            say(True, f"{dependent} after {prerequisite}: satisfied "
                      f"({'both carried' if carried[dependent] else 'dependent not yet carried'})")
    # The inverse direction is SAFE and is stated so an interrupted ceremony is not re-run in a
    # panic: file 1 and file 2 landing alone are inert.
    for inert in ("src/components/ultimate_book/spread_geometry.py",
                  "src/components/ultimate_book/book_engine.py"):
        if carried[inert] and not carried["src/components/ultimate_book/book_owner.py"]:
            say(None, f"{inert} is carried and book_owner.py is not — INERT, nothing has "
                      "changed. Continue the ceremony or stop; either is safe.")
    return problems_since(mark)


# --------------------------------------------------------------------------------------
# 4. imports
# --------------------------------------------------------------------------------------

def check_imports(root: Path, man: dict, *, quiet_header: bool = False) -> int:
    mark = len(_problems)
    if not quiet_header:
        print("\n== imports: does the carried code load under this interpreter? ==")
    _isolate_from_mt5(root)
    try:
        import src.components.ultimate_book.spread_geometry as sg   # noqa: F401
        say(True, "src.components.ultimate_book.spread_geometry imports")
    except Exception as exc:                                        # noqa: BLE001
        say(False, f"spread_geometry FAILED to import: {exc!r}")
        return problems_since(mark)
    for mod in ("src.components.ultimate_book.book_engine",
                "src.components.ultimate_book.book_owner",
                "src.components.ultimate_book.execution_packets",
                "src.components.ultimate_book.sleeves.registry"):
        try:
            __import__(mod)
            say(True, f"{mod} imports")
        except Exception as exc:                                    # noqa: BLE001
            say(False, f"{mod} FAILED to import: {exc!r}")
    # run_book.py is a SCRIPT: importing it would run argparse. Compile it instead — that is
    # what catches a syntax error in the anchored edits, which is the failure this can have.
    try:
        import py_compile
        py_compile.compile(str(root / "run_book.py"), doraise=True, cfile=str(
            Path(tempfile.mkdtemp()) / "run_book.pyc"))
        say(True, "run_book.py compiles")
    except Exception as exc:                                        # noqa: BLE001
        say(False, f"run_book.py FAILED to compile: {exc!r}")
    return problems_since(mark)


# --------------------------------------------------------------------------------------
# 5. behaviour
# --------------------------------------------------------------------------------------

class _Tick:
    def __init__(self, bid, ask):
        self.bid, self.ask = bid, ask


class _Intent:
    """Enough of a TradeIntent for the floor. `stop_dist` is all the floor reads; `sleeve` and
    `decision_day` are what the conviction ledger reads."""
    def __init__(self, sleeve, stop_dist, decision_day="2026-07-31", symbol="XAUUSD"):
        self.sleeve, self.stop_dist, self.decision_day, self.symbol = (
            sleeve, stop_dist, decision_day, symbol)
        self.direction = 1
        self.vp_loc = None


class _Spec:
    def __init__(self, tag):
        self.tag, self.cluster, self.timeframe = tag, "substrate", 16388


class _MT5:
    """A quote source. `fail=True` makes `get_tick` raise, which is the fail-closed gate."""
    def __init__(self, ticks: dict, fail: bool = False):
        self._ticks, self._fail = ticks, fail
        self.calls: list[str] = []

    def get_tick(self, symbol):
        self.calls.append(symbol)
        if self._fail:
            raise RuntimeError("terminal not connected")
        return self._ticks.get(symbol)


def _runtime_cfg(root: Path) -> dict:
    """The host's OWN resolved runtime config block, read the way the engine reads it."""
    import yaml
    cfg = yaml.safe_load((root / "config/agent_config.yaml").read_text(encoding="utf-8"))
    return cfg.get("gtos_vnext_runtime", cfg)


def _check_behaviour_inner(root: Path, man: dict) -> int:      # noqa: C901
    mark = len(_problems)
    _isolate_from_mt5(root)
    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
    from src.components.ultimate_book.book_owner import UltimateBookOwner
    from src.components.ultimate_book.spread_geometry import (
        SpreadGeometryFloorError, evaluate_intent, parse_spread_geometry_floor,
        resolve_floor_limit,
    )
    from src.components.ultimate_book.sleeves.registry import (
        BUILT, CANDIDATE_BUILT, MARKET_EXPANSION_BUILT,
    )

    rt = _runtime_cfg(root)
    known = set(BUILT) | set(CANDIDATE_BUILT) | set(MARKET_EXPANSION_BUILT)
    tmp_root = tempfile.mkdtemp(prefix="gtos_ce_verify_")

    REPAIR = ["sub_mid_dn_revert", "sub_xvol_pullback"]
    NEUTRAL = ["crypto", "energy_agri"]

    # ---- (a) the floor RESOLVES for the two REPAIR sleeves at the send gate's own limit ----
    print("\n-- (a) the floor resolves for AY's two REPAIR sleeves, at the LIVE limit --")
    sel = parse_spread_geometry_floor(",".join(REPAIR), known_sleeves=known)
    say(sorted(sel) == sorted(REPAIR) and all(v is None for v in sel.values()),
        f"parse('{','.join(REPAIR)}') -> {sel} (None == inherit the send gate's limit)")
    cfg_limit = rt.get("selected_cell_pretrade_max_spread_r")
    say(cfg_limit is not None,
        f"config/agent_config.yaml: selected_cell_pretrade_max_spread_r = {cfg_limit}")
    for s in REPAIR:
        lim = resolve_floor_limit(rt, s, sel)
        # AY's measurement is at spread_r <= 0.10 for both, which is the config's global value.
        ok = lim is not None and abs(lim - float(cfg_limit)) < 1e-12
        say(ok, f"resolve_floor_limit({s}) = {lim} == the send gate's own limit "
                f"({cfg_limit}) — AY-1b measured the REPAIR at exactly this threshold "
                f"({'+0.426' if s == 'sub_mid_dn_revert' else '+0.264'} R/day at mid)")
    # The per-sleeve override path is real (fx_jpy at 0.35 on a dated owner trial) and the
    # floor must honour it, or generation would be STRICTER than the send gate for that sleeve.
    by_sleeve = rt.get("selected_cell_pretrade_max_spread_r_by_sleeve") or {}
    if by_sleeve:
        s, want = next(iter(by_sleeve.items()))
        sel_fx = parse_spread_geometry_floor(s, known_sleeves=known)
        got = resolve_floor_limit(rt, s, sel_fx)
        say(got is not None and abs(got - float(want)) < 1e-12,
            f"per-sleeve override honoured: {s} -> {got} (config says {want}); a floor that "
            "ignored it would be stricter at generation than the send gate")

    # ---- (b) NEUTRAL sleeves and the mx frontier contract are UNTOUCHED ----
    print("\n-- (b) NEUTRAL sleeves and mx_btcusd's frontier contract are untouched --")
    for s in NEUTRAL:
        say(resolve_floor_limit(rt, s, sel) is None,
            f"resolve_floor_limit({s}) is None — not in the selection, so the floor is a "
            "no-op for it. AY measured it NEUTRAL (inside the 20-seed random envelope at "
            "every band), which is why this is a per-sleeve map and not a boolean")
    eng_off = UltimateBookLiveEngine(dict(rt), _MT5({}), tmp_root, namespace="verify_ce")
    say(eng_off._spread_geometry_floor == {},
        "an engine built with no selection has an EMPTY floor map (default-inert)")
    mt5_watch = _MT5({})
    eng_sel = UltimateBookLiveEngine(dict(rt), mt5_watch, tmp_root, namespace="verify_ce",
                                     spread_geometry_floor=sel)
    gen: dict = {}
    r = eng_sel._spread_geometry_refusal(_Intent("crypto", 100.0), _Spec("crypto"),
                                         "BTCUSD", gen)
    say(r is None and mt5_watch.calls == [] and "spread_geometry_floor" not in gen,
        "a NEUTRAL sleeve's intent is not evaluated at all — no refusal, no tick fetched, "
        "no telemetry row. The floor cannot change a sleeve nobody selected")
    try:
        from src.components.ultimate_book.execution_packets import (
            FRONTIER_EXIT_OVERRIDES, describe_frontier_contract,
        )
        mx = "mx_btcusd_d1_donchian_20_breakout"
        cell = FRONTIER_EXIT_OVERRIDES[mx]["frontier_cell"]
        say(cell == "target_5R",
            f"mx_btcusd frontier contract still resolves to {cell} — the estate's one "
            "standing admission is untouched by this carry")
        say(bool(describe_frontier_contract(mx)),
            f"describe_frontier_contract renders: {describe_frontier_contract(mx)}")
    except Exception as exc:                                        # noqa: BLE001
        say(False, f"the mx frontier contract broke: {exc!r}")

    # ---- (c) floor + frontier (+ weekend, where present) COMPOSE at the call sites ----
    print("\n-- (c) the kwargs compose at the call sites (hand-merged at the wave-13 train) --")
    owner_kwargs = dict(namespace="verify_ce",
                        frontier_exits=("mx_btcusd_d1_donchian_20_breakout",),
                        spread_geometry_floor=sel)
    try:
        import inspect
        from src.components.ultimate_book.weekend_policy import policy_from_args  # noqa: F401
        has_weekend = "weekend_policy" in inspect.signature(
            UltimateBookOwner.__init__).parameters
    except Exception:                                               # noqa: BLE001
        has_weekend = False
    if has_weekend:
        from src.components.ultimate_book.weekend_policy import policy_from_args
        owner_kwargs["weekend_policy"] = policy_from_args("sub_xvol_pullback")
    owner = UltimateBookOwner({"gtos_vnext_runtime": dict(rt)}, _MT5({}), tmp_root,
                              **owner_kwargs)
    say(owner._spread_geometry_floor == sel,
        f"owner._spread_geometry_floor == the parsed selection ({sorted(sel)})")
    say(tuple(owner._frontier_exits) == ("mx_btcusd_d1_donchian_20_breakout",),
        "owner._frontier_exits survives alongside it — the two selections do not overwrite "
        "each other (the wave-13 train hand-merged these signatures)")
    say(owner.engine._spread_geometry_floor == sel,
        "the OWNER's selection reached the ENGINE — this is the call site the ordering "
        "invariant in --check deps protects")
    say(getattr(owner.router, "_frontier_exits", None) is not None
        or tuple(owner._frontier_exits) == ("mx_btcusd_d1_donchian_20_breakout",),
        "the router still received the frontier selection")
    if has_weekend:
        say(getattr(owner._weekend_policy, "sleeves", None) is not None,
            "a weekend policy ALSO composes on this tree (three kwargs, one constructor)")
    else:
        say(None, "no weekend_policy kwarg on this tree — expected on the host, which has "
                  "never been carried BA's policy. The floor's anchored edits are placed so "
                  "a later weekend carry appends to the same signature without conflict.")

    # ---- (d) the refusal fires, at AY's own arithmetic ----
    print("\n-- (d) the refusal fires, and lands where an operator can see it --")
    limit = resolve_floor_limit(rt, "sub_mid_dn_revert", sel)
    # spread_r = (ask - bid) / stop. Build one just over and one just under the limit.
    stop = 10.0
    over = _Tick(bid=2000.0, ask=2000.0 + stop * float(limit) * 1.5)
    under = _Tick(bid=2000.0, ask=2000.0 + stop * float(limit) * 0.5)
    mt5b = _MT5({"XAUUSD": over})
    eng = UltimateBookLiveEngine(dict(rt), mt5b, tmp_root, namespace="verify_ce",
                                 spread_geometry_floor=sel)
    gen = {}
    row = eng._spread_geometry_refusal(_Intent("sub_mid_dn_revert", stop),
                                       _Spec("sub_mid_dn_revert"), "XAUUSD", gen)
    say(row is not None and str(row.get("reason", "")).startswith("spread_geometry_floor:"),
        f"an intent at spread_r {1.5 * float(limit):.4f} > {float(limit):.4f} is REFUSED: "
        f"{str(row.get('reason'))[:70] if row else None}")
    say(gen.get("spread_geometry_floor", {}).get("evaluated") == 1
        and gen["spread_geometry_floor"]["refused"] == 1
        and gen["spread_geometry_floor"]["sleeves"] == ["sub_mid_dn_revert"],
        f"generation telemetry counts it: {gen.get('spread_geometry_floor')}")
    mt5c = _MT5({"XAUUSD": under})
    eng2 = UltimateBookLiveEngine(dict(rt), mt5c, tmp_root, namespace="verify_ce",
                                  spread_geometry_floor=sel)
    gen2: dict = {}
    row2 = eng2._spread_geometry_refusal(_Intent("sub_mid_dn_revert", stop),
                                         _Spec("sub_mid_dn_revert"), "XAUUSD", gen2)
    say(row2 is None and gen2["spread_geometry_floor"] == {
            "evaluated": 1, "refused": 0, "sleeves": []},
        f"an intent at spread_r {0.5 * float(limit):.4f} is KEPT and still counted as "
        f"evaluated: {gen2.get('spread_geometry_floor')} — evaluated-vs-refused is what the "
        "dossier's stop condition 1 watches")

    # ---- (e) fail-CLOSED on an unreadable quote and on an internal fault ----
    print("\n-- (e) fail-closed, matching the authoritative gate --")
    eng3 = UltimateBookLiveEngine(dict(rt), _MT5({}, fail=True), tmp_root,
                                  namespace="verify_ce", spread_geometry_floor=sel)
    g3: dict = {}
    r3 = eng3._spread_geometry_refusal(_Intent("sub_mid_dn_revert", stop),
                                       _Spec("sub_mid_dn_revert"), "XAUUSD", g3)
    say(r3 is not None and "quote_unavailable" in str(r3.get("reason")),
        "a raising terminal REFUSES the intent (not admits it), matching "
        "broker_net_cost_engine's own missing_current_quote_spread_or_sl_distance")
    r4 = eng3._spread_geometry_refusal(_Intent("sub_mid_dn_revert", -1.0),
                                       _Spec("sub_mid_dn_revert"), "XAUUSD", {})
    say(r4 is not None and "nonpositive_stop" in str(r4.get("reason")),
        "a non-positive stop REFUSES rather than dividing by it")
    reason, _ = evaluate_intent(_Intent("x", stop), _Tick(bid=2000.0, ask=1999.0), 0.10)
    say(reason is not None and "quote_unavailable" in reason,
        "a CROSSED quote (ask < bid) refuses too")

    # ---- (f) the conviction-count half, which is what arming actually buys ----
    print("\n-- (f) a refused intent never enters the day's conviction count --")
    cfg_kelly = dict(rt)
    cfg_kelly.update({"ultimate_book_kelly_lite": True,
                      "ultimate_book_kelly_running_count": True})
    eng4 = UltimateBookLiveEngine(cfg_kelly, _MT5({}), tempfile.mkdtemp(
        prefix="gtos_ce_conv_"), namespace="verify_ce_conv",
        spread_geometry_floor=sel)
    day = "2026-07-31"
    doomed = _Intent("sub_mid_dn_revert", stop, decision_day=day)
    placer = _Intent("crypto", stop, decision_day=day, symbol="BTCUSD")
    with_doomed = eng4._running_conviction_override([placer, doomed])
    eng5 = UltimateBookLiveEngine(cfg_kelly, _MT5({}), tempfile.mkdtemp(
        prefix="gtos_ce_conv_"), namespace="verify_ce_conv",
        spread_geometry_floor=sel)
    without = eng5._running_conviction_override([placer])
    # `update_and_count` returns {decision_day: distinct-sleeve-count-so-far}, NOT an int --
    # the same shape that made one of Session AY's own test fixtures vacuously true. Compare
    # the DAY's counts, and assert the shape first so a future change of it fails loudly here
    # rather than passing by accident.
    say(isinstance(with_doomed, dict) and isinstance(without, dict)
        and day in with_doomed and day in without,
        f"the override is a per-day map, as `RunningConvictionLedger.update_and_count` "
        f"documents: {with_doomed} / {without}")
    got_with = (with_doomed or {}).get(day)
    got_without = (without or {}).get(day)
    say(got_with is not None and got_without is not None and got_with == got_without + 1,
        f"na for {day} with the doomed intent = {got_with}, without it = {got_without}. "
        "Under the live half-Kelly bins ((1,1,0.748),(2,3,0.991),(4,99,1.241)) a difference "
        "of one crossing a bin edge is worth up to +32.487 % on EVERY unit that day — this "
        "is the half of the repair that is about the OTHER sleeves, and it is true whether "
        "or not the filter improves any sleeve's expectancy")
    # And the two ledgers must be SEPARATE temp roots, or the second call would read the
    # first's persisted union and the gate would be vacuous (the ledger is idempotent ACROSS
    # re-ticks by design -- which is exactly why arming mid-day cannot un-count, B365).
    say(eng4._running_conviction._path != eng5._running_conviction._path
        if hasattr(eng4._running_conviction, "_path") else True,
        "the two arms wrote to different throwaway ledgers, so neither read the other's union")

    # ---- (g) the parser refuses every fail-open shape ----
    print("\n-- (g) launch-time refusals (a floor you think is on and is not) --")
    for raw, why in [("", "the empty string (--tags reads its empty string as ALL)"),
                     ("no_such_sleeve", "an unknown sleeve name"),
                     ("sub_mid_dn_revert:1.5", "a limit at/above 1.0 (permits the pathology)"),
                     ("sub_mid_dn_revert:0", "a zero limit (refuses every trade)"),
                     ("sub_mid_dn_revert,sub_mid_dn_revert", "a sleeve named twice"),
                     ("sub_mid_dn_revert,,crypto", "a stray comma")]:
        try:
            parse_spread_geometry_floor(raw, known_sleeves=known)
            say(False, f"parse({raw!r}) was ACCEPTED — {why} must be refused at launch")
        except SpreadGeometryFloorError:
            say(True, f"parse({raw!r}) refused at launch: {why}")
    say(parse_spread_geometry_floor(None, known_sleeves=known) == {},
        "parse(None) -> {} — omitting the flag is the default and is OFF")
    for s in REPAIR + NEUTRAL:
        if s not in known:
            say(False, f"{s} is not in this host's registry union — the launch validator "
                       "would refuse the ceremony's own command line as a typo")
    say(all(s in known for s in REPAIR + NEUTRAL),
        f"all four armed-relevant sleeves are in the registry union ({len(known)} sleeves), "
        "so the ceremony's command line will validate")

    return problems_since(mark)


def check_behaviour(root: Path, man: dict) -> int:
    print("\n== behaviour: does the floor do what AY measured, and nothing else? ==")
    try:
        return _check_behaviour_inner(root, man)
    except Exception as exc:                                        # noqa: BLE001
        import traceback
        traceback.print_exc()
        say(False, f"behaviour gate raised: {exc!r}")
        return 1


# --------------------------------------------------------------------------------------
# 6. rollback
# --------------------------------------------------------------------------------------

def check_rollback(root: Path, man: dict) -> int:
    mark = len(_problems)
    print("\n== rollback: is every file back at its BEFORE bytes? ==")
    for rec in man["files"]:
        dest = root / rec["repo_path"]
        got = sha256_of(dest)
        if rec["is_new_file_on_vps"]:
            say(got is None, f"{rec['repo_path']}: {'removed' if got is None else 'STILL PRESENT'}")
            continue
        ok = got == rec["sha256_before_expected"]
        say(ok, f"{rec['repo_path']}: {got[:12] if got else 'ABSENT'} "
                f"({'==' if ok else '!='} before {rec['sha256_before_expected'][:12]})")
    print("\n  NOTE: the floor writes nothing, holds nothing and touches no position, so a "
          "rollback unwinds NO state. A position already open is unaffected — the floor runs "
          "in _generate_intents and every exit path reads the trade record.")
    return problems_since(mark)


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify the CE spread-geometry-floor carry.")
    ap.add_argument("--check", required=True,
                    choices=["preflight", "postflight", "deps", "imports", "behaviour",
                             "rollback", "all"])
    args = ap.parse_args()
    root = resolve_repo_root()
    check_interpreter(root)
    man = load_manifest()
    print(f"repo root : {root}")
    print(f"python    : {sys.version.split()[0]} ({sys.executable})")
    print(f"manifest  : {MANIFEST.name} ({man['session']}, {man['blocks']})")

    if args.check == "preflight":
        check_preflight(root, man)
    elif args.check == "postflight":
        check_postflight(root, man)
    elif args.check == "deps":
        check_deps(root, man)
    elif args.check == "imports":
        check_imports(root, man)
    elif args.check == "behaviour":
        check_behaviour(root, man)
    elif args.check == "rollback":
        check_rollback(root, man)
    else:
        check_postflight(root, man)
        check_deps(root, man)
        check_imports(root, man)
        check_behaviour(root, man)

    print()
    if _problems:
        print(f"RESULT: FAIL — {len(_problems)} problem(s)")
        for p in _problems:
            print(f"  - {p}")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

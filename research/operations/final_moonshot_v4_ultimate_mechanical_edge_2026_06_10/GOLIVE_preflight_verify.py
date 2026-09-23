#!/usr/bin/env python3
"""GOLIVE_preflight_verify.py — owner-run pre-flight gate (READ-ONLY, no broker, no flip).

Run this BEFORE any go-live flip. It is fail-closed: any failed check exits non-zero and
prints the blocking reason. It performs NO broker / MT5 / network / order work and it does
NOT modify config or remove the halt file. It only asserts that the deployable surface is in
a safe, tested, parity-clean, DEFAULT-OFF state and that the physical halt control is present.

Checks (all must PASS):
  1. HALT-FILE PRESENT      — pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag exists and the
                              atomic halt guard reports active (the physical deployment control).
  2. DEFAULT-OFF            — ultimate_book_live_package default surface is the locked 8-sleeve
                              book; every upgrade flag (clean3/clean4/overlays/vp_acceptance/
                              stress_derisk/kelly_lite) defaults False.
  3. TESTS PASS             — all test_* functions in test_ultimate_book_live_package.py pass
                              (no pytest dependency required; uses a built-in plain-assert runner).
  4. PARITY HOLDS           — assert_clean3_parity().parity_ok and assert_confidence_parity().parity_ok.
  5. BROAD-SELECTOR DISABLE — informational: reports whether the proven-losing broad V4 selector
                              is still ENABLED in config (it should be staged-disabled before live).
                              Reported as a WARN by default; pass --require-broad-selector-off to
                              make a still-enabled broad selector a hard FAIL.

Usage (from anywhere):
  ROOT=/Users/borr/Documents/gtos/repo/ai-trading-agent
  ROUTE=$ROOT/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10
  /opt/homebrew/bin/python3 $ROUTE/GOLIVE_preflight_verify.py
  # optionally:  --require-broad-selector-off   (hard-fail if the loser is still on)

Exit codes:
  0 = all required checks PASS (safe pre-flight state; flip still requires the owner-domain
      broker/runtime AUTHORITY work in the readiness checklist — this script does NOT clear that).
  1 = at least one required check FAILED. DO NOT flip.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]  # repo root: research/operations/<route> -> repo
for p in (str(ROOT), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def _ok(msg: str) -> None:
    print(f"  {GREEN}PASS{RESET}  {msg}")


def _fail(msg: str) -> None:
    print(f"  {RED}FAIL{RESET}  {msg}")


def _warn(msg: str) -> None:
    print(f"  {YELLOW}WARN{RESET}  {msg}")


def check_halt_file_present() -> bool:
    print("[1] HALT-FILE PRESENT (physical deployment control)")
    ok = True
    try:
        from src.safety.runtime_halt import read_runtime_halt_state  # type: ignore

        snap = read_runtime_halt_state(repo_root=str(ROOT))
        if snap.active:
            _ok(f"atomic halt guard reports ACTIVE ({len(snap.active_flags)} flag(s))")
            for f in snap.active_flags:
                _ok(f"  active flag: {f.get('path')}")
        else:
            _fail("atomic halt guard reports CLEAR — no halt flag active; the physical control is OFF")
            ok = False
    except Exception as exc:  # noqa: BLE001
        _warn(f"could not import runtime_halt guard ({exc!r}); falling back to direct file check")

    hard_flag = ROOT / "pipeline_state" / "GTOS_HARD_PRODUCTION_HALT.flag"
    if hard_flag.exists():
        _ok(f"hard-halt flag present: {hard_flag}")
    else:
        _fail(f"hard-halt flag MISSING: {hard_flag}")
        ok = False
    return ok


def check_default_off() -> bool:
    print("[2] DEFAULT-OFF (deployable surface ships with every upgrade flag OFF)")
    ok = True
    try:
        import inspect

        import ultimate_book_live_package as u  # type: ignore
    except Exception as exc:  # noqa: BLE001
        _fail(f"cannot import ultimate_book_live_package: {exc!r}")
        return False

    sig = inspect.signature(u.admit_and_size)
    must_be_false = {
        "include_clean3", "include_clean4", "overlays",
        "vp_acceptance", "stress_derisk", "kelly_lite", "kelly_conservative",
    }
    for name in sorted(must_be_false):
        if name not in sig.parameters:
            _fail(f"admit_and_size missing expected flag '{name}'")
            ok = False
            continue
        default = sig.parameters[name].default
        if default is False:
            _ok(f"admit_and_size(..., {name}=False) default-off")
        else:
            _fail(f"admit_and_size '{name}' default is {default!r}, expected False")
            ok = False

    book = u.describe_book()
    if book.get("clean3", {}).get("default_off") is True:
        _ok("describe_book().clean3.default_off == True")
    else:
        _fail("describe_book().clean3.default_off is not True")
        ok = False
    if book.get("clean4", {}).get("default_off") is True:
        _ok("describe_book().clean4.default_off == True")
    else:
        _fail("describe_book().clean4.default_off is not True")
        ok = False

    # The default profile is the locked 8-sleeve conservative book, not a growth dial.
    if book.get("default_profile") == getattr(u, "DEFAULT_PROFILE", None):
        _ok(f"default_profile == {book.get('default_profile')} (locked book, not a growth dial)")
    else:
        _warn(f"default_profile is {book.get('default_profile')!r}")
    return ok


def check_tests_pass() -> bool:
    print("[3] TESTS PASS (test_ultimate_book_live_package.py; no pytest dependency)")
    test_path = HERE / "test_ultimate_book_live_package.py"
    if not test_path.exists():
        _fail(f"test file not found: {test_path}")
        return False
    spec = importlib.util.spec_from_file_location("_goldlive_testmod", str(test_path))
    if spec is None or spec.loader is None:
        _fail("could not load test module spec")
        return False
    mod = importlib.util.module_from_spec(spec)
    mod.__name__ = "_goldlive_testmod"  # keep the __main__ pytest block from firing
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:  # noqa: BLE001
        _fail(f"test module import failed: {exc!r}")
        traceback.print_exc()
        return False

    tests = sorted(
        (n, getattr(mod, n))
        for n in dir(mod)
        if n.startswith("test_") and callable(getattr(mod, n))
    )
    passed = 0
    failed: list[tuple[str, str]] = []
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as exc:  # noqa: BLE001
            failed.append((name, repr(exc)))
    if failed:
        for name, err in failed:
            _fail(f"{name}: {err}")
        _fail(f"collected {len(tests)} tests, {passed} passed, {len(failed)} FAILED")
        return False
    _ok(f"collected {len(tests)} tests, all {passed} passed")
    return True


def check_parity() -> bool:
    print("[4] PARITY HOLDS (replay-vs-module byte/weight parity)")
    ok = True
    try:
        import ultimate_book_live_package as u  # type: ignore
    except Exception as exc:  # noqa: BLE001
        _fail(f"cannot import ultimate_book_live_package: {exc!r}")
        return False
    try:
        c3 = u.assert_clean3_parity()
        if c3.get("parity_ok") is True and c3.get("vol_scale_ok") and c3.get("book_ok"):
            _ok(f"assert_clean3_parity parity_ok=True (vol_scale {c3.get('vol_scale_module')})")
        else:
            _fail(f"assert_clean3_parity NOT clean: {c3}")
            ok = False
    except Exception as exc:  # noqa: BLE001
        _fail(f"assert_clean3_parity raised: {exc!r}")
        ok = False
    try:
        cf = u.assert_confidence_parity()
        if cf.get("parity_ok") is True and not cf.get("mismatches"):
            _ok("assert_confidence_parity parity_ok=True")
        else:
            _fail(f"assert_confidence_parity NOT clean: {cf}")
            ok = False
    except Exception as exc:  # noqa: BLE001
        _fail(f"assert_confidence_parity raised: {exc!r}")
        ok = False
    return ok


def check_broad_selector(require_off: bool) -> bool:
    print("[5] BROAD-SELECTOR DISABLE (proven-losing V4 selector should be staged-OFF)")
    cfg_path = ROOT / "config" / "agent_config.yaml"
    if not cfg_path.exists():
        _warn(f"config not found: {cfg_path}")
        return True
    # Lightweight scan (no yaml dependency): inspect the selector_v4 apply/enabled flags.
    enabled = None
    applied = None
    for line in cfg_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("selector_v4_enabled:"):
            enabled = s.split(":", 1)[1].strip().lower().startswith("true")
        elif s.startswith("selector_v4_apply_to_execution:"):
            applied = s.split(":", 1)[1].strip().lower().startswith("true")
    broad_live = bool(enabled) and bool(applied)
    if not broad_live:
        _ok("broad V4 selector is NOT applied-to-execution (staged-disabled)")
        return True
    msg = ("broad V4 selector is STILL enabled+apply_to_execution in config "
           "(the -0.25R/fill loser). Apply GOLIVE_broad_selector_disable.patch before live.")
    if require_off:
        _fail(msg)
        return False
    _warn(msg + "  [advisory; pass --require-broad-selector-off to hard-fail]")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="GTOS go-live pre-flight verification (read-only).")
    ap.add_argument(
        "--require-broad-selector-off",
        action="store_true",
        help="treat a still-enabled broad V4 selector as a hard FAIL (default: WARN)",
    )
    args = ap.parse_args()

    print("=" * 72)
    print("GTOS GO-LIVE PRE-FLIGHT VERIFICATION (read-only; no broker, no flip)")
    print(f"repo_root = {ROOT}")
    print("=" * 72)

    results = {
        "halt_file_present": check_halt_file_present(),
        "default_off": check_default_off(),
        "tests_pass": check_tests_pass(),
        "parity_holds": check_parity(),
        "broad_selector": check_broad_selector(args.require_broad_selector_off),
    }

    print("=" * 72)
    all_ok = all(results.values())
    for name, ok in results.items():
        tag = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        print(f"  [{tag}] {name}")
    print("=" * 72)
    if all_ok:
        print(f"{GREEN}PRE-FLIGHT PASS{RESET} — deployable surface is safe/tested/parity-clean/default-off "
              "and the halt control is present.")
        print("NOTE: this does NOT authorize a flip. The owner-domain broker/runtime AUTHORITY gate "
              "(hard-halt forensic join, V3-vs-live gap audit, dual-broker audit, production-return "
              "dossier, FTMO credentials + VPS) must be cleared first. See GOLIVE_runbook_readiness.md.")
        return 0
    print(f"{RED}PRE-FLIGHT FAIL{RESET} — DO NOT flip. Resolve the FAILED checks above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

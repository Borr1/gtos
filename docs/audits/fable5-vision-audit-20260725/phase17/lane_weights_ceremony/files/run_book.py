#!/usr/bin/env python3
"""Live launcher for the W7 ultimate_book — one process owns the whole book.

    python run_book.py --profile operator_profile \
        --terminal-path "C:\\MT5\\FTMO\\terminal64.exe" --namespace operator_profile

SAFETY (default-OFF, fail-closed):
  - The ultimate_book authority gates in the merged config decide shadow vs live. Gates OFF -> the book
    only logs would_units and NEVER sends. Broker mutation requires explicit live_broker_authority=true.
  - The runtime-halt flag (pipeline_state/RESEARCH_RUNTIME_HALT.flag) and the operator kill-switch
    (pipeline_state/ULTIMATE_BOOK_KILL.flag) force observe-only each tick even if gated on.
  - Order idempotency: each (sleeve, symbol, decision_bar) sends at most once.
Use --once for a single read-only wiring tick.
"""
import argparse
import logging
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

# The activation directory is machine state, not repository state, and `.env`
# lives in the repository. `load_dotenv(override=True)` would let one untracked
# line relocate the authorization root — and the token layer will happily mint a
# fresh signing key wherever it is pointed, so relocation is not a broken
# config, it is a self-issued authorization. Snapshot the value the MACHINE set
# before `.env` is read, and put it back afterwards. See B103 and
# `activation_token.token_dir_is_inside_repo`.
_ACTIVATION_DIR_ENV = "GTOS_ACTIVATION_TOKEN_DIR"
_activation_dir_from_machine = os.environ.get(_ACTIVATION_DIR_ENV)

load_dotenv(override=True)

if os.environ.get(_ACTIVATION_DIR_ENV) != _activation_dir_from_machine:
    _dotenv_value = os.environ.get(_ACTIVATION_DIR_ENV)
    if _activation_dir_from_machine is None:
        os.environ.pop(_ACTIVATION_DIR_ENV, None)
    else:
        os.environ[_ACTIVATION_DIR_ENV] = _activation_dir_from_machine
    print(f"REFUSING the .env override of {_ACTIVATION_DIR_ENV} "
          f"({_dotenv_value!r}); using the machine value "
          f"{_activation_dir_from_machine!r}. The activation directory is machine state.",
          file=sys.stderr, flush=True)

from src.security import install_runtime_monitoring
install_runtime_monitoring()

from src.utils.config import apply_profile_overrides
from src.utils.broker_profile import assert_mt5_account_matches_profile
from src.mt5.mt5_real import RealMT5
from src.safety.activation_token import config_digest_for, token_dir
from src.components.ultimate_book.book_owner import UltimateBookOwner
from src.components.ultimate_book.bridge import config_bool_value
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
from src.components.ultimate_book.launcher import BookLauncher


class _BelowLevelFilter(logging.Filter):
    def __init__(self, max_level: int):
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < self.max_level


def configure_runtime_logging(level: int = logging.INFO) -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        except Exception:
            pass
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    stdout_handler.addFilter(_BelowLevelFilter(logging.ERROR))
    stdout_handler.setFormatter(formatter)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(stdout_handler)
    root.addHandler(stderr_handler)


def main():
    p = argparse.ArgumentParser(description="W7 ultimate_book live launcher")
    p.add_argument("--config", default="config/agent_config.yaml")
    p.add_argument("--profile", default="operator_profile",
                   help="Prop-firm profile overlay (config/profiles/<name>.yaml)")
    p.add_argument("--terminal-path", default=None,
                   help="MT5 terminal64.exe path; falls back to GTOS_MT5_TERMINAL_PATH / profile mt5.terminal_path")
    p.add_argument("--namespace", default="operator_profile",
                   help="State/ledger/log namespace under pipeline_state/ultimate_book/")
    p.add_argument("--poll-seconds", type=float, default=60.0)
    p.add_argument("--tags", default=None, help="Comma-separated sleeve tags to run (default: all BUILT)")
    p.add_argument("--lane-weights", default=None,
                   help="Signed gtos.lane_weights.v1 file; requires --lane-weights-key "
                        "and explicit --tags. Invalid/stale input becomes x1.00 everywhere.")
    p.add_argument("--lane-weights-key", default=None,
                   help="External HMAC verification key for --lane-weights.")
    p.add_argument("--kill-flag", default=None,
                   help="Per-instance operator kill-switch path (default pipeline_state/ULTIMATE_BOOK_KILL.flag). "
                        "Set a distinct path per account so FTMO and redacted_account can be braked independently.")
    p.add_argument("--once", action="store_true", help="Run a single tick and exit (wiring check)")
    p.add_argument("--frontier-exits", default=None,
                   help="Comma-separated sleeves to run on their WAVE-12 frontier exit contract "
                        "instead of the committed one (Session AU, B1550). The one this host is "
                        "carried for is mx_btcusd_d1_donchian_20_breakout -> target_5R: broker TP "
                        "5R instead of the generator's 2R, which is the exit the estate's ONE "
                        "standing admission is measured at (p 0.0011, admits at two of three cost "
                        "bands on the ratified RECORDED population, and REJECTS at all four bands "
                        "at the 2R the spec runs). sub_xvol_pullback -> target_4R is also wired and "
                        "IS ARMED ON BOTH ACCOUNTS at 3R -- it REJECTS at all four bands at the "
                        "ratified rule (Session AU section 1.3), so do not select it. Six further "
                        "default-off time-stop cells are wired and none of them is armed. Empty by "
                        "default. An empty string is REFUSED rather than read as 'all' (the --tags "
                        "fail-open, B359), and an unknown sleeve name is REFUSED rather than "
                        "dropped. FLIP AT A FLAT BOOK: a position adopted with no trade record is "
                        "rehydrated from the sleeve identity, so a pre-flip position's broker TP "
                        "would move. Set here rather than in agent_config.yaml or "
                        "profiles/redacted_account.yaml because BOTH are hashed into a live activation "
                        "token's config digest, and a byte moved there stops the armed book "
                        "placing until the token is re-minted.")
    p.add_argument("--spread-geometry-floor", default=None,
                   help="Comma-separated sleeves to run with the GENERATION-side "
                        "spread-geometry floor on, optionally with a per-sleeve spread_r "
                        "limit (`sub_mid_dn_revert` or `sub_mid_dn_revert:0.075`). Session AY, "
                        "B1810. A sleeve named WITHOUT a limit inherits the limit the send "
                        "gate will apply to it (`selected_cell_pretrade_max_spread_r`, with "
                        "the per-sleeve override), so the two layers cannot drift apart and an "
                        "owner config edit moves both at once. This book ALREADY refuses these "
                        "trades at the send layer; the floor refuses them EARLIER, which is "
                        "worth something for a reason that is about the OTHER sleeves: an "
                        "intent that reaches the intent list has already been counted by "
                        "`_running_conviction_override`, and `na = max(na, override)` is "
                        "monotone upward, so a sleeve whose every leg the cost gate refuses "
                        "still raises the day's Kelly-lite multiplier for every sleeve that "
                        "does place -- measured on this host's own export at 16 contaminated "
                        "account-days, 3 of which moved the multiplier, worst +25.227 %%. "
                        "REPAIR at the ratified rule on `sub_mid_dn_revert` (+0.426 R/day at "
                        "mid, 46.9 %% of its trades over the limit) and `sub_xvol_pullback` "
                        "(+0.264, on 6 dropped trades of 85); NEUTRAL on `crypto` and "
                        "`energy_agri`, which is why this is a per-sleeve map and not a "
                        "boolean. FAIL-CLOSED: an opted-in sleeve whose quote cannot be read "
                        "proposes nothing that tick, matching the authoritative gate's own "
                        "`missing_current_quote_spread_or_sl_distance`. Empty by default. An "
                        "empty string is REFUSED rather than read as 'all' (the --tags "
                        "fail-open, B359) and an unknown sleeve name is REFUSED rather than "
                        "dropped. Set here rather than in agent_config.yaml or "
                        "profiles/redacted_account.yaml because BOTH are hashed into a live "
                        "activation token's config digest.")
    args = p.parse_args()

    configure_runtime_logging(logging.INFO)

    # SINGLE-INSTANCE guard per namespace: a second live book on the same account = double-trade.
    # Refuse to start if another run_book for this namespace is already alive (stale lock is ignored).
    from pathlib import Path
    def _pid_alive(pid: int) -> bool:
        try:
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
            if h:
                ctypes.windll.kernel32.CloseHandle(h)
                return True
        except Exception:
            pass
        return False

    def _is_live_book(pid: int, namespace: str) -> bool:
        """True ONLY if `pid` is a live run_book.py process for THIS namespace. Precise so an OS-recycled
        PID (the dead lock-holder's PID reused by an unrelated process) does NOT cause a false
        single-instance refusal that blocks a legitimate restart (the exact failure that took a book down
        on the 2026-06-15 coordinated restart). Fails SAFE: if the process is dead -> False (allow
        restart); if it cannot be inspected -> the conservative loose liveness check (refuse if alive)."""
        try:
            import psutil
            cl = " ".join(psutil.Process(int(pid)).cmdline())
            return ("run_book.py" in cl) and (namespace in cl)
        except Exception as _e:
            try:
                import psutil
                if isinstance(_e, psutil.NoSuchProcess):
                    return False   # dead -> not a live book -> allow restart
            except Exception:
                pass
            return _pid_alive(int(pid))   # unreadable -> conservative: refuse only if the PID is alive

    # ATOMIC single-instance guard (double-start-toctou): the pid-file check-then-write below is NOT
    # atomic -- two simultaneous starts could both pass the .exists() check and both write their pid,
    # double-booking the real-money account. A named kernel mutex is atomic at the OS level (the 2nd
    # CreateMutexW returns ERROR_ALREADY_EXISTS) AND auto-frees when the holder process dies (no stale
    # lock the pid-file otherwise needs cmdline inspection to clear). Held for the whole process lifetime.
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p)
            kernel32.CreateMutexW.restype = ctypes.c_void_p
            kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
            kernel32.CloseHandle.restype = ctypes.c_bool
            _mx_name = f"Local\\GTOS_W7_run_book_{args.namespace}"
            _mx_handle = kernel32.CreateMutexW(None, True, _mx_name)
            _mx_last_error = ctypes.get_last_error()
            if _mx_handle and _mx_last_error == 183:   # ERROR_ALREADY_EXISTS
                kernel32.CloseHandle(_mx_handle)
                logging.error("Another run_book for namespace %s already holds the single-instance mutex "
                              "-- refusing to start (atomic guard).", args.namespace)
                return 4
            if not _mx_handle:
                raise ctypes.WinError(_mx_last_error)
            # keep the handle alive for the process lifetime (a module global so it is never GC'd/closed).
            globals()["_RUN_BOOK_SINGLE_INSTANCE_MUTEX"] = _mx_handle
        except Exception as _mx_e:   # noqa: BLE001 -- never let the guard's own failure block a start
            logging.warning("named-mutex single-instance guard unavailable (%r); relying on the pid-file "
                            "guard only", _mx_e)
        try:
            import msvcrt
            _lock_dir = Path("pipeline_state/ultimate_book") / args.namespace
            _lock_dir.mkdir(parents=True, exist_ok=True)
            _file_lock = open(_lock_dir / "run_book.lock", "a+b")
            try:
                msvcrt.locking(_file_lock.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                logging.error("Another run_book for namespace %s already holds the file lock "
                              "-- refusing to start (cross-process guard).", args.namespace)
                _file_lock.close()
                return 4
            globals()["_RUN_BOOK_SINGLE_INSTANCE_FILE_LOCK"] = _file_lock
        except Exception as _fl_e:   # noqa: BLE001 -- keep the historical pid guard as final fallback
            logging.warning("file-lock single-instance guard unavailable (%r); relying on the pid-file "
                            "guard only", _fl_e)

    _lock = Path("pipeline_state/ultimate_book") / args.namespace / "run_book.pid"
    _lock.parent.mkdir(parents=True, exist_ok=True)
    if _lock.exists():
        try:
            _old = int((_lock.read_text() or "0").strip() or "0")
        except Exception:
            _old = 0
        if _old and _old != os.getpid() and _is_live_book(_old, args.namespace):
            logging.error("Another run_book for namespace %s is already running (pid %s) — refusing "
                          "to start (single-instance guard).", args.namespace, _old)
            return 4
    _lock.write_text(str(os.getpid()))

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    merged = apply_profile_overrides(cfg, args.profile)
    runtime_cfg = merged.setdefault("runtime", {})
    if isinstance(runtime_cfg, dict):
        runtime_cfg["broker_account_namespace"] = args.namespace
        runtime_cfg["profile_namespace"] = args.namespace
    vnext_runtime_cfg = merged.setdefault("gtos_vnext_runtime", {})
    if isinstance(vnext_runtime_cfg, dict):
        vnext_runtime_cfg["runtime_namespace"] = args.namespace
        vnext_runtime_cfg["broker_account_namespace"] = args.namespace
    merged["broker_account_namespace"] = args.namespace

    tags = tuple(t.strip() for t in args.tags.split(",") if t.strip()) if args.tags else None
    # Validate and latch the external sizing carrier before opening an MT5 connection.
    from src.components.ultimate_book.lane_weights import (
        LaneWeightController,
        LaneWeightsConfigurationError,
    )
    try:
        lane_weight_controller = LaneWeightController(
            namespace=args.namespace,
            expected_sleeves=tags or (),
            repo_root=".",
            weights_path=args.lane_weights,
            key_path=args.lane_weights_key,
        )
    except LaneWeightsConfigurationError as exc:
        logging.error("lane-weight launch arguments refused: %s", exc)
        return 4
    lane_weight_snapshot = lane_weight_controller.snapshot()
    if lane_weight_snapshot.get("status") != "active" and lane_weight_controller.enabled:
        logging.error(
            "LANE WEIGHTS NOT ACTIVE: status=%s reason=%s; every --tags sleeve is x1.00",
            lane_weight_snapshot.get("status"),
            lane_weight_snapshot.get("reason"),
        )

    # notification queue (best-effort; reuse the existing Telegram stack — creds from .env). The $/R
    # nominal is configured AFTER mt5.connect() below, so it can use the LIVE balance + active book profile.
    try:
        from src.utils import notification_queue as _nq
        _nq.configure_from_config(merged)
    except Exception:
        logging.getLogger(__name__).warning("notification queue configure failed (non-fatal)", exc_info=True)

    terminal = (args.terminal_path or os.environ.get("GTOS_MT5_TERMINAL_PATH")
                or (merged.get("mt5", {}) or {}).get("terminal_path"))
    mt5 = RealMT5(terminal_path=terminal, portable=True)
    if not mt5.connect():
        logging.error("MT5 connect failed (terminal=%s) — aborting launcher.", terminal)
        try:
            from src.notifications import notify_critical
            notify_critical(f"W7 BOOK: MT5 connect FAILED (terminal={terminal}) — launcher aborting.")
        except Exception:
            pass
        return 2
    if not mt5.is_connected():
        logging.error("MT5 not connected after connect() — aborting.")
        return 2

    # ACCOUNT IDENTITY REQUIRED (fail-closed): a terminal PATH + --namespace does NOT prove WHICH real
    # account the terminal is logged into. If C:\MT5\FTMO is (re)logged into a different login, the
    # FTMO-namespaced book would trade the WRONG real-money account with FTMO's risk profile + ledger.
    # Verify the connected login/server/company/currency/terminal-paths against the profile's
    # broker_profile.expected_account contract (login is compared as a salted-free SHA-256 — no raw login
    # or credential in code/config). ANY mismatch or inability to verify -> refuse to start. A profile with
    # NO contract (legacy/non-live) keeps the documented default-off behavior but is flagged loudly.
    try:
        _idchk = assert_mt5_account_matches_profile(mt5, merged)
    except RuntimeError as _ide:
        logging.error("ACCOUNT IDENTITY check FAILED (namespace=%s): %s — refusing to start.",
                      args.namespace, _ide)
        try:
            from src.notifications import notify_critical
            notify_critical(f"W7 BOOK [{args.namespace}]: ACCOUNT IDENTITY mismatch/unverifiable — "
                            f"REFUSING to start: {_ide}")
        except Exception:
            pass
        return 5
    # ACTIVATION CONTEXT. The token at the order_send choke point may bind a
    # namespace and a config digest; a binding this process cannot answer is a
    # DENIAL, not a pass. So declare both here, after identity is proven and
    # before the first cycle. Nothing is enabled by this call — it only lets a
    # token that names this namespace/config recognise this process.
    try:
        _cfg_digest = config_digest_for(args.config, args.profile)
        mt5.set_activation_context(namespace=args.namespace, config_digest_sha256=_cfg_digest)
        logging.info("activation context declared (namespace=%s, config_digest=%s, token_dir=%s)",
                     args.namespace, (_cfg_digest or "unavailable")[:12], token_dir())
    except Exception:
        logging.exception("activation context could not be declared — exposure-increasing orders "
                          "will be refused until this is fixed.")

    if _idchk.get("checked"):
        logging.info("account identity verified (namespace=%s): fields=%s",
                     args.namespace, _idchk.get("fields_checked"))
    else:
        logging.warning("account identity NOT verified (namespace=%s): profile %s has no "
                        "broker_profile.expected_account contract — proceeding (default-off). A LIVE book "
                        "should carry this contract.", args.namespace, args.profile)
        try:
            from src.notifications import notify_alert
            notify_alert(f"W7 BOOK [{args.namespace}]: no expected_account contract in profile "
                         f"{args.profile} — account identity UNVERIFIED.")
        except Exception:
            pass

    # HEDGING ACCOUNT REQUIRED (fail-closed): the book runs per-(symbol, sleeve) — multiple concurrent
    # positions on one symbol from different sleeves (XAUUSD across 3 metals sleeves, GBPJPY/USDJPY across
    # 2 JPY sleeves). On a NETTING MT5 account the broker collapses same-symbol orders into ONE net
    # position, so per-sleeve adoption/lifecycle breaks and opposite-direction sleeves partially close each
    # other (orphaning tickets + realizing unintended exits). Refuse to start on a non-hedging account.
    try:
        _margin_mode = str(mt5.get_margin_mode()).lower()
    except Exception:
        _margin_mode = "unknown"
    if _margin_mode != "hedging":
        logging.error("Account margin mode is %r, NOT 'hedging' — the per-(symbol,sleeve) book is unsafe "
                      "on a netting account. Refusing to start (namespace=%s).", _margin_mode, args.namespace)
        try:
            from src.notifications import notify_critical
            notify_critical(f"W7 BOOK [{args.namespace}]: account margin mode is {_margin_mode}, NOT "
                            f"hedging — REFUSING to start (per-sleeve multi-position requires hedging).")
        except Exception:
            pass
        return 3

    # $/R notifier nominal: reflect the ACTIVE book allocation profile (e.g. clean3_w7_measured_nom1p25
    # = 1.25%), NOT the legacy per-symbol risk.risk_per_trade_pct (2.0%) the book does not size with, and
    # use the LIVE broker balance. Otherwise the engine close-card "Projected P&L" / daily $ figures
    # overstate by ~1.6x. (The owner-facing book cards already use real per-trade risk; this fixes the
    # engine-level projection path.)
    try:
        from src.notifications import configure_notifications
        from src.components.ultimate_book.admission import ALLOCATION_PROFILES
        rt_n = merged.get("gtos_vnext_runtime", merged)
        prof = ALLOCATION_PROFILES.get(rt_n.get("ultimate_book_profile"))
        nominal_pct = (float(prof.risk_per_unit_A) * 100.0) if prof is not None \
            else float(((merged.get("risk") or {}).get("risk_per_trade_pct")) or 2.0)
        bal = 100_000.0
        try:
            _b = mt5.get_account_balance()
            if isinstance(_b, (int, float)) and _b > 0:
                bal = float(_b)
        except Exception:
            pass
        configure_notifications(nominal_pct, account_balance=bal)
        # NOTE: %-style logging does NOT support the ',' thousands separator (that is f-string/str.format
        # only); use a plain %.0f to avoid a ValueError in the logging filter.
        logging.info("notifier $/R nominal: %.2f%% of $%.0f (profile=%s)",
                     nominal_pct, bal, rt_n.get("ultimate_book_profile"))
    except Exception:
        logging.getLogger(__name__).warning("notification $/R configure failed (non-fatal)", exc_info=True)

    # Validated at LAUNCH, before any engine exists: an unparseable selection must stop the
    # worker, not degrade to the committed contract at every tick in silence.
    # `parse_frontier_exits` raises on an empty string and on an unknown sleeve name
    # (Session AU, B1550). Exit 4 is this file's existing "refusing to start" code.
    from src.components.ultimate_book.execution_packets import (
        FRONTIER_EXIT_OVERRIDES, FrontierExitSelectionError, describe_frontier_contract,
        parse_frontier_exits,
    )
    try:
        frontier_exits = parse_frontier_exits(args.frontier_exits)
    except FrontierExitSelectionError as exc:
        logging.error("--frontier-exits refused: %s", exc)
        return 4
    # Same doctrine, same wave (Session AY, B1810): a floor the operator believes is running
    # and is not is worse than no floor, so an unparseable or unknown selection stops the
    # worker HERE rather than degrading silently at every tick.
    from src.components.ultimate_book.spread_geometry import (
        SpreadGeometryFloorError, parse_spread_geometry_floor,
    )
    # EVERY registered generator, not just `BUILT`. `BUILT` is the 11 core sleeves; the
    # candidate book adds 9 and market expansion 12, and AY-1's largest measured repair
    # (`asia_pdl_fade`, -0.902 -> +0.095 R/day at mid) is in CANDIDATE_BUILT. Validating
    # against `BUILT` alone would refuse the flag's best use as a typo.
    from src.components.ultimate_book.sleeves.registry import (
        BUILT as _BUILT_SLEEVES, CANDIDATE_BUILT as _CAND_SLEEVES,
        MARKET_EXPANSION_BUILT as _MX_SLEEVES,
    )
    _known_sleeves = set(_BUILT_SLEEVES) | set(_CAND_SLEEVES) | set(_MX_SLEEVES)
    try:
        spread_geometry_floor = parse_spread_geometry_floor(
            args.spread_geometry_floor, known_sleeves=_known_sleeves)
    except SpreadGeometryFloorError as exc:
        logging.error("--spread-geometry-floor refused: %s", exc)
        return 4
    owner = UltimateBookOwner(merged, mt5, ".", namespace=args.namespace,
                              frontier_exits=frontier_exits,
                              spread_geometry_floor=spread_geometry_floor,
                              lane_weight_controller=lane_weight_controller)
    for _s in frontier_exits:
        # B1852: this banner used to render `float(_o["final_target_r"])`, which SIX of the eight
        # wired sleeves do not carry -- so naming one of them killed the worker AFTER
        # `parse_frontier_exits` had accepted it. `describe_frontier_contract` renders whichever
        # contract keys the override actually has.
        logging.warning("FRONTIER EXIT CONTRACT IS ON for %s: %s (%s). This changes WHERE or WHEN "
                        "this book exits that sleeve; positions already open are managed from "
                        "their own trade record, but one adopted WITHOUT a record is rehydrated at "
                        "this contract.", _s, FRONTIER_EXIT_OVERRIDES[_s]["frontier_cell"],
                        describe_frontier_contract(_s))
    if spread_geometry_floor:
        _rt_cfg = merged.get("gtos_vnext_runtime", merged)
        from src.components.ultimate_book.spread_geometry import resolve_floor_limit
        for _s in sorted(spread_geometry_floor):
            _lim = resolve_floor_limit(_rt_cfg, _s, spread_geometry_floor)
            logging.warning("SPREAD-GEOMETRY FLOOR IS ON for %s at spread_r <= %.4f (%s). "
                            "Intents whose live spread exceeds that fraction of their own stop "
                            "are refused AT GENERATION, so they never enter the day's running "
                            "conviction count. This changes WHICH TRADES this book proposes.",
                            _s, _lim,
                            "explicit" if spread_geometry_floor[_s] is not None
                            else "inherited from the send gate's own limit")
    broker_symbol = build_broker_symbol_resolver(merged)
    launcher = BookLauncher(owner, mt5, broker_symbol, repo_root=".", tags=tags,
                            poll_seconds=args.poll_seconds, kill_flag=args.kill_flag)

    rt = merged.get("gtos_vnext_runtime", merged)
    gated_on = (
        config_bool_value(rt.get("ultimate_book_enabled", False), False)
        and config_bool_value(rt.get("ultimate_book_apply_to_execution", False), False)
        and config_bool_value(rt.get("ultimate_book_live_activation_allowed", False), False)
        and config_bool_value(rt.get("ultimate_book_live_broker_authority", False), False)
    )
    logging.info("book launcher: profile=%s namespace=%s authority_gates_ON=%s halted=%s killed=%s",
                 args.profile, args.namespace, gated_on, launcher.halted(), launcher.killed())

    try:
        if args.once:
            rec = launcher.tick()
            logging.info("single tick: %s", rec)
        else:
            launcher.run_forever()
    finally:
        try:
            mt5.disconnect()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

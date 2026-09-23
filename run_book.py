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


# Live profile, terminal, and derisk authority come from explicit CLI arguments plus
# the profile/config files bound by the activation token.  These environment variables
# sit outside that digest and historically leaked from a host-global/.env setting into
# a different account worker.  Strip them before importing runtime modules; values are
# never printed because the variables may contain host-specific paths.
# Ported 2026-09-08 from main ai-trading-agent run_book.py (GTOS_PROFILE landmine fix).
_UNDIGESTED_BEHAVIOR_ENV = (
    "GTOS_PROFILE",
    "GTOS_MT5_TERMINAL_PATH",
    "GTOS_UB_DERISK_MODE",
)
_discarded_behavior_env = [name for name in _UNDIGESTED_BEHAVIOR_ENV if os.environ.get(name)]
for _name in _UNDIGESTED_BEHAVIOR_ENV:
    os.environ.pop(_name, None)
if _discarded_behavior_env:
    print(
        "IGNORING undigested live-behavior environment overrides: "
        + ", ".join(_discarded_behavior_env)
        + "; using CLI/profile/config authority.",
        file=sys.stderr,
        flush=True,
    )

from src.security import install_runtime_monitoring
install_runtime_monitoring()

from src.utils.config import apply_profile_overrides
from src.utils.broker_profile import assert_mt5_account_matches_profile
from src.mt5.mt5_real import RealMT5
from src.mt5.mt5_interface import comment_prefix_for_namespace, magic_for_namespace
from src.safety.activation_token import (
    config_digest_for,
    normalized_f5_launch_contract,
    token_dir,
)
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


def _challenge_writer(namespace: object) -> bool:
    return str(namespace or "").strip() == "operator"


def _apply_challenge_launcher(launcher) -> None:
    """Write the score onto the cap and the clocks. An empty answer writes nothing."""

    from src.components.ultimate_book import minimal_size as clocks
    from src.components.ultimate_book.launcher_facts import clock_from_minutes, launcher_return

    cap = launcher_return("transient_retry_cap")
    owner = getattr(launcher, "owner", None)
    if owner is not None and cap is not None and not isinstance(cap, bool) and cap >= 0:
        try:
            owner._transient_retry_cap = int(cap)
        except (TypeError, ValueError):
            pass
    friday = clock_from_minutes(launcher_return("friday_cutoff_minute"))
    if friday is not None:
        clocks.F5_WEEKEND_NEW_RISK_CUTOFF_UTC_HHMM = friday
        clocks.F5_FRIDAY_NEW_RISK_CUTOFF_UTC = friday
    weekend = clock_from_minutes(launcher_return("weekend_flat_minute"))
    if weekend is not None:
        clocks.F5_WEEKEND_FLAT_UTC_HHMM = weekend


def run_loop(launcher, max_ticks=None) -> None:
    """Wait, then run one cycle.

    The poll flag stays a fact. A returned cycle_wait is the wait. Until that
    score has returned, the cycle starts at the next print of the fastest bar
    this book watches. An empty answer does not sleep a planted number.
    """

    import time

    from src.components.ultimate_book.launcher_facts import next_cycle_wait

    n = 0
    while max_ticks is None or n < max_ticks:
        wait = next_cycle_wait(launcher)
        _apply_challenge_launcher(launcher)
        if wait is not None:
            try:
                launcher.poll_seconds = wait
            except Exception:
                pass
            logging.info("cycle_wait seconds=%s", wait)
            if wait > 0:
                time.sleep(wait)
        else:
            logging.info("cycle_wait unset")
        launcher.tick()
        n += 1
        if max_ticks is not None and n >= max_ticks:
            break


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
                   help="Path to a signed gtos.lane_weights.v1 sleeve-weight file. Requires "
                        "--lane-weights-key and an explicit --tags scope. Missing, stale, invalid, "
                        "or badly signed input becomes x1.00 for the entire scope.")
    p.add_argument("--lane-weights-key", default=None,
                   help="Path to the external HMAC key that verifies --lane-weights. The key is "
                        "never read from config/profile bytes and must be private on POSIX.")
    p.add_argument("--kill-flag", default=None,
                   help="Per-instance operator kill-switch path (default pipeline_state/ULTIMATE_BOOK_KILL.flag). "
                        "Set a distinct path per account so FTMO and redacted_account can be braked independently.")
    p.add_argument("--once", action="store_true", help="Run a single tick and exit (wiring check)")
    p.add_argument(
        "--event-clock-shadow",
        action="store_true",
        help=(
            "Record Q2 exact-H4 event-close classifications in launcher telemetry. "
            "DEFAULT OFF and observation-only: does not admit, reject, size, place, "
            "modify, or close any order. Uses decision_bar_iso as bar OPEN, adds the "
            "timeframe, resolves the measured broker clock, and latches across retries."
        ),
    )
    p.add_argument("--recover-pre-gap-bar", action="store_true",
                   help="Keep the last closed bar before a session gap as the decision bar. "
                        "bar_provider drops it unconditionally as 'forming', so the last bar "
                        "before every weekend and holiday is unreachable: measured at 1.3-6.8 %% "
                        "of five H4 sleeves' trades (Session AB) and 4.26 %% of 134,027 D1 "
                        "trades (Session AF, because every Friday is a pre-gap bar). "
                        "CHANGES WHICH BARS AN ARMED BOOK TRADES -- owner decision, and the "
                        "unreachable population is currently the WORSE one at D1 "
                        "(-0.0771 R against +0.0117 R). Off by default. Set here rather than "
                        "in agent_config.yaml because that file's bytes are hashed into the "
                        "activation token's config digest.")
    p.add_argument("--vol-level-tilt", action="store_true",
                   help="Arm the WAVE-11 vol-LEVEL sizing tilt on sub_xvol_pullback: "
                        "clamp(vr/2.0, 0.80, 1.20) applied to each intent's size, where vr is "
                        "the decision bar's ATR(14) over its own 100-bar mean. Session AO "
                        "measured vr MONOTONE in this sleeve's net R inside its own firing range "
                        "(Spearman +0.4073, permutation p 0.00025, tertile net R/trade "
                        "0.512 -> 1.111 -> 2.124). The centre 2.0 is Session AB's PUBLISHED xhi "
                        "band value (regime_spine/dials.py:143), which no bucketiser implements, "
                        "so it is not a cut fitted to an outcome. NET DE-RISK: the mean "
                        "multiplier over the 88 archive trades is 0.925 -- `vol=xhi` starts at "
                        "1.6, so most of the range sits below the unit point and the size-up is "
                        "reserved for the most expanded fifth of the bars. CHANGES THE SIZE AN "
                        "ARMED BOOK RISKS on one of the three armed sleeves -- owner decision. "
                        "Off by default. Set here rather than in agent_config.yaml or "
                        "profiles/redacted_account.yaml because BOTH are hashed into a live activation "
                        "token's config digest.")
    p.add_argument("--frontier-exits", default=None,
                   help="Comma-separated sleeves to run on their WAVE-12 frontier exit contract "
                        "instead of the committed one (Session AU). Wired: "
                        "mx_btcusd_d1_donchian_20_breakout -> target_5R (broker TP 5R instead of the "
                        "generator's 2R) -- the exit the estate's ONE standing admission is measured "
                        "at (p 0.0011, admits at two of three cost bands on the ratified RECORDED "
                        "population); and sub_xvol_pullback -> target_4R (4R instead of 3R), AK's "
                        "frontier winner at +1.157 R/day. THE TWO ARE IN OPPOSITE LIVE STATES and "
                        "that is why this is a list and not a switch: mx_btcusd is in neither "
                        "account's --tags, so wiring its contract changes nothing an armed book does; "
                        "sub_xvol_pullback IS ARMED ON BOTH ACCOUNTS at 3R, so wiring its contract "
                        "CHANGES THE EXIT OF LIVE POSITIONS -- owner decision. Empty by default. An "
                        "empty string is REFUSED rather than read as 'all' (the --tags fail-open), "
                        "and an unknown sleeve name is REFUSED rather than dropped. FLIP AT A FLAT "
                        "BOOK: a position adopted with no trade record is rehydrated from the sleeve "
                        "identity, so a pre-flip position's broker TP would move. Set here rather "
                        "than in agent_config.yaml or profiles/redacted_account.yaml because BOTH are "
                        "hashed into a live activation token's config digest.")
    p.add_argument(
        "--risk-unit-floor-mode", choices=("off", "shadow", "apply"), default="off",
        help="Q1 adaptive minimum-risk-unit mode. off (default) performs no extra reads; "
             "shadow computes decision-cutoff and broker-grid observations but cannot mutate "
             "an intent; apply may widen only after the existing generation, admission and "
             "pre-send spread refusals. No supervisor selects apply by default.")
    p.add_argument(
        "--risk-unit-floor", default=None,
        help="Effective --tags sleeves for Q1, optionally with finite per-sleeve options "
             "(crypto,energy_agri:bar=1.5:cost=8:cap=4:target=weld). Defaults: bar=1, "
             "cost=5, uncapped, target=preserve. preserve keeps literal/POC price targets; "
             "weld must be explicit. The selection is refused unless mode is shadow/apply "
             "and every sleeve is in this worker's effective --tags surface.")
    p.add_argument("--spread-geometry-floor", default=None,
                   help="Comma-separated sleeves to run the WAVE-13 generation-side "
                        "spread-geometry floor on, optionally with a per-sleeve spread_r "
                        "limit (`sub_mid_dn_revert,asia_pdl_fade:0.075`). A sleeve named "
                        "without a limit uses THE ONE THE SEND GATE WILL APPLY TO IT "
                        "(selected_cell_pretrade_max_spread_r[_by_sleeve]), so the two "
                        "layers agree by construction. WHAT IT ADDS, given the send gate "
                        "already refuses these trades twice: an intent refused at "
                        "GENERATION never reaches the day's running conviction count, "
                        "which admission.py:1188 carries MONOTONE UPWARD -- measured on the "
                        "2026-07-25 export at 16 account-days contaminated, 3 of them "
                        "moving the Kelly-lite multiplier, worst +25.2%% on every unit that "
                        "day. Session AY measured the economics per sleeve at the ratified "
                        "rule: REPAIR on sub_mid_dn_revert (+0.426 R/day at mid, p 0.163 -> "
                        "0.023, beats all 20 random controls, inverse negative) and "
                        "sub_xvol_pullback (+0.264, p 0.012 -> 0.0020), NEUTRAL on crypto "
                        "and energy_agri, NO-OP on seven sleeves. CHANGES WHICH TRADES AN "
                        "ARMED BOOK PROPOSES -- owner decision. Empty by default. An empty "
                        "string is REFUSED rather than read as 'all' (the --tags fail-open) "
                        "and an unknown sleeve name is REFUSED rather than dropped. Set "
                        "here rather than in agent_config.yaml or profiles/redacted_account.yaml "
                        "because BOTH are hashed into a live activation token's config "
                        "digest.")
    p.add_argument("--f5-minimal-size-usd", type=float, default=None,
                   help="MINIMAL-SIZE EXPERIMENT (F5). Run EVERY decision at the NOMINAL dial "
                        "and place at this fixed dollar risk per trade. ABSENT = OFF, and every "
                        "seam is inert (the default path is unchanged). The scalar is applied at "
                        "the LAST step before the broker request, after the pre-trade cost model "
                        "and Execution Manager V4 have both seen the nominal risk_pct, so the "
                        "allocator never sees $1 candidates and never accepts thousands of them. "
                        "The governor's equity, day-start balance and gross OPEN RISK all read a "
                        "NOTIONAL ledger instead of the broker, because at 1/200th lots the 4%% "
                        "gross cap reads ~0.0002 and would never bind -- that hunk is what makes "
                        "this the same system at a smaller size rather than a different one. "
                        "Sub-minimum lots round UP to volume_min and record the inflation "
                        "instead of being shed, so the sample keeps BTCUSD/XAGUSD/XAUUSD/ETHUSD "
                        "and the 10x-contract indices. There is deliberately NO loss budget "
                        "(owner decision, 2026-08-12): the firm's limits, the governor, the "
                        "kill flag and the activation token are untouched and none is bypassed. "
                        "The worker takes its OWN broker identity (magic 0, comment "
                        "prefix 'F5:') so the ARMED book on the same account cannot see its "
                        "positions -- see tests/safety/test_f5_isolation.py. Set here rather "
                        "than in agent_config.yaml because that file is R2-bound AND inside "
                        "both live activation-token digests.")
    p.add_argument("--f5-notional-initial-usd", type=float, default=100000.0,
                   help="Starting equity of the NOTIONAL ledger the F5 governor reads. Only "
                        "meaningful with --f5-minimal-size-usd.")
    p.add_argument("--f5-friday-new-risk-cutoff-utc", default=None,
                   help="F5-ONLY Friday new-risk cutoff as HH:MM UTC. The string is a fact "
                        "on the ask. Challenge does not write it onto the clock. An empty "
                        "score leaves the clock unset. Does not flatten. Does not enter "
                        "the activation-token launch-contract digest (q1/q2/size/tags only). "
                        "Set here rather than in agent_config.yaml because that file is "
                        "R2-bound AND inside both live activation-token digests.")
    p.add_argument("--f5-weekend-flat-utc", default=None,
                   help="F5-ONLY weekend flatten clock as HH:MM UTC Friday. The string is a "
                        "fact on the ask. Challenge does not write it onto the clock. An empty "
                        "score leaves the clock unset. Does not enter the activation-token "
                        "launch-contract digest. Crypto stays exempt via F5_ALWAYS_OPEN_SYMBOLS. "
                        "Set here rather than in agent_config.yaml.")
    p.add_argument("--frozen-intent-reprice", action="store_true", default=False,
                   help="F5-ONLY FrozenPriceIntent V1. Default OFF. On a *_f5_minimal worker, "
                        "a QUOTE_DEPENDENT pre-send cost skip enqueues a frozen entry/stop/"
                        "target/max-lots object and leaves the decision bar live instead of "
                        "consuming it. Production books ignore the flag. Does not re-anchor "
                        "SL/TP, has no fill-count cap, and is inert unless this worker is F5. "
                        "See docs/audits/intent-20260816/FROZEN_PRICE_INTENT_V1.md.")
    p.add_argument("--judgment-rescue", action="store_true", default=False,
                   help="F5-ONLY judgment consume seam. Default OFF. With --frozen-intent-reprice "
                        "on the operator worker, a TERMINAL cost refusal that would drop a "
                        "FrozenPriceIntent consults judgment/verdicts_<day>.json first (one lookup: "
                        "RESCUE|VETO|ABSENT; TTL 600s; fail-to-absent). RESCUE keeps the intent on "
                        "the EXISTING rail — price re-check, TTL and chase kill-band all stay live "
                        "and judgment never calls place(). VETO is logged, not consumed. Stale / "
                        "missing / unreadable / wrong-book verdicts = ABSENT = code-only behavior; "
                        "the book never blocks on this layer. Set here rather than in "
                        "agent_config.yaml because that file is R2-bound AND inside both live "
                        "activation-token digests. See docs/audits/fable-20260816/JUDGMENT-LOCK.md.")
    # DEPLOY-NOTE (F5 ceremony 2026-08-18 ~06:00 +07). Flag-absent = byte-identical.
    # Ceremony N = 3: a real glitch clears in 1–2 polls (survives); the UK100
    # 2026-08-17 idxrev storm was 10 sends / one M15 bar — dies on send 4.
    # Carry as argv only (R2-bound agent_config.yaml must not move). Production
    # books (ftmo_server3 / redacted_account_live) do not get this flag tonight.
    p.add_argument("--transient-retry-cap", type=int, default=0,
                   help="Bound the transient place-retry loop. Default 0 == OFF == today's "
                        "behavior byte-for-byte (unbounded retry until a fill, a terminal "
                        "reason, or the 0.5x-bar lateness gate). N>0: placement failures are "
                        "counted per (sleeve, symbol, decision_bar, transient reason CLASS); "
                        "attempts 1..N retry exactly as today, and the (N+1)th same-class "
                        "failure is TERMINAL for that bar — one transient_retry_cap_reached "
                        "summary row (attempt count + first/last attempt times), one deduped "
                        "notify, bar consumed. Total order_sends per doomed leg == N+1. "
                        "Risk-reducing requests (closes/cancels/tightenings) never pass "
                        "through the placement branch and can never be capped. Counters are "
                        "in-memory: a restart resets them (the bar is re-run at most once "
                        "more), and every new decision bar starts at zero. Built for the "
                        "2026-08-17 UK100 idxrev storm (35+ identical order_rejected:"
                        "timeout_no_fill sends in 37 min — an activation-token refusal wearing "
                        "a transient label) and FN 2026-08-04 (~232 sends/2 h). Set here "
                        "rather than in agent_config.yaml because that file is R2-bound AND "
                        "inside both live activation-token digests.")
    p.add_argument("--entry-hour", default=None,
                   help="Comma-separated sleeves that must enter at a BROKER HOUR later than "
                        "their decision bar's close, optionally with the hour "
                        "(`sub_mid_dn_revert` or `sub_mid_dn_revert:1`; default 1, the "
                        "RATIFIED convention of phase9/OWNER_DECISION_ENTRY_HOUR.md). The "
                        "intent is DEFERRED at generation and re-proposed every tick until "
                        "the broker clock reaches the target -- not moved to a different "
                        "decision timeframe, because no bar closes at 01:00 on the matched "
                        "feed above M15. Per-sleeve because the rollover premium is a property "
                        "of the SYMBOL, not the timeframe: BTCUSD's median M15 spread is "
                        "identical at every broker hour (x1.000, it quotes 24/7) so "
                        "`mx_btcusd_d1_donchian_20_breakout` -- 318 of 318 fills at hour 00 -- "
                        "would pay -0.019 R/trade for nothing, while `sub_mid_dn_revert` puts "
                        "147 of its 533 trades on JPY crosses at hour 00 where the premium is "
                        "x8.0 to x19.9. FAIL-OPEN: an unresolvable broker clock emits the "
                        "intent unchanged (today's behaviour) and counts it in "
                        "`generation.entry_hour.fail_open` -- the opposite of the spread floor, "
                        "because a missed improvement is not a breach. Empty by default. An "
                        "empty string is REFUSED rather than read as 'all', an unknown sleeve "
                        "is REFUSED rather than dropped, hour 0 is REFUSED as a no-op spelled "
                        "as a change, and a target whose deferral would reach the "
                        "entry-lateness window for that sleeve's timeframe (2 h on H4, 12 h on "
                        "D1) is REFUSED because `_entry_too_late` would silently SHADOW the "
                        "entry.")
    p.add_argument("--weekend-flat", default=None,
                   help="Comma-separated sleeves that must be FLAT over the weekend (Session BA). "
                        "This is the redacted_account FUNDED-ACCOUNT rule -- FIRM_RULES_V1.json says "
                        "weekend holding is allowed in the Challenge and PROHIBITED once funded -- "
                        "so it binds the moment that account PASSES and binds on FTMO NEVER (FTMO's "
                        "captured rules carry no weekend clause at all). A governed position is "
                        "closed at market once broker-local Saturday 00:00 minus "
                        "--weekend-flatten-before-hours is reached, and a governed intent is refused "
                        "inside that same window. Empty by default. THE BILL IS PER SLEEVE AND SPANS "
                        "AN ORDER OF MAGNITUDE, which is why this is a list and not a switch -- see "
                        "phase13/BA_WEEKEND_POLICY_OWNER_PACKAGE.md for the number per sleeve at the "
                        "ratified rule. CHANGES WHEN LIVE POSITIONS CLOSE and refuses entries an "
                        "armed book would otherwise take -- owner decision. An empty string is "
                        "REFUSED rather than read as 'all' (the --tags fail-open) and an unknown "
                        "sleeve name is REFUSED rather than dropped. The worker REFUSES TO START if "
                        "the policy is armed and the broker clock or server name cannot be resolved: "
                        "src/utils/broker_clock.py was ABSENT from the live host at the 2026-07-26 "
                        "export, and a compliance guard that degrades to 'no weekend is due' is a "
                        "funded account holding through one while every log reads healthy. Set here "
                        "rather than in agent_config.yaml or profiles/redacted_account.yaml because BOTH "
                        "are hashed into a live activation token's config digest.")
    p.add_argument("--weekend-flatten-before-hours", type=float, default=None,
                   help="Hours before broker-local Saturday 00:00 at which --weekend-flat closes a "
                        "governed position. Default 4.0 == one H4 bar, which puts the close at the "
                        "close of the last H4 bar of the week -- the same instant Session BA's "
                        "headline research cell `m0` exits at, which is what makes the published "
                        "cost the cost of THIS setting. Smaller captures more of the week and fills "
                        "into its thinnest liquidity; larger is the margin dial and its cost is "
                        "measured per sleeve in BA_WEEKEND_V1.json -> flat.")
    p.add_argument("--weekend-entry-embargo-hours", type=float, default=0.0,
                   help="Hours before the same instant inside which a governed sleeve takes NO new "
                        "entry. Default 0 == no embargo beyond the flatten window itself (an entry "
                        "inside the flatten window is always refused, because it would be closed on "
                        "the tick that opened it). An embargo forgoes trades rather than truncating "
                        "them; whether that is worth it is per sleeve and measured "
                        "(BA_WEEKEND_V1.json -> embargo).")
    p.add_argument("--weekend-exempt", default=None,
                   help="Comma-separated subset of --weekend-flat exempted from it because their "
                        "market never closes. Session BA measured that BTCUSD gapped the weekend in "
                        "only 43.8 %% of its weeks and quoted through the other 56.2 %%, so whether "
                        "the firm rule reaches a 24/7 instrument is a real question worth 0.219 "
                        "R/day on the `crypto` sleeve alone. Empty by default: the CONSERVATIVE "
                        "reading (flat by the calendar whatever the instrument does) is the one that "
                        "cannot breach. Exempting a sleeve is an owner decision that needs the firm's "
                        "written answer, not an inference.")
    p.add_argument("--weekend-early-close", default=None,
                   help="Broker-local YYYY-MM-DD dates the market does NOT trade, comma-separated or "
                        "a path to a one-per-line file. A holiday at the END of a week pulls the whole "
                        "flatten deadline back a day, because the last close of a week whose Friday is "
                        "a holiday is that FRIDAY 00:00 broker. MEASURED: 7 of the archive's 271 "
                        "weekend-flat exits (2.6 %%) fall in such a week -- all Christmas or New Year -- "
                        "and without this list the flatten aims at an instant the market has already "
                        "been shut for a day, which under the redacted_account rule is a BREACH and not a "
                        "cost. Empty by default, and the empty case is that measured exposure rather "
                        "than a safe default; the alternative with no list to maintain is "
                        "--weekend-flatten-before-hours 24 (flat by Friday 00:00 broker every week), "
                        "which is automatic and costs an extra 0.117 R/day across the armed four. This "
                        "list is operator-supplied because the repo has NO trading-session calendar: "
                        "broker_net_cost_engine.py:44-45 names symbol_info_session_trade as authority "
                        "it does not have, and src/mt5/mt5_real.py exposes no sessions API. Capturing "
                        "that table is the durable fix and is filed in the repair queue.")
    args = p.parse_args()

    def _parse_f5_hhmm(raw, flag):
        text = str(raw or "").strip()
        parts = text.split(":")
        if len(parts) != 2:
            raise SystemExit(f"{flag} must be HH:MM UTC, got {raw!r}")
        try:
            hh, mm = int(parts[0]), int(parts[1])
        except ValueError as exc:
            raise SystemExit(f"{flag} must be HH:MM UTC, got {raw!r}") from exc
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            raise SystemExit(f"{flag} out of range: {raw!r}")
        return (hh, mm)

    # Challenge clocks are the score. The argv strings stay facts and are not written here.
    if not _challenge_writer(args.namespace) and (
        args.f5_friday_new_risk_cutoff_utc or args.f5_weekend_flat_utc
    ):
        from src.components.ultimate_book import minimal_size as _f5_ms
        if args.f5_friday_new_risk_cutoff_utc:
            hhmm = _parse_f5_hhmm(
                args.f5_friday_new_risk_cutoff_utc, "--f5-friday-new-risk-cutoff-utc"
            )
            _f5_ms.F5_WEEKEND_NEW_RISK_CUTOFF_UTC_HHMM = hhmm
            _f5_ms.F5_FRIDAY_NEW_RISK_CUTOFF_UTC = hhmm
        if args.f5_weekend_flat_utc:
            _f5_ms.F5_WEEKEND_FLAT_UTC_HHMM = _parse_f5_hhmm(
                args.f5_weekend_flat_utc, "--f5-weekend-flat-utc"
            )

    configure_runtime_logging(logging.INFO)

    # Operator notification delivery is default-deny per process (F30 / Q7,
    # src/safety/notification_authorization.py). This is a live book worker: it
    # emits Level.LOW alerts that the queue transports synchronously in-process
    # rather than handing to the drain worker, and falls back to
    # notifications._send_async when the queue subsystem is unavailable. Both
    # paths need this grant, so take it explicitly and on the record.
    from src.safety.notification_authorization import authorize_operator_delivery
    authorize_operator_delivery(
        reason=f"run_book.py live book worker namespace={args.namespace} profile={args.profile}"
    )

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
    # Session CO: validate and day-latch the external sizing carrier BEFORE opening an MT5
    # connection.  The source itself fails to a complete neutral vector; only inconsistent
    # launch arguments (one path without the other, or no explicit scope) refuse startup.
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
    # BROKER-SIDE IDENTITY, resolved ONCE from the namespace and bound to the wrapper (F5,
    # 2026-08-12). `ExecutionEngine` resolves the same value independently from
    # `broker_account_namespace(config)`, which this launcher set to `args.namespace` above --
    # two derivations of one function of one input, so a placing engine and the reader that has
    # to see its positions cannot disagree. The banner prints it because a book whose identity
    # you cannot read in the log is a book you cannot reconcile against the terminal.
    _magic = magic_for_namespace(args.namespace)
    # Build the F5 authorization contract before opening a terminal. In particular, a
    # *_f5_minimal namespace with a missing size flag is an accidental FULL-SIZE worker,
    # not a valid default, and must never reach a broker connection. Non-F5 returns None
    # and keeps the historical config digest and token behavior byte-for-byte unchanged.
    from src.components.ultimate_book.minimal_size import MinimalSizeConfig
    minimal_size_cfg = MinimalSizeConfig(
        enabled=args.f5_minimal_size_usd is not None,
        target_risk_usd=float(args.f5_minimal_size_usd or 0.0),
        notional_initial_usd=float(args.f5_notional_initial_usd),
    )
    try:
        minimal_size_cfg.validate()
        _f5_launch_contract = normalized_f5_launch_contract(
            f5_enabled=minimal_size_cfg.enabled,
            target_risk_usd=minimal_size_cfg.target_risk_usd,
            notional_initial_usd=minimal_size_cfg.notional_initial_usd,
            tags=tags,
            namespace=args.namespace,
            magic=_magic,
            profile=args.profile,
            q1_mode=args.risk_unit_floor_mode,
            q1_selection=args.risk_unit_floor,
            q2_enabled=args.event_clock_shadow,
        )
    except ValueError as exc:
        logging.error("F5 launch contract refused: %s", exc)
        return 6
    _cfg_digest = config_digest_for(
        args.config,
        args.profile,
        launch_contract=_f5_launch_contract,
    )
    mt5 = RealMT5(terminal_path=terminal, portable=True, magic=_magic)
    try:
        mt5.set_activation_context(
            namespace=args.namespace,
            config_digest_sha256=_cfg_digest,
            require_namespace_binding=_f5_launch_contract is not None,
            require_config_digest_binding=_f5_launch_contract is not None,
        )
        logging.info(
            "activation context declared (namespace=%s, config_digest=%s, "
            "f5_launch_contract=%s, token_dir=%s)",
            args.namespace,
            (_cfg_digest or "unavailable")[:12],
            "bound" if _f5_launch_contract is not None else "not_applicable",
            token_dir(),
        )
    except Exception:
        logging.exception(
            "activation context could not be declared — exposure-increasing orders "
            "will be refused until this is fixed."
        )
        if _f5_launch_contract is not None:
            return 6
    logging.info("broker identity: magic=%d comment_prefix=%r (namespace=%s)",
                 _magic, comment_prefix_for_namespace(args.namespace), args.namespace)
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

    # Validated at LAUNCH, before any engine exists: an unparseable selection must stop the worker,
    # not degrade to the committed contract at every tick in silence. `parse_frontier_exits` raises
    # on an empty string and on an unknown sleeve name (Session AU, B1550).
    from src.components.ultimate_book.execution_packets import (
        FrontierExitSelectionError, parse_frontier_exits,
    )
    try:
        frontier_exits = parse_frontier_exits(args.frontier_exits)
    except FrontierExitSelectionError as exc:
        logging.error("--frontier-exits refused: %s", exc)
        return 4
    # Same shape, same reason (Session AY, B1810): a floor the operator believes is running
    # and is not is worse than no floor, so an unparseable or unknown selection stops the
    # worker here rather than degrading silently at every tick.
    from src.components.ultimate_book.spread_geometry import (
        SpreadGeometryFloorError, parse_spread_geometry_floor,
    )
    # EVERY registered generator, not just `BUILT`. `BUILT` is the 11 core sleeves; the
    # candidate book adds 9 and market expansion 12, and AY-1's largest measured repair
    # (`asia_pdl_fade`, -0.902 -> +0.095 R/day at mid) is in CANDIDATE_BUILT. Validating
    # against `BUILT` alone would have refused the flag's best use as a typo.
    from src.components.ultimate_book.sleeves.registry import (
        BUILT as _BUILT_SLEEVES, CANDIDATE_BUILT as _CAND_SLEEVES,
        MARKET_EXPANSION_BUILT as _MX_SLEEVES, WIDEN_BUILT as _WIDEN_SLEEVES,
        DISPLACEMENT_BUILT as _DSP_SLEEVES,
        RESEARCH_DRAFT_BUILT as _RESEARCH_SLEEVES,
    )
    _known_sleeves = (set(_BUILT_SLEEVES) | set(_CAND_SLEEVES) | set(_MX_SLEEVES)
                      | set(_WIDEN_SLEEVES) | set(_DSP_SLEEVES) | set(_RESEARCH_SLEEVES))
    try:
        spread_geometry_floor = parse_spread_geometry_floor(
            args.spread_geometry_floor, known_sleeves=_known_sleeves)
    except SpreadGeometryFloorError as exc:
        logging.error("--spread-geometry-floor refused: %s", exc)
        return 4
    from src.components.ultimate_book.risk_unit_floor import (
        RiskUnitFloorError,
        policy_from_args as risk_unit_floor_policy_from_args,
    )
    _effective_risk_sleeves = None
    if args.risk_unit_floor_mode != "off" or args.risk_unit_floor is not None:
        # An active Q1 selection must be a sleeve this exact worker can evaluate, not merely
        # a name present somewhere in the union registry.  Compose the same tags/include/
        # allowlist/admission intersection generation uses, then require at least one symbol
        # supported by the merged profile.  Keep this branch entirely cold in default-off.
        from src.components.ultimate_book.book_engine import (
            effective_generation_sleeve_names,
        )
        _risk_floor_broker_symbol = build_broker_symbol_resolver(merged)
        _effective_risk_sleeves = (
            effective_generation_sleeve_names(
                merged.get("gtos_vnext_runtime", merged),
                tags,
                _risk_floor_broker_symbol,
            )
            if tags is not None
            else None
        )
    try:
        risk_unit_floor_policy = risk_unit_floor_policy_from_args(
            args.risk_unit_floor_mode,
            args.risk_unit_floor,
            known_sleeves=_known_sleeves,
            effective_sleeves=_effective_risk_sleeves,
        )
    except RiskUnitFloorError as exc:
        logging.error("risk-unit-floor launch policy refused: %s", exc)
        return 4
    # Same doctrine, two waves later (Session CE, B2314). The extra argument here is
    # `timeframe_of`: a target whose deferral would reach `_entry_too_late`'s window is
    # accepted by every other check and then silently SHADOWED at placement, which is a sleeve
    # that stops trading with a healthy log -- so it is a LAUNCH refusal, not a runtime one.
    from src.components.ultimate_book.entry_hour import (
        EntryHourSelectionError, parse_entry_hour,
    )
    try:
        _rt_for_lateness = merged.get("gtos_vnext_runtime", merged)
        entry_hour = parse_entry_hour(
            args.entry_hour, known_sleeves=_known_sleeves,
            timeframe_of={k: v.timeframe for k, v in
                          {**_BUILT_SLEEVES, **_CAND_SLEEVES, **_MX_SLEEVES, **_DSP_SLEEVES}.items()},
            lateness_frac=float(
                _rt_for_lateness.get("ultimate_book_max_entry_lateness_frac", 0.5) or 0.5))
    except EntryHourSelectionError as exc:
        logging.error("--entry-hour refused: %s", exc)
        return 4
    # Same doctrine, one wave later (Session BA, B1900): the weekend policy is parsed and
    # REFUSED at launch. Unlike the frontier selection it also has to be PREFLIGHTED after the
    # owner exists, because its correctness depends on a module and a server name that only the
    # live account can supply -- see `weekend_policy_preflight`.
    from src.components.ultimate_book.weekend_policy import (
        WeekendPolicySelectionError, policy_from_args,
    )
    try:
        weekend_policy = policy_from_args(
            args.weekend_flat,
            flatten_before_hours=args.weekend_flatten_before_hours,
            entry_embargo_hours=args.weekend_entry_embargo_hours,
            exempt=args.weekend_exempt,
            early_close=args.weekend_early_close,
        )
    except WeekendPolicySelectionError as exc:
        logging.error("--weekend-flat refused: %s", exc)
        return 5
    owner = UltimateBookOwner(merged, mt5, ".", namespace=args.namespace,
                              recover_pre_gap_bar=args.recover_pre_gap_bar,
                              vol_level_tilt=args.vol_level_tilt,
                              frontier_exits=frontier_exits,
                              spread_geometry_floor=spread_geometry_floor,
                              weekend_policy=weekend_policy,
                              entry_hour=entry_hour,
                              event_clock_shadow=args.event_clock_shadow,
                              lane_weight_controller=lane_weight_controller,
                              minimal_size=minimal_size_cfg,
                              risk_unit_floor_policy=risk_unit_floor_policy,
                              frozen_intent_reprice=bool(args.frozen_intent_reprice),
                              judgment_rescue=bool(args.judgment_rescue),
                              transient_retry_cap=(
                                  0
                                  if _challenge_writer(args.namespace)
                                  else int(args.transient_retry_cap or 0)
                              ))
    wpf = owner.weekend_policy_preflight()
    if not wpf.get("ok"):
        logging.error("WEEKEND POLICY PREFLIGHT FAILED (%s): %s — refusing to start. A funded "
                      "account under the redacted_account weekend rule must not run with a guard that "
                      "cannot locate the weekend.", wpf.get("status"), wpf.get("error"))
        try:
            from src.notifications import notify_critical
            notify_critical(f"W7 BOOK [{args.namespace}]: weekend policy preflight FAILED "
                            f"({wpf.get('status')}) — REFUSING to start.")
        except Exception:
            pass
        return 5
    if wpf.get("status") == "armed":
        logging.warning("WEEKEND FLAT IS ON for %s: flatten at %s (broker weekend boundary %s, "
                        "%.2f h of margin), entry embargo %.2f h, exempt=%s. This CLOSES LIVE "
                        "POSITIONS on a schedule and REFUSES entries inside the window.",
                        wpf["policy"]["sleeves"], wpf["next_flatten_deadline_utc"],
                        wpf["next_weekend_boundary_utc"],
                        wpf["policy"]["flatten_before_hours"],
                        wpf["policy"]["entry_embargo_hours"],
                        wpf["policy"]["exempt_sleeves"] or "none")
        if not wpf["policy"]["early_close_dates"]:
            logging.warning("WEEKEND FLAT has NO early-close list. 2.6 %% of the archive's "
                            "weekend-flat exits fall in a holiday-shortened week, where a "
                            "Saturday-anchored deadline aims at a market that shut a day "
                            "earlier — a BREACH, not a cost. Supply --weekend-early-close, or "
                            "use --weekend-flatten-before-hours 24.")
        _ungoverned = wpf.get("governs_sleeves_this_worker_does_not_trade")
        if _ungoverned:
            logging.warning("WEEKEND FLAT governs %s, which this worker's registry does not "
                            "generate. That is legal and is the safe ORDER (guard first, sleeve "
                            "second) — but the guard is inert for those names today.",
                            _ungoverned)
    if minimal_size_cfg.enabled:
        # A book whose command line you cannot read is a book you cannot trust (CLAUDE.md §4:
        # check the command line, not the heartbeat). This is the loudest line in the log.
        logging.warning(
            "F5 MINIMAL SIZE ARMED: every DECISION at the NOMINAL dial; every LOT at $%.2f "
            "risk/trade; governor reads a NOTIONAL ledger starting at $%.0f; sub-minimum lots "
            "ROUND UP to volume_min (never shed); broker identity magic=%d prefix=%r; "
            "NO loss budget (owner-directed 2026-08-12) -- the firm's limits, the governor, "
            "the kill flag and the activation token are the only brakes and none is bypassed.",
            minimal_size_cfg.target_risk_usd, minimal_size_cfg.notional_initial_usd,
            _magic, comment_prefix_for_namespace(args.namespace))
    if args.recover_pre_gap_bar:
        logging.warning("PRE-GAP BAR RECOVERY IS ON: the last closed bar before a session gap "
                        "is now a decision bar. This changes which bars this book trades.")
    if args.vol_level_tilt:
        logging.warning("VOL-LEVEL SIZING TILT IS ON: sub_xvol_pullback intents are sized by "
                        "clamp(vr/2.0, 0.80, 1.20). This changes the RISK this book puts behind "
                        "that sleeve (net de-risk, mean multiplier 0.925 on the archive).")
    if frontier_exits:
        # B1852: this banner used to render `float(_o["final_target_r"])`, which SIX of the eight
        # wired sleeves do not carry (they are `time_stop_*` cells) -- so naming one of them killed
        # the worker at launch, after `parse_frontier_exits` had accepted it, into a supervisor
        # restart loop in which `manage_open_positions` never runs. `describe_frontier_contract`
        # renders whichever contract keys the override actually has.
        from src.components.ultimate_book.execution_packets import (
            FRONTIER_EXIT_OVERRIDES, describe_frontier_contract,
        )
        for _s in frontier_exits:
            logging.warning("FRONTIER EXIT CONTRACT IS ON for %s: %s (%s). This changes WHERE or "
                            "WHEN this book exits that sleeve; positions already open are managed "
                            "from their own trade record, but one adopted WITHOUT a record is "
                            "rehydrated at this contract.", _s,
                            FRONTIER_EXIT_OVERRIDES[_s]["frontier_cell"],
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
    if risk_unit_floor_policy.enabled:
        for _s in sorted(risk_unit_floor_policy.sleeves):
            _p = risk_unit_floor_policy.sleeves[_s]
            logging.warning(
                "Q1 RISK-UNIT FLOOR %s for %s: max(stop, %.4g x decision-cutoff "
                "M15 bar24, %.4g x round-trip cost)%s; target=%s. %s",
                risk_unit_floor_policy.mode.upper(),
                _s,
                _p.bar_multiple,
                _p.cost_multiple,
                "" if _p.cap_widen is None else f", cap={_p.cap_widen:.4g}x",
                _p.target_policy,
                (
                    "SHADOW CANNOT CHANGE OR REFUSE A TRADE"
                    if risk_unit_floor_policy.mode == "shadow"
                    else "APPLY MAY CHANGE STOP/LOT GEOMETRY AFTER ALL EXISTING REFUSALS"
                ),
            )
    if entry_hour:
        for _s in sorted(entry_hour):
            logging.warning("ENTRY-HOUR CONVENTION IS ON for %s: enter at broker hour %02d "
                            "instead of the decision bar's own close. The intent is DEFERRED "
                            "at generation and re-proposed each tick until the broker clock "
                            "reaches it, so this book PLACES LATER and at a different price. "
                            "Ratified 2026-07-30 (phase9/OWNER_DECISION_ENTRY_HOUR.md).",
                            _s, entry_hour[_s])
    if args.event_clock_shadow:
        logging.warning(
            "Q2 EVENT-CLOCK SHADOW IS ON: exact H4 CLOSE events are classified from "
            "decision_bar_iso (bar OPEN) + 240 minutes and latched across retries. "
            "TELEMETRY ONLY -- admission, sizing, placement and broker state are unchanged."
        )
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
            if _challenge_writer(args.namespace):
                run_loop(launcher)
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

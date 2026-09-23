#!/usr/bin/env python3
"""Evidence pack 1.4a — the dial-counterfactual grid.

The question
------------
The 2.0 % nominal dial was **structurally unreachable** in the live fortnight: the highest
confidence that actually traded was 0.40, which caps a unit at 0.80 % (B65).  B65 then priced the
dial with a *linear* counterfactual — "at 1.25 % the loss would be 0.625×" — and concluded the dial
explains 37.5 % of the loss's magnitude and none of its sign.

Linear is the wrong model, and this pack exists to say by how much.  `base_risk_per_unit` feeds a
**closed feedback loop**: bigger dial → bigger losses → deeper drawdown → smaller
`size_cap_multiplier` (`admission.py:1300-1306`) → smaller subsequent units; and, discretely,
bigger dial → the −3 % soft daily stop and the −9 % entry block fire *earlier*, which removes
whole trades from the path rather than shrinking them.  Neither effect is linear and the second is
not even continuous.

What this simulates, exactly
----------------------------
Substrate is the 175 W7-denominator broker trade rows (`LIVE_TRADE_ROWS.jsonl`) — realised R,
realised risk %, entry/exit stamps, and all three day keys, per account.  For each dial the
simulator walks the account's event stream in time order and re-derives, at every entry:

  * the governor decision (`admission.evaluate_governor` semantics, smooth or band)
  * the −3 % soft daily stop, on **that account's own reset clock** (FTMO 00:00 CE(S)T,
    redacted_account 00:00 server time — B56; the rows carry both keys precomputed)
  * the −9 % max-DD entry block and the −10 % wall
  * the 4 % gross-open-risk cap against concurrently open counterfactual risk
  * OPS-03 profit-target protect (FTMO +10 %, redacted_account +8 %)

and sizes the trade as::

    risk_pct(dial) = risk_pct(live) × (dial / 0.02) × (cap_mult_cf / cap_mult_live)

which holds confidence, the Kelly bin, the ladder step, the unit split and the stop distance at
their **recorded** values and varies only what the dial actually varies.  R is dial-invariant by
construction: both the numerator (P&L including commission, which scales with volume) and the
denominator (`risk_at_entry_usd`) scale linearly with lot size, so `realized_r` transfers.

The null control (working agreement §3.1)
-----------------------------------------
``--null-draws`` **order-only** permutations per account, re-run over the whole grid.

Getting this right took two attempts and the first one is recorded because it was wrong in an
instructive way.  Version 1 permuted the realised-R *values* while leaving each slot's recorded
`live_risk_pct` welded in place.  That does not permute order; it destroys the pairing between an
outcome and the size it was taken at, and since `live_risk_pct` spans 26x across trades, that
de-pairing variance swamped everything.  An adversarial pass measured the damage: with the feedback
loop switched off the version-1 "band" is *wider* than with it on, i.e. essentially none of it was
the governor.

What is implemented now moves the **whole trade** — its R and its intrinsic size — to a new slot,
and re-derives the live reference along the same permuted path::

    s_i = live_risk_pct_i / cap_mult(live_equity at its original slot)

`s_i` is the dial-free, governor-free part of the sizing (base x confidence x Kelly x ladder,
`admission.py:1192`), so permuting `(r_i, s_i)` pairs and re-running the governor over the permuted
sequence varies **only** arrival order.  Under it, Sum r_i . risk_i is no longer invariant, because
each trade's size is recomputed from the drawdown the permuted path had actually reached.

Stated limitations, because they bound what the grid licenses
-------------------------------------------------------------
1. **In-sample.**  Choosing a dial on the same 38 days that produced the R sequence is in-sample by
   construction.  This is a sensitivity surface, not an optimiser, and the argmax is reported only
   alongside the whole surface.
2. **Realised-only equity.**  The path accrues P&L at exit; floating P&L on open positions is
   invisible.  ``--validate`` measures the resulting gap against the recorded governor multipliers.
3. **No intra-day flatten.**  `ultimate_book_flatten_on_breach` (−4 % daily / −9 % DD, 2 confirm
   ticks) would truncate losing days that this simulator rides to their recorded exits.  Not
   modelling it makes every reported loss and breach-proximity number a **conservative upper
   bound**, which is the correct direction for a risk statement.
4. **Lot granularity.**  Live volumes are quantised (0.01 lots); the counterfactual scales
   continuously.  At small dials this overstates deployable precision.

Run:  python3 scripts/evidence_pack_dial_grid.py
"""
from __future__ import annotations

import argparse
import gzip
import json
import random
import statistics
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

DEFAULT_ROWS = REPO / "docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl"
DEFAULT_PACKETS = Path(
    "/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/"
    "ultimate_book_runtime_learning_packets.jsonl.gz"
)
DEFAULT_OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase3/evidence_packs"

SCHEMA = "gtos.phase3.evidence_pack.dial_grid.v1"

LIVE_DIAL = 0.02                    # clean3_w7_ceiling_nom2p00, agent_config.yaml:1302
INITIAL_BALANCE = 100_000.0         # governor_static_initial_balance, agent_config.yaml:1345

#: `config/agent_config.yaml:1332-1335,1345,1353-1356` + the two profiles' prop-rule blocks.
LIMITS = {
    "soft_daily_stop_pct": 0.03,
    "max_dd_limit_pct": 0.10,
    "max_dd_entry_block_pct": 0.09,
    "derisk_start_dd_pct": 0.07,
    "gross_open_risk_cap_pct": 0.04,
    "profit_target_derisk_mult": 0.25,
    "flatten_daily_loss_pct": 0.04,
    "flatten_maxdd_pct": 0.09,
}
#: firm rules — `config/profiles/operator_profile.yaml:99-104`; redacted_account.yaml:9,14
#:
#: `reset_rule` / `alt_rule` are resolved through `broker_clock` at each instant rather than read
#: off the trade row, because the row only carries day keys computed at ENTRY time and the live
#: governor attributes realised P&L to the day a deal CLOSED (`governor_state.py:202-205` filters
#: to DEAL_ENTRY_OUT and keys on the close deal's `time`).  Reading the row's key for an exit was a
#: real defect in the first version of this script; see the receipt's withdrawal section.
#: `alt_rule` is the *other* firm's reset calendar, used only for the sensitivity probe.
ACCOUNTS = {
    "ftmo": {
        "namespace": "operator_profile",
        "reset_rule": "europe_prague",               # 00:00 CE(S)T — B56
        "alt_rule": "server",                        # what the pre-B56 code used
        "firm_daily_loss_limit_pct": 0.05,
        "firm_max_loss_pct": 0.10,
        "profit_target_pct": 0.10,
    },
    "redacted_account": {
        "namespace": "redacted_account_live_bee34003",
        "reset_rule": "server",                      # 00:00 server time — B56
        "alt_rule": "europe_prague",
        "firm_daily_loss_limit_pct": 0.05,
        "firm_max_loss_pct": 0.10,
        "profit_target_pct": 0.08,
    },
}

#: MT5 server clock per account, for the "server" reset rule (`broker_clock.NEW_YORK_PLUS_7`).
SERVER_RULE = {"ftmo": "ftmo-server3", "redacted_account": "redacted_account-server 2"}


def reset_day(instant_iso: str, account: str, rule_key: str) -> str:
    """Day key under a named reset calendar, for ANY instant (entry or exit).

    `rule_key` is `"europe_prague"` (a firm calendar) or `"server"` (the MT5 server clock).
    Never returns None: an unresolvable rule raises rather than silently bucketing everything
    under one key, which is exactly the defect this replaced.
    """
    from datetime import timedelta, datetime
    from src.utils import broker_clock as BC

    t = datetime.fromisoformat(instant_iso)
    if rule_key == "server":
        rule = BC.resolve_rule(SERVER_RULE[account])
        off_h = BC.offset_seconds_at_utc(t, rule) / 3600.0
    else:
        off_h = BC.daily_reset_offset_hours(t, rule_key)
        if off_h is None:
            raise SystemExit(f"unresolvable reset rule {rule_key!r} for {account}")
    return (t + timedelta(hours=off_h)).date().isoformat()

#: Extends well past any dial the owner would run, deliberately: the interesting structure in this
#: surface is *where the discrete brakes first engage*, and on this fortnight that is far above the
#: 2.0 % ceiling.  Reporting only the plausible range would hide the fact that the brakes never fire.
DIAL_GRID = [0.0025, 0.005, 0.0075, 0.010, 0.0125, 0.015, 0.0175, 0.020, 0.025, 0.030, 0.040,
             0.050, 0.060, 0.080, 0.100, 0.150, 0.200]
#: named live profiles, for labelling the grid
DIAL_LABELS = {
    0.005: "conservative_0p50", 0.0075: "balanced_0p75", 0.0125: "clean3_w7_deploy_nom1p25",
    0.015: "clean3_w7_growth_nom1p50", 0.020: "clean3_w7_ceiling_nom2p00 (LIVE)",
}


# --------------------------------------------------------------------------------------------
def _cap_mult(equity: float, derisk_mode: str) -> float:
    """`admission.py:1284-1306`, smooth and band, against the STATIC 100k reference."""
    dd = (INITIAL_BALANCE - equity) / INITIAL_BALANCE
    if dd <= 0:
        return 1.0
    if derisk_mode == "smooth":
        return max(0.0, 1.0 - dd / LIMITS["max_dd_limit_pct"])
    if dd <= LIMITS["derisk_start_dd_pct"]:
        return 1.0
    span = LIMITS["max_dd_limit_pct"] - LIMITS["derisk_start_dd_pct"]
    return max(0.0, 1.0 - (dd - LIMITS["derisk_start_dd_pct"]) / span)


@dataclass
class Trade:
    idx: int
    entry: str
    exit: str
    r: float
    live_risk_pct: float
    entry_day: dict           # rule_key -> day string at ENTRY (gates the soft daily stop)
    exit_day: dict            # rule_key -> day string at EXIT  (where realised P&L lands)
    sleeve: str
    symbol: str
    intrinsic: float = 0.0    # dial-free, governor-free size component; used by the order-only null


@dataclass
class SimResult:
    dial: float
    derisk_mode: str
    account: str
    reset_rule: str
    taken: int = 0
    blocked: dict = field(default_factory=dict)
    final_pct: float = 0.0
    w7_pct: float = 0.0
    exogenous_pct: float = 0.0
    sum_r_taken: float = 0.0
    worst_day_pct: float = 0.0
    best_day_pct: float = 0.0
    max_dd_static_pct: float = 0.0
    max_dd_peak_pct: float = 0.0
    daily_breach: bool = False
    total_breach: bool = False
    flatten_daily_hits: int = 0
    flatten_dd_hits: int = 0
    soft_stop_days: int = 0
    hit_profit_target: bool = False
    day_pnl: dict = field(default_factory=dict)


def simulate(trades: list[Trade], *, dial: float, derisk_mode: str, account: str,
             start_equity: float, reset_rule: str, r_override: list[float] | None = None,
             exogenous: list[tuple[str, float, str]] | None = None) -> SimResult:
    """One grid cell.  Trades are consumed in entry order; P&L accrues at exit.

    ``exogenous`` carries (exit_stamp, cash_pnl, reset_day) for non-W7 trades that close inside the
    window.  Their P&L is dial-independent — it moves the equity the governor reads, so it must be
    in the path, but it must not be scaled.  Omitting it was a real bug in the first version of
    this script, caught by :func:`validate_against_packets` as a persistent −$212 FTMO residual.
    """
    cfg = ACCOUNTS[account]
    res = SimResult(dial=dial, derisk_mode=derisk_mode, account=account, reset_rule=reset_rule)
    res.blocked = {"soft_daily_stop": 0, "max_dd_entry_block": 0, "max_dd_limit": 0,
                   "gross_risk_cap": 0, "ceiling_requires_smooth": 0}

    # The `admit_and_size` interlock: a >=2.0% dial on a non-smooth de-risk shape fails closed and
    # sizes NOTHING (`admission.py:1407-1410`).  That is a real, discrete cliff in this grid.
    if dial >= 0.02 - 1e-9 and derisk_mode != "smooth":
        res.blocked["ceiling_requires_smooth"] = len(trades)
        # the book sizes nothing, but the exogenous non-W7 P&L still happens
        res.exogenous_pct = sum(c for _s, c, _d in (exogenous or [])) / INITIAL_BALANCE
        res.final_pct = res.exogenous_pct
        return res

    events: list[tuple[str, int, str]] = []
    for t in trades:
        events.append((t.entry, t.idx, "entry"))
        events.append((t.exit or t.entry, t.idx, "exit"))
    exo_by_id: dict[int, tuple[float, str]] = {}
    for j, (stamp, cash, day) in enumerate(exogenous or []):
        eid = -(j + 1)
        exo_by_id[eid] = (cash, day)
        events.append((stamp, eid, "exogenous"))
    events.sort(key=lambda e: (e[0], {"exit": 0, "exogenous": 1, "entry": 2}[e[2]]))

    by_idx = {t.idx: t for t in trades}
    rs = {t.idx: (r_override[i] if r_override else t.r) for i, t in enumerate(trades)}

    equity = start_equity
    peak = max(equity, INITIAL_BALANCE)
    open_risk_pct = 0.0
    taken_risk: dict[int, float] = {}
    day_start_equity: dict[str, float] = {}
    day_realized: dict[str, float] = {}
    soft_stopped_days: set[str] = set()
    cur_day = None

    rule_key = (cfg["reset_rule"] if reset_rule == "firm_true" else cfg["alt_rule"])
    for stamp, idx, kind in events:
        if kind == "exogenous":
            cash, daymap = exo_by_id[idx]
            day = daymap[rule_key]
            if day not in day_start_equity:
                day_start_equity[day] = equity
                day_realized[day] = 0.0
            equity += cash
            day_realized[day] += cash
            res.exogenous_pct += cash / INITIAL_BALANCE
            peak = max(peak, equity)
            continue
        t = by_idx[idx]
        # Entries gate on the day they OPEN; realised P&L lands on the day the deal CLOSES, which
        # is what `governor_state.py:202-205` does (DEAL_ENTRY_OUT, keyed on the close deal's time).
        day = t.entry_day[rule_key] if kind == "entry" else t.exit_day[rule_key]
        if day not in day_start_equity:
            day_start_equity[day] = equity
            day_realized[day] = 0.0
        if kind == "entry":
            realized_today_pct = day_realized[day] / max(1e-9, day_start_equity[day])
            dd = (INITIAL_BALANCE - equity) / INITIAL_BALANCE
            if realized_today_pct <= -LIMITS["soft_daily_stop_pct"]:
                res.blocked["soft_daily_stop"] += 1
                soft_stopped_days.add(day)
                continue
            if dd >= LIMITS["max_dd_limit_pct"]:
                res.blocked["max_dd_limit"] += 1
                continue
            if dd >= LIMITS["max_dd_entry_block_pct"]:
                res.blocked["max_dd_entry_block"] += 1
                continue
            available = LIMITS["gross_open_risk_cap_pct"] - open_risk_pct
            if available <= 0:
                res.blocked["gross_risk_cap"] += 1
                continue

            cap_cf = _cap_mult(equity, derisk_mode)
            gain = (equity - INITIAL_BALANCE) / INITIAL_BALANCE
            if gain >= cfg["profit_target_pct"]:
                cap_cf *= LIMITS["profit_target_derisk_mult"]
                res.hit_profit_target = True
            cap_live = _cap_mult(t.live_equity, "smooth")     # live ran smooth, always
            if cap_live <= 1e-9:
                continue
            risk = t.live_risk_pct * (dial / LIVE_DIAL) * (cap_cf / cap_live)
            if risk > available + 1e-12:
                res.blocked["gross_risk_cap"] += 1
                continue
            taken_risk[idx] = risk
            open_risk_pct += risk
            res.taken += 1
            res.sum_r_taken += rs[idx]
        else:
            risk = taken_risk.pop(idx, None)
            if risk is None:
                continue
            open_risk_pct = max(0.0, open_risk_pct - risk)
            pnl_pct = rs[idx] * risk                 # R x risk% == P&L as a fraction of equity basis
            pnl_cash = pnl_pct * INITIAL_BALANCE
            res.w7_pct += pnl_pct
            equity += pnl_cash
            day_realized[day] = day_realized.get(day, 0.0) + pnl_cash
            peak = max(peak, equity)
            dd_static = (INITIAL_BALANCE - equity) / INITIAL_BALANCE
            dd_peak = (peak - equity) / peak
            res.max_dd_static_pct = max(res.max_dd_static_pct, dd_static)
            res.max_dd_peak_pct = max(res.max_dd_peak_pct, dd_peak)
            if dd_static >= cfg["firm_max_loss_pct"]:
                res.total_breach = True
            if dd_static >= LIMITS["flatten_maxdd_pct"]:
                res.flatten_dd_hits += 1

    for day, pnl in day_realized.items():
        pct = pnl / max(1e-9, day_start_equity.get(day, INITIAL_BALANCE))
        res.day_pnl[day] = pct
        res.worst_day_pct = min(res.worst_day_pct, pct)
        res.best_day_pct = max(res.best_day_pct, pct)
        if pct <= -cfg["firm_daily_loss_limit_pct"]:
            res.daily_breach = True
        if pct <= -LIMITS["flatten_daily_loss_pct"]:
            res.flatten_daily_hits += 1
    res.soft_stop_days = len(soft_stopped_days)
    res.final_pct = (equity - start_equity) / INITIAL_BALANCE
    return res


# --------------------------------------------------------------------------------------------
def load_trades(rows_path: Path):
    rows = [json.loads(l) for l in rows_path.read_text().splitlines() if l.strip()]
    per_account: dict[str, list[Trade]] = {}
    start_equity: dict[str, float] = {}
    for acct in ACCOUNTS:
        acct_rows = [r for r in rows if r["account"] == acct]
        w7 = sorted((r for r in acct_rows if r["in_w7_denominator"]),
                    key=lambda r: r["entry_time_utc"])
        first_entry = w7[0]["entry_time_utc"]
        # everything the account realised before the book's first W7 entry is the starting equity;
        # nothing non-W7 closes inside the window on either account (checked).
        prior = sum(r["realized_net"] for r in acct_rows
                    if not r["in_w7_denominator"] and (r["exit_time_utc"] or "") < first_entry)
        last_exit = max(r["exit_time_utc"] or r["entry_time_utc"] for r in w7)
        inside = [r for r in acct_rows if not r["in_w7_denominator"]
                  and first_entry <= (r["exit_time_utc"] or "") <= last_exit]
        start_equity[acct] = INITIAL_BALANCE + prior
        rules = (ACCOUNTS[acct]["reset_rule"], ACCOUNTS[acct]["alt_rule"])
        per_account[acct] = []
        for i, r in enumerate(w7):
            ex = r["exit_time_utc"] or r["entry_time_utc"]
            per_account[acct].append(Trade(
                idx=i, entry=r["entry_time_utc"], exit=ex,
                r=r["realized_r"], live_risk_pct=r["risk_pct_of_balance"],
                entry_day={k: reset_day(r["entry_time_utc"], acct, k) for k in rules},
                exit_day={k: reset_day(ex, acct, k) for k in rules},
                sleeve=r.get("sleeve_id") or "?", symbol=r["canonical_symbol"]))
        per_account[acct + "__exogenous"] = [
            (r["exit_time_utc"], r["realized_net"],
             {k: reset_day(r["exit_time_utc"], acct, k) for k in rules})
            for r in sorted(inside, key=lambda r: r["exit_time_utc"])
        ]
        per_account[acct + "__exogenous_rows"] = [
            {"entry": r["entry_time_utc"], "exit": r["exit_time_utc"], "era": r["stack_era"],
             "symbol": r["canonical_symbol"], "realized_net": r["realized_net"]} for r in inside
        ]
    return per_account, start_equity


def annotate_live_equity(trades: list[Trade], start_equity: float, exogenous=()):
    """Walk the LIVE path once so every trade knows the live equity at its own entry."""
    events = []
    for t in trades:
        events.append((t.entry, t.idx, "entry"))
        events.append((t.exit, t.idx, "exit"))
    exo = {}
    for j, (stamp, cash, _day) in enumerate(exogenous):
        exo[-(j + 1)] = cash
        events.append((stamp, -(j + 1), "exogenous"))
    events.sort(key=lambda e: (e[0], {"exit": 0, "exogenous": 1, "entry": 2}[e[2]]))
    by_idx = {t.idx: t for t in trades}
    equity = start_equity
    for stamp, idx, kind in events:
        if kind == "exogenous":
            equity += exo[idx]
            continue
        t = by_idx[idx]
        if kind == "entry":
            t.live_equity = equity
        else:
            equity += t.r * t.live_risk_pct * INITIAL_BALANCE
    return equity


def annotate_live_equity_from_intrinsic(trades, start_equity: float, exogenous=()):
    """Live reference for a permuted ordering: size = intrinsic x cap_mult(equity at that slot).

    This is what makes the null order-ONLY. Each trade keeps its own dial-free size component and
    the governor re-decides the multiplier from the drawdown the permuted path has actually
    reached, so nothing is compared against a multiplier from a path that never happened.
    """
    events = []
    for t in trades:
        events.append((t.entry, t.idx, "entry"))
        events.append((t.exit, t.idx, "exit"))
    exo = {}
    for j, (stamp, cash, _day) in enumerate(exogenous):
        exo[-(j + 1)] = cash
        events.append((stamp, -(j + 1), "exogenous"))
    events.sort(key=lambda e: (e[0], {"exit": 0, "exogenous": 1, "entry": 2}[e[2]]))
    by_idx = {t.idx: t for t in trades}
    equity = start_equity
    for stamp, idx, kind in events:
        if kind == "exogenous":
            equity += exo[idx]
            continue
        t = by_idx[idx]
        if kind == "entry":
            t.live_equity = equity
            t.live_risk_pct = t.intrinsic * _cap_mult(equity, "smooth")
        else:
            equity += t.r * t.live_risk_pct * INITIAL_BALANCE
    return equity


def validate_against_packets(packets: Path, trades_by_account, start_equity, exogenous) -> dict:
    """Independent check: the reconstructed live equity path vs the recorded governor multiplier.

    `size_cap_multiplier` under smooth inverts to an equity: equity = 100k·(1 − 0.10·(1 − mult)).
    The reconstruction accrues only *realised* P&L, so any residual is the floating P&L on open
    positions plus reconstruction error.  Reporting the residual is the point — an unvalidated
    comparator is the failure mode B99e named.
    """
    opener = gzip.open if packets.suffix == ".gz" else open
    with opener(packets, "rb") as fh:
        if fh.read(40).startswith(b"version https://git-lfs"):
            raise SystemExit(f"packet source is an unhydrated LFS pointer: {packets}")
    recorded: dict[str, list[tuple[str, float]]] = {a: [] for a in ACCOUNTS}
    ns_to_acct = {v["namespace"]: k for k, v in ACCOUNTS.items()}
    seen = set()
    with (gzip.open if packets.suffix == ".gz" else open)(packets, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            pkt = json.loads(line)
            gov = (pkt.get("bridge") or {}).get("governor")
            if not isinstance(gov, dict):
                continue
            acct = ns_to_acct.get(pkt.get("namespace"))
            if acct is None:
                continue
            key = (acct, pkt.get("created_at_utc"), gov.get("size_cap_multiplier"))
            if key in seen:
                continue
            seen.add(key)
            recorded[acct].append((pkt["created_at_utc"], float(gov["size_cap_multiplier"])))

    out = {}
    for acct, samples in recorded.items():
        samples.sort()
        trades = trades_by_account[acct]
        # Restrict to the simulated window. After the last W7 exit both the reconstruction and the
        # governor are frozen, so every later sample is an identical-zero residual that pads n and
        # drags the median to zero without testing anything. An adversarial pass found 1,557 of
        # redacted_account's 2,569 samples were exactly that.
        win_lo = min(t.entry for t in trades)
        win_hi = max(t.exit for t in trades)
        samples = [s for s in samples if win_lo <= s[0] <= win_hi]
        # step the realised path and compare at each recorded governor stamp
        events = sorted([(t.exit, t.r * t.live_risk_pct * INITIAL_BALANCE) for t in trades]
                        + [(stamp, cash) for stamp, cash, _d in exogenous.get(acct, [])])
        equity = start_equity[acct]
        ei = 0
        residuals = []
        for stamp, mult in samples:
            while ei < len(events) and events[ei][0] <= stamp:
                equity += events[ei][1]
                ei += 1
            if mult >= 1.0 - 1e-9:
                continue                                  # saturated: inverts to "equity >= 100k"
            implied = INITIAL_BALANCE * (1.0 - LIMITS["max_dd_limit_pct"] * (1.0 - mult))
            residuals.append(equity - implied)
        if not residuals:
            out[acct] = {"n": 0}
            continue
        rs = sorted(residuals)
        out[acct] = {
            "n_governor_samples": len(rs),
            "window_restricted": True,
            "residual_usd_mean": statistics.fmean(rs),
            "residual_usd_median": statistics.median(rs),
            "residual_usd_p05": rs[int(0.05 * (len(rs) - 1))],
            "residual_usd_p95": rs[int(0.95 * (len(rs) - 1))],
            "residual_usd_min": rs[0], "residual_usd_max": rs[-1],
            "residual_pct_of_balance_median": statistics.median(rs) / INITIAL_BALANCE,
            "interpretation": (
                "positive residual = reconstruction richer than the governor believed, i.e. the "
                "governor was seeing floating losses the realised path has not booked yet"),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=Path, default=DEFAULT_ROWS)
    ap.add_argument("--packets", type=Path, default=DEFAULT_PACKETS)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--seed", type=int, default=20260727)
    ap.add_argument("--null-draws", type=int, default=400)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    loaded, start_equity = load_trades(args.rows)
    trades_by_account = {a: loaded[a] for a in ACCOUNTS}
    exogenous = {a: loaded[a + "__exogenous"] for a in ACCOUNTS}
    for acct, trades in trades_by_account.items():
        annotate_live_equity(trades, start_equity[acct], exogenous[acct])

    report: dict = {
        "schema": SCHEMA,
        "trade_rows_source": str(args.rows),
        "packet_source": str(args.packets),
        "seed": args.seed,
        "live_dial": LIVE_DIAL,
        "live_dial_profile": "clean3_w7_ceiling_nom2p00 (config/agent_config.yaml:1302)",
        "initial_balance": INITIAL_BALANCE,
        "limits": LIMITS,
        "accounts": ACCOUNTS,
        "dial_grid": DIAL_GRID,
        "in_sample_caveat": (
            "Every number here is computed on the same 38 days that produced the R sequence. "
            "Choosing a dial from this surface is in-sample by construction. The surface answers "
            "'how does risk respond to the dial', not 'which dial is best'."),
        "substrate": {
            acct: {
                "n_w7_trades": len(trades),
                "start_equity": start_equity[acct],
                "window": [trades[0].entry, trades[-1].exit],
                "sum_realized_r": sum(t.r for t in trades),
                "non_w7_trades_closing_inside_window": loaded[acct + "__exogenous_rows"],
                "reset_rule_name": ACCOUNTS[acct]["reset_rule"],
                "distinct_entry_reset_days": len({t.entry_day[ACCOUNTS[acct]["reset_rule"]] for t in trades}),
                "distinct_exit_reset_days": len({t.exit_day[ACCOUNTS[acct]["reset_rule"]] for t in trades}),
                "trades_closing_on_a_different_reset_day_than_they_opened": sum(
                    1 for t in trades
                    if t.entry_day[ACCOUNTS[acct]["reset_rule"]] != t.exit_day[ACCOUNTS[acct]["reset_rule"]]),
            } for acct, trades in trades_by_account.items()
        },
    }

    report["comparator_validation"] = validate_against_packets(args.packets, trades_by_account,
                                                               start_equity, exogenous)

    # ---------------- the grid -----------------------------------------------------------------
    grid = []
    for acct, trades in trades_by_account.items():
        for mode in ("smooth", "band"):
            for rule in ("firm_true", "alt_rule"):
                for dial in DIAL_GRID:
                    r = simulate(trades, dial=dial, derisk_mode=mode, account=acct,
                                 start_equity=start_equity[acct], reset_rule=rule,
                                 exogenous=exogenous[acct])
                    grid.append({
                        "account": acct, "derisk_mode": mode, "reset_rule": rule,
                        "reset_rule_name": (ACCOUNTS[acct]["reset_rule"] if rule == "firm_true"
                                            else ACCOUNTS[acct]["alt_rule"]),
                        "dial": dial, "dial_label": DIAL_LABELS.get(dial),
                        "trades_taken": r.taken, "trades_blocked": dict(r.blocked),
                        "final_pct_of_initial": r.final_pct,
                        "final_cash": r.final_pct * INITIAL_BALANCE,
                        "w7_pct_of_initial": r.w7_pct,
                        "w7_cash": r.w7_pct * INITIAL_BALANCE,
                        "exogenous_pct_of_initial": r.exogenous_pct,
                        "sum_r_taken": r.sum_r_taken,
                        "worst_day_pct": r.worst_day_pct,
                        "best_day_pct": r.best_day_pct,
                        "max_dd_static_pct": r.max_dd_static_pct,
                        "max_dd_peak_pct": r.max_dd_peak_pct,
                        "firm_daily_breach": r.daily_breach,
                        "firm_total_breach": r.total_breach,
                        "daily_breach_proximity": (abs(r.worst_day_pct)
                                                   / ACCOUNTS[acct]["firm_daily_loss_limit_pct"]),
                        "total_breach_proximity": (r.max_dd_static_pct
                                                   / ACCOUNTS[acct]["firm_max_loss_pct"]),
                        "flatten_daily_hits": r.flatten_daily_hits,
                        "flatten_dd_hits": r.flatten_dd_hits,
                        "soft_stop_days": r.soft_stop_days,
                    })
    report["grid"] = grid

    # ---------------- identity check ------------------------------------------------------------
    # NARROWED after adversarial review.  At dial == LIVE_DIAL the sizing ratio (dial/LIVE_DIAL) is
    # 1 and cap_cf/cap_live cancels identically, so this check is ALGEBRAICALLY FORCED: a refuter
    # re-ran it with `_cap_mult` replaced by a constant 1.0 and it still passed to $0.00000000.  It
    # therefore proves nothing about the governor, the day bucketing, or any counterfactual cell.
    # What it does still test, and all it is claimed for: that no gate fires at the live dial
    # (trade counts match), that the exogenous path is applied symmetrically to the simulated and
    # reference walks, and that the event ordering does not corrupt the accumulation.
    identity = {}
    for acct, trades in trades_by_account.items():
        observed = sum(t.r * t.live_risk_pct for t in trades)
        cell = next(g for g in grid if g["account"] == acct and g["dial"] == LIVE_DIAL
                    and g["derisk_mode"] == "smooth" and g["reset_rule"] == "firm_true")
        identity[acct] = {
            "observed_w7_pct_of_initial": observed,
            "simulated_w7_pct_of_initial": cell["w7_pct_of_initial"],
            "abs_error_pct_of_initial": cell["w7_pct_of_initial"] - observed,
            "abs_error_usd": (cell["w7_pct_of_initial"] - observed) * INITIAL_BALANCE,
            "trades_observed": len(trades),
            "trades_simulated": cell["trades_taken"],
            "reproduces_live": (abs(cell["w7_pct_of_initial"] - observed) < 1e-12
                                and cell["trades_taken"] == len(trades)),
            "what_this_proves": ("no gate fires at the live dial; exogenous handling is symmetric; "
                                 "event ordering is sound. It is algebraically forced and proves "
                                 "NOTHING about the governor or any counterfactual cell."),
        }
    report["live_dial_identity_check"] = identity

    # ---------------- linearity test ------------------------------------------------------------
    lin = []
    for acct in trades_by_account:
        base = next(g for g in grid if g["account"] == acct and g["dial"] == LIVE_DIAL
                    and g["derisk_mode"] == "smooth" and g["reset_rule"] == "firm_true")
        for g in grid:
            if (g["account"] != acct or g["derisk_mode"] != "smooth"
                    or g["reset_rule"] != "firm_true"):
                continue
            predicted = base["w7_pct_of_initial"] * (g["dial"] / LIVE_DIAL)
            lin.append({
                "account": acct, "dial": g["dial"],
                "linear_prediction_pct": predicted,
                "simulated_pct": g["w7_pct_of_initial"],
                "abs_error_pct": g["w7_pct_of_initial"] - predicted,
                "rel_error": ((g["w7_pct_of_initial"] - predicted) / predicted
                              if abs(predicted) > 1e-12 else None),
                "trades_dropped_vs_live": base["trades_taken"] - g["trades_taken"],
            })
    report["linearity_test"] = {
        "reference": "B65 priced the dial linearly ('at 1.25 % the loss would be 0.625x')",
        "rows": lin,
    }

    # ---------------- null control --------------------------------------------------------------
    nulls = {}
    for acct, trades in trades_by_account.items():
        # (R, intrinsic size) pairs: the whole trade moves, so only ORDER varies.
        pairs = [(t.r, t.live_risk_pct / max(1e-12, _cap_mult(t.live_equity, "smooth")))
                 for t in trades]
        per_dial: dict[float, list[float]] = {d: [] for d in DIAL_GRID}
        worst_day: dict[float, list[float]] = {d: [] for d in DIAL_GRID}
        rank_of_live: list[int] = []
        for _ in range(args.null_draws):
            shuffled = pairs[:]
            rng.shuffle(shuffled)
            permuted = [
                Trade(idx=t.idx, entry=t.entry, exit=t.exit, r=shuffled[i][0],
                      live_risk_pct=0.0, entry_day=t.entry_day, exit_day=t.exit_day,
                      sleeve=t.sleeve, symbol=t.symbol)
                for i, t in enumerate(trades)]
            for i, t in enumerate(permuted):
                t.intrinsic = shuffled[i][1]
            # re-derive the LIVE reference along this permuted path, so cap_live is the multiplier
            # the live system would have had under this ordering rather than under the observed one
            annotate_live_equity_from_intrinsic(permuted, start_equity[acct], exogenous[acct])
            cells = {}
            for dial in DIAL_GRID:
                r = simulate(permuted, dial=dial, derisk_mode="smooth", account=acct,
                             start_equity=start_equity[acct], reset_rule="firm_true",
                             exogenous=exogenous[acct])
                per_dial[dial].append(r.final_pct)
                worst_day[dial].append(r.worst_day_pct)
                cells[dial] = r.final_pct
            order = sorted(DIAL_GRID, key=lambda d: -cells[d])
            rank_of_live.append(order.index(LIVE_DIAL) + 1)
        observed = {g["dial"]: g["final_pct_of_initial"] for g in grid
                    if g["account"] == acct and g["derisk_mode"] == "smooth"
                    and g["reset_rule"] == "firm_true"}
        obs_order = sorted(DIAL_GRID, key=lambda d: -observed[d])
        nulls[acct] = {
            "n_draws": args.null_draws,
            "observed_dial_ranking_best_to_worst": obs_order,
            "observed_rank_of_live_dial": obs_order.index(LIVE_DIAL) + 1,
            "null_rank_of_live_dial": {
                "mean": statistics.fmean(rank_of_live),
                "mode": statistics.mode(rank_of_live),
                "frac_equal_to_observed": sum(
                    1 for x in rank_of_live if x == obs_order.index(LIVE_DIAL) + 1) / len(rank_of_live),
            },
            "per_dial_final_pct": {
                str(d): {
                    "observed": observed[d],
                    "null_mean": statistics.fmean(per_dial[d]),
                    "null_p05": sorted(per_dial[d])[int(0.05 * (args.null_draws - 1))],
                    "null_p95": sorted(per_dial[d])[int(0.95 * (args.null_draws - 1))],
                    "observed_percentile_in_null": (
                        sum(1 for x in per_dial[d] if x <= observed[d]) / args.null_draws),
                } for d in DIAL_GRID},
            "per_dial_worst_day_pct": {
                str(d): {
                    "observed": next(g["worst_day_pct"] for g in grid if g["account"] == acct
                                     and g["dial"] == d and g["derisk_mode"] == "smooth"
                                     and g["reset_rule"] == "firm_true"),
                    "null_mean": statistics.fmean(worst_day[d]),
                    "null_p05": sorted(worst_day[d])[int(0.05 * (args.null_draws - 1))],
                } for d in DIAL_GRID},
        }
    # The one statistic in this pack that is NOT an in-sample artifact.  Σ R is fixed by the trade
    # set; only the *order* varies across permutations.  So the width of the null band at a dial is
    # that dial's order-dependence — how much of the outcome is decided by when the wins arrived
    # rather than by whether there were any.  It is computed over permutations, not over the
    # observed path, so choosing a dial to reduce it is not fitting these 38 days.
    for acct, n in nulls.items():
        spread = {}
        for d in DIAL_GRID:
            cell = n["per_dial_final_pct"][str(d)]
            spread[str(d)] = {
                "null_p05": cell["null_p05"], "null_p95": cell["null_p95"],
                "null_spread_pp": (cell["null_p95"] - cell["null_p05"]) * 100.0,
                "spread_per_dial_point": ((cell["null_p95"] - cell["null_p05"]) * 100.0) / (d * 100.0),
            }
        n["order_dependence"] = {
            "definition": ("p95 - p05 of final P&L across R-sequence permutations, in percentage "
                           "points of initial balance. Sum-of-R is identical in every permutation."),
            "per_dial": spread,
        }
    report["null_control"] = nulls

    args.out.mkdir(parents=True, exist_ok=True)
    dest = args.out / "DIAL_GRID.json"
    dest.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    print(f"wrote {dest}")

    # ---------------- console ------------------------------------------------------------------
    for acct in trades_by_account:
        s = report["substrate"][acct]
        print(f"\n=== {acct}: {s['n_w7_trades']} W7 trades, start equity {s['start_equity']:.2f}, "
              f"ΣR {s['sum_realized_r']:.4f}, {s['distinct_exit_reset_days']} exit-reset days "
              f"({s['reset_rule_name']}), "
              f"{s['trades_closing_on_a_different_reset_day_than_they_opened']} cross-day closes")
        v = report["comparator_validation"][acct]
        if v.get("n_governor_samples"):
            print(f"    comparator check vs recorded governor: n={v['n_governor_samples']}, "
                  f"median residual ${v['residual_usd_median']:.0f} "
                  f"({v['residual_pct_of_balance_median']*100:.3f} % of balance)")
        ic = report["live_dial_identity_check"][acct]
        print(f"    live-dial identity: simulated W7 {ic['simulated_w7_pct_of_initial']*100:.6f} % vs "
              f"observed {ic['observed_w7_pct_of_initial']*100:.6f} % "
              f"(err ${ic['abs_error_usd']:.6f}) -> reproduces_live={ic['reproduces_live']}")
        print(f"{'dial':>8s} {'label':<32s} {'taken':>6s} {'W7 %':>9s} {'worstday%':>10s} "
              f"{'maxDDstat%':>11s} {'dailyProx':>9s} {'totProx':>8s} {'softStop':>8s} {'linErr':>8s}")
        linrows = {(r["account"], r["dial"]): r for r in report["linearity_test"]["rows"]}
        for g in grid:
            if g["account"] != acct or g["derisk_mode"] != "smooth" or g["reset_rule"] != "firm_true":
                continue
            rel = linrows[(acct, g["dial"])]["rel_error"]
            print(f"{g['dial']*100:7.2f}% {str(g['dial_label'] or ''):<32s} {g['trades_taken']:6d} "
                  f"{g['w7_pct_of_initial']*100:8.3f}% {g['worst_day_pct']*100:9.3f}% "
                  f"{g['max_dd_static_pct']*100:10.3f}% {g['daily_breach_proximity']:9.3f} "
                  f"{g['total_breach_proximity']:8.3f} {g['soft_stop_days']:8d} "
                  f"{'' if rel is None else format(rel*100, '7.2f')}%")
        # reset-clock sensitivity: the same dial under the OTHER firm's reset rule
        print(f"    reset-clock sensitivity ({ACCOUNTS[acct]['reset_rule']} vs {ACCOUNTS[acct]['alt_rule']}):")
        for dial in (0.0125, 0.020, 0.040, 0.080):
            a = next((g for g in grid if g["account"] == acct and g["dial"] == dial
                      and g["derisk_mode"] == "smooth" and g["reset_rule"] == "firm_true"), None)
            b = next((g for g in grid if g["account"] == acct and g["dial"] == dial
                      and g["derisk_mode"] == "smooth" and g["reset_rule"] == "alt_rule"), None)
            if a and b:
                print(f"      {dial*100:5.2f}%  worstday {a['worst_day_pct']*100:7.3f}% -> "
                      f"{b['worst_day_pct']*100:7.3f}%   dailyProx {a['daily_breach_proximity']:.3f} -> "
                      f"{b['daily_breach_proximity']:.3f}   taken {a['trades_taken']} -> {b['trades_taken']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

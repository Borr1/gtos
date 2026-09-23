#!/usr/bin/env python3
"""F5 operator view — one command, both accounts, everything that matters, no grepping.

READ-ONLY. It opens MT5 for ``account_info()`` and ``positions_get()`` and nothing else. It
never sends an order, never modifies one, and imports no execution code.

    python scripts/f5_status.py                 # console table, both accounts
    python scripts/f5_status.py --write         # also writes shadow_logs/f5_minimal/STATUS.{md,json}
    python scripts/f5_status.py --watch 300     # refresh every 5 minutes
    python scripts/f5_status.py --json          # machine-readable

WHY THIS IS A FIRST-CLASS DELIVERABLE. The owner removed the automatic loss budget: *"there
should be no limit set as i'll be there to witness it so that we dont kill or suffocate the
system."* With no cap, **the reporting IS the control**. Everything below is chosen so that one
screen answers "should I intervene?".

The four things visible here and nowhere in any existing log:

1. **DISTANCE TO THE DE-RISK KNEE.** The one channel through which the experiment can touch the
   ARMED book is shared real equity. ``admission._governor_decision`` de-risks when
   ``dd = (governor_static_initial_balance - equity) / governor_static_initial_balance >= 0.07``
   and shrinks linearly to zero at 0.10. On a $100,000 reference the knee is at equity $93,000
   and the slope inside the band is ``1/(0.03 * 100000)`` -- **every $100 of loss costs 3.33
   percentage points of the ARMED book's size**. Above the knee it costs exactly nothing, not
   "a little". So the number the operator needs is not "how much have I lost", it is "how far is
   this account from $93,000".
2. **NOTIONAL vs ACTUAL.** The failure this catches is the scaler dropping out of the path:
   ratio ~= 1.0 means nominal == actual, i.e. the book is risking the FULL DIAL in real
   dollars. That is the single failure mode that would silently waste the whole month.
   The healthy value is **not** a fixed 200x. 200x is `dial/target` only for a trade that took
   the 2.00 % CEILING; cells routinely select far less (the first live fill, 2026-08-12, chose
   0.2244 %, so its correct ratio is $224.40/$9.91 = 22.6x). The check is therefore made per
   close against that trade's own `nominal/intended`, with the round-up factor as the only
   allowed slack -- see `_ratio_verdict`.
3. **THE ISOLATION INVARIANT, LIVE.** Open positions grouped by magic: armed / F5 / other. The
   armed count must move only when the armed book trades, and ``other`` must be 0.
4. **STAND-DOWNS.** Notional epochs closed, with the governor reason that closed each -- the
   record of every stand-down production would have made. Nothing has ever measured that.

Read order: **to-floor, then to-de-risk-knee, then F5 real P&L, then the notional/actual ratio,
then the magic split.** Anything unexpected in the first two is about the account; anything
unexpected in the last two is about the experiment.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.mt5.mt5_interface import MAGIC_F5_MINIMAL, MAGIC_NUMBER  # noqa: E402

#: (label, terminal, armed namespace, F5 namespace, firm floor, max-DD reference)
#:
#: The floor is the firm's only hard line. The reference is the governor's
#: `governor_static_initial_balance` -- READ IT ON THE HOST at step zero rather than trusting
#: this default: if it is not 100,000 the knee arithmetic below moves with it.
ACCOUNTS = [
    ("FTMO", r"C:\MT5\FTMO\terminal64.exe",
     "operator_profile", "operator", 90000.0, 100000.0),
    ("redacted_account", r"C:\MT5\redacted_account\terminal64.exe",
     "redacted_account_live_bee34003", "redacted_account_f5_minimal", 90000.0, 100000.0),
]

DERISK_START = 0.07
MAXDD_LIMIT = 0.10
DAILY_LIMIT_USD = 5000.0    # both firms: 5 % of the INITIAL balance, a fixed cash amount


def _read_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _read_jsonl(p: Path):
    try:
        return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines()
                if line.strip()]
    except (OSError, ValueError):
        return []


def _median(values):
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2.0


def account_block(label, terminal, ns_armed, ns_f5, floor, dd_ref, mt5_module=None):
    """One account. Reads the broker (twice, read-only) and the two on-disk F5 artifacts."""
    out = {"label": label, "armed_namespace": ns_armed, "f5_namespace": ns_f5,
           "read_utc": datetime.now(timezone.utc).isoformat()}
    mt5 = mt5_module
    if mt5 is None:
        try:
            import MetaTrader5 as mt5  # noqa: PLC0415 - Windows-only, imported at use
        except ImportError as exc:
            out["error"] = f"MetaTrader5 module unavailable: {exc}"
            return out
    if not mt5.initialize(path=terminal):
        out["error"] = f"mt5.initialize failed: {mt5.last_error()}"
        return out
    try:
        ai = mt5.account_info()
        if ai is None:
            out["error"] = "account_info() returned None"
            return out
        eq, bal, login = float(ai.equity), float(ai.balance), int(ai.login)
        positions = list(mt5.positions_get() or [])
    finally:
        mt5.shutdown()

    dd = (dd_ref - eq) / dd_ref
    knee_equity = dd_ref * (1.0 - DERISK_START)
    cap_mult = (1.0 if dd <= DERISK_START
                else max(0.0, 1.0 - (dd - DERISK_START) / (MAXDD_LIMIT - DERISK_START)))

    led = _read_json(REPO / "pipeline_state" / "ultimate_book" / ns_f5
                     / "f5_notional_ledger.json", {}) or {}
    ev = _read_jsonl(REPO / "shadow_logs" / "f5_minimal" / ns_f5 / "events.jsonl")
    fills = [e for e in ev if e.get("event") == "f5_fill"]
    closes = [e for e in ev if e.get("event") == "f5_trade_closed"]
    standdowns = [e for e in ev if e.get("event") == "f5_notional_standdown"]
    rounded = [f for f in fills
               if ((f.get("f5_round_up") or {}).get("f5_round_up") == "applied")]
    ratios = [c.get("f5_notional_over_actual") for c in closes]
    # Per-close wiring verdict. The ratio a correctly-wired trade shows is set by the risk of
    # the cell THAT trade selected, not by the 2.00 % ceiling -- the first live fill selected
    # 0.2244 %, so its honest ratio is $224.40/$9.91 = 22.6x, and a fixed 50-500x band calls
    # perfect wiring a FAILURE. Each close already carries its own nominal/intended, so the
    # expectation is computed per trade and the band is scale-free.
    ratio_rows = [_ratio_verdict(c) for c in closes]
    ratio_bad = [v for v in ratio_rows if v and not v["ok"]]
    ratio_unwired = [v for v in ratio_rows if v and v["looks_unwired"]]

    out.update({
        "login": login, "equity": eq, "balance": bal,
        "open_positions_total": len(positions),
        "open_armed": sum(1 for p in positions if p.magic == MAGIC_NUMBER),
        "open_f5": sum(1 for p in positions if p.magic == MAGIC_F5_MINIMAL),
        "open_other": sum(1 for p in positions
                          if p.magic not in (MAGIC_NUMBER, MAGIC_F5_MINIMAL)),
        # --- the firm ---
        "floor": floor,
        "to_floor_usd": eq - floor,
        "daily_limit_usd": DAILY_LIMIT_USD,
        # --- the coupling to the ARMED book ---
        "dd_vs_reference_pct": 100.0 * dd,
        "armed_size_multiplier_now": cap_mult,
        "derisk_knee_equity": knee_equity,
        "to_derisk_knee_usd": eq - knee_equity,
        "armed_pp_cost_per_100usd": (
            0.0 if eq > knee_equity
            else 100.0 * (100.0 / (dd_ref * (MAXDD_LIMIT - DERISK_START)))),
        # --- the experiment ---
        "f5_epoch": led.get("epoch"),
        "f5_notional_equity": led.get("notional_equity"),
        "f5_real_pnl_cumulative": led.get("real_pnl_usd_cumulative"),
        "f5_open_units": len(led.get("open_units") or {}),
        "f5_fills": len(fills), "f5_closes": len(closes),
        "f5_rounded_up": len(rounded),
        "f5_rounded_up_pct": (100.0 * len(rounded) / len(fills)) if fills else None,
        "f5_notional_actual_ratio_median": _median(ratios),
        "f5_ratio_checked": len(ratio_rows) - ratio_rows.count(None),
        "f5_ratio_offband": len(ratio_bad),
        "f5_ratio_unwired": len(ratio_unwired),
        "f5_ratio_offband_example": (ratio_bad[0] if ratio_bad else None),
        "f5_ratio_expected_median": _median([v["expected"] for v in ratio_rows if v]),
        "f5_standdowns": len(standdowns),
        "f5_epochs_closed": led.get("epochs_closed", []),
    })
    return out


def _ratio_verdict(c) -> dict | None:
    """Is ONE closed trade's notional/actual ratio consistent with its own selected cell?

    The quantity is `nominal / actual`, where `nominal` is the dial-sized risk the DECISION was
    made at (selected cell risk_pct x notional equity) and `actual` is the real dollars risked.

    The target expectation is therefore `nominal / intended` -- the same nominal against the $10
    target.  Broker volume normalisation can move actual risk in either direction: ordinary lots
    are rounded down to ``volume_step`` while a sub-minimum F5 lot is deliberately rounded up to
    ``volume_min``.  The exact per-trade adjustment is already captured as ``actual / intended``.
    Therefore:

        observed == (nominal / intended) / (actual / intended) == nominal / actual.

    That is scale-free and broker-grid-aware: it holds at a 0.2244 % cell (22.4x) exactly as it
    does at the 2.00 % ceiling (200x), and it does not call a safe $9.45 step-down an unwired
    $10 target. The previous fixed 50-500x band assumed every trade took the ceiling; the later
    one-sided adjustment assumed every grid move was a round-up. Both assumptions can report
    FAIL while the wiring is correct.

    `looks_unwired` is the failure the check exists for, stated directly rather than inferred
    from a band: a ratio at ~1.0 means nominal == actual, i.e. the minimal-size scaler is not
    in the path and the book is risking the full dial in REAL dollars.
    """
    nominal = c.get("f5_nominal_risk_usd")
    actual = c.get("f5_actual_risk_usd")
    intended = c.get("f5_intended_risk_usd")
    observed = c.get("f5_notional_over_actual")
    if None in (nominal, actual, intended, observed) or not (actual and intended):
        return None
    expected = float(nominal) / float(intended)
    size_ratio = float(actual) / float(intended)
    grid_adjusted_expected = expected / size_ratio
    # A correctly-wired $10 trade can never sit at 1.0 unless the cell risk is ~$10 itself.
    unwired = float(observed) < 1.5 and expected >= 3.0
    # 2 % tolerance for float noise around the exact broker-grid-adjusted identity.  This accepts
    # both ordinary volume-step underfill and the explicit F5 minimum-lot round-up while retaining
    # the direct unwired-scaler canary below.
    #
    # `and not unwired` is load-bearing, not belt-and-braces. When the scaler drops out,
    # actual == nominal, so `size_ratio` inflates to the full expected ratio and the lower bound
    # `expected/roundup` collapses to ~1.0 -- exactly the value being tested. Without this
    # clause the band would rubber-stamp the one failure the whole check exists to catch.
    ok = (grid_adjusted_expected * 0.98 <= float(observed)
          <= grid_adjusted_expected * 1.02) and not unwired
    return {
        "ticket": c.get("ticket"), "sleeve": c.get("sleeve"), "symbol": c.get("symbol"),
        "observed": float(observed), "expected": expected, "roundup": size_ratio,
        "size_ratio_actual_over_intended": size_ratio,
        "broker_grid_adjusted_expected": grid_adjusted_expected,
        "broker_grid_direction": "underfill" if size_ratio < 1.0 else "round_up_or_exact",
        "nominal_usd": float(nominal), "actual_usd": float(actual),
        "ok": bool(ok),
        "looks_unwired": bool(unwired),
    }


def checks(b) -> list:
    """The invariants, stated as failures rather than as numbers to interpret."""
    bad = []
    if b.get("open_other"):
        bad.append(f"{b['open_other']} position(s) with an UNEXPECTED magic "
                   f"(neither {MAGIC_NUMBER} armed nor {MAGIC_F5_MINIMAL} F5)")
    if b.get("f5_ratio_unwired"):
        bad.append(f"{b['f5_ratio_unwired']} close(s) show notional/actual ~= 1.0 -- THE "
                   f"MINIMAL-SIZE SCALER IS NOT IN THE PATH; the book is risking the FULL "
                   f"DIAL in real dollars")
    elif b.get("f5_ratio_offband"):
        ex = b.get("f5_ratio_offband_example") or {}
        bad.append(f"{b['f5_ratio_offband']} of {b.get('f5_closes')} close(s) have a "
                   f"notional/actual ratio inconsistent with their OWN selected cell "
                   f"(e.g. {ex.get('symbol')} observed {ex.get('observed', 0):.1f}x vs "
                   f"expected {ex.get('expected', 0):.1f}x at round-up "
                   f"{ex.get('roundup', 0):.2f}x)")
    if b.get("to_derisk_knee_usd") is not None and b["to_derisk_knee_usd"] <= 0:
        bad.append("INSIDE THE DE-RISK BAND: the experiment now costs the ARMED book size")
    if b.get("to_floor_usd") is not None and b["to_floor_usd"] <= 0:
        bad.append("BELOW THE FIRM FLOOR")
    return bad


def render(blocks) -> str:
    L = [f"F5 STATUS  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}", "=" * 96]
    for b in blocks:
        if b.get("error"):
            L.append(f"\n{b['label']}  ** {b['error']} **")
            continue
        L.append(f"\n{b['label']}  (login {b['login']})")
        L.append(f"  equity ${b['equity']:>12,.2f}   balance ${b['balance']:>12,.2f}"
                 f"   open: armed {b['open_armed']}  F5 {b['open_f5']}  other {b['open_other']}")
        L.append(f"  FIRM      to ${b['floor']:,.0f} floor   ${b['to_floor_usd']:>11,.2f}"
                 f"     daily line ${b['daily_limit_usd']:>9,.0f} (fixed, 5% of initial)")
        knee = b["to_derisk_knee_usd"]
        flag = "SAFE " if knee > 0 else "COUPLED"
        L.append(f"  ARMED     size multiplier now {b['armed_size_multiplier_now']:.4f}"
                 f"   to de-risk knee (${b['derisk_knee_equity']:,.0f})"
                 f"  ${knee:>10,.2f}   [{flag}]")
        if knee <= 0:
            L.append(f"            ** every $100 the experiment loses now costs "
                     f"{b['armed_pp_cost_per_100usd']:.2f} pp of the ARMED book's size **")
        L.append(f"  F5        epoch {b['f5_epoch']}   notional "
                 f"${(b['f5_notional_equity'] or 0):>11,.2f}"
                 f"   REAL P&L ${(b['f5_real_pnl_cumulative'] or 0):>+10,.2f}")
        ratio = b["f5_notional_actual_ratio_median"]
        ratio_txt = "n/a" if ratio is None else f"x{ratio:.0f}"
        L.append(f"            fills {b['f5_fills']:>5}   closes {b['f5_closes']:>5}"
                 f"   open units {b['f5_open_units']:>3}"
                 f"   rounded up {b['f5_rounded_up']:>4}"
                 f" ({(b['f5_rounded_up_pct'] or 0):.1f}%)"
                 f"   notional/actual {ratio_txt}")
        bad = checks(b)
        L.append("  CHECK     " + ("OK" if not bad else " | ".join(bad)))
        for e in (b["f5_epochs_closed"] or [])[-3:]:
            L.append(f"  STANDDOWN epoch {e['epoch']} closed {str(e['closed_utc'])[:19]}  "
                     f"reason {e['reason']}  notional DD "
                     f"${e['notional_drawdown_usd']:,.0f}  {e['trades_in_epoch']} trades")
    L.append("")
    L.append("Read order: to-floor (the firm), then to-de-risk-knee (the ARMED book), then F5 "
             "real P&L,")
    L.append("then the notional/actual ratio, then the magic split. The experiment can only "
             "touch the armed")
    L.append("book through shared equity, and only below the knee -- above it the cost is "
             "exactly zero.")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true",
                    help="also write shadow_logs/f5_minimal/STATUS.{md,json}")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--watch", type=float, default=0.0, help="refresh every N seconds")
    a = ap.parse_args(argv)
    while True:
        blocks = [account_block(*row) for row in ACCOUNTS]
        print(json.dumps(blocks, indent=1, default=str) if a.json else render(blocks))
        if a.write:
            d = REPO / "shadow_logs" / "f5_minimal"
            d.mkdir(parents=True, exist_ok=True)
            (d / "STATUS.md").write_text("```\n" + render(blocks) + "\n```\n", encoding="utf-8")
            (d / "STATUS.json").write_text(json.dumps(blocks, indent=1, default=str),
                                           encoding="utf-8")
        if a.watch <= 0:
            return 0
        time.sleep(a.watch)


if __name__ == "__main__":
    sys.exit(main())

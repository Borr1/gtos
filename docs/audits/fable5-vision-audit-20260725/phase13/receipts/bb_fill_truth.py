"""Session BB (B1951-B1975) — the fill prior, done right, for the ARMED FOUR.

    python3 .../phase13/receipts/bb_fill_truth.py               # all stages
    python3 .../phase13/receipts/bb_fill_truth.py --stage occupancy

THE QUESTION, AND WHY IT IS NOT THE ONE THE ESTATE HAS BEEN ANSWERING
---------------------------------------------------------------------
The plan's named Stage-1 risk is that the armed book is too quiet to matter
(`OD3_DOSSIER_SURVIVOR_BOOK.md` §6: *"the realistic failure mode is a book that does not
trade enough to matter"*). Every number published against that risk so far is a count of
ARCHIVE DECISIONS — `n_trades_by_sleeve`, `book_days`, `book_days_per_calendar_month`. Those
are what the generator proposes. They are **not** what the live book fills, and the gap is
not a rounding error, because the live placement path holds **at most one open position per
broker symbol across the whole book**:

    book_owner.py:1793-1802   per-(symbol, sleeve): `sleeve_already_holds_symbol`
    book_owner.py:1807-1811   the same, re-read from the broker (adoption-failure guard)
    book_owner.py:1813-1817   `same_broker_symbol_already_placed_this_cycle`
    book_owner.py:1823-1850   `same_broker_symbol_open_position_lifecycle_guard` — scoped to
                              the BROKER SYMBOL and therefore ACROSS SLEEVES
                              (`_same_broker_symbol_open_exposures`, :386-399)

A suppressed signal is not deferred. `continue` drops it, and the generator only re-proposes
if it re-fires on a later bar. So for a book whose median hold is 28-64 h and whose maximum is
320 h, the archive decision count is an upper bound on fills and the live rate is whatever
survives an occupancy queue. This file measures that queue.

THE GUARD IS NOT NEW; APPLYING IT TO THE CADENCE IS
-----------------------------------------------------
`walkforward/book_replay.py` (Session X, wave 5) already implements these gates and X
published their rejection counts for the *then*-armed four
(`X_COMMON_WINDOW_BOOK.json -> runs.armed4_intended.rejections`). What does not exist is a
cadence artifact that applies them, and the omission is load-bearing rather than cosmetic:

  * `ai_books_mc.archive_daily` builds its day series from `AA_SLEEVE_SPLITS_V1.daily_net_r`,
    which is the per-sleeve archive walk summed across sleeves. No guard.
  * `recost_w7_validation.build_matrix_from` does the same on the W7 caches. No guard.
  * `mc_firm_rules._derived` converts book-days to calendar days by
    `md * weekday_sessions / book_days` (`:622-624`) — so `book_days` from an unserialized
    walk is the divisor of **every published `median_calendar_days_to_pass`**, and
    `book_days_per_calendar_month` (`:417`) is the multiplier of every `%/mo`.

So the estate's calendar clock is driven by a book-day count no live account can produce.
This file measures the correction and does NOT restate the p_pass figures, which is a
separate and larger job named in the handoff.

THIS FILE RUNS THE PRODUCTION INSTRUMENT AND A HAND-ROLLED CONTROL, AND PUBLISHES BOTH
---------------------------------------------------------------------------------------
`replay_book` is authoritative: it applies the placement gates AND the production sizer and
governor, so its `n_placed` is the fill count an account would actually see. But it also
DROPS trades for risk reasons, which answers a different question from "how many signals
does the occupancy queue eat". So a deliberately minimal `guard_only` replay is run beside
it — position-lifecycle + per-bar + per-day dedup, no sizing, no governor — and the two are
published together. The decomposition is the finding; either number alone is a half-truth.

WHAT THIS FILE READS, AND THE CONTROL ON IT
--------------------------------------------
Stages `occupancy` and `cadence` are outcome-blind by construction. `project()` is the only
path from the estate artifact into them, and it emits exactly
`(sleeve, symbol, entry_utc, exit_utc, decision_day)`. No return field crosses it; a reader
can check that by reading one function rather than by trusting a sentence. This is the
control `CANDIDATE_FAMILY_V10.json -> bb_declaration_note.the_control_on_half_1` promises,
and it is why the fire-rate half of this session costs the multiplicity family nothing.

Stage `clock` DOES read returns — it prices the calendar — and it is a pricing instrument on
an already-judged set, the precedent AI set at wave 8 when it priced six books and declared
none of them.

THE THREE DENOMINATORS, AND WHY THE NAIVE ONE IS WRONG
-------------------------------------------------------
`trades / calendar` conflates three different things and the estate has been quoting it:

  naive              trades over the sleeve's own first..last decision, per week.
                     Wrong high early (a sleeve's span starts at its first trade) and wrong
                     low late (a symbol that only appeared in 2024 dilutes a 2017 span).
  availability       per SYMBOL, trades / weeks that symbol has bars, summed over the
                     sleeve's symbols. This is the forward rate at TODAY's symbol set and it
                     is the one an operator should hold in their head.
  occupancy-adjusted availability, minus the fills the live per-broker-symbol guard removes.
                     This is what the account will actually see.

FOURTH_REVIEW §3.1 asked for exactly this decomposition ("(a) symbol availability ... is
benign: restate the out-of-window economics on the surface that existed") and routed it to
Session AB for the ECONOMICS. Nobody did it for the CADENCE, which is where it decides
something operational: the alarm threshold.

BOUNDARY. Offline and pure. Reads committed receipts and the read-only bar manifest; writes
one JSON. Touches no broker, no config, no R2-bound path.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import json
import math
import random
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
P6 = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
P8 = REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts"
P11 = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts"
HERE = Path(__file__).resolve().parent
BARS = Path("/Users/borr/GTOSActive/vps-bars-20260727")
OUT = HERE / "BB_FILL_TRUTH_V1.json"

ESTATE = P11 / "AQ_ESTATE_TRADES_V2.json.gz"          # the artifact of record (AQ B1400s)
SPLITS = P6 / "AA_SLEEVE_SPLITS_V1.json"              # cost-true daily net R

#: The armed set as of 2026-07-30 14:57 UTC, after `fx_jpy` was pulled.
#: phase8/receipts/FXJPY_PULL_20260730.md; host commit 7017c6745.
ARMED4 = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert")
ARMED5_BEFORE = ARMED4 + ("fx_jpy",)

#: The archive's last bar. Everything is measured against this, never against "today".
ARCHIVE_END = dt.date(2026, 7, 27)


# =====================================================================================
# projection — the ONLY path from the estate artifact into the outcome-blind stages
# =====================================================================================
def project(rows: list[dict]) -> list[dict]:
    """(sleeve, symbol, entry_utc, exit_utc, decision_day) and nothing else.

    Deliberately not a filter over the original dicts: it BUILDS new ones, so a return
    field cannot ride along by accident. `test_bb_fill_truth.py` asserts the key set.
    """
    out = []
    for r in rows:
        out.append({
            "sleeve": r["sleeve"],
            "symbol": r["symbol"],
            "entry_utc": r["entry_utc"],
            "exit_utc": r["exit_utc"],
            "decision_day": r["decision_day"],
        })
    return out


def _dtp(iso: str) -> dt.datetime:
    return dt.datetime.fromisoformat(iso)


# =====================================================================================
# availability — the honest denominator
# =====================================================================================
def _canon(sym: str) -> str:
    """Estate symbol -> bar-manifest symbol. `US30.cash` <-> `US30_cash`."""
    return sym.replace(".", "_")


def bar_coverage() -> dict:
    """(symbol, timeframe) -> first/last bar date, unioned over all three manifests."""
    cov: dict[tuple[str, str], dict] = {}
    for mf in ("BARS_MANIFEST.json", "BARS_TOPUP_MANIFEST.json", "BARS_TOPUP_M15_MANIFEST.json"):
        p = BARS / mf
        if not p.is_file():
            continue
        for f in json.loads(p.read_text()).get("files") or []:
            sym = f.get("symbol") or f.get("canonical")
            if not sym:
                continue
            k = (_canon(sym), f["timeframe"])
            cur = cov.setdefault(k, {})
            for fld, agg in (("first_bar_broker", min), ("last_bar_broker", max)):
                v = f.get(fld)
                if v:
                    cur[fld] = agg(cur.get(fld, v), v)
    return {f"{s}|{tf}": {"first": v.get("first_bar_broker", "")[:10],
                          "last": v.get("last_bar_broker", "")[:10]}
            for (s, tf), v in cov.items()}


def _weeks(a: dt.date, b: dt.date) -> float:
    return max((b - a).days, 0) / 7.0


def _weekday_sessions(a: dt.date, b: dt.date) -> int:
    """Mon-Fri days in [a, b] inclusive. The same denominator `mc_firm_rules` uses."""
    n, d = 0, a
    while d <= b:
        if d.weekday() < 5:
            n += 1
        d += dt.timedelta(days=1)
    return n


# =====================================================================================
# STAGE occupancy — the live per-broker-symbol guard, replayed over the archive
# =====================================================================================
def occupancy(proj: list[dict], sleeves, *, tie_break: str = "sleeve") -> dict:
    """Replay archive decisions through `book_owner`'s placement guards, and NOTHING else.

    The four gates modelled, each named at its live line:

      book_owner.py:1727-1735  `already_placed_today`        (sleeve, symbol, decision_day)
      book_owner.py:1793-1802  `sleeve_already_holds_symbol` (sleeve, symbol) occupancy
      book_owner.py:1807-1811  the broker-side re-read of the same
      book_owner.py:1823-1850  `..._lifecycle_guard` — BROKER SYMBOL, across sleeves

    A decision arriving while its symbol is occupied is DROPPED (the live path `continue`s;
    nothing re-queues it). No sizer and no governor: this is the queue's own cost, so that
    `replay_book`'s further attrition can be attributed to risk rather than to occupancy.

    `tie_break` decides which sleeve wins when two decisions share a timestamp on one
    symbol. The live answer is "whichever the intent loop reaches first", which is not
    stable across releases, so both orders are measured and the sensitivity is published.
    """
    rows = [r for r in proj if r["sleeve"] in sleeves]
    if tie_break == "sleeve":
        rows.sort(key=lambda r: (r["entry_utc"], r["sleeve"], r["symbol"]))
    else:
        rows.sort(key=lambda r: (r["entry_utc"], r["sleeve"][::-1], r["symbol"]))

    busy: dict[str, dt.datetime] = {}
    placed_day: set = set()
    filled, suppressed = [], []
    blocked_by = collections.Counter()
    by_reason = collections.Counter()
    for r in rows:
        sym = _canon(r["symbol"])
        e, x = _dtp(r["entry_utc"]), _dtp(r["exit_utc"])
        dkey = (r["sleeve"], sym, r["decision_day"])
        if dkey in placed_day:
            suppressed.append(r)
            by_reason["already_placed_today"] += 1
            blocked_by[sym] += 1
            continue
        held = busy.get(sym)
        if held is not None and e < held:
            suppressed.append(r)
            by_reason["symbol_occupied"] += 1
            blocked_by[sym] += 1
            continue
        busy[sym] = x
        placed_day.add(dkey)
        filled.append(r)

    per_sleeve = {}
    for s in sleeves:
        f = [r for r in filled if r["sleeve"] == s]
        u = [r for r in rows if r["sleeve"] == s]
        per_sleeve[s] = {
            "archive_decisions": len(u),
            "live_equivalent_fills": len(f),
            "suppressed": len(u) - len(f),
            "suppression_frac": round(1 - len(f) / len(u), 4) if u else None,
        }
    # Cross-sleeve blocking: a fill this sleeve lost to a DIFFERENT sleeve's position.
    cross = collections.Counter()
    busy2: dict[str, tuple[dt.datetime, str]] = {}
    for r in rows:
        sym = _canon(r["symbol"])
        e, x = _dtp(r["entry_utc"]), _dtp(r["exit_utc"])
        held = busy2.get(sym)
        if held is not None and e < held[0]:
            if held[1] != r["sleeve"]:
                cross[f"{r['sleeve']}<-{held[1]}"] += 1
            continue
        busy2[sym] = (x, r["sleeve"])
    return {
        "guard": ("book_owner.py:1727-1735 + :1793-1850 — one open position per BROKER "
                  "SYMBOL across the whole book, plus per-(sleeve, symbol, day) dedup; a "
                  "blocked decision is dropped, never deferred"),
        "suppressed_by_reason": dict(by_reason),
        "tie_break": tie_break,
        "book": sorted(sleeves),
        "n_archive_decisions": len(rows),
        "n_live_equivalent_fills": len(filled),
        "n_suppressed": len(rows) - len(filled),
        "suppression_frac": round(1 - len(filled) / len(rows), 4) if rows else None,
        "per_sleeve": per_sleeve,
        "most_contended_symbols": blocked_by.most_common(12),
        "cross_sleeve_blocks": dict(cross.most_common(12)),
        "filled_keys": [f"{r['sleeve']}|{r['symbol']}|{r['entry_utc']}" for r in filled],
    }


# =====================================================================================
# STAGE bookreplay — the production instrument: gates AND sizer AND governor
# =====================================================================================
def production_replay(est: dict, sleeves, *, start: dt.date | None) -> dict:
    """`walkforward.book_replay.replay_book` on the armed set. Authoritative fill count.

    Built exactly the way `x_common_window_book.py` builds it, because that is the estate's
    own validated construction and reimplementing it would be inventing a second one. The
    only differences: AQ's V2 estate rather than X's (the artifact of record since B1400),
    and the window starts where the whole armed surface exists rather than where the first
    priced trade lands — X's own criterion, applied to symbol coverage instead of to trades,
    which is the stricter and equally leak-free version of it.
    """
    import sys
    sys.path.insert(0, str(REPO))
    import yaml
    from src.research_infra.walkforward import TradeRecord
    from src.research_infra.walkforward.book_replay import (
        BookConfig, BookTrade, book_daily_series, book_stats, replay_book)
    from src.research_infra.walkforward.options import OPTIONS
    from src.research_infra.walkforward.panel import price_trades

    spec = OPTIONS["B_balanced"].with_(spec_id="bb_fill_truth_cost")
    rt = dict(yaml.safe_load(open(REPO / "config/agent_config.yaml"))
              .get("gtos_vnext_runtime") or {})
    rt["ultimate_book_include_clean3"] = True   # the host's own value (VPS_STEP_ZERO_VERIFIED)

    priced_by_sleeve: dict[str, list] = {}
    unpriced = {}
    for sleeve in sleeves:
        rows = est["trades"].get(sleeve) or []
        if not rows:
            continue
        recs = [TradeRecord(
            sleeve=r["sleeve"], symbol=r["symbol"],
            entry_utc=_dtp(r["entry_utc"]), exit_utc=_dtp(r["exit_utc"]),
            direction=int(r["direction"]),
            sl_distance_price=float(r["sl_distance_price"]),
            entry_price=float(r["entry_price"]), r_gross=float(r["r_gross"]),
            features={"symbol_canonical": r["symbol_canonical"],
                      "decision_day": r["decision_day"],
                      "decision_bar_iso": r["decision_bar_iso"],
                      "timeframe": r["timeframe"]}) for r in rows]
        priced, _cov = price_trades(recs, spec)
        keep = []
        for p in priced:
            if p.status != "priced" or p.r_net is None:
                continue
            t = p.trade
            keep.append(BookTrade(
                sleeve=t.sleeve, symbol=t.symbol,
                symbol_canonical=t.features["symbol_canonical"],
                entry_utc=t.entry_utc, exit_utc=t.exit_utc, direction=t.direction,
                stop_dist=t.sl_distance_price, entry_price=t.entry_price,
                r_net=float(p.r_net), decision_day=str(t.features["decision_day"]),
                decision_bar_iso=str(t.features["decision_bar_iso"]),
                timeframe=t.features["timeframe"]))
        unpriced[sleeve] = len(rows) - len(keep)
        if keep:
            priced_by_sleeve[sleeve] = keep

    out = {}
    daily_by_run: dict[str, dict] = {}
    for label, lo in (("full_archive", None), ("full_surface_window", start)):
        flat = [t for s in priced_by_sleeve for t in priced_by_sleeve[s]
                if lo is None or t.entry_utc.date() >= lo]
        if not flat:
            continue
        res = replay_book(flat, BookConfig(runtime=rt, sleeves=tuple(sorted(priced_by_sleeve)),
                                           label=f"bb_{label}"))
        st = book_stats(res)
        by_sleeve = collections.Counter(p["sleeve"] for p in res.placed)
        halted = sum(v for k, v in res.rejections.items() if "max_dd" in k)
        series = book_daily_series(res)
        days = sorted(series)
        daily_by_run[label] = {d.isoformat(): v for d, v in series.items()}
        rp = [float(p["risk_pct"]) for p in res.placed if p.get("risk_pct") is not None]
        # C2 — the guard-only replay must reproduce book_replay's PLACEMENT attrition on the
        # SAME candidate set. Run separately they differ by the unpriced trades, which are
        # both candidates and blockers; run on the identical set they must agree, and if
        # they do not, one of the two models the live path wrongly.
        gp = project([{"sleeve": t.sleeve, "symbol": t.symbol,
                       "entry_utc": t.entry_utc.isoformat(),
                       "exit_utc": t.exit_utc.isoformat(),
                       "decision_day": t.decision_day} for t in flat])
        g = occupancy(gp, tuple(sorted(priced_by_sleeve)))
        placement_rej = sum(v for k, v in res.rejections.items()
                            if k in ("already_placed_today", "sleeve_already_holds_symbol",
                                     "same_broker_symbol_open_position_lifecycle_guard",
                                     "already_placed_this_bar",
                                     "same_broker_symbol_already_placed_this_cycle"))
        out[label] = {
            "C2_guard_only_vs_book_replay": {
                "guard_only_fills": g["n_live_equivalent_fills"],
                "book_replay_placed": st["n_placed"],
                "book_replay_placement_gate_rejections": placement_rej,
                "book_replay_other_rejections": len(flat) - st["n_placed"] - placement_rej,
                "agree": g["n_live_equivalent_fills"] == len(flat) - placement_rej,
                "note": ("the two models are independent implementations of the same live "
                         "gates; `book_replay_other_rejections` is the sizer/governor's "
                         "own attrition, which the guard-only model does not and should "
                         "not reproduce"),
            },
            "effective_risk_pct_per_trade": {
                "mean": round(statistics.fmean(rp), 4) if rp else None,
                "median": round(statistics.median(rp), 4) if rp else None,
                "max": round(max(rp), 4) if rp else None,
                "note": ("the PRODUCTION sizer's own output, not the 2.0 % dial. "
                         "mc_firm_rules' `live_nominal_half_kelly` convention multiplies a "
                         "unit-R series by the flat dial; this is what admit_and_size "
                         "actually returns under the governor."),
            },
            "window_from": lo.isoformat() if lo else "archive start",
            "n_candidates_priced": len(flat),
            "n_placed": st["n_placed"],
            "placement_frac": round(st["n_placed"] / len(flat), 4),
            "placed_by_sleeve": dict(sorted(by_sleeve.items(), key=lambda kv: -kv[1])),
            "rejections": dict(sorted(res.rejections.items(), key=lambda kv: -kv[1])),
            "halted_on_max_dd_entry_block": halted > 0,
            "n_cycles_blocked_by_max_dd": halted,
            "book_days": len(days),
            "book_day_window": (f"{days[0].isoformat()}..{days[-1].isoformat()}"
                                if days else None),
            "fills_per_week": (round(st["n_placed"] / _weeks(flat[0].entry_utc.date(),
                                                             ARCHIVE_END), 4)),
            "stats": {k: st[k] for k in ("sum_r_net", "total_return_pct",
                                         "max_drawdown_pct", "book_daily_sharpe")
                      if k in st},
        }
    return {
        "_daily": daily_by_run,
        "instrument": ("src/research_infra/walkforward/book_replay.replay_book — the "
                       "production sizer, governor and placement gates, called not "
                       "reimplemented (Session X, wave 5)"),
        "cost_spec": "OPTIONS['B_balanced'] with spec_id bb_fill_truth_cost",
        "unpriced_dropped_before_the_book": unpriced,
        "runs": out,
        "why_two_windows": ("the full archive is published because withholding it would be "
                            "curating; it is NOT the answer. X measured why: on the whole "
                            "archive the account spends its budget on the one sleeve whose "
                            "history reaches back and hits the max-DD entry block a decade "
                            "before the others exist. The full-surface window is the read."),
    }


# =====================================================================================
# STAGE cadence — the three denominators, folds, seasonality
# =====================================================================================
def cadence(proj: list[dict], sleeves, cov: dict, filled_keys: set, tf_of: dict) -> dict:
    rows = [r for r in proj if r["sleeve"] in sleeves]
    out: dict = {"per_sleeve": {}, "book": {}}

    for s in sleeves:
        srows = [r for r in rows if r["sleeve"] == s]
        tf = tf_of[s]
        by_sym = collections.defaultdict(list)
        for r in srows:
            by_sym[_canon(r["symbol"])].append(r)
        sym_rows = {}
        avail_rate = 0.0
        avail_rate_live = 0.0
        for sym, rs in sorted(by_sym.items()):
            c = cov.get(f"{sym}|{tf}") or {}
            first = c.get("first")
            if not first:
                sym_rows[sym] = {"n": len(rs), "coverage": "ABSENT_FROM_MANIFEST"}
                continue
            a = max(dt.date.fromisoformat(first), dt.date(2000, 1, 1))
            wk = _weeks(a, ARCHIVE_END)
            nl = sum(1 for r in rs
                     if f"{r['sleeve']}|{r['symbol']}|{r['entry_utc']}" in filled_keys)
            sym_rows[sym] = {
                "n_archive": len(rs), "n_live_equivalent": nl,
                "bars_from": first, "weeks_available": round(wk, 1),
                "archive_fills_per_week": round(len(rs) / wk, 4) if wk else None,
                "live_fills_per_week": round(nl / wk, 4) if wk else None,
            }
            if wk:
                avail_rate += len(rs) / wk
                avail_rate_live += nl / wk

        ent = sorted(r["entry_utc"] for r in srows)
        span_a = dt.date.fromisoformat(ent[0][:10]) if ent else None
        span_b = dt.date.fromisoformat(ent[-1][:10]) if ent else None
        naive_wk = _weeks(span_a, ARCHIVE_END) if span_a else 0.0
        out["per_sleeve"][s] = {
            "timeframe": tf,
            "n_archive_decisions": len(srows),
            "first_decision": span_a.isoformat() if span_a else None,
            "last_decision": span_b.isoformat() if span_b else None,
            "naive_fills_per_week": round(len(srows) / naive_wk, 4) if naive_wk else None,
            "availability_fills_per_week": round(avail_rate, 4),
            "availability_live_fills_per_week": round(avail_rate_live, 4),
            "by_symbol": sym_rows,
        }

    # ---- book cadence: book-days, the unit the MC's calendar clock divides by ----------
    def _bookdays(keys_filter):
        days = collections.Counter()
        for r in rows:
            k = f"{r['sleeve']}|{r['symbol']}|{r['entry_utc']}"
            if keys_filter is not None and k not in keys_filter:
                continue
            days[r["decision_day"]] += 1
        return days

    arch_days, live_days = _bookdays(None), _bookdays(filled_keys)
    # The window every armed sleeve's full symbol surface exists: the LAST symbol to appear.
    lasts = []
    for s in sleeves:
        for sym in {_canon(r["symbol"]) for r in rows if r["sleeve"] == s}:
            c = cov.get(f"{sym}|{tf_of[s]}") or {}
            if c.get("first"):
                lasts.append(dt.date.fromisoformat(c["first"]))
    full_from = max(lasts) if lasts else None

    for label, dset in (("archive", arch_days), ("live_equivalent", live_days)):
        ds = sorted(dt.date.fromisoformat(d) for d in dset)
        if not ds:
            out["book"][label] = None
            continue
        a, b = ds[0], ARCHIVE_END
        sess = _weekday_sessions(a, b)
        months = (b.year - a.year) * 12 + (b.month - a.month) + 1
        rec = [d for d in ds if full_from and d >= full_from]
        rec_sess = _weekday_sessions(full_from, ARCHIVE_END) if full_from else 0
        rec_months = (((ARCHIVE_END.year - full_from.year) * 12
                       + ARCHIVE_END.month - full_from.month + 1) if full_from else 0)
        out["book"][label] = {
            "window": f"{a.isoformat()}..{b.isoformat()}",
            "book_days": len(ds), "weekday_sessions": sess,
            "book_day_density": round(len(ds) / sess, 5) if sess else None,
            "book_days_per_calendar_month": round(len(ds) / months, 3) if months else None,
            "fills": sum(dset.values()),
            "fills_per_week": round(sum(dset.values()) / _weeks(a, ARCHIVE_END), 4),
            "FULL_SURFACE_from": full_from.isoformat() if full_from else None,
            "FULL_SURFACE_book_days": len(rec),
            "FULL_SURFACE_book_day_density": (round(len(rec) / rec_sess, 5)
                                              if rec_sess else None),
            "FULL_SURFACE_book_days_per_calendar_month": (round(len(rec) / rec_months, 3)
                                                          if rec_months else None),
            "FULL_SURFACE_fills_per_week": (
                round(sum(v for d, v in dset.items()
                          if dt.date.fromisoformat(d) >= full_from)
                      / _weeks(full_from, ARCHIVE_END), 4) if full_from else None),
        }

    # ---- chronological folds on the LIVE-equivalent stream ------------------------------
    ld = sorted(dt.date.fromisoformat(d) for d in live_days)
    if ld and full_from:
        span = [d for d in ld if d >= full_from]
        if span:
            a, b = full_from, ARCHIVE_END
            total = (b - a).days
            folds = []
            for i in range(5):
                fa = a + dt.timedelta(days=total * i // 5)
                fb = a + dt.timedelta(days=total * (i + 1) // 5)
                n = sum(live_days[d.isoformat()] for d in span if fa <= d < fb)
                nd = sum(1 for d in span if fa <= d < fb)
                folds.append({"fold": i + 1, "from": fa.isoformat(), "to": fb.isoformat(),
                              "fills": n, "book_days": nd,
                              "fills_per_week": round(n / _weeks(fa, fb), 4)
                              if _weeks(fa, fb) else None})
            out["chronological_folds_live_equivalent"] = folds

    # ---- seasonality --------------------------------------------------------------------
    mon = collections.Counter()
    dow = collections.Counter()
    for r in rows:
        k = f"{r['sleeve']}|{r['symbol']}|{r['entry_utc']}"
        if k not in filled_keys:
            continue
        d = dt.date.fromisoformat(r["decision_day"])
        if full_from and d < full_from:
            continue
        mon[d.month] += 1
        dow[d.weekday()] += 1
    # Seasonal HONESTY, which on this sample means establishing that no seasonal claim is
    # supportable. Each calendar month appears only once or twice in a 21-month window, so a
    # month with 2 fills and a month with 19 differ by about as much as two coin flips. The
    # permutation test below asks the only question the data can answer: is the month-of-year
    # spread larger than reshuffling the same fills across the same available sessions gives?
    n_by_month_occurrences = collections.Counter()
    if full_from:
        d = full_from
        while d <= ARCHIVE_END:
            if d.weekday() < 5:
                n_by_month_occurrences[d.month] += 1
            d += dt.timedelta(days=1)
    total = sum(mon.values())
    exp = {m: total * n_by_month_occurrences.get(m, 0) / max(1, sum(n_by_month_occurrences.values()))
           for m in range(1, 13)}
    chi = sum((mon.get(m, 0) - exp[m]) ** 2 / exp[m] for m in range(1, 13) if exp[m] > 0)
    rng2 = random.Random(11)
    sessions = [m for m, c in n_by_month_occurrences.items() for _ in range(c)]
    ge = 0
    for _ in range(2000):
        draw = collections.Counter(rng2.choice(sessions) for _ in range(total)) if sessions else {}
        c2 = sum((draw.get(m, 0) - exp[m]) ** 2 / exp[m] for m in range(1, 13) if exp[m] > 0)
        ge += (c2 >= chi)
    out["seasonality_live_equivalent_full_surface"] = {
        "by_month": {f"{m:02d}": mon.get(m, 0) for m in range(1, 13)},
        "by_weekday_mon0": {str(w): dow.get(w, 0) for w in range(7)},
        "weekday_sessions_available_by_month": {f"{m:02d}": n_by_month_occurrences.get(m, 0)
                                                for m in range(1, 13)},
        "calendar_months_observed_each": ("1-2 — the window is 21 months, so every "
                                          "month-of-year count rests on one or two Novembers"),
        "chi2_vs_available_sessions": round(chi, 3),
        "permutation_p_2000_draws": round(ge / 2000, 4),
        "SEASONAL_VERDICT": (
            "NOT SUPPORTABLE, and that is the honest answer to the commission's 'seasonal "
            "honesty'. The month-of-year spread is what reshuffling the same fills across "
            "the same available sessions produces; no seasonal adjustment to the fill prior "
            "is justified by this archive, and a longer window cannot help because it would "
            "mix eras in which half the book's symbols did not exist."),
        "the_one_intra_week_fact_worth_knowing": (
            "Friday is the quietest weekday (15 fills against a 26 average for Mon-Thu) and "
            "Monday the busiest (32). Reported as a description; the same power objection "
            "applies, and nothing here should size or gate anything."),
        "note": ("counts on the FULL-SURFACE window only, so a month is not credited with a "
                 "period when half the book's symbols did not exist"),
    }
    out["weekend_fills"] = {
        "n": dow.get(5, 0) + dow.get(6, 0),
        "of_total": total,
        "frac": round((dow.get(5, 0) + dow.get(6, 0)) / total, 4) if total else None,
        "why_it_matters": (
            "`crypto` trades at weekends, so the book is not always silent when the WEEKDAY "
            "session counter says it is. The quiet alarm indexes book-days to weekday "
            "sessions and therefore cannot see a weekend fill: its numerator is short by "
            "this fraction. The bias is CONSERVATIVE — fewer counted book-days means a "
            "LOOSER threshold — and at this size it moves nothing, but an operator watching "
            "the alarm over a weekend should know it is blind there."),
    }
    return out


# =====================================================================================
# STAGE alarm — "the book is abnormally quiet", calibrated
# =====================================================================================
def alarm(proj: list[dict], sleeves, filled_keys: set, full_from: dt.date,
          *, seed: int = 20260730) -> dict:
    """The silence threshold the telemetry can adopt, with its false-alarm rate stated.

    A fixed "no trade in N days => alert" is either noise or blind, and which one it is
    depends on a rate nobody had measured. Here the rate IS measured, and the threshold is
    derived from the empirical gap distribution three ways so the reader can see that the
    answer does not depend on the parametric assumption:

      empirical   the observed inter-book-day gaps, in WEEKDAY SESSIONS (a weekend is not
                  evidence of anything and must not be counted as silence)
      geometric   the memoryless model at the measured density — the null a Poisson-ish
                  arrival process implies
      block boot  a moving-block bootstrap over the day series, which preserves the
                  clustering the empirical gaps show and the geometric model denies

    The threshold is quoted at two false-alarm budgets, and both are stated as
    alerts-per-year rather than as a p-value, because that is the number an operator has to
    live with.
    """
    rows = [r for r in proj if r["sleeve"] in sleeves]
    days = sorted({dt.date.fromisoformat(r["decision_day"]) for r in rows
                   if f"{r['sleeve']}|{r['symbol']}|{r['entry_utc']}" in filled_keys
                   and dt.date.fromisoformat(r["decision_day"]) >= full_from})
    if len(days) < 3:
        return {"error": "too few book-days"}

    sess_index = {}
    d, i = full_from, 0
    while d <= ARCHIVE_END:
        if d.weekday() < 5:
            sess_index[d] = i
            i += 1
        d += dt.timedelta(days=1)
    n_sess = i

    idx = sorted(sess_index[d] for d in days if d in sess_index)
    gaps = [b - a for a, b in zip(idx, idx[1:])]
    density = len(idx) / n_sess if n_sess else 0.0

    def emp_q(p):
        if not gaps:
            return None
        g = sorted(gaps)
        return g[min(len(g) - 1, int(math.ceil(p * len(g))) - 1)]

    def geo_q(p):
        # P(gap > k) = (1-density)^k  =>  k = log(1-p)/log(1-density)
        if not (0 < density < 1):
            return None
        return int(math.ceil(math.log(1 - p) / math.log(1 - density)))

    rng = random.Random(seed)
    series = [1 if j in set(idx) else 0 for j in range(n_sess)]
    BL = 21  # ~a trading month: long enough to carry the clustering
    boot_q = {}
    for p in (0.95, 0.99):
        qs = []
        for _ in range(2000):
            out_s, cur = [], 0
            while cur < n_sess:
                st = rng.randrange(0, max(1, n_sess - BL))
                out_s.extend(series[st:st + BL])
                cur += BL
            out_s = out_s[:n_sess]
            ii = [j for j, v in enumerate(out_s) if v]
            gg = [b - a for a, b in zip(ii, ii[1:])] or [n_sess]
            gg.sort()
            qs.append(gg[min(len(gg) - 1, int(math.ceil(p * len(gg))) - 1)])
        qs.sort()
        boot_q[p] = {"median": qs[len(qs) // 2], "p05": qs[int(0.05 * len(qs))],
                     "p95": qs[int(0.95 * len(qs))]}

    def alerts_per_year(k):
        """How often a 'k silent sessions' rule fires on the OBSERVED history."""
        n = sum(1 for g in gaps if g > k)
        yrs = n_sess / 252.0
        return round(n / yrs, 3) if yrs else None

    rec = {}
    for label, k in (("empirical_p95", emp_q(0.95)), ("empirical_p99", emp_q(0.99)),
                     ("geometric_p95", geo_q(0.95)), ("geometric_p99", geo_q(0.99)),
                     ("block_bootstrap_p95", boot_q[0.95]["median"]),
                     ("block_bootstrap_p99", boot_q[0.99]["median"])):
        if k is not None:
            rec[label] = {"silent_weekday_sessions": int(k),
                          "calendar_days_approx": round(int(k) * 7 / 5),
                          "alerts_per_year_on_observed_history": alerts_per_year(int(k))}
    return {
        "basis": ("live-equivalent book-days on the FULL-SURFACE window; silence is counted "
                  "in WEEKDAY SESSIONS so a weekend never contributes to an alarm"),
        "window": f"{full_from.isoformat()}..{ARCHIVE_END.isoformat()}",
        "weekday_sessions": n_sess, "book_days": len(idx),
        "book_day_density": round(density, 5),
        "gap_sessions": {"n": len(gaps), "mean": round(statistics.fmean(gaps), 2) if gaps else None,
                         "median": statistics.median(gaps) if gaps else None,
                         "max": max(gaps) if gaps else None},
        "thresholds": rec,
        "block_bootstrap_detail": {str(k): v for k, v in boot_q.items()},
        "RECOMMENDATION": None,   # filled by main() once the numbers are in
        "what_it_is_NOT": (
            "not a health check on the engine. A book at this density is silent for long "
            "runs BY DESIGN, so an alarm can only ever say 'this silence is longer than the "
            "archive's 95th/99th percentile' — it cannot distinguish a quiet market from a "
            "dead worker. The engine-liveness question is the heartbeat's, not this one's."),
    }


# =====================================================================================
# STAGE clock — the calendar distribution to the FTMO target at the MEASURED cadence
# =====================================================================================
def clock(daily_frac: dict, *, live_density: float, archive_density: float,
          paths: int, targets, seed: int = 7, block: int = 5) -> dict:
    """Time-to-target in CALENDAR days, on the BOOK's own realised daily series.

    Deliberately NOT `mc_firm_rules.mc`: that engine answers "does this book pass the firm's
    rules", which AI already published for the armed sets. The commission's question is
    different and simpler — *how long does +X% take, and how wide is that distribution* —
    and the answer is dominated by CADENCE, which is what this file measured.

    The series is `book_replay.book_daily_series` on the full-surface window: P&L as a
    fraction of balance, at the PRODUCTION sizer and governor, on the V2 population, with
    the placement guards already applied. Nothing here re-derives a size or a confidence
    weight; the book already did.

    THE COMPARISON THAT MATTERS is not the absolute number — this clock charges no drawdown
    rule and is therefore optimistic — but the ratio between two calendar mappings of the
    SAME economics:

        live density     book-days the guards actually leave
        archive density  book-days the unserialized walk counts, which is the divisor in
                         `mc_firm_rules._derived` (:622-624) and hence in every published
                         `median_calendar_days_to_pass`

    Holding the day distribution fixed and varying only the density isolates exactly the
    error the published calendar clocks carry, and nothing else.

    Resampling is a MOVING-BLOCK bootstrap (block=5 book-days). An iid day bootstrap would
    destroy the clustering the gap distribution shows is there, and the estate's own
    standing rule is that treating trades as iid overstated an error budget by 2.1-7.7x
    (B279).
    """
    days = sorted(daily_frac)
    vals = [daily_frac[d] for d in days]
    if len(vals) < block + 1:
        return {"error": f"series too short: {len(vals)} book-days"}

    rng = random.Random(seed)
    n = len(vals)
    out = {}
    for tgt in targets:
        bd = []
        for _ in range(paths):
            eq, k = 1.0, 0
            while eq < 1.0 + tgt and k < 5000:
                st = rng.randrange(0, n)
                for j in range(block):
                    eq *= 1.0 + vals[(st + j) % n]
                    k += 1
                    if eq >= 1.0 + tgt:
                        break
            bd.append(k)
        bd.sort()

        def cal(x, dens):
            return round(x / dens * (7 / 5), 1) if dens else None

        out[f"+{tgt * 100:g}%"] = {
            "median_book_days": bd[len(bd) // 2],
            "p10_book_days": bd[int(0.10 * len(bd))],
            "p90_book_days": bd[int(0.90 * len(bd))],
            "median_calendar_days_LIVE_density": cal(bd[len(bd) // 2], live_density),
            "p10_calendar_days_LIVE_density": cal(bd[int(0.10 * len(bd))], live_density),
            "p90_calendar_days_LIVE_density": cal(bd[int(0.90 * len(bd))], live_density),
            "p99_calendar_days_LIVE_density": cal(bd[int(0.99 * len(bd))], live_density),
            "median_calendar_days_ARCHIVE_density": cal(bd[len(bd) // 2], archive_density),
            "calendar_inflation_vs_published_convention": (
                round(archive_density / live_density, 4) if live_density else None),
        }
    return {
        "paths": paths, "seed": seed, "block_book_days": block,
        "series_basis": ("book_replay.book_daily_series(key='exit') on the full-surface "
                         "window — production sizer + governor + placement guards, V2 "
                         "population, P&L as a fraction of balance"),
        "book_days_in_series": len(vals),
        "mean_daily_frac": round(statistics.fmean(vals), 6),
        "sd_daily_frac": round(statistics.pstdev(vals), 6),
        "live_book_day_density": round(live_density, 5),
        "archive_book_day_density": round(archive_density, 5),
        "targets": out,
        "NOT_a_p_pass": ("time-to-target only; it charges no drawdown rule and no daily-loss "
                         "rule, so it is an OPTIMISTIC clock. The p_pass question is "
                         "phase8/receipts/BOOKS_MC_V1.json's and is not restated here."),
    }


# =====================================================================================
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=("all", "occupancy", "cadence", "alarm", "clock", "bookreplay"))
    ap.add_argument("--paths", type=int, default=20000)
    args = ap.parse_args(argv)

    est = json.loads(gzip.open(ESTATE, "rt").read())
    tf_of = est["timeframe_by_sleeve"]
    proj = project([r for s in est["trades"] for r in est["trades"][s]])
    cov = bar_coverage()

    doc: dict = {
        "schema": "gtos.live.fill_truth.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase13/receipts/bb_fill_truth.py",
        "session": "BB", "blocks": "B1951-B1975",
        "armed_set": list(ARMED4),
        "armed_set_provenance": ("phase8/receipts/FXJPY_PULL_20260730.md — fx_jpy pulled "
                                 "2026-07-30 ~14:57Z, host commit 7017c6745"),
        "estate_artifact": str(ESTATE.relative_to(REPO)),
        "archive_end": ARCHIVE_END.isoformat(),
        "outcome_blind_control": ("project() emits exactly (sleeve, symbol, entry_utc, "
                                  "exit_utc, decision_day); no return field reaches the "
                                  "occupancy or cadence stages"),
    }

    occ = occupancy(proj, ARMED4)
    occ_alt = occupancy(proj, ARMED4, tie_break="reverse")
    occ["tie_break_sensitivity"] = {
        "reverse_order_fills": occ_alt["n_live_equivalent_fills"],
        "delta": occ_alt["n_live_equivalent_fills"] - occ["n_live_equivalent_fills"],
    }
    occ5 = occupancy(proj, ARMED5_BEFORE)
    doc["occupancy_armed_four"] = {k: v for k, v in occ.items() if k != "filled_keys"}
    doc["occupancy_armed_five_before_the_fx_jpy_pull"] = {
        k: v for k, v in occ5.items() if k != "filled_keys"}
    print(f"occupancy: {occ['n_archive_decisions']} archive decisions -> "
          f"{occ['n_live_equivalent_fills']} live-equivalent fills "
          f"({occ['suppression_frac']:.1%} suppressed)", flush=True)

    filled_keys = set(occ["filled_keys"])
    cad = cadence(proj, ARMED4, cov, filled_keys, tf_of)
    doc["cadence"] = cad
    full_from = dt.date.fromisoformat(cad["book"]["live_equivalent"]["FULL_SURFACE_from"])
    print(f"cadence: full symbol surface from {full_from}; live-equivalent "
          f"{cad['book']['live_equivalent']['FULL_SURFACE_fills_per_week']} fills/week",
          flush=True)

    pr = production_replay(est, ARMED4, start=full_from)
    doc["production_replay"] = {k: v for k, v in pr.items() if k != "_daily"}
    for lbl, r in pr["runs"].items():
        print(f"book_replay {lbl:22s} {r['n_candidates_priced']:5d} priced -> "
              f"{r['n_placed']:5d} placed ({r['placement_frac']:.1%}), "
              f"{r['book_days']} book-days, halt="
              f"{'YES' if r['halted_on_max_dd_entry_block'] else 'no'}", flush=True)

    if args.stage in ("all", "alarm"):
        al = alarm(proj, ARMED4, filled_keys, full_from)
        k95 = al["thresholds"]["block_bootstrap_p95"]["silent_weekday_sessions"]
        k99 = al["thresholds"]["block_bootstrap_p99"]["silent_weekday_sessions"]
        al["RECOMMENDATION"] = {
            "warn_after_silent_weekday_sessions": k95,
            "alert_after_silent_weekday_sessions": k99,
            "why_the_block_bootstrap_and_not_the_geometric": (
                "the empirical gaps are CLUSTERED, so the memoryless model understates the "
                "tail; the block bootstrap preserves the clustering and is the conservative "
                "of the three"),
            "expected_false_alarms_per_year": {
                "warn": al["thresholds"]["block_bootstrap_p95"]["alerts_per_year_on_observed_history"],
                "alert": al["thresholds"]["block_bootstrap_p99"]["alerts_per_year_on_observed_history"],
            },
        }
        doc["quiet_alarm"] = al
        print(f"alarm: warn at {k95} silent sessions, alert at {k99}", flush=True)

    if args.stage in ("all", "clock"):
        doc["clock"] = {}
        for run, dens_key in (("full_surface_window", "FULL_SURFACE_book_day_density"),
                              ("full_archive", "book_day_density")):
            doc["clock"][run] = clock(
                pr["_daily"][run], paths=args.paths,
                live_density=cad["book"]["live_equivalent"][dens_key],
                archive_density=cad["book"]["archive"][dens_key],
                targets=(0.0197, 0.05, 0.10))
            for t, c in (doc["clock"][run].get("targets") or {}).items():
                print(f"clock[{run[:12]:12s}] {t:>7s}: median {c['median_book_days']:4d} "
                      f"book-days = {c['median_calendar_days_LIVE_density']:6.0f} cal-days "
                      f"live (p90 {c['p90_calendar_days_LIVE_density']:.0f}); published "
                      f"convention would say "
                      f"{c['median_calendar_days_ARCHIVE_density']:.0f}", flush=True)
        doc["clock"]["which_to_read"] = (
            "full_surface_window is the forward read — it is the only window in which all "
            "four armed sleeves' symbol surfaces exist, and it is 87 book-days, which is "
            "thin and is stated as thin. full_archive is 504 book-days and is the long-run "
            "comparator; it mixes eras in which two of the four could not fire at all, so "
            "its cadence is a lower bound and its economics are a different book's."
        )

    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

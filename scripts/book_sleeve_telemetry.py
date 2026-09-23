#!/usr/bin/env python3
"""book_sleeve_telemetry.py — per-sleeve, per-account live telemetry for the ARMED FIVE-sleeve book,
and the pre-registered stop conditions evaluated against it.

READ-ONLY. No broker connection, no MT5 import, no config write, no VPS. It reads a fills file that
someone else produced from a read-only export and a committed stop-conditions artifact, and it
prints a page. It cannot remove a sleeve, change a size, or touch a gate — removing a sleeve is a
`--tags` ceremony on the host and it is the owner's and the orchestrator's, not this tool's.

    python3 scripts/book_sleeve_telemetry.py \
        --fills docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl \
        --armed-utc 2026-07-30T11:52:00Z

Where `--fills` comes from — without it NOTHING here evaluates, and a check that never evaluates is
the failure this tool exists to prevent:

    # 1. export the VPS's MT5 API state (read-only; the orchestrator's ceremony)
    #    -> <export>/09_mt5_api/{ftmo,redacted_account}_history_{deals,orders}_get.jsonl
    # 2. turn it into priced trade rows
    python3 scripts/w7_live_forensics.py --export-root <export> --out-dir <dir>
    #    -> <dir>/LIVE_TRADE_ROWS.jsonl        <- this is the --fills file

Exit codes, matching `canary_watch.py` so the two can sit behind the same thing:
    0  clean
    1  a STOP condition is met, or an ALERT at MEDIUM or above
    3  clean, but something could not be checked

Two design rules this file will not bend:

1. **The pre-arming prior and the post-arming window are never merged.** The prior is evidence the
   owner already had when he accepted the risk; the stop conditions are evaluated on the post-arming
   window ONLY. Both are printed. A tool that silently pooled them would present a sleeve's history
   as its verdict.

2. **Every economic statement is made twice — trade-weighted and day-weighted — and every
   inferential statement carries its own resolution floor.** The dependence unit for these sleeves
   is the decision day (Session R: lag-1 rho 0.511). On the one armed sleeve with a live record the
   two weightings differ by 42 %, and a tripwire reading only one of them would have been wrong
   about which.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import itertools
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs/audits/fable5-vision-audit-20260725"
DEFAULT_CONDITIONS = AUDIT / "phase11/receipts/FIVE_SLEEVE_STOP_CONDITIONS_V1.json"
DEFAULT_BASIS = AUDIT / "phase11/receipts/AS_LIVE_SLEEVE_BASIS_V1.json"

ACCOUNTS = ("FTMO", "redacted_account")
ACCOUNT_KEY = {"FTMO": "ftmo", "redacted_account": "redacted_account"}

CLEAN, UNCHECKED, ALERT, STOP = "CLEAN", "UNCHECKED", "ALERT", "STOP"
_RANK = {CLEAN: 0, UNCHECKED: 1, ALERT: 2, STOP: 3}


class Finding:
    __slots__ = ("cid", "level", "scope", "text", "why")

    def __init__(self, cid, level, scope, text, why=""):
        self.cid, self.level, self.scope, self.text, self.why = cid, level, scope, text, why

    def as_dict(self):
        return {"condition": self.cid, "level": self.level, "scope": self.scope,
                "text": self.text, "why": self.why}


# ---------------------------------------------------------------------------
def _open(path: Path):
    return gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" \
        else open(path, "r", encoding="utf-8")


def read_jsonl(path: Path | None) -> list[dict]:
    if path is None or not path.is_file():
        return []
    out = []
    with _open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def parse_utc(value):
    if not value:
        return None
    s = str(value).strip().replace("Z", "+00:00")
    try:
        d = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


#: Above this many day blocks, exhaustive enumeration is 2**n and the sign-flip goes to a SEEDED
#: Monte Carlo. 20 -> 1,048,576 assignments, about a second; 21 would be two.
_EXACT_BLOCK_LIMIT = 20
_MC_DRAWS = 200_000


def signflip_p(blocks: list[float], null_mean: float) -> dict:
    """One-sided sign-flip permutation over day blocks, with its own resolution floor.

    Exact by enumeration up to `_EXACT_BLOCK_LIMIT` blocks; above that a SEEDED Monte Carlo, so a
    healthy book with two months of trading days still gets a p. A first cut returned `p=None` above
    20 blocks, which meant MORE data produced a WEAKER statement — exactly backwards, and it is the
    normal case after a month of fills rather than an edge case.

    The seed is derived from the data itself, so the same input always yields the same p and the
    number on the page is reproducible without a wall clock or a global random state.

    `resolution_floor` is 1/achievable for the exact test and 1/draws for the Monte Carlo. A p at or
    below its floor is a floor artefact, not a measurement (wave-11 agreement §2).
    """
    cent = [float(v) - float(null_mean) for v in blocks]
    n = len(cent)
    if n == 0:
        return {"p": None, "reason": "no_day_blocks", "n_blocks": 0, "null_mean": float(null_mean)}
    obs = sum(cent)
    if n <= _EXACT_BLOCK_LIMIT:
        total = 2 ** n
        hits = sum(1 for s in itertools.product((1, -1), repeat=n)
                   if sum(a * b for a, b in zip(s, cent)) <= obs)
        p, floor = hits / total, 1.0 / total
        method, achievable = "exact_enumeration", total
    else:
        import hashlib
        import random
        seed = int(hashlib.sha256(
            json.dumps([round(c, 12) for c in cent]).encode()).hexdigest()[:16], 16)
        rng = random.Random(seed)
        hits = 0
        for _ in range(_MC_DRAWS):
            if sum(c if rng.random() < 0.5 else -c for c in cent) <= obs:
                hits += 1
        p, floor = hits / _MC_DRAWS, 1.0 / _MC_DRAWS
        method, achievable = f"seeded_monte_carlo_{_MC_DRAWS}_draws_seed_{seed}", 2 ** n
    return {"p": p, "n_blocks": n, "achievable_assignments": achievable,
            "resolution_floor": floor, "p_over_floor": p / floor,
            "at_or_below_floor": p <= floor, "method": method,
            "test": "sign_flip_over_day_blocks_one_sided_lower", "null_mean": float(null_mean)}


def longest_run(values: list[str], token: str) -> int:
    best = cur = 0
    for v in values:
        cur = cur + 1 if v == token else 0
        best = max(best, cur)
    return best


# ---------------------------------------------------------------------------
def summarise(fills: list[dict]) -> dict:
    """The per-(sleeve, account) telemetry block. Pure arithmetic over rows."""
    if not fills:
        return {"n_fills": 0}
    byday = defaultdict(list)
    for r in fills:
        byday[r.get("day_key_broker_server") or r.get("day_key_utc")].append(r)
    days = sorted(byday)
    g_day = [st.mean([x.get("gross_r") or 0.0 for x in byday[d]]) for d in days]
    n_day = [st.mean([x.get("realized_r") or 0.0 for x in byday[d]]) for d in days]
    g_all = [r.get("gross_r") or 0.0 for r in fills]
    n_all = [r.get("realized_r") or 0.0 for r in fills]
    holds = sorted((r.get("holding_seconds") or 0) / 3600.0 for r in fills)
    ordered = sorted(fills, key=lambda r: str(r.get("exit_time_utc") or r.get("entry_time_utc")))
    reasons = [str(r.get("close_reason")) for r in ordered]
    swaps = [float(r.get("swap") or 0.0) for r in fills]
    # swap nights are not in the row; the broker's swap CHARGE is. A nonzero charge is >= 1 night.
    n_swap_charged = sum(1 for s in swaps if s != 0.0)
    return {
        "n_fills": len(fills),
        "n_day_blocks": len(days),
        "span_utc": [min(str(r.get("entry_time_utc")) for r in fills),
                     max(str(r.get("exit_time_utc") or r.get("entry_time_utc")) for r in fills)],
        "gross_r_total": sum(g_all),
        "net_r_total": sum(n_all),
        "gross_r_per_fill_trade_weighted": st.mean(g_all),
        "gross_r_per_fill_day_weighted": st.mean(g_day),
        "net_r_per_fill_trade_weighted": st.mean(n_all),
        "net_r_per_fill_day_weighted": st.mean(n_day),
        "net_r_per_day_block": sum(n_all) / len(days),
        "cost_r_per_fill": st.mean([abs(r.get("cost_r") or 0.0) for r in fills]),
        "median_hold_hours": st.median(holds),
        "p90_hold_hours": holds[min(len(holds) - 1, int(0.9 * len(holds)))],
        "max_hold_hours": holds[-1],
        "n_swap_charged": n_swap_charged,
        "frac_swap_charged": n_swap_charged / len(fills),
        "swap_currency_total": sum(swaps),
        "close_reasons": {k: reasons.count(k) for k in sorted(set(reasons))},
        "longest_stop_run": longest_run(reasons, "sl"),
        "n_gross_positive": sum(1 for x in g_all if x > 0),
        "day_means_gross_r": g_day,
        "day_means_net_r": n_day,
    }


# ---------------------------------------------------------------------------
def evaluate(conds: dict, basis: dict, post: dict, prior: dict) -> tuple[list[Finding], dict]:
    """Evaluate the pre-registered conditions against the POST-ARMING window only."""
    findings: list[Finding] = []
    detail: dict = {}
    C = conds["conditions"]
    armed = tuple(conds["armed_tags"])

    for acct in ACCOUNTS:
        for tag in armed:
            key = f"{acct}::{tag}"
            blk = post.get(key) or {"n_fills": 0}
            row = {"n_fills": blk.get("n_fills", 0), "checks": {}}

            if not blk.get("n_fills"):
                row["checks"]["ALL"] = {"state": UNCHECKED, "reason": "no post-arming fill"}
                detail[key] = row
                continue

            # ---- S1a the RISK floor, and S1b the EVIDENCE floor -------------------------
            # Two floors because "what am I willing to lose" and "what would tell me something"
            # are different questions. S1a on fx_jpy fires 74 % of the time on a sleeve running at
            # exactly its archive expectancy — that is disclosed on every trip, not buried.
            s1a = (C["S1a_risk_floor"]["per_sleeve_account"] or {}).get(key)
            if s1a is None:
                row["checks"]["S1a"] = {"state": UNCHECKED, "reason": "no risk floor declared"}
            else:
                floor = float(s1a["cumulative_net_r_floor"])
                total = blk["net_r_total"]
                fp = s1a.get("measured_false_trip_probability_within_60_fills")
                state = STOP if total <= floor else CLEAN
                row["checks"]["S1a"] = {
                    "state": state, "net_r_total": total, "floor": floor,
                    "headroom_r": total - floor,
                    "measured_false_trip_probability_within_60_fills": fp}
                if state == STOP:
                    findings.append(Finding(
                        "S1a", STOP, key,
                        f"cumulative net {total:+.3f} R is at or below the pre-registered RISK "
                        f"floor {floor:+.3f} R over {blk['n_fills']} fills",
                        f"A risk bound, not an inference: the owner has paid what he "
                        f"pre-registered as the price of finding out. This floor fires "
                        f"{fp:.0%} of the time on a sleeve running at exactly its archive "
                        f"expectancy, so it says nothing about the sleeve."
                        if fp is not None else
                        "A risk bound, not an inference."))

            s1b = (C["S1b_evidence_floor"]["per_sleeve_account"] or {}).get(key)
            if s1b is None or s1b.get("evidence_floor_r") is None:
                row["checks"]["S1b"] = {"state": UNCHECKED, "reason": "no evidence floor declared"}
            else:
                ef = float(s1b["evidence_floor_r"])
                total = blk["net_r_total"]
                state = STOP if total <= ef else CLEAN
                row["checks"]["S1b"] = {
                    "state": state, "net_r_total": total, "evidence_floor": ef,
                    "headroom_r": total - ef,
                    "measured_false_trip_probability_within_60_fills":
                        s1b.get("measured_false_trip_probability_within_60_fills")}
                if state == STOP:
                    findings.append(Finding(
                        "S1b", STOP, key,
                        f"cumulative net {total:+.3f} R is at or below the EVIDENCE floor "
                        f"{ef:+.3f} R over {blk['n_fills']} fills",
                        f"This one is informative: at a false-alarm rate of "
                        f"{s1b.get('measured_false_trip_probability_within_60_fills')}, a walk "
                        f"this deep is evidence the sleeve is not running at its archive "
                        f"expectancy. Still not a significance test — read it with S2's p."))

            # ---- S2 gross negative on BOTH weightings -----------------------------------
            s2 = C["S2_gross_negative"]
            if blk["n_fills"] < s2["min_fills"] or blk["n_day_blocks"] < s2["min_day_blocks"]:
                row["checks"]["S2"] = {
                    "state": UNCHECKED,
                    "reason": f"needs >= {s2['min_fills']} fills over >= "
                              f"{s2['min_day_blocks']} day blocks; have {blk['n_fills']} over "
                              f"{blk['n_day_blocks']}"}
            else:
                tw, dw = blk["gross_r_per_fill_trade_weighted"], blk["gross_r_per_fill_day_weighted"]
                arch = ((basis.get("carry_basis") or {}).get(key) or {}) \
                    .get("archive_gross_r_per_trade")
                p0 = signflip_p(blk["day_means_gross_r"], 0.0)
                pa = signflip_p(blk["day_means_gross_r"], arch) if arch is not None else None
                both = tw < 0 and dw < 0
                row["checks"]["S2"] = {
                    "state": STOP if both else CLEAN,
                    "gross_trade_weighted": tw, "gross_day_weighted": dw,
                    "both_negative": both, "p_vs_zero": p0, "p_vs_archive_gross": pa}
                if both:
                    ptxt = f"p {p0['p']:.4f} vs zero over {p0['n_blocks']} day blocks " \
                           f"(floor {p0['resolution_floor']:.2e})" if p0.get("p") is not None else \
                           "p not evaluable"
                    findings.append(Finding(
                        "S2", STOP, key,
                        f"GROSS negative on both weightings: trade-weighted {tw:+.4f}, "
                        f"day-weighted {dw:+.4f} R/fill over {blk['n_fills']} fills",
                        f"A sleeve losing before any cost cannot be rescued by a better cost "
                        f"model. Power disclosure: {ptxt} — the tripwire is a risk bound, and "
                        f"this p is what it does and does not establish."))

            # ---- S3 carry surprise -------------------------------------------------------
            s3 = (C["S3_carry_surprise"]["per_sleeve_account"] or {}).get(key)
            if s3 is None:
                row["checks"]["S3"] = {"state": UNCHECKED, "reason": "no carry basis"}
            else:
                # the fills file carries the swap CHARGE, not a night count; frac_swap_charged is a
                # LOWER bound on mean nights (one charge is at least one night), so it can only
                # under-report. Stated rather than silently treated as equal.
                lower_bound_nights = blk["frac_swap_charged"]
                alert_at = s3.get("alert_mean_nights_above")
                stop_at = s3.get("stop_mean_nights_above")
                state = CLEAN
                if stop_at is not None and lower_bound_nights > stop_at:
                    state = STOP
                elif alert_at is not None and lower_bound_nights > alert_at:
                    state = ALERT
                row["checks"]["S3"] = {
                    "state": state,
                    "frac_positions_charged_swap": lower_bound_nights,
                    "is_a_lower_bound_on_mean_nights": True,
                    "alert_above": alert_at, "stop_above": stop_at}
                if state != CLEAN:
                    findings.append(Finding(
                        "S3", state, key,
                        f"{lower_bound_nights:.2%} of closed positions were charged swap; the "
                        f"basis alerts above {alert_at} nights and stops above {stop_at}",
                        "The number here is a LOWER bound on mean nights — the row records the "
                        "charge, not the night count — so a trip is real and a clean read is not "
                        "proof."))

            # ---- S4 hold-time surprise ---------------------------------------------------
            s4 = (C["S4_hold_time_surprise"]["per_sleeve"] or {}).get(tag)
            limit = (s4 or {}).get("alert_median_hold_hours_above")
            if limit is None:
                row["checks"]["S4"] = {"state": UNCHECKED, "reason": "no hold basis"}
            else:
                med = blk["median_hold_hours"]
                state = ALERT if med > limit else CLEAN
                row["checks"]["S4"] = {"state": state, "median_hold_hours": med,
                                       "alert_above_hours": limit,
                                       "archive_median_hours": s4.get("archive_median_hold_hours")}
                if state == ALERT:
                    findings.append(Finding(
                        "S4", ALERT, key,
                        f"median hold {med:.2f} h is above 3x the archive median "
                        f"({s4.get('archive_median_hold_hours')} h)",
                        "The published economics describe a different exit contract than the one "
                        "running. Re-price before acting on them."))

            # ---- S5 stop-out run ---------------------------------------------------------
            s5 = C["S5_stop_out_run"]
            run = blk["longest_stop_run"]
            state = STOP if run >= s5["stop_run"] else (ALERT if run >= s5["alert_run"] else CLEAN)
            row["checks"]["S5"] = {"state": state, "longest_stop_run": run,
                                   "alert_run": s5["alert_run"], "stop_run": s5["stop_run"]}
            if state != CLEAN:
                findings.append(Finding(
                    "S5", state, key,
                    f"longest run of stop-outs is {run} "
                    f"(alert {s5['alert_run']}, stop {s5['stop_run']})",
                    s5["caveat"]))

            row["telemetry"] = {k: v for k, v in blk.items()
                                if k not in ("day_means_gross_r", "day_means_net_r")}
            row["prior"] = prior.get(key)
            detail[key] = row
    return findings, detail


def expected_tags_for(conds: dict, account: str) -> list[str] | None:
    """S6's expected `--tags` for ONE account.

    THE TWO ACCOUNTS NO LONGER RUN THE SAME BOOK, and a single flat list cannot say so.
    Since 2026-07-31 FTMO carries `mx_btcusd_d1_donchian_20_breakout` on `--frontier-exits`
    while redacted_account carries four sleeves and no frontier
    (`phase13/receipts/MX_ACTIVATION_20260731.md`). Against a flat list, S6 fires CRITICAL on
    whichever account is not the one the list describes — for the wrong reason, on the
    condition whose whole job is to be believed before anything else on the page.

    So `expected_tags` may be either:
      * a LIST — the same book on both accounts (every artifact before 2026-07-31), or
      * a MAPPING account -> list — the per-account form.
    A mapping that omits an account returns None, and the caller reports UNCHECKED rather
    than guessing: an account with no declared expectation has not been checked.
    """
    raw = conds["conditions"]["S6_book_composition"]["expected_tags"]
    if isinstance(raw, dict):
        got = raw.get(account)
        return None if got is None else list(got)
    return list(raw)


def check_composition(conds: dict, launch_tags: dict | None) -> tuple[list[Finding], dict]:
    """S6 — the one condition that makes everything else meaningless if it is wrong."""
    out = {"expected": conds["conditions"]["S6_book_composition"]["expected_tags"],
           "per_account": {}}
    findings = []
    for acct in ACCOUNTS:
        expected = expected_tags_for(conds, acct)
        if expected is None:
            out["per_account"][acct] = {
                "state": UNCHECKED,
                "reason": (f"the conditions artifact declares expected_tags per account and "
                           f"carries no entry for {acct}. An account with no declared "
                           f"expectation has not been checked; it has not passed.")}
            findings.append(Finding(
                "S6", UNCHECKED, acct,
                "no expected_tags declared for this account",
                "the artifact uses the per-account form and omits this account. Declare it "
                "or the check is silently absent for a live book."))
            continue
        got = (launch_tags or {}).get(acct)
        if got is None:
            out["per_account"][acct] = {"state": UNCHECKED, "expected": expected,
                                        "reason": "no --launch-tags supplied for this account; "
                                                  "read the host launch command with your own eyes"}
            continue
        got = [t for t in got if t]
        ok = sorted(got) == sorted(expected)
        out["per_account"][acct] = {"state": CLEAN if ok else STOP, "observed": got,
                                    "expected": expected}
        if not ok:
            findings.append(Finding(
                "S6", STOP, acct,
                f"--tags is {got or '(empty -> ALL BUILT sleeves)'}, expected {expected}",
                "run_book.py treats --tags '' as falsy and runs every BUILT sleeve. Nothing else "
                "on this page means anything until this is right."))
    return findings, out


# ---------------------------------------------------------------------------
def render(page: dict) -> str:
    L: list[str] = []
    W = 92
    L.append("=" * W)
    L.append("  ARMED FIVE-SLEEVE BOOK — per-sleeve telemetry and pre-registered stop conditions")
    L.append(f"  as of {page['now_utc']}   ·   armed {page['armed_utc']}")
    L.append("=" * W)
    L.append("")
    L.append(f"  overall: {page['verdict']}   (exit code {page['exit_code']})")
    L.append(f"  fills file: {page['fills_path'] or '(none supplied)'}"
             f"   rows read: {page['n_rows_read']}")
    L.append(f"  post-arming fills across the armed set: {page['n_post_arming_fills']}")
    L.append("")

    comp = page["composition"]
    L.append("-" * W)
    L.append("  S6 — BOOK COMPOSITION (read this first; nothing below matters if it is wrong)")
    L.append("-" * W)
    L.append(f"  expected --tags : {','.join(comp['expected'])}")
    for acct, blk in comp["per_account"].items():
        if blk["state"] == UNCHECKED:
            L.append(f"  {acct:<12} UNCHECKED — {blk['reason']}")
        else:
            L.append(f"  {acct:<12} {blk['state']:<9} observed: {','.join(blk['observed']) or '(EMPTY)'}")
    L.append("")

    L.append("-" * W)
    L.append("  THE ARMED SET, AND WHAT EACH SLEEVE WAS ARMED ON")
    L.append("-" * W)
    L.append(f"  {'sleeve (FTMO)':<20}{'conf':>6}{'tgt':>5}{'ts':>10}{'archive R/tr':>14}"
             f"{'risk flr':>10}{'P(false)':>10}{'evid flr':>10}")
    for tag in page["armed_tags"]:
        c = page["contract"].get(tag) or {}
        f = page["floors"].get(f"FTMO::{tag}") or {}
        e = (page.get("evidence_floors") or {}).get(f"FTMO::{tag}") or {}
        own = c.get("time_stop_own_bars")
        fp = f.get("measured_false_trip_probability_within_60_fills")
        L.append(f"  {tag:<20}{c.get('registry_confidence', 0):>6}"
                 f"{str(c.get('final_target_r')):>5}"
                 f"{(f'{own:.0f}/80' if own is not None else '?'):>10}"
                 f"{f.get('archive_net_r_per_trade_at_measured_carry', 0):>14.5f}"
                 f"{f.get('cumulative_net_r_floor', 0):>10.2f}"
                 f"{(f'{fp:.0%}' if fp is not None else '?'):>10}"
                 f"{(e.get('evidence_floor_r') if e.get('evidence_floor_r') is not None else 0):>10.2f}")
    L.append("")
    L.append("  risk flr = what you pre-registered as the price of finding out. P(false) = how "
             "often it")
    L.append("  fires on a sleeve running at EXACTLY its archive expectancy. evid flr = the depth "
             "at which")
    L.append("  a trip is informative (false-alarm rate <= 10 %). They are different questions.")
    L.append("")
    for tag in page["armed_tags"]:
        n = (page["contract"].get(tag) or {}).get("note_for_operator")
        if n:
            for chunk in _wrap(f"  {tag}: {n}", W):
                L.append(chunk)
    L.append("")

    L.append("-" * W)
    L.append("  PER-SLEEVE TELEMETRY — POST-ARMING WINDOW ONLY")
    L.append("-" * W)
    any_post = False
    for key, row in page["per_sleeve"].items():
        if not row.get("n_fills"):
            continue
        any_post = True
        t = row["telemetry"]
        L.append(f"  {key}   n={t['n_fills']} over {t['n_day_blocks']} day blocks   "
                 f"{t['span_utc'][0][:16]} .. {t['span_utc'][1][:16]}")
        L.append(f"      gross R/fill  trade-wt {t['gross_r_per_fill_trade_weighted']:+.4f}   "
                 f"day-wt {t['gross_r_per_fill_day_weighted']:+.4f}   total "
                 f"{t['gross_r_total']:+.3f}")
        L.append(f"      net   R/fill  trade-wt {t['net_r_per_fill_trade_weighted']:+.4f}   "
                 f"day-wt {t['net_r_per_fill_day_weighted']:+.4f}   total "
                 f"{t['net_r_total']:+.3f}   R/day-block {t['net_r_per_day_block']:+.4f}")
        L.append(f"      cost R/fill {t['cost_r_per_fill']:.4f}   swap charged on "
                 f"{t['n_swap_charged']}/{t['n_fills']}   hold med {t['median_hold_hours']:.2f} h "
                 f"p90 {t['p90_hold_hours']:.2f} h max {t['max_hold_hours']:.2f} h")
        L.append(f"      closes {t['close_reasons']}   longest stop run {t['longest_stop_run']}")
        for cid, chk in row["checks"].items():
            L.append(f"      {cid:<4} {chk['state']}"
                     + (f" — {chk['reason']}" if chk.get("reason") else ""))
        L.append("")
    if not any_post:
        L.append("  no post-arming fill of any armed sleeve is present in this fills file.")
        L.append("  That is NOT a clean bill — it means every economic condition is UNCHECKED.")
        L.append("  Expect roughly 7 book-days a month; long silences are normal, not a fault.")
        L.append("")

    if page["prior"]:
        L.append("-" * W)
        L.append("  THE PRE-ARMING PRIOR — evidence the owner already had. NEVER merged above.")
        L.append("-" * W)
        for key, blk in page["prior"].items():
            if not blk or not blk.get("n_fills"):
                continue
            L.append(f"  {key}   n={blk['n_fills']} over {blk['n_day_blocks']} day blocks   "
                     f"eras {blk.get('stack_eras')}")
            L.append(f"      gross R/fill  trade-wt "
                     f"{blk['gross_r_per_fill_trade_weighted']:+.4f}   day-wt "
                     f"{blk['gross_r_per_fill_day_weighted']:+.4f}   total "
                     f"{blk['gross_r_total']:+.3f}")
            L.append(f"      net total {blk['net_r_total']:+.3f} R   "
                     f"{blk['net_r_per_day']:+.4f} R/day   closes {blk['close_reasons']}")
            sig = (page["prior_significance"] or {}).get(key) or {}
            z, a = sig.get("vs_zero") or {}, sig.get("vs_archive_gross") or {}
            if z.get("p") is not None:
                L.append(f"      day-blocked exact sign-flip: p vs 0 = {z['p']:.4f}  "
                         f"(floor {z['resolution_floor']:.2e}, {z['n_blocks']} blocks)")
            if a.get("p") is not None:
                L.append(f"                                  p vs archive gross "
                         f"{a['null_mean']:+.4f} = {a['p']:.4f}")
            L.append("")
        for chunk in _wrap(
                "  Read this the way the arithmetic supports it: the trade-weighted total is what "
                "the account lost, and the day-blocked permutation is what that establishes. On "
                "fx_jpy they disagree — the loss is real and it is not significant. 32 fills over "
                "13 days cannot establish an edge in either direction, which is exactly why the "
                "stop conditions above are risk bounds and not tests.", W):
            L.append(chunk)
        L.append("")

    L.append("-" * W)
    L.append("  FINDINGS")
    L.append("-" * W)
    if not page["findings"]:
        L.append("  none.")
    for f in page["findings"]:
        L.append(f"  [{f['level']}] {f['condition']} · {f['scope']}")
        for chunk in _wrap("      " + f["text"], W):
            L.append(chunk)
        if f["why"]:
            for chunk in _wrap("      why: " + f["why"], W):
                L.append(chunk)
        L.append("")

    L.append("-" * W)
    L.append("  IF YOU DECIDE TO TAKE A SLEEVE BACK OFF")
    L.append("-" * W)
    da = page["de_arm"]
    for k in ("how", "what_it_stops", "what_it_does_NOT_stop", "same_day_size_consequence",
              "never"):
        for chunk in _wrap(f"  {k}: {da[k]}", W):
            L.append(chunk)
    L.append("")
    L.append("  This tool changes nothing. It is not built so that it could.")
    L.append("=" * W)
    return "\n".join(L)


def _wrap(text: str, width: int) -> list[str]:
    indent = len(text) - len(text.lstrip())
    pad = " " * indent
    words, lines, cur = text.split(), [], pad
    for w in words:
        if len(cur) + len(w) + 1 > width and cur.strip():
            lines.append(cur)
            cur = pad + "  " + w
        else:
            cur = (cur + " " + w) if cur.strip() else pad + w
    if cur.strip():
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
def build_page(args) -> dict:
    conds = json.loads(Path(args.conditions).read_text())
    basis = json.loads(Path(args.basis).read_text()) if Path(args.basis).is_file() else {}
    armed = tuple(conds["armed_tags"])
    armed_utc = parse_utc(args.armed_utc) or parse_utc(
        (basis.get("armed_utc") or {}).get("FTMO"))

    rows = read_jsonl(Path(args.fills)) if args.fills else []
    post, prior = {}, {}
    n_post = 0
    for acct in ACCOUNTS:
        akey = ACCOUNT_KEY[acct]
        for tag in armed:
            mine = [r for r in rows
                    if r.get("sleeve_id") == tag and str(r.get("account", "")).lower() == akey]
            if armed_utc is None:
                after, before = mine, []
            else:
                after = [r for r in mine if (parse_utc(r.get("entry_time_utc")) or armed_utc)
                         >= armed_utc]
                before = [r for r in mine if r not in after]
            post[f"{acct}::{tag}"] = summarise(after)
            n_post += len(after)
            pb = (basis.get("live_prior") or {}).get("per_sleeve_account", {}).get(f"{acct}::{tag}")
            if not (pb and pb.get("n_fills")):
                pb = summarise(before) if before else None
                # `summarise` names the per-day figure `net_r_per_day_block`; the committed basis
                # names it `net_r_per_day`. Normalise here rather than letting the renderer KeyError
                # on the fallback path — a page that crashes on the rare branch is a page nobody
                # trusts on the day it matters.
                if pb and pb.get("n_fills"):
                    pb.setdefault("net_r_per_day", pb["net_r_per_day_block"])
                    pb.setdefault("stack_eras",
                                  sorted({str(r.get("stack_era")) for r in before}))
            prior[f"{acct}::{tag}"] = pb

    findings, detail = evaluate(conds, basis, post, prior)
    launch = None
    if args.launch_tags_ftmo or args.launch_tags_redacted_account:
        launch = {}
        if args.launch_tags_ftmo is not None:
            launch["FTMO"] = [t.strip() for t in args.launch_tags_ftmo.split(",")]
        if args.launch_tags_redacted_account is not None:
            launch["redacted_account"] = [t.strip() for t in args.launch_tags_redacted_account.split(",")]
    cf, comp = check_composition(conds, launch)
    findings = cf + findings

    # the operator note per sleeve: the one thing about this sleeve worth carrying in your head
    contract = dict(basis.get("live_contract") or {})
    for tag, blk in contract.items():
        notes = []
        if blk.get("contract_fidelity_class", "").startswith("UNIT_CORRECT_BINDS"):
            blk_t = blk.get("frac_trades_the_time_stop_would_truncate")
            notes.append(
                f"its live time stop is TIGHTER than the research horizon "
                f"({blk.get('time_stop_own_bars'):.0f} of 80 own bars); AQ measured the economic "
                f"cost of that at {blk_t:.1%} of walked trades — immaterial, but it is not the "
                f"contract the published figure describes")
        if blk.get("policy") == "partial_be_runner":
            notes.append("its live scale-out is a partial_be_runner; AD measured that feature at "
                         "-0.308 R/day against the plain exit on n=67 (thin — a question, not a "
                         "recommendation)")
        f = (conds["conditions"]["S1a_risk_floor"]["per_sleeve_account"] or {})
        for acct in ACCOUNTS:
            r = f.get(f"{acct}::{tag}") or {}
            ex = r.get("archive_net_r_per_trade_at_measured_carry")
            if ex is not None and abs(ex) < 0.10:
                notes.append(
                    f"on {acct} its archive net expectancy at measured carry is {ex:+.5f} R/trade "
                    f"— it needs {r.get('fills_to_trip_at_archive_expectancy')} fills to earn back "
                    f"the {abs(r.get('cumulative_net_r_floor', 0)):.1f} R floor it would trip in "
                    f"{r.get('fills_to_trip_at_live_prior')} at its live prior")
        if notes:
            blk["note_for_operator"] = "; ".join(notes)

    unchecked = any(
        c.get("state") == UNCHECKED
        for row in detail.values() for c in (row.get("checks") or {}).values()
    ) or any(b.get("state") == UNCHECKED for b in comp["per_account"].values())

    worst = max([_RANK[f.level] for f in findings], default=0)
    if worst >= _RANK[ALERT]:
        verdict, code = (STOP if worst == _RANK[STOP] else ALERT), 1
    elif unchecked:
        verdict, code = UNCHECKED, 3
    else:
        verdict, code = CLEAN, 0

    return {
        "schema": "gtos.live.sleeve_telemetry_page.v1",
        "now_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "armed_utc": args.armed_utc or (basis.get("armed_utc") or {}).get("FTMO"),
        "armed_tags": list(armed),
        "conditions_artifact": str(args.conditions),
        "basis_artifact": str(args.basis),
        "fills_path": str(args.fills) if args.fills else None,
        "n_rows_read": len(rows),
        "n_post_arming_fills": n_post,
        "composition": comp,
        "contract": contract,
        "floors": conds["conditions"]["S1a_risk_floor"]["per_sleeve_account"],
        "evidence_floors": conds["conditions"]["S1b_evidence_floor"]["per_sleeve_account"],
        "per_sleeve": detail,
        "prior": prior,
        "prior_significance": (basis.get("live_prior_significance") or {}).get(
            "per_sleeve_account", {}),
        "de_arm": conds["de_arm_mechanism"],
        "findings": [f.as_dict() for f in findings],
        "verdict": verdict,
        "exit_code": code,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fills", type=Path, default=None,
                    help="LIVE_TRADE_ROWS.jsonl from scripts/w7_live_forensics.py")
    ap.add_argument("--conditions", type=Path, default=DEFAULT_CONDITIONS)
    ap.add_argument("--basis", type=Path, default=DEFAULT_BASIS)
    ap.add_argument("--armed-utc", default=None,
                    help="split the fills file here; before = prior, at/after = the window")
    ap.add_argument("--launch-tags-ftmo", default=None,
                    help="the --tags string the FTMO worker was launched with (read it off the host)")
    ap.add_argument("--launch-tags-redacted_account", default=None)
    ap.add_argument("-o", "--output", type=Path, default=None)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    if not Path(args.conditions).is_file():
        print(f"stop-conditions artifact missing: {args.conditions}", file=sys.stderr)
        print("generate it: python3 docs/audits/fable5-vision-audit-20260725/phase11/receipts/"
              "as_live_basis.py", file=sys.stderr)
        return 3

    page = build_page(args)
    text = render(page)
    print(text)
    if args.output:
        args.output.write_text(text + "\n")
    if args.json:
        args.json.write_text(json.dumps(page, indent=1, default=str) + "\n")
    return page["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())

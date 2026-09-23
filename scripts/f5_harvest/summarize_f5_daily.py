#!/usr/bin/env python3
"""Summarize one day's F5 harvest into DAILY.md (v2, owner page) + TELEGRAM.txt.

Usage: summarize_f5_daily.py <dated-harvest-dir> [--date YYYY-MM-DD]

IN-REPO COPY (scripts/f5_harvest/, 2026-08-25). v2 changes vs the f5-harvest
original: DOLLARS FIRST — the page opens with day net by era ($10 vs $75,
broker-deals authority when the dump is present, ledger otherwise), cumulative
era split, the beyond-−1R overshoot ledger, per-day broker reconciliation with
explicit FAILED RECONCILIATION lines, fill-deviation breaches, same-bar fill
clusters, judge activity, and the open-position map; a 6-line TELEGRAM.txt is
written alongside. Fills are deduped by ticket (earliest event wins) so a
restart re-emission can never double-list a ticket across day pages. The v1
sections (blocks, frozen intents, ledger slate, LANES, artifacts) are retained
below the owner page.

RUN ORDER: after build_f5_outcome_ledger.py — this reads the cumulative ledger
and <root>/f5_broker_reconciliation.json. Missing inputs degrade to labelled
absence, never an exception.

UNITS DOCTRINE (CLAUDE.md section 7): dollars are broker-true USD (basis named
per block); R appears only with its denominator named — the trade's own
initial stop distance.

Stdlib only; compatible with macOS system python3 (3.9).
"""
import argparse
import json
import os
import sys
from collections import Counter, OrderedDict
from datetime import datetime, timezone


def read_jsonl(path):
    """Return (rows, n_parse_errors, file_exists)."""
    rows, bad = [], 0
    if not os.path.isfile(path):
        return rows, bad, False
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                bad += 1
    return rows, bad, True


def read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def short_reasons(reason_lists):
    """Unique refusal reasons with the parenthetical detail stripped."""
    out = []
    for reasons in reason_lists:
        for r in reasons or []:
            head = str(r).split(" (", 1)[0]
            if head not in out:
                out.append(head)
    return out


def hhmm(ts):
    ts = str(ts or "")
    return (ts[11:16] + "Z") if len(ts) >= 16 else (ts or "-")


def fmt_money(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "?"
    return ("-$%.2f" % abs(v)) if v < 0 else ("$%.2f" % v)


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def era_key(v):
    """f5_intended_risk_usd -> stratum label."""
    if is_num(v):
        if abs(v - 75.0) < 0.5:
            return "$75"
        if abs(v - 10.0) < 0.5:
            return "$10"
        return "$%g" % v
    return "unknown"


def dedupe_fills(fill_events):
    """One ticket == one fill. Earliest event wins; sleeve prefers the
    candidate_id tail on a dual attribution (mirrors the ledger builder)."""
    by_ticket = OrderedDict()
    dup_attrib = set()
    for e in sorted(fill_events, key=lambda r: str(r.get("ts_utc", ""))):
        t = e.get("ticket")
        if t is None:
            continue
        prev = by_ticket.get(t)
        if prev is None:
            by_ticket[t] = dict(e)
            continue
        if e.get("sleeve") != prev.get("sleeve"):
            dup_attrib.add(t)
            tail = str(prev.get("candidate_id") or "").split("::")[-1]
            if e.get("sleeve") == tail and prev.get("sleeve") != tail:
                keep = dict(e)
                keep["ts_utc"] = prev.get("ts_utc")
                by_ticket[t] = keep
    return list(by_ticket.values()), dup_attrib


# --------------------------------------------------------------- ledger pulls
def ledger_rows(root):
    rows, _, ok = read_jsonl(os.path.join(root, "f5_outcome_ledger_cumulative.jsonl"))
    return rows if ok else []


def closed_rows(rows):
    return [r for r in rows if r.get("outcome_class") == "FILLED_CLOSED"]


def row_net(r):
    lc = ((r.get("later_known") or {}).get("lifecycle") or {})
    return (lc.get("dollars") or {}).get("net_usd")


def row_exit_day(r):
    lc = ((r.get("later_known") or {}).get("lifecycle") or {})
    return str(lc.get("broker_exit_time_utc") or "")[:10]


def row_actual_risk(r):
    f = ((r.get("later_known") or {}).get("fill") or {})
    return f.get("f5_actual_risk_usd")


def era_of_row(r):
    return era_key(r.get("era"))


def net_by_era(rows_subset):
    out = {}
    for r in rows_subset:
        net = row_net(r)
        if is_num(net):
            k = era_of_row(r)
            out[k] = round(out.get(k, 0.0) + net, 2)
    return out


def overshoot_rows(rows_subset):
    """Closed losers that lost MORE than 1R of their own actual risk.

    overshoot_usd = net + actual_risk (negative = dollars beyond −1R).
    R denominator: the trade's own initial stop distance at its actual risk.
    """
    out = []
    for r in rows_subset:
        net, risk = row_net(r), row_actual_risk(r)
        if not (is_num(net) and is_num(risk) and risk > 0):
            continue
        if net < -risk - 0.005:
            exc = ((r.get("later_known") or {}).get("excursion") or {})
            out.append({
                "ticket": ((r.get("later_known") or {}).get("fill") or {}).get("ticket"),
                "symbol": r.get("symbol"), "sleeve": r.get("sleeve"),
                "era": era_of_row(r), "net_usd": net,
                "overshoot_usd": round(net + risk, 2),
                "realised_r": ((r.get("later_known") or {}).get("lifecycle") or {}).get("realised_r"),
                "mfe_r": exc.get("mfe_r"), "mfe_usd": exc.get("mfe_usd"),
                "exc_status": exc.get("status"),
                "exit_day": row_exit_day(r),
            })
    out.sort(key=lambda x: x["overshoot_usd"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dest", help="dated harvest directory")
    ap.add_argument("--date", default=None, help="UTC day YYYY-MM-DD (default: dir name)")
    args = ap.parse_args()
    dest = os.path.abspath(args.dest)
    root = os.path.dirname(dest)
    day = args.date or os.path.basename(dest)
    now = datetime.now(timezone.utc)
    missing = []

    events, events_bad, ok = read_jsonl(os.path.join(dest, "events.jsonl"))
    if not ok:
        missing.append("events.jsonl")
    decisions, dec_bad, ok = read_jsonl(os.path.join(dest, "execution_manager_v4_decisions.jsonl"))
    if not ok:
        missing.append("execution_manager_v4_decisions.jsonl")
    slip, slip_bad, ok = read_jsonl(os.path.join(dest, "slippage_runtime.jsonl"))
    if not ok:
        missing.append("slippage_runtime.jsonl")

    # tailday (4 MB, from 2026-08-18) preferred; tail256k is the pre-08-18 name.
    launcher_name = None
    launcher_rows = []
    for cand in ("ultimate_book_launcher.tailday.jsonl",
                 "ultimate_book_launcher.tail256k.jsonl"):
        if os.path.isfile(os.path.join(dest, cand)):
            launcher_name = cand
            break
    launcher_lines = 0
    launcher_bytes = 0
    if launcher_name:
        launcher_path = os.path.join(dest, launcher_name)
        launcher_bytes = os.path.getsize(launcher_path)
        with open(launcher_path, "r", encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                launcher_lines += 1
                try:
                    launcher_rows.append(json.loads(ln))
                except Exception:
                    pass   # byte-tail may start mid-line
    else:
        launcher_name = "ultimate_book_launcher.tailday.jsonl"
        missing.append(launcher_name)

    lrows = ledger_rows(root)
    lclosed = closed_rows(lrows)
    recon = read_json(os.path.join(root, "f5_broker_reconciliation.json"))

    # ---- fills today (deduped by ticket; earliest event wins) ---------------
    all_fills = [r for r in events if r.get("event") == "f5_fill"]
    fills_unique, dup_attrib = dedupe_fills(all_fills)
    fills = [r for r in fills_unique if str(r.get("ts_utc", ""))[:10] == day]
    fills.sort(key=lambda r: str(r.get("ts_utc", "")))
    n_dup_events_today = (
        len([r for r in all_fills if str(r.get("ts_utc", ""))[:10] == day]) - len(fills))
    fill_bits = []
    for r in fills:
        tag = " [dual-sleeve attribution]" if r.get("ticket") in dup_attrib else ""
        fill_bits.append("%s (%s) %s ticket %s risk %s%s" % (
            r.get("symbol", "?"), r.get("sleeve", "?"), hhmm(r.get("ts_utc")),
            r.get("ticket", "?"), fmt_money(r.get("f5_actual_risk_usd")), tag))

    # ---- OWNER PAGE blocks --------------------------------------------------
    # day net by era: broker-deals authority when today is covered, else ledger
    day_source = "ledger (broker-deals dump absent for %s)" % day
    day_net_era = {}
    recon_day = ((recon or {}).get("days") or {}).get(day)
    if recon_day and recon_day.get("status") != "NOT_COVERED_BY_DUMP":
        day_net_era = dict(recon_day.get("broker_net_by_era") or {})
        day_source = "broker deals dump (authority)"
    else:
        day_net_era = net_by_era([r for r in lclosed if row_exit_day(r) == day])
    day_net_total = round(sum(day_net_era.values()), 2) if day_net_era else 0.0

    cum_era = net_by_era(lclosed)
    cum_total = round(sum(cum_era.values()), 2) if cum_era else 0.0

    over_all = overshoot_rows(lclosed)
    over_today = [o for o in over_all if o["exit_day"] == day]
    over_usd_by_era = {}
    for o in over_all:
        over_usd_by_era[o["era"]] = round(
            over_usd_by_era.get(o["era"], 0.0) + o["overshoot_usd"], 2)

    # reconciliation lines (today + every FAILED day on record)
    recon_lines = []
    if recon:
        days_map = recon.get("days") or {}
        for d in sorted(days_map):
            v = days_map[d]
            if v.get("status") == "FAILED":
                recon_lines.append(
                    "**FAILED RECONCILIATION %s**: broker %s (%d closed) vs ledger %s "
                    "(%d closed), diff %s; broker-only tickets %s; ledger-only %s"
                    % (d, fmt_money(v.get("broker_net_usd")), v.get("broker_n_closed", 0),
                       fmt_money(v.get("ledger_net_usd")), v.get("ledger_n_closed", 0),
                       fmt_money(v.get("diff_usd")),
                       v.get("tickets_broker_only") or "-",
                       v.get("tickets_ledger_only") or "-"))
        if recon_day:
            if recon_day.get("status") == "RECONCILED":
                recon_lines.insert(0, "%s RECONCILED: broker %s == ledger %s (%d closed)"
                                   % (day, fmt_money(recon_day.get("broker_net_usd")),
                                      fmt_money(recon_day.get("ledger_net_usd")),
                                      recon_day.get("ledger_n_closed", 0)))
        elif not any(day in ln for ln in recon_lines):
            recon_lines.insert(0, "%s: not covered by the deals dump window" % day)
    else:
        recon_lines.append("no broker-deals reconciliation on record "
                           "(f5_broker_reconciliation.json absent — run "
                           "dump_f5_deals.py on the VPS and re-harvest)")

    # deviation breaches (events may not exist yet — tolerate absence)
    dev_breaches = [r for r in events if r.get("event") == "f5_fill_deviation_breach"
                    and str(r.get("ts_utc", ""))[:10] == day]

    # same-bar cluster concentration: >1 fill inside one decision bar
    clusters = OrderedDict()
    for r in fills:
        bar = str(r.get("decision_bar_iso") or "?")
        clusters.setdefault(bar, []).append(r)
    cluster_lines = []
    for bar, rs in clusters.items():
        if len(rs) < 2:
            continue
        dirs = Counter()
        risk_sum = 0.0
        for r in rs:
            cd = "?"
            for part in str(r.get("candidate_id") or "").split("::"):
                if part in ("LONG", "SHORT"):
                    cd = part
            dirs[cd] += 1
            if is_num(r.get("f5_actual_risk_usd")):
                risk_sum += r["f5_actual_risk_usd"]
        cluster_lines.append("- bar %s: **%d fills** (%s) — %s at risk: %s" % (
            hhmm(bar), len(rs),
            ", ".join("%d %s" % (v, k) for k, v in dirs.items()),
            fmt_money(risk_sum),
            "; ".join("%s/%s" % (r.get("symbol"), r.get("sleeve")) for r in rs)))

    # judge activity: judgment/judge_<day>.jsonl (harvested) + launcher
    # judgment_flow entries in today's cycle rows. Tolerate absence of both.
    judge_paths = [os.path.join(dest, "judgment", "judge_%s.jsonl" % day),
                   os.path.join(dest, "judge_%s.jsonl" % day),
                   os.path.join(root, "judgment", "judge_%s.jsonl" % day)]
    judge_rows = []
    judge_src = None
    for p in judge_paths:
        rs, _, ok = read_jsonl(p)
        if ok:
            judge_rows, judge_src = rs, p
            break
    judge_verdicts = Counter(str(r.get("verdict") or r.get("action") or "?").lower()
                             for r in judge_rows)
    judge_manage = [r for r in judge_rows
                    if str(r.get("kind") or r.get("row_type") or "") == "manage"
                    or r.get("manage_action")]
    flow_decisions = []
    flow_holds = []
    for lr in launcher_rows:
        if str(lr.get("ts", ""))[:10] != day:
            continue
        for fd in lr.get("judgment_flow") or []:
            flow_decisions.append(fd)
            if str(fd.get("action") or "").upper() == "HOLD":
                flow_holds.append(fd)
        for sk in lr.get("skipped") or []:
            if isinstance(sk, dict) and sk.get("reason") == "judgment_hold":
                flow_holds.append(sk)
    flow_mix = Counter(str(fd.get("action") or "?").upper() for fd in flow_decisions)

    # open-position map from the ledger
    open_rows = [r for r in lrows if r.get("outcome_class") == "FILLED_OPEN"]
    open_lines = []
    for r in open_rows:
        f = ((r.get("later_known") or {}).get("fill") or {})
        t_fill = str(f.get("broker_fill_time_utc") or f.get("placed_at_utc") or "")
        age = "?"
        try:
            tf = datetime.strptime(t_fill[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            age = "%.1fd" % ((now - tf).total_seconds() / 86400.0)
        except Exception:
            pass
        open_lines.append("- %s %s (%s, %s) ticket %s entry %s risk %s open %s" % (
            r.get("symbol", "?"), r.get("direction", "?"), r.get("sleeve", "?"),
            era_of_row(r), f.get("ticket", "?"),
            f.get("broker_entry_price", "?"),
            fmt_money(f.get("f5_actual_risk_usd")), age))

    # ---- blocks today, by fatal_reason (v1) ---------------------------------
    blocks = [r for r in decisions
              if r.get("action") == "block" and str(r.get("generated_at_utc", ""))[:10] == day]
    by_reason = OrderedDict()
    for r in sorted(blocks, key=lambda x: str(x.get("generated_at_utc", ""))):
        key = " ; ".join(r.get("fatal_reasons") or ["<none>"])
        ident = r.get("identity") or {}
        cand = str(ident.get("candidate_id") or "")
        sleeve = cand.split("::")[-1] if "::" in cand else "?"
        sym = ident.get("symbol") or ident.get("broker_symbol") or "?"
        by_reason.setdefault(key, []).append(
            "%s %s %s" % (hhmm(r.get("generated_at_utc")), sym, sleeve))

    # ---- frozen intents (v1) ------------------------------------------------
    refs = [r for r in events if r.get("event") == "f5_refusal_quote"
            and (r.get("decision_day") == day or str(r.get("ts_utc", ""))[:10] == day)]
    episodes = OrderedDict()
    for r in sorted(refs, key=lambda x: str(x.get("ts_utc", ""))):
        key = (str(r.get("candidate_id")), str(r.get("decision_bar_iso")))
        episodes.setdefault(key, []).append(r)

    ep_lines = []
    n_enq = n_ioc = n_never = n_cleared = n_killed_after_clear = 0
    for (cand, bar), rows in episodes.items():
        last = rows[-1]
        statuses = []
        for r in rows:
            s = str(r.get("frozen_price_intent_status"))
            if s not in statuses:
                statuses.append(s)
        reasons = short_reasons(r.get("refusal_reasons") for r in rows)
        sprs = [r.get("spread_r") for r in rows if is_num(r.get("spread_r"))]
        spr_txt = ("%.3f-%.3f" % (min(sprs), max(sprs))) if sprs else "-"
        lag = last.get("first_clear_lag_s")
        chase = last.get("chase_at_first_clear")
        enq = any(s in ("REFUSED_COST", "OBSERVING") for s in statuses)
        ioc = any("timeout_no_fill" in x for x in reasons)
        killed = [s for s in statuses if s.startswith("killed")]
        if enq:
            n_enq += 1
        if ioc:
            n_ioc += 1
        outcome = []
        if isinstance(lag, str) and lag == "never":
            n_never += 1
            outcome.append("never cleared")
        elif is_num(lag) and lag > 0:
            n_cleared += 1
            outcome.append("cleared %ds" % int(lag))
            if is_num(chase) and chase > 0:
                outcome.append("chase %.3fR" % chase)
            if killed:
                n_killed_after_clear += 1
        if killed:
            outcome.append("/".join(killed))
        if not outcome:
            outcome.append(statuses[-1] if statuses else "-")
        ep_lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            hhmm(bar), last.get("sleeve", "?"), last.get("symbol", "?"),
            " > ".join(statuses), spr_txt, " ".join(outcome) or "-",
            "; ".join(reasons) or "-"))

    # ---- ledger slate (v1) --------------------------------------------------
    slates = sorted((r for r in events if r.get("event") == "f5_slate"),
                    key=lambda r: str(r.get("ts_utc", "")))
    today_slates = [r for r in slates if str(r.get("ts_utc", ""))[:10] == day]
    src = today_slates or slates
    if src:
        last = src[-1]
        fn = last.get("f5_notional") or {}
        stale_note = "" if today_slates else \
            "  **NO SLATE TODAY — last slate is %s (book down?)**" % str(last.get("ts_utc", ""))[:10]
        ledger_line = ("real PnL cumulative **%s** over %s recorded trades; notional equity %s (slate %s)%s" % (
            fmt_money(fn.get("real_pnl_usd_cumulative")), fn.get("trades_recorded", "?"),
            fmt_money(fn.get("notional_equity")), hhmm(last.get("ts_utc")), stale_note))
    else:
        ledger_line = "no `f5_slate` rows in events.jsonl"

    ev_today = Counter(str(r.get("event")) for r in events
                       if str(r.get("ts_utc", ""))[:10] == day or r.get("decision_day") == day)

    # ---- LANES (v1) ---------------------------------------------------------
    lanes_updated, lanes_stale = [], []
    lanes_note = ""
    listing_path = os.path.join(dest, "outbox", "_listing.json")
    if os.path.isfile(listing_path):
        raw = open(listing_path, encoding="utf-8", errors="replace").read().strip()
        try:
            d = json.loads(raw) if raw else []
            if isinstance(d, dict):
                d = [d]
        except Exception:
            d, lanes_note = [], "listing unparseable"
        for x in sorted(d, key=lambda x: str(x.get("Name", ""))):
            name = str(x.get("Name", "?"))
            mt = str(x.get("mtime_utc", ""))
            tag = "" if os.path.isfile(os.path.join(dest, "outbox", name)) else " [pull FAILED]"
            if mt[:10] == day:
                lanes_updated.append("%s (%s)%s" % (name, hhmm(mt), tag))
            else:
                try:
                    t = datetime.strptime(mt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    age = "%.1fd" % ((now - t).total_seconds() / 86400.0)
                except Exception:
                    age = mt or "?"
                lanes_stale.append("%s (stale %s)%s" % (name, age, tag))
    else:
        lanes_note = "outbox listing missing"
        missing.append("outbox/_listing.json")

    # ---- render -------------------------------------------------------------
    L = []
    L.append("# F5 DAILY — %s (UTC day)" % day)
    L.append("")
    L.append("Harvested %s · read-only pull from VPS `redacted_host` shadow_logs + `grok-jobs/outbox`."
             % now.strftime("%Y-%m-%dT%H:%M:%SZ"))
    L.append("")
    L.append("## Dollars (broker USD, FTMO account)")
    era_txt = "; ".join("%s: %s" % (k, fmt_money(v))
                        for k, v in sorted(day_net_era.items())) or "(no closes)"
    L.append("- **Day net %s: %s** — %s · source: %s"
             % (day, fmt_money(day_net_total), era_txt, day_source))
    cum_txt = "; ".join("%s: %s" % (k, fmt_money(v))
                        for k, v in sorted(cum_era.items())) or "(none)"
    L.append("- Cumulative closed (ledger): **%s** — %s over %d closed trades"
             % (fmt_money(cum_total), cum_txt, len(lclosed)))
    over_txt = "; ".join("%s: %s" % (k, fmt_money(v))
                         for k, v in sorted(over_usd_by_era.items())) or "$0.00"
    L.append("- **Beyond-−1R overshoot ledger: %s** (dollars lost past each trade's "
             "own 1R risk; R denominator = the trade's initial stop distance) — %s"
             % (fmt_money(round(sum(over_usd_by_era.values()), 2)), over_txt))
    L.append("")
    L.append("### Broker reconciliation (deals dump vs ledger, per day)")
    for ln in recon_lines:
        L.append("- %s" % ln)
    L.append("")
    if over_all:
        L.append("### Worst beyond-−1R losers (all-time, top 5)")
        L.append("| ticket | symbol | sleeve | era | net | beyond −1R | realised R | MFE before loss |")
        L.append("|---|---|---|---|---|---|---|---|")
        for o in over_all[:5]:
            mfe = ("%.2fR / %s" % (o["mfe_r"], fmt_money(o["mfe_usd"]))
                   if is_num(o.get("mfe_r")) else (o.get("exc_status") or "?"))
            rr = ("%.2f" % o["realised_r"]) if is_num(o.get("realised_r")) else "?"
            L.append("| %s | %s | %s | %s | %s | **%s** | %s | %s |" % (
                o["ticket"], o["symbol"], o["sleeve"], o["era"],
                fmt_money(o["net_usd"]), fmt_money(o["overshoot_usd"]), rr, mfe))
        if over_today:
            L.append("")
            L.append("Overshoot TODAY: %s across %d trade(s)."
                     % (fmt_money(round(sum(o["overshoot_usd"] for o in over_today), 2)),
                        len(over_today)))
        L.append("")
    L.append("### Fill-deviation breaches today")
    if dev_breaches:
        for r in dev_breaches:
            L.append("- %s %s ticket %s: %s" % (
                hhmm(r.get("ts_utc")), r.get("symbol", "?"), r.get("ticket", "?"),
                r.get("reason") or r.get("deviation_r") or json.dumps(
                    {k: v for k, v in r.items() if k not in
                     ("event", "schema", "namespace", "account_login")})[:160]))
    else:
        L.append("(none — `f5_fill_deviation_breach` events absent or zero today)")
    L.append("")
    L.append("### Same-bar fill clusters today")
    if cluster_lines:
        L.extend(cluster_lines)
    else:
        L.append("(no decision bar produced more than one fill)")
    L.append("")
    L.append("### Judge activity")
    if judge_rows:
        L.append("- %d row(s) in %s — verdicts: %s; holds: %d; manage actions: %d"
                 % (len(judge_rows), os.path.basename(judge_src),
                    ", ".join("%s×%d" % (k, v) for k, v in sorted(judge_verdicts.items())) or "-",
                    judge_verdicts.get("hold", 0) + judge_verdicts.get("veto", 0),
                    len(judge_manage)))
    else:
        L.append("- no judge_%s.jsonl rows found (judge dark or file not harvested)" % day)
    if flow_decisions or flow_holds:
        L.append("- engine judgment_flow today: %s; judgment_hold skips: %d"
                 % (", ".join("%s×%d" % (k, v) for k, v in sorted(flow_mix.items())) or "-",
                    len([x for x in flow_holds if x.get("reason") == "judgment_hold"])))
    L.append("")
    L.append("### Open positions (ledger FILLED_OPEN)")
    if open_lines:
        L.extend(open_lines)
    else:
        L.append("(book flat by ledger)")
    L.append("")
    L.append("## Fills today")
    if fill_bits:
        dup_note = (" — %d duplicate fill event(s) suppressed (dedupe by ticket)"
                    % n_dup_events_today) if n_dup_events_today else ""
        L.append("**%d fill(s):** %s%s" % (len(fills), "; ".join(fill_bits), dup_note))
    else:
        L.append("**0 fills.**")
    L.append("")
    L.append("## Blocks today (exec-manager `action=block`, by fatal_reason)")
    if by_reason:
        for reason, items in by_reason.items():
            L.append("- `%s` × %d: %s" % (reason, len(items), "; ".join(items)))
    else:
        L.append("(none)")
    L.append("")
    L.append("## Frozen intents (`f5_refusal_quote` episodes)")
    if ep_lines:
        L.append("| bar | sleeve | symbol | statuses | spread_r | outcome | reasons |")
        L.append("|---|---|---|---|---|---|---|")
        L.extend(ep_lines)
        L.append("")
        L.append("**%d episode(s)** — %d enqueued (REFUSED_COST/OBSERVING), %d IOC timeout_no_fill, "
                 "%d never cleared, %d cleared post-refusal (%d of those killed after clearing)."
                 % (len(episodes), n_enq, n_ioc, n_never, n_cleared, n_killed_after_clear))
    else:
        L.append("(no refusal-quote rows today)")
    L.append("")
    L.append("## Ledger")
    L.append(ledger_line)
    if ev_today:
        L.append("")
        L.append("Event mix today: %s." % ", ".join(
            "%s×%d" % (k, v) for k, v in sorted(ev_today.items())))
    L.append("")
    L.append("## LANES (grok-jobs outbox)")
    L.append("- updated today: %s" % ("; ".join(lanes_updated) if lanes_updated else "(none)"))
    L.append("- stale: %s" % ("; ".join(lanes_stale) if lanes_stale else "(none)"))
    if lanes_note:
        L.append("- note: %s" % lanes_note)
    L.append("")
    L.append("## Artifacts")
    L.append("- events.jsonl: %d rows (%d parse errors)" % (len(events), events_bad))
    L.append("- execution_manager_v4_decisions.jsonl: %d rows (%d parse errors); %d blocks today"
             % (len(decisions), dec_bad, len(blocks)))
    L.append("- slippage_runtime.jsonl: %d rows (%d parse errors) — archived, not summarized"
             % (len(slip), slip_bad))
    L.append("- %s: %d lines / %d B "
             "(server-side byte-tail of the launcher log; first line may be partial)"
             % (launcher_name, launcher_lines, launcher_bytes))
    if missing:
        L.append("- **MISSING artifacts: %s**" % ", ".join(missing))
    L.append("")

    out_path = os.path.join(dest, "DAILY.md")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))

    # ---- TELEGRAM.txt: 6 lines, dollars first, plain text (no HTML) --------
    n_failed_recon = sum(1 for ln in recon_lines if ln.startswith("**FAILED"))
    recon_word = ("RECON FAILED x%d" % n_failed_recon) if n_failed_recon else \
        ("recon ok" if recon else "recon absent")
    breach_bits = []
    if dev_breaches:
        breach_bits.append("%d deviation breach(es)" % len(dev_breaches))
    if cluster_lines:
        breach_bits.append("%d same-bar cluster(s)" % len(cluster_lines))
    if over_today:
        breach_bits.append("overshoot today %s" % fmt_money(
            round(sum(o["overshoot_usd"] for o in over_today), 2)))
    T = [
        "F5 %s day net %s (%s)" % (day, fmt_money(day_net_total), era_txt),
        "cumulative %s (%s)" % (fmt_money(cum_total), cum_txt),
        "beyond -1R total %s" % fmt_money(round(sum(over_usd_by_era.values()), 2)),
        "flags: %s" % ("; ".join(breach_bits) if breach_bits else "none"),
        "open %d position(s); fills today %d; judge rows %d" % (
            len(open_rows), len(fills), len(judge_rows)),
        recon_word,
    ]
    with open(os.path.join(dest, "TELEGRAM.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(T) + "\n")

    print("DAILY %s: fills=%d blocks=%d intent_episodes=%d day_net=%s recon_failed=%d lanes_updated=%d/%d%s" % (
        day, len(fills), len(blocks), len(episodes), fmt_money(day_net_total),
        n_failed_recon, len(lanes_updated),
        len(lanes_updated) + len(lanes_stale),
        (" MISSING=" + ",".join(missing)) if missing else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

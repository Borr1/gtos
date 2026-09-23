"""Week-1 verification readout for the J46-J49 + side-aware ship.

Run after each KZ (or daily) to get a structured pass/fail summary across:
  - mechanical health (J46-J49 fired correctly per fill)
  - outcome distribution (R buckets, mean, median, BE rate)
  - WR cohorts (portfolio + per-symbol + LONG/SHORT)
  - shadow-logger comparison (cumulative delta_r vs OLD policy)
  - LONG-WR-watch SPRT status
  - side-aware SPRT watcher status
  - decay watch (OB continuation, regime distribution)
  - operational health (orchestrators alive, dormant marker, alerts)

Pure local — no API cost. Reads JSONL/CSV/JSON from shadow_logs/ + pipeline_state/.

Usage:
  python scripts/week1_j46_j49_verification.py
  python scripts/week1_j46_j49_verification.py --since 2026-04-28
  python scripts/week1_j46_j49_verification.py --json   # machine-readable
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parent.parent

SHADOW_DIR = REPO / "shadow_logs"
STATE_DIR = REPO / "pipeline_state"
LOGS_DIR = REPO / "logs"
LIVE_SESSIONS_DIR = REPO / "knowledge_base" / "live_sessions"

J46_J49_LOG = SHADOW_DIR / "j46_j49_shadow_outcomes.jsonl"
HEARTBEAT_LOG = SHADOW_DIR / "heartbeat_flatten_events.jsonl"
ALERTS_LOG = SHADOW_DIR / "live_monitor_alerts.jsonl"
OB_CONT_CSV = SHADOW_DIR / "ob_continuation_daily.csv"
REGIME_LOG = SHADOW_DIR / "regime_classifications.jsonl"
SIDE_AWARE_STATE = STATE_DIR / "side_aware_sprt_state.json"
DORMANT_STATE = STATE_DIR / "dormant_state.json"

EXPECTED_ORCHESTRATORS = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD", "XAGUSD", "NAS100"]


# ----- ANSI colors -----

ANSI = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _c(s: str, code: str) -> str:
    if not ANSI:
        return s
    return f"\033[{code}m{s}\033[0m"


def green(s: str) -> str: return _c(s, "32")
def red(s: str) -> str: return _c(s, "31")
def yellow(s: str) -> str: return _c(s, "33")
def cyan(s: str) -> str: return _c(s, "36")
def bold(s: str) -> str: return _c(s, "1")
def dim(s: str) -> str: return _c(s, "2")


# ----- I/O helpers -----

def _read_jsonl(path: Path, since: datetime | None = None,
                ts_field: str = "timestamp_logged") -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if since is not None:
                ts = d.get(ts_field) or d.get("ts") or d.get("ts_utc") or d.get("logged_at")
                if not ts:
                    rows.append(d)
                    continue
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    rows.append(d)
                    continue
                if dt < since:
                    continue
            rows.append(d)
    return rows


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


# ----- Health computations -----

def mechanical_health(rows: list[dict]) -> dict:
    """For each shadow row, check J46-J49 fields are populated and exit reasons are valid."""
    valid_actual_reasons = {
        "tp1_be_only_j46_j49",
        "tp2_higher_target_j46_j49",
        "j46_j49_time_stop",
        "broker_closed",
        "tp1_full_close",
        "tp2_full_close",
        "manual",
        "stop_loss",
        "sl_modification_failed",
        "consecutive_losses_stop",
        "portfolio_drawdown_stop",
    }
    valid_hyp_reasons = {"old_tp1_hit", "old_sl_hit", "old_timeout_close", "old_be_close"}

    n = len(rows)
    fields_ok = 0
    actual_reason_ok = 0
    hyp_reason_ok = 0
    missing_ai_tp1 = 0
    null_shadow = 0
    errors = 0

    for r in rows:
        if all(k in r for k in ("fill_id", "instrument", "direction", "entry_time",
                                "entry_price", "original_sl", "actual_close")):
            fields_ok += 1
        if r.get("original_ai_tp1") in (None, 0, 0.0):
            missing_ai_tp1 += 1
        actual = (r.get("actual_close") or {}).get("exit_reason") or ""
        if actual in valid_actual_reasons or actual.startswith("tp"):
            actual_reason_ok += 1
        hyp = r.get("hypothetical_old")
        if hyp is None:
            null_shadow += 1
            if r.get("error"):
                errors += 1
        else:
            hyp_reason = (hyp or {}).get("exit_reason") or ""
            if hyp_reason in valid_hyp_reasons:
                hyp_reason_ok += 1

    return {
        "n_fills": n,
        "fields_ok": fields_ok,
        "actual_reason_ok": actual_reason_ok,
        "hypothetical_ok": n - null_shadow,
        "hypothetical_reason_ok": hyp_reason_ok,
        "missing_original_ai_tp1": missing_ai_tp1,
        "null_shadow": null_shadow,
        "errors": errors,
    }


def outcome_distribution(rows: list[dict]) -> dict:
    """Bucket realized R values; compute mean/median; check loss bound."""
    rs = []
    over_loss_bound = []
    be_count = 0
    buckets = {"<=-1.05": 0, "(-1.05,-0.5)": 0, "[-0.5,0)": 0, "0_BE": 0,
               "(0,1)": 0, "[1,3)": 0, "[3,6)": 0, ">=6": 0}
    for r in rows:
        ac = r.get("actual_close") or {}
        try:
            R = float(ac.get("realized_R", 0))
        except (TypeError, ValueError):
            continue
        rs.append(R)
        if R <= -1.05:
            buckets["<=-1.05"] += 1
            over_loss_bound.append({"fill_id": r.get("fill_id"), "R": R})
        elif R < -0.5:
            buckets["(-1.05,-0.5)"] += 1
        elif R < 0:
            buckets["[-0.5,0)"] += 1
        elif abs(R) < 0.05:
            buckets["0_BE"] += 1
            be_count += 1
        elif R < 1:
            buckets["(0,1)"] += 1
        elif R < 3:
            buckets["[1,3)"] += 1
        elif R < 6:
            buckets["[3,6)"] += 1
        else:
            buckets[">=6"] += 1

    return {
        "n": len(rs),
        "mean_R": round(statistics.mean(rs), 4) if rs else None,
        "median_R": round(statistics.median(rs), 4) if rs else None,
        "stdev_R": round(statistics.stdev(rs), 4) if len(rs) >= 2 else None,
        "be_count": be_count,
        "over_loss_bound": over_loss_bound,
        "buckets": buckets,
    }


def wr_cohorts(rows: list[dict]) -> dict:
    """Win rate breakdowns. Win = realized_R > 0 (BE excluded)."""
    def _wr(subset: list[dict]) -> tuple[int, int, float | None]:
        wins = 0
        losses = 0
        for r in subset:
            ac = r.get("actual_close") or {}
            try:
                R = float(ac.get("realized_R", 0))
            except (TypeError, ValueError):
                continue
            if R > 0.05:
                wins += 1
            elif R < -0.05:
                losses += 1
        total = wins + losses
        return wins, losses, (wins / total if total else None)

    out: dict[str, Any] = {}
    pw, pl, pwr = _wr(rows)
    out["portfolio"] = {"wins": pw, "losses": pl, "wr": pwr}
    by_sym: dict[str, list[dict]] = {}
    by_dir: dict[str, list[dict]] = {"LONG": [], "SHORT": []}
    for r in rows:
        sym = r.get("instrument") or "?"
        by_sym.setdefault(sym, []).append(r)
        d = (r.get("direction") or "").upper()
        if d in by_dir:
            by_dir[d].append(r)
    out["per_symbol"] = {
        sym: dict(zip(("wins", "losses", "wr"), _wr(rs))) for sym, rs in by_sym.items()
    }
    out["per_direction"] = {
        d: dict(zip(("wins", "losses", "wr"), _wr(rs))) for d, rs in by_dir.items()
    }

    xau_long_wr = None
    if "XAUUSD" in by_sym:
        xau_long = [r for r in by_sym["XAUUSD"]
                    if (r.get("direction") or "").upper() == "LONG"]
        _, _, xau_long_wr = _wr(xau_long)
    out["xauusd_long_wr"] = xau_long_wr
    return out


def shadow_delta(rows: list[dict]) -> dict:
    """Cumulative delta_r and per-fill better/worse counts."""
    deltas: list[float] = []
    better = 0
    worse = 0
    same = 0
    for r in rows:
        try:
            d = float(r.get("delta_r"))
        except (TypeError, ValueError):
            continue
        deltas.append(d)
        if d > 0.01:
            better += 1
        elif d < -0.01:
            worse += 1
        else:
            same += 1
    return {
        "n": len(deltas),
        "cumulative_delta_r": round(sum(deltas), 4) if deltas else None,
        "mean_delta_r": round(statistics.mean(deltas), 4) if deltas else None,
        "median_delta_r": round(statistics.median(deltas), 4) if deltas else None,
        "shadow_better": better,
        "shadow_worse": worse,
        "tied": same,
    }


def long_wr_watch(rows: list[dict], symbol: str = "XAUUSD",
                  threshold: float = 0.40, n_window: int = 20) -> dict:
    """LONG-WR-watch SPRT proxy: portfolio LONG WR over the most recent N trades.
    Halts the symbol if WR < threshold."""
    sym_long = [r for r in rows
                if r.get("instrument") == symbol
                and (r.get("direction") or "").upper() == "LONG"]
    sym_long.sort(key=lambda r: r.get("entry_time", ""))
    sample = sym_long[-n_window:]
    wins = sum(1 for r in sample
               if float((r.get("actual_close") or {}).get("realized_R") or 0) > 0.05)
    n = len(sample)
    wr = wins / n if n else None
    return {
        "symbol": symbol,
        "n": n,
        "wins": wins,
        "wr": wr,
        "threshold": threshold,
        "window": n_window,
        "kill_breached": (wr is not None and n >= n_window and wr < threshold),
    }


def operational_health() -> dict:
    """Heartbeats + dormant marker + recent alerts."""
    now = datetime.now(timezone.utc)
    hb = {}
    for sym in EXPECTED_ORCHESTRATORS:
        path = STATE_DIR / f"heartbeat_{sym}.json"
        d = _read_json(path)
        if not d:
            hb[sym] = {"alive": False, "age_s": None, "ts": None}
            continue
        ts = d.get("ts") or d.get("timestamp")
        try:
            dt = datetime.fromisoformat((ts or "").replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age = int((now - dt).total_seconds())
        except (ValueError, AttributeError, TypeError):
            age = None
        hb[sym] = {"alive": age is not None and age < 1800, "age_s": age, "ts": ts}

    dormant = _read_json(DORMANT_STATE)

    alerts_last_24h = 0
    if ALERTS_LOG.exists():
        cutoff = now - timedelta(hours=24)
        rows = _read_jsonl(ALERTS_LOG, since=cutoff, ts_field="ts_utc")
        alerts_last_24h = len(rows)

    return {
        "heartbeats": hb,
        "alive_count": sum(1 for v in hb.values() if v["alive"]),
        "expected_count": len(EXPECTED_ORCHESTRATORS),
        "dormant_state": dormant,
        "alerts_24h": alerts_last_24h,
    }


def decay_watch() -> dict:
    """Latest OB continuation + regime distribution (last 24h)."""
    cont = _read_csv(OB_CONT_CSV)
    cont_latest_by_scope: dict[str, dict] = {}
    for r in cont:
        scope = r.get("scope")
        if not scope:
            continue
        prev = cont_latest_by_scope.get(scope)
        if prev is None or r.get("date_utc", "") > prev.get("date_utc", ""):
            cont_latest_by_scope[scope] = r

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    regime_rows = _read_jsonl(REGIME_LOG, since=cutoff, ts_field="ts")
    regime_counts: dict[str, dict[str, int]] = {}
    for r in regime_rows:
        sym = r.get("symbol", "?")
        reg = r.get("regime", "?")
        regime_counts.setdefault(sym, {}).setdefault(reg, 0)
        regime_counts[sym][reg] += 1

    return {
        "ob_continuation_latest": cont_latest_by_scope,
        "regime_24h": regime_counts,
    }


def side_aware_status() -> dict:
    """Read the side-aware SPRT watcher state."""
    d = _read_json(SIDE_AWARE_STATE)
    if not d:
        return {"present": False}
    outcomes = d.get("long_outcomes") or []
    wins = sum(1 for o in outcomes if o.get("win"))
    n = len(outcomes)
    return {
        "present": True,
        "n_long_outcomes": n,
        "wins": wins,
        "wr": (wins / n) if n else None,
        "disabled_at": d.get("disabled_at"),
        "disable_reason": d.get("disable_reason"),
    }


# ----- Pass/fail signals -----

GREEN = "GREEN"
YELLOW = "YELLOW"
RED = "RED"


def _signal(label: str, status: str, detail: str) -> dict:
    return {"label": label, "status": status, "detail": detail}


def evaluate_signals(report: dict) -> list[dict]:
    sigs: list[dict] = []
    mech = report["mechanical_health"]
    outc = report["outcome_distribution"]
    wr = report["wr_cohorts"]
    shadow = report["shadow_delta"]
    long_watch = report["long_wr_watch"]
    op = report["operational_health"]
    decay = report["decay_watch"]

    n_fills = mech["n_fills"]

    if n_fills == 0:
        sigs.append(_signal("Fills", YELLOW, "no fills since cutoff yet"))
    elif mech["fields_ok"] == n_fills and mech["missing_original_ai_tp1"] == 0:
        sigs.append(_signal("Mechanical fields", GREEN,
                            f"all {n_fills} fills have full J46-J49 schema"))
    else:
        sigs.append(_signal("Mechanical fields", RED,
                            f"{n_fills - mech['fields_ok']} fills missing schema fields, "
                            f"{mech['missing_original_ai_tp1']} missing original_ai_tp1"))

    if n_fills > 0:
        bad = outc["buckets"].get("<=-1.05", 0)
        if bad == 0:
            sigs.append(_signal("Loss bound (-1R)", GREEN,
                                f"no fills past -1.05R floor"))
        else:
            sigs.append(_signal("Loss bound (-1R)", RED,
                                f"{bad} fills exceeded -1.05R floor — investigate slippage / SL slip"))

    if n_fills >= 5:
        pwr = wr["portfolio"]["wr"]
        if pwr is None:
            sigs.append(_signal("Portfolio WR", YELLOW, "no decided trades yet"))
        elif pwr >= 0.55:
            sigs.append(_signal("Portfolio WR", GREEN,
                                f"{pwr:.1%} ({wr['portfolio']['wins']}/{wr['portfolio']['wins']+wr['portfolio']['losses']})"))
        elif pwr >= 0.45:
            sigs.append(_signal("Portfolio WR", YELLOW,
                                f"{pwr:.1%} (target ≥55%; below but within tolerance)"))
        else:
            sigs.append(_signal("Portfolio WR", RED,
                                f"{pwr:.1%} (target ≥55%; well below)"))
    else:
        sigs.append(_signal("Portfolio WR", YELLOW,
                            f"only {n_fills} decided fills — need ≥5 for confidence"))

    if long_watch["n"] >= long_watch["window"]:
        if long_watch["kill_breached"]:
            sigs.append(_signal("XAUUSD LONG-WR SPRT", RED,
                                f"{long_watch['wr']:.1%} < {long_watch['threshold']:.0%} on n={long_watch['n']} — KILL BOUNDARY breached"))
        elif (long_watch["wr"] or 0) < 0.50:
            sigs.append(_signal("XAUUSD LONG-WR SPRT", YELLOW,
                                f"{long_watch['wr']:.1%} on n={long_watch['n']} (above kill, below 50%)"))
        else:
            sigs.append(_signal("XAUUSD LONG-WR SPRT", GREEN,
                                f"{long_watch['wr']:.1%} on n={long_watch['n']}"))
    else:
        sigs.append(_signal("XAUUSD LONG-WR SPRT", YELLOW,
                            f"only {long_watch['n']}/{long_watch['window']} LONG fills — sample insufficient"))

    if shadow["n"] >= 5 and shadow["cumulative_delta_r"] is not None:
        cdr = shadow["cumulative_delta_r"]
        if cdr > 0:
            sigs.append(_signal("J46-J49 shadow Δ", GREEN,
                                f"+{cdr:.2f}R cumulative ({shadow['shadow_better']}/{shadow['n']} fills better than OLD)"))
        elif cdr > -0.5:
            sigs.append(_signal("J46-J49 shadow Δ", YELLOW,
                                f"{cdr:+.2f}R cumulative — neutral, watch trend"))
        else:
            sigs.append(_signal("J46-J49 shadow Δ", RED,
                                f"{cdr:+.2f}R cumulative — NEW POLICY UNDERPERFORMING"))
    else:
        sigs.append(_signal("J46-J49 shadow Δ", YELLOW,
                            f"only {shadow['n']} fills with shadow data — need ≥5"))

    alive = op["alive_count"]
    if alive == op["expected_count"]:
        sigs.append(_signal("Orchestrators alive", GREEN, f"{alive}/{op['expected_count']}"))
    elif alive >= 5:
        sigs.append(_signal("Orchestrators alive", YELLOW, f"{alive}/{op['expected_count']}"))
    else:
        sigs.append(_signal("Orchestrators alive", RED, f"{alive}/{op['expected_count']}"))

    if op["dormant_state"]:
        sigs.append(_signal("Dormant marker", RED,
                            f"{op['dormant_state'].get('symbol','?')}: {op['dormant_state'].get('trigger_reason','?')}"))
    else:
        sigs.append(_signal("Dormant marker", GREEN, "none"))

    cont = decay["ob_continuation_latest"]
    by_scope = []
    for scope, row in cont.items():
        try:
            rate = float(row.get("rate_pct"))
            insufficient = row.get("insufficient_sample") in ("true", "True", True)
            if insufficient:
                by_scope.append((scope, rate, "small"))
            elif rate < 60.0:
                by_scope.append((scope, rate, "ALARM"))
            else:
                by_scope.append((scope, rate, "ok"))
        except (TypeError, ValueError):
            continue
    alarms = [t for t in by_scope if t[2] == "ALARM"]
    if alarms:
        sigs.append(_signal("OB continuation", RED,
                            ", ".join(f"{s}={r:.1f}%" for s, r, _ in alarms)))
    elif by_scope:
        sigs.append(_signal("OB continuation", GREEN,
                            ", ".join(f"{s}={r:.1f}%{'(small)' if status=='small' else ''}"
                                      for s, r, status in by_scope[:5])))

    return sigs


# ----- Main -----

def build_report(since: datetime | None) -> dict:
    rows = _read_jsonl(J46_J49_LOG, since=since)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "since": since.isoformat() if since else None,
        "n_shadow_rows": len(rows),
        "mechanical_health": mechanical_health(rows),
        "outcome_distribution": outcome_distribution(rows),
        "wr_cohorts": wr_cohorts(rows),
        "shadow_delta": shadow_delta(rows),
        "long_wr_watch": long_wr_watch(rows),
        "side_aware_status": side_aware_status(),
        "operational_health": operational_health(),
        "decay_watch": decay_watch(),
    }


def render_text(report: dict) -> str:
    lines = []
    lines.append(bold("=" * 72))
    lines.append(bold("  WEEK-1 J46-J49 + SIDE-AWARE VERIFICATION READOUT"))
    lines.append(bold("=" * 72))
    lines.append(f"  generated: {report['generated_at']}")
    lines.append(f"  since:     {report['since'] or '(all)'}")
    lines.append(f"  fills:     {report['n_shadow_rows']}")
    lines.append("")

    sigs = evaluate_signals(report)
    lines.append(bold("  PASS/FAIL SUMMARY"))
    lines.append("  " + "-" * 70)
    for s in sigs:
        st = s["status"]
        marker = green("[GREEN]") if st == GREEN else (red("[ RED ]") if st == RED else yellow("[YELLO]"))
        lines.append(f"  {marker}  {s['label']:<24} {s['detail']}")
    lines.append("")

    mech = report["mechanical_health"]
    lines.append(bold("  MECHANICAL HEALTH"))
    lines.append("  " + "-" * 70)
    lines.append(f"  schema_ok:               {mech['fields_ok']}/{mech['n_fills']}")
    lines.append(f"  actual_reason_valid:     {mech['actual_reason_ok']}/{mech['n_fills']}")
    lines.append(f"  hypothetical_present:    {mech['hypothetical_ok']}/{mech['n_fills']}")
    lines.append(f"  hypothetical_reason_ok:  {mech['hypothetical_reason_ok']}/{mech['n_fills']}")
    lines.append(f"  missing_ai_tp1:          {mech['missing_original_ai_tp1']}")
    lines.append(f"  null_shadow:             {mech['null_shadow']}")
    lines.append(f"  errors:                  {mech['errors']}")
    lines.append("")

    outc = report["outcome_distribution"]
    lines.append(bold("  OUTCOME DISTRIBUTION"))
    lines.append("  " + "-" * 70)
    lines.append(f"  n: {outc['n']}  mean_R: {outc['mean_R']}  median_R: {outc['median_R']}  stdev: {outc['stdev_R']}")
    lines.append(f"  BE outcomes: {outc['be_count']}")
    lines.append(f"  buckets:")
    for k, v in outc["buckets"].items():
        bar = "#" * v
        lines.append(f"    {k:>14}: {v:>3}  {bar}")
    if outc["over_loss_bound"]:
        lines.append(red(f"  OVER -1.05R FLOOR: {len(outc['over_loss_bound'])} fills"))
        for x in outc["over_loss_bound"][:5]:
            lines.append(f"    {x['fill_id']}  R={x['R']}")
    lines.append("")

    wr = report["wr_cohorts"]
    lines.append(bold("  WR COHORTS"))
    lines.append("  " + "-" * 70)
    pw = wr["portfolio"]
    pwr_str = f"{pw['wr']:.1%}" if pw["wr"] is not None else "n/a"
    lines.append(f"  portfolio: W={pw['wins']} L={pw['losses']} WR={pwr_str}")
    for sym, d in wr["per_symbol"].items():
        wr_str = f"{d['wr']:.1%}" if d["wr"] is not None else "n/a"
        lines.append(f"    {sym:<10} W={d['wins']} L={d['losses']} WR={wr_str}")
    for d_, dd in wr["per_direction"].items():
        wr_str = f"{dd['wr']:.1%}" if dd["wr"] is not None else "n/a"
        lines.append(f"    {d_:<10} W={dd['wins']} L={dd['losses']} WR={wr_str}")
    if wr.get("xauusd_long_wr") is not None:
        lines.append(f"    XAUUSD LONG WR: {wr['xauusd_long_wr']:.1%}")
    lines.append("")

    sh = report["shadow_delta"]
    lines.append(bold("  J46-J49 SHADOW DELTA (vs OLD policy hypothetical)"))
    lines.append("  " + "-" * 70)
    lines.append(f"  n: {sh['n']}  cumulative Δ: {sh['cumulative_delta_r']}  mean: {sh['mean_delta_r']}  median: {sh['median_delta_r']}")
    lines.append(f"  shadow_better: {sh['shadow_better']}  shadow_worse: {sh['shadow_worse']}  tied: {sh['tied']}")
    lines.append("")

    lw = report["long_wr_watch"]
    lines.append(bold("  XAUUSD LONG-WR-WATCH SPRT"))
    lines.append("  " + "-" * 70)
    lines.append(f"  window: last {lw['window']} XAUUSD LONG fills (have {lw['n']})")
    lines.append(f"  wins: {lw['wins']}/{lw['n']}  WR: {f'{lw['wr']:.1%}' if lw['wr'] is not None else 'n/a'}")
    lines.append(f"  kill threshold: <{lw['threshold']:.0%}  breached: {lw['kill_breached']}")
    lines.append("")

    sa = report["side_aware_status"]
    lines.append(bold("  SIDE-AWARE SPRT WATCHER"))
    lines.append("  " + "-" * 70)
    if sa["present"]:
        wr_str = f"{sa['wr']:.1%}" if sa["wr"] is not None else "n/a"
        lines.append(f"  outcomes recorded: {sa['n_long_outcomes']}  wins: {sa['wins']}  WR: {wr_str}")
        if sa["disabled_at"]:
            lines.append(red(f"  AUTO-DISABLED at {sa['disabled_at']}: {sa['disable_reason']}"))
        else:
            lines.append(f"  status: active (or flag is OFF; auto-disable not triggered)")
    else:
        lines.append(dim("  no state file yet (no LONG fills since side-aware shipped)"))
    lines.append("")

    op = report["operational_health"]
    lines.append(bold("  OPERATIONAL"))
    lines.append("  " + "-" * 70)
    lines.append(f"  alive: {op['alive_count']}/{op['expected_count']}")
    for sym, hb in op["heartbeats"].items():
        ind = green("ALIVE") if hb["alive"] else red("DOWN")
        age = f"{hb['age_s']}s" if hb["age_s"] is not None else "n/a"
        lines.append(f"    {sym:<10} {ind:<10} age={age}")
    if op["dormant_state"]:
        lines.append(red(f"  DORMANT: {op['dormant_state']}"))
    lines.append(f"  alerts (last 24h): {op['alerts_24h']}")
    lines.append("")

    decay = report["decay_watch"]
    lines.append(bold("  DECAY WATCH"))
    lines.append("  " + "-" * 70)
    lines.append("  OB continuation (latest per scope):")
    for scope, row in decay["ob_continuation_latest"].items():
        rate = row.get("rate_pct", "?")
        ins = row.get("insufficient_sample", "?")
        lines.append(f"    {scope:<14} rate={rate}%  insufficient_sample={ins}  date={row.get('date_utc','?')}")
    if decay["regime_24h"]:
        lines.append("  regime distribution (last 24h):")
        for sym, counts in decay["regime_24h"].items():
            tot = sum(counts.values())
            parts = ", ".join(f"{r}={n}" for r, n in sorted(counts.items(), key=lambda x: -x[1]))
            lines.append(f"    {sym:<10} n={tot}  {parts}")
    lines.append("")

    lines.append(bold("=" * 72))
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--since", help="ISO date (YYYY-MM-DD) — only count fills logged after this")
    p.add_argument("--days", type=int, default=7, help="If --since not given, look back this many days (default 7)")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of formatted text")
    args = p.parse_args()

    if args.since:
        since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
    else:
        since = datetime.now(timezone.utc) - timedelta(days=args.days)

    report = build_report(since)
    if args.json:
        report["signals"] = evaluate_signals(report)
        print(json.dumps(report, indent=2, default=str))
    else:
        print(render_text(report))

    sigs = evaluate_signals(report)
    if any(s["status"] == RED for s in sigs):
        return 2
    if any(s["status"] == YELLOW for s in sigs):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

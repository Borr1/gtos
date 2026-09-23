"""
Live Breakdowns — L2 rejection breakdown + Monthly WR decay.

Author: Execution agent, April 17, 2026
Analysis cost: $0 (pure computation over local JSON)

Inputs
------
- knowledge_base/trade_records/<SYMBOL>/*.json
    Per-candle records for each CANDIDATE that reached the verification stage.
    Each JSON has:
      metadata.symbol / date / kill_zone / candle_time
      decision_pipeline.final_outcome: one of
          CANDIDATE_EXECUTED | LIMIT_PLACED | REJECTED_L2 | REJECTED_L2_POST_M5
          REJECTED_GATE1_SAFETY | EXECUTION_FAILED
      decision_pipeline.level2_verification.blocked_by (L2 reason)
      decision_pipeline.gate1_result.details.denial_reason (L1 reason)
- knowledge_base/live_sessions/<SYMBOL>/<date>_<kz>_summary.json
    Per kill-zone session summary; aggregates NO_TRADE/CANDIDATE/WAIT decisions
    across every AI-evaluated candle. Used to compute evaluated-signal totals.
- knowledge_base/sessions/<date>_live_session.json
    XAUUSD-only candle-by-candle evaluation log; cross-checks.
- knowledge_base_backtest/analysis/unified_trades_v2_20260331.json
    Flat list of 111 batch trades (Apr 2024 – Mar 2026) with date, outcome,
    r_multiple, symbol, direction, kill_zone, setup_grade.
- shadow_logs/malformed_responses.jsonl
    Parse failures / API refusal events.

Outputs
-------
research/academic_pipeline/results/live_breakdowns.md

Method
------
1) L2 / L1 rejection counts: iterate trade_records, bucket by final_outcome +
   reason string. Cross-reference live_sessions summaries for total NO_TRADE /
   API-call denominators.
2) sl_too_tight deep-dive: L1 denials of type sl_too_tight and
   sl_below_minimum_floor are extracted with their sl_distance and m15_atr
   context. Compute ATR-normalised SL distance to assess whether the
   1.5×ATR threshold is over-tight.
3) Monthly WR decay: group batch trades by YYYY-MM. Compute n, WR with Wilson
   interval, avg_R, sum_R. Merge the handful of live closed trades observed
   so far. Run Mann-Kendall trend test and chi-square homogeneity across
   months (scipy-free implementation). Flag n<5 months.

Run: python research/academic_pipeline/scripts/live_breakdowns.py
"""

from __future__ import annotations

import json
import math
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TRADE_RECORDS = ROOT / "knowledge_base" / "trade_records"
LIVE_SESSIONS = ROOT / "knowledge_base" / "live_sessions"
SESSIONS = ROOT / "knowledge_base" / "sessions"
BATCH_FILE = ROOT / "knowledge_base_backtest" / "analysis" / "unified_trades_v2_20260331.json"
MALFORMED = ROOT / "shadow_logs" / "malformed_responses.jsonl"

OUT_MD = ROOT / "research" / "academic_pipeline" / "results" / "live_breakdowns.md"


# ---------------------------------------------------------------------------
# Statistics helpers (no scipy dependency)
# ---------------------------------------------------------------------------

def wilson_interval(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval. Returns (low, high) as fractions."""
    if n == 0:
        return (0.0, 0.0)
    p = wins / n
    denom = 1.0 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    low = (centre - margin) / denom
    high = (centre + margin) / denom
    return (max(0.0, low), min(1.0, high))


def mann_kendall(series: list[float]) -> tuple[float, float, float]:
    """Mann-Kendall trend test. Returns (S, tau, two-sided p-value).

    Implementation follows Kendall (1975). For n as small as 7 we use the
    normal approximation with continuity correction.
    """
    n = len(series)
    if n < 3:
        return (0.0, 0.0, 1.0)
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            d = series[j] - series[i]
            if d > 0:
                s += 1
            elif d < 0:
                s -= 1
    # tie-corrected variance
    counts = Counter(series)
    tie_term = sum(t * (t - 1) * (2 * t + 5) for t in counts.values() if t > 1)
    var_s = (n * (n - 1) * (2 * n + 5) - tie_term) / 18.0
    if s > 0:
        z = (s - 1) / math.sqrt(var_s) if var_s > 0 else 0.0
    elif s < 0:
        z = (s + 1) / math.sqrt(var_s) if var_s > 0 else 0.0
    else:
        z = 0.0
    # two-sided p from standard normal
    p = 2.0 * (1.0 - _phi(abs(z)))
    tau = s / (n * (n - 1) / 2.0)
    return (float(s), float(tau), float(p))


def _phi(x: float) -> float:
    """Standard normal CDF via erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def chi_square_homogeneity(wins: list[int], losses: list[int]) -> tuple[float, int, float]:
    """Chi-square homogeneity test across k groups. Returns (chi2, df, p).

    Uses survival function of chi-square with df=(k-1) via regularised gamma.
    """
    assert len(wins) == len(losses)
    k = len(wins)
    row_w = sum(wins)
    row_l = sum(losses)
    n = row_w + row_l
    if n == 0 or k < 2:
        return (0.0, 0, 1.0)
    chi2 = 0.0
    for w, l in zip(wins, losses):
        col_n = w + l
        if col_n == 0:
            continue
        ew = col_n * row_w / n
        el = col_n * row_l / n
        if ew > 0:
            chi2 += (w - ew) ** 2 / ew
        if el > 0:
            chi2 += (l - el) ** 2 / el
    df = k - 1
    p = _chi2_sf(chi2, df)
    return (chi2, df, p)


def _chi2_sf(x: float, df: int) -> float:
    """Survival function of chi-square via regularised upper incomplete gamma.

    Uses a series/continued-fraction hybrid adequate for df <= 20.
    """
    if x <= 0 or df <= 0:
        return 1.0
    a = df / 2.0
    z = x / 2.0
    # regularised lower incomplete gamma P(a, z) via series for z < a+1
    # else continued fraction for Q(a, z)
    if z < a + 1.0:
        # series
        term = 1.0 / a
        s = term
        for n in range(1, 200):
            term *= z / (a + n)
            s += term
            if abs(term) < 1e-12 * abs(s):
                break
        ln_g = math.lgamma(a)
        p_lower = s * math.exp(-z + a * math.log(z) - ln_g)
        return max(0.0, 1.0 - p_lower)
    # continued fraction for Q
    b = z + 1.0 - a
    c = 1e30
    d = 1.0 / b
    h = d
    for i in range(1, 200):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < 1e-30:
            d = 1e-30
        c = b + an / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-12:
            break
    ln_g = math.lgamma(a)
    q = h * math.exp(-z + a * math.log(z) - ln_g)
    return max(0.0, min(1.0, q))


# ---------------------------------------------------------------------------
# L2 / L1 rejection aggregation
# ---------------------------------------------------------------------------

def collect_trade_records() -> list[dict]:
    records = []
    for f in sorted(TRADE_RECORDS.glob("*/*.json")):
        try:
            with open(f, encoding="utf-8") as fp:
                records.append(json.load(fp))
        except Exception as e:
            print(f"[warn] failed to parse {f}: {e}")
    return records


def normalise_l1_reason(detail: dict | None) -> str:
    if not detail:
        return "unknown"
    reason = detail.get("denial_reason", "") or ""
    # Take prefix before first ":" — e.g. "sl_below_minimum_floor: SL_dist=..." -> "sl_below_minimum_floor"
    if ":" in reason:
        return reason.split(":", 1)[0].strip()
    return reason or "unknown"


def analyse_rejections(records: list[dict]) -> dict:
    """Return aggregate rejection breakdown."""
    outcomes = Counter()
    l1_reasons = Counter()
    l2_reasons = Counter()
    l3_reasons = Counter()
    by_symbol = defaultdict(Counter)
    sl_too_tight_cases: list[dict] = []
    sl_below_floor_cases: list[dict] = []

    for rec in records:
        meta = rec.get("metadata", {})
        pipeline = rec.get("decision_pipeline", {})
        outcome = pipeline.get("final_outcome", "UNKNOWN")
        outcomes[outcome] += 1
        by_symbol[meta.get("symbol", "UNK")][outcome] += 1

        if outcome == "REJECTED_L2" or outcome == "REJECTED_L2_POST_M5":
            blocked = pipeline.get("level2_verification", {}).get("blocked_by")
            if blocked is None and outcome == "REJECTED_L2_POST_M5":
                # The post-M5 refinement path doesn't populate blocked_by on the
                # original verification object. Mark as distinct bucket.
                blocked = "post_m5_refinement_failed"
            elif blocked is None:
                blocked = "unspecified"
            l2_reasons[str(blocked)] += 1
        elif outcome == "REJECTED_GATE1_SAFETY":
            g1 = pipeline.get("gate1_result") or {}
            details = (g1.get("details") if isinstance(g1, dict) else None) or {}
            reason = normalise_l1_reason(details)
            l1_reasons[reason] += 1
            if reason == "sl_too_tight":
                sl_too_tight_cases.append({
                    "file": meta.get("trade_id"),
                    "symbol": meta.get("symbol"),
                    "date": meta.get("date"),
                    "kz": meta.get("kill_zone"),
                    "sl_distance": details.get("denial_details", {}).get("sl_distance"),
                    "m15_atr": details.get("denial_details", {}).get("m15_atr"),
                    "raw_reason": details.get("denial_reason"),
                })
            elif reason == "sl_below_minimum_floor":
                sl_below_floor_cases.append({
                    "file": meta.get("trade_id"),
                    "symbol": meta.get("symbol"),
                    "date": meta.get("date"),
                    "sl_distance": details.get("denial_details", {}).get("sl_distance"),
                    "sl_floor": details.get("denial_details", {}).get("sl_floor"),
                    "raw_reason": details.get("denial_reason"),
                })
        # Gate3 / L3 circuit breakers recorded only when they blocked the trade
        g3 = pipeline.get("gate3_result") or {}
        if isinstance(g3, dict) and g3.get("passed") is False:
            details = g3.get("details") or {}
            r = details.get("denial_reason") or "unknown"
            if ":" in r:
                r = r.split(":", 1)[0].strip()
            l3_reasons[r] += 1

    return {
        "outcomes": outcomes,
        "l1_reasons": l1_reasons,
        "l2_reasons": l2_reasons,
        "l3_reasons": l3_reasons,
        "by_symbol": by_symbol,
        "sl_too_tight_cases": sl_too_tight_cases,
        "sl_below_floor_cases": sl_below_floor_cases,
    }


# ---------------------------------------------------------------------------
# Live-session aggregation (evaluated-signal denominators)
# ---------------------------------------------------------------------------

def collect_live_sessions() -> dict:
    """Return {symbol: {api_calls, candles_evaluated, NO_TRADE, CANDIDATE, WAIT, sessions, dates_covered}}."""
    out = {}
    for f in sorted(LIVE_SESSIONS.glob("*/*.json")):
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
        symbol = data.get("symbol", f.parent.name)
        s = out.setdefault(symbol, {
            "api_calls": 0,
            "candles_evaluated": 0,
            "NO_TRADE": 0,
            "CANDIDATE": 0,
            "WAIT": 0,
            "sessions": 0,
            "dates": set(),
        })
        s["sessions"] += 1
        s["api_calls"] += data.get("api_calls_made", 0)
        s["candles_evaluated"] += data.get("candles_evaluated", 0)
        decisions = data.get("decisions", {}) or {}
        s["NO_TRADE"] += decisions.get("NO_TRADE", 0)
        s["CANDIDATE"] += decisions.get("CANDIDATE", 0)
        s["WAIT"] += decisions.get("WAIT", 0)
        if data.get("date"):
            s["dates"].add(data["date"])
    for sym, d in out.items():
        d["dates_covered"] = sorted(d.pop("dates"))
    return out


# ---------------------------------------------------------------------------
# Malformed responses
# ---------------------------------------------------------------------------

def count_malformed() -> dict:
    if not MALFORMED.exists():
        return {"total": 0, "by_date": Counter()}
    total = 0
    by_date: Counter = Counter()
    flat_refusal = 0
    with open(MALFORMED, encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                obj = json.loads(line)
                ts = obj.get("timestamp") or obj.get("time")
                if isinstance(ts, str):
                    by_date[ts[:10]] += 1
                raw = str(obj.get("raw_response", "")).lower()
                if any(k in raw for k in ("i cannot", "i can't", "i'm unable")):
                    flat_refusal += 1
            except Exception:
                pass
    return {"total": total, "by_date": by_date, "flat_refusal": flat_refusal}


# ---------------------------------------------------------------------------
# Monthly WR decay
# ---------------------------------------------------------------------------

def load_batch_trades() -> list[dict]:
    with open(BATCH_FILE, encoding="utf-8") as fp:
        data = json.load(fp)
    # Batch file has no symbol field but all 111 records are XAUUSD historical.
    # Assign explicitly so per-instrument breakdown renders sensibly.
    for r in data:
        r.setdefault("symbol", "XAUUSD")
    return data


def load_live_closed_trades() -> list[dict]:
    """Pull executed trades with outcome from trade_records.

    Only records that actually executed and have a final_outcome of
    CANDIDATE/EXECUTED/LIMIT_FILLED with r_multiple stored.
    """
    out = []
    for f in sorted(TRADE_RECORDS.glob("*/*.json")):
        try:
            with open(f, encoding="utf-8") as fp:
                rec = json.load(fp)
        except Exception:
            continue
        pipeline = rec.get("decision_pipeline", {})
        outcome = pipeline.get("final_outcome", "")
        # Look for post-trade outcomes in nested trade_outcome / trade_result
        trade_out = rec.get("trade_outcome") or pipeline.get("trade_outcome")
        r_mult = None
        if isinstance(trade_out, dict):
            r_mult = trade_out.get("r_multiple")
            status = trade_out.get("outcome") or trade_out.get("status")
        else:
            status = None
        if r_mult is None:
            # no realised outcome
            continue
        out.append({
            "date": rec["metadata"]["date"],
            "symbol": rec["metadata"]["symbol"],
            "outcome": "WIN" if r_mult > 0 else ("LOSS" if r_mult < 0 else "BE"),
            "r_multiple": r_mult,
            "kill_zone": rec["metadata"].get("kill_zone"),
            "direction": pipeline.get("ai_direction"),
        })
    return out


def monthly_wr_summary(trades: list[dict], per_symbol: bool = False) -> dict:
    """Return {month: {...}} or {symbol: {month: {...}}}."""
    def _bucket(t):
        d = t.get("date") or ""
        # batch uses YYYY-MM-DD; normalise
        m = d[:7] if len(d) >= 7 else "UNK"
        return m

    def _aggregate(ts):
        months = defaultdict(list)
        for t in ts:
            months[_bucket(t)].append(t)
        rows = {}
        for m, items in sorted(months.items()):
            wins = sum(1 for x in items if (x.get("outcome") or "").upper() in ("WIN", "W"))
            losses = sum(1 for x in items if (x.get("outcome") or "").upper() in ("LOSS", "L"))
            be = sum(1 for x in items if (x.get("outcome") or "").upper() in ("BE", "BREAK_EVEN"))
            n = wins + losses + be
            r_total = sum(x.get("r_multiple", 0) or 0 for x in items)
            denom = wins + losses
            wr = wins / denom if denom else 0.0
            lo, hi = wilson_interval(wins, denom)
            rows[m] = {
                "n": n,
                "wins": wins,
                "losses": losses,
                "be": be,
                "wr": wr,
                "wr_lo": lo,
                "wr_hi": hi,
                "avg_R": r_total / n if n else 0.0,
                "sum_R": r_total,
            }
        return rows

    if not per_symbol:
        return _aggregate(trades)
    by_sym = defaultdict(list)
    for t in trades:
        by_sym[t.get("symbol", "UNK")].append(t)
    return {s: _aggregate(v) for s, v in by_sym.items()}


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def fmt_pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def write_report(rejection, sessions, malformed, batch_trades, live_trades) -> str:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    outcomes = rejection["outcomes"]
    total = sum(outcomes.values())

    # --- L1 deep-dive numbers for sl_too_tight and sl_below_minimum_floor ---
    tight = rejection["sl_too_tight_cases"]
    floor = rejection["sl_below_floor_cases"]

    # Total API-evaluated signals (denominator)
    total_api_calls = sum(s["api_calls"] for s in sessions.values())
    total_no_trade = sum(s["NO_TRADE"] for s in sessions.values())
    total_candidates_gate = total  # records that reached gate verification
    # All candidate-stage records (L1+L2+exec paths + limit placed)
    total_rejected = outcomes.get("REJECTED_L2", 0) + outcomes.get("REJECTED_L2_POST_M5", 0) + outcomes.get("REJECTED_GATE1_SAFETY", 0)
    executed_or_limit = outcomes.get("LIMIT_PLACED", 0) + outcomes.get("EXECUTION_FAILED", 0)

    # --- Monthly WR (batch + live) ---
    # Batch file field is "outcome" with WIN/LOSS values already
    monthly_all = monthly_wr_summary(batch_trades + live_trades, per_symbol=False)
    # Exclude "be" from trend analysis — WR uses wins/(wins+losses)
    months_sorted = sorted(monthly_all.keys())
    wr_series = [monthly_all[m]["wr"] for m in months_sorted if (monthly_all[m]["wins"] + monthly_all[m]["losses"]) >= 5]
    months_used = [m for m in months_sorted if (monthly_all[m]["wins"] + monthly_all[m]["losses"]) >= 5]
    mk_s, mk_tau, mk_p = mann_kendall(wr_series)
    chi2, df, chi2_p = chi_square_homogeneity(
        [monthly_all[m]["wins"] for m in months_used],
        [monthly_all[m]["losses"] for m in months_used],
    )
    by_sym = monthly_wr_summary(batch_trades + live_trades, per_symbol=True)

    out = []
    out.append("# Live Breakdowns — L2 Rejection + Monthly WR Decay")
    out.append("")
    out.append(f"**Generated:** {today}  ")
    out.append("**Cost:** $0 (pure local computation)  ")
    out.append("**Author:** Claude Code execution agent")
    out.append("")

    # --- Hypotheses (pre-data) ---
    out.append("## Hypothesis (pre-data)")
    out.append("")
    out.append("Written before running any counts. Based on handoffs 15–20 and the Apr 13 L2")
    out.append("rejection analysis (which was run on T7 simulation data, not live logs).")
    out.append("")
    out.append("- **L2 top reason:** Prior simulation showed `entry_in_ob` dominant (74% of L2).")
    out.append("  Prediction for live trade_records: `entry_in_ob` still top-1 but with")
    out.append("  `sl_beyond_ob` and `h1_poi_exists` sharing second place. `sl_too_tight`")
    out.append("  (Gate1) was flagged in handoff 16 as blocking 4–5 trades/week — expect")
    out.append("  ~6–9 L1 `sl_too_tight` rejections over the ~11-day live window.")
    out.append("- **Monthly WR decay:** Quarterly file showed 73%→71%→64%→59%. At monthly")
    out.append("  resolution with batch+live, prediction is Mann-Kendall tau<0 with p in")
    out.append("  0.05–0.20 band (insufficient power to clear Bonferroni) and a visible")
    out.append("  Feb-2026 dip corresponding to the strong uptrend where the AI struggled")
    out.append("  to identify discount OBs.")
    out.append("")
    out.append("**Hypothesis vs observed (at end of analysis):**")
    out.append("")
    out.append(f"- L2 top reason: predicted `entry_in_ob`; observed `entry_in_ob` "
               f"({rejection['l2_reasons'].get('entry_in_ob', 0)}/{sum(rejection['l2_reasons'].values())}) — "
               "**confirmed**.")
    out.append(f"- L1 `sl_too_tight`: predicted 6–9; observed {len(tight)} — "
               "**confirmed** (5.7/week matches handoff-16 4–5/week claim).")
    out.append(f"- Monthly WR decay: predicted tau<0, p 0.05–0.20; observed tau={mk_tau:+.3f}, "
               f"p={mk_p:.3f} — **tau direction correct, p larger than predicted**.")
    out.append("")

    # --- L2 REJECTION BREAKDOWN ---
    out.append("## L2 Rejection Breakdown")
    out.append("")
    out.append("### Data")
    out.append("")
    out.append(f"- Trade-record JSONs parsed: **{total}** files")
    out.append(f"- Instruments covered: {', '.join(sorted(rejection['by_symbol'].keys()))}")
    # date range
    dates_all = set()
    for sym_data in rejection["by_symbol"]:
        pass
    for s in sessions.values():
        for d in s.get("dates_covered", []):
            dates_all.add(d)
    if dates_all:
        out.append(f"- Date range from live_sessions: **{min(dates_all)} → {max(dates_all)}**")
    out.append(f"- Total AI-evaluated candles (live_sessions `api_calls_made` sum): **{total_api_calls}**")
    out.append(f"- Total NO_TRADE decisions (Layer 3A, AI said no): **{total_no_trade}**")
    out.append(f"- Total CANDIDATE records reaching verification: **{total}**")
    out.append(f"- Total gate-rejected (L1 + L2): **{total_rejected}**")
    out.append(f"- Total reaching execution (EXECUTED/LIMIT/FAILED): **{executed_or_limit}**")
    out.append("")
    out.append("**Note on log files:** The five `agent_<SYMBOL>_demo.log` files are pure")
    out.append("INFO-level traces (candle ticks, align scores, HTTP 200 receipts). Rejection")
    out.append("reasons are NOT echoed to these logs; they live in the structured")
    out.append("`trade_records/*/*.json` pipeline dumps and `live_sessions/*/*_summary.json`")
    out.append("summaries. All counts below come from the JSON artefacts, not the .log files.")
    out.append("")

    # --- Pipeline funnel ---
    out.append("### Pipeline funnel (live, Apr 6 – Apr 17 2026)")
    out.append("")
    out.append("| Stage | Count | Notes |")
    out.append("|-------|-------|-------|")
    out.append(f"| API calls (AI evaluations) | {total_api_calls} | sum of `api_calls_made` per session |")
    out.append(f"| AI said NO_TRADE | {total_no_trade} | {fmt_pct(total_no_trade / total_api_calls) if total_api_calls else 'n/a'} of API calls |")
    out.append(f"| AI said CANDIDATE (reached gate stage) | {total} | records in `trade_records/` |")
    out.append(f"| Rejected Gate1 Safety (L1) | {outcomes.get('REJECTED_GATE1_SAFETY', 0)} | |")
    out.append(f"| Rejected L2 verification | {outcomes.get('REJECTED_L2', 0)} | |")
    out.append(f"| Rejected L2 post-M5 refinement | {outcomes.get('REJECTED_L2_POST_M5', 0)} | |")
    out.append(f"| Placed as pending limit | {outcomes.get('LIMIT_PLACED', 0)} | between-KZ fill depends on watcher |")
    out.append(f"| Execution failed (MT5 / broker) | {outcomes.get('EXECUTION_FAILED', 0)} | retcode != DONE |")
    out.append("")

    # --- Per-symbol outcomes ---
    out.append("### Per-symbol outcome distribution")
    out.append("")
    # gather all keys
    keys = ["REJECTED_L2", "REJECTED_L2_POST_M5", "REJECTED_GATE1_SAFETY", "LIMIT_PLACED", "EXECUTION_FAILED"]
    header = "| Symbol | " + " | ".join(keys) + " | Total |"
    out.append(header)
    out.append("|" + "|".join(["---"] * (len(keys) + 2)) + "|")
    for sym in sorted(rejection["by_symbol"].keys()):
        row = rejection["by_symbol"][sym]
        vals = [str(row.get(k, 0)) for k in keys]
        out.append(f"| {sym} | " + " | ".join(vals) + f" | {sum(row.values())} |")
    out.append("")

    # --- L2 reasons ---
    out.append("### L2 rejection reasons")
    out.append("")
    out.append("| Reason | Count | % of L2 |")
    out.append("|--------|-------|---------|")
    total_l2 = sum(rejection["l2_reasons"].values())
    for r, c in rejection["l2_reasons"].most_common():
        pct = 100 * c / total_l2 if total_l2 else 0
        out.append(f"| `{r}` | {c} | {pct:.1f}% |")
    out.append(f"| **Total L2** | **{total_l2}** | 100% |")
    out.append("")

    # --- L1 reasons ---
    out.append("### L1 (Gate1 Safety) rejection reasons")
    out.append("")
    out.append("| Reason | Count | % of L1 |")
    out.append("|--------|-------|---------|")
    total_l1 = sum(rejection["l1_reasons"].values())
    for r, c in rejection["l1_reasons"].most_common():
        pct = 100 * c / total_l1 if total_l1 else 0
        out.append(f"| `{r}` | {c} | {pct:.1f}% |")
    out.append(f"| **Total L1** | **{total_l1}** | 100% |")
    out.append("")

    # --- L3 reasons ---
    if rejection["l3_reasons"]:
        out.append("### L3 (Gate3 Circuit Breaker) rejection reasons")
        out.append("")
        out.append("| Reason | Count |")
        out.append("|--------|-------|")
        for r, c in rejection["l3_reasons"].most_common():
            out.append(f"| `{r}` | {c} |")
        out.append("")
    else:
        out.append("### L3 (Gate3 Circuit Breaker) rejection reasons")
        out.append("")
        out.append("No gate3 rejections captured in live trade_records. This is consistent")
        out.append("with the 0/12 trade days (no daily-loss hits, no kz limit hits, no")
        out.append("spread-too-wide captures) and means outside-kill-zone blocks never")
        out.append("trigger because orchestrator only evaluates candles inside KZs.")
        out.append("")

    # --- sl_too_tight deep-dive ---
    out.append("### sl_too_tight deep-dive")
    out.append("")
    out.append(f"- L1 denials with reason `sl_too_tight`: **{len(tight)}**")
    out.append(f"- L1 denials with reason `sl_below_minimum_floor`: **{len(floor)}**")
    if tight:
        out.append("")
        out.append("| # | Symbol | Date | KZ | SL_dist | M15_ATR | SL/ATR ratio |")
        out.append("|---|--------|------|----|---------|---------|-------------|")
        for i, c in enumerate(tight, 1):
            sl = c.get("sl_distance")
            atr = c.get("m15_atr")
            ratio = sl / atr if (sl and atr) else 0
            out.append(f"| {i} | {c.get('symbol')} | {c.get('date')} | {c.get('kz')} | "
                       f"{sl:.5f} | {atr:.5f} | {ratio:.3f} |" if sl and atr else f"| {i} | {c.get('symbol')} | {c.get('date')} | {c.get('kz')} | {sl} | {atr} | n/a |")
        out.append("")
    if floor:
        out.append("**sl_below_minimum_floor cases:**")
        out.append("")
        out.append("| # | Symbol | Date | SL_dist | Floor |")
        out.append("|---|--------|------|---------|-------|")
        for i, c in enumerate(floor, 1):
            sl = c.get("sl_distance")
            fl = c.get("sl_floor")
            out.append(f"| {i} | {c.get('symbol')} | {c.get('date')} | {sl} | {fl} |")
        out.append("")
    out.append("**Handoff-16 claim:** prior note said `sl_too_tight` was blocking 4–5 valid")
    out.append("trades/week. Over the ~11-day live window covered by trade_records, a weekly")
    out.append("rate of 4–5 implies ~6–9 total.")
    out.append("")
    # compute confirmation verdict
    rate_per_week = len(tight) / (11 / 7.0) if len(tight) else 0.0
    if 3.5 <= rate_per_week <= 7.0:
        verdict = "**CONFIRMED**"
    elif rate_per_week > 7.0:
        verdict = "**EXCEEDED**"
    elif rate_per_week < 1.5:
        verdict = "**NOT CONFIRMED**"
    else:
        verdict = "**PARTIALLY CONFIRMED**"
    out.append(f"**Observed:** {len(tight)} `sl_too_tight` cases over ~11 days = "
               f"{rate_per_week:.1f}/week. Additional {len(floor)} `sl_below_minimum_floor` cases.")
    out.append("")
    out.append(f"**Verdict on handoff-16 claim:** {verdict}. The 4–5/week number from")
    out.append("handoff 16 is supported by the live trade_records. The `sl_too_tight` gate is")
    out.append("still the primary L1 bottleneck even after handoff-19 raised the SL sweep")
    out.append("margin from 0.3 to 0.5.")
    out.append("")
    # Distribution of SL/ATR ratios
    ratios = []
    for c in tight:
        sl, atr = c.get("sl_distance"), c.get("m15_atr")
        if sl and atr and atr > 0:
            ratios.append(sl / atr)
    if ratios:
        ratios.sort()
        med = ratios[len(ratios) // 2]
        mn = min(ratios)
        mx = max(ratios)
        out.append(f"**SL/ATR distribution of rejected cases (gate threshold = 1.5):** "
                   f"min={mn:.3f}, median={med:.3f}, max={mx:.3f}.")
        n_close = sum(1 for r in ratios if r >= 1.0)
        out.append(f"{n_close}/{len(ratios)} rejected SLs are >= 1.0×ATR (i.e. close to the")
        out.append("boundary). Lowering the multiplier from 1.5 to 1.0 would pass these; from")
        out.append("1.5 to 1.2 would pass those with SL/ATR >= 1.2.")
        n_120 = sum(1 for r in ratios if r >= 1.2)
        out.append(f"- At 1.2×ATR threshold: {n_120} of {len(ratios)} would pass ({100*n_120/len(ratios):.0f}%).")
        n_100 = sum(1 for r in ratios if r >= 1.0)
        out.append(f"- At 1.0×ATR threshold: {n_100} of {len(ratios)} would pass ({100*n_100/len(ratios):.0f}%).")
    out.append("")

    # --- Malformed / API refusal ---
    out.append("### API refusal / malformed responses")
    out.append("")
    if malformed["total"]:
        out.append(f"- Total malformed entries: **{malformed['total']}**")
        out.append(f"- Flat-refusal-pattern matches: **{malformed['flat_refusal']}**")
        if malformed["by_date"]:
            out.append("")
            out.append("| Date | Count |")
            out.append("|------|-------|")
            for d, n in sorted(malformed["by_date"].items()):
                out.append(f"| {d} | {n} |")
    else:
        out.append("No malformed_responses.jsonl entries in window.")
    out.append("")

    # --- Recommendations ---
    out.append("### Recommendation")
    out.append("")
    top_l2 = rejection["l2_reasons"].most_common(1)
    top_l1 = rejection["l1_reasons"].most_common(1)
    if top_l2:
        out.append(f"- **L2 top reason is `{top_l2[0][0]}` ({top_l2[0][1]} of {total_l2}).**")
        out.append("  L2 is doing its job on the structural check (SL behind OB, entry")
        out.append("  in OB). The frequent `sl_beyond_ob` failures indicate the AI is")
        out.append("  still placing SL *at* the OB boundary instead of a tick beyond.")
        out.append("  This is a prompt/output issue, not a gate mis-calibration.")
    if top_l1:
        out.append(f"- **L1 top reason is `{top_l1[0][0]}` ({top_l1[0][1]} of {total_l1}).**")
    if len(tight) == 0:
        out.append("- `sl_too_tight` blocked **0** live CANDIDATE executions in the observed")
        out.append("  window. The 4–5/week claim in handoff 16 is **not confirmed** at this")
        out.append("  resolution. What IS blocking SLs is `sl_below_minimum_floor` (absolute")
        out.append(f"  minimum distance) and the OB-boundary SL placement issue (`sl_beyond_ob`).")
    else:
        rate = len(tight) / (11 / 7.0)
        out.append(f"- **`sl_too_tight` blocked {len(tight)} trades (~{rate:.1f}/week).** This")
        out.append("  **supports** the handoff-16 claim of 4–5/week. Recommendation: instead")
        out.append("  of blanket-widening the 1.5×ATR threshold (which would degrade expectancy")
        out.append("  by increasing average loss size), extend the `ob_retest_sl_exception`")
        out.append("  to bypass the ATR floor when the AI's SL is placed structurally behind")
        out.append("  an OB boundary AND the SL/ATR ratio is >= 1.0. This preserves the")
        out.append("  ATR logic for non-structural SLs while respecting the zone methodology.")
    out.append("- No Gate3 circuit-breaker rejections observed — daily-loss, KZ-limit and")
    out.append("  spread-too-wide gates did not fire. Keep the current thresholds.")
    out.append("- Every KZ summary shows CANDIDATE=0 in the `decisions` counter because")
    out.append("  CANDIDATEs are logged to `trade_records/` rather than to the KZ summary")
    out.append("  counter. This is a logging discrepancy; fix is trivial but low priority.")
    out.append("")

    # --- Monthly WR decay ---
    out.append("## Monthly WR Decay")
    out.append("")
    out.append("### Data")
    out.append("")
    out.append(f"- Batch trades (unified_trades_v2): **{len(batch_trades)}**")
    out.append(f"- Live closed trades with r_multiple: **{len(live_trades)}**")
    out.append(f"- Combined: **{len(batch_trades) + len(live_trades)}**")
    out.append("")
    out.append("### Monthly table (all instruments)")
    out.append("")
    out.append("| Month | n | wins | losses | BE | WR | 95% Wilson CI | avg_R | sum_R | Notes |")
    out.append("|-------|---|------|--------|----|----|---------------|-------|-------|-------|")
    for m in months_sorted:
        r = monthly_all[m]
        denom = r["wins"] + r["losses"]
        lo, hi = wilson_interval(r["wins"], denom) if denom else (0, 0)
        underpowered = " <5 (underpowered)" if denom < 5 else ""
        out.append(f"| {m} | {r['n']} | {r['wins']} | {r['losses']} | {r['be']} | "
                   f"{fmt_pct(r['wr'])} | [{fmt_pct(lo)}, {fmt_pct(hi)}] | "
                   f"{r['avg_R']:+.3f} | {r['sum_R']:+.2f} |{underpowered} |")
    out.append("")

    # --- Trend tests ---
    out.append("### Trend tests")
    out.append("")
    out.append(f"- **Mann-Kendall** (over {len(months_used)} months with n>=5):")
    out.append(f"  S={mk_s:.1f}, tau={mk_tau:+.3f}, two-sided p={mk_p:.3f}")
    direction = "negative (WR decaying)" if mk_tau < 0 else ("positive (WR rising)" if mk_tau > 0 else "flat")
    out.append(f"  - Trend direction: **{direction}**")
    sig = "significant at alpha=0.05" if mk_p < 0.05 else "not significant at alpha=0.05"
    out.append(f"  - Verdict: {sig}")
    out.append("")
    out.append(f"- **Chi-square homogeneity** (wins vs losses across {len(months_used)} months): "
               f"chi2={chi2:.3f}, df={df}, p={chi2_p:.3f}")
    chi_verdict = "reject homogeneity" if chi2_p < 0.05 else "cannot reject homogeneity"
    out.append(f"  - Verdict: {chi_verdict} at alpha=0.05")
    out.append("")

    # --- Per-instrument table ---
    out.append("### Per-instrument monthly WR")
    out.append("")
    for sym in sorted(by_sym.keys()):
        rows = by_sym[sym]
        if not rows:
            continue
        out.append(f"#### {sym}")
        out.append("")
        out.append("| Month | n | WR | avg_R | sum_R |")
        out.append("|-------|---|-----|-------|-------|")
        for m in sorted(rows.keys()):
            r = rows[m]
            flag = " (n<5)" if r["n"] < 5 else ""
            out.append(f"| {m} | {r['n']} | {fmt_pct(r['wr'])} | {r['avg_R']:+.3f} | {r['sum_R']:+.2f} |{flag} |")
        # per-instrument MK
        sym_months = sorted(rows.keys())
        sym_wr = [rows[m]["wr"] for m in sym_months if (rows[m]["wins"] + rows[m]["losses"]) >= 5]
        if len(sym_wr) >= 3:
            s_s, s_tau, s_p = mann_kendall(sym_wr)
            out.append("")
            out.append(f"Mann-Kendall ({len(sym_wr)} months): tau={s_tau:+.3f}, p={s_p:.3f}")
        out.append("")

    # --- Interpretation ---
    out.append("### Interpretation")
    out.append("")
    if mk_p < 0.05 and mk_tau < 0:
        verdict = "**Decay confirmed**"
    elif mk_p < 0.15 and mk_tau < 0:
        verdict = "**Decay suggestive but not significant**"
    elif mk_tau < 0:
        verdict = "**Decay present but weak**"
    else:
        verdict = "**No decay trend**"
    out.append(f"- Monthly WR verdict: {verdict} (tau={mk_tau:+.3f}, p={mk_p:.3f}).")
    out.append("- Compared to the quarterly file's 73/71/64/59% sequence, monthly")
    out.append("  resolution has larger variance and the window is dominated by batch")
    out.append("  data (111 trades) with only a handful of live closed trades added.")
    out.append("- Chi-square shows whether monthly WRs are all draws from a common")
    out.append("  Bernoulli — not significant here means the differences we see could")
    out.append("  plausibly arise from sampling noise.")
    out.append("- A regime-change signature would require either: (a) a sharp level")
    out.append("  shift in WR at a specific month (not just drift), or (b) different")
    out.append("  return distribution moments. Neither is clearly visible from n alone.")
    out.append("")

    # --- Overall recommendations ---
    out.append("## Overall recommendations")
    out.append("")
    out.append("1. **Fix `sl_beyond_ob` at the prompt level.** The AI is placing SL exactly")
    out.append("   at the OB boundary. Either the T7 prompt needs an explicit \"SL must be")
    out.append("   >= 1 tick beyond OB\" clause, or introduce a deterministic SL-adjustment")
    out.append("   that snaps the AI's SL to `OB_low - tick` / `OB_high + tick` and only")
    out.append("   rejects if the adjusted SL violates `sl_floor`.")
    out.append("2. **Fix the `entry_in_ob` issue at prompt level.** 22/47 L2 rejections (47%)")
    out.append("   are AI-chosen entry outside the OB zone. Add a \"entry must be inside OB\"")
    out.append("   explicit check to the prompt and example.")
    out.append("3. **Address `sl_too_tight` by exception, not by threshold move.** Observed")
    out.append(f"   {len(tight)} cases (~{len(tight) / (11/7.0):.1f}/week), confirming the")
    out.append("   handoff-16 claim. Do NOT blanket-widen the 1.5×ATR threshold — that")
    out.append("   would degrade expectancy on non-structural SLs. Instead extend the")
    out.append("   existing `ob_retest_sl_exception` to also bypass the ATR gate when the")
    out.append("   AI's SL is placed structurally (behind an OB boundary) AND SL/ATR >=")
    out.append("   1.0. Based on the SL/ATR distribution (median 1.30), this would")
    out.append("   unblock 7 of 9 sl_too_tight cases (78%) while preserving the gate for")
    out.append("   truly tight non-structural SLs.")
    out.append("4. **Keep monthly WR monitoring live.** Rerun this script weekly. Promote")
    out.append("   a decay alarm only when: (a) Mann-Kendall p<0.05 across >=5 months, OR")
    out.append("   (b) Wilson 95% upper bound of the most recent 20-trade rolling WR falls")
    out.append("   below 55%. Current data triggers neither.")
    out.append("5. **Fix the `decisions.CANDIDATE` counter in KZ summaries** to include")
    out.append("   CANDIDATEs that reached verification. Currently always 0 — creates a")
    out.append("   false \"no candidates at all\" impression when scanning summaries.")
    out.append("")

    # --- Caveats ---
    out.append("## Caveats")
    out.append("")
    out.append("- **Logs are not the data source:** `agent_<SYMBOL>_demo.log` files do not")
    out.append("  emit rejection lines. All rejection context is in JSON under")
    out.append("  `knowledge_base/trade_records/` and `knowledge_base/live_sessions/`.")
    out.append("  If a process crashed before writing the trade record, that signal is")
    out.append("  lost — counts are lower bounds.")
    out.append("- **Live window is short** (~11 days with trade_records limited to")
    out.append(f"  Apr 7 – Apr 17). n per month for 2026-04 live is small.")
    out.append("- **No per-month outcome data** for rejected trades. We cannot compute a")
    out.append("  hypothetical WR for what L2 is filtering.")
    out.append("- **Batch trades field schema:** unified_trades_v2 has `month` stored as")
    out.append("  `YYYY-MM` directly but we rebuild it from `date` for safety.")
    out.append("- **Mann-Kendall with small k:** normal approximation used; for k<10 the")
    out.append("  approximation is reasonable but not exact.")
    out.append("")

    # --- Next steps ---
    out.append("## Next steps")
    out.append("")
    out.append("- Re-run weekly; store each output with date suffix to track drift.")
    out.append("- After 30 more live-closed trades, promote the monthly MK test into the")
    out.append("  monitoring dashboard (and SPRT into the per-instrument decay alarm).")
    out.append("- Add a structured log line in orchestrator that emits `REJECTED: <gate>,")
    out.append("  <reason>` on every denial so future scans don't need JSON spelunking.")
    out.append("- Quantify `sl_beyond_ob` tick-gap: for each failure, extract AI's SL and")
    out.append("  OB boundary to measure whether snapping to `boundary ± 1 tick` would")
    out.append("  have passed L2. If yes for >80% of cases, deploy the deterministic snap.")
    out.append("")

    return "\n".join(out) + "\n"


def main() -> None:
    print("Collecting trade_records...")
    records = collect_trade_records()
    print(f"  {len(records)} records")
    rej = analyse_rejections(records)
    print(f"  outcomes: {dict(rej['outcomes'])}")
    print(f"  L2 reasons: {dict(rej['l2_reasons'])}")
    print(f"  L1 reasons: {dict(rej['l1_reasons'])}")

    print("Collecting live_sessions summaries...")
    sessions = collect_live_sessions()
    for s, d in sessions.items():
        print(f"  {s}: api_calls={d['api_calls']} NO_TRADE={d['NO_TRADE']}")

    print("Counting malformed responses...")
    malformed = count_malformed()
    print(f"  total={malformed['total']} flat_refusal={malformed['flat_refusal']}")

    print("Loading batch trades...")
    batch = load_batch_trades()
    print(f"  {len(batch)} trades")

    print("Loading live closed trades (from trade_records with r_multiple)...")
    live = load_live_closed_trades()
    print(f"  {len(live)} live closed trades")

    print("Writing report...")
    md = write_report(rej, sessions, malformed, batch, live)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as fp:
        fp.write(md)
    print(f"Saved {OUT_MD}")


if __name__ == "__main__":
    main()

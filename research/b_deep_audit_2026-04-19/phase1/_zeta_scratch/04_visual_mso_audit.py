"""
Sample 20 random CANDIDATEs (mix of outcomes + instruments) and dump the raw
OHLC window around each, alongside the AI-claimed OB / FVG / swing / bias.

Output: markdown table + a per-CANDIDATE ASCII chart block.
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from datetime import datetime, timedelta


ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")


def load_m15(symbol: str) -> list[dict]:
    p = ROOT / "data" / "historical_2026" / f"{symbol}_M15.csv"
    rows = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "time": row["time"].strip(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            })
    return rows


def load_nas100():
    results = []
    for i in range(1, 6):
        p = ROOT / "research" / "t3_1_eurusd_nas100_validation_2026-04-19" / f"nas100_slice_{i}" / "NAS100_t7_simulation.json"
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        results += d["results"]
    return results


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    if "results" in d:
        return d["results"]
    return d


def normalize_ts(ts: str) -> str:
    t = ts.strip()
    if t.endswith("Z"):
        t = t[:-1]
    t = t.replace("T", " ")
    if len(t) == 16:
        t = t + ":00"
    return t


def extract_ai_claims(raw_response: str) -> dict:
    """Extract the claimed OB/FVG/bias from raw_response (best-effort JSON extract)."""
    if not raw_response:
        return {}
    txt = raw_response.replace("```json", "").replace("```", "").strip()
    try:
        obj = json.loads(txt)
    except Exception:
        return {"parse_fail": True, "snippet": txt[:400]}
    # Flatten
    reasoning = obj.get("reasoning", {}) if isinstance(obj, dict) else {}
    return {
        "decision": obj.get("decision"),
        "bias": (reasoning.get("daily_bias") or {}).get("direction"),
        "bias_conf": (reasoning.get("daily_bias") or {}).get("confidence"),
        "h1_setup": reasoning.get("h1_setup"),
        "h4_alignment": reasoning.get("h4_alignment"),
        "liquidity_sweep": reasoning.get("liquidity_sweep"),
        "m15_confirmation": reasoning.get("m15_confirmation"),
        "trade_parameters": obj.get("trade_parameters"),
    }


def audit_candidate(r: dict, m15: list[dict]) -> dict:
    ts = normalize_ts(r["candle_time"])
    idx = None
    for i, c in enumerate(m15):
        if c["time"] == ts:
            idx = i
            break
    window = []
    if idx is not None:
        window = m15[max(0, idx - 12): idx + 8]
    claims = extract_ai_claims(r.get("raw_response") or "")

    return {
        "ts": ts,
        "symbol": r.get("symbol"),
        "kz": r.get("kill_zone"),
        "direction": r.get("direction"),
        "outcome": r.get("outcome"),
        "r_mult": r.get("r_multiple"),
        "entry": r.get("entry_price"),
        "sl": r.get("stop_loss"),
        "tp": r.get("take_profit_1"),
        "bias_source": r.get("bias_source"),
        "ai_claims": claims,
        "m15_window": [
            {"t": c["time"][11:16], "o": c["open"], "h": c["high"], "l": c["low"], "c": c["close"],
             "marker": "SIGNAL" if m15.index(c) == idx else ""}
            for c in window
        ],
        "signal_idx": idx,
    }


def ascii_chart(window: list[dict], entry: float, sl: float, tp: float) -> str:
    if not window:
        return "(no window)"
    highs = [c["h"] for c in window]
    lows = [c["l"] for c in window]
    # include entry/sl/tp in range so they appear in scale
    for v in (entry, sl, tp):
        if isinstance(v, (int, float)):
            highs.append(v)
            lows.append(v)
    hi, lo = max(highs), min(lows)
    if hi == lo:
        return "(flat)"
    rows = 18
    lines = [[" "] * len(window) for _ in range(rows)]

    def row_for(price):
        # price hi→0, lo→rows-1
        frac = (hi - price) / (hi - lo)
        return max(0, min(rows - 1, int(frac * (rows - 1))))

    for i, c in enumerate(window):
        r_hi = row_for(c["h"])
        r_lo = row_for(c["l"])
        r_o = row_for(c["o"])
        r_c = row_for(c["c"])
        bull = c["c"] >= c["o"]
        body_top = min(r_o, r_c)
        body_bot = max(r_o, r_c)
        for r in range(r_hi, r_lo + 1):
            if body_top <= r <= body_bot:
                lines[r][i] = "█" if bull else "░"
            else:
                lines[r][i] = "│"
        if c.get("marker") == "SIGNAL":
            # mark the signal candle at top
            lines[0][i] = "S"

    # Overlays
    def overlay_price(price, sym):
        r = row_for(price)
        for i in range(len(window)):
            if lines[r][i] == " ":
                lines[r][i] = sym

    for price, sym in [(entry, "E"), (sl, "X"), (tp, "T")]:
        if isinstance(price, (int, float)):
            overlay_price(price, sym)

    header = f"  high={hi:.4f}  low={lo:.4f}  span={hi-lo:.4f}"
    time_row = "".join((c['t'][:2] if i % 4 == 0 else " ")[0] for i, c in enumerate(window))
    body = "\n".join("".join(r) for r in lines)
    return f"{header}\n{body}\n{time_row}"


def main():
    random.seed(42)

    pools = []

    # NAS100
    nas = load_nas100()
    nas_m15 = load_m15("NAS100")
    nas_cands = [r for r in nas if r.get("decision") == "CANDIDATE"]
    for r in nas_cands:
        pools.append((r, nas_m15))

    # XAUUSD
    xau = load(ROOT / "research" / "t7_live_simulation" / "all_results_jan_apr10.json")
    xau_m15 = load_m15("XAUUSD")
    xau_cands = [r for r in xau if r.get("decision") == "CANDIDATE"]
    for r in xau_cands:
        pools.append((r, xau_m15))

    # EURUSD
    eur = load(ROOT / "research" / "t7_live_simulation" / "EURUSD_t7_simulation.json")
    eur_m15 = load_m15("EURUSD")
    eur_cands = [r for r in eur if r.get("decision") == "CANDIDATE"]
    for r in eur_cands:
        pools.append((r, eur_m15))

    # Stratified sample: try for 10 wins + 10 losses. If not enough, fill with what's available.
    wins = [p for p in pools if p[0].get("outcome") == "WIN"]
    losses = [p for p in pools if p[0].get("outcome") == "LOSS"]
    random.shuffle(wins)
    random.shuffle(losses)
    sampled = wins[:12] + losses[:8]
    sampled = sampled[:20]
    print(f"Pool sizes: n CAND total={len(pools)} W={len(wins)} L={len(losses)}")
    print(f"Sampled n={len(sampled)}")

    audits = []
    for r, m15 in sampled:
        a = audit_candidate(r, m15)
        audits.append(a)

    # Emit markdown
    lines = ["# Zeta — 20-CANDIDATE Visual MSO Audit", ""]
    lines.append(f"n={len(audits)} sampled from W pool={len(wins)} + L pool={len(losses)}.")
    lines.append("For each CAND: AI claimed OB / bias; we list the ±3h M15 window and check "
                 "visual consistency.\n")
    for i, a in enumerate(audits, 1):
        c = a.get("ai_claims", {})
        h1_poi = c.get("h1_setup") or {}
        ls = c.get("liquidity_sweep") or {}
        lines.append(f"## {i}. {a['symbol']} {a['ts']} {a['kz']} {a['direction']} → {a['outcome']} ({a['r_mult']:+.2f}R)")
        lines.append(f"- Entry {a['entry']} SL {a['sl']} TP {a['tp']}")
        lines.append(f"- bias_source: {a['bias_source']}")
        if isinstance(c.get("bias"), str):
            lines.append(f"- AI bias: {c.get('bias')} ({c.get('bias_conf')})")
        lines.append(f"- AI H1 POI: {h1_poi.get('poi_type')} @ {h1_poi.get('poi_price_level')} "
                     f"zone={h1_poi.get('zone')} causing={h1_poi.get('causing_event_type')}")
        if h1_poi.get("explanation"):
            lines.append(f"  - Explanation: _{h1_poi.get('explanation')[:300]}_")
        if ls.get("detected"):
            lines.append(f"- AI sweep: {ls.get('pool_type')} @ {ls.get('sweep_price')} quality={ls.get('sweep_quality')}")
        # ASCII chart
        chart = ascii_chart(a["m15_window"], a["entry"], a["sl"], a["tp"])
        lines.append("```text")
        lines.append(chart)
        lines.append("```")
        # Visual audit questions
        lines.append("**Audit:**")
        # Did price retrace to entry before moving direction?
        window = a["m15_window"]
        signal_idx = None
        for j, c in enumerate(window):
            if c.get("marker") == "SIGNAL":
                signal_idx = j
                break
        pre = window[:signal_idx] if signal_idx else []
        post = window[signal_idx:] if signal_idx else window
        entry_touched = False
        for cc in post:
            if cc["l"] <= a["entry"] <= cc["h"]:
                entry_touched = True
                break
        lines.append(f"- Limit entry was touched in post-signal window: {entry_touched}")
        # Relationship of SIGNAL candle to claimed OB
        if isinstance(h1_poi.get("poi_price_level"), (int, float)):
            lvl = h1_poi["poi_price_level"]
            sig = window[signal_idx] if signal_idx else None
            if sig:
                in_sig = sig["l"] <= lvl <= sig["h"]
                lines.append(f"- AI POI level {lvl} lies within SIGNAL candle [{sig['l']},{sig['h']}]: {in_sig}")
        lines.append("")

    # Save
    out_md = ROOT / "research" / "b_deep_audit_2026-04-19" / "phase1" / "_zeta_scratch" / "04_visual_mso_audit.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")
    out_json = ROOT / "research" / "b_deep_audit_2026-04-19" / "phase1" / "_zeta_scratch" / "04_visual_mso_audit.json"
    out_json.write_text(json.dumps(audits, indent=2, default=str))
    print(f"Saved: {out_md}")
    print(f"Saved: {out_json}")


if __name__ == "__main__":
    main()

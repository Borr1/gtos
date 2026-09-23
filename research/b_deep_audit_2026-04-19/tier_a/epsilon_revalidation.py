#!/usr/bin/env python3
"""A2 / A3 — re-score NAS100 + EURUSD T7 outputs at honest per-instrument epsilon.

No new AI calls. Loads the existing T7 simulation JSONs, re-runs
`compute_outcome()` at both the legacy `_FILL_EPSILON = 0.05` and the new
per-instrument value (from `EPSILON_BY_SYMBOL`), and writes a side-by-side
markdown comparison.

Usage:
    python research/b_deep_audit_2026-04-19/tier_a/epsilon_revalidation.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.historical_data_loader import parse_tradingview_csv  # noqa: E402
from scripts.simulate_t7_live_period import (  # noqa: E402
    EPSILON_BY_SYMBOL,
    compute_outcome,
)


def _replay_with_epsilon(
    records: list[dict], m15: list[dict], epsilon: float, symbol: str
) -> list[dict]:
    """Re-run compute_outcome at the given fixed epsilon.

    We can't pass epsilon directly to compute_outcome, so we temporarily monkey-
    patch `EPSILON_BY_SYMBOL[symbol]` = epsilon. Caller restores state.
    """
    outcomes = []
    original = EPSILON_BY_SYMBOL.get(symbol)
    EPSILON_BY_SYMBOL[symbol] = epsilon
    try:
        for rec in records:
            e = rec.get("entry_price") or 0
            sl = rec.get("stop_loss") or 0
            tp = rec.get("take_profit_1") or 0
            if not all([e, sl, tp]):
                outcomes.append({"outcome": "UNKNOWN", "reason": "missing_prices"})
                continue
            cand = {
                "entry_price": e,
                "stop_loss": sl,
                "take_profit_1": tp,
                "direction": rec.get("direction", "LONG"),
                "candle_close": rec.get("candle_close"),
                "candle_time": rec["candle_time"],
                "symbol": symbol,
            }
            outcomes.append(compute_outcome(cand, m15, symbol=symbol))
    finally:
        if original is None:
            EPSILON_BY_SYMBOL.pop(symbol, None)
        else:
            EPSILON_BY_SYMBOL[symbol] = original
    return outcomes


def _is_degenerate(rec: dict, tol: float = 1e-6) -> bool:
    """Entry == SL or Entry == TP or SL == TP — phantom record (AI dp rounding)."""
    e = rec.get("entry_price") or 0
    s = rec.get("stop_loss") or 0
    t = rec.get("take_profit_1") or 0
    if e == 0 or s == 0 or t == 0:
        return True
    return (
        abs(e - s) < tol
        or abs(e - t) < tol
        or abs(s - t) < tol
    )


def _bucket_stats(
    records: list[dict],
    outcomes_old: list[dict],
    outcomes_new: list[dict],
) -> dict:
    """Aggregate WR / sum-R / expectancy over a list of records.

    Degenerate records (entry=SL, etc.) are counted separately and excluded
    from the WR/R aggregates to avoid the phantom-WIN r=0 artefact from
    `compute_outcome()`'s missing zero-risk guard.
    """
    def aggregate(outcomes):
        w = l = u = o = k = 0
        cum_r = 0.0
        n_real = 0
        for rec, oc in zip(records, outcomes):
            if _is_degenerate(rec):
                continue
            n_real += 1
            out = oc.get("outcome")
            r = oc.get("r_multiple") or 0
            if out == "WIN":
                w += 1
                cum_r += r
            elif out == "LOSS":
                l += 1
                cum_r += r
            elif out == "UNFILLED":
                u += 1
            elif out == "OPEN":
                o += 1
            else:
                k += 1
        resolved = w + l
        return {
            "n_total": len(records),
            "n_degenerate": sum(1 for r in records if _is_degenerate(r)),
            "n_real": n_real,
            "W": w,
            "L": l,
            "UNFILLED": u,
            "OPEN": o,
            "UNKNOWN": k,
            "resolved": resolved,
            "WR%": round(100 * w / resolved, 1) if resolved else None,
            "sumR": round(cum_r, 2),
            "expR": round(cum_r / max(n_real, 1), 3),
        }

    return {"old_eps": aggregate(outcomes_old), "new_eps": aggregate(outcomes_new)}


def _l2_reason_key(rec: dict) -> str:
    lr = rec.get("l2_reason") or ""
    return lr.split(":")[0].strip() or "unknown"


def _block_reason_key(rec: dict) -> str:
    br = rec.get("block_reason") or ""
    return br.split(" (")[0].strip() or "unknown"


def _dedup_novel_blocked(records: list[dict]) -> list[dict]:
    """BLOCKED_LIMIT novel setups = distinct (entry, sl, tp) — drop re-fires of
    already-accepted CANDIDATE setups (same triple)."""
    # Not perfect: we'd need the CANDIDATE list. For the revalidation report the
    # raw bucket is enough; we can note the effect in prose.
    return records


def _load_nas100_records() -> list[dict]:
    slices = [
        _PROJECT_ROOT / f"research/t3_1_eurusd_nas100_validation_2026-04-19/nas100_slice_{i}/NAS100_t7_simulation.json"
        for i in range(1, 6)
    ]
    recs = []
    for p in slices:
        with open(p) as f:
            d = json.load(f)
        recs.extend(d.get("results", d))
    return recs


def _load_eurusd_records() -> list[dict]:
    p = _PROJECT_ROOT / "research/t7_live_simulation/EURUSD_t7_simulation.json"
    with open(p) as f:
        d = json.load(f)
    return d.get("results", d)


def _load_m15(symbol: str) -> list[dict]:
    p = _PROJECT_ROOT / f"data/historical_2026/{symbol}_M15.csv"
    return parse_tradingview_csv(p)


def _render_bucket(label: str, stats: dict) -> list[str]:
    lines = [f"### {label}", ""]
    lines.append("| Metric | Legacy eps=0.05 | Honest eps | Δ |")
    lines.append("|---|---:|---:|---:|")
    for k in ["n_total", "n_degenerate", "n_real", "W", "L", "UNFILLED", "OPEN", "UNKNOWN", "resolved", "WR%", "sumR", "expR"]:
        o = stats["old_eps"].get(k)
        n = stats["new_eps"].get(k)
        try:
            delta = None if (o is None or n is None) else round(n - o, 3)
        except Exception:
            delta = None
        lines.append(f"| {k} | {o} | {n} | {delta if delta is not None else '—'} |")
    lines.append("")
    return lines


def _render_per_l2(records_by_reason: dict[str, list[dict]], m15: list[dict], symbol: str, new_eps: float) -> list[str]:
    lines = [f"### REJECTED_L2 bucket breakdown (symbol={symbol}, new eps={new_eps})", ""]
    lines.append("| l2_reason | N | old.sumR | old.expR | new.sumR | new.expR | ΔsumR |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for reason, recs in sorted(records_by_reason.items(), key=lambda kv: -len(kv[1])):
        o_out = _replay_with_epsilon(recs, m15, 0.05, symbol)
        n_out = _replay_with_epsilon(recs, m15, new_eps, symbol)
        stats = _bucket_stats(recs, o_out, n_out)
        lines.append(
            f"| {reason} | {stats['old_eps']['n_total']} "
            f"| {stats['old_eps']['sumR']} | {stats['old_eps']['expR']} "
            f"| {stats['new_eps']['sumR']} | {stats['new_eps']['expR']} "
            f"| {round(stats['new_eps']['sumR'] - stats['old_eps']['sumR'], 2)} |"
        )
    lines.append("")
    return lines


def _render_per_block(records_by_reason: dict[str, list[dict]], m15: list[dict], symbol: str, new_eps: float) -> list[str]:
    lines = [f"### BLOCKED_LIMIT bucket breakdown (symbol={symbol}, new eps={new_eps})", ""]
    lines.append("| block_reason | N | old.sumR | old.expR | new.sumR | new.expR | ΔsumR |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for reason, recs in sorted(records_by_reason.items(), key=lambda kv: -len(kv[1])):
        o_out = _replay_with_epsilon(recs, m15, 0.05, symbol)
        n_out = _replay_with_epsilon(recs, m15, new_eps, symbol)
        stats = _bucket_stats(recs, o_out, n_out)
        lines.append(
            f"| {reason} | {stats['old_eps']['n_total']} "
            f"| {stats['old_eps']['sumR']} | {stats['old_eps']['expR']} "
            f"| {stats['new_eps']['sumR']} | {stats['new_eps']['expR']} "
            f"| {round(stats['new_eps']['sumR'] - stats['old_eps']['sumR'], 2)} |"
        )
    lines.append("")
    return lines


def _outcome_flip_table(label: str, records: list[dict], old: list[dict], new: list[dict]) -> list[str]:
    flips = Counter()
    for rec, a, b in zip(records, old, new):
        if _is_degenerate(rec):
            continue
        flips[(a.get("outcome"), b.get("outcome"))] += 1
    lines = [f"### {label} — outcome transitions (old → new)", ""]
    lines.append("| old | new | count |")
    lines.append("|---|---|---:|")
    for (a, b), n in sorted(flips.items(), key=lambda kv: -kv[1]):
        tag = "" if a == b else " ← FLIPPED"
        lines.append(f"| {a} | {b} | {n}{tag} |")
    lines.append("")
    return lines


def run_instrument(symbol: str, out_path: Path) -> dict:
    print(f"[{symbol}] loading sim records ...")
    if symbol == "NAS100":
        recs = _load_nas100_records()
    elif symbol == "EURUSD":
        recs = _load_eurusd_records()
    else:
        raise ValueError(symbol)
    new_eps = EPSILON_BY_SYMBOL[symbol]
    print(f"[{symbol}] loaded {len(recs)} records; new eps={new_eps}")

    print(f"[{symbol}] loading M15 CSV ...")
    m15 = _load_m15(symbol)
    print(f"[{symbol}] M15 candles: {len(m15)}")

    # Slice by decision
    cands = [r for r in recs if r.get("decision") == "CANDIDATE"]
    l2s = [r for r in recs if r.get("decision") == "REJECTED_L2"]
    blocks = [r for r in recs if r.get("decision") == "BLOCKED_LIMIT"]

    # Bucket L2 by reason prefix
    by_l2 = defaultdict(list)
    for r in l2s:
        by_l2[_l2_reason_key(r)].append(r)
    # Bucket BLOCKED by reason prefix
    by_block = defaultdict(list)
    for r in blocks:
        by_block[_block_reason_key(r)].append(r)

    # ── Replay CANDIDATE ────────────────────────────────────────────────
    cand_old = _replay_with_epsilon(cands, m15, 0.05, symbol)
    cand_new = _replay_with_epsilon(cands, m15, new_eps, symbol)
    cand_stats = _bucket_stats(cands, cand_old, cand_new)

    # ── Replay L2 ───────────────────────────────────────────────────────
    l2_old = _replay_with_epsilon(l2s, m15, 0.05, symbol)
    l2_new = _replay_with_epsilon(l2s, m15, new_eps, symbol)
    l2_stats = _bucket_stats(l2s, l2_old, l2_new)

    # ── Replay BLOCKED_LIMIT ────────────────────────────────────────────
    bl_old = _replay_with_epsilon(blocks, m15, 0.05, symbol)
    bl_new = _replay_with_epsilon(blocks, m15, new_eps, symbol)
    bl_stats = _bucket_stats(blocks, bl_old, bl_new)

    # Specifically: sl_beyond_ob L2 (the NAS100 +13.5R / +20.50R claim)
    sl_beyond = [r for r in l2s if (r.get("l2_reason") or "").startswith("sl_beyond_ob")]
    sl_old = _replay_with_epsilon(sl_beyond, m15, 0.05, symbol)
    sl_new = _replay_with_epsilon(sl_beyond, m15, new_eps, symbol)
    sl_stats = _bucket_stats(sl_beyond, sl_old, sl_new)

    # max_kz_trades BLOCKED_LIMIT (the +16.02R NAS100 claim)
    kz_block = [r for r in blocks if (r.get("block_reason") or "").startswith("max_kz_trades")]
    kz_old = _replay_with_epsilon(kz_block, m15, 0.05, symbol)
    kz_new = _replay_with_epsilon(kz_block, m15, new_eps, symbol)
    kz_stats = _bucket_stats(kz_block, kz_old, kz_new)

    # ── Render markdown ─────────────────────────────────────────────────
    lines: list[str] = []
    lines.append(f"# {symbol} — T7 Epsilon Revalidation (A2/A3, session 35)")
    lines.append("")
    lines.append(f"**Symbol:** {symbol}  ")
    lines.append(f"**Legacy `_FILL_EPSILON`:** 0.05 (hardcoded pre-session-35)  ")
    lines.append(f"**Honest `_FILL_EPSILON`:** {new_eps} (per-instrument from `EPSILON_BY_SYMBOL`)  ")
    lines.append(f"**Records replayed:** {len(recs)} total — {len(cands)} CANDIDATE, {len(l2s)} REJECTED_L2, {len(blocks)} BLOCKED_LIMIT.")
    lines.append("")
    lines.append("Degenerate records (entry=SL or entry=TP or SL=TP) are counted separately; "
                 "their phantom `WIN r=0` outcome under the original sim is excluded from WR / sumR / expR.")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.extend(_render_bucket(f"CANDIDATE (n={len(cands)}) — accepted trades", cand_stats))
    lines.extend(_outcome_flip_table("CANDIDATE", cands, cand_old, cand_new))

    lines.extend(_render_bucket(f"REJECTED_L2 (n={len(l2s)}) — counterfactual if all L2 rejects had traded", l2_stats))
    lines.extend(_render_per_l2(by_l2, m15, symbol, new_eps))

    lines.extend(_render_bucket(f"BLOCKED_LIMIT (n={len(blocks)}) — counterfactual if all KZ/day blocks had traded", bl_stats))
    lines.extend(_render_per_block(by_block, m15, symbol, new_eps))

    lines.append("---")
    lines.append("")
    lines.append(f"## Focus #1 — `sl_beyond_ob` L2 bucket (n={len(sl_beyond)})")
    lines.append("")
    lines.append("The +13.5R standalone / +20.50R joint NAS100 claim from session 33.")
    lines.append("")
    lines.extend(_render_bucket("sl_beyond_ob", sl_stats))
    lines.extend(_outcome_flip_table("sl_beyond_ob", sl_beyond, sl_old, sl_new))

    lines.append("---")
    lines.append("")
    lines.append(f"## Focus #2 — `max_kz_trades` BLOCKED_LIMIT bucket (n={len(kz_block)})")
    lines.append("")
    lines.append("The +16.02R claim from NAS100 T3.1. Includes dupes (same setup re-fires in same KZ); not deduped here.")
    lines.append("")
    lines.extend(_render_bucket("max_kz_trades", kz_stats))
    lines.extend(_outcome_flip_table("max_kz_trades", kz_block, kz_old, kz_new))

    lines.append("---")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("* **Old eps (0.05)** is the NAS100 T3.1 / EURUSD T3.1 regime — same numbers reported in the session 33/34 synthesis docs.")
    lines.append("* **New eps** replays identical record set with honest per-instrument fill geometry.")
    lines.append("* **ΔsumR** on NAS100 should be modest (0.05 ≈ a tenth of a point is ~tight enough on an index); if ΔsumR on CANDIDATE set ≤ ±1R, the T3.1 CANDIDATE WR stands.")
    lines.append("* **ΔsumR** on EURUSD should be large: 0.05 = 500 pips on EURUSD — every limit was at-market under legacy, so most 'WIN at legacy' records flip to UNFILLED under honest 2-pip eps.")
    lines.append("* **The `sl_beyond_ob` focus block is the T2.9 gate-fix decision evidence** — we re-check whether the NAS100 +13.5R claim survives honest eps.")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[{symbol}] wrote {out_path}")

    return {
        "cand": cand_stats,
        "l2": l2_stats,
        "bl": bl_stats,
        "sl_beyond_ob": sl_stats,
        "max_kz_trades": kz_stats,
    }


def main() -> int:
    out_dir = _PROJECT_ROOT / "research/t3_1_eurusd_nas100_validation_2026-04-19/analysis"
    r_nas = run_instrument("NAS100", out_dir / "NAS100_epsilon_revalidation.md")
    r_eur = run_instrument("EURUSD", out_dir / "EURUSD_epsilon_revalidation.md")

    # Summary to stdout
    print()
    print("=== SUMMARY ===")
    for sym, r in (("NAS100", r_nas), ("EURUSD", r_eur)):
        print(f"\n[{sym}] CANDIDATE:")
        print(f"  old eps 0.05: W={r['cand']['old_eps']['W']} L={r['cand']['old_eps']['L']} sumR={r['cand']['old_eps']['sumR']} expR={r['cand']['old_eps']['expR']}")
        print(f"  new eps     : W={r['cand']['new_eps']['W']} L={r['cand']['new_eps']['L']} sumR={r['cand']['new_eps']['sumR']} expR={r['cand']['new_eps']['expR']}")
        print(f"[{sym}] sl_beyond_ob:")
        print(f"  old eps 0.05: sumR={r['sl_beyond_ob']['old_eps']['sumR']} expR={r['sl_beyond_ob']['old_eps']['expR']}")
        print(f"  new eps     : sumR={r['sl_beyond_ob']['new_eps']['sumR']} expR={r['sl_beyond_ob']['new_eps']['expR']}")
        print(f"[{sym}] max_kz_trades (not deduped):")
        print(f"  old eps 0.05: sumR={r['max_kz_trades']['old_eps']['sumR']} expR={r['max_kz_trades']['old_eps']['expR']}")
        print(f"  new eps     : sumR={r['max_kz_trades']['new_eps']['sumR']} expR={r['max_kz_trades']['new_eps']['expR']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

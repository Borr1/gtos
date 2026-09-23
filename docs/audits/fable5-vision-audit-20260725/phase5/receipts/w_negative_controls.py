"""Can the gate fail? Feed it things that are known-bad and watch.

    python3 docs/audits/fable5-vision-audit-20260725/phase5/receipts/w_negative_controls.py

A gate that admits by construction is worse than no gate. This receipt is the falsification
test for `src/research_infra/walkforward/`, and it runs two families:

FAMILY 1 — REAL DATA, KNOWN ANSWERS. The 11 core W7 sleeves, rebuilt from the same caches
Session N re-costed (`scripts/recost_w7_validation.py`). Four waves of work already
established what these are, so the gate's verdicts can be checked against something. Two
of them are the brief's nominated known-dead controls:

  * `metals_ob_micro` — gross -0.5 R on n=7. Negative before any cost is charged.
  * `idxrev`         — the brief calls this "measured negative before any cost was charged"
                       and **that is wrong**. `SURVIVOR_BOOK_V1.json` records
                       `gross_r: +0.00585` on n=6473 — positive, and indistinguishable from
                       zero. (The artifact's own `killed_reason` string, "negative before
                       any cost", is also wrong for this sleeve; it is right for
                       `metals_ob_micro`.) That makes `idxrev` a *better* control than the
                       brief intended: a zero-edge sleeve with a 6,473-trade sample, which
                       is exactly the shape that defeats a gate whose null ignores
                       day-clustering. A naive per-trade test on 6,473 observations will
                       find significance in noise.
  * `fx_jpy`         — the brief calls it "measured dead live at -0.453 R gross, p 0.0059".
                       Both numbers are real and neither is about this population. The
                       -0.453 R is the **JPY cluster pooled over 41 LIVE trades**
                       (`GATE_G1B_RECEIPT.md:640`), not `fx_jpy`'s 530-trade validated
                       stream, whose gross is **+0.28235**. And the p is quoted without the
                       sentence that produced it: "Bonferroni x12 -> 0.0706, which does NOT
                       survive at 0.05" (`third_review_receipts/read_g1b.md:115`). It is
                       carried here as a *contested* control and reported both ways.

Carry is set to the most generous defensible case: a 6-hour hold entered at 08:00 UTC,
which crosses no broker midnight (broker wall clock = America/New_York + 7h, so broker
midnight falls at ~21:00-22:00 UTC) and therefore pays no swap. If the gate rejects a
sleeve under the *cheapest* cost treatment available, the rejection is robust to carry. A
second pass at each sleeve's structural horizon is run to show the direction of travel.

FAMILY 2 — SYNTHETIC ADVERSARIES, constructed so a broken gate passes them:

  shuffled_label      real R values, re-attached to random dates. Any genuine time
                      structure is destroyed; expectancy is preserved.
  random_entry        pure noise at a matched trade frequency and matched volatility.
  one_regime          strongly positive inside a single fold, flat everywhere else. Pooled
                      expectancy is comfortably positive. This is the one that catches a
                      gate with no stability requirement.
  cost_eaten          a real +0.03 R/trade gross edge on an instrument whose broker-true
                      cost exceeds it. Gross-positive, net-negative. This is the one that
                      catches a gate whose cost binding is decorative.
  day_clustered_noise zero edge, 8 trades per day on few dates. This is the one that
                      catches a gate whose null treats trades as iid.

Offline and pure: reads caches and the cost artifact, imports no broker module, writes one
JSON.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import pickle
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from src.research_infra.walkforward import TradeRecord, Verdict, run_gate  # noqa: E402
from src.research_infra.walkforward.spec import GateSpec  # noqa: E402

OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase5/receipts/W_NEGATIVE_CONTROLS.json"
CACHE = Path("/tmp/w7_rows.pkl")

ENTRY_HOUR_UTC = 8
MINIMAL_HOLD_H = 6.0  # crosses no broker midnight -> zero swap -> cheapest honest cost

SPEC = GateSpec(
    spec_id="w_negative_controls_v1",
    authored_utc="2026-07-29T00:00:00+00:00",
    author_note="Falsification run for the walk-forward gate. Not an admission decision.",
    account="FTMO",
)


def load_rows() -> list[dict]:
    if CACHE.is_file():
        return pickle.loads(CACHE.read_bytes())
    import recost_w7_validation as M  # noqa: PLC0415

    rows = M.build([])["rows"]
    CACHE.write_bytes(pickle.dumps(rows))
    return rows


def horizon_hours() -> dict[str, float]:
    import recost_w7_validation as M  # noqa: PLC0415

    return dict(M.SLEEVE_HORIZON_H)


def to_trades(rows: list[dict], hold_h: dict[str, float]) -> dict[str, list[TradeRecord]]:
    """Cached rows -> TradeRecords. Rows without a recoverable stop distance are dropped
    and counted; the gate's coverage gate would refuse them anyway, and inventing a stop
    would be the same class of error as inventing a cost."""
    out: dict[str, list[TradeRecord]] = {}
    dropped: dict[str, int] = {}
    for r in rows:
        sl = r["sleeve"]
        sd = r.get("sl_price")
        px = r.get("entry_price")
        sym = r.get("broker_symbol_FTMO")
        if not sd or not px or not sym or sd <= 0 or px <= 0:
            dropped[sl] = dropped.get(sl, 0) + 1
            continue
        d = r["date"]
        e = dt.datetime(d.year, d.month, d.day, ENTRY_HOUR_UTC, tzinfo=dt.timezone.utc)
        side = r.get("side")
        direction = -1 if str(side).upper().startswith("S") else 1
        out.setdefault(sl, []).append(
            TradeRecord(
                sleeve=sl, symbol=sym, entry_utc=e,
                exit_utc=e + dt.timedelta(hours=hold_h.get(sl, MINIMAL_HOLD_H)),
                direction=direction, sl_distance_price=float(sd), entry_price=float(px),
                r_gross=float(r["R_gross"]),
                features={"stop_tier": r.get("stop_tier"), "source": r.get("source")},
            )
        )
    if dropped:
        print(f"  dropped for missing stop/price/symbol: {dropped}")
    return out


# ---------------------------------------------------------------------------------------
# Synthetic adversaries. Each is built under a REAL sleeve name so it inherits that
# sleeve's fidelity record and symbol -- otherwise the fidelity gate would refuse them for
# being unknown and the test would prove nothing.
# ---------------------------------------------------------------------------------------
def synth(rng: random.Random) -> dict[str, list[TradeRecord]]:
    def series(name, sym, px, sd, n, gen, start=dt.date(2016, 1, 4), step=(1, 1, 2, 3)):
        out, d = [], start
        for i in range(n):
            d += dt.timedelta(days=rng.choice(step))
            e = dt.datetime(d.year, d.month, d.day, ENTRY_HOUR_UTC, tzinfo=dt.timezone.utc)
            out.append(TradeRecord(
                sleeve=name, symbol=sym, entry_utc=e,
                exit_utc=e + dt.timedelta(hours=MINIMAL_HOLD_H),
                direction=rng.choice([1, -1]), sl_distance_price=sd, entry_price=px,
                r_gross=gen(i, d)))
        return out

    # A pool of realistic R shapes, CENTRED AT ZERO: bounded below near the stop, open
    # above. Centring matters. A label shuffle preserves expectancy, so a shuffle of a
    # positive-expectancy pool is still a positive-expectancy sleeve and this gate — which
    # scores realised net R, not signal/outcome association — would be right to admit it.
    # The shuffle is a null for a *predictive* claim; for an *expectancy* claim the null is
    # zero expectancy. Both are run: `shuffled_zero_mean` is the honest null, and
    # `shuffled_positive_mean` is kept to show the distinction rather than hide it.
    pool = [max(-1.15, min(4.8, rng.gauss(0.0, 1.05))) for _ in range(3000)]
    pool_pos = [max(-1.15, min(4.8, rng.gauss(0.05, 1.05))) for _ in range(3000)]

    out: dict[str, list[TradeRecord]] = {}

    # 1. shuffled labels, zero expectancy -- the honest null
    out["mx_btcusd_d1_donchian_20_breakout"] = series(
        "mx_btcusd_d1_donchian_20_breakout", "BTCUSD", 30000.0, 900.0, 600,
        lambda i, d: rng.choice(pool))

    # 2. random entry, matched frequency and volatility, zero edge
    out["mx_ethusd_d1_donchian_20_breakout"] = series(
        "mx_ethusd_d1_donchian_20_breakout", "ETHUSD", 2000.0, 60.0, 600,
        lambda i, d: rng.gauss(0.0, 1.05))

    # 3. one regime: all the edge inside a single mid-span year, flat everywhere else, so
    #    pooled expectancy is comfortably POSITIVE and only the stability gate can catch it.
    out["mx_us30_cash_d1_volume_surge_reversal"] = series(
        "mx_us30_cash_d1_volume_surge_reversal", "US30.cash", 30000.0, 300.0, 900,
        lambda i, d: rng.gauss(2.20, 1.0) if d.year == 2018 else rng.gauss(0.0, 1.0),
        start=dt.date(2016, 1, 4), step=(1, 1, 2, 2))

    # 4. cost-eaten: a real but tiny gross edge, on a stop tight enough that broker-true
    #    cost exceeds it. Gross-positive by construction, net-negative by arithmetic.
    out["mx_jp225_cash_d1_volume_surge_reversal"] = series(
        "mx_jp225_cash_d1_volume_surge_reversal", "JP225.cash", 38000.0, 12.0, 600,
        lambda i, d: rng.gauss(0.03, 0.9))

    # 5. day-clustered noise: zero edge, 8 trades a day on a few hundred dates.
    clustered: list[TradeRecord] = []
    d = dt.date(2016, 1, 4)
    for _ in range(300):
        d += dt.timedelta(days=rng.choice([1, 2, 4]))
        e = dt.datetime(d.year, d.month, d.day, ENTRY_HOUR_UTC, tzinfo=dt.timezone.utc)
        day_shock = rng.gauss(0.0, 0.9)  # the whole day moves together
        for _k in range(8):
            clustered.append(TradeRecord(
                sleeve="mx_us500_cash_d1_atr_mean_reversion", symbol="US500.cash",
                entry_utc=e, exit_utc=e + dt.timedelta(hours=MINIMAL_HOLD_H),
                direction=rng.choice([1, -1]), sl_distance_price=40.0, entry_price=4000.0,
                r_gross=day_shock + rng.gauss(0.0, 0.35)))
    out["mx_us500_cash_d1_atr_mean_reversion"] = clustered

    # 6. shuffled labels with POSITIVE expectancy -- kept to make the point above concrete.
    out["mx_avausd_d1_donchian_20_breakout"] = series(
        "mx_avausd_d1_donchian_20_breakout", "AVAUSD", 30.0, 1.2, 600,
        lambda i, d: rng.choice(pool_pos))
    return out


def positive_control(rng: random.Random) -> dict[str, list[TradeRecord]]:
    """A sleeve that SHOULD be admitted.

    A gate that rejects everything is exactly as useless as one that admits everything, and
    the failure is harder to notice because every individual rejection looks prudent. This
    is the other half of the falsification: a stable, real, cost-surviving edge, spread
    evenly across the whole span so no fold carries it alone.
    """
    out, d = [], dt.date(2016, 1, 4)
    for _i in range(700):
        d += dt.timedelta(days=rng.choice([1, 1, 2, 3]))
        e = dt.datetime(d.year, d.month, d.day, ENTRY_HOUR_UTC, tzinfo=dt.timezone.utc)
        out.append(TradeRecord(
            sleeve="mx_nzdjpy_d1_donchian_20_breakout", symbol="NZDJPY", entry_utc=e,
            exit_utc=e + dt.timedelta(hours=MINIMAL_HOLD_H),
            direction=rng.choice([1, -1]), sl_distance_price=0.45, entry_price=80.0,
            r_gross=max(-1.15, min(4.8, rng.gauss(0.30, 1.0)))))
    return {"mx_nzdjpy_d1_donchian_20_breakout": out}


def summarise(res, label: str) -> dict:
    rows = []
    for s, v in sorted(res.verdicts.items()):
        rows.append({
            "sleeve": s, "verdict": v.verdict.value, "n_trades": v.n_trades,
            "pooled_oos_mean_r": v.pooled_oos_mean_r, "p_raw": v.p_raw,
            "q_value": v.q_value,
            "gates": {k: g.get("pass") for k, g in v.gates.items()},
            "oos_positive_fold_frac": v.gates.get("stability", {}).get("oos_positive_fold_frac"),
            "coverage_frac": v.gates.get("cost_coverage", {}).get("coverage_frac"),
            "lag1_autocorr": v.telemetry.get("dependence", {}).get("lag1_autocorr_oos_days"),
            "block_days": v.telemetry.get("dependence", {}).get("block_days_used"),
            "n_oos_days": v.telemetry.get("dependence", {}).get("n_oos_days"),
            "effective_n": v.telemetry.get("dependence", {}).get("effective_n_oos_days"),
            "first_reason": v.reasons[0] if v.reasons else None,
        })
    print(f"\n=== {label} ===")
    print(f"{'sleeve':38s} {'verdict':14s} {'n':>6s} {'meanR':>9s} {'p':>9s} {'q':>9s} {'pos':>5s}")
    for r in rows:
        m = "-" if r["pooled_oos_mean_r"] is None else f"{r['pooled_oos_mean_r']:.5f}"
        p = "-" if r["p_raw"] is None else f"{r['p_raw']:.4g}"
        q = "-" if r["q_value"] is None else f"{r['q_value']:.4g}"
        pf = "-" if r["oos_positive_fold_frac"] is None else f"{r['oos_positive_fold_frac']:.0%}"
        print(f"{r['sleeve']:38s} {r['verdict']:14s} {r['n_trades']:6d} {m:>9s} {p:>9s} {q:>9s} {pf:>5s}")
    print(f"  ADMIT={res.admitted}")
    return {"label": label, "spec_sha256": res.spec.seal(), "rows": rows,
            "admitted": res.admitted, "rejected": res.rejected,
            "not_evaluable": res.not_evaluable,
            "family": {k: v for k, v in res.family.items() if k != "n_trials_basis"}}


def main() -> dict:
    print("loading W7 cached rows ...")
    rows = load_rows()
    hz = horizon_hours()
    out: dict = {
        "schema": "gtos.walkforward.negative_controls.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase5/receipts/w_negative_controls.py",
        "spec_sha256": SPEC.seal(),
        "carry_note": (
            f"minimal carry = {MINIMAL_HOLD_H}h from {ENTRY_HOUR_UTC:02d}:00 UTC, crossing no "
            "broker midnight (broker wall clock = America/New_York + 7h), so zero swap is "
            "charged. This is the cheapest defensible cost treatment; a rejection under it "
            "is robust to carry."
        ),
        "runs": {},
    }

    SPEC_R = SPEC.with_(
        spec_id="w_negative_controls_v1_restrict",
        coverage_policy="restrict_to_priced",
    )

    print("\n--- FAMILY 1: real W7 sleeves, minimal carry, coverage_policy=refuse ---")
    t_min = to_trades(rows, {s: MINIMAL_HOLD_H for s in hz})
    out["runs"]["real_minimal_carry"] = summarise(
        run_gate(t_min, SPEC), "real W7 @ minimal carry, policy=refuse")

    print("\n--- FAMILY 1r: same, coverage_policy=restrict_to_priced ---")
    out["runs"]["real_minimal_carry_restricted"] = summarise(
        run_gate(t_min, SPEC_R), "real W7 @ minimal carry, policy=restrict_to_priced")

    print("\n--- FAMILY 1b: real W7 sleeves, structural horizon, restricted ---")
    t_hz = to_trades(rows, hz)
    out["runs"]["real_structural_horizon_restricted"] = summarise(
        run_gate(t_hz, SPEC_R), "real W7 @ structural horizon, policy=restrict_to_priced")

    print("\n--- FAMILY 2: synthetic adversaries ---")
    out["runs"]["synthetic_adversaries"] = summarise(
        run_gate(synth(random.Random(20260729)), SPEC_R),
        "synthetic adversaries (every one should REJECT)")

    print("\n--- FAMILY 3: positive control (SHOULD be admitted) ---")
    out["runs"]["positive_control"] = summarise(
        run_gate(positive_control(random.Random(4242)), SPEC_R),
        "positive control - a real, stable, cost-surviving edge")

    # ---- the headline assertion ---------------------------------------------------------
    syn = out["runs"]["synthetic_adversaries"]
    leaked = [s for s in syn["admitted"] if s != "mx_avausd_d1_donchian_20_breakout"]
    pos = out["runs"]["positive_control"]
    pos_ok = "mx_nzdjpy_d1_donchian_20_breakout" in pos["admitted"]
    real = out["runs"]["real_minimal_carry_restricted"]
    known_dead = {"metals_ob_micro", "idxrev"}
    dead_admitted = sorted(set(real["admitted"]) & known_dead)
    ok = (not leaked) and pos_ok and (not dead_admitted)
    out["falsification"] = {
        "synthetic_adversaries_admitted": leaked,
        "positive_control_admitted": pos_ok,
        "known_dead_admitted_on_real_data": dead_admitted,
        "shuffled_positive_mean_note": (
            "mx_avausd_d1_donchian_20_breakout carries a genuinely positive expectancy by "
            "construction and is excluded from the leak set. It is a null for a predictive "
            "claim, not for an expectancy claim, and this gate scores expectancy. Its "
            "verdict is reported and is informative either way."
        ),
        "verdict": (
            "PASS - every constructed adversary rejected, the positive control admitted, "
            "and no known-dead sleeve reached ADMIT"
            if ok else
            "FAIL - the gate did not behave as required; that is the headline"
        ),
    }
    print("\n" + "=" * 78)
    print("FALSIFICATION:", out["falsification"]["verdict"])
    print("  adversaries admitted:", leaked or "none")
    print("  positive control admitted:", pos_ok)
    print("  known-dead admitted:", dead_admitted or "none")
    print("=" * 78)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return out


if __name__ == "__main__":
    main()

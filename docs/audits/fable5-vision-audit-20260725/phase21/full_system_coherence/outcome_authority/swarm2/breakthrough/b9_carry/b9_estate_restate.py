"""B9 step 2 — restate every sleeve's economics with favourable carry CREDITED.

Method. Not a median approximation: the per-trade nights are counted with the engine's own
`src.costs.model.rollover_nights` (`costs/model.py:990-1021`) on the broker's own wall clock,
against each trade's real `entry_utc` and `hold_hours` from the estate walk. The signed
per-night drag uses the engine's own conversion (`broker_net_cost_engine:485-504`) with the
clamp REMOVED:

    drag_price_per_night = -swap_points * point            (mode 1)
                         = -price * (swap_pct/100)/360     (modes 5, 6)
    swap_r_true  = nights * drag_price_per_night / sl_distance_price
    swap_r_clamped = max(swap_r_true, 0)                   <-- what the estate books today

    credit_r = swap_r_clamped - swap_r_true  (>= 0; the R the estate discards)

Reported per sleeve x account x swap-snapshot, per trade and per calendar month, with a
bootstrap CI on the per-trade credit. Two snapshots are run because they disagree (see
`b9_persistence.py`): `2026-06-01` (the R2-bound profile, the table research uses) and
`2026-07-25` (the VPS export behind `BROKER_TRUE_COSTS_V1.json`, the table `src/costs/model.py`
uses). The honest headline is the RECENT one.

Writes B9_ESTATE_CARRY_RESTATEMENT_V1.json.
"""
from __future__ import annotations

import collections
import gzip
import json
import math
import pathlib
import random
import sys
from datetime import datetime, timezone

REPO = pathlib.Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402

from src.costs.model import rollover_nights  # noqa: E402  -- the engine's own night counter

HERE = pathlib.Path(__file__).resolve().parent
ESTATE = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
EXPORT = pathlib.Path("/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api")
SERVERS = {"FTMO": "FTMO-Server3", "redacted_account": "redacted_account-Server 2"}
DAYS_PER_YEAR = 360.0


# ---------------------------------------------------------------- swap tables


def table_from_profile(rel: str) -> dict:
    d = yaml.safe_load((REPO / rel).read_text())
    out = {}
    for sym, v in (d.get("instruments") or {}).items():
        m = (v or {}).get("market") or {}
        if "swap_long" not in m:
            continue
        rec = {
            "swap_long": m.get("swap_long"),
            "swap_short": m.get("swap_short"),
            "swap_mode": m.get("swap_mode"),
            "point": m.get("point"),
            "roll3": m.get("triple_rollover_day"),
        }
        out[sym] = rec                                      # GTOS canonical
        out[str(m.get("mt5_symbol") or sym)] = rec          # broker native
    return out


#: canonical GTOS symbol -> broker-native symbol, from
#: research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/
#: VERIFIED_BROKER_SYMBOL_SPECS.json (`ftmo_native` / `redacted_account_native`). The two brokers do
#: NOT share names -- redacted_account calls the crude CFDs `USOUSD`/`UKOUSD` -- and a naive
#: `symbol_canonical` lookup silently drops every energy_agri trade on redacted_account.
def native_map(account_key: str) -> dict:
    d = json.loads(
        (REPO / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
                "VERIFIED_BROKER_SYMBOL_SPECS.json").read_text()
    )
    return {
        c: v.get(f"{account_key}_native")
        for c, v in (d.get("symbols") or {}).items()
        if v.get(f"{account_key}_native")
    }


def table_from_export(fname: str, account_key: str) -> dict:
    out = {}
    for line in (EXPORT / fname).read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if "swap_long" not in r:
            continue
        rec = {
            "swap_long": r.get("swap_long"),
            "swap_short": r.get("swap_short"),
            "swap_mode": r.get("swap_mode"),
            "point": r.get("point"),
            "roll3": r.get("swap_rollover3days"),
        }
        n = str(r.get("name"))
        out[n] = rec
        out[n.replace(".", "_")] = rec  # USOIL.cash -> USOIL_cash
    for canon, native in native_map(account_key).items():
        if native in out:
            out.setdefault(canon, out[native])
    return out


def drag_per_night(rec: dict, direction: int, price: float | None):
    """Signed price drag per night. Negative = the broker PAYS. None = source gap."""
    swap = rec.get("swap_long") if direction > 0 else rec.get("swap_short")
    mode = rec.get("swap_mode")
    if swap is None or mode is None:
        return None, "missing_swap_or_mode"
    mode = int(float(mode))
    if mode == 1:
        pt = rec.get("point")
        if not pt:
            return None, "missing_point"
        return -float(swap) * float(pt), "points"
    if mode in (5, 6):
        if not price:
            return None, "missing_price"
        return -float(price) * (float(swap) / 100.0) / DAYS_PER_YEAR, "annual_pct"
    return None, f"currency_denominated_mode_{mode}"


def boot_ci(vals, n=4000, seed=20260811):
    if not vals:
        return None, None
    rng = random.Random(seed)
    k = len(vals)
    means = []
    for _ in range(n):
        means.append(sum(vals[rng.randrange(k)] for _ in range(k)) / k)
    means.sort()
    return means[int(0.025 * n)], means[int(0.975 * n)]


def main() -> int:
    est = json.loads(gzip.open(ESTATE, "rt").read())
    tables = {
        ("FTMO", "2026-06-01_profile"): table_from_profile("config/profiles/operator_profile.yaml"),
        ("FTMO", "2026-07-25_export"): table_from_export("ftmo_symbols_get.jsonl", "ftmo"),
        ("redacted_account", "2026-07-25_export"): table_from_export("redacted_account_symbols_get.jsonl", "redacted_account"),
    }

    results = {}
    for (acct, snap), tab in tables.items():
        server = SERVERS[acct]
        per_sleeve = {}
        for sleeve, trades in est["trades"].items():
            if not trades:
                continue
            rows = []
            gaps = collections.Counter()
            for t in trades:
                sym = t.get("symbol_canonical") or t.get("symbol")
                rec = tab.get(sym) or tab.get(str(t.get("symbol")))
                if rec is None:
                    gaps["symbol_not_in_broker_table"] += 1
                    continue
                sld = t.get("sl_distance_price")
                hh = t.get("hold_hours")
                eu = t.get("entry_utc")
                if not sld or hh is None or not eu:
                    gaps["missing_trade_fields"] += 1
                    continue
                drag, status = drag_per_night(rec, int(t.get("direction", 0)), t.get("entry_price"))
                if drag is None:
                    gaps[status] += 1
                    continue
                try:
                    nights, _ = rollover_nights(
                        datetime.fromisoformat(eu).astimezone(timezone.utc),
                        float(hh),
                        server=server,
                        rollover3days_weekday=(int(rec["roll3"]) if rec.get("roll3") is not None else None),
                    )
                except Exception as exc:  # noqa: BLE001
                    gaps[f"rollover:{type(exc).__name__}"] += 1
                    continue
                swap_true = nights * drag / float(sld)
                swap_clamped = swap_true if swap_true > 0 else 0.0
                rows.append(
                    {
                        "symbol": sym,
                        "direction": t.get("direction"),
                        "entry_utc": eu,
                        "month": str(eu)[:7],
                        "hold_hours": hh,
                        "nights": nights,
                        "swap_r_true": swap_true,
                        "swap_r_clamped": swap_clamped,
                        "credit_r": swap_clamped - swap_true,
                        "r_gross": t.get("r_gross"),
                    }
                )
            if not rows:
                continue
            n = len(rows)
            cred = [r["credit_r"] for r in rows]
            with_credit = [r for r in rows if r["credit_r"] > 0]
            zero_nights = sum(1 for r in rows if r["nights"] == 0)
            lo, hi = boot_ci(cred)
            days = len({str(r["entry_utc"])[:10] for r in rows})
            per_sleeve[sleeve] = {
                "n_trades": n,
                "n_priced": n,
                "source_gaps": dict(gaps),
                "n_trades_zero_nights": zero_nights,
                "pct_trades_zero_nights": 100.0 * zero_nights / n,
                "n_trades_with_credit": len(with_credit),
                "mean_nights": sum(r["nights"] for r in rows) / n,
                "median_hold_hours": sorted(r["hold_hours"] for r in rows)[n // 2],
                "mean_credit_r_per_trade": sum(cred) / n,
                "credit_ci95": [lo, hi],
                "total_credit_r": sum(cred),
                "mean_charge_r_per_trade": sum(r["swap_r_clamped"] for r in rows) / n,
                "mean_true_swap_r_per_trade": sum(r["swap_r_true"] for r in rows) / n,
                "distinct_entry_days": days,
                "long_share": sum(1 for r in rows if (r["direction"] or 0) > 0) / n,
                "by_symbol_side": {
                    f"{k[0]}|{'LONG' if k[1] > 0 else 'SHORT'}": {
                        "n": len(v),
                        "mean_credit_r": sum(x["credit_r"] for x in v) / len(v),
                        "mean_nights": sum(x["nights"] for x in v) / len(v),
                        "total_credit_r": sum(x["credit_r"] for x in v),
                    }
                    for k, v in sorted(
                        collections.defaultdict(
                            list,
                            {
                                kk: [r for r in rows if (r["symbol"], r["direction"]) == kk]
                                for kk in {(r["symbol"], r["direction"]) for r in rows}
                            },
                        ).items()
                    )
                },
                "by_month": {
                    m: {
                        "n": len([r for r in rows if r["month"] == m]),
                        "total_credit_r": sum(r["credit_r"] for r in rows if r["month"] == m),
                    }
                    for m in sorted({r["month"] for r in rows})
                },
            }
        results[f"{acct}|{snap}"] = per_sleeve

    armed = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert")
    out = {
        "method": {
            "nights": "src.costs.model.rollover_nights (costs/model.py:990-1021), broker wall clock, "
                      "weekend midnights uncharged, triple-swap weekday x3",
            "conversion": "broker_net_cost_engine:485-504 with the >=0 clamp removed",
            "estate_source": str(ESTATE),
            "estate_generated_by": est.get("generated_by"),
            "bars_archive": est.get("bars_archive"),
            "servers": SERVERS,
            "ci": "percentile bootstrap, 4000 resamples, seed 20260811",
            "caveat": "energy_agri's estate walk applies exit_contract 'stop+target+maxbars' with "
                      "time_stop_bars_applied=false; hold_hours is therefore the walked hold, not a "
                      "live broker hold",
        },
        "armed_sleeves_2026_08_11": list(armed),
        "results": results,
    }
    (HERE / "B9_ESTATE_CARRY_RESTATEMENT_V1.json").write_text(json.dumps(out, indent=1, sort_keys=True))

    for key, per in results.items():
        print(f"\n================ {key} ================")
        print(f"{'sleeve':<26}{'n':>5}{'med_hold_h':>11}{'mean_nights':>12}{'%0-night':>10}"
              f"{'credit_R/trade':>16}{'CI95':>26}{'total_R':>10}")
        for s in sorted(per, key=lambda k: -per[k]["mean_credit_r_per_trade"]):
            v = per[s]
            if v["mean_credit_r_per_trade"] == 0 and s not in armed:
                continue
            ci = v["credit_ci95"]
            mark = " *ARMED*" if s in armed else ""
            print(f"{s:<26}{v['n_trades']:>5}{v['median_hold_hours']:>11.1f}{v['mean_nights']:>12.3f}"
                  f"{v['pct_trades_zero_nights']:>9.1f}%{v['mean_credit_r_per_trade']:>+16.5f}"
                  f"  [{ci[0]:+.5f},{ci[1]:+.5f}]{v['total_credit_r']:>10.3f}{mark}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

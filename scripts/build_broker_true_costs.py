#!/usr/bin/env python3
"""Build ``BROKER_TRUE_COSTS_V1.json`` -- the one versioned source of cost truth.

Stage 1.1 (Session J). Every number in the artifact carries a coverage class
([MEASURED] / [TRANSFERRED] / [MODELLED]) and a provenance string, per
``SESSION_J_BROKER_TRUTH.md``.

The central design decision, and why it differs from the receipt table
---------------------------------------------------------------------
``GATE_G1B_RECEIPT.md`` §5.2a reports commission **in R** per symbol -- USDJPY 0.1948,
GBPJPY 0.0927, XAUUSD 0.0054, index CFDs 0.0000. Those are correct for the W7 window and
**must not be used as per-instrument rates**, because commission in R is

    commission_r = commission_ccy_per_lot / (sl_distance_price * usd_per_price_unit_per_lot)

i.e. it is a function of *that trade's stop distance*, not a property of the instrument.
Measured here: USDJPY and GBPJPY pay the **identical** $5.00/lot round turn on both
brokers. Their 2.1x difference in R is entirely stop distance. A re-cost that applied
0.1948 R to every USDJPY fill would misprice every sleeve whose stop is not the JPY
scalp's ~8 pips.

So this artifact stores **native broker units** -- USD/lot, basis points of notional,
price units, swap points/night -- and ``src.costs`` derives R at call time from the
caller's stop distance. This is the same split the live engine already uses for spread
and swap (``broker_net_cost_engine.py:293-294``, ``:357-360``); commission is the one
term that never had a native-unit representation, which is a large part of why it fell
out of the arithmetic (F38).

Inputs
------
- VPS export deals + symbol specs (``09_mt5_api/``) -- commission, swap params, contract geometry
- ``TICK_SPREAD_MEASUREMENT.json`` -- from ``scripts/measure_tick_spreads.py``
- ``GATE_G1B_RECEIPT.md`` §12 -- measured entry slippage
- ``ULTIMATE_REAL_COST_MAP.json`` -- vendored as the F39 legacy comparator

Usage
-----
    python3 scripts/build_broker_true_costs.py -o <out.json>
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]

DEFAULT_EXPORT_ROOT = Path("/Users/borr/GTOSActive/vps-export-20260725/extracted")
DEFAULT_TICK_MEASUREMENT = (
    REPO / "research/operations/broker_truth_layer_2026_07_27/TICK_SPREAD_MEASUREMENT.json"
)
LEGACY_COST_MAP = (
    REPO
    / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
    / "ULTIMATE_REAL_COST_MAP.json"
)

SCHEMA = "gtos.broker_truth.broker_true_costs.v1"
VERSION = "1.1.0"  # 1.1.0: energy classifier carve-out + cross-account commission (B603)

ACCOUNTS = {
    "FTMO": {
        "login": 531325516,
        "server": "FTMO-Server3",
        "company": "FTMO Global Markets Ltd",
        "currency": "USD",
        "deals": "ftmo_history_deals_get.jsonl",
        "specs": "ftmo_symbol_specs_traded.json",
        "universe": "ftmo_symbols_get.jsonl",
        "profile": "config/profiles/operator_profile.yaml",
    },
    "redacted_account": {
        "login": 0,
        "server": "redacted_account-Server 2",
        "company": "redacted_account Ltd",
        "currency": "USD",
        "deals": "redacted_account_history_deals_get.jsonl",
        "specs": "redacted_account_symbol_specs_traded.json",
        "universe": "redacted_account_symbols_get.jsonl",
        "profile": "config/profiles/redacted_account.yaml",
    },
}

# Broker `path` prefix -> normalised instrument class. Both brokers' own taxonomies,
# read from the MT5 symbol spec `path` field, so the class is broker-declared rather
# than hand-assigned. redacted_account files metals under "Commodities" alongside energy, so
# the metals symbols are pulled out by name.
_METALS = {"XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD"}

# ...and FTMO files its OIL CFDs under `Cash II CFD\`, which the path rule below reads as
# `index`, so `USOIL.cash` and `UKOIL.cash` inherited the index class's fitted ZERO
# commission while the identical instruments on redacted_account sit under `Commodities\`, are
# `energy`, and are MEASURED at $5.00/lot. They are the only two instruments where the two
# accounts' classes disagree.
#
# FIXED 2026-07-29 (B603), by the same name-based carve-out the metals already use — filed
# by `SESSION_N_W7_RECOST_RESULT.md` §7 and prescribed by `FOURTH_REVIEW.md` §3.1 as part
# of `energy_agri`'s repair. Barrel oil is not an index whatever folder a broker files it
# in, and the classifier had already established the shape of this exception.
#
# The base symbol is matched with the account suffix stripped (`.cash`, `.c`, `_cash`),
# because the two brokers spell the same instrument differently.
_ENERGY_BASES = {"USOIL", "UKOIL", "NATGAS", "HEATOIL", "BRENT", "WTI", "GASOLINE",
                 "USOUSD", "UKOUSD", "NGAS"}

# The two brokers spell the same barrel differently: FTMO `USOIL.cash` / `UKOIL.cash`,
# redacted_account `USOUSD` / `UKOUSD`. Verified by reading both universes' MT5 paths and
# descriptions — redacted_account files both under `Commodities\` and fits $5.00/lot on them
# (`class_fallback_schedule.energy.measured_from_symbols == ["UKOUSD", "USOUSD"]`).
# Without this the cross-account transfer below silently does not fire, which is the
# failure mode that produced the false zero in the first place.
_SYMBOL_ALIASES = {
    "USOUSD": "USOIL", "WTI": "USOIL",
    "UKOUSD": "UKOIL", "BRENT": "UKOIL",
    "NGAS": "NATGAS",
}


def _base_symbol(symbol: str) -> str:
    s = (symbol or "").upper()
    for suffix in (".CASH", "_CASH", ".C", "_C", ".SPOT", "-CASH"):
        if s.endswith(suffix):
            s = s[: -len(suffix)]
            break
    return _SYMBOL_ALIASES.get(s, s)


def instrument_class(symbol: str, path: str) -> str:
    head = (path or "").split("\\")[0].strip()
    if symbol in _METALS:
        return "metals"
    if _base_symbol(symbol) in _ENERGY_BASES:
        return "energy"
    if head.startswith("Forex"):
        return "jpy_fx" if symbol.endswith("JPY") else "fx"
    if "Crypto" in head:
        return "crypto"
    if head.startswith("Metals"):
        return "metals"
    if head.startswith("Cash") or head.startswith("Indices"):
        return "index"
    if head.startswith("Commodities"):
        return "energy"
    # Kept distinct rather than folded into the classes above: exotic FX and agri are
    # named by `GATE_G1B_RECEIPT.md` §5.2a as commission-unmeasured, and an exotic pair
    # is not safely priced at the majors' flat $5.00/lot.
    if head.startswith("Exotics"):
        return "fx_exotic"
    if head.startswith("Agriculture"):
        return "agri"
    if head.startswith("Equities"):
        return "equity"
    return "unclassified"


# GATE_G1B_RECEIPT.md:767-768 -- measured entry slippage, in R at the live stop geometry.
# Pooled +0.0132 R (n=140), corroborated +0.0108 R (n=147) by a second lane.
SLIPPAGE_POOLED_R = 0.0132
SLIPPAGE_POOLED_N = 140
SLIPPAGE_BY_SYMBOL_R = {
    "AUDUSD": 0.041,
    "GBPUSD": 0.040,
    "USDJPY": 0.039,
    "XAUUSD": 0.003,
}
SLIPPAGE_PROVENANCE = (
    "GATE_G1B_RECEIPT.md:767-768 (lifecycle capture + slippage_runtime, 78.6% of W7 days)"
)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    # The VPS wrote a UTF-8 BOM on these files.
    return [json.loads(line) for line in path.read_text("utf-8-sig").splitlines() if line.strip()]


def _dispersion_pct(values: list[float]) -> float:
    med = statistics.median(values)
    if not med:
        return 0.0
    return 100.0 * (max(values) - min(values)) / abs(med)


def derive_commission(deals: list[dict], specs: dict) -> tuple[dict, dict]:
    """Fit a per-symbol commission schedule from complete round turns.

    Returns (per_symbol, meta). Positions without a closing deal are excluded: on FTMO,
    which charges per side, an unclosed position carries only the entry half and would
    halve the fitted rate.
    """
    trades = [d for d in deals if d.get("type") in (0, 1) and d.get("symbol")]
    by_pos: dict = collections.defaultdict(list)
    for d in trades:
        by_pos[d["position_id"]].append(d)

    entry_comm = exit_comm = 0.0
    per: dict = collections.defaultdict(list)
    n_closed = n_open = 0
    for _pid, ds in by_pos.items():
        ent = [d for d in ds if d.get("entry") == 0]
        ex = [d for d in ds if d.get("entry") == 1]
        entry_comm += sum(d["commission"] for d in ent)
        exit_comm += sum(d["commission"] for d in ex)
        if not ent or not ex:
            n_open += 1
            continue
        n_closed += 1
        sym = ds[0]["symbol"]
        spec = specs.get(sym) or {}
        cs = spec.get("trade_contract_size")
        vol = sum(d["volume"] for d in ent)
        px = ent[0]["price"]
        comm = -sum(d["commission"] for d in ds)  # positive = cost
        if vol <= 0 or px <= 0 or not cs:
            continue
        per[sym].append(
            {
                "per_lot": comm / vol,
                "notional_bp": comm / (vol * cs * px) * 1e4,
                "volume": vol,
                "price": px,
            }
        )

    out: dict = {}
    for sym, rows in per.items():
        per_lot = [r["per_lot"] for r in rows]
        bp = [r["notional_bp"] for r in rows]
        if all(abs(v) < 1e-9 for v in per_lot):
            out[sym] = {
                "kind": "zero",
                "value": 0.0,
                "unit": "USD/lot round turn",
                "n_round_turns": len(rows),
                "note": "measured zero on every round turn -- not an unmeasured zero",
            }
            continue
        d_lot = _dispersion_pct(per_lot)
        d_bp = _dispersion_pct(bp)
        # Flat-per-lot and notional-bp are distinguishable by which one is stable across
        # the window's price range. Prefer per_lot on ties so FX reads as the flat
        # schedule it is.
        if d_lot <= d_bp + 1e-9:
            kind, value, unit, disp = "per_lot", statistics.median(per_lot), "USD/lot round turn", d_lot
        else:
            kind, value, unit, disp = (
                "notional_bp",
                statistics.median(bp),
                "bp of notional, round turn",
                d_bp,
            )
        out[sym] = {
            "kind": kind,
            "value": round(value, 6),
            "unit": unit,
            "n_round_turns": len(rows),
            "dispersion_pct": round(disp, 3),
            "fit_dispersion_pct": {"per_lot": round(d_lot, 3), "notional_bp": round(d_bp, 3)},
            "median_per_lot_usd": round(statistics.median(per_lot), 6),
            "median_notional_bp": round(statistics.median(bp), 6),
            "volume_range": [min(r["volume"] for r in rows), max(r["volume"] for r in rows)],
        }

    meta = {
        "round_turns_used": n_closed,
        "positions_excluded_no_close": n_open,
        "entry_side_commission_total": round(entry_comm, 2),
        "exit_side_commission_total": round(exit_comm, 2),
        "charge_side": (
            "entry_only"
            if abs(exit_comm) < 1e-9
            else "both_sides"
            if abs(entry_comm) > 1e-9
            else "exit_only"
        ),
    }
    return out, meta


def class_fallback(per_symbol: dict, specs: dict) -> dict:
    """Per class, the modal measured schedule -- the source for TRANSFERRED numbers."""
    by_class: dict = collections.defaultdict(list)
    for sym, rec in per_symbol.items():
        spec = specs.get(sym) or {}
        by_class[instrument_class(sym, spec.get("path", ""))].append((sym, rec))
    out = {}
    for klass, rows in by_class.items():
        kinds = collections.Counter(r["kind"] for _s, r in rows)
        kind = kinds.most_common(1)[0][0]
        vals = [r["value"] for _s, r in rows if r["kind"] == kind]
        srcs = [s for s, r in rows if r["kind"] == kind]
        med = statistics.median(vals)
        # The empirical transfer error: how far apart the measured members of this class
        # actually are. This is a direct test of the transfer rule rather than an
        # assumption about it -- where a class has >=2 measured symbols, it says what a
        # TRANSFERRED band should really be. Compare against the default x0.5/x2.
        spread_pct = (100.0 * (max(vals) - min(vals)) / abs(med)) if med else 0.0
        out[klass] = {
            "kind": kind,
            "value": round(med, 6),
            "unit": rows[0][1]["unit"],
            "measured_from_symbols": sorted(srcs),
            "n_symbols": len(srcs),
            "max_relative_deviation_pct": round(spread_pct, 4),
            "transfer_rule_testable": len(srcs) >= 2,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export-root", type=Path, default=DEFAULT_EXPORT_ROOT)
    ap.add_argument("--tick-measurement", type=Path, default=DEFAULT_TICK_MEASUREMENT)
    ap.add_argument("-o", "--out", type=Path, required=True)
    args = ap.parse_args()

    api = args.export_root / "09_mt5_api"
    ticks = json.loads(args.tick_measurement.read_text()) if args.tick_measurement.is_file() else {}
    legacy = json.loads(LEGACY_COST_MAP.read_text()) if LEGACY_COST_MAP.is_file() else {}

    inputs = []
    doc: dict = {
        "schema": SCHEMA,
        "version": VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/build_broker_true_costs.py",
        "coverage_classes": {
            "MEASURED": "observed on this account, this instrument",
            "TRANSFERRED": "inferred from a comparable instrument; names the source",
            "MODELLED": "no observation; a stated assumption with an owner and a date",
        },
        "conventions": {
            "sign": "costs are POSITIVE (matches broker_net_cost_engine.py:577-583)",
            "commission": "native units: USD per lot round turn, or bp of notional round "
            "turn. R is derived by src.costs from the caller's stop distance -- "
            "commission_r = usd_per_lot / (sl_distance_price * usd_per_price_unit_per_lot). "
            "The receipt's per-symbol R values are window-specific and are NOT rates.",
            "spread": "price units, ONE bid/ask crossing per round trip, matching "
            "KB7_tick_truth.py:128 and broker_net_cost_engine.py:294",
            "swap": "broker points per night (mode 1) or annual pct (modes 5/6); charged "
            "per ROLLOVER CROSSING, not per elapsed hour -- measured: swap present at "
            "2.2 h holds and absent at 24.3 h holds",
            "slippage": "R at the live stop geometry; does not rescale with stop distance",
            "usd_per_price_unit_per_lot": "trade_tick_value / trade_tick_size",
        },
        "accounts": {},
        "legacy_class_cost_map": {
            "note": "ULTIMATE_REAL_COST_MAP.json, vendored as the F39 comparator. Its "
            "consumers state it is spread+commission (KB7_tick_lib.py:22, "
            "KB7_tick_truth.py:59-63) but it has NO generator in git history, so what it "
            "actually contained is unestablished. Both F39 readings need it.",
            "values": legacy,
            "coverage": "MODELLED",
            "provenance": "research/operations/final_moonshot_v4_ultimate_mechanical_edge_"
            "2026_06_10/ULTIMATE_REAL_COST_MAP.json (enters git at 450a275f8 as a JSON-only "
            "diff with no generator)",
        },
    }

    # ---- pass 1: every account's MEASURED commissions, keyed by BASE symbol ------------
    # The cross-account transfer below needs them all before any instrument is built. Two
    # cheap reads rather than a restructure of the main loop.
    measured_by_base: dict[str, dict[str, Any]] = {}
    for _acct, _cfg in ACCOUNTS.items():
        try:
            _c, _m = derive_commission(read_jsonl(api / _cfg["deals"]),
                                       json.loads((api / _cfg["specs"]).read_text("utf-8-sig")))
        except (OSError, ValueError):  # pragma: no cover - defensive
            continue
        for _sym, _rec in _c.items():
            measured_by_base.setdefault(_base_symbol(_sym), []).append(
                {"account": _acct, "symbol": _sym, **_rec}
            )

    for acct, cfg in ACCOUNTS.items():
        deals_path = api / cfg["deals"]
        specs_path = api / cfg["specs"]
        for p in (deals_path, specs_path):
            inputs.append({"path": str(p), "sha256": sha256_of(p), "bytes": p.stat().st_size})

        deals = read_jsonl(deals_path)
        specs = json.loads(specs_path.read_text("utf-8-sig"))
        # Widen to the broker's whole quotable universe. The traded-specs file covers only
        # what was actually traded, which would make every coverage class MEASURED by
        # construction and hide the real gap: `GATE_G1B_RECEIPT.md` §5.2a names commission
        # as unmeasured for energy/agri, DASHUSD, the metal crosses and ~24% of `idxrev`'s
        # index universe. Those symbols live only in the universe dump.
        universe_path = api / cfg["universe"]
        inputs.append(
            {
                "path": str(universe_path),
                "sha256": sha256_of(universe_path),
                "bytes": universe_path.stat().st_size,
            }
        )
        traded_symbols = set(specs)
        for row in read_jsonl(universe_path):
            name = row.get("name")
            if name and name not in specs:
                specs[name] = row

        comm, comm_meta = derive_commission(deals, specs)
        fallback = class_fallback(comm, specs)
        tick_acct = (ticks.get("accounts") or {}).get(acct, {})

        instruments = {}
        for sym in sorted(specs):
            spec = specs[sym]
            klass = instrument_class(sym, spec.get("path", ""))
            tv, ts = spec.get("trade_tick_value"), spec.get("trade_tick_size")
            upu = (tv / ts) if (tv and ts) else None

            if sym in comm:
                crec = dict(comm[sym])
                crec["coverage"] = "MEASURED"
                crec["provenance"] = (
                    f"{cfg['deals']} -- {crec['n_round_turns']} complete round turns, "
                    f"charge side {comm_meta['charge_side']}"
                )
            elif klass in fallback:
                fb = fallback[klass]
                crec = {
                    **{k: fb[k] for k in ("kind", "value", "unit")},
                    "coverage": "TRANSFERRED",
                    "transferred_from": f"{acct} class '{klass}' "
                    f"({', '.join(fb['measured_from_symbols'])})",
                    "provenance": f"class median over {fb['n_symbols']} measured symbol(s); "
                    f"measured members disagree by {fb['max_relative_deviation_pct']}%",
                }
            else:
                # CROSS-ACCOUNT TRANSFER, added 2026-07-29 (B603). Before the class
                # fallback runs out, ask whether the SAME INSTRUMENT is measured on the
                # other account. `USOIL.cash` is the case this exists for: unmeasured on
                # FTMO, MEASURED at $5.00/lot on redacted_account, and the same barrel.
                #
                # It is stamped TRANSFERRED with the source account named, and it is the
                # CONSERVATIVE direction — charging a measured peer's rate rather than
                # zero. `W7_RECOST_V1.json:accounts.FTMO.sensitivities.
                # ftmo_oil_charged_redacted_account_rate` already priced it at +0.0144 R/trade
                # on `energy_agri`; this lands it instead of carrying it as a sensitivity.
                peers = [
                    p for p in measured_by_base.get(_base_symbol(sym), [])
                    if p["account"] != acct
                ]
                if peers:
                    src = peers[0]
                    crec = {
                        "kind": src["kind"],
                        "value": src["value"],
                        "unit": src.get("unit", "USD/lot round turn"),
                        "coverage": "TRANSFERRED",
                        "transferred_from": (
                            f"{src['account']} {src['symbol']} (MEASURED, "
                            f"{src.get('n_round_turns')} round turns)"
                        ),
                        "provenance": (
                            f"same instrument, other account: no {acct} deal rows and no "
                            f"measured {acct} peer in class '{klass}', so the measured "
                            f"{src['account']} rate for the same base symbol is charged. "
                            f"Conservative direction — the alternative in the record was "
                            f"a false zero via the 'Cash II' path match "
                            f"(SESSION_N_W7_RECOST_RESULT.md section 7)."
                        ),
                    }
                else:
                    crec = {
                        "kind": "unknown",
                        "value": None,
                        "unit": None,
                        "coverage": "MODELLED",
                        "owner": "Session J (Stage 1.1)",
                        "asof": "2026-07-27",
                        "provenance": "no deal rows for this symbol and no measured peer "
                        "in its class; commission is UNKNOWN, not zero",
                    }

            trec = tick_acct.get(sym) or tick_acct.get(sym.replace(".", "_")) or {}
            spread = None
            if trec and "spread_price" in trec and trec["spread_price"]:
                spread = {
                    "coverage": "MEASURED",
                    "unit": "price units, one crossing",
                    "provenance": f"vps-ticks-20260726/{trec.get('file')} -- "
                    f"{trec.get('rows_in_file')} ticks, stride {trec.get('stride')}, "
                    f"{trec.get('utc_first')} .. {trec.get('utc_last')} UTC",
                    "n_ticks_sampled": trec.get("rows_sampled"),
                    "percentiles": trec["spread_price"],
                    "by_session": {
                        k: v.get("spread_price") for k, v in (trec.get("by_session") or {}).items()
                    },
                    "mid_price_median": trec.get("mid_price_median"),
                }

            slip = (
                {
                    "value_r": SLIPPAGE_BY_SYMBOL_R[sym],
                    "coverage": "MEASURED",
                    "provenance": SLIPPAGE_PROVENANCE,
                }
                if sym in SLIPPAGE_BY_SYMBOL_R
                else {
                    "value_r": SLIPPAGE_POOLED_R,
                    "coverage": "TRANSFERRED",
                    "transferred_from": f"pooled W7 entry slippage, n={SLIPPAGE_POOLED_N}",
                    "provenance": SLIPPAGE_PROVENANCE,
                }
            )

            instruments[sym] = {
                "instrument_class": klass,
                "traded_in_export_window": sym in traded_symbols,
                "broker_path": spec.get("path"),
                "spec": {
                    k: spec.get(k)
                    for k in (
                        "trade_contract_size",
                        "trade_tick_value",
                        "trade_tick_size",
                        "point",
                        "digits",
                        "swap_mode",
                        "swap_long",
                        "swap_short",
                        "swap_rollover3days",
                        "currency_profit",
                    )
                },
                "usd_per_price_unit_per_lot": upu,
                "commission": crec,
                "spread_price": spread,
                "swap": {
                    "coverage": "MEASURED",
                    "unit": "broker points per night (mode 1) / annual pct (modes 5,6)",
                    "provenance": f"{cfg['specs']} symbol_info swap fields, export "
                    "2026-07-25",
                    "swap_mode": spec.get("swap_mode"),
                    "swap_long": spec.get("swap_long"),
                    "swap_short": spec.get("swap_short"),
                    "swap_rollover3days_weekday": spec.get("swap_rollover3days"),
                },
                "slippage": slip,
            }

        doc["accounts"][acct] = {
            **{k: cfg[k] for k in ("login", "server", "company", "currency", "profile")},
            "commission_charge_side": comm_meta["charge_side"],
            "commission_fit_meta": comm_meta,
            "class_fallback_schedule": fallback,
            "instruments": instruments,
        }

    if args.tick_measurement.is_file():
        inputs.append(
            {
                "path": str(args.tick_measurement),
                "sha256": sha256_of(args.tick_measurement),
                "bytes": args.tick_measurement.stat().st_size,
            }
        )
    if LEGACY_COST_MAP.is_file():
        inputs.append(
            {
                "path": str(LEGACY_COST_MAP),
                "sha256": sha256_of(LEGACY_COST_MAP),
                "bytes": LEGACY_COST_MAP.stat().st_size,
            }
        )
    doc["inputs"] = inputs

    counts: dict = collections.Counter()
    for name, acct in doc["accounts"].items():
        for rec in acct["instruments"].values():
            counts[f"{name} commission:{rec['commission']['coverage']}"] += 1
            counts[f"{name} spread:{'MEASURED' if rec['spread_price'] else 'ABSENT'}"] += 1
    doc["coverage_summary"] = dict(sorted(counts.items()))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=1, sort_keys=True))
    print(f"wrote {args.out}")
    for k, v in doc["coverage_summary"].items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

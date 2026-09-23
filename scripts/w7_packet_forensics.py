#!/usr/bin/env python3
"""Second evidence lane for Gate G1b: the live book's own runtime-learning telemetry.

`scripts/w7_live_forensics.py` reconstructs what the BROKER saw. This reconstructs what the BOOK
thought it was doing, from `shadow_logs/ultimate_book_runtime_learning_packets.jsonl.gz` in the VPS
export -- 99,112 packets over 38 unbroken days, the one live ledger that did NOT die on 2026-07-02
(finding V3).

It answers three questions broker truth cannot:

  1. **The dial, as the book computed it.** `bridge.realized_units[].risk_pct_per_trade` and
     `bridge.governor.size_cap_multiplier`. This is an INDEPENDENT measurement of the same quantity
     `w7_live_forensics.py` derives from |entry-sl| x volume x money-per-unit. The two agreeing is
     the cross-validation; they are computed from disjoint inputs.
  2. **Why a sleeve did not trade.** `unit_skipped.skip_reason`, per sleeve. Five of the eight core-8
     sleeves placed nothing in the live window and this says what they did instead.
  3. **The pre-trade cost gate.** `skip_reason` carries the live cost model's own
     `total_cost_r_exceeds_limit:<measured>><limit>` strings -- the only surviving quantitative
     record of execution cost for this window, since `slippage_runtime` died on 07-02 and the
     packet's own `spread_r` field is null on all 99,112 rows.

METHOD WARNING, recorded because it cost a wrong conclusion before it was caught. Every packet
carries a `bridge.broker_profile_generation.broker_unsupported_skips` SUMMARY LIST that repeats the
same skip reasons on unrelated events. Grepping a line for `profile_missing_instrument_config` and
attributing it to that packet inflates the count by ~10x and mislabels `unit_admitted` rows as skips.
This script matches ONLY `event_type == "unit_skipped"` and reads that row's OWN `skip_reason`.

Run:  python3 scripts/w7_packet_forensics.py
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

DEFAULT_PACKETS = Path("/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/"
                       "ultimate_book_runtime_learning_packets.jsonl.gz")
DEFAULT_OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics"

COST_RE = re.compile(r"total_cost_r_exceeds_limit:([0-9.]+)>([0-9.]+)")
SPREAD_RE = re.compile(r"cost_screen_spread_r:([0-9.]+)>([0-9.]+)\s*\(spread ([0-9.]+) vs (\S+) "
                       r"stop ([0-9.]+)\)")


def summarise(vals: list[float]) -> dict:
    if not vals:
        return {"n": 0}
    v = sorted(vals)
    return {
        "n": len(v),
        "mean": round(statistics.fmean(v), 6),
        "median": round(statistics.median(v), 6),
        "min": round(v[0], 6),
        "p90": round(v[int(0.9 * (len(v) - 1))], 6),
        "max": round(v[-1], 6),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packets", type=Path, default=DEFAULT_PACKETS)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    from src.components.ultimate_book import admission

    ev = Counter()
    per_sleeve_events: dict[str, Counter] = defaultdict(Counter)
    skip_reasons: dict[str, Counter] = defaultdict(Counter)
    missing_cfg: dict[str, Counter] = defaultdict(Counter)
    missing_cfg_ns: Counter = Counter()
    cost_rej: dict[str, list[tuple[float, float]]] = defaultdict(list)
    spread_rej: list[dict] = []
    gov: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    gov_reason: dict[str, Counter] = defaultdict(Counter)
    overlays: dict[str, Counter] = defaultdict(Counter)
    spread_r_presence = Counter()
    placed_days: dict[str, set] = defaultdict(set)
    bridge_flags: dict[str, dict] = {}

    with gzip.open(args.packets, "rt", encoding="utf-8-sig") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except Exception:
                ev["_unparseable"] += 1
                continue
            et = d.get("event_type")
            ev[et] += 1
            sleeve = d.get("sleeve")
            if sleeve:
                per_sleeve_events[sleeve][et] += 1
            spread_r_presence["null" if d.get("spread_r") is None else "value"] += 1

            if et == "unit_skipped":
                raw = d.get("skip_reason") or d.get("reject_reason") or "?"
                skip_reasons[sleeve or "<none>"][raw.split(";")[0]] += 1
                if raw.startswith("profile_missing_instrument_config"):
                    missing_cfg[sleeve or "<none>"][d.get("symbol")] += 1
                    missing_cfg_ns[d.get("namespace")] += 1
                m = COST_RE.search(raw)
                if m:
                    cost_rej[sleeve or "<none>"].append((float(m.group(1)), float(m.group(2))))
                m2 = SPREAD_RE.search(raw)
                if m2:
                    got, lim, spread, sym, stop = m2.groups()
                    spread_rej.append({
                        "sleeve": sleeve, "symbol": d.get("symbol"),
                        "spread_r_measured": float(got), "spread_r_limit": float(lim),
                        "spread_price": float(spread), "stop_price": float(stop),
                        "stop_over_spread": (round(float(stop) / float(spread), 4)
                                             if float(spread) else None),
                    })

            if et == "unit_placed":
                ns = d.get("namespace") or "?"
                b = d.get("bridge") or {}
                g = b.get("governor") or {}
                if g.get("size_cap_multiplier") is not None:
                    gov[ns]["size_cap_multiplier"].append(float(g["size_cap_multiplier"]))
                if g.get("available_gross_risk_pct") is not None:
                    gov[ns]["available_gross_risk_pct"].append(float(g["available_gross_risk_pct"]))
                gov_reason[ns][g.get("reason")] += 1
                for u in (b.get("realized_units") or []):
                    for f in ("risk_pct_per_trade", "unit_risk_pct", "confidence"):
                        if u.get(f) is not None:
                            gov[ns][f].append(float(u[f]))
                    for o in (u.get("overlays_applied") or []):
                        overlays[ns][o.split("_x")[0]] += 1
                if d.get("decision_day"):
                    placed_days[ns].add(d["decision_day"])
                if ns not in bridge_flags:
                    bridge_flags[ns] = {
                        k: b.get(k) for k in
                        ("profile", "derisk_mode", "include_clean3", "include_candidate_book",
                         "include_market_expansion_book", "kelly_lite", "kelly_conservative",
                         "kelly_running_count", "stress_derisk", "metals_confluence_gate",
                         "sqrt_n_pooling", "apply_to_execution", "broad_selector_apply_to_execution",
                         "live_activation_allowed_by_config", "runtime_effect_now",
                         "candidate_book_sleeve_count", "market_expansion_sleeve_count")
                    }

    core8 = admission.SLEEVE_REGISTRY
    composition = []
    for name, spec in sorted(core8.items(), key=lambda kv: -kv[1].confidence):
        evs = dict(per_sleeve_events.get(name, {}))
        composition.append({
            "sleeve": name,
            "confidence": spec.confidence,
            "status": spec.status,
            "asset_class": spec.asset_class,
            "universe": list(spec.symbols),
            "events": evs,
            "n_unit_placed": evs.get("unit_placed", 0),
            "n_unit_admitted": evs.get("unit_admitted", 0),
            "n_unit_shadow": evs.get("unit_shadow", 0),
            "n_unit_skipped": evs.get("unit_skipped", 0),
            "placed_anything": evs.get("unit_placed", 0) > 0,
            "skip_reasons": dict(skip_reasons.get(name, {})),
            "missing_config_symbols": dict(missing_cfg.get(name, {})),
        })
    traded_w = sum(c["confidence"] for c in composition if c["placed_anything"])
    total_w = sum(c["confidence"] for c in composition)

    out = {
        "schema": "gtos.w7_packet_forensics.v1",
        "generated_by": "scripts/w7_packet_forensics.py",
        "source": str(args.packets),
        "method_warning": (
            "Only event_type=='unit_skipped' rows are counted, reading that row's own skip_reason. "
            "Every packet also carries bridge.broker_profile_generation.broker_unsupported_skips, a "
            "SUMMARY list that repeats skip reasons on unrelated events; a line-level grep over it "
            "inflates counts ~10x and mislabels unit_admitted rows as skips."
        ),
        "event_type_totals": dict(ev),
        "spread_r_field_presence": dict(spread_r_presence),
        # DERIVED, not hardcoded. This was a fixed sentence asserting spread_r is null on every
        # row -- true of the 99,112-packet pre-carry corpus and false the moment the emitter
        # started populating it, at which point the artifact would have carried a claim
        # contradicting its own `spread_r_field_presence` count two lines above. A hardcoded
        # finding beside the count that disproves it is exactly the class of self-contradicting
        # evidence this programme keeps getting burned by.
        "spread_r_gap": (
            (
                "spread_r is declared on the packet and is NULL on every row. Packet-based spread "
                "reconstruction is therefore unavailable for this window; the only surviving "
                "quantitative cost record is the pretrade_cost_gate rejection strings below."
            )
            if not spread_r_presence.get("value")
            else (
                f"spread_r is populated on {spread_r_presence.get('value', 0)} of "
                f"{sum(spread_r_presence.values())} rows; packet-based spread reconstruction is "
                "available for that subset. Rows with a null spread_r predate the emitter carry "
                "or were never evaluated by the pre-send cost screen."
            )
        ),
        "bridge_flags_at_placement": bridge_flags,
        "core8_composition": composition,
        "core8_confidence_weight": {
            "total": round(total_w, 4),
            "that_placed_a_trade": round(traded_w, 4),
            "silent": round(total_w - traded_w, 4),
            "pct_that_placed": round(100.0 * traded_w / total_w, 2) if total_w else None,
            "note": (
                "A sleeve is 'silent' here if it emitted no unit_placed event in the window. The "
                "five silent sleeves emitted NO unit_admitted and NO unit_shadow either -- so they "
                "did not generate candidates that were then rejected; they generated nothing on any "
                "symbol either broker carries. Whether that is their natural firing frequency or a "
                "generation defect is NOT decidable from a 14-day window; see the receipt's gap G4."
            ),
        },
        "profile_missing_instrument_config": {
            "by_namespace": dict(missing_cfg_ns),
            "by_sleeve_symbol": {k: dict(v) for k, v in missing_cfg.items()},
            "note": (
                "Reported on the redacted_account namespace only, and only for symbols redacted_account does "
                "not list (XAUEUR, XAGEUR, XAUAUD, XAGAUD, DASHUSD, XPDUSD, XTZUSD, AVAUSD). This "
                "is the book CORRECTLY skipping instruments the broker does not carry -- not a "
                "defect, and NOT the reason the high-confidence core sleeves were silent."
            ),
        },
        "pretrade_cost_gate": {
            "global_limits": {"max_spread_r": 0.10, "max_total_cost_r": 0.15,
                              "source": "config/agent_config.yaml:715-716"},
            "per_sleeve_overrides": {
                "fx_jpy": {"max_spread_r": 0.35, "max_total_cost_r": 0.45},
                "fx_jpy_ny": {"max_spread_r": 0.35, "max_total_cost_r": 0.45},
                "source": "config/agent_config.yaml:717-729",
                "dated": "2026-06-16",
                "config_own_words": (
                    "OWNER-APPROVED JPY-CROSS LIVE TRIAL (2026-06-16) ... a normal JPY-CROSS spread "
                    "(GBPJPY ~2 pips) is ~22% of that stop, which the global 0.10 spread / 0.15 "
                    "total-cost gate CORRECTLY REFUSES ... To MEASURE the live edge net of spread "
                    "(not reject from logs), these two sleeves run a looser ceiling ONLY."
                ),
                "how_to_end": "Set the by_sleeve maps to {} to revert to the strict global gate.",
            },
            "rejections_by_sleeve": {
                sl: {
                    "n_rejected": len(v),
                    "limit": v[0][1],
                    "measured_total_cost_r": summarise([x[0] for x in v]),
                }
                for sl, v in sorted(cost_rej.items(), key=lambda kv: -len(kv[1]))
            },
            "spread_screen_rejections": spread_rej,
        },
        "governor_by_namespace": {
            ns: {
                "n_unit_placed": sum(gov_reason[ns].values()),
                "decision_days_with_a_placement": len(placed_days[ns]),
                "reason": dict(gov_reason[ns]),
                **{f: summarise(v) for f, v in gov[ns].items()},
                "overlays_applied": dict(overlays[ns].most_common(12)),
            }
            for ns in sorted(gov)
        },
    }

    caps = {ns: v.get("size_cap_multiplier", {}).get("median")
            for ns, v in out["governor_by_namespace"].items()}
    f = caps.get("operator_profile")
    n = caps.get("redacted_account_live_bee34003")
    out["governor_asymmetry"] = {
        "ftmo_median_size_cap_multiplier": f,
        "redacted_account_median_size_cap_multiplier": n,
        "fn_over_ftmo": round(n / f, 4) if (f and n) else None,
        "note": (
            "This is the mechanism for Gate G1b axis (d). The two book workers are independent "
            "processes; FTMO entered the window already down 2.74% from the pre-W7 fleet, so its "
            "reactive de-risk ladder was further along than redacted_account's. Same signal, different "
            "size. The de-risk overlay behaved as designed and REDUCED FTMO's loss."
        ),
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    p = args.out_dir / "W7_PACKET_FORENSICS.json"
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"wrote {p}")
    print(f"  packets: {sum(ev.values())}  unit_placed: {ev.get('unit_placed')}  "
          f"unit_skipped: {ev.get('unit_skipped')}")
    print(f"  core-8 confidence weight that placed a trade: "
          f"{out['core8_confidence_weight']['that_placed_a_trade']} of "
          f"{out['core8_confidence_weight']['total']} "
          f"({out['core8_confidence_weight']['pct_that_placed']}%)")
    print(f"  governor size_cap median: FTMO {f} / FN {n}  ratio "
          f"{out['governor_asymmetry']['fn_over_ftmo']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

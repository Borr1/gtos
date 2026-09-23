#!/usr/bin/env python3
"""Evidence pack 1.4c — the D2 runtime-day-key MC, and the cluster-cap reframing.

Two questions, and the second is the larger one
-----------------------------------------------
`bar_provider.decision_day_of` (`bar_provider.py:86-88`) returns the **signal bar's UTC date** and
is the correlated-unit grouping key.  It drives the Kelly-lite per-day count
(`admission.py:1113-1118,1144-1148`), the `(decision_day, cluster)` correlated-risk-unit bucket
(`:1107-1113`), and both placement caps (`book_owner.py:1601-1617`).  D2 measured that a cycle whose
intents' last-closed bars straddle UTC midnight gets **two Kelly multipliers on units decided from
one `size_correlated_units` call** — worst observed ×1.241 against ×0.748, a 1.66× ratio — and that
the only fix unifying all four measured cycles is a **runtime** day key.

Re-keying is an owner decision (B54 Part 2) because `book_owner.py:1607-1610` calls the cap it
drives "the one-unit-per-cluster-per-day envelope **the dial was certified on**".  **This script
does not change it.**  It produces the pack that lets the owner decide.

And the reframing that changes the decision: **`ultimate_book_one_unit_per_cluster_per_day` is
globally `false` at HEAD** (`config/agent_config.yaml:1373`), with `jpy` in
`cluster_cap_exempt_clusters` (`:1374`) underneath a cap that is not running — the exempt list is
unreachable, because `book_owner.py:1612` short-circuits on the global boolean first.  So the live
book is **already** operating outside the envelope the 2.0 % dial was certified on, and the day-key
question is downstream of a larger one: *should the certified envelope be re-imposed at all?*
Both are quantified here.

Run:  python3 scripts/evidence_pack_day_key_mc.py
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

DEFAULT_PACKETS = Path(
    "/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/"
    "ultimate_book_runtime_learning_packets.jsonl.gz"
)
DEFAULT_ROWS = REPO / "docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl"
DEFAULT_OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase3/evidence_packs"

SCHEMA = "gtos.phase3.evidence_pack.day_key_mc.v1"
KELLY_TAG = re.compile(r"^kelly_lite_na(\d+)_x([0-9.]+)$")

NAMESPACE_TO_ACCOUNT = {"operator_profile": "ftmo", "redacted_account_live_bee34003": "redacted_account"}
#: `config/agent_config.yaml:1374` — the exempt list as configured (unreachable at HEAD).
CONFIGURED_EXEMPT = frozenset({"jpy"})

#: live book composition, `config/agent_config.yaml:1272-1286`
LIVE_CANDIDATE_SLEEVES = (
    "asia_pdl_fade", "asian_fade", "kz_london_crypto_low", "liq_asia_up_low_metal",
    "metal_session_reversion", "ny_crypto_momentum", "orb_crypto_london",
    "vol_compression", "vss_fxcross_london_up_low",
)
LIVE_EXPANSION_POLICY = "positive_weighted12_after_swap"


def _bridge_digest(bridge: dict) -> str:
    return hashlib.sha256(json.dumps(bridge, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(packets: Path):
    opener = gzip.open if packets.suffix == ".gz" else open
    with opener(packets, "rb") as fh:
        if fh.read(40).startswith(b"version https://git-lfs"):
            raise SystemExit(f"packet source is an unhydrated LFS pointer: {packets}")

    cycles: dict[tuple, dict] = {}
    placements: list[dict] = []
    with (gzip.open if packets.suffix == ".gz" else open)(packets, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            pkt = json.loads(line)
            bridge = pkt.get("bridge") or {}
            if pkt.get("event_type") == "unit_placed":
                placements.append({
                    "namespace": pkt.get("namespace"),
                    "account": NAMESPACE_TO_ACCOUNT.get(pkt.get("namespace")),
                    "cluster": pkt.get("cluster"),
                    "sleeve": pkt.get("sleeve"),
                    "symbol": pkt.get("symbol"),
                    "decision_bar_iso": pkt.get("decision_bar_iso"),
                    "created_at_utc": pkt.get("created_at_utc"),
                    "candidate_id": pkt.get("candidate_id"),
                })
            if "would_units" not in bridge:
                continue
            key = (pkt.get("namespace"), _bridge_digest(bridge))
            c = cycles.setdefault(key, {
                "namespace": pkt.get("namespace"), "units": bridge.get("would_units") or [],
                "intents": set(), "runtimes": [],
            })
            c["runtimes"].append(pkt.get("created_at_utc"))
            if pkt.get("sleeve") and pkt.get("decision_bar_iso"):
                c["intents"].add((pkt["sleeve"], pkt.get("symbol"), pkt["decision_bar_iso"]))
    for c in cycles.values():
        c["runtime"] = min(c["runtimes"])
    return cycles, placements


# --------------------------------------------------------------------------------------------
# Part A — the Kelly / correlated-unit envelope under each day key
# --------------------------------------------------------------------------------------------
def part_a(cycles, rng, draws: int) -> dict:
    from src.components.ultimate_book import admission as A

    unit_bearing = {k: c for k, c in cycles.items() if c["units"]}
    with_intents = {k: c for k, c in unit_bearing.items() if c["intents"]}

    # D2's own headline counts, recomputed independently.
    two_counts = two_mults = 0
    for c in unit_bearing.values():
        nas, xs = set(), set()
        for u in c["units"]:
            for t in (u.get("overlays_applied") or []):
                m = KELLY_TAG.match(t)
                if m:
                    nas.add(int(m.group(1)))
                    xs.add(m.group(2))
        if len(nas) > 1:
            two_counts += 1
        if len(xs) > 1:
            two_mults += 1

    # The correlated-risk-unit key is (decision_day, cluster) -- `admission.py:1119-1135` -- so the
    # bucket count has to resolve the CLUSTER, not just the day. Counting (cycle, bar-day)
    # partitions and calling them buckets overstated this by 1.33x in the first version; caught by
    # an adversarial pass and corrected here.
    sleeves, err = A.resolve_market_expansion_sleeves(policy=LIVE_EXPANSION_POLICY)
    if err:
        raise SystemExit(f"market expansion policy unresolved: {err}")
    registry = A.effective_registry(
        include_clean3=False, include_clean4=False, include_candidate_book=True,
        candidate_book_sleeves=list(LIVE_CANDIDATE_SLEEVES),
        include_market_expansion_book=True, market_expansion_sleeves=sleeves)

    def cluster_for(sleeve):
        return A.cluster_of(sleeve, registry) or "__unknown__"

    buckets_utc: set = set()
    buckets_runtime: set = set()
    rows, span_rows = [], []
    for key, c in with_intents.items():
        rt_day = str(c["runtime"])[:10]
        ns = c["namespace"]
        for sleeve, _sym, bar in c["intents"]:
            buckets_utc.add((ns, str(bar)[:10], cluster_for(sleeve)))
            buckets_runtime.add((ns, rt_day, cluster_for(sleeve)))
        per_day_utc: dict[str, set] = defaultdict(set)
        for sleeve, _sym, bar in c["intents"]:
            per_day_utc[str(bar)[:10]].add(sleeve)
        na_runtime = len({s for s, _sym, _b in c["intents"]})       # one key => one bucket
        recorded_na = sorted({int(KELLY_TAG.match(t).group(1))
                              for u in c["units"] for t in (u.get("overlays_applied") or [])
                              if KELLY_TAG.match(t)})
        if not recorded_na:
            continue
        for day, sleeves in sorted(per_day_utc.items()):
            na_utc = len(sleeves)
            rows.append({
                "namespace": c["namespace"], "runtime_day": rt_day, "bar_day": day,
                "na_utc_per_cycle": na_utc, "na_runtime_per_cycle": na_runtime,
                "recorded_na": recorded_na,
                "mult_utc": A.kelly_lite_conviction_multiplier(na_utc, enabled=True, conservative=True),
                "mult_runtime": A.kelly_lite_conviction_multiplier(na_runtime, enabled=True,
                                                                   conservative=True),
            })
        if len(per_day_utc) > 1:
            span_rows.append({
                "namespace": c["namespace"], "runtime": c["runtime"],
                "bar_days": sorted(per_day_utc),
                "per_day_sleeves": {d: sorted(s) for d, s in sorted(per_day_utc.items())},
                "recorded_na": recorded_na,
            })

    ratios = [r["mult_runtime"] / r["mult_utc"] for r in rows if r["mult_utc"] > 0]
    changed = [r for r in rows if abs(r["mult_runtime"] - r["mult_utc"]) > 1e-12]

    # --- the MC over the unrecoverable running-conviction count ------------------------------
    # `kelly_running_count: true` means live used na = max(per_cycle, persisted_running)
    # (`admission.py:1167-1168`).  The running store is machine-local and absent from the export,
    # so the per-cycle recomputation is a LOWER bound.  Where the recorded na exceeds the per-cycle
    # count the running store is pinned; where it does not, running is only bounded above, so it is
    # drawn.  This is the honest way to carry the gap rather than assuming it away.
    # The upper bound matters and the first version got it wrong. Drawing `running` from
    # [0, na_utc_per_cycle] FORCES max(na_utc, running) == na_utc and max(na_runtime, running) ==
    # na_runtime, so the ratio cannot move and the "MC" recomputes one number `draws` times. The
    # record itself refutes that bound: recorded `kelly_lite_naN` tags reach na = %s while the
    # per-cycle reconstruction never exceeds %s. Drawing to the recorded maximum is the honest
    # support, and under it the MC is no longer degenerate.
    max_recorded_na = max((max(r["recorded_na"]) for r in rows), default=0)
    max_percycle_na = max((r["na_utc_per_cycle"] for r in rows), default=0)
    mc = {"draws": draws, "samples": [],
          "running_support": f"uniform 0..{max_recorded_na} (the recorded na maximum)",
          "max_recorded_na": max_recorded_na, "max_per_cycle_na": max_percycle_na,
          "withdrawn": ("v1 drew running from 0..na_utc_per_cycle, which forces degeneracy and is "
                        "contradicted by the recorded tags reaching na=" + str(max_recorded_na))}
    for _ in range(draws):
        deltas = []
        for r in rows:
            rec = max(r["recorded_na"])
            if rec > r["na_utc_per_cycle"]:
                running = rec                        # pinned by the record
            else:
                running = rng.randint(0, max_recorded_na)
            na_live = max(r["na_utc_per_cycle"], running)
            na_rk = max(r["na_runtime_per_cycle"], running)
            m_live = A.kelly_lite_conviction_multiplier(na_live, enabled=True, conservative=True)
            m_rk = A.kelly_lite_conviction_multiplier(na_rk, enabled=True, conservative=True)
            deltas.append(m_rk / m_live if m_live > 0 else 1.0)
        mc["samples"].append({
            "mean_size_ratio": statistics.fmean(deltas),
            "frac_changed": sum(1 for d in deltas if abs(d - 1.0) > 1e-12) / len(deltas),
            "max_ratio": max(deltas), "min_ratio": min(deltas),
        })
    mc["summary"] = {
        k: {"mean": statistics.fmean(s[k] for s in mc["samples"]),
            "p05": sorted(s[k] for s in mc["samples"])[int(0.05 * (draws - 1))],
            "p95": sorted(s[k] for s in mc["samples"])[int(0.95 * (draws - 1))],
            "min": min(s[k] for s in mc["samples"]), "max": max(s[k] for s in mc["samples"])}
        for k in ("mean_size_ratio", "frac_changed", "max_ratio", "min_ratio")
    }
    mc.pop("samples")

    return {
        "cycle_key": "sha256 of the bridge block, per namespace (Session H's grouping)",
        "distinct_bridge_states_with_would_units_key": len(cycles),
        "distinct_bridge_states_carrying_units": len(unit_bearing),
        "of_which_have_recoverable_intents": len(with_intents),
        "d2_reproduction": {
            "states_with_two_kelly_counts": two_counts,
            "states_with_two_kelly_multipliers": two_mults,
            "register_published": {"two_counts": 12, "two_multipliers": 4},
            "reproduces_register": (two_counts == 12 and two_mults == 4),
            "denominator_note": (
                "The register quotes 884 unit-bearing states; this grouping yields "
                f"{len(unit_bearing)}. The NUMERATORS reproduce exactly, so D2's mechanism and its "
                "corrected 12/4 counts are confirmed; only the rate's denominator differs by "
                "grouping convention, and both denominators are stated rather than reconciled."),
        },
        "cycle_day_bucket_rows": len(rows),
        "rows_whose_kelly_multiplier_changes_under_runtime_key": len(changed),
        "frac_rows_changed": len(changed) / len(rows) if rows else 0.0,
        "size_ratio_runtime_over_utc": {
            "mean": statistics.fmean(ratios) if ratios else None,
            "min": min(ratios) if ratios else None, "max": max(ratios) if ratios else None,
            "n_below_1": sum(1 for r in ratios if r < 1 - 1e-12),
            "n_above_1": sum(1 for r in ratios if r > 1 + 1e-12),
        },
        "correlated_unit_buckets": {
            "note": ("The correlated-risk-unit key is (decision_day, cluster) -- admission.py:1135. "
                     "Counted here by resolving the cluster through the live effective registry, "
                     "not by counting (cycle, bar-day) partitions, which is a different and larger "
                     "quantity. The runtime key cannot split one cycle, so the count is weakly "
                     "LOWER under it: the envelope tightens."),
            "distinct_day_cluster_buckets_utc_key": len(buckets_utc),
            "distinct_day_cluster_buckets_runtime_key": len(buckets_runtime),
            "buckets_removed_by_runtime_key": len(buckets_utc) - len(buckets_runtime),
            "cycles_split_across_more_than_one_bar_day": len(span_rows),
            "bar_day_span_histogram": dict(sorted(Counter(len(s["bar_days"]) for s in span_rows).items())),
            "cycle_bar_day_partitions_beyond_one": sum(len(s["bar_days"]) - 1 for s in span_rows),
            "withdrawn": ("The first version reported `cycle_bar_day_partitions_beyond_one` (129) as "
                          "a count of (day, cluster) buckets. It is not; the true bucket delta is "
                          "`buckets_removed_by_runtime_key`."),
        },
        "cycles_spanning_two_bar_days": span_rows[:20],
        "running_count_mc": mc,
    }


# --------------------------------------------------------------------------------------------
# Part B — the cluster cap, on and off, under each day key
# --------------------------------------------------------------------------------------------
def cluster_cap_sim(placements, *, day_key: str, exempt: frozenset) -> dict:
    """Re-run `placement_ledger.cluster_placed_today_other_bar` over the recorded placements.

    `book_owner.py:1607-1617`: a cluster that already placed on a DIFFERENT bar of the same day is
    skipped; same-bar members of one unit still place.
    """
    placed_bars: dict[tuple, set] = defaultdict(set)
    blocked, kept = [], []
    for p in sorted(placements, key=lambda x: x["created_at_utc"]):
        cluster = p["cluster"]
        day = (str(p["decision_bar_iso"])[:10] if day_key == "utc_bar"
               else str(p["created_at_utc"])[:10])
        bar = str(p["decision_bar_iso"])
        k = (p["namespace"], cluster, day)
        if cluster and cluster not in exempt and any(b != bar for b in placed_bars[k]):
            blocked.append(dict(p, blocked_day=day, blocked_cluster=cluster))
            continue
        placed_bars[k].add(bar)
        kept.append(p)
    return {"n_placed": len(kept), "n_blocked": len(blocked), "blocked": blocked}


def random_block_null(placements, w7_rows, n_block: int, rng, draws: int) -> dict:
    """THE NULL CONTROL for Part B, and it is the one that decides how to read Part B at all.

    The W7 fortnight lost money.  On a book with negative realised expectancy, **any** rule that
    removes trades improves the P&L in expectation — so "re-imposing the cap would have saved
    0.96 pp" is not evidence that the cap selects well unless it beats removing the same number of
    placements at random.  This measures exactly that.
    """
    saved: list[float] = []
    for _ in range(draws):
        picked = rng.sample(placements, min(n_block, len(placements)))
        priced = price_blocked(picked, w7_rows)
        saved.append(-priced["removed_sum_pct_of_initial"])
    s = sorted(saved)
    return {
        "draws": draws, "n_blocked_per_draw": n_block,
        "saved_pct_of_initial_mean": statistics.fmean(s),
        "saved_pct_of_initial_p05": s[int(0.05 * (len(s) - 1))],
        "saved_pct_of_initial_median": statistics.median(s),
        "saved_pct_of_initial_p95": s[int(0.95 * (len(s) - 1))],
        "saved_pct_of_initial_min": s[0], "saved_pct_of_initial_max": s[-1],
    }, saved


def part_b(placements, rows_path: Path, rng, null_draws: int) -> dict:
    rows = [json.loads(l) for l in rows_path.read_text().splitlines() if l.strip()]
    w7 = [r for r in rows if r["in_w7_denominator"]]

    configs = {
        "cap_off_HEAD": None,
        "cap_on_utc_key_jpy_exempt": ("utc_bar", CONFIGURED_EXEMPT),
        "cap_on_utc_key_no_exempt": ("utc_bar", frozenset()),
        "cap_on_runtime_key_jpy_exempt": ("runtime", CONFIGURED_EXEMPT),
        "cap_on_runtime_key_no_exempt": ("runtime", frozenset()),
    }
    out = {}
    for name, cfg in configs.items():
        if cfg is None:
            out[name] = {"n_placed": len(placements), "n_blocked": 0, "blocked_by_cluster": {},
                         "blocked_by_sleeve": {}, "priced": None}
            continue
        sim = cluster_cap_sim(placements, day_key=cfg[0], exempt=cfg[1])
        priced = price_blocked(sim["blocked"], w7)
        null, null_samples = random_block_null(placements, w7, sim["n_blocked"], rng, null_draws)
        observed_saved = -priced["removed_sum_pct_of_initial"]
        out[name] = {
            "n_placed": sim["n_placed"], "n_blocked": sim["n_blocked"],
            "blocked_by_cluster": dict(Counter(b["cluster"] for b in sim["blocked"]).most_common()),
            "blocked_by_sleeve": dict(Counter(b["sleeve"] for b in sim["blocked"]).most_common()),
            "blocked_by_account": dict(Counter(b["account"] for b in sim["blocked"]).most_common()),
            "priced": priced,
            "observed_saved_pct_of_initial": observed_saved,
            "null_control_random_blocking": null,
            "beats_null_percentile": None,
        }
        # TRUE empirical CDF. v1 interpolated over three quantiles and was off by up to 0.074
        # absolute / 30 % relative while being quoted to three decimals.
        out[name]["beats_null_percentile"] = (
            sum(1 for x in null_samples if x <= observed_saved) / len(null_samples))
    return out


def price_blocked(blocked, w7_rows) -> dict:
    """Join blocked placements to broker trade rows to price them in R and cash.

    Join key is (account, sleeve, symbol, decision-bar date) plus nearest entry time, because a
    placement packet and a broker fill are different events with different clocks.  Unmatched
    placements are reported, not silently dropped — the packet stream starts 2026-06-18 while the
    book's first W7 fill is 2026-06-15, so a residue is expected and its size is the check.
    """
    index: dict[tuple, list] = defaultdict(list)
    for r in w7_rows:
        index[(r["account"], r["sleeve_id"], r["canonical_symbol"])].append(r)
    matched, unmatched = [], []
    used = set()
    for b in blocked:
        cands = index.get((b["account"], b["sleeve"], b["symbol"]), [])
        best, best_gap = None, None
        for r in cands:
            if id(r) in used:
                continue
            gap = abs((_ts(r["entry_time_utc"]) - _ts(b["created_at_utc"])))
            if best_gap is None or gap < best_gap:
                best, best_gap = r, gap
        if best is not None and best_gap is not None and best_gap <= 6 * 3600:
            used.add(id(best))
            matched.append({"blocked": b, "row": best, "gap_seconds": best_gap})
        else:
            unmatched.append(b)
    return {
        "n_blocked": len(blocked),
        "n_matched_to_broker_rows": len(matched),
        "n_unmatched": len(unmatched),
        "match_window_seconds": 6 * 3600,
        "removed_sum_r": sum(m["row"]["realized_r"] for m in matched),
        "removed_sum_cash": sum(m["row"]["realized_net"] for m in matched),
        "removed_sum_pct_of_initial": sum(m["row"]["pct_of_initial_balance"] for m in matched),
        "removed_by_account": {
            a: {"n": sum(1 for m in matched if m["row"]["account"] == a),
                "sum_r": sum(m["row"]["realized_r"] for m in matched if m["row"]["account"] == a),
                "sum_pct_of_initial": sum(m["row"]["pct_of_initial_balance"] for m in matched
                                          if m["row"]["account"] == a)}
            for a in ("ftmo", "redacted_account")},
        "matched_detail": [
            {"account": m["row"]["account"], "sleeve": m["row"]["sleeve_id"],
             "symbol": m["row"]["canonical_symbol"], "entry": m["row"]["entry_time_utc"],
             "realized_r": m["row"]["realized_r"],
             "pct_of_initial": m["row"]["pct_of_initial_balance"],
             "gap_seconds": m["gap_seconds"]} for m in matched],
        "unmatched_detail": [{"sleeve": u["sleeve"], "symbol": u["symbol"],
                              "created_at_utc": u["created_at_utc"]} for u in unmatched],
    }


def _ts(s: str) -> float:
    from datetime import datetime
    return datetime.fromisoformat(s).timestamp()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packets", type=Path, default=DEFAULT_PACKETS)
    ap.add_argument("--rows", type=Path, default=DEFAULT_ROWS)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--seed", type=int, default=20260727)
    ap.add_argument("--mc-draws", type=int, default=2000)
    ap.add_argument("--null-draws", type=int, default=2000)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    cycles, placements = load(args.packets)

    report = {
        "schema": SCHEMA,
        "packet_source": str(args.packets),
        "trade_rows_source": str(args.rows),
        "seed": args.seed,
        "day_key_source": "src/components/ultimate_book/bar_provider.py:86-88",
        "cluster_cap_source": "src/components/ultimate_book/book_owner.py:1607-1617",
        "cluster_cap_config_at_head": {
            "ultimate_book_one_unit_per_cluster_per_day": False,
            "config_line": "config/agent_config.yaml:1373",
            "ultimate_book_cluster_cap_exempt_clusters": ["jpy"],
            "exempt_config_line": "config/agent_config.yaml:1374",
            "reachability": ("book_owner.py:1612 evaluates self._cluster_cap_on FIRST in a "
                             "short-circuiting `and`, so with the global boolean false the exempt "
                             "list is never consulted. Exempting jpy from a cap that is off buys "
                             "nothing; every cluster is effectively exempt."),
            "code_default": "book_owner.py:170 defaults the flag to True; the shipped config overrides it to False",
        },
        "not_changed": ("bar_provider.decision_day_of is untouched. B54 Part 2 is the owner's "
                        "decision; tests/ultimate_book/test_sleeve_server_clock.py:123-131 is the "
                        "deliberate tripwire and still passes."),
        "n_unit_placed_packets": len(placements),
        "part_a_day_key": part_a(cycles, rng, args.mc_draws),
        "part_b_cluster_cap": part_b(placements, args.rows, rng, args.null_draws),
    }

    args.out.mkdir(parents=True, exist_ok=True)
    dest = args.out / "DAY_KEY_MC.json"
    dest.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    print(f"wrote {dest}")

    a = report["part_a_day_key"]
    print(f"\n== Part A — day key")
    print(f"  bridge states carrying units: {a['distinct_bridge_states_carrying_units']} "
          f"(with recoverable intents: {a['of_which_have_recoverable_intents']})")
    print(f"  D2 reproduction: {a['d2_reproduction']['states_with_two_kelly_counts']} two-count / "
          f"{a['d2_reproduction']['states_with_two_kelly_multipliers']} two-multiplier "
          f"-> reproduces={a['d2_reproduction']['reproduces_register']}")
    cb = a["correlated_unit_buckets"]
    print(f"  (day,cluster) buckets: UTC {cb['distinct_day_cluster_buckets_utc_key']} -> runtime "
          f"{cb['distinct_day_cluster_buckets_runtime_key']}  (removed "
          f"{cb['buckets_removed_by_runtime_key']})")
    print(f"  cycles spanning >1 bar day: {cb['cycles_split_across_more_than_one_bar_day']}  "
          f"span histogram {cb['bar_day_span_histogram']}")
    sr = a["size_ratio_runtime_over_utc"]
    print(f"  per-cycle Kelly size ratio runtime/UTC: mean {sr['mean']:.6f}, "
          f"range [{sr['min']:.4f}, {sr['max']:.4f}], {sr['n_below_1']} down / {sr['n_above_1']} up")
    m = a["running_count_mc"]["summary"]
    print(f"  MC over the unrecoverable running count ({a['running_count_mc']['draws']} draws):")
    print(f"    running support: {a['running_count_mc']['running_support']}  "
          f"(max recorded na {a['running_count_mc']['max_recorded_na']}, "
          f"max per-cycle na {a['running_count_mc']['max_per_cycle_na']})")
    print(f"    mean size ratio {m['mean_size_ratio']['mean']:.6f} "
          f"p05..p95 [{m['mean_size_ratio']['p05']:.6f}, {m['mean_size_ratio']['p95']:.6f}] "
          f"full [{m['mean_size_ratio']['min']:.6f}, {m['mean_size_ratio']['max']:.6f}]")
    print(f"    frac of buckets whose size changes {m['frac_changed']['mean']:.6f} "
          f"p05..p95 [{m['frac_changed']['p05']:.6f}, {m['frac_changed']['p95']:.6f}]")

    print(f"\n== Part B — cluster cap ({report['n_unit_placed_packets']} recorded placements)")
    print(f"{'config':34s} {'placed':>7s} {'blkd':>5s} {'saved pp':>9s} "
          f"{'null mean':>10s} {'null p05..p95':>20s} {'pctile':>7s}")
    for name, b in report["part_b_cluster_cap"].items():
        if b["priced"] is None:
            print(f"{name:34s} {b['n_placed']:7d} {b['n_blocked']:5d} {'-':>9s}")
            continue
        n = b["null_control_random_blocking"]
        print(f"{name:34s} {b['n_placed']:7d} {b['n_blocked']:5d} "
              f"{b['observed_saved_pct_of_initial']*100:8.4f}% {n['saved_pct_of_initial_mean']*100:9.4f}% "
              f"{n['saved_pct_of_initial_p05']*100:9.4f}%..{n['saved_pct_of_initial_p95']*100:7.4f}% "
              f"{b['beats_null_percentile']:7.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

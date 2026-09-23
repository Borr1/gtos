"""Rebuild the K1-b cycle corpus from the sealed VPS packet export.

Session K's driver read a `cycles.pkl` from a wave-3 scratchpad that no longer
exists (`/private/tmp/claude-501/...`), so K1-b was not reproducible.  This
rebuilds it from the export itself, which is the durable artifact:

    /Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/
        ultimate_book_runtime_learning_packets.jsonl.gz

A **cycle** is one live generation pass, keyed by `created_at_utc`.  Only cycles
whose bridge carries `broker_profile_generation` are usable: that block is
written by the bridge at generation time and carries `n_candidates_in`, the
complete candidate counter (K1_GATE_RECEIPT.md section 3.1).

Emits `cycles.pkl` in the exact shape `k1b_replay.py` consumed:
    {key: {ns, created, bridge, shape, n_in, intents}}
`shape` = (active_spec_count, active_symbol_slot_count) -> which timeframes
advanced at that instant.
"""
import collections
import gzip
import json
import pickle
import sys

PACKETS = ("/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/"
           "ultimate_book_runtime_learning_packets.jsonl.gz")

#: Event types that name a (sleeve, symbol, decision_bar_iso) triple.  Live does
#: not name all of its candidates (D15/C6 attribution gap) — see K1 section 3.2.
NAMING_EVENTS = ("unit_admitted", "unit_shadow", "unit_skipped", "unit_placed")

#: GENERATION-side skips, not candidates.  `book_engine.py:503-510` appends
#: `future_decision_bar_time` to `generation_skips` and `:511` `continue`s
#: **before** any intent exists, so these slots were never in
#: `bridge.n_candidates_in` and the port — whose archive bars are clean UTC and
#: never look future — cannot reproduce them by construction.  Excluding them
#: reproduces K's live-named total of 383 exactly (915 named triples - 534
#: future-bar triples + 2 overlap).
#:
#: The record proves it without the source argument, which is the harder
#: evidence (found by a refuter): all 534 sit in **11 cycles whose own
#: `n_candidates_in` is 0** — the live engine's own complete counter says no
#: candidate existed there.  A subset sweep over all 90 observed skip reasons
#: found 275 subsets that reach 383 and **every one contains
#: `future_decision_bar_time`**; it is the unique minimal rule.
#:
#: They are kept separately because they are a measurement in their own right:
#: 534 decision-bar slots the deployed engine refused across 8 days, which is the
#: leaked-zero-broker-offset defect wave 3 repaired
#: (`book_engine._resolve_repair_offset_seconds`).
GENERATION_SIDE_SKIPS = frozenset({"future_decision_bar_time"})


def build(out_path: str, packets: str = PACKETS) -> dict:
    cycles: dict = {}
    named: dict[tuple[str, str], set] = collections.defaultdict(set)
    gen_skipped: dict[tuple[str, str], set] = collections.defaultdict(set)
    seen_events: collections.Counter = collections.Counter()
    for line in gzip.open(packets, "rt"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        ns = r.get("namespace")
        created = r.get("created_at_utc")
        if not ns or not created:
            continue
        seen_events[r.get("event_type")] += 1
        sleeve, sym, bar = r.get("sleeve"), r.get("symbol"), r.get("decision_bar_iso")
        if r.get("event_type") in NAMING_EVENTS and sleeve and sym and bar:
            if (r.get("event_type") == "unit_skipped"
                    and r.get("skip_reason") in GENERATION_SIDE_SKIPS):
                gen_skipped[(ns, created)].add((sleeve, sym, bar))
            else:
                named[(ns, created)].add((sleeve, sym, bar))
        bridge = r.get("bridge")
        if not isinstance(bridge, dict):
            continue
        gen = bridge.get("broker_profile_generation")
        if not isinstance(gen, dict):
            continue
        key = (ns, created)
        if key in cycles:
            continue
        cycles[key] = dict(
            ns=ns, created=created, bridge=bridge,
            shape=(gen.get("active_spec_count"), gen.get("active_symbol_slot_count")),
            n_in=bridge.get("n_candidates_in"), intents=[],
        )
    for key, c in cycles.items():
        c["intents"] = sorted(named.get(key, ()))
        c["intents_generation_skipped"] = sorted(gen_skipped.get(key, ()))
    with open(out_path, "wb") as fh:
        pickle.dump(cycles, fh)
    return cycles


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/sessionY/cycles.pkl"
    cycles = build(out)
    by_ns = collections.Counter(c["ns"] for c in cycles.values())
    print(f"cycles: {len(cycles)}")
    for ns, n in by_ns.most_common():
        sub = [c for c in cycles.values() if c["ns"] == ns]
        shapes = collections.Counter(c["shape"] for c in sub)
        n_named = len({t for c in sub for t in c["intents"]})
        n_skip = len({t for c in sub for t in c["intents_generation_skipped"]})
        n_counter = sum(c["n_in"] or 0 for c in sub)
        print(f"  {ns:28s} cycles={n:5d}  distinct_named={n_named:5d}  "
              f"gen_side_skipped={n_skip:5d}  counter_total={n_counter:5d}")
        for sh, k in sorted(shapes.items()):
            print(f"      shape {sh} : {k}")
    print(f"-> {out}")

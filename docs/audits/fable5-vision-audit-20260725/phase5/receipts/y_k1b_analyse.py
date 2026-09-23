"""K1-b scored per lineage, and the two lineages compared against each other.

Reproduces `phase3/receipts/k1b_analyse.py`'s two levels — COUNT (live's own
`bridge.n_candidates_in`, complete, the level at which zero is achievable) and
IDENTITY (the (sleeve, symbol, decision_bar_iso) set, bounded above by live's
54 % naming rate) — and adds the axis K1-b did not have: which code lineage the
port ran.

Usage:  python3 y_k1b_analyse.py /tmp/sessionY/raw_mainline.json /tmp/sessionY/raw_deployed.json \
                                 -o phase5/receipts/Y_K1B_LINEAGE.json
"""
import argparse
import collections
import json
import pathlib
import pickle


def _covered_symbols(profile_path: str, prefix: str) -> dict:
    """Canonical symbols with a delivered bar series, through the PRODUCTION
    resolver — the same crossing `k1b_replay.py` makes (`book_engine.py:461`)."""
    import glob
    import os
    import sys

    import yaml
    sys.path.insert(0, os.getcwd())
    from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
    prof = yaml.safe_load(open(profile_path)) or {}
    res = build_broker_symbol_resolver(prof)
    have = set()
    for p in glob.glob(f"/Users/borr/GTOSActive/vps-bars-20260727/{prefix}_*.csv.gz"):
        stem = os.path.basename(p)[:-7]
        tfn = stem.rsplit("_", 1)[1]
        have.add(res(stem[len(prefix) + 1:-(len(tfn) + 1)]))
    return {"__resolver__": res, "__have__": have}


def relive(payload: dict, cycles_path: str) -> dict:
    """Re-derive each row's live sets from a (possibly corrected) cycle corpus.

    The port's output for a cycle does not depend on live's intents, so a
    correction to the live side does not require a 6-minute re-replay.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "y_k1b_replay", str(pathlib.Path(__file__).with_name("y_k1b_replay.py")))
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)

    ns = payload.get("namespace", "operator_profile")
    profile_path, prefix = replay.NAMESPACES[ns]
    ctx = _covered_symbols(profile_path, prefix)
    res, have = ctx["__resolver__"], ctx["__have__"]
    cycles = pickle.load(open(cycles_path, "rb"))
    by_ts = {c["created"]: c for c in cycles.values() if c["ns"] == ns}
    for r in payload["rows"]:
        c = by_ts.get(r.get("cycle"))
        if c is None:
            continue
        live = [list(t) for t in c["intents"]]
        r["live"] = live
        r["live_covered"] = [t for t in live if res(t[1]) in have]
    return payload


def score(payload: dict) -> dict:
    rows = [r for r in payload["rows"] if "error" not in r]
    agree = 0
    dis = []
    for r in rows:
        n, p = r.get("n_in"), len(r["port"])
        if n is None:
            continue
        if n == p:
            agree += 1
        else:
            dis.append(dict(cycle=r["cycle"], shape=r["shape"], live_n=n, port_n=p,
                            live_named=[list(x) for x in r.get("live_covered", [])],
                            port=[list(x) for x in r["port"]]))
    tot = agree + len(dis)

    LIVE, LIVEC, PORT = set(), set(), set()
    for r in rows:
        LIVE |= {tuple(x) for x in r["live"]}
        LIVEC |= {tuple(x) for x in r.get("live_covered", [])}
        PORT |= {tuple(x) for x in r["port"]}
    per = collections.defaultdict(lambda: dict(agreed=0, live_only=0, port_only=0))
    for x in LIVEC & PORT:
        per[x[0]]["agreed"] += 1
    for x in LIVEC - PORT:
        per[x[0]]["live_only"] += 1
    for x in PORT - LIVEC:
        per[x[0]]["port_only"] += 1
    for s, d in per.items():
        denom = d["agreed"] + d["live_only"]
        d["live_recall"] = (d["agreed"] / denom) if denom else None
    return dict(
        lineage=payload["lineage"],
        namespace=payload.get("namespace", "operator_profile"),
        swapped=sorted((payload.get("lineage_report") or {}).get("modules") or {}),
        cycles=len(rows),
        count_agree=agree, count_total=tot,
        count_pct=(100.0 * agree / tot) if tot else None,
        over=sum(1 for d in dis if d["port_n"] > d["live_n"]),
        under=sum(1 for d in dis if d["port_n"] < d["live_n"]),
        over_sum=sum(d["port_n"] - d["live_n"] for d in dis if d["port_n"] > d["live_n"]),
        under_sum=sum(d["live_n"] - d["port_n"] for d in dis if d["live_n"] > d["port_n"]),
        live_named=len(LIVE), live_named_covered=len(LIVEC), port=len(PORT),
        agreed=len(LIVEC & PORT), live_only=len(LIVEC - PORT), port_only=len(PORT - LIVEC),
        counter_total=sum(r.get("n_in") or 0 for r in rows),
        per_sleeve={s: dict(d) for s, d in sorted(per.items())},
        _sets=dict(livec=LIVEC, port=PORT), _dis=dis,
    )


def table(s: dict) -> str:
    out = [f"lineage={s['lineage']}  cycles={s['cycles']}",
           f"  COUNT    {s['count_agree']}/{s['count_total']} ({s['count_pct']:.2f} %)  "
           f"over {s['over']} (+{s['over_sum']})  under {s['under']} (-{s['under_sum']})",
           f"  IDENTITY live_named {s['live_named']} (covered {s['live_named_covered']}) "
           f"port {s['port']} -> agreed {s['agreed']} live-only {s['live_only']} "
           f"port-only {s['port_only']}",
           f"  {'sleeve':32s} {'agreed':>7s} {'live-only':>10s} {'port-only':>10s} {'recall':>8s}"]
    for name, d in sorted(s["per_sleeve"].items(),
                          key=lambda kv: -(kv[1]["agreed"] + kv[1]["live_only"])):
        rec = "-" if d["live_recall"] is None else f"{100*d['live_recall']:.0f} %"
        out.append(f"  {name:32s} {d['agreed']:7d} {d['live_only']:10d} "
                   f"{d['port_only']:10d} {rec:>8s}")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raws", nargs="+")
    ap.add_argument("-o", "--out")
    ap.add_argument("--cycles", help="re-derive the live sets from this corpus")
    args = ap.parse_args()

    scored = []
    for path in args.raws:
        payload = json.load(open(path))
        if args.cycles:
            payload = relive(payload, args.cycles)
        s = score(payload)
        scored.append(s)
        print(table(s))
        print()

    doc = {"schema": "gtos.phase5.k1b_lineage.v1",
           "arms": [{k: v for k, v in s.items() if not k.startswith("_")} for s in scored]}

    if len(scored) == 2:
        a, b = scored           # a = mainline, b = deployed
        a_only = a["_sets"]["livec"] - a["_sets"]["port"]
        b_only = b["_sets"]["livec"] - b["_sets"]["port"]
        recovered = a_only - b_only
        lost = b_only - a_only
        print(f"CROSS-LINEAGE  live-only under {a['lineage']}: {len(a_only)}   "
              f"under {b['lineage']}: {len(b_only)}")
        print(f"  recovered by switching lineage: {len(recovered)}   newly missed: {len(lost)}")
        for label, s in (("recovered", recovered), ("newly missed", lost)):
            c = collections.Counter(x[0] for x in s)
            print(f"  {label} by sleeve: " + (", ".join(f"{k}={v}" for k, v in c.most_common())
                                              or "(none)"))
        doc["cross"] = {
            "a": a["lineage"], "b": b["lineage"],
            "live_only_a": len(a_only), "live_only_b": len(b_only),
            "recovered_by_b": sorted(map(list, recovered)),
            "newly_missed_by_b": sorted(map(list, lost)),
            "recovered_by_sleeve": dict(collections.Counter(x[0] for x in recovered)),
            "newly_missed_by_sleeve": dict(collections.Counter(x[0] for x in lost)),
            "still_missed_by_sleeve": dict(collections.Counter(x[0] for x in b_only)),
            "still_missed": sorted(map(list, b_only)),
        }
    if args.out:
        json.dump(doc, open(args.out, "w"), indent=1)
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()

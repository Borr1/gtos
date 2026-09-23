"""K1-b, replayed under a DECLARED code lineage.

Session K's driver (`phase3/receipts/k1b_replay.py`) is reproduced here with two
changes and no others:

  1. the cycle corpus is rebuilt from the sealed VPS packet export by
     `y_cycles.py`, instead of a wave-3 scratchpad that no longer exists;
  2. `--lineage {mainline,vps_redacted_host}` selects which code generation the port
     runs, via `replay_policy.generation_lineage`.

(2) is the point. The live record K1-b compares against was produced by
`redacted_host`, which has no `_server_clock.py`; mainline routes nine sleeves'
session hour through it. Replaying mainline against that record measures the
F7/B29 clock repair, not the port.

Usage:  python3 y_k1b_replay.py --lineage vps_redacted_host --out /tmp/sessionY/raw_deployed.json
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
import pickle
import sys
import time

sys.path.insert(0, os.getcwd())

from src.components.ultimate_book.admission import resolve_market_expansion_sleeves  # noqa: E402
from src.components.ultimate_book.sleeves.registry import active_specs  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.research_infra.replay_policy import generation_lineage as GL  # noqa: E402
from src.research_infra.replay_policy import packet_validation as PV  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource, GenerationPort  # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
TFN = {"M15": 15, "H1": 16385, "H4": 16388, "D1": 16408}

#: namespace -> (profile file, bar-archive prefix). redacted_account is the HOLD-OUT: its bar pull
#: is 14 of 43 symbols so K excluded it, but the lineage question only needs the sleeves
#: whose symbols ARE covered, and nothing about the shim was derived from it.
NAMESPACES = {
    "operator_profile": ("config/profiles/operator_profile.yaml", "FTMO"),
    "redacted_account_live_bee34003": ("config/profiles/redacted_account.yaml", "redacted_account"),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lineage", default=GL.MAINLINE, choices=[GL.MAINLINE, GL.DEPLOYED])
    ap.add_argument("--namespace", default="operator_profile", choices=sorted(NAMESPACES))
    ap.add_argument("--cycles", default="/tmp/sessionY/cycles.pkl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    NS = args.namespace
    profile_path, prefix = NAMESPACES[NS]

    import yaml
    base_rt = dict((yaml.safe_load(open("config/agent_config.yaml")) or {}).get(
        "gtos_vnext_runtime") or {})
    prof = yaml.safe_load(open(profile_path)) or {}
    res = build_broker_symbol_resolver(prof)

    files = {}
    for p in glob.glob(f"{BARS}/{prefix}_*.csv.gz"):
        stem = os.path.basename(p)[:-7]              # <PREFIX>_SYM_TF
        tfn = stem.rsplit("_", 1)[1]
        sym = stem[len(prefix) + 1:-(len(tfn) + 1)]
        if tfn in TFN:
            files[(res(sym), TFN[tfn])] = p          # key by BROKER symbol (book_engine.py:461)
    src = CsvBarSource(files, label=f"vps-bars-20260727/{prefix}")
    HAVE = {s for s, _ in files}
    print(f"bar series available: {len(files)}")

    me, _ = resolve_market_expansion_sleeves(
        policy=base_rt.get("ultimate_book_market_expansion_policy"),
        explicit_sleeves=base_rt.get("ultimate_book_market_expansion_sleeves") or [])
    specs = active_specs(None, include_candidate_book=True,
                         candidate_book_sleeves=base_rt.get("ultimate_book_candidate_book_sleeves"),
                         include_market_expansion_book=True, market_expansion_sleeves=me)
    tf_tags = collections.defaultdict(list)
    for s in specs:
        tf_tags[s.timeframe].append(s.tag)
    SHAPE_TAGS = {
        (6, 27): tf_tags[TFN["H4"]],
        (10, 53): tf_tags[TFN["M15"]],
        (13, 15): tf_tags[TFN["D1"]],
        (16, 80): tf_tags[TFN["M15"]] + tf_tags[TFN["H4"]],
        (19, 42): tf_tags[TFN["H4"]] + tf_tags[TFN["D1"]],
        (23, 68): tf_tags[TFN["M15"]] + tf_tags[TFN["D1"]],
        (29, 95): tf_tags[TFN["M15"]] + tf_tags[TFN["H4"]] + tf_tags[TFN["D1"]],
    }

    cycles = pickle.load(open(args.cycles, "rb"))
    ft = [c for c in cycles.values() if c["ns"] == NS]
    ft.sort(key=lambda c: c["created"] or "")
    if args.limit:
        ft = ft[:args.limit]
    print(f"replaying {len(ft)} FTMO cycles under lineage={args.lineage}")

    ports: dict = {}
    out: list = []
    t0 = time.time()
    with GL.lineage(args.lineage) as lineage_report:
        print("lineage:", json.dumps(lineage_report, sort_keys=True))
        for i, c in enumerate(ft):
            tags = SHAPE_TAGS.get(tuple(c["shape"]))
            if tags is None:
                out.append(dict(cycle=c["created"], shape=list(c["shape"]),
                                error="unknown_shape"))
                continue
            cfg = PV.config_from_bridge(c["bridge"], base=base_rt)
            ck = json.dumps({k: cfg.get(k) for k in sorted(cfg)}, sort_keys=True, default=str)
            if ck not in ports:
                ports[ck] = GenerationPort(cfg, src, namespace=f"k1b_y_{prefix}",
                                       broker_symbol=res)
            now = dt.datetime.fromisoformat(c["created"])
            r = ports[ck].generate(now, tags=tags)
            got = {(x.sleeve, x.symbol, x.decision_bar_iso) for x in r.candidates}
            live = set(map(tuple, c["intents"]))
            live_cov = {t for t in live if res(t[1]) in HAVE}
            out.append(dict(cycle=c["created"], shape=list(c["shape"]), n_in=c["n_in"],
                            live=sorted(live), live_covered=sorted(live_cov),
                            port=sorted(got)))
            if (i + 1) % 250 == 0:
                el = time.time() - t0
                print(f"  {i+1}/{len(ft)}  {el:.0f}s  ({el/(i+1):.2f}s/cycle)", flush=True)
    payload = {"lineage": args.lineage, "namespace": NS, "lineage_report": lineage_report,
               "n_cycles": len(ft), "rows": out}
    json.dump(payload, open(args.out, "w"))
    print(f"done in {time.time()-t0:.0f}s -> {args.out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Extract raw trade geometry for the FROZEN BOOTSTRAP days.

Lane 2 extracted geometry for the five 2026 months only.  The shipped rule and
every B3 arm train on `bootstrap (Oct/Nov 2025 dev + January 2026) + every
strictly prior day`, so an F2 arm that cannot see the bootstrap would be
handicapped against its own control.  This closes that gap: same sealed-sink
read, same field list, same output format as swarm2/lane2_receipts/extract_geom.py.

Read-only: opens sealed sinks through ReplayCompactEventSink.open_sealed
(hash-verified) and writes one gzip JSONL into job scratch.
"""
import gzip, importlib.util, json, sys, time
from pathlib import Path

REPO = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
sys.path.insert(0, str(REPO))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


j = load_module("w21_january_for_f2", Path("/private/tmp/w21_january_prequential.py"))
from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink

FIELDS = ("entry_price", "stop_loss", "take_profit_1", "decision_time_utc",
          "limit_first_expiry_utc", "symbol", "side", "origin_family", "trading_day")
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f2")
T0 = time.time()


def main():
    rows, counts = [], {}
    for day, root, authority in j.INITIAL_RUNS:
        sink = ReplayCompactEventSink.open_sealed(
            root=root, expected_authority_root_sha256=authority)
        n = 0
        for raw in sink.ledger("missed"):
            rec = {"k": raw["canonical_replay_candidate_instance_key"]}
            for f in FIELDS:
                rec[f] = raw.get(f)
            rows.append(rec); n += 1
        counts[str(day)] = n
        print(json.dumps({"t": round(time.time() - T0, 1), "dev_day": str(day), "n": n}), flush=True)
    for day, authority in j.JAN_RUNS:
        root = j.JAN_ROOT / day / "compact_events"
        sink = ReplayCompactEventSink.open_sealed(
            root=root, expected_authority_root_sha256=authority)
        n = 0
        for raw in sink.ledger("missed"):
            rec = {"k": raw["canonical_replay_candidate_instance_key"]}
            for f in FIELDS:
                rec[f] = raw.get(f)
            rows.append(rec); n += 1
        counts[str(day)] = n
        print(json.dumps({"t": round(time.time() - T0, 1), "jan_day": str(day), "n": n}), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT / "geom_boot.jsonl.gz", "wt") as fh:
        for rec in rows:
            fh.write(json.dumps(rec) + "\n")
    (OUT / "geom_boot_counts.json").write_text(json.dumps(counts, indent=1))
    print(json.dumps({"DONE": len(rows), "days": len(counts)}), flush=True)


if __name__ == "__main__":
    main()

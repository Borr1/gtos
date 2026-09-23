#!/usr/bin/env python3
"""OD-AI-7's premise-reader: did a session close produce a candle the engine dropped?

    python3 scripts/pre_gap_bar_premise.py --packets <packets.jsonl[.gz]> [--bars <dir>]

WHAT DECISION THIS CHANGES
--------------------------
`OD-AI-7` — turn on `run_book.py --recover-pre-gap-bar`? — is **not yet**, and its own
recommendation says why: the wiring is landed and inert, but the premise is `[UNVERIFIED]`.
`bar_provider.candles_to_bars`' docstring states it in as many words: *"whether a forming
candle exists at a session close is a property of the terminal"*. AB measured the defect on
the bar ARCHIVE (29 fires across five H4 sleeves, 4.26 % of 134,027 D1 trades); nobody has
measured it on the LIVE feed, and the queue's recommendation is to *"verify the live-feed
premise as a by-product of the packet carry, then decide"*.

This is that reader. It answers one question from accrued runtime packets, read-only, and it
is deliberately unable to answer anything else.

THE MECHANISM, AND WHY A LAG IS THE OBSERVABLE
----------------------------------------------
`candles_to_bars` drops the last candle unconditionally. Mid-session that candle is forming
and dropping it is right. At a session close there are two possible worlds:

  (a) the terminal still returns a forming candle for the next period -> the last CLOSED bar
      survives the drop, and the engine's decision bar is ~1 interval old. Nothing is lost.
  (b) the terminal returns no forming candle -> the last candle IS the freshly-closed
      decision bar, the drop discards it, and the engine's decision bar is ~2 intervals old.

So the discriminator is the **lag** between a cycle's `created_at_utc` and its
`decision_bar_iso`, measured in that sleeve's own bar intervals. World (b) is the defect.

WHY THE LAG ALONE IS A SIGNATURE AND NOT A PROOF
------------------------------------------------
A 2-interval lag has a second, innocent explanation: the market really was shut, so no bar
existed at the intervening grid slot and nothing was dropped. Distinguishing them needs one
more fact -- *did a closed bar exist at that slot?* -- and the bar archive answers it. So:

  packets alone         -> SIGNATURE_PRESENT / SIGNATURE_ABSENT
  packets + bar archive -> CONFIRMED / REFUTED, per observation

Both are reported. The verdict **fails closed**: anything short of CONFIRMED leaves OD-AI-7
where its own recommendation puts it, which is OFF. A tool for deciding whether to change what
an armed book trades must not be able to say "probably".

TWO HAZARDS THIS FILE OBEYS RATHER THAN REDISCOVERS
---------------------------------------------------
* **Bar timestamps are BROKER WALL CLOCK, not UTC.** `BARS_MANIFEST.json` says so on its own
  third line. Converted through `broker_clock.broker_epoch_to_utc`, which fails closed on an
  unregistered server. Never trust a `_utc` field name (CLAUDE.md §4).
* **The exported 2026-07-25 packet stream predates C4.** `spread_r` and broker deal timestamps
  are not on every evaluated leg there, and only a minority of its rows carry
  `decision_bar_iso` AND `timeframe` together. The reader reports its own field coverage as a
  first-class number, because a verdict computed over 0.7 % of a corpus is a different claim
  from one computed over all of it.

READ-ONLY. Imports no broker module, opens no terminal, writes only the file you name.
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import gzip
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.utils.broker_clock import (  # noqa: E402
    UnknownBrokerClockError,
    broker_epoch_to_utc,
    resolve_rule,
)

#: MT5 ENUM_TIMEFRAMES -> minutes, for the timeframes the book decides on.
TF_MINUTES = {1: 1, 5: 5, 15: 15, 30: 30, 16385: 60, 16388: 240, 16408: 1440, 32769: 10080}

#: namespace -> MT5 server string. The namespace is the only account identifier the packets
#: carry (tickets and logins are hashed by `redaction_policy`), and the clock rule keys on the
#: server. Unmapped namespaces are reported, never guessed: a wrong offset is silent.
NAMESPACE_SERVER = {
    "operator_profile": "FTMO-Server3",
    "redacted_account_live_bee34003": "redacted_account-Server 2",
}
#: bar-archive filename prefix per namespace.
NAMESPACE_ARCHIVE = {"operator_profile": "FTMO", "redacted_account_live_bee34003": "redacted_account"}
TF_NAME = {15: "M15", 16388: "H4", 16408: "D1", 16385: "H1"}

#: A cycle whose decision bar is at least this many intervals old is a candidate. 2.0 is not a
#: tuning knob: it is the boundary `book_engine.py:530-534` itself uses ("skip a bar whose
#: close is older than ~2 intervals"), so a candidate here is exactly a bar the recency guard
#: is about to refuse.
DEFAULT_STALE_INTERVALS = 1.95

VERDICTS = ("CONFIRMED", "CONFIRMED_CONFOUNDED_WITNESSES_ONLY", "REFUTED",
            "SIGNATURE_PRESENT_BARS_UNAVAILABLE", "SIGNATURE_ABSENT", "INSUFFICIENT_FIELDS")


# --------------------------------------------------------------------------- packets


def _open(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path, "rt")


def _parse_iso(s):
    if not isinstance(s, str) or not s:
        return None
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def read_observations(paths: list[Path]) -> tuple[list[dict], dict]:
    """Every packet that carries the three fields the question needs, plus the coverage."""
    obs: list[dict] = []
    cov = collections.Counter()
    for p in paths:
        with _open(p) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                cov["rows_read"] += 1
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    cov["rows_unparseable"] += 1
                    continue
                bar = _parse_iso(r.get("decision_bar_iso"))
                cyc = _parse_iso(r.get("created_at_utc"))
                tf = r.get("timeframe")
                if bar is None:
                    cov["no_decision_bar_iso"] += 1
                    continue
                if cyc is None:
                    cov["no_created_at_utc"] += 1
                    continue
                if tf is None:
                    cov["no_timeframe"] += 1
                    continue
                iv = TF_MINUTES.get(int(tf))
                if not iv:
                    cov["unknown_timeframe"] += 1
                    continue
                cov["usable"] += 1
                obs.append({
                    "namespace": r.get("namespace"), "symbol": r.get("symbol"),
                    "broker_symbol": r.get("broker_symbol"), "sleeve": r.get("sleeve"),
                    "timeframe": int(tf), "interval_minutes": iv,
                    "decision_bar_utc": bar, "cycle_utc": cyc,
                    "event_type": r.get("event_type"), "skip_reason": r.get("skip_reason"),
                    "bar_consumable": r.get("bar_consumable"),
                    "lag_intervals": (cyc - bar).total_seconds() / 60.0 / iv,
                })
    return obs, dict(cov)


def last_provably_closed_open(cycle: dt.datetime, bar: dt.datetime, iv: int) -> list[dt.datetime]:
    """Bar OPEN times strictly after `bar` whose close is <= `cycle`, on `bar`'s own grid.

    These are the slots the engine could have used and did not. Walking the grid from the bar
    it DID use is deliberate: it needs no assumption about where the broker's grid is anchored,
    which differs between the two servers and would be a second thing to get wrong.
    """
    out = []
    step = dt.timedelta(minutes=iv)
    t = bar + step
    while t + step <= cycle:
        out.append(t)
        t += step
        if len(out) > 4096:      # a runaway guard, not a policy
            break
    return out


# --------------------------------------------------------------------------- bar archive


class BarArchive:
    """Bar OPEN instants per (namespace, symbol, timeframe), in UTC. Lazy, read-only."""

    def __init__(self, root: Path):
        self.root = root
        self._cache: dict[tuple, set] = {}
        self._misses: list[str] = []

    def _path(self, namespace: str, symbol: str, tf: int) -> Path | None:
        pre = NAMESPACE_ARCHIVE.get(namespace)
        name = TF_NAME.get(tf)
        if not pre or not name or not symbol:
            return None
        p = self.root / f"{pre}_{symbol}_{name}.csv.gz"
        return p if p.is_file() else None

    def opens(self, namespace: str, symbol: str, tf: int) -> set | None:
        key = (namespace, symbol, tf)
        if key in self._cache:
            return self._cache[key]
        p = self._path(namespace, symbol, tf)
        if p is None:
            self._misses.append(f"{namespace}/{symbol}/{TF_NAME.get(tf, tf)}: no archive file")
            self._cache[key] = None
            return None
        server = NAMESPACE_SERVER.get(namespace)
        try:
            # `resolve_rule` raises UnknownBrokerClockError on an unmeasured server, which is
            # the fail-closed behaviour this reader wants: no offset is better than a guess.
            rule = resolve_rule(server)
            with gzip.open(p, "rt") as fh:
                rd = csv.DictReader(io.StringIO(fh.read()))
                # Broker wall clock, per BARS_MANIFEST.json. Convert, never assume UTC.
                opens = {broker_epoch_to_utc(int(row["time"]), rule)
                         for row in rd if row.get("time")}
        except UnknownBrokerClockError as e:
            self._misses.append(f"{namespace}: {e}")
            self._cache[key] = None
            return None
        except (OSError, KeyError, ValueError) as e:
            self._misses.append(f"{p.name}: {type(e).__name__}: {e}")
            self._cache[key] = None
            return None
        self._cache[key] = opens
        return opens

    @property
    def misses(self) -> list[str]:
        return sorted(set(self._misses))


# --------------------------------------------------------------------------- the read


def analyse(obs: list[dict], archive: BarArchive | None, stale: float) -> dict:
    cands = [o for o in obs if o["lag_intervals"] >= stale]
    future = [o for o in obs if o["lag_intervals"] < 0]
    per_obs = []
    n_confirmed = n_refuted = n_unresolved = 0
    for o in cands:
        slots = last_provably_closed_open(o["cycle_utc"], o["decision_bar_utc"],
                                          o["interval_minutes"])
        row = {
            "namespace": o["namespace"], "symbol": o["symbol"], "sleeve": o["sleeve"],
            "timeframe": TF_NAME.get(o["timeframe"], o["timeframe"]),
            "decision_bar_utc": o["decision_bar_utc"].isoformat(),
            "cycle_utc": o["cycle_utc"].isoformat(),
            "lag_intervals": round(o["lag_intervals"], 3),
            "event_type": o["event_type"], "skip_reason": o["skip_reason"],
            "skipped_grid_slots_utc": [s.isoformat() for s in slots],
        }
        if archive is None:
            row["resolution"] = "UNRESOLVED_NO_ARCHIVE"
            n_unresolved += 1
        else:
            opens = archive.opens(o["namespace"], o["symbol"], o["timeframe"])
            if opens is None:
                row["resolution"] = "UNRESOLVED_ARCHIVE_MISS"
                n_unresolved += 1
            else:
                existing = [s.isoformat() for s in slots if s in opens]
                row["slots_with_a_real_closed_bar"] = existing
                if existing:
                    row["resolution"] = "CONFIRMED_DROPPED_CLOSED_BAR"
                    n_confirmed += 1
                else:
                    row["resolution"] = "BENIGN_MARKET_WAS_SHUT"
                    n_refuted += 1
        # A `skip_reason` means the engine declined this unit for a reason of its own, and two
        # of those reasons make the row a weaker witness: `already_placed_this_bar` /
        # `already_placed_today` fire on the placement-ledger key, and a reader could argue the
        # bar being reported is a remembered one. (It is not — `book_engine.py:549,:590` sets
        # `decision_bar_iso` from `times[-1]` of THIS cycle's fetch — but the argument exists,
        # so the unconfounded subset is separated rather than defended.) `unit_admitted` and
        # `unit_shadow` rows with no skip reason are the clean witnesses.
        row["witness"] = "UNCONFOUNDED" if not o["skip_reason"] else "CONFOUNDED_BY_SKIP_REASON"
        per_obs.append(row)

    clean = [r for r in per_obs if r["resolution"] == "CONFIRMED_DROPPED_CLOSED_BAR"
             and r["witness"] == "UNCONFOUNDED"]
    if not obs:
        verdict = "INSUFFICIENT_FIELDS"
    elif not cands:
        verdict = "SIGNATURE_ABSENT"
    elif clean:
        # CONFIRMED requires at least one UNCONFOUNDED witness. A verdict that can be reached
        # entirely on rows the engine skipped for a placement-ledger reason is a verdict an
        # adversary gets to argue about, and this one decides whether to change what an armed
        # book trades.
        verdict = "CONFIRMED"
    elif n_confirmed:
        verdict = "CONFIRMED_CONFOUNDED_WITNESSES_ONLY"
    elif n_unresolved and not n_refuted:
        verdict = "SIGNATURE_PRESENT_BARS_UNAVAILABLE"
    elif n_refuted and not n_unresolved:
        verdict = "REFUTED"
    else:
        verdict = "SIGNATURE_PRESENT_BARS_UNAVAILABLE"

    def _hist(rows):
        h = collections.Counter()
        for o in rows:
            lg = o["lag_intervals"]
            h["<0 (future bar)" if lg < 0 else f"{min(int(lg), 5)}..{min(int(lg), 5) + 1}"] += 1
        return dict(sorted(h.items()))

    by_key = collections.Counter(
        (r["namespace"], r["timeframe"], r["sleeve"], r["symbol"]) for r in per_obs
        if r["resolution"] == "CONFIRMED_DROPPED_CLOSED_BAR")
    return {
        "verdict": verdict,
        "counts": {
            "usable_observations": len(obs),
            "stale_candidates": len(cands),
            "confirmed_dropped_closed_bar": n_confirmed,
            "confirmed_unconfounded": len(clean),
            "benign_market_was_shut": n_refuted,
            "unresolved": n_unresolved,
            "future_dated_decision_bars": len(future),
        },
        "lag_histogram_intervals": _hist(obs),
        "unconfounded_witnesses": clean,
        "confirmed_by_sleeve_symbol": [
            {"namespace": k[0], "timeframe": k[1], "sleeve": k[2], "symbol": k[3], "n": v}
            for k, v in sorted(by_key.items(), key=lambda kv: (-kv[1], str(kv[0])))],
        "observations": per_obs,
        "archive_misses": (archive.misses if archive else ["no --bars supplied"]),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--packets", nargs="+", required=True,
                    help="runtime learning packet JSONL(.gz) files. Read-only.")
    ap.add_argument("--bars", default=None,
                    help="bar archive directory (e.g. /Users/borr/GTOSActive/vps-bars-20260727). "
                         "Without it the reader can only report the SIGNATURE.")
    ap.add_argument("--stale-intervals", type=float, default=DEFAULT_STALE_INTERVALS,
                    help=f"candidate threshold in bar intervals (default {DEFAULT_STALE_INTERVALS}, "
                         "which is book_engine.py's own recency boundary)")
    ap.add_argument("-o", "--out", default=None, help="write the full JSON result here")
    ap.add_argument("--max-observations", type=int, default=500,
                    help="cap the per-observation list in the written JSON (0 = no cap)")
    a = ap.parse_args(argv)

    paths = [Path(p) for p in a.packets]
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        print(f"no such packet file(s): {missing}", file=sys.stderr)
        return 2

    obs, cov = read_observations(paths)
    archive = BarArchive(Path(a.bars)) if a.bars else None
    if archive is not None and not archive.root.is_dir():
        print(f"--bars {a.bars} is not a directory", file=sys.stderr)
        return 2

    res = analyse(obs, archive, a.stale_intervals)
    res["question"] = ("did a session close produce a candle the engine dropped as forming? "
                       "(OD-AI-7's premise)")
    res["decision"] = "OD-AI-7"
    res["field_coverage"] = cov
    res["field_coverage"]["usable_frac"] = (
        round(cov.get("usable", 0) / cov["rows_read"], 6) if cov.get("rows_read") else None)
    res["inputs"] = {"packets": [str(p) for p in paths], "bars": a.bars,
                     "stale_intervals": a.stale_intervals}
    res["fails_closed"] = ("anything short of CONFIRMED leaves OD-AI-7 where its own "
                           "recommendation puts it: --recover-pre-gap-bar stays OFF. A "
                           "CONFIRMED verdict makes the decision available; it does not take "
                           "it -- which bars an armed book trades is the owner's call.")
    res["what_this_cannot_answer"] = [
        "whether recovering the bar is PROFITABLE. AB measured the recovered D1 population at "
        "-0.0771 R against +0.0117 R, i.e. the defect is currently SAVING money on that "
        "family. This reader answers existence, not value.",
        "anything about a namespace not in NAMESPACE_SERVER, because the clock rule fails "
        "closed rather than guessing an offset.",
        "anything from packets that predate the field. The 2026-07-25 export carries "
        "decision_bar_iso + timeframe together on a minority of rows; read `field_coverage`.",
    ]

    if a.out:
        out = dict(res)
        if a.max_observations:
            out["observations"] = res["observations"][:a.max_observations]
            out["observations_truncated_from"] = len(res["observations"])
        Path(a.out).write_text(json.dumps(out, indent=1))

    c = res["counts"]
    print(f"VERDICT: {res['verdict']}")
    print(f"  usable observations   {c['usable_observations']} of {cov.get('rows_read')} rows "
          f"({res['field_coverage']['usable_frac']})")
    print(f"  stale candidates      {c['stale_candidates']} (>= {a.stale_intervals} intervals)")
    print(f"  CONFIRMED dropped     {c['confirmed_dropped_closed_bar']} "
          f"({c['confirmed_unconfounded']} unconfounded)")
    print(f"  benign (market shut)  {c['benign_market_was_shut']}")
    print(f"  unresolved            {c['unresolved']}")
    print(f"  future-dated bars     {c['future_dated_decision_bars']}")
    if res["confirmed_by_sleeve_symbol"]:
        print("  confirmed, by sleeve/symbol:")
        for r in res["confirmed_by_sleeve_symbol"][:12]:
            print(f"    {r['namespace']:26s} {r['timeframe']:4s} {r['sleeve']:38s} "
                  f"{r['symbol']:12s} n={r['n']}")
    if res["archive_misses"]:
        print(f"  archive misses ({len(res['archive_misses'])}): "
              f"{res['archive_misses'][:4]}")
    if a.out:
        print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

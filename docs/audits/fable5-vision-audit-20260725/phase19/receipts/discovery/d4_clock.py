"""d4_clock — clock and session-boundary audit of the broad family.

Four checks, all on the whole roster population:

 1. ANCHOR — is the lane-input tape actually true UTC?  Measured from the first
    M15 print of every trading week (FX opens Sunday 21:00 UTC under EU summer
    time, 22:00 UTC under EU winter time).
 2. TWO SESSION FUNCTIONS — `derive_session` (v4_timewarp:7488-7499, feeds the
    generator's ``kill_zone`` and hence ``route_session``) vs `_session_at`
    (broader_origin_generators:2433-2444, feeds ``session``/``session_bucket``).
    They differ in two ways: derive_session ignores the config kill_zones and
    uses an INCLUSIVE end boundary.  Disagreement is measured per row.
 3. DST — every session window is a FIXED UTC clock time while the exchanges it
    names move with their own DST calendars.  Measured: the share of rows whose
    session label would change if the window tracked the exchange's local clock.
 4. SESSION-OPEN ALIGNMENT — for session_open_range_break, the bar the family
    calls "the session open" against the exchange's real local open.
"""
from __future__ import annotations
import sys, os, gzip, json, glob, collections, bisect
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
sys.path.insert(0, "/tmp/d4")
import d4_lib as L

UTC = ZoneInfo("UTC")
LON = ZoneInfo("Europe/London")
NY = ZoneInfo("America/New_York")
TKY = ZoneInfo("Asia/Tokyo")
FRA = ZoneInfo("Europe/Berlin")

# exchange-local anchor for each named session, by symbol class
LOCAL_TZ = {"london": LON, "ny": NY, "tokyo": TKY}
SYM_LOCAL = {"GER40": {"london": FRA}}


def selected_index(s, T):
    j = bisect.bisect_right(s.t, T - timedelta(minutes=15)) - 1
    return j if j >= 0 else None


def derive_session_repl(sym, ts, windows_module):
    """v4_timewarp:7488-7499 — module dict only, INCLUSIVE end."""
    key = sym.upper().replace(".", "_")
    w = windows_module.get(key) or windows_module.get(sym) or ()
    minute = ts.hour * 60 + ts.minute
    for name, s, e in w:
        if L.hhmm(s) <= minute <= L.hhmm(e):
            return name
    return "off_configured_session"


def main(months, out_path):
    S = L.load_series()
    cw = L.config_windows()
    out = {}

    # ---- 1. anchor: first print of every trading week
    wk = collections.Counter()
    per_sym_first = collections.defaultdict(collections.Counter)
    for sym, s in S.items():
        prev = None
        for i, t in enumerate(s.t):
            if prev is not None and (t - prev) >= timedelta(hours=12):
                per_sym_first[sym][(t.weekday(), t.hour, t.minute)] += 1
                wk[(t.weekday(), t.hour, t.minute)] += 1
            prev = t
    out["weekly_open_anchor"] = {
        "note": "weekday 6 = Sunday; FX opens 21:00 UTC under EU summer, 22:00 under EU winter",
        "top": [{"weekday": k[0], "hh": k[1], "mm": k[2], "n": v}
                for k, v in wk.most_common(8)],
    }

    # ---- 2/3/4 over the roster population
    disagree = collections.Counter()
    pairs = collections.Counter()
    total = 0
    cfg_vs_module = {}
    for sym in S:
        a = tuple(cw.get(sym) or ())
        b = tuple(L.SESSION_WINDOWS.get(L.canon(sym)) or L.DEFAULT_EXPANSION)
        if a != b:
            cfg_vs_module[sym] = {"config": [list(x) for x in a], "module": [list(x) for x in b]}
    out["config_vs_module_session_windows"] = cfg_vs_module

    dst_shift = collections.Counter()
    sorb_align = collections.Counter()
    sorb_rows = 0
    fam_session = collections.defaultdict(collections.Counter)
    for m in months:
        rd = f"/tmp/d4/rosters/{m}"
        if not os.path.isdir(rd):
            rd = f"/tmp/f1/roster_{m}"
        files = [f for f in sorted(glob.glob(os.path.join(rd, "*.jsonl.gz")))
                 if os.path.exists(f.replace(".jsonl.gz", ".stats.json"))]
        for f in files:
            for line in gzip.open(f, "rt"):
                r = json.loads(line)
                if r["k"] != 15:
                    continue
                sym = r["s"]; s = S.get(sym)
                if s is None:
                    continue
                T = datetime.fromisoformat(r["t"]).replace(tzinfo=None)
                i = selected_index(s, T)
                if i is None:
                    continue
                bt = s.t[i]
                mins = bt.hour * 60 + bt.minute
                sess_gen = L.session_at(mins, s.win)          # candidate.session
                sess_kz = derive_session_repl(sym, T, L.SESSION_WINDOWS)  # kill_zone
                total += 1
                fam_session[r["f"]][sess_gen] += 1
                if sess_gen != sess_kz:
                    disagree[(sess_gen, sess_kz)] += 1
                    pairs["disagree"] += 1
                else:
                    pairs["agree"] += 1
                # ---- DST: would the label change if the window tracked local time?
                wins = s.win or ()
                utcdt = bt.replace(tzinfo=UTC)
                changed = None
                for name, ws, we in wins:
                    tz = (SYM_LOCAL.get(L.canon(sym), {}) or {}).get(name) or LOCAL_TZ.get(name)
                    if tz is None:
                        continue
                    # the window's UTC boundary as authored; the same wall-clock
                    # boundary in the exchange's own zone on THIS date
                    off_now = utcdt.astimezone(tz).utcoffset().total_seconds() / 60.0
                    # reference offset = the offset on 2025-07-01 (northern summer),
                    # which is the regime the fixed UTC windows were authored in
                    ref = datetime(2025, 7, 1, 12, tzinfo=UTC).astimezone(tz).utcoffset().total_seconds() / 60.0
                    shift = int(ref - off_now)   # +60 when the zone has left DST
                    if shift:
                        in_now = L.minute_in_window(mins, L.hhmm(ws), L.hhmm(we))
                        in_shift = L.minute_in_window((mins - shift) % 1440, L.hhmm(ws), L.hhmm(we))
                        if in_now != in_shift:
                            changed = (name, shift)
                            break
                dst_shift["changed" if changed else "same"] += 1
                if changed:
                    dst_shift[f"changed:{changed[0]}:{changed[1]}"] += 1
                # ---- session_open_range_break alignment
                if r["f"] == "session_open_range_break":
                    sorb_rows += 1
                    d0 = bt.date(); rs = i
                    while rs > 0:
                        pt = s.t[rs - 1]
                        if pt.date() != d0: break
                        if L.session_at(pt.hour * 60 + pt.minute, s.win) != sess_gen: break
                        rs -= 1
                    ob = s.t[rs]
                    tz = (SYM_LOCAL.get(L.canon(sym), {}) or {}).get(sess_gen) or LOCAL_TZ.get(sess_gen)
                    if tz is not None:
                        loc = ob.replace(tzinfo=UTC).astimezone(tz)
                        sorb_align[f"{sess_gen}:{loc.hour:02d}:{loc.minute:02d}"] += 1
    out["session_function_disagreement"] = {
        "rows": total, "agree": pairs["agree"], "disagree": pairs["disagree"],
        "disagree_rate": round(pairs["disagree"] / total, 6) if total else None,
        "top_pairs": [{"candidate_session": k[0], "kill_zone_session": k[1], "n": v}
                      for k, v in disagree.most_common(12)],
    }
    out["dst_label_change"] = {
        "rows": total,
        "changed": dst_shift["changed"],
        "changed_rate": round(dst_shift["changed"] / total, 6) if total else None,
        "detail": {k: v for k, v in dst_shift.items() if k.startswith("changed:")},
    }
    out["session_open_range_break_local_open_bar"] = {
        "rows": sorb_rows,
        "top": [{"session_local_time": k, "n": v} for k, v in sorb_align.most_common(14)],
    }
    out["family_session_mix"] = {k: dict(v.most_common()) for k, v in fam_session.items()}
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=1)
    print("anchor top:", out["weekly_open_anchor"]["top"][:4])
    print("cfg!=module symbols:", len(cfg_vs_module), list(cfg_vs_module)[:8])
    print("session disagree:", out["session_function_disagreement"]["disagree_rate"],
          out["session_function_disagreement"]["top_pairs"][:4])
    print("dst changed rate:", out["dst_label_change"]["changed_rate"], out["dst_label_change"]["detail"])
    print("sorb local open:", out["session_open_range_break_local_open_bar"]["top"][:8])


if __name__ == "__main__":
    main(sys.argv[1:-1], sys.argv[-1])

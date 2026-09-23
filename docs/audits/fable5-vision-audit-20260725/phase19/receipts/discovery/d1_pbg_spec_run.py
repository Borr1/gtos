"""d1_pbg_spec_run — Session PB's unmodified close-only roster harness, with the
candidate's own SPEC discriminators persisted alongside the geometry.

`pbg_run.emit_rows` keeps 10 fields and drops `source_fields`, so the roster on disk
carries only the ORIGIN FAMILY.  Lane d1 needs the finer spec the generator actually
emits (framework, sweep direction, setup tag, session, ...) to answer "per sleeve spec".

Nothing under `src/` is touched.  `pbg_run.run_day` resolves `emit_rows` as a module
global, so replacing that one function is the whole change; the generator call, the
grid, the MSO and the geometry are byte-for-byte PB's.

    python3 d1_pbg_spec_run.py --month 202603 --min-rr 1.5 --workers 2 --out /tmp/d1/spec_202603
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PBG = HERE.parent / "pbg"
sys.path.insert(0, str(PBG))

import pbg_run as P  # noqa: E402

# categorical source_fields keys worth persisting.  Anything str/bool/int is a spec
# discriminator; floats are measurements, Mappings are state objects — both dropped.
_SKIP = {
    "current_framework_replay_generation",
    "asof_control",
    "generation_rule",
    "mined_family_evidence",
    "source_time_utc",
    "source_boundary",
}


def emit_rows(cands, *, k, asof, bar_open, sym):
    out = []
    for c in cands:
        try:
            e = float(c["entry_price"])
            s = float(c["stop_loss"])
        except (TypeError, ValueError, KeyError):
            continue
        sf = c.get("source_fields") or {}
        spec = {}
        for key, val in sf.items():
            if key in _SKIP:
                continue
            if isinstance(val, bool):
                spec[key] = "T" if val else "F"
            elif isinstance(val, str) and len(val) <= 64:
                spec[key] = val
            elif isinstance(val, int):
                spec[key] = str(val)
        out.append(
            {
                "k": k,
                "t": P._iso(asof),
                "b": P._iso(bar_open),
                "s": sym,
                "f": c.get("origin_family"),
                "d": "L" if str(c.get("side", "")).upper() == "LONG" else "S",
                "e": e,
                "sl": s,
                "tp": float(c.get("take_profit_1") or 0.0),
                "cid": c.get("candidate_id"),
                "fw": c.get("framework"),
                "kz": sf.get("session_at_candidate") or sf.get("kill_zone"),
                "hb": sf.get("utc_hour_bucket"),
                "sp": spec,
            }
        )
    return out


P.emit_rows = emit_rows

if __name__ == "__main__":
    P.main()

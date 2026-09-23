"""CE-2 identity proof: with no `--entry-hour`, the generation path is byte-identical to the
commit this session branched from.

    python3 docs/audits/fable5-vision-audit-20260725/phase15/receipts/ce_entry_hour_identity.py <base-ref>

NON-VACUOUS BY ASSERTION. The first version of this proof ran against a fake broker with no
bars, generated zero intents on both sides, and printed PASS -- a comparison of two empty
lists. It now drives `test_book_engine.py`'s momentum fixture, which actually fires sleeves,
and REFUSES to report PASS if the fixture produced nothing. An identity proof that cannot fail
is not evidence.

Compared: the intents (sleeve/symbol/direction/stop/day), the meta rows, the generation
telemetry dict and the generation-skips list. All four, because the lever writes a telemetry
key when it is ON and must write none when it is OFF -- a flag that leaves a footprint while
off is a flag that changed the book by existing.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

BASE = sys.argv[1] if len(sys.argv) > 1 else "e19a2bb49"
MODPATH = "src/components/ultimate_book/book_engine.py"


def main() -> int:
    old = subprocess.run(["git", "show", f"{BASE}:{MODPATH}"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    tmp = Path(tempfile.mkdtemp())
    (tmp / "old.py").write_text(old, encoding="utf-8")

    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine as NEW
    spec = importlib.util.spec_from_file_location(
        "src.components.ultimate_book._base_engine", tmp / "old.py")
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "src.components.ultimate_book"
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    OLD = mod.UltimateBookLiveEngine

    from tests.ultimate_book.test_book_engine import _FakeMT5, _cfg, _fixture_now
    cfg, now = _cfg(True), _fixture_now()

    res = {}
    for label, cls in (("base", OLD), ("head", NEW)):
        e = cls(cfg, _FakeMT5(), str(tmp), namespace="ce_identity")
        intents, meta = e._generate_intents(tags=None, now=now)
        res[label] = (
            json.dumps([{"sleeve": i.sleeve, "symbol": i.symbol, "direction": i.direction,
                         "stop_dist": i.stop_dist, "decision_day": i.decision_day}
                        for i in intents], sort_keys=True),
            json.dumps(meta, sort_keys=True, default=str),
            json.dumps(e._last_generation_telemetry, sort_keys=True, default=str),
            json.dumps(e._last_generation_skips, sort_keys=True, default=str))
        print(f"  {label:5s}: {len(intents)} intents, {len(meta)} meta rows")

    if not json.loads(res["head"][0]):
        print("VACUOUS: the fixture generated no intents. Refusing to report a result.")
        return 2
    ok = True
    for i, name in enumerate(("intents", "meta", "telemetry", "skips")):
        same = res["base"][i] == res["head"][i]
        print(f"  {name:10s} identical: {same}")
        ok &= same
    print(f"\nbase ref  : {BASE}")
    print(f"RESULT    : {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

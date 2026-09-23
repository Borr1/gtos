"""VPS inject lander: path_scorecard without wholesale cycle replace."""
from __future__ import annotations
import ast
import json
import re
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ICT = timezone(timedelta(hours=7))
REPO = Path(r"host-local\redacted_host\repo")
STAGE = REPO / "_dig_stage_path_scorecard"
JUDGMENT_SRC = REPO / "judgment" / "warroom_shadow" / "src" / "judgment"
FANOUT = REPO / "judgment" / "warroom_shadow" / "warroom_shadow_jev_fanout_fields.json"
RESEARCH = REPO / "research" / "warroom_20260920"
CODILA = REPO / "research" / "codila_absorb" / "war_room"
PROVE = REPO / "judgment" / "warroom_shadow" / "prove" / "path_scorecard_smoke"

report = {
    "schema": "gtos.dig.qsx_path_scorecard_vps_land.v1",
    "as_of_ict": datetime.now(ICT).strftime("%Y-%m-%dT%H:%M:%S+07:00"),
    "place": False,
    "promote_grade_to_admit": False,
    "apply": False,
    "live_armed_set_touched": False,
    "paths_touched": [],
    "fanout_fields_added": 0,
    "hook_site": None,
    "smoke": "FAIL",
    "errors": [],
    "method": "inject_not_replace_cycle",
}

NEW_FIELDS = [
    {"field": "shadow.jev.path_scorecard.score", "type": "float|null", "desc": "path-quality composite 0-100 SHADOW; null=PROVISIONAL stub"},
    {"field": "shadow.jev.path_scorecard.grade", "type": "string", "desc": "PROVISIONAL|GOLD|SILVER|BRONZE|NEEDS_WORK|FLAGGED — SHADOW label; GOLD≠place"},
    {"field": "shadow.jev.path_scorecard.random_timing_p", "type": "float|null", "desc": "p-value vs random-timing null"},
    {"field": "shadow.jev.path_scorecard.beta", "type": "float|null", "desc": "buy-and-hold / benchmark beta"},
    {"field": "shadow.jev.path_scorecard.maxdd", "type": "float|null", "desc": "max drawdown"},
    {"field": "shadow.jev.path_scorecard.instrument", "type": "string", "desc": "affinity instrument"},
    {"field": "shadow.jev.path_scorecard.sleeve_id", "type": "string", "desc": "affinity sleeve"},
    {"field": "shadow.jev.path_scorecard.affinity_cell", "type": "string", "desc": "symbol|sleeve_id"},
    {"field": "shadow.jev.path_scorecard.place", "type": "bool", "const": False, "desc": "ALWAYS false"},
    {"field": "shadow.jev.path_scorecard.promote_grade_to_admit", "type": "bool", "const": False, "desc": "ALWAYS false"},
    {"field": "shadow.jev.path_scorecard.apply", "type": "bool", "const": False, "desc": "ALWAYS false"},
]


def cp(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    report["paths_touched"].append(str(dst))


def patch_fanout(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    fl = data.setdefault("field_list", [])
    existing = {e.get("field") for e in fl if isinstance(e, dict)}
    added = 0
    for nf in NEW_FIELDS:
        if nf["field"] not in existing:
            fl.append(nf)
            added += 1
    data["ts_ict"] = datetime.now(ICT).strftime("%Y-%m-%d %H:%M ICT")
    data["path_scorecard_shadow_wire"] = {
        "added": added,
        "steal": "STEAL-QSX-PATH-SCORECARD",
        "place": False,
        "promote_grade_to_admit": False,
        "apply": False,
    }
    bak = path.with_suffix(path.suffix + ".bak_pre_path_scorecard")
    if not bak.exists():
        shutil.copy2(path, bak)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report["paths_touched"].append(str(path))
    return added


IMPORT_BLOCK = """try:
    from .path_scorecard_shadow import emit_path_scorecard_into
except Exception:  # noqa: BLE001
    emit_path_scorecard_into = None  # type: ignore
"""

EMIT_LINES = [
    "# path_scorecard SHADOW stub — fields exist every cycle; place/promote/apply false",
    "if emit_path_scorecard_into is not None:",
    "    try:",
    '        sym = "UNKNOWN"',
    '        sleeve = "UNKNOWN"',
    "        try:",
    '            inv = payload.get("inventory") or {}',
    '            sleeves = inv.get("sleeves") or []',
    "            if sleeves:",
    "                s0 = sleeves[0]",
    "                if isinstance(s0, dict):",
    '                    sym = str(s0.get("symbol") or s0.get("instrument") or sym)',
    '                    sleeve = str(s0.get("sleeve_id") or s0.get("sleeve") or sleeve)',
    "                else:",
    "                    sleeve = str(s0)",
    "        except Exception:",
    "            pass",
    "        emit_path_scorecard_into(payload, symbol=sym, sleeve_id=sleeve, card_or_none=None)",
    '        notes.append("path_scorecard_shadow_stub")',
    "    except Exception as _psc_exc:  # noqa: BLE001",
    '        notes.append(f"path_scorecard_shadow_err:{type(_psc_exc).__name__}")',
    '        payload["shadow.jev.path_scorecard.place"] = False',
    '        payload["shadow.jev.path_scorecard.promote_grade_to_admit"] = False',
    '        payload["shadow.jev.path_scorecard.apply"] = False',
    '        payload["shadow.jev.path_scorecard.grade"] = "PROVISIONAL"',
    "else:",
    '    payload["shadow.jev.path_scorecard.place"] = False',
    '    payload["shadow.jev.path_scorecard.promote_grade_to_admit"] = False',
    '    payload["shadow.jev.path_scorecard.apply"] = False',
    '    payload["shadow.jev.path_scorecard.grade"] = "PROVISIONAL"',
]


def inject_cycle(cycle_path: Path) -> str:
    text = cycle_path.read_text(encoding="utf-8")
    bak = cycle_path.with_suffix(".py.bak_pre_path_scorecard")
    if not bak.exists():
        shutil.copy2(cycle_path, bak)

    if "path_scorecard SHADOW stub" in text and "emit_path_scorecard_into" in text:
        return "already_hooked:cycle.py:run_fluid_gate_cycle"

    if "from .path_scorecard_shadow import emit_path_scorecard_into" not in text:
        m = re.search(r"from \.veto import[^\n]+\n", text)
        if m:
            text = text[: m.end()] + IMPORT_BLOCK + text[m.end() :]
        else:
            m2 = list(re.finditer(r"^from \.[^\n]+\n", text, flags=re.M))
            if not m2:
                report["errors"].append("import_anchor_missing")
                return "missing_hook"
            pos = m2[-1].end()
            text = text[:pos] + IMPORT_BLOCK + text[pos:]

    if "path_scorecard SHADOW stub" not in text:
        m3 = re.search(r"\n([ \t]*)_write_json\([^\n]*payload", text)
        if not m3:
            report["errors"].append("write_json_anchor_missing")
            return "missing_hook"
        indent = m3.group(1)
        block = "\n" + "\n".join(indent + ln for ln in EMIT_LINES) + "\n"
        text = text[: m3.start()] + block + text[m3.start() :]

    cycle_path.write_text(text, encoding="utf-8")
    report["paths_touched"].append(str(cycle_path))
    return "injected:cycle.py:before__write_json"


def smoke() -> str:
    sys.path.insert(0, str(JUDGMENT_SRC))
    import path_scorecard_shadow as pss  # type: ignore

    fields = pss.fanout_fields(
        pss.compute_stub_path_scorecard(score=50.0, grade="PROVISIONAL"),
        symbol="XAUUSD",
        sleeve_id="dsp_spring_close",
    )
    assert fields["shadow.jev.path_scorecard.place"] is False
    assert fields["shadow.jev.path_scorecard.promote_grade_to_admit"] is False
    assert fields["shadow.jev.path_scorecard.apply"] is False
    bits: dict = {}
    pss.emit_path_scorecard_into(bits, symbol="XAUUSD", sleeve_id="dsp_spring_close", card_or_none=None)
    assert bits["shadow.jev.path_scorecard.grade"] == "PROVISIONAL"
    assert bits["shadow.jev.path_scorecard.place"] is False
    PROVE.mkdir(parents=True, exist_ok=True)
    out = PROVE / "path_scorecard_dry.jsonl"
    row = {
        "schema": "gtos.shadow.path_scorecard_dry.v1",
        "as_of_ict": datetime.now(ICT).strftime("%Y-%m-%dT%H:%M:%S+07:00"),
        **bits,
        "note": "dry stamp — not live admit",
    }
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    report["paths_touched"].append(str(out))
    ast.parse((JUDGMENT_SRC / "cycle.py").read_text(encoding="utf-8"))
    return "OK"


def main() -> int:
    src_emitter = STAGE / "judgment_src" / "path_scorecard_shadow.py"
    if not src_emitter.exists():
        report["errors"].append("emitter_missing_in_stage")
        print(json.dumps(report, indent=2))
        return 2

    JUDGMENT_SRC.mkdir(parents=True, exist_ok=True)
    cp(src_emitter, JUDGMENT_SRC / "path_scorecard_shadow.py")
    RESEARCH.mkdir(parents=True, exist_ok=True)
    cp(src_emitter, RESEARCH / "path_scorecard_shadow.py")

    report["fanout_fields_added"] = patch_fanout(FANOUT)
    for extra in [
        REPO / "judgment" / "astra" / "lab" / "warroom_intel_20260920" / "warroom_shadow_jev_fanout_fields.json",
        REPO / "judgment" / "warroom_shadow" / "judgment" / "astra" / "warroom_shadow_jev_fanout_fields.json",
    ]:
        if extra.exists():
            report["paths_touched"].append(f"extra_fanout+{patch_fanout(extra)}:{extra}")

    p0_src = STAGE / "research_warroom" / "p0_shadow_fanout.py"
    if p0_src.exists():
        cp(p0_src, RESEARCH / "p0_shadow_fanout.py")
        vps_p0 = JUDGMENT_SRC / "p0_shadow_fanout.py"
        if vps_p0.exists():
            bak_p0 = vps_p0.with_suffix(".py.bak_pre_path_scorecard")
            if not bak_p0.exists():
                shutil.copy2(vps_p0, bak_p0)
            cp(p0_src, vps_p0)

    cycle_path = JUDGMENT_SRC / "cycle.py"
    if cycle_path.exists():
        report["hook_site"] = inject_cycle(cycle_path)
    else:
        report["hook_site"] = "cycle.py_absent_on_vps"
        report["errors"].append("cycle_absent")

    CODILA.mkdir(parents=True, exist_ok=True)
    for name in [
        "QSX_PATH_SCORECARD_SHADOW_WIRE_20260920.md",
        "QSX_PATH_SCORECARD_SHADOW_WIRE_20260920.json",
        "XAG_FIRST_SCORE_PACK_HUNT_20260920.md",
        "XAG_FIRST_SCORE_PACK_HUNT_20260920.json",
        "FREQTRADE_PAIRLIST_LICENSE_REVIEW_20260920.md",
        "FREQTRADE_PAIRLIST_LICENSE_REVIEW_20260920.json",
    ]:
        s = STAGE / "wire_packs" / name
        if s.exists():
            cp(s, RESEARCH / name)
            cp(s, CODILA / name)

    try:
        report["smoke"] = smoke()
    except Exception as exc:  # noqa: BLE001
        report["smoke"] = "FAIL"
        report["errors"].append(f"smoke:{type(exc).__name__}:{exc}")

    report["dig_idle"] = True
    report["laws"] = {
        "place": False,
        "promote_grade_to_admit": False,
        "apply": False,
        "live_armed_set_untouched": True,
        "no_news_invent": True,
        "no_host-mesh": True,
        "cycle_not_wholesale_replaced": True,
    }
    out_json = RESEARCH / "QSX_PATH_SCORECARD_VPS_LAND_RUN_20260920.json"
    out_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report["paths_touched"].append(str(out_json))
    print(json.dumps(report, indent=2))
    return 0 if report["smoke"] == "OK" and not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

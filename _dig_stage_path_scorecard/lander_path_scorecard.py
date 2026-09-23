"""VPS lander: path_scorecard SHADOW emitter + fanout fields + cycle/p0 hook.
Laws: place=False, promote_grade_to_admit=False, apply=False, no live_armed_set, no NEWS, no host-mesh.
"""
from __future__ import annotations
import json
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ICT = timezone(timedelta(hours=7))
REPO = Path(r"host-local\redacted_host\repo")
JUDGMENT_SRC = REPO / "judgment" / "warroom_shadow" / "src" / "judgment"
FANOUT = REPO / "judgment" / "warroom_shadow" / "warroom_shadow_jev_fanout_fields.json"
RESEARCH = REPO / "research" / "warroom_20260920"
CODILA = REPO / "research" / "codila_absorb" / "war_room"
PROVE = REPO / "judgment" / "warroom_shadow" / "prove" / "path_scorecard_smoke"

# Staging dir = this script's parent (CopyFromBox lands lander + payload together)
STAGE = Path(__file__).resolve().parent

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
}


def cp(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    report["paths_touched"].append(str(dst))


def patch_fanout(path: Path) -> int:
    if not path.exists():
        report["errors"].append(f"fanout_missing:{path}")
        return 0
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
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report["paths_touched"].append(str(path))
    return added


def ensure_cycle_hook(cycle_path: Path) -> str:
    """If cycle lacks path_scorecard merge, inject smallest stub before _write_json."""
    text = cycle_path.read_text(encoding="utf-8")
    if "path_scorecard" in text and "emit_path_scorecard_into" in text:
        return "already_hooked:cycle.py:run_fluid_gate_cycle"
    # Prefer replacing with staged cycle if present
    staged = STAGE / "judgment_src" / "cycle.py"
    if staged.exists():
        cp(staged, cycle_path)
        return "replaced_with_staged:cycle.py:run_fluid_gate_cycle"
    report["errors"].append("cycle_hook_manual_needed")
    return "missing_hook"


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
    bits = {}
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
    return "OK"


def main() -> int:
    # 1) land emitter
    src_emitter = STAGE / "judgment_src" / "path_scorecard_shadow.py"
    if not src_emitter.exists():
        src_emitter = STAGE / "research_warroom" / "path_scorecard_shadow.py"
    if not src_emitter.exists():
        report["errors"].append("emitter_missing_in_stage")
        print(json.dumps(report, indent=2))
        return 2
    JUDGMENT_SRC.mkdir(parents=True, exist_ok=True)
    cp(src_emitter, JUDGMENT_SRC / "path_scorecard_shadow.py")

    # 2) fanout fields
    report["fanout_fields_added"] = patch_fanout(FANOUT)

    # 3) research mirror + p0
    RESEARCH.mkdir(parents=True, exist_ok=True)
    cp(src_emitter, RESEARCH / "path_scorecard_shadow.py")
    p0_src = STAGE / "research_warroom" / "p0_shadow_fanout.py"
    if p0_src.exists():
        cp(p0_src, RESEARCH / "p0_shadow_fanout.py")

    # 4) cycle hook
    cycle_path = JUDGMENT_SRC / "cycle.py"
    if cycle_path.exists() or (STAGE / "judgment_src" / "cycle.py").exists():
        report["hook_site"] = ensure_cycle_hook(cycle_path)
    else:
        report["hook_site"] = "cycle.py_absent_on_vps"
        report["errors"].append("cycle_absent")

    # 5) wire packs
    CODILA.mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
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

    # 6) smoke
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
    }
    out_json = RESEARCH / "QSX_PATH_SCORECARD_VPS_LAND_RUN_20260920.json"
    out_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report["paths_touched"].append(str(out_json))
    print(json.dumps(report, indent=2))
    return 0 if report["smoke"] == "OK" and not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

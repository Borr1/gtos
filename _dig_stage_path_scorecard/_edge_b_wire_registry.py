"""Wire Edge B sleeve into VPS registry as RESEARCH_DRAFT only — not BUILT/ACTIVE."""
from __future__ import annotations
import json
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

ICT = timezone(timedelta(hours=7))
REPO = Path(r"host-local\redacted_host\repo")
SLEEVES = REPO / "src" / "components" / "ultimate_book" / "sleeves"
REG = SLEEVES / "registry.py"
MOD = SLEEVES / "sub_mid_dn_re_proxy_eurusd_short_m15_atr.py"
ADM = REPO / "src" / "components" / "ultimate_book" / "admission.py"
RESEARCH = REPO / "research" / "warroom_20260920"
CODILA = REPO / "research" / "codila_absorb" / "war_room"
TAG = "sub_mid_dn_re_proxy_eurusd_short_m15_atr"

report = {
    "schema": "gtos.dig.edge_b_vps_land_wire.v1",
    "as_of_ict": datetime.now(ICT).strftime("%Y-%m-%dT%H:%M:%S+07:00"),
    "tag": TAG,
    "place": False,
    "apply": False,
    "live_armed_set_touched": False,
    "f5_contract_touched": False,
    "paths_touched": [],
    "errors": [],
    "smoke": "FAIL",
}

IMPORT_LINE = f"    {TAG},"
IMPORT_BLOCK_MARKER = "# DIG_EDGE_B_RESEARCH_DRAFT_IMPORT"

DRAFT_DICT = f'''
# ===========================================================================================
# DIG / CHAIR ENFORCE B — RESEARCH_DRAFT only (2026-09-20). NOT in BUILT / NOT in active_specs
# unless Chair explicitly opts in later. place=false · apply=false · no live_armed_set.
# NEVER alias to sub_mid_dn_revert (H4 LONG CLEAN3).
# ===========================================================================================
RESEARCH_DRAFT_BUILT: dict[str, SleeveSpec] = {{
    "{TAG}": SleeveSpec(
        "{TAG}",
        {TAG}.generate,
        TF_M15,
        "fx_reversion_research",
        {TAG}.ON_SURFACE,
    ),
}}
'''

ADM_DRAFT = f'''
# ===========================================================================================
# DIG / CHAIR ENFORCE B — admission confidence DRAFT only (2026-09-20).
# NOT spliced into SLEEVE_REGISTRY / CLEAN3_REGISTRY. No live_armed until Chair APPLY.
# ===========================================================================================
RESEARCH_DRAFT_SLEEVE_REGISTRY: dict[str, "SleeveSpec"] = {{
    "{TAG}": SleeveSpec(
        "{TAG}", 0.15, "fx_major",
        ("EURUSD",),
        "forward_only",
        "EURUSD M15 SHORT mid-stretch>=1ATR London/NY dn_re proxy; Module_ATR; "
        "NOT clean3 sub_mid_dn_revert H4 LONG; place=false until Chair APPLY"),
}}
'''


def main() -> int:
    if not MOD.exists():
        report["errors"].append(f"module_missing:{MOD}")
        print(json.dumps(report, indent=2))
        return 2

    # smoke module attrs
    import importlib.util
    import sys
    sys.path.insert(0, str(REPO))
    spec = importlib.util.spec_from_file_location(TAG, MOD)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    assert mod.TAG == TAG
    assert mod.ON_SURFACE == ("EURUSD",)
    assert mod.DIRECTION == -1
    assert mod.PLACE is False and mod.APPLY is False and mod.LIVE_ARMED is False
    assert mod.NEVER_ALIAS_TO == "sub_mid_dn_revert"
    report["paths_touched"].append(str(MOD))
    report["module_smoke"] = {
        "TAG": mod.TAG,
        "ON_SURFACE": list(mod.ON_SURFACE),
        "DIRECTION": mod.DIRECTION,
        "PLACE": mod.PLACE,
        "APPLY": mod.APPLY,
        "LIVE_ARMED": mod.LIVE_ARMED,
        "has_generate": callable(getattr(mod, "generate", None)),
        "DRAFT_SLEEVESPEC_live_armed": mod.DRAFT_SLEEVESPEC.get("live_armed"),
    }

    # patch registry.py
    text = REG.read_text(encoding="utf-8")
    bak = REG.with_suffix(".py.bak_pre_edge_b")
    if not bak.exists():
        shutil.copy2(REG, bak)

    if "RESEARCH_DRAFT_BUILT" not in text:
        # add import inside the big `from . import (` block — find a safe anchor before closing paren of imports
        # Prefer appending after last dsp import line if present, else after `from . import (` first chunk
        if TAG not in text:
            # Insert as separate import statement after the big import block ends (first occurrence of )\n from or )\n\n#)
            # Safer: add `from . import sub_mid_...` as its own line after dataclass imports area
            m = re.search(r"(from \. import \(\n)", text)
            if m:
                # add to the multi-import list near end before closing paren of first big block
                # Find CANDIDATE_BUILT or BUILT start and insert import just before BUILT
                pass
            # Always use standalone import to avoid breaking huge paren list
            anchor = "@dataclass(frozen=True)"
            if anchor not in text:
                report["errors"].append("dataclass_anchor_missing")
            else:
                text = text.replace(
                    anchor,
                    f"from . import {TAG}  # DIG_EDGE_B_RESEARCH_DRAFT_IMPORT\n\n{anchor}",
                    1,
                )
        # append RESEARCH_DRAFT_BUILT before active_specs
        if "def active_specs(" not in text:
            report["errors"].append("active_specs_missing")
        else:
            text = text.replace(
                "def active_specs(",
                DRAFT_DICT + "\n\ndef active_specs(",
                1,
            )
        REG.write_text(text, encoding="utf-8")
        report["paths_touched"].append(str(REG))
        report["registry_wire"] = "RESEARCH_DRAFT_BUILT_added_not_in_active_specs"
    else:
        report["registry_wire"] = "already_present"

    # admission draft append if missing
    if ADM.exists():
        at = ADM.read_text(encoding="utf-8")
        if "RESEARCH_DRAFT_SLEEVE_REGISTRY" not in at and TAG not in at[at.find("SLEEVE_REGISTRY"):at.find("SLEEVE_REGISTRY")+5000] if "SLEEVE_REGISTRY" in at else True:
            bak_a = ADM.with_suffix(".py.bak_pre_edge_b")
            if not bak_a.exists():
                shutil.copy2(ADM, bak_a)
            # append at end — draft dict only, not merged into live registries
            if "RESEARCH_DRAFT_SLEEVE_REGISTRY" not in at:
                ADM.write_text(at.rstrip() + "\n" + ADM_DRAFT + "\n", encoding="utf-8")
                report["paths_touched"].append(str(ADM))
                report["admission_wire"] = "RESEARCH_DRAFT_SLEEVE_REGISTRY_appended"
            else:
                report["admission_wire"] = "already_present"
        else:
            if "RESEARCH_DRAFT_SLEEVE_REGISTRY" in at:
                report["admission_wire"] = "already_present"
            else:
                bak_a = ADM.with_suffix(".py.bak_pre_edge_b")
                if not bak_a.exists():
                    shutil.copy2(ADM, bak_a)
                ADM.write_text(at.rstrip() + "\n" + ADM_DRAFT + "\n", encoding="utf-8")
                report["paths_touched"].append(str(ADM))
                report["admission_wire"] = "RESEARCH_DRAFT_SLEEVE_REGISTRY_appended"
    else:
        report["errors"].append("admission_missing")

    # verify registry syntax + RESEARCH_DRAFT not default-active
    import ast
    ast.parse(REG.read_text(encoding="utf-8"))
    # ensure active_specs body does not reference RESEARCH_DRAFT_BUILT
    rt = REG.read_text(encoding="utf-8")
    fn = rt[rt.find("def active_specs("): rt.find("def active_specs(") + 2500]
    if "RESEARCH_DRAFT_BUILT" in fn:
        report["errors"].append("RESEARCH_DRAFT_leaked_into_active_specs")
    else:
        report["active_specs_isolated"] = True

    # copy receipts to warroom
    RESEARCH.mkdir(parents=True, exist_ok=True)
    CODILA.mkdir(parents=True, exist_ok=True)

    report["smoke"] = "OK" if not report["errors"] else "FAIL"
    report["dig_idle"] = True
    report["laws"] = {
        "place": False,
        "apply": False,
        "live_armed_set_untouched": True,
        "f5_contract_untouched": True,
        "not_in_BUILT": True,
        "not_in_active_specs_default": True,
        "never_alias_to": "sub_mid_dn_revert",
    }
    out = RESEARCH / "EDGE_B_VPS_LAND_WIRE_20260920.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report["paths_touched"].append(str(out))
    (CODILA / "EDGE_B_VPS_LAND_WIRE_20260920.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["smoke"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())

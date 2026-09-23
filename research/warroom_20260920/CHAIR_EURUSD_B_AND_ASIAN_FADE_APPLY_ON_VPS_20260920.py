#!/usr/bin/env python3
"""CHAIR APPLY 20260920 — Package B + asian_fade SAME_TAG on Challenge operator.

Run ON VPS (machineId 7cfa9657 / Admin tree). Owner locked Chair APPLY.
- Arm sub_mid_dn_re_proxy_eurusd_short_m15_atr (NEW) RESEARCH_DRAFT -> live
- Arm asian_fade (SAME_TAG) via DISPLACEMENT_BUILT copy + tags
- ONE remint for BOTH tags; bump f5_launch hard count +2
- place=writer; Jev never places; NEVER alias sub_mid_dn_revert
"""
from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ICT = timezone(timedelta(hours=7))
AS_OF = datetime.now(ICT).strftime("%Y-%m-%dT%H:%M:%S+07:00")
UTC = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

TAG_B = "sub_mid_dn_re_proxy_eurusd_short_m15_atr"
TAG_AF = "asian_fade"
NEVER = "sub_mid_dn_revert"
NEW_TAGS = [TAG_B, TAG_AF]

ADMIN_ROOT = Path(r"host-local\redacted_host")
REPO = ADMIN_ROOT / "repo"
SLEEVES = REPO / "src" / "components" / "ultimate_book" / "sleeves"
REG = SLEEVES / "registry.py"
ADM = REPO / "src" / "components" / "ultimate_book" / "admission.py"
MOD_B = SLEEVES / f"{TAG_B}.py"
CONTRACT = ADMIN_ROOT / "launch_contracts" / "operator.json"
LAUNCH = ADMIN_ROOT / "f5_launch.ps1"
TOKEN_DIR = Path(r"host-local\.gtos\activation-f5")
VENV_PY = REPO / ".venv" / "Scripts" / "python.exe"
MSI_REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
WARROOM = REPO / "research" / "warroom_20260920"
JUDGMENT_LIVE = REPO / "judgment" / "live"

report: dict = {
    "schema": "gtos.chair.eurusd_b_and_asian_fade_apply.v1",
    "as_of_ict": AS_OF,
    "as_of_utc": UTC,
    "machineId": "7cfa9657-805b-4e9c-9fbb-886c500f997b",
    "login": "0",
    "namespace": "operator",
    "tags_add": NEW_TAGS,
    "never_alias_to": NEVER,
    "place": "writer",
    "apply": True,
    "live_armed": True,
    "steps": {},
    "errors": [],
    "blocked": False,
}


def _bak(p: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    b = p.with_suffix(p.suffix + f".bak_chair_apply_{stamp}")
    if p.exists() and not b.exists():
        shutil.copy2(p, b)
    return b


def step_module_b() -> None:
    if not MOD_B.exists():
        report["errors"].append(f"module_missing:{MOD_B}")
        return
    _bak(MOD_B)
    text = MOD_B.read_text(encoding="utf-8")
    text = re.sub(r"^PLACE = False", "PLACE = True", text, count=1, flags=re.M)
    text = re.sub(r"^APPLY = False", "APPLY = True", text, count=1, flags=re.M)
    text = re.sub(r"^LIVE_ARMED = False", "LIVE_ARMED = True", text, count=1, flags=re.M)
    old = "    if PLACE or APPLY or LIVE_ARMED:\n        return None"
    new = (
        "    # CHAIR_APPLY_20260920: LIVE_ARMED enables emit\n"
        "    if not LIVE_ARMED:\n"
        "        return None"
    )
    if old in text:
        text = text.replace(old, new, 1)
    elif "if not LIVE_ARMED:" not in text:
        report["errors"].append("module_b_generate_gate_unpatched")
    text = text.replace('"live_armed": False', '"live_armed": True', 1)
    text = text.replace('"place": False', '"place": True', 1)
    text = text.replace('"apply": False', '"apply": True', 1)
    MOD_B.write_text(text, encoding="utf-8")
    import importlib.util
    spec = importlib.util.spec_from_file_location(TAG_B, MOD_B)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    assert mod.PLACE is True and mod.APPLY is True and mod.LIVE_ARMED is True
    assert mod.ON_SURFACE == ("EURUSD",) and mod.DIRECTION == -1
    assert mod.NEVER_ALIAS_TO == NEVER
    report["steps"]["module_b"] = {"ok": True, "PLACE": True, "APPLY": True, "LIVE_ARMED": True}


def step_registry() -> None:
    _bak(REG)
    text = REG.read_text(encoding="utf-8")
    if f"from . import {TAG_B}" not in text and f"    {TAG_B}," not in text:
        anchor = "@dataclass(frozen=True)"
        if anchor in text:
            text = text.replace(
                anchor,
                f"from . import {TAG_B}  # CHAIR_APPLY_20260920\n\n{anchor}",
                1,
            )
    spec_b = (
        f'    "{TAG_B}": SleeveSpec(\n'
        f'        "{TAG_B}", {TAG_B}.generate, TF_M15, "fx_reversion_research",\n'
        f"        {TAG_B}.ON_SURFACE, bar_count=220),\n"
    )
    af_snip = (
        f'    "{TAG_AF}": SleeveSpec(\n'
        f'        "{TAG_AF}", asian_fade.generate, TF_M15, "fx_reversion",\n'
        f"        asian_fade.ON_SURFACE, bar_count=220),\n"
    )
    if "DISPLACEMENT_BUILT" not in text:
        block = (
            "\n# CHAIR_APPLY_20260920 — DISPLACEMENT_BUILT (M15 dsp-style)\n"
            "DISPLACEMENT_BUILT: dict[str, SleeveSpec] = {\n"
            + af_snip
            + spec_b
            + "}\n"
        )
        text = text.replace("def active_specs(", block + "\ndef active_specs(", 1)
    else:
        disp_start = text.find("DISPLACEMENT_BUILT")
        disp_chunk = text[disp_start : disp_start + 12000]
        if TAG_B not in disp_chunk:
            text = text.replace(
                "DISPLACEMENT_BUILT: dict[str, SleeveSpec] = {",
                "DISPLACEMENT_BUILT: dict[str, SleeveSpec] = {\n" + spec_b,
                1,
            )
        if TAG_AF not in disp_chunk:
            text = text.replace(
                "DISPLACEMENT_BUILT: dict[str, SleeveSpec] = {",
                "DISPLACEMENT_BUILT: dict[str, SleeveSpec] = {\n" + af_snip,
                1,
            )
    text = text.replace(
        "RESEARCH_DRAFT only (2026-09-20). NOT in BUILT / NOT in active_specs",
        "CHAIR_APPLY_20260920 — kept RESEARCH_DRAFT_BUILT + DISPLACEMENT_BUILT belt+suspenders",
    )
    needle = "    built = dict(BUILT)"
    if needle in text and "CHAIR_APPLY_20260920 belt+suspenders" not in text:
        inject = (
            "    built = dict(BUILT)\n"
            "    # CHAIR_APPLY_20260920 belt+suspenders: displacement + research draft tags\n"
            "    if 'DISPLACEMENT_BUILT' in globals():\n"
            "        built.update(DISPLACEMENT_BUILT)\n"
            "    if 'RESEARCH_DRAFT_BUILT' in globals():\n"
            "        built.update(RESEARCH_DRAFT_BUILT)\n"
        )
        text = text.replace(needle, inject, 1)
    REG.write_text(text, encoding="utf-8")
    ast.parse(text)
    report["steps"]["registry"] = {"ok": True, "displacement_tags": NEW_TAGS}


def step_admission() -> None:
    _bak(ADM)
    text = ADM.read_text(encoding="utf-8")
    entry_b = (
        f'    "{TAG_B}": SleeveSpec(\n'
        f'        "{TAG_B}", 0.15, "fx_major",\n'
        f'        ("EURUSD",),\n'
        f'        "forward_only",\n'
        f'        "EURUSD M15 SHORT mid-stretch>=1ATR London/NY dn_re proxy; Module_ATR; '
        f'NOT clean3 {NEVER} H4 LONG; CHAIR_APPLY_20260920"),\n'
    )
    if "RESEARCH_DRAFT_SLEEVE_REGISTRY" in text and TAG_B in text:
        m = re.search(
            rf'"{re.escape(TAG_B)}":\s*SleeveSpec\(\s*"[^"]+",\s*([0-9.]+),\s*"([^"]+)"',
            text,
        )
        if m:
            conf, asset = m.group(1), m.group(2)
            entry_b = (
                f'    "{TAG_B}": SleeveSpec(\n'
                f'        "{TAG_B}", {conf}, "{asset}",\n'
                f'        ("EURUSD",),\n'
                f'        "forward_only",\n'
                f'        "EURUSD M15 SHORT CHAIR_APPLY_20260920; NEVER alias {NEVER}"),\n'
            )
    for reg_name in ("SLEEVE_REGISTRY", "CLEAN3_REGISTRY"):
        if reg_name not in text:
            report["errors"].append(f"admission_missing_{reg_name}")
            continue
        idx = text.find(f"{reg_name}:")
        chunk = text[idx : idx + 12000]
        if TAG_B in chunk:
            continue
        m = re.search(rf"{reg_name}:\s*dict\[[^\]]+\]\s*=\s*\{{", text)
        if not m:
            report["errors"].append(f"admission_anchor_{reg_name}")
            continue
        insert_at = m.end()
        text = text[:insert_at] + "\n" + entry_b + text[insert_at:]
    ADM.write_text(text, encoding="utf-8")
    ast.parse(text)
    report["steps"]["admission"] = {"ok": True, "draft_mirror_kept": True}


def step_contract_and_launch() -> None:
    _bak(CONTRACT)
    _bak(LAUNCH)
    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    tb = data.setdefault("token_bound", {})
    csv = str(tb.get("selected_tags_csv") or "")
    tags = [t for t in csv.split(",") if t]
    before_n = len(tags)
    for t in NEW_TAGS:
        if t not in tags:
            tags.append(t)
    for key in ("selected_tags", "tags", "selected_tags_list"):
        if key in tb and isinstance(tb[key], list):
            for t in NEW_TAGS:
                if t not in tb[key]:
                    tb[key].append(t)
    tb["selected_tags_csv"] = ",".join(tags)
    tb["selected_tag_count"] = len(tags)
    after_n = len(tags)
    CONTRACT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    size_usd = tb.get("f5_minimal_size_usd")
    notional = tb.get("f5_notional_initial_usd")
    lp = LAUNCH.read_text(encoding="utf-8")

    def bump_ne(m: re.Match) -> str:
        old = int(m.group(1))
        if old == before_n:
            return m.group(0).replace(str(old), str(after_n), 1)
        return m.group(0)

    lp2 = re.sub(r"(?:-ne|!=)\s*(\d{2,3})", bump_ne, lp)
    lp2 = re.sub(
        r"(tagList\.Count\s*-ne\s*)(\d{2,3})",
        lambda m: m.group(1) + str(after_n) if int(m.group(2)) == before_n else m.group(0),
        lp2,
    )
    # strip bare asian_fade from hard-off lists; keep asian_fade_widen blocked
    lp2 = re.sub(r"([\[,\s])'asian_fade'(?!\w)", r"\1", lp2)
    lp2 = re.sub(r'([\[,\s])"asian_fade"(?!\w)', r"\1", lp2)
    LAUNCH.write_text(lp2, encoding="utf-8")
    report["steps"]["contract"] = {
        "ok": True,
        "tags_n_before": before_n,
        "tags_n_after": after_n,
        "added": list(NEW_TAGS),
        "size_usd": size_usd,
        "notional": notional,
        "csv": tb["selected_tags_csv"],
    }


def step_research_armed_overlay() -> None:
    dest_dir = REPO / "judgment" / "astra" / "lab" / "wires"
    dest_dir.mkdir(parents=True, exist_ok=True)
    WARROOM.mkdir(parents=True, exist_ok=True)
    for name in (
        "RESEARCH_ARMED_TAGS_OVERLAY_ADD_asian_fade_20260920.json",
        "RESEARCH_ARMED_TAGS_OVERLAY_ADD_sub_mid_dn_re_proxy_eurusd_short_m15_atr_20260920.json",
    ):
        src = WARROOM / name
        if src.exists():
            shutil.copy2(src, dest_dir / name)
    report["steps"]["research_armed_overlay"] = {"ok": True, "dest": str(dest_dir)}


def step_remint() -> None:
    tb = report["steps"]["contract"]
    tags = tb["csv"]
    size = tb["size_usd"]
    notional = tb.get("notional") or 100000
    py = VENV_PY if VENV_PY.exists() else (MSI_REPO / ".venv-gtos" / "Scripts" / "python.exe")
    if not py.exists():
        report["errors"].append("venv_python_missing")
        report["blocked"] = True
        report["block_reason"] = "no_venv_python_for_remint"
        return
    help_out = subprocess.run(
        [str(py), "scripts\\gtos_activation_token.py", "mint", "--help"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    report["steps"]["mint_help"] = {
        "rc": help_out.returncode,
        "stdout_tail": (help_out.stdout or "")[-1500],
        "stderr_tail": (help_out.stderr or "")[-800],
    }
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    bak_dir = TOKEN_DIR / f"bak_chair_apply_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    bak_dir.mkdir(parents=True, exist_ok=True)
    for p in TOKEN_DIR.glob("*.json"):
        if p.is_file():
            shutil.copy2(p, bak_dir / p.name)
    report["steps"]["token_backup"] = str(bak_dir)
    env = os.environ.copy()
    env["GTOS_ACTIVATION_TOKEN_DIR"] = str(TOKEN_DIR)
    cmd = [
        str(py),
        "scripts\\gtos_activation_token.py",
        "mint",
        "--profile",
        "operator_profile",
        "--namespace",
        "operator",
        "--f5-minimal-size-usd",
        str(int(size) if size is not None else 150),
        "--f5-notional-initial-usd",
        str(int(notional)),
        "--tags",
        tags,
        "--expires-in-hours",
        "720",
        "--issued-by",
        "chair",
        "--note",
        f"CHAIR_APPLY_20260920 PackageB+asian_fade tags_n={tb['tags_n_after']}",
        "--force",
    ]
    help_txt = (help_out.stdout or "") + (help_out.stderr or "")
    if "--risk-unit-floor-mode" in help_txt:
        cmd.extend(["--risk-unit-floor-mode", "shadow", "--risk-unit-floor", tags])
    if "--event-clock-shadow" in help_txt:
        cmd.append("--event-clock-shadow")
    proc = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, env=env)
    report["steps"]["remint"] = {
        "rc": proc.returncode,
        "cmd": cmd,
        "stdout": (proc.stdout or "")[-4000],
        "stderr": (proc.stderr or "")[-2000],
    }
    if proc.returncode != 0:
        report["blocked"] = True
        report["block_reason"] = f"remint_rc_{proc.returncode}"
        report["errors"].append((proc.stderr or proc.stdout or "remint_failed")[:1500])
        JUDGMENT_LIVE.mkdir(parents=True, exist_ok=True)
        (JUDGMENT_LIVE / "CHAIR_EURUSD_SHORT_B_APPLY_REMINT_20260920.json").write_text(
            json.dumps({"schema": "gtos.chair.remint_blocked.v1", "error": report["errors"][-1], "as_of_ict": AS_OF}, indent=2)
            + "\n",
            encoding="utf-8",
        )
        return
    digest = None
    token_meta = []
    for t in TOKEN_DIR.glob("*.json"):
        if "bak_" in t.name:
            continue
        try:
            tj = json.loads(t.read_text(encoding="utf-8"))
            token_meta.append(
                {
                    "path": str(t),
                    "namespace": tj.get("namespace"),
                    "config_digest_sha256": tj.get("config_digest_sha256"),
                    "expires_utc": tj.get("expires_utc"),
                }
            )
            if tj.get("config_digest_sha256"):
                digest = tj.get("config_digest_sha256")
        except Exception:
            pass
    report["steps"]["remint"]["digest"] = digest
    report["steps"]["remint"]["tokens"] = token_meta
    JUDGMENT_LIVE.mkdir(parents=True, exist_ok=True)
    remint_path = JUDGMENT_LIVE / "CHAIR_EURUSD_SHORT_B_APPLY_REMINT_20260920.json"
    remint_path.write_text(
        json.dumps(
            {
                "schema": "gtos.chair.remint.v1",
                "as_of_ict": AS_OF,
                "tags_n": tb["tags_n_after"],
                "tags_added": NEW_TAGS,
                "digest": digest,
                "size_usd": size,
                "namespace": "operator",
                "login": "0",
                "force": True,
                "backup": str(bak_dir),
                "stdout_tail": (proc.stdout or "")[-2000],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    report["steps"]["remint_receipt"] = str(remint_path)


def step_smoke() -> None:
    sys.path.insert(0, str(REPO))
    from src.components.ultimate_book.sleeves import registry as reg

    specs = reg.active_specs(tags=[TAG_B])
    specs_af = reg.active_specs(tags=[TAG_AF])
    import importlib.util

    spec = importlib.util.spec_from_file_location(TAG_B, MOD_B)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    report["steps"]["smoke"] = {
        "active_specs_B": len(specs),
        "active_specs_asian_fade": len(specs_af),
        "PLACE": mod.PLACE,
        "APPLY": mod.APPLY,
        "LIVE_ARMED": mod.LIVE_ARMED,
        "never_alias_ok": mod.NEVER_ALIAS_TO == NEVER and TAG_B != NEVER,
    }
    if len(specs) != 1:
        report["errors"].append(f"smoke_B_active_specs={len(specs)}")
    if len(specs_af) != 1:
        report["errors"].append(f"smoke_AF_active_specs={len(specs_af)}")


def step_recycle() -> None:
    ps_path = ADMIN_ROOT / "_chair_soft_recycle_f5_20260920.ps1"
    ps_path.write_text(
        "\n".join(
            [
                '$ErrorActionPreference = "Continue"',
                "$before = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -match 'run_book\\.py' -and $_.CommandLine -match 'operator' })",
                'Write-Output ("F5_BEFORE=" + $before.Count)',
                'foreach ($p in $before) { try { Stop-Process -Id $p.ProcessId -Force; Write-Output ("KILL " + $p.ProcessId) } catch {} }',
                "Start-Sleep -Seconds 3",
                "schtasks /End /TN '\\GTOS_F5_FTMO' 2>$null | Out-Null",
                "Start-Sleep -Seconds 2",
                "$proc = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-File','C:\\Users\\Administrator\\redacted_host\\f5_launch.ps1') -WindowStyle Hidden -PassThru",
                'Write-Output ("WRAPPER_PID=" + $proc.Id)',
                "Start-Sleep -Seconds 20",
                "$after = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -match 'run_book\\.py' -and $_.CommandLine -match 'operator' })",
                'Write-Output ("F5_AFTER=" + $after.Count)',
                'foreach ($p in $after) { Write-Output ("F5_PID=" + $p.ProcessId) }',
                "",
            ]
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ps_path),
        ],
        capture_output=True,
        text=True,
    )
    report["steps"]["recycle"] = {
        "rc": proc.returncode,
        "stdout": (proc.stdout or "")[-2000],
        "stderr": (proc.stderr or "")[-800],
    }


def step_msi_mirror() -> None:
    if not MSI_REPO.exists():
        report["steps"]["msi_mirror"] = {"skipped": True}
        return
    msi_sleeves = MSI_REPO / "src" / "components" / "ultimate_book" / "sleeves"
    if MOD_B.exists() and msi_sleeves.exists():
        shutil.copy2(MOD_B, msi_sleeves / MOD_B.name)
    report["steps"]["msi_mirror"] = {"ok": True}


def write_receipts() -> None:
    JUDGMENT_LIVE.mkdir(parents=True, exist_ok=True)
    WARROOM.mkdir(parents=True, exist_ok=True)
    tags_n = report.get("steps", {}).get("contract", {}).get("tags_n_after")
    digest = report.get("steps", {}).get("remint", {}).get("digest")
    body = {
        **report,
        "tag_b": TAG_B,
        "tag_asian_fade": TAG_AF,
        "remint_digest": digest,
        "contract_tags_n": tags_n,
        "pytest_import_smoke": report.get("steps", {}).get("smoke"),
        "place": "writer",
        "apply": True,
        "live_armed": True,
        "never_alias": NEVER,
    }
    for base in (
        JUDGMENT_LIVE / "CHAIR_EURUSD_SHORT_B_APPLY_ON_20260920",
        JUDGMENT_LIVE / "CHAIR_ASIAN_FADE_EURUSD_APPLY_ON_20260920",
        WARROOM / "CHAIR_EURUSD_SHORT_B_APPLY_ON_20260920",
        WARROOM / "CHAIR_ASIAN_FADE_EURUSD_APPLY_ON_20260920",
    ):
        base.with_suffix(".json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        status = "BLOCKED" if report.get("blocked") else "APPLY_ON"
        md = (
            f"# {base.name}\n\n"
            f"**as_of:** {AS_OF} ICT  \n"
            f"**status:** {status}  \n\n"
            f"| field | value |\n|---|---|\n"
            f"| tag_b | `{TAG_B}` |\n"
            f"| tag_asian_fade | `{TAG_AF}` |\n"
            f"| remint_digest | `{digest}` |\n"
            f"| contract tags_n | {tags_n} |\n"
            f"| place | writer |\n"
            f"| apply | true |\n"
            f"| live_armed | true |\n"
            f"| never_alias | `{NEVER}` |\n"
            f"| recycle | `{report.get('steps', {}).get('recycle', {})}` |\n"
            f"| smoke | `{report.get('steps', {}).get('smoke', {})}` |\n"
            f"| errors | `{report.get('errors')}` |\n"
        )
        base.with_suffix(".md").write_text(md, encoding="utf-8")


def main() -> int:
    step_module_b()
    step_registry()
    step_admission()
    step_contract_and_launch()
    step_research_armed_overlay()
    step_msi_mirror()
    if report["errors"] and any("missing" in e for e in report["errors"]):
        report["blocked"] = True
        write_receipts()
        print(json.dumps(report, indent=2))
        return 2
    step_remint()
    if not report.get("blocked"):
        try:
            step_smoke()
        except Exception as e:
            report["errors"].append(f"smoke_exc:{e}")
        step_recycle()
    write_receipts()
    print(json.dumps(report, indent=2))
    return 0 if not report.get("blocked") and not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

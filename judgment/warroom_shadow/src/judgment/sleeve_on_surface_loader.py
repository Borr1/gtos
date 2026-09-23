"""Parse ON_SURFACE/TAG/_DIRECTION from recovered sleeve modules without package import."""
from __future__ import annotations
import ast, re
from pathlib import Path
from typing import Any

_RECOVERED = Path("/workspace/gtos/research/codila_absorb/war_room/recovered")
_FABLE = Path("/workspace/gtos/redacted_host/parked/sleeves")
_WARROOM = Path("/workspace/gtos/research/warroom_20260920")
_VPS_SLEEVES = Path(r"C:host-local/redacted_host/repo/src/components/ultimate_book/sleeves")
_SWARM = Path("/workspace/gtos/_swarm_land_tip/extract/src/components/ultimate_book/sleeves")

def _paths_for(tag: str) -> list[Path]:
  return [
    _RECOVERED / f"{tag}.py",
    _WARROOM / f"{tag}.py",
    _FABLE / f"{tag}.py",
    _VPS_SLEEVES / f"{tag}.py",
    _SWARM / f"{tag}.py",
  ]

MODULES = {
  "dsp_expanding_up_staircase": _paths_for("dsp_expanding_up_staircase"),
  "dsp_three_fresh_lower_lows": _paths_for("dsp_three_fresh_lower_lows"),
  "dsp_spring_close_on_20low_through_the_box": _paths_for("dsp_spring_close_on_20low_through_the_box"),
  "sub_mid_dn_re_proxy_eurusd_short_m15_atr": _paths_for("sub_mid_dn_re_proxy_eurusd_short_m15_atr"),
  "asian_fade": _paths_for("asian_fade"),
  # blotter aliases
  "dsp_three_fresh": ["dsp_three_fresh_lower_lows"],
  "dsp_spring_close": ["dsp_spring_close_on_20low_through_the_box"],
  "sub_mid_dn_re_proxy": ["sub_mid_dn_re_proxy_eurusd_short_m15_atr"],
}

def _parse(path: Path) -> dict[str, Any]:
  src = path.read_text(encoding="utf-8")
  out = {"path": str(path), "status": "LOADED_FROM_RECOVERY", "ON_SURFACE": [], "TAG": None, "_DIRECTION": None, "DIRECTION": None, "apply": False}
  tree = ast.parse(src)
  for node in tree.body:
    if isinstance(node, ast.Assign):
      for t in node.targets:
        if isinstance(t, ast.Name) and t.id in ("ON_SURFACE", "TAG", "_DIRECTION", "DIRECTION"):
          try: out[t.id] = ast.literal_eval(node.value)
          except Exception: pass
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
      if node.target.id in ("ON_SURFACE", "TAG", "_DIRECTION", "DIRECTION") and node.value is not None:
        try: out[node.target.id] = ast.literal_eval(node.value)
        except Exception: pass
  if not out["ON_SURFACE"]:
    m = re.search(r"ON_SURFACE[^=]*=\s*(\([^)]+\))", src)
    if m: out["ON_SURFACE"] = list(ast.literal_eval(m.group(1)))
  if isinstance(out["ON_SURFACE"], tuple):
    out["ON_SURFACE"] = list(out["ON_SURFACE"])
  if out["_DIRECTION"] is None and out.get("DIRECTION") is not None:
    out["_DIRECTION"] = out["DIRECTION"]
  if out["_DIRECTION"] is None:
    m = re.search(r"_DIRECTION\s*=\s*(-?\d+)", src) or re.search(r"DIRECTION\s*=\s*(-?\d+)", src)
    if m: out["_DIRECTION"] = int(m.group(1))
  return out

def load_sleeve_module(tag_or_alias: str) -> dict[str, Any]:
  key = tag_or_alias
  paths = MODULES.get(key)
  if paths and paths and isinstance(paths[0], str):
    return load_sleeve_module(paths[0])
  # unknown tag: still try recovered path discovery
  candidates = list(paths) if paths else _paths_for(key)
  for p in candidates:
    if isinstance(p, str):
      continue
    if p.exists():
      return _parse(p)
  return {"path": None, "status": "MISSING_MODULE", "ON_SURFACE": [], "TAG": tag_or_alias, "_DIRECTION": None, "apply": False}

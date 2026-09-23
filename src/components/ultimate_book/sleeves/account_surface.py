"""Account symbols the FTMO Challenge profile can trade.

The running Challenge writer (--namespace operator) sees this surface.
Friend books keep the legacy four-name cut their process already imported.
"""
from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

ACCOUNT_SURFACE = (
    'AUDJPY',
    'BTCUSD',
    'CHFJPY',
    'ETHUSD',
    'EURJPY',
    'GBPJPY',
    'GER40',
    'JP225',
    'NAS100',
    'SPX500',
    'UK100',
    'UKOIL_cash',
    'US30_cash',
    'USDJPY',
    'USOIL_cash',
    'XAGUSD',
    'XAUUSD',
    'XAUEUR',
    'XAGEUR',
    'XAUAUD',
    'XAGAUD',
    'DASHUSD',
    'CORN_c',
    'COTTON_c',
    'EU50_cash',
    'FRA40_cash',
    'US2000_cash',
    'AUDUSD',
    'EURGBP',
    'EURUSD',
    'GBPUSD',
    'NZDUSD',
    'USDCAD',
    'USDCHF',
    'LTCUSD',
    'XPDUSD',
    'XPTUSD',
    'XRPUSD',
    'XTZUSD',
    'AVAUSD',
    'CADJPY',
    'NZDJPY',
)

LEGACY_FOUR = ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD")

FAMILIES = {
    "fx": [
        "AUDJPY",
        "CHFJPY",
        "EURJPY",
        "GBPJPY",
        "USDJPY",
        "AUDUSD",
        "EURGBP",
        "EURUSD",
        "GBPUSD",
        "NZDUSD",
        "USDCAD",
        "USDCHF",
        "CADJPY",
        "NZDJPY"
    ],
    "indices": [
        "GER40",
        "JP225",
        "NAS100",
        "SPX500",
        "UK100",
        "EU50_cash",
        "FRA40_cash",
        "US2000_cash",
        "US30_cash"
    ],
    "metals": [
        "XAGUSD",
        "XAUUSD",
        "XAUEUR",
        "XAGEUR",
        "XAUAUD",
        "XAGAUD",
        "XPDUSD",
        "XPTUSD"
    ],
    "energy": [
        "UKOIL_cash",
        "USOIL_cash"
    ],
    "agri": [
        "CORN_c",
        "COTTON_c"
    ],
    "crypto": [
        "BTCUSD",
        "ETHUSD",
        "DASHUSD",
        "LTCUSD",
        "XRPUSD",
        "XTZUSD",
        "AVAUSD"
    ]
}

STAMP = Path(r"host-local\gtos-agent-sessions\writer_surface_stamp.jsonl")
_SCHEDULED = False


def challenge_namespace() -> bool:
    argv = sys.argv
    for i, arg in enumerate(argv):
        if arg == "--namespace" and i + 1 < len(argv):
            return argv[i + 1] == "operator"
        if arg.startswith("--namespace="):
            return arg.split("=", 1)[1] == "operator"
    return False


def _is_run_book() -> bool:
    return any(str(arg).replace("\\", "/").endswith("run_book.py") for arg in sys.argv)


def on_surface_for_process(legacy=LEGACY_FOUR):
    surface = ACCOUNT_SURFACE if challenge_namespace() else tuple(legacy)
    if challenge_namespace() and _is_run_book():
        _schedule_proof(surface)
    return tuple(surface)


def _classify(symbols):
    out = {name: [] for name in FAMILIES}
    known = {sym: name for name, members in FAMILIES.items() for sym in members}
    for sym in symbols:
        name = known.get(sym)
        if name:
            out[name].append(sym)
    return out


def _append(row: dict) -> None:
    try:
        STAMP.parent.mkdir(parents=True, exist_ok=True)
        with STAMP.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    except OSError:
        return


def _tags_from_argv():
    argv = sys.argv
    for i, arg in enumerate(argv):
        if arg == "--tags" and i + 1 < len(argv):
            return [part.strip() for part in argv[i + 1].split(",") if part.strip()]
    return []


def _schedule_proof(surface) -> None:
    global _SCHEDULED
    if _SCHEDULED:
        return
    _SCHEDULED = True
    _append({
        "phase": "import",
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "namespace": "operator",
        "n_surface": len(surface),
        "symbols": list(surface),
        "families": _classify(list(surface)),
    })
    threading.Thread(target=_proof, args=(tuple(surface),), daemon=True).start()


def _proof(surface) -> None:
    import time
    time.sleep(2)
    row = {
        "phase": "active",
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "namespace": "operator",
    }
    try:
        import yaml
        from src.components.ultimate_book.admission import resolve_market_expansion_sleeves
        from src.components.ultimate_book.sleeves.registry import active_specs

        cfg = yaml.safe_load(Path(r"host-local\redacted_host\repo\config\agent_config.yaml").read_text(encoding="utf-8")) or {}

        def _find(obj, key):
            if isinstance(obj, dict):
                if key in obj:
                    return obj[key]
                for value in obj.values():
                    found = _find(value, key)
                    if found is not None:
                        return found
            return None

        include_candidate = bool(_find(cfg, "ultimate_book_include_candidate_book"))
        candidate = list(_find(cfg, "ultimate_book_candidate_book_sleeves") or [])
        include_mx = bool(_find(cfg, "ultimate_book_include_market_expansion_book"))
        policy = str(_find(cfg, "ultimate_book_market_expansion_policy") or "")
        explicit = list(_find(cfg, "ultimate_book_market_expansion_sleeves") or [])
        resolved, err = resolve_market_expansion_sleeves(policy=policy, explicit_sleeves=explicit)
        tags = _tags_from_argv()
        specs = active_specs(
            tags,
            include_candidate_book=include_candidate,
            candidate_book_sleeves=candidate,
            include_market_expansion_book=include_mx,
            market_expansion_sleeves=resolved or None,
        )
        symbols = sorted({sym for spec in specs for sym in (spec.on_surface or ())})
        account = set(surface)
        covered = [sym for sym in surface if sym in symbols]
        silent = [sym for sym in surface if sym not in symbols]
        row.update({
            "ok": True,
            "policy_error": err,
            "n_tags_argv": len(tags),
            "n_specs": len(specs),
            "spec_tags": [spec.tag for spec in specs],
            "symbols": symbols,
            "covered": covered,
            "silent": silent,
            "families": _classify(covered),
            "n_account": len(account),
            "n_covered": len(covered),
        })
    except Exception as exc:
        row.update({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
    _append(row)

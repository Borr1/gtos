"""Load the live import closure into the Challenge writer PID.

The module list is the import closure of ``run_book.py``, lazy imports
included. Each module is imported. The stamp records what loaded and what
failed. One stamp is written for the Challenge writer. An empty persist
stays empty. This module does not send an order.

redacted_account idle. Verification quarantined. Agents do not place friend tickets.
Canonical stamp is written only by Challenge ``run_book``
(``operator``). Side tests set ``GTOS_UNIQUE_LOADER_SIDE_TEST=1``.
"""

from __future__ import annotations

import ast
import importlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "gtos.judgment.unique_loader.v1"
CHALLENGE_LOGIN = "0"
CHALLENGE_NS = "operator"
SIDE_TEST_ENV = "GTOS_UNIQUE_LOADER_SIDE_TEST"

# Filled from the import closure. Not a hand menu.
UNIQUE_MODULES: tuple[str, ...] = ()

LOADED: list[str] = []
FAILED: dict[str, str] = {}
PERSIST: float | None = None
STAMP: dict[str, Any] = {}

_PKG = Path(__file__).resolve().parent
_REPO = _PKG.parents[1]
_STAMP_DIR = (
    _REPO
    / "pipeline_state"
    / "ultimate_book"
    / "operator"
    / "judgment"
)
_STAMP_PATH = _STAMP_DIR / "unique_loader_stamp.json"
_FIRE_PATH = _STAMP_DIR / "unique_fire_stamp.json"
_OBSERVE_PATH = _STAMP_DIR / "unique_observe_stamp.json"
_LAST_FIRE: dict[str, Any] = {}
_LAST_OBSERVE_KEY = ""
_LOAD_LOCK = False
_LOADED_ONCE = False
OCCUPANCY_SEAT = "occupancy"
# Names the occupancy Choice can return. The return is used. A miss stays unset.
OCCUPANCY_KEEP_ONE = frozenset(
    {
        "keep_one",
        "keep_one_occupied",
        "keep_one_occupied_integer",
    }
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _truthy(raw: str | None) -> bool:
    return str(raw or "").strip().lower() in {"1", "true", "yes", "on"}


def _is_challenge_writer() -> bool:
    if _truthy(os.environ.get(SIDE_TEST_ENV)):
        return False
    argv = " ".join(sys.argv).replace("\\", "/").lower()
    return "operator" in argv and "run_book" in argv


def _module_file(name: str) -> Path | None:
    parts = name.split(".")
    if not parts or any(not part.isidentifier() for part in parts):
        return None
    rel = Path(*parts)
    py = _REPO / rel.with_suffix(".py")
    init = _REPO / rel / "__init__.py"
    if py.is_file():
        return py
    if init.is_file():
        return init
    return None


def _package_of(path: Path) -> str | None:
    try:
        rel = path.resolve().relative_to(_REPO)
    except ValueError:
        return None
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    elif parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    else:
        return None
    if not parts:
        return None
    return ".".join(parts)


def _import_package(path: Path, module_name: str) -> str:
    if path.name == "__init__.py":
        return module_name
    parts = module_name.split(".")
    if len(parts) < 2:
        return ""
    return ".".join(parts[:-1])


def _resolve_relative(package: str, level: int, module: str | None) -> str | None:
    parts = package.split(".") if package else []
    drop = level - 1
    if drop < 0 or drop > len(parts):
        return None
    base = list(parts[: len(parts) - drop]) if drop else list(parts)
    if module:
        base.extend(module.split("."))
    if not base:
        return None
    return ".".join(base)


def _closure_from(entry: Path) -> list[str]:
    """Import closure of run_book.py. Function-body imports count. So do constant import_module strings."""

    class _Visitor(ast.NodeVisitor):
        def __init__(self, package: str) -> None:
            self.package = package
            self.found: list[str] = []

        def _add(self, name: str | None) -> None:
            if name:
                self.found.append(name)

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                self._add(alias.name)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.level:
                base = _resolve_relative(self.package, node.level, node.module)
            else:
                base = node.module
            self._add(base)
            if not base:
                return
            for alias in node.names:
                if alias.name == "*":
                    continue
                child = base + "." + alias.name
                if _module_file(child) is not None:
                    self._add(child)

        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            called = ""
            if isinstance(func, ast.Name):
                called = func.id
            elif isinstance(func, ast.Attribute):
                called = func.attr
            if called == "import_module" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    text = arg.value
                    if text and not text.startswith("."):
                        self._add(text)
            self.generic_visit(node)

    seen: set[str] = set()
    order: list[str] = []
    root_name = _package_of(entry)
    queue: list[str | None] = [root_name]
    while queue:
        current = queue.pop(0)
        if not current or current in seen:
            continue
        path = _module_file(current)
        if path is None:
            continue
        seen.add(current)
        order.append(current)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig", errors="replace"))
        except (OSError, SyntaxError):
            continue
        visitor = _Visitor(_import_package(path, current))
        visitor.visit(tree)
        for name in visitor.found:
            if name not in seen:
                queue.append(name)
    return order


def live_modules() -> tuple[str, ...]:
    """Dotted modules the live path can import, starting at run_book.py."""

    global UNIQUE_MODULES
    if UNIQUE_MODULES:
        return UNIQUE_MODULES
    entry = _REPO / "run_book.py"
    if not entry.is_file():
        return ()
    UNIQUE_MODULES = tuple(_closure_from(entry))
    return UNIQUE_MODULES


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _returned_persist() -> tuple[float | None, str | None]:
    """The persist Score already returned for this process. A miss stays empty.

    The pinned composite weight is not copied. An empty answer does not become 0.
    """

    try:
        priors = importlib.import_module("src.judgment.gold_priors")
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"
    reader = getattr(priors, "applied_persistence_weight", None)
    if not callable(reader):
        return None, None
    try:
        return _finite(reader()), None
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"


def _write_stamp(payload: dict[str, Any], *, canonical: bool) -> None:
    path_pid = _STAMP_DIR / f"unique_loader_stamp.{payload.get('pid')}.json"
    try:
        _STAMP_DIR.mkdir(parents=True, exist_ok=True)
        blob = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        path_pid.write_text(blob, encoding="utf-8")
        if canonical:
            _STAMP_PATH.write_text(blob, encoding="utf-8")
    except OSError:
        alt = _PKG / "unique_loader_stamp.json"
        try:
            alt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except OSError:
            return


def _write_fire(payload: dict[str, Any]) -> None:
    path_pid = _STAMP_DIR / f"unique_fire_stamp.{payload.get('pid')}.json"
    try:
        _STAMP_DIR.mkdir(parents=True, exist_ok=True)
        blob = json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n"
        path_pid.write_text(blob, encoding="utf-8")
        if _is_challenge_writer():
            _FIRE_PATH.write_text(blob, encoding="utf-8")
    except OSError:
        return


def _write_observe(payload: dict[str, Any]) -> None:
    """LABEL observe stamp. Never clobbers the send-choke unique_fire_stamp."""
    path_pid = _STAMP_DIR / f"unique_observe_stamp.{payload.get('pid')}.json"
    try:
        _STAMP_DIR.mkdir(parents=True, exist_ok=True)
        blob = json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n"
        path_pid.write_text(blob, encoding="utf-8")
        if _is_challenge_writer():
            _OBSERVE_PATH.write_text(blob, encoding="utf-8")
    except OSError:
        return


def _slim(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if hasattr(obj, "as_dict"):
        try:
            obj = obj.as_dict()
        except Exception:  # noqa: BLE001
            return {"type": type(obj).__name__}
    if not isinstance(obj, dict):
        return {"type": type(obj).__name__, "repr": str(obj)}
    keep = (
        "schema",
        "enabled",
        "skipped",
        "kind",
        "apply",
        "place",
        "flatten",
        "never_place",
        "persist_weight",
        "persist_ok",
        "persist_apply",
        "reason",
        "fail_closed",
        "proved",
        "disposition",
        "may_place",
        "may_send",
        "leave_orig",
        "occupancy_hold",
        "occupancy_hold_dead",
        "occupancy_after_close",
        "keep_one",
        "pack_ids",
        "blocks_send",
        "may_send",
        "two_stop_is_integer",
        "write",
        "n_keep",
        "n_kill",
        "n_label",
        "n_rows",
        "html_path",
        "md_path",
        "agent_order_send",
        "NEWS_PROTOCOL_APPLIED",
        "mill_url",
        "invented",
        "posted_ids",
        "n_posted",
        "seat",
        "seat_ids",
        "size_ids",
        "asked",
        "order_send",
        "n_decided",
        "historical_only",
        "decision_emitted",
    )
    return {k: obj.get(k) for k in keep if k in obj}


def _try_rung(name: str, call: Any) -> dict[str, Any]:
    try:
        got = call()
        slim = _slim(got)
        slim["ok"] = True
        slim["rung"] = name
        return slim
    except Exception as exc:  # noqa: BLE001 — stamp the exact block
        return {
            "ok": False,
            "rung": name,
            "block": f"{type(exc).__name__}: {exc}",
        }


def _occupancy_named(obj: Mapping[str, Any] | None) -> str:
    if not isinstance(obj, dict):
        return ""
    raw = obj.get("occupancy_after_close") or obj.get("disposition") or ""
    if isinstance(raw, dict):
        raw = raw.get("choice") or raw.get("id") or raw.get("label") or raw.get("answer") or ""
    return str(raw or "").strip().lower()


def _wake_positions() -> tuple[list[dict[str, Any]], bool]:
    """Positions on the chair wake. The second value is whether the wake was read."""

    path = _STAMP_DIR / "state" / "chair_wake.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return [], False
    book = data.get("book") if isinstance(data, dict) else None
    raw = book.get("positions") if isinstance(book, dict) else None
    if not isinstance(raw, list):
        return [], True
    found: list[dict[str, Any]] = []
    for pos in raw:
        if not isinstance(pos, dict):
            continue
        if pos.get("ticket") is None or not pos.get("symbol"):
            continue
        found.append(pos)
    return found, True


def _open_broker_positions() -> list[dict[str, Any]]:
    """Broker positions from the latest chair wake. No stand-in ticket."""

    positions, _read = _wake_positions()
    return positions


def _position_facts(positions: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    raw = _open_broker_positions() if positions is None else positions
    slim: list[dict[str, Any]] = []
    for pos in raw:
        slim.append(
            {
                "ticket": pos.get("ticket"),
                "symbol": pos.get("symbol"),
                "side": pos.get("side"),
                "lots": pos.get("lots"),
                "live_sl": pos.get("live_sl"),
                "tp": pos.get("tp") if pos.get("tp") is not None else pos.get("live_tp"),
                "sleeve": pos.get("sleeve") or pos.get("comment"),
            }
        )
    return slim


def _gold_rows(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pos in positions:
        symbol = str(pos.get("symbol") or "")
        upper = symbol.upper()
        if "XAU" not in upper and "GOLD" not in upper:
            continue
        rows.append(
            {
                "ticket": pos.get("ticket"),
                "symbol": symbol,
                "side": pos.get("side"),
            }
        )
    return rows


def _gold_ticket_occupied() -> bool | None:
    """Whether the wake shows a gold position. Unread wake stays unset."""

    positions, read = _wake_positions()
    if not read:
        return None
    return bool(_gold_rows(positions))


def _occupancy_state(
    *,
    login: Any = None,
    namespace: Any = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ident_login = login or CHALLENGE_LOGIN
    ident_ns = namespace or CHALLENGE_NS
    state: dict[str, Any] = {
        "identity": {"login": ident_login, "ns": ident_ns},
        "account": ident_login,
        "namespace": ident_ns,
        "login": ident_login,
        "open_positions": _position_facts(),
    }
    if extra:
        state.update(extra)
    return state


def _observe_seats() -> list[str]:
    """BRANCH_SEATS observe plus occupancy. Occupancy is not opt-in."""
    seats = ["companion", "weekend", "overlay", "frontier", "research", OCCUPANCY_SEAT]
    try:
        tree = importlib.import_module("src.judgment.remaining_ifs_tree")
        raw = (getattr(tree, "BRANCH_SEATS", {}) or {}).get("observe") or ()
        seats = [str(item) for item in raw]
    except Exception:
        pass
    if OCCUPANCY_SEAT not in seats:
        seats.append(OCCUPANCY_SEAT)
    return seats


def _keep_bit(choice: Any) -> bool | None:
    """True when the returned choice is a keep. Empty stays unset."""

    if choice is None:
        return None
    text = str(choice).strip().lower()
    if not text:
        return None
    if text in OCCUPANCY_KEEP_ONE:
        return True
    return False


def compose_occupancy_hop(state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Ask the occupancy pack. The Choice is that return. This hop does not send."""

    row: dict[str, Any] = {
        "seat": OCCUPANCY_SEAT,
        "asked": False,
        "ok": False,
        "occupancy_hold_dead": None,
        "choice": None,
        "keep_one": None,
    }
    st = dict(state or _occupancy_state())
    st["open_gold"] = _open_gold_fact()
    try:
        rem = importlib.import_module("src.judgment.remaining_ifs")
        occ = rem.compose_occupancy(st)
        d = occ.as_dict() if hasattr(occ, "as_dict") else (occ if isinstance(occ, dict) else {})
        named = _occupancy_named(d)
        row["asked"] = True
        row["ok"] = True
        row["disposition"] = d.get("disposition")
        row["choice"] = d.get("choice") or named or d.get("disposition")
        row["probabilities"] = d.get("probabilities")
        row["unique_highest"] = d.get("unique_highest")
        row["reason"] = d.get("reason")
        row["occupancy_after_close"] = named
        row["persist_apply"] = d.get("persist_apply")
        hold = d.get("occupancy_hold_dead")
        row["occupancy_hold_dead"] = hold if isinstance(hold, bool) else None
    except Exception as exc:  # noqa: BLE001
        row["block"] = f"{type(exc).__name__}: {exc}"
        row["choice"] = None
    pack_ids: list[str] = []
    try:
        tree = importlib.import_module("src.judgment.remaining_ifs_tree")
        pack_ids = [str(x) for x in (tree.occupancy_pack_ids(st) or ())]
    except Exception:
        pack_ids = []
    row["pack_ids"] = pack_ids
    row["n_posted"] = len(pack_ids) if pack_ids else None
    row["keep_one"] = _keep_bit(row.get("choice"))
    row["gold_ticket_occupied"] = _gold_ticket_occupied()
    return row


def _stamp_body(names: tuple[str, ...] | list[str], persist: float | None, persist_block: str | None) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "loaded_at_utc": _now(),
        "pid": os.getpid(),
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "persist": persist,
        "persist_block": persist_block,
        "loaded": list(LOADED),
        "failed": dict(FAILED),
        "n_loaded": len(LOADED),
        "n_failed": len(FAILED),
        "never_book_owner": True,
        "fn_idle": True,
        "verification_quarantined": True,
        "challenge_writer": _is_challenge_writer(),
        "n_declared": len(names),
        "choice_hops": list(LOADED),
    }


def load_unique_apply() -> dict[str, Any]:
    """Import the live closure into this process and write one stamp.

    Never raises into package init. Does not re-enter run_book. An empty
    persist stays empty. Friends and side tests do not write the canonical stamp.
    """

    global PERSIST, STAMP, _LOAD_LOCK, _LOADED_ONCE
    if _LOADED_ONCE and STAMP:
        return STAMP
    if _LOAD_LOCK:
        return STAMP
    _LOAD_LOCK = True
    try:
        names = live_modules()
        LOADED.clear()
        FAILED.clear()
        writer = _is_challenge_writer()
        STAMP = _stamp_body(names, None, None)
        if writer:
            _write_stamp(STAMP, canonical=True)
        for name in names:
            if name == "run_book" or name in sys.modules or name == __name__:
                if name == "run_book":
                    main_mod = sys.modules.get("__main__")
                    main_file = str(getattr(main_mod, "__file__", "") or "").replace("\\", "/")
                    if name in sys.modules or main_file.endswith("run_book.py"):
                        LOADED.append(name)
                    else:
                        FAILED[name] = "entry_script"
                else:
                    LOADED.append(name)
                continue
            try:
                importlib.import_module(name)
                LOADED.append(name)
            except Exception as exc:  # noqa: BLE001 — stamp the exact block
                FAILED[name] = f"{type(exc).__name__}: {exc}"
        persist, persist_block = _returned_persist()
        PERSIST = persist
        STAMP = _stamp_body(names, persist, persist_block)
        if writer:
            try:
                fear = importlib.import_module("src.components.ultimate_book.minimal_size")
                boot = getattr(fear, "_fear_boot_stamp", None)
                if callable(boot):
                    boot()
            except Exception:
                pass
            _write_stamp(STAMP, canonical=True)
        _LOADED_ONCE = True
        return STAMP
    finally:
        _LOAD_LOCK = False


def _open_gold_fact() -> dict[str, Any]:
    """Gold positions on the wake. No stand-in ticket."""

    positions, read = _wake_positions()
    metals = _gold_rows(positions)
    return {
        "positions": metals,
        "occupied": bool(metals) if read else None,
    }


def _account_facts() -> dict[str, Any]:
    """Equity, to_pass, floor_room, closed profit. Facts for the place Choice."""
    out: dict[str, Any] = {
        "equity": None,
        "to_pass": None,
        "floor_room": None,
        "closed_profit": None,
    }
    try:
        eq = importlib.import_module("src.judgment.equity_frame")
        state = eq.attach_account({"identity": {"login": CHALLENGE_LOGIN, "ns": CHALLENGE_NS}})
    except Exception:
        state = {}
    blobs = []
    if isinstance(state, dict):
        blobs.append(state)
        for key in ("account", "equity_frame", "card"):
            if isinstance(state.get(key), dict):
                blobs.append(state[key])
    for blob in blobs:
        for key in ("equity", "to_pass", "floor_room", "closed_profit"):
            if out.get(key) is None and blob.get(key) is not None:
                out[key] = blob.get(key)
    return out


def _sibling(module: str, fn: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    try:
        mod = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001
        return {"present": False, "block": type(exc).__name__}
    call = getattr(mod, fn, None)
    if not callable(call):
        return {"present": False}
    try:
        got = call(**kwargs)
        slim = _slim(got)
        slim["ok"] = True
        slim["present"] = True
        return slim
    except Exception as exc:  # noqa: BLE001
        return {"present": True, "ok": False, "block": f"{type(exc).__name__}: {exc}"}


def _hop_reason(raw: Any) -> Any:
    return raw


def _observe_key(namespace: str) -> str:
    """Structural facts for this observe. A quote flicker is not a new state."""

    facts = {
        "namespace": namespace,
        "positions": _position_facts(),
    }
    return json.dumps(facts, sort_keys=True, default=str)


def observe_unique_apply(*, namespace: Any = None, origin: str | None = None) -> dict[str, Any]:
    """Challenge observe. Same structural state returns the ask already made.

    A friend namespace is not this book. This function does not send.
    """

    global _LAST_FIRE, _LAST_OBSERVE_KEY

    ns = str(namespace or "").strip()
    row: dict[str, Any] = {
        "schema": "gtos.judgment.unique_observe.v1",
        "action": None,
        "origin": origin or "observe_unique_apply",
        "namespace": ns,
        "persist": PERSIST,
        "broker_effect": False,
        "leave_orig": None,
        "n_loaded": len(LOADED),
        "n_failed": len(FAILED),
        "pid": os.getpid(),
        "observed_at_utc": _now(),
    }
    if ns and ns != CHALLENGE_NS:
        row["reason"] = "not_challenge"
        return row
    if not ns:
        ns = CHALLENGE_NS
        row["namespace"] = ns
    state_key = _observe_key(ns)
    if _LAST_FIRE and state_key == _LAST_OBSERVE_KEY:
        return dict(_LAST_FIRE)

    try:
        fc = importlib.import_module("src.judgment.friend_copy")
        row["friend_copy"] = {
            "schema": getattr(fc, "SCHEMA", None),
            "agent_order_send": False,
            "fn_idle": True,
        }
    except Exception as exc:  # noqa: BLE001
        row["friend_copy_block"] = f"{type(exc).__name__}: {exc}"

    try:
        tape = importlib.import_module("src.judgment.news_tape_join")
        status = tape.tape_join_status()
        applied = getattr(tape, "NEWS_PROTOCOL_APPLIED", None)
        invented = status.get("invented") if isinstance(status, dict) else None
        row["news"] = {
            "NEWS_PROTOCOL_APPLIED": applied if isinstance(applied, bool) else None,
            "mill_url": getattr(tape, "MILL_URL", None),
            "invented": invented if isinstance(invented, bool) else None,
        }
    except Exception as exc:  # noqa: BLE001
        row["news"] = {
            "block": f"{type(exc).__name__}: {exc}",
        }

    seats = _observe_seats()
    row["observe_seats"] = seats
    challenge_state = {
        "identity": {"login": CHALLENGE_LOGIN, "ns": CHALLENGE_NS},
        "account": CHALLENGE_LOGIN,
        "namespace": CHALLENGE_NS,
        "login": CHALLENGE_LOGIN,
        "open_gold": _open_gold_fact(),
        "account_facts": _account_facts(),
    }
    rungs: dict[str, Any] = {}
    rungs["isolated_15m"] = _try_rung(
        "isolated_15m",
        lambda: importlib.import_module("src.judgment.isolated_15m_reentry").maybe_prove_isolated_15m(),
    )
    rungs["daily_loop"] = _try_rung(
        "daily_loop",
        lambda: importlib.import_module("src.judgment.challenge_daily_loop").maybe_run_daily_loop(
            login=CHALLENGE_LOGIN,
            namespace=CHALLENGE_NS,
        ),
    )
    rungs["command_center"] = _try_rung(
        "command_center",
        lambda: importlib.import_module("src.judgment.challenge_command_center").maybe_run_command_center(
            login=CHALLENGE_LOGIN,
            namespace=CHALLENGE_NS,
        ),
    )
    rungs["hist_apply"] = _try_rung(
        "hist_apply",
        lambda: importlib.import_module("src.judgment.hist_apply_candidate").maybe_label(
            login=CHALLENGE_LOGIN,
            namespace=CHALLENGE_NS,
        ),
    )
    rungs["remaining_ifs"] = _try_rung(
        "remaining_ifs",
        lambda: importlib.import_module("src.judgment.remaining_ifs").compose_remaining_ifs(
            challenge_state,
            None,
            seat="companion",
            branch="observe",
            seats=tuple(seats),
        ),
    )
    occ_obs = compose_occupancy_hop(challenge_state)
    occ_obs["rung"] = "occupancy"
    rungs["occupancy"] = occ_obs
    rungs["friend_feedback"] = _try_rung(
        "friend_feedback",
        lambda: importlib.import_module("src.judgment.friend_feedback_loop").maybe_run_friend_feedback(
            login=CHALLENGE_LOGIN,
            namespace=CHALLENGE_NS,
        ),
    )
    sib_state = dict(challenge_state)
    subject = _position_facts()
    lead = subject[0] if subject else {}
    rungs["sleeve_select"] = _sibling(
        "src.judgment.sleeve_select",
        "decide_sleeve_select_live",
        {"symbol": lead.get("symbol"), "state": sib_state},
    )
    rungs["gold_sleeve"] = _sibling(
        "src.judgment.gold_sleeve_ifs",
        "decide_gold_sleeve_live",
        {
            "sleeve": lead.get("sleeve"),
            "symbol": lead.get("symbol"),
            "side": lead.get("side"),
            "state": sib_state,
        },
    )
    try:
        manage = importlib.import_module("src.judgment.manage_choices")
        positions = _open_broker_positions()
        asked: list[dict[str, Any]] = []
        for pos in positions:
            acts: dict[str, Any] = {}
            for act in ("move_sl", "move_tp", "close"):
                facts = {
                    "ticket": pos.get("ticket"),
                    "symbol": pos.get("symbol"),
                    "side": pos.get("side"),
                    "lots": pos.get("lots"),
                    "live_sl": pos.get("live_sl"),
                    "entry": pos.get("entry") or pos.get("price_open"),
                    "bid": pos.get("bid"),
                    "ask": pos.get("ask"),
                    "tp": pos.get("tp") or pos.get("live_tp"),
                }
                got = manage.decide(
                    act,
                    ticket=pos.get("ticket"),
                    symbol=pos.get("symbol"),
                    reason="open_position_heartbeat",
                    facts=facts,
                )
                if (
                    act == "move_sl"
                    and isinstance(got, dict)
                    and got.get("send")
                    and got.get("choice") == "move_sl"
                ):
                    got = manage.send_unique_move_sl(got, facts=facts)
                send_bit = got.get("send") if isinstance(got, dict) else None
                emitted = got.get("decision_emitted") if isinstance(got, dict) else None
                agent_bit = got.get("agent_order_send") if isinstance(got, dict) else None
                acts[act] = {
                    "choice": got.get("choice") if isinstance(got, dict) else None,
                    "probability": got.get("probability") if isinstance(got, dict) else None,
                    "send": send_bit if isinstance(send_bit, bool) else None,
                    "decision_emitted": emitted if isinstance(emitted, bool) else None,
                    "agent_order_send": agent_bit if isinstance(agent_bit, bool) else None,
                }
            asked.append({"ticket": pos.get("ticket"), "symbol": pos.get("symbol"), "acts": acts})
        only = asked[0] if len(asked) == 1 else None
        sl_sent = None
        for item in asked:
            bit = ((item.get("acts") or {}).get("move_sl") or {}).get("agent_order_send")
            if bit is True:
                sl_sent = True
            elif sl_sent is None and bit is False:
                sl_sent = False
        row["manage"] = {
            "ok": True,
            "order_send": sl_sent,
            "ticket": None if only is None else only["ticket"],
            "acts": {} if only is None else only["acts"],
            "positions": asked,
        }
    except Exception as exc:  # noqa: BLE001
        row["manage"] = {"ok": False, "block": f"{type(exc).__name__}: {exc}", "order_send": None}
    rungs["exec_gov_news"] = _sibling(
        "src.judgment.exec_gov_news",
        "maybe_run_news_skip",
        {"state": sib_state},
    )
    rungs["state_choices"] = _sibling(
        "src.judgment.state_choices",
        "maybe_ask_surface",
        {"namespace": CHALLENGE_NS},
    )
    rungs["learning_choices"] = _sibling(
        "src.judgment.learning_choices",
        "maybe_ask_learning",
        {"namespace": CHALLENGE_NS},
    )
    row["rungs"] = rungs
    row["rung_ok"] = {
        key: (True if value.get("ok") is True else False if value.get("ok") is False else None)
        for key, value in rungs.items()
        if isinstance(value, dict)
    }
    occupancy = rungs.get("occupancy") if isinstance(rungs.get("occupancy"), dict) else {}
    row["reason"] = occupancy.get("choice")
    row["leave_orig"] = occupancy.get("leave_orig") if isinstance(occupancy.get("leave_orig"), bool) else None
    row["broker_effect"] = False
    row["learn_loop_env"] = _truthy(os.environ.get("GTOS_JEV_LEARN_LOOP"))
    row["trained_models_env"] = _truthy(os.environ.get("GTOS_JEV_TRAINED_MODELS"))
    row["x_dig_env"] = _truthy(os.environ.get("GTOS_JEV_X_DIG"))
    _LAST_FIRE = dict(row)
    _LAST_OBSERVE_KEY = state_key
    _write_observe(row)
    return row


def _intent_details(intent: Any) -> dict[str, Any]:
    det = getattr(intent, "details", None) if intent is not None else None
    if isinstance(det, dict):
        return det
    return {}


def _choice_of(obj: Any) -> Any:
    if not isinstance(obj, dict):
        return None
    for key in ("choice", "action", "admit", "disposition"):
        val = obj.get(key)
        if val:
            return val
    return None


def gate_order_send(
    *,
    intent: Any = None,
    login: Any = None,
    namespace: Any = None,
    tick: Any = None,
    unit: Any = None,
    extra_state: dict[str, Any] | None = None,
    origin: str | None = None,
) -> dict[str, Any]:
    """Ask place, admit, size, followthrough, and occupancy.

    The place decision is the unique highest place Choice.
    Admission, size, followthrough, and occupancy are recorded.
    This function does not send.
    """

    ns = str(namespace or "").strip()
    row: dict[str, Any] = {
        "schema": "gtos.judgment.unique_gate.v1",
        "origin": origin or "gate_order_send",
        "namespace": ns or CHALLENGE_NS,
        "persist": PERSIST,
        "broker_effect": False,
        "n_loaded": len(LOADED),
        "n_failed": len(FAILED),
        "pid": os.getpid(),
        "gated_at_utc": _now(),
        "observed_at_utc": _now(),
    }
    if ns and ns != CHALLENGE_NS:
        row["action"] = None
        row["choice"] = None
        row["reason"] = "not_challenge"
        return row

    details = _intent_details(intent)
    hops: dict[str, Any] = {}
    asked: dict[str, bool] = {}
    gold = _open_gold_fact()
    place_extra = dict(extra_state or {})
    place_extra["open_gold"] = gold
    place_extra["account_facts"] = _account_facts()

    place = details.get("jev_place_receipt") if isinstance(details.get("jev_place_receipt"), dict) else None
    if place is None:
        try:
            pc = importlib.import_module("src.judgment.place_choice")
            place = pc.evaluate_place_choice(
                intent,
                login=login or CHALLENGE_LOGIN,
                namespace=ns or CHALLENGE_NS,
                extra_state=place_extra,
                observe=False,
            )
            asked["place"] = True
        except Exception as exc:  # noqa: BLE001
            place = {
                "action": None,
                "choice": None,
                "source": "place_hop_exception",
                "error": type(exc).__name__,
                "seat": "gate",
            }
            asked["place"] = False
    else:
        asked["place"] = True
    if not isinstance(place, dict):
        place = {}
    choice = place.get("action")
    if isinstance(choice, str):
        choice = choice.strip().upper() or None
    hops["place"] = {
        "action": choice,
        "choice": choice,
        "probabilities": place.get("probabilities"),
        "unique_highest": place.get("unique_highest") if isinstance(place.get("unique_highest"), bool) else None,
        "probability": place.get("probability"),
        "source": place.get("source"),
        "error": place.get("error"),
        "posted_ids": place.get("posted_ids"),
        "n_posted": place.get("n_posted"),
        "seat": place.get("seat") or "gate",
        "model": place.get("model") or "jev-1.13.0",
        "asked": True if asked.get("place") is True else False if asked.get("place") is False else None,
    }

    admit = details.get("jev_admission_receipt") if isinstance(details.get("jev_admission_receipt"), dict) else None
    if admit is None:
        try:
            ap = importlib.import_module("src.judgment.admission_place")
            decision = ap.decide_admission_place(
                intent=intent,
                tick=tick,
                unit=unit,
                login=login or CHALLENGE_LOGIN,
                ns=ns or CHALLENGE_NS,
            )
            admit = decision.as_dict() if hasattr(decision, "as_dict") else {}
            asked["admission"] = True
        except Exception as exc:  # noqa: BLE001
            admit = {
                "admit": None,
                "reason": "admission_hop_exception",
                "disposition": None,
                "error": type(exc).__name__,
            }
            asked["admission"] = False
    else:
        asked["admission"] = True
    if not isinstance(admit, dict):
        admit = {}
    admit_choice = admit.get("admit") or admit.get("disposition")
    hops["admission"] = {
        "admit": admit_choice,
        "choice": admit.get("choice") or admit_choice,
        "probabilities": admit.get("probabilities"),
        "unique_highest": admit.get("unique_highest"),
        "probability": admit.get("probability"),
        "disposition": admit.get("disposition"),
        "reason": admit.get("reason"),
        "error": admit.get("error"),
        "seat": "admission",
        "seat_ids": admit.get("seat_ids"),
        "asked": bool(asked.get("admission")),
    }

    size_state = dict(place_extra)
    size_state.setdefault("identity", {"login": login or CHALLENGE_LOGIN, "ns": ns or CHALLENGE_NS})
    size_d: dict[str, Any] = {}
    try:
        se = importlib.import_module("src.judgment.size_exit")
        try:
            sized = se.decide_size_exit(state=size_state, evaluate_jev=True)
        except TypeError:
            sized = se.decide_size_exit(state=size_state)
        size_d = sized.as_dict() if hasattr(sized, "as_dict") else (sized if isinstance(sized, dict) else {})
        asked["size"] = True
    except Exception as exc:  # noqa: BLE001
        size_d = {"action": None, "error": type(exc).__name__, "source": "size_hop_exception"}
        asked["size"] = False
    size_choice = size_d.get("choice") or size_d.get("action")
    if not asked.get("size"):
        size_d["account_facts"] = place_extra.get("account_facts") or _account_facts()
    hops["size"] = {
        "action": size_choice,
        "choice": size_choice,
        "probabilities": size_d.get("probabilities"),
        "unique_highest": size_d.get("unique_highest"),
        "probability": size_d.get("probability"),
        "seat": "size",
        "size_ids": size_d.get("size_ids"),
        "n_posted": len(size_d.get("size_ids") or []) or size_d.get("n_posted"),
        "asked": bool(asked.get("size")),
        "source": size_d.get("source"),
        "account_facts": size_d.get("account_facts"),
    }

    leftover_row: dict[str, Any] = {}
    try:
        ft = importlib.import_module("src.judgment.followthrough")
        state = {
            "identity": {"login": login or CHALLENGE_LOGIN, "ns": ns or CHALLENGE_NS},
            "account": login or CHALLENGE_LOGIN,
            "namespace": ns or CHALLENGE_NS,
            "open_gold": gold,
            "account_facts": place_extra.get("account_facts"),
        }
        try:
            got = ft.compose_from_intent(state, None, branch="leftover", evaluate_jev=True)
        except TypeError:
            got = ft.compose_from_intent(state, branch="leftover", evaluate_jev=True)
        leftover_row = got if isinstance(got, dict) else {}
        asked["leftover"] = True
    except Exception as exc:  # noqa: BLE001
        leftover_row = {"decision": {"disposition": None, "error": type(exc).__name__}}
        asked["leftover"] = False
    decision = leftover_row.get("decision") if isinstance(leftover_row.get("decision"), dict) else {}
    left_choice = _choice_of(decision) or _choice_of(leftover_row)
    pack_keys = leftover_row.get("pack_payload_keys") if isinstance(leftover_row, dict) else None
    hops["leftover"] = {
        "choice": left_choice,
        "disposition": decision.get("disposition"),
        "leave_orig": decision.get("leave_orig"),
        "reason": decision.get("reason"),
        "seat": "leftover",
        "n_posted": len(pack_keys) if isinstance(pack_keys, list) else None,
        "asked": bool(asked.get("leftover")),
    }

    occ = compose_occupancy_hop(
        _occupancy_state(login=login or CHALLENGE_LOGIN, namespace=ns or CHALLENGE_NS)
    )
    asked["occupancy"] = bool(occ.get("asked"))
    hops["occupancy"] = {
        "seat": OCCUPANCY_SEAT,
        "choice": occ.get("choice"),
        "disposition": occ.get("disposition"),
        "reason": occ.get("reason"),
        "occupancy_after_close": occ.get("occupancy_after_close"),
        "keep_one": occ.get("keep_one"),
        "gold_ticket_occupied": occ.get("gold_ticket_occupied"),
        "pack_ids": occ.get("pack_ids"),
        "n_posted": occ.get("n_posted"),
        "occupancy_hold_dead": occ.get("occupancy_hold_dead") if isinstance(occ.get("occupancy_hold_dead"), bool) else None,
        "asked": True if occ.get("asked") is True else False if occ.get("asked") is False else None,
    }

    row["hops"] = hops
    row["asked"] = asked
    row["action"] = choice
    row["choice"] = choice
    place_unique = hops["place"].get("unique_highest")
    row["unique_highest"] = place_unique if isinstance(place_unique, bool) else None
    row["probability"] = hops["place"].get("probability")
    row["probabilities"] = hops["place"].get("probabilities")
    row["model"] = "jev-1.13.0"
    row["reason"] = choice
    row["broker_effect"] = False
    row["observe_seats"] = _observe_seats()

    try:
        det = getattr(intent, "details", None)
        if isinstance(det, dict):
            det["jev_send_gate"] = {
                "action": choice,
                "choice": choice,
                "unique_highest": row.get("unique_highest"),
                "model": "jev-1.13.0",
            }
    except Exception:
        pass

    fire = dict(row)
    fire["schema"] = "gtos.judgment.unique_fire.v1"
    _write_fire(fire)
    return row


def _boot_writer_load() -> None:
    """Challenge run_book writes one loader stamp. Other processes do not."""

    if not _is_challenge_writer():
        return
    try:
        load_unique_apply()
    except Exception:
        return


_boot_writer_load()

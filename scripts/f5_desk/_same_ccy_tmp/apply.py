"""Disk-wire same-currency dsp stack + call f5_standing_hold_reason from the writer."""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"host-local\redacted_host\repo")
STAMP = "pre_same_ccy_20260827"

NEW_HOLD = r'''
def f5_norm_direction(direction: object) -> str | None:
    """LONG / SHORT or None. Intent uses +1/-1. Broker type 0 is buy."""
    if direction is None:
        return None
    if isinstance(direction, str):
        u = direction.strip().upper()
        if u in {"LONG", "BUY"}:
            return "LONG"
        if u in {"SHORT", "SELL"}:
            return "SHORT"
        return None
    try:
        i = int(direction)
    except (TypeError, ValueError):
        return None
    if i > 0:
        return "LONG"
    if i < 0:
        return "SHORT"
    return None


def f5_is_dsp_family(family: object) -> bool:
    text = str(family or "").lower()
    return "dsp_" in text or text.startswith("dsp")


def f5_is_eur_gbp_fx(symbol: object) -> bool:
    """Cash FX pair with an EUR or GBP leg. Not metals, not indices."""
    sym = f5_norm_symbol(symbol)
    if not sym:
        return False
    if any(tag in sym for tag in ("XAU", "XAG", "US30", "US500", "NAS", "GER40", "UK100", "JPN", "WS30", "SPX")):
        return False
    letters = "".join(c for c in sym if c.isalpha())
    if len(letters) < 6:
        return False
    a, b = letters[:3], letters[3:6]
    return a in {"EUR", "GBP"} or b in {"EUR", "GBP"}


def f5_standing_hold_reason(
    namespace: str,
    symbol: str,
    occupied_symbols: Iterable[str] = (),
    direction: object = None,
    family: object = None,
    occupied_book: Iterable[Mapping[str, Any]] = (),
) -> str | None:
    """Why a new intent must not place. None = not a standing hold.

    USDJPY is held for the rest of verification. Any other symbol already
    occupied by a live F5 ticket or pending is held so a second ticket
    cannot fail-open between sits. Isolated re-entry on a *flat* symbol
    is not a hold.

    EUR+GBP same-direction dsp is one bet. Isolated EUR vs GBP opposite
    is not a stack. Occupied-symbol HOLD does not cover that by itself.
    """
    if str(namespace or "") != F5_NAMESPACE:
        return None
    sym = f5_norm_symbol(symbol)
    if not sym:
        return None
    for standing in F5_STANDING_HOLD_SYMBOLS:
        if sym == standing or sym.startswith(standing):
            return "usdjpy_verification_hold_5pip_dsp_stop"
    occupied = {f5_norm_symbol(s) for s in occupied_symbols if f5_norm_symbol(s)}
    if sym in occupied:
        return "same_symbol_stack_keep_working_ticket"
    d = f5_norm_direction(direction)
    if d and f5_is_dsp_family(family) and f5_is_eur_gbp_fx(sym):
        for row in occupied_book or ():
            if not isinstance(row, Mapping):
                continue
            o_sym = f5_norm_symbol(row.get("symbol"))
            o_dir = f5_norm_direction(row.get("direction") or row.get("side"))
            o_fam = row.get("family") or row.get("sleeve") or row.get("comment")
            if not o_sym or o_sym == sym:
                continue
            if not f5_is_eur_gbp_fx(o_sym) or not f5_is_dsp_family(o_fam):
                continue
            if o_dir == d:
                return "same_currency_dsp_stack_one_bet"
    return None
'''

NEW_BOOK_HOLD = r'''
    def _f5_occupied_book(self) -> list:
        """Live F5 tickets and pendings the standing hold can see. Empty on a failed read."""
        rows: list = []
        seen: set = set()
        try:
            positions = self._open_book_positions_snapshot() or []
        except Exception:
            positions = []
        for p in positions:
            ticket = getattr(p, "ticket", None)
            key = ("pos", ticket)
            if key in seen:
                continue
            seen.add(key)
            try:
                typ = int(getattr(p, "type", 1) or 0)
            except (TypeError, ValueError):
                typ = 1
            rows.append({
                "symbol": getattr(p, "symbol", "") or "",
                "direction": "LONG" if typ == 0 else "SHORT",
                "family": getattr(p, "comment", "") or "",
            })
        module = getattr(self._mt5, "_mt5", None)
        orders_get = getattr(module, "orders_get", None)
        if callable(orders_get):
            try:
                orders = orders_get() or []
            except Exception:
                orders = []
            for o in orders:
                if getattr(self, "_magic", None) is not None and getattr(o, "magic", None) != self._magic:
                    continue
                ticket = getattr(o, "ticket", None)
                key = ("ord", ticket)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    typ = int(getattr(o, "type", 99) or 99)
                except (TypeError, ValueError):
                    typ = 99
                if typ in (0, 2, 4, 6):
                    direction = "LONG"
                elif typ in (1, 3, 5, 7):
                    direction = "SHORT"
                else:
                    direction = None
                rows.append({
                    "symbol": getattr(o, "symbol", "") or "",
                    "direction": direction,
                    "family": getattr(o, "comment", "") or "",
                })
        return rows

    def _f5_standing_symbol_hold(self, intent, unit=None, candidate_id=None):
        """F5-only standing law: writer refuses. Other books untouched.

        USDJPY rest of verification. Same-symbol while a ticket or pending
        is live. EUR+GBP same-direction dsp is one bet. Isolated opposite
        is PASS. Isolated re-entry after that symbol is flat is not a hold.
        """
        absent = {"action": "PASS", "reason": "not_standing_symbol_hold", "verdict": None}
        if str(getattr(self, "_namespace", "")) != "operator":
            return False, absent
        family = (
            getattr(intent, "sleeve", None)
            or (unit.get("sleeve") if isinstance(unit, dict) else None)
            or getattr(intent, "candidate_id", None)
            or candidate_id
        )
        try:
            from .minimal_size import f5_standing_hold_reason
            occupied_book = self._f5_occupied_book()
            occupied_symbols = [row.get("symbol") for row in occupied_book if row.get("symbol")]
            reason = f5_standing_hold_reason(
                getattr(self, "_namespace", ""),
                getattr(intent, "symbol", ""),
                occupied_symbols=occupied_symbols,
                direction=getattr(intent, "direction", None),
                family=family,
                occupied_book=occupied_book,
            )
        except Exception:
            raw = str(getattr(intent, "symbol", "") or "")
            sym = raw.upper().replace(".CASH", "").replace(".cash", "")
            if not (sym == "USDJPY" or sym.startswith("USDJPY")):
                return False, absent
            reason = "usdjpy_verification_hold_5pip_dsp_stop"
        if not reason:
            return False, absent
        return True, {
            "action": "HOLD",
            "reason": reason,
            "verdict": "hold",
            "join_key": "STANDING::" + str(reason),
        }
'''


def backup(path: Path) -> Path:
    dest = path.with_name(path.name + "." + STAMP)
    if not dest.exists():
        shutil.copy2(path, dest)
    return dest


def replace_function(text: str, def_line: str, new_fn: str, *, stop_prefixes: tuple[str, ...]) -> str:
    start = text.find(def_line)
    if start < 0:
        raise SystemExit(f"missing {def_line!r}")
    rest = text[start:]
    # find next top-level or same-indent def/class after this function
    lines = rest.splitlines(keepends=True)
    first = lines[0]
    indent = first[: len(first) - len(first.lstrip())]
    end = None
    acc = 0
    for i, line in enumerate(lines):
        if i == 0:
            acc += len(line)
            continue
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#") or stripped.startswith(":"):
            acc += len(line)
            continue
        if line.startswith(indent) and not line.startswith(indent + " ") and not line.startswith(indent + "\t"):
            heads = tuple(s.lstrip() for s in stop_prefixes)
            if stripped.startswith(heads):
                end = start + acc
                break
        acc += len(line)
    if end is None:
        end = start + acc
    new = new_fn.strip("\n") + "\n\n"
    return text[:start] + new + text[end:]



def main() -> None:
    ms = REPO / r"src\components\ultimate_book\minimal_size.py"
    bo = REPO / r"src\components\ultimate_book\book_owner.py"
    for p in (ms, bo):
        if not p.exists():
            raise SystemExit(f"missing {p}")
        backup(p)

    ms_text = ms.read_text(encoding="utf-8")
    if "same_currency_dsp_stack_one_bet" in ms_text:
        print("minimal_size already wired")
    else:
        ms.write_text(
            replace_function(
                ms_text,
                "def f5_standing_hold_reason(",
                NEW_HOLD.strip() + "\n",
                stop_prefixes=("def ", "class ", "F5_DUP_STACK"),
            ),
            encoding="utf-8",
        )
        print("minimal_size wired")

    bo_text = bo.read_text(encoding="utf-8")
    if "_f5_occupied_book" in bo_text:
        print("book_owner occupied helper already present")
    else:
        bo_text = replace_function(
            bo_text,
            "    def _f5_standing_symbol_hold(self, intent):",
            NEW_BOOK_HOLD.strip() + "\n",
            stop_prefixes=("    def ", "    class "),
        )
        old_call = "        standing, standing_dec = self._f5_standing_symbol_hold(intent)"
        new_call = "        standing, standing_dec = self._f5_standing_symbol_hold(intent, unit=unit, candidate_id=candidate_id)"
        if old_call not in bo_text:
            raise SystemExit("missing standing hold call")
        bo_text = bo_text.replace(old_call, new_call, 1)
        bo.write_text(bo_text, encoding="utf-8")
        print("book_owner wired")


if __name__ == "__main__":
    main()

"""Demo PLACE adapter: Challenge fill/close → one Free Trial / demo book.

Tails already-normalized ``fleet_events.jsonl``. Never ``order_send`` on
Challenge login 0 or path ``C:\\MT5\\FTMO``. Size is the Challenge lot on the event. Never invent 0.01.
Comment is ``fleet:{ticket}``. State map: challenge_ticket → demo_ticket.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from judgment.fleet.allowlist import (
    FORBIDDEN_LOGINS,
    PlaceVeto,
    assert_demo_place_target,
    is_challenge_copy_pair,
    login_is_forbidden,
    place_veto_reason,
)
from judgment.fleet.common import QUARANTINE_LOGINS, SOURCE_LOGIN, atomic_write_json, load_json
from judgment.fleet.mt5_demo import (
    MT5DemoClient,
    connect_demo_terminal,
    market_close_request,
    market_open_request,
    market_sltp_request,
    result_ok,
    result_ticket,
    tick_price,
)
from judgment.fleet.observer_config import (
    Observer,
    parse_dry_run,
    parse_micro_lot,
    require_placeable,
    resolve_copy_levels,
    resolve_copy_volume,
)


def fleet_comment(ticket: Any) -> str:
    return f"fleet:{ticket}"


def _ticket_key(ticket: Any) -> str:
    return str(ticket)


class DemoMirrorAdapter:
    """One observer / one terminal. Inject ``mt5`` in tests.

    Chair / Jev still do not place. This adapter places only on a vetted
    demo/trial row from the registry.
    """

    def __init__(
        self,
        demo_login: int | None = None,
        *,
        observer: Observer | None = None,
        terminal_path: str = "",
        account_kind: str = "demo",
        server: str = "",
        password_env: str = "",
        mt5: MT5DemoClient | None = None,
        micro_lot: float | None = None,
        dry_run: bool | None = None,
        state: dict[str, Any] | None = None,
        state_path: Path | None = None,
    ) -> None:
        if observer is None:
            observer = Observer(
                id="adhoc",
                display_name="adhoc",
                channel="mt5_demo",
                demo_login=int(demo_login or 0),
                server=server,
                terminal_path=terminal_path,
                password_env=password_env,
                status="active",
                place_enabled=True,
                account_kind=account_kind,
            )
        self.observer = observer
        self.demo_login = observer.demo_login
        self.terminal_path = observer.terminal_path
        self.source_login = SOURCE_LOGIN
        self.mt5 = mt5
        self.micro_lot = parse_micro_lot(micro_lot)
        self.dry_run = parse_dry_run(dry_run)
        self.state_path = state_path
        self.state = dict(state or {})
        self.state.setdefault("ticket_map", {})
        self._connected = False

    @property
    def ticket_map(self) -> dict[str, Any]:
        raw = self.state.get("ticket_map")
        if not isinstance(raw, dict):
            raw = {}
            self.state["ticket_map"] = raw
        return raw

    def allowed_target(self, demo_login: int | None, terminal_path: str | None = None) -> bool:
        """Login-first check. Path is enforced when a terminal path is known."""
        if login_is_forbidden(demo_login):
            return False
        path = self.terminal_path if terminal_path is None else terminal_path
        if not path:
            return True
        kind = self.observer.account_kind if terminal_path is None else None
        return place_veto_reason(login=demo_login, terminal_path=path, account_kind=kind) is None

    def persist(self) -> None:
        if self.state_path is None:
            return
        atomic_write_json(self.state_path, self.state)

    def load_state(self) -> None:
        if self.state_path is None:
            return
        loaded = load_json(self.state_path, {"ticket_map": {}})
        ticket_map = loaded.get("ticket_map")
        if not isinstance(ticket_map, dict):
            ticket_map = {}
        loaded["ticket_map"] = {str(k): v for k, v in ticket_map.items()}
        self.state = loaded

    def connect(self) -> dict[str, Any]:
        require_placeable(self.observer)
        if self.dry_run:
            return {"ok": True, "reason": "dry_run", "connected": False, "place_on_challenge": False}
        if self.mt5 is None:
            raise PlaceVeto("mt5_client_required")
        login = connect_demo_terminal(self.observer, self.mt5)
        self._connected = True
        return {"ok": True, "connected_login": login, "place_on_challenge": False}

    def shutdown(self) -> None:
        if self.mt5 is not None and self._connected:
            self.mt5.shutdown()
        self._connected = False

    def handle_event(self, event: Mapping[str, Any]) -> dict[str, Any]:
        kind = str(event.get("kind") or "").strip().lower()
        if kind == "fill":
            return self.sync_fill(event)
        if kind == "close":
            return self.sync_close(event)
        return {
            "ok": True,
            "reason": "ignored_kind",
            "kind": kind,
            "ticket": event.get("ticket"),
            "place_on_challenge": False,
        }

    def sync_fill(self, event: Mapping[str, Any]) -> dict[str, Any]:
        blocked = self._preflight(event, action="sync_fill")
        if blocked is not None:
            return blocked
        ticket = event.get("ticket")
        key = _ticket_key(ticket)
        if key in self.ticket_map:
            demo_ticket = self.ticket_map[key]
            levels = self.sync_levels(event, demo_ticket)
            return {
                "ok": True,
                "reason": "already_mapped",
                "action": "sync_fill",
                "ticket": ticket,
                "demo_ticket": demo_ticket,
                "place_on_challenge": False,
                "levels": levels,
            }
        symbol = str(event.get("symbol") or "")
        side = event.get("side")
        comment = fleet_comment(ticket)
        if self.dry_run:
            demo_ticket = f"dry:{key}"
            self.ticket_map[key] = demo_ticket
            self.persist()
            return {
                "ok": True,
                "reason": "dry_run",
                "action": "sync_fill",
                "ticket": ticket,
                "demo_ticket": demo_ticket,
                "volume": resolve_copy_volume(event),
                "sl": resolve_copy_levels(event)[0],
                "tp": resolve_copy_levels(event)[1],
                "comment": comment,
                "symbol": symbol,
                "side": side,
                "place_on_challenge": False,
                "order_send": False,
            }
        if self.mt5 is None:
            return self._fail("mt5_client_required", event, action="sync_fill")
        if not self.mt5.symbol_select(symbol, True):
            return self._fail("symbol_select_failed", event, action="sync_fill")
        tick = self.mt5.symbol_info_tick(symbol)
        if tick is None:
            return self._fail("no_tick", event, action="sync_fill")
        copy_lot = resolve_copy_volume(event)
        if copy_lot is None:
            return self._fail("missing_source_volume", event, action="sync_fill")
        copy_sl, copy_tp = resolve_copy_levels(event)
        request = market_open_request(
            symbol=symbol,
            side=str(side),
            volume=copy_lot,
            comment=comment,
            price=tick_price(tick, str(side)),
            sl=copy_sl,
            tp=copy_tp,
        )
        result = self.mt5.order_send(request)
        if not result_ok(result):
            return self._fail(
                "order_send_failed",
                event,
                action="sync_fill",
                retcode=getattr(result, "retcode", None),
            )
        demo_ticket = result_ticket(result)
        if demo_ticket is None:
            return self._fail("missing_demo_ticket", event, action="sync_fill")
        self.ticket_map[key] = demo_ticket
        self.persist()
        return {
            "ok": True,
            "reason": "opened",
            "action": "sync_fill",
            "ticket": ticket,
            "demo_ticket": demo_ticket,
            "volume": copy_lot,
            "sl": copy_sl,
            "tp": copy_tp,
            "comment": comment,
            "symbol": symbol,
            "side": side,
            "place_on_challenge": False,
            "request": request,
        }

    def sync_levels(self, event: Mapping[str, Any], mapped: Any) -> dict[str, Any]:
        """Observer TRADE_ACTION_SLTP. Not an agent SSH place."""
        sl, tp = resolve_copy_levels(event)
        if sl is None and tp is None:
            return {"ok": True, "reason": "no_source_levels", "order_send": False}
        if self.dry_run or (isinstance(mapped, str) and str(mapped).startswith("dry:")):
            return {"ok": True, "reason": "dry_run", "sl": sl, "tp": tp, "order_send": False}
        if self.mt5 is None:
            return {"ok": False, "reason": "mt5_client_required", "order_send": False}
        try:
            demo_ticket = int(mapped)
        except (TypeError, ValueError):
            return {"ok": False, "reason": "invalid_mapped_ticket", "mapped": mapped, "order_send": False}
        positions = self.mt5.positions_get(ticket=demo_ticket) or ()
        if not positions:
            return {"ok": True, "reason": "demo_position_already_gone", "order_send": False}
        position = positions[0]
        symbol = str(getattr(position, "symbol", None) or event.get("symbol") or "")
        cur_sl = float(getattr(position, "sl", 0) or 0)
        cur_tp = float(getattr(position, "tp", 0) or 0)
        want_sl = sl if sl is not None else cur_sl
        want_tp = tp if tp is not None else cur_tp
        if abs(want_sl - cur_sl) < 1e-9 and abs(want_tp - cur_tp) < 1e-9:
            return {"ok": True, "reason": "levels_already", "sl": want_sl, "tp": want_tp, "order_send": False}
        request = market_sltp_request(symbol=symbol, position=demo_ticket, sl=want_sl, tp=want_tp)
        result = self.mt5.order_send(request)
        if not result_ok(result):
            return {
                "ok": False,
                "reason": "sltp_failed",
                "retcode": getattr(result, "retcode", None),
                "sl": want_sl,
                "tp": want_tp,
            }
        return {"ok": True, "reason": "levels_applied", "sl": want_sl, "tp": want_tp, "demo_ticket": demo_ticket}

    def sync_close(self, event: Mapping[str, Any]) -> dict[str, Any]:
        blocked = self._preflight(event, action="sync_close")
        if blocked is not None:
            return blocked
        ticket = event.get("ticket")
        key = _ticket_key(ticket)
        mapped = self.ticket_map.get(key)
        if mapped is None:
            return {
                "ok": True,
                "reason": "unmapped_close_skipped",
                "action": "sync_close",
                "ticket": ticket,
                "place_on_challenge": False,
            }
        comment = fleet_comment(ticket)
        if self.dry_run or (isinstance(mapped, str) and str(mapped).startswith("dry:")):
            self.ticket_map.pop(key, None)
            self.persist()
            return {
                "ok": True,
                "reason": "dry_run" if self.dry_run else "closed_dry_map",
                "action": "sync_close",
                "ticket": ticket,
                "demo_ticket": mapped,
                "comment": comment,
                "place_on_challenge": False,
                "order_send": False,
            }
        if self.mt5 is None:
            return self._fail("mt5_client_required", event, action="sync_close")
        try:
            demo_ticket = int(mapped)
        except (TypeError, ValueError):
            return self._fail("invalid_mapped_ticket", event, action="sync_close", mapped=mapped)
        positions = self.mt5.positions_get(ticket=demo_ticket) or ()
        if not positions:
            self.ticket_map.pop(key, None)
            self.persist()
            return {
                "ok": True,
                "reason": "demo_position_already_gone",
                "action": "sync_close",
                "ticket": ticket,
                "demo_ticket": demo_ticket,
                "place_on_challenge": False,
            }
        position = positions[0]
        symbol = str(getattr(position, "symbol", None) or event.get("symbol") or "")
        volume = float(getattr(position, "volume", None) or self.micro_lot)
        pos_type = int(getattr(position, "type", 0) or 0)
        tick = self.mt5.symbol_info_tick(symbol)
        if tick is None:
            return self._fail("no_tick", event, action="sync_close")
        side = "buy" if pos_type == 0 else "sell"
        request = market_close_request(
            symbol=symbol,
            volume=volume,
            position=demo_ticket,
            comment=comment,
            price=tick_price(tick, side, closing=True),
            position_type=pos_type,
        )
        result = self.mt5.order_send(request)
        if not result_ok(result):
            return self._fail(
                "order_send_failed",
                event,
                action="sync_close",
                retcode=getattr(result, "retcode", None),
            )
        self.ticket_map.pop(key, None)
        self.persist()
        return {
            "ok": True,
            "reason": "closed",
            "action": "sync_close",
            "ticket": ticket,
            "demo_ticket": demo_ticket,
            "comment": comment,
            "place_on_challenge": False,
            "request": request,
        }

    def _preflight(self, event: Mapping[str, Any], *, action: str) -> dict[str, Any] | None:
        if is_challenge_copy_pair(event.get("source_login") or SOURCE_LOGIN, self.demo_login):
            return self._fail("veto_challenge_copy", event, action=action)
        source = event.get("source_login")
        if source not in (None, "", SOURCE_LOGIN, str(SOURCE_LOGIN)):
            try:
                if int(source) != SOURCE_LOGIN:
                    return self._fail("foreign_source_login", event, action=action)
            except (TypeError, ValueError):
                return self._fail("foreign_source_login", event, action=action)
        if source in QUARANTINE_LOGINS or source in {str(x) for x in QUARANTINE_LOGINS}:
            return self._fail("quarantined_source", event, action=action)
        if event.get("ticket") in (None, ""):
            return self._fail("missing_ticket", event, action=action)
        if not event.get("symbol"):
            return self._fail("missing_symbol", event, action=action)
        if action == "sync_fill" and not event.get("side"):
            return self._fail("missing_side", event, action=action)
        try:
            require_placeable(self.observer)
            assert_demo_place_target(
                login=self.demo_login,
                terminal_path=self.terminal_path,
                account_kind=self.observer.account_kind,
            )
        except PlaceVeto as exc:
            return self._fail(exc.reason, event, action=action, **exc.extra)
        if self.demo_login in FORBIDDEN_LOGINS:
            return self._fail("forbidden_login", event, action=action)
        return None

    def _fail(self, reason: str, event: Mapping[str, Any], *, action: str, **extra: Any) -> dict[str, Any]:
        row = {
            "ok": False,
            "reason": reason,
            "action": action,
            "ticket": event.get("ticket"),
            "kind": event.get("kind"),
            "source_login": SOURCE_LOGIN,
            "demo_login": self.demo_login,
            "target_allowed": self.allowed_target(self.demo_login),
            "place_on_challenge": False,
            "order_send": False,
        }
        row.update(extra)
        return row


def main() -> int:
    adapter = DemoMirrorAdapter(demo_login=SOURCE_LOGIN, terminal_path=r"C:\MT5\FTMO\terminal64.exe")
    print(adapter.sync_fill({"kind": "fill", "ticket": None, "symbol": "XAUUSD", "source_login": SOURCE_LOGIN}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""A/B: does the never-worsen behaviour actually differ between BASE and PATCHED?
Uses only methods present in BOTH versions, so the comparison is apples-to-apples."""
import sys, types
def run(root, label):
    for m in list(sys.modules):
        if m == "src" or m.startswith("src."): del sys.modules[m]
    sys.path.insert(0, root)
    from src.components.execution import ExecutionEngine, TradeState
    class P:
        def __init__(s): s.ticket=1; s.sl=80.511; s.tp=56.230; s.type=1; s.price_open=83.233; s.volume=1.91; s.comment="W7:energy_agri"; s.profit=0.0
    class R:
        success=True; retcode=10009; price=0.0; order=1; comment="ok"; deal=1; volume=1.0
    class M:
        def __init__(s): s.p=[P()]; s.sent=[]
        def get_positions(s,sym=None): return list(s.p)
        def get_tick(s,sym=None): return types.SimpleNamespace(bid=100.0,ask=100.1,spread_cents=None)
        def order_send(s,req):
            s.sent.append(dict(req))
            for q in s.p:
                if q.ticket==req.get("position"): q.sl=req.get("sl",q.sl); q.tp=req.get("tp",q.tp)
            return R()
    eng = ExecutionEngine(M(), {"market":{"symbol":"UKOIL_cash","mt5_symbol":"UKOIL.cash"}})
    eng._runtime_halt_snapshot = lambda *a, **k: None
    eng._record_broker_runtime_lifecycle_event = lambda *a, **k: None
    tr = TradeState(ticket=1, direction="SHORT", entry_price=83.233, stop_loss=89.984,
                    take_profit_1=56.230, take_profit_2=0.0, take_profit_3=0.0,
                    initial_volume=1.91, current_volume=1.91, sl_distance=6.751,
                    trade_id="t1", entry_time="2026-08-04T13:00:28+00:00")
    eng.active_trade = tr
    # The owner's stop is live at 80.511. The book asks for break-even (entry 83.233).
    ok = eng._move_sl_to_breakeven(tr, 1)
    live = eng.mt5.p[0].sl
    print(f"  [{label}] _move_sl_to_breakeven returned {ok}; "
          f"broker requests sent = {len(eng.mt5.sent)}; live broker SL now {live}")
    sys.path.remove(root)
    for m in list(sys.modules):
        if m == "src" or m.startswith("src."): del sys.modules[m]
    return len(eng.mt5.sent), live
print("A/B — owner stop 80.511 live on a SHORT (entry 83.233); book attempts break-even:")
b_sent, b_sl = run("/tmp/lm_base", "BASE   (host today)")
p_sent, p_sl = run("/tmp/lm_test", "PATCHED")
print()
print(f"  BASE    sent {b_sent} request(s), owner's stop ended at {b_sl}")
print(f"  PATCHED sent {p_sent} request(s), owner's stop ended at {p_sl}")
assert b_sent == 1 and abs(b_sl - 83.233) < 1e-9, "BASE should have DESTROYED the owner stop"
assert p_sent == 0 and abs(p_sl - 80.511) < 1e-9, "PATCHED must preserve it"
print("\n  => The defect is REAL on the host today, and the patch fixes it.")

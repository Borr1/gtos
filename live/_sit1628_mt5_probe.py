import MetaTrader5 as mt5, json
from datetime import datetime, timezone, timedelta
ok = mt5.initialize()
ai = mt5.account_info()
pos = mt5.positions_get() or []
orders = mt5.orders_get() or []
# history deals last 3h
t1 = datetime.now(timezone.utc)
t0 = t1 - timedelta(hours=4)
deals = mt5.history_deals_get(t0, t1) or []
def d(o):
  return {k: getattr(o,k) for k in o._asdict().keys()} if hasattr(o,'_asdict') else str(o)
out = {
  'init': bool(ok),
  'login': getattr(ai,'login',None),
  'balance': getattr(ai,'balance',None),
  'equity': getattr(ai,'equity',None),
  'profit': getattr(ai,'profit',None),
  'server': getattr(ai,'server',None),
  'name': getattr(ai,'name',None),
  'positions': [ { 'ticket':p.ticket,'symbol':p.symbol,'type':p.type,'volume':p.volume,'price_open':p.price_open,'sl':p.sl,'tp':p.tp,'profit':p.profit,'magic':p.magic,'comment':p.comment,'price_current':p.price_current,'time':p.time } for p in pos ],
  'orders': [ { 'ticket':o.ticket,'symbol':o.symbol,'type':o.type,'volume_current':o.volume_current,'price_open':o.price_open,'sl':o.sl,'tp':o.tp,'magic':o.magic,'comment':o.comment,'time_setup':o.time_setup } for o in orders ],
  'deals_n': len(deals),
  'deals': [ { 'ticket':d.ticket,'order':d.order,'symbol':d.symbol,'type':d.type,'entry':d.entry,'volume':d.volume,'price':d.price,'profit':d.profit,'magic':d.magic,'comment':d.comment,'time':d.time,'position_id':d.position_id } for d in deals[-40:] ],
}
print(json.dumps(out, default=str))
mt5.shutdown()

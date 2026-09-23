"""Current physical census and explicit retained-writer handoff, without cash history."""
from src.components.ultimate_book.broker_account_observation_v1 import read_account_info as _observed_account_info, _raw as _capture_raw
from dataclasses import dataclass
from copy import deepcopy
import hashlib
from .broker_account_contract_v1 import *
from .cash_clock_v3 import SourceClock
from .runtime_state_v1 import ExclusiveStateLease

def current_account(raw):
    row=raw_mapping(_observed_account_info(raw,'bootstrap.current_account'));login=integer(row['login']);identity(row['server'])
    return digest(dict(login_sha256=hashlib.sha256(str(login).encode()).hexdigest(),server=row['server'])),row

@dataclass(frozen=True)
class BrokerOperationalBootstrap:
    encoded:str
    def document(self):return json.loads(self.encoded)

class BrokerBootstrapCollector:
    """A scope receipt is supplied release evidence, never inferred from absent files.

    The scope lists every retained positive transport/checkpoint record and each
    current writer disposition. A historical missing checkpoint is not itself a
    positive send. An unresolved positive record survives the installation.
    """
    def __init__(self,*,raw,policy,lease,scope,clock,monotonic,journal):
        require(type(policy) is BrokerAccountPolicy and type(lease) is ExclusiveStateLease,'broker_bootstrap_concrete_sources')
        s=body(scope)
        require(set(s)=={'schema','account_id','namespace','valid_from','valid_until','authority_receipt','retained_source_census','writer_dispositions','positive_obligations'},'broker_bootstrap_scope_fields')
        require(s['schema']=='gtos.broker_operational_handoff.v1' and s['account_id']==policy.contract.account_id and s['namespace']==policy.namespace,'broker_bootstrap_scope_identity')
        receipt(s['authority_receipt']);require(instant(s['valid_from'])<instant(s['valid_until']),'broker_bootstrap_scope_interval')
        require(type(s['retained_source_census']) is list and type(s['writer_dispositions']) is list and s['writer_dispositions'],'broker_bootstrap_complete_writer_census_required')
        seen=set()
        for row in s['retained_source_census']:
            require(set(row)=={'source_id','receipt','status'},'broker_bootstrap_census_fields');identity(row['source_id']);receipt(row['receipt'])
            require(row['status'] in ('PRESENT_FULLY_READ','ABSENT_AT_CAPTURE'),'broker_bootstrap_census_unknown')
            require(row['source_id'] not in seen,'broker_bootstrap_duplicate_source');seen.add(row['source_id'])
        for row in s['writer_dispositions']:
            require(set(row)=={'writer_id','status','receipt'},'broker_bootstrap_writer_fields');identity(row['writer_id']);receipt(row['receipt'])
            require(row['status'] in ('QUIESCENT_HANDOFF','COOPERATING_CURRENT_TRANSPORT_COVERED'),'broker_bootstrap_writer_unresolved')
        require(len({x['writer_id'] for x in s['writer_dispositions']})==len(s['writer_dispositions']),'broker_bootstrap_duplicate_writer')
        require(type(s['positive_obligations']) is list,'broker_bootstrap_positive_population')
        ids=set()
        for row in s['positive_obligations']:
            require(set(row)=={'id','action','source_id','evidence'},'broker_bootstrap_positive_fields');identity(row['id']);identity(row['action'])
            require(row['source_id'] in seen and row['id'] not in ids,'broker_bootstrap_positive_source_or_duplicate');body(row['evidence']);ids.add(row['id'])
        self.raw=raw;self.policy=policy;self.lease=lease;self.scope_json=canon(scope);self.clock=clock;self.monotonic=monotonic;self.journal=journal
        require(journal.lease is lease and journal.policy is policy,'broker_bootstrap_journal_source_conflict')
        self._observations=[]
        self._raw_source=raw;self._read_evidence=[];self.failure_evidence=None
        self._assert_raw_source()

    def _assert_raw_source(self):
        access=self.journal.ownership.access
        require(self.raw is self._raw_source and self.raw is access.raw and
                self.raw is access.account_clock.raw and self.raw is access.observer.raw,
                'broker_bootstrap_raw_source_changed')

    def collect(self):
        require(self.failure_evidence is None,'broker_bootstrap_collector_already_unqualified')
        self._observations=[];self._read_evidence=[]
        try:return self._collect()
        except BaseException as exc:
            self.failure_evidence=seal(dict(schema='gtos.broker_bootstrap_failed_read.v1',
                account_id=self.policy.contract.account_id,reason=type(exc).__name__+':'+str(exc),
                reads=deepcopy(self._read_evidence),qualified=False))
            raise
        finally:self.journal.retain_account_points(dict(account_observations=self._observations))

    def _account(self,trace,label):
        self._assert_raw_source()
        evidence=dict(kind='ACCOUNT',label=label,qualified=False);self._read_evidence.append(evidence)
        try:
            value=_observed_account_info(self.raw,'bootstrap.current_account')
            evidence['raw']=_capture_raw(value);self._assert_raw_source()
            row=raw_mapping(value);login=integer(row['login']);identity(row['server'])
            aid=digest(dict(login_sha256=hashlib.sha256(str(login).encode()).hexdigest(),server=row['server']))
            at=trace.read(label)
            require(aid==self.policy.contract.account_id and row['currency']=='USD','broker_bootstrap_account_changed')
            point=dict(account_id=aid,raw=deepcopy(row),observed_at=at.isoformat(),equity=str(money(row['equity'])))
            self._observations.append(point);evidence.update(qualified=True,observed_at=at.isoformat(),account_id=aid)
            return aid,row
        except BaseException as exc:
            evidence['error']=type(exc).__name__+':'+str(exc)
            raise

    def _inventory(self,trace,label,kind):
        before,_=self._account(trace,label+':account_before')
        evidence=dict(kind='INVENTORY',label=label,inventory_kind=kind,qualified=False)
        self._read_evidence.append(evidence)
        try:
            self._assert_raw_source()
            raw=self.raw.positions_get() if kind=='position' else self.raw.orders_get()
            evidence['raw']=_capture_raw(raw);self._assert_raw_source()
            after,_=self._account(trace,label+':account_after')
            require(before==after==self.policy.contract.account_id,'broker_bootstrap_inventory_account_changed')
            result=inventory(raw,kind);evidence.update(qualified=True,account_id=after)
            return result
        except BaseException as exc:
            evidence['error']=type(exc).__name__+':'+str(exc)
            raise

    def _collect(self):
        trace=SourceClock(self.clock,self.monotonic);begin=trace.read('bootstrap:begin');scope=body(json.loads(self.scope_json));lease=self.lease.proof()
        require(lease['account_id']==self.policy.contract.account_id and lease['namespace']==self.policy.namespace,'broker_bootstrap_lease_scope')
        require(instant(scope['valid_from'])<=begin<instant(scope['valid_until']),'broker_bootstrap_handoff_expired')
        a0,r0=self._account(trace,'bootstrap:account_before');p0=self._inventory(trace,'bootstrap:positions_before','position');o0=self._inventory(trace,'bootstrap:orders_before','pending')
        trace.read('bootstrap:middle');p1=self._inventory(trace,'bootstrap:positions_after','position');o1=self._inventory(trace,'bootstrap:orders_after','pending');a1,r1=self._account(trace,'bootstrap:account_after')
        end=trace.read('bootstrap:end')
        require(a0==a1==self.policy.contract.account_id and r0['currency']==r1['currency']=='USD','broker_bootstrap_account_changed')
        require(same(p0['structural'],p1['structural']) and same(o0['structural'],o1['structural']),'broker_bootstrap_physical_changed')
        require(same(lease,self.lease.proof()),'broker_bootstrap_lease_changed')
        require(end<instant(scope['valid_until']) and (end-begin).total_seconds()<=self.policy.max_read_seconds and trace.rows[-1]['monotonic_seconds']-trace.rows[0]['clock_read_monotonic_begin']<=self.policy.max_read_seconds,'broker_bootstrap_read_expired')
        d=seal(dict(schema='gtos.broker_operational_bootstrap.v1',account_id=a0,namespace=self.policy.namespace,scope=json.loads(self.scope_json),lease=lease,source_clock_prefix=trace.prefix(),source_begin=begin.isoformat(),source_end=end.isoformat(),account_before=r0,account_after=r1,positions=p0,pending=o0,positions_after=p1,pending_after=o1,positive_obligations=scope['positive_obligations'],account_inventory_read_evidence=deepcopy(self._read_evidence),completed_original_quantity_authority=False,nominal_history_authority=False))
        return BrokerOperationalBootstrap(canon(d))

    def validate_current(self,bootstrap):
        require(type(bootstrap) is BrokerOperationalBootstrap,'broker_bootstrap_type');old=body(bootstrap.document());new=body(self.collect().document())
        for key in ('account_id','namespace','scope','lease','positive_obligations'):require(same(old[key],new[key]),'broker_bootstrap_guard_binding_changed:'+key)
        for key in ('positions','pending'):require(same(old[key]['structural'],new[key]['structural']),'broker_bootstrap_guard_inventory_changed:'+key)
        return new

@dataclass(frozen=True)
class BrokerPhysicalDisposition:
    encoded:str
    def document(self):return json.loads(self.encoded)

class BrokerPhysicalReconciler:
    """Operational joins from exact transport rows or a retained residual anchor.

    No booked profit, nominal scale or completed-original-volume conclusion is
    made. A flat anchor requires actual post-anchor exit units and full current
    absence; empty current positions alone is insufficient. Each inventory and
    history read is bound to observed account identity through the existing
    account observer; observe_order receives that account_check. A failed
    reconciler cannot be reused. Discrete account_info brackets do not make
    one raw broker call atomic.
    """
    def __init__(self,provider):
        from .broker_account_snapshot_v1 import BrokerAccountSnapshotProvider
        require(type(provider) is BrokerAccountSnapshotProvider,'broker_reconciler_concrete_source');self.provider=provider
        self._raw_source=provider.raw;self._read_evidence=[];self.failure_evidence=None;self._observations=[]
        self._assert_raw_source()
    def _assert_raw_source(self):
        access=self.provider.journal.ownership.access
        require(self.provider.raw is self._raw_source and self.provider.raw is access.raw and
                self.provider.raw is access.account_clock.raw and self.provider.raw is access.observer.raw and
                self.provider.raw is self.provider.account_clock.raw,
                'broker_reconcile_raw_source_changed')
    def collect(self,rid,*,transport=None):
        require(self.failure_evidence is None,'broker_reconcile_already_unqualified')
        self._observations=[];self._read_evidence=[];self._observe_checks=0
        try:return self._collect(rid,transport=transport)
        except BaseException as exc:
            self.failure_evidence=seal(dict(schema='gtos.broker_physical_failed_read.v1',
                account_id=self.provider.policy.contract.account_id,reason=type(exc).__name__+':'+str(exc),
                reads=deepcopy(self._read_evidence),qualified=False))
            raise
        finally:self.provider.journal.retain_account_points(dict(account_observations=self._observations))
    def _account(self,trace,label):
        self._assert_raw_source()
        evidence=dict(kind='ACCOUNT',label=label,qualified=False);self._read_evidence.append(evidence)
        try:
            value=_observed_account_info(self.provider.raw,'physical_reconcile.current_account')
            evidence['raw']=_capture_raw(value);self._assert_raw_source()
            row=raw_mapping(value);login=integer(row['login']);identity(row['server'])
            aid=digest(dict(login_sha256=hashlib.sha256(str(login).encode()).hexdigest(),server=row['server']))
            at=trace.read(label)
            require(aid==self.provider.policy.contract.account_id and row['currency']=='USD','broker_reconcile_account_conflict')
            point=dict(account_id=aid,raw=deepcopy(row),observed_at=at.isoformat(),equity=str(money(row['equity'])))
            self._observations.append(point);evidence.update(qualified=True,observed_at=at.isoformat(),account_id=aid)
            return aid,row
        except BaseException as exc:
            evidence['error']=type(exc).__name__+':'+str(exc)
            raise
    def _bound(self,trace,label,*,kind,method,kwargs):
        before,_=self._account(trace,label+':account_before')
        evidence=dict(kind=kind,label=label,method=method,qualified=False)
        if kind=='INVENTORY':evidence['inventory_kind']='position' if method=='positions_get' else 'pending'
        if kwargs:evidence['arguments']=deepcopy(kwargs)
        self._read_evidence.append(evidence)
        try:
            self._assert_raw_source()
            fn=getattr(self.provider.raw,method,None);require(callable(fn),'broker_reconcile_source_method_missing:'+method)
            raw=fn(**kwargs) if kwargs else fn()
            evidence['raw']=_capture_raw(raw);self._assert_raw_source()
            after,_=self._account(trace,label+':account_after')
            require(before==after==self.provider.policy.contract.account_id,'broker_reconcile_read_account_changed')
            evidence.update(qualified=True,account_id=after)
            return raw
        except BaseException as exc:
            evidence['error']=type(exc).__name__+':'+str(exc)
            raise
    def _inventory(self,trace,label,kind):
        method='positions_get' if kind=='position' else 'orders_get'
        return inventory(self._bound(trace,label,kind='INVENTORY',method=method,kwargs={}),kind)
    def _history(self,trace,label,method,**kwargs):
        return self._bound(trace,label,kind='HISTORY',method=method,kwargs=kwargs)
    def _collect(self,rid,*,transport=None):
        from src.components.transport_v2 import Journal,observe_order
        p=self.provider;j=p.journal;op=j.get(rid);require(op is not None,'broker_reconcile_obligation_absent')
        self._assert_raw_source();raw=p.raw;trace=SourceClock(p.clock,p.monotonic);begin=trace.read('physical_reconcile:begin');binding=j.operational_binding();aid,a0=self._account(trace,'physical_reconcile:account_before')
        require(aid==j.contract.account_id,'broker_reconcile_account_conflict')
        def account_check():
            self._observe_checks+=1
            now,_=self._account(trace,'physical_reconcile:observe_order:'+str(self._observe_checks))
            require(now==aid,'broker_reconcile_account_conflict')
        positions=self._inventory(trace,'physical_reconcile:positions','position');pending=self._inventory(trace,'physical_reconcile:pending','pending');payload=op['payload'];evidence={};newpos=None;neworder=None;state=None;anchor=payload.get('residual_anchor')
        imported_order=transport is None and payload.get('kind')=='IMPORTED_PHYSICAL' and payload.get('broker_order_identity') is not None
        if transport is not None or imported_order:
            if not imported_order:
                require(type(transport) is Journal and payload['kind']=='NEW_REQUEST','broker_reconcile_concrete_transport')
                source=transport.execution_request_snapshot(rid);row=source['bundle']['row'];evidence['transport']=source
                require(same(row['request'],payload['request']) and same(row['context'],payload['context']),'broker_reconcile_transport_request_conflict')
                require(row['context']['account_identity']['account_id']==aid,'broker_reconcile_transport_account_conflict')
                ticket=integer(row.get('order_ticket'));request=row['request']
            else:
                broker_order=payload['broker_order_identity'];ticket=integer(broker_order['ticket'])
                # A comparison hint for the unchanged strict order observer.
                # It is not a submitted request, ACK, management contract or
                # broker_request_v2 receipt. Original broker facts stay retained.
                request=dict(action=5,symbol=broker_order['symbol'],magic=broker_order['magic'],type=broker_order['type'],volume=broker_order['volume_initial'],price=broker_order['price_open'])
                evidence['imported_broker_order_identity']=deepcopy(broker_order)
                candidates=[r for r in pending['structural'] if r['ticket']==ticket]
                if candidates:actual=candidates[0]
                else:
                    history=self._history(trace,'physical_reconcile:imported_terminal_order','history_orders_get',ticket=ticket)
                    require(type(history) in (list,tuple) and len(history)==1,'broker_imported_order_history_unknown');actual=raw_mapping(history[0])
                    evidence['imported_terminal_order']=deepcopy(actual)
                for key in ('ticket','symbol','magic','type'):
                    require(same(actual[key],broker_order[key]),'broker_imported_order_identity_conflict:'+key)
                for key in ('volume_initial','price_open'):
                    require(money(actual[key])==money(broker_order[key]),'broker_imported_order_identity_conflict:'+key)
            matches=[r for r in pending['structural'] if r['ticket']==ticket]
            oldpos=payload.get('position')
            absent_anchor_pending=(oldpos is not None and anchor is not None and len(matches)==1 and matches[0]['position_id']==oldpos['identifier'] and not any(r['identifier']==oldpos['identifier'] for r in positions['structural']))
            if absent_anchor_pending:
                for key in ('symbol','magic','type'):require(same(matches[0][key],request[key]),'broker_reconcile_pending_request_identity:'+key)
                observed=dict(state='PENDING',order_ticket=ticket,strict_source=dict(kind='current_pending_with_absent_residual_anchor_candidate',order=deepcopy(matches[0]),residual_anchor=deepcopy(anchor)))
            else:
                shared_flat=[]
                if imported_order and len(matches)==1 and not any(r['identifier']==matches[0]['position_id'] for r in positions['structural']):
                    for other in j.operations():
                        link=other['payload'].get('pending_position_flat_link')
                        if link is not None and any(same(matches[0],r) for r in body(link)['pending_remainders']):shared_flat.append(link)
                if shared_flat:
                    validate_pending_links(positions['structural'],matches,j.operations())
                    evidence['shared_qualified_residual_flat']=deepcopy(shared_flat)
                    observed=dict(state='PENDING',order_ticket=ticket,strict_source=dict(kind='current_pending_with_independently_qualified_flat_position',order=deepcopy(matches[0])))
                else:observed=observe_order(raw,ticket,request,account_check=account_check)
            evidence['strict_order_observation']=observed
            if observed['state'] in ('PENDING','PARTIAL'):
                require(len(matches)==1,'broker_reconcile_pending_population_conflict');neworder=matches[0]
            pt=observed.get('position_ticket')
            if pt is not None:
                matches=[r for r in positions['structural'] if r['ticket']==pt];require(len(matches)==1,'broker_reconcile_position_population_conflict');newpos=matches[0]
                expectedside=0 if request['type'] in (0,2,4) else 1
                require(newpos['type']==expectedside and newpos['symbol']==request['symbol'] and newpos['magic']==request['magic'],'broker_reconcile_position_scope_conflict')
                if neworder is not None:require(neworder['position_id']==newpos['identifier'],'broker_reconcile_partial_identity_conflict')
                state='PARTIAL' if neworder is not None else 'OPEN'
            elif neworder is not None:state='FLAT' if absent_anchor_pending else 'PENDING'
            elif observed.get('release') is True:
                require(observed['strict_source'].get('no_fill') is True,'broker_reconcile_no_fill_unproved');state='NO_FILL'
            elif observed.get('state')=='FILLED' and observed.get('strict_source',{}).get('kind')=='executed_order_position_not_current' and observed['strict_source'].get('history_state') in (2,6):
                history=self._history(trace,'physical_reconcile:remainder_terminal_order','history_orders_get',ticket=ticket)
                require(type(history) in (list,tuple) and len(history)==1,'broker_reconcile_remainder_terminal_population')
                h=raw_mapping(history[0]);pid=integer(h['position_id'])
                require(type(h['state']) is int and h['state'] in (2,6) and integer(h['ticket'])==ticket,'broker_reconcile_remainder_terminal_state')
                for key in ('symbol','magic','type'):require(same(h[key],request[key]),'broker_reconcile_remainder_identity:'+key)
                require(money(h['volume_initial'])==money(request['volume']) and 0<=money(h['volume_current'])<=money(h['volume_initial']),'broker_reconcile_remainder_units_conflict')
                if request['action']==5:require(money(h['price_open'])==money(request['price']),'broker_reconcile_remainder_price_conflict')
                require(not any(x['ticket']==ticket or x['position_id']==pid for x in pending['structural']) and not any(x['identifier']==pid for x in positions['structural']),'broker_reconcile_remainder_identity_still_live')
                evidence['terminal_remainder_disposition']=h
                if oldpos is not None and anchor is not None:
                    require(oldpos['identifier']==pid,'broker_reconcile_remainder_anchor_conflict');state='FLAT'
                else:
                    retained=payload.get('pending_position_flat_link');require(retained is not None,'broker_reconcile_partial_terminal_flat_unknown');link=body(retained)
                    require(link['position']['identifier']==pid and any(x['ticket']==ticket and money(x['volume_current'])==money(h['volume_current']) for x in link['pending_remainders']),'broker_reconcile_remainder_qualified_flat_conflict')
                    evidence['physically_resolved_flat']=dict(terminal_order=h,order_ticket=ticket,position_identifier=pid,qualified_residual_flat_source=retained,actual_completed_original_volume=None,realized_cash=None,analytics_complete=False,reusable_origin=False)
                    state='PHYSICALLY_RESOLVED_FLAT'
            else:
                source_order=observed['strict_source']
                require(observed['state']=='FILLED' and source_order.get('kind')=='executed_order_position_not_current' and source_order.get('history_state')==4 and money(source_order['volume_current'])==0,'broker_reconcile_terminal_filled_remainder_unproved')
                pid=integer(source_order['position_id'])
                require(not any(r['ticket']==ticket or r['position_id']==pid for r in pending['structural']) and not any(r['identifier']==pid for r in positions['structural']),'broker_reconcile_terminal_identity_still_live')
                history=self._history(trace,'physical_reconcile:terminal_filled_order','history_orders_get',ticket=ticket);require(type(history) in (list,tuple) and len(history)==1,'broker_reconcile_terminal_history_population')
                h=raw_mapping(history[0]);require(integer(h['ticket'])==ticket and integer(h['position_id'])==pid and type(h['state']) is int and h['state']==4 and money(h['volume_current'])==0,'broker_reconcile_terminal_history_identity')
                for key in ('symbol','magic','type'):require(same(h[key],request[key]),'broker_reconcile_terminal_request_identity:'+key)
                require(money(h['volume_initial'])==money(request['volume']),'broker_reconcile_terminal_requested_volume_conflict')
                if request['action']==5:require(money(h['price_open'])==money(request['price']),'broker_reconcile_terminal_requested_price_conflict')
                evidence['physically_resolved_flat']=dict(terminal_order=h,order_ticket=ticket,position_identifier=pid,actual_completed_original_volume=None,realized_cash=None,analytics_complete=False,reusable_origin=False)
                state='PHYSICALLY_RESOLVED_FLAT'
        else:
            require(payload.get('position') is not None,'broker_reconcile_position_anchor_required')
            old=payload['position'];matches=[r for r in positions['structural'] if r['identifier']==old['identifier']]
            if matches:
                require(len(matches)==1,'broker_reconcile_duplicate_position');newpos=matches[0]
                for key in ('ticket','identifier','symbol','magic','type','price_open'):require(same(newpos[key],old[key]),'broker_reconcile_identity_conflict:'+key)
                state='OPEN'
            else:state='FLAT';require(anchor is not None,'broker_reconcile_residual_anchor_required')
        if imported_order and newpos is not None:
            shared=[other for other in j.operations() if other['id']!=rid and other['payload'].get('kind')=='IMPORTED_PHYSICAL' and other['payload'].get('broker_order_identity') is None and other['payload'].get('position') is not None and other['payload']['position']['identifier']==newpos['identifier']]
            require(len(shared)<=1,'broker_imported_position_multiple_owners')
            if shared:
                for key in ('ticket','identifier','symbol','magic','type','price_open'):
                    require(same(shared[0]['payload']['position'][key],newpos[key]),'broker_imported_shared_position_conflict:'+key)
                evidence['shared_current_position_obligation']=deepcopy(shared[0]);newpos=None
        retained=payload.get('pending_position_flat_link')
        if imported_order and retained is not None and neworder is not None and newpos is None and state=='PENDING':
            link=body(retained)
            require(any(same(neworder,r) for r in link['pending_remainders']),'broker_retained_pending_remainder_changed')
            require(not any(r['identifier']==link['position']['identifier'] for r in positions['structural']),'broker_retained_flat_position_reappeared')
            evidence.update(retained_residual_flat_link=deepcopy(retained),qualified_pending_remainders=deepcopy(link['pending_remainders']),qualified_exits=deepcopy(link['qualified_exits']),residual_anchor=deepcopy(link['residual_anchor']))
            state='PENDING_POSITION_FLAT'
        if state=='FLAT':
            old=payload['position'];require(not any(r['identifier']==old['identifier'] for r in positions['structural']),'broker_reconcile_identity_still_live')
            remainders=[r for r in pending['structural'] if r['position_id']==old['identifier']]
            for order in remainders:
                require(order['symbol']==old['symbol'] and order['magic']==old['magic'] and (0 if order['type'] in (2,4) else 1)==old['type'],'broker_reconcile_pending_historical_identity_conflict')
            records=self._history(trace,'physical_reconcile:exit_deals','history_deals_get',position=old['identifier']);require(type(records) in (list,tuple),'broker_reconcile_exit_history_unknown');records=[raw_mapping(r) for r in records]
            require(len({integer(r['ticket']) for r in records})==len(records),'broker_reconcile_duplicate_deal')
            exits=[]
            for r in records:
                require(integer(r['position_id'])==old['identifier'],'broker_reconcile_history_position_conflict')
                seconds=integer(r['time'],positive=False);millis=integer(r['time_msc'],positive=False);require(millis//1000==seconds,'broker_reconcile_deal_time_conflict')
                at=p.account_clock.normalize(millis/1000)[0]
                if at<=instant(anchor['observed_at']):continue
                require(at<=begin,'broker_reconcile_future_deal')
                require(r['symbol']==old['symbol'] and integer(r['entry'],positive=False) in (1,3),'broker_reconcile_new_entry_or_symbol_conflict')
                require(type(r['type']) is int and r['type']==1-old['type'],'broker_reconcile_exit_direction_conflict')
                exits.append(dict(raw=r,utc=at.isoformat(),volume=str(money(r['volume'],positive=True))))
            require(exact_sum(x['volume'] for x in exits)==money(anchor['volume']),'broker_reconcile_anchor_exit_units_incomplete')
            evidence.update(history=records,qualified_exits=exits,residual_anchor=anchor)
            repeated=self._history(trace,'physical_reconcile:exit_deals_repeat','history_deals_get',position=old['identifier']);require(same(records,[raw_mapping(r) for r in repeated]),'broker_reconcile_history_changed')
            if remainders:
                evidence['qualified_pending_remainders']=deepcopy(remainders)
                state='PENDING_POSITION_FLAT' if neworder is not None else 'POSITION_FLAT_PENDING_REMAINDER'
        positions_after=self._inventory(trace,'physical_reconcile:positions_after','position');pending_after=self._inventory(trace,'physical_reconcile:pending_after','pending');aid1,a1=self._account(trace,'physical_reconcile:account_middle');trace.read('physical_reconcile:after_inventory')
        require(aid1==aid and same(positions['structural'],positions_after['structural']) and same(pending['structural'],pending_after['structural']),'broker_reconcile_source_changed')
        if transport is not None:require(same(source,transport.execution_request_snapshot(rid)),'broker_reconcile_transport_changed')
        if 'terminal_remainder_disposition' in evidence:
            repeated=self._history(trace,'physical_reconcile:remainder_history_repeat','history_orders_get',ticket=ticket);require(same([evidence['terminal_remainder_disposition']],[raw_mapping(x) for x in repeated]),'broker_reconcile_remainder_history_changed')
        if imported_order and 'imported_terminal_order' in evidence:
            repeated=self._history(trace,'physical_reconcile:imported_order_history_repeat','history_orders_get',ticket=ticket);require(same([evidence['imported_terminal_order']],[raw_mapping(x) for x in repeated]),'broker_imported_order_history_changed')
        if state=='PHYSICALLY_RESOLVED_FLAT':
            final=self._history(trace,'physical_reconcile:terminal_history_final','history_orders_get',ticket=ticket);require(same([evidence['physically_resolved_flat']['terminal_order']],[raw_mapping(x) for x in final]),'broker_reconcile_terminal_history_changed')
        aid2,a2=self._account(trace,'physical_reconcile:account_after');end=trace.read('physical_reconcile:end')
        require(aid2==aid and binding==j.operational_binding() and (end-begin).total_seconds()<=p.policy.max_read_seconds and trace.rows[-1]['monotonic_seconds']-trace.rows[0]['clock_read_monotonic_begin']<=p.policy.max_read_seconds,'broker_reconcile_binding_or_span_changed')
        value=seal(dict(schema='gtos.broker_physical_disposition.v1',request_id=rid,account_id=aid,operational_binding=binding,prior=op,state=state,position=newpos,order=neworder,evidence=evidence,positions=positions,pending=pending,positions_after=positions_after,pending_after=pending_after,account_before=a0,account_middle=a1,account_after=a2,account_inventory_read_evidence=deepcopy(self._read_evidence),source_begin=begin.isoformat(),source_end=end.isoformat(),source_clock_prefix=trace.prefix(),completed_original_quantity_authority=False,cash_completion_authority=False))
        return BrokerPhysicalDisposition(canon(value))

"""Append transport coverage to an existing W7 bootstrap; never reset its epoch."""
import copy,json
from pathlib import Path
from .runtime_assembly_v1 import canonical,digest,sealed,checked_document,instant,receipt,AssemblyUnavailable
from .runtime_state_v1 import ExclusiveStateLease
from .broker_account_contract_v1 import body as broker_body
from .broker_account_bootstrap_v1 import BrokerBootstrapCollector
from .broker_account_journal_v1 import BrokerAccountJournal
from .w7_constants_v1 import W7_NAMESPACE

TABLE='w7_bootstrap_coverage_transitions'
SCHEMA='gtos.w7_bootstrap_coverage.transition.v1'
RECORD='gtos.w7_bootstrap_coverage.transition_record.v2'
LINEAGE='gtos.w7_transport_lineage.v1'
OBSERVATION='gtos.w7_transport_lineage.observation.v1'
FIELDS={'schema','account_id','namespace','writer_journal_path','writer_lease_scope_receipt','prior_bootstrap_receipt','prior_observation_count','prior_observations_sha256','prior_transition_receipt','target_material_sha256','coordinator_sha256','account_journal_identity_sha256','account_journal_generation','account_bootstrap_source_receipt','account_scope_source_receipt','coverage_source_receipt','transition_id','authority_receipt','valid_from','valid_until'}

def require(ok,reason):
    if not ok:raise AssemblyUnavailable(reason)

def material(bootstrap):
    result=copy.deepcopy(bootstrap);result.pop('receipt',None);result.pop('coverage_transition',None);return result

def _transport_lineage(census):
    """Capture identities and immutable history, not authority from request states."""
    from src.components.transport_v2 import Journal
    stores=[]
    for path in census['paths']:
        view=Journal.open_existing(path,'__w7_lineage__');requests=[]
        with view.connection() as source:
            source.execute('BEGIN')
            rows=list(source.execute('SELECT id,lane,payload FROM requests ORDER BY id'))
            events=list(source.execute('SELECT id,request_id,payload FROM events ORDER BY rowid'))
        ids={row[0] for row in rows}
        require(all(row[1] in ids for row in events),'w7_transport_orphan_event')
        expected={rid for lane in census['lanes'] if lane['path']==path for rid in lane['request_ids']}
        require(ids==expected and all(lane['file_identity']==list(view._existing_identity) for lane in census['lanes'] if lane['path']==path),'w7_transport_census_lineage_changed')
        for rid,lane,payload in rows:
            row=json.loads(payload);history=[event for event in events if event[1]==rid]
            require(row.get('request_id')==rid and row.get('lane')==lane and type(row.get('revision')) is int and row['revision']==len(history),'w7_transport_request_revision')
            commitment={key:row[key] for key in ('request_id','lane','action_key','action','request','context','created_at','deadline')}
            for revision,(eid,event_rid,encoded) in enumerate(history,1):
                event=json.loads(encoded)
                require(eid==rid+':'+str(revision) and event.get('event_id')==eid and event.get('request_id')==rid,'w7_transport_event_sequence')
                require(all(event.get(key)==row[key] for key in ('request','context','action')),'w7_transport_event_contract')
            if history:
                final=json.loads(history[-1][2])
                require(all(final.get(key)==row.get(key) for key in ('state','observed_at','order_ticket','position_ticket')),'w7_transport_final_event')
            else:require(row.get('state')=='RESERVED','w7_transport_initial_state')
            requests.append(dict(request_id=rid,lane=lane,contract_sha256=digest(commitment),revision=row['revision'],payload_sha256=digest(row),events=[dict(event_id=eid,payload_sha256=digest(encoded)) for eid,_,encoded in history]))
        stores.append(dict(path=path,file_identity=list(view._existing_identity),requests=requests))
    return sealed(dict(schema=LINEAGE,stores=stores))

def _lineage_extends(prior,current):
    before=checked_document(prior,LINEAGE);after=checked_document(current,LINEAGE)
    require(set(before)==set(after)=={'schema','stores'},'w7_transport_lineage_fields')
    stores={s['path']:s for s in after['stores']}
    require(len(stores)==len(after['stores']),'w7_transport_duplicate_store')
    for old in before['stores']:
        new=stores.get(old['path'])
        require(new is not None and new['file_identity']==old['file_identity'],'w7_transport_known_store_missing_or_replaced')
        requests={r['request_id']:r for r in new['requests']}
        require(len(requests)==len(new['requests']),'w7_transport_duplicate_request')
        for original in old['requests']:
            observed=requests.get(original['request_id'])
            require(observed is not None and observed['lane']==original['lane'] and observed['contract_sha256']==original['contract_sha256'],'w7_transport_known_request_missing_or_changed')
            require(observed['revision']>=original['revision'] and observed['events'][:len(original['events'])]==original['events'],'w7_transport_known_event_missing_or_changed')
            if observed['revision']==original['revision']:require(observed['payload_sha256']==original['payload_sha256'],'w7_transport_unrecorded_state_change')

def _lineage_head(db,head):
    lineage=head['transport_lineage'];previous=head['receipt'];sequence=0;at=instant(head['committed_at'])
    exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='w7_transport_lineage_observations'").fetchone()
    if exists:
        for seq,payload in db.execute('SELECT sequence,payload FROM w7_transport_lineage_observations WHERE coverage_receipt=? ORDER BY sequence',(head['receipt'],)):
            row=json.loads(payload);record=checked_document(row,OBSERVATION)
            require(set(record)=={'schema','sequence','coverage_receipt','prior_receipt','lineage','observed_account_bootstrap','observed_at'} and seq==record['sequence']==sequence+1 and record['coverage_receipt']==head['receipt'] and record['prior_receipt']==previous,'w7_transport_lineage_observation_chain')
            source=broker_body(record['observed_account_bootstrap']);next_at=instant(record['observed_at'])
            require(source['schema']=='gtos.broker_operational_bootstrap.v1' and source['account_id']==head['target_bootstrap']['account_id'] and source['namespace']==broker_body(head['observed_account_bootstrap'])['namespace'] and at<=instant(source['source_begin'])<=instant(source['source_end'])<=next_at,'w7_transport_lineage_observation_source')
            _lineage_extends(lineage,record['lineage']);lineage=record['lineage'];previous=row['receipt'];sequence=seq
            at=next_at
    return lineage,previous,sequence

def _append_lineage_observation(db,head,lineage,prior_receipt,sequence,observed,at):
    row=sealed(dict(schema=OBSERVATION,sequence=sequence+1,coverage_receipt=head['receipt'],prior_receipt=prior_receipt,lineage=lineage,observed_account_bootstrap=observed,observed_at=at.isoformat()))
    db.execute('CREATE TABLE IF NOT EXISTS w7_transport_lineage_observations (coverage_receipt TEXT NOT NULL,sequence INTEGER NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(coverage_receipt,sequence))')
    db.execute("CREATE TRIGGER IF NOT EXISTS w7_lineage_no_update BEFORE UPDATE ON w7_transport_lineage_observations BEGIN SELECT RAISE(ABORT,'w7_transport_lineage_append_only'); END")
    db.execute("CREATE TRIGGER IF NOT EXISTS w7_lineage_no_delete BEFORE DELETE ON w7_transport_lineage_observations BEGIN SELECT RAISE(ABORT,'w7_transport_lineage_append_only'); END")
    db.execute('INSERT INTO w7_transport_lineage_observations VALUES(?,?,?)',(head['receipt'],sequence+1,canonical(row)))

def _authorization(prior,target,head,journal_path):
    from .w7_strategy_runtime_v1 import validate_w7_bootstrap
    from .dual_writer_assembly_v1 import _state_path,_overlap
    validate_w7_bootstrap(prior);validate_w7_bootstrap(target)
    t=target.get('coverage_transition');a=checked_document(t,SCHEMA)
    require(set(a)==FIELDS,'w7_coverage_transition_fields')
    for key in ('account_id','writer_lease_scope_receipt','prior_bootstrap_receipt','prior_observations_sha256','target_material_sha256','coordinator_sha256','account_journal_identity_sha256','account_bootstrap_source_receipt','account_scope_source_receipt','coverage_source_receipt','authority_receipt'):receipt(a[key])
    if a['prior_transition_receipt'] is not None:receipt(a['prior_transition_receipt'])
    require(type(a['prior_observation_count']) is int and a['prior_observation_count']>=0,'w7_coverage_observation_count')
    require(a['namespace']==prior['namespace']==target['namespace']==W7_NAMESPACE and a['account_id']==prior['account_id']==target['account_id'],'w7_coverage_identity')
    require(type(a['transition_id']) is str and bool(a['transition_id']) and type(a['account_journal_generation']) is str and bool(a['account_journal_generation']),'w7_coverage_explicit_identity')
    require(instant(a['valid_from'])<instant(a['valid_until']),'w7_coverage_interval')
    require(a['prior_bootstrap_receipt']==prior['receipt'] and a['prior_transition_receipt']==(None if head is None else head['receipt']) and a['target_material_sha256']==digest(material(target)),'w7_coverage_chain_conflict')
    require(_state_path(a['writer_journal_path'])==_state_path(str(journal_path)),'w7_coverage_same_strategy_journal_required')
    before,after=material(prior),material(target)
    require(set(before)==set(after),'w7_coverage_bootstrap_fields_changed')
    changed={k for k in before if canonical(before[k])!=canonical(after[k])}
    require(changed<= {'transport_roots','reconciliation_source_receipt'} and 'transport_roots' in changed,'w7_coverage_only_transport_extension_permitted')
    require(after['reconciliation_source_receipt']==a['coverage_source_receipt'],'w7_coverage_reconciliation_pin')
    old_roots=before['transport_roots'];new_roots=after['transport_roots']
    require(type(new_roots) is list and len(new_roots)>len(old_roots),'w7_coverage_extension_required')
    require(new_roots[:len(old_roots)]==old_roots,'w7_coverage_prior_root_order_and_bytes_preserved')
    paths=[_state_path(p) for p in new_roots]
    require(all(not _overlap(a,b) for i,a in enumerate(paths) for b in paths[i+1:]),'w7_coverage_root_alias_or_overlap')
    return a

def effective_bootstrap(journal,db,base):
    """Verify every append; the required_policy bootstrap row remains original."""
    from .w7_strategy_runtime_v1 import validate_w7_bootstrap
    validate_w7_bootstrap(base);current=base;head=None;seq=0;ids=set();coverage_receipts=set()
    exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(TABLE,)).fetchone()
    if exists:
        for sequence,transition_id,payload in db.execute('SELECT sequence,transition_id,payload FROM w7_bootstrap_coverage_transitions ORDER BY sequence'):
            row=json.loads(payload);r=checked_document(row,RECORD)
            require(set(r)=={'schema','sequence','prior_bootstrap','target_bootstrap','observed_account_bootstrap','committed_at','writer_lease_scope','transport_census','transport_lineage'},'w7_coverage_record_fields')
            require(type(r['sequence']) is int and r['sequence']==sequence==seq+1 and r['prior_bootstrap']==current,'w7_coverage_record_chain')
            target=r['target_bootstrap'];a=_authorization(current,target,head,journal.path)
            require(transition_id==a['transition_id'] and transition_id not in ids,'w7_coverage_transition_id')
            prefix=[list(row) for row in db.execute('SELECT id,payload FROM observations ORDER BY id LIMIT ?',(a['prior_observation_count'],))]
            require(len(prefix)==a['prior_observation_count'] and digest(prefix)==a['prior_observations_sha256'],'w7_coverage_original_observation_prefix_changed')
            require(r['transport_census']['issues']==[],'w7_coverage_record_transport_gap')
            checked_document(r['transport_lineage'],LINEAGE)
            require({s['path'] for s in r['transport_lineage']['stores']}==set(r['transport_census']['paths']),'w7_coverage_record_transport_lineage')
            if head is not None:_lineage_extends(_lineage_head(db,head)[0],r['transport_lineage'])
            held=checked_document(r['writer_lease_scope'],'gtos.state_lease_scope.v1')
            require(held['account_id']==a['account_id'] and held['namespace']==W7_NAMESPACE and r['writer_lease_scope']['receipt']==a['writer_lease_scope_receipt'],'w7_coverage_record_writer_lease')
            observed=broker_body(r['observed_account_bootstrap']);committed=instant(r['committed_at'])
            require(observed['schema']=='gtos.broker_operational_bootstrap.v1' and observed['account_id']==a['account_id'] and observed['scope']['source_receipt']==a['account_scope_source_receipt'],'w7_coverage_record_account_source')
            require(instant(a['valid_from'])<=instant(observed['source_begin'])<=instant(observed['source_end'])<=committed<instant(a['valid_until']),'w7_coverage_record_clock')
            current=target;head=row;seq+=1;ids.add(transition_id);coverage_receipts.add(row['receipt'])
    if head is not None:_lineage_head(db,head)
    lineage_exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='w7_transport_lineage_observations'").fetchone()
    if lineage_exists:
        require({r[0] for r in db.execute('SELECT DISTINCT coverage_receipt FROM w7_transport_lineage_observations')}<=coverage_receipts,'w7_transport_orphan_lineage_observation')
    return current,head,seq

def ensure_w7_bootstrap_coverage(journal,*,target,writer_lease,account_journal,collector,clock):
    """Called during canonical account-owned startup, before constructing W7 runtime."""
    from .w7_strategy_runtime_v1 import W7StrategyJournal,validate_w7_bootstrap,_JOURNAL_METHODS
    from .broker_account_handoff_transition_v1 import _pins,_chain
    require(type(journal) is W7StrategyJournal and type(writer_lease) is ExclusiveStateLease and type(account_journal) is BrokerAccountJournal and type(collector) is BrokerBootstrapCollector,'w7_coverage_concrete_dependencies')
    for name,method in _JOURNAL_METHODS.items():
        require(getattr(W7StrategyJournal,name) is method and getattr(getattr(journal,name),'__func__',None) is method,'w7_coverage_journal_methods_changed')
    validate_w7_bootstrap(target)
    require(collector.journal is account_journal and collector.policy is account_journal.policy and collector.lease is account_journal.lease and clock is collector.clock,'w7_coverage_collector_binding')
    ownership=broker_body(account_journal.ownership.proof());require(ownership['phase'] in ('BOOTSTRAP','MAINTENANCE'),'w7_coverage_account_ownership_required')
    writer_lease.proof();scope=writer_lease.scope();require(scope['account_id']==target['account_id'] and scope['namespace']==W7_NAMESPACE,'w7_coverage_writer_lease_identity')
    pins,account_bootstrap=_pins(account_journal);account_scope,_,_=_chain(account_journal,pins,account_bootstrap)
    require(json.loads(collector.scope_json)==account_scope,'w7_coverage_current_account_scope_required')
    with journal.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        saved=db.execute("SELECT payload FROM required_policy WHERE key='bootstrap'").fetchone()
        require(saved is not None,'w7_coverage_existing_bootstrap_required');base=json.loads(saved[0]);current,head,seq=effective_bootstrap(journal,db,base)
        reuse=current==target
        if reuse:
            require(head is not None,'w7_coverage_unused_authorization')
            a=checked_document(target['coverage_transition'],SCHEMA)
        else:
            a=_authorization(current,target,head,journal.path)
        expected=dict(coordinator_sha256=pins['coordinator_sha256'],account_journal_identity_sha256=pins['journal_identity_sha256'],account_journal_generation=pins['journal_generation'],account_bootstrap_source_receipt=pins['bootstrap_source_receipt'],writer_lease_scope_receipt=scope['receipt'])
        require(all(a[k]==v for k,v in expected.items()),'w7_coverage_live_pins_conflict')
        if reuse:
            # _chain validated every same-journal append above. An accepted later
            # handoff may advance scope; the committed scope must remain an ancestor.
            account_scopes={account_bootstrap['scope']['source_receipt']}
            exists=account_journal.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='operational_handoff_transitions'").fetchone()
            if exists:
                for row in account_journal.db.execute('SELECT payload FROM operational_handoff_transitions ORDER BY sequence'):
                    account_scopes.add(broker_body(json.loads(row[0]))['target_scope']['source_receipt'])
            require(a['account_scope_source_receipt'] in account_scopes,'w7_coverage_account_scope_lineage_conflict')
        else:
            require(a['account_scope_source_receipt']==account_scope['source_receipt'],'w7_coverage_live_pins_conflict')
            previous_observations=[list(row) for row in db.execute('SELECT id,payload FROM observations ORDER BY id')]
            require(len(previous_observations)==a['prior_observation_count'] and digest(previous_observations)==a['prior_observations_sha256'],'w7_coverage_current_observation_pin_conflict')
        begin=instant(clock())
        if not reuse:require(instant(a['valid_from'])<=begin<instant(a['valid_until']),'w7_coverage_authorization_expired')
        from .runtime_state_v1 import discover_recovery_lanes
        census=discover_recovery_lanes(target['transport_roots']);require(not census['issues'],'w7_coverage_transport_census_gap')
        lineage=_transport_lineage(census)
        known,prior_receipt,lineage_sequence=_lineage_head(db,head) if head is not None else (None,None,0)
        if known is not None:_lineage_extends(known,lineage)
        observed=collector.collect().document();end=instant(clock())
        require(begin<=end and (reuse or end<instant(a['valid_until'])) and (end-begin).total_seconds()<=account_journal.policy.max_read_seconds and instant(observed['source_begin'])>=begin and instant(observed['source_end'])<=end and (end-instant(observed['source_begin'])).total_seconds()<=account_journal.policy.max_read_seconds,'w7_coverage_source_expired')
        require(discover_recovery_lanes(target['transport_roots'])==census,'w7_coverage_transport_census_changed')
        require(_transport_lineage(census)==lineage,'w7_coverage_transport_history_changed')
        require(_pins(account_journal)[0]==pins,'w7_coverage_account_identity_changed')
        require(_chain(account_journal,pins,account_bootstrap)[0]==account_scope,'w7_coverage_account_scope_changed')
        writer_lease.proof();require(writer_lease.scope()==scope,'w7_coverage_writer_lease_changed')
        if reuse:
            returned=instant(clock())
            require(end<=returned and (returned-instant(observed['source_begin'])).total_seconds()<=account_journal.policy.max_read_seconds,'w7_coverage_reuse_source_expired')
            if lineage!=known:
                _append_lineage_observation(db,head,lineage,prior_receipt,lineage_sequence,observed,returned)
                committed=instant(clock());require(returned<=committed and (committed-instant(observed['source_begin'])).total_seconds()<=account_journal.policy.max_read_seconds,'w7_coverage_lineage_commit_expired')
                writer_lease.proof()
            return head['receipt']
        record=sealed(dict(schema=RECORD,sequence=seq+1,prior_bootstrap=current,target_bootstrap=target,observed_account_bootstrap=observed,committed_at=end.isoformat(),writer_lease_scope=scope,transport_census=census,transport_lineage=lineage))
        db.execute('CREATE TABLE IF NOT EXISTS w7_bootstrap_coverage_transitions (sequence INTEGER PRIMARY KEY,transition_id TEXT NOT NULL UNIQUE,payload TEXT NOT NULL)')
        db.execute("CREATE TRIGGER IF NOT EXISTS w7_coverage_no_update BEFORE UPDATE ON w7_bootstrap_coverage_transitions BEGIN SELECT RAISE(ABORT,'w7_coverage_history_append_only'); END")
        db.execute("CREATE TRIGGER IF NOT EXISTS w7_coverage_no_delete BEFORE DELETE ON w7_bootstrap_coverage_transitions BEGIN SELECT RAISE(ABORT,'w7_coverage_history_append_only'); END")
        db.execute('INSERT INTO w7_bootstrap_coverage_transitions VALUES(?,?,?)',(seq+1,a['transition_id'],canonical(record)))
        committed=instant(clock());require(end<=committed<instant(a['valid_until']) and (committed-instant(observed['source_begin'])).total_seconds()<=account_journal.policy.max_read_seconds,'w7_coverage_commit_expired');writer_lease.proof()
        require(db.execute("SELECT payload FROM required_policy WHERE key='bootstrap'").fetchone()[0]==saved[0],'w7_coverage_original_bootstrap_changed')
        return record['receipt']

"""Fixed invented155 exercise. No MT5, native helper or clock acquisition."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import uuid

from . import recorder_boundary_155 as r
from .acquisition_lifecycle_138 import AccountMode,Checks,Lifecycle,Policy
from .segment_journal_138 import DiskStore,Journal,StorageFailure,MAX_JOB
from .supervision_140 import Supervisor,SyntheticHelper,Ledger,Observation,MAX_STATUS_AGE_US,MAX_FRAME,MAX_FRAMES
from .helper_health_142 import HealthDecoder
from .paired_replay_133 import DENIED,canonical

ROOT=Path(__file__).resolve().parents[2]
SCENARIOS=('default_off','clean_repeats','post_guard_loss','stale_final','retry_boundary',
           'source_failure','orphan_commit','rotation','health_protocol')
GOOD=Checks(actual_mode=AccountMode.DEMO,query_ok=True,identity_unchanged=True,connected=True,
            non_tester=True,eurusd_visible=True,currency_usd=True,clock_safe=True)


def bindings():
    names=('src/forex_demo_lab/recorder_boundary_155.py','src/forex_demo_lab/recorder_fixture_155.py',
           'scripts/recorder-boundary-155.py','tests/test_recorder_boundary_155.py',
           'src/forex_demo_lab/acquisition_lifecycle_138.py','src/forex_demo_lab/segment_journal_138.py',
           'src/forex_demo_lab/supervision_140.py','src/forex_demo_lab/helper_health_142.py',
           'src/forex_demo_lab/native_supervision_143.py','src/forex_demo_lab/paired_replay_133.py')
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}


def exercise(output):
    root=Path(output);root.mkdir(parents=True,exist_ok=False);sources=bindings()
    def write(path,value):
        with path.open('x') as file:json.dump(value,file,indent=2);file.write('\n')
    write(root/'declaration.json',dict(schema='invented_recorder155_exercise_declaration',scenarios=list(SCENARIOS),
                                     sources=sources,native_helper_launched=False,collection_dates=None,**DENIED))
    cases=[]
    for name in SCENARIOS:
        folder=root/name;folder.mkdir();job=uuid.uuid4().hex;enabled=name!='default_off'
        life=Lifecycle(Journal(job,lambda token:DiskStore(folder,token),file_limit=20*1024 if name=='rotation' else 32*1024*1024,
                               job_limit=MAX_JOB-r.MAX_BYTES-MAX_FRAME*MAX_FRAMES),
                       Policy(enabled=enabled,retry_enabled=name=='retry_boundary',max_elapsed_us=60_000_000))
        supervisor=Supervisor(life,SyntheticHelper(),Ledger(folder,job),enabled=enabled)
        journal=r.PayloadJournal(folder,job);recorder=r.Recorder(supervisor,journal,enabled=enabled)
        decoder=HealthDecoder(job);sample=0;ports=[]
        def snapshot(at,checks=GOOD):
            nonlocal sample
            if name=='health_protocol':
                sample+=1;challenge=uuid.uuid4().hex
                wire=dict(schema='native_health142_status_v1',token=job,challenge=challenge,operation='POLL',contained=True,
                          running=True,sample_valid=True,sample_sequence=sample,sample_tick_ms=at//1000,owner_tick_ms=at//1000,
                          create_ack=True,set_ack=True,ready_signal=True,mains=True,helper_running_marker=True,cancel_ack=False)
                return r.decoded_snapshot(decoder,canonical(wire),challenge,at,at,checks)
            return r.Snapshot(at,checks,Observation(job,at,create_ack=True,set_ack=True,ready_signal=True))
        def context(at):
            port=r.InventedSource([r.Read('context',snapshot(at),snapshot(at+1),dict(epoch=1,digits=5,contract_units=100000,cost_state='unknown'))])
            ports.append(port);return port,snapshot(at+2)
        def triple(at,label=10):
            port=r.InventedSource([r.Read('clock_before',snapshot(at),snapshot(at+1),at),
                    r.Read('quote',snapshot(at+2),snapshot(at+3),dict(source_label=label,bid_points=110000,ask_points=110010,flags=6)),
                    r.Read('clock_after',snapshot(at+4),snapshot(at+5),at+5)])
            ports.append(port);return port,snapshot(at+6)
        try:
            started=recorder.start(snapshot(0))
            if enabled:
                if not started or not recorder.context(*context(1)):raise AssertionError('invented155_start')
                port,final=triple(2_000_000 if name=='stale_final' else 10)
                if name=='post_guard_loss':
                    reads=list(port.reads);item=reads[1]
                    reads[1]=replace(item,after=replace(item.after,checks=replace(GOOD,identity_unchanged=False)))
                    port=r.InventedSource(reads);ports.append(port)
                elif name=='stale_final':final=replace(final,health=replace(final.health,observed_us=final.at_us-MAX_STATUS_AGE_US-1))
                elif name=='retry_boundary':final=replace(final,checks=replace(GOOD,connected=False))
                elif name=='source_failure':port.fail_query=2
                elif name=='orphan_commit':
                    original=journal.append
                    def fail(event,*args,**kwargs):
                        if event=='commit':raise StorageFailure('invented155_ack_failure')
                        return original(event,*args,**kwargs)
                    journal.append=fail
                result=recorder.poll(port,final)
                if name=='retry_boundary':
                    due=life.wait_until
                    if not recorder.retry(snapshot(due)) or not recorder.context(*context(due+10)):raise AssertionError('invented155_retry')
                    port,final=triple(due+20);result=recorder.poll(port,final)
                elif name=='clean_repeats':
                    for i,label in enumerate((10,9),1):
                        port,final=triple(10+i*1_000_000,label);result=recorder.poll(port,final)
                elif name=='rotation':
                    for i in range(1,30):
                        at=10+i*1_000_000;old=life.journal.segment;port,final=triple(at)
                        result=recorder.poll(port,final)
                        if life.journal.segment>old:
                            if result or not recorder.context(*context(at+10)):raise AssertionError('invented155_rotation')
                            port,final=triple(at+20);result=recorder.poll(port,final);break
                recorder.stop(snapshot(max(final.at_us,supervisor.last)+1))
            segments=[path.read_bytes() for path in sorted((folder/('InventedJob138-'+job)).glob('*.journal'))]
            audit=(r.inspect(journal.path.read_bytes(),segments,supervisor.ledger.path.read_bytes()) if journal.path.exists() else None)
            case=dict(name=name,status=recorder.snapshot(),source_queries=sum(p.queries for p in ports),inspection=audit)
            cases.append(case);write(folder/'result.json',case)
        finally:
            journal.poison();life.journal.poison();supervisor.ledger.poison()
    if bindings()!=sources:raise ValueError('recorder155_exercise_sources_changed')
    report=dict(schema='invented_recorder155_exercise',cases=cases,sources=sources,invented_only=True,
                native_helper_launched=False,actual_account_queried=False,actual_quotes_read=False,collection_dates=None,**DENIED)
    write(root/'exercise.json',report)
    return report

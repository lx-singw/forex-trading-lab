"""Fixed invented159 replay exercises; no native launch or market-source option."""
import argparse
from dataclasses import replace
import json
from pathlib import Path

from .acquisition_lifecycle_138 import Checks,AccountMode
from .supervision_140 import Observation
from .recorder_boundary_155 import Snapshot
from .recorder_fixture_157 import Clock,Producer,Channel
from .recorder_startup_158 import Runner
from .diagnostic_bridge_159 import Bridge
from .diagnostic_audit_159 import inspect


def snapshot(at,job):
    checks=Checks(actual_mode=AccountMode.DEMO,query_ok=True,identity_unchanged=True,connected=True,non_tester=True,eurusd_visible=True,currency_usd=True,clock_safe=True)
    return Snapshot(at,checks,Observation(job,at,create_ack=True,set_ack=True,ready_signal=True))


def make_source(root,job,failed=False):
    folder=Path(root)/('Job156-'+job);clock=Clock();Producer(folder,job,clock,failed=failed)
    status=Runner(folder,job,Channel(clock),enabled=True,clock=clock.read,wait=clock.wait).run()
    if status['cause']!='complete':raise ValueError('fixture159_source')
    return folder


def sync_fault(journal,event):
    original=journal.sync
    def fail():
        row=json.loads(journal.path.read_bytes().splitlines()[-1].rsplit(b'\t',1)[0])
        if row['event']==event:raise OSError('invented missing acknowledgement')
        original()
    journal.sync=fail


def life_commit_fault(bridge):
    store=bridge.life.journal.store;original=store.sync
    def fail(stream):
        stream.flush()
        row=json.loads((store.folder/'Segment0001.journal').read_bytes().splitlines()[-1].rsplit(b'\t',1)[0])
        if row['event']=='triple_commit':raise OSError('invented missing lifecycle acknowledgement')
        original(stream)
    store.sync=fail


def abandon(bridge):
    # Test-only process-crash approximation: retain bytes without stop/receipt.
    bridge.journal.poison();bridge.life.journal.poison();bridge.supervisor.ledger.poison()


def run_case(root,case,source,source_job,replay_job):
    bridge=Bridge(Path(root)/'Replay159',replay_job,enabled=True)
    snap=lambda at:snapshot(at,replay_job)
    if not bridge.start(source,source_job,snap(0)):raise ValueError('fixture159_start')
    if not bridge.context(snap(10),snap(11)):raise ValueError('fixture159_context')
    if not bridge.begin(snap(20)):raise ValueError('fixture159_begin')
    if case=='abort_begin':bridge.abort(snap(21))
    else:
        if not bridge.prepare(snap(21)):raise ValueError('fixture159_prepare')
        if case=='abort_prepare':bridge.abort(snap(22))
        elif case=='crash_prepared':abandon(bridge)
        else:
            final=snap(22)
            if case=='guard_loss':final=replace(final,checks=replace(final.checks,actual_mode=AccountMode.CONTEST))
            if case=='stale':final=replace(final,at_us=1_000_022,health=replace(final.health,observed_us=21))
            if case=='binding_ack_unknown':sync_fault(bridge.journal,'commit')
            if case=='life_ack_unknown':life_commit_fault(bridge)
            committed=bridge.commit(final)
            if committed:
                if case=='crash_committed':abandon(bridge)
                elif not bridge.finish(snap(30)):raise ValueError('fixture159_finish')
            elif case in ('clean','failed_metadata','crash_committed'):raise ValueError('fixture159_commit')
    checked=inspect(bridge.output,source)
    expected=1 if case in ('clean','failed_metadata') else 0
    if checked['published_diagnostic_triples']!=expected:raise ValueError('fixture159_publication')
    return dict(case=case,status=bridge.snapshot(),independent=checked)


def exercise(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    cases=('clean','failed_metadata','abort_begin','abort_prepare','guard_loss','stale','binding_ack_unknown','life_ack_unknown','crash_prepared','crash_committed')
    (output/'declaration.json').write_text(json.dumps(dict(cases=cases,inputs='invented_only',replay_clock_separate=True,native_launch=False,market_eligible=False),indent=2)+'\n')
    results=[]
    for index,case in enumerate(cases,1):
        root=output/case;root.mkdir();job=f'{2000+index:032x}';source=make_source(root,job,case=='failed_metadata')
        results.append(run_case(root,case,source,job,f'{3000+index:032x}'))
    value=dict(schema='invented_bridge159_exercise_v1',cases=results,native_launch=False,market_eligible=False)
    (output/'summary.json').write_text(json.dumps(value,indent=2)+'\n');return value


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--exercise-invented',action='store_true');parser.add_argument('--output',type=Path);args=parser.parse_args(argv)
    if not args.exercise_invented:print(json.dumps(dict(enabled=False,native_launch=False,market_eligible=False)));return 0
    if args.output is None:parser.error('a new output directory is required')
    result=exercise(args.output);print(json.dumps(dict(cases=len(result['cases']),inputs='invented_only',native_launch=False)));return 0

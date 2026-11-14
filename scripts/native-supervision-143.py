"""Explicit brief helper-only tests with invented acquisition; no collection mode."""
import argparse
import json
from pathlib import Path
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from forex_demo_lab.acquisition_lifecycle_138 import AccountMode,Checks,Lifecycle,Policy
from forex_demo_lab.native_supervision_143 import NativePort,NativeSupervisor,WindowsChannel,now_us
from forex_demo_lab.paired_replay_133 import canonical,DENIED
from forex_demo_lab.segment_journal_138 import DiskStore,Journal,inspect_segments
from forex_demo_lab.supervision_140 import Cause,Ledger,inspect_ledger


class TestChannel(WindowsChannel):
    """Faults affect returned health packets only; native power state stays untouched."""
    def __init__(self,build):
        super().__init__(build);self.mode='good';self.last_sample=None;self.injected=[]
    def request(self,operation,challenge):
        raw=super().request(operation,challenge)
        if operation!='POLL':return raw
        value=json.loads(raw)
        if self.mode=='hold' and self.last_sample is not None:
            for key in ('sample_valid','sample_sequence','sample_tick_ms','create_ack','set_ack','ready_signal','mains','helper_running_marker'):
                value[key]=self.last_sample[key]
            self.injected.append(dict(kind='held_status_sample',packet=value.copy()))
            return canonical(value)
        if self.mode=='contradict':
            value.update(create_ack=False,ready_signal=True)
            self.injected.append(dict(kind='contradictory_status',packet=value.copy()))
            return canonical(value)
        self.last_sample=value
        return raw


def require(value):
    if not value:raise RuntimeError('native143_check_failed')


def run(build,root):
    root.mkdir(parents=False,exist_ok=False)
    # These are deliberately invented guard results. No broker/account call occurs.
    good=Checks(actual_mode=AccountMode.DEMO,query_ok=True,identity_unchanged=True,connected=True,
                non_tester=True,eurusd_visible=True,currency_usd=True,clock_safe=True)
    outcomes=[]
    for name,expected in [('clean_stream',Cause.CANCEL),('held_status',Cause.STALE),('contradictory_status',Cause.PROTOCOL)]:
        folder=root/name;folder.mkdir();job=uuid.uuid4().hex
        journal=Journal(job,lambda basename:DiskStore(folder,basename))
        life=Lifecycle(journal,Policy(enabled=True,max_elapsed_us=15_000_000))
        channel=TestChannel(build);port=NativePort(channel);s=NativeSupervisor(life,port,Ledger(folder,job),enabled=True)
        try:
            require(s.start(now_us(),good));limit=time.monotonic()+3
            while not s.observe(now_us(),good):
                require(s.state!='stopped' and time.monotonic()<limit);time.sleep(.02)
            mark=now_us();require(s.record_context(mark,mark,good,good));require(s.begin_triple(now_us(),good))
            if name=='clean_stream':
                require(s.finish_triple(now_us(),good))
                while port.packets<8:
                    require(time.monotonic()<limit and s.observe(now_us(),good));time.sleep(.02)
                s.stop(now_us(),good)
            else:
                channel.mode='hold' if name=='held_status' else 'contradict'
                while s.state!='stopped':
                    require(time.monotonic()<limit);s.observe(now_us(),good);time.sleep(.02)
            require(s.cause==expected and life.journal.committed==(1 if name=='clean_stream' else 0))
            require(life.pending is None and s.snapshot()['cleanup_complete'])
        finally:
            if s.state not in ('off','stopped'):s.stop(now_us(),good)
            port.cancel();require(port.confirm_exit())
        segments=[p.read_bytes() for p in sorted((folder/('InventedJob138-'+job)).glob('*.journal'))]
        inspection=inspect_ledger(s.ledger.path.read_bytes(),segments)
        life_read=inspect_segments(segments)
        require(inspection['lifecycle_acknowledged_prefix_bound'] and not life_read['pending_triple'])
        transcript=dict(native=channel.transcript,health_decoding=port.health_evidence,injected_test_packets=channel.injected)
        (folder/'transport.json').write_text(json.dumps(transcript,indent=2,sort_keys=True)+'\n')
        outcomes.append(dict(name=name,passed=True,status=s.snapshot(),supervision_inspection=inspection,lifecycle_inspection=life_read,
                             owner_exit_observed=channel.owner_exit_observed,fault_injection=channel.mode!='good'))
    report=dict(schema='native_supervision143_checks_v1',passed=True,scenarios=outcomes,
                native_helper_only=True,acquisition_events_invented_only=True,actual_account_queries=0,actual_quotes=0,actual_orders=0,
                new_collection_dates=None,owned_owner_processes_remaining=0,**DENIED)
    (root/'results.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enable-native-helper-tests',action='store_true')
    parser.add_argument('--build',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if not args.enable_native_helper_tests:
        print(json.dumps(dict(schema='native_supervision143_off_v1',enabled=False,**DENIED)));return 0
    if args.build is None or args.output is None:parser.error('explicit build and new output directory required')
    try:
        report=run(json.loads(args.build.read_text(encoding='utf-8-sig')),args.output)
    except (OSError,ValueError,RuntimeError):
        print('Native helper-only exercise failed; no market collection was enabled.',file=sys.stderr);return 2
    print(json.dumps(dict(passed=report['passed'],scenarios=len(report['scenarios']),actual_quotes=0,actual_orders=0)))
    return 0


if __name__=='__main__':raise SystemExit(main())

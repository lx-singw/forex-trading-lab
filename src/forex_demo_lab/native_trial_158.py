"""Explicit brief native-helper trials. Every price/context file is invented."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

from .native_supervision_143 import WindowsChannel, local_windows_path
from .recorder_fixture_157 import Producer
from .recorder_startup_158 import Runner
from .relay_audit_158 import inspect_job
from .native_journal_157 import require

ROOT=Path(__file__).resolve().parents[2]
PINS={'owner':'b2d4356cf558678698c0301df6526eab3838fd4b1cab84d6031e2229362cc8df',
      'helper':'0e7e085c8b9038dc41af855bbd154d098bb6834f61d68603ec02b9aeda21e6a8'}
SOURCES={'src/windows/KeepAwake139.cs':'ae75518c62ade82b2e668c58a1e0dea4e2a3a7bb1775cbcf47ae428e7b6f7a81',
         'src/windows/HelperOwner141.cs':'6c156d0449f19204946c1f1a305ab4a347efc2e3047a402e616785a4640aeb8c',
         'src/windows/HelperHealth142.cs':'f0ca31be10c8d80be30cc040917a267fe3f7e07165b4c1ade9c5229880c8a308'}


def save(path,value):
    with Path(path).open('x',encoding='utf-8') as file:json.dump(value,file,indent=2);file.write('\n')


def validate_build(build):
    require(type(build) is dict and build.get('schema')=='health142_build_v1')
    for kind in ('owner','helper'):
        require(build.get(kind+'_sha256')==PINS[kind])
        name='ForexDemoHealth'+('Owner' if kind=='owner' else 'Helper')+'142.exe'
        path=local_windows_path(build[kind+'_path'],name)
        require(hashlib.sha256(path.read_bytes()).hexdigest()==PINS[kind])
    for name,value in SOURCES.items():require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value)


def snapshot():
    # Read-only, static command text. No execution-policy or power-configuration writes.
    command=r"""
$ErrorActionPreference='Stop'
function HashPower([string[]]$items) {
    $value=(& powercfg @items | Out-String)
    if ($LASTEXITCODE -ne 0) { throw 'Power query failed' }
    $sha=[System.Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($value)))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
@{schema='relay158_host_v1';active=HashPower @('/getactivescheme');sleep=HashPower @('/q','SCHEME_CURRENT','SUB_SLEEP');display=HashPower @('/q','SCHEME_CURRENT','SUB_VIDEO');owner_count=@(Get-Process -Name ForexDemoHealthOwner142 -ErrorAction SilentlyContinue).Count;helper_count=@(Get-Process -Name ForexDemoHealthHelper142 -ErrorAction SilentlyContinue).Count} | ConvertTo-Json -Compress
"""
    process=subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-NonInteractive','-Command',command],capture_output=True,timeout=15,check=True)
    require(len(process.stdout)<=65536);value=json.loads(process.stdout)
    require(set(value)=={'schema','active','sleep','display','owner_count','helper_count'} and value['schema']=='relay158_host_v1')
    for key in ('active','sleep','display'):require(type(value[key]) is str and len(value[key])==64 and all(c in '0123456789abcdef' for c in value[key]))
    for key in ('owner_count','helper_count'):require(type(value[key]) is int and value[key]>=0)
    return value


def quiet(value):return value['owner_count']==0 and value['helper_count']==0
def same_power(a,b):return all(a[k]==b[k] for k in ('active','sleep','display'))


class Clock:
    """Synthetic program counter, paced by real elapsed time, not a Windows epoch."""
    def __init__(self):self.origin=time.monotonic_ns()//1000;self.producer=None
    @property
    def value(self):return 6_900_000+time.monotonic_ns()//1000-self.origin
    def wait(self,seconds):
        time.sleep(max(seconds,.01))
        if self.producer is not None:self.producer.step()


class Channel(WindowsChannel):
    def __init__(self,build,mode):
        require(mode in ('clean','held','contradictory','eof'))
        super().__init__(build);self.mode=mode;self.good_polls=0;self.held=None;self.injected=[]
    def request(self,operation,challenge):
        if operation=='POLL' and self.mode=='held' and self.held is not None:time.sleep(.12)
        raw=super().request(operation,challenge)
        if operation!='POLL':return raw
        value=json.loads(raw)
        healthy=all(value.get(k) is True for k in ('contained','running','sample_valid','mains','create_ack','set_ack','ready_signal','helper_running_marker'))
        if not healthy:return raw # Never conceal an actual native failure with a test packet.
        self.good_polls+=1
        if self.good_polls<5:return raw
        if self.mode=='held':
            if self.held is None:self.held=dict(value)
            for key in ('sample_sequence','sample_tick_ms','create_ack','set_ack','ready_signal','mains','helper_running_marker'):value[key]=self.held[key]
            self.injected.append(dict(kind='held_sample',poll=self.good_polls))
            return json.dumps(value,separators=(',',':')).encode('ascii')
        if self.mode=='contradictory':
            value.update(create_ack=False,ready_signal=True);self.injected.append(dict(kind='contradictory_status',poll=self.good_polls))
            return json.dumps(value,separators=(',',':')).encode('ascii')
        if self.mode=='eof':
            self.process.stdin.close();self.injected.append(dict(kind='actual_owner_input_eof',poll=self.good_polls))
        return raw


def metrics(runner,folder,channel):
    responses=[r for r in runner.responses if r['received_us'] is not None]
    native=[json.loads(e['packet']) for e in channel.transcript if e['operation']=='POLL']
    valid=[p for p in native if p['sample_valid']]
    native_file=(folder/'NativePort156.txt').read_bytes()
    leases=[line.split(b'\t') for line in native_file.splitlines() if line.startswith(b'J\t')]
    return dict(measured_service_round_trip_max_us=max((r['received_us']-r['sent_us'] for r in responses),default=0),
                native_sample_age_max_ms=max((p['owner_tick_ms']-p['sample_tick_ms'] for p in valid),default=0),
                distinct_native_samples=len({p['sample_sequence'] for p in valid}),native_poll_packets=len(native),
                first_invented_lease_round_trip_us=(int(leases[0][4])-int(leases[0][3])) if leases else None,
                owner_exit_observed=channel.owner_exit_observed)


def run(build,output,*,enabled=False):
    if not enabled:return dict(schema='native158_off_v1',enabled=False,actual_quotes=0,actual_orders=0)
    validate_build(build);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    cases=('clean','held','contradictory','eof')
    bindings=json.loads((ROOT/'docs/evidence/recorder-relay-157/source-sha256.json').read_text())
    for name in ('src/forex_demo_lab/recorder_startup_158.py','src/forex_demo_lab/relay_audit_158.py','src/forex_demo_lab/native_trial_158.py','scripts/recorder-native-158.py','scripts/check-native-journal-158.py','tests/test_recorder_native_158.py','docs/RECORDER-NATIVE-158-PLAN.md'):
        bindings[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    bindings.update(SOURCES)
    save(output/'declaration.json',dict(cases=cases,active_budget_us=15_000_000,inputs='invented_only',native_helper=True,actual_quotes=0,actual_orders=0,mt5_started=False,binary_sha256=PINS))
    save(output/'source-sha256.json',bindings)
    results=[]
    for case in cases:
        require(all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in bindings.items()))
        before=snapshot();save(output/(case+'-before.json'),before);require(quiet(before))
        clock=Clock();job=uuid.uuid4().hex;folder=output/case/('Job156-'+job);Producer(folder,job,clock)
        channel=Channel(build,case);runner=Runner(folder,job,channel,enabled=True,wait=clock.wait,budget_us=15_000_000)
        started=time.monotonic();status=runner.run();elapsed=time.monotonic()-started
        # Frozen157 orchestration always attempts cleanup. Save evidence before assertions.
        save(output/(case+'-transport.json'),dict(native=channel.transcript,injected=channel.injected))
        after=snapshot();save(output/(case+'-after.json'),after)
        checker=subprocess.run([sys.executable,str(ROOT/'scripts/check-native-journal-158.py'),'--folder',str(folder),'--job',job],capture_output=True,text=True,timeout=15)
        observation=json.loads(checker.stdout)
        result=dict(case=case,status=status,elapsed_seconds=round(elapsed,4),independent_exit_code=checker.returncode,independent=observation,
                    metrics=metrics(runner,folder,channel),power_unchanged=same_power(before,after),zero_processes_after=quiet(after),injections=len(channel.injected))
        results.append(result);save(output/(case+'-result.json'),result)
        require(quiet(after) and same_power(before,after) and channel.owner_exit_observed)
        require(status['cause']==('complete' if case=='clean' else 'fault') and status['receipt_acknowledged'])
        require((checker.returncode==0)==(case=='clean'))
        require(status['cleanup_complete']==(case!='eof'))
        if case=='clean':require(status['published']==107 and result['metrics']['distinct_native_samples']>=2)
        else:require(not status['writer_complete'] and channel.injected)
    require(all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in bindings.items()))
    report=dict(schema='native158_trial_v1',passed=True,cases=results,sources_unchanged=True,native_helper_only=True,actual_account_queries=0,
                actual_quotes=0,actual_orders=0,new_collection_dates=None,market_eligible=False)
    save(output/'results.json',report);return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--enable-native-helper-trial',action='store_true');parser.add_argument('--build',type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    if not args.enable_native_helper_trial:print(json.dumps(run(None,None)));return 0
    if args.build is None or args.output is None:parser.error('explicit pinned build and new output directory required')
    try:report=run(json.loads(args.build.read_text(encoding='utf-8-sig')),args.output,enabled=True)
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError):
        print(json.dumps(dict(error='native158_trial_failed',actual_quotes=0,actual_orders=0)),file=sys.stderr);return 2
    print(json.dumps(dict(passed=report['passed'],cases=len(report['cases']),actual_quotes=0,actual_orders=0)));return 0

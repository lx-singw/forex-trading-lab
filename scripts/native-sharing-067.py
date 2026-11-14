"""Declare/check/seal one066 interactive runtime under the frozen067 policy.

Does not start SDK/MT5, deploy or run scripts. The separately reviewed066
entry point alone performs native work after this declaration and user guidance.
"""
import argparse
import json
from pathlib import Path
import runpy
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/native-sharing-066.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE=API['HANDOFF'],API['ARCHIVE']
PRIOR=ROOT/'reports/native-sharing-066-final-source.json'
LEDGER=ROOT/'reports/native-sharing-067-ledger.json'
AUTH=ROOT/'reports/native-sharing-067-authorization.json'
POLICY=ROOT/'docs/NATIVE-SHARING-067-POLICY.md'
RUNTIME=ROOT/'reports/native-sharing-066-runtime.json'
RESERVATION=ROOT/'reports/native-sharing-066-runtime-reservation.json'


def prepare():
    from datetime import datetime,timezone
    assert datetime.now(timezone.utc).date().isoformat()=='2026-10-07'
    assert sha(PRIOR)=='66625a6edd8bcf06a738bf20833a86d67a61ac732c269bc052521c8bab984f93'
    p=sealed(PRIOR);review=sealed(ROOT/'reports/native-sharing-066-completion-review.json')
    assert review['review_passed'] and review['final_source_sha256']==sha(PRIOR)
    assert review['frozen_input_coverage_complete'] and review['tests_passed']==1128
    assert review['bindings_verified']==2115 and review['archive_members_verified']==1958
    assert review['next_policy_sha256']==sha(POLICY) and not review['next_policy_executed']
    b=dict(p['source_and_evidence_bindings'])
    for n,h in b.items():assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==1958
    API['verify']()
    for n in HANDOFF:b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),
            ROOT/'reports/native-sharing-066-completion-review.json',
            ROOT/'reports/native-sharing-066-completion-review.sha256',Path(__file__)):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    assert not RESERVATION.exists() and not RUNTIME.exists() and not AUTH.exists()
    write(LEDGER,dict(bindings=b,preparation_sha256=sha(PRIOR),policy_sha256=sha(POLICY),
        prior_bindings_verified=2115,prior_archive_members_verified=1958,tests_retained=1128,
        runtime_phase='66000000000000000000000000000001',declared_date='2026-10-07',
        maximum_native_sessions=1,maximum_sdk_connections=1,maximum_manual_launches=2,
        maximum_saved_log_reads=1,maximum_saved_log_bytes=65536,maximum_session_seconds=900,
        maximum_market_reads=0,maximum_orders=0,maximum_receipt_permissions=0,
        orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    write(AUTH,dict(version='sharing_native_067_v1',preparation_sha256=sha(PRIOR),
        policy_sha256=sha(POLICY),phase='66000000000000000000000000000001',date='2026-10-07',
        maximum_sdk_connections=1,maximum_launches=2,maximum_log_reads=1,maximum_log_bytes=65536,
        maximum_market_reads=0,maximum_orders=0,maximum_receipt_permissions=0))
    print(json.dumps(dict(prepared=True,bindings=len(b),tests_retained=1128,maximum_native_sessions=1)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    assert l['preparation_sha256']==sha(PRIOR) and l['policy_sha256']==sha(POLICY)
    return l


def check():
    l=verify();r=sealed(RUNTIME);reservation=sealed(RESERVATION)
    assert r['preparation_sha256']==reservation['bindings']['preparation']==sha(PRIOR)
    assert r['policy_sha256']==reservation['bindings']['policy']==sha(POLICY)
    assert r['phase']==reservation['phase']==l['runtime_phase'] and r['date']==reservation['date']==l['declared_date']
    assert reservation['maximum_launches']==2 and reservation['maximum_sdk_connections']==1
    assert reservation['maximum_log_reads']==1 and reservation['maximum_log_bytes']==65536
    sys_path=str(ROOT/'src')
    import sys
    sys.path.insert(0,sys_path)
    from forex_demo_lab.sharing_runtime_066 import LIMITS066
    assert set(r['counts'])==set(LIMITS066)
    assert all(type(v) is int and 0<=v<=LIMITS066[k] for k,v in r['counts'].items())
    assert all(r[k]==0 for k in ('quote_reads','history_reads','orders','receipt_permissions'))
    assert all(r[k] is False for k in ('native_mql_verified','native_publication_verified','orders_available','fresh_performance_eligible','annual_eligible'))
    assert r['counts']['reservation_writes']==1
    assert r['script_arms'] in ([],['disabled'],['disabled','enabled'])
    assert r['counts']['script_arms']==len(r['script_arms'])
    if r['counts']['sdk_connections']:
        assert r['sdk_shutdown_called'] and r['counts']['sdk_shutdowns']==1
    else:assert not r['sdk_shutdown_called'] and r['counts']['sdk_shutdowns']==0
    cleanup=r['bootstrap_cleanup']
    assert cleanup is not None and cleanup['all_handles_closed'] and cleanup['allocations_released'] and cleanup['unconfirmed_handles']==0
    if r['completed']:
        from forex_demo_lab.mql_sharing_064 import PrivateProof,Probe,match_evidence
        assert r['native_sharing_observed'] and r['native_private_bootstrap_passed'] and r['native_signature_checks_passed']
        assert r['deployment_completed'] and r['counts']['sdk_connections']==1 and len(r['script_arms'])==2
        assert r['counts']['log_reads']==1 and r['cleanup']['all_handles_closed'] and r['cleanup']['allocations_released']
        match_evidence(r['records'],[Probe(**p) for p in r['probes']],PrivateProof(True,True,True,True,True,True,True,True,'2026-10-07'))
    else:assert r['stop_reason'] and not r['native_sharing_observed']
    write(ROOT/'reports/native-sharing-067-checks.json',dict(checker_passed=True,runtime_completed=r['completed'],
        ledger_sha256=sha(LEDGER),authorization_sha256=sha(AUTH),runtime_sha256=sha(RUNTIME),
        reservation_sha256=sha(RESERVATION),sdk_connections=r['counts']['sdk_connections'],
        script_arms=len(r['script_arms']),orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(checker_passed=True,runtime_completed=r['completed'],stop_reason=r['stop_reason'])))


def seal():
    l=verify();c=sealed(ROOT/'reports/native-sharing-067-checks.json');r=sealed(RUNTIME)
    assert c['checker_passed'] and c['runtime_sha256']==sha(RUNTIME) and c['ledger_sha256']==sha(LEDGER)
    text=('# Native sharing067 outcome\n\n'
        f'Completed:{r["completed"]}; stop:{r["stop_reason"]}. One exclusive066 runtime reservation consumed. '
        f'SDK attempts:{r["counts"]["sdk_connections"]}; manual arms:{len(r["script_arms"])}; '
        f'private bootstrap passed:{r["native_private_bootstrap_passed"]}; deployment:{r["deployment_completed"]}. '
        f'Signature checks:{r["native_signature_checks_passed"]}; log reads:{r["counts"]["log_reads"]}; '
        f'bootstrap cleanup:{r["bootstrap_cleanup"]}; SDK shutdown:{r["sdk_shutdown_called"]}. '
        'Zero quotes/history/orders/receipt grants. Failure remains immutable; no reconnect/restart/retry/refund.\n\n'
        '1128 preparation tests retained; no code/suite/compiler rerun. Native outcome and counters are authoritative '
        'only for this attempt; incomplete bootstrap cannot certify actual MQL sharing/publication/ACK or root cause. '
        'Next diagnose the precise stopped stage offline and prepare a fresh bounded experiment if required. '
        'Keep old spent failures,033/035 diagnostics, clock/cost/coverage/flags, consumed2025, reserved Nov–Dec2026 '
        'and provider stops. Fresh/annual performance and orders remain unavailable.\n')
    with (ROOT/'docs/NATIVE-SHARING-067-RESULTS.md').open('x') as f:f.write(text)
    handoff=('Latest — 2026-10-07: native sharing067 outcome sealed; read NATIVE-SHARING-067-RESULTS.md. '
        f'Completed:{r["completed"]}, stop:{r["stop_reason"]}; one consumed066 reservation, '
        f'{r["counts"]["sdk_connections"]} SDK attempts/{len(r["script_arms"])} arms, '
        f'bootstrap:{r["native_private_bootstrap_passed"]}/deployment:{r["deployment_completed"]}; '
        'zero quotes/history/orders/grants. Cleanup and sanitized native evidence checked; no reset/reconnect/retry. '
        '1128 preparation tests retained. Native MQL sharing/publication/ACK/root cause remain unverified unless '
        'separately established by complete evidence. Next offline stopped-stage diagnosis/fresh plan as needed. '
        'Market gates/reserved exclusions retained; fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        path=ROOT/n;s=path.read_text();i=s.index('\n')+1;path.write_text(s[:i]+'\n'+handoff+s[i:]);b[n]=sha(path)
    for pattern in ('scripts/*067.py','docs/*067*.md','reports/native-sharing-067-*.json','reports/native-sharing-067-*.sha256',
            'reports/native-sharing-066-runtime*.json','reports/native-sharing-066-runtime*.sha256'):
        for path in ROOT.glob(pattern):b[path.relative_to(ROOT).as_posix()]=sha(path)
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external};final=ROOT/'reports/native-sharing-067-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),
        runtime_completed=r['completed'],tests_retained=1128,native_sessions=1,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','verify','check','seal'))
    dict(prepare=prepare,verify=lambda:print(len(verify()['bindings'])),check=check,seal=seal)[p.parse_args().action]()

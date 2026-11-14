"""Separate offline audit of failed067; never retries native066 or old checker."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OLD=runpy.run_path(str(ROOT/'scripts/native-sharing-067.py'))
sha,sealed,write,bound=(OLD[k] for k in ('sha','sealed','write','bound'))
ARCHIVE,HANDOFF=OLD['ARCHIVE'],OLD['HANDOFF']
PREFIX='native-sharing-067-r2';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
RUNTIME,RESERVATION=OLD['RUNTIME'],OLD['RESERVATION']
PLAN=ROOT/'docs/NATIVE-SHARING-068-PLAN.md'


def check():
    l=OLD['verify']();failure=sealed(ROOT/'reports/native-sharing-067-checker-failure.json')
    assert not failure['checker_passed'] and failure['reason']=='reservation_sha_sidecar_assumption_failed'
    assert failure['checker_source_sha256']==sha(ROOT/'scripts/native-sharing-067.py')
    assert not RESERVATION.with_suffix('.sha256').exists()
    assert not (ROOT/'reports/native-sharing-067-checks.json').exists()
    b=dict(l['bindings'])
    for path in (OLD['LEDGER'],OLD['AUTH'],RUNTIME,RESERVATION,
            ROOT/'reports/native-sharing-067-checker-failure.json',Path(__file__),PLAN):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    write(LEDGER,dict(bindings=b,maximum_sdk_connections=0,maximum_native_runs=0,
        maximum_external_file_stat_reads=2,maximum_market_reads=0,maximum_orders=0,
        original_checker_failed=True,original_reservation_sidecar_absent=True,
        baseline_log_saved_user_acknowledgment=True))
    r=sealed(RUNTIME);raw=RESERVATION.read_bytes()
    # Reservation066 uses exclusive JSON/fsync, without a SHA sidecar. Audit
    # exact bytes against this NEW pre-read ledger; never manufacture a sidecar.
    assert hashlib.sha256(raw).hexdigest()==b[RESERVATION.relative_to(ROOT).as_posix()]
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.clock_observer_042 import unique_pairs
    reservation=json.loads(raw.decode('ascii'),object_pairs_hook=unique_pairs)
    assert set(reservation)=={'version','phase','mql_phase','date','bindings','maximum_launches',
        'maximum_sdk_connections','maximum_log_reads','maximum_log_bytes','maximum_receipt_permissions','orders_available'}
    assert reservation['version']=='sharing_reservation_066_v1' and reservation['mql_phase']=='64000000000000000000000000000001'
    assert reservation['bindings']['preparation']==r['preparation_sha256']==l['preparation_sha256']
    assert reservation['bindings']['policy']==r['policy_sha256']==l['policy_sha256']
    assert r['phase']==reservation['phase']==l['runtime_phase'] and r['date']==reservation['date']==l['declared_date']
    assert reservation['maximum_launches']==2 and reservation['maximum_sdk_connections']==1
    assert reservation['maximum_log_reads']==1 and reservation['maximum_log_bytes']==65536
    assert reservation['maximum_receipt_permissions']==0 and reservation['orders_available'] is False
    assert set(reservation['bindings'])=={'source','ex5','terminal','editor','preparation','policy'}
    from forex_demo_lab.sharing_runtime_066 import LIMITS066
    assert set(r['counts'])==set(LIMITS066)
    assert all(type(v) is int and 0<=v<=LIMITS066[k] for k,v in r['counts'].items())
    c=r['counts']
    assert (c['reservation_writes'],c['hash_reads'],c['hash_path_stats'],c['hash_bytes'])==(1,1,5,0)
    assert all(c[k]==0 for k in ('native_calls','process_opens','process_snapshots','sdk_connections',
        'sdk_queries','script_arms','log_reads','directories','deployment_directories','deployment_writes','trust_queries'))
    assert all(r[k]==0 for k in ('quote_reads','history_reads','orders','receipt_permissions'))
    assert all(r[k] is False for k in ('completed','native_sharing_observed','native_private_bootstrap_passed',
        'native_signature_checks_passed','deployment_completed','sdk_shutdown_called','native_mql_verified',
        'native_publication_verified','orders_available','fresh_performance_eligible','annual_eligible'))
    assert not r['records'] and not r['probes'] and not r['script_arms'] and r['cleanup'] is None
    cleanup=r['bootstrap_cleanup']
    assert cleanup['all_handles_closed'] and cleanup['allocations_released'] and cleanup['unconfirmed_handles']==0
    sizes={n:bound('/mnt/c/Program Files/MetaTrader 5/'+n).stat().st_size for n in ('terminal64.exe','metaeditor64.exe')}
    assert sizes=={'terminal64.exe':134439504,'metaeditor64.exe':118065376}
    assert sizes['terminal64.exe']>134217728 and sizes['terminal64.exe']-134217728==221776
    assert sha(RESERVATION)==b[RESERVATION.relative_to(ROOT).as_posix()]
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,runtime_completed=False,
        original_checker_failed=True,reservation_exact_bytes_verified=True,reservation_sha_sidecar_added=False,
        ledger_sha256=sha(LEDGER),original_ledger_sha256=sha(OLD['LEDGER']),runtime_sha256=sha(RUNTIME),
        reservation_sha256=sha(RESERVATION),metadata_file_stats=sizes,guard_per_file_cap=134217728,
        terminal_exceeds_guard_cap_by=221776,stop_localized='first_terminal_hash_size_check',
        exact_private_exception_text_unavailable=True,bootstrap_cleanup_verified=True,
        new_native_runs=0,new_sdk_connections=0,new_market_reads=0,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False,next_plan_sha256=sha(PLAN)))
    print(json.dumps(dict(checker_passed=True,runtime_completed=False,terminal_exceeds_guard_cap_by=221776)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    return l


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER) and c['runtime_sha256']==sha(RUNTIME)
    text=('# Native sharing067 outcome and separate revision2 audit\n\n'
        'Actual066 session failed before signature/process/SDK/deployment/MT5 script actions. One exclusive '
        'reservation consumed; guard hash_reads1/path_stats5/hash_bytes0, native calls0, SDK0, arms0, '
        'deploy0/log0/quotes0/history0/orders0/grants0. Backend cleanup completed with no unconfirmed handles. '
        'Never rerun066 or refund this reservation.\n\n'
        'First terminal guard hash rejected at its size check: pinned current terminal134439504 bytes exceeds '
        'the134217728-byte cap by221776; editor118065376 fits. Two separate metadata stat reads confirm '
        'those sizes. Original counter sequence and unchanged source localize this rejection; original private '
        'exception text was deliberately not exported. Actual process/helper image/logon/SDK/MQL remains untested.\n\n'
        'Original067 checker failed because it expected a reservation SHA sidecar. Reservation066 writes '
        'exclusive JSON/fsync without that sidecar. Original failed checker/source retained; separate R2 audit '
        'binds exact existing reservation bytes/hash, verifies runtime/account-free counters, cleanup and source '
        'without fabricating a sidecar or changing original outcome.1128 preparation tests retained; no new '
        'native session/SDK/compiler/deployment/log content/market/order calls during audit.\n\n'
        'Next NATIVE-SHARING-068-PLAN.md: separate bounded image-reader correction and startup diagnostics, '
        'helper-image semantics and meaningful tests before a NEW native phase. No old source/date extension. '
        'Preserve old failures/spent permissions,033/035 diagnostics, historical clock/cost/coverage/flags, '
        'consumed2025/reserved Nov–Dec2026/provider stops. Fresh/annual eligibility/orders remain false.\n')
    with (ROOT/'docs/NATIVE-SHARING-067-RESULTS.md').open('x') as f:f.write(text)
    handoff=('Latest — 2026-10-07: native sharing067 failed and R2 audit sealed; read NATIVE-SHARING-067-RESULTS.md. '
        'One consumed066 reservation; guard stopped first terminal hash size check:134439504 >134217728 by221776 bytes. '
        'Zero native calls/process/SDK/arms/deploy/log/market/orders/grants; bootstrap cleanup verified. '
        'Original checker failed on nonexistent reservation SHA sidecar; source/failure preserved, separate exact-byte R2 audit passes. '
        'No rerun/reset/refund/sidecar fabrication.1128 preparation tests retained. Next068 bounded image-reader fix, '
        'helper-image semantics/startup diagnostics/tests before new native phase, not executed. Actual MQL/private bootstrap '
        'integration/publication/ACK remain unverified. Market gates/reserved exclusions retained; fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        path=ROOT/n;s=path.read_text();i=s.index('\n')+1;path.write_text(s[:i]+'\n'+handoff+s[i:]);b[n]=sha(path)
    for pattern in ('scripts/*067*.py','docs/*067*.md','docs/*068*.md','reports/native-sharing-067-*.json',
        'reports/native-sharing-067-*.sha256','reports/native-sharing-066-runtime*.json'):
        for path in ROOT.glob(pattern):b[path.relative_to(ROOT).as_posix()]=sha(path)
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external};final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),tests_retained=1128,
        runtime_completed=False,original_checker_failed=True,independent_audit_passed=True,native_sessions=1,
        sdk_connections=0,market_reads=0,orders=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);l=sealed(LEDGER)
    b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(final,r)
    assert all(b.get(n)==h for n,h in l['bindings'].items())
    assert r['original_checker_failed'] and r['independent_audit_passed'] and not r['runtime_completed']
    assert not RESERVATION.with_suffix('.sha256').exists() and not (ROOT/'reports/native-sharing-067-checks.json').exists()
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,
        final_source_sha256=sha(final),bindings_verified=len(b),archive_members_verified=members,
        frozen_input_coverage_complete=True,frozen_inputs_verified=len(l['bindings']),tests_retained=1128,
        runtime_completed=False,next_plan_sha256=sha(PLAN),next_plan_executed=False,
        sdk_connections=0,market_reads=0,orders=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,frozen_inputs=len(l['bindings']))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('check','seal','review'))
    dict(check=check,seal=seal,review=review)[p.parse_args().action]()

"""Review source/witness fidelity and preserve the declared next source hour."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import runpy
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/fresh-ticks-032.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']
REVIEW=ROOT/'reports/fresh-ticks-032-review.json'
FINAL=ROOT/'reports/fresh-ticks-032-final-source.json'


def handoff():
    ledger=API['verify']()
    capture=sealed(API['OUTPUT']/'capture.json')
    checks=sealed(ROOT/'reports/fresh-ticks-032-checks.json')
    tests=sealed(ROOT/'reports/fresh-ticks-032-tests.json')
    assert checks['checker_passed'] and checks['diagnostic_passed'] and tests['passed']
    assert checks['rows_checked']==196 and checks['witnesses_matched']==120
    assert checks['distinct_poll_quote_identities']==checks['distinct_original_rows_used_by_witnesses']==67
    text=('Latest — 2026-10-06: full-tick sample032 complete. Read '
        '`FRESH-TICKS-032-RESULTS.md`. One exact61-second raw-label request returned196 '
        'ticks; all120 prior poll witnesses match with no ambiguity. The67 distinct '
        'poll identities use67 rows, leaving129 additional unpolled ticks. One tied '
        'transition, zero exact duplicate transitions, zero row errors; maximum gap '
        '3.121 seconds. Lossless binary/CSV eight-field originals preserved; independent '
        'checker compares1,568 fields and all original counts/gaps/witnesses. Actual '
        'DEMO/USD, Algo Trading off and stable private identity checked around the '
        'single native request/completion; no identity exported. Native call33.5071578s '
        'below60s soft timeout.416 software tests pass (16 new), prior936 bindings/896 '
        'archive members/40 external inputs verified;63 new frozen bindings. Early '
        'checker-before-output preflight failure preserved; unchanged checker then '
        'passes after completion, no additional request. No clock normalization, '
        'completeness/cost/edge certification, strategy returns/selection or orders. '
        'Fresh/annual eligibility remains false; consumed2025/reservedNov–Dec2026 '
        'and provider stops untouched. Next `FRESH-CONTEXT-033-PLAN.md`, exactly one '
        'completed source-hour tick/bar consistency audit, declared not executed. '
        'Earlier entries below are historical.\n\n')
    for name in API['API']['API']['HANDOFF']:
        path=ROOT/name
        old=path.read_text();split=old.index('\n')+1
        path.write_text(old[:split]+'\n'+text+old[split:])
    print(json.dumps(dict(handoff_updated=True,rows=196,witnesses=120,tests=416)))


def review():
    previous=API['prior_verify'](allow_handoff=True)
    ledger=API['verify']()
    checks=sealed(ROOT/'reports/fresh-ticks-032-checks.json')
    tests=sealed(ROOT/'reports/fresh-ticks-032-tests.json')
    capture=sealed(API['OUTPUT']/'capture.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==416 and tests['new_tests']==16
    assert checks['checker_passed'] and checks['diagnostic_passed']
    assert checks['ledger_sha256']==sha(API['LEDGER'])
    assert checks['rows_checked']==capture['audit']['rows']==196
    assert checks['binary_fields_checked']==1568 and checks['witnesses_checked']==checks['witnesses_matched']==120
    assert checks['ambiguous_witnesses']==0
    assert checks['market_requests']==capture['requests']==1
    assert checks['original_audit']==capture['audit'] and not capture['audit']['error_counts']
    assert capture['complete_original_preserved'] and capture['status']=='sample_preserved_and_rows_valid'
    before,after=capture['receipt_before'],capture['receipt_after']
    for value in (before,after):
        assert type(value['utc_ms']) is int and type(value['monotonic_ns']) is int
        assert datetime.fromtimestamp(value['utc_ms']/1000,timezone.utc).date().isoformat()==ledger['date']
    assert after['utc_ms']>=before['utc_ms']
    elapsed=after['monotonic_ns']-before['monotonic_ns']
    assert 0<=elapsed==capture['elapsed_ns']<=60000000000
    outputs={}
    for name,expected in checks['original_bindings'].items():
        path=API['OUTPUT']/name
        assert sha(path)==expected,name
        outputs[path.relative_to(ROOT).as_posix()]=expected
    assert sum(p.stat().st_size for p in API['OUTPUT'].iterdir() if p.is_file())<=ledger['maximum_evidence_bytes']
    early=sealed(ROOT/'reports/fresh-ticks-032-check-preflight-failure.json')
    assert early['data_files_examined']==early['additional_api_requests']==0
    assert early['checker_output_written'] is False
    documents=('docs/FRESH-TICKS-032-RESULTS.md','docs/FRESH-CONTEXT-033-PLAN.md','scripts/finalize-fresh-ticks-032.py')
    for name in API['API']['API']['HANDOFF']:
        assert 'FRESH-TICKS-032-RESULTS.md' in (ROOT/name).read_text()
    assert 'not executed' in (ROOT/documents[1]).read_text()
    write(REVIEW,dict(kind='post_original_sample_review_032',passed=True,
        prior_snapshot_verification=previous,input_bindings_verified=len(ledger['bindings']),
        output_bindings=outputs,checks_sha256=sha(ROOT/'reports/fresh-ticks-032-checks.json'),
        documentation_bindings={name:sha(ROOT/name) for name in documents},
        software_tests_passed=416,market_requests=1,rows_checked=196,binary_fields_checked=1568,
        witnesses_matched=120,ambiguous_witnesses=0,receipt_elapsed_ns_independently_reconstructed=elapsed,
        early_checker_failure_preserved=True,diagnostic_passed=True,strategy_replays=0,
        fresh_performance_eligible=False,annual_eligible=False,orders_available=False,
        next_plan=documents[1],next_plan_executed=False))
    print(json.dumps(dict(passed=True,rows=196,witnesses=120,tests=416)))


def snapshot():
    checked=sealed(REVIEW)
    assert checked['passed']
    API['prior_verify'](allow_handoff=True)
    ledger=API['verify']()
    for name,expected in (checked['documentation_bindings']|checked['output_bindings']).items():
        assert sha(ROOT/name)==expected,name
    prior=sealed(API['PRIOR'])
    groups={g:dict(v) for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings'}
    for name in API['API']['API']['HANDOFF']:
        groups['source_bindings'][name]=sha(ROOT/name)
    for pattern in ('docs/*032*.md','docs/FRESH-CONTEXT-033-PLAN.md','scripts/*032*.py',
                    'src/forex_demo_lab/fresh_ticks_032.py','tests/test_fresh_ticks_032.py'):
        for path in ROOT.glob(pattern):groups['source_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for path in ROOT.glob('reports/fresh-ticks-032*'):
        assert 'final-source' not in path.name
        groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for suffix in ('.json','.sha256','.zip'):
        path=API['PRIOR'].with_suffix(suffix)
        groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    groups['full_tick_input_bindings']={}
    for path in API['OUTPUT'].iterdir():
        assert path.is_file()
        groups['full_tick_input_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    already={n:h for values in groups.values() for n,h in values.items()}
    for name,expected in ledger['bindings'].items():
        if name in already:assert already[name]==expected,name
        else:groups['full_tick_input_bindings'][name]=expected
    bindings={n:h for values in groups.values() for n,h in values.items()}
    assert len(bindings)==sum(map(len,groups.values()))
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
              n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    for name,expected in bindings.items():assert sha(ROOT/name)==expected,name
    archive=FINAL.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(internal):z.write(ROOT/name,name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.infolist())==len(internal)
        assert set(z.namelist())==set(internal)
        for name in z.namelist():assert hashlib.sha256(z.read(name)).hexdigest()==internal[name],name
    write(FINAL,dict(kind='post_full_tick_sample_snapshot_032',**groups,
        archive_external_bindings=external,archive_members_verified=len(internal),external_bindings_verified=len(external),
        archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
        snapshot_scope='Sources/reports/small original sample archived; older data/ZIPs/timezone/Windows runtime externally hash-bound and required',
        previous_snapshot=API['PRIOR'].relative_to(ROOT).as_posix(),previous_snapshot_sha256=sha(API['PRIOR']),
        completed_utc=datetime.now(timezone.utc).isoformat(),software_tests_passed=416,
        market_requests=1,rows_checked=196,binary_fields_checked=1568,witnesses_matched=120,
        strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False,
        next_plan=checked['next_plan'],next_plan_executed=False))
    print(json.dumps(dict(bindings=len(bindings),archive_members=len(internal),external_bindings=len(external),manifest_sha256=sha(FINAL))))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('handoff','review','snapshot'))
    {'handoff':handoff,'review':review,'snapshot':snapshot}[parser.parse_args().action]()

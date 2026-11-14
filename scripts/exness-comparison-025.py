"""Freeze and compare five declared hours in cached sources. No network/trades."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import runpy
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from forex_demo_lab.coverage_comparison import HOUR, aggregate, distances, questions
from forex_demo_lab.exness_diagnostics_b import timestamp_ms
from forex_demo_lab.normalization import completed

LEDGER = ROOT / 'reports/exness-comparison-025-ledger.json'
REPORT = ROOT / 'reports/exness-comparison-025-review.json'
LINEAGE = ROOT / 'reports/exness-comparison-025-lineage.csv'
PRIOR = ROOT / 'reports/exness-024-final-source.json'
HANDOFF = {'README.md','docs/CONTEXT.md','docs/PLAN.md','docs/VERIFICATION.md'}
PRIOR_GROUPS = ('source_bindings','report_bindings','synthetic_input_bindings',
                'access_evidence_bindings','market_input_bindings')
WINDOWS = (
    dict(name='march',start='2023-03-26T22:00:00.000Z',end='2023-03-27T01:00:00.000Z',month='202303',exness_month='03'),
    dict(name='july',start='2023-07-14T19:00:00.000Z',end='2023-07-14T21:00:00.000Z',month='202307',exness_month='07'),
)
SOURCES = ('exness','histdata_candidate','broker_conditional','forexite_reference')
CSV_FIELDS = ['window','source','path','member','record','raw_label','event_ms',
              'bid','ask','open','high','low','close']
CODE = ('docs/EXNESS-COMPARISON-025-PLAN.md','docs/EXNESS-COMPARISON-025-PROTOCOL.md',
        'src/forex_demo_lab/coverage_comparison.py','scripts/exness-comparison-025.py',
        'scripts/check-exness-comparison-025.py','tests/test_coverage_comparison.py')


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def write(path,value):
    with path.open('x') as stream:
        json.dump(value,stream,indent=2,sort_keys=True,allow_nan=False)
        stream.write('\n')
    with path.with_suffix('.sha256').open('x') as stream:
        stream.write(digest(path)+'\n')


def milliseconds(text):
    moment=datetime.fromisoformat(text.replace('Z','+00:00'))
    delta=moment-datetime(1970,1,1,tzinfo=timezone.utc)
    return delta.days*86400000+delta.seconds*1000+delta.microseconds//1000


def prior_check(allow_handoff=False):
    assert digest(PRIOR)=='66fb2220214f2f924930bfc2adea8582da87486a8f82d64af732c6afd124fe81'
    assert PRIOR.with_suffix('.sha256').read_text().strip()==digest(PRIOR)
    prior=load(PRIOR)
    bindings={}
    changed={}
    for group in PRIOR_GROUPS:
        for name,sha in prior[group].items():
            current=digest(ROOT/name)
            if current!=sha:
                assert allow_handoff and group=='source_bindings' and name in HANDOFF,name
                changed[name]=dict(previous_sha256=sha,current_sha256=current)
            bindings[name]=sha
    archive_path=PRIOR.with_suffix('.zip')
    assert digest(archive_path)==prior['archive_sha256']
    with zipfile.ZipFile(archive_path) as archive:
        assert len(archive.infolist())==prior['archive_members_verified']
        assert archive.testzip() is None
        for entry in archive.infolist():
            assert hashlib.sha256(archive.read(entry)).hexdigest()==bindings[entry.filename]
    return dict(counts={g:len(prior[g]) for g in PRIOR_GROUPS},
                archive_members_verified=len(bindings),allowed_handoff_changes=changed)


def preflight(allow_handoff=False):
    previous=prior_check(allow_handoff)
    verified=[]
    for name in ('correct-clock-013','normalize-history-015','reference-016','reference-016b',
                 'labels-017','exness-024','exness-024b','recovery-010'):
        runpy.run_path(str(ROOT/f'scripts/{name}.py'))['verify']()
        verified.append(name)
        print('Frozen dependency verified: '+name,flush=True)
    return dict(previous_snapshot=previous,verified_dependencies=verified,network_requests=0)


def input_paths():
    paths=set()
    for month in ('202303','202307'):
        paths.update(f'data/normalization-015/{month}/{name}' for name in
                     ('ticks.csv.gz','inventory.json','provenance.json','seal.json'))
        paths.update(f'data/history-009-raw/{month}/{name}' for name in ('original.zip','download.json'))
    for month in ('03','07'):
        paths.add(f'data/exness-024/Exness_EURUSD_2023_{month}.zip')
        paths.add(f'data/exness-024/exness-2023-{month}-get.json')
    for folder in ('data/correction-013-gaps/2023-03-27','data/recovery-010/chunk-081'):
        paths.update(f'{folder}/{name}' for name in ('ticks.csv.gz','capture.json'))
    paths.update(f'data/reference-016/{name}' for name in
                 ('diagnostic-minute-lineage.csv','diagnostic-minute-lineage.json'))
    for day in ('2023-03-26','2023-03-27','2023-07-14'):
        paths.update(f'data/reference-016/{day}/{name}' for name in ('original.zip','download.json'))
    for prefix in ('correction-013','normalization-015','reference-016','reference-016b','labels-017'):
        paths.add(f'reports/{prefix}-ledger.json')
    for prefix in ('exness-024','exness-024b'):
        paths.update(f'reports/{prefix}-{name}{suffix}' for name in ('ledger','audit','checks')
                     for suffix in ('.json','.sha256'))
    paths.update(('reports/correction-013-gap-probes.json','reports/recovery-010-review.json',
                  'reports/recovery-010-checks.json','reports/recovery-010-chunk-081.json',
                  'reports/normalization-015-review.json','reports/normalization-015-checks.json',
                  'reports/reference-016b-review.json','reports/reference-016b-independent.json',
                  'reports/labels-017-review.json','reports/labels-017-checks.json',
                  'reports/exness-024-final-source.json','reports/exness-024-final-source.sha256',
                  'src/forex_demo_lab/exness_diagnostics_b.py','src/forex_demo_lab/normalization.py',
                  '/usr/share/zoneinfo/Europe/Athens','/usr/share/zoneinfo/Europe/Berlin'))
    return paths


def check_selected_metadata():
    normalization=load(ROOT/'reports/normalization-015-ledger.json')
    for month in ('202303','202307'):
        completed(ROOT/f'data/normalization-015/{month}',normalization['bindings'][month])
    recovery=load(ROOT/'reports/recovery-010-review.json')
    report=load(ROOT/'reports/recovery-010-chunk-081.json')
    binding=next(row for row in recovery['bindings'] if row['folder']=='data/recovery-010/chunk-081')
    assert digest(ROOT/'reports/recovery-010-chunk-081.json')==binding['audit_sha256']
    assert digest(ROOT/'data/recovery-010/chunk-081/capture.json')==binding['capture_sha256']==report['capture_sha256']
    assert digest(ROOT/'data/recovery-010/chunk-081/ticks.csv.gz')==binding['ticks_sha256']==report['data_sha256']
    for folder in ('data/correction-013-gaps/2023-03-27','data/recovery-010/chunk-081'):
        capture=load(ROOT/f'{folder}/capture.json')
        assert capture['account_type']=='demo' and capture['terminal_algo_trading'] is False
        assert capture['symbol']=='EURUSD'
        assert digest(ROOT/f'{folder}/ticks.csv.gz')==capture['data_sha256']
    probes=load(ROOT/'reports/correction-013-gap-probes.json')
    probe=next(row for row in probes['windows'] if row['day']=='2023-03-27')
    assert digest(ROOT/'data/correction-013-gaps/2023-03-27/ticks.csv.gz')==probe['ticks_sha256']
    assert digest(ROOT/'data/correction-013-gaps/2023-03-27/capture.json')==probe['capture_sha256']
    lineage=load(ROOT/'data/reference-016/diagnostic-minute-lineage.json')
    assert digest(ROOT/'data/reference-016/diagnostic-minute-lineage.csv')==lineage['data_sha256']
    assert digest(ROOT/'reports/reference-016b-review.json')==lineage['review_sha256']


def freeze():
    evidence=preflight()
    check_selected_metadata()
    paths=input_paths() | set(CODE)
    write(LEDGER,dict(kind='frozen_fixed_coverage_comparison_025',windows=WINDOWS,
                      sources=SOURCES,bindings={p:digest(ROOT/p) for p in sorted(paths)},
                      preflight=evidence,annual_eligible=False,performance_evaluation_ready=False,
                      orders_available=False))
    print('025 exact windows, sources and inputs frozen',flush=True)


def verify():
    assert digest(LEDGER)==LEDGER.with_suffix('.sha256').read_text().strip()
    ledger=load(LEDGER)
    assert ledger['windows']==list(WINDOWS) and ledger['sources']==list(SOURCES)
    for name,sha in ledger['bindings'].items():
        assert digest(ROOT/name)==sha,name
    check_selected_metadata()
    return ledger


def events(window,source):
    start,end=milliseconds(window['start']),milliseconds(window['end'])
    if source=='exness':
        path=f"data/exness-024/Exness_EURUSD_2023_{window['exness_month']}.zip"
        lower,upper=window['start'].replace('T',' '),window['end'].replace('T',' ')
        with zipfile.ZipFile(ROOT/path) as archive:
            for member in archive.infolist():
                if member.is_dir():continue
                with archive.open(member) as binary:
                    rows=csv.reader(io.TextIOWrapper(binary,encoding='utf-8',newline=''),strict=True)
                    assert next(rows)==['Exness','Symbol','Timestamp','Bid','Ask']
                    for record,row in enumerate(rows,2):
                        assert len(row)==5 and row[:2]==['exness','EURUSD']
                        if lower<=row[2]<upper:
                            yield dict(kind='ticks',path=path,member=member.filename,record=record,
                                       raw_label=row[2],event_ms=timestamp_ms(row[2]),bid=row[3],ask=row[4])
    elif source=='histdata_candidate':
        path=f"data/normalization-015/{window['month']}/ticks.csv.gz"
        provenance=load(ROOT/Path(path).with_name('provenance.json'))
        count=0
        with gzip.open(ROOT/path,'rt',newline='') as stream:
            rows=csv.reader(stream)
            assert next(rows)==['sequence','source_sequence','source_label','candidate_time_msc','bid','ask','volume']
            for sequence,row in enumerate(rows):
                assert len(row)==7 and int(row[0])==sequence
                count+=1
                stamp=int(row[3])
                if start<=stamp<end:
                    yield dict(kind='ticks',path=f"data/history-009-raw/{window['month']}/original.zip",
                               member=provenance['source_member'],record=int(row[1])+1,
                               raw_label=row[2],event_ms=stamp,bid=row[4],ask=row[5])
        assert count==provenance['candidate_rows']
    elif source=='broker_conditional':
        folder='data/correction-013-gaps/2023-03-27' if window['name']=='march' else 'data/recovery-010/chunk-081'
        path=folder+'/ticks.csv.gz'
        count=0
        with gzip.open(ROOT/path,'rt',newline='') as stream:
            rows=csv.reader(stream)
            assert next(rows)==['sequence','time_msc','bid','ask','flags']
            for sequence,row in enumerate(rows):
                assert len(row)==5 and int(row[0])==sequence
                count+=1
                stamp=int(row[1])-3*HOUR
                if start<=stamp<end:
                    yield dict(kind='ticks',path=path,member=None,record=sequence+2,
                               raw_label=row[1],event_ms=stamp,bid=row[2],ask=row[3])
        assert count==load(ROOT/f'{folder}/capture.json')['ticks']
    elif source=='forexite_reference':
        path=ROOT/'data/reference-016/diagnostic-minute-lineage.csv'
        with path.open(newline='') as stream:
            for row in csv.DictReader(stream):
                stamp=int(row['reference_time_msc'])
                if start<=stamp<end:
                    day=row['source_day']
                    yield dict(kind='reference',path=f'data/reference-016/{day}/original.zip',
                               member=datetime.fromisoformat(day).strftime('%d%m%y.txt'),
                               record=int(row['source_row']),raw_label=row['source_date']+' '+row['source_time'],
                               event_ms=stamp,**{key:row[key] for key in ('open','high','low','close')})
    else:
        raise ValueError('Undeclared source')


def availability(window,source):
    start,end=milliseconds(window['start']),milliseconds(window['end'])
    if source!='broker_conditional':return start,end
    folder='data/correction-013-gaps/2023-03-27' if window['name']=='march' else 'data/recovery-010/chunk-081'
    capture=load(ROOT/f'{folder}/capture.json')
    return (milliseconds(capture['source_label_start'])-3*HOUR,
            milliseconds(capture['source_label_end_exclusive'])-3*HOUR)


def inventory_check(window,summary):
    inventory=load(ROOT/f"data/normalization-015/{window['month']}/inventory.json")
    indexed={row['hour_start_ms']:row for row in inventory['hourly']}
    from decimal import Decimal
    for hour in summary['hours']:
        original=indexed.get(hour['start_ms'])
        if original is None:
            assert hour['records']==0
        else:
            assert hour['records']==original['ticks']
            for field in ('first_ms','last_ms'):
                assert hour[field]==original[field]
            for side in ('bid','ask'):
                for key in ('open','high','low','close'):
                    assert Decimal(hour[f'{side}_{key}'])==Decimal(str(original[f'{side}_{key}']))


def run():
    verify()
    output_windows=[]
    with LINEAGE.open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=CSV_FIELDS)
        writer.writeheader()
        for window in WINDOWS:
            start,end=milliseconds(window['start']),milliseconds(window['end'])
            summaries={}
            for source in SOURCES:
                def save(event):
                    writer.writerow({'window':window['name'],'source':source,
                                     **{key:event.get(key,'') for key in CSV_FIELDS[2:]}})
                cutoff=milliseconds('2023-07-14T19:25:16.885Z') if window['name']=='july' and source=='exness' else None
                summary=aggregate(events(window,source),start,end,
                                  kind='reference' if source=='forexite_reference' else 'ticks',
                                  captured=availability(window,source),minute_bins=source=='exness',
                                  tail_cutoff=cutoff,save_event=save)
                if source=='histdata_candidate':inventory_check(window,summary)
                summaries[source]=summary
            output_windows.append(dict(**window,sources=summaries,distances=distances(summaries)))
    evidence=questions(output_windows[0]['sources']['exness'],output_windows[1]['sources']['exness'],
                       milliseconds('2023-03-26T23:00:00.000Z'),milliseconds('2023-07-14T20:00:00.000Z'))
    write(REPORT,dict(kind='fixed_coverage_comparison_025',windows=output_windows,questions=evidence,
                      lineage_path=LINEAGE.relative_to(ROOT).as_posix(),lineage_sha256=digest(LINEAGE),
                      ledger_sha256=digest(LEDGER),annual_eligible=False,absolute_utc_certified=False,
                      historical_sessions_certified=False,upstream_independence_verified=False,
                      performance_evaluation_ready=False,market_profitability_established=False,
                      orders_available=False))
    print(json.dumps(evidence),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('freeze','verify','run'))
    action=parser.parse_args().action
    {'freeze':freeze,'verify':verify,'run':run}[action]()

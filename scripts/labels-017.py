"""Freeze and compare cached minute streams; never fetch, approve or trade."""
import argparse
import csv
from datetime import datetime,timezone
import gzip
import json
from pathlib import Path
import runpy
import sys
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from forex_demo_lab.minute_labels import MINUTE,aggregate,compare
from forex_demo_lab.reference import ANCHORS,ms
from forex_demo_lab.tick_audit import sha256
from forex_demo_lab.cli import write_json

LEDGER=Path('reports/labels-017-ledger.json');ARCHIVE=Path('reports/labels-017-source.zip')
ROOT=Path('reports/labels-017')
CODE=[Path(p) for p in ('docs/LABELS-017-PLAN.md','src/forex_demo_lab/minute_labels.py',
    'scripts/labels-017.py','scripts/check-labels-017.py','tests/test_minute_labels.py')]


def preflight():
    for name in ('correct-clock-013','normalize-history-015','reference-016','reference-016b'):
        runpy.run_path('scripts/'+name+'.py')['verify']()


def bounds(day):
    start=ms(datetime.fromisoformat(day).replace(tzinfo=timezone.utc))
    return start+10*3600000,start+15*3600000


def ticks(day,source):
    start,end=bounds(day)
    if source=='broker':
        path=Path(f'data/clock-012/{day}/ticks.csv.gz');offset=(3 if day[5:7]=='07' else 2)*3600000
        with gzip.open(path,'rt',newline='') as f:
            reader=csv.DictReader(f)
            if reader.fieldnames!=['sequence','time_msc','bid','ask','flags']:raise ValueError('Broker schema differs')
            for count,row in enumerate(reader):
                if int(row['sequence'])!=count:raise ValueError('Broker sequence differs')
                stamp=int(row['time_msc'])-offset
                if start<=stamp<end:
                    yield {'source_row':count,'time_msc':stamp,'bid':row['bid'],'ask':row['ask']}
    elif source=='histdata':
        month=day[:7].replace('-','');path=Path(f'data/normalization-015/{month}/ticks.csv.gz')
        count=-1
        with gzip.open(path,'rt',newline='') as f:
            reader=csv.reader(f)
            if next(reader)!=['sequence','source_sequence','source_label','candidate_time_msc','bid','ask','volume']:
                raise ValueError('Candidate schema differs')
            for count,row in enumerate(reader):
                if len(row)!=7 or int(row[0])!=count:raise ValueError('Candidate sequence differs')
                if row[2].startswith(day):
                    stamp=int(row[3])
                    if start<=stamp<end:yield {'source_row':int(row[1]),'time_msc':stamp,'bid':row[4],'ask':row[5]}
        provenance=json.loads(path.with_name('provenance.json').read_text())
        if count+1!=provenance['candidate_rows']:raise ValueError('Candidate row count differs')
    else:raise ValueError('Undeclared tick source')


def freeze():
    preflight()
    if LEDGER.exists() or ARCHIVE.exists():raise FileExistsError('Labels already frozen')
    files=set(CODE)|{Path('data/reference-016/diagnostic-minute-lineage.csv'),Path('data/reference-016/diagnostic-minute-lineage.json')}
    for day in ANCHORS:
        folder=Path(f'data/clock-012/{day}');capture=json.loads((folder/'capture.json').read_text())
        if capture['account_type']!='demo' or capture['terminal_algo_trading'] is not False:
            raise ValueError('Capture not guarded demo evidence')
        if sha256(folder/'ticks.csv.gz')!=capture['data_sha256']:raise ValueError('Cached broker ticks changed')
        files.update((folder/'ticks.csv.gz',folder/'capture.json'))
        folder=Path(f'data/normalization-015/{day[:7].replace("-","")}')
        provenance=json.loads((folder/'provenance.json').read_text())
        if sha256(folder/'ticks.csv.gz')!=provenance['data_sha256']:raise ValueError('Candidate ticks changed')
        files.update(folder/name for name in ('ticks.csv.gz','inventory.json','provenance.json','seal.json'))
    for name in ('correction-013','normalization-015','reference-016','reference-016b'):
        files.add(Path(f'reports/{name}-ledger.json'))
    files.update(Path(p) for p in ('src/forex_demo_lab/reference.py','src/forex_demo_lab/reference_boundary.py',
                                  'src/forex_demo_lab/tick_audit.py','src/forex_demo_lab/cli.py'))
    with zipfile.ZipFile(ARCHIVE,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(CODE):z.write(p,p.as_posix())
    write_json(LEDGER,{'kind':'frozen_minute_label_diagnosis_017','client_date':'2026-10-06',
        'frozen_utc':datetime.now(timezone.utc).isoformat(),'archive_sha256':sha256(ARCHIVE),
        'file_bindings':{p.as_posix():sha256(p) for p in sorted(files)},'days':list(ANCHORS),
        'absolute_utc_certified':False,'performance_evaluation_ready':False,'demo_execution_ready':False})
    write_json(Path('reports/labels-017-seal.json'),{'ledger_sha256':sha256(LEDGER)})


def verify():
    ledger=json.loads(LEDGER.read_text())
    if sha256(LEDGER)!=json.loads(Path('reports/labels-017-seal.json').read_text())['ledger_sha256']:
        raise ValueError('Label ledger seal differs')
    if sha256(ARCHIVE)!=ledger['archive_sha256']:raise ValueError('Label source archive differs')
    for p,digest in ledger['file_bindings'].items():
        if sha256(Path(p))!=digest:raise ValueError('Bound label input/source changed: '+p)
    return ledger


def run():
    preflight();verify();ROOT.mkdir(exist_ok=False)
    reference={}
    with Path('data/reference-016/diagnostic-minute-lineage.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            stamp=int(row['reference_time_msc'])
            if stamp in reference:raise ValueError('Reference minute overlap')
            reference[stamp]={k:row[k] for k in ('open','high','low','close')}
    pairs=[]
    for day in ANCHORS:
        start,end=bounds(day);labels=range(start+MINUTE,end-MINUTE,MINUTE)
        for source in ('broker','histdata'):
            bars=aggregate(ticks(day,source));result=compare(labels,reference,bars)
            result.update(kind='diagnostic_minute_label_pair_017',day=day,tick_source=source,
                ledger_sha256=sha256(LEDGER),minute_bars=list(bars.values()),
                absolute_utc_certified=False,performance_evaluation_ready=False,demo_execution_ready=False)
            path=ROOT/f'{day}-{source}.json';write_json(path,result)
            summary={k:result[k] for k in ('day','tick_source','label_count','common_triplets',
                'paired_labels_by_hypothesis','common_close_median_pips','relative_end_label_screen_pass')}
            summary.update(report=path.as_posix(),report_sha256=sha256(path));pairs.append(summary)
            print(json.dumps(summary),flush=True)
    passed=all(p['relative_end_label_screen_pass'] for p in pairs if p['tick_source']=='broker')
    write_json(Path('reports/labels-017-review.json'),{'kind':'diagnostic_minute_label_review_017',
        'ledger_sha256':sha256(LEDGER),'pairs':pairs,'all_six_broker_screens_pass':passed,
        'original_provider_bar_semantics_verified':False,'absolute_utc_certified':False,
        'performance_evaluation_ready':False,'demo_execution_ready':False,'no_source_blending':True,
        'no_market_returns_computed':True})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['freeze','verify','run'])
    {'freeze':freeze,'verify':verify,'run':run}[parser.parse_args().command]()

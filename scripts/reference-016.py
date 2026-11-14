"""Freeze and compare nine acquired reference archives; no network or trading."""
import argparse
import io
import json
from pathlib import Path
import runpy
import sys
import zipfile
from datetime import datetime, timezone

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from forex_demo_lab.reference import ANCHORS, DAYS, HOUR, compare_day, hourly, ms, parse, screen
from forex_demo_lab.tick_audit import sha256
from forex_demo_lab.cli import write_json

ROOT=Path('data/reference-016')
LEDGER=Path('reports/reference-016-ledger.json')
ARCHIVE=Path('reports/reference-016-source.zip')
REPORT=Path('reports/reference-016-review.json')
CODE=[Path(p) for p in ('docs/REFERENCE-016-PLAN.md','src/forex_demo_lab/reference.py',
    'tests/test_reference.py','scripts/reference-016.py','scripts/check-reference-016.py')]


def preflight():
    runpy.run_path('scripts/correct-clock-013.py')['verify']()
    runpy.run_path('scripts/normalize-history-015.py')['verify']()


def freeze():
    preflight()
    if LEDGER.exists() or ARCHIVE.exists(): raise FileExistsError('Reference stage already frozen')
    files=set(CODE) | set(ROOT.glob('*.html')) | {ROOT/'pages.json', Path('/usr/share/zoneinfo/Europe/Berlin')}
    for day in DAYS:
        files.update((ROOT/day/'original.zip',ROOT/day/'download.json'))
        outcome=json.loads((ROOT/day/'download.json').read_text())
        if sha256(ROOT/day/'original.zip')!=outcome.get('sha256'):
            raise ValueError('Acquired archive hash differs')
        month=day[:7].replace('-','')
        files.update(Path(f'data/normalization-015/{month}/{name}.json') for name in ('inventory','provenance','seal'))
    with zipfile.ZipFile(ARCHIVE,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for path in CODE: z.write(path,path.as_posix())
    write_json(LEDGER,{'kind':'frozen_reference_diagnostics_016',
        'declared_utc':datetime.now(timezone.utc).isoformat(),'client_date':'2026-10-06',
        'file_bindings':{p.as_posix():sha256(p) for p in sorted(files)},
        'archive_sha256':sha256(ARCHIVE),'days':list(DAYS),
        'performance_evaluation_ready':False,'absolute_utc_certified':False,'demo_execution_ready':False})
    write_json(Path('reports/reference-016-seal.json'),{'ledger_sha256':sha256(LEDGER)})


def verify():
    ledger=json.loads(LEDGER.read_text())
    if sha256(LEDGER)!=json.loads(Path('reports/reference-016-seal.json').read_text())['ledger_sha256']:
        raise ValueError('Reference ledger changed')
    if sha256(ARCHIVE)!=ledger['archive_sha256']:
        raise ValueError('Reference source archive changed')
    for path,digest in ledger['file_bindings'].items():
        if sha256(Path(path))!=digest: raise ValueError('Frozen reference input/code changed: '+path)
    return ledger


def run():
    preflight(); verify()
    if REPORT.exists(): raise FileExistsError('Reference review exists')
    all_rows=[]; days=[]; candidate={}
    for day in sorted(DAYS):
        folder=ROOT/day
        with zipfile.ZipFile(folder/'original.zip') as z:
            members=z.infolist()
            expected=datetime.fromisoformat(day).strftime('%d%m%y.txt')
            if len(members)!=1 or members[0].filename!=expected or members[0].file_size>16*1024*1024:
                raise ValueError('Unexpected archive members or inflated size')
            with z.open(members[0]) as binary:
                rows=parse(io.TextIOWrapper(binary,encoding='ascii',newline=''),day)
        all_rows.extend(rows)
        bars=hourly(rows)
        days.append({'source_day':day,'eurusd_rows':len(rows),'hourly':list(bars.values()),
                     'archive_sha256':sha256(folder/'original.zip')})
        inventory=json.loads(Path(f'data/normalization-015/{day[:7].replace("-","")}/inventory.json').read_text())
        for h in inventory['hourly']: candidate[h['hour_start_ms']]=h
    references=hourly(all_rows)
    screens=[screen(day,references,candidate) for day in ANCHORS]
    probes=[]
    for label in ('2023-03-26T23:00:00+00:00','2023-07-14T19:00:00+00:00','2023-07-14T20:00:00+00:00'):
        stamp=ms(datetime.fromisoformat(label))
        probes.append({'utc_label':label,**compare_day(label[:10],references,candidate)[stamp%86_400_000//HOUR]})
    result={'kind':'diagnostic_minute_reference_review_016','ledger_sha256':sha256(LEDGER),
        'source':'Forexite original MetaStock daily ZIP','published_clock':'CET/CEST',
        'bar_start_or_end_semantics':'unverified_literal_labels_only',
        'original_metastock_bid_semantics':'unverified; redistributed Forex Tester Basic describes Bid',
        'upstream_independence':'different publisher; independent upstream lineage unverified',
        'source_days':days,'screens':screens,'all_six_screens_pass':all(s['fixed_screen_pass'] for s in screens),
        'utc_day_comparisons':{d:compare_day(d,references,candidate) for d in DAYS},'gap_probes':probes,
        'reference_eurusd_rows':len(all_rows),'reference_hourly':list(references.values()),
        'session_calendar_certified':False,'absolute_utc_certified':False,
        'performance_evaluation_ready':False,'demo_execution_ready':False,
        'no_source_blending':True,'no_market_returns_computed':True}
    write_json(REPORT,result)
    print(json.dumps({'rows':len(all_rows),'six_screens_pass':result['all_six_screens_pass'],
        'screens':screens,'gap_probes':probes}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['freeze','verify','run'])
    command=parser.parse_args().command
    {'freeze':freeze,'verify':verify,'run':run}[command]()

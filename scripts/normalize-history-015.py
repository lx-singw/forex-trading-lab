"""Freeze/normalize/review existing history; never approve performance or fetch data."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import runpy
import sys
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from forex_demo_lab.cli import write_json
from forex_demo_lab.corrected_clock import Replay
from forex_demo_lab.normalization import MONTHS, completed, coverage, empty_hours, normalize
from forex_demo_lab.tick_audit import sha256

ROOT=Path('data/normalization-015')
LEDGER=Path('reports/normalization-015-ledger.json')
ARCHIVE=Path('reports/normalization-015-source.zip')
CORRECTION=runpy.run_path(str(Path(__file__).with_name('correct-clock-013.py')))
HISTORY=CORRECTION['STUDY']['HISTORY']
LOAD=CORRECTION['LOAD']
CODE=[Path('docs/NORMALIZATION-015-PLAN.md'),Path('scripts/normalize-history-015.py'),
      Path('scripts/check-normalization-015.py'),Path('tests/test_normalization.py'),
      *sorted(Path('src/forex_demo_lab').glob('*.py'))]


def freeze():
    CORRECTION['verify']()
    if LEDGER.exists() or ARCHIVE.exists():
        raise FileExistsError('Normalizer already frozen')
    review=LOAD(Path('reports/history-009-review.json'))
    months={r['month']:r for r in review['months']}
    if set(months)!=set(MONTHS):
        raise ValueError('Original review lacks all 48 months')
    bindings={}
    files=set(CODE)
    for p in ('reports/history-009-review.json','reports/history-009-ledger.json',
              'reports/correction-013-ledger.json','reports/clock-012-repeat-content.json',
              '/usr/share/zoneinfo/Europe/Athens'):
        files.add(Path(p))
    for month in MONTHS:
        folder=HISTORY['ROOT']/month
        bindings[month]={**HISTORY['binding'](folder,month),'original_rows':months[month]['rows_examined']}
        if sha256(Path(months[month]['report']))!=months[month]['report_sha256']:
            raise ValueError('Original monthly review changed')
        files.update([folder/'original.zip',folder/'download.json',Path(months[month]['report'])])
    with zipfile.ZipFile(ARCHIVE,'x',compression=zipfile.ZIP_DEFLATED) as zipped:
        for p in CODE: zipped.write(p,p.as_posix())
    ledger={'kind':'frozen_diagnostic_normalization_015','frozen_utc':datetime.now(timezone.utc).isoformat(),
        'bindings':bindings,'file_bindings':{p.as_posix():sha256(p) for p in sorted(files)},
        'archive_sha256':sha256(ARCHIVE),'replays':LOAD(CORRECTION['LEDGER'])['replays'],
        'performance_evaluation_ready':False,'demo_execution_ready':False}
    write_json(LEDGER,ledger)
    write_json(Path('reports/normalization-015-seal.json'),{'ledger_sha256':sha256(LEDGER)})
    print('Frozen all 48 archives and diagnostic-only normalization',flush=True)


def verify():
    ledger=LOAD(LEDGER)
    if sha256(LEDGER)!=LOAD(Path('reports/normalization-015-seal.json'))['ledger_sha256']:
        raise ValueError('Normalization ledger changed')
    if sha256(ARCHIVE)!=ledger['archive_sha256']:
        raise ValueError('Normalization source archive changed')
    for p,digest in ledger['file_bindings'].items():
        if sha256(Path(p))!=digest:
            raise ValueError('Frozen normalization code/input/evidence changed')
    return ledger


def run_year(year):
    ledger=verify()
    for month in (m for m in MONTHS if m.startswith(str(year))):
        folder=ROOT/month
        binding=ledger['bindings'][month]
        if folder.exists():
            row=completed(folder,binding)
            status='verified_completed_month'
        else:
            replay=Replay(**ledger['replays'][month]) if month in ledger['replays'] else None
            row=normalize(CORRECTION['STUDY']['month_rows'](month),month,folder,binding,
                          binding['original_rows'],replay)
            status='normalized_diagnostic_month'
        print(json.dumps({'status':status,'month':month,'original_rows':row['original_rows'],
                          'candidate_rows':row['candidate_rows'],'collapsed':row['collapsed_replay_rows']}),flush=True)


def review():
    ledger=verify()
    path=Path('reports/normalization-015-review.json')
    if path.exists(): raise FileExistsError('Normalization review exists')
    rows=[completed(ROOT/m,ledger['bindings'][m]) for m in MONTHS]
    result=coverage(rows)
    observed=set();gaps=[];year_counts={};monthly=[]
    for month,row in zip(MONTHS,rows):
        inventory=LOAD(ROOT/month/'inventory.json')
        observed.update(h['hour_start_ms'] for h in inventory['hourly'])
        gaps.extend({'source_month':month,**g} for g in inventory['gaps_over_one_hour'])
        for year,count in inventory['candidate_year_tick_counts'].items():
            year_counts[year]=year_counts.get(year,0)+count
        monthly.append({'source_month':month,'provenance_sha256':sha256(ROOT/month/'provenance.json'),
            'data_sha256':row['data_sha256'],'inventory_sha256':row['inventory_sha256'],
            'candidate_rows':row['candidate_rows'],'observed_hours':len(inventory['hourly'])})
    if sum(year_counts.values())!=result['candidate_rows']:
        raise ValueError('Candidate year count accounting differs')
    result.update(kind='diagnostic_normalization_review_015',ledger_sha256=sha256(LEDGER),
        month_bindings=monthly,gaps_over_one_hour=gaps,candidate_year_tick_counts=year_counts,
        hourly_coverage=empty_hours(observed),
        blockers=['annual_clock_uncertified','open_session_coverage_unresolved','historical_costs_unverified'],
        no_source_blending=True,no_market_returns_computed=True,demo_execution_ready=False)
    write_json(path,result)
    print(json.dumps({'months':48,'candidate_rows':result['candidate_rows'],'collapsed':result['collapsed_replay_rows'],
        'seams':len(result['month_seams']),'quote_free_hours':len(result['hourly_coverage']['quote_free_hours']),
        'weekday_watchlist_hours':len(result['hourly_coverage']['weekday_quote_free_hours']),
        'performance_evaluation_ready':False}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('freeze','verify','run-year','review'))
    parser.add_argument('--year',type=int,choices=range(2020,2024))
    args=parser.parse_args()
    if args.action=='run-year':
        if args.year is None: parser.error('run-year requires --year')
        run_year(args.year)
    else: {'freeze':freeze,'verify':verify,'review':review}[args.action]()

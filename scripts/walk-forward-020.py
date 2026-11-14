"""CLI for gated frozen chronological replay; no trading or network access."""
import argparse
import csv
import gzip
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from forex_demo_lab.cli import write_json
from forex_demo_lab.tick_audit import sha256
from forex_demo_lab.walk_forward_metrics import YEARS, bound, freeze, load, review_gate, run, verify


def synthetic_fixture(destination):
    """Sparse invented quarters exercise windows; never approve market data."""
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    years = {}
    for year in YEARS:
        path = destination/f'{year}-ticks.csv.gz'
        count, first, last = 0, None, None
        from datetime import datetime, timezone
        with path.open('xb') as binary, gzip.GzipFile(filename='', mode='wb', fileobj=binary, mtime=0) as zipped:
            import io
            with io.TextIOWrapper(zipped, encoding='utf-8', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(['sequence','time_msc','bid','ask'])
                for month in (1,4,7,10):
                    start = int(datetime(year,month,1,tzinfo=timezone.utc).timestamp())*1000
                    for h in range(72):
                        for minute in (0,30,59):
                            ms = start+h*3_600_000+minute*60_000
                            bid = round(1.1+.001*math.sin(h/5+minute/60), 5)
                            writer.writerow([count,ms,bid,round(bid+.0001,5)])
                            first = ms if first is None else first
                            last, count = ms, count+1
        provenance = destination/f'{year}-provenance.json'
        write_json(provenance, {'kind':'chronological_research_ticks','symbol':'EURUSD',
            'year':year,'synthetic':True,'ticks':count,'first_ms':first,'last_ms':last,
            'data_sha256':sha256(path),'source':'invented sinusoidal software fixture; sparse quarters'})
        years[str(year)] = {'data':path.name,'provenance':provenance.name}
    write_json(destination/'review.json', {'kind':'synthetic_chronological_fixture','synthetic':True,
        'performance_evaluation_ready':False,'years':{str(y):{} for y in YEARS}})
    write_json(destination/'bundle.json', {'kind':'chronological_ticks_input','synthetic':True,
        'years':years,'review':'review.json'})
    return {'status':'invented_fixture_only','bundle':str(destination/'bundle.json')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action',required=True)
    p = commands.add_parser('synthetic-fixture'); p.add_argument('destination',type=Path)
    p = commands.add_parser('freeze'); p.add_argument('bundle',type=Path); p.add_argument('destination',type=Path)
    for action in ('verify','run'):
        p = commands.add_parser(action); p.add_argument('destination',type=Path)
    p = commands.add_parser('check-review'); p.add_argument('review',type=Path); p.add_argument('--report',type=Path)
    args = parser.parse_args()
    if args.action == 'check-review':
        try:
            review_gate(load(args.review),False)
            result = {'status':'review_schema_passed_only','review_sha256':sha256(args.review),
                      'dataset_bytes_not_yet_checked':True,'demo_execution_ready':False}
        except (ValueError,KeyError,TypeError) as error:
            result = {'status':'blocked_before_performance','review_sha256':sha256(args.review),
                      'reason':str(error),'performance_evaluation_ready':False,'demo_execution_ready':False}
        if args.report: write_json(args.report,result)
        print(json.dumps(result,indent=2))
        sys.exit(2 if result['status']=='blocked_before_performance' else 0)
    if args.action == 'synthetic-fixture':
        result = synthetic_fixture(args.destination)
    elif args.action == 'freeze':
        ledger = freeze(args.bundle,args.destination)
        result = {'status':'frozen_before_returns','synthetic':ledger['synthetic'],'scenarios':ledger['maximum_scenarios']}
    elif args.action == 'verify':
        ledger = verify(args.destination)
        result = {'status':'frozen_bindings_verified','synthetic':ledger['synthetic']}
    else:
        result = run(args.destination)
        result = {'status':result['status'],'scenarios':len(result['scenario_bindings']),
                  'choices':{r['fold']:r['candidate'] for r in result['selected_tests']},
                  'market_profitability_established':False,'demo_execution_ready':False}
    print(json.dumps(result,indent=2))

"""Predeclared relative-price checks; cannot establish absolute UTC or eligibility."""
import argparse
import csv
from datetime import datetime, timedelta, timezone
import math
from pathlib import Path
import runpy
from statistics import median
import zipfile

history = runpy.run_path(str(Path(__file__).with_name('history-009.py')))
DATES = ('2020-01-14', '2020-07-14', '2021-01-12', '2021-07-13',
         '2022-01-11', '2022-07-12', '2023-01-10', '2023-07-11')
REFERENCE = Path('data/history-009-mt5-reference')
PLAN = Path('reports/history-009-corroboration-plan.json')
OUTPUT = Path('reports/history-009-corroboration.json')


def compare(day, source, reference):
    start = datetime.fromisoformat(day).replace(hour=8)
    hours = [start + timedelta(hours=i) for i in range(12)]
    candidates = []
    for offset in range(10):
        differences = [abs(source[h] - reference[h + timedelta(hours=offset)]) / .0001
                       for h in hours if h in source and h + timedelta(hours=offset) in reference]
        candidates.append({'reference_minus_source_hours': offset, 'matched_hours': len(differences),
                           'mean_pips': sum(differences) / len(differences) if differences else None,
                           'median_pips': median(differences) if differences else None,
                           'maximum_pips': max(differences) if differences else None})
    full = sorted((c for c in candidates if c['matched_hours'] == 12), key=lambda c: c['mean_pips'])
    best = full[0] if full else None
    margin = full[1]['mean_pips'] - best['mean_pips'] if len(full) > 1 else None
    passed = bool(best and len(full) == 10 and best['median_pips'] <= 1
                  and best['maximum_pips'] <= 3 and margin >= 2)
    return {'source_day': day, 'all_offsets': candidates, 'best_offset': best['reference_minus_source_hours'] if best else None,
            'mean_margin_to_second_best_pips': margin, 'relative_price_screen_passed': passed}


def freeze():
    if PLAN.exists():
        raise FileExistsError('Corroboration already declared')
    sha = history['sha256']
    archive = Path('reports/history-009-corroboration-source.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for p in (Path(__file__), Path('tests/test_history_009_corroboration.py')):
            z.write(p, p.as_posix())
    history['write_json'](PLAN, {'declared_utc': datetime.now(timezone.utc).isoformat(), 'source_days': DATES,
        'hours': '08:00 through 19:00 inclusive, naive source labels', 'offsets': list(range(10)),
        'rule': 'All ten offsets require 12 matched closes; best median <=1 pip, max <=3 pips, mean advantage >=2 pips',
        'script_sha256': sha(Path(__file__)), 'source_archive_sha256': sha(archive),
        'reference_metadata_sha256': sha(REFERENCE / 'capture.json'), 'reference_raw_sha256': sha(REFERENCE / 'rates.csv'),
        'meaning': 'Relative price agreement only; not absolute UTC, full coverage, upstream independence or executable fills',
        'performance_evaluation_ready': False})


def run():
    load, sha = history['load'], history['sha256']
    plan = load(PLAN)
    if (plan['script_sha256'] != sha(Path(__file__)) or plan['source_days'] != list(DATES)
            or plan['reference_raw_sha256'] != sha(REFERENCE / 'rates.csv')
            or plan['reference_metadata_sha256'] != sha(REFERENCE / 'capture.json')
            or plan['source_archive_sha256'] != sha(Path('reports/history-009-corroboration-source.zip'))):
        raise ValueError('Frozen corroboration inputs changed')
    capture = load(REFERENCE / 'capture.json')
    if capture['raw_sha256'] != sha(REFERENCE / 'rates.csv'):
        raise ValueError('Reference capture hash mismatch')
    reference = {}
    with (REFERENCE / 'rates.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            stamp = datetime.fromisoformat(row['time'])
            if stamp.utcoffset() != timedelta(0) or any((stamp.minute, stamp.second, stamp.microsecond)):
                raise ValueError('Unexpected reference label representation')
            label = stamp.replace(tzinfo=None)  # Preserve raw clock label, not a timezone conversion.
            prices = [float(row[k]) for k in ('open', 'high', 'low', 'close')]
            o, h, l, c = prices
            if label in reference or not all(math.isfinite(v) and v > 0 for v in prices) or not l <= min(o, c) <= max(o, c) <= h:
                raise ValueError('Invalid reference OHLC or duplicate hour')
            reference[label] = c
    results, bindings = [], []
    for day in DATES:
        month = day.replace('-', '')[:6]
        p = Path(f'reports/history-009-raw-{month}.json')
        row = load(p)
        bound = history['binding'](history['ROOT'] / month, month)
        if not row['structural_checks_passed'] or any(row[k] != v for k, v in bound.items()):
            raise ValueError('Unverified or changed source archive')
        source = {datetime.fromisoformat(v['source_hour']): v['bid_close'] for v in row['source_hour_diagnostics']}
        results.append(compare(day, source, reference))
        bindings.append({'month': month, **bound, 'raw_audit_sha256': sha(p)})
    history['write_json'](OUTPUT, {'plan_sha256': sha(PLAN), 'windows': results, 'source_bindings': bindings,
        'all_relative_price_screens_passed': all(r['relative_price_screen_passed'] for r in results),
        'absolute_utc_verified': False, 'performance_evaluation_ready': False, 'demo_execution_ready': False})
    for r in results:
        print(r['source_day'], 'offset', r['best_offset'], 'passed', r['relative_price_screen_passed'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run'))
    args = parser.parse_args()
    {'freeze': freeze, 'run': run}[args.action]()

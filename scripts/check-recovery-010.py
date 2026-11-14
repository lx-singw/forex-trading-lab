"""Independent SQL quote aggregation and conditional cross-source coverage census."""
import csv
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import runpy
import sqlite3


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def load(path):
    return json.loads(path.read_text())


def check_chunk(folder, report):
    metadata = load(folder / 'capture.json')
    if (sha(folder / 'capture.json') != report['capture_sha256']
            or sha(folder / 'ticks.csv.gz') != report['data_sha256']
            or metadata['data_sha256'] != report['data_sha256']):
        raise ValueError('SQL check input binding changed')
    db = sqlite3.connect(':memory:')
    try:
        db.execute('CREATE TABLE quotes (seq INTEGER PRIMARY KEY, ms INTEGER, bid REAL, ask REAL)')
        with gzip.open(folder / 'ticks.csv.gz', 'rt', newline='') as stream:
            db.executemany('INSERT INTO quotes VALUES (?,?,?,?)',
                ((int(r['sequence']), int(r['time_msc']), float(r['bid']), float(r['ask']))
                 for r in csv.DictReader(stream)))
        rows = db.execute('''WITH groups AS (
            SELECT ms / 3600000 AS hour, COUNT(*) AS n, MIN(seq) AS first, MAX(seq) AS last,
                MAX(bid) AS bh, MIN(bid) AS bl, MAX(ask) AS ah, MIN(ask) AS al,
                MIN(ms) AS first_ms, MAX(ms) AS last_ms
            FROM quotes GROUP BY hour)
            SELECT hour, n, first_ms, last_ms, f.bid, bh, bl, l.bid, f.ask, ah, al, l.ask
            FROM groups JOIN quotes f ON f.seq=groups.first JOIN quotes l ON l.seq=groups.last
            ORDER BY hour''').fetchall()
    finally:
        db.close()
    observed = [h for h in report['hours'] if h['ticks']]
    if len(observed) != len(rows) or sum(r[1] for r in rows) != report['ticks']:
        raise ValueError('Independent SQL coverage/count differs')
    fields = ['ticks', 'first_ms', 'last_ms', 'bid_open', 'bid_high', 'bid_low', 'bid_close',
              'ask_open', 'ask_high', 'ask_low', 'ask_close']
    for hour, values in zip(observed, rows):
        if int(datetime.fromisoformat(hour['source_hour_label']).timestamp()) // 3600 != values[0]:
            raise ValueError('Independent SQL hour differs')
        if any(not math.isclose(hour[k], v, rel_tol=0, abs_tol=1e-10) for k, v in zip(fields, values[1:])):
            raise ValueError('Independent SQL quote aggregation differs')
    return {'ticks': report['ticks'], 'observed_hours': len(rows), 'capture_sha256': report['capture_sha256']}


def conditional_coverage(review):
    """+7 was previously observed; this census does not prove that clock mapping."""
    old_review_path = Path('reports/history-009-review.json')
    if sha(old_review_path) != load(Path('reports/history-009-checks.json'))['review_sha256']:
        raise ValueError('Original history review binding changed')
    old_review = load(old_review_path)
    source = set()
    bindings = []
    for row in old_review['months']:
        if not '202301' <= row['month'] <= '202308':
            continue
        path = Path(row['report'])
        if sha(path) != row['report_sha256'] or row['status'] != 'structural_pass':
            raise ValueError('Original raw coverage review changed or failed')
        raw = load(path)
        folder = Path('data/history-009-raw') / row['month']
        if sha(folder / 'original.zip') != raw['archive_sha256'] or sha(folder / 'download.json') != raw['metadata_sha256']:
            raise ValueError('Original monthly source binding changed')
        source.update((datetime.fromisoformat(h['source_hour']) + timedelta(hours=7)).replace(tzinfo=timezone.utc).isoformat()
                      for h in raw['source_hour_diagnostics'])
        bindings.append({'month': row['month'], 'audit_sha256': row['report_sha256'], 'archive_sha256': raw['archive_sha256']})
    counts = {}
    extra = []
    for h in review['hours']:
        status = ('both_observed' if h['source_hour_label'] in source else 'broker_ticks_without_histdata_hour') if h['ticks'] else (
            'histdata_hour_without_broker_ticks' if h['source_hour_label'] in source else 'both_empty_unclassified')
        month = h['source_hour_label'][:7]
        counts.setdefault(month, {})[status] = counts.setdefault(month, {}).get(status, 0) + 1
        if status == 'broker_ticks_without_histdata_hour':
            extra.append(h['source_hour_label'])
    return {'assumed_reference_minus_histdata_hours': 7, 'absolute_mapping_verified': False,
            'meaning': 'Coverage census conditional on prior relative mapping; not a UTC or completeness gate',
            'by_broker_raw_month': counts, 'broker_tick_hours_without_histdata_hour': extra, 'source_bindings': bindings}


def main():
    study = runpy.run_path(str(Path(__file__).with_name('recovery-010.py')))
    ledger = study['verify']()
    review = load(Path('reports/recovery-010-review.json'))
    if review['ledger_sha256'] != sha(Path('reports/recovery-010-ledger.json')) or len(review['bindings']) != len(ledger['windows']):
        raise ValueError('Final recovery review binding changed')
    checks = []
    flattened = []
    for i, binding in enumerate(review['bindings']):
        path = Path(f'reports/recovery-010-chunk-{i:03d}.json')
        report = load(path)
        if sha(path) != binding['audit_sha256']:
            raise ValueError('Final recovery audit changed')
        checks.append(check_chunk(Path(binding['folder']), report))
        flattened.extend(report['hours'])
        print(f'SQL checked {i + 1}/{len(review["bindings"])}', flush=True)
    if flattened != review['hours'] or sum(r['ticks'] for r in checks) != review['ticks']:
        raise ValueError('Final review differs from independently checked chunks')
    result = {'status': 'all_sql_aggregates_match', 'checks': checks, 'ticks': review['ticks'],
              'observed_hours': sum(c['observed_hours'] for c in checks),
              'review_sha256': sha(Path('reports/recovery-010-review.json')),
              'checker_sha256': sha(Path(__file__)), 'conditional_coverage': conditional_coverage(review),
              'raw_weekday_empty_hours': [h['source_hour_label'] for h in review['hours'] if not h['ticks']
                  and datetime.fromisoformat(h['source_hour_label']).weekday() < 5],
              'independent_market_feed': False, 'performance_evaluation_ready': False}
    with Path('reports/recovery-010-checks.json').open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(f'All SQL aggregates match: {result["ticks"]} ticks; {result["observed_hours"]} observed hours')


if __name__ == '__main__':
    main()

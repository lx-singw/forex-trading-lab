"""Preserve failed strict audits and finish diagnostics on remaining raw months.

Diagnostic continuation only: never reorder, normalize, repair or approve data.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime
import io
import math
from pathlib import Path
import runpy
import time
import zipfile

history = runpy.run_path(str(Path(__file__).with_name('history-009.py')))


def defects(folder, month):
    bound = history['binding'](folder, month)
    previous = None
    counts, examples = Counter(), []
    rows = 0
    with zipfile.ZipFile(folder / 'original.zip') as z:
        with z.open(f'DAT_ASCII_EURUSD_T_{month}.csv') as b, io.TextIOWrapper(b, encoding='utf-8-sig', newline='') as f:
            for rows, row in enumerate(csv.reader(f), 1):
                problems = []
                if len(row) != 4:
                    problems.append('invalid_schema')
                else:
                    try:
                        label = row[0]
                        if (len(label) != 18 or label[8] != ' ' or label[:6] != month
                                or not (label[:8] + label[9:]).isascii() or not (label[:8] + label[9:]).isdigit()):
                            raise ValueError('Invalid source label')
                        stamp = datetime(int(label[:4]), int(label[4:6]), int(label[6:8]), int(label[9:11]),
                                         int(label[11:13]), int(label[13:15]), int(label[15:]) * 1000)
                        if previous is not None and stamp < previous:
                            problems.append('backward_source_timestamp')
                            if len(examples) < 20:
                                examples.append({'row_number': rows, 'problem': 'backward_source_timestamp',
                                                 'previous_source_label': previous.isoformat(), 'source_label': stamp.isoformat(),
                                                 'backward_seconds': (previous - stamp).total_seconds()})
                        previous = stamp
                    except (ValueError, OverflowError):
                        problems.append('invalid_timestamp')
                    try:
                        bid, ask, volume = map(float, row[1:])
                        if not all(math.isfinite(v) for v in (bid, ask, volume)) or not 0 < bid <= ask or volume < 0:
                            raise ValueError('Invalid quote')
                    except (ValueError, OverflowError):
                        problems.append('invalid_quote_or_volume')
                counts.update(problems)
                for problem in problems:
                    if problem != 'backward_source_timestamp' and len(examples) < 20:
                        examples.append({'row_number': rows, 'problem': problem})
    if not rows:
        counts['empty_archive'] += 1
    return {**bound, 'month': month, 'rows_examined': rows, 'defect_counts': dict(counts), 'examples': examples,
            'structural_checks_passed': False, 'performance_evaluation_ready': False,
            'diagnostic_source_sha256': history['sha256'](Path(__file__))}


def run(follow=False):
    history['verify']()
    write, load, sha = history['write_json'], history['load'], history['sha256']
    output = Path('reports/history-009-review.json')
    if output.exists():
        raise FileExistsError('Review exists; do not overwrite')
    ledger_sha = sha(history['LEDGER'])
    records = []
    for month in history['MONTHS']:
        folder = history['ROOT'] / month
        while not (folder / 'download.json').exists():
            if not follow:
                raise FileNotFoundError('Archive not yet acquired')
            attempts = sorted(Path('reports').glob('history-009-download-attempt-*.json'))
            if attempts and not load(attempts[-1]).get('completed'):
                raise RuntimeError('Acquisition stopped; completed diagnostics preserved')
            time.sleep(2)
        good = Path(f'reports/history-009-raw-{month}.json')
        bad = Path(f'reports/history-009-defects-{month}.json')
        if good.exists() and bad.exists():
            raise ValueError('Conflicting strict audit results')
        if not good.exists() and not bad.exists():
            try:
                row = history['scan'](folder, month)
                path = good
            except ValueError:
                row = defects(folder, month)
                if not row['defect_counts']:
                    raise ValueError('Strict failure not explained by diagnostic; manual review required')
                path = bad
            write(path, {**row, 'ledger_sha256': ledger_sha})
        path = good if good.exists() else bad
        row = load(path)
        if row['ledger_sha256'] != ledger_sha or any(row[k] != v for k, v in history['binding'](folder, month).items()):
            raise ValueError('Audit input binding changed')
        if path == bad and row['diagnostic_source_sha256'] != sha(Path(__file__)):
            raise ValueError('Diagnostic implementation changed')
        records.append({'month': month, 'status': 'structural_pass' if path == good else 'structural_failure',
                        'rows_examined': row['ticks'] if path == good else row['rows_examined'],
                        'report_sha256': sha(path), 'report': path.as_posix(),
                        'archive_sha256': row['archive_sha256']})
        print(f'Reviewed {month}: {records[-1]["status"]}; {records[-1]["rows_examined"]} rows', flush=True)
    write(output, {'ledger_sha256': ledger_sha, 'diagnostic_source_sha256': sha(Path(__file__)),
                   'status': 'blocked_pending_clock_gap_and_structural_review', 'months': records,
                   'rows_examined': sum(r['rows_examined'] for r in records),
                   'structural_failures': [r['month'] for r in records if r['status'] == 'structural_failure'],
                   'performance_evaluation_ready': False, 'demo_execution_ready': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--follow', action='store_true', help='Wait for the already-running acquisition')
    args = parser.parse_args()
    run(args.follow)

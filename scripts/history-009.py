"""Acquire and audit raw 2020-2023 EURUSD history; never calculate returns."""
import argparse
import csv
from datetime import datetime, timezone
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from forex_demo_lab.cli import write_json
from forex_demo_lab.tick_audit import sha256

MONTHS = tuple(f'{y}{m:02d}' for y in range(2020, 2024) for m in range(1, 13))
ROOT = Path('data/history-009-raw')
PLAN = Path('docs/HISTORY-009-PLAN.md')
LEDGER = Path('reports/history-009-ledger.json')
ARCHIVE = Path('reports/history-009-source.zip')
DOWNLOADER = Path('scripts/download-histdata.py')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def binding(folder, month):
    if month not in MONTHS:
        raise ValueError('Month outside declared acquisition range')
    metadata = load(folder / 'download.json')
    archive = folder / 'original.zip'
    expected_page = f'https://www.histdata.com/download-free-forex-historical-data/?/ascii/tick-data-quotes/eurusd/{month[:4]}/{int(month[4:])}'
    if (metadata.get('source') != 'HistData' or metadata.get('page') != expected_page
            or metadata.get('sha256') != sha256(archive) or metadata.get('bytes') != archive.stat().st_size):
        raise ValueError('Archive identity/hash/size does not match metadata')
    with zipfile.ZipFile(archive) as z:
        members = [m for m in z.infolist() if m.filename.endswith('.csv')]
        if (len(members) != 1 or members[0].filename != f'DAT_ASCII_EURUSD_T_{month}.csv'
                or members[0].file_size > 500_000_000):
            raise ValueError('Wrong instrument/month/schema or oversized archive')
    return {'archive_sha256': sha256(archive), 'metadata_sha256': sha256(folder / 'download.json'),
            'bytes': archive.stat().st_size}


def raw_rows(folder, month):
    """Naive source labels: no EST/DST/UTC interpretation is applied."""
    with zipfile.ZipFile(folder / 'original.zip') as z:
        with z.open(f'DAT_ASCII_EURUSD_T_{month}.csv') as b, io.TextIOWrapper(b, encoding='utf-8-sig', newline='') as f:
            previous = None
            for row in csv.reader(f):
                if len(row) != 4:
                    raise ValueError('Invalid tick schema')
                label = row[0]
                if (len(label) != 18 or label[8] != ' ' or not (label[:8] + label[9:]).isascii()
                        or not (label[:8] + label[9:]).isdigit() or label[:6] != month):
                    raise ValueError('Invalid or out-of-month source label')
                stamp = datetime(int(label[:4]), int(label[4:6]), int(label[6:8]), int(label[9:11]),
                                 int(label[11:13]), int(label[13:15]), int(label[15:]) * 1000)
                bid, ask, volume = map(float, row[1:])
                if (not all(math.isfinite(v) for v in (bid, ask, volume)) or not 0 < bid <= ask
                        or volume < 0 or (previous is not None and stamp < previous)):
                    raise ValueError('Invalid quote/volume or reordered timestamp')
                previous = stamp
                yield stamp, bid, ask


def scan(folder, month):
    bound = binding(folder, month)
    count = same_ms = exact_duplicates = over_spread = 0
    first = previous = previous_row = None
    maximum_spread = 0
    gaps, hours, current = [], [], None
    for stamp, bid, ask in raw_rows(folder, month):
        count += 1
        first = first or stamp
        if previous is not None:
            delta = (stamp - previous).total_seconds()
            same_ms += delta == 0
            exact_duplicates += previous_row == (stamp, bid, ask)
            if delta > 3600:
                gaps.append({'after_source_label': previous.isoformat(), 'before_source_label': stamp.isoformat(),
                             'seconds': delta, 'classification': 'unreviewed'})
        previous, previous_row = stamp, (stamp, bid, ask)
        spread = (ask - bid) / .0001
        maximum_spread = max(maximum_spread, spread)
        over_spread += spread > 1.5
        hour = stamp.replace(minute=0, second=0, microsecond=0).isoformat()
        if current is None or current['source_hour'] != hour:
            current = {'source_hour': hour, 'ticks': 0, 'bid_open': bid, 'bid_high': bid,
                       'bid_low': bid, 'bid_close': bid, 'ask_close': ask}
            hours.append(current)
        current['ticks'] += 1
        current['bid_high'] = max(current['bid_high'], bid)
        current['bid_low'] = min(current['bid_low'], bid)
        current['bid_close'], current['ask_close'] = bid, ask
    if not count:
        raise ValueError('Empty tick archive')
    return {**bound, 'month': month, 'ticks': count, 'observed_source_hours': len(hours),
            'first_source_label': first.isoformat(), 'last_source_label': previous.isoformat(),
            'same_millisecond_transitions': same_ms, 'exact_duplicate_transitions': exact_duplicates,
            'quotes_above_1_5_pip_spread': over_spread, 'maximum_spread_pips': maximum_spread,
            'gaps_over_one_hour': gaps, 'source_hour_diagnostics': hours,
            'structural_checks_passed': True, 'clock_status': 'unreviewed_source_labels_not_UTC',
            'performance_evaluation_ready': False}


def freeze():
    if LEDGER.exists() or ARCHIVE.exists():
        raise FileExistsError('Acquisition already frozen')
    with zipfile.ZipFile(ARCHIVE, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for root in ('src', 'scripts', 'tests'):
            for path in sorted(Path(root).rglob('*.py')):
                z.write(path, path.as_posix())
        for path in (PLAN, Path('config/research-candidates-008.json'), Path('config/tick-pilot-003.json'),
                     Path('config/tick-pilot-003-adverse.json')):
            z.write(path, path.as_posix())
    write_json(LEDGER, {'months': MONTHS, 'plan_sha256': sha256(PLAN), 'archive_sha256': sha256(ARCHIVE),
                       'script_sha256': sha256(Path(__file__)), 'downloader_sha256': sha256(DOWNLOADER),
                       'frozen_utc': datetime.now(timezone.utc).isoformat(),
                       'performance_evaluation_ready': False, 'demo_execution_ready': False})
    print('Frozen 48-month acquisition and chronological protocol', flush=True)


def verify():
    ledger = load(LEDGER)
    if (ledger['months'] != list(MONTHS) or ledger['plan_sha256'] != sha256(PLAN)
            or ledger['archive_sha256'] != sha256(ARCHIVE) or ledger['script_sha256'] != sha256(Path(__file__))
            or ledger['downloader_sha256'] != sha256(DOWNLOADER)):
        raise ValueError('Frozen acquisition implementation/protocol changed')
    return ledger


def acquire():
    verify()
    attempts = sorted(Path('reports').glob('history-009-download-attempt-*.json'))
    attempt = Path(f'reports/history-009-download-attempt-{len(attempts)+1:03d}.json')
    result = {'ledger_sha256': sha256(LEDGER), 'months': [], 'completed': False}
    try:
        for month in MONTHS:
            folder = ROOT / month
            reused = folder.exists()
            if not reused:
                subprocess.run([sys.executable, str(DOWNLOADER), '--month', month, '--output', str(folder)],
                               check=True, timeout=120)
                time.sleep(1)  # Single request stream; no retries or access workarounds.
            result['months'].append({'month': month, 'reused': reused, **binding(folder, month)})
            print(f'Acquired {month} ({len(result["months"])}/48)', flush=True)
        result['completed'] = True
    except Exception as exc:
        result['failure_type'] = type(exc).__name__
        result['failed_month'] = month
        raise
    finally:
        write_json(attempt, result)


def audit():
    verify()
    output = Path('reports/history-009-raw-audit.json')
    if output.exists():
        raise FileExistsError('Audit summary exists; preserve it')
    rows = []
    for month in MONTHS:
        folder = ROOT / month
        path = Path(f'reports/history-009-raw-{month}.json')
        if path.exists():
            row = load(path)
            if (row['ledger_sha256'] != sha256(LEDGER)
                    or any(row[key] != value for key, value in binding(folder, month).items())):
                raise ValueError('Cached audit binding changed')
        else:
            row = {**scan(folder, month), 'ledger_sha256': sha256(LEDGER)}
            write_json(path, row)
        rows.append({'month': month, 'ticks': row['ticks'], 'observed_source_hours': row['observed_source_hours'],
                     'first_source_label': row['first_source_label'], 'last_source_label': row['last_source_label'],
                     'gaps_over_one_hour': len(row['gaps_over_one_hour']), 'report_sha256': sha256(path)})
        print(f'Audited {month}: {row["ticks"]} ticks; {row["observed_source_hours"]} observed source hours', flush=True)
    seams = [{'after_source_label': a['last_source_label'], 'before_source_label': b['first_source_label'],
              'seconds': (datetime.fromisoformat(b['first_source_label']) - datetime.fromisoformat(a['last_source_label'])).total_seconds(),
              'classification': 'unreviewed'} for a, b in zip(rows, rows[1:])]
    if any(s['seconds'] <= 0 for s in seams):
        raise ValueError('Nonchronological archive boundary')
    write_json(output, {'ledger_sha256': sha256(LEDGER), 'status': 'raw_structure_audited_not_performance_eligible',
                        'months': rows, 'month_boundaries': seams, 'ticks': sum(r['ticks'] for r in rows),
                        'observed_source_hours': sum(r['observed_source_hours'] for r in rows),
                        'performance_evaluation_ready': False, 'demo_execution_ready': False})
    print('All 48 raw archives audited; clock and gap review remain required', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'acquire', 'audit', 'verify'))
    args = parser.parse_args()
    {'freeze': freeze, 'acquire': acquire, 'audit': audit, 'verify': verify}[args.action]()

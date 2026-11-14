"""Frozen sequence/UTC-anchor diagnostics; no eligible dataset or trading."""
import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import struct
import subprocess
import sys
import zipfile
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from forex_demo_lab.reconstruction import checked_capture, HOUR
from forex_demo_lab.recovery import references
from forex_demo_lab.source_clock import Boundary, SequenceClock, activity_passes
from forex_demo_lab.tick_audit import sha256

HISTORY = runpy.run_path(str(Path(__file__).with_name('history-009.py')))
ROOT = Path('data/clock-012')
PLAN = Path('docs/CLOCK-012-PLAN.md')
LEDGER = Path('reports/clock-012-ledger.json')
ARCHIVE = Path('reports/clock-012-source.zip')
DATES = ('2020-01-10', '2020-07-02', '2021-01-08', '2021-07-02', '2022-01-07',
         '2022-07-08', '2023-01-06', '2023-07-07', '2021-11-05', '2022-11-04', '2023-11-03')
PAIRS = {
 '202003': ('2020-03-29T18:59:58.557', '2020-03-29T20:00:00.104'),
 '202103': ('2021-03-28T18:59:58.931', '2021-03-28T20:00:00.203'),
 '202203': ('2022-03-27T18:59:58.259', '2022-03-27T20:00:00.340'),
 '202303': ('2023-03-26T18:59:56.352', '2023-03-26T20:00:00.010'),
 '202010': ('2020-10-25T19:59:56.508', '2020-10-25T19:00:00.147'),
 '202110': ('2021-10-31T19:59:54.466', '2021-10-31T19:00:00.566'),
 '202210': ('2022-10-30T19:59:59.192', '2022-10-30T19:00:00.134'),
 '202310': ('2023-10-29T19:59:55.716', '2023-10-29T19:00:00.094')}
MONTHS = sorted(set(PAIRS) | {d.replace('-', '')[:6] for d in DATES})


def load(path):
    return json.loads(path.read_text())


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def code_files():
    return [Path('scripts/clock-012.py'), Path('src/forex_demo_lab/source_clock.py'),
            Path('tests/test_source_clock.py'), PLAN, Path('scripts/capture-ticks.py'),
            Path('src/forex_demo_lab/tick_audit.py'), Path('src/forex_demo_lab/collection.py')]


def freeze():
    HISTORY['verify']()
    if LEDGER.exists() or ARCHIVE.exists():
        raise FileExistsError('Clock study already frozen')
    with zipfile.ZipFile(ARCHIVE, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for path in code_files():
            z.write(path, path.as_posix())
    write(LEDGER, {'declared_utc': datetime.now(timezone.utc).isoformat(),
        'files': {p.as_posix(): sha256(p) for p in code_files()}, 'archive_sha256': sha256(ARCHIVE),
        'source_bindings': {m: HISTORY['binding'](HISTORY['ROOT'] / m, m) for m in MONTHS},
        'reference_sha256': sha256(Path('data/history-009-mt5-reference/rates.csv')),
        'dates': DATES, 'pairs': PAIRS,
        'new_york_zoneinfo_sha256': sha256(Path('/usr/share/zoneinfo/America/New_York')),
        'absolute_utc_verified': False, 'performance_evaluation_ready': False})
    print(f'Frozen {len(MONTHS)} source months, eight boundaries, eleven event anchors')


def verify():
    ledger = load(LEDGER)
    HISTORY['verify']()
    if (ledger['dates'] != list(DATES) or ledger['pairs'] != {m: list(v) for m, v in PAIRS.items()}
            or any(sha256(Path(p)) != digest for p, digest in ledger['files'].items())
            or sha256(ARCHIVE) != ledger['archive_sha256']
            or sha256(Path('data/history-009-mt5-reference/rates.csv')) != ledger['reference_sha256']):
        raise ValueError('Frozen clock inputs changed')
    for month, binding in ledger['source_bindings'].items():
        if HISTORY['binding'](HISTORY['ROOT'] / month, month) != binding:
            raise ValueError('Original monthly source changed')
    return ledger


def capture():
    verify()
    for day in DATES:
        folder = ROOT / day
        if folder.exists():
            metadata, ticks, start, end = checked_capture(folder)
            expected = int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()*1000)
            if (start, end) != (expected + 12*HOUR, expected + 18*HOUR) or metadata['account_type'] != 'demo':
                raise ValueError('Changed or incomplete existing anchor capture')
            print(f'{day}: validated existing capture', flush=True)
            continue
        subprocess.run([sys.executable, str(Path(__file__).with_name('capture-ticks.py')),
            '--terminal', r'C:\Program Files\MetaTrader 5\terminal64.exe', '--start', day+'T12:00:00Z',
            '--end', day+'T18:00:00Z', '--output', str(folder)], check=True, timeout=300)
        checked_capture(folder)
        print(f'{day}: captured', flush=True)


def month_rows(month):
    # Preserve raw order. SequenceClock, rather than the old strict monotonic
    # reader, validates the single declared backward episode.
    folder = HISTORY['ROOT'] / month
    with zipfile.ZipFile(folder / 'original.zip') as z:
        with z.open(f'DAT_ASCII_EURUSD_T_{month}.csv') as b, io.TextIOWrapper(b, encoding='utf-8-sig', newline='') as f:
            for i, row in enumerate(csv.reader(f)):
                if len(row) != 4:
                    raise ValueError('Invalid source schema')
                value = row[0]
                if len(value) != 18 or value[8] != ' ' or not (value[:8]+value[9:]).isascii() or not (value[:8]+value[9:]).isdigit() or value[:6] != month:
                    raise ValueError('Invalid raw source label')
                stamp = datetime(int(value[:4]), int(value[4:6]), int(value[6:8]), int(value[9:11]),
                    int(value[11:13]), int(value[13:15]), int(value[15:])*1000)
                bid, ask, volume = map(float, row[1:])
                if not all(math.isfinite(v) for v in (bid, ask, volume)) or volume < 0:
                    raise ValueError('Invalid raw quote/volume')
                yield {'sequence': i, 'source_label': stamp, 'bid': bid, 'ask': ask, 'volume': volume}


def chronology():
    ledger = verify()
    reference = references(Path('data/history-009-mt5-reference/rates.csv'))
    results = []
    for month in sorted(PAIRS):
        path = Path(f'reports/clock-012-sequence-{month}.json')
        if path.exists():
            raise FileExistsError('Sequence report already exists')
        before, after = map(datetime.fromisoformat, PAIRS[month])
        spring = month.endswith('03')
        clock = SequenceClock(Boundary(month, before, after, 5 if spring else 4, 4 if spring else 5))
        source_payload, mapped_payload = hashlib.sha256(), hashlib.sha256()
        bars, gaps, first, previous, equal_ms = {}, [], None, None, 0
        for tick in month_rows(month):
            mapped = clock.map(tick)
            stamp = mapped['candidate_time']
            source_payload.update(struct.pack('>ddd', tick['bid'], tick['ask'], tick['volume']))
            mapped_payload.update(struct.pack('>ddd', mapped['bid'], mapped['ask'], mapped['volume']))
            first = first or stamp
            if previous is not None:
                delta = (stamp - previous).total_seconds()
                equal_ms += delta == 0
                if delta > 3600:
                    gaps.append({'after_candidate_label': previous.isoformat(), 'before_candidate_label': stamp.isoformat(), 'seconds': delta, 'classification': 'unclassified'})
            previous = stamp
            hour = stamp.replace(minute=0, second=0, microsecond=0)
            bars[hour] = mapped['bid']
        clock.finish()
        if source_payload.digest() != mapped_payload.digest():
            raise ValueError('Converted quote payload differs')
        start = before.replace(hour=21, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        comparisons = []
        for i in range(6):
            hour = start + timedelta(hours=i)
            broker = int(hour.timestamp()*1000) + (3 if spring else 2)*HOUR
            comparisons.append({'candidate_utc_hour': hour.isoformat(), 'candidate_close': bars.get(hour),
                'broker_alternatives': [{'shift_hours': shift, 'reference_close': reference.get(broker+shift*HOUR, {}).get('close'),
                    'absolute_difference_pips': abs(bars[hour]-reference[broker+shift*HOUR]['close'])/.0001
                    if hour in bars and broker+shift*HOUR in reference else None} for shift in (-1, 0, 1)]})
        result = {'month': month, 'source_binding': ledger['source_bindings'][month],
            'ticks_preserved': clock.sequence, 'transition_sequence_zero_based': clock.transition_sequence,
            'first_candidate_label': first.isoformat(), 'last_candidate_label': previous.isoformat(),
            'source_payload_sha256': source_payload.hexdigest(), 'mapped_payload_sha256': mapped_payload.hexdigest(),
            'same_millisecond_events': equal_ms, 'candidate_gaps_over_one_hour': gaps,
            'six_hour_boundary_comparisons': comparisons, 'candidate_chronology_monotonic': True,
            'absolute_utc_verified': False, 'performance_evaluation_ready': False}
        write(path, result)
        results.append({'month': month, 'report_sha256': sha256(path), 'ticks': clock.sequence})
        print(f'{month}: {clock.sequence} events preserved; transition at row {clock.transition_sequence+1}', flush=True)
    write(Path('reports/clock-012-sequences.json'), {'ledger_sha256': sha256(LEDGER), 'months': results,
        'ticks': sum(r['ticks'] for r in results), 'performance_evaluation_ready': False})


def group(stats, minute, bid):
    item = stats.setdefault(minute, {'ticks': 0, 'low': bid, 'high': bid})
    item['ticks'] += 1
    item['low'], item['high'] = min(item['low'], bid), max(item['high'], bid)


def screen(stats, minute):
    def item(m):
        row = stats.get(m)
        return {**row, 'range_pips': (row['high']-row['low'])/.0001} if row else None
    event, controls = item(minute), [item(minute-timedelta(hours=1)), item(minute+timedelta(hours=1))]
    return {'event': event, 'controls': controls, 'passed': activity_passes(event, controls)}


def anchors():
    verify()
    if sha256(Path('/usr/share/zoneinfo/America/New_York')) != load(LEDGER)['new_york_zoneinfo_sha256']:
        raise ValueError('Historical UTC conversion database changed')
    results = []
    for day in DATES:
        month = day.replace('-', '')[:6]
        source_hour = 7 if month.endswith('11') else 8
        source_event = datetime.fromisoformat(day).replace(hour=source_hour, minute=30)
        desired = {source_event + timedelta(hours=h) for h in (-1, 0, 1)}
        hist = {}
        for stamp, bid, ask in HISTORY['raw_rows'](HISTORY['ROOT'] / month, month):
            minute = stamp.replace(second=0, microsecond=0)
            if minute in desired:
                group(hist, minute, bid)
        folder = ROOT / day
        metadata, ticks, lower, upper = checked_capture(folder)
        start = int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()*1000)
        if (lower, upper) != (start+12*HOUR, start+18*HOUR) or metadata['account_type'] != 'demo':
            raise ValueError('Anchor capture bounds/account mismatch')
        broker_event = source_event.replace(hour=14 if month.endswith('11') else 15)
        desired = {broker_event + timedelta(hours=h) for h in (-1, 0, 1)}
        broker = {}
        for tick in ticks:
            minute = datetime.fromtimestamp(tick['time_msc']/1000, timezone.utc).replace(tzinfo=None, second=0, microsecond=0)
            if minute in desired:
                group(broker, minute, tick['bid'])
        official_utc = datetime.fromisoformat(day).replace(hour=8, minute=30, tzinfo=ZoneInfo('America/New_York')).astimezone(timezone.utc)
        results.append({'day': day, 'official_release_url': f'https://www.bls.gov/news.release/archives/empsit_{day[5:7]}{day[8:10]}{day[:4]}.htm',
            'official_utc': official_utc.isoformat(), 'histdata_event_label': source_event.isoformat(),
            'broker_event_label': broker_event.isoformat(), 'histdata': screen(hist, source_event),
            'broker': screen(broker, broker_event), 'capture_sha256': sha256(folder/'capture.json')})
        print(f'{day}: HistData={results[-1]["histdata"]["passed"]}, broker={results[-1]["broker"]["passed"]}', flush=True)
    write(Path('reports/clock-012-anchors.json'), {'ledger_sha256': sha256(LEDGER), 'events': results,
        'all_anchor_screens_passed': all(r['histdata']['passed'] and r['broker']['passed'] for r in results),
        'absolute_annual_clock_verified': False, 'performance_evaluation_ready': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'verify', 'capture', 'chronology', 'anchors'))
    args = parser.parse_args()
    {'freeze': freeze, 'verify': verify, 'capture': capture, 'chronology': chronology, 'anchors': anchors}[args.action]()

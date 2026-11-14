"""Candidate correction diagnostic with exact replay lineage; no dataset approval."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import runpy
import struct
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from forex_demo_lab.corrected_clock import Replay, corrected_events

STUDY = runpy.run_path(str(Path(__file__).with_name('clock-012.py')))
PLAN = Path('docs/CORRECTION-013-PLAN.md')
LEDGER = Path('reports/correction-013-ledger.json')
ARCHIVE = Path('reports/correction-013-source.zip')
SHA, LOAD, WRITE = STUDY['sha256'], STUDY['load'], STUDY['write']
PROOF = Path('reports/clock-012-repeat-content.json')
ZONE = Path('/usr/share/zoneinfo/Europe/Athens')


def files():
    return [PLAN, Path('scripts/correct-clock-013.py'), Path('src/forex_demo_lab/corrected_clock.py'),
            Path('tests/test_corrected_clock.py'), Path('scripts/clock-012.py'),
            Path('src/forex_demo_lab/source_clock.py')]


def freeze():
    STUDY['verify']()
    if LEDGER.exists() or ARCHIVE.exists():
        raise FileExistsError('Correction already frozen')
    proof = LOAD(PROOF)
    if len(proof['months']) != 4 or not all(r['all_ordered_timestamps_quotes_volumes_identical'] for r in proof['months']):
        raise ValueError('Exact replay proof missing')
    with zipfile.ZipFile(ARCHIVE, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for path in files():
            z.write(path, path.as_posix())
    replays = {}
    for r in proof['months']:
        base = LOAD(Path(f'reports/clock-012-sequence-{r["month"]}.json'))
        second, count = base['transition_sequence_zero_based'], r['second_episode_rows']
        replays[r['month']] = {'first_start': second-count, 'second_start': second, 'rows': count}
    WRITE(LEDGER, {'declared_utc': datetime.now(timezone.utc).isoformat(),
        'files': {p.as_posix(): SHA(p) for p in files()}, 'archive_sha256': SHA(ARCHIVE),
        'proof_sha256': SHA(PROOF), 'clock_012_ledger_sha256': SHA(STUDY['LEDGER']),
        'sequence_report_hashes': {m: SHA(Path(f'reports/clock-012-sequence-{m}.json')) for m in STUDY['PAIRS']},
        'zoneinfo_sha256': SHA(ZONE), 'replays': replays,
        'performance_evaluation_ready': False, 'development_posthoc': True})
    print('Frozen explicit replay ranges and calendar candidate')


def verify():
    prior = STUDY['verify']()
    ledger = LOAD(LEDGER)
    if (any(SHA(Path(p)) != v for p, v in ledger['files'].items())
            or SHA(ARCHIVE) != ledger['archive_sha256'] or SHA(PROOF) != ledger['proof_sha256']
            or SHA(ZONE) != ledger['zoneinfo_sha256'] or SHA(STUDY['LEDGER']) != ledger['clock_012_ledger_sha256']
            or any(SHA(Path(f'reports/clock-012-sequence-{m}.json')) != v for m, v in ledger['sequence_report_hashes'].items())):
        raise ValueError('Frozen correction evidence/code changed')
    return ledger, prior


def run():
    ledger, prior = verify()
    reference = STUDY['references'](Path('data/history-009-mt5-reference/rates.csv'))
    results = []
    for month in sorted(STUDY['PAIRS']):
        replay = Replay(**ledger['replays'][month]) if month in ledger['replays'] else None
        input_rows = LOAD(Path(f'reports/clock-012-sequence-{month}.json'))['ticks_preserved']
        output_count, bars, gaps, previous, first = 0, {}, [], None, None
        payload = hashlib.sha256()
        for row in corrected_events(STUDY['month_rows'](month), month, replay):
            instant = row['candidate_time']
            first = first or instant
            if previous is not None and (instant-previous).total_seconds() > 3600:
                gaps.append({'after_candidate_label': previous.isoformat(), 'before_candidate_label': instant.isoformat(),
                             'seconds': (instant-previous).total_seconds(), 'classification': 'unclassified'})
            previous = instant
            payload.update(struct.pack('>ddd', row['bid'], row['ask'], row['volume']))
            bars[instant.replace(minute=0, second=0, microsecond=0)] = row['bid']
            output_count += 1
        collapsed = replay.rows if replay else 0
        if output_count + collapsed != input_rows:
            raise ValueError('Correction row accounting differs from original audit')
        before = datetime.fromisoformat(STUDY['PAIRS'][month][0])
        start = before.replace(hour=21, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        spring = month.endswith('03')
        comparisons = []
        for i in range(6):
            hour = start + timedelta(hours=i)
            broker = int(hour.timestamp()*1000) + (3 if spring else 2)*STUDY['HOUR']
            comparisons.append({'candidate_utc_hour': hour.isoformat(), 'candidate_close': bars.get(hour),
                'broker_alternatives': [{'shift_hours': shift,
                    'reference_close': reference.get(broker+shift*STUDY['HOUR'], {}).get('close'),
                    'absolute_difference_pips': abs(bars[hour]-reference[broker+shift*STUDY['HOUR']]['close'])/.0001
                    if hour in bars and broker+shift*STUDY['HOUR'] in reference else None} for shift in (-1, 0, 1)]})
        result = {'month': month, 'source_binding': prior['source_bindings'][month],
            'original_rows': input_rows, 'candidate_rows': output_count,
            'explicit_exact_replay_rows_collapsed': collapsed, 'candidate_payload_sha256': payload.hexdigest(),
            'first_candidate_label': first.isoformat(), 'last_candidate_label': previous.isoformat(),
            'candidate_gaps_over_one_hour': gaps, 'six_hour_boundary_comparisons': comparisons,
            'replay_lineage': {**ledger['replays'][month],
                'correspondence': 'second_start+i -> first_start+i, for every i from zero through rows-1'} if replay else None,
            'canonical_raw_source_unchanged': True, 'no_quotes_fabricated': True,
            'calendar_hypothesis_certified': False, 'performance_evaluation_ready': False}
        path = Path(f'reports/correction-013-{month}.json')
        WRITE(path, result)
        results.append({'month': month, 'original_rows': input_rows, 'candidate_rows': output_count,
                        'collapsed_replay_rows': collapsed, 'report_sha256': SHA(path)})
        print(f'{month}: {output_count} candidate rows; {collapsed} explicit replay rows collapsed', flush=True)
    WRITE(Path('reports/correction-013-review.json'), {'ledger_sha256': SHA(LEDGER), 'months': results,
        'original_rows': sum(r['original_rows'] for r in results),
        'candidate_rows': sum(r['candidate_rows'] for r in results),
        'collapsed_replay_rows': sum(r['collapsed_replay_rows'] for r in results),
        'performance_evaluation_ready': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'verify', 'run'))
    args = parser.parse_args()
    {'freeze': freeze, 'verify': verify, 'run': run}[args.action]()

"""Post-hypothesis content check: distinguish clock folds from exact replay."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import runpy
import struct


def main():
    study = runpy.run_path(str(Path(__file__).with_name('clock-012.py')))
    ledger = study['verify']()
    results = []
    for month in ('202010', '202110', '202210', '202310'):
        previous = None
        repeated = False
        first, second = [], []
        boundary = datetime.fromisoformat(study['PAIRS'][month][1])
        hour = boundary.replace(minute=0, second=0, microsecond=0)
        for row in study['month_rows'](month):
            stamp = row['source_label']
            if previous is not None and stamp < previous:
                if repeated or stamp != boundary:
                    raise ValueError('Unexpected source reversal')
                repeated = True
            if stamp.replace(minute=0, second=0, microsecond=0) == hour:
                record = stamp.isoformat().encode('ascii') + struct.pack('>ddd', row['bid'], row['ask'], row['volume'])
                (second if repeated else first).append(record)
            previous = stamp
        result = {'month': month, 'source_binding': ledger['source_bindings'][month],
            'source_hour': hour.isoformat(), 'first_episode_rows': len(first), 'second_episode_rows': len(second),
            'first_episode_sha256': hashlib.sha256(b''.join(first)).hexdigest(),
            'second_episode_sha256': hashlib.sha256(b''.join(second)).hexdigest(),
            'all_ordered_timestamps_quotes_volumes_identical': bool(first and first == second),
            'no_rows_removed': True, 'performance_evaluation_ready': False}
        results.append(result)
        print(f'{month}: {len(first)}/{len(second)} rows; exact replay={result["all_ordered_timestamps_quotes_volumes_identical"]}', flush=True)
    output = {'kind': 'post_hypothesis_duplicate_hour_diagnostic', 'script_sha256': study['sha256'](Path(__file__)),
              'ledger_sha256': study['sha256'](study['LEDGER']), 'months': results,
              'performance_evaluation_ready': False}
    study['write'](Path('reports/clock-012-repeat-content.json'), output)


if __name__ == '__main__':
    main()

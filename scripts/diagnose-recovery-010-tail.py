"""Post-failure cross-source tail diagnostic; no repair, gate or UTC approval."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import runpy
from statistics import median
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from forex_demo_lab.reconstruction import checked_capture
from forex_demo_lab.tick_audit import sha256


def main():
    history = runpy.run_path(str(Path(__file__).with_name('history-009.py')))
    history['verify']()
    folder = Path('data/history-009-raw/202307')
    binding = history['binding'](folder, '202307')
    audit = history['load'](Path('reports/history-009-raw-202307.json'))
    if not audit['structural_checks_passed'] or any(audit[k] != v for k, v in binding.items()):
        raise ValueError('Original HistData source changed or failed')
    metadata, broker, lower, upper = checked_capture(Path('data/recovery-010/mismatch-repeat'))
    source_start = datetime(2023, 7, 14, 15)
    source_end = source_start + timedelta(hours=1)
    if lower != int((source_start + timedelta(hours=7)).replace(tzinfo=timezone.utc).timestamp()*1000):
        raise ValueError('Wrong broker diagnostic interval')
    source = []
    for stamp, bid, ask in history['raw_rows'](folder, '202307'):
        if stamp >= source_end:
            break
        if stamp >= source_start:
            source.append((stamp, bid, ask))
    last = datetime.fromtimestamp(broker[-1]['time_msc']/1000, timezone.utc).replace(tzinfo=None) - timedelta(hours=7)
    tail = [row for row in source if row[0] > last]
    source_minutes = {t.replace(second=0, microsecond=0): bid for t, bid, ask in source if t <= last}
    broker_minutes = {}
    for tick in broker:
        raw = datetime.fromtimestamp(tick['time_msc']/1000, timezone.utc).replace(tzinfo=None) - timedelta(hours=7)
        broker_minutes[raw.replace(second=0, microsecond=0)] = tick['bid']
    differences = [abs(bid - broker_minutes[minute])/.0001 for minute, bid in source_minutes.items()
                   if minute in broker_minutes]
    result = {'kind': 'post_failure_conditional_tail_diagnostic', 'assumed_broker_minus_histdata_hours': 7,
        'source_binding': binding, 'script_sha256': sha256(Path(__file__)),
        'broker_capture_sha256': sha256(Path('data/recovery-010/mismatch-repeat/capture.json')),
        'source_hour': source_start.isoformat(), 'source_ticks': len(source),
        'broker_ticks': len(broker), 'last_broker_tick_in_assumed_source_clock': last.isoformat(),
        'histdata_ticks_after_last_broker_tick': len(tail),
        'first_histdata_tail_label': tail[0][0].isoformat() if tail else None,
        'last_histdata_tail_label': tail[-1][0].isoformat() if tail else None,
        'overlapping_minute_closes': len(differences),
        'median_close_difference_pips': median(differences) if differences else None,
        'maximum_close_difference_pips': max(differences) if differences else None,
        'source_hour_bid_close': source[-1][1], 'last_broker_bid': broker[-1]['bid'],
        'absolute_utc_verified': False, 'performance_evaluation_ready': False,
        'interpretation': 'Conditional tail evidence only; not full-feed validation, a mixed replacement dataset or a revised gate'}
    with Path('reports/recovery-010-tail-diagnostic.json').open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

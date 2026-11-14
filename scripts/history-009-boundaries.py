"""Complete raw gap/seam inventory, including months rejected by strict ordering."""
import csv
from datetime import datetime
import io
from pathlib import Path
import runpy
import zipfile


def run():
    history = runpy.run_path(str(Path(__file__).with_name('history-009.py')))
    history['verify']()
    load, sha, write = history['load'], history['sha256'], history['write_json']
    review_path = Path('reports/history-009-review.json')
    review = load(review_path)
    if len(review['months']) != 48 or [r['month'] for r in review['months']] != list(history['MONTHS']):
        raise ValueError('Incomplete or mismatched review inventory')
    months = []
    for entry in review['months']:
        report_path = Path(entry['report'])
        if sha(report_path) != entry['report_sha256']:
            raise ValueError('Reviewed report changed')
        row = load(report_path)
        folder = history['ROOT'] / entry['month']
        if any(row[k] != v for k, v in history['binding'](folder, entry['month']).items()):
            raise ValueError('Raw archive changed')
        if entry['status'] == 'structural_pass':
            first, last, gaps = row['first_source_label'], row['last_source_label'], row['gaps_over_one_hour']
        else:
            first = last = previous = None
            gaps = []
            with zipfile.ZipFile(folder / 'original.zip') as z:
                with z.open(f'DAT_ASCII_EURUSD_T_{entry["month"]}.csv') as b, io.TextIOWrapper(b, encoding='utf-8-sig', newline='') as f:
                    for record in csv.reader(f):
                        label = record[0]
                        stamp = datetime(int(label[:4]), int(label[4:6]), int(label[6:8]), int(label[9:11]),
                                         int(label[11:13]), int(label[13:15]), int(label[15:]) * 1000)
                        first = first or stamp.isoformat()
                        last = stamp.isoformat()
                        if previous is not None and (stamp - previous).total_seconds() > 3600:
                            gaps.append({'after_source_label': previous.isoformat(), 'before_source_label': stamp.isoformat(),
                                         'seconds': (stamp - previous).total_seconds(), 'classification': 'unreviewed'})
                        previous = stamp  # Keep observed sequence, including backward transitions.
        months.append({'month': entry['month'], 'first_source_label': first, 'last_source_label': last,
                       'gaps_over_one_hour': gaps, 'original_status': entry['status'],
                       'backward_transitions': row.get('defect_counts', {}).get('backward_source_timestamp', 0)})
    seams = [{'after_month': a['month'], 'before_month': b['month'], 'after_source_label': a['last_source_label'],
              'before_source_label': b['first_source_label'], 'seconds':
              (datetime.fromisoformat(b['first_source_label']) - datetime.fromisoformat(a['last_source_label'])).total_seconds(),
              'classification': 'unreviewed'} for a, b in zip(months, months[1:])]
    write(Path('reports/history-009-boundaries.json'), {'review_sha256': sha(review_path), 'source_sha256': sha(Path(__file__)),
          'months': months, 'month_boundaries': seams, 'performance_evaluation_ready': False,
          'note': 'Raw-label differences only; weekend/holiday closures and clock discontinuities are not classified as eligible'})
    print(f'Recorded {len(seams)} seams and {sum(len(m["gaps_over_one_hour"]) for m in months)} raw gaps over one hour')


if __name__ == '__main__':
    run()

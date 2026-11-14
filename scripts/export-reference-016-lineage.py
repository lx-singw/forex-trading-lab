"""Publish diagnostic minute lineage and independently check every saved row."""
import csv
from datetime import datetime
import io
import json
from pathlib import Path
import runpy
import zipfile

from forex_demo_lab.reference import DAYS
from forex_demo_lab.reference_boundary import parse
from forex_demo_lab.tick_audit import sha256
from forex_demo_lab.cli import write_json


def main():
    runner=runpy.run_path('scripts/reference-016b.py'); runner['preflight']();runner['verify']()
    path=Path('data/reference-016/diagnostic-minute-lineage.csv')
    meta=Path('data/reference-016/diagnostic-minute-lineage.json')
    if path.exists() or meta.exists():raise FileExistsError('Lineage publication already exists')
    fields=['source_day','source_row','source_date','source_time','reference_time_msc','open','high','low','close']
    count=0
    with path.open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for day in sorted(DAYS):
            with zipfile.ZipFile(Path('data/reference-016')/day/'original.zip') as z:
                with z.open(datetime.fromisoformat(day).strftime('%d%m%y.txt')) as binary:
                    for row in parse(io.TextIOWrapper(binary,encoding='ascii'),day):
                        writer.writerow(row);count+=1
    # Read original fields and row numbers independently; calendar arithmetic
    # comes from the separate frozen checker, not the adapter or IANA converter.
    checker=runpy.run_path('scripts/check-reference-016b.py')
    checked=0
    with path.open(newline='') as saved:
        rows=csv.DictReader(saved)
        if rows.fieldnames!=fields:raise ValueError('Lineage schema differs')
        for day in sorted(DAYS):
            with zipfile.ZipFile(Path('data/reference-016')/day/'original.zip') as z:
                with z.open(datetime.fromisoformat(day).strftime('%d%m%y.txt')) as binary:
                    source=csv.reader(io.TextIOWrapper(binary,encoding='ascii'));next(source)
                    for number,original in enumerate(source,2):
                        if original[0]!='EURUSD':continue
                        saved_row=next(rows,None)
                        if saved_row is None:raise ValueError('Lineage truncated')
                        local=datetime.strptime(original[1]+original[2],'%Y%m%d%H%M%S')
                        expected={'source_day':day,'source_row':str(number),'source_date':original[1],
                            'source_time':original[2],'reference_time_msc':str(checker['manual_utc'](local)),
                            **dict(zip(('open','high','low','close'),original[3:]))}
                        if expected!=saved_row:raise ValueError('Independent minute lineage differs')
                        checked+=1
        if next(rows,None) is not None:raise ValueError('Extra lineage row')
    review=json.loads(Path('reports/reference-016b-review.json').read_text())
    if count!=checked or count!=review['reference_eurusd_rows']:raise ValueError('Lineage count differs')
    write_json(meta,{'kind':'diagnostic_minute_reference_lineage_016','rows':count,
        'data_sha256':sha256(path),'ledger_sha256':sha256(Path('reports/reference-016b-ledger.json')),
        'review_sha256':sha256(Path('reports/reference-016b-review.json')),
        'exporter_sha256':sha256(Path(__file__)),'independent_original_row_checks':checked,
        'bar_start_or_end_semantics':'unverified_literal_labels_only',
        'absolute_utc_certified':False,'performance_evaluation_ready':False,'demo_execution_ready':False})
    print(json.dumps({'saved_minute_rows':count,'independent_lineage_rows_checked':checked}),flush=True)


if __name__=='__main__':main()

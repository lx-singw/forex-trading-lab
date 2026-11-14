"""Independent original-row accounting. No primary parser imports or functions."""
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def account(path, month):
    year, number = map(int, month.split('-'))
    begin = datetime(year, number, 1, tzinfo=timezone.utc)
    finish = datetime(year + (number == 12), number % 12 + 1, 1, tzinfo=timezone.utc)
    hourly = {}
    moment = begin
    while moment < finish:
        hourly[moment.isoformat(timespec='seconds').replace('+00:00', 'Z')] = 0
        moment += timedelta(hours=1)
    result = dict(rows=0, valid_rows=0, first=None, last=None, tied_timestamps=0,
                  exact_duplicate_records=0, backward_timestamps=0, hour_counts=hourly,
                  long_gaps=[], uncompressed_bytes=0, members=[])
    errors = Counter()
    original_records = 0
    previous = None
    group = set()
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        assert 0 < len(entries) <= 64
        assert len({e.filename for e in entries}) == len(entries)
        assert sum(e.file_size for e in entries) <= 256 * 1024 * 1024
        # Central-directory CRC check precedes CSV interpretation and respects size bounds.
        for entry in entries:
            assert not entry.flag_bits & 1
            assert re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_.-]*', entry.filename.rstrip('/'))
            assert '..' not in entry.filename
            if entry.is_dir():
                assert entry.file_size == 0
                continue
            assert entry.filename.lower().endswith('.csv')
            result['members'].append(entry.filename)
            read_size = 0
            with archive.open(entry) as stream:
                while block := stream.read(65536):
                    read_size += len(block)
                    assert read_size <= 256 * 1024 * 1024
            assert read_size == entry.file_size
            result['uncompressed_bytes'] += read_size
            assert result['uncompressed_bytes'] <= 256 * 1024 * 1024
            with archive.open(entry) as stream:
                rows = csv.reader(io.TextIOWrapper(stream, encoding='utf-8', newline=''), strict=True)
                header = next(rows, None)
                header_ok = header == ['Exness', 'Symbol', 'Timestamp', 'Bid', 'Ask']
                if not header_ok:
                    errors['header'] += 1
                for row in rows:
                    original_records += 1
                    if not header_ok:
                        continue
                    result['rows'] += 1
                    if len(row) != 5:
                        errors['field_count'] += 1
                        continue
                    if row[0] != 'Exness' or row[1] != 'EURUSD':
                        errors['provider_or_symbol'] += 1
                        continue
                    stamp = row[2]
                    try:
                        if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z', stamp):
                            raise ValueError()
                        clock = datetime(int(stamp[:4]), int(stamp[5:7]), int(stamp[8:10]),
                                         int(stamp[11:13]), int(stamp[14:16]), int(stamp[17:19]),
                                         int(stamp[20:23]) * 1000, tzinfo=timezone.utc)
                    except ValueError:
                        errors['timestamp'] += 1
                        continue
                    if clock < begin or clock >= finish:
                        errors['month_boundary'] += 1
                        continue
                    try:
                        bid, ask = Fraction(row[3]), Fraction(row[4])
                        if bid <= 0 or ask < bid:
                            raise ValueError()
                    except (ValueError, ZeroDivisionError):
                        errors['price'] += 1
                        continue
                    result['valid_rows'] += 1
                    hourly[stamp[:13] + ':00:00Z'] += 1
                    if result['first'] is None:
                        result['first'] = stamp
                    result['last'] = stamp
                    if previous is not None:
                        if clock < previous:
                            result['backward_timestamps'] += 1
                            errors['backward_timestamp'] += 1
                        elif clock == previous:
                            result['tied_timestamps'] += 1
                        elif clock - previous > timedelta(hours=1):
                            delta = clock - previous
                            result['long_gaps'].append(dict(before=int(previous.timestamp()) * 1000 + previous.microsecond // 1000,
                                                           after=int(clock.timestamp()) * 1000 + clock.microsecond // 1000,
                                                           milliseconds=delta.days * 86400000 + delta.seconds * 1000 + delta.microseconds // 1000))
                    if clock != previous:
                        group = set()
                    if tuple(row) in group:
                        result['exact_duplicate_records'] += 1
                    group.add(tuple(row))
                    previous = clock
    result['errors'] = dict(errors)
    result['observed_hours'] = sum(n != 0 for n in hourly.values())
    result['empty_hours'] = sum(n == 0 for n in hourly.values())
    return result, original_records


def main():
    ledger_path = ROOT / 'reports/exness-024-ledger.json'
    assert digest(ledger_path) == ledger_path.with_suffix('.sha256').read_text().strip()
    ledger = json.loads(ledger_path.read_text())
    for name, expected in ledger['bindings'].items():
        assert digest(ROOT / name) == expected, name
    audit_path = ROOT / 'reports/exness-024-audit.json'
    assert digest(audit_path) == audit_path.with_suffix('.sha256').read_text().strip()
    main_audit = json.loads(audit_path.read_text())
    reviews = []
    for month in main_audit['months']:
        independent, original_records = account(ROOT / month['source_path'], month['month'])
        matches = {key: value == month[key] for key, value in independent.items()}
        reviews.append(dict(month=month['month'], original_records=original_records,
                            matches=matches, passed=all(matches.values()), independent=independent))
    output = dict(kind='independent_original_row_review_024', months=reviews,
                  passed=all(m['passed'] for m in reviews), audit_sha256=digest(audit_path),
                  ledger_sha256=digest(ledger_path), annual_eligible=False, orders_available=False)
    path = ROOT / 'reports/exness-024-checks.json'
    with path.open('x') as stream:
        json.dump(output, stream, indent=2, sort_keys=True)
        stream.write('\n')
    with path.with_suffix('.sha256').open('x') as stream:
        stream.write(digest(path) + '\n')
    print(json.dumps([dict(month=m['month'], original_records=m['original_records'],
                           passed=m['passed'], mismatches=[k for k,v in m['matches'].items() if not v]) for m in reviews]))


if __name__ == '__main__':
    main()

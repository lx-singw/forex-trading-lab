"""Bounded, lossless diagnostic inspection; never supplies strategy inputs."""
from __future__ import annotations

import csv
import io
import re
import zipfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

HEADER = ['Exness', 'Symbol', 'Timestamp', 'Bid', 'Ask']
STAMP = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}Z', re.ASCII)
SAFE_NAME = re.compile(r'[A-Za-z0-9_-][A-Za-z0-9_.-]*', re.ASCII)
MAX_MEMBERS = 64
MAX_UNCOMPRESSED = 256 * 1024 * 1024
MAX_COMBINED = 512 * 1024 * 1024
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def month_bounds(month: str):
    start = datetime.strptime(month, '%Y-%m').replace(tzinfo=timezone.utc)
    end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return start, end


def timestamp_ms(value: str) -> int:
    if STAMP.fullmatch(value) is None:
        raise ValueError('timestamp_format')
    stamp = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
    delta = stamp - EPOCH
    return delta.days * 86400000 + delta.seconds * 1000 + delta.microseconds // 1000


def inspect_archive(archive: zipfile.ZipFile, max_members=MAX_MEMBERS,
                    max_uncompressed=MAX_UNCOMPRESSED) -> tuple[list, int]:
    entries = archive.infolist()
    if not entries or len(entries) > max_members:
        raise ValueError('archive_member_count')
    names = set()
    declared = 0
    files = []
    for entry in entries:
        name = entry.filename
        bare = name[:-1] if entry.is_dir() else name
        if (SAFE_NAME.fullmatch(bare) is None or '..' in bare or name in names
                or entry.flag_bits & 1):
            raise ValueError('archive_member_name_or_encryption')
        names.add(name)
        if entry.is_dir():
            if entry.file_size != 0:
                raise ValueError('nonempty_directory')
        elif not name.lower().endswith('.csv'):
            raise ValueError('non_csv_member')
        else:
            files.append(entry)
        declared += entry.file_size
        if declared > max_uncompressed:
            raise ValueError('archive_uncompressed_cap')
    if not files:
        raise ValueError('no_csv_members')
    # Complete CRC validation is bounded even if headers lie about output sizes.
    actual = 0
    for entry in entries:
        member_bytes = 0
        with archive.open(entry) as source:
            while True:
                block = source.read(min(65536, max_uncompressed - actual + 1))
                if not block:
                    break
                actual += len(block)
                member_bytes += len(block)
                if actual > max_uncompressed:
                    raise ValueError('archive_actual_uncompressed_cap')
        if member_bytes != entry.file_size:
            raise ValueError('member_size_mismatch')
    return files, actual


def audit_month(path: Path, month: str, *, max_members=MAX_MEMBERS,
                max_uncompressed=MAX_UNCOMPRESSED) -> dict:
    start, end = month_bounds(month)
    start_ms = int((start - EPOCH).total_seconds()) * 1000
    end_ms = int((end - EPOCH).total_seconds()) * 1000
    hourly = { (start + timedelta(hours=h)).strftime('%Y-%m-%dT%H:00:00Z'): 0
               for h in range((end - start).days * 24) }
    errors = Counter()
    examples = {}
    result = dict(month=month, source_path=str(path), members=[], rows=0,
                  valid_rows=0, first=None, last=None, tied_timestamps=0,
                  exact_duplicate_records=0, backward_timestamps=0,
                  hour_counts=hourly, long_gaps=[], uncompressed_bytes=0,
                  errors={}, error_examples={}, diagnostic_pass=False,
                  performance_evaluation_ready=False, annual_eligible=False,
                  market_profitability_established=False, orders_available=False)

    def issue(kind, member, record, row=None):
        errors[kind] += 1
        samples = examples.setdefault(kind, [])
        if len(samples) < 20:
            samples.append(dict(member=member, csv_record=record, fields=row))

    previous = None
    seen_at_time = set()
    try:
        with zipfile.ZipFile(path) as archive:
            members, size = inspect_archive(archive, max_members, max_uncompressed)
            result['uncompressed_bytes'] = size
            result['members'] = [entry.filename for entry in members]
            for entry in members:
                with archive.open(entry) as binary:
                    with io.TextIOWrapper(binary, encoding='utf-8', newline='') as stream:
                        reader = csv.reader(stream, strict=True)
                        header = next(reader, None)
                        if header != HEADER:
                            issue('header', entry.filename, 1, header)
                            continue
                        for record, row in enumerate(reader, 2):
                            result['rows'] += 1
                            if len(row) != 5:
                                issue('field_count', entry.filename, record, row)
                                continue
                            if row[:2] != ['exness', 'EURUSD']:
                                issue('provider_or_symbol', entry.filename, record, row)
                                continue
                            try:
                                current = timestamp_ms(row[2])
                            except ValueError:
                                issue('timestamp', entry.filename, record, row)
                                continue
                            if not start_ms <= current < end_ms:
                                issue('month_boundary', entry.filename, record, row)
                                continue
                            try:
                                bid, ask = Decimal(row[3]), Decimal(row[4])
                                if not (bid.is_finite() and ask.is_finite() and bid > 0 and ask >= bid):
                                    raise ValueError('price')
                            except (InvalidOperation, ValueError):
                                issue('price', entry.filename, record, row)
                                continue
                            result['valid_rows'] += 1
                            hour = row[2][:13].replace(' ', 'T') + ':00:00Z'
                            hourly[hour] += 1
                            if result['first'] is None:
                                result['first'] = row[2]
                            result['last'] = row[2]
                            if previous is not None:
                                difference = current - previous
                                if difference < 0:
                                    result['backward_timestamps'] += 1
                                    issue('backward_timestamp', entry.filename, record, row)
                                if difference == 0:
                                    result['tied_timestamps'] += 1
                                if difference > 3600000:
                                    result['long_gaps'].append(dict(before=previous, after=current,
                                                                   milliseconds=difference))
                            if current != previous:
                                seen_at_time.clear()
                            exact = tuple(row)
                            if exact in seen_at_time:
                                result['exact_duplicate_records'] += 1
                            seen_at_time.add(exact)
                            previous = current
    except (zipfile.BadZipFile, ValueError, UnicodeError, csv.Error, EOFError,
            RuntimeError, OSError, NotImplementedError) as error:
        # Do not leak full exception text or any unrelated filesystem information.
        issue('archive_or_stream_failure', None, None, [type(error).__name__])
    result['errors'] = dict(errors)
    result['error_examples'] = examples
    result['observed_hours'] = sum(value > 0 for value in hourly.values())
    result['empty_hours'] = sum(value == 0 for value in hourly.values())
    result['diagnostic_pass'] = not errors and result['rows'] > 0
    return result

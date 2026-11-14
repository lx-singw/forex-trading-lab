"""Create separately versioned parsers with an exact, testable diff contract."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPLACEMENTS = {
    'src/forex_demo_lab/exness_diagnostics.py': (
        ('src/forex_demo_lab/exness_diagnostics_b.py'),
        ((r'T\d{2}:\d{2}:\d{2}\.\d{3}Z', r' \d{2}:\d{2}:\d{2}\.\d{3}Z'),
         ("'%Y-%m-%dT%H:%M:%S.%fZ'", "'%Y-%m-%d %H:%M:%S.%fZ'"),
         ("row[:2] != ['Exness', 'EURUSD']", "row[:2] != ['exness', 'EURUSD']"),
         ("hour = row[2][:13] + ':00:00Z'", "hour = row[2][:13].replace(' ', 'T') + ':00:00Z'"))),
    'scripts/check-exness-024.py': (
        'scripts/check-exness-024b.py',
        ((r'T[0-9]{2}:[0-9]{2}:[0-9]{2}', r' [0-9]{2}:[0-9]{2}:[0-9]{2}'),
         ("row[0] != 'Exness'", "row[0] != 'exness'"),
         ("hourly[stamp[:13] + ':00:00Z']", "hourly[stamp[:13].replace(' ', 'T') + ':00:00Z']"),
         ('exness-024-ledger', 'exness-024b-ledger'),
         ('exness-024-audit', 'exness-024b-audit'),
         ('exness-024-checks', 'exness-024b-checks'),
         ('independent_original_row_review_024', 'independent_original_row_review_024b'))),
}


def transformed(name):
    target, replacements = REPLACEMENTS[name]
    source = (ROOT / name).read_text()
    for before, after in replacements:
        assert source.count(before) == 1, (name, before)
        source = source.replace(before, after)
    return target, source


def verify():
    for name in REPLACEMENTS:
        target, source = transformed(name)
        assert (ROOT / target).read_text() == source, target
    return True


def generate():
    original_ledger = ROOT / 'reports/exness-024-ledger.json'
    assert hashlib.sha256(original_ledger.read_bytes()).hexdigest() == original_ledger.with_suffix('.sha256').read_text().strip()
    ledger = json.loads(original_ledger.read_text())
    for name, expected in ledger['bindings'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    for name in REPLACEMENTS:
        target, source = transformed(name)
        with (ROOT / target).open('x') as stream:
            stream.write(source)
    assert verify()
    print('024B exact derivation passed; original 024 preserved')


if __name__ == '__main__':
    generate()

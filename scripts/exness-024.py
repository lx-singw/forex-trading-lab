"""Freeze and run the strict whole-month diagnostic, with exclusive outputs."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from forex_demo_lab.exness_diagnostics import MAX_COMBINED, audit_month

LEDGER = ROOT / 'reports/exness-024-ledger.json'
SOURCES = ('docs/DATA-SAMPLE-024-PLAN.md', 'docs/EXNESS-AUDIT-024-PROTOCOL.md',
           'src/forex_demo_lab/exness_diagnostics.py', 'tests/test_exness_diagnostics.py',
           'scripts/exness-024.py', 'scripts/check-exness-024.py',
           'scripts/download-exness-024.ps1', 'scripts/preflight-exness-024.py')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
    with path.with_suffix('.sha256').open('x') as stream:
        stream.write(digest(path) + '\n')


def verify():
    assert digest(LEDGER) == LEDGER.with_suffix('.sha256').read_text().strip()
    ledger = json.loads(LEDGER.read_text())
    for name, expected in ledger['bindings'].items():
        assert digest(ROOT / name) == expected, name
    return ledger


def freeze():
    names = list(SOURCES) + ['reports/exness-024-acquisition-preflight.json',
                            'reports/exness-024-local-policy-failure.json']
    for month in ('03', '07'):
        receipt_path = ROOT / f'data/exness-024/exness-2023-{month}-get.json'
        receipt = json.loads(receipt_path.read_text(encoding='utf-8-sig'))
        assert receipt['outcome'] == 'complete_original_preserved'
        original = ROOT / receipt['original_path']
        assert digest(original) == receipt['sha256']
        assert original.stat().st_size == receipt['stored_bytes'] == receipt['content_length']
        assert receipt['stored_bytes'] <= receipt['per_file_cap']
        names += [str(receipt_path.relative_to(ROOT)), receipt['original_path']]
    write(LEDGER, dict(kind='frozen_whole_month_exness_audit_024',
                       bindings={name: digest(ROOT / name) for name in names},
                       annual_eligible=False, orders_available=False))
    print('024 audit ledger frozen')


def run():
    verify()
    reports = []
    for month in ('03', '07'):
        path = Path(f'data/exness-024/Exness_EURUSD_2023_{month}.zip')
        result = audit_month(ROOT / path, f'2023-{month}')
        result['source_path'] = path.as_posix()
        result['source_sha256'] = digest(ROOT / path)
        reports.append(result)
    assert sum(r['uncompressed_bytes'] for r in reports) <= MAX_COMBINED
    output = dict(kind='strict_whole_month_diagnostic_024', months=reports,
                  diagnostic_pass=all(r['diagnostic_pass'] for r in reports),
                  ledger_sha256=digest(LEDGER), annual_eligible=False,
                  performance_evaluation_ready=False, market_profitability_established=False,
                  orders_available=False)
    write(ROOT / 'reports/exness-024-audit.json', output)
    print(json.dumps([dict(month=r['month'], rows=r['rows'], errors=r['errors'],
                           first=r['first'], last=r['last'], observed_hours=r['observed_hours'],
                           empty_hours=r['empty_hours'], diagnostic_pass=r['diagnostic_pass']) for r in reports]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['freeze', 'verify', 'run'])
    action = parser.parse_args().action
    {'freeze': freeze, 'verify': verify, 'run': run}[action]()

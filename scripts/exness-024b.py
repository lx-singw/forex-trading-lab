"""Separately frozen supplemental audit; original 024 code/reports stay sealed."""
import argparse
import json
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from forex_demo_lab.exness_diagnostics_b import MAX_COMBINED, audit_month

ORIGINAL = runpy.run_path(str(ROOT / 'scripts/exness-024.py'))
digest, write = ORIGINAL['digest'], ORIGINAL['write']
LEDGER = ROOT / 'reports/exness-024b-ledger.json'
NEW = ('docs/EXNESS-AUDIT-024B-PLAN.md', 'scripts/derive-exness-024b.py',
       'src/forex_demo_lab/exness_diagnostics_b.py', 'scripts/exness-024b.py',
       'scripts/check-exness-024b.py', 'tests/test_exness_diagnostics_b.py',
       'reports/exness-024-ledger.json', 'reports/exness-024-ledger.sha256',
       'reports/exness-024-audit.json', 'reports/exness-024-audit.sha256',
       'reports/exness-024-checks.json', 'reports/exness-024-checks.sha256')


def verify():
    assert digest(LEDGER) == LEDGER.with_suffix('.sha256').read_text().strip()
    ledger = json.loads(LEDGER.read_text())
    for name, expected in ledger['bindings'].items():
        assert digest(ROOT / name) == expected, name
    assert runpy.run_path(str(ROOT / 'scripts/derive-exness-024b.py'))['verify']()
    return ledger


def freeze():
    previous = ORIGINAL['verify']()
    bindings = dict(previous['bindings'])
    bindings.update({name: digest(ROOT / name) for name in NEW})
    assert runpy.run_path(str(ROOT / 'scripts/derive-exness-024b.py'))['verify']()
    write(LEDGER, dict(kind='supplemental_exness_format_audit_024b', bindings=bindings,
                       original_failure_preserved=True, annual_eligible=False,
                       orders_available=False))
    print('024B ledger and exact derivation frozen')


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
    output = dict(kind='supplemental_whole_month_diagnostic_024b', months=reports,
                  diagnostic_pass=all(r['diagnostic_pass'] for r in reports),
                  ledger_sha256=digest(LEDGER), annual_eligible=False,
                  performance_evaluation_ready=False, market_profitability_established=False,
                  orders_available=False)
    write(ROOT / 'reports/exness-024b-audit.json', output)
    print(json.dumps([dict(month=r['month'], rows=r['rows'], errors=r['errors'],
                           first=r['first'], last=r['last'], observed_hours=r['observed_hours'],
                           empty_hours=r['empty_hours'], ties=r['tied_timestamps'],
                           exact_duplicates=r['exact_duplicate_records'],
                           long_gaps=len(r['long_gaps']), diagnostic_pass=r['diagnostic_pass']) for r in reports]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['freeze', 'verify', 'run'])
    action = parser.parse_args().action
    {'freeze': freeze, 'verify': verify, 'run': run}[action]()

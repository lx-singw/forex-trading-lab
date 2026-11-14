"""Freeze local metadata and run one bounded receipt-clock probe; no trading."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
API = runpy.run_path(str(ROOT/'scripts/strategy-experiment-028.py'))
sha, write, sealed, load = API['sha'], API['write'], API['sealed'], API['load']
from forex_demo_lab.fresh_data_031 import DATE, VERSION, probe

PRIOR = ROOT/'reports/exit-experiment-030-final-source.json'
LEDGER = ROOT/'reports/fresh-data-031-ledger.json'
FIELDS = ('kind', 'symbol', 'synthetic', 'historical_timezone_verified',
          'complete_market_history_verified', 'broker_execution_conditions_verified',
          'absolute_utc_verified', 'performance_evaluation_ready',
          'annual_performance_eligible', 'walk_forward_performance_ready',
          'demo_execution_ready', 'blockers', 'status')
METADATA = {
    'data/eurusd-2024-2025-v1/provenance.json': 'reused_development_and_consumed_2025',
    'data/research-004-january-mt5/provenance.json': 'reused_2024_development',
    'data/research-005-april-new-york/provenance.json': 'reused_2024_development',
    'data/research-004-july-new-york/provenance.json': 'reused_2024_development',
    'data/research-005-october-new-york/provenance.json': 'blocked_2024_development',
    'data/history-009-mt5-reference/capture.json': 'historical_reference_not_executable_ticks',
    'reports/history-009-review.json': 'blocked_2020_2023_annual_source',
    'reports/normalization-015-review.json': 'blocked_2020_2023_normalization',
    'reports/labels-017-review.json': 'blocked_2020_2023_clock_coverage',
    'reports/walk-forward-014-market-gate.json': 'blocked_annual_performance',
    'reports/research-quality-004.json': 'development_only',
    'reports/research-quality-005.json': 'development_only',
    'reports/research-quality-006.json': 'blocked_development_clock',
    'reports/research-quality-007.json': 'blocked_development_clock',
}
PROBE = ROOT/'reports/fresh-data-031-probe.json'
RESERVATION = ROOT/'reports/fresh-data-031-probe-reservation.json'


def prior_verify(allow_handoff=False):
    assert sha(PRIOR) == '00531bea4604fade1b249671d7b418092faa750dd201a94e31ee272786630e34'
    previous = sealed(PRIOR)
    bindings, changes = {}, {}
    for group, values in previous.items():
        if not group.endswith('_bindings') or group == 'archive_external_bindings':
            continue
        for name, expected in values.items():
            assert name not in bindings
            actual = sha(ROOT/name)
            if actual != expected:
                assert allow_handoff and group == 'source_bindings' and name in API['HANDOFF'], name
                changes[name] = dict(previous_sha256=expected, current_sha256=actual)
            bindings[name] = expected
    external = previous['archive_external_bindings']
    assert len(bindings) == 900 and len(external) == 36
    assert all(bindings[n] == h for n,h in external.items())
    assert sha(PRIOR.with_suffix('.zip')) == previous['archive_sha256']
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist()) == 864
        assert set(z.namelist()) == set(bindings)-set(external)
        for name in z.namelist():
            assert hashlib.sha256(z.read(name)).hexdigest() == bindings[name], name
    return dict(bindings_verified=900, archived_members_verified=864,
                external_bindings_verified=36, allowed_handoff_changes=changes)


def freeze():
    assert os.name != 'nt', 'Freeze in canonical WSL workspace'
    checked = prior_verify()
    tests = sealed(ROOT/'reports/fresh-data-031-tests.json')
    assert tests['passed'] and tests['tests_run'] == tests['tests_passed'] == 400
    bindings = {}
    for pattern in ('src/**/*.py', 'scripts/*031*.py', 'tests/*031*.py', 'docs/*031*.md',
                    'reports/fresh-data-031-tests*'):
        for path in ROOT.glob(pattern):
            bindings[path.relative_to(ROOT).as_posix()] = sha(path)
    for name in METADATA:
        bindings[name] = sha(ROOT/name)
    for suffix in ('.json','.sha256','.zip'):
        path = PRIOR.with_suffix(suffix)
        bindings[path.relative_to(ROOT).as_posix()] = sha(path)
    runtime = Path('/mnt/c/Users/Linda Singwane/.forex-demo-lab/mt5-python')
    runtime_paths = [runtime/'Scripts/python.exe', *sorted((runtime/'Lib/site-packages/MetaTrader5').glob('*.pyd')),
                     runtime/'Lib/site-packages/MetaTrader5/__init__.py']
    assert len(runtime_paths) >= 3 and all(p.is_file() for p in runtime_paths)
    for path in runtime_paths:
        bindings[str(path)] = sha(path)
    outputs = ['reports/fresh-data-031-'+name+'.json' for name in ('inventory','probe','probe-reservation','checks')]
    assert not any((ROOT/name).exists() for name in outputs)
    write(LEDGER, dict(kind='bounded_fresh_data_readiness_031', version=VERSION, date=DATE,
        bindings=bindings, metadata_roles=METADATA, metadata_fields=FIELDS,
        existing_data_directories=sorted(p.name for p in (ROOT/'data').iterdir() if p.is_dir()),
        prior_snapshot_verification=checked, expected_outputs=outputs,
        max_reads=120, interval_seconds=.5, max_elapsed_seconds=60,
        terminal='C:/Program Files/MetaTrader 5/terminal64.exe',
        market_history_rows_authorized=0, strategy_replays_authorized=0,
        continuous_capture_authorized=False, fresh_performance_eligible=False,
        annual_eligible=False, orders_available=False))
    print(json.dumps(dict(frozen=True, bindings=len(bindings), metadata_files=len(METADATA))))


def bound_path(name):
    if os.name == 'nt' and name.startswith('/mnt/'):
        drive, tail = name[5], name[7:]
        return Path(drive+':/'+tail)
    return ROOT/name


def verify():
    ledger = sealed(LEDGER)
    for name, expected in ledger['bindings'].items():
        assert sha(bound_path(name)) == expected, name
    return ledger


def inventory():
    ledger = verify()
    records = []
    for name, role in ledger['metadata_roles'].items():
        original = load(ROOT/name)
        records.append(dict(path=name, sha256=sha(ROOT/name), role=role,
            evidence={k:original[k] for k in ledger['metadata_fields'] if k in original},
            qualified_fresh_dataset=False))
    write(ROOT/'reports/fresh-data-031-inventory.json', dict(kind='metadata_only_inventory_031',
        ledger_sha256=sha(LEDGER), directories=ledger['existing_data_directories'], records=records,
        qualified_fresh_datasets_in_this_catalog=0, historical_price_rows_read=0,
        scope='Fixed canonical metadata/reviews; not an exhaustive search for other sources',
        fresh_performance_eligible=False, annual_eligible=False, orders_available=False))
    print(json.dumps(dict(metadata_files=len(records), qualified_fresh_datasets=0, history_rows_read=0)))


def unavailable(reason):
    return dict(version=VERSION, status='probe_not_started', stop_reason=reason,
        actual_quote_reads=0, requested_reads=120, observations=[], contract_snapshot=None,
        continuous_tick_capture=False, raw_labels_interpreted_as_utc=False,
        local_clock_independently_certified=False, historical_timezone_verified=False,
        fresh_performance_eligible=False, annual_eligible=False, orders_available=False)


def run_probe():
    ledger = verify()
    assert not PROBE.exists() and not RESERVATION.exists(), 'One invocation only; preserve existing outcome'
    write(RESERVATION, dict(kind='exclusive_probe_reservation_031', ledger_sha256=sha(LEDGER),
        declared_date=DATE, terminal_launch_authorized=False, orders_available=False))
    outcome, initialized, mt5 = None, False, None
    try:
        if os.name != 'nt':
            outcome = unavailable('windows_runtime_required')
        else:
            status = subprocess.run(['powershell.exe','-NoProfile','-Command',
                'ConvertTo-Json -Compress -InputObject @(Get-Process terminal64 -ErrorAction SilentlyContinue | ForEach-Object { $_.Path })'],
                capture_output=True,text=True,check=True,timeout=15)
            paths = json.loads(status.stdout)
            wanted = os.path.normcase(str(Path(ledger['terminal']).resolve()))
            if wanted not in [os.path.normcase(p) for p in paths if p]:
                outcome = unavailable('terminal_not_running')
            else:
                import MetaTrader5 as mt5
                initialized = mt5.initialize(str(Path(ledger['terminal'])),timeout=15000)
                if not initialized:
                    outcome = unavailable('read_only_connection_failed_details_redacted')
                else:
                    outcome = probe(mt5, lambda:(time.time_ns()//1000000,time.monotonic_ns()),time.sleep)
                    outcome['package_version'] = str(mt5.__version__)
    except Exception:
        outcome = unavailable('runtime_preflight_failure_details_redacted')
    finally:
        if mt5 is not None:
            mt5.shutdown()
    outcome.update(ledger_sha256=sha(LEDGER), reservation_sha256=sha(RESERVATION),
                   historical_price_rows_read=0, strategy_replays=0)
    write(PROBE,outcome)
    print(json.dumps({k:outcome[k] for k in ('status','stop_reason','actual_quote_reads','fresh_performance_eligible','orders_available')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=('freeze','verify','inventory','probe'))
    {'freeze':freeze,'verify':verify,'inventory':inventory,'probe':run_probe}[parser.parse_args().action]()

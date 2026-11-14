"""Freeze inputs; execute one reserved read-only Windows clock diagnostic."""
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
OLD = runpy.run_path(str(ROOT/'scripts/data-qualification-036.py'))
BIND = runpy.run_path(str(ROOT/'scripts/fresh-data-031.py'))
sha, write, sealed = OLD['sha'], OLD['write'], OLD['sealed']
HANDOFF = OLD['HANDOFF']
bound_path = BIND['bound_path']
from forex_demo_lab.clock_reference_037 import DATE, VERSION, TARGETS, HEADERS, collect, https_head
from forex_demo_lab.fresh_data_031 import receipt

PRIOR = ROOT/'reports/data-qualification-036-final-source.json'
LEDGER = ROOT/'reports/clock-reference-037-ledger.json'
OUTPUT = ROOT/'reports/clock-reference-037-capture.json'
RESERVATION = ROOT/'reports/clock-reference-037-reservation.json'


def prior_verify(allow_handoff=False):
    assert sha(PRIOR) == 'b175af45524a5bf76e94d7f16d374c9106c41a597e7f01bdfdfcbca5959fbe57'
    prior = sealed(PRIOR); bindings = {}; changes = {}
    for group, values in prior.items():
        if not group.endswith('_bindings') or group == 'archive_external_bindings':
            continue
        for name, expected in values.items():
            assert name not in bindings
            current = sha(bound_path(name))
            if current != expected:
                assert allow_handoff and group == 'source_bindings' and name in HANDOFF, name
                changes[name] = dict(previous_sha256=expected, current_sha256=current)
            bindings[name] = expected
    external = prior['archive_external_bindings']
    assert len(bindings) == 1077 and len(external) == 45
    assert all(bindings[n] == h for n,h in external.items())
    assert sha(PRIOR.with_suffix('.zip')) == prior['archive_sha256']
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist()) == 1032
        assert set(z.namelist()) == set(bindings)-set(external)
        for n in z.namelist():
            assert hashlib.sha256(z.read(n)).hexdigest() == bindings[n], n
    assert prior['fresh_performance_eligible'] is prior['annual_eligible'] is prior['orders_available'] is False
    return dict(bindings_verified=1077, archived_members_verified=1032,
                external_bindings_verified=45, allowed_handoff_changes=changes)


def freeze():
    assert os.name != 'nt'
    previous = prior_verify(); tests = sealed(ROOT/'reports/clock-reference-037-tests.json')
    assert tests['passed'] and tests['tests_run'] == tests['tests_passed'] == 522 and tests['new_tests'] == 24
    bindings = {}
    for pattern in ('src/**/*.py','scripts/*037*.py','tests/*037*.py','docs/*037*.md',
                    'reports/clock-reference-037-tests*','reports/data-qualification-036-*',
                    'reports/fresh-data-031-probe.*','reports/fresh-data-031-checks.*',
                    'reports/fresh-replication-035-ledger.*','data/fresh-replication-035/*'):
        for path in ROOT.glob(pattern):
            bindings[path.relative_to(ROOT).as_posix()] = sha(path)
    old = sealed(ROOT/'reports/fresh-replication-035-ledger.json')
    for name,h in old['bindings'].items():
        if name.startswith('/mnt/'):
            assert sha(bound_path(name)) == h
            bindings[name] = h
    for name in ('ledger','reservation','capture','checks','review','final-source'):
        assert not (ROOT/('reports/clock-reference-037-'+name+'.json')).exists()
    write(LEDGER, dict(version=VERSION, declared_date=DATE, bindings=bindings,
        prior_snapshot_verification=previous, terminal=old['terminal'], targets=TARGETS,
        maximum_http_requests=3, per_request_timeout_seconds=10, total_request_seconds=30,
        maximum_quote_reads=1, maximum_history_reads=0, fresh_performance_eligible=False,
        annual_eligible=False, orders_available=False))
    print(json.dumps(dict(frozen=True, bindings=len(bindings))))


def verify():
    ledger = sealed(LEDGER)
    for name,h in ledger['bindings'].items():
        assert sha(bound_path(name)) == h, name
    return ledger


def head(index):
    assert os.name == 'nt' and RESERVATION.exists() and not OUTPUT.exists()
    try:
        result = https_head(index)
    except Exception:
        result = dict(status=None, headers={k:None for k in HEADERS}, transport_outcome='transport_failure')
    print(json.dumps(result))


def transport(index, timeout):
    try:
        response = subprocess.run([sys.executable, str(Path(__file__)), 'head', '--index', str(index)],
                                  capture_output=True, text=True, timeout=timeout, check=True)
        return json.loads(response.stdout)
    except subprocess.TimeoutExpired:
        return dict(status=None, headers={k:None for k in HEADERS}, transport_outcome='timeout')
    except Exception:
        return dict(status=None, headers={k:None for k in HEADERS}, transport_outcome='transport_failure')


def service_status():
    try:
        command = ('$s=Get-Service -Name W32Time -ErrorAction SilentlyContinue; '
                   'if ($null -eq $s) { ConvertTo-Json -Compress @{available=$false;running=$null;outcome="unavailable"} } '
                   'else { ConvertTo-Json -Compress @{available=$true;running=($s.Status -eq "Running");outcome="observed"} }')
        result = subprocess.run(['powershell.exe','-NoProfile','-Command',command],
                                capture_output=True, text=True, timeout=10, check=True)
        return json.loads(result.stdout)
    except Exception:
        return dict(available=False, running=None, outcome='query_failed')


def connect(ledger):
    import MetaTrader5 as mt5
    # The pinned package's initialize can start a terminal; check exact running path first.
    status = subprocess.run(['powershell.exe','-NoProfile','-Command',
        'ConvertTo-Json -Compress -InputObject @(Get-Process terminal64 -ErrorAction SilentlyContinue | ForEach-Object { $_.Path })'],
        capture_output=True, text=True, timeout=10, check=True)
    paths = json.loads(status.stdout)
    wanted = os.path.normcase(str(Path(ledger['terminal']).resolve()))
    if wanted not in [os.path.normcase(p) for p in paths if p]:
        return None
    if str(mt5.__version__) != '5.0.6231':
        return None
    receipt(time.time_ns()//1_000_000)
    if not mt5.initialize(str(Path(ledger['terminal'])), timeout=15000):
        mt5.shutdown()
        return None
    return mt5


def run():
    ledger = verify()
    assert os.name == 'nt', 'Use pinned existing Windows runtime'
    assert not OUTPUT.exists() and not RESERVATION.exists()
    write(RESERVATION, dict(version=VERSION, ledger_sha256=sha(LEDGER), declared_date=DATE,
        maximum_http_requests=3, maximum_quote_reads=1, terminal_launch_authorized=False,
        history_reads_authorized=0, orders_available=False))
    result = collect(lambda:(time.time_ns()//1_000_000, time.monotonic_ns()),
                     service_status, transport, lambda:connect(ledger))
    result.update(ledger_sha256=sha(LEDGER), reservation_sha256=sha(RESERVATION))
    write(OUTPUT, result)
    print(json.dumps(dict(http_requests=len(result['requests']), actual_quote_reads=result['actual_quote_reads'],
                         comparison=result['comparison'], stop_reason=result['stop_reason'], orders_available=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=('freeze','verify','run','head'))
    parser.add_argument('--index', type=int)
    args = parser.parse_args()
    if args.action == 'head':
        head(args.index)
    else:
        {'freeze':freeze,'verify':lambda:print(json.dumps(dict(verified=len(verify()['bindings'])))), 'run':run}[args.action]()

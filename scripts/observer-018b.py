"""Preserve 018 failure; freeze/rerun symbolic serialization without changing rules."""
import argparse
import json
from pathlib import Path
import runpy
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from forex_demo_lab.observer_parity import digest
from forex_demo_lab.observer_parity_symbols import supplemental_harness, check_symbols

OLD = runpy.run_path('scripts/observer-018.py')
LEDGER = Path('reports/observer-018b-ledger.json')
ARCHIVE = Path('reports/observer-018b-source.zip')
HARNESS = Path('mt5/Tests/ForexObserverParity018B.mq5')
DRIVER = Path('scripts/run-observer-018b.ps1')
ATTEMPT = Path('reports/observer-018-attempts/1605d50e22c5413e97da4784a8dccdf1')
CODE = ['docs/OBSERVER-018B-PLAN.md', 'src/forex_demo_lab/observer_parity_symbols.py',
        'scripts/observer-018b.py', 'tests/test_observer_parity_symbols.py']


def driver():
    text = Path('scripts/run-observer-018.ps1').read_text()
    text = text.replace('observer-018.py verify', 'observer-018b.py verify')
    text = text.replace('ForexDemoLab\\observer018\\\' + $runId)', 'ForexDemoLab\\observer018b\\\' + $runId)')
    text = text.replace('reports\\observer-018-attempts\\', 'reports\\observer-018b-attempts\\')
    text = text.replace('ForexObserverParity018', 'ForexObserverParity018B')
    text = text.replace('reports\\observer-018-ledger.json', 'reports\\observer-018b-ledger.json')
    needle = "    $evidence['result_sha256'] = Hash018 (Join-Path $attempt 'results.csv')"
    if text.count(needle) != 1: raise ValueError('Driver result site differs')
    extra = ("    $nativeResult = $commonResult + '.native.csv'\n"
             "    if (-not (Test-Path -LiteralPath $nativeResult)) { throw 'Native diagnostic output missing.' }\n"
             "    Copy-Item -LiteralPath $nativeResult -Destination (Join-Path $attempt 'native.csv')\n"
             "    $evidence['native_sha256'] = Hash018 (Join-Path $attempt 'native.csv')\n")
    return (text.replace(needle, extra + needle) + '\n').encode()


def prepare():
    OLD['verify']()
    if any(p.exists() for p in (LEDGER, ARCHIVE, HARNESS, DRIVER)):
        raise FileExistsError('018B already prepared; preserve all evidence')
    failure = json.loads((ATTEMPT / 'failed-review.json').read_text())
    if failure['passed'] or len(failure['failures']) != 2:
        raise ValueError('Declared first failure differs')
    OLD['write_new'](HARNESS, supplemental_harness(Path('mt5/Tests/ForexObserverParity018.mq5').read_text()).encode())
    OLD['write_new'](DRIVER, driver())
    names = CODE + [str(HARNESS), str(DRIVER), 'reports/observer-018-ledger.json',
                    'reports/observer-018-ledger.sha256', 'reports/observer-018-checks.json']
    names += [str(p) for p in sorted(ATTEMPT.iterdir()) if p.is_file()]
    bindings = {name: digest(Path(name).read_bytes()) for name in names}
    with zipfile.ZipFile(ARCHIVE, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name in names: archive.write(name, name)
    value = dict(kind='symbolic_observer_source_freeze_018b', cases=38,
                 source_bindings=bindings, archive_sha256=digest(ARCHIVE.read_bytes()),
                 original_018_strict_review_passed=False,
                 performance_evaluation_ready=False, demo_execution_ready=False)
    OLD['write_new'](LEDGER, OLD['json_bytes'](value))
    OLD['write_new'](Path('reports/observer-018b-ledger.sha256'), (digest(LEDGER.read_bytes())+'\n').encode())
    verify()
    print('018B frozen: same 38 inputs; symbolic serialization and raw enum evidence.')


def verify():
    OLD['verify']()
    if digest(LEDGER.read_bytes()) != Path('reports/observer-018b-ledger.sha256').read_text().strip():
        raise ValueError('018B ledger seal differs')
    value = json.loads(LEDGER.read_text())
    for name, checksum in value['source_bindings'].items():
        if digest(Path(name).read_bytes()) != checksum: raise ValueError('018B file changed: ' + name)
    if digest(ARCHIVE.read_bytes()) != value['archive_sha256']:
        raise ValueError('018B archive differs')
    if HARNESS.read_text() != supplemental_harness(Path('mt5/Tests/ForexObserverParity018.mq5').read_text()):
        raise ValueError('Supplemental harness has unrelated changes')
    if DRIVER.read_bytes() != driver(): raise ValueError('Supplemental driver changed')
    return value


def check(path):
    verify()
    if path.parent.parent != Path('reports/observer-018b-attempts') or path.name != 'results.csv':
        raise ValueError('Unexpected supplemental result path')
    folder = path.parent
    launch = json.loads((folder/'launch.json').read_text(encoding='utf-8-sig'))
    compilation = json.loads((folder/'compile.json').read_text(encoding='utf-8-sig'))
    if launch['status'] != 'completed' or not compilation['passed']:
        raise ValueError('Supplemental compile/runtime incomplete')
    if launch['ledger_sha256'] != digest(LEDGER.read_bytes()): raise ValueError('Launch ledger differs')
    if compilation['source_sha256'] != digest(HARNESS.read_bytes()): raise ValueError('Compiled source differs')
    for filename, key in (('results.csv', 'result_sha256'), ('native.csv', 'native_sha256'),
                          ('math018.ini', 'config_sha256'), ('Runtime018.set', 'preset_sha256')):
        if digest((folder/filename).read_bytes()) != launch[key]:
            raise ValueError('Launch output/config binding differs: '+filename)
    config = (folder/'math018.ini').read_text()
    for line in ('Model=3', 'Optimization=0', 'UseLocal=1', 'UseRemote=0', 'UseCloud=0',
                 'Enabled=0', 'AllowLiveTrading=0', 'AllowDllImport=0', 'ShutdownTerminal=1'):
        if line not in config.splitlines(): raise ValueError('Safety/math configuration differs')
    if any(launch[key] for key in ('copied_account_configuration', 'market_data_used', 'orders_available')):
        raise ValueError('Supplemental runtime scope differs')
    review = check_symbols(path.read_text(), (folder/'native.csv').read_text(),
                           json.loads(OLD['INPUTS'].read_text()))
    review.update(result_sha256=digest(path.read_bytes()),
                  native_sha256=digest((folder/'native.csv').read_bytes()),
                  ledger_sha256=digest(LEDGER.read_bytes()), run_id=launch['run_id'])
    OLD['write_new'](folder/'review.json', OLD['json_bytes'](review))
    print(json.dumps(review, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'verify', 'check'])
    parser.add_argument('--results', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare': prepare()
    elif args.action == 'verify': verify(); print('018 and 018B source, fixtures and failed evidence intact.')
    else:
        if args.results is None: parser.error('--results required')
        check(args.results)

"""Freeze original observer, synthetic inputs and checker before MT5 execution."""
import argparse
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from forex_demo_lab.observer_parity import digest, fixtures, mql_inputs, observer_body, check_runtime

LEDGER = Path('reports/observer-018-ledger.json')
ARCHIVE = Path('reports/observer-018-source.zip')
GENERATED = Path('mt5/Tests/generated018')
INPUTS = Path('reports/observer-018-fixtures.json')
SOURCES = ['docs/OBSERVER-018-PLAN.md', 'src/forex_demo_lab/observer_parity.py',
           'src/forex_demo_lab/model.py', 'config/baseline.json',
           'mt5/Experts/ForexDemoObserver.mq5', 'mt5/Tests/ForexObserverParity018.mq5',
           'scripts/observer-018.py', 'scripts/run-observer-018.ps1',
           'tests/test_observer_parity.py']


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream: stream.write(data)


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def prepare():
    if LEDGER.exists() or ARCHIVE.exists() or INPUTS.exists() or GENERATED.exists():
        raise FileExistsError('018 inputs already exist; preserve first attempt')
    prior = json.loads(Path('reports/labels-017-final-source.json').read_text())
    # No historical datasets are reused in this synthetic experiment.
    for name in ('src/forex_demo_lab/model.py', 'config/baseline.json',
                 'mt5/Experts/ForexDemoObserver.mq5'):
        if digest(Path(name).read_bytes()) != prior['source_bindings'][name]:
            raise ValueError('Baseline/observer differs from completed 017')
    for name, checksum in prior['report_bindings'].items():
        if digest(Path(name).read_bytes()) != checksum:
            raise ValueError('Previous report changed: ' + name)
    if prior['performance_evaluation_ready'] or prior['demo_execution_ready']:
        raise ValueError('Prior readiness state differs')
    cases = fixtures()
    write_new(INPUTS, json_bytes(cases))
    write_new(GENERATED / 'OriginalObserver018.mqh', observer_body(Path(SOURCES[4]).read_bytes()))
    write_new(GENERATED / 'Fixtures018.mqh', mql_inputs(cases))
    names = SOURCES + [str(INPUTS), str(GENERATED / 'OriginalObserver018.mqh'),
                      str(GENERATED / 'Fixtures018.mqh'), 'reports/labels-017-final-source.json']
    bindings = {name: digest(Path(name).read_bytes()) for name in names}
    with zipfile.ZipFile(ARCHIVE, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name in names: archive.write(name, name)
    ledger = dict(kind='synthetic_observer_source_freeze_018', cases=len(cases),
                  source_bindings=bindings, previous_reports=prior['report_bindings'],
                  archive_sha256=digest(ARCHIVE.read_bytes()),
                  performance_evaluation_ready=False, demo_execution_ready=False)
    write_new(LEDGER, json_bytes(ledger))
    write_new(Path('reports/observer-018-ledger.sha256'),
              (digest(LEDGER.read_bytes()) + '\n').encode())
    verify()
    print(f'018 frozen: {len(cases)} synthetic cases; original body preserved.')


def verify():
    if digest(LEDGER.read_bytes()) != Path('reports/observer-018-ledger.sha256').read_text().strip():
        raise ValueError('018 ledger seal differs')
    ledger = json.loads(LEDGER.read_text())
    for name, checksum in {**ledger['source_bindings'], **ledger['previous_reports']}.items():
        if digest(Path(name).read_bytes()) != checksum: raise ValueError('Frozen file changed: ' + name)
    if digest(ARCHIVE.read_bytes()) != ledger['archive_sha256']:
        raise ValueError('018 archive differs')
    if (GENERATED / 'OriginalObserver018.mqh').read_bytes() != observer_body(Path(SOURCES[4]).read_bytes()):
        raise ValueError('Original body not preserved exactly')
    cases = json.loads(INPUTS.read_text())
    if cases != fixtures() or (GENERATED / 'Fixtures018.mqh').read_bytes() != mql_inputs(cases):
        raise ValueError('Synthetic input regeneration differs')
    return ledger


def check(path):
    verify()
    # Compile/launch/result files must come from one uniquely named owned attempt.
    if path.parent.parent != Path('reports/observer-018-attempts') or path.name != 'results.csv':
        raise ValueError('Unexpected runtime result path')
    launch = json.loads((path.parent / 'launch.json').read_text())
    compile_result = json.loads((path.parent / 'compile.json').read_text())
    if launch['status'] != 'completed' or not compile_result['passed']:
        raise ValueError('Compiled runtime did not complete')
    if launch['result_sha256'] != digest(path.read_bytes()): raise ValueError('Result hash differs')
    if launch['ledger_sha256'] != digest(LEDGER.read_bytes()): raise ValueError('Launch ledger differs')
    review = check_runtime(path.read_text(), json.loads(INPUTS.read_text()))
    write_new(path.parent / 'review.json', json_bytes(review))
    print(json.dumps(review, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'verify', 'check'])
    parser.add_argument('--results', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare': prepare()
    elif args.action == 'verify': verify(); print('018 frozen source and previous reports intact.')
    else:
        if args.results is None: parser.error('--results required')
        check(args.results)

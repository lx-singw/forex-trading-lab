"""Freeze, acquire and review separate raw-label MT5 recovery ticks."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from forex_demo_lab.recovery import audit_chunk, chunks, combine, references, sample_passed
from forex_demo_lab.tick_audit import sha256

ROOT = Path('data/recovery-010')
REFERENCE = Path('data/history-009-mt5-reference')
PLAN = Path('docs/RECOVERY-010-PLAN.md')
LEDGER = Path('reports/recovery-010-ledger.json')
START, END = '2023-02-01T00:00:00+00:00', '2023-08-01T00:00:00+00:00'
SAMPLE_START, SAMPLE_END = '2023-07-11T15:00:00+00:00', '2023-07-12T03:00:00+00:00'
SOURCE = Path('reports/recovery-010-source.zip')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def source_files():
    return [PLAN, Path(__file__).relative_to(Path.cwd()) if Path(__file__).is_absolute() else Path(__file__),
            *sorted(Path('src/forex_demo_lab').glob('*.py')),
            Path('scripts/capture-ticks.py'), Path('tests/test_recovery.py')]


def freeze():
    if LEDGER.exists() or SOURCE.exists():
        raise FileExistsError('Recovery study already frozen')
    ref = load(REFERENCE / 'capture.json')
    if ref['raw_sha256'] != sha256(REFERENCE / 'rates.csv'):
        raise ValueError('Original reference binding changed')
    sample = audit_chunk(ROOT / 'sample', SAMPLE_START, SAMPLE_END, references(REFERENCE / 'rates.csv'))
    write_new(Path('reports/recovery-010-sample.json'), sample)
    with zipfile.ZipFile(SOURCE, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for path in source_files():
            z.write(path, path.as_posix())
    write_new(LEDGER, {'declared_utc': datetime.now(timezone.utc).isoformat(),
        'files': {p.as_posix(): sha256(p) for p in source_files()}, 'source_sha256': sha256(SOURCE),
        'reference_metadata_sha256': sha256(REFERENCE / 'capture.json'),
        'reference_sha256': sha256(REFERENCE / 'rates.csv'),
        'sample_capture_sha256': sha256(ROOT / 'sample/capture.json'),
        'sample_report_sha256': sha256(Path('reports/recovery-010-sample.json')),
        'sample_gate_passed': sample_passed(sample), 'windows': chunks(START, END),
        'performance_evaluation_ready': False})
    print(f'Sample gate: {sample_passed(sample)}; {sample["ticks"]} ticks; {len(chunks(START, END))} declared chunks')


def verify():
    ledger = load(LEDGER)
    if (any(sha256(Path(p)) != digest for p, digest in ledger['files'].items())
            or sha256(SOURCE) != ledger['source_sha256']
            or sha256(REFERENCE / 'capture.json') != ledger['reference_metadata_sha256']
            or sha256(REFERENCE / 'rates.csv') != ledger['reference_sha256']
            or sha256(ROOT / 'sample/capture.json') != ledger['sample_capture_sha256']
            or sha256(Path('reports/recovery-010-sample.json')) != ledger['sample_report_sha256']
            or ledger['windows'] != [list(w) for w in chunks(START, END)]):
        raise ValueError('Frozen recovery inputs changed')
    sample = audit_chunk(ROOT / 'sample', SAMPLE_START, SAMPLE_END, references(REFERENCE / 'rates.csv'))
    if not ledger['sample_gate_passed'] or not sample_passed(sample):
        raise ValueError('Sample gate failed; expansion unavailable')
    return ledger


def acquire():
    ledger = verify()
    if os.name != 'nt':
        raise ValueError('Acquisition requires existing Windows MT5 Python runtime')
    ref = references(REFERENCE / 'rates.csv')
    for i, (start, end) in enumerate(ledger['windows']):
        folder = ROOT / f'chunk-{i:03d}'
        report_path = Path(f'reports/recovery-010-chunk-{i:03d}.json')
        if not folder.exists():
            subprocess.run([sys.executable, str(Path(__file__).with_name('capture-ticks.py')),
                '--terminal', r'C:\Program Files\MetaTrader 5\terminal64.exe',
                '--start', start, '--end', end, '--output', str(folder)], check=True, timeout=300)
        report = audit_chunk(folder, start, end, ref)
        report['capture_sha256'] = sha256(folder / 'capture.json')
        if report_path.exists():
            if load(report_path) != report:
                raise ValueError('Completed recovery chunk changed; resume rejected')
        else:
            write_new(report_path, report)
        print(f'Chunk {i + 1}/{len(ledger["windows"])} checked: {report["ticks"]} ticks', flush=True)


def review():
    ledger = verify()
    ref, reports, bindings = references(REFERENCE / 'rates.csv'), [], []
    for i, (start, end) in enumerate(ledger['windows']):
        folder = ROOT / f'chunk-{i:03d}'
        report_path = Path(f'reports/recovery-010-chunk-{i:03d}.json')
        report = audit_chunk(folder, start, end, ref)
        report['capture_sha256'] = sha256(folder / 'capture.json')
        if report != load(report_path):
            raise ValueError('Chunk differs from recorded acquisition audit')
        reports.append(report)
        bindings.append({'folder': folder.as_posix(), 'capture_sha256': report['capture_sha256'],
                         'ticks_sha256': report['data_sha256'], 'audit_sha256': sha256(report_path)})
        print(f'Reviewed chunk {i + 1}/{len(ledger["windows"])}', flush=True)
    result = combine(reports)
    result.update(ledger_sha256=sha256(LEDGER), bindings=bindings,
        note='Separate original broker ticks; no splicing, interpolation, UTC certification or strategy returns')
    write_new(Path('reports/recovery-010-review.json'), result)
    print(json.dumps({'ticks': result['ticks'], 'hour_counts': result['hour_counts'],
                      'performance_evaluation_ready': False}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'acquire', 'review', 'verify'))
    args = parser.parse_args()
    {'freeze': freeze, 'acquire': acquire, 'review': review, 'verify': verify}[args.action]()

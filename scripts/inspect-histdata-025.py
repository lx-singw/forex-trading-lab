"""Preserve a checker schema failure and inspect ZIP metadata only."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ledger_path=ROOT/'reports/exness-comparison-025-ledger.json'
    ledger=json.loads(ledger_path.read_text())
    assert sha(ledger_path)==ledger_path.with_suffix('.sha256').read_text().strip()
    entries={}
    for month in ('202303','202307'):
        path=f'data/history-009-raw/{month}/original.zip'
        assert sha(ROOT/path)==ledger['bindings'][path]
        with zipfile.ZipFile(ROOT/path) as archive:
            entries[month]=[dict(name=e.filename,size=e.file_size,crc=e.CRC,encrypted=bool(e.flag_bits&1))
                            for e in archive.infolist()]
    report=dict(kind='preserved_checker_schema_failure_025',ledger_sha256=sha(ledger_path),
                checker_sha256=sha(ROOT/'scripts/check-exness-comparison-025.py'),
                original_check_completed=False,failure='Single-member HistData ZIP assumption rejected',
                archive_metadata=entries,inspection_quote_rows_read=0,network_requests=0,
                primary_review_unchanged=True,annual_eligible=False,orders_available=False)
    path=ROOT/'reports/exness-comparison-025-check-attempt.json'
    with path.open('x') as stream:json.dump(report,stream,indent=2,sort_keys=True);stream.write('\n')
    with path.with_suffix('.sha256').open('x') as stream:stream.write(sha(path)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()

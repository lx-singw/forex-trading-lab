"""Closed installed-binary rollover and honest failed-record bookkeeping."""
import json
from .clock_observer_042 import RuntimeSequence,parse_record,PREFIX,VERSION
from .clock_session_043 import require_interactive,reuse_path

ROLLOVER={
 '/mnt/c/Program Files/MetaTrader 5/metaeditor64.exe':(
  'c4641eda510ffea814c627c922ea19e9eef51a22ff1a7244cda31345736c1d2e',
  'fb9fbe19499f3241e6adf4bf1c5c9212be1eaae9f95df9cd183082e72c599f10'),
 '/mnt/c/Program Files/MetaTrader 5/terminal64.exe':(
  '49a205f54f0ae609492cd47bae78b6403b7b527b672c325e9b589b0e4aaee3a2',
  'daf2dfc61d593fe20a40b63610762d241c32ad4845b79f879fb7cbf114345cce')}
SUBJECT='CN=MetaQuotes Ltd., O=MetaQuotes Ltd., S=Lemesos, C=CY'
THUMBPRINT='5A64A7AED24C33DED342D01D01FA5286F06DA6DC'

def allowed_rollover(name,previous,current):
    return name in ROLLOVER and (previous,current)==ROLLOVER[name]

def validate_signatures(report):
    files=report['files']
    if len(files)!=2 or {r['name'] for r in files}!={'metaeditor64.exe','terminal64.exe'}:raise ValueError('installed_file_set_changed')
    for row in files:
        if row['signature_status']!='Valid' or row['signer_subject']!=SUBJECT or row['signer_thumbprint']!=THUMBPRINT or row['file_version']!='5.0.0.6241':
            raise ValueError('installed_signature_or_version_changed')
    return True

class RuntimeSequence044(RuntimeSequence):
    def collect(self,records):
        if self.pending is None or len(records)!=1:raise ValueError('exactly_one_native_record_required')
        r=parse_record(PREFIX+json.dumps(records[0]));enabled=self.pending
        self.records.append(r);self.pending=None
        if not enabled and r!=dict(version=VERSION,accepted=False,reason_code=17,quote_reads=0):
            raise ValueError('disabled_run_read_or_reason_invalid')
        if enabled and not r['accepted']:raise ValueError('native_observer_guard_rejected')
        return r

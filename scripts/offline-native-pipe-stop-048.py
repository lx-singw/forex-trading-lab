"""Offline-only dependency change accounting; never authorizes native execution."""
import hashlib
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-pipe-048.py'))
CHANGES={
 '/mnt/c/Program Files/MetaTrader 5/metaeditor64.exe':('fb9fbe19499f3241e6adf4bf1c5c9212be1eaae9f95df9cd183082e72c599f10','7d6e42249722888429bb3d4e90e4a810d745f195cfeda9c99a06f24605b29428'),
 '/mnt/c/Program Files/MetaTrader 5/terminal64.exe':('daf2dfc61d593fe20a40b63610762d241c32ad4845b79f879fb7cbf114345cce','eec25399ebd3171422d954fa01b75127c0356c94fe1d45d80dc27c3d0deb4ba1')}

def verify_offline():
    ledger=API['sealed'](API['LEDGER'])
    stop=API['sealed'](ROOT/'reports/native-pipe-048-stop-audit-preflight.json')
    change=API['sealed'](ROOT/'reports/native-pipe-048-installed-change.json')
    assert stop['original_ledger_sha256']==API['sha'](API['LEDGER']) and stop['unchanged_bindings_verified']==1452
    assert set(stop['changed_bindings'])==set(CHANGES) and not change['change_cause_established'] and not change['disconnect_cause_established']
    for n,h in ledger['bindings'].items():
        actual=API['sha'](API['bound'](n))
        if n in CHANGES:
            before,after=CHANGES[n]
            assert h==before and actual==after
            assert stop['changed_bindings'][n]==dict(frozen_sha256=before,observed_sha256=after)
        else:assert actual==h,n
    assert len(change['signatures'])==2
    for s in change['signatures']:
        n='/mnt/c/Program Files/MetaTrader 5/'+s['file']
        assert s['sha256']==CHANGES[n][1] and s['version']=='5.0.0.6244' and s['signature_status']=='Valid'
        assert s['subject']=='CN=MetaQuotes Ltd., O=MetaQuotes Ltd., S=Lemesos, C=CY'
        assert s['thumbprint']=='5A64A7AED24C33DED342D01D01FA5286F06DA6DC'
    archive=ROOT/'reports/native-pipe-048-stop-audit-r1-source.zip'
    assert API['sha'](archive)==change['source_archive_sha256']
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.infolist())==3 and set(z.namelist())==set(change['source_bindings'])
        for n,h in change['source_bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    # Original executable pins remain rejected. This is only an existing-log audit.
    return ledger

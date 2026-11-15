"""Fixed invented-profile admission for checked diagnostic snapshots, never markets."""
import hashlib
from .native_journal_157 import CAP, require
from .paired_replay_133 import canonical
from .recorder_files_157 import read_file, folder_check
from .relay_audit_158 import inspect_job

PROFILES={'5dae9da43571ed2d44ab68d719d4599ca2e6d799175271f34ec73892d971e2e1':'full',
          'b1060237d6f1d453aadd5f8aa20757d61227981038017f1d600b4d0ac6fbd5e1':'failed_metadata'}


def sha(raw):return hashlib.sha256(raw).hexdigest()


def capture(folder,job):
    folder=folder_check(folder,job);audit=inspect_job(folder,job)
    require(1<=audit['requests']<=256)
    names=['NativePort156.txt','Relay157.json','Owner157.claim']
    names.extend(f'{kind}{index:04d}.txt' for index in range(1,audit['requests']+1) for kind in ('Request','Reply'))
    files={};total=0;native=None
    for name in names:
        raw=read_file(folder/name,CAP if name in names[:2] else 512);total+=len(raw);require(total<=3*CAP)
        files[name]=sha(raw)
        if name=='NativePort156.txt':native=raw
    require(files['NativePort156.txt']==audit['native_sha256'])
    lines=native.splitlines(keepends=True);rows=[line[:-1].decode('ascii').rsplit('\t',1)[0].split('\t') for line in lines]
    projection=[r if r[0] in ('R','L') else r[:3]+r[9:] for r in rows if r[0] in ('C','I','D','V','W','K','R','L','M','T')]
    digest=sha(canonical(projection));require(digest in PROFILES)
    start=next(i for i,r in enumerate(rows) if r[0]=='B');end=next(i for i,r in enumerate(rows) if r[0]=='Z')
    descriptor=dict(schema='invented_diagnostic159_source_v1',source_job=job,profile=PROFILES[digest],projection_sha256=digest,
                    files=files,context_sha256=sha(b''.join(lines[start:end+1])),triple_sha256=sha(b''.join(lines[end+1:-1])),
                    source_origin_authenticated=False,source_caller_acknowledgement_known=False,market_eligible=False)
    # Refuse an ordinary change during admission. This is not an atomic hostile-user snapshot.
    require(inspect_job(folder,job)==audit)
    for name,digest in files.items():require(sha(read_file(folder/name,CAP if name in names[:2] else 512))==digest)
    return descriptor

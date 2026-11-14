"""Separate074 measured image-link profile; source/artifact readers stay073."""
from .sharing_build_073 import *
BUILD_PHASE="74000000000000000000000000000001"

def reserve_build074(path,value):
    required={'build_reservation_consumed','ledger_sha256','authorization_sha256','maximum_compiler_invocations','phase','orders_available'}
    if type(value) is not dict or set(value)!=required or value['build_reservation_consumed'] is not True or value['orders_available'] is not False:
        raise BuildRejected('stage_rejected')
    if type(value['maximum_compiler_invocations']) is not int or value['maximum_compiler_invocations']!=1 or value['phase']!=BUILD_PHASE:
        raise BuildRejected('stage_rejected')
    for k in ('ledger_sha256','authorization_sha256'):digest(value[k])
    raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode('ascii');path=Path(path)
    # A partial marker/sidecar pair still consumes the attempt. Never unlink it.
    with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    result=hashlib.sha256(raw).hexdigest()
    with path.with_suffix('.sha256').open('x') as f:f.write(result+'\n');f.flush();os.fsync(f.fileno())
    return result


def read_image074(path,budget,role):
    """Uncached image hash with an exact role-specific link profile."""
    cap=136314880;collect=False
    names={"terminal":"terminal64.exe","editor":"metaeditor64.exe","shell":"powershell.exe","python":"python.exe"}
    if role not in names or Path(path).name.casefold()!=names[role]:raise BuildRejected("file_rejected")
    links=2 if role=="shell" else 1
    if type(cap) is not int or not 0<cap<=136314880 or type(collect) is not bool:raise BuildRejected('file_rejected')
    path=Path(path);budget.consume('hash_reads');no_reparse073(path,budget)
    budget.consume('path_stats');before=path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink!=links or not 0<before.st_size<=cap:raise BuildRejected('file_rejected')
    stamp=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)
    total=0;h=hashlib.sha256();parts=[]
    with path.open('rb') as f:
        if stamp(os.fstat(f.fileno()))!=stamp(before):raise BuildRejected('file_rejected')
        while total<before.st_size:
            n=min(1048576,before.st_size-total);budget.consume('hash_bytes',n);raw=f.read(n)
            if len(raw)!=n:raise BuildRejected('file_rejected')
            h.update(raw);total+=len(raw)
            if collect:parts.append(raw)
        budget.consume('hash_bytes');extra=f.read(1)
        if extra or stamp(os.fstat(f.fileno()))!=stamp(before):raise BuildRejected('file_rejected')
    no_reparse073(path,budget);budget.consume('path_stats')
    if stamp(path.stat())!=stamp(before):raise BuildRejected('file_rejected')
    budget.check();return dict(sha256=h.hexdigest(),size=total,raw=b''.join(parts) if collect else None)



def build_record074(*args):
    r=build_record073(*args)
    return {**r,"version":"sharing_build_074_v1","build_phase":BUILD_PHASE}

def owned074(directory,root):
    p,r=Path(directory),Path(root)
    if p.parent!=r or re.fullmatch('compiler074-[0-9a-f]{32}',p.name) is None:raise BuildRejected('stage_rejected')
    return p


def stage074(inputs,expected,directory,root,budget):
    if type(inputs) is not dict or set(inputs)!=set(SOURCE_INPUTS) or set(expected)!=set(inputs):raise BuildRejected('stage_rejected')
    directory=owned074(directory,root);no_reparse073(root,budget);directory.mkdir(exist_ok=False)
    no_reparse073(directory,budget)
    for name in sorted(inputs):
        value=read_bound073(inputs[name],budget,collect=True)
        if value['sha256']!=expected[name]:raise BuildRejected('binding_rejected')
        dest=directory/Path(name).name;budget.consume('copies');budget.consume('copy_bytes',value['size'])
        with dest.open('xb') as f:f.write(value['raw']);f.flush();os.fsync(f.fileno())
        if read_bound073(dest,budget)['sha256']!=expected[name]:raise BuildRejected('binding_rejected')
    return directory


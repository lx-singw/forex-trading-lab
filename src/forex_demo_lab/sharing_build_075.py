"""Separate075 compiler-shell policy binding; image/source checks stay074."""
from .sharing_build_074 import *
BUILD_PHASE="75000000000000000000000000000001"

def reserve_build075(path,value):
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

def owned075(directory,root):
    p,r=Path(directory),Path(root)
    if p.parent!=r or re.fullmatch('compiler075-[0-9a-f]{32}',p.name) is None:raise BuildRejected('stage_rejected')
    return p


def stage075(inputs,expected,directory,root,budget):
    if type(inputs) is not dict or set(inputs)!=set(SOURCE_INPUTS) or set(expected)!=set(inputs):raise BuildRejected('stage_rejected')
    directory=owned075(directory,root);no_reparse073(root,budget);directory.mkdir(exist_ok=False)
    no_reparse073(directory,budget)
    for name in sorted(inputs):
        value=read_bound073(inputs[name],budget,collect=True)
        if value['sha256']!=expected[name]:raise BuildRejected('binding_rejected')
        dest=directory/Path(name).name;budget.consume('copies');budget.consume('copy_bytes',value['size'])
        with dest.open('xb') as f:f.write(value['raw']);f.flush();os.fsync(f.fileno())
        if read_bound073(dest,budget)['sha256']!=expected[name]:raise BuildRejected('binding_rejected')
    return directory


def build_record075(*args):
    r=build_record074(*args)
    return {**r,"version":"sharing_build_075_v1","build_phase":BUILD_PHASE}

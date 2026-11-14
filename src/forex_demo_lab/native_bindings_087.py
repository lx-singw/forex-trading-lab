"""Source-only bridge to raw086 facts; injected dependencies, no native entry.

The fresh WMI last-restart timestamp is corroboration, not a unique kernel boot
GUID or a bound on latency. Actual provider behavior remains unverified.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import re
import struct

from .clock_observer_042 import runtime_guard
from .private_guard_065 import Identity065
from .synchronization_083 import Guard083, Meter083, require, digest, integer
from .synchronization_084 import Peer084
from .sharing_probe_062 import ProbeRejected
from .build_bindings_087 import Build087

BOOT_QUERY = 'SELECT LastBootUpTime FROM Win32_OperatingSystem'
BOOT_KIND = 'local_wmi_last_restart_time_087'
SDK_VERSION = '5.0.6231'
HASH_ROLES = {'terminal','editor','artifact','helper','sdk','launcher','config','boot_script','boot_shell'}
GUARD_INPUTS = {'src/forex_demo_lab/native_bindings_087.py','src/forex_demo_lab/build_bindings_087.py','scripts/boot-proof-087.ps1'}


def native_entry087(*args, **kwargs):
    raise ProbeRejected('native087_entry_unavailable')


def boot_stamp087(raw, now_us):
    try:
        integer(now_us, 1)
        require(type(raw) is bytes and len(raw) == 25)
        text = raw.decode('ascii')
        require(re.fullmatch(r'[0-9]{14}\.[0-9]{6}[+-][0-9]{3}', text) is not None)
        offset = int(text[22:]) * (1 if text[21] == '+' else -1)
        require(abs(offset) <= 840)
        local = datetime.strptime(text[:14], '%Y%m%d%H%M%S').replace(
            microsecond=int(text[15:21]), tzinfo=timezone(timedelta(minutes=offset)))
        delta = local.astimezone(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)
        value = (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds
        require(0 < value <= now_us)
        return b'WMI-BOOT087:' + value.to_bytes(8, 'little')
    except Exception:
        raise ProbeRejected('boot087_query_rejected') from None


def sid_binary087(value):
    """Compare raw pipe logon SID with the separately acquired process SID."""
    try:
        require(type(value) is str and re.fullmatch(r'S-1-[0-9]+(?:-[0-9]+){1,15}', value) is not None)
        parts = list(map(int, value.split('-')[2:]))
        authority, subs = parts[0], parts[1:]
        require(0 <= authority < 2**48 and all(0 <= x < 2**32 for x in subs))
        return bytes((1, len(subs))) + authority.to_bytes(6, 'big') + b''.join(struct.pack('<I', x) for x in subs)
    except Exception:
        raise ProbeRejected('guard087_identity_rejected') from None


class BootReader087:
    """Fixed local source query through an owned, bounded MODEL-ONLY runner.

    Runner captures at most25 stdout bytes/no stderr, kills and waits its owned
    child on2s timeout, and checks the pinned child image. These are explicit
    dependency obligations tested here, not native guarantees or permission.
    """
    def __init__(self, runner, reader, meter, shell, script, bindings):
        require(getattr(runner, 'model_only', None) is True and getattr(reader, 'model_only', None) is True)
        require(type(meter) is Meter083 and type(bindings) is tuple and len(bindings) == 2)
        require(bindings[0][0] == shell and bindings[1][0] == script)
        for path, sha in bindings:
            require(type(path) is str and bool(path)); digest(sha)
        self.runner, self.reader, self.meter = runner, reader, meter
        self.shell, self.script, self.bindings = shell, script, bindings
        self.fixed=(runner,reader,meter,shell,script,bindings)
        self.calls = 0; self.stopped = False

    def __call__(self):
        try:
            require(not self.stopped and self.calls < 128)
            require((self.runner,self.reader,self.meter,self.shell,self.script,self.bindings)==self.fixed)
            self.calls += 1
            for path, sha in self.bindings:
                require(self.reader.hash_file(path) == sha)
            before = self.meter.check()
            result = self.runner.query(self.shell, [self.shell, '-NoProfile', '-NonInteractive', '-File', self.script],
                timeout_ms=2000, stdout_cap=25, stderr_cap=0)
            after = self.meter.check()
            require((self.runner,self.reader,self.meter,self.shell,self.script,self.bindings)==self.fixed)
            require(type(result) is dict and set(result) == {'exit_code', 'stdout', 'stderr', 'owned_child_absent'})
            require(type(result['exit_code']) is int and result['exit_code'] == 0)
            require(result['stderr'] == b'' and type(result['stderr']) is bytes and result['owned_child_absent'] is True)
            require(after[2] - before[2] <= 2000 and after[1] - before[1] <= 2000000000)
            for path, sha in self.bindings:
                require(self.reader.hash_file(path) == sha)
            return boot_stamp087(result['stdout'], after[0] * 1000)
        except (Exception, KeyboardInterrupt):
            self.stopped = True
            raise ProbeRejected('boot087_query_rejected') from None


@dataclass(frozen=True)
class Pins087:
    terminal: Identity065 = field(repr=False)
    helper: Identity065 = field(repr=False)
    peer: Peer084 = field(repr=False)
    terminal_directory: str = field(repr=False)
    data_root: str = field(repr=False)
    loaded_library: str = field(repr=False)
    build: Build087 = field(repr=False)
    hashes: dict = field(repr=False)
    sources: dict = field(repr=False)
    def __post_init__(self):
        require(type(self.terminal) is Identity065 and type(self.helper) is Identity065 and type(self.peer) is Peer084)
        for p in (self.terminal,self.helper):
            require(type(p.pid) is int and p.pid>0 and type(p.creation) is int and p.creation>0)
            require(type(p.session) is int and p.session>=0 and type(p.image) is str and bool(p.image))
            digest(p.digest);sid_binary087(p.logon)
        require(type(self.build) is Build087)
        record=self.build.record()
        require(record['runtime_authorized'] is False and record['orders_available'] is False)
        require(type(self.hashes) is dict and set(self.hashes)==HASH_ROLES)
        require(type(self.sources) is dict and set(self.sources)==set(record['input_bindings'])|GUARD_INPUTS)
        paths = []
        for path, sha in (*self.hashes.values(), *self.sources.values()):
            require(type(path) is str and bool(path)); digest(sha); paths.append(path.casefold())
        require(len(set(paths)) == len(paths))
        for s in (self.terminal_directory, self.data_root, self.loaded_library): require(type(s) is str and bool(s))
        require(self.hashes['terminal']==(self.terminal.image,self.terminal.digest))
        require(self.hashes['helper']==(self.helper.image,self.helper.digest))
        require(self.hashes['sdk'][0].casefold()==self.loaded_library.casefold())
        for role,key in (('terminal','terminal_sha256'),('editor','compiler_sha256'),('artifact','artifact_sha256')):
            require(self.hashes[role][1]==record[key])
        for name,sha in record['input_bindings'].items():require(self.sources[name][1]==sha)
        require(self.sources['scripts/boot-proof-087.ps1'][1]==self.hashes['boot_script'][1])


class Session087:
    """Already attached model SDK is owned before constructing either guard."""
    def __init__(self, sdk, reader, pins, meter, loaded_library):
        require(getattr(sdk, 'model_only', None) is True and getattr(reader, 'model_only', None) is True)
        require(type(pins) is Pins087 and type(meter) is Meter083)
        self.sdk, self.reader, self.pins, self.meter = sdk, reader, pins, meter
        self.loaded_library = loaded_library; self.closed = False; self.close_spent = False
        self.shutdown_confirmed = None
    def close(self):
        require(not self.close_spent); self.close_spent = True; self.closed = True
        try: self.shutdown_confirmed = self.sdk.shutdown() is True
        except (Exception, KeyboardInterrupt): self.shutdown_confirmed = False
        return self.shutdown_confirmed


class Metadata087:
    """No SDK quote/history/order/import/initialize methods are exposed."""
    ACCOUNT_TRADE_MODE_DEMO = 0
    def __init__(self, owner): self.owner = owner; self.queries = 0
    def call(self, name, *args):
        require(not self.owner.closed and self.queries < 1024)
        self.owner.meter.check(); self.queries += 1
        value = getattr(self.owner.sdk, name)(*args); self.owner.meter.check(); return value
    def account_info(self): return self.call('account_info')
    def terminal_info(self): return self.call('terminal_info')
    def symbol_info(self, name): require(name == 'EURUSD'); return self.call('symbol_info', name)


class FullGuard087:
    """Concrete uncached SDK/image/helper/source/boot bridge returning Guard083.

    Passing model facts cannot grant native admission. The raw086 adapter still
    acquires pipe/ACL/descriptor/path facts separately inside each full guard.
    """
    def __init__(self, owner, boot):
        require(type(owner) is Session087 and type(boot) is BootReader087)
        require(boot.reader is owner.reader and boot.meter is owner.meter)
        require(boot.bindings==(owner.pins.hashes['boot_shell'],owner.pins.hashes['boot_script']))
        self.owner, self.boot = owner, boot; self.metadata = Metadata087(owner)
        self.account = None; self.calls = 0; self.stopped = False
        self.sdk = owner.sdk; self.reader = owner.reader; self.pins = owner.pins
        self.hashes=dict(owner.pins.hashes);self.sources=dict(owner.pins.sources)

    def graph(self):
        o = self.owner
        require(not o.closed and not o.close_spent and o.sdk is self.sdk and o.reader is self.reader and o.pins is self.pins)
        require(self.metadata.owner is o and self.boot.reader is o.reader and self.boot.meter is o.meter)
        require(o.pins.hashes==self.hashes and o.pins.sources==self.sources)
        require(type(o.sdk.ACCOUNT_TRADE_MODE_DEMO) is int and o.sdk.ACCOUNT_TRADE_MODE_DEMO == 0)
        require(type(o.sdk.__version__) is str and o.sdk.__version__ == SDK_VERSION)
        library=o.loaded_library()
        require(type(library) is str and library.casefold() == o.pins.loaded_library.casefold())

    def identity(self):
        p = self.pins; r = self.reader
        require(r.unique_pid() == p.terminal.pid and r.identity(p.terminal.pid) == p.terminal)
        require(r.identity(p.helper.pid) == p.helper)
        require((p.peer.process_id, p.peer.created, p.peer.session, p.peer.logon) ==
            (p.terminal.pid, p.terminal.creation, p.terminal.session, sid_binary087(p.terminal.logon)))

    def account_metadata(self):
        self.account = runtime_guard(self.metadata, self.account)
        info = self.metadata.terminal_info()
        require(info is not None and type(info.build) is int and info.build == 6244)
        require(type(info.path) is str and info.path.casefold() == self.pins.terminal_directory.casefold())
        require(type(info.data_path) is str and info.data_path.casefold() == self.pins.data_root.casefold())

    def __call__(self):
        try:
            require(not self.stopped and self.calls < 96); self.calls += 1
            self.owner.meter.check(); self.graph(); self.identity(); self.account_metadata()
            require(self.boot() == self.pins.peer.boot)
            for path, sha in (*self.pins.hashes.values(), *self.pins.sources.values()):
                require(self.reader.hash_file(path) == sha)
            self.identity(); self.account_metadata(); self.graph(); self.owner.meter.check()
            return Guard083()
        except (Exception, KeyboardInterrupt):
            self.stopped = True
            raise ProbeRejected('guard087_binding_rejected') from None

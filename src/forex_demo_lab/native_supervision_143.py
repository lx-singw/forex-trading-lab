"""WSL-to-Windows helper-only transport; acquisition remains explicitly invented."""
from collections import deque
import hashlib
import os
from pathlib import Path
import selectors
import subprocess
import threading
import time
import uuid

from .acquisition_lifecycle_138 import Lifecycle, State
from .helper_health_142 import HealthDecoder, MAX_PACKET, STATUS_KEYS, identifier, packet
from .supervision_140 import Supervisor, Ledger, ZERO, Cause


def now_us(): return time.monotonic_ns() // 1000


def local_windows_path(value, basename):
    if (type(value) is not str or len(value) < 4 or value[1:3] != ':\\'
            or value[0].lower() not in 'abcdefghijklmnopqrstuvwxyz' or any(c in value for c in '"\r\n\x00')
            or value.split('\\')[-1] != basename):
        raise ValueError('native143_path')
    path = Path('/mnt/' + value[0].lower() + '/' + value[3:].replace('\\', '/'))
    if '..' in path.parts: raise ValueError('native143_path')
    return path


class WindowsChannel:
    """Only pinned142 binaries; bounded challenge/reply, no shell or broker integration."""
    def __init__(self, build):
        self.build = dict(build)
        self.process = None
        self.buffer = b''
        self.transcript = []
        self.owner_exit_observed = False

    def _remember(self, operation, raw, challenge=None):
        if len(self.transcript) >= 512: raise OSError('native143_transcript_bound')
        self.transcript.append(dict(operation=operation, expected_challenge=challenge, packet=raw.decode('utf-8')))

    def _read(self, timeout):
        deadline = time.monotonic() + timeout
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            while b'\n' not in self.buffer:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining): raise OSError('native143_reply_timeout')
                chunk = os.read(self.process.stdout.fileno(), MAX_PACKET + 1)
                if not chunk: raise OSError('native143_owner_eof')
                self.buffer += chunk
                if len(self.buffer) > MAX_PACKET: raise OSError('native143_reply_bound')
            raw, self.buffer = self.buffer.split(b'\n', 1)
        if self.buffer: raise OSError('native143_unsolicited_packet')
        return raw.removesuffix(b'\r')

    def start(self, token, duration_ms):
        if self.process is not None or not identifier(token) or type(duration_ms) is not int or not 1 <= duration_ms <= 30_000:
            raise ValueError('native143_start')
        if (os.name != 'posix' or not Path('/proc/sys/kernel/osrelease').is_file()
                or 'microsoft' not in Path('/proc/sys/kernel/osrelease').read_text().lower()):
            raise OSError('native143_wsl_interop_required')
        for kind, name in [('owner','ForexDemoHealthOwner142.exe'),('helper','ForexDemoHealthHelper142.exe')]:
            path = local_windows_path(self.build[kind+'_path'], name)
            expected = self.build[kind+'_sha256']
            if (type(expected) is not str or len(expected) != 64 or hashlib.sha256(path.read_bytes()).hexdigest() != expected):
                raise ValueError('native143_binary_binding')
        owner = local_windows_path(self.build['owner_path'], 'ForexDemoHealthOwner142.exe')
        args = [str(owner), '--enable', '--seconds', str((duration_ms+999)//1000), '--token', token,
                '--helper', self.build['helper_path'], '--sha256', self.build['helper_sha256']]
        self.process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
        raw = self._read(5); self._remember('START', raw); return raw

    def request(self, operation, challenge):
        if operation not in ('POLL','CANCEL','EXIT') or not identifier(challenge) or self.process is None:
            raise ValueError('native143_command')
        self.process.stdin.write((operation+' '+challenge+'\n').encode('ascii'))
        self.process.stdin.flush()
        raw = self._read(8 if operation == 'EXIT' else 1)
        self._remember(operation, raw, challenge); return raw

    def close(self):
        if self.process is None: return
        # EOF is a native owner shutdown request. Do not kill by process name or infer
        # that terminating a WSL launching process would kill its Windows owner.
        self.process.stdin.close()
        try:
            self.process.wait(timeout=8); self.owner_exit_observed = True
        finally: self.process.stdout.close()


class NativePort:
    def __init__(self, channel):
        self.channel = channel
        self.calls = dict(start=0,poll=0,cancel=0,confirm_exit=0)
        self.stop_event = threading.Event()
        self.first = threading.Event()
        self.lock = threading.Lock()
        self.cache = deque(maxlen=16)
        self.worker = None
        self.fault = False
        self.receipt = None
        self.token = None
        self.packets = 0
        self.health_evidence = []

    def start(self, token, duration_ms):
        self.calls['start'] += 1
        if (self.worker is not None or not identifier(token) or type(duration_ms) is not int
                or not 1 <= duration_ms <= 30_000): return False
        self.token = token
        try:
            raw = self.channel.start(token,duration_ms)
            value = packet(raw,'native_health142_start_v1',{'schema','token','contained','resumed','helper_pid'})
            if (value['token'] != token or value['contained'] is not True or value['resumed'] is not True
                    or type(value['helper_pid']) is not int or not 0 < value['helper_pid'] < 2**31):
                raise ValueError('native143_start_ack')
        except Exception:
            self.fault = True
            try: self.channel.close()
            except Exception: pass
            return False
        self.worker = threading.Thread(target=self._run,name='forex-helper143',daemon=True)
        self.worker.start()
        if not self.first.wait(3) or self.fault:
            self.stop_event.set(); self.worker.join(10); return False
        return True

    def _run(self):
        decoder = HealthDecoder(self.token)
        try:
            while not self.stop_event.is_set():
                challenge = uuid.uuid4().hex; sent = now_us()
                raw = self.channel.request('POLL',challenge); received = now_us()
                if len(self.health_evidence) >= 512: raise OSError('native143_health_evidence_bound')
                evidence=dict(challenge=challenge,sent_us=sent,received_us=received,packet=raw.decode('utf-8'),accepted=False)
                self.health_evidence.append(evidence)
                report = decoder.decode(raw,challenge,sent,received)
                evidence['accepted']=True
                self.packets += 1
                if report is not None:
                    with self.lock: self.cache.append((received,report))
                    self.first.set()
                self.stop_event.wait(0.1)
        except Exception:
            self.fault = True; self.first.set()
        finally:
            try:
                challenge = uuid.uuid4().hex
                cancel = packet(self.channel.request('CANCEL',challenge),'native_health142_status_v1',
                                STATUS_KEYS)
                if cancel['token'] != self.token or cancel['challenge'] != challenge or cancel['operation'] != 'CANCEL' or cancel['cancel_ack'] is not True:
                    raise ValueError('native143_cancel_ack')
                challenge = uuid.uuid4().hex
                value = packet(self.channel.request('EXIT',challenge),'native_health142_exit_v1',
                               {'schema','token','challenge','exit_observed','cancel_ack','job_closed','clear_ack','close_ack','forced'})
                if (value['token'] != self.token or value['challenge'] != challenge
                        or any(type(value[k]) is not bool for k in ('exit_observed','cancel_ack','job_closed','forced'))
                        or any(value[k] is not None and type(value[k]) is not bool for k in ('clear_ack','close_ack'))):
                    raise ValueError('native143_exit_ack')
                self.receipt = value
            except Exception: self.fault = True
            finally:
                try: self.channel.close()
                except Exception: self.fault = True

    def poll(self, marker):
        self.calls['poll'] += 1
        if self.fault: raise OSError('native143_status_failed')
        with self.lock:
            for received,report in reversed(self.cache):
                if received <= marker: return report
        raise OSError('native143_no_causal_status')

    def cancel(self):
        self.calls['cancel'] += 1
        self.stop_event.set()
        if self.worker is not None: self.worker.join(10)
        return self.receipt is not None and self.receipt['cancel_ack'] is True

    def confirm_exit(self):
        self.calls['confirm_exit'] += 1
        return (self.receipt is not None and self.receipt['exit_observed'] is True
                and self.receipt['job_closed'] is True and self.channel.owner_exit_observed)


class NativeSupervisor(Supervisor):
    """New143 constructor for the frozen140 transition engine and a native port.

    Inherited actions still receive only invented138 Checks/context/triple events.
    This class does not query accounts, ingest prices, or provide a collection CLI.
    """
    def __init__(self, life, helper, ledger, *, enabled=False):
        if (type(life) is not Lifecycle or type(helper) is not NativePort or type(ledger) is not Ledger
                or type(enabled) is not bool or life.state is not State.OFF or life.journal.job_id != ledger.job
                or life.journal.segment != 0 or life.journal.poisoned or life.journal.head != ZERO
                or ledger.sequence != 0 or ledger.closed or ledger.poisoned):
            raise ValueError('native143_configuration')
        # Mirror140's initial state; inherited transition methods remain unchanged.
        self.life,self.helper,self.ledger,self.enabled = life,helper,ledger,enabled
        self.state,self.cause = 'off',Cause.NONE
        self.last=self.origin=self.end=self.ready_until=self.helper_seen_at=None
        self.start_attempted=self.cleanup_attempted=False
        self.cancel_ack=self.exit_ack=None

    def snapshot(self):
        value=super().snapshot()
        value.update(schema='native_supervision143_status_v1',invented_only=False,
                     acquisition_events_invented_only=True,native_helper_launch_available=True,
                     actual_owner_death_tested=False,native_status_packets=self.helper.packets,
                     native_status_failed=self.helper.fault,native_cleanup_receipt=self.helper.receipt)
        receipt=self.helper.receipt
        value['cleanup_complete']=(not self.start_attempted or value['cleanup_complete'] and receipt is not None
                                   and receipt['clear_ack'] is True and receipt['close_ack'] is True)
        return value

"""Offline-tested one-use authority core. No SDK imports, IPC, quotes or orders."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import os
from threading import Lock

DATE = '2026-10-06'
WINDOW_MS = 900_000
RECEIPT_MS = 2_000
VERSION = 'capture_permission_046_v1'


class PermitRejected(ValueError):
    """Fixed reasons only; never expose upstream exceptions or private identity."""


@dataclass(frozen=True)
class Policy:
    phase: str
    digest: str

    def __post_init__(self):
        if type(self.phase) is not str or re.fullmatch('[0-9a-f]{32}', self.phase) is None:
            raise PermitRejected('invalid_phase')
        if type(self.digest) is not str or re.fullmatch('[0-9a-f]{64}', self.digest) is None:
            raise PermitRejected('invalid_policy_digest')


def clock_sample(clock):
    try:
        value = clock()
        if type(value) is not tuple or len(value) != 3 or any(type(x) is not int or x < 0 for x in value):
            raise ValueError()
        utc, mono, boot = value
        if datetime.fromtimestamp(utc // 1000, timezone.utc).date().isoformat() != DATE:
            raise ValueError()
        return value
    except Exception:
        raise PermitRejected('clock_invalid_or_date_expired') from None


def require_guard(guard):
    try:
        if guard() is not True:
            raise ValueError()
    except Exception:
        raise PermitRejected('private_account_or_instrument_guard_rejected') from None


def private_guard(api):
    """Injected fake API in046. Actual mode, symbol and private stable identity."""
    from .clock_observer_042 import runtime_guard
    try:
        identity = runtime_guard(api)
    except Exception:
        raise PermitRejected('private_account_or_instrument_guard_rejected') from None

    def check():
        try:
            runtime_guard(api, identity)
            return True
        except Exception:
            raise PermitRejected('private_account_or_instrument_guard_rejected') from None
    return check


def _reservation_bytes(policy):
    return (json.dumps(dict(version=VERSION, phase=policy.phase, policy_sha256=policy.digest,
        declared_date=DATE, maximum_permissions=1, maximum_session_ms=WINDOW_MS,
        maximum_receipt_ms=RECEIPT_MS, orders_available=False), sort_keys=True) + '\n').encode('ascii')


def start_authority(path, policy, clock, guard, journal):
    """Exclusive reservation BEFORE any authority. Never resume an existing phase."""
    if type(policy) is not Policy:
        raise PermitRejected('invalid_policy')
    path = Path(path)
    data = _reservation_bytes(policy)
    try:
        with path.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        raise PermitRejected('reservation_unavailable_or_already_exists') from None
    # Any following failure leaves the reservation consumed; no cleanup/refund.
    first = clock_sample(clock)
    require_guard(guard)
    return _Authority(path, data, policy, first, clock, guard, journal)


class _Authority:
    def __init__(self, path, data, policy, first, clock, guard, journal):
        self._lock = Lock()
        self._path, self._data, self._policy = path, data, policy
        self._first = self._last = first
        self._clock, self._guard, self._journal = clock, guard, journal
        self._spent, self._closed = False, False

    def _sample(self):
        now = clock_sample(self._clock)
        if any(x < y for x, y in zip(now, self._last)):
            raise PermitRejected('clock_reversed')
        delta = tuple(x-y for x, y in zip(now, self._first))
        if delta[0] >= WINDOW_MS or delta[1] >= WINDOW_MS * 1_000_000 or delta[2] >= WINDOW_MS:
            raise PermitRejected('session_expired')
        if abs(delta[0]-delta[1]//1_000_000) > 1_000 or abs(delta[2]-delta[1]//1_000_000) > 1_000:
            raise PermitRejected('clock_discontinuity')
        self._last = now
        return now

    def _check_reservation(self):
        try:
            if self._path.is_symlink():
                raise ValueError()
            with self._path.open('rb') as stream:
                if stream.read(len(self._data)+1) != self._data:
                    raise ValueError()
        except Exception:
            raise PermitRejected('reservation_missing_or_changed') from None

    def issue(self, phase, policy_digest):
        with self._lock:
            if self._closed or self._spent:
                raise PermitRejected('permission_unavailable')
            # The allowance is burned even if validation, journal or delivery fails.
            self._spent = True
            if type(phase) is not str or phase != self._policy.phase or type(policy_digest) is not str or policy_digest != self._policy.digest:
                raise PermitRejected('request_binding_rejected')
            self._check_reservation()
            self._sample()
            require_guard(self._guard)
            try:
                if self._journal(dict(version=VERSION, phase=self._policy.phase, permissions_consumed=1,
                    reservation_sha256=hashlib.sha256(self._data).hexdigest(), orders_available=False)) is not True:
                    raise ValueError()
            except Exception:
                raise PermitRejected('consumption_journal_rejected') from None
            require_guard(self._guard)
            utc, _, boot = self._sample()
            return dict(version=VERSION, phase=phase, policy_sha256=policy_digest, permission=1,
                issued_boot_ms=boot, expires_boot_ms=min(boot+RECEIPT_MS, self._first[2]+WINDOW_MS),
                expires_utc_ms=min(utc+RECEIPT_MS, self._first[0]+WINDOW_MS))

    def close(self):
        with self._lock:
            self._closed = True

    def summary(self):
        with self._lock:
            return dict(permissions_consumed=int(self._spent), closed=self._closed)


def receipt_valid(receipt, policy, now_utc_ms, now_boot_ms):
    """Reference for the native pure header; permission cannot be a script input."""
    keys={'version','phase','policy_sha256','permission','issued_boot_ms','expires_boot_ms','expires_utc_ms'}
    if type(receipt) is not dict or set(receipt) != keys or type(policy) is not Policy:
        return False
    if receipt['version'] != VERSION or receipt['phase'] != policy.phase or receipt['policy_sha256'] != policy.digest:
        return False
    fields=('permission','issued_boot_ms','expires_boot_ms','expires_utc_ms')
    if any(type(receipt[k]) is not int for k in fields) or type(now_utc_ms) is not int or type(now_boot_ms) is not int:
        return False
    if receipt['permission'] != 1 or not 0 <= receipt['issued_boot_ms'] <= now_boot_ms < receipt['expires_boot_ms']:
        return False
    if any(receipt[k] > 9_007_199_254_740_991 for k in ('issued_boot_ms','expires_boot_ms')) or now_boot_ms > 9_007_199_254_740_991:
        return False
    if not 0 < now_utc_ms <= 32_535_215_999_999 or not 0 < receipt['expires_utc_ms'] <= 32_535_215_999_999:
        return False
    if not 0 < receipt['expires_boot_ms']-receipt['issued_boot_ms'] <= RECEIPT_MS:
        return False
    if not 0 < receipt['expires_utc_ms']-now_utc_ms <= RECEIPT_MS:
        return False
    try:
        return datetime.fromtimestamp(now_utc_ms//1000, timezone.utc).date().isoformat() == DATE
    except Exception:
        return False

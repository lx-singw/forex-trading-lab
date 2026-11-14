"""Offline evidence matching for a FUTURE synthetic MQL sharing probe.

No native adapter, SDK, filesystem access, grants or market calls. Private OS
proofs are injected test capabilities, not evidence that a native run occurred.
"""
from dataclasses import dataclass
import json

from .clock_observer_042 import unique_pairs
from .transport_lifecycle_060 import MQL_ERRORS

PHASE = '64000000000000000000000000000001'
DATE = '2026-10-07'
PREFIX = 'FXDL_SHARE064 '
DATA = bytes((i*41+23)%256 for i in range(84))
MARGIN_MS = 250
ERROR_CATEGORIES = {-1, 0, 6, 7, *MQL_ERRORS.values()}


def hold_reason(start, end, elapsed_us, iterations, stopped, date_ok):
    if (any(type(x) is not int for x in (start, end, elapsed_us, iterations)) or
            type(stopped) is not bool or type(date_ok) is not bool or
            not 0 < start <= end <= 9007199254740991 or elapsed_us < 0):
        return 19
    if stopped: return 18
    if not date_ok: return 10
    if not 1 <= iterations <= 601: return 20
    if not 30000 <= end-start <= 31000 or not 30000000 <= elapsed_us <= 31000000:
        return 21
    if abs((end-start)*1000-elapsed_us) > 1000000: return 19
    return 0


KEYS = {'version','phase','reason_code','opens','reads','closes','read_bytes',
        'size_before','size_after','position_before','position_after','pattern_ok',
        'open_category','read_category','close_category','hold_start_boot_ms',
        'hold_end_boot_ms','hold_elapsed_us','hold_iterations','quote_reads',
        'history_reads','orders','receipt_permissions'}


def parse_record(text):
    if type(text) is not str or len(text) > 2048 or not text.startswith(PREFIX):
        raise ValueError('sharing_prefix_rejected')
    try:
        r = json.loads(text[len(PREFIX):], object_pairs_hook=unique_pairs)
        if type(r) is not dict or set(r) != KEYS: raise ValueError()
        if r['version'] != 'sharing_fixture_064_v1' or r['phase'] != PHASE: raise ValueError()
        ints = KEYS-{'version','phase','pattern_ok'}
        if any(type(r[k]) is not int for k in ints) or type(r['pattern_ok']) is not bool:
            raise ValueError()
        if not 0 <= r['reason_code'] <= 31: raise ValueError()
        if any(r[k] not in (0,1) for k in ('opens','reads','closes')): raise ValueError()
        if not 0 <= r['closes'] <= r['opens'] or not 0 <= r['reads'] <= r['opens']: raise ValueError()
        if any(r[k] != 0 for k in ('quote_reads','history_reads','orders','receipt_permissions')): raise ValueError()
        if any(not -1 <= r[k] <= 85 for k in ('size_before','size_after','position_before','position_after')): raise ValueError()
        if not 0 <= r['read_bytes'] <= 84 or not 0 <= r['hold_iterations'] <= 601: raise ValueError()
        if any(r[k] not in ERROR_CATEGORIES for k in ('open_category','read_category','close_category')): raise ValueError()
        if any(not -1 <= r[k] <= 9007199254740991 for k in ('hold_start_boot_ms','hold_end_boot_ms')): raise ValueError()
        if not -1 <= r['hold_elapsed_us'] <= 900000000: raise ValueError()
        if not r['reads'] and (r['read_bytes'] or r['read_category'] != -1 or r['pattern_ok']): raise ValueError()
        if not r['closes'] and r['close_category'] != -1: raise ValueError()
        if r['reason_code'] == 17:
            empty = dict(opens=0,reads=0,closes=0,read_bytes=0,size_before=-1,size_after=-1,
                position_before=-1,position_after=-1,pattern_ok=False,open_category=-1,
                read_category=-1,close_category=-1,hold_start_boot_ms=-1,
                hold_end_boot_ms=-1,hold_elapsed_us=-1,hold_iterations=0)
            if any(r[k] != v for k,v in empty.items()): raise ValueError()
        if r['reason_code'] == 0:
            expected = dict(opens=1,reads=1,closes=1,read_bytes=84,size_before=84,size_after=84,
                position_before=0,position_after=84,pattern_ok=True,open_category=0,
                read_category=0,close_category=0)
            if any(r[k] != v for k,v in expected.items()): raise ValueError()
            if hold_reason(r['hold_start_boot_ms'],r['hold_end_boot_ms'],r['hold_elapsed_us'],
                           r['hold_iterations'],False,True): raise ValueError()
        return r
    except Exception:
        raise ValueError('sharing_record_rejected') from None


def records_from_log(raw):
    if type(raw) is not bytes or len(raw)>65536 or len(raw)%2:
        raise ValueError('sharing_log_bound_rejected')
    try:
        rows = []
        for line in raw.decode('utf-16-le', errors='strict').splitlines():
            if PREFIX in line:
                if line.count(PREFIX) != 1: raise ValueError()
                rows.append(parse_record(line[line.index(PREFIX):]))
        return rows
    except Exception:
        raise ValueError('sharing_log_rejected') from None


@dataclass(frozen=True)
class Probe:
    stage: str                       # pre / independent / post
    access: str                      # write / delete; open only, no mutation
    start_boot_ms: int
    end_boot_ms: int
    error: int                       # 0 or actual GetLastError32
    opened: bool
    closed: bool
    blocking_companion_handles: int  # MUST be zero, not a copied seal proof
    full_guard_before: bool = False
    full_guard_after: bool = False
    same_file_before: bool = False
    same_file_after: bool = False


@dataclass(frozen=True)
class PrivateProof:
    same_process_image_account_logon_boot: bool = False
    full_hashes_rechecked: bool = False
    artifact_binding: bool = False
    owner_sandbox_no_reparse_single_link: bool = False
    metadata_handle_shares_all: bool = False
    saved_range_fresh_and_consumed: bool = False
    all_handles_closed: bool = False
    exclusive_launch_budget: bool = False
    current_date: str = ''


def match_evidence(rows, probes, proof):
    """Strict injected audit. Success is modeled_match, never native readiness.

    Require one disabled and one enabled record from a separately bounded saved
    range. Absolute boot-counter windows, not log arrival order, bind IO to the
    reviewed MQL hold. Actual private evidence production is future work.
    """
    try:
        if type(proof) is not PrivateProof or proof.current_date != DATE: raise ValueError()
        if any(getattr(proof,k) is not True for k in PrivateProof.__dataclass_fields__ if k != 'current_date'):
            raise ValueError()
        if type(rows) is not list or len(rows) != 2: raise ValueError()
        disabled, r = [parse_record(PREFIX+json.dumps(row)) for row in rows]
        if disabled['reason_code'] != 17 or r['reason_code'] != 0: raise ValueError()
        if type(probes) is not list or len(probes) != 6: raise ValueError()
        expected = [(s,a) for s in ('pre','independent','post') for a in ('write','delete')]
        last = -1
        lo, hi = r['hold_start_boot_ms'], r['hold_end_boot_ms']
        for p,(stage,access) in zip(probes,expected):
            if type(p) is not Probe or (p.stage,p.access) != (stage,access): raise ValueError()
            for k in ('start_boot_ms','end_boot_ms','error','blocking_companion_handles'):
                if type(getattr(p,k)) is not int: raise ValueError()
            if not 0 < p.start_boot_ms <= p.end_boot_ms <= 9007199254740991 or p.start_boot_ms < last:
                raise ValueError()
            last = p.end_boot_ms
            if p.blocking_companion_handles != 0: raise ValueError()
            for k in ('full_guard_before','full_guard_after','same_file_before','same_file_after'):
                if getattr(p,k) is not True: raise ValueError()
            if stage == 'independent':
                if p.error != 32 or p.opened is not False or p.closed is not False: raise ValueError()
                if not lo+MARGIN_MS < p.start_boot_ms <= p.end_boot_ms < hi-MARGIN_MS: raise ValueError()
            else:
                if p.error != 0 or p.opened is not True or p.closed is not True: raise ValueError()
                if stage == 'pre' and not p.end_boot_ms < lo-MARGIN_MS: raise ValueError()
                if stage == 'post' and not hi+MARGIN_MS < p.start_boot_ms: raise ValueError()
        return dict(modeled_match=True,probe_count=6,read_bytes=84,receipt_permissions=0,
                    native_mql_verified=False,native_publication_verified=False,
                    orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
                    quote_reads=0,history_reads=0,orders=0)
    except Exception:
        raise ValueError('sharing_evidence_rejected') from None

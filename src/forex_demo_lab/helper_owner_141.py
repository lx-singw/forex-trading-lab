"""Read bounded141 helper-owner traces; no native process or quote integration."""
import hashlib
import re

from .paired_replay_133 import DENIED, strict_json

MAX_BYTES, MAX_FRAME, MAX_FRAMES = 32768, 1024, 32
SCHEMA = 'invented_owner141_event_v1'
ZERO = '0' * 64
NEXT = {
    None: {'owner_started'},
    'owner_started': {'child_created_suspended', 'owner_stopped'},
    'child_created_suspended': {'child_resumed', 'owner_stopped'},
    'child_resumed': {'helper_ready', 'owner_stopped'},
    'helper_ready': {'invented_triple_begin', 'owner_stopped'},
    'invented_triple_begin': {'invented_triple_abort'},
    'invented_triple_abort': {'owner_stopped'},
    'owner_stopped': set(),
}


def inspect_bytes(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise ValueError('owner141_size')
    lines = raw.split(b'\n'); tail = lines.pop()
    if not lines or len(lines) > MAX_FRAMES or len(tail) >= MAX_FRAME:
        raise ValueError('owner141_frames')
    job = None; head = ZERO; previous = None; last_time = 0
    pid = 0; created = resumed = ready = pending = False
    for sequence, line in enumerate(lines, 1):
        if not 0 < len(line) < MAX_FRAME: raise ValueError('owner141_frame_size')
        try: payload, checksum = line.rsplit(b'\t', 1)
        except ValueError: raise ValueError('owner141_frame') from None
        if hashlib.sha256(payload).hexdigest().encode('ascii') != checksum:
            raise ValueError('owner141_checksum')
        f = strict_json(payload, MAX_FRAME)
        keys = {'Schema', 'Job', 'Sequence', 'Previous', 'Event', 'ElapsedMs', 'HelperPid', 'Contained', 'Ready', 'InventedPending'}
        if type(f) is not dict or set(f) != keys: raise ValueError('owner141_fields')
        if (f['Schema'] != SCHEMA or type(f['Job']) is not str or not re.fullmatch('[0-9a-f]{32}', f['Job'])
                or job is not None and f['Job'] != job or f['Previous'] != head
                or type(f['Sequence']) is not int or f['Sequence'] != sequence
                or type(f['ElapsedMs']) is not int or not last_time <= f['ElapsedMs'] < 2**63
                or type(f['HelperPid']) is not int or not 0 <= f['HelperPid'] < 2**31
                or any(type(f[k]) is not bool for k in ('Contained', 'Ready', 'InventedPending'))
                or type(f['Event']) is not str or f['Event'] not in NEXT[previous]):
            raise ValueError('owner141_transition')
        event = f['Event']
        if event == 'child_created_suspended':
            if f['HelperPid'] == 0: raise ValueError('owner141_child_pid')
            pid, created = f['HelperPid'], True
        elif event == 'child_resumed': resumed = True
        elif event == 'helper_ready': ready = True
        elif event == 'invented_triple_begin': pending = True
        elif event == 'invented_triple_abort': pending = False
        if f['HelperPid'] != pid or f['Contained'] != created or f['Ready'] != ready or f['InventedPending'] != pending:
            raise ValueError('owner141_state_fields')
        job, head, previous, last_time = f['Job'], checksum.decode('ascii'), event, f['ElapsedMs']
    if tail and previous == 'owner_stopped': raise ValueError('owner141_tail_after_stop')
    return dict(schema='helper_owner141_inspection_v1', input_sha256=hashlib.sha256(raw).hexdigest(),
                input_bytes=len(raw), valid_frames=len(lines), final_event=previous,
                owner_stopped_record_present=previous == 'owner_stopped', child_created=created,
                child_resumed=resumed, readiness_ack_recorded=ready, invented_pending=pending,
                elapsed_marker_ms=last_time, truncated_tail_bytes=len(tail), head_sha256=head,
                cause_of_unclosed_prefix=None, actual_process_exit_proven_by_trace=False,
                cleanup_ack_proven_by_trace=False, resume_available=False, native_quote_ingestion_available=False,
                financial_engine_events=0, strategy_evaluated=False, **DENIED)

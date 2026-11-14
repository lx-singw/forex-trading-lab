"""Offline, run-local transport replay. No conversion to financial-engine time."""
import hashlib
import json
from pathlib import Path
import re

from .paired_capture_132 import MAX_BYTES, inspect_bytes

SCHEMA = 'paired_replay133_v1'
GAP_US = 2_000_000
DETAIL_LIMIT = 128
ZERO = '0' * 64
PATH = re.compile(r'data/paired-recorder-132-native/Run132-([1-9][0-9]*)-([0-9]+)-([1-9][0-9]*)/Paired132\.txt')
DENIED = dict(source_utc_certified=False, receipt_utc_certified=False,
              tick_delivery_complete=False, executable_freshness_certified=False,
              producer_authenticated=False, market_data_qualified=False,
              paper_evaluation_available=False, orders_available=False,
              real_money_execution_available=False, source_age=None)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('ascii')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(data, limit):
    if type(data) is not bytes or not 0 < len(data) <= limit:
        raise ValueError('json_size')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('json_duplicate')
            result[key] = value
        return result
    def invalid(_):
        raise ValueError('json_nonfinite')
    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=pairs, parse_constant=invalid)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError('json_invalid') from None


def runtime_binding():
    root = Path(__file__).parent
    return {name: digest((root / name).read_bytes()) for name in
            ('paired_replay_133.py', 'paired_capture_132.py', 'metadata_probe_127.py')}


def _snapshot(quote):
    return [quote[k] for k in ('source_seconds', 'source_millis', 'native_bits', 'volume', 'raw_flags')]


class Replay:
    """One closed, validated file. peek returns a copy; ack commits only that packet.

    Validation reads the whole bounded input, but packets contain only causal
    prefixes. The end-of-file report is unavailable until all packets are acked.
    Checkpoint checksums detect inconsistency; they do not authenticate a user.
    """
    def __init__(self, raw):
        inspected = inspect_bytes(raw)
        self._inspection = inspected
        self._input_hash = digest(raw)
        self._runtime = runtime_binding()
        frames = raw.split(b'\r\n')[:-1]
        header = digest(frames[0] + b'\r\n')
        prefixes = {}
        for frame in frames[1:]:
            fields = frame.split(b'\t')
            if fields[0] == b'C' and fields[2] == b'after':
                prefixes[int(fields[1])] = fields[-1].decode('ascii')
        self._packets = []
        self._prefixes = [ZERO]
        self._next = 0
        prior = None
        highwater = None
        origin = inspected['origin_monotonic_us']
        rows = inspected['rows']
        for start in range(0, len(rows) - 2, 3):
            before, quote, after = rows[start:start + 3]
            marker = after['receipt_monotonic_us'][2] - origin
            quote_gap = None if prior is None else quote['receipt_monotonic_us'][0] - prior['quote']['receipt_monotonic_us'][0]
            source = quote['source_millis']
            repeated = prior is not None and _snapshot(quote) == _snapshot(prior['quote'])
            packet = dict(schema=SCHEMA, declared_kind=inspected['declared_kind'],
                          header_sha256=header, poll=start // 3 + 1,
                          wire_prefix_digest=prefixes[after['sequence']],
                          replay_offset_us=marker,
                          replay_marker_gap_us=None if prior is None else marker - prior['replay_offset_us'],
                          quote_receipt_gap_us=quote_gap,
                          sampling_gap=quote_gap is not None and quote_gap > GAP_US,
                          repeated_snapshot=repeated,
                          same_time_changed=prior is not None and source == prior['quote']['source_millis'] and not repeated,
                          source_reversal=prior is not None and source < prior['quote']['source_millis'],
                          source_below_highwater=highwater is not None and source < highwater,
                          before=before, quote=quote, after=after,
                          clock_domain='recorded_after_guard_monotonic_marker', **DENIED)
            packet['event_id'] = digest(canonical(packet))
            encoded = canonical(packet)
            self._packets.append(encoded)
            self._prefixes.append(digest(self._prefixes[-1].encode('ascii') + b'\n' + encoded))
            prior = packet
            highwater = source if highwater is None else max(highwater, source)

    def peek(self):
        return json.loads(self._packets[self._next]) if self._next < len(self._packets) else None

    def ack(self, packet):
        if type(packet) is not dict:
            raise ValueError('ack_packet')
        try:
            encoded = canonical(packet)
        except (TypeError, ValueError, OverflowError, RecursionError):
            raise ValueError('ack_packet') from None
        if self._next and encoded == self._packets[self._next - 1]:
            return False
        if self._next >= len(self._packets) or encoded != self._packets[self._next]:
            raise ValueError('ack_order_or_content')
        self._next += 1
        return True

    def checkpoint(self):
        state = dict(schema=SCHEMA + '_cursor', input_sha256=self._input_hash,
                     runtime=self._runtime, next_index=self._next,
                     committed_prefix_sha256=self._prefixes[self._next],
                     last_event_id=None if not self._next else json.loads(self._packets[self._next - 1])['event_id'])
        return canonical(dict(state=state, checksum=digest(canonical(state))))

    @classmethod
    def restore(cls, raw, checkpoint):
        saved = strict_json(checkpoint, 16_384)
        replay = cls(raw)
        if type(saved) is not dict or set(saved) != {'state', 'checksum'} or type(saved['state']) is not dict:
            raise ValueError('cursor_envelope')
        state = saved['state']
        index = state.get('next_index')
        if type(index) is not int or not 0 <= index <= len(replay._packets):
            raise ValueError('cursor_index')
        replay._next = index
        if canonical(saved) != replay.checkpoint():
            raise ValueError('cursor_binding_or_integrity')
        return replay

    def financial_tick(self, _packet):
        raise ValueError('absolute_time_and_age_unverified')

    def report(self):
        if self._next != len(self._packets):
            raise ValueError('replay_not_exhausted')
        packets = [json.loads(p) for p in self._packets]
        gaps = [dict(quote_sequence=p['quote']['sequence'],
                     prior_quote_sequence=p['quote']['sequence'] - 3,
                     quote_receipt_gap_us=p['quote_receipt_gap_us']) for p in packets if p['sampling_gap']]
        source = self._inspection
        return dict(schema=SCHEMA + '_audit', input_sha256=self._input_hash,
                    declared_kind=source['declared_kind'], runtime=self._runtime,
                    capture_status=source['capture_status'], stop_code=source['stop_code'],
                    pending_attempt=source['pending_attempt'], truncated_tail=source['truncated_tail'],
                    quarantined_rows=len(source['rows']) % 3,
                    quarantined_quotes=source['quotes_recorded'] - len(packets),
                    packets_committed=self._next, committed_prefix_sha256=self._prefixes[self._next],
                    first_replay_offset_us=packets[0]['replay_offset_us'] if packets else None,
                    last_replay_offset_us=packets[-1]['replay_offset_us'] if packets else None,
                    adjacent_repeated_snapshots=sum(p['repeated_snapshot'] for p in packets),
                    same_time_changed=sum(p['same_time_changed'] for p in packets),
                    source_reversals=sum(p['source_reversal'] for p in packets),
                    source_below_highwater=sum(p['source_below_highwater'] for p in packets),
                    sampling_gap_threshold_us=GAP_US, sampling_gap_count=len(gaps),
                    sampling_gaps=gaps[:DETAIL_LIMIT], sampling_gap_details_truncated=len(gaps) > DETAIL_LIMIT,
                    financial_engine_events=0,
                    replay_clock='recorded_after_guard_monotonic_marker',
                    marker_is_certified_delivery_time=False, interpolation_applied=False,
                    **DENIED)


def replay_bytes(raw):
    replay = Replay(raw)
    while (packet := replay.peek()) is not None:
        replay.ack(packet)
    return replay.report()


def replay_manifest(root, raw_manifest):
    manifest = strict_json(raw_manifest, 65_536)
    if (type(manifest) is not dict or set(manifest) != {'schema', 'runs'}
            or manifest['schema'] != SCHEMA + '_manifest' or type(manifest['runs']) is not list
            or not 1 <= len(manifest['runs']) <= 8):
        raise ValueError('manifest_schema')
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('manifest_root')
    root = root.resolve()
    seen_paths, seen_ids, inputs = set(), set(), []
    for run in manifest['runs']:
        if type(run) is not dict or set(run) != {'id', 'path', 'sha256'}:
            raise ValueError('manifest_run')
        name, path, sha = run['id'], run['path'], run['sha256']
        if (type(name) is not str or not re.fullmatch(r'[a-z][a-z0-9_]{0,31}', name)
                or type(path) is not str or not (match := PATH.fullmatch(path))
                or type(sha) is not str or not re.fullmatch('[0-9a-f]{64}', sha)
                or name in seen_ids or path in seen_paths):
            raise ValueError('manifest_binding')
        seen_ids.add(name); seen_paths.add(path)
        current = root
        for part in Path(path).parts:
            current = current / part
            if current.is_symlink():
                raise ValueError('manifest_symlink')
        if not current.is_file() or current.stat().st_size > MAX_BYTES:
            raise ValueError('manifest_file')
        with current.open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES or digest(raw) != sha:
            raise ValueError('manifest_hash')
        inspected = inspect_bytes(raw)
        if (int(match[1]) != inspected['origin_nominal_gmt_seconds']
                or int(match[3]) != inspected['origin_monotonic_us']):
            raise ValueError('manifest_origin')
        inputs.append((run, raw, inspected['declared_kind']))
    if len({kind for _, _, kind in inputs}) != 1:
        raise ValueError('manifest_mixed_provenance')
    return dict(schema=SCHEMA + '_bundle', runs=[dict(id=run['id'], path=run['path'],
                audit=replay_bytes(raw)) for run, raw, _ in inputs],
                runs_joined=False, **DENIED)


def markdown(bundle):
    lines = ['# Paired capture replay133', '',
             'Separate run-local transport replay; no strategy or profit evaluation.', '']
    for run in bundle['runs']:
        audit = run['audit']
        lines += [f"- {run['id']} ({audit['declared_kind']}): {audit['packets_committed']} paired packets; "
                  f"{audit['adjacent_repeated_snapshots']} repeated snapshots; "
                  f"{audit['sampling_gap_count']} sampling gaps over 2 seconds."]
        for gap in audit['sampling_gaps']:
            lines += [f"  - Quote {gap['prior_quote_sequence']} to {gap['quote_sequence']}: "
                      f"{gap['quote_receipt_gap_us'] / 1_000_000:.6f} seconds."]
        if audit['sampling_gap_details_truncated']:
            lines += ['  - Further gap details omitted; total count retained.']
    lines += ['', 'After-clock guard markers are not certified delivery times. UTC, source age,',
              'producer identity, complete delivery, executable freshness and full costs remain',
              'unverified. Final incomplete polls are quarantined. Runs are never joined.',
              'Financial-engine bridge, paper evaluation and automated orders remain unavailable.', '']
    return '\n'.join(lines)

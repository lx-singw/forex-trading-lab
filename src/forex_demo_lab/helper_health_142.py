"""Validate native helper health. No process launch, account query or quote input."""
import re

from .paired_replay_133 import strict_json
from .supervision_140 import Observation

TOKEN = re.compile('[a-f0-9]{32}')
MAX_PACKET = 2048
MAX_ROUND_TRIP_US = 1_000_000
STATUS_KEYS = {'schema', 'token', 'challenge', 'operation', 'contained', 'running',
               'sample_valid', 'sample_sequence', 'sample_tick_ms', 'owner_tick_ms',
               'create_ack', 'set_ack', 'ready_signal', 'mains', 'helper_running_marker', 'cancel_ack'}


def identifier(value):
    return type(value) is str and TOKEN.fullmatch(value) is not None


def packet(raw, schema, keys):
    value = strict_json(raw, MAX_PACKET)
    if type(value) is not dict or set(value) != keys or value['schema'] != schema:
        raise ValueError('health142_packet')
    return value


class HealthDecoder:
    def __init__(self, token):
        if not identifier(token): raise ValueError('health142_token')
        self.token = token
        self.sequence = self.tick = self.owner_tick = self.observed = None
        self.sample = None

    def decode(self, raw, challenge, sent_us, received_us):
        if (not identifier(challenge) or type(sent_us) is not int or type(received_us) is not int
                or not 0 <= sent_us <= received_us or received_us - sent_us > MAX_ROUND_TRIP_US):
            raise ValueError('health142_round_trip')
        v = packet(raw, 'native_health142_status_v1', STATUS_KEYS)
        bools = STATUS_KEYS - {'schema', 'token', 'challenge', 'operation', 'sample_sequence', 'sample_tick_ms', 'owner_tick_ms'}
        if (v['token'] != self.token or v['challenge'] != challenge or v['operation'] != 'POLL'
                or any(type(v[k]) is not bool for k in bools) or not v['contained'] or v['cancel_ack']
                or any(type(v[k]) is not int or not 0 <= v[k] < 2**63 for k in ('sample_sequence', 'sample_tick_ms', 'owner_tick_ms'))):
            raise ValueError('health142_binding_or_types')
        if self.owner_tick is not None and v['owner_tick_ms'] < self.owner_tick:
            raise ValueError('health142_owner_clock')
        if not v['running']:
            return Observation(self.token, sent_us, running=False)
        if not v['sample_valid']:
            if self.sequence is not None: raise ValueError('health142_sample_lost')
            return None  # Startup with no completed helper sample is not readiness.
        sequence, tick, owner_tick = (v[k] for k in ('sample_sequence', 'sample_tick_ms', 'owner_tick_ms'))
        if sequence < 1 or tick > owner_tick or self.sequence is not None and (sequence < self.sequence or tick < self.tick):
            raise ValueError('health142_sample_clock')
        if v['ready_signal'] and not (v['create_ack'] and v['set_ack'] and v['helper_running_marker']):
            raise ValueError('health142_contradiction')
        sample = tuple(v[k] for k in ('sample_tick_ms', 'create_ack', 'set_ack', 'ready_signal', 'mains', 'helper_running_marker'))
        if sequence == self.sequence and sample != self.sample: raise ValueError('health142_rewritten_sample')
        # Entire response transit is charged conservatively. No cross-OS epoch conversion.
        observed = sent_us - (owner_tick - tick) * 1000
        if observed < 0: raise ValueError('health142_clock_origin')
        if sequence == self.sequence:
            observed = self.observed  # Re-reading cannot refresh an old helper sample.
        elif self.observed is not None and observed < self.observed:
            raise ValueError('health142_time_reversal')
        self.sequence, self.tick, self.owner_tick, self.sample = sequence, tick, owner_tick, sample
        self.observed = observed
        return Observation(self.token, observed, True, v['create_ack'], v['set_ack'], v['ready_signal'], v['mains'])

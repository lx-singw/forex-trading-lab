"""Separate158 startup policy; all157 orchestration/budgets remain unchanged."""
import uuid
from .helper_health_142 import HealthDecoder, STATUS_KEYS, packet
from .native_journal_157 import require
from .recorder_runner_157 import Runner as Runner157


class Runner(Runner157):
    def readiness(self):
        require(self.enabled and self.used and self.attempted)
        decoder=HealthDecoder(self.job)
        for _ in range(32):
            challenge=uuid.uuid4().hex;record=dict(challenge=challenge,healthy=False);self.probes.append(record)
            raw=self.poll(challenge,record);value=packet(raw,'native_health142_status_v1',STATUS_KEYS)
            observation=decoder.decode(raw,challenge,record['sent_us'],record['received_us'])
            require(value['running'])
            if value['sample_valid']:require(value['mains'])
            if observation is not None and all(value[k] for k in ('sample_valid','create_ack','set_ack','ready_signal','helper_running_marker')):
                require(record['received_us']-observation.observed_us<=1_000_000)
                record['healthy']=True;self.relay.decoder=decoder;return
            self.wait(.05);self.tick()
        raise ValueError('relay158_readiness_limit')

"""Repeatable invented lifecycle exercise in new temporary folders only."""
from dataclasses import replace
from pathlib import Path
import tempfile

from .acquisition_lifecycle_138 import AccountMode, Checks, Lifecycle, Policy, State
from .segment_journal_138 import CONTROL_RESERVE, MAX_FRAME, DiskStore, Journal, inspect_segments
from .paired_replay_133 import DENIED


def run_demo():
    def require(condition):
        if not condition:
            raise RuntimeError('invented138_transition')
    good = Checks(actual_mode=AccountMode.DEMO, query_ok=True, identity_unchanged=True,
                  connected=True, non_tester=True, eurusd_visible=True, currency_usd=True, clock_safe=True)
    lost = replace(good, connected=False)
    outcomes = []
    def create(root, *, retry=False, job='a' * 32, small=False):
        journal = Journal(job, lambda name: DiskStore(root, name),
                          file_limit=CONTROL_RESERVE + 4 * MAX_FRAME if small else 32 * 1024 * 1024)
        machine = Lifecycle(journal, Policy(enabled=True, retry_enabled=retry))
        require(machine.start(0, good) and machine.record_context(0, 1, good, good))
        return machine
    def read(root, job='a' * 32):
        folder = Path(root) / ('InventedJob138-' + job)
        return inspect_segments([path.read_bytes() for path in sorted(folder.glob('*.journal'))])
    with tempfile.TemporaryDirectory(prefix='forex-invented138-') as root:
        machine = create(root, small=True)
        for index in range(40):
            now = (index + 1) * 1_000_000
            if not machine.begin_triple(now, good):
                require(machine.record_context(now, now, good, good))
                require(machine.begin_triple(now, good))
            require(machine.finish_triple(now + 10, good))
        machine.stop(41_000_000, good)
        outcomes.append(dict(name='clean_rotation', status=machine.snapshot(), journal=read(root)))
    with tempfile.TemporaryDirectory(prefix='forex-invented138-') as root:
        machine = create(root, retry=True)
        require(machine.begin_triple(1_000_000, good) and machine.finish_triple(1_000_010, good))
        require(machine.begin_triple(2_000_000, good))
        machine.interrupt(2_000_010, good)
        require(machine.retry(machine.wait_until, good))
        now = machine.last
        require(not machine.begin_triple(now, good))
        require(machine.record_context(now, now + 10, good, good))
        require(machine.begin_triple(now + 10, good) and machine.finish_triple(now + 20, good))
        machine.stop(now + 30, good)
        outcomes.append(dict(name='sleep_reconnect', status=machine.snapshot(), journal=read(root)))
    with tempfile.TemporaryDirectory(prefix='forex-invented138-') as root:
        machine = create(root, retry=True); machine.interrupt(2, good)
        for _ in range(3): machine.retry(machine.wait_until, lost)
        require(machine.state is State.STOPPED)
        outcomes.append(dict(name='retry_exhaustion', status=machine.snapshot(), journal=read(root)))
    with tempfile.TemporaryDirectory(prefix='forex-invented138-') as root:
        machine = create(root); require(machine.begin_triple(1_000_000, good))
        machine.journal.poison()  # Invented crash, no attempt to repair or append.
        prefix = read(root)
        restarted = create(root, job='b' * 32); restarted.stop(2, good)
        outcomes.append(dict(name='independent_restart', status=restarted.snapshot(),
                             journal=read(root, 'b' * 32), old_prefix=prefix))
    return dict(schema='invented_acquisition138_demo_v1', scenarios=outcomes,
                invented_only=True, native_acquisition_available=False, actual_account_queried=False,
                actual_quotes_read=False, power_settings_changed=False, keep_awake_API_used=False,
                collection_dates=None, strategy_evaluated=False, profitability_established=False, **DENIED)


def markdown(report):
    lines = ['# Invented acquisition138 exercise', '',
             'Temporary synthetic event journals; no native data or account query.', '',
             '| Scenario | Final state | Segments | Acknowledged triples | Retries | Resume available |',
             '| --- | --- | ---: | ---: | ---: | --- |']
    for scenario in report['scenarios']:
        s = scenario['status']
        lines.append(f"| {scenario['name']} | {s['state']} | {s['segments']} | "
                     f"{s['acknowledged_committed_sequence']} | {s['retry_attempts']} | false |")
    lines += ['', 'No freshness, clock qualification, strategy return or order capability is established.', '']
    return '\n'.join(lines)

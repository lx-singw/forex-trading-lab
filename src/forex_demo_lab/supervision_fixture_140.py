"""Deterministic invented supervisor exercise; temporary journals only."""
from dataclasses import replace
from pathlib import Path
import tempfile

from .acquisition_lifecycle_138 import AccountMode, Checks, Lifecycle, Policy
from .segment_journal_138 import DiskStore, Journal
from .supervision_140 import Ledger, Observation, Supervisor, SyntheticHelper, READY_TIMEOUT_US, inspect_ledger
from .paired_replay_133 import DENIED


def run_demo():
    good = Checks(actual_mode=AccountMode.DEMO, query_ok=True, identity_unchanged=True,
                  connected=True, non_tester=True, eurusd_visible=True, currency_usd=True, clock_safe=True)
    ready = Observation(create_ack=True, set_ack=True, ready_signal=True)
    scenarios = []
    def require(condition):
        if not condition: raise RuntimeError('invented140_transition')
    for name in ('delayed_ready_success', 'helper_exit_pending', 'owner_lost_pending', 'startup_timeout',
                 'helper_start_failed', 'network_reconnect', 'cleanup_unconfirmed'):
        with tempfile.TemporaryDirectory(prefix='forex-supervision140-') as root:
            job = 'a' * 32
            life = Lifecycle(Journal(job, lambda token: DiskStore(root, token)),
                             Policy(enabled=True, retry_enabled=True, max_elapsed_us=60_000_000))
            helper = SyntheticHelper()
            supervisor = Supervisor(life, helper, Ledger(root, job), enabled=True)
            if name == 'helper_start_failed':
                helper.start_ack = False; require(not supervisor.start(0, good))
            elif name == 'startup_timeout':
                require(supervisor.start(0, good)); require(not supervisor.observe(READY_TIMEOUT_US, good))
            else:
                require(supervisor.start(0, good))
                require(not supervisor.begin_triple(1, good))
                helper.report = ready
                require(supervisor.observe(2, good))
                require(supervisor.record_context(3, 4, good, good))
                require(supervisor.begin_triple(10, good))
                if name == 'helper_exit_pending':
                    helper.report = replace(ready, running=False); require(not supervisor.finish_triple(11, good))
                elif name == 'owner_lost_pending':
                    require(not supervisor.finish_triple(11, good, owner_alive=False))
                elif name == 'network_reconnect':
                    require(not supervisor.finish_triple(11, replace(good, connected=False)))
                    due = life.wait_until
                    require(supervisor.retry(due, good))
                    require(not supervisor.begin_triple(due, good))
                    require(supervisor.record_context(due, due + 1, good, good))
                    require(supervisor.begin_triple(due + 2, good)); require(supervisor.finish_triple(due + 3, good))
                    supervisor.stop(due + 4, good)
                else:
                    require(supervisor.finish_triple(11, good))
                    if name == 'cleanup_unconfirmed': helper.exit_ack = False
                    supervisor.stop(12, good)
            segments = [p.read_bytes() for p in sorted((Path(root) / ('InventedJob138-' + job)).glob('*.journal'))]
            audit = inspect_ledger(supervisor.ledger.path.read_bytes(), segments)
            scenarios.append(dict(name=name, status=supervisor.snapshot(), audit=audit))
    return dict(schema='invented_supervision140_demo_v1', scenarios=scenarios, invented_only=True,
                native_helper_launched=False, native_collector_started=False, actual_owner_death_tested=False,
                actual_account_queried=False, actual_quotes_read=False, power_API_calls=0,
                collection_dates=None, strategy_evaluated=False, profitability_established=False, **DENIED)


def markdown(report):
    lines = ['# Invented supervision140 exercise', '',
             'Synthetic helper reports linked to lifecycle138; no native processes or market data.', '',
             '| Scenario | Stop cause | Acknowledged triples | Cleanup confirmed in model | Prefix bound |',
             '| --- | --- | ---: | --- | --- |']
    for scenario in report['scenarios']:
        s, audit = scenario['status'], scenario['audit']
        lines.append(f"| {scenario['name']} | {s['cause']} | {s['life']['acknowledged_committed_sequence']} | "
                     f"{str(s['cleanup_complete']).lower()} | {str(audit['lifecycle_acknowledged_prefix_bound']).lower()} |")
    lines += ['', 'Readiness is an invented acknowledgement, not certified power-request effectiveness.',
              'No resume, native helper launch, actual owner-death handling, strategy return or orders.', '']
    return '\n'.join(lines)

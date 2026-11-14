from copy import deepcopy
import hashlib
import json
import unittest

from forex_demo_lab.execution_audit import compare,scenarios
from forex_demo_lab.execution_metrics import (ExecutableEquityTickSimulator,
                                             ExecutableEquityResearchTickSimulator,METRIC_VERSION)
from forex_demo_lab.execution_audit_runtime import make as original_make,snapshot
from forex_demo_lab.execution_audit_runtime_b import make


class ExecutionMetricTests(unittest.TestCase):
    def case(self,name):return next(c for c in scenarios() if c['case_id']==name)

    def run_path(self,case):
        sim=make(case);trace=[]
        for tick in case['ticks']:sim.step_tick(tick);trace.append(snapshot(sim))
        sim.finish();actual=dict(trace=trace,final=snapshot(sim));compare(actual,case['expected'])
        return sim

    def test_long_and_short_target_overshoots_cannot_inflate_peak(self):
        for side in ('long','short'):
            sim=self.run_path(self.case(side+'_target_overshoot_tick'))
            self.assertAlmostEqual(sim.peak_tick_equity,10042.46)
            self.assertAlmostEqual(sim.max_tick_drawdown,.000341)

    def test_actual_fixed_selector_has_same_fills_and_correct_diagnostics(self):
        for side in ('long','short'):
            sim=self.run_path(self.case('c04_actual_'+side))
            self.assertEqual(len(sim.decision_log),1)
            self.assertEqual(sim.decision_log[0]['features']['selected_mode'],'trend')
            self.assertAlmostEqual(sim.max_tick_drawdown,.001395)

    def test_stop_gap_fees_rollover_and_pause_stay_consistent(self):
        for side in ('long','short'):
            self.run_path(self.case(side+'_rollover_stop_gap_research'))

    def test_held_quote_equity_retained_when_no_exit_triggers(self):
        case=self.case('long_ask_widening_tick');sim=make(case)
        for tick in case['ticks']:sim.step_tick(tick)
        self.assertIsNotNone(sim.position)
        tick=case['ticks'][-1]
        self.assertEqual(sim.last_equity,sim.equity(tick['bid'],tick['ask']-tick['bid']))

    def test_legacy_checkpoint_requires_replay_and_cannot_import_old_peak(self):
        for name in ('long_target_overshoot_tick','c04_actual_long'):
            case=self.case(name);old=original_make(case);new=make(case)
            old.step_tick(case['ticks'][0])
            kw=dict(candidate=new.candidate,evaluation_start_ms=new.evaluation_start_ms) if hasattr(new,'candidate') else {}
            with self.assertRaisesRegex(ValueError,'version mismatch'):
                type(new).restore(old.checkpoint(),new.config,**kw)

    def test_valid_checksum_with_wrong_metric_version_rejected(self):
        case=self.case('long_ask_widening_tick');sim=make(case);sim.step_tick(case['ticks'][0])
        value=json.loads(sim.checkpoint());value['payload']['state']['execution_metric_version']='other'
        body=json.dumps(value['payload'],sort_keys=True,allow_nan=False)
        value['sha256']=hashlib.sha256(body.encode()).hexdigest()
        with self.assertRaisesRegex(ValueError,'version mismatch'):
            type(sim).restore(json.dumps(value),sim.config)

    def test_metric_version_roundtrips_and_duplicate_after_rollover_is_noop(self):
        case=self.case('short_skipped_rollovers_research');sim=make(case)
        for tick in case['ticks'][:3]:sim.step_tick(tick)
        restored=type(sim).restore(sim.checkpoint(),sim.config,candidate=sim.candidate,evaluation_start_ms=sim.evaluation_start_ms)
        self.assertEqual(restored.execution_metric_version,METRIC_VERSION)
        before=restored.checkpoint();self.assertFalse(restored.step_tick(case['ticks'][2]))
        self.assertEqual(restored.checkpoint(),before)
        restored.step_tick(case['ticks'][3]);sim.step_tick(case['ticks'][3])
        restored.finish();sim.finish();self.assertEqual(restored.checkpoint(),sim.checkpoint())


if __name__=='__main__':unittest.main()

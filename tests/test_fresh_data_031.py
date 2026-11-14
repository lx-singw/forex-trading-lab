import json
from types import SimpleNamespace as NS
import unittest

from forex_demo_lab.collection import SPEC_FIELDS
from forex_demo_lab.fresh_data_031 import MAX_READS, ProbeRejected, clock_summary, observation, probe

BASE = 1791280800000  # 2026-10-06 10:00 UTC


class API:
    ACCOUNT_TRADE_MODE_DEMO = 0

    def __init__(self):
        self.terminal = NS(connected=True, trade_allowed=False)
        self.account = NS(trade_mode=0, currency='USD', login=246813579, server='private_test_server')
        self.symbol = NS(**{k: 1 for k in SPEC_FIELDS})
        self.symbol.visible = True
        self.symbol.currency_base, self.symbol.currency_profit = 'EUR', 'USD'
        self.symbol.currency_margin = 'EUR'
        self.tick = NS(time_msc=BASE+10800000, bid=1.1, ask=1.1001)
        self.calls = self.guards = 0
        self.on_read = self.on_guard = None

    def terminal_info(self):
        return self.terminal

    def account_info(self):
        self.guards += 1
        if self.on_guard:
            self.on_guard(self)
        return self.account

    def symbol_info(self, name):
        assert name == 'EURUSD'
        return self.symbol

    def symbol_info_tick(self, name):
        assert name == 'EURUSD'
        self.calls += 1
        if self.on_read:
            self.on_read(self)
        return self.tick


class Clock:
    def __init__(self):
        self.ms = BASE

    def __call__(self):
        self.ms += 1
        return self.ms, (self.ms-BASE)*1000000

    def sleep(self, seconds):
        self.ms += int(seconds*1000)


class FreshDataTests(unittest.TestCase):
    def run_probe(self, api=None, reads=3, clock=None):
        api, clock = api or API(), clock or Clock()
        return probe(api, clock, clock.sleep, reads)

    def test_completed_probe_and_privacy(self):
        api = API()
        value = self.run_probe(api)
        self.assertEqual(value['status'], 'completed_receipt_probe')
        self.assertEqual(len(value['observations']), 3)
        self.assertEqual(value['clock_summary']['repeated_snapshots'], 2)
        text = json.dumps(value)
        for private in ('246813579', 'private_test_server', 'login', 'password', 'balance'):
            self.assertNotIn(private, text)
        self.assertFalse(value['fresh_performance_eligible'])
        self.assertFalse(value['continuous_tick_capture'])
        self.assertFalse(value['orders_available'])

    def test_actual_real_contest_unknown_and_boolean_mode_rejected(self):
        for mode in (1, 2, 7, False):
            api = API(); api.account.trade_mode = mode
            value = self.run_probe(api)
            self.assertEqual(value['stop_reason'], 'actual_account_not_demo')
            self.assertEqual(api.calls, 0)

    def test_disconnected_and_missing_objects_rejected(self):
        for name in ('terminal', 'account', 'connected'):
            api = API()
            if name=='connected': api.terminal.connected = False
            else: setattr(api, name, None)
            value = self.run_probe(api)
            self.assertEqual(value['stop_reason'], 'disconnected')
            self.assertEqual(api.calls, 0)

    def test_algo_and_currency_rejected(self):
        for change, reason in ((lambda a:setattr(a.terminal,'trade_allowed',True),'algo_trading_enabled'),
                               (lambda a:setattr(a.account,'currency','EUR'),'account_currency_not_usd')):
            api = API(); change(api)
            self.assertEqual(self.run_probe(api)['stop_reason'], reason)
            self.assertEqual(api.calls, 0)

    def test_account_and_server_change_after_read_discard_quote(self):
        for field in ('login','server'):
            api=API()
            api.on_read=lambda a:setattr(a.account,field,999 if field=='login' else 'changed')
            value=self.run_probe(api)
            self.assertEqual(value['stop_reason'],'account_changed_or_invalid')
            self.assertEqual(value['actual_quote_reads'],1)
            self.assertEqual(value['observations'],[])

    def test_account_change_before_next_read_keeps_partial(self):
        api=API()
        def change(a):
            if a.guards==5:a.account.trade_mode=1
        api.on_guard=change
        value=self.run_probe(api)
        self.assertEqual(value['actual_quote_reads'],1)
        self.assertEqual(len(value['observations']),1)
        self.assertEqual(value['stop_reason'],'actual_account_not_demo')

    def test_completion_guard_detects_change(self):
        api=API()
        def change(a):
            if a.guards==5:a.terminal.connected=False
        api.on_guard=change
        value=self.run_probe(api,reads=1)
        self.assertEqual(len(value['observations']),1)
        self.assertEqual(value['stop_reason'],'disconnected')

    def test_symbol_missing_hidden_or_wrong_currency(self):
        for field in ('missing','visible','currency_base','currency_profit'):
            api=API()
            if field=='missing':api.symbol=None
            else:setattr(api.symbol,field,False if field=='visible' else 'GBP')
            value=self.run_probe(api)
            self.assertEqual(value['stop_reason'],'symbol_not_supported_or_visible')
            self.assertEqual(api.calls,0)

    def test_invalid_crossed_nonfinite_missing_quotes(self):
        for quote in (None,NS(time_msc=BASE,bid=1.1,ask=1.0),NS(time_msc=BASE,bid=float('nan'),ask=1.1),
                      NS(time_msc=True,bid=1.0,ask=1.1),NS(time_msc=BASE,bid=0,ask=1.1)):
            api=API();api.tick=quote
            value=self.run_probe(api)
            self.assertEqual(len(value['observations']),0)
            self.assertIn(value['stop_reason'],('quote_unavailable','invalid_quote'))

    def test_decreasing_source_time_stops_without_sorting(self):
        api=API()
        def change(a):
            if a.calls==2:a.tick=NS(time_msc=BASE,bid=1.1,ask=1.1001)
        api.on_read=change
        value=self.run_probe(api)
        self.assertEqual(value['stop_reason'],'source_clock_reversed')
        self.assertEqual(len(value['observations']),1)

    def test_clock_reversal_and_reserved_receipt(self):
        q=API().tick
        for before,after in (((BASE,10),(BASE-1,11)),((BASE,10),(BASE,9)),
                             ((1793491200000,10),(1793491200001,11))):
            with self.assertRaises(ProbeRejected):observation(0,q,before,after)
        prior=observation(0,q,(BASE,10),(BASE+1,11))
        with self.assertRaises(ProbeRejected):observation(1,q,(BASE,12),(BASE+2,13),prior)

    def test_raw_labels_outside_probe_bound_rejected(self):
        api=API();api.tick.time_msc=BASE+2*86400000
        self.assertEqual(self.run_probe(api)['stop_reason'],'raw_label_outside_current_probe_bound')

    def test_read_and_elapsed_budgets(self):
        for reads in (0,121,True):
            with self.assertRaises(ValueError):self.run_probe(reads=reads)
        api=API(); clock=Clock()
        value=self.run_probe(api,reads=MAX_READS,clock=clock)
        self.assertEqual(api.calls,120)
        self.assertEqual(len(value['observations']),120)
        clock=Clock();api=API()
        api.on_read=lambda a:setattr(clock,'ms',clock.ms+61000)
        value=self.run_probe(api,clock=clock)
        self.assertEqual(value['stop_reason'],'elapsed_budget_exhausted')
        self.assertEqual(len(value['observations']),0)

    def test_api_exception_details_redacted_and_partial_kept(self):
        api=API()
        def fail(a):
            if a.calls==2:raise RuntimeError('private password secret login 246813579')
        api.on_read=fail
        value=self.run_probe(api)
        self.assertEqual(len(value['observations']),1)
        self.assertEqual(value['stop_reason'],'api_or_clock_failure_details_redacted')
        self.assertNotIn('secret',json.dumps(value))

    def test_tied_time_changed_prices_and_statistics(self):
        first=observation(0,NS(time_msc=BASE+100,bid=1.1,ask=1.2),(BASE,10),(BASE+1,11))
        second=observation(1,NS(time_msc=BASE+100,bid=1.2,ask=1.3),(BASE+2,12),(BASE+4,14),first)
        self.assertFalse(second['repeated_snapshot'])
        self.assertEqual(clock_summary([first,second]),dict(observations=2,repeated_snapshots=0,
            raw_minus_receipt_lower_ms=96,raw_minus_receipt_upper_ms=100,max_read_latency_ms=2))

    def test_invalid_contract_does_not_escape_nan(self):
        api=API();api.symbol.point=float('nan')
        value=self.run_probe(api)
        self.assertIsNone(value['contract_snapshot'])
        self.assertEqual(value['stop_reason'],'invalid_contract_snapshot')

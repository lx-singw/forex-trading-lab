"""Independent rational structural-stop accounting and coherent pipeline guards."""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import elliott_execution_125 as engine
from forex_demo_lab.elliott_execution_fixture_125 import CASES, fixture

D = engine.D
F = lambda n: Fraction(str(n))


def audit_account(value, report):
    """Independent Fraction ledger/admission reference; no production size/mark/fill calls."""
    profile, model = report["profile"], report["candidate"]
    slip, fee, floor, long_rate, short_rate = ((F('.00002'), F(7), F(0), F(-3), F('-1.5')) if profile == 'base'
                                             else (F('.00005'), F(10), F('.00012'), F('-4.5'), F('-2.25')))
    cash = equity = peak = F(10000)
    dd, day, anchor, paused, held, last, last_event = F(0), None, cash, False, None, None, None
    used, bindings, cursor, trade_count = set(), {}, 0, 0
    gross_total = commissions = financing = F(0)
    ledger, outcomes = report['final_state']['ledger'], report['final_state']['outcomes']
    assert len(value['events']) == len(outcomes)
    def near(actual, expected):
        assert abs(F(actual) - expected) <= F('1e-35'), (actual, str(expected))
    def prices(event):
        bid = F(event['bid']); spread = max(F(event['ask']) - bid, floor)
        return bid, bid + spread, spread
    def record(kind, event, numbers=None, **fields):
        nonlocal cursor
        row = ledger[cursor]
        assert row['index'] == cursor and row['sequence'] == event['sequence'] and row['source_msc'] == event['source_msc'] and row['kind'] == kind
        for k, n in (numbers or {}).items():near(row[k], n)
        for k, v in fields.items():assert row[k] == v, (kind, k, row[k], v)
        cursor += 1
        return row
    def mark():
        nonlocal equity, peak, dd, paused
        equity, margin = cash, F(0)
        if held:
            bid, ask, _ = prices(last)
            equity += held['side'] * ((bid if held['side'] > 0 else ask) - held['entry']) * held['lots'] * 100000
            margin = held['margin']
        peak = max(peak, equity); dd = max(dd, (peak - equity) / peak)
        paused = paused or equity <= anchor * F('.99')
        return {'balance_usd': cash, 'equity_usd': equity, 'margin_usd': margin, 'free_margin_usd': equity - margin}
    def exit_at(event, reason, price):
        nonlocal cash, commissions, gross_total, held, trade_count
        assert price > 0
        gross = held['side'] * (price - held['entry']) * held['lots'] * 100000
        commission = held['lots'] * fee / 2
        cash += gross - commission; commissions += commission; gross_total += gross
        net = gross - commission - held['entry_fee'] + held['financing']
        record('exit_fill', event, {'price': price, 'lots': held['lots'], 'gross_usd': gross, 'fee_usd': commission,
            'financing_usd': held['financing'], 'net_trade_usd': net, 'balance_usd': cash, 'estimated_stop_risk_usd': held['estimated']},
            position_id=held['id'], side=held['side'], reason=reason)
        record('release', event, position_id=held['id'])
        trade_count += 1; held = None
    for event, outcome in zip(value['events'], outcomes):
        current_day = event['source_msc'] // 86400000
        if current_day != day:
            day, anchor, paused = current_day, equity, False
        if held:
            for preceding in range(held['financed_day'], day):
                weekday = datetime.fromtimestamp(preceding * 86400, timezone.utc).weekday()
                multiplier = 0 if weekday >= 5 else 3 if weekday == 2 else 1
                debit = held['lots'] * (long_rate if held['side'] > 0 else short_rate) * multiplier
                cash += debit; financing += debit; held['financing'] += debit
                record('financing', event, {'amount_usd': debit, 'balance_usd': cash}, position_id=held['id'],
                       rollover_msc=(preceding + 1) * 86400000, weekday=weekday, multiplier=multiplier)
            held['financed_day'] = day
        feature = event['feature']; signal = feature['signal'] if model != 'CASH' else None
        side = signal['side'] if signal else 0
        bid, ask, spread = prices(event)
        row = next(r for r in value['calendar']['sessions'] if r['start_msc'] <= event['source_msc'] < r['end_msc'])
        repeated = last_event is not None and event['source_msc'] == last_event['source_msc']
        executable = not repeated and event['receipt_msc'] - event['source_msc'] <= 2000 and row['status'] == 'trading'
        held_on_arrival = held is not None
        if executable:
            last = event
            if held:
                price = bid if held['side'] > 0 else ask
                if (price <= held['stop'] if held['side'] > 0 else price >= held['stop']):exit_at(event, 'stop', price - held['side'] * slip)
                elif (price >= held['target'] if held['side'] > 0 else price <= held['target']):exit_at(event, 'target', held['target'])
        before = mark()
        binding = hashlib.sha256(json.dumps({'candidate': model, 'feature': feature}, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        key = str(feature['session_id']) if feature['session_id'] is not None else None
        if key is not None:bindings[key] = binding
        proposal = None
        if key is None:reason = 'no_completed_feature'
        elif event['source_msc'] <= feature['available_msc']:reason = 'before_feature'
        elif event['receipt_msc'] - event['source_msc'] > 2000:reason = 'stale_quote'
        elif repeated:reason = 'repeated_source'
        elif row['status'] != 'trading':reason = 'closed_quote'
        elif spread > F('.00015'):reason = 'wide_quote'
        elif key in used:reason = 'session_consumed'
        else:
            used.add(key)
            if held_on_arrival:reason = 'held_position'
            elif paused:reason = 'daily_pause'
            elif signal is None:reason = 'inactive_signal'
            elif equity <= 0:reason = 'nonpositive_equity'
            else:
                entry = ask + slip if side > 0 else bid - slip
                stop = F(signal['prospective_invalidation'])
                distance = side * (entry - stop); target = entry + side * 2 * distance
                if distance <= spread + slip or min(entry, stop, target) <= 0:reason = 'price_geometry'
                else:
                    budget, per_lot = equity / 400, (distance + slip) * 100000 + fee
                    per_margin, immediate_per = entry * 100000 / 30, (spread + 2 * slip) * 100000 + fee
                    risk_lots, margin_lots = budget / per_lot, max(F(0), before['free_margin_usd']) / (per_margin + fee / 2)
                    raw = min(risk_lots, margin_lots, F(1)) * 100
                    lots = Fraction(raw.numerator // raw.denominator, 100)
                    if lots < F('.01'):reason = 'minimum_lot_risk' if risk_lots < F('.01') else 'minimum_lot_margin'
                    elif equity - lots * immediate_per <= anchor * F('.99'):reason = 'daily_headroom'
                    else:
                        reason = 'entry_filled'; proposal = outcome['proposal']; assert proposal is not None
                        numbers = {'lots': lots, 'entry': entry, 'stop': stop, 'target': target, 'stop_distance': distance,
                            'risk_fraction': F('.0025'), 'risk_budget_usd': budget, 'estimated_stop_risk_usd': lots * per_lot,
                            'immediate_liquidation_debit_usd': lots * immediate_per, 'margin_usd': lots * per_margin, 'entry_fee_usd': lots * fee / 2}
                        for k, n in numbers.items():near(proposal[k], n)
                        assert proposal['candidate'] == 'EWPB_D124' and proposal['side'] == side and proposal['feature_binding'] == binding
                        assert proposal['pattern_id'] == signal['pattern_id']
                        assert lots * per_lot <= budget and lots * (per_margin + fee / 2) <= before['free_margin_usd']
                        pid = proposal['proposal_id']
                        assert pid == hashlib.sha256(json.dumps({k:v for k,v in proposal.items() if k!='proposal_id'},sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
                        record('reserve', event, position_id=pid)
                        cash -= lots * fee / 2; commissions += lots * fee / 2
                        held = {'id': pid, 'side': side, 'lots': lots, 'entry': entry, 'stop': stop, 'target': target,
                                'margin': lots * per_margin, 'entry_fee': lots * fee / 2, 'estimated': lots * per_lot,
                                'financing': F(0), 'financed_day': day}
                        record('entry_fill', event, {'price': entry, 'lots': lots, 'fee_usd': lots * fee / 2, 'balance_usd': cash}, position_id=pid, side=side)
                        mark()
        assert outcome['reason'] == reason and outcome['proposal'] is proposal, (event['sequence'],outcome['reason'],reason)
        assert outcome['feature_binding'] == binding and outcome['feature_side'] == side
        assert outcome['held_at_arrival'] == held_on_arrival and outcome['execution_quote'] == executable
        for k,n in before.items():near(outcome['pre_entry_account'][k], n)
        for k,n in mark().items():near(outcome['account'][k], n)
        near(outcome['day_start_equity'], anchor); near(outcome['peak_equity_usd'], peak); near(outcome['max_drawdown'], dd)
        assert outcome['paused'] is paused
        last_event = event
    if held:
        assert outcomes[-1]['execution_quote']
        bid, ask, _ = prices(value['events'][-1]); side = held['side']
        exit_at(value['events'][-1], 'boundary', (bid if side > 0 else ask) - side * slip)
    final = mark()
    assert cursor == len(ledger) and held is None
    for k,n in final.items():near(report['final_state'][k],n)
    assert report['final_state']['held'] is None and report['final_state']['reservation'] is None
    assert report['final_state']['consumed_sessions'] == list(dict.fromkeys(str(e['feature']['session_id']) for e,o in zip(value['events'],outcomes) if o['reason'] not in ('no_completed_feature','before_feature','stale_quote','repeated_source','closed_quote','wide_quote','session_consumed')))
    assert report['final_state']['session_bindings'] == bindings and report['final_state']['paused'] is paused
    for k,n in {'initial_cash_usd':F(10000),'final_cash_usd':cash,'toy_net_usd':cash-10000,'toy_return':(cash-10000)/10000,
                'gross_usd':gross_total,'commissions_usd':commissions,'financing_usd':financing,'max_drawdown':dd}.items():near(report['summary'][k],n)
    assert report['summary']['closed_positions']==trade_count and cash-10000 == gross_total-commissions+financing
    return {'ledger_rows':len(ledger),'quote_outcomes':len(outcomes),'closed_positions':trade_count}


class ExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.TemporaryDirectory()
        cls.root = Path(cls.home.name)
        cls.cache = {}

    @classmethod
    def tearDownClass(cls):
        cls.home.cleanup()

    def compiled(self, case='long_target', partition=0):
        key=(case,partition)
        if key not in self.cache:
            value=engine.validate_fixture(fixture(case)); directory=self.root/(case+'-'+str(partition)); directory.mkdir()
            engine.prepare_partition(value,value['partitions'][partition],directory)
            self.cache[key]=(directory/'compiled-input.json',directory/'compiled-frozen.json')
        return self.cache[key]

    def account(self, case='long_target', profile='base', model='EWPB_D124', partition=0):
        return engine.Account(*self.compiled(case,partition),profile,model)

    def run_account(self,*args,**kwargs):
        account=self.account(*args,**kwargs); report=account.run(); audit_account(account._fixture,report); return account

    def test_both_sides_and_both_profiles_independently_reconcile(self):
        for case in ('long_target','short_target','long_stop','short_stop','long_gap','short_gap'):
            for profile in ('base','adverse'):
                with self.subTest(case=case,profile=profile):self.run_account(case,profile)

    def test_target_is_limit_without_favorable_overshoot(self):
        account=self.run_account(); state=account.state
        entry=next(o['proposal'] for o in state['outcomes'] if o['proposal'])
        exit=next(r for r in state['ledger'] if r['kind']=='exit_fill')
        self.assertEqual(exit['reason'],'target'); self.assertEqual(exit['price'],entry['target'])
        self.assertLess(D(exit['price']),D(account._fixture['events'][1]['bid']))

    def test_structural_stop_is_not_reset_relative_to_entry(self):
        for profile in ('base','adverse'):
            account=self.run_account('long_target',profile)
            proposal=next(o['proposal'] for o in account.state['outcomes'] if o['proposal'])
            self.assertEqual(proposal['stop'],account._fixture['events'][0]['feature']['signal']['prospective_invalidation'])
            self.assertEqual(D(proposal['target']),D(proposal['entry'])+2*(D(proposal['entry'])-D(proposal['stop'])))

    def test_gap_stop_uses_observed_side_quote_and_exceeds_estimate(self):
        for case in ('long_gap','short_gap'):
            account=self.run_account(case); state=account.state
            exit=next(r for r in state['ledger'] if r['kind']=='exit_fill')
            event=account._fixture['events'][exit['sequence']]
            raw=D(event['bid']) if exit['side']==1 else D(event['ask'])
            self.assertEqual(D(exit['price']),raw-exit['side']*D('.00002'))
            self.assertGreater(-D(exit['net_trade_usd']),D(exit['estimated_stop_risk_usd']))
            self.assertTrue(state['outcomes'][exit['sequence']]['paused'])

    def test_weekend_and_triple_rollovers_are_not_skipped(self):
        account=self.run_account('boundary_hold'); finance=[r for r in account.state['ledger'] if r['kind']=='financing']
        self.assertTrue(any(r['multiplier']==0 for r in finance))
        self.assertTrue(any(r['multiplier']==3 for r in finance))
        self.assertEqual(account.state['held'],None)

    def test_financing_gap_pause_remains_latched_after_recovery(self):
        account=self.run_account('financing_pause'); state=account.state
        paused=[o for o in state['outcomes'] if o['paused']]
        self.assertTrue(paused)
        self.assertTrue(any(D(o['account']['equity_usd'])>D(o['day_start_equity'])*D('.99') for o in paused))
        self.assertTrue(any(r['kind']=='financing' and r['multiplier']==3 for r in state['ledger']))

    def test_one_held_slot_blocks_new_signal_even_on_exit_quote(self):
        account=self.run_account('held_signal_change'); state=account.state
        blocked=[o for o in state['outcomes'] if o['reason']=='held_position']
        self.assertTrue(blocked)
        self.assertEqual(sum(r['kind']=='entry_fill' for r in state['ledger']),1)
        for o in blocked:self.assertTrue(o['held_at_arrival'])
        self.assertEqual(sum(r['kind']=='release' for r in state['ledger']),1)

    def test_first_geometry_rejection_consumes_feature(self):
        account=self.run_account('invalid_geometry')
        self.assertEqual(account.state['outcomes'][0]['reason'],'price_geometry')
        self.assertEqual(account.state['outcomes'][1]['reason'],'session_consumed')
        self.assertFalse(any(r['kind']=='entry_fill' for r in account.state['ledger']))

    def test_bad_quality_does_not_consume_before_valid_quote(self):
        account=self.run_account('quote_guards')
        self.assertEqual([o['reason'] for o in account.state['outcomes'][:4]],['stale_quote','wide_quote','repeated_source','entry_filled'])

    def test_signal_publication_quote_is_not_an_entry(self):
        account=self.run_account('delayed_publication')
        self.assertEqual(account.state['outcomes'][0]['reason'],'before_feature')
        self.assertEqual(account.state['outcomes'][1]['reason'],'entry_filled')
        event=account._fixture['events'][1]
        self.assertGreater(event['source_msc'],event['feature']['available_msc'])

    def test_wide_quotes_can_exit_without_entry_spread_admission(self):
        account=self.run_account('wide_exit')
        self.assertEqual(account.state['ledger'][-2]['reason'],'stop')
        self.assertTrue(account.state['outcomes'][1]['execution_quote'])

    def test_cash_and_no_signal_have_zero_ledger_and_null_edge(self):
        for case,model in (('long_target','CASH'),('no_signal','EWPB_D124')):
            account=self.run_account(case,model=model)
            self.assertEqual(account.state['ledger'],[])
            self.assertEqual(account.report()['summary']['toy_net_usd'],'0')
            self.assertEqual(account.report()['market_assessment'],'unavailable_invented_unqualified')

    def test_maximum_lot_is_not_exceeded(self):
        account=self.run_account('max_lot')
        proposal=next(o['proposal'] for o in account.state['outcomes'] if o['proposal'])
        self.assertEqual(proposal['lots'],'1')

    def test_minimum_lot_abstains_without_rounding_up(self):
        account=self.run_account('minimum_lot')
        self.assertEqual(account.state['outcomes'][0]['reason'],'minimum_lot_risk')
        self.assertEqual(account.state['ledger'],[])

    def test_sizer_risk_margin_exact_minimum_boundaries(self):
        event={'bid':1.1,'ask':1.1001,'sequence':0,'source_msc':1000000000000,'feature':{'session_id':1}}
        signal={'side':1,'prospective_invalidation':'1.099','pattern_id':'0'*64}
        profile=engine.fills.risk.profiles()['base']
        with localcontext() as ctx:
            ctx.prec=50
            per_stop=(D('1.10012')-D('1.099')+D('.00002'))*100000+7
            equity=per_stop*D('.01')/D('.0025')
            margin=(D('1.10012')*100000/30+D('3.5'))*D('.01')
            for eq,free,reason in ((equity,margin,None),(equity-D('1e-20'),margin,'minimum_lot_risk'),(equity,margin-D('1e-20'),'minimum_lot_margin')):
                proposal,actual=engine.structural_size(signal,event,profile,eq,free,0,'test')
                self.assertEqual(actual,'entry_filled' if reason is None else reason)
                if proposal:self.assertEqual(proposal['lots'],'0.01')

    def test_sizer_daily_headroom_and_invalid_short_target(self):
        event={'bid':1.1,'ask':1.1001,'sequence':0,'source_msc':1000000000000,'feature':{'session_id':1}}
        profile=engine.fills.risk.profiles()['base']; signal={'side':1,'prospective_invalidation':'1.099','pattern_id':'0'*64}
        proposal,reason=engine.structural_size(signal,event,profile,D(10000),D(10000),D('9999'),'x')
        self.assertIsNone(proposal);self.assertEqual(reason,'daily_headroom')
        signal.update(side=-1,prospective_invalidation='3')
        self.assertEqual(engine.structural_size(signal,event,profile,D(10000),D(10000),0,'x')[1],'price_geometry')

    def test_nonpositive_slipped_exit_rejects_transactionally(self):
        account=self.account('nonpositive_exit'); account.step(account._fixture['events'][0]); before=account.state
        with self.assertRaisesRegex(ValueError,'nonpositive_exit_price'):account.step(account._fixture['events'][1])
        self.assertEqual(account.state,before)

    def test_paused_and_held_protection_never_resize_on_signal_change(self):
        account=self.account('held_signal_change'); original=None
        for event in account._fixture['events']:
            account.step(event)
            held=account.state['held']
            if held:
                current={k:held[k] for k in ('lots','entry','stop','target')}
                if original is None:original=current
                self.assertEqual(current,original)
        account.finish()

    def test_stale_endpoint_rejects_even_when_cash(self):
        account=self.account(model='CASH'); events=deepcopy(account._fixture['events'])
        events[-1]['receipt_msc']=events[-1]['source_msc']+2001
        account._fixture['events']=events
        for event in events:account.step(event)
        with self.assertRaisesRegex(ValueError,'missing_executable_endpoint'):account.finish()

    def test_actual_compiled_raw_quotes_and_latest_publications_match(self):
        p,m=self.compiled('long_target'); value=engine.daily._json(p.read_bytes())
        prefix=engine.daily._json((p.parent/'prefix-input.json').read_bytes())
        aggregate=engine.daily._json((p.parent/'aggregation.json').read_bytes())
        for event in value['events']:
            message=prefix['messages'][event['message_sequence']]
            for k in ('source_msc','receipt_msc','bid','ask'):self.assertEqual(event[k],message[k])
            available=[b for b in aggregate['final_state']['bars'] if b['available_msc']<=event['receipt_msc']]
            self.assertEqual(event['feature']['session_id'],available[-1]['session_id'])

    def test_fresh_later_partition_does_not_import_development_loss(self):
        first=self.run_account('long_gap'); later=self.account('long_gap',partition=1)
        self.assertLess(D(first.state['balance_usd']),10000)
        self.assertEqual(later.state['balance_usd'],'10000');self.assertIsNone(later.state['held'])
        later.run();audit_account(later._fixture,later.report())

    def test_future_prices_cannot_change_development_economic_prefix(self):
        value=fixture('boundary_hold'); changed=deepcopy(value)
        cutoff=value['partitions'][0]['end_msc']
        for message in changed['stream']['messages']:
            if message['kind']=='quote' and message['receipt_msc']>=cutoff:
                message['bid']+=.0003;message['ask']+=.0003
        engine.validate_fixture(changed)
        directory=Path(tempfile.mkdtemp(dir=self.root))
        engine.prepare_partition(changed,changed['partitions'][0],directory)
        first=self.account('boundary_hold');later=engine.Account(directory/'compiled-input.json',directory/'compiled-frozen.json')
        self.assertEqual(first._fixture['events'],later._fixture['events'])
        for i in range(5):
            first.step(first._fixture['events'][i]);later.step(later._fixture['events'][i])
            self.assertEqual(first.state,later.state)

    def test_old_signal_expires_when_a_new_completed_bar_publishes(self):
        value=fixture('boundary_hold');part=value['partitions'][0]
        first_day=part['start_msc']//engine.daily.DAY
        for message in value['stream']['messages']:
            if message['kind']=='quote' and message['source_msc']//engine.daily.DAY==first_day:
                midpoint=(D(message['bid'])+D(message['ask']))/2
                message['bid']=float(midpoint-D('.00015'));message['ask']=float(midpoint+D('.00015'))
        directory=Path(tempfile.mkdtemp(dir=self.root));engine.prepare_partition(value,part,directory)
        account=engine.Account(directory/'compiled-input.json',directory/'compiled-frozen.json');account.run()
        self.assertEqual([o['reason'] for o in account.state['outcomes'][:4]],['wide_quote']*4)
        self.assertEqual(account.state['outcomes'][4]['reason'],'inactive_signal')
        self.assertIsNone(account._fixture['events'][4]['feature']['signal'])
        self.assertEqual(account.state['ledger'],[])

    def test_prefix_restore_does_not_step_future_events(self):
        account=self.account();account.step(account._fixture['events'][0]);checkpoint=account.checkpoint()
        original=engine.Account._step
        def bounded(instance,event):
            self.assertLess(event['sequence'],1);return original(instance,event)
        with patch.object(engine.Account,'_step',bounded):
            restored=engine.Account.restore(*self.compiled(),checkpoint)
        self.assertEqual(restored.state,account.state)
        self.assertEqual(restored.run(),account.run())

    def test_every_quote_prefix_and_unfinished_boundary_restore(self):
        account=self.account('boundary_hold')
        for event in account._fixture['events']:
            restored=engine.Account.restore(*self.compiled('boundary_hold'),account.checkpoint())
            self.assertEqual(restored.state,account.state);account.step(event)
        restored=engine.Account.restore(*self.compiled('boundary_hold'),account.checkpoint())
        self.assertIsNotNone(restored.state['held']);self.assertEqual(restored.run(),account.run())

    def test_latest_duplicate_and_finished_run_are_idempotent(self):
        account=self.account();account.run();before=account.state
        self.assertFalse(account.step(account._fixture['events'][-1]));self.assertFalse(account.finish())
        self.assertEqual(account.run(),account.report());self.assertEqual(account.state,before)

    def test_altered_or_old_duplicate_rejects_without_changes(self):
        account=self.account();account.step(account._fixture['events'][0]);account.step(account._fixture['events'][1]);before=account.state
        with self.assertRaisesRegex(ValueError,'event_binding'):account.step(account._fixture['events'][0])
        bad=deepcopy(account._fixture['events'][1]);bad['bid']+=.00001
        with self.assertRaisesRegex(ValueError,'event_binding'):account.step(bad)
        self.assertEqual(account.state,before)

    def test_rehashed_cash_stop_reservation_and_consumption_forgeries_reject(self):
        account=self.account();account.step(account._fixture['events'][0])
        changes=(lambda s:s.update(balance_usd='999999'),lambda s:s['held'].update(stop='0.5'),
                 lambda s:s.update(reservation=None),lambda s:s.update(consumed_sessions=[]))
        for change in changes:
            checkpoint=account.checkpoint();change(checkpoint['payload']['state']);checkpoint['sha256']=engine.daily._digest(checkpoint['payload'])
            with self.assertRaisesRegex(ValueError,'elliott_checkpoint_reconstructed_state'):engine.Account.restore(*self.compiled(),checkpoint)

    def test_boolean_cursor_finished_and_cross_profile_reject(self):
        account=self.account();cp=account.checkpoint()
        cp['payload']['cursor']=False;cp['sha256']=engine.daily._digest(cp['payload'])
        with self.assertRaisesRegex(ValueError,'elliott_checkpoint_cursor'):engine.Account.restore(*self.compiled(),cp)
        cp=account.checkpoint();cp['payload']['finished']=0;cp['sha256']=engine.daily._digest(cp['payload'])
        with self.assertRaisesRegex(ValueError,'elliott_checkpoint_binding'):engine.Account.restore(*self.compiled(),cp)
        with self.assertRaisesRegex(ValueError,'elliott_checkpoint_binding'):engine.Account.restore(*self.compiled(),account.checkpoint(),'adverse')

    def test_synthetic_account_guard_rechecks_before_entry(self):
        for mode in (1,2,True):
            account=self.account();account._fixture['initial_account']['trade_mode']=mode
            with self.assertRaisesRegex(ValueError,'synthetic_demo_account_required'):account.step(account._fixture['events'][0])
            self.assertEqual(account.state['ledger'],[])

    def test_raw_market_positions_marks_real_and_contest_reject(self):
        for mode in (1,2,True):
            value=fixture();value['stream']['initial_account']['trade_mode']=mode
            with self.assertRaisesRegex(ValueError,'synthetic_demo_account_required'):engine.validate_fixture(value)
        for key in ('positions','signals','bars','market_data_qualified'):
            value=fixture();value[key]=True
            with self.assertRaisesRegex(ValueError,'elliott_execution_fields'):engine.validate_fixture(value)

    def test_unavailable_history_and_endpoints_publish_no_returns(self):
        for case in ('missing_history','missing_endpoint','stale_endpoint','nonpositive_exit'):
            value=fixture(case);directory=Path(tempfile.mkdtemp(dir=self.root));p=directory/'input.json';m=directory/'frozen.json'
            engine.daily.write_new(p,value);engine.freeze_fixture(p,m)
            report=engine.evaluate_fixture(p,m,directory/'run')
            self.assertTrue(any(r['status']=='unavailable' for r in report['partitions']))
            for row in report['partitions']:
                if row['status']=='unavailable':
                    self.assertIsNone(row['returns']);self.assertEqual(row['results'],[])
                    self.assertFalse((directory/'run'/row['partition']['name']/'account-reports.json').exists())

    def test_cli_and_root_collision_preserve_all_output_bytes(self):
        directory=Path(tempfile.mkdtemp(dir=self.root));p=directory/'input.json';m=directory/'frozen.json'
        engine.daily.write_new(p,fixture('no_signal'));engine.freeze_fixture(p,m)
        cmd=[sys.executable,str(engine.daily.ROOT/'scripts/elliott-execution-125.py'),'evaluate',str(p),str(m),str(directory/'run')]
        result=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        before={q.relative_to(directory).as_posix():hashlib.sha256(q.read_bytes()).hexdigest() for q in directory.rglob('*') if q.is_file()}
        repeated=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(repeated.returncode,1)
        self.assertEqual(json.loads(repeated.stdout)['reason'],'artifact_exists')
        self.assertEqual(before,{q.relative_to(directory).as_posix():hashlib.sha256(q.read_bytes()).hexdigest() for q in directory.rglob('*') if q.is_file()})


if __name__=='__main__':unittest.main()

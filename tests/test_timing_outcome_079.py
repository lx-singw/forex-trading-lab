"""Injected early-outcome audits only; no SDK or Windows calls."""
import copy
import hashlib
import json
import unittest

from forex_demo_lab.native_timing_078 import authorization078
from forex_demo_lab.sharing_adapter_076 import encoded076
from forex_demo_lab.sharing_probe_062 import ProbeRejected
from forex_demo_lab.timing_outcome_079 import audit_preflight079, INVENTORY


def fixture079():
    expected = authorization078(*[str(i)*64 for i in range(1,8)])
    raw = encoded076(expected)
    ah = hashlib.sha256(raw).hexdigest()
    sh, lh = 'a'*64, 'b'*64
    started = dict(version='native_timing_invocation_079_v1',
        invocation_consumed=True, maximum_invocations=1,
        started_utc='2026-10-08T16:03:07.5116612Z',
        authorization_sha256=ah, entry_sha256=expected['entry_sha256'],
        launcher_sha256=lh, orders_available=False)
    outcome = dict(version='native_timing_invocation_outcome_079_v1',
        invocation_consumed=True, native_entry_invocations=1, exit_code=1,
        elapsed_ms=1979, ended_utc='2026-10-08T16:03:09.7539867Z',
        output_characters=42, output_category='preflight_rejected',
        native_summary=None, started_record_sha256=sh, orders_available=False)
    return dict(auth_raw=raw, expected_auth=expected, auth_sha=ah,
        started=started, outcome=outcome, started_sha=sh, launcher_sha=lh,
        inventory=dict.fromkeys(INVENTORY,False))


class Outcome079Tests(unittest.TestCase):
    def reject(self, fixture):
        with self.assertRaisesRegex(ProbeRejected,'^timing_outcome_audit_rejected$'):
            audit_preflight079(**fixture)

    def start_change(self, **change):
        f=fixture079();f['started'].update(change);self.reject(f)

    def end_change(self, **change):
        f=fixture079();f['outcome'].update(change);self.reject(f)

    def test_accepts_exact_observed_early_branch(self):
        r=audit_preflight079(**fixture079());self.assertTrue(r['audit_passed'])
        self.assertEqual(r['samples_completed'],0);self.assertEqual(r['sdk_connections'],0)
        self.assertFalse(r['account_type_verified_this_attempt'])

    def test_no_resources_is_not_a_cleanup_proof(self):
        r=audit_preflight079(**fixture079())
        self.assertFalse(r['owned_cleanup_applicable'])
        self.assertIsNone(r['owned_cleanup_confirmed'])

    def test_process_duration_is_not_native_guard_latency_or_root_cause(self):
        r=audit_preflight079(**fixture079());self.assertEqual(r['invocation_elapsed_ms'],1979)
        for n in ('exact_failure_cause_known','elapsed_is_guard_latency',
                  'native_timing_verified','timing_bounds_comparison_possible','old070_cause_proven'):
            self.assertFalse(r[n])

    def test_each_dispatch_component_runtime_or_sidecar_presence_rejects(self):
        for name in INVENTORY:
            with self.subTest(name=name):
                f=fixture079();f['inventory'][name]=True;self.reject(f)

    def test_missing_or_extra_inventory_keys_reject(self):
        for mode in ('missing','extra'):
            f=fixture079()
            if mode=='missing':f['inventory'].pop('dispatch')
            else:f['inventory']['other']=False
            self.reject(f)

    def test_integer_false_is_not_boolean_absence(self):
        f=fixture079();f['inventory']['dispatch']=0;self.reject(f)

    def test_changed_authorization_bytes_reject(self):
        f=fixture079();f['auth_raw']+=b' ';self.reject(f)

    def test_noncanonical_authorization_even_with_matching_digest_rejects(self):
        f=fixture079();f['auth_raw']=json.dumps(f['expected_auth'],indent=2).encode('ascii')
        f['auth_sha']=hashlib.sha256(f['auth_raw']).hexdigest();self.reject(f)

    def test_duplicate_authorization_keys_reject(self):
        f=fixture079();f['auth_raw']=b'{"phase":1,"phase":2}\n'
        f['auth_sha']=hashlib.sha256(f['auth_raw']).hexdigest();self.reject(f)

    def test_authorization_must_match_independent_trusted_expectations(self):
        f=fixture079();f['expected_auth']=copy.deepcopy(f['expected_auth'])
        f['expected_auth']['policy_sha256']='0'*64;self.reject(f)

    def test_changed_entry_launcher_or_authorization_hash_rejects(self):
        for key in ('entry_sha256','launcher_sha256','authorization_sha256'):
            self.start_change(**{key:'0'*64})

    def test_changed_started_record_digest_rejects(self):
        self.end_change(started_record_sha256='0'*64)

    def test_unspent_start_or_outcome_rejects(self):
        self.start_change(invocation_consumed=False)
        self.end_change(invocation_consumed=False)

    def test_second_invocation_or_boolean_count_rejects(self):
        for n in (2,True,1.0):self.end_change(native_entry_invocations=n)
        self.start_change(maximum_invocations=2)

    def test_success_exit_or_boolean_exit_rejects(self):
        for n in (0,True,1.0):self.end_change(exit_code=n)

    def test_any_runtime_summary_rejects(self):
        self.end_change(native_summary={'entry_completed':True})
        self.end_change(native_summary={})

    def test_unknown_output_or_wrong_length_rejects(self):
        self.end_change(output_category='unexpected_output_redacted')
        for n in (0,43,42.0):self.end_change(output_characters=n)

    def test_account_identifiers_and_extra_fields_reject_with_redacted_error(self):
        self.start_change(account_login='sensitive')
        self.end_change(raw_exception='sensitive')

    def test_orders_enabled_or_integer_false_reject(self):
        for value in (True,0):
            self.start_change(orders_available=value);self.end_change(orders_available=value)

    def test_date_mismatch_rejects(self):
        self.start_change(started_utc='2026-10-09T16:03:07.5116612Z')
        self.end_change(ended_utc='2026-10-09T16:03:09.7539867Z')

    def test_non_utc_malformed_date_and_missing_time_reject(self):
        for value in ('2026-10-08T16:03:07+02:00','2026-10-08Z',None,
                      '2026-10-08T25:03:07.5116612Z','2026-10-08 16:03:07.5116612Z'):
            self.start_change(started_utc=value)

    def test_backward_time_or_impossible_process_duration_rejects(self):
        self.end_change(ended_utc='2026-10-08T16:03:06.7539867Z')
        for n in (3000,-1,True,1979.0,2**63):self.end_change(elapsed_ms=n)

    def test_bad_versions_digests_and_non_dicts_reject(self):
        self.start_change(version='other');self.end_change(version='other')
        for key in ('started_sha','launcher_sha'):
            f=fixture079();f[key]=False;self.reject(f)
        for key in ('started','outcome','inventory'):
            f=fixture079();f[key]=[];self.reject(f)

    def test_result_does_not_export_inputs_or_grant_retries_launches_or_orders(self):
        r=audit_preflight079(**fixture079());text=json.dumps(r)
        for secret in ('started_utc','launcher_sha256','entry_sha256','account_login','raw_exception'):
            self.assertNotIn(secret,text)
        for n in ('retry_authorized','native_launch_ready','latency_guaranteed',
                  'annual_eligible','fresh_performance_eligible','orders_available'):
            self.assertFalse(r[n])
        self.assertEqual((r['script_launches'],r['market_reads'],r['orders']), (0,0,0))


if __name__=='__main__':unittest.main()

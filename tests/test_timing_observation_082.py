from copy import deepcopy
import hashlib
import unittest

from forex_demo_lab.native_timing_081 import authorization081, dispatch_value081
from forex_demo_lab.public_trace_081 import invocation_bytes081
from forex_demo_lab.sharing_adapter_076 import encoded076
from forex_demo_lab.sharing_probe_062 import ProbeRejected
from forex_demo_lab.timing_observation_082 import (
    audit_observation082, timing_scenarios082, LIMITS077, CLEANUP, STAGES,
    ROOT_FALSE, ROOT_ZERO, AUTH_PINS, PHASE, DATE)


def fixture082():
    """Independent synthetic transcript: no files, SDK or native dependencies."""
    component = b'{"proposal":"injected-only"}\n'
    component_sha = hashlib.sha256(component).hexdigest()
    auth = authorization081('a'*64, 'b'*64, 'c'*64, 'd'*64, 'e'*64,
                            'f'*64, component_sha)
    raw = encoded076(auth); ash = hashlib.sha256(raw).hexdigest()
    started = dict(version='native_timing_invocation_082_v1', invocation_consumed=True,
        maximum_invocations=1, started_utc='2026-10-08T17:00:00.0000000Z',
        authorization_sha256=ash, entry_sha256='e'*64, launcher_sha256='1'*64,
        orders_available=False)
    outcome = dict(version='native_timing_invocation_outcome_082_v1',
        invocation_consumed=True, native_entry_invocations=1, exit_code=0,
        elapsed_ms=20000, ended_utc='2026-10-08T17:00:21.0000000Z',
        output_characters=146, output_category='fixed_native_summary',
        native_summary=dict(public_completed=True, stop_reason=None,
                            orders_available=False, entry_completed=True),
        started_record_sha256='2'*64, orders_available=False)
    metrics = dict(public_record_reads=12, public_record_bytes=10000,
        public_record_stats=120, public_source_reads=32, public_source_bytes=12000,
        public_source_stats=350, steps=94)
    public = dict(version='native_timing_public_081_v1', date=DATE, phase=PHASE,
        account_type_verified=False, authority_validated=True, completed=True,
        dispatch_reserved=True, invocation_consumed=True, latency_guaranteed=False,
        native_launch_ready=False, orders_available=False, owned_cleanup_applicable=False,
        owned_native_backend_created=False, sdk_connections=0, sdk_queries=0,
        source_index=None, source_pins_verified=True, stop_reason=None,
        stopped_operation=None, stopped_stage=None, **metrics)
    counts = dict.fromkeys(LIMITS077, 0)
    counts.update(guards=8, profile_samples=4, hash_reads=126, hash_bytes=46,
        sdk_queries=89, sdk_connections=1, sdk_shutdowns=1, reservation_writes=1,
        trust_queries=1, clock_samples=100, process_opens=38, identity_tokens=38,
        local_frees=38, token_queries=114, process_snapshots=19, process_entries=100,
        closes=95, native_calls=100, hash_path_stats=100, startup_path_stats=8)
    samples = [dict(composite_sample_ms=c, core_guard_ms=g,
                   hash_reads=25, hash_bytes=10, sdk_queries=22)
        for c, g in ((2521,[1138,1156]),(2689,[1264,1217]),
                     (2885,[1220,1444]),(3174,[1611,1279]))]
    observation = dict(version='timing_profile_observation_077_v1',
        phase='77000000000000000000000000000001', date=DATE,
        build_record_sha256='f'*64, cleanup=deepcopy(CLEANUP), completed=True,
        counts=deepcopy(counts), latency_guaranteed=False, native_launch_ready=False,
        native_timing_verified=False, observations_only=True,
        observed_composite_max_ms=3174, observed_core_guard_max_ms=1611,
        orders_available=False, preparation_contract_sha256=component_sha,
        runtime_authorized=False, samples=samples, samples_completed=4, stop_reason=None)
    runtime = dict(version='native_timing_entry_081_v1', date=DATE, phase=PHASE,
        authorization_sha256=ash, counts=counts, cleanup=deepcopy(CLEANUP),
        entry_completed=True, native_entry_invoked=True, observation=observation,
        observations_only=True, public_outcome_sha256='5'*64, checks_sha256='3'*64,
        completion_review_sha256='4'*64, reservation_sha256=component_sha,
        signature_checks_passed=True, stage_trace=[dict(stage=n,started=True,completed=True)
            for n in STAGES], stop_reason=None, stopped_stage=None,
        **{k:auth[k] for k in AUTH_PINS}, **dict.fromkeys(ROOT_FALSE,False),
        **dict.fromkeys(ROOT_ZERO,0))
    return dict(auth_raw=raw, expected_auth=auth, auth_sha=ash,
        component_expected_raw=component, markers=dict(invocation=invocation_bytes081(),
            dispatch=encoded076(dispatch_value081(auth,ash)), component=component),
        sidecars_present=dict(invocation=False,dispatch=False,component=False),
        started=started,outcome=outcome,started_sha='2'*64,launcher_sha='1'*64,
        public=public,runtime=runtime,checks_sha='3'*64,review_sha='4'*64,
        public_sha='5'*64,expected_public_metrics=metrics,
        sample_hash_bytes=10,bootstrap_hash_bytes=6)


class Observation082Tests(unittest.TestCase):
    def setUp(self): self.f=fixture082()
    def reject(self):
        with self.assertRaisesRegex(ProbeRejected,'^timing_observation_audit_rejected$'):
            audit_observation082(**self.f)
    def test_completed_metadata_evidence_and_no_execution_authority(self):
        r=audit_observation082(**self.f)
        self.assertTrue(r['audit_passed']);self.assertTrue(r['owned_cleanup_confirmed'])
        self.assertEqual((r['samples_completed'],r['guards'],r['sdk_queries']),(4,8,89))
        self.assertEqual((r['observed_core_guard_min_ms'],r['observed_core_guard_max_ms']),(1138,1611))
        self.assertTrue(r['capture_sample_count_omitted']);self.assertFalse(r['retry_authorized'])
        for k in ROOT_FALSE:self.assertFalse(r[k])
    def test_invocation_bytes_changed(self):
        self.f['markers']['invocation']+=b' ';self.reject()
    def test_dispatch_bytes_changed(self):
        self.f['markers']['dispatch']=self.f['markers']['dispatch'].replace(b'081',b'078');self.reject()
    def test_component_bytes_changed(self):
        self.f['markers']['component']+=b' ';self.reject()
    def test_raw_sidecar_fabrication_rejected(self):
        for k in self.f['sidecars_present']:
            with self.subTest(k=k):
                self.f=fixture082();self.f['sidecars_present'][k]=True;self.reject()
    def test_authorization_changed_even_with_matching_new_digest(self):
        v=deepcopy(self.f['expected_auth']);v['maximum_orders']=1
        self.f['auth_raw']=encoded076(v)
        self.f['auth_sha']=hashlib.sha256(self.f['auth_raw']).hexdigest();self.reject()
    def test_started_pins_changed(self):
        self.f['started']['entry_sha256']='0'*64;self.reject()
    def test_repeated_invocation_rejected(self):
        self.f['outcome']['native_entry_invocations']=2;self.reject()
    def test_nonzero_exit_rejected(self):
        self.f['outcome']['exit_code']=1;self.reject()
    def test_clock_reversal_date_and_malformed_stamp_rejected(self):
        for stamp in ('2026-10-08T16:00:00.0000000Z','2026-10-09T17:00:21.0000000Z','private'):
            with self.subTest(stamp=stamp):
                self.f=fixture082();self.f['outcome']['ended_utc']=stamp;self.reject()
    def test_elapsed_outside_capture_and_less_than_samples_rejected(self):
        for value in (22000,True,-1,1):
            with self.subTest(value=value):
                self.f=fixture082();self.f['outcome']['elapsed_ms']=value;self.reject()
    def test_capture_extra_identifier_rejected(self):
        self.f['outcome']['native_summary']['account_identifier']='private';self.reject()
    def test_public_metric_arithmetic_rejected(self):
        self.f['public']['public_record_bytes']+=1;self.reject()
    def test_public_authority_source_and_pre_native_flags_rejected(self):
        for k in ('authority_validated','source_pins_verified','account_type_verified'):
            with self.subTest(k=k):
                self.f=fixture082();self.f['public'][k]=not self.f['public'][k];self.reject()
    def test_public_extra_private_path_rejected(self):
        self.f['public']['runtime_path']='private';self.reject()
    def test_all_runtime_bindings_rejected_on_change(self):
        for k in (*AUTH_PINS,'checks_sha256','completion_review_sha256','public_outcome_sha256'):
            with self.subTest(k=k):
                self.f=fixture082();self.f['runtime'][k]='0'*64;self.reject()
    def test_runtime_extra_identifier_and_launch_claim_rejected(self):
        for k,v in (('account_identifier','private'),('native_launch_ready',True),('orders',1)):
            with self.subTest(k=k):
                self.f=fixture082();self.f['runtime'][k]=v;self.reject()
    def test_bool_counter_rejected(self):
        self.f['runtime']['counts']['sdk_connections']=True;self.reject()
    def test_counter_cap_and_denied_bucket_rejected(self):
        for k,v in (('native_calls',25001),('commands',1),('hash_bytes',17179869185)):
            with self.subTest(k=k):
                self.f=fixture082();self.f['runtime']['counts'][k]=v;self.reject()
    def test_sdk_query_and_connection_shutdown_counts_rejected(self):
        for k in ('sdk_queries','sdk_connections','sdk_shutdowns','guards','hash_reads'):
            with self.subTest(k=k):
                self.f=fixture082();self.f['runtime']['counts'][k]-=1;self.reject()
    def test_handle_token_release_arithmetic_rejected(self):
        self.f['runtime']['counts']['closes']-=1;self.reject()
    def test_stage_reordering_rejected(self):
        t=self.f['runtime']['stage_trace'];t[0],t[1]=t[1],t[0];self.reject()
    def test_stage_incomplete_rejected(self):
        self.f['runtime']['stage_trace'][-1]['completed']=False;self.reject()
    def test_cleanup_error_unconfirmed_handle_and_shutdown_rejected(self):
        for k,v in (('errors',['private']),('sdk_shutdown_called',False)):
            with self.subTest(k=k):
                self.f=fixture082();self.f['runtime']['cleanup'][k]=v;self.reject()
        self.f=fixture082();self.f['runtime']['cleanup']['bootstrap_cleanup']['unconfirmed_handles']=1;self.reject()
    def test_partial_samples_rejected(self):
        self.f['runtime']['observation']['samples'].pop();self.reject()
    def test_duration_negative_boolean_and_composite_below_guard_sum_rejected(self):
        for k,v in (('core_guard_ms',[-1,1]),('core_guard_ms',[True,1]),('composite_sample_ms',1)):
            with self.subTest(k=k,v=v):
                self.f=fixture082();self.f['runtime']['observation']['samples'][0][k]=v;self.reject()
    def test_sample_bytes_and_queries_rejected(self):
        for k in ('hash_bytes','sdk_queries','hash_reads'):
            with self.subTest(k=k):
                self.f=fixture082();self.f['runtime']['observation']['samples'][0][k]+=1;self.reject()
    def test_inconsistent_maximum_rejected(self):
        self.f['runtime']['observation']['observed_core_guard_max_ms']=1610;self.reject()
    def test_observation_count_disagreement_rejected(self):
        self.f['runtime']['observation']['counts']['sdk_queries']=88;self.reject()
    def test_independent_timing_formula_and_non_bound_flags(self):
        r=timing_scenarios082(1611)
        self.assertEqual([v['completion_ms'] for v in r['scenarios']],[30776,45776,47382])
        self.assertTrue(all(not v['end_margin_fits'] for v in r['scenarios']))
        self.assertFalse(r['measured_critical_path']);self.assertFalse(r['worst_case_bound_established'])
    def test_strict_start_margin_boundary_and_guard_type(self):
        r=timing_scenarios082(4750)['scenarios'][0]
        self.assertEqual(r['latest_start_ms']+250,5000);self.assertFalse(r['start_margin_fits'])
        for g in (True,-1,600001):
            with self.assertRaises(ValueError):timing_scenarios082(g)
    def test_rejection_redacts_private_exception_contents(self):
        self.f['runtime']['observation']={'private-runtime-path':'secret'}
        try:audit_observation082(**self.f)
        except ProbeRejected as e:
            self.assertEqual(str(e),'timing_observation_audit_rejected');self.assertIsNone(e.__cause__)
        else:self.fail('malformed report accepted')

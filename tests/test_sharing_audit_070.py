import copy
import hashlib
import json
import unittest
from forex_demo_lab.sharing_audit_070 import *
from test_mql_sharing_064 import record


class SharingAudit070Tests(unittest.TestCase):
    def setUp(self):
        self.b=dict.fromkeys(('source','ex5','terminal','editor','preparation','policy','helper_profile'),'a'*64)
        self.value=dict(version='sharing_reservation_069_v1',phase=PHASE,mql_phase=MQL_PHASE,date=DATE,
            bindings=self.b,maximum_launches=2,maximum_sdk_connections=1,maximum_log_reads=1,
            maximum_log_bytes=65536,maximum_receipt_permissions=0,orders_available=False)
        self.raw=json.dumps(self.value,sort_keys=True).encode('ascii');self.hash=hashlib.sha256(self.raw).hexdigest()
        self.r=dict(completed=False,stop_reason='native_runtime_failed_details_redacted',stopped_stage='preflight',
            stage_trace=[dict(stage='preflight',started=True,completed=False)],phase=PHASE,date=DATE,
            preparation_sha256='a'*64,policy_sha256='a'*64,helper_profile_sha256='a'*64,reservation_sha256=None,
            counts=None,sdk_shutdown_called=False,native_signature_checks_passed=False,native_private_bootstrap_passed=False,
            native_sharing_observed=False,native_mql_verified=False,native_publication_verified=False,
            orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
            quote_reads=0,history_reads=0,orders=0,receipt_permissions=0,script_arms=[],records=[],probes=[],
            cleanup=None,bootstrap_cleanup=None,cleanup_errors=[],deployment_completed=False,
            compiled_source_sha256=None,compiled_artifact_sha256=None,elapsed_us=None)
    def native_failed(self):
        self.r.update(counts=dict.fromkeys(LIMITS069,0),elapsed_us=1,reservation_sha256=self.hash,
            stopped_stage='terminal_image',compiled_source_sha256='a'*64,compiled_artifact_sha256='a'*64,
            bootstrap_cleanup=dict(all_handles_closed=True,allocations_released=True,unconfirmed_handles=0))
        self.r['counts']['reservation_writes']=1
    def rejects(self,raw=None):
        with self.assertRaisesRegex(ProbeRejected,'^native_outcome_audit_rejected$'):audit(self.r,self.b,raw)
    def test_early_outcome_needs_no_reservation_or_sdk_cleanup(self):
        out=audit(self.r,self.b);self.assertTrue(out['audit_passed']);self.assertFalse(out['reservation_present'])
    def test_native_failure_raw_reservation_audits_without_sidecar(self):
        self.native_failed();out=audit(self.r,self.b,self.raw);self.assertTrue(out['audit_passed']);self.assertFalse(out['runtime_completed'])
        self.r['records']=[record(),record(True),record(True)];self.r['counts']['log_reads']=1
        self.assertTrue(audit(self.r,self.b,self.raw)['audit_passed'])
    def test_exact_raw_hash_change_rejected(self):
        with self.assertRaises(ProbeRejected):reservation(self.raw+b' ',self.hash,self.b)
    def test_raw_duplicate_keys_rejected_even_with_matching_hash(self):
        raw=self.raw[:-1]+b',"orders_available":false}'
        with self.assertRaises(ProbeRejected):reservation(raw,hashlib.sha256(raw).hexdigest(),self.b)
    def test_raw_extra_field_rejected(self):
        raw=json.dumps({**self.value,'extra':0}).encode('ascii')
        with self.assertRaises(ProbeRejected):reservation(raw,hashlib.sha256(raw).hexdigest(),self.b)
    def test_raw_boolean_numeric_budget_rejected(self):
        raw=json.dumps({**self.value,'maximum_receipt_permissions':False}).encode('ascii')
        with self.assertRaises(ProbeRejected):reservation(raw,hashlib.sha256(raw).hexdigest(),self.b)
    def test_raw_old_phase_or_binding_rejected(self):
        for change in ({'phase':'6'*32},{'bindings':{**self.b,'helper_profile':'b'*64}}):
            raw=json.dumps({**self.value,**change}).encode('ascii')
            with self.assertRaises(ProbeRejected):reservation(raw,hashlib.sha256(raw).hexdigest(),self.b)
    def test_boolean_market_zero_and_false_eligibility_enforced(self):
        for key,value in (('quote_reads',False),('orders_available',True),('annual_eligible',True)):
            r=copy.deepcopy(self.r);r[key]=value
            with self.assertRaises(ProbeRejected):audit(r,self.b)
    def test_private_unknown_stage_and_reason_rejected(self):
        for key,value in (('stopped_stage','private SID'),('stop_reason','private account')):
            r=copy.deepcopy(self.r);r[key]=value
            with self.assertRaises(ProbeRejected):audit(r,self.b)
    def test_unknown_or_boolean_counter_rejected(self):
        self.native_failed();self.r['counts']['hash_reads']=True;self.rejects(self.raw)
        self.r['counts']['hash_reads']=0;self.r['counts']['unknown']=1;self.rejects(self.raw)
    def test_no_reservation_cannot_hide_sdk_attempt(self):
        self.native_failed();self.r['reservation_sha256']=None;self.r['counts']['sdk_connections']=1;self.rejects()
    def test_failed_shutdown_is_preserved_as_failure(self):
        self.native_failed();self.r['counts'].update(sdk_connections=1,sdk_shutdowns=1)
        self.r['cleanup_errors']=['sdk_cleanup_unconfirmed']
        self.assertTrue(audit(self.r,self.b,self.raw)['audit_passed'])
    def test_cleanup_overrun_cannot_be_mislabeled_success(self):
        self.native_failed();self.r['counts']['closes']=LIMITS069['closes']+1
        self.assertFalse(audit(self.r,self.b,self.raw)['counts_within_declared_caps'])
        self.r.update(completed=True,native_sharing_observed=True,stop_reason=None,stopped_stage=None)
        self.rejects(self.raw)
    def test_failed_trace_must_be_finite_fixed_typed(self):
        self.r['stage_trace']*=33;self.rejects()
        self.r['stage_trace']=[dict(stage='preflight',started=True,completed=1)];self.rejects()
    def test_missing_outcome_fields_or_extra_private_fields_rejected(self):
        r=copy.deepcopy(self.r);del r['cleanup']
        with self.assertRaises(ProbeRejected):audit(r,self.b)
        self.r['private_account']='secret';self.rejects()
    def test_claimed_success_without_native_window_evidence_rejected(self):
        self.native_failed();self.r.update(completed=True,native_sharing_observed=True,stop_reason=None,stopped_stage=None,
            sdk_shutdown_called=True,native_signature_checks_passed=True,native_private_bootstrap_passed=True,
            deployment_completed=True,script_arms=['disabled','enabled'],records=[record(),record(True)],
            cleanup=dict(all_handles_closed=True,allocations_released=True,unconfirmed_handles=0),
            stage_trace=[dict(stage='final_audit',started=True,completed=True)])
        self.r['counts'].update(sdk_connections=1,sdk_shutdowns=1,script_arms=2,log_reads=1)
        self.rejects(self.raw)
    def test_complete_injected_window_and_cleanup_evidence_accepted(self):
        import test_sharing_runtime_069 as fixture
        case=fixture.Runtime069Tests();case.setUp()
        try:
            case.boot();runner,files,log=case.runtime();out=case.finish_success(runner,log);closed=case.owner.close()
            self.r.update(completed=True,native_sharing_observed=True,stop_reason=None,stopped_stage=None,
                counts=dict(case.m.counts),reservation_sha256=self.hash,elapsed_us=case.m.elapsed_us,
                sdk_shutdown_called=True,native_signature_checks_passed=True,native_private_bootstrap_passed=True,
                deployment_completed=True,script_arms=['disabled','enabled'],records=runner.rows,
                probes=[vars(p) for p in runner.c.probes],cleanup=closed['file_cleanup'],bootstrap_cleanup=copy.deepcopy(closed['file_cleanup']),
                compiled_source_sha256='a'*64,compiled_artifact_sha256='a'*64,
                stage_trace=[dict(stage=s,started=True,completed=True) for s in STAGES])
            for key in ('deployment_directories','deployment_writes','trust_queries','native_calls',
                        'process_opens','identity_tokens','hash_reads','hash_bytes','sdk_queries'):self.r['counts'][key]=1
            self.assertTrue(audit(self.r,self.b,self.raw)['runtime_completed'])
            self.r['cleanup']['unconfirmed_handles']=1;self.rejects(self.raw)
        finally:case.doCleanups()

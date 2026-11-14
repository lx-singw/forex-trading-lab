from copy import deepcopy
import json
from pathlib import Path
import unittest
from forex_demo_lab.synchronization_audit_084_r3 import audit084_r3,validate_row084_r3

ROOT=Path(__file__).resolve().parents[1]
class Sync084R3AuditTests(unittest.TestCase):
    def setUp(self):self.e=json.loads((ROOT/'reports/synchronization-084-r2-evidence.json').read_text())
    def bad(self,name,mutate):
        row=deepcopy(self.e['cases'][name]);mutate(row)
        with self.assertRaises(ValueError):validate_row084_r3(name,row)
    def test_all_retained_cases_and_missing_final_span_explained(self):
        rows=audit084_r3(self.e);self.assertEqual(len(rows),14)
        self.assertEqual(rows['observed_guard']['started_guards'],75)
        self.assertEqual(rows['observed_guard']['valid_guard_spans'],74)
        self.assertFalse(rows['observed_guard']['missing_span_invented'])
    def test_ordinary_missing_or_additional_guard_rejected(self):
        self.bad('normal',lambda r:r.update(full_guards=r['full_guards']+1))
    def test_slow_case_cannot_claim_valid_cleanup_release_or_short_elapsed(self):
        for mutate in (lambda r:r.update(elapsed_ms=120000),lambda r:r['summary'].update(cleanup_confirmed=True),
            lambda r:r.update(model_release_calls=1),lambda r:r.update(full_guards=74)):
            self.bad('observed_guard',mutate)
    def test_native_counts_and_bool_integer_substitution_reject(self):
        self.bad('normal',lambda r:r.update(orders=1))
        self.bad('normal',lambda r:r.update(orders=False))
        self.bad('normal',lambda r:r['summary']['counts'].update(opens=True))
    def test_reversed_or_outside_completed_guard_span_rejected(self):
        self.bad('normal',lambda r:r['guard_spans'][0].update(start=1,end=0))
        self.bad('normal',lambda r:r['guard_spans'][-1].update(end=120000))
    def test_success_requires_fresh_original_frames_and_error32(self):
        self.bad('normal',lambda r:r['frames'][0].update(validated_offset_ms=99999))
        self.bad('normal',lambda r:r['probes'][2].update(error=5))
    def test_default_off_and_case_registry_exact(self):
        self.bad('default_off',lambda r:r.update(factories=1))
        self.e['cases'].pop('stale')
        with self.assertRaises(ValueError):audit084_r3(self.e)
    def test_uncertain_close_and_remaining_handles_rejected(self):
        self.bad('normal',lambda r:r['summary'].update(unconfirmed_handles=1))
        self.bad('normal',lambda r:r.update(backend_model_handles_remaining=1))

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import test_sharing_build_074 as legacy
from forex_demo_lab.sharing_build_075 import *

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('build_entry075',ROOT/'scripts/runtime-sharing-build-075.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)


class CompilerShell075Tests(legacy.CorrectedEntry074Tests):
    def setUp(self):
        super().setUp()
        self.ledger['execution_policy']='Restricted'
        self.child_policy=self.final_policy='Restricted'

    def metadata(self,shell,budget,policy,cleanup=False):
        value=super().metadata(shell,budget,policy,cleanup)
        value['policy']=self.final_policy if cleanup else self.child_policy
        return metadata073(value,policy)

    def run_entry(self):
        with patch.object(entry,'ROOT',self.root),patch.object(entry,'os',NS(name='nt')),patch.object(entry,'sys',NS(executable=self.ledger['python_path'])),\
             patch.object(entry.runpy,'run_path',return_value=self.api),patch.object(entry,'Budget073',lambda clock:Budget073(lambda:self.clock()[:2])),\
             patch.object(entry,'datetime',NS(now=lambda tz:datetime.fromtimestamp(self.clock.utc//1000,timezone.utc))),\
             patch.object(entry,'metadata',self.metadata),patch.object(entry,'compile_once073',self.compile):
            entry.run()
        return self.outputs[-1]

    def test_corrected_schema_phase_and_actual_exit_retained(self):
        r=self.run_entry();self.assertTrue(r['compiled'])
        self.assertEqual(r['build_record']['version'],'sharing_build_075_v1')
        self.assertEqual(r['build_record']['build_phase'],BUILD_PHASE)
        self.assertEqual(r['compiler_exit_code'],1)
        self.assertEqual(r['metadata_before']['policy'],'Restricted')
        self.assertEqual(r['metadata_after']['policy'],'Restricted')
        self.assertTrue(all(p.name.startswith('compiler075-') for p in self.build_root.iterdir()))

    def test_workspace_policy_cannot_substitute_for_child_policy(self):
        self.ledger['execution_policy']='RemoteSigned'
        r=self.run_entry()
        self.assertEqual((r['stop_reason'],r['stopped_stage']),('metadata_rejected','metadata_before'))
        self.assertEqual(r['counts']['compiler_invocations'],0)
        self.assertEqual(r['counts']['copies'],0)
        self.assertFalse(list(self.build_root.iterdir()))

    def test_changed_child_policy_after_compile_rejects_success(self):
        self.final_policy='RemoteSigned'
        r=self.run_entry()
        self.assertEqual(r['counts']['compiler_invocations'],1)
        self.assertFalse(r['completed'])
        self.assertEqual((r['stop_reason'],r['stopped_stage']),('metadata_rejected','metadata_after'))
        self.assertFalse(r['owned_compiler_absent_after'])

    def test_metadata_helper_reads_child_response_without_override(self):
        value=dict(policy='Restricted',editor_processes=0,terminal_build=6244,editor_build=6244,valid_signatures=True)
        result=NS(returncode=0,stdout=json.dumps(value),stderr='')
        shell=Path(self.ledger['shell_path']);budget=Budget073(lambda:self.clock()[:2])
        with patch.object(entry.subprocess,'run',return_value=result) as process:
            self.assertEqual(entry.metadata(shell,budget,'Restricted'),value)
        args,kwargs=process.call_args
        self.assertEqual(args[0][:4],[str(shell),'-NoProfile','-NonInteractive','-Command'])
        self.assertNotIn('-ExecutionPolicy',args[0])
        self.assertNotIn('Set-ExecutionPolicy',args[0][-1])
        self.assertEqual(kwargs['env']['PSModulePath'],str(shell.parent/'Modules'))
        self.assertEqual(kwargs['timeout'],15)
        self.assertEqual(budget.counts['metadata_calls'],1)
        with self.assertRaises(BuildRejected):metadata073(value,'RemoteSigned')

    def test_new_reservation_phase_and_restart_prevention(self):
        path=self.root/'reservation075.json'
        value=dict(build_reservation_consumed=True,ledger_sha256='a'*64,authorization_sha256='b'*64,
            maximum_compiler_invocations=1,phase=BUILD_PHASE,orders_available=False)
        reserve_build075(path,value)
        with self.assertRaises(FileExistsError):reserve_build075(path,value)
        with self.assertRaises(BuildRejected):reserve_build074(self.root/'wrong-phase.json',value)

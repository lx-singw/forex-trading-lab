import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import test_sharing_build_073 as legacy

from forex_demo_lab.sharing_build_074 import *
from test_transport_lifecycle_060 import Clock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('build_entry074',ROOT/'scripts/runtime-sharing-build-074.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)


class Image074Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.clock=Clock();self.clock.utc+=86400000;self.b=Budget073(lambda:self.clock()[:2])
        self.p=self.root/'powershell.exe';self.p.write_bytes(b'signed image fixture')
    def test_measured_two_link_shell_accepted_only_by_image_reader(self):
        (self.root/'component').hardlink_to(self.p)
        r=read_image074(self.p,self.b,'shell');self.assertEqual(r['sha256'],hashlib.sha256(self.p.read_bytes()).hexdigest())
        with self.assertRaises(BuildRejected):read_bound073(self.p,self.b)
    def test_one_or_three_link_shell_rejected(self):
        with self.assertRaises(BuildRejected):read_image074(self.p,self.b,'shell')
        (self.root/'link1').hardlink_to(self.p);(self.root/'link2').hardlink_to(self.p)
        with self.assertRaises(BuildRejected):read_image074(self.p,self.b,'shell')
    def test_other_role_cannot_accept_shell_link_exception(self):
        (self.root/'component').hardlink_to(self.p)
        with self.assertRaises(BuildRejected):read_image074(self.p,self.b,'python')
        with self.assertRaises(BuildRejected):read_image074(self.p,self.b,'source')
    def test_other_image_must_still_be_single_link(self):
        p=self.root/'terminal64.exe';p.write_bytes(b'image');(self.root/'link').hardlink_to(p)
        with self.assertRaises(BuildRejected):read_image074(p,self.b,'terminal')
    def test_hash_byte_and_file_caps_remain_unchanged(self):
        (self.root/'component').hardlink_to(self.p);self.b.counts['hash_bytes']=LIMITS['hash_bytes']
        with self.assertRaises(BuildRejected):read_image074(self.p,self.b,'shell')
        self.assertEqual(self.b.counts['hash_bytes'],LIMITS['hash_bytes'])
    def test_native_metadata_uses_private_revision_not_zero_build_component(self):
        s=(ROOT/'scripts/runtime-sharing-build-074.py').read_text()
        self.assertEqual(s.count('.VersionInfo.FilePrivatePart'),2);self.assertNotIn('.VersionInfo.FileBuildPart',s)
        old=(ROOT/'scripts/runtime-sharing-build-073.py').read_text();self.assertEqual(old.count('.VersionInfo.FileBuildPart'),2)
    def test_separate_reservation_phase_and_restart_prevention(self):
        p=self.root/'new.json';v=dict(build_reservation_consumed=True,ledger_sha256='a'*64,authorization_sha256='b'*64,
            maximum_compiler_invocations=1,phase=BUILD_PHASE,orders_available=False)
        reserve_build074(p,v)
        with self.assertRaises(FileExistsError):reserve_build074(p,v)
        with self.assertRaises(BuildRejected):reserve_build073(self.root/'old.json',v)


class CorrectedEntry074Tests(legacy.BuildEntry073Tests):
    def setUp(self):
        super().setUp()
        names={'terminal':'terminal64.exe','editor':'metaeditor64.exe','shell':'powershell.exe','python':'python.exe'}
        for role,name in names.items():
            p=Path(self.ledger[role+'_path']);dest=p.with_name(name);p.rename(dest);self.ledger[role+'_path']=str(dest)
        (self.root/'component-store-reference').hardlink_to(Path(self.ledger['shell_path']))
    def run_entry(self):
        with patch.object(entry,'ROOT',self.root),patch.object(entry,'os',NS(name='nt')),patch.object(entry,'sys',NS(executable=self.ledger['python_path'])),\
             patch.object(entry.runpy,'run_path',return_value=self.api),patch.object(entry,'Budget073',lambda clock:Budget073(lambda:self.clock()[:2])),\
             patch.object(entry,'datetime',NS(now=lambda tz:datetime.fromtimestamp(self.clock.utc//1000,timezone.utc))),\
             patch.object(entry,'metadata',self.metadata),patch.object(entry,'compile_once073',self.compile):
            entry.run()
        return self.outputs[-1]
    def test_corrected_schema_phase_and_actual_exit_retained(self):
        r=self.run_entry();self.assertTrue(r['compiled']);self.assertEqual(r['build_record']['version'],'sharing_build_074_v1')
        self.assertEqual(r['build_record']['build_phase'],BUILD_PHASE);self.assertEqual(r['compiler_exit_code'],1)
        self.assertTrue(all(p.name.startswith('compiler074-') for p in self.build_root.iterdir()))

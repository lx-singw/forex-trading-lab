import runpy
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MEMBER='DAT_ASCII_EURUSD_T_202303.csv'
NOTES='DAT_ASCII_EURUSD_T_202303.txt'


class CompanionArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'original.zip'
        self.check=runpy.run_path(str(ROOT/'scripts/check-exness-comparison-025b.py'))['check_hist_members']

    def archive(self,notes='metadata',name=NOTES):
        with zipfile.ZipFile(self.path,'w') as archive:
            archive.writestr(MEMBER,'quotes')
            archive.writestr(name,notes)

    def test_derivation_and_exact_two_members(self):
        self.assertTrue(runpy.run_path(str(ROOT/'scripts/derive-exness-comparison-025b.py'))['verify_derivation']())
        self.archive()
        with zipfile.ZipFile(self.path) as archive:self.check(archive,MEMBER)

    def test_wrong_extra_nested_and_oversized_companions(self):
        for name in ('unexpected.txt','nested/'+NOTES):
            self.archive(name=name)
            with zipfile.ZipFile(self.path) as archive:
                with self.assertRaises(AssertionError):self.check(archive,MEMBER)
        self.archive(notes='x'*65537)
        with zipfile.ZipFile(self.path) as archive:
            with self.assertRaises(AssertionError):self.check(archive,MEMBER)

    def test_encrypted_member_rejected_before_read(self):
        self.archive()
        with zipfile.ZipFile(self.path) as archive:
            archive.getinfo(NOTES).flag_bits|=1
            with self.assertRaises(AssertionError):self.check(archive,MEMBER)

    def test_companion_crc_corruption_is_detected(self):
        self.archive()
        with zipfile.ZipFile(self.path) as archive:
            offset=archive.getinfo(NOTES).header_offset
        data=bytearray(self.path.read_bytes())
        name,extra=struct.unpack_from('<HH',data,offset+26)
        data[offset+30+name+extra]^=1
        self.path.write_bytes(data)
        with zipfile.ZipFile(self.path) as archive:
            with self.assertRaises(zipfile.BadZipFile):self.check(archive,MEMBER)


if __name__=='__main__':unittest.main()

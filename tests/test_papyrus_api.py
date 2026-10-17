"""Regression: reject the actual published diagnostic4, not a synthetic mock."""
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from formats import read_pex
from verify_papyrus_api import verify_pex_calls, verify_stubs


def objects_in_archive(filename):
    with zipfile.ZipFile(ROOT / 'dist' / filename) as archive:
        return [read_pex(archive.read(name))['objects'][0]
                for name in archive.namelist() if name.lower().endswith('.pex')]


class VanillaApiTests(unittest.TestCase):
    def test_compiler_stubs_match_independent_upstream_declarations(self):
        self.assertEqual(verify_stubs(ROOT / 'tools/papyrus-api'), 10)

    def test_published_base_uses_matching_native_calls(self):
        self.assertGreater(verify_pex_calls(objects_in_archive('KhajiitKeenSenses-0.1.4-MO2.zip')), 0)

    def test_rejects_actual_diagnostic4_extra_notification_argument(self):
        with self.assertRaisesRegex(ValueError, r'Debug.Notification expects 1 arguments; got 2'):
            verify_pex_calls(objects_in_archive('KhajiitKeenSenses-0.1.4-diagnostic4-MO2.zip'))

    def test_corrected_diagnostic5_has_matching_native_calls(self):
        self.assertGreater(verify_pex_calls(objects_in_archive('KhajiitKeenSenses-0.1.4-diagnostic5-MO2.zip')), 0)


if __name__ == '__main__':
    unittest.main()

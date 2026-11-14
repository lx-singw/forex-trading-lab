"""Record one full regression suite after the frozen descriptive diagnosis."""
import json
from pathlib import Path
import runpy
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
api = runpy.run_path(str(ROOT/'scripts/strategy-diagnosis-027.py'))
api['verify']()
started = time.monotonic()
result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
output = dict(kind='full_software_regression_027', passed=result.wasSuccessful(),
    tests_run=result.testsRun, tests_passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
    failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped),
    elapsed_seconds=time.monotonic()-started, new_tests=12,
    ledger_sha256=api['sha'](ROOT/'reports/strategy-diagnosis-027-ledger.json'),
    annual_eligible=False, orders_available=False)
api['write'](ROOT/'reports/strategy-diagnosis-027-tests.json', output)
print(json.dumps(output))
raise SystemExit(0 if result.wasSuccessful() else 1)

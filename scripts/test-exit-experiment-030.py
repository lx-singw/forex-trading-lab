"""One complete pre-return regression suite, exclusively recorded."""
from pathlib import Path
import runpy
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
api = runpy.run_path(str(ROOT/'scripts/exit-experiment-030.py'))
started = time.monotonic()
result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
output = dict(kind='pre_return_full_regression_030', passed=result.wasSuccessful(),
    tests_run=result.testsRun, tests_passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
    failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped),
    elapsed_seconds=time.monotonic()-started, new_tests=16, annual_eligible=False, orders_available=False)
api['write'](ROOT/'reports/exit-experiment-030-tests.json', output)
print(output)
raise SystemExit(0 if result.wasSuccessful() else 1)

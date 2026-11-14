"""Record the pre-extraction full regression suite, exclusively."""
from pathlib import Path
import runpy
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
api = runpy.run_path(str(ROOT/'scripts/trade-path-029.py'))
started = time.monotonic()
result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
api['write'](ROOT/'reports/trade-path-029-tests.json', dict(passed=result.wasSuccessful(),
    tests_run=result.testsRun, tests_passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
    failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped), new_tests=12,
    elapsed_seconds=time.monotonic()-started, annual_eligible=False, orders_available=False))
raise SystemExit(0 if result.wasSuccessful() else 1)

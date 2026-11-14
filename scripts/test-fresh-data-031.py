"""Full pre-observation regression, exclusively recorded."""
from pathlib import Path
import runpy
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT/'scripts/fresh-data-031.py'))
started = time.monotonic()
result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
API['write'](ROOT/'reports/fresh-data-031-tests.json', dict(kind='pre_observation_regression_031',
    passed=result.wasSuccessful(), tests_run=result.testsRun,
    tests_passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
    failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped),new_tests=16,
    elapsed_seconds=time.monotonic()-started, market_quote_reads=0, orders_available=False))
raise SystemExit(0 if result.wasSuccessful() else 1)

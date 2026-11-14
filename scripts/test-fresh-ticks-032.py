"""Full regression before the sole request, exclusively recorded."""
from pathlib import Path
import runpy
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/fresh-ticks-032.py'))
started=time.monotonic()
result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
API['write'](ROOT/'reports/fresh-ticks-032-tests.json',dict(kind='pre_acquisition_regression_032',passed=result.wasSuccessful(),
    tests_run=result.testsRun,tests_passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
    failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),new_tests=16,
    elapsed_seconds=time.monotonic()-started,market_requests=0,orders_available=False))
raise SystemExit(0 if result.wasSuccessful() else 1)

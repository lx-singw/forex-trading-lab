"""Unchanged125 and122 invented paths under a separate comparison wrapper."""
from .elliott_execution_fixture_125 import CASES as EW_CASES, fixture as ew_fixture
from .daily_runs_fixture_122 import CASES as DAILY_CASES, fixture as daily_fixture
from .elliott_comparison_126 import VERSION

CASES = tuple("ew_" + c for c in EW_CASES) + tuple("daily_" + c for c in DAILY_CASES)


def fixture(case="ew_long_target"):
    if type(case) is not str or case not in CASES:
        raise ValueError("comparison_fixture_case")
    value = ew_fixture(case[3:]) if case.startswith("ew_") else daily_fixture(case[6:])
    return {**value, "format": VERSION, "kind": "invented_strategy_comparison", "case": case}

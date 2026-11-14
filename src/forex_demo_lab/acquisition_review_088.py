"""Offline budget review. No adapter, reader, native entry or admission authority.

The floor deliberately gives ancestry, staging and controls ZERO cost. It is
an optimistic bound for the existing acquisition layout, not a feasible proof.
"""
from datetime import date
import hashlib
from pathlib import Path

from .synchronization_083 import LIMITS, require
from .synchronization_086 import CAPS, MQL_INPUTS, source_contract086

PHASE = '88000000000000000000000000000001'
DATE = '2026-10-09'


def budget_review088():
    # Keep the original before/after guard pairs for all control operations.
    control_operations = dict(pre=2*5, independent=2*3, post=2*5)
    control_guards = 2*sum(control_operations.values())
    wire_guards = 2*4
    wait_guards = 2*4
    total_guards = 2+control_guards+wire_guards+wait_guards
    raw_inspections = total_guards-1  # first guard precedes factory ownership
    # Four descriptor/path facts: info + final path + three security calls.
    # Two fresh path opens. Pipe: two mode, three security, seven peer calls.
    costs = dict(descriptor_and_path_facts=4*5, fresh_path_opens=2,
        pipe_modes=2, pipe_security=3, pipe_peer=7)
    per_inspection = sum(costs.values())
    api_floor = raw_inspections*per_inspection
    clock_floor = 1+2*api_floor
    max_bracketed = (LIMITS['clock_samples']-1)//2
    bridge_calls = 1+2*raw_inspections
    sdk_queries = 12*bridge_calls
    boot_queries = bridge_calls+raw_inspections
    return dict(version='acquisition_budget_review_088_v1', phase=PHASE,
        review_date=DATE, control_operations=control_operations,
        control_guards=control_guards, wire_guards=wire_guards,
        wait_guards=wait_guards, total_guards=total_guards,
        raw_inspections=raw_inspections, per_inspection_costs=costs,
        api_calls_per_inspection_floor=per_inspection,
        api_calls_floor=api_floor, clock_samples_floor=clock_floor,
        clock_samples_limit=LIMITS['clock_samples'],
        maximum_fully_bracketed_api_calls=max_bracketed,
        bridge_calls=bridge_calls, bridge_call_limit=CAPS['guards'],
        sdk_queries=sdk_queries, sdk_query_limit=1024,
        boot_queries=boot_queries, boot_query_limit=128,
        omitted_costs=['all_ancestry','factory','control_io','wire_io','cleanup'],
        ancestor_deduplication_sufficient=False,
        bound_scope='existing_api_and_guard_layout_only',
        native_timing_proven=False, runtime_authorized=False,
        orders_available=False)


def reader_requirements088(root):
    """Dated requirements only; explicitly not an implemented reader contract."""
    root=Path(root)
    old=source_contract086(root)
    own=('src/forex_demo_lab/acquisition_review_088.py',
        'docs/ACQUISITION-088-DESIGN.md','docs/ACQUISITION-088-POLICY.md')
    return dict(version='future_reader_requirements_088_v1', phase=PHASE,
        date=DATE, prior_reader_date=old['date'],
        prior_reader_inputs=dict(old['input_bindings']),
        requirements_inputs={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in own},
        prior_compile_inputs=list(MQL_INPUTS),
        required_windows_ms=dict(freshness=2000, release_to_open=10000,
            hold_min=30000, hold_max=31000, control_margin=250,
            episode=60000, outer=120000),
        required_account_type='actual_DEMO', required_algo_trading_allowed=False,
        new_reader_implemented=False, new_reader_compiled=False,
        native_entry_available=False, runtime_authorized=False,
        orders_available=False)


def admission088(contract, utc_date):
    """Requirements can never admit a runtime, including on the declared date."""
    require(type(contract) is dict and type(utc_date) is str)
    date.fromisoformat(utc_date)
    return False

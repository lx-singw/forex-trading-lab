"""Independent integer receipt arithmetic and fixed-metadata reconstruction."""
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT/'scripts/fresh-data-031.py'))
ledger = API['verify']()
inventory = API['sealed'](ROOT/'reports/fresh-data-031-inventory.json')
result = API['sealed'](API['PROBE'])
reservation = API['sealed'](API['RESERVATION'])
for report in (inventory,result,reservation):
    assert report['ledger_sha256'] == API['sha'](API['LEDGER'])
assert result['reservation_sha256'] == API['sha'](API['RESERVATION'])
assert reservation['terminal_launch_authorized'] is False
assert inventory['historical_price_rows_read'] == result['historical_price_rows_read'] == result['strategy_replays'] == 0
assert len(inventory['records']) == len(ledger['metadata_roles']) == 14
assert inventory['directories'] == ledger['existing_data_directories']
assert inventory['qualified_fresh_datasets_in_this_catalog'] == 0
for record in inventory['records']:
    name = record['path']
    original = json.loads((ROOT/name).read_text())
    assert record['sha256'] == ledger['bindings'][name]
    assert record['role'] == ledger['metadata_roles'][name]
    assert record['qualified_fresh_dataset'] is False
    assert record['evidence'] == {k:original[k] for k in ledger['metadata_fields'] if k in original}
assert result['requested_reads'] == 120 and 0 <= result['actual_quote_reads'] <= 120
rows = result['observations']
assert len(rows) <= result['actual_quote_reads']
lower, upper, latency, repeats, previous = [], [], [], 0, None
fields = {'poll_index','raw_time_msc','bid','ask','received_before_utc_ms','received_after_utc_ms',
          'received_before_monotonic_ns','received_after_monotonic_ns','repeated_snapshot'}
for i,row in enumerate(rows):
    assert set(row) == fields and row['poll_index'] == i
    for key in fields-{'bid','ask','repeated_snapshot'}:
        assert type(row[key]) is int
    assert type(row['repeated_snapshot']) is bool
    assert math.isfinite(row['bid']) and math.isfinite(row['ask']) and 0 < row['bid'] <= row['ask']
    before,after = row['received_before_utc_ms'],row['received_after_utc_ms']
    mb,ma = row['received_before_monotonic_ns'],row['received_after_monotonic_ns']
    assert before <= after and mb <= ma
    assert datetime.fromtimestamp(before/1000,timezone.utc).date().isoformat() == ledger['date']
    assert datetime.fromtimestamp(after/1000,timezone.utc).date().isoformat() == ledger['date']
    assert before >= result['probe_started_utc_ms']
    assert 0 <= mb-result['probe_started_monotonic_ns'] < 60_000_000_000
    assert ma-result['probe_started_monotonic_ns'] <= 60_000_000_000
    stamp = row['raw_time_msc']
    assert stamp > 0 and abs(stamp-after) <= 86400000
    if previous is not None:
        assert before >= previous['received_after_utc_ms'] and mb >= previous['received_after_monotonic_ns']
        assert stamp >= previous['raw_time_msc']
        repeat = all(row[k] == previous[k] for k in ('raw_time_msc','bid','ask'))
    else:
        repeat = False
    assert row['repeated_snapshot'] == repeat
    repeats += repeat
    lower.append(stamp-after); upper.append(stamp-before); latency.append(after-before)
    previous = row
if rows or 'clock_summary' in result:
    assert result['clock_summary'] == dict(observations=len(rows), repeated_snapshots=repeats,
        raw_minus_receipt_lower_ms=min(lower,default=None),raw_minus_receipt_upper_ms=max(upper,default=None),
        max_read_latency_ms=max(latency,default=None))
if result['status'] == 'completed_receipt_probe':
    assert len(rows) == result['actual_quote_reads'] == 120 and result['stop_reason'] is None
elif result['status'] == 'probe_not_started':
    assert result['actual_quote_reads'] == 0 and not rows
else:
    assert result['status'] == 'stopped_guarded_probe' and result['stop_reason'] is not None
assert result['continuous_tick_capture'] is result['raw_labels_interpreted_as_utc'] is False
assert result['local_clock_independently_certified'] is result['historical_timezone_verified'] is False
for report in (inventory,result):
    assert report['fresh_performance_eligible'] is report['annual_eligible'] is report['orders_available'] is False
serialized = json.dumps(result).lower()
assert not any('"'+field+'"' in serialized for field in ('login','server','password','account_number','name','balance'))
if result['contract_snapshot'] is not None:
    from forex_demo_lab.collection import SPEC_FIELDS
    assert set(result['contract_snapshot']) == set(SPEC_FIELDS)
API['write'](ROOT/'reports/fresh-data-031-checks.json',dict(kind='independent_fresh_readiness_check_031',passed=True,
    ledger_sha256=API['sha'](API['LEDGER']), inventory_sha256=API['sha'](ROOT/'reports/fresh-data-031-inventory.json'),
    probe_sha256=API['sha'](API['PROBE']), metadata_files_checked=14, observations_checked=len(rows),
    observed_account_runtime_is_not_independently_reverified=True,
    strategy_replays=0, historical_rows_read=0, fresh_performance_eligible=False,annual_eligible=False,orders_available=False))
print(json.dumps(dict(passed=True,metadata_files=14,observations=len(rows),status=result['status'])))

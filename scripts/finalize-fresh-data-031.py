"""Preserve the receipt probe and declare the next bounded full-tick sample."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import zipfile

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT/'scripts/fresh-data-031.py'))
sha, write, sealed = API['sha'], API['write'], API['sealed']
FINAL = ROOT/'reports/fresh-data-031-final-source.json'
REVIEW = ROOT/'reports/fresh-data-031-review.json'


def documents():
    ledger = API['verify']()
    tests = sealed(ROOT/'reports/fresh-data-031-tests.json')
    probe = sealed(API['PROBE'])
    checks = sealed(ROOT/'reports/fresh-data-031-checks.json')
    assert checks['passed'] and tests['passed']
    rows = probe['observations']
    status = probe['status']
    summary = probe.get('clock_summary', {})
    if status == 'completed_receipt_probe':
        assert len(rows) == 120
        first = datetime.fromtimestamp(rows[0]['received_before_utc_ms']/1000,timezone.utc).isoformat()
        last = datetime.fromtimestamp(rows[-1]['received_after_utc_ms']/1000,timezone.utc).isoformat()
        lower, upper = summary['raw_minus_receipt_lower_ms']/1000, summary['raw_minus_receipt_upper_ms']/1000
        observed = (f'The running terminal passed actual DEMO and USD checks, Algo Trading off, '
            f'and the private identity remained stable around all120 reads and the completion guard. '
            f'120 accepted snapshots span {first} through {last}; '
            f'{summary["repeated_snapshots"]} repeat the preceding timestamp/bid/ask. '
            f'Maximum measured quote-read latency is {summary["max_read_latency_ms"]}ms. '
            f'Raw-label minus receipt ranges from {lower:.3f} to {upper:.3f} seconds '
            '(approximately three hours ahead). Receipt timing, polling delay and stale quotes '
            'prevent interpreting this as an exact offset or historical UTC certification.')
        # This selection is a schema/collection diagnostic informed by the probe,
        # never an unseen validation or performance window.
        start = rows[0]['raw_time_msc']//1000*1000
        end = (rows[-1]['raw_time_msc']+999)//1000*1000
        assert 0 < end-start <= 120000
        next_plan = ['# Full-tick sample 032 — declared, not executed', '',
            'One current-date infrastructure diagnostic, informed by031 polling. It is not '
            'an unseen validation window or a strategy experiment. No tuning or returns.', '',
            f'Bind031 final snapshot, ledger, probe, reservation, checks, raw receipt witnesses, '
            f'the existing Windows MT5 runtime and exact collector/test/checker code before any history call.', '',
            f'Exact EURUSD raw label bounds: inclusive {start} through {end} milliseconds; '
            f'UTC formatter renders {datetime.fromtimestamp(start/1000,timezone.utc).isoformat()} '
            f'through {datetime.fromtimestamp(end/1000,timezone.utc).isoformat()}. '
            'These are API numeric source labels, not certified UTC instants. '
            'Round the first observed raw label down and last up to the containing second, '
            'to include every accepted031 witness without reordering source records.', '',
            'One copy_ticks_range request for that exact interval, COPY_TICKS_ALL. '
            'No alternate offset, retry, history expansion, symbol selection or terminal launch. '
            'Use an already-running terminal only; reject actual REAL/CONTEST/unknown, '
            'disconnect, Algo Trading on, non-USD or a private account/server identity change '
            'before/after the read and at completion. Current receipts must remain '
            '2026-10-06 UTC. If this declaration has expired, preserve a no-call outcome '
            'and declare a new date/window before a different request.', '',
            'Maximum120 raw-label seconds,20,000 returned rows,4MiB serialized evidence. '
            'The Python API cannot forcibly bound an in-flight native call; record elapsed '
            'time and stop without retry if it returns an error or exceeds the declared '
            '60-second soft timeout. Do not mistake API success for complete history.', '',
            'Exclusive originals under data/fresh-ticks-032: raw.csv with all source '
            'time,bid,ask,last,volume,time_msc,flags,volume_real fields; capture.json '
            'with safe receipt/request/version/current-contract and original hash/size. '
            'Reports fresh-ticks-032-{ledger,tests,checks,review,final-source}.json plus seals. '
            'Reserve output before connection/request. Preserve bounded returned rows and '
            'the failure on malformed schema, out-of-range labels or chronology defects; '
            'do not drop, sort, interpolate, normalize or splice. For an oversized response, '
            'preserve count/schema/safe hashes and stop without treating a truncated prefix '
            'as an original complete dataset. No identifiers or credentials exported.', '',
            'Test actual account guards, reconnect/identity changes, bounded date/range, '
            'empty/errors, exact field/price/flag/volume validation, tied sequences, '
            'duplicates, chronology/out-of-range rejection, size bounds and immutable '
            'outputs before acquisition. Independently reconstruct original-row counts, '
            'timestamps, ties/duplicates/gaps and matches to every031 timestamp/bid/ask '
            'witness. A missing match is reported, never silently repaired.', '',
            'This stage supplies a full-source sample instead of a poll log; it cannot '
            'certify API completeness, absolute/historical clock, sessions/outages, '
            'independent upstreams, commissions, financing, slippage or edge. No conversion '
            'or fresh/annual eligibility approval, no performance runner/candidate changes, '
            'no orders or MT5 settings/EA changes. Consumed2025, reservedNov–Dec2026 '
            'and all stopped providers remain untouched. Larger acquisition needs a '
            'new explicit plan after this diagnostic passes.', '']
    else:
        observed = (f'Probe status: {status}; safe stop reason: {probe["stop_reason"]}. '
                    f'Accepted observations: {len(rows)}; quote-read attempts: {probe["actual_quote_reads"]}. '
                    'No readiness or clock approval follows from a stopped probe.')
        next_plan = ['# Fresh-data follow-on 032 — not executed', '',
            'Preserve031 outcome. Resolve the recorded runtime/account/clock blocker; '
            'declare a new current-date bounded receipt probe with exclusive paths '
            'before any additional API read. Never retry into031 outputs. '
            'No account creation, settings changes or execution; eligibility remains false.', '']
    with (ROOT/'docs/FRESH-TICKS-032-PLAN.md').open('x') as f:
        f.write('\n'.join(next_plan))
    text = ['# Fresh-data readiness 031 — complete', '', observed, '',
        '## Local qualification inventory', '',
        'The fixed catalog covers14 canonical provenance/review files and the data-directory '
        'names at freeze. None supplies a qualified fresh validation dataset. The2024 '
        'windows are reused development;2025 is consumed; annual2020–2023 sources remain '
        'blocked on clock/coverage/cost evidence. This is a scoped inventory, not proof '
        'that other sources do not exist. No historical quote rows or strategy returns '
        'were read or recomputed.', '',
        '## What changed', '',
        'Separate fresh_data_031.py and fresh-data-031.py add a receipt-clock probe. '
        'It connects only to the already-running installed terminal, with the pinned '
        'existing Windows Python/MetaTrader5 files. It has no history request, order API, '
        'terminal launch, login, symbol selection or settings/deployment action. '
        'It checks actual account type and connection around every quote, rejects Algo '
        'Trading on, and compares private account/server identity without exporting either. '
        'Source labels, bid/ask and receipt/monotonic bounds remain separate.', '',
        'Maximum120 reads at500ms spacing; a60-second monotonic budget prevents starting '
        'a new read at the deadline and rejects a late return. Native in-flight calls '
        'cannot be forcibly time-limited by this sampler. Date, reversed-clock, '
        'raw-label24-hour bound, invalid quote and identity errors stop and preserve '
        'accepted observations without retry. Exception details are redacted.', '',
        '## Verification and preservation', '',
        '400 software tests pass (16 new), before any MT5 connection. New cases include '
        'demo/real/contest/unknown/boolean modes, disconnect/identity/server changes, '
        'Algo Trading/currency/symbol rejection, invalid quotes, tied/repeated snapshots, '
        'clock reversal/reserved receipt dates, elapsed/read bounds, partial preservation '
        'and privacy. Existing strategy/risk tests remain intact.', '',
        f'Preflight verified all900 prior bindings,864 archived members and36 external '
        f'inputs. New ledger freezes{len(ledger["bindings"])} bindings,14 metadata files '
        'and exclusive outputs. Independent checker recomputes all accepted observation '
        'ordering, clocks, bounds, repeats and arithmetic; fixed metadata evidence exactly '
        'matches originals. Original031 code is frozen;030 and earlier evidence is preserved.', '',
        'Runtime account checks are performed by the collector. The independent checker '
        'validates its sealed evidence and arithmetic, not a second broker connection '
        'or independent proof of account/session identity. Local-clock accuracy and '
        'complete provider tick delivery remain uncertified.', '',
        'Artifacts: reports/fresh-data-031-{ledger,tests,inventory,probe-reservation,probe,checks,review,final-source}.json '
        'with seals. Probe contains only approved current contract fields and quote/receipt '
        'observations; current contract properties do not establish historical fees/swaps '
        'or real fills. Final ZIP archives sources/reports/small fixtures. Prior ZIPs, '
        'large cached data, timezone files and pinned Windows runtime files remain '
        'verified external bindings; it is not a self-contained replay bundle.', '',
        '## Next step and limits', '',
        'Read FRESH-TICKS-032-PLAN.md: one exact bounded full-tick sample and independent '
        'original-row/witness audit, not executed. Polling can miss intervening quotes; '
        '53 repeated snapshots in a completed run are not missing-tick or market-closure '
        'evidence. Do not subtract an assumed three-hour offset and call the data UTC.', '',
        'Fresh performance and annual eligibility remain false. No profits, strategy '
        'selection, performance replays, broker accounts, provider contacts, credentials, '
        'paid access, stopped-provider retries, execution mode or orders. Consumed2025 '
        'and reservedNovember–December2026 remain excluded. Demo-forward trading is '
        'unactivated; this is collection infrastructure only.', '']
    with (ROOT/'docs/FRESH-DATA-031-RESULTS.md').open('x') as f:
        f.write('\n'.join(text))
    handoff = ('Latest — 2026-10-06: fresh-data readiness031 complete. Read '
        '`FRESH-DATA-031-RESULTS.md`. Fixed14-file metadata catalog has no qualified '
        'fresh dataset; no historical price rows or returns read. '+observed+' '
        '400 tests pass (16 new); independent metadata/receipt arithmetic checks pass. '
        'Prior900 bindings/864 archived members/36 external inputs verified;67 new '
        'frozen bindings. Current labels remain raw, not UTC-certified; poll snapshots '
        'are not a complete tick stream. No strategy/cost changes or selection; '
        'fresh/annual eligibility remains false and orders unavailable. Next '
        '`FRESH-TICKS-032-PLAN.md`, one exact full-source sample/witness audit, declared '
        'not executed. Existing running demo terminal may be used with Algo Trading off; '
        'never launch/login/change settings. Consumed2025/reservedNov–Dec2026 and stopped '
        'providers untouched. Earlier entries below are historical.\n\n')
    for name in API['API']['HANDOFF']:
        path = ROOT/name
        old = path.read_text()
        split = old.index('\n')+1
        path.write_text(old[:split]+'\n'+handoff+old[split:])
    print(json.dumps(dict(documents_written=True,status=status,observations=len(rows),next_plan_executed=False)))


def review():
    previous = API['prior_verify'](allow_handoff=True)
    ledger = API['verify']()
    checks = sealed(ROOT/'reports/fresh-data-031-checks.json')
    tests = sealed(ROOT/'reports/fresh-data-031-tests.json')
    probe = sealed(API['PROBE'])
    assert checks['passed'] and tests['passed']
    assert tests['tests_run'] == tests['tests_passed'] == 400 and tests['new_tests'] == 16
    assert checks['ledger_sha256'] == sha(API['LEDGER'])
    assert checks['probe_sha256'] == sha(API['PROBE'])
    assert checks['inventory_sha256'] == sha(ROOT/'reports/fresh-data-031-inventory.json')
    assert checks['observations_checked'] == len(probe['observations'])
    docs = ('docs/FRESH-DATA-031-RESULTS.md','docs/FRESH-TICKS-032-PLAN.md','scripts/finalize-fresh-data-031.py')
    for name in API['API']['HANDOFF']:
        assert 'FRESH-DATA-031-RESULTS.md' in (ROOT/name).read_text()
    assert 'not executed' in (ROOT/docs[1]).read_text()
    outputs = {p.relative_to(ROOT).as_posix():sha(p) for p in ROOT.glob('reports/fresh-data-031-*')
               if 'final-source' not in p.name and 'review' not in p.name}
    write(REVIEW,dict(kind='post_independent_fresh_readiness_review_031',passed=True,
        prior_snapshot_verification=previous,input_bindings_verified=len(ledger['bindings']),
        documentation_bindings={name:sha(ROOT/name) for name in docs},output_bindings=outputs,
        metadata_files_checked=14,observations_checked=checks['observations_checked'],
        software_tests_passed=400,probe_status=probe['status'],
        clock_statistics=probe.get('clock_summary'),qualified_fresh_datasets_in_catalog=0,
        historical_price_rows_read=0,strategy_replays=0,fresh_performance_eligible=False,
        annual_eligible=False,orders_available=False,next_plan=docs[1],next_plan_executed=False))
    print(json.dumps(dict(passed=True,tests=400,observations=checks['observations_checked'])))


def snapshot():
    checked = sealed(REVIEW)
    assert checked['passed']
    API['prior_verify'](allow_handoff=True)
    ledger = API['verify']()
    for name,expected in (checked['documentation_bindings']|checked['output_bindings']).items():
        assert sha(ROOT/name) == expected, name
    prior = sealed(API['PRIOR'])
    groups = {g:dict(v) for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings'}
    for name in API['API']['HANDOFF']:
        groups['source_bindings'][name] = sha(ROOT/name)
    for pattern in ('docs/*031*.md','docs/FRESH-TICKS-032-PLAN.md','scripts/*031*.py',
                    'src/forex_demo_lab/fresh_data_031.py','tests/test_fresh_data_031.py'):
        for path in ROOT.glob(pattern):
            groups['source_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    for path in ROOT.glob('reports/fresh-data-031*'):
        assert 'final-source' not in path.name
        groups['report_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    for suffix in ('.json','.sha256','.zip'):
        path = API['PRIOR'].with_suffix(suffix)
        groups['report_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    already = {n:h for v in groups.values() for n,h in v.items()}
    groups['fresh_input_bindings'] = {}
    for name,expected in ledger['bindings'].items():
        if name in already:
            assert already[name] == expected,name
        else:
            groups['fresh_input_bindings'][name] = expected
    bindings = {n:h for v in groups.values() for n,h in v.items()}
    assert len(bindings) == sum(map(len,groups.values()))
    external = {n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
                n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal = {n:h for n,h in bindings.items() if n not in external}
    for name,expected in bindings.items():
        assert sha(ROOT/name) == expected,name
    archive = FINAL.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(internal):z.write(ROOT/name,name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.infolist()) == len(internal)
        assert set(z.namelist()) == set(internal)
        for name in z.namelist():assert hashlib.sha256(z.read(name)).hexdigest() == internal[name]
    write(FINAL,dict(kind='post_fresh_data_readiness_snapshot_031',**groups,
        archive_external_bindings=external,archive_members_verified=len(internal),external_bindings_verified=len(external),
        archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
        snapshot_scope='Sources/reports/small fixtures archived; cached data, prior ZIPs, timezone and Windows runtime files externally hash-bound and required',
        previous_snapshot=API['PRIOR'].relative_to(ROOT).as_posix(),previous_snapshot_sha256=sha(API['PRIOR']),
        completed_utc=datetime.now(timezone.utc).isoformat(),software_tests_passed=400,
        metadata_files_checked=14,observations_checked=checked['observations_checked'],
        historical_price_rows_read=0,strategy_replays=0,fresh_performance_eligible=False,
        annual_eligible=False,orders_available=False,next_plan=checked['next_plan'],next_plan_executed=False))
    print(json.dumps(dict(bindings=len(bindings),archive_members=len(internal),external_bindings=len(external),manifest_sha256=sha(FINAL))))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('documents','review','snapshot'))
    {'documents':documents,'review':review,'snapshot':snapshot}[parser.parse_args().action]()

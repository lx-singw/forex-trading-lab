"""Offline closure of a stopped documentation fetch; contains no network client."""
import argparse
import json
from pathlib import Path
import runpy
import zipfile

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT / 'scripts/research-readiness-091.py'))
sha, sealed, write, bound = (API[k] for k in ('sha', 'sealed', 'write', 'bound'))
HANDOFF, ARCHIVE, ZERO, FALSE = (API[k] for k in ('HANDOFF', 'ARCHIVE', 'ZERO', 'FALSE'))
PREFIX = 'archived-evidence-092'
LEDGER = ROOT / f'reports/{PREFIX}-ledger.json'
PRIOR = ROOT / 'reports/research-readiness-091-final-source.json'
REVIEW = ROOT / 'reports/research-readiness-091-completion-review.json'
ATTEMPT = ROOT / f'reports/{PREFIX}-doc-attempt.json'
OUTCOME = ROOT / f'reports/{PREFIX}-doc-outcome.json'
POLICY = ROOT / 'docs/ARCHIVED-EVIDENCE-092-POLICY.md'
PLAN = ROOT / 'docs/CHALLENGER-CHRONOLOGY-093-PLAN.md'
RESULT = ROOT / 'docs/ARCHIVED-EVIDENCE-092-RESULTS.md'
DOC_URL = 'https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server'
OWN = ('scripts/archived-evidence-092.py', 'docs/ARCHIVED-EVIDENCE-092-POLICY.md',
       'docs/CHALLENGER-CHRONOLOGY-093-PLAN.md')


def validate():
    a, o = sealed(ATTEMPT), sealed(OUTCOME)
    assert a['attempt_consumed'] and a['exact_url'] == o['exact_url'] == DOC_URL
    assert a['maximum_documentation_opens'] == a['documentation_attempts_reserved'] == 1
    assert a['plan_sha256'] == sha(ROOT / 'docs/ARCHIVED-EVIDENCE-092-PLAN.md')
    assert a['prior_final_source_sha256'] == sha(PRIOR)
    assert a['prior_review_sha256'] == sha(REVIEW)
    assert o['attempt_sha256'] == sha(ATTEMPT)
    assert o['outcome'] == 'documentation_fetch_blocked_by_browsing_tool'
    assert o['tool'] == 'web.run.open' and o['tool_result'] == 'Failed to fetch restricted URL'
    assert o['http_status'] is None and o['remote_server_denial_established'] is False
    assert o['documentation_opens_attempted'] == 1 and o['documentation_opens_successful'] == 0
    assert o['index_syntax_verified'] is False
    assert o['stopped_before_index_resolution'] and o['no_fallback_or_retry']
    for k in ('index_requests_started', 'index_records_received', 'snapshot_opens_started',
              'provider_documents_obtained', 'tests_run_this_phase', 'new_tests',
              'historical_price_rows_read', 'strategy_replays', 'new_returns_computed'):
        assert type(o[k]) is int and o[k] == 0, k
    for k in ('historical_evidence_added', 'archive_service_access_tested',
              'absence_of_archived_evidence_proven', 'selection_authorized', 'candidate_promoted'):
        assert o[k] is False, k
    assert o['latest_retained_tests'] == 1942
    for k, v in {**ZERO, **FALSE}.items():
        assert type(a[k]) is type(v) and a[k] == v
        assert type(o[k]) is type(v) and o[k] == v
    return o


def freeze():
    API['verify']()
    r, v = sealed(PRIOR), sealed(REVIEW)
    assert sha(PRIOR) == '8965ad8e1675272604fd438aa16339948c8fbe9616acba05a0a3dfb9948be061'
    assert v['review_passed'] and v['final_source_sha256'] == sha(PRIOR)
    assert (v['bindings_verified'], v['archive_members_verified']) == (2867, 2651)
    assert ARCHIVE(PRIOR, r) == 2651
    b = dict(r['source_and_evidence_bindings'])
    for n in HANDOFF:
        b.pop(n, None)
    for n, h in b.items():
        assert sha(bound(n)) == h, n
    for p in (PRIOR, PRIOR.with_suffix('.sha256'), PRIOR.with_suffix('.zip'), REVIEW,
              REVIEW.with_suffix('.sha256'), ATTEMPT, ATTEMPT.with_suffix('.sha256'),
              OUTCOME, OUTCOME.with_suffix('.sha256'), *(ROOT / n for n in OWN)):
        b[p.relative_to(ROOT).as_posix()] = sha(p)
    validate()
    write(LEDGER, dict(bindings=b, prior_source_sha256=sha(PRIOR),
        policy_sha256=sha(POLICY), next_plan_sha256=sha(PLAN),
        maximum_checks=1, maximum_full_regressions=0, latest_retained_tests=1942,
        tests_run_this_phase=0, new_tests=0, **ZERO, **FALSE))
    print(json.dumps(dict(frozen=True, bindings=len(b))))


def verify():
    l = sealed(LEDGER)
    for n, h in l['bindings'].items():
        assert sha(bound(n)) == h, n
    assert l['prior_source_sha256'] == sha(PRIOR)
    assert l['policy_sha256'] == sha(POLICY) and l['next_plan_sha256'] == sha(PLAN)
    validate()
    return l


def check():
    l = verify()
    write(ROOT / f'reports/{PREFIX}-checks.json', dict(checks_passed=True,
        ledger_sha256=sha(LEDGER), attempt_sha256=sha(ATTEMPT), outcome_sha256=sha(OUTCOME),
        frozen_inputs_verified=len(l['bindings']), prior_closure_verified=True,
        documentation_attempts=1, index_requests=0, snapshot_opens=0,
        setup_verified=False, historical_evidence_added=False, stopped_as_planned=True,
        prior_failure_records_preserved=True, latest_retained_tests=1942,
        tests_run_this_phase=0, new_tests=0, next_plan_executed=False,
        historical_price_rows_read=0, strategy_replays=0, new_returns_computed=0,
        **ZERO, **FALSE))
    print(json.dumps(dict(checks_passed=True, index_requests=0, snapshot_opens=0)))


RESULT_TEXT = '''# Archived documentation092 — stopped before index requests

The only permitted API-documentation open was blocked by the browsing tool:
“Failed to fetch restricted URL”. It returned no documentation body or HTTP
status. This does not establish a remote GitHub denial, test Internet Archive
access or prove that archived provider documents are absent.

The exact attempted URL was
https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server.
Its attempt was reserved before the fetch; the failure is retained separately.
The frozen092 plan required verified query syntax and stopping on setup failure.
No query resolution, archive-index request, returned index record or snapshot
open occurred. No retry, alternate URL/tool/identity or workaround was used.
Unused downstream allowances do not authorize resuming this stopped phase.

No new historical clock/session evidence was obtained. The four planned
HistData/Exness origins were not searched through the archive service. Their
2020–2023 clock applicability, fixed-EST conflict, March gap and July truncation
remain unresolved, alongside coverage, lineage, metadata revisions and costs.
Current documents, relative prices and synthetic tests still cannot clear them.
No historical source transformation, blended/interpolated data or gate change.

## Verification

Verified091 closure: 2,867 source/evidence bindings and2,651 archive members.
Checked the hash-bound attempt/outcome, exact documentation budget, prerequisite
failure and zero downstream requests. New closure includes the frozen source
and evidence chain, archive verification and the four updated handoffs.
Latest retained suite: 1,942 passing tests from090. No tests run or added in092;
this was a document-access attempt followed by offline evidence checks.
Hash verification reads retained opaque bytes without decoding market rows.

No strategy replay, new return, candidate selection/promotion, native invocation,
SDK/DLL/WMI/MT5/compiler/deployment/log/market/order/receipt/grant action. The090
native branch remains closed. Provider stops, October quarantine, consumed2025
and reserved Nov–Dec2026 remain. Eligibility, runtime and orders stay false;
real-money execution is unavailable and demo automated orders remain off.

## Next work

`CHALLENGER-CHRONOLOGY-093-PLAN.md` prepares separate chronological software for
the existing C00/C05/C06/C07/C08 batch using invented quotes only. It preserves
the009 selection screens, both003 cost scenarios and the original009/020 runner.
Tests must demonstrate training-only choices, choice locking before test data,
cost/equity reconciliation, protective-stop/restart behavior and rejection of
market inputs before iteration. This useful software work can proceed while
evidence is missing; it will not establish a profitable market edge or authorize
execution. The plan is frozen and unexecuted in092. No UI action is required.
'''

LATEST_TEXT = (
    'Latest — archived documentation092 stopped before archive-index requests: the sole exact '
    'API-documentation open returned browsing-tool restricted-URL failure, no HTTP status. '
    'Setup syntax unverified; frozen plan required stopping. No retry/workaround; zero index '
    'requests/snapshot opens/provider documents. This is not proof of absent archives or remote '
    'service denial. Read ARCHIVED-EVIDENCE-092-RESULTS.md.091 closure verified2867 bindings/2651 '
    'members; attempt/outcome and zero downstream activity checked. Latest retained1942 tests '
    'from090; no tests in092. Historical clocks/session/coverage/lineage/cost and metadata gates, '
    'provider stops, consumed2025/reserved Nov–Dec2026/October quarantine unchanged. Native090 '
    'branch closed. No new returns/selection/promotion or native/SDK/MT5/compiler/deploy/log/market/'
    'orders/receipts/grants; eligibility/runtime/orders false. Next093 separate synthetic-only '
    'chronological C00/C05/C06/C07/C08 software, original009/020 unchanged; plan unexecuted. '
    'No UI action. Earlier entries historical.\n\n')


def seal():
    l = verify()
    c = sealed(ROOT / f'reports/{PREFIX}-checks.json')
    assert c['checks_passed'] and c['ledger_sha256'] == sha(LEDGER)
    with RESULT.open('x') as f:
        f.write(RESULT_TEXT)
    b = dict(l['bindings'])
    for n in HANDOFF:
        p = ROOT / n
        s = p.read_text()
        i = s.index('\n') + 1
        p.write_text(s[:i] + '\n' + LATEST_TEXT + s[i:])
        b[n] = sha(p)
    b[RESULT.relative_to(ROOT).as_posix()] = sha(RESULT)
    for pattern in (f'reports/{PREFIX}-*.json', f'reports/{PREFIX}-*.sha256'):
        for p in ROOT.glob(pattern):
            b[p.relative_to(ROOT).as_posix()] = sha(p)
    for n, h in b.items():
        assert sha(bound(n)) == h, n
    external = {n: h for n, h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal = {n: h for n, h in b.items() if n not in external}
    final = ROOT / f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'), 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):
            z.write(ROOT / n, n)
    record = dict(source_and_evidence_bindings=b, archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')), archive_members_verified=len(internal),
        documentation_attempts=1, index_requests=0, snapshot_opens=0,
        historical_evidence_added=False, stopped_as_planned=True, latest_retained_tests=1942,
        tests_run_this_phase=0, new_tests=0, next_plan_executed=False,
        historical_price_rows_read=0, strategy_replays=0, new_returns_computed=0,
        **ZERO, **FALSE)
    ARCHIVE(final, record)
    write(final, record)
    print(json.dumps(dict(sealed=True, bindings=len(b), members=len(internal), sha256=sha(final))))


def review():
    l = verify()
    final = ROOT / f'reports/{PREFIX}-final-source.json'
    r = sealed(final)
    b = r['source_and_evidence_bindings']
    for n, h in b.items():
        assert sha(bound(n)) == h, n
    members = ARCHIVE(final, r)
    assert all(b.get(n) == h for n, h in l['bindings'].items())
    c = sealed(ROOT / f'reports/{PREFIX}-checks.json')
    assert c['checks_passed'] and c['ledger_sha256'] == sha(LEDGER)
    assert c['attempt_sha256'] == sha(ATTEMPT) and c['outcome_sha256'] == sha(OUTCOME)
    assert RESULT.read_text() == RESULT_TEXT
    assert (r['documentation_attempts'], r['index_requests'], r['snapshot_opens'],
            r['tests_run_this_phase'], r['new_tests']) == (1, 0, 0, 0, 0)
    assert r['historical_evidence_added'] is False and r['next_plan_executed'] is False
    for k, v in {**ZERO, **FALSE}.items():
        assert type(r[k]) is type(v) and r[k] == v
    write(ROOT / f'reports/{PREFIX}-completion-review.json', dict(review_passed=True,
        final_source_sha256=sha(final), bindings_verified=len(b), archive_members_verified=members,
        frozen_inputs_verified=len(l['bindings']), frozen_input_coverage_complete=True,
        stopped_as_planned=True, historical_evidence_added=False, documentation_attempts=1,
        index_requests=0, snapshot_opens=0, latest_retained_tests=1942,
        tests_run_this_phase=0, new_tests=0, next_plan_sha256=sha(PLAN), next_plan_executed=False,
        prior_failure_records_preserved=True, **ZERO, **FALSE))
    print(json.dumps(dict(review_passed=True, bindings=len(b), members=members, tests_run=0)))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=('freeze', 'verify', 'check', 'seal', 'review'))
    dict(freeze=freeze, verify=lambda: print(len(verify()['bindings'])), check=check,
         seal=seal, review=review)[p.parse_args().action]()

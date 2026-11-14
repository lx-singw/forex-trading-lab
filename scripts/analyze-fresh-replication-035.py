"""Post-exit primary analysis of originals using the seven predeclared definitions."""
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/fresh-replication-035.py'))
from forex_demo_lab.replication_analysis_035 import analyze,original


def main():
    API['verify']();folder=API['OUTPUT'];capture=API['sealed'](folder/'capture.json')
    decoded={'ticks':[],'bars':[]}
    for r in capture['reads']:
        if r['kind'] in decoded and r['complete_original_preserved']:
            decoded[r['kind']]=original(folder,r['kind'],r)
    old=API['sealed'](ROOT/'data/fresh-context-033/capture.json')
    witnesses=original(ROOT/'data/fresh-context-033','ticks',old['reads'][1])
    invalid=any(r.get('complete_original_preserved') and (r.get('audit',{}).get('error_counts') or r.get('audit',{}).get('errors')) for r in capture['reads'])
    if invalid:
        result=dict(analysis_available=False,analysis_stop_reason='invalid_originals_not_interpreted',source_rows=len(decoded['ticks']),
            witnesses_matched=None,disagreement_rows=None,all_four_relative_hypotheses_passed=False,
            prior_033_diagnostic_passed=False,strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False)
    else:
        result=analyze(decoded['ticks'],decoded['bars'],witnesses)
        result.update(analysis_available=True,analysis_stop_reason=None)
    result.update(kind='fixed_four_source_hour_analysis_035',ledger_sha256=API['sha'](API['LEDGER']),
        capture_sha256=API['sha'](folder/'capture.json'),market_requests=capture['requests'],
        collector_rows_valid=capture['status']=='four_source_hours_originals_preserved_and_rows_valid')
    result['diagnostic_passed']=result['collector_rows_valid'] and result['all_four_relative_hypotheses_passed'] and result['witnesses_matched']==13769
    API['write'](ROOT/'reports/fresh-replication-035-analysis.json',result)
    print({k:result[k] for k in ('source_rows','witnesses_matched','disagreement_rows','diagnostic_passed')})


if __name__=='__main__':main()

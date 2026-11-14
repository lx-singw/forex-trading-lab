"""Derive companion/checker without modifying042 or recompiling/redeploying."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
worker=(ROOT/'scripts/clock-runtime-042.py').read_text().replace("scripts/native-compiler-042.py","scripts/clock-session-043.py")
worker=worker.replace('reports/clock-observer-042-','reports/clock-observer-043-')
worker=worker.replace("from forex_demo_lab.compiler_launch_039 import ps_quote", "from forex_demo_lab.compiler_launch_039 import ps_quote\nfrom forex_demo_lab.clock_session_043 import require_interactive,reuse_path")
start=worker.index('def deploy(');end=worker.index('\ndef running(',start)
replacement='''def reuse_deployment(shell,data_root,artifact):
    source=sealed(ROOT/'reports/clock-observer-042-deployment.json')
    deployment={k:source[k] for k in ('folder','artifact_binding')}
    expected=reuse_path(data_root,deployment,sha(artifact))
    path=Path(str(expected))
    for parent in (path,*path.parents):
        if parent.is_symlink() or getattr(parent,'is_junction',lambda:False)():raise ValueError('reuse_reparse_rejected')
    if not path.is_file() or sha(path)!=sha(artifact):raise ValueError('reuse_artifact_changed')
    return deployment
'''
worker=worker[:start]+replacement+worker[end:]
worker=worker.replace('deployment=deploy(shell,data_root,artifact)','deployment=reuse_deployment(shell,data_root,artifact)')
worker=worker.replace("    ledger=API['verify']();date_guard();", "    require_interactive(sys.stdin)\n    ledger=API['verify']();date_guard();")
worker=worker.replace("'exclusive_deployment_failed'", "'reuse_artifact_changed','reuse_reparse_rejected'")
checker=(ROOT/'scripts/check-clock-runtime-042.py').read_text().replace('scripts/native-compiler-042.py','scripts/clock-session-043.py')
checker=checker.replace('reports/clock-observer-042-','reports/clock-observer-043-')
runner=(ROOT/'scripts/test-native-compiler-042.py').read_text().replace('scripts/native-compiler-042.py','scripts/clock-session-043.py')
runner=runner.replace('reports/native-compiler-042-regression.json','reports/clock-session-043-regression.json').replace('new_tests=20','new_tests=8')
for name,text in {'scripts/clock-runtime-043.py':worker,'scripts/check-clock-runtime-043.py':checker,'scripts/test-clock-session-043.py':runner}.items():
    with (ROOT/name).open('x',encoding='utf-8') as out:out.write(text)
print('Persistent043 companion created; reuses042 EX5, no compiler/deployment calls')

"""Harmless child argv witness; stdout only, no filesystem writes."""
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parent
assert root.name.startswith('compiler039-fixture-')
assert len(sys.argv)==3
expected=['/compile:'+str(root/'source with spaces.mq5'),'/log:'+str(root/'log with spaces.log')]
assert sys.argv[1:3]==expected
print(json.dumps(dict(argv=sys.argv[1:3],arguments_equal=True)))

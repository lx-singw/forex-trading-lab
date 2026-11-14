"""Harmless argv witness: no imports beyond JSON/sys and no filesystem writes."""
import json
import sys
print(json.dumps(dict(argv=sys.argv[1:])))

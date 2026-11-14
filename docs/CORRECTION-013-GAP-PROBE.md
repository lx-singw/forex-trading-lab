# Read-only March gap probes — declared before requests

The corrected candidate calendar leaves source19:00 missing on each late-March
Sunday, corresponding to candidate UTC23:00. The stored broker H1 reference
has those hours at raw Monday02:00. Preserve all gaps; do not compress time or
patch either provider.

Capture only raw labels 02:00 through 03:00 exclusive on 2020-03-30,
2021-03-29, 2022-03-28 and 2023-03-27, using the existing actual-demo guarded
read-only collector. Each has a separate folder under `data/correction-013-gaps`.
Preserve failure/empty results; no alternate date or automatic retry.
Rebuild every bid/ask hour and compare all bid OHLC with the original H1
reference at the unchanged 0.05-pip tolerance. This only checks whether an
alternative captured hour exists and reconstructs; it does not blend feeds,
certify annual UTC or clear the failed 012 anchor screen or data eligibility.
Algo Trading remains off and no terminal settings/orders are changed.

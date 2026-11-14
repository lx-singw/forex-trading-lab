# Bounded transport follow-up to probe 011

The first WSL request returned URLError without an HTTP status or response
body. Preserve `data/clock-011/20230714-19/download.json`. Both Windows and WSL
DNS lookups resolve the hostname normally. No public archive bytes or price
statistics have been read. This is a transport failure, not evidence of an
HTTP access refusal. The current clock/data gates remain unchanged.

Before requesting further data: permit one ordinary Windows Python request to
the same public URL into `data/clock-011/20230714-19-windows`. Use default TLS
verification and the same default Python user agent; no credentials, proxies,
IP substitution, identity change or paid service. Stop on any HTTP failure or
transport failure and preserve it. On success, the original eleven-file scope
and unchanged checks in CLOCK-011-PLAN.md apply. No automatic request retries.

The client must record HTTP status before inspecting the redirect, use
`urllib.parse.urlparse` for that inspection, and record a sanitized transport
failure category. Do not log environment variables or exception free text.

# Independent reference acquisition for history 009

Declared before requesting the reference: use the existing guarded, read-only
MT5 H1 collector for raw source-label 2020-01-01 through 2024-01-01 exclusive.
This supplements the frozen HistData acquisition, without changing its scope,
selection protocol or gates. Recheck actual demo-account mode around every
read; do not log account identifiers, submit orders or change terminal settings.

Capture to a new `data/history-009-mt5-reference` folder. Preserve raw labels,
request bounds, coverage and hashes. If any window is unavailable or outside
the requested bounds, preserve the failure and do not pretend a complete
reference was captured. Do not alter the terminal's history/chart settings to
force availability. This is acquisition only: no price-alignment scores,
timestamp selection, strategy returns or performance approval. Corroboration
windows and thresholds must be separately declared before comparisons.

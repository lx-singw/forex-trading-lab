# Native recorder156 portable verification

15 November2026. Final verification003 passes170 targeted checks:24 new and146
existing. Shared MQL/C++ decisions and Python file/health tests use invented data.
The isolated native build passes0 errors/0 warnings in MetaEditor5.0.0.6320.
No terminal, account or price is accessed. Entry remains hard closed.

`compile-manifest.json` binds the five staged/canonical MQL sources, compiler and
EX5 hashes. Only the compact result is portable; full compiler logs and EX5 stay
outside Git in ignored reports/non-terminal staging. `source-sha256.json`,
`preservation.json`, `declaration.json`, `invocation.json`, `tests.txt` and
`verification-summary.json` come from final ignored verification003.
`artifact-sha256.json` binds that folder, including its ignored source archive.
`portable-sha256.json` binds the portable copies, including this README.

Initial verification001 precedes the folder/close revision;002 stopped before
tests on config-basename resolution. Its failure is retained separately under
ignored reports;003 corrects only that resolver and verifies all46 old controls.
Earlier builds/verifications are not mixed into the final170 count.

These artifacts establish compilation and component behaviour. They do not prove
actual native IO, producer authentication, measured-clock relay integration,
physical power effects, storage durability or market eligibility. No actual
native journal is captured/admitted. See [scope and remaining work](../../NATIVE-RECORDER-156-RESULTS.md).

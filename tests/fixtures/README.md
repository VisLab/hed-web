# Test fixtures

## bidsDemoData

A copy of the BIDS demo dataset from hed-javascript, used by `tests/unit/pageFlows.spec.js`.

- Source repo: https://github.com/hed-standard/hed-javascript
- Source path: `tests/bidsDemoData`
- Commit: 613ece8 (the hed-validator commit locked in `package-lock.json`)
- 56 files

Copied with:

```
git -C H:/Repos/hed-javascript archive 613ece8 tests/bidsDemoData | tar -x --strip-components=1 -C tests/fixtures
```

Do not edit these files; refresh them from hed-javascript with the command above when the hed-validator commit
changes.

## small

Minimal inputs written for the page-flow tests: `valid_sidecar.json` and `invalid_sidecar.json` (one HED value
`Blech`), `valid_events.tsv` (no HED column) and `invalid_events.tsv` (a HED cell `Blech`).

# Morpheus

> Morpheus is a fork of [Graphiti](https://github.com/getzep/graphiti) that turns a temporal knowledge graph into an active reasoning substrate — every fact carries its justifications, every choice records its rejected alternatives, every belief lives as an immutable revision under moving tag pointers. The headline query is `explain(factId)`. The graph retains everything but auto-injects nothing into agent context.

## Status

Phase 0 — bootstrap. The fork is the Graphiti source tree (rooted at this commit on `v0.29.0`), with [Graphify](https://github.com/safishamsi/graphify) integrated as native source under `graphify/`. No new behaviour yet; this commit just gets the two upstreams co-located and mutable.

## Where to read first

- [`docs/seed.md`](docs/seed.md) — founding design doc: landscape survey (May 2026), the gap Morpheus targets, planned node/edge taxonomy, hard problems, open questions.
- [`docs/notes-2026-05-14.md`](docs/notes-2026-05-14.md) — session notes from a sibling project's Graphiti work that should seed v0 (bulk add-episodes, validation-on-add, deletion-impact, rename detection).
- [`docs/summary.md`](docs/summary.md) — cross-project log from the sibling project to Morpheus (tooling friction → design implications).
- [`docs/naming.md`](docs/naming.md) — naming candidates and rationale.
- [`docs/upstream/`](docs/upstream/) — preserved Graphiti upstream README, CONTRIBUTING, and CODE_OF_CONDUCT.

## Attribution

See [`NOTICE`](NOTICE) for upstream attribution. Graphiti is Apache-2.0; Graphify is MIT.

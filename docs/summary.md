# Tooling discussion log — MLGameBot → reasoning-graph

Cross-project channel: as MLGameBot (the lived-experience project) hits friction with its tooling surface — skills, hooks, agent-dispatch shapes, Graphiti conventions — entries get appended here. Raw material for the reasoning-graph design (Master's planned Graphiti fork with embedded rules + reasoning-backtracking).

**Append-only.** Each entry is dated. Tooling-side-effect observations live alongside design-implication notes when those emerge.

---

## 2026-05-14 — session-wide hook redundancy + agent-resume gap

Session context: implemented chunked log shipping for issue reports (full PR + edge function + Vercel proxy + 8 optimize iterations).

### Observations

- **`graphiti-search-nudge.mjs` re-fires on the same concept all session.** The PreToolUse hook on grep-class Bash commands injects *"Try `/graphiti explain <topic>` first"* whether or not the agent has already queried Graphiti for that concept earlier in the session. Observed ~9 fires across `move-resources`, `tus-uploader`, `index.ts` — each followed by the agent's earlier-queried answer being re-recalled rather than re-fetched. The hook lacks session-state awareness. Same shape applies to `graphiti-file-context.mjs` (PreToolUse on Edit/Write).

- **Storing "concept already queried" as state has a lifecycle question.** First instinct (a file at `.claude/session-state/...`) needs explicit session-end cleanup or it provides falsy info to the next session. Master's reaction (verbatim): *"that file must be cleaned at the end or before every session so it doesn't provide falsy info. do you think think there is a better way to do this?"*

- **Better alternative under consideration: hook reads its own session transcript.** Claude Code's PreToolUse hook payload includes `transcript_path` — the JSONL file of the current session. The hook can grep that file for prior `mcp__graphiti__search_*` tool-call records and extract their `query` parameters. Zero state file; the transcript IS the source of truth; resets-per-session by construction. Performance cost: ~50ms parse on a mid-session transcript (typical <5MB). Reasoning-graph implication: the same architectural shape — *"derive recency state from the conversation transcript rather than maintaining a parallel store"* — is a candidate primitive for the reasoning-graph's own provenance layer. Avoids duplicate-source-of-truth bugs.

### Tooling built / approved this session (cited in `.claude/feedback/2026-05-14_21-30.md`)

- `scripts/verify-session.sh` — wraps `tsc-node && tsc-web && lint-changed` into a single command that runs each step independently and prints a PASS/FAIL summary. Replaces a 250-char Bash retype that ran ~7 times during one /optimize session. **Design observation:** the inline `&&`-chained form silently swallows downstream failures when upstream fails — the wrapper script's no-early-exit shape is the correctness fix, not just convenience. Implication for reasoning-graph: any "run a sequence of validations" primitive should expose the FULL result vector, not just the first failure.

- `scripts/edge-curl.sh <function-name> <json-body>` — wraps a Supabase Edge Function POST with apikey + Authorization from `apps/web/.env.local`. Replaces ~12 inline curl invocations each pasting a 220-char JWT verbatim. **One Bash gotcha worth recording:** the default-value syntax `"${2:-{}}"` does NOT default to a literal `{}` — Bash closes the parameter substitution at the first unbalanced `}`, leaving the second `}` as a trailing literal that gets appended to the actual value. Use an explicit if/else for JSON-shaped defaults. Reasoning-graph implication: rules/constraints that EMBED a literal whose syntax overlaps the rule-language's own escape characters need their own escaping discipline. Same class of bug.

- `.claude/commands/episode-for.md` — on-demand backfill skill for historical commit episodes (one SHA at a time). **Pattern observation:** Master rejected the passive `pending-graphiti-episodes.md` list as a drain target (*"adding commit summaries to graphiti is best within the session context, instead of adding hystorical commits to graphiti"*). The skill exists for the deliberate-invocation case (a specific past SHA matters now), not for completeness. Implication: the reasoning-graph fork should NOT export a `backfillAll()` API even if technically possible — historical entries written without session context degrade retrieval quality.

### Sub-agent dispatch gap

- **`Plan` agent is read-only by harness design.** Dispatched a 1500-word chunking-feasibility investigation to a Plan agent expecting it could save its deliverable to `.claude/plans/<file>.md`. It couldn't (Plan's tool list excludes Edit/Write/NotebookEdit). The report came back inline and I relayed via my own `Write` call. **Implication:** when an agent's output IS a written artifact, dispatch with `general-purpose`; `Plan` is for "think deeply and report inline." Reasoning-graph implication: capability-typed agent surfaces are useful, but the dispatch-time decision needs the deliverable-shape encoded (artifact-target vs inline-report) — otherwise the matchmaker picks wrong.

- **Truncated-agent resume gap.** A `general-purpose` agent finished its work but its final report got truncated mid-output. Attempted to resume by wrapping a `SendMessage` instruction in a new `Agent` call — that spawned a fresh agent with no memory of the prior run. The correct path is the `SendMessage` deferred tool loaded via `ToolSearch`. **Implication for the reasoning-graph fork:** any long-running graph operation that emits intermediate state needs a deterministic continuation handle — not just "spawn a new actor with the prior context as a prompt." The harness already has this primitive (`SendMessage` by agent ID), but it's not the discoverable path.

### Pre-deploy verification gap

- **v1 of the new edge function shipped with two HIGH-severity bugs** (UTF-8 multi-byte split in `atob().join('')`; no try/catch around reassembly). Smoke tests had used ASCII payloads exclusively — the bugs only surface on multi-byte content (Cyrillic, CJK, emoji — i.e. the very content the function exists to ship from RU testers). Code-review caught them post-deploy. **Implication for reasoning-graph:** any edge-function deploy pipeline should require at least one multi-byte test fixture in its acceptance set. The reasoning-graph fork's own deploy step should bake that in — and the rule should be embedded in the deploy primitive, not left as discipline.

### Drift-bait applied to `/graphiti why`

The `/graphiti why` command was bundling commit episodes into every response by default, and returned metadata-only (no code chunk), forcing the agent to grep afterwards. Both were drift-bait — *"the graph pushed everything it had instead of letting the agent pull scoped to the current task"* (`CLAUDE.md §4.6`).

Sharpened the command this session:
- **Default payload = minimum-scoped.** Top 1–3 entities + their short summaries + a code chunk extracted via `grep -n -B 1 -A 30` against the node's `attributes.source_file`. Skips commit episodes entirely.
- **Each axis is one flag.** `--include-commits` is opt-in, used only when the question shape is on the time-axis (file history, recent bug, perf regression). Future flags (`--include-callers`, `--include-rejected`, etc.) follow the same shape: one axis = one flag.
- **No `--exclude-X` flags.** Nothing is on by default that you'd want to turn off. Minimal-by-default is the contract.

**Primitive for the fork to bake in from day one:** the `query()` / `explain()` API surface must be axis-flagged, not "smart-default-that-bundles." The temptation to be helpful by including-more-context IS the drift-bait — surface area that ships with rich defaults trains agents to consume more than they need, which is exactly the pattern the reasoning-graph project rejects. The fork should ship a minimal default + composable flags from v0; retrofitting later is harder than baking it in.

Also: code-content stays in the filesystem; the graph stores the REFERENCE (file + line range) + the rationale (narrative episode) + the relationships (callers, imports, contains). Grep at query time. No eager caching of code bodies in the graph — staleness disappears as a problem because the source-of-truth is always the live file.

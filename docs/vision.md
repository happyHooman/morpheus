# Vision — what the mind will track, and who it serves

> Wide-horizon vision. Informs design choices; does not name a phase scope.
> Near-term work tackles deliberately narrow slices and grows toward this
> picture. The six mission capabilities (collect / structure / validate /
> attribute / judge relevance / manage conflicts) are the *verbs*. The
> categories below are the *nouns* those verbs act on.

---

## 1. Knowledge categories the mind tracks

The reasoning mind doesn't just retain free-form notes — it captures distinct kinds of project knowledge, each with its own structure and update cadence:

- **Project evolution history.** Git branches and commits as Episodes. The *why* a branch was cut, *why* a commit landed, what tradeoff was accepted at the time.
- **Project-specific knowledge.** UX framings, user expectations, use cases, terminology, domain/field knowledge, end-user perspective. Reference material that survives implementation churn.
- **Research findings.** External sources read while building the project: papers, articles, prior-art comparisons. Become Evidence on later Decisions.
- **File changes + reasoning.** For every meaningful diff, the *why* — not just the *what*. Investigation-ready trace from any current line of code back to the question that motivated it.
- **Production-ready features.** What works, how it works, how features compose with each other.
- **Features in development.** What's WIP, who owns it, what's blocking it.
- **Tries and fails.** What was attempted, why it failed, what to avoid repeating. The opposite of *"we don't talk about that one."*
- **Knowledge at multiple abstraction levels.** System architecture and shapes at one end; individual-implementation specifics at the other. The mind reasons across levels and surfaces the right altitude per question.
- **User perspectives and preferences.** Owner, users, operators — distinct viewpoints, captured separately, never collapsed.
- **Project rules / decisions / tech approaches.** The load-bearing constraints. Things that, when violated, indicate drift. The mind enforces these via the validation layer.

These map back to the [mission](seed.md) capabilities:

| Mission verb | Categories it most directly touches |
|---|---|
| Collect | All of them — every category is an ingestion target. |
| Structure | Knowledge-at-multiple-abstraction-levels, features and their relations, project rules. |
| Validate | Project rules, decisions, tech approaches, file changes + reasoning. |
| Attribute | User perspectives, tries-and-fails, file changes (who-decided-what), git history. |
| Judge relevance | Knowledge at multiple abstraction levels — return the right altitude per asker. |
| Manage conflicts | Decisions vs. rules, conflicting perspectives, supersession of tried-and-failed approaches. |

---

## 2. Capture surfaces (tooling implications)

The categories above become real only when tools actively capture them. Near-term plan: build capture *as each category needs to be addressable by a real query*, not all at once. Likely order:

- **Hooks (Git-side).** `post-commit` / `post-checkout` write commit Episodes with author, branch, touched files, and the commit-message body parsed for Decision/Justification candidates. Lifts the pattern proven in MLGameBot's commit episodes, into a Morpheus-installable hook.
- **Skills (agent-side).** Slash-commands like `/morpheus capture-decision`, `/morpheus capture-rule`, `/morpheus explain <X>` for in-session capture and recall. Installable per AI-tooling platform (the Graphify-style install matrix).
- **CLI subcommands.** `morpheus ask "<question>"` (free-form Q&A with answer synthesis on top of the current `query`), `morpheus capture commit <sha>`, `morpheus capture file <path>`. The CLI is the human-driven entry point; the hooks are the automatic one.
- **External integrations (deferred until a clear concrete win).**
  - **Jira (or equivalent).** Pull task tickets that name estimated plans + expected touched files; the mind compares expected vs. actual, surfaces scope drift. Auto-link tickets to commits/branches.
  - **GitHub.** PR descriptions and code-review comments as Episodes attributed to their authors.
  - Other code-host integrations follow the same shape.

Each integration is its own future plan. None of them belong in the current phase.

---

## 3. Audiences and usage models

### Single contributor (current dogfood)

- Reload context when picking up a sleeping part of the app.
- Ask free-form questions and get answers grounded in prior decisions, not generic LLM output.
- Stay honest about what's been tried and rejected — a personal memory the user can interrogate.

### Multi-team engineering (target horizon)

- One remote Morpheus MCP server shared within an org. Many engineers, many teams, one mind per project.
- Everyone contributes; project rules are *respected and aligned* via the mind's validation layer. Contributions that contradict load-bearing rules get a `Finding`, not a silent merge.
- New-engineer onboarding measured in hours, not weeks — the new engineer asks the mind, not the senior. Especially valuable on large codebases where the relevant context is scattered.
- Big start-boost on any new task: the mind surfaces what's already known, what's been tried, what's been rejected, and who's currently working on adjacent things.

The typed reasoning layer (Justification, Decision, Rule, Revision, Finding) is what makes this *safe* at team scale. Without it, a shared knowledge graph is just a worse Confluence. With it, the graph can:
- Refuse contributions that contradict load-bearing rules (or, more usefully, surface them as Findings for a human to triage).
- Show where two teams' beliefs diverge and which Decision is older.
- Explain *why* the project believes anything it believes — without forcing the asker to read the whole history.

Per the [drift-bait principle](seed.md) (`§4.6`), retrieval stays scoped: the mind does not *push* its full history into every agent's context. It answers questions, on demand, at the right altitude.

---

## 4. What this changes in the near-term plan

- **Phase 1B's typed nodes** (`Justification`, `Decision`, `Rule`, `Revision`, `Finding`) remain the next-up work. They are the load-bearing primitives every capture surface and every integration above will write into. **Building any capture tool before the typed nodes exist would write knowledge into a shape that can't be queried meaningfully.**
- **`morpheus ask`** joins the CLI roadmap as the headline free-form Q&A surface. It builds on the existing `morpheus query` (which returns top-K nodes/facts) by adding LLM synthesis grounded in the retrieved context. Lands in the same phase as the reasoning nodes, since "ask" answers are most useful when they can cite Justifications and Decisions.
- **Git hooks and Jira integration are deferred** until the typed nodes ship. They become genuinely valuable the moment a commit can ingest as both an Episode *and* a Justification — not before.
- **Multi-team / remote-server work is not a near-term scope.** It's a target audience the design must not foreclose. The drift-bait principle, group-id partitioning, and per-source attribution all already point in the right direction.

The order is: **typed nodes first → `morpheus ask` + targeted capture skills next → integrations after that → multi-team hardening last.** Each step makes the next one more valuable.

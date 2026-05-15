# Ideas — backlog for later exploration

> Append-only. Each entry is dated, headed by its idea title, and includes both the user's framing and a short structural sketch the project can return to. **These are not commitments and not Phase 1 work.** Entries here are explicitly held back until a future phase deliberately picks them up.

---

## 2026-05-15 — Hierarchical agent organization with role-scoped responses

### The idea (Master's framing)

> Any big project has not only a file structure but also a *component's structure*. The file structure might only partially reflect this. Any app is just a combination of how different components are being used at different levels. There is hierarchy everywhere, and consistency is kept only when things and rules are being kept simple.
>
> That is how people have been able to create great things so far: separation of concerns, and multiple workers specialized for different tasks, and there is hierarchy between them — who reports to whom. Many are executing minor work, others supervise a few workers, others supervise a few groups, and others supervise a big part of the project, and others supervise how the whole project is going.
>
> The smaller report to their immediate authority, and the command goes from greater authority to the immediate subordinates — *not* subordinates of subordinates. Even though there are multiple subordinates for each supervisor, each of them has their own task to focus on, *not* a collective mind. And that leads to order. Order is the base for anything great ever created.
>
> We are thinking of summoning different agents with different abilities, authority, concerns and tasks to work on. Morpheus should be able to know this, and provide responses depending on who is asking.

### What this implies for Morpheus

1. **Component structure is a first-class thing, separate from file structure.** The graph already has Entities and structural edges (`imports_from`, `contains`); component structure adds a higher-level overlay that names *responsibilities* and *boundaries*, not just code-level relations.
2. **Agents are not equal queriers.** A worker-level agent and a project-supervisor-level agent asking the same question should get different responses — same facts, different scope, different framing, different rejected alternatives surfaced. Morpheus is *role-aware* at the query surface.
3. **Strict chain of command.** Information flows up one level at a time; commands flow down one level at a time. No skip-level reads, no skip-level orders. This maps cleanly to a layered retrieval pattern in the graph: each agent's scope = the subgraph immediately above and below its level, never further.
4. **Each agent has *its own* task.** Not a collective mind. The graph should not merge what two agents at the same level are thinking; their decisions, justifications, and findings stay distinct nodes, linked but not collapsed.
5. **Order from separation of concerns.** The smallest, sharpest version: every agent has one task; every task has one supervisor; every supervisor has one upward report. Anywhere the structure violates this, the project has drifted.

### Open questions for the future phase that takes this on

- How does Morpheus represent **roles** in the graph? A new node type (`Role`)? A subtype of `Entity`? An attribute on `Decision`/`Rule` nodes? (Same constraint as `seed.md` §4.1 — start with the minimum.)
- What edge captures "this agent reports to that supervisor"? `reportsTo`? `subordinateOf`? Should it carry strength/scope metadata?
- How does `explain(factId)` behave under role-scoping? Does a worker's `explain()` stop at the layer above them (omitting the supervisor's reasoning) — and is that a feature, a default, or always-overridable?
- The **drift-bait principle** (`docs/seed.md` §4.6) reads strongly with this idea: surfacing skip-level context to a worker isn't just noise, it's a coupling violation that re-anchors the worker on responsibilities not theirs. Role scoping is partly an instance of drift-bait avoidance.
- How does Morpheus know *who is asking*? An MCP-call attribute? A signed identity? A self-declared role? The honesty of the answer depends on this.
- **Audit shape.** Every action by every agent should leave a `Decision` node (chosen option, considered alternatives, criterion, the supervisor under whose authority the choice was made). The supervisor can query their own subordinates' Decisions; cross-team queries require going up to the common supervisor.
- Multi-agent task decomposition is a *separate* concern from role-scoped responses. They overlap — but the first is about *who is given what work*, the second is about *what they're told when they ask*. Worth keeping them as distinct future-phase tickets.

### Why this isn't Phase 1

Phase 1 is reasoning-layer primitives (`Justification`, `Decision`, `Rule`, `Revision` types + `explain()`). Roles and authority are a layer that *sits on top of* those primitives and won't make sense until the primitives are in place. This entry exists so the idea is captured and queryable, not so it pulls forward.

Cross-references:
- [`seed.md`](seed.md) §4.1 (minimal node taxonomy), §4.4 (`explain()` surface), §4.6 (drift-bait principle).

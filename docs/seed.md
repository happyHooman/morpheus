# Reasoning Graph — project seed

> Seed doc for a future personal project. Captures Master's spark in his own
> words, plus a survey of what's already out there in the AI-memory-graph
> space (May 2026), the gap his project would occupy, and concrete first
> moves. Not a spec — a launchpad.

---

## 1. The spark (Master's words)

> Graphiti is good out of itself because it does facts deduplication and
> disambiguation and a kind of conflict resolution when the episode is
> created and ingested. But we can do more than that — and use my knowledge
> from the related project that used Graphiti as an inspiration but got
> further by using custom nodes and relations so that they can be used to
> track information, find the reasoning of some decisions, and so on.
>
> Basically what is inside the graph is no longer abstract and following no
> rules — but does that using our own specific rules for it which are
> embedded into nodes and relations, depend on them and their properties,
> but also provides backtracking capabilities so we know not only the
> *what*, but we can extract the *why* and the *how* from the graph.

The two new things relative to vanilla Graphiti:

1. **Embedded rules.** Nodes and relations carry constraints / behaviour
   that depend on their properties — the graph stops being a passive store
   and becomes an active substrate that enforces meaning.
2. **Backtracking on reasoning.** Every fact in the graph can be traced
   back to (a) the episodes that contributed evidence, (b) the rule(s) that
   derived it, and (c) the alternatives that were considered and rejected.
   "Why does the graph believe X?" becomes a first-class query.

---

## 2. The landscape (May 2026)

| System | What it gives you | Where it stops short |
|---|---|---|
| **Graphiti** (Zep / getzep) | Temporal KG with valid_at/invalid_at, dedup, disambiguation, conflict-resolution at ingest. JSON / text / message episodes. Built-in entity types + opt-in custom Pydantic types via the core lib. | Reasoning chains aren't first-class. No formal provenance edges from derived fact → justification. MCP server exposes only built-in types. Temporal model is "valid_at marker" — no automatic invalidation cascade. |
| **Cognee** (topoteretes/cognee) | OWL-grounded ontology + Pydantic-typed entities, 80% fuzzy match against OWL classes, URI canonicalisation, `ontology_valid` tag per node. Production-grade; >70 companies. ECL pipeline (Extract / Cognify / Load). | Doesn't appear to capture *decision rationale* or *rule applications* as first-class graph elements. No published explainability surface ("why does the graph believe X?"). |
| **Mem0g** (mem0.ai) | Entity extractor + relations generator + **conflict detector that runs pre-write**. Vector store alongside graph. Reports +1.5pp on multi-hop QA vs vector-only. | Conflicts are flagged, not resolved with traceable rationale. No structured rejection log. |
| **Kumiho** (Ranjan Kumar, 2026 — paper architecture) | Item / Revision / Tag-pointer split. Immutable revisions, mutable tags, supersession edges, AGM-postulate-conscious revision (K\*2, K\*5 enforced; K\*7/K\*8 acknowledged-unproven). Six-step audit traversal as the backtracking primitive. URI-addressed cross-agent references. Prospective indexing of hypothetical future scenarios at write time. | No public code. Open problems flagged honestly: extraction validation gap, graph bloat from append-only, consolidation lag in distributed setups. Decisions/rationale not the headline — provenance + revision are. |
| **Letta / MemGPT** | Self-editing memory hierarchies; agents revise their own context. | Not graph-shaped; not built around explainability. |
| **Mem0** | Memory layer with structured/unstructured separation; broad adoption. | Reasoning chains and rule-typed edges aren't a primary primitive. |
| **Neo4j Labs `agent-memory`** | Reference Neo4j-native memory implementation. | Plumbing, not opinionated about ontology or reasoning. |

### Older ideas worth knowing (still relevant)

- **Truth Maintenance Systems (TMS)** — Doyle (1979). Each derived fact
  carries a *justification* (list of antecedents + rule applied);
  contradictions trigger *dependency-directed backtracking* to find the
  minimal set of base assumptions to retract. Two flavours: **JTMS** (one
  consistent context at a time) and **ATMS** (de Kleer 1986 — multiple
  contexts in parallel, each tagged by its assumption set). Almost
  nobody implements TMS literally any more, but the *data shape* (a fact
  carries pointers to its supports) is the right mental model for what
  Master means by "the why and the how."
- **PROV-O** (W3C, 2013) — standard provenance ontology. `Entity`,
  `Activity`, `Agent` + edges like `wasGeneratedBy`, `wasDerivedFrom`,
  `wasInformedBy`. Overkill for an MVP, but if you ever want to *export*
  reasoning traces interoperably, PROV-O is the lingua franca.
- **Argumentation frameworks** (Dung 1995) — model claims with attack
  relationships; computes which subsets of claims survive. Maps cleanly
  to "rejected alternatives" tracking.
- **Datalog with provenance** — academic line of work where every derived
  tuple is annotated with the proof tree that produced it. Closest
  existing thing to "give me the WHY for this fact." See also
  *semiring provenance* (Green / Karvounarakis / Tannen).

---

## 3. Where Master's project sits

Pencil-sketch of the gap:

```
                shallow on reasoning   ⟶   deep on reasoning
production      ┌──────────────┬──────────────────────────┐
ready           │  Graphiti    │  Cognee                  │
                │              │                          │
                ├──────────────┼──────────────────────────┤
paper /         │              │  Kumiho                  │
prototype       │              │  classical TMS           │
                └──────────────┴──────────────────────────┘
                                          ↑
                                          │
                                          └── target zone:
                                              production-ish + decision rationale
                                              + first-class rule provenance
```

The angle Master's prior project earned (custom nodes + relations carrying
their own rules) plus an explicit *decision/rationale layer* (which neither
Cognee nor Kumiho headline) is a real, defensible contribution.

---

## 4. Design directions worth pursuing

### 4.1 Node taxonomy with a reasoning layer

Beyond `Entity` + `Episode`, add at least:

- **Justification** — every derived fact links to one. A Justification
  carries: ordered list of supporting facts (`supportedBy`), the rule that
  fired (`appliedRule`), the episode that triggered it (`triggeredBy`),
  and a confidence/strength annotation. TMS-shaped.
- **Decision** — when an agent (or rule, or human curator) chose between
  alternatives. Carries: the chosen option (`selected`), rejected
  alternatives (`considered`), the criterion (`appliedCriterion`), and a
  free-text rationale. Distinct from Justification because Decisions are
  agentic; Justifications are inferential.
- **Rule** — first-class declarative entity. A Rule has a precondition
  pattern (graph subgraph), a postcondition (what it asserts), and a
  source (who authored it / which episode introduced it). Lets you query
  "which rules have ever fired on facts about X?"
- **Revision** — Kumiho-style immutable snapshot of a belief. Tag pointers
  move; revisions don't. Backtracking is just walking `supersededBy`
  edges.

### 4.2 Edge taxonomy worth declaring upfront

- `derivedFrom` (fact → Justification)
- `supportedBy` (Justification → fact, ordered)
- `triggeredBy` (Justification → Episode)
- `appliedRule` (Justification → Rule)
- `supersededBy` (Revision → Revision)
- `tagPointsTo` (Tag → Revision)
- `chosenOver` (Decision.selected → Decision.considered, weighted with rationale)
- `wasAuthoredBy` (Rule → Agent | Episode)

Avoid the trap of starting with twenty edge types — Kumiho explicitly
warns about graph bloat, and Zep's docs cap custom types around 10 for
extraction quality. Start with 5–6, add when you hit a query you can't
answer.

### 4.3 Constrained extraction

Largest open risk per Kumiho: "the entire formal correctness argument
assumes clean input." Mitigations to evaluate early:

- **Structured output at extraction time** — Outlines, Instructor, or
  provider-native JSON schema constraints. Don't accept free-form LLM
  output that *might* parse — force it to.
- **Two-pass with quarantine** — extractor proposes, validator (smaller
  rule-bound model OR symbolic checker) approves. Rejected items land in
  a `quarantine` namespace that humans review weekly.
- **Confidence-weighted edges** — every assertion carries a 0–1 score;
  conflict resolution preferentially keeps high-confidence edges.

### 4.4 The "why does the graph believe X" query surface

This is the headline feature. Concretely:

- `explain(factId)` → walks `derivedFrom` → `supportedBy` recursively
  until base facts (Episodes), produces a tree of Justifications →
  rendered as either a graph diagram or a linear narrative.
- `whatIf(removeEpisode)` → counterfactual: which derived facts lose all
  justifications if a given episode is retracted? (Classical TMS
  answers this.)
- `whyChosen(decisionId)` → returns the chosen option, the alternatives,
  the criterion, the agent.

If the project builds nothing else from this list, build `explain` —
that's where it differentiates from every existing memory system.

### 4.5 Append-only with revision pointers

Kumiho's pattern is sound: never mutate, always append, move tags. The
graph-bloat risk is real; budget for compaction (a periodic job that
prunes Revisions older than N with no live referrers and no
`supportedBy` outbound edges).

### 4.6 Query-on-demand, never auto-loaded — the drift-bait principle

> Master's framing (2026-05-05): *"keeping a log of what changed and why
> is important. but that should not be loaded in the context every time,
> as that's exactly the food that attracts drift bait bugs."*

Recording reasoning is the whole point of the graph. **Loading recorded
reasoning back into the prompt by default is the failure mode.** When an
agent's context window contains the full history of what was decided,
revised, rejected, and superseded, the model starts hedging back toward
revised-away conclusions, anchors on stale framings, and drifts toward
deleted patterns. This is what we're calling **drift bait**: residual
context — old explanations, "this used to be" notes, justification
trails — that pulls current behaviour back toward removed or superseded
state.

The graph's job is to *retain*, not to *push*. Retrieval is the agent's
job, on demand, scoped to the current task.

Concrete consequences for v0:

- **`explain(factId)` returns a tree, not a stream of context.** The
  caller decides whether to flatten and inject; by default the agent
  sees only the current value and a pointer to the explanation.
- **Revisions and superseded edges are queryable, not loaded.** A query
  like `whatChanged(factId)` walks `supersededBy`, but only when asked.
  Default reads return current state only.
- **Decision nodes are referenced by id from the active context, never
  inlined.** Inlining the rejected alternatives back into the agent's
  prompt re-tempts the model toward them.
- **Justification chains stay collapsed unless an `explain` call is
  made.** The mere presence of an old `supportedBy` edge in context can
  re-anchor extraction.
- **Anti-pattern to avoid in the storage UX:** auto-summarising "here's
  everything we've ever revised on this topic" into the working memory.
  That's the steel-trap version of drift bait.

This principle is also why the project should *not* present itself as a
"context window booster" or "memory injector." The graph is a reasoning
substrate the agent queries, not a transcript it inhales. The framing
matters because it forces the API design honest — `query()` and
`explain()` first, never `dumpAll()`.

---

## 5. Hard problems to expect (eyes open)

1. **Extraction–schema impedance.** LLMs propose; rules demand. The
   reconciliation layer is where most of the engineering effort goes,
   not the schema design itself.
2. **Rule expressiveness ↔ tractability.** Datalog is decidable and fast;
   first-order logic is expressive and undecidable. The middle ground
   (e.g., constrained Cypher patterns + simple deductive rules) is
   probably right but you'll be tempted to add power.
3. **Decision capture honesty.** Agents (LLM or otherwise) confabulate
   reasons. A Decision node populated by "ask the agent why it picked X"
   risks recording rationalisation, not actual decision criteria. Worth
   a design pass: do you record the criteria *the agent was given*, or
   the criteria *it claims it used*? They're not the same.
4. **Graph bloat under append-only.** Already flagged by Kumiho. Need a
   compaction story before Day 90.
5. **Iterated revision soundness.** AGM K\*7 / K\*8 across sessions is
   formally hard. Kumiho leaves it open. Decide early whether you care
   about formal guarantees or pragmatic monotonicity.
6. **Multi-agent consistency windows.** If multiple agents write
   concurrently, your graph diverges from any single agent's view of
   truth. Either lock, or accept eventual consistency with explicit
   "as-of" reads.
7. **The deduplication problem doesn't go away.** Custom types help —
   they constrain the extractor — but two episodes can still describe
   the same Entity with different surface forms. Cognee's URI
   canonicalisation + fuzzy matching is a sane reference.

---

## 6. First moves (week 1 sketch)

- Stand up Graphiti core lib (not the MCP server) so you can pass custom
  Pydantic entity / edge types directly to `add_episode`.
- Define the minimal six: `Entity`, `Episode`, `Justification`,
  `Decision`, `Rule`, `Revision`. No more, until you find a query that
  requires more.
- Write three example episodes by hand (not via LLM extraction yet) that
  exercise: a fact derived from two prior facts via a rule; a decision
  choosing between alternatives; a revision that supersedes an earlier
  belief.
- Implement `explain(factId)` first. It's the smallest thing that proves
  the architecture earns its keep.
- Only after that works on hand-crafted data, plug in LLM extraction
  with structured-output constraints.

---

## 7. Open questions to settle before week 2

1. **Backend.** Neo4j (mature, expensive at scale), Kuzu (embedded, new,
   what Mem0g picked in Sep 2025), FalkorDB (Redis-native graph, used by
   the Graphiti MCP), or stay with whatever Graphiti core defaults to?
2. **Storage of Revisions.** Inline as graph nodes (Kumiho's choice) or
   as a separate event log with graph projections? The first is simpler;
   the second scales further.
3. **Where do Rules live?** As graph nodes (introspectable, queryable)
   or as code (faster, less reflective)? Probably both — code for hot
   path, graph for audit and discovery.
4. **Ontology authoring UX.** Pydantic classes are fine for engineers;
   not for domain experts. Do you ever want a GUI / DSL?
5. **What's the v1 use case?** Pick one — agent memory for coding
   assistants, scientific lab notebook, legal contract reasoning,
   debugging traces of distributed systems. The schema bends differently
   for each. v0 should be the one Master will dogfood himself.

---

## 8. Reading list

Direct sources that informed this seed (verify before citing in any
public material — links rot):

- **Graphiti / Zep**
  - https://help.getzep.com/graphiti/getting-started/welcome
  - https://help.getzep.com/graphiti/core-concepts/custom-entity-and-edge-types
  - https://github.com/getzep/graphiti
- **Cognee**
  - https://www.cognee.ai/
  - https://www.cognee.ai/blog/deep-dives/grounding-ai-memory
  - https://www.cognee.ai/blog/deep-dives/ontology-ai-memory
  - https://github.com/topoteretes/cognee
- **Kumiho architecture**
  - https://ranjankumar.in/why-agent-memory-needs-a-graph-lessons-from-the-kumiho-architecture
- **Survey & state-of-the-field**
  - https://mem0.ai/blog/state-of-ai-agent-memory-2026
  - https://mem0.ai/blog/graph-memory-solutions-ai-agents
  - https://arxiv.org/html/2602.05665v1 — "Graph-based Agent Memory: Taxonomy, Techniques, and Applications"
- **Truth Maintenance Systems (background)**
  - https://en.wikipedia.org/wiki/Truth_maintenance_systems
  - Doyle, "A Truth Maintenance System," AI Journal 12(3), 1979
  - de Kleer, "An Assumption-Based TMS," AI Journal 28(2), 1986
- **Provenance**
  - W3C PROV-O — https://www.w3.org/TR/prov-o/
  - Green, Karvounarakis, Tannen, "Provenance Semirings," PODS 2007
- **Argumentation**
  - Dung, "On the acceptability of arguments and its fundamental role in
    nonmonotonic reasoning, logic programming and n-person games," AI
    Journal 77(2), 1995

---

## 9. Footnote — what only you know

The "related project that used Graphiti as inspiration and got further"
in your head isn't represented anywhere in this doc — I haven't seen its
code or its lessons. Whatever survived contact with reality there should
be the *first* thing you write into v0 of this project, ahead of
anything in section 4. The literature gives you a frame; that prior
project gives you the actual gear.

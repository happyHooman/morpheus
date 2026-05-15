"""`morpheus query "<question>"` — Graphify-absorbed: answer-shaped graph query.

v0 implementation is search-only: runs an embedding-backed hybrid search via
``Graphiti.search_`` and returns the top-K results with the facts that
contributed. No LLM-generated answer synthesis in v0 — that's deferred so
this command doesn't double the provider cost surface. Callers can pipe the
output into their own LLM if they want a generated answer.
"""

from __future__ import annotations

import click

from graphiti_core.search.search_config_recipes import COMBINED_HYBRID_SEARCH_RRF

from morpheus_cli.cli import async_command
from morpheus_cli.client import graphiti_session
from morpheus_cli.output import emit


@click.command('query', help='Ask a question against the graph; returns top-K nodes + facts.')
@click.argument('question')
@click.option('--max-results', '-n', type=int, default=5, show_default=True)
@click.pass_obj
@async_command
async def query(obj: dict, question: str, max_results: int) -> None:
    config = obj['build_config']()
    search_config = COMBINED_HYBRID_SEARCH_RRF.model_copy(deep=True)
    search_config.limit = max_results

    async with graphiti_session(config) as client:
        results = await client.search_(
            query=question,
            config=search_config,
            group_ids=[config.group_id],
        )

    nodes_payload = [
        {
            'uuid': str(n.uuid),
            'name': n.name,
            'summary': n.summary,
        }
        for n in results.nodes
    ]
    facts_payload = [
        {
            'uuid': str(e.uuid),
            'fact': e.fact,
        }
        for e in results.edges
    ]

    payload = {
        'question': question,
        'nodes': nodes_payload,
        'facts': facts_payload,
    }

    human_lines = [f'query: {question}', '']
    if nodes_payload:
        human_lines.append(f'top {len(nodes_payload)} node(s):')
        for n in nodes_payload:
            human_lines.append(f'  - {n["name"]}: {n["summary"][:160]}')
        human_lines.append('')
    if facts_payload:
        human_lines.append(f'supporting facts ({len(facts_payload)}):')
        for f in facts_payload:
            human_lines.append(f'  - {f["fact"]}')
    if not nodes_payload and not facts_payload:
        human_lines.append(f'no results in group {config.group_id}')

    emit(payload, human='\n'.join(human_lines))

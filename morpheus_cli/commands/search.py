"""`morpheus search-nodes` and `morpheus search-facts`."""

from __future__ import annotations

import click

from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF

from morpheus_cli.cli import async_command
from morpheus_cli.client import graphiti_session
from morpheus_cli.output import emit


@click.command('search-nodes', help='Search entity nodes by query (MCP search_nodes parity).')
@click.argument('query')
@click.option('--max-results', '-n', type=int, default=10, show_default=True)
@click.pass_obj
@async_command
async def search_nodes(obj: dict, query: str, max_results: int) -> None:
    config = obj['build_config']()
    search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
    search_config.limit = max_results

    async with graphiti_session(config) as client:
        results = await client.search_(
            query=query,
            config=search_config,
            group_ids=[config.group_id],
        )

    nodes_payload = [
        {
            'uuid': str(n.uuid),
            'name': n.name,
            'labels': list(n.labels) if n.labels else [],
            'summary': n.summary,
        }
        for n in results.nodes
    ]
    emit(
        {'count': len(nodes_payload), 'nodes': nodes_payload},
        human=(
            f'found {len(nodes_payload)} node(s) for "{query}"\n'
            + '\n'.join(
                f'  - {n["name"]} ({n["uuid"][:8]})\n    {n["summary"][:120]}'
                for n in nodes_payload
            )
        )
        if nodes_payload
        else f'no nodes matched "{query}" in group {config.group_id}',
    )


@click.command('search-facts', help='Search facts (entity edges) by query (MCP search_memory_facts parity).')
@click.argument('query')
@click.option('--max-results', '-n', type=int, default=10, show_default=True)
@click.pass_obj
@async_command
async def search_facts(obj: dict, query: str, max_results: int) -> None:
    config = obj['build_config']()

    async with graphiti_session(config) as client:
        edges = await client.search(
            query=query,
            group_ids=[config.group_id],
            num_results=max_results,
        )

    edges_payload = [
        {
            'uuid': str(e.uuid),
            'fact': e.fact,
            'source_node_uuid': str(e.source_node_uuid),
            'target_node_uuid': str(e.target_node_uuid),
            'valid_at': e.valid_at.isoformat() if e.valid_at else None,
            'invalid_at': e.invalid_at.isoformat() if e.invalid_at else None,
        }
        for e in edges
    ]
    emit(
        {'count': len(edges_payload), 'facts': edges_payload},
        human=(
            f'found {len(edges_payload)} fact(s) for "{query}"\n'
            + '\n'.join(f'  - {e["fact"]}' for e in edges_payload)
        )
        if edges_payload
        else f'no facts matched "{query}" in group {config.group_id}',
    )

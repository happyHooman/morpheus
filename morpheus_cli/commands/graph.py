"""`morpheus clear` — destructively clear the graph for the current group only."""

from __future__ import annotations

import click

from morpheus_cli.cli import async_command
from morpheus_cli.client import graphiti_session
from morpheus_cli.output import emit


@click.command(
    'clear',
    help='Delete all episodes, nodes, and edges in the current group. '
    'Requires --yes. Operates strictly within --group-id; never global.',
)
@click.option('--yes', is_flag=True, required=True, help='Confirmation flag — required.')
@click.pass_obj
@async_command
async def clear(obj: dict, yes: bool) -> None:
    # ``required=True`` on --yes means click already enforced presence; keep
    # the parameter to make the destructive nature explicit at the call site.
    _ = yes
    config = obj['build_config']()
    async with graphiti_session(config) as client:
        # Strict group-scoped delete via Cypher. We do NOT call
        # Graphiti.clear_graph() because that drops indices and constraints
        # globally — heavier and would interfere with other groups sharing
        # the same Neo4j instance.
        delete_queries = [
            'MATCH (n {group_id: $group_id}) DETACH DELETE n',
        ]
        for q in delete_queries:
            await client.driver.execute_query(q, group_id=config.group_id)

    emit(
        {'cleared_group_id': config.group_id},
        human=f'cleared all nodes/edges/episodes in group {config.group_id}',
    )

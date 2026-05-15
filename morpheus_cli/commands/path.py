"""`morpheus path <A> <B>` — Graphify-absorbed: shortest path between two named nodes.

Uses Neo4j's ``shortestPath`` over the ``RELATES_TO`` edge type. If multiple
nodes share a name, picks the most-connected (highest degree) one on each
side.
"""

from __future__ import annotations

import click

from morpheus_cli.cli import async_command
from morpheus_cli.client import graphiti_session
from morpheus_cli.output import emit


_PATH_CYPHER = """
MATCH (a:Entity {group_id: $group_id, name: $a_name})
WITH a, COUNT { (a)-[:RELATES_TO]-() } AS a_deg
ORDER BY a_deg DESC
LIMIT 1
MATCH (b:Entity {group_id: $group_id, name: $b_name})
WITH a, b, COUNT { (b)-[:RELATES_TO]-() } AS b_deg
ORDER BY b_deg DESC
LIMIT 1
MATCH p = shortestPath((a)-[:RELATES_TO*..10]-(b))
RETURN [n IN nodes(p) | {uuid: n.uuid, name: n.name}] AS nodes,
       [r IN relationships(p) | r.fact] AS facts
"""


@click.command('path', help='Find the shortest path between two named nodes.')
@click.argument('a_name')
@click.argument('b_name')
@click.pass_obj
@async_command
async def path(obj: dict, a_name: str, b_name: str) -> None:
    config = obj['build_config']()

    async with graphiti_session(config) as client:
        records, *_ = await client.driver.execute_query(
            _PATH_CYPHER,
            group_id=config.group_id,
            a_name=a_name,
            b_name=b_name,
        )

    if not records:
        emit(
            {'found': False, 'a': a_name, 'b': b_name},
            human=f'no path between "{a_name}" and "{b_name}" in group {config.group_id} (max depth 10)',
        )
        return

    rec = records[0]
    nodes = rec.get('nodes') or []
    facts = rec.get('facts') or []

    payload = {
        'found': True,
        'length': len(facts),
        'nodes': nodes,
        'facts': facts,
    }

    human_lines = [f'shortest path {a_name} → {b_name}: {len(facts)} hop(s)']
    for i, node in enumerate(nodes):
        human_lines.append(f'  {node["name"]}')
        if i < len(facts):
            human_lines.append(f'    ↓ {facts[i]}')
    emit(payload, human='\n'.join(human_lines))

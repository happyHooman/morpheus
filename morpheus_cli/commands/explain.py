"""`morpheus explain <node>` — Graphify-absorbed: plain-language node summary.

Finds a node by name in the current group, fetches its direct neighbours
via a single Cypher query, and prints both the node's summary and the
facts on its incoming/outgoing edges.
"""

from __future__ import annotations

import click

from morpheus_cli.cli import async_command
from morpheus_cli.client import graphiti_session
from morpheus_cli.output import emit


_NODE_AND_NEIGHBOURS_CYPHER = """
MATCH (n:Entity {group_id: $group_id, name: $name})
OPTIONAL MATCH (n)-[r_out:RELATES_TO]->(m_out:Entity {group_id: $group_id})
OPTIONAL MATCH (m_in:Entity {group_id: $group_id})-[r_in:RELATES_TO]->(n)
RETURN n.uuid AS uuid, n.name AS name, n.summary AS summary, labels(n) AS labels,
       collect(DISTINCT {fact: r_out.fact, target: m_out.name}) AS outgoing,
       collect(DISTINCT {fact: r_in.fact, source: m_in.name})  AS incoming
LIMIT 1
"""


@click.command('explain', help='Explain a node by name: its summary plus direct neighbours.')
@click.argument('node_name')
@click.pass_obj
@async_command
async def explain(obj: dict, node_name: str) -> None:
    config = obj['build_config']()

    async with graphiti_session(config) as client:
        records, *_ = await client.driver.execute_query(
            _NODE_AND_NEIGHBOURS_CYPHER,
            group_id=config.group_id,
            name=node_name,
        )

    if not records:
        emit(
            {'found': False, 'name': node_name, 'group_id': config.group_id},
            human=f'no node named "{node_name}" in group {config.group_id}',
        )
        return

    rec = records[0]
    outgoing = [o for o in rec.get('outgoing', []) if o.get('fact')]
    incoming = [i for i in rec.get('incoming', []) if i.get('fact')]

    payload = {
        'found': True,
        'uuid': rec['uuid'],
        'name': rec['name'],
        'labels': list(rec.get('labels') or []),
        'summary': rec.get('summary') or '',
        'outgoing': outgoing,
        'incoming': incoming,
    }

    human_lines = [
        f'{payload["name"]}  ({payload["uuid"][:8]})',
        f'  labels: {", ".join(payload["labels"]) or "(none)"}',
    ]
    if payload['summary']:
        human_lines.append('')
        human_lines.append(payload['summary'])
    if outgoing:
        human_lines.append('')
        human_lines.append(f'outgoing ({len(outgoing)}):')
        human_lines.extend(f'  → {o["target"]}: {o["fact"]}' for o in outgoing)
    if incoming:
        human_lines.append('')
        human_lines.append(f'incoming ({len(incoming)}):')
        human_lines.extend(f'  ← {i["source"]}: {i["fact"]}' for i in incoming)

    emit(payload, human='\n'.join(human_lines))

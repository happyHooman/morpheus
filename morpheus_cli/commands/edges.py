"""`morpheus get-edge` and `morpheus delete-edge`."""

from __future__ import annotations

import click

from graphiti_core.edges import EntityEdge

from morpheus_cli.cli import async_command
from morpheus_cli.client import graphiti_session
from morpheus_cli.output import emit


@click.command('get-edge', help='Fetch a single entity edge by UUID (MCP get_entity_edge parity).')
@click.argument('uuid_arg')
@click.pass_obj
@async_command
async def get_edge(obj: dict, uuid_arg: str) -> None:
    config = obj['build_config']()
    async with graphiti_session(config) as client:
        edge = await EntityEdge.get_by_uuid(driver=client.driver, uuid=uuid_arg)

    payload = {
        'uuid': str(edge.uuid),
        'fact': edge.fact,
        'source_node_uuid': str(edge.source_node_uuid),
        'target_node_uuid': str(edge.target_node_uuid),
        'group_id': edge.group_id,
        'valid_at': edge.valid_at.isoformat() if edge.valid_at else None,
        'invalid_at': edge.invalid_at.isoformat() if edge.invalid_at else None,
        'episodes': [str(u) for u in (edge.episodes or [])],
    }
    emit(
        payload,
        human=(
            f'edge {payload["uuid"]}\n'
            f'  fact:   {payload["fact"]}\n'
            f'  source: {payload["source_node_uuid"]}\n'
            f'  target: {payload["target_node_uuid"]}\n'
            f'  group:  {payload["group_id"]}'
        ),
    )


@click.command('delete-edge', help='Delete an entity edge by UUID (MCP delete_entity_edge parity).')
@click.argument('uuid_arg')
@click.option('--yes', is_flag=True, help='Skip the confirmation prompt.')
@click.pass_obj
@async_command
async def delete_edge(obj: dict, uuid_arg: str, yes: bool) -> None:
    if not yes:
        click.confirm(f'Delete edge {uuid_arg}? This cannot be undone.', abort=True)
    config = obj['build_config']()
    async with graphiti_session(config) as client:
        edge = await EntityEdge.get_by_uuid(driver=client.driver, uuid=uuid_arg)
        await edge.delete(client.driver)
    emit({'deleted_uuid': uuid_arg}, human=f'deleted edge {uuid_arg}')

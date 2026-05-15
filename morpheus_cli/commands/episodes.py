"""`morpheus episodes` (list) and `morpheus delete-episode`."""

from __future__ import annotations

import click

from graphiti_core.nodes import EpisodicNode

from morpheus_cli.cli import async_command
from morpheus_cli.client import graphiti_session
from morpheus_cli.output import emit


@click.command('episodes', help='List recent episodes in the group (MCP get_episodes parity).')
@click.option('--limit', '-n', type=int, default=10, show_default=True)
@click.pass_obj
@async_command
async def episodes(obj: dict, limit: int) -> None:
    config = obj['build_config']()
    async with graphiti_session(config) as client:
        eps = await EpisodicNode.get_by_group_ids(
            driver=client.driver,
            group_ids=[config.group_id],
            limit=limit,
        )

    payload = [
        {
            'uuid': str(e.uuid),
            'name': e.name,
            'source': e.source.value if hasattr(e.source, 'value') else str(e.source),
            'source_description': e.source_description,
            'created_at': e.created_at.isoformat() if e.created_at else None,
            'valid_at': e.valid_at.isoformat() if e.valid_at else None,
        }
        for e in eps
    ]
    emit(
        {'count': len(payload), 'episodes': payload},
        human=(
            f'{len(payload)} episode(s) in group {config.group_id}\n'
            + '\n'.join(
                f'  - {e["uuid"][:8]}  {e["name"]}  ({e["created_at"] or "?"})'
                for e in payload
            )
        )
        if payload
        else f'no episodes in group {config.group_id}',
    )


@click.command('delete-episode', help='Delete an episode by UUID (MCP delete_episode parity).')
@click.argument('uuid_arg')
@click.option('--yes', is_flag=True, help='Skip the confirmation prompt.')
@click.pass_obj
@async_command
async def delete_episode(obj: dict, uuid_arg: str, yes: bool) -> None:
    if not yes:
        click.confirm(f'Delete episode {uuid_arg}? This cannot be undone.', abort=True)
    config = obj['build_config']()
    async with graphiti_session(config) as client:
        await client.remove_episode(uuid_arg)
    emit({'deleted_uuid': uuid_arg}, human=f'deleted episode {uuid_arg}')

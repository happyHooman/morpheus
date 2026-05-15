"""`morpheus status` — health check on Neo4j + provider resolution."""

from __future__ import annotations

import click

from morpheus_cli.cli import async_command
from morpheus_cli.client import graphiti_session
from morpheus_cli.llm import resolve_provider
from morpheus_cli.output import emit


@click.command('status', help='Check Neo4j connectivity and LLM provider resolution.')
@click.pass_obj
@async_command
async def status(obj: dict) -> None:
    config = obj['build_config']()
    # Resolve provider eagerly so we surface key-missing errors as part of status.
    provider = resolve_provider(config.provider)
    async with graphiti_session(config) as client:
        # Trivial driver round-trip to confirm the connection is live.
        records, *_ = await client.driver.execute_query('RETURN 1 AS ok')
        ok = bool(records) and records[0].get('ok') == 1

    result = {
        'status': 'ok' if ok else 'error',
        'group_id': config.group_id,
        'provider': provider,
        'neo4j_uri': config.neo4j_uri,
    }
    emit(
        result,
        human=(
            f'status:    {result["status"]}\n'
            f'group_id:  {result["group_id"]}\n'
            f'provider:  {result["provider"]}\n'
            f'neo4j_uri: {result["neo4j_uri"]}'
        ),
    )

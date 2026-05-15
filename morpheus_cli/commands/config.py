"""`morpheus config` — show the resolved configuration."""

from __future__ import annotations

import click

from morpheus_cli.llm import detect_provider
from morpheus_cli.output import emit


@click.command('config', help='Show resolved configuration (group_id, neo4j, provider).')
@click.pass_obj
def config(obj: dict) -> None:
    # build_config() raises if group_id is unset; do that translation here
    # so the error message is uniform with the rest of the CLI.
    cfg = obj['build_config']()
    detected_or_set = cfg.provider or detect_provider()

    payload = {
        'group_id': cfg.group_id,
        'neo4j_uri': cfg.neo4j_uri,
        'neo4j_user': cfg.neo4j_user,
        'neo4j_password_set': bool(cfg.neo4j_password),
        'provider_override': cfg.provider,
        'provider_resolved': detected_or_set,
    }
    emit(
        payload,
        human=(
            f'group_id:           {payload["group_id"]}\n'
            f'neo4j_uri:          {payload["neo4j_uri"]}\n'
            f'neo4j_user:         {payload["neo4j_user"]}\n'
            f'neo4j_password:     {"<set>" if payload["neo4j_password_set"] else "<unset>"}\n'
            f'provider_override:  {payload["provider_override"] or "<auto-detect>"}\n'
            f'provider_resolved:  {payload["provider_resolved"] or "<none>"}'
        ),
    )

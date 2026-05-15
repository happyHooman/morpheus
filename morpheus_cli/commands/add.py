"""`morpheus add` and `morpheus add-bulk` — episode ingestion commands."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

from graphiti_core.nodes import EpisodeType
from graphiti_core.utils.bulk_utils import RawEpisode

from morpheus_cli.cli import async_command
from morpheus_cli.client import graphiti_session
from morpheus_cli.output import emit


_SOURCE_CHOICES = ['text', 'json', 'message']


def _episode_type(source: str) -> EpisodeType:
    return EpisodeType[source]


@click.command('add', help='Add a single episode to the graph (MCP add_memory parity).')
@click.argument('name')
@click.option(
    '--body',
    default=None,
    help='Episode body. If omitted, the body is read from stdin.',
)
@click.option(
    '--source',
    type=click.Choice(_SOURCE_CHOICES, case_sensitive=False),
    default='text',
    show_default=True,
    help='Episode source type.',
)
@click.option(
    '--source-description',
    default='',
    help='Free-text description of the episode source.',
)
@click.pass_obj
@async_command
async def add(
    obj: dict,
    name: str,
    body: str | None,
    source: str,
    source_description: str,
) -> None:
    if body is None:
        body = sys.stdin.read()
    if not body.strip():
        raise click.UsageError('Empty episode body. Pass --body or pipe content on stdin.')

    config = obj['build_config']()
    reference_time = datetime.now(timezone.utc)

    async with graphiti_session(config) as client:
        result = await client.add_episode(
            name=name,
            episode_body=body,
            source_description=source_description,
            reference_time=reference_time,
            source=_episode_type(source),
            group_id=config.group_id,
        )

    episode = result.episode
    payload = {
        'episode_uuid': str(episode.uuid),
        'name': episode.name,
        'group_id': episode.group_id,
        'reference_time': reference_time.isoformat(),
        'nodes_created': len(result.nodes),
        'edges_created': len(result.edges),
    }
    emit(
        payload,
        human=(
            f'added episode {payload["episode_uuid"]}\n'
            f'  name:      {payload["name"]}\n'
            f'  group_id:  {payload["group_id"]}\n'
            f'  nodes:     {payload["nodes_created"]}\n'
            f'  edges:     {payload["edges_created"]}'
        ),
    )


@click.command('add-bulk', help='Bulk-add episodes from a JSONL file (CLI-only; no MCP parity).')
@click.option(
    '--file',
    '-f',
    'file_path',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help='Path to a JSONL file. Each line is one episode object with keys: '
    'name, content, source (text|json|message), source_description, '
    'reference_time (ISO 8601; defaults to now), uuid (optional).',
)
@click.pass_obj
@async_command
async def add_bulk(obj: dict, file_path: Path) -> None:
    raw_episodes: list[RawEpisode] = []
    with file_path.open() as f:
        for line_num, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj_dict = json.loads(stripped)
            except json.JSONDecodeError as e:
                raise click.UsageError(f'Invalid JSON on line {line_num} of {file_path}: {e}') from e

            reference_time_raw = obj_dict.get('reference_time')
            reference_time = (
                datetime.fromisoformat(reference_time_raw)
                if reference_time_raw
                else datetime.now(timezone.utc)
            )
            source_name = obj_dict.get('source', 'text')
            raw_episodes.append(
                RawEpisode(
                    name=obj_dict['name'],
                    content=obj_dict['content'],
                    source_description=obj_dict.get('source_description', ''),
                    source=_episode_type(source_name),
                    reference_time=reference_time,
                    uuid=obj_dict.get('uuid'),
                )
            )

    if not raw_episodes:
        raise click.UsageError(f'No episodes found in {file_path}.')

    config = obj['build_config']()

    async with graphiti_session(config) as client:
        result = await client.add_episode_bulk(
            bulk_episodes=raw_episodes,
            group_id=config.group_id,
        )

    payload = {
        'episodes_ingested': len(result.episodes),
        'episode_uuids': [str(ep.uuid) for ep in result.episodes],
        'nodes_created': len(result.nodes),
        'edges_created': len(result.edges),
        'group_id': config.group_id,
    }
    emit(
        payload,
        human=(
            f'bulk-added {payload["episodes_ingested"]} episodes to group {payload["group_id"]}\n'
            f'  nodes: {payload["nodes_created"]}, edges: {payload["edges_created"]}\n'
            + '\n'.join(f'  - {u}' for u in payload['episode_uuids'])
        ),
    )

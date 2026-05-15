"""Root Click group for the Morpheus CLI."""

from __future__ import annotations

import asyncio
import functools
from typing import Any, Callable

import click

from morpheus_cli import __version__
from morpheus_cli.config import MissingGroupIdError, load_config
from morpheus_cli.llm import NoProviderConfiguredError
from morpheus_cli.output import set_json_mode


def async_command(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Decorate a click command so its async body runs under asyncio.run."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(fn(*args, **kwargs))

    return wrapper


def _build_config(ctx: click.Context) -> Any:
    """Translate config-resolution exceptions into click UsageError."""
    try:
        return load_config(
            group_id=ctx.obj.get('group_id'),
            provider=ctx.obj.get('provider'),
        )
    except MissingGroupIdError as e:
        raise click.UsageError(str(e)) from e
    except NoProviderConfiguredError as e:
        raise click.UsageError(str(e)) from e


# Pass this to commands via @click.pass_obj — they receive the ctx.obj dict
# and call _build_config(ctx) at the moment they need a resolved config.
# This deferred resolution keeps `--help` working even when env vars are
# unset (so `morpheus --help` doesn't error on a missing MORPHEUS_GROUP_ID).


@click.group(help='Morpheus — query, write, and explain the Morpheus knowledge graph.')
@click.version_option(__version__, '--version', '-V')
@click.option(
    '--group-id',
    envvar='MORPHEUS_GROUP_ID',
    default=None,
    show_envvar=True,
    help='Group ID partitioning the graph. Set MORPHEUS_GROUP_ID in your project '
    'environment, or pass --group-id. Required.',
)
@click.option(
    '--provider',
    type=click.Choice(['openai', 'anthropic', 'gemini'], case_sensitive=False),
    default=None,
    help='LLM provider override. Defaults to auto-detection from API-key env vars.',
)
@click.option(
    '--json',
    'json_mode',
    is_flag=True,
    default=False,
    help='Emit machine-readable JSON output instead of human-readable text.',
)
@click.pass_context
def main(
    ctx: click.Context,
    group_id: str | None,
    provider: str | None,
    json_mode: bool,
) -> None:
    ctx.ensure_object(dict)
    ctx.obj['group_id'] = group_id
    ctx.obj['provider'] = provider
    ctx.obj['build_config'] = lambda: _build_config(ctx)
    set_json_mode(json_mode)


# Register subcommands. Imported here at the bottom to avoid circular imports.
from morpheus_cli.commands import (  # noqa: E402
    add,
    edges,
    episodes,
    explain,
    graph,
    path,
    query,
    search,
    status,
)
from morpheus_cli.commands import config as config_cmd  # noqa: E402

main.add_command(status.status)
main.add_command(add.add)
main.add_command(add.add_bulk)
main.add_command(search.search_nodes)
main.add_command(search.search_facts)
main.add_command(episodes.episodes)
main.add_command(episodes.delete_episode)
main.add_command(edges.get_edge)
main.add_command(edges.delete_edge)
main.add_command(graph.clear)
main.add_command(explain.explain)
main.add_command(path.path)
main.add_command(query.query)
main.add_command(config_cmd.config)

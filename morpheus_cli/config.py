"""Configuration resolution for the Morpheus CLI.

The CLI honours, in priority order:

1. Command-line flags (``--group-id``, ``--provider``, etc.)
2. Environment variables — ``MORPHEUS_GROUP_ID`` (set by the consuming
   project, not by Morpheus), plus the standard Graphiti / provider
   env vars (``NEO4J_URI``, ``OPENAI_API_KEY`` etc.)
3. Hard-coded defaults *only* for non-load-bearing settings (Neo4j URI
   defaults to ``bolt://localhost:7687`` if nothing else is set).

Missing ``group_id`` is **always** an error — never a silent fallback to
``main`` or any other implicit default. This is the partition key for
multi-project sharing of a single Morpheus MCP server / Neo4j instance.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MorpheusCliConfig:
    """Resolved CLI configuration for a single invocation."""

    group_id: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    provider: str | None
    """Provider name override; ``None`` means auto-detect at client-build time."""


class MissingGroupIdError(Exception):
    """Raised when no ``group_id`` can be resolved from flag or env.

    The CLI surface translates this into a click.UsageError so the user
    sees a clean error message instead of a traceback.
    """

    def __init__(self) -> None:
        super().__init__(
            'group_id is required. Set MORPHEUS_GROUP_ID in your project\'s '
            'environment (e.g. export MORPHEUS_GROUP_ID=<your-project>), or '
            'pass --group-id <value> on the command line.'
        )


def resolve_group_id(flag_value: str | None) -> str:
    """Resolve group_id from flag (highest precedence) then env.

    Raises ``MissingGroupIdError`` if neither source provides a value.
    """
    if flag_value:
        return flag_value
    env_value = os.environ.get('MORPHEUS_GROUP_ID', '').strip()
    if env_value:
        return env_value
    raise MissingGroupIdError()


def load_config(
    group_id: str | None = None,
    provider: str | None = None,
) -> MorpheusCliConfig:
    """Load the resolved CLI config.

    Args:
        group_id: optional override for the group_id flag.
        provider: optional override for the provider flag.
    """
    return MorpheusCliConfig(
        group_id=resolve_group_id(group_id),
        neo4j_uri=os.environ.get('NEO4J_URI', 'bolt://localhost:7687'),
        neo4j_user=os.environ.get('NEO4J_USER', 'neo4j'),
        neo4j_password=os.environ.get('NEO4J_PASSWORD', 'neo4j'),
        provider=provider.lower() if provider else None,
    )

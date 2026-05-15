"""Build a ``Graphiti`` instance from the resolved CLI config."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from graphiti_core import Graphiti

from morpheus_cli.config import MorpheusCliConfig
from morpheus_cli.llm import build_chat_client, build_embedder


@asynccontextmanager
async def graphiti_session(config: MorpheusCliConfig) -> AsyncIterator[Graphiti]:
    """Async context manager that yields a configured ``Graphiti`` instance.

    Constructs the LLM + embedder via the shared graphiti_core factory and
    wires them to the Neo4j driver. Closes the driver on exit.
    """
    llm_client = build_chat_client(config.provider)
    embedder = build_embedder(config.provider)
    client = Graphiti(
        uri=config.neo4j_uri,
        user=config.neo4j_user,
        password=config.neo4j_password,
        llm_client=llm_client,
        embedder=embedder,
    )
    try:
        yield client
    finally:
        await client.close()

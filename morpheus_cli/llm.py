"""LLM provider resolution for the Morpheus CLI.

The CLI uses Graphiti's LLM provider directly (no Graphify-side adapter).
Provider name comes from (in order):

1. ``--provider`` CLI flag (already resolved into ``MorpheusCliConfig.provider``)
2. Auto-detection from API-key env vars present: anthropic → openai → gemini

API keys themselves are read straight from the standard env vars. The
``graphiti_core.llm_client.factory`` module does the concrete client
construction — this module just resolves the name and reads the key.
"""

from __future__ import annotations

import os

from graphiti_core.embedder.client import EmbedderClient
from graphiti_core.llm_client.client import LLMClient
from graphiti_core.llm_client.factory import make_embedder, make_llm_client


# Env vars consulted, in detection order. The first one whose value is
# non-empty wins for the chat client. Matches the order Graphify uses,
# minus providers Graphiti's factory doesn't ship (kimi, bedrock, ollama).
_PROVIDER_ENV_PRIORITY: tuple[tuple[str, tuple[str, ...]], ...] = (
    ('anthropic', ('ANTHROPIC_API_KEY',)),
    ('openai', ('OPENAI_API_KEY',)),
    ('gemini', ('GEMINI_API_KEY', 'GOOGLE_API_KEY')),
)


class NoProviderConfiguredError(Exception):
    """Raised when no provider override is given and no API key env var is set."""

    def __init__(self) -> None:
        super().__init__(
            'No LLM provider could be resolved. Set one of '
            'ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY (or GOOGLE_API_KEY) '
            'in the environment, or pass --provider on the command line.'
        )


def detect_provider() -> str | None:
    """Return the first provider whose API key env var is set, or ``None``."""
    for provider, env_keys in _PROVIDER_ENV_PRIORITY:
        for key in env_keys:
            if os.environ.get(key, '').strip():
                return provider
    return None


def resolve_provider(override: str | None) -> str:
    """Resolve the provider name. ``override`` wins if truthy; else auto-detect."""
    if override:
        return override.lower()
    detected = detect_provider()
    if detected is None:
        raise NoProviderConfiguredError()
    return detected


def _api_key_for(provider: str) -> str:
    """Read the API key env var for ``provider``. Returns ``''`` if not set."""
    for prov, env_keys in _PROVIDER_ENV_PRIORITY:
        if prov == provider:
            for key in env_keys:
                value = os.environ.get(key, '').strip()
                if value:
                    return value
            return ''
    return ''


def build_chat_client(provider: str | None = None) -> LLMClient:
    """Build a chat LLM client following the resolution chain."""
    name = resolve_provider(provider)
    api_key = _api_key_for(name)
    return make_llm_client(name, api_key=api_key)


def build_embedder(provider: str | None = None) -> EmbedderClient:
    """Build an embedder following the same provider resolution.

    Graphiti supports embedders for openai and gemini; if the resolved
    chat provider is anthropic (which has no embedder of its own), we
    fall back to openai for the embedder slot.
    """
    name = resolve_provider(provider)
    if name == 'anthropic':
        name = 'openai'
    api_key = _api_key_for(name)
    return make_embedder(name, api_key=api_key)

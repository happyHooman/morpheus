"""Provider-name → concrete LLMClient / EmbedderClient factory.

Shared by the MCP server and any other in-tree consumer (e.g. a CLI) so that
"given a provider string, give me a configured client" lives in one place.

Provider-specific extras that need custom client construction (e.g.
``azure_openai`` building an ``AsyncOpenAI`` instance against a v1
endpoint) are not handled here — callers that need them should construct
the client directly. This module covers the common providers that map
cleanly to ``LLMConfig`` + a concrete client class.
"""

from __future__ import annotations

from graphiti_core.embedder.client import EmbedderClient
from graphiti_core.llm_client.client import LLMClient
from graphiti_core.llm_client.config import LLMConfig


def make_llm_client(
    provider: str,
    api_key: str,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    base_url: str | None = None,
    small_model: str | None = None,
) -> LLMClient:
    """Create an LLM chat client for a named provider.

    Supports ``openai``, ``anthropic``, ``gemini``, ``groq``.

    OpenAI reasoning models (``o1*``, ``o3*``, ``gpt-5*``) are detected from
    the model name and passed ``reasoning='minimal', verbosity='low'``;
    non-reasoning models pass ``None`` for both so the request payload does
    not include those parameters.

    Args:
        provider: Provider name, case-insensitive.
        api_key: API key. Required and non-empty.
        model: Model name override; provider default applies if ``None``.
        temperature: Sampling temperature.
        max_tokens: Maximum output tokens.
        base_url: Custom base URL (groq supports this; others ignore).
        small_model: Smaller/cheaper model for small-task slots (openai only).

    Returns:
        A concrete ``LLMClient`` subclass instance.

    Raises:
        ValueError: If the provider is unsupported, the API key is missing,
            or the corresponding optional dependency is not installed.
    """
    if not api_key:
        raise ValueError(
            f'{provider} API key is not configured. '
            'Set the appropriate environment variable or pass api_key explicitly.'
        )

    provider_lower = provider.lower()

    config = LLMConfig(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        base_url=base_url,
        small_model=small_model,
    )

    if provider_lower == 'openai':
        from graphiti_core.llm_client.openai_client import OpenAIClient

        reasoning_prefixes = ('o1', 'o3', 'gpt-5')
        is_reasoning_model = model is not None and model.startswith(reasoning_prefixes)
        if is_reasoning_model:
            return OpenAIClient(config=config, reasoning='minimal', verbosity='low')
        return OpenAIClient(config=config, reasoning=None, verbosity=None)

    if provider_lower == 'anthropic':
        try:
            from graphiti_core.llm_client.anthropic_client import AnthropicClient
        except ImportError as e:
            raise ValueError(
                'Anthropic client not available. '
                'Install with `pip install graphiti-core[anthropic]`.'
            ) from e
        return AnthropicClient(config=config)

    if provider_lower == 'gemini':
        try:
            from graphiti_core.llm_client.gemini_client import GeminiClient
        except ImportError as e:
            raise ValueError(
                'Gemini client not available. '
                'Install with `pip install graphiti-core[google-genai]`.'
            ) from e
        return GeminiClient(config=config)

    if provider_lower == 'groq':
        try:
            from graphiti_core.llm_client.groq_client import GroqClient
        except ImportError as e:
            raise ValueError(
                'Groq client not available. Install with `pip install graphiti-core[groq]`.'
            ) from e
        return GroqClient(config=config)

    raise ValueError(f'Unsupported LLM provider: {provider}')


def make_embedder(
    provider: str,
    api_key: str,
    model: str | None = None,
    embedding_dim: int | None = None,
    base_url: str | None = None,
) -> EmbedderClient:
    """Create an Embedder client for a named provider.

    Supports ``openai``, ``gemini``, ``voyage``.

    Args:
        provider: Provider name, case-insensitive.
        api_key: API key. Required and non-empty.
        model: Embedding model name; provider default applies if ``None``.
        embedding_dim: Embedding dimensionality; provider default if ``None``.
        base_url: Custom base URL (openai supports this for compat endpoints).

    Returns:
        A concrete ``EmbedderClient`` subclass instance.

    Raises:
        ValueError: If the provider is unsupported, the API key is missing,
            or the corresponding optional dependency is not installed.
    """
    if not api_key:
        raise ValueError(
            f'{provider} embedder API key is not configured. '
            'Set the appropriate environment variable or pass api_key explicitly.'
        )

    provider_lower = provider.lower()

    if provider_lower == 'openai':
        from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig

        kwargs: dict = {'api_key': api_key, 'base_url': base_url}
        if model is not None:
            kwargs['embedding_model'] = model
        if embedding_dim is not None:
            kwargs['embedding_dim'] = embedding_dim
        embedder_config = OpenAIEmbedderConfig(**kwargs)
        return OpenAIEmbedder(config=embedder_config)

    if provider_lower == 'gemini':
        try:
            from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
        except ImportError as e:
            raise ValueError(
                'Gemini embedder not available. '
                'Install with `pip install graphiti-core[google-genai]`.'
            ) from e
        gemini_config = GeminiEmbedderConfig(
            api_key=api_key,
            embedding_model=model or 'models/text-embedding-004',
            embedding_dim=embedding_dim or 768,
        )
        return GeminiEmbedder(config=gemini_config)

    if provider_lower == 'voyage':
        try:
            from graphiti_core.embedder.voyage import VoyageAIEmbedder, VoyageAIEmbedderConfig
        except ImportError as e:
            raise ValueError(
                'Voyage embedder not available. '
                'Install with `pip install graphiti-core[voyageai]`.'
            ) from e
        voyage_config = VoyageAIEmbedderConfig(
            api_key=api_key,
            embedding_model=model or 'voyage-3',
            embedding_dim=embedding_dim or 1024,
        )
        return VoyageAIEmbedder(config=voyage_config)

    raise ValueError(f'Unsupported Embedder provider: {provider}')

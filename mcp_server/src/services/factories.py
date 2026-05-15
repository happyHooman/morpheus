"""Factory classes for creating LLM, Embedder, and Database clients."""

from config.schema import (
    DatabaseConfig,
    EmbedderConfig,
    LLMConfig,
)

# Try to import FalkorDriver if available
try:
    from graphiti_core.driver.falkordb_driver import FalkorDriver  # noqa: F401

    HAS_FALKOR = True
except ImportError:
    HAS_FALKOR = False

# Kuzu support removed - FalkorDB is now the default
from graphiti_core.embedder import EmbedderClient, OpenAIEmbedder
from graphiti_core.llm_client import LLMClient, OpenAIClient
from graphiti_core.llm_client.config import LLMConfig as GraphitiLLMConfig

# Try to import additional providers if available
try:
    from graphiti_core.embedder.azure_openai import AzureOpenAIEmbedderClient

    HAS_AZURE_EMBEDDER = True
except ImportError:
    HAS_AZURE_EMBEDDER = False

try:
    from graphiti_core.embedder.gemini import GeminiEmbedder

    HAS_GEMINI_EMBEDDER = True
except ImportError:
    HAS_GEMINI_EMBEDDER = False

try:
    from graphiti_core.embedder.voyage import VoyageAIEmbedder

    HAS_VOYAGE_EMBEDDER = True
except ImportError:
    HAS_VOYAGE_EMBEDDER = False

try:
    from graphiti_core.llm_client.azure_openai_client import AzureOpenAILLMClient

    HAS_AZURE_LLM = True
except ImportError:
    HAS_AZURE_LLM = False

try:
    from graphiti_core.llm_client.anthropic_client import AnthropicClient

    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from graphiti_core.llm_client.gemini_client import GeminiClient

    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    from graphiti_core.llm_client.groq_client import GroqClient

    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


def _validate_api_key(provider_name: str, api_key: str | None, logger) -> str:
    """Validate API key is present.

    Args:
        provider_name: Name of the provider (e.g., 'OpenAI', 'Anthropic')
        api_key: The API key to validate
        logger: Logger instance for output

    Returns:
        The validated API key

    Raises:
        ValueError: If API key is None or empty
    """
    if not api_key:
        raise ValueError(
            f'{provider_name} API key is not configured. Please set the appropriate environment variable.'
        )

    logger.info(f'Creating {provider_name} client')

    return api_key


class LLMClientFactory:
    """Factory for creating LLM clients based on configuration."""

    @staticmethod
    def create(config: LLMConfig) -> LLMClient:
        """Create an LLM client based on the configured provider.

        Simple providers (openai, anthropic, gemini, groq) delegate to
        ``graphiti_core.llm_client.factory.make_llm_client`` so the
        provider-name → client-class mapping lives in one place. The
        ``azure_openai`` path stays here because it needs custom
        ``AsyncOpenAI`` client construction against a v1-compatibility
        endpoint, which is mcp_server specific.
        """
        import logging

        from graphiti_core.llm_client.factory import make_llm_client

        logger = logging.getLogger(__name__)

        provider = config.provider.lower()

        if provider == 'azure_openai':
            if not HAS_AZURE_LLM:
                raise ValueError(
                    'Azure OpenAI LLM client not available in current graphiti-core version'
                )
            if not config.providers.azure_openai:
                raise ValueError('Azure OpenAI provider configuration not found')
            azure_config = config.providers.azure_openai

            if not azure_config.api_url:
                raise ValueError('Azure OpenAI API URL is required')

            # Currently using API key authentication
            # TODO: Add Azure AD authentication support for v1 API compatibility
            api_key = azure_config.api_key
            _validate_api_key('Azure OpenAI', api_key, logger)

            # Azure OpenAI should use the standard AsyncOpenAI client with v1 compatibility endpoint
            # See: https://github.com/getzep/graphiti README Azure OpenAI section
            from openai import AsyncOpenAI

            # Ensure the base_url ends with /openai/v1/ for Azure v1 compatibility
            base_url = azure_config.api_url
            if not base_url.endswith('/'):
                base_url += '/'
            if not base_url.endswith('openai/v1/'):
                base_url += 'openai/v1/'

            azure_client = AsyncOpenAI(
                base_url=base_url,
                api_key=api_key,
            )

            # Then create the LLMConfig
            llm_config = GraphitiLLMConfig(
                api_key=api_key,
                base_url=base_url,
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )

            return AzureOpenAILLMClient(
                azure_client=azure_client,
                config=llm_config,
                max_tokens=config.max_tokens,
            )

        # Pull provider-specific config block; nested attribute mirrors the
        # match arms removed above (config.providers.openai, .anthropic, etc.).
        provider_block = getattr(config.providers, provider, None)
        if provider_block is None:
            raise ValueError(f'{provider} provider configuration not found')

        api_key = provider_block.api_key
        _validate_api_key(provider.capitalize(), api_key, logger)

        # openai reused config.model for both main and small slots in the
        # original match; preserve that exactly. Other providers don't set
        # small_model.
        small_model = config.model if provider == 'openai' else None

        # groq is the only simple provider that passes a base_url.
        base_url = getattr(provider_block, 'api_url', None) if provider == 'groq' else None

        return make_llm_client(
            provider=provider,
            api_key=api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            base_url=base_url,
            small_model=small_model,
        )


class EmbedderFactory:
    """Factory for creating Embedder clients based on configuration."""

    @staticmethod
    def create(config: EmbedderConfig) -> EmbedderClient:
        """Create an Embedder client based on the configured provider.

        Simple providers (openai, gemini, voyage) delegate to
        ``graphiti_core.llm_client.factory.make_embedder``. The
        ``azure_openai`` path stays here because it needs custom
        ``AsyncOpenAI`` client construction.
        """
        import logging

        from graphiti_core.llm_client.factory import make_embedder

        logger = logging.getLogger(__name__)

        provider = config.provider.lower()

        if provider == 'azure_openai':
            if not HAS_AZURE_EMBEDDER:
                raise ValueError(
                    'Azure OpenAI embedder not available in current graphiti-core version'
                )
            if not config.providers.azure_openai:
                raise ValueError('Azure OpenAI provider configuration not found')
            azure_config = config.providers.azure_openai

            if not azure_config.api_url:
                raise ValueError('Azure OpenAI API URL is required')

            # Currently using API key authentication
            # TODO: Add Azure AD authentication support for v1 API compatibility
            api_key = azure_config.api_key
            _validate_api_key('Azure OpenAI Embedder', api_key, logger)

            # Azure OpenAI should use the standard AsyncOpenAI client with v1 compatibility endpoint
            # See: https://github.com/getzep/graphiti README Azure OpenAI section
            from openai import AsyncOpenAI

            # Ensure the base_url ends with /openai/v1/ for Azure v1 compatibility
            base_url = azure_config.api_url
            if not base_url.endswith('/'):
                base_url += '/'
            if not base_url.endswith('openai/v1/'):
                base_url += 'openai/v1/'

            azure_client = AsyncOpenAI(
                base_url=base_url,
                api_key=api_key,
            )

            return AzureOpenAIEmbedderClient(
                azure_client=azure_client,
                model=config.model or 'text-embedding-3-small',
            )

        provider_block = getattr(config.providers, provider, None)
        if provider_block is None:
            raise ValueError(f'{provider} provider configuration not found')

        api_key = provider_block.api_key
        _validate_api_key(f'{provider.capitalize()} Embedder', api_key, logger)

        # openai is the only embedder provider whose api_url is honored for
        # custom endpoints (e.g. Ollama-style).
        base_url = getattr(provider_block, 'api_url', None) if provider == 'openai' else None

        return make_embedder(
            provider=provider,
            api_key=api_key,
            model=config.model,
            embedding_dim=config.dimensions,
            base_url=base_url,
        )


class DatabaseDriverFactory:
    """Factory for creating Database drivers based on configuration.

    Note: This returns configuration dictionaries that can be passed to Graphiti(),
    not driver instances directly, as the drivers require complex initialization.
    """

    @staticmethod
    def create_config(config: DatabaseConfig) -> dict:
        """Create database configuration dictionary based on the configured provider."""
        provider = config.provider.lower()

        match provider:
            case 'neo4j':
                # Use Neo4j config if provided, otherwise use defaults
                if config.providers.neo4j:
                    neo4j_config = config.providers.neo4j
                else:
                    # Create default Neo4j configuration
                    from config.schema import Neo4jProviderConfig

                    neo4j_config = Neo4jProviderConfig()

                # Check for environment variable overrides (for CI/CD compatibility)
                import os

                uri = os.environ.get('NEO4J_URI', neo4j_config.uri)
                username = os.environ.get('NEO4J_USER', neo4j_config.username)
                password = os.environ.get('NEO4J_PASSWORD', neo4j_config.password)

                return {
                    'uri': uri,
                    'user': username,
                    'password': password,
                    # Note: database and use_parallel_runtime would need to be passed
                    # to the driver after initialization if supported
                }

            case 'falkordb':
                if not HAS_FALKOR:
                    raise ValueError(
                        'FalkorDB driver not available in current graphiti-core version'
                    )

                # Use FalkorDB config if provided, otherwise use defaults
                if config.providers.falkordb:
                    falkor_config = config.providers.falkordb
                else:
                    # Create default FalkorDB configuration
                    from config.schema import FalkorDBProviderConfig

                    falkor_config = FalkorDBProviderConfig()

                # Check for environment variable overrides (for CI/CD compatibility)
                import os
                from urllib.parse import urlparse

                uri = os.environ.get('FALKORDB_URI', falkor_config.uri)
                password = os.environ.get('FALKORDB_PASSWORD', falkor_config.password)

                # Parse the URI to extract host and port
                parsed = urlparse(uri)
                host = parsed.hostname or 'localhost'
                port = parsed.port or 6379

                return {
                    'driver': 'falkordb',
                    'host': host,
                    'port': port,
                    'password': password,
                    'database': falkor_config.database,
                }

            case _:
                raise ValueError(f'Unsupported Database provider: {provider}')

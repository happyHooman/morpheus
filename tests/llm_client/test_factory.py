"""Tests for the provider-name → client-class factory.

These tests do not make any network calls; they only confirm that
``make_llm_client`` and ``make_embedder`` return the expected concrete
client class for each supported provider name and raise on bad input.
"""

import pytest

from graphiti_core.llm_client.factory import make_embedder, make_llm_client


def test_make_llm_client_openai_returns_openai_client():
    from graphiti_core.llm_client.openai_client import OpenAIClient

    client = make_llm_client('openai', api_key='sk-test', model='gpt-4.1-mini')
    assert isinstance(client, OpenAIClient)


def test_make_llm_client_openai_is_case_insensitive():
    from graphiti_core.llm_client.openai_client import OpenAIClient

    client = make_llm_client('OpenAI', api_key='sk-test', model='gpt-4.1-mini')
    assert isinstance(client, OpenAIClient)


def test_make_llm_client_anthropic_returns_anthropic_client():
    pytest.importorskip('anthropic')
    from graphiti_core.llm_client.anthropic_client import AnthropicClient

    client = make_llm_client('anthropic', api_key='sk-ant-test')
    assert isinstance(client, AnthropicClient)


def test_make_llm_client_gemini_returns_gemini_client():
    pytest.importorskip('google.genai')
    from graphiti_core.llm_client.gemini_client import GeminiClient

    client = make_llm_client('gemini', api_key='ai-test')
    assert isinstance(client, GeminiClient)


def test_make_llm_client_groq_returns_groq_client():
    pytest.importorskip('groq')
    from graphiti_core.llm_client.groq_client import GroqClient

    client = make_llm_client('groq', api_key='gsk-test')
    assert isinstance(client, GroqClient)


def test_make_llm_client_unsupported_provider_raises():
    with pytest.raises(ValueError, match='Unsupported LLM provider'):
        make_llm_client('kimi', api_key='dummy')


def test_make_llm_client_missing_api_key_raises():
    with pytest.raises(ValueError, match='API key is not configured'):
        make_llm_client('openai', api_key='', model='gpt-4.1-mini')


def test_make_llm_client_openai_reasoning_model_passes_reasoning_kwarg():
    """Reasoning models (o1, o3, gpt-5*) should set reasoning='minimal'."""
    from graphiti_core.llm_client.openai_client import OpenAIClient

    client = make_llm_client('openai', api_key='sk-test', model='gpt-5-mini')
    assert isinstance(client, OpenAIClient)
    # The reasoning kwarg is preserved on the client instance.
    assert client.reasoning == 'minimal'
    assert client.verbosity == 'low'


def test_make_llm_client_openai_non_reasoning_model_disables_reasoning():
    """Non-reasoning models should pass reasoning=None to omit the param."""
    from graphiti_core.llm_client.openai_client import OpenAIClient

    client = make_llm_client('openai', api_key='sk-test', model='gpt-4.1-mini')
    assert isinstance(client, OpenAIClient)
    assert client.reasoning is None
    assert client.verbosity is None


def test_make_embedder_openai_returns_openai_embedder():
    from graphiti_core.embedder.openai import OpenAIEmbedder

    embedder = make_embedder('openai', api_key='sk-test', model='text-embedding-3-small')
    assert isinstance(embedder, OpenAIEmbedder)


def test_make_embedder_unsupported_provider_raises():
    with pytest.raises(ValueError, match='Unsupported Embedder provider'):
        make_embedder('voyage_v2', api_key='dummy')


def test_make_embedder_missing_api_key_raises():
    with pytest.raises(ValueError, match='API key is not configured'):
        make_embedder('openai', api_key='')

"""Smoke tests for the Morpheus CLI.

Confirms that every subcommand's ``--help`` returns exit 0, that
config/provider resolution errors translate to clean ``UsageError``
messages, and that the right LLMClient subclass is built for each
provider. No live Neo4j or LLM calls.
"""

from __future__ import annotations

import os

import click
import pytest
from click.testing import CliRunner

from morpheus_cli.cli import main
from morpheus_cli.config import MissingGroupIdError, resolve_group_id
from morpheus_cli.llm import (
    NoProviderConfiguredError,
    build_chat_client,
    detect_provider,
    resolve_provider,
)


# Every subcommand registered on the root group. Updating this list when
# new commands land doubles as a low-effort regression guard.
_SUBCOMMANDS: tuple[str, ...] = (
    'status',
    'add',
    'add-bulk',
    'search-nodes',
    'search-facts',
    'episodes',
    'delete-episode',
    'get-edge',
    'delete-edge',
    'clear',
    'explain',
    'path',
    'query',
    'config',
)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_root_help_lists_all_commands(runner: CliRunner) -> None:
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0, result.output
    for cmd in _SUBCOMMANDS:
        assert cmd in result.output, f'{cmd} missing from `morpheus --help` output'


def test_root_version(runner: CliRunner) -> None:
    result = runner.invoke(main, ['--version'])
    assert result.exit_code == 0
    assert 'morpheus' in result.output.lower() or 'version' in result.output.lower()


@pytest.mark.parametrize('subcommand', _SUBCOMMANDS)
def test_subcommand_help_exits_clean(runner: CliRunner, subcommand: str) -> None:
    result = runner.invoke(main, [subcommand, '--help'])
    assert result.exit_code == 0, (
        f'`morpheus {subcommand} --help` exited {result.exit_code}\n{result.output}'
    )
    assert subcommand in result.output or 'Usage' in result.output


def test_missing_group_id_is_usage_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('MORPHEUS_GROUP_ID', raising=False)
    with pytest.raises(MissingGroupIdError):
        resolve_group_id(flag_value=None)


def test_flag_group_id_wins_over_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('MORPHEUS_GROUP_ID', 'from-env')
    assert resolve_group_id(flag_value='from-flag') == 'from-flag'


def test_env_group_id_used_when_flag_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('MORPHEUS_GROUP_ID', 'from-env')
    assert resolve_group_id(flag_value=None) == 'from-env'


def test_resolve_provider_override(monkeypatch: pytest.MonkeyPatch) -> None:
    # Override wins even if no env keys are set.
    for k in ('ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY'):
        monkeypatch.delenv(k, raising=False)
    assert resolve_provider('openai') == 'openai'
    assert resolve_provider('Anthropic') == 'anthropic'


def test_resolve_provider_autodetect(monkeypatch: pytest.MonkeyPatch) -> None:
    for k in ('ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY'):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test')
    assert detect_provider() == 'openai'
    assert resolve_provider(None) == 'openai'


def test_resolve_provider_anthropic_priority(monkeypatch: pytest.MonkeyPatch) -> None:
    # Both set; anthropic comes first in priority.
    for k in ('ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY'):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'sk-ant-test')
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test')
    assert detect_provider() == 'anthropic'


def test_resolve_provider_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    for k in ('ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY'):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(NoProviderConfiguredError):
        resolve_provider(None)


def test_build_chat_client_returns_openai_class(monkeypatch: pytest.MonkeyPatch) -> None:
    from graphiti_core.llm_client.openai_client import OpenAIClient

    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test')
    client = build_chat_client('openai')
    assert isinstance(client, OpenAIClient)


def test_build_chat_client_returns_anthropic_class(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip('anthropic')
    from graphiti_core.llm_client.anthropic_client import AnthropicClient

    monkeypatch.setenv('ANTHROPIC_API_KEY', 'sk-ant-test')
    client = build_chat_client('anthropic')
    assert isinstance(client, AnthropicClient)

"""Unit tests for the LLM client factory — provider routing + lazy imports."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from tradingagents.llm_clients.factory import create_llm_client


@pytest.mark.unit
def test_factory_routes_anthropic_to_anthropic_client():
    with patch("tradingagents.llm_clients.anthropic_client.AnthropicClient") as mock_cls:
        create_llm_client("anthropic", "claude-sonnet-4-6")
    mock_cls.assert_called_once()


@pytest.mark.unit
def test_factory_routes_google_to_google_client():
    with patch("tradingagents.llm_clients.google_client.GoogleClient") as mock_cls:
        create_llm_client("google", "gemini-3.1-pro-preview")
    mock_cls.assert_called_once()


@pytest.mark.unit
@pytest.mark.parametrize(
    "provider", ["openai", "xai", "deepseek", "qwen", "glm", "ollama", "openrouter"]
)
def test_factory_routes_openai_compatible_providers(provider):
    """All OpenAI-compatible providers route through OpenAIClient with the
    provider tag preserved as kwarg."""
    with patch("tradingagents.llm_clients.openai_client.OpenAIClient") as mock_cls:
        create_llm_client(provider, "some-model")
    mock_cls.assert_called_once()
    _args, kwargs = mock_cls.call_args
    assert kwargs.get("provider") == provider


@pytest.mark.unit
def test_factory_provider_routing_is_case_insensitive():
    with patch("tradingagents.llm_clients.anthropic_client.AnthropicClient") as mock_cls:
        create_llm_client("ANTHROPIC", "claude-sonnet-4-6")
    mock_cls.assert_called_once()


@pytest.mark.unit
def test_factory_raises_on_unsupported_provider():
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        create_llm_client("definitely-not-a-real-provider", "some-model")


@pytest.mark.unit
def test_factory_passes_base_url_through():
    with patch("tradingagents.llm_clients.anthropic_client.AnthropicClient") as mock_cls:
        create_llm_client("anthropic", "claude-sonnet-4-6", base_url="https://proxy/")
    args, _kwargs = mock_cls.call_args
    # AnthropicClient's __init__ takes (model, base_url, **kwargs) positionally
    assert args[1] == "https://proxy/"


@pytest.mark.unit
def test_factory_passes_extra_kwargs_through():
    with patch("tradingagents.llm_clients.anthropic_client.AnthropicClient") as mock_cls:
        create_llm_client("anthropic", "claude-sonnet-4-6", max_tokens=4096, api_key="sk-x")
    _args, kwargs = mock_cls.call_args
    assert kwargs["max_tokens"] == 4096
    assert kwargs["api_key"] == "sk-x"

"""Unit tests for AnthropicClient.

The framework's actual deep_think_llm path runs through this module on
every propagate(). Previously had 0% test coverage — adding smoke tests
that catch the most likely regressions (model passthrough, kwargs
filtering, content normalization, unknown-model warning).
"""

from __future__ import annotations

import warnings
from unittest.mock import MagicMock, patch

import pytest

from tradingagents.llm_clients.anthropic_client import (
    AnthropicClient,
    NormalizedChatAnthropic,
)
from tradingagents.llm_clients.base_client import normalize_content


# -- normalize_content --------------------------------------------------------


@pytest.mark.unit
def test_normalize_content_passthrough_string():
    """Plain-string content is returned unchanged."""
    response = MagicMock()
    response.content = "hello world"
    out = normalize_content(response)
    assert out.content == "hello world"


@pytest.mark.unit
def test_normalize_content_extracts_text_blocks():
    """List-of-blocks (Anthropic with extended thinking) is joined to string."""
    response = MagicMock()
    response.content = [
        {"type": "reasoning", "text": "thinking..."},
        {"type": "text", "text": "Final answer."},
        {"type": "text", "text": "More text."},
    ]
    out = normalize_content(response)
    # Only `type=text` blocks contribute. Reasoning is discarded.
    assert out.content == "Final answer.\nMore text."


@pytest.mark.unit
def test_normalize_content_discards_non_text_blocks():
    """Tool-use blocks and other typed blocks are not included."""
    response = MagicMock()
    response.content = [
        {"type": "tool_use", "id": "abc", "input": {}},
        {"type": "text", "text": "Visible."},
    ]
    out = normalize_content(response)
    assert out.content == "Visible."


@pytest.mark.unit
def test_normalize_content_handles_string_items_in_list():
    """Bare strings inside a content list are concatenated too."""
    response = MagicMock()
    response.content = ["chunk a", "chunk b"]
    out = normalize_content(response)
    assert out.content == "chunk a\nchunk b"


@pytest.mark.unit
def test_normalize_content_empty_list_yields_empty_string():
    response = MagicMock()
    response.content = []
    out = normalize_content(response)
    assert out.content == ""


# -- AnthropicClient ----------------------------------------------------------


@pytest.mark.unit
def test_anthropic_client_passes_model_to_chat_anthropic():
    """The model arg flows into ChatAnthropic."""
    client = AnthropicClient(model="claude-sonnet-4-6")
    with patch(
        "tradingagents.llm_clients.anthropic_client.NormalizedChatAnthropic"
    ) as mock_chat:
        client.get_llm()
    args, kwargs = mock_chat.call_args
    assert kwargs["model"] == "claude-sonnet-4-6"


@pytest.mark.unit
def test_anthropic_client_filters_unknown_kwargs():
    """Only whitelisted kwargs (PASSTHROUGH) reach ChatAnthropic.

    A user-passed `temperature=0.5` should NOT silently appear because it's
    not in the passthrough list — Anthropic kwargs are tightly controlled
    here.
    """
    client = AnthropicClient(
        model="claude-sonnet-4-6",
        temperature=0.5,  # not in passthrough — should be dropped
        max_tokens=2048,  # in passthrough — should be kept
        api_key="sk-test",  # in passthrough
    )
    with patch(
        "tradingagents.llm_clients.anthropic_client.NormalizedChatAnthropic"
    ) as mock_chat:
        client.get_llm()
    _args, kwargs = mock_chat.call_args
    assert kwargs["max_tokens"] == 2048
    assert kwargs["api_key"] == "sk-test"
    assert "temperature" not in kwargs


@pytest.mark.unit
def test_anthropic_client_passes_base_url_when_provided():
    """A non-None base_url is forwarded; a None base_url is omitted."""
    client = AnthropicClient(model="claude-sonnet-4-6", base_url="https://proxy.example/")
    with patch(
        "tradingagents.llm_clients.anthropic_client.NormalizedChatAnthropic"
    ) as mock_chat:
        client.get_llm()
    _args, kwargs = mock_chat.call_args
    assert kwargs["base_url"] == "https://proxy.example/"


@pytest.mark.unit
def test_anthropic_client_omits_base_url_when_none():
    """When base_url is None we must NOT pass base_url=None to ChatAnthropic
    (would override its provider default and was the source of the Gemini
    404 bug noted in CLAUDE.md)."""
    client = AnthropicClient(model="claude-sonnet-4-6", base_url=None)
    with patch(
        "tradingagents.llm_clients.anthropic_client.NormalizedChatAnthropic"
    ) as mock_chat:
        client.get_llm()
    _args, kwargs = mock_chat.call_args
    assert "base_url" not in kwargs


@pytest.mark.unit
def test_anthropic_client_validates_known_model():
    """Sonnet 4.6 is in the catalog → validate_model returns True."""
    client = AnthropicClient(model="claude-sonnet-4-6")
    assert client.validate_model() is True


@pytest.mark.unit
def test_anthropic_client_validates_unknown_model_returns_false():
    """A non-catalog model returns False from validate_model (drives the
    warn_if_unknown_model warning at get_llm() time)."""
    client = AnthropicClient(model="claude-not-a-real-model")
    assert client.validate_model() is False


@pytest.mark.unit
def test_anthropic_client_warns_on_unknown_model():
    """Unknown model triggers a RuntimeWarning when get_llm() is called."""
    client = AnthropicClient(model="claude-not-a-real-model")
    with patch("tradingagents.llm_clients.anthropic_client.NormalizedChatAnthropic"):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            client.get_llm()
    assert any(
        "is not in the known model list" in str(w.message) for w in caught
    ), f"expected unknown-model warning, got {[str(w.message) for w in caught]}"


@pytest.mark.unit
def test_anthropic_client_does_not_warn_on_known_model():
    """Known model produces NO unknown-model warning."""
    client = AnthropicClient(model="claude-sonnet-4-6")
    with patch("tradingagents.llm_clients.anthropic_client.NormalizedChatAnthropic"):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            client.get_llm()
    assert not any("is not in the known model list" in str(w.message) for w in caught)


@pytest.mark.unit
def test_anthropic_client_provider_name_is_anthropic():
    """get_provider_name() drives warning text and metrics tagging."""
    client = AnthropicClient(model="claude-sonnet-4-6")
    assert client.get_provider_name() == "anthropic"


@pytest.mark.unit
def test_opus_47_is_in_catalog():
    """Regression: claude-opus-4-7 was added to the catalog after the
    005 experiment warned 'not in the known model list'. Ensure it stays."""
    client = AnthropicClient(model="claude-opus-4-7")
    assert client.validate_model() is True

"""Unit tests for OpenAIClient and NormalizedChatOpenAI.

Covers all 7 OpenAI-compatible providers (openai, xai, deepseek, qwen,
glm, openrouter, ollama) — base URL routing, API key env-var lookup,
kwargs filtering, structured-output method default, and the OpenAI-only
use_responses_api flag.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tradingagents.llm_clients.openai_client import (
    NormalizedChatOpenAI,
    OpenAIClient,
)


# -- Native OpenAI ------------------------------------------------------------


@pytest.mark.unit
def test_openai_provider_uses_responses_api():
    """Native OpenAI sets use_responses_api=True (drives reasoning_effort
    support across all model families)."""
    client = OpenAIClient(model="gpt-5.4", provider="openai")
    with patch("tradingagents.llm_clients.openai_client.NormalizedChatOpenAI") as mock_cls:
        client.get_llm()
    _args, kwargs = mock_cls.call_args
    assert kwargs.get("use_responses_api") is True
    assert kwargs["model"] == "gpt-5.4"


@pytest.mark.unit
def test_third_party_provider_does_not_set_responses_api():
    """xAI / DeepSeek / etc. use standard Chat Completions, not Responses API."""
    client = OpenAIClient(model="grok-4-0709", provider="xai")
    with patch("tradingagents.llm_clients.openai_client.NormalizedChatOpenAI") as mock_cls:
        with patch.dict("os.environ", {"XAI_API_KEY": "sk-xai-test"}, clear=False):
            client.get_llm()
    _args, kwargs = mock_cls.call_args
    assert "use_responses_api" not in kwargs


# -- Provider routing --------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    "provider, expected_base_url, env_var, env_value",
    [
        ("xai", "https://api.x.ai/v1", "XAI_API_KEY", "sk-xai-test"),
        ("deepseek", "https://api.deepseek.com", "DEEPSEEK_API_KEY", "sk-ds-test"),
        ("qwen", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1", "DASHSCOPE_API_KEY", "sk-q-test"),
        ("glm", "https://api.z.ai/api/paas/v4/", "ZHIPU_API_KEY", "sk-glm-test"),
        ("openrouter", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "sk-or-test"),
    ],
)
def test_openai_compatible_provider_base_url_and_key(
    provider, expected_base_url, env_var, env_value
):
    """Each compatible provider gets its hardcoded base_url and reads its
    API key from the documented env var."""
    client = OpenAIClient(model="some-model", provider=provider)
    with patch("tradingagents.llm_clients.openai_client.NormalizedChatOpenAI") as mock_cls:
        with patch.dict("os.environ", {env_var: env_value}, clear=False):
            client.get_llm()
    _args, kwargs = mock_cls.call_args
    assert kwargs["base_url"] == expected_base_url
    assert kwargs["api_key"] == env_value


@pytest.mark.unit
def test_ollama_uses_local_url_and_dummy_api_key():
    """Ollama gets a local base URL and the literal "ollama" as api_key
    (Ollama doesn't authenticate but ChatOpenAI requires non-empty key)."""
    client = OpenAIClient(model="qwen3:latest", provider="ollama")
    with patch("tradingagents.llm_clients.openai_client.NormalizedChatOpenAI") as mock_cls:
        client.get_llm()
    _args, kwargs = mock_cls.call_args
    assert kwargs["base_url"] == "http://localhost:11434/v1"
    assert kwargs["api_key"] == "ollama"


@pytest.mark.unit
def test_provider_with_missing_env_var_omits_api_key():
    """If the provider's env var isn't set, api_key is NOT added (rather than
    crashing or sending an empty string). User sees the auth error from the
    SDK, which is clearer."""
    client = OpenAIClient(model="grok-4-0709", provider="xai")
    with patch("tradingagents.llm_clients.openai_client.NormalizedChatOpenAI") as mock_cls:
        with patch.dict("os.environ", {}, clear=True):
            client.get_llm()
    _args, kwargs = mock_cls.call_args
    # base_url still set, but api_key omitted
    assert kwargs["base_url"] == "https://api.x.ai/v1"
    assert "api_key" not in kwargs


@pytest.mark.unit
def test_native_openai_with_user_base_url():
    """For native openai, no provider-config entry → user's base_url passes
    through if provided."""
    client = OpenAIClient(
        model="gpt-5.4", base_url="https://proxy.example/", provider="openai"
    )
    with patch("tradingagents.llm_clients.openai_client.NormalizedChatOpenAI") as mock_cls:
        client.get_llm()
    _args, kwargs = mock_cls.call_args
    assert kwargs["base_url"] == "https://proxy.example/"


# -- Kwargs filtering --------------------------------------------------------


@pytest.mark.unit
def test_kwargs_filtered_to_passthrough_list():
    """Only the documented PASSTHROUGH kwargs reach ChatOpenAI."""
    client = OpenAIClient(
        model="gpt-5.4",
        provider="openai",
        reasoning_effort="medium",  # in passthrough
        max_retries=3,  # in passthrough
        temperature=0.5,  # NOT in passthrough — must be dropped
        top_p=0.9,  # NOT in passthrough
    )
    with patch("tradingagents.llm_clients.openai_client.NormalizedChatOpenAI") as mock_cls:
        client.get_llm()
    _args, kwargs = mock_cls.call_args
    assert kwargs["reasoning_effort"] == "medium"
    assert kwargs["max_retries"] == 3
    assert "temperature" not in kwargs
    assert "top_p" not in kwargs


# -- Validation --------------------------------------------------------------


@pytest.mark.unit
def test_validate_known_openai_model():
    client = OpenAIClient(model="gpt-5.4", provider="openai")
    assert client.validate_model() is True


@pytest.mark.unit
def test_validate_known_xai_model():
    client = OpenAIClient(model="grok-4-0709", provider="xai")
    assert client.validate_model() is True


@pytest.mark.unit
def test_validate_unknown_model_returns_false():
    client = OpenAIClient(model="not-a-real-model", provider="openai")
    assert client.validate_model() is False


@pytest.mark.unit
def test_provider_lowercased():
    """OpenAIClient lowercases the provider arg for case-insensitive lookup."""
    client = OpenAIClient(model="gpt-5.4", provider="OPENAI")
    assert client.provider == "openai"


# -- NormalizedChatOpenAI.with_structured_output -----------------------------


@pytest.mark.unit
def test_structured_output_defaults_to_function_calling():
    """Default method is function_calling (avoids the Pydantic serialization
    warnings from the Responses-API parse path)."""
    instance = NormalizedChatOpenAI.__new__(NormalizedChatOpenAI)
    schema = MagicMock()
    with patch.object(
        type(instance).__mro__[1],  # ChatOpenAI base
        "with_structured_output",
        return_value=MagicMock(),
    ) as mock_super:
        instance.with_structured_output(schema)
    _args, kwargs = mock_super.call_args
    assert kwargs["method"] == "function_calling"


@pytest.mark.unit
def test_structured_output_respects_explicit_method():
    """If the caller specifies method=, we don't override it."""
    instance = NormalizedChatOpenAI.__new__(NormalizedChatOpenAI)
    schema = MagicMock()
    with patch.object(
        type(instance).__mro__[1],
        "with_structured_output",
        return_value=MagicMock(),
    ) as mock_super:
        instance.with_structured_output(schema, method="json_schema")
    _args, kwargs = mock_super.call_args
    assert kwargs["method"] == "json_schema"

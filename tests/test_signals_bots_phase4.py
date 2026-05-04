"""Tests for spec 001 Phase 4 — per-bot LLM model routing."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tradingagents.signals.role_models import BotLLMFactory

pytestmark = pytest.mark.unit


# ---- Default-fallback behavior (no bot_models override) -------------------


def test_factory_returns_default_quick_when_bot_models_empty():
    """Empty bot_models → all bots get default_quick_llm."""
    quick = MagicMock(name="default_quick")
    deep = MagicMock(name="default_deep")
    factory = BotLLMFactory(
        config={"bot_models": {}, "llm_provider": "anthropic"},
        default_quick_llm=quick,
        default_deep_llm=deep,
    )
    assert factory.get_llm_for_bot("market") is quick
    assert factory.get_llm_for_bot("news") is quick


def test_factory_returns_default_deep_for_role_deep():
    """role='deep' → default_deep_llm when no override."""
    quick = MagicMock(name="default_quick")
    deep = MagicMock(name="default_deep")
    factory = BotLLMFactory(
        config={"bot_models": {}, "llm_provider": "anthropic"},
        default_quick_llm=quick,
        default_deep_llm=deep,
    )
    assert factory.get_llm_for_bot("portfolio_manager", role="deep") is deep
    assert factory.get_llm_for_bot("research_manager", role="deep") is deep


def test_factory_handles_missing_bot_models_key():
    """Config without 'bot_models' key → falls back to defaults."""
    quick = MagicMock(name="default_quick")
    factory = BotLLMFactory(
        config={"llm_provider": "anthropic"},
        default_quick_llm=quick,
        default_deep_llm=MagicMock(),
    )
    assert factory.get_llm_for_bot("market") is quick


def test_factory_handles_none_bot_models():
    """Config with bot_models=None → falls back to defaults (defensive)."""
    quick = MagicMock(name="default_quick")
    factory = BotLLMFactory(
        config={"bot_models": None, "llm_provider": "anthropic"},
        default_quick_llm=quick,
        default_deep_llm=MagicMock(),
    )
    assert factory.get_llm_for_bot("market") is quick


# ---- Per-bot override builds new client -----------------------------------


def test_factory_builds_client_when_bot_has_override():
    """A bot with an entry in bot_models gets a custom client built."""
    quick = MagicMock(name="default_quick")
    fake_client = MagicMock(name="fake_client_haiku")
    factory = BotLLMFactory(
        config={
            "bot_models": {"market": "claude-haiku-4-5"},
            "llm_provider": "anthropic",
        },
        default_quick_llm=quick,
        default_deep_llm=MagicMock(),
    )
    with patch(
        "tradingagents.signals.role_models.create_llm_client",
        return_value=fake_client,
    ) as mock_create:
        result = factory.get_llm_for_bot("market")
    assert result is fake_client
    mock_create.assert_called_once()
    # Ensure the right (provider, model) were passed
    args, kwargs = mock_create.call_args
    assert args[0] == "anthropic"
    assert args[1] == "claude-haiku-4-5"


def test_factory_caches_clients_across_bots():
    """Two bots configured for the same model share an instance."""
    factory = BotLLMFactory(
        config={
            "bot_models": {
                "market": "claude-haiku-4-5",
                "news": "claude-haiku-4-5",
            },
            "llm_provider": "anthropic",
        },
        default_quick_llm=MagicMock(),
        default_deep_llm=MagicMock(),
    )
    fake_client = MagicMock(name="haiku")
    with patch(
        "tradingagents.signals.role_models.create_llm_client",
        return_value=fake_client,
    ) as mock_create:
        client_market = factory.get_llm_for_bot("market")
        client_news = factory.get_llm_for_bot("news")
    # Same client instance (cache hit)
    assert client_market is client_news
    # create_llm_client called only ONCE (cached)
    assert mock_create.call_count == 1


def test_factory_builds_separate_clients_for_different_models():
    factory = BotLLMFactory(
        config={
            "bot_models": {
                "market": "claude-haiku-4-5",
                "fundamentals": "claude-opus-4-7",
            },
            "llm_provider": "anthropic",
        },
        default_quick_llm=MagicMock(),
        default_deep_llm=MagicMock(),
    )
    haiku = MagicMock(name="haiku")
    opus = MagicMock(name="opus")

    def fake_create(provider, model, **kwargs):
        return haiku if "haiku" in model else opus

    with patch(
        "tradingagents.signals.role_models.create_llm_client",
        side_effect=fake_create,
    ) as mock_create:
        client_market = factory.get_llm_for_bot("market")
        client_fund = factory.get_llm_for_bot("fundamentals")
    assert client_market is haiku
    assert client_fund is opus
    assert mock_create.call_count == 2


def test_factory_falls_back_to_default_for_unconfigured_bot():
    """Bot NOT in bot_models gets the default, even when other bots have overrides."""
    quick = MagicMock(name="default_quick")
    factory = BotLLMFactory(
        config={
            "bot_models": {"market": "claude-haiku-4-5"},
            "llm_provider": "anthropic",
        },
        default_quick_llm=quick,
        default_deep_llm=MagicMock(),
    )
    with patch(
        "tradingagents.signals.role_models.create_llm_client",
        return_value=MagicMock(),
    ):
        # market gets the override; news falls back to default_quick
        assert factory.get_llm_for_bot("news") is quick


# ---- Provider-specific kwargs forwarded ----------------------------------


def test_factory_forwards_anthropic_effort():
    factory = BotLLMFactory(
        config={
            "bot_models": {"market": "claude-opus-4-7"},
            "llm_provider": "anthropic",
            "anthropic_effort": "high",
        },
        default_quick_llm=MagicMock(),
        default_deep_llm=MagicMock(),
    )
    with patch(
        "tradingagents.signals.role_models.create_llm_client",
        return_value=MagicMock(),
    ) as mock_create:
        factory.get_llm_for_bot("market")
    args, kwargs = mock_create.call_args
    assert kwargs.get("effort") == "high"


def test_factory_forwards_openai_reasoning_effort():
    factory = BotLLMFactory(
        config={
            "bot_models": {"market": "gpt-5.4"},
            "llm_provider": "openai",
            "openai_reasoning_effort": "medium",
        },
        default_quick_llm=MagicMock(),
        default_deep_llm=MagicMock(),
    )
    with patch(
        "tradingagents.signals.role_models.create_llm_client",
        return_value=MagicMock(),
    ) as mock_create:
        factory.get_llm_for_bot("market")
    args, kwargs = mock_create.call_args
    assert kwargs.get("reasoning_effort") == "medium"


def test_factory_forwards_google_thinking_level():
    factory = BotLLMFactory(
        config={
            "bot_models": {"market": "gemini-3-flash"},
            "llm_provider": "google",
            "google_thinking_level": "high",
        },
        default_quick_llm=MagicMock(),
        default_deep_llm=MagicMock(),
    )
    with patch(
        "tradingagents.signals.role_models.create_llm_client",
        return_value=MagicMock(),
    ) as mock_create:
        factory.get_llm_for_bot("market")
    args, kwargs = mock_create.call_args
    assert kwargs.get("thinking_level") == "high"


def test_factory_forwards_backend_url():
    factory = BotLLMFactory(
        config={
            "bot_models": {"market": "deepseek-chat"},
            "llm_provider": "deepseek",
            "backend_url": "https://api.deepseek.com",
        },
        default_quick_llm=MagicMock(),
        default_deep_llm=MagicMock(),
    )
    with patch(
        "tradingagents.signals.role_models.create_llm_client",
        return_value=MagicMock(),
    ) as mock_create:
        factory.get_llm_for_bot("market")
    args, kwargs = mock_create.call_args
    assert kwargs.get("base_url") == "https://api.deepseek.com"


def test_factory_omits_thinking_kwargs_when_unset():
    """No anthropic_effort / openai_reasoning_effort / google_thinking_level
    in config → those kwargs are NOT passed to create_llm_client."""
    factory = BotLLMFactory(
        config={
            "bot_models": {"market": "claude-haiku-4-5"},
            "llm_provider": "anthropic",
        },
        default_quick_llm=MagicMock(),
        default_deep_llm=MagicMock(),
    )
    with patch(
        "tradingagents.signals.role_models.create_llm_client",
        return_value=MagicMock(),
    ) as mock_create:
        factory.get_llm_for_bot("market")
    args, kwargs = mock_create.call_args
    assert "effort" not in kwargs
    assert "reasoning_effort" not in kwargs
    assert "thinking_level" not in kwargs


# ---- model_for_bot reporting ---------------------------------------------


def test_model_for_bot_returns_override_when_set():
    factory = BotLLMFactory(
        config={
            "bot_models": {"market": "claude-haiku-4-5"},
            "llm_provider": "anthropic",
            "quick_think_llm": "claude-sonnet-4-6",
        },
        default_quick_llm=MagicMock(),
        default_deep_llm=MagicMock(),
    )
    assert factory.model_for_bot("market") == "claude-haiku-4-5"


def test_model_for_bot_returns_quick_default_when_unset():
    factory = BotLLMFactory(
        config={
            "bot_models": {},
            "llm_provider": "anthropic",
            "quick_think_llm": "claude-sonnet-4-6",
            "deep_think_llm": "claude-opus-4-7",
        },
        default_quick_llm=MagicMock(),
        default_deep_llm=MagicMock(),
    )
    assert factory.model_for_bot("news") == "claude-sonnet-4-6"


def test_model_for_bot_returns_deep_default_when_role_deep():
    factory = BotLLMFactory(
        config={
            "bot_models": {},
            "llm_provider": "anthropic",
            "quick_think_llm": "claude-sonnet-4-6",
            "deep_think_llm": "claude-opus-4-7",
        },
        default_quick_llm=MagicMock(),
        default_deep_llm=MagicMock(),
    )
    assert factory.model_for_bot("portfolio_manager", role="deep") == "claude-opus-4-7"


# ---- Integration with GraphSetup -----------------------------------------


def test_graph_setup_uses_factory_when_provided():
    """GraphSetup._llm_for routes through the factory when wired."""
    from tradingagents.graph.setup import GraphSetup

    quick = MagicMock(name="default_quick")
    deep = MagicMock(name="default_deep")
    fake_haiku = MagicMock(name="haiku")

    factory = BotLLMFactory(
        config={
            "bot_models": {"market": "claude-haiku-4-5"},
            "llm_provider": "anthropic",
        },
        default_quick_llm=quick,
        default_deep_llm=deep,
    )

    setup = GraphSetup(
        quick_thinking_llm=quick,
        deep_thinking_llm=deep,
        tool_nodes={},
        conditional_logic=MagicMock(),
        bot_llm_factory=factory,
    )

    with patch(
        "tradingagents.signals.role_models.create_llm_client",
        return_value=fake_haiku,
    ):
        market_llm = setup._llm_for("market")
        news_llm = setup._llm_for("news")
        pm_llm = setup._llm_for("portfolio_manager", role="deep")

    assert market_llm is fake_haiku  # override
    assert news_llm is quick  # default
    assert pm_llm is deep  # default deep


def test_graph_setup_uses_defaults_when_factory_none():
    """When bot_llm_factory=None, GraphSetup uses framework defaults
    (FR-007 backwards-compat — current production behavior)."""
    from tradingagents.graph.setup import GraphSetup

    quick = MagicMock(name="default_quick")
    deep = MagicMock(name="default_deep")

    setup = GraphSetup(
        quick_thinking_llm=quick,
        deep_thinking_llm=deep,
        tool_nodes={},
        conditional_logic=MagicMock(),
        bot_llm_factory=None,
    )
    assert setup._llm_for("market") is quick
    assert setup._llm_for("portfolio_manager", role="deep") is deep

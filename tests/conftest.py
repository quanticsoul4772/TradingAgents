"""Shared pytest fixtures that prevent CI hangs when API keys are absent."""

import os
from unittest.mock import MagicMock, patch

import pytest


def pytest_configure(config):
    for marker in ("unit", "integration", "smoke"):
        config.addinivalue_line("markers", f"{marker}: {marker}-level tests")


_API_KEY_ENV_VARS = (
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "XAI_API_KEY",
    "DEEPSEEK_API_KEY",
    "DASHSCOPE_API_KEY",
    "ZHIPU_API_KEY",
    "OPENROUTER_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "ALPHA_VANTAGE_API_KEY",
)


@pytest.fixture(autouse=True)
def _dummy_api_keys(monkeypatch):
    for env_var in _API_KEY_ENV_VARS:
        monkeypatch.setenv(env_var, os.environ.get(env_var, "placeholder"))


@pytest.fixture(autouse=True)
def _disable_spec_007_lazy_factory_call():
    """Globally disable spec 007's lazy `create_llm_client` import.

    Without this fixture, any test that triggers `evaluate_forward_catalyst`
    (e.g. via the PM hook chain) would attempt a real Anthropic Opus call
    if a real `ANTHROPIC_API_KEY` is present in the dev environment (which
    overrides conftest's `placeholder`-default). Spec 007 then catches the
    successful call's structured output, computes the bull/bear scores, and
    can legitimately fire — downgrading PM ratings non-deterministically
    and breaking tests that assert specific pre-spec-007 behavior.

    The patch makes `create_llm_client` raise; spec 007's `evaluate_forward_catalyst`
    catches and degrades cleanly to `skipped="llm_failed"` — no fire, no
    rating override, no API call, no test flake.

    Tests that exercise spec 007 directly bypass this patch by:
      - Passing `llm=mocked` to `evaluate_forward_catalyst` (used in
        `tests/test_forward_catalyst_filter.py` +
        `tests/test_forward_catalyst_filter_calendar_boost.py`), OR
      - Using a per-test `with patch("...create_llm_client", return_value=...)`
        context manager that overrides this autouse patch (used in
        `tests/test_portfolio_manager_filter_integration.py` for active-mode
        fire-decision tests).

    Without this autouse fixture, `test_memory_log.py::TestPortfolioManagerInjection
    ::test_pm_returns_rendered_markdown_with_rating` flakes when run after
    other test files that left some yfinance cache state — the spec 007 Opus
    call returns a high enough `bull_case_priced_in` score on the test's
    NVDA state to fire and downgrade Overweight → Hold.
    """
    with patch(
        "tradingagents.llm_clients.factory.create_llm_client",
        side_effect=RuntimeError("disabled by global conftest autouse fixture"),
    ):
        yield


@pytest.fixture()
def mock_llm_client():
    client = MagicMock()
    client.get_llm.return_value = MagicMock()
    with patch(
        "tradingagents.llm_clients.factory.create_llm_client",
        return_value=client,
    ):
        yield client

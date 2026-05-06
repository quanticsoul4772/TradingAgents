"""Tests for the overload-backoff helper in tradingagents/agents/utils/structured.py.

Added 2026-05-06 after experiment 2026-05-06-001-paper-harness-live-forward
observed 2/5 tickers lost to sustained Anthropic 529 overload. The single-retry
fallback couldn't cover sustained overload conditions; this module verifies the
new exponential-backoff retry triggers only on detected overload and propagates
real errors immediately.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tradingagents.agents.utils.structured import (
    _is_transient_overload,
    invoke_structured_or_freetext,
)


def _render(_):
    return "rendered output"


# -- _is_transient_overload classifier --------------------------------------


@pytest.mark.unit
def test_overload_detected_via_status_code_attribute():
    exc = Exception("oops")
    exc.status_code = 529
    assert _is_transient_overload(exc) is True


@pytest.mark.unit
def test_overload_detected_via_message_substring_529():
    exc = Exception("Error code: 529 - {'type': 'overloaded_error'}")
    assert _is_transient_overload(exc) is True


@pytest.mark.unit
def test_overload_detected_via_message_substring_overloaded():
    exc = Exception("API is overloaded right now")
    assert _is_transient_overload(exc) is True


@pytest.mark.unit
def test_non_overload_exception_not_detected():
    assert _is_transient_overload(ValueError("bad input")) is False
    assert _is_transient_overload(TimeoutError("slow")) is False


@pytest.mark.unit
def test_auth_error_not_detected_as_overload():
    exc = Exception("Error code: 401 - Unauthorized")
    assert _is_transient_overload(exc) is False


# -- invoke_structured_or_freetext with overload backoff --------------------


@pytest.mark.unit
def test_structured_call_succeeds_first_attempt_no_retry():
    structured = MagicMock()
    structured.invoke.return_value = MagicMock()
    result = invoke_structured_or_freetext(structured, MagicMock(), "prompt", _render, "Trader")
    assert result == "rendered output"
    structured.invoke.assert_called_once()


@pytest.mark.unit
def test_structured_call_retries_on_overload_then_succeeds():
    """First two structured calls hit 529; third succeeds."""
    structured = MagicMock()
    overload_exc = Exception("Error code: 529 - overloaded")
    structured.invoke.side_effect = [overload_exc, overload_exc, MagicMock()]

    with patch("tradingagents.agents.utils.structured.time.sleep") as sleep:
        result = invoke_structured_or_freetext(structured, MagicMock(), "p", _render, "Trader")
    assert result == "rendered output"
    assert structured.invoke.call_count == 3
    # Sleeps: first attempt (0s no-op), second (2s), third (8s) — only the
    # nonzero sleeps actually call time.sleep
    assert sleep.call_count == 2
    sleep.assert_any_call(2.0)
    sleep.assert_any_call(8.0)


@pytest.mark.unit
def test_structured_call_falls_to_freetext_after_exhausted_overload_retries():
    """4 structured 529s exhaust retries → falls to free-text path."""
    structured = MagicMock()
    structured.invoke.side_effect = Exception("Error code: 529 - overloaded")
    plain = MagicMock()
    plain_response = MagicMock()
    plain_response.content = "freetext content"
    plain.invoke.return_value = plain_response

    with patch("tradingagents.agents.utils.structured.time.sleep"):
        result = invoke_structured_or_freetext(structured, plain, "p", _render, "Trader")
    assert result == "freetext content"
    # 4 structured attempts (initial + 3 backoff retries), 1 freetext
    assert structured.invoke.call_count == 4
    plain.invoke.assert_called_once()


@pytest.mark.unit
def test_freetext_path_also_retries_on_overload():
    """Sustained overload on the free-text fallback also retries."""
    structured = MagicMock()
    structured.invoke.side_effect = ValueError(
        "malformed JSON"
    )  # non-overload → straight to freetext
    plain = MagicMock()
    overload_exc = Exception("Error code: 529 - overloaded")
    success_response = MagicMock()
    success_response.content = "freetext recovered"
    plain.invoke.side_effect = [overload_exc, success_response]

    with patch("tradingagents.agents.utils.structured.time.sleep"):
        result = invoke_structured_or_freetext(structured, plain, "p", _render, "Trader")
    assert result == "freetext recovered"
    assert plain.invoke.call_count == 2


@pytest.mark.unit
def test_non_overload_structured_error_falls_through_immediately_no_retry():
    """Real errors (e.g. malformed JSON from a weak model) skip the backoff."""
    structured = MagicMock()
    structured.invoke.side_effect = ValueError("malformed JSON")
    plain = MagicMock()
    plain_response = MagicMock()
    plain_response.content = "freetext"
    plain.invoke.return_value = plain_response

    with patch("tradingagents.agents.utils.structured.time.sleep") as sleep:
        result = invoke_structured_or_freetext(structured, plain, "p", _render, "Trader")
    assert result == "freetext"
    assert structured.invoke.call_count == 1  # NO retry; ValueError isn't overload
    sleep.assert_not_called()


@pytest.mark.unit
def test_no_structured_llm_uses_freetext_with_backoff():
    """structured_llm=None uses free-text path which still gets backoff."""
    plain = MagicMock()
    overload_exc = Exception("Error code: 529 - overloaded")
    success = MagicMock()
    success.content = "freetext"
    plain.invoke.side_effect = [overload_exc, success]

    with patch("tradingagents.agents.utils.structured.time.sleep"):
        result = invoke_structured_or_freetext(None, plain, "p", _render, "Trader")
    assert result == "freetext"
    assert plain.invoke.call_count == 2


@pytest.mark.unit
def test_exhausted_overload_retries_propagate_final_exception():
    """If both structured AND free-text exhaust overload retries, the final
    overload exception propagates (matches prior behavior of letting upstream
    record an errored row)."""
    structured = MagicMock()
    structured.invoke.side_effect = Exception("Error code: 529 - overloaded")
    plain = MagicMock()
    plain.invoke.side_effect = Exception("Error code: 529 - overloaded")

    with patch("tradingagents.agents.utils.structured.time.sleep"):
        with pytest.raises(Exception, match="529"):
            invoke_structured_or_freetext(structured, plain, "p", _render, "Trader")

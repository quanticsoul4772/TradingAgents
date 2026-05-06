"""Shared helpers for invoking an agent with structured output and a graceful fallback.

The Portfolio Manager, Trader, and Research Manager all follow the same
canonical pattern:

1. At agent creation, wrap the LLM with ``with_structured_output(Schema)``
   so the model returns a typed Pydantic instance. If the provider does
   not support structured output (rare; mostly older Ollama models), the
   wrap is skipped and the agent uses free-text generation instead.
2. At invocation, run the structured call and render the result back to
   markdown. If the structured call itself fails for any reason
   (malformed JSON from a weak model, transient provider issue), fall
   back to a plain ``llm.invoke`` so the pipeline never blocks.

Centralising the pattern here keeps the agent factories small and ensures
all three agents log the same warnings when fallback fires.

**Overload backoff** (added 2026-05-06 after experiment 2026-05-06-001
observed 2/5 tickers lost to sustained Anthropic 529 overload): both the
structured call and the free-text fallback are wrapped in a 3-attempt
exponential-backoff retry that fires only on detected transient overload
(HTTP 529 / "overloaded" in the exception message). Real errors (auth,
malformed JSON, etc.) fast-fail without retry as before.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Backoff schedule for transient overload retries: 2s, 8s, 32s between attempts.
# Total worst-case latency: ~42s + the underlying call time. Tuned for Anthropic
# 529s which typically resolve within seconds of the failing request.
_OVERLOAD_BACKOFF_SCHEDULE = (2.0, 8.0, 32.0)


def _is_transient_overload(exc: BaseException) -> bool:
    """True iff exc looks like a transient API-overload condition worth retrying.

    Detected via:
      - ``status_code == 529`` attribute (anthropic SDK)
      - "529" or "overloaded" in str(exc) (broader catch for langchain-wrapped
        or HTTP-client variants)
    Real errors (auth 401, bad request 400, malformed JSON, etc.) return False.
    """
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if status == 529:
        return True
    msg = str(exc).lower()
    return "529" in msg or "overloaded" in msg


def _invoke_with_overload_backoff(llm: Any, prompt: Any, agent_name: str, label: str) -> Any:
    """Invoke ``llm`` with exponential-backoff retries on 529/overload.

    Non-overload exceptions propagate immediately. The final attempt's
    exception (if any) propagates to the caller.
    """
    last_exc: BaseException | None = None
    for attempt, sleep_s in enumerate((0.0,) + _OVERLOAD_BACKOFF_SCHEDULE, start=1):
        if sleep_s > 0:
            logger.warning(
                "%s: %s overload retry %d after %.0fs sleep",
                agent_name,
                label,
                attempt - 1,
                sleep_s,
            )
            time.sleep(sleep_s)
        try:
            return llm.invoke(prompt)
        except Exception as exc:
            last_exc = exc
            if not _is_transient_overload(exc):
                raise
    assert last_exc is not None  # for type checkers
    raise last_exc


def bind_structured(llm: Any, schema: type[T], agent_name: str) -> Any | None:
    """Return ``llm.with_structured_output(schema)`` or ``None`` if unsupported.

    Logs a warning when the binding fails so the user understands the agent
    will use free-text generation for every call instead of one-shot fallback.
    """
    try:
        return llm.with_structured_output(schema)
    except (NotImplementedError, AttributeError) as exc:
        logger.warning(
            "%s: provider does not support with_structured_output (%s); "
            "falling back to free-text generation",
            agent_name,
            exc,
        )
        return None


def invoke_structured_or_freetext(
    structured_llm: Any | None,
    plain_llm: Any,
    prompt: Any,
    render: Callable[[T], str],
    agent_name: str,
) -> str:
    """Run the structured call and render to markdown; fall back to free-text on any failure.

    Both the structured call and the free-text fallback are wrapped in
    exponential-backoff retry on transient API overload (HTTP 529 /
    "overloaded"). Other exceptions fall through to the free-text path or
    propagate, matching prior behavior.
    """
    if structured_llm is not None:
        try:
            result = _invoke_with_overload_backoff(
                structured_llm, prompt, agent_name, "structured-output"
            )
            return render(result)
        except Exception as exc:
            logger.warning(
                "%s: structured-output invocation failed (%s); retrying once as free text",
                agent_name,
                exc,
            )

    response = _invoke_with_overload_backoff(plain_llm, prompt, agent_name, "free-text")
    return response.content

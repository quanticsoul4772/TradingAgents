"""Spec 001 Phase 3 — per-bot token budget tracker.

Reservation-based usage tracking. Per spec FR-005: when a bot exceeds its
configured token budget, it MUST emit ``Signal(abstain=True)`` and log a
``BudgetExceeded`` warning. This module ships the deterministic tracker
(no LLM-call instrumentation yet); wiring into the analyst factories is
deferred to Phase 3.5.

Usage::

    budget = BotBudget({"market": 5000, "fundamentals": 8000})
    if budget.can_reserve("market"):
        reservation = budget.reserve("market")
        # ... call LLM ...
        budget.record(reservation, prompt_tokens=1500, completion_tokens=2000)
    else:
        # over budget — return an abstaining Signal instead
        return Signal(bot_id="market", direction=0, magnitude=0, abstain=True)

The tracker is intentionally pure data + simple methods. The "what to do
when over budget" decision is the caller's — keeping policy out of the
tracker makes it composable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class BudgetReservation:
    """Returned by ``BotBudget.reserve(bot_id)``. Caller passes this back to
    ``budget.record(reservation, prompt_tokens, completion_tokens)`` after the
    LLM call completes.
    """

    bot_id: str
    reservation_id: int  # opaque; used only for double-record detection


@dataclass
class BudgetExceeded(Warning):
    """Raised (as a logged warning, not an exception) when a bot tries to
    reserve beyond its configured budget. Caller decides whether to abstain
    or proceed anyway.
    """

    bot_id: str
    requested: int  # implicit reservation cost; default 0 (advisory)
    used_so_far: int
    limit: int


@dataclass
class BotBudget:
    """Per-bot token-spend tracker.

    Configured per-propagate via ``config["bot_budgets"]``. ``record`` accepts
    prompt_tokens + completion_tokens separately for diagnostics; the budget
    check uses the sum.
    """

    limits: dict[str, int]
    used: dict[str, int] = field(default_factory=dict)
    by_bot_calls: dict[str, int] = field(default_factory=dict)
    _next_reservation_id: int = 0
    _open_reservations: dict[int, str] = field(default_factory=dict)

    def can_reserve(self, bot_id: str) -> bool:
        """Cheap check: is this bot's used-spend below its limit?

        Returns True for bots without a configured limit (unbudgeted).
        """
        limit = self.limits.get(bot_id)
        if limit is None:
            return True  # no limit set → unconstrained
        return self.used.get(bot_id, 0) < limit

    def reserve(self, bot_id: str) -> BudgetReservation:
        """Open a reservation. Caller must close via ``record()`` after the LLM
        call completes (with the actual token counts).

        If the bot is already over budget, logs a BudgetExceeded warning but
        still returns a reservation — the policy decision is the caller's.
        """
        if not self.can_reserve(bot_id):
            warning = BudgetExceeded(
                bot_id=bot_id,
                requested=0,
                used_so_far=self.used.get(bot_id, 0),
                limit=self.limits.get(bot_id, 0),
            )
            logger.warning(
                "BudgetExceeded: bot=%s used=%d limit=%d (caller decides whether to proceed)",
                warning.bot_id,
                warning.used_so_far,
                warning.limit,
            )
        self._next_reservation_id += 1
        rid = self._next_reservation_id
        self._open_reservations[rid] = bot_id
        return BudgetReservation(bot_id=bot_id, reservation_id=rid)

    def record(
        self,
        reservation: BudgetReservation,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        """Close a reservation by recording actual token counts.

        Idempotent on double-record (warns + skips). Total tokens = prompt +
        completion are added to the bot's running usage.
        """
        if reservation.reservation_id not in self._open_reservations:
            logger.warning(
                "BotBudget.record called with closed/unknown reservation %d (bot=%s); skipping",
                reservation.reservation_id,
                reservation.bot_id,
            )
            return

        bot_id = reservation.bot_id
        total = max(0, prompt_tokens) + max(0, completion_tokens)
        self.used[bot_id] = self.used.get(bot_id, 0) + total
        self.by_bot_calls[bot_id] = self.by_bot_calls.get(bot_id, 0) + 1
        self._open_reservations.pop(reservation.reservation_id)

    def remaining(self, bot_id: str) -> int | None:
        """How many tokens are left for this bot? None = no limit set."""
        limit = self.limits.get(bot_id)
        if limit is None:
            return None
        return max(0, limit - self.used.get(bot_id, 0))

    def summary(self) -> dict[str, dict]:
        """Per-bot usage summary for state log persistence.

        Returns ``{bot_id: {used, limit, calls, remaining, exceeded}}``.
        """
        out: dict[str, dict] = {}
        all_bots = set(self.limits) | set(self.used) | set(self.by_bot_calls)
        for bot in sorted(all_bots):
            limit = self.limits.get(bot)
            used = self.used.get(bot, 0)
            out[bot] = {
                "used": used,
                "limit": limit,
                "calls": self.by_bot_calls.get(bot, 0),
                "remaining": (max(0, limit - used) if limit is not None else None),
                "exceeded": (limit is not None and used > limit),
            }
        return out

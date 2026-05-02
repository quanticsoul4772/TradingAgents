"""Parse and apply --config-override KEY=VALUE flags.

Coercion order per research.md R-003:
    int -> float -> bool ("true"/"false") -> null ("none"/"null") -> str.
Quoted values (KEY="42") skip coercion.

See specs/001-experiments-scaffolding/contracts/backtest_extensions.md.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _coerce(raw: str) -> Any:
    """Apply the R-003 coercion ladder to a raw string value."""
    # Quoted-string escape hatch: KEY="..." is always a string, no coercion.
    if len(raw) >= 2 and raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]

    # int
    try:
        return int(raw)
    except ValueError:
        pass

    # float
    try:
        return float(raw)
    except ValueError:
        pass

    # bool
    lower = raw.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False

    # null
    if lower in ("none", "null"):
        return None

    # fallback
    return raw


def parse_override(spec: str) -> tuple[str, Any]:
    """Parse a single 'KEY=VALUE' string into (key, coerced_value).

    Raises ValueError if the spec lacks an '=' or has an empty key.
    """
    if "=" not in spec:
        raise ValueError(
            f"Invalid --config-override {spec!r}: must contain '=' (e.g. KEY=VALUE)."
        )
    key, _, raw = spec.partition("=")
    key = key.strip()
    if not key:
        raise ValueError(f"Invalid --config-override {spec!r}: empty key.")
    return key, _coerce(raw)


def apply_overrides(
    config: dict[str, Any],
    overrides: list[str],
    allow_unknown: bool = True,
) -> dict[str, Any]:
    """Return a copy of `config` with parsed `overrides` applied on top.

    If `allow_unknown` is False and an override key is not already in `config`,
    raises ValueError. Otherwise emits a logger warning and applies anyway.
    The returned dict is a shallow copy; the original is not mutated.
    """
    out = dict(config)
    for spec in overrides:
        key, value = parse_override(spec)
        if key not in out:
            if not allow_unknown:
                raise ValueError(
                    f"Unknown config key {key!r} in --config-override; "
                    f"known keys: {sorted(out)}."
                )
            logger.warning(
                "--config-override %s=%r adds an unknown config key; "
                "applying anyway (allow_unknown=True).",
                key, value,
            )
        out[key] = value
    return out


def overrides_as_dict(overrides: list[str]) -> dict[str, Any]:
    """Parse `overrides` into a {key: coerced_value} dict, no merge."""
    return dict(parse_override(s) for s in overrides)

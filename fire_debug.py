"""
Optional diagnostics for the FIRE calculator pipeline.

Enable with environment variable:
  FIRE_CALC_DEBUG=1

Logs go to stderr via the ``fire_calc`` logger (INFO-level lines when debug is on).
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

LOG = logging.getLogger("fire_calc")

VERBOSE_JSON_MAX = 12000


def is_debug() -> bool:
    return os.environ.get("FIRE_CALC_DEBUG", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def configure() -> None:
    """Attach a stderr handler once when debug mode is enabled."""
    if not is_debug():
        return
    LOG.setLevel(logging.INFO)
    if LOG.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(levelname)s [fire_calc] %(message)s")
    )
    LOG.addHandler(handler)
    LOG.propagate = False


def log_event(stage: str, **fields: Any) -> None:
    """Structured one-line log for tracing life-event / simulation flow."""
    if not is_debug():
        return
    parts = [f"{stage}"] + [f"{k}={_fmt(v)}" for k, v in sorted(fields.items())]
    LOG.info(" | ".join(parts))


def log_verbose_bundle(stage: str, payload: Dict[str, Any]) -> None:
    """Multi-line JSON dump for debugging stale Dash State / cache issues."""
    if not is_debug():
        return
    try:
        blob = json.dumps(payload, indent=2, default=str, sort_keys=True)
    except TypeError:
        blob = repr(payload)
    raw_len = len(blob)
    if raw_len > VERBOSE_JSON_MAX:
        blob = (
            blob[:VERBOSE_JSON_MAX]
            + f"\n... [truncated; raw length was {raw_len} chars]\n"
        )
    LOG.info("[fire_calc] ========== VERBOSE %s ==========\n%s", stage, blob)
    LOG.info("[fire_calc] ========== END %s ==========", stage)


def log_callback_context(stage: str) -> None:
    """Log Dash ``ctx.triggered`` (which inputs fired). Import-safe for tests."""
    if not is_debug():
        return
    try:
        from dash import ctx  # type: ignore
    except ImportError:
        return
    triggered = getattr(ctx, "triggered", None) or []
    rows = []
    for t in triggered:
        pid = t.get("prop_id", "")
        val = t.get("value")
        rows.append(f"{pid} -> {_fmt(val)}")
    tid = getattr(ctx, "triggered_id", None)
    LOG.info(
        "[fire_calc] ctx | %s | triggered_id=%s | %s",
        stage,
        repr(tid),
        " ; ".join(rows) if rows else "(empty)",
    )


def _fmt(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:.6g}"
    if isinstance(v, dict):
        return str({k: _fmt(x) for k, x in v.items()})
    return repr(v)


configure()

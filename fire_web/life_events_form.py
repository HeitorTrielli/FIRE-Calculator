"""Parsing and validation for life-event modal inputs."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from fire_web.simulation import FINANCIAL_LIFE_KEYS


def parse_optional_float(raw: Any) -> Optional[float]:
    """Parse sidebar numbers; accepts commas / ``$``."""
    if raw is None or raw == "":
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip().replace(",", "").replace("$", "")
    if s == "" or s.lower() in ("nan", "inf", "-inf"):
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def life_event_row_from_inputs(
    future_year: Any,
    event_name: Any,
    inc: Any,
    exp: Any,
    nw: Any,
    ret_pct: Any,
    lump: Any,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Build a stored life-event dict (display format) or return an error message."""
    try:
        fy = int(future_year)
    except (TypeError, ValueError):
        return None, "Invalid year."

    params: Dict[str, Any] = {"year": fy}
    oi = parse_optional_float(inc)
    if oi is not None:
        params["yearly_income"] = oi
    oe = parse_optional_float(exp)
    if oe is not None:
        params["yearly_expenses"] = oe
    on = parse_optional_float(nw)
    if on is not None:
        params["non_wage_income"] = on
    or_pct = parse_optional_float(ret_pct)
    if or_pct is not None:
        params["annual_return_rate"] = or_pct / 100.0
    ol = parse_optional_float(lump)
    if ol is not None and ol != 0:
        params["lump_sum"] = ol

    if event_name is not None and event_name != "":
        nm = str(event_name).strip()
        if nm:
            params["name"] = nm

    if not FINANCIAL_LIFE_KEYS.intersection(params.keys()):
        return (
            None,
            "Add at least one financial change (income, expenses, returns, lump sum, …).",
        )

    display_params = params.copy()
    if "annual_return_rate" in display_params:
        display_params["annual_return_rate"] = round(
            display_params["annual_return_rate"] * 100.0, 2
        )
    return display_params, None


_parse_optional_float = parse_optional_float
_life_event_row_from_inputs = life_event_row_from_inputs

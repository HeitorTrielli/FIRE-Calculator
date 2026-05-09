"""Simulation orchestration, charts, and results table formatting."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go

from fire_calculator import FIRECalculator
from fire_debug import log_event, log_verbose_bundle
from fire_state import FIREState, FIREStateManager
from fire_web.constants import OVERLAY_COLORS

# Stored on life-event dicts but not passed to FIREStateManager.add_future_state
LIFE_EVENT_META_KEYS = frozenset({"name"})
FINANCIAL_LIFE_KEYS = frozenset(
    {
        "yearly_income",
        "yearly_expenses",
        "annual_return_rate",
        "non_wage_income",
        "lump_sum",
        "inflation_rate",
    }
)


RETIREMENT_LIFE_EVENT_NAME = "Retirement year"


def is_retirement_life_event_name(name: Any) -> bool:
    return str(name or "").strip().lower() == RETIREMENT_LIFE_EVENT_NAME.lower()


def sort_life_events_chronologically(
    events: Optional[List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Sort life events by ``year`` (years from now) ascending."""

    def _year_key(ev: Dict[str, Any]) -> int:
        try:
            return int(ev.get("year", 0))
        except (TypeError, ValueError):
            return 0

    return sorted(copy.deepcopy(events or []), key=_year_key)


def build_simulation(
    initial_balance: float,
    yearly_income: float,
    yearly_expenses: float,
    annual_return_rate: float,
    inflation_rate: float,
    non_wage_income: float,
    future_states: List[Dict[str, Any]],
    max_years: int,
) -> Tuple[Dict[str, Any], FIREStateManager]:
    manager = FIREStateManager()
    calc = FIRECalculator(manager)

    initial_state = FIREState.create_initial_state(
        initial_balance=initial_balance,
        yearly_income=yearly_income,
        yearly_expenses=yearly_expenses,
        annual_return_rate=annual_return_rate,
        inflation_rate=inflation_rate,
        non_wage_income=non_wage_income,
        retirement_year=None,
    )
    manager.add_initial_state(initial_state)

    log_event(
        "build_simulation:start",
        initial_balance=initial_balance,
        yearly_expenses=yearly_expenses,
        yearly_income=yearly_income,
        max_years=max_years,
        n_future_states=len(future_states or []),
    )
    log_verbose_bundle(
        "build_simulation:future_states_argument",
        {
            "future_states_passed_to_engine": list(future_states or []),
            "repr_future_states": repr(future_states),
        },
    )

    for fs in future_states:
        params = {
            k: v
            for k, v in fs.items()
            if k != "year" and k not in LIFE_EVENT_META_KEYS and v is not None
        }
        if "annual_return_rate" in params:
            ar = float(params["annual_return_rate"])
            params["annual_return_rate"] = ar / 100.0 if ar > 1.0 else ar
        if params:
            y = int(float(fs["year"]))
            manager.add_future_state(year=y, **params)
            st = manager.get_state_at_year(y)
            log_event(
                "build_simulation:registered_future_state",
                year=y,
                params=params,
                state_yearly_expenses=st.yearly_expenses if st else None,
                state_yearly_income=st.yearly_income if st else None,
            )

    results = calc.calculate_until_year(max_years)
    milestones = calc.calculate_million_dollar_milestones(results)

    init = manager.get_state_at_year(0)
    payload = {
        "results": results,
        "milestones": milestones,
        "max_years": max_years,
        "initial": {
            "balance": init.balance if init else 0.0,
            "yearly_income": init.yearly_income if init else 0.0,
            "non_wage_income": init.non_wage_income if init else 0.0,
            "yearly_expenses": init.yearly_expenses if init else 0.0,
            "lump_sum": init.lump_sum if init else 0.0,
        },
    }
    return payload, manager


def sim_from_scenario(s: Dict[str, Any], max_years: int) -> Dict[str, Any]:
    i = s["initial_state"]
    fs = sort_life_events_chronologically(s.get("life_events"))
    payload, _ = build_simulation(
        i["initial_balance"],
        i["yearly_income"],
        i["yearly_expenses"],
        i["annual_return_rate"],
        i["inflation_rate"],
        i["non_wage_income"],
        fs,
        max_years,
    )
    return payload


def _hex_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Parse ``#RRGGBB`` or ``#RGB`` to RGB ints."""
    raw = hex_color.strip().lstrip("#").lower()
    if len(raw) == 6:
        return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
    if len(raw) == 3:
        return (
            int(raw[0] + raw[0], 16),
            int(raw[1] + raw[1], 16),
            int(raw[2] + raw[2], 16),
        )
    return (88, 166, 255)


def _rgba(rgb: Tuple[int, int, int], a: float) -> str:
    r, g, b = rgb
    return f"rgba({r},{g},{b},{max(0.0, min(1.0, a)):.3f})"


def _max_balance_across_payloads(payloads: List[Dict[str, Any]]) -> float:
    mx = 0.0
    for pl in payloads:
        ini = pl["initial"]
        rs: List[Dict[str, Any]] = pl["results"]
        vals = [float(ini["balance"])] + [float(r["balance"]) for r in rs]
        if vals:
            mx = max(mx, max(vals))
    return mx


def _max_year_across_payloads(payloads: List[Dict[str, Any]]) -> int:
    mx = 1
    for pl in payloads:
        for r in pl.get("results") or []:
            try:
                mx = max(mx, int(r["year"]))
            except (KeyError, TypeError, ValueError):
                continue
    return mx


def _life_event_label_half_width_years(text: str, x_span: float) -> float:
    """Rough horizontal half-width of the label in x-axis (year) units for overlap checks."""
    n = max(4, len(text.strip()))
    per = max(x_span, 1.0) * 0.0078
    return max(1.4, min(max(x_span, 1.0) * 0.16, n * per))


def _assign_life_event_vertical_tiers(
    events: List[Tuple[int, str]],
    x_span: float,
) -> List[int]:
    """Greedy stacking: same tier only if estimated label boxes do not overlap on the x-axis."""
    if not events:
        return []
    span = max(1.0, float(x_span))
    occupied: Dict[int, List[Tuple[float, float]]] = {}
    tiers: List[int] = []
    for x, label in events:
        xf = float(x)
        hw = _life_event_label_half_width_years(label, span)
        t = 0
        while True:
            bucket = occupied.setdefault(t, [])
            if not any(abs(xf - ox) < (hw + ohw) for (ox, ohw) in bucket):
                bucket.append((xf, hw))
                tiers.append(t)
                break
            t += 1
    return tiers


def _life_event_chart_x(policy_year: int) -> int:
    """Horizontal position for a life event on the balance chart.

    ``(x, balance)`` uses ``x = 0`` for today and ``x = k`` for the balance at the
    **end** of simulation year ``k``. A row stored as ``year = N`` first changes
    cash flows on the step **into** year ``N`` (the segment from ``N-1`` to ``N``).
    Draw the marker at ``N - 1`` so it marks the **beginning** of year ``N``,
    aligned with that inflection.
    """
    return max(0, int(policy_year) - 1)


def _life_event_sorted_year_labels(pl: Dict[str, Any]) -> List[Tuple[int, str]]:
    out: List[Tuple[int, str]] = []
    for ev in sorted(
        pl.get("life_events_display") or [],
        key=lambda x: int(x.get("year", 0)),
    ):
        try:
            y_ev = int(ev["year"])
        except (KeyError, TypeError, ValueError):
            continue
        raw = (ev.get("name") or "").strip()
        ann = raw if raw else f"Life event (year {y_ev})"
        out.append((y_ev, ann))
    return out


def _life_event_tiers_per_payload(
    payloads: List[Dict[str, Any]],
    x_span: float,
) -> List[List[int]]:
    """Tiers aligned with ``_life_event_sorted_year_labels(pl)`` for each payload (global x layout)."""
    per_pl: List[List[Tuple[int, str]]] = [
        _life_event_sorted_year_labels(pl) for pl in payloads
    ]
    flat: List[Tuple[int, str, int, int, int]] = []
    for pl_idx, items in enumerate(per_pl):
        for j, pair in enumerate(items):
            y_pol = pair[0]
            x_plot = _life_event_chart_x(y_pol)
            flat.append((x_plot, pair[1], pl_idx, j, y_pol))
    flat.sort(key=lambda r: (r[0], r[2], r[3]))
    tiers_flat = _assign_life_event_vertical_tiers(
        [(x_plot, ann) for x_plot, ann, _, _, _ in flat],
        x_span,
    )
    out: List[List[int]] = [[0] * len(items) for items in per_pl]
    for tier, (_, _, pl_idx, j, _) in zip(tiers_flat, flat):
        out[pl_idx][j] = tier
    return out


def _markers_legend_proxy(markers_legendgroup: str, legend_name: str) -> go.Scatter:
    """Invisible trace so life-event markers share one legend row per scenario."""
    return go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker=dict(size=0.01, opacity=0),
        name=legend_name,
        legendgroup=markers_legendgroup,
        showlegend=True,
        hoverinfo="skip",
    )


def _add_milestone_and_life_traces(
    fig: go.Figure,
    pl: Dict[str, Any],
    markers_legendgroup: str,
    y_min: float,
    y_max: float,
    scenario_rgb: Tuple[int, int, int],
    x_span_years: float,
    life_event_tiers: List[int],
    life_label_dy: float,
) -> int:
    """Add vertical life-event markers tinted like the scenario balance line.

    Markers use ``_life_event_chart_x`` so a stored policy year ``N`` sits at the
    start of simulation year ``N`` on the axis. Text is stacked when labels overlap.
    """
    rgb = scenario_rgb
    ev_line = _rgba(rgb, 0.58)
    ev_text = _rgba(rgb, 0.93)

    added = 0
    life_rows = _life_event_sorted_year_labels(pl)
    tiers = (
        life_event_tiers
        if len(life_event_tiers) == len(life_rows)
        else _assign_life_event_vertical_tiers(
            [(max(0, y - 1), ann) for y, ann in life_rows],
            max(1.0, float(x_span_years)),
        )
    )
    for tier, (y_ev, ann) in zip(tiers, life_rows):
        x_line = _life_event_chart_x(y_ev)
        y_text = y_max + (float(tier) + 1.0) * life_label_dy
        fig.add_trace(
            go.Scatter(
                x=[x_line, x_line],
                y=[y_min, y_max],
                mode="lines",
                name="",
                line=dict(color=ev_line, width=1, dash="dot"),
                legendgroup=markers_legendgroup,
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[x_line],
                y=[y_text],
                mode="text",
                text=[ann],
                textposition="top center",
                legendgroup=markers_legendgroup,
                showlegend=False,
                textfont=dict(color=ev_text, size=11),
                hoverinfo="skip",
                cliponaxis=False,
            )
        )
        added += 1
    return added


def build_figure(
    payload: Dict[str, Any],
    balance_overlays: Optional[List[Tuple[str, str, Dict[str, Any]]]] = None,
) -> go.Figure:
    """Nominal balance with optional compare overlays.

    Each scenario has two legend groups: **balance line** (``L:…``) and **life-event
    markers** (``M:…``). With ``legend.groupclick`` = ``togglegroup``, you can hide
    the line only, or only the vertical markers, independently.
    """
    fig = go.Figure()

    payloads_for_range: List[Dict[str, Any]]
    if balance_overlays:
        payloads_for_range = [pl for (_, _, pl) in balance_overlays]
    else:
        payloads_for_range = [payload]

    y_max = _max_balance_across_payloads(payloads_for_range) * 1.06
    if y_max <= 0:
        y_max = 1.0
    y_min = 0.0

    x_span_years = max(1.0, float(_max_year_across_payloads(payloads_for_range)))
    life_tier_lists = _life_event_tiers_per_payload(payloads_for_range, x_span_years)
    max_life_tier = max((max(ts) for ts in life_tier_lists if ts), default=-1)
    life_label_dy = (y_max - y_min) * 0.042
    life_label_y_pad = (
        (float(max_life_tier) + 1.0) * life_label_dy + (y_max - y_min) * 0.028
        if max_life_tier >= 0
        else 0.0
    )

    if balance_overlays:
        for i, (label, scenario_id, pl) in enumerate(balance_overlays):
            rs = pl["results"]
            ini = pl["initial"]
            oy = [0] + [x["year"] for x in rs]
            ob = [ini["balance"]] + [x["balance"] for x in rs]
            color = OVERLAY_COLORS[i % len(OVERLAY_COLORS)]
            rgb = _hex_rgb(color)
            sid = str(scenario_id)
            line_lg = f"L:{sid}"
            markers_lg = f"M:{sid}"
            fig.add_trace(
                go.Scatter(
                    x=oy,
                    y=ob,
                    name=label,
                    mode="lines",
                    line=dict(color=color),
                    legendgroup=line_lg,
                ),
            )
            n_mark = _add_milestone_and_life_traces(
                fig,
                pl,
                markers_lg,
                y_min,
                y_max,
                rgb,
                x_span_years,
                life_tier_lists[i],
                life_label_dy,
            )
            if n_mark > 0:
                fig.add_trace(
                    _markers_legend_proxy(
                        markers_lg,
                        f"{label} — life events",
                    )
                )
    else:
        results: List[Dict[str, Any]] = payload["results"]
        initial = payload["initial"]
        years = [0] + [r["year"] for r in results]
        balances = [initial["balance"]] + [r["balance"] for r in results]
        line_lg = "L:single"
        markers_lg = "M:single"
        fig.add_trace(
            go.Scatter(
                x=years,
                y=balances,
                name="Balance (nominal)",
                mode="lines",
                line=dict(color="#58a6ff"),
                legendgroup=line_lg,
            ),
        )
        n_mark = _add_milestone_and_life_traces(
            fig,
            payload,
            markers_lg,
            y_min,
            y_max,
            _hex_rgb(OVERLAY_COLORS[0]),
            x_span_years,
            life_tier_lists[0],
            life_label_dy,
        )
        if n_mark > 0:
            fig.add_trace(
                _markers_legend_proxy(markers_lg, "Life events")
            )

    fig.update_layout(
        template="plotly_dark",
        title="Nominal balance over time",
        height=480,
        showlegend=True,
        legend=dict(groupclick="togglegroup"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(
        title_text="Balance ($)",
        tickformat=",",
        range=[y_min, y_max + life_label_y_pad],
    )
    return fig


def format_results_table(payload: Dict[str, Any]) -> pd.DataFrame:
    initial = payload["initial"]
    results: List[Dict[str, Any]] = payload["results"]

    row0 = {
        "year": 0,
        "balance": initial["balance"],
        "yearly_return": 0.0,
        "yearly_income": initial["yearly_income"] + initial["non_wage_income"],
        "yearly_expenses": initial["yearly_expenses"],
        "lump_sum": initial["lump_sum"],
    }
    df = pd.DataFrame([row0] + results)
    df = df.set_index("year")
    df["balance"] = df["balance"].map(lambda x: f"${x:,.0f}")
    df["yearly_income"] = df["yearly_income"].map(lambda x: f"${x:,.0f}")
    df["yearly_expenses"] = df["yearly_expenses"].map(lambda x: f"${x:,.0f}")
    df["yearly_return"] = df["yearly_return"].map(lambda x: f"${x:,.0f}")
    df["lump_sum"] = df["lump_sum"].map(lambda x: f"${x:,.0f}" if x != 0 else "-")
    df.columns = [c.replace("_", " ").title() for c in df.columns]
    return df


_sort_life_events_chronologically = sort_life_events_chronologically
_sim_from_scenario = sim_from_scenario

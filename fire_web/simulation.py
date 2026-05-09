"""Simulation orchestration, charts, and results table formatting."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    retirement_year: int,
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
        retirement_year=retirement_year,
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
    payload, _ = build_simulation(
        i["initial_balance"],
        i["yearly_income"],
        i["yearly_expenses"],
        i["annual_return_rate"],
        i["inflation_rate"],
        i["non_wage_income"],
        i["retirement_year"],
        s["life_events"],
        max_years,
    )
    return payload


def build_figure(
    payload: Dict[str, Any],
    balance_overlays: Optional[List[Tuple[str, Dict[str, Any]]]] = None,
) -> go.Figure:
    results: List[Dict[str, Any]] = payload["results"]
    milestones: List[Dict[str, Any]] = payload["milestones"]
    initial = payload["initial"]

    years = [0] + [r["year"] for r in results]
    balances = [initial["balance"]] + [r["balance"] for r in results]
    incomes = [
        initial["yearly_income"] + initial["non_wage_income"]
    ] + [r["yearly_income"] for r in results]
    expenses = [initial["yearly_expenses"]] + [r["yearly_expenses"] for r in results]
    lump_sums = [initial["lump_sum"]] + [r["lump_sum"] for r in results]
    returns = [0.0] + [r["yearly_return"] for r in results]
    net_flows = [
        incomes[i] - expenses[i] + lump_sums[i] for i in range(len(years))
    ]

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Balance Over Time (comparison)",
            "Income vs Expenses (active scenario)",
            "Returns vs Expenses (active scenario)",
            "Net Cash Flow (active scenario)",
        ),
        specs=[
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": False}],
        ],
    )

    if balance_overlays:
        for i, (label, pl) in enumerate(balance_overlays):
            rs = pl["results"]
            ini = pl["initial"]
            oy = [0] + [x["year"] for x in rs]
            ob = [ini["balance"]] + [x["balance"] for x in rs]
            color = OVERLAY_COLORS[i % len(OVERLAY_COLORS)]
            fig.add_trace(
                go.Scatter(
                    x=oy,
                    y=ob,
                    name=label,
                    line=dict(color=color),
                    legendgroup=label,
                ),
                row=1,
                col=1,
            )
    else:
        fig.add_trace(
            go.Scatter(
                x=years, y=balances, name="Balance", line=dict(color="#58a6ff")
            ),
            row=1,
            col=1,
        )
    fig.add_trace(
        go.Scatter(x=years, y=incomes, name="Income", line=dict(color="#3fb950")),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(x=years, y=expenses, name="Expenses", line=dict(color="#f85149")),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(x=years, y=returns, name="Returns", line=dict(color="#d29922")),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=years, y=expenses, name="Expenses", line=dict(color="#f85149")),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=net_flows,
            name="Net Cash Flow",
            line=dict(color="#a371f7"),
            fill="tonexty",
        ),
        row=2,
        col=2,
    )

    for m in milestones:
        fig.add_vline(
            x=m["year"],
            line_dash="dash",
            line_color="#e3b341",
            annotation_text=m["milestone_text"],
            row=1,
            col=1,
        )

    life_labels = list(payload.get("life_events_display") or [])
    for ev in sorted(life_labels, key=lambda x: int(x.get("year", 0))):
        try:
            y_ev = int(ev["year"])
        except (KeyError, TypeError, ValueError):
            continue
        raw_lbl = (ev.get("name") or "").strip()
        ann = raw_lbl if raw_lbl else f"Life event (year {y_ev})"
        for row, col in ((1, 1), (1, 2), (2, 1), (2, 2)):
            if (row, col) == (1, 1):
                fig.add_vline(
                    x=y_ev,
                    line_dash="dot",
                    line_width=1,
                    line_color="rgba(121, 192, 255, 0.55)",
                    annotation_text=ann,
                    annotation_position="top",
                    row=row,
                    col=col,
                )
            else:
                fig.add_vline(
                    x=y_ev,
                    line_dash="dot",
                    line_width=1,
                    line_color="rgba(121, 192, 255, 0.55)",
                    row=row,
                    col=col,
                )

    fig.update_layout(
        template="plotly_dark",
        height=800,
        showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(title_text="Years")
    fig.update_yaxes(title_text="Amount ($)", tickformat=",")
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

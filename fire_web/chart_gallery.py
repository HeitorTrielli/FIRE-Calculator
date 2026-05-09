"""
Curated FIRE projection charts (gallery below the nominal-balance overview).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# (display name, scenario id, simulation payload)
BalanceOverlayRow = Tuple[str, str, Dict[str, Any]]

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from fire_web.constants import OVERLAY_COLORS
from fire_web.simulation import build_figure


def _returns_expenses_series(pl: Dict[str, Any]) -> Tuple[List[int], List[float], List[float]]:
    initial = pl["initial"]
    results: List[Dict[str, Any]] = pl["results"]
    years = [0] + [int(r["year"]) for r in results]
    ret = [0.0] + [float(r.get("yearly_return", 0) or 0) for r in results]
    exp = [float(initial["yearly_expenses"])] + [
        float(r["yearly_expenses"]) for r in results
    ]
    return years, ret, exp


def chart_returns_vs_expenses_comparable(
    balance_overlays: Optional[List[BalanceOverlayRow]],
    fallback_payload: Dict[str, Any],
) -> go.Figure:
    """One chart per compared scenario: returns vs expenses (same overlay list as balance)."""
    overlays = balance_overlays
    if not overlays:
        pl = fallback_payload
        overlays = [("Scenario", "", pl)]

    fig = go.Figure()
    for i, (label, _sid, pl) in enumerate(overlays):
        years, ret, exp = _returns_expenses_series(pl)
        color = OVERLAY_COLORS[i % len(OVERLAY_COLORS)]
        fig.add_trace(
            go.Scatter(
                x=years,
                y=ret,
                mode="lines+markers",
                name=f"Returns — {label}",
                legendgroup=label,
                line=dict(color=color),
                marker=dict(size=6, symbol="circle"),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=years,
                y=exp,
                mode="lines+markers",
                name=f"Expenses — {label}",
                legendgroup=label,
                line=dict(color=color, dash="dash"),
                marker=dict(size=6, symbol="square"),
            )
        )

    fig.update_layout(
        title="Investment returns vs annual expenses — compared scenarios"
        if len(overlays) > 1
        else "Investment returns vs annual expenses ($)",
    )
    fig.update_yaxes(title_text="Dollars", tickformat=",")
    return _dark_layout(fig)


def _projection_frame(payload: Dict[str, Any]) -> pd.DataFrame:
    """Numeric series for gallery charts (year 0 + results)."""
    initial = payload["initial"]
    results: List[Dict[str, Any]] = payload["results"]

    years = [0] + [int(r["year"]) for r in results]
    bal = [float(initial["balance"])] + [float(r["balance"]) for r in results]
    inc = [float(initial["yearly_income"] + initial["non_wage_income"])] + [
        float(r["yearly_income"]) for r in results
    ]
    exp = [float(initial["yearly_expenses"])] + [
        float(r["yearly_expenses"]) for r in results
    ]
    ret = [0.0] + [float(r.get("yearly_return", 0) or 0) for r in results]

    adj_bal = [np.nan]
    for r in results:
        adj_bal.append(float(r.get("adjusted_balance", np.nan)))

    df = pd.DataFrame(
        {
            "year": years,
            "balance": bal,
            "income": inc,
            "expenses": exp,
            "yearly_return": ret,
            "adjusted_balance": adj_bal,
        }
    )
    df["balance_delta"] = df["balance"].diff()
    return df


def _dark_layout(fig: go.Figure, height: int = 400) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=50, r=30, t=40, b=40),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(title_text="Year")
    return fig


def chart_nominal_vs_real_balance(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["balance"],
            name="Nominal balance",
            line=dict(color="#58a6ff"),
        )
    )
    real = df["adjusted_balance"].dropna()
    if len(real) > 0:
        fig.add_trace(
            go.Scatter(
                x=df.loc[real.index, "year"],
                y=real,
                name="Real (inflation-adjusted)",
                line=dict(color="#79c0ff", dash="dash"),
            )
        )
    fig.update_yaxes(title_text="Balance ($)", tickformat=",")
    return _dark_layout(fig)


def chart_balance_delta_bars(df: pd.DataFrame) -> go.Figure:
    sub = df[df["year"] > 0]
    fig = go.Figure(
        go.Bar(
            x=sub["year"],
            y=sub["balance_delta"],
            marker_color=np.where(sub["balance_delta"] >= 0, "#3fb950", "#f85149"),
            name="Year-over-year Δ balance",
        )
    )
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.3)")
    fig.update_yaxes(title_text="Change in balance ($)", tickformat=",")
    return _dark_layout(fig)


def chart_income_expense_margin(df: pd.DataFrame) -> go.Figure:
    margin = df["income"] - df["expenses"]
    fig = go.Figure(
        go.Bar(
            x=df["year"],
            y=margin,
            marker_color=np.where(margin >= 0, "#3fb950", "#f85149"),
            name="Income − expenses",
        )
    )
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.3)")
    fig.update_yaxes(title_text="Dollars", tickformat=",")
    return _dark_layout(fig)


def chart_fire_cushion(df: pd.DataFrame) -> go.Figure:
    nw = df["balance"] / df["expenses"].replace(0, np.nan)
    fig = go.Figure(
        go.Scatter(
            x=df["year"],
            y=nw,
            mode="lines+markers",
            name="Balance ÷ annual expenses",
            line=dict(color="#79c0ff"),
            marker=dict(size=6),
        )
    )
    fig.update_yaxes(title_text="Years of expenses covered (FIRE cushion)")
    return _dark_layout(fig)


def build_chart_gallery_children(
    payload: Dict[str, Any],
    balance_overlays: Optional[List[BalanceOverlayRow]] = None,
):
    """Dash children: intro + balance overview + curated extra charts."""
    from dash import dcc, html

    df = _projection_frame(payload)
    charts: List[Tuple[str, go.Figure]] = [
        (
            "Overview — nominal balance (scenario compare overlays)",
            build_figure(payload, balance_overlays),
        ),
        (
            "Investment returns vs annual expenses ($) — same scenarios as Compare on chart",
            chart_returns_vs_expenses_comparable(balance_overlays, payload),
        ),
        ("Nominal vs inflation-adjusted balance", chart_nominal_vs_real_balance(df)),
        ("Yearly change in balance ($)", chart_balance_delta_bars(df)),
        ("Income minus expenses by year ($)", chart_income_expense_margin(df)),
        (
            "FIRE cushion — balance ÷ annual expenses (years of spending covered)",
            chart_fire_cushion(df),
        ),
    ]

    children: List[Any] = [
        html.P(
            [
                "Extra views you asked to keep. To add or remove charts, edit ",
                html.Code("fire_web/chart_gallery.py"),
                ".",
            ],
            className="chart-gallery-lead",
        )
    ]
    for title, fig in charts:
        children.append(html.H4(title, className="chart-gallery-heading"))
        children.append(
            dcc.Graph(
                figure=fig,
                config={
                    "displayModeBar": True,
                    "scrollZoom": True,
                    "toImageButtonOptions": {"format": "png"},
                },
                style={"minHeight": "380px"},
            )
        )
    return html.Div(children, className="chart-gallery")

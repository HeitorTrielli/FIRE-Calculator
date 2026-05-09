"""Dash layout tree for the FIRE Calculator UI."""

from __future__ import annotations

from dash import dcc, html

from fire_web.bootstrap import (
    ACTIVE_BOOTSTRAP,
    SCENARIOS_BOOTSTRAP,
    SCFG_BOOT_VALUES,
)
from fire_web.constants import DEFAULT_CONFIG_FILE, MODAL_STYLE_CLOSED


def build_layout() -> html.Div:
    return html.Div(
        className="app-shell",
        children=[
            html.Div(
                className="sidebar",
                children=[
                    html.H2("Scenarios"),
                    html.P(
                        [
                            "Use ",
                            html.Strong("Add scenario"),
                            " to enter all financial numbers and manage life events. "
                            "Mark one scenario as ",
                            html.Strong("active"),
                            " for the detailed charts; use ",
                            html.Strong("Compare on chart"),
                            " to overlay balances. Saving a scenario or using ",
                            html.Strong("Save all scenarios"),
                            " writes your scenarios to disk so they persist between sessions.",
                        ],
                        className="lead-muted",
                        style={"fontSize": "0.8rem", "marginBottom": "0.5rem"},
                    ),
                    html.Button(
                        "＋ Add scenario",
                        id="btn-add-scenario",
                        n_clicks=0,
                        className="btn-accent",
                        style={"width": "100%", "marginTop": "0.25rem"},
                    ),
                    html.Div(
                        id="scenario-sidebar-msg",
                        style={
                            "fontSize": "0.85rem",
                            "minHeight": "1rem",
                            "marginTop": "0.35rem",
                        },
                    ),
                    html.Div(id="scenario-list-container", className="scenario-list"),
                    html.Button(
                        "Save all scenarios",
                        id="btn-save-scenarios-disk",
                        n_clicks=0,
                        className="btn-outline",
                        type="button",
                        title=f"Write all scenarios to {DEFAULT_CONFIG_FILE} in the project folder",
                        style={"width": "100%", "marginTop": "0.5rem"},
                    ),
                    dcc.Store(id="scenarios-store", data=SCENARIOS_BOOTSTRAP),
                    dcc.Store(id="active-scenario-id", data=ACTIVE_BOOTSTRAP),
                    dcc.Store(id="scenario-modal-target-id", data=None),
                    dcc.Store(id="scfg-life-events-draft", data=[]),
                    dcc.Store(id="lev-edit-index", data=None),
                    html.Hr(className="sidebar-divider"),
                    html.H2("Simulation"),
                    html.Div(
                        className="sidebar-section",
                        children=[
                            html.Span("Years to Simulate", className="label-inline"),
                            dcc.Input(
                                id="in-max-years",
                                type="number",
                                min=5,
                                max=50,
                                step=1,
                                value=20,
                                style={"width": "100%"},
                            ),
                        ],
                    ),
                    html.Button(
                        "🚀 Calculate FIRE Trajectory",
                        id="btn-calculate",
                        n_clicks=0,
                        className="btn-accent",
                    ),
                ],
            ),
            html.Div(
                className="main",
                children=[
                    html.H1("🔥 FIRE Calculator"),
                    html.P(
                        "Project Financial Independence / Retire Early (FIRE) with optional "
                        "life events and named scenarios you can compare.",
                        className="lead-muted",
                    ),
                    html.Div(id="live-summary", className="live-summary"),
                    dcc.Store(id="sim-output-store", data=None),
                    html.Div(id="metrics-row", className="metrics-row"),
                    html.H3("Charts gallery"),
                    dcc.Loading(
                        id="loading-charts",
                        type="default",
                        children=[
                            html.Div(
                                id="charts-gallery",
                                className="chart-gallery",
                                children=html.P(
                                    [
                                        "Run ",
                                        html.Strong("Calculate FIRE Trajectory"),
                                        " to populate charts.",
                                    ],
                                    className="chart-gallery-empty",
                                ),
                            )
                        ],
                    ),
                    html.Div(id="milestone-section"),
                    html.Details(
                        [
                            html.Summary("📊 Detailed Results"),
                            html.Div(
                                id="results-table-container",
                                style={"marginTop": "0.5rem", "overflowX": "auto"},
                            ),
                        ],
                        style={"marginTop": "1rem"},
                        open=False,
                    ),
                    html.Div(id="main-hint", className="hint"),
                    html.Div(
                        className="footer-note",
                        children="Built with Dash • FIRE Calculator with future state planning",
                    ),
                ],
            ),
            html.Div(
                id="scenario-config-modal-root",
                className="modal-overlay",
                style=MODAL_STYLE_CLOSED,
                children=[
                    html.Div(
                        className="modal-panel scenario-config-panel",
                        children=[
                            html.Div(
                                className="modal-header",
                                children=[
                                    dcc.Input(
                                        id="scfg-scenario-name",
                                        type="text",
                                        value=SCENARIOS_BOOTSTRAP[0]["name"],
                                        className="modal-title-input",
                                        placeholder="Scenario name",
                                    ),
                                    html.Button(
                                        "✕",
                                        id="btn-close-scenario-config",
                                        className="modal-close",
                                        n_clicks=0,
                                        type="button",
                                        title="Close",
                                    ),
                                ],
                            ),
                            html.P(
                                "Enter starting assumptions for this scenario. For wage income, living "
                                "expenses, and non-wage income you can check Monthly on any field "
                                "independently (the rest stay yearly). Add life events below "
                                "(each opens in its own dialog). Save applies everything to your scenario "
                                "list — Calculate runs from saved scenarios.",
                                className="modal-lead",
                            ),
                            html.H4(
                                "Starting assumptions",
                                className="scenario-config-subheading",
                            ),
                            html.Div(
                                className="scfg-assumptions-grid",
                                children=[
                                    html.Div(
                                        className="modal-field",
                                        children=[
                                            html.Span(
                                                "Initial Balance ($)",
                                                className="label-inline",
                                            ),
                                            dcc.Input(
                                                id="scfg-initial-balance",
                                                type="number",
                                                step="any",
                                                value=SCFG_BOOT_VALUES[0],
                                                style={"width": "100%"},
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="modal-field",
                                        children=[
                                            html.Div(
                                                className="scfg-field-head",
                                                children=[
                                                    html.Span(
                                                        "Wage income ($)",
                                                        className="label-inline",
                                                    ),
                                                    dcc.Checklist(
                                                        id="scfg-income-monthly",
                                                        options=[
                                                            {
                                                                "label": "Monthly",
                                                                "value": "m",
                                                            }
                                                        ],
                                                        value=SCFG_BOOT_VALUES[6],
                                                        className="scfg-monthly-toggle",
                                                        inputStyle={"marginRight": "0.35rem"},
                                                        labelStyle={
                                                            "fontSize": "0.8rem",
                                                            "color": "var(--text-muted)",
                                                        },
                                                    ),
                                                ],
                                            ),
                                            dcc.Input(
                                                id="scfg-yearly-income",
                                                type="number",
                                                min=0,
                                                step=1000,
                                                value=SCFG_BOOT_VALUES[1],
                                                style={"width": "100%"},
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="modal-field",
                                        children=[
                                            html.Div(
                                                className="scfg-field-head",
                                                children=[
                                                    html.Span(
                                                        "Non-wage income ($)",
                                                        className="label-inline",
                                                    ),
                                                    dcc.Checklist(
                                                        id="scfg-nonwage-monthly",
                                                        options=[
                                                            {
                                                                "label": "Monthly",
                                                                "value": "m",
                                                            }
                                                        ],
                                                        value=SCFG_BOOT_VALUES[8],
                                                        className="scfg-monthly-toggle",
                                                        inputStyle={"marginRight": "0.35rem"},
                                                        labelStyle={
                                                            "fontSize": "0.8rem",
                                                            "color": "var(--text-muted)",
                                                        },
                                                    ),
                                                ],
                                            ),
                                            dcc.Input(
                                                id="scfg-non-wage-income",
                                                type="number",
                                                min=0,
                                                step=1000,
                                                value=SCFG_BOOT_VALUES[5],
                                                style={"width": "100%"},
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="modal-field",
                                        children=[
                                            html.Div(
                                                className="scfg-field-head",
                                                children=[
                                                    html.Span(
                                                        "Living expenses ($)",
                                                        className="label-inline",
                                                    ),
                                                    dcc.Checklist(
                                                        id="scfg-expenses-monthly",
                                                        options=[
                                                            {
                                                                "label": "Monthly",
                                                                "value": "m",
                                                            }
                                                        ],
                                                        value=SCFG_BOOT_VALUES[7],
                                                        className="scfg-monthly-toggle",
                                                        inputStyle={"marginRight": "0.35rem"},
                                                        labelStyle={
                                                            "fontSize": "0.8rem",
                                                            "color": "var(--text-muted)",
                                                        },
                                                    ),
                                                ],
                                            ),
                                            dcc.Input(
                                                id="scfg-yearly-expenses",
                                                type="number",
                                                min=0,
                                                step=1000,
                                                value=SCFG_BOOT_VALUES[2],
                                                style={"width": "100%"},
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="modal-field",
                                        children=[
                                            html.Span(
                                                "Annual Return Rate (%)",
                                                className="label-inline",
                                            ),
                                            dcc.Input(
                                                id="scfg-annual-return-pct",
                                                type="number",
                                                min=0,
                                                max=20,
                                                step=0.1,
                                                value=SCFG_BOOT_VALUES[3],
                                                style={"width": "100%"},
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="modal-field",
                                        children=[
                                            html.Span(
                                                "Inflation Rate (%)",
                                                className="label-inline",
                                            ),
                                            dcc.Input(
                                                id="scfg-inflation-pct",
                                                type="number",
                                                min=0,
                                                max=10,
                                                step=0.1,
                                                value=SCFG_BOOT_VALUES[4],
                                                style={"width": "100%"},
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            html.H4(
                                "Life events",
                                className="scenario-config-subheading",
                            ),
                            html.P(
                                "Events apply from the start of that simulation year forward "
                                "(chart markers line up with the first balance change). Add a life event with "
                                "yearly income 0 to stop wage income from that year on. "
                                "Named events appear as markers on charts after Calculate.",
                                className="modal-lead",
                                style={"marginBottom": "0.65rem"},
                            ),
                            html.Div(
                                id="scfg-life-events-list",
                                style={
                                    "marginTop": "0.35rem",
                                    "marginBottom": "0.65rem",
                                },
                            ),
                            html.Button(
                                "＋ Add life event",
                                id="btn-open-life-event-modal",
                                n_clicks=0,
                                className="btn-outline",
                                style={"width": "100%"},
                                type="button",
                            ),
                            html.Div(
                                className="modal-actions",
                                style={
                                    "marginTop": "1.25rem",
                                    "paddingTop": "1rem",
                                    "borderTop": "1px solid rgba(48, 54, 61, 0.85)",
                                },
                                children=[
                                    html.Button(
                                        "Cancel",
                                        id="btn-cancel-scenario-modal",
                                        className="btn-outline",
                                        n_clicks=0,
                                        type="button",
                                    ),
                                    html.Button(
                                        "Save scenario",
                                        id="btn-save-scenario-modal",
                                        className="btn-modal-submit",
                                        n_clicks=0,
                                        type="button",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                id="life-event-modal-root",
                className="modal-overlay nested-event-overlay",
                style=MODAL_STYLE_CLOSED,
                children=[
                    html.Div(
                        className="modal-panel scenario-config-panel life-event-modal-panel",
                        children=[
                            html.Div(
                                className="modal-header",
                                children=[
                                    dcc.Input(
                                        id="lev-event-name",
                                        type="text",
                                        value="",
                                        className="modal-title-input",
                                        placeholder="Life event",
                                    ),
                                    html.Button(
                                        "✕",
                                        id="btn-close-life-modal",
                                        className="modal-close",
                                        n_clicks=0,
                                        type="button",
                                        title="Close",
                                    ),
                                ],
                            ),
                            html.P(
                                "Pick the year from today and any values that change then. "
                                "Leave fields blank to inherit from the projected path.",
                                className="modal-lead",
                            ),
                            html.Div(
                                id="lev-msg",
                                style={"fontSize": "0.88rem", "minHeight": "1rem"},
                            ),
                            html.Div(
                                className="scfg-assumptions-grid",
                                children=[
                                    html.Div(
                                        className="modal-field",
                                        children=[
                                            html.Span(
                                                "Year (from now)",
                                                className="label-inline",
                                            ),
                                            dcc.Input(
                                                id="lev-year",
                                                type="number",
                                                min=1,
                                                max=50,
                                                step=1,
                                                value=5,
                                                style={"width": "100%"},
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="modal-field",
                                        children=[
                                            html.Span(
                                                "New Yearly Income ($), optional",
                                                className="label-inline",
                                            ),
                                            dcc.Input(
                                                id="lev-income",
                                                type="number",
                                                min=0,
                                                step=1000,
                                                placeholder="inherit",
                                                style={"width": "100%"},
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="modal-field",
                                        children=[
                                            html.Span(
                                                "New Yearly Expenses ($), optional",
                                                className="label-inline",
                                            ),
                                            dcc.Input(
                                                id="lev-expenses",
                                                type="number",
                                                min=0,
                                                step=1000,
                                                placeholder="inherit",
                                                style={"width": "100%"},
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="modal-field",
                                        children=[
                                            html.Span(
                                                "New Non-Wage Income ($), optional",
                                                className="label-inline",
                                            ),
                                            dcc.Input(
                                                id="lev-nonwage",
                                                type="number",
                                                min=0,
                                                step=1000,
                                                placeholder="inherit",
                                                style={"width": "100%"},
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="modal-field",
                                        children=[
                                            html.Span(
                                                "New Return Rate (%), optional",
                                                className="label-inline",
                                            ),
                                            dcc.Input(
                                                id="lev-return-pct",
                                                type="number",
                                                min=0,
                                                max=20,
                                                step=0.1,
                                                placeholder="inherit",
                                                style={"width": "100%"},
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="modal-field",
                                        children=[
                                            html.Span(
                                                "Lump Sum ($), optional",
                                                className="label-inline",
                                            ),
                                            dcc.Input(
                                                id="lev-lump",
                                                type="number",
                                                step=1000,
                                                placeholder="none",
                                                style={"width": "100%"},
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            html.Div(
                                className="modal-actions",
                                children=[
                                    html.Button(
                                        "Cancel",
                                        id="btn-cancel-life-modal",
                                        className="btn-outline",
                                        n_clicks=0,
                                        type="button",
                                    ),
                                    html.Button(
                                        "Save event",
                                        id="btn-save-life-modal",
                                        className="btn-modal-submit",
                                        n_clicks=0,
                                        type="button",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

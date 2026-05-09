"""Calculate button, live summary, main chart/metrics/table."""

from __future__ import annotations

import base64
import copy
import json
from typing import Any, Dict, List, Optional, Tuple

import dash.dash_table as dash_table
import plotly.graph_objects as go
from dash import Input, Output, State, callback, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate

from fire_debug import log_callback_context, log_event, log_verbose_bundle
from fire_web.bootstrap import config_file_path, migrate_config_v1_to_scenarios
from fire_web.constants import DT_CELL, DT_HEADER
from fire_web.constants import DEFAULT_CONFIG_FILE
from fire_web.persist import (
    life_events_server_debug_snapshot,
    life_events_server_get,
    life_events_server_reset_from_scenarios,
    persist_scenarios_to_disk,
)
from fire_web.simulation import (
    build_figure,
    build_simulation,
    format_results_table,
    sim_from_scenario,
)


@callback(
    Output("live-summary", "children"),
    Input("in-max-years", "value"),
    Input("scenarios-store", "data"),
    Input("active-scenario-id", "data"),
)
def update_live_summary(max_y, scenarios, aid):
    scen = next((s for s in (scenarios or []) if s.get("id") == aid), None)
    if not scen:
        return html.Div()
    init = scen.get("initial_state") or {}
    try:
        horizon = int(max_y) if max_y not in (None, "") else 20
    except (TypeError, ValueError):
        horizon = 20
    try:
        ret_y = int(init.get("retirement_year", 1) or 1)
    except (TypeError, ValueError):
        ret_y = 1
    bal = float(init.get("initial_balance", 0) or 0)
    name = scen.get("name") or "—"
    n_ev = len(scen.get("life_events") or [])
    n_compare = sum(1 for s in (scenarios or []) if s.get("compare"))
    n_scen = len(scenarios or [])
    return html.Div(
        [
            html.Span(
                "Live summary", style={"display": "block", "marginBottom": "0.35rem"}
            ),
            html.Div(
                [
                    html.Strong(name),
                    f" · start ",
                    html.Strong(f"${bal:,.0f}"),
                    f" · horizon ",
                    html.Strong(f"{horizon} yr"),
                    f" · wage stops year ",
                    html.Strong(str(ret_y)),
                    f" · ",
                    html.Strong(str(n_ev)),
                    " life event(s) · ",
                    html.Strong(str(n_compare)),
                    f" / {n_scen}",
                    " scenario(s) compared",
                ]
            ),
        ]
    )


@callback(
    Output("sim-output-store", "data"),
    Input("btn-calculate", "n_clicks"),
    State("in-max-years", "value"),
    State("scenarios-store", "data"),
    State("active-scenario-id", "data"),
    prevent_initial_call=True,
)
def run_calculate(
    n_clicks,
    max_years,
    scenarios,
    active_id,
):
    if not n_clicks:
        raise PreventUpdate

    log_callback_context("run_calculate")

    my = int(max_years) if max_years not in (None, "") else 20
    scen_list = scenarios or []
    active_scen = next((s for s in scen_list if s.get("id") == active_id), None)
    if not active_scen:
        active_scen = scen_list[0] if scen_list else None
    if not active_scen:
        raise PreventUpdate

    init = active_scen["initial_state"]
    ib = float(init.get("initial_balance", 0) or 0)
    yi = float(init.get("yearly_income", 0) or 0)
    ye = float(init.get("yearly_expenses", 0) or 0)
    arr = float(init.get("annual_return_rate", 0) or 0)
    inf = float(init.get("inflation_rate", 0) or 0)
    nw = float(init.get("non_wage_income", 0) or 0)
    try:
        ry = int(init.get("retirement_year", 1) or 1)
    except (TypeError, ValueError):
        ry = 1

    fs = list(active_scen.get("life_events") or [])
    merge_source = "scenarios_store"
    if not fs:
        fs = life_events_server_get(active_id)
        if fs:
            merge_source = "SERVER_MEMORY_CACHE"

    log_verbose_bundle(
        "run_calculate_BEFORE_MERGE",
        {
            "active_id": active_id,
            "merge_hint": merge_source,
            "active_scenario_from_State": active_scen,
            "server_cache_before_merge": life_events_server_debug_snapshot(),
        },
    )

    log_event(
        "run_calculate:after_merge",
        active_id=active_id,
        merge_source=merge_source,
        n_life_events=len(fs),
        life_events_preview=fs[:12],
        scenario_saved_events_len=len(active_scen.get("life_events", [])),
    )
    log_verbose_bundle(
        "run_calculate_AFTER_MERGE",
        {
            "merge_source": merge_source,
            "resolved_life_events": fs,
        },
    )

    active_payload, _ = build_simulation(ib, yi, ye, arr, inf, nw, ry, fs, my)

    meta_rows: List[Dict[str, Any]] = []
    for fs_item in fs:
        try:
            yr_m = int(float(fs_item["year"]))
        except (KeyError, TypeError, ValueError):
            continue
        meta_rows.append(
            {"year": yr_m, "name": str(fs_item.get("name") or "").strip()}
        )
    active_payload["life_events_display"] = meta_rows

    compare_set = [s for s in scen_list if s.get("compare")]
    if not compare_set:
        try:
            compare_set = [next(s for s in scen_list if s["id"] == active_id)]
        except StopIteration:
            compare_set = [scen_list[0]] if scen_list else []

    overlay: List[Tuple[str, Dict[str, Any]]] = []
    for s in compare_set:
        try:
            if s["id"] == active_id:
                pl = active_payload
            else:
                pl = sim_from_scenario(s, my)
            overlay.append((s.get("name", "Scenario"), pl))
        except (ValueError, KeyError, IndexError):
            continue

    sim_out = {
        "active_payload": active_payload,
        "balance_overlays": overlay,
        "active_id": active_id,
    }
    return sim_out


@callback(
    Output("metrics-row", "children"),
    Output("main-graph", "figure"),
    Output("milestone-section", "children"),
    Output("results-table-container", "children"),
    Output("main-hint", "children"),
    Input("sim-output-store", "data"),
    State("config-had-initial", "data"),
    State("scenarios-store", "data"),
    State("active-scenario-id", "data"),
)
def render_main(sim_data, config_had_initial, scenarios, active_id):
    hint_empty_setup = html.Span(
        "Add a scenario with **＋ Add scenario**, enter your numbers, save, then click "
        "**Calculate FIRE Trajectory**."
    )
    hint_click_calc = html.Span(
        "Click **Calculate FIRE Trajectory** in the sidebar to run the simulation."
    )

    if not sim_data:
        scen = next((s for s in (scenarios or []) if s.get("id") == active_id), None)
        if not scen and scenarios:
            scen = scenarios[0]
        ib = 0.0
        n_ev = 0
        if scen:
            ib = float(scen.get("initial_state", {}).get("initial_balance", 0) or 0)
            n_ev = len(scen.get("life_events") or [])
        if config_had_initial or n_ev or ib != 0:
            return (
                [],
                go.Figure(
                    layout={
                        "template": "plotly_dark",
                        "paper_bgcolor": "rgba(0,0,0,0)",
                        "plot_bgcolor": "rgba(0,0,0,0)",
                    }
                ),
                html.Div(),
                html.Div(),
                hint_click_calc,
            )
        return (
            [],
            go.Figure(
                layout={
                    "template": "plotly_dark",
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0)",
                }
            ),
            html.Div(),
            html.Div(),
            hint_empty_setup,
        )

    active_payload = sim_data.get("active_payload") or sim_data
    overlays = sim_data.get("balance_overlays")

    milestones: List[Dict[str, Any]] = active_payload["milestones"]
    results: List[Dict[str, Any]] = active_payload["results"]
    max_years = active_payload["max_years"]
    final_balance = results[-1]["balance"] if results else 0.0

    first_m = milestones[0] if milestones else None
    if first_m:
        m2_label = "First Million"
        m2_val = f"In {first_m['year']} Years"
        m2_title = f"Balance: ${first_m['balance']:,.0f}"
    else:
        m2_label = "First Million"
        m2_val = "Not reached"
        m2_title = "No million-dollar milestone reached"

    if milestones:
        last_m = milestones[-1]
        m3_val = f"{last_m['milestone']}M"
        m3_title = f"Reached {len(milestones)} milestone(s)"
    else:
        m3_val = "0"
        m3_title = "No milestones reached"

    metrics = html.Div(
        [
            html.Div(
                className="metric-card",
                title=f"Projected balance in {max_years} years",
                children=[
                    html.Div("Final Balance", className="label"),
                    html.Div(f"${final_balance:,.0f}", className="value"),
                ],
            ),
            html.Div(
                className="metric-card",
                title=m2_title if first_m else None,
                children=[
                    html.Div(m2_label, className="label"),
                    html.Div(m2_val, className="value"),
                ],
            ),
            html.Div(
                className="metric-card",
                title=m3_title,
                children=[
                    html.Div("Highest Milestone", className="label"),
                    html.Div(m3_val, className="value"),
                ],
            ),
        ]
    )

    fig = build_figure(active_payload, overlays)

    mile_children = []
    if milestones:
        cards = []
        for m in milestones:
            if len(m["milestones_reached"]) == 1:
                title = f"${m['milestone']}M"
            else:
                title = ", ".join(f"{x}M" for x in m["milestones_reached"])
            cards.append(
                html.Div(
                    className="metric-card",
                    title=f"Balance: ${m['balance']:,.0f}",
                    children=[
                        html.Div(title, className="label"),
                        html.Div(f"In {m['year']} Years", className="value"),
                    ],
                )
            )
        mile_children = [
            html.H3("Million Dollar Milestones"),
            html.Div(className="milestone-grid", children=cards),
        ]

    df = format_results_table(active_payload)
    table = dash_table.DataTable(
        columns=[{"name": c, "id": c} for c in df.columns],
        data=df.reset_index().to_dict("records"),
        style_cell=DT_CELL,
        style_header=DT_HEADER,
        style_table={"backgroundColor": "#161b22"},
        page_action="none",
    )

    return metrics, fig, html.Div(mile_children), table, html.Div()


def _upload_err(msg: html.Span):
    return no_update, no_update, msg, no_update, no_update


@callback(
    Output("download-config", "data"),
    Input("btn-download", "n_clicks"),
    State("scenarios-store", "data"),
    State("active-scenario-id", "data"),
    prevent_initial_call=True,
)
def download_config(
    n_clicks,
    scenarios,
    active_id,
):
    if not n_clicks:
        raise PreventUpdate

    scen_list = copy.deepcopy(scenarios or [])
    out = {
        "version": 2,
        "active_scenario_id": active_id,
        "scenarios": scen_list,
    }
    json_str = json.dumps(out, indent=4)
    return dcc.send_string(json_str, filename=DEFAULT_CONFIG_FILE)


@callback(
    Output("scenarios-store", "data", allow_duplicate=True),
    Output("active-scenario-id", "data", allow_duplicate=True),
    Output("upload-status", "children"),
    Output("config-had-initial", "data"),
    Output("sim-output-store", "data", allow_duplicate=True),
    Input("upload-config", "contents"),
    State("upload-config", "filename"),
    prevent_initial_call=True,
)
def upload_config(contents, filename):
    if contents is None:
        raise PreventUpdate
    try:
        _content_type, content_string = contents.split(",", 1)
        raw = base64.b64decode(content_string)
        config_data = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as e:
        return _upload_err(html.Span(f"Invalid file: {e}", style={"color": "#f85149"}))

    if config_data.get("version") == 2:
        scenarios_in = config_data.get("scenarios") or []
        if not scenarios_in:
            return _upload_err(
                html.Span("Invalid v2 file: empty scenarios.", style={"color": "#f85149"})
            )
        scenarios = scenarios_in
        aid = config_data.get("active_scenario_id") or scenarios[0]["id"]
    else:
        if not config_data.get("initial_state"):
            return _upload_err(
                html.Span(
                    "Missing initial_state (legacy v1 file).",
                    style={"color": "#f85149"},
                )
            )
        scenarios, aid = migrate_config_v1_to_scenarios(config_data)

    ids = {s["id"] for s in scenarios}
    if aid not in ids:
        aid = scenarios[0]["id"]

    disk_err = persist_scenarios_to_disk(scenarios, aid)
    if disk_err:
        life_events_server_reset_from_scenarios(scenarios, "upload_config_disk_error")
        return (
            scenarios,
            aid,
            html.Span(
                f"Loaded scenarios but could not write {config_file_path()}: {disk_err}",
                style={"color": "#f85149"},
            ),
            True,
            None,
        )

    status = html.Span(
        f"Loaded {len(scenarios)} scenario(s). Saved to {config_file_path().name}. Run Calculate.",
        style={"color": "#3fb950"},
    )
    return scenarios, aid, status, True, None

"""Scenario sidebar list, compare/active/remove, scenario configuration modal."""

from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, List, Optional

from dash import ALL, Input, Output, State, callback, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate

from fire_web.bootstrap import (
    BLANK_CFG_TUPLE,
    _initial_to_input_values,
    _inputs_to_initial_state,
    config_file_path,
    duplicate_scenario_record,
)
from fire_web.constants import MODAL_STYLE_CLOSED, MODAL_STYLE_OPEN
from fire_web.persist import (
    life_events_server_pop,
    life_events_server_put,
    persist_scenarios_to_disk,
)
from fire_web.simulation import sort_life_events_chronologically


@callback(
    Output("scenario-list-container", "children"),
    Input("scenarios-store", "data"),
    Input("active-scenario-id", "data"),
)
def render_scenario_sidebar_list(
    scenarios: Optional[List[Dict[str, Any]]],
    active_id: Optional[str],
):
    if not scenarios:
        return html.Div(
            className="scenario-rows-root",
            children=[
                html.P(
                    "No scenarios.",
                    className="lead-muted",
                    style={"fontSize": "0.85rem"},
                )
            ],
        )
    rows = []
    for s in scenarios:
        sid = s["id"]
        is_active = sid == active_id
        rows.append(
            html.Div(
                className="scenario-row" + (" scenario-row-active" if is_active else ""),
                **{"data-sid": sid},
                children=[
                    html.Div(
                        className="scenario-row-title-row",
                        children=[
                            html.Div(
                                className="scenario-row-title-left",
                                children=[
                                    html.Span(
                                        s.get("name") or "Untitled",
                                        className="scenario-row-title",
                                    ),
                                ],
                            ),
                            html.Button(
                                "Active",
                                id={"type": "scen-activate", "sid": sid},
                                n_clicks=0,
                                className="btn-small scenario-active-btn",
                                style={
                                    "opacity": 1.0 if is_active else 0.65,
                                },
                                title="Use this scenario for detailed charts",
                            ),
                        ],
                    ),
                    html.Div(
                        className="scenario-row-toolbar",
                        children=[
                            dcc.Checklist(
                                id={"type": "scen-compare", "sid": sid},
                                options=[{"label": "Compare on chart", "value": "y"}],
                                value=["y"] if s.get("compare", True) else [],
                                style={
                                    "fontSize": "0.82rem",
                                    "marginBottom": "0.35rem",
                                },
                                inputStyle={"marginRight": "0.35rem"},
                            ),
                            html.Div(
                                style={
                                    "display": "flex",
                                    "gap": "0.35rem",
                                    "flexWrap": "wrap",
                                },
                                children=[
                                    html.Button(
                                        "Edit",
                                        id={"type": "scen-edit", "sid": sid},
                                        n_clicks=0,
                                        className="btn-outline",
                                        style={
                                            "flex": "1",
                                            "marginTop": 0,
                                            "minWidth": "4rem",
                                        },
                                    ),
                                    html.Button(
                                        "Copy",
                                        id={"type": "scen-copy", "sid": sid},
                                        n_clicks=0,
                                        className="btn-outline",
                                        style={
                                            "flex": "1",
                                            "marginTop": 0,
                                            "minWidth": "4rem",
                                        },
                                        title="Duplicate this scenario",
                                    ),
                                    html.Button(
                                        "Remove",
                                        id={"type": "scen-remove", "sid": sid},
                                        n_clicks=0,
                                        className="btn-outline",
                                        style={
                                            "flex": "1",
                                            "marginTop": 0,
                                            "minWidth": "4rem",
                                        },
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            )
        )
    return html.Div(className="scenario-rows-root", children=rows)


@callback(
    Output("scenario-config-modal-root", "style"),
    Output("scenario-modal-target-id", "data"),
    Output("scfg-life-events-draft", "data"),
    Output("scfg-scenario-name", "value"),
    Output("scfg-initial-balance", "value"),
    Output("scfg-yearly-income", "value"),
    Output("scfg-yearly-expenses", "value"),
    Output("scfg-annual-return-pct", "value"),
    Output("scfg-inflation-pct", "value"),
    Output("scfg-non-wage-income", "value"),
    Output("scfg-income-monthly", "value"),
    Output("scfg-expenses-monthly", "value"),
    Output("scfg-nonwage-monthly", "value"),
    Input("btn-add-scenario", "n_clicks"),
    Input({"type": "scen-edit", "sid": ALL}, "n_clicks"),
    State("scenarios-store", "data"),
    prevent_initial_call=True,
)
def open_scenario_modal(n_add, _edit_clicks, scenarios):
    trig = ctx.triggered_id
    if trig == "btn-add-scenario":
        if not n_add:
            raise PreventUpdate
        return (
            MODAL_STYLE_OPEN,
            None,
            [],
            "",
            *BLANK_CFG_TUPLE,
        )
    if isinstance(trig, dict) and trig.get("type") == "scen-edit":
        sid = trig["sid"]
        clicks = list(_edit_clicks or [])
        idx = next(
            (i for i, s in enumerate(scenarios or []) if s["id"] == sid),
            -1,
        )
        if idx < 0 or idx >= len(clicks) or int(clicks[idx] or 0) < 1:
            raise PreventUpdate
        scen = scenarios[idx]
        init = scen["initial_state"]
        ib, yi, ye, arp, inf, nw, inc_m, exp_m, nw_m = _initial_to_input_values(init)
        return (
            MODAL_STYLE_OPEN,
            sid,
            sort_life_events_chronologically(scen.get("life_events") or []),
            scen.get("name", "Scenario"),
            ib,
            yi,
            ye,
            arp,
            inf,
            nw,
            inc_m,
            exp_m,
            nw_m,
        )
    raise PreventUpdate


@callback(
    Output("scenario-config-modal-root", "style", allow_duplicate=True),
    Output("life-event-modal-root", "style", allow_duplicate=True),
    Input("btn-cancel-scenario-modal", "n_clicks"),
    Input("btn-close-scenario-config", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_scenario_modal(_cancel, _close):
    trig = ctx.triggered_id
    if trig not in ("btn-cancel-scenario-modal", "btn-close-scenario-config"):
        raise PreventUpdate
    return MODAL_STYLE_CLOSED, MODAL_STYLE_CLOSED


@callback(
    Output("scenarios-store", "data"),
    Output("scenario-config-modal-root", "style", allow_duplicate=True),
    Output("scenario-sidebar-msg", "children"),
    Output("active-scenario-id", "data", allow_duplicate=True),
    Input("btn-save-scenario-modal", "n_clicks"),
    State("scenario-modal-target-id", "data"),
    State("scfg-scenario-name", "value"),
    State("scfg-initial-balance", "value"),
    State("scfg-yearly-income", "value"),
    State("scfg-yearly-expenses", "value"),
    State("scfg-annual-return-pct", "value"),
    State("scfg-inflation-pct", "value"),
    State("scfg-non-wage-income", "value"),
    State("scfg-income-monthly", "value"),
    State("scfg-expenses-monthly", "value"),
    State("scfg-nonwage-monthly", "value"),
    State("scfg-life-events-draft", "data"),
    State("scenarios-store", "data"),
    State("active-scenario-id", "data"),
    prevent_initial_call=True,
)
def save_scenario_modal(
    n_clicks,
    target_id,
    name,
    ib,
    yi,
    ye,
    arp,
    inf,
    nw,
    inc_monthly,
    exp_monthly,
    nw_monthly,
    draft_events,
    scenarios,
    cur_active,
):
    if not n_clicks:
        raise PreventUpdate
    scen_list = copy.deepcopy(scenarios or [])
    snap = _inputs_to_initial_state(
        ib,
        yi,
        ye,
        arp,
        inf,
        nw,
        inc_monthly,
        exp_monthly,
        nw_monthly,
    )
    snap.pop("retirement_year", None)
    nm = (name or "").strip() or "Untitled scenario"
    events = sort_life_events_chronologically(list(draft_events or []))
    if target_id is None:
        sid = uuid.uuid4().hex[:12]
        scen_list.append(
            {
                "id": sid,
                "name": nm,
                "compare": True,
                "initial_state": snap,
                "life_events": events,
            }
        )
        life_events_server_put(sid, events, "modal_save_new")
        disk_err = persist_scenarios_to_disk(scen_list, sid)
        msg = (
            html.Div(
                [
                    html.Span(f"Saved new scenario “{nm}”. ", style={"color": "#3fb950"}),
                    html.Span(
                        f"Could not write {config_file_path().name}: {disk_err}",
                        style={"color": "#d29922", "fontSize": "0.82rem"},
                    ),
                ]
            )
            if disk_err
            else html.Span(f"Saved new scenario “{nm}”.", style={"color": "#3fb950"})
        )
        return scen_list, MODAL_STYLE_CLOSED, msg, sid
    patched = False
    for s in scen_list:
        if s["id"] == target_id:
            s["name"] = nm
            s["initial_state"] = snap
            s["life_events"] = events
            patched = True
            break
    if not patched:
        raise PreventUpdate
    life_events_server_put(target_id, events, "modal_save_edit")
    disk_err = persist_scenarios_to_disk(scen_list, cur_active)
    msg = (
        html.Div(
            [
                html.Span(f"Updated “{nm}”. ", style={"color": "#3fb950"}),
                html.Span(
                    f"Could not write {config_file_path().name}: {disk_err}",
                    style={"color": "#d29922", "fontSize": "0.82rem"},
                ),
            ]
        )
        if disk_err
        else html.Span(f"Updated “{nm}”.", style={"color": "#3fb950"})
    )
    return scen_list, MODAL_STYLE_CLOSED, msg, no_update


@callback(
    Output("scenarios-store", "data", allow_duplicate=True),
    Input({"type": "scen-compare", "sid": ALL}, "value"),
    State("scenarios-store", "data"),
    State("active-scenario-id", "data"),
    prevent_initial_call=True,
)
def toggle_scenario_compare(checkbox_values, scenarios, active_id):
    trig = ctx.triggered_id
    if not isinstance(trig, dict) or trig.get("type") != "scen-compare":
        raise PreventUpdate
    sid = trig["sid"]
    idx = next((i for i, s in enumerate(scenarios or []) if s["id"] == sid), None)
    if idx is None:
        raise PreventUpdate
    val = checkbox_values[idx]
    on = bool(val and "y" in val)
    out = copy.deepcopy(scenarios or [])
    for s in out:
        if s["id"] == sid:
            s["compare"] = on
            break
    persist_scenarios_to_disk(out, active_id)
    return out


@callback(
    Output("scenarios-store", "data", allow_duplicate=True),
    Output("scenario-sidebar-msg", "children", allow_duplicate=True),
    Input({"type": "scen-copy", "sid": ALL}, "n_clicks"),
    State("scenarios-store", "data"),
    State("active-scenario-id", "data"),
    prevent_initial_call=True,
)
def copy_scenario_sidebar(_clicks, scenarios, aid):
    trig = ctx.triggered_id
    if not isinstance(trig, dict) or trig.get("type") != "scen-copy":
        raise PreventUpdate
    sid = trig["sid"]
    order = [s["id"] for s in (scenarios or [])]
    try:
        ix = order.index(sid)
    except ValueError:
        raise PreventUpdate
    cl = list(_clicks or [])
    if ix >= len(cl) or int(cl[ix] or 0) < 1:
        raise PreventUpdate
    src = next((s for s in (scenarios or []) if s["id"] == sid), None)
    if not src:
        raise PreventUpdate
    new_scen = duplicate_scenario_record(src)
    out = copy.deepcopy(scenarios or [])
    out.append(new_scen)
    life_events_server_put(
        new_scen["id"],
        list(new_scen.get("life_events") or []),
        "sidebar_copy",
    )
    disk_err = persist_scenarios_to_disk(out, aid)
    nm = new_scen.get("name", "Copy")
    msg = (
        html.Div(
            [
                html.Span(f"Copied to “{nm}”. ", style={"color": "#3fb950"}),
                html.Span(
                    f"Could not write {config_file_path().name}: {disk_err}",
                    style={"color": "#d29922", "fontSize": "0.82rem"},
                ),
            ]
        )
        if disk_err
        else html.Span(f"Copied to “{nm}”.", style={"color": "#3fb950"})
    )
    return out, msg


@callback(
    Output("active-scenario-id", "data"),
    Input({"type": "scen-activate", "sid": ALL}, "n_clicks"),
    State("scenarios-store", "data"),
    prevent_initial_call=True,
)
def activate_scenario_sidebar(clicks, scenarios):
    trig = ctx.triggered_id
    if not isinstance(trig, dict) or trig.get("type") != "scen-activate":
        raise PreventUpdate
    sid = trig["sid"]
    order = [s["id"] for s in (scenarios or [])]
    try:
        ix = order.index(sid)
    except ValueError:
        raise PreventUpdate
    cl = list(clicks or [])
    if ix >= len(cl) or int(cl[ix] or 0) < 1:
        raise PreventUpdate
    persist_scenarios_to_disk(scenarios or [], sid)
    return sid


@callback(
    Output("scenarios-store", "data", allow_duplicate=True),
    Output("active-scenario-id", "data", allow_duplicate=True),
    Output("scenario-sidebar-msg", "children", allow_duplicate=True),
    Input({"type": "scen-remove", "sid": ALL}, "n_clicks"),
    State("scenarios-store", "data"),
    State("active-scenario-id", "data"),
    prevent_initial_call=True,
)
def remove_scenario_from_sidebar(_clicks, scenarios, aid):
    trig = ctx.triggered_id
    if not isinstance(trig, dict) or trig.get("type") != "scen-remove":
        raise PreventUpdate
    sid = trig["sid"]
    order_rm = [s["id"] for s in (scenarios or [])]
    try:
        ix_rm = order_rm.index(sid)
    except ValueError:
        raise PreventUpdate
    cl = list(_clicks or [])
    if ix_rm >= len(cl) or int(cl[ix_rm] or 0) < 1:
        raise PreventUpdate
    if not scenarios or len(scenarios) <= 1:
        return no_update, no_update, html.Span(
            "Keep at least one scenario.", style={"color": "#d29922"}
        )
    rest = [s for s in scenarios if s["id"] != sid]
    new_active = rest[0]["id"] if aid == sid else aid
    life_events_server_pop(sid)
    na_scen = next((s for s in rest if s["id"] == new_active), rest[0])
    life_events_server_put(
        new_active,
        list(na_scen.get("life_events") or []),
        "sidebar_remove",
    )
    persist_scenarios_to_disk(rest, new_active)
    return (
        rest,
        new_active,
        html.Span("Scenario removed.", style={"color": "#3fb950"}),
    )


@callback(
    Output("scenario-sidebar-msg", "children", allow_duplicate=True),
    Input("btn-save-scenarios-disk", "n_clicks"),
    State("scenarios-store", "data"),
    State("active-scenario-id", "data"),
    prevent_initial_call=True,
)
def save_all_scenarios_to_disk_manual(n_clicks, scenarios, active_id):
    if not n_clicks:
        raise PreventUpdate
    disk_err = persist_scenarios_to_disk(scenarios or [], active_id)
    if disk_err:
        return html.Span(
            f"Could not save to {config_file_path().name}: {disk_err}",
            style={"color": "#d29922", "fontSize": "0.85rem"},
        )
    return html.Span(
        f"Saved {len(scenarios or [])} scenario(s) to {config_file_path().name}.",
        style={"color": "#3fb950", "fontSize": "0.85rem"},
    )

"""Life-event modal and scenario-draft life event list."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

from dash import ALL, Input, Output, State, callback, ctx, html, no_update
from dash.exceptions import PreventUpdate

from fire_web.constants import MODAL_STYLE_CLOSED, MODAL_STYLE_OPEN
from fire_web.life_events_form import life_event_row_from_inputs
from fire_web.simulation import sort_life_events_chronologically


@callback(
    Output("life-event-modal-root", "style"),
    Output("lev-edit-index", "data"),
    Output("lev-year", "value"),
    Output("lev-event-name", "value"),
    Output("lev-income", "value"),
    Output("lev-expenses", "value"),
    Output("lev-nonwage", "value"),
    Output("lev-return-pct", "value"),
    Output("lev-lump", "value"),
    Output("lev-msg", "children"),
    Input("btn-open-life-event-modal", "n_clicks"),
    Input({"type": "draft-edit-life", "idx": ALL}, "n_clicks"),
    State("scfg-life-events-draft", "data"),
    prevent_initial_call=True,
)
def open_life_event_modal(n_add, edit_clicks, draft):
    trig = ctx.triggered_id
    empty_err = html.Span()
    if trig == "btn-open-life-event-modal":
        if not n_add:
            raise PreventUpdate
        return (
            MODAL_STYLE_OPEN,
            None,
            5,
            "",
            None,
            None,
            None,
            None,
            None,
            empty_err,
        )
    if isinstance(trig, dict) and trig.get("type") == "draft-edit-life":
        idx = int(trig["idx"])
        ec = list(edit_clicks or [])
        if idx < 0 or idx >= len(ec) or int(ec[idx] or 0) < 1:
            raise PreventUpdate
        ev = (draft or [])[idx]
        fy = int(ev["year"])
        nm = ev.get("name") or ""
        return (
            MODAL_STYLE_OPEN,
            idx,
            fy,
            nm,
            ev.get("yearly_income"),
            ev.get("yearly_expenses"),
            ev.get("non_wage_income"),
            ev.get("annual_return_rate"),
            ev.get("lump_sum"),
            empty_err,
        )
    raise PreventUpdate


@callback(
    Output("life-event-modal-root", "style", allow_duplicate=True),
    Output("lev-msg", "children", allow_duplicate=True),
    Input("btn-cancel-life-modal", "n_clicks"),
    Input("btn-close-life-modal", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_life_event_modal(_a, _b):
    trig = ctx.triggered_id
    if trig not in ("btn-cancel-life-modal", "btn-close-life-modal"):
        raise PreventUpdate
    return MODAL_STYLE_CLOSED, html.Span()


@callback(
    Output("scfg-life-events-draft", "data", allow_duplicate=True),
    Output("life-event-modal-root", "style", allow_duplicate=True),
    Output("lev-msg", "children", allow_duplicate=True),
    Input("btn-save-life-modal", "n_clicks"),
    State("lev-edit-index", "data"),
    State("lev-year", "value"),
    State("lev-event-name", "value"),
    State("lev-income", "value"),
    State("lev-expenses", "value"),
    State("lev-nonwage", "value"),
    State("lev-return-pct", "value"),
    State("lev-lump", "value"),
    State("scfg-life-events-draft", "data"),
    prevent_initial_call=True,
)
def save_life_event_modal(
    n_clicks,
    edit_idx,
    y,
    evname,
    inc,
    exp,
    nw,
    rp,
    lump,
    draft,
):
    if not n_clicks:
        raise PreventUpdate
    row, err = life_event_row_from_inputs(y, evname, inc, exp, nw, rp, lump)
    if err:
        return no_update, no_update, html.Span(err, style={"color": "#d29922"})
    if row is None:
        raise PreventUpdate
    d = copy.deepcopy(list(draft or []))
    try:
        fy = int(row["year"])
    except (TypeError, ValueError):
        return no_update, no_update, html.Span("Invalid year.", style={"color": "#f85149"})
    if edit_idx is None:
        replaced = False
        for i, ex in enumerate(d):
            if int(ex["year"]) == fy:
                d[i] = row
                replaced = True
                break
        if not replaced:
            d.append(row)
    else:
        ei = int(edit_idx)
        if ei < 0 or ei >= len(d):
            return no_update, no_update, html.Span("Invalid event.", style={"color": "#f85149"})
        other_years = [int(x["year"]) for j, x in enumerate(d) if j != ei]
        if fy in other_years:
            return (
                no_update,
                no_update,
                html.Span(
                    "Another event already uses that year.",
                    style={"color": "#d29922"},
                ),
            )
        d[ei] = row
    d = sort_life_events_chronologically(d)
    return d, MODAL_STYLE_CLOSED, html.Span()


@callback(
    Output("scfg-life-events-draft", "data", allow_duplicate=True),
    Input({"type": "draft-remove-life", "idx": ALL}, "n_clicks"),
    State("scfg-life-events-draft", "data"),
    prevent_initial_call=True,
)
def remove_draft_life_event(_clicks, draft):
    trig = ctx.triggered_id
    if not isinstance(trig, dict) or trig.get("type") != "draft-remove-life":
        raise PreventUpdate
    idx = int(trig["idx"])
    cl = list(_clicks or [])
    if idx < 0 or idx >= len(cl) or int(cl[idx] or 0) < 1:
        raise PreventUpdate
    d = list(draft or [])
    if idx >= len(d):
        raise PreventUpdate
    return sort_life_events_chronologically(
        [x for i, x in enumerate(d) if i != idx]
    )


@callback(Output("scfg-life-events-list", "children"), Input("scfg-life-events-draft", "data"))
def render_scfg_life_event_list(data: Optional[List[Dict[str, Any]]]):
    if not data:
        return html.P(
            "No life events yet.",
            className="lead-muted",
            style={"fontSize": "0.82rem", "margin": 0},
        )
    blocks = []
    for i, state in enumerate(data):
        title_bit = (state.get("name") or "").strip()
        summary = (
            f"{title_bit} · year {state['year']} from now"
            if title_bit
            else f"Year {state['year']} from now"
        )
        lines = []
        for key, value in state.items():
            if key in ("year", "name") or value is None:
                continue
            label = key.replace("_", " ").title()
            if key == "annual_return_rate":
                lines.append(html.Div(f"{label}: {float(value):.1f}%"))
            else:
                lines.append(html.Div(f"{label}: ${float(value):,.0f}"))
        blocks.append(
            html.Div(
                className="future-item",
                style={"padding": "0.5rem 0.65rem"},
                children=[
                    html.Div(
                        className="scenario-le-row-head",
                        children=[
                            html.Strong(summary, style={"fontSize": "0.88rem"}),
                            html.Div(
                                style={"display": "flex", "gap": "0.35rem"},
                                children=[
                                    html.Button(
                                        "Edit",
                                        id={"type": "draft-edit-life", "idx": i},
                                        n_clicks=0,
                                        className="btn-small",
                                    ),
                                    html.Button(
                                        "Remove",
                                        id={"type": "draft-remove-life", "idx": i},
                                        n_clicks=0,
                                        className="btn-small",
                                    ),
                                ],
                            ),
                        ],
                    ),
                    (html.Div(lines) if lines else html.Div()),
                ],
            )
        )
    return html.Div(blocks, className="scfg-life-events-grid")

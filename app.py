"""
FIRE Calculator — Dash web UI entrypoint.

Logic lives in the ``fire_web`` package; this module wires the Dash app and
re-exports helpers used by tests.
"""
from __future__ import annotations

from dash import Dash

from fire_web.bootstrap import (
    _fv,
    _inputs_to_initial_state,
    _initial_to_input_values,
    _migrate_config_v1_to_scenarios,
)
from fire_web.callbacks import register_callbacks
from fire_web.layout import build_layout
from fire_web.life_events_form import _parse_optional_float
from fire_web.persist import (
    _life_events_server_get,
    _life_events_server_pop,
    _life_events_server_put,
    _patch_active_scenario_life_events,
)
from fire_web.simulation import build_simulation, format_results_table

app = Dash(__name__, title="FIRE Calculator")
app.layout = build_layout()
register_callbacks()

server = app.server

if __name__ == "__main__":
    app.run(debug=True)

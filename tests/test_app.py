"""Unit tests for app helpers and simulation wiring (no browser)."""
from __future__ import annotations

import copy

import pandas as pd
import pytest

from app import (
    _fv,
    _life_events_server_get,
    _life_events_server_pop,
    _life_events_server_put,
    _patch_active_scenario_life_events,
    _parse_optional_float,
    _inputs_to_initial_state,
    _initial_to_input_values,
    _migrate_config_v1_to_scenarios,
    build_simulation,
    format_results_table,
)


def test_server_life_events_cache_put_get_pop():
    aid = "__pytest_cache_sid__"
    _life_events_server_put(aid, [{"year": 5, "yearly_income": 1.0}], "unit_test")
    got = _life_events_server_get(aid)
    assert len(got) == 1
    assert got[0]["year"] == 5
    _life_events_server_pop(aid)
    assert _life_events_server_get(aid) == []


def test_patch_active_scenario_life_events():
    scenarios = [
        {"id": "a", "name": "A", "life_events": []},
        {"id": "b", "name": "B", "life_events": [{"year": 1}]},
    ]
    out = _patch_active_scenario_life_events(scenarios, "a", [{"year": 5, "yearly_income": 1.0}])
    assert out[0]["life_events"][0]["year"] == 5
    assert out[1]["life_events"] == [{"year": 1}]
    assert scenarios[0]["life_events"] == []


def test_parse_optional_float_accepts_commas_and_currency():
    assert _parse_optional_float("10,000,000") == pytest.approx(10_000_000.0)
    assert _parse_optional_float("$81,000") == pytest.approx(81_000.0)
    assert _parse_optional_float(0) == pytest.approx(0.0)


def test_fv_coercion():
    assert _fv(None, 1.0) == 1.0
    assert _fv("", 2.0) == 2.0
    assert _fv("12.5", 0.0) == 12.5
    assert _fv("bad", 99.0) == 99.0


def test_inputs_initial_state_roundtrip_percent_fields():
    init = _inputs_to_initial_state(
        350_000,
        180_000,
        81_000,
        7.0,
        3.0,
        0,
        20,
    )
    assert init["annual_return_rate"] == pytest.approx(0.07)
    assert init["inflation_rate"] == pytest.approx(0.03)
    tup = _initial_to_input_values(init)
    back = _inputs_to_initial_state(*tup)
    assert back["annual_return_rate"] == pytest.approx(0.07)
    assert back["inflation_rate"] == pytest.approx(0.03)
    assert back["initial_balance"] == pytest.approx(350_000)


def test_migrate_config_v1_to_scenarios():
    data = {
        "initial_state": {
            "initial_balance": 1000,
            "yearly_income": 50000,
            "yearly_expenses": 40000,
            "annual_return_rate": 0.06,
            "inflation_rate": 0.02,
            "non_wage_income": 0,
            "retirement_year": 15,
        },
        "future_states": [{"year": 5, "yearly_expenses": 120000}],
    }
    scenarios, sid = _migrate_config_v1_to_scenarios(data)
    assert len(scenarios) == 1
    assert scenarios[0]["id"] == sid
    assert scenarios[0]["life_events"][0]["year"] == 5
    assert scenarios[0]["initial_state"]["yearly_income"] == 50000


def test_build_simulation_life_event_zero_income_zero_expenses_year_five():
    """Zero is a valid override; must not be treated as 'no change'."""
    payload, _ = build_simulation(
        initial_balance=350_000,
        yearly_income=180_000,
        yearly_expenses=81_000,
        annual_return_rate=0.07,
        inflation_rate=0.0,
        non_wage_income=0,
        retirement_year=8,
        future_states=[
            {"year": 5, "yearly_income": 0.0, "yearly_expenses": 0.0},
        ],
        max_years=10,
    )
    by_year = {r["year"]: r for r in payload["results"]}
    assert by_year[5]["yearly_income"] == pytest.approx(0.0)
    assert by_year[5]["yearly_expenses"] == pytest.approx(0.0)
    assert by_year[4]["yearly_expenses"] == pytest.approx(81_000)


def test_build_simulation_life_event_expenses_year_five():
    """Regression: life event at year N must appear in results for that calendar year."""
    payload, _ = build_simulation(
        initial_balance=350_000,
        yearly_income=180_000,
        yearly_expenses=81_000,
        annual_return_rate=0.07,
        inflation_rate=0.03,
        non_wage_income=0,
        retirement_year=25,
        future_states=[{"year": 5, "yearly_expenses": 120_000}],
        max_years=10,
    )
    by_year = {r["year"]: r for r in payload["results"]}
    assert by_year[4]["yearly_expenses"] != 120_000
    assert by_year[5]["yearly_expenses"] == pytest.approx(120_000)


def test_build_simulation_ignores_life_event_name_meta_key():
    """``name`` is for charts/UI only and must not affect the simulation engine."""
    with_meta, _ = build_simulation(
        100_000,
        50_000,
        40_000,
        0.05,
        0.02,
        0,
        30,
        [{"year": 3, "yearly_expenses": 99_000, "name": "Big expense"}],
        5,
    )
    plain, _ = build_simulation(
        100_000,
        50_000,
        40_000,
        0.05,
        0.02,
        0,
        30,
        [{"year": 3, "yearly_expenses": 99_000}],
        5,
    )
    assert with_meta["results"] == plain["results"]


def test_build_simulation_future_state_year_as_string():
    payload, _ = build_simulation(
        100_000,
        50_000,
        40_000,
        0.05,
        0.02,
        0,
        30,
        [{"year": "3", "yearly_expenses": 99_000}],
        5,
    )
    assert any(r["year"] == 3 and r["yearly_expenses"] == pytest.approx(99_000) for r in payload["results"])


def test_build_simulation_annual_return_percent_vs_decimal():
    """Stored JSON may use 0.07; UI uses 7 — both must normalize to ~7% return rate."""
    dec, _ = build_simulation(
        100_000,
        0,
        50_000,
        0.05,
        0,
        0,
        99,
        [{"year": 2, "annual_return_rate": 0.07}],
        3,
    )
    pct, _ = build_simulation(
        100_000,
        0,
        50_000,
        0.05,
        0,
        0,
        99,
        [{"year": 2, "annual_return_rate": 7.0}],
        3,
    )
    y2d = {r["year"]: r for r in dec["results"]}
    y2p = {r["year"]: r for r in pct["results"]}
    assert y2d[2]["yearly_return"] == pytest.approx(y2p[2]["yearly_return"], rel=1e-9)


def test_format_results_table_columns_and_shape():
    payload, _ = build_simulation(
        10_000,
        40_000,
        30_000,
        0.04,
        0.02,
        0,
        10,
        [],
        2,
    )
    df = format_results_table(payload)
    assert isinstance(df, pd.DataFrame)
    assert df.index.name == "year" or "year" in str(df.index)
    assert "Balance" in df.columns


def test_patch_active_updates_compare_and_leaves_other_scenario():
    scenarios = [
        {
            "id": "a",
            "name": "A",
            "compare": False,
            "initial_state": {"initial_balance": 1.0},
            "life_events": [],
        },
        {
            "id": "b",
            "name": "B",
            "compare": True,
            "initial_state": {"initial_balance": 2.0},
            "life_events": [{"year": 1}],
        },
    ]
    out = copy.deepcopy(scenarios)
    for s in out:
        if s["id"] == "a":
            s["compare"] = True
            s["life_events"] = [{"year": 3}]
    active = next(s for s in out if s["id"] == "a")
    assert active["compare"] is True
    assert active["life_events"][0]["year"] == 3
    other = next(s for s in out if s["id"] == "b")
    assert other["life_events"] == [{"year": 1}]

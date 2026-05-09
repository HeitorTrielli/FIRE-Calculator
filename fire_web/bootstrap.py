"""Config loading, default scenarios, and sidebar/modal input coercion."""

from __future__ import annotations

import copy
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fire_web.constants import DEFAULT_CONFIG_FILE
from fire_web.simulation import sort_life_events_chronologically


def repo_root() -> Path:
    """Directory containing ``app.py`` / package parent (works regardless of cwd)."""
    return Path(__file__).resolve().parent.parent


def config_file_path() -> Path:
    return repo_root() / DEFAULT_CONFIG_FILE


def try_load_default_config() -> Optional[Dict[str, Any]]:
    path = config_file_path()
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None


_cfg = try_load_default_config()
_init = _cfg.get("initial_state", {}) if _cfg else {}
_future_initial: List[Dict[str, Any]] = (
    list(_cfg.get("future_states", [])) if _cfg else []
)
CONFIG_HAD_INITIAL = bool(_cfg and _cfg.get("initial_state"))


def _pct(key: str, default: float = 0.0) -> float:
    v = _init.get(key, default)
    if v is None:
        return default
    return round(float(v) * 100.0, 2)


def _num(key: str, default: float = 0.0) -> float:
    v = _init.get(key, default)
    if v is None:
        return default
    return round(float(v), 2)


def _int(key: str, default: int = 1) -> int:
    v = _init.get(key, default)
    if v is None:
        return default
    return int(v)


def initial_state_dict_from_defaults() -> Dict[str, Any]:
    """Persisted shape: rates as decimals (same as JSON download)."""
    if not _init:
        return {
            "initial_balance": 0.0,
            "yearly_income": 0.0,
            "yearly_expenses": 0.0,
            "annual_return_rate": 0.0,
            "inflation_rate": 0.0,
            "non_wage_income": 0.0,
            "input_income_monthly": False,
            "input_expenses_monthly": False,
            "input_non_wage_monthly": False,
        }
    return {
        "initial_balance": _num("initial_balance", 0),
        "yearly_income": _num("yearly_income", 0),
        "yearly_expenses": _num("yearly_expenses", 0),
        "annual_return_rate": float(_init.get("annual_return_rate", 0) or 0),
        "inflation_rate": float(_init.get("inflation_rate", 0) or 0),
        "non_wage_income": _num("non_wage_income", 0),
        "input_income_monthly": bool(_init.get("input_income_monthly")),
        "input_expenses_monthly": bool(_init.get("input_expenses_monthly")),
        "input_non_wage_monthly": bool(_init.get("input_non_wage_monthly")),
    }


def bootstrap_scenarios() -> Tuple[List[Dict[str, Any]], str]:
    sid = uuid.uuid4().hex[:12]
    scen: Dict[str, Any] = {
        "id": sid,
        "name": "Baseline",
        "compare": True,
        "initial_state": initial_state_dict_from_defaults(),
        "life_events": sort_life_events_chronologically(list(_future_initial)),
    }
    return [scen], sid


def _fv(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _monthly_toggle_on(v: Any) -> bool:
    """``dcc.Checklist`` value is a list; ``True`` also accepted for tests."""
    if v is True:
        return True
    return bool(v) and "m" in v


def _monthly_checklist_value(on: bool) -> List[str]:
    return ["m"] if on else []


def _inputs_to_initial_state(
    initial_balance: Any,
    yearly_income: Any,
    yearly_expenses: Any,
    annual_return_pct: Any,
    inflation_pct: Any,
    non_wage_income: Any,
    income_monthly_toggle: Any = None,
    expenses_monthly_toggle: Any = None,
    non_wage_monthly_toggle: Any = None,
) -> Dict[str, Any]:
    inc_m = _monthly_toggle_on(income_monthly_toggle)
    exp_m = _monthly_toggle_on(expenses_monthly_toggle)
    nw_m = _monthly_toggle_on(non_wage_monthly_toggle)
    yi = _fv(yearly_income, 0.0)
    ye = _fv(yearly_expenses, 0.0)
    nw = _fv(non_wage_income, 0.0)
    if inc_m:
        yi *= 12.0
    if exp_m:
        ye *= 12.0
    if nw_m:
        nw *= 12.0
    return {
        "initial_balance": _fv(initial_balance, 0.0),
        "yearly_income": yi,
        "yearly_expenses": ye,
        "annual_return_rate": _fv(annual_return_pct, 0.0) / 100.0,
        "inflation_rate": _fv(inflation_pct, 0.0) / 100.0,
        "non_wage_income": nw,
        "input_income_monthly": inc_m,
        "input_expenses_monthly": exp_m,
        "input_non_wage_monthly": nw_m,
    }


def _initial_to_input_values(init: Dict[str, Any]) -> Tuple[Any, ...]:
    inc_m = bool(init.get("input_income_monthly"))
    exp_m = bool(init.get("input_expenses_monthly"))
    nw_m = bool(init.get("input_non_wage_monthly"))
    yi = float(init.get("yearly_income", 0) or 0)
    ye = float(init.get("yearly_expenses", 0) or 0)
    nw = float(init.get("non_wage_income", 0) or 0)
    if inc_m:
        yi = yi / 12.0
    if exp_m:
        ye = ye / 12.0
    if nw_m:
        nw = nw / 12.0
    return (
        init.get("initial_balance", 0),
        yi,
        ye,
        round(float(init.get("annual_return_rate", 0) or 0) * 100.0, 2),
        round(float(init.get("inflation_rate", 0) or 0) * 100.0, 2),
        nw,
        _monthly_checklist_value(inc_m),
        _monthly_checklist_value(exp_m),
        _monthly_checklist_value(nw_m),
    )


def migrate_config_v1_to_scenarios(data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
    """Wrap legacy {initial_state, future_states} as one scenario."""
    sid = uuid.uuid4().hex[:12]
    init = data.get("initial_state") or {}
    ry = int(init.get("retirement_year", 1) or 1)
    life_events = list(data.get("future_states", []))
    life_events.append(
        {"year": ry, "name": "Retirement year", "yearly_income": 0.0},
    )
    life_events = sort_life_events_chronologically(life_events)
    scen = {
        "id": sid,
        "name": "Baseline",
        "compare": True,
        "initial_state": {
            "initial_balance": float(init.get("initial_balance", 0) or 0),
            "yearly_income": float(init.get("yearly_income", 0) or 0),
            "yearly_expenses": float(init.get("yearly_expenses", 0) or 0),
            "annual_return_rate": float(init.get("annual_return_rate", 0) or 0),
            "inflation_rate": float(init.get("inflation_rate", 0) or 0),
            "non_wage_income": float(init.get("non_wage_income", 0) or 0),
            "input_income_monthly": bool(init.get("input_income_monthly")),
            "input_expenses_monthly": bool(init.get("input_expenses_monthly")),
            "input_non_wage_monthly": bool(init.get("input_non_wage_monthly")),
        },
        "life_events": life_events,
    }
    return [scen], sid


def _upgrade_scenario_retirement_field(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Drop legacy ``initial_state.retirement_year``; add an explicit life event once if needed."""
    s = copy.deepcopy(scenario)
    init = s.get("initial_state")
    if not isinstance(init, dict):
        return s
    raw = init.pop("retirement_year", None)
    if raw is None:
        return s
    try:
        y = max(1, int(raw))
    except (TypeError, ValueError):
        return s
    le = list(s.get("life_events") or [])
    has_retirement_row = any(
        str(e.get("name") or "").strip().lower() == "retirement year" for e in le
    )
    if not has_retirement_row:
        le.append({"year": y, "name": "Retirement year", "yearly_income": 0.0})
        s["life_events"] = sort_life_events_chronologically(le)
    return s


def initial_scenarios_from_disk() -> Tuple[List[Dict[str, Any]], str]:
    if _cfg is None:
        return bootstrap_scenarios()
    if _cfg.get("version") == 2 and _cfg.get("scenarios"):
        scenarios = [_upgrade_scenario_retirement_field(s) for s in _cfg["scenarios"]]
        aid = _cfg.get("active_scenario_id") or scenarios[0]["id"]
        return scenarios, aid
    if _cfg.get("initial_state") is not None:
        return migrate_config_v1_to_scenarios(_cfg)
    return bootstrap_scenarios()


SCENARIOS_BOOTSTRAP, ACTIVE_BOOTSTRAP = initial_scenarios_from_disk()

SCFG_BOOT_VALUES = _initial_to_input_values(SCENARIOS_BOOTSTRAP[0]["initial_state"])


def blank_initial_state() -> Dict[str, Any]:
    return {
        "initial_balance": 0.0,
        "yearly_income": 0.0,
        "yearly_expenses": 0.0,
        "annual_return_rate": 0.0,
        "inflation_rate": 0.0,
        "non_wage_income": 0.0,
        "input_income_monthly": False,
        "input_expenses_monthly": False,
        "input_non_wage_monthly": False,
    }


BLANK_CFG_TUPLE = _initial_to_input_values(blank_initial_state())


def reorder_scenarios_by_id_order(
    scenarios: List[Dict[str, Any]],
    order: List[str],
) -> Optional[List[Dict[str, Any]]]:
    """Return ``scenarios`` permuted to ``order`` if valid; otherwise ``None``."""
    if not scenarios or not order or len(order) != len(scenarios):
        return None
    ids_present = {str(s["id"]) for s in scenarios}
    if {str(x) for x in order} != ids_present:
        return None
    by_id = {str(s["id"]): s for s in scenarios}
    return [by_id[str(i)] for i in order]


def duplicate_scenario_record(source: Dict[str, Any]) -> Dict[str, Any]:
    """Deep-copy a scenario with a new id and ``Name (copy)``; life events stay ordered."""
    from fire_web.simulation import sort_life_events_chronologically

    new_id = uuid.uuid4().hex[:12]
    out = copy.deepcopy(source)
    out["id"] = new_id
    base = (out.get("name") or "Untitled").strip() or "Untitled"
    out["name"] = f"{base} (copy)"
    out["life_events"] = sort_life_events_chronologically(
        list(out.get("life_events") or [])
    )
    out["compare"] = bool(source.get("compare", True))
    return out


_migrate_config_v1_to_scenarios = migrate_config_v1_to_scenarios

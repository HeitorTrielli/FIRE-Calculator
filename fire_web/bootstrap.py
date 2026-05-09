"""Config loading, default scenarios, and sidebar/modal input coercion."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fire_web.constants import DEFAULT_CONFIG_FILE


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
            "retirement_year": 1,
        }
    return {
        "initial_balance": _num("initial_balance", 0),
        "yearly_income": _num("yearly_income", 0),
        "yearly_expenses": _num("yearly_expenses", 0),
        "annual_return_rate": float(_init.get("annual_return_rate", 0) or 0),
        "inflation_rate": float(_init.get("inflation_rate", 0) or 0),
        "non_wage_income": _num("non_wage_income", 0),
        "retirement_year": _int("retirement_year", 1),
    }


def bootstrap_scenarios() -> Tuple[List[Dict[str, Any]], str]:
    sid = uuid.uuid4().hex[:12]
    scen: Dict[str, Any] = {
        "id": sid,
        "name": "Baseline",
        "compare": True,
        "initial_state": initial_state_dict_from_defaults(),
        "life_events": list(_future_initial),
    }
    return [scen], sid


def _fv(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _inputs_to_initial_state(
    initial_balance: Any,
    yearly_income: Any,
    yearly_expenses: Any,
    annual_return_pct: Any,
    inflation_pct: Any,
    non_wage_income: Any,
    retirement_year: Any,
) -> Dict[str, Any]:
    try:
        ry = int(retirement_year) if retirement_year not in (None, "") else 1
    except (TypeError, ValueError):
        ry = 1
    return {
        "initial_balance": _fv(initial_balance, 0.0),
        "yearly_income": _fv(yearly_income, 0.0),
        "yearly_expenses": _fv(yearly_expenses, 0.0),
        "annual_return_rate": _fv(annual_return_pct, 0.0) / 100.0,
        "inflation_rate": _fv(inflation_pct, 0.0) / 100.0,
        "non_wage_income": _fv(non_wage_income, 0.0),
        "retirement_year": ry,
    }


def _initial_to_input_values(init: Dict[str, Any]) -> Tuple[Any, ...]:
    return (
        init.get("initial_balance", 0),
        init.get("yearly_income", 0),
        init.get("yearly_expenses", 0),
        round(float(init.get("annual_return_rate", 0) or 0) * 100.0, 2),
        round(float(init.get("inflation_rate", 0) or 0) * 100.0, 2),
        init.get("non_wage_income", 0),
        int(init.get("retirement_year", 1) or 1),
    )


def migrate_config_v1_to_scenarios(data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
    """Wrap legacy {initial_state, future_states} as one scenario."""
    sid = uuid.uuid4().hex[:12]
    init = data.get("initial_state") or {}
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
            "retirement_year": int(init.get("retirement_year", 1) or 1),
        },
        "life_events": list(data.get("future_states", [])),
    }
    return [scen], sid


def initial_scenarios_from_disk() -> Tuple[List[Dict[str, Any]], str]:
    if _cfg is None:
        return bootstrap_scenarios()
    if _cfg.get("version") == 2 and _cfg.get("scenarios"):
        scenarios = _cfg["scenarios"]
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
        "retirement_year": 1,
    }


BLANK_CFG_TUPLE = _initial_to_input_values(blank_initial_state())

_migrate_config_v1_to_scenarios = migrate_config_v1_to_scenarios

"""Disk persistence and server-side mirror of scenario ``life_events`` (Dash timing workaround)."""

from __future__ import annotations

import copy
import json
from typing import Any, Dict, List, Optional

from fire_debug import log_event
from fire_web.bootstrap import config_file_path


def persist_scenarios_to_disk(
    scenarios: List[Dict[str, Any]], active_id: Optional[str]
) -> Optional[str]:
    """Write scenarios to ``fire_config.json``. Returns error message or ``None``."""
    if not scenarios:
        return "No scenarios to save."
    valid_ids = {s["id"] for s in scenarios}
    aid = active_id if active_id in valid_ids else scenarios[0]["id"]
    payload = {
        "version": 2,
        "active_scenario_id": aid,
        "scenarios": copy.deepcopy(scenarios),
    }
    path = config_file_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4)
        life_events_server_reset_from_scenarios(scenarios, "persist_disk")
        log_event(
            "persist_scenarios_disk",
            path=str(path),
            n=len(scenarios),
            active_scenario_id=aid,
        )
    except OSError as e:
        log_event("persist_scenarios_disk_error", path=str(path), error=str(e))
        return str(e)
    return None


_SERVER_LIFE_EVENTS_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def life_events_server_put(
    aid: Optional[str], events: List[Dict[str, Any]], reason: str
) -> None:
    if not aid:
        return
    _SERVER_LIFE_EVENTS_CACHE[aid] = copy.deepcopy(events)
    log_event(
        "life_events_SERVER_CACHE_PUT",
        reason=reason,
        active_id=aid,
        n=len(events),
    )


def life_events_server_get(aid: Optional[str]) -> List[Dict[str, Any]]:
    if not aid:
        return []
    got = _SERVER_LIFE_EVENTS_CACHE.get(aid)
    log_event(
        "life_events_SERVER_CACHE_GET",
        active_id=aid,
        cache_hit=got is not None,
        n=len(got or []),
    )
    return copy.deepcopy(got) if got else []


def life_events_server_pop(aid: Optional[str]) -> None:
    if not aid:
        return
    _SERVER_LIFE_EVENTS_CACHE.pop(aid, None)
    log_event("life_events_SERVER_CACHE_POP", active_id=aid)


def life_events_server_reset_from_scenarios(
    scenarios: Optional[List[Dict[str, Any]]], reason: str
) -> None:
    global _SERVER_LIFE_EVENTS_CACHE
    _SERVER_LIFE_EVENTS_CACHE.clear()
    if not scenarios:
        log_event("life_events_SERVER_CACHE_RESET", reason=reason, n_scenarios=0)
        return
    for s in scenarios:
        _SERVER_LIFE_EVENTS_CACHE[s["id"]] = copy.deepcopy(
            list(s.get("life_events") or [])
        )
    log_event(
        "life_events_SERVER_CACHE_RESET",
        reason=reason,
        counts={k: len(v) for k, v in _SERVER_LIFE_EVENTS_CACHE.items()},
    )


def life_events_server_debug_snapshot() -> Dict[str, Any]:
    return {k: copy.deepcopy(v) for k, v in _SERVER_LIFE_EVENTS_CACHE.items()}


def patch_active_scenario_life_events(
    scenarios: Optional[List[Dict[str, Any]]],
    active_id: Optional[str],
    life_events: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Keep ``scenarios-store`` life_events aligned with the sidebar."""
    out = copy.deepcopy(scenarios or [])
    if not active_id:
        return out
    for s in out:
        if s.get("id") == active_id:
            s["life_events"] = list(life_events)
            break
    return out


# Private-style names for tests / legacy imports
_life_events_server_put = life_events_server_put
_life_events_server_get = life_events_server_get
_life_events_server_pop = life_events_server_pop
_persist_scenarios_to_disk = persist_scenarios_to_disk
_patch_active_scenario_life_events = patch_active_scenario_life_events

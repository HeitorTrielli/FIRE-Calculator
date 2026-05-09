"""Shared UI constants (styles, filenames)."""

from __future__ import annotations

from typing import Any, Dict

DEFAULT_CONFIG_FILE = "fire_config.json"

DT_CELL = {
    "textAlign": "left",
    "padding": "6px",
    "backgroundColor": "#21262d",
    "color": "#e6edf3",
    "border": "1px solid #30363d",
}
DT_HEADER = {
    "fontWeight": "600",
    "backgroundColor": "#161b22",
    "color": "#e6edf3",
    "border": "1px solid #30363d",
}

MODAL_STYLE_CLOSED: Dict[str, Any] = {"display": "none"}
MODAL_STYLE_OPEN: Dict[str, Any] = {
    "display": "flex",
    "position": "fixed",
    "left": 0,
    "top": 0,
    "right": 0,
    "bottom": 0,
    "backgroundColor": "rgba(0, 0, 0, 0.72)",
    "zIndex": 10000,
    "alignItems": "center",
    "justifyContent": "center",
    "padding": "1rem",
}

OVERLAY_COLORS = [
    "#58a6ff",
    "#3fb950",
    "#f85149",
    "#d29922",
    "#a371f7",
    "#ff7eb6",
    "#79c0ff",
]

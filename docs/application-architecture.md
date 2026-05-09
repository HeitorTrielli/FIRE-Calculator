# FIRE Calculator — Application Architecture

This document describes how the Dash web application is structured, how data flows through it, and how it connects to the simulation engine. For product-focused usage, see the project `README.md`.

## 1. Technology stack

| Layer | Technology |
|-------|------------|
| UI framework | [Dash](https://dash.plotly.com/) (Plotly) |
| Charts | Plotly Graph Objects (overview + gallery figures) |
| Tables | `dash_table.DataTable` |
| Numerics / tables | NumPy, Pandas |
| Simulation core | Custom modules: `fire_calculator.py`, `fire_state.py` |
| Optional diagnostics | `fire_debug.py` (structured logging) |

The browser loads Dash’s React bundle; Python callbacks run on the server and update component props (`dcc.Store`, `html.Div`, `dcc.Graph`, etc.).

---

## 2. Repository layout (application-relevant)

```
FIRE-Calculator/
├── app.py                 # Dash entrypoint: app instance, layout, callback registration
├── fire_web/              # All UI logic (recommended place for new features)
│   ├── constants.py       # Modal styles, DataTable styles, default filename
│   ├── bootstrap.py       # Config load path, default scenarios, input coercion
│   ├── persist.py         # fire_config.json writes + in-memory life_events mirror
│   ├── simulation.py      # Orchestrates engine: build_simulation, charts, results DF
│   ├── life_events_form.py # Parse modal inputs → stored life-event dict
│   ├── layout.py          # build_layout() → full component tree
│   └── callbacks/
│       ├── __init__.py    # register_callbacks()
│       ├── scenario_ui.py # Sidebar scenarios + scenario configuration modal
│       ├── life_event_ui.py # Nested life-event modal + draft list in scenario modal
│       └── simulation_ui.py # Calculate, live summary, main area, upload/download
├── fire_calculator.py     # Year-by-year projection + milestones
├── fire_state.py          # FIREState, FIREStateManager (timeline of overrides)
├── fire_debug.py          # Logging helpers for traces
├── assets/
│   └── style.css          # Dark theme, modal grids, metrics (loaded automatically by Dash)
├── docs/
│   └── application-architecture.md   # This file
├── tests/
│   └── test_app.py        # Unit tests for helpers and simulation wiring
└── fire_config.json       # Optional; persisted scenarios (created/updated by the app)
```

Static assets under `assets/` are served by Dash at `/assets/…` when referenced from the layout (implicitly via `Dash(__name__)`).

---

## 3. Application bootstrap (`app.py`)

1. **`Dash(__name__, title="FIRE Calculator")`** — Creates the app; `__name__` enables asset discovery.
2. **`app.layout = build_layout()`** (`fire_web/layout.py`) — Single layout tree with fixed component IDs used by callbacks.
3. **`register_callbacks()`** (`fire_web/callbacks/__init__.py`) — Imports callback modules so `@callback`-decorated functions register with Dash **after** the layout exists (required ordering).

The module **`server = app.server`** exposes the WSGI app for production servers (e.g. Gunicorn).

For backward compatibility with tests and notebooks, `app.py` re-exports selected helpers (`build_simulation`, `_fv`, persist cache functions, etc.).

---

## 4. Configuration and startup data (`fire_web/bootstrap.py`)

### 4.1 Config file location

- **Path**: `{repository_root}/fire_config.json`
- **Resolution**: `repo_root()` is the parent of the `fire_web` package (project directory containing `app.py`), not necessarily the process current working directory.

### 4.2 First-run behavior

- If `fire_config.json` is missing or invalid, the app still starts.
- **Default scenario list**: one scenario named `"Baseline"` built from:
  - Legacy keys in JSON: `initial_state` + optional `future_states` (see §6).
  - If no file: zeros / defaults for financial fields.

Module-level constants computed at import:

- `SCENARIOS_BOOTSTRAP`, `ACTIVE_BOOTSTRAP` — initial `dcc.Store` payloads.
- `SCFG_BOOT_VALUES` — tuple of UI defaults for the scenario modal derived from the first scenario’s `initial_state`.
- `CONFIG_HAD_INITIAL` — whether loaded JSON contained `initial_state` (used for empty-state hints on first paint).

### 4.3 Input coercion

- **`_inputs_to_initial_state`** — Maps modal/sidebar strings and numbers into persisted `initial_state` (percent fields → decimals for rates).
- **`_fv`** — Safe float parsing with defaults for blank/invalid inputs.
- **`_initial_to_input_values`** — Inverse mapping for editing (decimals → percent display where applicable).

---

## 5. Domain model: scenarios and life events

### 5.1 Scenario (in-memory / JSON)

Each scenario is a dictionary:

| Field | Type | Meaning |
|-------|------|---------|
| `id` | string | Stable identifier (short hex-like string). |
| `name` | string | Display name; editable as the scenario modal title. |
| `compare` | bool | If true, included in multi-series balance overlay on the chart. |
| `initial_state` | object | Year 0 financial parameters (see below). |
| `life_events` | array | Ordered list of overrides keyed by simulation year (see §5.3). |

### 5.2 `initial_state`

| Key | Stored format | UI notes |
|-----|----------------|----------|
| `initial_balance` | dollars | May be negative (debt). |
| `yearly_income` | dollars/year | Wage income until retirement. |
| `yearly_expenses` | dollars/year | Base expenses; inflation may apply year-over-year when no override row exists. |
| `annual_return_rate` | **decimal** (e.g. `0.07`) | Modal shows percent (e.g. `7`). |
| `inflation_rate` | **decimal** | Same as above. |
| `non_wage_income` | dollars/year | Continues after retirement when wage drops out. |
| `retirement_year` | integer | Simulation year index when wage income stops (year 0 = start). |

### 5.3 Life events (`life_events`)

Each item is a partial override at a given **`year`** (integer, years from start):

- Financial keys understood by the engine include: `yearly_income`, `yearly_expenses`, `annual_return_rate`, `non_wage_income`, `lump_sum`, `inflation_rate` (subset used depends on `fire_state` / registration).
- **`name`** is metadata for chart annotations only; it is **not** passed into `FIREStateManager.add_future_state` as a numeric parameter (see `LIFE_EVENT_META_KEYS` in `fire_web/simulation.py`).

The UI sorts life events chronologically by `year` when saving or displaying drafts.

Life-event modal validation (`life_events_form.py`) requires at least one **financial** change in addition to `year` (or the save is rejected with a message).

---

## 6. JSON file formats (`fire_config.json`)

### 6.1 Version 2 (current)

```json
{
  "version": 2,
  "active_scenario_id": "<id>",
  "scenarios": [ /* array of scenario objects */ ]
}
```

Written whenever scenarios are persisted (save scenario, toggle compare if persisted, activate, remove scenario, successful upload, etc.).

### 6.2 Legacy version 1

Older files had top-level `initial_state` and `future_states` without `version: 2`. **`migrate_config_v1_to_scenarios`** wraps them into a single `"Baseline"` scenario (`fire_web/bootstrap.py`). Upload and migration paths still accept this shape.

---

## 7. Persistence and the life-events server cache (`fire_web/persist.py`)

### 7.1 Disk

- **`persist_scenarios_to_disk(scenarios, active_id)`** writes the v2 JSON atomically from the in-memory scenario list.
- Returns `None` on success or an error **string** on `OSError` (permissions, disk full, etc.). The UI surfaces non-fatal warnings when save partly fails.

### 7.2 In-memory cache per scenario id

Dash client callbacks can momentarily send **stale** `dcc.Store` state immediately after another callback updates scenarios (especially life events edited only in the modal draft). To avoid running Calculate with empty life events:

- **`life_events_server_put` / `get` / `pop`** mirror `life_events` per scenario id on the server.
- **`life_events_server_reset_from_scenarios`** rebuilds the cache from the full scenario list whenever disk persistence succeeds.

**`run_calculate`** (`simulation_ui.py`) merges: if the active scenario’s `life_events` from `State` is empty, it falls back to **`life_events_server_get(active_id)`** and logs the merge source for debugging.

---

## 8. Simulation pipeline (`fire_web/simulation.py` + engine)

### 8.1 `build_simulation(...)`

1. Builds **`FIREState`** for year 0 via `FIREState.create_initial_state`.
2. Registers **`FIREStateManager`** rows for each life event year with non-meta parameters (normalizes `annual_return_rate` if stored as percent > 1).
3. **`FIRECalculator.calculate_until_year(max_years)`** walks year 0 → target, applying `calculate_next_year`.
4. Computes **million-dollar milestones** via `FIRECalculator.calculate_million_dollar_milestones`.
5. Returns a **payload** used by charts and table: `results`, `milestones`, `max_years`, `initial` snapshot.

### 8.2 Chart overlays

For each scenario with `compare` true (or fallback to active only), **`sim_from_scenario`** runs the same pipeline with that scenario’s `initial_state` and `life_events`. The active scenario’s payload may be reused if ids match to avoid duplicate work.

### 8.3 `build_figure`

Renders a **single** nominal-balance chart (with optional scenario overlays), plus milestone and life-event vertical lines from `life_events_display` on **`run_calculate`**. Additional charts live in **`fire_web/chart_gallery.py`**.

### 8.4 Detailed results table

**`format_results_table`** builds a Pandas `DataFrame` with formatted currency strings for display. The UI uses **`page_action="none"`** so all rows appear when the accordion is opened.

---

## 9. Callback organization (`fire_web/callbacks/`)

Callbacks are split by feature area. All use Dash `callback`/`ctx` and shared stores.

### 9.1 `scenario_ui.py`

- Renders sidebar scenario cards (`scenario-list-container`).
- Opens/closes **scenario configuration modal**; seeds fields from selected scenario or blanks for “Add scenario”.
- **Save scenario**: merges draft life events, updates or appends scenario, persists, updates server cache.
- **Compare** checkbox, **Active** button, **Remove** scenario (enforces at least one scenario).

### 9.2 `life_event_ui.py`

- Opens nested **life event** modal (add vs edit by draft index).
- **Save event**: validates row, resolves duplicate-year replace rules, sorts draft, closes modal.
- **Remove** draft event by index.
- Renders **`scfg-life-events-list`** from `scfg-life-events-draft` store.

### 9.3 `simulation_ui.py`

- **Live summary** text from active scenario + horizon input.
- **Calculate**: builds simulation payload + overlays, writes **`sim-output-store`**.
- **Main panel**: metrics cards, graph, milestone cards, DataTable, hints when no run yet.
- **Download** / **Upload** configuration JSON (v2 or legacy v1).

Duplicate-output patterns (`allow_duplicate=True`) follow Dash rules for stores updated from multiple callbacks.

---

## 10. UI constants (`fire_web/constants.py`)

- **`DEFAULT_CONFIG_FILE`** — `"fire_config.json"` (shared with download default filename).
- **`MODAL_STYLE_OPEN` / `MODAL_STYLE_CLOSED`** — Full-screen overlay flex centering for modals.
- **`DT_CELL` / `DT_HEADER`** — Dark-theme styling for `DataTable`.

---

## 11. Styling (`assets/style.css`)

Not exhaustive:

- **`.app-shell`** — Sidebar + main flex layout.
- **`.metrics-row`**, **`.milestone-grid`** — Responsive grids for summary cards.
- **`#scenario-config-modal-root`**, **`#life-event-modal-root`** — Modal panels, two-column assumption grids, title inputs (`.modal-title-input`).
- Life-event nested modal uses higher `z-index` so it stacks above the scenario modal.

---

## 12. Testing (`tests/test_app.py`)

Tests avoid a browser: they import helpers re-exported from **`app.py`** (or could import from `fire_web` directly) and assert:

- Float parsing, initial-state round-trip, migration v1 → scenarios.
- **`build_simulation`** behavior (life events at year N, meta `name` ignored, return rate percent vs decimal).
- **`format_results_table`** shape.
- Life-events server cache and **`patch_active_scenario_life_events`** (pattern-style scenario mutation).

Run: `python -m pytest tests/test_app.py`.

---

## 13. Running and deployment

- **Development**: `python app.py` → default Dash server (typically `http://127.0.0.1:8050`).
- **Production**: Use `server = app.server` with a WSGI/HTTP gateway; ensure `fire_web` package and `assets/` are deployed with the same layout relative to `app.py`.

Environment variables follow Dash/Flask conventions where applicable.

---

## 14. Extension points

| Goal | Where to change |
|------|------------------|
| New sidebar control | `fire_web/layout.py` + new callback in an appropriate `callbacks/*.py` |
| New persisted field on scenario | Modal in `layout.py`, save/load in `scenario_ui.py`, migration if needed |
| Simulation rule change | Prefer `fire_calculator.py` / `fire_state.py`; wire params in `simulation.build_simulation` |
| New chart series | `simulation.build_figure` + payload from `run_calculate` |
| Additional exports for tests | `app.py` re-exports or import `fire_web` in tests directly |

---

## 15. Related documents

- `README.md` — User-facing features and quick start.
- `docs/implementation-plan-scenarios.md` — Historical / planning notes for scenarios feature work.

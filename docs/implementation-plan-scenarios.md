# Scenario UX — implementation plan

This document tracks the upgrade from a single implicit configuration to **named scenarios**, **life-event** wording, **comparison**, and supporting UX. Work is split into phases so we can ship incrementally.

---

## Goals (from product discussion)

| Idea | Intent |
|------|--------|
| **Guided scenarios** | Multiple saved setups with clear names, not one anonymous blob. |
| **Free-form life events** | Keep full flexibility: any year, optional fields, inherit behavior unchanged. |
| **Compare** | Run several named scenarios and see results together (especially balance paths). |
| **“Add life event”** | Frame future rows as time-stamped events, not abstract “state changes.” |
| **Presets** | Optional starter templates (good for demos to friends/family); low priority. |
| **First-run wizard** | Optional step-by-step first visit; can come after core scenario model. |
| **Strict config files (old “point 5”)** | See [Config validation](#config-validation-what-point-5-meant) below. |
| **Live summary** | Always-visible recap of what is being modeled (no Streamlit rerun limits). |
| **Table editor** | Optional later: spreadsheet-style grid for life events instead of add-form only. |

---

## Config validation (what “point 5” meant)

**JSON Schema** is a small JSON document that *describes allowed shape* of your config file (required keys, types, min/max). Tools can:

- Validate uploads **before** merging into the app and show errors like:  
  `initial_state.annual_return_rate must be a number between 0 and 1`.
- Generate editor autocomplete in some IDEs.

It does **not** replace your app; it’s an optional contract for `fire_config.json`. Implementation can be phased: start with manual checks in Python (`if not 0 <= r <= 0.25: …`), add a `schema.json` file later if you want strict validation.

---

## Data model

### Scenario object

```text
id:            string (stable, e.g. short uuid)
name:          string (user-visible)
compare:       bool   (include trajectory in multi-scenario overlay chart)
initial_state: same keys as today’s JSON initial_state (decimals for rates)
life_events:   same list shape as today’s future_states (year + optional overrides)
```

### Session / persistence stores (Dash)

- `scenarios-store`: `list` of scenario objects.
- `active-scenario-id`: `string` — which scenario drives the sidebar inputs + life-event list.
- `sim-output-store`: simulation results (extended to hold active + comparison payloads).

### File format versioning

- **v1 (legacy):** `{ "initial_state": {...}, "future_states": [...] }`
- **v2:** `{ "version": 2, "scenarios": [...], "active_scenario_id": "..." }`

Load path: if `version == 2`, use as-is; else wrap v1 into a single scenario named `"Baseline"` (or imported filename).

---

## UI behavior

### Scenario toolbar (sidebar, above “Initial Financial State”)

- Dropdown: pick **active scenario** (loads its `initial_state` + `life_events` into the form).
- Text input: **rename** active scenario.
- Checkbox: **Include in comparison chart** (maps to `compare`).
- Buttons: **New** (blank or minimal defaults), **Duplicate** (copy active), **Delete** (guard: keep ≥1 scenario).

### Life events

- Section title: **Life events** (not “future states”).
- Primary button: **Add life event** (same underlying logic as before).
- Help copy: optional fields inherit from the path implied by prior events + inflation (unchanged engine behavior).

### Calculate

1. Snapshot current sidebar **into the active scenario** (`initial_state` + `life_events`).
2. Run `build_simulation` for **every scenario with `compare == True`** (and always run **active** for the detailed table even if `compare` is false — engine always runs active).
3. Build chart: **balance panel (1,1)** overlays one curve per compared scenario; other panels use **active scenario only** (keeps chart readable).

### Live summary (main column, under title)

Short bullet or sentence block, updating as inputs change (callback `State` on all relevant controls + stores):

- Active scenario name  
- Starting balance, horizon years  
- Wage stop / retirement year  
- Count of life events  
- Number of scenarios included in comparison  

---

## Phases

| Phase | Scope | Status |
|-------|--------|--------|
| **P0** | This document + align wording (“life event”) | Done |
| **P1** | `scenarios-store`, toolbar, load/switch scenario, persist on Calculate, comparison overlay | Done |
| **P2** | Live summary strip | Done |
| **P3** | JSON v2 export/import + v1 migration | Done |
| **P4** | Optional presets (`presets/*.json` or embedded dicts) | Later |
| **P5** | First-run wizard (`dcc.Location` steps or multi-page) | Later |
| **P6** | JSON Schema file + optional `jsonschema` validation on upload | Later |
| **P7** | DataTable / grid editor for life events | Later |

---

## Testing checklist (manual)

- [ ] Two scenarios, different expenses → two balance lines on chart; table matches active scenario.
- [ ] Toggle **Include in comparison** → line appears/disappears after Calculate.
- [ ] Switch scenario → form + life events list update.
- [ ] Download → reopen app → import JSON v2 restores scenarios.
- [ ] Import old v1 file → one Baseline scenario, same numbers as before.

---

## Open questions

- **Maximum scenarios** for overlay (performance/clarity): soft cap e.g. 6 with UI note.
- **Table source when comparing:** keep showing **active** scenario year-by-year table; optional future “side-by-side CSV export.”

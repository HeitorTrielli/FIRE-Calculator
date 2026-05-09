# FIRE Calculator

A **Financial Independence, Retire Early (FIRE)** planner built with **Dash** and Plotly. Model multiple **named scenarios**, optional **life events** (income, expenses, returns, lump sums) at specific future years, and **compare** scenario balances on one chart. Results include million-dollar milestones and a year-by-year results table.

The web UI lives in the **`fire_web`** package; **`app.py`** is the entrypoint. Technical details: **[Application architecture](docs/application-architecture.md)**.

---

### Documentation for developers

- **[Application architecture](docs/application-architecture.md)** — Package layout (`fire_web`), scenario / life-event data model, `fire_config.json` formats, callbacks, simulation pipeline, persistence, tests, extension points.

---

## Features

### Core

- **Year-by-year projections** — Balance, income, expenses, returns, lump sums, inflation-adjusted metrics where applicable.
- **Named scenarios** — Each scenario has its own starting assumptions and life events.
- **Life events** — At year *N* from today, override wages, expenses, non-wage income, return rate, or add a lump sum; optional **name** for chart markers.
- **Retirement** — After **Retirement in Years**, wage income stops; **non-wage income** can continue.
- **Million-dollar milestones** — Timing and labels on the balance chart.
- **Starting balance** — Can be negative to approximate starting debt.

### Advanced

- **Compare on chart** — Overlay balance curves for any scenarios you enable (active scenario still drives the detailed subplots for income/expenses/cash flow).
- **Inflation** — Modeled on the expense path when no life-event row overrides that year.
- **Import / export** — Download all scenarios as JSON; upload to replace or merge via file picker.
- **Auto-save** — Scenarios persist to **`fire_config.json`** in the project folder when you save from the UI or perform actions that write config (see architecture doc).

### UI

- **Scenario modal** — Scenario **name** in the header; **starting assumptions** in a two-column grid; **life events** list with add/edit/remove (life events open a nested modal).
- **Live summary** — Active scenario snapshot and simulation horizon from the sidebar.
- **Detailed results** — Expand **Detailed Results** to see the full DataTable (no pagination).

---

## Requirements

- **Python 3.8+** (newer Python recommended for current Pandas/Dash stacks)
- Dependencies are pinned in **`requirements.txt`** (`dash`, `plotly`, `pandas`, `numpy`, `pytest` for tests).

---

## Installation

```bash
git clone <repository-url>
cd FIRE-Calculator
pip install -r requirements.txt
```

---

## Run the app

```bash
python app.py
```

Open **http://127.0.0.1:8050** (default Dash development server).

---

## How to use

### 1. Scenarios (sidebar)

- **＋ Add scenario** — Opens the configuration modal with empty defaults (or use **Edit** on a card).
- **Active** — Chooses which scenario powers the **detailed** charts (income vs expenses, returns, net cash flow) and the **live summary** text.
- **Compare on chart** — When checked, that scenario’s **balance** line is drawn on the top-left plot alongside other checked scenarios.
- **Edit** — Opens the scenario modal: title field = scenario name, then starting assumptions and life events.
- **Remove** — Deletes a scenario (at least one must remain).

### 2. Starting assumptions (scenario modal)

Set **initial balance**, wage and non-wage income, expenses, annual return and inflation **percentages**, and **retirement year** (year index when wage income stops). **Save scenario** stores changes and writes **`fire_config.json`** when possible.

### 3. Life events

Inside the scenario modal, **＋ Add life event** opens the life-event dialog:

- **Title field** = event name (optional; used on charts).
- **Year (from now)** and any **financial overrides** you need; leave blanks to keep the projected path from previous years.
- At least one financial change is required (the app will prompt if you only set a year/name).

Events are listed in **chronological order** by year.

### 4. Simulation (sidebar)

- **Years to Simulate** — Horizon for the projection (e.g. 20 years).
- **Calculate FIRE Trajectory** — Runs the engine for the **active** scenario and refreshes metrics, charts, milestones, and the detailed table.

### 5. Main area

- **Live summary** — Active scenario name, starting balance, horizon, retirement year, life-event count, compare counts.
- **Metric cards** — Final balance, first million milestone, highest milestone band.
- **Financial Trajectory** — Four-panel chart (balance with comparisons; income/expenses; returns vs expenses; net cash flow).
- **Million Dollar Milestones** — Cards when milestones exist.
- **Detailed Results** — Full year-by-year table inside an expandable section.

### 6. Configuration file

- **Download Configuration** — Exports all scenarios as JSON (version 2 format).
- **Upload Configuration** — Loads a file; legacy single-scenario files are migrated automatically.
- On startup, if **`fire_config.json`** exists next to **`app.py`**, it is loaded to restore scenarios.

---

## Understanding the charts

### Balance Over Time (comparison)

- Primary view of wealth vs time.
- **Gold dashed** vertical lines: million-dollar milestones.
- **Dot** lines: named life events (when calculated).
- Multiple **colored** lines when several scenarios have **Compare on chart** enabled.

### Income vs Expenses (active scenario)

- Green: income; red: expenses.

### Returns vs Expenses (active scenario)

- Orange: investment returns; red: expenses.

### Net Cash Flow (active scenario)

- Purple: income − expenses + lump sums (with fill).

---

## Example workflows

### Simple FIRE path

Create a scenario (e.g. **Baseline**), set roughly:

- Initial balance `$50,000`, yearly wage `$75,000`, expenses `$45,000`, return **7%**, inflation **2.5%**, retirement year **15**, then **Calculate**.

### Career + inheritance

Add life events on the scenario:

- Year **10**: higher income / expenses if desired.
- Year **12**: positive **lump sum** (inheritance).
- Year **15**: align with retirement (wage drops per assumptions).

### Major purchase

- Year **8**: lump sum **−500,000** (if your convention treats outflows as negative lump sums — enter per modal validation).
- Year **10**: expense override for higher housing costs.

*(Exact keys follow the JSON schema below; the modal writes the same structure.)*

---

## Configuration JSON

### Current format (version 2)

The app saves and downloads a **scenario list**:

```json
{
  "version": 2,
  "active_scenario_id": "abc123def456",
  "scenarios": [
    {
      "id": "abc123def456",
      "name": "Baseline",
      "compare": true,
      "initial_state": {
        "initial_balance": 50000,
        "yearly_income": 75000,
        "yearly_expenses": 45000,
        "annual_return_rate": 0.07,
        "inflation_rate": 0.025,
        "non_wage_income": 5000,
        "retirement_year": 15
      },
      "life_events": [
        {
          "year": 10,
          "yearly_income": 90000,
          "yearly_expenses": 50000,
          "name": "Promotion"
        },
        {
          "year": 12,
          "lump_sum": 100000,
          "name": "Inheritance"
        }
      ]
    }
  ]
}
```

Rates in **`initial_state`** are stored as **decimals** (`0.07` = 7%). Life-event rows may store display-friendly **return rates** in the UI layer; the engine normalizes percent vs decimal where needed.

### Legacy format (version 1)

Older files used top-level **`initial_state`** and **`future_states`** only. The app still **imports** these and wraps them into a single scenario named **Baseline**.

### Sharing configs

1. Use **Download Configuration** in the sidebar.
2. Share the JSON file.
3. Recipients use **Upload Configuration** to load it (ensure `fire_config.json` is writable if you rely on auto-save).

---

## Running the sample script

```bash
python example.py
```

Runs a **console-only** sample using the core calculator (no Dash UI).

---

## Tests

```bash
python -m pytest tests/test_app.py
```

Covers helpers, simulation wiring, and migration paths.

---

## Key concepts

### FIRE number

Often discussed as **25× annual expenses** (4% annual withdrawal). This app focuses on **projected balances and milestones** rather than enforcing a single FIRE number formula.

### Safe withdrawal rate

The underlying engine includes withdrawal-rate assumptions in **`fire_calculator.py`** for related logic; the Dash UI emphasizes trajectory and milestones.

### Sequence of returns

Year-by-year simulation illustrates how volatility ordering affects balances versus a smooth average return.

---

## Contributing

1. Fork the repository  
2. Create a feature branch  
3. Make changes (prefer tests for calculation or parsing changes)  
4. Submit a pull request  

---

## License

MIT License — see repository license file.

---

## Troubleshooting

1. **Nothing plots** — Choose **Active**, enter assumptions, **Save scenario**, then **Calculate FIRE Trajectory**.  
2. **Compare shows one line** — Enable **Compare on chart** on multiple scenarios.  
3. **Life event rejected** — Add at least one financial field besides year/name.  
4. **Config not sticking** — Check write permissions for **`fire_config.json`** in the project directory.  
5. **Upload errors** — Use valid JSON; v2 must include a non-empty **`scenarios`** array; v1 must include **`initial_state`**.  

---

## Tips

1. Use **conservative** returns (e.g. 6–8%) and realistic inflation.  
2. Model **several scenarios** (aggressive savings vs baseline vs higher spend).  
3. **Revisit** assumptions yearly and adjust life events.  
4. Use **Compare** to see balance paths without duplicating spreadsheets.  
5. Read **`docs/application-architecture.md`** before larger code changes.  

---

Built with **Dash** and Plotly • FIRE Calculator with named scenarios and life events  

import json
from pathlib import Path
from typing import Any, Dict, List

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from fire_calculator import FIRECalculator
from fire_state import FIREState, FIREStateManager

st.set_page_config(
    page_title="FIRE Calculator",
    page_icon="🔥",
    layout="wide",
)

# Initialize session state
if "state_manager" not in st.session_state:
    st.session_state.state_manager = FIREStateManager()
if "calculator" not in st.session_state:
    st.session_state.calculator = FIRECalculator(st.session_state.state_manager)
if "future_states" not in st.session_state:
    st.session_state.future_states = []
if "calculation_ready" not in st.session_state:
    st.session_state.calculation_ready = False
if "config_loaded" not in st.session_state:
    st.session_state.config_loaded = False

# Initialize default values for sidebar inputs
if "config_initial_balance" not in st.session_state:
    st.session_state.config_initial_balance = 0
if "config_yearly_income" not in st.session_state:
    st.session_state.config_yearly_income = 0
if "config_non_wage_income" not in st.session_state:
    st.session_state.config_non_wage_income = 0
if "config_yearly_expenses" not in st.session_state:
    st.session_state.config_yearly_expenses = 0
if "config_annual_return_rate" not in st.session_state:
    st.session_state.config_annual_return_rate = 0.0
if "config_inflation_rate" not in st.session_state:
    st.session_state.config_inflation_rate = 0.0
if "config_retirement_year" not in st.session_state:
    st.session_state.config_retirement_year = 1

# Default configuration filename
DEFAULT_CONFIG_FILE = "fire_config.json"

# Auto-load default configuration on first run
if not st.session_state.config_loaded:
    if Path(DEFAULT_CONFIG_FILE).exists():
        try:
            with open(DEFAULT_CONFIG_FILE, "r") as f:
                config_data = json.load(f)

            # Load initial state and update config values
            if config_data.get("initial_state"):
                initial_data = config_data["initial_state"]

                # Update config values that widgets read from
                st.session_state.config_initial_balance = initial_data.get(
                    "initial_balance", 0
                )
                st.session_state.config_yearly_income = initial_data.get(
                    "yearly_income", 0
                )
                st.session_state.config_non_wage_income = initial_data.get(
                    "non_wage_income", 0
                )
                st.session_state.config_yearly_expenses = initial_data.get(
                    "yearly_expenses", 0
                )
                st.session_state.config_annual_return_rate = (
                    initial_data.get("annual_return_rate", 0.0) * 100
                )
                st.session_state.config_inflation_rate = (
                    initial_data.get("inflation_rate", 0.0) * 100
                )
                st.session_state.config_retirement_year = initial_data.get(
                    "retirement_year", 1
                )

                initial_state = FIREState.create_initial_state(**initial_data)
                st.session_state.state_manager.add_initial_state(initial_state)

            # Load future states
            for future_state_data in config_data.get("future_states", []):
                st.session_state.future_states.append(future_state_data)
        except:
            pass  # If loading fails, just use defaults
    st.session_state.config_loaded = True


def save_configuration_to_json(filename: str) -> bool:
    """Save the complete configuration including initial state and future states to JSON."""
    try:
        config_data = {"initial_state": None, "future_states": []}

        # Get initial state from current widget values
        config_data["initial_state"] = {
            "initial_balance": initial_balance,
            "yearly_income": yearly_income,
            "yearly_expenses": yearly_expenses,
            "annual_return_rate": annual_return_rate,
            "inflation_rate": inflation_rate,
            "non_wage_income": non_wage_income,
            "retirement_year": retirement_year,
        }

        # Get only manually added future states from session state
        config_data["future_states"] = st.session_state.future_states.copy()

        with open(filename, "w") as f:
            json.dump(config_data, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving configuration: {str(e)}")
        return False


# Create or update initial state when calculate button is pressed
def update_initial_state_and_calculate():
    """Update initial state and future states, then run calculations."""
    # Reset state manager
    st.session_state.state_manager = FIREStateManager()
    st.session_state.calculator = FIRECalculator(st.session_state.state_manager)

    # Create new initial state
    initial_state = FIREState.create_initial_state(
        initial_balance=initial_balance,
        yearly_income=yearly_income,
        yearly_expenses=yearly_expenses,
        annual_return_rate=annual_return_rate,
        inflation_rate=inflation_rate,
        non_wage_income=non_wage_income,
        retirement_year=retirement_year,
    )
    st.session_state.state_manager.add_initial_state(initial_state)

    # Re-add all future states from session state
    for future_state in st.session_state.future_states:
        params = {
            k: v for k, v in future_state.items() if k != "year" and v is not None
        }
        if "annual_return_rate" in params:
            params["annual_return_rate"] /= 100  # Convert back to decimal
        if params:  # Only add if there are actual changes
            st.session_state.state_manager.add_future_state(
                year=future_state["year"], **params
            )

    st.session_state.calculation_ready = True


# Title and description
st.title("🔥 FIRE Calculator")
st.markdown(
    """
Calculate your path to Financial Independence and Retire Early (FIRE).
This advanced calculator supports yearly planning with future scenario changes and lump sum events.
"""
)

# Main input section
st.sidebar.header("Initial Financial State")

# Initial state inputs
with st.sidebar.expander("Initial State (Year 0)", expanded=True):
    initial_balance = st.number_input(
        "Initial Balance ($)",
        min_value=0,
        value=st.session_state.config_initial_balance,
        step=1000,
        help="Your current investment portfolio value",
    )

    yearly_income = st.number_input(
        "Yearly Wage Income ($)",
        min_value=0,
        value=st.session_state.config_yearly_income,
        step=1000,
        help="Your yearly wage/salary income (will become 0 after retirement)",
    )

    non_wage_income = st.number_input(
        "Non-Wage Income ($)",
        min_value=0,
        value=st.session_state.config_non_wage_income,
        step=1000,
        help="Yearly income that continues after retirement (rental, dividends, etc.)",
    )

    yearly_expenses = st.number_input(
        "Yearly Expenses ($)",
        min_value=0,
        value=st.session_state.config_yearly_expenses,
        step=1000,
        help="Your total yearly expenses",
    )

    annual_return_rate = (
        st.number_input(
            "Annual Return Rate (%)",
            min_value=0.0,
            max_value=20.0,
            value=st.session_state.config_annual_return_rate,
            step=0.1,
            help="Expected annual return rate on investments",
        )
        / 100
    )

    inflation_rate = (
        st.number_input(
            "Inflation Rate (%)",
            min_value=0.0,
            max_value=10.0,
            value=st.session_state.config_inflation_rate,
            step=0.1,
            help="Expected annual inflation rate",
        )
        / 100
    )

    retirement_year = st.number_input(
        "Retirement Year",
        min_value=1,
        max_value=50,
        value=st.session_state.config_retirement_year,
        step=1,
        help="Year when wage income stops",
    )

# Future states section
st.sidebar.header("Future State Changes")

with st.sidebar.expander("Add Future State Change", expanded=False):
    future_year = st.number_input(
        "Year",
        min_value=1,
        max_value=50,
        value=5,
        step=1,
        help="Year when changes take effect",
    )

    st.write("**Leave fields empty to inherit from previous state**")

    # Use None as default and only include if user actively changes
    future_yearly_income_input = st.number_input(
        "New Yearly Income ($)",
        min_value=0,
        value=None,
        step=1000,
        help="New yearly wage income (leave empty to keep current, set to 0 for no wage income)",
        format="%d",
    )

    future_yearly_expenses_input = st.number_input(
        "New Yearly Expenses ($)",
        min_value=0,
        value=None,
        step=1000,
        help="New yearly expenses (leave empty to keep current)",
        format="%d",
    )

    future_non_wage_income_input = st.number_input(
        "New Non-Wage Income ($)",
        min_value=0,
        value=None,
        step=1000,
        help="New non-wage income (leave empty to keep current)",
        format="%d",
    )

    future_return_rate_input = st.number_input(
        "New Return Rate (%)",
        min_value=0.0,
        max_value=20.0,
        value=None,
        step=0.1,
        help="New annual return rate (leave empty to keep current)",
        format="%.1f",
    )

    lump_sum_input = st.number_input(
        "Lump Sum ($)",
        min_value=None,
        value=None,
        step=1000,
        help="One-time lump sum (positive for income like inheritance, negative for major purchases like house/car)",
        format="%d",
    )

    if st.button("➕ Add Future State"):
        try:
            # Build parameters dict, only including values that user actually specified
            params = {"year": future_year}

            if future_yearly_income_input is not None:
                params["yearly_income"] = future_yearly_income_input
            if future_yearly_expenses_input is not None:
                params["yearly_expenses"] = future_yearly_expenses_input
            if future_non_wage_income_input is not None:
                params["non_wage_income"] = future_non_wage_income_input
            if future_return_rate_input is not None:
                params["annual_return_rate"] = future_return_rate_input / 100
            if lump_sum_input is not None and lump_sum_input != 0:
                params["lump_sum"] = lump_sum_input

            # Only add if there are actual parameter changes
            if len(params) > 1:  # More than just the year
                # Add to session state for display (convert percentage for display)
                display_params = params.copy()
                if "annual_return_rate" in display_params:
                    display_params[
                        "annual_return_rate"
                    ] *= 100  # Convert back to percentage for display

                # Check if year already exists and overwrite it
                existing_index = None
                for i, existing_state in enumerate(st.session_state.future_states):
                    if existing_state["year"] == future_year:
                        existing_index = i
                        break

                if existing_index is not None:
                    # Overwrite existing state
                    st.session_state.future_states[existing_index] = display_params
                    st.sidebar.success(f"Updated future state for year {future_year}!")
                else:
                    # Add new state
                    st.session_state.future_states.append(display_params)
                    st.sidebar.success(f"Added future state for year {future_year}!")

                st.session_state.calculation_ready = False
                st.rerun()  # Refresh to show the new state
            else:
                st.sidebar.warning("Please specify at least one parameter to change.")
        except Exception as e:
            st.sidebar.error(f"Error adding future state: {str(e)}")

# Display current future states
if st.session_state.future_states:
    st.sidebar.subheader("Current Future States")
    for i, state in enumerate(st.session_state.future_states):
        with st.sidebar.expander(f"Year {state['year']}", expanded=False):
            for key, value in state.items():
                if key != "year" and value is not None:
                    if key == "annual_return_rate":
                        st.write(f"**{key.replace('_', ' ').title()}**: {value:.1f}%")
                    else:
                        st.write(f"**{key.replace('_', ' ').title()}**: ${value:,.0f}")

            if st.button(f"🗑️ Remove", key=f"remove_{i}"):
                # Remove from session state
                st.session_state.future_states.pop(i)
                st.session_state.calculation_ready = False
                st.rerun()

    # Simulation parameters
st.sidebar.header("Simulation")
max_years = st.sidebar.number_input(
    "Years to Simulate", min_value=5, max_value=50, value=20, step=1
)

# Calculate button
st.sidebar.markdown("---")
if st.sidebar.button("🚀 **Calculate FIRE Trajectory**", type="primary"):
    update_initial_state_and_calculate()

# Configuration management at the end
st.sidebar.markdown("---")
st.sidebar.header("Configuration Management")

# File upload/download
uploaded_file = st.sidebar.file_uploader("Upload Configuration", type=["json"])
if uploaded_file is not None:
    # Show file info and update button
    st.sidebar.info(f"📁 File: {uploaded_file.name}")

    if st.sidebar.button("🔄 Update Config", type="primary"):
        try:
            # Read the uploaded file content
            file_content = uploaded_file.read()
            config_data = json.loads(file_content.decode("utf-8"))

            # Validate the JSON structure
            if not config_data.get("initial_state"):
                st.sidebar.error("Invalid configuration file: missing initial_state")
            else:
                # Save the uploaded config as the default config file
                with open(DEFAULT_CONFIG_FILE, "w") as f:
                    json.dump(config_data, f, indent=4)

                st.sidebar.success("Configuration updated successfully!")
                st.sidebar.info("🔄 Restarting app to apply new configuration...")

                # Force app restart by clearing all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]

                st.rerun()

        except json.JSONDecodeError:
            st.sidebar.error("Invalid JSON file format")
        except Exception as e:
            st.sidebar.error(f"Error updating configuration: {str(e)}")

# Download configuration
# Generate JSON data for download
config_data = {"initial_state": None, "future_states": []}

# Get initial state from sidebar values
config_data["initial_state"] = {
    "initial_balance": initial_balance,
    "yearly_income": yearly_income,
    "yearly_expenses": yearly_expenses,
    "annual_return_rate": annual_return_rate,
    "inflation_rate": inflation_rate,
    "non_wage_income": non_wage_income,
    "retirement_year": retirement_year,
}

# Get only manually added future states from session state
config_data["future_states"] = st.session_state.future_states.copy()

# Convert to JSON string
json_str = json.dumps(config_data, indent=4)

st.sidebar.download_button(
    label="📥 Download Configuration",
    data=json_str,
    file_name=DEFAULT_CONFIG_FILE,
    mime="application/json",
)

# Main content area
if st.session_state.calculation_ready and st.session_state.state_manager.states:
    # Calculate results
    results = st.session_state.calculator.calculate_until_year(max_years)
    milestones = st.session_state.calculator.calculate_million_dollar_milestones(
        results
    )

    # Display key metrics
    col1, col2, col3 = st.columns(3)

    final_balance = results[-1]["balance"] if results else 0

    with col1:
        st.metric(
            "Final Balance",
            f"${final_balance:,.0f}",
            help=f"Projected balance at year {max_years}",
        )

    with col2:
        first_milestone = milestones[0] if milestones else None
        if first_milestone:
            st.metric(
                "First Million",
                f"Year {first_milestone['year']}",
                help=f"Balance: ${first_milestone['balance']:,.0f}",
            )
        else:
            st.metric(
                "First Million",
                "Not reached",
                help="No million-dollar milestone reached",
            )

    with col3:
        total_milestones = len(milestones)
        if total_milestones > 0:
            last_milestone = milestones[-1]
            st.metric(
                "Total Milestones",
                f"{last_milestone['milestone']}M",
                help=f"Reached {total_milestones} milestone(s)",
            )
        else:
            st.metric("Total Milestones", "0", help="No milestones reached")

    # Create visualization
    st.subheader("Financial Trajectory")

    # Prepare data for plotting
    years = [r["year"] for r in results]
    balances = [r["balance"] for r in results]
    incomes = [r["yearly_income"] for r in results]
    expenses = [r["yearly_expenses"] for r in results]
    lump_sums = [r["lump_sum"] for r in results]

    # Create subplots
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Balance Over Time",
            "Income vs Expenses",
            "Returns vs Expenses",
            "Net Cash Flow",
        ),
        specs=[
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": False}],
        ],
    )

    # Balance chart
    fig.add_trace(
        go.Scatter(x=years, y=balances, name="Balance", line=dict(color="blue")),
        row=1,
        col=1,
    )

    # Income vs Expenses
    fig.add_trace(
        go.Scatter(x=years, y=incomes, name="Income", line=dict(color="green")),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(x=years, y=expenses, name="Expenses", line=dict(color="red")),
        row=1,
        col=2,
    )

    # Returns vs Expenses
    returns = [r["yearly_return"] for r in results]
    fig.add_trace(
        go.Scatter(x=years, y=returns, name="Returns", line=dict(color="orange")),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=years, y=expenses, name="Expenses", line=dict(color="red")),
        row=2,
        col=1,
    )

    # Net cash flow
    net_flows = [incomes[i] - expenses[i] + lump_sums[i] for i in range(len(years))]
    fig.add_trace(
        go.Scatter(
            x=years,
            y=net_flows,
            name="Net Cash Flow",
            line=dict(color="purple"),
            fill="tonexty",
        ),
        row=2,
        col=2,
    )

    # Add milestone markers
    for milestone in milestones:
        fig.add_vline(
            x=milestone["year"],
            line_dash="dash",
            line_color="gold",
            annotation_text=f"{milestone['milestone_text']}",
            row=1,
            col=1,
        )

    fig.update_layout(height=800, showlegend=True)
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="Amount ($)", tickformat=",")

    st.plotly_chart(fig, use_container_width=True)

    # Million dollar milestones
    if milestones:
        st.subheader("Million Dollar Milestones")
        milestone_cols = st.columns(min(len(milestones), 4))
        for i, milestone in enumerate(milestones):
            col_idx = i % 4
            with milestone_cols[col_idx]:
                if len(milestone["milestones_reached"]) == 1:
                    st.metric(
                        f"${milestone['milestone']}M",
                        f"Year {milestone['year']}",
                        help=f"Balance: ${milestone['balance']:,.0f}",
                    )
                else:
                    milestones_text = ", ".join(
                        [f"{m}M" for m in milestone["milestones_reached"]]
                    )
                    st.metric(
                        milestones_text,
                        f"Year {milestone['year']}",
                        help=f"Balance: ${milestone['balance']:,.0f}",
                    )

    # Data table
    with st.expander("📊 Detailed Results", expanded=False):
        import pandas as pd

        df = pd.DataFrame(results)

        # Set year as index and remove the year column
        df = df.set_index("year")

        # Format currency columns
        df["balance"] = df["balance"].apply(lambda x: f"${x:,.0f}")
        df["yearly_income"] = df["yearly_income"].apply(lambda x: f"${x:,.0f}")
        df["yearly_expenses"] = df["yearly_expenses"].apply(lambda x: f"${x:,.0f}")
        df["yearly_return"] = df["yearly_return"].apply(lambda x: f"${x:,.0f}")
        df["lump_sum"] = df["lump_sum"].apply(lambda x: f"${x:,.0f}" if x != 0 else "-")

        # Rename columns for better display
        df.columns = [col.replace("_", " ").title() for col in df.columns]

        st.dataframe(df, use_container_width=True)

elif st.session_state.state_manager.states:
    st.info(
        "👆 Click the **Calculate FIRE Trajectory** button in the sidebar to run the simulation."
    )
else:
    st.info(
        "👆 Please set up your initial financial state in the sidebar and click **Update Initial State** to begin."
    )

# Footer
st.markdown("---")
st.markdown(
    "Built with ❤️ using Streamlit • Enhanced FIRE Calculator with Future State Planning"
)

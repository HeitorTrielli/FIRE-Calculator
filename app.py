import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from fire_calculator import FIRECalculator, FIREConfig
from visualizations import FIREVisualizer

st.set_page_config(
    page_title="FIRE Calculator",
    page_icon="🔥",
    layout="wide",
)

# Title and description
st.title("🔥 FIRE Calculator")
st.markdown(
    """
Calculate your path to Financial Independence and Retire Early (FIRE).
This calculator helps you estimate when you can achieve financial independence based on your current financial situation and future plans.
"""
)

# Sidebar inputs
st.sidebar.header("Your Financial Inputs")

# Income and savings
with st.sidebar.expander("Income & Expenses", expanded=True):
    yearly_wage = st.number_input(
        "Net Salary Income ($)",
        min_value=0,
        value=80000,
        step=1000,
        help="Your total yearly salary after taxes and deductions (this will become 0 after retirement)",
    )

    non_wage_income = st.number_input(
        "Additional Net Income ($)",
        min_value=0,
        value=0,
        step=1000,
        help="Additional yearly income that continues after retirement (e.g., rental income, side gigs, pension) - after taxes",
    )

    monthly_expenses = st.number_input(
        "Monthly Expenses ($)",
        min_value=0,
        value=4000,
        step=100,
        help="Your average monthly expenses",
    )

    initial_capital = st.number_input(
        "Initial Capital ($)",
        min_value=0,
        value=50000,
        step=1000,
        help="Your current investment portfolio value",
    )

# Investment parameters
with st.sidebar.expander("Investment Parameters", expanded=True):
    expected_return_rate = (
        st.number_input(
            "Expected Return Rate (%)",
            min_value=1.0,
            max_value=15.0,
            value=7.0,
            step=0.1,
            help="Expected annual return rate on your investments after inflation",
        )
        / 100
    )

    safe_withdrawal_rate = (
        st.number_input(
            "Safe Withdrawal Rate (%)",
            min_value=2.0,
            max_value=10.0,
            value=3.5,
            step=0.1,
            help="The percentage of your portfolio you plan to withdraw annually in retirement",
        )
        / 100
    )

    wage_growth_rate = (
        st.number_input(
            "Wage Growth Rate (%)",
            min_value=0.0,
            max_value=10.0,
            value=2.0,
            step=0.1,
            help="Expected annual growth rate of your income",
        )
        / 100
    )

# Simulation parameters
with st.sidebar.expander("Simulation Parameters", expanded=True):
    num_years = st.number_input(
        "Years to Simulate",
        min_value=5,
        max_value=50,
        value=30,
        step=1,
        help="Number of years to simulate",
    )

    retirement_year = st.number_input(
        "Planned Retirement Year",
        min_value=1,
        max_value=num_years,
        value=15,
        step=1,
        help="Year you plan to retire",
    )

# Create FIRE configuration
config = FIREConfig(
    yearly_wage=yearly_wage,
    monthly_expenses=monthly_expenses,
    initial_capital=initial_capital,
    expected_return_rate=expected_return_rate,
    retirement_safe_withdrawal_rate=safe_withdrawal_rate,
    wage_growth_rate=wage_growth_rate,
    non_wage_income=non_wage_income,
)

# Create calculator and visualizer
calculator = FIRECalculator(config)
visualizer = FIREVisualizer(calculator)

# Calculate FIRE trajectory
wealth_df, income_df, breakeven_year = calculator.calculate_fire_trajectory(
    num_years=num_years, retirement_year=retirement_year
)

# Display key metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Years to FIRE",
        f"{breakeven_year} years" if breakeven_year > 0 else "Not achieved",
        help="Number of years until financial independence",
    )

with col2:
    final_wealth = wealth_df["total"].iloc[-1]
    st.metric(
        "Final Wealth",
        f"${final_wealth:,.0f}",
        help="Projected wealth at the end of simulation",
    )

with col3:
    final_income = income_df["total"].iloc[-1]
    st.metric(
        "Final Passive Income",
        f"${final_income:,.0f}/year",
        help="Projected passive income at the end of simulation",
    )

# Display charts
st.subheader("FIRE Trajectory")

# Create subplots
fig = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=("Wealth Trajectory", "Passive Income vs Expenses"),
    horizontal_spacing=0.1,
)

# Plot wealth trajectory
fig.add_trace(
    go.Scatter(
        x=wealth_df.year,
        y=wealth_df.total,
        name="Total Wealth",
        line=dict(color="rgb(31, 119, 180)"),
    ),
    row=1,
    col=1,
)

if breakeven_year > 0:
    fig.add_vline(
        x=breakeven_year,
        line_dash="dash",
        line_color="green",
        annotation_text=f"FIRE achieved (Year {breakeven_year})",
        annotation_position="top right",
        row=1,
        col=1,
    )

# Plot passive income
fig.add_trace(
    go.Scatter(
        x=income_df.year,
        y=income_df.total,
        name="Passive Income",
        line=dict(color="rgb(31, 119, 180)"),
    ),
    row=1,
    col=2,
)

fig.add_hline(
    y=calculator.config.yearly_expenses,
    line_dash="dash",
    line_color="red",
    annotation_text="Yearly Expenses",
    annotation_position="top right",
    row=1,
    col=2,
)

if breakeven_year > 0:
    fig.add_vline(
        x=breakeven_year,
        line_dash="dash",
        line_color="green",
        annotation_text=f"FIRE achieved (Year {breakeven_year})",
        annotation_position="top right",
        row=1,
        col=2,
    )

# Update layout
fig.update_layout(
    height=500,
    showlegend=True,
    yaxis=dict(
        title="Total Wealth ($)",
        tickformat=",",
    ),
    yaxis2=dict(
        title="Amount ($)",
        tickformat=",",
    ),
    xaxis=dict(title="Year"),
    xaxis2=dict(title="Year"),
    hovermode="x unified",
)

st.plotly_chart(fig, use_container_width=True)

# Display million-dollar milestones
st.subheader("Million Dollar Milestones")

# Calculate milestones
last_million = wealth_df["total"].iloc[0] // 1_000_000
milestones = []

for index, row in wealth_df.iterrows():
    current_millions = row["total"] // 1_000_000
    if current_millions > last_million:
        milestones.append(
            {
                "year": row["year"],
                "millions": int(current_millions),
                "total": row["total"],
            }
        )
        last_million = current_millions

if milestones:
    milestone_cols = st.columns(3)
    for i, milestone in enumerate(milestones):
        col_index = i % 3
        with milestone_cols[col_index]:
            st.metric(
                f"${milestone['millions']}M Milestone",
                f"Year {milestone['year']}",
                help=f"Total wealth: ${milestone['total']:,.0f}",
            )
else:
    st.info("No million-dollar milestones reached in the simulation period.")

# Add explanatory notes
st.markdown(
    """
### 📝 Notes
- All monetary values are net (after-tax) amounts
- The simulation assumes constant inflation-adjusted returns (real returns)
- The 4% rule is a common safe withdrawal rate based on historical data
- All values are in today's dollars (adjusted for inflation)
"""
)

# Footer
st.markdown("---")
st.markdown(
    "Built with ❤️ using Streamlit • [View Source Code](https://github.com/yourusername/FIRE-Calculator)"
)

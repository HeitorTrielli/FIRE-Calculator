from typing import List, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fire_calculator import FIRECalculator


class FIREVisualizer:
    """Visualization tools for FIRE calculations."""

    def __init__(self, calculator: FIRECalculator):
        self.calculator = calculator

    def plot_fire_trajectory(
        self,
        wealth_df: pd.DataFrame,
        income_df: pd.DataFrame,
        breakeven_year: int,
        title: str = "FIRE Trajectory",
    ) -> go.Figure:
        """
        Plot wealth and passive income trajectories.

        Args:
            wealth_df: DataFrame with total wealth per year
            income_df: DataFrame with passive income per year
            breakeven_year: Year when FIRE is achieved
            title: Plot title

        Returns:
            Plotly figure object
        """
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
            y=self.calculator.config.yearly_expenses,
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

        return fig

    def plot_monte_carlo_simulation(
        self,
        num_simulations: int,
        num_years: int,
        retirement_year: int,
        initial_return: float = 1.06,
        phi: float = 0.98,
        sigma: float = 0.005,
    ) -> Tuple[go.Figure, dict]:
        """
        Plot multiple Monte Carlo simulations of FIRE trajectories.

        Args:
            num_simulations: Number of simulations to run
            num_years: Number of years to simulate
            retirement_year: Year to retire
            initial_return: Initial return rate
            phi: AR(1) coefficient
            sigma: Standard deviation of noise

        Returns:
            Tuple containing:
            - Plotly figure object
            - Dictionary with simulation statistics
        """
        fig = go.Figure()

        successful_sims = 0
        earliest_fire = float("inf")
        latest_fire = 0
        final_year_values = []

        for i in range(num_simulations):
            # Generate random returns for this simulation
            returns = self.calculator.generate_monte_carlo_returns(
                num_years, initial_return=initial_return, phi=phi, sigma=sigma
            )

            # Calculate trajectory with these returns
            _, income_df, breakeven_year = self.calculator.calculate_fire_trajectory(
                num_years=num_years,
                retirement_year=retirement_year,
                custom_returns=returns,
            )

            # Plot this simulation
            fig.add_trace(
                go.Scatter(
                    x=income_df.year,
                    y=income_df.total,
                    mode="lines",
                    line=dict(color="rgba(31, 119, 180, 0.1)"),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

            # Update statistics
            if breakeven_year > 0:
                successful_sims += 1
                earliest_fire = min(earliest_fire, breakeven_year)
                latest_fire = max(latest_fire, breakeven_year)

            final_year_values.append(income_df["total"].iloc[-1])

        # Add expenses line
        fig.add_hline(
            y=self.calculator.config.yearly_expenses,
            line_dash="dash",
            line_color="red",
            annotation_text="Yearly Expenses",
            annotation_position="top right",
        )

        # Calculate statistics
        success_rate = (successful_sims / num_simulations) * 100
        stats = {
            "success_rate": success_rate,
            "earliest_fire": earliest_fire if earliest_fire != float("inf") else None,
            "latest_fire": latest_fire if latest_fire > 0 else None,
            "median_final": np.median(final_year_values),
            "p25_final": np.percentile(final_year_values, 25),
            "p75_final": np.percentile(final_year_values, 75),
        }

        # Update layout
        fig.update_layout(
            title=dict(
                text=(
                    f"Monte Carlo Simulation<br>"
                    f"Success Rate: {stats['success_rate']:.1f}%<br>"
                    f"FIRE Achievement Range: Years {stats['earliest_fire']}-{stats['latest_fire']}<br>"
                    f"Final Year Income Range: ${stats['p25_final']:,.0f} - ${stats['p75_final']:,.0f} "
                    f"(Median: ${stats['median_final']:,.0f})"
                ),
                x=0.5,
                xanchor="center",
            ),
            xaxis_title="Year",
            yaxis_title="Passive Income ($)",
            yaxis=dict(tickformat=","),
            showlegend=False,
            hovermode="x unified",
            height=500,
        )

        return fig, stats


def main():
    """Example usage of visualization tools."""
    import streamlit as st

    from fire_calculator import FIRECalculator, FIREConfig

    # Create a sample configuration
    config = FIREConfig(
        yearly_wage=80000,
        monthly_expenses=4000,
        initial_capital=50000,
        expected_return_rate=0.07,
        retirement_safe_withdrawal_rate=0.035,
        wage_growth_rate=0.02,
        non_wage_income=0.0,
    )

    calculator = FIRECalculator(config)
    visualizer = FIREVisualizer(calculator)

    # Calculate and plot a single trajectory
    wealth_df, income_df, breakeven_year = calculator.calculate_fire_trajectory(
        num_years=30, retirement_year=15
    )
    fig = visualizer.plot_fire_trajectory(wealth_df, income_df, breakeven_year)
    st.plotly_chart(fig)

    # Run and plot Monte Carlo simulation
    fig, stats = visualizer.plot_monte_carlo_simulation(
        num_simulations=100, num_years=30, retirement_year=15
    )
    st.plotly_chart(fig)
    st.write("Simulation Statistics:", stats)


if __name__ == "__main__":
    main()

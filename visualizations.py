from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MultipleLocator

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
    ) -> None:
        """
        Plot wealth and passive income trajectories.

        Args:
            wealth_df: DataFrame with total wealth per year
            income_df: DataFrame with passive income per year
            breakeven_year: Year when FIRE is achieved
            title: Plot title
        """
        plt.figure(figsize=(12, 6))

        # Plot wealth trajectory
        plt.subplot(1, 2, 1)
        plt.plot(wealth_df.year, wealth_df.total, label="Total Wealth")
        if breakeven_year > 0:
            plt.axvline(
                x=breakeven_year,
                color="g",
                linestyle="--",
                label=f"FIRE achieved (Year {breakeven_year})",
            )
        plt.title("Wealth Trajectory")
        plt.xlabel("Year")
        plt.ylabel("Total Wealth ($)")
        plt.grid(True)
        plt.legend()

        # Plot passive income
        plt.subplot(1, 2, 2)
        plt.plot(income_df.year, income_df.total, label="Passive Income")
        plt.axhline(
            y=self.calculator.config.yearly_expenses,
            color="r",
            linestyle="--",
            label="Yearly Expenses",
        )
        if breakeven_year > 0:
            plt.axvline(
                x=breakeven_year,
                color="g",
                linestyle="--",
                label=f"FIRE achieved (Year {breakeven_year})",
            )
        plt.title("Passive Income vs Expenses")
        plt.xlabel("Year")
        plt.ylabel("Amount ($)")
        plt.grid(True)
        plt.legend()

        plt.tight_layout()
        plt.show()

    def plot_monte_carlo_simulation(
        self,
        num_simulations: int,
        num_years: int,
        retirement_year: int,
        alpha: float = 0.1,
    ) -> None:
        """
        Plot multiple Monte Carlo simulations of FIRE trajectories.

        Args:
            num_simulations: Number of simulations to run
            num_years: Number of years to simulate
            retirement_year: Year to retire
            alpha: Transparency of simulation lines
        """
        plt.figure(figsize=(12, 6))

        successful_sims = 0
        earliest_fire = float("inf")
        latest_fire = 0

        for i in range(num_simulations):
            # Generate random returns for this simulation
            returns = self.calculator.generate_monte_carlo_returns(num_years)

            # Calculate trajectory with these returns
            _, income_df, breakeven_year = self.calculator.calculate_fire_trajectory(
                num_years=num_years,
                retirement_year=retirement_year,
                custom_returns=returns,
            )

            # Plot this simulation
            plt.plot(income_df.year, income_df.total, alpha=alpha, color="blue")

            # Update statistics
            if breakeven_year > 0:
                successful_sims += 1
                earliest_fire = min(earliest_fire, breakeven_year)
                latest_fire = max(latest_fire, breakeven_year)

        # Plot expenses line
        plt.axhline(
            y=self.calculator.config.yearly_expenses,
            color="r",
            linestyle="--",
            label="Yearly Expenses",
        )

        # Add labels and title
        success_rate = (successful_sims / num_simulations) * 100
        plt.title(
            f"Monte Carlo Simulation\n"
            f"Success Rate: {success_rate:.1f}%\n"
            f"FIRE Achievement Range: Years {earliest_fire}-{latest_fire}"
        )
        plt.xlabel("Year")
        plt.ylabel("Passive Income ($)")
        plt.grid(True)
        plt.legend()

        plt.tight_layout()
        plt.show()


def main():
    """Example usage of visualization tools."""
    from fire_calculator import FIRECalculator, FIREConfig

    # Create a sample configuration
    config = FIREConfig(
        yearly_wage=126000,
        monthly_expenses=5500,
        initial_capital=208000,
        expected_return_rate=0.09,
    )

    calculator = FIRECalculator(config)
    visualizer = FIREVisualizer(calculator)

    # Calculate and plot a single trajectory
    wealth_df, income_df, breakeven_year = calculator.calculate_fire_trajectory(
        num_years=35, retirement_year=10
    )
    visualizer.plot_fire_trajectory(wealth_df, income_df, breakeven_year)

    # Run and plot Monte Carlo simulation
    visualizer.plot_monte_carlo_simulation(
        num_simulations=100, num_years=35, retirement_year=10
    )


if __name__ == "__main__":
    main()

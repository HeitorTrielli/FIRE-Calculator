import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class FIREConfig:
    """Configuration class for FIRE calculator parameters."""

    yearly_wage: float
    monthly_expenses: float
    initial_capital: float
    expected_return_rate: float
    retirement_safe_withdrawal_rate: float = 0.04  # 4% rule
    wage_growth_rate: float = 0.0
    non_wage_income: float = 0.0

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.expected_return_rate <= 0:
            raise ValueError("Expected return rate must be positive")
        if self.retirement_safe_withdrawal_rate <= 0:
            raise ValueError("Safe withdrawal rate must be positive")
        if self.yearly_wage < 0:
            raise ValueError("Yearly wage cannot be negative")
        if self.monthly_expenses < 0:
            raise ValueError("Monthly expenses cannot be negative")

    @property
    def yearly_expenses(self) -> float:
        """Calculate yearly expenses after cost coverage."""
        return self.monthly_expenses * 12

    @classmethod
    def from_json(cls, json_path: str) -> "FIREConfig":
        """Create a FIREConfig instance from a JSON file."""
        with open(json_path, "r") as f:
            config_data = json.load(f)
        return cls(**config_data)


class FIRECalculator:
    """Financial Independence Retire Early (FIRE) calculator."""

    def __init__(self, config: FIREConfig):
        self.config = config

    def calculate_fire_trajectory(
        self,
        num_years: int,
        retirement_year: int,
        custom_returns: Optional[List[float]] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, int]:
        """
        Calculate the wealth trajectory and passive income over time.

        Args:
            num_years: Number of years to simulate
            retirement_year: Year to retire (1-based)
            custom_returns: Optional list of custom yearly returns

        Returns:
            Tuple containing:
            - DataFrame with total wealth per year
            - DataFrame with passive income per year
            - Year when FIRE is achieved (breakeven year)
        """
        if retirement_year > num_years:
            raise ValueError("Retirement year cannot be greater than simulation years")

        total = self.config.initial_capital
        yearly_income = self.config.yearly_wage + self.config.non_wage_income
        yearly_wage = self.config.yearly_wage

        wealth_data = []
        income_data = []
        breakeven_year = -1
        fire_achieved = False
        last_million_milestone = total // 1_000_000

        for year in range(num_years):
            # Calculate return rate for the year
            return_rate = (
                custom_returns[year]
                if custom_returns
                else self.config.expected_return_rate
            )

            # Apply wage growth before retirement
            if year < retirement_year - 1:
                wage_growth = yearly_wage * self.config.wage_growth_rate
                yearly_wage += wage_growth
                yearly_income += wage_growth
            else:
                yearly_income = self.config.non_wage_income
                yearly_wage = 0

            # Calculate total wealth and passive income
            total += total * return_rate + yearly_income - self.config.yearly_expenses
            passive_income = total * self.config.retirement_safe_withdrawal_rate

            # Check for million dollar milestones
            current_millions = total // 1_000_000
            if current_millions > last_million_milestone:
                last_million_milestone = current_millions

            wealth_data.append((year + 1, total))
            income_data.append((year + 1, passive_income))

            # Check if FIRE is achieved
            if (
                not fire_achieved
                and passive_income + self.config.non_wage_income
                >= self.config.yearly_expenses
            ):
                fire_achieved = True
                breakeven_year = year + 1

        wealth_df = pd.DataFrame(wealth_data, columns=["year", "total"])
        income_df = pd.DataFrame(income_data, columns=["year", "total"])

        return wealth_df, income_df, breakeven_year

    def generate_monte_carlo_returns(
        self,
        num_years: int,
        initial_return: float = 1.06,
        phi: float = 0.98,
        sigma: float = 0.005,
    ) -> List[float]:
        """
        Generate simulated market returns using an AR(1) process.

        Args:
            num_years: Number of years to simulate
            initial_return: Initial return rate
            phi: AR(1) coefficient
            sigma: Standard deviation of noise

        Returns:
            List of simulated yearly returns
        """
        # Center the process around the expected return rate
        target_return = (
            self.config.expected_return_rate + 1
        )  # Convert to multiplier format
        initial_deviation = initial_return - target_return

        # Start with deviation from target
        deviations = [initial_deviation]

        # Generate deviations using AR(1)
        for _ in range(1, num_years):
            noise = np.random.normal(0, sigma)
            new_deviation = phi * deviations[-1] + noise
            deviations.append(new_deviation)

        # Convert deviations back to actual returns centered around target return
        returns = [deviation + target_return for deviation in deviations]

        # Ensure returns don't go below a minimum threshold (e.g., -20% real return)
        min_return = 0.8  # -20% real return
        returns = [max(r, min_return) for r in returns]

        return returns

    def save_results(
        self,
        wealth_df: pd.DataFrame,
        income_df: pd.DataFrame,
        output_dir: str = "results",
    ) -> None:
        """Save calculation results to CSV files."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        wealth_df.to_csv(f"{output_dir}/wealth_trajectory.csv", index=False)
        income_df.to_csv(f"{output_dir}/passive_income.csv", index=False)


def main():
    # Example usage
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

    # Calculate FIRE trajectory
    wealth_df, income_df, breakeven_year = calculator.calculate_fire_trajectory(
        num_years=30, retirement_year=15
    )

    # Save results
    calculator.save_results(wealth_df, income_df)

    print(f"FIRE achieved in year: {breakeven_year}")
    print(f"Final wealth: ${wealth_df['total'].iloc[-1]:,.2f}")
    print(f"Final passive income: ${income_df['total'].iloc[-1]:,.2f}")


if __name__ == "__main__":
    main()

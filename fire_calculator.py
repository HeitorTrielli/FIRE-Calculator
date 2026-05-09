import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from fire_debug import log_event
from fire_state import FIREState, FIREStateManager


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
    """Calculates FIRE-related financial projections."""

    def __init__(self, state_manager: FIREStateManager):
        self.state_manager = state_manager

    def calculate_next_year(self, current_state: FIREState) -> Dict[str, Any]:
        """Calculate the next year's results based on the current state."""
        next_year = current_state.year + 1
        next_state = self.state_manager.get_state_at_year(next_year)

        # When a life-event / future row exists for next_year, cash flows for that
        # year must come from that row (expenses were wrongly taken from current_year).
        if next_state is not None:
            ret_rate = next_state.annual_return_rate
            expenses_for_year = next_state.yearly_expenses
            if (
                current_state.retirement_year is not None
                and next_year >= current_state.retirement_year
            ):
                total_income = next_state.non_wage_income
            else:
                total_income = next_state.yearly_income + next_state.non_wage_income
        else:
            ret_rate = current_state.annual_return_rate
            expenses_for_year = current_state.yearly_expenses * (
                1 + current_state.inflation_rate
            )
            if (
                current_state.retirement_year is not None
                and next_year >= current_state.retirement_year
            ):
                total_income = current_state.non_wage_income
            else:
                total_income = current_state.yearly_income + current_state.non_wage_income

        if next_state is not None:
            log_event(
                "calculate_next_year:life_event_row",
                current_year=current_state.year,
                expenses_applied=expenses_for_year,
                next_year=next_year,
                row_yearly_expenses=next_state.yearly_expenses,
                total_income=total_income,
            )

        yearly_return = current_state.balance * ret_rate
        lump_sum = next_state.lump_sum if next_state else 0.0

        new_balance = (
            current_state.balance
            + yearly_return
            + total_income
            - expenses_for_year
            + lump_sum
        )

        inflation_factor = (1 + current_state.inflation_rate) ** current_state.year
        adjusted_balance = new_balance / inflation_factor
        adjusted_income = total_income / inflation_factor
        adjusted_expenses = expenses_for_year / inflation_factor
        adjusted_lump_sum = lump_sum / inflation_factor

        return {
            "year": next_year,
            "balance": new_balance,
            "yearly_return": yearly_return,
            "yearly_income": total_income,
            "yearly_expenses": expenses_for_year,
            "lump_sum": lump_sum,
            "adjusted_balance": adjusted_balance,
            "adjusted_income": adjusted_income,
            "adjusted_expenses": adjusted_expenses,
            "adjusted_lump_sum": adjusted_lump_sum,
        }

    def calculate_until_year(self, target_year: int) -> List[Dict[str, Any]]:
        """Calculate results until the target year."""
        if not self.state_manager.states:
            raise ValueError("No initial state exists")

        results = []

        # Start from year 0 (initial state)
        current_year = 0

        while current_year < target_year:
            # Get the current state
            current_state = self.state_manager.get_state_at_year(current_year)
            if not current_state:
                raise ValueError(f"No state exists for year {current_year}")

            # Calculate next year's results
            next_year_results = self.calculate_next_year(current_state)
            results.append(next_year_results)

            # Move to next year
            next_year = current_year + 1

            # Create or update state for next year
            current_state = self.state_manager.create_next_year_state(
                current_state, next_year_results["balance"]
            )

            current_year = next_year

        return results

    def calculate_million_dollar_milestones(
        self, results: List[Dict[str, Any]] = None, max_years: int = 100
    ) -> List[Dict[str, Any]]:
        """Calculate when each million-dollar milestone is reached."""
        if results is None:
            results = self.calculate_until_year(max_years)

        milestones = []
        current_milestone = 1  # Start with $1M

        for result in results:
            balance = result["balance"]
            year = result["year"]

            # Track milestones reached this year
            milestones_this_year = []

            # Check if we've crossed one or more milestones this year
            while balance >= current_milestone * 1_000_000:
                milestones_this_year.append(current_milestone)
                current_milestone += 1

            # If any milestones were reached this year, add a single entry
            if milestones_this_year:
                if len(milestones_this_year) == 1:
                    milestone_text = f"{milestones_this_year[0]}M"
                else:
                    milestone_text = (
                        f"{milestones_this_year[0]}M-{milestones_this_year[-1]}M"
                    )

                milestones.append(
                    {
                        "year": year,
                        "balance": balance,
                        "milestone": milestones_this_year[
                            -1
                        ],  # Highest milestone reached
                        "milestone_text": milestone_text,
                        "milestones_reached": milestones_this_year,
                    }
                )

        return milestones

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

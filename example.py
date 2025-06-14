from fire_calculator import FIRECalculator
from fire_state import FIREState, FIREStateManager


def print_results(results):
    """Print results in a formatted table."""
    print("\nYear | Balance | Income | Expenses | Return | Lump Sum")
    print("-" * 65)
    for result in results:
        print(
            f"{result['year']:4d} | "
            f"${result['balance']:,.2f} | "
            f"${result['yearly_income']:,.2f} | "
            f"${result['yearly_expenses']:,.2f} | "
            f"${result['yearly_return']:,.2f} | "
            f"${result['lump_sum']:,.2f}"
        )


def main():
    # Create state manager and calculator
    state_manager = FIREStateManager()
    calculator = FIRECalculator(state_manager)

    # Set up initial state
    initial_state = FIREState.create_initial_state(
        initial_balance=50000,  # $50k initial balance
        yearly_income=75000,  # $75k yearly income
        yearly_expenses=45000,  # $45k yearly expenses
        annual_return_rate=0.07,  # 7% annual return
        inflation_rate=0.025,  # 2.5% inflation
        non_wage_income=5000,  # $5k yearly non-wage income
    )
    state_manager.add_initial_state(initial_state)

    # Add retirement at year 15
    state_manager.add_future_state(year=15, yearly_income=0)

    # Add career progression at year 10
    state_manager.add_future_state(year=10, yearly_income=90000, yearly_expenses=50000)

    # Add inheritance at year 12
    state_manager.add_future_state(year=12, lump_sum=100000)  # $100k inheritance

    # Calculate all years at once
    results = calculator.calculate_until_year(20)
    print_results(results)

    # Calculate and print million dollar milestones using the already calculated results
    milestones = calculator.calculate_million_dollar_milestones(results)
    if milestones:
        print("\nMillion Dollar Milestones:")
        for milestone in milestones:
            if len(milestone["milestones_reached"]) == 1:
                print(
                    f"Year {milestone['year']}: "
                    f"${milestone['balance']:,.2f} "
                    f"({milestone['milestone_text']} milestone)"
                )
            else:
                milestones_list = ", ".join(
                    [f"{m}M" for m in milestone["milestones_reached"]]
                )
                print(
                    f"Year {milestone['year']}: "
                    f"${milestone['balance']:,.2f} "
                    f"({milestones_list} milestones)"
                )
    else:
        print("\nNo million dollar milestones reached in the simulation period.")


if __name__ == "__main__":
    main()

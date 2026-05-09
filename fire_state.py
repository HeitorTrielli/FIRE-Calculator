from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FIREState:
    """Represents the state of a FIRE calculation at a specific point in time."""

    year: int
    balance: float
    yearly_income: float
    yearly_expenses: float
    annual_return_rate: float
    inflation_rate: float
    non_wage_income: float
    retirement_year: Optional[int] = None
    lump_sum: float = 0.0  # One-time lump sum for this year

    @classmethod
    def create_initial_state(
        cls,
        initial_balance: float,
        yearly_income: float,
        yearly_expenses: float,
        annual_return_rate: float,
        inflation_rate: float,
        non_wage_income: float,
        retirement_year: Optional[int] = None,
        lump_sum: float = 0.0,
    ) -> "FIREState":
        """Create the initial state for year 0."""
        return cls(
            year=0,
            balance=initial_balance,
            yearly_income=yearly_income,
            yearly_expenses=yearly_expenses,
            annual_return_rate=annual_return_rate,
            inflation_rate=inflation_rate,
            non_wage_income=non_wage_income,
            retirement_year=retirement_year,
            lump_sum=lump_sum,
        )

    def copy(self) -> "FIREState":
        """Create a copy of the current state."""
        return FIREState(
            year=self.year,
            balance=self.balance,
            yearly_income=self.yearly_income,
            yearly_expenses=self.yearly_expenses,
            annual_return_rate=self.annual_return_rate,
            inflation_rate=self.inflation_rate,
            non_wage_income=self.non_wage_income,
            retirement_year=self.retirement_year,
            lump_sum=self.lump_sum,
        )

    @property
    def total_income(self) -> float:
        """Calculate total income considering retirement year."""
        if self.retirement_year is not None and self.year >= self.retirement_year:
            return self.non_wage_income
        return self.yearly_income + self.non_wage_income


class FIREStateManager:
    """Manages the sequence of states in a FIRE calculation."""

    def __init__(self):
        self.states: List[FIREState] = []
        self._current_year = 0

    def add_initial_state(self, state: FIREState) -> None:
        """Add the initial state (year 0)."""
        if self.states:
            raise ValueError("Initial state already exists")
        self.states.append(state)

    def add_future_state(
        self,
        year: int,
        yearly_income: Optional[float] = None,
        yearly_expenses: Optional[float] = None,
        annual_return_rate: Optional[float] = None,
        inflation_rate: Optional[float] = None,
        non_wage_income: Optional[float] = None,
        lump_sum: Optional[float] = None,
    ) -> FIREState:
        """Add a state for a future year with new parameters."""
        if not self.states:
            raise ValueError("No initial state exists")

        if year <= 0:
            raise ValueError(f"Year must be greater than 0")

        # Get the state with the highest year that is less than the target year
        # This handles non-linear state additions properly
        reference_state = None
        for state in sorted(self.states, key=lambda x: x.year, reverse=True):
            if state.year < year:
                reference_state = state
                break

        if reference_state is None:
            # If no state exists before this year, use the initial state (year 0)
            reference_state = self.get_state_at_year(0)
            if reference_state is None:
                raise ValueError("No initial state exists")

        # Create new state with new parameters, inheriting from reference state if not specified
        # Note: balance will be set to 0.0 initially and updated by the calculator

        # Calculate inflation-adjusted expenses if inheriting from reference state
        if yearly_expenses is not None:
            # User provided new expenses - use as-is (these are in today's dollars)
            adjusted_expenses = yearly_expenses
        else:
            # Inherit expenses from reference state and adjust for inflation
            years_difference = year - reference_state.year
            inflation_factor = (1 + reference_state.inflation_rate) ** years_difference
            adjusted_expenses = reference_state.yearly_expenses * inflation_factor

        new_state = FIREState(
            year=year,
            balance=0.0,  # Placeholder - will be updated by calculator
            yearly_income=(
                yearly_income
                if yearly_income is not None
                else reference_state.yearly_income
            ),
            yearly_expenses=adjusted_expenses,
            annual_return_rate=(
                annual_return_rate
                if annual_return_rate is not None
                else reference_state.annual_return_rate
            ),
            inflation_rate=(
                inflation_rate
                if inflation_rate is not None
                else reference_state.inflation_rate
            ),
            non_wage_income=(
                non_wage_income
                if non_wage_income is not None
                else reference_state.non_wage_income
            ),
            retirement_year=reference_state.retirement_year,  # Retirement year is inherited from initial state
            lump_sum=(
                lump_sum if lump_sum is not None else 0.0
            ),  # Lump sums don't inherit
        )

        self.states.append(new_state)
        return new_state

    def get_state_at_year(self, year: int) -> Optional[FIREState]:
        """Get the state for a specific year."""
        for state in self.states:
            if state.year == year:
                return state
        return None

    def get_latest_state(self) -> FIREState:
        """Get the most recent state."""
        if not self.states:
            raise ValueError("No states exist")
        return self.states[-1]

    def get_all_states(self) -> List[FIREState]:
        """Get all states in chronological order."""
        return sorted(self.states, key=lambda x: x.year)

    def update_state_balance(self, year: int, new_balance: float) -> None:
        """Update the balance for a specific year's state."""
        state = self.get_state_at_year(year)
        if state:
            state.balance = new_balance
        else:
            raise ValueError(f"No state exists for year {year}")

    def create_next_year_state(
        self, current_state: FIREState, new_balance: float
    ) -> FIREState:
        """Create a state for the next year based on the current state."""
        next_year = current_state.year + 1

        # Check if we already have a state for next year
        existing_state = self.get_state_at_year(next_year)
        if existing_state:
            # Update only the balance
            existing_state.balance = new_balance
            return existing_state

        # Create new state inheriting all parameters from current state
        # Note: lump_sum defaults to 0.0 for new states (lump sums are one-time only)
        # Apply inflation to expenses for the next year
        inflated_expenses = current_state.yearly_expenses * (
            1 + current_state.inflation_rate
        )

        new_state = FIREState(
            year=next_year,
            balance=new_balance,
            yearly_income=current_state.yearly_income,
            yearly_expenses=inflated_expenses,
            annual_return_rate=current_state.annual_return_rate,
            inflation_rate=current_state.inflation_rate,
            non_wage_income=current_state.non_wage_income,
            retirement_year=current_state.retirement_year,
            lump_sum=0.0,  # Lump sums are one-time only, don't inherit
        )

        self.states.append(new_state)
        return new_state

    def get_latest_state_before_year(self, year: int) -> Optional[FIREState]:
        """Get the state with the highest year that is less than the target year."""
        latest_state = None
        for state in self.states:
            if state.year < year:
                if latest_state is None or state.year > latest_state.year:
                    latest_state = state
        return latest_state

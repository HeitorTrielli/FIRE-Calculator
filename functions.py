import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MultipleLocator


def generate_ar1_timeseries(
    initial_return, num_years_simulated, phi=0.999, sigma=0.005
):
    initial_return = initial_return - 1
    returns = [initial_return]
    for _ in range(1, num_years_simulated):
        noise = np.random.normal(0, sigma)
        new_return = phi * returns[-1] + noise
        returns.append(new_return)

    returns = [x + 1 for x in returns]

    return returns


def get_wealth(
    num_years_simulated,
    retirement_year,
    yearly_wage,
    yearly_fixed_cost,
    yearly_real_rate,
    non_wage_income=0,
    initial_capital=0,
    wage_growth_rate=0,
    yearly_returns=None,
    retirement_real_rate=0.06,
):
    total = initial_capital
    found_breakeven = False
    million_mult = 1
    first_million = False

    yearly_income = yearly_wage + non_wage_income

    list_year_total = []
    list_year_income = []
    breakeven_year = -1
    for i in range(num_years_simulated):
        if yearly_returns:
            return_rate = yearly_returns[i]
            print(f"On year {i+1} we had the return rate of: {return_rate}%")
        else:
            return_rate = yearly_real_rate

        wage_growth = yearly_wage * wage_growth_rate
        yearly_wage += wage_growth
        yearly_income += wage_growth
        if i == retirement_year - 1:
            print(f"After {retirement_year} years, you are finally retired!")
            yearly_income = non_wage_income
            yearly_wage = 0

        total += total * return_rate + yearly_income - yearly_fixed_cost

        yearly_income_from_savings = total * yearly_real_rate

        list_year_total.append((i + 1, total))
        list_year_income.append((i + 1, yearly_income_from_savings))

        if int(total / 1_000_000) > million_mult or (
            not first_million and total >= 1_000_000
        ):
            first_million = True
            print(
                f"In {i+1} years you accumulated to ${int(total / 1_000_000)} million"
            )
            million_mult = int(total / 1_000_000)

        if (
            total * retirement_real_rate + non_wage_income > yearly_fixed_cost
            and not found_breakeven
        ):
            found_breakeven = True
            breakeven_year = i + 1
            print("Break even at year:", breakeven_year)

    print(
        f"You accumulated over the {num_years_simulated} num_years_simulated of saving {yearly_income-yearly_fixed_cost:,}/year at a real rate of {yearly_real_rate}: {round(total, ndigits = 2):,}"
    )
    print(
        f"This will give you a real income (yet to be taxed) of: {round(total * retirement_real_rate, ndigits = 2):,}"
    )

    year_total_df = pd.DataFrame(list_year_total, columns=["year", "total"])
    year_income_df = pd.DataFrame(list_year_income, columns=["year", "total"])

    return year_total_df, year_income_df, breakeven_year


def plot_multiple_projections(
    retirement_years,
    num_simulation,
    yearly_fixed_cost,
    total_years=35,
    alpha=0.05,
    initial_return_rate=1.06,
):
    colors = [
        "blue",
        "green",
        "red",
        "cyan",
        "magenta",
        "yellow",
        "black",
        "white",
        "orange",
        "purple",
        "brown",
        "pink",
        "gray",
        "olive",
        "gold",
        "teal",
        "navy",
        "lime",
    ]

    for idx, retirement_year in enumerate(retirement_years):
        for i in range(num_simulation):
            yearly_returns = generate_ar1_timeseries(initial_return_rate, total_years)
            year_total_df, year_income_df, breakeven_year = get_wealth(
                yearly_returns=yearly_returns,
                retirement_year=retirement_year,
                num_years_simulated=total_years,
            )

            plt.plot(
                year_income_df["year"],
                year_income_df["total"],
                label=f"Model {i+1}",
                alpha=alpha,
                color=colors[idx],
            )

            if breakeven_year is not None:
                plt.axvline(x=breakeven_year, color="g", linestyle="--", alpha=0.5)

            # Add fixed yearly cost line
            plt.axhline(
                y=yearly_fixed_cost, color="r", linestyle="--", label="Cost Line"
            )

    # Formatting the plot
    plt.xlabel("Year")
    plt.ylabel("Cumulative Income")
    plt.title("AR(1) Wealth Models Over Time")
    plt.ticklabel_format(style="plain", axis="y")
    plt.grid(True)
    plt.show()


def plot_retirement_comparison(
    list_retirement: list[int],
    num_years_simulated: int,
    yearly_wage: float,
    yearly_fixed_cost: float,
    yearly_real_rate: float,
    non_wage_income: float = 0.0,
    initial_capital: float = 0.0,
    wage_growth_rate: float = 0.0,
    yearly_returns: list[float] | None = None,
):
    for retirement_year in list_retirement:
        year_total_df, year_income_df, breakeven_year = get_wealth(
            num_years_simulated,
            retirement_year=retirement_year,
            yearly_wage=yearly_wage,
            yearly_fixed_cost=yearly_fixed_cost,
            yearly_real_rate=yearly_real_rate,
            non_wage_income=non_wage_income,
            initial_capital=initial_capital,
            wage_growth_rate=wage_growth_rate,
            yearly_returns=yearly_returns,
        )
        plt.plot(
            year_income_df.year,
            year_income_df.total,
            label=f"Retirement at year {retirement_year}",
        )

        if breakeven_year > 0:
            plt.axvline(x=breakeven_year, linestyle="--")
            plt.ticklabel_format(style="plain", axis="y")

    plt.axhline(y=yearly_fixed_cost, color="r", linestyle="--")
    plt.legend()
    plt.grid(color="gray", linestyle="--", linewidth=0.5)
    plt.gca().xaxis.set_major_locator(MultipleLocator(1))
    plt.show()

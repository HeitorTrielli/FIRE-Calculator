import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def generate_ar1_timeseries(initial_return, years, phi=0.999, sigma=0.005):
    initial_return = initial_return - 1
    returns = [initial_return]
    for _ in range(1, years):
        noise = np.random.normal(0, sigma)
        new_return = phi * returns[-1] + noise
        returns.append(new_return)

    returns = [x + 1 for x in returns]

    return returns


def get_wealth(
    years,
    retirement_year,
    yearly_wage,
    yr_allow,
    cost_coverage,
    fixed_yearly_cost,
    yearly_real_rate,
    wage_growth_rate,
    m0,
    yearly_returns=None,
):

    fixed_yearly_cost_covered = fixed_yearly_cost * (1 - cost_coverage)
    yearly_allowance = 50_000 * yr_allow
    yearly_savings = yearly_allowance + yearly_wage - fixed_yearly_cost_covered

    total = m0
    found_breakeven = False
    million_mult = 1

    list_year_total = []
    list_year_income = []
    breakeven_year = -1
    for i in range(int(years)):
        if yearly_returns:
            return_rate = yearly_returns[i]
            print(f"On year {i+1} we had the return rate of: {return_rate}")
        else:
            return_rate = yearly_real_rate

        wage_growth = yearly_wage * (wage_growth_rate - 1)
        yearly_wage += wage_growth
        yearly_savings += wage_growth
        if i == retirement_year - 1:
            yearly_savings = yearly_savings - yearly_wage
            yearly_wage = 0

        total += total * (return_rate - 1) + yearly_savings

        yearly_income_from_savings = total * (1.06 - 1)

        list_year_total.append((i + 1, total))
        list_year_income.append((i + 1, yearly_income_from_savings))

        if int(total / 1_000_000) > million_mult:
            print(f"On year {i+1} you got to ${int(total / 1_000_000)} million dollars")
            million_mult = int(total / 1_000_000)

        if yearly_income_from_savings > fixed_yearly_cost and not found_breakeven:
            found_breakeven = True
            breakeven_year = i + 1
            print("Break even at year:", breakeven_year)

    print(
        f"You accumulated over the {years} years of saving {yearly_savings:,}/year at a real rate of {yearly_real_rate}: {round(total, ndigits = 2):,}"
    )
    print(
        f"This will give you a real income (yet to be taxed) of: {round(yearly_income_from_savings, ndigits = 2):,}"
    )

    year_total_df = pd.DataFrame(list_year_total, columns=["year", "total"])
    year_income_df = pd.DataFrame(list_year_income, columns=["year", "total"])

    return year_total_df, year_income_df, breakeven_year


def plot_multiple_projections(
    retirement_years,
    num_simulation,
    fixed_yearly_cost,
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
                years=total_years,
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
                y=fixed_yearly_cost, color="r", linestyle="--", label="Cost Line"
            )

    # Formatting the plot
    plt.xlabel("Year")
    plt.ylabel("Cumulative Income")
    plt.title("AR(1) Wealth Models Over Time")
    plt.ticklabel_format(style="plain", axis="y")
    plt.grid(True)
    plt.show()


def plot_retirement_comparison(list_retirement):
    for retirement_year in list_retirement:
        year_total_df, year_income_df, breakeven_year = get_wealth(
            retirement_year=retirement_year
        )
        plt.plot(
            year_income_df.year,
            year_income_df.total,
            label=f"Retirement at year {retirement_year}",
        )

        plt.axhline(y=fixed_yearly_cost, color="r", linestyle="--")
        plt.axvline(x=breakeven_year, color="g", linestyle="--")
        plt.ticklabel_format(style="plain", axis="y")

    plt.legend()
    plt.show()

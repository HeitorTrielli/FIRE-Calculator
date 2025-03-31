from functions import get_wealth

num_years_simulated = 35
retirement_year = 10

# NWI = Non-Wage Income (e.g. rent from real estate (if you are not counting real estate as net worth that is incident on the interest rate), allowance, etc)
yearly_nwi_flag = 0
yearly_nwi = 10_000

monthly_cost = 5000
yearly_fixed_cost = monthly_cost * 12

yearly_real_rate = 0.075
wage_growth_rate = 0.0

initial_capital = 50_000

non_wage_income = yearly_nwi * yearly_nwi_flag
yearly_wage = 8_000 * 12

year_total_df, year_income_df, breakeven_year = get_wealth(
    num_years_simulated=num_years_simulated,
    retirement_year=retirement_year,
    yearly_wage=yearly_wage,
    non_wage_income=non_wage_income,
    yearly_fixed_cost=yearly_fixed_cost,
    yearly_real_rate=yearly_real_rate + 0.0,
    wage_growth_rate=wage_growth_rate,
    initial_capital=initial_capital,
    yearly_returns=None,
    retirement_real_rate=0.06,
)

# year_total_df["total"].apply(lambda x: f"{x:_.2f}")
# year_income_df["total"].apply(lambda x: f"{x:_.2f}")

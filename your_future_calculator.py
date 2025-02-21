from functions import get_wealth, plot_retirement_comparison

num_years_simulated = 35
retirement_year = 15
doc = 1
mt = 1
yr_allow = 1
cost_coverage = 0
fixed_yearly_cost = 5500 * 12

yearly_real_rate = 0.06
wage_growth_rate = 0.0

m0 = 180_000

yearly_fixed_cost = fixed_yearly_cost * (1 - cost_coverage)
yearly_allowance = 50_000 * yr_allow
yearly_wage = (10000 * 15) * mt + 4000 * 12 * doc


_ = get_wealth(
    num_years_simulated=num_years_simulated,
    retirement_year=retirement_year,
    yearly_wage=yearly_wage,
    non_wage_income=yearly_allowance,
    yearly_fixed_cost=yearly_fixed_cost,
    yearly_real_rate=yearly_real_rate + 0.0,
    wage_growth_rate=wage_growth_rate,
    initial_capital=m0,
    yearly_returns=None,
)

plot_retirement_comparison(
    [7, 15],
    num_years_simulated=num_years_simulated,
    yearly_wage=yearly_wage,
    non_wage_income=yearly_allowance,
    yearly_fixed_cost=yearly_fixed_cost,
    yearly_real_rate=yearly_real_rate + 0.0,
    wage_growth_rate=wage_growth_rate,
    initial_capital=m0,
    yearly_returns=None,
)

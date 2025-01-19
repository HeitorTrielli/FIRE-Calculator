from functions import get_wealth

years = 15
retirement_year = 255
doc = 1
mt = 1
yr_allow = 1
cost_coverage = 0
fixed_yearly_cost = 4500 * 12 * 0

yearly_real_rate = 1.06
wage_growth_rate = 1.0


m0 = 151_000
yearly_wage = (10000 * 15) * mt + 4000 * 12 * doc

_ = get_wealth(
    years=years,
    retirement_year=retirement_year,
    yearly_wage=yearly_wage,
    yr_allow=yr_allow,
    cost_coverage=cost_coverage,
    fixed_yearly_cost=fixed_yearly_cost,
    yearly_real_rate=yearly_real_rate + 0.0,
    wage_growth_rate=wage_growth_rate,
    m0=m0,
    yearly_returns=None,
)

# plot_retirement_comparison([8, 15])

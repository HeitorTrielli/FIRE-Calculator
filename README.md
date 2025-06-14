# 🔥 FIRE Calculator

A comprehensive Financial Independence, Retire Early (FIRE) calculator built with Streamlit. Plan your path to financial freedom with advanced scenario modeling, future state changes, and detailed visualizations.

## 🚀 Features

### Core Functionality
- **Yearly Financial Projections**: Calculate your balance growth over time
- **FIRE Timeline Calculation**: Determine when you'll reach financial independence
- **Million Dollar Milestones**: Track when you hit major wealth milestones
- **Future Scenario Planning**: Model changes in income, expenses, and returns over time
- **Lump Sum Events**: Include one-time income (inheritance, bonuses) or expenses (house, car)
- **Retirement Planning**: Automatic transition from wage income to investment returns

### Advanced Features
- **Non-Wage Income**: Model rental income, dividends, or side businesses that continue after retirement
- **Inflation Modeling**: Account for purchasing power erosion over time
- **Configuration Management**: Save and load different financial scenarios
- **Interactive Visualizations**: Four-panel charts showing balance, income vs expenses, returns vs expenses, and net cash flow
- **Detailed Results Table**: Year-by-year breakdown of all financial metrics

## 📋 Requirements

- Python 3.8+
- Streamlit
- Plotly
- Pandas

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd FIRE-Calculator
   ```

2. **Install dependencies**:
   ```bash
   pip install streamlit plotly pandas
   ```

3. **Run the application**:
   ```bash
   streamlit run app.py
   ```

4. **Open your browser** to `http://localhost:8501`

## 🎯 How to Use

### 1. Initial Setup
Configure your starting financial state in the sidebar:

- **Initial Balance**: Your current investment portfolio value
- **Yearly Wage Income**: Your salary/wage income (stops at retirement)
- **Non-Wage Income**: Income that continues after retirement (rentals, dividends)
- **Yearly Expenses**: Your total annual expenses
- **Annual Return Rate**: Expected investment return (typically 6-8%)
- **Inflation Rate**: Expected annual inflation (typically 2-3%)
- **Retirement Year**: When you plan to stop working

### 2. Add Future Changes
Plan for life changes using the "Future State Changes" section:

- **Income Changes**: Salary increases, career changes, or retirement
- **Expense Changes**: Lifestyle inflation or downsizing
- **Return Rate Changes**: Different investment strategies over time
- **Lump Sum Events**: 
  - Positive: Inheritance, bonuses, stock options
  - Negative: Major purchases (house down payment, car, etc.)

### 3. Run Calculations
Click "🚀 Calculate FIRE Trajectory" to generate:

- **Financial projections** for your specified timeline
- **Interactive charts** showing your wealth accumulation
- **Million dollar milestones** with exact timing
- **Detailed year-by-year breakdown** in expandable table

### 4. Configuration Management
- **Download**: Save your current configuration as JSON
- **Upload**: Load a previously saved configuration
- **Auto-load**: App automatically loads `fire_config.json` on startup

## 📊 Understanding the Charts

### 1. Balance Over Time
- Shows your total investment balance growth
- Golden dashed lines mark million-dollar milestones
- Main indicator of FIRE progress

### 2. Income vs Expenses
- Green line: Total income (wage + non-wage)
- Red line: Annual expenses
- Gap between lines = annual savings

### 3. Returns vs Expenses
- Orange line: Investment returns each year
- Red line: Annual expenses
- When orange exceeds red = financially independent

### 4. Net Cash Flow
- Purple area: Total cash flow (income - expenses + lump sums)
- Shows annual contribution to wealth building
- Negative values indicate spending more than earning

## 💡 Example Scenarios

### Basic FIRE Journey
```
Initial Balance: $50,000
Yearly Income: $75,000
Yearly Expenses: $45,000
Annual Return: 7%
Retirement Year: 15
```

### Career Progression
```
Year 10: Income increases to $90,000, expenses to $50,000
Year 12: $100,000 inheritance
Year 15: Retirement (wage income stops)
```

### Major Purchase
```
Year 8: -$500,000 lump sum (house down payment)
Year 10: Expenses increase to $60,000 (mortgage payments)
```

## 🔧 Configuration Files

### JSON Structure
```json
{
    "initial_state": {
        "initial_balance": 50000,
        "yearly_income": 75000,
        "yearly_expenses": 45000,
        "annual_return_rate": 0.07,
        "inflation_rate": 0.025,
        "non_wage_income": 5000,
        "retirement_year": 15
    },
    "future_states": [
        {
            "year": 10,
            "yearly_income": 90000,
            "yearly_expenses": 50000
        },
        {
            "year": 12,
            "lump_sum": 100000
        }
    ]
}
```

### Sharing Configurations
1. Configure your scenario in the app
2. Click "📥 Download Configuration"
3. Share the JSON file with others
4. They can upload it using "Upload Configuration" → "🔄 Update Config"

## 🧮 Running Examples

### Command Line Example
```bash
python example.py
```

This runs a sample calculation and prints results to the console, demonstrating the core calculation engine.

### Streamlit Web App
```bash
streamlit run app.py
```

This launches the full interactive web application with charts and configuration management.

## 📈 Key Concepts

### FIRE Number
Your FIRE number is typically 25x your annual expenses (4% withdrawal rule). The app calculates when you'll reach this milestone.

### Safe Withdrawal Rate
The app assumes you can safely withdraw 4% of your portfolio annually in retirement without depleting it.

### Sequence of Returns Risk
The app models year-by-year returns, helping you understand how market volatility affects your timeline.

### Coast FIRE
When your investment returns exceed your expenses, you've reached "Coast FIRE" - you could stop saving and still retire comfortably.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

If you encounter issues or have questions:

1. Check the example configurations
2. Verify your JSON file format
3. Ensure all required fields are present
4. Try restarting the app with a fresh configuration

## 🎉 Tips for Success

1. **Be Conservative**: Use realistic return rates (6-8%) and account for inflation
2. **Plan for Changes**: Model salary increases, lifestyle inflation, and major purchases
3. **Regular Updates**: Revisit and update your projections annually
4. **Multiple Scenarios**: Create different configurations for optimistic/pessimistic cases
5. **Track Progress**: Compare actual results to projections and adjust as needed

---

**Built with ❤️ using Streamlit • Enhanced FIRE Calculator with Future State Planning** 
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf

# Read data from the original Excel file
file_path = "merged_stock_data_with_categories_in_cells_nov2024.xlsx"
df = pd.read_excel(file_path)

# Read data from the additional Excel file with calculated metrics
metrics_file_path = "calculated_stock_metrics_full.xlsx"
metrics_df = pd.read_excel(metrics_file_path)

# Categories and risk thresholds
risk_categories = {
    "Market Risk": {
        "Volatility": (0.1, 0.2),
        "Beta": (0.5, 1.5),
        "Correlation with ^NSEI": (0.7, 1),
    },
    "Financial Risk": {
        "debtToEquity": (0.5, 1.5),
        "currentRatio": (1.5, 2),
        "quickRatio": (1, 1.5),
        "Profit Margins": (20, 30),
        "returnOnAssets": (10, 20),
        "returnOnEquity": (15, 25),
    },
    "Liquidity Risk": {
        "Volume": (1_000_000, float('inf')),
        "Average Volume": (500_000, 1_000_000),
        "marketCap": (10_000_000_000, float('inf')),
    },
}

def categorize_risk(value, thresholds):
    """Categorizes risk based on predefined thresholds."""
    try:
        value = float(value)
    except (ValueError, TypeError):
        return "Data not available"

    if value < thresholds[0]:
        return "Good"
    elif thresholds[0] <= value <= thresholds[1]:
        return "Neutral"
    else:
        return "Bad"

def get_risk_color(risk_level):
    """Returns the color associated with a risk level."""
    if risk_level == "Good":
        return "green"
    elif risk_level == "Neutral":
        return "yellow"
    elif risk_level == "Bad":
        return "red"
    else:
        return "black"

def fetch_stock_data(stock_symbols):
    """Fetches real-time stock data from Yahoo Finance."""
    stock_data = yf.download(stock_symbols, period="1d", group_by='ticker')
    return stock_data

def calculate_risk_parameters(stock_symbols):
    """Calculates and categorizes risk parameters for a given stock portfolio."""
    results = []
    stock_scores = {}
    category_scores = {category: 0 for category in risk_categories}
    total_portfolio_score = 0

    stock_data = fetch_stock_data(stock_symbols)  # Fetch latest stock data

    # Iterate over each stock symbol
    for stock_symbol in stock_symbols:
        # Get data from Excel file
        stock_info = df[df['Stock Symbol'] == stock_symbol]

        if stock_info.empty:
            print(f"No data found for stock symbol: {stock_symbol}")
            continue

        stock_info = stock_info.iloc[0]  # Get the first row for the stock

        # Fetch real-time data from Yahoo Finance (Price, Volume, etc.)
        if stock_symbol in stock_data:
            real_time_data = stock_data[stock_symbol].iloc[-1]
            stock_info['Price'] = real_time_data['Close']
            stock_info['Volume'] = real_time_data['Volume']
        else:
            stock_info['Price'] = 'Data not available'
            stock_info['Volume'] = 'Data not available'

        # Initialize summary for the stock
        total_stock_score = 0
        summary = {category: {'Good': 0, 'Neutral': 0, 'Bad': 0, 'Data not available': 0} for category in risk_categories}

        # Process each risk category and its parameters
        for category, parameters in risk_categories.items():
            for param, thresholds in parameters.items():
                value = stock_info.get(param)

                if value is not None:
                    risk_level = categorize_risk(value, thresholds)
                    summary[category][risk_level] += 1
                    results.append({
                        'Stock Symbol': stock_symbol,
                        'Category': category,
                        'Parameter': param,
                        'Value': value,
                        'Risk Level': risk_level,
                        'Color': get_risk_color(risk_level)
                    })

                    if risk_level == "Good":
                        category_scores[category] += 1
                        total_portfolio_score += 1
                        total_stock_score += 1
                    elif risk_level == "Bad":
                        category_scores[category] -= 1
                        total_portfolio_score -= 1
                        total_stock_score -= 1
                else:
                    results.append({
                        'Stock Symbol': stock_symbol,
                        'Category': category,
                        'Parameter': param,
                        'Value': 'Data not available',
                        'Risk Level': 'Data not available',
                        'Color': 'black'
                    })
                    summary[category]['Data not available'] += 1

        stock_scores[stock_symbol] = total_stock_score  # Save the score for the stock

    return results, category_scores, stock_scores, total_portfolio_score

# Streamlit layout
st.title("Real-Time Risk Management Dashboard")

# Dropdown for stock selection
selected_stocks = st.multiselect(
    "Select Stocks",
    options=df['Stock Symbol'].unique(),
    default=df['Stock Symbol'].unique()[0],
)

# Display risk category overview
st.subheader("Risk Category Overview")

results, category_scores, stock_scores, total_portfolio_score = calculate_risk_parameters(selected_stocks)

market_risk_data = [result for result in results if result['Category'] == 'Market Risk']
financial_risk_data = [result for result in results if result['Category'] == 'Financial Risk']
liquidity_risk_data = [result for result in results if result['Category'] == 'Liquidity Risk']

# Market Risk Meter
st.write("### Market Risk Meter")
market_risk_score = category_scores['Market Risk']
market_risk_color = get_risk_color("Good" if market_risk_score > 0 else "Bad")
fig_market = go.Figure(go.Indicator(
    mode="gauge+number",
    value=market_risk_score,
    title={"text": "Market Risk", "font": {"size": 24}},
    gauge={"axis": {"range": [None, 5]}, "steps": [
        {"range": [0, 2], "color": "green"},
        {"range": [2, 3], "color": "yellow"},
        {"range": [3, 5], "color": "red"}],
    },
))
st.plotly_chart(fig_market)

# Financial Risk Meter
st.write("### Financial Risk Meter")
financial_risk_score = category_scores['Financial Risk']
financial_risk_color = get_risk_color("Good" if financial_risk_score > 0 else "Bad")
fig_financial = go.Figure(go.Indicator(
    mode="gauge+number",
    value=financial_risk_score,
    title={"text": "Financial Risk", "font": {"size": 24}},
    gauge={"axis": {"range": [None, 5]}, "steps": [
        {"range": [0, 2], "color": "green"},
        {"range": [2, 3], "color": "yellow"},
        {"range": [3, 5], "color": "red"}],
    },
))
st.plotly_chart(fig_financial)

# Liquidity Risk Meter
st.write("### Liquidity Risk Meter")
liquidity_risk_score = category_scores['Liquidity Risk']
liquidity_risk_color = get_risk_color("Good" if liquidity_risk_score > 0 else "Bad")
fig_liquidity = go.Figure(go.Indicator(
    mode="gauge+number",
    value=liquidity_risk_score,
    title={"text": "Liquidity Risk", "font": {"size": 24}},
    gauge={"axis": {"range": [None, 5]}, "steps": [
        {"range": [0, 2], "color": "green"},
        {"range": [2, 3], "color": "yellow"},
        {"range": [3, 5], "color": "red"}],
    },
))
st.plotly_chart(fig_liquidity)

# Investment Scores Visualization
st.subheader("Investment Scores Visualization")

investment_data = [{"Stock Symbol": stock, "Investment Score": score} for stock, score in stock_scores.items()]
investment_df = pd.DataFrame(investment_data)
fig = px.bar(investment_df, x="Stock Symbol", y="Investment Score", title="Investment Scores for Selected Stocks")
st.plotly_chart(fig)

# Portfolio Score Table
st.write("### Total Portfolio Score")
st.dataframe(pd.DataFrame([{"Portfolio Score": total_portfolio_score}]))

# Display summary
st.subheader("Summary")
st.write(f"Total Portfolio Score: {total_portfolio_score}")
for category, score in category_scores.items():
    st.write(f"{category}: {score}")

# Additional metrics
st.subheader("Additional Stock Metrics")
metrics_data = metrics_df[metrics_df['Stock Symbol'].isin(selected_stocks)].to_dict('records')
st.dataframe(pd.DataFrame(metrics_data))

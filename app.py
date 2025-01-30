import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Load the stock data and metrics
file_path = "merged_stock_data_with_categories_in_cells_nov2024.xlsx"
df = pd.read_excel(file_path)

metrics_file_path = "calculated_stock_metrics_full.xlsx"
metrics_df = pd.read_excel(metrics_file_path)

# Categories and risk thresholds from the original code
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

def create_risk_meter(risk_score, max_score=5):
    """Creates a gauge meter visualization for risk categories."""
    color = 'green' if risk_score > 0 else 'red' if risk_score < 0 else 'yellow'
    fig = go.Figure(go.Gauge(
        gauge={'axis': {'range': [None, max_score]}},
        value=risk_score,
        title={'text': f"Risk Meter: {color.capitalize()}"}, 
        delta={'reference': 0},
        domain={'x': [0, 1], 'y': [0, 1]},
        marker={'color': color, 'size': 35},
    ))
    return fig

# Streamlit interface
st.title("Real-Time Risk Management Dashboard")

# Stock selection dropdown
selected_stocks = st.multiselect(
    "Select Stocks", options=df['Stock Symbol'].unique(), default=df['Stock Symbol'].unique()[0:3]
)

# Calculate risk parameters
if selected_stocks:
    results, category_scores, stock_scores, total_portfolio_score = calculate_risk_parameters(selected_stocks)

    # Display stock-specific risk meters
    for stock_symbol in selected_stocks:
        st.subheader(f"Risk Meter for {stock_symbol}")
        stock_score = stock_scores.get(stock_symbol, 0)
        risk_level = "Good" if stock_score > 0 else "Bad" if stock_score < 0 else "Neutral"
        color = get_risk_color(risk_level)

        st.markdown(f"<h3 style='color:{color};'>{stock_symbol} - {risk_level}</h3>", unsafe_allow_html=True)

    # Portfolio risk overview
    st.subheader("Overall Portfolio Risk")
    portfolio_risk_level = "Good" if total_portfolio_score > 0 else "Bad" if total_portfolio_score < 0 else "Neutral"
    portfolio_color = get_risk_color(portfolio_risk_level)
    st.markdown(f"<h3 style='color:{portfolio_color};'>Portfolio Risk Level: {portfolio_risk_level}</h3>", unsafe_allow_html=True)

    # Risk meters for categories (Market, Financial, Liquidity)
    st.subheader("Risk Meters for Categories")
    
    # Create a risk meter for each category
    market_risk_score = category_scores["Market Risk"]
    financial_risk_score = category_scores["Financial Risk"]
    liquidity_risk_score = category_scores["Liquidity Risk"]

    # Market Risk Meter
    st.write("**Market Risk Meter**")
    st.plotly_chart(create_risk_meter(market_risk_score))

    # Financial Risk Meter
    st.write("**Financial Risk Meter**")
    st.plotly_chart(create_risk_meter(financial_risk_score))

    # Liquidity Risk Meter
    st.write("**Liquidity Risk Meter**")
    st.plotly_chart(create_risk_meter(liquidity_risk_score))

    # Risk tables
    st.subheader("Risk Overview by Category")

    market_risk_data = [r for r in results if r['Category'] == "Market Risk"]
    financial_risk_data = [r for r in results if r['Category'] == "Financial Risk"]
    liquidity_risk_data = [r for r in results if r['Category'] == "Liquidity Risk"]

    # Display data tables for each risk category
    st.write("**Market Risk**")
    st.dataframe(pd.DataFrame(market_risk_data))

    st.write("**Financial Risk**")
    st.dataframe(pd.DataFrame(financial_risk_data))

    st.write("**Liquidity Risk**")
    st.dataframe(pd.DataFrame(liquidity_risk_data))

    # Portfolio score table
    st.subheader("Portfolio Score Table")
    st.write(f"Total Portfolio Score: {total_portfolio_score}")

    # Investment Scores Visualization (Bar Chart)
    investment_data = [{"Stock Symbol": stock, "Investment Score": score} for stock, score in stock_scores.items()]
    investment_df = pd.DataFrame(investment_data)

    fig = px.bar(investment_df, x="Stock Symbol", y="Investment Score", title="Investment Scores for Selected Stocks")
    st.plotly_chart(fig)

    # Additional metrics for selected stocks
    st.subheader("Additional Stock Metrics")
    metrics_data = metrics_df[metrics_df['Stock Symbol'].isin(selected_stocks)].to_dict('records')
    st.write(pd.DataFrame(metrics_data))
else:
    st.write("Please select at least one stock.")
